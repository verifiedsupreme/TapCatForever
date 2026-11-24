"""Lotus Bloom set (1.7.0): the Herbalism long chase. The legendary Black Lotus and a garden in bloom:
a crown of dark lotus petals around a glowing heart, a cape of layered petals and leaves, a living
vine staff topped with a black lotus, and an aura of drifting petals and leaves, butterflies, pollen
and a little garden at the cat's feet. Gathered over months; the whole set gives the title Lotus Keeper.
  python3 tools/sets/lotus_bloom.py            -> Art/v/k_lotus_*.tga, Art/lotus_*.tga, Sets/LotusBloom.lua
  python3 tools/set_preview.py tools/sets/lotus_bloom.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: black lotus petals with a violet sheen, a glowing gold-green heart, spring leaves and vines
PET, PET2, PET3, PETL = "#26142f", "#3b2150", "#573274", "#8a55b8"
EDGE, EDGEL = "#c66be0", "#f0b8ff"
HEART, HEART2, HEARTC = "#d9f25a", "#fff07a", "#fffde6"
LEAF, LEAF2, LEAFL = "#4fb548", "#2c8236", "#a6e86e"
VINE, VINE2, VINEL = "#3c6a28", "#2a4c1c", "#7fb04a"
WATER, WATERL = "#2f6f78", "#7fd6d0"
WHITE = "#ffffff"
POLLEN = [1.0, 0.92, 0.5]


def frames(n, fn, seed=900):
    return {"fl%d" % (k + 1): fn(random.Random(seed + k), k) for k in range(n)}


WIDEBLUR = ('<defs><filter id="wblur" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1100" height="1100">'
            '<feGaussianBlur stdDeviation="%s"/></filter></defs>')
def blur(s, sd=5): return (WIDEBLUR % sd) + '<g filter="url(#wblur)">%s</g>' % s


def sprite(inner, S=32):
    """a small particle sprite: the drawing centred in an exact S x S box (faint corner dots fix the crop)"""
    dots = ('<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/>'
            '<rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S))
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)


def at(x, y, ang, s):
    return '<g transform="translate(%.1f %.1f) rotate(%.1f)">%s</g>' % (x, y, ang, s)


def petal_d(ln, w):
    """a pointed lotus petal with its base at 0,0 pointing up (negative y)"""
    return ("M 0 0 C %.1f %.1f %.1f %.1f 0 %.1f C %.1f %.1f %.1f %.1f 0 0 Z"
            % (w * 1.25, -ln * 0.22, w * 0.8, -ln * 0.74, -ln, -w * 0.8, -ln * 0.74, -w * 1.25, -ln * 0.22))


def petal(x, y, ln, w, ang, fill=PET, ink=3.5, vein=True):
    s = P(petal_d(ln, w), fill, ink)
    if vein:
        s += P("M 0 %.1f C %.1f %.1f %.1f %.1f 0 %.1f C %.1f %.1f %.1f %.1f 0 %.1f Z"
               % (-ln * 0.12, w * 0.45, -ln * 0.3, w * 0.3, -ln * 0.7, -ln * 0.9, -w * 0.3, -ln * 0.7, -w * 0.45, -ln * 0.3, -ln * 0.12), light(fill, 0.18), 0)
        s += LN("M 0 %.1f Q %.1f %.1f 0 %.1f" % (-ln * 0.55, w * 0.12, -ln * 0.75, -ln * 0.93), EDGE, max(1.4, w * 0.14))
    return at(x, y, ang, s)


def petal_tipglow(x, y, ln, w, ang):
    return at(x, y, ang, LN("M 0 %.1f Q %.1f %.1f 0 %.1f" % (-ln * 0.6, w * 0.12, -ln * 0.8, -ln * 0.95), EDGE, max(2.5, w * 0.25)))


def leaf(x, y, ln, w, ang, col=LEAF, ink=3):
    d = "M 0 0 Q %.1f %.1f 0 %.1f Q %.1f %.1f 0 0 Z" % (w, -ln * 0.45, -ln, -w, -ln * 0.45)
    s = P(d, col, ink) + LN("M 0 -2 L 0 %.1f" % (-ln * 0.8), darker(col, .7), max(1.2, ink * 0.5))
    s += LN("M %.1f %.1f Q %.1f %.1f %.1f %.1f" % (-w * 0.4, -ln * 0.3, -w * 0.5, -ln * 0.5, -w * 0.2, -ln * 0.75), light(col, .35), 1.6)
    return at(x, y, ang, s)


def heart(x, y, r):
    """the black lotus' glowing seed heart"""
    s = CI(x, y, r, HEART, 3.5) + CI(x, y + r * 0.1, r * 0.66, HEART2, 0)
    for i in range(5):
        a = math.radians(i * 72 + 18)
        s += CI(x + math.sin(a) * r * 0.45, y - math.cos(a) * r * 0.45, max(1.2, r * 0.13), "#9fae2a", 0)
    return s + CI(x - r * 0.35, y - r * 0.4, max(1.2, r * 0.2), WHITE, 0)


