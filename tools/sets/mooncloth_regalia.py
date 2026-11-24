"""Mooncloth Regalia (1.7.0): the Mooncloth tailor's long-chase set. Shimmering silver-white and pale
blue moonlit cloth: a crescent-moon circlet with stars circling it, crescent mantles over a starry
night lining, a robe embroidered with the phases of the moon, starlit side drapes, a moonbeam staff
whose crescent cradles a glowing moon, and an aura of drifting moonlight under a slow pale halo.
Crafted by Tailoring (Mooncloth), no zone or bosses; the full set gives the title Moonweaver.
  python3 tools/sets/mooncloth_regalia.py            -> Art/v/k_moonreg_*.tga, Art/moonreg_*.tga, Sets/MoonclothRegalia.lua
  python3 tools/set_preview.py tools/sets/mooncloth_regalia.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: mooncloth silver-white, pale moon blue, deep night lining
SIL, SIL2, SIL3 = "#f6f8ff", "#d9e2f3", "#a9b8d6"
SKY, SKY2, SKY3 = "#cfe3ff", "#9cc2f2", "#6f97d6"
NIGHT, NIGHT2, NIGHT3 = "#1c2456", "#2b387a", "#41539e"
MOON, MOONC = "#f4f8ff", "#ffffff"
GLOWC = "#bfdcff"
GLOWB = "#6ea4ff"   # the blurred glows: a deeper blue, so they read as moonlight and not a white blur
MOON3 = [0.72, 0.86, 1.0]

# a blur whose region is the whole canvas, so the glow of a small shape is never cut off into a box
WIDEBLUR = ('<defs><filter id="wblur" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1100" height="1100">'
            '<feGaussianBlur stdDeviation="%s"/></filter></defs>')
def blur(s, sd=5): return (WIDEBLUR % sd) + '<g filter="url(#wblur)">%s</g>' % s

def sprite(inner, S=32):
    """a small particle sprite: the drawing centred in an exact S x S box (faint corner dots fix the crop)"""
    dots = '<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/><rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S)
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)

# canvas helpers: a point in head space / body space / the right paw -> the 512 canvas (for particle boxes)
def hc(x, y): return [round(2 * (128 + (x - 128) * 0.8)), round(2 * (16 + (y - 28) * 0.8 + 16))]
def bc(x, y): return [round(2 * x), round(2 * (y + 16))]
def rc(x, y):
    a = math.radians(14)
    return bc(166 + x * math.cos(a) - y * math.sin(a), 200 + x * math.sin(a) + y * math.cos(a))
def box(p, q): return [min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1])]

def crescent_d(cx, cy, R, d, r, rot=0):
    """a crescent moon: outer circle R, bitten by a circle r whose centre sits d above; horns point up,
    then the whole thing turned by rot degrees around (cx, cy)"""
    y = (r * r - R * R - d * d) / (2.0 * d)
    x = math.sqrt(max(0.0, R * R - y * y))
    big = 1 if (y + d) < 0 else 0
    def rp(px, py):
        a = math.radians(rot)
        return cx + px * math.cos(a) - py * math.sin(a), cy + px * math.sin(a) + py * math.cos(a)
    (ax, ay), (bx, by) = rp(-x, y), rp(x, y)
    return "M %.1f %.1f A %.1f %.1f 0 1 0 %.1f %.1f A %.1f %.1f 0 %d 1 %.1f %.1f Z" % (ax, ay, R, R, bx, by, r, r, big, ax, ay)

def star4(x, y, r, fill=MOONC, ink=2.5, thin=0.32):
    """a four-pointed twinkle star"""
    t = r * thin
    d = "M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" % (
        x, y - r, x + t, y - t, x + r, y, x + t, y + t, x, y + r, x - t, y + t, x - r, y, x - t, y - t, x, y - r)
    return P(d, fill, ink)

def star5(x, y, r, fill=MOONC, ink=2.5, rot=0):
    pts = []
    for i in range(10):
        a = math.radians(rot - 90 + i * 36)
        rr = r if i % 2 == 0 else r * 0.45
        pts.append("%.1f %.1f" % (x + rr * math.cos(a), y + rr * math.sin(a)))
    return P("M " + " L ".join(pts) + " Z", fill, ink)

def feather(x, y, a, ln, col):
    """a long pointed moonlit feather from (x, y), leaning a degrees from straight up (negative: outward left)"""
    r = math.radians(a)
    ux, uy = math.sin(r), -math.cos(r)        # along the feather
    nx, ny = -uy, ux                           # across it
    w = ln * 0.2
    tx, ty = x + ux * ln, y + uy * ln
    mx, my = x + ux * ln * 0.45, y + uy * ln * 0.45
    d = "M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" % (x, y, mx + nx * w * 1.6, my + ny * w * 1.6, tx, ty, mx - nx * w * 1.6, my - ny * w * 1.6, x, y)
    s = P(d, col, 3.5)
    s += LN("M %.1f %.1f L %.1f %.1f" % (x + ux * 4, y + uy * 4, x + ux * ln * 0.85, y + uy * ln * 0.85), SKY2 if col == SIL else SKY3, 2)
    for t in (0.35, 0.55, 0.75):   # barbs
        bx, by = x + ux * ln * t, y + uy * ln * t
        s += LN("M %.1f %.1f L %.1f %.1f" % (bx, by, bx + (nx * 0.7 + ux * 0.5) * w, by + (ny * 0.7 + uy * 0.5) * w), SKY2, 1.4, .8)
    return s

def frames(n, fn, seed=700):
    return {"fl%d" % (k + 1): fn(random.Random(seed + k), k) for k in range(n)}

# ---------------------------------------------------------------- circlet (head space)
CM = (128, 30, 35, 17, 31)            # the great crescent: x, y, R, d, r
def crown_crescent(): return crescent_d(*CM)

def crown():
    s = ""
    # moonlit veil wings sweeping back from the temples
    for sx in (-1, 1):
        w = ""
        for a, ln, col in ((-66, 46, SKY), (-44, 60, SIL), (-22, 48, SKY)):
            w += feather(66, 80, a, ln, col)
        s += w if sx < 0 else mirror(w, 128)
    # the band: a thin silver circlet with a night-blue inlay
    band = "M 54 92 Q 128 70 202 92 L 200 76 Q 128 54 56 76 Z"
    s += P(band, SIL2, 4.5)
    s += LN("M 62 84 Q 128 64 194 84", NIGHT2, 5) + LN("M 62 84 Q 128 64 194 84", SKY2, 1.6)
    s += LN("M 60 78 Q 128 58 196 78", "#ffffff", 2, .8)
    # small crescents on the band, turned outward, and star studs
    for sx in (-1, 1):
        s += P(crescent_d(128 + sx * 50, 74, 9, 5, 8, rot=sx * 60), SIL, 3)
        s += star4(128 + sx * 30, 70, 5.5, SKY, 2)
        s += star4(128 + sx * 68, 84, 4.5, SKY, 2)
    # filigree arms holding the crescent
    for sx in (-1, 1):
        d = "M %d 70 C %d 56 %d 50 %d 42" % (128 + sx * 16, 128 + sx * 24, 128 + sx * 26, 128 + sx * 30)
        s += LN(d, INK, 7) + LN(d, SIL2, 3.5)
    # the great crescent with a star in its cradle
    s += P(crown_crescent(), MOON, 5)
    s += LN("M %.1f %.1f A 30 30 0 0 0 %.1f %.1f" % (101, 44, 120, 61), "#ffffff", 2.5, .9)
    s += star4(128, 24, 14, SKY, 3.5) + star4(128, 24, 6.5, MOONC, 0)
    # a teardrop moonstone hanging at the brow
    s += LN("M 128 82 L 128 88", SIL3, 2.5)
    s += P("M 128 88 Q 136 98 128 104 Q 120 98 128 88 Z", SKY, 3) + CI(126, 96, 1.6, "#ffffff", 0)
    return HEAD(s)

def crown_glow():
    s = blur(P(crown_crescent(), GLOWB, 5) + star4(128, 24, 16, GLOWB, 0), 6)
    s += blur("".join(star4(128 + sx * k, y, 7, GLOWB, 0) for sx in (-1, 1) for k, y in ((30, 70), (68, 84))), 3)
    s += star4(128, 24, 6, MOONC, 0)
    return HEAD(s)

def crown_mask():
    return HEAD(P(crown_crescent(), "#ffffff", 0) + P("M 54 92 Q 128 70 202 92 L 200 76 Q 128 54 56 76 Z", "#ffffff", 0))

def crown_orbit(rnd, k):
    """three little stars circling the crescent (4 frames x 30 degrees = one third of a turn: loops)"""
    s = ""
    for i in range(3):
        a = math.radians(k * 30 + i * 120)
        x, y = 128 + 54 * math.cos(a), 34 + 13 * math.sin(a)
        front = math.sin(a) > 0
        r = 7 if front else 4.5
        s += blur(CI(x, y, r * 1.2, GLOWB, 0), 3) + star4(x, y, r, MOONC, 2.2 if front else 1.6)
    return HEAD(s)

def mote():
    """a moonlight mote: a soft round dot with a bright core (tinted in game)"""
    return sprite(blur(CI(0, 0, 9, "#ffffff", 0), 3) + CI(0, 0, 4, "#ffffff", 0))

# ---------------------------------------------------------------- shoulders (body space, both sides)
def sh_dome():
    cx, cy = SH_C
    return "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 30, cy + 8, cx + 26, cy - 22, cx - 4, cy - 22,
        cx - 34, cy - 20, cx - 36, cy + 12, cx - 4, cy + 22, cx + 30, cy + 8)

def sh_cres():
    cx, cy = SH_C
    return crescent_d(cx - 10, cy - 2, 32, 15, 28, rot=50)

def pauldron():
    cx, cy = SH_C
    s = ""
    # layered mooncloth flaps hanging under the dome, each tipped with a star charm
    for i, (x, ln) in enumerate(((cx - 30, 30), (cx - 14, 34), (cx + 4, 30), (cx + 20, 22))):
        d = "M %d %d L %d %d Q %d %d %d %d L %d %d Z" % (x - 9, cy + 4, x - 7, cy + ln, x, cy + ln + 7, x + 7, cy + ln, x + 9, cy + 4)
        s += P(d, SIL if i % 2 == 0 else SKY, 3.5) + LN("M %d %d L %d %d" % (x, cy + 8, x, cy + ln), SKY2 if i % 2 == 0 else SKY3, 2)
        s += star4(x, cy + ln + 10, 4.5, SKY, 2)
    s += P(sh_dome(), NIGHT2, 5)
    s += LN("M %d %d Q %d %d %d %d" % (cx - 36, cy + 10, cx - 4, cy + 24, cx + 28, cy + 8), SIL2, 6) + LN("M %d %d Q %d %d %d %d" % (cx - 36, cy + 10, cx - 4, cy + 24, cx + 28, cy + 8), INK, 2)
    for x, y in ((cx - 18, cy - 10), (cx + 10, cy - 12), (cx - 2, cy + 4), (cx + 18, cy)):
        s += CI(x, y, 1.6, "#ffffff", 0)
    # the crescent plate curling around the dome
    s += P(sh_cres(), MOON, 4.5)
    s += star4(cx - 4, cy - 4, 8, SKY, 3) + star4(cx - 4, cy - 4, 3.5, MOONC, 0)
    return BOTH(s)

def pauldron_glow():
    cx, cy = SH_C
    return BOTH(blur(P(sh_cres(), GLOWB, 4) + star4(cx - 4, cy - 4, 12, GLOWB, 0), 5) + star4(cx - 4, cy - 4, 4, MOONC, 0))

def pauldron_mask():
    return BOTH(P(sh_dome(), "#ffffff", 0))

# ---------------------------------------------------------------- robe (body space)
PANEL = "M 112 124 Q 128 128 144 124 L 154 212 L 102 212 Z"
PHASES = [(152, 0.25), (166, 0.5), (183, 1.0)]   # y, how full: crescent, half, full moon brooch
def moon_phase(x, y, r, f, ink=3):
    """a moon: f=1 full, 0.5 half, lower = thinner crescent (lit side right)"""
    s = CI(x, y, r, NIGHT3, ink)
    if f >= 1: return CI(x, y, r, MOON, ink) + CI(x - r * .3, y - r * .2, r * .22, SKY, 0) + CI(x + r * .35, y + r * .3, r * .15, SKY, 0)
    k = (1 - 2 * f) * r   # x radius of the terminator ellipse
    sweep = 1 if f < 0.5 else 0
    d = "M %.1f %.1f A %.1f %.1f 0 0 1 %.1f %.1f A %.1f %.1f 0 0 %d %.1f %.1f Z" % (x, y - r, r, r, x, y + r, abs(k) + .01, r, sweep, x, y - r)
    return s + P(d, MOON, 0) + CI(x, y, r, "none", ink)

def chest():
    s = P(BODY_OUT, SIL, 5)
    # soft folds of the mooncloth
    for sx in (-1, 1):
        for x0, x1 in ((92, 84), (78, 70)):
            s += LN("M %d 132 Q %d 170 %d 210" % (128 + sx * (128 - x0), 128 + sx * (128 - x0 + 4), 128 + sx * (128 - x1)), SKY, 3.5)
    # the night panel down the front, trimmed in pale blue with stitched stars
    s += P(PANEL, NIGHT, 4)
    for sx in (-1, 1):
        d = "M %d 126 L %d 212" % (128 + sx * 17, 128 + sx * 27)
        s += LN(d, INK, 8) + LN(d, SKY2, 4)
        for t in (0.2, 0.5, 0.8):
            s += star4(128 + sx * (17 + 10 * t), 126 + 86 * t, 3.5, MOONC, 1.5)
    for y, f in PHASES:
        s += moon_phase(128, y, 6 if f < 1 else 10, f, 2.5)
    # high pale collar
    s += P("M 98 118 Q 112 132 128 135 Q 144 132 158 118 L 164 122 Q 150 140 128 143 Q 106 140 92 122 Z", SKY, 4)
    s += LN("M 98 123 Q 112 136 128 139 Q 144 136 158 123", "#ffffff", 1.8, .8)
    # embroidered crescents and stars scattered over the white cloth
    for sx in (-1, 1):
        for x, y, k in ((84, 150, 0), (96, 176, 1), (80, 192, 2), (98, 140, 3)):
            X = 128 + sx * (128 - x)
            if k % 2 == 0: s += P(crescent_d(X, y, 5, 3, 4.5, rot=sx * 40), SKY2, 1.5)
            else: s += star4(X, y, 4, SKY2, 1.4)
    # pale blue hem band
    s += P("M 58 196 L 198 196 L 198 214 L 58 214 Z", SKY, 0)
    # sash with a crescent clasp
    s += RC(60, 198, 136, 14, SKY2, 4, 4) + LN("M 64 203 L 192 203", "#ffffff", 1.6, .6)
    s += P(crescent_d(128, 205, 11, 6, 10, rot=0), MOON, 3) + star4(128, 202, 4, SKY, 1.6)
    return s

def chest_panel():
    return P(PANEL, "#ffffff", 0)

def chest_cloth():
    return P(BODY_OUT, "#ffffff", 0)

def chest_glow():
    s = "".join(blur(CI(128, y, (6 if f < 1 else 9) + 3, GLOWB, 0), 4) for y, f in PHASES)
    s += "".join(star4(128 + sx * (17 + 10 * t), 126 + 86 * t, 3, MOONC, 0) for sx in (-1, 1) for t in (0.2, 0.5, 0.8))
    s += blur(P(crescent_d(128, 205, 11, 6, 10), GLOWB, 3), 3)
    return s

# ---------------------------------------------------------------- cape (side drapes)
def cape():
    s = "".join(P(p, NIGHT, 5) for p in DRAPE_OUT) + "".join(P(p, NIGHT2, 3) for p in DRAPE_IN)
    # silver hem along the outer edges with stitched stars
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        d = "M " + " L ".join("%.1f %.1f" % (x + (4 if x < 128 else -4), y) for x, y in pts)
        s += LN(d, INK, 9) + LN(d, SIL2, 5) + LN(d, SKY2, 1.6)
        for i, (x, y) in enumerate(qpts(*side, n=5)[1:]):
            out = -1 if x < 128 else 1
            s += star4(x - out * 10, y - 2, 4 if i % 2 else 5.5, MOONC, 1.8)
    # crescent clasps at the shoulders and moon charms at the hems
    for sx in (-1, 1):
        x = 128 + sx * 50
        s += P(crescent_d(x, 112, 10, 5, 9, rot=sx * 30), MOON, 3.5) + CI(x, 112, 3, SKY, 2)
        hx = 128 + sx * 82
        s += LN("M %d 206 L %d 216" % (hx, hx), SIL3, 2.5) + moon_phase(hx, 222, 6, 1.0, 2.5)
    return s

def cape_mask():
    return "".join(P(p, "#ffffff", 0) for p in DRAPE_OUT)

def cape_glow():
    s = ""
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        d = "M " + " L ".join("%.1f %.1f" % (x + (4 if x < 128 else -4), y) for x, y in pts)
        s += blur(LN(d, GLOWB, 8), 4) + LN(d, MOONC, 1.6)
    for sx in (-1, 1): s += blur(CI(128 + sx * 82, 222, 7, GLOWB, 0), 3)
    return s

# ---------------------------------------------------------------- moonbeam staff (right paw)
SL = 150
TOP = (0, -SL - 26)                  # the moon in the crescent's cradle
def staff_cres(): return crescent_d(0, -SL - 22, 30, 15, 26)

def staff():
    s = RC(-5.5, -SL, 11, SL + 32, SIL2, 4, 4)
    s += LN("M -2 -%d L -2 26" % (SL - 4), "#ffffff", 2, .7)
    for y in range(-SL + 18, 10, 26):   # pale ribbon wound around the shaft
        s += P("M -7 %d L 7 %d L 7 %d L -7 %d Z" % (y, y - 9, y - 3, y + 6), SKY2, 2.5)
    s += RC(-9, -SL - 4, 18, 10, SIL, 3, 3.5) + RC(-8, -12, 16, 9, SIL, 3, 3)
    s += star4(0, 36, 8, SKY, 3)
    # the crescent and its little hanging stars
    s += P(staff_cres(), MOON, 5)
    s += LN("M -24 -%d A 26 26 0 0 0 -8 -%d" % (SL + 12, SL - 3), "#ffffff", 2.5, .9)
    for sx in (-1, 1):
        x = sx * 26
        s += LN("M %d -%d L %d -%d" % (x, SL + 34, x, SL + 22), SIL3, 2) + star4(x, -SL - 18, 5, SKY, 2)
    s += CI(TOP[0], TOP[1], 12, MOON, 4) + CI(-4, TOP[1] - 3, 2.5, SKY, 0) + CI(4, TOP[1] + 4, 2, SKY, 0)
    return RHAND(s)

def staff_glow():
    return RHAND(blur(CI(TOP[0], TOP[1], 20, GLOWB, 0), 7) + blur(P(staff_cres(), GLOWB, 4), 4) + CI(TOP[0], TOP[1], 6, MOONC, 0))

def staff_mask():
    return RHAND(P(staff_cres(), "#ffffff", 0))

def staff_rays(rnd, k):
    """eight moonbeams wheeling around the moon (4 frames x 11.25 degrees = one eighth of a turn: loops)"""
    s = ""
    x0, y0 = TOP
    for i in range(8):
        a = math.radians(k * 11.25 + i * 45)
        L = 40 if i % 2 == 0 else 28
        ca, sa = math.cos(a), math.sin(a)
        tip = (x0 + ca * L, y0 + sa * L)
        l = (x0 + ca * 14 - sa * 4, y0 + sa * 14 + ca * 4)
        r = (x0 + ca * 14 + sa * 4, y0 + sa * 14 - ca * 4)
        s += '<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" fill="%s" opacity=".8"/>' % (l[0], l[1], tip[0], tip[1], r[0], r[1], GLOWB)
    return RHAND(blur(s, 2.5))

# ---------------------------------------------------------------- aura: drifting moonlight under a slow pale halo
HALO = (128, 112, 104)
def halo_glow():
    x, y, r = HALO
    return blur('<circle cx="%d" cy="%d" r="%d" fill="none" stroke="%s" stroke-width="14"/>' % (x, y, r, GLOWB), 8)

def halo_ring(rnd, k):
    """the crisp halo: a thin silver ring with twelve stars that turn slowly (4 frames x 7.5 degrees: loops)"""
    x, y, r = HALO
    s = '<circle cx="%d" cy="%d" r="%d" fill="none" stroke="%s" stroke-width="2.5" opacity=".9"/>' % (x, y, r, MOONC)
    s += '<circle cx="%d" cy="%d" r="%d" fill="none" stroke="%s" stroke-width="1.2" opacity=".6" stroke-dasharray="2 7"/>' % (x, y, r - 9, MOONC)
    for i in range(12):
        a = math.radians(k * 7.5 + i * 30)
        px, py = x + r * math.cos(a), y + r * math.sin(a)
        big = i % 3 == 0
        s += blur(CI(px, py, 7 if big else 4, GLOWB, 0), 3)
        s += star4(px, py, 7 if big else 4, MOONC, 0, 0.26)
    return s

SET = {
    "key": "moonreg", "name": "Mooncloth Regalia", "zone": None, "lua": "MoonclothRegalia", "file": "mooncloth_regalia",
    "prof": "tailoring", "spec": "mooncloth", "title": "Moonweaver",
    "about": "Mooncloth Regalia: the Mooncloth tailor's long-chase set, silver moonlit cloth, crescents and drifting stars.",
    "preview_fur": "fur_midnight",
    "pieces": [
        {"id": "set_moonreg_head", "slot": "head", "kind": "head", "art": "moonreg_head", "name": "Crescent Circlet of the Moonweaver", "rarity": 5,
         "icon": "INV_Crown_01", "word": "crown",
         "svg": crown(), "layers": dict(frames(4, crown_orbit), glow=crown_glow(), mask=crown_mask(), mote=mote()),
         "anim": [
             {"kind": "pulse", "key": K("moonreg_head", "glow"), "a": [0.25, 0.85], "speed": 1.8, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_shine", "mask": K("moonreg_head", "mask"), "scale": 90, "vx": 40, "vy": 0, "color": MOON3, "blend": "ADD", "alpha": 0.6},
             {"kind": "flip", "keys": [K("moonreg_head", "fl%d" % i) for i in range(1, 5)], "fps": 6, "at": "front"},
             {"kind": "glint", "n": 3, "spots": [box(hc(100, 2), hc(156, 60)), box(hc(60, 64), hc(196, 90))], "life": 0.7, "gap": [0.4, 1.2],
              "size": [14, 22], "color": [0.85, 0.93, 1.0], "blend": "ADD", "at": "front"},
             {"kind": "particles", "sprite": "k_moonreg_head_mote", "n": 6, "box": box(hc(70, -6), hc(186, 40)), "vx": [-8, 8], "vy": [-30, -14],
              "life": [1.6, 2.6], "size": [8, 14], "color": MOON3, "blend": "ADD", "sway": 6, "at": "front"},
         ]},
        {"id": "set_moonreg_shoulders", "slot": "shoulder", "kind": "shoulder", "art": "moonreg_shoulders", "name": "Shoulders of the Twin Crescents", "rarity": 4,
         "icon": "INV_Shoulder_02", "word": "shoulders",
         "svg": pauldron(), "layers": {"glow": pauldron_glow(), "mask": pauldron_mask()},
         "anim": [
             {"kind": "scroll", "sprite": "a_stars", "mask": K("moonreg_shoulders", "mask"), "scale": 110, "vx": 6, "vy": -8, "color": MOON3, "blend": "ADD"},
             {"kind": "pulse", "key": K("moonreg_shoulders", "glow"), "a": [0.25, 1.0], "speed": 1.7, "blend": "ADD"},
             {"kind": "glint", "n": 2, "spots": "pieceSides", "life": 0.7, "gap": [0.5, 1.4], "size": [12, 20], "color": [0.85, 0.93, 1.0], "blend": "ADD", "at": "front"},
             {"kind": "particles", "sprite": "a_spark", "n": 4, "box": [80, 300, 440, 340], "vx": [-4, 4], "vy": [12, 28], "life": [1.2, 1.8],
              "size": [8, 13], "color": MOON3, "blend": "ADD", "sway": 3, "at": "front"},
         ]},
        {"id": "set_moonreg_chest", "slot": "chest", "kind": "chest", "art": "moonreg_chest", "name": "Robe of the Turning Moons", "rarity": 4,
         "icon": "INV_Chest_Cloth_16", "word": "robe",
         "svg": chest(), "layers": {"panel": chest_panel(), "cloth": chest_cloth(), "glow": chest_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K("moonreg_chest", "cloth"), "scale": 180, "vx": 26, "vy": 10, "color": MOON3, "blend": "ADD", "alpha": 0.45},
             {"kind": "scroll", "sprite": "a_stars", "mask": K("moonreg_chest", "panel"), "scale": 100, "vx": 0, "vy": -10, "color": MOON3, "blend": "ADD"},
             {"kind": "pulse", "key": K("moonreg_chest", "glow"), "a": [0.2, 0.95], "speed": 1.9, "blend": "ADD"},
             {"kind": "glint", "n": 2, "spots": [box(bc(112, 130), bc(144, 196))], "life": 0.7, "gap": [0.6, 1.4], "size": [12, 18], "color": [0.85, 0.93, 1.0], "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_moonreg_cape", "slot": "back", "kind": "back", "art": "moonreg_cape", "name": "Drape of the Starlit Night", "rarity": 4,
         "icon": "INV_Misc_Cape_06", "word": "cape",
         "svg": cape(), "layers": {"mask": cape_mask(), "glow": cape_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_stars", "mask": K("moonreg_cape", "mask"), "scale": 120, "vx": 4, "vy": 12, "color": MOON3, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_nebula", "mask": K("moonreg_cape", "mask"), "scale": 200, "vx": -6, "vy": 4, "color": [0.55, 0.7, 1.0], "blend": "ADD", "alpha": 0.35},
             {"kind": "pulse", "key": K("moonreg_cape", "glow"), "a": [0.15, 0.9], "speed": 1.5, "blend": "ADD"},
             {"kind": "particles", "sprite": "t_star", "n": 3, "box": [56, 260, 100, 380], "vx": [-14, -4], "vy": [26, 44], "life": [1.4, 2.0],
              "size": [9, 14], "color": [0.85, 0.92, 1.0], "spin": [-1.5, 1.5], "at": "behind"},
             {"kind": "particles", "sprite": "t_star", "n": 3, "box": [412, 260, 456, 380], "vx": [4, 14], "vy": [26, 44], "life": [1.4, 2.0],
              "size": [9, 14], "color": [0.85, 0.92, 1.0], "spin": [-1.5, 1.5], "at": "behind"},
         ]},
        {"id": "set_moonreg_weapon", "slot": "main", "kind": "weapon", "art": "moonreg_weapon", "name": "Moonbeam Crescent Staff", "rarity": 4,
         "icon": "INV_Staff_13", "word": "staff",
         "svg": staff(), "layers": dict(frames(4, staff_rays), glow=staff_glow(), mask=staff_mask()),
         "anim": [
             {"kind": "flip", "keys": [K("moonreg_weapon", "fl%d" % i) for i in range(1, 5)], "fps": 7, "blend": "ADD", "alpha": 0.8},
             {"kind": "pulse", "key": K("moonreg_weapon", "glow"), "a": [0.3, 0.85], "speed": 2.2, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_shine", "mask": K("moonreg_weapon", "mask"), "scale": 70, "vx": 30, "vy": -10, "color": MOON3, "blend": "ADD", "alpha": 0.8},
             {"kind": "particles", "sprite": "a_spark", "n": 5, "box": box(rc(-30, -SL - 30), rc(30, -SL + 10)), "vx": [-6, 6], "vy": [14, 34], "life": [1.0, 1.6],
              "size": [8, 14], "color": MOON3, "blend": "ADD", "sway": 4, "at": "front"},
             {"kind": "glint", "n": 2, "spots": [box(rc(-30, -SL - 50), rc(30, -SL + 6))], "life": 0.6, "gap": [0.4, 1.0], "size": [14, 22], "color": [0.9, 0.95, 1.0], "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_moonreg_aura", "slot": "effect", "kind": "effect", "art": "moonreg_aura", "name": "Moonweaver's Halo", "rarity": 5,
         "icon": "Spell_Nature_AstralRecal", "word": "aura", "glow": (0.72, 0.86, 1.0),
         "fx": {"layer": "back", "anim": "float"},
         "layers": dict(frames(4, halo_ring), halo=halo_glow(), mote=mote()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [0.45, 0.65, 1.0], "a": [0.1, 0.3], "speed": 1.1, "blend": "ADD", "at": "behind"},
             {"kind": "pulse", "key": K("moonreg_aura", "halo"), "a": [0.2, 0.7], "speed": 0.9, "blend": "ADD", "at": "behind"},
             {"kind": "flip", "keys": [K("moonreg_aura", "fl%d" % i) for i in range(1, 5)], "fps": 3, "blend": "ADD", "alpha": 0.9, "at": "behind"},
             {"kind": "particles", "sprite": "k_moonreg_aura_mote", "n": 8, "box": [70, 200, 442, 470], "vx": [-10, 10], "vy": [-40, -18], "life": [2.0, 3.2],
              "size": [8, 16], "color": MOON3, "blend": "ADD", "sway": 10, "at": "front"},
             {"kind": "particles", "sprite": "t_moon", "n": 3, "box": [60, 160, 452, 440], "vx": [-6, 6], "vy": [-26, -14], "life": [2.4, 3.4],
              "size": [16, 24], "color": [0.8, 0.9, 1.0], "alpha": 0.9, "spin": [-0.4, 0.4], "sway": 8, "at": "behind"},
             {"kind": "glint", "n": 4, "spots": [[40, 60, 140, 460], [372, 60, 472, 460], [140, 20, 372, 90]], "life": 0.8, "gap": [0.3, 1.0],
              "size": [14, 24], "color": [0.85, 0.93, 1.0], "blend": "ADD", "at": "front"},
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
