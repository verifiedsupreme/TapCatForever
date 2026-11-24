# 1.6.3: shift-click an item to try it on your cat. The item stays on the window's cat until it is
# shift-clicked again or Clear preview is pressed, several at once (one per slot); nothing is equipped
# or bought. Hovering still only shows the tooltip as before, and leaving an item puts the pinned look
# back (not the bare one). Pins go when the window closes or the class changes. Gear list, Appearance,
# Shop, recipes and the Compendium all do it.

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      local U = T.UI
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      _shift = false
      IsShiftKeyDown = function() return _shift end
      T:ToggleWindow()
      local win = T.window
      local applied
      local apply0 = win.preview.ApplyAppearance
      win.preview.ApplyAppearance = function(cat, look, ...) applied = look; return apply0(cat, look, ...) end
      -- a hat and a cape the cat doesn't wear, and a piece of gear
      local hat, cape, hat2
      for _, it in ipairs(T.ITEM_LIST) do
        if not it.class or it.class == T.db.class then
          if it.slot == "head" and not hat then hat = it
          elseif it.slot == "head" and hat and not hat2 then hat2 = it
          elseif it.slot == "back" and not cape then cape = it end
        end
      end
      local gear
      for id, g in pairs(T.GEAR) do
        if g.slot and (g.slot == "INVTYPE_HEAD" or g.slot == "HEAD" or g.invType == "HEAD") then gear = g; break end
      end
      if not gear then for id, g in pairs(T.GEAR) do gear = g; break end end
      ck(hat and cape and hat2 and gear, "test items found")
      ck(U.IsGearItem(gear) and not U.IsGearItem(hat), "gear and cosmetics told apart")
      local base = T:GetAppearance()
      ck(base.head ~= hat and base.back ~= cape, "the cat doesn't wear them")
      -- a plain click elsewhere does nothing here; shift-click pins
      ck(U.PreviewClick(win, hat) == false, "no shift: not handled")
      _shift = true
      ck(U.PreviewClick(win, hat) == true and U.IsPinned(win, hat), "shift-click pins the hat")
      ck(applied and applied.head == hat, "the window's cat wears it")
      ck(win.previewClear:IsShown(), "Clear preview shows")
      ck(not T:IsEquipped(hat) and T:GetAppearance().head ~= hat, "nothing equipped")
      U.PreviewClick(win, cape)
      ck(applied.head == hat and applied.back == cape and #win.pinOrder == 2, "a cape on top: both on")
      -- hovering another item and leaving it keeps the pins
      U.ShowTryOn(win, hat2)
      ck(applied.head == hat2 and applied.back == cape, "hovering another hat shows it over the pinned cape")
      U.HideTryOn(win)
      ck(applied.head == hat and applied.back == cape, "leaving it puts the pinned look back")
      -- a refresh keeps them
      win:Refresh()
      ck(applied.head == hat and applied.back == cape, "a window refresh keeps the pins")
      -- a second hat replaces the first in its slot; shift-clicking it again takes it off
      U.PreviewClick(win, hat2)
      ck(applied.head == hat2 and not U.IsPinned(win, hat) and #win.pinOrder == 2, "one item per slot")
      U.PreviewClick(win, hat2)
      ck(applied.head == base.head and applied.back == cape and #win.pinOrder == 1, "shift-click again takes it off")
      -- gear
      U.PreviewClick(win, gear)
      ck(U.IsPinned(win, gear) and #win.pinOrder == 2, "gear pins too")
      -- Clear preview
      win.previewClear.scripts.OnClick(win.previewClear)
      ck(#win.pinOrder == 0 and not win.previewClear:IsShown() and applied.back == base.back, "Clear preview takes everything off")
      -- the tooltip line
      local lines = {}
      local tt = { AddLine = function(_, t) lines[#lines + 1] = t end }
      U.PreviewHint(tt, win, hat)
      U.PreviewClick(win, hat)
      U.PreviewHint(tt, win, hat)
      ck(lines[1] == "Shift-click to try it on your cat." and lines[2] == "Shift-click to take it off your cat.", "hint lines: " .. table.concat(lines, " / "))
      -- class change drops the pins; closing the window too
      local other
      for _, c in ipairs(T.CLASSES) do if c.key ~= T.db.class then other = c.key; break end end
      T:SetClass(other)
      win:Refresh()
      ck(#(win.pinOrder or {}) == 0, "a class change drops the pins")
      U.PreviewClick(win, cape)
      ck(#win.pinOrder == 1, "pinned again")
      win:Hide()
      if win.scripts and win.scripts.OnHide then win.scripts.OnHide(win) end
      ck(#win.pinOrder == 0, "closing the window drops the pins")
      -- the Compendium opens the window and pins there
      if T.CompendiumPreview then
        T:CompendiumPreview(hat)
        ck(win:IsShown() and U.IsPinned(win, hat), "shift-click in the Compendium tries it on in the window")
      end
      _shift = false
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("preview pins: " + r)
    print("preview pins section (shift-click tries items on the window's cat, stacks per slot, hover keeps pins, Clear, class change and closing drop them, Compendium): all checks passed")
