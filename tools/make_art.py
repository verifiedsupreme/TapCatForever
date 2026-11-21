#!/usr/bin/env python3
"""
TapCatForever art generator.

Draws every sprite layer of the cat procedurally on a 64x64 pixel grid,
then writes 256x256 RLE TGA files (4x nearest-neighbour upscale) that the
WoW client can load directly. Also emits Art/ArtData.lua with bounding
boxes (used to crop wardrobe previews) and a showcase PNG.

Layers are drawn in greyscale so the addon can tint them per item with
SetVertexColor. Two-part items produce <name>_a and <name>_b files so each
part gets its own tint (e.g. blade vs. hilt).
"""
import math, os, random, sys
from PIL import Image

N = 64          # logical canvas
UP = 4          # upscale factor written to disk
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "Art")

# ---------------------------------------------------------------- shapes
def E(cx, cy, rx, ry):
    s = set()
    for y in range(N):
        for x in range(N):
            dx = (x + .5 - cx) / rx; dy = (y + .5 - cy) / ry
            if dx * dx + dy * dy <= 1: s.add((x, y))
    return s

def P(pts):
    s = set()
    n = len(pts)
    for y in range(N):
        for x in range(N):
            px, py = x + .5, y + .5; inside = False; j = n - 1
            for i in range(n):
                xi, yi = pts[i]; xj, yj = pts[j]
                if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
                    inside = not inside
                j = i
            if inside: s.add((x, y))
    return s

def R(x0, y0, x1, y1):
    return {(x, y) for x in range(max(0, x0), min(N, x1 + 1)) for y in range(max(0, y0), min(N, y1 + 1))}

def L(x0, y0, x1, y1, w=1.0):
    s = set(); r = w / 2
    vx, vy = x1 - x0, y1 - y0; ll = vx * vx + vy * vy or 1
    for y in range(N):
        for x in range(N):
            px, py = x + .5, y + .5
            t = max(0, min(1, ((px - x0) * vx + (py - y0) * vy) / ll))
            dx = px - (x0 + t * vx); dy = py - (y0 + t * vy)
            if dx * dx + dy * dy <= r * r: s.add((x, y))
    return s

def poly_line(pts, w):
    s = set()
    for a, b in zip(pts, pts[1:]): s |= L(a[0], a[1], b[0], b[1], w)
    return s

def arc(cx, cy, r, a0, a1, w, steps=24):
    pts = [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
            cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / steps))) for i in range(steps + 1)]
    return poly_line(pts, w)

def ring(cx, cy, rx, ry, t):
    return E(cx, cy, rx, ry) - E(cx, cy, rx - t, ry - t)

def M(s):  # mirror horizontally
    return {(N - 1 - x, y) for x, y in s}

def shift(s, dx, dy):
    return {(x + dx, y + dy) for x, y in s if 0 <= x + dx < N and 0 <= y + dy < N}

def border(s):  # pixels of s touching outside of s
    return {(x, y) for x, y in s if any((x + a, y + b) not in s for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))}

def star4(cx, cy, r):
    return L(cx - r, cy, cx + r, cy, 1.2) | L(cx, cy - r, cx, cy + r, 1.2) | E(cx, cy, 1.1, 1.1)

def diamond(cx, cy, r):
    return P([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)])

# ---------------------------------------------------------------- tones
TONES = {
    "light": (228, 250, 182),
    "mid":   (172, 204, 132),
    "dark":  (112, 140, 82),
    "white": (255, 255, 255),
}
OUTLINE = (30, 24, 36, 255)

class Layer:
    def __init__(self): self.px = {}
    def paint(self, mask, tone="light", shade=True, color=None, alpha=255):
        if color is not None:
            for p in mask: self.px[p] = (*color, alpha)
            return self
        base, hi, sh = TONES[tone]
        for (x, y) in mask:
            v = base
            if shade:
                if (x, y - 1) not in mask: v = hi
                elif (x, y + 1) not in mask or (x + 1, y) not in mask: v = sh
            self.px[(x, y)] = (v, v, v, alpha)
        return self
    def erase(self, mask):
        for p in mask: self.px.pop(p, None)
        return self
    def mask(self): return set(self.px)

def finish(a, b=None, outline=True):
    """Outline the union of a and b (outline pixels go on layer a)."""
    if outline:
        u = a.mask() | (b.mask() if b else set())
        for (x, y) in list(u):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if 0 <= q[0] < N and 0 <= q[1] < N and q not in u:
                    a.px[q] = OUTLINE
    return a, b

# ---------------------------------------------------------------- io
def to_image(layer, size=N):
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    pix = im.load()
    for (x, y), c in layer.px.items():
        if 0 <= x < N and 0 <= y < N: pix[x, y] = c
    return im

def write_tga(im, path):
    """32-bit RLE TGA, origin top-left."""
    w, h = im.size
    data = im.load()
    out = bytearray()
    out += bytes([0, 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                  w & 255, w >> 8, h & 255, h >> 8, 32, 8 | 32])
    for y in range(h):
        row = [data[x, y] for x in range(w)]
        i = 0
        while i < w:
            j = i + 1
            while j < w and j - i < 128 and row[j] == row[i]: j += 1
            if j - i > 1:
                r, g, b, a = row[i]
                out += bytes([0x80 | (j - i - 1), b, g, r, a]); i = j
            else:
                j = i + 1
                while j < w and j - i < 128 and (j + 1 >= w or row[j] != row[j + 1]): j += 1
                out += bytes([j - i - 1])
                for k in range(i, j):
                    r, g, b, a = row[k]; out += bytes([b, g, r, a])
                i = j
    with open(path, "wb") as f: f.write(out)

ART = {}      # name -> PIL image (64x64)
BOUNDS = {}   # base name -> (x0,y0,x1,y1)

def save(name, a, b=None, outline=True):
    finish(a, b, outline)
    if b is None:
        ART[name] = to_image(a)
    else:
        ART[name + "_a"] = to_image(a); ART[name + "_b"] = to_image(b)
    m = a.mask() | (b.mask() if b else set())
    if m:
        xs = [p[0] for p in m]; ys = [p[1] for p in m]
        BOUNDS[name] = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)

def save_img(name, im):
    ART[name] = im
    bb = im.getbbox() or (0, 0, N, N)
    BOUNDS[name] = bb

# ================================================================ CAT
HEAD = E(32, 30, 17, 13.5)
EAR_L = P([(15.5, 27), (17.5, 8.5), (29, 18)])
EAR_R = M(EAR_L)
BODY = E(32, 55, 19, 16)
FUR = HEAD | EAR_L | EAR_R | BODY
CHEST = BODY - HEAD          # region armour may cover

# paw anchors (right side; left is mirrored)
PAW_DOWN = (44, 58)
PAW_UP = (50, 44)

def cat_fur():
    a = Layer()
    a.paint(BODY, "light").paint(HEAD | EAR_L | EAR_R, "light")
    # chin line where the head overlaps the body
    chin = {p for p in border(HEAD) if p in BODY and p[1] > 34}
    a.paint(chin, color=OUTLINE[:3])
    save("cat_fur", a)

def paw(down, side):
    a, b = Layer(), Layer()
    if down:
        cx, cy = PAW_DOWN
        m = E(cx, cy, 6.2, 4.6)
        a.paint(m, "light")
        for tx in (-2, 1):  # toe separators
            a.paint({(cx + tx, cy + 2), (cx + tx, cy + 3)}, color=(150, 150, 150))
    else:
        cx, cy = PAW_UP
        arm = L(45, 54, cx, cy + 2, 7)
        m = E(cx, cy, 5.2, 5.6) | arm
        a.paint(m, "light")
        # toe beans (part b, tinted pink by addon)
        b.paint(E(cx, cy + 1.5, 2.2, 1.8), color=(255, 255, 255))
        for bx, by in ((-2.5, -2.5), (0, -3.5), (2.5, -2.5)):
            b.paint(E(cx + bx, cy + by, 1.0, 1.0), color=(255, 255, 255))
    if side == "L":
        a.px = {(N - 1 - x, y): c for (x, y), c in a.px.items()}
        b.px = {(N - 1 - x, y): c for (x, y), c in b.px.items()}
    save("paw_%s_%s" % (side, "down" if down else "up"), a, b)

