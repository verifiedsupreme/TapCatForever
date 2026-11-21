-- TapCatForever: Professions, an idle tycoon game.
--
-- Each profession is a board of six operations (Copper Vein, Tin Vein, ...).
-- Run an operation to earn Trade Gold and its material; buy more of it to earn
-- more; hire a foreman to automate it (also offline). Owning 25/50/100/...
-- doubles its speed; upgrades triple profits. Renown is the prestige reset.
-- Every key press in WoW restarts idle operations, so playing is the clicker.
-- Materials craft cosmetics you can't get anywhere else.
local ADDON, TCF = ...

local floor, min, max, random = math.floor, math.min, math.max, math.random

TCF.PROF_OFFLINE_CAP = 24 * 3600

-- Operation economics (shared shape, like a classic idle tycoon)
local OPS = {
  { cost = 4,       mult = 1.09, time = 5,   rev = 1,      foreman = 5000 },
  { cost = 60,      mult = 1.17, time = 12,  rev = 60,     foreman = 75000 },
  { cost = 720,     mult = 1.16, time = 24,  rev = 540,    foreman = 500000 },
  { cost = 8640,    mult = 1.15, time = 48,  rev = 4320,   foreman = 2.5e6 },
  { cost = 103680,  mult = 1.14, time = 96,  rev = 51840,  foreman = 6e6 },
  { cost = 1244160, mult = 1.13, time = 384, rev = 622080, foreman = 5e7 },
}
TCF.PROF_OPS = OPS
TCF.MILESTONES = { 25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000 }
local MILESTONE_CHEST = { [25] = "pouch", [100] = "strong", [300] = "heroic" }

-- scale: later professions are bigger businesses; unlock: Trade Gold to start it
TCF.PROFESSIONS = {
  { key = "mining", name = "Mining", icon = "Trade_Mining", scale = 1, unlock = 0,
    ops = {
      { "Copper Vein", "copper", "Copper Ore", "INV_Ore_Copper_01" },
      { "Tin Vein", "tin", "Tin Ore", "INV_Ore_Tin_01" },
      { "Iron Deposit", "iron", "Iron Ore", "INV_Ore_Iron_01" },
      { "Mithril Deposit", "mithril", "Mithril Ore", "INV_Ore_Mithril_02" },
      { "Thorium Vein", "thorium", "Thorium Ore", "INV_Ore_Thorium_02" },
      { "Arcane Crystal Geode", "arcane", "Arcane Crystal", "INV_Misc_Gem_Crystal_01" },
    } },
  { key = "herbalism", name = "Herbalism", icon = "Trade_Herbalism", scale = 40, unlock = 1e6,
    ops = {
      { "Peacebloom Patch", "peacebloom", "Peacebloom", "INV_Misc_Flower_02" },
      { "Mageroyal Garden", "mageroyal", "Mageroyal", "INV_Jewelry_Talisman_03" },
      { "Kingsblood Grove", "kingsblood", "Kingsblood", "INV_Misc_Herb_03" },
      { "Sungrass Meadow", "sungrass", "Sungrass", "INV_Misc_Herb_18" },
      { "Dreamfoil Glade", "dreamfoil", "Dreamfoil", "INV_Misc_Herb_DreamFoil" },
      { "Black Lotus Bloom", "lotus", "Black Lotus", "INV_Misc_Herb_BlackLotus" },
    } },
  { key = "skinning", name = "Skinning", icon = "INV_Misc_Pelt_Wolf_01", scale = 1600, unlock = 1e10,
    ops = {
      { "Wolf Hunts", "light", "Light Leather", "INV_Misc_LeatherScrap_03" },
      { "Boar Hunts", "medium", "Medium Leather", "INV_Misc_LeatherScrap_05" },
      { "Raptor Hunts", "heavy", "Heavy Leather", "INV_Misc_LeatherScrap_07" },
      { "Yeti Hunts", "thick", "Thick Leather", "INV_Misc_LeatherScrap_08" },
      { "Chimaera Hunts", "rugged", "Rugged Leather", "INV_Misc_LeatherScrap_02" },
      { "Devilsaur Hunts", "devilsaur", "Devilsaur Leather", "INV_Misc_Pelt_Bear_03", bonus = { "onyxscale", "Black Dragonscale", "INV_Misc_MonsterScales_10", 0.15 } },
    } },
  { key = "fishing", name = "Fishing", icon = "Trade_Fishing", scale = 64000, unlock = 1e14,
    ops = {
      { "Goldshire Pond", "smallfish", "Raw Brilliant Smallfish", "INV_Misc_Fish_02" },
      { "Wetlands Shore", "bristle", "Raw Bristle Whisker Catfish", "INV_Misc_Fish_05" },
      { "Mithril Head Pool", "trout", "Raw Mithril Head Trout", "INV_Misc_Fish_08" },
      { "Feralas Waters", "nightfin", "Raw Nightfin Snapper", "INV_Misc_Fish_03" },
      { "Stonescale School", "eel", "Stonescale Eel", "INV_Misc_Fish_36" },
      { "Mr. Pinchy's Spot", "pinchy", "Mr. Pinchy", "INV_Misc_Fish_35" },
    } },
}
TCF.PROF_BY_KEY = {}
TCF.MAT_BY_KEY = {}
for pi, p in ipairs(TCF.PROFESSIONS) do
  p.index = pi
  TCF.PROF_BY_KEY[p.key] = p
  for i, o in ipairs(p.ops) do
    TCF.MAT_BY_KEY[o[2]] = { key = o[2], name = o[3], icon = o[4], prof = p.key, op = i }
    if o.bonus then TCF.MAT_BY_KEY[o.bonus[1]] = { key = o.bonus[1], name = o.bonus[2], icon = o.bonus[3], prof = p.key, op = i, bonus = true } end
  end
