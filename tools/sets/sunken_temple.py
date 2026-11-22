"""Sunken Temple set (1.6): the drowned serpent temple. A serpent-hood crown with a great water frill
(water swirling inside it, foam rippling along its edge), jade scales and Atal'ai gold, glowing serpent
eyes and rising bubbles. Each piece is guaranteed from one Sunken Temple boss in Adventure until owned.
  python3 tools/sets/sunken_temple.py            -> Art/v/k_st_*.tga, Art/st_*.tga, Sets/SunkenTemple.lua
  python3 tools/set_preview.py tools/sets/sunken_temple.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: deep water, aqua, foam, jade serpent scales, Atal'ai gold, a little coral
DEEP, WATER, AQUA, FOAM = "#155c80", "#1f98b8", "#62dce8", "#eafcff"
JADE, JADE2, JADEL = "#2fa886", "#1d7a63", "#7ee0b8"
GOLD, GOLD2, GOLDL = "#efbd3c", "#b9861c", "#ffe48a"
CORAL, EYE = "#ff6f5e", "#fff27a"
WHITE = "#ffffff"


def frames(n, fn):
    return {"fl%d" % (k + 1): fn(k) for k in range(n)}


def glow(s, op=1): return '<g filter="url(#blur)" opacity="%s">%s</g>' % (op, s)


def wave_line(pts, amp, phase, n=6):
    """a wavy line through the points (list of (x, y)), with n bumps that shift with phase (0..1)"""
    out = []
    m = len(pts) - 1
    for i in range(m * 8 + 1):
        u = i / float(m * 8)
        j = min(m - 1, int(u * m)); f = u * m - j
        x = pts[j][0] + (pts[j + 1][0] - pts[j][0]) * f
        y = pts[j][1] + (pts[j + 1][1] - pts[j][1]) * f
        dx, dy = pts[j + 1][0] - pts[j][0], pts[j + 1][1] - pts[j][1]
        L = math.hypot(dx, dy) or 1
        o = math.sin((u * n + phase) * 2 * math.pi) * amp
        out.append((x - dy / L * o, y + dx / L * o))
    return "M " + " L ".join("%.1f %.1f" % p for p in out)


def scales(x0, y0, x1, y1, col, step=12, clip=None):
    pat = "".join('<path d="M %d %d q %d %d %d 0" fill="none" stroke="%s" stroke-width="2.2"/>' % (x + (step // 2 if (y // step) % 2 else 0), y, step // 2, step * 0.8, step, col)
                  for y in range(y0, y1, step) for x in range(x0, x1, step))
    return '<g clip-path="url(#%s)">%s</g>' % (clip, pat) if clip else pat


# ---------------------------------------------------------------- serpent crown (head space)
FC = (128, 98)   # the frill fans out from here
ANG = [-100 + 25 * i for i in range(9)]
def frill_pt(a, r=1.0):
    t = math.radians(a)
    return FC[0] + 150 * r * math.sin(t), FC[1] - 102 * r * math.cos(t)

def frill_path():
    pts = []
    for i, a in enumerate(ANG):
        pts.append(frill_pt(a))
        if i < len(ANG) - 1: pts.append(frill_pt(a + 12.5, 0.8))
    d = "M %.1f %.1f " % (FC[0] - 60, FC[1] + 6)
    d += "L %.1f %.1f " % pts[0]
    for i in range(1, len(pts), 2):
        d += "Q %.1f %.1f %.1f %.1f " % (pts[i] + pts[i + 1])
    return d + "L %.1f %.1f Z" % (FC[0] + 60, FC[1] + 6)

HOOD = "M 40 98 Q 32 46 84 26 Q 128 12 172 26 Q 224 46 216 98 Q 172 82 128 86 Q 84 82 40 98 Z"
def crown():
    s = P(frill_path(), WATER, 5)
    # spines
    for a in ANG:
        x, y = frill_pt(a, 0.98)
        s += LN("M %.1f %.1f L %.1f %.1f" % (FC[0] + (x - FC[0]) * 0.35, FC[1] + (y - FC[1]) * 0.35, x, y), INK, 7) + LN("M %.1f %.1f L %.1f %.1f" % (FC[0] + (x - FC[0]) * 0.35, FC[1] + (y - FC[1]) * 0.35, x, y), GOLD, 3.5)
    # the serpent hood
    s += P(HOOD, JADE, 5)
    s += '<clipPath id="sthood"><path d="%s"/></clipPath>' % HOOD + scales(30, 4, 226, 100, JADE2, 13, "sthood")
    s += LN("M 66 42 Q 100 22 128 22", JADEL, 5)
    # gold brow ridges over glowing serpent eyes
    for x, side in ((86, -1), (170, 1)):
        s += EL(x, 56, 19, 12, "#25303a", 4, side * 12) + EL(x, 56, 14, 8, EYE, 0, side * 12) + EL(x, 56, 3.5, 8, INK, 0, side * 12)
        s += P("M %d %d Q %d %d %d %d L %d %d Q %d %d %d %d Z" % (x - side * 26, 50, x, 30, x + side * 26, 40, x + side * 24, 48, x, 38, x - side * 24, 56), GOLD, 4)
    # nostrils and the jaw band with fangs over the forehead
    s += EL(118, 34, 4, 2.5, JADE2, 0) + EL(138, 34, 4, 2.5, JADE2, 0)
    for x in (98, 158):
        s += P("M %d 84 L %d 108 L %d 84 Z" % (x - 7, x, x + 7), FOAM, 3.5)
    band = "M 40 98 Q 84 80 128 84 Q 172 80 216 98 L 214 86 Q 172 70 128 74 Q 84 70 42 86 Z"
    s += P(band, GOLD, 4) + LN("M 50 90 Q 128 70 206 90", GOLDL, 2.5)
    for x in (64, 192): s += GEM(x, 87, 4.5, AQUA)
    s += P("M 128 64 L 144 80 L 128 96 L 112 80 Z", GOLD, 4) + GEM(128, 80, 8, AQUA)
    # coral feathers at the ear sides
    for side in (-1, 1):
        x0 = 128 + side * 90
        for k, a in enumerate((side * 120, side * 140, side * 160)):
            s += '<g transform="translate(%d 92) rotate(%d)">%s</g>' % (x0, a, P("M 0 0 Q 8 -14 0 -30 Q -8 -14 0 0 Z", (CORAL, GOLD, CORAL)[k], 3) + LN("M 0 -4 L 0 -24", darker(CORAL, .7), 1.5))
    return HEAD(s)

def crown_mask():
    return HEAD(P(frill_path(), WHITE, 0))

def crown_foam(k):
    """foam rippling along the frill's edge"""
    pts = [frill_pt(a, 0.93) for a in range(-100, 101, 10)]
    d = wave_line(pts, 3.5, k / 4.0, n=14)
    s = LN(d, INK, 8) + LN(d, FOAM, 4.5)
    for i, a in enumerate(ANG[1:-1]):
        if (i + k) % 3 == 0:
            x, y = frill_pt(a, 1.04)
            s += CI(x, y - 3, 4, FOAM, 2.5)
    return HEAD(s)

