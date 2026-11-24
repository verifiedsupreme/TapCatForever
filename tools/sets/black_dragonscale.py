"""Black Dragonscale set (1.7.0): a leatherworking long chase (Dragonscale). Overlapping black dragon
scales with deep red rims that smoulder like coals, a horned black-dragon skull helm with burning eye
sockets, scale pauldrons with ivory dorsal spines, a jerkin with a living dragon eye set in bone talons,
folded black-dragon wings as the cape, a serrated dragon-tooth blade and an aura of rising embers over a
smouldering red glow. Crafted over months; the full set gives the title Dragonscale Stalker.
  python3 tools/sets/black_dragonscale.py            -> Art/v/k_blackscale_*.tga, Art/blackscale_*.tga, Sets/BlackDragonscale.lua
  python3 tools/set_preview.py tools/sets/black_dragonscale.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: black dragon scale, deep red rims, ember light, old ivory
BLK, BLK2, BLK3 = "#1c171b", "#2e2529", "#4a3b41"
SKULL, SKULL2 = "#3a3034", "#56484d"
RED, RED2, RED3 = "#7a1220", "#c0262e", "#ff5236"
EMB, EMBC = "#ffa640", "#ffe2a0"
BONE, BONE2, BONED = "#efe5cc", "#cfc1a0", "#8f8268"
MEMB, MEMB2, MEMBV = "#3e0c16", "#58141f", "#1e0509"
LEATH = "#5e1a22"
EMBERC = [1.0, 0.55, 0.2]
REDC = [1.0, 0.22, 0.12]

def frames(n, fn, seed=1700):
    return {"fl%d" % (k + 1): fn(random.Random(seed + k), k) for k in range(n)}

# a blur whose region is the whole canvas, so a glow is never cut off into a box
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

def pts_d(pts, close=False):
    return "M " + " L ".join("%.1f %.1f" % p for p in pts) + (" Z" if close else "")

def horn(b0, c1, c2, tip, c3, c4, b1, col=BONE, tipcol=BLK2, rings=5, ink=4.5):
    """a curved horn or spine: outer curve b0 -> tip, inner curve tip -> b1, ring ridges and a dark tip"""
    d = "M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f Z" % (b0 + c1 + c2 + tip + c3 + c4 + b1)
    s = P(d, col, 0)
    tt = 0.68
    poly = [cub(b0, c1, c2, tip, tt + (1 - tt) * i / 8.0) for i in range(9)] + [cub(tip, c3, c4, b1, (1 - tt) * i / 8.0) for i in range(1, 9)]
    s += P(pts_d(poly, True), tipcol, 0)
    for k in range(1, rings + 1):
        t = 0.1 + 0.55 * k / float(rings + 1)
        a, b = cub(b0, c1, c2, tip, t), cub(tip, c3, c4, b1, 1 - t)
        s += LN("M %.1f %.1f Q %.1f %.1f %.1f %.1f" % (a[0], a[1], (a[0] + b[0]) / 2 + 2, (a[1] + b[1]) / 2 + 3, b[0], b[1]), BONED, 2)
    # a shine along the outer curve
    sh = [cub(b0, c1, c2, tip, 0.12 + 0.5 * i / 6.0) for i in range(7)]
    sh = [(x + (b1[0] - b0[0]) * 0.18, y + (b1[1] - b0[1]) * 0.18) for x, y in sh]
    s += LN(pts_d(sh), "#ffffff", 2.2, .55)
    return s + P(d, "none", ink)

def dscales(x0, y0, x1, y1, r, fill=BLK2, rim="#a31c28", clip=None, rims_only=False, rimw=2.0):
    """rows of pointed dragon scales filling a box; upper rows overlap lower ones, every scale has a red rim"""
    rows = []
    y, row = y0, 0
    while y <= y1:
        rows.append((y, row)); y += r * 1.0; row += 1
    s = ""
    for y, row in reversed(rows):
        x = x0 + (r if row % 2 else 0)
        while x <= x1 + r:
            rd = "M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f" % (x - r * 0.72, y + r * 0.55, x - r * 0.5, y + r * 1.15, x, y + r * 1.36,
                                                                           x + r * 0.5, y + r * 1.15, x + r * 0.72, y + r * 0.55)
            if rims_only:
                s += LN(rd, "#ffffff", rimw)
            else:
                d = "M %.1f %.1f L %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f L %.1f %.1f Z" % (
                    x - r, y, x - r, y + r * 0.5, x - r * 0.7, y + r * 1.3, x, y + r * 1.62, x + r * 0.7, y + r * 1.3, x + r, y + r * 0.5, x + r, y)
                s += '<path d="%s" fill="%s" stroke="%s" stroke-width="1.8" stroke-linejoin="round"/>' % (d, fill, INK)
                s += LN(rd, rim, rimw)
                s += LN("M %.1f %.1f Q %.1f %.1f %.1f %.1f" % (x - r * 0.6, y + r * 0.35, x - r * 0.35, y + r * 0.15, x - r * 0.05, y + r * 0.2), BLK3, 1.6)
            x += 2 * r
    if clip: s = '<g clip-path="url(#%s)">%s</g>' % (clip, s)
    return s

def ribbon(pts, w0, w1, col, op=1.0):
    """a tapering filled ribbon along a polyline, w0 wide at the start, w1 at the end"""
    L, R = [], []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]; b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        w = (w0 + (w1 - w0) * i / float(n - 1)) / 2.0
        L.append((x + nx * w, y + ny * w)); R.append((x - nx * w, y - ny * w))
    return '<path d="%s" fill="%s" opacity="%s"/>' % (pts_d(L + R[::-1], True), col, op)

def smooth(pts, k=3):
    """Catmull-Rom style resampling of a polyline, k points per segment"""
    out = []
    P_ = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        for j in range(k):
            t = j / float(k)
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2 + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    out.append(pts[-1])
    return out

def flame(x, y, h, w, lean=0.0, ink=3.0, cols=(RED, RED2, RED3, EMB)):
    """a small sticker flame standing on (x, y), in smouldering dragonfire colours"""
    out = ""
    for k, (s, col) in enumerate(zip((1.0, 0.72, 0.46, 0.24), cols)):
        hh, ww, tx = h * s, w * s, x + lean * s
        by = y - h * (1 - s) * 0.18
        d = ("M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z"
             % (x - ww, by, x - ww * 1.15, by - hh * 0.45, tx - ww * 0.45, by - hh * 0.72, tx, by - hh,
                tx + ww * 0.55, by - hh * 0.66, x + ww * 1.15, by - hh * 0.42, x + ww, by, x, by + ww * 0.95, x - ww, by))
        out += P(d, col, ink if k == 0 else 0)
    return out

# ---------------------------------------------------------------- helm: horned black-dragon skull (head space)
DOME = "M 40 100 C 30 42 64 8 128 6 C 192 8 226 42 216 100 Z"
EYES = [(94, 60), (162, 60)]
CRACKS = ["M 52 88 L 60 76 L 56 66 L 64 54", "M 204 88 L 196 76 L 200 66 L 192 54",
          "M 128 12 L 122 22 L 130 30 L 125 40", "M 78 30 L 88 36 L 86 46", "M 178 30 L 168 36 L 170 46"]

def big_horn():
    return horn((58, 66), (30, 58), (10, 34), (8, -6), (24, 16), (50, 32), (92, 38), rings=6)

def cheek_horn():
    return horn((52, 76), (36, 80), (20, 88), (6, 108), (22, 100), (36, 98), (54, 94), rings=2, ink=4)

def helm():
    s = big_horn() + mirror(big_horn(), 128) + cheek_horn() + mirror(cheek_horn(), 128)
    # a crest of small spines along the top
    for x, tx, ty in ((106, 98, -2), (128, 128, -8), (150, 158, -2)):
        s += P("M %d 16 L %d %d L %d 16 Z" % (x - 9, tx, ty, x + 9), BONE2, 3.5) + P("M %d 8 L %d %d L %d 8 Z" % (x - 4, tx, ty, x + 4), BLK2, 0)
    s += P(DOME, SKULL, 5)
    s += '<clipPath id="bdsdome"><path d="%s"/></clipPath>' % DOME
    s += dscales(30, 4, 226, 70, 9, fill=SKULL, rim=RED, clip="bdsdome", rimw=1.8)
    # the bare skull face plate over the brow and snout, the scaled hood behind it
    s += P("M 58 98 Q 52 56 82 38 Q 128 22 174 38 Q 204 56 198 98 Z", SKULL2, 4.5)
    s += LN("M 70 50 Q 98 32 128 30", "#7a6a70", 3, .8)
    for d in CRACKS: s += LN(d, INK, 6) + LN(d, RED2, 2.6)
    # the skull face: brow ridges, deep sockets, the snout
    for sx in (-1, 1):
        ex, ey = EYES[0 if sx < 0 else 1]
        brow = "M %d %d Q %d %d %d %d L %d %d Q %d %d %d %d Z" % (128 + sx * 66, 60, 128 + sx * 44, 30, 128 + sx * 12, 42,
                                                                 128 + sx * 14, 50, 128 + sx * 42, 40, 128 + sx * 62, 66)
        sock = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (128 + sx * 58, 64, 128 + sx * 40, 42, 128 + sx * 16, 54,
                                                                       128 + sx * 20, 72, 128 + sx * 40, 74, 128 + sx * 54, 72, 128 + sx * 58, 64)
        s += P(sock, "#110a0c", 4) + P(brow, "#6e5e64", 4)
        s += EL(ex, ey + 2, 7, 5, RED2, 0) + EL(ex, ey + 2, 3, 2.4, EMBC, 0)
    snout = "M 112 96 Q 106 68 118 50 Q 128 44 138 50 Q 150 68 144 96 Z"
    s += P(snout, "#6e5e64", 4.5) + LN("M 128 52 L 128 70", "#8a7a80", 3)
    s += EL(119, 82, 4, 2.6, "#110a0c", 0, rot=-24) + EL(137, 82, 4, 2.6, "#110a0c", 0, rot=24)
    # the upper jaw and its fangs: the cat looks out from under them
    jaw = "M 46 98 Q 128 84 210 98"
    s += LN(jaw, INK, 14) + LN(jaw, SKULL2, 9) + LN("M 52 95 Q 128 83 204 95", RED, 2)
    for i in range(10):
        x = 56 + i * 16
        y = 98 - 14 * (1 - ((x - 128) / 80.0) ** 2) + 4
        L = 15 if i in (2, 7) else (10 if i in (4, 5) else 7)
        s += P("M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" % (x - 4.5, y, x - 3, y + L * 0.6, x + (1 if x > 128 else -1), y + L,
                                                                           x + 3, y + L * 0.6, x + 4.5, y), BONE, 2.4)
    return HEAD(s)

def helm_eyes():
    s = ""
    for ex, ey in EYES:
        s += blur(EL(ex, ey + 2, 20, 13, RED3, 0)) + EL(ex, ey + 2, 8, 5.5, EMB, 0) + EL(ex, ey + 2, 3.5, 2.6, "#ffffff", 0)
    return HEAD(s)

def helm_cracks():
    return HEAD(blur("".join(LN(d, RED3, 7) for d in CRACKS)) + "".join(LN(d, EMBC, 2) for d in CRACKS))

def helm_trails(rnd, k):
    """burning wisps streaming up and out of the eye sockets, different every frame"""
    s = ""
    for sx in (-1, 1):
        ex, ey = EYES[0 if sx < 0 else 1]
        pts = [(ex + sx * 8, ey - 2)]
        x, y = pts[0]
        for i in range(4):
            x += sx * (10 + rnd.uniform(0, 7)); y -= 13 + rnd.uniform(0, 6)
            pts.append((x + rnd.uniform(-5, 5), y))
        pts = smooth(pts, 4)
        s += blur(ribbon(pts, 14, 3, RED2, .8)) + ribbon(pts, 9, 1, RED3, .9) + ribbon(pts, 4, 0.5, EMBC, .9)
    return HEAD(s)

# ---------------------------------------------------------------- shoulders (body space, both sides)
def pauldron_dome():
    cx, cy = SH_C
    return "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 32, cy + 10, cx + 28, cy - 26, cx - 6, cy - 24,
        cx - 40, cy - 22, cx - 42, cy + 12, cx - 4, cy + 26, cx + 32, cy + 10)

SPINES = [((-30, -10), (-48, -20), (-60, -34), (-66, -50), (-52, -40), (-36, -30), (-18, -18)),
          ((-14, -18), (-26, -34), (-30, -52), (-26, -70), (-18, -54), (-8, -38), (0, -22)),
          ((4, -22), (2, -36), (6, -50), (14, -62), (14, -48), (16, -34), (18, -20))]

def pauldron():
    cx, cy = SH_C
    s = ""
    for sp in SPINES:
        q = [(cx + x, cy + y) for x, y in sp]
        s += horn(*q, rings=2, ink=3.5)
    dome = pauldron_dome()
    s += P(dome, BLK, 5)
    s += '<clipPath id="bdpaul"><path d="%s"/></clipPath>' % dome
    s += dscales(cx - 46, cy - 30, cx + 36, cy + 22, 8, clip="bdpaul")
    s += P(dome, "none", 5)
    # red leather hem with ivory talon studs
    hem = "M %d %d Q %d %d %d %d" % (cx - 40, cy + 10, cx - 6, cy + 26, cx + 30, cy + 8)
    s += LN(hem, INK, 10) + LN(hem, LEATH, 6)
    for t in (0.12, 0.36, 0.62, 0.86):
        x, y = cub((cx - 40, cy + 10), (cx - 28, cy + 21), (cx + 18, cy + 20), (cx + 30, cy + 8), t)
        s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x - 4, y + 1, x - 1, y + 11, x + 4, y + 1), BONE, 2.2)
    # an ember gem held by two little ivory claws
    gx, gy = cx - 6, cy - 2
    for sx in (-1, 1):
        s += P("M %d %d Q %d %d %d %d L %d %d Z" % (gx + sx * 8, gy + 8, gx + sx * 16, gy - 2, gx + sx * 6, gy - 11, gx + sx * 6, gy + 2), BONE, 2.5)
    s += CI(gx, gy, 7.5, RED2, 3) + CI(gx, gy, 3.5, EMB, 0) + '<circle cx="%.1f" cy="%.1f" r="1.8" fill="#fff"/>' % (gx - 3, gy - 3)
    return BOTH(s)

def pauldron_rims():
    cx, cy = SH_C
    return BOTH('<clipPath id="bdpaulm"><path d="%s"/></clipPath>' % pauldron_dome()
                + dscales(cx - 46, cy - 30, cx + 36, cy + 22, 8, clip="bdpaulm", rims_only=True))

def pauldron_glow():
    cx, cy = SH_C
    return BOTH(blur(CI(cx - 6, cy - 2, 13, RED3, 0)) + CI(cx - 6, cy - 2, 4.5, EMBC, 0))

# ---------------------------------------------------------------- chest: scale jerkin with a dragon eye (body space)
EYE_C = (128, 154)
def chest():
    s = P(BODY_OUT, BLK, 5)
    s += dscales(56, 110, 204, 214, 9, clip="chestclip")
    s += P(BODY_OUT, "none", 5)
    # red leather straps from the shoulders to the eye plate
    for sx in (-1, 1):
        d = "M %d 120 Q %d 132 %d 146" % (128 + sx * 46, 128 + sx * 30, 128 + sx * 14)
        s += LN(d, INK, 13) + LN(d, LEATH, 8) + LN(d, RED, 1.5)
        s += CI(128 + sx * 36, 128, 3, BONE2, 2)
    ex, ey = EYE_C
    # the dark plate and the four ivory talons holding the eye
    s += P("M %d %d L %d %d L %d %d L %d %d Z" % (ex, ey - 26, ex + 26, ey, ex, ey + 26, ex - 26, ey), BLK2, 4.5)
    for a in (-135, -45, 45, 135):
        r0, r1 = 13, 27
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        bx, by = ex + ca * r0, ey + sa * r0
        tx, ty = ex + ca * r1, ey + sa * r1
        px, py = -sa, ca
        d = "M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" % (bx - px * 5, by - py * 5, tx + px * 6, ty + py * 6, bx + px * 7 - ca * 4, by + py * 7 - sa * 4,
                                                                         tx - px * 2, ty - py * 2, bx - px * 5, by - py * 5)
        s += P(d, BONE, 2.5)
    s += EL(ex, ey, 15, 12, "#e8a028", 4) + EL(ex, ey, 11, 8.5, "#ff6a20", 0) + EL(ex, ey, 2.6, 9, INK, 0) + CI(ex - 6, ey - 5, 2.2, "#ffffff", 0)
    # belt with tooth studs
    s += RC(60, 198, 136, 14, LEATH, 4, 4)
    for x in (72, 90, 108, 148, 166, 184):
        s += P("M %d 200 L %d 210 L %d 200 Z" % (x - 3.5, x, x + 3.5), BONE, 2)
    s += RC(116, 195, 24, 19, BLK2, 4, 4) + GEM(128, 204.5, 4.5, RED2)
    return s

def chest_rims():
    return dscales(56, 110, 204, 214, 9, clip="chestclip", rims_only=True)

def chest_glow():
    ex, ey = EYE_C
    return blur(EL(ex, ey, 26, 21, RED3, 0)) + EL(ex, ey, 11, 8.5, EMB, 0)

def chest_pupil(rnd, k):
    """the eye's slit pupil widening and narrowing"""
    ex, ey = EYE_C
    w = (2.4, 4.4, 6.5)[k]
    return EL(ex, ey, 11, 8.5, ("#ff6a20", "#ff7a28", "#ff8a30")[k], 0) + EL(ex, ey, w, 9, INK, 0) + CI(ex - 6, ey - 5, 2.2, "#ffffff", 0)

