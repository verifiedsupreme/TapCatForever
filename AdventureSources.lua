-- TapCatForever: "how to get it" lines for the Adventure track's rewards, added to the lines
-- Compendium.lua gives (TCF:HowToGet, used by the Compendium and item tooltips):
--  * cosmetics an Adventure boss gives until owned (TCF.BOSS_COSMETICS)
--  * the chance to farm a piece of boss loot on later kills (AdventureRewards.lua)
--  * real WoW boss rewards and boss-unlocked effects (RealBosses.lua, BossEffects.lua)
local ADDON, TCF = ...

local function extraLines(self, it)
  local out = {}
  if not it then return out end
  if it.q and not it.rarity then
    -- real gear: farming it from its Adventure boss
    local t = it.tier and it.tier > 0 and TCF.TIERS[it.tier]
    local b = t and it.boss and it.boss > 0 and t.bosses[it.boss]
    if b and self.AdvFarmChance and self.db then
      local p = self:AdvFarmChance(it.tier, it.boss, it.id)
      if p > 0 then
        out[#out + 1] = string.format("Adventure: after its first kill, %s drops it for your cat about %s of the time (%s). Use Farm in Bosses and loot",
          b[1], TCF.AdvPct(p), TCF.AdvOneIn(p))
      end
    end
    return out
  end
  if self.BossCosmeticSources then
    for _, s in ipairs(self:BossCosmeticSources(it.id)) do
      out[#out + 1] = string.format("Adventure: %s%s gives it every time you beat it, until you have it", s[1], s[2] and (" in " .. s[2]) or "")
    end
  end
  if self.RealBossSourceLines then
    for _, l in ipairs(self:RealBossSourceLines(it)) do out[#out + 1] = l end
  end
  if self.BossEffectSourceLines then
    for _, l in ipairs(self:BossEffectSourceLines(it)) do out[#out + 1] = l end
  end
  return out
end
TCF.AdvExtraSourceLines = extraLines

-- Compendium.lua's gear lines still say every boss's first kill drops a piece of its loot;
-- the reward now grows with the zone (AdventureRewards.lua), so that line says what it gives
local OLD_FIRST_KILL = "Each Adventure boss always drops a piece of its own loot the first time you beat it"
local function firstKillLine(self, it)
  local t = it.tier and it.tier > 0 and TCF.TIERS[it.tier]
  local b = t and it.boss and it.boss > 0 and t.bosses[it.boss]
  if not b or not self.AdvFirstKillText then return nil end
  return string.format("The first time your cat beats %s it gives %s, picked from what your cat's class can use",
    b[1], self:AdvFirstKillText(it.tier, it.boss == #t.bosses))
end

do
  local how = TCF.HowToGet
  if how then
    function TCF:HowToGet(it)
      local out = how(self, it)
      if it and it.q and not it.rarity then
        for i, l in ipairs(out) do
          if l == OLD_FIRST_KILL then out[i] = firstKillLine(self, it) or l end
        end
      end
      local extra = extraLines(self, it)
      if #extra > 0 then
        -- "Not available right now" no longer applies when the Adventure track has a source
        if #out == 1 and out[1] == "Not available right now" then out = {} end
        for _, l in ipairs(extra) do out[#out + 1] = l end
      end
      return out
    end
  end
end

-- the short source word on Compendium skin cells: "WoW" for a skin from a real boss
do
  local tag = TCF.SkinSourceTag
  if tag then
    function TCF.SkinSourceTag(it)
      if TCF.RealBossRewardsFor and #TCF:RealBossRewardsFor(it.id) > 0 then return "WoW" end
      return tag(it)
    end
  end
end

-- the Treasure Bag's chest sources (UI.lua): first kills in Adventure now give chests too
do
  local ADD = {
    ["Cat Treat Pouch:"] = "Also first kills of Adventure bosses in open-world zones and early dungeons.",
    ["Adventurer's Strongbox:"] = "Also first kills of Adventure bosses in dungeons from level 30 (a chance).",
    ["Dungeon Chest:"] = "Also first kills of Adventure bosses in dungeons from level 45.",
  }
  for i, line in ipairs(TCF.CHEST_SOURCES or {}) do
    for prefix, more in pairs(ADD) do
      if type(line) == "string" and line:sub(1, #prefix) == prefix and not line:find(more, 1, true) then
        TCF.CHEST_SOURCES[i] = line .. " " .. more
      end
    end
  end
end
