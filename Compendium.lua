-- TapCatForever: the Compendium. Every skin, cosmetic, tap effect, effect and piece of real
-- gear in one book: what you have, what you're missing, and how to get each one.
-- TCF:HowToGet(item) gives the plain-English source lines used here and in item tooltips.
local ADDON, TCF = ...

local floor, min, max = math.floor, math.min, math.max

---------------------------------------------------------------- how to get
local function pct(c)
  local p = (c or 0) * 100
  if p >= 1 and math.abs(p - floor(p + 0.5)) < 0.05 then return string.format("%d%%", floor(p + 0.5)) end
  local s = string.format("%.2f", p):gsub("0+$", ""):gsub("%.$", "")
  return s .. "%"
end

local function commas(n) return TCF.Commas(n) end

-- boss name -> its Adventure zone (first zone that has a boss of that name)
local bossZone
local function zoneOfBoss(name)
  if not bossZone then
    bossZone = {}
    for _, t in ipairs(TCF.TIERS or {}) do
      for _, b in ipairs(t.bosses or {}) do bossZone[b[1]] = bossZone[b[1]] or t end
    end
  end
  return bossZone[name]
end

local function achFor(field, id)
  if not id then return nil end
  for _, a in ipairs(TCF.ACHIEVEMENTS) do if a[field] == id then return a end end
end

local function profName(key)
  local p = TCF.PROF_BY_KEY and TCF.PROF_BY_KEY[key]
  return p and p.name or tostring(key)
end