# ---------------------------------------------------------------- cape: folded black-dragon wings (side drapes)
W_ROOT, W_APEX = (88, 112), (22, 88)
W_TIPS = [(6, 168), (22, 206), (50, 214)]
def wing_membrane():
    (x1, y1), (x2, y2), (x3, y3) = W_TIPS
    return ("M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d L 66 206 Q 70 160 %d %d Z"
            % (W_ROOT[0], W_ROOT[1], 52, 80, W_APEX[0], W_APEX[1], 2, 124, x1, y1, 26, 176, x2, y2, 42, 196, x3, y3, W_ROOT[0] + 10, W_ROOT[1] + 12))

def wing_veins():
    out = []
    for (tx, ty), (ux, uy) in zip(W_TIPS, W_TIPS[1:] + [(70, 200)]):
        mx, my = (tx + ux) / 2.0, (ty + uy) / 2.0
        out.append("M %d %d Q %.1f %.1f %.1f %.1f" % (W_APEX[0] + 6, W_APEX[1] + 10, (W_APEX[0] + mx) / 2 + 6, (W_APEX[1] + my) / 2, mx, my - 6))
    return out

def wing():
    s = P(wing_membrane(), MEMB, 5)
    s += P("M 34 104 Q 20 140 18 170 Q 30 160 44 186 Q 48 168 60 194 Q 64 150 84 122 Z", MEMB2, 0)
    for d in wing_veins(): s += LN(d, MEMBV, 2.4)
    # finger bones fanning from the wrist
    for (tx, ty), bend in zip(W_TIPS, (-14, -6, 4)):
        d = "M %d %d Q %.1f %.1f %d %d" % (W_APEX[0], W_APEX[1], (W_APEX[0] + tx) / 2.0 + bend, (W_APEX[1] + ty) / 2.0, tx, ty)
        s += LN(d, INK, 8) + LN(d, "#66565e", 4) + LN(d, "#8a7a82", 1.2)
        s += P("M %d %d L %d %d L %d %d Z" % (tx - 4, ty - 4, tx - 1, ty + 9, tx + 4, ty - 2), BONE, 2.2)
    # the arm bone along the leading edge and the thumb claw
    arm = "M %d %d Q %d %d %d %d" % (W_ROOT[0], W_ROOT[1], 52, 82, W_APEX[0], W_APEX[1])
    s += LN(arm, INK, 12) + LN(arm, "#55464d", 7) + LN("M 80 104 Q 54 86 30 88", "#8a7a82", 2)
    s += CI(W_APEX[0], W_APEX[1], 6.5, "#55464d", 3.5)
    s += P("M %d %d Q %d %d %d %d Q %d %d %d %d Z" % (W_APEX[0] - 4, W_APEX[1] - 3, W_APEX[0] - 10, W_APEX[1] - 14, W_APEX[0] - 2, W_APEX[1] - 24,
                                                      W_APEX[0] - 2, W_APEX[1] - 12, W_APEX[0] + 5, W_APEX[1] - 4), BONE, 2.5)
    # red glowing trailing edge
    (x1, y1), (x2, y2), (x3, y3) = W_TIPS
    s += LN("M %d %d Q 26 176 %d %d Q 42 196 %d %d" % (x1 + 3, y1, x2, y2 - 3, x3, y3 - 3), RED2, 2.2)
    return s

