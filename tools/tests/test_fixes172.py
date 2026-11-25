# 1.7.2 fixes: item sets say where they come from, show their pieces and try on (whole set or a piece),
# test mode can give any item or set (and nothing outside test mode), the recipe search box, and
# crafting a guild order's gear right from the order.

def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      -- set sources
      local wrath
      for _, s in ipairs(T.ITEM_SETS) do if s.name == "Battlegear of Wrath" then wrath = s end end
      ck(wrath, "Battlegear of Wrath exists")
      local nWith = 0
      for _, s in ipairs(T.ITEM_SETS) do
        local lines, tag = T:SetSources(s)
        if #lines > 0 and tag ~= "" then nWith = nWith + 1 end
      end
      ck(nWith == #T.ITEM_SETS, "every set says where it comes from: " .. nWith .. "/" .. #T.ITEM_SETS)
      if wrath then
        local lines = T:SetSources(wrath)
        ck(table.concat(lines, " "):find("Adventure", 1, true), "Wrath: from Adventure: " .. table.concat(lines, " | "))
      end
      -- try on a whole set, then take it off again
      T:ToggleWindow()
      local win = T.window
      if wrath then
        T:CompendiumPreviewSet(wrath)
        local n = 0
        for _, id in ipairs(wrath.items) do if T.GEAR[id] and T.UI.IsPinned(win, T.GEAR[id]) then n = n + 1 end end
        ck(n > 0, "the set's pieces are on the cat: " .. n)
        T:CompendiumPreviewSet(wrath)
        local m = 0
        for _, id in ipairs(wrath.items) do if T.GEAR[id] and T.UI.IsPinned(win, T.GEAR[id]) then m = m + 1 end end
        ck(m == 0, "and off again: " .. m)
      end
      -- giving: only in test mode
      T.db.ui.testMode = nil
      local cos
      for _, it in ipairs(T.ITEM_LIST) do if it.source == "loot" and not T.db.owned[it.id] then cos = it; break end end
      ck(not T:TestGive(cos) and not T.db.owned[cos.id], "nothing is given outside test mode")
      T.db.ui.testMode = true
      ck(T:TestGive(cos) and T.db.owned[cos.id], "a cosmetic given in test mode")
      if wrath then
        ck(T:TestGiveSet(wrath), "a set given in test mode")
        local bag, all = T:Bag(), true
        for _, id in ipairs(wrath.items) do if T.GEAR[id] and not bag[id] then all = false end end
        ck(all, "every piece in the bag")
      end
      T.db.ui.testMode = nil
      -- the recipe search
      T:SetClass("MAGE")
      win:SelectTab(win.TAB_PROFESSIONS)
      win.profView = "craft"; win:Refresh()
      local box = win.craftSearchBox
      ck(box, "a search box on the recipe list")
      local function shown()
        local n = 0
        for _, f in ipairs(_frames) do
          if f.kind == "FontString" and type(f.text) == "string" and f.text:find("^Recipes %d+%-%d+ of (%d+)") then n = tonumber(f.text:match("of (%d+)")) end
        end
        return n
      end
      local all = shown()
      box:SetText("robe"); box.scripts.OnTextChanged(box)
      local some = shown()
      ck(all > some and some > 0, "searching narrows the list: " .. all .. " -> " .. some)
      box:SetText(""); box.scripts.OnTextChanged(box)
      ck(shown() == all, "clearing shows them all again")
      -- craft for a guild order
      local craft = T:CraftProf()
      local rec
      for _, r in ipairs(T.RECIPES[craft]) do if r.gear and not r.starter and (r.skill or 1) <= 1 then rec = r; break end end
      if not rec then for _, r in ipairs(T.RECIPES[craft]) do if r.gear then rec = r; break end end end
      local s = T:ProfState()
      s.skill[craft] = math.max(s.skill[craft] or 1, rec.skill or 1)
      for m, n in pairs(rec.mats) do s.mats[m] = (s.mats[m] or 0) + n * 3 end
      local d = T:DepthState(); d.orders[craft] = d.orders[craft] or {}
      local o = { kind = "gear", key = rec.gear, n = 1, who = "a tester", rep = 10, gold = 5, coins = 0, id = 7777, expires = time() + 3600 }
      table.insert(d.orders[craft], o)
      T.MASTERWORK_CHANCE = 0
      ck(T:OrderCanCraft(o, craft), "the order's gear can be made here")
      ck(T:CraftForOrder(7777, craft) and T:OrderHave(o) >= 1 and not T:OrderCanCraft(o, craft), "crafted for the order, then nothing more needed")
      return table.concat(fails, "; ")
    ''')
    assert r == "", "1.7.2 fixes: " + r
    print("1.7.2 fixes section (set sources, try on a set and a piece, test mode gives items and sets, recipe search, craft for a guild order): all checks passed")
