-- TapCatForever: Professions. Five professions, each with its own mechanic and an
-- idle mode, sharing Trade Gold and Renown (the prestige reset):
--   Mining     (free)      idle tycoon: veins, foremen, milestones + your own pickaxe clicks
--   Herbalism  (5 Renown)  garden plots that grow in real time, gardener automates
--   First Aid  (20 Renown) turn cloth into bandages that heal your cat in Adventure
--   Fishing    (60 Renown) bobber mini-game, fishing buddy catches while you're away
--   Cooking    (150 Renown) experiment with ingredients to discover dishes that buff you
-- Like WoW: Mining and Herbalism are the two main professions; the rest are secondary.
local ADDON, TCF = ...

local floor, min, max, random = math.floor, math.min, math.max, math.random

TCF.PROF_OFFLINE_CAP = 24 * 3600

TCF.PROFESSIONS = {
  { key = "mining",    name = "Mining",    icon = "Trade_Mining",           renown = 0 },
  { key = "herbalism", name = "Herbalism", icon = "Trade_Herbalism",        renown = 5 },
  { key = "firstaid",  name = "First Aid", icon = "Spell_Holy_SealOfSacrifice", renown = 20 },
  { key = "fishing",   name = "Fishing",   icon = "Trade_Fishing",          renown = 60 },
  { key = "cooking",   name = "Cooking",   icon = "INV_Misc_Food_15",       renown = 150 },
}
TCF.PROF_BY_KEY = {}
for i, p in ipairs(TCF.PROFESSIONS) do p.index = i; TCF.PROF_BY_KEY[p.key] = p end

-- every material and product, by key (filled by each profession file)
TCF.MAT_BY_KEY = TCF.MAT_BY_KEY or {}
function TCF.AddMat(key, name, icon, value, prof)
  TCF.MAT_BY_KEY[key] = { key = key, name = name, icon = icon, value = value or 1, prof = prof }
end

-- Mining: operation economics (classic idle tycoon shape)
local OPS = {
  { cost = 4,       mult = 1.09, time = 5,   rev = 1,      foreman = 5000 },
  { cost = 60,      mult = 1.17, time = 12,  rev = 60,     foreman = 75000 },
  { cost = 720,     mult = 1.16, time = 24,  rev = 540,    foreman = 500000 },
  { cost = 8640,    mult = 1.15, time = 48,  rev = 4320,   foreman = 2.5e6 },
  { cost = 103680,  mult = 1.14, time = 96,  rev = 51840,  foreman = 6e6 },
  { cost = 1244160, mult = 1.13, time = 384, rev = 622080, foreman = 5e7 },
}
TCF.PROF_OPS = OPS
TCF.MINING_OPS = {
  { "Copper Vein", "copper", "Copper Ore", "INV_Ore_Copper_01" },
  { "Tin Vein", "tin", "Tin Ore", "INV_Ore_Tin_01" },
  { "Iron Deposit", "iron", "Iron Ore", "INV_Ore_Iron_01" },
  { "Mithril Deposit", "mithril", "Mithril Ore", "INV_Ore_Mithril_02" },
  { "Thorium Vein", "thorium", "Thorium Ore", "INV_Ore_Thorium_02" },
  { "Arcane Crystal Geode", "arcane", "Arcane Crystal", "INV_Misc_Gem_Crystal_01" },
}
for i, o in ipairs(TCF.MINING_OPS) do TCF.AddMat(o[2], o[3], o[4], 1, "mining") end
TCF.MILESTONES = { 25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000 }
local MILESTONE_CHEST = { [25] = "pouch", [100] = "strong", [300] = "heroic" }

-- your own pickaxe: one pickaxe for every vein, upgraded level by level forever.
-- Each level is a small boost (+15% per click, compounding) and costs more than the last.
TCF.PICKAXE_NAMES = { "Copper", "Bronze", "Iron", "Mithril", "Thorium", "Arcanite", "Elementium", "Titanium" }
TCF.PICK_BOOST, TCF.PICK_COST, TCF.PICK_COST_GROWTH = 1.15, 25, 1.55
-- a swing is worth half a second of the whole vein's output (every mine you own on it, with
-- milestones and upgrades), with a 1 in 4 chance of ore. Fast veins give a big share of a
-- cycle per swing, slow veins a small one, so no vein breaks the economy.
TCF.PICK_SECONDS, TCF.PICK_ORE_CHANCE = 0.5, 0.25

