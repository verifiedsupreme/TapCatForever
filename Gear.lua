-- TapCatForever: real WoW gear (stats, class proficiencies, equipping, loot)
-- Item data lives in GearData.lua (generated from real Classic item data).
local ADDON, TCF = ...

local floor, min, max, random = math.floor, math.min, math.max, math.random

TCF.GEAR = {}
TCF.GEAR_LIST = {}
TCF.BOSS_LOOT = {}   -- [tier][boss] = { item, ... }
TCF.TIER_POOL = {}   -- [tier] = { item, ... } (zone drops, other bosses)
TCF.WORLD_POOL = {}  -- [level band (req level // 5)] = { item, ... }

-- Blizzard's placeholder/test items that leaked into the data. They stay known (so old
-- saves still show them) but never drop.
local function isPlaceholder(name, ilvl)
  return ilvl == 0 or name:sub(1, 2) == "zz" or name:find("OLD", 1, true) or name:find("(Extra Effects)", 1, true)
    or name:sub(1, 6) == "Bland "
end

-- Called once per item by GearData.lua (and by CraftData.lua for crafted items that only
-- exist there: crafted = "blacksmithing" / "leatherworking" / "tailoring").
-- Crafted gear is never loot: it goes into TCF.GEAR and TCF.GEAR_LIST only.
function TCF.AddGear(id, name, icon, q, ilvl, req, slot, sub, stats, tier, boss, dc, cls, crafted)
  if crafted and TCF.GEAR[id] then return TCF.MarkCrafted(id, crafted) end
  -- Many quest/vendor items have no level requirement in the data, which would put
  -- ilvl 40-70 gear in the level 1-4 loot band. Give them the usual "item level - 5".
  if req == 0 and ilvl > 10 then req = min(60, max(1, ilvl - 5)) end
  local it = { id = id, name = name, icon = icon, q = q, ilvl = ilvl, req = req, slot = slot, sub = sub,
    statStr = stats, tier = tier, boss = boss, dc = dc, cls = cls }
  TCF.GEAR[id] = it
  TCF.GEAR_LIST[#TCF.GEAR_LIST + 1] = it
  if crafted then it.crafted, it.tier, it.boss, it.dc = crafted, 0, 0, 0; return end
  if isPlaceholder(name, ilvl) then return end
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

-- CraftData.lua: an item GearData.lua already has becomes crafted gear. It leaves every loot
-- pool (boss loot, zone loot, world drops) so the only way to get it is to make it.
local function dropFrom(list, it)
  if not list then return end
  for i = #list, 1, -1 do if list[i] == it then table.remove(list, i) end end
end
function TCF.MarkCrafted(id, craft)
  local it = TCF.GEAR[id]
  if not it then return end
  dropFrom(TCF.WORLD_POOL[floor(it.req / 5)], it)
  if it.tier and it.tier > 0 then
    dropFrom(TCF.TIER_POOL[it.tier], it)
    for _, list in pairs(TCF.BOSS_LOOT[it.tier] or {}) do dropFrom(list, it) end
  end
  it.crafted, it.tier, it.boss, it.dc = craft, 0, 0, 0
  return it
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
-- How many copies of an item are equipped on a class (rings/trinkets/1H can be doubled)
local function equippedCount(eq, id)
  local n = 0
  for _, v in pairs(eq) do if v == id then n = n + 1 end end
  return n
end
TCF.GearEquippedCount = equippedCount

function TCF:GearEquipped(class)
  local cd = self:CD(class)
  cd.gear = cd.gear or {}
  return cd.gear
end

-- Each cat class has its own gear bag. Older saves kept one bag for all classes:
-- that is split once (items a class wears stay with it, the rest go to the current class).
function TCF:Bag(class)
  local db = self.db
  if db.gear and next(db.gear) then
    local pool = db.gear
    for key, cd in pairs(db.classData) do
      cd.bag = cd.bag or {}
      for _, id in pairs(cd.gear or {}) do
        if (pool[id] or 0) > 0 then
          cd.bag[id] = (cd.bag[id] or 0) + 1; pool[id] = pool[id] - 1
          if pool[id] <= 0 then pool[id] = nil end
        elseif (cd.bag[id] or 0) < equippedCount(cd.gear, id) then
          -- the old shared bag let several classes wear one copy: each wearer keeps one
          cd.bag[id] = (cd.bag[id] or 0) + 1
        end
      end
    end
    local cur = db.classData[db.class]
    cur.bag = cur.bag or {}
    for id, n in pairs(pool) do cur.bag[id] = (cur.bag[id] or 0) + n end
    db.gear = {}
  end
  local cd = self:CD(class)
  cd.bag = cd.bag or {}
  -- Saves split by 1.3.1-1.3.3 (before the repair above) can have worn-but-unowned
  -- copies: once per class, top the bag up to what the class is wearing.
  -- Selling never takes worn copies, so this cannot hand back something already sold.
  if not cd.bagChecked then
    for _, id in pairs(cd.gear or {}) do
      local worn = equippedCount(cd.gear, id)
      if (cd.bag[id] or 0) < worn then cd.bag[id] = worn end
    end
    cd.bagChecked = true
  end
  return cd.bag
end

function TCF:GearOwned(id, class) return (self:Bag(class)[id] or 0) > 0 end

function TCF:CanEquipGear(it, class, slotKey)
  class = class or self.db.class
  if not self:GearUsable(it, class) then return false, "Your " .. TCF.CLASS_BY_KEY[class].name .. " can't use this." end
  if self:CD(class).level < it.req then return false, "Requires class level " .. it.req .. "." end
  if not self:GearOwned(it.id, class) then return false, "You don't have this item." end
  if slotKey then
    local ok = false
    for _, s in ipairs(self:GearTargetSlots(it, class)) do if s == slotKey then ok = true end end
    if not ok then return false, "Doesn't fit that slot." end
  end
  return true
end

local function isTwoHand(id) return id and TCF.GEAR[id] and TCF.GEAR[id].slot == "2H" end

-- Which slot "Equip" puts an item in when the player didn't pick one. The Gear page's
-- "+N power" uses the same choice, so the number shown is what the click does.
function TCF:BestGearSlot(it, class)
  class = class or self.db.class
  local targets = self:GearTargetSlots(it, class)
  if #targets == 1 then return targets[1] end
  local eq = self:GearEquipped(class)
  -- a one-hander replaces a two-hander (it can't go next to it)
  if it.slot == "1H" and isTwoHand(eq.MAINHAND) then return "MAINHAND" end
  -- fill an empty slot first (main hand before off hand, ring 1 before ring 2)
  for _, s in ipairs(targets) do if not eq[s] then return s end end
  -- all full: replace whichever gives the most power; a slot already holding this
  -- item only counts if every slot holds it (wearing a second copy is the point)
  local best, bestPower
  for _, s in ipairs(targets) do
    if eq[s] ~= it.id then
      local p = self:CombatStats(class, it, s).power
      if not bestPower or p > bestPower then best, bestPower = s, p end
    end
  end
  return best or targets[1]
end

function TCF:EquipGear(id, slotKey, class)
  class = class or self.db.class
  local it = TCF.GEAR[id]
  if not it then return false end
  slotKey = slotKey or self:BestGearSlot(it, class)
  local eq = self:GearEquipped(class)
  local ok, why = self:CanEquipGear(it, class, slotKey)
  if not ok then self:Print(why, true); return false end
  if equippedCount(eq, id) >= (self:Bag(class)[id] or 0) and eq[slotKey] ~= id then
    self:Print("You need another copy of " .. TCF.GearLink(it) .. " to equip it twice.", true); return false
  end
  eq[slotKey] = id
  if it.slot == "2H" then eq.OFFHAND = nil end
  if slotKey == "OFFHAND" and eq.MAINHAND and TCF.GEAR[eq.MAINHAND] and TCF.GEAR[eq.MAINHAND].slot == "2H" then eq.MAINHAND = nil end
  self:MarkDirty()
  self:RefreshAll()
  return true
end

function TCF:UnequipGear(slotKey, class)
  self:Bag(class) -- runs the one-time bag repair first, so the item stays owned
  self:GearEquipped(class)[slotKey] = nil
  self:MarkDirty()
  self:RefreshAll()
end

function TCF.GearLink(it)
  return "|c" .. TCF.RARITY[it.q].hex .. "[" .. it.name .. "]|r"
end

-- Material tier -> its value; ore is the base value of every family's material of that tier
-- (cloth's own sale value may differ, crafted gear doesn't depend on it)
local TIER_ORE = { "copper", "tin", "iron", "mithril", "thorium", "arcane" }
local function craftMatValue(it)
  local v = 0
  for k, n in pairs(it.craftMats or {}) do
    local tier = TCF.CRAFT_MAT_TIER and TCF.CRAFT_MAT_TIER[k]
    local m = tier and TCF.MAT_BY_KEY and TCF.MAT_BY_KEY[TIER_ORE[tier]]
    v = v + n * (m and m.value or 1)
  end
  return v
end

-- What one copy sells for, and in what: "coins" (TapCoins, found gear) or "gold" (Trade Gold,
-- crafted gear: half its material value, so TapCoins stay scarce and crafting is no exploit)
function TCF:GearSellValue(it)
  if it.crafted then return max(1, floor(craftMatValue(it) * 0.5)), "gold" end
  -- vendor-style value in TapCoins; deliberately small
  return max(1, floor(it.ilvl * (it.q == 2 and 0.15 or it.q == 3 and 0.35 or it.q == 4 and 1.0 or 3) )), "coins"
end

-- "1,234 TapCoins" / "1,234 Trade Gold"
function TCF:GearSellText(it, n)
  local v, cur = self:GearSellValue(it)
  return TCF.Commas(v * (n or 1)) .. (cur == "gold" and " Trade Gold" or " TapCoins")
end

-- pays for sold gear; returns what was actually added
local function payFor(self, it, n)
  local v, cur = self:GearSellValue(it)
  if cur == "gold" then return 0, self.EarnGold and self:EarnGold(v * n) or 0 end
  self:AddCoins(v * n)
  return v * n, 0
end

-- "Junk" for the current class: copies of an item beyond what the cat can wear at once, and
-- every unworn copy of an item that would lower the cat's Power. Better items (including ones
-- the cat isn't high enough level for yet) and items this class can't use are never junk.
-- Returns { [id] = copies } plus the item count, TapCoins and Trade Gold (crafted gear).
function TCF:JunkGear(class)
  class = class or self.db.class
  local eq = self:GearEquipped(class)
  local junk, count, coins, gold = {}, 0, 0, 0
  -- with a two-hander worn, a one-hander or off-hand item on its own always looks worse (it
  -- replaces half of the pair), so hand items are only sold as extra copies then
  local twoHand = isTwoHand(eq.MAINHAND)
  local HAND = { MH = true, ["1H"] = true, OH = true, HOLD = true }
  for id, have in pairs(self:Bag(class)) do
    local it = TCF.GEAR[id]
    if it and have > 0 then
      local worn = equippedCount(eq, id)
      local keep
      if not self:GearUsable(it, class) then
        keep = worn   -- this class can never wear it (each class has its own bag)
      else
        keep = math.max(worn, #self:GearTargetSlots(it, class))
        if worn == 0 and not (twoHand and HAND[it.slot]) then
          local d = self:GearUpgrade(it, class)
          if d and d < 0 then keep = 0 end
        end
      end
      local n = have - keep
      if n > 0 then
        junk[id] = n
        local v, cur = self:GearSellValue(it)
        if cur == "gold" then gold = gold + v * n else coins = coins + v * n end
        count = count + n
      end
    end
  end
  return junk, count, coins, gold
end

-- Copies of an item this class could sell (everything it isn't wearing)
function TCF:GearSpare(id)
  return (self:Bag()[id] or 0) - equippedCount(self:GearEquipped(), id)
end

-- Removes unworn copies and pays for them. No chat line, no refresh.
-- Returns copies sold, TapCoins and Trade Gold paid.
local function sellCopies(self, id, all)
  local it = TCF.GEAR[id]
  local spare = self:GearSpare(id)
  if not it or spare <= 0 then return 0, 0, 0 end
  local n = all and spare or 1
  local bag = self:Bag()
  bag[id] = bag[id] - n
  if bag[id] <= 0 then bag[id] = nil end
  local coins, gold = payFor(self, it, n)
  return n, coins, gold
end

-- "12 TapCoins", "40 Trade Gold" or both
local function paidText(coins, gold)
  local parts = {}
  if coins > 0 or gold <= 0 then parts[#parts + 1] = TCF.Commas(coins) .. " TapCoins" end
  if gold > 0 then parts[#parts + 1] = TCF.Commas(floor(gold + 0.5)) .. " Trade Gold" end
  return table.concat(parts, " and ")
end

-- Returns the TapCoins paid (0 for crafted gear) and the Trade Gold paid.
function TCF:SellGear(id, all)
  local it = TCF.GEAR[id]
  local n, coins, gold = sellCopies(self, id, all)
  if n == 0 then return 0, 0 end
  self:Print(string.format("Sold %s%s for %s.", TCF.GearLink(it), n > 1 and (" x" .. n) or "", paidText(coins, gold)), true)
  self:MarkDirty(); self:RefreshAll()
  return coins, gold
end

-- "Sell junk": one chat line and one refresh for the whole bag
function TCF:SellJunk()
  local junk = self:JunkGear()
  local bag = self:Bag()
  local count, total, gold = 0, 0, 0
  for id, n in pairs(junk) do
    local it = TCF.GEAR[id]
    bag[id] = bag[id] - n
    if bag[id] <= 0 then bag[id] = nil end
    local c, g = payFor(self, it, n)
    count, total, gold = count + n, total + c, gold + g
  end
  if count == 0 then return 0, 0 end
  self:Print(string.format("Sold %d %s of junk for %s.", count, count == 1 and "item" or "items", paidText(total, gold)), true)
  self:MarkDirty(); self:RefreshAll()
  return total, gold
end

-- Gives a gear item. Returns isNewItem.
function TCF:GrantGear(it, reason, reveal, chestKey)
  local bag = self:Bag()
  local have = bag[it.id] or 0
  bag[it.id] = have + 1
  -- crafted gear is made, not found: it has its own 'crafted' stat and achievements
  if not it.crafted then self.db.stats.gearFound = (self.db.stats.gearFound or 0) + 1 end
  self:Print((reason and (reason .. ": ") or "") .. TCF.GearLink(it))
  -- a chest you opened (chestKey) gets the reel and loot box; gear found anywhere else gets a
  -- small notice instead (ChestReel.lua decides)
  if self.ShowLootReveal then self:ShowLootReveal(it, have == 0, 0, reason, chestKey, true) end
  if it.q >= 4 then self:PlaySound("rare") else self:PlaySound("loot") end
  self:MarkDirty()
  self:RefreshAll()
  return have == 0
end

---------------------------------------------------------------- loot rolls
-- Weighted pick from a list using real drop chances; epics/legendaries are
-- extra rare (rarity damping) so top items stay a long-term goal.
local QDAMP = { [1] = 1, [2] = 1, [3] = 1, [4] = 0.35, [5] = 0.05 }
local function weightedPick(list, usable)
  local total = 0
  for _, it in ipairs(list) do
    if not it.crafted and usable(it) then total = total + max(5, it.dc) * QDAMP[it.q] end
  end
  if total <= 0 then return nil end
  local r = random() * total
  for _, it in ipairs(list) do
    if not it.crafted and usable(it) then
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
  -- 80% something made for this class; 20% anything it can wear (maybe off-spec).
  -- Never gear it can't use at all: bags are per class, so that would be dead loot.
  local own = random() < 0.8
  local pick = weightedPick(list, function(it)
    if own then return self:GearSuits(it, class) end
    return self:GearUsable(it, class)
  end)
  if not pick and own then pick = weightedPick(list, function(it) return self:GearUsable(it, class) end) end
  return pick
end

-- Trash / world loot near a level, by quality weights {unc, rare, epic}
-- If the rolled quality has nothing near the level, the search widens (a little higher
-- level, plus zone and boss loot of zones at this level) before dropping one quality.
function TCF:RollWorldLoot(level, class, weights, tier)
  class = class or self.db.class
  -- cat levels keep climbing but world gear ends at level 60
  level = min(60, max(1, level or 1))
  weights = weights or { 85, 13, 2 }
  local q = 2
  local r, acc = random() * (weights[1] + weights[2] + weights[3]), 0
  for i = 1, 3 do acc = acc + weights[i]; if r <= acc then q = i + 1; break end end
  local suits = function(it) return self:GearSuits(it, class) end
  local usable = function(it) return self:GearUsable(it, class) end
  local function find(wq, test, wide)
    local lo, hi = level - 8, level + (wide and 5 or 2)
    local cands, seen = {}, {}
    local function scan(list)
      if not list then return end
      for _, it in ipairs(list) do
        if it.q == wq and it.req <= hi and it.req >= lo and not seen[it] and not it.crafted and test(it) then
          seen[it] = true; cands[#cands + 1] = it
        end
      end
    end
    if tier then scan(TCF.TIER_POOL[tier]) end
    for b = floor(max(0, lo) / 5), floor(hi / 5) do scan(TCF.WORLD_POOL[b]) end
    if wide and TCF.TIERS then
      for ti, t in ipairs(TCF.TIERS) do
        if level >= t.min and level <= t.max then
          scan(TCF.TIER_POOL[ti])
          for _, list in pairs(TCF.BOSS_LOOT[ti] or {}) do scan(list) end
        end
      end
    end
    if #cands > 0 then return cands[random(#cands)] end
  end
  for wq = q, 2, -1 do
    local it = find(wq, suits) or find(wq, suits, true) or find(wq, usable, true)
    if it then return it end
  end
  return nil
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
  -- what equipping the override would also take off: a 2H empties the off hand,
  -- and an off-hand item can't stay next to a 2H
  local cleared
  if overrideItem and overrideSlot == "MAINHAND" and overrideItem.slot == "2H" then cleared = "OFFHAND"
  elseif overrideItem and overrideSlot == "OFFHAND" and isTwoHand(eq.MAINHAND) then cleared = "MAINHAND" end
  local wMain, wOff, wRanged, ilvlSum, nItems = nil, nil, nil, 0, 0
  for _, s in ipairs(TCF.GEAR_SLOTS) do
    local id = eq[s.key]
    if overrideSlot == s.key then id = overrideItem and overrideItem.id end
    if cleared == s.key then id = nil end
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
  -- Well Fed buffs from Cooking
  if self.FoodBuff then dps = dps * self:FoodBuff("dmg", class); hp = hp * self:FoodBuff("hp", class) end
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
-- override: a gear item to show as if equipped (hover preview), in its first usable slot
function TCF:GearAppearance(class, override)
  class = class or self.db.class
  local eq = self:GearEquipped(class)
  local out = {}
  local oslot = override and (self:GearTargetSlots(override, class) or {})[1]
  local function get(k)
    if oslot and (k == oslot or (k == "FINGER1" and oslot == "FINGER2")) then return override end
    if oslot == "MAINHAND" and override.slot == "2H" and k == "OFFHAND" then return nil end
    return eq[k] and TCF.GEAR[eq[k]]
  end
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
  -- small pieces only the cartoon cat draws (neck, belt, ring)
  local n, w, r = get("NECK"), get("WAIST"), get("FINGER1") or get("FINGER2")
  if n then out.neck = look("acc_bell", n, "neck") end
  if w then out.belt = look("acc_bell", w, "belt") end
  if r then out.ring = look("acc_bell", r, "ring") end
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

-- A starter weapon so a fresh cat isn't fighting bare-pawed: the weapon each class is known
-- for (a bow for hunters, a dagger for rogues, a staff for mages...), the plainest one there is.
TCF.STARTER_WEAPONS = {
  WARRIOR = { "sword", "axe" }, PALADIN = { "mace", "sword" }, HUNTER = { "bow", "gun", "xbow" },
  ROGUE = { "dagger" }, PRIEST = { "mace", "staff" }, SHAMAN = { "mace", "axe" },
  MAGE = { "staff" }, WARLOCK = { "staff", "dagger" }, DRUID = { "staff", "mace" },
}
local STARTER_MAX_REQ = 10
local function isStarterCandidate(self, it, class)
  return it.q == 2 and (it.slot == "MH" or it.slot == "1H" or it.slot == "2H" or it.slot == "RANGED")
    and it.req <= STARTER_MAX_REQ and not it.crafted and self:GearUsable(it, class)
end
function TCF:StarterWeapon(class)
  for _, sub in ipairs(TCF.STARTER_WEAPONS[class] or {}) do
    local best
    for band = 0, floor(STARTER_MAX_REQ / 5) do
      for _, it in ipairs(TCF.WORLD_POOL[band] or {}) do
        if it.sub == sub and isStarterCandidate(self, it, class)
          and (not best or it.ilvl < best.ilvl or (it.ilvl == best.ilvl and it.id < best.id)) then
          best = it
        end
      end
    end
    if best then return best end
  end
end

function TCF:StarterGear(class)
  local best = self:StarterWeapon(class)
  if best then
    local bag = self:Bag(class)
    bag[best.id] = (bag[best.id] or 0) + 1
    local eq = self:GearEquipped(class)
    eq[best.slot == "RANGED" and "RANGED" or "MAINHAND"] = best.id
  end
end

-- Older versions gave every class the lowest-numbered green weapon it could use from the
-- level 0-4 world pool (a staff for hunters, a hammer for rogues). A cat still wearing exactly
-- that weapon gets its class weapon instead (the old one stays in the bag); a cat with no weapon
-- at all gets one. Anything the player chose is left alone. Runs once per character and class.
local function oldStarter(self, class)
  local best
  for _, it in ipairs(TCF.WORLD_POOL[0] or {}) do
    if it.q == 2 and not it.crafted and it.req <= 5
      and (it.slot == "MH" or it.slot == "1H" or it.slot == "2H" or (class == "HUNTER" and it.slot == "RANGED"))
      and self:GearUsable(it, class) and (not best or it.id < best.id) then
      best = it
    end
  end
  return best
end
function TCF:FixStarterWeapons()
  for _, cl in ipairs(TCF.CLASSES) do
    local class = cl.key
    local cd = self:CD(class)
    if cd and not cd.starterFixed then
      cd.starterFixed = true
      local new = self:StarterWeapon(class)
      local eq = self:GearEquipped(class)
      local old = oldStarter(self, class)
      local slot = new and (new.slot == "RANGED" and "RANGED" or "MAINHAND")
      local wearingOld = old and (eq.MAINHAND == old.id or eq.RANGED == old.id)
      local noWeapon = not eq.MAINHAND and not eq.RANGED
      if new and (not old or old.id ~= new.id) and (wearingOld or noWeapon) then
        local bag = self:Bag(class)
        bag[new.id] = (bag[new.id] or 0) + 1
        if wearingOld and eq.MAINHAND == old.id and slot == "RANGED" then
          -- a hunter's old staff stays on; the cat shows the bow over it
        elseif wearingOld and eq.RANGED == old.id and slot == "MAINHAND" then
          eq.RANGED = nil
        end
        eq[slot] = new.id
        if new.slot == "2H" then eq.OFFHAND = nil end   -- a two-hander can't share with an off-hand
      end
    end
  end
end
