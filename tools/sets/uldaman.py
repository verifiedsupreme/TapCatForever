"""Uldaman set (1.6): titan stone and amethyst crystal. Carved stone with glowing blue titan runes,
violet crystals that catch the light, spinning shards floating around the crown and the staff, stones
rising around the cat. Each piece is guaranteed from one Uldaman boss in Adventure until owned.
  python3 tools/sets/uldaman.py            -> Art/v/k_uld_*.tga, Art/uld_*.tga, Sets/Uldaman.lua
  python3 tools/set_preview.py tools/sets/uldaman.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: carved titan stone, bronze, amethyst, rune blue
STONE, STONE2, STONE3, STONED = "#8f857a", "#6e655c", "#b2a796", "#4e4740"
BRONZE, BRONZEL = "#c4893a", "#efc27a"
AME, AME2, AME3, AMEL = "#9a62f2", "#c49dff", "#6a35c8", "#f0e4ff"
RUNE, RUNEL = "#3fdcff", "#c6f6ff"

def frames(n, fn):
    return {"fl%d" % (k + 1): fn(k) for k in range(n)}

def sprite(inner, S=32):
    """a small particle sprite: the drawing centred in an exact S x S box (faint corner dots fix the crop)"""
    dots = '<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/><rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S)
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)

def blur(s): return '<g filter="url(#blur)">%s</g>' % s

def crystal_pts(bx, by, ang, L, W):
    """a hexagonal crystal standing on (bx, by), leaning ang degrees, L long, W wide"""
    a = math.radians(ang)
    ux, uy = math.sin(a), -math.cos(a)        # along the crystal
    vx, vy = math.cos(a), math.sin(a)         # across
    h = W / 2.0
    side = L - W * 0.9
    pt = lambda t, s: (bx + ux * t + vx * s, by + uy * t + vy * s)
    return [pt(0, -h), pt(side, -h), pt(L, 0), pt(side, h), pt(0, h)], pt(0, 0), pt(L, 0), pt(side, 0)

def crystal(bx, by, ang, L, W, ink=4.5, cols=(AME, AME2, AMEL)):
    pts, base, tip, mid = crystal_pts(bx, by, ang, L, W)
    d = "M " + " L ".join("%.1f %.1f" % p for p in pts) + " Z"
    s = P(d, cols[0], ink)
    # the lit facet: the left half
    s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (pts[0] + pts[1] + tip + base), cols[1], 0)
    s += LN("M %.1f %.1f L %.1f %.1f L %.1f %.1f" % (base + mid + tip), darker(cols[0], .8), 2)
    # a highlight stripe
    a = math.radians(ang); vx, vy = math.cos(a), math.sin(a)
    hx, hy = -vx * W * 0.24, -vy * W * 0.24
    p0 = (base[0] + (mid[0] - base[0]) * 0.15 + hx, base[1] + (mid[1] - base[1]) * 0.15 + hy)
    p1 = (base[0] + (mid[0] - base[0]) * 0.8 + hx, base[1] + (mid[1] - base[1]) * 0.8 + hy)
    s += LN("M %.1f %.1f L %.1f %.1f" % (p0 + p1), cols[2], max(1.5, W * 0.1))
    return s

def crystal_mask(bx, by, ang, L, W):
    pts = crystal_pts(bx, by, ang, L, W)[0]
    return P("M " + " L ".join("%.1f %.1f" % p for p in pts) + " Z", "#ffffff", 0)

def rune_glyph(x, y, r, col=RUNE, w=2.5):
    """a small titan rune: a circle with a cross and a notch"""
    return ('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="%s"/>' % (x, y, r, col, w)
            + LN("M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f" % (x, y - r * 1.4, x, y + r * 1.4, x - r * 0.7, y, x + r * 0.7, y), col, w))

# ---------------------------------------------------------------- crown (head space)
CROWN_CR = [  # base x, base y, angle, length, width
    (62, 80, -68, 40, 18), (194, 80, 68, 40, 18),
    (80, 72, -44, 56, 24), (176, 72, 44, 56, 24),
    (104, 68, -20, 68, 28), (152, 68, 20, 68, 28),
    (128, 70, 0, 82, 36),
]
def crown():
    s = ""
    for c in CROWN_CR: s += crystal(*c)
    band = "M 48 100 Q 128 84 208 100 L 204 66 Q 128 50 52 66 Z"
    s += P(band, STONE, 5)
    for x0 in (64, 92, 164, 192):
        s += P("M %d %d L %d %d L %d %d L %d %d Z" % (x0 - 9, 92, x0 - 7, 68, x0 + 7, 66, x0 + 9, 90), STONE3, 0)
    s += LN("M 56 94 Q 128 80 200 94", STONED, 2.5) + LN("M 58 71 Q 128 57 198 71", STONE3, 3)
    for x in (70, 186): s += rune_glyph(x, 82, 4.5)
    # the titan eye
    s += CI(128, 80, 15, BRONZE, 4.5) + CI(128, 80, 9, "#1b4d63", 3) + CI(128, 80, 5, RUNE, 0) + CI(126, 78, 2, "#ffffff", 0)
    return HEAD(s)

def crown_mask():
    return HEAD("".join(crystal_mask(*c) for c in CROWN_CR))

def crown_runes():
    return HEAD(blur(CI(128, 80, 16, RUNE, 0)) + CI(128, 80, 6, RUNEL, 0) + rune_glyph(70, 82, 4.5, RUNEL, 2.5) + rune_glyph(186, 82, 4.5, RUNEL, 2.5)
                + blur(rune_glyph(70, 82, 6, RUNE, 5) + rune_glyph(186, 82, 6, RUNE, 5)))

def shard(x, y, k, r=9, phase=0):
    """a small floating crystal shard turning around: frame k squeezes it like a spinning coin"""
    sq = (1.0, 0.62, 0.22, 0.62)[(k + phase) % 4]
    w = r * 0.62 * sq + 0.8
    d = "M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x, y - r * 1.5, x + w, y, x, y + r * 1.1, x - w, y)
    s = P(d, AME, 3) + P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x, y - r * 1.5, x - w, y, x, y + r * 1.1), AME2 if (k + phase) % 4 < 2 else AME3, 0)
    return s

def crown_shards(k):
    bob = (0, -2, -3, -2)
    return HEAD(shard(34, 26 + bob[k], k) + shard(222, 26 + bob[(k + 2) % 4], k, phase=2) + shard(128, -2 + bob[(k + 1) % 4], k, r=6, phase=1))

# ---------------------------------------------------------------- shoulders (body space)
SH_CR = [(-26, -8, -62, 34, 15), (-14, -16, -32, 44, 19), (2, -18, -6, 40, 17), (16, -14, 18, 28, 13)]
def pauldron():
    cx, cy = SH_C
    s = ""
    for dx, dy, a, L, W in SH_CR: s += crystal(cx + dx, cy + dy, a, L, W, ink=4)
    slab = "M %d %d L %d %d Q %d %d %d %d L %d %d Q %d %d %d %d L %d %d Q %d %d %d %d Z" % (
        cx - 36, cy + 12, cx - 34, cy - 10, cx - 30, cy - 22, cx - 12, cy - 22, cx + 22, cy - 18,
        cx + 34, cy - 14, cx + 32, cy + 4, cx + 26, cy + 14, cx - 4, cy + 24, cx - 36, cy + 12)
    s += P(slab, STONE, 5)
    s += P("M %d %d L %d %d L %d %d L %d %d Z" % (cx - 30, cy - 8, cx - 26, cy - 18, cx - 2, cy - 18, cx - 8, cy - 6), STONE3, 0)
    s += LN("M %d %d L %d %d L %d %d" % (cx - 32, cy + 6, cx - 4, cy + 16, cx + 28, cy + 4), STONED, 2.5)
    s += LN("M %d %d L %d %d L %d %d L %d %d" % (cx - 24, cy + 2, cx - 10, cy - 4, cx + 4, cy + 4, cx + 18, cy - 4), "#1b4d63", 4)
    s += LN("M %d %d L %d %d L %d %d L %d %d" % (cx - 24, cy + 2, cx - 10, cy - 4, cx + 4, cy + 4, cx + 18, cy - 4), RUNE, 2)
    for x, y in ((cx - 26, cy + 12), (cx + 20, cy + 8)): s += CI(x, y, 3, BRONZE, 2)
    return BOTH(s)

def pauldron_mask():
    cx, cy = SH_C
    return BOTH("".join(crystal_mask(cx + dx, cy + dy, a, L, W) for dx, dy, a, L, W in SH_CR))

def pauldron_runes():
    cx, cy = SH_C
    d = "M %d %d L %d %d L %d %d L %d %d" % (cx - 24, cy + 2, cx - 10, cy - 4, cx + 4, cy + 4, cx + 18, cy - 4)
    return BOTH(blur(LN(d, RUNE, 7)) + LN(d, RUNEL, 2.5))

# ---------------------------------------------------------------- chest (body space)
DISC = (128, 162)
CIRCUIT = ["M 128 128 L 128 144", "M 128 180 L 128 196 L 112 206", "M 128 196 L 144 206",
           "M 110 162 L 92 162 L 84 150 L 84 132", "M 146 162 L 164 162 L 172 150 L 172 132",
           "M 116 176 L 98 190 L 74 190", "M 140 176 L 158 190 L 182 190"]
def chest():
    s = P(BODY_OUT, STONE, 5)
    for d in ("M 80 124 L 112 128 L 106 150 L 74 146 Z", "M 176 124 L 144 128 L 150 150 L 182 146 Z",
              "M 66 196 L 98 198 L 96 212 L 62 212 Z", "M 190 196 L 158 198 L 160 212 L 194 212 Z"):
        s += P(d, STONE3, 0)
    for d in CIRCUIT: s += LN(d, STONED, 9) + LN(d, "#1b4d63", 5)
    for x, y in ((84, 132), (172, 132), (74, 190), (182, 190), (112, 206), (144, 206)): s += CI(x, y, 4, BRONZE, 2.5)
    # the titan disc
    s += CI(DISC[0], DISC[1], 21, BRONZE, 5) + CI(DISC[0], DISC[1], 14, "#1b4d63", 3.5)
    for i in range(8):
        a = math.radians(i * 45)
        s += LN("M %.1f %.1f L %.1f %.1f" % (DISC[0] + math.cos(a) * 15, DISC[1] + math.sin(a) * 15, DISC[0] + math.cos(a) * 20, DISC[1] + math.sin(a) * 20), BRONZEL, 2)
    s += CI(DISC[0], DISC[1], 7, RUNE, 0) + CI(DISC[0] - 2, DISC[1] - 2, 2.5, "#ffffff", 0)
    return s

def chest_mask():
    return "".join(LN(d, "#ffffff", 5) for d in CIRCUIT) + CI(DISC[0], DISC[1], 13, "#ffffff", 0)

def chest_core():
    return blur(CI(DISC[0], DISC[1], 18, RUNE, 0)) + CI(DISC[0], DISC[1], 8, RUNEL, 0)

# ---------------------------------------------------------------- cape (side drapes)
def cape_crystals():
    out = []
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        sgn = -1 if pts[0][0] < 128 else 1
        for i in (2, 4, 6):
            x, y = pts[i]
            out.append((x + sgn * 2, y + 2, sgn * (62 + i * 4), 22 + i * 1.5, 12))
    return out

def cape():
    s = ""
    for bx, by, a, L, W in cape_crystals(): s += crystal(bx, by, a, L, W, ink=3.5)
    s += "".join(P(p, STONE2, 5) for p in DRAPE_OUT) + "".join(P(p, AME3, 3) for p in DRAPE_IN)
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        d = "M " + " L ".join("%.1f %.1f" % (x + (5 if x < 128 else -5), y) for x, y in pts)
        s += LN(d, STONE3, 4)
    for x0, sg in ((56, 1), (200, -1)):
        s += LN("M %d 140 L %d 156 L %d 170 L %d 186" % (x0, x0 - sg * 6, x0 - sg * 2, x0 - sg * 8), STONED, 2.5)
        s += rune_glyph(x0 - sg * 6, 168, 3.5)
    return s

def cape_mask():
    return "".join(crystal_mask(*c) for c in cape_crystals())

def cape_glow():
    return blur("".join(crystal_mask(*c).replace("#ffffff", AME2) for c in cape_crystals()))

# ---------------------------------------------------------------- staff (right paw)
STAFF_CR = [(0, -128, 0, 48, 22), (-6, -126, -28, 34, 15), (6, -126, 28, 34, 15)]
def staff():
    s = RC(-5, -124, 10, 160, STONED, 4, 4)
    for y in (-96, -50, -4): s += RC(-8, y, 16, 10, BRONZE, 3, 3)
    s += CI(0, 36, 7, BRONZE, 3.5)
    # bronze claw holding the cluster
    claw = "M -4 -112 Q -24 -118 -26 -142 Q -16 -128 -6 -126 Z"
    s += P(claw, BRONZE, 3.5) + mirror(P(claw, BRONZE, 3.5), 0)
    for c in STAFF_CR[1:] + STAFF_CR[:1]: s += crystal(*c, ink=4)
    s += CI(0, -118, 8, BRONZE, 3.5) + CI(0, -118, 4, RUNE, 0)
    return RHAND(s)

def staff_mask():
    return RHAND("".join(crystal_mask(*c) for c in STAFF_CR))

def staff_glow():
    return RHAND(blur(CI(0, -150, 30, AME2, 0)) + blur(CI(0, -118, 10, RUNE, 0)))

def staff_shards(k):
    s = ""
    for i in range(3):
        a = math.radians(k * 30 + i * 120)
        x, y = math.cos(a) * 30, -150 + math.sin(a) * 9
        s += shard(x, y, k, r=6, phase=i)
    return RHAND(s)

# ---------------------------------------------------------------- aura: rune circle, rising stones
def rune_ring(k):
    cx, cy, rx, ry = 128, 214, 112, 20
    s = '<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="none" stroke="%s" stroke-width="7"/>' % (cx, cy, rx, ry, "#1b4d63")
    s += '<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="none" stroke="%s" stroke-width="2.5"/>' % (cx, cy, rx, ry, RUNE)
    s += '<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="none" stroke="%s" stroke-width="2" stroke-dasharray="6 8"/>' % (cx, cy, rx - 14, ry - 5, RUNE)
    for i in range(10):
        a = math.radians(i * 36 + k * 12)
        s += rune_glyph(cx + math.cos(a) * rx, cy + math.sin(a) * ry, 3.2, RUNEL, 2)
    return blur('<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="none" stroke="%s" stroke-width="10"/>' % (cx, cy, rx, ry, RUNE)) + s

def rock():
    d = "M -10 -6 L -2 -12 L 9 -8 L 12 3 L 4 11 L -8 9 L -12 1 Z"
    return sprite(P(d, STONE, 2.5) + P("M -10 -6 L -2 -12 L 9 -8 L 2 -2 Z", STONE3, 0) + LN("M -6 4 L 2 2", STONED, 1.6))

def ame_shard():
    return sprite('<g transform="rotate(18)">%s</g>' % (P("M 0 -14 L 6 0 L 0 12 L -6 0 Z", AME, 2.5) + P("M 0 -14 L -6 0 L 0 12 Z", AME2, 0)))

RUNEC = [0.3, 0.85, 1.0]
SET = {
    "key": "uld", "name": "Uldaman", "zone": "uld", "lua": "Uldaman", "file": "uldaman",
    "about": "Uldaman set: titan stone and amethyst crystal, each piece guaranteed from one Uldaman boss in Adventure until owned.",
    "preview_fur": "fur_ginger",
    "pieces": [
        {"id": "set_uld_crown", "slot": "head", "kind": "head", "art": "uld_crown", "name": "Archaedas' Crystal Crown", "rarity": 5,
         "icon": "INV_Crown_13", "boss": "Archaedas", "word": "crown",
         "svg": crown(), "layers": dict(frames(4, crown_shards), mask=crown_mask(), runes=crown_runes()),
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K("uld_crown", "mask"), "scale": 110, "vx": 45, "vy": -10, "color": [1.0, 0.9, 1.0], "blend": "ADD", "alpha": 0.9},
             {"kind": "pulse", "key": K("uld_crown", "runes"), "a": [0.15, 1.0], "speed": 2.3, "blend": "ADD"},
             {"kind": "flip", "keys": [K("uld_crown", "fl%d" % i) for i in range(1, 5)], "fps": 6},
             {"kind": "glint", "sprite": "a_spark", "n": 3, "spots": [[232, 20, 280, 110], [176, 50, 222, 110], [290, 50, 336, 110]],
              "size": [20, 30], "gap": [0.3, 1.0], "color": [0.95, 0.85, 1.0], "blend": "ADD", "at": "front"},
             {"kind": "particles", "sprite": "a_spark", "n": 4, "box": [170, 40, 342, 110], "vx": [-8, 8], "vy": [-40, -20], "life": [0.9, 1.5],
              "size": [8, 12], "color": RUNEC, "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_uld_shoulders", "slot": "shoulder", "kind": "shoulder", "art": "uld_shoulders", "name": "Ironaya's Titan Pauldrons", "rarity": 4,
         "icon": "INV_Shoulder_23", "boss": "Ironaya", "word": "shoulders",
         "svg": pauldron(), "layers": {"mask": pauldron_mask(), "runes": pauldron_runes()},
         "anim": [
             {"kind": "pulse", "key": K("uld_shoulders", "runes"), "a": [0.1, 1.0], "speed": 2.0, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_shine", "mask": K("uld_shoulders", "mask"), "scale": 90, "vx": 30, "vy": -20, "color": [1.0, 0.9, 1.0], "blend": "ADD", "alpha": 0.8},
             {"kind": "glint", "sprite": "a_spark", "n": 2, "spots": [[70, 170, 130, 230], [382, 170, 442, 230]], "size": [16, 24],
              "gap": [0.5, 1.4], "color": [0.95, 0.85, 1.0], "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_uld_chest", "slot": "chest", "kind": "chest", "art": "uld_chest", "name": "Stone Keeper's Rune Plate", "rarity": 4,
         "icon": "INV_Chest_Plate08", "boss": "Ancient Stone Keeper", "word": "chest",
         "svg": chest(), "layers": {"mask": chest_mask(), "core": chest_core()},
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K("uld_chest", "mask"), "scale": 60, "vx": 0, "vy": 40, "color": RUNEC, "blend": "ADD"},
             {"kind": "pulse", "key": K("uld_chest", "core"), "a": [0.2, 1.0], "speed": 2.6, "blend": "ADD"},
         ]},
        {"id": "set_uld_cape", "slot": "back", "kind": "back", "art": "uld_cape", "name": "Revelosh's Geode Drape", "rarity": 4,
         "icon": "INV_Misc_Cape_09", "boss": "Revelosh", "word": "cape",
         "svg": cape(), "layers": {"mask": cape_mask(), "glow": cape_glow()},
         "anim": [
             {"kind": "pulse", "key": K("uld_cape", "glow"), "a": [0.1, 0.7], "speed": 1.7, "blend": "ADD", "at": "behind"},
             {"kind": "scroll", "sprite": "a_shine", "mask": K("uld_cape", "mask"), "scale": 90, "vx": 0, "vy": -45, "color": [1.0, 0.9, 1.0], "blend": "ADD", "alpha": 0.8},
             {"kind": "glint", "sprite": "a_spark", "n": 2, "spots": [[30, 280, 90, 420], [422, 280, 482, 420]], "size": [16, 24],
              "gap": [0.5, 1.5], "color": [0.95, 0.85, 1.0], "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_uld_staff", "slot": "main", "kind": "weapon", "art": "uld_staff", "name": "Galgann's Geode Staff", "rarity": 5,
         "icon": "INV_Staff_13", "boss": "Galgann Firehammer", "word": "staff",
         "svg": staff(), "layers": dict(frames(4, staff_shards), mask=staff_mask(), glow=staff_glow()),
         "anim": [
             {"kind": "pulse", "key": K("uld_staff", "glow"), "a": [0.05, 0.45], "speed": 2.2, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_shine", "mask": K("uld_staff", "mask"), "scale": 80, "vx": 30, "vy": -30, "color": [1.0, 0.9, 1.0], "blend": "ADD", "alpha": 0.6},
             {"kind": "flip", "keys": [K("uld_staff", "fl%d" % i) for i in range(1, 5)], "fps": 7},
         ]},
        {"id": "set_uld_aura", "slot": "effect", "kind": "effect", "art": "fx_uld_stones", "name": "Grimlok's Earthen Aura", "rarity": 4,
         "icon": "Spell_Nature_EarthBindTotem", "boss": "Grimlok", "word": "aura", "glow": (0.6, 0.45, 1.0),
         "fx": {"layer": "back", "anim": "float"},
         "layers": dict(frames(3, rune_ring), rock=rock(), shard=ame_shard()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [0.55, 0.4, 1.0], "a": [0.2, 0.45], "speed": 1.5, "blend": "ADD", "at": "behind"},
             {"kind": "flip", "keys": [K("fx_uld_stones", "fl%d" % i) for i in range(1, 4)], "fps": 4, "at": "behind"},
             {"kind": "particles", "sprite": "k_fx_uld_stones_rock", "n": 5, "box": [60, 380, 452, 460], "vx": [-6, 6], "vy": [-45, -25],
              "life": [2.2, 3.2], "size": [18, 28], "spin": [-0.8, 0.8], "sway": 4, "at": "behind"},
             {"kind": "particles", "sprite": "k_fx_uld_stones_shard", "n": 4, "box": [70, 300, 442, 440], "vx": [-8, 8], "vy": [-55, -30],
              "life": [1.8, 2.6], "size": [18, 26], "spin": [-1.0, 1.0], "at": "front"},
             {"kind": "particles", "sprite": "a_spark", "n": 5, "box": [90, 380, 422, 470], "vx": [-8, 8], "vy": [-70, -40], "life": [1.0, 1.6],
              "size": [8, 12], "color": RUNEC, "blend": "ADD", "at": "front"},
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