---------------------------------------------------------------- state
local function S(self)
  local db = self.db
  if not db.trade then
    db.trade = { gold = 0, lifetime = 0, renown = 0, prestiges = 0, ops = {}, upgrades = {}, milestones = {},
      mats = {}, last = time(), buy = 1 }
  end
  local s = db.trade
  s.renownEver = max(s.renownEver or 0, s.renown or 0)
  s.ops.mining = s.ops.mining or {}
  for i = 1, 6 do s.ops.mining[i] = s.ops.mining[i] or { n = 0, p = 0, run = false, mgr = false } end
  -- older saves had a pickaxe per vein: keep the best one as the overall level
  if type(s.pick) == "table" then
    local best = 1
    for _, t in pairs(s.pick) do if type(t) == "number" and t > best then best = t end end
    s.pickLvl = math.max(s.pickLvl or 0, (best - 1) * 10)
    s.pick = nil
  end
  s.pickLvl = s.pickLvl or 0
  s.skill = s.skill or {}
  return s
end
TCF.TradeState = S
function TCF:ProfState() return S(self) end

function TCF:ProfUnlocked(prof)
  local p = TCF.PROF_BY_KEY[prof]
  return p and S(self).renownEver >= p.renown
end

-- Profession skill 1..300 (WoW style). Chance to improve is higher while easy.
function TCF:ProfSkill(prof) return S(self).skill[prof] or 1 end
function TCF:ProfSkillUp(prof, difficulty)
  local s = S(self)
  local cur = s.skill[prof] or 1
  if cur >= 300 then return end
  local gap = cur - (difficulty or 1)
  local chance = gap < 25 and 1 or gap < 50 and 0.5 or gap < 75 and 0.25 or 0.05
  if random() < chance then s.skill[prof] = cur + 1 end
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

---------------------------------------------------------------- mining
function TCF:OpCost(prof, i, count)
  local o = OPS[i]
  local n = S(self).ops.mining[i].n
  count = count or 1
  local base = o.cost * o.mult ^ n
  return base * (o.mult ^ count - 1) / (o.mult - 1)
end

function TCF:OpMaxBuy(prof, i)
  local o = OPS[i]
  local n = S(self).ops.mining[i].n
  local base = o.cost * o.mult ^ n
  return max(0, floor(math.log(S(self).gold * (o.mult - 1) / base + 1) / math.log(o.mult)))
end

function TCF:OpSpeedMult(prof, i)
  local n = S(self).ops.mining[i].n
  local m = 1
  for _, ms in ipairs(TCF.MILESTONES) do if n >= ms then m = m * 2 end end
  return m
end
function TCF:OpCycleTime(prof, i) return OPS[i].time / self:OpSpeedMult(prof, i) end

function TCF:UpgradeMult(prof, i)
  local s = S(self)
  local m = 1
  for _, u in ipairs(TCF.UPGRADES.mining) do
    if s.upgrades[u.id] and u.kind == "profit" and (u.op == i or u.op == 0) then m = m * u.mult end
  end
  return m * (self.FoodBuff and self:FoodBuff("mining") or 1)
end

function TCF:OpRevenue(prof, i)
  return OPS[i].rev * S(self).ops.mining[i].n * self:UpgradeMult(prof, i)
end

-- Trade Gold per second from every mine you own, as if all veins were running (before Renown)
function TCF:MiningIncome()
  local s, g = S(self), 0
  for i = 1, 6 do
    if s.ops.mining[i].n > 0 then g = g + self:OpRevenue("mining", i) / self:OpCycleTime("mining", i) end
  end
  return g
end

function TCF:OpMatsPerCycle(prof, i)
  local n = S(self).ops.mining[i].n
  return 1 + (n >= 100 and 1 or 0) + (n >= 300 and 1 or 0)
end

