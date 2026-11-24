-- TapCatForever: Professions. Every cat has one main profession picked by its class, then four
-- more it unlocks as it earns Trade Gold (all the Trade Gold this cat ever earned: s.lifetime, which
-- selling the business for Renown never resets). Each class's cat has its own trade: its own
-- Trade Gold, Renown, spots, skills, materials and helpers (db.classData[class].trade).
--   Main (free)       one of three "families" with identical numbers (idle tycoon + hand tool):
--                       mining   (Warrior, Paladin)                  Mining    -> Blacksmithing
--                       skinning (Rogue, Druid, Hunter, Shaman)      Skinning  -> Leatherworking
--                       cloth    (Mage, Priest, Warlock)             Tailoring -> Tailoring
--   Herbalism  (1B Trade Gold earned)  garden plots that grow in real time, gardener automates
--   First Aid  (50T)   turn cloth into bandages that heal your cat in Adventure
--   Fishing    (1Qa)   bobber mini-game, fishing buddy catches while you're away
--   Cooking    (50Qa)  experiment with ingredients to discover dishes that buff you
--   (the later ones need a few rounds of selling the business for Renown, which makes gold come faster)
--   (1.5.2 and older: 5/20/60/150 Renown, still honoured so no save loses an unlock)
--
-- PUBLIC API (prof = a family key "mining" | "skinning" | "cloth"; nil = the current class's family)
--   Families and lists
--     TCF.FAMILIES[fam]          names, icons, nouns, ops (spots), tool names, hire noun (see below)
--     TCF.FAMILY_KEYS            { "mining", "skinning", "cloth" }
--     TCF.CRAFT_FAMILY[craftKey] family key of a crafting skill ("blacksmithing" -> "mining")
--     TCF:MainProf(class)        family key for a class (default: the cat's current class)
--     TCF:MainFamily(class)      TCF.FAMILIES[TCF:MainProf(class)]
--     TCF:CraftProf(class)       crafting key of that family ("blacksmithing"/"leatherworking"/"tailoring")
--     TCF:ProfList(class)        profession rows to show: { main family, herbalism, firstaid, fishing, cooking }
--     TCF.PROFESSIONS            ALL rows (3 families + 4 shared); UI should iterate TCF:ProfList() instead
--     TCF.PROF_BY_KEY[key]       row by key; also has the crafting keys (name, icon, craft = true, family)
--     TCF:ProfUnlocked(key)      learned? (families are always learned; crafting keys too)
--     TCF:ProfUnlockProgress(key) Trade Gold earned so far, Trade Gold needed (p.gold), unlocked?
--     TCF:CheckProfUnlocks()     one chat line per newly unlocked profession of the cat you play (remembered)
--   State and skill
--     TCF:ProfState(class)       a cat's trade, default the current class's (gold, lifetime, renown, mats,
--                                ops[fam][i], tools[fam], upgrades, milestones, skill, garden, aid, fish, cook)
--     TCF:WithTradeClass(cl, fn, ...)  run fn with every profession call on class cl's cat (quiet)
--     TCF:ProfCatchUp()          the cats you aren't playing catch up their idle work to now
--     TCF:TradeTotals()          Trade Gold earned by all the cats, best Renown of one
--     TCF:ProfSkill(key)         1..300 for any profession, family or crafting key
--     TCF:ProfSkillUp(key, diff) WoW-style chance to gain a point (1.6 bands: TCF.SKILLUP_BANDS)
--     TCF.SkillUpChance(skill, diff)  TCF.SkillUpColor(skill, diff)  TCF.SkillUpLine(skill, diff)
--     TCF:StarterSet(craft) / TCF:StarterProgress(craft)   the white starter sets (CraftData.lua)
--     TCF:EarnGold(n) / TCF:SpendGold(n)   Trade Gold (EarnGold applies Renown)
--   Gathering spots (veins / hunting grounds / cloth spots), i = 1..9 (1.6: 7-9 open later)
--     TCF:SpotCount()  TCF:SpotUnlocked(prof, i) -> ok, reason   TCF.SPOT_UNLOCKS[i]
--     TCF.SpotDifficulty(i)  skill-up difficulty of a spot worked by hand
--     TCF:Glitch() / TCF:GlitchClick(prof, i) / TCF:GlitchTick()   the 1.6 patch secret (see below)
--     TCF:OpCost(prof, i, count)   TCF:OpMaxBuy(prof, i)   TCF:BuyOp(prof, i, count|"max")
--     TCF:OpSpeedMult(prof, i)     TCF:OpCycleTime(prof, i)   TCF:OpRevenue(prof, i)
--     TCF:OpMatsPerCycle(prof, i)  TCF:UpgradeMult(prof, i)   TCF:RunOp(prof, i)  (start one cycle)
--     TCF:HireForeman(prof, i)     hire the family's helper (Foreman/Trapper/Scavenger); TCF:HireHelper alias
--     TCF:GatherIncome(prof)       gold/second of a family's spots; nil = every family this cat has
--     TCF:MiningIncome()           = GatherIncome() of all families (old name)
--     TCF.PROF_OPS[i]              economics (cost, mult, time, rev, foreman), identical for every family
--     TCF.UPGRADES[fam]            upgrade rows { id, kind, op, mult, cost, name, icon }; TCF:BuyUpgrade(id)
--     TCF.MILESTONES               counts that double a spot's speed
--   Hand tool (Pickaxe / Skinning Knife / Shears), one per family
--     TCF:GatherClick(prof, i)     one hand click; sets TCF.lastMineGold, TCF.lastMineOre, TCF.lastMineMat
--     TCF:ToolLevel(prof)  TCF:ToolMult(prof, lvl)  TCF:ToolCost(prof, lvl)  TCF:ToolCooldown(prof, lvl)
--     TCF:ToolReadyIn(prof)  TCF:ToolCycleShare(prof, i)  TCF:ToolGold(prof, i)  TCF:ToolRolls(prof, lvl)
--     TCF:ToolName(prof, lvl)  ("Iron Skinning Knife (Lv 23)")   TCF:UpgradeTool(prof)
--   Hand speed (1.6), one per family, kept when the business is sold: shortens the click cooldown
--     TCF:SpeedLevel(prof)  TCF:SpeedCost(prof, lvl)  TCF:SpeedMult(lvl)  TCF:UpgradeSpeed(prof)
--     TCF:ClicksPerSecond(prof, toolLvl, speedLvl)   TCF.SPEED_MAX levels
--     Old names still work: MineClick(i, prof), PickLevel(prof), PickMult(lvl, prof), PickCost(lvl, prof),
--     PickCooldown(lvl, prof), PickReadyIn(prof), PickCycleShare(i, prof), PickGold(i, prof),
--     PickOre(lvl, prof), PickName(lvl, prof), UpgradePick(prof)
--   Crafting
--     TCF.RECIPES[key]             recipe lists: crafting keys, herbalism, firstaid, fishing, cooking.
--                                  TCF.RECIPES[fam] (e.g. RECIPES.mining) reads that family's crafting list.
--       cosmetic recipe  { item = cosmeticId, mats, prof, cosmetic = true, skin = true?, skill? }
--       gear recipe      { gear = itemId, skill, mats, prof }   (from CraftData.lua, sorted by skill)
--     TCF:CraftBlocked(r)  reason text or nil     TCF:CanCraft(r)     TCF:Craft(r)
--     TCF:RecipeItem(r)    the TCF.ITEMS / TCF.GEAR row a recipe makes
--     TCF:RecipeUsable(r)  false when a gear recipe makes something the current class can't wear
--   Renown: TCF:RenownOnReset(), TCF:PrestigeTrade()      Materials: TCF.MAT_BY_KEY, TCF:SellMat(key, n)
local ADDON, TCF = ...

local floor, min, max, random = math.floor, math.min, math.max, math.random

TCF.PROF_OFFLINE_CAP = 24 * 3600

-- every material and product, by key (filled by each profession file)
TCF.MAT_BY_KEY = TCF.MAT_BY_KEY or {}
function TCF.AddMat(key, name, icon, value, prof)
  TCF.MAT_BY_KEY[key] = { key = key, name = name, icon = icon, value = value or 1, prof = prof }
end

---------------------------------------------------------------- the three main professions
-- Gathering spot economics (classic idle tycoon shape), the same for every family
local OPS = {
  { cost = 4,       mult = 1.09, time = 5,   rev = 1,      foreman = 5000 },
  { cost = 60,      mult = 1.17, time = 12,  rev = 60,     foreman = 75000 },
  { cost = 720,     mult = 1.16, time = 24,  rev = 540,    foreman = 500000 },
  { cost = 8640,    mult = 1.15, time = 48,  rev = 4320,   foreman = 2.5e6 },
  { cost = 103680,  mult = 1.14, time = 96,  rev = 51840,  foreman = 6e6 },
  { cost = 1244160, mult = 1.13, time = 384, rev = 622080, foreman = 5e7 },
  -- 1.6: spots 7-9 open up later (TCF.SPOT_UNLOCKS). Bigger and slower, and dearer for what they
  -- earn than the first six, so they add to a big business without breaking the pace of the
  -- later profession unlocks (tools/trade_sim.py --speed against --nospots).
  { cost = 4.5e7,   mult = 1.13, time = 768,  rev = 1.87e6, foreman = 5e8 },
  { cost = 1.6e9,   mult = 1.13, time = 1536, rev = 5e6,    foreman = 2e10 },
  { cost = 5.8e10,  mult = 1.13, time = 3072, rev = 1.24e7, foreman = 8e11 },
}
TCF.PROF_OPS = OPS

-- tool tiers: one tier every 10 levels, the same metals for every family's tool
TCF.PICKAXE_NAMES = { "Copper", "Bronze", "Iron", "Mithril", "Thorium", "Arcanite", "Elementium", "Titanium" }
local function toolTiers(noun)
  local t = {}
  for i, m in ipairs(TCF.PICKAXE_NAMES) do t[i] = m .. " " .. noun end
  return t
end

-- ops rows: { spot name, mat key, mat name, mat icon, creature display ID (3D model) or nil }
TCF.FAMILIES = {
  mining = {
    key = "mining", tab = "Mining", name = "Mining", skillName = "Mining", icon = "Trade_Mining",
    craft = "blacksmithing", craftName = "Blacksmithing", craftIcon = "Trade_BlackSmithing",
    classes = { "WARRIOR", "PALADIN" },
    spotNoun = "vein", spotNounPlural = "veins", spotsTitle = "Veins",
    verb = "Mine", verbing = "mining", matNoun = "ore",
    toolNoun = "Pickaxe", tool = toolTiers("Pickaxe"),
    hire = "Foreman", hirePlural = "Foremen",
    hireDesc = "Works this vein automatically, forever, even offline (up to 24 hours).",
    clickHint = "Click a vein (or its bar) to mine one cycle. Hire a Foreman to keep it running on its own, even offline. The pickaxe digs a little extra by hand.",
    ops = {
      { "Copper Vein", "copper", "Copper Ore", "INV_Ore_Copper_01" },
      { "Tin Vein", "tin", "Tin Ore", "INV_Ore_Tin_01" },
      { "Iron Deposit", "iron", "Iron Ore", "INV_Ore_Iron_01" },
      { "Mithril Deposit", "mithril", "Mithril Ore", "INV_Ore_Mithril_02" },
      { "Thorium Vein", "thorium", "Thorium Ore", "INV_Ore_Thorium_02" },
      { "Arcane Crystal Geode", "arcane", "Arcane Crystal", "INV_Misc_Gem_Crystal_01" },
      { "Dark Iron Deposit (Blackrock Depths)", "darkiron", "Dark Iron Ore", "INV_Ore_Mithril_01" },
      { "Elementium Vein (Blackwing Lair)", "elementium", "Elementium Ore", "INV_Stone_SharpeningStone_01" },
      { "Obsidian Chunk (Ahn'Qiraj)", "obsidian", "Large Obsidian Shard", "INV_Stone_15" },
    },
  },
  skinning = {
    key = "skinning", tab = "Skinning", name = "Skinning", skillName = "Skinning", icon = "INV_Misc_Pelt_Wolf_01",
    craft = "leatherworking", craftName = "Leatherworking", craftIcon = "Trade_LeatherWorking",
    classes = { "ROGUE", "DRUID", "HUNTER", "SHAMAN" },
    spotNoun = "hunting ground", spotNounPlural = "hunting grounds", spotsTitle = "Hunting Grounds",
    verb = "Skin", verbing = "skinning", matNoun = "leather",
    toolNoun = "Skinning Knife", tool = toolTiers("Skinning Knife"),
    hire = "Trapper", hirePlural = "Trappers",
    hireDesc = "Hunts and skins here automatically, forever, even offline (up to 24 hours).",
    clickHint = "Click a hunting ground (or its bar) to skin one cycle. Hire a Trapper to keep it running on its own, even offline. Your skinning knife takes a little extra by hand.",
    ops = {
      { "Barrens Plainstriders",    "lightleather",  "Light Leather",     "INV_Misc_LeatherScrap_03", 1219 },  -- Plainstrider
      { "Wetlands Raptors",         "mediumleather", "Medium Leather",    "INV_Misc_LeatherScrap_05", 960 },   -- Mottled Raptor
      { "Stranglethorn Panthers",   "heavyleather",  "Heavy Leather",     "INV_Misc_LeatherScrap_07", 633 },   -- Shadowmaw Panther
      { "Feralas Yetis",            "thickleather",  "Thick Leather",     "INV_Misc_LeatherScrap_08", 3220 },  -- Rage Scar Yeti
      { "Winterspring Frostsabers", "ruggedleather", "Rugged Leather",    "INV_Misc_LeatherScrap_02", 9953 },  -- Frostsaber
      { "Un'Goro Devilsaurs",       "devilsaur",     "Devilsaur Leather", "INV_Misc_Pelt_03",         5239 },  -- Devilsaur
      { "Zul'Gurub Bats",           "primalbat",     "Primal Bat Leather", "INV_Misc_Pelt_01",       14562 }, -- Frenzied Bloodseeker Bat
      { "Molten Core Hounds",       "coreleather",   "Core Leather",      "INV_Ammo_FireTar",         12168 }, -- Core Hound
      { "Silithid Swarm (Ahn'Qiraj)", "silithid",    "Heavy Silithid Carapace", "INV_Misc_MonsterScales_05", 15334 }, -- Vekniss Warrior
    },
  },
  cloth = {
    key = "cloth", tab = "Tailoring", name = "Tailoring", skillName = "Cloth Scavenging", icon = "Trade_Tailoring",
    craft = "tailoring", craftName = "Tailoring", craftIcon = "Trade_Tailoring",
    classes = { "MAGE", "PRIEST", "WARLOCK" },
    spotNoun = "cloth spot", spotNounPlural = "cloth spots", spotsTitle = "Cloth Spots",
    verb = "Loot", verbing = "looting", matNoun = "cloth",
    toolNoun = "Shears", tool = toolTiers("Shears"),
    hire = "Scavenger", hirePlural = "Scavengers",
    hireDesc = "Loots this spot for cloth automatically, forever, even offline (up to 24 hours).",
    clickHint = "Click a cloth spot (or its bar) to loot one cycle. Hire a Scavenger to keep it running on its own, even offline. Your shears cut a little extra by hand.",
    ops = {
      { "Defias Hideout (Westfall)",          "linen",     "Linen Cloth",     "INV_Fabric_Linen_01",      2331 },  -- Defias Trapper
      { "Syndicate Camp (Alterac)",           "wool",      "Wool Cloth",      "INV_Fabric_Wool_01",       3712 },  -- Syndicate Wizard
      { "Bloodsail Camp (Stranglethorn)",     "silk",      "Silk Cloth",      "INV_Fabric_Silk_01",       796 },   -- Bloodsail Swashbuckler
      { "Gordunni Camp (Feralas)",            "mageweave", "Mageweave Cloth", "INV_Fabric_Mageweave_01",  11558 }, -- Gordunni Ogre Mage
      { "Scourge Camp (Eastern Plaguelands)", "runecloth", "Runecloth",       "INV_Fabric_PurpleFire_01", 7847 },  -- Scourge Champion
      { "Jadefire Satyrs (Felwood)",          "felcloth",  "Felcloth",        "INV_Fabric_Felrag",        2019 },  -- Jadefire Satyr
      { "Moonwell (Felwood)",                 "mooncloth", "Mooncloth",       "INV_Fabric_MoonRag_01" },
      { "Ironweb Spiders (Blackrock Spire)",  "ironweb",   "Ironweb Spider Silk", "Spell_Nature_Web",       9755 },  -- Spire Spider
      { "Cult of the Damned (Naxxramas)",     "wartorn",   "Wartorn Cloth Scrap", "INV_Misc_WartornScrap_Cloth", 16605 }, -- Naxxramas Follower
    },
  },
}
TCF.FAMILY_KEYS = { "mining", "skinning", "cloth" }
local FAM_KEYS = TCF.FAMILY_KEYS
TCF.CRAFT_FAMILY = {}
local CLASS_FAMILY = {}
for _, k in ipairs(FAM_KEYS) do
  local f = TCF.FAMILIES[k]
  TCF.CRAFT_FAMILY[f.craft] = k
  for _, cl in ipairs(f.classes) do CLASS_FAMILY[cl] = k end
  -- every spot's material sells for the same small amount (cloth from the merchant keeps its buy price)
  for _, o in ipairs(f.ops) do
    if not TCF.MAT_BY_KEY[o[2]] then TCF.AddMat(o[2], o[3], o[4], 1, k) end
  end
end
TCF.MINING_OPS = TCF.FAMILIES.mining.ops

TCF.PROFESSIONS = {
  { key = "mining",    name = "Mining",    icon = "Trade_Mining",           gold = 0, renown = 0, family = true },
  { key = "skinning",  name = "Skinning",  icon = "INV_Misc_Pelt_Wolf_01",  gold = 0, renown = 0, family = true },
  { key = "cloth",     name = "Tailoring", icon = "Trade_Tailoring",        gold = 0, renown = 0, family = true },
  -- gold: the Trade Gold this cat has earned in total (s.lifetime) to learn it. renown: the old
  -- rule of 1.5.2 and older, kept as a hidden fallback so no save loses an unlock. Renown is at
  -- most sqrt(earned / 1e8), so a cat that had that Renown had earned more than the new cost anyway.
  -- 1.5.3.4: much higher, so the later ones need a few rounds of selling for Renown. Measured at
  -- about 2 hours a day (scratchpad prestige sim): a cat that never sells levels off at about 1.5T
  -- a day; one that sells whenever it would double its Renown reaches about 50T in 3 weeks, 1Qa
  -- in about 4 and 50Qa in about 5 to 6.
  { key = "herbalism", name = "Herbalism", icon = "Trade_Herbalism",        gold = 1e9,    renown = 5 },
  { key = "firstaid",  name = "First Aid", icon = "Spell_Holy_SealOfSacrifice", gold = 5e13, renown = 20 },
  { key = "fishing",   name = "Fishing",   icon = "Trade_Fishing",          gold = 1e15,   renown = 60 },
  { key = "cooking",   name = "Cooking",   icon = "INV_Misc_Food_15",       gold = 5e16,   renown = 150 },
}
-- unlocked in a trade table s (either rule)
local function unlockedIn(s, p)
  if not p then return false end
  if not p then return false end
  -- learned before (this cat was told): kept, so no save loses an unlock when the amounts change.
  -- (1.5.3.4: Renown alone no longer unlocks anything; 1.5.2 saves were marked told at load.)
  if type(s.announced) == "table" and s.announced[p.key] then return true end
  return (s.lifetime or 0) >= (p.gold or 0)
end
TCF.PROF_BY_KEY = {}
for i, p in ipairs(TCF.PROFESSIONS) do p.index = i; TCF.PROF_BY_KEY[p.key] = p end
-- crafting skills are looked up like professions (names for skill text, Compendium, recipes)
for _, k in ipairs(FAM_KEYS) do
  local f = TCF.FAMILIES[k]
  TCF.PROF_BY_KEY[f.craft] = { key = f.craft, name = f.craftName, icon = f.craftIcon, gold = 0, renown = 0, craft = true, family = k }
  -- the gathering skill's own label (cloth: "Cloth Scavenging", so it can't be mixed up with Tailoring)
  TCF.PROF_BY_KEY[k].skillName = f.skillName
end

function TCF:MainProf(class)
  class = class or self.tradeClass or (self.db and self.db.class)
  return CLASS_FAMILY[class] or "mining"
end
function TCF:MainFamily(class) return TCF.FAMILIES[self:MainProf(class)] end
function TCF:CraftProf(class) return TCF.FAMILIES[self:MainProf(class)].craft end
function TCF:ProfList(class)
  local list = { TCF.PROF_BY_KEY[self:MainProf(class)] }
  for _, p in ipairs(TCF.PROFESSIONS) do if not p.family then list[#list + 1] = p end end
  return list
end

-- family key for a prof argument: a family key, a crafting key, or nil (= current class)
local function famOf(self, prof)
  if prof and TCF.FAMILIES[prof] then return prof end
  if prof and TCF.CRAFT_FAMILY[prof] then return TCF.CRAFT_FAMILY[prof] end
  return self:MainProf()
end

TCF.MILESTONES = { 25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000 }

-- 1.6: spots 7-9 open up with milestones (this cat's highest Renown ever, Trade Gold earned in
-- total, and the gathering skill from working spots by hand). Once open, a spot stays open
-- (selling the business resets what you own there, as with the other spots).
TCF.SPOT_UNLOCKS = {
  [7] = { renown = 100 },
  [8] = { renown = 500, skill = 250 },
  [9] = { lifetime = 1e15, skill = 300 },
}

local MILESTONE_CHEST = { [25] = "pouch", [100] = "strong", [300] = "heroic" }

-- your own hand tool: one per family, for every spot of that family, upgraded level by level
-- forever. Each level is a small boost (+15% per click, compounding) and costs more than the last.
TCF.PICK_BOOST, TCF.PICK_COST, TCF.PICK_COST_GROWTH = 1.15, 25, 1.55
-- a click is worth half a second of the whole spot's output (every spot you own there, with
-- milestones and upgrades), with a 1 in 4 chance of a material. Fast spots give a big share of a
-- cycle per click, slow spots a small one, so no spot breaks the economy.
TCF.PICK_SECONDS, TCF.PICK_ORE_CHANCE = 0.5, 0.25

---------------------------------------------------------------- state
-- Every class's cat has its own trade: Trade Gold, Renown, gathering spots, tools, upgrades,
-- milestones, skills, materials, garden, bandages, fishing and cooking all live in
-- db.classData[class].trade (classData is the account's since 1.6.0). TCF:ProfState() is the current
-- class's. TCF.tradeClass, set only inside TCF:WithTradeClass, points every profession call at
-- another class's cat, which is how idle work runs for the cats you aren't playing.
local function freshOp() return { n = 0, p = 0, run = false, mgr = false } end
local function freshTrade()
  return { gold = 0, lifetime = 0, renown = 0, prestiges = 0, ops = {}, upgrades = {}, milestones = {},
    mats = {}, skill = {}, tools = {}, last = time(), buy = 1, famMoved = true }
end

-- Once per save (1.4 and older): the old single Mining progress moves to the family of the
-- character's class at the time (Warriors and Paladins keep it as Mining). Ore turns into
-- that family's materials tier by tier. Nothing else changes.
local function migrateFamily(s, fam)
  if fam == "mining" or not TCF.FAMILIES[fam] then return end
  local target = s.ops[fam]
  local empty = true
  for i = 1, 6 do if target[i] and (target[i].n or 0) > 0 then empty = false end end
  if empty then s.ops[fam] = s.ops.mining; s.ops.mining = {} end
  s.tools[fam] = max(s.tools[fam] or 0, s.tools.mining or 0); s.tools.mining = 0
  local function rekey(t)
    local moves = {}
    for k in pairs(t) do
      local rest = type(k) == "string" and k:match("^mining(.*)$")
      if rest then moves[k] = rest end
    end
    for k, rest in pairs(moves) do
      if t[fam .. rest] == nil then t[fam .. rest] = t[k] end
      t[k] = nil
    end
  end
  rekey(s.upgrades); rekey(s.milestones)
  if s.skill.mining then
    s.skill[fam] = max(s.skill[fam] or 1, s.skill.mining)
    s.skill.mining = nil
  end
  local ore, to = TCF.FAMILIES.mining.ops, TCF.FAMILIES[fam].ops
  for t = 1, 6 do
    local n = s.mats[ore[t][2]]
    if type(n) == "number" and n > 0 then s.mats[to[t][2]] = (s.mats[to[t][2]] or 0) + n end
    s.mats[ore[t][2]] = nil
  end
end

-- fills in missing fields of a trade table (older saves) for a cat of this class
local checked = setmetatable({}, { __mode = "k" })  -- trade tables already repaired this session
local function repair(s, class)
  s.renownEver = max(s.renownEver or 0, s.renown or 0)
  if checked[s] then return s end
  s.gold, s.lifetime, s.renown, s.prestiges = s.gold or 0, s.lifetime or 0, s.renown or 0, s.prestiges or 0
  -- professions whose unlock this cat was told about. A save from 1.5.2 or older was already
  -- told about the ones its Renown unlocked ("You can now learn ..." when it sold the business).
  if type(s.announced) ~= "table" then
    s.announced = {}
    for _, p in ipairs(TCF.PROFESSIONS) do
      if (p.renown or 0) > 0 and s.renownEver >= p.renown then s.announced[p.key] = true end
    end
  end
  s.ops = type(s.ops) == "table" and s.ops or {}
  s.upgrades = type(s.upgrades) == "table" and s.upgrades or {}
  s.milestones = type(s.milestones) == "table" and s.milestones or {}
  s.mats = type(s.mats) == "table" and s.mats or {}
  s.skill = type(s.skill) == "table" and s.skill or {}
  s.buy = s.buy or 1
  -- older saves had a pickaxe per vein: keep the best one as the overall level
  if type(s.pick) == "table" then
    local best = 1
    for _, t in pairs(s.pick) do if type(t) == "number" and t > best then best = t end end
    s.pickLvl = max(s.pickLvl or 0, (best - 1) * 10)
    s.pick = nil
  end
  s.tools = type(s.tools) == "table" and s.tools or {}
  s.speed = type(s.speed) == "table" and s.speed or {}   -- 1.6 hand speed per family (kept when selling)
  if s.pickLvl then s.tools.mining = max(s.tools.mining or 0, s.pickLvl); s.pickLvl = nil end
  for _, k in ipairs(FAM_KEYS) do
    s.ops[k] = type(s.ops[k]) == "table" and s.ops[k] or {}
    s.tools[k] = s.tools[k] or 0
  end
  if not s.famMoved then
    s.famMoved = true
    migrateFamily(s, TCF:MainProf(class))
  end
  for _, k in ipairs(FAM_KEYS) do
    for i = 1, #OPS do
      local st = s.ops[k][i]
      if type(st) ~= "table" then s.ops[k][i] = freshOp()
      else st.n, st.p = st.n or 0, st.p or 0 end
    end
  end
  checked[s] = true
  return s
end

---------------------------------------------------------------- 1.5.1: one trade per class
-- Up to 1.5.0 a character had one trade (db.trade) shared by all its cats. On the first login
-- with 1.5.1 it is split (db.tradeSplit) and db.trade is removed: everything goes to the current class's cat, except the progress of another
-- family (spots, tool, upgrades, milestones, skills and that family's materials, except cloth
-- when this cat uses First Aid, which needs the same cloth), which goes to the cat of that
-- family this character played most, with no Trade Gold of its own.
-- Milestone keys move with their spots, so no milestone chest can be earned twice.

-- an upgrade or milestone id of family fam ("cloth3_1", "cloth_all0", "mining1_25")
local function famId(k, fam)
  if type(k) ~= "string" or k:sub(1, #fam) ~= fam then return false end
  local rest = k:sub(#fam + 1)
  return (rest:match("^%d+_%d+$") or rest:match("^_all%d+$")) and true or false
end

local function familyProgress(s, fam)
  for i = 1, #OPS do local st = s.ops[fam][i]; if st.n > 0 or st.mgr then return true end end
  if (s.tools[fam] or 0) > 0 then return true end
  for k in pairs(s.upgrades) do if famId(k, fam) then return true end end
  for k in pairs(s.milestones) do if famId(k, fam) then return true end end
  local f = TCF.FAMILIES[fam]
  return (s.skill[fam] or 1) > 1 or (s.skill[f.craft] or 1) > 1
end

-- moves family fam's progress from trade src to trade dst (counts add up, levels keep the best);
-- materials in the set keep (by key) stay in src
local function moveFamily(src, dst, fam, keep)
  local f = TCF.FAMILIES[fam]
  for i = 1, #OPS do
    local a, b = src.ops[fam][i], dst.ops[fam][i]
    b.n = b.n + a.n
    b.mgr = (b.mgr or a.mgr) and true or false
    b.run = (b.run or a.run) and true or false
    b.p = max(b.p or 0, a.p or 0)
    src.ops[fam][i] = freshOp()
  end
  dst.tools[fam] = max(dst.tools[fam] or 0, src.tools[fam] or 0); src.tools[fam] = 0
  for _, t in ipairs({ "upgrades", "milestones" }) do
    local moves = {}
    for k, v in pairs(src[t]) do if famId(k, fam) then moves[k] = v end end
    for k, v in pairs(moves) do dst[t][k] = dst[t][k] or v; src[t][k] = nil end
  end
  for _, k in ipairs({ fam, f.craft }) do
    if src.skill[k] then dst.skill[k] = max(dst.skill[k] or 1, src.skill[k]); src.skill[k] = nil end
  end
  for _, o in ipairs(f.ops) do
    if not (keep and keep[o[2]]) then
      local n = src.mats[o[2]]
      if type(n) == "number" and n > 0 then dst.mats[o[2]] = (dst.mats[o[2]] or 0) + n end
      src.mats[o[2]] = nil
    end
  end
end

-- the cat of family fam this character played most (level, then XP, then ever played)
local function familyClass(self, fam, db)
  db = db or self.db
  local played = db.stats and db.stats.classesPlayed or {}
  local best, bestScore
  for _, cl in ipairs(TCF.FAMILIES[fam].classes) do
    local cd = db.classData[cl]
    if type(cd) == "table" then
      local score = (tonumber(cd.level) or 1) * 1e9 + (tonumber(cd.xp) or 0) * 10 + (played[cl] and 1 or 0)
      if not bestScore or score > bestScore then best, bestScore = cl, score end
    end
  end
  return best
end

-- adds everything in trade src to trade dst (only needed if a class already had its own trade)
local function mergeTrade(src, dst)
  for _, fam in ipairs(FAM_KEYS) do moveFamily(src, dst, fam) end
  dst.gold, dst.lifetime = dst.gold + src.gold, dst.lifetime + src.lifetime
  if src.lifetimeMerged then dst.lifetimeMerged = (tonumber(dst.lifetimeMerged) or 0) + (tonumber(src.lifetimeMerged) or 0) end
  dst.renown = max(dst.renown, src.renown); dst.renownEver = max(dst.renownEver, src.renownEver)
  dst.prestiges = max(dst.prestiges, src.prestiges)
  for k, v in pairs(src.announced or {}) do if v then dst.announced = dst.announced or {}; dst.announced[k] = true end end
  for t, v in pairs(src.upgrades) do dst.upgrades[t] = dst.upgrades[t] or v end
  for t, v in pairs(src.milestones) do dst.milestones[t] = dst.milestones[t] or v end
  for k, v in pairs(src.skill) do dst.skill[k] = max(dst.skill[k] or 1, v) end
  for k, n in pairs(src.mats) do if type(n) == "number" then dst.mats[k] = (dst.mats[k] or 0) + n end end
  for _, k in ipairs({ "garden", "aid", "fish", "cook" }) do
    local a, b = src[k], dst[k]
    if b == nil then dst[k] = a
    elseif type(a) == "table" and type(b) == "table" then
      -- keep every upgrade, plot, buddy level and known dish either one had
      for _, t in ipairs({ "up", "known" }) do
        if type(a[t]) == "table" then
          b[t] = type(b[t]) == "table" and b[t] or {}
          for key, v in pairs(a[t]) do if v then b[t][key] = v end end
        end
      end
      if type(a.n) == "number" then b.n = max(b.n or 0, a.n) end
      if type(a.buddy) == "number" then b.buddy = max(b.buddy or 0, a.buddy) end
      if type(a.gl) == "number" then b.gl = max(b.gl or 0, a.gl) end   -- (1.6.7) the gardener's rank
    end
  end
end

-- db: TCF.db, or (AccountCats.lua, an older character merged in) a stand-in with that
-- character's trade, class and cats (classData) and the account's stats
local function splitShared(self, db)
  db = db or self.db
  local old = db.trade
  db.trade = nil
  db.tradeSplit = true   -- a record that this character's trade was split
  if type(old) ~= "table" then return end
  -- Only an older version of the addon writes db.trade, so a trade found here is always
  -- progress the cats don't have yet (also after going back to 1.5.0 and up again): it is
  -- added to theirs, never dropped and never counted twice.
  local cur = db.class
  repair(old, cur)
  local curFam = TCF:MainProf(cur)
  -- 1.5.0 paid each milestone chest once per spot for all families together, keyed by the
  -- family that made the buy: every family with spots there has had that chest
  for i = 1, #OPS do
    for ms in pairs(MILESTONE_CHEST) do
      local had = false
      for _, k in ipairs(FAM_KEYS) do if old.milestones[k .. i .. "_" .. ms] then had = true end end
      if had then
        for _, k in ipairs(FAM_KEYS) do if old.ops[k][i].n > 0 then old.milestones[k .. i .. "_" .. ms] = true end end
      end
    end
  end
  -- First Aid uses the same cloth as the cloth family: a cat that has First Aid keeps it
  local aidCloth
  if unlockedIn(old, TCF.PROF_BY_KEY.firstaid) or type(old.aid) == "table" then
    aidCloth = {}
    for _, c in ipairs(TCF.CLOTH or {}) do aidCloth[c[1]] = true end
  end
  for _, fam in ipairs(FAM_KEYS) do
    if fam ~= curFam and familyProgress(old, fam) then
      local cl = familyClass(self, fam, db)
      local cd = cl and db.classData[cl]
      if cd then
        local isNew = type(cd.trade) ~= "table"
        if isNew then cd.trade = freshTrade(); cd.trade.last = old.last or time() end
        moveFamily(old, repair(cd.trade, cl), fam, fam == "cloth" and aidCloth or nil)
      end
    end
  end
  local cd = db.classData[cur]
  if type(cd) ~= "table" then return end
  if type(cd.trade) ~= "table" then cd.trade = old
  else mergeTrade(old, repair(cd.trade, cur)) end
end

-- (AccountCats.lua) a pre-1.5.1 character's one trade, split between its own cats the way it
-- would have been at its next login: ctx = { trade, class, classData, stats }
function TCF:SplitOldTrade(ctx) splitShared(self, ctx) end

local scratch = {}   -- a class with no class data (never happens in a real save): not saved
local function S(self, class)
  local db = self.db
  if db.trade ~= nil then splitShared(self) end
  class = class or self.tradeClass or db.class
  local cd = db.classData and db.classData[class]
  local s
  if type(cd) == "table" then
    if type(cd.trade) ~= "table" then cd.trade = freshTrade() end
    s = cd.trade
  else
    scratch[class or "?"] = scratch[class or "?"] or freshTrade()
    s = scratch[class or "?"]
  end
  return repair(s, class)
end
TCF.TradeState = S
-- the current class's trade (or the given class's)
function TCF:ProfState(class) return S(self, class) end

-- class keys whose cat has a trade
local function tradeClasses(self)
  local list = {}
  for _, cl in ipairs(TCF.CLASSES or {}) do
    local cd = self.db.classData[cl.key]
    if type(cd) == "table" and type(cd.trade) == "table" then list[#list + 1] = cl.key end
  end
  return list
end
TCF.TradeClasses = tradeClasses

-- Runs fn(self, ...) with every profession call pointed at class's cat. For a class you aren't
-- playing it is quiet: no loot pop-ups or chat lines.
function TCF:WithTradeClass(class, fn, ...)
  local prevClass, prevQuiet = self.tradeClass, self.tradeQuiet
  self.tradeClass = class
  self.tradeQuiet = (class ~= self.db.class) or nil
  local ok, a, b = pcall(fn, self, ...)
  self.tradeClass, self.tradeQuiet = prevClass, prevQuiet
  if not ok then error(a, 0) end
  return a, b
end

-- Trade Gold earned in total by all the cats, and the best Renown of one cat
function TCF:TradeTotals()
  S(self)
  local life, renown = 0, 0
  for _, cl in ipairs(tradeClasses(self)) do
    local s = S(self, cl)
    -- (with the Trade Gold of the businesses merged into this one when the cats became shared)
    life = life + s.lifetime + (tonumber(s.lifetimeMerged) or 0)
    renown = max(renown, s.renown)
  end
  return life, renown
end

function TCF:ProfUnlocked(prof)
  return unlockedIn(S(self), TCF.PROF_BY_KEY[prof])
end

-- Trade Gold this cat has earned in total, the amount the profession needs, and whether it is learned
function TCF:ProfUnlockProgress(prof)
  local p = TCF.PROF_BY_KEY[prof]
  local s = S(self)
  return s.lifetime, p and p.gold or 0, unlockedIn(s, p)
end

-- Tells the cat you're playing, once, about each profession it can now learn (a chat line, no
-- pop-up), and remembers it in the cat's trade (s.announced). The cats you aren't playing stay
-- quiet: their news waits until you play them (login or switching class).
function TCF:CheckProfUnlocks()
  if not self.db or self.tradeQuiet then return end
  if self.tradeClass and self.tradeClass ~= self.db.class then return end
  local s = S(self)
  for _, p in ipairs(TCF.PROFESSIONS) do
    if not p.family and not s.announced[p.key] and unlockedIn(s, p) then
      s.announced[p.key] = true
      local cl = TCF.CLASS_BY_KEY and TCF.CLASS_BY_KEY[self.db.class]
      local why = s.lifetime >= p.gold and (" has earned " .. TCF.FormatBig(p.gold) .. " Trade Gold and") or ""
      self:Print(string.format("Your %s cat%s can now learn |cffffd100%s|r in the Professions tab.", cl and cl.name or "", why, p.name), true)
      self:PlaySound("ach")
      self:MarkDirty()
    end
  end
end

-- Profession skill 1..300 (WoW style). Chance to improve is higher while easy.
-- 1.6: one curve for every profession, by gap = your skill - the thing's difficulty (a gathering
-- spot, a recipe, a seed, a bandage, a fishing spot, a dish):
--   gap < 5: always (orange), < 15: half the time (yellow), < 30: 1 in 5 (green),
--   < 50: 1 in 20 (green, rarely), 50 or more: never (grey), for gathering too.
-- So the first few always give a point, then it slows down a lot, then stops until you move on.
TCF.SKILLUP_BANDS = {
  { gap = 5,  chance = 1,    color = "ff8040", word = "always" },
  { gap = 15, chance = 0.5,  color = "ffff00", word = "often" },
  { gap = 30, chance = 0.2,  color = "40c040", word = "sometimes" },
  { gap = 50, chance = 0.05, color = "70a070", word = "rarely" },
}
TCF.SKILLUP_GREY = { chance = 0, color = "808080", word = "no longer" }
local function skillBand(skill, difficulty)
  local gap = (skill or 1) - (difficulty or 1)
  for _, b in ipairs(TCF.SKILLUP_BANDS) do if gap < b.gap then return b end end
  return TCF.SKILLUP_GREY
end
-- chance (0..1) that one gather / craft at difficulty gives a point at this skill
function TCF.SkillUpChance(skill, difficulty)
  if (skill or 1) >= 300 then return 0 end
  return skillBand(skill, difficulty).chance
end
-- WoW-style colour code ("|cffff8040") and plain words ("often") for a difficulty at this skill
function TCF.SkillUpColor(skill, difficulty)
  local b = (skill or 1) >= 300 and TCF.SKILLUP_GREY or skillBand(skill, difficulty)
  return "|cff" .. b.color, b.word
end
-- the tooltip line: "Still teaches you: often" (or "no longer"), and its colour code
function TCF.SkillUpLine(skill, difficulty)
  local col, word = TCF.SkillUpColor(skill, difficulty)
  if (skill or 1) >= 300 then return "Still teaches you: no longer (skill is maxed)", col end
  return "Still teaches you: " .. word, col
end
-- A list whose requirements are far apart (seeds, bandages, fishing spots, dishes) would leave a
-- player stuck: nothing teaches more than 49 above its difficulty. Each entry gets a teach level
-- (the difficulty its skill-ups use): at least its requirement, at most 30 below the next one's,
-- and 270 for the last one, so every step can be reached, and 300 too.
function TCF.SetTeachLevels(list, reqOf, set)
  for i, e in ipairs(list) do
    local req = reqOf(e)
    local nextReq = list[i + 1] and reqOf(list[i + 1]) or 300
    set(e, max(req, nextReq - 30))
  end
end
-- skill-up difficulty of gathering spot i (by hand): the first 0, then 50 more for each
function TCF.SpotDifficulty(i) return ((i or 1) - 1) * 50 end

function TCF:ProfSkill(prof) return S(self).skill[prof] or 1 end
function TCF:ProfSkillUp(prof, difficulty)
  local s = S(self)
  local cur = s.skill[prof] or 1
  if cur >= 300 then return end
  if random() < TCF.SkillUpChance(cur, difficulty) then s.skill[prof] = cur + 1; return true end
end

---------------------------------------------------------------- numbers
local SUFFIX = { "", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc" }
function TCF.FormatBig(n)
  if n < 1000 then return (n == floor(n)) and tostring(floor(n)) or string.format("%.1f", n) end
  local e = min(#SUFFIX - 1, floor(math.log10(n) / 3))
  return string.format("%.2f%s", n / 10 ^ (e * 3), SUFFIX[e + 1])
end
function TCF.GoldStr(n, size)
  size = size or 12
  return TCF.FormatBig(n) .. "|TInterface\\MoneyFrame\\UI-GoldIcon:" .. size .. ":" .. size .. ":2:0|t"
end

-- Add Trade Gold (all professions earn through this)
function TCF:EarnGold(n)
  local s = S(self)
  n = n * (1 + 0.02 * s.renown)
  s.gold = s.gold + n
  s.lifetime = s.lifetime + n
  -- a new profession to learn? (cheap: only when the next unlock has been passed)
  if not self.tradeQuiet then
    for _, p in ipairs(TCF.PROFESSIONS) do
      if p.gold > 0 and s.lifetime >= p.gold and not s.announced[p.key] then self:CheckProfUnlocks(); break end
    end
  end
  return n
end
function TCF:SpendGold(n)
  local s = S(self)
  if s.gold < n then return false end
  s.gold = s.gold - n
  return true
end

---------------------------------------------------------------- gathering spots
local function opState(self, prof, i)
  return S(self).ops[famOf(self, prof)][i]
end

-- how many spots a family has (TCF.PROF_SPOTS_CAP: a simulation can play with fewer)
function TCF:SpotCount() return min(#OPS, TCF.PROF_SPOTS_CAP or #OPS) end
-- Is spot i open for this cat? Returns ok, and a plain reason when it is not.
function TCF:SpotUnlocked(prof, i)
  if not OPS[i] or i > self:SpotCount() then return false, "Not available." end
  local u = TCF.SPOT_UNLOCKS[i]
  if not u then return true end
  local s = S(self)
  if type(s.spotsOpen) == "table" and s.spotsOpen[i] then return true end
  local fam = famOf(self, prof)
  local need = {}
  if u.renown and (s.renownEver or 0) < u.renown then need[#need + 1] = string.format("Renown %d (highest so far %d)", u.renown, s.renownEver or 0) end
  if u.lifetime and (s.lifetime or 0) < u.lifetime then need[#need + 1] = string.format("%s Trade Gold earned (so far %s)", TCF.FormatBig(u.lifetime), TCF.FormatBig(s.lifetime or 0)) end
  if u.skill and (s.skill[fam] or 1) < u.skill then
    need[#need + 1] = string.format("%s skill %d (now %d)", TCF.FAMILIES[fam].skillName, u.skill, s.skill[fam] or 1)
  end
  if #need > 0 then return false, "Opens at " .. table.concat(need, " and ") .. "." end
  -- remembered, so changing the numbers later never closes a spot someone has
  s.spotsOpen = type(s.spotsOpen) == "table" and s.spotsOpen or {}
  s.spotsOpen[i] = true
  return true
end

-- Prices, speed milestones and milestone chests count only this cat's own spots: every class
-- has its own trade, so switching class can't stack or repeat anything.
function TCF:OpCost(prof, i, count)
  local o = OPS[i]
  local n = opState(self, prof, i).n
  count = count or 1
  local base = o.cost * o.mult ^ n
  return base * (o.mult ^ count - 1) / (o.mult - 1)
end

function TCF:OpMaxBuy(prof, i)
  local o = OPS[i]
  if not self:SpotUnlocked(prof, i) then return 0 end
  local n = opState(self, prof, i).n
  local base = o.cost * o.mult ^ n
  return max(0, floor(math.log(S(self).gold * (o.mult - 1) / base + 1) / math.log(o.mult)))
end

function TCF:OpSpeedMult(prof, i)
  local n = opState(self, prof, i).n
  local m = 1
  for _, ms in ipairs(TCF.MILESTONES) do if n >= ms then m = m * 2 end end
  -- (1.7.0) the helper's level and trait, the hiding buff and the Busy Hands perk (Workshop.lua)
  if self.WorkshopSpeedMult then m = m * self:WorkshopSpeedMult(famOf(self, prof), i) end
  return m
end
function TCF:OpCycleTime(prof, i) return OPS[i].time / self:OpSpeedMult(prof, i) end

-- Cooking's "gathering profits" dishes (buff key "mining") boost every family
function TCF:UpgradeMult(prof, i)
  local s = S(self)
  local m = 1
  for _, u in ipairs(TCF.UPGRADES[famOf(self, prof)]) do
    if s.upgrades[u.id] and u.kind == "profit" and (u.op == i or u.op == 0) then m = m * u.mult end
  end
  return m * (self.FoodBuff and self:FoodBuff("mining") or 1)
end

function TCF:OpRevenue(prof, i)
  return OPS[i].rev * opState(self, prof, i).n * self:UpgradeMult(prof, i)
end

-- Trade Gold per second from every spot you own in a family (nil: all three families), as if
-- every spot were running (before Renown)
function TCF:GatherIncome(prof)
  local s, g = S(self), 0
  for _, k in ipairs(FAM_KEYS) do
    if prof == nil or k == famOf(self, prof) then
      for i = 1, #OPS do
        if s.ops[k][i].n > 0 then g = g + self:OpRevenue(k, i) / self:OpCycleTime(k, i) end
      end
    end
  end
  return g
end
function TCF:MiningIncome() return self:GatherIncome() end

-- (1.6.2) the goods a cycle gives (ore, leather, cloth) grow with the x3 profit upgrades and Renown,
-- like its Trade Gold: 1 (2 from 100 owned, 3 from 300) times TCF:UpgradeMult times (1 + 2% per Renown)
function TCF:OpMatsBase(prof, i)
  local n = opState(self, prof, i).n
  return 1 + (n >= 100 and 1 or 0) + (n >= 300 and 1 or 0)
end
function TCF:OpMatsPerCycle(prof, i)
  return self:OpMatsBase(prof, i) * self:UpgradeMult(prof, i) * (1 + 0.02 * (S(self).renown or 0))
end

---------------------------------------------------------------- hand tools
function TCF:ToolLevel(prof) return S(self).tools[famOf(self, prof)] or 0 end
function TCF:ToolMult(prof, lvl) return TCF.PICK_BOOST ^ (lvl or self:ToolLevel(prof)) end
function TCF:ToolCost(prof, lvl) lvl = lvl or self:ToolLevel(prof); return floor(TCF.PICK_COST * TCF.PICK_COST_GROWTH ^ lvl) end
-- one click per cooldown (shared by every spot of the family); tool upgrades shorten it a little,
-- down to 0.75s. (A separate Hand speed upgrade was tried during 1.6 testing and taken out: the
-- user wants the click to speed up only slowly with the tool. Its functions stay, unused.)
function TCF:ToolCooldown(prof, lvl)
  return max(0.75, 1.5 * 0.985 ^ (lvl or self:ToolLevel(prof)))
end

-- Hand speed (1.6): a separate upgrade per family, bought with Trade Gold and kept when you sell
-- the business. Each level makes the click cooldown about 7% shorter; at level 15 it is a third
-- (0.75s -> 0.25s with a well upgraded tool). The cost curve is steep: the first levels cost
-- little, the last ones are a goal for many business sales (tools/trade_sim.py --speed).
TCF.SPEED_MAX, TCF.SPEED_FLOOR = 15, 0.25
TCF.SPEED_COST_A, TCF.SPEED_COST_B, TCF.SPEED_COST_BASE = 0.5, 0.0306, 1e4
function TCF:SpeedLevel(prof) return S(self).speed[famOf(self, prof)] or 0 end
function TCF:SpeedMult(lvl) return (1 / 3) ^ (min(TCF.SPEED_MAX, max(0, lvl or 0)) / TCF.SPEED_MAX) end
-- the Trade Gold the next level costs (from level lvl to lvl + 1); nil at the top
function TCF:SpeedCost(prof, lvl)
  lvl = lvl or self:SpeedLevel(prof)
  if lvl >= TCF.SPEED_MAX then return nil end
  local e = TCF.SPEED_COST_A * lvl + TCF.SPEED_COST_B * lvl * lvl
  local c = TCF.SPEED_COST_BASE * 10 ^ e
  local p = 10 ^ floor(math.log10(c) - 1)   -- two significant digits
  return floor(c / p + 0.5) * p
end
function TCF:UpgradeSpeed(prof)
  local f = famOf(self, prof)
  local cost = self:SpeedCost(f)
  if not cost or not self:SpendGold(cost) then return false end
  local s = S(self)
  s.speed[f] = (s.speed[f] or 0) + 1
  self:MarkDirty()
  return true
end
function TCF:ClicksPerSecond(prof, lvl, speedLvl) return 1 / self:ToolCooldown(prof, lvl, speedLvl) end
function TCF:ToolReadyIn(prof)
  self.toolNext = self.toolNext or {}
  return max(0, (self.toolNext[famOf(self, prof)] or 0) - GetTime())
end
-- share of spot i's cycle that one click is worth
function TCF:ToolCycleShare(prof, i) return min(1, TCF.PICK_SECONDS * self:ToolMult(prof) / self:OpCycleTime(prof, i)) end
-- gold for one click on spot i
function TCF:ToolGold(prof, i)
  local n = opState(self, prof, i).n
  local share = OPS[i].rev * n * self:UpgradeMult(prof, i) * self:ToolCycleShare(prof, i)
  -- First spot only: never less than a quarter of one spot's cycle, so you can work your way
  -- to the first purchase. Other spots need one bought first and use the cycle share alone
  -- (a floor there would let a few clicks on a high spot outpay all of its purchases).
  local floorGold = (i == 1) and OPS[1].rev * 0.25 * self:ToolMult(prof) * self:UpgradeMult(prof, 1) or 0
  return max(share, floorGold)
end
-- rolls for a material per click: one more every 15 levels
function TCF:ToolRolls(prof, lvl) return 1 + floor((lvl or self:ToolLevel(prof)) / 15) end
function TCF:ToolName(prof, lvl)
  local f = TCF.FAMILIES[famOf(self, prof)]
  lvl = lvl or self:ToolLevel(prof)
  local n = f.tool[min(#f.tool, floor(lvl / 10) + 1)]
  return string.format("%s (Lv %d)", n, lvl)
end
function TCF:UpgradeTool(prof)
  local f = famOf(self, prof)
  if not self:SpendGold(self:ToolCost(f)) then return false end
  local s = S(self)
  s.tools[f] = (s.tools[f] or 0) + 1
  self:MarkDirty()
  return true
end

-- Work spot i by hand with the family's tool (works on the first spot from the start)
function TCF:GatherClick(prof, i)
  local f = famOf(self, prof)
  local s = S(self)
  local op = TCF.FAMILIES[f].ops[i]
  if not op then return false end
  if i > 1 and s.ops[f][i].n < 1 then return false end
  if self:ToolReadyIn(f) > 0 then return false end
  self.toolNext[f] = GetTime() + self:ToolCooldown(f)
  local gold = self:EarnGold(self:ToolGold(f, i))
  local got = 0
  for _ = 1, self:ToolRolls(f) do if random() < TCF.PICK_ORE_CHANCE then got = got + 1 end end
  s.mats[op[2]] = (s.mats[op[2]] or 0) + got
  self:ProfSkillUp(f, TCF.SpotDifficulty(i))
  -- 1.6 patch secret (TCF:GlitchClick below): a glitched spot pays far too much for a minute
  if self.GlitchClick then
    local g2, m2 = self:GlitchClick(f, i)
    gold, got = gold + g2, got + m2
  end
  -- (1.7.0) glints, rich spots, Sharp Tools and rare finds (Workshop.lua)
  if self.WorkshopClick then
    local g2, m2 = self:WorkshopClick(f, i, gold, got)
    gold, got = gold + g2, got + m2
  end
  self.lastMineOre, self.lastMineMat, self.lastMineGold, self.lastMineFamily = got, op[2], gold, f
  return true
end

---------------------------------------------------------------- 1.6 patch secret: the glitched spot
-- DEVELOPER NOTE (kept out of the game's own text; the patch notes only hint at it):
-- While this patch is installed (TCF.version starts with TCF.GLITCH_PATCH), working a gathering
-- spot by hand can make that spot "glitch" for TCF.GLITCH_SECONDS: every click by hand on it pays
-- an extra TCF.GLITCH_GOLD_SECONDS seconds of all of this family's spots' income (at least 10
-- normal clicks) and three more of its material. It starts on a click:
--   * any minute: a 1 in TCF.GLITCH_ODDS chance per click by hand
--   * at sixteen minutes past the hour (the player's clock, "1.6"): the first click by hand
-- At most once a day per WoW character (TCF.charData.profGlitchDay), only for the cat you play, only by hand
-- (helpers never glitch). One chat line when it starts and one when it ends with what it paid.
-- No pop-ups. While it lasts the spot's row flickers purple on the Professions page.
TCF.GLITCH_PATCH, TCF.GLITCH_SECONDS, TCF.GLITCH_GOLD_SECONDS, TCF.GLITCH_ODDS, TCF.GLITCH_MINUTE = "1.6", 60, 5, 3000, 16
function TCF:GlitchPatchActive()
  if self.glitchForce ~= nil then return self.glitchForce end
  local v = tostring(TCF.version or "")
  return v:sub(1, #TCF.GLITCH_PATCH + 1) == TCF.GLITCH_PATCH .. "."
end
local function today() local ok, d = pcall(date, "%Y-%m-%d"); return ok and d or "?" end
local function clockMinute() local ok, m = pcall(date, "%M"); return ok and tonumber(m) or -1 end
-- the glitch going on now ({ fam, i, ends, gold, mats, class }) or nil
function TCF:Glitch()
  local g = self.profGlitch
  if g and g.class == (self.db and self.db.class) and GetTime() < g.ends then return g end
end
function TCF:GlitchLeft() local g = self:Glitch(); return g and max(0, g.ends - GetTime()) or 0 end
-- the day this WoW character last had a glitch: kept in this character's own saved data
-- (TCF.charData), so alts don't share one, without making it a new per-character db key
function TCF:GlitchDay()
  local c = TCF.charData or self.db
  return c and c.profGlitchDay
end
function TCF:SetGlitchDay(d)
  local c = TCF.charData or self.db
  if c then c.profGlitchDay = d end
end
-- called by every successful click by hand: the bonus while glitched, else maybe start one
function TCF:GlitchClick(f, i)
  if self.tradeQuiet or not self.db or (self.tradeClass and self.tradeClass ~= self.db.class) then return 0, 0 end
  local g = self:Glitch()
  if g then
    if g.fam ~= f or g.i ~= i then return 0, 0 end
    local s = S(self)
    local op = TCF.FAMILIES[f].ops[i]
    local bonus = self:EarnGold(max(self:GatherIncome(f) * TCF.GLITCH_GOLD_SECONDS, self:ToolGold(f, i) * 10))
    s.mats[op[2]] = (s.mats[op[2]] or 0) + 3
    g.gold, g.mats, g.clicks = g.gold + bonus, g.mats + 3, g.clicks + 1
    return bonus, 3
  end
  if not self:GlitchPatchActive() or self:GlitchDay() == today() then return 0, 0 end
  if clockMinute() ~= TCF.GLITCH_MINUTE and random(TCF.GLITCH_ODDS) ~= 1 then return 0, 0 end
  self:SetGlitchDay(today())
  self.db.stats.profGlitches = (self.db.stats.profGlitches or 0) + 1
  self.profGlitch = { fam = f, i = i, ends = GetTime() + TCF.GLITCH_SECONDS, gold = 0, mats = 0, clicks = 0, class = self.db.class }
  local name = TCF.FAMILIES[f].ops[i][1]
  self:Print(string.format("|cffcc66ffSomething is wrong at your %s spot. It is giving far too much. Better be quick.|r", name), true)
  self:MarkDirty()
  return 0, 0
end
-- ends the glitch (one chat line with what it paid); run from the professions tick
function TCF:GlitchTick()
  local g = self.profGlitch
  if not g or GetTime() < g.ends then return end
  self.profGlitch = nil
  -- shown even with chat lines off only while you still play that cat (it answers your clicks)
  local force = self.db and g.class == self.db.class or false
  if g.clicks > 0 or g.gold > 0 then
    local f = TCF.FAMILIES[g.fam]
    self:Print(string.format("|cffcc66ffYour %s spot is back to normal. While it lasted it paid %s Trade Gold and %d %s.|r",
      f.ops[g.i][1], TCF.GoldStr(g.gold), g.mats, f.ops[g.i][3]), force)
  else
    self:Print(string.format("|cffcc66ffYour %s spot is back to normal.|r", TCF.FAMILIES[g.fam].ops[g.i][1]), force)
  end
end

-- 1.6: whether any recipe uses this material (the later spots' materials have no recipe yet)
function TCF.MatUsedInRecipe(key)
  if not TCF.matUsedCache then
    local used = {}
    for _, list in pairs(TCF.RECIPES or {}) do
      for _, r in ipairs(list) do
        if type(r.mats) == "table" then for k in pairs(r.mats) do used[k] = true end end
      end
    end
    TCF.matUsedCache = used
  end
  return TCF.matUsedCache[key] or false
end

-- old names (Mining only before families existed); prof defaults to the current class's family
function TCF:MineClick(i, prof) return self:GatherClick(prof, i) end
function TCF:PickLevel(prof) return self:ToolLevel(prof) end
function TCF:PickMult(lvl, prof) return self:ToolMult(prof, lvl) end
function TCF:PickCost(lvl, prof) return self:ToolCost(prof, lvl) end
function TCF:PickCooldown(lvl, prof) return self:ToolCooldown(prof, lvl) end
function TCF:PickReadyIn(prof) return self:ToolReadyIn(prof) end
function TCF:PickCycleShare(i, prof) return self:ToolCycleShare(prof, i) end
function TCF:PickGold(i, prof) return self:ToolGold(prof, i) end
function TCF:PickOre(lvl, prof) return self:ToolRolls(prof, lvl) end
function TCF:PickName(lvl, prof) return self:ToolName(prof, lvl) end
function TCF:UpgradePick(prof) return self:UpgradeTool(prof) end

-- Upgrades: x3 profits per spot and for all spots, per family (ids "<family><spot>_<k>",
-- "<family>_all<k>"; Mining keeps its old ids). The hand tool has its own endless upgrade.
TCF.UPGRADES = {}
for _, k in ipairs(FAM_KEYS) do
  local f = TCF.FAMILIES[k]
  local list = {}
  for i, o in ipairs(f.ops) do
    for t = 0, 2 do
      list[#list + 1] = { id = k .. i .. "_" .. t, kind = "profit", op = i, mult = 3, family = k,
        cost = OPS[i].cost * 2e5 * 500 ^ t, name = o[1] .. ": Trade Gold and goods x3", icon = o[4] }
    end
  end
  for t = 0, 2 do
    list[#list + 1] = { id = k .. "_all" .. t, kind = "profit", op = 0, mult = 3, family = k,
      cost = 1e9 * 1e4 ^ t, name = "All " .. f.tab .. ": Trade Gold and goods x3", icon = f.icon }
  end
  table.sort(list, function(a, b) return a.cost < b.cost end)
  TCF.UPGRADES[k] = list
end

function TCF:BuyOp(prof, i, count)
  local f = famOf(self, prof)
  local s = S(self)
  if not self:SpotUnlocked(f, i) then return false end
  if count == "max" then count = self:OpMaxBuy(f, i) end
  if not count or count < 1 then return false end
  local cost = self:OpCost(f, i, count)
  if not self:SpendGold(cost) then return false end
  local st = s.ops[f][i]
  local before = st.n
  st.n = st.n + count
  local after = st.n
  for ms, chest in pairs(MILESTONE_CHEST) do
    local key = f .. i .. "_" .. ms
    -- once per spot for this cat (a save from before 1.5 may hold another family's key)
    local had = false
    for _, k in ipairs(FAM_KEYS) do if s.milestones[k .. i .. "_" .. ms] then had = true end end
    if before < ms and after >= ms and not had then
      s.milestones[key] = true
      self:AwardChest(chest, TCF.FAMILIES[f].ops[i][1] .. " x" .. ms)
    end
  end
  self:MarkDirty()
  return true
end

-- hire the family's helper (Foreman / Trapper / Scavenger) for spot i
function TCF:HireForeman(prof, i)
  local f = famOf(self, prof)
  local st = S(self).ops[f][i]
  if st.mgr or st.n < 1 or not self:SpendGold(OPS[i].foreman) then return false end
  st.mgr = true; st.run = true
  local fam = TCF.FAMILIES[f]
  if self.HelperHired then
    -- (1.7.0) every helper has a name and a trait (Workshop.lua)
    self:HelperHired(f, i)
    local h = self:HelperInfo(f, i)
    self:Print(string.format("%s the %s (%s: %s) now works %s for you.", h.name, fam.hire:lower(), h.trait.name, h.trait.text, fam.ops[i][1]), true)
  else
    self:Print(string.format("A %s now works %s for you.", fam.hire, fam.ops[i][1]), true)
  end
  self:MarkDirty()
  return true
end
TCF.HireHelper = TCF.HireForeman

function TCF:BuyUpgrade(id)
  local s = S(self)
  for _, k in ipairs(FAM_KEYS) do
    for _, u in ipairs(TCF.UPGRADES[k]) do
      if u.id == id then
        -- (1.6) a spot that hasn't opened yet can't be upgraded
        if u.op > 0 and not self:SpotUnlocked(k, u.op) then return false end
        if s.upgrades[id] or not self:SpendGold(u.cost) then return false end
        s.upgrades[id] = true
        self:MarkDirty()
        return true
      end
    end
  end
  return false
end

function TCF:RunOp(prof, i)
  local st = opState(self, prof, i)
  if st.n > 0 and not st.run then st.run = true; return true end
end

---------------------------------------------------------------- key presses and ticking
-- Every key press in WoW waters the garden (of the cat you're playing). Gathering spots only
-- run when you start them yourself (click the spot) or once a helper works them.
function TCF:ProfTap()
  if not self.db then return end
  if self.GardenTap and self:ProfUnlocked("herbalism") then self:GardenTap() end
end

local function produce(self, s, f, i, cycles)
  self:EarnGold(self:OpRevenue(f, i) * cycles)
  local op = TCF.FAMILIES[f].ops[i]
  -- whole goods go in the bag; the part of one left over waits for the next cycle (s.matCarry)
  s.matCarry = type(s.matCarry) == "table" and s.matCarry or {}
  local got = cycles * self:OpMatsPerCycle(f, i) * (self.HelperGoodsMult and self:HelperGoodsMult(f, i) or 1)
    + (tonumber(s.matCarry[op[2]]) or 0)
  local whole = floor(got)
  s.matCarry[op[2]] = got - whole
  if whole > 0 then s.mats[op[2]] = (s.mats[op[2]] or 0) + whole end
end

-- Advance one cat's trade by dt seconds (the current class's, or TCF.tradeClass's inside
-- TCF:WithTradeClass). offline = only automated things run.
function TCF:ProfAdvance(dt, offline)
  local s = S(self)
  for _, f in ipairs(FAM_KEYS) do
    for i, st in ipairs(s.ops[f]) do
      if st.n > 0 and (st.mgr or (st.run and not offline)) then
        st.p = st.p + dt / self:OpCycleTime(f, i)
        if st.p >= 1 then
          local cycles = st.mgr and floor(st.p) or 1
          produce(self, s, f, i, cycles)
          if st.mgr and self.HelperWorked then self:HelperWorked(f, i, cycles) end   -- (1.7.0) helpers learn
          st.p = st.mgr and (st.p - cycles) or 0
          if not st.mgr then st.run = false end
        end
      end
    end
  end
  for _, mod in ipairs(TCF.PROF_MODULES) do
    if self:ProfUnlocked(mod.key) then mod.advance(self, dt, offline) end
  end
  -- (1.7.0) the Profession Bag: goods past the bag's stack size are sold (Bag.lua)
  if self.MatBagTrim then self:MatBagTrim() end
  -- last is how far this cat has been counted: a fraction of a second ahead of time() while you
  -- play (time() is whole seconds), so a catch-up never counts the same moment twice
  local now = time()
  if offline then s.last = now
  else s.last = min(now + 1, max(now - 1, (s.last or now) + dt)) end
end
TCF.PROF_MODULES = TCF.PROF_MODULES or {}

-- The cats you aren't playing keep working: their helpers, gardener, field medic, fishing
-- buddy and sous-chef catch up to now (at most 24 hours), quietly, into each cat's own trade.
-- Runs every few seconds while you play and before you switch class.
function TCF:ProfCatchUp()
  local db = self.db
  if not db then return end
  S(self)
  local now = time()
  for _, cl in ipairs(tradeClasses(self)) do
    if cl ~= db.class then
      local s = S(self, cl)
      local dt = min(TCF.PROF_OFFLINE_CAP, max(0, now - (s.last or now)))
      if dt > 0 then self:WithTradeClass(cl, self.ProfAdvance, dt, true)
      elseif (s.last or 0) > now + 1 then s.last = now end   -- the clock went back
    end
  end
end

TCF.PROF_CATCHUP_EVERY = 5
function TCF:ProfessionsTick(login, dt)
  local cur = S(self)
  if login then
    -- offline time for every cat on this character, each from its own last update
    local now = time()
    local away = min(TCF.PROF_OFFLINE_CAP, max(0, now - (cur.last or now)))
    if away > 60 then
      local before = cur.gold
      self:ProfAdvance(away, true)
      if cur.gold > before then
        self:Print(string.format("While you were away your professions earned %s Trade Gold.", TCF.GoldStr(cur.gold - before)))
      end
    elseif away > 0 then
      -- a short gap (a /reload) is counted too, quietly
      local quiet = self.tradeQuiet
      self.tradeQuiet = true
      local ok, err = pcall(self.ProfAdvance, self, away, true)
      self.tradeQuiet = quiet
      if not ok then error(err, 0) end
    end
    if not cur.last or cur.last > now + 1 then cur.last = now end
    self:ProfCatchUp()   -- every other cat, quietly, from its own last update
    self.profCatchT = 0
    -- anything this cat unlocked but was never told about (offline, or while you played another cat)
    self:CheckProfUnlocks()
    return
  end
  self:ProfAdvance(dt or 0.25)
  if self.profGlitch then self:GlitchTick() end
  self.profCatchT = (self.profCatchT or 0) + (dt or 0.25)
  if self.profCatchT >= TCF.PROF_CATCHUP_EVERY then
    self.profCatchT = 0
    self:ProfCatchUp()
  end
end

---------------------------------------------------------------- renown (prestige)
function TCF:RenownOnReset()
  local s = S(self)
  return max(0, floor(math.sqrt(s.lifetime / 1e8)) - s.renown)
end

-- Sells everything this cat bought with Trade Gold for permanent Renown (for this cat only;
-- every class has its own business). Skills, Hand speed (1.6), known recipes, materials, bandages,
-- dishes and unlocked professions are kept.
function TCF:PrestigeTrade()
  local s = S(self)
  local gain = self:RenownOnReset()
  if gain < 5 then return false end
  if self.AddRenownPoints then self:DepthState(); self:AddRenownPoints(gain) end   -- (1.7.0) Renown shop (ProfDepth.lua)
  s.renown = s.renown + gain
  s.renownEver = max(s.renownEver, s.renown)
  s.prestiges = s.prestiges + 1
  s.gold = 0
  s.upgrades = {}
  for _, f in ipairs(FAM_KEYS) do
    s.tools[f] = 0
    for i = 1, #OPS do s.ops[f][i] = freshOp() end
  end
  for _, mod in ipairs(TCF.PROF_MODULES) do if mod.reset then mod.reset(self, s) end end
  local coins = min(1000, gain * 3)
  self:AddCoins(coins)
  local cl = TCF.CLASS_BY_KEY and TCF.CLASS_BY_KEY[self.db.class]
  self:Print(string.format("Your %s sold its business for |cffffd100%d Renown|r (+%d%% profits forever) and %d TapCoins.",
    cl and (cl.name .. " cat") or "cat", gain, gain * 2, coins), true)
  self:CheckProfUnlocks()   -- (the old Renown rule can still unlock something)
  self:PlaySound("ach")
  self:MarkDirty(); self:RefreshAll()
  return true
end

---------------------------------------------------------------- crafting (all professions)
-- Cosmetic recipes (cosmetic = true: "Cosmetic only (no stats)") and, for the three crafting
-- skills, real gear from CraftData.lua. Blacksmithing keeps the old Mining cosmetics.
TCF.RECIPES = {
  blacksmithing = {
    { item = "craft_copper_circlet",  mats = { copper = 60 } },
    { item = "craft_iron_greathelm",  mats = { iron = 250, tin = 120 } },
    { item = "craft_mithril_medal",   mats = { mithril = 400 } },
    { item = "craft_thorium_axe",     mats = { thorium = 600, mithril = 300 } },
    { item = "craft_arcanite_reaper", mats = { arcane = 400, thorium = 1200 } },
  },
  leatherworking = {
    { item = "craft_lw_cap",          mats = { lightleather = 60 } },
    { item = "craft_lw_bandolier",    mats = { heavyleather = 250, mediumleather = 120 } },
    { item = "craft_lw_mantle",       mats = { thickleather = 400 } },
    { item = "craft_lw_hornhelm",     mats = { ruggedleather = 600, thickleather = 300 } },
    { item = "craft_lw_devilclaws",   mats = { devilsaur = 400, ruggedleather = 1200 } },
  },
  tailoring = {
    { item = "craft_tl_scarf",        mats = { linen = 60 } },
    { item = "craft_tl_wizardhat",    mats = { silk = 250, wool = 120 } },
    { item = "craft_tl_robe",         mats = { mageweave = 400 } },
    { item = "craft_tl_tophat",       mats = { runecloth = 600, mageweave = 300 } },
    { item = "craft_tl_felwings",     mats = { felcloth = 400, runecloth = 1200 } },
  },
  herbalism = {
    { item = "craft_peacebloom_crown", mats = { peacebloom = 60 } },
    { item = "craft_mageroyal_bloom",  mats = { mageroyal = 250 } },
    { item = "craft_kingsblood_aura",  mats = { kingsblood = 400 } },
    { item = "craft_dreamfoil_wreath", mats = { dreamfoil = 300, sungrass = 300 } },
    { item = "craft_lotus_bloom",      mats = { lotus = 60, dreamfoil = 600 } },
  },
  firstaid = {
    { item = "craft_wolfpelt_cloak",   mats = { linen = 80 } },
    { item = "craft_raptor_hood",      mats = { wool = 150 } },
    { item = "craft_thick_mantle",     mats = { silk = 200 } },
    { item = "craft_devilsaur_mantle", mats = { mageweave = 300 } },
    { item = "craft_onyxia_cloak",     mats = { runecloth = 600, b_heavyrunecloth = 100 } },
  },
  fishing = {
    { item = "craft_fishing_hat",    mats = { smallfish = 60 } },
    { item = "craft_iron_pole",      mats = { trout = 150, bristle = 100 } },
    { item = "craft_murloc_bubbles", mats = { nightfin = 200 } },
    { item = "craft_eel_shield",     mats = { eel = 300 } },
    { item = "craft_pinchy_gift",    mats = { pinchy = 5, whitescale = 300 } },
  },
  cooking = {
    { item = "craft_chef_spice", mats = { d_chili = 25, hotspice = 100 } },
    { item = "craft_chef_feast", mats = { d_feast = 10, d_soup = 50 } },
  },
}

-- Cat skins with a crafting source (get = { kind = "craft", prof, mats, skill } in
-- Data.lua's SKINS) become recipes in that profession, after its cosmetics, easiest first.
do
  local skins = {}
  for _, it in ipairs(TCF.ITEM_LIST) do
    local g = it.get
    if it.slot == "skin" and g and g.kind == "craft" and g.mats and TCF.RECIPES[g.prof] then skins[#skins + 1] = it end
  end
  table.sort(skins, function(a, b)
    if (a.get.skill or 0) ~= (b.get.skill or 0) then return (a.get.skill or 0) < (b.get.skill or 0) end
    return a.id < b.id
  end)
  for _, it in ipairs(skins) do
    local list = TCF.RECIPES[it.get.prof]
    list[#list + 1] = { item = it.id, mats = it.get.mats, skill = it.get.skill, prof = it.get.prof, skin = true }
  end
end
for prof, list in pairs(TCF.RECIPES) do
  for _, r in ipairs(list) do r.prof = r.prof or prof; if r.item then r.cosmetic = true end end
end

-- 1.6: Cosmetic only recipes (fur colours and the other cosmetics) cost a lot more of the materials
-- they are made from, more for rarer ones. Gear recipes are unchanged. Gathered materials (ore,
-- leather, cloth, herbs, fish) are multiplied; rare or made things (Black Lotus, Mr. Pinchy,
-- bandages, dishes, bought spices) stay as they were. Amounts keep two significant digits.
-- A skin's recipe shares its materials table with the skin's get (Data.lua), so the Compendium
-- shows the same amounts. tools/trade_sim.py --speed shows when a cat can afford them.
TCF.COSMETIC_MAT_MULT = { [1] = 3, [2] = 5, [3] = 10, [4] = 20, [5] = 40 }
TCF.COSMETIC_MAT_KEEP = { lotus = true, pinchy = true, hotspice = true, mildspice = true }
local function keepMat(k) return TCF.COSMETIC_MAT_KEEP[k] or k:sub(1, 2) == "d_" or k:sub(1, 2) == "b_" end
local function tidyAmount(n)
  if n < 100 then return floor(n + 0.5) end
  local p = 10 ^ (floor(math.log10(n)) - 1)
  return floor(n / p + 0.5) * p
end
do
  local done = {}
  for _, list in pairs(TCF.RECIPES) do
    for _, r in ipairs(list) do
      local it = r.cosmetic and TCF.ITEMS[r.item]
      if it and not done[r.mats] then
        done[r.mats] = true
        local mult = TCF.COSMETIC_MAT_MULT[it.rarity] or 1
        for k, n in pairs(r.mats) do
          if not keepMat(k) then r.mats[k] = tidyAmount(n * mult) end
        end
      end
    end
  end
end

-- Gear recipes from CraftData.lua (TCF.CRAFT_RECIPES[craftKey] = { { gear, skill, mats }, ... }),
-- after the cosmetics, sorted by skill. Unknown items and malformed rows are skipped.
do
  local src = type(TCF.CRAFT_RECIPES) == "table" and TCF.CRAFT_RECIPES or {}
  for _, k in ipairs(FAM_KEYS) do
    local ck = TCF.FAMILIES[k].craft
    local add = {}
    for _, r in ipairs(type(src[ck]) == "table" and src[ck] or {}) do
      if type(r) == "table" and r.gear and TCF.GEAR and TCF.GEAR[r.gear] and type(r.mats) == "table" then
        add[#add + 1] = { gear = r.gear, skill = tonumber(r.skill) or 1, mats = r.mats, prof = ck, starter = r.starter and true or nil }
      end
    end
    table.sort(add, function(a, b) if a.skill ~= b.skill then return a.skill < b.skill end return a.gear < b.gear end)
    local list = TCF.RECIPES[ck]
    for _, r in ipairs(add) do list[#list + 1] = r end
  end
end
-- TCF.RECIPES.mining / .skinning / .cloth read the family's crafting list (not seen by pairs)
setmetatable(TCF.RECIPES, { __index = function(t, k)
  local f = TCF.FAMILIES[k]
  return f and rawget(t, f.craft) or nil
end })

-- 1.6 starter sets (CraftData.lua TCF.CRAFT_STARTER): white pieces for every armour slot (and a
-- Blacksmithing weapon) a new cat can wear. A slot counts once one of its items was crafted by this
-- cat, is in its bag or is worn. The recipe list shows the set first while the skill is low.
TCF.STARTER_SET_SKILL = 75   -- below this the Crafting page shows the starter set at the top
function TCF:StarterSet(craft)
  craft = craft or self:CraftProf()
  local list = TCF.CRAFT_STARTER and TCF.CRAFT_STARTER[craft] or {}
  local s = S(self)
  local made = type(s.starterMade) == "table" and s.starterMade or {}
  local bag = self.Bag and self:Bag() or {}
  local worn = {}
  for _, id in pairs(self.GearEquipped and self:GearEquipped() or {}) do worn[id] = true end
  local out, done = {}, 0
  for _, ids in ipairs(list) do
    local have
    for _, id in ipairs(ids) do
      if made[id] or (bag[id] or 0) > 0 or worn[id] then have = id; break end
    end
    out[#out + 1] = { ids = ids, have = have }
    if have then done = done + 1 end
  end
  return out, done, #list
end
function TCF:StarterProgress(craft)
  local _, done, total = self:StarterSet(craft)
  return done, total
end

function TCF:RecipeItem(r)
  if r.gear then return TCF.GEAR and TCF.GEAR[r.gear] end
  if r.potion then return TCF.POTION_BY_KEY and TCF.POTION_BY_KEY[r.potion] end
  return TCF.ITEMS[r.item]
end

-- a gear recipe whose item the current class can't wear (it can still be made and sold)
function TCF:RecipeUsable(r)
  if not r.gear then return true end
  local it = self:RecipeItem(r)
  if not it then return false end
  if self.GearUsable then return self:GearUsable(it, self.db.class) and true or false end
  return true
end

local function classNames(fam)
  local names = {}
  for _, k in ipairs(TCF.FAMILIES[fam].classes) do
    local cl = TCF.CLASS_BY_KEY and TCF.CLASS_BY_KEY[k]
    names[#names + 1] = cl and cl.name or k
  end
  if #names <= 1 then return names[1] or "" end
  return table.concat(names, ", ", 1, #names - 1) .. " or " .. names[#names]
end

-- Why a recipe can't be made yet (skill too low, another class's craft, a cosmetic or
-- skin you already have), or nil.
function TCF:CraftBlocked(r)
  if r.gear and not self:RecipeItem(r) then return "This item is not available." end
  local fam = TCF.CRAFT_FAMILY[r.prof]
  if r.gear and fam and fam ~= self:MainProf() then
    return string.format("Switch to a %s cat to make this.", classNames(fam))
  end
  if r.skill and r.prof and self:ProfSkill(r.prof) < r.skill then
    local p = TCF.PROF_BY_KEY[r.prof]
    return string.format("Needs %s %d.", p and p.name or r.prof, r.skill)
  end
  -- (1.7.0) the long-chase recipes need a specialization and a guild rank (ProfDepth.lua, ProfSets.lua)
  if r.spec and self.Spec then
    local sp = self:Spec(r.prof)
    if not sp or sp.key ~= r.spec then
      local want = TCF.SPEC_BY_KEY[r.spec]
      return string.format("Needs the %s specialization.", want and want.name or r.spec)
    end
  end
  if r.rank and self.GuildRank and self:GuildRank(r.prof) < r.rank then
    local g = TCF.GUILDS[r.prof]
    return string.format("Needs %s with %s.", TCF.GUILD_RANKS[r.rank].name, g and g.name or "your guild")
  end
  local it = r.item and TCF.ITEMS[r.item]
  if it and self.db.owned[it.id] then
    return it.slot == "skin" and "You already have this skin." or "You already have this."
  end
end

function TCF:CanCraft(r)
  if self:CraftBlocked(r) then return false end
  local s = S(self)
  for m, n in pairs(r.mats) do if (s.mats[m] or 0) < n then return false end end
  return true
end

-- "All": craft a recipe as many times as the materials allow (up to 50 at once), quietly, with
-- one chat line at the end instead of a line and a notice for every item.
TCF.CRAFT_ALL_MAX = 50
function TCF:CraftCount(r)
  if not self:CanCraft(r) then return 0 end
  local s, n = S(self), math.huge
  for m, need in pairs(r.mats) do n = min(n, floor((s.mats[m] or 0) / need)) end
  local it = self.RecipeItem and self:RecipeItem(r)
  if not r.gear and it and (it.slot == "skin" or it.source) then n = min(n, 1) end   -- a cosmetic is made once
  return min(n, TCF.CRAFT_ALL_MAX)
end
function TCF:CraftAll(r)
  local want = self:CraftCount(r)
  if want <= 0 then return 0 end
  local s = S(self)
  local skill0 = r.prof and self:ProfSkill(r.prof) or 0
  local origPrint, origToast = TCF.Print, TCF.ShowLootToast
  TCF.Print = function(selfp, msg, force) if force then return origPrint(selfp, msg, force) end end
  TCF.ShowLootToast = function() end
  local made = 0
  local ok, err = pcall(function()
    for _ = 1, want do
      if not self:Craft(r) then break end
      made = made + 1
    end
  end)
  TCF.Print, TCF.ShowLootToast = origPrint, origToast
  if not ok then error(err, 0) end
  if made > 0 then
    local it = self:RecipeItem(r)
    local name = it and it.name or "items"
    local gained = r.prof and (self:ProfSkill(r.prof) - skill0) or 0
    local where = r.gear and "your Gear bag" or (r.potion and "your potions" or "your collection")
    self:Print(string.format("Crafted %d x %s (in %s)%s.", made, name, where,
      gained > 0 and string.format(", skill +%d", gained) or ""), true)
    self:MarkDirty(); self:RefreshAll()
  end
  return made
end

function TCF:Craft(r)
  if not self:CanCraft(r) then return false end
  local s = S(self)
  for m, n in pairs(r.mats) do s.mats[m] = s.mats[m] - n end
  self.db.stats.crafted = (self.db.stats.crafted or 0) + 1
  -- crafting skills (Blacksmithing, Leatherworking, Tailoring) improve WoW style
  if TCF.CRAFT_FAMILY[r.prof] then self:ProfSkillUp(r.prof, r.skill or 1) end
  if r.starter then
    s.starterMade = type(s.starterMade) == "table" and s.starterMade or {}
    s.starterMade[r.gear] = true
  end
  if r.potion then
    -- (1.6.7) a potion: into this cat's stock (Herbalism), and brewing teaches Herbalism
    s.mats[r.potion] = (s.mats[r.potion] or 0) + 1
    self:ProfSkillUp("herbalism", r.teach or r.skill or 1)
    local it = self:RecipeItem(r)
    self:Print(string.format("Brewed %s (you have %d). Drink it from Crafting.", it and it.name or "a potion", s.mats[r.potion]))
  elseif r.gear then
    local it = self:RecipeItem(r)
    -- (1.7.0) sometimes a Masterwork version (ProfDepth.lua)
    if self.MasterworkChance and not r.starter and random() < self:MasterworkChance(r) then
      local mw = TCF.MasterworkGear(r.gear)
      if mw then
        it = mw
        local d = self:DepthState()
        d.masterworks = (d.masterworks or 0) + 1
        if not self.tradeQuiet then self:Print(string.format("Masterwork. You made %s.", TCF.GearLink and TCF.GearLink(mw) or mw.name), true) end
      end
    end
    self:GrantGear(it, "Crafted", true)
  else
    local it = TCF.ITEMS[r.item]
    self:GrantItem(it, "Crafted", true)
    if it.slot == "skin" then self:Print("Wear your new " .. TCF.ItemLink(it) .. " skin from the Appearance tab.", true) end
    if r.longChase and self.CheckSetTitles then self:CheckSetTitles() end   -- (1.7.0) a whole set: its title
  end
  self:MarkDirty()
  return true
end

function TCF:SellMat(key, n)
  local s = S(self)
  local m = TCF.MAT_BY_KEY[key]
  n = min(n or 1, s.mats[key] or 0)
  if not m or n <= 0 then return 0 end
  s.mats[key] = s.mats[key] - n
  local g = self:EarnGold(m.value * n)
  self:MarkDirty()
  return g
end
