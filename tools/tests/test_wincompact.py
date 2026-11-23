# 1.6.0 window track: the compact layout (narrow and tall, round tab buttons, pages scaled to fit,
# the character pane as its own view, the Casino scaled to the width), remembered
import os, importlib.util
_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("test_winpane", os.path.join(_here, "test_winpane.py"))
_pane = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_pane)
RECORDER = _pane.RECORDER

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(RECORDER + r'''
      local T = TapCatForever
      T:CreateWindow()
      local win = T.window
      local P = win.parts
      local C = T.WIN_COMPACT
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      local function near(a, b) return type(a) == "number" and type(b) == "number" and math.abs(a - b) < 1e-6 end
      local function sx() return win:GetLeft() * win:GetScale() end
      win:Show()
      win:SelectTab(win.TAB_GEAR)
      local x0 = sx()
      local lay = win.layoutButton
      -- the TapCoins text is a font string: record its points too
      P.coins.ClearAllPoints = function(f) f._pts = {} end
      P.coins.SetPoint = function(f, p, rel, rp, x, y)
        f._pts = f._pts or {}
        if type(rel) == "number" then rel, rp, x, y = nil, p, rel, rp end
        f._pts[#f._pts + 1] = { p, rel, rp or p, x or 0, y or 0 }
      end
      ck(lay and _pt(lay, "RIGHT") and _pt(lay, "RIGHT")[2] == P.compBtn and _pt(win.paneButton, "RIGHT")[2] == lay, "the cat button, then the layout button, then the Compendium")
      ck(lay.icon.tex and lay.icon.tex:find("layout_compact", 1, true), "it shows the phone icon")
      lay.scripts.OnClick(lay)
      ck(T.db.ui.winCompact == true and win.layoutMode == "compact", "compact on, and saved")
      ck(win._w == 420 and win._h == C.H and C.H >= 590 and C.H <= 630, "compact is narrow and tall: " .. tostring(win._w) .. "x" .. tostring(win._h))
      ck(near(sx(), x0), "the top-left corner stays put")
      ck(lay.icon.tex:find("layout_wide", 1, true), "the layout button now offers the full window")
      -- the tabs: round buttons, two rows of five, in the window
      local n = 0
      for i, b in pairs(win.roundTabs) do
        n = n + 1
        ck(b.label and b.label:GetText() and b.label:GetText():find(win.tabNames[i], 1, true), "round tab label: " .. tostring(b.label and b.label:GetText()))
        ck(b.icon.tex and b.ring.tex and b.ring.tex:find("win\\tab_ring", 1, true), "round tab art: " .. win.tabNames[i])
        local p = _pt(b, "TOP")
        ck(p and p[4] - b._w / 2 >= 0 and p[4] + b._w / 2 <= C.CW, "round tab " .. win.tabNames[i] .. " inside the width")
      end
      ck(n == 10, "ten round tabs: " .. n)
      for i, b in ipairs(win.tabButtons) do
        if i == win.TAB_ACH or i == win.TAB_SETTINGS then ck(b:IsShown(), "the Achievements and Settings icons stay in the header")
        else ck(not b:IsShown(), "text tab " .. i .. " hidden") end
      end
      ck(_pt(win.roundTabs[win.TAB_GEAR], "TOP")[5] == 0, "first row on top")
      ck(win.roundTabs[win.TAB_CASINO] and not win.roundTabs[win.TAB_ACH] and not win.roundTabs[win.TAB_SETTINGS], "the Casino is a round tab, Achievements and Settings are not")
      do
        local cp, lp = _pt(win.roundTabs[win.TAB_CASINO], "TOP"), _pt(win.roundTabs[win.TAB_LEADERBOARD], "TOP")
        ck(cp[5] == lp[5] and cp[4] < lp[4] and lp[4] > C.CW * 0.8, "the Casino sits where Achievements was, before the Leaderboard")
      end
      -- the pages: scaled to the width, between the tabs and the bottom line
      local s = P.right:GetScale()
      local rp = _pt(P.right, "TOPLEFT")
      ck(near(s, 388 / 560) and near(rp[4] * s, 16) and near(rp[5] * s, C.PAGE_Y), "the pages are scaled to fit: " .. s)
      ck(near(rp[4] * s + 560 * s, 404), "the pages end 16 from the right edge")
      local stripTop = -_pt(win.compactStrip, "TOPLEFT")[5]
      ck(-C.PAGE_Y + 494 * s <= stripTop and stripTop + win.compactStrip._h <= C.H - 12, "the pages end above the bottom line, and it inside the window")
      ck(-C.TAB_Y + C.TAB_ROW * 2 <= -C.PAGE_Y + 2, "the tabs end above the pages")
      ck(not P.left:IsShown() and win.compactStrip:IsShown(), "no character column, the bottom line shows")
      ck(win.compactStrip.lvl:GetText():find("Level", 1, true) and win.compactStrip.power:GetText():find("Power", 1, true), "the bottom line: " .. tostring(win.compactStrip.lvl:GetText()))
      -- the header: second row
      ck(_pt(win.paneButton, "TOPLEFT") and _pt(lay, "LEFT")[2] == win.paneButton and _pt(P.compBtn, "LEFT")[2] == lay, "second header row: cat, layout, Compendium")
      -- (the TapCoins take the bag label's place, so big numbers don't reach the icons by the title)
      ck(P.compBtn:IsShown() and not win.compIcon:IsShown() and not P.bagLabel:IsShown() and _pt(P.bagBtn, "TOPRIGHT"), "the Compendium button and the Treasure Bag on the second row")
      ck(_pt(P.coins, "RIGHT") and _pt(P.coins, "RIGHT")[2] == P.bagBtn and not _pt(P.coins, "TOPRIGHT"), "the TapCoins sit left of the Treasure Bag")
      ck(not win.roundTabs[8 - 0] or not (win.roundTabs[8].icon.tex or ""):find("Bag", 1, true), "the Shop's round tab is not a second bag icon: " .. tostring(win.roundTabs[8] and win.roundTabs[8].icon.tex))
      -- every round tab selects its page
      for i, b in pairs(win.roundTabs) do
        b.scripts.OnClick(b)
        ck(win.tab == i and win.layoutMode == "compact", "round tab " .. win.tabNames[i] .. " opens its page")
        for j, o in pairs(win.roundTabs) do ck(o.selected == (j == i), "only the open tab glows") end
        local lines = {}
        local add = GameTooltip.AddLine
        GameTooltip.AddLine = function(_, t) lines[#lines + 1] = t end
        b.scripts.OnEnter(b)
        GameTooltip.AddLine = add
        ck(lines[1] == win.tabNames[i] and #lines == 2 and not table.concat(lines):find("!", 1, true), "round tab tooltip: " .. table.concat(lines, " / "))
        ck(b.glow:IsShown(), "hover glow"); b.scripts.OnLeave(b)
      end
      -- Settings and the Casino icons still work in compact
      win:SelectTab(win.TAB_SETTINGS)
      ck(win.layoutMode == "compact" and P.right:IsShown(), "Settings in compact")
      win:SelectTab(win.TAB_CASINO)
      local cv = T.casinoView
      local k = 388 / 888
      ck(win.layoutMode == "compact" and win._w == 420, "the Casino stays compact")
      ck(near(cv:GetScale() * s, k), "the Casino is scaled to the width: " .. cv:GetScale() * s)
      local cp, sp = _pt(cv, "TOPLEFT"), _pt(cv.sign, "TOPLEFT")
      ck(cp[2] == win and near(cp[4] * k, 16) and near(sp[4] * k, 16), "the Casino starts at the left edge")
      local top, bottom = -sp[5] * k, -cp[5] * k + 494 * k
      ck(top >= -C.PAGE_Y - 1e-6 and bottom <= -C.PAGE_Y + 494 * s + 1e-6 and near(-cp[5] * k - top, 60 * k), "the Casino fits the page area: " .. top .. " " .. bottom)
      -- the character view
      local pb = win.paneButton
      win:SelectTab(win.TAB_GEAR)
      pb.scripts.OnClick(pb)
      ck(win.compactChar and P.left:IsShown() and not P.right:IsShown() and not win.compactStrip:IsShown(), "the cat button shows the character view")
      local lp = _pt(P.left, "TOPLEFT")
      ck(near(P.left:GetScale(), s) and lp[4] * s >= 16 and lp[4] * s + 316 * s <= 404 and near(lp[5] * s, C.PAGE_Y) and -C.PAGE_Y + 554 * s <= C.H - 8,
        "the character view fits under the tabs")
      for _, b in pairs(win.roundTabs) do ck(not b.selected, "no tab glows in the character view") end
      pb.scripts.OnClick(pb)
      ck(not win.compactChar and not P.left:IsShown() and P.right:IsShown() and win.tab == win.TAB_GEAR, "the cat button goes back to the page")
      win.compactStrip.scripts.OnClick(win.compactStrip)
      ck(win.compactChar and P.left:IsShown(), "the bottom line opens the character view")
      win.roundTabs[win.TAB_GEAR].scripts.OnClick(win.roundTabs[win.TAB_GEAR])
      ck(not win.compactChar and P.right:IsShown(), "a tab closes the character view")
      -- the grip measures the compact window
      ck(win.layoutW == 420 and win.layoutH == C.H, "the grip uses the compact size")
      local gx, gy = x0 + 420, 900 - C.H
      GetCursorPosition = function() return gx, gy end
      local g = win.sizeGrip
      g.scripts.OnMouseDown(g, "LeftButton")
      gx, gy = x0 + 420 * 1.3, 900 - C.H * 1.3
      g.scripts.OnUpdate(g, 0.02); g.scripts.OnMouseUp(g)
      ck(math.abs(win:GetScale() - 1.3) < 0.011 and near(sx(), x0), "the grip scales the compact window: " .. win:GetScale())
      ck(T.db.ui.winScaleCompact == win:GetScale() and T.db.ui.winScale == nil, "the compact size is saved apart: " .. tostring(T.db.ui.winScaleCompact) .. " " .. tostring(T.db.ui.winScale))
      -- the quest count on the round Quests tab
      local qi
      for i, nme in ipairs(win.tabNames) do if nme == "Quests" then qi = i end end
      local realReady = T.QuestsReady
      T.QuestsReady = function() return 2 end
      win:RefreshLight()
      ck(win.roundTabs[qi].label:GetText():find("(2)", 1, true), "the round Quests tab counts ready quests: " .. tostring(win.roundTabs[qi].label:GetText()))
      T.QuestsReady = realReady
      win:RefreshLight()
      -- back to the full window
      lay.scripts.OnClick(lay)
      ck(T.db.ui.winCompact == nil and win.layoutMode == "full" and win._w == 920 and win._h == 620, "back to the full window")
      ck(near(win:GetScale(), 1) and near(sx(), x0), "at its own size (normal), corner kept: " .. win:GetScale())
      ck(_pt(P.coins, "TOPRIGHT") and not _pt(P.coins, "RIGHT") and P.bagLabel:IsShown(), "the TapCoins are back in the top row, with the bag label")
      win:SetWindowScale(1.1)
      ck(T.db.ui.winScale == 1.1 and math.abs(T.db.ui.winScaleCompact - 1.3) < 0.011, "the full window's size is its own")
      lay.scripts.OnClick(lay)
      ck(math.abs(win:GetScale() - 1.3) < 0.011 and near(sx(), x0), "compact again: its own size back: " .. win:GetScale())
      lay.scripts.OnClick(lay)
      ck(near(win:GetScale(), 1.1), "full again: 1.1")
      win:SetWindowScale(1)
      ck(near(P.right:GetScale(), 1) and _pt(P.right, "TOPLEFT")[4] == 344 and P.left:IsShown() and near(P.left:GetScale(), 1), "the pages and pane are back")
      ck(not win.compactStrip:IsShown(), "no bottom line")
      for i, b in ipairs(win.tabButtons) do ck(b:IsShown(), "text tab " .. i .. " back") end
      ck(_pt(P.compBtn, "TOP") and _pt(P.compBtn, "TOP")[4] == 0, "the Compendium button is back in the middle")
      win:SelectTab(win.TAB_CASINO)
      ck(near(cv:GetScale(), 1) and _pt(cv, "TOPLEFT")[4] == 16 and _pt(cv, "TOPLEFT")[5] == -106 and _pt(cv.sign, "TOPLEFT")[5] == -46, "the Casino is full size again")
      win:SelectTab(win.TAB_GEAR)
      -- compact, then back with the pane folded: the narrow window
      pb.scripts.OnClick(pb)
      lay.scripts.OnClick(lay)
      do
        local lines = {}
        local add = GameTooltip.AddLine
        GameTooltip.AddLine = function(_, t) lines[#lines + 1] = t end
        lay.scripts.OnEnter(lay)
        GameTooltip.AddLine = add
        local all = table.concat(lines, " ")
        ck(all:find("wide window", 1, true) and not all:find("character column", 1, true), "with the column folded, the Full window tooltip doesn't promise it: " .. all)
      end
      ck(win.layoutMode == "compact" and T.db.ui.winPaneHidden, "compact keeps the folded choice")
      lay.scripts.OnClick(lay)
      ck(win.layoutMode == "narrow" and win._w == 592, "and leaving compact goes back to the narrow window")
      ck(near(sx(), x0), "the corner stayed put the whole time")
      -- 1.6.0: no round Professions button in the header; the narrow header's cat button follows
      -- Settings, then the layout button
      ck(win.profQuick == nil, "no Professions button by the title")
      ck(_pt(win.paneButton, "LEFT") and _pt(win.paneButton, "LEFT")[2] == win.tabButtons[win.TAB_SETTINGS], "narrow: the cat button follows Settings")
      ck(_pt(lay, "LEFT") and _pt(lay, "LEFT")[2] == win.paneButton, "narrow: the layout button follows the cat button")
      -- an added header button goes after the Compendium button in compact; the try-on cat shows
      local extra = CreateFrame("Button", nil, win)
      win:AddHeaderButton(extra, function(b) b:SetPoint("RIGHT", lay, "LEFT", -6, 0) end)
      lay.scripts.OnClick(lay)
      ck(win.layoutMode == "compact" and _pt(extra, "LEFT") and _pt(extra, "LEFT")[2] == P.compBtn, "an added header button sits after the Compendium button")
      win.preview:ApplyAppearance(T:GetAppearance(nil, T.ITEM_LIST[1]))
      ck(win.tryOnStage:IsShown(), "the try-on cat shows in compact")
      win.preview:ApplyAppearance(T:GetAppearance())
      ck(not win.tryOnStage:IsShown(), "and goes")
      lay.scripts.OnClick(lay)
      -- every layout button tooltip, no exclamation marks
      for _, b in ipairs({ lay, pb, win.compactStrip, win.compIcon }) do
        local lines = {}
        local add = GameTooltip.AddLine
        GameTooltip.AddLine = function(_, t) lines[#lines + 1] = t end
        b.scripts.OnEnter(b)
        GameTooltip.AddLine = add
        ck(#lines >= 2 and not table.concat(lines):find("!", 1, true), "tooltip: " .. table.concat(lines, " / "))
      end
      T.db.ui.winPaneHidden = nil
      win:ApplyLayout()
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("compact window: " + r)
    # remembered, and every tab builds and refreshes in compact
    lua = load_addon()
    r = lua.execute(RECORDER + r'''
      local T = TapCatForever
      T.db.ui.winCompact = true
      T:ToggleWindow()
      local win = T.window
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      ck(win._w == 420 and win.layoutMode == "compact" and win.roundTabs[2].selected, "compact is remembered, Adventure open")
      for i = 1, #win.tabButtons do win:SelectTab(i); win:Refresh(); ck(win.tab == i and win.parts.right:IsShown(), "tab " .. i .. " in compact") end
      for _, cl in ipairs(T.CLASSES) do T:SetClass(cl.key) end
      ck(win.compactStrip.lvl:GetText():find(T.CLASS_BY_KEY[T.db.class].name, 1, true), "the bottom line names the class")
      -- the What's new strip takes the compact window's width, and the full width again after
      T.version = T.NEWS[1].version
      T.NEWS_POPUPS = {} -- (1.6.0's news is a pop-up; the strip is for later versions)
      T.db.newsSeen, T.db.newsShows = nil, nil
      win:Hide(); win:Show(); T:CheckNews()
      local strip = T.newsStrip
      if strip then strip.text.SetWidth = function(fs, w) fs._w = w end; T:FitNewsStrip() end
      ck(T:CurrentNews() == nil or strip and strip:IsShown() and strip._w == 420 and strip.text._w == 420 - 192 and strip._h >= 46, "the news strip fits the compact window: " .. tostring(strip and strip._w) .. " x " .. tostring(strip and strip._h))
      if strip then
      win.layoutButton.scripts.OnClick(win.layoutButton)
      ck(strip._w == 760 and strip.text._w == 520, "and is full width with the full window: " .. tostring(strip._w))
      win.paneButton.scripts.OnClick(win.paneButton)
      ck(strip._w == 592, "and narrow with the narrow window: " .. tostring(strip._w))
      -- placed with its real height (it grows in narrow windows): above the window only if it fits
      strip.GetHeight = function(f) return f._h or 46 end
      function UIParent:GetTop() return 1000 end
      win.GetBottom = function(f) return (f:GetTop() - 620) end
      win:PlaceTopLeft(100, 960)
      strip._h = 46; T:FitNewsStrip()
      ck(_pt(strip, "TOP") and _pt(strip, "TOP")[3] == "BOTTOM", "a tall strip with no room above goes below: " .. tostring(strip._h))
      win:PlaceTopLeft(100, 900)
      T:FitNewsStrip()
      ck(_pt(strip, "BOTTOM") and _pt(strip, "BOTTOM")[3] == "TOP", "with room above, above the window")
      win:PlaceTopLeft(100, 970); win.GetBottom = function() return 5 end
      T:FitNewsStrip()
      ck(_pt(strip, "TOP") and _pt(strip, "TOP")[3] == "TOP", "no room either side: just inside the top edge")
      win.GetBottom = nil; UIParent.GetTop = nil
      _newsPlaced = true
      T:MarkNewsSeen()
      end
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("compact window (remembered): " + r)
    assert lua.eval("_newsPlaced") or lua.eval("TapCatForever:CurrentNews() == nil"), "the news strip checks did not run"
    print("compact window section (narrow and tall, round tabs, pages scaled to fit, Casino scaled, character view, grip, quest count, back to full and narrow, no Professions button, the cat button before the layout button, the Casino where Achievements was, remembered): all checks passed")
