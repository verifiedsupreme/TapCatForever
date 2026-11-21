-- TapCatForever: static data (classes, cosmetics, chests, achievements)
local ADDON, TCF = ...

local function c(r, g, b) return { r, g, b } end

TCF.ART_PATH = "Interface\\AddOns\\TapCatForever\\Art\\"
TCF.ICON = "Interface\\Icons\\"

---------------------------------------------------------------- rarity
TCF.RARITY = {
  { name = "Common",    color = c(1.00, 1.00, 1.00), hex = "ffffffff", price = 60,   salvage = 15 },
  { name = "Uncommon",  color = c(0.12, 1.00, 0.00), hex = "ff1eff00", price = 180,  salvage = 45 },
  { name = "Rare",      color = c(0.00, 0.44, 0.87), hex = "ff0070dd", price = 500,  salvage = 120 },
  { name = "Epic",      color = c(0.64, 0.21, 0.93), hex = "ffa335ee", price = 1500, salvage = 350 },
  { name = "Legendary", color = c(1.00, 0.50, 0.00), hex = "ffff8000", price = 5000, salvage = 1000 },
}

---------------------------------------------------------------- slots
-- "look" slots are shared by every class; the rest are saved per class.
TCF.SLOTS = {
  { key = "head",    name = "Head",      icon = "INV_Helmet_01" },
  { key = "chest",   name = "Chest",     icon = "INV_Chest_Plate16" },
  { key = "back",    name = "Back",      icon = "INV_Misc_Cape_02" },
  { key = "main",    name = "Main Hand", icon = "INV_Sword_04" },
  { key = "off",     name = "Off Hand",  icon = "INV_Shield_06" },
  { key = "effect",  name = "Effect",    icon = "Spell_Holy_MagicalSentry" },
  { key = "acc",     name = "Accessory", icon = "INV_Misc_Gift_01" },
  { key = "fur",     name = "Fur",       icon = "Ability_Druid_CatForm", look = true },
  { key = "pattern", name = "Pattern",   icon = "Ability_Druid_Rake",    look = true },
  { key = "skin",    name = "Skin",      icon = "Ability_Mount_WhiteTiger", look = true },
}
TCF.SLOT_BY_KEY = {}
for _, s in ipairs(TCF.SLOTS) do TCF.SLOT_BY_KEY[s.key] = s end

---------------------------------------------------------------- effect behaviour per art
TCF.FX = {
  fx_aura      = { layer = "back",  anim = "pulse" },
  fx_rays      = { layer = "back",  anim = "spin" },
  fx_runes     = { layer = "back",  anim = "spin" },
  fx_wisps     = { layer = "back",  anim = "spinslow" },
  fx_flames    = { layer = "back",  anim = "flicker" },
  fx_sparkles  = { layer = "front", anim = "twinkle" },
  fx_leaves    = { layer = "front", anim = "spinslow" },
  fx_lightning = { layer = "front", anim = "flicker" },
  fx_snow      = { layer = "front", anim = "float" },
  fx_hearts    = { layer = "front", anim = "float" },
  fx_notes     = { layer = "front", anim = "float" },
  fx_bubbles   = { layer = "front", anim = "float" },
  fx_coins     = { layer = "front", anim = "float" },
}

