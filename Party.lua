-- TapCatForever: party cats. Group members who also run TapCatForever say hello over a hidden
-- addon channel; their cats sit in a little row beside yours. Each of them makes your taps count
-- 10% more, up to +50% with five (tap count, cat XP and TapCoins from tapping; Core.lua TCF:Tap
-- asks TCF:PartyTapMult). Lucky finds and chests are unchanged.
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

local SLOT_CODES = { "h", "c", "m", "o", "b", "a", "e", "n", "w", "r" }  -- send order (most visible first)
local CODE_SLOT = { h = "head", c = "chest", m = "main", o = "off", b = "back", a = "acc", e = "effect",
  n = "neck", w = "belt", r = "ring" }
-- look slot -> gear slot, so a friend's real gear is drawn the same way Gear.lua draws yours
local GEAR_SLOT = { head = "HEAD", chest = "CHEST", back = "BACK", main = "MAINHAND", off = "OFFHAND",
  neck = "NECK", belt = "WAIST", ring = "FINGER1" }

local known, order = {}, {}  -- name -> member; names in the order they said hello
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
  local n = UnitName and UnitName("player")
  if type(n) ~= "string" or isSecret(n) then return nil end
  return nameKey(n)
end

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
  if gid then return "#" .. gid end
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
        if GEAR_SLOT[slot] and TCF.GEAR and TCF.GEAR[gid] then eq[GEAR_SLOT[slot]] = gid end
      else
        local it = cos(v, slot)
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
  return kind .. "1", class, floor(level), look
end
TCF.PartyParse = parse

---------------------------------------------------------------- sending
local function send(kind)
  if not inGroup() then return true end
  local payload = TCF:PartyPayload()
  if not payload then return true end
  local api = C_ChatInfo and C_ChatInfo.SendAddonMessage
  if not api then return true end
  local ok, res = pcall(api, PREFIX, kind .. ";" .. payload, chatType())
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

-- each tap counts as this many taps: +10% for every other group member who has the addon,
-- up to five of them (1.0 .. 1.5)
TCF.PARTY_TAP_EACH, TCF.PARTY_TAP_MAX_FRIENDS = 0.1, 5
function TCF:PartyTapMult()
  return 1 + TCF.PARTY_TAP_EACH * math.min(TCF.PARTY_TAP_MAX_FRIENDS, self:PartyCount())
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

local refreshRow  -- defined below

local function onMessage(prefix, text, channel, sender)
  if isSecret(prefix) or prefix ~= PREFIX then return end
  if isSecret(channel) or (channel ~= "PARTY" and channel ~= "RAID" and channel ~= "INSTANCE_CHAT") then return end
  if isSecret(sender) or isSecret(text) then return end
  local name = nameKey(sender)
  if not name or name == myKey() then return end
  local kind, class, level, look = parse(text)
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
  m.class, m.level, m.look, m.text = class, level, look, text
  -- answer a hello, or anyone we hadn't met; request() merges replies to one per SEND_GAP
  if kind == "H1" or isNew then request("U1") end
  refreshRow()
  if TCF.MarkDirty then TCF:MarkDirty() end
end

local function onRoster()
  local grouped = inGroup()
  if not grouped then
    if next(known) then clearAll(); refreshRow() end
    wasGrouped = false
    return
  end
  local names, complete = roster()
  local pruned = false
  if complete then
    for name in pairs(known) do if not names[name] then forget(name); pruned = true end end
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
  tt:AddLine("Party bonus: your taps count 10% more for each friend with TapCatForever (up to +50%)", 0.4, 1, 0.4, true)
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

---------------------------------------------------------------- test mode
-- Fake party cats so the row can be seen while playing alone. Test mode only (/tcf testmode).
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
for _, e in ipairs({ "CHAT_MSG_ADDON", "GROUP_ROSTER_UPDATE", "PLAYER_ENTERING_WORLD", "PLAYER_REGEN_ENABLED" }) do
  pcall(ev.RegisterEvent, ev, e)
end
if C_ChatInfo and C_ChatInfo.RegisterAddonMessagePrefix then pcall(C_ChatInfo.RegisterAddonMessagePrefix, PREFIX) end

ev:SetScript("OnEvent", function(_, event, a1, a2, a3, a4)
  if not TCF.db then return end
  if event == "CHAT_MSG_ADDON" then
    onMessage(a1, a2, a3, a4)
  elseif event == "GROUP_ROSTER_UPDATE" then
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
