-- TapCatForever: Herbalism, a garden. Plant seeds in plots; they grow in real time.
-- Click a growing plot (or just press keys while playing) to water it. Harvest for
-- herbs and Trade Gold. Bramble the gardener harvests and replants for you, also offline,
-- and learns more as you train it (Apprentice to Master).
-- (1.6.7) Each plot remembers the seed to grow there (g.want[i]): right-click a plot to grow the
-- seed you picked there from its next harvest on, shift-right-click to dig it up and plant it now,
-- or set every plot at once. Rare herbs turn up in some harvests: Swiftthistle, Wildvine and
-- Black Lotus. Herbs brew into potions in Crafting (Alchemy.lua).
local ADDON, TCF = ...

local floor, min, max, random = math.floor, math.min, math.max, math.random

-- key, name, icon, grow seconds, seed cost, sell gold per herb, skill needed (sorted by skill)
-- rare = { herb, chance }: a harvest of this herb sometimes brings a rare one too
TCF.SEEDS = {
  { "peacebloom",  "Peacebloom",          "INV_Misc_Flower_02",       60,    3e3,   4e3,    1 },
  { "silverleaf",  "Silverleaf",          "INV_Misc_Herb_10",         120,   8e3,   1.1e4,  1 },
  { "earthroot",   "Earthroot",           "INV_Misc_Herb_07",         150,   1.3e4, 1.8e4,  15 },
  { "mageroyal",   "Mageroyal",           "INV_Jewelry_Talisman_03",  300,   4e4,   6e4,    50, rare = { "swiftthistle", 0.05 } },
  { "briarthorn",  "Briarthorn",          "INV_Misc_Root_01",         480,   9e4,   1.35e5, 70, rare = { "swiftthistle", 0.05 } },
  { "stranglekelp","Stranglekelp",        "INV_Misc_Herb_11",         600,   1.4e5, 2.1e5,  85 },
  { "bruiseweed",  "Bruiseweed",          "INV_Misc_Herb_01",         780,   2e5,   3.2e5,  100 },
  { "steelbloom",  "Wild Steelbloom",     "INV_Misc_Flower_01",       1020,  3e5,   4.9e5,  115 },
  { "kingsblood",  "Kingsblood",          "INV_Misc_Herb_03",         1200,  4e5,   6.5e5,  125 },
  { "liferoot",    "Liferoot",            "INV_Misc_Root_02",         1680,  8.5e5, 1.4e6,  145 },
  { "fadeleaf",    "Fadeleaf",            "INV_Misc_Herb_12",         2100,  1.5e6, 2.5e6,  160 },
  { "goldthorn",   "Goldthorn",           "INV_Misc_Herb_15",         2340,  2e6,   3.3e6,  170 },
  { "khadgar",     "Khadgar's Whisker",   "INV_Misc_Herb_08",         2760,  3e6,   5.1e6,  185 },
  { "wintersbite", "Wintersbite",         "INV_Misc_Flower_03",       3060,  4e6,   6.8e6,  195 },
  { "firebloom",   "Firebloom",           "INV_Misc_Herb_19",         3420,  5.2e6, 9.1e6,  205, rare = { "wildvine", 0.04 } },
  { "sungrass",    "Sungrass",            "INV_Misc_Herb_18",         3600,  6e6,   1.05e7, 210, rare = { "lotus", 0.01 } },
  { "purplelotus", "Purple Lotus",        "INV_Misc_Herb_17",         3900,  7.3e6, 1.3e7,  215, rare = { "wildvine", 0.04 } },
  { "arthastears", "Arthas' Tears",       "INV_Misc_Herb_13",         4680,  1.1e7, 2e7,    225 },
  { "blindweed",   "Blindweed",           "INV_Misc_Herb_14",         5580,  1.6e7, 3e7,    235 },
  { "ghostshroom", "Ghost Mushroom",      "INV_Mushroom_08",          6600,  2.5e7, 4.5e7,  245 },
  { "dreamfoil",   "Dreamfoil",           "INV_Misc_Herb_DreamFoil",  7200,  3e7,   5.5e7,  250, rare = { "lotus", 0.01 } },
  { "gromsblood",  "Gromsblood",          "INV_Misc_Herb_16",         7560,  3.4e7, 6.2e7,  255, rare = { "wildvine", 0.04 } },
  { "sansam",      "Golden Sansam",       "INV_Misc_Herb_SansamRoot", 7980,  3.8e7, 7.1e7,  260, rare = { "lotus", 0.01 } },
  { "silversage",  "Mountain Silversage", "INV_Misc_Herb_MountainSilverSage", 8880, 4.9e7, 9e7, 270, rare = { "lotus", 0.01 } },
  { "plaguebloom", "Plaguebloom",         "INV_Misc_Herb_PlagueBloom", 9840, 6.2e7, 1.2e8,  280, rare = { "lotus", 0.01 } },
  { "icecap",      "Icecap",              "INV_Misc_Herb_IceCap",     10920, 7.9e7, 1.5e8,  290, rare = { "lotus", 0.01 } },
}
TCF.SEED_BY_KEY = {}
for i, sd in ipairs(TCF.SEEDS) do
  TCF.SEED_BY_KEY[sd[1]] = sd
  sd.index = i
  TCF.AddMat(sd[1], sd[2], sd[3], sd[6] / 4, "herbalism")
