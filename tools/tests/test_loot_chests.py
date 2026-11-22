# 1.5.4 loot track A: chests belong to each class's cat and are stamped with the level of the cat
# that earned them; a chest holds gear for its stamp. Old saves move once to the current cat.
def check(seed, load_addon):
    # 1. migration: a 1.5.3 save with chests in db.keys (one bag per character)
    lua = load_addon(login=False)
    lua.execute("math.randomseed(%d)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      TapCatForeverDB = { charsMigrated = true, version = 3, chars = { ["Kittyhawk-Forever"] = {
        class = "MAGE", keys = { pouch = 3, strong = 1, heroic = 0, raid = 2, dungeon = 1 },
        classData = { MAGE = { level = 22, xp = 0 }, WARRIOR = { level = 7, xp = 0 } }, started = true } } }
      _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")
      local p = {}
      local function ck(c, m) if not c then p[#p + 1] = m end end
      ck(T:ChestsOf("pouch", "MAGE") == 3 and T:ChestsOf("raid", "MAGE") == 2 and T:ChestCount("MAGE") == 7, "old chests go to the Mage: " .. T:ChestCount("MAGE"))
      ck(T:ChestCount("WARRIOR") == 0, "none to the Warrior")
      local st = T:ChestStamps("pouch", "MAGE")
      ck(#st == 1 and st[1].level == 22 and st[1].n == 3, "stamped with the Mage's level")
      ck(T.db.keys.pouch == 3 and T.db.keys.heroic == 0, "db.keys reads the current cat")
      -- a second load of the same save moves nothing again
      local char = TapCatForeverDB.chars["Kittyhawk-Forever"]
      local raw = 0
      for _ in pairs(char.keys) do raw = raw + 1 end
      ck(raw == 0, "db.keys keeps no counts of its own (saved as an empty table)")
      char.keys = {}   -- what the save holds after a reload
      T:InitDB()
      ck(T:ChestCount("MAGE") == 7, "reload: still 7, not doubled: " .. T:ChestCount("MAGE"))
      -- a 1.5.3 install that had no chests at all
      char.keys = { pouch = 0, strong = 0, heroic = 0, raid = 0 }
      T:InitDB()
      ck(T:ChestCount("MAGE") == 7, "zero counts move nothing")
      return table.concat(p, "\n")
    ''')
    if r:
        raise AssertionError("loot chests migration:\n" + r)

    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local p = {}
      local function ck(c, m) if not c then p[#p + 1] = m end end
      local print0, refresh0 = T.Print, T.RefreshAll
      T.RefreshAll = function() end
      -- 2. per cat: earned while playing a class goes to that cat
      T:SetClass("MAGE"); T:CD("MAGE").level = 20
      for _, ch in ipairs(T.CHESTS) do T.db.keys[ch.key] = 0 end
      T:AwardChest("strong", "Test")
      ck(T:ChestsOf("strong", "MAGE") == 1 and T.db.keys.strong == 1, "the Mage's Strongbox")
      T:SetClass("WARRIOR"); T:CD("WARRIOR").level = 5
      ck(T.db.keys.strong == 0 and T:ChestCount() == 0, "the Warrior's bag is its own")
      T:AwardChest("pouch", "Test")
      T:AwardChest("pouch", "Test", nil, "MAGE")   -- a chest for another cat
      ck(T:ChestsOf("pouch", "WARRIOR") == 1 and T:ChestsOf("pouch", "MAGE") == 1, "explicit class")
      ck(T:ChestStamps("pouch", "MAGE")[1].level == 20 and T:ChestStamps("pouch", "WARRIOR")[1].level == 5, "each stamped with its own cat's level")
      -- level-up chests go to the cat that levelled (expedition XP while playing another cat)
      local mage = T:CD("MAGE"); mage.level = 24; mage.xp = 0
      T.db.levelPaid.MAGE = 24
      T:AddClassXP("MAGE", T.XPForLevel(24) + 1)
      local st = T:ChestStamps("strong", "MAGE")
      ck(mage.level == 25 and st[1].level == 25, "level 25 Strongbox for the Mage, stamped 25")
      ck(T:ChestsOf("strong", "WARRIOR") == 0, "not in the Warrior's bag")
      -- the chat line names the other cat
      local line
      T.Print = function(_, m) line = m end
      T:AwardChest("heroic", "Expedition", nil, "MAGE")
      T.Print = print0
      ck(line and line:find("your Mage cat earned", 1, true) and line:find("(level 25)", 1, true) and not line:find("!", 1, true), "chat: " .. tostring(line))
      -- 3. a professions helper of another cat (TCF:WithTradeClass) fills that cat's bag
      T:WithTradeClass("MAGE", function(self) self.db.keys.dungeon = (self.db.keys.dungeon or 0) + 1; self:AwardChest("dungeon", "Spot") end)
      ck(T:ChestsOf("dungeon", "MAGE") == 2 and T:ChestsOf("dungeon", "WARRIOR") == 0, "trade chests: " .. T:ChestsOf("dungeon", "MAGE"))
      -- 4. expeditions: the cat you play if it went, else the party's first cat
      local st0 = T.db.expeditions or { active = {} }
      T.db.expeditions = st0; st0.active = st0.active or {}
      local e = T.EXPEDITIONS[1]
      local saved = e.chest[2]; e.chest[2] = 1
      table.insert(st0.active, { key = e.key, members = { "ROGUE", "MAGE", "PRIEST" }, start = 0, finish = 0, power = 1, chance = 1 })
      local before = T:ChestsOf(e.chest[1], "ROGUE")
      T:ClaimExpedition(#st0.active)
      ck(T:ChestsOf(e.chest[1], "ROGUE") >= before + 1, "expedition chest to the party's first cat")
      table.insert(st0.active, { key = e.key, members = { "ROGUE", "WARRIOR", "PRIEST" }, start = 0, finish = 0, power = 1, chance = 1 })
      before = T:ChestsOf(e.chest[1], "WARRIOR")
      T:ClaimExpedition(#st0.active)
      ck(T:ChestsOf(e.chest[1], "WARRIOR") >= before + 1, "expedition chest to the cat you play when it went")
      e.chest[2] = saved
      ck(T.chestOwner == nil, "owner cleared")
      -- 5. opening uses the stamp: a level 5 pouch opened by a level 60 cat holds low gear
      T:SetClass("WARRIOR")
      for _, ch in ipairs(T.CHESTS) do T.db.keys[ch.key] = 0 end
      local w = T:CD("WARRIOR"); w.level = 5
      for i = 1, 30 do T:AwardChest("pouch", "Test") end
      w.level = 60
      T.lastStamp = nil
      local over = 0
      for i = 1, 30 do
        T:OpenChest("pouch", true)
        local g = T.lastChest and T.lastChest.gear
        if g and (g.req or 0) > 8 then over = over + 1 end
        ck(T.lastChest and T.lastChest.stamp == 5, "stamp on lastChest")
      end
      ck(over == 0 and T.db.keys.pouch == 0, "a level 5 pouch holds level 5 gear: " .. over)
      ck(T.openStamp == nil, "stamp cleared after opening")
      -- a bought chest is for the cat's level now
      T.db.coins = 100000
      T:OpenChest("pouch")
      ck(T.lastChest and T.lastChest.stamp == 60, "bought: stamped 60")
      -- Open picks the level asked for, then the last opened, then the highest
      T:AwardChest("strong", "T", nil, nil, 10); T:AwardChest("strong", "T", nil, nil, 30); T:AwardChest("strong", "T", nil, nil, 30)
      T.lastStamp = nil
      T:OpenChest("strong", true, 10); ck(T.lastChest.stamp == 10, "asked level")
      T:OpenChest("strong", true); ck(T.lastChest.stamp == 30, "highest when the last level is gone")
      -- 6. the Treasure Bag: a row per kind and level, paging, tooltip, other cats
      for _, lv in ipairs({ 5, 10, 15, 20, 25, 30, 35 }) do T:AwardChest("pouch", "T", nil, nil, lv) end
      T:AwardChest("pouch", "T", nil, nil, 20)
      if T.bag then T.bag:Hide() end
      T.bag = nil
      local bag = T:CreateBag(); bag:Show(); bag:Refresh()
      local shown = 0
      for _, row in ipairs(bag.rows) do if row:IsShown() then shown = shown + 1 end end
      ck(shown == 5 and bag.next:IsShown() and bag.pageText:GetText() == "1/2", "5 rows, 2 pages: " .. shown .. " " .. tostring(bag.pageText:GetText()))
      local desc = {}
      for _, row in ipairs(bag.rows) do if row:IsShown() then desc[#desc + 1] = row.desc:GetText() end end
      local all = table.concat(desc, " | ")
      ck(all:find("Lv 35 x1", 1, true) and all:find("Lv 20 x2", 1, true), "Lv rows: " .. all)
      bag.scripts.OnMouseWheel(bag, -1)
      ck(bag.page == 2, "the wheel turns the page")
      local tipLines = {}
      local oAdd = GameTooltip.AddLine
      GameTooltip.AddLine = function(_, t) tipLines[#tipLines + 1] = tostring(t) end
      bag.rows[1].scripts.OnEnter(bag.rows[1])
      GameTooltip.AddLine = oAdd
      ck(table.concat(tipLines, "\n"):find("Holds gear for about level", 1, true), "row tooltip: " .. table.concat(tipLines, " / "))
      ck(bag.others:GetText():find("Mage", 1, true), "other cats line: " .. tostring(bag.others:GetText()))
      -- Open on a row opens that level
      bag.page = 1; bag:Refresh()
      local r1 = bag.rows[1]
      local lv1 = r1.level
      local n1 = T:ChestsOf(r1.chest.key)
      r1.open.scripts.OnClick(r1.open)
      ck(T:ChestsOf(r1.chest.key) == n1 - 1 and T.lastChest.stamp == lv1, "row Open opens its level")
      T:OpenAllChests("pouch", 20)
      local left20 = 0
      for _, s in ipairs(T:ChestStamps("pouch")) do if s.level == 20 then left20 = s.n end end
      ck(left20 == 0 and T:ChestsOf("pouch") > 0, "Open all of one level")
      T:OpenAllChests()
      ck(T:ChestCount() == 0 and T:ChestCount("MAGE") > 0, "Open everything empties only this cat's bag")
      if TapCatForeverLootReveal then TapCatForeverLootReveal:Hide() end
      if T.reel then T.reel:Hide(); T.reel.queue = {}; T.reel.pending = {} end
      -- the reel shows gear for the chest's level
      T.db.ui.chestAnim = true
      w.level = 60
      T:AwardChest("dungeon", "T", nil, nil, 12)
      T:OpenChest("dungeon", true)
      ck(T.reel and T.reel.hint:GetText():find("level 12", 1, true), "reel hint: " .. tostring(T.reel and T.reel.hint:GetText()))
      if T.reel then T.reel:Hide(); T.reel.queue = {}; T.reel.pending = {} end
      if TapCatForeverLootReveal then TapCatForeverLootReveal:Hide() end
      T.RefreshAll = refresh0
      return table.concat(p, "\n")
    ''')
    if r:
        raise AssertionError("loot chests:\n" + r)

    # 7. simulation: stamps 5/15/30/50/60 for every chest type (cat at level 60, so only the
    # stamp keeps the gear near the level)
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    res = lua.execute(r'''
      local T = TapCatForever
      local p, rows = {}, {}
      T.Print = function() end; T.RefreshAll = function() end; T.PlaySound = function() end
      T.ShowLootReveal = function() end
      T:SetClass("WARRIOR")
      local cd = T:CD(); cd.level = 60; cd.adv.best = 1900; cd.adv.tier = 19
      local N = 400
      for _, key in ipairs({ "pouch", "strong", "heroic", "dungeon", "raid" }) do
        local ch = T.CHEST_BY_KEY[key]
        for _, stamp in ipairs({ 5, 15, 30, 50, 60 }) do
          local q, cos, sum, hi, n = { 0, 0, 0, 0, 0 }, 0, 0, 0, 0
          for i = 1, N do
            T.openStamp = stamp
            local it = T:OpenChestContents(ch, key)
            T.openStamp = nil
            local g = T.lastChest and T.lastChest.gear
            if g then
              n = n + 1; q[g.q] = q[g.q] + 1
              local req = g.req or 0
              sum = sum + req; hi = math.max(hi, req)
              if req > stamp + 3 and not (stamp >= 55 and req <= 60) then p[#p + 1] = key .. " stamp " .. stamp .. ": " .. g.name .. " req " .. req end
              if g.q >= 5 and stamp < 60 then p[#p + 1] = key .. " stamp " .. stamp .. ": legendary" end
            else cos = cos + 1 end
          end
          local function pc(x) return string.format("%4.1f", x * 100 / N) end
          rows[#rows + 1] = string.format("  %-7s Lv %2d: req avg %4.1f max %2d | Unc %s Rare %s Epic %s Leg %s Cosmetic %s",
            key, stamp, n > 0 and sum / n or 0, hi, pc(q[2]), pc(q[3]), pc(q[4]), pc(q[5]), pc(cos))
        end
      end
      return table.concat(p, "\n"), table.concat(rows, "\n")
    ''')
    if res[0]:
        raise AssertionError("loot chest stamps:\n" + res[0])
    print("chest stamps (Warrior, 400 chests each; cat at 60, gear by the chest's level):")
    print(res[1])
    print("loot chests section (per-cat bags, level stamps, migration, expedition owner, Treasure Bag rows and pages, reel level, stamps 5-60 for every chest): all checks passed")
