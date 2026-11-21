-- TapCatForever: Adventure, an idle game where the cat fights through tiers of
-- Azeroth using the gear equipped on the current class.
local ADDON, TCF = ...

local floor, min, max, random = math.floor, math.min, math.max, math.random

---------------------------------------------------------------- zones
-- Each tier is 10 stages; stage 10 is the boss. After the last zone the list
-- repeats as Heroic tiers with higher numbers.
-- mobs: { name, icon }; colours: sky, ground
TCF.ZONES = {
  { name = "Elwynn Forest", sky = { 0.42, 0.62, 0.90 }, ground = { 0.27, 0.52, 0.22 },
    mobs = { { "Kobold Tunneler", "INV_Pick_02" }, { "Murloc Raider", "INV_Misc_Head_Murloc_01" }, { "Young Wolf", "Ability_Hunter_Pet_Wolf" } },
    boss = { "Hogger", "Ability_Hunter_Pet_Hyena" } },
  { name = "The Deadmines", sky = { 0.80, 0.66, 0.42 }, ground = { 0.52, 0.42, 0.26 },
    mobs = { { "Defias Thug", "Ability_Rogue_Ambush" }, { "Harvest Watcher", "INV_Misc_Gear_01" }, { "Gnoll Brute", "Ability_Hunter_Pet_Hyena" } },
    boss = { "Edwin VanCleef", "Achievement_Boss_EdwinVancleef" } },
  { name = "Duskwood", sky = { 0.18, 0.18, 0.32 }, ground = { 0.18, 0.24, 0.18 },
    mobs = { { "Skeletal Warrior", "Spell_Shadow_RaiseDead" }, { "Nightbane Worgen", "Ability_Mount_WhiteDireWolf" }, { "Venom Web Spider", "Ability_Hunter_Pet_Spider" } },
    boss = { "Stitches", "Spell_Shadow_AnimateDead" } },
  { name = "Stranglethorn Vale", sky = { 0.38, 0.72, 0.66 }, ground = { 0.18, 0.42, 0.18 },
    mobs = { { "Jungle Raptor", "Ability_Hunter_Pet_Raptor" }, { "Skullsplitter Troll", "INV_Misc_Head_Troll_01" }, { "Silverback Gorilla", "Ability_Hunter_Pet_Gorilla" } },
    boss = { "King Bangalash", "Ability_Mount_JungleTiger" } },
  { name = "Uldaman", sky = { 0.82, 0.52, 0.32 }, ground = { 0.50, 0.32, 0.22 },
    mobs = { { "Dustbelcher Ogre", "Ability_Warrior_Cleave" }, { "Badlands Scorpid", "Ability_Hunter_Pet_Scorpid" }, { "Stone Keeper", "Spell_Nature_Earthquake" } },
    boss = { "Archaedas", "INV_Misc_StoneTablet_04" } },
  { name = "Zul'Farrak", sky = { 0.94, 0.80, 0.50 }, ground = { 0.80, 0.66, 0.38 },
    mobs = { { "Sandfury Axe Thrower", "INV_Misc_Head_Troll_01" }, { "Sand Basilisk", "Ability_Hunter_Pet_Crocolisk" }, { "Wastewander Pirate", "INV_Misc_Bandana_03" } },
    boss = { "Gahz'rilla", "Ability_Hunter_Pet_Turtle" } },
  { name = "Blackrock Depths", sky = { 0.32, 0.10, 0.07 }, ground = { 0.24, 0.14, 0.11 },
    mobs = { { "Dark Iron Watchman", "INV_Hammer_09" }, { "Fireguard", "Spell_Fire_Fire" }, { "Molten Imp", "Spell_Shadow_SummonImp" } },
    boss = { "Emperor Dagran Thaurissan", "INV_Crown_01" } },
  { name = "Stratholme", sky = { 0.28, 0.28, 0.24 }, ground = { 0.22, 0.28, 0.18 },
    mobs = { { "Plague Ghoul", "Spell_Shadow_RaiseDead" }, { "Bile Abomination", "Spell_Shadow_AbominationExplosion" }, { "Wailing Banshee", "Spell_Shadow_SoulLeech_3" } },
    boss = { "Baron Rivendare", "Ability_Mount_Undeadhorse" } },
  { name = "Molten Core", sky = { 0.48, 0.12, 0.02 }, ground = { 0.33, 0.07, 0.03 },
    mobs = { { "Core Hound", "Ability_Hunter_Pet_CoreHound" }, { "Lava Surger", "Spell_Fire_Volcano" }, { "Firelord", "Spell_Fire_Elemental_Totem" } },
    boss = { "Ragnaros", "Achievement_Boss_Ragnaros" } },
  { name = "Blackwing Lair", sky = { 0.20, 0.10, 0.15 }, ground = { 0.14, 0.09, 0.10 },
    mobs = { { "Death Talon Wyrmguard", "INV_Misc_Head_Dragon_Black" }, { "Chromatic Whelp", "INV_Misc_Head_Dragon_Bronze" }, { "Blackwing Technician", "INV_Gizmo_01" } },
    boss = { "Nefarian", "Achievement_Boss_Nefarion" } },
  { name = "Temple of Ahn'Qiraj", sky = { 0.66, 0.52, 0.30 }, ground = { 0.56, 0.42, 0.24 },
    mobs = { { "Qiraji Champion", "INV_Qiraj_JewelBlessed" }, { "Anubisath Sentinel", "INV_Misc_AhnQirajTrinket_04" }, { "Vekniss Soldier", "Ability_Hunter_Pet_Silithid" } },
    boss = { "C'Thun", "Achievement_Boss_CThun" } },
  { name = "Naxxramas", sky = { 0.18, 0.24, 0.34 }, ground = { 0.13, 0.18, 0.24 },
    mobs = { { "Plagued Ghoul", "Spell_Shadow_RaiseDead" }, { "Patchwork Golem", "Spell_Shadow_AbominationExplosion" }, { "Crypt Reaver", "Ability_Hunter_Pet_Spider" } },
    boss = { "Kel'Thuzad", "Achievement_Boss_KelThuzad_01" } },
}
local MOB_FALLBACK = "INV_Misc_Bone_HumanSkull_01"

