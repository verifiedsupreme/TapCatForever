"""Scarlet Monastery set (1.6): crimson and holy light. A winged seraph helm under a bobbing halo,
crimson-and-gold plate with the Scarlet sun, light sweeping over the wings and the blade, golden
feathers drifting down. Each piece is guaranteed from one Scarlet Monastery boss in Adventure until owned.
  python3 tools/sets/scarlet_monastery.py            -> Art/v/k_sm_*.tga, Art/sm_*.tga, Sets/ScarletMonastery.lua
  python3 tools/set_preview.py tools/sets/scarlet_monastery.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: Scarlet crimson, burnished gold, holy white light
CRIM, CRIM2, CRIM3 = "#c81f33", "#8a1323", "#ec5560"
GOLD, GOLD2, GOLDL = "#f3bd3f", "#c58a1c", "#ffe08a"
HOLY, WHITE, PLATE = "#fff6c8", "#fbf7ee", "#ece5d4"
WSHADE = "#e4dcc8"

def frames(n, fn):
    return {"fl%d" % (k + 1): fn(k) for k in range(n)}

def sprite(inner, S=32):
    """a small particle sprite: the drawing centred in an exact S x S box (faint corner dots fix the crop)"""
    dots = '<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/><rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S)
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)

def sun(cx, cy, r, rays=8, ray=0.75, fill=GOLD, core=GOLDL, ink=3.5, gem=None):
    """the Scarlet sun: a disc with pointed flame rays"""
    s = ""
    for i in range(rays):
        a = math.radians(i * 360.0 / rays)
        b1, b2 = a - math.pi / rays * 0.8, a + math.pi / rays * 0.8
        tip = r * (1 + ray)
        s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (cx + math.cos(b1) * r * 0.85, cy + math.sin(b1) * r * 0.85,
               cx + math.cos(a) * tip, cy + math.sin(a) * tip, cx + math.cos(b2) * r * 0.85, cy + math.sin(b2) * r * 0.85), fill, ink * 0.8)
    s += CI(cx, cy, r, fill, ink) + CI(cx, cy, r * 0.62, core, 0)
    if gem: s += GEM(cx, cy, r * 0.42, gem)
    return s

def sun_shape(cx, cy, r, rays=8, ray=0.75, col="#ffffff"):
    return sun(cx, cy, r, rays, ray, col, col, 0)

# ---------------------------------------------------------------- helm (head space)
def wing_one():
    """the left wing, rising from the helm's side: three rows of feathers"""
    s = ""
    rows = [  # (root, tip, scallops, fill, ink)
        ((62, 54), (-22, -6), 6, WHITE, 5),
        ((62, 62), (-28, 26), 5, WHITE, 4.5),
        ((62, 70), (-22, 56), 4, WSHADE, 4),
        ((62, 78), (-2, 82), 3, GOLDL, 4),
    ]
    for (rx, ry), (tx, ty), n, col, ink in rows:
        # top edge: a curve from the root up to the tip; bottom edge: scallops back to the root
        d = "M %d %d Q %.1f %.1f %d %d" % (rx, ry, (rx + tx) / 2 + 6, min(ry, ty) - 14, tx, ty)
        px, py = tx, ty
        for k in range(1, n + 1):
            f = k / float(n)
            nx, ny = tx + (rx - tx) * f, ty + (ry + 20 - ty) * f
            mx, my = (px + nx) / 2 - 6, (py + ny) / 2 + 12
            d += " Q %.1f %.1f %.1f %.1f" % (mx, my, nx, ny)
            px, py = nx, ny
        d += " Z"
        s += P(d, col, ink)
    s += LN("M 54 58 Q 22 30 -8 6", GOLD2, 2.5) + LN("M 54 66 Q 22 46 -12 32", GOLD2, 2) + LN("M 54 74 Q 26 64 -6 60", GOLD2, 2)
    return s

def wing_shape():
    s = wing_one()
    s = s.replace(WHITE, "#ffffff").replace(WSHADE, "#ffffff").replace(GOLDL, "#ffffff")
    return HEAD(s + mirror(s, 128))

