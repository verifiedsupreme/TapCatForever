-- TapCatForever: Herbalism, a garden. Plant seeds in plots; they grow in real time.
-- Click a growing plot (or just press keys while playing) to water it. Harvest for
-- herbs and Trade Gold. A gardener harvests and replants for you, also offline.
-- Ripe Sungrass and Dreamfoil can mutate into Black Lotus.
local ADDON, TCF = ...

local floor, min, max, random = math.floor, math.min, math.max, math.random

-- key, name, icon, grow seconds, seed cost, sell gold per herb, skill needed
TCF.SEEDS = {
  { "peacebloom", "Peacebloom",  "INV_Misc_Flower_02",       60,   3e3, 4e3,   1 },
  { "silverleaf", "Silverleaf",  "INV_Misc_Herb_10",         120,  8e3, 1.1e4, 1 },
  { "mageroyal",  "Mageroyal",   "INV_Jewelry_Talisman_03",  300,  4e4, 6e4,   50 },
  { "briarthorn", "Briarthorn",  "INV_Misc_Root_01",         480,  9e4, 1.35e5, 70 },
  { "kingsblood", "Kingsblood",  "INV_Misc_Herb_03",         1200, 4e5, 6.5e5, 125 },
  { "fadeleaf",   "Fadeleaf",    "INV_Misc_Herb_12",         2100, 1.5e6, 2.5e6, 160 },
  { "sungrass",   "Sungrass",    "INV_Misc_Herb_18",         3600, 6e6, 1.05e7, 210 },
  { "dreamfoil",  "Dreamfoil",   "INV_Misc_Herb_DreamFoil",  7200, 3e7, 5.5e7, 250 },
}
TCF.SEED_BY_KEY = {}
for i, sd in ipairs(TCF.SEEDS) do
  TCF.SEED_BY_KEY[sd[1]] = sd
  TCF.AddMat(sd[1], sd[2], sd[3], sd[6] / 4, "herbalism")
end
-- 1.6: each seed teaches up to its teach level (Professions.lua TCF.SetTeachLevels), so no gap
-- between two seeds leaves you stuck
TCF.SetTeachLevels(TCF.SEEDS, function(sd) return sd[7] end, function(sd, t) sd.teach = t end)
TCF.AddMat("lotus", "Black Lotus", "INV_Misc_Herb_BlackLotus", 5e7, "herbalism")

TCF.GARDEN_MAX_PLOTS = 12
TCF.GARDEN_UPGRADES = {
  { key = "gardener",   name = "Hire a Gardener",  desc = "Harvests and replants ripe plots for you, even offline.", cost = 5e5 },
  { key = "compost",    name = "Compost",          desc = "Plants grow 50% faster.",                                cost = 2e6 },
  { key = "greenhouse", name = "Greenhouse",       desc = "Twice the herbs and gold from every harvest.",           cost = 2e7 },
  { key = "soil",       name = "Enchanted Soil",   desc = "Plants grow twice as fast again.",                       cost = 5e8 },
}

local function G(self)
  local s = TCF:ProfState()
  s.garden = s.garden or { plots = {}, n = 3, up = {} }
  return s.garden, s
end
TCF.GardenState = G

function TCF:GardenSpeed()
  local g = G(self)
  local m = 1
  if g.up.compost then m = m * 1.5 end
  if g.up.soil then m = m * 2 end
  return m * (self.FoodBuff and self:FoodBuff("garden") or 1)
end

function TCF:PlotCost(n) return 2e4 * 3 ^ (n - 3) end

function TCF:BuyPlot()
  local g = G(self)
  if g.n >= TCF.GARDEN_MAX_PLOTS then return false end
  if not self:SpendGold(self:PlotCost(g.n + 1)) then return false end
  g.n = g.n + 1
  self:MarkDirty()
  return true
end

function TCF:BuyGardenUpgrade(key)
  local g = G(self)
  for _, u in ipairs(TCF.GARDEN_UPGRADES) do
    if u.key == key and not g.up[key] and self:SpendGold(u.cost) then g.up[key] = true; self:MarkDirty(); return true end
  end
  return false
end

function TCF:Plant(i, seedKey)
  local g = G(self)
  local sd = TCF.SEED_BY_KEY[seedKey]
  if not sd or i > g.n or (g.plots[i] and g.plots[i].seed) then return false end
  if self:ProfSkill("herbalism") < sd[7] then return false, "Needs Herbalism skill " .. sd[7] .. " to plant " .. sd[2] .. "." end
  if not self:SpendGold(sd[5]) then return false, "Not enough Trade Gold: " .. sd[2] .. " seeds cost " .. TCF.GoldStr(sd[5]) .. "." end
  g.plots[i] = { seed = seedKey, grown = 0 }
  return true
end

local function harvest(self, g, s, i)
  local p = g.plots[i]
  local sd = TCF.SEED_BY_KEY[p.seed]
  local n = 1 + floor(self:ProfSkill("herbalism") / 100)
  if g.up.greenhouse then n = n * 2 end
  s.mats[sd[1]] = (s.mats[sd[1]] or 0) + n
  self:EarnGold(sd[6] * n)
  if (sd[1] == "sungrass" or sd[1] == "dreamfoil") and random() < 0.01 + self:ProfSkill("herbalism") / 30000 then
    s.mats.lotus = (s.mats.lotus or 0) + 1
    if not self.tradeQuiet then self.gardenMutation = true end
  end
  self:ProfSkillUp("herbalism", sd.teach or sd[7])
  local seed = p.seed
  g.plots[i] = nil
  return seed
end

-- Click a plot: plant the chosen seed, water it, or harvest it
function TCF:PlotClick(i, seedKey)
  local g, s = G(self)
  local p = g.plots[i]
  if not p or not p.seed then return self:Plant(i, seedKey) end
  local sd = TCF.SEED_BY_KEY[p.seed]
  if p.grown >= sd[4] then harvest(self, g, s, i); self:MarkDirty(); return true end
  p.grown = min(sd[4], p.grown + 2 * self:GardenSpeed())  -- watering
  return true
end

-- Every key press in WoW waters the whole garden a little
function TCF:GardenTap()
  local g = G(self)
  local sp = self:GardenSpeed()
  for i = 1, g.n do
    local p = g.plots[i]
    if p and p.seed then p.grown = min(TCF.SEED_BY_KEY[p.seed][4], p.grown + 0.3 * sp) end
  end
end

local function advance(self, dt, offline)
  local g, s = G(self)
  local sp = self:GardenSpeed()
  for i = 1, g.n do
    local p = g.plots[i]
    if p and p.seed then
      local sd = TCF.SEED_BY_KEY[p.seed]
      p.grown = p.grown + dt * sp
      if g.up.gardener then
        -- harvest every finished crop in this time and replant while affordable
        local guard = 0
        while p and p.grown >= sd[4] and guard < 5000 do
          guard = guard + 1
          local over = p.grown - sd[4]
          local seed = harvest(self, g, s, i)
          if self:SpendGold(sd[5]) then
            g.plots[i] = { seed = seed, grown = over }
            p = g.plots[i]
          else p = nil end
        end
      elseif p.grown > sd[4] then
        p.grown = sd[4]
      end
    end
  end
end

table.insert(TCF.PROF_MODULES, { key = "herbalism", advance = advance,
  reset = function(self, s) if s.garden then s.garden.plots = {}; s.garden.n = 3; s.garden.up = {} end end })
