-- TapCatForever: realm leaderboard (opt-in). It uses the same checkbox as the developer stats
-- (Settings > Help and info, db.ui.shareDev), and nothing is sent or shown without it.
--
-- How it works, all inside the game (addon messages, no internet):
--   * Opted-in players share a short summary of their own cat on the hidden addon channel that
--     DevView.lua joins for them (never shown in chat): a little after login, about every 2 minutes while
--     your taps go up (otherwise every 12 to 15
--     minutes after that, and sooner when something changes a lot (a level, an achievement, a zone,
--     many taps).
--   * Everyone also passes on a few of the entries they know (gossip): after their own summary, and
--     when someone new turns up on the channel. So the board spreads to everyone opted in on the
--     realm, even to players who are never online at the same time.
--   * Each client keeps the board in SavedVariables, account-wide, per realm: at most MAX_ENTRIES
--     players, newest summary wins, nobody seen for 30 days.
--   * Turning sharing off sends a "take me off" message for every character on the account that
--     shared (each sends its own, the next time it logs in, as clients only take R1 from the player
--     it is about). It is saved until it has gone out. Other clients keep a note, pass it on like
--     the board (X1), so players who were offline get it too, and older copies passed on later
--     don't bring the player back. Only the player's own summary, heard from them, clears the note.
--   * Limits per sender: a few messages a minute and a few new players an hour each, so one
--     character can't flood the board. Nothing is signed, so a summary can still be made up.
--   * The board is the Leaderboard tab of the main window (UI_Leaderboard.lua): Total taps, Per class
--     and Professions sections, or the opt-in panel for players who haven't joined.
--
-- Protocol (prefix "TapCatFvr", CHANNEL only, every field checked; older versions ignore it):
--   L1;<Name-Realm>;<class>;<level>;<taps>;<achievements>;<zones>;<version>;<time>   one player's summary
--   L2;<Name-Realm>;<time>;<levels>;<gold>;<skills>[;...]                            the extra fields (1.5.3)
--   R1;<time>                                                                        take me off
--   X1;<Name-Realm>;<time>                                                           that player took themselves off
-- <time> is the realm's clock (GetServerTime), so summaries from different players compare fairly.
-- L2 always follows its player's L1 (own summary and passed on alike) and has its own time: the newest
-- L2 of a player on the board wins, and it never adds a player. Clients that only know L1 skip it.
--   <levels>  the cat level of each class, in LB_CLASSES order, "." between them (0 = no cat)
--   <gold>    Trade Gold earned in total by all the player's cats: digits, or <digits>e<exponent>
--   <skills>  the best skill of any of the player's cats, in LB_SKILLS order, "." between them
-- A later version may add more numbers to a list or more fields at the end; they are skipped.
local ADDON, TCF = ...
local floor, min, max, random = math.floor, math.min, math.max, math.random

local PREFIX = "TapCatFvr"           -- shared with Party.lua and DevView.lua
local CHANNEL = "TapCatFvrShare"     -- DevView.lua's hidden channel
local MAX_ENTRIES = 500              -- players kept per realm
local MAX_REMOVED = 500              -- "take me off" notes kept per realm
local EXPIRE = 30 * 86400            -- players not seen for 30 days drop off
local SKEW = 600                     -- a summary may be this far ahead of our clock (clocks differ a little)
local FIRST_DELAY = 45               -- seconds after login or opting in before our first summary (the channel joins at 20)
local OWN_GAP, OWN_JITTER = 12 * 60, 3 * 60   -- then every 12 to 15 minutes
local OWN_MIN_GAP = 5 * 60           -- a big change sends sooner, but not more often than this
local TAP_GAP = 2 * 60               -- while your taps go up, your summary goes out about every 2 minutes
local RELAY_GAP = 12 * 60            -- other players' entries are passed on at most this often
local CHECK_GAP = 60                 -- how often we look for a big change
local RELAY_BATCH = 3                -- entries passed on at a time
local RELAY_FRESH = 15 * 60          -- an entry heard on the channel this recently is not passed on again
local RELAY_AGAIN = 60 * 60          -- and we pass on the same entry at most once an hour (newcomers aside)
local HELLO_GAP = 2 * 60             -- at most one newcomer batch this often
local SEND_GAP = 3                   -- seconds between our messages
local SEND_BUDGET, SEND_WINDOW = 30, 600     -- at most 30 messages in 10 minutes (an L1 and its L2 are two)
local READ_BUDGET, READ_WINDOW = 600, 60     -- at most 600 messages read a minute; the rest are ignored
local SENDER_MSGS, SENDER_WINDOW = 40, 600   -- at most 40 messages read from one sender in 10 minutes
local SENDER_ADDS, SENDER_ADD_WINDOW = 40, 3600   -- and at most 40 players added or taken off by them an hour
local REMOVE_GAP = 10                -- seconds between two of our "take me off" (unless we shared in between)
local MAX_QUEUE, QUEUE_TTL = 12, 120

TCF.LB_MAX_ENTRIES, TCF.LB_EXPIRE, TCF.LB_SEND_BUDGET, TCF.LB_READ_BUDGET = MAX_ENTRIES, EXPIRE, SEND_BUDGET, READ_BUDGET
TCF.LB_SENDER_MSGS, TCF.LB_SENDER_ADDS = SENDER_MSGS, SENDER_ADDS

-- the order of the numbers in an L2 message: never reorder, only add at the end
local LB_CLASSES = { "WARRIOR", "PALADIN", "HUNTER", "ROGUE", "PRIEST", "SHAMAN", "MAGE", "WARLOCK", "DRUID" }
local LB_SKILLS = { "blacksmithing", "leatherworking", "tailoring", "herbalism", "firstaid", "fishing", "cooking" }
local CLASS_INDEX, SKILL_INDEX = {}, {}
for i, k in ipairs(LB_CLASSES) do CLASS_INDEX[k] = i end
for i, k in ipairs(LB_SKILLS) do SKILL_INDEX[k] = i end
TCF.LB_CLASSES, TCF.LB_SKILLS = LB_CLASSES, LB_SKILLS

local function isSecret(v) return TCF.IsSecret and TCF.IsSecret(v) end
local function plain(v) return type(v) == "string" and not isSecret(v) end
local function now() return GetTime and GetTime() or 0 end

-- the realm's clock in seconds (GetServerTime), or the computer's clock without it
local function serverNow()
  local t
  if GetServerTime then local ok, v = pcall(GetServerTime); if ok then t = v end end
  if (isSecret(t) or type(t) ~= "number") and time then local ok, v = pcall(time); t = ok and v or nil end
  if isSecret(t) or type(t) ~= "number" then return 0 end
  return floor(t)
end

local function optedIn() return TCF.db and TCF.db.ui and TCF.db.ui.shareDev and true or false end

-- not seen for 30 days (by the realm clock `st`; an unknown clock keeps everything)
local function fresh(ts, st) return st == 0 or ts >= st - EXPIRE end

---------------------------------------------------------------- names
-- "Name-Realm" as it travels: a name of letters, a realm without spaces or hyphens
local function validName(s)
  if not plain(s) or #s > 80 then return false end
  local n, r = s:match("^([^%-]+)%-([^%-]+)$")
  if not n or #n < 2 or #n > 48 or #r > 48 then return false end
  return n:find("^[%a\128-\255]+$") ~= nil and r:find("^[^%s%c;|:,]+$") ~= nil
end
TCF.LeaderboardValidName = validName

local function keyOf(full) return TCF.DevFullKey and TCF.DevFullKey(full) or nil end

local function myRealm()
  local r = TCF.DevMyRealm and TCF.DevMyRealm()
  if not plain(r) then return nil end
  r = r:gsub("[%s%-]", "")
  if r == "" or #r > 48 then return nil end
  return r
end

local function myFull()
  local n = UnitName and UnitName("player")
  local r = myRealm()
  if not plain(n) or not r then return nil end
  local full = n .. "-" .. r
  return validName(full) and full or nil
end
local function myKey() local f = myFull(); return f and keyOf(f) end

---------------------------------------------------------------- the saved board
-- TapCatForeverDB.board[realm] = { e = { [key] = entry }, rm = { [key] = time }, rmn = { [key] = "Name-Realm" } }
-- entry = { n = "Name-Realm", c = class, l = level, t = taps, a = achievements, z = zones, v = version, ts = time,
--           d = true when heard from that player (a full board drops second-hand entries first) }
-- rm holds the "take me off" notes, rmn their names (a note without a name, from before 1.5.3 was
-- finished, is kept but not passed on).
local function validEntry(e)
  return type(e) == "table" and validName(e.n) and type(e.c) == "string" and TCF.CLASS_BY_KEY[e.c] ~= nil
    and type(e.l) == "number" and e.l >= 1 and e.l <= 200 and type(e.t) == "number" and e.t >= 0 and e.t < 1e15
    and type(e.a) == "number" and e.a >= 0 and e.a <= 2000 and type(e.z) == "number" and e.z >= 0 and e.z <= 200
    and type(e.v) == "string" and #e.v <= 16 and type(e.ts) == "number" and e.ts > 0
end

-- the extra fields of an L2: x = { lv = { level per LB_CLASSES }, g = Trade Gold, sk = { skill per LB_SKILLS } }
local MAX_GOLD = 1e100
local function validList(l, n, hi)
  if type(l) ~= "table" or #l ~= n then return false end
  for i = 1, n do
    local v = l[i]
    if type(v) ~= "number" or v < 0 or v > hi or v ~= floor(v) then return false end
  end
  return true
end
local function validExtra(x)
  return type(x) == "table" and validList(x.lv, #LB_CLASSES, 200) and validList(x.sk, #LB_SKILLS, 999)
    and type(x.g) == "number" and x.g >= 0 and x.g < MAX_GOLD and x.g == x.g
end
TCF.LeaderboardValidExtra = validExtra

local pruned = {}   -- realm -> true once tidied this session

-- drop anything odd, too old or too far ahead, and keep the newest MAX_ENTRIES
local function prune(b, t)
  local n, list = 0, {}
  for k, e in pairs(b.e) do
    if type(k) ~= "string" or not validEntry(e) or keyOf(e.n) ~= k or e.ts < t - EXPIRE or e.ts > t + SKEW then
      b.e[k] = nil
    else
      if e.x ~= nil and not (validExtra(e.x) and type(e.xts) == "number" and e.xts > 0 and e.xts <= t + SKEW) then e.x, e.xts = nil, nil end
      n = n + 1; list[n] = k
    end
  end
  if n > MAX_ENTRIES then
    table.sort(list, function(x, y) return b.e[x].ts > b.e[y].ts end)
    for i = MAX_ENTRIES + 1, n do b.e[list[i]] = nil end
  end
  local rn, rlist = 0, {}
  for k, ts in pairs(b.rm) do
    if type(k) ~= "string" or type(ts) ~= "number" or ts < t - EXPIRE or ts > t + SKEW then b.rm[k] = nil
    else rn = rn + 1; rlist[rn] = k end
  end
  if rn > MAX_REMOVED then
    table.sort(rlist, function(x, y) return b.rm[x] > b.rm[y] end)
    for i = MAX_REMOVED + 1, rn do b.rm[rlist[i]] = nil end
  end
  if type(b.rmn) ~= "table" then b.rmn = {} end
  for k, nm in pairs(b.rmn) do
    if type(k) ~= "string" or not b.rm[k] or not validName(nm) or keyOf(nm) ~= k then b.rmn[k] = nil end
  end
end

local function board(create)
  local sv = TapCatForeverDB
  if type(sv) ~= "table" then return nil end
  local realm = myRealm()
  if not realm then return nil end
  local rk = realm:lower()
  local all = sv.board
  if type(all) ~= "table" then
    if not create then return nil end
    all = {}; sv.board = all
  end
  local b = all[rk]
  if type(b) ~= "table" then
    if not create then return nil end
    b = {}; all[rk] = b
  end
  if type(b.e) ~= "table" then b.e = {} end
  if type(b.rm) ~= "table" then b.rm = {} end
  if type(b.rmn) ~= "table" then b.rmn = {} end
  if not pruned[rk] then pruned[rk] = true; prune(b, serverNow()) end
  return b
end
TCF.LeaderboardBoard = board

---------------------------------------------------------------- messages
local function numStr(n) return string.format("%.0f", n) end

local function entryText(e)
  local text = string.format("L1;%s;%s;%s;%s;%s;%s;%s;%s", e.n, e.c, numStr(e.l), numStr(min(e.t, 1e14)),
    numStr(e.a), numStr(e.z), e.v, numStr(e.ts))
  return #text <= 250 and text or nil
end
TCF.LeaderboardEntryText = entryText

local function parseEntry(text)
  if not plain(text) or #text > 255 then return nil end
  local n, c, l, t, a, z, v, ts = text:match("^L1;([^;|]+);(%u+);(%d+);(%d+);(%d+);(%d+);([%w%.%-]+);(%d+)$")
  if not n or #l > 3 or #t > 15 or #a > 4 or #z > 3 or #v > 16 or #ts > 11 then return nil end
  local e = { n = n, c = c, l = tonumber(l), t = tonumber(t), a = tonumber(a), z = tonumber(z), v = v, ts = tonumber(ts) }
  return validEntry(e) and e or nil
end
TCF.LeaderboardParse = parseEntry

-- Trade Gold as it travels: whole numbers up to 7 digits, then 7 digits and a power of ten
local function bigText(n)
  n = max(0, floor(n))
  if n < 1e7 then return numStr(n) end
  local e = floor(math.log10(n)) - 6
  local m = floor(n / 10 ^ e)
  if m >= 1e7 then m, e = floor(m / 10), e + 1 end
  return numStr(m) .. "e" .. numStr(e)
end
local function parseBig(s)
  local m, e = s:match("^(%d+)e(%d+)$")
  if m then
    if #m > 7 or #e > 2 then return nil end
    local v = tonumber(m) * 10 ^ tonumber(e)
    return v < MAX_GOLD and v or nil
  end
  if not s:find("^%d+$") or #s > 7 then return nil end
  return tonumber(s)
end
TCF.LeaderboardBigText, TCF.LeaderboardParseBig = bigText, parseBig

-- the L2 for entry e (nil without extra fields)
local function extraText(e)
  local x = e.x
  if not validExtra(x) or type(e.xts) ~= "number" then return nil end
  local lv, sk = {}, {}
  for i = 1, #LB_CLASSES do lv[i] = numStr(x.lv[i]) end
  for i = 1, #LB_SKILLS do sk[i] = numStr(x.sk[i]) end
  local text = "L2;" .. e.n .. ";" .. numStr(e.xts) .. ";" .. table.concat(lv, ".") .. ";" .. bigText(x.g) .. ";" .. table.concat(sk, ".")
  return #text <= 250 and text or nil
end
TCF.LeaderboardExtraText = extraText

-- "1.2.3" -> { 1, 2, 3 }: at least n numbers of up to 3 digits; more (from a later version) are skipped
local function numList(s, n, hi)
  if #s > 120 then return nil end
  local out = {}
  for part in (s .. "."):gmatch("([^%.]*)%.") do
    if not part:find("^%d+$") or #part > 3 then return nil end
    if #out < n then
      local v = tonumber(part)
      if v > hi then return nil end
      out[#out + 1] = v
    end
  end
  return #out == n and out or nil
end

-- an L2: the player's name, the time, and x; nil when anything is off
local function parseExtra(text)
  if not plain(text) or #text > 255 then return nil end
  local n, ts, lv, g, sk = text:match("^L2;([^;|]+);(%d+);([%d%.]+);([%de]+);([%d%.]+)")
  if not n or #ts > 11 or not validName(n) then return nil end
  -- whatever follows must be a new field (";..."), not more of the last one
  local rest = text:sub(#("L2;" .. n .. ";" .. ts .. ";" .. lv .. ";" .. g .. ";" .. sk) + 1)
  if rest ~= "" and rest:sub(1, 1) ~= ";" then return nil end
  local x = { lv = numList(lv, #LB_CLASSES, 200), g = parseBig(g), sk = numList(sk, #LB_SKILLS, 999) }
  ts = tonumber(ts)
  if not ts or ts <= 0 or not validExtra(x) then return nil end
  return n, ts, x
end
TCF.LeaderboardParseExtra = parseExtra

local function parseRemove(text)
  if not plain(text) or #text > 20 then return nil end
  local ts = text:match("^R1;(%d+)$")
  if not ts or #ts > 11 then return nil end
  ts = tonumber(ts)
  return ts and ts > 0 and ts or nil
end

-- a "take me off" passed on: the player's name and the note's time
local function parseRemoval(text)
  if not plain(text) or #text > 100 then return nil end
  local n, ts = text:match("^X1;([^;|]+);(%d+)$")
  if not n or #ts > 11 or not validName(n) then return nil end
  ts = tonumber(ts)
  if not ts or ts <= 0 then return nil end
  return n, ts
end
TCF.LeaderboardParseRemoval = parseRemoval

local function removalText(n, ts)
  local text = "X1;" .. n .. ";" .. numStr(ts)
  return #text <= 250 and text or nil
end

-- Puts one summary on the board. The newest summary of a player wins; one older than what we have,
-- or older than that player's "take me off", never replaces it; your own entry only ever comes from
-- you. `direct`: heard from that player (kept ahead of second-hand entries when the board is full).
-- Returns "added" or "updated", or nil and why not.
local function merge(b, e, t, mine, direct)
  local k = keyOf(e.n)
  if not k then return nil, "name" end
  if mine and k == mine then return nil, "self" end
  if e.ts > t + SKEW then return nil, "future" end
  if e.ts < t - EXPIRE then return nil, "old" end
  local rm = b.rm[k]
  if rm and rm >= e.ts then return nil, "removed" end
  local cur = b.e[k]
  local copy = { n = e.n, c = e.c, l = e.l, t = e.t, a = e.a, z = e.z, v = e.v, ts = e.ts,
    d = (direct or (cur and cur.d)) and true or nil }
  -- the extra fields: the newest of what we had and what came with e (an L2 follows its L1)
  if cur and cur.x then copy.x, copy.xts = cur.x, cur.xts end
  if validExtra(e.x) and type(e.xts) == "number" and e.xts <= t + SKEW and (not copy.xts or e.xts > copy.xts) then
    copy.x, copy.xts = e.x, e.xts
  end
  if cur then
    if cur.ts >= e.ts then return nil, "older" end
    b.e[k] = copy; b.rm[k] = nil; b.rmn[k] = nil
    return "updated"
  end
  local n, oldK, oldTs, sideK, sideTs = 0, nil, nil, nil, nil
  for kk, v in pairs(b.e) do
    n = n + 1
    if not oldTs or v.ts < oldTs then oldK, oldTs = kk, v.ts end
    if not v.d and (not sideTs or v.ts < sideTs) then sideK, sideTs = kk, v.ts end
  end
  if n >= MAX_ENTRIES then
    -- full: the second-hand entry seen longest ago makes room, or the oldest of all when every
    -- entry was heard from its player
    if sideK then oldK, oldTs = sideK, sideTs end
    if e.ts <= oldTs then return nil, "full" end
    b.e[oldK] = nil
  end
  b.e[k] = copy; b.rm[k] = nil; b.rmn[k] = nil
  return "added"
end
TCF.LeaderboardMerge = merge

-- An L2 for key k: only for a player already on the board, newest wins, never older than the
-- player's "take me off", never about yourself. Returns "updated", or nil and why not.
local function mergeExtra(b, k, x, xts, t, mine)
  if mine and k == mine then return nil, "self" end
  if xts > t + SKEW then return nil, "future" end
  if xts < t - EXPIRE then return nil, "old" end
  local rm = b.rm[k]
  if rm and rm >= xts then return nil, "removed" end
  local cur = b.e[k]
  if not cur then return nil, "unknown" end
  if cur.xts and cur.xts >= xts then return nil, "older" end
  cur.x, cur.xts = x, xts
  return "updated"
end
TCF.LeaderboardMergeExtra = mergeExtra

-- a "take me off" for key k at time ts: from the player (R1) or passed on (X1). `name` is kept so
-- the note can be passed on. Returns true when it changed the board.
local function remove(b, k, ts, t, name)
  if ts > t + SKEW or ts < t - EXPIRE then return false end
  local cur = b.e[k]
  if cur and cur.ts > ts then return false end   -- they shared again after this
  name = name and validName(name) and keyOf(name) == k and name or nil
  if b.rm[k] == ts and name and not b.rmn[k] then b.rmn[k] = name end
  if (b.rm[k] or 0) >= ts then return false end
  b.e[k] = nil
  b.rm[k], b.rmn[k] = ts, name
  local n, oldK, oldTs = 0, nil, nil
  for kk, v in pairs(b.rm) do
    n = n + 1
    if not oldTs or v < oldTs then oldK, oldTs = kk, v end
  end
  if n > MAX_REMOVED then b.rm[oldK] = nil; b.rmn[oldK] = nil end
  return true
end
TCF.LeaderboardRemove = remove

---------------------------------------------------------------- your own summary
local function countAchievements()
  local n = 0
  local got = TCF.db and TCF.db.achievements or {}
  for _, a in ipairs(TCF.ACHIEVEMENTS or {}) do if got[a.id] then n = n + 1 end end
  return n
end

function TCF:LeaderboardOwnEntry()
  local db = self.db
  if not db or not TCF.CLASS_BY_KEY[db.class] then return nil end
  local full = myFull()
  if not full then
    -- 1.5.3.3: your own row always shows, even when the realm name can't be read
    local n = UnitName and UnitName("player")
    if not plain(n) or n == "" then n = "You" end
    full = n .. "-" .. (myRealm() or "Realm")
  end
  local cd = self:CD()
  local okS, s = pcall(function() return self.DevSummary and self:DevSummary() end)
  if not okS then s = nil end
  local v = s and s.version or "?"
  if not v:find("^[%w%.%-]+$") then v = "?" end
  local ts = serverNow()
  return { n = full, c = db.class, l = max(1, min(200, floor(cd and cd.level or 1))), t = max(0, floor(db.taps or 0)),
    a = countAchievements(), z = min(200, TCF.DevZonesCleared and TCF.DevZonesCleared() or 0), v = v, ts = ts,
    x = (function() local ok, x = pcall(self.LeaderboardOwnExtra, self); return ok and x or nil end)(), xts = ts }
end

-- every class cat's level, Trade Gold earned by all the cats, and the best skill of any cat
function TCF:LeaderboardOwnExtra()
  local db = self.db
  local lv, sk, g = {}, {}, 0
  for i, ck in ipairs(LB_CLASSES) do
    local cd = type(db.classData) == "table" and db.classData[ck]
    local l = type(cd) == "table" and tonumber(cd.level) or 0
    lv[i] = max(0, min(200, floor(l)))
  end
  for i = 1, #LB_SKILLS do sk[i] = 1 end   -- a skill is at least 1, as ProfSkill says
  if TCF.TradeClasses and self.ProfState then
    for _, ck in ipairs(TCF.TradeClasses(self)) do
      local s = self:ProfState(ck)
      if type(s) == "table" then
        g = g + max(0, tonumber(s.lifetime) or 0)
        for i, key in ipairs(LB_SKILLS) do
          local v = type(s.skill) == "table" and tonumber(s.skill[key]) or 1
          sk[i] = max(sk[i], max(0, min(999, floor(v))))
        end
      end
    end
  end
  return { lv = lv, g = min(g, MAX_GOLD * 0.99), sk = sk }
end

---------------------------------------------------------------- sending
local queue = {}            -- { text, own, at, tries, key (a relay: the player it is about), follow (an L2 after its L1) }
local sentAt = {}           -- GetTime of our recent messages (SEND_BUDGET)
local lastSend = -1e9
local ownAt, lastOwnAt, lastOwn = nil, -1e9, nil
local lastOwnSentAt = -1e9  -- GetTime our own summary last went out
local lastRelayAt = -1e9    -- GetTime we last passed on other players' entries (RELAY_GAP)
local checkAt = nil
local helloAt, helloSince, lastHello = nil, nil, -1e9
local heardAt, relayedAt, senders = {}, {}, {}   -- entry key -> GetTime; direct sender key -> first heard
local readAt = {}           -- GetTime of messages read (READ_BUDGET)
local senderMsgs, senderAdds, lastSweep = {}, {}, -1e9   -- sender key -> GetTimes (per-sender limits)
local lastRemoveAt = -1e9
local signupPending = false
local dirty = false

-- text (an L1) and, right after it, extra (its L2, or nil)
local function enqueue(text, own, key, extra)
  if not text then return false end
  local t = now()
  for i = #queue, 1, -1 do
    if not queue[i].own and t - queue[i].at > QUEUE_TTL then table.remove(queue, i) end
  end
  if own then
    for i = #queue, 1, -1 do if queue[i].own then table.remove(queue, i) end end   -- only the newest summary
    table.insert(queue, 1, { text = text, own = true, at = t, tries = 0 })
    if extra then table.insert(queue, 2, { text = extra, own = true, at = t, tries = 0, follow = true }) end
    return true
  end
  if #queue + (extra and 2 or 1) > MAX_QUEUE then return false end
  queue[#queue + 1] = { text = text, at = t, tries = 0, key = key }
  if extra then queue[#queue + 1] = { text = extra, at = t, tries = 0, key = key, follow = true } end
  return true
end

-- drops the L2 waiting right behind an L1 that won't go out
local function dropFollow(item)
  local nxt = queue[1]
  if nxt and nxt.follow and not item.follow and nxt.key == item.key and nxt.own == item.own then table.remove(queue, 1) end
end

-- the account's characters that shared (db.ui.lbShared) and those still to send "take me off" (db.ui.lbRemove)
local function accountTable(name)
  local ui = TCF.db and TCF.db.ui
  if not ui then return nil end
  if type(ui[name]) ~= "table" then ui[name] = {} end
  return ui[name]
end

-- this character's "take me off" still to send (its time), or nil; old ones are dropped
local function pendingRemoval()
  local ui = TCF.db and TCF.db.ui
  if not ui or type(ui.lbRemove) ~= "table" then return nil end
  local mk = myKey()
  if not mk then return nil end
  local ts = ui.lbRemove[mk]
  if ts == nil then return nil end
  local st = serverNow()
  if type(ts) ~= "number" or (st > 0 and ts < st - EXPIRE) then ui.lbRemove[mk] = nil; return nil end
  return ts
end

-- DevView.lua keeps the hidden channel joined while this is true (opted out, removal not sent yet)
function TCF.LeaderboardRemovePending()
  if optedIn() then return false end
  return pendingRemoval() ~= nil
end

local function underBudget(t)
  for i = #sentAt, 1, -1 do if t - sentAt[i] >= SEND_WINDOW then table.remove(sentAt, i) end end
  return #sentAt < SEND_BUDGET
end

-- Where our messages go (1.5.3.2): your party or raid and your guild, the same addon messages
-- party cats use, plus the hidden channel when the game lets us join and use it (WoW: Forever may
-- not allow addon messages on custom channels). Every route gets the same message.
local function groupRoute()
  if not IsInGroup then return nil end
  local ok, g = pcall(IsInGroup)
  if not ok or not g or isSecret(g) then return nil end
  local inst = LE_PARTY_CATEGORY_INSTANCE and IsInGroup(LE_PARTY_CATEGORY_INSTANCE)
  local home = LE_PARTY_CATEGORY_HOME and IsInGroup(LE_PARTY_CATEGORY_HOME)
  if inst and not isSecret(inst) and not home then return "INSTANCE_CHAT" end
  local okR, raid = pcall(function() return IsInRaid and IsInRaid() end)
  if okR and raid and not isSecret(raid) then return "RAID" end
  return "PARTY"
end
local function guildRoute()
  if not IsInGuild then return false end
  local ok, g = pcall(IsInGuild)
  return ok and g and not isSecret(g) and true or false
end
local function routes()
  local out = {}
  local id = TCF.DevChannelId and TCF.DevChannelId() or 0
  if id > 0 then out[#out + 1] = { "CHANNEL", tostring(id) } end
  local g = groupRoute()
  if g then out[#out + 1] = { g } end
  if guildRoute() then out[#out + 1] = { "GUILD" } end
  return out
end
TCF.LeaderboardRoutes = routes
-- true when there is somewhere to send (kept the old name: it used to mean "in the channel")
local function channel() return #routes() > 0 end
-- send on every route; true when at least one took it
local function sendAll(text)
  if not TCF.DevSendRaw then return false end
  local okAny = false
  for _, r in ipairs(routes()) do
    if TCF.DevSendRaw(text, r[1], r[2]) then okAny = true end
  end
  return okAny
end

-- one message every SEND_GAP seconds, within the budget, only while sharing and in the channel
local function pump(t)
  if #queue == 0 then return end
  if not optedIn() then wipe(queue); return end
  if t - lastSend < SEND_GAP or not underBudget(t) then return end
  if InCombatLockdown and InCombatLockdown() then return end   -- addon messages can be blocked in fights: after
  if not channel() or not TCF.DevSendRaw then return end   -- nowhere to send yet (no group, guild or channel)
  local item = table.remove(queue, 1)
  -- someone else passed this one on while ours waited: no need to send it again
  if item.key and not item.follow and heardAt[item.key] and heardAt[item.key] >= item.at then dropFollow(item); return pump(t) end
  lastSend = t
  if item.own then
    -- counted as shared even when the game reports a failure: it may still have gone out
    lastOwnSentAt = t
    local mk, shared = myKey(), accountTable("lbShared")
    if mk and shared then shared[mk] = true end
  end
  if sendAll(item.text) then
    sentAt[#sentAt + 1] = t
    if item.key and not item.follow then heardAt[item.key], relayedAt[item.key] = t, t end   -- the others online heard it from us
  else
    item.tries = item.tries + 1   -- throttled or blocked: try once or twice more
    if item.tries < 3 then table.insert(queue, 1, item) else dropFollow(item) end
  end
end

-- What is worth passing on: entries and "take me off" notes not heard on the channel since `since`
-- (and, hourly, not passed on by us in the last hour). At most one note, the freshest, goes first;
-- then the freshest entries, plus one older one picked at random so older players keep spreading too.
local function pickRelays(t, since, hourly)
  local b = board(false)
  if not b then return {} end
  local mine, st = myKey(), serverNow()
  local queued = {}
  for _, item in ipairs(queue) do if item.key then queued[item.key] = true end end
  local function wanted(k)
    return k ~= mine and not queued[k] and not (heardAt[k] and heardAt[k] >= since)
      and not (hourly and relayedAt[k] and t - relayedAt[k] < RELAY_AGAIN)
  end
  local out = {}
  local rk, rts
  for k, ts in pairs(b.rm) do
    if b.rmn[k] and fresh(ts, st) and wanted(k) and (not rts or ts > rts or (ts == rts and k < rk)) then rk, rts = k, ts end
  end
  if rk then out[1] = rk end
  local list = {}
  for k, e in pairs(b.e) do
    if fresh(e.ts, st) and wanted(k) then list[#list + 1] = k end
  end
  table.sort(list, function(x, y)
    if b.e[x].ts ~= b.e[y].ts then return b.e[x].ts > b.e[y].ts end
    return x < y
  end)
  local room = RELAY_BATCH - #out
  for i = 1, min(room - 1, #list) do out[#out + 1] = list[i] end
  if room >= 1 and #list >= room then out[#out + 1] = list[random(room, #list)] end
  return out
end

-- queues what pickRelays chose; marked as heard once it actually goes out (pump)
local function relay(t, since, hourly)
  local b = board(false)
  if not b or not channel() then return 0 end
  local n = 0
  for _, k in ipairs(pickRelays(t, since, hourly)) do
    local text, extra
    if b.e[k] then text, extra = entryText(b.e[k]), extraText(b.e[k])
    elseif b.rm[k] and b.rmn[k] then text = removalText(b.rmn[k], b.rm[k]) end
    if text and enqueue(text, nil, k, extra) then n = n + 1 end
  end
  return n
end

-- this character's "take me off", if the channel is there and the limits allow; true once it went out
local function sendRemove(t)
  if not channel() or not TCF.DevSendRaw then return false end
  if InCombatLockdown and InCombatLockdown() then return false end
  -- a second one within REMOVE_GAP only when our own summary went out after the last one
  if t - lastRemoveAt < REMOVE_GAP and lastOwnSentAt < lastRemoveAt then return false end
  if not underBudget(t) then return false end
  lastRemoveAt, lastSend = t, t
  if not sendAll("R1;" .. numStr(serverNow())) then return false end   -- tried again later
  sentAt[#sentAt + 1] = t
  local mk, ui = myKey(), TCF.db and TCF.db.ui
  if mk and ui and type(ui.lbRemove) == "table" then
    ui.lbRemove[mk] = nil
    if next(ui.lbRemove) == nil then ui.lbRemove = nil end
  end
  return true
end

local function sum(l) local n = 0; for _, v in ipairs(l) do n = n + v end; return n end
local function snapshot(e)
  return { c = e.c, l = e.l, a = e.a, z = e.z, t = e.t, lv = e.x and table.concat(e.x.lv, "."), sk = e.x and sum(e.x.sk) or 0,
    g = e.x and e.x.g or 0 }
end

-- our own summary, then (unless noRelay) a few entries the others online haven't heard lately
local function sendOwn(t, noRelay)
  local e = TCF:LeaderboardOwnEntry()
  if not e then return false end
  enqueue(entryText(e), true, nil, extraText(e))
  lastOwnAt, lastOwn = t, snapshot(e)
  ownAt = t + OWN_GAP + random() * OWN_JITTER
  -- passing on others' entries stays on the slow schedule, however often our own taps go out
  if not noRelay and t - lastRelayAt >= RELAY_GAP then lastRelayAt = t; relay(t, t - RELAY_FRESH, true) end
  dirty = true
  return true
end

-- a level (of any class cat), an achievement, a zone, a quarter more taps, 10 more skill points or
-- twice the Trade Gold since our last summary
local function bigChange()
  if not lastOwn then return false end
  local e = TCF:LeaderboardOwnEntry()
  if not e then return false end
  local now_ = snapshot(e)
  return e.c ~= lastOwn.c or e.l ~= lastOwn.l or e.a ~= lastOwn.a or e.z ~= lastOwn.z
    or e.t >= lastOwn.t * 1.25 + 500 or now_.lv ~= lastOwn.lv or now_.sk >= lastOwn.sk + 10
    or now_.g >= lastOwn.g * 2 + 1e6
end

---------------------------------------------------------------- receiving
local function readBudget(t)
  for i = #readAt, 1, -1 do if t - readAt[i] >= READ_WINDOW then table.remove(readAt, i) end end
  if #readAt >= READ_BUDGET then return false end
  readAt[#readAt + 1] = t
  return true
end

-- keeps the times in `list` newer than `window`; returns how many are left
local function within(list, t, window)
  local j = 0
  for i = 1, #list do if t - list[i] < window then j = j + 1; list[j] = list[i] end end
  for i = #list, j + 1, -1 do list[i] = nil end
  return j
end

-- per-sender limits: SENDER_MSGS messages read in SENDER_WINDOW, SENDER_ADDS players added or
-- taken off in SENDER_ADD_WINDOW (only for players other than the sender)
local function senderOk(sk, t)
  if t - lastSweep >= 300 then
    lastSweep = t
    for k, l in pairs(senderMsgs) do if within(l, t, SENDER_WINDOW) == 0 then senderMsgs[k] = nil end end
    for k, l in pairs(senderAdds) do if within(l, t, SENDER_ADD_WINDOW) == 0 then senderAdds[k] = nil end end
  end
  local l = senderMsgs[sk]
  if not l then l = {}; senderMsgs[sk] = l end
  if within(l, t, SENDER_WINDOW) >= SENDER_MSGS then return false end
  l[#l + 1] = t
  return true
end
local function addOk(sk, t)
  local l = senderAdds[sk]
  return not l or within(l, t, SENDER_ADD_WINDOW) < SENDER_ADDS
end
local function noteAdd(sk, t)
  local l = senderAdds[sk]
  if not l then l = {}; senderAdds[sk] = l end
  l[#l + 1] = t
end

-- "Name-Realm" of a sender (the game leaves the realm off for some players on your own realm)
local function senderFull(s)
  if validName(s) then return s end
  if plain(s) and not s:find("-", 1, true) then
    local r = myRealm()
    if r and validName(s .. "-" .. r) then return s .. "-" .. r end
  end
  return nil
end

-- the hidden channel, and (1.5.3.2) your party, raid, instance group and guild
local ROUTE_OK = { CHANNEL = true, PARTY = true, RAID = true, INSTANCE_CHAT = true, GUILD = true }
local function onAddon(prefix, text, chan, sender, chanName)
  if not optedIn() then return end                       -- opted out: nothing is read
  if isSecret(prefix) or prefix ~= PREFIX then return end
  if not plain(text) or not plain(chan) or not plain(sender) or not ROUTE_OK[chan] then return end
  local kind = text:sub(1, 3)
  if kind ~= "L1;" and kind ~= "L2;" and kind ~= "R1;" and kind ~= "X1;" then return end
  if isSecret(chanName) then return end
  if chan == "CHANNEL" and type(chanName) == "string" and chanName ~= "" and not chanName:lower():find(CHANNEL:lower(), 1, true) then return end
  local sk = keyOf(sender)
  if not sk then return end
  local mine = myKey()
  if sk == mine then return end                          -- our own message coming back: costs nothing
  local t = now()
  if not senderOk(sk, t) then return end                 -- one sender can't use up everyone's reading
  if not readBudget(t) then return end
  local b = board(true)
  if not b then return end
  local st = serverNow()
  if kind == "L1;" then
    local e = parseEntry(text)
    if not e then return end
    local k = keyOf(e.n)
    if not k then return end
    local direct = k == sk
    if not direct then
      -- a player who took themselves off comes back only by sharing again themselves
      if b.rm[k] then return end
      if not b.e[k] and not addOk(sk, t) then return end
    end
    local res = merge(b, e, st, mine, direct)
    if res == "added" and not direct then noteAdd(sk, t) end
    local cur = b.e[k]
    if cur and cur.ts == e.ts then heardAt[k] = t end   -- everyone online now has this one
    if res then dirty = true end
    -- someone new on the channel: pass on what they missed (a few of us, not everyone)
    if k == sk and not senders[sk] then
      senders[sk] = t
      local active = 0
      for _, at in pairs(senders) do if t - at < 30 * 60 then active = active + 1 end end
      if not helloAt and t - lastHello >= HELLO_GAP and random() < min(1, 2 / max(1, active - 1)) then
        helloAt, helloSince = t + 5 + random() * 15, t
      end
    end
  elseif kind == "L2;" then
    -- the extra fields of a player already on the board
    local n, ts, x = parseExtra(text)
    if not n then return end
    local k = keyOf(n)
    if not k then return end
    if k ~= sk and b.rm[k] then return end   -- like L1: only the player's own brings them back
    if mergeExtra(b, k, x, ts, st, mine) then dirty = true end
  elseif kind == "R1;" then
    -- the player's own "take me off"
    local ts = parseRemove(text)
    if not ts then return end
    if remove(b, sk, ts, st, senderFull(sender)) then dirty = true end
    if b.rm[sk] == ts then heardAt[sk] = t end           -- everyone online has heard it
  else
    -- a "take me off" passed on by someone else
    local n, ts = parseRemoval(text)
    if not n then return end
    local k = keyOf(n)
    if not k or k == mine then return end
    if k ~= sk and not addOk(sk, t) then return end
    if remove(b, k, ts, st, n) then
      dirty = true
      if k ~= sk then noteAdd(sk, t) end
    end
    if b.rm[k] == ts then heardAt[k] = t end
  end
end

---------------------------------------------------------------- opting in and out
-- the first time this account ever opts in: a Heroic Cache for the current cat, once, forever
local function signupReward()
  local ui = TCF.db and TCF.db.ui
  if not ui or ui.lbSignupChest then return false end
  ui.lbSignupChest = true
  if TCF.AwardChest and TCF.CHEST_BY_KEY and TCF.CHEST_BY_KEY.heroic then
    TCF:AwardChest("heroic", "Thanks for joining the realm leaderboard", true)
  end
  return true
end

function TCF:LeaderboardShareChanged(on)
  local t = now()
  local ui = self.db and self.db.ui
  if on then
    signupReward()
    if ui then ui.lbRemove = nil end   -- sharing again: the summaries to come replace any "take me off"
    ownAt = t + 5 + random() * 5   -- once the channel is joined
    checkAt = t + CHECK_GAP
  else
    wipe(queue)
    ownAt, checkAt, helloAt, lastOwn = nil, nil, nil, nil
    -- Every character on the account that shared sends its own "take me off" (other clients only
    -- take it from that character): saved until it has gone out, at that character's next login
    -- for the others. This one too when it was in the channel and may have shared before this was
    -- kept, unless it already sent one since its last summary.
    if ui then
      local st, mk = serverNow(), myKey()
      local rmList = accountTable("lbRemove")
      if type(ui.lbShared) == "table" then
        for k in pairs(ui.lbShared) do if type(k) == "string" then rmList[k] = st end end
      end
      ui.lbShared = nil
      if mk and channel() and lastOwnSentAt >= lastRemoveAt then rmList[mk] = st end
      if next(rmList) == nil then ui.lbRemove = nil end
    end
    -- straight away while still in the channel; otherwise once DevView.lua has joined it for this
    if pendingRemoval() then sendRemove(t) end
  end
  dirty = true
end

---------------------------------------------------------------- the rows
local SORTS = {
  taps = { "t", "Taps" }, level = { "l", "Cat level" }, ach = { "a", "Achievements" }, zones = { "z", "Zones" },
}
TCF.LB_SORTS = SORTS

-- the boards of the Professions section: { key, name, heading, icon }
local PROF_BOARDS = {
  { "gold", "Trade Gold", "Trade Gold earned by all cats", "INV_Misc_Coin_02" },
  { "blacksmithing", "Blacksmithing", "Best Blacksmithing skill", "Trade_BlackSmithing" },
  { "leatherworking", "Leatherworking", "Best Leatherworking skill", "Trade_LeatherWorking" },
  { "tailoring", "Tailoring", "Best Tailoring skill", "Trade_Tailoring" },
  { "herbalism", "Herbalism", "Best Herbalism skill", "Trade_Herbalism" },
  { "firstaid", "First Aid", "Best First Aid skill", "Spell_Holy_SealOfSacrifice" },
  { "fishing", "Fishing", "Best Fishing skill", "Trade_Fishing" },
  { "cooking", "Cooking", "Best Cooking skill", "INV_Misc_Food_15" },
}
TCF.LB_PROF_BOARDS = PROF_BOARDS

-- A section's value for entry e: nil when e is not on that board.
--   "taps": the sort column. "class": that class cat's level (from L2, or L1 for the class being
--   played). "prof": Trade Gold or a skill (L2 only). Your own row is always there.
local function sectionValue(e, section, sub)
  if section == "class" then
    if e.c == sub then return e.l end   -- the class they play: L1's level is the freshest
    local i = CLASS_INDEX[sub]
    local v = i and e.x and e.x.lv[i]
    if v and (v >= 2 or e.self) then return v end
    return e.self and 1 or nil
  elseif section == "prof" then
    local v
    if sub == "gold" then v = e.x and e.x.g
    else local i = SKILL_INDEX[sub]; v = i and e.x and e.x.sk[i] end
    if v and (v > (sub == "gold" and 0 or 1) or e.self) then return v end
    return e.self and (sub == "gold" and 0 or 1) or nil
  end
  return e[(SORTS[sub] or SORTS.taps)[1]]
end

-- Everyone on your realm's board and you, ranked for a section of the Leaderboard tab:
--   ("taps", sortKey)    sortKey "taps", "level", "ach" or "zones"
--   ("class", classKey)  by that class cat's level, ties by taps
--   ("prof", boardKey)   "gold" or a skill key from LB_SKILLS
-- Each row has the entry's fields, rank, val (the section's number) and self for your own.
-- Empty when you don't share.
function TCF:LeaderboardSection(section, sub)
  local list = {}
  if not optedIn() then return list end
  if section ~= "class" and section ~= "prof" then section = "taps" end
  if section == "taps" and not SORTS[sub] then sub = "taps" end
  if section == "class" and not CLASS_INDEX[sub] then sub = self.db.class end
  if section == "prof" and sub ~= "gold" and not SKILL_INDEX[sub] then sub = "gold" end
  local mine, st = myKey(), serverNow()
  local function add(e, isSelf)
    local r = { n = e.n, c = e.c, l = e.l, t = e.t, a = e.a, z = e.z, v = e.v, ts = e.ts, x = e.x, self = isSelf }
    r.val = sectionValue(r, section, sub)
    if r.val then list[#list + 1] = r end
  end
  local b = board(false)
  if b then
    for k, e in pairs(b.e) do
      if k ~= mine and fresh(e.ts, st) then add(e) end   -- 30 days old during a long session: gone at once
    end
  end
  local own = self:LeaderboardOwnEntry()
  if own then add(own, true) end
  table.sort(list, function(x, y)
    if x.val ~= y.val then return x.val > y.val end
    if x.t ~= y.t then return x.t > y.t end
    if x.l ~= y.l then return x.l > y.l end
    return x.n < y.n
  end)
  for i, r in ipairs(list) do r.rank = i end
  return list
end

-- the Total taps board, ranked by sortKey ("taps", "level", "ach" or "zones")
function TCF:LeaderboardRows(sortKey)
  return self:LeaderboardSection("taps", SORTS[sortKey] and sortKey or "taps")
end

local function ago(ts, t)
  local d = max(0, t - ts)
  if d < 120 then return "just now" end
  if d < 3600 then return floor(d / 60) .. " min ago" end
  if d < 2 * 86400 then return floor(d / 3600) .. " h ago" end
  return floor(d / 86400) .. " days ago"
end
TCF.LeaderboardAgo = ago

-- "Name" for players on your realm, "Name-Realm" otherwise
function TCF.LeaderboardDisplayName(full)
  local n, r = full:match("^([^%-]+)%-(.+)$")
  local mine = myRealm()
  if n and mine and r:lower() == mine:lower() then return n end
  return full
end
TCF.LeaderboardRealm = myRealm
TCF.LeaderboardServerNow = serverNow
TCF.LeaderboardOptedIn = optedIn

-- whether the board changed since the Leaderboard tab last drew it; clear: it is drawing now
function TCF.LeaderboardDirty(clear)
  local d = dirty
  if clear then dirty = false end
  return d
end

---------------------------------------------------------------- the tab
-- The board is the Leaderboard tab of the main window (UI_Leaderboard.lua).
function TCF:ShowLeaderboard()
  if not self.window and self.CreateWindow then self:CreateWindow() end
  local win = self.window
  if not win then return nil end
  win:Show()
  if win.SelectTab and win.TAB_LEADERBOARD then win:SelectTab(win.TAB_LEADERBOARD) end
  return win
end

-- /tcf top: wrapped at login, after every file has added its own commands (Compendium.lua answers
-- any word it doesn't know with the usage line), like DevView.lua's /tcf players
local function wrapSlash()
  if TCF.leaderboardSlash or not (SlashCmdList and SlashCmdList.TAPCATFOREVER) then return end
  TCF.leaderboardSlash = true
  local inner = SlashCmdList.TAPCATFOREVER
  local WORDS = { top = true, leaderboard = true }
  SlashCmdList.TAPCATFOREVER = function(msg, ...)
    local cmd = type(msg) == "string" and msg:lower():match("^%s*(%S*)") or ""
    if WORDS[cmd] and TCF.db then TCF:ShowLeaderboard(); return end
    return inner(msg, ...)
  end
end

---------------------------------------------------------------- events
local ev = CreateFrame("Frame")
for _, e in ipairs({ "CHAT_MSG_ADDON", "PLAYER_LOGIN", "GROUP_ROSTER_UPDATE", "PLAYER_GUILD_UPDATE" }) do pcall(ev.RegisterEvent, ev, e) end
local groupSize = 0

local function onEvent(_, event, a1, a2, a3, a4, _, _, _, a8)
  if event == "PLAYER_LOGIN" then
    wrapSlash()
    if not TCF.db then return end
    board(false)   -- tidies the saved board (old players drop off)
    -- "take me off" still to send for characters on this account: old ones are no longer needed
    local rmList, st = TCF.db.ui.lbRemove, serverNow()
    if type(rmList) == "table" then
      for k, ts in pairs(rmList) do
        if type(k) ~= "string" or type(ts) ~= "number" or (st > 0 and ts < st - EXPIRE) then rmList[k] = nil end
      end
      if next(rmList) == nil then TCF.db.ui.lbRemove = nil end
    elseif rmList ~= nil then
      TCF.db.ui.lbRemove = nil
    end
    if optedIn() then
      -- shared before this version: the sign-up chest once (on the first tick, once the cat is up)
      signupPending = true
      ownAt = now() + FIRST_DELAY + random() * 15
      checkAt = now() + CHECK_GAP
    end
    return
  end
  if (event == "GROUP_ROSTER_UPDATE" or event == "PLAYER_GUILD_UPDATE") and TCF.db then
    -- someone joined your group (or you joined a guild): share your cat and pass on the board soon
    local n = 0
    if GetNumGroupMembers then
      local ok, v = pcall(GetNumGroupMembers)
      if ok and type(v) == "number" and not isSecret(v) then n = v end
    end
    local grew = event == "PLAYER_GUILD_UPDATE" or n > groupSize
    groupSize = n
    if grew and optedIn() then
      local t = now()
      if t - lastOwnAt >= 30 then ownAt = min(ownAt or 1e18, t + 3 + random() * 5) end
      if not helloAt and t - lastHello >= 30 then helloAt, helloSince = t + 6 + random() * 8, t end
    end
    return
  end
  if event == "CHAT_MSG_ADDON" and TCF.db then onAddon(a1, a2, a3, a4, a8) end
end
ev:SetScript("OnEvent", onEvent)

local acc = 0
ev:SetScript("OnUpdate", function(_, e)
  acc = acc + e
  if acc < 1 then return end
  acc = 0
  if not TCF.db then return end
  local t = now()
  if not optedIn() then
    if #queue > 0 then wipe(queue) end
    signupPending = false
    -- this character's "take me off", once DevView.lua has joined the channel for it; then it leaves
    if pendingRemoval() and sendRemove(t) and TCF.DevLeaveIfUnwanted then TCF.DevLeaveIfUnwanted() end
    return
  end
  if signupPending then signupPending = false; signupReward() end
  if ownAt and t >= ownAt then
    if channel() then sendOwn(t) else ownAt = t + 5 end   -- wait for the channel
  end
  if checkAt and t >= checkAt then
    checkAt = t + CHECK_GAP
    if bigChange() and t - lastOwnAt >= OWN_MIN_GAP then ownAt = t
    elseif lastOwn and t - lastOwnAt >= TAP_GAP then
      -- taps went up since our last summary: share them (nothing goes out when nothing changed)
      local e = TCF:LeaderboardOwnEntry()
      if e and e.t > lastOwn.t then ownAt = t end
    end
  end
  if helloAt and t >= helloAt then
    -- a newcomer: our own summary (unless just sent) and what they missed while away
    helloAt, lastHello = nil, t
    if channel() and t - lastOwnAt >= 60 then sendOwn(t, true) end
    relay(t, helloSince or t, false)   -- nothing without the channel
  end
  pump(t)
end)

-- test hooks (the harness)
TCF.LeaderboardTest = {
  state = function() return { queue = queue, sentAt = sentAt, ownAt = ownAt, lastOwnAt = lastOwnAt, helloAt = helloAt,
    checkAt = checkAt, heardAt = heardAt, relayedAt = relayedAt, senders = senders, readAt = readAt,
    lastRemoveAt = lastRemoveAt, lastOwnSentAt = lastOwnSentAt, senderMsgs = senderMsgs, senderAdds = senderAdds } end,
  -- a reload: everything kept only for the session goes
  reset = function()
    wipe(queue); wipe(sentAt); wipe(heardAt); wipe(relayedAt); wipe(senders); wipe(readAt); wipe(pruned)
    wipe(senderMsgs); wipe(senderAdds)
    lastSend, ownAt, lastOwnAt, lastOwn, checkAt = -1e9, nil, -1e9, nil, nil
    helloAt, helloSince, lastHello, lastRemoveAt, lastOwnSentAt, lastSweep = nil, nil, -1e9, -1e9, -1e9, -1e9
    lastRelayAt = -1e9
    signupPending = false
  end,
  setOwnAt = function(t) ownAt = t end,
  event = function(...) onEvent(ev, ...) end,
  prune = prune,
  serverNow = serverNow,
  pickRelays = pickRelays,
  relay = relay,
}