BLACK = (22, 18, 26); WHITE = (255, 255, 255); PINK = (255, 150, 170); BLUSH = (255, 120, 150)

def face(kind):
    a = Layer()
    # inner ears
    a.paint(P([(19, 23), (19.5, 12.5), (26, 18.5)]), color=(255, 170, 185))
    a.paint(M(P([(19, 23), (19.5, 12.5), (26, 18.5)])), color=(255, 170, 185))
    # nose + mouth
    a.paint({(31, 33), (32, 33)}, color=PINK)
    a.paint({(31, 34), (32, 34), (29, 35), (30, 36), (33, 36), (34, 35)}, color=BLACK)
    # blush
    a.paint({(20, 34), (21, 34), (22, 34), (41, 34), (42, 34), (43, 34)}, color=BLUSH, alpha=170)
    if kind == "normal":
        for ex in (24, 38):
            a.paint(R(ex, 28, ex + 1, 31), color=BLACK)
            a.paint({(ex, 28)}, color=WHITE)
    elif kind == "blink":
        for ex in (23, 37):
            a.paint(R(ex, 30, ex + 3, 30), color=BLACK)
    elif kind == "happy":   # ^ ^
        for ex in (24, 38):
            a.paint({(ex - 1, 31), (ex, 30), (ex + 1, 29), (ex + 2, 30), (ex + 3, 31)} if False else
                    {(ex - 1, 31), (ex, 30), (ex + 1, 30), (ex + 2, 31)}, color=BLACK)
            a.paint({(ex, 29), (ex + 1, 29)}, color=BLACK)
    elif kind == "focus":   # > <
        a.paint({(23, 28), (24, 29), (25, 30), (24, 31), (23, 32)}, color=BLACK)
        a.paint({(40, 28), (39, 29), (38, 30), (39, 31), (40, 32)}, color=BLACK)
    elif kind == "sparkle":
        for ex in (24, 38):
            a.paint(R(ex - 1, 28, ex + 2, 31), color=BLACK)
            a.paint({(ex - 1, 28), (ex, 28), (ex + 1, 30)}, color=WHITE)
    save("face_" + kind, a, outline=False)

# fur patterns (tinted overlay clipped to fur)
def pattern(name, a_mask, b_mask=None):
    a, b = Layer(), Layer()
    a.paint(a_mask & FUR, "light", shade=False)
    if b_mask: b.paint(b_mask & FUR, "light", shade=False)
    save("pat_" + name, a, b if b_mask else None, outline=False)

def patterns():
    tabby = (L(28, 17, 28, 22, 1.4) | L(32, 16.5, 32, 23, 1.4) | L(36, 17, 36, 22, 1.4) |
             L(15, 28, 19, 29, 1.3) | L(15, 32, 19, 32, 1.3) | M(L(15, 28, 19, 29, 1.3) | L(15, 32, 19, 32, 1.3)) |
             L(14, 48, 21, 50, 1.6) | L(13, 54, 20, 55, 1.6) | M(L(14, 48, 21, 50, 1.6) | L(13, 54, 20, 55, 1.6)))
    pattern("tabby", tabby)
    pattern("tuxedo", E(32, 56, 9, 12) | E(32, 37, 7, 4.5))
    pattern("calico", E(21, 22, 7, 7) | E(46, 54, 7, 6), E(42, 21, 6, 5) | E(20, 56, 6, 5))
    pattern("points", EAR_L | EAR_R | E(32, 35, 8, 6))
    spots = set()
    rnd = random.Random(7)
    for _ in range(14):
        x, y = rnd.uniform(15, 49), rnd.uniform(20, 62)
        spots |= ring(x, y, 2.4, 2.4, 1.1)
    pattern("leopard", spots)
    pattern("socks", E(32, 22, 4, 3) | L(32, 22, 32, 26, 2))  # forehead blaze

# ================================================================ HEAD GEAR
def head_items():
    # Great helm (warrior)
    a, b = Layer(), Layer()
    dome = E(32, 25, 19.5, 15) & R(0, 0, 63, 24)
    a.paint(dome, "light")
    b.paint(R(13, 22, 50, 25) & E(32, 25, 20.5, 16), "mid")
    b.paint(R(31, 24, 32, 29), "mid")
    b.paint(R(31, 10, 32, 22), "mid", shade=False)
    save("head_greathelm", a, b)

    # Horned helm
    a, b = Layer(), Layer()
    a.paint(dome, "light"); a.paint(R(13, 22, 50, 25) & E(32, 25, 20.5, 16), "mid")
    hl = poly_line([(15, 19), (9, 15), (6, 9), (7, 3)], 3.6) | poly_line([(7, 3), (8, 0)], 2)
    b.paint(hl | M(hl), "light")
    save("head_hornhelm", a, b)

    # Winged helm (paladin)
    a, b = Layer(), Layer()
    a.paint(dome, "light"); a.paint(R(13, 22, 50, 25) & E(32, 25, 20.5, 16), "mid")
    a.paint(diamond(32, 17, 3), "dark")
    w = P([(14, 18), (2, 6), (5, 13), (1, 14), (7, 19), (4, 22), (13, 22)])
    b.paint(w | M(w), "light")
    b.paint(L(4, 11, 12, 18, 1) | M(L(4, 11, 12, 18, 1)), "mid", shade=False)
    save("head_winghelm", a, b)

    # Wizard hat (mage)
    a, b = Layer(), Layer()
    cone = P([(20, 20), (44, 20), (39, 9), (47, 0), (35, 5), (27, 9)])
    a.paint(cone, "light"); a.paint(E(32, 20.5, 22, 3.6), "mid")
    b.paint(cone & R(0, 15, 63, 17), "light", shade=False)
    b.paint(star4(35, 10, 2), "white")
    save("head_wizard", a, b)

    # Hood (rogue / warlock / priest)
    a, b = Layer(), Layer()
    hood = E(32, 30, 21, 17.5) | P([(22, 16), (32, 4), (42, 16)])
    window = E(32, 32, 13, 10.5)
    a.paint(hood - window, "light")
    a.erase(R(0, 44, 63, 63) - E(32, 30, 21, 17.5))
    b.paint(ring(32, 32, 14, 11.5, 1.4) & (hood - window), "mid", shade=False)
    save("head_hood", a, b)

    # Bandit mask (rogue)
    a, b = Layer(), Layer()
    band = (R(14, 26, 49, 32) & E(32, 30, 18, 14.5)) - E(24.5, 29.5, 3, 2.6) - E(38.5, 29.5, 3, 2.6)
    a.paint(band, "dark")
    tails = P([(48, 27), (60, 22), (57, 28), (61, 33), (48, 31)])
    b.paint(tails, "dark")
    save("head_mask", a, b)

    # Feathered cap (hunter)
    a, b = Layer(), Layer()
    cap = (E(32, 21, 16, 9) & R(0, 0, 63, 21)) | E(32, 21, 19, 2.5)
    a.paint(cap, "light")
    b.paint(poly_line([(40, 15), (48, 8), (56, 3), (60, 1)], 3) | poly_line([(44, 12), (50, 4)], 2), "white")
    save("head_featcap", a, b)

    # Demon horns (warlock)
    a, b = Layer(), Layer()
    hl = poly_line([(22, 18), (19, 10), (14, 5), (9, 4), (12, 7)], 4) | poly_line([(9, 4), (6, 5)], 2)
    a.paint(hl | M(hl), "light")
    b.paint((R(0, 9, 63, 10) | R(0, 13, 63, 13)) & (hl | M(hl)), "dark", shade=False)
    save("head_horns", a, b)

    # Halo (priest)
    a = Layer()
    a.paint(ring(32, 6, 13, 3.6, 1.8), "white", shade=False)
    save("head_halo", a, outline=False)

    # Circlet with gem
    a, b = Layer(), Layer()
    a.paint(arc(32, 40, 23, 222, 318, 2.2), "light")
    b.paint(diamond(32, 17, 2.6), "white")
    save("head_circlet", a, b)

    # Mitre (priest/paladin)
    a, b = Layer(), Layer()
    m = P([(21, 22), (43, 22), (42, 10), (32, 0), (22, 10)])
    a.paint(m, "light")
    b.paint((R(30, 4, 33, 21) | R(25, 11, 38, 13)) & m, "light", shade=False)
    save("head_mitre", a, b)

    # Antlers (druid)
    a, b = Layer(), Layer()
    al = (poly_line([(24, 17), (20, 8), (17, 1)], 2.6) | poly_line([(21, 11), (13, 7), (9, 7)], 2.2) |
          poly_line([(19, 6), (23, 1)], 2) | poly_line([(15, 8), (11, 2)], 2))
    a.paint(al | M(al), "light")
    leaf = P([(26, 17), (22, 13), (27, 12)]) | P([(37, 17), (41, 13), (36, 12)])
    b.paint(leaf, "light")
    save("head_antlers", a, b)

    # Flower crown (druid)
    a, b = Layer(), Layer()
    a.paint(arc(32, 39, 22, 215, 325, 2.5), "mid")
    fl = set()
    for ang in (225, 250, 270, 290, 315):
        x = 32 + 22 * math.cos(math.radians(ang)); y = 39 + 22 * math.sin(math.radians(ang))
        fl |= E(x, y, 2.6, 2.6)
    b.paint(fl, "light")
    save("head_flowers", a, b)

    # Feather headdress (shaman)
    a, b = Layer(), Layer()
    a.paint(arc(32, 40, 22, 218, 322, 3), "light")
    fe = set()
    for ang in range(215, 330, 16):
        r0 = 22; x0 = 32 + r0 * math.cos(math.radians(ang)); y0 = 40 + r0 * math.sin(math.radians(ang))
        x1 = 32 + 35 * math.cos(math.radians(ang)); y1 = 40 + 35 * math.sin(math.radians(ang))
        fe |= L(x0, y0, x1, y1, 3.2)
    b.paint(fe - E(32, 40, 23.5, 23.5), "light")
    save("head_headdress", a, b)

    # Crown (universal)
    a, b = Layer(), Layer()
    cr = P([(19, 22), (45, 22), (46, 9), (40, 15), (37, 6), (32, 13), (27, 6), (24, 15), (18, 9)])
    a.paint(cr, "light")
    b.paint(diamond(32, 18, 2) | E(24, 19, 1.4, 1.4) | E(40, 19, 1.4, 1.4), "white")
    save("head_crown", a, b)

    # Party hat (universal)
    a, b = Layer(), Layer()
    ph = P([(25, 21), (39, 21), (33, 3)])
    a.paint(ph, "light")
    b.paint((L(26, 17, 37, 13, 1.5) | L(28, 11, 35, 8, 1.5)) & ph | E(33, 3, 2.2, 2.2), "white")
    save("head_partyhat", a, b)

    # Top hat (universal)
    a, b = Layer(), Layer()
    a.paint(R(23, 3, 40, 19) | E(32, 20, 16, 2.8), "light")
    b.paint(R(23, 14, 40, 16), "light", shade=False)
    save("head_tophat", a, b)

    # Pumpkin / skull helm? -> Skull cap (warlock/rogue fun)
    a, b = Layer(), Layer()
    sk = E(32, 16, 11, 9)
    a.paint(sk, "light")
    b.paint(E(28, 16, 2.4, 2.6) | E(36, 16, 2.4, 2.6) | R(31, 20, 32, 22), "dark", shade=False)
    save("head_skull", a, b)

