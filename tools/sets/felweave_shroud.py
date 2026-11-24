"""Felweave Shroud (1.7.0): the Shadoweave tailor's long-chase set. Black and deep purple shadoweave
cloth trimmed in burning fel green: a horned warlock cowl with fel fire on its horns, spaulders with a
watching demon eye, a robe stitched with glowing fel runes, side drapes whose hems burn green, a staff
crowned with a green skull in fel flames, and an aura of fel wisps rising from a summoning circle.
Crafted by Tailoring (Shadoweave), no zone or bosses; the full set gives the title Felweaver.
  python3 tools/sets/felweave_shroud.py            -> Art/v/k_felweave_*.tga, Art/felweave_*.tga, Sets/FelweaveShroud.lua
  python3 tools/set_preview.py tools/sets/felweave_shroud.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: shadoweave black and deep purple, burning fel green
SHD, SHD2, SHD3 = "#1d1528", "#2e2042", "#47305f"
PUR, PUR2 = "#5b2f86", "#7d48b0"
FELD, FEL, FEL2, FELC = "#2f8f14", "#74e82a", "#c4ff6a", "#f4ffd8"
FELG = "#4cff10"                      # the blurred glows
BONEF, BONEF2 = "#c9f59a", "#8fcf5c"  # the fel-soaked skull
FEL3 = [0.5, 1.0, 0.18]
FELLIGHT = [0.8, 1.0, 0.55]

WIDEBLUR = ('<defs><filter id="wblur" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1100" height="1100">'
            '<feGaussianBlur stdDeviation="%s"/></filter></defs>')
def blur(s, sd=5): return (WIDEBLUR % sd) + '<g filter="url(#wblur)">%s</g>' % s

def sprite(inner, S=32):
    dots = '<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/><rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S)
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)

def hc(x, y): return [round(2 * (128 + (x - 128) * 0.8)), round(2 * (16 + (y - 28) * 0.8 + 16))]
def bc(x, y): return [round(2 * x), round(2 * (y + 16))]
def rc(x, y):
    a = math.radians(14)
    return bc(166 + x * math.cos(a) - y * math.sin(a), 200 + x * math.sin(a) + y * math.cos(a))
def box(p, q): return [min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1])]

def frames(n, fn, seed=900):
    return {"fl%d" % (k + 1): fn(random.Random(seed + k), k) for k in range(n)}

def flame(x, y, h, w, lean=0.0, ink=3.5, cols=(FELD, FEL, FEL2, FELC), top=None):
    """a sticker flame standing on (x, y): tip h above, base half-width w, tip pushed sideways by lean"""
    if top is not None: h = min(h, y - top)
    out = ""
    for k, (s, col) in enumerate(zip((1.0, 0.72, 0.46, 0.24), cols)):
        hh, ww, tx = h * s, w * s, x + lean * s
        by = y - h * (1 - s) * 0.18
        d = ("M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z"
             % (x - ww, by, x - ww * 1.15, by - hh * 0.45, tx - ww * 0.45, by - hh * 0.72, tx, by - hh,
                tx + ww * 0.55, by - hh * 0.66, x + ww * 1.15, by - hh * 0.42, x + ww, by, x, by + ww * 0.95, x - ww, by))
        out += P(d, col, ink if k == 0 else 0)
    return out

# fel runes: angular glyphs, each a list of strokes in a -1..1 box
GLYPHS = [
    [[(0, -1), (0, 1)], [(-0.7, -0.4), (0, 0.15), (0.7, -0.4)]],
    [[(-0.6, -1), (0.6, 0), (-0.6, 1)], [(0.6, -1), (0.6, 1)]],
    [[(0, -1), (0.7, 0), (0, 1), (-0.7, 0), (0, -1)], [(0, -0.35), (0, 0.35)]],
    [[(-0.7, -1), (0, -0.2), (0.7, -1)], [(0, -0.2), (0, 1)], [(-0.5, 0.55), (0.5, 0.55)]],
    [[(-0.6, 1), (-0.6, -1), (0.6, -0.4), (-0.6, 0.2)]],
    [[(-0.7, -0.7), (0.7, -0.7)], [(0, -0.7), (-0.5, 1)], [(0, -0.7), (0.5, 1)]],
]
def rune_d(x, y, s, k):
    return " ".join("M " + " L ".join("%.1f %.1f" % (x + px * s, y + py * s) for px, py in stroke) for stroke in GLYPHS[k % len(GLYPHS)])

def rune(x, y, s, k, col=FEL, w=2.4):
    d = rune_d(x, y, s, k)
    return LN(d, INK, w + 2.5) + LN(d, col, w)

def skull(cx, cy, r, eyes=INK, ink=4, fill=BONEF, shade=BONEF2):
    """a cartoon skull facing us"""
    d = ("M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f L %.1f %.1f L %.1f %.1f Z"
         % (cx - r * 0.62, cy + r * 0.78, cx - r * 1.12, cy + r * 0.3, cx - r * 1.05, cy - r, cx, cy - r,
            cx + r * 1.05, cy - r, cx + r * 1.12, cy + r * 0.3, cx + r * 0.62, cy + r * 0.78, cx + r * 0.5, cy + r * 1.15, cx - r * 0.5, cy + r * 1.15))
    s = P(d, fill, ink)
    s += LN("M %.1f %.1f Q %.1f %.1f %.1f %.1f" % (cx - r * 0.62, cy - r * 0.5, cx - r * 0.2, cy - r * 0.85, cx + r * 0.3, cy - r * 0.78), "#ffffff", max(1.5, r * 0.12), .6)
    for sx in (-1, 1):
        s += P("M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" % (
            cx + sx * r * 0.12, cy + r * 0.02, cx + sx * r * 0.45, cy - r * 0.3, cx + sx * r * 0.78, cy + r * 0.1,
            cx + sx * r * 0.45, cy + r * 0.5, cx + sx * r * 0.12, cy + r * 0.02), eyes, 0)
    s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (cx - r * 0.12, cy + r * 0.66, cx, cy + r * 0.44, cx + r * 0.12, cy + r * 0.66), INK, 0)
    for k in range(4):
        x = cx - r * 0.44 + k * r * 0.29
        s += LN("M %.1f %.1f L %.1f %.1f" % (x + r * 0.14, cy + r * 0.84, x + r * 0.14, cy + r * 1.1), shade, max(1.2, r * 0.07))
    return s

def skull_eyes(cx, cy, r):
    s = ""
    for sx in (-1, 1):
        ex, ey = cx + sx * r * 0.45, cy + r * 0.12
        s += blur(EL(ex, ey, r * 0.5, r * 0.45, FELG, 0), 3) + EL(ex, ey, r * 0.16, r * 0.16, FELC, 0)
    return s

def ember():
    """a fel ember: a hot dot with a soft green halo (tinted in game)"""
    return sprite(blur(CI(0, 0, 8, "#ffffff", 0), 3) + CI(0, 0, 3.5, "#ffffff", 0))

# ---------------------------------------------------------------- horned cowl (head space)
HOOD = "M 34 128 Q 22 36 110 14 L 128 2 L 146 14 Q 234 36 222 128 Q 228 176 196 182 L 60 182 Q 28 176 34 128 Z"
HOLE = "M 58 122 Q 60 62 128 58 Q 196 62 198 122 Q 196 170 128 172 Q 60 170 58 122 Z"
HORN = "M 64 66 C 30 68 4 50 0 10 C 14 28 36 36 88 36 Z"
HTIP = (0, 12)
GEM_H = (128, 38)

def horn(side):
    s = P(HORN, SHD3, 5)
    for x, y in ((12, 32), (22, 42), (34, 50), (48, 54), (62, 56)):
        s += LN("M %d %d Q %d %d %d %d" % (x - 2, y + 7, x + 2, y, x + 6, y - 7), SHD, 3)
    s += LN("M 6 22 C 14 40 32 50 64 50", PUR2, 2.5, .8)
    s += P("M 0 10 C 2 18 6 24 12 28 L 16 22 C 8 20 4 16 0 10 Z", FEL, 2.5)   # the fel-burnt tip
    return s if side < 0 else mirror(s, 128)

def cowl():
    s = horn(-1) + horn(1)
    s += '<path d="%s %s" fill="%s" fill-rule="evenodd" stroke="%s" stroke-width="5" stroke-linejoin="round"/>' % (HOOD, HOLE, SHD2, INK)
    # folds and a deep purple sheen on the cloth
    for d in ("M 44 120 Q 40 70 84 36", "M 212 120 Q 216 70 172 36", "M 128 6 L 128 46"):
        s += LN(d, SHD3, 4)
    s += LN("M 48 100 Q 52 58 100 32", PUR2, 2.5, .7)
    s += P("M 40 150 Q 128 196 216 150 Q 220 170 196 182 L 60 182 Q 36 170 40 150 Z", SHD, 0)
    # fel runes stitched along the cheeks of the cowl
    for k, (x, y) in enumerate(((44, 142), (212, 142), (46, 108), (210, 108))):
        s += rune(x, y, 6, k + 1, FEL, 2)
    # the burning trim around the face
    s += LN(HOLE, INK, 10) + LN(HOLE, FELD, 7) + LN(HOLE, FEL2, 2.5)
    # fel crystal at the brow in a horned setting
    gx, gy = GEM_H
    s += P("M %d %d L %d %d L %d %d L %d %d Z" % (gx - 22, gy + 14, gx - 30, gy - 4, gx - 10, gy + 6, gx, gy + 18), SHD3, 3.5)
    s += mirror(P("M %d %d L %d %d L %d %d L %d %d Z" % (gx - 22, gy + 14, gx - 30, gy - 4, gx - 10, gy + 6, gx, gy + 18), SHD3, 3.5), 128)
    s += P("M %d %d L %d %d L %d %d L %d %d Z" % (gx, gy - 16, gx + 11, gy, gx, gy + 16, gx - 11, gy), FEL, 4)
    s += P("M %d %d L %d %d L %d %d Z" % (gx, gy - 12, gx + 6, gy, gx, gy + 2), FEL2, 0)
    s += LN(rune_d(gx, gy + 2, 4.5, 0), FELD, 1.8)
    return HEAD(s)

def cowl_glow():
    gx, gy = GEM_H
    s = blur(LN(HOLE, FELG, 9), 5)
    s += blur(P("M %d %d L %d %d L %d %d L %d %d Z" % (gx, gy - 20, gx + 15, gy, gx, gy + 20, gx - 15, gy), FELG, 0), 4)
    s += "".join(blur(LN(rune_d(x, y, 6, k + 1), FELG, 4), 2) for k, (x, y) in enumerate(((44, 142), (212, 142), (46, 108), (210, 108))))
    s += "".join(LN(rune_d(x, y, 6, k + 1), FELC, 1.2) for k, (x, y) in enumerate(((44, 142), (212, 142), (46, 108), (210, 108))))
    s += LN(HOLE, FELC, 1.5)
    return HEAD(s)

def cowl_mask():
    return HEAD('<path d="%s %s" fill="#ffffff" fill-rule="evenodd"/>' % (HOOD, HOLE))

def cowl_flames(rnd, k):
    s = ""
    for sx in (-1, 1):
        x = 128 + sx * (128 - HTIP[0])
        s += flame(x, HTIP[1] + 10, 30 * (0.8 + rnd.random() * 0.4), 9, lean=sx * (3 + rnd.random() * 8) + (rnd.random() - 0.5) * 6, top=-11)
    gx, gy = GEM_H
    s += flame(gx, gy - 12, 22 * (0.8 + rnd.random() * 0.4), 6, lean=(rnd.random() - 0.5) * 8, ink=3)
    return HEAD(s)

# ---------------------------------------------------------------- spaulders (body space, both sides)
def sh_dome():
    cx, cy = SH_C
    return "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 30, cy + 8, cx + 26, cy - 22, cx - 4, cy - 22,
        cx - 34, cy - 20, cx - 36, cy + 12, cx - 4, cy + 22, cx + 30, cy + 8)

SPIKES = ((-26, -12, -52, 24), (-8, -18, -24, 30), (12, -18, 6, 24))   # x, y off the centre, angle, length
def spike_tip(dx, dy, a, ln):
    cx, cy = SH_C
    x, y = cx + dx, cy + dy
    return x + math.sin(math.radians(a)) * ln, y - math.cos(math.radians(a)) * ln

def pauldron():
    cx, cy = SH_C
    s = ""
    # tattered shadoweave strips under the dome, singed green at the tips
    for i, (x, ln) in enumerate(((cx - 32, 30), (cx - 18, 36), (cx - 2, 32), (cx + 14, 28), (cx + 26, 20))):
        d = "M %d %d L %d %d L %d %d L %d %d L %d %d Z" % (x - 8, cy + 4, x - 7, cy + ln, x - 2, cy + ln - 6, x + 3, cy + ln + 4, x + 8, cy + 4)
        s += P(d, PUR if i % 2 == 0 else SHD3, 3.5)
        s += P("M %d %d L %d %d L %d %d L %d %d Z" % (x - 7, cy + ln - 5, x - 7, cy + ln, x - 2, cy + ln - 6, x - 2, cy + ln - 11), FEL, 0)
        s += P("M %d %d L %d %d L %d %d Z" % (x + 3, cy + ln - 6, x + 3, cy + ln + 4, x + 7, cy + ln - 4), FEL, 0)
    # black horn spikes
    for dx, dy, a, ln in SPIKES:
        x, y = cx + dx, cy + dy
        tx, ty = spike_tip(dx, dy, a, ln)
        s += P("M %.1f %.1f Q %.1f %.1f %.1f %.1f L %.1f %.1f Z" % (x - 8, y + 6, x - 6 + (tx - x) * 0.3, y + (ty - y) * 0.6, tx, ty, x + 8, y + 6), SHD3, 4)
        s += LN("M %.1f %.1f L %.1f %.1f" % (x + (tx - x) * 0.55, y + (ty - y) * 0.55, tx, ty), FEL, 2.5)
    s += P(sh_dome(), SHD2, 5)
    s += LN("M %d %d Q %d %d %d %d" % (cx - 26, cy - 10, cx - 8, cy - 18, cx + 12, cy - 14), SHD3, 5)
    # green-burning rim
    rim = "M %d %d Q %d %d %d %d" % (cx - 36, cy + 10, cx - 4, cy + 24, cx + 28, cy + 8)
    s += LN(rim, INK, 9) + LN(rim, FELD, 6) + LN(rim, FEL2, 2)
    # the demon eye
    ex, ey = cx - 4, cy - 2
    s += P("M %d %d Q %d %d %d %d Q %d %d %d %d Z" % (ex - 17, ey, ex, ey - 15, ex + 17, ey, ex, ey + 15, ex - 17, ey), SHD, 4)
    s += CI(ex, ey, 8, FEL, 2.5) + EL(ex, ey, 2.4, 7, INK, 0) + CI(ex - 3, ey - 3, 1.8, FELC, 0)
    return BOTH(s)

def pauldron_glow():
    cx, cy = SH_C
    ex, ey = cx - 4, cy - 2
    rim = "M %d %d Q %d %d %d %d" % (cx - 36, cy + 10, cx - 4, cy + 24, cx + 28, cy + 8)
    return BOTH(blur(CI(ex, ey, 14, FELG, 0), 5) + blur(LN(rim, FELG, 7), 3) + CI(ex, ey, 5, FEL2, 0) + EL(ex, ey, 1.6, 6, INK, 0))

def pauldron_mask():
    return BOTH(P(sh_dome(), "#ffffff", 0))

def pauldron_flames(rnd, k):
    s = ""
    for dx, dy, a, ln in SPIKES:
        tx, ty = spike_tip(dx, dy, a, ln)
        s += flame(tx, ty + 7, 16 * (0.8 + rnd.random() * 0.45), 5, lean=(rnd.random() - 0.5) * 8 + a * 0.12, ink=3)
    return BOTH(s)

# ---------------------------------------------------------------- robe (body space)
PANEL = "M 112 124 Q 128 128 144 124 L 152 212 L 104 212 Z"
RUNES = [(128, 152, 7, 3), (128, 172, 7, 0), (128, 190, 6, 2)]   # x, y, size, glyph (down the panel)
SIDERUNES = [(88, 150, 5, 1), (168, 150, 5, 4), (84, 176, 5, 5), (172, 176, 5, 1)]
def chest():
    s = P(BODY_OUT, SHD, 5)
    for sx in (-1, 1):
        side = "M 76 116 Q 66 160 70 214 L 94 214 Q 88 160 100 120 Z"
        s += P(side, SHD2, 0) if sx < 0 else mirror(P(side, SHD2, 0), 128)
    s += LN("M 82 130 Q 76 170 80 210", SHD3, 3) + LN("M 174 130 Q 180 170 176 210", SHD3, 3)
    s += P(PANEL, PUR, 4)
    s += LN("M 116 130 L 110 210", PUR2, 2, .6)
    for sx in (-1, 1):   # green-burning trim down the panel edges
        d = "M %d 126 L %d 212" % (128 + sx * 16, 128 + sx * 24)
        s += LN(d, INK, 8) + LN(d, FELD, 5) + LN(d, FEL2, 1.6)
    for x, y, r, g in RUNES: s += rune(x, y, r, g, FEL, 2.6)
    for x, y, r, g in SIDERUNES: s += rune(x, y, r, g, FELD, 2)
    # a high spiked collar
    col = "M 92 118 L 100 132 L 110 126 L 118 140 L 128 132 L 138 140 L 146 126 L 156 132 L 164 118 Q 128 128 92 118 Z"
    s += P(col, SHD3, 4) + LN("M 100 130 L 110 124 L 118 138 L 128 130 L 138 138 L 146 124 L 156 130", FEL, 1.8)
    # belt with a fel crystal buckle
    s += RC(60, 198, 136, 14, SHD2, 4, 4) + LN("M 64 205 L 192 205", PUR2, 1.6, .7)
    s += P("M 128 194 L 138 205 L 128 216 L 118 205 Z", FEL, 3.5) + P("M 128 198 L 133 205 L 128 207 Z", FEL2, 0)
    return s

def chest_runes():   # white mask of the runes and trim (green light runs up inside it)
    s = "".join(LN(rune_d(x, y, r, g), "#ffffff", 4.5) for x, y, r, g in RUNES + SIDERUNES)
    s += "".join(LN("M %d 126 L %d 212" % (128 + sx * 16, 128 + sx * 24), "#ffffff", 5) for sx in (-1, 1))
    return s

def chest_glow():
    s = blur("".join(LN(rune_d(x, y, r, g), FELG, 6) for x, y, r, g in RUNES + SIDERUNES), 3)
    s += blur(P("M 128 190 L 142 205 L 128 220 L 114 205 Z", FELG, 0), 4)
    s += "".join(LN(rune_d(x, y, r, g), FELC, 1.2) for x, y, r, g in RUNES)
    return s

# ---------------------------------------------------------------- shroud (side drapes)
def cape():
    s = "".join(P(p, SHD2, 5) for p in DRAPE_OUT) + "".join(P(p, PUR, 3) for p in DRAPE_IN)
    for sx in (-1, 1):
        one = LN("M 70 130 Q 50 160 48 194", SHD3, 3) + LN("M 64 146 Q 54 170 56 196", PUR2, 2, .6)
        for k, (x, y) in enumerate(((60, 150), (52, 172), (50, 192))):
            one += rune(x, y, 5.5, k + 2, FEL, 2)
        s += one if sx < 0 else mirror(one, 128)
    # charred, green-burning outer hem
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        d = "M " + " L ".join("%.1f %.1f" % (x + (4 if x < 128 else -4), y) for x, y in pts)
        s += LN(d, INK, 9) + LN(d, FELD, 6) + LN(d, FEL2, 2)
    # clasps: little horned skulls at the shoulders
    for sx in (-1, 1):
        s += skull(128 + sx * 52, 114, 7, eyes=SHD, ink=2.5)
    return s

def cape_glow():
    s = ""
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        d = "M " + " L ".join("%.1f %.1f" % (x + (4 if x < 128 else -4), y) for x, y in pts)
        s += blur(LN(d, FELG, 9), 4)
    for sx in (-1, 1):
        one = "".join(blur(LN(rune_d(x, y, 5.5, k + 2), FELG, 4), 2) for k, (x, y) in enumerate(((60, 150), (52, 172), (50, 192))))
        s += one if sx < 0 else mirror(one, 128)
        s += skull_eyes(128 + sx * 52, 114, 7)
    return s

def cape_flames(rnd, k):
    s = ""
    for side in DRAPE_EDGE:
        for i, (x, y) in enumerate(qpts(*side, n=4)[1:]):
            out = -1 if x < 128 else 1
            s += flame(x + out * 3, y + 4, (11 + i * 3) * (0.8 + rnd.random() * 0.45), 4.5, lean=out * (6 + rnd.random() * 6), ink=2.5)
    return s

# ---------------------------------------------------------------- skull staff (right paw)
SL = 150
SK = (0, -SL - 24, 21)
def staff():
    s = RC(-5.5, -SL, 11, SL + 32, SHD3, 4, 4)
    for y in range(-SL + 10, 20, 16):   # twisted grain
        s += LN("M -5 %d Q 0 %d 5 %d" % (y, y - 7, y - 12), SHD, 2.5)
    for y in (-SL + 30, -80, -20):
        s += RC(-8, y, 16, 8, SHD2, 3, 3) + LN("M -6 %d L 6 %d" % (y + 4, y + 4), FEL, 2)
    s += P("M -9 26 L 0 44 L 9 26 Z", SHD3, 3.5) + P("M -4 30 L 0 38 L 4 30 Z", FEL, 0)
    # iron claws cradling the skull
    x, y, r = SK
    for sx in (-1, 1):
        d = "M %d %d C %d %d %d %d %d %d" % (sx * 4, -SL + 2, sx * 26, -SL - 4, sx * 30, y + 4, sx * 18, y - 10)
        s += LN(d, INK, 9) + LN(d, SHD3, 5)
    # curling horns on the skull
    for sx in (-1, 1):
        h = P("M %d %d C %d %d %d %d %d %d C %d %d %d %d %d %d Z" % (
            x + sx * 12, y - 10, x + sx * 30, y - 16, x + sx * 34, y - 34, x + sx * 24, y - 44,
            x + sx * 26, y - 32, x + sx * 22, y - 22, x + sx * 8, y - 16), SHD3, 3.5)
        s += h
    s += skull(x, y, r, eyes=SHD, ink=4)
    return RHAND(s)

def staff_glow():
    x, y, r = SK
    return RHAND(blur(CI(x, y, r + 3, FELG, 0), 6) + skull_eyes(x, y, r))

def staff_mask():
    x, y, r = SK
    return RHAND(CI(x, y - 2, r * 0.95, "#ffffff", 0))

def staff_flames(rnd, k):
    x, y, r = SK
    s = flame(x, y - r + 6, 44 * (0.8 + rnd.random() * 0.35), 13, lean=(rnd.random() - 0.5) * 16, top=-8 - 210)
    for sx in (-1, 1):
        s += flame(x + sx * 24, y - 40, 14 * (0.8 + rnd.random() * 0.5), 4.5, lean=sx * 3 + (rnd.random() - 0.5) * 6, ink=2.5)
    return RHAND(s)

# ---------------------------------------------------------------- aura: a summoning circle, fel wisps and green flames
CIRC = (128, 214, 108, 22)
def circle_ring(width, col, op=1.0):
    x, y, rx, ry = CIRC
    return '<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="none" stroke="%s" stroke-width="%s" opacity="%s"/>' % (x, y, rx, ry, col, width, op)

def summon_circle():
    x, y, rx, ry = CIRC
    s = blur(circle_ring(12, FELG), 6)
    s += circle_ring(3, FEL2) + '<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="none" stroke="%s" stroke-width="1.6" opacity=".85"/>' % (x, y, rx - 14, ry - 5, FEL2)
    for i in range(14):   # runes along the band between the two rings
        a = math.radians(i * (360 / 14.0))
        px, py = x + (rx - 7) * math.cos(a), y + (ry - 2.5) * math.sin(a)
        s += '<g transform="translate(%.1f %.1f) scale(1 0.55)">%s</g>' % (px, py, LN(rune_d(0, 0, 3.5, i), FEL2, 1.6))
    return s

def ground_flames(rnd, k):
    """green flames dancing along the back and sides of the circle"""
    x, y, rx, ry = CIRC
    s = ""
    for i in range(9):
        a = math.radians(180 + i * 22.5)
        px, py = x + rx * math.cos(a), y + ry * math.sin(a) + 2
        h = (18 + 10 * abs(math.cos(a))) * (0.75 + rnd.random() * 0.5)
        s += flame(px, py, h, 6.5, lean=(rnd.random() - 0.5) * 10, ink=2.5)
    return s

def wisp():
    """a fel wisp: a soft teardrop of green smoke with a curling tail (tinted in game)"""
    d = "M 0 -12 C 8 -8 9 4 2 10 C 6 4 2 -2 -3 2 C -8 6 -6 -8 0 -12 Z"
    return sprite(blur(P(d, "#ffffff", 0), 2.5) + P("M 0 -8 C 4 -4 5 2 1 6 C 2 2 -1 -1 -3 1 C -5 -2 -3 -6 0 -8 Z", "#ffffff", 0))

FX_ART = "felweave_aura"
SET = {
    "key": "felweave", "name": "Felweave Shroud", "zone": None, "lua": "FelweaveShroud", "file": "felweave_shroud",
    "prof": "tailoring", "spec": "shadoweave", "title": "Felweaver",
    "about": "Felweave Shroud: the Shadoweave tailor's long-chase set, shadoweave cloth burning with fel fire.",
    "preview_fur": "fur_silver",
    "pieces": [
        {"id": "set_felweave_head", "slot": "head", "kind": "head", "art": "felweave_head", "name": "Horned Cowl of the Felweaver", "rarity": 5,
         "icon": "INV_Helmet_70", "word": "hood",
         "svg": cowl(), "layers": dict(frames(4, cowl_flames), glow=cowl_glow(), mask=cowl_mask(), ember=ember()),
         "anim": [
             {"kind": "flip", "keys": [K("felweave_head", "fl%d" % i) for i in range(1, 5)], "fps": 10},
             {"kind": "pulse", "key": K("felweave_head", "glow"), "a": [0.25, 0.85], "speed": 3.0, "blend": "ADD", "flicker": True},
             {"kind": "scroll", "sprite": "a_nebula", "mask": K("felweave_head", "mask"), "scale": 160, "vx": 8, "vy": -14, "color": [0.7, 0.35, 1.0], "blend": "ADD", "alpha": 0.3},
             {"kind": "particles", "sprite": "k_felweave_head_ember", "n": 7, "box": box(hc(4, -8), hc(252, 30)), "vx": [-10, 10], "vy": [-70, -40], "life": [0.9, 1.5],
              "size": [8, 14], "color": FELLIGHT, "color2": [0.3, 0.9, 0.1], "blend": "ADD", "sway": 6, "at": "front"},
         ]},
        {"id": "set_felweave_shoulders", "slot": "shoulder", "kind": "shoulder", "art": "felweave_shoulders", "name": "Spaulders of the Watching Eye", "rarity": 4,
         "icon": "INV_Shoulder_25", "word": "shoulders",
         "svg": pauldron(), "layers": dict(frames(3, pauldron_flames), glow=pauldron_glow(), mask=pauldron_mask()),
         "anim": [
             {"kind": "flip", "keys": [K("felweave_shoulders", "fl%d" % i) for i in range(1, 4)], "fps": 9},
             {"kind": "pulse", "key": K("felweave_shoulders", "glow"), "a": [0.25, 1.0], "speed": 2.4, "blend": "ADD", "flicker": True},
             {"kind": "scroll", "sprite": "a_nebula", "mask": K("felweave_shoulders", "mask"), "scale": 120, "vx": 10, "vy": -12, "color": [0.7, 0.35, 1.0], "blend": "ADD", "alpha": 0.45},
             {"kind": "particles", "sprite": "a_ember", "n": 5, "box": [70, 200, 450, 260], "vx": [-8, 8], "vy": [-60, -36], "life": [0.8, 1.3],
              "size": [8, 12], "color": FELLIGHT, "color2": [0.3, 0.9, 0.1], "blend": "ADD", "sway": 5, "at": "front"},
         ]},
        {"id": "set_felweave_chest", "slot": "chest", "kind": "chest", "art": "felweave_chest", "name": "Rune-Stitched Felweave Robe", "rarity": 4,
         "icon": "INV_Chest_Cloth_49", "word": "robe",
         "svg": chest(), "layers": {"runes": chest_runes(), "glow": chest_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K("felweave_chest", "runes"), "scale": 70, "vx": 0, "vy": -40, "color": FELLIGHT, "blend": "ADD"},
             {"kind": "pulse", "key": K("felweave_chest", "glow"), "a": [0.2, 1.0], "speed": 2.6, "blend": "ADD", "flicker": True},
             {"kind": "particles", "sprite": "a_ember", "n": 4, "box": [200, 300, 312, 420], "vx": [-8, 8], "vy": [-50, -30], "life": [0.8, 1.3],
              "size": [7, 11], "color": FELLIGHT, "color2": [0.3, 0.9, 0.1], "blend": "ADD", "sway": 4, "at": "front"},
             {"kind": "glint", "n": 2, "spots": [box(bc(110, 140), bc(146, 200))], "life": 0.6, "gap": [0.5, 1.3], "size": [12, 18], "color": [0.7, 1.0, 0.4], "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_felweave_cape", "slot": "back", "kind": "back", "art": "felweave_cape", "name": "Shroud of Smoldering Fel", "rarity": 4,
         "icon": "INV_Misc_Cape_16", "word": "cape",
         "svg": cape(), "layers": dict(frames(3, cape_flames), glow=cape_glow()),
         "anim": [
             {"kind": "flip", "keys": [K("felweave_cape", "fl%d" % i) for i in range(1, 4)], "fps": 9},
             {"kind": "pulse", "key": K("felweave_cape", "glow"), "a": [0.2, 0.9], "speed": 2.2, "blend": "ADD", "flicker": True},
             {"kind": "particles", "sprite": "a_wisp", "n": 3, "box": [40, 260, 100, 420], "vx": [-14, 0], "vy": [-44, -24], "life": [1.4, 2.2],
              "size": [20, 30], "color": FEL3, "blend": "ADD", "sway": 6, "at": "behind"},
             {"kind": "particles", "sprite": "a_wisp", "n": 3, "box": [412, 260, 472, 420], "vx": [0, 14], "vy": [-44, -24], "life": [1.4, 2.2],
              "size": [20, 30], "color": FEL3, "blend": "ADD", "sway": 6, "at": "behind"},
         ]},
        {"id": "set_felweave_weapon", "slot": "main", "kind": "weapon", "art": "felweave_weapon", "name": "Staff of the Green Skull", "rarity": 4,
         "icon": "INV_Staff_19", "word": "staff",
         "svg": staff(), "layers": dict(frames(4, staff_flames), glow=staff_glow(), mask=staff_mask()),
         "anim": [
             {"kind": "flip", "keys": [K("felweave_weapon", "fl%d" % i) for i in range(1, 5)], "fps": 10},
             {"kind": "pulse", "key": K("felweave_weapon", "glow"), "a": [0.15, 0.75], "speed": 3.2, "blend": "ADD", "flicker": True},
             {"kind": "scroll", "sprite": "a_swirl", "mask": K("felweave_weapon", "mask"), "scale": 60, "vx": 14, "vy": -24, "color": FEL3, "blend": "ADD", "alpha": 0.6},
             {"kind": "particles", "sprite": "a_ember", "n": 6, "box": box(rc(-26, -SL - 80), rc(26, -SL - 40)), "vx": [-10, 10], "vy": [-70, -40], "life": [0.8, 1.3],
              "size": [8, 13], "color": FELLIGHT, "color2": [0.3, 0.9, 0.1], "blend": "ADD", "sway": 5, "at": "front"},
         ]},
        {"id": "set_felweave_aura", "slot": "effect", "kind": "effect", "art": FX_ART, "name": "Felweaver's Summoning Circle", "rarity": 5,
         "icon": "Spell_Shadow_SummonFelHunter", "word": "aura", "glow": (0.4, 1.0, 0.15),
         "fx": {"layer": "back", "anim": "flicker"},
         "layers": dict(frames(4, ground_flames), circle=summon_circle(), wisp=wisp()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [0.35, 1.0, 0.15], "a": [0.1, 0.3], "speed": 2.4, "blend": "ADD", "flicker": True, "at": "behind"},
             {"kind": "pulse", "key": K(FX_ART, "circle"), "a": [0.45, 1.0], "speed": 1.6, "blend": "ADD", "at": "behind"},
             {"kind": "flip", "keys": [K(FX_ART, "fl%d" % i) for i in range(1, 5)], "fps": 9, "at": "behind"},
             {"kind": "particles", "sprite": "k_felweave_aura_wisp", "n": 8, "box": [50, 300, 462, 470], "vx": [-8, 8], "vy": [-70, -40], "life": [1.6, 2.6],
              "size": [18, 30], "color": FEL3, "blend": "ADD", "sway": 12, "at": "front"},
             {"kind": "particles", "sprite": "t_felfire", "n": 4, "box": [50, 330, 462, 450], "vx": [-6, 6], "vy": [-60, -36], "life": [1.0, 1.6],
              "size": [16, 24], "alpha": 0.95, "sway": 4, "at": "behind"},
             {"kind": "particles", "sprite": "a_ember", "n": 8, "box": [60, 380, 452, 470], "vx": [-10, 10], "vy": [-90, -50], "life": [0.9, 1.5],
              "size": [7, 12], "color": FELLIGHT, "color2": [0.3, 0.9, 0.1], "blend": "ADD", "at": "front"},
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
