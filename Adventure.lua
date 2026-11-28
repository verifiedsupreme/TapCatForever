-- TapCatForever: Adventure, an idle game. The cat fights through Azeroth's real
-- zones, dungeons and raids (TCF.TIERS, from GearData.lua) using its equipped gear,
-- class level and learned abilities. Bosses drop their real loot.
local ADDON, TCF = ...

local floor, min, max, random = math.floor, math.min, math.max, math.random

TCF.ADV = {
  SWING = 1.0,          -- cat attacks once a second
  MOB_SWING = 1.6,      -- each enemy attacks every 1.6 s
  TAP_STRIKE = 0.15,    -- each key press: 15% of DPS as a bonus paw strike
  -- enemy scaling, tuned with tools/balance.py (expected gear at each level)
  -- typical gear gives ~level^1.12 DPS and ~40 HP per level, so a trash enemy
  -- lasts ~5 s and a dungeon boss ~25 s; raids keep scaling past level 60.
  K = { hp = 5.83, hpExp = 1.12, dps = 0.9, dpsExp = 1.0, raidHp = 1.085, raidDps = 1.065 },   -- 1.6.5: hp +6% (gear picked for each class's own stats hits harder)
  BOSS = { hp = 5, dps = 2.4 },
  RAIDBOSS = { hp = 6, dps = 2.0 },
  -- Chests are paced by time spent fighting, not by kill count, so fast farming
  -- of an easy zone doesn't flood you (players idle here for months).
  -- A chest clock counts seconds while a fight is on; once it passes CHEST_MIN,
  -- each boss kill has a growing chance ((clock - MIN) / RAMP) to drop a chest,
  -- which resets the clock. Dungeons/zones: a Cat Treat Pouch every ~18 min of
  -- fighting (~3/hour). Raids: a Raider's Hoard every ~3 hours of fighting (it is
  -- always an Epic or better, so it comes much more slowly than a Pouch).
  CHEST_MIN = 900, CHEST_RAMP = 600,
  RAID_CHEST_MIN = 3 * 3600, RAID_CHEST_RAMP = 3600,
  -- Dungeon Chests: the first clear of each dungeon (beating its final boss) always gives one.
  -- After that a separate dungeon chest clock counts fight time spent in dungeons (not zones or
  -- raids). Once it passes 2 hours, each repeat kill of a dungeon's final boss has a growing
  -- chance ((clock - 2h) / 1h) to give one, which resets it: about one every 2.5 hours of
  -- dungeon fighting, so running a dungeon over and over can't farm them.
  DUNGEON_CHEST_MIN = 2 * 3600, DUNGEON_CHEST_RAMP = 3600,
  -- Auto-advance tries a zone this many levels before its minimum level (raids still wait for 60;
  -- travelling by hand has no level gate at all).
  AUTO_EARLY = 2,
  -- A zone's final boss has extra health: 1.3x, or 1.1x in the starter zones (minimum level under 20).
  FINAL_HP = 1.3, STARTER_FINAL_HP = 1.1, STARTER_BELOW = 20,
  -- (1.6.0) Level difference, like WoW. Enemies up to DIFF_FREE levels above the cat fight as
  -- before. For each level past that the cat deals DIFF_DMG x less damage (never under DIFF_DMG_MIN)
  -- and takes DIFF_TAKEN x more, and it misses DIFF_MISS plus DIFF_MISS_STEP for each level above
  -- DIFF_FREE (at most DIFF_MISS_MAX). Enemies below the cat give it DIFF_BONUS more damage a level,
  -- at most DIFF_BONUS_MAX. TCF.AdvEnemyLevel says what level an enemy counts as. Tuned with
  -- tools/balance.py --levels: normal progression with Auto-advance stays as it was.
  DIFF_FREE = 3, DIFF_DMG = 0.94, DIFF_DMG_MIN = 0.05, DIFF_TAKEN = 1.06,
  DIFF_MISS = 0.05, DIFF_MISS_STEP = 0.02, DIFF_MISS_MAX = 0.6,
  DIFF_BONUS = 0.01, DIFF_BONUS_MAX = 0.05, ENEMY_LEVEL_MAX = 60,
  LEVEL_DIFF = true,   -- (tools/balance.py turns it off to compare with before)
}
local K, ADV = TCF.ADV.K, TCF.ADV

