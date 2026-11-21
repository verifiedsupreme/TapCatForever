-- TapCatForever: Professions. Every cat has one main profession picked by its CURRENT class,
-- then four shared ones it unlocks with Renown (the prestige reset). All share Trade Gold.
--   Main (free)       one of three "families" with identical numbers (idle tycoon + hand tool):
--                       mining   (Warrior, Paladin)                  Mining    -> Blacksmithing
--                       skinning (Rogue, Druid, Hunter, Shaman)      Skinning  -> Leatherworking
--                       cloth    (Mage, Priest, Warlock)             Tailoring -> Tailoring
--   Herbalism  (5 Renown)  garden plots that grow in real time, gardener automates
--   First Aid  (20 Renown) turn cloth into bandages that heal your cat in Adventure
--   Fishing    (60 Renown) bobber mini-game, fishing buddy catches while you're away
--   Cooking    (150 Renown) experiment with ingredients to discover dishes that buff you
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
--   State and skill
--     TCF:ProfState()            db.trade (gold, renown, mats, ops[fam][i], tools[fam], upgrades, skill, ...)
--     TCF:ProfSkill(key)         1..300 for any profession, family or crafting key
--     TCF:ProfSkillUp(key, diff) WoW-style chance to gain a point
--     TCF:EarnGold(n) / TCF:SpendGold(n)   Trade Gold (EarnGold applies Renown)
--   Gathering spots (veins / hunting grounds / cloth spots), i = 1..6
--     TCF:OpCost(prof, i, count)   TCF:OpMaxBuy(prof, i)   TCF:BuyOp(prof, i, count|"max")
--     TCF:OpSpeedMult(prof, i)     TCF:OpCycleTime(prof, i)   TCF:OpRevenue(prof, i)
--     TCF:OpMatsPerCycle(prof, i)  TCF:UpgradeMult(prof, i)   TCF:RunOp(prof, i)  (start one cycle)
--     TCF:HireForeman(prof, i)     hire the family's helper (Foreman/Trapper/Scavenger); TCF:HireHelper alias
--     TCF:GatherIncome(prof)       gold/second of a family's spots; nil = all three families
--     TCF:MiningIncome()           = GatherIncome() of all families (old name)
--     TCF.PROF_OPS[i]              economics (cost, mult, time, rev, foreman), identical for every family
--     TCF.UPGRADES[fam]            upgrade rows { id, kind, op, mult, cost, name, icon }; TCF:BuyUpgrade(id)
--     TCF.MILESTONES               counts that double a spot's speed
--   Hand tool (Pickaxe / Skinning Knife / Shears), one per family
--     TCF:GatherClick(prof, i)     one hand click; sets TCF.lastMineGold, TCF.lastMineOre, TCF.lastMineMat
--     TCF:ToolLevel(prof)  TCF:ToolMult(prof, lvl)  TCF:ToolCost(prof, lvl)  TCF:ToolCooldown(prof, lvl)
--     TCF:ToolReadyIn(prof)  TCF:ToolCycleShare(prof, i)  TCF:ToolGold(prof, i)  TCF:ToolRolls(prof, lvl)
--     TCF:ToolName(prof, lvl)  ("Iron Skinning Knife (Lv 23)")   TCF:UpgradeTool(prof)
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
  { key = "mining",    name = "Mining",    icon = "Trade_Mining",           renown = 0, family = true },
  { key = "skinning",  name = "Skinning",  icon = "INV_Misc_Pelt_Wolf_01",  renown = 0, family = true },
  { key = "cloth",     name = "Tailoring", icon = "Trade_Tailoring",        renown = 0, family = true },
  { key = "herbalism", name = "Herbalism", icon = "Trade_Herbalism",        renown = 5 },
  { key = "firstaid",  name = "First Aid", icon = "Spell_Holy_SealOfSacrifice", renown = 20 },
  { key = "fishing",   name = "Fishing",   icon = "Trade_Fishing",          renown = 60 },
  { key = "cooking",   name = "Cooking",   icon = "INV_Misc_Food_15",       renown = 150 },
}
TCF.PROF_BY_KEY = {}
for i, p in ipairs(TCF.PROFESSIONS) do p.index = i; TCF.PROF_BY_KEY[p.key] = p end
-- crafting skills are looked up like professions (names for skill text, Compendium, recipes)
for _, k in ipairs(FAM_KEYS) do
  local f = TCF.FAMILIES[k]
  TCF.PROF_BY_KEY[f.craft] = { key = f.craft, name = f.craftName, icon = f.craftIcon, renown = 0, craft = true, family = k }
  -- the gathering skill's own label (cloth: "Cloth Scavenging", so it can't be mixed up with Tailoring)
  TCF.PROF_BY_KEY[k].skillName = f.skillName
