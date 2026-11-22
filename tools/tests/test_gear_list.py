# 1.5.3.4: gear the cat wears is not listed in the Gear page's bag list (spare copies are)
def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      T:CreateWindow(); T.window:Show(); T.window:SelectTab(1)
      local class = T.db.class
      T:CD().level = 40
      local it
      local slotKey
      for _, g in ipairs(T.GEAR_LIST) do
        local ts = T:GearTargetSlots(g, class)
        if g.q == 2 and #ts == 1 and ts[1] == "HEAD" and T:GearUsable(g, class) and not g.placeholder and g.req <= 40 and not g.crafted then it, slotKey = g, ts[1]; break end
      end
      if not it then return "no test item" end
      local function listed()
        T.window:Refresh()
        for _, f in ipairs(_frames) do if f.item == it and f.shown and f.equip then return true end end
        return false
      end
      T:GrantGear(it, "test")
      if not listed() then return "a new item is listed" end
      T:EquipGear(it.id)
      if listed() then return "a worn item is not listed" end
      T:GrantGear(it, "test")
      if not listed() then return "a spare copy is listed" end
      T:SellGear(it.id)
      if listed() then return "after selling the spare, the worn one is not listed" end
      T:UnequipGear("HEAD")
      if not listed() then return "taken off: listed again" end
      return ""
    ''')
    if r:
        raise AssertionError("gear list: " + r)
    print("gear list section (worn gear not listed, spares are, taken off comes back): all checks passed")
