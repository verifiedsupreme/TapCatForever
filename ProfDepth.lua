-- TapCatForever: profession depth (1.7.0), for the three crafting skills (Blacksmithing,
-- Leatherworking, Tailoring):
--   * Specializations at skill 225, like Classic: Tailoring (Mooncloth, Shadoweave, Spellfire),
--     Blacksmithing (Armorsmith, Weaponsmith), Leatherworking (Dragonscale, Tribal). Each gives its
--     own daily craft, its long-chase set (ProfSets.lua) and a small perk.
--   * Daily crafts: one special material a day (every 20 hours) made by your specialization:
--     Primal Mooncloth, Shadowcloth, Spellcloth, Enchanted Thorium Bar, Arcanite Bar, Cured Rugged
--     Hide, Enchanted Leather. The long-chase sets need many of them.
--   * Guilds and work orders: your craft's guild (Silken Thread, Thorium Brotherhood, Hide and Hunt
--     Lodge) posts orders: bring materials, crafted gear, a rare find or a daily material. Orders pay
--     Trade Gold, TapCoins and reputation; reputation raises your rank from Initiate to Grand Master,
--     and the best recipes need a rank. Grand Master gives a title.
--   * Masterwork: crafted gear sometimes comes out as a Masterwork version with better stats (and one
--     step better quality). Its id is the gear's id in the random-suffix scheme with suffix 99, so an
--     older addon in your party still knows what it is.
--   * Renown shop: selling the business gives Renown points as well as Renown. Spend them on perks that
--     stay forever: Sharp Tools, Keen Eye, Glint Seeker, Busy Hands, Guild Ties, Rested Hands, Steady Hands.
--   * Titles: earned titles (Grand Master ranks, whole sets) can be shown in place of the level title.
-- Everything is per cat (the class's own trade), like the rest of the professions.
local ADDON, TCF = ...
local floor, min, max, random = math.floor, math.min, math.max, math.random

local function S(self) return self:ProfState() end
local function craftOf(self) return self:CraftProf() end

---------------------------------------------------------------- specializations and daily crafts
TCF.SPEC_SKILL = 225
TCF.SPEC_SWITCH_COINS = 500
TCF.DAILY_HOURS, TCF.DAILY_HOURS_RESTED = 20, 16
TCF.SPECS = {
  tailoring = {
    { key = "mooncloth",  name = "Mooncloth Tailoring",  icon = "Spell_Nature_AstralRecal", daily = "primalmooncloth",
      perk = "Your daily craft makes two Primal Mooncloth.", set = "moonreg" },
    { key = "shadoweave", name = "Shadoweave Tailoring", icon = "Spell_Shadow_AntiShadow",  daily = "shadowcloth",
      perk = "10% more Masterwork crafts.", set = "felweave" },
    { key = "spellfire",  name = "Spellfire Tailoring",  icon = "Spell_Fire_FireArmor",     daily = "spellcloth",
      perk = "Your daily craft is ready 4 hours sooner.", set = "spellfire" },
  },
  blacksmithing = {
    { key = "armorsmith",  name = "Armorsmith",  icon = "INV_Chest_Plate04", daily = "enchthorium",
      perk = "10% more Masterwork crafts of armor.", set = "darkiron" },
    { key = "weaponsmith", name = "Weaponsmith", icon = "INV_Sword_25",      daily = "arcanite",
      perk = "10% more Masterwork crafts of weapons.", set = "sulfuron" },
  },
  leatherworking = {
    { key = "dragonscale", name = "Dragonscale Leatherworking", icon = "INV_Misc_MonsterScales_03", daily = "curedhide",
      perk = "Your daily craft makes two Cured Rugged Hides.", set = "blackscale" },
    { key = "tribal",      name = "Tribal Leatherworking",      icon = "INV_Misc_Pelt_Bear_03",     daily = "enchleather",
      perk = "10% more Masterwork crafts.", set = "devilsaur" },
  },
}
TCF.SPEC_BY_KEY = {}
for craft, list in pairs(TCF.SPECS) do for _, sp in ipairs(list) do sp.craft = craft; TCF.SPEC_BY_KEY[sp.key] = sp end end

-- the daily materials: name, icon, what it takes
TCF.DAILY_MATS = {
  primalmooncloth = { name = "Primal Mooncloth",       icon = "INV_Fabric_MoonRag_Primal", mats = { mooncloth = 5, runecloth = 40 } },
  shadowcloth     = { name = "Shadowcloth",            icon = "INV_Fabric_Felcloth_Ebon",  mats = { felcloth = 10, runecloth = 40 } },
  spellcloth      = { name = "Spellcloth",             icon = "INV_Fabric_Spellfire",      mats = { mageweave = 60, runecloth = 40 } },
  enchthorium     = { name = "Enchanted Thorium Bar",  icon = "INV_Ingot_Eternium",        mats = { thorium = 60, arcane = 5 } },
  arcanite        = { name = "Arcanite Bar",           icon = "INV_Misc_StoneTablet_05",   mats = { arcane = 10, thorium = 40 } },
  curedhide       = { name = "Cured Rugged Hide",      icon = "INV_Misc_LeatherScrap_02",  mats = { ruggedleather = 40, thickleather = 30 } },
  enchleather     = { name = "Enchanted Leather",      icon = "INV_Misc_LeatherScrap_04",  mats = { ruggedleather = 30, devilsaur = 5 } },
}
for key, d in pairs(TCF.DAILY_MATS) do TCF.AddMat(key, d.name, d.icon, 0, "craft") end

local function depth(self)
  local s = S(self)
  if type(s.depth) ~= "table" then s.depth = { spec = {}, rep = {}, cds = {}, orders = {}, perks = {}, rp = nil } end
  local d = s.depth
  d.spec, d.rep, d.cds, d.orders, d.perks = d.spec or {}, d.rep or {}, d.cds or {}, d.orders or {}, d.perks or {}
  -- Renown points: every Renown this cat ever had counts once (so older cats can shop right away)
  if d.rp == nil then d.rp = s.renownEver or s.renown or 0 end
  return d, s
end
TCF.DepthState = depth

function TCF:Spec(craft)
  craft = craft or craftOf(self)
  local key = depth(self).spec[craft]
  return key and TCF.SPEC_BY_KEY[key] or nil
end

-- choose (or change) a specialization: free the first time, TapCoins after that
function TCF:ChooseSpec(key)
  local sp = TCF.SPEC_BY_KEY[key]
  if not sp then return false end
  if self:ProfSkill(sp.craft) < TCF.SPEC_SKILL then return false, string.format("Specializations open at %s %d.", self:CraftName(sp.craft), TCF.SPEC_SKILL) end
  local d = depth(self)
  local cur = d.spec[sp.craft]
  if cur == key then return false end
  if cur then
    if (self.db.coins or 0) < TCF.SPEC_SWITCH_COINS then return false, string.format("Changing costs %d TapCoins.", TCF.SPEC_SWITCH_COINS) end
    self:SpendCoins(TCF.SPEC_SWITCH_COINS)
  end
  d.spec[sp.craft] = key
  self:Print(string.format("You are now a |cffffd100%s|r specialist. %s", sp.name, sp.perk), true)
  self:PlaySound("ach")
  self:MarkDirty()
  return true
end

function TCF:CraftName(craft)
  local p = TCF.PROF_BY_KEY[craft]
  return p and p.name or craft
end

-- the daily craft of the current specialization: ready in how many seconds (0 = now)
function TCF:DailyReadyIn(craft)
  craft = craft or craftOf(self)
  local sp = self:Spec(craft)
  if not sp then return nil end
  local t = depth(self).cds[sp.daily] or 0
  return max(0, t - time())
end
function TCF:DailyHours(craft)
  local sp = self:Spec(craft)
  local h = (self:RenownPerk("rested") > 0) and TCF.DAILY_HOURS_RESTED or TCF.DAILY_HOURS
  if sp and sp.key == "spellfire" then h = h - 4 end
  return h
end
-- make today's daily material
function TCF:DailyCraft(craft)
  craft = craft or craftOf(self)
  local sp = self:Spec(craft)
  if not sp then return false, "Choose a specialization first." end
  local d, s = depth(self)
  if self:DailyReadyIn(craft) > 0 then return false, "Not ready yet." end
  local dm = TCF.DAILY_MATS[sp.daily]
  for m, n in pairs(dm.mats) do
    if (s.mats[m] or 0) < n then
      local mat = TCF.MAT_BY_KEY[m]
      return false, string.format("You need %d %s.", n, mat and mat.name or m)
    end
  end
  for m, n in pairs(dm.mats) do s.mats[m] = s.mats[m] - n end
  local n = (sp.key == "mooncloth" or sp.key == "dragonscale") and 2 or 1
  s.mats[sp.daily] = (s.mats[sp.daily] or 0) + n
  d.cds[sp.daily] = time() + self:DailyHours(craft) * 3600
  self:ProfSkillUp(craft, 300)
  self:Print(string.format("You made %d %s. Next one in %d hours.", n, dm.name, self:DailyHours(craft)), true)
  self:PlaySound("buy")
  self:MarkDirty()
  return true
end

---------------------------------------------------------------- guilds and reputation
TCF.GUILDS = {
  tailoring      = { name = "The Silken Thread",       icon = "INV_Fabric_Silk_02",        master = "Grand Master Tailor" },
  blacksmithing  = { name = "Thorium Brotherhood",     icon = "INV_Hammer_20",             master = "Grand Master Blacksmith" },
  leatherworking = { name = "The Hide and Hunt Lodge", icon = "INV_Misc_Pelt_Wolf_Ruin_02", master = "Grand Master Leatherworker" },
}
TCF.GUILD_RANKS = {
  { name = "Initiate", rep = 0 }, { name = "Apprentice", rep = 300 }, { name = "Journeyman", rep = 1000 },
  { name = "Expert", rep = 3000 }, { name = "Artisan", rep = 7500 }, { name = "Master", rep = 15000 },
  { name = "Grand Master", rep = 30000 },
}
function TCF:GuildRep(craft) return depth(self).rep[craft or craftOf(self)] or 0 end
-- rank number (1-7), its name, rep into it, rep for the next one (nil at the top)
function TCF:GuildRank(craft)
  local rep = self:GuildRep(craft)
  local r = 1
  for i, e in ipairs(TCF.GUILD_RANKS) do if rep >= e.rep then r = i end end
  local nxt = TCF.GUILD_RANKS[r + 1]
  return r, TCF.GUILD_RANKS[r].name, rep, nxt and nxt.rep or nil
end
function TCF:AddGuildRep(craft, n)
  craft = craft or craftOf(self)
  local d = depth(self)
  local before = self:GuildRank(craft)
  d.rep[craft] = (d.rep[craft] or 0) + n
  local after, name = self:GuildRank(craft)
  if after > before then
    local g = TCF.GUILDS[craft]
    self:Print(string.format("%s: you are now |cffffd100%s|r.", g.name, name), true)
    self:PlaySound("ach")
    if after == #TCF.GUILD_RANKS then self:EarnTitle(g.master) end
  end
end

---------------------------------------------------------------- work orders
TCF.ORDER_SLOTS, TCF.ORDER_REFILL, TCF.ORDER_LIFE = 3, 15 * 60, 24 * 3600
local ORDER_WHO = {
  tailoring = { "a Stormwind noble", "the Dalaran Magus", "an Orgrimmar shaman", "Mistress of the Silken Thread", "a Darkmoon Faire performer" },
  blacksmithing = { "the Thorium Brotherhood quartermaster", "a Ironforge guard captain", "a Thunder Bluff brave", "the Argent Dawn armory", "an Undercity apothecary" },
  leatherworking = { "a Cenarion Circle druid", "a Ratchet bruiser", "a Timbermaw hunter", "the Lodge's master skinner", "an Everlook trader" },
}
local function income(self, f) return max(self.GatherIncome and self:GatherIncome(f) or 0, 1) end
function TCF:OrderSlots() return TCF.ORDER_SLOTS + self:RenownPerk("orders") end
-- (1.8.0) the most of one material an order asks for: three quarters of what the bag's stack holds
-- (Bag.lua), so it can always be filled; nil with the Bottomless Bag
TCF.ORDER_BAG_SHARE = 0.75
function TCF:OrderMatCap(key)
  local cap = self.MatCapFor and self:MatCapFor(key)
  if not cap or cap == math.huge then return nil end
  return max(10, floor(cap * TCF.ORDER_BAG_SHARE / 10) * 10)
end

-- a new order this cat can fill with work: materials it gathers, gear it can craft, a rare find or
-- a daily material once it has them
local function newOrder(self, craft)
  local s = S(self)
  local f = TCF.CRAFT_FAMILY[craft]
  local fam = TCF.FAMILIES[f]
  local who = ORDER_WHO[craft][random(#ORDER_WHO[craft])]
  local inc = income(self, f)
  local roll = random()
  -- gathered material: about ten minutes of the best spot this cat owns
  local best
  for i = 1, #s.ops[f] do if s.ops[f][i].n > 0 then best = i end end
  local spec = self:Spec(craft)
  if spec and roll < 0.12 then
    local dm = TCF.DAILY_MATS[spec.daily]
    return { kind = "mat", key = spec.daily, n = 1, who = who, rep = 300, gold = inc * 1800, coins = 25 }
  end
  local finds = {}
  for _, r in ipairs(TCF.RARE_FINDS[f] or {}) do if (s.mats[r.key] or 0) > 0 or (s.ws and (s.ws.found or 0) > 0) then finds[#finds + 1] = r end end
  if #finds > 0 and roll < 0.25 then
    local r = finds[random(#finds)]
    return { kind = "mat", key = r.key, n = 1, who = who, rep = 250, gold = inc * 1200, coins = 20 }
  end
  -- crafted gear this cat can make now
  local gear = {}
  for _, r in ipairs(TCF.RECIPES[craft] or {}) do
    if r.gear and not r.starter and (r.skill or 1) <= self:ProfSkill(craft) and (r.skill or 1) >= self:ProfSkill(craft) - 100 then gear[#gear + 1] = r end
  end
  if #gear > 0 and roll < 0.6 then
    local r = gear[random(#gear)]
    local n = random(1, 2)
    local worth = 0
    for m, k in pairs(r.mats) do worth = worth + k end
    return { kind = "gear", key = r.gear, n = n, who = who, rep = 60 + 40 * n, gold = inc * 300 * n, coins = random() < 0.3 and 10 or 0 }
  end
  if best then
    local op = fam.ops[best]
    local per = self:OpMatsPerCycle(f, best) * 600 / max(1, self:OpCycleTime(f, best))
    local n = max(10, floor(per / 10 + 0.5) * 10)
    local cap = self:OrderMatCap(op[2])
    if cap then n = min(n, cap) end
    return { kind = "mat", key = op[2], n = n, who = who, rep = 50 + 10 * best, gold = inc * 600, coins = 0 }
  end
  return { kind = "mat", key = fam.ops[1][2], n = 10, who = who, rep = 40, gold = 500, coins = 0 }
end

-- the orders on the board (filled up as slots free up), oldest first
function TCF:WorkOrders(craft)
  craft = craft or craftOf(self)
  local d = depth(self)
  local list = d.orders[craft]
  if type(list) ~= "table" then list = {}; d.orders[craft] = list end
  local t = time()
  for i = #list, 1, -1 do if (list[i].expires or 0) < t then table.remove(list, i) end end
  -- an order bigger than the bag can hold (made before 1.8.0): it asks for what fits, same reward
  for _, o in ipairs(list) do
    if o.kind == "mat" then
      local cap = self:OrderMatCap(o.key)
      if cap and o.n > cap then o.n = max(cap, o.got or 0) end
    end
  end
  d.orderAt = d.orderAt or {}
  local slots = self:OrderSlots()
  while #list < slots and (d.orderAt[craft] or 0) <= t do
    local o = newOrder(self, craft)
    o.expires = t + TCF.ORDER_LIFE
    o.id = (d.orderSeq or 0) + 1; d.orderSeq = o.id
    list[#list + 1] = o
    if #list < slots then d.orderAt[craft] = 0 end
  end
  return list
end
function TCF:NextOrderIn(craft)
  local d = depth(self)
  return max(0, ((d.orderAt or {})[craft or craftOf(self)] or 0) - time())
end

function TCF:OrderText(o)
  if o.kind == "gear" then
    local it = TCF.GEAR and TCF.GEAR[o.key]
    return string.format("%s wants %d %s", o.who:gsub("^%l", string.upper), o.n, it and it.name or "?")
  end
  local m = TCF.MAT_BY_KEY[o.key]
  return string.format("%s wants %d %s", o.who:gsub("^%l", string.upper), o.n, m and m.name or o.key)
end
function TCF:OrderHave(o)
  if o.kind == "gear" then return self.GearSpare and self:GearSpare(o.key) or 0 end
  return S(self).mats[o.key] or 0
end

function TCF:FillOrder(id, craft)
  craft = craft or craftOf(self)
  local list = self:WorkOrders(craft)
  for k, o in ipairs(list) do
    if o.id == id then
      -- (1.8.0) deliver what you have now; the reward comes when the whole order is in
      local got = o.got or 0
      local give = min(self:OrderHave(o), o.n - got)
      if give <= 0 then return false, "You don't have any to deliver yet." end
      if o.kind == "gear" then
        local bag = self:Bag()
        bag[o.key] = bag[o.key] - give
        if bag[o.key] <= 0 then bag[o.key] = nil end
      else
        local s = S(self)
        s.mats[o.key] = s.mats[o.key] - give
      end
      o.got = got + give
      if o.got < o.n then
        self:Print(string.format("Delivered %s. %s more to finish the order.", TCF.Commas(give), TCF.Commas(o.n - o.got)), true)
        self:PlaySound("click")
        self:MarkDirty()
        return true, "partial"
      end
      local gold = self:EarnGold(o.gold)
      if (o.coins or 0) > 0 then self:AddCoins(o.coins) end
      table.remove(list, k)
      local d = depth(self)
      d.orderAt = d.orderAt or {}
      d.orderAt[craft] = time() + TCF.ORDER_REFILL
      d.filled = (d.filled or 0) + 1
      self:Print(string.format("Order filled: %s, +%d reputation%s.", TCF.GoldStr(gold), o.rep,
        (o.coins or 0) > 0 and string.format(", %d TapCoins", o.coins) or ""), true)
      self:AddGuildRep(craft, o.rep)
      self:PlaySound("loot")
      self:MarkDirty()
      return true
    end
  end
  return false
end

---------------------------------------------------------------- Masterwork crafts
TCF.MASTERWORK_SUFFIX, TCF.MASTERWORK_CHANCE = 99, 0.05
-- the Masterwork version of a crafted gear item (made when first needed)
function TCF.MasterworkGear(baseId)
  local id = TCF.SUFFIX_ID_BASE + baseId * 100 + TCF.MASTERWORK_SUFFIX
  if TCF.GEAR[id] then return TCF.GEAR[id] end
  local b = TCF.GEAR[baseId]
  if not b then return nil end
  local parts = {}
  for k, v in (b.statStr or ""):gmatch("(%a+)=([%d%.]+)") do
    v = tonumber(v)
    if k ~= "spd" then
      if v >= 5 or v == floor(v) then v = max(v + 1, floor(v * 1.15 + 0.5)) else v = floor(v * 11.5 + 0.5) / 10 end
    end
    parts[#parts + 1] = k .. "=" .. v
  end
  TCF.AddGear(id, "Masterwork " .. b.name, b.icon, min(4, (b.q or 1) + 1), (b.ilvl or 1) + 3, b.req or 1, b.slot, b.sub,
    table.concat(parts, ","), 0, 0, 0, b.cls, b.crafted or true)
  local it = TCF.GEAR[id]
  it.base, it.suffix, it.masterwork = baseId, TCF.MASTERWORK_SUFFIX, true
  return it
end
-- the chance a gear craft comes out Masterwork (Steady Hands, specializations)
function TCF:MasterworkChance(r)
  local c = TCF.MASTERWORK_CHANCE + 0.03 * self:RenownPerk("masterwork")
  local sp = self:Spec(r.prof)
  if sp then
    local it = TCF.GEAR and TCF.GEAR[r.gear]
    local weapon = it and (it.slot == "main" or it.slot == "off" or it.slot == "ranged" or it.slot == "twohand")
    if sp.key == "shadoweave" or sp.key == "tribal" then c = c + 0.10
    elseif sp.key == "weaponsmith" and weapon then c = c + 0.10
    elseif sp.key == "armorsmith" and it and not weapon then c = c + 0.10 end
  end
  return c
end

---------------------------------------------------------------- Renown shop
TCF.RENOWN_PERKS = {
  { key = "sharptools", name = "Sharp Tools",   icon = "INV_Pick_02",            costs = { 10, 20, 40, 80 },
    text = "Clicks by hand pay 25% more gold and goods per rank." },
  { key = "keeneye",    name = "Keen Eye",      icon = "INV_Misc_Gem_06",        costs = { 15, 30, 60, 120, 240 },
    text = "Rare finds are 20% likelier per rank." },
  { key = "glints",     name = "Glint Seeker",  icon = "Spell_Holy_MagicalSentry", costs = { 10, 25, 60 },
    text = "Glints come 25% more often per rank." },
  { key = "helpers",    name = "Busy Hands",    icon = "INV_Misc_Bag_10",        costs = { 20, 40, 80, 160, 320 },
    text = "Your helpers bring 10% more goods per rank." },
  { key = "orders",     name = "Guild Ties",    icon = "INV_Scroll_03",          costs = { 30, 90 },
    text = "One more work order on the board per rank." },
  { key = "rested",     name = "Rested Hands",  icon = "Spell_Nature_Sleep",     costs = { 100 },
    text = "Your daily craft is ready every 16 hours instead of 20." },
  { key = "masterwork", name = "Steady Hands",  icon = "INV_Hammer_05",          costs = { 25, 75, 200 },
    text = "3% more Masterwork crafts per rank." },
}
TCF.RENOWN_PERK_BY_KEY = {}
for _, p in ipairs(TCF.RENOWN_PERKS) do TCF.RENOWN_PERK_BY_KEY[p.key] = p end
function TCF:RenownPerk(key)
  if not self.db then return 0 end
  return depth(self).perks[key] or 0
end
function TCF:RenownPoints() return depth(self).rp or 0 end
function TCF:BuyRenownPerk(key)
  local p = TCF.RENOWN_PERK_BY_KEY[key]
  if not p then return false end
  local d = depth(self)
  local rank = d.perks[key] or 0
  local cost = p.costs[rank + 1]
  if not cost then return false, "Already at the top rank." end
  if (d.rp or 0) < cost then return false, string.format("You need %d Renown points.", cost) end
  d.rp = d.rp - cost
  d.perks[key] = rank + 1
  self:Print(string.format("%s, rank %d: %s", p.name, rank + 1, p.text), true)
  self:PlaySound("buy")
  self:MarkDirty()
  return true
end
-- selling the business (Professions.lua TCF:PrestigeTrade) adds Renown points
function TCF:AddRenownPoints(n)
  local d = depth(self)
  d.rp = (d.rp or 0) + n
end

---------------------------------------------------------------- titles
-- earned titles are kept for the whole account (db.titles); db.titleSel is the one shown, if any
function TCF:EarnTitle(title)
  local db = self.db
  if not db or not title then return end
  db.titles = type(db.titles) == "table" and db.titles or {}
  if db.titles[title] then return end
  db.titles[title] = true
  self:Print(string.format("New title: |cffffd100%s|r. Click your cat's title in the window to show it.", title), true)
end
function TCF:EarnedTitles()
  local list = {}
  for t in pairs(type(self.db.titles) == "table" and self.db.titles or {}) do list[#list + 1] = t end
  table.sort(list)
  return list
end
-- the next title to show: the level title, then each earned title
function TCF:CycleTitle()
  local list = self:EarnedTitles()
  if #list == 0 then return false end
  local cur, idx = self.db.titleSel, 0
  for i, t in ipairs(list) do if t == cur then idx = i end end
  self.db.titleSel = list[idx + 1]   -- nil after the last one: back to the level title
  self:MarkDirty()
  return true
end
