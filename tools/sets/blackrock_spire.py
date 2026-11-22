"""Blackrock Spire set (1.6): the storm dragon. Black-violet dragon scale, gold belly plates and old horn,
with lightning crackling over every piece: a dragon-head helm with wings and glowing eyes (the cat looks
out from between its teeth), scale pauldrons with beast horns, a scaled drape with a spiny edge, a fang
glaive and a thunderstorm around the cat. Each piece is guaranteed from one Blackrock Spire boss in
Adventure until owned.
  python3 tools/sets/blackrock_spire.py            -> Art/v/k_brs_*.tga, Art/brs_*.tga, Sets/BlackrockSpire.lua
  python3 tools/set_preview.py tools/sets/blackrock_spire.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: black dragon scale, gold belly, horn, storm light
SCALE, SCALE2, SCALE3 = "#2c2440", "#45395f", "#6a5a94"
BELLY, BELLY2 = "#d9b062", "#f2d48e"
HORN, HORN2 = "#ece1c6", "#b8a784"
BOLT, BOLTL, STORM = "#7ee6ff", "#effdff", "#8a6cff"
EYE = "#ffd84a"
BOLTC = [0.5, 0.9, 1.0]

def frames(n, fn):
    return {"fl%d" % (k + 1): fn(random.Random(700 + k), k) for k in range(n)}

# a blur whose region is the whole canvas, so the glow of a short bolt is never cut off into a box
WIDEBLUR = ('<defs><filter id="wblur" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1100" height="1100">'
            '<feGaussianBlur stdDeviation="5"/></filter></defs>')
def blur(s): return WIDEBLUR + '<g filter="url(#wblur)">%s</g>' % s

def sprite(inner, S=32):
    """a small particle sprite: the drawing centred in an exact S x S box (faint corner dots fix the crop)"""
    dots = '<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/><rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S)
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)

def bolt(rnd, x0, y0, x1, y1, n=5, jag=8, w=4):
    """a crackling lightning bolt from (x0, y0) to (x1, y1): an ink-outlined zigzag with a soft glow"""
    pts = [(x0, y0)]
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    for i in range(1, n):
        t = i / float(n)
        o = rnd.uniform(-jag, jag)
        pts.append((x0 + dx * t + nx * o, y0 + dy * t + ny * o))
    pts.append((x1, y1))
    d = "M " + " L ".join("%.1f %.1f" % p for p in pts)
    return blur(LN(d, STORM, w + 8)) + LN(d, INK, w + 3) + LN(d, BOLT, w) + LN(d, BOLTL, max(1.2, w - 2.5))

def scales(x0, y0, x1, y1, r, col, rim, clip=None):
    """rows of overlapping round scales filling a box (each row offset by half a scale)"""
    s = ""
    row = 0
    y = y0
    while y <= y1:
        x = x0 + (r if row % 2 else 0)
        while x <= x1:
            s += '<path d="M %.1f %.1f A %.1f %.1f 0 0 0 %.1f %.1f" fill="%s" stroke="%s" stroke-width="2"/>' % (x - r, y, r, r, x + r, y, col, rim)
            x += 2 * r
        y += r * 0.9
        row += 1
    if clip: s = '<g clip-path="url(#%s)">%s</g>' % (clip, s)
    return s

# ---------------------------------------------------------------- helm (head space)
WING_TIPS = [(-14, 2), (-22, 36), (-6, 66)]
WROOT = (62, 60)
def wing():
    (x1, y1), (x2, y2), (x3, y3) = WING_TIPS
    mem = ("M %d %d L %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z"
           % (WROOT[0], WROOT[1] - 10, x1, y1, 0, 26, x2, y2, 4, 56, x3, y3, 22, 70, 58, 80))
    s = P(mem, SCALE2, 4.5) + P("M 56 62 L -12 12 Q 6 30 -22 40 Q 8 56 -6 64 Q 24 70 54 76 Z", STORM, 0, ' opacity=".55"')
    for x, y in WING_TIPS:
        d = "M %d %d Q %.1f %.1f %d %d" % (WROOT[0], WROOT[1], (WROOT[0] + x) / 2.0, (WROOT[1] + y) / 2.0 - 8, x, y)
        s += LN(d, INK, 7) + LN(d, SCALE3, 3.5)
        s += P("M %d %d L %d %d L %d %d Z" % (x + 2, y - 3, x - 7, y - 6, x + 1, y + 4), HORN, 2.5)
    return s

def horn():
    """a big swept-back dragon horn rising from the top of the helm"""
    d = "M 76 46 C 46 40 26 18 28 -8 C 40 12 62 22 100 26 Z"
    return (P(d, HORN, 5) + P("M 72 40 C 48 34 34 18 32 2 C 44 18 60 26 84 30 Z", "#ffffff", 0, ' opacity=".45"')
            + "".join(LN("M %d %d Q %d %d %d %d" % (x, y, x + 5, y - 6, x + 12, y - 6), HORN2, 2.2) for x, y in ((32, 8), (40, 18), (50, 26), (62, 32))))

def helm():
    s = wing() + mirror(wing(), 128) + horn() + mirror(horn(), 128)
    # the dragon's head over the top of the cat's head
    dome = "M 42 106 C 30 42 62 10 128 10 C 194 10 226 42 214 106 Z"
    s += P(dome, SCALE, 5)
    s += '<clipPath id="brsdome"><path d="%s"/></clipPath>' % dome
    s += scales(40, 18, 216, 64, 9, SCALE2, SCALE3, clip="brsdome")
    # brow ridges, the snout ridge with nostrils and the dragon's eyes
    s += P("M 128 14 Q 136 40 128 66 Q 120 40 128 14 Z", SCALE3, 3)
    for sx in (-1, 1):
        s += P("M %d 56 Q %d 34 %d 40 Q %d 52 %d 64 Z" % (128 + sx * 14, 128 + sx * 40, 128 + sx * 70, 128 + sx * 50, 128 + sx * 16), SCALE2, 4)
        s += EL(128 + sx * 40, 54, 10, 6, EYE, 3, rot=sx * 14) + EL(128 + sx * 40, 54, 2.2, 5, INK, 0)
    muzzle = "M 106 92 Q 104 66 116 58 Q 128 52 140 58 Q 152 66 150 92 Z"
    s += P(muzzle, SCALE2, 4.5) + P("M 112 86 Q 112 68 122 62 Q 128 60 128 70 L 128 86 Z", SCALE3, 0)
    s += EL(118, 78, 4, 2.6, INK, 0, rot=-20) + EL(138, 78, 4, 2.6, INK, 0, rot=20)
    # the upper jaw's gold rim and teeth: the cat looks out from inside
    s += LN("M 48 98 Q 128 84 208 98", INK, 13) + LN("M 48 98 Q 128 84 208 98", BELLY, 8) + LN("M 52 96 Q 128 84 204 96", BELLY2, 2)
    for i in range(10):
        x = 56 + i * 16
        y = 98 - 14 * (1 - ((x - 128) / 80.0) ** 2) + 4
        L = 13 if i in (3, 6) else 7
        s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x - 4.5, y, x, y + L, x + 4.5, y), HORN, 2.5)
    return HEAD(s)

def helm_eyes():
    s = ""
    for sx in (-1, 1):
        s += blur(EL(128 + sx * 40, 54, 15, 10, BOLT, 0, rot=sx * 14)) + EL(128 + sx * 40, 54, 7, 4, BOLTL, 0, rot=sx * 14)
    return HEAD(s)

def helm_bolts(rnd, k):
    """lightning crackling between the horn tips and along the wing bones, different every frame"""
    s = ""
    if k % 2 == 0:
        s += bolt(rnd, 32, -4, 224, -4, n=8, jag=7, w=3.5)
    for sx in (-1, 1):
        x, y = WING_TIPS[k % 3]
        x2, y2 = WING_TIPS[(k + 1) % 3]
        a, b = (x, y) if sx < 0 else (256 - x, y), (x2, y2) if sx < 0 else (256 - x2, y2)
        s += bolt(rnd, a[0], a[1], b[0], b[1], n=4, jag=6, w=3)
    return HEAD(s)

# ---------------------------------------------------------------- shoulders (body space)
def pauldron():
    cx, cy = SH_C
    # a beast horn curling up and out
    s = P("M %d %d C %d %d %d %d %d %d C %d %d %d %d %d %d Z" % (cx - 18, cy - 12, cx - 40, cy - 24, cx - 50, cy - 46, cx - 36, cy - 64,
          cx - 38, cy - 46, cx - 24, cy - 32, cx - 4, cy - 20), HORN, 4)
    s += LN("M %d %d Q %d %d %d %d" % (cx - 26, cy - 22, cx - 38, cy - 34, cx - 38, cy - 50), HORN2, 2)
    # three overlapping rows of big scales
    for k in range(3):
        y = cy - 16 + k * 12
        w = 34 - k * 3
        d = "M %d %d Q %d %d %d %d L %d %d Q %d %d %d %d Z" % (cx - w - 4, y + 12, cx - 4, y - 14, cx + w - 2, y + 6, cx + w - 4, y + 14, cx - 4, y - 2, cx - w - 2, y + 20)
        s += P(d, (SCALE, SCALE2, SCALE)[k], 4)
        for j in range(4):
            x = cx - w + 8 + j * (2 * w - 10) / 3.0
            s += '<path d="M %.1f %.1f A 7 7 0 0 0 %.1f %.1f" fill="none" stroke="%s" stroke-width="2"/>' % (x - 7, y + 4 + abs(j - 1.5) * 2, x + 7, y + 4 + abs(j - 1.5) * 2, SCALE3)
    s += LN("M %d %d Q %d %d %d %d" % (cx - 36, cy + 16, cx - 4, cy + 28, cx + 28, cy + 14), BELLY, 5) + LN("M %d %d Q %d %d %d %d" % (cx - 36, cy + 16, cx - 4, cy + 28, cx + 28, cy + 14), INK, 1.5)
    s += GEM(cx - 6, cy + 2, 6, BOLT)
    return BOTH(s)

def pauldron_bolts(rnd, k):
    cx, cy = SH_C
    tip = (cx - 36, cy - 62)
    end = [(cx - 50, cy - 20), (cx - 24, cy - 30), (cx - 44, cy - 6)][k]
    return BOTH(bolt(rnd, tip[0], tip[1], end[0], end[1], n=4, jag=5, w=2.6) + blur(CI(cx - 6, cy + 2, 9, BOLT, 0)))

# ---------------------------------------------------------------- chest (body space)
VEINS = ["M 128 150 L 112 138 L 100 142 L 86 128", "M 128 150 L 144 138 L 156 142 L 170 128",
         "M 128 150 L 108 162 L 96 158 L 80 176", "M 128 150 L 148 162 L 160 158 L 176 176",
         "M 128 150 L 122 170 L 130 182 L 124 196"]
def chest():
    s = P(BODY_OUT, SCALE, 5)
    s += scales(62, 120, 196, 214, 8, SCALE2, SCALE3, clip="chestclip")
    # gold belly plates down the middle
    for k, y in enumerate(range(124, 200, 15)):
        w = 18 - abs(k - 2) * 1.5
        s += P("M %.1f %d Q 128 %d %.1f %d L %.1f %d Q 128 %d %.1f %d Z" % (128 - w, y + 4, y - 4, 128 + w, y + 4, 128 + w - 2, y + 15, y + 9, 128 - w + 2, y + 15), BELLY, 3)
    for d in VEINS: s += LN(d, INK, 7) + LN(d, "#2b5a77", 3.5)
    s += CI(128, 150, 14, SCALE2, 4.5) + CI(128, 150, 8, BOLT, 0) + CI(125, 147, 2.5, "#ffffff", 0)
    s += RC(60, 198, 136, 14, SCALE2, 4, 4) + "".join(P("M %d 199 L %d 211 L %d 199 Z" % (x - 4, x, x + 4), HORN, 2) for x in (72, 90, 166, 184)) + RC(116, 196, 24, 18, BELLY, 4, 4)
    return s

def chest_mask():
    return "".join(LN(d, "#ffffff", 4) for d in VEINS) + CI(128, 150, 9, "#ffffff", 0)

def chest_core():
    return blur(CI(128, 150, 18, BOLT, 0)) + CI(128, 150, 7, BOLTL, 0)

# ---------------------------------------------------------------- cape (side drapes with a spiny dorsal edge)
def cape_spines():
    out = []
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=9)
        sgn = -1 if pts[0][0] < 128 else 1
        for i in range(1, 9):
            (x, y), (x2, y2) = pts[i], pts[i + 1]
            L = 14 + 6 * math.sin(i * 0.8)
            out.append(((x, y), (x2, y2), sgn, L))
    return out

def cape():
    s = ""
    for (x, y), (x2, y2), sgn, L in cape_spines():
        tx, ty = (x + x2) / 2 + sgn * L, (y + y2) / 2 - 4
        s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x, y, tx, ty, x2, y2), SCALE3, 3.5)
    s += "".join(P(p, SCALE, 5) for p in DRAPE_OUT) + "".join(P(p, "#5a2230", 3) for p in DRAPE_IN)
    s += '<clipPath id="brsdrape"><path d="%s"/><path d="%s"/></clipPath>' % DRAPE_OUT
    s += scales(26, 110, 230, 214, 8, SCALE2, SCALE3, clip="brsdrape")
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        d = "M " + " L ".join("%.1f %.1f" % (x + (5 if x < 128 else -5), y) for x, y in pts)
        s += LN(d, BELLY, 4)
    return s

def cape_bolts(rnd, k):
    s = ""
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        sgn = -1 if pts[0][0] < 128 else 1
        i = 1 + (k * 3 + (2 if sgn > 0 else 0)) % 5
        (x, y), (x2, y2) = pts[i], pts[i + 3]
        s += bolt(rnd, x + sgn * 10, y, x2 + sgn * 12, y2, n=4, jag=6, w=2.8)
    return s

# ---------------------------------------------------------------- glaive (right paw)
FANG = "M -8 -118 C -20 -150 -6 -184 14 -200 C 10 -176 18 -146 10 -118 Z"
def glaive():
    s = RC(-5, -118, 10, 156, SCALE2, 4, 4)
    for y in (-90, -50, -10): s += RC(-8, y, 16, 9, BELLY, 3, 3)
    s += CI(0, 40, 7, BELLY, 3.5)
    s += P(FANG, HORN, 5) + P("M -4 -120 C -14 -150 -2 -180 12 -196 C 0 -170 -2 -146 2 -120 Z", "#ffffff", 0, ' opacity=".55"')
    s += LN("M 4 -124 C 8 -150 8 -170 12 -192", HORN2, 2)
    # the dragon-head socket holding the fang
    s += P("M -16 -104 Q -18 -124 0 -128 Q 18 -124 16 -104 Q 0 -96 -16 -104 Z", SCALE, 4.5)
    for sx in (-1, 1): s += P("M %d -122 L %d -136 L %d -124 Z" % (sx * 8, sx * 22, sx * 14), HORN, 2.5)
    s += EL(-6, -114, 3.5, 2.5, EYE, 2) + EL(6, -114, 3.5, 2.5, EYE, 2) + GEM(0, -104, 4.5, BOLT)
    return RHAND(s)

def glaive_mask():
    return RHAND(P(FANG, "#ffffff", 0))

def glaive_bolts(rnd, k):
    s = bolt(rnd, 12, -198, [30, 40, 24][k], [-150, -176, -126][k], n=4, jag=6, w=2.8)
    s += bolt(rnd, -6, -150, [-30, -24, -36][k], [-168, -128, -150][k], n=3, jag=5, w=2.4)
    return RHAND(s + blur(CI(0, -104, 8, BOLT, 0)))

# ---------------------------------------------------------------- aura: thunderstorm
def ground_arcs(rnd, k):
    s = blur('<ellipse cx="128" cy="214" rx="110" ry="14" fill="%s" opacity=".55"/>' % STORM)
    for i in range(3):
        a0 = rnd.uniform(0, math.pi)
        x0, y0 = 128 + math.cos(a0) * 108, 212 + math.sin(a0) * 12
        x1, y1 = x0 + rnd.choice((-1, 1)) * rnd.uniform(30, 50), 212 + rnd.uniform(-8, 6)
        x0, x1 = min(240, max(16, x0)), min(240, max(16, x1))
        s += bolt(rnd, x0, y0, x1, y1, n=4, jag=7, w=2.8)
    side = -1 if k % 2 == 0 else 1
    x = 128 + side * rnd.uniform(92, 104)
    s += bolt(rnd, x + side * 10, 96, x, 210, n=6, jag=9, w=3.2)   # a strike beside the cat
    return s

def mini_bolt():
    return sprite(P("M 3 -13 L -6 2 L 0 2 L -3 13 L 7 -3 L 1 -3 L 4 -13 Z", "#ffffff", 2.4))

SET = {
    "key": "brs", "name": "Blackrock Spire", "zone": "brs", "lua": "BlackrockSpire", "file": "blackrock_spire",
    "about": "Blackrock Spire set: a storm dragon, black scale and crackling lightning, each piece guaranteed from one Blackrock Spire boss in Adventure until owned.",
    "preview_fur": "fur_cream",
    "pieces": [
        {"id": "set_brs_helm", "slot": "head", "kind": "head", "art": "brs_helm", "name": "Drakkisath's Stormwing Helm", "rarity": 5,
         "icon": "INV_Helmet_18", "boss": "General Drakkisath", "word": "helm",
         "svg": helm(), "layers": dict(frames(4, helm_bolts), eyes=helm_eyes()),
         "anim": [
             {"kind": "flip", "keys": [K("brs_helm", "fl%d" % i) for i in range(1, 5)], "fps": 11},
             {"kind": "pulse", "key": K("brs_helm", "eyes"), "a": [0.3, 1.0], "speed": 3.2, "blend": "ADD", "flicker": True},
             {"kind": "particles", "sprite": "a_spark", "n": 5, "box": [100, 10, 412, 120], "vx": [-20, 20], "vy": [-40, -10], "life": [0.4, 0.8],
              "size": [10, 16], "color": BOLTC, "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_brs_shoulders", "slot": "shoulder", "kind": "shoulder", "art": "brs_shoulders", "name": "The Beast's Horned Scale Pauldrons", "rarity": 4,
         "icon": "INV_Shoulder_01", "boss": "The Beast", "word": "shoulders",
         "svg": pauldron(), "layers": frames(3, pauldron_bolts),
         "anim": [
             {"kind": "flip", "keys": [K("brs_shoulders", "fl%d" % i) for i in range(1, 4)], "fps": 10},
             {"kind": "glint", "sprite": "a_spark", "n": 2, "spots": [[40, 120, 110, 220], [402, 120, 472, 220]], "size": [16, 24],
              "gap": [0.3, 1.0], "color": BOLTC, "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_brs_chest", "slot": "chest", "kind": "chest", "art": "brs_chest", "name": "Wyrmthalak's Stormscale Plate", "rarity": 4,
         "icon": "INV_Chest_Chain_15", "boss": "Overlord Wyrmthalak", "word": "chest",
         "svg": chest(), "layers": {"mask": chest_mask(), "core": chest_core()},
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K("brs_chest", "mask"), "scale": 50, "vx": 70, "vy": 30, "color": BOLTC, "blend": "ADD"},
             {"kind": "pulse", "key": K("brs_chest", "core"), "a": [0.2, 1.0], "speed": 3.0, "blend": "ADD", "flicker": True},
         ]},
        {"id": "set_brs_cape", "slot": "back", "kind": "back", "art": "brs_cape", "name": "Gyth's Spined Drape", "rarity": 4,
         "icon": "INV_Misc_Cape_06", "boss": "Warchief Rend Blackhand", "word": "cape",
         "svg": cape(), "layers": frames(3, cape_bolts),
         "anim": [
             {"kind": "flip", "keys": [K("brs_cape", "fl%d" % i) for i in range(1, 4)], "fps": 9},
         ]},
        {"id": "set_brs_glaive", "slot": "main", "kind": "weapon", "art": "brs_glaive", "name": "Voone's Thunderfang Glaive", "rarity": 5,
         "icon": "INV_Spear_08", "boss": "War Master Voone", "word": "glaive",
         "svg": glaive(), "layers": dict(frames(3, glaive_bolts), mask=glaive_mask()),
         "anim": [
             {"kind": "flip", "keys": [K("brs_glaive", "fl%d" % i) for i in range(1, 4)], "fps": 10},
             {"kind": "scroll", "sprite": "a_shine", "mask": K("brs_glaive", "mask"), "scale": 70, "vx": 20, "vy": -60, "color": BOLTC, "blend": "ADD"},
         ]},
        {"id": "set_brs_aura", "slot": "effect", "kind": "effect", "art": "fx_brs_storm", "name": "Valthalak's Thunderstorm", "rarity": 4,
         "icon": "Spell_Nature_Lightning", "boss": "Lord Valthalak", "word": "aura", "glow": (0.55, 0.6, 1.0),
         "fx": {"layer": "back", "anim": "flicker"},
         "layers": dict(frames(4, ground_arcs), bolt=mini_bolt()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [0.5, 0.45, 1.0], "a": [0.2, 0.55], "speed": 2.4, "blend": "ADD", "flicker": True, "at": "behind"},
             {"kind": "flip", "keys": [K("fx_brs_storm", "fl%d" % i) for i in range(1, 5)], "fps": 7, "at": "front"},
             {"kind": "particles", "sprite": "k_fx_brs_storm_bolt", "n": 4, "box": [60, 200, 452, 440], "vx": [-8, 8], "vy": [-50, -30], "life": [0.8, 1.4],
              "size": [16, 24], "spin": [-0.5, 0.5], "color": [0.75, 0.95, 1.0], "at": "behind"},
             {"kind": "particles", "sprite": "a_spark", "n": 6, "box": [60, 380, 452, 470], "vx": [-30, 30], "vy": [-60, -20], "life": [0.4, 0.8],
              "size": [8, 14], "color": BOLTC, "blend": "ADD", "at": "front"},
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