---------------------------------------------------------------- classes
-- mats: five material tiers (Common..Legendary): name, primary colour, secondary colour
-- gear: { slot, art, name, icon }
-- fx:   { art, name, rarity, colour }
TCF.CLASSES = {
  {
    key = "WARRIOR", name = "Warrior", color = c(0.78, 0.61, 0.43), fur = "fur_ginger",
    mats = {
      { "Rusty",       c(0.62, 0.56, 0.52), c(0.50, 0.34, 0.20) },
      { "Bronze",      c(0.88, 0.62, 0.36), c(0.45, 0.28, 0.14) },
      { "Cobalt",      c(0.45, 0.62, 1.00), c(0.88, 0.88, 0.96) },
      { "Bloodforged", c(0.78, 0.16, 0.16), c(0.28, 0.22, 0.28) },
      { "Titanforged", c(1.00, 0.84, 0.36), c(0.96, 0.96, 1.00) },
    },
    gear = {
      { "head",  "head_greathelm",  "Greathelm",       "INV_Helmet_01" },
      { "head",  "head_hornhelm",   "Horned Helm",     "INV_Helmet_08" },
      { "chest", "chest_plate",     "Breastplate",     "INV_Chest_Plate16" },
      { "chest", "chest_spiked",    "Spiked Harness",  "INV_Chest_Plate06" },
      { "chest", "chest_mail",      "Chainmail",       "INV_Chest_Chain" },
      { "main",  "wpn_sword",       "Longsword",       "INV_Sword_04" },
      { "main",  "wpn_greatsword",  "Greatsword",      "INV_Sword_39" },
      { "main",  "wpn_axe",         "Battleaxe",       "INV_Axe_09" },
      { "off",   "off_roundshield", "Round Shield",    "INV_Shield_06" },
      { "off",   "off_sword",       "Parrying Blade",  "INV_Sword_05" },
      { "back",  "back_cape",       "War Cloak",       "INV_Misc_Cape_02" },
    },
    fx = {
      { "fx_sparkles", "Victory Sparks", 3, c(1.00, 0.80, 0.30) },
      { "fx_flames",   "Battle Rage",    4, c(1.00, 0.25, 0.10) },
      { "fx_aura",     "Avatar",         5, c(1.00, 0.55, 0.15) },
    },
  },
  {
    key = "PALADIN", name = "Paladin", color = c(0.96, 0.55, 0.73), fur = "fur_cream",
    mats = {
      { "Squire's",    c(0.75, 0.75, 0.78), c(0.40, 0.55, 0.85) },
      { "Crusader's",  c(0.92, 0.92, 0.96), c(0.85, 0.20, 0.20) },
      { "Lawbringer",  c(1.00, 0.82, 0.35), c(0.30, 0.50, 1.00) },
      { "Judgement",   c(0.95, 0.40, 0.30), c(1.00, 0.85, 0.40) },
      { "Ashbringer",  c(1.00, 0.95, 0.70), c(1.00, 0.70, 0.20) },
    },
    gear = {
      { "head",  "head_winghelm",   "Winged Helm",     "INV_Helmet_05" },
      { "head",  "head_greathelm",  "Crusader Helm",   "INV_Helmet_03" },
      { "chest", "chest_plate",     "Breastplate",     "INV_Chest_Plate03" },
      { "chest", "chest_tabard",    "Tabard",          "INV_Shirt_GuildTabard_01" },
      { "main",  "wpn_hammer",      "Warhammer",       "INV_Hammer_10" },
      { "main",  "wpn_mace",        "Holy Mace",       "INV_Mace_01" },
      { "main",  "wpn_greatsword",  "Blessed Blade",   "INV_Sword_39" },
      { "off",   "off_kiteshield",  "Kite Shield",     "INV_Shield_09" },
      { "off",   "off_tome",        "Libram",          "INV_Misc_Book_09" },
      { "back",  "back_cape",       "Crusader Cape",   "INV_Misc_Cape_06" },
      { "back",  "back_angelwings", "Wings of Light",  "Spell_Holy_PowerWordShield" },
    },
    fx = {
      { "fx_aura",     "Devotion Aura",     3, c(1.00, 0.85, 0.40) },
      { "fx_sparkles", "Blessing of Kings", 3, c(1.00, 0.95, 0.60) },
      { "fx_rays",     "Divine Shield",     4, c(1.00, 0.90, 0.50) },
      { "fx_runes",    "Consecration",      5, c(1.00, 0.75, 0.25) },
    },
  },
  {
    key = "HUNTER", name = "Hunter", color = c(0.67, 0.83, 0.45), fur = "fur_peach",
    mats = {
      { "Wild",          c(0.50, 0.62, 0.35), c(0.55, 0.40, 0.25) },
      { "Trailblazer",   c(0.35, 0.70, 0.35), c(0.95, 0.45, 0.30) },
      { "Beaststalker",  c(0.65, 0.50, 0.30), c(0.40, 0.75, 0.95) },
      { "Giantstalker",  c(0.30, 0.55, 0.85), c(0.95, 0.85, 0.40) },
      { "Dragonstalker", c(0.90, 0.30, 0.20), c(1.00, 0.80, 0.30) },
    },
    gear = {
      { "head",  "head_featcap",    "Feathered Cap",   "INV_Helmet_04" },
      { "head",  "head_hood",       "Ranger Hood",     "INV_Helmet_29" },
      { "chest", "chest_furmantle", "Fur Mantle",      "INV_Chest_Leather_09" },
      { "chest", "chest_mail",      "Mail Hauberk",    "INV_Chest_Chain_05" },
      { "chest", "chest_leather",   "Leather Vest",    "INV_Chest_Leather_01" },
      { "main",  "wpn_bow",         "Longbow",         "INV_Weapon_Bow_07" },
      { "main",  "wpn_rifle",       "Rifle",           "INV_Weapon_Rifle_01" },
      { "main",  "wpn_spear",       "Spear",           "INV_Spear_04" },
      { "off",   "off_dagger",      "Skinning Knife",  "INV_Weapon_ShortBlade_05" },
      { "back",  "back_quiver",     "Quiver",          "INV_Misc_Quiver_02" },
      { "back",  "back_cape",       "Ranger Cloak",    "INV_Misc_Cape_10" },
    },
    fx = {
      { "fx_leaves",   "Aspect of the Wild", 3, c(0.50, 0.90, 0.40) },
      { "fx_sparkles", "Hunter's Mark",      3, c(1.00, 0.35, 0.30) },
      { "fx_aura",     "Aspect of the Hawk", 4, c(1.00, 0.60, 0.20) },
      { "fx_runes",    "Eagle Eye",          5, c(0.95, 0.85, 0.35) },
    },
  },
  {
    key = "ROGUE", name = "Rogue", color = c(1.00, 0.96, 0.41), fur = "fur_midnight",
    mats = {
      { "Ragged",       c(0.48, 0.42, 0.36), c(0.62, 0.62, 0.66) },
      { "Duskwood",     c(0.30, 0.42, 0.30), c(0.75, 0.75, 0.80) },
      { "Nightslayer",  c(0.28, 0.26, 0.42), c(0.85, 0.85, 0.95) },
      { "Bloodfang",    c(0.65, 0.12, 0.15), c(0.20, 0.18, 0.22) },
      { "Shadowmourne", c(0.30, 0.20, 0.55), c(0.55, 1.00, 0.85) },
    },
    gear = {
      { "head",  "head_hood",      "Hood",           "INV_Helmet_29" },
      { "head",  "head_mask",      "Bandit Mask",    "INV_Misc_Bandana_01" },
      { "chest", "chest_leather",  "Leather Jerkin", "INV_Chest_Leather_07" },
      { "chest", "chest_mail",     "Brigandine",     "INV_Chest_Chain_03" },
      { "main",  "wpn_dagger",     "Dagger",         "INV_Weapon_ShortBlade_05" },
      { "main",  "wpn_sword",      "Short Sword",    "INV_Sword_05" },
      { "main",  "wpn_claws",      "Fist Blades",    "INV_Gauntlets_04" },
      { "off",   "off_dagger",     "Offhand Dagger", "INV_Weapon_ShortBlade_01" },
      { "off",   "off_sword",      "Offhand Sword",  "INV_Sword_07" },
      { "back",  "back_cape",      "Shadow Cloak",   "INV_Misc_Cape_18" },
    },
    fx = {
      { "fx_wisps",    "Stealth Mist",     3, c(0.60, 0.60, 0.75) },
      { "fx_coins",    "Ill-Gotten Gains", 4, c(1.00, 0.85, 0.30) },
      { "fx_sparkles", "Blade Flurry",     4, c(0.80, 0.95, 1.00) },
      { "fx_aura",     "Vanish",           5, c(0.45, 0.30, 0.80) },
    },
  },
  {
    key = "PRIEST", name = "Priest", color = c(1.00, 1.00, 1.00), fur = "fur_snow",
    mats = {
      { "Novice's",      c(0.85, 0.82, 0.75), c(0.55, 0.45, 0.35) },
      { "Devout",        c(0.95, 0.95, 1.00), c(0.40, 0.60, 0.95) },
      { "Prophecy",      c(1.00, 1.00, 1.00), c(1.00, 0.82, 0.35) },
      { "Transcendence", c(1.00, 0.95, 0.75), c(0.70, 0.85, 1.00) },
      { "Benediction",   c(0.55, 0.35, 0.85), c(1.00, 0.85, 0.35) },
    },
    gear = {
      { "head",  "head_halo",      "Halo",           "Spell_Holy_InnerFire" },
      { "head",  "head_mitre",     "Mitre",          "INV_Helmet_16" },
      { "head",  "head_hood",      "Cowl",           "INV_Helmet_29" },
      { "chest", "chest_vestment", "Vestments",      "INV_Chest_Cloth_17" },
      { "chest", "chest_robe",     "Robes",          "INV_Chest_Cloth_05" },
      { "main",  "wpn_wand",       "Wand",           "INV_Wand_01" },
      { "main",  "wpn_staff",      "Staff",          "INV_Staff_13" },
      { "main",  "wpn_mace",       "Holy Mace",      "INV_Mace_01" },
      { "off",   "off_lantern",    "Holy Lantern",   "Spell_Holy_HolyBolt" },
      { "off",   "off_tome",       "Prayer Book",    "INV_Misc_Book_07" },
      { "back",  "back_angelwings","Seraph Wings",   "Spell_Holy_PowerWordShield" },
    },
    fx = {
      { "fx_sparkles", "Blessed Glimmer",   3, c(1.00, 0.95, 0.70) },
      { "fx_aura",     "Power Word: Shield", 3, c(0.70, 0.85, 1.00) },
      { "fx_rays",     "Holy Radiance",     4, c(1.00, 0.90, 0.50) },
      { "fx_wisps",    "Shadowform",        5, c(0.50, 0.25, 0.85) },
    },
  },
  {
    key = "SHAMAN", name = "Shaman", color = c(0.00, 0.44, 0.87), fur = "fur_bluesmoke",
    mats = {
      { "Tribal",      c(0.62, 0.45, 0.28), c(0.85, 0.75, 0.55) },
      { "Earthfury",   c(0.55, 0.40, 0.25), c(0.40, 0.75, 0.35) },
      { "Ten Storms",  c(0.30, 0.55, 0.95), c(0.90, 0.90, 0.95) },
      { "Stormcaller", c(0.25, 0.35, 0.75), c(0.55, 0.90, 1.00) },
      { "Doomhammer",  c(0.35, 0.30, 0.30), c(1.00, 0.60, 0.20) },
    },
    gear = {
      { "head",  "head_headdress",  "Feather Headdress", "INV_Helmet_22" },
      { "head",  "head_hornhelm",   "Horned Helm",       "INV_Helmet_08" },
      { "head",  "head_hood",       "Spirit Hood",       "INV_Helmet_29" },
      { "chest", "chest_furmantle", "Fur Mantle",        "INV_Chest_Leather_09" },
      { "chest", "chest_mail",      "Mail Hauberk",      "INV_Chest_Chain_05" },
      { "main",  "wpn_totem",       "Totem Staff",       "Spell_Nature_StoneSkinTotem" },
      { "main",  "wpn_hammer",      "Earthshaker",       "INV_Hammer_09" },
      { "main",  "wpn_axe",         "Tribal Axe",        "INV_Axe_02" },
      { "off",   "off_totem",       "Totem",             "Spell_Nature_StoneClawTotem" },
      { "off",   "off_roundshield", "Tribal Shield",     "INV_Shield_02" },
      { "back",  "back_totempack",  "Totem Pack",        "Spell_Nature_InvisibilityTotem" },
    },
    fx = {
      { "fx_bubbles",   "Water Shield",     3, c(0.40, 0.75, 1.00) },
      { "fx_flames",    "Searing Totem",    3, c(1.00, 0.50, 0.15) },
      { "fx_lightning", "Chain Lightning",  4, c(0.55, 0.80, 1.00) },
      { "fx_runes",     "Ancestral Circle", 5, c(0.35, 0.85, 1.00) },
    },
  },
  {
    key = "MAGE", name = "Mage", color = c(0.25, 0.78, 0.92), fur = "fur_silver",
    mats = {
      { "Apprentice's", c(0.55, 0.60, 0.80), c(0.85, 0.80, 0.60) },
      { "Arcanist",     c(0.30, 0.45, 0.95), c(1.00, 0.82, 0.35) },
      { "Frostweave",   c(0.60, 0.90, 1.00), c(0.95, 0.98, 1.00) },
      { "Spellfire",    c(0.85, 0.25, 0.15), c(1.00, 0.75, 0.25) },
      { "Archmage's",   c(0.55, 0.30, 0.90), c(1.00, 0.85, 0.40) },
    },
    gear = {
      { "head",  "head_wizard",       "Pointed Hat",     "INV_Helmet_28" },
      { "head",  "head_circlet",      "Circlet",         "INV_Crown_02" },
      { "head",  "head_hood",         "Hood",            "INV_Helmet_29" },
      { "chest", "chest_robe",        "Robes",           "INV_Chest_Cloth_08" },
      { "chest", "chest_vestment",    "Spellweave",      "INV_Chest_Cloth_17" },
      { "main",  "wpn_staff",         "Staff",           "INV_Staff_13" },
      { "main",  "wpn_crystalstaff",  "Crystal Staff",   "INV_Staff_08" },
      { "main",  "wpn_wand",          "Wand",            "INV_Wand_07" },
      { "off",   "off_tome",          "Spellbook",       "INV_Misc_Book_09" },
      { "off",   "off_orb",           "Orb",             "INV_Misc_Orb_01" },
      { "back",  "back_cape",         "Mantle Cloak",    "INV_Misc_Cape_16" },
    },
    fx = {
      { "fx_sparkles", "Arcane Glitter", 3, c(0.75, 0.55, 1.00) },
      { "fx_snow",     "Frost Nova",     4, c(0.65, 0.90, 1.00) },
      { "fx_flames",   "Pyroblast",      4, c(1.00, 0.45, 0.15) },
      { "fx_runes",    "Arcane Circle",  5, c(0.75, 0.45, 1.00) },
    },
  },
  {
    key = "WARLOCK", name = "Warlock", color = c(0.53, 0.53, 0.93), fur = "fur_shadow",
    mats = {
      { "Cultist",     c(0.45, 0.35, 0.40), c(0.60, 0.20, 0.20) },
      { "Dreadweave",  c(0.30, 0.25, 0.45), c(0.75, 0.30, 0.95) },
      { "Felheart",    c(0.40, 0.70, 0.25), c(0.25, 0.20, 0.25) },
      { "Nemesis",     c(0.75, 0.15, 0.25), c(0.20, 0.15, 0.20) },
      { "Netherflame", c(0.55, 0.20, 0.85), c(0.45, 1.00, 0.35) },
    },
    gear = {
      { "head",  "head_horns",     "Demon Horns",   "Spell_Shadow_ShadowWordDominate" },
      { "head",  "head_hood",      "Dark Hood",     "INV_Helmet_29" },
      { "head",  "head_skull",     "Skull Cap",     "INV_Misc_Bone_HumanSkull_01" },
      { "chest", "chest_robe",     "Robes",         "INV_Chest_Cloth_14" },
      { "chest", "chest_spiked",   "Spiked Mantle", "INV_Chest_Cloth_43" },
      { "main",  "wpn_scythe",     "Scythe",        "INV_Weapon_Halberd_02" },
      { "main",  "wpn_staff",      "Staff",         "INV_Staff_08" },
      { "main",  "wpn_wand",       "Wand",          "INV_Wand_04" },
      { "off",   "off_skull",      "Skull",         "INV_Misc_Bone_HumanSkull_01" },
      { "off",   "off_tome",       "Grimoire",      "INV_Misc_Book_06" },
      { "back",  "back_batwings",  "Shadow Wings",  "Spell_Shadow_GatherShadows" },
      { "back",  "back_cape",      "Cultist Cloak", "INV_Misc_Cape_20" },
    },
    fx = {
      { "fx_wisps",  "Fel Wisps",         3, c(0.45, 1.00, 0.30) },
      { "fx_flames", "Hellfire",          4, c(0.40, 1.00, 0.25) },
      { "fx_runes",  "Summoning Circle",  4, c(0.70, 0.35, 1.00) },
      { "fx_aura",   "Shadowflame",       5, c(0.60, 0.15, 0.90) },
    },
  },
  {
    key = "DRUID", name = "Druid", color = c(1.00, 0.49, 0.04), fur = "fur_chocolate",
    mats = {
      { "Thornwood",  c(0.55, 0.40, 0.25), c(0.45, 0.65, 0.30) },
      { "Wildheart",  c(0.50, 0.75, 0.35), c(0.90, 0.55, 0.65) },
      { "Cenarion",   c(0.65, 0.45, 0.25), c(0.40, 0.90, 0.40) },
      { "Stormrage",  c(0.35, 0.55, 0.30), c(0.60, 0.75, 1.00) },
      { "Elune's",    c(0.75, 0.80, 1.00), c(0.85, 0.60, 1.00) },
    },
    gear = {
      { "head",  "head_antlers",     "Antlers",        "Ability_Druid_TravelForm" },
      { "head",  "head_flowers",     "Flower Crown",   "INV_Misc_Flower_02" },
      { "head",  "head_hood",        "Leaf Hood",      "INV_Helmet_29" },
      { "chest", "chest_leaves",     "Leaf Mantle",    "Spell_Nature_Thorns" },
      { "chest", "chest_leather",    "Hide Vest",      "INV_Chest_Leather_06" },
      { "main",  "wpn_staff",        "Staff",          "INV_Staff_06" },
      { "main",  "wpn_crystalstaff", "Moonstaff",      "INV_Staff_08" },
      { "main",  "wpn_claws",        "Feral Claws",    "Ability_Druid_Rake" },
      { "off",   "off_orb",          "Moon Orb",       "Spell_Nature_StarFall" },
      { "back",  "back_vines",       "Living Vines",   "Spell_Nature_StrangleVines" },
      { "back",  "back_cape",        "Barkskin Cloak", "INV_Misc_Cape_14" },
    },
    fx = {
      { "fx_leaves",   "Swirling Leaves", 3, c(0.45, 0.90, 0.35) },
      { "fx_sparkles", "Moonfire Glints", 3, c(0.75, 0.70, 1.00) },
      { "fx_aura",     "Tranquility",     4, c(0.45, 1.00, 0.55) },
      { "fx_runes",    "Starfall",        5, c(0.55, 0.70, 1.00) },
    },
  },
}
TCF.CLASS_BY_KEY = {}
for i, cl in ipairs(TCF.CLASSES) do cl.index = i; TCF.CLASS_BY_KEY[cl.key] = cl end

