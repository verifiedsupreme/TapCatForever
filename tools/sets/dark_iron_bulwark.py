"""Dark Iron Bulwark (1.7.0): the Armorsmith's long-chase Blacksmithing set (title: Dark Iron Warden).
Massive charcoal dark iron plate, bevelled and riveted, with Dark Iron runes and rivets glowing
red-orange like coals: a horned greathelm with a nasal guard, spiked pauldrons, a keeled breastplate,
spiked shieldwall drapes, a studded warmaul with a crow's-beak spike, and dark smoke drifting
around the cat with embers and a slowly turning ring of runes on the ground (heavy armour and
rune-light, not Blackrock Depths' brass and furnaces). Crafted, not dropped: no zone or bosses,
the recipes are in ProfSets.lua.
  python3 tools/sets/dark_iron_bulwark.py   -> Art/v/k_darkiron_*.tga, Art/darkiron_*.tga, Sets/DarkIronBulwark.lua
  python3 tools/set_preview.py tools/sets/dark_iron_bulwark.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: charcoal dark iron with bevels, rune-light from deep red to hot orange
CHAR, CHAR2, CHAR3, BEVEL = "#323237", "#44444c", "#5d5d68", "#8e8e9c"
RUNE, RUNE2, RUNEHOT = "#d8281a", "#ff5e24", "#ffc28a"
DARKRED, LEATHER = "#5a1510", "#4a2a26"
WHITE = "#ffffff"
EMBERC = [1.0, 0.42, 0.14]

A = "darkiron"
def art(part): return "%s_%s" % (A, part)


def frames(n, fn, seed=1200):
    return {"fl%d" % (k + 1): fn(random.Random(seed + k), k) for k in range(n)}

WIDEBLUR = ('<defs><filter id="dibblur" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1100" height="1100">'
            '<feGaussianBlur stdDeviation="4"/></filter></defs>')
def blur(s, op=1): return WIDEBLUR + '<g filter="url(#dibblur)" opacity="%s">%s</g>' % (op, s)


def path(pts): return "M " + " L ".join("%.1f %.1f" % p for p in pts)

# Dark Iron runes: angular glyphs in a unit box (-1..1), drawn as strokes
GLYPHS = [
    [[(0, -1), (0, 1)], [(0, -0.4), (0.7, -1)], [(0, 0.2), (0.7, -0.4)]],                       # two branches
    [[(0, -1), (0.75, 0), (0, 1), (-0.75, 0), (0, -1)], [(0, -0.45), (0, 0.45)]],               # diamond
    [[(0, 1), (0, -1)], [(-0.7, -0.9), (0, -0.2), (0.7, -0.9)], [(-0.6, 0.6), (0.6, 0.6)]],     # crowned staff
    [[(-0.7, 1), (0, 0.3), (0.7, 1)], [(-0.7, -1), (0, -0.3), (0.7, -1)], [(0, -0.3), (0, 0.3)]],  # hourglass
    [[(-0.6, 1), (-0.6, -1), (0.6, -0.1)], [(0.6, 1), (0.6, -1), (-0.6, -0.1)]],               # crossed staves
]
def glyph_d(x, y, s, k, rot=0):
    c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return " ".join(path([(x + (px * c - py * sn) * s, y + (px * sn + py * c) * s) for px, py in stroke]) for stroke in GLYPHS[k % len(GLYPHS)])

def rune(x, y, s, k, rot=0, w=3):
    """a carved rune glowing like a coal: dark groove, red, hot core"""
    d = glyph_d(x, y, s, k, rot)
    return LN(d, INK, w + 3) + LN(d, RUNE, w + 0.6) + LN(d, RUNE2, w * 0.6) + LN(d, RUNEHOT, max(1, w * 0.25))

def rune_mask(x, y, s, k, rot=0, w=3): return LN(glyph_d(x, y, s, k, rot), WHITE, w + 1.5)
def rune_glow(x, y, s, k, rot=0, w=3): return LN(glyph_d(x, y, s, k, rot), RUNE2, w + 6)


def hot_rivets(pts, r=3.2):
    return "".join(CI(x, y, r, RUNE, 2) + CI(x - r * 0.2, y - r * 0.2, r * 0.5, RUNEHOT, 0) for x, y in pts)
def rivet_glow(pts, r=3.2): return "".join(CI(x, y, r * 2.2, RUNE2, 0) for x, y in pts)


def bevel(d, w=2.2, op=0.9): return LN(d, BEVEL, w, op)


def sprite(inner, S=32):
    dots = '<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/><rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S)
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)

# ---------------------------------------------------------------- horned greathelm (head space)
DOME = "M 40 92 C 30 44 64 14 128 14 C 192 14 226 44 216 92 Q 128 68 40 92 Z"
BAND = "M 38 92 Q 128 66 218 92 L 214 60 Q 128 38 42 60 Z"
NASAL = "M 120 72 L 136 72 L 133 96 L 128 102 L 123 96 Z"
HORN_TIP = "M 2 -8 C 10 4 18 12 28 16 C 22 6 14 -2 2 -8 Z"
HELM_RIVETS = [(52, 76), (76, 66), (102, 61), (154, 61), (180, 66), (204, 76)]
HELM_RUNE = (128, 28, 9.5, 2)
def horn():
    s = P("M 80 56 C 42 56 10 38 2 -8 C 26 8 52 12 82 10 Z", CHAR2, 5)
    for t, w in ((0.2, 5), (0.42, 4.5), (0.62, 4)):          # forged rings along the horn
        x, y = 78 - 70 * t, 33 - 40 * t * t - 4 * t
        s += LN("M %.1f %.1f L %.1f %.1f" % (x - 2, y - 13 + t * 10, x + 3, y + 13 - t * 8), INK, w + 2.5) + LN("M %.1f %.1f L %.1f %.1f" % (x - 2, y - 13 + t * 10, x + 3, y + 13 - t * 8), CHAR3, w)
    s += bevel("M 76 18 C 50 18 26 10 10 -2", 2.2, .8)
    s += P(HORN_TIP, RUNE2, 2.5) + P("M 4 -5 C 8 0 12 4 16 6 C 13 2 9 -1 4 -5 Z", RUNEHOT, 0)
    return s

def helm():
    s = horn() + mirror(horn(), 128)
    # cheek plates down both sides of the face
    for sx in (-1, 1):
        g = "M %d 78 L %d 78 Q %d 116 %d 148 L %d 140 Q %d 112 %d 94 Z" % (128 + sx * 94, 128 + sx * 72, 128 + sx * 76, 128 + sx * 84, 128 + sx * 100, 128 + sx * 100, 128 + sx * 96)
        s += P(g, CHAR2, 4.5) + bevel("M %d 92 Q %d 118 %d 140" % (128 + sx * 78, 128 + sx * 80, 128 + sx * 86))
        s += hot_rivets([(128 + sx * 90, 104), (128 + sx * 92, 128)], 2.8)
    s += P(DOME, CHAR, 5)
    # a raised keel down the middle and plate seams
    s += P("M 118 16 Q 128 10 138 16 L 136 70 L 120 70 Z", CHAR2, 3.5) + bevel("M 122 20 L 122 66", 1.8)
    s += LN("M 70 30 Q 84 50 82 72", INK, 2.5) + LN("M 186 30 Q 172 50 174 72", INK, 2.5)
    s += bevel("M 60 50 Q 66 36 80 28", 2.4, .7) + bevel("M 196 50 Q 190 36 176 28", 2.4, .5)
    x, y, sz, k = HELM_RUNE
    s += P("M 113 14 L 143 14 L 143 38 L 128 45 L 113 38 Z", CHAR3, 3.5)       # the rune plate on the keel
    s += rune(x, y, sz, k, w=2.6)
    # the heavy brow band with glowing rivets and the nasal guard
    s += P(BAND, CHAR2, 5) + bevel("M 48 66 Q 128 44 208 66", 2.6)
    s += LN("M 44 84 Q 128 60 212 84", INK, 2)
    s += hot_rivets(HELM_RIVETS, 3.2)
    s += P(NASAL, CHAR3, 4) + bevel("M 124 76 L 125 94", 1.8)
    s += hot_rivets([(128, 82)], 2.6)
    return HEAD(s)

def helm_mask():
    x, y, sz, k = HELM_RUNE
    return HEAD(rune_mask(x, y, sz, k, w=2.6) + "".join(CI(px, py, 2.6, WHITE, 0) for px, py in HELM_RIVETS))

def helm_glow():
    x, y, sz, k = HELM_RUNE
    s = blur(rune_glow(x, y, sz, k, w=3) + rivet_glow(HELM_RIVETS, 2.6) + P(HORN_TIP, RUNE2, 6) + mirror(P(HORN_TIP, RUNE2, 6), 128), .9)
    return HEAD(s + LN(glyph_d(x, y, sz, k), RUNEHOT, 1.4))

# ---------------------------------------------------------------- spiked pauldrons (body space)
def SPIKES(cx, cy):  # base x, base y, angle (0 = up, negative = out), length
    return [(cx - 30, cy - 4, -78, 30), (cx - 20, cy - 14, -46, 34), (cx - 2, cy - 18, -14, 30)]
def spike(x, y, a, ln, w=8):
    tx, ty = x + math.sin(math.radians(a)) * ln, y - math.cos(math.radians(a)) * ln
    nx, ny = math.cos(math.radians(a)) * w, math.sin(math.radians(a)) * w
    s = P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x - nx, y - ny, tx, ty, x + nx, y + ny), CHAR3, 4)
    s += LN("M %.1f %.1f L %.1f %.1f" % (x - nx * 0.4, y - ny * 0.4, tx - nx * 0.1, ty - ny * 0.1), BEVEL, 1.8, .8)
    return s, (tx, ty)

def pauldron():
    cx, cy = SH_C
    s = ""
    for x, y, a, ln in SPIKES(cx, cy): s += spike(x, y, a, ln)[0]
    # three heavy lames, the top one the biggest
    for k in (2, 1, 0):
        y = cy - 14 + k * 11
        w = 40 - k * 3
        lame = "M %d %d Q %d %d %d %d L %d %d Q %d %d %d %d Z" % (cx - w - 4, y + 14, cx - 6, y - 18, cx + w - 4, y + 4, cx + w - 6, y + 16,
                                                              cx - 6, y, cx - w - 2, y + 26)
        s += P(lame, CHAR if k == 0 else CHAR2, 5)
        s += bevel("M %d %d Q %d %d %d %d" % (cx - w + 2, y + 10, cx - 6, y - 10, cx + w - 10, y + 4), 2, .75)
    s += P("M %d %d L %d %d L %d %d L %d %d Z" % (cx - 18, cy - 12, cx + 2, cy - 15, cx + 4, cy + 3, cx - 16, cy + 6), CHAR3, 3)
    s += rune(cx - 7, cy - 5, 7, 0, rot=-8, w=2.2)
    rim = "M %d %d Q %d %d %d %d" % (cx - 42, cy + 34, cx - 8, cy + 24, cx + 28, cy + 30)
    s += LN(rim, INK, 9) + LN(rim, CHAR3, 5)
    s += hot_rivets([(cx - 34, cy + 31), (cx - 14, cy + 27), (cx + 8, cy + 27)], 2.8)
    return BOTH(s)

def pauldron_glow():
    cx, cy = SH_C
    s = rune_glow(cx - 7, cy - 5, 7, 0, -8, 2.2) + rivet_glow([(cx - 34, cy + 31), (cx - 14, cy + 27), (cx + 8, cy + 27)], 2.4)
    tips = [spike(x, y, a, ln)[1] for x, y, a, ln in SPIKES(cx, cy)]
    s += "".join(CI(tx, ty, 6, RUNE2, 0) for tx, ty in tips)
    return BOTH(blur(s, .9) + "".join(CI(tx, ty, 2.2, RUNEHOT, 0) for tx, ty in tips) + LN(glyph_d(cx - 7, cy - 5, 7, 0, -8), RUNEHOT, 1.2))

# ---------------------------------------------------------------- keeled breastplate (body space)
CHEST_RUNES = [(128, 148, 12, 2)]
CHEST_RIVETS = [(86, 172), (98, 176), (158, 176), (170, 172), (84, 188), (98, 191), (158, 191), (172, 188)]
def chest():
    s = P(BODY_OUT, CHAR, 5)
    # two great pectoral plates meeting at a raised keel
    for sx in (-1, 1):
        pec = "M 128 124 L %d 120 Q %d 140 %d 166 Q %d 172 128 170 Z" % (128 + sx * 54, 128 + sx * 60, 128 + sx * 52, 128 + sx * 24)
        s += P(pec, CHAR2, 4.5)
        s += bevel("M %d 127 L %d 124 Q %d 140 %d 158" % (128 + sx * 6, 128 + sx * 50, 128 + sx * 55, 128 + sx * 49), 3, .95 if sx < 0 else .55)
        s += hot_rivets([(128 + sx * 44, 130), (128 + sx * 50, 150)], 2.6)
    s += P("M 116 124 L 140 124 L 142 168 L 128 178 L 114 168 Z", CHAR3, 4)
    # abdomen lames
    for y in (170, 185):
        s += P("M 66 %d Q 128 %d 190 %d L 192 %d Q 128 %d 64 %d Z" % (y, y + 8, y, y + 14, y + 22, y + 14), CHAR2, 3.5)
        s += bevel("M 72 %d Q 128 %d 184 %d" % (y + 3, y + 11, y + 3), 1.6, .6)
    s += hot_rivets(CHEST_RIVETS, 2.6)
    for x, y, sz, k in CHEST_RUNES: s += rune(x, y, sz, k, w=3)
    # belt with a horned buckle
    s += RC(60, 198, 136, 14, DARKRED, 4, 4) + LN("M 64 205 L 192 205", LEATHER, 2)
    s += P("M 112 194 L 144 194 L 150 186 L 148 202 L 144 214 L 112 214 L 108 202 L 106 186 Z", CHAR3, 4)
    s += CI(128, 204, 5, RUNE, 2.5) + CI(127, 203, 2, RUNEHOT, 0)
    return s

def chest_mask(): return "".join(rune_mask(x, y, sz, k, w=3) for x, y, sz, k in CHEST_RUNES) + "".join(CI(x, y, 2.4, WHITE, 0) for x, y in CHEST_RIVETS)
def chest_glow():
    s = blur("".join(rune_glow(x, y, sz, k, w=3) for x, y, sz, k in CHEST_RUNES) + rivet_glow(CHEST_RIVETS, 2.2) + CI(128, 204, 9, RUNE2, 0), .9)
    return s + "".join(LN(glyph_d(x, y, sz, k), RUNEHOT, 1.4) for x, y, sz, k in CHEST_RUNES)

# ---------------------------------------------------------------- shieldwall drapes (side drapes)
def drape_runes():
    """runes down the middle of each drape: (x, y, size, glyph)"""
    out = []
    for side in (-1, 1):
        for i, (y, k) in enumerate(((140, 1), (166, 3), (192, 0))):
            out.append((128 + side * (70 + (y - 130) * 0.26), y, 7, k))
    return out

def cape():
    s = ""
    # iron spikes along the outer edges (behind the drapes)
    for side in DRAPE_EDGE:
        out = -1 if side[0][0] < 128 else 1
        for i, (x, y) in enumerate(qpts(*side, n=7)[1:-1]):
            ln = 16 + (i % 2) * 6
            a = out * (60 + i * 4)
            sp, _ = spike(x, y, a, ln, 6)
            s += sp
    s += "".join(P(p, CHAR, 5) for p in DRAPE_OUT) + "".join(P(p, DARKRED, 3) for p in DRAPE_IN)
    # big riveted plates
    s += '<clipPath id="dibdrape"><path d="%s"/><path d="%s"/></clipPath>' % DRAPE_OUT
    plates = ""
    for y in (126, 152, 178, 204):
        plates += LN("M 0 %d Q 64 %d 120 %d" % (y + 10, y + 2, y - 12), INK, 3) + bevel("M 0 %d Q 64 %d 120 %d" % (y + 13, y + 5, y - 9), 1.8, .6)
        plates += LN("M 136 %d Q 192 %d 256 %d" % (y - 12, y + 2, y + 10), INK, 3) + bevel("M 136 %d Q 192 %d 256 %d" % (y - 9, y + 5, y + 13), 1.8, .4)
    s += '<g clip-path="url(#dibdrape)">%s</g>' % plates
    for side in DRAPE_EDGE:
        out = -1 if side[0][0] < 128 else 1
        d = "M " + " L ".join("%.1f %.1f" % (x - out * 4, y) for x, y in qpts(*side, n=10))
        s += LN(d, INK, 10) + LN(d, CHAR3, 6) + LN(d, BEVEL, 1.6, .7)
        s += hot_rivets([(x - out * 4, y) for x, y in qpts(*side, n=8)[1:-1:2]], 2.4)
    for x, y, sz, k in drape_runes(): s += rune(x, y, sz, k, w=2.2)
    return s

def cape_glow():
    s = blur("".join(rune_glow(x, y, sz, k, w=2.2) for x, y, sz, k in drape_runes()), .85)
    return s + "".join(LN(glyph_d(x, y, sz, k), RUNEHOT, 1.2) for x, y, sz, k in drape_runes())

# ---------------------------------------------------------------- the warmaul (right paw)
HL = 120
HX, HY = -14, -146
MAUL_RUNE = (HX - 6, HY, 13, 3)
def maul():
    s = RC(-6, -HL, 12, HL + 26, "#2a2426", 4)
    for y in (-14, -44, -74): s += RC(-7.5, y - 10, 15, 16, DARKRED, 2.5, 3) + LN("M -6 %d L 6 %d M -6 %d L 6 %d" % (y - 6, y - 2, y, y + 4), LEATHER, 1.6)
    s += RC(-9, -102, 18, 10, CHAR3, 3, 3.5) + hot_rivets([(0, -97)], 2.2)
    s += P("M -9 24 L 9 24 L 6 38 L 0 44 L -6 38 Z", CHAR3, 3.5) + hot_rivets([(0, 31)], 2.4)
    x, y = HX, HY
    # the crow's-beak spike on the back (left) and the studded striking face (right)
    s += P("M %d %d C %d %d %d %d %d %d C %d %d %d %d %d %d Z" % (x - 30, y - 12, x - 50, y - 12, x - 64, y + 2, x - 70, y + 22,
                                                          x - 56, y + 10, x - 44, y + 8, x - 30, y + 10), CHAR3, 4)
    s += bevel("M %d %d C %d %d %d %d %d %d" % (x - 32, y - 8, x - 48, y - 8, x - 60, y + 4, x - 66, y + 16), 1.8, .8)
    s += P("M %d %d L %d %d L %d %d L %d %d Z" % (x - 8, y - 34, x + 8, y - 34, x + 4, y - 46, x - 4, y - 46), CHAR3, 3.5)
    block = "M %d %d L %d %d L %d %d L %d %d L %d %d L %d %d L %d %d L %d %d Z" % (
        x - 32, y - 26, x + 30, y - 30, x + 36, y - 24, x + 36, y + 24, x + 30, y + 30, x - 32, y + 26, x - 36, y + 20, x - 36, y - 20)
    s += P(block, CHAR, 5)
    s += bevel("M %d %d L %d %d" % (x - 30, y - 21, x + 28, y - 25), 2.4)
    s += LN("M %d %d L %d %d M %d %d L %d %d" % (x - 22, y - 24, x - 22, y + 24, x + 16, y - 27, x + 16, y + 27), INK, 2.5)
    s += P("M %d %d L %d %d L %d %d L %d %d Z" % (x + 36, y - 24, x + 44, y - 20, x + 44, y + 20, x + 36, y + 24), CHAR2, 4)
    for sy in (-12, 10):                       # pyramid studs on the face
        s += P("M %d %d L %d %d L %d %d Z" % (x + 44, y + sy - 8, x + 54, y + sy + 1, x + 44, y + sy + 10), CHAR3, 3)
    s += P("M %d %d L %d %d L %d %d L %d %d Z" % (x - 16, y - 22, x + 10, y - 23, x + 10, y + 22, x - 16, y + 21), CHAR3, 3)
    s += hot_rivets([(x - 29, y - 18), (x - 29, y + 18), (x + 24, y - 21), (x + 24, y + 21)], 2.6)
    s += rune(MAUL_RUNE[0] + 3, MAUL_RUNE[1], MAUL_RUNE[2], MAUL_RUNE[3], w=2.6)
    return RHAND(s)

def maul_mask():
    x, y, sz, k = MAUL_RUNE
    return RHAND(rune_mask(x + 3, y, sz, k, w=2.6))

def maul_glow():
    x, y, sz, k = MAUL_RUNE
    pts = [(HX - 29, HY - 18), (HX - 29, HY + 18), (HX + 24, HY - 21), (HX + 24, HY + 21)]
    return RHAND(blur(rune_glow(x + 3, y, sz, k, w=3) + rivet_glow(pts, 2.4), .95) + LN(glyph_d(x + 3, y, sz, k), RUNEHOT, 1.4))

# ---------------------------------------------------------------- aura: smoke, embers and a ring of runes
def rune_ring(rnd, k):
    """a ring of runes on the ground around the cat, turning one quarter step per frame (only the near half
    is drawn: it sits in front of the paws)"""
    s = ""
    cx, cy, rx, ry = 128, 212, 112, 16
    ring = "M %d %d A %d %d 0 0 0 %d %d" % (cx - rx, cy, rx, ry, cx + rx, cy)
    s += blur(LN(ring, RUNE, 6), .7) + LN(ring, RUNE2, 2.2, .9)
    n = 12
    for i in range(n):
        a = math.radians(i * 360.0 / n + k * 360.0 / n / 4)
        x, y = cx + math.cos(a) * (rx - 4), cy + math.sin(a) * ry
        if math.sin(a) < 0.05: continue             # the far half is hidden behind the cat
        sc = 0.75 + 0.25 * math.sin(a)
        s += blur(LN(glyph_d(x, y + 1, 5.5 * sc, i), RUNE2, 6), .8) + LN(glyph_d(x, y + 1, 5.5 * sc, i), RUNEHOT, 2)
    return s

def smoke_puff():
    """a cartoon puff of dark smoke (drawn light, tinted dark by the particles)"""
    blobs = [(-6, 3, 7.5), (3, -4, 8.5), (8, 5, 6.5), (-1, 8, 6.5), (-9, -4, 5)]
    ink = "".join('<circle cx="%d" cy="%d" r="%.1f" fill="%s"/>' % (x, y, r + 2.2, INK) for x, y, r in blobs)
    body = "".join('<circle cx="%d" cy="%d" r="%.1f" fill="#c9c6cc"/>' % (x, y, r) for x, y, r in blobs)
    shade = "".join('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#9c98a2"/>' % (x + 1.6, y + 2, r * 0.7) for x, y, r in blobs[:4])
    hi = '<circle cx="1" cy="-6" r="3.2" fill="#f2f0f4"/><circle cx="-8" cy="0" r="2.2" fill="#f2f0f4"/>'
    return sprite('<g opacity=".92">%s%s%s%s</g>' % (ink, body, shade, hi))

PUFF = "k_%s_puff" % art("aura")
SMOKE = {"kind": "particles", "sprite": PUFF, "color": [0.5, 0.47, 0.5], "color2": [0.3, 0.28, 0.31], "spin": [-0.4, 0.4]}
EMBERS = {"kind": "particles", "sprite": "a_ember", "blend": "ADD", "color": [1.0, 0.55, 0.22], "color2": [0.9, 0.16, 0.06]}
GLINT = {"kind": "glint", "sprite": "a_spark", "blend": "ADD", "color": [1.0, 0.5, 0.25]}

SET = {
    "key": A, "name": "Dark Iron Bulwark", "zone": None, "lua": "DarkIronBulwark", "file": "dark_iron_bulwark",
    "prof": "blacksmithing", "spec": "armorsmith", "title": "Dark Iron Warden",
    "about": "Dark Iron Bulwark set: the Armorsmith's long chase, massive dark iron plate with glowing runes and drifting smoke, crafted with Blacksmithing.",
    "preview_fur": "fur_cream",
    "pieces": [
        {"id": "set_darkiron_head", "slot": "head", "kind": "head", "art": art("head"), "name": "Horned Greathelm of the Warden", "rarity": 5,
         "icon": "INV_Helmet_10", "word": "helm",
         "svg": helm(), "layers": {"mask": helm_mask(), "glow": helm_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_firetile", "mask": K(art("head"), "mask"), "scale": 60, "vx": 10, "vy": -30, "blend": "ADD"},
             {"kind": "pulse", "key": K(art("head"), "glow"), "a": [0.25, 1.0], "speed": 1.8, "blend": "ADD"},
             dict(SMOKE, n=4, box=[44, 0, 70, 20], vx=[-16, 0], vy=[-34, -18], life=[1.6, 2.4], size=[28, 38], grow=1.8, sway=5, alpha=0.7, at="front"),
             dict(SMOKE, n=4, box=[442, 0, 468, 20], vx=[0, 16], vy=[-34, -18], life=[1.6, 2.4], size=[28, 38], grow=1.8, sway=5, alpha=0.7, at="front"),
             dict(GLINT, n=2, spots=[[50, 0, 150, 60], [362, 0, 462, 60]], size=[12, 20], gap=[0.6, 1.6], at="front"),
         ]},
        {"id": "set_darkiron_shoulders", "slot": "shoulder", "kind": "shoulder", "art": art("shoulders"), "name": "Spiked Bulwark Pauldrons", "rarity": 4,
         "icon": "INV_Shoulder_10", "word": "shoulders",
         "svg": pauldron(), "layers": {"glow": pauldron_glow()},
         "anim": [
             {"kind": "pulse", "key": K(art("shoulders"), "glow"), "a": [0.2, 1.0], "speed": 1.6, "blend": "ADD"},
             dict(SMOKE, n=3, box=[40, 180, 80, 210], vx=[-14, 0], vy=[-30, -14], life=[1.6, 2.4], size=[20, 28], grow=1.6, sway=4, alpha=0.6, at="front"),
             dict(SMOKE, n=3, box=[432, 180, 472, 210], vx=[0, 14], vy=[-30, -14], life=[1.6, 2.4], size=[20, 28], grow=1.6, sway=4, alpha=0.6, at="front"),
             dict(GLINT, n=2, spots=[[0, 190, 120, 280], [392, 190, 512, 280]], size=[12, 18], gap=[0.5, 1.4], at="front"),
         ]},
        {"id": "set_darkiron_chest", "slot": "chest", "kind": "chest", "art": art("chest"), "name": "Runeriveted Dark Iron Breastplate", "rarity": 4,
         "icon": "INV_Chest_Plate08", "word": "chest",
         "svg": chest(), "layers": {"mask": chest_mask(), "glow": chest_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_firetile", "mask": K(art("chest"), "mask"), "scale": 70, "vx": 6, "vy": -26, "blend": "ADD"},
             {"kind": "pulse", "key": K(art("chest"), "glow"), "a": [0.2, 1.0], "speed": 1.7, "blend": "ADD"},
             dict(GLINT, n=2, spots=[[220, 270, 292, 340]], size=[14, 22], gap=[0.6, 1.6], at="front"),
         ]},
        {"id": "set_darkiron_cape", "slot": "back", "kind": "back", "art": art("cape"), "name": "Shieldwall Drape", "rarity": 4,
         "icon": "INV_Misc_Cape_20", "word": "cape",
         "svg": cape(), "layers": {"glow": cape_glow()},
         "anim": [
             {"kind": "pulse", "key": K(art("cape"), "glow"), "a": [0.15, 1.0], "speed": 1.5, "blend": "ADD"},
             dict(SMOKE, n=4, box=[40, 300, 100, 420], vx=[-14, 0], vy=[-26, -12], life=[2.0, 3.0], size=[30, 40], grow=1.5, sway=6, alpha=0.6, at="behind"),
             dict(SMOKE, n=4, box=[412, 300, 472, 420], vx=[0, 14], vy=[-26, -12], life=[2.0, 3.0], size=[30, 40], grow=1.5, sway=6, alpha=0.6, at="behind"),
             dict(EMBERS, n=4, box=[40, 300, 472, 430], vx=[-10, 10], vy=[-40, -20], life=[1.4, 2.2], size=[8, 12], sway=6, at="behind"),
         ]},
        {"id": "set_darkiron_weapon", "slot": "main", "kind": "weapon", "art": art("weapon"), "name": "Wardenforged Warmaul", "rarity": 4,
         "icon": "INV_Hammer_10", "word": "warmaul",
         "svg": maul(), "layers": {"mask": maul_mask(), "glow": maul_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_firetile", "mask": K(art("weapon"), "mask"), "scale": 50, "vx": 8, "vy": -30, "blend": "ADD"},
             {"kind": "pulse", "key": K(art("weapon"), "glow"), "a": [0.3, 1.0], "speed": 2.0, "blend": "ADD"},
             dict(SMOKE, n=4, box=[330, 50, 450, 110], vx=[-8, 8], vy=[-34, -18], life=[1.6, 2.4], size=[22, 32], grow=1.7, sway=5, alpha=0.6, at="front"),
             dict(EMBERS, n=4, box=[330, 50, 450, 120], vx=[-14, 14], vy=[-50, -24], life=[0.9, 1.5], size=[8, 12], sway=4, at="front"),
         ]},
        {"id": "set_darkiron_aura", "slot": "effect", "kind": "effect", "art": art("aura"), "name": "Aura of the Smoldering Bulwark", "rarity": 5,
         "icon": "Ability_Warrior_ShieldWall", "word": "aura", "glow": (0.85, 0.25, 0.1),
         "fx": {"layer": "back", "anim": "flicker"},
         "layers": dict(frames(4, rune_ring), puff=smoke_puff()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [0.9, 0.22, 0.08], "a": [0.18, 0.45], "speed": 1.4, "blend": "ADD", "at": "behind"},
             {"kind": "flip", "keys": [K(art("aura"), "fl%d" % i) for i in range(1, 5)], "fps": 6, "blend": "ADD", "at": "front"},
             dict(SMOKE, n=8, box=[30, 140, 482, 360], vx=[-14, 14], vy=[-34, -16], life=[2.8, 3.8], size=[60, 84], grow=1.5, sway=10, alpha=0.85, at="behind"),
             dict(SMOKE, n=6, box=[40, 390, 472, 460], vx=[-20, 20], vy=[-24, -10], life=[2.4, 3.2], size=[48, 66], grow=1.5, sway=8, alpha=0.5, at="front"),
             dict(EMBERS, n=8, box=[70, 200, 442, 450], vx=[-12, 12], vy=[-55, -25], life=[1.6, 2.6], size=[8, 14], sway=8, at="front"),
             dict(GLINT, n=3, spots=[[50, 120, 140, 420], [372, 120, 462, 420]], size=[14, 22], gap=[0.4, 1.2], at="front"),
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
