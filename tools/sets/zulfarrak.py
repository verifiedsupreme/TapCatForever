"""Zul'Farrak set (1.6): sun and sand. A striped gold-and-turquoise headdress under a blazing sun whose
rays turn behind the head, a scarab collar, a dune veil shedding sand, a sun staff, and a sandstorm
swirling around the cat. Each piece is guaranteed from one Zul'Farrak boss in Adventure until owned.
  python3 tools/sets/zulfarrak.py            -> Art/v/k_zf_*.tga, Art/zf_*.tga, Sets/ZulFarrak.lua
  python3 tools/set_preview.py tools/sets/zulfarrak.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: sandstone, sun gold, turquoise, lapis
SAND, SAND2, SAND3 = "#e9c27c", "#c8974e", "#f7dfaa"
GOLD, GOLD2, GOLDL = "#ffc632", "#e0921a", "#fff0a0"
TURQ, TURQ2, TURQL = "#2ec4b4", "#16877e", "#9af2e6"
LAPIS, SUNO, SUNC = "#2f5fc4", "#ff9f22", "#fff4b8"
TROLLRED = "#d8483a"

def frames(n, fn):
    return {"fl%d" % (k + 1): fn(k) for k in range(n)}

def blur(s): return '<g filter="url(#blur)">%s</g>' % s

def sunburst(cx, cy, r, n, k, up_room=None, long_=1.75, short=1.4, ink=4, lower=True):
    """a blazing sun: n pointed rays (alternating long and short) turned by frame k, then the disc"""
    s = ""
    step = 360.0 / n
    for i in range(n):
        a = math.radians(i * step + k * step / 4.0)      # 0 = up
        if not lower and math.cos(a) < -0.35: continue
        L = r * (long_ if i % 2 == 0 else short)
        if up_room and math.cos(a) > 0: L = min(L, up_room / max(0.2, math.cos(a)))
        w = math.radians(step * 0.4)
        p = lambda ang, rr: (cx + math.sin(ang) * rr, cy - math.cos(ang) * rr)
        s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (p(a - w, r * 0.9) + p(a, L) + p(a + w, r * 0.9)), GOLD if i % 2 == 0 else SUNO, ink * 0.85)
    s += CI(cx, cy, r, SUNO, ink) + CI(cx, cy, r * 0.78, GOLD, 0) + CI(cx, cy, r * 0.5, SUNC, 0)
    # flares turning on the sun's face
    for j in range(3):
        a = math.radians(j * 120 + k * 30)
        s += EL(cx + math.sin(a) * r * 0.55, cy - math.cos(a) * r * 0.55, r * 0.16, r * 0.09, GOLDL, 0, math.degrees(a) + 90)
    return s

# ---------------------------------------------------------------- headdress (head space)
NEMES = ("M 52 94 Q 40 22 128 18 Q 216 22 204 94 L 226 170 Q 208 182 190 176 L 184 106 Q 128 94 72 106 "
         "L 66 176 Q 48 182 30 170 Z")
def helm():
    clip = '<defs><clipPath id="zfnemes"><path d="%s"/></clipPath></defs>' % NEMES
    s = clip + P(NEMES, GOLD, 5)
    stripes = ""
    for k in range(-2, 12):
        y = 30 + k * 15
        stripes += '<path d="M 0 %d Q 128 %d 256 %d L 256 %d Q 128 %d 0 %d Z" fill="%s"/>' % (y, y - 26, y, y + 7, y - 19, y + 7, TURQ)
    s += '<g clip-path="url(#zfnemes)">%s</g>' % stripes
    s += P(NEMES, "none", 5)
    s += LN("M 66 60 Q 84 34 120 28", SAND3, 5)
    # gold brow band with turquoise inlays
    band = "M 60 108 Q 128 92 196 108 L 194 92 Q 128 76 62 92 Z"
    s += P(band, GOLD, 5)
    for x in (76, 98, 158, 180): s += RC(x - 5, 92 - abs(x - 128) * 0.05 - 4, 10, 10, TURQ, 2, 2.5)
    # winged scarab at the brow
    wing = "M 124 80 Q 100 62 82 70 Q 92 76 90 82 Q 104 80 124 88 Z"
    s += P(wing, GOLD, 3.5) + mirror(P(wing, GOLD, 3.5), 128)
    s += EL(128, 80, 11, 14, TURQ, 3.5) + LN("M 128 68 L 128 92", TURQ2, 2) + CI(128, 64, 5, LAPIS, 2.5)
    s += CI(124, 76, 2.5, TURQL, 0)
    # a small sun on the crown of the head
    s += CI(128, 36, 9, SUNO, 3.5) + CI(128, 36, 5, SUNC, 0)
    return HEAD(s)

def helm_sun(k):
    return HEAD(sunburst(128, 62, 58, 16, k, up_room=72, long_=2.15, short=1.7))

def helm_corona():
    return HEAD(blur(EL(128, 66, 104, 54, SUNO, 0)) + blur(EL(128, 62, 64, 44, GOLDL, 0)))

# ---------------------------------------------------------------- shoulders (body space)
def scales(cx, cy):
    s = ""
    rows = [(cy - 20, 4, 30), (cy - 11, 5, 36), (cy - 2, 6, 40), (cy + 7, 6, 42)]
    for r, (y, n, half) in reversed(list(enumerate(rows))):
        for i in range(n):
            x = cx - half + (2 * half) * (i + 0.5) / n + (4 if r % 2 else 0)
            d = "M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" % (x - 9, y - 4, x - 9, y + 11, x, y + 13, x + 9, y + 11, x + 9, y - 4)
            s += P(d, TURQ if (i + r) % 2 == 0 else TURQ2, 3)
            s += LN("M %.1f %.1f Q %.1f %.1f %.1f %.1f" % (x - 4, y, x - 4, y + 6, x, y + 8), TURQL, 1.8)
    return s

def pauldron():
    cx, cy = SH_C
    s = ""
    for dx, a, L in ((-28, -52, 30), (-8, -20, 36), (14, 10, 26)):
        x, y = cx + dx, cy - 14
        s += P("M %d %d Q %.1f %.1f %.1f %.1f Q %.1f %.1f %d %d Z" % (x - 11, y + 8, x - 6 + math.sin(math.radians(a)) * L * 0.5, y - math.cos(math.radians(a)) * L * 0.5,
               x + math.sin(math.radians(a)) * L, y - math.cos(math.radians(a)) * L, x + 6 + math.sin(math.radians(a)) * L * 0.4, y - math.cos(math.radians(a)) * L * 0.4, x + 11, y + 8), GOLD, 4)
    dome = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 32, cy + 8, cx + 28, cy - 24, cx - 4, cy - 24,
        cx - 38, cy - 22, cx - 40, cy + 12, cx - 4, cy + 24, cx + 32, cy + 8)
    s += P(dome, TURQ2, 5)
    s += '<g clip-path="url(#zfdome)">%s</g>' % scales(cx - 3, cy)
    s = '<defs><clipPath id="zfdome"><path d="%s"/></clipPath></defs>' % dome + s + P(dome, "none", 5)
    rim = "M %d %d Q %d %d %d %d" % (cx - 38, cy + 8, cx - 6, cy + 22, cx + 30, cy + 6)
    s += LN(rim, INK, 11) + LN(rim, GOLD, 7) + LN(rim, GOLDL, 2)
    s += CI(cx - 4, cy - 2, 8, SUNO, 3) + CI(cx - 4, cy - 2, 4.5, SUNC, 0)
    return BOTH(s)

def pauldron_mask():
    cx, cy = SH_C
    dome = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 32, cy + 8, cx + 28, cy - 24, cx - 4, cy - 24,
        cx - 38, cy - 22, cx - 40, cy + 12, cx - 4, cy + 24, cx + 32, cy + 8)
    return BOTH(P(dome, "#ffffff", 0))

# ---------------------------------------------------------------- chest (body space)
COLLAR_ROWS = [(0, GOLD), (1, TURQ), (2, LAPIS), (3, GOLD), (4, TURQ)]
def collar_band(i):
    """one row of the broad collar: an arc from shoulder to shoulder"""
    r0, r1 = 26 + i * 8, 34 + i * 8
    cx, cy = 128, 112
    a0, a1 = math.radians(20), math.radians(160)
    p = lambda a, r: (cx + math.cos(a) * r * 1.55, cy + math.sin(a) * r)
    return "M %.1f %.1f A %.1f %.1f 0 0 1 %.1f %.1f L %.1f %.1f A %.1f %.1f 0 0 0 %.1f %.1f Z" % (
        p(a0, r1) + (r1 * 1.55, r1) + p(a1, r1) + p(a1, r0) + (r0 * 1.55, r0) + p(a0, r0))

def chest():
    s = P(BODY_OUT, SAND, 5)
    s += LN("M 98 168 L 94 212", SAND2, 3) + LN("M 158 168 L 162 212", SAND2, 3) + LN("M 128 176 L 128 212", SAND2, 3)
    s += '<defs><clipPath id="zfbody"><path d="%s"/></clipPath></defs>' % BODY_OUT
    col = ""
    for i, c in COLLAR_ROWS: col += P(collar_band(i), c, 3)
    for i in (1, 3):
        r = 30 + i * 8
        for j in range(9):
            a = math.radians(30 + j * 15)
            col += CI(128 + math.cos(a) * r * 1.55, 112 + math.sin(a) * r, 2.2, GOLDL, 0)
    s += '<g clip-path="url(#zfbody)">%s</g>' % col
    # winged scarab with the sun
    wing = "M 122 176 Q 98 166 78 176 Q 90 180 88 186 Q 104 184 122 188 Z"
    s += P(wing, GOLD, 4) + mirror(P(wing, GOLD, 4), 128)
    s += LN("M 86 180 Q 104 176 120 180", GOLD2, 2) + mirror(LN("M 86 180 Q 104 176 120 180", GOLD2, 2), 128)
    s += EL(128, 186, 11, 14, TURQ, 4) + LN("M 128 174 L 128 198", TURQ2, 2)
    s += CI(128, 166, 9, SUNO, 3.5) + CI(128, 166, 5, SUNC, 0)
    s += RC(58, 200, 140, 12, GOLD, 4, 4) + "".join(RC(x - 4, 202, 8, 8, TURQ, 2, 2) for x in (80, 104, 152, 176))
    return s

def chest_mask():
    return '<defs><clipPath id="zfbody"><path d="%s"/></clipPath></defs><g clip-path="url(#zfbody)">%s</g>' % (
        BODY_OUT, "".join(P(collar_band(i), "#ffffff", 0) for i, _ in COLLAR_ROWS))

def chest_sun():
    return blur(CI(128, 166, 16, GOLDL, 0)) + CI(128, 166, 5, "#ffffff", 0)

# ---------------------------------------------------------------- cape (side drapes)
def cape():
    s = "".join(P(p, SAND, 5) for p in DRAPE_OUT) + "".join(P(p, TURQ2, 3) for p in DRAPE_IN)
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        sg = 1 if pts[0][0] < 128 else -1
        for off, col, w in ((7, TROLLRED, 4), (13, TURQ, 4), (18, GOLD, 3)):
            d = "M " + " L ".join("%.1f %.1f" % (x + sg * off, y) for x, y in pts[1:])
            s += LN(d, col, w)
        # little troll diamonds
        for x, y in pts[2:7:2]:
            x += sg * 13
            s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x, y - 5, x + 4, y, x, y + 5, x - 4, y), GOLD, 1.8)
    return s

def cape_fringe(k):
    """the tattered hem along the outer edges, fluttering in the wind"""
    rnd = random.Random(300 + k)
    s = ""
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=9)
        sg = -1 if pts[0][0] < 128 else 1
        for i, (x, y) in enumerate(pts[2:]):
            L = 9 + i * 1.2 + rnd.random() * 5
            ang = math.radians(sg * (75 + rnd.random() * 30))
            tx, ty = x + math.sin(ang) * L, y + math.cos(ang) * L * 0.5 + 3
            bend = (rnd.random() - 0.5) * 10
            mx, my = (x + tx) / 2, (y + ty) / 2 + bend
            s += P("M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" % (x, y - 6, mx, my - 5, tx, ty, mx, my + 4, x, y + 6),
                   SAND if i % 2 else SAND3, 2.5)
    return s

# ---------------------------------------------------------------- sun staff (right paw)
ORB = (0, -150)
def staff():
    s = RC(-5, -128, 10, 166, "#8a5a32", 4, 4)
    s += LN("M -2 -120 L -2 30", "#a87444", 2)
    for y in (-110, -64, -18): s += RC(-8, y, 16, 9, GOLD, 3, 3)
    for y in (-88, -40): s += CI(0, y, 5, TURQ, 2.5)
    s += CI(0, 40, 6, GOLD, 3)
    # gold horns holding the sun
    horn = "M -4 -124 Q -34 -130 -30 -170 Q -22 -146 -6 -140 Z"
    s += P(horn, GOLD, 4) + mirror(P(horn, GOLD, 4), 0)
    # troll feathers
    for x, col in ((-24, TROLLRED), (24, TURQ)):
        s += P("M %d -138 Q %d -112 %d -100 Q %d -114 %d -138 Z" % (x, x - 6, x, x + 6, x), col, 3)
    return RHAND(s)

def staff_sun(k):
    return RHAND(sunburst(ORB[0], ORB[1], 15, 12, k, long_=1.9, short=1.5, ink=3.5))

def staff_glow():
    return RHAND(blur(CI(ORB[0], ORB[1], 30, SUNO, 0)) + blur(CI(ORB[0], ORB[1], 16, GOLDL, 0)))

# ---------------------------------------------------------------- aura: sandstorm
def storm_mask():
    return '<ellipse cx="128" cy="150" rx="104" ry="64" fill="none" stroke="#ffffff" stroke-width="40"/>'

SANDC = [1.0, 0.82, 0.5]
SET = {
    "key": "zf", "name": "Zul'Farrak", "zone": "zf", "lua": "ZulFarrak", "file": "zulfarrak",
    "about": "Zul'Farrak set: sun and sand, each piece guaranteed from one Zul'Farrak boss in Adventure until owned.",
    "preview_fur": "fur_midnight",
    "pieces": [
        {"id": "set_zf_helm", "slot": "head", "kind": "head", "art": "zf_helm", "name": "Sandscalp's Sun Crown", "rarity": 5,
         "icon": "INV_Helmet_51", "boss": "Chief Ukorz Sandscalp", "word": "headdress",
         "svg": helm(), "layers": dict(frames(4, helm_sun), corona=helm_corona()),
         "anim": [
             {"kind": "pulse", "key": K("zf_helm", "corona"), "a": [0.35, 0.85], "speed": 1.8, "blend": "ADD", "flicker": True, "at": "behind"},
             {"kind": "flip", "keys": [K("zf_helm", "fl%d" % i) for i in range(1, 5)], "fps": 6, "at": "behind"},
             {"kind": "glint", "sprite": "a_spark", "n": 2, "spots": [[150, 60, 362, 120]], "size": [18, 26], "gap": [0.4, 1.2],
              "color": [1, 0.92, 0.6], "blend": "ADD", "at": "front"},
             {"kind": "particles", "sprite": "a_ember", "n": 5, "box": [150, 0, 362, 60], "vx": [-10, 10], "vy": [-30, -12], "life": [1.0, 1.6],
              "size": [10, 16], "color": [1, 0.85, 0.4], "blend": "ADD", "at": "behind"},
         ]},
        {"id": "set_zf_shoulders", "slot": "shoulder", "kind": "shoulder", "art": "zf_shoulders", "name": "Gahz'rilla Scale Spaulders", "rarity": 4,
         "icon": "INV_Shoulder_14", "boss": "Gahz'rilla", "word": "shoulders",
         "svg": pauldron(), "layers": {"mask": pauldron_mask()},
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K("zf_shoulders", "mask"), "scale": 90, "vx": 40, "vy": 0, "color": [0.7, 1.0, 0.95], "blend": "ADD", "alpha": 0.8},
             {"kind": "glint", "sprite": "a_spark", "n": 2, "spots": [[60, 190, 140, 250], [372, 190, 452, 250]], "size": [16, 24],
              "gap": [0.5, 1.4], "color": [1, 0.92, 0.6], "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_zf_chest", "slot": "chest", "kind": "chest", "art": "zf_chest", "name": "Antu'sul's Scarab Collar", "rarity": 4,
         "icon": "INV_Chest_Leather_06", "boss": "Antu'sul", "word": "chest",
         "svg": chest(), "layers": {"mask": chest_mask(), "sun": chest_sun()},
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K("zf_chest", "mask"), "scale": 90, "vx": 50, "vy": 0, "color": [1, 0.92, 0.65], "blend": "ADD", "alpha": 0.8},
             {"kind": "pulse", "key": K("zf_chest", "sun"), "a": [0.2, 1.0], "speed": 2.2, "blend": "ADD"},
         ]},
        {"id": "set_zf_cape", "slot": "back", "kind": "back", "art": "zf_cape", "name": "Sezz'ziz's Dune Veil", "rarity": 4,
         "icon": "INV_Misc_Cape_14", "boss": "Shadowpriest Sezz'ziz", "word": "cape",
         "svg": cape(), "layers": frames(3, cape_fringe),
         "anim": [
             {"kind": "flip", "keys": [K("zf_cape", "fl%d" % i) for i in range(1, 4)], "fps": 7},
             {"kind": "particles", "sprite": "a_spark", "n": 5, "box": [30, 280, 90, 430], "vx": [-60, -30], "vy": [-10, 10], "life": [0.8, 1.4],
              "size": [6, 10], "color": SANDC, "sway": 6, "at": "behind"},
             {"kind": "particles", "sprite": "a_spark", "n": 5, "box": [422, 280, 482, 430], "vx": [30, 60], "vy": [-10, 10], "life": [0.8, 1.4],
              "size": [6, 10], "color": SANDC, "sway": 6, "at": "behind"},
         ]},
        {"id": "set_zf_staff", "slot": "main", "kind": "weapon", "art": "zf_staff", "name": "Zum'rah's Sunstaff", "rarity": 5,
         "icon": "INV_Staff_11", "boss": "Witch Doctor Zum'rah", "word": "staff",
         "svg": staff(), "layers": dict(frames(4, staff_sun), glow=staff_glow()),
         "anim": [
             {"kind": "pulse", "key": K("zf_staff", "glow"), "a": [0.25, 0.85], "speed": 2.4, "blend": "ADD", "flicker": True},
             {"kind": "flip", "keys": [K("zf_staff", "fl%d" % i) for i in range(1, 5)], "fps": 7},
         ]},
        {"id": "set_zf_aura", "slot": "effect", "kind": "effect", "art": "fx_zf_storm", "name": "Dustwraith's Sandstorm", "rarity": 4,
         "icon": "Spell_Nature_Cyclone", "boss": "Dustwraith", "word": "aura", "glow": (1.0, 0.78, 0.4),
         "fx": {"layer": "back", "anim": "spinslow"},
         "layers": {"ring": storm_mask()},
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [1.0, 0.7, 0.3], "a": [0.2, 0.45], "speed": 1.4, "blend": "ADD", "at": "behind"},
             {"kind": "scroll", "sprite": "a_swirl", "mask": K("fx_zf_storm", "ring"), "scale": 120, "vx": 110, "vy": 8, "color": [1.0, 0.85, 0.55], "alpha": 0.9, "at": "behind"},
             {"kind": "particles", "sprite": "a_spark", "n": 8, "box": [20, 220, 200, 470], "vx": [80, 140], "vy": [-20, 10], "life": [1.0, 1.8],
              "size": [6, 11], "color": SANDC, "sway": 10, "at": "front"},
             {"kind": "particles", "sprite": "a_spark", "n": 8, "box": [60, 160, 452, 470], "vx": [70, 120], "vy": [-25, 5], "life": [1.2, 2.0],
              "size": [7, 12], "color": [0.95, 0.75, 0.45], "sway": 12, "at": "behind"},
             {"kind": "particles", "sprite": "a_glow", "n": 4, "box": [40, 300, 300, 470], "vx": [50, 90], "vy": [-15, 5], "life": [1.6, 2.4],
              "size": [40, 64], "color": [0.9, 0.7, 0.45], "alpha": 0.35, "grow": 0.8, "at": "behind"},
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
