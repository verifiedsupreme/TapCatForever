-- TapCatForever: one of a kind Legendaries (1.7.7), made up for TapCatForever and named for the
-- developer's friends. Level 60, found like every Legendary: in a Heroic Cache or a Raider's Hoard
-- opened by a level 60 cat. Each has its own drawing on the cat and its own icon
-- (tools/make_custom_legendaries.py writes them and CustomGearArt.lua).
-- Their ids are in TCF.CUSTOM_ID_BASE's range (Gear.lua): never a real WoW item, never reused.
local ADDON, TCF = ...

local ICON = "Interface\\AddOns\\TapCatForever\\Art\\v\\ic_tcf_"
-- id, key, name, slot, type, stats, class, friend, flavour
local LEGENDS = {
  { 1, "n8_harness", "N8 Dawg's Alpha Pack Harness", "CHEST", "leather",
    "arm=230,str=20,agi=24,sta=28,int=20,spi=12,crit=1,sp=30", "DRUID", "N8 Dawg",
    "The pack follows N8 Dawg everywhere. Now it follows you." },
  { 2, "caff_bow", "Caffeinated's Double Espresso", "RANGED", "bow",
    "min=150,max=245,spd=3,dps=65.83,agi=24,sta=12,hit=1,rap=40", "HUNTER", "Caffeinated",
    "Brewed double strength. Every arrow arrives a little early." },
  { 3, "bd_hammer", "Battledancer's Hammer of Justice", "2H", "mace",
    "min=236,max=374,spd=3.6,dps=84.72,str=32,sta=24,int=14,crit=1,ap=40", "PALADIN", "Battledancer",
    "Justice, delivered in perfect rhythm." },
  { 4, "shua_robe", "Shua's Vestments of the Dawn", "CHEST", "cloth",
    "arm=130,sta=24,int=30,spi=28,sp=64,mp5=10", "PRIEST", "Shua",
    "Woven from the first light of morning." },
  { 5, "ziggu_wand", "Ziggu's Wand of Endless Taps", "RANGED", "wand",
    "min=120,max=223,spd=1.6,dps=107.19,sta=12,int=16,sp=36,critr=14", nil, "Ziggu",
    "Tap. Tap. Tap. It never gets tired, and neither does Ziggu." },
}

