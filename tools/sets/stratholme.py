"""Stratholme set (1.6): the death knight's winter. Dark runed steel and living ice: a horned helm under a
crown of icicles with frost drifting inside them, glowing blue runes, a glacial cloak with frost creeping
over it, a runeblade, and snow falling around the cat. Each piece is guaranteed from one Stratholme boss
in Adventure until owned.
  python3 tools/sets/stratholme.py            -> Art/v/k_strat_*.tga, Art/strat_*.tga, Sets/Stratholme.lua
  python3 tools/set_preview.py tools/sets/stratholme.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: dark runed steel, glacier ice, rune blue
STEEL, STEEL2, STEEL3 = "#3f4a66", "#5b6888", "#8b9bbb"
ICE, ICE2, ICE3, ICED = "#86d8ff", "#d4f4ff", "#4aa8e0", "#2c6a9a"
RUNE, RUNEL = "#58dcff", "#e8fdff"
RUNEC = [0.45, 0.88, 1.0]
SNOWC = [0.9, 0.97, 1.0]

def frames(n, fn):
    return {"fl%d" % (k + 1): fn(k) for k in range(n)}

# a blur whose region is the whole canvas, so the glow of a small shape is never cut off into a box
WIDEBLUR = ('<defs><filter id="wblur" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1100" height="1100">'
            '<feGaussianBlur stdDeviation="5"/></filter></defs>')
def blur(s): return WIDEBLUR + '<g filter="url(#wblur)">%s</g>' % s

def sprite(inner, S=32):
    """a small particle sprite: the drawing centred in an exact S x S box (faint corner dots fix the crop)"""
    dots = '<rect x="2" y="2" width="1" height="1" fill="#fff" opacity=".03"/><rect x="%d" y="%d" width="1" height="1" fill="#fff" opacity=".03"/>' % (1 + S, 1 + S)
    return '<g transform="translate(%.1f %.1f)">%s</g>%s' % (2 + S / 2.0, 2 + S / 2.0, inner, dots)

def spike_pts(bx, by, ang, L, W):
    """an icicle standing on (bx, by), leaning ang degrees (0 = straight up, 180 = hanging down)"""
    a = math.radians(ang)
    ux, uy = math.sin(a), -math.cos(a)
    vx, vy = math.cos(a), math.sin(a)
    pt = lambda t, s: (bx + ux * t + vx * s, by + uy * t + vy * s)
    return [pt(0, -W / 2.0), pt(L * 0.55, -W * 0.32), pt(L, 0), pt(L * 0.55, W * 0.3), pt(0, W / 2.0)], pt(0, 0), pt(L, 0)

def icicle(bx, by, ang, L, W, ink=4):
    pts, base, tip = spike_pts(bx, by, ang, L, W)
    d = "M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" % (pts[0] + pts[1] + pts[2] + pts[3] + pts[4])
    s = P(d, ICE, ink)
    s += P("M %.1f %.1f Q %.1f %.1f %.1f %.1f L %.1f %.1f Z" % (pts[0] + pts[1] + pts[2] + base), ICE2, 0)
    s += LN("M %.1f %.1f L %.1f %.1f" % (base + tip), ICE3, 1.8)
    return s

def icicle_mask(bx, by, ang, L, W):
    pts = spike_pts(bx, by, ang, L, W)[0]
    return P("M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" % (pts[0] + pts[1] + pts[2] + pts[3] + pts[4]), "#ffffff", 0)

def rune(x, y, r, col=RUNE, w=2.4):
    """a death knight rune: a vertical stroke with two angled branches"""
    return LN("M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f"
              % (x, y - r, x, y + r, x, y - r * 0.4, x + r * 0.6, y - r, x, y + r * 0.2, x - r * 0.6, y - r * 0.3), col, w)

# ---------------------------------------------------------------- helm (head space)
CROWN_IC = [(128, 24, 0, 34, 22), (104, 28, -18, 30, 17), (152, 28, 18, 30, 17), (80, 36, -36, 28, 14), (176, 36, 36, 28, 14)]
HORN = "M 58 88 C 8 92 -22 60 -26 -4 C -10 22 10 46 58 58 Z"
HORN_IC = [(6, 66, 186, 22, 9), (20, 74, 180, 28, 10), (36, 80, 176, 18, 8)]   # icicles hanging under each horn
def horn():
    s = "".join(icicle(*c, ink=3) for c in HORN_IC)
    s += P(HORN, ICE, 5) + P("M 56 82 C 14 84 -12 58 -20 12 C -4 40 16 56 58 64 Z", ICE2, 0) + LN("M 50 74 C 18 74 -6 52 -16 18", ICE3, 2.2)
    # steel rings where the horn leaves the helm
    for x0, y0, x1, y1 in ((52, 56, 50, 88), (38, 52, 32, 86)):
        s += LN("M %d %d Q %d %d %d %d" % (x0, y0, x0 - 8, (y0 + y1) / 2, x1, y1), INK, 9) + LN("M %d %d Q %d %d %d %d" % (x0, y0, x0 - 8, (y0 + y1) / 2, x1, y1), STEEL3, 5)
    return s

def helm():
    s = horn() + mirror(horn(), 128)
    for c in CROWN_IC[::-1]: s += icicle(*c)
    # the steel helm over the top of the head, with a sharp brow
    dome = "M 42 104 C 30 40 62 8 128 8 C 194 8 226 40 214 104 L 166 96 L 128 112 L 90 96 Z"
    s += P(dome, STEEL, 5)
    s += P("M 56 92 C 50 50 80 20 120 16 C 94 30 76 54 74 92 Z", STEEL2, 0)
    s += LN("M 54 96 L 90 90 L 128 106 L 166 90 L 202 96", STEEL3, 4)
    # frost creeping over the top of the helm
    s += P("M 60 46 Q 78 16 128 14 Q 178 16 196 46 Q 184 40 178 50 Q 166 38 154 48 Q 142 36 128 46 Q 114 36 102 48 Q 90 38 78 50 Q 72 40 60 46 Z", ICE2, 3)
    # rune band and the ice gem
    for x, y in ((76, 76), (98, 70), (158, 70), (180, 76)): s += rune(x, y, 7, ICED, 3)
    s += P("M 128 56 L 142 78 L 128 100 L 114 78 Z", ICE, 4) + P("M 128 56 L 114 78 L 128 100 Z", ICE2, 0)
    for x in (62, 194): s += CI(x, 92, 3.5, STEEL3, 2)
    return HEAD(s)

def helm_mask():
    one = P(HORN, "#ffffff", 0) + "".join(icicle_mask(*c) for c in HORN_IC)
    return HEAD("".join(icicle_mask(*c) for c in CROWN_IC) + one + mirror(one, 128))

def helm_runes():
    s = ""
    for x, y in ((76, 76), (98, 70), (158, 70), (180, 76)): s += blur(rune(x, y, 8, RUNE, 6)) + rune(x, y, 7, RUNEL, 2.2)
    s += blur(P("M 128 52 L 146 78 L 128 106 L 110 78 Z", RUNE, 0)) + P("M 128 64 L 136 78 L 128 92 L 120 78 Z", RUNEL, 0)
    return HEAD(s)

# ---------------------------------------------------------------- shoulders (body space)
SH_IC = [(-24, -12, -50, 30, 12), (-6, -18, -18, 36, 14), (12, -16, 14, 24, 11)]
SH_HANG = [(-30, 14, 190, 16, 8), (-16, 20, 184, 22, 9), (0, 22, 178, 18, 8), (16, 16, 172, 13, 7)]
def pauldron():
    cx, cy = SH_C
    s = "".join(icicle(cx + dx, cy + dy, a, L, W, 3.5) for dx, dy, a, L, W in SH_IC)
    s += "".join(icicle(cx + dx, cy + dy, a, L, W, 3) for dx, dy, a, L, W in SH_HANG)
    dome = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 32, cy + 10, cx + 28, cy - 22, cx - 4, cy - 22,
        cx - 38, cy - 20, cx - 40, cy + 14, cx - 4, cy + 26, cx + 32, cy + 10)
    s += P(dome, STEEL, 5)
    # a frosted cap of snow on top
    cap = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (
        cx - 36, cy - 4, cx - 34, cy - 22, cx - 4, cy - 22, cx + 26, cy - 22, cx + 30, cy - 2,
        cx + 22, cy + 4, cx + 14, cy - 4, cx + 4, cy + 4, cx - 8, cy - 4, cx - 22, cy + 4, cx - 36, cy - 4)
    s += P(cap, ICE2, 3.5) + LN("M %d %d Q %d %d %d %d" % (cx - 24, cy - 14, cx - 8, cy - 20, cx + 10, cy - 17), "#ffffff", 3)
    s += LN("M %d %d Q %d %d %d %d" % (cx - 38, cy + 10, cx - 4, cy + 24, cx + 30, cy + 8), STEEL3, 6) + LN("M %d %d Q %d %d %d %d" % (cx - 38, cy + 10, cx - 4, cy + 24, cx + 30, cy + 8), INK, 2)
    s += rune(cx - 4, cy + 8, 6, ICED, 2.8)
    return BOTH(s)

def pauldron_mask():
    cx, cy = SH_C
    return BOTH("".join(icicle_mask(cx + dx, cy + dy, a, L, W) for dx, dy, a, L, W in SH_IC + SH_HANG))

def pauldron_runes():
    cx, cy = SH_C
    return BOTH(blur(rune(cx - 4, cy + 8, 7, RUNE, 6)) + rune(cx - 4, cy + 8, 6, RUNEL, 2.2))

# ---------------------------------------------------------------- chest (body space)
PLATES = [(132, 40), (152, 46), (172, 50), (192, 52)]   # carapace bands: top y, half width
def chest():
    s = P(BODY_OUT, STEEL, 5)
    for y, w in PLATES:
        d = "M %d %d Q 128 %d %d %d L %d %d Q 128 %d %d %d Z" % (128 - w, y + 10, y - 6, 128 + w, y + 10, 128 + w - 4, y + 22, y + 10, 128 - w + 4, y + 22)
        s += P(d, STEEL2, 3.5) + LN("M %d %d Q 128 %d %d %d" % (128 - w + 6, y + 9, y - 3, 128 + w - 6, y + 9), ICE3, 2.5)
    # Nerubian legs folded down the sides
    for sx in (-1, 1):
        s += LN("M %d 124 Q %d 150 %d 176" % (128 + sx * 50, 128 + sx * 64, 128 + sx * 56), INK, 9) + LN("M %d 124 Q %d 150 %d 176" % (128 + sx * 50, 128 + sx * 64, 128 + sx * 56), STEEL3, 5)
    s += CI(128, 160, 17, STEEL, 4.5) + '<circle cx="128" cy="160" r="11" fill="none" stroke="%s" stroke-width="3"/>' % ICED + rune(128, 160, 7, ICED, 3)
    s += RC(60, 198, 136, 14, STEEL2, 4, 4) + "".join(CI(x, 205, 3.5, ICE, 2) for x in (76, 102, 154, 180)) + P("M 128 194 L 138 205 L 128 216 L 118 205 Z", ICE, 3.5)
    return s

def chest_mask():
    s = ""
    for y, w in PLATES:
        s += LN("M %d %d Q 128 %d %d %d" % (128 - w + 6, y + 9, y - 3, 128 + w - 6, y + 9), "#ffffff", 4)
    return s + CI(128, 160, 11, "#ffffff", 0)

def chest_runes():
    return blur(CI(128, 160, 14, RUNE, 0)) + '<circle cx="128" cy="160" r="11" fill="none" stroke="%s" stroke-width="2.5"/>' % RUNEL + rune(128, 160, 7, RUNEL, 2.5)

# ---------------------------------------------------------------- cape (side drapes)
def cape_ic():
    out = []
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        sgn = -1 if pts[0][0] < 128 else 1
        for i in (2, 3, 4, 5, 6, 7):
            x, y = pts[i]
            out.append((x + sgn * 1, y + 4, 180 - sgn * 24, 12 + (i % 2) * 8, 8))
    return out

def cape():
    s = "".join(icicle(*c, ink=3) for c in cape_ic())
    s += "".join(P(p, ICE3, 5) for p in DRAPE_OUT) + "".join(P(p, ICED, 3) for p in DRAPE_IN)
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        d = "M " + " L ".join("%.1f %.1f" % (x + (5 if x < 128 else -5), y) for x, y in pts)
        s += LN(d, ICE2, 5)
    for x0, sg in ((50, 1), (206, -1)):
        s += rune(x0 - sg * 4, 168, 7, ICE2, 2.5)
    return s

def cape_mask():
    return "".join(P(p, "#ffffff", 0) for p in DRAPE_OUT)

# ---------------------------------------------------------------- runeblade (right paw)
BL = 150
BLADE = "M -11 -26 L -14 %d L 0 %d L 14 %d L 11 -26 Z" % (-BL + 22, -BL - 10, -BL + 22)
def blade():
    s = RC(-4.5, -12, 9, 46, "#2e2a36", 4)
    for y in (-2, 10, 22): s += LN("M -5 %d L 5 %d" % (y, y + 4), STEEL3, 2)
    s += CI(0, 38, 8, STEEL2, 3.5) + CI(0, 38, 3.5, ICE, 0)
    s += P(BLADE, STEEL3, 5)
    s += P("M 0 -30 L 0 %d L -12 %d L -9 -30 Z" % (-BL - 6, -BL + 22), "#a8b6d0", 0)
    s += LN("M 0 -32 L 0 %d" % (-BL + 6), STEEL, 4)
    for k, y in enumerate((-52, -78, -104, -128)): s += rune(0, y, 7, ICED, 3)
    # winged guard and the ice gem
    guard = "M 0 -34 Q -26 -30 -40 -50 Q -26 -40 -12 -40 Q -26 -20 -32 -18 Q -14 -16 0 -18 Z"
    s += P(guard, STEEL2, 4) + mirror(P(guard, STEEL2, 4), 0)
    s += P("M 0 -40 L 9 -28 L 0 -14 L -9 -28 Z", ICE, 3.5) + P("M 0 -40 L -9 -28 L 0 -14 Z", ICE2, 0)
    return RHAND(s)

def blade_mask():
    return RHAND(P(BLADE, "#ffffff", 0))

def blade_runes():
    s = ""
    for y in (-52, -78, -104, -128): s += blur(rune(0, y, 8, RUNE, 6)) + rune(0, y, 7, RUNEL, 2.2)
    return RHAND(s + blur(CI(0, -28, 9, RUNE, 0)))

# ---------------------------------------------------------------- aura: winter's grasp
def ice_ring(k):
    """a ring of ice spikes rising out of the ground around the cat, breathing up and down"""
    s = blur('<ellipse cx="128" cy="214" rx="112" ry="16" fill="%s" opacity=".7"/>' % ICE)
    spikes = []
    for i in range(13):
        x = 22 + i * 17.7
        grow = 0.75 + 0.25 * math.sin(i * 1.9 + k * 2.1)
        L = (14 + 10 * ((i * 7) % 3)) * grow * (0.45 if abs(x - 128) < 52 else 1.0)
        y = 214 + 6 * math.sin(i * 0.5)
        spikes.append((y, icicle(x, y, (x - 128) * 0.15, L, 8 + (i % 2) * 3, 3)))
    return s + "".join(sp for _, sp in sorted(spikes))

def flake():
    arm = "M 0 0 L 0 -12 M 0 -7 L -4 -10 M 0 -7 L 4 -10"
    s = "".join('<g transform="rotate(%d)">%s</g>' % (a, LN(arm, INK, 4.5)) for a in range(0, 360, 60))
    s += "".join('<g transform="rotate(%d)">%s</g>' % (a, LN(arm, "#ffffff", 2.2)) for a in range(0, 360, 60))
    return sprite(s)

SET = {
    "key": "strat", "name": "Stratholme", "zone": "strat", "lua": "Stratholme", "file": "stratholme",
    "about": "Stratholme set: runed steel and living ice, each piece guaranteed from one Stratholme boss in Adventure until owned.",
    "preview_fur": "fur_midnight",
    "pieces": [
        {"id": "set_strat_helm", "slot": "head", "kind": "head", "art": "strat_helm", "name": "Rivendare's Frostforged Helm", "rarity": 5,
         "icon": "INV_Helmet_74", "boss": "Baron Rivendare", "word": "helm",
         "svg": helm(), "layers": {"mask": helm_mask(), "runes": helm_runes(), "flake": flake()},
         "anim": [
             {"kind": "scroll", "sprite": "a_frost", "mask": K("strat_helm", "mask"), "scale": 90, "vx": 6, "vy": 18, "color": [0.8, 0.95, 1.0], "blend": "ADD"},
             {"kind": "pulse", "key": K("strat_helm", "runes"), "a": [0.2, 1.0], "speed": 2.4, "blend": "ADD"},
             {"kind": "glint", "sprite": "a_spark", "n": 3, "spots": [[230, 10, 282, 70], [190, 30, 236, 90], [276, 30, 322, 90], [96, 10, 150, 90], [362, 10, 416, 90]],
              "size": [18, 28], "gap": [0.3, 1.0], "color": [0.85, 0.97, 1.0], "blend": "ADD", "at": "front"},
             {"kind": "particles", "sprite": "k_strat_helm_flake", "n": 5, "box": [96, 0, 416, 40], "vx": [-10, 10], "vy": [25, 45], "life": [1.6, 2.4],
              "size": [12, 18], "spin": [-1.0, 1.0], "sway": 8, "alpha": 0.95, "color": SNOWC, "at": "front"},
         ]},
        {"id": "set_strat_shoulders", "slot": "shoulder", "kind": "shoulder", "art": "strat_shoulders", "name": "Ramstein's Glacial Spaulders", "rarity": 4,
         "icon": "INV_Shoulder_25", "boss": "Ramstein the Gorger", "word": "shoulders",
         "svg": pauldron(), "layers": {"mask": pauldron_mask(), "runes": pauldron_runes()},
         "anim": [
             {"kind": "scroll", "sprite": "a_frost", "mask": K("strat_shoulders", "mask"), "scale": 70, "vx": 4, "vy": 16, "color": [0.8, 0.95, 1.0], "blend": "ADD"},
             {"kind": "pulse", "key": K("strat_shoulders", "runes"), "a": [0.15, 1.0], "speed": 2.0, "blend": "ADD"},
             {"kind": "glint", "sprite": "a_spark", "n": 2, "spots": [[60, 160, 120, 230], [392, 160, 452, 230]], "size": [16, 24],
              "gap": [0.5, 1.4], "color": [0.85, 0.97, 1.0], "blend": "ADD", "at": "front"},
         ]},
        {"id": "set_strat_chest", "slot": "chest", "kind": "chest", "art": "strat_chest", "name": "Nerub'enkan's Frost Carapace", "rarity": 4,
         "icon": "INV_Chest_Plate02", "boss": "Nerub'enkan", "word": "chest",
         "svg": chest(), "layers": {"mask": chest_mask(), "runes": chest_runes()},
         "anim": [
             {"kind": "scroll", "sprite": "a_shine", "mask": K("strat_chest", "mask"), "scale": 80, "vx": 40, "vy": 0, "color": RUNEC, "blend": "ADD"},
             {"kind": "pulse", "key": K("strat_chest", "runes"), "a": [0.2, 1.0], "speed": 2.2, "blend": "ADD"},
         ]},
        {"id": "set_strat_cape", "slot": "back", "kind": "back", "art": "strat_cape", "name": "Anastari's Frostveil", "rarity": 4,
         "icon": "INV_Misc_Cape_15", "boss": "Baroness Anastari", "word": "cape",
         "svg": cape(), "layers": {"mask": cape_mask()},
         "anim": [
             {"kind": "scroll", "sprite": "a_frost", "mask": K("strat_cape", "mask"), "scale": 80, "vx": 0, "vy": 14, "color": [0.85, 0.97, 1.0], "blend": "ADD", "alpha": 0.9},
             {"kind": "particles", "sprite": "t_snow", "n": 3, "box": [20, 200, 100, 300], "vx": [-8, 8], "vy": [30, 50], "life": [2.0, 3.0],
              "size": [10, 14], "spin": [-1, 1], "sway": 8, "color": SNOWC, "at": "behind"},
             {"kind": "particles", "sprite": "t_snow", "n": 3, "box": [412, 200, 492, 300], "vx": [-8, 8], "vy": [30, 50], "life": [2.0, 3.0],
              "size": [10, 14], "spin": [-1, 1], "sway": 8, "color": SNOWC, "at": "behind"},
         ]},
        {"id": "set_strat_blade", "slot": "main", "kind": "weapon", "art": "strat_blade", "name": "Maleki's Runeblade of Winter", "rarity": 5,
         "icon": "INV_Sword_48", "boss": "Maleki the Pallid", "word": "runeblade",
         "svg": blade(), "layers": {"mask": blade_mask(), "runes": blade_runes()},
         "anim": [
             {"kind": "pulse", "key": K("strat_blade", "runes"), "a": [0.2, 1.0], "speed": 2.8, "blend": "ADD"},
             {"kind": "scroll", "sprite": "a_frost", "mask": K("strat_blade", "mask"), "scale": 60, "vx": 0, "vy": -20, "color": [0.8, 0.95, 1.0], "blend": "ADD", "alpha": 0.8},
             {"kind": "particles", "sprite": "a_glow", "n": 4, "box": [330, 60, 420, 250], "vx": [-6, 6], "vy": [-20, -8], "life": [1.4, 2.2],
              "size": [24, 36], "grow": 0.8, "alpha": 0.5, "color": [0.6, 0.9, 1.0], "blend": "ADD"},
         ]},
        {"id": "set_strat_aura", "slot": "effect", "kind": "effect", "art": "fx_strat_winter", "name": "Winter's Grasp", "rarity": 4,
         "icon": "Spell_Frost_FrostNova", "boss": "Cannon Master Willey", "word": "aura", "glow": (0.55, 0.88, 1.0),
         "fx": {"layer": "back", "anim": "float"},
         "layers": dict(frames(3, ice_ring), flake=flake()),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [0.5, 0.85, 1.0], "a": [0.2, 0.5], "speed": 1.4, "blend": "ADD", "at": "behind"},
             {"kind": "flip", "keys": [K("fx_strat_winter", "fl%d" % i) for i in range(1, 4)], "fps": 3, "at": "front"},
             {"kind": "particles", "sprite": "k_fx_strat_winter_flake", "n": 7, "box": [40, 0, 472, 120], "vx": [-14, 6], "vy": [35, 60], "life": [3.0, 4.5],
              "size": [12, 20], "spin": [-1.2, 1.2], "sway": 12, "color": SNOWC, "at": "front"},
             {"kind": "particles", "sprite": "t_snow", "n": 6, "box": [40, 0, 472, 160], "vx": [-10, 4], "vy": [25, 45], "life": [3.5, 5.0],
              "size": [8, 12], "spin": [-1, 1], "sway": 10, "alpha": 0.8, "color": SNOWC, "at": "behind"},
             {"kind": "glint", "sprite": "a_spark", "n": 3, "spots": [[40, 380, 472, 460]], "size": [16, 26], "gap": [0.3, 1.0],
              "color": [0.85, 0.97, 1.0], "blend": "ADD", "at": "front"},
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
