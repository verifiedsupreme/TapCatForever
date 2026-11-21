-- TapCatForever: HUD cat, main window (wardrobe / shop / achievements / settings), minimap button
local ADDON, TCF = ...

local floor, min, max = math.floor, math.min, math.max
local BT = BackdropTemplateMixin and "BackdropTemplate" or nil
local ART = TCF.ART_PATH
local function coinStr(n, size) return "|T" .. ART .. "ui_coin:" .. (size or 14) .. ":" .. (size or 14) .. "|t " .. TCF.Commas(n) end

local BACKDROP_PANEL = {
  bgFile = "Interface\\Tooltips\\UI-Tooltip-Background", edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border",
  tile = true, tileSize = 16, edgeSize = 14, insets = { left = 3, right = 3, top = 3, bottom = 3 },
}
local BACKDROP_DIALOG = {
  bgFile = "Interface\\DialogFrame\\UI-DialogBox-Background-Dark", edgeFile = "Interface\\DialogFrame\\UI-DialogBox-Border",
  tile = true, tileSize = 32, edgeSize = 32, insets = { left = 11, right = 12, top = 12, bottom = 11 },
}

local function Panel(parent, w, h, alpha)
  local f = CreateFrame("Frame", nil, parent, BT)
  if w then f:SetSize(w, h) end
  if f.SetBackdrop then
    f:SetBackdrop(BACKDROP_PANEL)
    f:SetBackdropColor(0.06, 0.05, 0.09, alpha or 0.85)
    f:SetBackdropBorderColor(0.45, 0.40, 0.55, 1)
  end
  return f
end

local function Text(parent, font, txt, justify)
  local fs = parent:CreateFontString(nil, "OVERLAY", font or "GameFontHighlight")
  if txt then fs:SetText(txt) end
  if justify then fs:SetJustifyH(justify) end
  return fs
end

local function Button(parent, txt, w, h, onClick)
  local b = CreateFrame("Button", nil, parent, "UIPanelButtonTemplate")
  b:SetSize(w or 100, h or 22)
  b:SetText(txt)
  b:SetScript("OnClick", onClick)
  return b
end

local function Tip(owner, fn)
  owner:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT"); fn(GameTooltip, self); GameTooltip:Show()
  end)
  owner:SetScript("OnLeave", function() GameTooltip:Hide() end)
end

function TCF:ItemTooltip(tt, it)
  local col = TCF.RARITY[it.rarity].color
  tt:AddLine("|T" .. TCF.Icon(it.icon) .. ":20:20|t " .. it.name, col[1], col[2], col[3])
  tt:AddLine(TCF.RARITY[it.rarity].name .. " " .. TCF.SLOT_BY_KEY[it.slot].name, 1, 1, 1)
  if it.class then
    local cl = TCF.CLASS_BY_KEY[it.class]
    tt:AddLine(cl.name .. " only", cl.color[1], cl.color[2], cl.color[3])
  else
    tt:AddLine("Any class", 0.7, 0.7, 0.7)
  end
  local owned = self.db.owned[it.id]
  if owned then
    tt:AddLine("Collected" .. (owned > 1 and (" (x" .. owned .. ")") or ""), 0.3, 1, 0.3)
  elseif it.source == "achievement" then
    tt:AddLine("Reward from an achievement", 1, 0.82, 0)
  else
    tt:AddLine("Not collected - found in chests, random drops and the daily shop", 0.6, 0.6, 0.6, true)
  end
end

---------------------------------------------------------------- item preview cell
local function CropToBounds(tex, art)
  local b = TCF.ArtBounds[art] or { 0, 0, 1, 1 }
  local w, h = b[3] - b[1], b[4] - b[2]
  local s = min(1, max(w, h) + 0.06)
  local cx, cy = (b[1] + b[3]) / 2, (b[2] + b[4]) / 2
  local l, t = cx - s / 2, cy - s / 2
  l = max(0, min(1 - s, l)); t = max(0, min(1 - s, t))
  tex:SetTexCoord(l, l + s, t, t + s)
end

local function ItemPicture(parent, size)
  local f = CreateFrame("Frame", nil, parent)
  f:SetSize(size, size)
  f.base = f:CreateTexture(nil, "ARTWORK", nil, 0); f.base:SetAllPoints()
  f.a = f:CreateTexture(nil, "ARTWORK", nil, 1); f.a:SetAllPoints()
  f.b = f:CreateTexture(nil, "ARTWORK", nil, 2); f.b:SetAllPoints()
  function f:SetItem(it, desat)
    self.base:Hide(); self.b:Hide()
    local art = it.art
    if it.slot == "fur" or it.slot == "pattern" then
      self.base:SetTexture(ART .. "cat_fur", nil, nil, "NEAREST")
      CropToBounds(self.base, "cat_fur")
      local c = it.slot == "fur" and it.c1 or { 0.85, 0.85, 0.85 }
      self.base:SetVertexColor(c[1], c[2], c[3]); self.base:Show()
      if it.slot == "fur" then self.a:Hide(); self.base:SetDesaturated(desat); return end
      self.base:SetDesaturated(desat)
      CropToBounds(self.a, "cat_fur"); CropToBounds(self.b, "cat_fur")
    else
      CropToBounds(self.a, art); CropToBounds(self.b, art)
    end
    local pb = TCF.PART_B[art]
    if it.slot == "effect" then
      self.a:SetTexture(ART .. art); self.a:SetTexCoord(0, 1, 0, 1)
    else
      self.a:SetTexture(ART .. art .. (pb and "_a" or ""), nil, nil, "NEAREST")
    end
    self.a:SetVertexColor(it.c1[1], it.c1[2], it.c1[3]); self.a:SetDesaturated(desat); self.a:Show()
    if pb then
      local c2 = it.c2 or it.c1
      self.b:SetTexture(ART .. art .. "_b", nil, nil, "NEAREST")
      self.b:SetVertexColor(c2[1], c2[2], c2[3]); self.b:SetDesaturated(desat); self.b:Show()
    end
  end
  return f
end

