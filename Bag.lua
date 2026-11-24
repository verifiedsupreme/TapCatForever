-- TapCatForever: the Profession Bag (1.7.0). Every kind of material a cat has, in one place, with
-- tabs (Gathered, Rare, Daily, Herbs & Potions, Fish & Food, Bandages), what each one is used for, and
-- selling leftovers for Trade Gold.
-- Bags (bought with TapCoins, for the whole account): every kind of material always fits, but a bag
-- has a stack size. Goods past it are sold right away for Trade Gold, so nothing is wasted; a pile a
-- cat already had above the size when it got the bag is kept (it only shrinks as you use it).
local ADDON, TCF = ...
local floor, min, max = math.floor, math.min, math.max

TCF.MAT_BAGS = {
  { key = "linen",      name = "Linen Bag",      icon = "INV_Misc_Bag_09",        cap = 20000,   coins = 0 },
  { key = "wool",       name = "Wool Bag",       icon = "INV_Misc_Bag_10",        cap = 50000,   coins = 500 },
  { key = "silk",       name = "Silk Bag",       icon = "INV_Misc_Bag_10_Blue",   cap = 150000,  coins = 1500 },
  { key = "mageweave",  name = "Mageweave Bag",  icon = "INV_Misc_Bag_10_Red",    cap = 500000,  coins = 4000 },
  { key = "runecloth",  name = "Runecloth Bag",  icon = "INV_Misc_Bag_EnchantedRunecloth", cap = 2e6, coins = 10000 },
  { key = "mooncloth",  name = "Mooncloth Bag",  icon = "INV_Misc_Bag_EnchantedMageweave", cap = 1e7, coins = 25000 },
  { key = "bottomless", name = "Bottomless Bag", icon = "INV_Misc_Bag_CoreFelcloth", cap = math.huge, coins = 60000 },
}

