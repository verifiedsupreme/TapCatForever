# 1.6.0 window track: the main window's size grip (drag to scale, double-click to reset, top-left
# stays put) and the Window size - / + buttons in Settings
# a big screen (1600 x 1000 UI units) unless a check says otherwise; the mock's UIParent is 140 x 140
SCREEN = r'''
  function UIParent:GetWidth() return _sw or 1600 end
  function UIParent:GetHeight() return _sh or 1000 end
'''

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(SCREEN + r'''
      local T = TapCatForever
      T.db.ui.winScale = 1.25
      local scaledAt
      local realCreate = CreateFrame
      CreateFrame = function(kind, name, ...)
        local f = realCreate(kind, name, ...)
        if name == "TapCatForeverWindow" then f.SetScale = function(self, v) scaledAt = v end end
        return f
      end
      T:CreateWindow()
      CreateFrame = realCreate
      local win = T.window
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      ck(scaledAt == 1.25 and win:GetWindowScale() == 1.25, "the saved size is used when the window is built: " .. tostring(scaledAt))
      -- a little layout model: left/top in the window's own units, scale
      win._l, win._t, win._s = 100, 900, 1
      function win:GetLeft() return self._l end
      function win:GetTop() return self._t end
      function win:GetScale() return self._s end
      function win:SetScale(v) self._s = v end
      function win:SetPoint(p, rel, rp, x, y) if p == "TOPLEFT" then self._l, self._t = x, y end end
      local function cornerKept() return math.abs(win._l * win._s - 100) < 1e-6 and math.abs(win._t * win._s - 900) < 1e-6 end
      local g = win.sizeGrip
      ck(g ~= nil, "the window has a size grip")
      win:SetWindowScale(1.25)
      ck(math.abs(win._s - 1.25) < 1e-6 and T.db.ui.winScale == 1.25, "scale set and saved")
      ck(cornerKept(), "the top-left corner stays on screen where it was")
      win:SetWindowScale(5); ck(win._s == T.WIN_SCALE_MAX, "bigger than the largest size is clamped")
      win:SetWindowScale(0.1); ck(win._s == T.WIN_SCALE_MIN, "smaller than the smallest size is clamped")
      win:SetWindowScale(0 / 0); ck(win._s == 1, "a bad number is normal size")
      ck(cornerKept(), "the corner stayed through every change")
      -- dragging: grab the grip at its corner, move the cursor right/down: it gets bigger
      local cx, cy = 100 + 920, 900 - 620
      GetCursorPosition = function() return cx, cy end
      win:SetWindowScale(1)
      g.scripts.OnMouseDown(g, "LeftButton")
      cx, cy = 100 + 920 * 1.2, 900 - 620 * 1.2
      g.scripts.OnUpdate(g, 0.02)
      ck(math.abs(win._s - 1.2) < 0.011, "dragging the grip scales the window: " .. tostring(win._s))
      ck(cornerKept(), "dragging keeps the top-left corner")
      cx, cy = 100 + 920 * 0.3, 900 - 620 * 0.3
      g.scripts.OnUpdate(g, 0.02)
      ck(win._s == T.WIN_SCALE_MIN, "dragging past the smallest size stops there: " .. tostring(win._s))
      g.scripts.OnMouseUp(g)
      ck(g.scripts.OnUpdate == nil, "letting go stops resizing")
      -- a plain click on the grip (the cursor rests on its middle, inside the corner) changes nothing
      win:SetWindowScale(1)
      for _, start in ipairs({ 1, 1.2, 0.8 }) do
        win:SetWindowScale(start)
        local mid = 9 * start   -- the grip's middle: 9 window units in from the corner
        cx, cy = 100 + 920 * start - 5 * start - mid, 900 - 620 * start + 5 * start + mid
        for _ = 1, 5 do
          g.scripts.OnMouseDown(g, "LeftButton")
          for _ = 1, 4 do g.scripts.OnUpdate(g, 0.02) end
          cx = cx + 1; g.scripts.OnUpdate(g, 0.02); cx = cx - 1   -- a 1 pixel shake
          g.scripts.OnMouseUp(g)
        end
        ck(math.abs(win._s - start) < 1e-6, "clicking the grip keeps the size " .. start .. ": " .. tostring(win._s))
        ck(cornerKept(), "and the corner")
      end
      ck(math.abs(win._s - 0.8) < 1e-6 and T.db.ui.winScale == 0.8, "the size from before the clicks is the saved one")
      -- the drag follows the cursor from where it grabbed, wherever that was on the grip
      win:SetWindowScale(1)
      cx, cy = 100 + 920 - 14, 900 - 620 + 14
      g.scripts.OnMouseDown(g, "LeftButton")
      cx, cy = cx + 920 * 0.1, cy - 620 * 0.1
      g.scripts.OnUpdate(g, 0.02); g.scripts.OnMouseUp(g)
      ck(math.abs(win._s - 1.1) < 0.006, "moving 10% of the size makes it 10% bigger: " .. tostring(win._s))
      g.scripts.OnMouseDown(g, "RightButton")
      ck(g.scripts.OnUpdate == nil, "the right button does nothing")
      g.scripts.OnDoubleClick(g)
      ck(win._s == 1 and T.db.ui.winScale == nil, "double-click goes back to normal size: " .. tostring(win._s) .. " " .. tostring(T.db.ui.winScale))
      -- Settings: Window size - and +
      win:SelectTab(win.TAB_SETTINGS)
      local byLabel = {}
      for _, a in ipairs(win.settingsLayout) do byLabel[a.label] = a end
      local minus, plus, label = byLabel["Window smaller"], byLabel["Window bigger"], byLabel["Window size"]
      ck(minus and plus and label, "Settings has the Window size buttons")
      if minus and plus and label then
        ck(label.frame:GetText() == "Window size: 100%", "Window size label: " .. tostring(label.frame:GetText()))
        plus.frame.scripts.OnClick(plus.frame)
        ck(math.abs(win._s - 1.05) < 1e-6 and T.db.ui.winScale == 1.05, "+ makes it 5% bigger: " .. tostring(win._s))
        ck(label.frame:GetText() == "Window size: 105%", "the label follows: " .. tostring(label.frame:GetText()))
        minus.frame.scripts.OnClick(minus.frame); minus.frame.scripts.OnClick(minus.frame)
        ck(math.abs(win._s - 0.95) < 1e-6, "- makes it smaller: " .. tostring(win._s))
        for _ = 1, 30 do plus.frame.scripts.OnClick(plus.frame) end
        ck(win._s == T.WIN_SCALE_MAX, "+ stops at the largest size")
        for _ = 1, 30 do minus.frame.scripts.OnClick(minus.frame) end
        ck(win._s == T.WIN_SCALE_MIN and label.frame:GetText() == "Window size: 60%", "- stops at the smallest size")
        g.scripts.OnDoubleClick(g)
        ck(label.frame:GetText() == "Window size: 100%", "double-click shows 100% again")
        ck(cornerKept(), "the corner stayed put through the Settings buttons")
      end
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("window size: " + r)
    # a default screen (768 tall at UI scale 1): the largest size still fits on it
    lua = load_addon()
    r = lua.execute(SCREEN + r'''
      _sw, _sh = 1366, 768
      local T = TapCatForever
      T.db.ui.winScale = 1.4    -- saved on a bigger screen
      T:CreateWindow()
      local win = T.window
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      win._l, win._t, win._s = 40, 740, 1
      function win:GetLeft() return self._l end
      function win:GetTop() return self._t end
      function win:GetScale() return self._s end
      function win:SetScale(v) self._s = v end
      function win:SetPoint(p, rel, rp, x, y) if p == "TOPLEFT" then self._l, self._t = x, y end end
      local fit = math.floor((768 - 16) / 620 * 100) / 100
      ck(math.abs(win:GetWindowScale() - fit) < 1e-6, "a saved size too big for this screen is shown smaller: " .. win:GetWindowScale())
      win:SetWindowScale(1.4)
      ck(math.abs(win._s - fit) < 1e-6 and 620 * win._s <= 768 - 16, "1.4 is cut to what fits: " .. win._s)
      win:SetWindowScale(1)
      -- dragging far past the screen's bottom-right corner: the window stops at the screen's edge
      local g = win.sizeGrip
      local cx, cy = 40 + 920, 740 - 620
      GetCursorPosition = function() return cx, cy end
      g.scripts.OnMouseDown(g, "LeftButton")
      cx, cy = 1366, 0
      for _ = 1, 3 do g.scripts.OnUpdate(g, 0.02) end
      g.scripts.OnMouseUp(g)
      ck(win._s > 1.1 and 740 - 620 * win._s >= -1e-6 and 40 + 920 * win._s <= 1366 + 1e-6, "the dragged window stays on the screen: " .. win._s)
      ck(math.abs(win._l * win._s - 40) < 1e-6 and math.abs(win._t * win._s - 740) < 1e-6, "with its corner where it was")
      -- a tiny screen never makes normal size impossible
      _sw, _sh = 800, 600
      win:SetWindowScale(1)
      ck(win._s == 1, "normal size is always allowed: " .. win._s)
      win:SetWindowScale(1.3)
      ck(win._s == 1, "but no bigger when it doesn't fit: " .. win._s)
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("window size (screen): " + r)
    print("window size section (grip, clamp, saved, top-left kept, a click changes nothing, fits the screen, double-click reset, Settings - and +): all checks passed")