end

function TCF:MainProf(class)
  class = class or (self.db and self.db.class)
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
local MILESTONE_CHEST = { [25] = "pouch", [100] = "strong", [300] = "heroic" }

-- your own hand tool: one per family, for every spot of that family, upgraded level by level
-- forever. Each level is a small boost (+15% per click, compounding) and costs more than the last.
TCF.PICK_BOOST, TCF.PICK_COST, TCF.PICK_COST_GROWTH = 1.15, 25, 1.55
-- a click is worth half a second of the whole spot's output (every spot you own there, with
-- milestones and upgrades), with a 1 in 4 chance of a material. Fast spots give a big share of a
-- cycle per click, slow spots a small one, so no spot breaks the economy.
TCF.PICK_SECONDS, TCF.PICK_ORE_CHANCE = 0.5, 0.25

---------------------------------------------------------------- state
local function freshOp() return { n = 0, p = 0, run = false, mgr = false } end

-- Once per save: the old single Mining progress moves to the family of the character's
-- current class (Warriors and Paladins keep it as Mining). Ore turns into that family's
-- materials tier by tier. Nothing else changes.
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

local checked = setmetatable({}, { __mode = "k" })  -- trade tables already repaired this session
local function S(self)
  local db = self.db
  if not db.trade then
    db.trade = { gold = 0, lifetime = 0, renown = 0, prestiges = 0, ops = {}, upgrades = {}, milestones = {},
      mats = {}, last = time(), buy = 1, famMoved = true }
  end
  local s = db.trade
  s.renownEver = max(s.renownEver or 0, s.renown or 0)
  if checked[s] then return s end
  s.gold, s.lifetime, s.renown, s.prestiges = s.gold or 0, s.lifetime or 0, s.renown or 0, s.prestiges or 0
  s.ops = type(s.ops) == "table" and s.ops or {}
  s.upgrades = s.upgrades or {}
  s.milestones = s.milestones or {}
  s.mats = s.mats or {}
  s.skill = s.skill or {}
  s.buy = s.buy or 1
  -- older saves had a pickaxe per vein: keep the best one as the overall level
  if type(s.pick) == "table" then
    local best = 1
    for _, t in pairs(s.pick) do if type(t) == "number" and t > best then best = t end end
    s.pickLvl = max(s.pickLvl or 0, (best - 1) * 10)
    s.pick = nil
  end
  s.tools = type(s.tools) == "table" and s.tools or {}
  if s.pickLvl then s.tools.mining = max(s.tools.mining or 0, s.pickLvl); s.pickLvl = nil end
  for _, k in ipairs(FAM_KEYS) do
    s.ops[k] = type(s.ops[k]) == "table" and s.ops[k] or {}
    s.tools[k] = s.tools[k] or 0
  end
  if not s.famMoved and db.class then
    s.famMoved = true
    migrateFamily(s, TCF:MainProf(db.class))
  end
  for _, k in ipairs(FAM_KEYS) do
    for i = 1, 6 do s.ops[k][i] = s.ops[k][i] or freshOp() end
  end
  if s.famMoved then checked[s] = true end
  return s
end
TCF.TradeState = S
function TCF:ProfState() return S(self) end

function TCF:ProfUnlocked(prof)
  local p = TCF.PROF_BY_KEY[prof]
  return p and S(self).renownEver >= (p.renown or 0) or false
end

-- Profession skill 1..300 (WoW style). Chance to improve is higher while easy.
function TCF:ProfSkill(prof) return S(self).skill[prof] or 1 end
function TCF:ProfSkillUp(prof, difficulty)
  local s = S(self)
  local cur = s.skill[prof] or 1
  if cur >= 300 then return end
  local gap = cur - (difficulty or 1)
  -- grey recipes (75+ below your skill) never raise a crafting skill; gathering keeps 5%
  local chance = gap < 25 and 1 or gap < 50 and 0.5 or gap < 75 and 0.25 or (TCF.CRAFT_FAMILY[prof] and 0 or 0.05)
  if random() < chance then s.skill[prof] = cur + 1; return true end
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

-- Spot i's count summed over every family. Prices, speed milestones and milestone chests use
-- this, so spreading spots over several families (by switching class) costs and earns the
-- same as building one family deep.
local function combinedN(self, i)
  local s, n = S(self), 0
  for _, k in ipairs(FAM_KEYS) do n = n + s.ops[k][i].n end
  return n
