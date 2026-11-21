-- TapCatForever: small loot notices. Gear and cosmetics you find (Adventure, quests,
-- expeditions, crafting, the shop...) go straight into your bags and a little notice slides in
-- instead of the big loot box. Hover a notice to see the item (gear is compared with what your
-- cat is wearing), click it to open the Gear or Appearance tab, right-click to dismiss.
-- Opening a chest yourself still plays the reel and shows the loot box.
local ADDON, TCF = ...
local min, max = math.min, math.max

local W, H, GAP, MAX_SHOWN = 270, 46, 4, 5
local LIFE, FADE = 7, 0.6

local holder, toasts = nil, {}

local function anchorHolder()
  holder:ClearAllPoints()
  local hud = TCF.hud
  if hud and hud:IsShown() then
    holder:SetPoint("BOTTOM", hud, "TOP", 0, 26)
  else
    holder:SetPoint("TOP", UIParent, "TOP", 0, -170)
  end
end

local function layout()
  anchorHolder()
  local y = 0
  for i = #toasts, 1, -1 do   -- newest at the bottom, nearest the cat
    local t = toasts[i]
    t:ClearAllPoints()
    t:SetPoint("BOTTOM", holder, "BOTTOM", 0, y)
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
  local t = CreateFrame("Button", nil, holder, U.BT)
  t:SetSize(W, H)
  t:SetFrameStrata("DIALOG")
  if t.SetBackdrop then t:SetBackdrop(U.BACKDROP_DIALOG or U.BACKDROP) end
  t.icon = t:CreateTexture(nil, "ARTWORK"); t.icon:SetSize(32, 32); t.icon:SetPoint("LEFT", 9, 0)
  t.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
  t.name = U.Text(t, "GameFontNormal", nil, "LEFT"); t.name:SetPoint("TOPLEFT", t.icon, "TOPRIGHT", 8, -1); t.name:SetWidth(W - 60)
  t.name:SetWordWrap(false)
  t.sub = U.Text(t, "GameFontHighlightSmall", nil, "LEFT"); t.sub:SetPoint("BOTTOMLEFT", t.icon, "BOTTOMRIGHT", 8, 1); t.sub:SetWidth(W - 60)
  t.sub:SetWordWrap(false)
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
function TCF:ShowLootToast(it, isNew, salvage, title, isGear)
  if not it then return end
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
  if t.SetBackdropBorderColor then t:SetBackdropBorderColor(col[1], col[2], col[3], 1) end
  t.name:SetText(it.name .. (t.count > 1 and (" |cffffffffx" .. t.count .. "|r") or ""))
  t.name:SetTextColor(col[1], col[2], col[3])
  local sub
  if isGear then
    local d = self.GearUpgrade and self:GearUpgrade(it)
    if not self:GearUsable(it, self.db.class) then sub = "|cffff8040Your class can't use it|r"
    elseif d and d > 0 then sub = "|cff20ff20+" .. d .. " Power|r if worn"
    elseif d and d < 0 then sub = "|cffff4040" .. d .. " Power|r if worn"
    else sub = "|cffaaaaaaSame Power as what you wear|r" end
  elseif it.slot == "skin" then
    sub = "|cffcc88ffNew cat skin|r"
  else
    sub = isNew and "|cffcc88ffNew cosmetic|r" or string.format("|cffcc88ffDuplicate:|r +%d TapCoins", salvage or 0)
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
