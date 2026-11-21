-- TapCatForever: gathering professions. Pick up to two; the cat gathers real
-- materials over time (also while offline, up to 12 hours), skill rises from
-- 1 to 300, and recipes turn materials into cosmetics you can't get elsewhere.
local ADDON, TCF = ...

local floor, min, max, random = math.floor, math.min, math.max, math.random

TCF.GATHER_SECONDS = 6 * 60          -- one gather every 6 minutes
TCF.GATHER_OFFLINE_CAP = 12 * 3600   -- offline gathering stops after 12 hours
TCF.MAX_PROFESSIONS = 2

-- materials: key, name, icon, min skill, sell value, rare chance (rare = only sometimes)
TCF.PROFESSIONS = {
  { key = "mining", name = "Mining", icon = "Trade_Mining", verb = "mined",
    mats = {
      { "copper", "Copper Ore", "INV_Ore_Copper_01", 1, 1 },
      { "tin", "Tin Ore", "INV_Ore_Tin_01", 65, 1 },
      { "iron", "Iron Ore", "INV_Ore_Iron_01", 125, 2 },
      { "mithril", "Mithril Ore", "INV_Ore_Mithril_02", 175, 2 },
      { "thorium", "Thorium Ore", "INV_Ore_Thorium_02", 230, 3 },
      { "arcane", "Arcane Crystal", "INV_Misc_Gem_Crystal_01", 275, 20, 0.04 },
    } },
  { key = "herbalism", name = "Herbalism", icon = "Trade_Herbalism", verb = "picked",
    mats = {
      { "peacebloom", "Peacebloom", "INV_Misc_Flower_02", 1, 1 },
      { "mageroyal", "Mageroyal", "INV_Jewelry_Talisman_03", 50, 1 },
      { "kingsblood", "Kingsblood", "INV_Misc_Herb_03", 125, 2 },
      { "sungrass", "Sungrass", "INV_Misc_Herb_18", 200, 2 },
      { "dreamfoil", "Dreamfoil", "INV_Misc_Herb_DreamFoil", 250, 3 },
      { "lotus", "Black Lotus", "INV_Misc_Herb_BlackLotus", 285, 40, 0.02 },
    } },
  { key = "skinning", name = "Skinning", icon = "INV_Misc_Pelt_Wolf_01", verb = "skinned",
    mats = {
      { "light", "Light Leather", "INV_Misc_LeatherScrap_03", 1, 1 },
      { "medium", "Medium Leather", "INV_Misc_LeatherScrap_05", 75, 1 },
      { "heavy", "Heavy Leather", "INV_Misc_LeatherScrap_07", 125, 2 },
      { "thick", "Thick Leather", "INV_Misc_LeatherScrap_08", 200, 2 },
      { "rugged", "Rugged Leather", "INV_Misc_LeatherScrap_02", 250, 3 },
      { "devilsaur", "Devilsaur Leather", "INV_Misc_Pelt_Bear_03", 260, 15, 0.06 },
      { "onyxscale", "Black Dragonscale", "INV_Misc_MonsterScales_10", 285, 40, 0.02 },
    } },
  { key = "fishing", name = "Fishing", icon = "Trade_Fishing", verb = "caught",
    mats = {
      { "smallfish", "Raw Brilliant Smallfish", "INV_Misc_Fish_02", 1, 1 },
      { "bristle", "Raw Bristle Whisker Catfish", "INV_Misc_Fish_05", 75, 1 },
      { "trout", "Raw Mithril Head Trout", "INV_Misc_Fish_08", 150, 2 },
      { "eel", "Stonescale Eel", "INV_Misc_Fish_36", 225, 3 },
      { "pinchy", "Mr. Pinchy", "INV_Misc_Fish_35", 250, 50, 0.01 },
    } },
}
TCF.PROF_BY_KEY = {}
TCF.MAT_BY_KEY = {}
for _, p in ipairs(TCF.PROFESSIONS) do
  TCF.PROF_BY_KEY[p.key] = p
  for _, m in ipairs(p.mats) do
    TCF.MAT_BY_KEY[m[1]] = { key = m[1], name = m[2], icon = m[3], skill = m[4], value = m[5], rare = m[6], prof = p.key }
  end
end

-- Recipes: cosmetics only obtainable by crafting. item = cosmetic id (Data.lua, source "craft")
TCF.RECIPES = {
  mining = {
    { item = "craft_copper_circlet", skill = 25,  mats = { copper = 12 } },
    { item = "craft_iron_greathelm", skill = 125, mats = { iron = 20, tin = 6 } },
    { item = "craft_mithril_medal",  skill = 175, mats = { mithril = 18 } },
    { item = "craft_thorium_axe",    skill = 230, mats = { thorium = 25, mithril = 10 } },
    { item = "craft_arcanite_reaper", skill = 275, mats = { arcane = 4, thorium = 40 } },
  },
  herbalism = {
    { item = "craft_peacebloom_crown", skill = 15,  mats = { peacebloom = 15 } },
    { item = "craft_mageroyal_bloom",  skill = 60,  mats = { mageroyal = 15 } },
    { item = "craft_kingsblood_aura",  skill = 150, mats = { kingsblood = 22 } },
    { item = "craft_dreamfoil_wreath", skill = 250, mats = { dreamfoil = 25, sungrass = 10 } },
    { item = "craft_lotus_bloom",      skill = 285, mats = { lotus = 3, dreamfoil = 30 } },
  },
  skinning = {
    { item = "craft_wolfpelt_cloak",  skill = 20,  mats = { light = 15 } },
    { item = "craft_raptor_hood",     skill = 125, mats = { heavy = 20, medium = 10 } },
    { item = "craft_thick_mantle",    skill = 200, mats = { thick = 25 } },
    { item = "craft_devilsaur_mantle", skill = 260, mats = { devilsaur = 4, rugged = 20 } },
    { item = "craft_onyxia_cloak",    skill = 285, mats = { onyxscale = 3, rugged = 30 } },
  },
  fishing = {
    { item = "craft_fishing_hat",    skill = 50,  mats = { smallfish = 20 } },
    { item = "craft_iron_pole",      skill = 150, mats = { trout = 20, bristle = 10 } },
    { item = "craft_murloc_bubbles", skill = 200, mats = { trout = 30 } },
    { item = "craft_eel_shield",     skill = 225, mats = { eel = 25 } },
    { item = "craft_pinchy_gift",    skill = 250, mats = { pinchy = 1, eel = 30 } },
  },
}

