# 1.6.0 window track: the character pane folds away (button left of the Compendium), the window
# gets narrower, every page still lays out, the Casino stays full width, the state is remembered
RECORDER = r'''
  -- frames remember their size, points and scale (the mock forgets them)
  _realCreateFrame = _realCreateFrame or CreateFrame
  CreateFrame = function(kind, name, ...)
    local f = _realCreateFrame(kind, name, ...)
    f.SetSize = function(s, w, h) s._w, s._h = w, h end
    f.SetWidth = function(s, w) s._w = w end
    f.SetHeight = function(s, h) s._h = h end
    f.ClearAllPoints = function(s) s._pts = {} end
    f.SetPoint = function(s, p, rel, rp, x, y)
      s._pts = s._pts or {}
      if type(rel) == "number" then rel, rp, x, y = nil, p, rel, rp end
      s._pts[#s._pts + 1] = { p, rel, rp or p, x or 0, y or 0 }
    end
    f.SetScale = function(s, v) s._s = v end
    f.GetScale = function(s) return s._s or 1 end
    if name == "TapCatForeverWindow" then
      -- on screen: its TOPLEFT point against UIParent's BOTTOMLEFT, or 100, 900 until placed
      f.GetLeft = function(s) for _, p in ipairs(s._pts or {}) do if p[1] == "TOPLEFT" then return p[4] end end return 100 / (s._s or 1) end
      f.GetTop = function(s) for _, p in ipairs(s._pts or {}) do if p[1] == "TOPLEFT" then return p[5] end end return 900 / (s._s or 1) end
    end
    return f
  end
  -- a 1600 x 1000 screen (the mock's UIParent is 140 x 140)
  function UIParent:GetWidth() return _sw or 1600 end
  function UIParent:GetHeight() return _sh or 1000 end
  function _pt(f, which) for _, p in ipairs(f._pts or {}) do if p[1] == which then return p end end end
'''

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(RECORDER + r'''
      local T = TapCatForever
      T:CreateWindow()
      local win = T.window
      local P = win.parts
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      local function sx() return win:GetLeft() * win:GetScale() end   -- top-left on screen
      local function rightX() return sx() + _pt(P.right, "TOPLEFT")[4] * win:GetScale() end
      win:Show()
      ck(win._w == 920 and win._h == 620, "full width to start: " .. tostring(win._w))
      ck(P.left:IsShown() and P.compBtn:IsShown() and not win.compIcon:IsShown() and P.bagLabel:IsShown(), "the pane, Compendium button and bag label show")
      local rp = _pt(P.right, "TOPLEFT")
      ck(rp and rp[2] == win and rp[4] == 344 and rp[5] == -106, "the right column sits right of the pane")
      local pb = win.paneButton
      ck(pb and _pt(pb, "RIGHT") and _pt(pb, "RIGHT")[2] == P.compBtn, "the pane button sits left of the Compendium button")
      win:SelectTab(win.TAB_GEAR)
      local x0 = sx()
      -- fold it away
      pb.scripts.OnClick(pb)
      ck(T.db.ui.winPaneHidden == true and win.layoutMode == "narrow", "the pane folds away and it is saved")
      ck(win._w == 920 - T.WIN_PANE_W and win._w == 592 and win._h == 620, "the window gets narrower: " .. tostring(win._w))
      ck(not P.left:IsShown(), "the pane is hidden")
      rp = _pt(P.right, "TOPLEFT")
      ck(rp[4] == 16 and rp[5] == -106, "the right column slides left")
      ck(math.abs(sx() - x0) < 1e-6, "the top-left corner stays put")
      ck(not P.compBtn:IsShown() and win.compIcon:IsShown() and not P.bagLabel:IsShown(), "the narrow header: Compendium icon, no bag label")
      ck(_pt(win.compIcon, "LEFT")[2] == pb, "the Compendium icon is right of the pane button")
      ck(win.compIcon.scripts.OnClick ~= nil, "the Compendium icon works")
      win.compIcon.scripts.OnClick(win.compIcon); ck(T.compendium and T.compendium:IsShown(), "the Compendium icon opens it")
      win.compIcon.scripts.OnClick(win.compIcon); ck(not T.compendium:IsShown(), "and closes it")
      ck(win.layoutW == 592, "the size grip measures the narrow window")
      -- every tab lays out in the narrow window; the Casino goes full width, growing to the left
      local rx = rightX()
      for i = 1, #win.tabButtons do
        win:SelectTab(i)
        if i == win.TAB_CASINO then
          ck(win._w == 920 and win.layoutMode == "full", "the Casino is full width")
          ck(math.abs(rightX() - rx) < 1e-6, "the window grows to the left: the tabs stay put")
          ck(not P.left:IsShown(), "the folded pane stays folded under the Casino")
          ck(T.casinoView:IsShown(), "the Casino shows")
          pb.scripts.OnClick(pb)
          ck(T.db.ui.winPaneHidden == true and win._w == 920, "the pane button does nothing on the Casino tab")
        else
          ck(win._w == 592 and win.layoutMode == "narrow", "tab " .. i .. " is narrow: " .. tostring(win._w))
          ck(math.abs(rightX() - rx) < 1e-6, "tab " .. i .. ": the tabs stay put")
        end
        ck(win.tabButtons[i]:IsShown(), "tab button " .. i .. " shows")
      end
      win:SelectTab(win.TAB_GEAR)
      ck(math.abs(sx() - x0) < 1e-6, "back from the Casino, the window is where it was: " .. sx() .. " " .. x0)
      -- the size grip still works in the narrow window
      local g = win.sizeGrip
      local gx, gy = x0 + 592, 900 - 620
      GetCursorPosition = function() return gx, gy end
      g.scripts.OnMouseDown(g, "LeftButton")
      gx, gy = x0 + 592 * 1.2, 900 - 620 * 1.2
      g.scripts.OnUpdate(g, 0.02); g.scripts.OnMouseUp(g)
      ck(math.abs(win:GetScale() - 1.2) < 0.011, "the grip scales the narrow window: " .. win:GetScale())
      ck(math.abs(sx() - x0) < 1e-6, "and keeps its corner")
      -- open it again
      pb.scripts.OnClick(pb)
      ck(T.db.ui.winPaneHidden == nil and win._w == 920 and P.left:IsShown() and P.compBtn:IsShown(), "the pane opens again")
      ck(_pt(P.right, "TOPLEFT")[4] == 344, "the right column moves back")
      ck(math.abs(sx() - x0) < 1e-6, "the corner stays put opening it")
      -- tooltips say what it does
      for _, want in ipairs({ "Fold away", "Show the gear" }) do
        local lines = {}
        GameTooltip.AddLine = function(_, t) lines[#lines + 1] = t end
        pb.scripts.OnEnter(pb)
        local all = table.concat(lines, " ")
        ck(all:find(want, 1, true) and not all:find("!", 1, true), "pane tooltip: " .. all)
        pb.scripts.OnClick(pb)
      end
      -- near the screen's left edge: the full-width Casino is pushed back on the screen, and
      -- leaving it puts the narrow window back where it was (it used to creep right)
      pb.scripts.OnClick(pb)
      win:SetWindowScale(1)
      local set = win.SetPoint
      win.SetPoint = function(f, p, rel, rp, x, y)   -- clamped to the screen
        if p == "TOPLEFT" and type(x) == "number" and x < 0 then x = 0 end
        return set(f, p, rel, rp, x, y)
      end
      win:PlaceTopLeft(60, 900)
      win:SelectTab(win.TAB_GEAR)
      for _ = 1, 3 do
        win:SelectTab(win.TAB_CASINO)
        ck(win._w == 920 and sx() >= 0, "the Casino on the screen: " .. sx())
        win:SelectTab(win.TAB_GEAR)
        ck(math.abs(sx() - 60) < 1e-6, "back from the Casino near the edge, where it was: " .. sx())
      end
      -- moved by hand on the Casino tab: it goes back from the new place
      win:SelectTab(win.TAB_CASINO)
      win.scripts.OnDragStart(win)
      win:PlaceTopLeft(200, 900)
      win:SelectTab(win.TAB_GEAR)
      ck(math.abs(sx() - (200 + T.WIN_PANE_W)) < 1e-6, "moved on the Casino tab: the tabs stay where they are: " .. sx())
      win.SetPoint = set
      -- try-on: with the column folded away, hovering an item shows it on a small cat beside the window
      local stage = win.tryOnStage
      local look = T:GetAppearance()
      ck(stage and not stage:IsShown(), "no try-on cat to start")
      local some
      for _, it in ipairs(T.ITEM_LIST) do if it.slot == "hat" or it.slot == "head" then some = it; break end end
      some = some or T.ITEM_LIST[1]
      win.preview:ApplyAppearance(T:GetAppearance(nil, some))
      ck(stage:IsShown() and stage.cat and stage.cat.look ~= nil, "hovering an item shows the try-on cat: " .. tostring(some.key))
      local sp = _pt(stage, "TOPRIGHT") or _pt(stage, "TOPLEFT")
      ck(sp and sp[2] == win, "beside the window")
      win.preview:ApplyAppearance(T:GetAppearance())
      ck(not stage:IsShown(), "leaving the item hides it")
      pb.scripts.OnClick(pb)
      win.preview:ApplyAppearance(T:GetAppearance(nil, some))
      ck(not stage:IsShown(), "with the column open, the column's own cat tries it on")
      win.preview:ApplyAppearance(T:GetAppearance())
      -- buttons other parts add to the header find a place in the narrow header
      local extra = CreateFrame("Button", nil, win)
      win:AddHeaderButton(extra, function(b) b:SetPoint("RIGHT", win.layoutButton, "LEFT", -6, 0) end)
      ck(_pt(extra, "RIGHT") and _pt(extra, "RIGHT")[2] == win.layoutButton, "an added button keeps its place in the full header")
      pb.scripts.OnClick(pb)
      ck(_pt(extra, "LEFT") and _pt(extra, "LEFT")[2] == win.compIcon, "and goes after the Compendium icon in the narrow header")
      pb.scripts.OnClick(pb)
      ck(_pt(extra, "RIGHT") and not _pt(extra, "LEFT"), "and back in the full header")
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("character pane: " + r)
    # remembered: a window built with the pane folded starts narrow
    lua = load_addon()
    r = lua.execute(RECORDER + r'''
      local T = TapCatForever
      T.db.ui.winPaneHidden = true
      T:ToggleWindow()
      local win = T.window
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      ck(win:IsShown() and win._w == 592 and not win.parts.left:IsShown(), "a folded pane is remembered")
      ck(win.tabNames[win.tab] == "Adventure" and _pt(win.parts.right, "TOPLEFT")[4] == 16, "the Adventure page in the narrow window: " .. tostring(win.tab) .. " " .. tostring(_pt(win.parts.right, "TOPLEFT") and _pt(win.parts.right, "TOPLEFT")[4]))
      T:ToggleWindow(); T:ToggleWindow()
      ck(win._w == 592, "still narrow after closing and opening")
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("character pane (remembered): " + r)
    print("character pane section (fold away and back, narrower window, corner kept, every tab, Casino full width, grip, remembered): all checks passed")