local function ItemCell(parent, size)
  local b = CreateFrame("Button", nil, parent, BT)
  b:SetSize(size, size)
  if b.SetBackdrop then b:SetBackdrop(BACKDROP_PANEL) end
  b.pic = ItemPicture(b, size - 8); b.pic:SetPoint("CENTER")
  b.check = b:CreateTexture(nil, "OVERLAY"); b.check:SetSize(18, 18)
  b.check:SetPoint("TOPRIGHT", 2, 2); b.check:SetTexture("Interface\\Buttons\\UI-CheckBox-Check")
  b.count = Text(b, "NumberFontNormalSmall", nil, "RIGHT"); b.count:SetPoint("BOTTOMRIGHT", -4, 4)
  b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  function b:SetItem(it, owned, equipped)
    self.item = it
    local col = TCF.RARITY[it.rarity].color
    if self.SetBackdrop then
      self:SetBackdropColor(0.05, 0.05, 0.08, owned and 0.95 or 0.6)
      self:SetBackdropBorderColor(col[1], col[2], col[3], owned and 1 or 0.45)
    end
    self.pic:SetItem(it, not owned)
    self.pic:SetAlpha(owned and 1 or 0.35)
    self.check:SetShown(equipped and true or false)
    local n = TCF.db.owned[it.id]
    self.count:SetText((n and n > 1) and ("x" .. n) or "")
    self:Show()
  end
  return b
end

---------------------------------------------------------------- HUD (the cat on screen)
local CAT_SIZE = 120

