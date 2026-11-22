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
  return out
end
TCF.AdvExtraSourceLines = extraLines

do
  local how = TCF.HowToGet
  if how then
    function TCF:HowToGet(it)
      local out = how(self, it)
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