---------------------------------------------------------------- tiers & stages
function TCF:AdvTier(tier) return TCF.TIERS[min(tier, #TCF.TIERS)] end
function TCF:AdvStages(tier) return #self:AdvTier(tier).bosses * 2 end
local function stageCode(tier, stage) return tier * 100 + stage end
TCF.AdvStageCode = stageCode

-- enemy level ("difficulty") at a stage
function TCF:AdvLevel(tier, stage)
  local t = self:AdvTier(tier)
  local n = self:AdvStages(tier)
  if t.raid then return t.diff + floor(2 * stage / n) end
  return t.diff - 2 + floor(4 * stage / n)
end

function TCF.AdvMobBase(D)
  local hp = K.hp * D ^ K.hpExp
  local dps = K.dps * D ^ K.dpsExp
  if D > 60 then
    hp = K.hp * 60 ^ K.hpExp * K.raidHp ^ (D - 60)
    dps = K.dps * 60 ^ K.dpsExp * K.raidDps ^ (D - 60)
  end
  return hp, dps
end

-- Builds the enemies for a stage: odd stages are packs of 1-3 enemies,
-- even stages are the tier's bosses in order (the last is the final boss).
function TCF:AdvPack(tier, stage)
  local t = self:AdvTier(tier)
  local D = self:AdvLevel(tier, stage)
  local hp, dps = TCF.AdvMobBase(D)
  local pack = {}
  if stage % 2 == 0 then
    local bi = stage / 2
    local b = t.bosses[bi]
    local mult = t.raid and ADV.RAIDBOSS or ADV.BOSS
    local final = bi == #t.bosses
    local finalHp = (t.min or 1) < ADV.STARTER_BELOW and ADV.STARTER_FINAL_HP or ADV.FINAL_HP
    pack[1] = { name = b[1], display = b[2], boss = bi, final = final, level = D + (t.raid and 3 or 1),
      max = floor(hp * mult.hp * (final and finalHp or 1)), dmg = dps * mult.dps * ADV.MOB_SWING }
  else
    local n = 1 + (stage % 3 == 1 and 1 or 0) + ((stage > 2 and random() < 0.5) and 1 or 0)
    n = min(3, n)
    -- different creatures in one pack whenever the zone has enough of them
    local pickFrom = {}
    for i = 1, #t.mobs do pickFrom[i] = t.mobs[i] end
    for i = 1, n do
      local m = table.remove(pickFrom, random(#pickFrom))
      if #pickFrom == 0 then for k = 1, #t.mobs do pickFrom[k] = t.mobs[k] end end
      pack[i] = { name = m[1], display = m[2], level = D, max = floor(hp * (0.85 + random() * 0.3)), dmg = dps * ADV.MOB_SWING }
    end
  end
  for _, m in ipairs(pack) do
    m.hp = m.max; m.alive = true; m.swing = random() * ADV.MOB_SWING
    m.zoneMin, m.zoneLow = t.min, t.diff - 2   -- (for TCF.AdvEnemyLevel)
  end
  return pack, D
end

-- The level at which Auto-advance moves into a zone: AUTO_EARLY levels before its minimum level,
-- except raids, which wait for their full level (60).
function TCF:AdvAutoLevel(tier)
  local t = TCF.TIERS[tier]
  if not t then return nil end
  if t.raid then return t.min end
  return max(1, t.min - ADV.AUTO_EARLY)
end

---------------------------------------------------------------- run state
function TCF:AdvLog(text)
  self.advLog = self.advLog or {}
  table.insert(self.advLog, 1, text)
  if #self.advLog > 6 then table.remove(self.advLog) end
end

function TCF:AdvEvent(kind, a, b, c)
  local run = self.advRun
  if not run or not self.advWatching then return end
  if #run.events < 60 then table.insert(run.events, { kind, a, b, c }) end
end

function TCF:AdvReset()
  local st = self:CombatStats()
  self.advRun = { class = self.db.class, catMax = st.hp, catHP = st.hp, swing = 0, respawn = 0.6, events = {},
    stats = st, cds = {}, buffs = {}, dots = {}, shield = 0, stunUntil = 0, t = 0 }
end

function TCF:AdvSpawn()
  local adv = self:CD().adv
  local run = self.advRun
  run.pack, run.level = self:AdvPack(adv.tier, adv.stage)
  run.target = 1
  run.dots = {}
  -- run.t keeps counting across packs: buffs, cooldowns and bandages all use it,
  -- so resetting it here would leave buffs up forever and refresh every cooldown
  run.stunUntil = run.t
  self:AdvEvent("spawn")
end

local function alive(run)
  local n = 0
  for _, m in ipairs(run.pack or {}) do if m.alive then n = n + 1 end end
  return n
end
TCF.AdvAlive = alive

local function pickTarget(run)
  if not run.pack then return end
  if run.pack[run.target] and run.pack[run.target].alive then return run.pack[run.target], run.target end
  for i, m in ipairs(run.pack) do if m.alive then run.target = i; return m, i end end
end

---------------------------------------------------------------- level difference (1.6.0)
-- The level an enemy counts as against the cat: the zone's lowest level (the "Levels 10-18" on
-- the Adventure page) for the first packs, one level more for every 2 levels its pack's difficulty
-- (TCF:AdvLevel, plus 1 for a boss) is above the zone's first stage, so a zone's last boss counts
-- as 2 or 3 levels over the zone's lowest level. Raids count as level 60 (their difficulty above
-- 60 is for gear, not levels). m: an enemy of TCF:AdvPack, or a level.
function TCF.AdvEnemyLevel(m)
  local lv = (type(m) == "table" and m.level) or tonumber(m) or 1
  if type(m) == "table" and m.zoneMin and m.zoneLow then
    lv = m.zoneMin + floor(max(0, lv - m.zoneLow) / 2)
  end
  return min(ADV.ENEMY_LEVEL_MAX, lv)
end
-- the level the enemies of a stage count as (a boss: its own level)
function TCF:AdvStageEnemyLevel(tier, stage)
  local t = self:AdvTier(tier)
  local D = self:AdvLevel(tier, stage)
  if stage % 2 == 0 then D = D + (t.raid and 3 or 1) end
  return TCF.AdvEnemyLevel({ level = D, zoneMin = t.min, zoneLow = t.diff - 2 })
end
-- how many levels the enemies where the cat is now are above it (the pack it fights, else its stage)
function TCF:AdvLevelGap(class)
  local cd = self:CD(class)
  if not cd then return 0 end
  local run = self.advRun
  local top
  if run and run.pack and run.class == (class or self.db.class) then
    for _, m in ipairs(run.pack) do
      if m.alive ~= false then local lv = TCF.AdvEnemyLevel(m); if not top or lv > top then top = lv end end
    end
  end
  top = top or self:AdvStageEnemyLevel(cd.adv.tier, cd.adv.stage)
  return top - (cd.level or 1)
end
TCF.ADV_GAP_WARN = 5   -- the Adventure page says so from this many levels

-- levels the enemy is above the cat (negative: below)
local function levelDiff(self, run, m)
  local cd = self:CD(run and run.class)
  return TCF.AdvEnemyLevel(m) - (cd and cd.level or 1)
end
-- the cat's damage multiplier, its miss chance and the enemy's damage multiplier at a level difference
function TCF.AdvLevelMods(diff)
  if not ADV.LEVEL_DIFF or diff == 0 then return 1, 0, 1 end
  if diff < 0 then return 1 + min(ADV.DIFF_BONUS_MAX, ADV.DIFF_BONUS * -diff), 0, 1 end
  local d = diff - ADV.DIFF_FREE
  if d <= 0 then return 1, 0, 1 end
  return max(ADV.DIFF_DMG_MIN, ADV.DIFF_DMG ^ d), min(ADV.DIFF_MISS_MAX, ADV.DIFF_MISS + ADV.DIFF_MISS_STEP * d), ADV.DIFF_TAKEN ^ d
end

---------------------------------------------------------------- damage
local function dmgMult(self, run)
  local m = 1
  for _, a in ipairs(TCF.ABILITIES[run.class]) do
    if a.kind == "passive" and self:AbilityKnown(run.class, a.key) then m = m + a.value end
  end
  for _, b in pairs(run.buffs) do if b.kind == "buff" and b["until"] > run.t then m = m + b.value end end
  return m
end

local function takenMult(self, run, D)
  local armor = run.stats.armor
  local dr = armor / (armor + 400 + 85 * D)
  local m = 1 - min(0.75, dr)
  for _, a in ipairs(TCF.ABILITIES[run.class]) do
    if a.kind == "ward" and self:AbilityKnown(run.class, a.key) then m = m * (1 - a.value) end
  end
  for _, b in pairs(run.buffs) do if b.kind == "defense" and b["until"] > run.t then m = m * (1 - b.value) end end
  return m
end

function TCF:AdvHitMob(m, idx, dmg, kind)
  if not m.alive then return end
  -- (1.6.0) an enemy above the cat's level takes less damage and dodges more (damage over time
  -- ticks can't miss: the spell already landed)
  local run = self.advRun
  if run then
    local mult, miss = TCF.AdvLevelMods(levelDiff(self, run, m))
    if miss > 0 and kind ~= "dot" and random() < miss then
      self:AdvEvent("miss", 0, idx)
      return
    end
    dmg = dmg * mult
  end
  m.hp = m.hp - dmg
  self:AdvEvent(kind, dmg, idx)
  if m.hp <= 0 then
    m.alive = false
    self:AdvEvent("mobdie", idx)
    self:AdvMobKilled(m)
  end
end

function TCF:AdvTapStrike()
  local run = self.advRun
  if not run or not run.pack or run.respawn > 0 or run.class ~= self.db.class or run.away or not self:CD().adv.active then return end
  local m, i = pickTarget(run)
  if m then self:AdvHitMob(m, i, run.stats.dps * ADV.TAP_STRIKE * dmgMult(self, run), "tap") end
  if run.pack and alive(run) == 0 then self:AdvPackCleared() end
end

---------------------------------------------------------------- abilities AI
local function ready(run, a) return (run.cds[a.key] or 0) <= run.t end

function TCF:AdvUseAbility(run)
  local class = run.class
  local list = TCF.ABILITIES[class]
  local hpPct = run.catHP / run.catMax
  local nAlive = alive(run)
  local target = pickTarget(run)
  if not target then return end
  local boss = target.boss ~= nil
  local function usable(a) return self:AbilityKnown(class, a.key) and ready(run, a) end
  local choice
  -- priority: survive, control, buff, aoe, execute, dot, nuke
  for _, a in ipairs(list) do
    if usable(a) and (a.kind == "heal" or a.kind == "drain") and hpPct < 0.5 then choice = a; break end
  end
  if not choice then
    for _, a in ipairs(list) do
      if usable(a) and (a.kind == "defense" or a.kind == "shield") and (hpPct < 0.6 or (boss and hpPct < 0.85)) then choice = a; break end
    end
  end
  if not choice then
    for _, a in ipairs(list) do
      if usable(a) and a.kind == "stun" and (nAlive >= 2 or boss) and run.stunUntil <= run.t then choice = a; break end
    end
  end
  if not choice then
    for _, a in ipairs(list) do if usable(a) and a.kind == "buff" and (boss or nAlive >= 2) then choice = a; break end end
  end
  if not choice and nAlive >= 2 then
    for _, a in ipairs(list) do if usable(a) and a.kind == "aoe" then choice = a; break end end
  end
  if not choice and target.hp / target.max < 0.2 then
    for _, a in ipairs(list) do if usable(a) and a.kind == "execute" then choice = a; break end end
  end
  if not choice and target.hp > run.stats.dps * 6 then
    for _, a in ipairs(list) do if usable(a) and a.kind == "dot" and not run.dots[a.key] then choice = a; break end end
  end
  if not choice then
    local best
    for _, a in ipairs(list) do
      if usable(a) and (a.kind == "nuke" or a.kind == "drain") and (not best or a.value > best.value) then best = a end
    end
    -- (1.6.0) an area spell also hits a lone enemy (a boss): it goes off when no single-target
    -- spell is ready, so spells like Arcane Explosion aren't kept for packs only
    if not best then
      for _, a in ipairs(list) do
        if usable(a) and a.kind == "aoe" and (not best or a.value > best.value) then best = a end
      end
    end
    choice = best
  end
  if not choice then return end

  run.cds[choice.key] = run.t + choice.cd
  local dps = run.stats.dps * dmgMult(self, run)
  local k = choice.kind
  self:AdvEvent("ability", choice.name, choice.icon, { key = choice.key, kind = k, target = run.target, class = class })
  if k == "nuke" or k == "execute" or k == "drain" then
    local crit = random() * 100 < run.stats.crit
    if k == "drain" then run.catHP = min(run.catMax, run.catHP + run.catMax * (choice.value >= 2 and 0.1 or 0.15)) end
    self:AdvHitMob(target, run.target, dps * choice.value * (crit and 1.5 or 1), crit and "crit" or "hit")
  elseif k == "aoe" then
    for i, m in ipairs(run.pack) do if m.alive then self:AdvHitMob(m, i, dps * choice.value, "hit") end end
  elseif k == "dot" then
    run.dots[choice.key] = { target = run.target, perSec = dps * choice.value / choice.dur, ["until"] = run.t + choice.dur }
  elseif k == "heal" then
    run.catHP = min(run.catMax, run.catHP + run.catMax * choice.value)
    self:AdvEvent("heal", run.catMax * choice.value)
  elseif k == "shield" then
    run.shield = run.catMax * choice.value
  elseif k == "buff" or k == "defense" then
    run.buffs[choice.key] = { kind = k, value = choice.value, ["until"] = run.t + choice.dur }
  elseif k == "stun" then
    run.stunUntil = run.t + choice.dur
  end
end

---------------------------------------------------------------- rewards
-- TapCoins for clearing a zone (beating its last boss) the first time: 200 for Elwynn Forest,
-- 50 more for each zone after it (1,550 for Naxxramas). The first of your cats to clear a zone
-- gets the full amount; another class clearing it later gets a quarter.
TCF.ADV_CLEAR_BASE, TCF.ADV_CLEAR_STEP, TCF.ADV_CLEAR_REPEAT = 200, 50, 0.25
function TCF:AdvClearCoins(tier)
  local t = self:AdvTier(tier)
  local full = TCF.ADV_CLEAR_BASE + TCF.ADV_CLEAR_STEP * (tier - 1)
  local done = t and self.db.zonesCleared and self.db.zonesCleared[t.key]
  return done and math.floor(full * TCF.ADV_CLEAR_REPEAT) or full
end

-- Rewards are mostly chests (opened from the Treasure Bag); no direct gear and
-- only a one-time TapCoin bonus per zone, so idling doesn't flood you with loot.
function TCF:AdvMobKilled(m)
  local adv = self:CD().adv
  adv.kills = adv.kills + 1
  local t = self:AdvTier(adv.tier)
  if m.boss then
    adv.bossKills = adv.bossKills + 1
    local key = stageCode(adv.tier, adv.stage)
    local first = not adv.cleared[key]
    adv.cleared[key] = true
    self:AdvLog(string.format("|cffffd100Defeated %s.|r", m.name))
    -- rare cat skins some bosses drop (one entry, or a list if a boss drops several)
    local sd = TCF.SKIN_DROPS[m.name]
    if sd then
      for _, d in ipairs(sd.id and { sd } or sd) do
        if not self.db.owned[d.id] and random() < (d.chance or 0) then
          self:GrantSkin(d.id, "Dropped by " .. m.name .. " in " .. t.name)
          break
        end
      end
    end
    -- the first time you beat each boss it gives a reward that grows with the zone
    -- (AdventureRewards.lua: gear from its real loot, and chests in bigger zones)
    if first and self.AdvFirstKillReward then
      local got = self:AdvFirstKillReward(adv.tier, m)
      if got and got ~= "" then self:AdvLog("First kill: " .. got) end
    elseif self.AdvRepeatLoot then
      -- repeat kills: a small chance of a piece of its real loot (farming)
      local drop = self:AdvRepeatLoot(adv.tier, m)
      if drop then self:AdvLog("Loot: " .. (TCF.GearLink and TCF.GearLink(drop) or drop.name) .. " from " .. m.name) end
      if self.AdvFarmKill then self:AdvFarmKill(adv.tier, m, drop) end
    end
    -- cosmetics this boss gives on every kill until you have them (TCF.BOSS_COSMETICS)
    if self.AdvBossCosmetics then self:AdvBossCosmetics(m) end
    -- back effects some late final bosses unlock (BossEffects.lua: a short notice over the cat)
    if self.AdvBossEffect then self:AdvBossEffect(m) end
    if m.final and first then
      local coins = self:AdvClearCoins(adv.tier)
      self.db.zonesCleared = self.db.zonesCleared or {}   -- account-wide: the first cat to clear it gets the full bonus
      self.db.zonesCleared[t.key] = true
      self:AddCoins(coins)
      -- clearing a raid zone in Adventure counts for the raid achievements (WoW: Forever has no raids yet)
      if t.raid then self.db.stats.raids = (self.db.stats.raids or 0) + 1 end
      -- raids give a Raider's Hoard, dungeons a Dungeon Chest, open-world zones a Strongbox
      local dungeon = TCF.IsDungeonTier(t)
      if dungeon then adv.dungeonClock = 0 end
      self:AwardChest(t.raid and "raid" or dungeon and "dungeon" or "strong", t.name .. " cleared")
      self:AdvLog(string.format("|cff20ff20%s cleared for the first time.|r +%s TapCoins and a chest", t.name, TCF.Commas(coins)))
    elseif m.final and TCF.IsDungeonTier(t) and random() < min(1, max(0, ((adv.dungeonClock or 0) - ADV.DUNGEON_CHEST_MIN) / ADV.DUNGEON_CHEST_RAMP)) then
      -- finishing a dungeon again: a Dungeon Chest on the dungeon chest clock (instead of a Pouch roll)
      adv.dungeonClock = 0
      self:AwardChest("dungeon", t.name .. " finished")
      self:AdvLog("Loot: a " .. TCF.CHEST_BY_KEY.dungeon.name .. " for finishing " .. t.name)
    else
      local lo, ramp = ADV.CHEST_MIN, ADV.CHEST_RAMP
      if t.raid then lo, ramp = ADV.RAID_CHEST_MIN, ADV.RAID_CHEST_RAMP end
      if random() < min(1, max(0, ((adv.chestClock or 0) - lo) / ramp)) then
        adv.chestClock = 0
        local chest = t.raid and "raid" or "pouch"
        self:AwardChest(chest, m.name)
        self:AdvLog("Loot: a " .. TCF.CHEST_BY_KEY[chest].name .. " from " .. m.name)
      end
    end
  else
    -- profession ingredients: cloth for First Aid, meat for Cooking
    if self.DropCloth then self:DropCloth(m.level) end
    if self.DropMeat then self:DropMeat(m.level) end
    -- now and then a small find: a white or green piece for the cat's level (Gear.lua)
    if self.TrashSmallFind then self:TrashSmallFind(m, t) end
  end
  self:MarkDirty()
end

function TCF:AdvPackCleared()
  local run, cd = self.advRun, self:CD()
  local adv = cd.adv
  local code = stageCode(adv.tier, adv.stage)
  if code > adv.best then
    adv.best = code; adv.newStages = (adv.newStages or 0) + 1
  end
  -- (1.7.5) the dungeon's last stage cleared (first time, again, or farming): its companion cat joins you
  if adv.stage >= self:AdvStages(adv.tier) and self.CompanionEarnFromClear then self:CompanionEarnFromClear(adv.tier) end
  if self.advRun then self.advRun.losses = 0 end
  run.catHP = min(run.catMax, run.catHP + run.catMax * 0.35)
  run.shield = 0
  if adv.auto then
    if adv.stage >= self:AdvStages(adv.tier) then
      local nt = TCF.TIERS[adv.tier + 1]
      if nt and cd.level >= self:AdvAutoLevel(adv.tier + 1) then
        adv.tier, adv.stage = adv.tier + 1, 1
        run.catHP = run.catMax
        self:AdvLog("Onward to " .. nt.name .. ".")
      else
        adv.stage = 1
        if nt then
          -- once per change (a new zone or level to wait for), not after every run of the zone
          local need = self:AdvAutoLevel(adv.tier + 1)
          local key = nt.name .. ":" .. need .. ":" .. self.db.class
          if self.advWaitNote ~= key then
            self.advWaitNote = key
            self:AdvLog(string.format("|cffaaaaaa%s opens at level %d. Running %s again until then.|r", nt.name, need, self:AdvTier(adv.tier).name))
          end
        end
      end
    else
      adv.stage = adv.stage + 1
    end
  end
  -- farming one boss keeps the cat on its stage (AdventureRewards.lua)
  if adv.farm and self.AdvFarmAfterClear then self:AdvFarmAfterClear() end
  self:AdvEvent("kill")
  run.pack = nil
  run.respawn = 1.2
  self:MarkDirty()
end

function TCF:AdvDefeat()
  local run, adv = self.advRun, self:CD().adv
  local m = pickTarget(run)
  local line = string.format("|cffff6060%s was too strong.|r Your cat retreats to heal. |cff999999(Better gear, levels and abilities help.)|r", m and m.name or "The enemy")
  -- the same retreat line again right after it (a hard boss beats the cat a few times) is left out
  if not self.advLog or (self.advLog[1] ~= line and self.advLog[2] ~= line) then self:AdvLog(line) end
  -- with Auto-advance off the cat retries the same stage (it was told to farm here),
  -- but after 3 losses in a row it drops back to an easier pack instead of losing forever
  run.losses = (run.losses or 0) + 1
  if not adv.auto and run.losses >= 3 and (adv.stage > 1 or adv.tier > 1) then
    run.losses = 0
    if adv.stage == 1 then
      adv.tier = adv.tier - 1
      adv.stage = max(1, self:AdvStages(adv.tier) - 1)
    else
      adv.stage = max(1, adv.stage - 1)
      if adv.stage % 2 == 0 then adv.stage = max(1, adv.stage - 1) end
    end
    self:AdvLog("Your cat lost 3 times in a row and drops back to an easier pack.")
  end
  if adv.auto then
    if adv.stage == 1 and adv.tier > 1 then
      -- losing at the very start of a zone: fall back to the previous zone's last trash pack
      adv.tier = adv.tier - 1
      adv.stage = max(1, self:AdvStages(adv.tier) - 1)
      self:AdvLog("Your cat falls back to " .. self:AdvTier(adv.tier).name .. ".")
    else
      adv.stage = max(1, adv.stage - 1)
      if adv.stage % 2 == 0 then adv.stage = max(1, adv.stage - 1) end -- back to the last trash pack
    end
  end
  run.catHP = run.catMax
  run.pack = nil
  run.respawn = 2.5
  run.buffs = {}; run.shield = 0
  self:AdvEvent("defeat")
end

---------------------------------------------------------------- simulation step
function TCF:AdvTick(dt)
  local run = self.advRun
  if not run or run.class ~= self.db.class then self:AdvReset(); run = self.advRun end
  -- a cat away on an expedition can't fight here
  run.away = self.IsOnExpedition and self:IsOnExpedition(run.class) or false
  if run.away then return end
  -- nothing happens until the player presses Start
  if not self:CD().adv.active then return end
  local st = self:CombatStats()
  run.stats = st
  if st.hp ~= run.catMax then
    run.catHP = run.catHP * st.hp / run.catMax
    run.catMax = st.hp
  end
  if run.respawn > 0 then
    run.respawn = run.respawn - dt
    if run.respawn <= 0 then self:AdvSpawn() end
    return
  end
  if not run.pack then return end
  run.t = run.t + dt
  local cadv = self:CD().adv
  cadv.chestClock = (cadv.chestClock or 0) + dt -- only counts while a fight is on
  -- the Dungeon Chest clock: fight time in dungeons only
  if TCF.IsDungeonTier(self:AdvTier(cadv.tier)) then cadv.dungeonClock = (cadv.dungeonClock or 0) + dt end
  -- the small-find gap clock (Gear.lua TrashSmallFind): saved per class, also fight time only.
  -- nil means this class has never had a find, so its first one is not held back.
  if cadv.findClock then cadv.findClock = cadv.findClock + dt end
  for key, d in pairs(run.dots) do
    if d["until"] < run.t then run.dots[key] = nil
    else
      local m = run.pack[d.target]
      if m and m.alive then self:AdvHitMob(m, d.target, d.perSec * dt, "dot") end
    end
  end
  if not run.pack then return end
  run.swing = run.swing + dt
  while run.pack and run.swing >= ADV.SWING and alive(run) > 0 do
    run.swing = run.swing - ADV.SWING
    local m, i = pickTarget(run)
    if m then
      local crit = random() * 100 < st.crit
      self:AdvEvent("swing", 0, i) -- the basic attack's look (a shot, wand bolt, spell or swipe: AdventureFX.lua)
      self:AdvHitMob(m, i, st.dps * dmgMult(self, run) * (crit and 2 or 1), crit and "crit" or "hit")
    end
    if alive(run) > 0 then self:AdvUseAbility(run) end
  end
  if not run.pack then return end
  if alive(run) == 0 then self:AdvPackCleared(); return end
  if self.UseBandage then self:UseBandage(run) end
  if run.stunUntil > run.t then return end
  local mult = takenMult(self, run, run.level)
  for i, m in ipairs(run.pack) do
    if m.alive then
      m.swing = m.swing + dt
      if m.swing >= ADV.MOB_SWING then
        m.swing = m.swing - ADV.MOB_SWING
        local _, _, taken = TCF.AdvLevelMods(levelDiff(self, run, m))   -- (1.6.0) higher enemies hit harder
        local dmg = m.dmg * mult * taken * (0.85 + random() * 0.3)
        if run.shield > 0 then
          local absorbed = min(run.shield, dmg)
          run.shield = run.shield - absorbed; dmg = dmg - absorbed
        end
        run.catHP = run.catHP - dmg
        self:AdvEvent("hurt", dmg, i)
        if run.catHP <= 0 then self:AdvDefeat(); return end
      end
    end
  end
end

---------------------------------------------------------------- manual navigation
-- You can revisit any stage you've reached, as long as you meet the tier's level.
function TCF:AdvCanGoTo(tier, stage)
  local cd = self:CD()
  local t = TCF.TIERS[tier]
  if not t or stage < 1 or stage > self:AdvStages(tier) then return false end
  -- no level gate: once you've beaten a zone you may push on (Auto-advance still waits for the level)
  local code = stageCode(tier, stage)
  if code <= cd.adv.best + 1 or code == 101 then return true end
  -- first stage of the next tier once the previous tier is fully cleared
  return stage == 1 and tier > 1 and cd.adv.best >= stageCode(tier - 1, self:AdvStages(tier - 1))
end

function TCF:AdvGoTo(tier, stage)
  if not self:AdvCanGoTo(tier, stage) then return false end
  local adv = self:CD().adv
  adv.tier, adv.stage = tier, stage
  local run = self.advRun
  if run then run.pack = nil; run.respawn = 0.4; run.catHP = run.catMax; run.buffs = {}; run.shield = 0 end
  return true
end

function TCF:AdvStep(delta)
  local adv = self:CD().adv
  local tier, stage = adv.tier, adv.stage + delta
  if stage > self:AdvStages(tier) then tier, stage = tier + 1, 1
  elseif stage < 1 then tier = tier - 1; if tier >= 1 then stage = self:AdvStages(tier) end end
  return self:AdvGoTo(tier, stage)
end

---------------------------------------------------------------- start / retreat
function TCF:AdvStart()
  local adv = self:CD().adv
  if adv.active then return end
  adv.active = true
  if self.advRun then self.advRun.pack = nil; self.advRun.respawn = 0.8; self.advRun.catHP = self.advRun.catMax end
  self:AdvLog("Your cat sets out into " .. self:AdvTier(adv.tier).name .. ".")
  self:PlaySound("click")
  self:MarkDirty()
end

function TCF:AdvRetreat()
  local adv = self:CD().adv
  adv.active = false
  local run = self.advRun
  if run then run.pack = nil; run.respawn = 0.5; run.catHP = run.catMax; run.buffs = {}; run.shield = 0 end
  self:AdvLog("Your cat heads home to rest.")
  self:AdvEvent("defeat")
  self:MarkDirty()
end
