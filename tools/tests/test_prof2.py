# 1.7.0 Professions 2.0: rare finds by hand (never by helpers), glints (x5, combo, rare chance), spot
# events (stash, rich spot, patrol), named helpers that level, specializations at 225 with daily crafts,
# guild reputation and work orders, Masterwork gear (suffix 99 id), the Renown shop, titles, and the
# long-chase set recipes (spec, rank, daily materials, rare finds) with the set title.

def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      T:SetClass("MAGE")
      local s = T:ProfState()
      s.gold, s.lifetime = 1e12, 1e17
      local fam = T:MainProf()
      ck(fam == "cloth", "a Mage gathers cloth")
      for i = 1, 6 do T:BuyOp(fam, i, 10) end

      -- rare finds: by hand only, from the right spots
      ck(#T.RareFindsAt("cloth", 1) == 0 and #T.RareFindsAt("cloth", 2) == 1 and #T.RareFindsAt("cloth", 7) == 3, "finds by spot")
      local keep = T.RARE_FIND_CHANCE
      T.RARE_FIND_CHANCE = 1
      T.toolNext = {}
      local before = (s.mats.essundeath or 0) + (s.mats.demonicrune or 0)
      ck(T:GatherClick(fam, 3), "a click by hand")
      ck((s.mats.essundeath or 0) + (s.mats.demonicrune or 0) == before + 1, "a click by hand with a sure chance finds one")
      T.RARE_FIND_CHANCE = keep
      -- helpers never find them
      T:HireForeman(fam, 3)
      local r0 = (s.mats.essundeath or 0) + (s.mats.demonicrune or 0)
      T.RARE_FIND_CHANCE = 1
      T:ProfAdvance(3600)
      ck((s.mats.essundeath or 0) + (s.mats.demonicrune or 0) == r0, "helpers never find rare things")
      T.RARE_FIND_CHANCE = keep

      -- named helpers: a name, a trait, levels from work, faster with levels
      local h = T:HelperInfo(fam, 3)
      ck(h and h.name and h.trait and h.level >= 1, "the helper has a name and a trait")
      s.ops[fam][3].hxp = 0
      ck(T:HelperInfo(fam, 3).level == 1, "a new helper is level 1")
      local sp0, g0m = T:OpSpeedMult(fam, 3), T:HelperGoodsMult(fam, 3)
      s.ops[fam][3].hxp = 25 * 81    -- level 10
      ck(T:HelperInfo(fam, 3).level == 10, "level from cycles worked")
      ck(T:HelperGoodsMult(fam, 3) > g0m * 1.15 and T:OpSpeedMult(fam, 3) == sp0, "a level 10 helper brings more goods, gold stays the same")

      -- glints: x5, combo, a missed one ends the combo
      T.WorkshopTest.reset()
      T.WorkshopTest.setGlint({ fam = fam, i = 2, ends = GetTime() + 5 })
      T.toolNext = {}
      local g0 = s.gold
      local base = T:ToolGold(fam, 2)
      T:GatherClick(fam, 2)
      local paid = s.gold - g0
      ck(paid >= base * 4.5, "a glint pays 5 times as much (" .. paid .. " vs " .. base .. ")")
      ck(T:WorkshopCombo() == 1 and not T:WorkshopGlint(), "combo 1, the glint is used")
      ck(T:RareFindChance(fam, 2) > T.RARE_FIND_CHANCE, "a combo makes rare finds likelier")
      T.WorkshopTest.setGlint({ fam = fam, i = 2, ends = GetTime() - 1 })
      T:WorkshopTick({ 1, 2, 3, 4, 5, 6 })
      ck(T:WorkshopCombo() == 0, "a missed glint ends the combo")
      -- glints appear on their own while the page is open
      T.WorkshopTest.reset()
      T:WorkshopTick({ 1, 2, 3, 4, 5, 6 })
      ck(not T:WorkshopGlint(), "no glint right away")
      _clock = _clock + 30
      T:WorkshopTick({ 1, 2, 3, 4, 5, 6 })
      ck(T:WorkshopGlint(), "a glint appears after a while")

      -- events: stash (10 quick clicks), rich spot (x3), patrol (hide: helpers x2)
      T.WorkshopTest.reset()
      T.WorkshopTest.setEvent({ kind = "stash", fam = fam, i = 2, ends = GetTime() + 8, clicks = 0 })
      local gs = s.gold
      for k = 1, 10 do T:WorkshopRowClick(fam, 2) end
      ck(s.gold > gs and not T:WorkshopEvent(), "the stash is grabbed with 10 clicks")
      T.WorkshopTest.setEvent({ kind = "rich", fam = fam, i = 4, ends = GetTime() + 30 })
      T.toolNext = {}
      local g1 = s.gold
      T:GatherClick(fam, 4)
      ck(s.gold - g1 >= T:ToolGold(fam, 4) * 2.5, "a rich spot pays 3 times as much")
      T.WorkshopTest.setEvent({ kind = "patrol", fam = fam, ends = GetTime() + 0.1 })
      local spBefore = T:OpSpeedMult(fam, 3)
      _clock = _clock + 1
      T:WorkshopTick({ 1, 2, 3 })
      ck(T:WorkshopBuffLeft(fam) > 50 and math.abs(T:OpSpeedMult(fam, 3) - spBefore * 2) < 1e-6, "hidden from the patrol: helpers twice as fast")
      T.WorkshopTest.setEvent({ kind = "patrol", fam = fam, ends = GetTime() + 5 })
      T:WorkshopRowClick(fam, 1)
      ck(not T:WorkshopEvent(), "clicking during a patrol: spotted")

      -- specializations at 225, daily crafts
      local craft = T:CraftProf()
      s.skill[craft] = 200
      ck(not T:ChooseSpec("mooncloth"), "no specialization before 225")
      s.skill[craft] = 230
      ck(T:ChooseSpec("mooncloth") and T:Spec().key == "mooncloth", "Mooncloth Tailoring")
      ck(not T:ChooseSpec("blacksmithing"), "an unknown key does nothing")
      s.mats.mooncloth, s.mats.runecloth = 10, 100
      ck(T:DailyCraft() and s.mats.primalmooncloth == 2, "the daily craft makes two Primal Mooncloth (Mooncloth perk)")
      ck(not T:DailyCraft() and T:DailyReadyIn() > 19 * 3600, "once every 20 hours")
      local coins = T.db.coins
      T.db.coins = 1000
      ck(T:ChooseSpec("spellfire") and T.db.coins == 500, "changing costs 500 TapCoins")
      ck(T:DailyHours() == 16, "Spellfire: ready 4 hours sooner")

      -- guild reputation and ranks, work orders
      ck(T:GuildRank() == 1, "Initiate to start")
      local orders = T:WorkOrders()
      ck(#orders == 3, "three orders: " .. #orders)
      local o = orders[1]
      if o.kind == "gear" then T:GrantGear(T.GEAR[o.key], "test"); for k = 2, o.n do T:GrantGear(T.GEAR[o.key], "test") end
      else s.mats[o.key] = (s.mats[o.key] or 0) + o.n end
      local rep0 = T:GuildRep()
      ck(T:FillOrder(o.id), "an order filled")
      ck(T:GuildRep() == rep0 + o.rep and #T:WorkOrders() == 2, "reputation, and the slot waits for a new order")
      -- (1.8.0) orders never ask for more than the bag holds; part of one can be delivered
      local fam = T:MainProf()
      local key = T.FAMILIES[fam].ops[1][2]
      local cap = T:OrderMatCap(key)
      ck(cap and cap <= T:MatCapFor(key), "an order fits the bag: " .. tostring(cap))
      local big = { kind = "mat", key = key, n = 891460, who = "a Ratchet bruiser", rep = 140, gold = 1000, coins = 0, id = 9001, expires = time() + 3600 }
      local d = T:DepthState(); local list = d.orders[craft]
      list[#list + 1] = big
      T:WorkOrders()
      ck(big.n == cap, "an old order bigger than the bag asks for what fits: " .. big.n)
      s.mats[key] = math.floor(cap / 2)
      local rep1 = T:GuildRep()
      local ok, part = T:FillOrder(9001)
      ck(ok and part == "partial" and big.got == math.floor(cap / 2) and (s.mats[key] or 0) == 0 and T:GuildRep() == rep1, "half delivered, no reward yet")
      ck(not T:FillOrder(9001), "nothing more to deliver")
      s.mats[key] = cap
      ck(T:FillOrder(9001) and T:GuildRep() == rep1 + 140 and s.mats[key] == cap - (cap - math.floor(cap / 2)), "the rest delivered: the reward, and the extra stays in the bag")
      _clock = _clock + 1
      local tnow = time
      local off = 0
      time = function() return tnow() + off end
      off = 16 * 60
      ck(#T:WorkOrders() == 3, "a new order after a while")
      T:AddGuildRep(craft, 30000)
      ck(T:GuildRank() == 7 and T.db.titles["Grand Master Tailor"], "Grand Master and its title")
      time = tnow

      -- Masterwork: a better version of crafted gear, id in the suffix scheme
      local rec
      for _, rr in ipairs(T.RECIPES[craft]) do if rr.gear and not rr.starter then rec = rr; break end end
      local mw = T.MasterworkGear(rec.gear)
      ck(mw and mw.id == T.SUFFIX_ID_BASE + rec.gear * 100 + 99 and mw.name:find("^Masterwork "), "a Masterwork id and name")
      ck(T.GearModelId(mw.id) == rec.gear, "older versions see the base item")
      local bs, ms = T.GearStats(T.GEAR[rec.gear]), T.GearStats(mw)
      local better = true
      for k, v in pairs(bs) do if k ~= "spd" and (ms[k] or 0) < v then better = false end end
      ck(better and (mw.q or 0) >= (T.GEAR[rec.gear].q or 0), "Masterwork stats and quality are better")
      T.MASTERWORK_CHANCE = 1
      for m, n in pairs(rec.mats) do s.mats[m] = n end
      s.skill[craft] = 300
      local bag = T:Bag()
      ck(T:Craft(rec) and (bag[mw.id] or 0) >= 1, "a craft can come out Masterwork")
      T.MASTERWORK_CHANCE = 0.05

      -- Renown shop: points from selling, perks that work and stay
      local d = T:DepthState()
      d.rp = 0
      T:AddRenownPoints(30)
      ck(T:BuyRenownPerk("sharptools") and T:RenownPerk("sharptools") == 1 and T:RenownPoints() == 20, "Sharp Tools rank 1")
      ck(not T:BuyRenownPerk("rested"), "Rested Hands needs 100 points")
      T:AddRenownPoints(200)
      T:BuyRenownPerk("orders")
      ck(T:OrderSlots() == 4, "Guild Ties: a fourth order slot")
      local rp = T:RenownPoints()
      s.lifetime = 1e18; s.gold = 1e15
      T:PrestigeTrade()
      ck(T:RenownPoints() > rp and T:RenownPerk("sharptools") == 1, "selling gives points and keeps the perks")

      -- titles: cycle through earned ones
      T.db.titles = { ["Moonweaver"] = true }; T.db.titleSel = nil
      local lvlTitle = T:GetTitle()
      ck(T:CycleTitle() and T:GetTitle() == "Moonweaver", "show an earned title")
      T:CycleTitle()
      ck(T:GetTitle() == lvlTitle, "and back to the level title")

      -- the long-chase recipes: a crafted set gets recipes needing spec, rank, daily materials, rare finds
      T.AddCosmeticSet({ key = "zzt", name = "Test Regalia", prof = "tailoring", spec = "mooncloth", title = "Test Weaver", vec = {},
        pieces = { { id = "set_zzt_head", slot = "head", art = "zzt_head", name = "Test Crown", rarity = 5, icon = "INV_Crown_01" },
                   { id = "set_zzt_aura", slot = "effect", art = "zzt_aura", name = "Test Aura", rarity = 5, icon = "Spell_Holy_Halo", fx = { layer = "back", anim = "pulse" } } } })
      T.ProfSetsAddRecipes()
      local head, aura
      for _, rr in ipairs(T.RECIPES.tailoring) do
        if rr.item == "set_zzt_head" then head = rr elseif rr.item == "set_zzt_aura" then aura = rr end
      end
      ck(head and aura, "recipes for the set's pieces")
      ck(head and head.spec == "mooncloth" and head.rank == 6 and head.mats.primalmooncloth == 10 and head.mats.righteousorb == 4, "the crown needs Master, 10 Primal Mooncloth, 4 Righteous Orbs")
      ck(aura and aura.rank == 7 and aura.mats.essundeath == 10, "the aura needs Grand Master and many rare finds")
      d.spec.tailoring = "spellfire"
      ck(T:CraftBlocked(head) and T:CraftBlocked(head):find("Mooncloth", 1, true), "needs the Mooncloth specialization")
      d.spec.tailoring = "mooncloth"
      d.rep.tailoring = 7000
      ck(T:CraftBlocked(head) and T:CraftBlocked(head):find("Master", 1, true), "needs Master with the guild")
      d.rep.tailoring = 40000
      for _, rr in ipairs({ head, aura }) do for m, n in pairs(rr.mats) do s.mats[m] = (s.mats[m] or 0) + n end end
      ck(T:Craft(head) and T:Craft(aura), "both pieces crafted")
      ck(T.db.titles["Test Weaver"], "the whole set gives its title")
      local lines = table.concat(T:HowToGet(T.ITEMS.set_zzt_head), " | ")
      ck(lines:find("Crafted", 1, true) and lines:find("Primal Mooncloth", 1, true) and lines:find("Test Regalia set", 1, true), "how to get it: " .. lines)
      -- gathering skill: a third as fast, reset on a sale (the best is kept for the later spots), cut once in 1.7.0
      local sk = T:ProfState()
      sk.skill.cloth = 100; sk.gatherCut170 = nil; sk.skillBest = nil
      T:ProfAdvance(0.01)
      ck(sk.skill.cloth == 33 and sk.skillBest.cloth == 100, "1.7.0 keeps a third of gathering skill: " .. tostring(sk.skill.cloth))
      local ups, n = 0, 3000
      for k = 1, n do sk.skill.cloth = 50; if T:ProfSkillUp("cloth", 50) then ups = ups + 1 end end
      ck(ups > n * 0.25 and ups < n * 0.42, "a 'always' gathering skill-up now comes a third of the time: " .. ups)
      local cups = 0
      for k = 1, 600 do sk.skill.tailoring = 50; if T:ProfSkillUp("tailoring", 50) then cups = cups + 1 end end
      ck(cups == 600, "crafting skill-ups are unchanged")
      -- professions open with this run's Trade Gold
      sk.skill.cloth = 120
      sk.gold, sk.lifetime, sk.runEarned = 1e15, 1e20, 2e9
      ck(T:ProfUnlocked("herbalism") and not T:ProfUnlocked("firstaid"), "this run's 2B opens Herbalism only")
      T:PrestigeTrade()
      ck(sk.runEarned == 0 and not T:ProfUnlocked("herbalism") and T:ProfUnlocked("cloth"), "a sale closes Herbalism again (the main profession stays)")
      ck((sk.skill.cloth or 1) == 1 and sk.skillBest.cloth >= 120, "a sale resets gathering skill and keeps the best")
      T:EarnGold(2e9)
      ck(T:ProfUnlocked("herbalism"), "earned back: open again")
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("professions 2.0: " + r)
    print("professions 2.0 section (rare finds by hand only, named helpers that level, glints x5 and combos, stash, rich spot and patrol events, "
          "specializations with daily crafts, guild ranks and work orders, Masterwork gear, the Renown shop, titles, long-chase set recipes and the set title): all checks passed")