end
function TCF:OpCombinedCount(i) return combinedN(self, i) end
-- true when this character owns at least one spot of family k
function TCF:FamilyOwned(k)
  local ops = S(self).ops[k]
  if not ops then return false end
  for i = 1, 6 do if ops[i].n > 0 then return true end end
  return false
end

function TCF:OpCost(prof, i, count)
  local o = OPS[i]
  local n = combinedN(self, i)
  count = count or 1
  local base = o.cost * o.mult ^ n
  return base * (o.mult ^ count - 1) / (o.mult - 1)
end

function TCF:OpMaxBuy(prof, i)
  local o = OPS[i]
  local n = combinedN(self, i)
  local base = o.cost * o.mult ^ n
  return max(0, floor(math.log(S(self).gold * (o.mult - 1) / base + 1) / math.log(o.mult)))
end

function TCF:OpSpeedMult(prof, i)
  local n = combinedN(self, i)
  local m = 1
  for _, ms in ipairs(TCF.MILESTONES) do if n >= ms then m = m * 2 end end
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
      for i = 1, 6 do
        if s.ops[k][i].n > 0 then g = g + self:OpRevenue(k, i) / self:OpCycleTime(k, i) end
      end
    end
  end
  return g
end
function TCF:MiningIncome() return self:GatherIncome() end

function TCF:OpMatsPerCycle(prof, i)
  local n = opState(self, prof, i).n
  return 1 + (n >= 100 and 1 or 0) + (n >= 300 and 1 or 0)
end

---------------------------------------------------------------- hand tools
function TCF:ToolLevel(prof) return S(self).tools[famOf(self, prof)] or 0 end
function TCF:ToolMult(prof, lvl) return TCF.PICK_BOOST ^ (lvl or self:ToolLevel(prof)) end
function TCF:ToolCost(prof, lvl) lvl = lvl or self:ToolLevel(prof); return floor(TCF.PICK_COST * TCF.PICK_COST_GROWTH ^ lvl) end
-- one click per cooldown (shared by every spot of the family); upgrades shorten it a little, down to 0.75s
function TCF:ToolCooldown(prof, lvl) return max(0.75, 1.5 * 0.985 ^ (lvl or self:ToolLevel(prof))) end
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
  self:ProfSkillUp(f, (i - 1) * 50)
  self.lastMineOre, self.lastMineMat, self.lastMineGold, self.lastMineFamily = got, op[2], gold, f
  return true
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
        cost = OPS[i].cost * 2e5 * 500 ^ t, name = o[1] .. " profits x3", icon = o[4] }
    end
  end
  for t = 0, 2 do
    list[#list + 1] = { id = k .. "_all" .. t, kind = "profit", op = 0, mult = 3, family = k,
      cost = 1e9 * 1e4 ^ t, name = "All " .. f.tab .. " profits x3", icon = f.icon }
  end
  table.sort(list, function(a, b) return a.cost < b.cost end)
  TCF.UPGRADES[k] = list
end