# ---------------------------------------------------------------- crown (head space)
FAN_C = (128, 150)   # the fan of petals radiates from here
def crown_petals():
    """(x, y, length, width, angle, fill) of each crown petal, back row first"""
    out = []
    for i in range(7):
        a = -60 + i * 20
        ln = 52 + 26 * math.cos(math.radians(a * 1.3))
        x = FAN_C[0] + math.sin(math.radians(a)) * 72
        y = FAN_C[1] - math.cos(math.radians(a)) * 72
        out.append((x, y, ln, 19 + 3 * math.cos(math.radians(a)), a * 1.1, PET if i % 2 else PET2))
    for i in range(6):
        a = -50 + i * 20
        ln = 36 + 16 * math.cos(math.radians(a * 1.3))
        x = FAN_C[0] + math.sin(math.radians(a)) * 72
        y = FAN_C[1] - math.cos(math.radians(a)) * 72 + 4
        out.append((x, y, ln, 16, a * 1.1, PET3))
    return out


HEART_H = (128, 70)
def crown():
    s = ""
    # leaves fanning out at the ends of the circlet
    for x, y, ln, w, a, f in crown_petals(): s += petal(x, y, ln, w, a, f)
    # leaves hanging from the ends of the circlet
    for sx in (-1, 1):
        s += leaf(128 + sx * 66, 88, 40, 13, sx * 128, LEAF2) + leaf(128 + sx * 58, 90, 32, 11, sx * 154, LEAF)
    # the vine circlet
    band = "M 54 92 Q 128 66 202 92"
    s += LN(band, INK, 15) + LN(band, VINE, 9) + LN("M 56 88 Q 92 74 128 74 Q 164 74 200 88", VINEL, 3)
    for i in range(7):
        t = (i + 0.5) / 7.0
        x = 54 + 148 * t
        y = 92 - 26 * (1 - (2 * t - 1) ** 2) * 1.0 + 3
        s += LN("M %.1f %.1f q 4 -6 9 -2" % (x - 4, y + 2), VINE2, 2.5)
    # the black lotus at the front: little curled petals around the glowing heart
    hx, hy = HEART_H
    for a, ln in ((-66, 32), (66, 32), (-34, 40), (34, 40), (0, 42)):
        s += petal(hx, hy + 16, ln, 14, a, PET3 if a else PETL, 4)
    for a in (-104, 104, -20, 20):
        s += petal(hx, hy + 18, 26 if abs(a) > 90 else 22, 11, a, PET2, 3.5)
    s += heart(hx, hy + 2, 12)
    for x, y in ((92, 50), (164, 50), (108, 22), (148, 22)): s += CI(x, y, 2.6, EDGEL, 1.5)   # dewdrops
    return HEAD(s)


def crown_mask():   # the petals alone: a sheen sweeps across them
    s = "".join(at(x, y, a, P(petal_d(ln, w), WHITE, 0)) for x, y, ln, w, a, f in crown_petals())
    return HEAD(s)


