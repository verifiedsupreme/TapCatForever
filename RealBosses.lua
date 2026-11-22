-- TapCatForever: rewards for killing specific bosses in real World of Warcraft.
--
-- How a kill is seen (12.x safe: the combat log is restricted, so it isn't used):
--  * dungeon and raid bosses: ENCOUNTER_END with success (Dungeons.lua passes it on). Matched,
--    in this order, by the encounter's ID (a boss's encounterIds, when known), by the NPC IDs of
--    the boss units seen during that encounter (ENCOUNTER_START and boss frames: works in every
--    language), and last by the encounter's English name.
--  * open-world bosses (Hogger): the boss is watched through the units the game lets addons
--    read (target, focus, mouseover, boss frames, and nameplates already known to be the boss).
--    Matched by the NPC ID in its GUID, or its English name. It counts as your kill when you
--    were fighting it (it was alive, not tapped by someone else, and you or it were in combat)
--    and you then see it dead within 2 minutes.
--    Secret values (names, GUIDs, flags) are never compared: such a unit is skipped.
-- Each kill is counted per character (shown in the Compendium). Rewards are cosmetics (Cosmetic
-- only) and boss effects (BossEffects.lua), each guaranteed on a kill or with a chance per kill.
-- WoW: Forever has no raids yet, so nothing here needs a raid.
-- /run TapCatForever:RealBossDebug() lists this session's kills and unmatched encounters (with IDs).
local ADDON, TCF = ...

local random = math.random

local function isSecret(v) return TCF.IsSecret and TCF.IsSecret(v) end

