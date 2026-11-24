"""Field Medic (1.7.0): the First Aid long-chase set. A white field cap with a winged red-cross badge,
bandage-wrapped shoulder pads whose loose ends flutter, a white cape with a red cross and a medic's
satchel, and a soft green-white healing aura: a turning ring of crosses at the feet, rising crosses and
sparkles, and a gentle pulse. Crafted by First Aid (ProfSets.lua); the whole set gives the title Field Medic.
  python3 tools/sets/field_medic.py            -> Art/v/k_medic_*.tga, Art/medic_*.tga, Sets/FieldMedic.lua
  python3 tools/set_preview.py tools/sets/field_medic.py <out>   -> animated preview
"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: clean white, medic red, bandage cream, gold, healing green
WHITE, WHITE2, SHADE = "#fbfcfa", "#eef1f0", "#d5dbdd"
RED, RED2, REDD = "#e2383c", "#ff6a64", "#a51e26"
BAND, BANDD = "#f4ecd6", "#cdbf98"
GOLD, GOLD2, GOLDD = "#f2b93a", "#ffe08a", "#b98220"
GREEN, GREEN2, GREENC = "#45d67e", "#a8f7c4", "#effff4"
LEATHER, LEATHER2, LEATHERD = "#94592f", "#bb7a45", "#64391c"
HEAL3 = [0.55, 1.0, 0.7]

WIDEBLUR = ('<defs><filter id="wblur" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1100" height="1100">'
            '<feGaussianBlur stdDeviation="%s"/></filter></defs>')
def blur(s, sd=5): return WIDEBLUR % sd + '<g filter="url(#wblur)">%s</g>' % s

def sprite(inner, S=32):
    dots = '<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/><rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S)
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)

def rot(s, a, x, y): return '<g transform="rotate(%.1f %.1f %.1f)">%s</g>' % (a, x, y, s)
def H(x, y): return 2 * (128 + 0.8 * (x - 128)), 2 * (32 + 0.8 * (y - 28))
def B(x, y): return 2 * x, 2 * (y + 16)
def box(c, w, h): return [round(c[0] - w), round(c[1] - h), round(c[0] + w), round(c[1] + h)]
def frames(n, fn, name="fl"): return {"%s%d" % (name, k + 1): fn(k) for k in range(n)}

def cross_d(x, y, s, t=0.36):
    """a plus sign s across, arms t*s thick, as a path"""
    a, b = s / 2.0, s * t / 2.0
    pts = [(-b, -a), (b, -a), (b, -b), (a, -b), (a, b), (b, b), (b, a), (-b, a), (-b, b), (-a, b), (-a, -b), (-b, -b)]
    return "M " + " L ".join("%.1f %.1f" % (x + px, y + py) for px, py in pts) + " Z"

def cross(x, y, s, fill=RED, ink=3, t=0.36):
    return P(cross_d(x, y, s, t), fill, ink)

def badge(x, y, r, ink=3.5):
    """white roundel with a gold rim and a red cross"""
    s = CI(x, y, r, GOLD, ink) + CI(x, y, r * 0.78, WHITE, 0) + LN("M %.1f %.1f A %.1f %.1f 0 0 1 %.1f %.1f" % (x - r * 0.9, y, r * 0.9, r * 0.9, x + r * 0.9, y), GOLD2, max(1.2, r * 0.08))
    s += cross(x, y, r * 1.15, RED, max(1.8, ink * 0.6))
    s += LN("M %.1f %.1f L %.1f %.1f" % (x - r * 0.12, y - r * 0.45, x - r * 0.12, y - r * 0.1), "#ffffff", max(1.2, r * 0.1), .7)
    return s

def wing(x, y, side, sc=1.0):
    """a small golden wing spreading out from (x, y)"""
    s = ""
    for i, (ln, a) in enumerate(((30, -28), (26, -10), (20, 8))):
        t = math.radians(a)
        tx, ty = ln * math.cos(t), ln * math.sin(t)
        s += P("M 0 -5 Q %.1f %.1f %.1f %.1f Q %.1f %.1f 0 5 Z" % (tx * 0.5, ty * 0.5 - 7, tx, ty, tx * 0.6, ty * 0.6 + 6), GOLD if i != 1 else GOLD2, 2.5)
    g = '<g transform="translate(%.1f %.1f) scale(%.2f %.2f)">%s</g>' % (x, y, sc * side, sc, s)
    return g

# ---------------------------------------------------------------- field cap (head space)
CAP = "M 54 98 L 62 34 Q 128 14 194 34 L 202 98 Q 128 86 54 98 Z"
TOP = (128, 30, 66, 13)
BADGE = (128, 56, 20)
def cap():
    s = P(CAP, WHITE, 5)
    s += P("M 62 36 L 56 96 Q 72 92 84 90 L 84 30 Q 72 32 62 36 Z", WHITE2, 0) + P("M 194 36 L 200 96 Q 184 92 172 90 L 172 30 Q 184 32 194 36 Z", SHADE, 0)
    s += EL(*TOP, fill=WHITE, w=4) + EL(TOP[0] - 10, TOP[1] - 2, 40, 5, "#ffffff", 0)
    # red band round the cap, white piping
    s += P("M 57 80 Q 128 68 199 80 L 200 92 Q 128 80 56 92 Z", RED, 3.5) + LN("M 58 84 Q 128 72 198 84", RED2, 2)
    # visor
    s += P("M 52 94 Q 128 82 204 94 Q 208 102 198 106 Q 128 96 58 106 Q 48 102 52 94 Z", "#5d6a74", 4) + LN("M 60 98 Q 128 88 196 98", "#8a98a2", 2)
    # golden wings and the badge
    s += wing(BADGE[0] - BADGE[2] + 2, BADGE[1], -1, 1.3) + wing(BADGE[0] + BADGE[2] - 2, BADGE[1], 1, 1.3)
    s += badge(*BADGE)
    return HEAD(s)

def cap_gold():
    return HEAD(wing(BADGE[0] - BADGE[2] + 2, BADGE[1], -1, 1.3).replace(GOLD2, "#fff").replace(GOLD, "#fff").replace('stroke="%s"' % INK, 'stroke="#fff"')
                + wing(BADGE[0] + BADGE[2] - 2, BADGE[1], 1, 1.3).replace(GOLD2, "#fff").replace(GOLD, "#fff").replace('stroke="%s"' % INK, 'stroke="#fff"'))

def cap_glow():
    x, y, r = BADGE
    return HEAD(blur('<circle cx="%d" cy="%d" r="%d" fill="none" stroke="%s" stroke-width="7"/>' % (x, y, r + 3, GREEN2), 4)
                + '<circle cx="%d" cy="%d" r="%d" fill="none" stroke="%s" stroke-width="2"/>' % (x, y, r + 1, GREENC))

# ---------------------------------------------------------------- bandaged shoulder pads (body space)
def pad_shape(cx, cy):
    return "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 30, cy + 10, cx + 26, cy - 22, cx - 4, cy - 23,
        cx - 38, cy - 22, cx - 40, cy + 12, cx - 4, cy + 25, cx + 30, cy + 10)

def pad():
    cx, cy = SH_C
    s = P(pad_shape(cx, cy), BANDD, 5)
    clip = '<defs><clipPath id="fmpad"><path d="%s"/></clipPath></defs>' % pad_shape(cx, cy)
    wraps = ""
    for k in range(-3, 4):   # bandage strips wound diagonally round the pad
        x0 = cx + k * 14
        d = "M %d %d L %d %d" % (x0 - 20, cy + 30, x0 + 16, cy - 30)
        wraps += LN(d, INK, 12, .55) + LN(d, BAND if k % 2 else WHITE, 9.5) + LN("M %d %d L %d %d" % (x0 - 22, cy + 30, x0 + 14, cy - 30), "#ffffff", 2, .7)
    s += clip + '<g clip-path="url(#fmpad)">%s</g>' % wraps
    s += P(pad_shape(cx, cy), "none", 5)
    # gold trim with rivets
    tr = "M %d %d Q %d %d %d %d" % (cx - 39, cy + 9, cx - 4, cy + 25, cx + 29, cy + 8)
    s += LN(tr, GOLD, 7) + LN(tr, INK, 2)
    for x, y in ((cx - 26, cy + 15), (cx - 6, cy + 19), (cx + 14, cy + 15)): s += CI(x, y, 2.8, GOLD2, 2)
    s += badge(cx - 8, cy - 4, 12, 3)
    # a safety pin
    s += LN("M %d %d L %d %d" % (cx + 8, cy - 14, cx + 22, cy - 8), "#c9d2d8", 2.5) + CI(cx + 23, cy - 7.5, 2.5, GOLD, 1.8)
    return BOTH(s)

def pad_tail(k):
    """the loose bandage end fluttering out from the outer edge"""
    cx, cy = SH_C
    x0, y0 = cx - 38, cy + 4
    w = (0, 5, 9, 5)[k]
    ex, ey = x0 - 16 - w * 0.8, y0 + 32 - w * 0.3
    d = "M %d %d Q %.1f %.1f %.1f %.1f T %.1f %.1f" % (x0, y0, x0 - 12, y0 + 2 - w * 0.6, x0 - 10 - w * 0.5, y0 + 14, ex, ey)
    s = LN(d, INK, 13) + LN(d, BAND, 9) + LN(d, BANDD, 1.5)
    s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (ex - 5, ey - 2, ex + 5, ey + 1, ex + 3, ey + 9, ex - 1, ey + 5), BAND, 2.5)
    return BOTH(s)

def pad_glow():
    cx, cy = SH_C
    return BOTH(blur('<circle cx="%d" cy="%d" r="14" fill="none" stroke="%s" stroke-width="6"/>' % (cx - 8, cy - 4, GREEN2), 3.5)
                + '<circle cx="%d" cy="%d" r="12.5" fill="none" stroke="%s" stroke-width="1.6"/>' % (cx - 8, cy - 4, GREENC))

# ---------------------------------------------------------------- cape with a red cross and a satchel (side drapes)
def cape():
    s = "".join(P(d, WHITE, 5) for d in DRAPE_OUT) + "".join(P(d, RED, 3) for d in DRAPE_IN)
    for side in DRAPE_EDGE:   # red hem with a gold thread
        pts = qpts(*side, n=10)
        d = "M " + " L ".join("%.1f %.1f" % (x + (4 if x < 128 else -4), y) for x, y in pts)
        s += LN(d, RED, 6) + LN(d, GOLD2, 1.5)
    s += LN("M 58 150 Q 48 172 50 196", SHADE, 3) + LN("M 198 150 Q 208 172 206 196", SHADE, 3)
    # the red cross on the left drape
    s += CI(44, 170, 15, WHITE, 0) + cross(44, 170, 24, RED, 3.5)
    # the satchel on the right: strap, bag, flap with a cross, gold buckle
    s += LN("M 196 118 L 214 158", INK, 8) + LN("M 196 118 L 214 158", LEATHER2, 4)
    bag = "M 196 162 L 232 160 Q 236 184 230 198 Q 214 204 198 198 Q 192 184 196 162 Z"
    s += P(bag, LEATHER, 4) + LN("M 199 194 Q 214 199 228 194", LEATHERD, 2)
    s += P("M 194 160 L 234 158 Q 236 172 226 178 Q 214 182 202 178 Q 192 172 194 160 Z", LEATHER2, 3.5)
    s += CI(214, 168, 7.5, WHITE, 2.5) + cross(214, 168, 11, RED, 2)
    s += RC(210, 177, 8, 7, GOLD, 2, 2)
    return s

def cape_mask():
    return "".join(P(d, "#ffffff", 0) for d in DRAPE_OUT)

def cape_glow():
    return blur('<circle cx="44" cy="170" r="16" fill="none" stroke="%s" stroke-width="6"/>' % GREEN2, 4) + blur('<circle cx="214" cy="168" r="9" fill="none" stroke="%s" stroke-width="4"/>' % GREEN2, 3)

# ---------------------------------------------------------------- aura: healing circle, rising crosses
def heal_ring(k):
    """a circle at the feet with six crosses turning round it (4 frames = 1/6 turn, so it loops)"""
    s = blur('<ellipse cx="128" cy="214" rx="92" ry="17" fill="%s" opacity=".55"/>' % GREEN, 7)
    s += '<ellipse cx="128" cy="214" rx="96" ry="18" fill="none" stroke="%s" stroke-width="3" opacity=".9"/>' % GREEN2
    s += '<ellipse cx="128" cy="214" rx="74" ry="13" fill="none" stroke="%s" stroke-width="1.6" opacity=".7"/>' % GREENC
    for i in range(6):
        a = math.radians(i * 60 + k * 15)
        x, y = 128 + 85 * math.cos(a), 214 + 15.5 * math.sin(a)
        sc = 0.75 + 0.25 * (math.sin(a) + 1) / 2
        s += P(cross_d(x, y, 10 * sc), GREENC, 0)
    return s

def heal_halo():
    return blur('<ellipse cx="128" cy="150" rx="104" ry="96" fill="none" stroke="%s" stroke-width="10" opacity=".8"/>' % GREEN2, 8)

def heal_cross():
    return sprite(blur(P(cross_d(0, 0, 22), GREEN, 0), 2.5) + cross(0, 0, 20, GREEN2, 2.5) + P(cross_d(0, 0, 10), GREENC, 0))

SET = {
    "key": "medic", "name": "Field Medic", "zone": None, "lua": "FieldMedic", "file": "field_medic",
    "prof": "firstaid", "spec": None, "title": "Field Medic",
    "about": "Field Medic: the First Aid long-chase set (a winged red-cross cap, bandaged pads, a medic's cape and a healing aura), crafted by First Aid.",
    "preview_fur": "fur_chocolate",
    "pieces": [
        {"id": "set_medic_head", "slot": "head", "kind": "head", "art": "medic_head", "name": "Winged Cap of the Lifesaver", "rarity": 5,
         "icon": "INV_Helmet_29", "word": "cap",
         "svg": cap(), "layers": {"gold": cap_gold(), "glow": cap_glow(), "cross": heal_cross()},
         "anim": [
             {"kind": "pulse", "key": K("medic_head", "glow"), "a": [0.15, 0.85], "speed": 2.0, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_shine", "mask": K("medic_head", "gold"), "scale": 100, "vx": 60, "vy": 0, "color": [1.0, 0.95, 0.75], "blend": "ADD", "alpha": 0.9},
             {"kind": "glint", "sprite": "t_sparkle", "n": 2, "spots": [box(H(128, 58), 60, 16)], "life": 0.8, "size": [14, 22], "gap": [0.5, 1.4], "color": [1.0, 0.95, 0.7], "at": "front"},
             {"kind": "particles", "sprite": "k_medic_head_cross", "n": 3, "box": box(H(128, 20), 60, 12), "vx": [-8, 8], "vy": [-40, -24], "life": [1.4, 2.0],
              "size": [14, 20], "sway": 6, "alpha": 0.9, "at": "front"},
         ]},
        {"id": "set_medic_shoulders", "slot": "shoulder", "kind": "shoulder", "art": "medic_shoulders", "name": "Bandage-Bound Pauldrons", "rarity": 4,
         "icon": "INV_Shoulder_02", "word": "shoulders",
         "svg": pad(), "layers": dict(frames(4, pad_tail), glow=pad_glow()),
         "anim": [
             {"kind": "flip", "keys": [K("medic_shoulders", "fl%d" % i) for i in range(1, 5)], "fps": 6},
             {"kind": "pulse", "key": K("medic_shoulders", "glow"), "a": [0.1, 0.8], "speed": 2.0, "blend": "ADD"},
             {"kind": "glint", "sprite": "t_sparkle", "n": 2, "spots": "pieceSides", "life": 0.8, "size": [12, 20], "gap": [0.5, 1.4], "color": [0.8, 1.0, 0.85], "at": "front"},
         ]},
        {"id": "set_medic_cape", "slot": "back", "kind": "back", "art": "medic_cape", "name": "Mantle of the Mercy Corps", "rarity": 4,
         "icon": "INV_Misc_Cape_11", "word": "cape",
         "svg": cape(), "layers": {"mask": cape_mask(), "glow": cape_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K("medic_cape", "mask"), "scale": 130, "vx": 0, "vy": -45, "color": [0.8, 1.0, 0.88], "blend": "ADD", "alpha": 0.55},
             {"kind": "pulse", "key": K("medic_cape", "glow"), "a": [0.15, 0.9], "speed": 2.0, "blend": "ADD"},
             {"kind": "particles", "sprite": "a_spark", "n": 3, "box": [50, 300, 110, 430], "vx": [-10, 2], "vy": [-50, -28], "life": [1.2, 1.8],
              "size": [10, 16], "color": HEAL3, "blend": "ADD", "sway": 5, "at": "behind"},
             {"kind": "particles", "sprite": "a_spark", "n": 3, "box": [402, 300, 462, 430], "vx": [-2, 10], "vy": [-50, -28], "life": [1.2, 1.8],
              "size": [10, 16], "color": HEAL3, "blend": "ADD", "sway": 5, "at": "behind"},
         ]},
        {"id": "set_medic_aura", "slot": "effect", "kind": "effect", "art": "medic_aura", "name": "Lifeline Aura", "rarity": 5,
         "icon": "Spell_Holy_Renew", "word": "aura", "glow": (0.5, 1.0, 0.65),
         "fx": {"layer": "back", "anim": "float"},
         "layers": dict(frames(4, heal_ring), halo=heal_halo(), cross=heal_cross()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [0.45, 1.0, 0.62], "a": [0.2, 0.5], "speed": 1.4, "blend": "ADD", "at": "behind"},
             {"kind": "pulse", "key": K("medic_aura", "halo"), "a": [0.0, 0.7], "speed": 2.2, "blend": "ADD", "at": "behind"},
             {"kind": "flip", "keys": [K("medic_aura", "fl%d" % i) for i in range(1, 5)], "fps": 5, "blend": "ADD", "at": "behind"},
             {"kind": "particles", "sprite": "k_medic_aura_cross", "n": 6, "box": [80, 260, 432, 450], "vx": [-8, 8], "vy": [-60, -35], "life": [1.6, 2.4],
              "size": [16, 26], "sway": 8, "alpha": 0.95, "at": "front"},
             {"kind": "particles", "sprite": "a_spark", "n": 6, "box": [70, 140, 442, 460], "vx": [-8, 8], "vy": [-55, -30], "life": [1.4, 2.2],
              "size": [10, 18], "color": HEAL3, "color2": [1.0, 1.0, 1.0], "blend": "ADD", "sway": 6, "at": "behind"},
             {"kind": "glint", "sprite": "t_sparkle", "n": 4, "spots": [[60, 120, 160, 420], [352, 120, 452, 420], [150, 30, 362, 120]],
              "life": 0.9, "size": [16, 28], "gap": [0.2, 0.9], "color": [0.85, 1.0, 0.9], "at": "front"},
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