# ================================================================ CHEST
def chest_items():
    base = CHEST & R(0, 38, 63, 63)
    # Plate
    a, b = Layer(), Layer()
    a.paint(base, "light")
    for y in (47, 53, 59): a.paint((R(0, y, 63, y)) & base, "mid", shade=False)
    pa = E(15, 44, 7.5, 5.5); pb = M(pa)
    b.paint(pa | pb, "light")
    b.paint({(13, 43), (17, 43), (46, 43), (50, 43)}, "dark", shade=False)
    save("chest_plate", a, b)
    # Robe
    a, b = Layer(), Layer()
    a.paint(base, "light")
    v = (L(25, 41, 32, 50, 2) | L(39, 41, 32, 50, 2) | R(31, 50, 32, 63)) & base
    belt = R(0, 52, 63, 54) & base
    b.paint(v | belt, "mid", shade=False)
    save("chest_robe", a, b)
    # Leather
    a, b = Layer(), Layer()
    a.paint(base, "mid")
    strap = (L(16, 42, 46, 62, 2.6) | R(0, 55, 63, 56)) & base
    b.paint(strap, "light", shade=False); b.paint(R(30, 54, 33, 57) & base, "white", shade=False)
    save("chest_leather", a, b)
    # Mail
    a, b = Layer(), Layer()
    a.paint(base, "light", shade=False)
    for (x, y) in base:
        if (x + y) % 3 == 0 and (x % 2 == 0): a.px[(x, y)] = (150, 150, 150, 255)
    b.paint(R(0, 55, 63, 57) & base, "mid")
    save("chest_mail", a, b)
    # Tabard
    a, b = Layer(), Layer()
    tab = R(24, 40, 39, 63) & BODY
    a.paint(tab, "light")
    b.paint(diamond(31.5, 51, 4.5), "light")
    save("chest_tabard", a, b)
    # Vestments (priest)
    a, b = Layer(), Layer()
    a.paint(base, "light")
    b.paint((R(23, 40, 26, 63) | R(37, 40, 40, 63)) & base, "light", shade=False)
    b.paint((star4(24.5, 58, 1.5) | star4(38.5, 58, 1.5)) & base, "white", shade=False)
    save("chest_vestment", a, b)
    # Leaf mantle (druid)
    a, b = Layer(), Layer()
    leaves = set()
    for i in range(9):
        ang = 200 + i * 17.5
        x = 32 + 19 * math.cos(math.radians(ang)) * -1
        y = 45 + 6 * math.sin(math.radians(i * 22))
        leaves |= E(12 + i * 5, 44 + (2 if i % 2 else 0), 3.6, 2.4)
    a.paint((leaves | (base & R(0, 41, 63, 46))), "light")
    b.paint(R(0, 47, 63, 48) & base, "mid", shade=False)
    save("chest_leaves", a, b)
    # Fur mantle (shaman / hunter)
    a, b = Layer(), Layer()
    fur = set()
    for i in range(8): fur |= E(13 + i * 5.4, 44, 3.6, 3.4)
    a.paint(fur | (base & R(0, 41, 63, 45)), "light")
    beads = set()
    for i in range(5): beads |= E(24 + i * 4, 50 - abs(2 - i) * 0.8, 1.3, 1.3)
    b.paint(beads | L(22, 47, 42, 47, 0.8), "white", shade=False)
    save("chest_furmantle", a, b)
    # Spiked shoulders (warlock / warrior)
    a, b = Layer(), Layer()
    a.paint(base, "dark")
    sp = E(15, 44, 7, 5) | P([(10, 42), (6, 33), (15, 40)]) | P([(15, 40), (16, 32), (20, 41)])
    b.paint(sp | M(sp), "light")
    save("chest_spiked", a, b)

# ================================================================ BACK
def back_items():
    a, b = Layer(), Layer()
    cape = P([(15, 40), (49, 40), (60, 64), (4, 64)])
    a.paint(cape - BODY, "light"); a.paint(cape & BODY, "mid")
    b.paint(E(17, 41, 2.2, 2.2) | E(46, 41, 2.2, 2.2), "white")
    save("back_cape", a, b)

    a, b = Layer(), Layer()
    q = P([(6, 53), (12, 56), (22, 33), (16, 30)])
    a.paint(q, "light")
    fe = set()
    for dx in (0, 3, 6):
        fe |= P([(15 + dx, 30), (13 + dx, 22), (17 + dx, 24)])
    b.paint(fe, "white")
    save("back_quiver", a, b)

    a, b = Layer(), Layer()
    wl = P([(16, 44), (2, 22), (8, 26), (6, 32), (12, 34), (9, 40), (16, 40)])
    a.paint(wl | M(wl), "light")
    b.paint(poly_line([(15, 42), (4, 24)], 1) | M(poly_line([(15, 42), (4, 24)], 1)), "dark", shade=False)
    save("back_batwings", a, b)

    a, b = Layer(), Layer()
    feathers = set()
    for i in range(5):
        ang = 200 + i * 22
        x = 16 + 14 * math.cos(math.radians(ang)); y = 42 + 14 * math.sin(math.radians(ang))
        feathers |= L(17, 44, x, y, 6 - i * 0.6)
    a.paint(feathers | M(feathers), "light")
    b.paint(E(9, 34, 3, 3) & feathers | M(E(9, 34, 3, 3) & feathers), "white")
    save("back_angelwings", a, b)

    a, b = Layer(), Layer()  # totem pack (shaman)
    t = R(46, 16, 54, 42)
    a.paint(t, "light")
    b.paint(R(46, 20, 54, 22) | R(46, 30, 54, 32) | E(48, 26, 1, 1) | E(52, 26, 1, 1) | P([(44, 16), (56, 16), (50, 10)]), "dark", shade=False)
    save("back_totempack", a, b)

    a, b = Layer(), Layer()  # vines (druid)
    v = arc(32, 48, 24, 150, 390, 2.2)
    a.paint(v - BODY - HEAD, "mid")
    lv = set()
    for ang in range(160, 380, 30):
        lv |= E(32 + 24 * math.cos(math.radians(ang)), 48 + 24 * math.sin(math.radians(ang)), 2.4, 1.6)
    b.paint(lv - BODY - HEAD, "light")
    save("back_vines", a, b)

