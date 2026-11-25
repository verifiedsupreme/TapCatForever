# 1.7.3 materials library (MatLibrary.lua): every material says where it comes from, the Compendium's
# Materials page lists and searches them, recipe tooltips say where a missing material comes from;
# cosmetic sets (crafted and dungeon) lead the Item Sets list; the Sets button in the recipe list.

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      local none = {}
      for key in pairs(T.MAT_BY_KEY) do if not T:MatSource(key) then none[#none + 1] = key end end
      ck(#none == 0, "every material has a source: " .. table.concat(none, ", "))
      ck(T:MatSource("demonicrune"):find("Gordunni Camp", 1, true), "Demonic Rune: from Gordunni Camp on: " .. T:MatSource("demonicrune"))
      ck(T:MatSource("arcanite"):find("Weaponsmith", 1, true), "Arcanite Bar: the Weaponsmith daily craft")
      for key in pairs(T.POTION_BY_KEY or {}) do ck(T:MatSource(key):find("Brewed", 1, true), key .. " is brewed, not grown") end
      local all = #T:MatLibraryList()
      local rune = T:MatLibraryList("rune")
      ck(#rune >= 1 and #rune < all, "the search narrows it: " .. #rune)
      -- the Compendium page
      T:ToggleCompendium()
      local f = T.compendium
      f.cat = "mats"; f.page = 1; f:Refresh()
      ck(f.matsView and f.matsView:IsShown(), "a Materials page")
      f.matsView.box:SetText("demonic"); f.matsView.box.scripts.OnTextChanged(f.matsView.box)
      local shown = 0
      for _, r in ipairs(f.matsView.rows) do if r:IsShown() then shown = shown + 1 end end
      ck(shown == 1 and f.matsView.rows[1].key == "demonicrune", "searching finds Demonic Rune")
      -- cosmetic sets lead the Item Sets list
      f.cat = "sets"; f.page = 1; f:Refresh()
      local first = f.setsView.rows[1]
      ck(first.cos and first.set.prof, "the crafted legendary sets come first: " .. tostring(first.set and first.set.name))
      return table.concat(fails, "; ")
    ''')
    assert r == "", "materials library: " + r
    print("materials library section (every material's source, potions brewed, search, the Compendium page, cosmetic sets first): all checks passed")
