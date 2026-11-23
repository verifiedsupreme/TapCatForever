-- TapCatForever: the main window's size (the grip in its bottom-right corner), the character
-- pane that folds away (the button left of the Compendium) and the compact layout (narrow and
-- tall, round tab buttons).
-- UI.lua's CreateWindow hands over its parts in win.parts and calls TCF.UI.SetupWindowLayout(win).
local ADDON, TCF = ...
local floor, min, max = math.floor, math.min, math.max

TCF.UI = TCF.UI or {}
TCF.WIN_SCALE_MIN, TCF.WIN_SCALE_MAX, TCF.WIN_SCALE_STEP = 0.6, 1.4, 0.05

-- the screen (UIParent) size, or nil outside the game
local function screenSize()
  local w = UIParent and UIParent.GetWidth and UIParent:GetWidth()
  local h = UIParent and UIParent.GetHeight and UIParent:GetHeight()
  if type(w) ~= "number" or w <= 0 then w = nil end
  if type(h) ~= "number" or h <= 0 then h = nil end
  return w, h
end
-- the largest size a w x h window may have: it must fit on the screen (at the default UI scale
-- the screen is 768 tall, less than 620 x 1.4); normal size is always allowed
local function maxScale(w, h)
  local m = TCF.WIN_SCALE_MAX
  local sw, sh = screenSize()
  if sw and w then m = min(m, (sw - 16) / w) end
  if sh and h then m = min(m, (sh - 16) / h) end
  return max(1, floor(m * 100) / 100)
end
-- w, h (optional): the window's layout size, to keep it on the screen
local function clampScale(v, w, h)
  v = tonumber(v) or 1
  if v ~= v then v = 1 end
  return max(TCF.WIN_SCALE_MIN, min(maxScale(w, h), v))
end
TCF.ClampWindowScale = clampScale

local function uiDB() return TCF.db and TCF.db.ui end
-- the full and narrow windows share one size, the compact window has its own (a compact window
-- made bigger to read its small text would be too big as the full window)
local function scaleKey()
  local u = uiDB()
  return (u and u.winCompact) and "winScaleCompact" or "winScale"
end