def crown_glow():
    s = "".join(petal_tipglow(x, y, ln, w, a) for x, y, ln, w, a, f in crown_petals())
    hx, hy = HEART_H
    g = blur(s + CI(hx, hy + 2, 20, HEART2, 0), 4)
    g += "".join(at(x, y, a, LN("M 0 %.1f Q %.1f %.1f 0 %.1f" % (-ln * 0.6, w * 0.1, -ln * 0.78, -ln * 0.92), EDGEL, 1.4)) for x, y, ln, w, a, f in crown_petals())
    g += CI(hx, hy + 2, 5, HEARTC, 0)
    return HEAD(g)


def H2C(x, y):
    return (128 + 0.8 * (x - 128)) * 2, (16 + 0.8 * (y - 28) + 16) * 2


# ---------------------------------------------------------------- cape (side drapes of petals and leaves)
def cape_petals():
    """(x, y, length, width, angle, fill) of the petals down each drape, top tier first so lower ones overlap:
    big outer petals fanning out past the drape's edge (out and up at the top, down at the hem) and
    smaller ones laid over them"""
    out = []
    for side in DRAPE_EDGE:
        sx = -1 if side[0][0] < 128 else 1
        pts = qpts(*side, n=4)
        for i, (x, y) in enumerate(pts[1:]):
            out.append((x - sx * 12, y - 4, 46 - i * 3, 17, sx * (62 + i * 26), PET if i % 2 else PET2))
        for i, (x, y) in enumerate(pts[1:]):
            out.append((x - sx * 18, y + 2, 32 - i * 2, 13, sx * (84 + i * 22), PET3))
    return out


def cape():
    s = "".join(P(p, PET2, 5) for p in DRAPE_OUT)
    s += "".join(P(p, LEAF2, 3) for p in DRAPE_IN)
    for p in DRAPE_IN:   # leaf veins on the green lining
        x0 = 60 if p == DRAPE_IN[0] else 196
        sx = 1 if x0 < 128 else -1
        s += LN("M %d 130 Q %d 160 %d 196" % (x0 + sx * 22, x0 - sx * 2, x0 - sx * 10), VINE2, 2.5)
    # leaves peeking out between the petals
    for side in DRAPE_EDGE:
        sx = -1 if side[0][0] < 128 else 1
        for i, (x, y) in enumerate(qpts(*side, n=4)[1:]):
            s += leaf(x - sx * 8, y + 4, 42 - i * 3, 12, sx * (70 + i * 24), LEAF if i % 2 else LEAF2, 3)
    for x, y, ln, w, a, f in cape_petals(): s += petal(x, y, ln, w, a, f, 3.5)
    # a little black lotus pinned at each shoulder
    for sx in (-1, 1):
        x = 128 + sx * 58
        for a in (-50, 0, 50): s += petal(x, 124, 18, 8, a, PET, 3)
        s += heart(x, 118, 5.5)
    return s


def cape_mask():
    return "".join(at(x, y, a, P(petal_d(ln, w), WHITE, 0)) for x, y, ln, w, a, f in cape_petals())


def cape_glow():
    g = blur("".join(petal_tipglow(x, y, ln, w, a) for x, y, ln, w, a, f in cape_petals())
             + "".join(CI(128 + sx * 58, 118, 9, HEART2, 0) for sx in (-1, 1)), 3.5)
    return g + "".join(CI(128 + sx * 58, 118, 2.5, HEARTC, 0) for sx in (-1, 1))


# ---------------------------------------------------------------- vine staff (right paw)
SL = 140
BLOOM_Y = -SL - 14


def vine_path(ph, amp=5):
    pts = []
    for i in range(0, 29):
        y = 34 - i * (SL + 34) / 28.0
        pts.append((amp * math.sin(i * 0.75 + ph), y))
    return "M " + " L ".join("%.1f %.1f" % p for p in pts)