local function pstate(self)
  self.db.prof = self.db.prof or { known = {}, skill = {}, mats = {}, last = {} }
  return self.db.prof
end
TCF.ProfState = pstate

function TCF:LearnProfession(key)
  local ps = pstate(self)
  if ps.known[key] then return false end
  local n = 0
  for _ in pairs(ps.known) do n = n + 1 end
  if n >= TCF.MAX_PROFESSIONS then self:Print("Your cat already knows two professions. Unlearn one first."); return false end
  ps.known[key] = true
  ps.skill[key] = ps.skill[key] or 1
  ps.last[key] = time()
  self:Print("Your cat learned |cffffd100" .. TCF.PROF_BY_KEY[key].name .. "|r!")
  self:MarkDirty(); self:RefreshAll()
  return true
end

function TCF:UnlearnProfession(key)
  local ps = pstate(self)
  ps.known[key] = nil
  ps.skill[key] = nil
  ps.last[key] = nil
  self:MarkDirty(); self:RefreshAll()
end

local function skillUpChance(skill)
  if skill < 75 then return 1 elseif skill < 150 then return 0.75 elseif skill < 225 then return 0.5 else return 0.3 end
end

-- One gather: 1-3 of the best common material, sometimes a lower one, rarely a rare one.
function TCF:GatherOnce(key, quiet)
  local ps = pstate(self)
  local p = TCF.PROF_BY_KEY[key]
  local skill = ps.skill[key]
  local commons, rares = {}, {}
  for _, m in ipairs(p.mats) do
    if skill >= m[4] then
      if m[6] then rares[#rares + 1] = m else commons[#commons + 1] = m end
    end
  end
  local got = {}
  local pick = (#commons > 1 and random() < 0.3) and commons[#commons - 1] or commons[#commons]
  local n = random(1, 3)
  ps.mats[pick[1]] = (ps.mats[pick[1]] or 0) + n
  got[#got + 1] = n .. "x " .. pick[2]
  for _, r in ipairs(rares) do
    if random() < r[6] then
      ps.mats[r[1]] = (ps.mats[r[1]] or 0) + 1
      got[#got + 1] = "|cffa335ee" .. r[2] .. "|r"
      if not quiet then self:Print("Your cat found a rare " .. r[2] .. "!") end
    end
  end
  if skill < 300 and random() < skillUpChance(skill) then ps.skill[key] = skill + 1 end
  return got
end

-- Catch up on gathering since the last check (called every few seconds and at login)
function TCF:ProfessionsTick(login)
  local ps = pstate(self)
  local now = time()
  for key in pairs(ps.known) do
    local last = ps.last[key] or now
    local elapsed = min(now - last, TCF.GATHER_OFFLINE_CAP)
    local n = floor(elapsed / TCF.GATHER_SECONDS)
    if n > 0 then
      local before = ps.skill[key]
      for _ = 1, n do self:GatherOnce(key, login) end
      ps.last[key] = (now - last > TCF.GATHER_OFFLINE_CAP) and now or (last + n * TCF.GATHER_SECONDS)
      if login and n > 1 then
        self:Print(string.format("While you were away your cat %s %d times (%s skill %d -> %d).",
          TCF.PROF_BY_KEY[key].verb, n, TCF.PROF_BY_KEY[key].name, before, ps.skill[key]))
      end
      self:MarkDirty()
    end
  end
end

function TCF:GatherProgress(key)
  local ps = pstate(self)
  local last = ps.last[key] or time()
  return min(1, (time() - last) / TCF.GATHER_SECONDS)
end

function TCF:CanCraft(r)
  local ps = pstate(self)
  local prof
  for k, list in pairs(TCF.RECIPES) do for _, x in ipairs(list) do if x == r then prof = k end end end
  if not ps.known[prof] or ps.skill[prof] < r.skill then return false end
  for m, n in pairs(r.mats) do if (ps.mats[m] or 0) < n then return false end end
  return true
end

function TCF:Craft(r)
  if not self:CanCraft(r) then return false end
  local ps = pstate(self)
  for m, n in pairs(r.mats) do ps.mats[m] = ps.mats[m] - n end
  local it = TCF.ITEMS[r.item]
  self.db.stats.crafted = (self.db.stats.crafted or 0) + 1
  self:GrantItem(it, "Crafted", true)
  return true
end

function TCF:SellMaterial(key, n)
  local ps = pstate(self)
  local m = TCF.MAT_BY_KEY[key]
  n = min(n or 1, ps.mats[key] or 0)
  if n <= 0 then return end
  ps.mats[key] = ps.mats[key] - n
  local coins = floor(m.value * n / 4)
  if coins > 0 then self:AddCoins(coins) end
  self:Print(string.format("Sold %dx %s for %d TapCoins.", n, m.name, coins))
  self:MarkDirty(); self:RefreshAll()
end
