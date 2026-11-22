# 1.5.4 loot track B: a care package for players who played before this update. White pieces
# for every played cat's empty slots (in its bag, not worn), a small TapCoin gift once per account,
# one chat line, never twice, nothing for brand-new characters or accounts.
def check(seed, load_addon):
    lua = load_addon(login=False)
    lua.execute("math.randomseed(%d)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local p = {}
      local function ck(c, m) if not c then p[#p + 1] = m end end
      local function login(name) _charName = name; _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN") end
      -- an old save: the Mage is level 18 with a weapon and a chest piece, the Warrior was never played
      TapCatForeverDB = { charsMigrated = true, version = 3, coins = 1000, chars = { ["Kittyhawk-Forever"] = {
        class = "MAGE", started = true,
        classData = { MAGE = { level = 18, xp = 40, gear = {}, bag = {} }, WARRIOR = { level = 1, xp = 0 } } } } }
      -- (other features may pay TapCoins or chests at login for progress cats already had, such as
      -- class achievements: mark those as earned so only the care package is counted here)
      if T.CLASS_ACHIEVEMENTS then
        TapCatForeverDB.classAch = {}
        for _, cl in ipairs(T.CLASSES) do
          TapCatForeverDB.classAch[cl.key] = {}
          for _, a in ipairs(T.CLASS_ACHIEVEMENTS) do TapCatForeverDB.classAch[cl.key][a.id] = 1 end
        end
      end
      local weapon, chest
      for _, it in ipairs(T.WORLD_POOL[3] or {}) do
        if it.q == 2 and not it.crafted and not it.retired and T:GearUsable(it, "MAGE") then
          if not weapon and it.slot == "2H" then weapon = it end
          if not chest and it.slot == "CHEST" then chest = it end
        end
      end
      local mcd = TapCatForeverDB.chars["Kittyhawk-Forever"].classData.MAGE
      mcd.gear.MAINHAND, mcd.gear.CHEST = weapon.id, chest.id
      mcd.bag[weapon.id], mcd.bag[chest.id] = 1, 1
      local chat0 = #_chat
      login("Kittyhawk")
      -- (the daily treat comes on top)
      ck(T.db.coins >= 1000 + T.CARE_COINS and T.db.coins < 1000 + T.CARE_COINS + 60, "150 TapCoins once per account: " .. T.db.coins)
      local whites, worn = 0, 0
      local eq = T:GearEquipped("MAGE")
      for id, n in pairs(T:Bag("MAGE")) do
        local it = T.GEAR[id]
        if it and it.q == 1 then
          whites = whites + n
          ck((it.req or 0) <= 18, "wearable at 18: " .. it.name .. " " .. (it.req or 0))
          ck(T:GearUsable(it, "MAGE"), "a Mage can use " .. it.name)
          ck(it.sub ~= "plate" and it.sub ~= "mail" and it.sub ~= "leather", "cloth for a Mage: " .. it.name)
          for _, v in pairs(eq) do if v == id then worn = worn + 1 end end
        end
      end
      ck(whites >= 6, "the Mage got whites for its empty slots: " .. whites)
      ck(worn == 0, "not equipped")
      ck(eq.MAINHAND == weapon.id and eq.CHEST == chest.id, "worn gear unchanged")
      local newMain = false
      for id in pairs(T:Bag("MAGE")) do local it = T.GEAR[id]; if it and it.q == 1 and (it.slot == "MH" or it.slot == "1H" or it.slot == "2H" or it.slot == "CHEST") then newMain = true end end
      ck(not newMain, "nothing for filled slots (main hand, chest)")
      local wbag = 0
      for id, n in pairs(T:Bag("WARRIOR")) do local it = T.GEAR[id]; if it and it.q == 1 then wbag = wbag + n end end
      ck(wbag == 0, "a cat that was never played gets nothing: " .. wbag)
      local lines = {}
      for i = chat0 + 1, #_chat do if _chat[i]:find("care package", 1, true) then lines[#lines + 1] = _chat[i] end end
      ck(#lines == 1 and not lines[1]:find("!", 1, true) and lines[1]:find("Mage " .. whites, 1, true) and lines[1]:find("150 TapCoins", 1, true)
        and lines[1]:find("your cat's empty gear slots", 1, true) and lines[1]:find("in its gear bag", 1, true), "one chat line: " .. table.concat(lines, " / "))
      -- a pop-up never: the loot box stays hidden
      ck(not (TapCatForeverLootReveal and TapCatForeverLootReveal:IsShown()), "no loot box")
      -- logging in again gives nothing
      local coins = T.db.coins
      login("Kittyhawk")
      local whites2 = 0
      for id, n in pairs(T:Bag("MAGE")) do local it = T.GEAR[id]; if it and it.q == 1 then whites2 = whites2 + n end end
      ck(T.db.coins == coins and whites2 == whites, "never twice")
      -- a brand-new character on this account: nothing (the account gift is already paid)
      login("Newalt")
      local any = 0
      for _, cl in ipairs(T.CLASSES) do for id in pairs(T:Bag(cl.key)) do local it = T.GEAR[id]; if it and it.q == 1 then any = any + 1 end end end
      ck(any == 0 and T.db.coins == coins, "a new character gets nothing")
      -- an old character on this account that logs in later gets its gear, not more coins
      TapCatForeverDB.chars["Oldwar-Forever"] = { class = "WARRIOR", started = true, classData = { WARRIOR = { level = 30, xp = 0 } } }
      login("Oldwar")
      local wwhites, heavy = 0, 0
      for id, n in pairs(T:Bag("WARRIOR")) do
        local it = T.GEAR[id]
        if it and it.q == 1 then
          wwhites = wwhites + n
          if it.sub == "mail" or it.sub == "plate" then heavy = heavy + 1 end
        end
      end
      ck(wwhites >= 8 and T.db.coins == coins, "the old Warrior's pieces: " .. wwhites .. ", coins " .. T.db.coins)
      -- (whites are mostly cloth in Classic; a Warrior still gets mail or plate where there is any)
      ck(heavy >= 4, "mostly mail or plate for a Warrior: " .. heavy)
      return table.concat(p, "\n")
    ''')
    if r:
        raise AssertionError("loot care package:\n" + r)
    # a brand-new account: nothing at all
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      local n = 0
      for i = 1, #_chat do if _chat[i]:find("care package", 1, true) then n = n + 1 end end
      return n, T.db.coins, T.db.careCoins and true or false, T.charData.carePackage and true or false
    ''')
    r = tuple(r)
    if not (r[0] == 0 and r[1] < 100 and r[2] and r[3]):   # (only the daily treat)
        raise AssertionError("loot care package: a new account got something %r" % (tuple(r),))
    print("loot care package section (old cats get whites for empty slots in their bags, 150 TapCoins once per account, one chat line, never twice, nothing for new characters or accounts): all checks passed")
