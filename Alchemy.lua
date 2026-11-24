-- TapCatForever: Alchemy (1.6.7). Herbs from the garden brew into potions in Herbalism's
-- Crafting list (classic elixirs and flasks). Brewing raises Herbalism skill like harvesting.
-- Drink a potion for a buff: one potion at a time (a new one replaces it), next to the Well Fed
-- buff from Cooking, and both count (TCF:FoodBuff multiplies them). The Alchemy Lab garden
-- upgrade makes potions last twice as long. Potions are kept per cat, like herbs.
local ADDON, TCF = ...

local floor, min, max = math.floor, math.min, math.max

-- key, name, icon, buff kind (Cooking.lua TCF.BUFF_TEXT), value, minutes, skill, herbs, quality
TCF.POTIONS = {
  { "p_lion",      "Elixir of Lion's Strength",   "INV_Potion_15",  "dmg",     0.05, 30,  1,   { earthroot = 2, silverleaf = 2 }, 1 },
  { "p_fort",      "Elixir of Minor Fortitude",   "INV_Potion_43",  "hp",      0.05, 30,  30,  { earthroot = 3, peacebloom = 2 }, 1 },
  { "p_swift",     "Swiftness Potion",            "INV_Potion_95",  "mining",  0.15, 30,  60,  { swiftthistle = 1, briarthorn = 2 }, 2 },
  { "p_wisdom",    "Elixir of Wisdom",            "INV_Potion_08",  "xp",      0.10, 30,  90,  { mageroyal = 3, stranglekelp = 2 }, 2 },
  { "p_waterbr",   "Elixir of Water Breathing",   "INV_Potion_06",  "fishing", 0.50, 60,  110, { stranglekelp = 4, bruiseweed = 2 }, 2 },
  { "p_ogre",      "Elixir of Ogre's Strength",   "INV_Potion_61",  "dmg",     0.08, 30,  150, { kingsblood = 2, earthroot = 3 }, 2 },
  { "p_fort2",     "Elixir of Fortitude",         "INV_Potion_44",  "hp",      0.10, 60,  175, { steelbloom = 3, goldthorn = 2 }, 2 },
  { "p_dreamless", "Dreamless Sleep Potion",      "INV_Potion_83",  "xp",      0.20, 60,  200, { khadgar = 2, liferoot = 2 }, 3 },
  { "p_nature",    "Nature Protection Potion",    "INV_Potion_22",  "garden",  0.50, 60,  215, { liferoot = 3, purplelotus = 2 }, 3 },
  { "p_arthas",    "Gift of Arthas",              "INV_Potion_28",  "all",     0.08, 60,  240, { arthastears = 2, blindweed = 2 }, 3 },
  { "p_giants",    "Elixir of the Giants",        "INV_Potion_61",  "dmg",     0.12, 60,  255, { sungrass = 2, gromsblood = 2 }, 3 },
  { "p_superdef",  "Elixir of Superior Defense",  "INV_Potion_66",  "hp",      0.15, 60,  265, { sansam = 2, silversage = 1, wildvine = 1 }, 3 },
  { "p_mongoose",  "Elixir of the Mongoose",      "INV_Potion_32",  "dmg",     0.15, 60,  280, { silversage = 2, plaguebloom = 2 }, 3 },
  { "p_gnature",   "Greater Nature Protection Potion", "INV_Potion_22", "garden", 1.00, 60, 290, { icecap = 2, liferoot = 2, wildvine = 1 }, 3 },
  { "p_titans",    "Flask of the Titans",         "INV_Potion_62",  "hp",      0.30, 120, 300, { gromsblood = 10, lotus = 1 }, 4 },
  { "p_power",     "Flask of Supreme Power",      "INV_Potion_41",  "dmg",     0.30, 120, 300, { dreamfoil = 10, silversage = 5, lotus = 1 }, 4 },
  { "p_wisdom2",   "Flask of Distilled Wisdom",   "INV_Potion_97",  "xp",      0.30, 120, 300, { dreamfoil = 7, icecap = 3, lotus = 1 }, 4 },
}
TCF.POTION_BY_KEY = {}
-- a potion as the Crafting list shows it (an item-like table: id, name, icon, rarity)
for _, p in ipairs(TCF.POTIONS) do
  local it = { id = p[1], name = p[2], icon = p[3], kind = p[4], value = p[5], minutes = p[6], skill = p[7], mats = p[8],
               rarity = p[9], potion = true }
  TCF.POTION_BY_KEY[p[1]] = it
  -- what a potion sells for: about what its herbs are worth, and a bit more
  local worth = 0
  for k, n in pairs(p[8]) do
    local m = TCF.MAT_BY_KEY and TCF.MAT_BY_KEY[k]
    worth = worth + (m and m.value or 0) * n
  end
  TCF.AddMat(p[1], p[2], p[3], floor(worth * 1.2), "herbalism")