end

-- Recipes: cosmetics only obtainable by crafting (Data.lua, source "craft")
TCF.RECIPES = {
  mining = {
    { item = "craft_copper_circlet", mats = { copper = 60 } },
    { item = "craft_iron_greathelm", mats = { iron = 250, tin = 120 } },
    { item = "craft_mithril_medal",  mats = { mithril = 400 } },
    { item = "craft_thorium_axe",    mats = { thorium = 600, mithril = 300 } },
    { item = "craft_arcanite_reaper", mats = { arcane = 400, thorium = 1200 } },
  },
  herbalism = {
    { item = "craft_peacebloom_crown", mats = { peacebloom = 60 } },
    { item = "craft_mageroyal_bloom",  mats = { mageroyal = 250 } },
    { item = "craft_kingsblood_aura",  mats = { kingsblood = 400 } },
    { item = "craft_dreamfoil_wreath", mats = { dreamfoil = 600, sungrass = 300 } },
    { item = "craft_lotus_bloom",      mats = { lotus = 400, dreamfoil = 1200 } },
  },
  skinning = {
    { item = "craft_wolfpelt_cloak",  mats = { light = 60 } },
    { item = "craft_raptor_hood",     mats = { heavy = 250, medium = 120 } },
    { item = "craft_thick_mantle",    mats = { thick = 400 } },
    { item = "craft_devilsaur_mantle", mats = { devilsaur = 300, rugged = 600 } },
    { item = "craft_onyxia_cloak",    mats = { onyxscale = 80, rugged = 1200 } },
  },
  fishing = {
    { item = "craft_fishing_hat",    mats = { smallfish = 60 } },
    { item = "craft_iron_pole",      mats = { trout = 250, bristle = 120 } },
    { item = "craft_murloc_bubbles", mats = { nightfin = 400 } },
    { item = "craft_eel_shield",     mats = { eel = 600 } },
    { item = "craft_pinchy_gift",    mats = { pinchy = 400, eel = 1200 } },
  },
}

---------------------------------------------------------------- state
local function S(self)
  local db = self.db
  if not db.trade then
    db.trade = { gold = 5, lifetime = 0, renown = 0, prestiges = 0, unlocked = { mining = true }, ops = {},
      upgrades = {}, milestones = {}, mats = {}, last = time(), buy = 1 }
    -- carry over materials and professions from the old gathering system
    if db.prof then
      for k, n in pairs(db.prof.mats or {}) do db.trade.mats[k] = n end
      for k in pairs(db.prof.known or {}) do db.trade.unlocked[k] = true end
    end
  end
  local s = db.trade
  for _, p in ipairs(TCF.PROFESSIONS) do
    s.ops[p.key] = s.ops[p.key] or {}
    for i = 1, 6 do s.ops[p.key][i] = s.ops[p.key][i] or { n = 0, p = 0, run = false, mgr = false } end
  end
  return s