function TCF:CreateHUD()
  local ui = self.db.ui
  local f = CreateFrame("Frame", "TapCatForeverFrame", UIParent)
  f:SetSize(CAT_SIZE, CAT_SIZE + 40)
  f:SetFrameStrata("MEDIUM")
  f:SetMovable(true); f:SetClampedToScreen(true)
  f:RegisterForDrag("LeftButton")
  self.hud = f

  local cat = TCF.CreateCat(f, CAT_SIZE)
  cat.frame:SetPoint("TOP", f, "TOP", 0, 0)
  self.cat = cat

  -- info block
  local info = CreateFrame("Frame", nil, f)
  info:SetSize(CAT_SIZE + 40, 40); info:SetPoint("TOP", cat.frame, "BOTTOM", 0, 2)
  f.info = info
  f.level = Text(info, "GameFontNormalSmall"); f.level:SetPoint("TOP", 0, 0)
  local xp = CreateFrame("StatusBar", nil, info, BT)
  xp:SetSize(CAT_SIZE - 20, 6); xp:SetPoint("TOP", f.level, "BOTTOM", 0, -2)
  xp:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar")
  xp:SetStatusBarColor(0.58, 0.0, 0.55)
  local xbg = xp:CreateTexture(nil, "BACKGROUND"); xbg:SetAllPoints(); xbg:SetColorTexture(0, 0, 0, 0.55)
  f.xp = xp
  f.stats = Text(info, "GameFontHighlightSmall"); f.stats:SetPoint("TOP", xp, "BOTTOM", 0, -2)

  -- input
  f:SetScript("OnDragStart", function(s)
    if not ui.locked then s.dragging = true; s:StartMoving() end
  end)
  f:SetScript("OnDragStop", function(s)
    s:StopMovingOrSizing()
    local p, _, rp, x, y = s:GetPoint()
    ui.point = { p, rp, x, y }
    s.justDragged = true
    s.dragging = false
  end)
  f:SetScript("OnMouseUp", function(s, button)
    if s.justDragged then s.justDragged = false; return end
    if button == "RightButton" then
      TCF:ToggleWindow()
    elseif button == "LeftButton" then
      TCF.db.stats.pets = TCF.db.stats.pets + 1
      TCF:MarkDirty()
      cat:Pet()
    end
  end)
  f:SetScript("OnMouseWheel", function(s, delta)
    if IsControlKeyDown() then
      ui.scale = max(0.3, min(3, ui.scale + delta * 0.05)); s:ApplySettings()
    elseif IsShiftKeyDown() then
      ui.alpha = max(0.1, min(1, ui.alpha + delta * 0.05)); s:ApplySettings()
    end
    if TCF.window and TCF.window:IsShown() then TCF.window:RefreshSettings() end
  end)
  Tip(f, function(tt)
    tt:AddLine("TapCatForever", 1, 0.72, 0.3)
    tt:AddLine(string.format("Level %d %s", TCF.db.level, TCF:GetTitle()), 1, 1, 1)
    tt:AddLine(" ")
    tt:AddLine("Left-click: pet the cat", 0.8, 0.8, 0.8)
    tt:AddLine("Right-click: wardrobe, shop & settings", 0.8, 0.8, 0.8)
    if not ui.locked then tt:AddLine("Drag: move", 0.8, 0.8, 0.8) end
    tt:AddLine("Ctrl+wheel: size   Shift+wheel: opacity", 0.8, 0.8, 0.8)
  end)

  function f:ResetPosition()
    ui.point = { "BOTTOM", "BOTTOM", 0, 160 }
    self:ApplySettings()
  end

  function f:ApplySettings()
    self:SetScale(ui.scale)
    self:SetAlpha(ui.alpha)
    self:ClearAllPoints()
    local p = ui.point
    self:SetPoint(p[1], UIParent, p[2], p[3], p[4])
    self:SetShown(ui.shown)
    local interactive = not (ui.locked and ui.clickThrough)
    self:EnableMouse(interactive)
    if self.EnableMouseWheel then self:EnableMouseWheel(interactive) end
    local showInfo = not ui.catOnly
    self.level:SetShown(showInfo and ui.showLevel)
    self.xp:SetShown(showInfo and ui.showXP)
    self.stats:SetShown(showInfo and (ui.showTaps or ui.showCoins))
    self:Refresh()
  end

  function f:Refresh()
    local db = TCF.db
    self.level:SetText(string.format("Lv %d  |cffbbbbbb%s|r", db.level, TCF:GetTitle()))
    self.xp:SetMinMaxValues(0, TCF.XPForLevel(db.level))
    self.xp:SetValue(db.xp)
    local parts = {}
    if ui.showTaps then parts[#parts + 1] = TCF.Commas(db.taps) .. " taps" end
    if ui.showCoins then parts[#parts + 1] = coinStr(db.coins, 11) end
    self.stats:SetText(table.concat(parts, "   "))
  end

  f:ApplySettings()
end

---------------------------------------------------------------- main window
function TCF:ToggleWindow()
  if not self.window then self:CreateWindow() end
  if self.window:IsShown() then self.window:Hide() else self.window:Show() end
end

function TCF:CreateWindow()
  local W, H = 800, 540
  local win = CreateFrame("Frame", "TapCatForeverWindow", UIParent, BT)
  win:SetSize(W, H); win:SetPoint("CENTER")
  win:SetFrameStrata("HIGH"); win:SetToplevel(true)
  win:SetMovable(true); win:EnableMouse(true); win:SetClampedToScreen(true)
  win:RegisterForDrag("LeftButton")
  win:SetScript("OnDragStart", win.StartMoving)
  win:SetScript("OnDragStop", win.StopMovingOrSizing)
  if win.SetBackdrop then win:SetBackdrop(BACKDROP_DIALOG) end
  win:Hide()
  tinsert(UISpecialFrames, "TapCatForeverWindow")
  self.window = win

  local title = Text(win, "GameFontNormalLarge", "|cffffb84dTapCat|r|cffffffffForever|r")
  title:SetPoint("TOPLEFT", 22, -18)
  local ver = Text(win, "GameFontDisableSmall", "v" .. TCF.version); ver:SetPoint("LEFT", title, "RIGHT", 8, -1)
  local close = CreateFrame("Button", nil, win, "UIPanelCloseButton"); close:SetPoint("TOPRIGHT", -6, -6)
  local coins = Text(win, "GameFontHighlightLarge"); coins:SetPoint("TOPRIGHT", -44, -18)

  ------------------------------------------------ left column: preview, class, stats
  local left = Panel(win, 236, H - 66); left:SetPoint("TOPLEFT", 16, -46)
  local stage = Panel(left, 216, 210, 0.95); stage:SetPoint("TOP", 0, -10)
  local stageBg = stage:CreateTexture(nil, "BACKGROUND", nil, 1); stageBg:SetPoint("TOPLEFT", 4, -4); stageBg:SetPoint("BOTTOMRIGHT", -4, 4)
  stageBg:SetColorTexture(0.12, 0.10, 0.18, 1)
  local preview = TCF.CreateCat(stage, 190, { preview = true })
  preview.frame:SetPoint("CENTER", 0, -4)
  win.preview = preview
  local tapTimer = 0
  stage:SetScript("OnUpdate", function(_, e)   -- the preview cat taps gently by itself
    tapTimer = tapTimer + e
    if tapTimer > 0.45 then tapTimer = 0; preview:Tap() end
  end)

  local className = Text(left, "GameFontNormal"); className:SetPoint("TOP", stage, "BOTTOM", 0, -6)
  local classBtns = {}
  for i, cl in ipairs(TCF.CLASSES) do
    local b = CreateFrame("Button", nil, left)
    b:SetSize(23, 23)
    b:SetPoint("TOPLEFT", left, "TOPLEFT", 9 + (i - 1) * 24.5, -246)
    local t = b:CreateTexture(nil, "ARTWORK"); t:SetAllPoints()
    TCF.SetClassIcon(t, cl.key)
    b.sel = b:CreateTexture(nil, "OVERLAY"); b.sel:SetPoint("TOPLEFT", -5, 5); b.sel:SetPoint("BOTTOMRIGHT", 5, -5)
    b.sel:SetTexture("Interface\\Buttons\\CheckButtonHilight"); b.sel:SetBlendMode("ADD")
    b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    b:SetScript("OnClick", function() TCF:SetClass(cl.key); TCF:PlaySound("click") end)
    Tip(b, function(tt)
      tt:AddLine(cl.name, cl.color[1], cl.color[2], cl.color[3])
      tt:AddLine("Dress your cat as a " .. cl.name .. ".", 1, 1, 1, true)
      tt:AddLine("Each class keeps its own outfit.", 0.7, 0.7, 0.7, true)
    end)
    classBtns[i] = b
  end

  local lvl = Text(left, "GameFontHighlight", nil, "LEFT"); lvl:SetPoint("TOPLEFT", 12, -280)
  local xp = CreateFrame("StatusBar", nil, left)
  xp:SetSize(212, 14); xp:SetPoint("TOPLEFT", 12, -298)
  xp:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar"); xp:SetStatusBarColor(0.58, 0.0, 0.55)
  local xbg = xp:CreateTexture(nil, "BACKGROUND"); xbg:SetAllPoints(); xbg:SetColorTexture(0, 0, 0, 0.6)
  local xpText = Text(xp, "GameFontHighlightSmall"); xpText:SetPoint("CENTER")
  local statLines = Text(left, "GameFontHighlightSmall", nil, "LEFT")
  statLines:SetPoint("TOPLEFT", 12, -322); statLines:SetWidth(212); statLines:SetSpacing(3)

  ------------------------------------------------ right column: tabs
  local right = Panel(win, W - 280, H - 98); right:SetPoint("TOPLEFT", left, "TOPRIGHT", 12, -32)
  local tabs, pages = {}, {}
  local tabNames = { "Wardrobe", "Shop", "Achievements", "Settings" }
  local function SelectTab(i)
    win.tab = i
    for j, p in ipairs(pages) do p:SetShown(j == i) end
    for j, t in ipairs(tabs) do if j == i then t:LockHighlight() else t:UnlockHighlight() end end
    win:Refresh()
  end
  for i, n in ipairs(tabNames) do
    local b = Button(win, n, 118, 24, function() SelectTab(i); TCF:PlaySound("click") end)
    b:SetPoint("BOTTOMLEFT", right, "TOPLEFT", (i - 1) * 122, 4)
    tabs[i] = b
    local p = CreateFrame("Frame", nil, right); p:SetAllPoints(); p:Hide()
    pages[i] = p
  end

  ------------------------------------------------ Wardrobe
  local wd = pages[1]
  win.slot = "head"
  win.showLocked = true
  local slotBtns = {}
  for i, s in ipairs(TCF.SLOTS) do
    local b = CreateFrame("Button", nil, wd)
    b:SetSize(34, 34); b:SetPoint("TOPLEFT", 12 + (i - 1) * 38, -12)
    local t = b:CreateTexture(nil, "ARTWORK"); t:SetAllPoints(); t:SetTexture(TCF.Icon(s.icon))
    t:SetTexCoord(0.07, 0.93, 0.07, 0.93)
    b.sel = b:CreateTexture(nil, "OVERLAY"); b.sel:SetAllPoints()
    b.sel:SetTexture("Interface\\Buttons\\CheckButtonHilight"); b.sel:SetBlendMode("ADD")
    b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    b:SetScript("OnClick", function() win.slot = s.key; win.page = 1; win:RefreshWardrobe(); TCF:PlaySound("click") end)
    Tip(b, function(tt)
      tt:AddLine(s.name, 1, 0.82, 0)
      tt:AddLine(s.look and "Shared by every class." or "Saved separately for each class.", 0.8, 0.8, 0.8)
    end)
    b.key = s.key
    slotBtns[i] = b
  end
  local slotTitle = Text(wd, "GameFontNormal", nil, "LEFT"); slotTitle:SetPoint("TOPLEFT", 14, -54)
  local lockedCB = CreateFrame("CheckButton", nil, wd, "UICheckButtonTemplate")
  lockedCB:SetSize(24, 24); lockedCB:SetPoint("TOPRIGHT", -110, -50)
  local lcText = Text(wd, "GameFontHighlightSmall", "Show uncollected"); lcText:SetPoint("LEFT", lockedCB, "RIGHT", 0, 1)
  lockedCB:SetChecked(true)
  lockedCB:SetScript("OnClick", function(s) win.showLocked = s:GetChecked() and true or false; win.page = 1; win:RefreshWardrobe() end)

  local COLS, ROWS, CELL, GAP = 8, 6, 54, 5
  local cells = {}
  local grid = CreateFrame("Frame", nil, wd)
  grid:SetSize(COLS * (CELL + GAP), ROWS * (CELL + GAP)); grid:SetPoint("TOP", 0, -76)
  for i = 1, COLS * ROWS do
    local c = ItemCell(grid, CELL)
    c:SetPoint("TOPLEFT", ((i - 1) % COLS) * (CELL + GAP), -floor((i - 1) / COLS) * (CELL + GAP))
    c:RegisterForClicks("LeftButtonUp", "RightButtonUp")
    c:SetScript("OnClick", function(s)
      local it = s.item
      if not it or not TCF.db.owned[it.id] then return end
      if TCF:IsEquipped(it) then TCF:Unequip(it.slot) else TCF:Equip(it) end
      TCF:PlaySound("click")
    end)
    c:SetScript("OnEnter", function(s)
      GameTooltip:SetOwner(s, "ANCHOR_RIGHT"); TCF:ItemTooltip(GameTooltip, s.item)
      if TCF.db.owned[s.item.id] then
        GameTooltip:AddLine(TCF:IsEquipped(s.item) and "Click to unequip" or "Click to equip", 0, 1, 0)
      end
      GameTooltip:Show()
      win.preview:ApplyAppearance(TCF:GetAppearance(nil, s.item))
    end)
    c:SetScript("OnLeave", function() GameTooltip:Hide(); win.preview:ApplyAppearance(TCF:GetAppearance()) end)
    cells[i] = c
  end
  local pageText = Text(wd, "GameFontHighlightSmall"); pageText:SetPoint("BOTTOM", 0, 16)
  local prev = Button(wd, "<", 28, 22, function() win.page = max(1, (win.page or 1) - 1); win:RefreshWardrobe() end)
  prev:SetPoint("RIGHT", pageText, "LEFT", -10, 0)
  local nextB = Button(wd, ">", 28, 22, function() win.page = (win.page or 1) + 1; win:RefreshWardrobe() end)
  nextB:SetPoint("LEFT", pageText, "RIGHT", 10, 0)
  local unequip = Button(wd, "Unequip slot", 110, 22, function() TCF:Unequip(win.slot) end)
  unequip:SetPoint("BOTTOMLEFT", 12, 12)
  local collected = Text(wd, "GameFontDisableSmall", nil, "RIGHT"); collected:SetPoint("BOTTOMRIGHT", -14, 18)
  wd:EnableMouseWheel(true)
  wd:SetScript("OnMouseWheel", function(_, d) win.page = max(1, (win.page or 1) - d); win:RefreshWardrobe() end)

  function win:WardrobeItems()
    local list = {}
    local class = TCF.db.class
    for _, it in ipairs(TCF.ITEM_LIST) do
      if it.slot == self.slot and (not it.class or it.class == class)
        and (self.showLocked or TCF.db.owned[it.id]) then
        list[#list + 1] = it
      end
    end
    table.sort(list, function(a, b)
      local ao, bo = TCF.db.owned[a.id] and 1 or 0, TCF.db.owned[b.id] and 1 or 0
      if ao ~= bo then return ao > bo end
      if (a.class and 1 or 0) ~= (b.class and 1 or 0) then return a.class ~= nil end
      if a.art ~= b.art then return a.art < b.art end
      if a.rarity ~= b.rarity then return a.rarity < b.rarity end
      return a.name < b.name
    end)
    return list
  end

  function win:RefreshWardrobe()
    for _, b in ipairs(slotBtns) do b.sel:SetShown(b.key == self.slot) end
    local s = TCF.SLOT_BY_KEY[self.slot]
    local cl = TCF.CLASS_BY_KEY[TCF.db.class]
    slotTitle:SetText(s.name .. (s.look and "  |cff888888(all classes)|r" or ("  |cff888888(" .. cl.name .. ")|r")))
    local list = self:WardrobeItems()
    local per = COLS * ROWS
    local pagesN = max(1, math.ceil(#list / per))
    self.page = min(max(1, self.page or 1), pagesN)
    local owned = 0
    for _, it in ipairs(list) do if TCF.db.owned[it.id] then owned = owned + 1 end end
    for i = 1, per do
      local it = list[(self.page - 1) * per + i]
      if it then cells[i]:SetItem(it, TCF.db.owned[it.id], TCF:IsEquipped(it)) else cells[i]:Hide() end
    end
    pageText:SetText(string.format("Page %d / %d", self.page, pagesN))
    prev:SetEnabled(self.page > 1); nextB:SetEnabled(self.page < pagesN)
    unequip:SetEnabled(self.slot ~= "fur")
    collected:SetText(string.format("%d collected", owned))
  end

  ------------------------------------------------ Shop
  local sh = pages[2]
  local shopTitle = Text(sh, "GameFontNormalLarge", "Daily Wares"); shopTitle:SetPoint("TOPLEFT", 16, -14)
  local resetText = Text(sh, "GameFontDisableSmall", nil, "LEFT"); resetText:SetPoint("LEFT", shopTitle, "RIGHT", 10, -1)
  local reroll = Button(sh, "New Stock", 150, 22, function()
    if TCF:RerollShop() then TCF:PlaySound("buy") end
  end)
  reroll:SetPoint("TOPRIGHT", -14, -12)
  Tip(reroll, function(tt)
    tt:AddLine("Refresh the daily wares", 1, 0.82, 0)
    tt:AddLine("The price doubles with each refresh, and resets at midnight.", 1, 1, 1, true)
  end)
  local cards = {}
  for i = 1, 6 do
    local c = Panel(sh, 160, 112, 0.9)
    c:SetPoint("TOPLEFT", 14 + ((i - 1) % 3) * 166, -42 - floor((i - 1) / 3) * 118)
    c.cell = ItemCell(c, 56); c.cell:SetPoint("TOPLEFT", 8, -8)
    c.cell:SetScript("OnEnter", function(s)
      GameTooltip:SetOwner(s, "ANCHOR_RIGHT"); TCF:ItemTooltip(GameTooltip, s.item); GameTooltip:Show()
      if TCF:CanEquip(s.item) then win.preview:ApplyAppearance(TCF:GetAppearance(nil, s.item)) end
    end)
    c.cell:SetScript("OnLeave", function() GameTooltip:Hide(); win.preview:ApplyAppearance(TCF:GetAppearance()) end)
    c.name = Text(c, "GameFontNormalSmall", nil, "LEFT"); c.name:SetPoint("TOPLEFT", c.cell, "TOPRIGHT", 6, 0)
    c.name:SetWidth(84); c.name:SetHeight(42); c.name:SetJustifyV("TOP")
    c.cls = Text(c, "GameFontDisableSmall", nil, "LEFT"); c.cls:SetPoint("BOTTOMLEFT", c.cell, "BOTTOMRIGHT", 6, 2)
    c.price = Text(c, "GameFontHighlight", nil, "LEFT"); c.price:SetPoint("BOTTOMLEFT", 10, 12)
    c.buy = Button(c, "Buy", 60, 20, function() if c.id then TCF:BuyItem(c.id) end end)
    c.buy:SetPoint("BOTTOMRIGHT", -8, 8)
    cards[i] = c
  end
  local chestTitle = Text(sh, "GameFontNormalLarge", "Treasure Chests"); chestTitle:SetPoint("TOPLEFT", 16, -288)
  local chestCards = {}
  for i, ch in ipairs(TCF.CHESTS) do
    local c = Panel(sh, 160, 118, 0.9)
    c:SetPoint("TOPLEFT", 14 + (i - 1) * 166, -312)
    local ic = c:CreateTexture(nil, "ARTWORK"); ic:SetSize(40, 40); ic:SetPoint("TOPLEFT", 10, -10)
    ic:SetTexture(TCF.Icon(ch.icon))
    local n = Text(c, "GameFontNormalSmall", ch.name, "LEFT"); n:SetPoint("TOPLEFT", ic, "TOPRIGHT", 6, 0); n:SetWidth(96)
    local d = Text(c, "GameFontDisableSmall", ch.desc, "LEFT"); d:SetPoint("TOPLEFT", 10, -54); d:SetWidth(140)
    c.open = Button(c, coinStr(ch.cost, 12), 72, 20, function() TCF:OpenChest(ch.key) end)
    c.open:SetPoint("BOTTOMLEFT", 8, 8)
    c.key = Button(c, "Key", 66, 20, function() TCF:OpenChest(ch.key, true) end)
    c.key:SetPoint("BOTTOMRIGHT", -8, 8)
    Tip(c.key, function(tt)
      tt:AddLine("Free chest keys", 1, 0.82, 0)
      tt:AddLine("Earned every 5 levels (Strongbox) and every 20 levels (Heroic Cache).", 1, 1, 1, true)
    end)
    Tip(c, function(tt)
      tt:AddLine(ch.name, 1, 0.82, 0)
      local names = {}
      for r = 1, 5 do
        if ch.weights[r] > 0 then
          local col = TCF.RARITY[r]
          tt:AddDoubleLine("|c" .. col.hex .. col.name .. "|r", ch.weights[r] .. "%", 1, 1, 1, 1, 1, 1)
        end
      end
      tt:AddLine("Duplicates are salvaged into TapCoins.", 0.7, 0.7, 0.7, true)
    end)
    c.chest = ch
    chestCards[i] = c
  end
  local lastLoot = Text(sh, "GameFontHighlight", nil, "LEFT"); lastLoot:SetPoint("BOTTOMLEFT", 16, 14); lastLoot:SetWidth(480)

  function win:RefreshShop()
    TCF:BuildShop()
    local secs = TCF:SecondsUntilReset()
    resetText:SetText(string.format("new wares in %dh %dm", floor(secs / 3600), floor(secs % 3600 / 60)))
    reroll:SetText("New Stock " .. coinStr(TCF:RerollCost(), 12))
    reroll:SetEnabled(TCF.db.coins >= TCF:RerollCost())
    local stock = TCF.db.shop.stock
    for i, c in ipairs(cards) do
      local id = stock[i]
      local it = id and TCF.ITEMS[id]
      if it then
        c:Show(); c.id = id
        local owned = TCF.db.owned[id]
        c.cell:SetItem(it, true, false)
        local col = TCF.RARITY[it.rarity]
        c.name:SetText("|c" .. col.hex .. it.name .. "|r")
        local cl = it.class and TCF.CLASS_BY_KEY[it.class]
        c.cls:SetText(cl and cl.name or "Any class")
        c.price:SetText(owned and "|cff20ff20Owned|r" or coinStr(it.price, 13))
        c.buy:SetEnabled(not owned and TCF.db.coins >= it.price)
      else
        c:Hide()
      end
    end
    for _, c in ipairs(chestCards) do
      c.open:SetEnabled(TCF.db.coins >= c.chest.cost)
      local k = TCF.db.keys[c.chest.key] or 0
      c.key:SetText("Key (" .. k .. ")"); c.key:SetShown(c.chest.key ~= "pouch"); c.key:SetEnabled(k > 0)
    end
    local lc = TCF.lastChest
    if lc and lc.item then
      lastLoot:SetText("Last chest: " .. TCF.ItemLink(lc.item) .. (lc.isNew and " |cff20ff20NEW!|r" or
        string.format(" |cffaaaaaa(duplicate, +%d TapCoins)|r", lc.salvage)))
    else
      lastLoot:SetText("|cff888888Earn TapCoins by playing: every 10 key presses = 1 TapCoin.|r")
    end
  end

  ------------------------------------------------ Achievements
  local ac = pages[3]
  local acHeader = Text(ac, "GameFontNormalLarge"); acHeader:SetPoint("TOPLEFT", 16, -14)
  local ROWS_A = 8
  local rows = {}
  for i = 1, ROWS_A do
    local r = Panel(ac, 488, 46, 0.85)
    r:SetPoint("TOPLEFT", 12, -40 - (i - 1) * 49)
    r.icon = r:CreateTexture(nil, "ARTWORK"); r.icon:SetSize(34, 34); r.icon:SetPoint("LEFT", 6, 0)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("TOPLEFT", r.icon, "TOPRIGHT", 8, -1)
    r.desc = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.desc:SetPoint("BOTTOMLEFT", r.icon, "BOTTOMRIGHT", 8, 2)
    r.bar = CreateFrame("StatusBar", nil, r); r.bar:SetSize(150, 12); r.bar:SetPoint("TOPRIGHT", -10, -8)
    r.bar:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar")
    local bg = r.bar:CreateTexture(nil, "BACKGROUND"); bg:SetAllPoints(); bg:SetColorTexture(0, 0, 0, 0.6)
    r.barText = Text(r.bar, "GameFontHighlightSmall"); r.barText:SetPoint("CENTER")
    r.reward = Text(r, "GameFontHighlightSmall", nil, "RIGHT"); r.reward:SetPoint("BOTTOMRIGHT", -10, 6)
    r:SetScript("OnLeave", function() GameTooltip:Hide() end)
    rows[i] = r
  end
  local acPage = Text(ac, "GameFontHighlightSmall"); acPage:SetPoint("BOTTOM", 0, 12)
  ac:EnableMouseWheel(true)
  ac:SetScript("OnMouseWheel", function(_, d) win.acScroll = max(0, (win.acScroll or 0) - d); win:RefreshAchievements() end)

  function win:RefreshAchievements()
    local list, done = {}, 0
    for _, a in ipairs(TCF.ACHIEVEMENTS) do
      list[#list + 1] = a
      if TCF.db.achievements[a.id] then done = done + 1 end
    end
    acHeader:SetText(string.format("Achievements  |cffffffff%d / %d|r", done, #list))
    local maxScroll = max(0, #list - ROWS_A)
    self.acScroll = min(self.acScroll or 0, maxScroll)
    for i, r in ipairs(rows) do
      local a = list[i + self.acScroll]
      if a then
        r:Show()
        local got = TCF.db.achievements[a.id]
        local cur = min(TCF:GetStat(a.stat), a.goal)
        r.icon:SetTexture(TCF.Icon(a.icon)); r.icon:SetDesaturated(not got)
        r.name:SetText(got and ("|cffffd100" .. a.name .. "|r") or ("|cffaaaaaa" .. a.name .. "|r"))
        r.desc:SetText(a.desc)
        r.bar:SetMinMaxValues(0, a.goal); r.bar:SetValue(cur)
        r.bar:SetStatusBarColor(got and 0.2 or 0.15, got and 0.8 or 0.45, got and 0.2 or 0.9)
        r.barText:SetText(got and "Complete" or (TCF.Commas(cur) .. " / " .. TCF.Commas(a.goal)))
        local rw = coinStr(a.coins, 12)
        if a.item then rw = rw .. " + " .. TCF.ItemLink(TCF.ITEMS[a.item]) end
        r.reward:SetText(rw)
        if r.SetBackdropBorderColor then
          if got then r:SetBackdropBorderColor(1, 0.82, 0.2, 1) else r:SetBackdropBorderColor(0.45, 0.40, 0.55, 1) end
        end
        r:SetScript("OnEnter", function(s)
          if not a.item then return end
          GameTooltip:SetOwner(s, "ANCHOR_RIGHT"); TCF:ItemTooltip(GameTooltip, TCF.ITEMS[a.item]); GameTooltip:Show()
        end)
      else
        r:Hide()
      end
    end
    acPage:SetText(maxScroll > 0 and "Scroll for more" or "")
  end

  ------------------------------------------------ Settings
  local st = pages[4]
  local ui = TCF.db.ui
  local stTitle = Text(st, "GameFontNormalLarge", "Settings"); stTitle:SetPoint("TOPLEFT", 16, -14)
  local checks = {}
  local function Check(label, key, col, row, tip, after)
    local cb = CreateFrame("CheckButton", nil, st, "UICheckButtonTemplate")
    cb:SetSize(26, 26); cb:SetPoint("TOPLEFT", 14 + col * 250, -44 - row * 30)
    local t = Text(cb, "GameFontHighlight", label, "LEFT"); t:SetPoint("LEFT", cb, "RIGHT", 2, 1)
    cb:SetScript("OnClick", function(s)
      ui[key] = s:GetChecked() and true or false
      TCF.hud:ApplySettings()
      if after then after() end
      TCF:PlaySound("click")
    end)
    if tip then Tip(cb, function(tt) tt:AddLine(label, 1, 0.82, 0); tt:AddLine(tip, 1, 1, 1, true) end) end
    cb.key = key
    checks[#checks + 1] = cb
  end
  Check("Show cat", "shown", 0, 0, "Show or hide the cat on your screen.")
  Check("Lock position", "locked", 0, 1, "Stop the cat being dragged.")
  Check("Click-through when locked", "clickThrough", 0, 2, "When locked, mouse clicks pass straight through the cat.")
  Check("Cat only (hide all text)", "catOnly", 0, 3, "Hide the level, XP bar and counters.")
  Check("Count mouse clicks", "mouse", 0, 4, "Mouse clicks also make the cat tap and earn progress.")
  Check("Show level", "showLevel", 1, 0)
  Check("Show XP bar", "showXP", 1, 1)
  Check("Show tap counter", "showTaps", 1, 2)
  Check("Show TapCoins", "showCoins", 1, 3)
  Check("Popups on cat", "popups", 1, 4, "Floating text for level ups, loot and achievements.")
  Check("Sounds", "sound", 0, 5)
  Check("Chat messages", "chat", 1, 5)

  local function Slider(label, minV, maxV, step, y, get, set, fmt)
    local s = CreateFrame("Slider", nil, st, BT)
    s:SetOrientation("HORIZONTAL"); s:SetSize(220, 16); s:SetPoint("TOPLEFT", 22, y)
    if s.SetBackdrop then
      s:SetBackdrop({ bgFile = "Interface\\Buttons\\UI-SliderBar-Background", edgeFile = "Interface\\Buttons\\UI-SliderBar-Border",
        tile = true, tileSize = 8, edgeSize = 8, insets = { left = 3, right = 3, top = 6, bottom = 6 } })
    end
    s:SetThumbTexture("Interface\\Buttons\\UI-SliderBar-Button-Horizontal")
    s:SetMinMaxValues(minV, maxV); s:SetValueStep(step)
    if s.SetObeyStepOnDrag then s:SetObeyStepOnDrag(true) end
    local t = Text(s, "GameFontHighlight", nil, "LEFT"); t:SetPoint("BOTTOMLEFT", s, "TOPLEFT", 0, 3)
    s:SetScript("OnValueChanged", function(_, v)
      v = floor(v / step + 0.5) * step
      set(v); t:SetText(string.format(fmt, label, v)); TCF.hud:ApplySettings()
    end)
    s.Sync = function() s:SetValue(get()); t:SetText(string.format(fmt, label, get())) end
    return s
  end
  local scaleS = Slider("Cat size", 0.3, 3, 0.05, -250, function() return ui.scale end, function(v) ui.scale = v end, "%s: %.2fx")
  local alphaS = Slider("Opacity", 0.1, 1, 0.05, -300, function() return ui.alpha end, function(v) ui.alpha = v end, "%s: %.2f")
  local resetB = Button(st, "Reset position", 130, 22, function() TCF.hud:ResetPosition() end)
  resetB:SetPoint("TOPLEFT", 280, -246)
  local mmB = Button(st, "Toggle minimap icon", 160, 22, function()
    ui.minimap.hide = not ui.minimap.hide; TCF:UpdateMinimapButton()
  end)
  mmB:SetPoint("TOPLEFT", 280, -278)
  local help = Text(st, "GameFontDisableSmall", nil, "LEFT"); help:SetPoint("BOTTOMLEFT", 16, 14); help:SetWidth(490)
  help:SetText("Ctrl + mouse wheel over the cat resizes it, Shift + wheel changes opacity.\n" ..
    "Slash commands: /tapcat (or /tcf) show | hide | lock | unlock | reset | scale <n> | stats\n" ..
    "All progress is shared by every character on your account.")

  function win:RefreshSettings()
    for _, cb in ipairs(checks) do cb:SetChecked(ui[cb.key] and true or false) end
    scaleS.Sync(); alphaS.Sync()
  end

  ------------------------------------------------ refresh
  function win:RefreshLight()
    local db = TCF.db
    coins:SetText(coinStr(db.coins, 18))
    lvl:SetText(string.format("Level %d  |cffbbbbbb%s|r", db.level, TCF:GetTitle()))
    local need = TCF.XPForLevel(db.level)
    xp:SetMinMaxValues(0, need); xp:SetValue(db.xp)
    xpText:SetText(TCF.Commas(db.xp) .. " / " .. TCF.Commas(need))
    local n, total = TCF:CountOwned()
    local done = 0
    for _ in pairs(db.achievements) do done = done + 1 end
    statLines:SetText(string.format(
      "Lifetime taps: |cffffffff%s|r\nCollection: |cffffffff%d / %d|r\nAchievements: |cffffffff%d / %d|r\nTapCoins earned: |cffffffff%s|r\nChest keys: |cffffffff%d|r Strongbox, |cffffffff%d|r Heroic\nDaily streak: |cffffffff%d|r (best %d)",
      TCF.Commas(db.taps), n, total, done, #TCF.ACHIEVEMENTS, TCF.Commas(db.coinsEarned),
      db.keys.strong, db.keys.heroic, db.daily.streak, db.daily.best))
    if self.tab == 2 then self:RefreshShop() elseif self.tab == 3 then self:RefreshAchievements() end
  end

  function win:Refresh()
    local cl = TCF.CLASS_BY_KEY[TCF.db.class]
    className:SetText(cl.name)
    className:SetTextColor(cl.color[1], cl.color[2], cl.color[3])
    for i, b in ipairs(classBtns) do b.sel:SetShown(TCF.CLASSES[i].key == TCF.db.class) end
    self.preview:ApplyAppearance(TCF:GetAppearance())
    if self.tab == 1 then self:RefreshWardrobe()
    elseif self.tab == 4 then self:RefreshSettings() end
    self:RefreshLight()
  end

  win:SetScript("OnShow", function(s) s:Refresh() end)
  SelectTab(1)
end

---------------------------------------------------------------- class icons
-- Modern clients (WoW: Forever / Midnight) ship class icons as atlases.
function TCF.SetClassIcon(t, key)
  local atlas = "classicon-" .. key:lower()
  if t.SetAtlas and C_Texture and C_Texture.GetAtlasInfo and C_Texture.GetAtlasInfo(atlas) then
    t:SetAtlas(atlas)
    return
  end
  t:SetTexture("Interface\\TargetingFrame\\UI-Classes-Circles")
  local tc = CLASS_ICON_TCOORDS and CLASS_ICON_TCOORDS[key]
  if tc then t:SetTexCoord(unpack(tc)) end
end

---------------------------------------------------------------- game options panel (Esc > Options > AddOns)
function TCF:RegisterSettingsPanel()
  if self.settingsCategory or not (Settings and Settings.RegisterCanvasLayoutCategory and Settings.RegisterAddOnCategory) then return end
  local panel = CreateFrame("Frame")
  panel:Hide()
  local title = Text(panel, "GameFontNormalHuge", "|cffffb84dTapCat|r|cffffffffForever|r")
  title:SetPoint("TOPLEFT", 16, -16)
  local desc = Text(panel, "GameFontHighlight", nil, "LEFT")
  desc:SetPoint("TOPLEFT", title, "BOTTOMLEFT", 0, -10); desc:SetWidth(560)
  desc:SetText("Your tapping cat companion. The wardrobe, shop, achievements and all settings live in the TapCatForever window.\n\nRight-click the cat, click the minimap button, or type /tapcat to open it.")
  local open = Button(panel, "Open TapCatForever", 180, 26, function()
    if SettingsPanel and SettingsPanel.Close then pcall(SettingsPanel.Close, SettingsPanel, true) end
    if not TCF.window or not TCF.window:IsShown() then TCF:ToggleWindow() end
  end)
  open:SetPoint("TOPLEFT", desc, "BOTTOMLEFT", 0, -16)
  local ok, category = pcall(Settings.RegisterCanvasLayoutCategory, panel, "TapCatForever")
  if ok and category then
    pcall(Settings.RegisterAddOnCategory, category)
    self.settingsCategory = category
  end
end

---------------------------------------------------------------- minimap button
function TCF:CreateMinimapButton()
  if not Minimap then return end
  local b = CreateFrame("Button", "TapCatForeverMinimapButton", Minimap)
  b:SetSize(31, 31); b:SetFrameStrata("MEDIUM"); b:SetFrameLevel(8)
  b:RegisterForClicks("LeftButtonUp", "RightButtonUp"); b:RegisterForDrag("LeftButton")
  local bg = b:CreateTexture(nil, "BACKGROUND"); bg:SetSize(20, 20); bg:SetPoint("CENTER")
  bg:SetTexture("Interface\\Minimap\\UI-Minimap-Background")
  local fur = b:CreateTexture(nil, "ARTWORK", nil, 0); fur:SetSize(20, 20); fur:SetPoint("CENTER", 0, 1)
  fur:SetTexture(ART .. "cat_fur", nil, nil, "NEAREST"); fur:SetTexCoord(0.2, 0.8, 0.1, 0.7)
  local face = b:CreateTexture(nil, "ARTWORK", nil, 1); face:SetAllPoints(fur)
  face:SetTexture(ART .. "face_happy", nil, nil, "NEAREST"); face:SetTexCoord(0.2, 0.8, 0.1, 0.7)
  b.fur = fur
  local border = b:CreateTexture(nil, "OVERLAY"); border:SetSize(53, 53); border:SetPoint("TOPLEFT")
  border:SetTexture("Interface\\Minimap\\MiniMap-TrackingBorder")
  b:SetHighlightTexture("Interface\\Minimap\\UI-Minimap-ZoomButton-Highlight")
  self.minimapButton = b

  local function place()
    local a = math.rad(TCF.db.ui.minimap.angle)
    local r = (Minimap:GetWidth() / 2) + 10
    b:ClearAllPoints(); b:SetPoint("CENTER", Minimap, "CENTER", math.cos(a) * r, math.sin(a) * r)
  end
  b:SetScript("OnDragStart", function(s)
    s:SetScript("OnUpdate", function()
      local mx, my = Minimap:GetCenter()
      local cx, cy = GetCursorPosition()
      local sc = Minimap:GetEffectiveScale()
      TCF.db.ui.minimap.angle = math.deg(math.atan2(cy / sc - my, cx / sc - mx))
      place()
    end)
  end)
  b:SetScript("OnDragStop", function(s) s:SetScript("OnUpdate", nil) end)
  b:SetScript("OnClick", function(_, button)
    if button == "RightButton" then
      TCF.db.ui.shown = not TCF.db.ui.shown; TCF.hud:ApplySettings()
      if TCF.window and TCF.window:IsShown() then TCF.window:RefreshSettings() end
    else
      TCF:ToggleWindow()
    end
  end)
  Tip(b, function(tt)
    tt:AddLine("TapCatForever", 1, 0.72, 0.3)
    tt:AddLine(string.format("Level %d  |  %s TapCoins", TCF.db.level, TCF.Commas(TCF.db.coins)), 1, 1, 1)
    tt:AddLine("Left-click: open window", 0.8, 0.8, 0.8)
    tt:AddLine("Right-click: show / hide cat", 0.8, 0.8, 0.8)
    tt:AddLine("Drag: move this button", 0.8, 0.8, 0.8)
  end)
  place()
  self:UpdateMinimapButton()
end

function TCF:UpdateMinimapButton()
  local b = self.minimapButton
  if not b then return end
  b:SetShown(not self.db.ui.minimap.hide)
  local fur = TCF.ITEMS[self.db.look.fur]
  if fur then b.fur:SetVertexColor(fur.c1[1], fur.c1[2], fur.c1[3]) end
end