---------------------------------------------------------------- new cosmetics
-- Adds an item after Data.lua built the item table (same fields as Data.lua's add()).
function TCF.AddExtraItem(it)
  if TCF.ITEMS[it.id] then return TCF.ITEMS[it.id] end
  it.price = TCF.RARITY[it.rarity].price
  if it.slot == "effect" then
    local fx = TCF.FX[it.art]
    it.fxLayer = it.fxLayer or (fx and fx.layer)
    it.fxAnim = it.fxAnim or (fx and fx.anim)
  end
  TCF.ITEMS[it.id] = it
  TCF.ITEM_LIST[#TCF.ITEM_LIST + 1] = it
  return it
end

local function c(r, g, b) return { r, g, b } end
for _, u in ipairs({
  { "rb_hogger_bandana", "acc",  "acc_scarf", "Hogger's Chewed Bandana", 2, c(0.78, 0.42, 0.20), c(0.35, 0.24, 0.14), "INV_Misc_Bandana_01" },
  { "rb_arugal_hood",    "head", "head_hood", "Arugal's Worgen Cowl",    3, c(0.34, 0.24, 0.46), c(0.78, 0.78, 0.88), "INV_Helmet_29" },
  { "rb_drakkisath_crown", "head", "head_crown", "Drakkisath's Ember Crown", 4, c(0.95, 0.40, 0.15), c(1.00, 0.82, 0.30), "INV_Crown_01" },
}) do
  TCF.AddExtraItem({ id = u[1], slot = u[2], art = u[3], name = u[4], rarity = u[5], c1 = u[6], c2 = u[7], icon = u[8], source = "realboss" })
end

---------------------------------------------------------------- the bosses
-- name: the boss's English name; place: where it is; world: an open-world boss; npc: its NPC ID
-- (the number in its GUID, the same in every language); encounterIds (optional): its dungeon
-- encounter IDs, when known (RealBossDebug prints the ID of every encounter it can't match).
-- rewards: { id = TCF.ITEMS key, chance = per kill (1 = the first kill always gives it) }.
-- Three skins that used to drop from these bosses in Adventure now only come from the real
-- bosses (Adventure keeps its other boss skins). The Diamond Cat drops from General Drakkisath
-- and from Nefarian in Adventure (Data.lua).
TCF.REAL_BOSSES = {
  { key = "hogger",      name = "Hogger",                   place = "Elwynn Forest", npc = 448, world = true,
    rewards = { { id = "rb_hogger_bandana", chance = 1 } } },
  { key = "taragaman",   name = "Taragaman the Hungerer",   place = "Ragefire Chasm", npc = 11520,
    rewards = { { id = "skin_ragefire", chance = 0.15 } } },
  { key = "vancleef",    name = "Edwin VanCleef",           place = "The Deadmines", npc = 639,
    rewards = { { id = "skin_defias", chance = 0.15 } } },
  { key = "arugal",      name = "Archmage Arugal",          place = "Shadowfang Keep", npc = 4275, aliases = { "Arugal" },
    rewards = { { id = "rb_arugal_hood", chance = 0.2 } } },
  { key = "thermaplugg", name = "Mekgineer Thermaplugg",    place = "Gnomeregan", npc = 7800,
    rewards = { { id = "fx_boss_storm", chance = 1 } } },
  { key = "whitemane",   name = "High Inquisitor Whitemane", place = "Scarlet Monastery", npc = 3977,
    rewards = { { id = "fx_boss_holy", chance = 1 } } },
  { key = "archaedas",   name = "Archaedas",                place = "Uldaman", npc = 2748,
    rewards = { { id = "skin_stonewatcher", chance = 0.1 } } },
  { key = "theradras",   name = "Princess Theradras",       place = "Maraudon", npc = 12201,
    rewards = { { id = "fx_boss_nature", chance = 1 } } },
  { key = "thaurissan",  name = "Emperor Dagran Thaurissan", place = "Blackrock Depths", npc = 9019,
    rewards = { { id = "fx_boss_fire", chance = 1 } } },
  { key = "drakkisath",  name = "General Drakkisath",       place = "Blackrock Spire", npc = 10363,
    rewards = { { id = "rb_drakkisath_crown", chance = 0.2 }, { id = "skin_diamond", chance = 0.05 } } },
  { key = "frostwhisper", name = "Ras Frostwhisper",        place = "Scholomance", npc = 10508,
    rewards = { { id = "fx_boss_frost", chance = 1 } } },
  { key = "rivendare",   name = "Baron Rivendare",          place = "Stratholme", npc = 10440,
    rewards = { { id = "fx_boss_shadow", chance = 1 } } },
}

local function norm(s) return (tostring(s):lower():gsub("[^%w]", "")) end
TCF.REAL_BOSS_BY_KEY, TCF.REAL_BOSS_BY_NAME, TCF.REAL_BOSS_BY_NPC, TCF.REAL_BOSS_BY_ENCOUNTER = {}, {}, {}, {}
for _, b in ipairs(TCF.REAL_BOSSES) do
  TCF.REAL_BOSS_BY_KEY[b.key] = b
  TCF.REAL_BOSS_BY_NAME[norm(b.name)] = b
  for _, a in ipairs(b.aliases or {}) do TCF.REAL_BOSS_BY_NAME[norm(a)] = b end
  if b.npc then TCF.REAL_BOSS_BY_NPC[b.npc] = b end
  for _, id in ipairs(b.encounterIds or {}) do TCF.REAL_BOSS_BY_ENCOUNTER[id] = b end
end

-- the NPC ID in a creature GUID ("Creature-0-1-2-3-448-0001" -> 448); nil for secret or other GUIDs
function TCF.NpcIdFromGUID(guid)
  if type(guid) ~= "string" or isSecret(guid) then return nil end
  local kind, id = guid:match("^(%a+)%-[^-]*%-[^-]*%-[^-]*%-[^-]*%-(%d+)")
  if kind == "Creature" or kind == "Vehicle" then return tonumber(id) end
end

-- the skins that moved from Adventure drops to the real bosses
for _, boss in ipairs({ "Edwin VanCleef", "Taragaman the Hungerer", "Archaedas" }) do
  local d = TCF.SKIN_DROPS and TCF.SKIN_DROPS[boss]
  local moved = { skin_defias = true, skin_ragefire = true, skin_stonewatcher = true }
  if d and d.id and moved[d.id] then TCF.SKIN_DROPS[boss] = nil end
end

-- Those skins are still rare skins that can't be bought: count them for "dropSkins" (the Tiger
-- King achievement) as they counted when they were Adventure drops. Core.lua counts only
-- TCF.SKIN_DROPS and skins with a "get" source, so only the others are added here.
do
  local getStat = TCF.GetStat
  function TCF:GetStat(stat, ...)
    local n = getStat(self, stat, ...)
    if stat ~= "dropSkins" or type(n) ~= "number" or not self.db then return n end
    local drops = {}
    for _, d in pairs(TCF.SKIN_DROPS or {}) do
      if d.id then drops[d.id] = true else for _, e in ipairs(d) do drops[e.id] = true end end
    end
    local seen = {}
    for _, b in ipairs(TCF.REAL_BOSSES) do
      for _, r in ipairs(b.rewards) do
        local it = TCF.ITEMS[r.id]
        if it and it.slot == "skin" and not seen[r.id] and self.db.owned[r.id] and not drops[r.id] and it.get == nil then
          seen[r.id] = true
          n = n + 1
        end
      end
    end
    return n
  end
end

-- the real-boss rewards of one item: { { boss, reward }, ... }
function TCF:RealBossRewardsFor(id)
  local out = {}
  for _, b in ipairs(TCF.REAL_BOSSES) do
    for _, r in ipairs(b.rewards) do if r.id == id then out[#out + 1] = { b, r } end end
  end
  return out
end

-- real bosses in one place (dungeon name): for the in-dungeon banner
function TCF:RealBossesIn(place)
  local out = {}
  if not place or isSecret(place) then return out end
  for _, b in ipairs(TCF.REAL_BOSSES) do if b.place == place then out[#out + 1] = b end end
  return out
end

---------------------------------------------------------------- kills and rewards
local function killLog()
  local holder = TCF.charData or TCF.db
  holder.realBosses = holder.realBosses or {}
  return holder.realBosses
end
function TCF:RealBossKills(key) return killLog()[key] or 0 end

TCF.realBossLog = {}   -- this session's matched kills and unmatched encounters (for /run TapCatForever:RealBossDebug())

-- A real boss died to you. Counts the kill and rolls its rewards. how: "encounter" / "world".
function TCF:RealBossKilled(b, how)
  if not b or not self.db then return end
  local log = killLog()
  log[b.key] = (log[b.key] or 0) + 1
  table.insert(self.realBossLog, 1, string.format("%s (%s)", b.name, how or "?"))
  if #self.realBossLog > 20 then table.remove(self.realBossLog) end
  local reason = "In WoW: " .. b.name .. " in " .. b.place
  for _, r in ipairs(b.rewards) do
    local it = TCF.ITEMS[r.id]
    if it and not self.db.owned[r.id] and ((r.chance or 0) >= 1 or random() < (r.chance or 0)) then
      if it.slot == "effect" and self.UnlockBossEffect then self:UnlockBossEffect(r.id, reason)
      elseif it.slot == "skin" then self:GrantSkin(r.id, reason)
      else self:GrantItem(it, reason) end
    end
  end
  self:MarkDirty()
  if self.RefreshDungeonBanner then self:RefreshDungeonBanner() end
end

local function logLine(self, line)
  table.insert(self.realBossLog, 1, line)
  if #self.realBossLog > 20 then table.remove(self.realBossLog) end
end

-- the real boss behind each encounter ID, from the NPC IDs of its boss units (ENCOUNTER_START,
-- INSTANCE_ENCOUNTER_ENGAGE_UNIT): works whatever language the client uses
local encounterBoss, currentEncounter = {}, nil
TCF.realBossEncounterNpcs = encounterBoss
local function plainNumber(v)
  if v == nil or isSecret(v) or type(v) ~= "number" then return nil end
  return v
end
function TCF:RealBossScanBossUnits(encounterID)
  local id = plainNumber(encounterID) or currentEncounter
  if not id then return end
  for i = 1, 5 do
    local ok, guid = pcall(UnitGUID, "boss" .. i)
    local b = ok and TCF.REAL_BOSS_BY_NPC[TCF.NpcIdFromGUID(guid) or 0]
    if b then encounterBoss[id] = b end
  end
end

-- ENCOUNTER_START: encounterID (the boss units are read now and when they change)
function TCF:RealBossEncounterStart(id)
  currentEncounter = plainNumber(id)
  self:RealBossScanBossUnits(currentEncounter)
end

-- ENCOUNTER_END (from Dungeons.lua): encounterID, encounterName, success
function TCF:RealBossEncounter(id, name, success)
  if isSecret(success) then return end
  local ok, won = pcall(function() return success == 1 end)
  if not ok or not won then return end
  id = plainNumber(id)
  if id == currentEncounter then currentEncounter = nil end
  local b = id and (TCF.REAL_BOSS_BY_ENCOUNTER[id] or encounterBoss[id])
  if not b and type(name) == "string" and not isSecret(name) then b = TCF.REAL_BOSS_BY_NAME[norm(name)] end
  if b then self:RealBossKilled(b, "encounter " .. tostring(id or "?"))
  else
    local shown = (type(name) == "string" and not isSecret(name)) and name or "(hidden name)"
    logLine(self, string.format("unmatched encounter: %s (ID %s)", shown, tostring(id or "?")))
  end
end

function TCF:RealBossDebug()
  print("TapCat real boss kills this session (newest first):")
  for _, l in ipairs(self.realBossLog) do print("  " .. l) end
end

---------------------------------------------------------------- open-world bosses
local WORLD, WORLD_NPC = {}, {}
for _, b in ipairs(TCF.REAL_BOSSES) do
  if b.world then
    WORLD[norm(b.name)] = b
    if b.npc then WORLD_NPC[b.npc] = b end
  end
end

local function call(fn, ...)
  if type(fn) ~= "function" then return nil end
  local ok, v = pcall(fn, ...)
  if not ok or isSecret(v) then return nil end
  return v
end

local engaged, credited = {}, {}
local ENGAGE_SECONDS, CREDIT_GAP = 120, 300
TCF.realBossEngaged = engaged

local function inInstance()
  local v = call(IsInInstance)
  return v == true
end

-- names already looked at (raw name -> boss or false), so a busy target costs one table lookup
local nameCache, nameCacheN = {}, 0
local function worldBossByName(name)
  local b = nameCache[name]
  if b == nil then
    b = WORLD[norm(name)] or false
    if nameCacheN > 300 then nameCache, nameCacheN = {}, 0 end
    nameCache[name] = b; nameCacheN = nameCacheN + 1
  end
  return b or nil
end

-- looks at one unit; returns true when it was a watched boss
function TCF:RealBossScanUnit(unit)
  if not self.db or inInstance() then return end
  if not call(UnitExists, unit) then return end
  local guid = call(UnitGUID, unit)
  if type(guid) ~= "string" then guid = nil end
  local b = WORLD_NPC[TCF.NpcIdFromGUID(guid) or 0]
  if not b then
    local name = call(UnitName, unit)
    if type(name) ~= "string" then return end
    b = worldBossByName(name)
  end
  if not b then return end
  local now = GetTime()
  local dead = call(UnitIsDead, unit)
  local denied = call(UnitIsTapDenied, unit)
  if dead == false then
    local fighting = call(UnitAffectingCombat, "player") or call(UnitAffectingCombat, unit)
    if denied ~= true and fighting then engaged[b.key] = { t = now, guid = guid } end
  elseif dead == true then
    local e = engaged[b.key]
    if e and now - e.t <= ENGAGE_SECONDS and denied ~= true and (not e.guid or not guid or e.guid == guid) then
      local ck = guid or b.key
      if not credited[ck] or now - credited[ck] > CREDIT_GAP then
        credited[ck] = now
        engaged[b.key] = nil
        self:RealBossKilled(b, "world")
      end
    end
  end
  return true
end

-- The units looked at: target, focus, mouseover, soft target and boss frames on their health
-- and flag events; a nameplate only once it is known to show a watched boss (checked when it
-- appears). Nothing is looked at inside instances (cached on zone changes).
local WATCHED = { target = true, focus = true, mouseover = true, softenemy = true }
for i = 1, 5 do WATCHED["boss" .. i] = true end
local plates = {}
local inside = false
TCF.realBossPlates = plates
local ev = CreateFrame("Frame")
TCF.realBossEvents = ev
for _, e in ipairs({ "PLAYER_TARGET_CHANGED", "UPDATE_MOUSEOVER_UNIT", "NAME_PLATE_UNIT_ADDED", "NAME_PLATE_UNIT_REMOVED",
  "UNIT_HEALTH", "UNIT_FLAGS", "PLAYER_REGEN_ENABLED", "PLAYER_REGEN_DISABLED", "PLAYER_ENTERING_WORLD", "ZONE_CHANGED_NEW_AREA",
  "ENCOUNTER_START", "INSTANCE_ENCOUNTER_ENGAGE_UNIT" }) do
  pcall(ev.RegisterEvent, ev, e)
end
ev:SetScript("OnEvent", function(_, event, a)
  if not TCF.db then return end
  if event == "PLAYER_ENTERING_WORLD" or event == "ZONE_CHANGED_NEW_AREA" then
    inside = inInstance()
    for k in pairs(plates) do plates[k] = nil end
    if not inside then currentEncounter = nil end
    return
  elseif event == "ENCOUNTER_START" then TCF:RealBossEncounterStart(a); return
  elseif event == "INSTANCE_ENCOUNTER_ENGAGE_UNIT" then TCF:RealBossScanBossUnits(); return
  end
  if inside then return end
  if event == "PLAYER_TARGET_CHANGED" or event == "PLAYER_REGEN_ENABLED" or event == "PLAYER_REGEN_DISABLED" then
    TCF:RealBossScanUnit("target")
  elseif event == "UPDATE_MOUSEOVER_UNIT" then TCF:RealBossScanUnit("mouseover")
  elseif type(a) ~= "string" or isSecret(a) then return
  elseif event == "NAME_PLATE_UNIT_ADDED" then plates[a] = TCF:RealBossScanUnit(a) or nil
  elseif event == "NAME_PLATE_UNIT_REMOVED" then plates[a] = nil
  elseif WATCHED[a] or plates[a] then TCF:RealBossScanUnit(a)
  end
end)
-- while a watched boss was being fought, look at the target, focus and its nameplates every half
-- second (a dead boss sends no more health events)
local acc = 0
ev:SetScript("OnUpdate", function(_, e)
  acc = acc + e
  if acc < 0.5 then return end
  acc = 0
  if not next(engaged) then return end
  local now = GetTime()
  for k, x in pairs(engaged) do if now - x.t > ENGAGE_SECONDS then engaged[k] = nil end end
  TCF:RealBossScanUnit("target"); TCF:RealBossScanUnit("focus")
  for u in pairs(plates) do TCF:RealBossScanUnit(u) end
end)

---------------------------------------------------------------- "how to get it" lines
-- whole percents without a decimal ("5%"), others with one ("2.5%")
local function pct(p)
  local v = p * 100
  if math.abs(v - math.floor(v + 0.5)) < 0.05 then return string.format("%d%%", math.floor(v + 0.5)) end
  return string.format("%.1f%%", v)
end

function TCF:RealBossSourceLines(it)
  local out = {}
  for _, e in ipairs(self:RealBossRewardsFor(it.id)) do
    local b, r = e[1], e[2]
    local odds = (r.chance or 0) >= 1 and "the first kill always gives it" or (pct(r.chance) .. " chance each kill")
    out[#out + 1] = string.format("In WoW: kill %s in %s with TapCatForever on, %s", b.name, b.place, odds)
    if self.db then
      local n = self:RealBossKills(b.key)
      out[#out + 1] = string.format("You have killed %s %s on this character", b.name, n == 1 and "once" or (n .. " times"))
    end
  end
  return out
end
