-- TapCatForever: party cats. Group members who also run TapCatForever say hello over a hidden
-- addon channel; their cats sit in a little row beside yours, and your taps count more: +20% with
-- one of them, +10% for each one after that, up to +50% with a full party (tap count, cat XP and
-- TapCoins from tapping; Core.lua TCF:Tap asks TCF:PartyTapMult). Lucky finds and chests are unchanged.
--
-- Protocol (prefix "TapCatFvr", party/raid/instance channel only, every field checked):
--   H1;<class>;<level>;<fur>;<pattern>;<skin>;<slot>=<id>,<slot>=<id>...   hello, please answer
--   U1;...same fields...                                                    update or answer
-- Slot codes: h head, c chest, m main, o off, b back, a acc, e effect, n neck, w belt, r ring.
-- An id is a cosmetic id (TCF.ITEMS) or #<item id> for real gear (TCF.GEAR).
local ADDON, TCF = ...
local floor, min, max = math.floor, math.min, math.max

local PREFIX = "TapCatFvr"
local MAX_MSG = 240          -- bytes we send at most (addon messages allow 255)
local SEND_GAP = 10          -- seconds between our own messages
local MAX_KNOWN = 40
local MAX_SLOTS = 12         -- slot entries read from one message
local MINI, MINI_GAP, MAX_SHOWN = 40, 2, 4

local SLOT_CODES = { "h", "c", "m", "o", "b", "a", "e", "n", "w", "r", "s", "x" }  -- send order (most visible first)
local CODE_SLOT = { h = "head", c = "chest", m = "main", o = "off", b = "back", a = "acc", e = "effect",
  n = "neck", w = "belt", r = "ring", s = "shoulder", x = "race" }  -- 1.6: s (shoulders), x (racial accessory); older versions skip codes they don't know
-- look slot -> gear slot, so a friend's real gear is drawn the same way Gear.lua draws yours
local GEAR_SLOT = { head = "HEAD", chest = "CHEST", back = "BACK", main = "MAINHAND", off = "OFFHAND",
  neck = "NECK", belt = "WAIST", ring = "FINGER1", shoulder = "SHOULDER" }

local known, order = {}, {}  -- name -> member; names in the order they said hello
local refreshRow  -- defined below
local fakes = {}             -- test-mode party cats (TCF:PartyTestInject)
local seq = 0
local lastSent, pendingKind, pendingAt, retryOnRegen = -1e9, nil, nil, false
local lastPayload = nil
local wasGrouped = false
local row                    -- the mini cat row (created on first use)

local function isSecret(v) return TCF.IsSecret and TCF.IsSecret(v) end
local function now() return GetTime and GetTime() or 0 end

---------------------------------------------------------------- group helpers
local function inGroup()
  if not IsInGroup then return false end
  local ok, g = pcall(IsInGroup)
  return ok and g and true or false
end

local function chatType()
  local home = LE_PARTY_CATEGORY_HOME and IsInGroup and IsInGroup(LE_PARTY_CATEGORY_HOME)
  local inst = LE_PARTY_CATEGORY_INSTANCE and IsInGroup and IsInGroup(LE_PARTY_CATEGORY_INSTANCE)
  if inst and not home then return "INSTANCE_CHAT" end
  if IsInRaid and IsInRaid() then return "RAID" end
  return "PARTY"
end

-- "Name" for your own realm, "Name-Realm" otherwise, without spaces, so roster names and
-- addon-message senders compare equal
local function nameKey(full)
  if type(full) ~= "string" or full == "" or isSecret(full) then return nil end
  -- display realms ("Azjol-Nerub", "Argent Dawn") lose spaces and hyphens, like sender names;
  -- character names cannot contain "-", so the first hyphen splits name and realm
  local n, r = full:match("^([^-]+)-(.+)$")
  if r then full = n .. "-" .. (r:gsub("[%s%-]", "")) end
  local short = full
  if Ambiguate then
    local ok, a = pcall(Ambiguate, full, "none")
    if ok and type(a) == "string" and not isSecret(a) then short = a end
  end
  short = short:gsub("%s", "")
  if short == "" or #short > 64 then return nil end
  return short
end

local function myKey()
  local n = TCF.SelfName and TCF.SelfName() or (UnitName and UnitName("player"))
  if type(n) ~= "string" or isSecret(n) then return nil end
  return nameKey(n)
