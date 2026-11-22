-- TapCatForever: First Aid. Cloth (from Adventure enemies or the cloth merchant)
-- becomes bandages in a crafting queue. In Adventure the cat uses its best bandage
-- when it gets hurt. A field medic keeps crafting while you're away, and a cloth
-- contract buys cloth automatically.
local ADDON, TCF = ...

local floor, min, max, random = math.floor, math.min, math.max, math.random

-- cloth: key, name, icon, price at the cloth merchant, enemy level it drops from.
-- Tailoring cats farm cloth by the hundred (Professions.lua cloth spots), so cloth and
-- bandages sell for the same small amount as ore and leather; the merchant's prices stay.
TCF.CLOTH = {
  { "linen",     "Linen Cloth",     "INV_Fabric_Linen_01",     2e3,   1 },
  { "wool",      "Wool Cloth",      "INV_Fabric_Wool_01",      1e4,   18 },
  { "silk",      "Silk Cloth",      "INV_Fabric_Silk_01",      5e4,   32 },
  { "mageweave", "Mageweave Cloth", "INV_Fabric_Mageweave_01", 2.5e5, 42 },
  { "runecloth", "Runecloth",       "INV_Fabric_PurpleFire_01", 1.2e6, 52 },
}
for _, c in ipairs(TCF.CLOTH) do TCF.AddMat(c[1], c[2], c[3], 1, "cloth") end

-- bandages: key, name, icon, cloth, amount, seconds, skill, heal (% of max health)
TCF.BANDAGES = {
  { "b_linen",           "Linen Bandage",           "INV_Misc_Bandage_15", "linen",     1, 5,  1,   0.10 },
  { "b_heavylinen",      "Heavy Linen Bandage",     "INV_Misc_Bandage_18", "linen",     2, 8,  40,  0.15 },
  { "b_wool",            "Wool Bandage",            "INV_Misc_Bandage_14", "wool",      1, 10, 80,  0.20 },
  { "b_heavywool",       "Heavy Wool Bandage",      "INV_Misc_Bandage_17", "wool",      2, 12, 115, 0.25 },
  { "b_silk",            "Silk Bandage",            "INV_Misc_Bandage_01", "silk",      1, 15, 150, 0.30 },
  { "b_heavysilk",       "Heavy Silk Bandage",      "INV_Misc_Bandage_02", "silk",      2, 18, 180, 0.35 },
  { "b_mageweave",       "Mageweave Bandage",       "INV_Misc_Bandage_19", "mageweave", 1, 20, 210, 0.40 },
  { "b_heavymageweave",  "Heavy Mageweave Bandage", "INV_Misc_Bandage_20", "mageweave", 2, 24, 240, 0.45 },
  { "b_runecloth",       "Runecloth Bandage",       "INV_Misc_Bandage_11", "runecloth", 1, 28, 260, 0.50 },
  { "b_heavyrunecloth",  "Heavy Runecloth Bandage", "INV_Misc_Bandage_12", "runecloth", 2, 32, 290, 0.60 },
}
TCF.BANDAGE_BY_KEY = {}
for _, b in ipairs(TCF.BANDAGES) do
  TCF.BANDAGE_BY_KEY[b[1]] = b
  TCF.AddMat(b[1], b[2], b[3], b[5], "firstaid")  -- worth the cloth it took
end
TCF.BANDAGE_COOLDOWN = 20

TCF.AID_UPGRADES = {
  { key = "medic",    name = "Hire a Field Medic",  desc = "Keeps making bandages, even offline: your best one when you have its cloth, otherwise the best one you have cloth for. A Tailoring cat's medic stops at 100 of each, so your cloth stays for Tailoring.", cost = 1e6 },
  { key = "contract", name = "Cloth Contract",      desc = "Buys cloth for the field medic automatically (costs Trade Gold).",      cost = 5e6 },
  { key = "fast",     name = "Steady Hands",        desc = "Bandages are made twice as fast.",                                       cost = 2e7 },
}

local function A(self)
  local s = TCF:ProfState()
  s.aid = s.aid or { queue = nil, up = {} }
  return s.aid, s
end
TCF.AidState = A

function TCF:BuyAidUpgrade(key)
  local a = A(self)
  for _, u in ipairs(TCF.AID_UPGRADES) do
    if u.key == key and not a.up[key] and self:SpendGold(u.cost) then a.up[key] = true; self:MarkDirty(); return true end
  end
  return false
end

function TCF:BuyCloth(key, n)
  local _, s = A(self)
  for _, c in ipairs(TCF.CLOTH) do
    if c[1] == key and self:SpendGold(c[4] * n) then s.mats[key] = (s.mats[key] or 0) + n; self:MarkDirty(); return true end
  end
  return false
end

function TCF:QueueBandages(key, count)
  local a = A(self)
  local b = TCF.BANDAGE_BY_KEY[key]
  if not b or self:ProfSkill("firstaid") < b[7] then return false end
  a.queue = { key = key, left = count, p = 0 }
  self:MarkDirty()
  return true
