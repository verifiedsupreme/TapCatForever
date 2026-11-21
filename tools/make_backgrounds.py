"""Cartoon Adventure backgrounds, one per zone, in the sticker style of the cat.
Flat colours, soft silhouettes in the distance, ink-outlined props up close, and a
floor band at the bottom where the cat and enemies stand.
usage: python3 tools/make_backgrounds.py <work_dir> [preview.png]  -> Art/v/bg_<key>.tga (512x256)
Also the fishing dock scene (bg_dock) used by the Fishing profession view.
"""
import math, os, random, subprocess, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from make_art import write_tga
W, Hh, FLOOR = 512, 256, 192
INK = "#3b2620"

def rect(x, y, w, h, c, op=1): return '<rect x="%s" y="%s" width="%s" height="%s" fill="%s" opacity="%s"/>' % (x, y, w, h, c, op)
def path(d, c, sw=0, op=1):
    st = ' stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"' % (INK, sw) if sw else ""
    return '<path d="%s" fill="%s"%s opacity="%s"/>' % (d, c, st, op)
def circ(x, y, r, c, sw=0, op=1):
    st = ' stroke="%s" stroke-width="%s"' % (INK, sw) if sw else ""
    return '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"%s opacity="%s"/>' % (x, y, r, c, st, op)
def ell(x, y, rx, ry, c, sw=0, op=1):
    st = ' stroke="%s" stroke-width="%s"' % (INK, sw) if sw else ""
    return '<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="%s"%s opacity="%s"/>' % (x, y, rx, ry, c, st, op)

# ---------------------------------------------------------------- pieces
def sky(*bands):
    """flat horizontal colour bands from the top"""
    s, y, h = "", 0, FLOOR / len(bands)
    for c in bands: s += rect(0, y, W, h + 1, c); y += h
    return s
def wave(y, amp, c, seed, n=6, sw=0, op=1):
    rnd = random.Random(seed); pts = [(0, y)]
    for k in range(1, n + 1): pts.append((W * k / n, y - rnd.uniform(0.2, 1) * amp))
    d = "M -10 %d L -10 %.1f" % (Hh, pts[0][1])
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]): d += " Q %.1f %.1f %.1f %.1f" % ((x0 + x1) / 2, min(y0, y1) - amp * 0.3, x1, y1)
    return path(d + " L %d %d Z" % (W + 10, Hh), c, sw, op)
