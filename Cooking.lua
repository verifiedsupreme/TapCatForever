-- TapCatForever: Cooking. Put up to three ingredients in the pot to experiment;
-- the right combination discovers a recipe. Dishes give a "Well Fed" buff (one at
-- a time, real-time duration). A sous-chef keeps cooking a recipe you know, offline too.
-- Ingredients: fish (Fishing), meat (Adventure beasts), herbs (Herbalism), spices (bought).
local ADDON, TCF = ...

local floor, min, max, random = math.floor, math.min, math.max, math.random

-- meat drops from Adventure enemies by level
TCF.MEATS = {
  { "wolfmeat", "Stringy Wolf Meat", "INV_Misc_Food_14", 1 },
  { "boarmeat", "Boar Ribs",         "INV_Misc_Food_16", 12 },
  { "raptor",   "Raptor Flesh",      "INV_Misc_Food_06", 30 },
  { "egg",      "Giant Egg",         "INV_Egg_01",       40 },
  { "mystery",  "Mystery Meat",      "INV_Misc_Food_48", 50 },
}
for _, m in ipairs(TCF.MEATS) do TCF.AddMat(m[1], m[2], m[3], 2e3 * m[4], "cooking") end
TCF.SPICES = {
  { "mildspice", "Mild Spices", "INV_Misc_Food_Wheat_01", 1e3 },
  { "hotspice",  "Hot Spices",  "INV_Misc_Food_Wheat_02", 5e4 },
}
for _, sp in ipairs(TCF.SPICES) do TCF.AddMat(sp[1], sp[2], sp[3], sp[4] / 4, "cooking") end

-- recipes: key, name, icon, ingredients (sorted multiset), skill, buff type, buff value, minutes, hint
-- buff types: dmg (Adventure damage), hp (Adventure health), xp (cat XP from key presses),
--             mining (gathering profits: Mining, Skinning or Tailoring spots), garden (garden growth), fishing (rare catches), all (dmg+hp)
TCF.COOK_RECIPES = {
  { "d_wolf",    "Spiced Wolf Meat",     "INV_Misc_Food_14", { "mildspice", "wolfmeat" },                 1,   "dmg",     0.05, 30,  "Something with wolf and a pinch of spice." },
  { "d_smallfish","Brilliant Smallfish", "INV_Misc_Fish_02", { "smallfish", "smallfish" },                1,   "xp",      0.10, 30,  "Two of the smallest fish there are." },
  { "d_snapper", "Longjaw Mud Snapper",  "INV_Misc_Fish_04", { "longjaw", "mildspice" },                  50,  "mining",  0.25, 30,  "A muddy snapper, lightly spiced." },
  { "d_stew",    "Westfall Stew",        "INV_Misc_Food_15", { "boarmeat", "mildspice", "wolfmeat" },     75,  "hp",      0.10, 30,  "Two kinds of meat in one pot." },
  { "d_egg",     "Herb Baked Egg",       "INV_Misc_Food_57", { "egg", "peacebloom" },                     90,  "garden",  0.25, 60,  "An egg and a flower." },
  { "d_raptor",  "Roast Raptor",         "INV_Misc_Food_06", { "hotspice", "raptor" },                    150, "dmg",     0.08, 30,  "A raptor steak with a bit of heat." },
  { "d_cod",     "Rockscale Cod",        "INV_Misc_Fish_16", { "hotspice", "rockscale" },                 175, "dmg",     0.10, 30,  "A cod from Stranglethorn, with heat." },
  { "d_chili",   "Dragonbreath Chili",   "INV_Misc_Food_49", { "hotspice", "kingsblood", "mystery" },     200, "dmg",     0.15, 60,  "Mysterious meat, a royal herb and fire." },
  { "d_soup",    "Nightfin Soup",        "INV_Drink_17",     { "mageroyal", "nightfin" },                 225, "mining",  0.50, 60,  "A Feralas fish with a mage's herb." },
  { "d_omelet",  "Monster Omelet",       "INV_Misc_Food_34", { "egg", "egg", "hotspice" },                225, "hp",      0.20, 60,  "Lots of eggs. Spicy." },
  { "d_salmon",  "Smoked Sagefish",      "INV_Misc_Fish_21", { "sungrass", "whitescale" },                250, "xp",      0.25, 60,  "Salmon from Azshara smoked over a sunny herb." },
  { "d_mightfish","Mightfish Steak",     "INV_Misc_Fish_36", { "dreamfoil", "eel", "hotspice" },          275, "all",     0.20, 120, "An eel, a dreamy herb and spice." },
  { "d_feast",   "Pinchy's Luxury Feast","INV_Misc_Food_64", { "lotus", "mystery", "pinchy" },            300, "fishing", 2.00, 120, "Something only a wish could provide." },
}
TCF.COOK_BY_KEY = {}
for _, r in ipairs(TCF.COOK_RECIPES) do
  table.sort(r[4])
  TCF.COOK_BY_KEY[r[1]] = r
  TCF.AddMat(r[1], r[2], r[3], 1e4 * r[5], "cooking")