---------------------------------------------------------------- window size
-- Dragging the grip scales the whole window (every page keeps its layout); the top-left corner
-- stays where it is on the screen. Double-click the grip to go back to normal size.
-- Remembered in db.ui.winScale (compact: db.ui.winScaleCompact; nil = 1).
local function SetupSize(win)
  local U = TCF.UI
  -- move the window so its top-left corner is (x, y) in UIParent units
  local function placeTopLeft(self, x, y)
    local s = self:GetScale() or 1
    self:ClearAllPoints()
    self:SetPoint("TOPLEFT", UIParent, "BOTTOMLEFT", x / s, y / s)
  end
  -- the top-left corner in UIParent units, or nil when the window has no position yet
  function win:ScreenTopLeft()
    local l, t = self:GetLeft(), self:GetTop()
    if type(l) ~= "number" or type(t) ~= "number" then return nil end
    local s = self:GetScale() or 1
    return l * s, t * s
  end
  win.PlaceTopLeft = placeTopLeft

  function win:SetWindowScale(v)
    v = clampScale(v, self.layoutW, self.layoutH)
    local x, y = self:ScreenTopLeft()
    self:SetScale(v)
    if x then placeTopLeft(self, x, y) end
    self.casinoReturn = nil   -- (UI_Window's layouts) the narrow window's place is no longer known
    local ui = uiDB()
    if ui then
      if math.abs(v - 1) < 0.001 then ui[scaleKey()] = nil else ui[scaleKey()] = v end   -- nil: normal size
    end
    if self.OnWindowScale then self:OnWindowScale(v) end
  end
  -- the saved size of the current layout, kept on the screen
  function win:GetWindowScale()
    local u = uiDB()
    return clampScale(u and u[scaleKey()] or 1, self.layoutW, self.layoutH)
  end
  win:SetScale(win:GetWindowScale())

  local grip = CreateFrame("Button", nil, win)
  grip:SetSize(18, 18); grip:SetPoint("BOTTOMRIGHT", -5, 5)
  if grip.SetFrameLevel then grip:SetFrameLevel((win:GetFrameLevel() or 1) + 80) end
  grip:SetNormalTexture("Interface\\ChatFrame\\UI-ChatIM-SizeGrabber-Up")
  grip:SetHighlightTexture("Interface\\ChatFrame\\UI-ChatIM-SizeGrabber-Highlight")
  grip:SetPushedTexture("Interface\\ChatFrame\\UI-ChatIM-SizeGrabber-Down")
  grip:RegisterForClicks("LeftButtonUp")
  win.sizeGrip = grip
  local function cursor()
    local x, y = GetCursorPosition()
    local es = UIParent.GetEffectiveScale and UIParent:GetEffectiveScale() or 1
    if type(es) ~= "number" or es <= 0 then es = 1 end
    return x / es, y / es
  end
  local function stop(g) g:SetScript("OnUpdate", nil); g.dragging = nil end
  grip:SetScript("OnMouseDown", function(g, button)
    if button ~= "LeftButton" then return end
    local x, y = win:ScreenTopLeft()
    if not x then return end
    -- the size follows how far the cursor moves from where it grabbed the grip (a click without
    -- moving changes nothing)
    g.L, g.T, g.dragging, g.moved = x, y, true, nil
    g.s0 = win:GetScale() or 1
    g.cx0, g.cy0 = cursor()
    g:SetScript("OnUpdate", function()
      local cx, cy = cursor()
      if not g.moved then
        if math.abs(cx - g.cx0) + math.abs(cy - g.cy0) < 3 then return end
        g.moved = true
      end
      local w, h = win.layoutW or 920, win.layoutH or 620
      local v = g.s0 + ((cx - g.cx0) / w + (g.cy0 - cy) / h) / 2
      -- from where its corner is, the window must still fit above the screen's bottom edge and
      -- left of its right edge
      local sw = screenSize()
      local room = g.T / h
      if sw then room = min(room, (sw - g.L) / w) end
      if room >= TCF.WIN_SCALE_MIN then v = min(v, room) end
      v = floor(clampScale(v, w, h) * 100 + 0.5) / 100
      if math.abs(v - (win:GetScale() or 1)) >= 0.005 then
        win:SetWindowScale(v)
        -- the corner stays where the drag started, even if the screen edge nudged the window
        placeTopLeft(win, g.L, g.T)
      end
    end)
  end)
  grip:SetScript("OnMouseUp", stop)
  grip:SetScript("OnHide", stop)
  grip:SetScript("OnDoubleClick", function(g) stop(g); win:SetWindowScale(1); TCF:PlaySound("click") end)
  U.Tip(grip, function(tt)
    tt:AddLine("Window size", 1, 0.82, 0)
    tt:AddLine("Drag to make the window bigger or smaller. Double-click to go back to normal size.", 1, 1, 1, true)
    tt:AddLine(string.format("Now: %d%%", floor((win:GetScale() or 1) * 100 + 0.5)), 0.8, 0.8, 0.8)
  end)
end

-- Settings > Cat and display: "Window size" with - and + buttons, in the free spot under the text
-- checkboxes. place(frame, x, y, w, h, kind, label) is the Settings page's own layout helper.
function TCF.UI.WindowSizeControl(win, st, place, x, y, w)
  local U = TCF.UI
  local function step(d)
    win:SetWindowScale(floor(((win:GetScale() or 1) + d * TCF.WIN_SCALE_STEP) * 100 + 0.5) / 100)
    TCF:PlaySound("click")
  end
  local tip = function(tt)
    tt:AddLine("Window size", 1, 0.82, 0)
    tt:AddLine("Make this window bigger or smaller. Everything inside grows or shrinks with it.", 1, 1, 1, true)
    tt:AddLine("You can also drag the grip in the window's bottom-right corner. Double-click the grip to go back to normal size.", 0.8, 0.8, 0.8, true)
  end
  local minus = U.Button(st, "-", 22, 22, function() step(-1) end)
  place(minus, x, y, 22, 22, "button", "Window smaller")
  local plus = U.Button(st, "+", 22, 22, function() step(1) end)
  place(plus, x + 26, y, 22, 22, "button", "Window bigger")
  local label = U.Text(st, "GameFontHighlight", nil, "LEFT")
  place(label, x + 54, y + 4, w - 54, 14, "text", "Window size")
  U.Tip(minus, tip); U.Tip(plus, tip)
  local function sync() label:SetText(string.format("Window size: %d%%", floor((win:GetScale() or 1) * 100 + 0.5))) end
  win.windowSizeControl = { minus = minus, plus = plus, label = label, Sync = sync }
  sync()
  return win.windowSizeControl
end

---------------------------------------------------------------- layouts
-- Three layouts:
--   full     920 x 620: the character pane on the left, two rows of text tabs over the pages
--   narrow   592 x 620: the pane folded away (db.ui.winPaneHidden), the tabs and pages slide left
--   compact  420 x 604: phone-like (db.ui.winCompact): round tab buttons in two rows of five,
--            the pages scaled down to the narrow width, a level and XP line at the bottom, and
--            the character pane as its own view (the cat button or that line opens it)
-- The Casino covers the whole window, so in the narrow layout its tab is full width (the window
-- grows to the left, so the tabs stay where they are); in the compact layout it is scaled down to
-- fit the width.
TCF.WIN_PANE_W = 316 + 12   -- the left column and the gap after it
local ART = TCF.ART_PATH
local RIGHT_X, RIGHT_Y = 16, -106      -- the right column's top-left with the pane folded away
local PAGE_W, PAGE_H = 560, 494        -- every page's own size
local LEFT_W, LEFT_H = 316, 554        -- the character pane's
local CASINO_W, CASINO_H = 888, 554    -- the Casino (its sign and table) covers this much
-- compact: window size, the content width, the round tab rows and where the pages start
local C = { W = 420, H = 604, X = 16, CW = 388, TAB = 44, TAB_Y = -78, TAB_ROW = 64, PAGE_Y = -206 }
C.S = C.CW / PAGE_W                     -- the pages' scale (0.69)
C.PAGE_BOTTOM = C.PAGE_Y - PAGE_H * C.S  -- -548
TCF.WIN_COMPACT = C
local TAB_ICONS = {
  Gear = { "INV_Helmet_03", "Your cat's gear for this class." },
  Adventure = { "INV_Sword_04", "Your cat fights through zones and dungeons." },
  Abilities = { "Spell_Nature_Lightning", "Your cat's class abilities." },
  Expeditions = { "INV_Misc_Map_01", "Send your cats out on expeditions." },
  Professions = { "Trade_BlackSmithing", "Gathering and crafting." },
  Appearance = { "INV_Misc_Cape_02", "The cosmetics you collected. Cosmetic only." },
  Quests = { "INV_Misc_Note_01", "Quests and their rewards." },
  Shop = { "INV_Box_01", "Chests and cosmetics for TapCoins." },   -- a chest: the Treasure Bag next to it is a bag
  Casino = { "INV_Misc_Coin_02", "Slots, blackjack, death roll and rock paper scissors." },
  Leaderboard = { "INV_Crown_02", "Cats of players on your realm." },
}
TCF.WIN_TAB_ICONS = TAB_ICONS

local function IconButton(parent, size, icon)
  local b = CreateFrame("Button", nil, parent)
  b:SetSize(size, size)
  b.icon = b:CreateTexture(nil, "ARTWORK"); b.icon:SetAllPoints()
  if icon then b.icon:SetTexture(TCF.Icon(icon)); b.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93) end
  b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  return b