def crown_eyes():
    return HEAD(glow(EL(86, 56, 16, 10, EYE, 0) + EL(170, 56, 16, 10, EYE, 0) + CI(128, 80, 12, AQUA, 0)))

# ---------------------------------------------------------------- shoulders (body space)
def pauldron():
    cx, cy = SH_C
    s = ""
    fin = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx - 26, cy - 10, cx - 40, cy - 34, cx - 52, cy - 44,
        cx - 36, cy - 40, cx - 26, cy - 46, cx - 18, cy - 34, cx - 4, cy - 40, cx - 2, cy - 18, cx - 26, cy - 10)
    s += P(fin, WATER, 4) + LN("M %d %d L %d %d M %d %d L %d %d" % (cx - 22, cy - 14, cx - 46, cy - 40, cx - 14, cy - 16, cx - 22, cy - 40), GOLD, 2.5)
    dome = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 30, cy + 8, cx + 26, cy - 22, cx - 4, cy - 22,
        cx - 36, cy - 20, cx - 38, cy + 12, cx - 4, cy + 22, cx + 30, cy + 8)
    s += P(dome, JADE, 5)
    s += '<clipPath id="stdome"><path d="%s"/></clipPath>' % dome + scales(cx - 40, cy - 24, cx + 34, cy + 24, JADE2, 10, "stdome")
    rim = "M %d %d Q %d %d %d %d" % (cx - 36, cy + 6, cx - 6, cy + 20, cx + 28, cy + 4)
    s += LN(rim, INK, 11) + LN(rim, GOLD, 7) + LN(rim, GOLDL, 2)
    # a little serpent rising from the outer edge
    neck = "M %d %d Q %d %d %d %d" % (cx - 30, cy + 4, cx - 50, cy - 6, cx - 44, cy - 24)
    s += LN(neck, INK, 13) + LN(neck, JADE, 7.5)
    hx, hy = cx - 44, cy - 28
    s += EL(hx - 3, hy, 11, 7, JADE, 3.5, -20) + CI(hx - 6, hy - 3, 2.6, EYE, 1.5)
    s += P("M %d %d L %d %d L %d %d" % (hx - 13, hy + 3, hx - 20, hy + 6, hx - 14, hy + 8), "none", 0) + LN("M %d %d L %d %d L %d %d M %d %d L %d %d" % (hx - 13, hy + 4, hx - 21, hy + 5, hx - 25, hy + 2, hx - 21, hy + 5, hx - 25, hy + 9), CORAL, 2)
    s += GEM(cx - 4, cy - 2, 6.5, AQUA)
    return BOTH(s)