end
-- 1.6: skill-ups use each dish's teach level (Professions.lua TCF.SetTeachLevels)
TCF.SetTeachLevels(TCF.COOK_RECIPES, function(r) return r[5] end, function(r, t) r.teach = t end)
TCF.BUFF_TEXT = { dmg = "Adventure damage", hp = "Adventure health", xp = "cat XP from key presses", mining = "gathering profits",
  garden = "garden growth", fishing = "rare catch chance", all = "Adventure damage and health" }

TCF.COOK_UPGRADES = {
  { key = "chef",   name = "Hire a Sous-Chef",  desc = "Cooks your chosen recipe every 20 seconds while you have the ingredients, even offline.", cost = 3e6 },
  { key = "spices", name = "Spice Rack",        desc = "The sous-chef buys missing spices automatically (costs Trade Gold).",                       cost = 1e7 },
}

local function C(self)
  local s = TCF:ProfState()
  s.cook = s.cook or { known = {}, pot = {}, up = {}, chefRecipe = nil, cp = 0 }
  return s.cook, s
end
TCF.CookState = C

function TCF:BuyCookUpgrade(key)
  local c = C(self)
  for _, u in ipairs(TCF.COOK_UPGRADES) do
    if u.key == key and not c.up[key] and self:SpendGold(u.cost) then c.up[key] = true; self:MarkDirty(); return true end
  end
  return false
end

function TCF:BuySpice(key, n)
  local _, s = C(self)
  for _, sp in ipairs(TCF.SPICES) do
    if sp[1] == key and self:SpendGold(sp[4] * n) then s.mats[key] = (s.mats[key] or 0) + n; self:MarkDirty(); return true end
  end
end

-- the pot holds up to three ingredients
function TCF:PotAdd(key)
  local c, s = C(self)
  if #c.pot >= 3 then return false end
  local used = 0
  for _, k in ipairs(c.pot) do if k == key then used = used + 1 end end
  if (s.mats[key] or 0) <= used then return false end
  table.insert(c.pot, key)
  return true
end
function TCF:PotClear() C(self).pot = {} end

local function matchRecipe(list)
  local sorted = {}
  for i, k in ipairs(list) do sorted[i] = k end
  table.sort(sorted)
  local sig = table.concat(sorted, "+")
  for _, r in ipairs(TCF.COOK_RECIPES) do
    if table.concat(r[4], "+") == sig then return r end
  end
end

local function consume(s, list)
  for _, k in ipairs(list) do s.mats[k] = max(0, (s.mats[k] or 0) - 1) end
end

-- Cook what's in the pot. Returns result text, recipe (if any), discovered (bool)
function TCF:CookPot()
  local c, s = C(self)
  if #c.pot == 0 then return end
  local r = matchRecipe(c.pot)
  if r and self:ProfSkill("cooking") < r[5] then
    return "You're not skilled enough to cook this yet (needs " .. r[5] .. ").", nil, false
  end
  -- the pot doesn't reserve anything: selling, crafting or the sous-chef may have used
  -- the ingredients since they went in, so count them again
  local need = {}
  for _, k in ipairs(c.pot) do need[k] = (need[k] or 0) + 1 end
  for k, n in pairs(need) do
    if (s.mats[k] or 0) < n then
      c.pot = {}
      return "Some ingredients are no longer in your bags.", nil, false
    end
  end
  consume(s, c.pot)
  c.pot = {}
  if not r then
    -- a failed experiment rarely teaches anything (1 in 20 chance of a skill point)
    self:ProfSkillUp("cooking", self:ProfSkill("cooking") - 40)
    return "Burnt Mess. That didn't work...", nil, false
  end
  local discovered = not c.known[r[1]]
  c.known[r[1]] = true
  s.mats[r[1]] = (s.mats[r[1]] or 0) + 1
  self:ProfSkillUp("cooking", r.teach or r[5])
  if discovered then
    self.db.stats.recipesFound = (self.db.stats.recipesFound or 0) + 1
    self:Print("New recipe discovered: |cffffd100" .. r[2] .. "|r.", true)
    self:PlaySound("ach")
  end
  self:MarkDirty()
  return (discovered and "Discovered: " or "Cooked: ") .. r[2], r, discovered
