-- TapCatForever: realm leaderboard (opt-in). It uses the same checkbox as the developer stats
-- (Settings > Help and info, db.ui.shareDev), and nothing is sent or shown without it.
--
-- How it works, all inside the game (addon messages, no internet):
--   * Opted-in players share a short summary of their own cat on the hidden addon channel that
--     DevView.lua joins for them (never shown in chat): a little after login, about every 12 to 15
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
--
-- Protocol (prefix "TapCatFvr", CHANNEL only, every field checked; older versions ignore it):
--   L1;<Name-Realm>;<class>;<level>;<taps>;<achievements>;<zones>;<version>;<time>   one player's summary
--   R1;<time>                                                                        take me off
--   X1;<Name-Realm>;<time>                                                           that player took themselves off
-- <time> is the realm's clock (GetServerTime), so summaries from different players compare fairly.
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
local CHECK_GAP = 60                 -- how often we look for a big change
local RELAY_BATCH = 3                -- entries passed on at a time
local RELAY_FRESH = 15 * 60          -- an entry heard on the channel this recently is not passed on again
local RELAY_AGAIN = 60 * 60          -- and we pass on the same entry at most once an hour (newcomers aside)
local HELLO_GAP = 2 * 60             -- at most one newcomer batch this often
local SEND_GAP = 2                   -- seconds between our messages
local SEND_BUDGET, SEND_WINDOW = 15, 600     -- at most 15 messages in 10 minutes
local READ_BUDGET, READ_WINDOW = 240, 60     -- at most 240 messages read a minute; the rest are ignored
local SENDER_MSGS, SENDER_WINDOW = 20, 600   -- at most 20 messages read from one sender in 10 minutes
local SENDER_ADDS, SENDER_ADD_WINDOW = 40, 3600   -- and at most 40 players added or taken off by them an hour
local REMOVE_GAP = 10                -- seconds between two of our "take me off" (unless we shared in between)
local MAX_QUEUE, QUEUE_TTL = 8, 120
local ROWS = 14                      -- rows shown at once (the mouse wheel scrolls)

TCF.LB_MAX_ENTRIES, TCF.LB_EXPIRE, TCF.LB_SEND_BUDGET, TCF.LB_READ_BUDGET = MAX_ENTRIES, EXPIRE, SEND_BUDGET, READ_BUDGET
TCF.LB_SENDER_MSGS, TCF.LB_SENDER_ADDS = SENDER_MSGS, SENDER_ADDS

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
  return n:find("^[%a\128-\255]+$") ~= nil and r:find("^[%w\128-\255']+$") ~= nil
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

local pruned = {}   -- realm -> true once tidied this session

-- drop anything odd, too old or too far ahead, and keep the newest MAX_ENTRIES
local function prune(b, t)
  local n, list = 0, {}
  for k, e in pairs(b.e) do
    if type(k) ~= "string" or not validEntry(e) or keyOf(e.n) ~= k or e.ts < t - EXPIRE or e.ts > t + SKEW then
      b.e[k] = nil
    else
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
  if not full then return nil end
  local cd = self:CD()
  local s = self.DevSummary and self:DevSummary()
  local v = s and s.version or "?"
  if not v:find("^[%w%.%-]+$") then v = "?" end
  return { n = full, c = db.class, l = max(1, min(200, floor(cd and cd.level or 1))), t = max(0, floor(db.taps or 0)),
    a = countAchievements(), z = min(200, TCF.DevZonesCleared and TCF.DevZonesCleared() or 0), v = v, ts = serverNow() }
end

