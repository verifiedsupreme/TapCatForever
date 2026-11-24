-- TapCatForever: the long-chase profession sets (1.7.0). Each crafted cosmetic set (Sets/*.lua with a
-- prof, made by tools/sets/<set>.py) gets one recipe per piece in its profession's Crafting list. They
-- take months on purpose:
--   * the three crafting skills: skill 300, the set's specialization, a guild rank (Expert to Grand
--     Master), many of the specialization's daily material, rare finds from clicking by hand, and a
--     lot of the best gathered materials
--   * Herbalism, Fishing, Cooking and First Aid: skill 300 and a lot of that profession's rarest things
-- Owning every piece of a set gives its title (TCF:EarnTitle, ProfDepth.lua).
-- A set whose drawings aren't in the addon yet has no recipes (only sets that loaded count).
local ADDON, TCF = ...

-- per piece of a crafting set: guild rank, daily materials, rare finds (low, mid, top), gathered
-- materials (as a share of the family's base amounts)
local CRAFT_PARTS = {
  shoulders = { rank = 4, daily = 5,  rare = { 8, 0, 0 },  share = 0.6 },
  cape      = { rank = 4, daily = 5,  rare = { 6, 2, 0 },  share = 0.6 },
  chest     = { rank = 5, daily = 8,  rare = { 0, 6, 0 },  share = 1.0 },
  weapon    = { rank = 5, daily = 8,  rare = { 0, 4, 2 },  share = 1.0 },
  head      = { rank = 6, daily = 10, rare = { 0, 6, 4 },  share = 1.2 },
  aura      = { rank = 7, daily = 12, rare = { 10, 8, 6 }, share = 1.5 },
}
-- the family's base amounts for one piece
local BASE_MATS = {
  tailoring      = { runecloth = 2000, felcloth = 500, mooncloth = 200 },
  blacksmithing  = { thorium = 2000, darkiron = 500, elementium = 150 },
  leatherworking = { ruggedleather = 2000, devilsaur = 500, coreleather = 150 },
}
local FAMILY_OF = { tailoring = "cloth", blacksmithing = "mining", leatherworking = "skinning" }

-- the other professions' sets: materials per piece
local OTHER = {
  herbalism = {
    head = { lotus = 10, dreamfoil = 400, icecap = 200 },
    cape = { wildvine = 12, silversage = 300, plaguebloom = 200 },
    weapon = { lotus = 6, gromsblood = 300, p_power = 5 },
    aura = { lotus = 20, swiftthistle = 30, wildvine = 20, p_gnature = 8 },
  },
  fishing = {
    head = { pinchy = 3, whitescale = 300, eel = 200 },
    cape = { nightfin = 400, sunscale = 300, boot = 50 },
    weapon = { pinchy = 2, eel = 400, rockscale = 300 },
    aura = { pinchy = 5, whitescale = 500, eel = 500 },
  },
  cooking = {
    head = { d_feast = 5, d_soup = 60 },
    chest = { d_omelet = 80, d_salmon = 60 },
    weapon = { d_mightfish = 60, d_chili = 80 },
    aura = { d_feast = 10, d_mightfish = 40, d_salmon = 40 },
  },
  firstaid = {
    head = { b_heavyrunecloth = 300, b_runecloth = 300 },
    shoulders = { b_heavymageweave = 400, b_heavysilk = 400 },
    cape = { b_heavyrunecloth = 400, runecloth = 1500 },
    aura = { b_heavyrunecloth = 800, b_heavymageweave = 600, runecloth = 2500 },
  },
}

-- the part of an item id: set_<key>_<part>
local function partOf(def, it) return it.id:sub(#("set_" .. def.key .. "_") + 1) end

local function addRecipes()
  for _, def in ipairs(TCF.COSMETIC_SETS or {}) do
    local prof = def.prof
    if prof and TCF.RECIPES[prof] then
      local list = TCF.RECIPES[prof]
      local have = {}
      for _, r in ipairs(list) do if r.item then have[r.item] = true end end
      for _, it in ipairs(def.items) do
       if not have[it.id] then
        local part = partOf(def, it)
        local r = { item = it.id, prof = prof, skill = 300, cosmetic = true, longChase = true, set = def.key }
        local cp = CRAFT_PARTS[part]
        if BASE_MATS[prof] and cp then
          local sp = def.spec and TCF.SPEC_BY_KEY and TCF.SPEC_BY_KEY[def.spec]
          r.spec, r.rank = def.spec, cp.rank
          local mats = {}
          for m, n in pairs(BASE_MATS[prof]) do mats[m] = math.floor(n * cp.share / 10 + 0.5) * 10 end
          if sp then mats[sp.daily] = cp.daily end
          local finds = TCF.RARE_FINDS and TCF.RARE_FINDS[FAMILY_OF[prof]] or {}
          for k, n in ipairs(cp.rare) do if n > 0 and finds[k] then mats[finds[k].key] = n end end
          r.mats = mats
        else
          r.mats = (OTHER[prof] and OTHER[prof][part]) or { lotus = 99 }
        end
        list[#list + 1] = r
       end
      end
    end
  end
end
addRecipes()
TCF.ProfSetsAddRecipes = addRecipes   -- (tests: a set added later)

-- how-to-get lines for a crafted set piece (CosmeticSets.lua TCF:CosmeticSetLines)
function TCF:ProfSetLines(it)
  for _, r in ipairs(TCF.RECIPES[it.craftSet] or {}) do
    if r.item == it.id then
      local p = TCF.PROF_BY_KEY[r.prof]
      local need = { string.format("%s 300", p and p.name or r.prof) }
      if r.spec then local sp = TCF.SPEC_BY_KEY[r.spec]; need[#need + 1] = (sp and sp.name or r.spec) .. " specialization" end
      if r.rank then local g = TCF.GUILDS[r.prof]; need[#need + 1] = string.format("%s with %s", TCF.GUILD_RANKS[r.rank].name, g and g.name or "the guild") end
      local mats = {}
      for m, n in pairs(r.mats) do local mt = TCF.MAT_BY_KEY[m]; mats[#mats + 1] = string.format("%s %s", TCF.FormatBig(n), mt and mt.name or m) end
      table.sort(mats)
      return { "Crafted: " .. table.concat(need, ", "), "Materials: " .. table.concat(mats, ", ") }
    end
  end
  return { "Crafted by a profession" }
end

-- a whole set owned: its title (called after a craft, and at login for sets finished before)
function TCF:CheckSetTitles()
  for _, def in ipairs(TCF.COSMETIC_SETS or {}) do
    if def.title then
      local have, total = self:CosmeticSetProgress(def.key)
      if total > 0 and have >= total then self:EarnTitle(def.title) end
    end
  end
end
