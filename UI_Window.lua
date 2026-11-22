-- TapCatForever: the main window's size (the grip in its bottom-right corner).
-- UI.lua's CreateWindow hands over its parts in win.parts and calls TCF.UI.SetupWindowLayout(win).
local ADDON, TCF = ...
local floor, min, max = math.floor, math.min, math.max

TCF.UI = TCF.UI or {}
TCF.WIN_SCALE_MIN, TCF.WIN_SCALE_MAX, TCF.WIN_SCALE_STEP = 0.6, 1.4, 0.05

local function clampScale(v)
  v = tonumber(v) or 1
  if v ~= v then v = 1 end
  return max(TCF.WIN_SCALE_MIN, min(TCF.WIN_SCALE_MAX, v))
end
TCF.ClampWindowScale = clampScale

local function uiDB() return TCF.db and TCF.db.ui end

---------------------------------------------------------------- window size
-- Dragging the grip scales the whole window (every page keeps its layout); the top-left corner
-- stays where it is on the screen. Double-click the grip to go back to normal size.
-- Remembered in db.ui.winScale (nil = 1).
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
    v = clampScale(v)
    local x, y = self:ScreenTopLeft()
    self:SetScale(v)
    if x then placeTopLeft(self, x, y) end
    local ui = uiDB()
    if ui then
      if math.abs(v - 1) < 0.001 then ui.winScale = nil else ui.winScale = v end   -- nil: normal size
    end
    if self.OnWindowScale then self:OnWindowScale(v) end
  end
  function win:GetWindowScale() return clampScale(uiDB() and uiDB().winScale or 1) end
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
    g.L, g.T, g.dragging = x, y, true
    g:SetScript("OnUpdate", function()
      local cx, cy = cursor()
      local w, h = win.layoutW or 920, win.layoutH or 620
      local v = ((cx - g.L) / w + (g.T - cy) / h) / 2
      v = floor(clampScale(v) * 100 + 0.5) / 100
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

function TCF.UI.SetupWindowLayout(win)
  local P = win.parts or {}
  win.layoutW, win.layoutH = P.W or 920, P.H or 620
  SetupSize(win)
  function win:OnWindowScale()
    if self.windowSizeControl then self.windowSizeControl.Sync() end
  end
end
