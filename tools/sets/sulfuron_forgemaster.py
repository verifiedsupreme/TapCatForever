"""Sulfuron Forgemaster (1.7.0): the Weaponsmith's long-chase Blacksmithing set (title: Forgemaster).
A master weaponsmith fresh from the forge: blackened, hammered iron split by white-hot cracks, a forge
helm with a raised welding visor and a glowing blade for a crest, anvils on the shoulders with
white-hot ingots on them, a riveted forge apron, lamellar drapes with molten seams, a huge
Sulfuron-style hammer that throws sparks off both faces, and a fountain of forge sparks around the cat
(hammered metal and white-hot sparks, not Molten Core's lava and flame). Crafted, not dropped: no zone
or bosses, the recipes are in ProfSets.lua.
  python3 tools/sets/sulfuron_forgemaster.py   -> Art/v/k_sulfuron_*.tga, Art/sulfuron_*.tga, Sets/SulfuronForgemaster.lua
  python3 tools/set_preview.py tools/sets/sulfuron_forgemaster.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: blackened iron, hammered steel, cooling metal from cherry red to white-hot
IRON, IRON2, IRON3, STEEL = "#2e2a2b", "#433d3d", "#5e5654", "#9a9290"
LEATHER, LEATHER2, STITCH = "#5c3322", "#7a4630", "#c9935e"
CHERRY, ORANGE, YELLOW, WHITEHOT = "#d8361a", "#ff7a1c", "#ffc43a", "#fff6d6"
WHITE = "#ffffff"
HOTC = [1.0, 0.62, 0.22]
SPARKC = [1.0, 0.95, 0.75]

A = "sulfuron"
def art(part): return "%s_%s" % (A, part)


def frames(n, fn, seed=900):
    return {"fl%d" % (k + 1): fn(random.Random(seed + k), k) for k in range(n)}

# a blur whose region is the whole canvas, so a short glow is never cut into a box
WIDEBLUR = ('<defs><filter id="sulblur" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1100" height="1100">'
            '<feGaussianBlur stdDeviation="4.5"/></filter></defs>')
def blur(s, op=1): return WIDEBLUR + '<g filter="url(#sulblur)" opacity="%s">%s</g>' % (op, s)

# white-hot metal: cherry at the base, white at the tip (a gradient along the drawing's own box)
def hotgrad(gid, vertical=True):
    xy = 'x1="0" y1="1" x2="0" y2="0"' if vertical else 'x1="0" y1="0" x2="1" y2="0"'
    return ('<defs><linearGradient id="%s" %s><stop offset="0" stop-color="%s"/><stop offset=".45" stop-color="%s"/>'
            '<stop offset=".8" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient></defs>' % (gid, xy, CHERRY, ORANGE, YELLOW, WHITEHOT))


def sprite(inner, S=32):
    """a small particle sprite: the drawing centred in an exact S x S box (faint corner dots fix the crop)"""
    dots = '<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/><rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S)
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)


def path(pts): return "M " + " L ".join("%.1f %.1f" % p for p in pts)


def crack(pts, w=4):
    """a white-hot crack in blackened iron: ink, orange, yellow core"""
    d = path(pts)
    return LN(d, INK, w + 3) + LN(d, ORANGE, w) + LN(d, YELLOW, max(1.4, w - 2.4))


def rivets(pts, r=3.2, col=STEEL): return "".join(CI(x, y, r, col, 2) for x, y in pts)
def hot_rivets(pts, r=3.2): return "".join(CI(x, y, r, ORANGE, 2) + CI(x - r * 0.25, y - r * 0.25, r * 0.45, WHITEHOT, 0) for x, y in pts)


def dents(pts, col=IRON3):
    """hammer marks on blackened metal: small soft facets"""
    return "".join(EL(x, y, rx, rx * 0.6, col, 0, rot) + EL(x - rx * 0.3, y - rx * 0.25, rx * 0.4, rx * 0.22, STEEL, 0, rot)
                   for x, y, rx, rot in pts)


def spark_streaks(rnd, x, y, n, a0, a1, r0, r1, w=3.4):
    """a burst of white-hot streaks flying out of (x, y) between angles a0..a1 (degrees, 0 = right, -90 = up)"""
    s = ""
    for i in range(n):
        a = math.radians(rnd.uniform(a0, a1))
        d0 = rnd.uniform(r0, r1)
        ln = rnd.uniform(6, 13)
        x0, y0 = x + math.cos(a) * d0, y + math.sin(a) * d0
        x1, y1 = x0 + math.cos(a) * ln, y0 + math.sin(a) * ln
        d = "M %.1f %.1f L %.1f %.1f" % (x0, y0, x1, y1)
        s += LN(d, ORANGE, w + 1.6) + LN(d, WHITEHOT, w * 0.55)
        if rnd.random() < 0.5: s += CI(x1 + math.cos(a) * 4, y1 + math.sin(a) * 4, 1.6, YELLOW, 0)
    return s

# ---------------------------------------------------------------- forge helm (head space)
DOME = "M 42 102 C 32 46 66 18 128 18 C 190 18 224 46 214 102 Z"
VISOR = "M 54 90 Q 128 70 202 90 L 198 58 Q 128 40 58 58 Z"                # the raised welding visor
SLIT = "M 72 74 Q 128 58 184 74"
# a fan of freshly forged blades for a crest: base x, base y, lean (degrees), length, half-width
BLADES = [(84, 48, -60, 30, 5.5), (104, 34, -30, 37, 6.5), (128, 30, 0, 39, 7.5), (152, 34, 30, 37, 6.5), (172, 48, 60, 30, 5.5)]
HELM_CRACKS = [[(60, 60), (68, 50), (66, 42), (74, 34)], [(68, 50), (80, 50)],
               [(196, 60), (188, 50), (190, 42), (182, 34)], [(188, 50), (176, 50)],
               [(112, 46), (118, 40), (114, 32)], [(144, 46), (138, 40), (142, 32)]]

def blade_shape(L, w): return "M %.1f 6 L %.1f %.1f L 0 %.1f L %.1f %.1f L %.1f 6 Z" % (-w, -w, -(L - 2.2 * w), -L, w, -(L - 2.2 * w), w)
def blades(fn):
    return "".join('<g transform="translate(%d %d) rotate(%d)">%s</g>' % (x, y, a, fn(L, w)) for x, y, a, L, w in BLADES)

def helm():
    s = hotgrad("sulfin")
    # the blade crest behind the dome: white-hot steel cooling to cherry red at the hilt
    s += blades(lambda L, w: P(blade_shape(L, w), "url(#sulfin)", 4) + LN("M 0 2 L 0 %.1f" % -(L - 2.6 * w), WHITEHOT, 1.6, .85)
                + RC(-w - 3, 4, 2 * w + 6, 6, IRON3, 2, 3))
    # cheek guards hinged on the sides
    for sx in (-1, 1):
        g = "M %d 80 Q %d 108 %d 136 Q %d 132 %d 104 Z" % (128 + sx * 82, 128 + sx * 98, 128 + sx * 84, 128 + sx * 72, 128 + sx * 72)
        s += P(g, IRON2, 4) + LN("M %d 92 Q %d 112 %d 128" % (128 + sx * 84, 128 + sx * 90, 128 + sx * 84), IRON3, 2.5)
        s += hot_rivets([(128 + sx * 84, 120)], 2.6)
    s += P(DOME, IRON, 5)
    s += '<clipPath id="suldome"><path d="%s"/></clipPath>' % DOME
    s += '<g clip-path="url(#suldome)">%s</g>' % dents([(90, 34, 9, -20), (124, 26, 7, 0), (160, 32, 7, 10), (186, 46, 7, 25), (70, 46, 6, -40)])
    # a forged ridge down the middle
    s += LN("M 128 22 L 128 50", INK, 8) + LN("M 128 22 L 128 50", IRON3, 4.5) + LN("M 127 24 L 127 46", STEEL, 1.4)
    for c in HELM_CRACKS: s += crack(c, 3.2)
    # the welding visor, raised onto the brow, with its white-hot slit
    s += P(VISOR, IRON2, 5)
    s += LN("M 60 62 Q 128 46 196 62", IRON3, 3)
    s += LN(SLIT, INK, 11) + LN(SLIT, ORANGE, 7.5) + LN(SLIT, YELLOW, 4.5) + LN(SLIT, WHITEHOT, 1.8)
    s += rivets([(66, 82), (94, 75), (162, 75), (190, 82)], 3)
    # crossed-hammers badge on the visor
    s += P("M 114 79 L 142 79 L 142 92 Q 128 104 114 92 Z", IRON3, 3.5)
    for sx in (-1, 1):
        s += LN("M %d 99 L %d 83" % (128 - sx * 9, 128 + sx * 7), INK, 4) + RC(128 + sx * 7 - 4.5, 79, 9, 5.5, ORANGE, 1, 2)
    return HEAD(s)

def helm_mask():  # white: everything that glows white-hot (lava drifts inside)
    s = "".join(LN(path(c), WHITE, 3.4) for c in HELM_CRACKS) + LN(SLIT, WHITE, 6)
    return HEAD(s)

def helm_glow():
    s = blur(LN(SLIT, YELLOW, 12) + blades(lambda L, w: P(blade_shape(L, w), ORANGE, 5)), .9) + LN(SLIT, WHITEHOT, 2.5)
    s += blades(lambda L, w: LN("M 0 -2 L 0 %.1f" % -(L - 2.6 * w), WHITEHOT, 2.2))
    return HEAD(s)

def helm_fin():  # mask for a sheen sweeping up the blades
    return HEAD(blades(lambda L, w: P(blade_shape(L, w), WHITE, 0)))

# ---------------------------------------------------------------- anvil pauldrons (body space)
AX = -14      # the anvil sits on the outer half of the pauldron, out from behind the head
def anvil(cx, cy):
    """an anvil standing on the pauldron, its horn pointing out (left)"""
    x, top = cx + AX, cy - 46
    body = ("M %d %d L %d %d L %d %d L %d %d Q %d %d %d %d L %d %d L %d %d L %d %d Q %d %d %d %d L %d %d Q %d %d %d %d Q %d %d %d %d Z"
            % (x - 20, top, x + 18, top, x + 18, top + 10, x + 8, top + 12, x + 4, top + 18, x + 10, top + 26,
               x + 14, top + 32, x - 18, top + 32, x - 14, top + 26, x - 8, top + 18, x - 12, top + 12,
               x - 20, top + 12, x - 30, top + 13, x - 42, top + 7, x - 32, top - 1, x - 20, top))
    s = P(body, IRON3, 4.5)
    s += LN("M %d %d L %d %d" % (x - 18, top + 3.5, x + 15, top + 3.5), STEEL, 3)
    s += LN("M %d %d Q %d %d %d %d" % (x - 22, top + 4, x - 30, top + 4, x - 38, top + 6), STEEL, 1.8)
    s += LN("M %d %d L %d %d" % (x - 2, top + 16, x - 2, top + 28), IRON2, 2.5)
    return s

def INGOT(cx, cy):
    x, top = cx + AX, cy - 46
    return "M %d %d L %d %d L %d %d L %d %d Z" % (x - 14, top - 1, x - 10, top - 10, x + 8, top - 10, x + 12, top - 1)
def PCRACKS(cx, cy):
    return [[(cx - 34, cy + 4), (cx - 24, cy - 2), (cx - 20, cy + 6), (cx - 10, cy + 2)], [(cx - 24, cy - 2), (cx - 22, cy - 10)],
            [(cx + 2, cy + 8), (cx + 10, cy), (cx + 20, cy + 4)], [(cx + 10, cy), (cx + 8, cy - 8)]]
def pauldron():
    cx, cy = SH_C
    dome = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 32, cy + 10, cx + 28, cy - 16, cx - 4, cy - 16,
        cx - 40, cy - 14, cx - 42, cy + 14, cx - 4, cy + 26, cx + 32, cy + 10)
    s = anvil(cx, cy)
    s += P(INGOT(cx, cy), "url(#sulingot)", 3.5)
    s += P(dome, IRON, 5)
    s += '<clipPath id="sulpaul"><path d="%s"/></clipPath>' % dome
    s += '<g clip-path="url(#sulpaul)">%s</g>' % dents([(cx - 26, cy - 6, 7, -20), (cx + 4, cy - 8, 6, 10), (cx - 12, cy + 10, 6, 0)])
    for c in PCRACKS(cx, cy): s += crack(c, 3)
    rim = "M %d %d Q %d %d %d %d" % (cx - 40, cy + 12, cx - 6, cy + 26, cx + 30, cy + 10)
    s += LN(rim, INK, 11) + LN(rim, IRON3, 7) + LN(rim, STEEL, 2)
    s += hot_rivets([(cx - 28, cy + 16), (cx - 8, cy + 20), (cx + 12, cy + 17)], 3)
    return hotgrad("sulingot") + BOTH(s)

def pauldron_glow():
    cx, cy = SH_C
    x, top = cx + AX, cy - 46
    s = blur(P(INGOT(cx, cy), YELLOW, 7) + "".join(LN(path(c), ORANGE, 6) for c in PCRACKS(cx, cy)), .85)
    s += P("M %d %d L %d %d L %d %d L %d %d Z" % (x - 8, top - 3, x - 6, top - 8, x + 4, top - 8, x + 6, top - 3), WHITEHOT, 0)
    return BOTH(s)

def pauldron_sparks(rnd, k):
    """sparks jumping off the hot ingot as if it had just been struck"""
    cx, cy = SH_C
    return BOTH(spark_streaks(rnd, cx + AX - 1, cy - 56, 6, -175, -5, 4, 16, 3))

# ---------------------------------------------------------------- forge apron (body space)
BIB = "M 96 126 Q 128 132 160 126 L 164 196 L 92 196 Z"
PLATE = "M 104 134 Q 128 140 152 134 L 150 172 Q 128 182 106 172 Z"
EMBLEM_ANVIL = "M 114 158 L 142 158 L 136 163 L 132 163 L 134 170 L 122 170 L 124 163 L 120 163 Z"
EMBLEM_HAMMERS = ["M 112 140 L 140 166", "M 144 140 L 116 166"]
CCRACKS = [[(74, 128), (82, 140), (78, 152), (86, 166)], [(182, 128), (174, 140), (178, 152), (170, 166)],
           [(70, 182), (80, 190), (76, 200)], [(186, 182), (176, 190), (180, 200)]]
def chest():
    s = P(BODY_OUT, IRON, 5)
    s += '<clipPath id="sulbody"><path d="%s"/></clipPath>' % BODY_OUT
    s += '<g clip-path="url(#sulbody)">%s</g>' % dents([(72, 150, 7, -10), (184, 150, 7, 10), (68, 196, 6, 0), (188, 196, 6, 0), (80, 124, 5, -30), (176, 124, 5, 30)])
    for c in CCRACKS: s += crack(c, 3.4)
    # apron straps and leather bib
    for sx in (-1, 1):
        st = "M %d 128 Q %d 120 %d 116" % (128 + sx * 30, 128 + sx * 40, 128 + sx * 50)
        s += LN(st, INK, 10) + LN(st, LEATHER2, 6)
    s += P(BIB, LEATHER, 4.5)
    s += '<path d="M 100 132 Q 128 137 156 132 L 159 192 L 97 192 Z" fill="none" stroke="%s" stroke-width="1.6" stroke-dasharray="4 3"/>' % STITCH
    s += LN("M 110 176 Q 112 186 108 194", LEATHER2, 3) + LN("M 146 176 Q 144 186 148 194", LEATHER2, 3)
    # riveted iron plate with the forge emblem: crossed hammers over an anvil
    s += P(PLATE, IRON2, 4)
    s += LN("M 108 138 Q 128 143 148 138", STEEL, 2, .8)
    s += rivets([(109, 140), (147, 140), (110, 168), (146, 168)], 2.3)
    for d in EMBLEM_HAMMERS: s += LN(d, INK, 5.5) + LN(d, IRON3, 2.5)
    for x, y, a in ((112, 140, 42), (144, 140, -42)):
        s += '<g transform="translate(%d %d) rotate(%d)">%s</g>' % (x, y, a, RC(-8, -4.5, 16, 9, STEEL, 2, 2.5))
    s += P(EMBLEM_ANVIL, ORANGE, 2.5)
    # tool belt: tongs on the left, a buckle like a hot ingot
    s += RC(60, 196, 136, 14, IRON2, 4, 4) + "".join(CI(x, 203, 2.6, STEEL, 1.6) for x in (70, 86, 170, 186))
    s += LN("M 80 172 L 88 212", INK, 5.5) + LN("M 80 172 L 88 212", STEEL, 2.4) + LN("M 86 172 L 82 212", INK, 5.5) + LN("M 86 172 L 82 212", IRON3, 2.4)
    s += CI(84, 194, 2.8, STEEL, 2)
    s += RC(114, 194, 28, 18, IRON3, 4, 4) + RC(120, 199, 16, 8, ORANGE, 2, 2.5)
    return s

def chest_plate(): return P(PLATE, WHITE, 0)
def chest_cracks(): return "".join(LN(path(c), WHITE, 4) for c in CCRACKS) + P(EMBLEM_ANVIL, WHITE, 0) + RC(120, 199, 16, 8, WHITE, 2, 0)
def chest_glow():
    s = blur(P(EMBLEM_ANVIL, YELLOW, 8) + "".join(LN(d, ORANGE, 6) for d in EMBLEM_HAMMERS) + RC(118, 197, 20, 12, ORANGE, 3, 0), .9)
    return s + P(EMBLEM_ANVIL, WHITEHOT, 0, ' opacity=".7"')

# ---------------------------------------------------------------- slag-plate drapes (side drapes)
# overlapping tassets of hammered iron down each drape, their lower edges still glowing from the forge
TASSETS = [110, 132, 154, 176, 198]
def tasset(y):
    top = "M -4 %d Q 50 %d 112 %d" % (y + 14, y + 4, y - 10)
    bot = "M 112 %d Q 50 %d -4 %d" % (y + 14, y + 30, y + 36)
    edge = "M -4 %d Q 50 %d 112 %d" % (y + 36, y + 30, y + 14)
    return top + " L" + bot[1:] + " Z", edge

def both_drapes(s): return s + mirror(s, 128)

def cape():
    s = "".join(P(p, IRON, 5) for p in DRAPE_OUT) + "".join(P(p, "#5a1c10", 3) for p in DRAPE_IN)
    s += '<clipPath id="suldrape"><path d="%s"/></clipPath>' % DRAPE_OUT[0]
    plates = ""
    for i, y in enumerate(reversed(TASSETS)):       # the lower ones first: each plate overlaps the one below
        shape, edge = tasset(y)
        plates += P(shape, IRON2 if i % 2 else IRON, 3)
        plates += LN(edge, INK, 7) + LN(edge, ORANGE, 3.6) + LN(edge, YELLOW, 1.4)
        plates += LN("M 4 %d Q 50 %d 108 %d" % (y + 19, y + 10, y - 4), IRON3, 2)
        plates += dents([(46, y + 20, 5, -15)])
    s += both_drapes('<g clip-path="url(#suldrape)">%s</g>' % plates)
    # a forged iron edge with hot rivets
    for side in DRAPE_EDGE:
        out = -1 if side[0][0] < 128 else 1
        d = "M " + " L ".join("%.1f %.1f" % (x - out * 4, y) for x, y in qpts(*side, n=10))
        s += LN(d, INK, 10) + LN(d, IRON3, 6) + LN(d, STEEL, 1.6)
        s += hot_rivets([(x - out * 4, y) for x, y in qpts(*side, n=6)[1:]], 2.6)
    return s

def cape_mask():
    m = "".join(LN(tasset(y)[1], WHITE, 4) for y in TASSETS)
    return '<clipPath id="suldm"><path d="%s"/></clipPath>' % DRAPE_OUT[0] + both_drapes('<g clip-path="url(#suldm)">%s</g>' % m)

def cape_glow():
    g = blur("".join(LN(tasset(y)[1], ORANGE, 7) for y in TASSETS), .8)
    return '<clipPath id="suldg"><path d="%s"/></clipPath>' % DRAPE_OUT[0] + both_drapes('<g clip-path="url(#suldg)">%s</g>' % g)

# ---------------------------------------------------------------- Sulfuron-style hammer (right paw)
HL = 124
HX, HY = -18, -150      # the head's centre (left of the haft so the right face stays in the canvas)
CORE = (HX, HY, 13)
HEADCRACKS = [[(HX - 40, HY - 14), (HX - 32, HY - 4), (HX - 38, HY + 6), (HX - 30, HY + 16)],
              [(HX + 22, HY - 16), (HX + 28, HY - 6), (HX + 22, HY + 4), (HX + 30, HY + 14)],
              [(HX - 18, HY + 20), (HX - 8, HY + 16), (HX + 2, HY + 24)]]
def hammer():
    s = hotgrad("sulface", vertical=False)
    # haft, bound in iron with hot bands, and a spiked pommel
    s += RC(-6, -HL, 12, HL + 26, "#2a2222", 4)
    for y in (-28, -62, -96): s += RC(-9, y - 6, 18, 10, IRON3, 3, 3) + LN("M -7 %d L 7 %d" % (y - 1, y - 1), ORANGE, 2)
    s += P("M -8 24 L 8 24 L 0 44 Z", IRON3, 3.5) + CI(0, 24, 7, IRON2, 3.5) + CI(0, 24, 3, ORANGE, 0)
    x, y = HX, HY
    # flanges under the head and a spike on top
    s += P("M %d %d L %d %d L %d %d L %d %d Z" % (x - 14, y + 26, x + 14, y + 26, x + 8, y + 42, x - 8, y + 42), IRON2, 4)
    s += P("M %d %d L %d %d L %d %d Z" % (x - 9, y - 28, x, y - 50, x + 9, y - 28), IRON3, 4)
    s += P("M %d %d L %d %d L %d %d Z" % (x - 26, y - 26, x - 34, y - 42, x - 14, y - 28), IRON2, 3.5)
    s += P("M %d %d L %d %d L %d %d Z" % (x + 26, y - 26, x + 34, y - 42, x + 14, y - 28), IRON2, 3.5)
    # the head: a heavy block flaring into two striking faces
    head = ("M %d %d L %d %d L %d %d L %d %d L %d %d L %d %d L %d %d L %d %d Z"
            % (x - 38, y - 28, x + 38, y - 28, x + 44, y - 36, x + 44, y + 36, x + 38, y + 28, x - 38, y + 28, x - 44, y + 36, x - 44, y - 36))
    s += P(head, IRON, 5)
    s += '<clipPath id="sulhead"><path d="%s"/></clipPath>' % head
    s += '<g clip-path="url(#sulhead)">%s</g>' % dents([(x - 22, y - 16, 7, 0), (x + 14, y - 18, 6, 0), (x - 26, y + 14, 6, 0), (x + 16, y + 16, 6, 0)])
    # white-hot striking faces
    for sx in (-1, 1):
        f = "M %d %d L %d %d L %d %d L %d %d Z" % (x + sx * 44, y - 36, x + sx * 52, y - 30, x + sx * 52, y + 30, x + sx * 44, y + 36)
        s += P(f, "url(#sulface)" if sx > 0 else ORANGE, 4)
    for c in HEADCRACKS: s += crack(c, 3.2)
    # the molten core, held in a ring of rivets
    cx, cy, r = CORE
    s += CI(cx, cy, r + 8, IRON2, 4.5) + rivets([(cx + math.cos(math.radians(a)) * (r + 4), cy + math.sin(math.radians(a)) * (r + 4)) for a in range(0, 360, 60)], 2, STEEL)
    s += CI(cx, cy, r, ORANGE, 3.5)
    return RHAND(s)

def hammer_mask():
    cx, cy, r = CORE
    s = CI(cx, cy, r - 1, WHITE, 0) + "".join(LN(path(c), WHITE, 3.6) for c in HEADCRACKS)
    return RHAND(s)

def hammer_glow():
    cx, cy, r = CORE
    x, y = HX, HY
    s = blur(CI(cx, cy, r + 8, YELLOW, 0) + "".join(RC(x + sx * 48 - 5, y - 34, 10, 68, ORANGE, 3, 0) for sx in (-1, 1)), .95)
    s += CI(cx, cy, r * 0.5, WHITEHOT, 0)
    return RHAND(s)

def hammer_sparks(rnd, k):
    """sparks spraying off the striking faces, a new burst every frame"""
    x, y = HX, HY
    s = spark_streaks(rnd, x + 54, y + rnd.uniform(-20, 20), 6, -120, 70, 4, 16)
    s += spark_streaks(rnd, x - 54, y + rnd.uniform(-20, 20), 5, 120, 260, 4, 18)
    return RHAND(s)

# ---------------------------------------------------------------- aura: the ceaseless forge
def fountain(rnd, k):
    """white-hot sparks spraying up from the ground at both sides of the cat, and a hot glow on the ground"""
    s = blur('<ellipse cx="128" cy="214" rx="96" ry="10" fill="%s" opacity=".7"/>' % ORANGE)
    for sx in (-1, 1):
        bx = 128 + sx * rnd.uniform(70, 86)
        s += spark_streaks(rnd, bx, 212, 7, -90 + sx * 10 - 32, -90 + sx * 10 + 32, 6, 48, 3.2)
    return s

def hammer_glyph():
    """a little glowing hammer: the forge's sigil, rising from the aura"""
    g = ('<g transform="rotate(-30)">' + RC(-2.5, -4, 5, 18, WHITE, 1.5, 0) + RC(-10, -12, 20, 9, WHITE, 2, 0) + '</g>')
    return sprite('<g filter="url(#blur)" opacity=".8">%s</g>%s' % (g, g))


