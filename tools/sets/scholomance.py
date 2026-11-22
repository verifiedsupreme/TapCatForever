"""Scholomance set (1.6): necromancy. Bone and dark violet iron, a horned skull crown burning with green
soulfire, a ribcage breastplate with trapped souls swirling inside it, a tattered bat-wing shroud, a
soul-reaper scythe and ghosts rising around the cat. Each piece is guaranteed from one Scholomance boss
in Adventure until owned.
  python3 tools/sets/scholomance.py            -> Art/v/k_scholo_*.tga, Art/scholo_*.tga, Sets/Scholomance.lua
  python3 tools/set_preview.py tools/sets/scholomance.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: old bone, dark violet iron, green soulfire
BONE, BONE2, BONED = "#efe6cf", "#d3c6a6", "#9c8f72"
VOID, VOID2, VOID3 = "#2b1f3d", "#43305e", "#634887"
SOULD, SOUL, SOUL2, SOULC = "#1d9a5c", "#4cf08a", "#b6ffcf", "#f2fff6"
SOULC3 = [0.35, 1.0, 0.6]

def frames(n, fn):
    return {"fl%d" % (k + 1): fn(random.Random(300 + k), k) for k in range(n)}

# a blur whose region is the whole canvas, so the glow of a small shape is never cut off into a box
WIDEBLUR = ('<defs><filter id="wblur" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1100" height="1100">'
            '<feGaussianBlur stdDeviation="5"/></filter></defs>')
def blur(s): return WIDEBLUR + '<g filter="url(#wblur)">%s</g>' % s

def sprite(inner, S=32):
    """a small particle sprite: the drawing centred in an exact S x S box (faint corner dots fix the crop)"""
    dots = '<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/><rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S)
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)

def flame(x, y, h, w, lean=0.0, ink=3.5, cols=(SOULD, SOUL, SOUL2, SOULC), top=None):
    """a sticker flame standing on (x, y): tip h above, base half-width w, tip pushed sideways by lean"""
    if top is not None: h = min(h, y - top)   # keep the tip inside the canvas
    out = ""
    for k, (s, col) in enumerate(zip((1.0, 0.72, 0.46, 0.24), cols)):
        hh, ww, tx = h * s, w * s, x + lean * s
        by = y - h * (1 - s) * 0.18
        d = ("M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z"
             % (x - ww, by, x - ww * 1.15, by - hh * 0.45, tx - ww * 0.45, by - hh * 0.72, tx, by - hh,
                tx + ww * 0.55, by - hh * 0.66, x + ww * 1.15, by - hh * 0.42, x + ww, by, x, by + ww * 0.95, x - ww, by))
        out += P(d, col, ink if k == 0 else 0)
    return out

def skull(cx, cy, r, eyes=INK, ink=4, jaw=True, fill=BONE):
    """a cartoon skull facing us: cranium r wide, two eye sockets, a nose notch and a row of teeth"""
    d = ("M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f L %.1f %.1f L %.1f %.1f Z"
         % (cx - r * 0.62, cy + r * 0.78, cx - r * 1.12, cy + r * 0.3, cx - r * 1.05, cy - r, cx, cy - r,
            cx + r * 1.05, cy - r, cx + r * 1.12, cy + r * 0.3, cx + r * 0.62, cy + r * 0.78, cx + r * 0.5, cy + r * 1.15, cx - r * 0.5, cy + r * 1.15))
    s = P(d, fill, ink)
    s += P("M %.1f %.1f Q %.1f %.1f %.1f %.1f" % (cx - r * 0.7, cy - r * 0.55, cx, cy - r * 0.95, cx + r * 0.55, cy - r * 0.7), "none", 0) \
        + LN("M %.1f %.1f Q %.1f %.1f %.1f %.1f" % (cx - r * 0.62, cy - r * 0.5, cx - r * 0.2, cy - r * 0.85, cx + r * 0.3, cy - r * 0.78), "#ffffff", max(1.5, r * 0.12), .7)
    for sx in (-1, 1):
        s += EL(cx + sx * r * 0.42, cy + r * 0.12, r * 0.3, r * 0.34, eyes, 0)
    s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (cx - r * 0.12, cy + r * 0.66, cx, cy + r * 0.44, cx + r * 0.12, cy + r * 0.66), INK, 0)
    if jaw:
        for k in range(4):
            x = cx - r * 0.44 + k * r * 0.29
            s += LN("M %.1f %.1f L %.1f %.1f" % (x + r * 0.14, cy + r * 0.82, x + r * 0.14, cy + r * 1.1), BONED, max(1.2, r * 0.07))
    return s

def skull_eyes(cx, cy, r, col=SOUL, core=SOULC):
    s = ""
    for sx in (-1, 1):
        s += blur(EL(cx + sx * r * 0.42, cy + r * 0.12, r * 0.5, r * 0.5, col, 0)) + EL(cx + sx * r * 0.42, cy + r * 0.12, r * 0.18, r * 0.2, core, 0)
    return s

# ---------------------------------------------------------------- crown (head space)
SPIRES = [(64, 30, 17), (94, 8, 19), (162, 8, 19), (192, 30, 17)]   # x, tip y, half width
SK = (128, 54, 27)                                                 # the crown's skull: x, y, size
def horn(side):
    """a curling bone horn sweeping out from the band"""
    d = "M 70 88 C 30 90 4 62 12 14 C 18 4 26 6 26 16 C 26 46 40 62 74 66 Z"
    s = P(d, BONE, 5)
    for t, (x, y) in enumerate(((20, 24), (18, 40), (22, 56), (34, 70), (50, 78))):
        s += LN("M %d %d Q %d %d %d %d" % (x - 7, y + 2, x, y - 3 + t, x + 8 + t, y + 4), BONED, 2.5)
    s += LN("M 20 16 C 18 40 30 64 62 72", "#ffffff", 3, .55)
    return s if side < 0 else mirror(s, 128)

def crown():
    s = horn(-1) + horn(1)
    for x, ty, w in SPIRES:
        tx = x + (x - 128) * 0.1
        s += P("M %d 72 L %.1f %d L %.1f %d L %.1f %d L %d 72 Z" % (x - w, x - w * 0.5, ty + 34, tx, ty, x + w * 0.5, ty + 30, x + w), VOID2, 5)
        s += P("M %.1f %d L %d 68 L %d 68 Z" % (tx, ty + 10, x + 3, x + w - 5), VOID3, 0)
        s += P("M %.1f %d L %.1f %d L %.1f %d Z" % (tx - 6, ty + 14, tx, ty, tx + 6, ty + 13), BONE, 3)
    band = "M 52 96 Q 128 76 204 96 L 202 66 Q 128 48 54 66 Z"
    s += P(band, VOID, 5)
    s += LN("M 58 90 Q 128 72 198 90", VOID3, 3) + LN("M 56 70 Q 128 53 200 70", BONE2, 4)
    # little bone teeth hanging from the band, and soul gems
    for i in range(9):
        x = 62 + i * 16.5
        if abs(x - 128) < 20: continue
        y = 92 - 9 * (1 - ((x - 128) / 76.0) ** 2) + 1
        s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x - 4.5, y - 2, x, y + 8, x + 4.5, y - 2), BONE, 2.5)
    for x in (80, 176): s += GEM(x, 80, 6, SOUL)
    s += skull(*SK, eyes="#15301f")
    return HEAD(s)

def crown_glow():  # skull eyes and gems burning brighter
    return HEAD(skull_eyes(*SK) + "".join(blur(CI(x, 80, 9, SOUL, 0)) + CI(x, 80, 3, SOULC, 0) for x in (80, 176)))

def crown_flames(rnd, k):
    s = ""
    for x, ty, w in SPIRES:
        tx = x + (x - 128) * 0.1
        s += flame(tx, ty + 8, 30 * (0.8 + rnd.random() * 0.4), 9, lean=(rnd.random() - 0.5) * 14 + (x - 128) * 0.06, top=-6)
    for sx in (-1, 1):  # flames licking off the horn tips
        s += flame(128 + sx * 109, 10, 26 * (0.8 + rnd.random() * 0.4), 8, lean=sx * (4 + rnd.random() * 8), top=-6)
    s += flame(SK[0], SK[1] - SK[2] + 4, 58 * (0.85 + rnd.random() * 0.3), 15, lean=(rnd.random() - 0.5) * 16, top=-6)
    return HEAD(s)

def wisp():
    """a small ghost: rounded head, wavy tail, two dark eyes"""
    d = "M -9 2 C -10 -10 -4 -14 0 -14 C 4 -14 10 -10 9 2 C 9 8 6 12 4 9 C 2 13 -2 13 -3 9 C -6 13 -9 8 -9 2 Z"
    return sprite(P(d, "#ffffff", 2.5) + EL(-3.5, -4, 1.8, 2.5, INK, 0) + EL(3.5, -4, 1.8, 2.5, INK, 0) + EL(0, 2, 1.6, 1.2, INK, 0))

# ---------------------------------------------------------------- shoulders (body space)
def pauldron():
    cx, cy = SH_C
    s = ""
    # bone spikes fanning out behind (ribs)
    for a, ln in ((-70, 30), (-46, 38), (-22, 34)):
        x, y = cx - 14, cy - 6
        tx, ty = x + math.sin(math.radians(a)) * ln, y - math.cos(math.radians(a)) * ln
        s += P("M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" % (x - 6, y + 4, (x + tx) / 2 - 6, (y + ty) / 2 - 2, tx, ty,
               (x + tx) / 2 + 4, (y + ty) / 2 + 4, x + 6, y + 6), BONE, 3.5)
    plate = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 30, cy + 10, cx + 26, cy - 20, cx - 2, cy - 22,
        cx - 36, cy - 20, cx - 38, cy + 14, cx - 4, cy + 26, cx + 30, cy + 10)
    s += P(plate, VOID2, 5)
    s += LN("M %d %d Q %d %d %d %d" % (cx - 26, cy - 10, cx - 8, cy - 18, cx + 12, cy - 14), VOID3, 5)
    s += LN("M %d %d Q %d %d %d %d" % (cx - 36, cy + 10, cx - 4, cy + 24, cx + 28, cy + 8), BONE2, 6) + LN("M %d %d Q %d %d %d %d" % (cx - 36, cy + 10, cx - 4, cy + 24, cx + 28, cy + 8), INK, 2)
    s += skull(cx - 6, cy - 2, 15, eyes="#15301f", ink=3.5)
    return BOTH(s)

def pauldron_eyes():
    cx, cy = SH_C
    return BOTH(skull_eyes(cx - 6, cy - 2, 15))

def pauldron_flames(rnd, k):
    cx, cy = SH_C
    s = ""
    for a, ln in ((-70, 30), (-46, 38), (-22, 34)):
        x, y = cx - 14, cy - 6
        tx, ty = x + math.sin(math.radians(a)) * ln, y - math.cos(math.radians(a)) * ln
        s += flame(tx, ty + 6, 15 * (0.8 + rnd.random() * 0.5), 5, lean=(rnd.random() - 0.5) * 8 + a * 0.1, ink=3)
    return BOTH(s)

# ---------------------------------------------------------------- chest (body space)
RIBS = [(132, 26), (146, 30), (160, 32), (174, 30)]   # y, half width of each rib pair
CAGE = "M 128 124 C 96 132 92 176 104 190 L 152 190 C 164 176 160 132 128 124 Z"
def chest():
    s = P(BODY_OUT, VOID, 5)
    s += P("M 76 116 Q 66 160 70 214 L 92 214 Q 86 160 98 120 Z", VOID2, 0) + mirror(P("M 76 116 Q 66 160 70 214 L 92 214 Q 86 160 98 120 Z", VOID2, 0), 128)
    s += P(CAGE, "#123222", 4)                                    # the dark hollow the souls swirl in
    for y, w in RIBS:                                               # rib pairs curving from the spine
        for sx in (-1, 1):
            d = "M %d %d Q %d %d %d %d" % (128 + sx * 4, y, 128 + sx * w * 1.2, y - 6, 128 + sx * w, y + 14)
            s += LN(d, INK, 10) + LN(d, BONE, 6)
    s += RC(122, 124, 12, 70, BONE, 5, 3.5)                        # the spine
    for y in range(132, 192, 12): s += LN("M 123 %d L 133 %d" % (y, y), BONED, 2)
    # collar of small skulls, belt with a skull buckle
    s += RC(60, 198, 136, 14, VOID2, 4, 4) + "".join(CI(x, 205, 3.5, BONE, 2) for x in (72, 92, 164, 184))
    s += skull(128, 202, 10, eyes="#15301f", ink=3)
    return s

def chest_mask():
    return P(CAGE, "#ffffff", 0)

def chest_glow():
    return blur(P(CAGE, SOUL, 0)) + skull_eyes(128, 202, 10)

# ---------------------------------------------------------------- cape (side drapes grown into bat wings)
ROOT = (78, 112)
TIPS = [(16, 104), (8, 150), (20, 194)]
def wing_path():
    (x1, y1), (x2, y2), (x3, y3) = TIPS
    return ("M %d %d L %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d L 96 124 Z"
            % (ROOT[0], ROOT[1] - 6, x1, y1, 38, 128, x2, y2, 36, 172, x3, y3, 44, 204, 64, 212))

def wing_edge():
    (x1, y1), (x2, y2), (x3, y3) = TIPS
    return "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d" % (x1, y1, 38, 128, x2, y2, 36, 172, x3, y3, 44, 204, 64, 212)

def cape_one():
    s = P(wing_path(), VOID2, 5)
    s += P("M 70 120 L 22 112 Q 40 130 16 150 Q 40 170 26 190 Q 48 200 66 206 Z", VOID3, 0)
    for x, y in TIPS:   # finger bones from the shoulder out to each point
        d = "M %d %d Q %d %d %d %d" % (ROOT[0], ROOT[1], (ROOT[0] + x) / 2, (ROOT[1] + y) / 2 - 10, x, y)
        s += LN(d, INK, 8) + LN(d, BONE, 4)
        s += P("M %d %d L %d %d L %d %d Z" % (x - 1, y - 4, x - 9, y - 2, x - 1, y + 4), BONE, 2.5)
    s += P("M 74 108 Q 64 92 70 80 Q 74 94 84 104 Z", BONE, 3)   # the thumb claw
    s += P(DRAPE_OUT[0], VOID, 5) + P(DRAPE_IN[0], VOID2, 3)
    return s

def cape():
    one = cape_one()
    return one + mirror(one, 128)

def cape_edge():  # soulfire glow along the wing's scalloped edge
    d = wing_edge()
    one = blur(LN(d, SOUL, 7)) + LN(d, SOUL2, 2.5)
    return one + mirror(one, 128)

# ---------------------------------------------------------------- scythe (right paw)
SL = 150
BLADE = "M 2 -160 C 44 -172 70 -140 60 -88 C 50 -120 32 -138 4 -134 Z"
EDGE = "M 8 -142 C 34 -140 52 -122 58 -94"
def scythe():
    s = RC(-5, -SL, 10, SL + 34, BONE2, 4, 4)
    for y in (-118, -70, -22): s += RC(-8, y, 16, 9, VOID2, 3, 3)
    s += LN("M -2 -140 L -2 20", "#ffffff", 2, .5)
    s += P(BLADE, VOID2, 5) + LN(EDGE, SOUL, 4) + LN("M 14 -158 C 40 -160 58 -142 60 -112", VOID3, 3)
    s += skull(0, -SL - 2, 15, eyes="#15301f", ink=4)
    s += CI(0, 36, 7, BONE, 3.5)
    return RHAND(s)

def scythe_mask():
    return RHAND(P(BLADE, "#ffffff", 0))

def scythe_glow():
    return RHAND(blur(LN(EDGE, SOUL, 10)) + LN(EDGE, SOULC, 2.5) + skull_eyes(0, -SL - 2, 15))

def scythe_flames(rnd, k):
    return RHAND(flame(0, -SL - 14, 40 * (0.8 + rnd.random() * 0.4), 11, lean=(rnd.random() - 0.5) * 14))

# ---------------------------------------------------------------- aura: ghosts and grave mist
def mist(rnd, k):
    """a low curling grave mist on the ground: long soft wisps that drift and change shape each frame"""
    s = ""
    for i in range(7):
        x = 40 + i * 30 + 8 * math.sin(k * 2.1 + i) + rnd.uniform(-3, 3)
        y = 212 - 3 * math.sin(i * 0.9 + k) + rnd.uniform(-2, 2)
        s += EL(x, y, 26 + rnd.uniform(0, 8), 7 + rnd.uniform(0, 3), SOUL, 0)
    curls = ""
    for i in range(4):
        x = 52 + i * 50 + 10 * math.sin(k * 1.7 + i * 2) + rnd.uniform(-4, 4)
        curls += LN("M %.1f 214 q 8 -12 18 -4 q 6 6 -2 8" % x, SOUL2, 2.5, .8)
    return blur(s) + curls

def bone_skull():
    return sprite(skull(0, 0, 11, eyes="#15301f", ink=2.5, jaw=False))

SET = {
    "key": "scholo", "name": "Scholomance", "zone": "scholo", "lua": "Scholomance", "file": "scholomance",
    "about": "Scholomance set: necromancy and green soulfire, each piece guaranteed from one Scholomance boss in Adventure until owned.",
    "preview_fur": "fur_silver",
    "pieces": [
        {"id": "set_scholo_crown", "slot": "head", "kind": "head", "art": "scholo_crown", "name": "Gandling's Soulfire Crown", "rarity": 5,
         "icon": "INV_Helmet_08", "boss": "Darkmaster Gandling", "word": "crown",
         "svg": crown(), "layers": dict(frames(4, crown_flames), glow=crown_glow(), wisp=wisp()),
         "anim": [
             {"kind": "flip", "keys": [K("scholo_crown", "fl%d" % i) for i in range(1, 5)], "fps": 9},
             {"kind": "pulse", "key": K("scholo_crown", "glow"), "a": [0.3, 1.0], "speed": 2.8, "blend": "ADD"},
             {"kind": "particles", "sprite": "a_ember", "n": 6, "box": [160, 0, 352, 70], "vx": [-12, 12], "vy": [-70, -40], "life": [0.9, 1.5],
              "size": [10, 16], "color": SOULC3, "color2": [0.2, 0.8, 0.45], "blend": "ADD", "sway": 6, "at": "front"},
             {"kind": "particles", "sprite": "k_scholo_crown_wisp", "n": 2, "box": [150, 40, 362, 100], "vx": [-10, 10], "vy": [-40, -25], "life": [1.6, 2.4],
              "size": [22, 30], "alpha": 0.75, "color": [0.75, 1.0, 0.85], "sway": 10, "at": "front"},
         ]},
        {"id": "set_scholo_shoulders", "slot": "shoulder", "kind": "shoulder", "art": "scholo_shoulders", "name": "Rattlegore's Skull Spaulders", "rarity": 4,
         "icon": "INV_Shoulder_23", "boss": "Rattlegore", "word": "shoulders",
         "svg": pauldron(), "layers": dict(frames(3, pauldron_flames), eyes=pauldron_eyes()),
         "anim": [
             {"kind": "flip", "keys": [K("scholo_shoulders", "fl%d" % i) for i in range(1, 4)], "fps": 8},
             {"kind": "pulse", "key": K("scholo_shoulders", "eyes"), "a": [0.25, 1.0], "speed": 2.4, "blend": "ADD"},
         ]},
        {"id": "set_scholo_chest", "slot": "chest", "kind": "chest", "art": "scholo_chest", "name": "Kormok's Bound-Soul Ribcage", "rarity": 4,
         "icon": "INV_Chest_Cloth_43", "boss": "Kormok", "word": "chest",
         "svg": chest(), "layers": {"mask": chest_mask(), "glow": chest_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_swirl", "mask": K("scholo_chest", "mask"), "scale": 90, "vx": 10, "vy": -30, "color": SOULC3, "blend": "ADD"},
             {"kind": "pulse", "key": K("scholo_chest", "glow"), "a": [0.15, 0.8], "speed": 2.0, "blend": "ADD"},
         ]},
        {"id": "set_scholo_cape", "slot": "back", "kind": "back", "art": "scholo_cape", "name": "Kirtonos' Bat-Wing Shroud", "rarity": 4,
         "icon": "INV_Misc_Cape_20", "boss": "Kirtonos the Herald", "word": "cape",
         "svg": cape(), "layers": {"edge": cape_edge()},
         "anim": [
             {"kind": "pulse", "key": K("scholo_cape", "edge"), "a": [0.1, 0.85], "speed": 1.8, "blend": "ADD"},
             {"kind": "particles", "sprite": "a_wisp", "n": 3, "box": [20, 230, 90, 420], "vx": [-14, 0], "vy": [-40, -20], "life": [1.4, 2.2],
              "size": [20, 30], "color": SOULC3, "blend": "ADD", "sway": 6, "at": "behind"},
             {"kind": "particles", "sprite": "a_wisp", "n": 3, "box": [422, 230, 492, 420], "vx": [0, 14], "vy": [-40, -20], "life": [1.4, 2.2],
              "size": [20, 30], "color": SOULC3, "blend": "ADD", "sway": 6, "at": "behind"},
         ]},
        {"id": "set_scholo_scythe", "slot": "main", "kind": "weapon", "art": "scholo_scythe", "name": "Frostwhisper's Soul Reaper", "rarity": 5,
         "icon": "INV_Staff_14", "boss": "Ras Frostwhisper", "word": "scythe",
         "svg": scythe(), "layers": dict(frames(4, scythe_flames), mask=scythe_mask(), glow=scythe_glow()),
         "anim": [
             {"kind": "flip", "keys": [K("scholo_scythe", "fl%d" % i) for i in range(1, 5)], "fps": 9},
             {"kind": "pulse", "key": K("scholo_scythe", "glow"), "a": [0.2, 1.0], "speed": 3.0, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_swirl", "mask": K("scholo_scythe", "mask"), "scale": 70, "vx": -30, "vy": -10, "color": SOULC3, "blend": "ADD", "alpha": 0.7},
         ]},
        {"id": "set_scholo_aura", "slot": "effect", "kind": "effect", "art": "fx_scholo_ghosts", "name": "Jandice Barov's Haunting", "rarity": 4,
         "icon": "Spell_Shadow_Haunting", "boss": "Jandice Barov", "word": "aura", "glow": (0.3, 1.0, 0.55),
         "fx": {"layer": "back", "anim": "float"},
         "layers": dict(frames(3, mist), skull=bone_skull(), ghost=wisp()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [0.3, 1.0, 0.55], "a": [0.2, 0.5], "speed": 1.6, "blend": "ADD", "at": "behind"},
             {"kind": "flip", "keys": [K("fx_scholo_ghosts", "fl%d" % i) for i in range(1, 4)], "fps": 4, "alpha": 0.8, "blend": "ADD", "at": "behind"},
             {"kind": "particles", "sprite": "k_fx_scholo_ghosts_ghost", "n": 4, "box": [60, 260, 452, 450], "vx": [-10, 10], "vy": [-50, -30], "life": [1.8, 2.8],
              "size": [24, 36], "alpha": 0.8, "color": [0.7, 1.0, 0.8], "sway": 14, "at": "front"},
             {"kind": "particles", "sprite": "k_fx_scholo_ghosts_skull", "n": 3, "box": [70, 300, 442, 440], "vx": [-8, 8], "vy": [-45, -25], "life": [2.0, 3.0],
              "size": [18, 26], "spin": [-0.6, 0.6], "at": "behind"},
             {"kind": "particles", "sprite": "a_ember", "n": 6, "box": [80, 380, 432, 470], "vx": [-8, 8], "vy": [-70, -40], "life": [1.0, 1.6],
              "size": [8, 12], "color": SOULC3, "blend": "ADD", "at": "front"},
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
