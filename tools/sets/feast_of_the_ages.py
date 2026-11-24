"""Feast of the Ages (1.7.0): the Cooking long-chase set. A towering gold-trimmed chef's toque with steam
curling off it, a chef's jacket under a wine-red apron with a golden embroidered crest, a giant golden
ladle brimming with bubbling broth, and an aura of little dishes, steam puffs and warm sparkles floating
up around the cat. Crafted by Cooking (ProfSets.lua); the whole set gives the title Master Chef.
  python3 tools/sets/feast_of_the_ages.py            -> Art/v/k_feast_*.tga, Art/feast_*.tga, Sets/FeastOfTheAges.lua
  python3 tools/set_preview.py tools/sets/feast_of_the_ages.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: starched white, royal gold, wine red, warm broth
WHITE, WHITE2, SHADE = "#fffdf6", "#f1eadc", "#ddd2c0"
GOLD, GOLD2, GOLDD, GOLDC = "#f2b93a", "#ffe08a", "#b98220", "#fff5cc"
WINE, WINE2, WINED = "#7d1f3f", "#a6345c", "#561230"
BROTH, BROTH2, BROTHC = "#f08a2a", "#ffc154", "#fff0b0"
CRUST, CRUST2, CRUSTD = "#e3a04e", "#f6c579", "#a8642a"
WARM3 = [1.0, 0.78, 0.35]

WIDEBLUR = ('<defs><filter id="wblur" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1100" height="1100">'
            '<feGaussianBlur stdDeviation="%s"/></filter></defs>')
def blur(s, sd=5): return WIDEBLUR % sd + '<g filter="url(#wblur)">%s</g>' % s

def sprite(inner, S=40):
    dots = '<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/><rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S)
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)

def rot(s, a, x, y): return '<g transform="rotate(%.1f %.1f %.1f)">%s</g>' % (a, x, y, s)
def H(x, y): return 2 * (128 + 0.8 * (x - 128)), 2 * (32 + 0.8 * (y - 28))
def B(x, y): return 2 * x, 2 * (y + 16)
def box(c, w, h): return [round(c[0] - w), round(c[1] - h), round(c[0] + w), round(c[1] + h)]
def frames(n, fn, name="fl"): return {"%s%d" % (name, k + 1): fn(k) for k in range(n)}

def star4(x, y, r, fill, ink=0):
    d = "M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" % (
        x, y - r, x + r * 0.18, y - r * 0.18, x + r, y, x + r * 0.18, y + r * 0.18, x, y + r, x - r * 0.18, y + r * 0.18, x - r, y, x - r * 0.18, y - r * 0.18, x, y - r)
    return P(d, fill, ink)

def cloud(circles, fill, ink=5):
    """circles merged into one puffy outlined shape"""
    return "".join(CI(x, y, r + ink / 2.0, INK, 0) for x, y, r in circles) + "".join(CI(x, y, r, fill, 0) for x, y, r in circles)

def spoon_fork(x, y, sc=1.0):
    """crossed golden spoon and fork (the cook's crest)"""
    sp = LN("M -9 11 L 7 -7", INK, 5.5) + LN("M -9 11 L 7 -7", GOLD2, 2.5) + EL(9, -9, 4, 6, GOLD2, 2, 45)
    fk = LN("M 9 11 L -6 -5", INK, 5.5) + LN("M 9 11 L -6 -5", GOLD2, 2.5)
    fk += P("M -4 -3 L -12 -11 M -6 -1 L -14 -9 M -8 1 L -15 -6", "none", 0) + LN("M -5 -4 L -11 -10 M -7 -2 L -13 -8 M -9 0 L -14 -5", INK, 2.2)
    return '<g transform="translate(%.1f %.1f) scale(%.2f)">%s</g>' % (x, y, sc, fk + sp)

# ---------------------------------------------------------------- toque (head space)
PUFF = [(62, 46, 24), (90, 28, 28), (128, 22, 30), (166, 28, 28), (194, 46, 24), (100, 54, 26), (156, 54, 26), (128, 50, 28)]
BAND = "M 56 100 Q 128 88 200 100 L 196 62 Q 128 52 60 62 Z"
def toque():
    s = cloud(PUFF, WHITE)
    # soft folds on the puff
    for x0, x1 in ((76, 84), (108, 104), (148, 152), (180, 172)):
        s += LN("M %d 66 Q %d 50 %d 36" % (x0, (x0 + x1) / 2 + 4, x1), SHADE, 3, .9)
    s += LN("M 104 4 Q 116 -2 128 -2", "#ffffff", 4) + LN("M 70 30 Q 76 24 84 22", "#ffffff", 3)
    # gold-embroidered stars on the puff
    for x, y, r in ((84, 34, 5), (172, 36, 5), (128, 30, 6), (64, 54, 3.5), (194, 54, 3.5)):
        s += star4(x, y, r + 1.5, GOLDD) + star4(x, y, r, GOLD2)
    s += P(BAND, WHITE, 5)
    for x in range(72, 190, 12):   # pleats
        yb = 96 - 8 * (1 - ((x - 128) / 72.0) ** 2)
        s += LN("M %d %.1f L %d %.1f" % (x, 62 - 6 * (1 - ((x - 128) / 70.0) ** 2) + 3, x, yb - 9), SHADE, 2.5)
    # gold trims
    s += P("M 56 100 Q 128 88 200 100 L 199 90 Q 128 78 57 90 Z", GOLD, 3.5) + LN("M 60 95 Q 128 83 196 95", GOLD2, 1.8)
    s += P("M 60 66 Q 128 56 196 66 L 196 60 Q 128 50 60 60 Z", GOLD, 3)
    # the crest: a gold medallion with a ruby, crossed spoon and fork behind
    s += spoon_fork(128, 76, 1.25)
    s += CI(128, 76, 11, GOLD, 3.5) + CI(128, 76, 7, GOLD2, 0) + GEM(128, 76, 5, "#e0304e")
    for sx in (-1, 1):
        for i in range(3):
            x = 128 + sx * (22 + i * 9)
            s += P("M %.1f %d Q %.1f %d %.1f %d Q %.1f %d %.1f %d Z" % (x, 70 + i, x + sx * 6, 66 + i, x + sx * 9, 72 + i, x + sx * 4, 78 + i, x, 70 + i), GOLD2, 1.8)
    return HEAD(s)

def toque_trim():
    return HEAD(P("M 56 100 Q 128 88 200 100 L 199 90 Q 128 78 57 90 Z", "#fff", 0) + P("M 60 66 Q 128 56 196 66 L 196 60 Q 128 50 60 60 Z", "#fff", 0) + CI(128, 76, 11, "#fff", 0))

def toque_glow():
    return HEAD(blur(CI(128, 76, 11, GOLD2, 0), 4) + CI(128, 76, 3, GOLDC, 0)
                + "".join(blur(star4(x, y, r * 2, GOLD2), 2.5) for x, y, r in ((84, 34, 5), (172, 36, 5), (128, 30, 6))))

# ---------------------------------------------------------------- chef's jacket and apron (body space)
BIB = "M 98 134 L 158 134 L 162 162 Q 180 188 178 214 L 78 214 Q 76 188 94 162 Z"
POCKET = "M 108 184 L 148 184 L 146 206 Q 128 210 110 206 Z"
def chest():
    s = P(BODY_OUT, WHITE, 5)
    s += P("M 76 116 Q 66 160 66 214 L 84 214 Q 80 160 94 122 Z", WHITE2, 0) + mirror(P("M 76 116 Q 66 160 66 214 L 84 214 Q 80 160 94 122 Z", WHITE2, 0), 128)
    # double-breasted gold buttons beside the bib
    for y in (146, 168, 190):
        for x in (86, 170): s += CI(x, y, 4.5, GOLD, 2.5) + '<circle cx="%.1f" cy="%.1f" r="1.4" fill="#fff"/>' % (x - 1.3, y - 1.3)
    # straps
    s += LN("M 100 136 L 92 118", INK, 9) + LN("M 100 136 L 92 118", WINE, 5) + LN("M 156 136 L 164 118", INK, 9) + LN("M 156 136 L 164 118", WINE, 5)
    s += P(BIB, WINE, 5)
    s += P("M 104 138 L 152 138 L 156 162 Q 170 186 170 208 L 152 208 Q 150 180 128 176 Q 106 180 104 208 L 86 208 Q 86 186 100 162 Z", WINE2, 0)
    # gold piping round the bib
    s += LN("M 102 140 L 154 140 L 158 163 Q 174 188 172 210 L 84 210 Q 82 188 98 163 Z", GOLD, 2.5)
    # the embroidered crest: a laurel of golden wheat round a gold medallion
    for sx in (-1, 1):
        for i in range(4):
            a = math.radians(200 + i * 22) if sx < 0 else math.radians(-20 - i * 22)
            x, y = 128 + 19 * math.cos(a), 160 + 19 * math.sin(a) * -1
            s += EL(x, y, 4.5, 2.4, GOLD, 1.6, math.degrees(-a) + 90 * sx)
    s += spoon_fork(128, 158, 1.0)
    s += CI(128, 158, 9, GOLD, 3) + CI(128, 158, 5.5, GOLD2, 0) + GEM(128, 158, 3.6, "#e0304e")
    # the pocket, with a wooden spoon and a whisk
    s += LN("M 116 196 L 110 160", INK, 6) + LN("M 116 196 L 110 160", "#c88a4a", 3) + EL(109, 157, 5, 7, "#c88a4a", 2.5, -8)
    s += LN("M 140 196 L 144 170", INK, 5) + LN("M 140 196 L 144 170", "#cfd6de", 2.5)
    s += EL(146, 160, 7, 12, "none", 2.5, 10) + EL(146, 160, 3, 12, "none", 2, 10)
    s += P(POCKET, WINED, 3.5) + LN("M 110 188 L 146 188", GOLD, 2)
    return s

def chest_trim():
    return LN("M 102 140 L 154 140 L 158 163 Q 174 188 172 210 L 84 210 Q 82 188 98 163 Z", "#fff", 4) + CI(128, 158, 10, "#fff", 0)

def chest_glow():
    return blur(CI(128, 158, 10, GOLD2, 0), 4) + CI(128, 158, 2.5, GOLDC, 0)

# ---------------------------------------------------------------- the great ladle (right paw)
BOWL_C, BRX, BRY = (12, -146), 30, 9
def ladle():
    cx, cy = BOWL_C
    h = "M 0 36 L 0 -116 Q 0 -146 %.1f %.1f" % (cx - BRX + 2, cy)
    s = LN(h, INK, 13) + LN(h, GOLD, 7.5) + LN("M -1.5 30 L -1.5 -110", GOLD2, 2)
    # grip: wine leather with gold rings, a ruby pommel
    s += RC(-6.5, -8, 13, 40, WINE, 4, 3.5)
    for y in (-8, 10, 28): s += RC(-7.5, y - 2.5, 15, 6, GOLD, 2, 2.5)
    s += CI(0, 40, 6.5, GOLD, 3) + GEM(0, 40, 3.4, "#e0304e")
    s += CI(0, -70, 5, GOLD, 3) + GEM(0, -70, 3, "#3fc3e8")
    # the bowl, held level
    b = ""
    bowl = "M %.1f %.1f A %d %d 0 0 0 %.1f %.1f Z" % (cx - BRX, cy, BRX, 24, cx + BRX, cy)
    b += P(bowl, GOLD, 4.5)
    b += LN("M %.1f %.1f Q %.1f %.1f %.1f %.1f" % (cx - 18, cy + 8, cx - 12, cy + 18, cx, cy + 20), GOLD2, 3)
    b += LN("M %.1f %.1f Q %.1f %.1f %.1f %.1f" % (cx - 4, cy + 10, cx + 8, cy + 6, cx + 18, cy + 12), GOLDD, 2)
    b += GEM(cx + 4, cy + 13, 4, "#e0304e")
    # broth to the brim
    b += EL(cx, cy, BRX, BRY, GOLD, 4) + EL(cx, cy + 1, BRX - 4, BRY - 2.5, GOLDD, 0) + EL(cx, cy + 1.5, BRX - 6, BRY - 3.5, BROTH, 0) + EL(cx - 5, cy + 0.5, BRX - 15, BRY - 6, BROTH2, 0)
    return RHAND(s + rot(b, -14, cx, cy))

def ladle_mask():
    cx, cy = BOWL_C
    return RHAND(LN("M 0 -14 L 0 -116 Q 0 -140 %.1f %.1f" % (cx - BRX + 6, cy + 2), "#fff", 7) +
                 rot(P("M %.1f %.1f A %d %d 0 0 0 %.1f %.1f Z" % (cx - BRX + 2, cy + 6, BRX - 2, 21, cx + BRX - 2, cy + 6), "#fff", 0), -14, cx, cy))

def ladle_glow():
    cx, cy = BOWL_C
    return RHAND(rot(blur(EL(cx, cy - 1, BRX - 6, BRY - 2, BROTH2, 0), 3) + EL(cx - 4, cy + 0.5, 9, 2, BROTHC, 0), -14, cx, cy))

def ladle_bubbles(k):
    cx, cy = BOWL_C
    rnd = random.Random(40 + k)
    s = ""
    for i in range(3):
        x = cx + rnd.uniform(-18, 18)
        y = cy + rnd.uniform(-2, 2.5)
        r = rnd.uniform(2.2, 4.4) * (1.0 if (i + k) % 3 else 1.4)
        s += CI(x, y - r * 0.5, r, BROTH2, 1.8) + '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#fff"/>' % (x - r * 0.35, y - r * 0.85, r * 0.3)
    # a splash curl on one frame of four
    if k == 2: s += LN("M %.1f %.1f q 3 -8 7 -2" % (cx + 8, cy - 2), BROTH2, 3)
    return RHAND(rot(s, -14, cx, cy))

# ---------------------------------------------------------------- aura: the floating feast
def pie():
    s = EL(0, 9, 17, 6, WHITE, 2.5) + EL(0, 8, 12, 3.5, WHITE2, 0) + LN("M -15 9 A 17 6 0 0 0 15 9", GOLD, 1.6)
    s += P("M -13 7 Q -14 -8 0 -10 Q 14 -8 13 7 Q 0 10 -13 7 Z", CRUST, 2.5)
    for x in (-6, 0, 6): s += LN("M %d -8 Q %d 0 %d 7" % (x, x - 1, x), CRUSTD, 1.4)
    s += LN("M -11 -2 Q 0 -5 11 -2", CRUSTD, 1.4) + LN("M -12 3 Q 0 0 12 3", CRUSTD, 1.4)
    s += CI(0, -11, 3, "#e0304e", 1.6) + LN("M 0 -14 q 2 -3 4 -3", "#5a9a3a", 1.4)
    s += LN("M -6 -14 q -3 -4 0 -7 q 3 -3 0 -6", "#ffffff", 1.6, .8)
    return sprite(s)

def drumstick():
    s = P("M -12 8 C -18 -6 -6 -18 6 -12 C 14 -8 12 2 2 6 L -4 10 Z", "#b8662c", 2.5)
    s += P("M -9 4 C -13 -5 -5 -13 3 -10", "none", 0) + LN("M -9 3 C -12 -4 -6 -11 2 -10", "#d98a48", 2.4, .9)
    s += LN("M -3 9 L 6 16", INK, 6) + LN("M -3 9 L 6 16", WHITE, 3)
    s += CI(6, 18, 3, WHITE, 1.6) + CI(9, 15, 3, WHITE, 1.6)
    return sprite(s)

def cake():
    s = P("M -14 10 L -14 -2 L 14 -8 L 14 4 Z", "#fff0dc", 2.5)
    s += LN("M -14 4 L 14 -2", "#ff8fb0", 3) + LN("M -14 0 L 14 -6", "#fff8ee", 1.5)
    s += P("M -14 -2 L 14 -8 L 6 -12 L -16 -6 Z", "#fff8ee", 2.5)
    s += P("M 2 -12 C -2 -16 2 -22 6 -18 C 10 -22 12 -16 8 -12 Z", "#e0304e", 1.8)
    s += P("M 4 -20 l 2 -3 l 2 3 Z", "#5a9a3a", 0)
    return sprite(s)

def warm_ring(k):
    """a glowing banquet ring of golden light at the feet, rippling outwards"""
    s = blur('<ellipse cx="128" cy="214" rx="86" ry="15" fill="%s" opacity=".55"/>' % GOLD, 7)
    for i in range(2):
        f = (i / 2.0 + k / 8.0) % 1
        rx = 40 + 80 * f
        s += '<ellipse cx="128" cy="214" rx="%.1f" ry="%.1f" fill="none" stroke="%s" stroke-width="%.1f" opacity="%.2f"/>' % (rx, rx * 0.19, GOLD2, 3.5 - 1.5 * f, 0.9 * (1 - f))
    return s

SET = {
    "key": "feast", "name": "Feast of the Ages", "zone": None, "lua": "FeastOfTheAges", "file": "feast_of_the_ages",
    "prof": "cooking", "spec": None, "title": "Master Chef",
    "about": "Feast of the Ages: the Cooking long-chase set (a legendary chef's toque, apron and ladle, and a floating feast), crafted by Cooking.",
    "preview_fur": "fur_silver",
    "pieces": [
        {"id": "set_feast_head", "slot": "head", "kind": "head", "art": "feast_head", "name": "Toque of the Grand Banquet", "rarity": 5,
         "icon": "INV_Misc_Food_15", "word": "hat",
         "svg": toque(), "layers": {"trim": toque_trim(), "glow": toque_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K("feast_head", "trim"), "scale": 110, "vx": 70, "vy": 0, "color": [1.0, 0.95, 0.75], "blend": "ADD", "alpha": 0.9},
             {"kind": "pulse", "key": K("feast_head", "glow"), "a": [0.15, 0.75], "speed": 2.4, "blend": "ADD"},
             {"kind": "particles", "sprite": "a_wisp", "n": 3, "box": box(H(128, 0), 60, 10), "vx": [-10, 10], "vy": [-40, -24], "life": [1.4, 2.0],
              "size": [26, 38], "grow": 0.6, "sway": 8, "alpha": 0.55, "at": "front"},
             {"kind": "glint", "sprite": "t_sparkle", "n": 3, "spots": [box(H(128, 30), 70, 22), box(H(128, 80), 60, 10)], "life": 0.8, "size": [14, 24],
              "gap": [0.3, 1.0], "color": WARM3, "at": "front"},
         ]},
        {"id": "set_feast_chest", "slot": "chest", "kind": "chest", "art": "feast_chest", "name": "Embroidered Apron of Plenty", "rarity": 4,
         "icon": "INV_Chest_Cloth_25", "word": "apron",
         "svg": chest(), "layers": {"trim": chest_trim(), "glow": chest_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K("feast_chest", "trim"), "scale": 120, "vx": 50, "vy": -30, "color": [1.0, 0.95, 0.75], "blend": "ADD", "alpha": 0.9},
             {"kind": "pulse", "key": K("feast_chest", "glow"), "a": [0.15, 0.7], "speed": 2.2, "blend": "ADD"},
             {"kind": "glint", "sprite": "t_sparkle", "n": 2, "spots": [box(B(128, 160), 26, 20), box(B(86, 168), 6, 24), box(B(170, 168), 6, 24)],
              "life": 0.8, "size": [14, 22], "gap": [0.4, 1.2], "color": WARM3, "at": "front"},
         ]},
        {"id": "set_feast_weapon", "slot": "main", "kind": "weapon", "art": "feast_weapon", "name": "Ladle of Endless Broth", "rarity": 4,
         "icon": "INV_Misc_Food_33", "word": "ladle",
         "svg": ladle(), "layers": dict(frames(4, ladle_bubbles), mask=ladle_mask(), glow=ladle_glow()),
         "anim": [
             {"kind": "flip", "keys": [K("feast_weapon", "fl%d" % i) for i in range(1, 5)], "fps": 6},
             {"kind": "pulse", "key": K("feast_weapon", "glow"), "a": [0.2, 0.8], "speed": 2.8, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_shine", "mask": K("feast_weapon", "mask"), "scale": 120, "vx": 0, "vy": -60, "color": [1.0, 0.95, 0.7], "blend": "ADD", "alpha": 0.85},
             {"kind": "particles", "sprite": "a_wisp", "n": 4, "box": [410, 118, 462, 140], "vx": [-8, 8], "vy": [-45, -28], "life": [1.2, 1.8],
              "size": [24, 34], "grow": 0.7, "sway": 7, "alpha": 0.6, "at": "front"},
             {"kind": "glint", "sprite": "t_sparkle", "n": 2, "spots": [[400, 136, 470, 186], [370, 200, 410, 330]], "life": 0.7, "size": [14, 22],
              "gap": [0.4, 1.2], "color": WARM3, "at": "front"},
         ]},
        {"id": "set_feast_aura", "slot": "effect", "kind": "effect", "art": "feast_aura", "name": "Banquet of the Ages", "rarity": 5,
         "icon": "INV_Misc_Food_59", "word": "aura", "glow": (1.0, 0.72, 0.3),
         "fx": {"layer": "back", "anim": "float"},
         "layers": dict(frames(4, warm_ring), pie=pie(), leg=drumstick(), cake=cake()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [1.0, 0.62, 0.22], "a": [0.25, 0.55], "speed": 1.5, "blend": "ADD", "at": "behind"},
             {"kind": "flip", "keys": [K("feast_aura", "fl%d" % i) for i in range(1, 5)], "fps": 5, "blend": "ADD", "at": "behind"},
             {"kind": "particles", "sprite": "k_feast_aura_pie", "n": 2, "box": [60, 300, 160, 440], "vx": [-6, 6], "vy": [-42, -28], "life": [2.6, 3.4],
              "size": [72, 84], "spin": [-0.4, 0.4], "sway": 10, "at": "front"},
             {"kind": "particles", "sprite": "k_feast_aura_leg", "n": 2, "box": [352, 300, 452, 440], "vx": [-6, 6], "vy": [-42, -28], "life": [2.6, 3.4],
              "size": [70, 82], "spin": [-0.7, 0.7], "sway": 10, "at": "front"},
             {"kind": "particles", "sprite": "k_feast_aura_cake", "n": 2, "box": [150, 380, 362, 460], "vx": [-10, 10], "vy": [-48, -32], "life": [2.8, 3.6],
              "size": [68, 80], "spin": [-0.4, 0.4], "sway": 12, "at": "behind"},
             {"kind": "glint", "sprite": "t_sparkle", "n": 5, "spots": [[50, 100, 160, 440], [352, 100, 462, 440], [150, 20, 362, 120]],
              "life": 0.9, "size": [16, 28], "gap": [0.2, 0.8], "color": WARM3, "at": "front"},
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