end
TCF.TradeState = S
function TCF:ProfState() return S(self) end

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

---------------------------------------------------------------- formulas
function TCF:OpDef(prof, i) return OPS[i], TCF.PROF_BY_KEY[prof] end

function TCF:OpCost(prof, i, count)
  local o, p = self:OpDef(prof, i)
  local n = S(self).ops[prof][i].n
  count = count or 1
  local base = o.cost * p.scale * o.mult ^ n
  return base * (o.mult ^ count - 1) / (o.mult - 1)
end

-- how many you can afford (for "Max")
function TCF:OpMaxBuy(prof, i)
  local o, p = self:OpDef(prof, i)
  local n = S(self).ops[prof][i].n
  local gold = S(self).gold
  local base = o.cost * p.scale * o.mult ^ n
  local k = floor(math.log(gold * (o.mult - 1) / base + 1) / math.log(o.mult))
  return max(0, k)
end

function TCF:OpSpeedMult(prof, i)
  local n = S(self).ops[prof][i].n
  local m = 1
  for _, ms in ipairs(TCF.MILESTONES) do if n >= ms then m = m * 2 end end
  return m
end

function TCF:OpCycleTime(prof, i) return OPS[i].time / self:OpSpeedMult(prof, i) end

function TCF:UpgradeMult(prof, i)
  local s = S(self)
  local m = 1
  for _, u in ipairs(TCF.UPGRADES[prof]) do
    if s.upgrades[u.id] and (u.op == i or u.op == 0) then m = m * u.mult end
  end
  return m * (1 + 0.02 * s.renown)
end

function TCF:OpRevenue(prof, i)
  local o, p = self:OpDef(prof, i)
  local st = S(self).ops[prof][i]
  return o.rev * p.scale * st.n * self:UpgradeMult(prof, i)
end

function TCF:OpMatsPerCycle(prof, i)
  local n = S(self).ops[prof][i].n
  return 1 + (n >= 100 and 1 or 0) + (n >= 300 and 1 or 0)
end

-- Upgrades: three x3 per operation, plus x3 for the whole profession
TCF.UPGRADES = {}
for _, p in ipairs(TCF.PROFESSIONS) do
  local list = {}
  for i, o in ipairs(p.ops) do
    for k = 0, 2 do
      list[#list + 1] = { id = p.key .. i .. "_" .. k, prof = p.key, op = i, mult = 3,
        cost = OPS[i].cost * p.scale * 2e5 * 500 ^ k, name = o[1] .. " profits x3", icon = o[4] }
    end
  end
  for k = 0, 2 do
    list[#list + 1] = { id = p.key .. "_all" .. k, prof = p.key, op = 0, mult = 3,
      cost = p.scale * 1e9 * 1e4 ^ k, name = "All " .. p.name .. " profits x3", icon = p.icon }
  end
  table.sort(list, function(a, b) return a.cost < b.cost end)
  TCF.UPGRADES[p.key] = list
end

---------------------------------------------------------------- actions
function TCF:ProfUnlocked(prof) return S(self).unlocked[prof] == true end

function TCF:UnlockProfession(prof)
  local s, p = S(self), TCF.PROF_BY_KEY[prof]
  if s.unlocked[prof] or s.gold < p.unlock then return false end
  s.gold = s.gold - p.unlock
  s.unlocked[prof] = true
  self:Print("Your cat took up |cffffd100" .. p.name .. "|r!")
  self:PlaySound("ach")
  self:MarkDirty(); self:RefreshAll()
  return true
end

function TCF:BuyOp(prof, i, count)
  local s = S(self)
  if not s.unlocked[prof] then return false end
  if count == "max" then count = self:OpMaxBuy(prof, i) end
  if not count or count < 1 then return false end
  local cost = self:OpCost(prof, i, count)
  if s.gold < cost then return false end
  s.gold = s.gold - cost
  local st = s.ops[prof][i]
  local before = st.n
  st.n = st.n + count
  -- milestone chests (once ever per operation)
  for ms, chest in pairs(MILESTONE_CHEST) do
    local key = prof .. i .. "_" .. ms
    if before < ms and st.n >= ms and not s.milestones[key] then
      s.milestones[key] = true
      self:AwardChest(chest, TCF.PROF_BY_KEY[prof].ops[i][1] .. " x" .. ms)
    end
  end
  self:MarkDirty()
  return true
