"""Maraudon set (1.6): the living grove. A crown of branching living-wood antlers with rustling leaves,
green sap flowing inside the wood, glowing blossoms, fireflies and falling leaves. Each piece is
guaranteed from one Maraudon boss in Adventure until owned.
  python3 tools/sets/maraudon.py            -> Art/v/k_mara_*.tga, Art/mara_*.tga, Sets/Maraudon.lua
  python3 tools/set_preview.py tools/sets/maraudon.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: living wood, spring leaves, Maraudon's violet blossoms and crystals
BARK, BARK2, BARKL = "#7a5232", "#553520", "#a87a4c"
LEAF, LEAF2, LEAFL = "#4fb548", "#2c8236", "#a6e86e"
MOSS, MOSS2 = "#72b03c", "#4f8a2a"
BLOOM, BLOOM2, BLOOML = "#d660c6", "#9c3aa0", "#f7b2ec"
SAP, FIRE = "#d8ff7a", "#fffbd0"
STONE, STONE2, STONEL = "#8a7c92", "#605469", "#ab9fb3"
CRYS, CRYSL = "#a77cff", "#e3d0ff"
WHITE = "#ffffff"


def frames(n, fn):
    return {"fl%d" % (k + 1): fn(k) for k in range(n)}


def sprite(inner, S=32):
    """a small particle sprite: the drawing centred in an exact S x S box (faint corner dots fix the crop)"""
    dots = ('<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/>'
            '<rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S))
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)


def leaf(x, y, ln, w, ang, col=LEAF, ink=3, vein=True):
    """a sticker leaf with its stem at (x, y), pointing at angle ang (degrees, 0 = up)"""
    d = "M 0 0 Q %.1f %.1f 0 %.1f Q %.1f %.1f 0 0 Z" % (w, -ln * 0.45, -ln, -w, -ln * 0.45)
    s = P(d, col, ink)
    if vein: s += LN("M 0 -2 L 0 %.1f" % (-ln * 0.8), darker(col, .7), max(1.2, ink * 0.55))
    return '<g transform="translate(%.1f %.1f) rotate(%.1f)">%s</g>' % (x, y, ang, s)


def bloom(x, y, r, col=BLOOM, core=SAP, ink=3.5, petals=5, rot=0):
    s = ""
    for i in range(petals):
        a = math.radians(rot + i * 360.0 / petals)
        s += EL(x + math.sin(a) * r * 0.62, y - math.cos(a) * r * 0.62, r * 0.5, r * 0.36 + 1, col, ink, rot + i * 360.0 / petals + 90)
    for i in range(petals):
        a = math.radians(rot + i * 360.0 / petals)
        s += EL(x + math.sin(a) * r * 0.56, y - math.cos(a) * r * 0.56, r * 0.22, r * 0.12 + 0.5, BLOOML, 0, rot + i * 360.0 / petals + 90)
    return s + CI(x, y, r * 0.34, core, ink * 0.8)


def branch(d, w, col="#4c2d17", hi="#7a4e2a"):
    """a living-wood branch: an outlined stroke with a light grain line (dark, since the cel shading lightens thin strokes)"""
    return LN(d, INK, w + 7) + LN(d, col, w) + LN(d, hi, max(1.5, w * 0.22))


def glow(s): return '<g filter="url(#blur)">%s</g>' % s


# ---------------------------------------------------------------- crown of antlers (head space)
# left antler; the right one is its mirror
BEAM = "M 94 70 C 84 50 52 44 2 42"
TINES = ["M 80 54 Q 70 36 80 18", "M 54 47 Q 38 32 44 14", "M 24 43 Q 6 32 -6 18", "M 8 42 Q -6 46 -12 34"]
TIPS = [(80, 18, -4), (44, 14, -20), (-4, 18, -40), (-12, 34, -58)]   # x, y, leaf direction
def antler_paths(): return [BEAM] + TINES

def crown():
    s = ""
    one = branch(BEAM, 11) + "".join(branch(t, 7) for t in TINES)
    # little leaves along the beam (the tips rustle in the flipbook)
    one += leaf(66, 50, 18, 7, -150, LEAF2) + leaf(36, 45, 16, 6, -170, LEAF) + leaf(14, 42, 15, 6, 160, LEAF2)
    s += one + mirror(one, 128)
    # woven circlet with moss
    band = "M 50 96 Q 128 74 206 96 L 204 66 Q 128 48 52 66 Z"
    s += P(band, BARK, 5)
    for x in range(62, 200, 16):
        s += LN("M %d 92 Q %d 76 %d 62" % (x, x + 8, x + 2), BARK2, 3)
    s += LN("M 56 70 Q 128 52 200 70", BARKL, 3)
    moss = "M 52 68 Q 60 54 72 62 Q 82 50 94 58 Q 106 46 118 54 Q 128 44 138 54 Q 150 46 162 58 Q 174 50 184 62 Q 196 54 204 68 Q 128 54 52 68 Z"
    s += P(moss, MOSS, 4)
    # hanging vines past the ears
    for x, ln in ((52, 46), (204, 46)):
        d = "M %d 92 Q %d %d %d %d" % (x, x + (-10 if x < 128 else 10), 92 + ln * 0.5, x, 92 + ln)
        s += LN(d, INK, 7) + LN(d, LEAF2, 3.5)
        s += leaf(x, 92 + ln * 0.55, 13, 5, 210 if x < 128 else 150, LEAF) + leaf(x, 92 + ln, 14, 6, 180, LEAF2)
    # blossoms on the band, the big one in front
    s += bloom(92, 80, 15, BLOOM2, rot=10) + bloom(164, 80, 15, BLOOM2, rot=-10)
    s += leaf(114, 70, 20, 8, -60, LEAF) + leaf(142, 70, 20, 8, 60, LEAF)
    s += bloom(128, 70, 24, BLOOM, rot=0)
    return HEAD(s)

def crown_tips(k):
    """leaf clusters on the antler tips, rustling"""
    sway = (0, 7, 0, -7)[k]
    one = ""
    for i, (x, y, a) in enumerate(TIPS):
        sw = sway * (1 if i % 2 else -1)
        one += leaf(x, y, 22, 8, a - 30 + sw, LEAF2) + leaf(x, y, 24, 9, a + 28 + sw, LEAF) + leaf(x, y, 26, 9, a + sw * 1.5, LEAFL if i == 1 else LEAF)
    return HEAD(one + mirror(one, 128))

def crown_wood():  # white mask of the antlers: green sap drifts inside
    one = "".join(LN(d, WHITE, 11 if d == BEAM else 7) for d in antler_paths())
    return HEAD(one + mirror(one, 128))

def crown_glow():
    s = glow(CI(128, 70, 14, SAP, 0) + CI(92, 80, 8, SAP, 0) + CI(164, 80, 8, SAP, 0)) + CI(128, 70, 6, FIRE, 0)
    return HEAD(s)

# ---------------------------------------------------------------- shoulders (body space): mossy boulders
def boulder():
    cx, cy = SH_C
    s = ""
    # violet crystals breaking out of the rock
    for x, y, w, h, a in ((cx - 30, cy - 6, 10, 26, -42), (cx - 18, cy - 14, 11, 30, -18)):
        s += '<g transform="rotate(%d %d %d)">%s%s</g>' % (a, x, y + 12, P("M %d %d L %d %d L %d %d L %d %d Z" % (x - w / 2, y + 12, x, y + 12 - h, x + w / 2, y + 12, x, y + 18), CRYS, 3.5),
                                                          LN("M %d %d L %d %d" % (x - 1, y + 8, x, y + 14 - h + 4), CRYSL, 2))
    rock = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 32, cy + 10, cx + 30, cy - 20, cx + 2, cy - 22,
        cx - 26, cy - 24, cx - 38, cy - 2, cx - 44, cy + 18, cx - 8, cy + 24, cx + 14, cy + 26, cx + 32, cy + 10)
    s += P(rock, STONE, 5)
    s += P("M %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx - 30, cy + 12, cx - 12, cy + 2, cx + 8, cy + 14, cx - 8, cy + 20, cx - 30, cy + 12), STONE2, 0)
    s += LN("M %d %d L %d %d L %d %d" % (cx - 2, cy + 22, cx + 4, cy + 10, cx + 16, cy + 6), STONE2, 3)
    # moss cap dripping over the top
    moss = ("M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z"
            % (cx - 38, cy - 2, cx - 34, cy - 26, cx - 6, cy - 24, cx + 22, cy - 26, cx + 32, cy - 4, cx + 26, cy + 4, cx + 20, cy - 4,
               cx + 12, cy + 4, cx + 4, cy - 6, cx - 6, cy + 2, cx - 14, cy - 6, cx - 26, cy + 6, cx - 38, cy - 2))
    s += P(moss, MOSS, 4.5) + LN("M %d %d Q %d %d %d %d" % (cx - 26, cy - 16, cx - 8, cy - 22, cx + 12, cy - 18), light(MOSS, .4), 3.5)
    # glowing mushrooms on the outer edge
    for x, y, r in ((cx - 40, cy + 8, 7), (cx - 34, cy + 18, 5)):
        s += RC(x - 2, y, 4, 8, "#f4ead8", 2, 2.5) + P("M %d %d Q %d %d %d %d Z" % (x - r, y + 1, x, y - r * 1.4, x + r, y + 1), BLOOM, 3)
        s += CI(x - 2, y - 3, 1.4, BLOOML, 0)
    return BOTH(s)

def boulder_sprout(k):
    """a sprout with a blossom growing out of the moss, swaying"""
    cx, cy = SH_C
    a = (-6, 4, 12, 4)[k]
    x0, y0 = cx + 2, cy - 22
    sp = LN("M 0 0 Q -4 -12 0 -24", INK, 6) + LN("M 0 0 Q -4 -12 0 -24", LEAF2, 3)
    sp += leaf(-1, -10, 14, 6, -62, LEAF) + leaf(-1, -14, 13, 5, 58, LEAFL)
    sp += bloom(0, -28, 10, BLOOM, rot=a * 2)
    return BOTH('<g transform="translate(%d %d) rotate(%d)">%s</g>' % (x0, y0, a, sp))

def boulder_glow():
    cx, cy = SH_C
    return BOTH('<g filter="url(#blur)" opacity=".7">%s</g>' % (EL(cx - 26, cy - 12, 7, 12, CRYS, 0, -30) + CI(cx - 38, cy + 10, 5, BLOOM, 0)))

# ---------------------------------------------------------------- chest (body space): heartwood and vines
VINE = "M 70 132 Q 108 140 120 160 Q 132 180 160 176 Q 186 172 194 196"
VINE2 = "M 186 132 Q 160 138 150 150"
HEART = (128, 166)
def chest():
    s = P(BODY_OUT, BARK, 5)
    for x, k in ((78, -4), (96, -2), (114, 0), (142, 0), (160, 2), (178, 4)):
        s += LN("M %d 128 Q %d 170 %d 212" % (x, x + k + 6, x + k), BARK2, 3)
    s += LN("M 104 190 Q 100 198 106 204", BARK2, 2.5) + EL(168, 196, 6, 4, BARK2, 2.5)  # knots
    # moss collar
    collar = "M 74 118 Q 128 132 182 118 Q 186 132 176 134 Q 166 142 154 136 Q 140 146 128 138 Q 116 146 102 136 Q 90 142 80 134 Q 70 132 74 118 Z"
    s += P(collar, MOSS, 4.5) + LN("M 86 126 Q 128 138 170 126", light(MOSS, .4), 3)
    # vines wrapping across
    for d in (VINE, VINE2):
        s += LN(d, INK, 11) + LN(d, LEAF2, 6)
    for x, y, a in ((92, 136, -30), (112, 150, 40), (144, 178, -140), (176, 176, 30), (190, 190, 120), (162, 140, -60)):
        s += leaf(x, y, 16, 6, a, LEAF if a > 0 else LEAFL)
    # the blossoming heart
    s += leaf(HEART[0] - 10, HEART[1] + 6, 20, 8, -120, LEAF2) + leaf(HEART[0] + 10, HEART[1] + 6, 20, 8, 120, LEAF2)
    s += bloom(HEART[0], HEART[1], 22, BLOOM, rot=36)
    s += RC(60, 198, 136, 14, BARK2, 4, 4) + RC(116, 195, 24, 20, MOSS2, 4, 4) + GEM(128, 205, 5, CRYS)
    return s

def chest_vines(): return LN(VINE, WHITE, 6) + LN(VINE2, WHITE, 6)

def chest_glow(): return glow(CI(HEART[0], HEART[1], 16, SAP, 0)) + CI(HEART[0], HEART[1], 6, FIRE, 0)

# ---------------------------------------------------------------- cape (side drapes of leaves)
def cape():
    s = "".join(P(p, LEAF2, 5) for p in DRAPE_OUT) + "".join(P(p, "#1f5e2a", 3) for p in DRAPE_IN)
    # shingled leaf rows on the drapes
    for side in DRAPE_EDGE:
        out = -1 if side[0][0] < 128 else 1
        for row in range(3):
            for i, (x, y) in enumerate(qpts(*side, n=6)[1:]):
                xx = x - out * (8 + row * 11)
                if (xx - 128) * out < 50: continue
                s += leaf(xx, y - 10 + row * 4, 20, 8, 180 + out * (20 + row * 8), (LEAF, MOSS, LEAF2)[(i + row) % 3], 2.5)
    # a thorny vine along the inside
    for p0, p1, p2 in (((92, 124), (62, 160), (62, 206)), ((164, 124), (194, 160), (194, 206))):
        d = "M %d %d Q %d %d %d %d" % (p0 + p1 + p2)
        s += LN(d, INK, 9) + LN(d, BARK, 5)
        for x, y in qpts(p0, p1, p2, n=5)[1:]:
            o = 1 if x < 128 else -1
            s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x - 3, y - 3, x + o * 9, y - 6, x + 3, y + 3), BARKL, 2.5)
    return s

def cape_edge(k):
    """big leaves on the outer edges, fluttering"""
    s = ""
    for side in DRAPE_EDGE:
        out = -1 if side[0][0] < 128 else 1
        for i, (x, y) in enumerate(qpts(*side, n=6)[1:]):
            a = 180 + out * (70 - i * 8) + (0, 9, 0, -9)[(k + i) % 4] * out
            s += leaf(x + out * 2, y, 26 + i * 2, 10, a, (LEAF, LEAFL, LEAF)[i % 3], 3)
    return s

# ---------------------------------------------------------------- staff (right paw)
SL = 156
ORB = (0, -SL - 22)
def staff():
    s = ""
    shaft = "M 0 24 Q -6 -40 4 -90 Q 10 -130 0 %d" % (-SL)
    s += branch(shaft, 13)
    for y in (-50, -112): s += EL(2, y, 5, 3, BARK2, 2.5)
    s += LN("M -4 -20 Q -22 -34 -18 -54", INK, 6) + LN("M -4 -20 Q -22 -34 -18 -54", LEAF2, 3) + leaf(-18, -54, 14, 6, -20, LEAF)
    ox, oy = ORB
    # the cradle: three branches curling around the orb
    for d in ("M 0 %d Q -34 %d -18 %d" % (-SL, oy + 8, oy - 30), "M 0 %d Q 34 %d 18 %d" % (-SL, oy + 8, oy - 30), "M 0 %d Q 4 %d -2 %d" % (-SL, oy + 20, oy + 6)):
        s += branch(d, 6)
    s += CI(ox, oy, 19, "#6a3fc4", 4.5) + CI(ox, oy, 12, CRYS, 0) + '<circle cx="%d" cy="%d" r="4" fill="#fff"/>' % (ox - 6, oy - 7)
    s += P("M -18 %d Q 0 %d 18 %d" % (oy - 30, oy - 40, oy - 30), "none", 0)
    s += branch("M -18 %d Q 0 %d 18 %d" % (oy - 30, oy - 38, oy - 30), 5)
    s += bloom(14, oy - 30, 10, BLOOM, rot=20)
    return RHAND(s)

def staff_tips(k):
    ox, oy = ORB
    sw = (0, 8, 0, -8)[k]
    s = leaf(-18, oy - 30, 22, 8, -40 + sw, LEAF) + leaf(-18, oy - 30, 20, 8, -90 + sw, LEAF2) + leaf(18, oy - 30, 20, 8, 40 - sw, LEAFL)
    return RHAND(s)

def staff_orb(): return RHAND(CI(ORB[0], ORB[1], 16, WHITE, 0))

def staff_glow(): return RHAND(glow(CI(ORB[0], ORB[1], 21, SAP, 0)))

# ---------------------------------------------------------------- particles
def petal():
    return sprite('<g transform="rotate(30)">%s</g>' % (P("M 0 -12 Q 10 -2 0 12 Q -10 -2 0 -12 Z", BLOOML, 2.5) + LN("M 0 -6 L 0 6", BLOOM, 1.6)))

GREENS = {"color": [0.75, 1.0, 0.55], "color2": [1.0, 0.72, 0.3]}  # leaves turn gold as they fall
FIREFLY = {"kind": "particles", "sprite": "a_glow", "blend": "ADD", "color": [0.85, 1.0, 0.45]}

SET = {
    "key": "mara", "name": "Maraudon", "zone": "mara", "lua": "Maraudon", "file": "maraudon",
    "about": "Maraudon set: the living grove, each piece guaranteed from one Maraudon boss in Adventure until owned.",
    "preview_fur": "fur_cream",
    "pieces": [
        {"id": "set_mara_crown", "slot": "head", "kind": "head", "art": "mara_crown", "name": "Theradras' Crown of the Grove", "rarity": 5,
         "icon": "INV_Misc_Herb_09", "boss": "Princess Theradras", "word": "antler crown",
         "svg": crown(), "layers": dict(frames(4, crown_tips), wood=crown_wood(), glow=crown_glow()),
         "anim": [
             {"kind": "scroll", "sprite": "a_swirl", "mask": K("mara_crown", "wood"), "scale": 90, "vx": 4, "vy": -30,
              "color": [0.35, 0.95, 0.15], "blend": "ADD", "alpha": 0.7},
             {"kind": "flip", "keys": [K("mara_crown", "fl%d" % i) for i in range(1, 5)], "fps": 4},
             {"kind": "pulse", "key": K("mara_crown", "glow"), "a": [0.2, 1.0], "speed": 2.2, "blend": "ADD"},
             dict(GREENS, kind="particles", sprite="t_leaf", n=4, box=[40, 10, 472, 70], vx=[-10, 10], vy=[30, 55], life=[1.8, 2.6],
                  size=[16, 22], sway=14, spin=[-2.5, 2.5], at="front"),
             dict(FIREFLY, n=6, box=[30, 0, 482, 130], vx=[-14, 14], vy=[-18, 10], life=[1.6, 2.6], size=[12, 20], sway=12, at="front"),
         ]},
        {"id": "set_mara_shoulders", "slot": "shoulder", "kind": "shoulder", "art": "mara_shoulders", "name": "Landslide's Mossy Boulders", "rarity": 4,
         "icon": "INV_Stone_15", "boss": "Landslide", "word": "shoulders",
         "svg": boulder(), "layers": dict(frames(4, boulder_sprout), glow=boulder_glow()),
         "anim": [
             {"kind": "flip", "keys": [K("mara_shoulders", "fl%d" % i) for i in range(1, 5)], "fps": 3},
             {"kind": "pulse", "key": K("mara_shoulders", "glow"), "a": [0.05, 0.6], "speed": 1.8, "blend": "ADD"},
             dict(FIREFLY, n=3, box=[30, 180, 130, 260], vx=[-8, 8], vy=[-24, -8], life=[1.4, 2.2], size=[10, 15], sway=8, at="front"),
             dict(FIREFLY, n=3, box=[382, 180, 482, 260], vx=[-8, 8], vy=[-24, -8], life=[1.4, 2.2], size=[10, 15], sway=8, at="front"),
         ]},
        {"id": "set_mara_chest", "slot": "chest", "kind": "chest", "art": "mara_chest", "name": "Meshlok's Heartwood Vest", "rarity": 4,
         "icon": "INV_Chest_Leather_03", "boss": "Meshlok the Harvester", "word": "chest",
         "svg": chest(), "layers": {"vines": chest_vines(), "glow": chest_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_swirl", "mask": K("mara_chest", "vines"), "scale": 80, "vx": 30, "vy": -10,
              "color": [0.35, 0.95, 0.15], "blend": "ADD", "alpha": 0.8},
             {"kind": "pulse", "key": K("mara_chest", "glow"), "a": [0.15, 0.95], "speed": 2.0, "blend": "ADD"},
         ]},
        {"id": "set_mara_cape", "slot": "back", "kind": "back", "art": "mara_cape", "name": "Razorlash's Thornleaf Drape", "rarity": 4,
         "icon": "INV_Misc_Cape_16", "boss": "Razorlash", "word": "cape",
         "svg": cape(), "layers": frames(4, cape_edge),
         "anim": [
             {"kind": "flip", "keys": [K("mara_cape", "fl%d" % i) for i in range(1, 5)], "fps": 4},
             dict(GREENS, kind="particles", sprite="t_leaf", n=3, box=[40, 300, 100, 400], vx=[-14, 0], vy=[30, 50], life=[1.6, 2.4],
                  size=[11, 16], sway=10, spin=[-2, 2], at="behind"),
             dict(GREENS, kind="particles", sprite="t_leaf", n=3, box=[412, 300, 472, 400], vx=[0, 14], vy=[30, 50], life=[1.6, 2.4],
                  size=[11, 16], sway=10, spin=[-2, 2], at="behind"),
         ]},
        {"id": "set_mara_staff", "slot": "main", "kind": "weapon", "art": "mara_staff", "name": "Celebras' Blooming Staff", "rarity": 5,
         "icon": "INV_Staff_26", "boss": "Celebras the Cursed", "word": "staff",
         "svg": staff(), "layers": dict(frames(4, staff_tips), orb=staff_orb(), glow=staff_glow()),
         "anim": [
             {"kind": "scroll", "sprite": "a_swirl", "mask": K("mara_staff", "orb"), "scale": 60, "vx": 26, "vy": -18,
              "color": [0.45, 1.0, 0.3], "blend": "ADD", "alpha": 0.45},
             {"kind": "pulse", "key": K("mara_staff", "glow"), "a": [0.05, 0.4], "speed": 2.6, "blend": "ADD"},
             {"kind": "flip", "keys": [K("mara_staff", "fl%d" % i) for i in range(1, 5)], "fps": 4},
         ]},
        {"id": "set_mara_aura", "slot": "effect", "kind": "effect", "art": "fx_mara_leaves", "name": "Vyletongue's Falling Leaves", "rarity": 4,
         "icon": "Spell_Nature_Tranquility", "boss": "Lord Vyletongue", "word": "aura", "glow": (0.55, 1.0, 0.4),
         "fx": {"layer": "back", "anim": "pulse"},
         "layers": {"petal": petal()},
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [0.5, 1.0, 0.35], "a": [0.15, 0.4], "speed": 1.5, "blend": "ADD", "at": "behind"},
             dict(GREENS, kind="particles", sprite="t_leaf", n=6, box=[30, -20, 482, 140], vx=[-16, 16], vy=[40, 70], life=[3.0, 4.2],
                  size=[18, 26], sway=18, spin=[-2.5, 2.5], at="front"),
             {"kind": "particles", "sprite": "k_fx_mara_leaves_petal", "n": 6, "box": [30, -20, 482, 160], "vx": [-14, 14], "vy": [35, 60],
              "life": [3.0, 4.2], "size": [16, 22], "sway": 16, "spin": [-3, 3], "at": "behind"},
             dict(FIREFLY, n=6, box=[40, 120, 472, 470], vx=[-14, 14], vy=[-20, 6], life=[1.8, 2.8], size=[12, 20], sway=14, at="front"),
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