def pauldron_fin():
    cx, cy = SH_C
    fin = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx - 26, cy - 10, cx - 40, cy - 34, cx - 52, cy - 44,
        cx - 36, cy - 40, cx - 26, cy - 46, cx - 18, cy - 34, cx - 4, cy - 40, cx - 2, cy - 18, cx - 26, cy - 10)
    return BOTH(P(fin, WHITE, 0))

def pauldron_glow():
    cx, cy = SH_C
    return BOTH(glow(CI(cx - 4, cy - 2, 11, AQUA, 0) + CI(cx - 50, cy - 31, 5, EYE, 0), .9))

# ---------------------------------------------------------------- chest (body space)
IDOL = (128, 164)
CHANNELS = ["M 92 136 Q 84 150 92 166 Q 100 182 90 200", "M 164 136 Q 172 150 164 166 Q 156 182 166 200"]
def chest():
    s = P(BODY_OUT, JADE, 5) + scales(46, 120, 210, 214, JADE2, 12, "chestclip")
    for d in CHANNELS: s += LN(d, INK, 13) + LN(d, DEEP, 8)
    s += P("M 88 118 Q 128 134 168 118 L 164 132 Q 128 148 92 132 Z", GOLD, 4)
    for x in (100, 114, 142, 156): s += CI(x, 132 + abs(x - 128) * -0.05, 3, AQUA, 2)
    # the serpent idol: a gold sun disc around a water orb
    x, y = IDOL
    for i in range(12):
        a = math.radians(i * 30)
        s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x + math.sin(a - 0.2) * 20, y - math.cos(a - 0.2) * 20, x + math.sin(a) * 31, y - math.cos(a) * 31,
                                                    x + math.sin(a + 0.2) * 20, y - math.cos(a + 0.2) * 20), GOLD, 3)
    s += CI(x, y, 22, GOLD, 4.5) + CI(x, y, 15, WATER, 3.5) + '<circle cx="%d" cy="%d" r="3.5" fill="#fff"/>' % (x - 6, y - 6)
    s += RC(60, 198, 136, 14, GOLD2, 4, 4) + "".join(CI(xx, 205, 3.5, AQUA, 2) for xx in (76, 102, 154, 180)) + RC(116, 195, 24, 20, GOLD, 4, 4) + GEM(128, 205, 5, AQUA)
    return s

