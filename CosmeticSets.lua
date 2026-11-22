-- TapCatForever: cosmetic slots added in 1.6 (shoulders, racial accessory) and the registry for
-- themed cosmetic sets. Each set is one generated file, Sets/<Name>.lua (tools/sets/<set>.py, see
-- tools/sets/README.md), that calls TCF.AddCosmeticSet with its drawings, items and animations.
-- Set pieces are cosmetic only: each is guaranteed from one Adventure boss until you own it
-- (TCF.BOSS_COSMETICS, read by Adventure.lua).
local ADDON, TCF = ...

---------------------------------------------------------------- slots
local function addSlot(def, after)
  if TCF.SLOT_BY_KEY[def.key] then return end
  local pos = #TCF.SLOTS + 1
  for i, s in ipairs(TCF.SLOTS) do if s.key == after then pos = i + 1 end end
  table.insert(TCF.SLOTS, pos, def)
  TCF.SLOT_BY_KEY[def.key] = def
end
-- shoulders: pauldrons drawn on both shoulders (real shoulder gear shows there too)
addSlot({ key = "shoulder", name = "Shoulders", icon = "INV_Shoulder_02" }, "back")
-- the racial heritage accessory has its own slot, so it can be worn together with an accessory
addSlot({ key = "race", name = "Racial", icon = "Achievement_Character_Orc_Male",
  desc = "Your race's accessory (tusks, horns, ears...). Worn together with an accessory. Hide it with \"Show racial accessory\" in Settings." }, "acc")
for _, it in ipairs(TCF.ITEM_LIST) do
  if it.source == "race" then it.slot = "race" end
end

-- saves from before 1.6 wore the racial piece in the accessory slot: move it to its own slot
function TCF:MigrateRaceSlot(db)
  for _, lo in pairs(db.loadouts or {}) do
    local it = lo.acc and TCF.ITEMS[lo.acc]
    if it and it.slot == "race" then
      lo.race = lo.race or lo.acc
      lo.acc = nil
    end
  end
end

---------------------------------------------------------------- cosmetic sets
TCF.COSMETIC_SETS = TCF.COSMETIC_SETS or {}
TCF.COSMETIC_SET_BY_KEY = TCF.COSMETIC_SET_BY_KEY or {}
TCF.BOSS_COSMETICS = TCF.BOSS_COSMETICS or {}   -- Adventure boss name -> { item id, ... }
TCF.VEC_ANIM = TCF.VEC_ANIM or {}

-- what the Compendium calls each slot in a set line
local PIECE_WORD = { head = "helm", shoulder = "shoulders", chest = "chest", back = "cape", main = "weapon", off = "off hand", effect = "aura" }

-- def = { key, name, zone (Adventure tier key), vec = { [VEC key] = entry }, pieces = {
--   { id, slot, art, name, rarity, icon, boss, word, anim = { layers }, fx = { layer, anim } } } }
function TCF.AddCosmeticSet(def)
  -- loading a set again (a preview of a new build) replaces it
  local old = TCF.COSMETIC_SET_BY_KEY[def.key]
  if old then
    for _, it in ipairs(old.items) do
      TCF.ITEMS[it.id] = nil
      for i = #TCF.ITEM_LIST, 1, -1 do if TCF.ITEM_LIST[i] == it then table.remove(TCF.ITEM_LIST, i) end end
      for _, list in pairs(TCF.BOSS_COSMETICS) do
        for i = #list, 1, -1 do if list[i] == it.id then table.remove(list, i) end end
      end
    end
    for i = #TCF.COSMETIC_SETS, 1, -1 do if TCF.COSMETIC_SETS[i] == old then table.remove(TCF.COSMETIC_SETS, i) end end
  end
  for k, e in pairs(def.vec or {}) do TCF.VEC[k] = e end
  def.items = {}
  for _, p in ipairs(def.pieces) do
    assert(not TCF.ITEMS[p.id], "duplicate item " .. p.id)
    local it = { id = p.id, slot = p.slot, art = p.art, name = p.name, rarity = p.rarity, c1 = { 1, 1, 1 }, c2 = { 1, 1, 1 },
      icon = p.icon, source = "set", set = def.key, bossName = p.boss, word = p.word or PIECE_WORD[p.slot] }
    -- bossName, not boss: gear items use it.boss as a number (an index into a tier's bosses)
    it.price = TCF.RARITY[it.rarity].price
    if p.slot == "effect" then
      TCF.FX[p.art] = TCF.FX[p.art] or p.fx or { layer = "back", anim = "pulse" }
      it.fxLayer, it.fxAnim = TCF.FX[p.art].layer, TCF.FX[p.art].anim
    end
    TCF.ITEMS[it.id] = it
    TCF.ITEM_LIST[#TCF.ITEM_LIST + 1] = it
    if p.anim then TCF.VEC_ANIM[p.art] = p.anim end
    if p.boss then
      local list = TCF.BOSS_COSMETICS[p.boss] or {}
      TCF.BOSS_COSMETICS[p.boss] = list
      list[#list + 1] = it.id
    end
    def.items[#def.items + 1] = it
  end
  TCF.COSMETIC_SETS[#TCF.COSMETIC_SETS + 1] = def
  TCF.COSMETIC_SET_BY_KEY[def.key] = def
  return def
end

-- owned pieces and the size of a set
function TCF:CosmeticSetProgress(key)
  local def = TCF.COSMETIC_SET_BY_KEY[key]
  if not def then return 0, 0 end
  local n = 0
  for _, it in ipairs(def.items) do if self.db and self.db.owned[it.id] then n = n + 1 end end
  return n, #def.items
end

-- how-to-get lines for a set piece (Compendium and tooltips):
--   Adventure: Ragnaros in Molten Core always drops it until you own it
--   Molten Core set (2/6), cosmetic only: helm from Ragnaros, shoulders from Golemagg the Incinerator, ...
-- The first line only when Adventure.lua does not give its own line for TCF.BOSS_COSMETICS
-- (TCF:BossCosmeticSources), so a piece never lists its boss twice.
function TCF:CosmeticSetLines(it)
  local def = it and TCF.COSMETIC_SET_BY_KEY[it.set]
  if not def then return {} end
  local zone
  for _, t in ipairs(TCF.TIERS or {}) do if t.key == def.zone then zone = t.name end end
  local out = {}
  if it.bossName and not self.BossCosmeticSources then
    out[1] = string.format("Adventure: %s%s always drops it until you own it", it.bossName, zone and (" in " .. zone) or "")
  end
  local have, total = self:CosmeticSetProgress(def.key)
  local parts = {}
  for _, p in ipairs(def.items) do
    parts[#parts + 1] = (self.db and self.db.owned[p.id] and "|cff40ff40" or "") .. p.word .. " from " .. (p.bossName or "?")
      .. (self.db and self.db.owned[p.id] and "|r" or "")
  end
  out[#out + 1] = string.format("%s set (%d/%d), cosmetic only: %s", def.name, have, total, table.concat(parts, ", "))
  return out
end