end

-- a big round button: a WoW icon cut round (where the client can) in a gold ring
local function RoundButton(parent, size, icon)
  local b = CreateFrame("Button", nil, parent)
  b:SetSize(size, size)
  b.glow = b:CreateTexture(nil, "BACKGROUND"); b.glow:SetPoint("CENTER"); b.glow:SetSize(size * 1.3, size * 1.3)
  b.glow:SetTexture(ART .. "win\\tab_glow"); b.glow:SetBlendMode("ADD"); b.glow:Hide()
  b.icon = b:CreateTexture(nil, "ARTWORK"); b.icon:SetPoint("CENTER"); b.icon:SetSize(size * 0.76, size * 0.76)
  b.icon:SetTexture(TCF.Icon(icon)); b.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
  if b.CreateMaskTexture and b.icon.AddMaskTexture then
    local ok, m = pcall(b.CreateMaskTexture, b)
    if ok and m then
      pcall(m.SetTexture, m, "Interface\\CharacterFrame\\TempPortraitAlphaMask", "CLAMPTOBLACKADDITIVE", "CLAMPTOBLACKADDITIVE")
      m:SetAllPoints(b.icon); pcall(b.icon.AddMaskTexture, b.icon, m)
    end
  end
  b.ring = b:CreateTexture(nil, "OVERLAY"); b.ring:SetAllPoints(); b.ring:SetTexture(ART .. "win\\tab_ring")
  function b:SetSelected(on) self.selected = on and true or false; self:ShowGlow() end
  function b:ShowGlow()
    if self.selected then self.glow:SetAlpha(1); self.glow:Show()
    elseif self.hover then self.glow:SetAlpha(0.45); self.glow:Show()
    else self.glow:Hide() end
  end
  return b
end