end

-- true when a message's sender is you. Your own party messages come back to you, and the sender
-- can arrive as "Name-Realm" while Ambiguate keeps the realm on some clients, so compare the name
-- and (when there is one) the realm with yours, ignoring spaces, hyphens, apostrophes and case.
-- (1.6.0) The game may not tell an addon your own name in a usable way (it can come back as a
-- protected value), so your own name is also learned from your own party messages: they come back
-- to you, and the one that matches exactly what you just sent is yours. TCF.SelfSender holds the
-- sender name the game uses for you, TCF.SelfBase its name part in lower case.
local sentTexts = {}   -- the last few exact texts we sent
-- this session's tag (code "z" in every party message) and the probe ids: made on first use, so
-- each session (and each client in the tests) has its own
local selfTag
local function tag()
  if not selfTag then selfTag = string.format("%05x", math.random(0, 0xFFFFF)) end
  return selfTag
end
local function baseOf(name)
  if type(name) ~= "string" or isSecret(name) or name == "" then return nil end
  local b = name:match("^([^%-]+)") or name
  b = b:gsub("%s", ""):lower()
  return b ~= "" and b or nil
end
-- sender: the name the game put on one of our own messages
function TCF.LearnSelf(sender)
  local b = baseOf(sender)
  if not b or #sender > 80 then return end
  local changed = TCF.SelfSender ~= sender or TCF.SelfBase ~= b
  TCF.SelfSender = sender
  TCF.SelfBase = b
  if not changed then return end
  -- a cat that came in under this name before we knew it was us (a message sent before a /reload
  -- comes back with the old session's tag): take it off the row now
  local gone = false
  for k in pairs(known) do
    if baseOf(k) == b then
      known[k] = nil
      for i, n in ipairs(order) do if n == k then table.remove(order, i); break end end
      gone = true
    end
  end
  if gone and refreshRow then refreshRow() end
end
local function rememberSent(text)
  sentTexts[#sentTexts + 1] = text
  if #sentTexts > 6 then table.remove(sentTexts, 1) end
end
local function isOwnEcho(text)
  for _, t in ipairs(sentTexts) do if t == text then return true end end
  -- the tag is only ours (a friend with the same look and level sends the same text otherwise)
  local z = text:match("[;,]z=(%x+)$")
  return z ~= nil and z == selfTag
end
-- your name: what UnitName says when it can be read, else the name the game puts on your messages
-- (without the realm); nil while neither is known
function TCF.SelfName()
  local n = UnitName and UnitName("player")
  if type(n) == "string" and not isSecret(n) and n ~= "" then return n end
  return TCF.SelfSender and (TCF.SelfSender:match("^([^%-]+)") or TCF.SelfSender) or nil
end

-- A probe for learning your own name where no party message goes (the leaderboard's guild and
-- channel routes): "N1;<id>" comes back to you with the name the game uses for you. Every
-- version ignores it (Party.lua reads only H1 and U1, the others their own letters).
local probeId
function TCF.SelfProbe(chan, target)
  if TCF.SelfSender then return false end
  probeId = probeId or string.format("%06x", math.random(0, 0xFFFFFF))
  local api = C_ChatInfo and C_ChatInfo.SendAddonMessage
  if not api then return false end
  local ok = pcall(api, PREFIX, "N1;" .. probeId, chan, target)
  return ok
end
local function onProbe(prefix, text, sender)
  if not probeId or isSecret(prefix) or prefix ~= PREFIX or isSecret(text) or isSecret(sender) then return end
  if type(text) == "string" and text == "N1;" .. probeId then TCF.LearnSelf(sender) end
end

local function isMe(sender)
  if type(sender) ~= "string" or isSecret(sender) or sender == "" then return false end
  if TCF.SelfSender and sender == TCF.SelfSender then return true end
  if TCF.SelfBase and baseOf(sender) == TCF.SelfBase then return true end
  local me = UnitName and UnitName("player")
  if type(me) ~= "string" or isSecret(me) or me == "" then return false end
  local n, r = sender:match("^([^%-]+)%-?(.*)$")
  if not n or n:lower() ~= me:lower() then return false end
  -- 1.5.3.6: your own name is enough. Realm names come in different forms on different clients,
  -- and two players with the same name in one group is rare enough to accept.
  return true
end
TCF.PartyIsMe = isMe

-- the current group's names; complete = false when some name could not be read (secret)
local function roster()
  local names, complete = {}, true
  if not inGroup() then return names, true end
  local raid = IsInRaid and IsInRaid()
  local count = (GetNumGroupMembers and GetNumGroupMembers()) or 0
  if isSecret(count) then return names, false end
  local n = raid and min(40, count) or 4
  for i = 1, n do
    local unit = (raid and "raid" or "party") .. i
    local exists = not UnitExists or UnitExists(unit)
    if isSecret(exists) then complete = false
    elseif exists and isSecret(UnitIsConnected and UnitIsConnected(unit)) then
      complete = false  -- can't tell: don't prune anyone on a guess
    elseif exists and UnitIsConnected and UnitIsConnected(unit) == false then
      -- offline: left out, so they're pruned and stop counting toward the bonus
    elseif exists then
      local name, realm = UnitName(unit)
      if type(name) ~= "string" or isSecret(name) or isSecret(realm)
         or name == "" or name == (UNKNOWNOBJECT or "Unknown") or name == "Unknown" then
        complete = false  -- not loaded yet: don't prune anyone from this roster
      else
        local full = (type(realm) == "string" and realm ~= "") and (name .. "-" .. realm) or name
        local k = nameKey(full)
        if k then names[k] = true else complete = false end
      end
    end
  end
  return names, complete
end

---------------------------------------------------------------- encoding
local function lookId(it)
  if type(it) ~= "table" or type(it.id) ~= "string" then return nil end
  local gid = it.gear and it.id:match("^gear:(%d+)$")
  if gid then
    -- a random-suffix item draws exactly like its base, so send the base: friends on an older
    -- version know it, and the message stays short
    local g = TCF.GEAR and TCF.GEAR[tonumber(gid)]
    if g and g.base then gid = tostring(g.base) end
    return "#" .. gid
  end
  if it.id:find("^[%w_:]+$") then return it.id end
end

-- your own cat, as one short message (without the H1/U1 kind)
function TCF:PartyPayload(class)
  local db = self.db
  if not db then return nil end
  class = class or db.class
  local look = self:GetAppearance(class)
  local cd = self:CD(class)
  local function id(it) return (it and it.id and it.id:find("^[%w_:]+$")) and it.id or "" end
  local head = string.format("%s;%d;%s;%s;%s", class, cd and cd.level or 1, id(look.fur), id(look.pattern), id(look.skin))
  local parts, len = {}, #head + 4
  for _, code in ipairs(SLOT_CODES) do
    local v = lookId(look[CODE_SLOT[code]])
    if v then
      local entry = code .. "=" .. v
      if len + #entry + 1 <= MAX_MSG then parts[#parts + 1] = entry; len = len + #entry + 1 end
    end
  end
  parts[#parts + 1] = "z=" .. tag()
  return head .. ";" .. table.concat(parts, ",")
end

-- a look table (as TCF:GetAppearance returns) from a friend's message; nil if malformed
local function parse(text)
  if type(text) ~= "string" or isSecret(text) or #text > 255 then return nil end
  local kind, class, level, fur, pat, skin, slots =
    text:match("^([HU])1;(%u+);(%d+);([%w_:]*);([%w_:]*);([%w_:]*);([%w_:#=,]*)$")
  if not kind or not TCF.CLASS_BY_KEY[class] then return nil end
  level = tonumber(level)
  if not level or level < 1 or level > 999 then return nil end
  local items = TCF.ITEMS
  local function cos(id, slot)
    local it = id ~= "" and items[id]
    return (it and it.slot == slot) and it or nil
  end
  local eq, cosmetics, n = {}, {}, 0
  for code, v in slots:gmatch("(%l)=([^,]+)") do
    n = n + 1
    if n > MAX_SLOTS then break end
    local slot = CODE_SLOT[code]
    if slot then
      local gid = v:match("^#(%d+)$")
      if gid then
        gid = tonumber(gid)
        -- a random-suffix item (id = SUFFIX_ID_BASE + base * 100 + suffix) this version doesn't
        -- know: show its base item, which draws the same (Gear.lua tints and shapes suffix
        -- items by their base). Current versions send the base already; this is a safety net.
        local sb = TCF.SUFFIX_ID_BASE
        if gid and TCF.GEAR and not TCF.GEAR[gid] and sb and gid > sb then gid = floor((gid - sb) / 100) end
        if GEAR_SLOT[slot] and TCF.GEAR and TCF.GEAR[gid] then eq[GEAR_SLOT[slot]] = gid end
      else
        local it = cos(v, slot)
        -- a version before 1.6 sends its racial accessory as the accessory (a=)
        if not it and slot == "acc" then it = cos(v, "race"); slot = it and "race" or slot end
        if it then cosmetics[slot] = it end
      end
    end
  end
  -- real gear goes through Gear.lua's own drawing rules with the friend's equipped items
  local look = {}
  if next(eq) and TCF.GearAppearance then
    local proxy = setmetatable({ GearEquipped = function() return eq end }, { __index = TCF })
    local ok, out = pcall(TCF.GearAppearance, proxy, class)
    if ok and type(out) == "table" then look = out end
  end
  for slot, it in pairs(cosmetics) do look[slot] = it end
  look.fur = cos(fur, "fur") or items.fur_ginger
  look.pattern = cos(pat, "pattern")
  look.skin = cos(skin, "skin")
  return kind .. "1", class, floor(level), look, eq
end
TCF.PartyParse = parse

---------------------------------------------------------------- sending
local function send(kind)
  if not inGroup() then return true end
  local payload = TCF:PartyPayload()
  if not payload then return true end
  local api = C_ChatInfo and C_ChatInfo.SendAddonMessage
  if not api then return true end
  local text = kind .. ";" .. payload
  rememberSent(text)
  local ok, res = pcall(api, PREFIX, text, chatType())
  -- 12.x returns a result code (0 = sent); older clients return nothing or a boolean
  local sent = ok and (res == nil or res == true or res == 0 or
    (Enum and Enum.SendAddonMessageResult and res == Enum.SendAddonMessageResult.Success))
  if sent then
    lastSent, lastPayload = now(), payload
    return true
  end
  -- blocked (combat inside an instance) or throttled: try again later; known cats stay shown
  pendingKind = (kind == "H1" or pendingKind == "H1") and "H1" or (pendingKind or kind)  -- keep a hello a hello
  if InCombatLockdown and InCombatLockdown() then retryOnRegen = true
  else pendingAt = now() + SEND_GAP end
  return false
end

-- send now if allowed, otherwise once SEND_GAP has passed (H1 wins over U1)
local function request(kind)
  if pendingKind ~= "H1" then pendingKind = kind end
  local t = now()
  pendingAt = max(t, lastSent + SEND_GAP)
  if pendingAt <= t then
    local k = pendingKind
    pendingKind, pendingAt = nil, nil
    send(k)
  end
end

---------------------------------------------------------------- members
local function memberList()
  local list = {}
  for _, name in ipairs(order) do if known[name] then list[#list + 1] = known[name] end end
  for _, m in ipairs(fakes) do list[#list + 1] = m end
  return list
end

function TCF:PartyMembers() return memberList() end

function TCF:PartyCount()
  local n = 0
  for _ in pairs(known) do n = n + 1 end
  return n + #fakes
end

-- each tap counts as this many taps: +20% with the first group member who has the addon and
-- +10% for each one after that, up to four (a full party): 1.0, 1.2, 1.3, 1.4, 1.5
TCF.PARTY_TAP_FIRST, TCF.PARTY_TAP_EACH, TCF.PARTY_TAP_MAX_FRIENDS = 0.2, 0.1, 4
function TCF:PartyTapMult()
  local n = math.min(TCF.PARTY_TAP_MAX_FRIENDS, self:PartyCount())
  if n <= 0 then return 1 end
  return 1 + TCF.PARTY_TAP_FIRST + TCF.PARTY_TAP_EACH * (n - 1)
end
-- older name kept for anything that still asks
function TCF:PartyBonus() return self:PartyTapMult() end

local function forget(name)
  known[name] = nil
  for i, n in ipairs(order) do if n == name then table.remove(order, i); break end end
end

local function clearAll()
  for k in pairs(known) do known[k] = nil end
  for i = #order, 1, -1 do order[i] = nil end
end

local function onMessage(prefix, text, channel, sender)
  if isSecret(prefix) or prefix ~= PREFIX then return end
  if isSecret(channel) or (channel ~= "PARTY" and channel ~= "RAID" and channel ~= "INSTANCE_CHAT") then return end
  if isSecret(sender) or isSecret(text) then return end
  -- our own message coming back: learn the name the game gives us, never show our own cat
  if isOwnEcho(text) then TCF.LearnSelf(sender); return end
  local name = nameKey(sender)
  if not name or name == myKey() or isMe(sender) then return end   -- never your own cat
  local kind, class, level, look, eq = parse(text)
  if not kind then return end
  local m = known[name]
  if not m then
    local count = 0
    for _ in pairs(known) do count = count + 1 end
    if count >= MAX_KNOWN then return end
    seq = seq + 1
    m = { name = name, seq = seq }
    known[name] = m
    order[#order + 1] = name
  end
  local isNew = not m.look
  m.class, m.level, m.look, m.text, m.eq = class, level, look, text, eq
  m.sender = sender   -- the name exactly as the game sends it (challenges name you this way)
  m.missing = nil
  m.heardAt = now()   -- a duel keeps them present a while after their last message (DeathRoll.lua)
  -- answer a hello, or anyone we hadn't met; request() merges replies to one per SEND_GAP
  if kind == "H1" or isNew then request("U1") end
  refreshRow()
  if TCF.MarkDirty then TCF:MarkDirty() end
end

local function onRoster()
  local grouped = inGroup()
  if not grouped then
    if next(known) then clearAll(); refreshRow() end
    -- leaving a group also takes away any test-mode fake cats
    if wasGrouped and TCF.PartyTestClear then TCF:PartyTestClear() end
    wasGrouped = false
    return
  end
  local names, complete = roster()
  local pruned = false
  if complete then
    -- names compare without the realm (clients write realms differently), and a cat is only
    -- taken off when it is missing twice in a row, a few seconds apart, so the row doesn't blink
    local short = {}
    for k in pairs(names) do short[(k:match("^[^%-]+") or k):lower()] = true end
    local t = now()
    for name, m in pairs(known) do
      if names[name] or short[(name:match("^[^%-]+") or name):lower()] then m.missing = nil
      elseif not m.missing then m.missing = t
      elseif t - m.missing >= 3 then forget(name); pruned = true end
    end
  end
  -- just joined a group: say hello; after a prune, a hello also lets a wrongly pruned friend answer
  if not wasGrouped or pruned then request("H1") end  -- we just joined a group: say hello
  wasGrouped = true
  refreshRow()
end

---------------------------------------------------------------- mini cats beside the HUD cat
local function tooltip(btn)
  local m = btn.member
  if not m then return end
  local tt = GameTooltip
  tt:SetOwner(btn, "ANCHOR_TOP")
  local name = (m.name or "?"):gsub("|", "||")
  tt:AddLine(name, 1, 0.82, 0)
  local cl = TCF.CLASS_BY_KEY[m.class]
  if cl then tt:AddLine(string.format("Level %d %s cat", m.level or 1, cl.name), cl.color[1], cl.color[2], cl.color[3]) end
  if m.fake then tt:AddLine("Test party cat (test mode only)", 0.7, 0.7, 0.7) end
  tt:AddLine("Click to see this cat and its gear.", 0.6, 0.8, 1)
  tt:AddLine("Party bonus: your taps count 20% more with one friend who has TapCatForever, and 10% more for each friend after that, up to +50% with a full party.", 0.4, 1, 0.4, true)
  tt:Show()
end

local function createRow()
  local hud = TCF.hud
  if not hud or not TCF.cat then return nil end
  local f = CreateFrame("Frame", "TapCatForeverPartyCats", hud)
  f:SetSize(MAX_SHOWN * (MINI + MINI_GAP) + 30, MINI)
  f.cells = {}
  for i = 1, MAX_SHOWN do
    local b = CreateFrame("Button", nil, f)
    b:SetSize(MINI, MINI)
    local cat = TCF.CreateCat(b, MINI, { preview = true })
    cat.frame:SetPoint("BOTTOM", b, "BOTTOM", 0, 0)
    b.cat = cat
    b:SetScript("OnEnter", tooltip)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    b:RegisterForClicks("LeftButtonUp")
    b:SetScript("OnClick", function(self) if self.member and TCF.ShowPartyProfile then TCF:ShowPartyProfile(self.member) end end)
    b:Hide()
    f.cells[i] = b
  end
  local more = f:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
  more:Hide()
  f.more = more
  f:Hide()
  return f
end

-- beside the cat on the right, or on the left when the right side would leave the screen
local function placeRow()
  local cat = TCF.cat
  if not row or not cat then return end
  local left = false
  local hud = TCF.hud
  local right = hud and hud.GetRight and hud:GetRight()
  local sw = UIParent and UIParent.GetWidth and UIParent:GetWidth()
  local hs = hud and hud.GetEffectiveScale and hud:GetEffectiveScale()
  local us = UIParent and UIParent.GetEffectiveScale and UIParent:GetEffectiveScale()
  if type(right) == "number" and type(sw) == "number" and type(hs) == "number" and type(us) == "number" and us > 0 then
    local need = (#row.shownCells * (MINI + MINI_GAP) + (row.more:IsShown() and 26 or 0)) * hs / us
    left = right * hs / us + need > sw
  end
  if row.left == left and row.placed then return end
  row.left, row.placed = left, true
  row:ClearAllPoints()
  if left then row:SetPoint("BOTTOMRIGHT", cat.frame, "BOTTOMLEFT", -MINI_GAP, 0)
  else row:SetPoint("BOTTOMLEFT", cat.frame, "BOTTOMRIGHT", MINI_GAP, 0) end
  local prev
  for i, b in ipairs(row.shownCells) do
    b:ClearAllPoints()
    if left then
      if prev then b:SetPoint("BOTTOMRIGHT", prev, "BOTTOMLEFT", -MINI_GAP, 0) else b:SetPoint("BOTTOMRIGHT", row, "BOTTOMRIGHT", 0, 0) end
    else
      if prev then b:SetPoint("BOTTOMLEFT", prev, "BOTTOMRIGHT", MINI_GAP, 0) else b:SetPoint("BOTTOMLEFT", row, "BOTTOMLEFT", 0, 0) end
    end
    prev = b
  end
  row.more:ClearAllPoints()
  if prev then
    if left then row.more:SetPoint("RIGHT", prev, "LEFT", -2, 0) else row.more:SetPoint("LEFT", prev, "RIGHT", 2, 0) end
  end
end

refreshRow = function()
  local list = memberList()
  if #list == 0 and not row then return end
  if not row then row = createRow(); if not row then return end end
  local hud = TCF.hud
  local interactive = not hud or hud.interactive ~= false
  row.shownCells = {}
  for i, b in ipairs(row.cells) do
    local m = list[i]
    b.member = m
    if m then
      if b.text ~= m.text then
        b.text = m.text
        b.cat:ApplyAppearance(m.look)
      end
      b:EnableMouse(interactive)
      b:Show()
      row.shownCells[#row.shownCells + 1] = b
    else
      b.text = nil
      b:Hide()
    end
  end
  local extra = #list - MAX_SHOWN
  row.more:SetText(extra > 0 and ("+" .. extra) or "")
  row.more:SetShown(extra > 0)
  row.placed = false
  placeRow()
  row:SetShown(#list > 0)
end
TCF.PartyRefresh = function() refreshRow() end

---------------------------------------------------------------- a party cat's profile
-- Click a party cat: a small window with that cat drawn big, its class and level, and the gear it
-- wears (hover a piece for its tooltip). Opened by your click only; Escape or the X closes it.
local profile
local PROFILE_SLOTS = { "HEAD", "NECK", "SHOULDER", "BACK", "CHEST", "WRIST", "HANDS", "WAIST", "LEGS", "FEET",
  "FINGER1", "FINGER2", "TRINKET1", "TRINKET2", "MAINHAND", "OFFHAND", "RANGED" }
function TCF:ShowPartyProfile(m)
  if not m then return end
  local U = TCF.UI
  if not profile then
    local f = CreateFrame("Frame", "TapCatForeverPartyProfile", UIParent, U and U.BT)
    f:SetSize(360, 420); f:SetPoint("CENTER", 0, 60)
    f:SetFrameStrata("DIALOG"); f:SetToplevel(true)
    f:EnableMouse(true); f:SetMovable(true); f:RegisterForDrag("LeftButton")
    f:SetScript("OnDragStart", f.StartMoving); f:SetScript("OnDragStop", f.StopMovingOrSizing)
    if f.SetBackdrop and U then f:SetBackdrop(U.BACKDROP_DIALOG) end
    tinsert(UISpecialFrames, "TapCatForeverPartyProfile")
    local close = CreateFrame("Button", nil, f, "UIPanelCloseButton"); close:SetPoint("TOPRIGHT", -6, -6)
    f.title = U.Text(f, "GameFontNormalLarge"); f.title:SetPoint("TOP", 0, -16)
    f.sub = U.Text(f, "GameFontHighlight"); f.sub:SetPoint("TOP", f.title, "BOTTOM", 0, -4)
    local holder = CreateFrame("Frame", nil, f); holder:SetSize(150, 150); holder:SetPoint("TOPLEFT", 16, -56)
    f.cat = TCF.CreateCat(holder, 150, { preview = true })
    f.cat.frame:SetPoint("BOTTOM", holder, "BOTTOM", 0, 0)
    f.cells = {}
    for i, key in ipairs(PROFILE_SLOTS) do
      local b = U.GearButton(f, 30)
      local col, row = (i - 1) % 5, math.floor((i - 1) / 5)
      b:SetPoint("TOPLEFT", 18 + col * 66, -226 - row * 40)
      b.key = key
      b:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
        if self.item then TCF:GearTooltip(GameTooltip, self.item, f.class)
        else
          local s = TCF.GEAR_SLOT_BY_KEY and TCF.GEAR_SLOT_BY_KEY[key]
          GameTooltip:AddLine(s and s.name or key, 1, 0.82, 0); GameTooltip:AddLine("Empty", 0.6, 0.6, 0.6)
        end
        GameTooltip:Show()
      end)
      b:SetScript("OnLeave", function() GameTooltip:Hide(); if TCF.HideGearCompare then TCF:HideGearCompare() end end)
      f.cells[i] = b
    end
    f.note = U.Text(f, "GameFontDisableSmall", "What your friend's cat wears right now. Hover a piece for its details.")
    f.note:SetPoint("BOTTOM", 0, 16); f.note:SetWidth(320)
    f.info = U.Text(f, "GameFontHighlight", nil, "LEFT"); f.info:SetPoint("TOPLEFT", holder, "TOPRIGHT", 12, -6); f.info:SetWidth(170)
    if f.info.SetJustifyV then f.info:SetJustifyV("TOP") end
    profile = f
  end
  local f = profile
  local cl = TCF.CLASS_BY_KEY[m.class]
  f.class = m.class
  f.title:SetText((m.name or "?"):gsub("|", "||"))
  f.sub:SetText(cl and string.format("|cff%02x%02x%02xLevel %d %s cat|r", cl.color[1] * 255, cl.color[2] * 255, cl.color[3] * 255, m.level or 1, cl.name) or "")
  if m.look then f.cat:ApplyAppearance(m.look) end
  local eq, power, n = m.eq or {}, 0, 0
  for i, key in ipairs(PROFILE_SLOTS) do
    local id = eq[key]
    local it = id and TCF.GEAR and TCF.GEAR[id]
    f.cells[i].item = it
    f.cells[i]:SetGear(it, TCF.GEAR_SLOT_BY_KEY and TCF.GEAR_SLOT_BY_KEY[key] and TCF.GEAR_SLOT_BY_KEY[key].icon)
    if it then n = n + 1; power = power + (it.ilvl or 0) end
  end
  local look = m.look or {}
  local lines = { string.format("Gear worn: %d pieces", n) }
  if n > 0 then lines[#lines + 1] = string.format("Average item level: %d", math.floor(power / n + 0.5)) end
  if look.skin then lines[#lines + 1] = "Skin: " .. look.skin.name end
  if look.fur and not look.skin then lines[#lines + 1] = "Fur: " .. look.fur.name end
  for _, slot in ipairs({ "head", "chest", "back", "acc", "main" }) do
    local it = look[slot]
    if it and not it.gear then lines[#lines + 1] = "Cosmetic: " .. it.name end
  end
  if m.fake then lines[#lines + 1] = "|cffaaaaaaTest party cat|r" end
  f.info:SetText(table.concat(lines, "\n"))
  f:Show()
end

---------------------------------------------------------------- test mode
-- Fake party cats so the row can be seen while playing alone. Test mode only (/tcf testmode).
-- test mode off: fake cats go away (Core.lua's /tcf testmode calls this)
function TCF:PartyTestClear()
  if #fakes == 0 then return end
  for i = #fakes, 1, -1 do fakes[i] = nil end
  refreshRow()
  if self.MarkDirty then self:MarkDirty() end
end

function TCF:PartyTestInject(n)
  if not (self.db and self.db.ui.testMode) then return end
  n = max(0, min(8, floor(tonumber(n) or 0)))
  for i = #fakes, 1, -1 do fakes[i] = nil end
  local furs, skins, hats = {}, {}, {}
  for _, it in ipairs(TCF.ITEM_LIST or {}) do
    if it.slot == "fur" then furs[#furs + 1] = it.id
    elseif it.slot == "skin" then skins[#skins + 1] = it.id
    elseif it.slot == "head" and not it.class then hats[#hats + 1] = it.id end
  end
  for i = 1, n do
    local cl = TCF.CLASSES[(i * 3) % #TCF.CLASSES + 1]
    local skin = (i % 2 == 0 and #skins > 0) and skins[(i * 7) % #skins + 1] or ""
    local fur = #furs > 0 and furs[(i * 5) % #furs + 1] or ""
    local hat = #hats > 0 and ("h=" .. hats[(i * 11) % #hats + 1]) or ""
    -- goes through the real message reader, so the test also checks parsing
    local text = string.format("U1;%s;%d;%s;;%s;%s", cl.key, 5 + i * 9, fur, skin, hat)
    local kind, class, level, look = parse(text)
    if kind then
      fakes[#fakes + 1] = { name = "Test Cat " .. i, class = class, level = level, look = look, text = text, fake = true }
    end
  end
  refreshRow()
  if self.MarkDirty then self:MarkDirty() end
  return #fakes
end

function TCF:PartyTestCount() return #fakes end

---------------------------------------------------------------- events
local ev = CreateFrame("Frame")
for _, e in ipairs({ "CHAT_MSG_ADDON", "GROUP_ROSTER_UPDATE", "UNIT_CONNECTION", "PLAYER_ENTERING_WORLD", "PLAYER_REGEN_ENABLED" }) do
  pcall(ev.RegisterEvent, ev, e)
end
if C_ChatInfo and C_ChatInfo.RegisterAddonMessagePrefix then pcall(C_ChatInfo.RegisterAddonMessagePrefix, PREFIX) end

ev:SetScript("OnEvent", function(_, event, a1, a2, a3, a4)
  if not TCF.db then return end
  if event == "CHAT_MSG_ADDON" then
    onProbe(a1, a2, a4)
    onMessage(a1, a2, a3, a4)
  elseif event == "GROUP_ROSTER_UPDATE" or event == "UNIT_CONNECTION" then
    onRoster()
  elseif event == "PLAYER_ENTERING_WORLD" then
    wasGrouped = false   -- login, reload or zoning: say hello again so friends answer
    onRoster()
  elseif event == "PLAYER_REGEN_ENABLED" then
    if retryOnRegen then retryOnRegen = false; request(pendingKind or "U1") end
  end
end)

-- every half second: due messages; every two seconds: look changes and the row's side
local acc, lookAcc = 0, 0
ev:SetScript("OnUpdate", function(_, elapsed)
  acc = acc + elapsed
  if acc < 0.5 then return end
  lookAcc = lookAcc + acc
  acc = 0
  if not TCF.db then return end
  if pendingAt and now() >= pendingAt and not retryOnRegen then
    local k = pendingKind or "U1"
    pendingKind, pendingAt = nil, nil
    send(k)
  end
  if lookAcc >= 2 then
    lookAcc = 0
    if lastPayload and inGroup() and not pendingAt then
      local p = TCF:PartyPayload()
      if p and p ~= lastPayload then request("U1") end
    end
    if not row and TCF.hud and (next(known) or #fakes > 0) then refreshRow() end  -- heard before the HUD existed
    if row and row:IsShown() then
      local interactive = not TCF.hud or TCF.hud.interactive ~= false
      for _, b in ipairs(row.cells) do if b.member then b:EnableMouse(interactive) end end
      placeRow()
    end
  end
end)
