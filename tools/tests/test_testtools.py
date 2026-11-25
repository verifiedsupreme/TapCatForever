# 1.8.0 test tools (TestTools.lua): saved states (save, change things, restore everything back), forcing
# professions and gathering spots open or closed, the quick setters, and none of it outside test mode.

def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      local db = T.db
      -- outside test mode nothing works
      db.ui.testMode = nil
      ck(not T:TestSnapSave(1) and T:TestForced("prof:herbalism") == nil and not T:TestSet("coins1m") and not T:ToggleTestTools(), "test mode only")
      db.ui.testMode = true

      -- saved states: save, change a lot, restore
      db.coins = 1234
      local cd = T:CD(); cd.level = 17
      local s = T:ProfState(); s.gold = 777
      ck(T:TestSnapSave(2) and T:TestSnapInfo(2) and T:TestSnapInfo(2).label:find("level 17", 1, true), "saved in slot 2")
      db.coins = 999999; cd.level = 55; s.gold = 1; db.somethingNew = true
      local reloaded = false
      local realReload = ReloadUI; ReloadUI = function() reloaded = true end
      ck(T:TestSnapLoad(2), "restored")
      ReloadUI = realReload
      local sv = TapCatForeverDB
      ck(reloaded, "the UI reloads")
      ck(sv.coins == 1234 and sv.somethingNew == nil, "TapCoins back, new things gone: " .. tostring(sv.coins))
      ck(sv.ui.testMode == true and rawget(sv, "testSnaps") and rawget(sv, "testSnaps")[2], "test mode stays on, slots kept")
      -- a fresh login on the restored save sees the old cat
      _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")
      db = T.db
      ck(T:CD().level == 17 and T:ProfState().gold == 777, "the cat and its trade are as saved")
      ck(T:TestSnapDelete(2) and not T:TestSnapInfo(2), "deleted")

      -- open or close: professions and spots
      local s2 = T:ProfState(); s2.runEarned = 0; s2.lifetime = 0; s2.announced = {}
      ck(not T:ProfUnlocked("herbalism"), "herbalism closed at the start")
      ck(T:TestCycleForce("prof:herbalism") == true and T:ProfUnlocked("herbalism"), "forced open")
      ck(T:TestCycleForce("prof:herbalism") == false and not T:ProfUnlocked("herbalism"), "forced closed")
      ck(T:TestCycleForce("prof:herbalism") == nil and not T:ProfUnlocked("herbalism"), "back to auto")
      local fam = T:MainProf()
      ck(T:TestCycleForce("spots") == true and T:SpotUnlocked(fam, T:SpotCount()), "every spot open")
      ck(T:TestCycleForce("spots") == false and T:SpotUnlocked(fam, 1) and not T:SpotUnlocked(fam, 2), "only the first spot")
      T:TestClearForces()
      ck(T:TestForced("spots") == nil, "all auto")
      -- forces mean nothing once test mode is off
      T:TestCycleForce("prof:cooking")
      db.ui.testMode = nil
      ck(T:TestForced("prof:cooking") == nil and not T:ProfUnlocked("cooking"), "no forcing outside test mode")
      db.ui.testMode = true

      -- quick setters
      ck(T:TestSet("level60") and T:CD().level == T.MAX_LEVEL, "level 60")
      ck(T:TestSet("level1") and T:CD().level == 1, "level 1")
      ck(T:TestSet("skillmax") and T:ProfState().skill[fam] == 300, "skills 300")
      local craft = T:CraftProf()
      ck(T:TestSet("rankup") and T:GuildRank(craft) == 2, "guild rank up")
      ck(T:TestSet("rankdown") and T:GuildRank(craft) == 1, "guild rank down")
      local rp0 = T:DepthState().rp or 0
      ck(T:TestSet("rp") and T:DepthState().rp == rp0 + 5, "+5 Renown points")
      ck(T:TestSet("bagup") and T:MatBagLevel() == 2 and T:TestSet("bagdown") and T:MatBagLevel() == 1, "bag up and down")
      ck(T:TestSet("advall") and T:CD().adv.best >= T.AdvStageCode(#T.TIERS, 1), "Adventure all open")
      ck(T:TestSet("advreset") and T:CD().adv.best == 0, "Adventure from the start")
      local c0 = db.coins
      ck(T:TestSet("coins1m") and db.coins == c0 + 1000000 and T:TestSet("coins0") and db.coins == 0, "TapCoins")

      -- the window
      ck(T:ToggleTestTools() and T.testTools:IsShown(), "the window opens")
      T.testTools:Refresh()
      T:ToggleTestTools()
      return table.concat(fails, "; ")
    ''')
    assert r == "", "test tools: " + r
    print("test tools section (saved states restore everything, professions and spots forced open or closed, quick setters, test mode only): all checks passed")