def helm():
    w = wing_one()
    s = w + mirror(w, 128)
    # ear guards: pointed crimson plates over the ears
    ear = P("M 40 92 L 50 14 L 104 42 Z", CRIM, 5) + P("M 52 70 L 56 30 L 88 46 Z", CRIM3, 0) + LN("M 44 88 L 52 24", GOLD, 3)
    s += ear + mirror(ear, 128)
    dome = "M 40 100 Q 38 30 128 24 Q 218 30 216 100 Z"
    s += P(dome, CRIM, 5)
    s += LN("M 64 66 Q 80 40 116 34", CRIM3, 6)  # shine
    for x in (84, 172): s += LN("M %d 86 Q %d 50 %d 34" % (x, x + (128 - x) * 0.25, x + (128 - x) * 0.45), GOLD2, 3)
    s += RC(120, 22, 16, 56, GOLD, 7, 4) + LN("M 128 28 L 128 70", GOLDL, 3)
    s += RC(34, 84, 188, 20, GOLD, 9, 5) + LN("M 46 90 Q 128 84 210 90", GOLDL, 3)
    for x in (62, 92, 164, 194): s += CI(x, 94, 4, CRIM2, 2.5)
    s += sun(128, 62, 17, rays=10, ray=0.7, gem="#e8283c")
    return HEAD(s)

def helm_emblem_glow():
    return HEAD('<g filter="url(#blur)">%s</g>' % CI(128, 62, 20, HOLY, 0))

def halo(k):
    dy = (0, -2, -3, -2)[k]
    y = 8 + dy
    s = '<g filter="url(#blur)"><ellipse cx="128" cy="%d" rx="54" ry="11" fill="none" stroke="%s" stroke-width="12"/></g>' % (y, HOLY)
    ring = lambda col, w: '<ellipse cx="128" cy="%d" rx="52" ry="10" fill="none" stroke="%s" stroke-width="%s"/>' % (y, col, w)
    s += ring(INK, 11) + ring(GOLD, 6.5) + ring(GOLDL, 2.5)
    return HEAD(s)

# ---------------------------------------------------------------- shoulders (body space)
def pauldron():
    cx, cy = SH_C
    s = ""
    # a small gold wing sweeping up and out
    wing = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (
        cx - 8, cy - 12, cx - 30, cy - 30, cx - 50, cy - 48, cx - 46, cy - 34, cx - 44, cy - 26,
        cx - 40, cy - 22, cx - 38, cy - 12, cx - 26, cy - 8, cx - 8, cy - 12)
    s += P(wing, GOLD, 4) + LN("M %d %d Q %d %d %d %d" % (cx - 14, cy - 14, cx - 30, cy - 26, cx - 44, cy - 40), GOLDL, 2.5)
    dome = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 32, cy + 8, cx + 28, cy - 24, cx - 4, cy - 24,
        cx - 38, cy - 22, cx - 40, cy + 12, cx - 4, cy + 24, cx + 32, cy + 8)
    s += P(dome, CRIM, 5)
    s += LN("M %d %d Q %d %d %d %d" % (cx - 24, cy - 10, cx - 8, cy - 18, cx + 10, cy - 15), CRIM3, 5)
    rim = "M %d %d Q %d %d %d %d" % (cx - 38, cy + 8, cx - 6, cy + 22, cx + 30, cy + 6)
    s += LN(rim, INK, 11) + LN(rim, GOLD, 7) + LN(rim, GOLDL, 2)
    s += sun(cx - 6, cy - 2, 9, rays=8, ray=0.6, gem="#e8283c", ink=3)
    return BOTH(s)

def pauldron_glow():
    cx, cy = SH_C
    return BOTH('<g filter="url(#blur)">%s</g>' % CI(cx - 6, cy - 2, 18, HOLY, 0))