---------------------------------------------------------------- sending
local queue = {}            -- { text, own, at, tries, key (a relay: the player it is about) }
local sentAt = {}           -- GetTime of our recent messages (SEND_BUDGET)
local lastSend = -1e9
local ownAt, lastOwnAt, lastOwn = nil, -1e9, nil
local lastOwnSentAt = -1e9  -- GetTime our own summary last went out
local checkAt = nil
local helloAt, helloSince, lastHello = nil, nil, -1e9
local heardAt, relayedAt, senders = {}, {}, {}   -- entry key -> GetTime; direct sender key -> first heard
local readAt = {}           -- GetTime of messages read (READ_BUDGET)
local senderMsgs, senderAdds, lastSweep = {}, {}, -1e9   -- sender key -> GetTimes (per-sender limits)
local lastRemoveAt = -1e9
local signupPending = false
local dirty = false
local view

local function enqueue(text, own, key)
  if not text then return end
  local t = now()
  for i = #queue, 1, -1 do
    if not queue[i].own and t - queue[i].at > QUEUE_TTL then table.remove(queue, i) end
  end
  if own then
    for i = #queue, 1, -1 do if queue[i].own then table.remove(queue, i) end end   -- only the newest summary
    table.insert(queue, 1, { text = text, own = true, at = t, tries = 0 })
  elseif #queue < MAX_QUEUE then
    queue[#queue + 1] = { text = text, at = t, tries = 0, key = key }
  end
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

local function channel()
  local id = TCF.DevChannelId and TCF.DevChannelId() or 0
  return id > 0 and id or nil
end

-- one message every SEND_GAP seconds, within the budget, only while sharing and in the channel
local function pump(t)
  if #queue == 0 then return end
  if not optedIn() then wipe(queue); return end
  if t - lastSend < SEND_GAP or not underBudget(t) then return end
  if InCombatLockdown and InCombatLockdown() then return end   -- addon messages can be blocked in fights: after
  local id = channel()
  if not id or not TCF.DevSendRaw then return end   -- waiting for the channel
  local item = table.remove(queue, 1)
  -- someone else passed this one on while ours waited: no need to send it again
  if item.key and heardAt[item.key] and heardAt[item.key] >= item.at then return pump(t) end
  lastSend = t
  if item.own then
    -- counted as shared even when the game reports a failure: it may still have gone out
    lastOwnSentAt = t
    local mk, shared = myKey(), accountTable("lbShared")
    if mk and shared then shared[mk] = true end
  end
  if TCF.DevSendRaw(item.text, "CHANNEL", id) then
    sentAt[#sentAt + 1] = t
    if item.key then heardAt[item.key], relayedAt[item.key] = t, t end   -- the others online heard it from us
  else
    item.tries = item.tries + 1   -- throttled or blocked: try once or twice more
    if item.tries < 3 then table.insert(queue, 1, item) end
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
    local text
    if b.e[k] then text = entryText(b.e[k])
    elseif b.rm[k] and b.rmn[k] then text = removalText(b.rmn[k], b.rm[k]) end
    if text and #queue < MAX_QUEUE then
      enqueue(text, nil, k)
      n = n + 1
    end
  end
  return n
end

-- this character's "take me off", if the channel is there and the limits allow; true once it went out
local function sendRemove(t)
  local id = channel()
  if not id or not TCF.DevSendRaw then return false end
  if InCombatLockdown and InCombatLockdown() then return false end
  -- a second one within REMOVE_GAP only when our own summary went out after the last one
  if t - lastRemoveAt < REMOVE_GAP and lastOwnSentAt < lastRemoveAt then return false end
  if not underBudget(t) then return false end
  lastRemoveAt, lastSend = t, t
  if not TCF.DevSendRaw("R1;" .. numStr(serverNow()), "CHANNEL", id) then return false end   -- tried again later
  sentAt[#sentAt + 1] = t
  local mk, ui = myKey(), TCF.db and TCF.db.ui
  if mk and ui and type(ui.lbRemove) == "table" then
    ui.lbRemove[mk] = nil
    if next(ui.lbRemove) == nil then ui.lbRemove = nil end
  end
  return true
end

local function snapshot(e) return { c = e.c, l = e.l, a = e.a, z = e.z, t = e.t } end

-- our own summary, then (unless noRelay) a few entries the others online haven't heard lately
local function sendOwn(t, noRelay)
  local e = TCF:LeaderboardOwnEntry()
  if not e then return false end
  enqueue(entryText(e), true)
  lastOwnAt, lastOwn = t, snapshot(e)
  ownAt = t + OWN_GAP + random() * OWN_JITTER
  if not noRelay then relay(t, t - RELAY_FRESH, true) end
  dirty = true
  return true
end

-- a level, an achievement, a zone or a quarter more taps since our last summary
local function bigChange()
  if not lastOwn then return false end
  local e = TCF:LeaderboardOwnEntry()
  if not e then return false end
  return e.c ~= lastOwn.c or e.l ~= lastOwn.l or e.a ~= lastOwn.a or e.z ~= lastOwn.z
    or e.t >= lastOwn.t * 1.25 + 500
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

local function onAddon(prefix, text, chan, sender, chanName)
  if not optedIn() then return end                       -- opted out: nothing is read
  if isSecret(prefix) or prefix ~= PREFIX then return end
  if not plain(text) or not plain(chan) or not plain(sender) or chan ~= "CHANNEL" then return end
  local kind = text:sub(1, 3)
  if kind ~= "L1;" and kind ~= "R1;" and kind ~= "X1;" then return end
  if isSecret(chanName) then return end
  if type(chanName) == "string" and chanName ~= "" and not chanName:lower():find(CHANNEL:lower(), 1, true) then return end
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

-- everyone on your realm's board and you, ranked by sortKey ("taps", "level", "ach" or "zones");
-- empty when you don't share
function TCF:LeaderboardRows(sortKey)
  local list = {}
  if not optedIn() then return list end
  local field = (SORTS[sortKey] or SORTS.taps)[1]
  local mine, st = myKey(), serverNow()
  local b = board(false)
  if b then
    for k, e in pairs(b.e) do
      if k ~= mine and fresh(e.ts, st) then   -- 30 days old during a long session: gone at once
        list[#list + 1] = { n = e.n, c = e.c, l = e.l, t = e.t, a = e.a, z = e.z, v = e.v, ts = e.ts }
      end
    end
  end
  local own = self:LeaderboardOwnEntry()
  if own then own.self = true; list[#list + 1] = own end
  table.sort(list, function(x, y)
    if x[field] ~= y[field] then return x[field] > y[field] end
    if x.t ~= y.t then return x.t > y.t end
    if x.l ~= y.l then return x.l > y.l end
    return x.n < y.n
  end)
  for i, r in ipairs(list) do r.rank = i end
  return list
end

local function ago(ts, t)
  local d = max(0, t - ts)
  if d < 120 then return "just now" end
  if d < 3600 then return floor(d / 60) .. " min ago" end
  if d < 2 * 86400 then return floor(d / 3600) .. " h ago" end
  return floor(d / 86400) .. " days ago"
end
TCF.LeaderboardAgo = ago

local function displayName(full)
  local n, r = full:match("^([^%-]+)%-(.+)$")
  local mine = myRealm()
  if n and mine and r:lower() == mine:lower() then return n end
  return full
end

---------------------------------------------------------------- the window
-- { title, x, width, sort key }
local COLS = { { "#", 0, 30 }, { "Name", 32, 150 }, { "Cat level", 184, 60, "level" }, { "Taps", 246, 92, "taps" },
  { "Achievements", 340, 90, "ach" }, { "Zones", 432, 46, "zones" }, { "Last seen", 480, 76 } }
local W = 588

local function openSettings()
  if not TCF.window and TCF.CreateWindow then TCF:CreateWindow() end
  local win = TCF.window
  if not win then return end
  win:Show()
  if win.SelectTab then win:SelectTab(10) end
end

local function createView()
  local U = TCF.UI
  local f = CreateFrame("Frame", "TapCatForeverLeaderboard", UIParent, U and U.BT)
  f:SetSize(W, 150 + ROWS * 18); f:SetPoint("CENTER", 0, 30)
  f:SetFrameStrata("DIALOG"); f:SetToplevel(true)
  f:EnableMouse(true); f:SetMovable(true); f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving); f:SetScript("OnDragStop", f.StopMovingOrSizing)
  if f.SetBackdrop and U and U.BACKDROP_DIALOG then f:SetBackdrop(U.BACKDROP_DIALOG) end
  f:Hide()
  tinsert(UISpecialFrames, "TapCatForeverLeaderboard")
  local function T(font, parent) return (parent or f):CreateFontString(nil, "OVERLAY", font) end
  f.title = T("GameFontNormalLarge"); f.title:SetPoint("TOP", 0, -16)
  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton"); close:SetPoint("TOPRIGHT", -6, -6)
  f.sort = "taps"
  f.scroll = 0

  -- column headings; the ones with a sort key are buttons
  f.heads = {}
  for i, c in ipairs(COLS) do
    local h
    if c[4] then
      h = CreateFrame("Button", nil, f)
      h:SetSize(c[3], 16); h:SetPoint("TOPLEFT", 16 + c[2], -44)
      h.label = T("GameFontNormalSmall", h); h.label:SetPoint("LEFT", 0, 0); h.label:SetJustifyH("LEFT")
      h.sortKey = c[4]
      h:SetScript("OnClick", function() f.sort = c[4]; f.scroll = 0; f:Refresh(); TCF:PlaySound("click") end)
      if U and U.Tip then
        U.Tip(h, function(tt) tt:AddLine("Sort by " .. SORTS[c[4]][2]:lower(), 1, 0.82, 0) end)
      end
    else
      h = CreateFrame("Frame", nil, f)
      h:SetSize(c[3], 16); h:SetPoint("TOPLEFT", 16 + c[2], -44)
      h.label = T("GameFontNormalSmall", h); h.label:SetPoint("LEFT", 0, 0); h.label:SetJustifyH("LEFT")
    end
    h.label:SetText(c[1])
    f.heads[i] = h
  end

  f.rows = {}
  for r = 1, ROWS do
    local row = { cells = {} }
    local y = -44 - r * 18
    row.hl = f:CreateTexture(nil, "BACKGROUND")
    row.hl:SetPoint("TOPLEFT", 12, y + 2); row.hl:SetSize(W - 24, 18)
    row.hl:SetColorTexture(1, 0.82, 0.2, 0.18)
    for i, c in ipairs(COLS) do
      local t = T("GameFontHighlightSmall"); t:SetPoint("TOPLEFT", 16 + c[2], y); t:SetWidth(c[3]); t:SetJustifyH("LEFT")
      if t.SetWordWrap then t:SetWordWrap(false) end
      row.cells[i] = t
    end
    f.rows[r] = row
  end

  f.empty = T("GameFontHighlight"); f.empty:SetPoint("TOP", 0, -96); f.empty:SetWidth(W - 80)
  if f.empty.SetJustifyH then f.empty:SetJustifyH("CENTER") end
  f.settingsBtn = (U and U.Button or function(p, txt, w, h, fn)
    local b = CreateFrame("Button", nil, p, "UIPanelButtonTemplate"); b:SetSize(w, h); b:SetText(txt); b:SetScript("OnClick", fn); return b
  end)(f, "Open Settings", 120, 22, function() openSettings(); TCF:PlaySound("click") end)
  f.settingsBtn:SetPoint("TOP", f.empty, "BOTTOM", 0, -12)
  f.count = T("GameFontDisableSmall"); f.count:SetPoint("BOTTOMRIGHT", -18, 70); f.count:SetJustifyH("RIGHT")
  f.note = T("GameFontDisableSmall"); f.note:SetPoint("BOTTOMLEFT", 18, 16); f.note:SetWidth(W - 36); f.note:SetJustifyH("LEFT")
  f.note:SetText("Only players on your realm who turned on sharing are listed. Players pass the list on to each other " ..
    "inside the game, so it fills up over time and can be a little behind. Taps count all of a player's characters. " ..
    "Players not seen for 30 days drop off, and at most " .. MAX_ENTRIES .. " are kept. Click a heading to sort. " ..
    "Scroll with the mouse wheel.")

  f:EnableMouseWheel(true)
  f:SetScript("OnMouseWheel", function(s, d) s.scroll = max(0, s.scroll - d); s:Refresh() end)

  function f:Refresh()
    dirty = false
    local on = optedIn()
    local list = TCF:LeaderboardRows(self.sort)
    self.scroll = max(0, min(self.scroll, #list - ROWS))
    local realm = myRealm()
    self.title:SetText("Realm leaderboard" .. (realm and (" - " .. realm) or ""))
    for i, h in ipairs(self.heads) do
      local c = COLS[i]
      h.label:SetText(c[1])
      if c[4] and c[4] == self.sort then h.label:SetTextColor(1, 1, 1) elseif c[4] then h.label:SetTextColor(1, 0.82, 0) end
      h:SetShown(on)
    end
    local t = serverNow()
    for r, row in ipairs(self.rows) do
      local e = list[r + self.scroll]
      if e then
        local cl = TCF.CLASS_BY_KEY[e.c]
        local cells = row.cells
        cells[1]:SetText(e.rank)
        cells[2]:SetText((displayName(e.n):gsub("|", "||")) .. (e.self and " (you)" or ""))
        if cl then cells[2]:SetTextColor(cl.color[1], cl.color[2], cl.color[3]) end
        cells[3]:SetText(e.l)
        cells[4]:SetText(TCF.Commas(e.t))
        cells[5]:SetText(e.a)
        cells[6]:SetText(e.z)
        cells[7]:SetText(e.self and "now" or ago(e.ts, t))
      end
      for _, c in ipairs(row.cells) do c:SetShown(e and true or false) end
      row.hl:SetShown(e and e.self and true or false)
      row.entry = e
    end
    if not on then
      self.empty:SetText("The realm leaderboard shows the cats of players on your realm who share their progress.\n\n" ..
        "To see it and be on it, turn on \"Share my cat's progress\" in Settings > Help and info. " ..
        "It applies to every character on your account. The first time you do, your cat gets a Heroic Cache.")
    else
      self.empty:SetText("No other players yet. Others on your realm who turn on sharing show up here " ..
        "as you and they are online, which can take a while.")
    end
    self.empty:SetShown(not on or #list <= 1)
    self.settingsBtn:SetShown(not on)
    self.note:SetShown(on)
    self.count:SetText(on and string.format("%d players", #list) or "")
  end

  local acc = 0
  f:SetScript("OnUpdate", function(s, e)
    acc = acc + e
    if acc >= 5 or (dirty and acc >= 0.5) then acc = 0; s:Refresh() end
  end)
  f:SetScript("OnShow", function(s) s:Refresh() end)
  return f
end

function TCF:ShowLeaderboard()
  view = view or createView()
  TCF.leaderboardView = view
  view:Show()
  view:Refresh()
  return view
end

function TCF:ToggleLeaderboard()
  if view and view:IsShown() then view:Hide(); return view end
  return self:ShowLeaderboard()
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
for _, e in ipairs({ "CHAT_MSG_ADDON", "PLAYER_LOGIN" }) do pcall(ev.RegisterEvent, ev, e) end

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
    if bigChange() and t - lastOwnAt >= OWN_MIN_GAP then ownAt = t end
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
    signupPending = false
  end,
  setOwnAt = function(t) ownAt = t end,
  event = function(...) onEvent(ev, ...) end,
  prune = prune,
  serverNow = serverNow,
  pickRelays = pickRelays,
  relay = relay,
}