def cape():
    return wing() + mirror(wing(), 128)

def cape_mask():
    m = P(wing_membrane(), "#ffffff", 0)
    return m + mirror(m, 128)

def cape_veins():
    s = "".join(LN(d, RED3, 2.4) for d in wing_veins())
    (x1, y1), (x2, y2), (x3, y3) = W_TIPS
    s += LN("M %d %d Q 26 176 %d %d Q 42 196 %d %d" % (x1 + 3, y1, x2, y2 - 3, x3, y3 - 3), EMB, 2.6)
    s = blur(s) + s
    return s + mirror(s, 128)

# ---------------------------------------------------------------- weapon: serrated dragon-tooth blade (right paw)
B0, B1, B2, BT = (-14, -36), (-22, -92), (-14, -150), (6, -200)
C1, C2, C3 = (18, -150), (20, -92), (14, -36)
BLADE = "M %d %d C %d %d %d %d %d %d C %d %d %d %d %d %d Z" % (B0 + B1 + B2 + BT + C1 + C2 + C3)
RUNES = [(0, -58), (0, -84), (1, -110), (2, -136), (3, -160)]
def blade_teeth():
    s = ""
    for i in range(7):
        t = 0.12 + i * 0.1
        x, y = cub(B0, B1, B2, BT, t)
        s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x + 1, y + 7, x - 9, y + 2, x + 1, y - 5), BONE, 3)
    return s