def staff():
    s = ""
    s += P("M -6 30 Q -2 52 3 56 Q 6 46 6 30 Z", VINE2, 3)                      # the root tip
    a, b = vine_path(0), vine_path(math.pi)
    s += LN(a, INK, 11) + LN(b, INK, 11) + LN(a, VINE, 6) + LN(b, VINE2, 6) + LN(a, VINEL, 2)
    # tendrils curling off the top
    for sx in (-1, 1):
        d = "M 0 %d C %d %d %d %d %d %d C %d %d %d %d %d %d" % (BLOOM_Y + 18, sx * 18, BLOOM_Y + 16, sx * 30, BLOOM_Y + 2, sx * 26, BLOOM_Y - 8,
                                                              sx * 22, BLOOM_Y - 16, sx * 14, BLOOM_Y - 10, sx * 18, BLOOM_Y - 4)
        s += LN(d, INK, 6) + LN(d, VINEL, 3)
    # the black lotus: a fan of dark petals around the glowing heart
    bx, by = 0, BLOOM_Y
    for ang, ln, f in ((-78, 30, PET3), (78, 30, PET3), (-50, 38, PET2), (50, 38, PET2), (-22, 44, PET), (22, 44, PET), (0, 46, PET2)):
        s += petal(bx, by + 10, ln, 12, ang, f, 3.5)
    for ang in (-36, 36, 0):
        s += petal(bx, by + 12, 22, 10, ang, PET3 if ang else PET2, 3)
    s += heart(bx, by - 2, 9)
    return RHAND(s)


def staff_glow():
    bx, by = 0, BLOOM_Y
    s = "".join(petal_tipglow(bx, by + 10, ln, 12, ang) for ang, ln in ((-50, 38), (50, 38), (-22, 44), (22, 44), (0, 46)))
    return RHAND(blur(s + CI(bx, by - 2, 16, HEART2, 0), 4) + CI(bx, by - 2, 4, HEARTC, 0))


def staff_leaves(rnd, k):
    """little leaves along the vine, swaying a few degrees each frame"""
    s = ""
    for i, (y, sx, ln) in enumerate(((10, 1, 20), (-26, -1, 22), (-60, 1, 24), (-94, -1, 20), (-122, 1, 18))):
        sway = 9 * math.sin(k * 2.1 + i * 1.3)
        s += leaf(sx * 4, y, ln, 7.5, sx * (62 + sway), LEAF if i % 2 else LEAFL, 2.8)
    return RHAND(s)


def hand2c(x, y):
    a = math.radians(14)
    bx, by = 166 + x * math.cos(a) - y * math.sin(a), 200 + x * math.sin(a) + y * math.cos(a)
    return bx * 2, (by + 16) * 2


# ---------------------------------------------------------------- aura: a garden at the feet, petals, butterflies
def lily_pad(x, y, rx, ry, rot=0):
    s = P("M %.1f %.1f A %.1f %.1f 0 1 0 %.1f %.1f L %.1f %.1f Z" % (x + rx * 0.2, y - ry * 0.98, rx, ry, x + rx * 0.45, y - ry * 0.9, x, y), LEAF, 3)
    s += LN("M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f" % (x, y, x - rx * 0.7, y + ry * 0.2, x, y, x + rx * 0.1, y + ry * 0.8), LEAF2, 1.6)
    return s


def small_lotus(x, y, r, k, i):
    s = ""
    open_ = 1 + 0.12 * math.sin(k * 2.1 + i)
    for a, f in ((-70, PET3), (70, PET3), (-38, PET2), (38, PET2), (0, PET)):
        s += petal(x, y, r * (1.2 if a == 0 else 1.0), r * 0.42, a * open_, f, 2.6)
    s += heart(x, y - r * 0.25, r * 0.3)
    return s


GARDEN = [  # x, y, kind, size
    (26, 222, "pad", 16), (48, 232, "pad", 12), (210, 224, "pad", 15), (232, 232, "pad", 11),
    (36, 216, "lotus", 16), (220, 218, "lotus", 15), (72, 232, "lotus", 10), (186, 233, "lotus", 10),
    (14, 214, "grass", 12), (60, 222, "grass", 10), (198, 222, "grass", 10), (244, 214, "grass", 12),
    (106, 236, "pad", 9), (150, 236, "pad", 9),
]