---------------------------------------------------------------- universal cosmetics
-- { id, slot, art, name, rarity, c1, c2, icon, extra }
local U = {
  -- fur colours
  { "fur_snow",      "fur", "cat_fur", "Snow White",    1, c(1.00, 1.00, 1.00), nil, "Ability_Druid_CatForm" },
  { "fur_ginger",    "fur", "cat_fur", "Ginger",        1, c(1.00, 0.72, 0.42), nil, "Ability_Druid_CatForm" },
  { "fur_cream",     "fur", "cat_fur", "Cream",         1, c(1.00, 0.92, 0.78), nil, "Ability_Druid_CatForm" },
  { "fur_silver",    "fur", "cat_fur", "Silver",        1, c(0.80, 0.82, 0.88), nil, "Ability_Druid_CatForm" },
  { "fur_peach",     "fur", "cat_fur", "Peach",         1, c(1.00, 0.82, 0.70), nil, "Ability_Druid_CatForm" },
  { "fur_midnight",  "fur", "cat_fur", "Midnight",      2, c(0.32, 0.32, 0.38), nil, "Ability_Druid_CatForm" },
  { "fur_chocolate", "fur", "cat_fur", "Chocolate",     2, c(0.62, 0.42, 0.30), nil, "Ability_Druid_CatForm" },
  { "fur_bluesmoke", "fur", "cat_fur", "Blue Smoke",    2, c(0.62, 0.70, 0.82), nil, "Ability_Druid_CatForm" },
  { "fur_lilac",     "fur", "cat_fur", "Lilac",         3, c(0.84, 0.74, 0.92), nil, "Ability_Druid_CatForm" },
  { "fur_frost",     "fur", "cat_fur", "Frostfur",      3, c(0.66, 0.90, 1.00), nil, "Spell_Frost_FrostArmor02" },
  { "fur_ember",     "fur", "cat_fur", "Ember",         3, c(1.00, 0.48, 0.32), nil, "Spell_Fire_Fire" },
  { "fur_shadow",    "fur", "cat_fur", "Shadow",        3, c(0.24, 0.22, 0.30), nil, "Spell_Shadow_Shadowform" },
  { "fur_fel",       "fur", "cat_fur", "Fel-Touched",   4, c(0.55, 1.00, 0.45), nil, "Spell_Shadow_SummonFelHunter" },
  { "fur_arcane",    "fur", "cat_fur", "Arcane",        4, c(0.72, 0.56, 1.00), nil, "Spell_Holy_MagicalSentry" },
  { "fur_golden",    "fur", "cat_fur", "Golden",        4, c(1.00, 0.86, 0.36), nil, "INV_Misc_Coin_01" },
  { "fur_spectral",  "fur", "cat_fur", "Spectral",      5, c(0.60, 1.00, 0.95), nil, "Spell_Shadow_Possession", { alpha = 0.6 } },
  { "fur_prismatic", "fur", "cat_fur", "Prismatic",     5, c(1.00, 1.00, 1.00), nil, "INV_Misc_Gem_Pearl_04", { rainbow = true } },

  -- fur patterns
  { "pat_tabby",       "pattern", "pat_tabby",   "Brown Tabby",     1, c(0.55, 0.38, 0.24), nil, "Ability_Druid_Rake" },
  { "pat_tabby_g",     "pattern", "pat_tabby",   "Ginger Tabby",    2, c(0.90, 0.50, 0.20), nil, "Ability_Druid_Rake" },
  { "pat_tabby_s",     "pattern", "pat_tabby",   "Silver Tabby",    2, c(0.45, 0.46, 0.52), nil, "Ability_Druid_Rake" },
  { "pat_tuxedo",      "pattern", "pat_tuxedo",  "Tuxedo",          2, c(1.00, 1.00, 1.00), nil, "INV_Shirt_White_01" },
  { "pat_blaze",       "pattern", "pat_socks",   "Star Blaze",      2, c(1.00, 1.00, 1.00), nil, "Spell_Holy_SealOfMight" },
  { "pat_calico",      "pattern", "pat_calico",  "Calico",          3, c(0.95, 0.58, 0.25), c(0.22, 0.20, 0.22), "Ability_Druid_Rake" },
  { "pat_points",      "pattern", "pat_points",  "Siamese Points",  3, c(0.42, 0.32, 0.26), nil, "Ability_Druid_Rake" },
  { "pat_leopard",     "pattern", "pat_leopard", "Leopard Spots",   3, c(0.30, 0.20, 0.12), nil, "Ability_Mount_JungleTiger" },
  { "pat_snowleopard", "pattern", "pat_leopard", "Snow Leopard",    4, c(0.45, 0.50, 0.58), nil, "Ability_Mount_WhiteTiger" },
  { "pat_fel",         "pattern", "pat_leopard", "Fel Spots",       4, c(0.40, 0.95, 0.30), nil, "Spell_Shadow_SummonFelHunter" },
  { "pat_void",        "pattern", "pat_points",  "Void Points",     5, c(0.50, 0.25, 0.95), nil, "Spell_Shadow_Shadowform" },

  -- accessories
  { "acc_shades",      "acc", "acc_shades",    "Cool Shades",          1, c(0.22, 0.22, 0.26), c(1, 1, 1), "INV_Helmet_47" },
  { "acc_shades_pink", "acc", "acc_shades",    "Pink Shades",          2, c(1.00, 0.45, 0.70), c(1, 1, 1), "INV_Helmet_47" },
  { "acc_shades_gold", "acc", "acc_shades",    "Goblin Aviators",      4, c(1.00, 0.80, 0.25), c(1, 1, 0.8), "INV_Gizmo_GoblinGogglesMod" },
  { "acc_monocle",     "acc", "acc_monocle",   "Brass Monocle",        2, c(0.85, 0.65, 0.35), c(0.85, 0.65, 0.35), "INV_Misc_Spyglass_02" },
  { "acc_monocle_g",   "acc", "acc_monocle",   "Gnomish Monocle",      3, c(1.00, 0.85, 0.35), c(0.70, 0.90, 1.00), "INV_Misc_Spyglass_03" },
  { "acc_scarf_red",   "acc", "acc_scarf",     "Red Scarf",            1, c(0.85, 0.20, 0.20), c(1, 1, 1), "INV_Misc_Cape_02" },
  { "acc_scarf_blue",  "acc", "acc_scarf",     "Blue Scarf",           1, c(0.25, 0.45, 0.90), c(1, 1, 1), "INV_Misc_Cape_16" },
  { "acc_scarf_green", "acc", "acc_scarf",     "Green Scarf",          2, c(0.30, 0.75, 0.35), c(1, 0.9, 0.5), "INV_Misc_Cape_14" },
  { "acc_scarf_frost", "acc", "acc_scarf",     "Winter Veil Scarf",    3, c(0.95, 0.95, 1.00), c(0.85, 0.20, 0.20), "INV_Holiday_Christmas_Present_01" },
  { "acc_bowtie",      "acc", "acc_bowtie",    "Black Bow Tie",        1, c(0.22, 0.22, 0.26), c(0.3, 0.3, 0.35), "INV_Misc_Ribbon_01" },
  { "acc_bowtie_red",  "acc", "acc_bowtie",    "Red Bow Tie",          2, c(0.85, 0.20, 0.25), c(1, 0.8, 0.3), "INV_Misc_Ribbon_01" },
  { "acc_bowtie_gold", "acc", "acc_bowtie",    "Golden Bow Tie",       3, c(1.00, 0.82, 0.30), c(1, 1, 1), "INV_Misc_Ribbon_01" },
  { "acc_bell",        "acc", "acc_bell",      "Bell Collar",          1, c(0.85, 0.20, 0.25), c(1.0, 0.85, 0.3), "INV_Misc_Bell_01" },
  { "acc_bell_s",      "acc", "acc_bell",      "Silver Bell Collar",   2, c(0.30, 0.45, 0.90), c(0.9, 0.9, 1.0), "INV_Misc_Bell_01" },
  { "acc_eyepatch",    "acc", "acc_eyepatch",  "Pirate Eyepatch",      2, c(0.18, 0.16, 0.20), c(0.3, 0.25, 0.2), "INV_Misc_Bandana_01" },
  { "acc_flower",      "acc", "acc_flower",    "Pink Blossom",         1, c(1.00, 0.55, 0.75), c(1, 0.9, 0.4), "INV_Misc_Flower_01" },
  { "acc_peacebloom",  "acc", "acc_flower",    "Peacebloom",           2, c(1.00, 1.00, 0.85), c(1, 0.85, 0.3), "INV_Misc_Flower_02" },
  { "acc_mageroyal",   "acc", "acc_flower",    "Mageroyal",            3, c(0.75, 0.45, 1.00), c(1, 1, 0.6), "INV_Jewelry_Talisman_03" },
  { "acc_blacklotus",  "acc", "acc_flower",    "Black Lotus",          5, c(0.25, 0.15, 0.35), c(0.85, 0.30, 1.0), "INV_Misc_Herb_BlackLotus" },
  { "acc_mustache",    "acc", "acc_mustache",  "Dashing Mustache",     2, c(0.40, 0.28, 0.20), nil, "INV_Misc_Comb_01" },
  { "acc_mustache_d",  "acc", "acc_mustache",  "Dwarven Mustache",     3, c(0.85, 0.40, 0.18), nil, "INV_Misc_Comb_02" },
  { "acc_medal_b",     "acc", "acc_medal",     "Bronze Medal",         2, c(0.80, 0.55, 0.30), c(0.30, 0.45, 0.90), "INV_Jewelry_Talisman_07" },
  { "acc_medal_s",     "acc", "acc_medal",     "Silver Medal",         3, c(0.85, 0.88, 0.95), c(0.30, 0.45, 0.90), "INV_Jewelry_Talisman_07" },
  { "acc_medal_g",     "acc", "acc_medal",     "Gold Medal",           4, c(1.00, 0.82, 0.30), c(0.85, 0.20, 0.25), "INV_Jewelry_Talisman_07" },
  { "acc_bandolier",   "acc", "acc_bandolier", "Bandolier",            1, c(0.55, 0.38, 0.22), c(1.0, 0.85, 0.4), "INV_Ammo_Bullet_01" },
  { "acc_bandolier_e", "acc", "acc_bandolier", "Engineer's Bandolier", 2, c(0.35, 0.30, 0.28), c(0.4, 0.9, 1.0), "INV_Ammo_Bullet_02" },

  -- universal heads / weapons
  { "head_partyhat",   "head", "head_partyhat", "Party Hat",              1, c(1.00, 0.45, 0.70), c(1, 1, 1), "INV_Misc_Gift_02" },
  { "head_partyhat_b", "head", "head_partyhat", "Blue Party Hat",         2, c(0.35, 0.60, 1.00), c(1, 1, 0.6), "INV_Misc_Gift_03" },
  { "head_partyhat_g", "head", "head_partyhat", "Gilded Party Hat",       3, c(1.00, 0.82, 0.30), c(1, 0.4, 0.7), "INV_Misc_Gift_05" },
  { "head_tophat",     "head", "head_tophat",   "Top Hat",                2, c(0.24, 0.22, 0.26), c(0.85, 0.20, 0.25), "INV_Helmet_06" },
  { "head_tophat_p",   "head", "head_tophat",   "Dapper Purple Top Hat",  3, c(0.45, 0.25, 0.65), c(1, 0.82, 0.3), "INV_Helmet_06" },
  { "head_skull_u",    "head", "head_skull",    "Hallow's End Skull",     3, c(0.95, 0.92, 0.82), c(0.2, 0.2, 0.2), "INV_Misc_Bone_HumanSkull_01" },
  { "head_crown",      "head", "head_crown",    "King's Crown",           4, c(1.00, 0.82, 0.30), c(0.90, 0.20, 0.30), "INV_Crown_01" },
  { "head_crown_ice",  "head", "head_crown",    "Frozen Throne Crown",    5, c(0.65, 0.85, 1.00), c(0.40, 0.70, 1.00), "INV_Crown_02" },
  { "wpn_fishpole",    "main", "wpn_fishpole",  "Fishing Pole",           1, c(0.60, 0.42, 0.25), c(1, 1, 1), "INV_Fishingpole_02" },
  { "wpn_fishpole_a",  "main", "wpn_fishpole",  "Arcanite Fishing Pole",  4, c(0.45, 0.85, 1.00), c(1, 0.85, 0.3), "INV_Fishingpole_01" },
  { "wpn_torch",       "main", "wpn_torch",     "Torch",                  1, c(1.00, 0.70, 0.25), c(0.55, 0.40, 0.25), "INV_Torch_Lit" },
  { "wpn_torch_e",     "main", "wpn_torch",     "Everburning Torch",      3, c(0.50, 0.85, 1.00), c(0.35, 0.30, 0.40), "INV_Torch_Lit" },

  -- universal effects
  { "fx_hearts",       "effect", "fx_hearts",   "Lovely Hearts",     2, c(1.00, 0.45, 0.65), nil, "INV_ValentinesCandy" },
  { "fx_bubbles",      "effect", "fx_bubbles",  "Bubbles",           2, c(0.65, 0.90, 1.00), nil, "Spell_Frost_SummonWaterElemental" },
  { "fx_dust",         "effect", "fx_sparkles", "Fairy Dust",        2, c(1.00, 0.75, 1.00), nil, "INV_Misc_Dust_02" },
  { "fx_notes",        "effect", "fx_notes",    "Bongo Beat",        3, c(1.00, 0.90, 0.50), nil, "INV_Misc_Drum_01" },
  { "fx_snow_u",       "effect", "fx_snow",     "Winter Veil Snow",  3, c(1.00, 1.00, 1.00), nil, "Spell_Frost_FrostShock" },
  { "fx_coins_u",      "effect", "fx_coins",    "Jackpot",           4, c(1.00, 0.85, 0.30), nil, "INV_Misc_Coin_02" },
}