# ================================================================ WEAPONS (right paw, down pose)
def weapons():
    # Sword
    a, b = Layer(), Layer()
    a.paint(P([(46, 51), (49, 52.5), (59, 24), (58, 20), (56, 23)]), "light")
    b.paint(L(41, 50, 52, 54, 2.4) | L(44, 58, 47, 52, 2.4) | E(43.5, 59, 1.5, 1.5), "mid")
    save("wpn_sword", a, b)
    # Greatsword (wider)
    a, b = Layer(), Layer()
    a.paint(P([(45, 50), (50, 52), (61, 22), (60, 14), (56, 21)]), "light")
    b.paint(L(39, 48, 54, 54, 3) | L(44, 59, 47, 52, 2.6) | diamond(47.5, 51, 1.6), "mid")
    save("wpn_greatsword", a, b)
    # Axe
    a, b = Layer(), Layer()
    b.paint(L(43, 62, 54, 20, 2.4), "mid")
    a.paint(P([(53, 22), (62, 18), (63, 32), (55, 31)]) | P([(53, 23), (48, 22), (49, 29), (54, 29)]), "light")
    save("wpn_axe", a, b)
    # Mace / hammer
    a, b = Layer(), Layer()
    b.paint(L(43, 62, 52, 26, 2.4), "mid")
    a.paint(P([(46, 21), (59, 24), (56, 34), (43, 31)]), "light")
    a.paint(L(45, 26, 57, 29, 1), "mid", shade=False)
    save("wpn_hammer", a, b)
    # Mace (spiked ball)
    a, b = Layer(), Layer()
    b.paint(L(43, 62, 51, 30, 2.4), "mid")
    a.paint(E(52, 26, 5, 5) | diamond(52, 19, 2.2) | diamond(59, 26, 2.2) | diamond(45, 26, 2.2) | diamond(55.5, 20.5, 1.6) | diamond(48.5, 20.5, 1.6), "light")
    save("wpn_mace", a, b)
    # Staff (orb)
    a, b = Layer(), Layer()
    b.paint(L(42, 63, 52, 15, 2.4), "mid")
    b.paint(poly_line([(50, 17), (49, 10), (52, 8)], 1.4) | poly_line([(54, 17), (56, 10), (53, 8)], 1.4), "mid", shade=False)
    a.paint(E(52.5, 11.5, 3.6, 3.6), "white")
    save("wpn_staff", a, b)
    # Crystal staff
    a, b = Layer(), Layer()
    b.paint(L(42, 63, 52, 18, 2.4), "mid")
    a.paint(P([(52, 3), (56, 11), (52, 19), (48, 11)]), "white")
    save("wpn_crystalstaff", a, b)
    # Wand
    a, b = Layer(), Layer()
    b.paint(L(44, 59, 53, 38, 2), "mid")
    a.paint(star4(54, 36, 3.5), "white")
    save("wpn_wand", a, b)
    # Dagger
    a, b = Layer(), Layer()
    a.paint(P([(47, 51), (50, 52), (56, 37), (54, 36)]), "light")
    b.paint(L(43, 50, 52, 54, 2) | L(44, 58, 47, 52, 2.2), "mid")
    save("wpn_dagger", a, b)
    # Bow
    a, b = Layer(), Layer()
    a.paint(arc(36, 46, 20, -62, 62, 2.8), "light")
    a1 = (36 + 20 * math.cos(math.radians(-62)), 46 + 20 * math.sin(math.radians(-62)))
    a2 = (36 + 20 * math.cos(math.radians(62)), 46 + 20 * math.sin(math.radians(62)))
    b.paint(L(a1[0], a1[1], a2[0], a2[1], 0.9), "white", shade=False)
    save("wpn_bow", a, b)
    # Crossbow / gun -> Rifle
    a, b = Layer(), Layer()
    a.paint(L(40, 50, 62, 36, 3), "dark")
    b.paint(P([(38, 52), (46, 47), (47, 53), (41, 58)]) | R(51, 40, 53, 44), "light")
    save("wpn_rifle", a, b)
    # Polearm / spear
    a, b = Layer(), Layer()
    b.paint(L(41, 63, 54, 14, 2.2), "mid")
    a.paint(P([(54, 3), (58, 13), (53, 17), (51, 12)]), "light")
    save("wpn_spear", a, b)
    # Scythe
    a, b = Layer(), Layer()
    b.paint(L(42, 63, 52, 12, 2.4), "mid")
    a.paint(P([(52, 12), (60, 10), (63, 16), (61, 23), (59, 16), (53, 15)]), "light")
    save("wpn_scythe", a, b)
    # Totem staff (shaman)
    a, b = Layer(), Layer()
    b.paint(L(43, 63, 50, 26, 2.4), "mid")
    a.paint(R(45, 12, 55, 27), "light")
    a.paint(E(48, 18, 1.2, 1.2) | E(52, 18, 1.2, 1.2) | R(48, 22, 52, 23), "dark", shade=False)
    a.paint(P([(43, 12), (57, 12), (50, 6)]), "mid")
    save("wpn_totem", a, b)
    # Fist / claw (druid/rogue fun) -> Moonglaive? keep Claw
    a, b = Layer(), Layer()
    for dx in (0, 4, 8):
        a.paint(poly_line([(42 + dx, 54), (44 + dx, 46), (48 + dx, 41)], 1.8), "light")
    b.paint(R(41, 54, 53, 57), "mid")
    save("wpn_claws", a, b)
    # Fishing pole (universal fun)
    a, b = Layer(), Layer()
    a.paint(L(43, 60, 60, 6, 1.6), "mid")
    b.paint(L(60, 6, 62, 30, 0.7) | E(62, 31, 1.4, 1.6), "white", shade=False)
    save("wpn_fishpole", a, b)
    # Torch (universal)
    a, b = Layer(), Layer()
    b.paint(L(44, 60, 50, 38, 2.6), "mid")
    a.paint(P([(46, 37), (54, 37), (52, 30), (51, 33), (50, 26), (48, 32), (47, 30)]), "white")
    save("wpn_torch", a, b)

