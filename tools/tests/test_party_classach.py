# Class achievements (ClassAchievements.lua): every class's cat has its own set next to the
# account-wide achievements. Checks: the list and its texts, earning per class, once per account
# (an alt of the same class can't earn it again), small TapCoins, chests only for the class you
# play and for the other cats (each in its own cat's Treasure Bag), the level 60 cosmetic (also on alts), credit at login
# for an existing save (one summary line), expedition counts, the Achievements tab filter and
# class picker, and that the account achievements still work as before.
# Run on its own:  python3 tools/tests/test_party_classach.py [seed]
import os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

CODE = r'''
local TCF = TapCatForever
local function check(c, m) if not c then error("check failed: " .. tostring(m), 2) end end
local function login(name) _charName = name; _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN") end
local function keys() local n = 0; for _, cl in ipairs(TCF.CLASSES) do n = n + TCF:ChestCount(cl.key) end; return n end
local function chatSince(n0) local t = {}; for i = n0 + 1, #_chat do t[#t + 1] = _chat[i] end; return t end
local r = {}
TCF.db.ui.chat = true

-- 1. the list
local list = TCF.CLASS_ACHIEVEMENTS
check(#list >= 20, "a full set per class: " .. #list)
local seen, coins = {}, 0
for _, a in ipairs(list) do
  check(not seen[a.id], "unique id " .. a.id); seen[a.id] = true
  check(not TCF.CLASS_ACH_BY_ID[a.id] or TCF.CLASS_ACH_BY_ID[a.id] == a, "lookup")
  for _, b in ipairs(TCF.ACHIEVEMENTS) do check(b.id ~= a.id, "no clash with an account achievement: " .. a.id) end
  check(a.coins <= 60, "small TapCoins: " .. a.id)
  check(a.chest and TCF.CHEST_BY_KEY[a.chest], "a chest: " .. a.id)
  for _, cl in ipairs(TCF.CLASSES) do
    local d = TCF:ClassAchDesc(a, cl.key)
    check(type(d) == "string" and d ~= "" and not d:find("!", 1, true) and not a.name:find("!", 1, true), "plain text: " .. a.id)
    check(TCF:ClassAchGoal(a, cl.key) >= 1, "goal " .. a.id)
  end
  coins = coins + a.coins
end
r.coinsPerClass = coins
check(coins <= 800, "TapCoins stay scarce: " .. coins .. " per class")
for _, cl in ipairs(TCF.CLASSES) do
  check(TCF:ClassAchGoal(TCF.CLASS_ACH_BY_ID.c_abil, cl.key) == #TCF.ABILITIES[cl.key], "every ability of " .. cl.key)
  local it = TCF:ClassAchItem(TCF.CLASS_ACH_BY_ID.c_lvl60, cl.key)
  check(it and it.class == cl.key and it.rarity == 5 and it.slot == "main", "level 60 cosmetic for " .. cl.key)
end
check(TCF:ClassAchGoal(TCF.CLASS_ACH_BY_ID.c_dungall, "MAGE") >= 15 and TCF:ClassAchGoal(TCF.CLASS_ACH_BY_ID.c_raidall, "MAGE") >= 5, "dungeon and raid counts")

-- 2. a fresh character: nothing earned yet beyond what a new cat has
login("Classach")
check(TCF.db.class == "MAGE", "a Mage")
local acc0 = 0; for _ in pairs(TCF.db.achievements) do acc0 = acc0 + 1 end
local c0, k0, n0 = TCF.db.coins, keys(), #_chat
TCF.db.classData.WARRIOR.level = 21          -- a cat you aren't playing
TCF.db.classData.MAGE.level = 10             -- the cat you play
TCF:CheckAchievements()
check(TCF:ClassAchEarned("WARRIOR", "c_lvl10") and TCF:ClassAchEarned("WARRIOR", "c_lvl20") and not TCF:ClassAchEarned("WARRIOR", "c_lvl30"), "Warrior 10 and 20")
check(TCF:ClassAchEarned("MAGE", "c_lvl10") and not TCF:ClassAchEarned("MAGE", "c_lvl20"), "Mage 10")
check(not TCF:ClassAchEarned("PRIEST", "c_lvl10"), "not for a level 1 Priest")
local lines = chatSince(n0)
local wl, ml = 0, 0
for _, l in ipairs(lines) do
  check(not l:find("!", 1, true), "plain chat: " .. l)
  if l:find("Warrior achievement earned", 1, true) then wl = wl + 1; check(l:find("goes to your Warrior cat's Treasure Bag", 1, true), "Warrior chest to its bag: " .. l) end
  if l:find("Mage achievement earned", 1, true) then ml = ml + 1 end
end
check(wl == 2 and ml == 1, "one chat line each: " .. wl .. " " .. ml)
check(keys() == k0 + 3 and TCF:ChestCount("WARRIOR") == 2, "the Mage's chest and two in the Warrior's own bag: " .. (keys() - k0))
check(not TCF.db.classAchPending.WARRIOR, "nothing waits: the Warrior has its own bag")
-- earned once: checking again gives nothing more
local c1, k1 = TCF.db.coins, keys()
TCF:CheckAchievements()
check(TCF.db.coins == c1 and keys() == k1, "nothing twice")
-- switching to the Warrior: its chests are already in its bag
TCF:SetClass("WARRIOR"); _update(1.5)
check(keys() == k1 and TCF:ChestCount() == 2, "the Warrior's chests in its bag: " .. TCF:ChestCount())
TCF:SetClass("MAGE"); _update(1.5)

-- 3. stats: zones, abilities, gear sets, crafting, expeditions
local cd = TCF.db.classData.MAGE
check(TCF:ClassStat("dungeons", "MAGE") == 0 and TCF:ClassStat("world", "MAGE") == 0, "nothing cleared yet")
local function clearTo(ti) local t = TCF.TIERS[ti]; cd.adv.best = ti * 100 + #t.bosses * 2 end
local firstDungeon, firstRaid
for ti, t in ipairs(TCF.TIERS) do
  if t.raid and not firstRaid then firstRaid = ti end
  if TCF.IsDungeonTier(t) and not firstDungeon then firstDungeon = ti end
end
clearTo(firstDungeon)
check(TCF:ClassStat("world", "MAGE") == 2 and TCF:ClassStat("dungeons", "MAGE") == 1 and TCF:ClassStat("raids", "MAGE") == 0, "first dungeon cleared")
clearTo(firstRaid)
check(TCF:ClassStat("dungeons", "MAGE") == TCF:ClassAchGoal(TCF.CLASS_ACH_BY_ID.c_dungall, "MAGE") and TCF:ClassStat("raids", "MAGE") == 1, "every dungeon and one raid")
for _, ab in ipairs(TCF.ABILITIES.MAGE) do cd.abilities[ab.key] = true end
check(TCF:ClassStat("abilities", "MAGE") == #TCF.ABILITIES.MAGE, "abilities")
local k2, p2 = keys(), TCF.db.coins
TCF:CheckAchievements()
for _, id in ipairs({ "c_world", "c_dung1", "c_dung5", "c_dung10", "c_dungall", "c_raid1", "c_abil" }) do check(TCF:ClassAchEarned("MAGE", id), id) end
check(not TCF:ClassAchEarned("MAGE", "c_raidall"), "not every raid")
check(keys() == k2 + 7, "seven Mage chests: " .. (keys() - k2))
check(TCF.db.keys.raid >= 1 and (TCF.db.keys.dungeon or 0) >= 3, "dungeon chests and a hoard")
-- a full Rare set worn
local bySlot = {}
for _, g in ipairs(TCF.GEAR_LIST) do
  if not g.retired and g.q == 3 then
    local s = TCF:GearTargetSlots(g, "MAGE")
    if #s == 1 and not bySlot[s[1]] then bySlot[s[1]] = g.id end
  end
end
local n = 0
for _, slot in ipairs(TCF.CLASS_SET_SLOTS) do if bySlot[slot] then cd.gear[slot] = bySlot[slot]; n = n + 1 end end
check(n == 9 and TCF:ClassStat("rareSet", "MAGE") == 9 and TCF:ClassStat("epicSet", "MAGE") < 9, "a Rare set: " .. n)
cd.gear.HEAD = nil
check(TCF:ClassStat("rareSet", "MAGE") == 8, "a missing piece")
cd.gear.HEAD = bySlot.HEAD
-- crafted gear worn
local crafted = {}
for _, g in ipairs(TCF.GEAR_LIST) do if g.crafted then crafted[#crafted + 1] = g end end
check(#crafted >= 5, "crafted gear exists")
local ring = 0
cd.gear = {}
local used = {}
for _, g in ipairs(crafted) do
  local s = TCF:GearTargetSlots(g, "MAGE")[1]
  if s and not used[s] then used[s] = true; cd.gear[s] = g.id; ring = ring + 1 end
  if ring >= 5 then break end
end
check(TCF:ClassStat("craftedWorn", "MAGE") == ring, "crafted pieces worn")
-- crafting skill (this cat's own trade)
local ps = TCF:ProfState("MAGE")
ps.skill[TCF:CraftProf("MAGE")] = 300
check(TCF:ClassStat("craftSkill", "MAGE") == 300 and TCF:ClassStat("craftSkill", "WARRIOR") == 1, "crafting skill per cat")
-- expeditions: every cat that went counts
TCF.db.expeditions = { active = {} }
TCF.db.classData.ROGUE.level = 30
for i = 1, 10 do
  table.insert(TCF.db.expeditions.active, { key = "elwynn", members = { "MAGE", "WARRIOR", "ROGUE" }, start = 0, finish = 0, power = 1, chance = 1 })
  TCF:ClaimExpedition(1)
end
check(TCF:ClassCount("MAGE", "exp") == 10 and TCF:ClassCount("ROGUE", "exp") == 10 and TCF:ClassCount("PRIEST", "exp") == 0, "expedition counts")
TCF:CheckAchievements()
check(TCF:ClassAchEarned("MAGE", "c_exp10") and TCF:ClassAchEarned("ROGUE", "c_exp10") and TCF:ClassAchEarned("MAGE", "c_craft300")
  and TCF:ClassAchEarned("MAGE", "c_craftset"), "expeditions, crafting skill and crafted set")

-- 4. level 60: the class's Legendary main hand cosmetic
local legend = TCF:ClassAchItem(TCF.CLASS_ACH_BY_ID.c_lvl60, "PRIEST")
TCF.db.owned[legend.id] = nil
TCF.db.classData.PRIEST.level = 60
TCF:CheckAchievements()
check(TCF:ClassAchEarned("PRIEST", "c_lvl60") and TCF.db.owned[legend.id], "level 60 cosmetic")

-- 5. once per account: another character with the same classes earns nothing again, but gets the cosmetic
login("Classalt")
check(TCF.db.owned[legend.id], "the cosmetic on an alt too")
local c3, k3, n3 = TCF.db.coins, keys(), #_chat
TCF.db.classData.WARRIOR.level = 25
TCF.db.classData.PRIEST.level = 60
TCF:CheckAchievements()
check(TCF.db.coins == c3 and keys() == k3, "alts of the same class can't farm: +" .. (TCF.db.coins - c3))
for _, l in ipairs(chatSince(n3)) do check(not l:find("Warrior achievement", 1, true) and not l:find("Priest achievement", 1, true), "no repeat: " .. l) end
TCF.db.classData.WARRIOR.level = 30
TCF:CheckAchievements()
check(TCF:ClassAchEarned("WARRIOR", "c_lvl30"), "the next one is new")

-- 6. an existing save gets credit at login, with one summary line
TapCatForeverDB.classAch, TapCatForeverDB.classAchPending, TapCatForeverDB.classProgress = nil, nil, nil
TapCatForeverDB.chars["Classold-Forever"] = { classData = { HUNTER = { level = 44, xp = 0 } } }
local n4 = #_chat
login("Classold")
check(TCF.db.classData.HUNTER.level == 44, "old save loaded")
check(TCF:ClassAchEarned("HUNTER", "c_lvl40") and not TCF:ClassAchEarned("HUNTER", "c_lvl50"), "credit for an old Hunter")
local sums, per = 0, 0
for _, l in ipairs(chatSince(n4)) do
  if l:find("class achievement", 1, true) and l:find("already done", 1, true) then sums = sums + 1 end
  if l:find("achievement earned", 1, true) and l:find("Hunter", 1, true) then per = per + 1 end
end
check(sums == 1 and per == 0, "one summary line at login: " .. sums .. " " .. per)
check(TCF:ChestCount("HUNTER") >= 4 and not TCF.db.classAchPending.HUNTER, "the Hunter's chests in its bag: " .. TCF:ChestCount("HUNTER"))

-- 7. the Achievements tab: Account / This class and the class picker
TCF.db.class = "HUNTER"; _update(1.5)
TCF:CreateWindow(); TCF.window:Show()
local win = TCF.window
win:SelectTab(9)
local ui = win.achUI
check(ui and ui.acc and ui.cls and #ui.picks == 9, "filter buttons and class picker")
check(ui.picks[1]:IsShown() == false, "the picker hides in the account view")
local accHeader = ui.header:GetText()
check(accHeader:find("Achievements", 1, true), "account view: " .. accHeader)
ui.cls.scripts.OnClick(ui.cls)
check(win.achMode == "class" and ui.picks[1]:IsShown(), "class view")
check(ui.header:GetText():find("Hunter", 1, true), "the class you play: " .. ui.header:GetText())
local row1 = ui.rows[1]
check(row1.name:GetText():find("Finding Its Feet", 1, true) and row1.barText:GetText() == "Complete", "first row done")
check(row1.reward:GetText():find("Cat Treat Pouch", 1, true), "chest in the reward: " .. row1.reward:GetText())
for i, cl in ipairs(TCF.CLASSES) do
  if cl.key == "PRIEST" then ui.picks[i].scripts.OnClick(ui.picks[i]) end
end
check(ui.header:GetText():find("Priest", 1, true), "picking another class")
win.acScroll = 100; win:RefreshAchievements()
check(win.acScroll == #TCF.CLASS_ACHIEVEMENTS - ui.nRows, "scrolls to the end: " .. win.acScroll)
local last = ui.rows[ui.nRows]
check(last:IsShown() and last.name:GetText():find("Party Regular", 1, true), "last row")
ui.acc.scripts.OnClick(ui.acc)
check(win.achMode == "account" and ui.header:GetText():find("Achievements", 1, true) and not ui.picks[1]:IsShown(), "back to the account view")
local acc1 = 0; for _ in pairs(TCF.db.achievements) do acc1 = acc1 + 1 end
check(acc1 >= acc0, "account achievements kept")
return string.format("%d per class, %d TapCoins per class in all", #list, r.coinsPerClass)
'''

def check(seed, load_addon):
    lua = load_addon()
    out = lua.execute(CODE)
    print("party class achievements section (%s; earned per class once per account, chests in each cat's own bag, level 60 cosmetic on alts, login credit with one line, expedition counts, the Account / This class filter): all checks passed" % out)

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    os.chdir(ROOT)
    import test_harness
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