RUNE_D = ["M 0 6 L 0 -6 M 0 0 L -4 -5 M 0 0 L 4 -5",          # three-claw rune
          "M 0 -6 L 4 0 L 0 6 L -4 0 Z",                       # dragon eye diamond
          "M -4 -5 L 2 -1 L -2 2 L 4 6",                       # flame zigzag
          "M -4 -6 L 0 -2 L 4 -6 M 0 -2 L 0 6"]                # fork
def rune(x, y, col, w, i=0):
    return '<g transform="translate(%.1f %.1f)">%s</g>' % (x, y, LN(RUNE_D[i % len(RUNE_D)], col, w))

def blade():
    s = blade_teeth()
    s += P(BLADE, BONE, 5)
    s += P("M 2 -40 C 8 -92 8 -150 6 -194 C 14 -150 16 -92 10 -40 Z", BONE2, 0)
    s += LN("M -8 -44 C -12 -92 -6 -146 4 -188", "#ffffff", 2.5, .6)
    s += LN("M 0 -44 C -1 -92 1 -140 4 -172", BONED, 6)
    for i, (x, y) in enumerate(RUNES): s += rune(x, y, RED2, 2.2, i)
    # claw crossguard of black scale
    g = "M -32 -30 Q -22 -46 0 -40 Q 22 -46 32 -30 Q 22 -22 0 -26 Q -22 -22 -32 -30 Z"
    for sx in (-1, 1):
        s += P("M %d -36 Q %d -52 %d -66 Q %d -52 %d -38 Z" % (sx * 28, sx * 30, sx * 18, sx * 22, sx * 16), BONE, 3)
    s += P(g, BLK2, 4.5) + LN("M -24 -32 Q 0 -40 24 -32", BLK3, 2)
    s += GEM(0, -33, 6, RED2)
    # grip and pommel
    s += RC(-5.5, -26, 11, 52, LEATH, 4, 4)
    for y in (-16, -4, 8, 20): s += LN("M -5 %d L 5 %d" % (y, y - 4), BLK, 2.5)
    s += CI(0, 30, 7.5, BLK2, 4) + P("M -4 36 L 0 50 L 4 36 Z", BONE, 2.5)
    return RHAND(s)

