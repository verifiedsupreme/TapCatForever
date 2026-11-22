"""Dire Maul set (1.6): the Highborne night sky. Moonsilver and deep night blue with the galaxy inside: a
great crescent-moon crown full of drifting stars and nebula, a starweave robe, a nebula drape, an orrery
staff with little planets circling its orb, and stars falling around the cat. Each piece is guaranteed
from one Dire Maul boss in Adventure until owned.
  python3 tools/sets/dire_maul.py            -> Art/v/k_dim_*.tga, Art/dim_*.tga, Sets/DireMaul.lua
  python3 tools/set_preview.py tools/sets/dire_maul.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: deep night, moonsilver, arcane violet, star gold
NIGHT, NIGHT2, NIGHT3 = "#1b1d4e", "#2b2f78", "#4048a8"
SILVER, SILVER2, SILVERL = "#cfd6ee", "#9aa4c8", "#f4f6ff"
ARC, ARCL, ARCD = "#b07cff", "#efdcff", "#6b3fc4"
STAR = "#ffe9a0"
ARCC = [0.75, 0.55, 1.0]
STARC = [1.0, 0.92, 0.65]

def frames(n, fn):
    return {"fl%d" % (k + 1): fn(k) for k in range(n)}

# a blur whose region is the whole canvas, so the glow of a small shape is never cut off into a box
WIDEBLUR = ('<defs><filter id="wblur" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1100" height="1100">'
            '<feGaussianBlur stdDeviation="5"/></filter></defs>')
def blur(s): return WIDEBLUR + '<g filter="url(#wblur)">%s</g>' % s

def sprite(inner, S=32):
    """a small particle sprite: the drawing centred in an exact S x S box (faint corner dots fix the crop)"""
    dots = '<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/><rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S)
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)

def star4(x, y, r, col=STAR, ink=0):
    d = "M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" % (
        x, y - r, x + r * .18, y - r * .18, x + r, y, x + r * .18, y + r * .18, x, y + r, x - r * .18, y + r * .18, x - r, y, x - r * .18, y - r * .18, x, y - r)
    return P(d, col, ink)

def crescent(cx, cy, R, dy, r):
    """a crescent with its horns up: the outer circle (cx, cy, R) minus a circle r raised by dy.
    Returns the path and the two horn tips."""
    cy2 = cy - dy
    y = (cy + cy2) / 2.0 - (R * R - r * r) / (2.0 * dy)
    dx = math.sqrt(max(0.0, R * R - (y - cy) ** 2))
    return ("M %.1f %.1f A %.1f %.1f 0 1 0 %.1f %.1f A %.1f %.1f 0 1 1 %.1f %.1f Z"
            % (cx - dx, y, R, R, cx + dx, y, r, r, cx - dx, y)), (cx - dx, y), (cx + dx, y)

# ---------------------------------------------------------------- crown (head space)
MOON, TIP_L, TIP_R = crescent(128, 24, 72, 20, 66)
def crown():
    s = LN(MOON, INK, 15) + LN(MOON, SILVER, 9) + LN(MOON, SILVERL, 2, .8) + P(MOON, NIGHT, 0)
    s += P("M 70 70 Q 128 108 186 70 Q 128 96 70 70 Z", NIGHT2, 0)
    # a few fixed bright stars and a constellation inside the crescent
    pts = [(74, 60), (92, 78), (114, 86), (142, 86), (164, 78), (182, 60)]
    s += LN("M " + " L ".join("%d %d" % p for p in pts), SILVER2, 1.2, .8)
    for i, (x, y) in enumerate(pts): s += star4(x, y, 5 if i % 2 else 3.5, STAR)
    # the silver filigree band along the bottom, a moonstone in the middle, little crescents on the horns
    s += LN("M 60 82 Q 128 122 196 82", INK, 10) + LN("M 60 82 Q 128 122 196 82", SILVER, 6) + LN("M 64 84 Q 128 120 192 84", SILVERL, 1.8)
    s += P("M 128 84 Q 146 98 128 118 Q 110 98 128 84 Z", SILVER, 4) + CI(128, 101, 8, ARC, 3) + CI(125, 98, 2.5, "#ffffff", 0)
    for (x, y), sg in ((TIP_L, -1), (TIP_R, 1)):
        s += CI(x - sg * 2, y + 4, 6, SILVERL, 3)
    return HEAD(s)

def crown_mask():
    return HEAD(P(MOON, "#ffffff", 0))

def crown_glow():
    s = blur(CI(128, 101, 12, ARC, 0)) + CI(128, 101, 4, ARCL, 0)
    pts = [(74, 60), (92, 78), (114, 86), (142, 86), (164, 78), (182, 60)]
    for i, (x, y) in enumerate(pts): s += blur(CI(x, y, 6, STAR, 0)) + star4(x, y, 7 if i % 2 else 5, "#ffffff")
    return HEAD(s)

def moon_orbit(k):
    """the full moon floating between the horns, two little planets circling it"""
    cx, cy = 128, 10
    s = blur(CI(cx, cy, 20, ARC, 0)) + CI(cx, cy, 13, SILVERL, 4) + CI(cx + 4, cy - 3, 3.5, SILVER, 0) + CI(cx - 4, cy + 4, 2.5, SILVER, 0)
    for i, (rx, ry, r, col) in enumerate(((30, 9, 4.5, ARC), (24, 7, 3.5, STAR))):
        a = math.radians(k * 90 + i * 140)
        x, y = cx + math.cos(a) * rx, cy + math.sin(a) * ry
        body = CI(x, y, r, col, 2.5)
        s = (s + body) if math.sin(a) > 0 else (body + s)
    return HEAD(s)

# ---------------------------------------------------------------- shoulders (body space)
FIN = "M %d %d Q %d %d %d %d Q %d %d %d %d Z"
def fin_path():
    cx, cy = SH_C
    return FIN % (cx - 30, cy - 4, cx - 54, cy - 30, cx - 38, cy - 62, cx - 40, cy - 34, cx - 10, cy - 18)

def pauldron():
    cx, cy = SH_C
    s = P(fin_path(), SILVER, 4)  # an upswept crescent fin
    s += LN("M %d %d Q %d %d %d %d" % (cx - 30, cy - 10, cx - 44, cy - 30, cx - 38, cy - 56), SILVERL, 2)
    dome = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 30, cy + 10, cx + 26, cy - 22, cx - 4, cy - 22,
        cx - 38, cy - 20, cx - 40, cy + 14, cx - 4, cy + 26, cx + 30, cy + 10)
    s += P(dome, SILVER, 5)
    inset = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 20, cy + 6, cx + 18, cy - 12, cx - 4, cy - 13,
        cx - 28, cy - 12, cx - 30, cy + 10, cx - 4, cy + 16, cx + 20, cy + 6)
    s += P(inset, NIGHT, 3)
    for x, y, r in ((cx - 18, cy - 2, 3.5), (cx + 8, cy - 4, 2.5), (cx - 4, cy + 8, 2.5)): s += star4(x, y, r, STAR)
    s += LN("M %d %d Q %d %d %d %d" % (cx - 38, cy + 12, cx - 4, cy + 26, cx + 28, cy + 10), SILVER2, 4)
    s += GEM(cx - 4, cy + 20, 5, ARC)
    return BOTH(s)

def pauldron_mask():
    cx, cy = SH_C
    inset = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 20, cy + 6, cx + 18, cy - 12, cx - 4, cy - 13,
        cx - 28, cy - 12, cx - 30, cy + 10, cx - 4, cy + 16, cx + 20, cy + 6)
    return BOTH(P(inset, "#ffffff", 0))

# ---------------------------------------------------------------- chest (body space)
CONST = [(98, 142), (114, 132), (134, 140), (150, 128), (160, 150), (142, 170), (112, 176), (96, 160)]
def chest():
    s = P(BODY_OUT, NIGHT, 5)
    s += P("M 76 116 Q 66 160 70 214 L 84 214 Q 80 160 92 120 Z", NIGHT2, 0) + mirror(P("M 76 116 Q 66 160 70 214 L 84 214 Q 80 160 92 120 Z", NIGHT2, 0), 128)
    # silver V collar and trim down the front
    s += LN("M 80 118 L 128 150 L 176 118", INK, 10) + LN("M 80 118 L 128 150 L 176 118", SILVER, 6)
    s += LN("M 128 150 L 128 198", INK, 8) + LN("M 128 150 L 128 198", SILVER, 4)
    s += LN("M " + " L ".join("%d %d" % p for p in CONST) + " Z", SILVER2, 1.4, .8)
    for i, (x, y) in enumerate(CONST): s += star4(x, y, 4.5 if i % 3 == 0 else 3, STAR)
    # belt with a crescent buckle
    s += RC(60, 198, 136, 14, SILVER2, 4, 4) + "".join(star4(x, 205, 4, STAR, 1.5) for x in (78, 100, 156, 178))
    m, _, _ = crescent(128, 206, 11, 6, 9)
    s += CI(128, 205, 12, NIGHT2, 3.5) + P(m, SILVERL, 2.5)
    return s

def chest_mask():
    return P(BODY_OUT, "#ffffff", 0)

def chest_glow():
    s = ""
    for i, (x, y) in enumerate(CONST): s += blur(CI(x, y, 6, STAR, 0)) + star4(x, y, 6 if i % 3 == 0 else 4.5, "#ffffff")
    return s

# ---------------------------------------------------------------- cape (side drapes)
def cape():
    s = "".join(P(p, NIGHT, 5) for p in DRAPE_OUT) + "".join(P(p, NIGHT2, 3) for p in DRAPE_IN)
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        d = "M " + " L ".join("%.1f %.1f" % (x + (5 if x < 128 else -5), y) for x, y in pts)
        s += LN(d, SILVER, 5) + LN(d, INK, 1.5)
        for i in (2, 4, 6):
            x, y = pts[i]
            s += star4(x + (5 if x < 128 else -5), y, 6, SILVERL, 2.5)
    return s

def cape_mask():
    return "".join(P(p, "#ffffff", 0) for p in DRAPE_OUT)

# ---------------------------------------------------------------- orrery staff (right paw)
ORB = (0, -160)
def staff():
    s = RC(-5, -140, 10, 176, SILVER2, 4, 4)
    for y in (-110, -66, -22): s += RC(-8, y, 16, 9, NIGHT2, 3, 3)
    s += CI(0, 38, 7, SILVER, 3.5)
    # the crescent cradle and the armillary rings
    m, _, _ = crescent(0, -150, 30, 12, 26)
    s += P(m, SILVER, 4)
    s += '<ellipse cx="0" cy="%d" rx="30" ry="10" fill="none" stroke="%s" stroke-width="7" transform="rotate(-20 0 %d)"/>' % (ORB[1], INK, ORB[1])
    s += '<ellipse cx="0" cy="%d" rx="30" ry="10" fill="none" stroke="%s" stroke-width="3.5" transform="rotate(-20 0 %d)"/>' % (ORB[1], SILVER, ORB[1])
    s += CI(ORB[0], ORB[1], 15, ARC, 4.5) + CI(ORB[0] - 4, ORB[1] - 5, 5, ARCL, 0) + CI(ORB[0] - 5, ORB[1] - 6, 2, "#ffffff", 0)
    return RHAND(s)

def staff_glow():
    return RHAND(blur(CI(ORB[0], ORB[1], 26, ARC, 0)) + CI(ORB[0], ORB[1], 8, ARCL, 0))

def staff_orbit(k):
    s = ""
    for i, (rx, ry, r, col, ph) in enumerate(((44, 14, 5.5, STAR, 0), (36, 24, 4.5, "#7fd8ff", 120), (50, 8, 4, ARCL, 240))):
        a = math.radians(k * 90 + ph)
        x, y = ORB[0] + math.cos(a) * rx, ORB[1] + math.sin(a) * ry
        s += CI(x, y, r, col, 2.5)
    return RHAND(s)

# ---------------------------------------------------------------- aura: starfall
def star_ring(k):
    """a ring of tiny stars circling the cat's middle"""
    s = ""
    for i in range(14):
        a = math.radians(i * 360 / 14.0 + k * 360 / 14.0 / 3)
        x, y = 128 + math.cos(a) * 118, 168 + math.sin(a) * 26
        if math.sin(a) < -0.2: continue      # the back half hides behind the cat: leave it out
        s += star4(x, y, 5 + 2 * (i % 2), STAR) + blur(CI(x, y, 4, ARC, 0))
    return s