def chest_water():
    return "".join(LN(d, WHITE, 8) for d in CHANNELS) + CI(IDOL[0], IDOL[1], 15, WHITE, 0)

def chest_glow(): return glow(CI(IDOL[0], IDOL[1], 20, AQUA, 0))

# ---------------------------------------------------------------- cape (side drapes of water)
def cape():
    s = "".join(P(p, DEEP, 5) for p in DRAPE_OUT) + "".join(P(p, "#0f3f5c", 3) for p in DRAPE_IN)
    for side in DRAPE_EDGE:
        pts = qpts(*side, n=8)
        out = -1 if side[0][0] < 128 else 1
        inner = [(x - out * 12, y) for x, y in pts]
        s += LN(wave_line(inner, 2.5, 0.2, 5), WATER, 4)
        s += LN(wave_line([(x - out * 22, y + 4) for x, y in pts[1:]], 2, 0.6, 4), WATER, 3)
    # gold clasps at the shoulders
    for x in (84, 172): s += CI(x, 118, 8, GOLD, 4) + GEM(x, 118, 4, AQUA)
    return s

def cape_mask(): return "".join(P(p, WHITE, 0) for p in DRAPE_OUT)

def cape_waves(k):
    """foaming wave crests curling along the outer edges"""
    s = ""
    for side in DRAPE_EDGE:
        out = -1 if side[0][0] < 128 else 1
        edge = qpts(*side, n=10)
        outer = wave_line([(x + out * 7, y) for x, y in edge], 3, k / 4.0, n=4)
        inner = [(x - out * 7, y) for x, y in edge]
        d = outer + " L " + " L ".join("%.1f %.1f" % p for p in reversed(inner)) + " Z"
        s += P(d, AQUA, 4) + LN(wave_line([(x + out * 3, y) for x, y in edge[1:]], 2, k / 4.0 + 0.1, n=4), FOAM, 2.5)
        for i, (x, y) in enumerate(edge[2::3]):
            if (i + k) % 2 == 0: s += CI(x + out * 12, y - 4, 3.2, FOAM, 2.2)
    return s

# ---------------------------------------------------------------- trident (right paw)
TL = 148
def trident():
    s = RC(-5, -TL, 10, TL + 28, GOLD2, 4)
    for y in (-24, -60, -96): s += RC(-7, y - 8, 14, 16, JADE, 3, 3)
    s += CI(0, 22, 7, GOLD, 4) + GEM(0, 22, 3.5, AQUA)
    y = -TL
    s += P("M -30 %d Q 0 %d 30 %d L 26 %d Q 0 %d -26 %d Z" % (y + 6, y + 22, y + 6, y - 6, y + 6, y - 6), GOLD, 4)
    for x, h in ((-28, 46), (28, 46)):
        s += P("M %d %d L %d %d L %d %d L %d %d L %d %d Z" % (x - 6, y - 2, x - 6, y - h + 12, x, y - h, x + 6, y - h + 12, x + 6, y - 2), GOLD, 4)
        s += P("M %d %d L %d %d L %d %d Z" % (x - (6 if x > 0 else -6), y - h + 18, x - (16 if x > 0 else -16), y - h + 26, x - (6 if x > 0 else -6), y - h + 28), GOLD, 3)
    s += P("M -8 %d L -8 %d L 0 %d L 8 %d L 8 %d Z" % (y - 4, y - 60, y - 76, y - 60, y - 4), GOLD, 4)
    s += LN("M -2 %d L -2 %d" % (y - 10, y - 58), GOLDL, 2.5)
    s += CI(0, y - 12, 9, WATER, 3.5) + '<circle cx="-3" cy="%d" r="2.5" fill="#fff"/>' % (y - 15)
    return RHAND(s)