-- "40 Peacebloom, 10 Black Lotus" (biggest amounts first)
local function matList(mats)
  local keys = {}
  for k in pairs(mats or {}) do keys[#keys + 1] = k end
  table.sort(keys, function(a, b) if mats[a] ~= mats[b] then return mats[a] > mats[b] end return a < b end)
  local out = {}
  for _, k in ipairs(keys) do
    local m = TCF.MAT_BY_KEY and TCF.MAT_BY_KEY[k]
    out[#out + 1] = commas(mats[k]) .. " " .. (m and m.name or k)
  end
  return table.concat(out, ", ")
end

-- "Crafted with Tailoring (skill 250): 900 Runecloth, 500 Mageweave Cloth" (verb "by" for gear)
local function craftLine(prof, skill, mats, verb)
  local list = matList(mats)
  return string.format("Crafted %s %s%s%s", verb or "with", profName(prof), (skill and skill > 0) and (" (skill " .. skill .. ")") or "",
    list ~= "" and (": " .. list) or "")
end

-- "Warrior or Paladin", "Rogue, Druid, Hunter or Shaman"
local function classList(keys)
  local names = {}
  for _, k in ipairs(keys or {}) do
    local cl = TCF.CLASS_BY_KEY and TCF.CLASS_BY_KEY[k]
    names[#names + 1] = cl and cl.name or k
  end
  if #names <= 1 then return names[1] or "" end
  return table.concat(names, ", ", 1, #names - 1) .. " or " .. names[#names]
end

-- Where a main-profession craft is made: "Made in the Mining tab by Warrior or Paladin cats"
-- (names from TCF.FAMILIES; nil for the shared professions)
local function whereLine(prof)
  local fk = TCF.CRAFT_FAMILY and TCF.CRAFT_FAMILY[prof]
  local fam = fk and TCF.FAMILIES and TCF.FAMILIES[fk]
  if not fam then return nil end
  return string.format("Made in the %s tab by %s cats", fam.tab or fam.name or fk, classList(fam.classes))
end

local function recipeFor(id)
  for prof, list in pairs(TCF.RECIPES or {}) do
    for _, r in ipairs(list) do if r.item == id then return r, r.prof or prof end end
  end
end

-- gear id -> its recipe (TCF.RECIPES gear rows, built once)
local gearRecipes
local function gearRecipeFor(id)
  if not gearRecipes then
    gearRecipes = {}
    for prof, list in pairs(TCF.RECIPES or {}) do
      for _, r in ipairs(list) do if r.gear then gearRecipes[r.gear] = gearRecipes[r.gear] or { r, r.prof or prof } end end
    end
  end
  local e = gearRecipes[id]
  if e then return e[1], e[2] end
end

-- Adventure boss drops for a skin: { { boss, chance }, ... }
local function skinDrops(it)
  local out, seen = {}, {}
  if it.drop and it.drop[1] then out[1] = { it.drop[1], it.drop[2] }; seen[it.drop[1]] = true end
  for boss, d in pairs(TCF.SKIN_DROPS or {}) do
    for _, e in ipairs(d.id and { d } or d) do
      if e.id == it.id and not seen[boss] then seen[boss] = true; out[#out + 1] = { boss, e.chance } end
    end
  end
  table.sort(out, function(a, b) return a[1] < b[1] end)
  return out
end

-- a skin's extra sources (Data.lua SKINS "get"): one table, or a list of them
local function getsOf(it)
  local g = it.get
  if not g then return {} end
  if g.kind then return { g } end
  return g
end

-- How a crafted thing is made: prof (crafting key), skill, mats, isGear. nil if it isn't crafted.
-- Works for real gear (it.crafted), crafted cosmetics (source "craft") and craft skins.
function TCF.CraftSourceOf(it)
  if not it then return nil end
  if it.q and not it.rarity then
    if not it.crafted then return nil end
    local r, prof = gearRecipeFor(it.id)
    return it.crafted or prof, it.craftSkill or (r and r.skill), it.craftMats or (r and r.mats), true
  end
  if it.source == "craft" or it.craftSet then   -- (1.7.0) a crafted set's piece (ProfSets.lua)
    local r, prof = recipeFor(it.id)
    if r then return prof, r.skill, r.mats, false end
    return "?", nil, nil, false
  end
  if it.slot == "skin" then
    for _, g in ipairs(getsOf(it)) do
      if g.kind == "craft" then return g.prof, g.skill, g.mats, false end
    end
  end
end

-- "Crafted with Leatherworking (skill 250)" (short, no materials)
function TCF.CraftShortLine(it)
  local prof, skill, _, isGear = TCF.CraftSourceOf(it)
  if not prof or prof == "?" then return prof and "Crafted with a profession" or nil end
  return string.format("Crafted %s %s%s", isGear and "by" or "with", profName(prof),
    (skill and skill > 0) and (" (skill " .. skill .. ")") or "")
end

local function getLine(g)
  local k = g.kind
  if k == "chest" then
    local ch = TCF.CHEST_BY_KEY[g.chest]
    local line = string.format("%s: %s chance each time you open one", ch and ch.name or "Chest", pct(g.chance))
    if g.chest == "heroic" then
      -- (Dungeons.lua rolls the Heroic Cache's skins after some real dungeon runs)
      local lo, hi = TCF.DUNGEON_HEROIC_SKIN_LOW or 0.10, TCF.DUNGEON_HEROIC_SKIN_HIGH or 0.25
      return line, string.format("In WoW: or after a real dungeon from level 20: %s of runs get this same chance (%s from level 50)",
        pct(lo), pct(hi))
    end
    return line
  elseif k == "quest" then
    local weekly = g.quest == "weekly"
    return string.format("%s quest reward: %s chance each time you finish a %s quest", weekly and "Weekly" or "Daily",
      pct(g.chance), weekly and "weekly" or "daily")
  elseif k == "expedition" then
    local ex = g.expedition and g.expedition ~= "any" and TCF.EXPEDITION_BY_KEY and TCF.EXPEDITION_BY_KEY[g.expedition]
    return string.format("Expedition reward: %s chance each time %s comes back successful", pct(g.chance),
      ex and ("\"" .. ex.name .. "\"") or "any expedition")
  elseif k == "realdungeon" then
    local what = g.run == "raid" and "raid" or g.run == "any" and "dungeon or raid" or "dungeon"
    return string.format("In WoW: finish a real %s with TapCatForever on, %s chance each time", what, pct(g.chance))
  elseif k == "craft" then
    return craftLine(g.prof, g.skill, g.mats), whereLine(g.prof)
  end
end

local STARTER
local function isStarter(id)
  if not STARTER then
    STARTER = {}
    for _, s in ipairs(TCF.STARTER or {}) do STARTER[s] = true end
  end
  return STARTER[id]
end

local RACE_NAMES = {
  race_human = "Human", race_dwarf = "Dwarf", race_nightelf = "Night Elf", race_gnome = "Gnome", race_orc = "Orc",
  race_undead = "Undead", race_tauren = "Tauren", race_troll = "Troll", race_skyborne = "Skyborne",
}

-- the chests whose rolls can give a cosmetic of this rarity
local function chestsFor(rarity)
  local names = {}
  for _, ch in ipairs(TCF.CHESTS) do
    -- a gear-only chest (the Raider's Hoard) never gives a cosmetic
    if not ch.gearOnly and (ch.weights[rarity] or 0) > 0 then names[#names + 1] = ch.name end
  end
  return table.concat(names, ", ")
end

local function gearLines(it, add)
  if it.crafted then
    local prof, skill, mats = TCF.CraftSourceOf(it)
    add(craftLine(prof, skill, mats, "by"))
    add(whereLine(prof))
    add("Crafted gear is never found as loot. It sells for Trade Gold, not TapCoins")
    return
  end
  if it.retired then
    local kinds = {}
    for k, name in ipairs(TCF.GEAR_SUFFIXES or {}) do
      if TCF.GEAR[(TCF.SUFFIX_ID_BASE or 0) + it.id * 100 + k] then kinds[#kinds + 1] = name end
    end
    if #kinds == 0 then
      if it.placeholder then
        -- a leftover test item (Gear.lua TCF:RemovePlaceholderGear takes it off the cats)
        add("Removed: a leftover test item with no stats")
        add("Cats that had it were paid its sell value")
        return
      end
      -- a later-expansion item, or one with no stats: known, but never loot
      add("This item never drops")
      add("Players who have it keep it")
      return
    end
    add("No longer drops on its own: it is found with a random bonus now (" .. table.concat(kinds, ", ") .. ")")
    add("Players who have this plain one keep it")
    return
  end
  if it.q == 1 then
    add(string.format("Adventure: plain (white) gear that regular enemies drop now and then, around level %d", max(1, it.req or 1)))
    add("Mostly found early on, and mostly for slots your cat has empty. Chests never hold white gear")
    return
  end
  if it.q == 5 then
    local real = false
    for _, l in ipairs(TCF.Legendaries and TCF:Legendaries() or {}) do if l == it then real = true; break end end
    if not real then add("This item never drops"); return end
    local parts = {}
    for _, ch in ipairs(TCF.CHESTS) do
      if (ch.legendary or 0) > 0 then
        parts[#parts + 1] = string.format("about 1 in %d %s", floor(1 / ch.legendary + 0.5), ch.plural or (ch.name .. "s"))
      end
    end
    add("A real Legendary, never a world drop. Only " .. (#parts > 0 and table.concat(parts, " and ") or "special chests") .. " hold one")
    add("The chest picks a Legendary your cat's class can use, preferring one made for that class")
    add("Raider's Hoards come from raids: raid bosses and first clears in Adventure, real raids and raid expeditions")
    return
  end
  if it.suffix and TCF.GEAR_SUFFIXES then
    add(string.format("One of the random bonuses %s can come with (%s)", (it.base and TCF.GEAR[it.base] or it).name, TCF.GEAR_SUFFIXES[it.suffix] or "?"))
  end
  local t = it.tier and it.tier > 0 and TCF.TIERS and TCF.TIERS[it.tier]
  local b = t and it.boss and it.boss > 0 and t.bosses[it.boss]
  if b then
    add(string.format("Adventure: dropped by %s in %s", b[1], t.name))
    add("Each Adventure boss always drops a piece of its own loot the first time you beat it")
    add("After that, chests can hold loot from bosses your cat has already beaten")
    if TCF.IsDungeonTier and TCF.IsDungeonTier(t) and it.q >= 2 and it.q <= 4 then
      local req = max(1, it.req or 1)
      -- (a Dungeon Chest picks gear from 10 levels below to 3 above the cat's level, up to 60)
      local lv = req + 10 >= 60 and string.format("from about level %d", max(1, req - 3))
        or string.format("about level %d to %d", max(1, req - 3), req + 10)
      add(string.format("Dungeon Chests can hold it once your cat has reached %s, when the chest is %s", t.name, lv))
    end
  elseif t then
    -- A first kill only falls back to zone loot when that boss has no loot list of its own.
    local fallback = false
    local bl = TCF.BOSS_LOOT[it.tier] or {}
    for i = 1, #(t.bosses or {}) do
      if not bl[i] or #bl[i] == 0 then fallback = true; break end
    end
    if fallback then
      add(string.format("Adventure: zone loot from %s, a possible first-kill reward from bosses there that have no loot of their own", t.name))
    end
    local lv = t.min == t.max and tostring(t.min) or (t.min .. "-" .. t.max)
    add(string.format("Adventure: zone loot from %s, rarely found in chests of level %s", t.name, lv))
  else
    add(string.format("Adventure and chests: world drop around level %d", max(1, it.req or 1)))
    add("A chest holds gear for the level of the cat that earned it (the Treasure Bag shows each chest's level)")
    if it.q == 2 then add("Enemies in Adventure sometimes drop it too, mostly for slots your cat has empty") end
  end
end

-- Plain-English lines saying how to get an item (cosmetic, skin, tap effect, effect or real gear).
function TCF:HowToGet(it)
  local out = {}
  if not it then return out end
  local function add(s) if s then out[#out + 1] = s end end

  if it.q and not it.rarity then  -- real gear (TCF.GEAR)
    gearLines(it, add)
    return out
  end

  if it.slot == "skin" then
    if it.skinPrice then add("Buy in the Shop (Cat Skins) for " .. commas(it.skinPrice) .. " TapCoins") end
    for _, d in ipairs(skinDrops(it)) do
      local t = zoneOfBoss(d[1])
      add(string.format("Adventure: dropped by %s%s, %s chance", d[1], t and (" in " .. t.name) or "", pct(d[2])))
    end
    for _, g in ipairs(getsOf(it)) do
      local a, b = getLine(g)
      add(a); add(b)
    end
    local a = achFor("id", it.skinAch) or achFor("skin", it.id)
    if a then add("Achievement reward: " .. a.name .. " (" .. (a.desc:gsub("%.$", "")) .. ")") end
    if it.skinPrice then add("Or find it in a Heroic Cache (3% chance of a shop skin you don't have yet)") end
    if #out == 0 then
      add(it.id == "skin_orange" and "Every cat starts as an Orange Tabby" or "Not available right now")
    end
    return out
  end

  if isStarter(it.id) then
    local scl = it.class and TCF.CLASS_BY_KEY[it.class]
    add(scl and ("Every " .. scl.name .. " cat starts with this") or "Every cat starts with this")
  end
  local src = it.source
  if src == "loot" then
    add("Found in chests, as a lucky find while tapping, and in the Shop's Daily Wares")
    local chests = chestsFor(it.rarity)
    if chests ~= "" then
      add(string.format("Chests that can hold %s cosmetics: %s", TCF.RARITY[it.rarity].name, chests))
    end
    local cl = it.class and TCF.CLASS_BY_KEY[it.class]
    if cl then add(string.format("%s only: it drops only while your cat is a %s, and it turns up only in that class's Daily Wares", cl.name, cl.name)) end
  elseif src == "achievement" then
    local a = achFor("item", it.id)
    add(a and ("Achievement reward: " .. a.name .. " (" .. (a.desc:gsub("%.$", "")) .. ")") or "Achievement reward")
  elseif src == "craft" then
    local r, prof = recipeFor(it.id)
    add(r and craftLine(prof, r.skill, r.mats) or "Crafted with a profession")
    if r then add(whereLine(prof)) end
  elseif src == "race" then
    local race = RACE_NAMES[it.id] or "matching"
    add(string.format("Racial heritage: buy it in the Shop for %s TapCoins while playing %s %s character",
      commas(TCF.RACE_PRICE or 600), race:match("^[AEIOU]") and "an" or "a", race))
  elseif src == "set" and self.CosmeticSetLines then
    for _, line in ipairs(self:CosmeticSetLines(it)) do add(line) end
  elseif src == "purr" and self.PurrUnlockLine then
    add(self:PurrUnlockLine(it))
  elseif src == "retired" then
    add("No longer available. Players who have it keep it.")
  end
  if #out == 0 then add("Not available right now") end
  return out
end

-- A short word for where a skin comes from (shown on grid cells): chest, quest, craft...
local TAG = { chest = "chest", quest = "quest", expedition = "exped.", craft = "craft" }
function TCF.SkinSourceTag(it)
  -- an Adventure boss drop comes first (the Emberheart Cat is also a rarer expedition find)
  if #skinDrops(it) > 0 then return "drop" end
  local g = getsOf(it)[1]
  if g then
    if g.kind == "realdungeon" then return g.run == "raid" and "raid" or "dungeon" end
    return TAG[g.kind] or "?"
  end
  if it.skinAch or achFor("skin", it.id) then return "ach." end
  return ""
end

---------------------------------------------------------------- the window
local W, H = 800, 600
local CATS = {
  { key = "skin", name = "Skins" }, { key = "cos", name = "Cosmetics" }, { key = "tap", name = "Tap Effects" },
  { key = "effect", name = "Effects" }, { key = "gear", name = "Gear" }, { key = "sets", name = "Item Sets" },
  { key = "mats", name = "Materials" },   -- (1.7.3) MatLibrary.lua: every material and where it comes from
}
local COS_SLOTS = { "head", "shoulder", "chest", "back", "main", "off", "acc", "race", "pattern", "pet" }   -- (1.7.4) furs are skins
local FILTERS = { { "all", "All" }, { "owned", "Owned" }, { "missing", "Missing" } }
-- item grid: 12 x 7 cells of 58 (+5 gap) = 751 x 436; gear grid: 9 x 10 of 40 (+4) = 392 x 436
local COLS, ROWS, CELL, GAP = 12, 7, 58, 5
local GCOLS, GROWS, GCELL, GGAP = 9, 10, 40, 4
-- zone list: 28 Adventure zones, World drops, Crafted (30 rows of 14.5 = 435, the grid's height)
local LIST_ROWS, LIST_H, LIST_W = 30, 14.5, 176
local CRAFTED = -1  -- gearZone index of the "Crafted" row (0 is World drops)
local TOP = -108  -- where the grids and lists start

-- class filter choices for cosmetics and effects
local CLASS_CHOICES = { { nil, "All classes" }, { "ANY", "No class needed" } }
for _, cl in ipairs(TCF.CLASSES) do CLASS_CHOICES[#CLASS_CHOICES + 1] = { cl.key, cl.name .. " only" } end

local function itemOrder(cat)
  local SKIN_GROUP = { shop = 1, chest = 2, quest = 3, expedition = 4, realdungeon = 5, craft = 6, drop = 7, ach = 8 }
  local function group(it)
    if it.id == "skin_orange" then return 0 end
    if it.skinPrice then return 1 end
    if #skinDrops(it) > 0 then return 7 end
    local g = getsOf(it)[1]
    if g then return SKIN_GROUP[g.kind] or 9 end
    return 8
  end
  if cat == "skin" then
    local cache = {}
    return function(a, b)
      cache[a] = cache[a] or group(a); cache[b] = cache[b] or group(b)
      if cache[a] ~= cache[b] then return cache[a] < cache[b] end
      if (a.skinPrice or 0) ~= (b.skinPrice or 0) then return (a.skinPrice or 0) < (b.skinPrice or 0) end
      if a.rarity ~= b.rarity then return a.rarity < b.rarity end
      return a.name < b.name
    end
  end
  return function(a, b)
    local ca = a.class and TCF.CLASS_BY_KEY[a.class].index or 0
    local cb = b.class and TCF.CLASS_BY_KEY[b.class].index or 0
    if ca ~= cb then return ca < cb end
    if a.art ~= b.art then return a.art < b.art end
    if a.rarity ~= b.rarity then return a.rarity < b.rarity end
    return a.name < b.name
  end
end

-- every piece of gear your cats have (any class's bag or worn)
local function ownedGear()
  local set = {}
  for _, cd in pairs(TCF.db.classData or {}) do
    for id, n in pairs(cd.bag or {}) do if n and n > 0 then set[id] = true end end
    for _, id in pairs(cd.gear or {}) do set[id] = true end
  end
  return set
end

local sortedCache = setmetatable({}, { __mode = "k" })
local function sortedGear(list)
  local s = sortedCache[list]
  if s then return s end
  s = {}
  for i, it in ipairs(list) do s[i] = it end
  table.sort(s, function(a, b)
    if a.q ~= b.q then return a.q > b.q end
    if a.req ~= b.req then return a.req < b.req end
    return a.name < b.name
  end)
  sortedCache[list] = s
  return s
end

-- crafted gear, one list per crafting skill (family order), easiest recipe first
local craftedCache
local function craftedSections()
  if craftedCache then return craftedCache end
  local byCraft = {}
  for _, it in ipairs(TCF.GEAR_LIST or {}) do
    if it.crafted then
      byCraft[it.crafted] = byCraft[it.crafted] or {}
      table.insert(byCraft[it.crafted], it)
    end
  end
  local out = {}
  for _, fk in ipairs(TCF.FAMILY_KEYS or {}) do
    local fam = TCF.FAMILIES[fk]
    local list = fam and byCraft[fam.craft]
    if list and #list > 0 then
      table.sort(list, function(a, b)
        local sa, sb = a.craftSkill or 0, b.craftSkill or 0
        if sa ~= sb then return sa < sb end
        if a.req ~= b.req then return a.req < b.req end
        return a.name < b.name
      end)
      out[#out + 1] = { label = fam.craftName or profName(fam.craft), list = list, ordered = true, craft = fam.craft }
    end
  end
  craftedCache = out
  return out
end

-- world drops by level band: Uncommon and better first, then that band's plain (white) gear
-- in its own list, so the many whites don't bury the greens and blues
local worldCache
local function worldSections()
  if worldCache then return worldCache end
  local bands = {}
  for b in pairs(TCF.WORLD_POOL or {}) do bands[#bands + 1] = b end
  table.sort(bands)
  local out = {}
  for _, b in ipairs(bands) do
    local lo, hi = max(1, b * 5), b * 5 + 4
    local label = (lo >= 60 and "Level 60") or string.format("Levels %d-%d", lo, min(60, hi))
    local good, plain = {}, {}
    for _, it in ipairs(TCF.WORLD_POOL[b]) do
      if it.q <= 1 then plain[#plain + 1] = it else good[#good + 1] = it end
    end
    if #good > 0 then out[#out + 1] = { label = label, list = good } end
    if #plain > 0 then out[#out + 1] = { label = "|cffccccccPlain gear, " .. label:lower() .. "|r", list = plain } end
  end
  worldCache = out
  return out
end

-- the lists of gear for one Adventure zone (bosses with loot, then other zone loot),
-- for world drops (index 0): level bands, or for crafted gear (CRAFTED): one list per craft
local function gearSections(zone)
  local out = {}
  if zone == CRAFTED then return craftedSections() end
  if zone == 0 then return worldSections() end
  local t = TCF.TIERS[zone]
  local loot = TCF.BOSS_LOOT[zone] or {}
  for bi, b in ipairs(t.bosses or {}) do
    if loot[bi] and #loot[bi] > 0 then out[#out + 1] = { label = b[1], list = loot[bi] } end
  end
  if TCF.TIER_POOL[zone] and #TCF.TIER_POOL[zone] > 0 then
    out[#out + 1] = { label = "Other loot in this zone", list = TCF.TIER_POOL[zone] }
  end
  return out
end

local function addHowSection(tt, it)
  tt:AddLine(" ")
  tt:AddLine("How to get", 1, 0.82, 0)
  for _, line in ipairs(TCF:HowToGet(it)) do tt:AddLine("- " .. line, 1, 1, 1, true) end
end

function TCF:CreateCompendium()
  local UI = TCF.UI
  local Text, Button, Tip = UI.Text, UI.Button, UI.Tip
  local f = CreateFrame("Frame", "TapCatForeverCompendium", UIParent, UI.BT)
  f:SetSize(W, H); f:SetPoint("CENTER", 0, 20)
  f:SetFrameStrata("DIALOG"); f:SetToplevel(true)
  f:SetMovable(true); f:EnableMouse(true); f:SetClampedToScreen(true)
  f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving); f:SetScript("OnDragStop", f.StopMovingOrSizing)
  if f.SetBackdrop then f:SetBackdrop(UI.BACKDROP_DIALOG) end
  f:Hide()
  tinsert(UISpecialFrames, "TapCatForeverCompendium")
  self.compendium = f
  f.cat, f.slot, f.filter, f.classIdx, f.page = "skin", "head", "all", 1, 1
  f.gearZone, f.gearSub = 1, 1

  local title = Text(f, "GameFontNormalLarge", "Compendium"); title:SetPoint("TOPLEFT", 22, -18)
  local overall = Text(f, "GameFontDisableSmall", nil, "LEFT"); overall:SetPoint("LEFT", title, "RIGHT", 12, -1)
  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton"); close:SetPoint("TOPRIGHT", -6, -6)
  local count = Text(f, "GameFontHighlight", nil, "RIGHT"); count:SetPoint("TOPRIGHT", -42, -21)

  -- categories
  local catBtns = {}
  for i, c in ipairs(CATS) do
    local b = Button(f, c.name, 104, 24, function()
      f.cat = c.key; f.page = 1; f:Refresh(); TCF:PlaySound("click")
    end)
    b:SetPoint("TOPLEFT", 18 + (i - 1) * 108, -44)
    b.key = c.key
    catBtns[i] = b
  end

  -- All / Owned / Missing (right side of the filter row: x 552-782)
  local filterBtns = {}
  for i, fl in ipairs(FILTERS) do
    local b = Button(f, fl[2], 74, 22, function() f.filter = fl[1]; f.page = 1; f:Refresh(); TCF:PlaySound("click") end)
    b:SetPoint("TOPRIGHT", -(18 + (#FILTERS - i) * 78), -76)
    b.key = fl[1]
    filterBtns[i] = b
  end

  -- cosmetic slot icons (x 20-256) and the slot's name
  local slotBtns = {}
  for i, key in ipairs(COS_SLOTS) do
    local s = TCF.SLOT_BY_KEY[key]
    local b = CreateFrame("Button", nil, f)
    b:SetSize(22, 22); b:SetPoint("TOPLEFT", 20 + (i - 1) * 24, -76)  -- 10 slots fit in x 20-256
    local t = b:CreateTexture(nil, "ARTWORK"); t:SetAllPoints(); t:SetTexture(TCF.Icon(s.icon)); t:SetTexCoord(0.07, 0.93, 0.07, 0.93)
    b.sel = b:CreateTexture(nil, "OVERLAY"); b.sel:SetPoint("TOPLEFT", -3, 3); b.sel:SetPoint("BOTTOMRIGHT", 3, -3)
    b.sel:SetTexture("Interface\\Buttons\\CheckButtonHilight"); b.sel:SetBlendMode("ADD")
    b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    b:SetScript("OnClick", function() f.slot = key; f.page = 1; f:Refresh(); TCF:PlaySound("click") end)
    Tip(b, function(tt) tt:AddLine(s.name, 1, 0.82, 0) end)
    b.key = key
    slotBtns[i] = b
  end
  local slotName = Text(f, "GameFontNormal", nil, "LEFT"); slotName:SetPoint("TOPLEFT", 264, -80); slotName:SetWidth(84)
  if slotName.SetWordWrap then slotName:SetWordWrap(false) end

  -- class filter (cosmetics and effects): click for the next choice, right-click for the previous
  local classBtn = Button(f, "", 150, 22, nil)
  classBtn:SetPoint("TOPLEFT", 352, -76)
  classBtn:RegisterForClicks("LeftButtonUp", "RightButtonUp")
  classBtn:SetScript("OnClick", function(_, button)
    local n = #CLASS_CHOICES
    f.classIdx = (f.classIdx - 1 + (button == "RightButton" and n - 1 or 1)) % n + 1
    f.page = 1; f:Refresh(); TCF:PlaySound("click")
  end)
  Tip(classBtn, function(tt)
    tt:AddLine("Class filter", 1, 0.82, 0)
    tt:AddLine("Click for the next class, right-click for the previous one.", 1, 1, 1, true)
  end)

  -- a line of help where the slot icons would be (skins, tap effects, gear)
  local hint = Text(f, "GameFontHighlightSmall", nil, "LEFT"); hint:SetPoint("TOPLEFT", 22, -82)

  -- item grid, built once
  local grid = CreateFrame("Frame", nil, f)
  grid:SetSize(COLS * (CELL + GAP) - GAP, ROWS * (CELL + GAP) - GAP); grid:SetPoint("TOPLEFT", 18, TOP)
  local cells = {}
  for i = 1, COLS * ROWS do
    local c = UI.ItemCell(grid, CELL)
    c:SetPoint("TOPLEFT", ((i - 1) % COLS) * (CELL + GAP), -floor((i - 1) / COLS) * (CELL + GAP))
    c:SetScript("OnClick", function(s)
      local it = s.item
      -- (1.7.4) test mode: ctrl-click gives it to you
      if it and IsControlKeyDown and IsControlKeyDown() and TCF.TestGive and TCF:TestGive(it) then f:Refresh(); return end
      -- (1.6.3) shift-click: try it on the cat in the main window (opened if it isn't)
      if it and IsShiftKeyDown and IsShiftKeyDown() then
        TCF:CompendiumPreview(it)
        if s:IsMouseOver() and s:GetScript("OnEnter") then s:GetScript("OnEnter")(s) end
        return
      end
      -- wear something you own (if your cat's class can); anything else does nothing
      if it and TCF.db.owned[it.id] and TCF:CanEquip(it) and not TCF:IsEquipped(it) then
        TCF:Equip(it)
        TCF:PlaySound("click")
        f:Refresh()
        if s:IsMouseOver() and s:GetScript("OnEnter") then s:GetScript("OnEnter")(s) end
      end
    end)
    c:SetScript("OnEnter", function(s)
      local it = s.item
      if not it then return end
      GameTooltip:SetOwner(s, "ANCHOR_RIGHT")
      TCF:ItemTooltip(GameTooltip, it, true)
      addHowSection(GameTooltip, it)
      if TCF.db.owned[it.id] then
        GameTooltip:AddLine(" ")
        if TCF:IsEquipped(it) then GameTooltip:AddLine("Your cat is wearing this.", 0.3, 1, 0.3)
        elseif TCF:CanEquip(it) then GameTooltip:AddLine("Click to wear it.", 0, 1, 0)
        else
          local cl = TCF.CLASS_BY_KEY[it.class]
          GameTooltip:AddLine("Switch your cat to " .. (cl and cl.name or "its class") .. " to wear it.", 1, 0.6, 0.2, true)
        end
      end
      if TCF.UI.PreviewHint then TCF.UI.PreviewHint(GameTooltip, TCF.window, it) end
      GameTooltip:Show()
    end)
    c:SetScript("OnLeave", function() GameTooltip:Hide() end)
    c:Hide()
    cells[i] = c
  end

  -- gear view: zone list, section list (bosses or level bands), gear grid
  local gearView = CreateFrame("Frame", nil, f)
  gearView:SetPoint("TOPLEFT", 18, TOP); gearView:SetSize(W - 36, GROWS * (GCELL + GGAP))
  local function ListRow(parent, x, i, onClick)
    local r = CreateFrame("Button", nil, parent)
    r:SetSize(LIST_W, LIST_H); r:SetPoint("TOPLEFT", x, -(i - 1) * LIST_H)
    r.bg = r:CreateTexture(nil, "BACKGROUND"); r.bg:SetAllPoints(); r.bg:SetColorTexture(1, 0.82, 0.2, 0.22)
    r:SetHighlightTexture("Interface\\QuestFrame\\UI-QuestTitleHighlight", "ADD")
    r.name = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.name:SetPoint("LEFT", 4, 0); r.name:SetWidth(LIST_W - 52)
    r.num = Text(r, "GameFontDisableSmall", nil, "RIGHT"); r.num:SetPoint("RIGHT", -4, 0); r.num:SetWidth(46)
    if r.name.SetWordWrap then r.name:SetWordWrap(false); r.num:SetWordWrap(false) end
    r:SetScript("OnClick", function(s) onClick(s.index); TCF:PlaySound("click") end)
    r:Hide()
    return r
  end
  local zoneRows, subRows = {}, {}
  for i = 1, LIST_ROWS do
    zoneRows[i] = ListRow(gearView, 0, i, function(idx)
      f.gearZone = idx; f.gearSub = 1; f.page = 1
      -- Crafted opens on the current class's own craft
      if idx == CRAFTED and TCF.CraftProf then
        local mine = TCF:CraftProf()
        for si, sec in ipairs(craftedSections()) do if sec.craft == mine then f.gearSub = si end end
      end
      f:Refresh()
    end)
    subRows[i] = ListRow(gearView, LIST_W + 6, i, function(idx) f.gearSub = idx; f.page = 1; f:Refresh() end)
  end
  local gearGrid = CreateFrame("Frame", nil, gearView)
  gearGrid:SetSize(GCOLS * (GCELL + GGAP) - GGAP, GROWS * (GCELL + GGAP) - GGAP)
  gearGrid:SetPoint("TOPRIGHT", 0, 0)  -- x 384-776 of the window
  local gcells = {}
  for i = 1, GCOLS * GROWS do
    local b = UI.GearButton(gearGrid, GCELL)
    b:SetPoint("TOPLEFT", ((i - 1) % GCOLS) * (GCELL + GGAP), -floor((i - 1) / GCOLS) * (GCELL + GGAP))
    b.check = b:CreateTexture(nil, "OVERLAY"); b.check:SetSize(16, 16); b.check:SetPoint("TOPRIGHT", 2, 2)
    b.check:SetTexture("Interface\\Buttons\\UI-CheckBox-Check")
    b:SetScript("OnEnter", function(s)
      if not s.item then return end
      GameTooltip:SetOwner(s, "ANCHOR_RIGHT")
      TCF:GearTooltip(GameTooltip, s.item)
      addHowSection(GameTooltip, s.item)
      if TCF.UI.PreviewHint then TCF.UI.PreviewHint(GameTooltip, TCF.window, s.item) end
      GameTooltip:Show()
    end)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    b:SetScript("OnClick", function(s)
      if s.item and IsControlKeyDown and IsControlKeyDown() and TCF.TestGive and TCF:TestGive(s.item) then f:Refresh(); return end
      if s.item and IsShiftKeyDown and IsShiftKeyDown() then
        TCF:CompendiumPreview(s.item)
        s:GetScript("OnEnter")(s)
      end
    end)
    b:Hide()
    gcells[i] = b
  end
  gearView:Hide()

  -- empty-view note and paging
  local empty = Text(f, "GameFontHighlight", nil); empty:SetWidth(420)
  local pageText = Text(f, "GameFontHighlightSmall"); pageText:SetPoint("BOTTOM", 0, 20); pageText:SetWidth(110)
  local prev = Button(f, "<", 28, 22, function() f.page = max(1, f.page - 1); f:Refresh() end)
  prev:SetPoint("RIGHT", pageText, "LEFT", -6, 0)
  local nextB = Button(f, ">", 28, 22, function() f.page = f.page + 1; f:Refresh() end)
  nextB:SetPoint("LEFT", pageText, "RIGHT", 6, 0)
  f:EnableMouseWheel(true)
  f:SetScript("OnMouseWheel", function(_, d) f.page = max(1, f.page - d); f:Refresh() end)

  local function setPages(n, per)
    local pages = max(1, math.ceil(n / per))
    f.page = min(max(1, f.page), pages)
    pageText:SetText(string.format("Page %d / %d", f.page, pages))
    prev:SetEnabled(f.page > 1); nextB:SetEnabled(f.page < pages)
    pageText:SetShown(pages > 1); prev:SetShown(pages > 1); nextB:SetShown(pages > 1)
    return (f.page - 1) * per
  end

  local function passes(owned)
    return f.filter == "all" or (f.filter == "owned") == (owned and true or false)
  end

  local function collectedText(have, total)
    count:SetText(string.format("Collected |cffffffff%s / %s|r", commas(have), commas(total)))
  end

  ---------------------------------------------------------------- items
  function f:RefreshItems()
    local cat = self.cat
    local owned = TCF.db.owned
    local classKey = CLASS_CHOICES[self.classIdx][1]
    local useClass = cat == "cos" or cat == "effect"
    local all, list, have = 0, {}, 0
    -- like TCF:CountOwned: other races' heritage pieces count only if owned
    local myRace = TCF:RaceItemForPlayer()
    for _, it in ipairs(TCF.ITEM_LIST) do
      local slotOk
      if cat == "cos" then slotOk = it.slot == self.slot else slotOk = it.slot == cat end
      if slotOk and (it.source ~= "retired" or owned[it.id])
        and (it.source ~= "race" or owned[it.id] or (myRace and myRace.id == it.id))
        and (not useClass or not classKey or (classKey == "ANY" and not it.class) or it.class == classKey) then
        all = all + 1
        if owned[it.id] then have = have + 1 end
        if passes(owned[it.id]) then list[#list + 1] = it end
      end
    end
    table.sort(list, itemOrder(cat))
    collectedText(have, all)
    local first = setPages(#list, COLS * ROWS)
    for i, c in ipairs(cells) do
      local it = list[first + i]
      if it then
        local got = owned[it.id] and true or false
        c:SetItem(it, got, got)
        -- the check: green = collected, gold = your cat is wearing it
        if TCF:IsEquipped(it) then c.check:SetVertexColor(1, 1, 1) else c.check:SetVertexColor(0.35, 1, 0.35) end
        if not got and it.slot == "skin" then
          c.count:SetText(it.skinPrice and ("|cffffd100" .. commas(it.skinPrice) .. "|r") or ("|cffff8000" .. TCF.SkinSourceTag(it) .. "|r"))
        end
      else
        c:Hide()
      end
    end
    local noun = cat == "skin" and "skins" or cat == "tap" and "tap effects" or cat == "effect" and "effects" or "items"
    empty:SetText(f.filter == "owned" and ("|cff888888No " .. noun .. " collected here yet.|r")
      or f.filter == "missing" and ("|cff20ff20You have every one of these " .. noun .. ".|r") or "|cff888888Nothing here.|r")
    empty:ClearAllPoints(); empty:SetPoint("CENTER", grid, "CENTER")
    empty:SetShown(#list == 0)
  end

  ---------------------------------------------------------------- gear
  function f:RefreshGear()
    local got = ownedGear()
    local function countList(l)
      local n = 0
      for _, it in ipairs(l) do if got[it.id] then n = n + 1 end end
      return n
    end
    local tiers = TCF.TIERS or {}
    -- zone rows: every Adventure zone, then world drops (index 0), then crafted gear
    local zones = {}
    for ti in ipairs(tiers) do zones[#zones + 1] = ti end
    zones[#zones + 1] = 0
    local hasCrafted = #craftedSections() > 0
    if hasCrafted then zones[#zones + 1] = CRAFTED end
    if self.gearZone ~= 0 and not (self.gearZone == CRAFTED and hasCrafted) and not tiers[self.gearZone] then
      self.gearZone = tiers[1] and 1 or 0
    end
    for i, r in ipairs(zoneRows) do
      local z = zones[i]
      if z then
        local secs = gearSections(z)
        local n, tot = 0, 0
        for _, s in ipairs(secs) do n = n + countList(s.list); tot = tot + #s.list end
        r.index = z
        r.name:SetText(z == 0 and "|cffccccccWorld drops|r" or z == CRAFTED and "|cff9fd8ffCrafted|r"
          or (tiers[z].raid and ("|cffffb060" .. tiers[z].name .. "|r") or tiers[z].name))
        r.num:SetText(n .. "/" .. tot)
        r.bg:SetShown(z == self.gearZone)
        r:Show()
      else
        r:Hide()
      end
    end
    local secs = gearSections(self.gearZone)
    self.gearSub = min(max(1, self.gearSub), max(1, #secs))
    for i, r in ipairs(subRows) do
      local s = secs[i]
      if s then
        r.index = i
        r.name:SetText(s.label)
        r.num:SetText(countList(s.list) .. "/" .. #s.list)
        r.bg:SetShown(i == self.gearSub)
        r:Show()
      else
        r:Hide()
      end
    end
    local sec = secs[self.gearSub]
    local src = sec and (sec.ordered and sec.list or sortedGear(sec.list)) or {}
    local list = {}
    for _, it in ipairs(src) do if passes(got[it.id]) then list[#list + 1] = it end end
    collectedText(countList(src), #src)
    local first = setPages(#list, GCOLS * GROWS)
    for i, b in ipairs(gcells) do
      local it = list[first + i]
      if it then
        b:SetGear(it)
        local have = got[it.id]
        b.icon:SetDesaturated(not have); b.icon:SetAlpha(have and 1 or 0.4)
        b.check:SetShown(have and true or false)
        b:Show()
      else
        b:Hide()
      end
    end
    empty:SetText(#src == 0 and (self.gearZone == CRAFTED and "|cff888888Nothing to craft here.|r" or "|cff888888No loot here.|r") or f.filter == "owned" and "|cff888888None of this gear collected yet.|r"
      or "|cff20ff20You have every piece here.|r")
    empty:ClearAllPoints(); empty:SetPoint("CENTER", gearGrid, "CENTER")
    empty:SetShown(#list == 0)
  end

  ---------------------------------------------------------------- refresh
  function f:Refresh()
    self.dirty = nil
    local cat = self.cat
    for _, b in ipairs(catBtns) do if b.key == cat then b:LockHighlight() else b:UnlockHighlight() end end
    for _, b in ipairs(filterBtns) do if b.key == self.filter then b:LockHighlight() else b:UnlockHighlight() end end
    local isCos, isGear, isSets, isMats = cat == "cos", cat == "gear", cat == "sets", cat == "mats"
    for _, b in ipairs(slotBtns) do b:SetShown(isCos); b.sel:SetShown(b.key == self.slot) end
    slotName:SetShown(isCos); slotName:SetText(TCF.SLOT_BY_KEY[self.slot].name)
    local useClass = isCos or cat == "effect" or isSets
    classBtn:SetShown(useClass); classBtn:SetText(CLASS_CHOICES[self.classIdx][2])
    hint:SetShown(not isCos)
    hint:SetWidth(useClass and 320 or 520)
    hint:SetText(cat == "skin" and "Click a skin you own to wear it. Hover any skin to see how to get it."
      or cat == "tap" and "Click a tap effect you own to use it."
      or cat == "effect" and "Click an effect you own to wear it."
      or isSets and "Cosmetic sets first, then real gear sets. Hover for where to get one, click for its pieces."
      or isMats and "Every material and where it comes from. Hover for what it's used in."
      or "Pick a zone, then a boss. World drops are listed by level, crafted gear by profession.")
    -- overall progress on cosmetics and skins
    local n, total = TCF:CountOwned()  -- the same numbers as the main window
    overall:SetText(string.format("All cosmetics and skins: %s / %s", commas(n), commas(total)))
    grid:SetShown(not isGear and not isSets and not isMats); gearView:SetShown(isGear)
    if self.setsView then self.setsView:SetShown(isSets) end
    if self.matsView then self.matsView:SetShown(isMats) end
    if isMats and TCF.RefreshCompendiumMats then
      local n = TCF:RefreshCompendiumMats(self, { top = TOP, width = W - 36, passes = passes, collected = collectedText, setPages = setPages })
      empty:SetText("|cff888888No material matches.|r")
      empty:ClearAllPoints(); empty:SetPoint("CENTER", self.matsView, "CENTER")
      empty:SetShown(n == 0)
    elseif isSets and TCF.RefreshCompendiumSets then
      -- (ItemSets.lua draws the list; Owned = complete sets, Missing = sets still to finish)
      local n = TCF:RefreshCompendiumSets(self, { top = TOP, width = W - 36, classKey = CLASS_CHOICES[self.classIdx][1],
        passes = passes, collected = collectedText, setPages = setPages })
      empty:SetText(f.filter == "owned" and "|cff888888No complete sets yet.|r" or "|cff888888Nothing here.|r")
      empty:ClearAllPoints(); empty:SetPoint("CENTER", self.setsView, "CENTER")
      empty:SetShown(n == 0)
    elseif isGear then self:RefreshGear() else self:RefreshItems() end
  end

  -- something changed while the book is open: redraw at most a few times a second
  local wait = 0
  f:SetScript("OnUpdate", function(s, e)
    wait = wait - e
    if s.dirty and wait <= 0 then wait = 0.3; s:Refresh() end
  end)
  f:SetScript("OnShow", function(s) s:Refresh() end)
  f:SetScript("OnHide", function() GameTooltip:Hide() end)
  return f
end

function TCF:ToggleCompendium()
  local f = self.compendium or self:CreateCompendium()
  if f:IsShown() then f:Hide() else f:Show() end
end

-- keep an open Compendium up to date when items are gained or worn
do
  local refreshAll = TCF.RefreshAll
  if refreshAll then
    TCF.RefreshAll = function(self, ...)
      refreshAll(self, ...)
      if self.compendium and self.compendium:IsShown() then self.compendium.dirty = true end
    end
  end
end

-- /tcf compendium (Core.lua owns the other commands)
do
  local slash = SlashCmdList and SlashCmdList.TAPCATFOREVER
  if slash then
    local WORDS = { compendium = true, comp = true, book = true, collection = true }
    -- commands Core.lua handles; anything else (help, typos) gets the usage line with compendium in it
    local KNOWN = { [""] = true, open = true, config = true, show = true, hide = true, toggle = true, lock = true,
      unlock = true, reset = true, scale = true, bag = true, welcome = true, testmode = true, stats = true,
      companions = true, companion = true, pets = true, tools = true }
    SlashCmdList.TAPCATFOREVER = function(msg, ...)
      local cmd, arg = (msg or ""):lower():match("^(%S*)%s*(.-)$")
      if WORDS[cmd] then TCF:ToggleCompendium() return end
      if not KNOWN[cmd] or (cmd == "scale" and not tonumber(arg)) then
        TCF:Print("/tapcat - open window | bag | companions | compendium | news | top | feedback | welcome | show | hide | toggle | lock | unlock | reset | scale <0.3-3> | stats", true)
        return
      end
      return slash(msg, ...)
    end
  end
end

-- (1.6.3) shift-click in the Compendium: the item goes on the cat in the main window (opened if it
-- isn't, with the Appearance or Gear page behind it), or comes off again
function TCF:CompendiumPreview(it)
  if not it or not TCF.UI.TogglePreview then return end
  if not self.window or not self.window:IsShown() then self:ToggleWindow() end
  local win = self.window
  if not win then return end
  TCF.UI.TogglePreview(win, it)
end