-- Achievement-only rewards (never in shops or chests)
local ACH_ITEMS = {
  { "ach_crown",   "head",   "head_crown",       "Crown of the Tapmaster",      5, c(1.00, 0.70, 0.20), c(0.35, 1.00, 0.85), "INV_Crown_01" },
  { "ach_glow",    "effect", "fx_aura",          "Veteran's Glow",              4, c(1.00, 0.90, 0.60), nil, "Spell_Holy_SurgeOfLight" },
  { "ach_tophat",  "head",   "head_tophat",      "Collector's Top Hat",         4, c(0.20, 0.55, 0.45), c(1.00, 0.82, 0.30), "INV_Helmet_06" },
  { "ach_prism",   "effect", "fx_sparkles",      "Prismatic Sparkles",          5, c(1, 1, 1), nil, "INV_Misc_Gem_Pearl_04", { rainbow = true } },
  { "ach_medal",   "acc",    "acc_medal",        "Medal of Devotion",           3, c(0.70, 0.40, 1.00), c(1.00, 0.85, 0.30), "INV_Jewelry_Talisman_07" },
  { "ach_wings",   "back",   "back_angelwings",  "Wings of the Eternal Tapper", 5, c(1.00, 0.85, 0.45), c(1.00, 1.00, 1.00), "Spell_Holy_PowerWordShield" },
  { "ach_fur",     "fur",    "cat_fur",          "Starlight",                   4, c(0.55, 0.60, 1.00), nil, "Spell_Nature_StarFall" },
  { "ach_bongo",   "effect", "fx_notes",         "Drum Solo",                   4, c(0.55, 1.00, 0.70), nil, "INV_Misc_Drum_01", },
  { "ach_party",   "head",   "head_partyhat",    "Birthday Party Hat",          3, c(0.70, 0.40, 1.00), c(1.00, 0.95, 0.40), "INV_Misc_Gift_04" },
  { "ach_shades",  "acc",    "acc_shades",       "Speedrunner Shades",          4, c(1.00, 0.30, 0.25), c(1.00, 1.00, 0.60), "INV_Helmet_47" },
}