SPARKS = {"kind": "particles", "sprite": "a_spark", "blend": "ADD", "color": SPARKC, "color2": [1.0, 0.45, 0.1]}
EMBERS = {"kind": "particles", "sprite": "a_ember", "blend": "ADD", "color": [1.0, 0.8, 0.4], "color2": [1.0, 0.32, 0.08]}
GLINT = {"kind": "glint", "sprite": "a_spark", "blend": "ADD", "color": SPARKC}

SET = {
    "key": A, "name": "Sulfuron Forgemaster", "zone": None, "lua": "SulfuronForgemaster", "file": "sulfuron_forgemaster",
    "prof": "blacksmithing", "spec": "weaponsmith", "title": "Forgemaster",
    "about": "Sulfuron Forgemaster set: the Weaponsmith's long chase, blackened iron and white-hot sparks, crafted with Blacksmithing.",
    "preview_fur": "fur_silver",
    "pieces": [
        {"id": "set_sulfuron_head", "slot": "head", "kind": "head", "art": art("head"), "name": "Forgemaster's Searing Visor", "rarity": 5,
         "icon": "INV_Helmet_08", "word": "helm",
         "svg": helm(), "layers": {"mask": helm_mask(), "glow": helm_glow(), "fin": helm_fin()},
         "anim": [
             {"kind": "scroll", "sprite": "a_lava", "mask": K(art("head"), "mask"), "scale": 90, "vx": 14, "vy": -30, "blend": "ADD"},
             {"kind": "pulse", "key": K(art("head"), "glow"), "a": [0.3, 1.0], "speed": 3.2, "blend": "ADD", "flicker": True},
             {"kind": "scroll", "sprite": "a_shine", "mask": K(art("head"), "fin"), "scale": 40, "vx": 0, "vy": -45, "color": [1, 1, 0.9], "blend": "ADD"},
             dict(SPARKS, n=7, box=[170, 10, 342, 50], vx=[-50, 50], vy=[-100, -45], life=[0.4, 0.8], size=[8, 14], at="front"),
             dict(GLINT, n=3, spots=[[150, 8, 362, 60], [150, 80, 362, 100]], size=[16, 26], gap=[0.4, 1.2], at="front"),
         ]},
        {"id": "set_sulfuron_shoulders", "slot": "shoulder", "kind": "shoulder", "art": art("shoulders"), "name": "Anvilborne Pauldrons", "rarity": 4,
         "icon": "INV_Shoulder_29", "word": "shoulders",
         "svg": pauldron(), "layers": dict(frames(3, pauldron_sparks, 910), glow=pauldron_glow()),
         "anim": [
             {"kind": "pulse", "key": K(art("shoulders"), "glow"), "a": [0.25, 1.0], "speed": 2.8, "blend": "ADD", "flicker": True},
             {"kind": "flip", "keys": [K(art("shoulders"), "fl%d" % i) for i in range(1, 4)], "fps": 9, "blend": "ADD"},
             dict(EMBERS, n=4, box=[84, 170, 120, 195], vx=[-20, 10], vy=[-60, -30], life=[0.8, 1.4], size=[8, 12], sway=4, at="front"),
             dict(EMBERS, n=4, box=[392, 170, 428, 195], vx=[-10, 20], vy=[-60, -30], life=[0.8, 1.4], size=[8, 12], sway=4, at="front"),
         ]},
        {"id": "set_sulfuron_chest", "slot": "chest", "kind": "chest", "art": art("chest"), "name": "Ironbound Forgemaster's Apron", "rarity": 4,
         "icon": "INV_Chest_Plate16", "word": "apron",
         "svg": chest(), "layers": {"plate": chest_plate(), "cracks": chest_cracks(), "glow": chest_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_lava", "mask": K(art("chest"), "cracks"), "scale": 110, "vx": 8, "vy": -24, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_shine", "mask": K(art("chest"), "plate"), "scale": 60, "vx": 50, "vy": 10, "color": [1, 0.92, 0.8], "blend": "ADD", "alpha": 0.7},
             {"kind": "pulse", "key": K(art("chest"), "glow"), "a": [0.2, 0.95], "speed": 2.4, "blend": "ADD", "flicker": True},
             dict(GLINT, n=2, spots=[[214, 300, 298, 350]], size=[16, 24], gap=[0.5, 1.4], at="front"),
         ]},
        {"id": "set_sulfuron_cape", "slot": "back", "kind": "back", "art": art("cape"), "name": "Slagplate Drape", "rarity": 4,
         "icon": "INV_Misc_Cape_16", "word": "cape",
         "svg": cape(), "layers": {"mask": cape_mask(), "glow": cape_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_lava", "mask": K(art("cape"), "mask"), "scale": 100, "vx": 18, "vy": 30, "blend": "ADD"},
             {"kind": "pulse", "key": K(art("cape"), "glow"), "a": [0.15, 0.85], "speed": 2.0, "blend": "ADD"},
             dict(SPARKS, n=4, box=[50, 300, 96, 420], vx=[-30, 0], vy=[40, 90], life=[0.5, 0.9], size=[8, 12], at="behind"),
             dict(SPARKS, n=4, box=[416, 300, 462, 420], vx=[0, 30], vy=[40, 90], life=[0.5, 0.9], size=[8, 12], at="behind"),
         ]},
        {"id": "set_sulfuron_weapon", "slot": "main", "kind": "weapon", "art": art("weapon"), "name": "The Thousandth Strike", "rarity": 4,
         "icon": "INV_Hammer_Unique_Sulfuras", "word": "hammer",
         "svg": hammer(), "layers": dict(frames(4, hammer_sparks, 940), mask=hammer_mask(), glow=hammer_glow()),
         "anim": [
             {"kind": "scroll", "sprite": "a_lava", "mask": K(art("weapon"), "mask"), "scale": 70, "vx": 20, "vy": -36, "blend": "ADD"},
             {"kind": "pulse", "key": K(art("weapon"), "glow"), "a": [0.35, 1.0], "speed": 3.6, "blend": "ADD", "flicker": True},
             {"kind": "flip", "keys": [K(art("weapon"), "fl%d" % i) for i in range(1, 5)], "fps": 11, "blend": "ADD"},
             dict(EMBERS, n=5, box=[340, 40, 470, 120], vx=[-20, 20], vy=[-70, -35], life=[0.8, 1.4], size=[9, 15], sway=5, at="front"),
         ]},
        {"id": "set_sulfuron_aura", "slot": "effect", "kind": "effect", "art": art("aura"), "name": "Aura of the Ceaseless Forge", "rarity": 5,
         "icon": "Trade_BlackSmithing", "word": "aura", "glow": (1.0, 0.55, 0.18),
         "fx": {"layer": "back", "anim": "flicker"},
         "layers": dict(frames(4, fountain, 960), glyph=hammer_glyph()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [1.0, 0.5, 0.14], "a": [0.3, 0.7], "speed": 2.2, "blend": "ADD", "flicker": True, "at": "behind"},
             {"kind": "flip", "keys": [K(art("aura"), "fl%d" % i) for i in range(1, 5)], "fps": 10, "blend": "ADD", "at": "front"},
             dict(SPARKS, n=8, box=[100, 400, 412, 460], vx=[-70, 70], vy=[-170, -90], life=[0.6, 1.1], size=[10, 18], at="front"),
             dict(EMBERS, n=8, box=[70, 160, 442, 460], vx=[-14, 14], vy=[-80, -40], life=[1.6, 2.6], size=[10, 18], sway=9, at="behind"),
             {"kind": "particles", "sprite": "k_%s_glyph" % art("aura"), "n": 4, "box": [70, 260, 442, 440], "vx": [-8, 8], "vy": [-46, -26],
              "life": [1.8, 2.6], "size": [18, 26], "spin": [-0.6, 0.6], "color": [1.0, 0.62, 0.2], "blend": "ADD", "at": "behind"},
             dict(GLINT, n=4, spots=[[60, 120, 150, 420], [362, 120, 452, 420]], size=[18, 30], gap=[0.3, 0.9], at="front"),
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