end

-- best bandage this skill can make
local function bestRecipe(self)
  local best
  for _, b in ipairs(TCF.BANDAGES) do if self:ProfSkill("firstaid") >= b[7] then best = b end end
  return best
end

local function clothOf(b)
  for _, c in ipairs(TCF.CLOTH) do if c[1] == b[4] then return c end end
end

-- the Cloth Contract buys 10 bandages' worth of cloth for b
local function contractBuy(self, a, s, b)
  if not (a.up.contract and self:SpendGold(clothOf(b)[4] * b[5] * 10)) then return false end
  s.mats[b[4]] = (s.mats[b[4]] or 0) + b[5] * 10
  return true
end

-- Cloth spots fill the same cloth the medic uses. When this cat owns cloth spots, the medic
-- stops making a bandage once you hold this many, so the cloth stays for Tailoring.
TCF.MEDIC_STOCK = 100
local function ownsClothSpots(s)
  local ops = s.ops and s.ops.cloth
  if not ops then return false end
  for i = 1, 6 do if ops[i] and (ops[i].n or 0) > 0 then return true end end
  return false
end
local function stocked(self, s, b)
  return (s.mats[b[1]] or 0) >= TCF.MEDIC_STOCK and ownsClothSpots(s)
end

-- what the field medic makes next: your best bandage if you have its cloth (or the
-- contract can buy it), otherwise the best bandage you do have cloth for
local function medicRecipe(self, a, s)
  local best = bestRecipe(self)
  if not best then return end
  if not stocked(self, s, best) and ((s.mats[best[4]] or 0) >= best[5] or contractBuy(self, a, s, best)) then return best end
  local skill = self:ProfSkill("firstaid")
  for k = #TCF.BANDAGES, 1, -1 do
    local b = TCF.BANDAGES[k]
    if skill >= b[7] and (s.mats[b[4]] or 0) >= b[5] and not stocked(self, s, b) then return b end
  end
end

local function advance(self, dt, offline)
  local a, s = A(self)
  local guard = 0
  local remaining = dt
  while remaining > 0 and guard < 3000 do
    guard = guard + 1
    if not a.queue or a.queue.left <= 0 then
      if not a.up.medic then a.queue = nil; return end
      local b = medicRecipe(self, a, s)
      if not b then a.queue = nil; return end
      -- one bandage at a time, so the medic picks again after each one
      a.queue = { key = b[1], left = 1, p = 0, auto = true }
    end
    local b = TCF.BANDAGE_BY_KEY[a.queue.key]
    if (s.mats[b[4]] or 0) < b[5] and not contractBuy(self, a, s, b) then
      -- out of cloth: the field medic switches to another bandage, a manual queue waits
      if not a.queue.auto then return end
      a.queue = nil
    else
      local need = b[6] / (a.up.fast and 2 or 1)
      local step = min(remaining, (1 - a.queue.p) * need)
      a.queue.p = a.queue.p + step / need
      remaining = remaining - step
      if a.queue.p >= 1 - 1e-9 then
        s.mats[b[4]] = s.mats[b[4]] - b[5]
        s.mats[b[1]] = (s.mats[b[1]] or 0) + 1
        a.queue.p = 0
        a.queue.left = a.queue.left - 1
        self:ProfSkillUp("firstaid", b[7])
      end
    end
  end
end

-- Adventure: the cat uses its best bandage when hurt (20 s cooldown)
function TCF:UseBandage(run)
  if not self:ProfUnlocked("firstaid") then return end
  local _, s = A(self)
  if (run.bandageReady or 0) > run.t or run.catHP > run.catMax * 0.4 then return end
  for k = #TCF.BANDAGES, 1, -1 do
    local b = TCF.BANDAGES[k]
    if (s.mats[b[1]] or 0) > 0 then
      s.mats[b[1]] = s.mats[b[1]] - 1
      run.catHP = min(run.catMax, run.catHP + run.catMax * b[8])
      run.bandageReady = run.t + TCF.BANDAGE_COOLDOWN
      self:AdvEvent("ability", b[2], b[3])
      self:AdvEvent("heal", run.catMax * b[8])
      return true
    end
  end
end

-- Adventure: enemies drop cloth for their level
function TCF:DropCloth(level)
  if not self:ProfUnlocked("firstaid") or random() > 0.18 then return end
  local _, s = A(self)
  local pick = TCF.CLOTH[1]
  for _, c in ipairs(TCF.CLOTH) do if level >= c[5] then pick = c end end
  s.mats[pick[1]] = (s.mats[pick[1]] or 0) + random(1, 2)
end

table.insert(TCF.PROF_MODULES, { key = "firstaid", advance = advance,
  reset = function(self, s) if s.aid then s.aid.up = {}; s.aid.queue = nil end end })