-- Profession-only cosmetics (crafted, never sold or dropped)
local CRAFT = {
  { "craft_copper_circlet",   "head",   "head_circlet",    "Copper Circlet",         2, c(0.85, 0.55, 0.35), c(0.30, 0.80, 0.50), "INV_Crown_02" },
  { "craft_iron_greathelm",   "head",   "head_greathelm",  "Ironforge Greathelm",    3, c(0.60, 0.62, 0.68), c(0.85, 0.65, 0.30), "INV_Helmet_03" },
  { "craft_mithril_medal",    "acc",    "acc_medal",       "Mithril Medal",          3, c(0.70, 0.85, 0.95), c(0.30, 0.50, 0.90), "INV_Jewelry_Talisman_07" },
  { "craft_thorium_axe",      "main",   "wpn_axe",         "Thorium Battleaxe",      4, c(0.65, 0.55, 0.78), c(0.30, 0.25, 0.30), "INV_Axe_09" },
  { "craft_arcanite_reaper",  "main",   "wpn_axe",         "Arcanite Reaper",        5, c(0.40, 0.85, 1.00), c(0.25, 0.25, 0.35), "INV_Axe_09" },
  { "craft_peacebloom_crown", "head",   "head_flowers",    "Peacebloom Crown",       2, c(0.45, 0.75, 0.35), c(1.00, 1.00, 0.85), "INV_Misc_Flower_02" },
  { "craft_mageroyal_bloom",  "acc",    "acc_flower",      "Pressed Mageroyal",      3, c(0.80, 0.50, 1.00), c(1.00, 1.00, 0.60), "INV_Jewelry_Talisman_03" },
  { "craft_kingsblood_aura",  "effect", "fx_leaves",       "Kingsblood Swirl",       3, c(0.90, 0.25, 0.30), nil, "INV_Misc_Herb_03" },
  { "craft_dreamfoil_wreath", "head",   "head_flowers",    "Dreamfoil Wreath",       4, c(0.35, 0.70, 0.60), c(0.75, 0.60, 1.00), "INV_Misc_Herb_DreamFoil" },
  { "craft_lotus_bloom",      "effect", "fx_aura",         "Black Lotus Bloom",      5, c(0.55, 0.25, 0.85), nil, "INV_Misc_Herb_BlackLotus" },
  { "craft_wolfpelt_cloak",   "back",   "back_cape",       "Wolfpelt Cloak",         2, c(0.55, 0.45, 0.38), c(0.85, 0.80, 0.70), "INV_Misc_Cape_10" },
  { "craft_raptor_hood",      "head",   "head_hood",       "Raptor Hide Hood",       3, c(0.45, 0.55, 0.30), c(0.85, 0.70, 0.40), "INV_Helmet_29" },
  { "craft_thick_mantle",     "chest",  "chest_furmantle", "Thick Wolfhide Mantle",  3, c(0.50, 0.42, 0.35), c(0.90, 0.85, 0.75), "INV_Misc_Pelt_Wolf_01" },
  { "craft_devilsaur_mantle", "chest",  "chest_furmantle", "Devilsaur Mantle",       4, c(0.35, 0.55, 0.30), c(0.95, 0.60, 0.25), "INV_Misc_Pelt_Bear_03" },
  { "craft_onyxia_cloak",     "back",   "back_cape",       "Onyxia Scale Cloak",     5, c(0.25, 0.20, 0.25), c(0.85, 0.20, 0.20), "INV_Misc_Cape_18" },
  { "craft_fishing_hat",      "head",   "head_featcap",    "Lucky Fishing Hat",      2, c(0.55, 0.60, 0.40), c(0.95, 0.95, 0.85), "INV_Helmet_04" },
  { "craft_iron_pole",        "main",   "wpn_fishpole",    "Big Iron Fishing Pole",  3, c(0.60, 0.62, 0.68), c(1, 1, 1), "INV_Fishingpole_01" },
  { "craft_murloc_bubbles",   "effect", "fx_bubbles",      "Murloc's Bubbles",       3, c(0.40, 0.85, 0.70), nil, "INV_Misc_Head_Murloc_01" },
  { "craft_eel_shield",       "off",    "off_roundshield", "Stonescale Shield",      4, c(0.45, 0.55, 0.60), c(0.85, 0.75, 0.40), "INV_Shield_06" },
  { "craft_pinchy_gift",      "effect", "fx_coins",        "Mr. Pinchy's Gift",      5, c(1.00, 0.40, 0.30), nil, "INV_Misc_Fish_35" },
}

