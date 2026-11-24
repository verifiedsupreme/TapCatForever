"""Devilsaur Hunter set (1.7.0): a leatherworking long chase (Tribal). An Un'Goro jungle hunter's trophies:
green devilsaur hide with dark tiger stripes, a devilsaur-skull helm whose jaws frame the cat's face, claw
spaulders with dangling feather charms, a hide vest with a bone-and-tooth necklace around a glowing Un'Goro
crystal, a cape of jungle leaves and bright feathers, a huge devilsaur-claw glaive and an aura of drifting
jungle leaves, swaying ferns, dust puffs and green-gold glints. Crafted over months; the full set gives the
title Devilsaur Hunter.
  python3 tools/sets/devilsaur_hunter.py            -> Art/v/k_devilsaur_*.tga, Art/devilsaur_*.tga, Sets/DevilsaurHunter.lua
  python3 tools/set_preview.py tools/sets/devilsaur_hunter.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: devilsaur hide, tiger stripes, old bone, jungle leaves, tribal feathers, Un'Goro crystal
HIDE, HIDE2, HIDED = "#5f8f3a", "#7cad4c", "#3e6428"
STRIPE = "#4a3020"
BONE, BONE2, BONED = "#f1e6c8", "#d6c69e", "#9e8c66"
WOOD, WOOD2 = "#7a4c2a", "#9c6a3c"
LEATH, LEATH2 = "#8a5a32", "#b07a46"
LEAF, LEAF2, LEAFD, LEAFV = "#3f9a3e", "#68c24c", "#2a6a2c", "#c6ec72"
FRED, FTEAL, FGOLD = "#d8482e", "#2aa89c", "#f2c14e"
CRYS, CRYS2, CRYSC = "#3fd46a", "#9cff9a", "#eaffd8"
PAINT = "#c0442c"
GOLDC = [1.0, 0.88, 0.45]
GREENC = [0.6, 1.0, 0.45]

def frames(n, fn, seed=2700):
    return {"fl%d" % (k + 1): fn(random.Random(seed + k), k) for k in range(n)}

WIDEBLUR = ('<defs><filter id="wblur" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1100" height="1100">'
            '<feGaussianBlur stdDeviation="5"/></filter></defs>')
def blur(s): return WIDEBLUR + '<g filter="url(#wblur)">%s</g>' % s

def sprite(inner, S=32):
    """a small particle sprite: the drawing centred in an exact S x S box (faint corner dots fix the crop)"""
    dots = ('<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/>'
            '<rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S))
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)

def cub(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])

def rot(x, y, ang, s): return '<g transform="translate(%.1f %.1f) rotate(%.1f)">%s</g>' % (x, y, ang, s)

def feather(x, y, ang, L, col, tip=None, ink=2.0):
    """a tribal feather hanging or standing from (x, y), pointing along ang (0 = up)"""
    w = L * 0.27
    s = P("M 0 0 Q %.1f %.1f 0 %.1f Q %.1f %.1f 0 0 Z" % (-w, -L * 0.45, -L, w, -L * 0.45), col, ink)
    if tip:
        s += P("M %.1f %.1f Q %.1f %.1f 0 %.1f Q %.1f %.1f %.1f %.1f Q 0 %.1f %.1f %.1f Z" % (-w * 0.78, -L * 0.72, -w * 0.6, -L * 0.86, -L + 1.5,
                                                                                       w * 0.6, -L * 0.86, w * 0.78, -L * 0.72, -L * 0.78, -w * 0.78, -L * 0.72), tip, 0)
    s += LN("M 0 %.1f L 0 %.1f" % (2, -L * 0.92), darker(col, 0.6), 1.4)
    s += LN("M %.1f %.1f L %.1f %.1f" % (-w * 0.95, -L * 0.42, -w * 0.3, -L * 0.36), INK, 1.4)
    s += LN("M %.1f %.1f L %.1f %.1f" % (w * 0.95, -L * 0.55, w * 0.3, -L * 0.5), INK, 1.4)
    return rot(x, y, ang, s)

def leaf(x, y, ang, L, col=LEAF, vein=LEAFV, ink=2.4):
    """a broad jungle leaf with a midrib and side veins, pointing along ang (0 = up)"""
    w = L * 0.36
    s = P("M 0 0 C %.1f %.1f %.1f %.1f 0 %.1f C %.1f %.1f %.1f %.1f 0 0 Z" % (-w * 1.2, -L * 0.2, -w, -L * 0.8, -L, w, -L * 0.8, w * 1.2, -L * 0.2), col, ink)
    s += LN("M 0 2 L 0 %.1f" % (-L * 0.88), vein, 1.5)
    for t in (0.3, 0.52, 0.72):
        s += LN("M 0 %.1f L %.1f %.1f M 0 %.1f L %.1f %.1f" % (-L * t, -w * 0.7, -L * (t + 0.12), -L * t, w * 0.7, -L * (t + 0.12)), vein, 1.1, .8)
    return rot(x, y, ang, s)

def wedge(x, y, ang, L, t, col=STRIPE):
    """one tiger stripe: a dark wedge from (x, y) tapering to a point along ang (0 = right)"""
    return rot(x, y, ang, '<path d="M 0 %.1f Q %.1f %.1f %.1f 0 Q %.1f %.1f 0 %.1f Z" fill="%s"/>' % (-t / 2.0, L * 0.5, -t * 0.7, L, L * 0.5, t * 0.15, t / 2.0, col))

def stripes(edges, y0, y1, step, clip, rnd, ln=(22, 36), t=7):
    """devilsaur tiger stripes reaching in from the given edges [(x, direction)], in rows, inside a clip"""
    s = ""
    y, row = y0, 0
    while y <= y1:
        for x, dirn in edges:
            L = rnd.uniform(*ln)
            a = (0 if dirn > 0 else 180) + rnd.uniform(-12, 12) * dirn + (row % 2) * 6 * dirn
            s += wedge(x, y + rnd.uniform(-2, 2), a, L, t * rnd.uniform(0.8, 1.15))
        y += step; row += 1
    return '<g clip-path="url(#%s)">%s</g>' % (clip, s)

def tooth(x, y, L, w, ang=0, col=BONE, ink=2.4):
    """a conical tooth hanging from (x, y) (ang 0 = pointing down)"""
    s = P("M %.1f 0 Q %.1f %.1f 0 %.1f Q %.1f %.1f %.1f 0 Z" % (-w, -w * 0.8, L * 0.6, L, w * 0.8, L * 0.6, w), col, ink)
    s += LN("M %.1f %.1f Q %.1f %.1f %.1f %.1f" % (-w * 0.45, 2, -w * 0.4, L * 0.45, -w * 0.05, L * 0.8), "#ffffff", 1.2, .7)
    return rot(x, y, ang, s)

# ---------------------------------------------------------------- helm: devilsaur skull, jaws around the face (head space)
SKULL = "M 30 104 C 18 50 50 2 128 0 C 206 2 238 50 226 104 Z"
SOCKETS = [(80, 50), (176, 50)]
TEETH = [(52, 12, 5.5), (68, 17, 6.5), (86, 22, 7.5), (106, 15, 6.5), (128, 13, 6), (150, 15, 6.5), (170, 22, 7.5), (188, 17, 6.5), (204, 12, 5.5)]

def jaw_side():
    """the lower jaw bone along the left cheek, its teeth pointing up and in, a big fang at the front"""
    d = "M 30 94 Q 16 128 38 160 Q 50 166 58 156 Q 40 130 46 100 Z"
    s = P(d, BONE2, 4.5) + LN("M 32 104 Q 26 130 40 152", "#ffffff", 2, .5)
    for y, L in ((118, 11), (134, 10)):
        s += tooth(44 + (y - 118) * 0.1, y, L, 3.8, ang=-112)
    s += tooth(52, 156, 16, 5, ang=200)
    return s

def feather_fan():
    s = ""
    for ang, L, col, tip in ((-100, 50, FGOLD, FRED), (-78, 66, FRED, BONE), (-56, 74, FTEAL, INK), (-36, 60, FRED, FGOLD)):
        s += feather(44, 64, ang, L, col, tip)
    return s + CI(44, 64, 7, FTEAL, 3) + CI(42, 62, 2, "#ffffff", 0)

def helm():
    s = feather_fan() + mirror(feather_fan(), 128)
    s += jaw_side() + mirror(jaw_side(), 128)
    # little horns behind the eyes
    for sx in (-1, 1):
        s += P("M %d 40 L %d 10 L %d 30 Z" % (128 + sx * 70, 128 + sx * 92, 128 + sx * 88), BONE2, 3.5)
        s += P("M %d 28 L %d 4 L %d 20 Z" % (128 + sx * 52, 128 + sx * 62, 128 + sx * 66), BONE2, 3.5)
    s += P(SKULL, BONE, 5)
    s += '<clipPath id="dshskull"><path d="%s"/></clipPath>' % SKULL
    s += '<g clip-path="url(#dshskull)">%s</g>' % (P("M 18 104 C 26 70 36 40 66 18 C 46 56 56 84 64 104 Z", BONE2, 0)
                                                     + P("M 238 104 C 230 70 220 40 190 18 C 210 56 200 84 192 104 Z", BONE2, 0))
    s += LN("M 128 4 Q 122 14 128 24", BONED, 2) + LN("M 56 34 Q 66 40 62 54", BONED, 2) + LN("M 200 34 Q 190 40 194 54", BONED, 2)
    # three red claw slashes of war paint across the crown
    for k in range(3):
        x = 98 + k * 15
        s += P("M %d 6 Q %d 22 %d 40 L %d 40 Q %d 22 %d 8 Z" % (x, x + 10, x + 22, x + 26, x + 16, x + 6), PAINT, 0)
    # deep angry sockets under a heavy brow shelf
    for sx in (-1, 1):
        ex, ey = SOCKETS[0 if sx < 0 else 1]
        sock = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (128 + sx * 76, 42, 128 + sx * 50, 34, 128 + sx * 24, 54,
                                                                       128 + sx * 36, 68, 128 + sx * 52, 66, 128 + sx * 72, 62, 128 + sx * 76, 42)
        s += P(sock, "#2a1a14", 4)
        s += EL(ex + sx * 2, ey + 4, 6, 4, "#ffb02e", 0, rot=sx * 20) + CI(ex + sx * 2, ey + 4, 1.8, "#fff6c0", 0)
        brow = "M %d %d Q %d %d %d %d L %d %d Q %d %d %d %d Z" % (128 + sx * 84, 44, 128 + sx * 54, 20, 128 + sx * 18, 46,
                                                                 128 + sx * 22, 54, 128 + sx * 52, 32, 128 + sx * 78, 50)
        s += P(brow, BONE2, 4)
    # the snout ridge and nostrils between the eyes
    s += P("M 116 76 Q 112 52 128 40 Q 144 52 140 76 Z", BONE2, 4) + EL(121, 68, 4.5, 3, "#2a1a14", 0, rot=-30) + EL(135, 68, 4.5, 3, "#2a1a14", 0, rot=30)
    # a striped hide strap that ties the skull on
    strap = "M 34 90 Q 128 70 222 90"
    s += LN(strap, INK, 13) + LN(strap, HIDE, 8.5)
    for k in range(9):
        x = 46 + k * 20.5
        y = 90 - 20 * (1 - ((x - 128) / 94.0) ** 2) * 0.95
        s += LN("M %.1f %.1f L %.1f %.1f" % (x - 2, y - 3.5, x + 3, y + 3.5), STRIPE, 2.6)
    # the upper jaw and its huge teeth over the brow
    jaw = "M 38 100 Q 128 84 218 100"
    s += LN(jaw, INK, 15) + LN(jaw, BONE2, 10) + LN("M 46 97 Q 128 84 210 97", "#ffffff", 2, .6)
    for x, L, w in TEETH:
        s += tooth(x, tooth_y(x), L, w)
    return HEAD(s)

def tooth_y(x): return 100 - 14 * (1 - ((x - 128) / 90.0) ** 2) + 3

def helm_teeth_mask():
    s = ""
    for x, L, w in TEETH:
        y = tooth_y(x)
        s += rot(x, y, 0, '<path d="M %.1f 0 Q %.1f %.1f 0 %.1f Q %.1f %.1f %.1f 0 Z" fill="#fff"/>' % (-w, -w * 0.8, L * 0.6, L, w * 0.8, L * 0.6, w))
    return HEAD(s)

def helm_eyes():
    s = ""
    for sx in (-1, 1):
        ex, ey = SOCKETS[0 if sx < 0 else 1]
        s += blur(EL(ex + sx * 2, ey + 4, 14, 9, "#ffc23a", 0, rot=sx * 20)) + EL(ex + sx * 2, ey + 4, 6, 4, "#ffe27a", 0, rot=sx * 20) + CI(ex + sx * 2, ey + 4, 2.2, "#ffffff", 0)
    return HEAD(s)

def charm(x, y, ang, L, col, tip):
    """a feather charm on a cord: cord, bead, feather hanging down"""
    s = LN("M 0 0 L 0 10", LEATH, 2.2) + CI(0, 12, 3.6, FTEAL, 2) + feather(0, 14, 180, L, col, tip)
    return rot(x, y, ang, s)

def helm_charms(rnd, k):
    swing = (-12, 0, 12, 0)[k]
    s = ""
    for sx in (-1, 1):
        x = 128 + sx * 92
        s += charm(x, 106, swing + sx * 6 + rnd.uniform(-3, 3), 26, FRED if sx < 0 else FGOLD, INK)
    return HEAD(s)

# ---------------------------------------------------------------- shoulders: striped hide with devilsaur claws (body space)
CLAWS = [((-34, -4), (-52, -14), (-62, -34), (-56, -54), (-48, -40), (-36, -26), (-20, -14)),
         ((-18, -16), (-28, -34), (-26, -54), (-12, -68), (-12, -50), (-6, -36), (-2, -20)),
         ((2, -20), (4, -36), (12, -48), (26, -56), (20, -42), (18, -30), (18, -16))]
def claw(b0, c1, c2, tip, c3, c4, b1, col=BONE, ink=3.5):
    d = "M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f Z" % (b0 + c1 + c2 + tip + c3 + c4 + b1)
    s = P(d, col, ink)
    sh = [cub(b0, c1, c2, tip, 0.15 + 0.6 * i / 5.0) for i in range(6)]
    sh = [(x + (b1[0] - b0[0]) * 0.22, y + (b1[1] - b0[1]) * 0.22) for x, y in sh]
    s += LN("M " + " L ".join("%.1f %.1f" % p for p in sh), "#ffffff", 2, .6)
    base = [cub(b0, c1, c2, tip, 0.0), cub(b0, c1, c2, tip, 0.18), cub(tip, c3, c4, b1, 0.82), b1]
    s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (base[0] + base[1] + base[2] + base[3]), BONED, 0)
    return s + P(d, "none", ink)

def paul_dome():
    cx, cy = SH_C
    return "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 32, cy + 10, cx + 28, cy - 26, cx - 6, cy - 24,
        cx - 40, cy - 22, cx - 42, cy + 12, cx - 4, cy + 26, cx + 32, cy + 10)

def pauldron():
    cx, cy = SH_C
    s = ""
    for c in CLAWS: s += claw(*[(cx + x, cy + y) for x, y in c])
    dome = paul_dome()
    s += P(dome, HIDE, 5)
    s += '<clipPath id="dshpaul"><path d="%s"/></clipPath>' % dome
    s += '<g clip-path="url(#dshpaul)">%s</g>' % P("M %d %d Q %d %d %d %d L %d %d Z" % (cx - 44, cy - 20, cx - 10, cy - 30, cx + 30, cy - 22, cx + 30, cy - 40), HIDE2, 0)
    s += stripes([(cx - 46, 1), (cx + 34, -1)], cy - 22, cy + 22, 9, "dshpaul", random.Random(5), ln=(14, 26), t=5.5)
    s += P(dome, "none", 5)
    # bone rim with a fringe of small teeth
    hem = "M %d %d Q %d %d %d %d" % (cx - 40, cy + 10, cx - 6, cy + 26, cx + 30, cy + 8)
    s += LN(hem, INK, 11) + LN(hem, BONE2, 7) + LN(hem, "#ffffff", 1.5, .5)
    for t in (0.1, 0.3, 0.5, 0.7, 0.9):
        x, y = cub((cx - 40, cy + 10), (cx - 28, cy + 21), (cx + 18, cy + 20), (cx + 30, cy + 8), t)
        s += tooth(x, y + 2, 9, 3.4)
    # an Un'Goro crystal stud
    gx, gy = cx - 8, cy - 2
    s += P("M %d %d L %d %d L %d %d L %d %d Z" % (gx, gy - 9, gx + 7, gy, gx, gy + 9, gx - 7, gy), CRYS, 3) + P("M %d %d L %d %d L %d %d Z" % (gx, gy - 9, gx + 7, gy, gx, gy), CRYS2, 0)
    return BOTH(s)

def pauldron_glow():
    cx, cy = SH_C
    return BOTH(blur(CI(cx - 8, cy - 2, 7, CRYS2, 0)) + P("M %d %d L %d %d L %d %d L %d %d Z" % (cx - 8, cy - 7, cx - 4, cy - 2, cx - 8, cy + 3, cx - 12, cy - 2), CRYSC, 0))

def pauldron_claw_mask():
    cx, cy = SH_C
    s = ""
    for c in CLAWS:
        q = [(cx + x, cy + y) for x, y in c]
        s += '<path d="M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f Z" fill="#fff"/>' % tuple(v for p in q for v in p)
    return BOTH(s)

def pauldron_charms(rnd, k):
    cx, cy = SH_C
    swing = (-14, 0, 14, 0)[k]
    return BOTH(charm(cx - 38, cy + 12, swing + 10, 24, FTEAL, FRED))

# ---------------------------------------------------------------- chest: striped hide vest, bone-and-tooth necklace (body space)
NECK = ((80, 122), (96, 152), (160, 152), (176, 122))
def necklace_pts(n):
    return [cub(NECK[0], NECK[1], NECK[2], NECK[3], 0.1 + 0.8 * i / float(n - 1)) for i in range(n)]

def chest():
    s = P(BODY_OUT, HIDE, 5)
    s += '<g clip-path="url(#chestclip)">%s</g>' % (P("M 60 214 Q 70 150 90 116 L 60 116 Z", HIDED, 0) + P("M 196 214 Q 186 150 166 116 L 196 116 Z", HIDED, 0))
    s += stripes([(54, 1), (202, -1)], 122, 214, 12, "chestclip", random.Random(11), ln=(24, 40), t=7) + stripes([(112, -1), (144, 1)], 128, 196, 16, "chestclip", random.Random(12), ln=(10, 16), t=5)
    # the vest opening laced up the middle
    s += P("M 112 150 Q 128 146 144 150 L 140 214 L 116 214 Z", LEATH, 3.5)
    for y in (166, 182, 198):
        s += LN("M 116 %d L 140 %d M 116 %d L 140 %d" % (y - 5, y + 5, y + 5, y - 5), BONE2, 2.4)
    s += P(BODY_OUT, "none", 5)
    # the necklace: a cord with fangs, beads and claws, and the crystal pendant
    d = "M %d %d C %d %d %d %d %d %d" % (NECK[0] + NECK[1] + NECK[2] + NECK[3])
    s += LN(d, INK, 5.5) + LN(d, LEATH2, 3)
    for i, (x, y) in enumerate(necklace_pts(9)):
        if i == 4: continue
        if i % 2 == 0:
            ang = (x - 128) * 0.5
            s += tooth(x, y, 15 if i in (2, 6) else 12, 4.2, ang=ang)
        else:
            s += CI(x, y + 1, 4, (FRED, FTEAL)[(i // 2) % 2], 2.2)
    px, py = 128, 158
    s += CI(px, py, 13, BONE2, 4) + CI(px, py, 13, "none", 0)
    for a in range(0, 360, 45):
        s += LN("M %.1f %.1f L %.1f %.1f" % (px + math.cos(math.radians(a)) * 9.5, py + math.sin(math.radians(a)) * 9.5,
                                           px + math.cos(math.radians(a)) * 12, py + math.sin(math.radians(a)) * 12), BONED, 1.6)
    s += P("M %d %d L %d %d L %d %d L %d %d Z" % (px, py - 9, px + 6, py, px, py + 9, px - 6, py), CRYS, 2.6) + P("M %d %d L %d %d L %d %d Z" % (px, py - 9, px + 6, py, px, py), CRYS2, 0)
    # belt with bone toggles
    s += RC(60, 198, 136, 14, LEATH, 4, 4) + LN("M 64 205 L 192 205", "#6a4426", 2)
    for x in (80, 176): s += RC(x - 8, 201, 16, 8, BONE, 3, 2.4)
    return s

def chest_teeth_mask():
    s = ""
    for i, (x, y) in enumerate(necklace_pts(9)):
        if i % 2 == 0 and i != 4:
            L, w = (15 if i in (2, 6) else 12), 4.2
            s += rot(x, y, (x - 128) * 0.5, '<path d="M %.1f 0 Q %.1f %.1f 0 %.1f Q %.1f %.1f %.1f 0 Z" fill="#fff"/>' % (-w, -w * 0.8, L * 0.6, L, w * 0.8, L * 0.6, w))
    return s + CI(128, 158, 12, "#ffffff", 0)

def chest_glow():
    px, py = 128, 158
    return blur(CI(px, py, 14, CRYS2, 0)) + P("M %d %d L %d %d L %d %d L %d %d Z" % (px, py - 7, px + 4, py, px, py + 7, px - 4, py), CRYSC, 0)

# ---------------------------------------------------------------- cape: jungle leaves and feathers (side drapes)
def cape():
    s = "".join(P(p, LEAFD, 5) for p in DRAPE_OUT) + "".join(P(p, HIDED, 3) for p in DRAPE_IN)
    s += '<clipPath id="dshdrape"><path d="%s"/><path d="%s"/></clipPath>' % DRAPE_OUT
    # rows of overlapping leaves hanging down the drapes (lower rows first)
    rnd = random.Random(41)
    body = ""
    for row in range(5, -1, -1):
        y = 112 + row * 18
        for side in (-1, 1):
            for j in range(4):
                x = 128 + side * (40 + j * 16 + row * 4 + (8 if row % 2 else 0))
                col = (LEAF, LEAF2, "#4fae3e")[(row + j) % 3]
                body += leaf(x, y, 180 + side * (-12 - j * 4) + rnd.uniform(-6, 6), 26, col)
    s += '<g clip-path="url(#dshdrape)">%s</g>' % body
    for p in DRAPE_OUT: s += P(p, "none", 5)
    # a strip of striped hide at the top where the cape is tied
    for sx in (-1, 1):
        x = 128 + sx * 52
        s += P("M %d 108 Q %d 104 %d 112 L %d 126 Q %d 120 %d 122 Z" % (x - sx * 18, x, x + sx * 14, x + sx * 4, x - sx * 6, x - sx * 22), HIDE, 3.5)
        s += LN("M %d 110 L %d 120" % (x - sx * 4, x - sx * 2), STRIPE, 2.6) + CI(x, 116, 3.5, BONE, 2)
    return s

EDGE_FEATHERS = [(FRED, BONE), (FGOLD, FRED), (FTEAL, INK), (FRED, BONE), (FGOLD, FTEAL), (FTEAL, FGOLD)]
def cape_feathers(rnd, k):
    """the long feathers along the outer edges, ruffling in the jungle breeze"""
    s = ""
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=7)[1:]
        sgn = -1 if pts[0][0] < 128 else 1
        for i, (x, y) in enumerate(pts):
            col, tip = EDGE_FEATHERS[i % len(EDGE_FEATHERS)]
            base = sgn * (62 + i * 12)
            wob = math.sin(k * math.pi / 2 + i * 1.3) * 7
            s += feather(x + sgn * 2, y, base + wob, 26 + (i % 2) * 6, col, tip)
    return s

# ---------------------------------------------------------------- glaive: a huge devilsaur claw on a hide-wrapped haft (right paw)
CL0, CL1, CL2, CLT, CL3, CL4, CL5 = (-12, -128), (-26, -162), (-8, -204), (32, -212), (12, -194), (6, -160), (14, -126)
CLAW_D = "M %d %d C %d %d %d %d %d %d C %d %d %d %d %d %d Z" % (CL0 + CL1 + CL2 + CLT + CL3 + CL4 + CL5)
def glaive():
    s = RC(-5.5, -126, 11, 168, WOOD, 4, 4) + LN("M -2 -120 L -2 36", WOOD2, 2.2)
    for y0 in (-96, -40, 4):
        s += RC(-8, y0, 16, 22, HIDE, 3, 3.2) + LN("M -6 %d L 6 %d M -6 %d L 6 %d" % (y0 + 6, y0 + 2, y0 + 15, y0 + 11), STRIPE, 2.4)
    s += P("M -5 40 L 0 58 L 5 40 Z", BONE, 2.5)
    # the back spur: a smaller claw
    s += claw((-8, -118), (-22, -118), (-34, -126), (-40, -144), (-30, -134), (-18, -132), (-6, -130), ink=3.2)
    # the great claw
    s += P(CLAW_D, BONE, 5)
    s += P("M -6 -132 C -16 -160 -4 -196 26 -208 C 4 -192 -4 -164 2 -132 Z", "#ffffff", 0, ' opacity=".5"')
    s += LN("M 10 -134 C 4 -160 12 -188 28 -206", BONE2, 2.4)
    s += P("M -12 -128 C -14 -138 -14 -146 -12 -150 L 10 -150 C 8 -142 10 -134 14 -126 Z", BONED, 0)
    s += P(CLAW_D, "none", 5)
    # leather lashing and the crystal
    s += RC(-12, -134, 24, 14, LEATH, 3, 3.5) + LN("M -10 -130 L 10 -124 M -10 -124 L 10 -130", "#5a3a20", 2)
    s += P("M 0 -118 L 6 -110 L 0 -102 L -6 -110 Z", CRYS, 2.6) + P("M 0 -118 L 6 -110 L 0 -110 Z", CRYS2, 0)
    return RHAND(s)

def glaive_mask():
    return RHAND(P(CLAW_D, "#ffffff", 0))

def glaive_glow():
    return RHAND(blur(CI(0, -110, 11, CRYS2, 0)) + P("M 0 -114 L 3 -110 L 0 -106 L -3 -110 Z", CRYSC, 0))

def glaive_charms(rnd, k):
    swing = (-14, 0, 14, 0)[k]
    s = charm(-10, -122, swing + 16, 28, FRED, BONE) + charm(10, -122, swing - 6, 24, FTEAL, FGOLD)
    return RHAND(s)

# ---------------------------------------------------------------- aura: swaying ferns, drifting leaves, dust and glints
def fern(x, y, ang, L, col, k):
    """a fern frond rising from (x, y), its tip bending with the sway"""
    s = ""
    pts = []
    for i in range(9):
        t = i / 8.0
        bend = math.radians(ang + t * t * (25 + 10 * math.sin(k * math.pi / 2)) * (1 if ang >= 0 else -1))
        pts.append((x + math.sin(bend) * L * t, y - math.cos(bend) * L * t))
    d = "M " + " L ".join("%.1f %.1f" % p for p in pts)
    for i in range(1, 8):
        (px, py), (qx, qy) = pts[i], pts[i + 1]
        a = math.degrees(math.atan2(qx - px, -(qy - py)))
        ln = 12 * (1 - i / 9.0) + 4
        s += leaf(px, py, a - 60, ln, col, LEAFV, 1.8) + leaf(px, py, a + 60, ln, col, LEAFV, 1.8)
    s += LN(d, INK, 4) + LN(d, LEAF2, 2)
    return s

def ferns(rnd, k):
    s = blur('<ellipse cx="128" cy="214" rx="104" ry="10" fill="#6a5a2a" opacity=".5"/>')
    for x, ang, L, col in ((22, -34, 48, LEAF), (40, -10, 56, "#4fae3e"), (58, 18, 38, LEAF2),
                           (234, 34, 48, LEAF), (216, 10, 56, "#4fae3e"), (198, -18, 38, LEAF2)):
        s += fern(x, 214, ang + math.sin(k * math.pi / 2 + x) * 4, L, col, k)
    return s

def leaf_sprite():
    return sprite(leaf(0, 12, 20, 26, LEAF2, LEAFV, 2.2))

GLINT = {"kind": "glint", "sprite": "a_spark", "blend": "ADD", "color": GOLDC, "at": "front"}

def A(part): return "devilsaur_" + part

SET = {
    "key": "devilsaur", "name": "Devilsaur Hunter", "zone": None, "lua": "DevilsaurHunter", "file": "devilsaur_hunter",
    "prof": "leatherworking", "spec": "tribal", "title": "Devilsaur Hunter",
    "about": "Devilsaur Hunter set: a leatherworking (Tribal) long chase, Un'Goro devilsaur trophies, leaves and feathers.",
    "preview_fur": "fur_ginger",
    "pieces": [
        {"id": "set_devilsaur_head", "slot": "head", "kind": "head", "art": A("head"), "name": "Tyrant King's Skull", "rarity": 5,
         "icon": "INV_Misc_Bone_TaurenSkull_01", "word": "helm",
         "svg": helm(), "layers": dict(frames(4, helm_charms), eyes=helm_eyes(), teeth=helm_teeth_mask()),
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K(A("head"), "teeth"), "scale": 60, "vx": 50, "vy": 10, "color": [1.0, 0.95, 0.7], "blend": "ADD", "alpha": 0.8},
             {"kind": "pulse", "key": K(A("head"), "eyes"), "a": [0.25, 1.0], "speed": 2.2, "blend": "ADD"},
             {"kind": "flip", "keys": [K(A("head"), "fl%d" % i) for i in range(1, 5)], "fps": 4},
             dict(GLINT, n=2, spots=[[150, 70, 362, 110]], size=[14, 22], gap=[0.5, 1.4]),
         ]},
        {"id": "set_devilsaur_shoulders", "slot": "shoulder", "kind": "shoulder", "art": A("shoulders"), "name": "Tyrant Claw Spaulders", "rarity": 4,
         "icon": "INV_Shoulder_14", "word": "shoulders",
         "svg": pauldron(), "layers": dict(frames(4, pauldron_charms), glow=pauldron_glow(), claws=pauldron_claw_mask()),
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K(A("shoulders"), "claws"), "scale": 60, "vx": 40, "vy": -30, "color": [1.0, 0.95, 0.7], "blend": "ADD", "alpha": 0.7},
             {"kind": "pulse", "key": K(A("shoulders"), "glow"), "a": [0.1, 0.75], "speed": 2.0, "blend": "ADD"},
             {"kind": "flip", "keys": [K(A("shoulders"), "fl%d" % i) for i in range(1, 5)], "fps": 4},
             dict(GLINT, n=2, spots=[[20, 140, 110, 200], [402, 140, 492, 200]], size=[14, 20], gap=[0.6, 1.6]),
         ]},
        {"id": "set_devilsaur_chest", "slot": "chest", "kind": "chest", "art": A("chest"), "name": "Toothcharm Devilsaur Vest", "rarity": 4,
         "icon": "INV_Chest_Leather_07", "word": "chest",
         "svg": chest(), "layers": {"teeth": chest_teeth_mask(), "glow": chest_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K(A("chest"), "teeth"), "scale": 60, "vx": 45, "vy": 12, "color": [1.0, 0.95, 0.7], "blend": "ADD", "alpha": 0.8},
             {"kind": "pulse", "key": K(A("chest"), "glow"), "a": [0.15, 0.9], "speed": 1.8, "blend": "ADD"},
             {"kind": "particles", "sprite": "a_glow", "n": 3, "box": [236, 300, 276, 330], "vx": [-10, 10], "vy": [-30, -15], "life": [0.9, 1.4],
              "size": [8, 12], "color": GREENC, "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_devilsaur_cape", "slot": "back", "kind": "back", "art": A("cape"), "name": "Featherleaf Cloak of Un'Goro", "rarity": 4,
         "icon": "INV_Misc_Cape_14", "word": "cape",
         "svg": cape(), "layers": frames(4, cape_feathers),
         "anim": [
             {"kind": "flip", "keys": [K(A("cape"), "fl%d" % i) for i in range(1, 5)], "fps": 4},
             {"kind": "particles", "sprite": "t_leaf", "n": 3, "box": [20, 300, 90, 400], "vx": [-16, -4], "vy": [25, 45], "life": [1.6, 2.4],
              "size": [11, 16], "sway": 10, "spin": [-2, 2], "color": [0.85, 1.0, 0.7], "at": "behind"},
             {"kind": "particles", "sprite": "t_leaf", "n": 3, "box": [422, 300, 492, 400], "vx": [4, 16], "vy": [25, 45], "life": [1.6, 2.4],
              "size": [11, 16], "sway": 10, "spin": [-2, 2], "color": [0.85, 1.0, 0.7], "at": "behind"},
         ]},
        {"id": "set_devilsaur_weapon", "slot": "main", "kind": "weapon", "art": A("weapon"), "name": "Tyrant's Talon Glaive", "rarity": 4,
         "icon": "INV_Spear_06", "word": "glaive",
         "svg": glaive(), "layers": dict(frames(4, glaive_charms), mask=glaive_mask(), glow=glaive_glow()),
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K(A("weapon"), "mask"), "scale": 70, "vx": 20, "vy": -60, "color": [1.0, 0.95, 0.7], "blend": "ADD", "alpha": 0.7},
             {"kind": "pulse", "key": K(A("weapon"), "glow"), "a": [0.2, 1.0], "speed": 2.4, "blend": "ADD"},
             {"kind": "flip", "keys": [K(A("weapon"), "fl%d" % i) for i in range(1, 5)], "fps": 4},
             dict(GLINT, n=1, spots=[[440, 24, 470, 56]], size=[16, 24], gap=[0.8, 1.6]),
         ]},
        {"id": "set_devilsaur_aura", "slot": "effect", "kind": "effect", "art": A("aura"), "name": "Breath of the Un'Goro Wilds", "rarity": 5,
         "icon": "Spell_Nature_ProtectionformNature", "word": "aura", "glow": (0.9, 0.8, 0.35),
         "fx": {"layer": "back", "anim": "pulse"},
         "layers": dict(frames(4, ferns), leaf=leaf_sprite()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [0.95, 0.78, 0.3], "a": [0.1, 0.3], "speed": 1.3, "blend": "ADD", "at": "behind"},
             {"kind": "flip", "keys": [K(A("aura"), "fl%d" % i) for i in range(1, 5)], "fps": 3, "at": "front"},
             {"kind": "particles", "sprite": "k_devilsaur_aura_leaf", "n": 5, "box": [-40, 40, 300, 380], "vx": [40, 70], "vy": [8, 28],
              "life": [3.0, 4.2], "size": [18, 26], "sway": 16, "spin": [-2.2, 2.2], "at": "front"},
             {"kind": "particles", "sprite": "t_leaf", "n": 5, "box": [30, -10, 482, 160], "vx": [-14, 14], "vy": [30, 55], "life": [3.0, 4.0],
              "size": [14, 20], "sway": 16, "spin": [-2.5, 2.5], "color": [0.8, 1.0, 0.6], "at": "behind"},
             {"kind": "particles", "sprite": "a_wisp", "n": 4, "box": [90, 430, 422, 470], "vx": [-14, 14], "vy": [-22, -10], "life": [1.2, 1.8],
              "size": [34, 50], "grow": 1.0, "color": [0.9, 0.78, 0.55], "alpha": 0.75, "at": "front"},
             dict(GLINT, n=4, spots=[[40, 80, 472, 460]], size=[14, 22], gap=[0.3, 0.9], color=[0.85, 1.0, 0.5]),
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