end

function TCF:HireForeman(prof, i)
  local s = S(self)
  local st = s.ops[prof][i]
  local cost = OPS[i].foreman * TCF.PROF_BY_KEY[prof].scale
  if st.mgr or st.n < 1 or s.gold < cost then return false end
  s.gold = s.gold - cost
  st.mgr = true
  st.run = true
  self:Print(TCF.PROF_BY_KEY[prof].ops[i][1] .. " is now automated.")
  self:MarkDirty()
  return true
end

function TCF:BuyUpgrade(id)
  local s = S(self)
  for _, list in pairs(TCF.UPGRADES) do
    for _, u in ipairs(list) do
      if u.id == id and not s.upgrades[id] and s.gold >= u.cost and s.unlocked[u.prof] then
        s.gold = s.gold - u.cost
        s.upgrades[id] = true
        self:MarkDirty()
        return true
      end
    end
  end
  return false
end

-- Start an operation's cycle by hand (or by a key press)
function TCF:RunOp(prof, i)
  local st = S(self).ops[prof][i]
  if st.n > 0 and not st.run then st.run = true; return true end
end

-- Every key press restarts idle operations in unlocked professions.
function TCF:ProfTap()
  local s = self.db and self.db.trade
  if not s then return end
  for prof in pairs(s.unlocked) do
    for _, st in ipairs(s.ops[prof]) do
      if st.n > 0 and not st.run then st.run = true end
    end
  end
end

---------------------------------------------------------------- simulation
local function produce(self, s, prof, i, cycles)
  local rev = self:OpRevenue(prof, i) * cycles
  s.gold = s.gold + rev
  s.lifetime = s.lifetime + rev
  local op = TCF.PROF_BY_KEY[prof].ops[i]
  s.mats[op[2]] = (s.mats[op[2]] or 0) + cycles * self:OpMatsPerCycle(prof, i)
  if op.bonus then
    local expect = cycles * op.bonus[4]
    local got = floor(expect) + ((random() < expect - floor(expect)) and 1 or 0)
    if got > 0 then s.mats[op.bonus[1]] = (s.mats[op.bonus[1]] or 0) + got end
  end
end

-- Advance every operation by dt seconds. offline = only automated ones run.
function TCF:ProfAdvance(dt, offline)
  local s = S(self)
  for prof in pairs(s.unlocked) do
    for i, st in ipairs(s.ops[prof]) do
      if st.n > 0 and (st.mgr or (st.run and not offline)) then
        st.p = st.p + dt / self:OpCycleTime(prof, i)
        if st.p >= 1 then
          local cycles = st.mgr and floor(st.p) or 1
          produce(self, s, prof, i, cycles)
          st.p = st.mgr and (st.p - cycles) or 0
          if not st.mgr then st.run = false end
        end
      end
    end
  end
  s.last = time()
end

function TCF:ProfessionsTick(login, dt)
  local s = S(self)
  if login then
    local away = min(TCF.PROF_OFFLINE_CAP, max(0, time() - (s.last or time())))
    if away > 60 then
      local before = s.gold
      self:ProfAdvance(away, true)
      if s.gold > before then
        self:Print(string.format("While you were away your foremen earned %s Trade Gold.", TCF.GoldStr(s.gold - before)))
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

function TCF:PrestigeTrade()
  local s = S(self)
  local gain = self:RenownOnReset()
  if gain < 5 then return false end
  s.renown = s.renown + gain
  s.prestiges = s.prestiges + 1
  s.gold = 5
  s.upgrades = {}
  s.unlocked = { mining = true }
  for _, p in ipairs(TCF.PROFESSIONS) do
    for i = 1, 6 do s.ops[p.key][i] = { n = 0, p = 0, run = false, mgr = false } end
  end
  local coins = min(1000, gain * 3)
  self:AddCoins(coins)
  self:Print(string.format("Your cat sold its business for |cffffd100%d Renown|r (+%d%% profits forever) and %d TapCoins!", gain, gain * 2, coins))
  self:PlaySound("ach")
  self:MarkDirty(); self:RefreshAll()
  return true
end

---------------------------------------------------------------- crafting
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
