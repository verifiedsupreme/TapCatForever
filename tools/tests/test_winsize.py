# 1.6.0 window track: the main window's size grip (drag to scale, double-click to reset, top-left
# stays put) and the Window size - / + buttons in Settings
def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
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
      win._l, win._t, win._s = 100, 700, 1
      function win:GetLeft() return self._l end
      function win:GetTop() return self._t end
      function win:GetScale() return self._s end
      function win:SetScale(v) self._s = v end
      function win:SetPoint(p, rel, rp, x, y) if p == "TOPLEFT" then self._l, self._t = x, y end end
      local function cornerKept() return math.abs(win._l * win._s - 100) < 1e-6 and math.abs(win._t * win._s - 700) < 1e-6 end
      local g = win.sizeGrip
      ck(g ~= nil, "the window has a size grip")
      win:SetWindowScale(1.25)
      ck(math.abs(win._s - 1.25) < 1e-6 and T.db.ui.winScale == 1.25, "scale set and saved")
      ck(cornerKept(), "the top-left corner stays on screen where it was")
      win:SetWindowScale(5); ck(win._s == T.WIN_SCALE_MAX, "bigger than the largest size is clamped")
      win:SetWindowScale(0.1); ck(win._s == T.WIN_SCALE_MIN, "smaller than the smallest size is clamped")
      win:SetWindowScale(0 / 0); ck(win._s == 1, "a bad number is normal size")
      ck(cornerKept(), "the corner stayed through every change")
      -- dragging: cursor far right/down makes it bigger
      local cx, cy = 100 + 920 * 1.2, 700 - 620 * 1.2
      GetCursorPosition = function() return cx, cy end
      win:SetWindowScale(1)
      g.scripts.OnMouseDown(g, "LeftButton")
      g.scripts.OnUpdate(g, 0.02)
      ck(math.abs(win._s - 1.2) < 0.011, "dragging the grip scales the window: " .. tostring(win._s))
      ck(cornerKept(), "dragging keeps the top-left corner")
      cx, cy = 100 + 920 * 0.3, 700 - 620 * 0.3
      g.scripts.OnUpdate(g, 0.02)
      ck(win._s == T.WIN_SCALE_MIN, "dragging past the smallest size stops there: " .. tostring(win._s))
      g.scripts.OnMouseUp(g)
      ck(g.scripts.OnUpdate == nil, "letting go stops resizing")
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
    print("window size section (grip, clamp, saved, top-left kept, double-click reset, Settings - and +): all checks passed")
