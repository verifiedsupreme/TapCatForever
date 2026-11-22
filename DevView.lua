-- TapCatForever: developer view (opt-in). Players who tick "Share my cat's progress (developer
-- stats and leaderboard)" in Settings answer a short question from the addon's developer with five things:
-- addon version, cat class, cat level, zones cleared and TapCoins. Nothing is sent by anyone who
-- has not ticked it, answers only ever go to the developer (a whisper addon message to the
-- developer's own characters, known by name and realm together), and only while both are online.
--
-- How the question reaches players, all without the player doing anything:
--   * GUILD and PARTY / RAID / INSTANCE_CHAT addon messages, when the developer is in a guild or group;
--   * a hidden custom channel (CHANNEL addon messages). Only players who opted in join it, with
--     JoinTemporaryChannel (never saved), and it is taken out of every chat window and its notices
--     are filtered, so nothing from it prints in chat. The game still lists it in the Chat Channels
--     window, and anyone else in the channel can see the names of the characters in it (the Settings
--     tooltip says so). Anyone can join it by name, and with an addon could read what is sent on it.
--     Leaving the option off never joins it, except briefly to send the leaderboard's "take me off"
--     for a character that shared before (Leaderboard.lua). A join that keeps failing (a password
--     or ban set by whoever holds the name, or too many channels) is tried at most 3 times a session.
--
-- Protocol (Party.lua's prefix "TapCatFvr", which every version since 1.4 ignores unless a message
-- starts H1 or U1; every field checked, anything else ignored):
--   Q1;<nonce>                                              the developer asks (rate limited)
--   A1;<nonce>;<version>;<class>;<level>;<zones>;<coins>    an answer, whispered to the developer
-- The developer (name and realm checked by hash, or test mode) asks with /tcf players and sees who
-- answered in a small window.
--
-- The same opt-in also puts you on the realm leaderboard (Leaderboard.lua), which uses this file's
-- hidden channel and sending helpers (TCF.DevChannelId, TCF.DevSendRaw) for its own L1, R1 and X1 messages.
local ADDON, TCF = ...
local floor, min, max, random = math.floor, math.min, math.max, math.random

local PREFIX = "TapCatFvr"         -- shared with Party.lua (one prefix for the addon)
local CHANNEL = "TapCatFvrShare"   -- the hidden channel's name
local ANSWER_GAP = 60              -- seconds between our answers, whoever asks
local ASK_GAP = ANSWER_GAP + 5     -- seconds between the developer's questions: longer than ANSWER_GAP, so
                                   -- everyone who answered the last question can answer the next one
local MAX_JOIN_TRIES = 3           -- channel joins per session before the channel route is given up
local JOIN_DELAY = 20              -- seconds after login before joining (the game's own channels go first)
local MAX_KEPT = 200               -- answers kept in the window
local ROWS = 12                    -- rows shown at once (the mouse wheel scrolls)
-- The developer's characters: hashes (keyHash below) of the lower-case "name-realm", with the realm as
-- GetNormalizedRealmName gives it (no spaces or hyphens). A name alone is not enough: names are only
-- unique on one realm. To add a character, turn on test mode on it and type /tcf devkey.
-- Until this holds the developer's characters, nobody counts as the developer (test mode still
-- works for trying the window) and no player answers anyone.
local DEV_HASH = {}
-- The developer's character names on their own (lower case, any realm): Ziggu and Ziggutrip. Realm
-- keys above can be added later with /tcf devkey; until then the names are enough. Someone else with
-- the same name could see the same short summaries opted-in players already agreed to share.
local DEV_NAME_HASH = { [282723659] = true, [1306739114] = true }

TCF.DEV_PREFIX, TCF.DEV_CHANNEL, TCF.DEV_ASK_GAP, TCF.DEV_ANSWER_GAP = PREFIX, CHANNEL, ASK_GAP, ANSWER_GAP

local function isSecret(v) return TCF.IsSecret and TCF.IsSecret(v) end
local function now() return GetTime and GetTime() or 0 end
local function plain(v) return type(v) == "string" and not isSecret(v) end

local function keyHash(s)
  local x = 5381
  for i = 1, #s do x = (x * 33 + s:byte(i)) % 4294967296 end
  return x
end

-- "Name" from "Name" or "Name-Realm"; nil for anything odd
local function shortName(full)
  if not plain(full) or full == "" or #full > 64 then return nil end
  local n = full:match("^([^%-]+)")
  if not n or n == "" or n:find("[%s;|]") then return nil end
  return n
end

local function myRealm()
  local r
  if GetNormalizedRealmName then
    local ok, v = pcall(GetNormalizedRealmName)
    if ok then r = v end
  end
  if not plain(r) or r == "" then
    local ok, v = pcall(function() return GetRealmName and GetRealmName() end)
    r = ok and v or nil
  end
  if not plain(r) or r == "" then return nil end
  return r
end

-- "name-realm" in lower case, the realm without spaces, hyphens or apostrophes; a sender without a
-- realm is on your own realm. nil when the realm isn't known (then nobody is the developer).
local function fullKey(full)
  local n = shortName(full)
  if not n then return nil end
  local realm = full:match("^[^%-]+%-(.+)$")
  if not realm or realm == "" then realm = myRealm() end
  if not realm then return nil end
  realm = realm:gsub("[%s%-']", "")
  if realm == "" or #realm > 64 then return nil end
  return (n .. "-" .. realm):lower()
end

local function isDevName(full)
  local k = fullKey(full)
  if k and DEV_HASH[keyHash(k)] then return true end
  local n = shortName(full)
  return n and DEV_NAME_HASH[keyHash(n:lower())] or false
end
TCF.DevIsDeveloperName = isDevName
TCF.DevFullKey = fullKey
TCF.DevMyRealm = myRealm

local function myName()
  local n = UnitName and UnitName("player")
  if not plain(n) then return nil end
  return n
end

-- the developer: one of the developer's characters, or test mode
function TCF:IsDeveloper()
  if self.db and self.db.ui and self.db.ui.testMode then return true end
  local n = myName()
  return n and isDevName(n) and true or false
end

---------------------------------------------------------------- what is shared
local function zonesCleared(class)
  local ok, n = pcall(function()
    local adv = TCF:CD(class).adv
    local count = 0
    for i = 1, #(TCF.TIERS or {}) do
      if (adv.best or 0) >= TCF.AdvStageCode(i, TCF:AdvStages(i)) then count = count + 1 else break end
    end
    return count
  end)
  return ok and type(n) == "number" and n or 0
end
TCF.DevZonesCleared = zonesCleared

-- the five things shared: addon version, class, cat level, zones cleared, TapCoins
function TCF:DevSummary()
  local db = self.db
  if not db then return nil end
  local cd = self:CD()
  local version = tostring(self.version or "?"):gsub("[^%w%.%-]", ""):sub(1, 16)
  return {
    version = version ~= "" and version or "?",
    class = db.class,
    level = floor(cd and cd.level or 1),
    zones = zonesCleared(),
    coins = max(0, floor(db.coins or 0)),
  }
end

local function num(n) return string.format("%.0f", n) end

function TCF:DevAnswerText(nonce)
  local s = self:DevSummary()
  if not s or not TCF.CLASS_BY_KEY[s.class] then return nil end
  return string.format("A1;%s;%s;%s;%s;%s;%s", nonce, s.version, s.class, num(s.level), num(s.zones), num(min(s.coins, 1e15)))
end

-- an answer from someone; nil if anything about it is off
local function parseAnswer(text)
  if not plain(text) or #text > 255 then return nil end
  local nonce, version, class, level, zones, coins = text:match("^A1;(%w+);([%w%.%-]+);(%u+);(%d+);(%d+);(%d+)$")
  if not nonce or #nonce > 12 or #version > 16 or not TCF.CLASS_BY_KEY[class] then return nil end
  level, zones, coins = tonumber(level), tonumber(zones), tonumber(coins)
  if not level or level < 1 or level > 999 or not zones or zones > 999 or not coins or coins > 1e15 then return nil end
  return nonce, { version = version, class = class, level = level, zones = zones, coins = coins }
end
TCF.DevParseAnswer = parseAnswer

local function parseQuestion(text)
  if not plain(text) or #text > 32 then return nil end
  local nonce = text:match("^Q1;(%w+)$")
  if nonce and #nonce <= 12 then return nonce end
end

---------------------------------------------------------------- sending
local function sendRaw(text, chatType, target)
  local api = C_ChatInfo and C_ChatInfo.SendAddonMessage
  if not api then return false end
  local ok, res = pcall(api, PREFIX, text, chatType, target)
  -- 12.x returns a result code (0 = sent); older clients return nothing or a boolean
  return ok and (res == nil or res == true or res == 0 or
    (Enum and Enum.SendAddonMessageResult and res == Enum.SendAddonMessageResult.Success)) and true or false
end
TCF.DevSendRaw = sendRaw

local function groupType()
  if not IsInGroup then return nil end
  local ok, g = pcall(IsInGroup)
  if not ok or not g or isSecret(g) then return nil end
  local home = LE_PARTY_CATEGORY_HOME and IsInGroup(LE_PARTY_CATEGORY_HOME)
  local inst = LE_PARTY_CATEGORY_INSTANCE and IsInGroup(LE_PARTY_CATEGORY_INSTANCE)
  if inst and not home and not isSecret(inst) then return "INSTANCE_CHAT" end
  if IsInRaid and IsInRaid() then return "RAID" end
  return "PARTY"
end

local function inGuild()
  if not IsInGuild then return false end
  local ok, g = pcall(IsInGuild)
  return ok and g and not isSecret(g) and true or false
end

---------------------------------------------------------------- the hidden channel
local joinAt, joinSent, hideAt = nil, false, nil
local joinTries, joinGaveUp = 0, false   -- joins sent this session; true once the channel route is given up
local devListening = false   -- the developer asked this session: stay in the channel to ask again

local function channelId()
  if not GetChannelName then return 0 end
  local ok, id = pcall(GetChannelName, CHANNEL)
  if ok and type(id) == "number" and not isSecret(id) and id > 0 then return id end
  return 0
end
TCF.DevChannelId = channelId

-- take the channel out of every chat window, so nothing it carries can show in chat
local function hideChannel()
  for i = 1, (NUM_CHAT_WINDOWS or 10) do
    local cf = _G["ChatFrame" .. i]
    if cf then
      if ChatFrame_RemoveChannel then pcall(ChatFrame_RemoveChannel, cf, CHANNEL)
      elseif ChatFrameUtil and ChatFrameUtil.RemoveChannel then pcall(ChatFrameUtil.RemoveChannel, cf, CHANNEL)
      elseif type(cf.RemoveChannel) == "function" then pcall(cf.RemoveChannel, cf, CHANNEL) end
    end
  end
end

-- opted out, and this character's leaderboard "take me off" has not gone out yet
local function removalPending()
  return TCF.LeaderboardRemovePending and TCF.LeaderboardRemovePending() and true or false
end

local function wantChannel()
  return TCF.db and (TCF.db.ui.shareDev or devListening or removalPending()) and true or false
end

local function join()
  if channelId() > 0 then hideChannel(); return true end
  if not JoinTemporaryChannel then return false end
  if InCombatLockdown and InCombatLockdown() then return false end
  if joinGaveUp then return true end   -- the channel can't be joined this session: guild and group only
  joinTries = joinTries + 1
  if joinTries >= MAX_JOIN_TRIES then joinGaveUp = true end
  -- no chat window given, so the game adds it to none; taken out of all of them again below
  pcall(JoinTemporaryChannel, CHANNEL, nil, nil, false)
  joinSent = true
  hideChannel()
  hideAt = now() + 2   -- once more after the server confirms the join
  return true
end

local function leave()
  joinAt = nil
  if channelId() > 0 and LeaveChannelByName then pcall(LeaveChannelByName, CHANNEL) end
end

-- the leaderboard sent its "take me off": leave unless something else still needs the channel
function TCF.DevLeaveIfUnwanted()
  if not wantChannel() then leave() end
end

-- chat filter: anything about the hidden channel (join notices and the like) never reaches chat
local function isOurChannel(v)
  return plain(v) and #v <= 80 and v:lower():find(CHANNEL:lower(), 1, true) ~= nil
end
local function chatFilter(_, _, _, _, _, channelString, _, _, _, _, channelName)
  if isOurChannel(channelString) or isOurChannel(channelName) then return true end
  return false
end
TCF.DevChatFilter = chatFilter

do
  local add = (ChatFrameUtil and ChatFrameUtil.AddMessageEventFilter) or ChatFrame_AddMessageEventFilter
  if add then
    for _, e in ipairs({ "CHAT_MSG_CHANNEL_NOTICE", "CHAT_MSG_CHANNEL_NOTICE_USER", "CHAT_MSG_CHANNEL",
                         "CHAT_MSG_CHANNEL_JOIN", "CHAT_MSG_CHANNEL_LEAVE" }) do
      pcall(add, e, chatFilter)
    end
  end
end

-- Settings checkbox changed (UI.lua). The leaderboard hears it first: turning sharing off sends its
-- "take me off" message while the channel is still joined. If that could not go out yet (no channel,
-- combat, a refused send), the channel stays (or gets) joined until it has.
function TCF:DevShareChanged()
  if self.LeaderboardShareChanged then self:LeaderboardShareChanged(self.db.ui.shareDev and true or false) end
  if self.db.ui.shareDev then
    joinTries, joinGaveUp = 0, false   -- a click: a fresh try
    joinAt = now()   -- join now (out of combat)
  elseif not wantChannel() then
    leave()
  elseif removalPending() and channelId() == 0 and not joinAt then
    joinAt = now()
  end
end

-- Turns the opt-in on or off. The Settings checkbox and the Leaderboard tab's Join and Leave buttons
-- all come here, so the sign-up chest, the channel and the leaderboard's "take me off" always follow.
function TCF:SetShareProgress(on)
  if not self.db then return end
  self.db.ui.shareDev = on and true or false
  self:DevShareChanged()
  if self.window and self.window:IsShown() and self.window.Refresh then self.window:Refresh() end
end

---------------------------------------------------------------- answering (players who opted in)
local lastAnswer, lastNonce = -1e9, nil
local pendingAnswer = nil   -- { target, nonce, at }

local function onQuestion(text, chan, sender)
  if not (TCF.db and TCF.db.ui.shareDev) then return end   -- opted out: never answer
  if chan ~= "GUILD" and chan ~= "PARTY" and chan ~= "RAID" and chan ~= "INSTANCE_CHAT" and chan ~= "CHANNEL" then return end
  if not isDevName(sender) then return end                -- only ever the developer
  local me = myName()
  if me and fullKey(sender) == fullKey(me) then return end   -- the developer's own question
  local nonce = parseQuestion(text)
  if not nonce or nonce == lastNonce then return end
  if pendingAnswer or now() - lastAnswer < ANSWER_GAP then return end
  lastNonce = nonce
  lastAnswer = now()   -- the gap runs from the question, so the developer's next one (ASK_GAP) is answered
  -- a moment later, so many answers don't all arrive at once
  pendingAnswer = { target = sender, nonce = nonce, at = now() + 0.5 + random() * 3 }
end

local function sendAnswer()
  local p = pendingAnswer
  pendingAnswer = nil
  if not p or not (TCF.db and TCF.db.ui.shareDev) then return end
  local text = TCF:DevAnswerText(p.nonce)
  if text then sendRaw(text, "WHISPER", p.target) end
end

---------------------------------------------------------------- asking (the developer)
local answers, answerOrder = {}, {}
local askNonce, lastAsk, askRoutes, channelAskAt = nil, -1e9, {}, nil
local dirty = false
local view                 -- the window (created on first use)

local function onAnswer(text, chan, sender)
  if not askNonce or chan ~= "WHISPER" then return end
  if not TCF:IsDeveloper() then return end
  local nonce, rec = parseAnswer(text)
  if not nonce or nonce ~= askNonce then return end
  local name = plain(sender) and #sender <= 64 and not sender:find("[%s;|]") and sender or nil
  if not name then return end
  if not answers[name] then
    if #answerOrder >= MAX_KEPT then return end
    answerOrder[#answerOrder + 1] = name
  end
  rec.name, rec.at = name, now()
  answers[name] = rec
  dirty = true
end

local function sendChannelAsk()
  channelAskAt = nil
  local id = channelId()
  if id > 0 and askNonce and sendRaw("Q1;" .. askNonce, "CHANNEL", id) then askRoutes.channel = true end
end

-- /tcf players: ask everyone who opted in (at most once every ASK_GAP seconds) and show the window
function TCF:DevAsk()
  if not self:IsDeveloper() then return false end
  self:DevShowView()
  local t = now()
  if askNonce and t - lastAsk < ASK_GAP then
    self:Print(string.format("You asked %d seconds ago. You can ask again in %d seconds.", floor(t - lastAsk), math.ceil(ASK_GAP - (t - lastAsk))), true)
    return false
  end
  lastAsk = t
  askNonce = tostring(random(100000, 999999))
  wipe(answers); wipe(answerOrder); wipe(askRoutes)
  if inGuild() and sendRaw("Q1;" .. askNonce, "GUILD") then askRoutes.guild = true end
  local g = groupType()
  if g and sendRaw("Q1;" .. askNonce, g) then askRoutes.group = true end
  devListening = true
  if channelId() > 0 then sendChannelAsk()
  else join(); channelAskAt = now() + 3 end   -- the channel needs a moment after joining
  dirty = true
  return true
end

-- the rows the window lists: everyone who answered, and you when you share (so it can be tried alone)
function TCF:DevViewRows()
  local list = {}
  for _, name in ipairs(answerOrder) do if answers[name] then list[#list + 1] = answers[name] end end
  if self.db and self.db.ui.shareDev then
    local s = self:DevSummary()
    if s then s.name = (myName() or "You") .. " (you)"; s.self = true; list[#list + 1] = s end
  end
  table.sort(list, function(a, b)
    if a.level ~= b.level then return a.level > b.level end
    return a.name < b.name
  end)
  return list
end

---------------------------------------------------------------- the window
local COLS = { { "Name", 10, 130 }, { "Class", 140, 70 }, { "Level", 212, 40 }, { "Zones", 254, 44 }, { "TapCoins", 300, 80 }, { "Version", 382, 56 } }

local function createView()
  local U = TCF.UI
  local f = CreateFrame("Frame", "TapCatForeverDevView", UIParent, U and U.BT)
  f:SetSize(460, 96 + ROWS * 16); f:SetPoint("CENTER", 0, 40)
  f:SetFrameStrata("DIALOG"); f:SetToplevel(true)
  f:EnableMouse(true); f:SetMovable(true); f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving); f:SetScript("OnDragStop", f.StopMovingOrSizing)
  if f.SetBackdrop and U and U.BACKDROP_DIALOG then f:SetBackdrop(U.BACKDROP_DIALOG) end
  f:Hide()
  tinsert(UISpecialFrames, "TapCatForeverDevView")
  local function T(font) return f:CreateFontString(nil, "OVERLAY", font) end
  f.title = T("GameFontNormalLarge"); f.title:SetPoint("TOP", 0, -16)
  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton"); close:SetPoint("TOPRIGHT", -6, -6)
  f.cols = {}
  for i, c in ipairs(COLS) do
    local h = T("GameFontNormalSmall"); h:SetPoint("TOPLEFT", 12 + c[2], -42); h:SetWidth(c[3]); h:SetJustifyH("LEFT"); h:SetText(c[1])
    f.cols[i] = h
  end
  f.rows = {}
  for r = 1, ROWS do
    local row = {}
    for i, c in ipairs(COLS) do
      local t = T("GameFontHighlightSmall"); t:SetPoint("TOPLEFT", 12 + c[2], -42 - r * 16); t:SetWidth(c[3]); t:SetJustifyH("LEFT")
      if t.SetWordWrap then t:SetWordWrap(false) end
      row[i] = t
    end
    f.rows[r] = row
  end
  f.empty = T("GameFontDisable"); f.empty:SetPoint("TOP", 0, -80); f.empty:SetWidth(400)
  f.status = T("GameFontDisableSmall"); f.status:SetPoint("BOTTOMLEFT", 16, 16); f.status:SetWidth(300); f.status:SetJustifyH("LEFT")
  f.ask = (U and U.Button or function(p, txt, w, h, fn)
    local b = CreateFrame("Button", nil, p, "UIPanelButtonTemplate"); b:SetSize(w, h); b:SetText(txt); b:SetScript("OnClick", fn); return b
  end)(f, "Ask again", 90, 22, function() TCF:DevAsk() end)
  f.ask:SetPoint("BOTTOMRIGHT", -16, 12)
  f.scroll = 0
  f:EnableMouseWheel(true)
  f:SetScript("OnMouseWheel", function(s, d) s.scroll = max(0, s.scroll - d); s:Refresh() end)

  function f:Refresh()
    dirty = false
    local list = TCF:DevViewRows()
    self.scroll = max(0, min(self.scroll, #list - ROWS))
    local others = 0
    for _, r in ipairs(list) do if not r.self then others = others + 1 end end
    self.title:SetText(string.format("Players sharing their progress (%d)", others))
    for r, row in ipairs(self.rows) do
      local a = list[r + self.scroll]
      if a then
        local cl = TCF.CLASS_BY_KEY[a.class]
        row[1]:SetText((tostring(a.name):gsub("|", "||")))
        row[2]:SetText(cl and cl.name or a.class)
        if cl then row[2]:SetTextColor(cl.color[1], cl.color[2], cl.color[3]) end
        row[3]:SetText(a.level); row[4]:SetText(a.zones)
        row[5]:SetText(TCF.Commas(a.coins)); row[6]:SetText(a.version)
      end
      for _, t in ipairs(row) do t:SetShown(a and true or false) end
    end
    self.empty:SetShown(#list == 0)
    self.empty:SetText(askNonce and "No answers yet. Only players who turned on sharing answer." or "Ask with /tcf players.")
    local routes = {}
    if askRoutes.guild then routes[#routes + 1] = "guild" end
    if askRoutes.group then routes[#routes + 1] = "group" end
    if askRoutes.channel then routes[#routes + 1] = "hidden channel" end
    local wait = askNonce and math.ceil(ASK_GAP - (now() - lastAsk)) or 0
    if askNonce then
      self.status:SetText(string.format("Asked %d seconds ago over %s.", floor(now() - lastAsk),
        #routes > 0 and table.concat(routes, ", ") or "nothing yet"))
    else
      self.status:SetText("")
    end
    self.ask:SetEnabled(wait <= 0)
    self.ask:SetText(wait > 0 and ("Ask again (" .. wait .. ")") or "Ask again")
  end
  local acc = 0
  f:SetScript("OnUpdate", function(s, e)
    acc = acc + e
    if acc >= 1 or (dirty and acc >= 0.25) then acc = 0; s:Refresh() end
  end)
  f:SetScript("OnShow", function(s) s:Refresh() end)
  return f
end

function TCF:DevShowView()
  view = view or createView()
  TCF.devView = view
  view:Show()
  view:Refresh()
  return view
end

---------------------------------------------------------------- events
local ev = CreateFrame("Frame")
for _, e in ipairs({ "CHAT_MSG_ADDON", "PLAYER_LOGIN", "CHAT_MSG_CHANNEL_NOTICE", "PLAYER_REGEN_ENABLED" }) do
  pcall(ev.RegisterEvent, ev, e)
end
if C_ChatInfo and C_ChatInfo.RegisterAddonMessagePrefix then pcall(C_ChatInfo.RegisterAddonMessagePrefix, PREFIX) end

local slashWrapped = false
local function wrapSlash()
  -- wrapped at login, after every file has added its own commands, so /tcf players reaches here
  if slashWrapped or not (SlashCmdList and SlashCmdList.TAPCATFOREVER) then return end
  slashWrapped = true
  local inner = SlashCmdList.TAPCATFOREVER
  SlashCmdList.TAPCATFOREVER = function(msg, ...)
    local cmd = type(msg) == "string" and msg:lower():match("^%s*(%S*)") or ""
    if cmd == "players" and TCF.db and TCF:IsDeveloper() then TCF:DevAsk(); return end
    -- test mode: the key that makes this character one of the developer's (DEV_HASH above)
    if cmd == "devkey" and TCF.db and TCF.db.ui.testMode then
      local k = fullKey(myName() or "")
      TCF:Print(k and ("Developer key for this character: " .. keyHash(k)) or "Your realm isn't known yet. Try again in a moment.", true)
      return
    end
    return inner(msg, ...)
  end
end

local function onEvent(_, event, a1, a2, a3, a4, _, _, _, _, a9)
  if event == "PLAYER_LOGIN" then
    wrapSlash()
    -- sharing, or a leaderboard "take me off" still to send for this character
    if TCF.db and wantChannel() then joinAt = now() + JOIN_DELAY end
    return
  end
  if not TCF.db then return end
  if event == "CHAT_MSG_ADDON" then
    if isSecret(a1) or a1 ~= PREFIX then return end
    if not plain(a2) or not plain(a3) or not plain(a4) then return end
    local kind = a2:sub(1, 2)
    if kind == "Q1" then onQuestion(a2, a3, a4)
    elseif kind == "A1" then onAnswer(a2, a3, a4) end
  elseif event == "CHAT_MSG_CHANNEL_NOTICE" then
    if isOurChannel(a4) or isOurChannel(a9) then
      hideChannel()
      if a1 == "WRONG_PASSWORD" or a1 == "BANNED" or a1 == "INVALID_NAME" or a1 == "NOT_ALLOWED" or a1 == "THROTTLED" then
        joinGaveUp = true   -- someone holds the channel, or the server said no: guild and group only
      elseif a1 == "YOU_JOINED" then
        joinTries = 0
      end
      -- our own join came through after sharing was turned off again: leave at once
      if joinSent and (a1 == "YOU_JOINED" or a1 == "YOU_CHANGED") then
        joinSent = false
        if not wantChannel() then leave() end
      end
    end
  elseif event == "PLAYER_REGEN_ENABLED" then
    if wantChannel() and channelId() == 0 and not joinAt and not joinGaveUp then joinAt = now() end
  end
end
ev:SetScript("OnEvent", onEvent)

-- once a second: a due join, the second hide, a due answer, the developer's channel question
local acc = 0
ev:SetScript("OnUpdate", function(_, e)
  acc = acc + e
  if acc < 1 then return end
  acc = 0
  if not TCF.db then return end
  local t = now()
  if joinAt and t >= joinAt then
    if not wantChannel() then joinAt = nil
    elseif join() then joinAt = nil end   -- in combat: tried again on the next tick
  end
  if hideAt and t >= hideAt then hideAt = nil; hideChannel() end
  if pendingAnswer and t >= pendingAnswer.at then sendAnswer() end
  if channelAskAt then
    if channelId() > 0 then sendChannelAsk()
    elseif t >= channelAskAt + 10 then channelAskAt = nil end   -- couldn't join: guild and group only
  end
end)

-- test hooks (the harness)
TCF.DevTest = {
  state = function() return { joinAt = joinAt, joinSent = joinSent, lastAnswer = lastAnswer, pending = pendingAnswer,
    askNonce = askNonce, lastAsk = lastAsk, routes = askRoutes, devListening = devListening, channelAskAt = channelAskAt,
    joinTries = joinTries, joinGaveUp = joinGaveUp } end,
  reset = function()
    joinAt, joinSent, hideAt, devListening = nil, false, nil, false
    joinTries, joinGaveUp = 0, false
    lastAnswer, lastNonce, pendingAnswer = -1e9, nil, nil
    askNonce, lastAsk, channelAskAt = nil, -1e9, nil
    wipe(answers); wipe(answerOrder); wipe(askRoutes)
  end,
  wrapSlash = wrapSlash,
  keyHash = keyHash,
  setDevKeys = function(keys)   -- the harness's own developer characters (hashes); returns the old ones
    local old = {}
    for h in pairs(DEV_HASH) do old[#old + 1] = h end
    DEV_HASH = {}
    for _, h in ipairs(keys or {}) do DEV_HASH[h] = true end
    return old
  end,
  event = function(...) onEvent(ev, ...) end,   -- events the test's mock client can't register
}