function TCF:BuyOp(prof, i, count)
  local f = famOf(self, prof)
  local s = S(self)
  if count == "max" then count = self:OpMaxBuy(f, i) end
  if not count or count < 1 then return false end
  local cost = self:OpCost(f, i, count)
  if not self:SpendGold(cost) then return false end
  local st = s.ops[f][i]
  local before = combinedN(self, i)
  st.n = st.n + count
  local after = combinedN(self, i)
  for ms, chest in pairs(MILESTONE_CHEST) do
    local key = f .. i .. "_" .. ms
    -- once per spot across all families (older saves may hold another family's key)
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
  self:Print(string.format("A %s now works %s for you.", fam.hire, fam.ops[i][1]), true)
  self:MarkDirty()
  return true
end
TCF.HireHelper = TCF.HireForeman

function TCF:BuyUpgrade(id)
  local s = S(self)
  for _, k in ipairs(FAM_KEYS) do
    for _, u in ipairs(TCF.UPGRADES[k]) do
      if u.id == id then
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
-- Every key press in WoW waters the garden. Gathering spots only run when you start
-- them yourself (click the spot) or once a helper works them.
function TCF:ProfTap()
  if not (self.db and self.db.trade) then return end
  if self.GardenTap and self:ProfUnlocked("herbalism") then self:GardenTap() end
end

local function produce(self, s, f, i, cycles)
  self:EarnGold(self:OpRevenue(f, i) * cycles)
  local op = TCF.FAMILIES[f].ops[i]
  s.mats[op[2]] = (s.mats[op[2]] or 0) + cycles * self:OpMatsPerCycle(f, i)
end

-- Advance everything by dt seconds. offline = only automated things run. Helpers of every
-- family keep working, whichever class the cat is right now.
function TCF:ProfAdvance(dt, offline)
  local s = S(self)
  for _, f in ipairs(FAM_KEYS) do
    for i, st in ipairs(s.ops[f]) do
      if st.n > 0 and (st.mgr or (st.run and not offline)) then
        st.p = st.p + dt / self:OpCycleTime(f, i)
        if st.p >= 1 then
          local cycles = st.mgr and floor(st.p) or 1
          produce(self, s, f, i, cycles)
          st.p = st.mgr and (st.p - cycles) or 0
          if not st.mgr then st.run = false end
        end
      end
    end
  end
  for _, mod in ipairs(TCF.PROF_MODULES) do
    if self:ProfUnlocked(mod.key) then mod.advance(self, dt, offline) end
  end
  s.last = time()
end
TCF.PROF_MODULES = TCF.PROF_MODULES or {}

function TCF:ProfessionsTick(login, dt)
  local s = S(self)
  if login then
    local away = min(TCF.PROF_OFFLINE_CAP, max(0, time() - (s.last or time())))
    if away > 60 then
      local before = s.gold
      self:ProfAdvance(away, true)
      if s.gold > before then
        self:Print(string.format("While you were away your professions earned %s Trade Gold.", TCF.GoldStr(s.gold - before)))
      end
    end
    s.last = time()
    return
  end
  self:ProfAdvance(dt or 0.25)
end

---------------------------------------------------------------- renown (prestige)
function TCF:RenownOnReset()
  local s = S(self)
  return max(0, floor(math.sqrt(s.lifetime / 1e8)) - s.renown)
end

-- Sells everything bought with Trade Gold for permanent Renown. Skills, known
-- recipes, materials, bandages, dishes and unlocked professions are kept.
function TCF:PrestigeTrade()
  local s = S(self)
  local gain = self:RenownOnReset()
  if gain < 5 then return false end
  s.renown = s.renown + gain
  s.renownEver = max(s.renownEver, s.renown)
  s.prestiges = s.prestiges + 1
  s.gold = 0
  s.upgrades = {}
  for _, f in ipairs(FAM_KEYS) do
    s.tools[f] = 0
    for i = 1, 6 do s.ops[f][i] = freshOp() end
  end
  for _, mod in ipairs(TCF.PROF_MODULES) do if mod.reset then mod.reset(self, s) end end
  local coins = min(1000, gain * 3)
  self:AddCoins(coins)
  self:Print(string.format("Your cat sold its business for |cffffd100%d Renown|r (+%d%% profits forever) and %d TapCoins.", gain, gain * 2, coins), true)
  for _, p in ipairs(TCF.PROFESSIONS) do
    if p.renown > 0 and s.renownEver >= p.renown and s.renownEver - gain < p.renown then
      self:Print("You can now learn |cffffd100" .. p.name .. "|r.", true)
    end
  end
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

-- Gear recipes from CraftData.lua (TCF.CRAFT_RECIPES[craftKey] = { { gear, skill, mats }, ... }),
-- after the cosmetics, sorted by skill. Unknown items and malformed rows are skipped.
do
  local src = type(TCF.CRAFT_RECIPES) == "table" and TCF.CRAFT_RECIPES or {}
  for _, k in ipairs(FAM_KEYS) do
    local ck = TCF.FAMILIES[k].craft
    local add = {}
    for _, r in ipairs(type(src[ck]) == "table" and src[ck] or {}) do
      if type(r) == "table" and r.gear and TCF.GEAR and TCF.GEAR[r.gear] and type(r.mats) == "table" then
        add[#add + 1] = { gear = r.gear, skill = tonumber(r.skill) or 1, mats = r.mats, prof = ck }
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

function TCF:RecipeItem(r)
  if r.gear then return TCF.GEAR and TCF.GEAR[r.gear] end
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

function TCF:Craft(r)
  if not self:CanCraft(r) then return false end
  local s = S(self)
  for m, n in pairs(r.mats) do s.mats[m] = s.mats[m] - n end
  self.db.stats.crafted = (self.db.stats.crafted or 0) + 1
  -- crafting skills (Blacksmithing, Leatherworking, Tailoring) improve WoW style
  if TCF.CRAFT_FAMILY[r.prof] then self:ProfSkillUp(r.prof, r.skill or 1) end
  if r.gear then
    self:GrantGear(self:RecipeItem(r), "Crafted", true)
  else
    local it = TCF.ITEMS[r.item]
    self:GrantItem(it, "Crafted", true)
    if it.slot == "skin" then self:Print("Wear your new " .. TCF.ItemLink(it) .. " skin from the Appearance tab.", true) end
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