# ---------------------------------------------------------------- chest (body space)
EMB = (128, 166)
def chest():
    s = P(BODY_OUT, PLATE, 5)
    s += LN("M 82 132 Q 74 170 76 206", "#d4cab4", 4) + LN("M 174 132 Q 182 170 180 206", "#d4cab4", 4)
    tabard = "M 94 122 Q 128 132 162 122 L 168 214 L 88 214 Z"
    s += P(tabard, CRIM, 5)
    s += LN("M 98 128 L 93 210", GOLD, 4) + LN("M 158 128 L 163 210", GOLD, 4)
    s += LN("M 104 136 Q 108 170 104 206", CRIM3, 4)
    # gold collar
    s += P("M 92 120 Q 128 136 164 120 L 160 130 Q 128 146 96 130 Z", GOLD, 4)
    s += sun(EMB[0], EMB[1], 15, rays=12, ray=0.65, gem="#e8283c")
    s += RC(58, 198, 140, 14, GOLD, 4, 4) + RC(116, 195, 24, 20, GOLD2, 4, 4) + GEM(128, 205, 5, "#e8283c")
    return s

def chest_emblem_mask():
    return sun_shape(EMB[0], EMB[1], 15, rays=12, ray=0.65)

def chest_glow():
    return '<g filter="url(#blur)">%s</g>' % CI(EMB[0], EMB[1], 24, HOLY, 0)

# ---------------------------------------------------------------- cape (side drapes)
GLYPH_T = (0.42, 0.72)
def glyph_spots():
    out = []
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=10)
        for t in GLYPH_T:
            x, y = pts[int(t * 10)]
            out.append((x + (14 if x < 128 else -14), y))
    return out

def cape():
    s = "".join(P(p, CRIM, 5) for p in DRAPE_OUT) + "".join(P(p, GOLD2, 3) for p in DRAPE_IN)
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        d = "M " + " L ".join("%.1f %.1f" % (x + (5 if x < 128 else -5), y) for x, y in pts)
        s += LN(d, INK, 10) + LN(d, GOLD, 6) + LN(d, GOLDL, 2)
    s += LN("M 58 146 Q 46 172 48 196", CRIM3, 3) + LN("M 198 146 Q 210 172 208 196", CRIM3, 3)
    for x, y in glyph_spots(): s += sun(x, y, 5, rays=8, ray=0.7, ink=2.5)
    return s

def cape_glyph_glow():
    return '<g filter="url(#blur)">%s</g>' % "".join(CI(x, y, 10, HOLY, 0) for x, y in glyph_spots())

def cape_mask():
    return "".join(P(p, "#ffffff", 0) for p in DRAPE_OUT)

# ---------------------------------------------------------------- greatsword (right paw)
BLADE = "M -11 -16 L -11 -122 L 0 -146 L 11 -122 L 11 -16 Z"
def sword():
    s = RC(-5, -8, 10, 34, CRIM2, 3, 4)
    for y in (-2, 8, 18): s += LN("M -5 %d L 5 %d" % (y, y + 4), CRIM3, 2)
    s += CI(0, 32, 8, GOLD, 4) + GEM(0, 32, 4, "#e8283c")
    s += P(BLADE, "#e3e9f3", 5) + P("M 0 -22 L 0 -138 L 9 -122 L 9 -22 Z", "#b9c4d6", 0)
    s += LN("M 0 -24 L 0 -126", GOLD, 3)
    # winged guard
    guard = "M 0 -10 Q -24 -6 -40 -26 Q -34 -12 -38 -8 Q -28 -2 -20 -2 Q -10 0 0 4 Z"
    s += P(guard, GOLD, 4) + mirror(P(guard, GOLD, 4), 0)
    s += sun(0, -28, 8, rays=8, ray=0.6, gem="#e8283c", ink=3)
    return RHAND(s)

def sword_mask(): return RHAND(P(BLADE, "#ffffff", 0))
def sword_glow(): return RHAND('<g filter="url(#blur)"><path d="%s" fill="%s" stroke="%s" stroke-width="12" stroke-linejoin="round"/></g>' % (BLADE, HOLY, GOLDL))