def trident_swirl(k):
    """a ring of water spinning around the prongs"""
    y = -TL - 34
    s = ""
    for i in range(3):
        a0 = k * 30 + i * 120
        pts = []
        for j in range(9):
            a = math.radians(a0 + j * 11)
            pts.append((math.cos(a) * 40, y + math.sin(a) * 13 - j * 1.2))
        d = "M " + " L ".join("%.1f %.1f" % p for p in pts)
        front = math.sin(math.radians(a0 + 45)) > 0
        s += LN(d, INK, 9 if front else 7) + LN(d, AQUA if front else WATER, 5 if front else 3.5) + (LN(d, FOAM, 1.8) if front else "")
    return RHAND(s)

def trident_glow(): return RHAND(glow(CI(0, -TL - 12, 14, AQUA, 0) + EL(0, -TL - 34, 40, 18, AQUA, 0), .8))

# ---------------------------------------------------------------- aura: rising tide
def ripple(k):
    s = ""
    for i in range(3):
        f = ((k / 3.0) + i / 3.0) % 1.0
        rx, ry = 70 + f * 60, 12 + f * 9
        op = 1.0 - f
        s += '<ellipse cx="128" cy="222" rx="%.1f" ry="%.1f" fill="none" stroke="%s" stroke-width="%.1f" opacity="%.2f"/>' % (rx, ry, AQUA, 4 - f * 2, op)
        s += '<ellipse cx="128" cy="222" rx="%.1f" ry="%.1f" fill="none" stroke="%s" stroke-width="1.5" opacity="%.2f"/>' % (rx, ry, FOAM, op)
    return s

BUBBLES = {"kind": "particles", "sprite": "t_bubble", "color": [0.7, 0.95, 1.0], "alpha": 0.85}
AQ = [0.4, 0.9, 1.0]