TCF.CUSTOM_LEGENDARIES = {}
for _, l in ipairs(LEGENDS) do
  local id = TCF.CUSTOM_ID_BASE + l[1]
  local it = TCF.AddGear(id, l[3], ICON .. l[2], 5, 90, 60, l[4], l[5], l[6], 0, 0, 0, l[7])
  it = it or TCF.GEAR[id]
  it.custom, it.vec, it.friend, it.flavor = true, "tcf:" .. l[2], l[8], l[9]
  TCF.CUSTOM_LEGENDARIES[#TCF.CUSTOM_LEGENDARIES + 1] = it
end
-- Ziggu's wand shoots arcane bolts in Adventure (every wand has a school, SpellKitData.lua)
TCF.WAND_SCHOOL = TCF.WAND_SCHOOL or {}
TCF.WAND_SCHOOL[TCF.CUSTOM_ID_BASE + 5] = "arcane"

-- They look Legendary on the cat: each has its own effects, with sprites made for these five and used by
-- nothing else (tools/make_custom_legendaries.py: paw prints, leaves, coffee beans, steam, music notes, a holy
-- rune, feathers, a sun halo, tiny cat heads, tap stars), on top of the Legendary shine. CatAnim.lua layers,
-- in the 512 canvas the drawings use (CustomGearArt.lua has where each drawing sits).
TCF.ITEM_ANIM = TCF.ITEM_ANIM or {}
local function shine(col) return { kind = "scroll", sprite = "a_shine", scale = 220, vx = 110, vy = 0, color = col, alpha = 0.8, blend = "ADD" } end
-- a breathing glow: x, y, w, h
local function glow(sprite, x, y, w, h, col, lo, hi, speed, at)
  return { kind = "pulse", sprite = sprite, rect = { x, y, w, h }, color = col, a = { lo, hi }, speed = speed or 2, blend = "ADD", at = at or "behind" }
end
-- things floating off it: box x0, y0, x1, y1
local function float(sprite, box, col, col2, n, size, vy, spin, blend)
  return { kind = "particles", sprite = sprite, n = n or 5, box = box, vx = { -14, 14 }, vy = vy or { -60, -35 }, life = { 1.4, 2.4 },
    size = size or { 14, 22 }, sway = 12, spin = spin, color = col, color2 = col2, alpha = 0.95, blend = blend or "ADD", at = "front" }
end
local function twinkle(sprite, spots, col, n, size)
  return { kind = "glint", sprite = sprite, n = n or 3, spots = spots, size = size or { 22, 34 }, life = 0.8, gap = { 0.2, 1.0 }, color = col, blend = "ADD", at = "front" }
end
local A, B = TCF.ITEM_ANIM, TCF.CUSTOM_ID_BASE
-- N8 Dawg's harness: glowing green paw prints padding up off the pack, druid leaves swirling round it
A["gear:" .. (B + 1)] = { shine({ 0.8, 1, 0.7 }), glow("a_glow", -10, 130, 532, 400, { 0.35, 1, 0.4 }, 0.6, 1, 1.6),
  glow("a_glow", 92, 236, 328, 248, { 0.4, 1, 0.45 }, 0.1, 0.3, 1.6, "front"),
  float("a_tcf_paw", { 60, 230, 452, 450 }, { 0.55, 1, 0.5 }, { 1, 0.9, 0.4 }, 9, { 40, 54 }, { -60, -35 }, { -0.6, 0.6 }),
  float("a_tcf_leaf", { 50, 220, 462, 470 }, { 0.45, 0.95, 0.4 }, { 0.8, 1, 0.5 }, 7, { 32, 44 }, { -45, -22 }, { -2, 2 }) }
-- Caffeinated's bow: coffee beans popping out and tumbling, steam curling up from the cup
A["gear:" .. (B + 2)] = { shine({ 1, 0.9, 0.7 }), glow("a_glow", 270, 60, 260, 450, { 1, 0.6, 0.25 }, 0.45, 0.95, 2.2),
  float("a_tcf_steam", { 380, 170, 490, 270 }, { 1, 0.95, 0.9 }, { 1, 0.8, 0.6 }, 6, { 46, 62 }, { -60, -35 }),
  float("a_tcf_bean", { 300, 120, 512, 470 }, { 1, 1, 1 }, nil, 9, { 28, 38 }, { -55, -28 }, { -3, 3 }, "BLEND"),
  twinkle("a_tcf_star", { { 320, 104, 486, 474 } }, { 1, 0.8, 0.5 }, 3, { 26, 38 }) }
-- Battledancer's hammer: golden music notes dancing off the head, a holy rune turning above it
A["gear:" .. (B + 3)] = { shine({ 1, 1, 0.8 }), glow("a_glow", 170, 0, 342, 290, { 1, 0.95, 0.5 }, 0.55, 1, 2.6),
  float("a_tcf_note", { 170, 10, 512, 240 }, { 1, 0.9, 0.4 }, { 0.6, 0.85, 1 }, 10, { 38, 52 }, { -60, -32 }, { -1, 1 }),
  float("a_tcf_rune", { 290, 20, 430, 110 }, { 1, 1, 0.7 }, nil, 1, { 92, 104 }, { -6, -2 }, { 1.2, 1.6 }),
  twinkle("a_tcf_star", { { 230, 48, 478, 220 } }, { 1, 1, 0.75 }, 4, { 42, 58 }) }
-- Shua's robes: a big sun halo blazing out round the cat, white and gold feathers drifting up
A["gear:" .. (B + 4)] = { shine({ 1, 0.95, 0.75 }), glow("a_tcf_halo", 6, 100, 500, 500, { 1, 0.85, 0.4 }, 0.55, 1, 1.4),
  glow("a_glow", 92, 242, 328, 242, { 1, 0.9, 0.5 }, 0.1, 0.3, 1.4, "front"),
  float("a_tcf_feather", { 50, 220, 462, 470 }, { 1, 1, 1 }, { 1, 0.9, 0.55 }, 9, { 36, 50 }, { -50, -28 }, { -1.5, 1.5 }),
  twinkle("a_tcf_star", { { 200, 270, 312, 380 } }, { 1, 0.95, 0.6 }, 3, { 30, 44 }) }
-- Ziggu's wand: tiny glowing cat heads spilling off the crystal, tap stars bursting round it
A["gear:" .. (B + 5)] = { shine({ 1, 0.8, 1 }), glow("a_glow", 240, 50, 272, 260, { 1, 0.45, 0.95 }, 0.55, 1, 3),
  float("a_tcf_cat", { 260, 80, 512, 270 }, { 1, 0.55, 1 }, { 0.7, 0.6, 1 }, 10, { 32, 46 }, { -50, -24 }, { -1, 1 }),
  twinkle("a_tcf_star", { { 270, 80, 510, 270 } }, { 1, 0.95, 0.7 }, 7, { 42, 62 }) }