-- Racial heritage accessories: given to the cat when you log in on a character of that race
local RACE_ITEMS = {
  { "race_human",    "acc", "acc_race_human",    "Stormwind Crest",           3, c(0.25, 0.40, 0.85), c(1.00, 0.82, 0.30), "Achievement_Character_Human_Male" },
  { "race_dwarf",    "acc", "acc_race_dwarf",    "Ironforge Braids",          3, c(0.80, 0.40, 0.15), c(1.00, 0.80, 0.30), "Achievement_Character_Dwarf_Male" },
  { "race_nightelf", "acc", "acc_race_nightelf", "Kaldorei Ears",             3, c(0.72, 0.58, 0.92), c(0.35, 0.85, 0.75), "Achievement_Character_Nightelf_Female" },
  { "race_gnome",    "acc", "acc_race_gnome",    "Gnomish Goggles",           3, c(0.75, 0.55, 0.30), c(0.60, 0.90, 1.00), "Achievement_Character_Gnome_Male" },
  { "race_orc",      "acc", "acc_race_orc",      "Orcish Tusks",              3, c(0.95, 0.92, 0.82), c(0.65, 0.15, 0.15), "Achievement_Character_Orc_Male" },
  { "race_undead",   "acc", "acc_race_undead",   "Forsaken Stitches",         3, c(0.25, 0.22, 0.28), c(0.90, 0.88, 0.80), "Achievement_Character_Undead_Male" },
  { "race_tauren",   "acc", "acc_race_tauren",   "Tauren Horns & Nose Ring",  3, c(0.95, 0.90, 0.78), c(1.00, 0.80, 0.30), "Achievement_Character_Tauren_Male" },
  { "race_troll",    "acc", "acc_race_troll",    "Darkspear Tusks & Mohawk",  3, c(0.95, 0.92, 0.82), c(0.90, 0.30, 0.25), "Achievement_Character_Troll_Male" },
  { "race_skyborne", "acc", "acc_race_skyborne", "Skyborne Feathers",         3, c(0.55, 0.80, 1.00), c(1, 1, 1), "INV_Feather_02" },
}
-- UnitRace() file names (and name fragments for newer races) -> item
TCF.RACE_ITEM = {
  Human = "race_human", Dwarf = "race_dwarf", NightElf = "race_nightelf", Gnome = "race_gnome",
  Orc = "race_orc", Scourge = "race_undead", Undead = "race_undead", Tauren = "race_tauren", Troll = "race_troll",
}

-- Cat skins: replace the whole cat's look (fur, markings, eyes). Bought in the
-- Appearance tab with TapCoins, or dropped by the boss that drops the real mount.
-- { id, name, rarity, fur, alpha, overlay {art, c1, c2}, eyes, mane, price, icon, drop }
local SKINS = {
  { "skin_frostsaber",   "Striped Frostsaber",      3, c(0.95, 0.97, 1.00), 1,   { "skin_stripes", c(0.55, 0.62, 0.75) }, c(0.50, 0.80, 1.00), nil, 900,  "Ability_Mount_WhiteTiger" },
  { "skin_nightsaber",   "Striped Nightsaber",      3, c(0.36, 0.28, 0.46), 1,   { "skin_stripes", c(0.16, 0.12, 0.22) }, c(0.80, 0.60, 1.00), nil, 900,  "Ability_Mount_BlackPanther" },
  { "skin_spotted",      "Spotted Frostsaber",      3, c(0.95, 0.97, 1.00), 1,   { "pat_leopard", c(0.55, 0.60, 0.72) },  c(0.50, 0.80, 1.00), nil, 900,  "Ability_Mount_WhiteTiger" },
  { "skin_panther",      "Black Panther",           3, c(0.16, 0.15, 0.18), 1,   nil,                                     c(1.00, 0.85, 0.20), nil, 900,  "Ability_Mount_BlackPanther" },
  { "skin_darkmoon",     "Darkmoon Kitty",          3, c(0.92, 0.58, 0.88), 1,   { "skin_stars", c(1.00, 1.00, 0.70) },   nil,                 nil, 900,  "INV_Misc_Ticket_Darkmoon_01" },
  { "skin_winterspring", "Winterspring Frostsaber", 4, c(0.82, 0.92, 1.00), 1,   { "skin_stripes", c(0.62, 0.80, 1.00) }, c(0.40, 0.90, 1.00), nil, 2800, "Ability_Mount_PinkTiger" },
  { "skin_mech",         "Mechanical Kitty",        4, c(0.60, 0.63, 0.68), 1,   { "skin_plates", c(0.35, 0.37, 0.42), c(0.95, 0.80, 0.40) }, c(1.00, 0.30, 0.20), nil, 2800, "INV_Gizmo_01" },
  { "skin_fel",          "Fel Kitty",               4, c(0.38, 0.85, 0.30), 1,   { "skin_stripes", c(0.15, 0.42, 0.10) }, c(0.90, 1.00, 0.30), nil, 2800, "Spell_Shadow_SummonFelHunter" },
  { "skin_lion",         "Golden Lion",             4, c(1.00, 0.82, 0.42), 1,   nil,                                     nil, c(0.78, 0.46, 0.16), 2800, "INV_Misc_Head_Dragon_Bronze" },
  { "skin_zulian",       "Swift Zulian Tiger",      5, c(1.00, 0.55, 0.15), 1,   { "skin_stripes", c(0.12, 0.08, 0.05) }, c(0.40, 1.00, 0.40), nil, nil,  "Ability_Mount_JungleTiger", { "High Priest Thekal", 0.03 } },
  { "skin_skeletal",     "Skeletal Cat",            5, c(0.24, 0.22, 0.27), 1,   { "skin_bones", c(0.92, 0.90, 0.82) },   c(0.40, 1.00, 0.60), nil, nil,  "Ability_Mount_Undeadhorse", { "Baron Rivendare", 0.03 } },
  { "skin_spectral",     "Spectral Tiger",          5, c(0.45, 1.00, 0.90), 0.6, { "skin_stripes", c(0.20, 0.60, 0.60) }, c(0.60, 1.00, 1.00), nil, 12000, "Ability_Mount_JungleTiger" },
}
TCF.SKIN_DROPS = {}  -- boss name -> { id, chance }

---------------------------------------------------------------- build item table
TCF.ITEMS = {}      -- id -> item
TCF.ITEM_LIST = {}  -- array

