# 1.6.0: "can you make it to where progress carries over between wow characters?" The nine class
# cats belong to the account (AccountCats.lua): any character of a class plays the account's cat.
# Checks, with a 1.5.x save of three characters (two Mages, one Hunter that also has a Mage):
#   - the merge: the highest level (then most XP) Mage is the base (level, XP, worn gear, look,
#     Adventure place); the others add bag items (their worn gear too), chests, cosmetics, kill
#     counts, first kills, abilities; professions keep the business with the most Trade Gold earned,
#     the best skill per profession and the best Renown, materials added up; expeditions all kept
#   - a backup of every character's old cats, one chat line once, quests keep their progress
#   - a reload changes nothing; every character sees the same cats and what another one did
#   - a brand-new character plays the account's cats; an older save joining later is merged too
#   - per character still: which cat it plays, the Daily Wares, real dungeon limits and the run,
#     real boss kill counts, the professions glitch day
# The save here is made by hand: chests already on the cats (classData[class].chests) and only one
# or two cats per character, so the classes can be told apart. Real 1.5.x saves keep each
# character's chests in chars[name].keys and all nine cats on every character (so after the merge
# every class cat owns every character's cosmetics): that is tools/tests/test_account_real_save.py,
# with a save the 1.5.3.6 release wrote.
# Run on its own:  python3 tools/tests/test_account_cats.py [seed]
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import test_deathroll as TD

def ck(c, m):
    if not c: raise AssertionError("account cats: " + m)

def boot(load_addon, name, db, cls="MAGE"):
    lua = load_addon(login=False)
    lua.execute(TD.CLIENT)
    lua.execute('_charName = "%s"; UnitClass = function() return "%s", "%s" end' % (name, cls.title(), cls))
    lua.execute("TapCatForeverDB = loadstring(%r)()" % ("return " + db))
    lua.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    return lua