end

-- Cook a known recipe directly (also used by the sous-chef)
function TCF:CookKnown(key, auto)
  local c, s = C(self)
  local r = TCF.COOK_BY_KEY[key]
  if not r or not c.known[key] then return false end
  local need = {}
  for _, k in ipairs(r[4]) do need[k] = (need[k] or 0) + 1 end
  for k, n in pairs(need) do
    if (s.mats[k] or 0) < n then
      local isSpice
      for _, sp in ipairs(TCF.SPICES) do if sp[1] == k then isSpice = sp end end
      if auto and isSpice and c.up.spices and self:SpendGold(isSpice[4] * 10) then s.mats[k] = (s.mats[k] or 0) + 10
      else return false end
    end
  end
  consume(s, r[4])
  s.mats[key] = (s.mats[key] or 0) + 1
  self:ProfSkillUp("cooking", r.teach or r[5])
  return true
end

-- Eat a dish: one Well Fed buff at a time (replaces the current one)
function TCF:EatDish(key)
  local c, s = C(self)
  local r = TCF.COOK_BY_KEY[key]
  if not r or (s.mats[key] or 0) < 1 then return false end
  s.mats[key] = s.mats[key] - 1
  c.buff = { key = key, kind = r[6], value = r[7], ["until"] = time() + r[8] * 60 }
  self:Print(string.format("Well Fed: +%d%% %s for %d minutes.", r[7] * 100, TCF.BUFF_TEXT[r[6]], r[8]), true)
  self:PlaySound("click")
  self:MarkDirty(); self:RefreshAll()
  return true
end

-- Multiplier from the active Well Fed buff for a system. A dish feeds the cat that ate it:
-- the buff is in that class's trade (class: default the current class).
function TCF:FoodBuff(kind, class)
  local db = self.db
  if not db then return 1 end
  if db.trade ~= nil then TCF:ProfState() end   -- an old shared trade is split first
  -- read without creating a trade for a cat that never had one (gear stats ask for every class)
  local cd = db.classData and db.classData[class or self.tradeClass or db.class]
  local s = cd and type(cd.trade) == "table" and cd.trade
  local b = s and s.cook and s.cook.buff
  -- (1.6.7) a potion (Alchemy.lua) counts on top of the dish
  local potion = self.PotionBuff and self:PotionBuff(kind, class) or 1
  if not b or b["until"] < time() then return potion end
  if b.kind == kind or (b.kind == "all" and (kind == "dmg" or kind == "hp")) then return (1 + b.value) * potion end
  return potion
end

-- Adventure: beasts drop meat for their level
function TCF:DropMeat(level)
  if not self:ProfUnlocked("cooking") or random() > 0.15 then return end
  local _, s = C(self)
  local pick = TCF.MEATS[1]
  for _, m in ipairs(TCF.MEATS) do if level >= m[4] then pick = m end end
  s.mats[pick[1]] = (s.mats[pick[1]] or 0) + 1
end

local function advance(self, dt, offline)
  local c = C(self)
  if c.up.chef and c.chefRecipe then
    c.cp = (c.cp or 0) + dt
    local guard = 0
    while c.cp >= 20 and guard < 5000 do
      guard = guard + 1
      c.cp = c.cp - 20
      if not self:CookKnown(c.chefRecipe, true) then c.cp = 0; break end
    end
  end
end

table.insert(TCF.PROF_MODULES, { key = "cooking", advance = advance,
  reset = function(self, s) if s.cook then s.cook.up = {}; s.cook.cp = 0 end end })