# ================================================================ OFF-HANDS (left paw, down pose)
def offhands():
    a, b = Layer(), Layer()
    a.paint(E(11, 53, 8.5, 9.5), "light")
    b.paint(ring(11, 53, 8.5, 9.5, 1.5) | E(11, 53, 2.2, 2.2), "mid")
    save("off_roundshield", a, b)

    a, b = Layer(), Layer()
    ks = P([(3, 44), (19, 44), (19, 54), (11, 64), (3, 54)])
    a.paint(ks, "light")
    b.paint((R(10, 44, 12, 63) | R(3, 50, 19, 52)) & ks, "light", shade=False)
    save("off_kiteshield", a, b)

    a, b = Layer(), Layer()
    a.paint(R(4, 47, 18, 59), "light")
    b.paint(R(5, 48, 10, 58) | R(12, 48, 17, 58), "white", shade=False)
    b.erase(R(11, 47, 11, 59))
    save("off_tome", a, b)

    a, b = Layer(), Layer()
    a.paint(E(10, 45, 4.6, 4.6), "white")
    b.paint(ring(10, 45, 6.5, 6.5, 0.9), "white", shade=False)
    save("off_orb", a, b, outline=True)

    a, b = Layer(), Layer()
    a.paint(R(6, 40, 14, 56), "light")
    b.paint(R(6, 44, 14, 45) | R(6, 50, 14, 51) | P([(4, 40), (16, 40), (10, 35)]), "dark", shade=False)
    save("off_totem", a, b)

    a, b = Layer(), Layer()
    a.paint(E(11, 46, 5.5, 4.8) | R(8, 49, 14, 53), "white")
    b.paint(E(9, 46, 1.4, 1.6) | E(13, 46, 1.4, 1.6) | R(9, 51, 13, 51), "dark", shade=False)
    save("off_skull", a, b)

    a, b = Layer(), Layer()  # lantern
    a.paint(R(6, 44, 14, 54), "light")
    b.paint(R(8, 46, 12, 52), "white", shade=False)
    b.paint(arc(10, 44, 3, 180, 360, 1), "mid", shade=False)
    save("off_lantern", a, b)

    # offhand dagger/sword = mirrored weapons
    for w in ("dagger", "sword"):
        ia, ib = ART["wpn_%s_a" % w], ART["wpn_%s_b" % w]
        save_img("off_%s_a" % w, ia.transpose(Image.FLIP_LEFT_RIGHT))
        save_img("off_%s_b" % w, ib.transpose(Image.FLIP_LEFT_RIGHT))
        bb = BOUNDS["wpn_" + w]; BOUNDS["off_" + w] = (N - bb[2], bb[1], N - bb[0], bb[3])
        del BOUNDS["off_%s_a" % w]; del BOUNDS["off_%s_b" % w]

# ================================================================ ACCESSORIES
def accessories():
    a, b = Layer(), Layer()  # shades
    a.paint(R(20, 27, 28, 32) | R(35, 27, 43, 32), "dark")
    b.paint(R(28, 28, 35, 28) | {(21, 28), (22, 28), (36, 28), (37, 28)}, "white", shade=False)
    save("acc_shades", a, b)

    a, b = Layer(), Layer()  # monocle
    a.paint(ring(38.5, 29.5, 4.2, 4.2, 1.2), "light", shade=False)
    b.paint(poly_line([(42, 32), (44, 38), (44, 44)], 0.8), "light", shade=False)
    save("acc_monocle", a, b)

    a, b = Layer(), Layer()  # scarf
    sc = (E(32, 43, 16, 4) - E(32, 40, 13, 3)) | P([(36, 44), (44, 44), (42, 56), (37, 55)])
    a.paint(sc, "light")
    b.paint((R(0, 48, 63, 49) | R(0, 52, 63, 53)) & sc, "white", shade=False)
    save("acc_scarf", a, b)

    a, b = Layer(), Layer()  # bow tie
    a.paint(P([(26, 41), (31, 43), (26, 46)]) | P([(38, 41), (33, 43), (38, 46)]), "light")
    b.paint(R(31, 42, 32, 44), "mid")
    save("acc_bowtie", a, b)

    a, b = Layer(), Layer()  # bell collar
    a.paint(arc(32, 30, 14, 40, 140, 2), "light", shade=False)
    b.paint(E(32, 45.5, 2.4, 2.4), "white")
    save("acc_bell", a, b)

    a, b = Layer(), Layer()  # eyepatch
    a.paint(E(38.5, 29.5, 3.4, 3), "dark")
    b.paint(L(20, 22, 44, 36, 0.9) - E(38.5, 29.5, 3.4, 3), "dark", shade=False)
    save("acc_eyepatch", a, b)

    a, b = Layer(), Layer()  # flower behind ear
    fl = set()
    for k in range(5):
        ang = k * 72
        fl |= E(45 + 2.6 * math.cos(math.radians(ang)), 17 + 2.6 * math.sin(math.radians(ang)), 1.8, 1.8)
    a.paint(fl, "light")
    b.paint(E(45, 17, 1.2, 1.2), "white", shade=False)
    save("acc_flower", a, b)

    a, b = Layer(), Layer()  # mustache
    m = P([(31, 36), (26, 37), (22, 35), (24, 38), (30, 39), (32, 37)])
    a.paint(m | M(m), "dark")
    save("acc_mustache", a, b if b.px else None)

    a, b = Layer(), Layer()  # tiny pauldron pin / medal
    a.paint(diamond(24, 47, 3), "light")
    b.paint(R(23, 41, 25, 44), "mid", shade=False)
    save("acc_medal", a, b)

    a, b = Layer(), Layer()  # backpack strap hero bandolier
    a.paint(L(18, 42, 46, 62, 3) & CHEST, "mid")
    for k in range(4):
        b.paint(R(22 + k * 6, 44 + int(k * 4.3), 23 + k * 6, 46 + int(k * 4.3)), "white", shade=False)
    save("acc_bandolier", a, b)

# ================================================================ EFFECTS (smooth, 128px, white w/ alpha)
def fx_canvas(): return Image.new("RGBA", (128, 128), (0, 0, 0, 0))

def fx_put(im, x, y, a):
    if 0 <= x < 128 and 0 <= y < 128:
        r, g, b, a0 = im.getpixel((x, y))
        im.putpixel((x, y), (255, 255, 255, min(255, max(a0, int(a)))))

def fx_aura():
    im = fx_canvas()
    for y in range(128):
        for x in range(128):
            dx = (x - 64) / 60; dy = (y - 70) / 58
            d = math.sqrt(dx * dx + dy * dy)
            if d < 1: fx_put(im, x, y, 200 * (1 - d) ** 1.6)
    return im

def fx_sparkles(seed=3, n=14):
    im = fx_canvas(); rnd = random.Random(seed)
    for _ in range(n):
        cx, cy = rnd.uniform(8, 120), rnd.uniform(6, 118)
        if abs(cx - 64) < 30 and 30 < cy < 110: cx += 40 if cx > 64 else -40
        r = rnd.uniform(3, 7)
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                dx, dy = abs(x - cx), abs(y - cy)
                v = max(0, 1 - (dx * dy * 1.2 + (dx + dy) * 0.25) / r)
                fx_put(im, x, y, 255 * v)
    return im

def fx_flames():
    im = fx_canvas(); rnd = random.Random(11)
    for k in range(26):
        cx = rnd.uniform(14, 114); base = 126; h = rnd.uniform(18, 46) * (1.3 - abs(cx - 64) / 90)
        w = rnd.uniform(5, 9)
        for y in range(int(base - h), base):
            t = (base - y) / h
            hw = w * max(0.0, 1 - t) ** 0.7 * (0.6 + 0.4 * math.sin(t * 3.1))
            for x in range(int(cx - hw - 1), int(cx + hw + 2)):
                d = abs(x - cx) / (hw + 0.01)
                if d < 1: fx_put(im, x, y, 230 * (1 - d) * (1 - t * 0.7))
    return im

def fx_wisps():
    im = fx_canvas(); rnd = random.Random(5)
    for k in range(9):
        ang = rnd.uniform(0, math.tau); r0 = rnd.uniform(44, 56)
        for s in range(60):
            a2 = ang + s * 0.045; rr = r0 - s * 0.25
            cx = 64 + rr * math.cos(a2); cy = 68 + rr * math.sin(a2) * 0.9
            rad = 5 * (1 - s / 60) + 1
            for y in range(int(cy - rad), int(cy + rad + 1)):
                for x in range(int(cx - rad), int(cx + rad + 1)):
                    d = math.hypot(x - cx, y - cy) / rad
                    if d < 1: fx_put(im, x, y, 150 * (1 - d) * (1 - s / 60))
    return im

def fx_leaves():
    im = fx_canvas(); rnd = random.Random(9)
    for k in range(12):
        ang = k / 12 * math.tau; cx = 64 + 54 * math.cos(ang); cy = 66 + 52 * math.sin(ang)
        rot = rnd.uniform(0, math.pi)
        for y in range(int(cy - 7), int(cy + 8)):
            for x in range(int(cx - 7), int(cx + 8)):
                dx, dy = x - cx, y - cy
                u = dx * math.cos(rot) + dy * math.sin(rot); v = -dx * math.sin(rot) + dy * math.cos(rot)
                if (u / 6) ** 2 + (v / 2.8) ** 2 < 1:
                    fx_put(im, x, y, 120 if abs(v) < 0.6 else 235)
    return im

