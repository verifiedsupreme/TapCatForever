-- TapCatForever: class abilities the cat learns with TapCoins and uses in Adventure.
--
-- type: nuke (x DPS to target), aoe (x DPS to every enemy), dot (x DPS over dur),
--       heal (% max HP), shield (absorb % max HP), buff (+% damage for dur),
--       defense (-% damage taken for dur), stun (enemies can't attack for dur),
--       execute (x DPS when target is below 20%), drain (x DPS and heal % max HP),
--       passive (+% damage always), ward (-% damage taken always)
local ADDON, TCF = ...

local function A(key, name, icon, level, kind, value, cd, dur, desc)
  return { key = key, name = name, icon = icon, level = level, kind = kind, value = value, cd = cd or 0, dur = dur or 0, desc = desc }
end

-- TapCoin price to learn an ability, by required level
function TCF.AbilityCost(level)
  if level <= 1 then return 15 end
  return math.floor(10 + level * level * 0.5)
end

TCF.ABILITIES = {
  WARRIOR = {
    A("hs", "Heroic Strike", "Ability_Rogue_Ambush", 1, "nuke", 1.6, 6, 0, "A strong attack."),
    A("bs", "Battle Shout", "Ability_Warrior_BattleShout", 4, "buff", 0.15, 30, 20, "+15% damage for 20 sec."),
    A("rend", "Rend", "Ability_Gouge", 6, "dot", 1.5, 12, 9, "Bleeds the target."),
    A("tc", "Thunder Clap", "Spell_Nature_ThunderClap", 8, "aoe", 0.9, 10, 0, "Hits every enemy."),
    A("exe", "Execute", "INV_Sword_48", 24, "execute", 3.5, 5, 0, "Huge hit on an enemy below 20% health."),
    A("sw", "Shield Wall", "Ability_Warrior_ShieldWall", 28, "defense", 0.6, 60, 8, "-60% damage taken for 8 sec."),
    A("ww", "Whirlwind", "Ability_Whirlwind", 36, "aoe", 1.6, 10, 0, "Strikes every enemy."),
    A("ms", "Mortal Strike", "Ability_Warrior_SavageBlow", 40, "nuke", 2.5, 8, 0, "A vicious strike."),
    A("reck", "Recklessness", "Ability_CriticalStrike", 50, "buff", 0.5, 90, 12, "+50% damage for 12 sec."),
  },
  PALADIN = {
    A("sor", "Seal of Righteousness", "Ability_ThunderBolt", 1, "passive", 0.1, 0, 0, "+10% damage."),
    A("hl", "Holy Light", "Spell_Holy_HolyBolt", 4, "heal", 0.35, 12, 0, "Heals 35% of max health."),
    A("judge", "Judgement", "Spell_Holy_RighteousFury", 6, "nuke", 1.8, 8, 0, "Unleashes your seal."),
    A("hoj", "Hammer of Justice", "Spell_Holy_SealOfMight", 8, "stun", 0, 30, 3, "Stuns enemies for 3 sec."),
    A("dev", "Devotion Aura", "Spell_Holy_DevotionAura", 10, "ward", 0.1, 0, 0, "-10% damage taken."),
    A("cons", "Consecration", "Spell_Holy_InnerFire", 20, "aoe", 1.2, 8, 0, "Holy damage to every enemy."),
    A("ds", "Divine Shield", "Spell_Holy_DivineIntervention", 34, "defense", 1.0, 120, 6, "Immune to damage for 6 sec."),
    A("bom", "Blessing of Might", "Spell_Holy_FistOfJustice", 40, "passive", 0.15, 0, 0, "+15% damage."),
    A("hs", "Holy Shock", "Spell_Holy_SearingLight", 48, "nuke", 2.4, 10, 0, "A burst of holy energy."),
  },
  HUNTER = {
    A("as", "Arcane Shot", "Ability_ImpalingBolt", 1, "nuke", 1.5, 6, 0, "An instant arcane shot."),
    A("ss", "Serpent Sting", "Ability_Hunter_Quickshot", 4, "dot", 1.8, 15, 15, "Poisons the target."),
    A("cs", "Concussive Shot", "Spell_Frost_Stun", 8, "stun", 0, 12, 2, "Dazes enemies for 2 sec."),
    A("pet", "Call Pet", "Ability_Hunter_BeastCall", 10, "passive", 0.25, 0, 0, "Your pet fights too: +25% damage."),
    A("ms", "Multi-Shot", "Ability_UpgradeMoonGlaive", 18, "aoe", 1.2, 10, 0, "Hits every enemy."),
    A("aim", "Aimed Shot", "INV_Spear_07", 20, "nuke", 2.8, 10, 0, "A carefully aimed shot."),
    A("rf", "Rapid Fire", "Ability_Hunter_RunningShot", 26, "buff", 0.4, 120, 15, "+40% damage for 15 sec."),
    A("fd", "Feign Death", "Ability_Rogue_FeignDeath", 30, "heal", 0.25, 60, 0, "Play dead and recover 25% health."),
    A("ts", "Trueshot Aura", "Ability_TrueShot", 40, "passive", 0.1, 0, 0, "+10% damage."),
  },
  ROGUE = {
    A("ss", "Sinister Strike", "Spell_Shadow_RitualOfSacrifice", 1, "nuke", 1.5, 4, 0, "A quick strike."),
    A("evis", "Eviscerate", "Ability_Rogue_Eviscerate", 4, "nuke", 2.4, 10, 0, "A finishing move."),
    A("gouge", "Gouge", "Ability_Gouge", 6, "stun", 0, 15, 3, "Incapacitates enemies for 3 sec."),
    A("evas", "Evasion", "Spell_Shadow_ShadowWard", 8, "defense", 0.5, 60, 10, "-50% damage taken for 10 sec."),
    A("snd", "Slice and Dice", "Ability_Rogue_SliceDice", 10, "buff", 0.2, 25, 20, "+20% damage for 20 sec."),
    A("rupt", "Rupture", "Ability_Rogue_Rupture", 20, "dot", 2.5, 15, 12, "The target bleeds."),
    A("ks", "Kidney Shot", "Ability_Rogue_KidneyShot", 30, "stun", 0, 20, 4, "Stuns enemies for 4 sec."),
    A("bf", "Blade Flurry", "Ability_Warrior_PunishingBlow", 30, "aoe", 1.2, 12, 0, "Hits every enemy."),
    A("ar", "Adrenaline Rush", "Spell_Shadow_ShadowWordDominate", 40, "buff", 0.6, 120, 12, "+60% damage for 12 sec."),
  },
  PRIEST = {
    A("smite", "Smite", "Spell_Holy_HolySmite", 1, "nuke", 1.4, 4, 0, "Holy damage."),
    A("swp", "Shadow Word: Pain", "Spell_Shadow_ShadowWordPain", 4, "dot", 2.0, 18, 18, "Shadow damage over time."),
    A("pws", "Power Word: Shield", "Spell_Holy_PowerWordShield", 6, "shield", 0.3, 15, 0, "Absorbs damage (30% of max health)."),
    A("renew", "Renew", "Spell_Holy_Renew", 8, "heal", 0.25, 15, 0, "Heals 25% of max health."),
    A("mb", "Mind Blast", "Spell_Shadow_UnholyFrenzy", 10, "nuke", 2.0, 8, 0, "Blasts the target's mind."),
    A("if", "Inner Fire", "Spell_Holy_InnerFire", 12, "ward", 0.1, 0, 0, "-10% damage taken."),
    A("scream", "Psychic Scream", "Spell_Shadow_PsychicScream", 14, "stun", 0, 30, 3, "Enemies flee for 3 sec."),
    A("nova", "Holy Nova", "Spell_Holy_HolyNova", 20, "aoe", 1.0, 8, 0, "Holy damage to every enemy."),
    A("sf", "Shadowform", "Spell_Shadow_Shadowform", 40, "passive", 0.2, 0, 0, "+20% damage."),
  },
  SHAMAN = {
    A("lb", "Lightning Bolt", "Spell_Nature_Lightning", 1, "nuke", 1.6, 5, 0, "A bolt of lightning."),
    A("es", "Earth Shock", "Spell_Nature_EarthShock", 4, "nuke", 1.4, 6, 0, "Instant nature damage."),
    A("hw", "Healing Wave", "Spell_Nature_MagicImmunity", 6, "heal", 0.35, 12, 0, "Heals 35% of max health."),
    A("ls", "Lightning Shield", "Spell_Nature_LightningShield", 8, "ward", 0.1, 0, 0, "-10% damage taken."),
    A("fs", "Flame Shock", "Spell_Fire_FlameShock", 10, "dot", 1.8, 12, 12, "Fire damage over time."),
    A("st", "Searing Totem", "Spell_Fire_SearingTotem", 12, "passive", 0.15, 0, 0, "A totem joins the fight: +15% damage."),
    A("wf", "Windfury Weapon", "Spell_Nature_Cyclone", 30, "buff", 0.3, 30, 20, "+30% damage for 20 sec."),
    A("cl", "Chain Lightning", "Spell_Nature_ChainLightning", 32, "aoe", 1.5, 8, 0, "Lightning jumps between every enemy."),
    A("storm", "Stormstrike", "Spell_Holy_SealOfMight", 40, "nuke", 2.4, 10, 0, "A crackling strike."),
  },
  MAGE = {
    A("fb", "Fireball", "Spell_Fire_FlameBolt", 1, "nuke", 1.7, 5, 0, "Hurls a ball of fire."),
    A("fa", "Frost Armor", "Spell_Frost_FrostArmor02", 1, "ward", 0.1, 0, 0, "-10% damage taken."),
    A("blast", "Fire Blast", "Spell_Fire_Fireball", 6, "nuke", 1.3, 4, 0, "Instant fire damage."),
    A("nova", "Frost Nova", "Spell_Frost_FrostNova", 10, "stun", 0, 25, 4, "Freezes enemies for 4 sec."),
    A("ae", "Arcane Explosion", "Spell_Nature_WispSplode", 14, "aoe", 1.0, 5, 0, "Arcane damage to every enemy."),
    A("bliz", "Blizzard", "Spell_Frost_IceStorm", 20, "aoe", 2.0, 12, 0, "Ice shards strike every enemy."),
    A("pyro", "Pyroblast", "Spell_Fire_Fireball02", 24, "nuke", 3.5, 20, 0, "A massive fireball."),
    A("block", "Ice Block", "Spell_Frost_Frost", 30, "defense", 1.0, 120, 6, "Immune to damage for 6 sec."),
    A("barrier", "Ice Barrier", "Spell_Ice_Lament", 40, "shield", 0.4, 30, 0, "Absorbs damage (40% of max health)."),
    A("ap", "Arcane Power", "Spell_Nature_Lightning", 44, "buff", 0.3, 90, 15, "+30% damage for 15 sec."),
  },
  WARLOCK = {
    A("sb", "Shadow Bolt", "Spell_Shadow_ShadowBolt", 1, "nuke", 1.7, 5, 0, "A bolt of shadow."),
    A("immo", "Immolate", "Spell_Fire_Immolation", 1, "dot", 1.5, 15, 15, "Burns the target."),
    A("corr", "Corruption", "Spell_Shadow_AbominationExplosion", 4, "dot", 2.0, 18, 18, "Shadow damage over time."),
    A("fear", "Fear", "Spell_Shadow_Possession", 8, "stun", 0, 25, 3, "Enemies flee for 3 sec."),
    A("vw", "Summon Voidwalker", "Spell_Shadow_SummonVoidWalker", 10, "ward", 0.15, 0, 0, "A Voidwalker takes hits: -15% damage taken."),
    A("dl", "Drain Life", "Spell_Shadow_LifeDrain02", 14, "drain", 1.0, 10, 0, "Steals health (heals 15%)."),
    A("rof", "Rain of Fire", "Spell_Shadow_RainOfFire", 20, "aoe", 1.8, 12, 0, "Fire rains on every enemy."),
    A("burn", "Shadowburn", "Spell_Shadow_ScourgeBuild", 24, "execute", 3.0, 8, 0, "Big hit on an enemy below 20% health."),
    A("coil", "Death Coil", "Spell_Shadow_DeathCoil", 42, "drain", 2.0, 20, 0, "Shadow damage that heals you."),
  },
  DRUID = {
    A("wrath", "Wrath", "Spell_Nature_AbolishMagic", 1, "nuke", 1.5, 4, 0, "Nature damage."),
    A("ht", "Healing Touch", "Spell_Nature_HealingTouch", 1, "heal", 0.35, 12, 0, "Heals 35% of max health."),
    A("mf", "Moonfire", "Spell_Nature_StarFall", 4, "dot", 1.6, 12, 12, "Arcane damage over time."),
    A("roots", "Entangling Roots", "Spell_Nature_StrangleVines", 8, "stun", 0, 25, 3, "Roots enemies for 3 sec."),
    A("rejuv", "Rejuvenation", "Spell_Nature_Rejuvenation", 10, "heal", 0.2, 10, 0, "Heals 20% of max health."),
    A("cat", "Cat Form", "Ability_Druid_CatForm", 20, "passive", 0.15, 0, 0, "Become a cat (very fitting): +15% damage."),
    A("fb", "Ferocious Bite", "Ability_Druid_FerociousBite", 32, "nuke", 2.4, 10, 0, "A savage bite."),
    A("hurr", "Hurricane", "Spell_Nature_Cyclone", 40, "aoe", 2.0, 15, 0, "A storm hits every enemy."),
    A("bark", "Barkskin", "Spell_Nature_StoneClawTotem", 44, "defense", 0.3, 60, 12, "-30% damage taken for 12 sec."),
  },
}

function TCF:AbilityKnown(class, key) return self:CD(class).abilities[key] == true end

function TCF:LearnAbility(class, key)
  local ab
  for _, a in ipairs(TCF.ABILITIES[class]) do if a.key == key then ab = a end end
  if not ab or self:AbilityKnown(class, key) then return false end
  if self:CD(class).level < ab.level then return false end
  if not self:SpendCoins(TCF.AbilityCost(ab.level)) then
    self:Print(string.format("You need %d TapCoins to learn %s.", TCF.AbilityCost(ab.level), ab.name), true)
    return false
  end
  self:CD(class).abilities[key] = true
  -- a reply to the player's own click, so it shows even with chat messages turned off
  self:Print(string.format("Your %s cat learned |cffffd100%s|r!", TCF.CLASS_BY_KEY[class].name, ab.name), true)
  self:PlaySound("ach")
  self:MarkDirty(); self:RefreshAll()
  return true
end

-- How each ability looks in Adventure fights: { sprite, mode [, tint] }
-- modes: proj (fly to the target), multi (fly to every enemy), drain (fly back to the cat),
--        hit (pop on the target), each (pop on every enemy), rain (fall on every enemy),
--        stun (stars over enemies), self (rise on the cat), bubble (surround the cat)
local SPELL = {
  WARRIOR = { hs = { "slash", "hit" }, bs = { "buff", "self" }, rend = { "slash", "hit" }, tc = { "lightning", "each" },
              exe = { "slash", "hit" }, sw = { "shield", "bubble", { 1, 0.85, 0.4 } }, ww = { "slash", "each" }, ms = { "slash", "hit" }, reck = { "buff", "self" } },
  PALADIN = { hl = { "heal", "self" }, judge = { "holy", "proj" }, hoj = { "holy", "stun" }, cons = { "holy", "each" },
              ds = { "shield", "bubble", { 1, 0.9, 0.5 } }, hs = { "holy", "proj" } },
  HUNTER = { as = { "arcane", "proj" }, ss = { "poison", "proj" }, cs = { "frost", "stun" }, ms = { "arrow", "multi" },
             aim = { "arrow", "proj" }, rf = { "buff", "self" }, fd = { "heal", "self" } },
  ROGUE = { ss = { "slash", "hit" }, evis = { "slash", "hit" }, gouge = { "slash", "stun" }, evas = { "shield", "bubble", { 0.8, 0.8, 0.8 } },
            snd = { "buff", "self" }, rupt = { "slash", "hit" }, ks = { "slash", "stun" }, bf = { "slash", "each" }, ar = { "buff", "self" } },
  PRIEST = { smite = { "holy", "proj" }, swp = { "shadow", "proj" }, pws = { "shield", "bubble" }, renew = { "heal", "self" },
             mb = { "shadow", "proj" }, scream = { "shadow", "stun" }, nova = { "holy", "each" } },
  SHAMAN = { lb = { "lightning", "proj" }, es = { "rock", "proj" }, hw = { "heal", "self" }, fs = { "fire", "proj" },
             wf = { "buff", "self" }, cl = { "lightning", "multi" }, storm = { "lightning", "hit" } },
  MAGE = { fb = { "fire", "proj" }, blast = { "fire", "hit" }, nova = { "frost", "stun" }, ae = { "arcane", "each" },
           bliz = { "frost", "rain" }, pyro = { "fire", "proj" }, block = { "shield", "bubble", { 0.7, 0.9, 1 } },
           barrier = { "shield", "bubble", { 0.6, 0.85, 1 } }, ap = { "arcane", "self" } },
  WARLOCK = { sb = { "shadow", "proj" }, immo = { "fire", "hit" }, corr = { "shadow", "proj" }, fear = { "shadow", "stun" },
              dl = { "shadow", "drain" }, rof = { "fire", "rain" }, burn = { "shadow", "proj" }, coil = { "shadow", "proj" } },
  DRUID = { wrath = { "nature", "proj" }, ht = { "heal", "self" }, mf = { "moon", "rain" }, roots = { "nature", "stun" },
            rejuv = { "heal", "self" }, fb = { "slash", "hit" }, hurr = { "nature", "rain" }, bark = { "shield", "bubble", { 0.6, 0.45, 0.3 } } },
}
-- fallback by kind for anything not listed above
local BY_KIND = { nuke = { "impact", "hit" }, execute = { "slash", "hit" }, drain = { "shadow", "drain" }, dot = { "poison", "proj" },
                  aoe = { "impact", "each" }, heal = { "heal", "self" }, shield = { "shield", "bubble" }, buff = { "buff", "self" },
                  defense = { "shield", "bubble" }, stun = { "stun", "stun" } }
TCF.SPELL_FX = {
  For = function(class, key, kind)
    local c = SPELL[class]
    return (c and c[key]) or BY_KIND[kind]
  end,
  -- colour of the impact burst after a projectile lands
  TINT = { fire = { 1, 0.6, 0.2 }, frost = { 0.6, 0.9, 1 }, shadow = { 0.75, 0.45, 1 }, arcane = { 1, 0.6, 0.95 }, holy = { 1, 0.95, 0.5 },
           nature = { 0.5, 1, 0.4 }, lightning = { 0.7, 0.9, 1 }, arrow = { 1, 1, 1 }, poison = { 0.55, 1, 0.3 }, moon = { 0.8, 0.85, 1 },
           rock = { 0.85, 0.7, 0.5 }, impact = { 1, 1, 1 }, slash = { 1, 1, 1 } },
}