# a 1.5.x account: Ann (Mage, level 30), Bob (Mage, level 20, the bigger business), Cid (Hunter 12,
# with a level 30 Mage that has less XP than Ann's)
OLD = r'''
local T = TapCatForever
local today = date("%Y%m%d")
local staff, wand, robe
for _, it in ipairs(T.WORLD_POOL[4] or {}) do
  if it.q == 2 and not it.crafted and not it.retired and T:GearUsable(it, "MAGE") then
    if not staff and it.slot == "2H" then staff = it.id end
    if not wand and it.slot == "RANGED" then wand = it.id end
    if not robe and it.slot == "CHEST" then robe = it.id end
  end
end
_ids = { staff = staff, wand = wand, robe = robe }
local function trade(t)
  t.ops = t.ops or {}; t.upgrades = t.upgrades or {}; t.milestones = t.milestones or {}; t.tools = t.tools or {}
  t.famMoved = true; t.last = time(); t.buy = 1
  return t
end
_old = { charsMigrated = true, version = 3, coins = 5000, careCoins = true,
  quests = { day = today, week = "x", v = 2, weekly = {}, daily = {
    { name = "Monster Hunter", desc = "", counter = "kills", goal = 70, reward = 45, icon = "x", key = "pouch", kind = "daily",
      base = 100, last = 130, char = "Ann-Forever", claimed = false, others = { ["Bob-Forever"] = { base = 10, last = 20 } } } } },
  chars = {
  ["Ann-Forever"] = { class = "MAGE", started = true, carePackage = true, shop = { day = today, rerolls = 0, stock = { "x_ann" }, bought = {} },
    dungeonPaid = { ["party:36"] = time() }, realBosses = { hogger = 2 }, profGlitchDay = today,
    owned = { skin_lion = 1, fur_snow = 1 }, look = { fur = "fur_snow", skin = "skin_lion", tap = "tap_puff", tapSet = true },
    itemSources = { skin_lion = { first = { "Heroic Cache", 2000 }, last = { "Heroic Cache", 2000 } } },
    loadouts = { MAGE = {} },
    expeditions = { active = { { key = "elwynn", members = { "MAGE", "WARRIOR", "PRIEST" }, start = 0, finish = 10, power = 1, chance = 1 } }, done = 3,
      group = { id = "aaaaaa", place = "dm", len = 1, diff = 1, start = 0, finish = 10, seed = 1, players = {}, mine = { "WARRIOR" }, chance = 1 } },
    classData = {
      MAGE = { level = 30, xp = 100, gear = { MAINHAND = staff }, bag = { [staff] = 1, [robe] = 2 }, chests = { pouch = { [30] = 2 } },
        abilities = { fireball = true }, adv = { tier = 5, stage = 3, best = 503, kills = 100, bossKills = 10, cleared = { [501] = true }, newStages = 4 },
        trade = trade({ gold = 50, lifetime = 1000, renown = 2, renownEver = 2, skill = { cloth = 100, tailoring = 50 }, mats = { linen = 10 } }) },
      WARRIOR = { level = 5, xp = 0 } } },
  ["Bob-Forever"] = { class = "MAGE", started = true, carePackage = true, shop = { day = today, rerolls = 0, stock = { "x_bob" }, bought = {} },
    realBosses = { hogger = 7 },
    owned = { skin_frostsaber = 1, skin_lion = 1 }, look = { fur = "fur_ginger", skin = "skin_frostsaber", tap = "tap_puff", tapSet = true },
    loadouts = { MAGE = {} },
    expeditions = { active = { { key = "westfall", members = { "MAGE", "ROGUE", "DRUID" }, start = 0, finish = 10, power = 1, chance = 1 } }, done = 2,
      group = { id = "bbbbbb", place = "dm", len = 1, diff = 1, start = 0, finish = 10, seed = 1, players = {}, mine = { "ROGUE" }, chance = 1 } },
    classData = {
      MAGE = { level = 20, xp = 900, gear = { RANGED = wand }, bag = { [wand] = 1 }, chests = { strong = { [20] = 1 }, pouch = { [18] = 1 } },
        abilities = { frostbolt = true }, adv = { tier = 3, stage = 1, best = 309, kills = 50, bossKills = 5, cleared = { [301] = true }, newStages = 1 },
        trade = trade({ gold = 777, lifetime = 5000, renown = 1, renownEver = 1, skill = { cloth = 50, tailoring = 120 }, mats = { linen = 5, wool = 3 } }) } } },
  ["Cid-Forever"] = { class = "HUNTER", started = true, carePackage = true,
    owned = { skin_diamond = 1 }, look = { fur = "fur_cream", tap = "tap_puff", tapSet = true },
    classData = {
      HUNTER = { level = 12, xp = 0 },
      MAGE = { level = 30, xp = 50, bag = { [robe] = 1 } } } },
} }
-- (class achievements already earned, so the login pays no chests on top of what is merged)
_old.classAch = {}
for _, cl in ipairs(T.CLASSES) do
  _old.classAch[cl.key] = {}
  for _, a in ipairs(T.CLASS_ACHIEVEMENTS) do _old.classAch[cl.key][a.id] = 1 end
end
-- (saves from 1.5.3 on: the XP curve change was already applied)
for _, ch in pairs(_old.chars) do for _, cd in pairs(ch.classData) do cd.xpCurve2 = true end end
'''