def shoot():
    s = '<path d="M -14 -14 L 6 6" stroke="%s" stroke-width="3" stroke-linecap="round" opacity=".7"/>' % STAR
    return sprite(s + star4(7, 7, 8, "#ffffff", 2))

SET = {
    "key": "dim", "name": "Dire Maul", "zone": "dim", "lua": "DireMaul", "file": "dire_maul",
    "about": "Dire Maul set: moonsilver and the night sky, each piece guaranteed from one Dire Maul boss in Adventure until owned.",
    "preview_fur": "fur_snow",
    "pieces": [
        {"id": "set_dim_crown", "slot": "head", "kind": "head", "art": "dim_crown", "name": "Crown of the Endless Night", "rarity": 5,
         "icon": "INV_Crown_01", "boss": "Immol'thar", "word": "crown",
         "svg": crown(), "layers": dict(frames(4, moon_orbit), mask=crown_mask(), glow=crown_glow()),
         "anim": [
             {"kind": "scroll", "sprite": "a_nebula", "mask": K("dim_crown", "mask"), "scale": 140, "vx": 8, "vy": -4, "alpha": 0.85, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_stars", "mask": K("dim_crown", "mask"), "scale": 110, "vx": -14, "vy": 6, "blend": "ADD"},
             {"kind": "pulse", "key": K("dim_crown", "glow"), "a": [0.2, 1.0], "speed": 2.2, "blend": "ADD"},
             {"kind": "flip", "keys": [K("dim_crown", "fl%d" % i) for i in range(1, 5)], "fps": 4},
             {"kind": "glint", "sprite": "a_spark", "n": 3, "spots": [[150, 0, 220, 90], [292, 0, 362, 90], [200, 70, 312, 120]],
              "size": [16, 26], "gap": [0.3, 1.0], "color": STARC, "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_dim_shoulders", "slot": "shoulder", "kind": "shoulder", "art": "dim_shoulders", "name": "Tortheldrin's Moonsilver Mantle", "rarity": 4,
         "icon": "INV_Shoulder_02", "boss": "Prince Tortheldrin", "word": "shoulders",
         "svg": pauldron(), "layers": {"mask": pauldron_mask()},
         "anim": [
             {"kind": "scroll", "sprite": "a_nebula", "mask": K("dim_shoulders", "mask"), "scale": 90, "vx": 6, "vy": -4, "alpha": 0.8, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_stars", "mask": K("dim_shoulders", "mask"), "scale": 70, "vx": -10, "vy": 4, "blend": "ADD"},
             {"kind": "glint", "sprite": "a_spark", "n": 2, "spots": [[40, 120, 110, 220], [402, 120, 472, 220]], "size": [16, 24],
              "gap": [0.5, 1.4], "color": STARC, "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_dim_chest", "slot": "chest", "kind": "chest", "art": "dim_chest", "name": "Starweave Robe of Eldre'Thalas", "rarity": 4,
         "icon": "INV_Chest_Cloth_25", "boss": "Alzzin the Wildshaper", "word": "robe",
         "svg": chest(), "layers": {"mask": chest_mask(), "glow": chest_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_nebula", "mask": K("dim_chest", "mask"), "scale": 160, "vx": 5, "vy": -3, "alpha": 0.7, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_stars", "mask": K("dim_chest", "mask"), "scale": 120, "vx": -8, "vy": 4, "blend": "ADD"},
             {"kind": "pulse", "key": K("dim_chest", "glow"), "a": [0.15, 1.0], "speed": 1.8, "blend": "ADD"},
         ]},
        {"id": "set_dim_cape", "slot": "back", "kind": "back", "art": "dim_cape", "name": "Hydrospawn's Nebula Drape", "rarity": 4,
         "icon": "INV_Misc_Cape_16", "boss": "Hydrospawn", "word": "cape",
         "svg": cape(), "layers": {"mask": cape_mask()},
         "anim": [
             {"kind": "scroll", "sprite": "a_nebula", "mask": K("dim_cape", "mask"), "scale": 140, "vx": 0, "vy": -6, "alpha": 0.9, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_stars", "mask": K("dim_cape", "mask"), "scale": 100, "vx": 0, "vy": 10, "blend": "ADD"},
             {"kind": "glint", "sprite": "a_spark", "n": 2, "spots": [[30, 260, 100, 420], [412, 260, 482, 420]], "size": [14, 22],
              "gap": [0.4, 1.2], "color": STARC, "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_dim_staff", "slot": "main", "kind": "weapon", "art": "dim_staff", "name": "Mizzle's Orrery Staff", "rarity": 5,
         "icon": "INV_Staff_10", "boss": "Mizzle the Crafty", "word": "staff",
         "svg": staff(), "layers": dict(frames(4, staff_orbit), glow=staff_glow()),
         "anim": [
             {"kind": "pulse", "key": K("dim_staff", "glow"), "a": [0.2, 0.9], "speed": 2.4, "blend": "ADD"},
             {"kind": "flip", "keys": [K("dim_staff", "fl%d" % i) for i in range(1, 5)], "fps": 5},
             {"kind": "particles", "sprite": "a_spark", "n": 4, "box": [360, 30, 450, 110], "vx": [-10, 10], "vy": [-30, -10], "life": [0.8, 1.4],
              "size": [8, 14], "color": ARCC, "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_dim_aura", "slot": "effect", "kind": "effect", "art": "fx_dim_starfall", "name": "Gordok's Starfall", "rarity": 4,
         "icon": "Spell_Nature_StarFall", "boss": "King Gordok", "word": "aura", "glow": (0.7, 0.5, 1.0),
         "fx": {"layer": "back", "anim": "float"},
         "layers": dict(frames(3, star_ring), shoot=shoot()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [0.55, 0.4, 1.0], "a": [0.2, 0.5], "speed": 1.5, "blend": "ADD", "at": "behind"},
             {"kind": "flip", "keys": [K("fx_dim_starfall", "fl%d" % i) for i in range(1, 4)], "fps": 5, "at": "front"},
             {"kind": "particles", "sprite": "k_fx_dim_starfall_shoot", "n": 4, "box": [20, 0, 420, 120], "vx": [70, 100], "vy": [70, 100], "life": [1.2, 1.8],
              "size": [22, 30], "color": STARC, "at": "behind"},
             {"kind": "particles", "sprite": "t_star", "n": 6, "box": [60, 120, 452, 420], "vx": [-6, 6], "vy": [10, 30], "life": [1.4, 2.4],
              "size": [8, 14], "spin": [-1.5, 1.5], "color": STARC, "at": "front"},
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