SET = {
    "key": "st", "name": "Sunken Temple", "zone": "st", "lua": "SunkenTemple", "file": "sunken_temple",
    "about": "Sunken Temple set: the drowned serpent temple, each piece guaranteed from one Sunken Temple boss in Adventure until owned.",
    "preview_fur": "fur_snow",
    "pieces": [
        {"id": "set_st_crown", "slot": "head", "kind": "head", "art": "st_crown", "name": "Eranikus' Tidewyrm Crown", "rarity": 5,
         "icon": "INV_Misc_Head_Dragon_Green", "boss": "Shade of Eranikus", "word": "serpent crown",
         "svg": crown(), "layers": dict(frames(4, crown_foam), frill=crown_mask(), eyes=crown_eyes()),
         "anim": [
             {"kind": "scroll", "sprite": "a_swirl", "mask": K("st_crown", "frill"), "scale": 110, "vx": 18, "vy": -24,
              "color": AQ, "blend": "ADD", "alpha": 0.75},
             {"kind": "flip", "keys": [K("st_crown", "fl%d" % i) for i in range(1, 5)], "fps": 6},
             {"kind": "pulse", "key": K("st_crown", "eyes"), "a": [0.15, 0.95], "speed": 2.4, "blend": "ADD"},
             dict(BUBBLES, n=6, box=[20, 40, 492, 150], vx=[-8, 8], vy=[-60, -35], life=[1.2, 1.9], size=[9, 16], sway=6, grow=0.4, at="front"),
         ]},
        {"id": "set_st_shoulders", "slot": "shoulder", "kind": "shoulder", "art": "st_shoulders", "name": "Hakkar's Spawn Coils", "rarity": 4,
         "icon": "INV_Shoulder_23", "boss": "Spawn of Hakkar", "word": "shoulders",
         "svg": pauldron(), "layers": {"fin": pauldron_fin(), "glow": pauldron_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_swirl", "mask": K("st_shoulders", "fin"), "scale": 60, "vx": -14, "vy": -30, "color": AQ, "blend": "ADD", "alpha": 0.8},
             {"kind": "pulse", "key": K("st_shoulders", "glow"), "a": [0.1, 0.9], "speed": 2.0, "blend": "ADD"},
             dict(BUBBLES, n=3, box=[20, 150, 110, 230], vx=[-6, 6], vy=[-45, -25], life=[1.0, 1.6], size=[7, 12], sway=5, at="front"),
             dict(BUBBLES, n=3, box=[402, 150, 492, 230], vx=[-6, 6], vy=[-45, -25], life=[1.0, 1.6], size=[7, 12], sway=5, at="front"),
         ]},
        {"id": "set_st_chest", "slot": "chest", "kind": "chest", "art": "st_chest", "name": "Atal'ai Tidescale Vest", "rarity": 4,
         "icon": "INV_Chest_Chain_12", "boss": "Atal'alarion", "word": "chest",
         "svg": chest(), "layers": {"water": chest_water(), "glow": chest_glow()},
         "anim": [
             {"kind": "scroll", "sprite": "a_swirl", "mask": K("st_chest", "water"), "scale": 70, "vx": 8, "vy": 40, "color": AQ, "blend": "ADD"},
             {"kind": "pulse", "key": K("st_chest", "glow"), "a": [0.1, 0.8], "speed": 1.9, "blend": "ADD"},
         ]},
        {"id": "set_st_cape", "slot": "back", "kind": "back", "art": "st_cape", "name": "Ogom's Drowned Drape", "rarity": 4,
         "icon": "INV_Misc_Cape_17", "boss": "Ogom the Wretched", "word": "cape",
         "svg": cape(), "layers": dict(frames(4, cape_waves), water=cape_mask()),
         "anim": [
             {"kind": "scroll", "sprite": "a_swirl", "mask": K("st_cape", "water"), "scale": 120, "vx": 0, "vy": 34, "color": [0.3, 0.75, 0.95], "blend": "ADD", "alpha": 0.6},
             {"kind": "flip", "keys": [K("st_cape", "fl%d" % i) for i in range(1, 5)], "fps": 6},
             dict(BUBBLES, n=3, box=[50, 300, 110, 420], vx=[-6, 4], vy=[-50, -30], life=[1.2, 2.0], size=[8, 13], sway=5, at="behind"),
             dict(BUBBLES, n=3, box=[402, 300, 462, 420], vx=[-4, 6], vy=[-50, -30], life=[1.2, 2.0], size=[8, 13], sway=5, at="behind"),
         ]},
        {"id": "set_st_trident", "slot": "main", "kind": "weapon", "art": "st_trident", "name": "Jammal'an's Tidecaller Trident", "rarity": 5,
         "icon": "INV_Spear_04", "boss": "Jammal'an the Prophet", "word": "trident",
         "svg": trident(), "layers": dict(frames(4, trident_swirl), glow=trident_glow()),
         "anim": [
             {"kind": "flip", "keys": [K("st_trident", "fl%d" % i) for i in range(1, 5)], "fps": 10},
             {"kind": "pulse", "key": K("st_trident", "glow"), "a": [0.1, 0.7], "speed": 2.6, "blend": "ADD"},
         ]},
        {"id": "set_st_aura", "slot": "effect", "kind": "effect", "art": "fx_st_tide", "name": "Hakkar's Rising Tide", "rarity": 4,
         "icon": "Spell_Frost_SummonWaterElemental", "boss": "Shade of Hakkar", "word": "aura", "glow": (0.35, 0.85, 1.0),
         "fx": {"layer": "back", "anim": "pulse"},
         "layers": frames(3, ripple),
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [0.3, 0.75, 1.0], "a": [0.2, 0.45], "speed": 1.4, "blend": "ADD", "at": "behind"},
             {"kind": "flip", "keys": [K("fx_st_tide", "fl%d" % i) for i in range(1, 4)], "fps": 4, "at": "behind"},
             dict(BUBBLES, n=8, box=[60, 300, 452, 470], vx=[-10, 10], vy=[-90, -55], life=[1.6, 2.6], size=[10, 20], sway=10, grow=0.5, at="front"),
             dict(BUBBLES, n=6, box=[40, 200, 472, 460], vx=[-8, 8], vy=[-70, -40], life=[1.8, 2.8], size=[8, 14], sway=8, at="behind"),
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
