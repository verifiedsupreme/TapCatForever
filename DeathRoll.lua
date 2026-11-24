-- TapCatForever: death roll (Casino tab, "Death roll" view; the scene is UI_DeathRoll.lua).
-- Two players take turns rolling 1 to N. The first roll is 1 to the start range (1000 by default),
-- each next roll is 1 to the previous result, and whoever rolls a 1 loses.
--
-- Against the house cat (solo): the stake goes through Casino.lua's TCF:CasinoBet, and a win pays
-- 1.9 times the stake through TCF:CasinoPay (rounded to the nearest TapCoin). Who rolls first is a
-- coin flip, so you win exactly half the games; the house keeps 5% of every stake on average
-- (between 3.33% and 6.25% for stakes that aren't a multiple of 10, because of the rounding).
-- tools/tests/test_deathroll.py measures it.
--
-- Against a party member who has the addon: the rolls are real /roll results. The Roll button calls
-- the game's RandomRoll, and both players' addons read the result from the system chat line (the
-- game's own localized RANDOM_ROLL_RESULT text, so it works in every language). Each addon checks
-- its own side: enough TapCoins, turn order, range. The stake is held (taken out of your TapCoins)
-- while the duel runs, and given back if the duel is called off, so nobody can spend it mid-duel.
-- When both addons have seen the 1, each settles its own side with TCF:CasinoSettleDuel: the loser
-- pays the bet and the winner gets the whole bet (DR.DUEL_FEE is 0: duels between friends are even,
-- so they never make or take TapCoins overall).
--
-- Protocol (prefix "TapCatFvr", party/raid/instance channel, every field checked; v = 1):
--   D0;v;id;hi / D0;v;000000;ok  hello (1.6.0): every version with the casino answers "ok" (one answer
--                                covers every hello heard in a short while, and any D0 of ours sent after
--                                a hello arrived counts as the answer); our own hello coming back (its
--                                random id) tells us the name the game uses for us. D0 is never queued.
--   D1;v;id;target;bet;range     challenge (target = the challenged player's name, as the game sends
--                                it with their messages: "Name-Realm")
--   D2;v;id;answer;first         y accept (first: c challenger or t target rolls first),
--                                n decline, b busy, c can't bet that much
--   D3;v;id;reason               called off: x withdrawn, t timeout, s hidden roll text, r reload,
--                                c not enough TapCoins, g left the group, m results didn't match,
--                                e the roll didn't come through; f: I ran out of time, I lose
--   D4;v;id;loser;rolls          I saw the 1 (loser: c or t; rolls: how many rolls in the duel)
-- Fair rules: a turn has 60 seconds. If you don't press Roll in time, you lose the duel: your own
-- addon pays the bet and sends D3 f, and the other side is paid only when that D3 f arrives (it
-- waits 15 seconds longer, then calls the duel off). A /reload, logout, leaving the group or a
-- hidden roll line before the 1 calls the duel off and no coins move.
-- Settling never makes TapCoins: once you have seen the 1 yourself and you are the loser, you pay
-- (when the other addon agrees, when it never answers, or if you leave the group); the winner is
-- paid only when the loser's addon says it saw the same 1. Any failure takes coins out, never in.
local ADDON, TCF = ...
local floor, min, max, random = math.floor, math.min, math.max, math.random

local PREFIX = "TapCatFvr"
local VER = "1"
local GAME = "deathroll"
TCF.DR = TCF.DR or {}
local DR = TCF.DR
DR.GAME = GAME
DR.RANGES = { 100, 1000, 10000 }
DR.DEFAULT_RANGE = 1000
DR.PAY_NUM, DR.PAY_DEN = 19, 10      -- solo: a win pays 1.9x the stake (rounded to the nearest TapCoin)
DR.DUEL_FEE = 0                      -- duels: the % of the loser's bet the table keeps (0: the winner gets the whole bet)
DR.HOUSE_DELAY = 1.2                 -- the house cat rolls this long after your roll
DR.INVITE_TIME = 60                  -- a challenge waits this long for an answer
DR.TURN_TIME = 60                    -- each turn of a duel
DR.DONE_WAIT = 0                     -- (1.6.4) after the 1 each side settles by what it saw, no wait (was 90)
DR.STALL_CALL_OFF = 20               -- (1.6.4) on their turn: after this long with no roll you may call it off
DR.TIMEOUT_FORFEIT = true            -- a turn that runs out without a roll loses the duel (false: it is called off)
local FORFEIT_GRACE = 15             -- the waiting side waits this much longer for the "I ran out of time"
local PRESSED_GRACE = 5              -- Roll was pressed: wait this much longer for its chat line
local RESEND_DONE = 5                -- resend "I saw the 1" this often while waiting
local IN_WINDOW, IN_MAX = 10, 24     -- at most IN_MAX messages per sender in IN_WINDOW seconds
local CHALLENGE_GAP = 3              -- one challenge per sender per this many seconds
local MUTE_AFTER_NO = 20             -- after you decline (or let it run out), that player's challenges wait this long
local OUT_RETRY, OUT_TRIES, OUT_MAX = 2, 15, 8

local HOUSE_NAMES = { "Lucky Paws", "Sir Whiskers", "Madame Mittens", "Dice Kitty", "Captain Purrbeard",
  "Duchess Fluff", "Old Tom", "Velvet Snoop", "Biscuit Boss", "Lady Luck", "Professor Pounce", "Mister Marbles" }

local function isSecret(v) return TCF.IsSecret and TCF.IsSecret(v) end
local function now() return GetTime and GetTime() or 0 end

---------------------------------------------------------------- money (Casino.lua, see the contract)
-- a challenge's bet is checked against each player's own limits (half their TapCoins); this only
-- turns away numbers no one could hold
DR.MSG_BET_MAX = 1e15

function DR.Limits()
  if TCF.CasinoLimits then
    local lo, hi = TCF:CasinoLimits()
    if type(lo) == "number" and type(hi) == "number" then return lo, hi end
  end
  local coins = TCF.db and TCF.db.coins or 0
  return 10, floor(coins / 20) * 10
end

local function validBet(bet)
  bet = tonumber(bet)
  if not bet or bet ~= floor(bet) then return false end
  local lo, hi = DR.Limits()
  return bet >= lo and bet <= hi and (TCF.db.coins or 0) >= bet
end

local function validRange(r)
  for _, v in ipairs(DR.RANGES) do if v == r then return true end end
  return false
end

function DR.Payout(bet) return floor(bet * DR.PAY_NUM / DR.PAY_DEN + 0.5) end
-- what the winner of a duel gets: the loser's bet less the table's fee (none while DR.DUEL_FEE is 0)
function DR.DuelWin(bet)
  if (DR.DUEL_FEE or 0) <= 0 then return bet end
  return bet - max(1, math.ceil(bet * DR.DUEL_FEE / 100))
end

-- the duel stake is held: out of your TapCoins while the duel runs, back when it's called off.
-- The hold is saved, so a /reload or a crash gives it back at the next login.
local function store()
  local db = TCF.db
  if type(db.deathRoll) ~= "table" then db.deathRoll = {} end
  return db.deathRoll
end

local function hold(id, bet)
  local st = store()
  if st.hold then return false end
  if (TCF.db.coins or 0) < bet then return false end
  TCF.db.coins = TCF.db.coins - bet
  st.hold = { id = id, bet = bet }
  if TCF.MarkDirty then TCF:MarkDirty() end
  return true
end

local function release(id)
  local st = store()
  local h = st.hold
  if not h or (id and h.id ~= id) then return 0 end
  st.hold = nil
  TCF.db.coins = (TCF.db.coins or 0) + (tonumber(h.bet) or 0)
  if TCF.MarkDirty then TCF:MarkDirty() end
  return h.bet
end

-- shared with RPS.lua (rock paper scissors uses the same stake hold, so only one game runs at a time)
DR.Store, DR.Hold, DR.Release, DR.ValidBet = store, hold, release, validBet

local function settleDuel(delta, opponent, stake)
  if TCF.CasinoSettleDuel then return TCF:CasinoSettleDuel(delta, opponent, stake) end
  if delta > 0 then TCF:AddCoins(delta) else TCF:SpendCoins(-delta) end
  return true
end

---------------------------------------------------------------- listeners (the scene)
local function notify(ev, ...)
  local fn = DR.OnChange
  if fn then fn(ev, ...) end
  if TCF.MarkDirty then TCF:MarkDirty() end
end

---------------------------------------------------------------- names
local function base(name)
  if type(name) ~= "string" or isSecret(name) or name == "" then return nil end
  local b = name:match("^([^%-]+)")
  return b and b:gsub("%s", ""):lower() or nil
end

-- your name in lower case without the realm: learned from your own messages (Party.lua), as the
-- game may not let an addon read UnitName("player"); nil while it isn't known
local function myBase()
  if TCF.SelfBase then return TCF.SelfBase end
  local n = UnitName and UnitName("player")
  if type(n) ~= "string" or isSecret(n) then return nil end
  return base(n)
end

local function isMe(sender)
  if TCF.PartyIsMe then return TCF.PartyIsMe(sender) end
  local b = base(sender)
  return b ~= nil and b == myBase()
end

-- (1.6.1) a protected answer counts as grouped, like Party.lua's: "unknown" must never end a duel
local function inGroup()
  if not IsInGroup then return false end
  local ok, g = pcall(IsInGroup)
  return ok and g and true or false
end
DR.Base, DR.IsMe, DR.InGroup = base, isMe, inGroup

-- another casino game with a party member or the house cat is running (RPS.lua sets this)
local function otherBusy() return DR.OtherBusy and DR.OtherBusy() or false end
local OTHER_BUSY = "Finish your rock paper scissors game first."

-- duels with friends read the /roll lines in system chat, which the game hides inside dungeons,
-- raids, battlegrounds and arenas (and during boss fights): no duels there
local function chatHidden()
  if C_ChatInfo and C_ChatInfo.InChatMessagingLockdown then
    local ok, v = pcall(C_ChatInfo.InChatMessagingLockdown)
    if ok and v and not isSecret(v) then return true end
  end
  if IsInInstance then
    local ok, inside, kind = pcall(IsInInstance)
    if ok and inside and not isSecret(inside) and kind ~= "none" then return true end
  end
  return false
end
DR.ChatHidden = chatHidden
local NO_DUEL_HERE = "Death rolls with friends don't work inside dungeons, raids, battlegrounds or arenas: the game hides the rolls there."

-- the party member (TCF:PartyMembers) with this name, or nil
local function member(name)
  local b = base(name)
  if not b or not TCF.PartyMembers then return nil end
  for _, m in ipairs(TCF:PartyMembers()) do
    if not m.fake and base(m.name) == b then return m end
  end
end
DR.Member = member

-- Is the opponent still in the group? The addon's own knowledge decides, never UnitName alone: on
-- WoW: Forever the roster's names can come back as protected values, "Unknown" or in another form,
-- so a name that can't be matched means nothing. They are present while Party.lua lists them (it
-- takes a cat off only when a roster it could read in full doesn't have them, twice, 3 seconds
-- apart); once Party.lua has them missing or forgot them, they get OPP_GONE_GRACE more seconds,
-- counted from the last message or roll of theirs, so a roster blink never ends a duel. The roster
-- can only confirm them: a unit whose name was read as a plain string and is theirs says they are
-- here right now, whatever Party.lua thinks. It can also say they went offline, but a loading screen
-- (hearth, portal, zone line) reads as offline for a second or two, so that too waits the grace.
local OPP_GONE_GRACE = 10
DR.OPP_GONE_GRACE = OPP_GONE_GRACE
-- what the roster says about the opponent when it can be read: "here", "offline" or nil (nothing
-- readable is theirs: names protected, "Unknown", nil, another form)
local function rosterSays(d)
  if not (UnitName and GetNumGroupMembers) then return nil end
  local okr, raid = pcall(IsInRaid or function() return false end)
  raid = okr and raid == true
  local ok, count = pcall(GetNumGroupMembers)
  if not ok or isSecret(count) or type(count) ~= "number" then return nil end
  for i = 1, raid and min(40, count) or 4 do
    local unit = (raid and "raid" or "party") .. i
    local okn, n = pcall(UnitName, unit)
    if okn and type(n) == "string" and not isSecret(n) and base(n) == d.oppBase then
      if UnitIsConnected then
        local okc, c = pcall(UnitIsConnected, unit)
        if okc and not isSecret(c) and c == false then return "offline" end
      end
      return "here"
    end
  end
  return nil
end
DR.RosterSays = rosterSays
local function oppPresent(d)
  local t = now()
  local says = rosterSays(d)
  if says == "here" then
    d.oppMissingAt, d.oppOfflineAt = nil, nil
    return true
  elseif says == "offline" then
    local since = d.oppOfflineAt or t
    if (d.oppHeardAt or 0) > since then since = d.oppHeardAt end   -- a message of theirs: the roster is behind
    d.oppOfflineAt = since
    if t - since >= OPP_GONE_GRACE then return false end
  else
    d.oppOfflineAt = nil
  end
  local m = member(d.opp)
  local since
  if m and not m.missing then
    d.oppMissingAt = nil
    return true
  elseif m then
    since = m.missing                 -- Party.lua read a full roster without them
  else
    since = d.oppMissingAt or t       -- Party.lua forgot them: the wait starts now
  end
  d.oppMissingAt = since
  local heard = max(d.oppHeardAt or 0, m and m.heardAt or 0)
  if heard > since then since = heard end
  return t - since < OPP_GONE_GRACE
end
DR.OppPresent = oppPresent
-- a message (or a roll) of the opponent's arrived: they are here right now (RPS.lua calls it too)
local function oppHeard(d) if d then d.oppHeardAt = now() end end
DR.OppHeard = oppHeard

local function chatType()
  local home = LE_PARTY_CATEGORY_HOME and IsInGroup and IsInGroup(LE_PARTY_CATEGORY_HOME)
  local inst = LE_PARTY_CATEGORY_INSTANCE and IsInGroup and IsInGroup(LE_PARTY_CATEGORY_INSTANCE)
  if inst and not home then return "INSTANCE_CHAT" end
  if IsInRaid and IsInRaid() then return "RAID" end
  return "PARTY"
end

-- the name to put in a challenge: the sender name the game gave their messages
function DR.TargetName(m)
  local s = m and m.sender
  if type(s) == "string" and not isSecret(s) and s ~= "" and #s <= 64 and not s:find("[;|]") then return s end
  return m and m.name
end

---------------------------------------------------------------- the /roll line
-- RANDOM_ROLL_RESULT ("%s rolls %d (%d-%d)" in English) turned into a pattern; positional forms
-- ("%1$s", "%2$d") are supported for languages that reorder them. Returns name, roll, low, high.
local rollPat, rollOrder, rollFmt
function DR.RollPattern(fmt)
  local pat, order, argn, i = { "^" }, {}, 0, 1
  while i <= #fmt do
    local c = fmt:sub(i, i)
    if c == "%" then
      local pos, conv, len = fmt:match("^%%(%d)%$([sd])()", i)
      if pos then
        len = len - i
      else
        conv = fmt:match("^%%([sd])", i); len = 2
        if conv then argn = argn + 1; pos = argn end
      end
      if conv then
        order[#order + 1] = tonumber(pos)
        pat[#pat + 1] = conv == "s" and "(.+)" or "(%d+)"
        i = i + len
      elseif fmt:sub(i + 1, i + 1) == "%" then
        pat[#pat + 1] = "%%"; i = i + 2
      else
        pat[#pat + 1] = "%%"; i = i + 1
      end
    else
      pat[#pat + 1] = c:find("[%^%$%(%)%%%.%[%]%*%+%-%?]") and ("%" .. c) or c
      i = i + 1
    end
  end
  pat[#pat + 1] = "$"
  return table.concat(pat), order
end

function DR.ParseRoll(text)
  if type(text) ~= "string" or isSecret(text) or #text > 200 then return nil end
  local fmt = RANDOM_ROLL_RESULT
  if type(fmt) ~= "string" or isSecret(fmt) or not fmt:find("%", 1, true) then fmt = "%s rolls %d (%d-%d)" end
  if fmt ~= rollFmt then rollFmt = fmt; rollPat, rollOrder = DR.RollPattern(fmt) end
  local caps = { text:match(rollPat) }
  if #caps ~= 4 or #rollOrder ~= 4 then return nil end
  local args = {}
  for k, pos in ipairs(rollOrder) do args[pos] = caps[k] end
  local name, roll, lo, hi = args[1], tonumber(args[2]), tonumber(args[3]), tonumber(args[4])
  if not (name and roll and lo and hi) then return nil end
  return name, roll, lo, hi
end

-- the game's /roll; the result comes back as a system chat line (read in onSystem)
local function doRandomRoll(n)
  if type(RandomRoll) == "function" and pcall(RandomRoll, 1, n) then return true end
  local slash = SlashCmdList and SlashCmdList.RANDOM
  if type(slash) == "function" and pcall(slash, tostring(n)) then return true end
  return false
end

---------------------------------------------------------------- solo game against the house cat
local solo           -- the running solo game (also saved in db.deathRoll.solo)
local lastSolo       -- the finished one, for the scene

local function pickHouse()
  local furs, skins, hats = {}, {}, {}
  for _, it in ipairs(TCF.ITEM_LIST or {}) do
    if it.slot == "fur" then furs[#furs + 1] = it.id
    elseif it.slot == "skin" and not it.rainbow then skins[#skins + 1] = it.id
    elseif it.slot == "head" and not it.class and it.source ~= "set" then hats[#hats + 1] = it.id end
  end
  local h = { name = HOUSE_NAMES[random(#HOUSE_NAMES)] }
  if h.name == "Lucky Paws" and TCF.ITEMS and TCF.ITEMS.skin_tuxedo then h.skin = "skin_tuxedo"   -- the classic tuxedo
  elseif #skins > 0 and random() < 0.6 then h.skin = skins[random(#skins)]
  elseif #furs > 0 then h.fur = furs[random(#furs)] end
  if #hats > 0 and random() < 0.5 then h.head = hats[random(#hats)] end
  return h
end
DR.PickHouse = pickHouse

-- a look table (like TCF:GetAppearance) for the house cat
function DR.HouseLook(h)
  local items = TCF.ITEMS or {}
  local look = { fur = items[h and h.fur or ""] or items.fur_ginger }
  if h then
    look.skin = items[h.skin or ""]
    look.head = items[h.head or ""]
  end
  return look
end

local function soloSave()
  store().solo = solo
end

local function soloRoll(who, v)
  local g = solo
  g.rolls[#g.rolls + 1] = { who = who, v = v, hi = g.cur }
  while #g.rolls > 40 do table.remove(g.rolls, 1) end
  local hi = g.cur
  g.cur = v
  g.n = (g.n or 0) + 1
  if v == 1 then
    g.over, g.loser = true, who
    local paid = 0
    if who == "house" then
      paid = DR.Payout(g.bet)
      if TCF.CasinoPay then TCF:CasinoPay(paid, GAME, g.bet) else TCF:AddCoins(paid) end
    end
    g.paid = paid
    local st = store()
    st.soloPlayed = (st.soloPlayed or 0) + 1
    if who == "house" then st.soloWon = (st.soloWon or 0) + 1 end
    lastSolo, solo = g, nil
    st.solo = nil
    notify("roll", "solo", who, v, hi)
    notify("end", "solo", who == "house" and "me" or "house", paid)
    return
  end
  g.turn = who == "me" and "house" or "me"
  g.houseAt = g.turn == "house" and (now() + DR.HOUSE_DELAY) or nil
  soloSave()
  notify("roll", "solo", who, v, hi)
end

function TCF:DeathRollSoloStart(bet, range)
  if not self.db then return false end
  bet, range = tonumber(bet), tonumber(range) or DR.DEFAULT_RANGE
  if solo then return false, "Finish this death roll first." end
  if otherBusy() then return false, OTHER_BUSY end
  local d = DR.duel
  if d and d.state ~= "over" then return false, "Finish your death roll with your friend first." end
  if not validRange(range) then return false, "Pick a roll range." end
  if not bet or not validBet(bet) then
    local lo, hi = DR.Limits()
    if hi < lo then return false, string.format("You need at least %d TapCoins to play.", lo * 2) end
    return false, string.format("Bets go from %s to %s TapCoins right now.", TCF.Commas(lo), TCF.Commas(hi))
  end
  local ok = self.CasinoBet and self:CasinoBet(bet, GAME) or (not self.CasinoBet and self:SpendCoins(bet))
  if not ok then return false, "That bet can't be placed right now." end
  solo = { bet = bet, range = range, cur = range, rolls = {}, n = 0, house = pickHouse(),
           turn = random(2) == 1 and "me" or "house" }
  if solo.turn == "house" then solo.houseAt = now() + DR.HOUSE_DELAY end
  lastSolo = nil
  soloSave()
  notify("start", "solo")
  return true
end

function TCF:DeathRollSoloRoll()
  local g = solo
  if not g or g.over or g.turn ~= "me" then return false end
  soloRoll("me", random(1, g.cur))
  return true
end

function TCF:DeathRollSolo() return solo or lastSolo, solo ~= nil end

-- a death roll is running (with the house cat, or with a friend, invites included): RPS.lua waits
function DR.Busy()
  local d = DR.duel
  return solo ~= nil or (d ~= nil and d.state ~= "over")
end

---------------------------------------------------------------- sending (party/raid channel)
local outQ = {}
local function rawSend(text)
  if not inGroup() then return false end
  local api = C_ChatInfo and C_ChatInfo.SendAddonMessage
  if not api then return false end
  local ok, res = pcall(api, PREFIX, text, chatType())
  -- 12.x returns a result code (0 = sent); older clients return nothing or a boolean
  return ok and (res == nil or res == true or res == 0 or
    (Enum and Enum.SendAddonMessageResult and res == Enum.SendAddonMessageResult.Success)) and true or false
end

local d0SentAt = -1e9   -- when our last hello or answer went out
local function send(kind, ...)
  local parts = { kind, VER, ... }
  local text = table.concat(parts, ";")
  if rawSend(text) then
    if kind == "D0" then d0SentAt = now() end
    return true
  end
  -- a hello or its answer is never kept for later: a stale one would only stand in front of a duel
  -- message (and use up the prefix's sending allowance in a raid)
  if kind == "D0" then return false end
  -- refused (combat in an instance, throttled): try again a few times
  if #outQ < OUT_MAX then outQ[#outQ + 1] = { text = text, at = now() + OUT_RETRY, tries = 1 } end
  return false
end
DR.Send = send

local function flushQueue()
  if #outQ == 0 then return end
  local t = now()
  local q = outQ[1]
  if t < q.at then return end
  if rawSend(q.text) then table.remove(outQ, 1); return end
  q.tries = q.tries + 1
  q.at = t + OUT_RETRY
  if q.tries > OUT_TRIES or not inGroup() then table.remove(outQ, 1) end
end

---------------------------------------------------------------- the multiplayer duel
-- DR.duel = { id, role = "out" (you challenged) or "in", opp (their name), oppBase, bet, range,
--   cur, state = "asking" / "invited" / "rolling" / "done" / "over", turn = "me" / "opp",
--   turnAt, expires, rolls = { { who, v, hi } }, n, loser = "me" / "opp", result, reason }
local muted = {}  -- name -> time their challenges are heard again (after you said no)
local function roleOf(who, d) -- who = "me"/"opp" -> "c" (challenger) / "t" (target)
  if who == "me" then return d.role == "out" and "c" or "t" end
  return d.role == "out" and "t" or "c"
end
local function whoOf(r, d)    -- "c"/"t" -> "me"/"opp"
  if r == "c" then return d.role == "out" and "me" or "opp" end
  return d.role == "out" and "opp" or "me"
end

local REASONS = {
  x = "%s called it off.",
  t = "Time ran out, so the death roll was called off.",
  s = "The game hid the roll results just now (this can happen in combat), so the death roll was called off.",
  r = "%s reloaded or logged out, so the death roll was called off.",
  c = "%s doesn't have enough TapCoins for that bet any more.",
  g = "%s is no longer in your group.",
  m = "The two addons saw different results, so the death roll was called off.",
  e = "The roll didn't come through, so the death roll was called off.",
  f = "%s ran out of time on their turn.",
}
DR.REASONS = REASONS
-- the same when it was your side
DR.REASONS_ME = {
  x = "You called it off.",
  r = "You reloaded or logged out, so the death roll was called off.",
  c = "You don't have enough TapCoins for that bet any more.",
  g = "You left the group, so the death roll was called off.",
  f = "You ran out of time on your turn.",
}

local function saveDuel(d)
  local st = store()
  if d and (d.state == "asking" or d.state == "rolling" or d.state == "done") then
    st.duel = { id = d.id, role = d.role, opp = d.opp, bet = d.bet, range = d.range, state = d.state,
                loser = d.loser, n = d.n, look = nil }
  else
    st.duel = nil
  end
end

local function finish(d, result, reason, by)
  d.state, d.result, d.reason, d.by = "over", result, reason, by
  d.endedAt = now()
  if result ~= "win" and result ~= "lose" then release(d.id) end
  saveDuel(nil)
  notify("end", "duel", result, reason)
end

-- call the duel off: nobody's TapCoins move (the held stake comes back)
local function callOff(reason, tell, by)
  local d = DR.duel
  if not d or d.state == "over" then return end
  if tell then send("D3", d.id, reason) end
  finish(d, "cancel", reason, by or "me")
end
DR.CallOff = callOff

-- pay out: the loser pays the bet, the winner gets it (DR.DuelWin). Only called when this
-- side may settle: the loser once it saw the 1 (or ran out of time), the winner once the loser's
-- addon said so.
local function settle(d, reason)
  if d.settled or d.state == "over" then return end
  d.settled = true
  local won = d.loser == "opp"
  release(d.id)            -- the stake comes back first, then the result moves it for real
  settleDuel(won and DR.DuelWin(d.bet) or -d.bet, d.opp, d.bet)
  local st = store()
  st.duelsPlayed = (st.duelsPlayed or 0) + 1
  if won then st.duelsWon = (st.duelsWon or 0) + 1 end
  d.replies = 0
  finish(d, won and "win" or "lose", reason)
end

-- your turn ran out without a roll: you lose (your own addon pays) and the other side is told
local function forfeit(d)
  d.loser = "me"
  send("D3", d.id, "f")
  settle(d, "f")
end

local function newId()
  return string.format("%06x", random(0, 0xffffff))
end

local function busy()
  local d = DR.duel
  return d and d.state ~= "over"
end

-- challenge a party member (name from TCF:PartyMembers) for bet TapCoins, rolls from range
-- Who in the group can play casino games with you (they run a version with the casino): a "D0"
-- hello goes out when you join a group or open the Death roll view, and every TapCatForever with
-- the casino answers it. Party cats work on older versions too, so a friend's cat can show up while
-- their addon can't take a challenge; then the Casino says so instead of waiting for nothing.
local capable, helloAt, asked = {}, -1e9, {}
-- our hellos carry a random id (made on first use): when one comes back to us, the sender is us
-- (TCF.LearnSelf), which is how this side learns the name the game uses for you
local helloId
local HELLO_GAP, ASK_WAIT, ASK_AGAIN, FORCE_GAP = 10, 6, 30, 2
local helloTry = -1e9
-- true when a hello went out
local function sayHello(force)
  if not inGroup() then return false end
  local t = now()
  if not force and t - helloAt < HELLO_GAP then return false end
  if t - helloTry < FORCE_GAP then return false end   -- the game just refused one: not every frame
  helloTry = t
  helloId = helloId or newId()
  if not send("D0", helloId, "hi") then return false end
  helloAt = t
  return true
end
DR.SayHello = sayHello
-- ask a friend's addon (a hello) unless it already answered or we asked a moment ago; the wait for
-- an answer only starts once the hello really went out
function DR.AskFriend(name)
  local b = base(name)
  if not b or capable[b] then return end
  if asked[b] and now() - asked[b] < ASK_AGAIN then return end
  if sayHello(true) then asked[b] = now() end
end
-- Answering hellos: one "ok" covers every hello heard in a short while. It goes out after a short
-- random wait, never sooner than OK_GAP after our last one, and not at all when a D0 of ours went out
-- after the first of those hellos arrived (everyone who said hello has heard that one). So a roster
-- change in a raid costs each addon one hello and at most one answer.
local OK_GAP, OK_WAIT = 3, 1.2
local okDue, okSince, okSentAt = nil, nil, -1e9
local function heardHello()
  if okDue then return end
  local t = now()
  okSince = t
  okDue = max(t + 0.3 + random() * OK_WAIT, okSentAt + OK_GAP)
end
local function answerHellos()
  if not okDue or now() < okDue then return end
  if not inGroup() or d0SentAt >= okSince then okDue = nil; return end
  if send("D0", "000000", "ok") then
    okSentAt, okDue = now(), nil
  else
    okDue = now() + 2   -- refused (throttled, combat in an instance): try again in a moment
  end
end
DR.HelloState = function() return okDue, d0SentAt, okSentAt end
-- true: their addon answered; false: asked a while ago and no answer (older version); nil: not known yet
function TCF:CasinoCanPlay(name)
  local b = base(name)
  if not b then return nil end
  if capable[b] then return true end
  if asked[b] and now() - asked[b] > ASK_WAIT then return false end
  return nil
end
-- a short line about a friend for the Casino's friend view
function DR.FriendStatus(name)
  local can = TCF:CasinoCanPlay(name)
  if can then return "Ready to play", "ready" end
  if can == false then return "Their TapCatForever didn't answer (they need the newest version)", "old" end
  return "Checking their TapCatForever...", "checking"
end
-- checks a friend before a challenge: true when they can play, else false and the reason
function DR.CheckFriend(name)
  local can = TCF:CasinoCanPlay(name)
  if can then return true end
  local b = base(name)
  local shown = (type(name) == "string" and name:match("^([^%-]+)")) or "Your friend"
  if can == false then
    DR.AskFriend(name)   -- ask again now and then: they may have updated or come back
    return false, shown .. "'s TapCatForever didn't answer. They need the newest TapCatForever for casino games with friends (party cats work on older versions, which is why you can see their cat)."
  end
  DR.AskFriend(name)
  return false, "Checking " .. shown .. "'s TapCatForever. Try again in a few seconds."
end

function TCF:DeathRollChallenge(name, bet, range)
  if not self.db then return false end
  bet, range = tonumber(bet), tonumber(range) or DR.DEFAULT_RANGE
  if busy() then return false, "You already have a death roll going." end
  if solo then return false, "Finish your death roll with the house cat first." end
  if otherBusy() then return false, OTHER_BUSY end
  if not inGroup() then return false, "Join a party or raid with a friend who has TapCatForever." end
  if InCombatLockdown and InCombatLockdown() then return false, "Death rolls can't start in combat." end
  if chatHidden() then return false, NO_DUEL_HERE end
  local m = member(name)
  if not m or isMe(m.name) then return false, "Pick a friend in your group who has TapCatForever." end
  -- your /roll lines are told apart by your name: it must be known first (learned from your own
  -- messages coming back, which takes a moment after joining a group)
  if not myBase() then
    sayHello(true)
    return false, "Your TapCatForever is still getting your name from the group. Try again in a few seconds."
  end
  local okFriend, why = DR.CheckFriend(m.name)
  if not okFriend then return false, why end
  if not validRange(range) then return false, "Pick a roll range." end
  if not bet or not validBet(bet) then
    local lo, hi = DR.Limits()
    return false, string.format("Bets go from %s to %s TapCoins right now.", TCF.Commas(lo), TCF.Commas(max(lo, hi)))
  end
  local d = { id = newId(), role = "out", opp = m.name, oppBase = base(m.name), bet = bet, range = range,
              cur = range, state = "asking", expires = now() + DR.INVITE_TIME, rolls = {}, n = 0 }
  DR.duel = d
  saveDuel(d)   -- a /reload while waiting withdraws the challenge (restore tells them)
  -- their name exactly as the game gave it with their messages: their addon matches it against the
  -- name it learned from its own messages
  send("D1", d.id, DR.TargetName(m), bet, range)
  notify("state", "duel")
  return true
end

-- answer the challenge you were sent (accept = true / false)
function TCF:DeathRollAnswer(accept)
  local d = DR.duel
  if not d or d.state ~= "invited" then return false end
  if not accept then
    send("D2", d.id, "n", "-")
    muted[d.oppBase or ""] = now() + MUTE_AFTER_NO
    finish(d, "declined", nil, "me")
    return true
  end
  if solo then return false, "Finish your death roll with the house cat first." end
  if otherBusy() then
    send("D2", d.id, "b", "-")
    finish(d, "cancel", "x", "me")
    return false, OTHER_BUSY
  end
  if chatHidden() then
    send("D2", d.id, "b", "-")
    finish(d, "cancel", "s", "me")
    return false, NO_DUEL_HERE
  end
  if not validBet(d.bet) or not hold(d.id, d.bet) then
    send("D2", d.id, "c", "-")
    finish(d, "cancel", "c", "me")
    return false, "You don't have enough TapCoins for that bet any more."
  end
  local first = random(2) == 1 and "c" or "t"
  d.state, d.turn, d.turnAt = "rolling", whoOf(first, d), now()
  d.first = d.turn
  send("D2", d.id, "y", first)
  saveDuel(d)
  notify("state", "duel")
  return true
end

-- (1.6.4) their turn and nothing came for a while: you may call the duel off (both bets come back).
-- Only while it's their turn, so nobody can leave a duel they are about to lose on their own turn.
function DR.CanCallOff()
  local d = DR.duel
  return d ~= nil and d.state == "rolling" and d.turn == "opp" and now() - (d.turnAt or 0) >= DR.STALL_CALL_OFF
end
function TCF:DeathRollCallOff()
  if not DR.CanCallOff() then return false end
  callOff("x", true)
  return true
end

-- withdraw your challenge before it's answered
function TCF:DeathRollWithdraw()
  local d = DR.duel
  if not d or d.state ~= "asking" then return false end
  callOff("x", true)
  return true
end

-- your roll in a duel: the game's /roll 1-N; the result arrives as a system chat line
function TCF:DeathRollRoll()
  local d = DR.duel
  if not d or d.state ~= "rolling" or d.turn ~= "me" then return false end
  if d.rolledAt and now() - d.rolledAt < 2 and d.rolledHi == d.cur then return false end  -- no double clicks
  d.rolledAt, d.rolledHi = now(), d.cur
  if not doRandomRoll(d.cur) then
    callOff("e", true)
    return false
  end
  return true
end

function TCF:DeathRollDuel() return DR.duel end

---------------------------------------------------------------- incoming addon messages
local seen = {}   -- sender -> { t, n, lastChallenge }
local function allow(sender)   -- shared with RPS.lua (DR.Allow): one budget per sender
  local t = now()
  local s = seen[sender]
  if not s then
    local count = 0
    for k, v in pairs(seen) do
      if t - v.t > IN_WINDOW then seen[k] = nil else count = count + 1 end
    end
    if count >= 60 then return false end
    s = { t = t, n = 0 }
    seen[sender] = s
  end
  if t - s.t > IN_WINDOW then s.t, s.n = t, 0 end
  s.n = s.n + 1
  return s.n <= IN_MAX, s
end

DR.Allow = allow
local function fromOpp(d, sender) return d and base(sender) == d.oppBase end

local function onChallenge(sender, id, target, bet, range, s)
  if not isMe(target) then return end
  bet, range = tonumber(bet), tonumber(range)
  if not bet or bet ~= floor(bet) or bet < 1 or bet > DR.MSG_BET_MAX or not validRange(range) then return end
  local t = now()
  if s.lastChallenge and t - s.lastChallenge < CHALLENGE_GAP then return end
  s.lastChallenge = t
  local b = base(sender)
  if muted[b] and t < muted[b] then return end
  muted[b] = nil
  local m = member(sender)
  if not m then return end      -- only group members whose cat we know (they said hello)
  local d = DR.duel
  if d and d.state ~= "over" then
    if d.id ~= id then send("D2", id, "b", "-") end
    return
  end
  if solo or otherBusy() or (InCombatLockdown and InCombatLockdown()) or chatHidden() then send("D2", id, "b", "-"); return end
  if not validBet(bet) then
    send("D2", id, "c", "-")
    DR.duel = { id = id, role = "in", opp = m.name, oppBase = base(m.name), bet = bet, range = range, cur = range,
                state = "over", result = "toohigh", rolls = {}, n = 0, endedAt = t }
    notify("end", "duel", "toohigh")
    return
  end
  DR.duel = { id = id, role = "in", opp = m.name, oppBase = base(m.name), bet = bet, range = range, cur = range,
              state = "invited", expires = t + DR.INVITE_TIME, rolls = {}, n = 0 }
  if TCF.PlaySound then TCF:PlaySound("click") end
  notify("invite", "duel")
end

local function onAnswer(d, answer, first)
  if d.state ~= "asking" then
    -- an accept after we gave up waiting: tell them (once) it's off, so their stake comes back
    if answer == "y" and d.state == "over" and d.result ~= "win" and d.result ~= "lose" and not d.toldOff then
      d.toldOff = true
      send("D3", d.id, d.reason or "t")
    end
    return
  end
  if answer == "y" then
    if first ~= "c" and first ~= "t" then return end
    if not validBet(d.bet) or not hold(d.id, d.bet) then
      send("D3", d.id, "c")
      finish(d, "cancel", "c", "me")
      return
    end
    d.state, d.turn, d.turnAt = "rolling", whoOf(first, d), now()
    d.first = d.turn
    saveDuel(d)
    if TCF.PlaySound then TCF:PlaySound("click") end
    notify("state", "duel")
    -- their first roll can beat their "accept" here: play the lines we kept back
    local early = d.early
    d.early = nil
    for _, text in ipairs(early or {}) do
      if DR.duel == d and d.state == "rolling" then DR.OnSystem(text) end
    end
  elseif answer == "n" then finish(d, "declined", nil, "opp")
  elseif answer == "b" then finish(d, "busy", nil, "opp")
  elseif answer == "c" then finish(d, "toohigh", nil, "opp") end
end

local function onDone(d, loser, n)
  local who = whoOf(loser, d)
  n = tonumber(n)
  if not n then return end
  if d.state == "rolling" then
    if who == "opp" then
      -- (1.6.4) they saw their own 1 before our chat line came: their word that they lost is enough
      d.loser, d.n = "opp", max(d.n or 0, n)
      d.state, d.doneAt = "done", now()
      settle(d)
    else
      d.peerDone = { who = who, n = n }    -- they say we rolled the 1: only our own chat line decides
      d.doneAt = d.doneAt or now()
    end
  elseif d.state == "done" then
    settle(d)
  elseif d.state == "over" and (d.result == "win" or d.result == "lose") then
    -- they missed our message (a /reload while waiting): say it once more
    d.replies = (d.replies or 0) + 1
    if d.replies <= 3 then send("D4", d.id, roleOf(d.loser, d), d.n) end
  end
end

local function onAddon(prefix, text, channel, sender)
  if isSecret(prefix) or prefix ~= PREFIX then return end
  if isSecret(text) or type(text) ~= "string" or text:sub(1, 1) ~= "D" or #text > 200 then return end
  if isSecret(channel) or (channel ~= "PARTY" and channel ~= "RAID" and channel ~= "INSTANCE_CHAT") then return end
  if isSecret(sender) or type(sender) ~= "string" or sender == "" then return end
  local kind, ver, id, a, b, c = text:match("^(D%d);(%d+);(%x%x%x%x%x%x);([^;]*);?([^;]*);?([^;]*)$")
  if not kind or ver ~= VER then return end
  if kind == "D0" and a == "hi" and helloId and id == helloId then
    if TCF.LearnSelf then TCF.LearnSelf(sender) end   -- our own hello came back
    return
  end
  if isMe(sender) then return end
  local ok, s = allow(sender)
  if not ok then return end
  local sb = base(sender)
  if sb then capable[sb] = now(); asked[sb] = nil end
  local d = DR.duel
  if d and d.state ~= "over" and fromOpp(d, sender) then oppHeard(d) end
  if kind == "D0" then
    -- any D0 shows their addon can play (above); a hello also wants to hear from us
    if a == "hi" then heardHello() end
    return
  end
  if kind == "D1" then
    if a ~= "" and b ~= "" and c ~= "" then onChallenge(sender, id, a, b, c, s) end
    return
  end
  if not d or d.id ~= id or not fromOpp(d, sender) then return end
  if kind == "D2" then
    if d.role == "out" then onAnswer(d, a, b) end
  elseif kind == "D3" then
    if REASONS[a] and d.state ~= "over" then
      if a == "f" and (d.state == "rolling" or (d.state == "done" and d.loser == "opp")) then
        -- they ran out of time on their turn and paid their bet: you win
        d.loser = "opp"
        settle(d, "f")
        return
      end
      if d.state == "invited" and a == "t" then muted[d.oppBase or ""] = now() + MUTE_AFTER_NO end
      finish(d, "cancel", a, "opp")
    end
  elseif kind == "D4" then
    if (a == "c" or a == "t") and (d.state == "rolling" or d.state == "done" or d.state == "over") then onDone(d, a, b) end
  end
end
DR.OnAddon = onAddon

---------------------------------------------------------------- the /roll lines
local function onSystem(text)
  local d = DR.duel
  if not d then return end
  if d.state == "asking" and not isSecret(text) and type(text) == "string" then
    -- the other player may roll first as soon as they accept, and that line can arrive before their
    -- "accept" message: keep their last few roll lines until the answer comes
    local name = DR.ParseRoll(text)
    if name and base(name) == d.oppBase then
      d.early = d.early or {}
      if #d.early >= 3 then table.remove(d.early, 1) end
      d.early[#d.early + 1] = text
    end
    return
  end
  if d.state ~= "rolling" then return end
  -- a protected line (or one that isn't text at all: a protected value on a client without
  -- issecretvalue) can't be read: nobody is to blame
  if isSecret(text) or (text ~= nil and type(text) ~= "string") then callOff("s", true); return end
  local name, v, lo, hi = DR.ParseRoll(text)
  if not name then return end
  local b = base(name)
  local mb = myBase()
  -- (a duel only starts once your name is known: a roll is never guessed to be yours, as someone
  -- else in the group may /roll the same range at the same moment)
  local who = (mb and b == mb) and "me" or (b == d.oppBase and "opp") or nil
  if not who or who ~= d.turn then return end          -- not this player's turn: not part of the duel
  if lo ~= 1 or hi ~= d.cur or v < 1 or v > hi then return end   -- a different /roll
  if who == "opp" then oppHeard(d) end
  d.rolls[#d.rolls + 1] = { who = who, v = v, hi = hi }
  while #d.rolls > 40 do table.remove(d.rolls, 1) end
  d.n = d.n + 1
  d.cur = v
  if v == 1 then
    -- (1.6.4) settled by what this side saw, at once: the loser pays, the winner is paid. The other
    -- addon still hears "I saw the 1" (older versions wait for it before they settle).
    d.state, d.loser, d.doneAt, d.sentDoneAt = "done", who, now(), now()
    send("D4", d.id, roleOf(who, d), d.n)
    notify("roll", "duel", who, v, hi)
    settle(d)
    return
  end
  d.turn = who == "me" and "opp" or "me"
  d.turnAt = now()
  saveDuel(d)
  notify("roll", "duel", who, v, hi)
end
DR.OnSystem = onSystem

---------------------------------------------------------------- timers
local function tick()
  local t = now()
  flushQueue()
  answerHellos()
  local g = solo
  if g and not g.over and g.turn == "house" and g.houseAt and t >= g.houseAt then
    g.houseAt = nil
    soloRoll("house", random(1, g.cur))
  end
  local d = DR.duel
  if not d or d.state == "over" then return end
  if d.state == "asking" and t >= d.expires then
    callOff("t", true)
  elseif d.state == "invited" and t >= d.expires then
    send("D2", d.id, "n", "-")
    muted[d.oppBase or ""] = t + MUTE_AFTER_NO
    finish(d, "expired", nil, "me")
  elseif d.state == "rolling" then
    if not inGroup() then callOff("g", false)
    elseif not oppPresent(d) then callOff("g", false, "opp")
    elseif d.turn == "me" then
      local late = t - d.turnAt
      if d.rolledAt and d.rolledAt >= d.turnAt then
        -- Roll was pressed but its line never came: nobody is to blame
        if late >= DR.TURN_TIME + PRESSED_GRACE then callOff("e", true) end
      elseif late >= DR.TURN_TIME then
        if DR.TIMEOUT_FORFEIT then forfeit(d) else callOff("t", true) end
      end
    elseif t - d.turnAt >= DR.TURN_TIME + (DR.TIMEOUT_FORFEIT and FORFEIT_GRACE or 0) then
      callOff("t", true)
    end
  elseif d.state == "done" then
    -- after the 1 nothing calls the duel off on this side but the other addon (D3, or a result
    -- that doesn't match): when the wait runs out, the loser pays and the winner gets its own
    -- stake back, never the other way round
    -- (1.6.4) only a duel restored after a /reload sits here: it settles by what was seen
    send("D4", d.id, roleOf(d.loser, d), d.n)
    settle(d)
  end
end
DR.Tick = tick

---------------------------------------------------------------- login: finish what a /reload interrupted
local function restore()
  local st = store()
  -- a solo game goes on where it stopped
  if type(st.solo) == "table" and not solo then
    local g = st.solo
    if tonumber(g.bet) and tonumber(g.cur) and g.cur >= 1 and type(g.rolls) == "table" and type(g.house) == "table" then
      solo = g
      if g.turn == "house" then g.houseAt = now() + DR.HOUSE_DELAY end
    else
      st.solo = nil
    end
  end
  -- a duel: if we had already seen the 1, keep waiting for the other addon to agree;
  -- anything else is called off and the held stake comes back
  local sd = st.duel
  if type(sd) == "table" and sd.state == "done" and st.hold and st.hold.id == sd.id
     and (sd.loser == "me" or sd.loser == "opp") and tonumber(sd.n) then
    DR.duel = { id = sd.id, role = sd.role, opp = sd.opp, oppBase = base(sd.opp), bet = sd.bet, range = sd.range,
                cur = 1, state = "done", loser = sd.loser, n = sd.n, rolls = {}, doneAt = now(), sentDoneAt = now() - RESEND_DONE,
                restored = true }
    return
  end
  if type(sd) == "table" and type(sd.id) == "string" then
    DR.reloadCancel = { id = sd.id, opp = sd.opp }   -- told once we're back in the group
  end
  st.duel = nil
  if st.hold then
    local back = release()
    if back > 0 then DR.refunded = back end
  end
end

---------------------------------------------------------------- events
local ev = CreateFrame("Frame")
DR.frame = ev
for _, e in ipairs({ "CHAT_MSG_ADDON", "CHAT_MSG_SYSTEM", "PLAYER_LOGIN", "PLAYER_ENTERING_WORLD", "GROUP_ROSTER_UPDATE" }) do
  pcall(ev.RegisterEvent, ev, e)
end
if C_ChatInfo and C_ChatInfo.RegisterAddonMessagePrefix then pcall(C_ChatInfo.RegisterAddonMessagePrefix, PREFIX) end

local restored = false
ev:SetScript("OnEvent", function(_, event, a1, a2, a3, a4)
  if not TCF.db then return end
  if not restored then restored = true; restore() end
  if event == "CHAT_MSG_ADDON" then onAddon(a1, a2, a3, a4)
  elseif event == "CHAT_MSG_SYSTEM" then onSystem(a1)
  elseif event == "PLAYER_ENTERING_WORLD" then
    sayHello(false)
  elseif event == "GROUP_ROSTER_UPDATE" then
    sayHello(false)
    -- leaving the group calls off a duel before the 1; after it (state "done") the duel settles
    -- by what this side saw, so a quick /leave can't undo a loss
    local d = DR.duel
    if d and d.state ~= "over" and d.state ~= "done" and not inGroup() then callOff("g", false) end
  end
end)

local acc = 0
ev:SetScript("OnUpdate", function(_, elapsed)
  acc = acc + elapsed
  if acc < 0.2 then return end
  acc = 0
  if not TCF.db then return end
  if not restored then restored = true; restore() end
  local rc = DR.reloadCancel
  if rc and inGroup() then
    DR.reloadCancel = nil
    send("D3", rc.id, "r")   -- retried by the queue if the game refuses it right now
  end
  tick()
end)
