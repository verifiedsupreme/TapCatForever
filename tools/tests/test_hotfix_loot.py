# 1.5.3.1: chest gear stays near the cat's level, rare world Epics stay rare, the reel spins for
# every chest opened by hand and the loot box only follows blue or better.
def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    res = lua.execute(r'''
      local T = TapCatForever
      local out, problems = {}, {}
      local chests = { "pouch", "strong", "heroic", "dungeon", "raid" }
      for _, class in ipairs({ "MAGE", "WARRIOR", "HUNTER", "PRIEST", "ROGUE" }) do
        T.db.class = class
        T.db.classData[class] = T.db.classData[class] or {}
        local cd = T:CD(class)
        if not cd.adv then T:CD() end
        for _, lvl in ipairs({ 1, 5, 10, 15, 20, 25, 30, 40, 50, 55, 60 }) do
          cd.level = lvl
          for _, key in ipairs(chests) do
            local ch = T.CHEST_BY_KEY[key]
            local over, n, counts, jordan, legend = 0, 0, {}, 0, 0
            for i = 1, 300 do
              local rarity = T:RollRarity(ch.weights)
              local g = T:ChestGear(ch, rarity)
              if g then
                n = n + 1
                if (g.req or 0) > lvl + 3 and not (lvl >= 55 and (g.req or 0) <= 60) then over = over + 1 end
                counts[g] = (counts[g] or 0) + 1
                if g.name == "Staff of Jordan" then jordan = jordan + 1 end
                if g.q == 5 then legend = legend + 1 end
              end
            end
            local top, topn = nil, 0
            for g, c in pairs(counts) do if c > topn then top, topn = g, c end end
            if over > 0 then problems[#problems + 1] = string.format("%s lv%d %s: %d above level+3", class, lvl, key, over) end
            if jordan > 0 then problems[#problems + 1] = string.format("%s lv%d %s: Staff of Jordan x%d", class, lvl, key, jordan) end
            if lvl < 60 and legend > 0 then problems[#problems + 1] = string.format("%s lv%d %s: legendary", class, lvl, key) end
            if class == "MAGE" then out[#out + 1] = string.format("%-6s lv%2d %-8s n=%d top=%s x%d", class, lvl, key, n, top and top.name or "-", topn) end
          end
        end
      end
      -- the legendary roll inside OpenChestContents is off below 60
      T.db.class = "MAGE"; T:CD().level = 30
      local ch = T.CHEST_BY_KEY.heroic
      local saved = ch.legendary; ch.legendary = 1
      for i = 1, 50 do local g = T:OpenChestContents(ch, "heroic"); if g and g.q == 5 then problems[#problems + 1] = "legendary at 30"; break end end
      ch.legendary = saved
      return table.concat(problems, "\n"), table.concat(out, "\n")
    ''')
    problems, table_ = res[0], res[1]
    if problems:
        raise AssertionError("hotfix loot:\n" + problems)
    # the reel: a green from a chest you open yourself spins, then a slim line, no loot box
    r = lua.execute(r'''
      local T = TapCatForever
      local reel, toast, box = 0, 0, 0
      local oReel, oToast, oBox = T.PlayChestReel, T.ShowLootToast, T.ShowLootRevealDirect
      T.PlayChestReel = function(self, ...) reel = reel + 1; return oReel(self, ...) end
      T.ShowLootToast = function(self, ...) toast = toast + 1 end
      T.ShowLootRevealDirect = function(self, ...) box = box + 1 end
      T.db.ui.chestAnim = true
      if T.reel then T.reel:Hide(); T.reel.queue = {} end
      local green
      for _, list in pairs(T.WORLD_POOL) do for _, g in ipairs(list) do if g.q == 2 then green = g; break end end if green then break end end
      T:ShowLootReveal(green, true, 0, "Cat Treat Pouch", "pouch", true)
      if T.reel and T.reel.Finish then T.reel:Finish() end
      local r1, t1, b1 = reel, toast, box
      if T.reel then T.reel:Hide(); T.reel.queue = {} end
      reel, toast, box = r1, t1, b1
      local blue
      for _, list in pairs(T.WORLD_POOL) do for _, g in ipairs(list) do if g.q == 3 then blue = g; break end end if blue then break end end
      T:ShowLootReveal(blue, true, 0, "Cat Treat Pouch", "pouch", true)
      if T.reel and T.reel.Finish then T.reel:Finish() end
      T.PlayChestReel, T.ShowLootToast, T.ShowLootRevealDirect = oReel, oToast, oBox
      return r1, t1, b1, reel, toast, box
    ''')
    r = tuple(r)
    if not (r[0] == 1 and r[1] == 1 and r[2] == 0 and r[3] == 2 and r[4] == 1 and r[5] == 1):
        raise AssertionError("hotfix reel: green/blue reel,toast,box counts %r" % (r,))
    print(table_)
    print("hotfix loot section (chest gear near level, rare world epics, legendaries at 60, reel for every chest): all checks passed")
