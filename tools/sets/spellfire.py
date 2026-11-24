"""Spellfire set (1.7.0): a Tailoring long chase (Spellfire specialization). Arcane fire: deep violet
cloth stitched with gold, magenta-pink and orange spellfire and glowing arcane runes. A tall bent
wizard hat burning at the tip, a runed mantle, a robe with burning seams, a star-lined cloak, a
spellfire staff cradling an orb of pink fire and a turning rune circle under the cat. Crafted over
months; the whole set gives the title Spellfire Savant.
  python3 tools/sets/spellfire.py            -> Art/v/k_spellfire_*.tga, Art/spellfire_*.tga, Sets/Spellfire.lua
  python3 tools/set_preview.py tools/sets/spellfire.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: deep violet cloth, gold thread, spellfire (magenta, pink, orange, cream)
CLOTH, CLOTH2, CLOTH3, CLOTHD = "#3e1f66", "#58308c", "#7b4bb8", "#2a1448"
GOLD, GOLD2, GOLDL = "#f1b843", "#c4842a", "#ffe08a"
MAG, PINK, PINKL, ORANGE, CREAM = "#d42a8e", "#ff5cb4", "#ffb0dc", "#ffa040", "#fff0c8"
LINING = "#a3307e"
FIRE = (MAG, PINK, ORANGE, CREAM)
PINKC = [1.0, 0.45, 0.85]
WHITE = "#ffffff"


def frames(n, fn, seed=700):
    return {"fl%d" % (k + 1): fn(random.Random(seed + k), k) for k in range(n)}


# a blur whose region is the whole canvas, so the glow of a small shape is never cut off into a box
WIDEBLUR = ('<defs><filter id="wblur" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1100" height="1100">'
            '<feGaussianBlur stdDeviation="%s"/></filter></defs>')
def blur(s, sd=5): return (WIDEBLUR % sd) + '<g filter="url(#wblur)">%s</g>' % s


def sprite(inner, S=32):
    """a small particle sprite: the drawing centred in an exact S x S box (faint corner dots fix the crop)"""
    dots = ('<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/>'
            '<rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S))
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)


def flame(x, y, h, w, lean=0.0, ink=3.5, cols=FIRE, top=None):
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


def rune_d(x, y, s, kind):
    """the path of one arcane rune glyph, about 2s tall, centred on (x, y)"""
    k = kind % 6
    if k == 0:   # diamond pierced by a line
        return ("M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z M %.1f %.1f L %.1f %.1f"
                % (x, y - s * 0.75, x + s * 0.55, y, x, y + s * 0.75, x - s * 0.55, y, x, y - s * 1.1, x, y + s * 1.1))
    if k == 1:   # arrow with a crossbar
        return ("M %.1f %.1f L %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f"
                % (x - s * 0.6, y + s, x, y - s, x + s * 0.6, y + s, x - s * 0.35, y + s * 0.15, x + s * 0.35, y + s * 0.15, x, y - s, x, y + s))
    if k == 2:   # hook and bar
        return ("M %.1f %.1f L %.1f %.1f Q %.1f %.1f %.1f %.1f M %.1f %.1f L %.1f %.1f"
                % (x - s * 0.4, y - s, x - s * 0.4, y + s * 0.4, x - s * 0.4, y + s, x + s * 0.5, y + s * 0.6, x - s * 0.4, y - s * 0.2, x + s * 0.45, y - s * 0.55))
    if k == 3:   # eye: an arc over a dot line
        return ("M %.1f %.1f Q %.1f %.1f %.1f %.1f M %.1f %.1f Q %.1f %.1f %.1f %.1f M %.1f %.1f L %.1f %.1f"
                % (x - s * 0.7, y, x, y - s * 1.1, x + s * 0.7, y, x - s * 0.7, y, x, y + s * 1.1, x + s * 0.7, y, x, y - s * 0.25, x, y + s * 0.25))
    if k == 4:   # zigzag
        return ("M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f"
                % (x - s * 0.5, y - s, x + s * 0.5, y - s * 0.35, x - s * 0.5, y + s * 0.35, x + s * 0.5, y + s))
    # triangle with a tail
    return ("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z M %.1f %.1f L %.1f %.1f"
            % (x, y - s, x + s * 0.65, y + s * 0.2, x - s * 0.65, y + s * 0.2, x, y + s * 0.2, x, y + s))


def rune(x, y, s, kind, col=PINKL, w=2.2):
    return LN(rune_d(x, y, s, kind), col, w)


def star(x, y, r, n=4, inner=0.35, rot=0):
    pts = []
    for i in range(n * 2):
        a = math.radians(rot + i * 180.0 / n)
        rr = r if i % 2 == 0 else r * inner
        pts.append("%.1f %.1f" % (x + math.sin(a) * rr, y - math.cos(a) * rr))
    return "M " + " L ".join(pts) + " Z"


def seam(pts, w=5):
    """a burning seam: a dark slit with magenta fire and a hot pink core"""
    d = "M " + " L ".join("%.1f %.1f" % p for p in pts)
    return LN(d, INK, w + 3) + LN(d, MAG, w) + LN(d, PINKL, max(1.5, w - 3))


# ---------------------------------------------------------------- hat (head space)
CONE = "M 68 80 C 76 50 94 16 122 -2 C 150 -14 200 -2 228 40 C 206 28 180 24 166 32 C 172 50 180 64 188 80 Z"
BRIM = "M 20 88 C 28 70 90 64 128 64 C 166 64 228 70 236 88 C 228 104 170 102 128 102 C 86 102 28 104 20 88 Z"
BAND = "M 66 82 Q 128 71 191 82 L 186 62 Q 128 51 71 62 Z"
TIP = (228, 40)
GEMH = (128, 70)
HAT_RUNES = [(100, 34, 8, 0), (128, 16, 7, 3), (154, 38, 8, 5)]


def hat():
    s = P(BRIM, CLOTH2, 5) + P("M 30 92 C 60 100 100 100 128 100 C 156 100 196 100 226 92 C 222 99 170 101 128 101 C 86 101 34 99 30 92 Z", CLOTHD, 0)
    s += LN("M 30 90 C 60 98 100 98 128 98 C 156 98 196 98 226 90", GOLD, 4)          # gold edge of the brim
    s += P(CONE, CLOTH, 6.5)
    s += P("M 80 76 C 86 50 100 26 124 8 C 114 30 108 52 106 76 Z", CLOTH2, 0)          # a lighter fold
    s += LN("M 168 30 C 186 24 206 26 222 36", CLOTH3, 3)
    # spellfire embroidery licking up from the band
    for x, h in ((90, 22), (128, 30), (166, 22)):
        s += P("M %d 64 C %d %d %d %d %d %d C %d %d %d %d %d 64 Z" % (x - 9, x - 10, 64 - h * 0.5, x - 2, 64 - h * 0.7, x + 2, 64 - h,
               x + 4, 64 - h * 0.6, x + 11, 64 - h * 0.45, x + 9), MAG, 0)
        s += P("M %d 64 C %d %d %d %d %d %d C %d %d %d 64 Z" % (x - 4, x - 5, 64 - h * 0.35, x, 64 - h * 0.5, x + 1, 64 - h * 0.62,
               x + 3, 64 - h * 0.4, x + 5), ORANGE, 0)
    for x, y, r, k in HAT_RUNES: s += rune(x, y, r, k, PINK, 3)
    s += P("M 150 4 A 11 11 0 1 0 162 20 A 8 8 0 1 1 150 4 Z", GOLDL, 2.5)            # a crescent moon
    s += P(star(108, 6, 5), GOLDL, 2) + P(star(188, 22, 4.5), GOLDL, 1.8) + P(star(88, 52, 4), GOLDL, 1.5)
    s += P(BAND, GOLD, 4.5)
    s += LN("M 70 66 Q 128 55 187 66", GOLDL, 2.5)
    for i, x in enumerate((80, 100, 156, 176)):
        y = 70 - 7 * (1 - ((x - 128) / 64.0) ** 2)
        s += rune(x, y + 2, 5, i + 1, CLOTH2, 2.6)
    # the spellfire gem in a gold claw setting
    gx, gy = GEMH
    s += P("M %d %d L %d %d L %d %d Z" % (gx - 16, gy + 8, gx, gy - 20, gx + 16, gy + 8), GOLD2, 3.5)
    s += CI(gx, gy, 11, MAG, 4) + CI(gx, gy + 1, 7, PINK, 0) + CI(gx, gy + 2, 3.5, ORANGE, 0) + CI(gx - 4, gy - 4, 2.5, WHITE, 0)
    # the gold bead at the tip
    s += CI(TIP[0], TIP[1], 6, GOLD, 3.5)
    return HEAD(mirror(s, 128))


def hat_mask():   # the cone above the band: stars drift inside it
    return HEAD(mirror('<defs><clipPath id="upper"><rect x="0" y="-60" width="256" height="122"/></clipPath></defs>'
                       '<g clip-path="url(#upper)">%s</g>' % P(CONE, WHITE, 0), 128))


def hat_glow():   # runes, embroidery and the gem burning brighter
    s = "".join(rune(x, y, r, k, PINK, 6) for x, y, r, k in HAT_RUNES)
    g = blur(s + CI(GEMH[0], GEMH[1], 15, PINK, 0) + CI(TIP[0], TIP[1], 9, ORANGE, 0), 4)
    g += "".join(rune(x, y, r, k, CREAM, 1.6) for x, y, r, k in HAT_RUNES) + CI(GEMH[0], GEMH[1] + 1, 4, CREAM, 0)
    return HEAD(mirror(g, 128))


def hat_flames(rnd, k):
    s = flame(TIP[0], TIP[1] - 4, 46 * (0.85 + rnd.random() * 0.3), 11, lean=(rnd.random() - 0.6) * 14, top=-12)
    s += flame(GEMH[0], GEMH[1] - 18, 20 * (0.8 + rnd.random() * 0.4), 6, lean=(rnd.random() - 0.5) * 8, ink=3)
    return HEAD(mirror(s, 128))


def H2C(x, y):
    """head space -> the 512 canvas"""
    return (128 + 0.8 * (x - 128)) * 2, (16 + 0.8 * (y - 28) + 16) * 2


# ---------------------------------------------------------------- mantle (body space, both shoulders)
def mantle_spikes():
    cx, cy = SH_C
    return [(cx - 26, cy - 12, -52, 24), (cx - 6, cy - 18, -16, 30), (cx + 14, cy - 16, 18, 22)]


def mantle():
    cx, cy = SH_C
    s = ""
    # gold flame-shaped spires fanning out behind
    for x, y, a, ln in mantle_spikes():
        tx, ty = x + math.sin(math.radians(a)) * ln, y - math.cos(math.radians(a)) * ln
        nx, ny = math.cos(math.radians(a)), math.sin(math.radians(a))
        d = "M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" % (x - 8 * nx, y - 8 * ny + 4, x - 4 * nx + (tx - x) * 0.5 - 6 * nx, y + (ty - y) * 0.5,
                                                                             tx, ty, x + (tx - x) * 0.5 + 8 * nx, y + (ty - y) * 0.5 + 6 * ny, x + 8 * nx, y + 8 * ny + 4)
        s += P(d, GOLD, 3.5)
        s += LN("M %.1f %.1f L %.1f %.1f" % (x, y + 2, x + (tx - x) * 0.75, y + (ty - y) * 0.75), MAG, 3)
    # hanging cloth tabs under the dome
    for i, x in enumerate((cx - 30, cx - 12, cx + 6, cx + 22)):
        y0 = cy + 10 + (6 if 0 < i < 3 else 2)
        s += P("M %d %d L %d %d L %d %d L %d %d Z" % (x - 9, y0 - 6, x - 8, y0 + 12, x, y0 + 18, x + 8, y0 + 12) + " M %d %d L %d %d" % (x + 8, y0 + 12, x + 9, y0 - 6),
               LINING, 3)
        s += LN("M %d %d L %d %d L %d %d" % (x - 6, y0 + 10, x, y0 + 14, x + 6, y0 + 10), GOLD, 2.5)
    dome = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 32, cy + 8, cx + 28, cy - 24, cx - 4, cy - 24,
        cx - 38, cy - 22, cx - 40, cy + 12, cx - 4, cy + 24, cx + 32, cy + 8)
    s += P(dome, CLOTH, 5)
    s += P("M %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx - 34, cy + 4, cx - 34, cy - 18, cx - 6, cy - 20, cx - 22, cy - 10, cx - 34, cy + 4), CLOTH2, 0)
    rim = "M %d %d Q %d %d %d %d" % (cx - 38, cy + 8, cx - 6, cy + 22, cx + 30, cy + 6)
    s += LN(rim, INK, 10) + LN(rim, GOLD, 6) + LN(rim, GOLDL, 2)
    # the rune medallion
    mx, my = cx - 4, cy - 4
    s += CI(mx, my, 12, GOLD, 4) + CI(mx, my, 8, MAG, 0) + P(star(mx, my, 7, 4, 0.32, 45), PINKL, 0) + CI(mx, my, 2.2, CREAM, 0)
    for x, y, k in ((cx - 28, cy - 6, 2), (cx + 18, cy - 8, 4)): s += rune(x, y, 5, k, PINK, 2.6)
    return BOTH(s)


def mantle_glow():
    cx, cy = SH_C
    mx, my = cx - 4, cy - 4
    s = blur(CI(mx, my, 13, PINK, 0) + rune(cx - 28, cy - 6, 5, 2, PINK, 6) + rune(cx + 18, cy - 8, 5, 4, PINK, 6), 4)
    s += P(star(mx, my, 8, 4, 0.32, 45), CREAM, 0) + rune(cx - 28, cy - 6, 5, 2, CREAM, 1.5) + rune(cx + 18, cy - 8, 5, 4, CREAM, 1.5)
    return BOTH(s)


def mantle_flames(rnd, k):
    s = ""
    for x, y, a, ln in mantle_spikes():
        tx, ty = x + math.sin(math.radians(a)) * ln, y - math.cos(math.radians(a)) * ln
        s += flame(tx, ty + 7, (17 if ln < 30 else 22) * (0.8 + rnd.random() * 0.45), 5.5, lean=(rnd.random() - 0.5) * 8 + a * 0.14, ink=3)
    return BOTH(s)


# ---------------------------------------------------------------- robe (body space)
PANEL = "M 106 124 L 150 124 L 160 214 L 96 214 Z"
SEAMS = [[(106, 128), (102, 160), (98, 196)], [(150, 128), (154, 160), (158, 196)],
         [(82, 132), (88, 150), (80, 170), (86, 192)], [(174, 132), (168, 150), (176, 170), (170, 192)]]
SIG = (128, 166)


def robe():
    s = P(BODY_OUT, CLOTH, 5)
    s += P("M 76 116 Q 64 160 68 214 L 84 214 Q 80 160 92 120 Z", CLOTHD, 0) + mirror(P("M 76 116 Q 64 160 68 214 L 84 214 Q 80 160 92 120 Z", CLOTHD, 0), 128)
    s += P(PANEL, CLOTH2, 0)
    for sm in SEAMS: s += seam(sm, 5)
    # the high gold collar
    col = "M 84 116 L 128 146 L 172 116"
    s += LN(col, INK, 13) + LN(col, GOLD, 8) + LN(col, GOLDL, 2.5)
    # the spellfire sigil
    x, y = SIG
    s += CI(x, y, 19, GOLD, 4.5) + CI(x, y, 14, CLOTHD, 0)
    s += P(star(x, y, 13, 8, 0.45, 0), MAG, 0) + P(star(x, y, 10, 4, 0.3, 0), PINKL, 0) + CI(x, y, 3.5, CREAM, 0)
    for i in range(4):
        a = math.radians(45 + i * 90)
        s += CI(x + math.sin(a) * 19, y - math.cos(a) * 19, 3, PINK, 2)
    # sash with a gem
    s += RC(60, 198, 136, 14, GOLD2, 4, 4) + LN("M 64 202 L 192 202", GOLDL, 2)
    for xx, k in ((76, 0), (98, 3), (158, 1), (180, 5)): s += rune(xx, 205, 4.5, k, CLOTH, 2.4)
    s += P("M 128 194 L 140 205 L 128 216 L 116 205 Z", MAG, 3.5) + P("M 128 199 L 134 205 L 128 211 L 122 205 Z", PINKL, 0)
    return s


def robe_seams():
    return "".join(LN("M " + " L ".join("%.1f %.1f" % p for p in sm), WHITE, 6) for sm in SEAMS)


def robe_glow():
    x, y = SIG
    s = blur(CI(x, y, 17, PINK, 0) + "".join(LN("M " + " L ".join("%.1f %.1f" % p for p in sm), MAG, 8) for sm in SEAMS), 4)
    s += P(star(x, y, 10, 4, 0.3, 0), CREAM, 0) + P("M 128 199 L 134 205 L 128 211 L 122 205 Z", CREAM, 0)
    return s


# ---------------------------------------------------------------- cloak (side drapes)
def cloak():
    s = "".join(P(p, CLOTH, 5) for p in DRAPE_OUT) + "".join(P(p, LINING, 3) for p in DRAPE_IN)
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        d = "M " + " L ".join("%.1f %.1f" % (x + (5 if x < 128 else -5), y) for x, y in pts)
        s += LN(d, INK, 10) + LN(d, GOLD, 6) + LN(d, GOLDL, 2)
        for i, (x, y) in enumerate(qpts(*side, n=5)[1:5]):
            inn = 13 if x < 128 else -13
            s += rune(x + inn, y + 2, 5, i + (0 if x < 128 else 3), GOLDL, 2.4)
    for x, y in ((48, 168), (208, 168)): s += P(star(x, y, 5), GOLDL, 1.5)
    # gold clasps where the cloak hangs from the shoulders
    for sx in (-1, 1):
        x = 128 + sx * 56
        s += CI(x, 118, 9, GOLD, 4) + CI(x, 118, 5, MAG, 0) + CI(x - 2, 116, 1.8, WHITE, 0)
    return s


def cloak_mask():
    return "".join(P(p, WHITE, 0) for p in DRAPE_IN)


def cloak_flames(rnd, k):
    s = ""
    for side in DRAPE_EDGE:
        for i, (x, y) in enumerate(qpts(*side, n=5)[1:]):
            out = -1 if x < 128 else 1
            h = (16, 26, 19, 30, 22)[i]
            s += flame(x + out * 2, y + 4, h * (0.8 + rnd.random() * 0.4), 5.5 + h * 0.08, lean=out * (9 + rnd.random() * 9), ink=3)
    return s


# ---------------------------------------------------------------- staff (right paw)
SL = 140
ORB = (0, -174, 19)


def staff():
    s = RC(-5.5, -SL, 11, SL + 34, CLOTHD, 4, 4)
    # gold ribbon spiralling up the shaft
    d = "M -5 26 " + " ".join("Q %d %d %d %d" % ((8 if i % 2 == 0 else -8), 18 - i * 18, (-5 if i % 2 else 5), 10 - i * 18) for i in range(9))
    s += LN(d, INK, 6) + LN(d, GOLD, 3)
    for y in (-30, -96): s += RC(-8, y - 5, 16, 10, GOLD, 3, 3)
    s += RC(-9, -SL - 4, 18, 12, GOLD, 3, 3.5)
    s += P("M 0 30 L 9 40 L 0 52 L -9 40 Z", GOLD, 3.5) + CI(0, 41, 3.5, PINK, 0)
    ox, oy, r = ORB
    # two gold prongs cradling the orb
    for sx in (-1, 1):
        d = "M %d %d C %d %d %d %d %d %d C %d %d %d %d %d %d Z" % (sx * 4, -SL - 2, sx * 30, -SL - 10, sx * 32, oy - 8, sx * 14, oy - r - 10,
                                                                 sx * 22, oy - 6, sx * 18, -SL - 18, 0, -SL - 10)
        s += P(d, GOLD, 4)
        s += CI(sx * 14, oy - r - 10, 3.5, PINK, 2.5)
    s += CI(ox, oy, r, MAG, 4.5) + CI(ox, oy + 2, r * 0.7, PINK, 0) + CI(ox, oy + 4, r * 0.38, ORANGE, 0)
    s += CI(ox - 6, oy - 6, 3.5, WHITE, 0)
    return RHAND(s)


def staff_mask():
    ox, oy, r = ORB
    return RHAND(CI(ox, oy, r - 2, WHITE, 0))


def staff_glow():
    ox, oy, r = ORB
    return RHAND(blur(CI(ox, oy, r + 8, PINK, 0), 6) + CI(ox, oy + 3, r * 0.4, CREAM, 0))


def staff_flames(rnd, k):
    ox, oy, r = ORB
    s = ""
    for dx, h, w in ((-11, 24, 6), (11, 24, 6), (0, 40, 10)):
        s += flame(ox + dx, oy - r * 0.4, h * (0.8 + rnd.random() * 0.4), w, lean=(rnd.random() - 0.5) * 12 + dx * 0.4, ink=3, top=-218)
    return RHAND(s)


def hand2c(x, y):
    a = math.radians(14)
    bx, by = 166 + x * math.cos(a) - y * math.sin(a), 200 + x * math.sin(a) + y * math.cos(a)
    return bx * 2, (by + 16) * 2


# ---------------------------------------------------------------- aura: the turning rune circle
RING = (128, 218, 112, 20)


def ring_frame(rnd, k):
    """the magic circle on the ground, turned a little further each frame (45-degree symmetry, so it loops)"""
    cx, cy, rx, ry = RING
    rot = k * 45.0 / 4
    def pt(a, f): return cx + math.sin(math.radians(a)) * rx * f, cy - math.cos(math.radians(a)) * ry * f
    lines = ""
    lines += '<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="none" stroke="%s" stroke-width="%s"/>' % (cx, cy, rx, ry, "{c}", "{w}")
    lines += '<ellipse cx="%d" cy="%d" rx="%.1f" ry="%.1f" fill="none" stroke="%s" stroke-width="%s"/>' % (cx, cy, rx * 0.8, ry * 0.8, "{c}", "{w2}")
    # an eight-pointed star {8/3} inside the inner ring
    pts = [pt(rot + i * 135, 0.8) for i in range(9)]
    lines += '<path d="M %s" fill="none" stroke="{c}" stroke-width="{w2}" stroke-linejoin="round"/>' % " L ".join("%.1f %.1f" % p for p in pts)
    glyphs = ""
    for i in range(8):
        x, y = pt(rot + 22.5 + i * 45, 0.9)
        glyphs += '<g transform="translate(%.1f %.1f) scale(1 0.55) translate(%.1f %.1f)">%s</g>' % (x, y, -x, -y, LN(rune_d(x, y, 6, i), "{c}", "{w2}"))
    body = lines + glyphs
    glow = body.replace("{c}", MAG).replace("{w2}", "7").replace("{w}", "9")
    core = body.replace("{c}", PINKL).replace("{w2}", "1.8").replace("{w}", "2.6")
    return blur(glow, 3.5) + core


def rune_sprite():
    s = blur(LN(rune_d(0, 0, 10, 0), PINK, 7), 2.5) + LN(rune_d(0, 0, 10, 0), CREAM, 2.2)
    return sprite(s)


# ---------------------------------------------------------------- data
hx, hy = H2C(256 - TIP[0], TIP[1])   # the hat is drawn mirrored: its tip flops to the left, away from the staff
gx, gy = H2C(*GEMH)
ox, oy = hand2c(ORB[0], ORB[1])
SPELLEMBERS = {"kind": "particles", "sprite": "a_ember", "blend": "ADD", "color": [1.0, 0.7, 0.95], "color2": [1.0, 0.5, 0.15]}

SET = {
    "key": "spellfire", "name": "Spellfire", "zone": None, "lua": "Spellfire", "file": "spellfire",
    "prof": "tailoring", "spec": "spellfire", "title": "Spellfire Savant",
    "about": "Spellfire set: a Tailoring long chase (Spellfire), violet cloth, gold thread and pink arcane fire; the whole set gives the title Spellfire Savant.",
    "preview_fur": "fur_silver",
    "pieces": [
        {"id": "set_spellfire_head", "slot": "head", "kind": "head", "art": "spellfire_head", "name": "Hat of the Burning Arcanum", "rarity": 5,
         "icon": "INV_Helmet_51", "word": "hat",
         "svg": hat(), "layers": dict(frames(4, hat_flames), mask=hat_mask(), glow=hat_glow()),
         "anim": [
             {"kind": "scroll", "sprite": "a_stars", "mask": K("spellfire_head", "mask"), "scale": 110, "vx": 8, "vy": -14, "color": [1.0, 0.75, 0.95], "blend": "ADD"},
             {"kind": "flip", "keys": [K("spellfire_head", "fl%d" % i) for i in range(1, 5)], "fps": 9},
             {"kind": "pulse", "key": K("spellfire_head", "glow"), "a": [0.25, 1.0], "speed": 2.6, "blend": "ADD"},
             dict(SPELLEMBERS, n=6, box=[hx - 22, hy - 50, hx + 22, hy - 10], vx=[-12, 12], vy=[-70, -40], life=[0.8, 1.3], size=[10, 16], sway=6, at="front"),
         ]},
        {"id": "set_spellfire_shoulders", "slot": "shoulder", "kind": "shoulder", "art": "spellfire_shoulders", "name": "Spellfire Runed Mantle", "rarity": 4,
         "icon": "INV_Shoulder_02", "word": "shoulders",
         "svg": mantle(), "layers": dict(frames(3, mantle_flames, 740), glow=mantle_glow()),
         "anim": [
             {"kind": "flip", "keys": [K("spellfire_shoulders", "fl%d" % i) for i in range(1, 4)], "fps": 8},
             {"kind": "pulse", "key": K("spellfire_shoulders", "glow"), "a": [0.2, 1.0], "speed": 2.2, "blend": "ADD"},
             {"kind": "glint", "spots": "pieceSides", "sprite": "a_spark", "n": 2, "size": [18, 28], "color": [1.0, 0.75, 0.95], "blend": "ADD", "gap": [0.6, 1.6]},
         ]},
        {"id": "set_spellfire_chest", "slot": "chest", "kind": "chest", "art": "spellfire_chest", "name": "Robe of Woven Spellfire", "rarity": 4,
         "icon": "INV_Chest_Cloth_38", "word": "robe",
         "svg": robe(), "layers": {"seam": robe_seams(), "glow": robe_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_firetile", "mask": K("spellfire_chest", "seam"), "scale": 90, "vx": 4, "vy": -34, "color": [1.0, 0.5, 0.9], "blend": "ADD"},
             {"kind": "pulse", "key": K("spellfire_chest", "glow"), "a": [0.15, 0.9], "speed": 2.0, "blend": "ADD"},
             {"kind": "glint", "spots": [[236, 306, 276, 346], [240, 404, 272, 436]], "sprite": "a_spark", "n": 2, "size": [20, 30], "color": [1.0, 0.8, 0.95], "blend": "ADD", "gap": [0.8, 1.8]},
         ]},
        {"id": "set_spellfire_cape", "slot": "back", "kind": "back", "art": "spellfire_cape", "name": "Cloak of Rising Spellfire", "rarity": 4,
         "icon": "INV_Misc_Cape_13", "word": "cape",
         "svg": cloak(), "layers": dict(frames(3, cloak_flames, 760), mask=cloak_mask()),
         "anim": [
             {"kind": "flip", "keys": [K("spellfire_cape", "fl%d" % i) for i in range(1, 4)], "fps": 8},
             {"kind": "scroll", "sprite": "a_stars", "mask": K("spellfire_cape", "mask"), "scale": 90, "vx": 0, "vy": -16, "color": [1.0, 0.85, 0.95], "blend": "ADD"},
             dict(SPELLEMBERS, n=6, box=[50, 290, 462, 430], vx=[-10, 10], vy=[-60, -30], life=[1.2, 2.0], size=[10, 16], sway=5, at="behind"),
         ]},
        {"id": "set_spellfire_weapon", "slot": "main", "kind": "weapon", "art": "spellfire_weapon", "name": "Staff of the Arcane Pyre", "rarity": 4,
         "icon": "INV_Staff_10", "word": "staff",
         "svg": staff(), "layers": dict(frames(4, staff_flames, 780), mask=staff_mask(), glow=staff_glow()),
         "anim": [
             {"kind": "scroll", "sprite": "a_swirl", "mask": K("spellfire_weapon", "mask"), "scale": 50, "vx": -30, "vy": -18, "color": [1.0, 0.8, 0.95], "blend": "ADD", "alpha": 0.8},
             {"kind": "flip", "keys": [K("spellfire_weapon", "fl%d" % i) for i in range(1, 5)], "fps": 10},
             {"kind": "pulse", "key": K("spellfire_weapon", "glow"), "a": [0.3, 1.0], "speed": 3.2, "blend": "ADD"},
             dict(SPELLEMBERS, n=5, box=[ox - 24, oy - 40, ox + 24, oy], vx=[-14, 14], vy=[-70, -40], life=[0.7, 1.2], size=[10, 16], sway=6, at="front"),
             {"kind": "glint", "spots": [[ox - 20, oy - 16, ox + 20, oy + 24]], "sprite": "a_spark", "n": 1, "size": [26, 36], "color": [1.0, 0.85, 0.95], "blend": "ADD", "gap": [0.5, 1.2]},
         ]},
        {"id": "set_spellfire_aura", "slot": "effect", "kind": "effect", "art": "spellfire_aura", "name": "Circle of the Spellfire Savant", "rarity": 5,
         "icon": "Spell_Fire_SoulBurn", "word": "aura", "glow": (1.0, 0.4, 0.8),
         "fx": {"layer": "back", "anim": "spinslow"},
         "layers": dict(frames(4, ring_frame), rune=rune_sprite()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [1.0, 0.35, 0.8], "a": [0.25, 0.6], "speed": 1.8, "blend": "ADD", "flicker": True, "at": "behind"},
             {"kind": "flip", "keys": [K("spellfire_aura", "fl%d" % i) for i in range(1, 5)], "fps": 6, "blend": "ADD", "at": "behind"},
             {"kind": "particles", "sprite": "a_flame", "n": 6, "box": [50, 420, 462, 462], "vx": [-6, 6], "vy": [-60, -36], "life": [0.9, 1.4],
              "size": [18, 28], "color": [1.0, 0.4, 0.85], "color2": [1.0, 0.62, 0.2], "blend": "ADD", "at": "behind"},
             {"kind": "particles", "sprite": "k_spellfire_aura_rune", "n": 4, "box": [50, 250, 462, 430], "vx": [-8, 8], "vy": [-40, -22], "life": [2.0, 3.0],
              "size": [22, 32], "spin": [-1.2, 1.2], "sway": 12, "blend": "ADD", "at": "front"},
             {"kind": "glint", "spots": [[30, 150, 100, 280], [412, 150, 482, 280], [70, 40, 150, 110], [362, 40, 442, 110]], "sprite": "t_arcane",
              "n": 4, "size": [36, 50], "color": [1.0, 0.7, 1.0], "gap": [0.4, 1.4], "life": 1.1, "at": "behind"},
             dict(SPELLEMBERS, n=7, box=[90, 220, 422, 460], vx=[-12, 12], vy=[-90, -50], life=[1.4, 2.2], size=[10, 18], sway=10, at="front"),
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
