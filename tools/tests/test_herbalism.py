# 1.6.7 Herbalism: each plot keeps its own seed (right-click: grow the picked seed there next,
# shift-right-click: dig up and plant now, or every plot at once), Bramble the gardener plants empty
# plots and replants with each plot's seed and trains from Apprentice to Master, 26 herbs with
# Swiftthistle, Wildvine and Black Lotus from some harvests, new garden upgrades, and potions brewed
# in Herbalism's Crafting list (one potion buff at a time, on top of Well Fed).

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      T.ProfUnlocked = function() return true end
      local ps = T:ProfState()
      ps.gold, ps.lifetime = 1e12, 1e17
      local function wait(sec) ps.last = time() - sec; T:ProfessionsTick(true) end
      local g = T:GardenState()

      -- the seed list: sorted by skill, every herb a material, teach levels never below the skill
      local prev = 0
      for i, sd in ipairs(T.SEEDS) do
        ck(sd[7] >= prev, "seeds sorted by skill at " .. sd[1]); prev = sd[7]
        ck(T.MAT_BY_KEY[sd[1]], "material for " .. sd[1])
        ck(sd.teach >= sd[7], "teach level " .. sd[1])
        if sd.rare then ck(T.RARE_BY_KEY[sd.rare[1]], "rare herb " .. sd.rare[1]) end
      end
      ck(#T.SEEDS >= 26, "26 herbs: " .. #T.SEEDS)
      for _, r in ipairs(T.RARE_HERBS) do ck(T.RareSources(r.key) ~= "", "some seed brings " .. r.key) end

      -- a 1.6.6 save: the gardener was one upgrade, it is rank 1 now
      g.up.gardener = true; g.gl = nil
      ck(T:GardenerLevel() == 1, "an old gardener is an Apprentice")
      g.up.gardener = nil; g.gl = nil

      -- empty plot, plant, the plot remembers its seed
      ps.skill.herbalism = 1
      ck(T:Plant(1, "peacebloom") and T:PlotWant(1) == "peacebloom", "planted, and the plot remembers peacebloom")
      ck(not T:PlotSetNext(1, "icecap"), "can't pick a seed above your skill")
      ck(T:PlotSetNext(1, "silverleaf") and T:PlotWant(1) == "silverleaf" and g.plots[1].seed == "peacebloom", "right-click: silverleaf next, peacebloom still grows")
      -- without a gardener, a harvested plot stays empty and a click plants its next seed
      wait(61)
      ck(T:PlotClick(1) and not g.plots[1], "harvested by hand")
      ck(T:PlotClick(1) and g.plots[1].seed == "silverleaf", "a click on the empty plot plants the seed it remembers")

      -- the gardener: replants each plot with its own seed, and plants empty plots
      g.plots = {}; g.want = {}
      ck(T:TrainGardener() and T:GardenerLevel() == 1 and g.up.gardener, "hired Bramble (Apprentice)")
      T:Plant(1, "peacebloom"); T:Plant(2, "peacebloom")
      T:PlotSetNext(2, "silverleaf")
      g.want[3] = "peacebloom"    -- an empty plot with a seed to grow
      wait(70)
      ck(g.plots[1] and g.plots[1].seed == "peacebloom", "plot 1 keeps growing peacebloom")
      ck(g.plots[2] and g.plots[2].seed == "silverleaf", "plot 2 switched to silverleaf at its harvest")
      ck(g.plots[3] and g.plots[3].seed == "peacebloom", "Bramble planted the empty plot")
      -- dig up now
      local gold0 = ps.gold
      ck(T:PlotDig(1, "silverleaf") and g.plots[1].seed == "silverleaf" and g.plots[1].grown == 0, "shift-right-click: dug up, silverleaf planted now")
      ck(ps.gold == gold0 - T.SEED_BY_KEY.silverleaf[5], "digging up pays for the new seed only")
      -- every plot at once
      T:BuyPlot()
      local ok, planted = T:GardenPlantAll("earthroot")
      ck(not ok, "earthroot needs skill 15")
      ps.skill.herbalism = 20
      ok, planted = T:GardenPlantAll("earthroot")
      ck(ok and planted == 1 and g.plots[4].seed == "earthroot", "every plot: the empty one planted now (" .. tostring(planted) .. ")")
      local all = true
      for i = 1, g.n do if T:PlotWant(i) ~= "earthroot" then all = false end end
      ck(all, "every plot grows earthroot next")

      -- the ranks
      ck(math.abs(T:GardenSpeed() - 1) < 1e-9, "Apprentice: normal speed")
      ck(T:TrainGardener() and math.abs(T:GardenSpeed() - 1.25) < 1e-9, "Journeyman: 25% faster")
      ck(T:TrainGardener() and T:GardenerLevel() == 3, "Expert")
      g.plots = {}; g.want = {}; g.saved = 0
      for i = 1, g.n do T:Plant(i, "peacebloom") end
      local g0 = ps.gold
      wait(60 * 60 * 3)
      ck((g.saved or 0) > 0, "Expert: some replants were free (" .. tostring(g.saved) .. ")")
      local n0 = ps.mats.peacebloom or 0
      g.plots = { { seed = "peacebloom", grown = 59 } }
      g.want = { "peacebloom" }
      ck(T:TrainGardener() and T:GardenerLevel() == 4, "Artisan")
      T:PlotClick(1); T:PlotClick(1)
      ck((ps.mats.peacebloom or 0) - n0 == 2 * 1 + 0 or (ps.mats.peacebloom or 0) - n0 == 2, "Artisan: one more herb (skill below 100: 1 + 1)")
      ck(T:TrainGardener() and T:GardenerLevel() == 5 and T:RareMult() == 2, "Master: rare herbs twice as often")
      ck(not T:TrainGardener(), "nothing past Master")
      T:BuyGardenUpgrade("moonwell")
      ck(T:RareMult() == 4, "with the Moonwell: four times")
      -- a rare herb from a harvest
      local sd = T.SEED_BY_KEY.mageroyal
      local keep = sd.rare[2]; sd.rare[2] = 1
      ps.skill.herbalism = 60
      g.plots = { { seed = "mageroyal", grown = 1e9 } }
      local st0 = ps.mats.swiftthistle or 0
      T:PlotClick(1)
      ck((ps.mats.swiftthistle or 0) == st0 + 1, "Mageroyal brought Swiftthistle")
      sd.rare[2] = keep
      -- Rain Barrel: watering three times as much
      g.plots = { { seed = "peacebloom", grown = 0 } }
      T:PlotClick(1)
      local w1 = g.plots[1].grown
      T:BuyGardenUpgrade("rainbarrel")
      g.plots[1].grown = 0; T:PlotClick(1)
      ck(math.abs(g.plots[1].grown - 3 * w1) < 1e-6, "Rain Barrel: three times the watering")

      -- potions: in Herbalism's Crafting list, brewed from herbs
      local rec
      for _, r in ipairs(T.RECIPES.herbalism) do if r.potion == "p_wisdom" then rec = r end end
      ck(rec and rec.teach and T:RecipeItem(rec) and T:RecipeItem(rec).name == "Elixir of Wisdom", "Elixir of Wisdom is a recipe")
      local npot = 0
      for _, r in ipairs(T.RECIPES.herbalism) do
        if r.potion then
          npot = npot + 1
          for m in pairs(r.mats) do ck(T.MAT_BY_KEY[m], r.potion .. " uses a known herb: " .. m) end
          ck(T.MAT_BY_KEY[r.potion] and T.MAT_BY_KEY[r.potion].value > 0, r.potion .. " sells for something")
        end
      end
      ck(npot >= 15, "15 potions: " .. npot)
      ps.skill.herbalism = 80
      ck(T:CraftBlocked(rec) ~= nil, "needs Herbalism 90")
      ps.skill.herbalism = 95
      ps.mats.mageroyal, ps.mats.stranglekelp, ps.mats.p_wisdom = 9, 6, 0
      ck(T:CraftCount(rec) == 3, "three Elixirs of Wisdom from the herbs: " .. T:CraftCount(rec))
      ck(T:CraftAll(rec) == 3 and ps.mats.p_wisdom == 3 and ps.mats.mageroyal == 0, "brewed three")
      -- drink: one potion at a time, on top of Well Fed
      local xp0 = T:FoodBuff("xp")
      ck(T:DrinkPotion("p_wisdom") and ps.mats.p_wisdom == 2, "drank one")
      ck(math.abs(T:FoodBuff("xp") - xp0 * 1.10) < 1e-9, "+10% cat XP")
      local cook = T:CookState()
      cook.buff = { key = "d_smallfish", kind = "xp", value = 0.10, ["until"] = time() + 600 }
      ck(math.abs(T:FoodBuff("xp") - 1.10 * 1.10) < 1e-9, "a dish and a potion both count")
      ck(T:PotionLine():find("Elixir of Wisdom", 1, true), "the potion line")
      ps.mats.p_lion = 1
      T:DrinkPotion("p_lion")
      ck(math.abs(T:FoodBuff("xp") - 1.10) < 1e-9 and T:FoodBuff("dmg") > 1, "a new potion replaces the old one")
      cook.buff = nil
      -- the Alchemy Lab doubles how long they last (bought earlier? buy it now)
      T:BuyGardenUpgrade("alchemylab")
      T:DrinkPotion("p_wisdom")
      local b = T:PotionActive()
      ck(b and math.abs((b["until"] - time()) - 60 * 60) < 2, "Alchemy Lab: 30 minutes become an hour")
      ck(not T:DrinkPotion("p_titans"), "can't drink what you don't have")
      -- a potion belongs to the cat that drank it
      ck(T:PotionBuff("xp", "WARRIOR") == 1, "the Warrior's cat didn't drink it")

      -- selling the business resets the garden, gardener included
      for _, m in ipairs(T.PROF_MODULES) do if m.key == "herbalism" then m.reset(T, ps) end end
      ck(T:GardenerLevel() == 0 and next(T:GardenState().want) == nil, "a sale resets Bramble and the plots' seeds")

      -- the screens: Gardener view, right-click a plot, Drink button
      T:ToggleWindow()
      local win = T.window
      win:SelectTab(win.TAB_PROFESSIONS)
      win.profSel = "herbalism"; win.profView = "upg"; win:Refresh()
      T.db.profGuides = { family = true, herbalism = true, firstaid = true, fishing = true, cooking = true }
      win:Refresh()
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("herbalism: " + r)
    print("herbalism section (26 herbs, a seed per plot, Bramble plants and replants with each plot's seed, ranks Apprentice to Master, rare herbs, "
          "Rain Barrel, Moonwell, potions brewed and drunk, one at a time, on top of Well Fed, Alchemy Lab, reset on sale): all checks passed")