local function SetupLayout(win)
  local U, P = TCF.UI, win.parts
  local left, right = P.left, P.right
  local iconTabs = P.iconTabs or {}

  ------------------------------------------------ header buttons
  -- the Compendium as an icon, for the narrow window (the text button doesn't fit)
  local compIcon = IconButton(win, 26, "INV_Misc_Book_09")
  compIcon:SetScript("OnClick", function() TCF:ToggleCompendium(); TCF:PlaySound("click") end)
  U.Tip(compIcon, function(tt)
    tt:AddLine("Compendium", 1, 0.82, 0)
    tt:AddLine("Every skin, cosmetic, effect and piece of gear, what you have, and how to get the rest.", 1, 1, 1, true)
  end)
  compIcon:Hide()
  win.compIcon = compIcon
  -- the pane button: the cat with a small arrow (points left: fold away; right: open)
  local pane = IconButton(win, 24, "Ability_Druid_CatForm")
  pane.arrow = pane:CreateTexture(nil, "OVERLAY"); pane.arrow:SetSize(14, 14); pane.arrow:SetPoint("BOTTOMRIGHT", 4, -4)
  pane.arrow:SetTexture("Interface\\ChatFrame\\ChatFrameExpandArrow")
  pane:SetScript("OnClick", function()
    if win:IsCompact() then win:ShowCharacterView(not win.compactChar)
    elseif win:IsCasinoTab() then return
    else win:SetPaneShown(not win:PaneShown()) end
    TCF:PlaySound("click")
  end)
  U.Tip(pane, function(tt)
    tt:AddLine("Character", 1, 0.82, 0)
    if win:IsCompact() then
      tt:AddLine(win.compactChar and "Back to the page you were on." or "Your cat, gear slots, class and stats.", 1, 1, 1, true)
    elseif win:IsCasinoTab() then
      tt:AddLine("The Casino uses the whole window. The character column folds away on the other tabs.", 1, 1, 1, true)
    elseif win:PaneShown() then
      tt:AddLine("Fold away the gear, class and stats column. The window gets narrower.", 1, 1, 1, true)
    else
      tt:AddLine("Show the gear, class and stats column again.", 1, 1, 1, true)
    end
  end)
  win.paneButton = pane
  -- the layout button: compact (a phone) or back to the full window
  local lay = CreateFrame("Button", nil, win)
  lay:SetSize(24, 24)
  lay.icon = lay:CreateTexture(nil, "ARTWORK"); lay.icon:SetAllPoints()
  lay:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  lay:SetScript("OnClick", function() win:SetCompact(not win:IsCompact()); TCF:PlaySound("click") end)
  U.Tip(lay, function(tt)
    if win:IsCompact() then
      tt:AddLine("Full window", 1, 0.82, 0)
      tt:AddLine(win:PaneShown() and "Back to the wide window with the character column." or "Back to the wide window.", 1, 1, 1, true)
    else
      tt:AddLine("Compact window", 1, 0.82, 0)
      tt:AddLine("A narrow, tall window like a phone screen, with round tab buttons. Pages are shown smaller to fit.", 1, 1, 1, true)
      tt:AddLine("Make it bigger or smaller with the grip in the bottom-right corner.", 0.8, 0.8, 0.8, true)
    end
  end)
  win.layoutButton = lay

  ------------------------------------------------ compact: round tab buttons
  local rtabs = CreateFrame("Frame", nil, win)
  rtabs:SetSize(C.CW, 2 * C.TAB_ROW); rtabs:SetPoint("TOPLEFT", win, "TOPLEFT", C.X, C.TAB_Y)
  rtabs:Hide()
  local round = {}
  win.roundTabs = round
  local slots = {}
  -- in the text tabs' order (UI.lua win.tabOrder: the Casino sits where Achievements was)
  for _, i in ipairs(win.tabOrder or {}) do if not iconTabs[i] then slots[#slots + 1] = i end end
  if #slots == 0 then for i in ipairs(win.tabNames or {}) do if not iconTabs[i] then slots[#slots + 1] = i end end end
  local questsTab
  for i, n in ipairs(win.tabNames or {}) do if n == "Quests" then questsTab = i end end
  local perRow = math.ceil(#slots / 2)
  local step = C.CW / perRow
  for k, i in ipairs(slots) do
    local name = win.tabNames[i]
    local info = TAB_ICONS[name] or { "INV_Misc_QuestionMark", nil }
    local b = RoundButton(rtabs, C.TAB, info[1])
    local col, row = (k - 1) % perRow, floor((k - 1) / perRow)
    b:SetPoint("TOP", rtabs, "TOPLEFT", step * (col + 0.5), -row * C.TAB_ROW)
    b.label = U.Text(rtabs, "GameFontHighlightSmall", name); b.label:SetPoint("TOP", b, "BOTTOM", 0, -1)
    b.tab, b.name = i, name
    b:SetScript("OnClick", function() win:SelectTab(i); TCF:PlaySound("click") end)
    b:SetScript("OnEnter", function(self)
      self.hover = true; self:ShowGlow()
      GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
      GameTooltip:AddLine(name, 1, 0.82, 0)
      if info[2] then GameTooltip:AddLine(info[2], 1, 1, 1, true) end
      GameTooltip:Show()
    end)
    b:SetScript("OnLeave", function(self) self.hover = nil; self:ShowGlow(); GameTooltip:Hide() end)
    round[i] = b
  end

  ------------------------------------------------ compact: level, XP and Power at the bottom
  local strip = CreateFrame("Button", nil, win)
  strip:SetSize(C.CW - 20, 32); strip:SetPoint("TOPLEFT", win, "TOPLEFT", C.X, C.PAGE_BOTTOM - 8)
  strip.lvl = U.Text(strip, "GameFontHighlightSmall", nil, "LEFT"); strip.lvl:SetPoint("TOPLEFT", 0, 0)
  strip.power = U.Text(strip, "GameFontNormalSmall", nil, "RIGHT"); strip.power:SetPoint("TOPRIGHT", 0, 0)
  local xp = CreateFrame("StatusBar", nil, strip)
  xp:SetSize(C.CW - 20, 10); xp:SetPoint("TOPLEFT", 0, -16)
  xp:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar"); xp:SetStatusBarColor(0.58, 0.0, 0.55)
  local xbg = xp:CreateTexture(nil, "BACKGROUND"); xbg:SetAllPoints(); xbg:SetColorTexture(0, 0, 0, 0.6)
  strip.xp = xp
  strip:SetScript("OnClick", function() win:ShowCharacterView(true); TCF:PlaySound("click") end)
  U.Tip(strip, function(tt)
    tt:AddLine("Character", 1, 0.82, 0)
    tt:AddLine("Click to see your cat, gear slots, class and stats.", 1, 1, 1, true)
  end)
  strip:Hide()
  win.compactStrip = strip

  ------------------------------------------------ more header buttons
  -- Buttons other parts add to the header register here, so the narrow and compact headers find a
  -- place for them: win:AddHeaderButton(button, placeFull). placeFull(button) anchors it in the
  -- full window's header (without it, where it is anchored when registered).
  win.headerExtras = win.headerExtras or {}
  function win:AddHeaderButton(b, placeFull)
    if not b then return end
    local e = { frame = b, placeFull = placeFull }
    if not placeFull and b.GetNumPoints and b.GetPoint then
      local pts = {}
      local ok, n = pcall(b.GetNumPoints, b)
      for k = 1, (ok and type(n) == "number" and n or 0) do pts[k] = { b:GetPoint(k) } end
      e.points = pts
    end
    self.headerExtras[#self.headerExtras + 1] = e
    if self.layoutMode then self:ApplyLayout() end
  end

  ------------------------------------------------ try-on preview with the character column hidden
  -- The Appearance, Shop, Gear and Professions pages try items on the cat in the character column
  -- (win.preview). With that column folded away or in compact, a small cat beside the window shows
  -- the try-on while an item is hovered.
  local tryOn = CreateFrame("Frame", nil, win, U.BT)
  tryOn:SetSize(150, 166)
  if tryOn.SetBackdrop then tryOn:SetBackdrop(U.BACKDROP_DIALOG) end
  if tryOn.SetFrameLevel then tryOn:SetFrameLevel((win:GetFrameLevel() or 1) + 90) end
  tryOn.label = U.Text(tryOn, "GameFontNormalSmall", "Trying on"); tryOn.label:SetPoint("TOP", 0, -12)
  tryOn:Hide()
  win.tryOnStage = tryOn
  local function lookSig(look)
    local t = {}
    for k, v in pairs(look or {}) do
      local id = v
      if type(v) == "table" then id = v.id or v.key or v.name or tostring(v) end
      t[#t + 1] = tostring(k) .. "=" .. tostring(id)
    end
    table.sort(t)
    return table.concat(t, ";")
  end
  -- beside the window where there is room on the screen (left first, where the column was), else
  -- inside its top-right corner
  local function placeTryOn()
    tryOn:ClearAllPoints()
    local s = win:GetScale() or 1
    local x = win:ScreenTopLeft()
    local sw = screenSize()
    local top = (win:IsCompact() and C.PAGE_Y or RIGHT_Y)
    local tw = 150 + 4
    if not x or x >= tw * s then tryOn:SetPoint("TOPRIGHT", win, "TOPLEFT", -4, top)
    elseif sw and x + ((win.layoutW or 920) + tw) * s <= sw then tryOn:SetPoint("TOPLEFT", win, "TOPRIGHT", 4, top)
    else tryOn:SetPoint("TOPRIGHT", win, "TOPRIGHT", -16, top) end
  end
  function win:MirrorPreview(look)
    if left:IsShown() or not self:IsShown() then tryOn:Hide(); return end
    if not look or lookSig(look) == lookSig(TCF:GetAppearance()) then tryOn:Hide(); return end
    if not tryOn.cat then
      tryOn.cat = TCF.CreateCat(tryOn, 128, { preview = true })
      tryOn.cat.frame:SetPoint("BOTTOM", 0, 10)
    end
    placeTryOn()
    tryOn:Show()
    tryOn.cat:ApplyAppearance(look)
  end
  local pv = win.preview
  if pv and pv.ApplyAppearance then
    local apply = pv.ApplyAppearance
    pv.ApplyAppearance = function(cat, look, ...)
      local r = apply(cat, look, ...)
      if win.MirrorPreview then win:MirrorPreview(look) end
      return r
    end
  end

  ------------------------------------------------ state
  local ui = uiDB
  function win:IsCasinoTab() return self.TAB_CASINO ~= nil and self.tab == self.TAB_CASINO end
  function win:IsCompact() local u = ui(); return u and u.winCompact and true or false end
  -- the saved choice (the Casino tab shows full width whatever it is)
  function win:PaneShown() local u = ui(); return not (u and u.winPaneHidden) end
  function win:SetPaneShown(show)
    local u = ui()
    if u then if show then u.winPaneHidden = nil else u.winPaneHidden = true end end
    self:ApplyLayout()
  end
  function win:SetCompact(on)
    local u = ui()
    if u then if on then u.winCompact = true else u.winCompact = nil end end
    self.compactChar = nil
    self:ApplyLayout()
    self:Refresh()
  end
  -- compact only: the character pane in place of the page
  function win:ShowCharacterView(on)
    self.compactChar = (on and self:IsCompact()) and true or nil
    self:ApplyLayout()
  end
  function win:LayoutMode()
    if self:IsCompact() then return "compact" end
    if self:PaneShown() or self:IsCasinoTab() then return "full" end
    return "narrow"
  end

  ------------------------------------------------ placing things
  local function placeCasino(mode)
    local cv = TCF.casinoView
    if not cv then return end
    local sign = cv.sign
    cv:ClearAllPoints(); if sign then sign:ClearAllPoints() end
    if mode == "compact" then
      -- scaled to fit the width, in the middle of the page area
      local k = C.CW / CASINO_W
      local top = -C.PAGE_Y + (PAGE_H * C.S - CASINO_H * k) / 2
      cv:SetScale(k / C.S)
      cv:SetPoint("TOPLEFT", win, "TOPLEFT", C.X / k, -(top + 60 * k) / k)
      if sign then sign:SetPoint("TOPLEFT", win, "TOPLEFT", C.X / k, -top / k) end
    else
      cv:SetScale(1)
      cv:SetPoint("TOPLEFT", win, "TOPLEFT", 16, -106)
      if sign then sign:SetPoint("TOPLEFT", win, "TOPLEFT", 16, -46) end
    end
  end

  function win:ApplyLayout(keepRight)
    local mode = self:LayoutMode()
    local W, H = P.W or 920, P.H or 620
    local compact = mode == "compact"
    local paneW = (mode == "full") and TCF.WIN_PANE_W or 0
    local w, h = W - TCF.WIN_PANE_W + paneW, H
    if compact then w, h = C.W, C.H end
    -- keep the top-left corner where it is, or with keepRight the right column (tabs and pages)
    local x, y = self:ScreenTopLeft()
    local back = self.casinoReturn
    if not (mode == "full" and self:IsCasinoTab() and not self:PaneShown()) then self.casinoReturn = nil end
    if x and keepRight and self.layoutPaneW and self.layoutPaneW ~= paneW and not compact and self.layoutMode ~= "compact" then
      if paneW < self.layoutPaneW and back then
        -- back from the Casino: exactly where the narrow window was (the screen edge may have
        -- nudged the full-width window)
        x, y = back[1], back[2]
      else
        if paneW > self.layoutPaneW then self.casinoReturn = { x, y } end
        x = x + (self.layoutPaneW - paneW) * (self:GetScale() or 1)
      end
    end
    self:SetSize(w, h)
    self.layoutW, self.layoutH, self.layoutMode, self.layoutPaneW = w, h, mode, paneW
    -- each layout's own size (the compact one is saved apart), kept on the screen
    local sc = self:GetWindowScale()
    if math.abs(sc - (self:GetScale() or 1)) >= 0.001 then
      self:SetScale(sc)
      if self.OnWindowScale then self:OnWindowScale(sc) end
    end
    if x and self.layoutPlaced then self:PlaceTopLeft(x, y) end
    self.layoutPlaced = true
    if not compact then self.compactChar = nil end
    local charView = compact and self.compactChar

    -- the character pane: on the left (full), folded away (narrow), or its own view (compact)
    left:ClearAllPoints()
    if compact then
      left:SetScale(C.S)
      left:SetPoint("TOPLEFT", self, "TOPLEFT", (C.X + (C.CW - LEFT_W * C.S) / 2) / C.S, C.PAGE_Y / C.S)
    else
      left:SetScale(1)
      left:SetPoint("TOPLEFT", self, "TOPLEFT", 16, -46)
    end
    left:SetShown((mode == "full" and self:PaneShown()) or charView and true or false)
    -- the pages
    right:ClearAllPoints()
    if compact then
      right:SetScale(C.S)
      right:SetPoint("TOPLEFT", self, "TOPLEFT", C.X / C.S, C.PAGE_Y / C.S)
    else
      right:SetScale(1)
      right:SetPoint("TOPLEFT", self, "TOPLEFT", RIGHT_X + paneW, RIGHT_Y)
    end
    right:SetShown(not charView)
    placeCasino(mode)
    -- the tabs: text tabs, or the round buttons
    for i, b in ipairs(self.tabButtons or {}) do if not iconTabs[i] then b:SetShown(not compact) end end
    rtabs:SetShown(compact)
    for i, b in pairs(round) do b:SetSelected(self.tab == i and not charView) end
    strip:SetShown(compact and not charView)

    -- the header
    local narrow = mode == "narrow"
    if P.bagLabel then P.bagLabel:SetShown(not narrow and not compact) end
    P.compBtn:SetShown(not narrow); compIcon:SetShown(narrow)
    pane:ClearAllPoints(); compIcon:ClearAllPoints(); lay:ClearAllPoints(); P.compBtn:ClearAllPoints()
    if P.bagBtn then P.bagBtn:ClearAllPoints() end
    if P.coins then P.coins:ClearAllPoints() end
    -- the round icons by the title: Achievements and Settings; the narrow header's buttons follow
    -- the last one. The cat button always comes first (nearest the character column it folds),
    -- then the layout button.
    local iconRow = (self.tabButtons and self.TAB_SETTINGS and self.tabButtons[self.TAB_SETTINGS]) or P.ver
    if compact then
      -- a second row: [cat][layout][Compendium] on the left, the Treasure Bag on the right
      pane:SetPoint("TOPLEFT", self, "TOPLEFT", 18, -45)
      lay:SetPoint("LEFT", pane, "RIGHT", 6, 0)
      P.compBtn:SetPoint("LEFT", lay, "RIGHT", 8, 0)
      -- the TapCoins move down beside the Treasure Bag, so large numbers don't reach the
      -- Achievements and Settings icons by the title
      if P.bagBtn then P.bagBtn:SetPoint("TOPRIGHT", self, "TOPRIGHT", -20, -42) end
      if P.coins then
        if P.bagBtn then P.coins:SetPoint("RIGHT", P.bagBtn, "LEFT", -8, 0)
        else P.coins:SetPoint("TOPRIGHT", self, "TOPRIGHT", -20, -48) end
      end
    else
      if P.coins then P.coins:SetPoint("TOPRIGHT", self, "TOPRIGHT", -44, -18) end
      if narrow then
        pane:SetPoint("LEFT", iconRow, "RIGHT", 18, 0)
        lay:SetPoint("LEFT", pane, "RIGHT", 6, 0)
        compIcon:SetPoint("LEFT", lay, "RIGHT", 6, 0)
      else
        lay:SetPoint("RIGHT", P.compBtn, "LEFT", -6, 0)
        pane:SetPoint("RIGHT", lay, "LEFT", -6, 0)
      end
      P.compBtn:SetPoint("TOP", self, "TOP", 0, -15)
      if P.bagBtn and P.coins then P.bagBtn:SetPoint("RIGHT", P.coins, "LEFT", -18, 0) end
    end
    -- buttons other parts added (win:AddHeaderButton): in a row after the last header button
    local prev = compact and P.compBtn or narrow and compIcon or nil
    for _, e in ipairs(self.headerExtras) do
      local b = e.frame
      if prev then
        b:ClearAllPoints(); b:SetPoint("LEFT", prev, "RIGHT", 6, 0); prev = b
        e.moved = true
      elseif e.moved or e.placeFull then
        b:ClearAllPoints()
        if e.placeFull then e.placeFull(b)
        else for _, pt in ipairs(e.points or {}) do b:SetPoint(unpack(pt)) end end
        e.moved = nil
      end
    end
    lay.icon:SetTexture(ART .. "win\\" .. (compact and "layout_wide" or "layout_compact"))
    -- the cat button's arrow points the way the column will move (no arrow in compact)
    local open = compact and charView or (not compact and self:PaneShown())
    if open then pane.arrow:SetTexCoord(1, 0, 0, 1) else pane.arrow:SetTexCoord(0, 1, 0, 1) end
    local off = not compact and self:IsCasinoTab()
    pane.icon:SetDesaturated(off); pane.arrow:SetShown(not off)
    if compact then self:RefreshCompact() end
    if left:IsShown() then tryOn:Hide() end
    TCF:FitNewsStrip()
    if self.OnLayout then self:OnLayout(mode) end
  end

  function win:RefreshCompact()
    if not self:IsCompact() then return end
    local db = TCF.db
    if not db then return end
    local cl = TCF.CLASS_BY_KEY and TCF.CLASS_BY_KEY[db.class]
    local cd = TCF:CD()
    local hex = cl and string.format("%02x%02x%02x", floor(cl.color[1] * 255), floor(cl.color[2] * 255), floor(cl.color[3] * 255)) or "ffffff"
    strip.lvl:SetText(string.format("|cff%s%s|r  Level %d  |cffbbbbbb%s|r", hex, cl and cl.name or "", cd.level, TCF:GetTitle()))
    local cs = TCF:CombatStats()
    strip.power:SetText("Power " .. TCF.Commas(cs.power))
    local need = TCF.XPForLevel(cd.level)
    xp:SetMinMaxValues(0, need); xp:SetValue(TCF:IsMaxLevel() and need or cd.xp)
    -- Quests shows how many are ready to hand in, like its text tab
    local q = questsTab and round[questsTab]
    if q then
      local ready = TCF.QuestsReady and TCF:QuestsReady() or 0
      q.label:SetText(ready > 0 and ("Quests |cff20ff20(" .. ready .. ")|r") or "Quests")
    end
  end
  -- keep the bottom line current with the rest of the window
  local baseLight = win.RefreshLight
  if baseLight then
    function win:RefreshLight(...)
      baseLight(self, ...)
      if self:IsCompact() then self:RefreshCompact() end
    end
  end

  -- moving the window by hand: the Casino goes back from where it is now
  if win.HookScript then win:HookScript("OnDragStart", function(f) f.casinoReturn = nil end) end

  function win:OnTabSelected()
    self.compactChar = nil
    if self.layoutMode and self:LayoutMode() ~= self.layoutMode then self:ApplyLayout(true)
    else self:ApplyLayout() end
  end
end

-- The What's new strip (News.lua) is 760 wide, centred on the window: in the narrow and compact
-- windows it takes the window's width instead, and grows taller for its wrapped text.
local NEWS_W, NEWS_H, NEWS_SIDE = 760, 46, 192   -- NEWS_SIDE: the icon, the gaps, Read more and close
function TCF:FitNewsStrip()
  if self.FitNewsPopup then self:FitNewsPopup() end -- the 1.6 What's new pop-up (News.lua): centred, sized for the layout
  local strip, win = self.newsStrip, self.window
  if not strip or not win then return end
  local w = min(NEWS_W, win.layoutW or NEWS_W)
  strip:SetWidth(w)
  if strip.text then
    strip.text:SetWidth(w - NEWS_SIDE - (w < NEWS_W and 0 or 48))
    local th = strip.text.GetStringHeight and strip.text:GetStringHeight()
    if type(th) ~= "number" then
      -- no measurement (outside the game): about 6 pixels a letter, 14 a line
      local len = #(tostring(strip.text:GetText() or ""):gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""))
      th = math.ceil(len * 6 / max(1, w - NEWS_SIDE)) * 14
    end
    strip:SetHeight(max(NEWS_H, th + 20))
  end
  -- News.lua places it above the window when 50 pixels fit there; the strip can now be taller and
  -- the window scaled, so check again with its real height: above, else below, else just inside
  -- the window's top edge
  if strip.IsShown and strip:IsShown() then
    local s = win:GetScale() or 1
    local top, bottom = win.GetTop and win:GetTop(), win.GetBottom and win:GetBottom()
    local ptop = UIParent.GetTop and UIParent:GetTop()
    local sh = strip.GetHeight and strip:GetHeight()
    if type(top) == "number" and type(bottom) == "number" and type(ptop) == "number" and type(sh) == "number" then
      local need = (sh + 4) * s
      strip:ClearAllPoints()
      if top * s + need <= ptop then strip:SetPoint("BOTTOM", win, "TOP", 0, 2)
      elseif bottom * s - need >= 0 then strip:SetPoint("TOP", win, "BOTTOM", 0, -2)
      else
        strip:SetPoint("TOP", win, "TOP", 0, -44)
        if strip.SetFrameLevel and win.GetFrameLevel then pcall(strip.SetFrameLevel, strip, (win:GetFrameLevel() or 1) + 80) end
      end
    end
  end
end

function TCF.UI.SetupWindowLayout(win)
  local P = win.parts or {}
  win.layoutW, win.layoutH = P.W or 920, P.H or 620
  SetupSize(win)
  if P.left and P.right and P.compBtn then SetupLayout(win) end
  -- News.lua loads after this file: wrap its CheckNews once, when the first window is built
  if TCF.CheckNews and not TCF.newsFitHooked then
    TCF.newsFitHooked = true
    local check = TCF.CheckNews
    TCF.CheckNews = function(self, ...)
      check(self, ...)
      self:FitNewsStrip()
    end
  end
  function win:OnWindowScale()
    if self.windowSizeControl then self.windowSizeControl.Sync() end
  end
  if win.ApplyLayout then win:ApplyLayout() end
end