def blade_mask():
    return RHAND(P(BLADE, "#ffffff", 0))

def blade_runes():
    s = "".join(rune(x, y, RED3, 5, i) for i, (x, y) in enumerate(RUNES))
    return RHAND(blur(s) + "".join(rune(x, y, EMBC, 1.8, i) for i, (x, y) in enumerate(RUNES)) + blur(CI(0, -33, 9, RED3, 0)))

def blade_flames(rnd, k):
    s = ""
    for i in range(1, 7, 2):
        t = 0.14 + i * 0.1 + rnd.uniform(-0.03, 0.03)
        x, y = cub(B0, B1, B2, BT, t)
        s += flame(x - 6, y + 4, 14 * (0.75 + rnd.random() * 0.5), 4.5, lean=-6 + rnd.uniform(-4, 4), ink=2.5)
    x, y = BT
    s += flame(x, y + 10, 18 * (0.8 + rnd.random() * 0.4), 5, lean=rnd.uniform(-5, 5), ink=2.5)
    return RHAND(s)

# ---------------------------------------------------------------- aura: smouldering ground and rising embers
def ground(rnd, k):
    s = blur('<ellipse cx="128" cy="212" rx="112" ry="16" fill="%s" opacity=".75"/>' % RED2)
    s += blur('<ellipse cx="128" cy="212" rx="70" ry="9" fill="%s" opacity=".7"/>' % EMB)
    for i in range(7):
        a = rnd.uniform(0, math.pi * 2)
        x0, y0 = 128 + math.cos(a) * 60, 212 + math.sin(a) * 8
        pts = [(x0, y0)]
        for j in range(3):
            x0 += math.cos(a) * rnd.uniform(12, 20) + rnd.uniform(-4, 4); y0 += math.sin(a) * 3 + rnd.uniform(-2, 2)
            pts.append((x0, y0))
        d = pts_d(pts)
        s += LN(d, RED3, 3.2, .9) + LN(d, EMBC, 1.2)
    for i in range(4):
        x = rnd.choice((rnd.uniform(16, 60), rnd.uniform(196, 240)))
        s += flame(x, 214, rnd.uniform(14, 24), 5, lean=rnd.uniform(-6, 6), ink=2.5)
    return s

