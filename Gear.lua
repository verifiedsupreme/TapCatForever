-- TapCatForever: real WoW gear (stats, class proficiencies, equipping, loot)
-- Item data lives in GearData.lua (generated from real Classic item data).
local ADDON, TCF = ...

local floor, min, max, random = math.floor, math.min, math.max, math.random

TCF.GEAR = {}
TCF.GEAR_LIST = {}
TCF.BOSS_LOOT = {}   -- [tier][boss] = { item, ... }
TCF.TIER_POOL = {}   -- [tier] = { item, ... } (zone drops, other bosses)
TCF.WORLD_POOL = {}  -- [level band (req level // 5)] = { item, ... }

-- Called once per item by GearData.lua
function TCF.AddGear(id, name, icon, q, ilvl, req, slot, sub, stats, tier, boss, dc, cls)
  local it = { id = id, name = name, icon = icon, q = q, ilvl = ilvl, req = req, slot = slot, sub = sub,
    statStr = stats, tier = tier, boss = boss, dc = dc, cls = cls }
  TCF.GEAR[id] = it
  TCF.GEAR_LIST[#TCF.GEAR_LIST + 1] = it
  if tier > 0 then
    if boss > 0 then
      TCF.BOSS_LOOT[tier] = TCF.BOSS_LOOT[tier] or {}
      TCF.BOSS_LOOT[tier][boss] = TCF.BOSS_LOOT[tier][boss] or {}
      table.insert(TCF.BOSS_LOOT[tier][boss], it)
    else
      TCF.TIER_POOL[tier] = TCF.TIER_POOL[tier] or {}
      table.insert(TCF.TIER_POOL[tier], it)
    end
  else
    local band = floor(req / 5)
    TCF.WORLD_POOL[band] = TCF.WORLD_POOL[band] or {}
    table.insert(TCF.WORLD_POOL[band], it)
  end
end

-- Parsed stats (cached)
function TCF.GearStats(it)
  if it.stats then return it.stats end
  local s = {}
  for k, v in it.statStr:gmatch("(%a+)=([%d%.]+)") do s[k] = tonumber(v) end
  it.stats = s
  return s
end

---------------------------------------------------------------- slots
TCF.GEAR_SLOTS = {
  { key = "HEAD", name = "Head", icon = "INV_Helmet_01" },
  { key = "NECK", name = "Neck", icon = "INV_Jewelry_Necklace_07" },
  { key = "SHOULDER", name = "Shoulder", icon = "INV_Shoulder_02" },
  { key = "BACK", name = "Back", icon = "INV_Misc_Cape_02" },
  { key = "CHEST", name = "Chest", icon = "INV_Chest_Chain" },
  { key = "WRIST", name = "Wrist", icon = "INV_Bracer_02" },
  { key = "WAIST", name = "Waist", icon = "INV_Belt_03" },
  { key = "HANDS", name = "Hands", icon = "INV_Gauntlets_04" },
  { key = "LEGS", name = "Legs", icon = "INV_Pants_02" },
  { key = "FEET", name = "Feet", icon = "INV_Boots_05" },
  { key = "FINGER1", name = "Ring", icon = "INV_Jewelry_Ring_02" },
  { key = "FINGER2", name = "Ring", icon = "INV_Jewelry_Ring_03" },
  { key = "TRINKET1", name = "Trinket", icon = "INV_Misc_Gem_Pearl_01" },
  { key = "TRINKET2", name = "Trinket", icon = "INV_Misc_Gem_Pearl_02" },
  { key = "MAINHAND", name = "Main Hand", icon = "INV_Sword_04" },
  { key = "OFFHAND", name = "Off Hand", icon = "INV_Shield_06" },
  { key = "RANGED", name = "Ranged", icon = "INV_Weapon_Bow_07" },
}
TCF.GEAR_SLOT_BY_KEY = {}
for _, s in ipairs(TCF.GEAR_SLOTS) do TCF.GEAR_SLOT_BY_KEY[s.key] = s end

local SLOT_NAMES = {
  HEAD = "Head", NECK = "Neck", SHOULDER = "Shoulder", BACK = "Back", CHEST = "Chest", WRIST = "Wrist",
  HANDS = "Hands", WAIST = "Waist", LEGS = "Legs", FEET = "Feet", FINGER = "Finger", TRINKET = "Trinket",
  MH = "Main Hand", ["1H"] = "One-Hand", ["2H"] = "Two-Hand", OH = "Off Hand", HOLD = "Held In Off-hand", RANGED = "Ranged",
}
TCF.ITEM_SLOT_NAMES = SLOT_NAMES
local TYPE_NAMES = {
  cloth = "Cloth", leather = "Leather", mail = "Mail", plate = "Plate", shield = "Shield", misc = "",
  sword = "Sword", mace = "Mace", axe = "Axe", dagger = "Dagger", staff = "Staff", wand = "Wand", bow = "Bow",
  gun = "Gun", polearm = "Polearm", fist = "Fist Weapon", xbow = "Crossbow", thrown = "Thrown",
}
TCF.ITEM_TYPE_NAMES = TYPE_NAMES

---------------------------------------------------------------- class rules (Classic)
local ARMOR_RANK = { cloth = 1, leather = 2, mail = 3, plate = 4 }
local CLASS_RULES = {
  WARRIOR = { armor = 4, shield = true, dual = true, weapons = "sword axe mace dagger fist polearm staff bow gun xbow thrown", two = "sword axe mace polearm staff", role = "melee" },
  PALADIN = { armor = 4, shield = true, weapons = "sword axe mace polearm", two = "sword axe mace polearm", role = "melee" },
  HUNTER  = { armor = 3, dual = true, weapons = "sword axe dagger fist polearm staff bow gun xbow thrown", two = "sword axe polearm staff", role = "ranged" },
  ROGUE   = { armor = 2, dual = true, weapons = "sword mace dagger fist bow gun xbow thrown", two = "", role = "melee" },
  PRIEST  = { armor = 1, weapons = "mace dagger staff wand", two = "staff", role = "caster" },
  SHAMAN  = { armor = 3, shield = true, weapons = "axe mace dagger fist staff", two = "axe mace staff", role = "hybrid" },
  MAGE    = { armor = 1, weapons = "sword dagger staff wand", two = "staff", role = "caster" },
  WARLOCK = { armor = 1, weapons = "sword dagger staff wand", two = "staff", role = "caster" },
  DRUID   = { armor = 2, weapons = "mace dagger fist staff", two = "mace staff", role = "hybrid" },
}
for _, r in pairs(CLASS_RULES) do
  local w, t = {}, {}
  for k in r.weapons:gmatch("%a+") do w[k] = true end
  for k in r.two:gmatch("%a+") do t[k] = true end
  r.w, r.t = w, t
end
TCF.CLASS_RULES = CLASS_RULES

-- Can this class ever use the item? (ignores level)
function TCF:GearUsable(it, class)
  local r = CLASS_RULES[class]
  if it.cls and not (("," .. it.cls .. ","):find("," .. class .. ",", 1, true)) then return false end
  local slot, sub = it.slot, it.sub
  if ARMOR_RANK[sub] then return ARMOR_RANK[sub] <= r.armor end
  if sub == "shield" then return r.shield and true or false end
  if sub == "misc" then return true end
  if slot == "RANGED" then
    if sub == "wand" then return r.w.wand == true end
    return r.w[sub] == true
  end
  if not r.w[sub] then return false end
  if slot == "2H" then return r.t[sub] == true end
  if slot == "OH" then return r.dual == true end
  return true
end

-- How much each class values each stat, and the weapons it actually wants.
local STAT_WEIGHTS = {
  WARRIOR = { str = 1, agi = 0.8, sta = 0.6, ap = 0.5, critr = 0.8, hitr = 0.8, crit = 1, hit = 1, def = 0.5 },
  PALADIN = { str = 1, sta = 0.6, int = 0.5, agi = 0.4, sp = 0.3, heal = 0.3, critr = 0.6, crit = 1, hit = 1, hitr = 0.6, def = 0.4 },
  HUNTER  = { agi = 1, ap = 0.5, rap = 0.5, int = 0.3, sta = 0.5, critr = 0.8, hitr = 0.8, crit = 1, hit = 1 },
  ROGUE   = { agi = 1, str = 0.6, ap = 0.5, sta = 0.4, critr = 0.8, hitr = 0.8, crit = 1, hit = 1 },
  PRIEST  = { int = 1, spi = 0.8, sp = 1, heal = 0.8, sta = 0.4, mp5 = 1 },
  SHAMAN  = { int = 0.8, str = 0.7, agi = 0.4, sp = 0.8, heal = 0.5, sta = 0.4, mp5 = 0.8, crit = 0.8 },
  MAGE    = { int = 1, sp = 1, sta = 0.5, spi = 0.5, hit = 1, crit = 1 },
  WARLOCK = { int = 1, sp = 1, sta = 0.6, spi = 0.5, hit = 1, crit = 1 },
  DRUID   = { int = 0.8, agi = 0.7, str = 0.6, sp = 0.7, heal = 0.6, spi = 0.6, sta = 0.4, mp5 = 0.6 },
}
local PREFERRED_WEAPONS = {
  WARRIOR = "sword axe mace polearm fist dagger bow gun xbow thrown",
  PALADIN = "sword axe mace polearm",
  HUNTER  = "sword axe polearm staff dagger fist bow gun xbow",
  ROGUE   = "sword mace dagger fist bow gun xbow thrown",
  PRIEST  = "staff mace dagger wand",
  SHAMAN  = "axe mace staff fist dagger",
  MAGE    = "staff sword dagger wand",
  WARLOCK = "staff sword dagger wand",
  DRUID   = "staff mace dagger fist",
}
for k, v in pairs(PREFERRED_WEAPONS) do
  local t = {}
  for w in v:gmatch("%a+") do t[w] = true end
  PREFERRED_WEAPONS[k] = t
end
local PRIMARY = { str = true, agi = true, sta = true, int = true, spi = true, ap = true, rap = true, sp = true,
  heal = true, critr = true, hitr = true, crit = true, hit = true, mp5 = true, def = true }

-- Does this item's stats and type fit what the class actually wants?
function TCF:GearSuits(it, class)
  if not self:GearUsable(it, class) then return false end
  local w = STAT_WEIGHTS[class]
  if it.sub and TYPE_NAMES[it.sub] and not ARMOR_RANK[it.sub] and it.sub ~= "shield" and it.sub ~= "misc" then
    if not PREFERRED_WEAPONS[class][it.sub] then return false end
  end
  local st = TCF.GearStats(it)
  local total, good = 0, 0
  for k, v in pairs(st) do
    if PRIMARY[k] then total = total + v; good = good + v * (w[k] or 0) end
  end
  if total == 0 then return true end
  return good / total >= 0.45
end

-- Equip slots an item can go in, for a class
function TCF:GearTargetSlots(it, class)
  local s = it.slot
  if s == "FINGER" then return { "FINGER1", "FINGER2" } end
  if s == "TRINKET" then return { "TRINKET1", "TRINKET2" } end
  if s == "MH" or s == "2H" then return { "MAINHAND" } end
  if s == "1H" then return CLASS_RULES[class].dual and { "MAINHAND", "OFFHAND" } or { "MAINHAND" } end
  if s == "OH" or s == "HOLD" or it.sub == "shield" then return { "OFFHAND" } end
  if s == "RANGED" then return { "RANGED" } end
  return { s }
end

---------------------------------------------------------------- ownership & equipping
function TCF:GearEquipped(class)
  local cd = self:CD(class)
  cd.gear = cd.gear or {}
  return cd.gear
end

function TCF:GearOwned(id) return (self.db.gear[id] or 0) > 0 end

function TCF:CanEquipGear(it, class, slotKey)
  class = class or self.db.class
  if not self:GearUsable(it, class) then return false, "Your " .. TCF.CLASS_BY_KEY[class].name .. " can't use this." end
  if self:CD(class).level < it.req then return false, "Requires class level " .. it.req .. "." end
  if not self:GearOwned(it.id) then return false, "You don't have this item." end
  if slotKey then
    local ok = false
    for _, s in ipairs(self:GearTargetSlots(it, class)) do if s == slotKey then ok = true end end
    if not ok then return false, "Doesn't fit that slot." end
  end
  return true
end

-- How many copies of an item are equipped on a class (rings/trinkets/1H can be doubled)
local function equippedCount(eq, id)
  local n = 0
  for _, v in pairs(eq) do if v == id then n = n + 1 end end
  return n
end

function TCF:EquipGear(id, slotKey, class)
  class = class or self.db.class
  local it = TCF.GEAR[id]
  if not it then return false end
  local targets = self:GearTargetSlots(it, class)
  slotKey = slotKey or targets[1]
  local eq = self:GearEquipped(class)
  -- prefer an empty second ring/trinket/offhand slot
  if not slotKey or (#targets > 1 and eq[slotKey] and not eq[targets[2]]) then slotKey = targets[2] or targets[1] end
  local ok, why = self:CanEquipGear(it, class, slotKey)
  if not ok then self:Print(why); return false end
  if equippedCount(eq, id) >= (self.db.gear[id] or 0) and eq[slotKey] ~= id then
    self:Print("You need another copy of " .. TCF.GearLink(it) .. " to equip it twice."); return false
  end
  eq[slotKey] = id
  if it.slot == "2H" then eq.OFFHAND = nil end
  if slotKey == "OFFHAND" and eq.MAINHAND and TCF.GEAR[eq.MAINHAND] and TCF.GEAR[eq.MAINHAND].slot == "2H" then eq.MAINHAND = nil end
  self:MarkDirty()
  self:RefreshAll()
  return true
end

function TCF:UnequipGear(slotKey, class)
  self:GearEquipped(class)[slotKey] = nil
  self:MarkDirty()
  self:RefreshAll()
end

function TCF.GearLink(it)
  return "|c" .. TCF.RARITY[it.q].hex .. "[" .. it.name .. "]|r"
end

function TCF:GearSellValue(it)
  -- vendor-style value in TapCoins; deliberately small
  return max(1, floor(it.ilvl * (it.q == 2 and 0.15 or it.q == 3 and 0.35 or it.q == 4 and 1.0 or 3) ))
end

function TCF:SellGear(id, all)
  local it = TCF.GEAR[id]
  local have = self.db.gear[id] or 0
  -- keep copies that are equipped by any class
  local inUse = 0
  for _, cd in pairs(self.db.classData) do inUse = max(inUse, equippedCount(cd.gear or {}, id)) end
  local spare = have - inUse
  if spare <= 0 then return 0 end
  local n = all and spare or 1
  self.db.gear[id] = have - n
  if self.db.gear[id] <= 0 then self.db.gear[id] = nil end
  local coins = self:GearSellValue(it) * n
  self:AddCoins(coins)
  self:Print(string.format("Sold %s%s for %d TapCoins.", TCF.GearLink(it), n > 1 and (" x" .. n) or "", coins))
  self:MarkDirty(); self:RefreshAll()
  return coins
end

-- Gives a gear item. Returns isNewItem.
function TCF:GrantGear(it, reason, reveal, chestKey)
  local have = self.db.gear[it.id] or 0
  self.db.gear[it.id] = have + 1
  self.db.stats.gearFound = (self.db.stats.gearFound or 0) + 1
  self:Print((reason and (reason .. ": ") or "") .. TCF.GearLink(it))
  if self.ShowLootReveal and (reveal or (self.window and self.window:IsShown())) then
    self:ShowLootReveal(it, have == 0, 0, reason, chestKey, true)
  elseif self.cat then
    self.cat:Toast("|T" .. TCF.Icon(it.icon) .. ":18:18|t " .. it.name, unpack(TCF.RARITY[it.q].color))
  end
  if it.q >= 4 then self:PlaySound("rare") else self:PlaySound("loot") end
  self:MarkDirty()
  self:RefreshAll()
  return have == 0
end

---------------------------------------------------------------- loot rolls
-- Weighted pick from a list using real drop chances; epics/legendaries are
-- extra rare (rarity damping) so top items stay a long-term goal.
local QDAMP = { [2] = 1, [3] = 1, [4] = 0.35, [5] = 0.05 }
local function weightedPick(list, usable)
  local total = 0
  for _, it in ipairs(list) do
    if usable(it) then total = total + max(5, it.dc) * QDAMP[it.q] end
  end
  if total <= 0 then return nil end
  local r = random() * total
  for _, it in ipairs(list) do
    if usable(it) then
      r = r - max(5, it.dc) * QDAMP[it.q]
      if r <= 0 then return it end
    end
  end
end

-- Boss loot: mostly items your class can use (80%), like real loot tables.
function TCF:RollBossLoot(tier, boss, class)
  class = class or self.db.class
  local list = TCF.BOSS_LOOT[tier] and TCF.BOSS_LOOT[tier][boss]
  if not list or #list == 0 then list = TCF.TIER_POOL[tier] end
  if not list then return nil end
  local own = random() < 0.8
  local pick = weightedPick(list, function(it) return (not own) or self:GearSuits(it, class) end)
  if not pick and own then pick = weightedPick(list, function(it) return self:GearUsable(it, class) end) end
  return pick
end

-- Trash / world loot near a level, by quality weights {unc, rare, epic}
function TCF:RollWorldLoot(level, class, weights, tier)
  class = class or self.db.class
  weights = weights or { 85, 13, 2 }
  local q = 2
  local r, acc = random() * (weights[1] + weights[2] + weights[3]), 0
  for i = 1, 3 do acc = acc + weights[i]; if r <= acc then q = i + 1; break end end
  local cands = {}
  local function scan(list)
    if not list then return end
    for _, it in ipairs(list) do
      if it.q == q and it.req <= level + 2 and it.req >= level - 8 and self:GearSuits(it, class) then cands[#cands + 1] = it end
    end
  end
  if tier and TCF.TIER_POOL[tier] then scan(TCF.TIER_POOL[tier]) end
  local band = floor(level / 5)
  for b = band - 2, band do scan(TCF.WORLD_POOL[b]) end
  if #cands == 0 then
    for b = band - 2, band do
      for _, it in ipairs(TCF.WORLD_POOL[b] or {}) do if it.q == 2 and self:GearUsable(it, class) then cands[#cands + 1] = it end end
    end
  end
  if #cands == 0 then return nil end
  return cands[random(#cands)]
end

---------------------------------------------------------------- combat stats from gear
-- Base attribute growth per level, roughly following Classic class stats.
local GROWTH = {
  WARRIOR = { str = 1.6, agi = 1.0, sta = 1.4, int = 0.2, spi = 0.5 },
  PALADIN = { str = 1.4, agi = 0.6, sta = 1.3, int = 0.8, spi = 0.8 },
  HUNTER  = { str = 0.6, agi = 1.6, sta = 1.2, int = 0.8, spi = 0.8 },
  ROGUE   = { str = 0.9, agi = 1.7, sta = 1.0, int = 0.3, spi = 0.6 },
  PRIEST  = { str = 0.3, agi = 0.4, sta = 0.8, int = 1.6, spi = 1.7 },
  SHAMAN  = { str = 1.1, agi = 0.6, sta = 1.2, int = 1.1, spi = 1.1 },
  MAGE    = { str = 0.3, agi = 0.4, sta = 0.7, int = 1.8, spi = 1.6 },
  WARLOCK = { str = 0.4, agi = 0.5, sta = 1.0, int = 1.5, spi = 1.5 },
  DRUID   = { str = 0.9, agi = 0.9, sta = 1.0, int = 1.3, spi = 1.4 },
}

function TCF:CombatStats(class, overrideItem, overrideSlot)
  class = class or self.db.class
  local L = min(60, self:CD(class).level)
  local g = GROWTH[class]
  local rule = CLASS_RULES[class]
  local t = { str = 0, agi = 0, sta = 0, int = 0, spi = 0, arm = 0, ap = 0, rap = 0, sp = 0, heal = 0,
    crit = 0, critr = 0, hit = 0, hitr = 0, def = 0, blk = 0, mp5 = 0, dodger = 0 }
  local eq = self:GearEquipped(class)
  local wMain, wOff, wRanged, ilvlSum, nItems = nil, nil, nil, 0, 0
  for _, s in ipairs(TCF.GEAR_SLOTS) do
    local id = eq[s.key]
    if overrideSlot == s.key then id = overrideItem and overrideItem.id end
    local it = id and TCF.GEAR[id]
    if it then
      local st = TCF.GearStats(it)
      for k, v in pairs(st) do if t[k] then t[k] = t[k] + v end end
      ilvlSum = ilvlSum + it.ilvl; nItems = nItems + 1
      if s.key == "MAINHAND" then wMain = st
      elseif s.key == "OFFHAND" and st.dps then wOff = st
      elseif s.key == "RANGED" then wRanged = st end
    end
  end
  for _, k in ipairs({ "str", "agi", "sta", "int", "spi" }) do t[k] = t[k] + floor(20 + L * g[k]) end

  local hp = 40 + L * 14 + max(0, t.sta - 20) * 10
  local armor = t.arm + t.agi * 2
  -- physical
  local ap
  if class == "ROGUE" or class == "HUNTER" then ap = t.str + t.agi + L * 2 else ap = t.str * 2 + L * 3 end
  ap = ap + t.ap
  local weaponDPS = wMain and (wMain.dps or 0) or (1 + L * 0.5)
  if wOff and rule.dual then weaponDPS = weaponDPS + wOff.dps * 0.5 end
  local melee = (weaponDPS + ap / 14) * 1.4   -- keeps melee on par with spellcasters
  local ranged = 0
  if class == "HUNTER" then
    local rap = t.agi * 2 + L * 2 + t.ap + t.rap
    ranged = ((wRanged and wRanged.dps or 1 + L * 0.3) + rap / 14) * 1.4
  end
  -- spells (wands add a little)
  local spell = 6 + L * 1.4 + (t.sp + t.heal * 0.25) * 0.35 + t.int * 0.05
  if wRanged and wRanged.dps and (class == "MAGE" or class == "WARLOCK" or class == "PRIEST") then spell = spell + wRanged.dps * 0.3 end

  local dps, crit
  if rule.role == "caster" then
    dps = spell; crit = 5 + t.int / 60
  elseif rule.role == "ranged" then
    dps = max(ranged, melee * 0.8); crit = 5 + t.agi / 20
  elseif rule.role == "hybrid" then
    if spell > melee then dps = spell; crit = 5 + t.int / 60 else dps = melee; crit = 5 + t.agi / 20 end
  else
    dps = melee; crit = 5 + t.agi / 20
  end
  crit = min(50, crit + t.crit + t.critr / 14)
  local hit = t.hit + t.hitr / 10
  local miss = max(0, 8 - hit) / 100
  dps = dps * (1 - miss)
  return {
    level = L, dps = dps, hp = hp, armor = armor, crit = crit, hit = hit,
    str = t.str, agi = t.agi, sta = t.sta, int = t.int, spi = t.spi, ap = ap, sp = t.sp, def = t.def,
    ilvl = nItems > 0 and floor(ilvlSum / nItems + 0.5) or 0, items = nItems,
    power = floor(dps * 10 + hp / 4 + armor / 10), -- one number for expeditions and comparisons
  }
end

---------------------------------------------------------------- appearance from gear
-- When no cosmetic is chosen for a visible slot, the cat wears its real gear.
local QTINT = {
  [2] = { { 0.55, 0.70, 0.45 }, { 0.75, 0.65, 0.45 }, { 0.62, 0.62, 0.66 } },
  [3] = { { 0.40, 0.60, 0.95 }, { 0.80, 0.82, 0.90 }, { 0.35, 0.45, 0.75 } },
  [4] = { { 0.62, 0.30, 0.90 }, { 1.00, 0.80, 0.35 }, { 0.80, 0.20, 0.25 } },
  [5] = { { 1.00, 0.55, 0.10 }, { 1.00, 0.85, 0.40 } },
}
local KEYWORD_TINT = {
  { "fire", { 1.0, 0.45, 0.15 } }, { "flame", { 1.0, 0.45, 0.15 } }, { "molten", { 1.0, 0.40, 0.10 } },
  { "frost", { 0.60, 0.90, 1.0 } }, { "ice", { 0.65, 0.90, 1.0 } }, { "shadow", { 0.45, 0.25, 0.70 } },
  { "blood", { 0.80, 0.12, 0.15 } }, { "gold", { 1.0, 0.82, 0.30 } }, { "holy", { 1.0, 0.92, 0.55 } },
  { "light", { 1.0, 0.92, 0.55 } }, { "nature", { 0.40, 0.80, 0.35 } }, { "wild", { 0.45, 0.70, 0.35 } },
  { "arcane", { 0.70, 0.50, 1.0 } }, { "dark", { 0.30, 0.25, 0.35 } }, { "black", { 0.25, 0.22, 0.28 } },
  { "storm", { 0.45, 0.65, 1.0 } }, { "thunder", { 0.45, 0.65, 1.0 } }, { "fel", { 0.45, 1.0, 0.30 } },
}
local function tintFor(it, n)
  local lname = it.name:lower()
  for _, kw in ipairs(KEYWORD_TINT) do
    if lname:find(kw[1], 1, true) then return kw[2] end
  end
  local set = QTINT[it.q] or QTINT[2]
  return set[(it.id + (n or 0)) % #set + 1]
end

local ART_FOR = {
  HEAD = { plate = "head_greathelm", mail = "head_hornhelm", leather = "head_hood", cloth = "head_wizard", misc = "head_circlet" },
  CHEST = { plate = "chest_plate", mail = "chest_mail", leather = "chest_leather", cloth = "chest_robe" },
  WEAPON = { sword = "wpn_sword", axe = "wpn_axe", mace = "wpn_mace", dagger = "wpn_dagger", staff = "wpn_staff",
    polearm = "wpn_spear", fist = "wpn_claws", wand = "wpn_wand", bow = "wpn_bow", gun = "wpn_rifle", xbow = "wpn_bow", thrown = "wpn_dagger" },
}
local CLASS_HEAD_CLOTH = { PRIEST = "head_hood", WARLOCK = "head_hood", MAGE = "head_wizard" }

local function look(art, it, slot)
  local c1 = tintFor(it, 0)
  local c2 = tintFor(it, 1)
  return { id = "gear:" .. it.id, art = art, c1 = c1, c2 = c2, rarity = it.q, slot = slot, name = it.name, icon = it.icon, gear = true }
end

-- Visible look items for a class from its equipped gear: head, chest, back, main, off
function TCF:GearAppearance(class)
  class = class or self.db.class
  local eq = self:GearEquipped(class)
  local out = {}
  local function get(k) return eq[k] and TCF.GEAR[eq[k]] end
  local h = get("HEAD")
  if h then
    local art = (h.sub == "cloth" and CLASS_HEAD_CLOTH[class]) or ART_FOR.HEAD[h.sub] or "head_circlet"
    out.head = look(art, h, "head")
  end
  local c = get("CHEST")
  if c then out.chest = look(ART_FOR.CHEST[c.sub] or "chest_robe", c, "chest") end
  local b = get("BACK")
  if b then out.back = look("back_cape", b, "back") end
  local m = get("MAINHAND")
  if class == "HUNTER" and get("RANGED") then m = get("RANGED") end
  if m then
    local art = ART_FOR.WEAPON[m.sub] or "wpn_sword"
    if m.slot == "2H" and m.sub == "sword" then art = "wpn_greatsword" end
    if m.slot == "2H" and m.sub == "mace" then art = "wpn_hammer" end
    out.main = look(art, m, "main")
  end
  local o = get("OFFHAND")
  if o then
    local art
    if o.sub == "shield" then art = o.q >= 3 and "off_kiteshield" or "off_roundshield"
    elseif o.slot == "HOLD" then art = (o.id % 3 == 0) and "off_orb" or (o.id % 3 == 1) and "off_tome" or "off_lantern"
    elseif o.sub == "dagger" then art = "off_dagger" else art = "off_sword" end
    out.off = look(art, o, "off")
  end
  return out
end

-- A starter weapon so a fresh cat isn't fighting bare-pawed.
function TCF:StarterGear(class)
  local best
  for _, it in ipairs(TCF.WORLD_POOL[0] or {}) do
    if it.q == 2 and (it.slot == "MH" or it.slot == "1H" or it.slot == "2H" or (class == "HUNTER" and it.slot == "RANGED"))
      and it.req <= 5 and self:GearUsable(it, class) and (not best or it.id < best.id) then
      best = it
    end
  end
  if best then
    self.db.gear[best.id] = (self.db.gear[best.id] or 0) + 1
    local eq = self:GearEquipped(class)
    eq[best.slot == "RANGED" and "RANGED" or "MAINHAND"] = best.id
  end
end