end
-- 1.6: each seed teaches up to its teach level (Professions.lua TCF.SetTeachLevels), so no gap
-- between two seeds leaves you stuck
TCF.SetTeachLevels(TCF.SEEDS, function(sd) return sd[7] end, function(sd, t) sd.teach = t end)
-- rare herbs: they come with some harvests, never from a seed
TCF.RARE_HERBS = {
  { key = "swiftthistle", name = "Swiftthistle", icon = "INV_Misc_Herb_04",          value = 2e5 },
  { key = "wildvine",     name = "Wildvine",     icon = "INV_Misc_Herb_02",          value = 5e6 },
  { key = "lotus",        name = "Black Lotus",  icon = "INV_Misc_Herb_BlackLotus",  value = 5e7 },
}
TCF.RARE_BY_KEY = {}
for _, r in ipairs(TCF.RARE_HERBS) do
  TCF.RARE_BY_KEY[r.key] = r
  TCF.AddMat(r.key, r.name, r.icon, r.value, "herbalism")
end
-- which seeds bring each rare herb ("Mageroyal or Briarthorn")
function TCF.RareSources(key)
  local names = {}
  for _, sd in ipairs(TCF.SEEDS) do if sd.rare and sd.rare[1] == key then names[#names + 1] = sd[2] end end
  if #names <= 1 then return names[1] or "" end
  return table.concat(names, ", ", 1, #names - 1) .. " or " .. names[#names]
end

TCF.GARDEN_MAX_PLOTS = 12
-- one-time garden upgrades (Trade Gold)
TCF.GARDEN_UPGRADES = {
  { key = "rainbarrel", name = "Rain Barrel",     desc = "Watering (clicking a plot, or key presses while you play) helps three times as much.", cost = 1e5 },
  { key = "compost",    name = "Compost",         desc = "Plants grow 50% faster.",                                cost = 2e6 },
  { key = "alchemylab", name = "Alchemy Lab",     desc = "Potions you drink last twice as long.",                  cost = 1e7 },
  { key = "greenhouse", name = "Greenhouse",      desc = "Twice the herbs and gold from every harvest.",           cost = 2e7 },
  { key = "moonwell",   name = "Moonwell",        desc = "Rare herbs (Swiftthistle, Wildvine, Black Lotus) turn up twice as often.", cost = 2e8 },
  { key = "soil",       name = "Enchanted Soil",  desc = "Plants grow twice as fast again.",                       cost = 5e8 },
}
-- Bramble the gardener: hire it, then train it rank by rank (each rank keeps the earlier ones)
TCF.GARDENER_NAME = "Bramble"
TCF.GARDENER = {
  { rank = "Apprentice", cost = 5e5, perk = "Harvests ripe plots and replants each with its seed, even offline." },
  { rank = "Journeyman", cost = 5e6, perk = "Waters as it works: plants grow 25% faster." },
  { rank = "Expert",     cost = 5e7, perk = "Saves seeds: one replant in three costs nothing." },
  { rank = "Artisan",    cost = 5e8, perk = "Knows the herbs: one more herb from every harvest." },
  { rank = "Master",     cost = 5e9, perk = "Has a nose for rare herbs: they turn up twice as often." },
}

local function G(self)
  local s = TCF:ProfState()
  s.garden = s.garden or { plots = {}, n = 3, up = {} }
  local g = s.garden
  if type(g.want) ~= "table" then g.want = {} end
  -- before 1.6.7 the gardener was one upgrade: that is rank 1
  if g.up.gardener and (g.gl or 0) < 1 then g.gl = 1 end
  return g, s
end
TCF.GardenState = G

function TCF:GardenerLevel()
  local g = G(self)
  return g.gl or 0
end

function TCF:GardenSpeed()
  local g = G(self)
  local m = 1
  if g.up.compost then m = m * 1.5 end
  if g.up.soil then m = m * 2 end
  if (g.gl or 0) >= 2 then m = m * 1.25 end
  return m * (self.FoodBuff and self:FoodBuff("garden") or 1)
end
-- how much more often rare herbs turn up
function TCF:RareMult()
  local g = G(self)
  local m = 1
  if g.up.moonwell then m = m * 2 end
  if (g.gl or 0) >= 5 then m = m * 2 end
  return m
end
local function waterMult(g) return g.up.rainbarrel and 3 or 1 end

function TCF:PlotCost(n) return 2e4 * 3 ^ (n - 3) end

function TCF:BuyPlot()
  local g = G(self)
  if g.n >= TCF.GARDEN_MAX_PLOTS then return false end
  if not self:SpendGold(self:PlotCost(g.n + 1)) then return false end
  g.n = g.n + 1
  self:MarkDirty()
  return true
end

-- hire or train the gardener: the next rank
function TCF:TrainGardener()
  local g = G(self)
  local nxt = TCF.GARDENER[(g.gl or 0) + 1]
  if not nxt then return false, "Bramble is already a Master Gardener." end
  if not self:SpendGold(nxt.cost) then return false, "Not enough Trade Gold: " .. TCF.GoldStr(nxt.cost) .. "." end
  g.gl = (g.gl or 0) + 1
  g.up.gardener = true
  self:MarkDirty()
  return true
end

function TCF:BuyGardenUpgrade(key)
  local g = G(self)
  if key == "gardener" then
    if (g.gl or 0) >= 1 then return false end
    return self:TrainGardener()
  end
  for _, u in ipairs(TCF.GARDEN_UPGRADES) do
    if u.key == key and not g.up[key] and self:SpendGold(u.cost) then g.up[key] = true; self:MarkDirty(); return true end
  end
  return false
end

local function canGrow(self, sd)
  return sd and self:ProfSkill("herbalism") >= sd[7]
end

function TCF:Plant(i, seedKey)
  local g = G(self)
  local sd = TCF.SEED_BY_KEY[seedKey]
  if not sd or i > g.n or (g.plots[i] and g.plots[i].seed) then return false end
  if not canGrow(self, sd) then return false, "Needs Herbalism skill " .. sd[7] .. " to plant " .. sd[2] .. "." end
  if not self:SpendGold(sd[5]) then return false, "Not enough Trade Gold: " .. sd[2] .. " seeds cost " .. TCF.GoldStr(sd[5]) .. "." end
  g.plots[i] = { seed = seedKey, grown = 0 }
  g.want[i] = seedKey
  return true
end

-- the seed a plot grows from its next planting on (what it grows now, or what you picked for it)
function TCF:PlotWant(i)
  local g = G(self)
  local p = g.plots[i]
  return g.want[i] or (p and p.seed)
end

-- grow seedKey in plot i from its next harvest on (the gardener replants it with that)
function TCF:PlotSetNext(i, seedKey)
  local g = G(self)
  local sd = TCF.SEED_BY_KEY[seedKey]
  if not sd or i < 1 or i > g.n then return false end
  if not canGrow(self, sd) then return false, "Needs Herbalism skill " .. sd[7] .. " to grow " .. sd[2] .. "." end
  g.want[i] = seedKey
  self:MarkDirty()
  return true
end

-- dig up what grows in plot i (it is lost) and plant seedKey there now
function TCF:PlotDig(i, seedKey)
  local g = G(self)
  local sd = TCF.SEED_BY_KEY[seedKey]
  if not sd or i < 1 or i > g.n then return false end
  if not canGrow(self, sd) then return false, "Needs Herbalism skill " .. sd[7] .. " to plant " .. sd[2] .. "." end
  if (self:ProfState().gold or 0) < sd[5] then return false, "Not enough Trade Gold: " .. sd[2] .. " seeds cost " .. TCF.GoldStr(sd[5]) .. "." end
  g.plots[i] = nil
  local ok, why = self:Plant(i, seedKey)
  self:MarkDirty()
  return ok, why
end

-- every plot grows seedKey from its next harvest on; empty plots are planted now (while affordable)
function TCF:GardenPlantAll(seedKey)
  local g = G(self)
  local sd = TCF.SEED_BY_KEY[seedKey]
  if not sd then return false end
  if not canGrow(self, sd) then return false, "Needs Herbalism skill " .. sd[7] .. " to grow " .. sd[2] .. "." end
  local planted = 0
  for i = 1, g.n do
    g.want[i] = seedKey
    if not (g.plots[i] and g.plots[i].seed) and self:Plant(i, seedKey) then planted = planted + 1 end
  end
  self:MarkDirty()
  return true, planted
end

local function harvest(self, g, s, i)
  local p = g.plots[i]
  local sd = TCF.SEED_BY_KEY[p.seed]
  local n = 1 + floor(self:ProfSkill("herbalism") / 100)
  if (g.gl or 0) >= 4 then n = n + 1 end
  if g.up.greenhouse then n = n * 2 end
  s.mats[sd[1]] = (s.mats[sd[1]] or 0) + n
  self:EarnGold(sd[6] * n)
  local rare = sd.rare
  if rare then
    local chance = rare[2] * self:RareMult()
    if rare[1] == "lotus" then chance = (rare[2] + self:ProfSkill("herbalism") / 30000) * self:RareMult() end
    if random() < chance then
      s.mats[rare[1]] = (s.mats[rare[1]] or 0) + 1
      g.rares = (g.rares or 0) + 1
      if rare[1] == "lotus" and not self.tradeQuiet then self.gardenMutation = true end
    end
  end
  g.harvests = (g.harvests or 0) + 1
  self:ProfSkillUp("herbalism", sd.teach or sd[7])
  local seed = p.seed
  g.plots[i] = nil
  return seed
end

-- Click a plot: plant the chosen seed, water it, or harvest it
function TCF:PlotClick(i, seedKey)
  local g, s = G(self)
  local p = g.plots[i]
  if not p or not p.seed then return self:Plant(i, seedKey or g.want[i]) end
  local sd = TCF.SEED_BY_KEY[p.seed]
  if p.grown >= sd[4] then harvest(self, g, s, i); self:MarkDirty(); return true end
  p.grown = min(sd[4], p.grown + 2 * waterMult(g) * self:GardenSpeed())  -- watering
  return true
end

-- Every key press in WoW waters the whole garden a little
function TCF:GardenTap()
  local g = G(self)
  local sp = self:GardenSpeed() * waterMult(g)
  for i = 1, g.n do
    local p = g.plots[i]
    if p and p.seed then p.grown = min(TCF.SEED_BY_KEY[p.seed][4], p.grown + 0.3 * sp) end
  end
end

-- the gardener pays for a seed (rank 3: one in three is free)
local function gardenerSeed(self, g, sd)
  if (g.gl or 0) >= 3 and random() < 1 / 3 then g.saved = (g.saved or 0) + 1; return true end
  return self:SpendGold(sd[5])
end

local function advance(self, dt, offline)
  local g, s = G(self)
  local sp = self:GardenSpeed()
  local gardener = (g.gl or 0) >= 1
  for i = 1, g.n do
    local p = g.plots[i]
    if gardener and not (p and p.seed) then
      -- an empty plot with a seed to grow: the gardener plants it
      local sd = TCF.SEED_BY_KEY[g.want[i] or ""]
      if canGrow(self, sd) and gardenerSeed(self, g, sd) then
        g.plots[i] = { seed = sd[1], grown = 0 }
        p = g.plots[i]
      end
    end
    if p and p.seed then
      local sd = TCF.SEED_BY_KEY[p.seed]
      p.grown = p.grown + dt * sp
      if gardener then
        -- harvest every finished crop in this time and replant (with the plot's seed) while affordable
        local guard = 0
        while p and p.grown >= sd[4] and guard < 5000 do
          guard = guard + 1
          local over = p.grown - sd[4]
          local seed = harvest(self, g, s, i)
          local nextSd = TCF.SEED_BY_KEY[g.want[i] or seed]
          if not canGrow(self, nextSd) then nextSd = TCF.SEED_BY_KEY[seed] end
          g.want[i] = nextSd[1]
          if gardenerSeed(self, g, nextSd) then
            -- growth left over carries to the new crop
            g.plots[i] = { seed = nextSd[1], grown = over }
            p, sd = g.plots[i], nextSd
          else p = nil end
        end
      elseif p.grown > sd[4] then
        p.grown = sd[4]
      end
    end
  end
end

table.insert(TCF.PROF_MODULES, { key = "herbalism", advance = advance,
  reset = function(self, s)
    if s.garden then s.garden.plots = {}; s.garden.n = 3; s.garden.up = {}; s.garden.gl = nil; s.garden.want = {} end
  end })
