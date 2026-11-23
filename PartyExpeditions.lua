-- TapCatForever: party expeditions. Group members who have TapCatForever send their cats into a
-- dungeon or raid together. The one who starts it picks the place, the length (15 min to 4 h) and
-- the difficulty (Normal, Hard, Heroic); the others get a small Accept / Decline invite just above
-- their cat (and in the Expeditions tab) that runs out after 60 seconds. Accepting sends your current
-- cat, or the cats you picked in the Expeditions tab (up to 3).
--
-- Success uses every cat's Power added up against what the place needs at that difficulty (more
-- players need a little more, but bring a lot more Power). Everybody sees the same result: it is
-- rolled from a seed the starter shares. Each player claims their own rewards at the end: XP for
-- their cats, a few TapCoins, chests (TCF:AwardChest) and a small group bonus for every player.
--
-- Once it has started it runs for everyone even if the group breaks up or someone logs out: every
-- client saves the shared expedition (id, start, length, difficulty, seed, players and their
-- Power) in db.expeditions.group. It has its own slot: the two solo expedition slots stay free.
--
-- Protocol (prefix "TapCatFvr", party/raid/instance channel only, every field checked; v = 1):
--   G1;v;id;place;len;diff;power;cats           invite (the starter's Power and cats)
--   G2;v;id;answer;power;cats                   y accept (with my Power and cats), n decline, b busy,
--                                               s seen (I got it and will answer: the starter waits for me)
--   G3;v;id;place;len;diff;start;seed;players   start: players = name:power:cats,name:power:cats...
--   G4;v;id;reason                              called off: x withdrawn, n nobody joined
--   G5;v;id                                     I accepted but never saw the start: please send it again
-- id: 6 hex digits. place: an Adventure dungeon or raid key (TCF.TIERS). len: 1-5, diff: 1-3.
-- cats: one letter per class (TCF.GROUP_CLASS_CODE). start: the realm clock (GetServerTime).
-- Names are sent without the realm (as the party row shows them), at most 5 players.
local ADDON, TCF = ...
local floor, min, max, random = math.floor, math.min, math.max, math.random

local PREFIX = "TapCatFvr"
local VER = "1"
local GX = TCF.GX or {}
TCF.GX = GX
GX.INVITE_TIME = 60         -- an invite waits this long for an answer (no answer = decline)
GX.MAX_PLAYERS = 5
GX.MAX_CATS = 3             -- cats per player
local START_WAIT = 30       -- after the invite ran out: how long an accepted player waits for the start
local LATE_MAX = 240        -- the starter keeps trying to send the start this long after the invite ran out
local LATE_KEEP = 300       -- an accepted player still takes a late start this long after the invite ran out
local ACK_GRACE = 5         -- seconds the starter waits for "seen" answers before counting who is still to answer
local MAX_ASKS = 6          -- G5 asks per accepted player (and per player on the starter's side)
local RESEND_AT = { 4, 12 } -- the starter sends the start again this many seconds later (lost messages)
local IN_WINDOW, IN_MAX = 10, 20
local OUT_RETRY, OUT_TRIES, OUT_MAX = 2, 60, 8   -- refused sends are tried again for about 2 minutes
local MUTE_AFTER_NO = 20    -- after you decline, that player's invites wait this long

GX.LENGTHS = { { 15 * 60, "15 min" }, { 30 * 60, "30 min" }, { 3600, "1 h" }, { 2 * 3600, "2 h" }, { 4 * 3600, "4 h" } }
-- req: how much more Power the place needs; reward: XP, TapCoins and chest chance
GX.DIFFS = {
  { name = "Normal", req = 1.0, reward = 1.0 },
  { name = "Hard",   req = 1.6, reward = 1.3 },
  { name = "Heroic", req = 2.5, reward = 1.7 },
}
GX.COINS_PER_HOUR = 10      -- TapCoins per hour on Normal for one player (TapCoins stay scarce)
GX.CHEST_CHANCE = 0.15      -- per chest roll on Normal; one roll per hour away (part of one for shorter trips)
GX.GROUP_BONUS = 0.1        -- +10% XP and TapCoins for every other player
GX.XP_PER_MIN = 5           -- like the solo expeditions

local CODES = { WARRIOR = "W", PALADIN = "P", HUNTER = "H", ROGUE = "R", PRIEST = "I", SHAMAN = "S",
  MAGE = "M", WARLOCK = "L", DRUID = "D" }
local CLASS_OF = {}
for k, v in pairs(CODES) do CLASS_OF[v] = k end
TCF.GROUP_CLASS_CODE = CODES

local function isSecret(v) return TCF.IsSecret and TCF.IsSecret(v) end
local function now() return GetTime and GetTime() or 0 end

-- the realm's clock (shared by everyone in the group), or the computer's clock without it
local function serverNow()
  local t
  if GetServerTime then local ok, v = pcall(GetServerTime); if ok then t = v end end
  if (isSecret(t) or type(t) ~= "number") and time then local ok, v = pcall(time); t = ok and v or nil end
  if isSecret(t) or type(t) ~= "number" then return 0 end
  return floor(t)
end
GX.ServerNow = serverNow

---------------------------------------------------------------- places and numbers
-- every Adventure dungeon and raid, easiest first
local places, placeBy
local function placeList()
  if places then return places, placeBy end
  places, placeBy = {}, {}
  -- the solo expeditions' recommended Power, by the zone's difficulty: the same scale here
  local pts = { { 6, 700 }, { 21, 1600 }, { 38, 3400 }, { 56, 5800 }, { 61, 6600 }, { 66, 7600 }, { 71, 9400 }, { 78, 12500 } }
  local function rec(d)
    if d <= pts[1][1] then return pts[1][2] end
    for i = 2, #pts do
      if d <= pts[i][1] then
        local a, b = pts[i - 1], pts[i]
        return floor((a[2] + (b[2] - a[2]) * (d - a[1]) / (b[1] - a[1])) / 50 + 0.5) * 50
      end
    end
    return pts[#pts][2]
  end
  for ti, t in ipairs(TCF.TIERS or {}) do
    if t.raid or (TCF.IsDungeonTier and TCF.IsDungeonTier(t)) then
      local p = { key = t.key, name = t.name, tier = ti, raid = t.raid and true or false, rec = rec(t.diff or 1) }
      places[#places + 1] = p
      placeBy[p.key] = p
    end
  end
  return places, placeBy
end
function TCF:GroupExpPlaces() return (placeList()) end
function TCF.GroupExpPlace(key) local _, by = placeList(); return by[key] end

-- Power a group of `players` needs at this place and difficulty for the best odds
function TCF.GroupExpNeed(placeKey, diff, players)
  local p = TCF.GroupExpPlace(placeKey)
  local d = GX.DIFFS[diff]
  if not p or not d then return 1 end
  players = max(2, min(GX.MAX_PLAYERS, players or 2))
  return floor(p.rec * d.req * (1 + 0.5 * (players - 1)))
end

-- the chance of success in permille (the same on every client: integers in, integer out)
function TCF.GroupExpChance(power, need)
  local r = (power or 0) / max(1, need or 1)
  -- from 5% with no Power at all up to 97% at the Power needed (a group with no progress can't farm
  -- Heroic raids)
  return floor(1000 * min(0.97, 0.05 + 0.92 * r * r) + 0.5)
end

-- success or not, from the shared seed: every client gets the same answer
function TCF.GroupExpRoll(seed, id)
  local h = 0
  for i = 1, #(id or "") do h = (h * 31 + id:byte(i)) % 999983 end
  return ((((seed or 0) + h) % 999983) * 7919 + 104729) % 1000
end

-- the chest a successful roll gives, and the rare extra chest (a Dungeon Chest or a Raider's Hoard)
function TCF.GroupExpChests(placeKey, diff)
  local p = TCF.GroupExpPlace(placeKey)
  local raid = p and p.raid
  local main = raid and ({ "strong", "strong", "heroic" })[diff] or ({ "pouch", "strong", "strong" })[diff]
  local extra = diff == 3 and (raid and "raid" or "dungeon") or nil
  return main or "pouch", extra
end

-- what one player gets on success: XP for each cat, TapCoins (about), chest rolls and their chance,
-- the extra chest's chance. A failure gives half the XP and a tenth of the TapCoins.
function TCF.GroupExpRewards(placeKey, len, diff, players)
  local L, D = GX.LENGTHS[len], GX.DIFFS[diff]
  if not L or not D then return 0, 0, 0, 0, 0 end
  players = max(2, min(GX.MAX_PLAYERS, players or 2))
  local hours = L[1] / 3600
  local bonus = 1 + GX.GROUP_BONUS * (players - 1)
  local xp = floor(L[1] / 60 * GX.XP_PER_MIN * D.reward * bonus)
  local coins = max(2, floor(GX.COINS_PER_HOUR * hours * D.reward * bonus + 0.5))
  local rolls = max(1, math.ceil(hours)) + (players >= 3 and 1 or 0)
  local chance = min(0.95, GX.CHEST_CHANCE * D.reward * min(1, hours))
  local extraChance = diff == 3 and min(0.5, 0.05 * hours) or 0
  return xp, coins, rolls, chance, extraChance
end

---------------------------------------------------------------- saved state
local function store(self)
  self = self or TCF
  self.db.expeditions = self.db.expeditions or { active = {} }
  return self.db.expeditions
end
function TCF:GroupExp() return store(self).group end

-- the cats you sent (or are about to send) on a party expedition can't go anywhere else
function TCF:GroupExpBusy(class)
  if not self.db then return nil end
  local g = store(self).group
  if g then for _, c in ipairs(g.mine or {}) do if c == class then return g end end end
  local inv = GX.inv
  if inv and inv.state == "accepted" then for _, c in ipairs(inv.cats or {}) do if c == class then return inv end end end
  local out = GX.out
  if out then for _, c in ipairs(out.cats or {}) do if c == class then return out end end end
  return nil
end

local function codesOf(cats)
  local t = {}
  for _, c in ipairs(cats) do t[#t + 1] = CODES[c] end
  return table.concat(t)
end
local function catsOf(codes)
  if type(codes) ~= "string" or #codes < 1 or #codes > GX.MAX_CATS then return nil end
  local list, seen = {}, {}
  for i = 1, #codes do
    local c = CLASS_OF[codes:sub(i, i)]
    if not c or seen[c] then return nil end
    seen[c] = true
    list[#list + 1] = c
  end
  return list
end
GX.CodesOf, GX.CatsOf = codesOf, catsOf

-- checks a list of your own cats: 1 to 3 different classes, none away. Returns the list or nil, why.
local function validCats(self, cats)
  if type(cats) ~= "table" or #cats < 1 then return nil, "Choose at least one cat." end
  if #cats > GX.MAX_CATS then return nil, "Choose up to " .. GX.MAX_CATS .. " cats." end
  local seen, list = {}, {}
  for _, c in ipairs(cats) do
    local cl = TCF.CLASS_BY_KEY[c]
    if not cl or seen[c] then return nil, "Each cat can only go once." end
    seen[c] = true
    local solo = self.SoloExpeditionOf and self:SoloExpeditionOf(c)
    if solo then return nil, "Your " .. cl.name .. " cat is away on an expedition." end
    local g = store(self).group
    if g then for _, m in ipairs(g.mine or {}) do if m == c then return nil, "Your " .. cl.name .. " cat is away on a party expedition." end end end
    list[#list + 1] = c
  end
  return list
end

-- the cats you'd send by default: the ones picked in the Expeditions tab, else your current cat
function TCF:GroupExpDefaultCats()
  local picked = {}
  for _, cl in ipairs(TCF.CLASSES) do
    if GX.picked and GX.picked[cl.key] then picked[#picked + 1] = cl.key end
  end
  if #picked > 0 then return picked end
  return { self.db.class }
end

function TCF:GroupExpPower(cats)
  local p = 0
  for _, c in ipairs(cats or {}) do p = p + self:CombatStats(c).power end
  return floor(p)
end

---------------------------------------------------------------- names and group
local function base(name)
  if type(name) ~= "string" or isSecret(name) or name == "" then return nil end
  local b = name:match("^([^%-]+)")
  return b and b:gsub("%s", ""):lower() or nil
end
-- the name players see (no realm, no "|"), as the party row shows it
local function shortName(name)
  if type(name) ~= "string" or isSecret(name) then return "?" end
  local n = (name:match("^([^%-]+)") or name):gsub("[|:;,%s]", "")
  if n == "" then return "?" end
  return n
end
GX.ShortName = shortName

local function isMe(sender)
  if TCF.PartyIsMe then return TCF.PartyIsMe(sender) end
  local n = UnitName and UnitName("player")
  return base(sender) ~= nil and base(sender) == base(n)
end

-- your name without the realm, as friends see it in the party row: UnitName when it can be read,
-- else the name learned from your own party messages (Party.lua); "?" while neither is known
local function myName()
  local n = TCF.SelfName and TCF.SelfName()
  if type(n) ~= "string" or isSecret(n) then n = UnitName and UnitName("player") end
  if type(n) ~= "string" or isSecret(n) then return "?" end
  return shortName(n)
end

local function inGroup()
  if not IsInGroup then return false end
  local ok, g = pcall(IsInGroup)
  return ok and g and not isSecret(g) and true or false
end

local function chatType()
  local home = LE_PARTY_CATEGORY_HOME and IsInGroup and IsInGroup(LE_PARTY_CATEGORY_HOME)
  local inst = LE_PARTY_CATEGORY_INSTANCE and IsInGroup and IsInGroup(LE_PARTY_CATEGORY_INSTANCE)
  if inst and not home then return "INSTANCE_CHAT" end
  if IsInRaid and IsInRaid() then return "RAID" end
  return "PARTY"
end

-- group members whose addon said hello (Party.lua), never test-mode fake cats
local function addonFriends()
  local list = {}
  if not TCF.PartyMembers then return list end
  for _, m in ipairs(TCF:PartyMembers()) do
    if not m.fake and base(m.name) then list[#list + 1] = m end
  end
  return list
end
local function friendNamed(name)
  local b = base(name)
  if not b then return nil end
  for _, m in ipairs(addonFriends()) do if base(m.name) == b then return m end end
end
function TCF:GroupExpFriends() return #addonFriends() end

---------------------------------------------------------------- sending
local outQ = {}
local function rawSend(text)
  if not inGroup() then return false end
  local api = C_ChatInfo and C_ChatInfo.SendAddonMessage
  if not api then return false end
  local ok, res = pcall(api, PREFIX, text, chatType())
  -- 12.x returns a result code (0 = sent) and can refuse (combat in an instance, throttled)
  return ok and (res == nil or res == true or res == 0 or
    (Enum and Enum.SendAddonMessageResult and res == Enum.SendAddonMessageResult.Success)) and true or false
end
-- sends now, or queues it while sending is refused; onSent runs once it has really gone out
local function sendThen(onSent, kind, ...)
  local text = table.concat({ kind, VER, ... }, ";")
  if #text > 250 then return false end
  if rawSend(text) then
    if onSent then onSent() end
    return true
  end
  if #outQ < OUT_MAX then outQ[#outQ + 1] = { text = text, at = now() + OUT_RETRY, tries = 1, onSent = onSent } end
  return false
end
local function send(kind, ...) return sendThen(nil, kind, ...) end
local function flushQueue()
  if #outQ == 0 then return end
  local q = outQ[1]
  if now() < q.at then return end
  if rawSend(q.text) then
    table.remove(outQ, 1)
    if q.onSent then q.onSent() end
    return
  end
  q.tries, q.at = q.tries + 1, now() + OUT_RETRY
  if q.tries > OUT_TRIES or not inGroup() then table.remove(outQ, 1) end
end

local function notify()
  if GX.UpdatePrompt then GX.UpdatePrompt() end
  if GX.OnChange then pcall(GX.OnChange) end
  if TCF.MarkDirty then TCF:MarkDirty() end
end

local function newId() return string.format("%06x", random(0, 16777215)) end

local function describe(placeKey, len, diff)
  local p = TCF.GroupExpPlace(placeKey)
  return string.format("%s, %s, %s", p and p.name or "?", GX.LENGTHS[len] and GX.LENGTHS[len][2] or "?", GX.DIFFS[diff] and GX.DIFFS[diff].name or "?")
end
GX.Describe = describe

---------------------------------------------------------------- starting one (the starter)
-- GX.out = { id, place, len, diff, cats, power, expires, answers = { base = { name, ans, power, cats, at } },
--   order = { base... } (accepts in the order they came), seen = { base = true } (players whose client
--   said it got the invite: only they are waited for, so members on an older version don't hold it up),
--   sentAt (when the invite really went out), startNow (start as soon as the group can hear it) }
local function busy(self)
  if store(self).group then return "Your cats are already on a party expedition. Claim it first." end
  if GX.out then return "You already sent an invite." end
  if GX.inv and GX.inv.state ~= "over" then return "Answer the invite you have first." end
  return nil
end

function TCF:GroupExpInvite(placeKey, len, diff, cats)
  if not self.db then return false end
  if not TCF.GroupExpPlace(placeKey) or not GX.LENGTHS[len] or not GX.DIFFS[diff] then return false, "Choose a place, a length and a difficulty." end
  if not inGroup() then return false, "You need to be in a party or raid." end
  if #addonFriends() == 0 then return false, "Nobody else in your group has TapCatForever." end
  -- (1.6.0) the start lists every player by name: yours is learned from your own party messages
  -- when the game doesn't let addons read it, which takes a moment after joining a group
  if myName() == "?" then return false, "Your addon is still getting your name from the group. Try again in a few seconds." end
  local why = busy(self)
  if why then return false, why end
  local list, err = validCats(self, cats or self:GroupExpDefaultCats())
  if not list then return false, err end
  local id = newId()
  local power = self:GroupExpPower(list)
  local o = { id = id, place = placeKey, len = len, diff = diff, cats = list, power = power,
    expires = now() + GX.INVITE_TIME + 3, answers = {}, order = {}, seen = {} }
  GX.out = o
  -- the 60 seconds count from when the invite really went out (sending can be refused for a while)
  sendThen(function()
    if GX.out == o then o.sentAt = now(); o.expires = o.sentAt + GX.INVITE_TIME + 3 end
  end, "G1", id, placeKey, len, diff, power, codesOf(list))
  self:Print(string.format("You invited your group: |cffffd100%s|r. Waiting for answers.", describe(placeKey, len, diff)), true)
  notify()
  return true
end

function TCF:GroupExpWithdraw()
  local out = GX.out
  if not out then return false end
  GX.out = nil
  send("G4", out.id, "x")
  self:Print("You called off the party expedition invite.", true)
  notify()
  return true
end

-- the players that go: you first, then the ones who accepted, in the order they answered
local function lineup(out)
  local list = { { name = myName(), power = out.power, cats = out.cats, me = true } }
  for _, b in ipairs(out.order) do
    local a = out.answers[b]
    if a and a.ans == "y" and #list < GX.MAX_PLAYERS then list[#list + 1] = { name = a.name, power = a.power, cats = a.cats } end
  end
  return list
end
function TCF:GroupExpLineup() return GX.out and lineup(GX.out) or nil end

local function encodePlayers(list)
  local parts = {}
  for _, p in ipairs(list) do parts[#parts + 1] = p.name .. ":" .. p.power .. ":" .. codesOf(p.cats) end
  return table.concat(parts, ",")
end

-- save the started expedition (both sides use this, so everyone stores the same thing)
local function begin(self, id, placeKey, len, diff, start, seed, players, mine)
  local total = 0
  for _, p in ipairs(players) do total = total + p.power end
  local need = TCF.GroupExpNeed(placeKey, diff, #players)
  local g = { id = id, place = placeKey, len = len, diff = diff, start = start, finish = start + GX.LENGTHS[len][1],
    seed = seed, players = players, power = total, need = need, chance = TCF.GroupExpChance(total, need), mine = mine }
  store(self).group = g
  self.db.stats.groupExpeditionsSent = (self.db.stats.groupExpeditionsSent or 0) + 1
  return g
end

-- Sends the start and saves it. When the group can't get messages right now (sending refused, as in
-- combat in an instance) nothing is saved: it returns false, why, true and sets off as soon as it can,
-- so the starter never has an expedition the others don't know about.
function TCF:GroupExpStartNow()
  local out = GX.out
  if not out then return false end
  local players = lineup(out)
  if #players < 2 then return false, "Nobody has accepted yet." end
  -- your own cats are checked once more (one may have left on a solo expedition meanwhile)
  local list, err = validCats(self, out.cats)
  if not list then return false, err end
  local start, seed = serverNow(), random(1, 1073741823)
  for _, p in ipairs(players) do p.me = nil end
  local text = encodePlayers(players)
  -- 5 players with long names still fit, but a message over the limit loses its last players
  while #("G3;1;" .. out.id .. ";" .. out.place .. ";1;1;" .. start .. ";" .. seed .. ";" .. text) > 250 and #players > 2 do
    table.remove(players)
    text = encodePlayers(players)
  end
  if not rawSend(table.concat({ "G3", VER, out.id, out.place, out.len, out.diff, start, seed, text }, ";")) then
    out.startNow = true
    return false, "Your group can't get addon messages right now (in combat, for example). It sets off as soon as they can.", true
  end
  GX.out = nil
  local g = begin(self, out.id, out.place, out.len, out.diff, start, seed, players, list)
  g.starter = true
  GX.resend = { id = out.id, at = now(), n = 0, asked = {}, text = { out.place, out.len, out.diff, start, seed, text } }
  local names = {}
  for i = 2, #players do names[#names + 1] = players[i].name end
  self:Print(string.format("Your party expedition set out: |cffffd100%s|r with %s (back in %s, %d%% chance).",
    describe(out.place, out.len, out.diff), table.concat(names, ", "), TCF.FormatDuration(GX.LENGTHS[out.len][1]), floor(g.chance / 10 + 0.5)), true)
  if self.PlaySound then self:PlaySound("click") end
  notify(); if self.RefreshAll then self:RefreshAll() end
  return true
end

---------------------------------------------------------------- invited (the others)
-- GX.inv = { id, from (name), fromBase, place, len, diff, power (theirs), cats (theirs), expires,
--   state = "invited" / "accepted" / "over", result }
local muted = {}

function TCF:GroupExpAnswer(yes, cats)
  local inv = GX.inv
  if not inv or (inv.state ~= "invited" and not (yes and inv.state == "accepted")) then return false end
  if not yes then
    inv.state, inv.result = "over", "declined"
    send("G2", inv.id, "n", 0, "-")
    muted[inv.fromBase] = now() + MUTE_AFTER_NO
    notify()
    return true
  end
  if store(self).group then return false, "Your cats are already on a party expedition." end
  local list, err = validCats(self, cats or self:GroupExpDefaultCats())
  if not list then return false, err end
  local again = inv.state == "accepted"
  inv.cats, inv.power = list, self:GroupExpPower(list)
  inv.state = "accepted"
  inv.waitUntil = max(inv.expires, now()) + START_WAIT
  send("G2", inv.id, "y", inv.power, codesOf(list))
  notify()
  if again then return true end     -- a new choice of cats: no second chat line
  GX.repickAt = nil
  local names = {}
  for _, c in ipairs(list) do names[#names + 1] = TCF.CLASS_BY_KEY[c].name end
  self:Print(string.format("You joined %s's party expedition with your %s cat%s. It starts when %s sends it off.",
    inv.from, table.concat(names, ", "), #list == 1 and "" or "s", inv.from), true)
  return true
end

-- the cats picked in the Party view changed after accepting: tell the starter once the clicking stops
function TCF:GroupExpRepick()
  local inv = GX.inv
  if inv and inv.state == "accepted" then GX.repickAt = now() + 1.5 end
end

-- the pending invite, for the prompt and the Expeditions tab
function TCF:GroupExpInviteInfo() return GX.inv, GX.out end

---------------------------------------------------------------- incoming messages
local seen = {}
local function allow(sender)
  if TCF.DR and TCF.DR.Allow then return TCF.DR.Allow(sender) end
  local t = now()
  local s = seen[sender]
  if not s or t - s.t > IN_WINDOW then s = { t = t, n = 0 }; seen[sender] = s end
  s.n = s.n + 1
  return s.n <= IN_MAX
end

local function onInvite(sender, id, place, len, diff, power, codes)
  len, diff, power = tonumber(len), tonumber(diff), tonumber(power)
  local cats = catsOf(codes)
  if not TCF.GroupExpPlace(place) or not GX.LENGTHS[len or 0] or not GX.DIFFS[diff or 0] or not cats then return end
  if not power or power < 0 or power > 1e7 or power ~= floor(power) then return end
  local m = friendNamed(sender)
  if not m then return end                    -- only group members whose cat said hello
  local b = base(sender)
  if muted[b] and now() < muted[b] then send("G2", id, "b", 0, "-"); return end
  muted[b] = nil
  -- one invite at a time: anything else running answers "busy"
  if busy(TCF) then
    if not (GX.inv and GX.inv.id == id) then send("G2", id, "b", 0, "-") end
    return
  end
  GX.inv = { id = id, from = shortName(m.name), fromBase = b, place = place, len = len, diff = diff, power = power, cats = nil,
    theirCats = cats, expires = now() + GX.INVITE_TIME, state = "invited" }
  send("G2", id, "s", 0, "-")                 -- "I got it": the starter waits for my answer
  if TCF.PlaySound then TCF:PlaySound("click") end
  notify()
end

local function onAnswer(sender, id, ans, power, codes)
  local out = GX.out
  if not out or out.id ~= id then return end
  local m = friendNamed(sender)
  if not m then return end
  local b = base(sender)
  if ans == "s" then out.seen[b] = true; return end
  local a = out.answers[b]
  if ans == "y" then
    power = tonumber(power)
    local cats = catsOf(codes)
    if not power or power < 0 or power > 1e7 or power ~= floor(power) or not cats then return end
    if not a then
      a = { name = shortName(m.name) }
      out.answers[b] = a
    end
    local first = a.ans ~= "y"
    a.ans, a.power, a.cats = "y", power, cats
    if first then out.order[#out.order + 1] = b end
  elseif ans == "n" or ans == "b" then
    if a and a.ans == "y" then
      for i, x in ipairs(out.order) do if x == b then table.remove(out.order, i); break end end
    end
    out.answers[b] = { name = shortName(m.name), ans = ans }
  else
    return
  end
  notify()
end

-- a player name from a message: no colour codes, links or textures, no realm
local function cleanName(s)
  s = s:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""):gsub("|T.-|t", ""):gsub("|A.-|a", "")
    :gsub("|H.-|h", ""):gsub("|K.-|k", "")
  return shortName(s)
end
GX.CleanName = cleanName

local function parsePlayers(text)
  if type(text) ~= "string" then return nil end
  local list, n, names = {}, 0, {}
  for entry in text:gmatch("[^,]+") do
    n = n + 1
    if n > GX.MAX_PLAYERS then return nil end
    local name, power, codes = entry:match("^([^:]+):(%d+):(%u+)$")
    power = tonumber(power)
    local cats = catsOf(codes)
    if not name or not power or power > 1e7 or not cats or #name > 48 then return nil end
    name = cleanName(name)
    local b = base(name)
    if name == "?" or not b or names[b] then return nil end   -- an empty name, or a player twice
    names[b] = true
    list[#list + 1] = { name = name, power = power, cats = cats }
  end
  if #list < 2 then return nil end
  return list
end

local function onStart(sender, id, place, len, diff, start, seed, playersText)
  local inv = GX.inv
  local g = store(TCF).group
  if g and g.id == id then return end          -- already have it (a resent start)
  if not inv or inv.id ~= id or base(sender) ~= inv.fromBase then return end
  if g then return end                         -- busy with another one (can't happen when accepted)
  if inv.state == "invited" then
    -- it set off before you answered: the invite goes away
    inv.state, inv.result = "over", "full"
    notify()
    return
  end
  -- a start that came after we stopped waiting (the starter couldn't send for a while) still counts
  local late = inv.state == "over" and inv.result == "nostart"
  if inv.state ~= "accepted" and not late then return end
  len, diff, start, seed = tonumber(len), tonumber(diff), tonumber(start), tonumber(seed)
  if place ~= inv.place or len ~= inv.len or diff ~= inv.diff then return end
  if not start or not seed or start ~= floor(start) or seed ~= floor(seed) then return end
  local t = serverNow()
  if t > 0 and math.abs(start - t) > 3600 then return end   -- a start time that makes no sense
  local players = parsePlayers(playersText)
  if not players or base(players[1].name) ~= inv.fromBase then return end   -- the starter comes first
  local mine = base(myName())
  local found
  for _, p in ipairs(players) do if base(p.name) == mine then found = p end end
  inv.state = "over"
  if not found then
    inv.result = "full"
    TCF:Print(string.format("%s's party expedition set out without you (it takes %d players at most).", inv.from, GX.MAX_PLAYERS), true)
    notify()
    return
  end
  -- our own cats are the ones we accepted with (a cat that left meanwhile still counts here); after a
  -- late start only the ones still free go
  local cats = inv.cats
  if late then
    cats = {}
    for _, c in ipairs(inv.cats or {}) do if validCats(TCF, { c }) then cats[#cats + 1] = c end end
    if #cats == 0 then
      TCF:Print(string.format("%s's party expedition set out late, and your cats had already gone elsewhere.", inv.from), true)
      notify()
      return
    end
  end
  inv.result = "started"
  local g2 = begin(TCF, id, place, len, diff, start, seed, players, cats)
  g2.from = inv.from
  local names = {}
  for _, p in ipairs(players) do if p ~= found then names[#names + 1] = p.name end end
  TCF:Print(string.format("Your party expedition set out: |cffffd100%s|r with %s (back in %s, %d%% chance).",
    describe(place, len, diff), table.concat(names, ", "), TCF.FormatDuration(max(0, g2.finish - t)), floor(g2.chance / 10 + 0.5)), true)
  notify(); if TCF.RefreshAll then TCF:RefreshAll() end
end

local function onCancel(sender, id, reason)
  local inv = GX.inv
  if not inv or inv.id ~= id or base(sender) ~= inv.fromBase or inv.state == "over" then return end
  inv.state, inv.result = "over", "cancel"
  if inv.cats then TCF:Print(string.format("%s called off the party expedition.", inv.from), true) end
  notify()
end

local function onAsk(sender, id)
  -- someone who accepted missed the start: send it again (at most a few times for each player)
  local g = store(TCF).group
  local r = GX.resend
  if not g or g.id ~= id or not g.starter or not r or r.id ~= id then return end
  local b = base(sender)
  if not b then return end
  r.asked[b] = (r.asked[b] or 0) + 1
  if r.asked[b] > MAX_ASKS then return end
  local x = r.text
  send("G3", id, x[1], x[2], x[3], x[4], x[5], x[6])
end

local function onAddon(prefix, text, channel, sender)
  if isSecret(prefix) or prefix ~= PREFIX then return end
  if isSecret(text) or type(text) ~= "string" or text:sub(1, 1) ~= "G" or #text > 255 then return end
  if isSecret(channel) or (channel ~= "PARTY" and channel ~= "RAID" and channel ~= "INSTANCE_CHAT") then return end
  if isSecret(sender) or type(sender) ~= "string" or sender == "" or isMe(sender) then return end
  if not TCF.db then return end
  local f = {}
  for part in (text .. ";"):gmatch("([^;]*);") do f[#f + 1] = part end
  local kind, ver, id = f[1], f[2], f[3]
  if ver ~= VER or type(id) ~= "string" or not id:match("^%x%x%x%x%x%x$") then return end
  if not allow(sender) then return end
  if kind == "G1" and #f == 8 then onInvite(sender, id, f[4], f[5], f[6], f[7], f[8])
  elseif kind == "G2" and #f == 6 then onAnswer(sender, id, f[4], f[5], f[6])
  elseif kind == "G3" and #f == 9 then onStart(sender, id, f[4], f[5], f[6], f[7], f[8], f[9])
  elseif kind == "G4" and #f == 4 then onCancel(sender, id, f[4])
  elseif kind == "G5" and #f == 3 then onAsk(sender, id) end
end
GX.OnAddon = onAddon

---------------------------------------------------------------- claiming
function TCF:GroupExpReady()
  local g = store(self).group
  return g ~= nil and serverNow() >= g.finish
end

function TCF:GroupExpClaim()
  local st = store(self)
  local g = st.group
  if not g or serverNow() < g.finish then return nil end
  st.group = nil
  st.groupDone = (st.groupDone or 0) + 1
  local p = TCF.GroupExpPlace(g.place)
  local name = p and p.name or "a dungeon"
  local players = #(g.players or {})
  local won = TCF.GroupExpRoll(g.seed, g.id) < (g.chance or 0)
  local xp, coins, rolls, chance, extraChance = TCF.GroupExpRewards(g.place, g.len, g.diff, players)
  local canLevel = false
  for _, c in ipairs(g.mine or {}) do
    if TCF.CLASS_BY_KEY[c] then
      if not (self.IsMaxLevel and self:IsMaxLevel(c)) then canLevel = true end
      self:AddClassXP(c, won and xp or floor(xp / 2))
      if self.ClassCount then self:ClassCount(c, "party", 1); self:ClassCount(c, "exp", 1) end
    end
  end
  self.db.stats.groupExpeditions = (self.db.stats.groupExpeditions or 0) + 1
  local label = string.format("Party expedition: %s", name)
  if not won then
    local c = max(1, floor(coins * 0.1))
    self:AddCoins(c)
    self:Print(string.format("|cffff6060Your party expedition to %s failed.|r Your cats came home with %d TapCoins%s. More Power, or an easier difficulty, raises the odds.",
      name, c, canLevel and string.format(" and %d XP each", floor(xp / 2)) or ""), true)
    self:MarkDirty(); self:RefreshAll()
    return false
  end
  self.db.stats.groupExpeditionWins = (self.db.stats.groupExpeditionWins or 0) + 1
  local c = max(1, floor(coins * (0.8 + random() * 0.4) + 0.5))
  self:AddCoins(c)
  self:Print(string.format("|cff20ff20Your party expedition to %s succeeded.|r +%d TapCoins%s.", name, c,
    canLevel and string.format(", +%d XP for each cat", xp) or ""), true)
  local main, extra = TCF.GroupExpChests(g.place, g.diff)
  for _ = 1, rolls do
    if random() < chance then self:AwardChest(main, label, true, g.mine and g.mine[1]) end
  end
  -- (the 4th argument: the cat the chest goes to, once chests belong to a class cat; ignored before)
  if extra and random() < extraChance then self:AwardChest(extra, label, true, g.mine and g.mine[1]) end
  if self.RollSkinSource then
    -- (1.6.0) a skin goes to a cat that went: the one you are playing if it went, else the first
    local owner = g.mine and g.mine[1]
    for _, c in ipairs(g.mine or {}) do if c == self.db.class then owner = c end end
    self:WithOwner(owner, self.RollSkinSource, "expedition", function(x) return x.expedition == "any" end, "Your party brought it home from " .. name, true)
  end
  self:MarkDirty(); self:RefreshAll()
  return true
end

---------------------------------------------------------------- the invite above your cat
-- the one allowed pop-up for this: a small Accept / Decline box just above the screen cat. It never
-- takes the keyboard, shrinks to a smaller box during combat (so the 60 seconds never run out
-- unseen; the invite is in the Expeditions tab too) and sits next to a casino invite when both are
-- open (above it, or below it when the casino invite sits below the cat).
local prompt
local SIZE = { full = { 260, 72, 20 }, small = { 196, 56, 18 } }   -- width, button width, button height
local function buildPrompt()
  local U = TCF.UI
  local f = CreateFrame("Frame", "TapCatForeverGroupExpPrompt", UIParent, U and U.BT)
  f:SetSize(260, 66)
  f:SetFrameStrata("MEDIUM")
  if f.SetBackdrop and U then
    f:SetBackdrop(U.BACKDROP_PANEL)
    f:SetBackdropColor(0.08, 0.06, 0.1, 0.92); f:SetBackdropBorderColor(0.55, 0.8, 1, 1)
  end
  f:EnableMouse(true)
  if f.SetClampedToScreen then f:SetClampedToScreen(true) end
  f.text = U.Text(f, "GameFontHighlightSmall"); f.text:SetPoint("TOP", 0, -8); f.text:SetWidth(246)
  f.yes = U.Button(f, "Accept", 72, 20, function()
    local ok, err = TCF:GroupExpAnswer(true)
    if err then TCF:Print(err, true) end
    TCF:PlaySound("click")
  end)
  f.yes:SetPoint("BOTTOMLEFT", 10, 8)
  f.no = U.Button(f, "Decline", 72, 20, function() TCF:GroupExpAnswer(false); TCF:PlaySound("click") end)
  f.no:SetPoint("LEFT", f.yes, "RIGHT", 6, 0)
  f.left = U.Text(f, "GameFontDisableSmall", nil, "RIGHT"); f.left:SetPoint("BOTTOMRIGHT", -12, 12)
  f:Hide()
  return f
end

local function setSize(small)
  local z = small and SIZE.small or SIZE.full
  prompt.small = small
  prompt:SetWidth(z[1])
  prompt.text:SetWidth(z[1] - 14)
  prompt.yes:SetSize(z[2], z[3]); prompt.no:SetSize(z[2], z[3])
  prompt.yes:ClearAllPoints(); prompt.yes:SetPoint("BOTTOMLEFT", 10, small and 6 or 8)
  prompt.left:ClearAllPoints(); prompt.left:SetPoint("BOTTOMRIGHT", -12, small and 10 or 12)
end

local function num(v) return type(v) == "number" and not isSecret(v) and v or nil end

local function placePrompt(minH)
  prompt:ClearAllPoints()
  local th = prompt.text.GetStringHeight and prompt.text:GetStringHeight()
  local h = (type(th) == "number" and th > 0) and floor(th + 0.5) + (prompt.small and 34 or 40) or minH
  h = max(minH, h)
  prompt:SetHeight(h)
  local hud = TCF.hud
  local dr = _G.TapCatForeverDeathRollPrompt
  if dr and dr:IsShown() then
    -- next to the casino invite: below it when it sits below the cat (the cat is near the top of the
    -- screen), so neither covers the cat
    local drTop = num(dr.GetTop and dr:GetTop())
    local hudTop = hud and hud:IsShown() and num(hud.GetTop and hud:GetTop())
    if drTop and hudTop and drTop < hudTop then
      prompt:SetPoint("TOP", dr, "BOTTOM", 0, -4); prompt.over = "casino-below"
    else
      prompt:SetPoint("BOTTOM", dr, "TOP", 0, 4); prompt.over = "casino"
    end
    return
  end
  prompt.over = "cat"
  if hud and hud:IsShown() then
    local top, ptop = num(hud.GetTop and hud:GetTop()), num(UIParent.GetTop and UIParent:GetTop())
    if top and ptop and top + 22 + h > ptop then
      prompt:SetPoint("TOP", hud, "BOTTOM", 0, -8)
    else
      prompt:SetPoint("BOTTOM", hud, "TOP", 0, 22)
    end
  else prompt:SetPoint("BOTTOM", UIParent, "BOTTOM", 0, 260) end
end

local function inCombat() return InCombatLockdown and InCombatLockdown() and true or false end

local function updatePrompt()
  local inv = GX.inv
  local show = inv and inv.state == "invited"
  if not show then
    if prompt then prompt:Hide() end
    return
  end
  if not prompt then prompt = buildPrompt() end
  local small = inCombat()
  setSize(small)
  if small then
    -- in combat: one short line and smaller buttons
    prompt.text:SetText(string.format("%s invites your cat", inv.from))
  else
    local cats = TCF:GroupExpDefaultCats()
    local catText = #cats == 1 and string.format("Sends your %s cat", TCF.CLASS_BY_KEY[cats[1]].name)
      or string.format("Sends %d of your cats", #cats)
    prompt.text:SetText(string.format("%s invites your cat: %s\n|cffaaaaaa%s. More cats: Expeditions tab.|r",
      inv.from, describe(inv.place, inv.len, inv.diff), catText))
  end
  prompt.left:SetText(string.format("%d s", max(0, floor(inv.expires - now()))))
  placePrompt(small and 46 or 66)
  prompt:Show()
end
GX.UpdatePrompt = updatePrompt

---------------------------------------------------------------- timers
local function tick()
  flushQueue()
  local t = now()
  local inv = GX.inv
  if inv then
    if inv.state == "accepted" and (inCombat() or #outQ > 0) then
      -- we may not hear the start (or our answer is still waiting to go out): keep waiting
      inv.waitUntil = max(inv.waitUntil, t + 5)
    end
    if inv.state == "invited" and t >= inv.expires then
      -- no answer in time counts as a decline
      inv.state, inv.result = "over", "timeout"
      send("G2", inv.id, "n", 0, "-")
      TCF:Print(string.format("The party expedition invite from %s ran out.", inv.from))
      notify()
    elseif inv.state == "accepted" and t >= inv.waitUntil then
      inv.state, inv.result = "over", "nostart"
      TCF:Print(string.format("%s's party expedition didn't start.", inv.from), true)
      notify()
    elseif inv.state == "accepted" and t >= inv.expires + 8 and (inv.asked or 0) < MAX_ASKS and t >= (inv.askAt or 0)
      and not inCombat() and #outQ == 0 then
      inv.asked, inv.askAt = (inv.asked or 0) + 1, t + 8
      send("G5", inv.id)
    elseif inv.state == "over" and t >= (inv.expires or 0) + (inv.result == "nostart" and LATE_KEEP or START_WAIT + 30) then
      GX.inv = nil
      notify()
    end
    if GX.repickAt and t >= GX.repickAt then
      GX.repickAt = nil
      if inv.state == "accepted" then TCF:GroupExpAnswer(true, TCF:GroupExpDefaultCats()) end
    end
  end
  local out = GX.out
  if out then
    local accepted, waiting = 0, 0
    for _, a in pairs(out.answers) do
      if a.ans == "y" then accepted = accepted + 1 end
    end
    local heard = 0
    for _ in pairs(out.answers) do heard = heard + 1 end
    for b in pairs(out.seen) do if not out.answers[b] then waiting, heard = waiting + 1, heard + 1 end end
    -- everyone answered: all who said they got the invite (members on an older version never do; a
    -- few seconds for the "seen" answers, unless every addon friend has been heard from already)
    local acked = out.sentAt and (t >= out.sentAt + ACK_GRACE or heard >= #addonFriends())
    local all = (acked and waiting == 0) or accepted >= GX.MAX_PLAYERS - 1
    if out.startNow or (all and accepted > 0) or (t >= out.expires and accepted > 0) then
      local ok, err, wait = TCF:GroupExpStartNow()
      if not ok and wait then
        -- the group can't hear us right now: try again, up to a few minutes
        if t >= out.expires + LATE_MAX or not inGroup() then
          GX.out = nil
          send("G4", out.id, "n")
          TCF:Print("Your group couldn't get your messages for a few minutes, so the party expedition didn't start.", true)
          notify()
        end
      elseif not ok then
        GX.out = nil
        send("G4", out.id, "n")
        if err then TCF:Print(err, true) end
        notify()
      end
    elseif (all and accepted == 0) or t >= out.expires or not inGroup() then
      GX.out = nil
      send("G4", out.id, "n")
      if next(out.seen) == nil and next(out.answers) == nil and out.sentAt then
        TCF:Print("Nobody joined your party expedition. Group members need the newest TapCatForever to join.", true)
      else
        TCF:Print("Nobody joined your party expedition.", true)
      end
      notify()
    end
  end
  local r = GX.resend
  if r then
    local g = TCF.db and store(TCF).group
    if not g or g.id ~= r.id then GX.resend = nil
    elseif r.n < #RESEND_AT and t - r.at >= RESEND_AT[r.n + 1] then
      r.n = r.n + 1
      local x = r.text
      send("G3", r.id, x[1], x[2], x[3], x[4], x[5], x[6])
    end
  end
  -- the party is back: tell the player once
  local g = TCF.db and TCF.db.expeditions and TCF.db.expeditions.group
  if g and not g.notified and serverNow() >= g.finish then
    g.notified = true
    local p = TCF.GroupExpPlace(g.place)
    TCF:Print(string.format("Your party expedition is back from |cffffd100%s|r. Open the Expeditions tab to claim the rewards.", p and p.name or "?"))
    notify()
  end
  updatePrompt()
end
GX.Tick = tick

local ev = CreateFrame("Frame")
for _, e in ipairs({ "CHAT_MSG_ADDON", "PLAYER_REGEN_ENABLED" }) do pcall(ev.RegisterEvent, ev, e) end
ev:SetScript("OnEvent", function(_, event, a1, a2, a3, a4)
  if not TCF.db then return end
  if event == "CHAT_MSG_ADDON" then onAddon(a1, a2, a3, a4)
  elseif event == "PLAYER_REGEN_ENABLED" then updatePrompt() end
end)
local acc = 0
ev:SetScript("OnUpdate", function(_, e)
  acc = acc + e
  if acc < 0.5 then return end
  acc = 0
  if TCF.db then tick() end
end)