def peaks(y, h, c, seed, n=5, op=1, snow=None):
    rnd = random.Random(seed); s = ""
    for k in range(n):
        x = -30 + k * (W + 60) / (n - 1) + rnd.uniform(-20, 20); ph = h * rnd.uniform(0.6, 1)
        s += path("M %.1f %d L %.1f %.1f L %.1f %d Z" % (x - 80, y, x, y - ph, x + 80, y), c, 0, op)
        if snow: s += path("M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x - 18, y - ph + 22, x, y - ph, x + 18, y - ph + 22, x, y - ph + 14), snow, 0, op)
    return s
def clouds(seed, n=4, c="#ffffff", op=0.9):
    rnd = random.Random(seed); s = ""
    for _ in range(n):
        x, y = rnd.uniform(20, W - 20), rnd.uniform(18, 70)
        for dx, dy, r in ((-16, 4, 12), (0, 0, 16), (18, 4, 12)): s += circ(x + dx, y + dy, r, c, 0, op)
    return s
def floor(c, top=None, line=True):
    s = rect(0, FLOOR, W, Hh - FLOOR, c)
    if top: s += rect(0, FLOOR, W, 6, top)
    if line: s += '<path d="M 0 %d L %d %d" stroke="%s" stroke-width="3"/>' % (FLOOR, W, FLOOR, INK)
    return s
def roundtree(x, y, r, leaf, trunk="#7a4a2a", sw=3):
    return rect(x - 5, y - 10, 10, 30, trunk).replace("/>", ' stroke="%s" stroke-width="%d"/>' % (INK, sw)) + circ(x, y - 18 - r * 0.6, r, leaf, sw) + circ(x - r * 0.35, y - 26 - r * 0.6, r * 0.35, "#ffffff", 0, 0.18)
def pine(x, y, h, leaf, trunk="#6a3f22", sw=3):
    w = h * 0.45
    return (rect(x - 4, y - 8, 8, 14, trunk) + path("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x - w, y - 6, x, y - h, x + w, y - 6), leaf, sw)
            + path("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x - w * 0.7, y - h * 0.45, x, y - h * 1.15, x + w * 0.7, y - h * 0.45), leaf, sw))
def stalactites(c, seed, n=12, maxh=46, sw=0):
    rnd = random.Random(seed); s = path("M -10 -10 L %d -10 L %d 18 L -10 18 Z" % (W + 10, W + 10), c, sw)
    for k in range(n):
        x = k * W / n + rnd.uniform(0, 20); h = rnd.uniform(16, maxh)
        s += path("M %.1f 16 L %.1f %.1f L %.1f 16 Z" % (x - 12, x, 16 + h, x + 12), c, sw)
    return s
def cavewalls(c, sw=0):
    return (path("M -10 0 L 70 0 Q 40 80 56 140 Q 64 170 40 %d L -10 %d Z" % (FLOOR, FLOOR), c, sw)
            + path("M %d 0 L %d 0 Q %d 80 %d 140 Q %d 170 %d %d L %d %d Z" % (W + 10, W - 70, W - 40, W - 56, W - 64, W - 40, FLOOR, W + 10, FLOOR), c, sw))
def rocks(seed, c, n=6, y=FLOOR, sw=3):
    rnd = random.Random(seed); s = ""
    for _ in range(n):
        x, r = rnd.uniform(10, W - 10), rnd.uniform(8, 16)
        s += path("M %.1f %d L %.1f %.1f L %.1f %.1f L %.1f %d Z" % (x - r, y + 2, x - r * 0.6, y - r, x + r * 0.5, y - r * 0.9, x + r, y + 2), c, sw)
    return s
def particles(seed, c, n=24, rmax=2.5, y0=20, y1=FLOOR, op=0.8):
    rnd = random.Random(seed)
    return "".join(circ(rnd.uniform(0, W), rnd.uniform(y0, y1), rnd.uniform(1, rmax), c, 0, op) for _ in range(n))
def castle(x, y, w, h, c, roof=None, sw=3, windows="#ffd65a"):
    s = rect(x, y - h, w, h, c).replace("/>", ' stroke="%s" stroke-width="%d"/>' % (INK, sw))
    for k in range(int(w // 16)):
        s += rect(x + k * 16 + 2, y - h - 10, 10, 10, c).replace("/>", ' stroke="%s" stroke-width="%d"/>' % (INK, sw))
    for k in range(int(w // 30)):
        s += path("M %.1f %.1f q 6 -10 12 0 v 14 h -12 Z" % (x + 9 + k * 30, y - h + 22), windows, 2)
    if roof: s += path("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x - 6, y - h - 10, x + w / 2, y - h - 10 - w * 0.6, x + w + 6, y - h - 10), roof, sw)
    return s
def pillar(x, y, h, c, cap, sw=3):
    return rect(x - 11, y - h, 22, h, c).replace("/>", ' stroke="%s" stroke-width="%d"/>' % (INK, sw)) + rect(x - 16, y - h - 8, 32, 10, cap).replace("/>", ' stroke="%s" stroke-width="%d"/>' % (INK, sw)) + rect(x - 16, y - 8, 32, 10, cap).replace("/>", ' stroke="%s" stroke-width="%d"/>' % (INK, sw))
def banner(x, y, h, c, trim="#f2c14e", sw=3):
    return path("M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x - 14, y, x + 14, y, x + 14, y + h, x, y + h - 12, x - 14, y + h), c, sw) + rect(x - 16, y - 4, 32, 6, trim).replace("/>", ' stroke="%s" stroke-width="2"/>' % INK)
def crystal(x, y, h, c, sw=3):
    return path("M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x - h * 0.22, y, x - h * 0.12, y - h * 0.8, x + h * 0.05, y - h, x + h * 0.22, y), c, sw) + path("M %.1f %.1f L %.1f %.1f" % (x - h * 0.05, y - h * 0.1, x, y - h * 0.85), "none", 0).replace('fill="none"', 'fill="none" stroke="#ffffff" stroke-width="2" opacity=".6"')
def lavapool(y, c="#ff7a1a", glow="#ffd04a"):
    return path("M -10 %d Q 128 %d 256 %d Q 384 %d %d %d L %d %d L -10 %d Z" % (y, y - 6, y, y + 6, W + 10, y, W + 10, Hh, Hh), c) + path("M 30 %d q 30 -6 60 0 M 200 %d q 40 -6 80 0 M 380 %d q 30 -5 60 0" % (y + 12, y + 20, y + 10), "none").replace('fill="none"', 'fill="none" stroke="%s" stroke-width="4" stroke-linecap="round"' % glow)
def moon(x, y, r, c="#f4f0d0"):
    return circ(x, y, r + 10, c, 0, 0.15) + circ(x, y, r, c)
def sun(x, y, r, c="#ffe36a"):
    return circ(x, y, r + 14, c, 0, 0.25) + circ(x, y, r, c)
def pyramid(x, y, w, c, shade, sw=3):
    return path("M %.1f %d L %.1f %.1f L %.1f %d Z" % (x - w / 2, y, x, y - w * 0.55, x + w / 2, y), c, sw) + path("M %.1f %.1f L %.1f %d L %.1f %d Z" % (x, y - w * 0.55, x + w / 2, y, x + w * 0.1, y), shade, 0, 0.5)
def ziggurat(x, y, c, sw=3):
    s = ""
    for k, (w, h) in enumerate(((180, 26), (140, 24), (100, 22), (60, 20))):
        yy = y - sum(hh for _, hh in ((180, 26), (140, 24), (100, 22), (60, 20))[:k])
        s += rect(x - w / 2, yy - h, w, h, c).replace("/>", ' stroke="%s" stroke-width="%d"/>' % (INK, sw))
    return s
def leaves(seed, c, n=10, top=True):
    rnd = random.Random(seed); s = ""
    for _ in range(n):
        x = rnd.uniform(-10, W + 10); y = rnd.uniform(-10, 30) if top else rnd.uniform(FLOOR - 30, FLOOR + 5)
        s += ell(x, y, rnd.uniform(26, 44), rnd.uniform(12, 18), c, 3)
    return s
def fence(y, c="#a2683e"):
    s = rect(0, y - 22, W, 5, c) + rect(0, y - 12, W, 5, c)
    for x in range(10, W, 40): s += rect(x, y - 30, 7, 30, c).replace("/>", ' stroke="%s" stroke-width="2"/>' % INK)
    return s
def windmill(x, y, c="#d9b98c"):
    s = path("M %d %d L %d %d L %d %d L %d %d Z" % (x - 22, y, x - 14, y - 90, x + 14, y - 90, x + 22, y), c, 3)
    for a in (20, 110, 200, 290):
        r = math.radians(a)
        s += path("M %d %d L %.1f %.1f L %.1f %.1f Z" % (x, y - 90, x + math.cos(r) * 70 - math.sin(r) * 10, y - 90 + math.sin(r) * 70 + math.cos(r) * 10,
                                                        x + math.cos(r) * 70 + math.sin(r) * 10, y - 90 + math.sin(r) * 70 - math.cos(r) * 10), "#f6f0e0", 3)
    return s + circ(x, y - 90, 7, "#8a5a36", 3)
def bars(c="#5a5e6a"):
    s = rect(0, 30, W, 8, c).replace("/>", ' stroke="%s" stroke-width="3"/>' % INK)
    for x in range(20, W, 34): s += rect(x, 30, 8, FLOOR - 30, c).replace("/>", ' stroke="%s" stroke-width="3"/>' % INK)
    return s
def shelves(c="#5a3a22"):
    s = ""
    for x in (30, 150, 270, 390):
        s += rect(x, 30, 96, 150, c).replace("/>", ' stroke="%s" stroke-width="3"/>' % INK)
        for k, yy in enumerate((44, 82, 120, 158)):
            for j in range(7):
                col = ("#8a2a2a", "#2a4a8a", "#3a6a3a", "#8a6a2a", "#5a2a6a")[(j + k * 2 + x) % 5]
                s += rect(x + 6 + j * 12, yy, 10, 30, col)
            s += rect(x, yy + 30, 96, 4, "#3a2414")
    return s
def ship(x, y):
    s = path("M %d %d L %d %d Q %d %d %d %d Z" % (x - 120, y - 40, x + 120, y - 40, x + 90, y + 10, x - 90, y + 10), "#7a4a2a", 3)
    s += rect(x - 4, y - 150, 8, 112, "#5a3a22").replace("/>", ' stroke="%s" stroke-width="3"/>' % INK)
    s += path("M %d %d L %d %d L %d %d Z" % (x + 6, y - 146, x + 80, y - 100, x + 6, y - 60), "#e8e0c8", 3)
    return s + path("M %d %d L %d %d L %d %d L %d %d Z" % (x - 30, y - 150, x - 6, y - 150, x - 6, y - 130, x - 30, y - 130), "#2e2e36", 2)
def gearwheel(x, y, r, c, sw=3):
    s = ""
    for k in range(10):
        a = k * 36
        s += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="%s" stroke-width="%d" transform="rotate(%d %.1f %.1f)"/>' % (x - r * 0.18, y - r * 1.25, r * 0.36, r * 0.4, c, INK, sw, a, x, y)
    return s + circ(x, y, r, c, sw) + circ(x, y, r * 0.35, "#3a3e48", sw)
def pipes(c="#8a929e"):
    return (rect(0, 40, W, 16, c).replace("/>", ' stroke="%s" stroke-width="3"/>' % INK) + rect(60, 40, 16, 150, c).replace("/>", ' stroke="%s" stroke-width="3"/>' % INK)
            + rect(430, 56, 16, 136, c).replace("/>", ' stroke="%s" stroke-width="3"/>' % INK) + circ(68, 48, 12, "#c08a3a", 3) + circ(438, 48, 12, "#c08a3a", 3))
def bones(seed, n=5, c="#efe6cc"):
    rnd = random.Random(seed); s = ""
    for _ in range(n):
        x, y, a = rnd.uniform(20, W - 20), rnd.uniform(FLOOR + 10, Hh - 12), rnd.uniform(-30, 30)
        s += '<g transform="rotate(%.1f %.1f %.1f)">%s%s%s</g>' % (a, x, y, rect(x - 14, y - 3, 28, 6, c), circ(x - 14, y - 3, 4, c), circ(x + 14, y + 3, 4, c))
    return s
def eggs(seed, n=6):
    rnd = random.Random(seed)
    return "".join(ell(rnd.uniform(30, W - 30), FLOOR + rnd.uniform(4, 30), 10, 13, "#d8c8a0", 3) for _ in range(n))
def webs(c="#e8e8e8"):
    return ('<path d="M 0 0 L 90 90 M 0 30 L 70 90 M 30 0 L 90 70 M 20 20 Q 40 50 60 60 M 10 50 Q 30 60 50 80 M 50 10 Q 60 30 80 50" fill="none" stroke="%s" stroke-width="2" opacity=".6"/>' % c)

# ---------------------------------------------------------------- scenes
S = {}
S["elwynn"] = (sky("#8fd0f4", "#a8dcf6", "#c2e8f8") + sun(430, 50, 22) + clouds(1) + wave(150, 30, "#8fcf7a", 2) + wave(172, 24, "#6fb85a", 3)
               + "".join(roundtree(x, 168, r, c) for x, r, c in ((40, 26, "#4f9e46"), (120, 20, "#5aae4e"), (380, 24, "#4f9e46"), (470, 30, "#459040")))
               + castle(230, 150, 60, 60, "#d8d2c4", "#3d6fd8") + floor("#7ec06a", "#93d47c") + path("M 180 256 Q 240 220 256 192 L 300 192 Q 300 220 340 256 Z", "#d9b98c"))
S["westfall"] = (sky("#f4c88a", "#f7d8a0", "#fae6bc") + sun(90, 60, 24, "#fff0a0") + clouds(4, 3, "#fff6e0") + wave(160, 20, "#d9b05a", 5) + wave(176, 14, "#c89a40", 6)
                 + windmill(400, 176) + path("M 150 176 L 150 130 L 190 110 L 230 130 L 230 176 Z", "#b8402a", 3) + rect(178, 150, 24, 26, "#5a3a22") + fence(192)
                 + floor("#d6b260", "#e6c878"))
S["rfc"] = (rect(0, 0, W, Hh, "#3a1a14") + stalactites("#5a2a1a", 7) + cavewalls("#4a2216") + particles(8, "#ffb04a", 30, 2.5)
            + rocks(9, "#6a3020", 7, FLOOR) + floor("#5a2a1a", "#7a3a22") + lavapool(222))
S["wc"] = (rect(0, 0, W, Hh, "#1e3a2a") + stalactites("#2e5a3a", 10) + cavewalls("#264a32") + "".join(ell(x, 120, 18, 40, "#3a7a4a", 3) for x in (110, 400))
           + particles(11, "#c6ff9a", 26, 2.2) + floor("#2e5a3a", "#3e7a4a") + path("M -10 230 Q 256 218 522 232 L 522 256 L -10 256 Z", "#3a8a8a", 0, 0.8))
S["dm"] = (rect(0, 0, W, Hh, "#2a2420") + stalactites("#3a322a", 12) + ship(330, 190) + rect(30, 60, 14, 132, "#6a4a2a").replace("/>", ' stroke="%s" stroke-width="3"/>' % INK)
           + rect(20, 60, 120, 12, "#6a4a2a").replace("/>", ' stroke="%s" stroke-width="3"/>' % INK) + circ(100, 92, 10, "#ffd65a", 0, 0.5) + floor("#4a3a2a", "#5a4a3a"))
S["sfk"] = (sky("#1e1a3a", "#2a2450", "#3a3068") + moon(420, 56, 26) + particles(13, "#ffffff", 40, 1.4, 0, 120, 0.8)
            + castle(60, 192, 90, 120, "#5a5a6a", None, 3, "#ffd65a") + castle(330, 192, 120, 100, "#5a5a6a", "#3a2a4a", 3, "#ffd65a")
            + pine(220, 192, 60, "#2a3a3a") + floor("#3a3a46", "#4a4a58"))
S["bfd"] = (rect(0, 0, W, Hh, "#14283e") + stalactites("#1e3a56", 15) + "".join(pillar(x, FLOOR, 130, "#3a5a7a", "#4a7a9a") for x in (90, 420))
            + particles(16, "#9fe4ff", 30, 3, 30, FLOOR, 0.6) + floor("#1e3a56", "#2e5a7a") + path("M -10 214 Q 256 204 522 216 L 522 256 L -10 256 Z", "#2a6aa0", 0, 0.75))
S["stocks"] = (rect(0, 0, W, Hh, "#3a3a42") + "".join(rect(x, y, 60, 30, "#46464e").replace("/>", ' stroke="#2a2a30" stroke-width="2"/>') for x in range(0, W, 60) for y in range(0, FLOOR, 30))
               + bars() + circ(256, 80, 14, "#ffb04a", 0, 0.35) + floor("#2e2e34", "#3a3a42"))
S["gnomer"] = (rect(0, 0, W, Hh, "#2a3040") + pipes() + gearwheel(160, 110, 36, "#9aa2ae") + gearwheel(340, 90, 26, "#c08a3a") + gearwheel(390, 150, 18, "#9aa2ae")
               + particles(19, "#7fff6a", 18, 3, 60, FLOOR, 0.5) + floor("#4a5060", "#5a6274") + path("M -10 232 Q 256 226 522 234 L 522 256 L -10 256 Z", "#5ad04a", 0, 0.55))
S["rfk"] = (sky("#e0a860", "#e8b878", "#f0cc98") + wave(150, 26, "#c08040", 20) + "".join(path("M %d 192 Q %d 120 %d 60 Q %d 130 %d 192 Z" % (x - 16, x - 30, x, x + 10, x + 16), "#7a5a30", 3) for x in (60, 150, 360, 450))
            + "".join(path("M %d %d l -12 -6 M %d %d l 12 -8" % (x, y, x, y + 14), "none").replace('fill="none"', 'fill="none" stroke="%s" stroke-width="3"' % INK) for x, y in ((60, 120), (150, 110), (360, 120), (450, 100)))
            + floor("#a86a3a", "#c0804a"))
S["sm"] = (rect(0, 0, W, Hh, "#e8dccc") + "".join(pillar(x, FLOOR, 160, "#d8ccb8", "#c0b098") for x in (70, 190, 322, 442))
           + "".join(banner(x, 40, 90, "#b3161e") for x in (130, 256, 382)) + path("M 216 40 Q 256 0 296 40 L 296 150 L 216 150 Z", "#9ad0f0", 3)
           + floor("#b8a890", "#c8b8a0") + rect(196, FLOOR, 120, 64, "#b3161e"))
S["rfd"] = (sky("#4a3a4a", "#5a4858", "#6a5868") + moon(80, 50, 18, "#d8d8e8") + wave(160, 24, "#5a4a3a", 22)
            + "".join(path("M %d 192 Q %d 120 %d 60 Q %d 130 %d 192 Z" % (x - 16, x - 30, x, x + 10, x + 16), "#5a4a3a", 3) for x in (120, 400)) + bones(23, 6) + floor("#6a5a4a", "#7a6a5a"))
S["uld"] = (rect(0, 0, W, Hh, "#5a4a3a") + "".join(rect(x, y, 64, 32, "#6a5a48").replace("/>", ' stroke="#4a3a2a" stroke-width="2"/>') for x in range(0, W, 64) for y in range(0, FLOOR, 32))
            + pillar(80, FLOOR, 150, "#8a7a60", "#a08a68") + pillar(432, FLOOR, 150, "#8a7a60", "#a08a68")
            + path("M 200 192 L 200 70 Q 256 30 312 70 L 312 192 Z", "#3a4a6a", 3) + circ(256, 100, 16, "#7fd4ff", 3) + floor("#7a6a50", "#8a7a60"))
S["zf"] = (sky("#f0b060", "#f4c478", "#f8d898") + sun(420, 48, 20, "#fff0a0") + pyramid(140, 182, 200, "#d8a860", "#a0702a") + pyramid(390, 186, 150, "#e0b470", "#a0702a")
           + wave(186, 10, "#e8c07a", 24) + floor("#e0b468", "#ecc480"))
S["mara"] = (rect(0, 0, W, Hh, "#2a1e3a") + stalactites("#3a2a50", 25) + cavewalls("#34264a")
             + "".join(crystal(x, FLOOR, h, c) for x, h, c in ((70, 70, "#b47cf0"), (110, 46, "#8a4fd0"), (410, 80, "#b47cf0"), (450, 50, "#8a4fd0")))
             + leaves(26, "#3e8a4a", 6, False) + particles(27, "#e0b0ff", 24, 2.4) + floor("#3a2a50", "#4a3a64"))
S["st"] = (sky("#2a4a3a", "#3a5a48", "#4a6a58") + ziggurat(256, 186, "#6a7a5a") + leaves(28, "#2f7a3a", 12, True)
           + path("M -10 206 Q 256 196 522 208 L 522 256 L -10 256 Z", "#3a6a4a", 0, 1) + floor("#4a5a3a", "#5a6a48", False) + particles(29, "#c6ff9a", 20, 2))
S["brd"] = (rect(0, 0, W, Hh, "#2a1e1a") + "".join(rect(x, 20, 70, 172, "#3a2a24").replace("/>", ' stroke="%s" stroke-width="3"/>' % INK) for x in (30, 412))
            + "".join(path("M %d 20 L %d 192" % (x, x), "none").replace('fill="none"', 'fill="none" stroke="#ff8a2a" stroke-width="5" opacity=".7"') for x in (65, 447))
            + path("M 150 60 L 362 60 L 340 170 L 172 170 Z", "#4a3a32", 3) + rect(200, 90, 112, 60, "#ff8a2a", 0.7) + particles(31, "#ffb04a", 26, 2.4)
            + floor("#3a2a24", "#4a3a30") + lavapool(232))
S["brs"] = (sky("#3a1e1a", "#5a2a1e", "#7a3a22") + peaks(192, 150, "#2a1a16", 32, 4) + castle(180, 192, 150, 110, "#4a3a32", None, 3, "#ff8a2a")
            + particles(33, "#ffb04a", 30, 2.6) + floor("#3a2a24", "#4a3a30"))
S["dim"] = (sky("#3a5a48", "#4a6a58", "#5a7a68") + "".join(pillar(x, FLOOR, 140, "#a8b8c8", "#8a9aaa") for x in (90, 210, 330, 450))
            + path("M 60 52 Q 256 0 452 52 L 452 62 L 60 62 Z", "#8a9aaa", 3) + leaves(34, "#3e8a4a", 9, True) + leaves(35, "#4e9a5a", 6, False)
            + floor("#4a5a4a", "#5a6a5a"))
S["scholo"] = (rect(0, 0, W, Hh, "#22202a") + shelves() + particles(36, "#9fffd0", 18, 2.5, 20, FLOOR, 0.6) + webs() + floor("#3a3440", "#4a4450") + bones(37, 3))
S["strat"] = (sky("#3a1e3a", "#5a2a3a", "#8a3a2a") + "".join(castle(x, 192, w, h, "#3a3440", None, 3, "#ff8a2a") for x, w, h in ((10, 90, 100), (150, 70, 70), (260, 110, 120), (410, 90, 90)))
              + particles(38, "#ff8a2a", 30, 2.6, 0, 120) + particles(39, "#d0ff9a", 14, 2.2) + floor("#3a3440", "#4a4450"))
S["zg"] = (sky("#5aa070", "#6ab080", "#7ac090") + ziggurat(256, 190, "#8a8a6a") + leaves(40, "#2f7a3a", 14, True)
           + "".join(path("M %d 192 Q %d 120 %d 70" % (x, x - 20, x + 10), "none").replace('fill="none"', 'fill="none" stroke="#6a4a2a" stroke-width="10"') for x in (40, 470))
           + leaves(41, "#3e8a4a", 6, False) + floor("#5a6a3a", "#6a7a48") + particles(42, "#ffe36a", 14, 2.2))
S["mc"] = (rect(0, 0, W, Hh, "#2a0e0a") + stalactites("#4a1a10", 43, 12, 60) + cavewalls("#3a140e") + particles(44, "#ffb04a", 40, 3)
           + path("M 0 120 Q 100 100 160 140 Q 220 180 300 150 Q 400 110 512 140 L 512 150 Q 400 120 300 160 Q 220 190 160 150 Q 100 110 0 130 Z", "#ff7a1a", 0, 0.9)
           + rocks(45, "#4a1a10", 8) + floor("#3a1410", "#5a2014") + lavapool(226, "#ff5a10"))
S["ony"] = (rect(0, 0, W, Hh, "#2a1a1e") + stalactites("#3a2428", 46, 12, 50) + cavewalls("#34202a") + rect(0, 130, W, 62, "#3a2428")
            + path("M -10 192 Q 256 150 522 192 Z", "#ff7a1a", 0, 0.5) + eggs(47, 7) + bones(48, 4) + floor("#3a2428", "#4a3034"))
S["aq20"] = (sky("#e8b878", "#ecc890", "#f0d8a8") + sun(80, 46, 18, "#fff0a0") + wave(170, 20, "#e0b070", 49)
             + "".join(path("M %d 192 L %d 90 L %d 192 Z" % (x - 30, x, x + 30), "#a0702a", 3) for x in (140, 380))
             + "".join(circ(x, 90, 10, "#b8402a", 3) for x in (140, 380)) + floor("#e0b468", "#ecc480"))
S["bwl"] = (rect(0, 0, W, Hh, "#1e1418") + "".join(rect(x, y, 64, 32, "#2a1c22").replace("/>", ' stroke="#140c10" stroke-width="2"/>') for x in range(0, W, 64) for y in range(0, FLOOR, 32))
            + "".join(banner(x, 30, 100, "#5a1a2a", "#c08a3a") for x in (90, 422))
            + path("M 176 170 Q 170 90 230 70 L 256 40 L 282 70 Q 342 90 336 170 Q 300 150 256 156 Q 212 150 176 170 Z", "#3a2a30", 3)
            + circ(226, 112, 9, "#ff5a2a", 0) + circ(286, 112, 9, "#ff5a2a", 0) + path("M 230 140 L 238 156 L 246 140 M 266 140 L 274 156 L 282 140", "#efe6cc", 2)
            + particles(54, "#ff7a3a", 22, 2.4) + floor("#2a1c22", "#3a2830"))
S["aq40"] = (rect(0, 0, W, Hh, "#2a1e2a") + "".join(rect(x, y, 64, 32, "#3a2a3a").replace("/>", ' stroke="#2a1a2a" stroke-width="2"/>') for x in range(0, W, 64) for y in range(0, FLOOR, 32))
             + pillar(80, FLOOR, 160, "#c8a060", "#e0b870") + pillar(432, FLOOR, 160, "#c8a060", "#e0b870")
             + circ(256, 80, 40, "#7a3ab0", 3) + circ(256, 80, 22, "#c87af0", 0) + particles(50, "#e0b0ff", 22, 2.4) + floor("#4a3a4a", "#5a4a5a"))
S["naxx"] = (sky("#1a2a3a", "#22364a", "#2a425a") + particles(51, "#ffffff", 40, 1.4, 0, 120, 0.8)
             + path("M 140 40 L 372 40 L 330 130 L 182 130 Z", "#3a4a5a", 3) + "".join(path("M %d 130 L %d 160 L %d 130 Z" % (x - 8, x, x + 8), "#3a4a5a", 3) for x in (200, 256, 312))
             + rect(220, 64, 72, 30, "#7aff9a", 0.7) + peaks(192, 70, "#2a3a4a", 52, 5, 1, "#e8f0ff") + particles(53, "#9fffd0", 16, 2.4) + floor("#3a4a5a", "#4a5a6a"))

# ---------------------------------------------------------------- fishing dock (Professions > Fishing), not an Adventure zone
# A calm lake: far shore with pines, open water on the right for the bobber, and a wooden dock on the
# left third whose deck (x 0..196, top at y 176) has room for two sitting cats.
DOCK_TOP = 176
def ripples(seed, n, x0, x1, y0, y1, c="#ffffff", op=0.55):
    rnd = random.Random(seed); s = ""
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1); w = 6 + (y - 128) * 0.18 + rnd.uniform(0, 8)
        s += '<path d="M %.1f %.1f q %.1f -3 %.1f 0" fill="none" stroke="%s" stroke-width="2" stroke-linecap="round" opacity="%s"/>' % (x, y, w / 2, w, c, op)
    return s
def cattail(x, y, h, lean):
    tx = x + lean
    return ('<path d="M %d %d Q %.1f %.1f %.1f %.1f" fill="none" stroke="%s" stroke-width="6" stroke-linecap="round"/>' % (x, y, x + lean * 0.2, y - h * 0.5, tx, y - h, INK)
            + '<path d="M %d %d Q %.1f %.1f %.1f %.1f" fill="none" stroke="#5a9a3e" stroke-width="3" stroke-linecap="round"/>' % (x, y, x + lean * 0.2, y - h * 0.5, tx, y - h)
            + ell(tx, y - h + 4, 5, 11, "#8a5a36", 2.5))
def dock_scene():
    s = sky("#8fd0f4", "#a6dbf5", "#c4e9f8") + sun(410, 46, 20)
    for x, y in ((92, 40), (236, 58), (318, 30)):                                     # clouds kept clear of the sun
        for dx, dy, r in ((-16, 4, 12), (0, 0, 16), (18, 4, 12)): s += circ(x + dx, y + dy, r, "#ffffff", 0, 0.9)
    s += peaks(126, 46, "#9fc4dc", 62, 6, 0.9, "#eef6fb")                           # far blue mountains
    s += wave(124, 12, "#7fbf86", 63, 7) + wave(130, 6, "#5fa868", 64, 8)            # far shore hills
    rnd = random.Random(65)
    for k in range(22):                                                               # pines along the far shore
        x = 6 + k * 24 + rnd.uniform(-6, 6); h = rnd.uniform(18, 30)
        s += path("M %.1f 132 L %.1f %.1f L %.1f 132 Z" % (x - h * 0.32, x, 132 - h, x + h * 0.32), "#3f7f4e")
    s += rect(0, 131, W, Hh - 131, "#6cc0e6") + rect(0, 158, W, 40, "#60b4de") + rect(0, 198, W, 58, "#53a6d6")
    s += path("M 0 131 L %d 131" % W, "none").replace('fill="none"', 'fill="none" stroke="#3f7f4e" stroke-width="2"')
    s += rect(0, 132, W, 4, "#ffffff", 0.35)                                           # shine along the far shore
    for k, (w, y) in enumerate(((60, 140), (44, 150), (30, 162), (18, 174))):        # sun glitter on the water
        s += rect(410 - w / 2 + (k % 2) * 6, y, w, 3, "#fff6c8", 0.7)
    s += ripples(66, 26, 200, W - 20, 140, 250)
    # lily pads near the bottom edge, out of the bobber's way
    for x, y, r in ((236, 244, 11), (258, 250, 8), (484, 238, 10)):
        s += ell(x, y, r * 1.5, r * 0.6, "#5aae4e", 2.5) + path("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x, y, x + r * 1.5, y - r * 0.4, x + r * 1.5, y + r * 0.1), "#53a6d6")
    s += circ(242, 238, 4, "#f6a0c8", 2)
    # cattails on the right edge
    for x, h, lean in ((488, 74, -6), (500, 92, 4), (512, 66, 10), (476, 54, -12)): s += cattail(x, 250, h, lean)
    # grassy bank in the bottom-left corner where the dock starts
    s += path("M -10 200 Q 30 192 64 214 Q 84 236 78 266 L -10 266 Z", "#6fb85a", 3) + path("M -10 206 Q 28 200 56 216", "none").replace('fill="none"', 'fill="none" stroke="#93d47c" stroke-width="4" stroke-linecap="round"')
    # dock: posts into the water, deck top, plank front face
    T = DOCK_TOP
    for x, y1, wet in ((34, 230, False), (104, 234, True), (172, 232, True)):     # the first post stands on the bank
        if wet: s += ell(x + 6, y1, 18, 4, "#ffffff", 0, 0.5)
        s += rect(x, T, 12, y1 - T, "#7a4a2a").replace("/>", ' stroke="%s" stroke-width="3"/>' % INK)
        if wet: s += rect(x + 2, y1 - 10, 8, 10, "#3f8fc0", 0.35)                     # post under the water
    s += path("M -10 %d L 190 %d L 200 %d L -10 %d Z" % (T, T, T + 10, T + 10), "#c99a62", 3)
    s += "".join(path("M %d %d L %d %d" % (x, T, x + 3, T + 10), "none").replace('fill="none"', 'fill="none" stroke="#9a6a3e" stroke-width="2"') for x in range(18, 190, 22))
    s += path("M -10 %d L 200 %d L 200 %d L -10 %d Z" % (T + 10, T + 10, T + 22, T + 22), "#a2683e", 3)
    s += "".join(circ(x, T + 16, 2, "#5e3d24") for x in range(12, 200, 44))            # nail heads
    # a short mooring post with a rope at the end of the dock (kept low, below the fishing line)
    s += rect(188, T - 16, 14, 50, "#8a5a36").replace("/>", ' stroke="%s" stroke-width="3"/>' % INK) + ell(195, T - 16, 7, 3, "#b07a48", 2)
    s += path("M 186 %d q 9 5 18 0 M 186 %d q 9 5 18 0" % (T - 4, T + 2), "none").replace('fill="none"', 'fill="none" stroke="#e0c890" stroke-width="3"')
    return s
S_EXTRA = {"dock": dock_scene()}

def main():
    work = sys.argv[1]; os.makedirs(work, exist_ok=True)
    out = os.path.join(ROOT, "Art", "v"); os.makedirs(out, exist_ok=True)
    ALL = dict(S, **S_EXTRA)
    for key, body in ALL.items():
        # a soft vignette darkens the edges so the fighters stand out
        vig = '<rect width="%d" height="%d" fill="url(#vg)"/>' % (W, Hh)
        defs = '<defs><radialGradient id="vg" cx="50%" cy="55%" r="70%"><stop offset=".65" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".35"/></radialGradient></defs>'
        open(os.path.join(work, key + ".svg"), "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d">%s%s%s</svg>' % (W, Hh, defs, body, vig))
    subprocess.check_call(["node", os.path.join(HERE, "render_svg.js"), work, str(W), str(Hh)])
    for key in ALL:
        write_tga(Image.open(os.path.join(work, key + ".png")).convert("RGBA"), os.path.join(out, "bg_" + key + ".tga"))
    if len(sys.argv) > 2:
        keys = list(ALL); cols = 4; tw, th = 256, 128
        sheet = Image.new("RGBA", (cols * tw, ((len(keys) + cols - 1) // cols) * th), (0, 0, 0, 255))
        for i, k in enumerate(keys):
            sheet.paste(Image.open(os.path.join(work, k + ".png")).convert("RGBA").resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
        sheet.save(sys.argv[2])
    print("backgrounds:", len(ALL))

if __name__ == "__main__":
    main()