function TCF:MatBagLevel()
  local db = self.db
  return min(#TCF.MAT_BAGS, max(1, db and tonumber(db.matBag) or 1))
end
function TCF:MatBag() return TCF.MAT_BAGS[self:MatBagLevel()] end
function TCF:MatStackCap() return self:MatBag().cap end

function TCF:BuyMatBag()
  local nxt = TCF.MAT_BAGS[self:MatBagLevel() + 1]
  if not nxt then return false, "You already have the biggest bag." end
  if (self.db.coins or 0) < nxt.coins then return false, string.format("The %s costs %s TapCoins.", nxt.name, TCF.Commas(nxt.coins)) end
  self:SpendCoins(nxt.coins)
  self.db.matBag = self:MatBagLevel() + 1
  self:Print(string.format("New bag: |cffffd100%s|r. Stacks hold %s now.", nxt.name, nxt.cap == math.huge and "any amount" or TCF.Commas(nxt.cap)), true)
  self:PlaySound("buy")
  self:MarkDirty()
  return true
end

-- the bag's stack size for one of a cat's materials: the bag's, or the pile it already had
local function capFor(self, s, key)
  local cap = self:MatStackCap()
  local keep = s.bagKeep and s.bagKeep[key]
  return keep and max(cap, keep) or cap
end
function TCF:MatCapFor(key) return capFor(self, self:ProfState(), key) end

-- keeps a cat's materials inside the bag (Professions.lua TCF:ProfAdvance, every tick): what grew past
-- its stack size is sold for Trade Gold. The first time, every pile over the size is remembered.
function TCF:MatBagTrim()
  local s = self:ProfState()
  if type(s.mats) ~= "table" then return end
  local cap = self:MatStackCap()
  if type(s.bagKeep) ~= "table" then
    s.bagKeep = {}
    for k, n in pairs(s.mats) do if type(n) == "number" and n > cap then s.bagKeep[k] = floor(n) end end
  end
  local sold = 0
  for k, n in pairs(s.mats) do
    if type(n) == "number" then
      local keep = s.bagKeep[k]
      if keep then
        -- a kept pile shrinks with use, and is forgotten once it fits the bag
        if n < keep then keep = floor(n); s.bagKeep[k] = keep end
        if keep <= cap then s.bagKeep[k] = nil; keep = nil end
      end
      local limit = keep and max(cap, keep) or cap
      if n > limit then
        local extra = n - limit
        s.mats[k] = limit
        local m = TCF.MAT_BY_KEY[k]
        sold = sold + self:EarnGold(extra * ((m and m.value) or 1))
        s.bagSoldN = (s.bagSoldN or 0) + extra
      end
    end
  end
  if sold > 0 then s.bagSold = (s.bagSold or 0) + sold end
end

---------------------------------------------------------------- tabs and uses
TCF.BAG_TABS = {
  { key = "gathered", name = "Gathered" },
  { key = "rare",     name = "Rare" },
  { key = "daily",    name = "Daily" },
  { key = "herbs",    name = "Herbs" },
  { key = "food",     name = "Fish & Food" },
  { key = "bandages", name = "Bandages" },
}
function TCF.MatTab(key)
  local m = TCF.MAT_BY_KEY[key]
  if not m then return nil end
  if (TCF.RARE_FIND_BY_KEY and TCF.RARE_FIND_BY_KEY[key]) or (TCF.RARE_BY_KEY and TCF.RARE_BY_KEY[key]) or key == "pinchy" then return "rare" end
  if TCF.DAILY_MATS and TCF.DAILY_MATS[key] then return "daily" end
  if m.prof == "herbalism" then return "herbs" end
  if m.prof == "fishing" or m.prof == "cooking" then return "food" end
  if m.prof == "firstaid" then return "bandages" end
  return "gathered"
end
-- the materials of a tab this cat has, sorted by name
function TCF:BagList(tab)
  local s = self:ProfState()
  local list = {}
  for k, n in pairs(s.mats or {}) do
    if type(n) == "number" and n >= 1 and TCF.MatTab(k) == tab then list[#list + 1] = k end
  end
  table.sort(list, function(a, b) return (TCF.MAT_BY_KEY[a].name or a) < (TCF.MAT_BY_KEY[b].name or b) end)
  return list
end

-- what a material is for: recipes (crafted items, potions, dishes, bandages), daily crafts, open orders
function TCF:MatUses(key)
  local out, seen = {}, {}
  local function add(s) if s and not seen[s] then seen[s] = true; out[#out + 1] = s end end
  for _, list in pairs(TCF.RECIPES) do
    for _, r in ipairs(list) do
      if r.mats and r.mats[key] then
        local it = self:RecipeItem(r)
        local def = r.set and TCF.COSMETIC_SET_BY_KEY and TCF.COSMETIC_SET_BY_KEY[r.set]
        add(def and def.name or (it and it.name))
      end
    end
  end
  for dk, d in pairs(TCF.DAILY_MATS or {}) do if d.mats[key] then add(d.name .. " (daily craft)") end end
  for _, r in ipairs(TCF.COOK_RECIPES or {}) do for _, ing in ipairs(r[4]) do if ing == key then add(r[2]) end end end
  for _, b in ipairs(TCF.BANDAGES or {}) do if b[4] == key then add(b[2]) end end
  if TCF.SEED_BY_KEY and TCF.SEED_BY_KEY[key] then add("selling and cooking") end
  if self.WorkOrders and self.CraftProf then
    local ok, orders = pcall(self.WorkOrders, self)
    if ok then for _, o in ipairs(orders or {}) do if o.kind == "mat" and o.key == key then add("a work order") end end end
  end
  return out
end

-- sell a whole stack for Trade Gold
function TCF:SellMatStack(key)
  local s = self:ProfState()
  local n = floor(s.mats[key] or 0)
  if n <= 0 then return 0 end
  local m = TCF.MAT_BY_KEY[key]
  s.mats[key] = s.mats[key] - n
  local g = self:EarnGold(n * ((m and m.value) or 1))
  self:Print(string.format("Sold %s %s for %s.", TCF.Commas(n), m and m.name or key, TCF.GoldStr(g)), true)
  self:MarkDirty()
  return g
end
