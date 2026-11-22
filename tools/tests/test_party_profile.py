# 1.5.3.6: click a party cat to see its profile (the cat, class, level and worn gear)
def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      _group = { party1 = { "Alice", nil } }
      _fire("GROUP_ROSTER_UPDATE")
      local helm
      for _, g in ipairs(T.GEAR_LIST) do if g.q == 3 and #T:GearTargetSlots(g, "WARRIOR") == 1 and T:GearTargetSlots(g, "WARRIOR")[1] == "HEAD" then helm = g; break end end
      _fire("CHAT_MSG_ADDON", "TapCatFvr", "U1;WARRIOR;23;;;;h=#" .. helm.id, "PARTY", "Alice-Forever")
      local row = TapCatForeverPartyCats
      if not (row and row.cells[1]:IsShown()) then return "Alice's cat is in the row" end
      -- your own message never adds your own cat
      _fire("CHAT_MSG_ADDON", "TapCatFvr", "U1;MAGE;5;;;;", "PARTY", _charName .. "-SomeOtherRealmForm")
      if T:PartyCount() ~= 1 then return "own cat added" end
      local cell = row.cells[1]
      cell.scripts.OnClick(cell, "LeftButton")
      local f = TapCatForeverPartyProfile
      if not (f and f:IsShown()) then return "profile opens" end
      if f.title.text ~= "Alice" then return "profile name: " .. tostring(f.title.text) end
      local found = false
      for _, c in ipairs(f.cells) do if c.item == helm then found = true end end
      if not found then return "profile shows the helm" end
      if not tostring(f.sub.text):find("Level 23 Warrior", 1, true) then return "class and level: " .. tostring(f.sub.text) end
      _group = nil; _fire("GROUP_ROSTER_UPDATE")
      return ""
    ''')
    if r:
        raise AssertionError("party profile: " + r)
    print("party profile section (click a party cat: name, class, level, gear; own cat never added): all checks passed")