function TCF:PickLevel() return S(self).pickLvl end
function TCF:PickMult(lvl) return TCF.PICK_BOOST ^ (lvl or self:PickLevel()) end
function TCF:PickCost(lvl) lvl = lvl or self:PickLevel(); return floor(TCF.PICK_COST * TCF.PICK_COST_GROWTH ^ lvl) end
-- one swing per cooldown (shared by every vein); upgrades shorten it a little, down to 0.75s
function TCF:PickCooldown(lvl) return max(0.75, 1.5 * 0.985 ^ (lvl or self:PickLevel())) end
function TCF:PickReadyIn() return max(0, (self.pickNext or 0) - GetTime()) end
-- gold for one swing on vein i
function TCF:PickCycleShare(i) return min(1, TCF.PICK_SECONDS * self:PickMult() / self:OpCycleTime("mining", i)) end
function TCF:PickGold(i)
  local n = S(self).ops.mining[i].n
  local share = OPS[i].rev * n * self:UpgradeMult("mining", i) * self:PickCycleShare(i)
  -- Copper only: never less than a quarter of one mine's cycle, so you can dig your way to
  -- the first mine. Other veins need a mine first and use the cycle share alone (a floor
  -- there would let a few swings on a high vein outpay all of its mines).
  local floorGold = (i == 1) and OPS[1].rev * 0.25 * self:PickMult() * self:UpgradeMult("mining", 1) or 0
  return max(share, floorGold)