local function add(it)
  assert(not TCF.ITEMS[it.id], "duplicate item " .. it.id)
  TCF.ITEMS[it.id] = it
  TCF.ITEM_LIST[#TCF.ITEM_LIST + 1] = it
  it.price = TCF.RARITY[it.rarity].price
  if it.slot == "effect" then
    local fx = TCF.FX[it.art]
    it.fxLayer, it.fxAnim = fx.layer, fx.anim
  end
end

for _, cl in ipairs(TCF.CLASSES) do
  for _, g in ipairs(cl.gear) do
    for tier, m in ipairs(cl.mats) do
      add({
        id = cl.key .. ":" .. g[2] .. ":" .. tier,
        name = m[1] .. " " .. g[3], slot = g[1], art = g[2], class = cl.key,
        rarity = tier, c1 = m[2], c2 = m[3], icon = g[4], source = "loot",
      })
    end
  end
  for _, f in ipairs(cl.fx) do
    add({
      id = cl.key .. ":" .. f[1] .. ":" .. f[3],
      name = f[2], slot = "effect", art = f[1], class = cl.key,
      rarity = f[3], c1 = f[4], icon = TCF.SLOT_BY_KEY.effect.icon, source = "loot",
    })
  end
end

local function addUniversal(list, source)
  for _, u in ipairs(list) do
    local it = {
      id = u[1], slot = u[2], art = u[3], name = u[4], rarity = u[5],
      c1 = u[6], c2 = u[7], icon = u[8], source = source,
    }
    if u[9] then for k, v in pairs(u[9]) do it[k] = v end end
    add(it)
  end
end
addUniversal(U, "loot")
addUniversal(ACH_ITEMS, "achievement")
addUniversal(CRAFT, "craft")
addUniversal(RACE_ITEMS, "race")
for _, k in ipairs(SKINS) do
  local it = { id = k[1], slot = "skin", art = "cat_fur", name = k[2], rarity = k[3], c1 = k[4], alpha = k[5],
    overlay = k[6], eyes = k[7], mane = k[8], skinPrice = k[9], icon = k[10], source = "skin" }
  add(it)
  if k[11] then TCF.SKIN_DROPS[k[11][1]] = { id = k[1], chance = k[11][2] } end
end

-- Items every player owns from the start: each class's Common chest + main hand,
-- plus a few basic furs.
TCF.STARTER = { "fur_snow", "fur_ginger", "fur_cream", "fur_silver", "fur_peach" }
for _, cl in ipairs(TCF.CLASSES) do
  local gotChest, gotMain
  for _, g in ipairs(cl.gear) do
    if g[1] == "chest" and not gotChest then
      gotChest = true; TCF.STARTER[#TCF.STARTER + 1] = cl.key .. ":" .. g[2] .. ":1"
    elseif g[1] == "main" and not gotMain then
      gotMain = true; TCF.STARTER[#TCF.STARTER + 1] = cl.key .. ":" .. g[2] .. ":1"
    end
  end
end

---------------------------------------------------------------- chests
TCF.CHESTS = {
  { key = "pouch",  name = "Cat Treat Pouch",        cost = 100,  icon = "INV_Misc_Bag_10",
    weights = { 62, 28, 9, 1, 0 },  desc = "Mostly Common & Uncommon." },
  { key = "strong", name = "Adventurer's Strongbox", cost = 450,  icon = "INV_Box_02",
    weights = { 0, 55, 33, 10, 2 }, desc = "Uncommon or better. Small Legendary chance." },
  { key = "heroic", name = "Heroic Cache",           cost = 1400, icon = "INV_Box_04",
    weights = { 0, 0, 58, 34, 8 },  desc = "Rare or better. Best Legendary odds." },
}
TCF.CHEST_BY_KEY = {}
for _, ch in ipairs(TCF.CHESTS) do TCF.CHEST_BY_KEY[ch.key] = ch end

---------------------------------------------------------------- level titles
TCF.TITLES = {
  { 1, "Kitten" }, { 5, "Tabby Trainee" }, { 10, "Paw Adept" }, { 20, "Whisker Knight" },
  { 30, "Claw Champion" }, { 40, "Grand Mouser" }, { 50, "Purrlord" }, { 75, "Legendary Lap Cat" },
  { 100, "Eternal Tapper" },
}

---------------------------------------------------------------- achievements
-- stat: name of a TCF:GetStat() value; goal: threshold
TCF.ACHIEVEMENTS = {
  { id = "tap100",    name = "First Steps",         stat = "taps",     goal = 100,       coins = 25,    icon = "Ability_Druid_CatForm" },
  { id = "tap1k",     name = "Paws On",             stat = "taps",     goal = 1000,      coins = 75,    icon = "Ability_Druid_CatForm" },
  { id = "tap10k",    name = "Tap Dancer",          stat = "taps",     goal = 10000,     coins = 250,   icon = "Ability_Druid_Dash" },
  { id = "tap50k",    name = "Relentless Paws",     stat = "taps",     goal = 50000,     coins = 600,   icon = "Ability_Druid_Dash" },
  { id = "tap100k",   name = "Hundred Thousand",    stat = "taps",     goal = 100000,    coins = 1000,  icon = "Ability_Druid_Ravage", item = "ach_glow" },
  { id = "tap250k",   name = "Quarter Million",     stat = "taps",     goal = 250000,    coins = 2000,  icon = "Ability_Druid_Ravage" },
  { id = "tap500k",   name = "Half a Million",      stat = "taps",     goal = 500000,    coins = 3500,  icon = "Ability_Druid_Maul" },
  { id = "tap1m",     name = "The Tapmaster",       stat = "taps",     goal = 1000000,   coins = 7500,  icon = "INV_Crown_01", item = "ach_crown" },
  { id = "tap5m",     name = "Tapped Into Eternity",stat = "taps",     goal = 5000000,   coins = 25000, icon = "Spell_Holy_DivineIntervention" },

  { id = "lvl5",      name = "Growing Kitten",      stat = "level",    goal = 5,         coins = 100,   icon = "Spell_Holy_SealOfMight" },
  { id = "lvl10",     name = "Paw Adept",           stat = "level",    goal = 10,        coins = 250,   icon = "Spell_Holy_SealOfMight", item = "ach_party" },
  { id = "lvl25",     name = "Seasoned Whiskers",   stat = "level",    goal = 25,        coins = 750,   icon = "Spell_Holy_SealOfWisdom" },
  { id = "lvl50",     name = "Purrlord",            stat = "level",    goal = 50,        coins = 2500,  icon = "Spell_Holy_SealOfWisdom", item = "ach_fur" },
  { id = "lvl75",     name = "Legendary Lap Cat",   stat = "level",    goal = 75,        coins = 5000,  icon = "Spell_Holy_SealOfSalvation" },
  { id = "lvl100",    name = "Eternal Tapper",      stat = "level",    goal = 100,       coins = 10000, icon = "Spell_Holy_DivineIntervention", item = "ach_wings" },

  { id = "own25",     name = "Wardrobe Started",    stat = "owned",    goal = 25,        coins = 100,   icon = "INV_Chest_Cloth_17" },
  { id = "own50",     name = "Fashionista",         stat = "owned",    goal = 50,        coins = 250,   icon = "INV_Chest_Cloth_17" },
  { id = "own100",    name = "Clothes Horse",       stat = "owned",    goal = 100,       coins = 600,   icon = "INV_Chest_Plate16" },
  { id = "own250",    name = "The Collector",       stat = "owned",    goal = 250,       coins = 1500,  icon = "INV_Misc_Bag_10", item = "ach_tophat" },
  { id = "own400",    name = "Hoarder",             stat = "owned",    goal = 400,       coins = 4000,  icon = "INV_Misc_Bag_10" },
  { id = "ownall",    name = "Completionist",       stat = "ownedPct", goal = 100,       coins = 25000, icon = "INV_Misc_Bag_EnchantedRunecloth" },

  { id = "rare1",     name = "Ooh, Shiny",          stat = "rares",    goal = 1,         coins = 50,    icon = "INV_Misc_Gem_Sapphire_01" },
  { id = "epic1",     name = "Purple Paws",         stat = "epics",    goal = 1,         coins = 150,   icon = "INV_Misc_Gem_Amethyst_01" },
  { id = "epic10",    name = "Epic Collection",     stat = "epics",    goal = 10,        coins = 750,   icon = "INV_Misc_Gem_Amethyst_02" },
  { id = "leg1",      name = "Legendary!",          stat = "legends",  goal = 1,         coins = 500,   icon = "INV_Misc_Gem_Topaz_01" },
  { id = "leg10",     name = "Living Legend",       stat = "legends",  goal = 10,        coins = 3000,  icon = "INV_Misc_Gem_Topaz_02", item = "ach_prism" },

  { id = "classes",   name = "Jack of All Classes", stat = "classesPlayed", goal = 9,    coins = 300,   icon = "INV_Misc_Book_09" },
  { id = "outfit1",   name = "Dressed for Battle",  stat = "outfits",  goal = 1,         coins = 100,   icon = "INV_Shirt_GuildTabard_01" },
  { id = "outfit9",   name = "Master of Disguise",  stat = "outfits",  goal = 9,         coins = 2000,  icon = "Spell_Shadow_Charm" },

  { id = "earn1k",    name = "Pocket Change",       stat = "coinsEarned", goal = 1000,   coins = 50,    icon = "INV_Misc_Coin_01" },
  { id = "earn10k",   name = "Fat Coin Purse",      stat = "coinsEarned", goal = 10000,  coins = 500,   icon = "INV_Misc_Coin_02" },
  { id = "earn100k",  name = "Goblin Tycoon",       stat = "coinsEarned", goal = 100000, coins = 5000,  icon = "INV_Misc_Coin_03" },
  { id = "spend5k",   name = "Big Spender",         stat = "coinsSpent",  goal = 5000,   coins = 250,   icon = "INV_Misc_Coin_04" },

  { id = "chest10",   name = "Treasure Hunter",     stat = "chests",   goal = 10,        coins = 150,   icon = "INV_Box_02" },
  { id = "chest100",  name = "Loot Goblin",         stat = "chests",   goal = 100,       coins = 1500,  icon = "INV_Box_04" },
  { id = "drop1",     name = "Lucky Paw",           stat = "drops",    goal = 1,         coins = 50,    icon = "INV_Misc_Bag_07" },
  { id = "drop25",    name = "Fortune Favors",      stat = "drops",    goal = 25,        coins = 750,   icon = "INV_Misc_Bag_07" },

  { id = "frenzy1",   name = "Paw Frenzy",          stat = "frenzies", goal = 1,         coins = 25,    icon = "Ability_Druid_Berserk" },
  { id = "frenzy100", name = "Button Masher",       stat = "frenzies", goal = 100,       coins = 400,   icon = "Ability_Druid_Berserk", item = "ach_bongo" },
  { id = "tps12",     name = "Speed Demon",         stat = "peakTPS",  goal = 12,        coins = 300,   icon = "Ability_Rogue_Sprint", item = "ach_shades" },
  { id = "pet100",    name = "Good Kitty",          stat = "pets",     goal = 100,       coins = 200,   icon = "INV_ValentinesCandy" },
  { id = "adv1",      name = "Hogger Down!",         stat = "advTier",  goal = 1,         coins = 100,   icon = "Ability_Hunter_Pet_Hyena" },
  { id = "adv3",      name = "VanCleef's Downfall",  stat = "advTier",  goal = 5,         coins = 300,   icon = "INV_Misc_Bandana_03" },
  { id = "adv6",      name = "Crusade's End",        stat = "advTier",  goal = 11,        coins = 800,   icon = "INV_Shield_03" },
  { id = "adv9",      name = "Emperor's Fall",       stat = "advTier",  goal = 17,        coins = 2000,  icon = "INV_Crown_01" },
  { id = "adv12",     name = "Ragnaros Falls",       stat = "advTier",  goal = 23,        coins = 5000,  icon = "Spell_Fire_Elemental_Totem" },
  { id = "adv28",     name = "Naxxramas Conquered",  stat = "advTier",  goal = 28,        coins = 15000, icon = "Spell_Shadow_AbominationExplosion" },
  { id = "boss50",    name = "Boss Slayer",          stat = "bossKills", goal = 50,       coins = 750,   icon = "INV_Misc_Bone_HumanSkull_01" },
  { id = "quest10",   name = "Errand Cat",           stat = "questsDone", goal = 10,      coins = 150,   icon = "INV_Misc_Note_01" },
  { id = "quest100",  name = "Hero of the Realm",    stat = "questsDone", goal = 100,     coins = 1500,  icon = "INV_Misc_Note_02" },
  { id = "dungeon1",  name = "Delving Deeper",       stat = "dungeons", goal = 1,         coins = 100,   icon = "INV_Misc_Key_03" },
  { id = "dungeon25", name = "Dungeon Regular",      stat = "dungeons", goal = 25,        coins = 1000,  icon = "INV_Misc_Key_10" },
  { id = "raid1",     name = "Raid Cat",             stat = "raids",    goal = 1,         coins = 300,   icon = "INV_Misc_Key_14" },
  { id = "gear1",     name = "Shiny New Loot",       stat = "gearFound", goal = 1,        coins = 25,    icon = "INV_Chest_Chain" },
  { id = "gear100",   name = "Well Equipped",        stat = "gearFound", goal = 100,      coins = 600,   icon = "INV_Chest_Plate16" },
  { id = "epicgear",  name = "Purple Rain",          stat = "epicGear",  goal = 1,        coins = 400,   icon = "INV_Helmet_09" },
  { id = "epicgear25",name = "Raid Ready",           stat = "epicGear",  goal = 25,       coins = 3000,  icon = "INV_Chest_Plate09" },
  { id = "leggear",   name = "Legendary Weaponry",   stat = "legendGear", goal = 1,       coins = 10000, icon = "INV_Sword_39" },
  { id = "exp1",      name = "Into the Wild",        stat = "expeditionWins", goal = 1,   coins = 50,    icon = "INV_Misc_Map_01" },
  { id = "exp50",     name = "Expedition Leader",    stat = "expeditionWins", goal = 50,  coins = 1500,  icon = "INV_Misc_Map02" },
  { id = "craft1",    name = "Handmade",             stat = "crafted",   goal = 1,        coins = 75,    icon = "Trade_BlackSmithing" },
  { id = "craft10",   name = "Master Crafter",       stat = "crafted",   goal = 10,       coins = 1000,  icon = "Trade_BlackSmithing" },
  { id = "races4",    name = "Citizen of Azeroth",   stat = "races",    goal = 4,         coins = 400,   icon = "INV_Misc_Map02" },
  { id = "trade1m",   name = "Small Business",       stat = "tradeGold", goal = 1000000,  coins = 200,   icon = "INV_Misc_Coin_02" },
  { id = "trade1t",   name = "Trade Prince",         stat = "tradeGold", goal = 1e12,     coins = 2500,  icon = "INV_Misc_Coin_03" },
  { id = "renown1",   name = "Renowned Artisan",     stat = "renown",   goal = 1,         coins = 500,   icon = "INV_Misc_Note_02" },
  { id = "skins3",    name = "Nine Lives, Many Coats", stat = "skins",  goal = 3,         coins = 500,   icon = "Ability_Mount_WhiteTiger" },
  { id = "skinrare",  name = "Tiger King",           stat = "dropSkins", goal = 1,        coins = 1500,  icon = "Ability_Mount_JungleTiger" },
  { id = "streak7",   name = "Devoted",             stat = "streak",   goal = 7,         coins = 500,   icon = "INV_Misc_PocketWatch_01", item = "ach_medal" },
  { id = "streak30",  name = "Inseparable",         stat = "streak",   goal = 30,        coins = 3000,  icon = "INV_Misc_PocketWatch_02" },
}
local STAT_TEXT = {
  taps = "Tap %s times.", level = "Reach level %s.", owned = "Own %s cosmetics.",
  ownedPct = "Own every cosmetic.", rares = "Own %s Rare (or better) cosmetic.",
  epics = "Own %s Epic cosmetics.", legends = "Own %s Legendary cosmetics.",
  classesPlayed = "Dress your cat as all %s classes.", outfits = "Equip head, chest and main hand on %s class(es).",
  coinsEarned = "Earn %s TapCoins in total.", coinsSpent = "Spend %s TapCoins.",
  chests = "Open %s chests.", drops = "Find %s random loot drops while tapping.",
  frenzies = "Enter a Paw Frenzy %s times.", peakTPS = "Tap %s times in one second.",
  pets = "Pet your cat %s times.", streak = "Log in %s days in a row.",
  advTier = "Clear %s Adventure zones.", bossKills = "Defeat %s Adventure bosses.", questsDone = "Complete %s quests.",
  tradeGold = "Earn %s Trade Gold in Professions.", renown = "Earn %s Renown by selling your business.",
  skins = "Own %s cat skins.", dropSkins = "Get %s rare boss-drop skin (Swift Zulian Tiger or Skeletal Cat).",
  races = "Collect %s racial heritage pieces (log in on characters of different races).",
  gearFound = "Find %s pieces of real gear.", epicGear = "Own %s Epic gear item(s).", legendGear = "Own %s Legendary item.",
  expeditionWins = "Complete %s successful expedition(s).", crafted = "Craft %s cosmetic(s) with professions.",
  dungeons = "Finish %s real WoW dungeon(s) with the addon on.", raids = "Finish %s real WoW raid(s).",
}
for _, a in ipairs(TCF.ACHIEVEMENTS) do
  a.desc = string.format(STAT_TEXT[a.stat] or "%s", BreakUpLargeNumbers and BreakUpLargeNumbers(a.goal) or tostring(a.goal))
end