def fx_rays():
    im = fx_canvas()
    for y in range(128):
        for x in range(128):
            dx, dy = x - 64, y - 64; d = math.hypot(dx, dy)
            if 10 < d < 64:
                a = math.atan2(dy, dx)
                v = max(0, math.cos(a * 8)) ** 6 * (1 - d / 64) ** 1.2
                fx_put(im, x, y, 210 * v)
    return im

def fx_runes():
    im = fx_canvas()
    for y in range(128):
        for x in range(128):
            d = math.hypot(x - 64, y - 64)
            if 54 < d < 57 or 44 < d < 45.5: fx_put(im, x, y, 210)
    for k in range(8):
        ang = k / 8 * math.tau; cx = 64 + 50 * math.cos(ang); cy = 64 + 50 * math.sin(ang)
        glyph = [(0, -3, 0, 3), (-2, -1, 2, 1)] if k % 2 else [(-2, -3, 2, 3), (2, -3, -2, 3)]
        for x0, y0, x1, y1 in glyph:
            for s in range(13):
                t = s / 12
                fx_put(im, int(cx + x0 + (x1 - x0) * t), int(cy + y0 + (y1 - y0) * t), 255)
    return im

def fx_lightning():
    im = fx_canvas(); rnd = random.Random(21)
    for bolt in range(5):
        x, y = rnd.uniform(10, 118), 0
        side = -1 if x < 64 else 1
        while y < 120:
            nx = x + rnd.uniform(-9, 9); ny = y + rnd.uniform(8, 16)
            if abs(nx - 64) < 30: nx = 64 + side * 30
            for s in range(20):
                t = s / 19; px, py = x + (nx - x) * t, y + (ny - y) * t
                for oy in (-1, 0, 1):
                    for ox in (-1, 0, 1):
                        fx_put(im, int(px + ox), int(py + oy), 255 if ox == 0 and oy == 0 else 120)
            x, y = nx, ny
    return im

def fx_snow():
    im = fx_canvas(); rnd = random.Random(13)
    for k in range(18):
        cx, cy = rnd.uniform(6, 122), rnd.uniform(6, 122)
        if abs(cx - 64) < 32 and cy > 30: cx += 42 if cx > 64 else -42
        for ang in range(0, 180, 60):
            for s in range(-5, 6):
                fx_put(im, int(cx + s * math.cos(math.radians(ang))), int(cy + s * math.sin(math.radians(ang))), 235)
    return im