end
function TCF:PickOre(lvl) return 1 + floor((lvl or self:PickLevel()) / 15) end
function TCF:PickName(lvl)
  lvl = lvl or self:PickLevel()
  local n = TCF.PICKAXE_NAMES[min(#TCF.PICKAXE_NAMES, floor(lvl / 10) + 1)]
  return string.format("%s Pickaxe (Lv %d)", n, lvl)
end
function TCF:UpgradePick()
  if not self:SpendGold(self:PickCost()) then return false end
  local s = S(self)
  s.pickLvl = s.pickLvl + 1
  self:MarkDirty()
  return true
end

-- Mine by hand with your pickaxe (works on the first vein from the start)
function TCF:MineClick(i)
  local s = S(self)
  if i > 1 and s.ops.mining[i].n < 1 then return false end
  if self:PickReadyIn() > 0 then return false end
  self.pickNext = GetTime() + self:PickCooldown()
  local gold = self:EarnGold(self:PickGold(i))
  local op = TCF.MINING_OPS[i]
  local ore = 0
  for _ = 1, self:PickOre() do if random() < TCF.PICK_ORE_CHANCE then ore = ore + 1 end end
  s.mats[op[2]] = (s.mats[op[2]] or 0) + ore
  self.lastMineOre = ore
  self:ProfSkillUp("mining", (i - 1) * 50)
  self.lastMineGold = gold
  return true
end

-- Upgrades: x3 profits per vein and for all veins (the pickaxe has its own endless upgrade)
TCF.UPGRADES = { mining = {} }
do
  local list = TCF.UPGRADES.mining
  for i, o in ipairs(TCF.MINING_OPS) do
    for k = 0, 2 do
      list[#list + 1] = { id = "mining" .. i .. "_" .. k, kind = "profit", op = i, mult = 3,
        cost = OPS[i].cost * 2e5 * 500 ^ k, name = o[1] .. " profits x3", icon = o[4] }
    end
  end
  for k = 0, 2 do
    list[#list + 1] = { id = "mining_all" .. k, kind = "profit", op = 0, mult = 3, cost = 1e9 * 1e4 ^ k, name = "All Mining profits x3", icon = "Trade_Mining" }
  end
  table.sort(list, function(a, b) return a.cost < b.cost end)
end

function TCF:BuyOp(prof, i, count)
  local s = S(self)
  if count == "max" then count = self:OpMaxBuy(prof, i) end
  if not count or count < 1 then return false end
  local cost = self:OpCost(prof, i, count)
  if not self:SpendGold(cost) then return false end
  local st = s.ops.mining[i]
  local before = st.n
  st.n = st.n + count
  for ms, chest in pairs(MILESTONE_CHEST) do
    local key = "mining" .. i .. "_" .. ms
    if before < ms and st.n >= ms and not s.milestones[key] then
      s.milestones[key] = true
      self:AwardChest(chest, TCF.MINING_OPS[i][1] .. " x" .. ms)
    end
  end
  self:MarkDirty()
  return true
end

function TCF:HireForeman(prof, i)
  local s = S(self)
  local st = s.ops.mining[i]
  if st.mgr or st.n < 1 or not self:SpendGold(OPS[i].foreman) then return false end
  st.mgr = true; st.run = true
  self:Print(TCF.MINING_OPS[i][1] .. " is now automated.", true)
  self:MarkDirty()
  return true
end

function TCF:BuyUpgrade(id)
  local s = S(self)
  for _, u in ipairs(TCF.UPGRADES.mining) do
    if u.id == id and not s.upgrades[id] then
      if not self:SpendGold(u.cost) then return false end
      s.upgrades[id] = true
      self:MarkDirty()
      return true
    end
  end
  return false
end

function TCF:RunOp(prof, i)
  local st = S(self).ops.mining[i]
  if st.n > 0 and not st.run then st.run = true; return true end
end

---------------------------------------------------------------- key presses and ticking
-- Every key press in WoW waters the garden. Mining veins only run when you start
-- them yourself (click the vein) or once a foreman works them.
function TCF:ProfTap()
  if not (self.db and self.db.trade) then return end
  if self.GardenTap and self:ProfUnlocked("herbalism") then self:GardenTap() end
end

local function produce(self, s, i, cycles)
  self:EarnGold(self:OpRevenue("mining", i) * cycles)
  local op = TCF.MINING_OPS[i]
  s.mats[op[2]] = (s.mats[op[2]] or 0) + cycles * self:OpMatsPerCycle("mining", i)
end

-- Advance everything by dt seconds. offline = only automated things run.
function TCF:ProfAdvance(dt, offline)
  local s = S(self)
  for i, st in ipairs(s.ops.mining) do
    if st.n > 0 and (st.mgr or (st.run and not offline)) then
      st.p = st.p + dt / self:OpCycleTime("mining", i)
      if st.p >= 1 then
        local cycles = st.mgr and floor(st.p) or 1
        produce(self, s, i, cycles)
        st.p = st.mgr and (st.p - cycles) or 0
        if not st.mgr then st.run = false end
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
  s.pickLvl = 0
  for i = 1, 6 do s.ops.mining[i] = { n = 0, p = 0, run = false, mgr = false } end
  for _, mod in ipairs(TCF.PROF_MODULES) do if mod.reset then mod.reset(self, s) end end
  local coins = min(1000, gain * 3)
  self:AddCoins(coins)
  self:Print(string.format("Your cat sold its business for |cffffd100%d Renown|r (+%d%% profits forever) and %d TapCoins!", gain, gain * 2, coins), true)
  for _, p in ipairs(TCF.PROFESSIONS) do
    if p.renown > 0 and s.renownEver >= p.renown and s.renownEver - gain < p.renown then
      self:Print("You can now learn |cffffd100" .. p.name .. "|r!", true)
    end
  end
  self:PlaySound("ach")
  self:MarkDirty(); self:RefreshAll()
  return true
end

---------------------------------------------------------------- crafting cosmetics (all professions)
TCF.RECIPES = {
  mining = {
    { item = "craft_copper_circlet",  mats = { copper = 60 } },
    { item = "craft_iron_greathelm",  mats = { iron = 250, tin = 120 } },
    { item = "craft_mithril_medal",   mats = { mithril = 400 } },
    { item = "craft_thorium_axe",     mats = { thorium = 600, mithril = 300 } },
    { item = "craft_arcanite_reaper", mats = { arcane = 400, thorium = 1200 } },
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

function TCF:CanCraft(r)
  local s = S(self)
  for m, n in pairs(r.mats) do if (s.mats[m] or 0) < n then return false end end
  return true
end

function TCF:Craft(r)
  if not self:CanCraft(r) then return false end
  local s = S(self)
  for m, n in pairs(r.mats) do s.mats[m] = s.mats[m] - n end
  self.db.stats.crafted = (self.db.stats.crafted or 0) + 1
  self:GrantItem(TCF.ITEMS[r.item], "Crafted", true)
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