def scale_sprite():
    d = "M -8 -9 L -8 -2 Q -6 6 0 10 Q 6 6 8 -2 L 8 -9 Z"
    return sprite(P(d, BLK2, 2.2) + LN("M -6 -1 Q -4 5 0 7 Q 4 5 6 -1", RED3, 2) + LN("M -5 -6 L -1 -7", BLK3, 1.5), S=24)

FIREC = (0.8, 0.15, 0.1)
EMBERS = {"kind": "particles", "sprite": "a_ember", "blend": "ADD", "color": [1.0, 0.62, 0.25], "color2": [0.9, 0.12, 0.06]}
SPARK = {"kind": "glint", "sprite": "a_spark", "blend": "ADD", "color": [1.0, 0.6, 0.3], "at": "front"}

def A(part): return "blackscale_" + part

SET = {
    "key": "blackscale", "name": "Black Dragonscale", "zone": None, "lua": "BlackDragonscale", "file": "black_dragonscale",
    "prof": "leatherworking", "spec": "dragonscale", "title": "Dragonscale Stalker",
    "about": "Black Dragonscale set: a leatherworking (Dragonscale) long chase, black dragon scale smouldering with red embers.",
    "preview_fur": "fur_cream",
    "pieces": [
        {"id": "set_blackscale_head", "slot": "head", "kind": "head", "art": A("head"), "name": "Horned Skull of the Black Brood", "rarity": 5,
         "icon": "INV_Misc_Head_Dragon_Black", "word": "helm",
         "svg": helm(), "layers": dict(frames(4, helm_trails), eyes=helm_eyes(), cracks=helm_cracks()),
         "anim": [
             {"kind": "pulse", "key": K(A("head"), "cracks"), "a": [0.15, 0.9], "speed": 1.7, "blend": "ADD"},
             {"kind": "flip", "keys": [K(A("head"), "fl%d" % i) for i in range(1, 5)], "fps": 8, "blend": "ADD"},
             {"kind": "pulse", "key": K(A("head"), "eyes"), "a": [0.45, 1.0], "speed": 3.0, "blend": "ADD", "flicker": True},
             dict(EMBERS, n=5, box=[60, 20, 452, 110], vx=[-12, 12], vy=[-70, -40], life=[0.9, 1.5], size=[10, 16], sway=6, at="front"),
         ]},
        {"id": "set_blackscale_shoulders", "slot": "shoulder", "kind": "shoulder", "art": A("shoulders"), "name": "Emberrim Wyrmscale Spaulders", "rarity": 4,
         "icon": "INV_Shoulder_23", "word": "shoulders",
         "svg": pauldron(), "layers": {"rims": pauldron_rims(), "glow": pauldron_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_firetile", "mask": K(A("shoulders"), "rims"), "scale": 90, "vx": 8, "vy": -24, "color": [1.0, 0.5, 0.35], "blend": "ADD", "alpha": 0.45, "pulse": 1.7},
             {"kind": "pulse", "key": K(A("shoulders"), "glow"), "a": [0.2, 1.0], "speed": 2.4, "blend": "ADD", "flicker": True},
             dict(SPARK, n=2, spots=[[40, 130, 90, 180], [422, 130, 472, 180]], size=[14, 22], gap=[0.5, 1.4]),
         ]},
        {"id": "set_blackscale_chest", "slot": "chest", "kind": "chest", "art": A("chest"), "name": "Wyrmeye Dragonscale Jerkin", "rarity": 4,
         "icon": "INV_Chest_Leather_08", "word": "chest",
         "svg": chest(), "layers": dict(frames(3, chest_pupil), rims=chest_rims(), glow=chest_glow()),
         "anim": [
             {"kind": "scroll", "sprite": "a_firetile", "mask": K(A("chest"), "rims"), "scale": 110, "vx": 6, "vy": -20, "color": [1.0, 0.5, 0.35], "blend": "ADD", "alpha": 0.4, "pulse": 1.3},
             {"kind": "pulse", "key": K(A("chest"), "glow"), "a": [0.15, 0.85], "speed": 2.0, "blend": "ADD"},
             {"kind": "flip", "keys": [K(A("chest"), "fl%d" % i) for i in (1, 2, 3, 2)], "fps": 2},
         ]},
        {"id": "set_blackscale_cape", "slot": "back", "kind": "back", "art": A("cape"), "name": "Folded Wings of the Black Flight", "rarity": 4,
         "icon": "INV_Misc_Cape_20", "word": "cape",
         "svg": cape(), "layers": {"mask": cape_mask(), "veins": cape_veins()},
         "anim": [
             {"kind": "scroll", "sprite": "a_firetile", "mask": K(A("cape"), "mask"), "scale": 140, "vx": 4, "vy": -16, "color": [1.0, 0.35, 0.2], "blend": "ADD", "alpha": 0.3, "pulse": 1.1},
             {"kind": "pulse", "key": K(A("cape"), "veins"), "a": [0.1, 0.9], "speed": 1.6, "blend": "ADD"},
             dict(EMBERS, n=3, box=[10, 340, 120, 440], vx=[-10, 4], vy=[-40, -20], life=[1.2, 2.0], size=[9, 14], sway=6, at="behind"),
             dict(EMBERS, n=3, box=[392, 340, 502, 440], vx=[-4, 10], vy=[-40, -20], life=[1.2, 2.0], size=[9, 14], sway=6, at="behind"),
         ]},
        {"id": "set_blackscale_weapon", "slot": "main", "kind": "weapon", "art": A("weapon"), "name": "Serrated Wyrmtooth Blade", "rarity": 4,
         "icon": "INV_Sword_48", "word": "blade",
         "svg": blade(), "layers": dict(frames(3, blade_flames), mask=blade_mask(), runes=blade_runes()),
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K(A("weapon"), "mask"), "scale": 70, "vx": 18, "vy": -60, "color": [1.0, 0.75, 0.55], "blend": "ADD", "alpha": 0.4},
             {"kind": "pulse", "key": K(A("weapon"), "runes"), "a": [0.2, 1.0], "speed": 2.6, "blend": "ADD"},
             {"kind": "flip", "keys": [K(A("weapon"), "fl%d" % i) for i in range(1, 4)], "fps": 8},
             dict(EMBERS, n=4, box=[370, 40, 440, 300], vx=[-8, 8], vy=[-50, -25], life=[0.8, 1.3], size=[8, 13], sway=5, at="front"),
         ]},
        {"id": "set_blackscale_aura", "slot": "effect", "kind": "effect", "art": A("aura"), "name": "Smouldering Brood Embers", "rarity": 5,
         "icon": "Spell_Fire_Incinerate", "word": "aura", "glow": FIREC,
         "fx": {"layer": "back", "anim": "flicker"},
         "layers": dict(frames(4, ground), scale=scale_sprite()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [0.85, 0.1, 0.06], "a": [0.35, 0.75], "speed": 1.4, "blend": "ADD", "flicker": True, "at": "behind"},
             {"kind": "flip", "keys": [K(A("aura"), "fl%d" % i) for i in range(1, 5)], "fps": 6, "at": "behind"},
             {"kind": "particles", "sprite": "k_blackscale_aura_scale", "n": 5, "box": [60, 260, 452, 460], "vx": [-10, 10], "vy": [-50, -28],
              "life": [1.8, 2.8], "size": [12, 18], "spin": [-1.5, 1.5], "sway": 10, "at": "behind"},
             dict(EMBERS, n=8, box=[90, 300, 422, 470], vx=[-14, 14], vy=[-95, -55], life=[1.3, 2.2], size=[11, 20], sway=10, at="front"),
             dict(EMBERS, n=6, box=[40, 140, 472, 460], vx=[-10, 10], vy=[-70, -40], life=[1.6, 2.6], size=[10, 16], sway=8, at="behind"),
             {"kind": "particles", "sprite": "a_wisp", "n": 4, "box": [100, 320, 412, 460], "vx": [-8, 8], "vy": [-45, -25], "life": [1.8, 2.6],
              "size": [40, 60], "grow": 0.8, "color": [0.7, 0.12, 0.08], "blend": "ADD", "alpha": 0.55, "at": "behind"},
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
