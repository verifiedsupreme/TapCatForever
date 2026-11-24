"""Pinchy's Wish (1.7.0): the Fishing long-chase set. Mr. Pinchy the magic lobster rides on the cat's head
and snaps his claws, a fishing-net cape hung with shells and starfish shimmers like sea water, a golden
rod swings a sparkling lure, and bubbles, wish sparkles and tiny Pinchys in bubbles rise around the cat.
Crafted by Fishing (ProfSets.lua); the whole set gives the title Angler of Legend.
  python3 tools/sets/pinchys_wish.py            -> Art/v/k_pinchy_*.tga, Art/pinchy_*.tga, Sets/PinchysWish.lua
  python3 tools/set_preview.py tools/sets/pinchys_wish.py <out>   -> animated preview
"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: lobster red, treasure gold, deep sea, net rope, pearl
RED, RED2, REDD, REDL = "#e8442e", "#ff7a52", "#a82618", "#ffb59a"
GOLD, GOLD2, GOLDD, GOLDC = "#f5c23e", "#ffe48a", "#c48a22", "#fff6cf"
SEA, SEA2, SEAD, SEADD = "#2c9cc4", "#86e4f2", "#1d5f8c", "#163e66"
ROPE, ROPED = "#f0ddb0", "#c9ad74"
PEARL = "#fff4fa"
CORAL, CORAL2 = "#ff8a5c", "#ffc29a"
AQUA3 = [0.45, 0.95, 1.0]
GOLD3 = [1.0, 0.85, 0.35]

WIDEBLUR = ('<defs><filter id="wblur" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1100" height="1100">'
            '<feGaussianBlur stdDeviation="%s"/></filter></defs>')
def blur(s, sd=5): return WIDEBLUR % sd + '<g filter="url(#wblur)">%s</g>' % s

def sprite(inner, S=32):
    """a small particle sprite: the drawing centred in an exact S x S box (faint corner dots fix the crop)"""
    dots = '<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/><rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S)
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)

def rot(s, a, x, y): return '<g transform="rotate(%.1f %.1f %.1f)">%s</g>' % (a, x, y, s)
def tr(s, x, y, sc=1.0, a=0.0): return '<g transform="translate(%.1f %.1f) rotate(%.1f) scale(%.3f)">%s</g>' % (x, y, a, sc, s)

def H(x, y):   # head space -> 512 canvas
    return 2 * (128 + 0.8 * (x - 128)), 2 * (32 + 0.8 * (y - 28))
def B(x, y):   # body space -> 512 canvas
    return 2 * x, 2 * (y + 16)
def box(c, w, h): return [round(c[0] - w), round(c[1] - h), round(c[0] + w), round(c[1] + h)]

def star5(x, y, R, r, fill, ink=3, a=-90):
    pts = []
    for i in range(10):
        rr = R if i % 2 == 0 else r
        t = math.radians(a + i * 36)
        pts.append((x + rr * math.cos(t), y + rr * math.sin(t)))
    d = "M %.1f %.1f " % pts[0]
    for i in range(1, 11):
        p, q = pts[i % 10], pts[(i - 1) % 10]
        if i % 2 == 1:   # inner corner: soft
            d += "Q %.1f %.1f %.1f %.1f " % (q[0] * 0.15 + p[0] * 0.85, q[1] * 0.15 + p[1] * 0.85, p[0], p[1])
        else:
            d += "L %.1f %.1f " % p
    return P(d + "Z", fill, ink)

def starfish(x, y, R, a=0):
    s = star5(x, y, R, R * 0.45, CORAL, 3, -90 + a)
    s += star5(x, y, R * 0.55, R * 0.25, CORAL2, 0, -90 + a)
    for i in range(5):
        t = math.radians(-90 + a + i * 72)
        s += '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#fff" opacity=".85"/>' % (x + R * 0.6 * math.cos(t), y + R * 0.6 * math.sin(t), max(1, R * 0.09))
    return s

def scallop(x, y, r, a=0, col=GOLD, rib=GOLDD):
    """a fan shell, hinge at the bottom"""
    s = P("M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x - r * 0.42, y + r * 0.55, x - r * 0.2, y + r * 0.25, x + r * 0.2, y + r * 0.25, x + r * 0.42, y + r * 0.55), col, 2.5)
    d = "M %.1f %.1f " % (x - r * 0.2, y + r * 0.3)
    n = 5
    for i in range(n + 1):
        t = math.radians(200 + i * 140 / n)
        px, py = x + r * math.cos(t), y + r * math.sin(t) * 0.95
        if i == 0: d += "L %.1f %.1f " % (px, py)
        else:
            tm = math.radians(200 + (i - 0.5) * 140 / n)
            d += "Q %.1f %.1f %.1f %.1f " % (x + r * 1.18 * math.cos(tm), y + r * 1.12 * math.sin(tm), px, py)
    d += "L %.1f %.1f Z" % (x + r * 0.2, y + r * 0.3)
    s += P(d, col, 3)
    for i in range(1, n):
        t = math.radians(200 + i * 140 / n)
        s += LN("M %.1f %.1f L %.1f %.1f" % (x, y + r * 0.25, x + r * 0.85 * math.cos(t), y + r * 0.8 * math.sin(t)), rib, 1.8)
    return rot(s, a, x, y)

def pearl(x, y, r):
    return CI(x, y, r, PEARL, 2.5) + '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#ffd6ee" opacity=".7"/>' % (x + r * 0.25, y + r * 0.3, r * 0.45) \
        + '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#fff"/>' % (x - r * 0.35, y - r * 0.35, max(1, r * 0.3))

# ---------------------------------------------------------------- Mr. Pinchy (head space)
def claw_base():
    """claw pointing up, wrist at 0 0: the palm and the fixed finger"""
    palm = "M -13 0 C -28 -12 -26 -40 -10 -48 L 14 -48 C 28 -38 24 -10 13 0 Z"
    fixed = "M 0 -44 C 6 -56 12 -66 8 -86 C 24 -76 26 -54 16 -44 Z"
    s = P(fixed, RED, 3.5) + P(palm, RED, 4)
    s += LN("M -16 -30 Q -12 -42 -2 -44", REDL, 3, .8)
    for y in (-58, -66): s += P("M 4 %d l -4 2 l 4 3 Z" % y, PEARL, 1.5)
    s += '<circle cx="8" cy="-24" r="3" fill="%s"/><circle cx="-6" cy="-14" r="2.4" fill="%s"/>' % (REDD, REDD)
    return s

def claw_finger(open_deg):
    mov = "M -16 -44 C -24 -60 -14 -80 2 -86 C -4 -72 -2 -56 2 -44 Z"
    s = P(mov, RED, 3.5) + LN("M -16 -50 Q -18 -66 -8 -78", REDL, 2.5, .8)
    s += P("M -2 -62 l 4 2 l -4 3 Z", PEARL, 1.5)
    return rot(s, -open_deg, -4, -44)

CLAWS = [((38, 66), -28), ((218, 66), 28)]   # wrist (head space), lean
CLAW_SC = 0.8
def arm(side):
    sx = -1 if side == 0 else 1
    (wx, wy), _ = CLAWS[side]
    x0, y0 = 128 + sx * 66, 80
    d = "M %.1f %.1f Q %.1f %.1f %.1f %.1f" % (x0, y0, 128 + sx * 86, 86, wx, wy)
    s = LN(d, INK, 15) + LN(d, RED, 9)
    s += CI(128 + sx * 82, 80, 6, RED, 3)
    return s

def claw(side, part, open_deg=0):
    (wx, wy), lean = CLAWS[side]
    body = claw_base() if part == "base" else claw_finger(open_deg)
    if side == 1:
        body = mirror(body, 0)
    return tr(body, wx, wy, CLAW_SC, lean)

DOME = "M 44 98 C 36 34 80 8 128 8 C 176 8 220 34 212 98 Q 128 82 44 98 Z"
BAND = "M 44 100 Q 128 82 212 100 L 210 84 Q 128 66 46 84 Z"
def lobster_hat():
    s = arm(0) + arm(1)
    s += claw(0, "base") + claw(1, "base")
    # antennae sweeping back over the claws
    for sx in (-1, 1):
        d = "M %.1f 12 Q %.1f -10 %.1f -6 Q %.1f -2 %.1f 14" % (128 + sx * 10, 128 + sx * 30, 128 + sx * 62, 128 + sx * 78, 128 + sx * 84)
        s += LN(d, INK, 5) + LN(d, RED2, 2.5)
    s += P(DOME, RED, 5)
    # shell plates and freckles
    s += P("M 58 52 Q 128 30 198 52 Q 196 44 190 38 Q 128 22 66 38 Q 60 44 58 52 Z", RED2, 0)
    for d in ("M 50 74 Q 128 54 206 74", "M 60 48 Q 128 28 196 48"): s += LN(d, REDD, 3.5)
    s += LN("M 70 30 Q 96 14 124 14", "#ffffff", 4, .45)
    for x, y, r in ((72, 62, 3.5), (88, 58, 2.5), (176, 60, 3.5), (190, 66, 2.5), (160, 36, 2.5), (98, 34, 2.5)):
        s += '<circle cx="%d" cy="%d" r="%.1f" fill="%s"/>' % (x, y, r, REDD)
    # the cheery face: eyes on stalks, a smile and blush
    for sx in (-1, 1):
        sx0 = 128 + sx * 14
        s += LN("M %.1f 16 L %.1f 2" % (sx0, sx0 + sx * 8), INK, 8) + LN("M %.1f 16 L %.1f 2" % (sx0, sx0 + sx * 8), RED, 4)
        ex = sx0 + sx * 9
        s += CI(ex, -1, 8.5, "#ffffff", 3.5) + CI(ex - sx * 1.5, 0, 4.6, INK, 0) + '<circle cx="%.1f" cy="-2.5" r="1.8" fill="#fff"/>' % (ex - sx * 2.5)
    s += LN("M 116 42 Q 128 52 140 42", INK, 3.5)
    s += EL(102, 44, 7, 4, "#ff9a9a", 0) + EL(154, 44, 7, 4, "#ff9a9a", 0)
    # golden band with pearls, a scallop holding the wish pearl
    s += P(BAND, GOLD, 4.5) + LN("M 50 88 Q 128 72 206 88", GOLD2, 2.5)
    for i in range(10):
        x = 58 + i * 15.5
        if abs(x - 128) < 22: continue
        y = 92 - 13 * (1 - ((x - 128) / 82.0) ** 2) + 0.5
        s += pearl(x, y, 3.4)
    s += scallop(128, 80, 17)
    s += pearl(128, 84, 9)
    return HEAD(s)

def hat_fingers(k):
    opens = (2, 20, 36, 20)
    return HEAD(claw(0, "finger", opens[k]) + claw(1, "finger", opens[k]))

def hat_glow():
    s = blur(CI(128, 84, 14, GOLD2, 0), 6) + CI(128, 84, 5, GOLDC, 0)
    return HEAD(s)

# ---------------------------------------------------------------- fishing-net cape (side drapes)
CLIP = '<defs><clipPath id="pwnet">%s</clipPath></defs>' % "".join('<path d="%s"/>' % d for d in DRAPE_OUT)
SHELLS_L = [(44, 180, 10, -20), (58, 138, 8, 10)]
STARS_L = [(38, 154, 11, 8), (54, 202, 8, -12)]
def net():
    s = ""
    for k in range(-12, 30):
        x0 = k * 9
        s += LN("M %d 100 L %d 230" % (x0, x0 + 130), ROPE, 2, .85) + LN("M %d 100 L %d 230" % (x0 + 130, x0), ROPE, 2, .85)
    return '<g clip-path="url(#pwnet)">%s</g>' % s

def cape_side():
    s = ""
    for x, y, r, a in SHELLS_L: s += scallop(x, y, r, a, PEARL, "#d9a9c4") + pearl(x, y + 2, r * 0.32)
    for x, y, r, a in STARS_L: s += starfish(x, y, r, a)
    return s

def cape():
    s = "".join(P(d, SEAD, 5) for d in DRAPE_OUT) + "".join(P(d, SEA, 3) for d in DRAPE_IN)
    s += CLIP + net()
    for side in DRAPE_EDGE:   # rope edge with cork floats
        pts = qpts(*side, n=10)
        d = "M " + " L ".join("%.1f %.1f" % (x + (3 if x < 128 else -3), y) for x, y in pts)
        s += LN(d, INK, 9) + LN(d, ROPE, 5) + LN(d, ROPED, 1.5)
        for i, (x, y) in enumerate(qpts(*side, n=4)[1:]):
            x += 3 if x < 128 else -3
            s += CI(x, y, 5.5, "#ffffff", 3) + P("M %.1f %.1f A 5.5 5.5 0 0 1 %.1f %.1f Z" % (x - 5.5, y, x + 5.5, y), "#e8442e", 0)
    s += cape_side() + mirror(cape_side(), 128)
    return s

def cape_mask():
    return "".join(P(d, "#ffffff", 0) for d in DRAPE_OUT)

def cape_glow():
    one = "".join(blur(CI(x, y + 2, r * 0.7, "#ffe6f6", 0), 3) for x, y, r, a in SHELLS_L)
    one += "".join(blur(star5(x, y, r * 1.2, r * 0.6, GOLD2, 0), 3) for x, y, r, a in STARS_L)
    return one + mirror(one, 128)

# ---------------------------------------------------------------- golden rod and lure (right paw)
HAND = (166, 200, 14)
def to_body(x, y):
    a = math.radians(HAND[2])
    return HAND[0] + x * math.cos(a) - y * math.sin(a), HAND[1] + x * math.sin(a) + y * math.cos(a)

ROD = ((0, 30), (-10, -92), (20, -170))
def rod_pt(t):
    (x0, y0), (x1, y1), (x2, y2) = ROD
    x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * x1 + t * t * x2
    y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * y1 + t * t * y2
    dx = 2 * (1 - t) * (x1 - x0) + 2 * t * (x2 - x1)
    dy = 2 * (1 - t) * (y1 - y0) + 2 * t * (y2 - y1)
    l = math.hypot(dx, dy)
    return x, y, -dy / l, dx / l

def rod_poly(t0, t1, w0, w1, n=18):
    L, R = [], []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        x, y, nx, ny = rod_pt(t)
        w = w0 + (w1 - w0) * (t - t0) / (t1 - t0)
        L.append((x + nx * w, y + ny * w)); R.append((x - nx * w, y - ny * w))
    pts = L + R[::-1]
    return "M " + " L ".join("%.1f %.1f" % p for p in pts) + " Z"

def rod():
    s = P(rod_poly(0.0, 1.0, 6.5, 2.8), GOLD, 3.5)
    x, y, nx, ny = rod_pt(0.5)
    s += LN("M " + " L ".join("%.1f %.1f" % rod_pt(t)[:2] for t in [0.2 + i * 0.04 for i in range(18)]), GOLD2, 1.8)
    s += P(rod_poly(0.0, 0.2, 8.5, 7.5), "#d9a066", 3.5)   # cork grip
    for t in (0.04, 0.09, 0.14):
        x, y, nx, ny = rod_pt(t)
        s += '<circle cx="%.1f" cy="%.1f" r="1.3" fill="#9a6838"/>' % (x + nx * 2, y + ny * 2)
    for t, w in ((0.0, 8.5), (0.2, 8)):   # gold ferrules
        x, y, nx, ny = rod_pt(t)
        s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x + nx * w, y + ny * w, x - nx * w, y - ny * w, x - nx * w + ny * 5, y - ny * w - nx * 5, x + nx * w + ny * 5, y + ny * w - nx * 5), GOLD, 3)
    for t in (0.42, 0.62, 0.8, 0.93):   # line guides
        x, y, nx, ny = rod_pt(t)
        s += CI(x - nx * 6, y - ny * 6, 2.6, "none", 2) + LN("M %.1f %.1f L %.1f %.1f" % (x, y, x - nx * 4, y - ny * 4), INK, 2)
    # the reel
    x, y, nx, ny = rod_pt(0.27)
    rx, ry = x - nx * 13, y - ny * 13
    s += LN("M %.1f %.1f L %.1f %.1f" % (x, y, rx, ry), INK, 6) + LN("M %.1f %.1f L %.1f %.1f" % (x, y, rx, ry), GOLDD, 3)
    s += CI(rx, ry, 10, GOLD, 3.5) + CI(rx, ry, 5.5, GOLD2, 2) + CI(rx, ry, 2.2, "#e0445a", 0)
    s += LN("M %.1f %.1f L %.1f %.1f" % (rx, ry, rx - 4, ry + 11), INK, 3) + CI(rx - 4, ry + 12, 3, "#ffffff", 2)
    # pommel and tip star
    x, y, nx, ny = rod_pt(0.0)
    s += CI(x, y + 6, 6, GOLD, 3) + GEM(x, y + 6, 3, "#3fc3e8")
    tx, ty = rod_pt(1.0)[:2]
    s += star5(tx, ty - 2, 8, 3.6, GOLD2, 2.5)
    return RHAND(s)

def rod_mask():
    return RHAND(P(rod_poly(0.2, 1.0, 6.5 - 3.7 * 0.2, 2.8), "#ffffff", 0))

def rod_glow():
    tx, ty = rod_pt(1.0)[:2]
    x, y, nx, ny = rod_pt(0.27)
    return RHAND(blur(CI(tx, ty - 2, 11, GOLD2, 0), 4) + blur(CI(x - nx * 13, y - ny * 13, 8, GOLD2, 0), 3))

LINE = 64
def lure(x, y, a):
    """a little golden fish lure hanging nose up at (x, y), swung a degrees"""
    s = blur('<circle cx="%.1f" cy="%.1f" r="11" fill="%s" opacity=".7"/>' % (x, y + 4, GOLD2), 5)
    f = P("M 0 -12 C 8 -10 9 4 0 12 C -9 4 -8 -10 0 -12 Z", GOLD, 3)
    f += P("M 0 10 L 7 20 L 0 17 L -7 20 Z", GOLD, 2.5)
    f += LN("M -4 -4 Q 0 -1 4 -4 M -4 2 Q 0 5 4 2", GOLDD, 1.6) + GEM(0, -6, 2.6, "#e0445a")
    f += LN("M 0 20 L 0 26 Q 0 32 5 30 L 4 26", INK, 2)
    s += tr(f, x, y, 1.35, a)
    return s

def lure_frame(k):
    tip = to_body(*rod_pt(1.0)[:2])
    tx, ty = tip[0], tip[1] - 2
    a = (-11, 0, 11, 0)[k]
    lx, ly = tx + LINE * math.sin(math.radians(-a)), ty + LINE * math.cos(math.radians(a))
    s = LN("M %.1f %.1f L %.1f %.1f" % (tx, ty, lx, ly - 12), "#fff8e0", 1.6)
    bx, by = tx + (lx - tx) * 0.42, ty + (ly - ty) * 0.42
    s += CI(bx, by, 4.5, "#ffffff", 2.5) + P("M %.1f %.1f A 4.5 4.5 0 0 1 %.1f %.1f Z" % (bx - 4.5, by, bx + 4.5, by), "#e8442e", 0)
    s += lure(lx, ly, a)
    return s

# ---------------------------------------------------------------- aura: bubbles, wishes, little Pinchys
def ripples(k):
    s = ""
    for i in range(3):
        f = (i / 3.0 + k / 12.0) % 1
        rx = 24 + 96 * f
        op = (1 - f) * 0.9
        s += '<ellipse cx="128" cy="214" rx="%.1f" ry="%.1f" fill="none" stroke="%s" stroke-width="%.1f" opacity="%.2f"/>' % (rx, rx * 0.2, SEA2, 4 - 2 * f, op)
    s = blur('<ellipse cx="128" cy="214" rx="90" ry="16" fill="%s" opacity=".5"/>' % SEA, 6) + s
    return s

def pinchy_bubble():
    b = CI(0, 0, 14, "#d8f6ff", 2.5)
    b = b.replace('fill="#d8f6ff"', 'fill="#d8f6ff" fill-opacity=".45"')
    lob = EL(0, 3, 5, 6.5, RED, 2)
    for sx in (-1, 1):
        lob += LN("M %d 0 L %d -5" % (sx * 3, sx * 7), INK, 2) + EL(sx * 8, -7, 3.2, 3.8, RED, 2, sx * 25)
        lob += CI(sx * 2, -5, 1.6, INK, 0)
    lob += LN("M -2 5 Q 0 6.5 2 5", INK, 1.2)
    b += lob + '<path d="M -8 -5 Q -6 -10 -1 -11" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>'
    return sprite(b)

def wish_star():
    s = blur(CI(0, 0, 8, GOLD2, 0), 3) + star5(0, 0, 9, 4, GOLD2, 2) + '<circle cx="-2" cy="-3" r="1.6" fill="#fff"/>'
    return sprite(s)

def frames(n, fn, name="fl"): return {"%s%d" % (name, k + 1): fn(k) for k in range(n)}

HEAD_C = H(128, 60)
SET = {
    "key": "pinchy", "name": "Pinchy's Wish", "zone": None, "lua": "PinchysWish", "file": "pinchys_wish",
    "prof": "fishing", "spec": None, "title": "Angler of Legend",
    "about": "Pinchy's Wish: the Fishing long-chase set (Mr. Pinchy the magic lobster, sea shells and wishes), crafted by Fishing.",
    "preview_fur": "fur_ginger",
    "pieces": [
        {"id": "set_pinchy_head", "slot": "head", "kind": "head", "art": "pinchy_head", "name": "Mr. Pinchy's Snapping Cap", "rarity": 5,
         "icon": "INV_Misc_Fish_35", "word": "hat",
         "svg": lobster_hat(), "layers": dict(frames(4, hat_fingers, "cl"), glow=hat_glow()),
         "anim": [
             {"kind": "flip", "keys": [K("pinchy_head", "cl%d" % i) for i in range(1, 5)], "fps": 5},
             {"kind": "pulse", "key": K("pinchy_head", "glow"), "a": [0.3, 1.0], "speed": 2.6, "blend": "ADD"},
             {"kind": "glint", "sprite": "t_sparkle", "n": 3, "spots": [box(H(128, 84), 24, 14), box(H(34, 10), 24, 20), box(H(222, 10), 24, 20)],
              "life": 0.8, "size": [16, 26], "gap": [0.3, 1.1], "color": GOLD3, "at": "front"},
             {"kind": "particles", "sprite": "t_bubble", "n": 3, "box": box(H(128, 0), 70, 14), "vx": [-8, 8], "vy": [-45, -25], "life": [1.4, 2.2],
              "size": [9, 15], "sway": 6, "color": [0.8, 0.97, 1.0], "alpha": 0.85, "at": "front"},
         ]},
        {"id": "set_pinchy_cape", "slot": "back", "kind": "back", "art": "pinchy_cape", "name": "Tidecaller's Net Mantle", "rarity": 4,
         "icon": "INV_Misc_Cape_16", "word": "cape",
         "svg": cape(), "layers": {"mask": cape_mask(), "glow": cape_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_swirl", "mask": K("pinchy_cape", "mask"), "scale": 110, "vx": 12, "vy": -22, "color": AQUA3, "blend": "ADD", "alpha": 0.4},
             {"kind": "pulse", "key": K("pinchy_cape", "glow"), "a": [0.2, 1.0], "speed": 2.2, "blend": "ADD"},
             {"kind": "glint", "sprite": "t_sparkle", "n": 2, "spots": [box(B(46, 166), 18, 40), box(B(210, 166), 18, 40)],
              "life": 0.8, "size": [14, 22], "gap": [0.5, 1.4], "color": GOLD3, "at": "front"},
             {"kind": "particles", "sprite": "t_bubble", "n": 3, "box": [44, 300, 110, 440], "vx": [-12, 2], "vy": [-55, -30], "life": [1.4, 2.2],
              "size": [9, 16], "sway": 6, "color": [0.8, 0.97, 1.0], "alpha": 0.85, "at": "behind"},
             {"kind": "particles", "sprite": "t_bubble", "n": 3, "box": [402, 300, 468, 440], "vx": [-2, 12], "vy": [-55, -30], "life": [1.4, 2.2],
              "size": [9, 16], "sway": 6, "color": [0.8, 0.97, 1.0], "alpha": 0.85, "at": "behind"},
         ]},
        {"id": "set_pinchy_weapon", "slot": "main", "kind": "weapon", "art": "pinchy_weapon", "name": "Wishgold Angler's Rod", "rarity": 4,
         "icon": "INV_Fishingpole_02", "word": "fishing pole",
         "svg": rod(), "layers": dict(frames(4, lure_frame), mask=rod_mask(), glow=rod_glow()),
         "anim": [
             {"kind": "flip", "keys": [K("pinchy_weapon", "fl%d" % i) for i in range(1, 5)], "fps": 4},
             {"kind": "scroll", "sprite": "a_shine", "mask": K("pinchy_weapon", "mask"), "scale": 120, "vx": 0, "vy": -60, "color": [1.0, 0.95, 0.7], "blend": "ADD", "alpha": 0.9},
             {"kind": "pulse", "key": K("pinchy_weapon", "glow"), "a": [0.3, 1.0], "speed": 3.0, "blend": "ADD"},
             {"kind": "glint", "sprite": "t_sparkle", "n": 2, "spots": [box(B(226, 104), 22, 18)], "life": 0.7, "size": [14, 22], "gap": [0.3, 0.9], "color": GOLD3, "at": "front"},
             {"kind": "particles", "sprite": "a_spark", "n": 4, "box": box(B(226, 108), 18, 10), "vx": [-10, 10], "vy": [-30, 20], "life": [0.8, 1.3],
              "size": [8, 13], "color": [1.0, 0.92, 0.5], "color2": [1.0, 0.7, 0.2], "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_pinchy_aura", "slot": "effect", "kind": "effect", "art": "pinchy_aura", "name": "Pinchy's Last Wish", "rarity": 5,
         "icon": "Spell_Frost_SummonWaterElemental", "word": "aura", "glow": (0.35, 0.85, 1.0),
         "fx": {"layer": "back", "anim": "float"},
         "layers": dict(frames(4, ripples), pinchy=pinchy_bubble(), wish=wish_star()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [0.3, 0.8, 1.0], "a": [0.25, 0.55], "speed": 1.6, "blend": "ADD", "at": "behind"},
             {"kind": "flip", "keys": [K("pinchy_aura", "fl%d" % i) for i in range(1, 5)], "fps": 6, "blend": "ADD", "at": "behind"},
             {"kind": "particles", "sprite": "t_bubble", "n": 7, "box": [90, 300, 422, 470], "vx": [-10, 10], "vy": [-80, -45], "life": [1.6, 2.6],
              "size": [10, 20], "sway": 10, "color": [0.8, 0.97, 1.0], "alpha": 0.9, "at": "front"},
             {"kind": "particles", "sprite": "k_pinchy_aura_pinchy", "n": 2, "box": [110, 330, 402, 460], "vx": [-8, 8], "vy": [-50, -32], "life": [2.4, 3.2],
              "size": [36, 46], "sway": 12, "at": "front"},
             {"kind": "particles", "sprite": "k_pinchy_aura_wish", "n": 4, "box": [70, 160, 442, 460], "vx": [-6, 6], "vy": [-40, -20], "life": [1.8, 2.8],
              "size": [14, 22], "spin": [-1.2, 1.2], "sway": 8, "at": "behind"},
             {"kind": "glint", "sprite": "t_sparkle", "n": 4, "spots": [[60, 120, 160, 420], [352, 120, 452, 420], [150, 40, 362, 120]],
              "life": 0.9, "size": [18, 30], "gap": [0.2, 0.9], "color": GOLD3, "at": "front"},
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
