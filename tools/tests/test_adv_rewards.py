# Adventure track A and B: first-kill rewards that grow by zone, the status line and guide,
# farmable bosses (repeat-kill loot, Farm this, Stop farming), TCF.BOSS_COSMETICS, and a
# measured time-to-drop for typical pieces when farming.
def check(seed, load_addon):
    lua = load_addon()
    lua.execute("_seed = %d; math.randomseed(_seed)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local bad = {}
      local function ck(c, m) if not c then bad[#bad + 1] = m end end
      T.db.ui.chat = true
      local cls = T.CLASSES[_seed % #T.CLASSES + 1].key
      T:SetClass(cls)
      local adv = T:CD().adv
      local function tierOf(key) for i, t in ipairs(T.TIERS) do if t.key == key then return i end end end
      -- watch what a first kill gives
      local gear, chests = {}, {}
      local G, A = T.GrantGear, T.AwardChest
      T.GrantGear = function(self, it, reason, ...) gear[#gear + 1] = it; return G(self, it, reason, ...) end
      T.AwardChest = function(self, key, src, ...) chests[#chests + 1] = key; return A(self, key, src, ...) end
      local function firstKill(key, bi, final)
        local ti = tierOf(key)
        local t = T.TIERS[ti]
        adv.tier, adv.stage = ti, bi * 2
        adv.cleared[T.AdvStageCode(ti, bi * 2)] = nil
        adv.chestClock, adv.dungeonClock = 0, 0
        gear, chests = {}, {}
        T:AdvMobKilled({ name = t.bosses[bi][1], boss = bi, final = final, level = t.diff })
        return gear, chests
      end
      local N = 120
      local stats = {}
      for _, c in ipairs({ { "elwynn", 2, "world" }, { "dm", 3, "early" }, { "sm", 2, "mid" }, { "brd", 3, "late" }, { "mc", 2, "raid" }, { "mc", 6, "raidfinal", true } }) do
        local s = { n = 0, pieces = 0, chests = {}, minQ = 9, maxQ = 0, both = 0, none = 0, maxPieces = 0, minPieces = 9 }
        for i = 1, N do
          local g, ch = firstKill(c[1], c[2], c[4])
          s.n = s.n + 1; s.pieces = s.pieces + #g
          s.maxPieces, s.minPieces = math.max(s.maxPieces, #g), math.min(s.minPieces, #g)
          for _, it in ipairs(g) do
            s.minQ, s.maxQ = math.min(s.minQ, it.q), math.max(s.maxQ, it.q)
            ck(T:GearUsable(it, cls), c[3] .. ": a first-kill piece the class can't use: " .. it.name)
            ck(it.q <= 4, c[3] .. ": never a Legendary from a first kill: " .. it.name)
          end
          for _, k in ipairs(ch) do s.chests[k] = (s.chests[k] or 0) + 1 end
          if #g > 0 and #ch > 0 then s.both = s.both + 1 end
          if #g == 0 and #ch == 0 then s.none = s.none + 1 end
        end
        stats[c[3]] = s
      end
      local w, e, m, l, r, rf = stats.world, stats.early, stats.mid, stats.late, stats.raid, stats.raidfinal
      ck(w.both == 0 and w.none == 0 and w.maxQ <= 2 and (w.chests.pouch or 0) > N * 0.15 and (w.chests.pouch or 0) < N * 0.5,
        string.format("open world: a green or a Pouch (%d pouches, both %d, none %d, max q %d)", w.chests.pouch or 0, w.both, w.none, w.maxQ))
      ck(e.minPieces == 1 and e.maxPieces == 1 and (e.chests.pouch or 0) > N * 0.1 and (e.chests.pouch or 0) < N * 0.45,
        string.format("early dungeon: a piece and sometimes a Pouch (%d pouches)", e.chests.pouch or 0))
      ck(m.minQ >= 3 and m.minPieces == 1 and (m.chests.strong or 0) > N * 0.07 and (m.chests.strong or 0) < N * 0.4,
        string.format("mid dungeon: Rare or better, a Strongbox chance (%d strongboxes, min q %d)", m.chests.strong or 0, m.minQ))
      ck(l.minPieces >= 1 and l.maxPieces == 2 and (l.chests.dungeon or 0) > N * 0.25 and (l.chests.dungeon or 0) < N * 0.75,
        string.format("late dungeon: two pieces, or one and a Dungeon Chest (%d chests)", l.chests.dungeon or 0))
      ck(r.minPieces == 2 and r.maxPieces == 2 and (r.chests.raid or 0) > N * 0.07 and (r.chests.raid or 0) < N * 0.4,
        string.format("raid: two pieces and a Hoard chance (%d hoards)", r.chests.raid or 0))
      ck(rf.minPieces == 2 and rf.maxPieces == 3 and (rf.chests.raid or 0) == N,
        string.format("raid final: 2-3 pieces and a Hoard (%d-%d pieces, %d hoards)", rf.minPieces, rf.maxPieces, rf.chests.raid or 0))
      _advFirst = string.format("first kills x%d: world %d pouches, early %d pouches, mid %d strongboxes, late %d dungeon chests, raid %d hoards",
        N, w.chests.pouch or 0, e.chests.pouch or 0, m.chests.strong or 0, l.chests.dungeon or 0, r.chests.raid or 0)
      -- the final boss of a dungeon: its pieces, then the zone clear's Dungeon Chest (one chest only)
      local dm = tierOf("dm")
      adv.cleared[T.AdvStageCode(dm, T:AdvStages(dm))] = nil
      local g, ch = firstKill("dm", 6, true)
      ck(#ch == 1 and ch[1] == "dungeon" and #g >= 1, "The Deadmines' first clear: a piece and the Dungeon Chest: " .. table.concat(ch, ","))
      -- repeat kills: small chances, class-usable only, capped
      local F = T.ADV_FARM
      for _, key in ipairs({ "dm", "sfk", "brd", "mc" }) do
        local ti = tierOf(key)
        for bi = 1, #T.TIERS[ti].bosses do
          local list, total = T:AdvFarmTable(ti, bi, cls)
          ck(total <= F.TOTAL_MAX + 1e-9, key .. " boss " .. bi .. ": total per kill capped: " .. total)
          for _, e2 in ipairs(list) do
            ck(e2[2] <= F.ITEM_MAX + 1e-9 and e2[2] > 0, "per piece chance capped: " .. e2[1].name)
            ck(T:GearUsable(e2[1], cls) and e2[1].q <= 4, "repeat loot is class-usable, never Legendary: " .. e2[1].name)
          end
        end
      end
      ck(#T:AdvFarmTable(1, 5, cls) == 0, "open-world bosses have no repeat loot")
      -- repeat kills drop at about the listed rate
      local ti = dm
      local list, total = T:AdvFarmTable(ti, 6, cls)
      adv.cleared[T.AdvStageCode(ti, 12)] = true
      adv.tier, adv.stage = ti, 12
      gear = {}
      local K = 20000
      for i = 1, K do T:AdvRepeatLoot(ti, { name = "Edwin VanCleef", boss = 6 }) end
      ck(total == 0 or math.abs(#gear / K - total) < total * 0.35 + 0.0005, string.format("repeat drops near the listed rate: %d in %d (%.3f%%)", #gear, K, total * 100))
      T.GrantGear, T.AwardChest = G, A

      ------------------------------------------------ BOSS_COSMETICS
      local cos
      for _, it in ipairs(T.ITEM_LIST) do if it.source == "loot" and not T.db.owned[it.id] and it.slot ~= "skin" then cos = it; break end end
      T.BOSS_COSMETICS["Hogger"] = { cos.id }
      local grants = 0
      local GI = T.GrantItem
      T.GrantItem = function(self, it, ...) grants = grants + 1; return GI(self, it, ...) end
      adv.tier, adv.stage = 1, 10
      T:AdvMobKilled({ name = "Hogger", boss = 5, final = true, level = 10 })
      T:AdvMobKilled({ name = "Hogger", boss = 5, final = true, level = 10 })
      T.GrantItem = GI
      ck(T.db.owned[cos.id] == 1 and grants == 1, "TCF.BOSS_COSMETICS: given on a kill until owned, once: " .. grants)
      local how = table.concat(T:HowToGet(cos), " / ")
      ck(how:find("Adventure: Hogger in Elwynn Forest gives it", 1, true), "boss cosmetic source line: " .. how)
      T.BOSS_COSMETICS["Hogger"] = nil

      ------------------------------------------------ farming
      T:ToggleWindow(); T.window:SelectTab(2)
      local list6 = T:AdvFarmTable(dm, 6, cls)
      local want = list6[1] and list6[1][1]
      adv.best = math.max(adv.best, T.AdvStageCode(dm, 12))
      adv.auto = true
      local ok = T:AdvStartFarm(dm, 6, want and want.id)
      ck(ok and adv.farm and adv.auto == false and adv.tier == dm and adv.stage == 12 and adv.active, "Farm this: Auto-advance off, on the boss's stage, fighting")
      local st = T:AdvStatusText()
      ck(st:find("^Farming Edwin VanCleef for ") and st:find("per kill%), kills so far: 0%.$"), "farming status line: " .. st)
      T.window:Refresh()
      local page = T.window and T.window.tabButtons and nil
      -- a drop-back after losses comes back to the boss after the easier pack
      adv.stage = 11
      T:AdvReset(); T.advRun.pack = {}
      T:AdvPackCleared()
      ck(adv.stage == 12 and adv.farm, "after a drop-back the cat goes back to the farmed boss")
      -- farm until the wanted piece drops (chances raised so the test is quick)
      local printed = {}
      local P = T.Print
      T.Print = function(self, m, force) printed[#printed + 1] = { m, force }; return P(self, m, force) end
      F.SCALE, F.ITEM_MAX, F.TOTAL_MAX = 5, 0.5, 0.9
      local kills = 0
      for i = 1, 400 do
        if not adv.farm then break end
        adv.stage = 12
        T:AdvMobKilled({ name = "Edwin VanCleef", boss = 6, final = true, level = 23 })
        kills = kills + 1
      end
      F.SCALE, F.ITEM_MAX, F.TOTAL_MAX = 0.012, 0.004, 0.006
      T.Print = P
      local stopLines = 0
      for _, p in ipairs(printed) do if p[1]:find("Farming stopped", 1, true) then stopLines = stopLines + 1; ck(p[2] == true and not p[1]:find("!", 1, true), "the stop line prints even with chat off: " .. p[1]) end end
      ck(not adv.farm and stopLines == 1 and adv.auto == true and (not want or T:Bag(cls)[want.id]), "farming stops when the wanted piece drops, one chat line, Auto-advance back on: " .. stopLines)
      -- moving by hand ends farming; turning Auto-advance on ends it
      T:AdvStartFarm(dm, 6, nil)
      T:AdvStep(-1)
      ck(not adv.farm, "moving by hand stops farming")
      T:AdvStartFarm(dm, 6, nil)
      adv.auto = true
      T:AdvReset(); T.advRun.pack = {}
      T:AdvPackCleared()
      ck(not adv.farm, "turning Auto-advance on stops farming")
      ck(not T:AdvStartFarm(tierOf("naxx") or #T.TIERS, 2, nil), "can't farm a boss your cat hasn't reached")
      T:AdvRetreat()

      ------------------------------------------------ the page: status, guide, Bosses and loot, Stop farming
      local function findText(pat)
        for _, f in ipairs(_frames) do if f.kind == "FontString" and f.shown and type(f.text) == "string" and f.text:find(pat) then return f end end
      end
      T.window:SelectTab(2); T.window:Refresh()
      ck(T.db.advGuideSeen, "the guide opened by itself the first time")
      local fs = findText("^How Adventure works")
      ck(fs, "the guide's title is shown")
      local btnLoot, btnStop, btnHelp
      for _, f in ipairs(_frames) do
        if f.kind == "Button" and f.text == "Bosses and loot" then btnLoot = f end
        if f.kind == "Button" and f.text == "Stop farming" then btnStop = f end
        if f.kind == "Button" and f.text == "Help" then btnHelp = btnHelp or f end
      end
      ck(btnLoot and btnStop, "Bosses and loot and Stop farming buttons")
      adv.tier, adv.stage = dm, 12
      btnLoot.scripts.OnClick(btnLoot)
      local lp = T.advLootPanel
      local farmBtn = lp and lp.shown and lp.rows[1].shown and lp.rows[1].item and lp.rows[1].farm
      ck(farmBtn, "loot rows with a Farm button")
      if farmBtn then farmBtn.scripts.OnClick(farmBtn) end
      ck(adv.farm and adv.farm.item, "Farm on a row farms that piece")
      T.window:Refresh()
      ck(btnStop.shown, "Stop farming shows while farming")
      local status = findText("^Farming ")
      ck(status, "the status line shows the farming")
      btnStop.scripts.OnClick(btnStop)
      ck(not adv.farm, "Stop farming stops")
      T.window:Refresh()
      ck(not btnStop.shown, "Stop farming hides")
      -- the zone tooltip and status texts are plain English without exclamation marks
      local lines = T:AdvZoneSummary(dm)
      ck(#lines >= 4, "zone summary lines")
      for _, l in ipairs(lines) do ck(not l:find("!", 1, true), "no exclamation marks: " .. l) end
      -- the 12/12 case: cleared and waiting for the next zone's level
      local sfk, bfd = tierOf("sfk"), tierOf("bfd")
      adv.tier, adv.stage, adv.auto = sfk, 12, true
      adv.best = math.max(adv.best, T.AdvStageCode(sfk, 12))
      T:CD().level = 19
      local s2 = T:AdvStatusText()
      ck(s2 == "Shadowfang Keep cleared. Next: Blackfathom Deeps opens at level 22 (your cat is 19). Farming here until then.", "cleared status: " .. s2)
      ------------------------------------------------ review fixes
      -- every farmable piece has a floor (1 in 5,000 kills) and no chance reads "0.00%"
      local lowest = 1
      for ti2 = 1, #T.TIERS do
        for bi2 = 1, #T.TIERS[ti2].bosses do
          local l2, tot2 = T:AdvFarmTable(ti2, bi2, cls)
          ck(tot2 <= F.TOTAL_MAX + 1e-9, "total capped with the floor: " .. T.TIERS[ti2].name .. " " .. bi2)
          for _, e2 in ipairs(l2) do lowest = math.min(lowest, e2[2]); ck(T.AdvPct(e2[2]) ~= "0.00%", "no 0.00%: " .. e2[1].name) end
        end
      end
      ck(lowest >= F.ITEM_MIN - 1e-12, "the rarest farmable piece is at least 1 in 5,000 kills: " .. lowest)
      ck(T.AdvPct(0.00001) == "under 0.01%" and T.AdvPct(0.0002) == "0.02%", "AdvPct for tiny chances: " .. T.AdvPct(0.00001))
      -- a and an
      local el = tierOf("elwynn")
      adv.cleared[T.AdvStageCode(el, T:AdvStages(el))] = nil
      local zl = table.concat(T:AdvZoneSummary(el), " / ")
      ck(zl:find("and an Adventurer's Strongbox.", 1, true) and not zl:find(" a Adventurer", 1, true), "an Adventurer's Strongbox: " .. zl)
      -- a first kill made while farming counts, and stops the farm when it is the wanted piece
      adv.cleared[T.AdvStageCode(dm, 12)] = true
      adv.best = math.max(adv.best, T.AdvStageCode(dm, 12))
      local want3 = T:AdvFarmTable(dm, 3, cls)[1]
      if want3 then
        adv.cleared[T.AdvStageCode(dm, 6)] = nil
        ck(T:AdvStartFarm(dm, 3, want3[1].id), "farming a boss not beaten yet")
        local R = T.ADV_FIRST.early
        local savedChance = R.chance
        R.chance = 0   -- no Pouches, so the test runs only the gear part
        -- beat the boss for the first time again and again until its first-kill piece is the wanted one
        for tries = 1, 200 do
          if not adv.farm then break end
          adv.cleared[T.AdvStageCode(dm, 6)] = nil
          adv.stage = 6
          T:AdvMobKilled({ name = T.TIERS[dm].bosses[3][1], boss = 3, level = 20 })
          if adv.farm then ck(adv.farm.kills == tries, "first kills while farming count: " .. adv.farm.kills .. " of " .. tries) end
        end
        R.chance = savedChance
        ck(not adv.farm, "a wanted piece from a first kill stops the farm")
      end
      -- turning Auto-advance on ends farming at once and keeps Auto-advance on
      T:AdvStartFarm(dm, 6, nil)
      adv.auto = true
      ck(not T:AdvStatusText():find("^Farming"), "the status stops saying Farming once Auto-advance is on")
      T:AdvFarmCheckAuto()
      ck(not adv.farm and adv.auto == true, "Auto-advance on ends farming and stays on")
      -- the Compendium's first-kill line follows the zone's band
      local piece = T:AdvFarmTable(dm, 6, cls)[1]
      if piece then
        local how2 = table.concat(T:HowToGet(piece[1]), " / ")
        ck(how2:find("The first time your cat beats Edwin VanCleef it gives a piece of its loot", 1, true)
          and not how2:find("always drops a piece of its own loot", 1, true), "Compendium first-kill line: " .. how2)
      end
      local cs = table.concat(T.CHEST_SOURCES, " / ")
      ck(cs:find("first kills of Adventure bosses in dungeons from level 45", 1, true), "chest sources mention first kills: " .. cs)
      -- the guide: the 3-loss drop-back is with Auto-advance off
      local gt
      for _, f in ipairs(_frames) do if f.kind == "FontString" and type(f.text) == "string" and f.text:find("Auto%-advance on") then gt = f.text end end
      ck(gt and gt:find("If it loses, it drops back to the last trash pack", 1, true)
        and gt:find("Auto%-advance off|r: your cat stays on its stage and farms it%. After 3 losses in a row"), "guide's Auto-advance text: " .. tostring(gt))
      return table.concat(bad, "; ")
    ''')
    if r:
        raise AssertionError("adventure rewards: " + r)
    # measured farming pace: a geared level 24 warrior and mage farming Edwin VanCleef
    pace = []
    for cls in ("WARRIOR", "MAGE"):
        lua2 = load_addon()
        lua2.execute("_seed = %d; math.randomseed(_seed)" % seed)
        out = lua2.execute(r'''
          local T = TapCatForever
          local cls = "%s"
          T:SetClass(cls)
          local c = T:CD(); c.level = 24
          for i = 1, 300 do
            local it = T:RollWorldLoot(24, cls, { 60, 35, 5 })
            if it then T:Bag(cls)[it.id] = (T:Bag(cls)[it.id] or 0) + 1 end
          end
          T:EquipBestGear(cls)
          local dm; for i, t in ipairs(T.TIERS) do if t.key == "dm" then dm = i end end
          c.adv.best = T.AdvStageCode(dm, 12)
          for s = 1, 12 do c.adv.cleared[T.AdvStageCode(dm, s)] = true end
          T:AdvReset()
          T:AdvStartFarm(dm, 6, nil)
          local kb = TapCatForeverKeyListener
          local t, acc = 0, 0
          while t < 1800 do
            _clock = _clock + 0.25; t = t + 0.25
            T:AdvTick(0.25)
            acc = acc + 1.5 * 0.25
            while acc >= 1 do kb.scripts.OnKeyDown(kb, "Q"); acc = acc - 1 end
          end
          local perHour = c.adv.farm.kills * 2
          local list, total = T:AdvFarmTable(dm, 6, cls)
          local parts = {}
          for _, e in ipairs(list) do parts[#parts + 1] = string.format("%%s %%s (%%.1f h)", e[1].name, T.AdvPct(e[2]), 1 / (e[2] * perHour)) end
          return string.format("%%s %%d kills/h: %%s", cls, perHour, table.concat(parts, ", "))
        ''' % cls)
        pace.append(out)
    print("adventure rewards section (%s; farming VanCleef: %s): all checks passed" % (lua.globals()._advFirst, "; ".join(pace)))