TCF.ADV = {
  ATTACK_INTERVAL = 1.0,   -- cat swings once a second
  MOB_INTERVAL = 1.6,      -- mobs swing every 1.6 s
  TAP_STRIKE = 0.25,       -- each key press adds 25% of attack as a paw strike
  POWER = { 4, 9, 18, 34, 60 }, -- gear power by rarity
}

function TCF:AdvZone(tier)
  local n = #TCF.ZONES
  local idx = (tier - 1) % n + 1
  local heroic = floor((tier - 1) / n)
  local z = TCF.ZONES[idx]
  local name = heroic > 0 and (z.name .. " |cffff8000(Heroic " .. heroic .. ")|r") or z.name
  return z, name, heroic
end

function TCF:AdvMob(tier, stage)
  local z = self:AdvZone(tier)
  local g = (tier - 1) * 10 + stage
  local isBoss = stage == 10
  local m = isBoss and z.boss or z.mobs[(stage - 1) % #z.mobs + 1]
  -- tuned so each tier lines up with a gear/level milestone (see README)
  -- Heroic tiers (past stage 120) grow more slowly so class levels keep you going.
  local scale = 1.04 ^ min(g, 120) * 1.005 ^ max(0, g - 120)
  local hp = 28 * scale
  local dmg = 4 * scale
  if isBoss then hp, dmg = hp * 4, dmg * 1.5 end
  return { name = m[1], icon = TCF.Icon(m[2], MOB_FALLBACK), boss = isBoss, hp = floor(hp), dmg = dmg, g = g }
end

---------------------------------------------------------------- cat combat stats from gear
function TCF:AdvStats(class)
  class = class or self.db.class
  local lo = self:GetLoadout(class)
  local P = TCF.ADV.POWER
  local function pw(slot)
    local it = lo[slot] and TCF.ITEMS[lo[slot]]
    return it and P[it.rarity] or 0, it and it.rarity or 0
  end
  local main, off, head, chest, back = pw("main"), pw("off"), pw("head"), pw("chest"), pw("back")
  local _, fxR = pw("effect")
  local _, accR = pw("acc")
  local level = self:CD(class).level
  local mult = 1 + 0.08 * (level - 1)
  local s = {
    atk = (5 + main * 1.5 + off * 0.75) * mult,
    hp = (50 + (head + chest + back) * 6 + off * 3) * mult,
    crit = min(30, 5 + fxR * 3 + accR * 2),
    gs = main + off + head + chest + back + (fxR > 0 and P[fxR] or 0) + (accR > 0 and P[accR] or 0),
    level = level,
  }
  return s
end

---------------------------------------------------------------- simulation
local function bossWeights(tier)
  local t = tier - 1
  return { max(0, 60 - 12 * t), max(10, 35 - 2 * t), 5 + 6 * t, max(0, t - 2) * 4, max(0, t - 5) * 2 }
end

function TCF:AdvLog(text)
  self.advLog = self.advLog or {}
  table.insert(self.advLog, 1, text)
  if #self.advLog > 6 then table.remove(self.advLog) end
end

-- Visual events are only queued while the Adventure tab is open.
function TCF:AdvEvent(kind, a, b)
  local run = self.advRun
  if not run or not self.advWatching then return end
  if #run.events < 40 then table.insert(run.events, { kind, a, b }) end
end

function TCF:AdvReset()
  local st = self:AdvStats()
  self.advRun = { class = self.db.class, catMax = st.hp, catHP = st.hp, atkT = 0, mobT = 0, respawn = 0.6, events = {}, stats = st }
end

function TCF:AdvSpawn()
  local adv = self:CD().adv
  local run = self.advRun
  local m = self:AdvMob(adv.tier, adv.stage)
  run.mob = m
  run.mobHP = m.hp
  run.atkT, run.mobT = 0, 0
  self:AdvEvent("spawn")
end

function TCF:AdvDamageMob(dmg, kind)
  local run = self.advRun
  if not run or not run.mob or run.respawn > 0 then return end
  run.mobHP = run.mobHP - dmg
  self:AdvEvent(kind, dmg)
  if run.mobHP <= 0 then self:AdvKill() end
end

function TCF:AdvTapStrike()
  local run = self.advRun
  if run and run.mob and run.respawn <= 0 and run.class == self.db.class then
    self:AdvDamageMob(run.stats.atk * TCF.ADV.TAP_STRIKE, "tap")
  end
end

function TCF:AdvKill()
  local run, cd = self.advRun, self:CD()
  local adv = cd.adv
  local m = run.mob
  adv.kills = adv.kills + 1
  local firstClear = m.g > adv.best
  if m.boss then
    adv.bossKills = adv.bossKills + 1
    local coins = floor(10 * adv.tier ^ 1.1)
    self:AddCoins(coins)
    self:AdvLog(string.format("|cffffd100Defeated %s!|r +%d TapCoins", m.name, coins))
    if firstClear or random() < 0.25 then
      local it = self:RollItem(self:RollRarity(bossWeights(adv.tier)), true)
      if it then self:GrantItem(it, m.name .. " dropped"); self:AdvLog("Loot: " .. TCF.ItemLink(it)) end
    end
  elseif random() < 0.08 then
    self:AddCoins(1 + floor(m.g / 20))
  end
  if firstClear then adv.best = m.g end
  run.catHP = min(run.catMax, run.catHP + run.catMax * 0.3)
  if adv.auto then
    if adv.stage >= 10 then
      adv.tier, adv.stage = adv.tier + 1, 1
      run.catHP = run.catMax
      local _, zname = self:AdvZone(adv.tier)
      self:AdvLog("Onward to " .. zname .. "!")
    else
      adv.stage = adv.stage + 1
    end
  end
  self:AdvEvent("kill")
  run.mob = nil
  run.respawn = 1.2
  self:MarkDirty()
end

function TCF:AdvDefeat()
  local run, adv = self.advRun, self:CD().adv
  local tip = run.mob.boss and " |cff999999(Better gear and class levels raise Attack and Health.)|r" or ""
  local line = string.format("|cffff6060%s was too strong.|r Your cat retreats to heal.%s", run.mob.name, tip)
  if not self.advLog or self.advLog[1] ~= line then self:AdvLog(line) end
  adv.stage = max(1, adv.stage - 1)
  run.catHP = run.catMax
  run.mob = nil
  run.respawn = 2.5
  self:AdvEvent("defeat")
end

-- Advances the fight by dt seconds (called 4x a second from the core ticker).
function TCF:AdvTick(dt)
  local run = self.advRun
  if not run or run.class ~= self.db.class then self:AdvReset(); run = self.advRun end
  local st = self:AdvStats()
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
  if not run.mob then return end
  run.atkT = run.atkT + dt
  while run.mob and run.atkT >= TCF.ADV.ATTACK_INTERVAL do
    run.atkT = run.atkT - TCF.ADV.ATTACK_INTERVAL
    local crit = random() * 100 < st.crit
    self:AdvDamageMob(st.atk * (crit and 2 or 1), crit and "crit" or "hit")
  end
  if not run.mob then return end
  run.mobT = run.mobT + dt
  if run.mobT >= TCF.ADV.MOB_INTERVAL then
    run.mobT = run.mobT - TCF.ADV.MOB_INTERVAL
    run.catHP = run.catHP - run.mob.dmg
    self:AdvEvent("hurt", run.mob.dmg)
    if run.catHP <= 0 then self:AdvDefeat() end
  end
end

-- Manual stage selection: any stage up to one past the best clear.
function TCF:AdvCanGoTo(tier, stage)
  return tier >= 1 and stage >= 1 and stage <= 10 and ((tier - 1) * 10 + stage) <= self:CD().adv.best + 1
end

function TCF:AdvStep(delta)
  local adv = self:CD().adv
  local tier, stage = adv.tier, adv.stage + delta
  if stage > 10 then tier, stage = tier + 1, 1 elseif stage < 1 then tier, stage = tier - 1, 10 end
  if not self:AdvCanGoTo(tier, stage) then return end
  adv.tier, adv.stage = tier, stage
  local run = self.advRun
  if run then run.mob = nil; run.respawn = 0.4; run.catHP = run.catMax end
end