# ---------------------------------------------------------------- aura: light from above, falling feathers
def beams(k):
    """a fan of soft light beams from above that fade out downwards, turning slightly between frames"""
    s = ('<defs><linearGradient id="smbeam" x1="0" y1="0" x2="0" y2="1">'
         '<stop offset="0" stop-color="%s" stop-opacity="1"/><stop offset="0.6" stop-color="%s" stop-opacity="0.75"/>'
         '<stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient></defs>' % (HOLY, HOLY, HOLY))
    for i in range(9):
        a = math.radians(-56 + i * 14 + (k - 1) * 4.5)
        w = math.radians(3.6 if i % 2 else 4.8)
        ox, oy = 128, -6
        L = min(215, 118 / max(0.01, abs(math.sin(a) + math.copysign(math.sin(w), math.sin(a)))))
        s += '<path d="M %d %d L %.1f %.1f L %.1f %.1f Z" fill="url(#smbeam)" opacity="%.2f"/>' % (ox, oy, ox + math.sin(a - w) * L,
             oy + math.cos(a - w) * L, ox + math.sin(a + w) * L, oy + math.cos(a + w) * L, 1.0 if i % 2 else 0.8)
    return '<g filter="url(#blur)">%s</g>' % s

def feather():
    f = P("M 0 -14 Q 10 -4 5 10 L 0 14 L -5 10 Q -10 -4 0 -14 Z", WHITE, 2.5) + LN("M 0 -10 L 0 14", GOLD2, 1.8)
    return sprite('<g transform="rotate(28)">%s</g>' % f)