def garden(rnd, k):
    s = ""
    for i, (x, y, kind, r) in enumerate(GARDEN):
        if kind == "pad": s += lily_pad(x, y, r, r * 0.45)
    for i, (x, y, kind, r) in enumerate(GARDEN):
        if kind == "grass":
            for j, a in enumerate((-24, -6, 14)):
                a2 = a + 6 * math.sin(k * 2.1 + i + j)
                s += at(x + j * 3 - 3, y, a2, P("M -3 0 Q -2 %.1f 0 %.1f Q 2 %.1f 3 0 Z" % (-r * 0.6, -r * 1.3, -r * 0.6), LEAFL if j == 1 else LEAF, 2.2))
    for i, (x, y, kind, r) in enumerate(GARDEN):
        if kind == "lotus": s += small_lotus(x, y, r, k, i)
    glow = blur("".join(CI(x, y - r * 0.25, r * 0.5, HEART2, 0) for x, y, kind, r in GARDEN if kind == "lotus"), 3)
    return glow + s


def butterfly():
    up = "M 0 -1 C -6 -12 -15 -12 -14 -5 C -13 1 -6 2 0 0 Z"
    lo = "M 0 1 C -5 3 -11 7 -9 11 C -7 14 -2 9 0 2 Z"
    one = P(up, "#b88cff", 2) + P(lo, "#ff9fd8", 2) + CI(-9, -6, 2.2, HEART2, 0) + CI(-6, 7, 1.5, HEART2, 0)
    s = one + mirror(one, 0)
    s += EL(0, 1, 1.8, 7, INK, 0) + LN("M -1 -6 Q -4 -12 -6 -13 M 1 -6 Q 4 -12 6 -13", INK, 1.2)
    return sprite(s)


def petal_sprite():
    s = at(-4, 9, 30, P(petal_d(22, 8), PETL, 2.2) + LN("M 0 -10 Q 1 -15 0 -20", EDGEL, 2))
    return sprite(s)


# ---------------------------------------------------------------- data
chx, chy = H2C(HEART_H[0], HEART_H[1])
sbx, sby = hand2c(0, BLOOM_Y)
GOLDDUST = {"kind": "particles", "sprite": "a_spark", "blend": "ADD", "color": [1.0, 0.95, 0.6], "color2": [0.7, 1.0, 0.4]}

