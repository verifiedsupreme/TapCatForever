-- TapCatForever: quiet loot notices. Everything you find outside a chest you open (Adventure,
-- quests, expeditions, crafting...) goes straight into your bags. Nothing ever shows on or
-- around the cat on your screen.
--  * Cosmetics and skins: no notice at all (they're in Appearance; chat says so if chat is on).
--  * Gear: only while the TapCatForever window is open, one slim line under the window (icon,
--    name, Power change) that fades after a few seconds. Hover it for the item compared with
--    what your cat wears; click to open Gear.
-- Opening a chest yourself plays the reel and shows the loot box only for a blue (Rare) or
-- better item; a common or green one gets the same slim line, under the Treasure Bag.
local ADDON, TCF = ...
local min, max = math.min, math.max

-- one slim line per item; names that don't fit end in "..." (the tooltip has the full name)
local W, H, GAP, MAX_SHOWN = 240, 22, 2, 3
local LIFE, FADE = 5, 0.8

local holder, toasts = nil, {}

local function anchorHolder()
  holder:ClearAllPoints()
  -- under the Treasure Bag when it is open (chest openings), otherwise under the main window
  local bag, win = TCF.bag, TCF.window
  if bag and bag:IsShown() then holder:SetPoint("TOP", bag, "BOTTOM", 0, -4)
  elseif win and win:IsShown() then holder:SetPoint("TOP", win, "BOTTOM", 0, -4)
  else holder:SetPoint("TOP", UIParent, "TOP", 0, -170) end
end

local function layout()
  anchorHolder()
  local y = 0
  for i = #toasts, 1, -1 do   -- newest at the top, right under the window
    local t = toasts[i]
    t:ClearAllPoints()
    t:SetPoint("TOP", holder, "TOP", 0, -y)
    y = y + H + GAP
  end
end

local function remove(t)
  for i, o in ipairs(toasts) do if o == t then table.remove(toasts, i); break end end
  t:Hide()
  t.free = true
  layout()
end

local pool = {}
local function getToast()
  for _, t in ipairs(pool) do if t.free then t.free = false; return t end end
  local U = TCF.UI
  local t = CreateFrame("Button", nil, holder)
  t:SetSize(W, H)
  t:SetFrameStrata("MEDIUM")
  -- a faint dark strip, no border, so it reads over the game without looking like a window
  t.bg = t:CreateTexture(nil, "BACKGROUND"); t.bg:SetAllPoints(); t.bg:SetColorTexture(0, 0, 0, 0.35)
  t.icon = t:CreateTexture(nil, "ARTWORK"); t.icon:SetSize(18, 18); t.icon:SetPoint("LEFT", 3, 0)
  t.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
  t.sub = U.Text(t, "GameFontHighlightSmall", nil, "RIGHT"); t.sub:SetPoint("RIGHT", -5, 0)
  t.sub:SetWordWrap(false)
  t.name = U.Text(t, "GameFontHighlightSmall", nil, "LEFT"); t.name:SetPoint("LEFT", t.icon, "RIGHT", 5, 0)
  t.name:SetPoint("RIGHT", t.sub, "LEFT", -6, 0)
  t.name:SetWordWrap(false)
  t:RegisterForClicks("LeftButtonUp", "RightButtonUp")
  t:SetScript("OnClick", function(self, button)
    if button == "LeftButton" and TCF.OpenTab then TCF:OpenTab(self.isGear and "gear" or "appearance") end
    remove(self)
  end)
  t:SetScript("OnEnter", function(self)
    self.hover = true
    self:SetAlpha(1)
    GameTooltip:SetOwner(self, "ANCHOR_TOP")
    if self.isGear then TCF:GearTooltip(GameTooltip, self.item)
    elseif TCF.ItemTooltip then TCF:ItemTooltip(GameTooltip, self.item) end
    if self.title and self.title ~= "" then GameTooltip:AddLine("From: " .. self.title, 0.8, 0.8, 0.8, true) end
    GameTooltip:AddLine("Click to open the " .. (self.isGear and "Gear" or "Appearance") .. " tab. Right-click to dismiss.", 0.6, 0.6, 0.6, true)
    GameTooltip:Show()
  end)
  t:SetScript("OnLeave", function(self) self.hover = false; GameTooltip:Hide() end)
  t:SetScript("OnUpdate", function(self, e)
    if self.hover then return end
    self.age = self.age + e
    if self.age > LIFE then
      local a = 1 - (self.age - LIFE) / FADE
      if a <= 0 then remove(self) else self:SetAlpha(a) end
    end
  end)
  pool[#pool + 1] = t
  return t
end

-- it: a gear item (isGear) or a cosmetic/skin/effect from TCF.ITEMS
-- fromChest: a common or green item from a chest you just opened (always gets its line)
function TCF:ShowLootToast(it, isNew, salvage, title, isGear, fromChest)
  if not it then return end
  if not fromChest then
    -- found while playing: cosmetics and skins get no notice; gear only while the window is open
    if not isGear then return end
    if not (self.window and self.window:IsShown()) then return end
  end
  if not holder then
    holder = CreateFrame("Frame", "TapCatForeverLootToasts", UIParent)
    holder:SetSize(W, H)
    holder:SetFrameStrata("DIALOG")
  end
  -- the same item twice in a row (a stack of salvaged duplicates) refreshes one notice
  local last = toasts[#toasts]
  local t
  if last and last.item == it and not last.hover then
    t = last
    t.count = (t.count or 1) + 1
  else
    t = getToast()
    t.count = 1
    toasts[#toasts + 1] = t
    while #toasts > MAX_SHOWN do remove(toasts[1]) end
  end
  t.item, t.isGear, t.age, t.hover = it, isGear and true or false, 0, false
  t:SetAlpha(1)
  t.icon:SetTexture(TCF.Icon(it.icon or "INV_Misc_QuestionMark"))
  local q = isGear and it.q or it.rarity or 1
  local col = TCF.RARITY[q] and TCF.RARITY[q].color or { 1, 1, 1 }
  t.name:SetText(it.name .. (t.count > 1 and (" |cffffffffx" .. t.count .. "|r") or ""))
  t.name:SetTextColor(col[1], col[2], col[3])
  -- the right side: just the Power change, short
  local sub
  if not isGear then
    sub = isNew and "|cffcc88ffnew|r" or string.format("|cffaaaaaa+%d coins|r", salvage or 0)
  else
    local d = self.GearUpgrade and self:GearUpgrade(it)
    if not self:GearUsable(it, self.db.class) then sub = "|cffff8040can't use|r"
    elseif d and d > 0 then sub = "|cff20ff20+" .. d .. "|r"
    elseif d and d < 0 then sub = "|cffff4040" .. d .. "|r"
    else sub = "|cffaaaaaa=|r" end
  end
  t.title = title
  t.sub:SetText(sub)
  t:Show()
  layout()
end

-- open the main window on the Gear (1) or Appearance (6) tab
function TCF:OpenTab(name)
  if not self.window then self:CreateWindow() end
  self.window:Show()
  if self.window.SelectTab then self.window:SelectTab(name == "gear" and 1 or 6) end
end