GOLDEN = [1.0, 0.85, 0.4]
SET = {
    "key": "sm", "name": "Scarlet Monastery", "zone": "sm", "lua": "ScarletMonastery", "file": "scarlet_monastery",
    "about": "Scarlet Monastery set: crimson and holy light, each piece guaranteed from one Scarlet Monastery boss in Adventure until owned.",
    "preview_fur": "fur_midnight",
    "pieces": [
        {"id": "set_sm_helm", "slot": "head", "kind": "head", "art": "sm_helm", "name": "Whitemane's Seraph Helm", "rarity": 5,
         "icon": "INV_Helmet_74", "boss": "High Inquisitor Whitemane", "word": "helm",
         "svg": helm(), "layers": dict(frames(4, halo), wings=wing_shape(), glow=helm_emblem_glow()),
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K("sm_helm", "wings"), "scale": 140, "vx": 55, "vy": 20, "color": [1.0, 0.92, 0.6], "blend": "ADD", "alpha": 0.8},
             {"kind": "flip", "keys": [K("sm_helm", "fl%d" % i) for i in range(1, 5)], "fps": 5},
             {"kind": "pulse", "key": K("sm_helm", "glow"), "a": [0.05, 0.5], "speed": 2.4, "blend": "ADD"},
             {"kind": "particles", "sprite": "t_sparkle", "n": 5, "box": [150, 20, 362, 90], "vx": [-8, 8], "vy": [-40, -20],
              "life": [1.0, 1.6], "size": [10, 16], "color": GOLDEN, "at": "front"},
         ]},
        {"id": "set_sm_shoulders", "slot": "shoulder", "kind": "shoulder", "art": "sm_shoulders", "name": "Fallen Champion's Pauldrons", "rarity": 4,
         "icon": "INV_Shoulder_10", "boss": "Fallen Champion", "word": "shoulders",
         "svg": pauldron(), "layers": {"glow": pauldron_glow()},
         "anim": [
             {"kind": "pulse", "key": K("sm_shoulders", "glow"), "a": [0.05, 0.6], "speed": 2.0, "blend": "ADD"},
             {"kind": "glint", "sprite": "a_spark", "n": 2, "spots": [[40, 180, 110, 240], [402, 180, 472, 240]], "size": [18, 26],
              "gap": [0.6, 1.6], "color": [1, 0.95, 0.7], "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_sm_chest", "slot": "chest", "kind": "chest", "art": "sm_chest", "name": "Fairbanks' Crimson Tabard", "rarity": 4,
         "icon": "INV_Chest_Plate03", "boss": "High Inquisitor Fairbanks", "word": "chest",
         "svg": chest(), "layers": {"emblem": chest_emblem_mask(), "glow": chest_glow()},
         "anim": [
             {"kind": "pulse", "key": K("sm_chest", "glow"), "a": [0.05, 0.5], "speed": 1.8, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_shine", "mask": K("sm_chest", "emblem"), "scale": 70, "vx": 40, "vy": 0, "color": [1, 0.95, 0.75], "blend": "ADD"},
         ]},
        {"id": "set_sm_cape", "slot": "back", "kind": "back", "art": "sm_cape", "name": "Doan's Scarlet Mantle", "rarity": 4,
         "icon": "INV_Misc_Cape_06", "boss": "Arcanist Doan", "word": "cape",
         "svg": cape(), "layers": {"glyphs": cape_glyph_glow(), "mask": cape_mask()},
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K("sm_cape", "mask"), "scale": 180, "vx": 0, "vy": 50, "color": [1, 0.75, 0.7], "blend": "ADD", "alpha": 0.45},
             {"kind": "pulse", "key": K("sm_cape", "glyphs"), "a": [0.1, 0.9], "speed": 2.6, "blend": "ADD"},
             {"kind": "particles", "sprite": "t_sparkle", "n": 3, "box": [50, 260, 110, 330], "vx": [-6, 4], "vy": [25, 45], "life": [1.6, 2.4],
              "size": [8, 13], "color": GOLDEN, "sway": 5, "at": "behind"},
             {"kind": "particles", "sprite": "t_sparkle", "n": 3, "box": [402, 260, 462, 330], "vx": [-4, 6], "vy": [25, 45], "life": [1.6, 2.4],
              "size": [8, 13], "color": GOLDEN, "sway": 5, "at": "behind"},
         ]},
        {"id": "set_sm_sword", "slot": "main", "kind": "weapon", "art": "sm_sword", "name": "Herod's Crusader Greatsword", "rarity": 5,
         "icon": "INV_Sword_39", "boss": "Herod", "word": "greatsword",
         "svg": sword(), "layers": {"mask": sword_mask(), "glow": sword_glow()},
         "anim": [
             {"kind": "pulse", "key": K("sm_sword", "glow"), "a": [0.05, 0.45], "speed": 2.2, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_shine", "mask": K("sm_sword", "mask"), "scale": 110, "vx": 10, "vy": -70, "color": [1, 0.95, 0.75], "blend": "ADD"},
         ]},
        {"id": "set_sm_aura", "slot": "effect", "kind": "effect", "art": "fx_sm_vigil", "name": "Azshir's Sleepless Vigil", "rarity": 4,
         "icon": "Spell_Holy_HolyBolt", "boss": "Azshir the Sleepless", "word": "aura", "glow": (1.0, 0.88, 0.5),
         "fx": {"layer": "back", "anim": "pulse"},
         "layers": dict(frames(3, beams), feather=feather()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [1.0, 0.86, 0.5], "a": [0.15, 0.35], "speed": 1.6, "blend": "ADD", "at": "behind"},
             {"kind": "flip", "keys": [K("fx_sm_vigil", "fl%d" % i) for i in range(1, 4)], "fps": 3, "blend": "ADD", "alpha": 0.95, "at": "behind"},
             {"kind": "particles", "sprite": "k_fx_sm_vigil_feather", "n": 5, "box": [40, 0, 472, 100], "vx": [-14, 14], "vy": [40, 70],
              "life": [2.6, 3.6], "size": [28, 38], "sway": 18, "spin": [-1.2, 1.2], "at": "front"},
             {"kind": "particles", "sprite": "t_sparkle", "n": 5, "box": [90, 260, 422, 460], "vx": [-8, 8], "vy": [-60, -30], "life": [1.2, 2.0],
              "size": [9, 15], "color": GOLDEN, "at": "behind"},
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