def fx_hearts():
    im = fx_canvas(); rnd = random.Random(17)
    for k in range(10):
        cx, cy = rnd.uniform(10, 118), rnd.uniform(8, 120); s = rnd.uniform(4, 6.5)
        if abs(cx - 64) < 32 and cy > 28: cx += 42 if cx > 64 else -42
        for y in range(int(cy - s * 1.5), int(cy + s * 1.5)):
            for x in range(int(cx - s * 1.5), int(cx + s * 1.5)):
                u = (x - cx) / s; v = -(y - cy) / s
                if (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0: fx_put(im, x, y, 235)
    return im

def fx_notes():
    im = fx_canvas(); rnd = random.Random(19)
    for k in range(8):
        cx, cy = rnd.uniform(10, 118), rnd.uniform(14, 120)
        if abs(cx - 64) < 32 and cy > 28: cx += 42 if cx > 64 else -42
        for y in range(int(cy - 3), int(cy + 4)):
            for x in range(int(cx - 4), int(cx + 4)):
                if ((x - cx) / 4) ** 2 + ((y - cy) / 3) ** 2 < 1: fx_put(im, x, y, 240)
        for y in range(int(cy - 14), int(cy)): fx_put(im, int(cx + 3), y, 240); fx_put(im, int(cx + 2), y, 240)
        for x in range(int(cx + 3), int(cx + 8)): fx_put(im, x, int(cy - 14), 240); fx_put(im, x, int(cy - 13), 240)
    return im

def fx_bubbles():
    im = fx_canvas(); rnd = random.Random(23)
    for k in range(14):
        cx, cy, r = rnd.uniform(8, 120), rnd.uniform(8, 120), rnd.uniform(3, 7)
        if abs(cx - 64) < 32 and cy > 28: cx += 42 if cx > 64 else -42
        for y in range(int(cy - r - 2), int(cy + r + 3)):
            for x in range(int(cx - r - 2), int(cx + r + 3)):
                d = math.hypot(x - cx, y - cy)
                if abs(d - r) < 1.1: fx_put(im, x, y, 230)
                elif d < r: fx_put(im, x, y, 40)
        fx_put(im, int(cx - r / 2), int(cy - r / 2), 255)
    return im

def fx_coins():
    im = fx_canvas(); rnd = random.Random(29)
    for k in range(10):
        cx, cy = rnd.uniform(8, 120), rnd.uniform(8, 120)
        if abs(cx - 64) < 32 and cy > 28: cx += 42 if cx > 64 else -42
        for y in range(int(cy - 5), int(cy + 6)):
            for x in range(int(cx - 4), int(cx + 5)):
                d = ((x - cx) / 4) ** 2 + ((y - cy) / 5) ** 2
                if d < 1: fx_put(im, x, y, 255 if d > 0.5 else 190)
    return im

EFFECTS = {
    "fx_aura": fx_aura, "fx_sparkles": fx_sparkles, "fx_flames": fx_flames, "fx_wisps": fx_wisps,
    "fx_leaves": fx_leaves, "fx_rays": fx_rays, "fx_runes": fx_runes, "fx_lightning": fx_lightning,
    "fx_snow": fx_snow, "fx_hearts": fx_hearts, "fx_notes": fx_notes, "fx_bubbles": fx_bubbles,
    "fx_coins": fx_coins,
}

# ================================================================ UI bits
# ================================================================ RACIAL ACCESSORIES
def race_accessories():
    # Human: Stormwind crest on the chest
    a, b = Layer(), Layer()
    crest = P([(26.5, 40), (37.5, 40), (37.5, 46), (32, 51), (26.5, 46)])
    a.paint(crest, "light")
    b.paint(diamond(32, 44.5, 2.6) | R(27, 40, 37, 41), "light", shade=False)
    save("acc_race_human", a, b)

    # Dwarf: braided beard and mustache
    a, b = Layer(), Layer()
    beard = P([(22, 35), (42, 35), (40.5, 43), (36, 49), (32, 52), (28, 49), (23.5, 43)])
    stache = P([(31, 33.5), (24, 34.5), (21.5, 37.5), (27, 36.5), (32, 35.5)])
    a.paint(beard | stache | M(stache), "light")
    b.paint(R(29, 45, 34, 46) | R(29, 48, 34, 49), "light", shade=False)
    save("acc_race_dwarf", a, b)

    # Night Elf: long ears and face markings
    a, b = Layer(), Layer()
    ear = P([(18, 25), (2, 12), (19, 19)])
    a.paint(ear | M(ear), "light")
    mark = L(21.5, 33, 25.5, 36, 1.3) | L(30, 18, 34, 18, 1.2)
    b.paint(mark | M(L(21.5, 33, 25.5, 36, 1.3)), "light", shade=False)
    save("acc_race_nightelf", a, b)

    # Gnome: goggles pushed up on the forehead
    a, b = Layer(), Layer()
    band = R(15, 19, 48, 21) & E(32, 30, 18, 14.5)
    frames = ring(25, 20, 4.4, 3.8, 1.4) | M(ring(25, 20, 4.4, 3.8, 1.4))
    a.paint(band | frames, "light")
    b.paint(E(25, 20, 3.0, 2.4) | M(E(25, 20, 3.0, 2.4)), "white")
    save("acc_race_gnome", a, b)

    # Orc: tusks and war paint
    a, b = Layer(), Layer()
    tusk = P([(26, 39), (29, 38.5), (27, 31.5)])
    a.paint(tusk | M(tusk), "white")
    paint = L(21, 36.5, 24, 39.5, 1.0) | L(19, 37, 22, 40, 1.0)
    b.paint(paint | M(paint), "light", shade=False)
    save("acc_race_orc", a, b)

    # Undead: stitches and a bandaged ear
    a, b = Layer(), Layer()
    st = L(36, 37, 45, 32, 0.9)
    for t in (0.2, 0.5, 0.8):
        x, y = 36 + 9 * t, 37 - 5 * t
        st |= L(x - 1, y - 1.5, x + 1, y + 1.5, 0.8)
    a.paint(st, "light", shade=False)
    b.paint(P([(16, 12), (24, 16.5), (22, 20), (15, 15.5)]), "light")
    save("acc_race_undead", a, b)

    # Tauren: horns and a nose ring
    a, b = Layer(), Layer()
    horn = poly_line([(17.5, 23), (11, 20), (7, 15), (7.5, 9)], 3.6) | poly_line([(7.5, 9), (9, 6)], 2)
    a.paint(horn | M(horn), "light")
    b.paint(ring(31.5, 36, 2.4, 2.2, 0.9), "light", shade=False)
    save("acc_race_tauren", a, b)

    # Troll: big tusks and a mohawk
    a, b = Layer(), Layer()
    tusk = poly_line([(27, 38.5), (24, 37), (22, 33), (23, 29.5)], 2.2)
    a.paint(tusk | M(tusk), "white")
    hawk = P([(25, 18.5), (26, 9), (29, 5), (32, 3), (35, 5), (38, 9), (39, 18.5)])
    b.paint(hawk - E(32, 30, 17, 13.5) | (hawk & R(0, 0, 63, 17)), "light")
    b.paint(L(32, 4, 32, 16, 1), "dark", shade=False)
    save("acc_race_troll", a, b)

    # Skyborne: feathers swept back from the temples
    a, b = Layer(), Layer()
    fe = set()
    for ang, ln in ((200, 14), (215, 16), (230, 13)):
        x1 = 17 + ln * math.cos(math.radians(ang)); y1 = 24 + ln * math.sin(math.radians(ang))
        fe |= L(17, 24, x1, y1, 3.2)
    a.paint(fe | M(fe), "light")
    tips = set()
    for ang, ln in ((200, 14), (215, 16), (230, 13)):
        tips |= E(17 + ln * math.cos(math.radians(ang)), 24 + ln * math.sin(math.radians(ang)), 1.6, 1.6)
    b.paint((tips | M(tips)), "white", shade=False)
    save("acc_race_skyborne", a, b)

# ================================================================ CAT SKINS (overlays on the fur)
def skins():
    # bold tiger stripes on head and body
    st = set()
    for x0, y0, x1, y1 in ((24, 17, 26, 23), (32, 16, 32, 23), (40, 17, 38, 23),
                           (15, 26, 20, 28), (15, 31, 19, 32),
                           (14, 46, 22, 49), (13, 52, 21, 54), (14, 58, 21, 60),
                           (24, 44, 27, 50), (30, 46, 33, 52)):
        st |= L(x0, y0, x1, y1, 2.0)
    st |= M(L(15, 26, 20, 28, 2.0) | L(15, 31, 19, 32, 2.0) | L(14, 46, 22, 49, 2.0) | L(13, 52, 21, 54, 2.0) | L(14, 58, 21, 60, 2.0))
    a = Layer(); a.paint(st & FUR, "light", shade=False)
    save("skin_stripes", a, outline=False)

    # skeleton: ribs and a skull mask
    a = Layer()
    bones = R(31, 40, 32, 62)
    for y in (44, 48, 52, 56):
        bones |= arc(32, y - 6, 9, 50, 130, 1.4)
    bones |= ring(24.5, 29.5, 3.6, 3.4, 1.2) | M(ring(24.5, 29.5, 3.6, 3.4, 1.2)) | R(30, 33, 33, 34)
    a.paint(bones & FUR, "light", shade=False)
    save("skin_bones", a, outline=False)

    # mechanical: panel lines (a) and rivets (b)
    a, b = Layer(), Layer()
    lines = (L(15, 24, 49, 24, 1) | L(32, 16, 32, 24, 1) | L(14, 46, 50, 46, 1) | L(32, 46, 32, 63, 1)) & FUR
    a.paint(lines, "light", shade=False)
    rv = set()
    for x, y in ((20, 21), (44, 21), (20, 43), (44, 43), (22, 50), (42, 50), (22, 59), (42, 59)):
        rv |= E(x, y, 1.1, 1.1)
    b.paint(rv & FUR, "white", shade=False)
    save("skin_plates", a, b, outline=False)

    # lion mane behind the head
    a = Layer()
    mane = set()
    for k in range(16):
        ang = k / 16 * 2 * math.pi
        mane |= E(32 + 19 * math.cos(ang), 30 + 16 * math.sin(ang), 5, 5)
    a.paint(mane - E(32, 30, 15, 12), "light")
    save("skin_mane", a)

    # glowing eyes (drawn over the face)
    a = Layer()
    for ex in (24, 38):
        a.paint(R(ex, 28, ex + 1, 31), "white", shade=False)
        a.paint({(ex - 1, 29), (ex + 2, 29), (ex - 1, 30), (ex + 2, 30)}, "white", shade=False, alpha=110)
    save("skin_eyes", a, outline=False)

    # stars and sparkles in the fur
    a = Layer()
    sm = set()
    for x, y in ((22, 22), (41, 19), (18, 50), (44, 55), (30, 58), (37, 45), (25, 40)):
        sm |= star4(x, y, 1.8)
    a.paint(sm & FUR, "white", shade=False)
    save("skin_stars", a, outline=False)

# ================================================================ ADVENTURE SCENES (pixel art, 128x64 -> 256x128)
def scene_canvas():
    return Image.new("RGBA", (128, 64), (0, 0, 0, 255))

def vgrad(im, y0, y1, c0, c1):
    px = im.load()
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        c = tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3)) + (255,)
        for x in range(128): px[x, y] = c

def fill(im, pts, col):
    px = im.load()
    for (x, y) in pts:
        if 0 <= x < 128 and 0 <= y < 64: px[x, y] = col + (255,) if len(col) == 3 else col

def disc(cx, cy, r):
    return {(x, y) for x in range(int(cx - r - 1), int(cx + r + 2)) for y in range(int(cy - r - 1), int(cy + r + 2))
            if (x + .5 - cx) ** 2 + (y + .5 - cy) ** 2 <= r * r}

def rect(x0, y0, x1, y1):
    return {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}

def tri(pts):
    s = set()
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        for x in range(int(min(xs)), int(max(xs)) + 1):
            px, py = x + .5, y + .5; inside = False; j = len(pts) - 1
            for i in range(len(pts)):
                xi, yi = pts[i]; xj, yj = pts[j]
                if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi: inside = not inside
                j = i
            if inside: s.add((x, y))
    return s