SET = {
    "key": "lotus", "name": "Lotus Bloom", "zone": None, "lua": "LotusBloom", "file": "lotus_bloom",
    "prof": "herbalism", "spec": None, "title": "Lotus Keeper",
    "about": "Lotus Bloom set: the Herbalism long chase, the Black Lotus and a garden in bloom; the whole set gives the title Lotus Keeper.",
    "preview_fur": "fur_ginger",
    "pieces": [
        {"id": "set_lotus_head", "slot": "head", "kind": "head", "art": "lotus_head", "name": "Crown of the Black Lotus", "rarity": 5,
         "icon": "INV_Misc_Herb_BlackLotus", "word": "crown",
         "svg": crown(), "layers": {"mask": crown_mask(), "glow": crown_glow(), "bfly": butterfly()},
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K("lotus_head", "mask"), "scale": 170, "vx": 46, "vy": 0, "color": [0.9, 0.7, 1.0], "blend": "ADD", "alpha": 0.35},
             {"kind": "pulse", "key": K("lotus_head", "glow"), "a": [0.15, 0.75], "speed": 2.0, "blend": "ADD"},
             dict(GOLDDUST, n=6, box=[chx - 40, chy - 30, chx + 40, chy + 4], vx=[-14, 14], vy=[-50, -26], life=[1.2, 2.0], size=[8, 14], sway=8, at="front"),
             {"kind": "glint", "spots": "piece", "sprite": "t_sparkle", "n": 2, "size": [16, 24], "color": [1.0, 0.95, 0.7], "gap": [0.6, 1.6]},
             {"kind": "particles", "sprite": "k_lotus_head_bfly", "n": 1, "box": [140, 20, 372, 70], "vx": [-14, 14], "vy": [-10, 4], "life": [3.0, 4.0],
              "size": [24, 30], "sway": 16, "at": "front"},
         ]},
        {"id": "set_lotus_cape", "slot": "back", "kind": "back", "art": "lotus_cape", "name": "Cloak of a Thousand Petals", "rarity": 4,
         "icon": "INV_Misc_Cape_17", "word": "cape",
         "svg": cape(), "layers": {"mask": cape_mask(), "glow": cape_glow(), "petal": petal_sprite()},
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K("lotus_cape", "mask"), "scale": 170, "vx": 0, "vy": 40, "color": [0.9, 0.7, 1.0], "blend": "ADD", "alpha": 0.35},
             {"kind": "pulse", "key": K("lotus_cape", "glow"), "a": [0.1, 0.7], "speed": 1.8, "blend": "ADD"},
             {"kind": "particles", "sprite": "t_leaf", "n": 4, "box": [30, 260, 482, 360], "vx": [-14, 14], "vy": [30, 55], "life": [1.8, 2.6],
              "size": [14, 20], "spin": [-1.5, 1.5], "sway": 8, "color": [0.55, 0.95, 0.45], "at": "behind"},
             {"kind": "particles", "sprite": "k_lotus_cape_petal", "n": 3, "box": [30, 260, 482, 360], "vx": [-12, 12], "vy": [28, 46], "life": [2.0, 2.8],
              "size": [16, 22], "spin": [-1.2, 1.2], "sway": 10, "at": "behind"},
         ]},
        {"id": "set_lotus_weapon", "slot": "main", "kind": "weapon", "art": "lotus_weapon", "name": "Staff of the Living Vine", "rarity": 4,
         "icon": "INV_Staff_25", "word": "staff",
         "svg": staff(), "layers": dict(frames(3, staff_leaves), glow=staff_glow()),
         "anim": [
             {"kind": "flip", "keys": [K("lotus_weapon", "fl%d" % i) for i in range(1, 4)], "fps": 4},
             {"kind": "pulse", "key": K("lotus_weapon", "glow"), "a": [0.3, 1.0], "speed": 2.4, "blend": "ADD"},
             dict(GOLDDUST, n=5, box=[sbx - 26, sby - 30, sbx + 26, sby + 4], vx=[-14, 14], vy=[-50, -26], life=[1.2, 1.8], size=[8, 14], sway=8, at="front"),
             {"kind": "glint", "spots": [[sbx - 30, sby - 40, sbx + 30, sby + 10]], "sprite": "t_sparkle", "n": 1, "size": [18, 26], "color": [1.0, 0.95, 0.7], "gap": [0.6, 1.4]},
         ]},
        {"id": "set_lotus_aura", "slot": "effect", "kind": "effect", "art": "lotus_aura", "name": "Everbloom Garden", "rarity": 5,
         "icon": "Spell_Nature_Rejuvenation", "word": "aura", "glow": (0.6, 1.0, 0.45),
         "fx": {"layer": "back", "anim": "float"},
         "layers": dict(frames(3, garden), bfly=butterfly(), petal=petal_sprite()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [0.6, 1.0, 0.45], "a": [0.2, 0.5], "speed": 1.4, "blend": "ADD", "at": "behind"},
             {"kind": "flip", "keys": [K("lotus_aura", "fl%d" % i) for i in range(1, 4)], "fps": 3, "at": "front"},
             {"kind": "particles", "sprite": "k_lotus_aura_petal", "n": 5, "box": [40, 0, 472, 160], "vx": [-16, 16], "vy": [36, 60], "life": [3.0, 4.2],
              "size": [22, 30], "spin": [-1.2, 1.2], "sway": 14, "at": "front"},
             {"kind": "particles", "sprite": "t_leaf", "n": 4, "box": [40, 0, 472, 200], "vx": [-14, 14], "vy": [40, 64], "life": [3.0, 4.0],
              "size": [14, 20], "spin": [-1.5, 1.5], "sway": 10, "color": [0.55, 0.95, 0.45], "at": "behind"},
             {"kind": "particles", "sprite": "k_lotus_aura_bfly", "n": 3, "box": [40, 120, 472, 420], "vx": [-18, 18], "vy": [-24, -8], "life": [3.0, 4.2],
              "size": [30, 40], "sway": 18, "at": "front"},
             {"kind": "glint", "spots": [[40, 120, 120, 420], [392, 120, 472, 420], [120, 40, 392, 110]], "sprite": "t_sparkle", "n": 5,
              "size": [16, 26], "color": [1.0, 0.95, 0.6], "gap": [0.3, 1.0], "life": 0.9},
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