end

-- the recipes: after the herbal cosmetics in Herbalism's Crafting list
do
  local list = TCF.RECIPES.herbalism
  for _, p in ipairs(TCF.POTIONS) do
    list[#list + 1] = { potion = p[1], mats = p[8], skill = p[7], prof = "herbalism" }
  end
  -- each potion teaches up to its teach level, like seeds (no gap leaves you stuck)
  local brews = {}
  for _, r in ipairs(list) do if r.potion then brews[#brews + 1] = r end end
  TCF.SetTeachLevels(brews, function(r) return r.skill end, function(r, t) r.teach = t end)
end

-- "+10% cat XP for 30 minutes"
function TCF.PotionEffectText(it, minutes)
  return string.format("+%d%% %s for %s", floor(it.value * 100 + 0.5), TCF.BUFF_TEXT[it.kind] or it.kind,
    TCF.FormatDuration((minutes or it.minutes) * 60))
end

local function A(self)
  local s = TCF:ProfState()
  if type(s.alch) ~= "table" then s.alch = {} end
  return s.alch, s
end
TCF.AlchemyState = A

-- minutes a potion lasts for this cat (the Alchemy Lab doubles it)
function TCF:PotionMinutes(it)
  local g = self.GardenState and self:GardenState()
  return it.minutes * ((g and g.up and g.up.alchemylab) and 2 or 1)
end

-- drink one: its buff replaces the potion buff you had
function TCF:DrinkPotion(key)
  local a, s = A(self)
  local it = TCF.POTION_BY_KEY[key]
  if not it or (s.mats[key] or 0) < 1 then return false, "You don't have one." end
  s.mats[key] = s.mats[key] - 1
  local mins = self:PotionMinutes(it)
  a.buff = { key = key, kind = it.kind, value = it.value, ["until"] = time() + mins * 60 }
  self:Print(string.format("%s: %s.", it.name, TCF.PotionEffectText(it, mins)), true)
  self:PlaySound("click")
  self:MarkDirty(); self:RefreshAll()
  return true
end

-- the active potion buff of a cat, or nil
function TCF:PotionActive(class)
  local db = self.db
  if not db then return nil end
  local cd = db.classData and db.classData[class or self.tradeClass or db.class]
  local s = cd and type(cd.trade) == "table" and cd.trade
  local b = s and type(s.alch) == "table" and s.alch.buff
  if not b or (tonumber(b["until"]) or 0) < time() then return nil end
  return b
end

-- the multiplier from the potion buff for a system (TCF:FoodBuff multiplies it in)
function TCF:PotionBuff(kind, class)
  local b = self:PotionActive(class)
  if not b then return 1 end
  if b.kind == kind or (b.kind == "all" and (kind == "dmg" or kind == "hp")) then return 1 + (tonumber(b.value) or 0) end
  return 1
end

-- "Elixir of Wisdom: +10% cat XP (22m left)", or nil
function TCF:PotionLine(class)
  local b = self:PotionActive(class)
  local it = b and TCF.POTION_BY_KEY[b.key]
  if not it then return nil end
  return string.format("%s: +%d%% %s (%s left)", it.name, floor(b.value * 100 + 0.5), TCF.BUFF_TEXT[b.kind] or b.kind,
    TCF.FormatDuration(b["until"] - time()))
end