def scene_elwynn():
    im = scene_canvas(); rnd = random.Random(4)
    vgrad(im, 0, 40, (110, 170, 235), (190, 225, 250))
    fill(im, disc(100, 10, 5), (255, 245, 200))
    for cx, cy, r in ((20, 12, 5), (28, 11, 6), (36, 13, 4), (70, 8, 4), (77, 7, 5)):
        fill(im, disc(cx, cy, r), (250, 252, 255))
    for x in range(128):  # far hills
        h = 30 + int(4 * math.sin(x / 11) + 3 * math.sin(x / 5 + 1))
        fill(im, rect(x, h, x, 44), (70, 120, 70))
    # Goldshire inn: stone walls, blue roof
    fill(im, rect(78, 30, 100, 44), (205, 195, 170)); fill(im, rect(78, 30, 100, 31), (150, 140, 120))
    fill(im, tri([(75, 31), (89, 20), (103, 31)]), (50, 80, 160))
    fill(im, rect(86, 37, 89, 44), (90, 60, 40)); fill(im, rect(81, 33, 83, 35), (255, 220, 120)); fill(im, rect(94, 33, 96, 35), (255, 220, 120))
    fill(im, rect(97, 18, 99, 27), (170, 160, 140))
    vgrad(im, 44, 64, (95, 160, 70), (60, 120, 45))
    px = im.load()
    for y in range(46, 64):  # dirt path
        w = 5 + (y - 46) // 2
        for x in range(60 - w, 60 + w):
            if 0 <= x < 128: px[x, y] = (165, 130, 85, 255) if (x + y) % 7 else (140, 110, 70, 255)
    for tx in (6, 18, 40, 112, 122):  # oak trees
        th = rnd.randint(14, 20)
        fill(im, rect(tx - 1, 46 - th // 2, tx + 1, 48), (95, 65, 40))
        for k in range(5):
            fill(im, disc(tx + rnd.randint(-4, 4), 46 - th + rnd.randint(-3, 3), rnd.uniform(4, 6.5)), (40 + k * 6, 100 + k * 8, 45))
    for _ in range(140):
        x, y = rnd.randrange(128), rnd.randrange(48, 64)
        if not (abs(x - 60) < 5 + (y - 46) // 2): px[x, y] = (120, 185, 85, 255)
    for _ in range(12):
        x, y = rnd.randrange(128), rnd.randrange(50, 64)
        px[x, y] = rnd.choice([(250, 220, 80, 255), (240, 120, 160, 255), (255, 255, 255, 255)])
    return im

def scene_westfall():
    im = scene_canvas(); rnd = random.Random(8)
    vgrad(im, 0, 40, (235, 170, 110), (250, 225, 170))
    fill(im, disc(24, 12, 6), (255, 240, 190))
    for x in range(128):
        h = 34 + int(3 * math.sin(x / 9) + 2 * math.sin(x / 4))
        fill(im, rect(x, h, x, 44), (170, 140, 80))
    # red farmhouse / barn
    fill(im, rect(14, 30, 34, 44), (165, 55, 45)); fill(im, tri([(11, 31), (24, 21), (37, 31)]), (95, 60, 45))
    fill(im, rect(22, 36, 26, 44), (70, 40, 30)); fill(im, rect(16, 33, 18, 35), (255, 220, 140))
    # windmill
    fill(im, rect(98, 22, 104, 44), (215, 200, 170)); fill(im, tri([(97, 23), (101, 15), (105, 23)]), (120, 80, 60))
    for ang in (0.6, 0.6 + math.pi / 2, 0.6 + math.pi, 0.6 + 3 * math.pi / 2):
        for r in range(1, 13):
            x, y = 101 + r * math.cos(ang), 20 + r * math.sin(ang)
            fill(im, {(int(x), int(y)), (int(x) + 1, int(y))}, (240, 235, 220))
    vgrad(im, 44, 64, (215, 180, 80), (180, 140, 55))
    px = im.load()
    for y in range(46, 64, 3):  # wheat rows
        for x in range(128):
            if (x + y) % 4 == 0: px[x, y] = (240, 205, 100, 255)
    for x in range(0, 128, 6):  # fence
        fill(im, rect(x, 45, x, 49), (110, 75, 45))
    fill(im, rect(0, 46, 127, 46), (130, 90, 55))
    # scarecrow
    fill(im, rect(70, 40, 70, 52), (100, 70, 40)); fill(im, rect(66, 43, 74, 43), (100, 70, 40))
    fill(im, disc(70.5, 39, 2.2), (230, 200, 120)); fill(im, rect(67, 44, 73, 48), (90, 110, 160))
    return im

def scene_fishing():
    im = scene_canvas(); rnd = random.Random(12)
    vgrad(im, 0, 30, (120, 175, 235), (200, 230, 250))
    for cx, cy, r in ((25, 9, 5), (33, 8, 6), (90, 12, 4)):
        fill(im, disc(cx, cy, r), (250, 252, 255))
    for x in range(128):  # far shore with trees
        h = 24 + int(2 * math.sin(x / 7) + 2 * math.sin(x / 3))
        fill(im, rect(x, h, x, 30), (60, 105, 60))
    vgrad(im, 30, 64, (70, 130, 190), (30, 70, 130))
    px = im.load()
    for _ in range(90):
        x, y = rnd.randrange(128), rnd.randrange(32, 64)
        px[x, y] = (150, 200, 240, 255)
        if x + 1 < 128: px[x + 1, y] = (150, 200, 240, 255)
    # little wooden pier
    fill(im, rect(0, 40, 22, 43), (130, 90, 55)); fill(im, rect(4, 43, 5, 56), (95, 65, 40)); fill(im, rect(17, 43, 18, 56), (95, 65, 40))
    return im

def ui_bobber():
    a = Layer()
    a.paint(E(32, 26, 11, 10) & R(0, 0, 63, 26), color=(220, 40, 40))
    a.paint(E(32, 26, 11, 10) & R(0, 27, 63, 63), color=(245, 245, 245))
    a.paint(R(31, 6, 32, 16), color=(90, 70, 50))
    a.paint(R(20, 26, 43, 27), color=(30, 24, 36))
    save("ui_bobber", a)

def mob_shadow():
    """Last-resort enemy picture: a shadowy pixel monster with glowing eyes (64x64)."""
    a = Layer()
    body = E(32, 40, 18, 20) | E(32, 22, 12, 11) | P([(20, 16), (16, 4), (26, 13)]) | M(P([(20, 16), (16, 4), (26, 13)]))
    a.paint(body, color=(60, 45, 75))
    a.paint(E(26, 22, 2.5, 2) | E(38, 22, 2.5, 2), color=(255, 90, 70))
    a.paint(P([(26, 30), (38, 30), (32, 34)]), color=(30, 20, 35))
    save("mob_shadow", a)

def ui_bits():
    # floating heart (for petting) 32x32 logical drawn on 64 canvas
    a = Layer()
    h = set()
    for y in range(N):
        for x in range(N):
            u = (x + .5 - 32) / 20; v = -(y + .5 - 34) / 20
            if (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0: h.add((x, y))
    a.paint(h, color=(255, 90, 130)); a.paint({p for p in h if p[1] < 26 and p[0] < 28 and p[0] > 18 and p[1] > 18}, color=(255, 190, 210))
    save("ui_heart", a)
    # TapCoin: gold coin with paw print
    a = Layer()
    a.paint(E(32, 32, 28, 28), color=(240, 180, 40)); a.paint(E(32, 32, 23, 23), color=(255, 214, 80))
    pawp = E(32, 38, 8, 6.5)
    for bx, by in ((-8, -6), (-3, -11), (3, -11), (8, -6)): pawp |= E(32 + bx, 38 + by, 3, 3.6)
    a.paint(pawp, color=(196, 130, 20))
    save("ui_coin", a)

# ================================================================ main
def main():
    os.makedirs(OUT, exist_ok=True)
    cat_fur()
    for side in "LR":
        paw(True, side); paw(False, side)
    for k in ("normal", "blink", "happy", "focus", "sparkle"): face(k)
    mob_shadow(); ui_bobber()
    patterns(); head_items(); chest_items(); back_items(); weapons(); offhands(); accessories(); race_accessories(); skins(); ui_bits()

    count = 0
    for name, im in ART.items():
        big = im.resize((N * UP, N * UP), Image.NEAREST)
        write_tga(big, os.path.join(OUT, name + ".tga")); count += 1
    for name, fn in EFFECTS.items():
        im = fn(); ART[name] = im
        write_tga(im.resize((256, 256), Image.BILINEAR), os.path.join(OUT, name + ".tga")); count += 1
        BOUNDS[name] = (0, 0, N, N)

    for name, fn in (("bg_elwynn", scene_elwynn), ("bg_westfall", scene_westfall), ("bg_fishing", scene_fishing)):
        im = fn(); im.save(os.path.join(HERE, "..", "media", name + ".png"))
        write_tga(im.resize((256, 128), Image.NEAREST), os.path.join(OUT, name + ".tga")); count += 1

    with open(os.path.join(HERE, "..", "ArtData.lua"), "w") as f:
        f.write("-- Generated by tools/make_art.py. Do not edit by hand.\n")
        f.write("local _, TCF = ...\nTCF.ArtBounds = {\n")
        for k in sorted(BOUNDS):
            x0, y0, x1, y1 = BOUNDS[k]
            f.write('  ["%s"] = {%.4f, %.4f, %.4f, %.4f},\n' % (k, x0 / N, y0 / N, x1 / N, y1 / N))
        f.write("}\nTCF.PART_B = {\n")
        for k in sorted(ART):
            if k.endswith("_b"):
                f.write('  ["%s"] = true,\n' % k[:-2])
        f.write("}\n")
    print("wrote %d textures" % count)

if __name__ == "__main__":
    main()
