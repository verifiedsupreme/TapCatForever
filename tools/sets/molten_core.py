"""Molten Core set (1.6): animated fire, the reference set for tools/sets/README.md.
Each piece is guaranteed from one Molten Core boss in Adventure until you own it.
  python3 tools/sets/molten_core.py            -> Art/v/k_mc_*.tga, Art/mc_*.tga, Sets/MoltenCore.lua
  python3 tools/set_preview.py tools/sets/molten_core.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: obsidian rock, glowing lava
OBS, OBS2, OBS3 = "#33232a", "#4b3036", "#6a4440"
LAVA, LAVA2, HOT, CORE = "#e2461a", "#ff8a1e", "#ffc93a", "#fff2b0"
IRON = "#5a5058"

def flame(x, y, h, w, lean=0.0, ink=3.5, cols=(LAVA, LAVA2, HOT, CORE)):
    """a sticker flame standing on (x, y): tip h above, base half-width w, tip pushed sideways by lean"""
    out = ""
    for k, (s, col) in enumerate(zip((1.0, 0.72, 0.46, 0.24), cols)):
        hh, ww, tx = h * s, w * s, x + lean * s
        by = y - h * (1 - s) * 0.18
        d = ("M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z"
             % (x - ww, by, x - ww * 1.15, by - hh * 0.45, tx - ww * 0.45, by - hh * 0.72, tx, by - hh,
                tx + ww * 0.55, by - hh * 0.66, x + ww * 1.15, by - hh * 0.42, x + ww, by, x, by + ww * 0.95, x - ww, by))
        out += P(d, col, ink if k == 0 else 0)
    return out

def frames(n, fn):
    """n flipbook frames: fn(rnd, k) draws frame k with its own random flicker"""
    return {"fl%d" % (k + 1): fn(random.Random(100 + k), k) for k in range(n)}

def lava_crack(pts, w=5):
    d = "M " + " L ".join("%.1f %.1f" % p for p in pts)
    return LN(d, INK, w + 3) + LN(d, LAVA2, w) + LN(d, HOT, max(1.5, w - 3))

# ---------------------------------------------------------------- crown (head space)
SPIKES = [(70, 32, 0.0), (98, 16, -0.0), (128, -2, 0.0), (158, 16, 0.0), (186, 32, 0.0)]  # x, tip y
def crown():
    s = ""
    for x, ty, _ in SPIKES:
        w = 20 if x != 128 else 25
        tx = x + (x - 128) * 0.12
        s += P("M %d 70 L %d %d L %.1f %d L %d %d L %d 70 Z" % (x - w, x - w * 0.55, ty + 30, tx, ty, x + w * 0.6, ty + 24, x + w), OBS2, 5)
        s += P("M %.1f %d L %d 66 L %d 66 Z" % (tx, ty + 8, x + 4, x + w - 6), OBS3, 0)
        # lava-dipped tip
        s += P("M %.1f %d L %.1f %d Q %.1f %d %.1f %d Z" % (tx - 7, ty + 14, tx, ty, tx + 7, ty + 12, tx - 7, ty + 14), LAVA2, 3)
        s += lava_crack([(x + (x - 128) * 0.1, ty + 16), (x - 4, ty + 32), (x + 2, 62)], 4)
    band = "M 54 92 Q 128 70 202 92 L 200 64 Q 128 46 56 64 Z"
    s += P(band, OBS, 5)
    s += lava_crack([(62, 80), (84, 72), (100, 78), (116, 68)], 4) + lava_crack([(140, 68), (156, 78), (172, 72), (194, 80)], 4)
    s += CI(128, 74, 13, HOT, 4) + CI(128, 74, 7, CORE, 0) + '<circle cx="124" cy="70" r="3" fill="#fff"/>'
    for x in (80, 176): s += GEM(x, 82, 5, "#ff5a2a")
    return HEAD(s)

def crown_veins():  # the lava veins alone, pulsing brighter
    s = ""
    for x, ty, _ in SPIKES: s += LN("M %.1f %d L %d %d L %d 62" % (x + (x - 128) * 0.1, ty + 14, x - 3, ty + 30, x + 2), CORE, 2.5)
    s += LN("M 62 80 L 84 72 L 100 78 L 116 68", CORE, 2.5) + LN("M 140 68 L 156 78 L 172 72 L 194 80", CORE, 2.5)
    s += '<g filter="url(#blur)">%s</g>' % CI(128, 74, 16, HOT, 0)
    return HEAD(s)

def crown_flames(rnd, k):
    s = ""
    for i, (x, ty, _) in enumerate(SPIKES):
        h = (40 if x != 128 else 56) * (0.85 + rnd.random() * 0.35)
        s += flame(x + (x - 128) * 0.12, ty + 10, h, 10 if x != 128 else 13, lean=(rnd.random() - 0.5) * 16 + (x - 128) * 0.06)
    return HEAD(s)

# ---------------------------------------------------------------- shoulders (body space, both sides)
def pauldron():
    cx, cy = SH_C
    dome = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 32, cy + 8, cx + 28, cy - 24, cx - 4, cy - 24,
        cx - 38, cy - 22, cx - 40, cy + 12, cx - 4, cy + 24, cx + 32, cy + 8)
    s = ""
    # three rock horns along the top
    for x, y, a, ln in ((cx - 24, cy - 14, -46, 22), (cx - 4, cy - 20, -14, 28), (cx + 16, cy - 18, 14, 20)):
        s += P("M %d %d L %.1f %.1f L %d %d Z" % (x - 7, y + 6, x + math.sin(math.radians(a)) * ln, y - math.cos(math.radians(a)) * ln, x + 7, y + 6), OBS2, 4)
    s += P(dome, OBS, 5)
    s += LN("M %d %d Q %d %d %d %d" % (cx - 26, cy - 10, cx - 10, cy - 18, cx + 8, cy - 15), OBS3, 5)
    s += lava_crack([(cx - 30, cy + 4), (cx - 16, cy - 4), (cx - 6, cy + 6), (cx + 8, cy - 2), (cx + 22, cy + 6)], 4)
    s += LN("M %d %d Q %d %d %d %d" % (cx - 38, cy + 8, cx - 6, cy + 22, cx + 30, cy + 6), IRON, 7) + LN("M %d %d Q %d %d %d %d" % (cx - 38, cy + 8, cx - 6, cy + 22, cx + 30, cy + 6), INK, 2)
    for x, y in ((cx - 26, cy + 13), (cx - 6, cy + 17), (cx + 14, cy + 13)): s += CI(x, y, 3, HOT, 2)
    return BOTH(s)

def pauldron_veins():
    cx, cy = SH_C
    return BOTH(LN("M %d %d L %d %d L %d %d L %d %d L %d %d" % (cx - 30, cy + 4, cx - 16, cy - 4, cx - 6, cy + 6, cx + 8, cy - 2, cx + 22, cy + 6), CORE, 2.5))

def pauldron_flames(rnd, k):
    cx, cy = SH_C
    s = ""
    for x, y, a in ((cx - 24, cy - 14, -46), (cx - 4, cy - 20, -14), (cx + 16, cy - 18, 14)):
        ln = 22 if a != -14 else 28
        tx, ty = x + math.sin(math.radians(a)) * ln, y - math.cos(math.radians(a)) * ln
        s += flame(tx, ty + 8, 16 * (0.8 + rnd.random() * 0.45), 5, lean=(rnd.random() - 0.5) * 8 + a * 0.12, ink=3)
    return BOTH(s)

# ---------------------------------------------------------------- chest (body space)
SEAMS = [[(128, 128), (124, 146), (128, 160)], [(128, 172), (132, 190), (126, 212)],
         [(116, 160), (98, 150), (84, 132)], [(140, 160), (158, 150), (172, 132)],
         [(118, 170), (96, 184), (78, 204)], [(138, 170), (160, 184), (178, 204)]]
def chest():
    s = P(BODY_OUT, OBS, 5)
    # rock plates: lighter facets between the seams
    for d in ("M 84 132 L 98 150 L 116 160 L 112 128 Z", "M 172 132 L 158 150 L 140 160 L 144 128 Z",
              "M 78 204 L 96 184 L 118 170 L 114 210 Z", "M 178 204 L 160 184 L 138 170 L 142 210 Z"):
        s += P(d, OBS2, 0)
    for seam in SEAMS: s += lava_crack(seam, 5)
    # the molten heart
    heart = "M 128 180 C 104 166 104 146 118 142 C 124 140 128 146 128 150 C 128 146 132 140 138 142 C 152 146 152 166 128 180 Z"
    s += P(heart, LAVA2, 4.5) + P("M 128 172 C 114 162 114 150 121 148 C 125 147 128 151 128 154 C 128 151 131 147 135 148 C 142 150 142 162 128 172 Z", HOT, 0)
    s += RC(60, 198, 136, 14, IRON, 4, 4) + "".join(CI(x, 205, 3.5, HOT, 2) for x in (76, 102, 154, 180)) + RC(116, 196, 24, 18, OBS2, 4, 4) + CI(128, 205, 5, LAVA2, 2.5)
    return s

def chest_seams():  # white mask of the seams (lava flows inside it)
    return "".join(LN("M " + " L ".join("%.1f %.1f" % p for p in seam), "#ffffff", 5) for seam in SEAMS)

def chest_core():
    heart = "M 128 180 C 104 166 104 146 118 142 C 124 140 128 146 128 150 C 128 146 132 140 138 142 C 152 146 152 166 128 180 Z"
    return '<g filter="url(#blur)">%s</g>' % P(heart, HOT, 0) + P("M 128 170 C 116 161 116 151 122 150 C 125 149 128 152 128 155 C 128 152 131 149 134 150 C 140 151 140 161 128 170 Z", CORE, 0)

# ---------------------------------------------------------------- cape (side drapes)
def cape():
    s = "".join(P(p, OBS, 5) for p in DRAPE_OUT) + "".join(P(p, "#7a1e14", 3) for p in DRAPE_IN)
    # glowing hem along the outer edges
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        d = "M " + " L ".join("%.1f %.1f" % (x + (5 if x < 128 else -5), y) for x, y in pts)
        s += LN(d, LAVA, 7) + LN(d, HOT, 3)
    s += LN("M 56 150 Q 46 172 48 194", "#a8361c", 3) + LN("M 200 150 Q 210 172 208 194", "#a8361c", 3)
    return s

def cape_flames(rnd, k):
    s = ""
    for side in DRAPE_EDGE:
        for i, (x, y) in enumerate(qpts(*side, n=5)[1:]):
            out = -1 if x < 128 else 1
            s += flame(x + out * 2, y + 4, (18 + i * 3) * (0.8 + rnd.random() * 0.45), 6, lean=out * (8 + rnd.random() * 8), ink=3)
    return s

# ---------------------------------------------------------------- hammer (right paw)
HL = 150
def hammer():
    s = RC(-5.5, -HL, 11, HL + 30, "#3a2c2a", 4)
    for y in (-30, -70, -110): s += RC(-8, y - 6, 16, 10, LAVA2, 3, 3)
    s += CI(0, 22, 8, OBS2, 4) + CI(0, 22, 4, HOT, 0)
    y = -HL - 14
    head = "M -44 %d L 40 %d L 46 %d L 40 %d L -44 %d L -50 %d Z" % (y - 24, y - 24, y, y + 24, y + 24, y)
    s += P(head, OBS, 5)
    s += P("M 40 %d L 62 %d L 46 %d L 62 %d L 40 %d Z" % (y - 18, y - 30, y, y + 30, y + 18), OBS2, 4)
    s += RC(-10, y - 30, 20, 60, IRON, 4, 4)
    for x in (-34, -18): s += lava_crack([(x, y - 16), (x + 6, y - 4), (x, y + 6), (x + 6, y + 16)], 3.5)
    s += lava_crack([(20, y - 14), (28, y), (20, y + 14)], 3.5)
    s += CI(0, y, 8, HOT, 3) + CI(0, y, 4, CORE, 0)
    return RHAND(s)

def hammer_veins():
    y = -HL - 14
    s = "".join(LN("M %d %d L %d %d L %d %d L %d %d" % (x, y - 16, x + 6, y - 4, x, y + 6, x + 6, y + 16), CORE, 2) for x in (-34, -18))
    s += LN("M 20 %d L 28 %d L 20 %d" % (y - 14, y, y + 14), CORE, 2) + '<g filter="url(#blur)">%s</g>' % CI(0, y, 12, HOT, 0)
    return RHAND(s)

def hammer_flames(rnd, k):
    y = -HL - 14 - 22
    s = ""
    for x, h in ((-36, 26), (-14, 36), (10, 32), (32, 24)):
        s += flame(x, y + 6, h * (0.8 + rnd.random() * 0.4), 8, lean=(rnd.random() - 0.5) * 14 - 6)
    return RHAND(s)

# ---------------------------------------------------------------- data
FIRE = (1.0, 0.55, 0.18)
EMBERS = {"kind": "particles", "sprite": "a_ember", "blend": "ADD", "color": [1.0, 0.75, 0.3], "color2": [1.0, 0.3, 0.08]}

SET = {
    "key": "mc", "name": "Molten Core", "zone": "mc", "lua": "MoltenCore", "file": "molten_core",
    "about": "Molten Core set: animated fire, each piece guaranteed from one Molten Core boss in Adventure until owned.",
    "preview_fur": "fur_midnight",
    "pieces": [
        {"id": "set_mc_crown", "slot": "head", "kind": "head", "art": "mc_crown", "name": "Crown of the Firelord", "rarity": 5,
         "icon": "INV_Crown_02", "boss": "Ragnaros", "word": "crown",
         "svg": crown(), "layers": dict(frames(4, crown_flames), veins=crown_veins()),
         "anim": [
             {"kind": "flip", "keys": [K("mc_crown", "fl%d" % i) for i in range(1, 5)], "fps": 9},
             {"kind": "pulse", "key": K("mc_crown", "veins"), "a": [0.25, 1.0], "speed": 3.1, "blend": "ADD"},
             dict(EMBERS, n=6, box=[170, 10, 342, 80], vx=[-14, 14], vy=[-80, -45], life=[1.0, 1.6], size=[12, 20], sway=6, at="front"),
         ]},
        {"id": "set_mc_shoulders", "slot": "shoulder", "kind": "shoulder", "art": "mc_shoulders", "name": "Golemagg's Molten Pauldrons", "rarity": 4,
         "icon": "INV_Shoulder_09", "boss": "Golemagg the Incinerator", "word": "shoulders",
         "svg": pauldron(), "layers": dict(frames(3, pauldron_flames), veins=pauldron_veins()),
         "anim": [
             {"kind": "flip", "keys": [K("mc_shoulders", "fl%d" % i) for i in range(1, 4)], "fps": 8},
             {"kind": "pulse", "key": K("mc_shoulders", "veins"), "a": [0.2, 1.0], "speed": 2.6, "blend": "ADD"},
         ]},
        {"id": "set_mc_chest", "slot": "chest", "kind": "chest", "art": "mc_chest", "name": "Lava-Heart Breastplate", "rarity": 4,
         "icon": "INV_Chest_Plate09", "boss": "Garr", "word": "chest",
         "svg": chest(), "layers": {"seam": chest_seams(), "core": chest_core()},
         "anim": [
             {"kind": "scroll", "sprite": "a_lava", "mask": K("mc_chest", "seam"), "scale": 150, "vx": 6, "vy": -26},
             {"kind": "pulse", "key": K("mc_chest", "core"), "a": [0.15, 0.95], "speed": 2.2, "blend": "ADD"},
         ]},
        {"id": "set_mc_cape", "slot": "back", "kind": "back", "art": "mc_cape", "name": "Magmadar's Cinder Drape", "rarity": 4,
         "icon": "INV_Misc_Cape_18", "boss": "Magmadar", "word": "cape",
         "svg": cape(), "layers": frames(3, cape_flames),
         "anim": [
             {"kind": "flip", "keys": [K("mc_cape", "fl%d" % i) for i in range(1, 4)], "fps": 8},
             dict(EMBERS, n=4, box=[60, 300, 110, 430], vx=[-16, 4], vy=[-60, -30], life=[1.2, 2.0], size=[10, 16], sway=5, at="behind"),
             dict(EMBERS, n=4, box=[402, 300, 452, 430], vx=[-4, 16], vy=[-60, -30], life=[1.2, 2.0], size=[10, 16], sway=5, at="behind"),
         ]},
        {"id": "set_mc_hammer", "slot": "main", "kind": "weapon", "art": "mc_hammer", "name": "Lucifron's Firehammer", "rarity": 5,
         "icon": "INV_Hammer_Unique_Sulfuras", "boss": "Lucifron", "word": "hammer",
         "svg": hammer(), "layers": dict(frames(4, hammer_flames), veins=hammer_veins()),
         "anim": [
             {"kind": "flip", "keys": [K("mc_hammer", "fl%d" % i) for i in range(1, 5)], "fps": 9},
             {"kind": "pulse", "key": K("mc_hammer", "veins"), "a": [0.2, 1.0], "speed": 3.4, "blend": "ADD"},
         ]},
        {"id": "set_mc_aura", "slot": "effect", "kind": "effect", "art": "fx_mc_embers", "name": "Baron Geddon's Ember Aura", "rarity": 4,
         "icon": "Spell_Fire_SelfDestruct", "boss": "Baron Geddon", "word": "aura", "glow": FIRE,
         "fx": {"layer": "back", "anim": "flicker"},
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [1.0, 0.45, 0.12], "a": [0.25, 0.6], "speed": 2.0, "blend": "ADD", "flicker": True, "at": "behind"},
             dict(EMBERS, n=7, box=[100, 240, 412, 470], vx=[-12, 12], vy=[-90, -50], life=[1.4, 2.4], size=[12, 22], sway=10, at="front"),
             dict(EMBERS, n=6, box=[80, 120, 432, 440], vx=[-10, 10], vy=[-70, -40], life=[1.6, 2.6], size=[11, 18], sway=8, at="behind"),
             {"kind": "particles", "sprite": "a_flame", "n": 3, "box": [130, 380, 382, 460], "vx": [-6, 6], "vy": [-60, -40], "life": [0.9, 1.3],
              "size": [18, 26], "alpha": 0.9, "at": "behind"},
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