def check(seed, load_addon):
    # build the old save in a scratch client
    S = load_addon(login=False)
    S.execute(TD.CLIENT)
    S.execute('_fire("ADDON_LOADED", "TapCatForever")')   # (gear data ready)
    S.execute(OLD)
    old = S.eval("_ser(_old)")
    ids = {k: S.eval("_ids.%s" % k) for k in ("staff", "wand", "robe")}
    ck(all(ids.values()), "test gear found: %r" % ids)

    # --- Ann logs in first on 1.6.0: everything is merged
    A = boot(load_addon, "Ann", old)
    E = lambda e: A.eval(e)
    X = lambda c: A.execute(c)
    X("T = TapCatForever; M = T:CD('MAGE')")
    ck(E("M.level") == 30 and E("M.xp") == 100, "the base Mage is Ann's (level 30, most XP): %r %r" % (E("M.level"), E("M.xp")))
    ck(E("M.gear.MAINHAND") == ids["staff"] and E("M.gear.RANGED == nil"), "the base keeps its worn gear")
    bag = lambda i: E("T:Bag('MAGE')[%d] or 0" % i)
    ck(bag(ids["staff"]) == 1 and bag(ids["wand"]) == 1 and bag(ids["robe"]) == 3, "bags added up, Bob's worn wand in the bag: %r" % [bag(ids[k]) for k in ("staff", "wand", "robe")])
    ck(E("T:ChestsOf('pouch', 'MAGE')") == 3 and E("T:ChestsOf('strong', 'MAGE')") == 1 and E("M.chests.pouch[30]") == 2 and E("M.chests.pouch[18]") == 1,
       "chests added up with their level stamps: %r %r" % (E("T:ChestsOf('pouch', 'MAGE')"), E("T:ChestsOf('strong', 'MAGE')")))
    ck(E("T:Owned('MAGE').skin_lion") == 2 and E("T:Owned('MAGE').skin_frostsaber") == 1 and E("T:Owned('MAGE').skin_diamond") == 1,
       "cosmetics of every character's Mage")
    ck(E("T:Owned('HUNTER').skin_diamond") == 1 and E("T:Owned('HUNTER').skin_frostsaber == nil"), "the Hunter has Cid's cosmetics only (Cid is the only character here with a Hunter)")
    ck(E("M.adv.kills") == 150 and E("M.adv.bossKills") == 15 and E("M.adv.best") == 503 and E("M.adv.tier") == 5
       and E("M.adv.cleared[301] and M.adv.cleared[501]") and E("M.abilities.fireball and M.abilities.frostbolt"),
       "Adventure: Ann's place, kills added, first kills and abilities kept")
    t = "T:ProfState('MAGE')"
    ck(E(t + ".lifetime") == 5000 and E(t + ".gold") == 777, "the business with the most Trade Gold earned (Bob's)")
    ck(E(t + ".skill.cloth") == 100 and E(t + ".skill.tailoring") == 120 and E(t + ".renown") == 2,
       "best skill per profession and best Renown: %r %r %r" % (E(t + ".skill.cloth"), E(t + ".skill.tailoring"), E(t + ".renown")))
    ck(E(t + ".mats.linen") == 15 and E(t + ".mats.wool") == 3, "materials added up")
    ck(E("T:CD('HUNTER').level") == 12 and E("T:CD('WARRIOR').level") == 5, "the other classes")
    ck(E("T:LookOf('MAGE').skin") == "skin_lion" and E("T:LookOf('MAGE').fur") == "fur_snow", "the Mage wears the base cat's look")
    ck(E("T:LookOf('HUNTER').fur") == "fur_cream", "the Hunter wears Cid's look")
    ck(E("#T.db.expeditions.active") == 2 and E("T.db.expeditions.done") == 5 and E("T.db.expeditions.group.id") == "aaaaaa"
       and E("T.db.expeditions.groupQueue[1].id") == "bbbbbb", "every expedition under way is kept")
    ck(E("T:ItemSourceRecord('skin_lion', 'MAGE').first[1]") == "Heroic Cache", "where cosmetics came from is kept")
    ck(E("T:QuestProgress(T.db.quests.daily[1])") == 40, "the kill quest keeps its progress: %r" % E("T:QuestProgress(T.db.quests.daily[1])"))
    for who in ("Ann", "Bob", "Cid"):
        ck(E("TapCatForeverDB.preAccountBackup['%s-Forever'].classData ~= nil" % who), "backup of %s's old cats" % who)
        ck(E("rawget(TapCatForeverDB.chars['%s-Forever'], 'classData') == nil" % who), "%s's cats left the character" % who)
    ck(E("TapCatForeverDB.preAccountBackup['Bob-Forever'].classData.MAGE.level") == 20, "the backup is the untouched old data")
    lines = lambda L: [m for m in L.eval("_chat").values() if "now shared by all your characters" in m]
    ck(len(lines(A)) == 1 and lines(A)[0].endswith("Your cats are now shared by all your characters: each class has one cat, with everything your characters had."),
       "one chat line: %r" % lines(A))
    ck(E("T.db.class") == "MAGE" and E("T.charData.shop.stock[1]") == "x_ann" and E("T:RealBossKills('hogger')") == 2
       and E("T.charData.dungeonPaid['party:36'] ~= nil") and E("T.charData.profGlitchDay ~= nil"), "Ann's own things stay hers")

    # --- a reload: nothing changes, no second line
    X("TapCatForever:AddClassXP('MAGE', 5)")
    db = A.eval("_dbString()")
    R = boot(load_addon, "Ann", db)
    ck(R.eval("TapCatForever:CD('MAGE').level") == 30 and R.eval("TapCatForever:CD('MAGE').xp") == 105, "after a reload: the same Mage")
    ck(R.eval("TapCatForever:Bag('MAGE')[%d]" % ids["robe"]) == 3 and R.eval("TapCatForever:ChestsOf('pouch', 'MAGE')") == 3, "nothing merged twice")
    ck(len(lines(R)) == 0, "the chat line comes once")
    ck(R.eval("TapCatForeverDB.preAccountBackup['Ann-Forever (2)'] == nil"), "no second backup")

    # --- Bob logs in: the same cats, his own Shop and boss kills
    B = boot(load_addon, "Bob", R.eval("_dbString()"))
    ck(B.eval("TapCatForever.db.class") == "MAGE" and B.eval("TapCatForever:CD('MAGE').level") == 30 and B.eval("TapCatForever:CD('MAGE').xp") == 105,
       "Bob plays the account's Mage")
    ck(B.eval("TapCatForever.charData.shop.stock[1]") == "x_bob" and B.eval("TapCatForever:RealBossKills('hogger')") == 7
       and B.eval("TapCatForever.charData.dungeonPaid == nil or TapCatForever.charData.dungeonPaid['party:36'] == nil"),
       "Bob's Shop, boss kills and dungeon limits are his own")
    B.execute("TapCatForever:GrantItem(TapCatForever.ITEMS.skin_diamond, 'Dropped by Nefarian in Blackwing Lair'); TapCatForever:AddClassXP('MAGE', 50)")
    # --- Cid (a Hunter) plays his Hunter, and sees what Bob's Mage got
    C = boot(load_addon, "Cid", B.eval("_dbString()"), "HUNTER")
    ck(C.eval("TapCatForever.db.class") == "HUNTER" and C.eval("TapCatForever:CD('HUNTER').level") == 12, "Cid plays the Hunter")
    ck(C.eval("TapCatForever:CD('MAGE').xp") == 155 and C.eval("TapCatForever:Owned('MAGE').skin_diamond") == 2, "Bob's progress on the Mage shows for Cid")
    ck(C.eval("TapCatForever.db.owned.skin_lion == nil"), "the Hunter's own collection")

    # --- a brand-new character plays the account's cats
    D = boot(load_addon, "Dee", C.eval("_dbString()"), "WARRIOR")
    ck(D.eval("TapCatForever.db.class") == "WARRIOR" and D.eval("TapCatForever:CD('WARRIOR').level") == 5 and D.eval("TapCatForever:CD('MAGE').level") == 30,
       "a new character starts on its class's account cat")
    ck(D.eval("TapCatForever.charData.shop.stock[1] ~= 'x_ann'") and D.eval("TapCatForever:RealBossKills('hogger')") == 0, "with its own Shop and boss kills")
    ck(D.eval("TapCatForever:Bag('MAGE')[%d]" % ids["robe"]) == 3, "and the Mage's bag")

    # --- an older save joining later (a character saved by an older version): merged the same way
    D.execute(r'''
      local wand = %d
      TapCatForeverDB.chars["Eve-Forever"] = { class = "PRIEST", started = true, carePackage = true,
        owned = { skin_frostsaber = 1 }, look = { fur = "fur_silver", tap = "tap_puff", tapSet = true },
        classData = { MAGE = { level = 45, xp = 7, gear = {}, bag = { [wand] = 2 }, chests = { heroic = { [45] = 1 } } }, PRIEST = { level = 3, xp = 0 } } }
    ''' % ids["wand"])
    Ev = boot(load_addon, "Eve", D.eval("_dbString()"), "PRIEST")
    ck(Ev.eval("TapCatForever:CD('MAGE').level") == 45 and Ev.eval("TapCatForever:Bag('MAGE')[%d]" % ids["wand"]) == 3
       and Ev.eval("TapCatForever:Bag('MAGE')[%d]" % ids["robe"]) == 3 and Ev.eval("TapCatForever:ChestsOf('heroic', 'MAGE')") == 1
       and Ev.eval("TapCatForever:ChestsOf('pouch', 'MAGE')") == 3, "the later Mage is higher: it is the base, and keeps everything else")
    ck(Ev.eval("TapCatForever:ProfState('MAGE').lifetime") == 5000, "the business stays")
    ck(Ev.eval("TapCatForeverDB.preAccountBackup['Eve-Forever'] ~= nil") and len(lines(Ev)) == 0, "a backup for Eve, no second chat line")
    ck(Ev.eval("TapCatForever.db.class") == "PRIEST", "Eve plays her Priest")
    print("account cats section (3 characters with two Mages: highest level is the base, bags, worn gear, chests, cosmetics, kills, "
          "first kills and abilities added, the bigger business with the best skills and Renown, expeditions kept, backup, one chat "
          "line, quest progress; reload; every character sees the same cats; a new character; an older save joining later; "
          "Shop, dungeon limits and boss kills stay per character): all checks passed")

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(HERE, ".."))
    import test_harness
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
