"""Blackrock Depths set (1.6): the Dark Iron forge. Heavy dark iron and brass, furnaces burning behind
grates, gears turning, white-hot metal, chimneys puffing smoke and showers of forge sparks (iron and
smoke, not Molten Core's rock and flame). Each piece is guaranteed from one Blackrock Depths boss in
Adventure until owned.
  python3 tools/sets/blackrock_depths.py            -> Art/v/k_brd_*.tga, Art/brd_*.tga, Sets/BlackrockDepths.lua
  python3 tools/set_preview.py tools/sets/blackrock_depths.py <out>   -> animated preview
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from setlib import *

# palette: dark iron (blue-grey), brass, furnace fire, white-hot metal
IRON, IRON2, IRONL = "#454c5c", "#2c313c", "#7a8496"
BRASS, BRASS2, BRASSL = "#cf9a3c", "#93661f", "#f6d07a"
FIRE, FIRE2, HOT, WHITEHOT = "#e8501c", "#ff8c22", "#ffc845", "#fff3c4"
WHITE = "#ffffff"


def frames(n, fn):
    return {"fl%d" % (k + 1): fn(random.Random(300 + k), k) for k in range(n)}


def glow(s, op=1): return '<g filter="url(#blur)" opacity="%s">%s</g>' % (op, s)


def flame(x, y, h, w, lean=0.0, ink=3.0):
    out = ""
    for k, (sc, col) in enumerate(zip((1.0, 0.7, 0.42), (FIRE, FIRE2, HOT))):
        hh, ww, tx = h * sc, w * sc, x + lean * sc
        out += P("M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f Z"
                 % (x - ww, y, x - ww * 1.1, y - hh * 0.5, tx - ww * 0.4, y - hh * 0.75, tx, y - hh,
                    tx + ww * 0.5, y - hh * 0.7, x + ww * 1.1, y - hh * 0.45, x + ww, y), col, ink if k == 0 else 0)
    return out


def rivets(pts, r=3, col=BRASSL): return "".join(CI(x, y, r, col, 2) for x, y in pts)


def gear(x, y, r, a, col=BRASS, teeth=8):
    """a brass cog turned by a degrees"""
    d = ""
    for i in range(teeth * 2):
        ang = math.radians(a + i * 180.0 / teeth)
        rr = r if i % 2 == 0 else r * 0.78
        for da in (-0.13, 0.13):
            d += "%s %.1f %.1f " % ("M" if d == "" else "L", x + math.sin(ang + da) * rr, y - math.cos(ang + da) * rr)
    return P(d + "Z", col, 3.5) + CI(x, y, r * 0.42, BRASS2, 3) + CI(x, y, r * 0.16, IRON2, 0)


def grate(x0, y0, x1, y1, arch=True, n=3):
    """iron bars over a furnace window"""
    s = ""
    for i in range(1, n + 1):
        x = x0 + (x1 - x0) * i / (n + 1.0)
        s += LN("M %.1f %.1f L %.1f %.1f" % (x, y0 + (6 if arch else 0), x, y1), INK, 6) + LN("M %.1f %.1f L %.1f %.1f" % (x, y0 + (6 if arch else 0), x, y1), IRONL, 2.5)
    ym = (y0 + y1) / 2.0
    s += LN("M %.1f %.1f L %.1f %.1f" % (x0, ym, x1, ym), INK, 6) + LN("M %.1f %.1f L %.1f %.1f" % (x0, ym, x1, ym), IRONL, 2.5)
    return s


def fire_in(clip_id, shape, x0, x1, ybot, h, rnd, n=4):
    s = P(shape, FIRE, 0)
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        s += flame(x, ybot + 4, h * (0.7 + rnd.random() * 0.5), (x1 - x0) / n * 0.75, lean=(rnd.random() - 0.5) * 8, ink=0)
    return '<clipPath id="%s"><path d="%s"/></clipPath><g clip-path="url(#%s)">%s</g>' % (clip_id, shape, clip_id, s)


# ---------------------------------------------------------------- forge crown (head space)
WIN = "M 106 54 L 106 26 Q 128 4 150 26 L 150 54 Z"      # the furnace window in the crown's front tower
CHIM = [(34, 24), (222, 24)]                                # chimney tops (x, y)
def crown():
    s = ""
    # chimneys at the sides, leaning out
    for (x, y), side in zip(CHIM, (-1, 1)):
        bx = x - side * 14
        stack = "M %d 86 L %d %d L %d %d L %d 86 Z" % (bx - 15, x - 11, y + 8, x + 11, y + 8, bx + 15)
        s += P(stack, IRON, 4.5) + RC(x - 16, y, 32, 13, BRASS, 3, 4) + EL(x, y + 2, 11, 3.5, IRON2, 0)
        s += LN("M %d 78 L %d %d" % (bx - 6, x - 5, y + 18), IRONL, 3)
        s += RC(bx - 12 + side * 2, 52, 24, 8, BRASS2, 2, 3)
    # battlements
    for x, top in ((66, 30), (86, 22), (170, 22), (190, 30)):
        s += RC(x - 11, top, 22, 74 - top, IRON, 3, 4.5) + RC(x - 11, top, 22, 8, BRASS, 2, 3) + LN("M %d %d L %d 70" % (x - 5, top + 12, x - 5), IRONL, 2.5)
    # the front furnace tower
    tower = "M 96 80 L 96 22 Q 128 -12 160 22 L 160 80 Z"
    s += P(tower, IRON, 5) + LN("M 102 24 Q 128 -4 154 24", IRONL, 3)
    s += P(WIN, IRON2, 4)
    s += P("M 122 0 L 128 -10 L 134 0 Z", BRASS, 3)
    # the heavy band with a white-hot seam
    band = "M 42 100 Q 128 80 214 100 L 212 66 Q 128 48 44 66 Z"
    s += P(band, IRON, 5)
    s += LN("M 48 74 Q 128 56 208 74", BRASS, 6) + LN("M 48 74 Q 128 56 208 74", INK, 1.5)
    s += LN("M 50 92 Q 128 74 206 92", INK, 7) + LN("M 50 92 Q 128 74 206 92", FIRE2, 4) + LN("M 50 92 Q 128 74 206 92", HOT, 1.6)
    s += rivets([(60, 82), (84, 77), (172, 77), (196, 82)])
    # the Dark Iron emblem: an anvil on a brass shield
    s += P("M 112 62 L 144 62 L 144 76 Q 128 92 112 76 Z", BRASS, 4)
    s += P("M 118 68 L 138 68 L 134 73 L 131 73 L 133 80 L 123 80 L 125 73 L 122 73 Z", IRON2, 2)
    return HEAD(s)

def crown_fire(rnd, k):
    s = fire_in("brdwin%d" % k, WIN, 106, 150, 54, 30, rnd, 3) + grate(106, 26, 150, 54, n=2)
    s += P(WIN, "none", 4)
    for (x, y), side in zip(CHIM, (-1, 1)):   # fire belching from the chimneys
        s += flame(x - 6, y + 2, 24 * (0.8 + rnd.random() * 0.3), 7, lean=side * 6 + (rnd.random() - 0.5) * 6)
        s += flame(x + 6, y + 2, 30 * (0.8 + rnd.random() * 0.25), 8, lean=side * 8 + (rnd.random() - 0.5) * 6)
    return HEAD(s)

def crown_glow():
    return HEAD(glow(P(WIN, HOT, 0) + LN("M 50 92 Q 128 74 206 92", HOT, 8)) + LN("M 50 92 Q 128 74 206 92", WHITEHOT, 2))

# ---------------------------------------------------------------- shoulders (body space)
def pauldron():
    cx, cy = SH_C
    s = ""
    # a small chimney vent on top
    s += P("M %d %d L %d %d L %d %d L %d %d Z" % (cx - 20, cy - 12, cx - 24, cy - 38, cx - 10, cy - 38, cx - 8, cy - 14), IRON, 4) + RC(cx - 27, cy - 44, 20, 9, BRASS, 2, 3.5)
    # three stacked iron lames
    for k in range(3):
        y = cy - 18 + k * 12; w = 34 - k * 3
        lame = "M %d %d Q %d %d %d %d L %d %d Q %d %d %d %d Z" % (cx - w - 4, y + 12, cx - 4, y - 14, cx + w - 2, y + 6, cx + w - 4, y + 16,
                                                              cx - 4, y - 2, cx - w - 2, y + 22)
        s += P(lame, IRON if k % 2 == 0 else IRONL, 4.5)
        s += LN("M %d %d Q %d %d %d %d" % (cx - w - 2, y + 18, cx - 4, y + 2, cx + w - 4, y + 13), FIRE2, 2.5)
    rim = "M %d %d Q %d %d %d %d" % (cx - 38, cy + 18, cx - 4, cy + 8, cx + 26, cy + 18)
    s += LN(rim, INK, 11) + LN(rim, BRASS, 7) + LN(rim, BRASSL, 2)
    s += rivets([(cx - 26, cy + 15), (cx - 6, cy + 12), (cx + 14, cy + 15)], 2.8, IRON2)
    s += gear(cx + 10, cy - 10, 10, 0)
    return BOTH(s)

def pauldron_glow():
    cx, cy = SH_C
    s = ""
    for k in range(3):
        y = cy - 18 + k * 12; w = 34 - k * 3
        s += LN("M %d %d Q %d %d %d %d" % (cx - w - 2, y + 18, cx - 4, y + 2, cx + w - 4, y + 13), HOT, 6)
    return BOTH(glow(s, .7))

def pauldron_gears(rnd, k):
    cx, cy = SH_C
    return BOTH(gear(cx + 10, cy - 10, 10, k * 15))

# ---------------------------------------------------------------- chest (body space)
DOOR = (128, 166, 20)
def chest():
    s = P(BODY_OUT, IRON, 5)
    s += LN("M 82 132 Q 74 170 76 206", IRONL, 4) + LN("M 174 132 Q 182 170 180 206", IRON2, 4)
    # brass plates down the sides with rivets
    for side in (-1, 1):
        plate = "M %d 128 L %d 128 L %d 196 L %d 196 Z" % (128 + side * 40, 128 + side * 52, 128 + side * 56, 128 + side * 42)
        s += P(plate, BRASS, 3.5) + rivets([(128 + side * 47, y) for y in (138, 162, 186)], 2.6, BRASS2)
    s += P("M 86 118 Q 128 132 170 118 L 166 132 Q 128 146 90 132 Z", BRASS, 4)
    # the furnace door
    x, y, r = DOOR
    s += CI(x, y, r + 9, IRON2, 5) + rivets([(x + math.sin(math.radians(a)) * (r + 4.5), y - math.cos(math.radians(a)) * (r + 4.5)) for a in range(0, 360, 45)], 2.4, BRASSL)
    s += CI(x, y, r, IRON2, 3)
    s += RC(60, 198, 136, 14, IRON2, 4, 4) + RC(116, 195, 24, 20, BRASS, 4, 4) + CI(128, 205, 5, FIRE2, 2.5)
    return s

def chest_fire(rnd, k):
    x, y, r = DOOR
    shape = "M %d %d A %d %d 0 1 0 %d %d A %d %d 0 1 0 %d %d Z" % (x - r, y, r, r, x + r, y, r, r, x - r, y)
    s = fire_in("brddoor%d" % k, shape, x - r, x + r, y + r, 34, rnd, 3)
    for i in range(1, 4):
        xx = x - r + 2 * r * i / 4.0
        hh = math.sqrt(max(0, r * r - (xx - x) ** 2))
        s += LN("M %.1f %.1f L %.1f %.1f" % (xx, y - hh, xx, y + hh), INK, 5) + LN("M %.1f %.1f L %.1f %.1f" % (xx, y - hh, xx, y + hh), IRONL, 2)
    s += CI(x, y, r, "none", 3.5)
    # cogs turning in the upper corners
    s += gear(98, 146, 12, k * 15) + gear(158, 146, 12, -k * 15)
    return s

def chest_glow(): return glow(CI(DOOR[0], DOOR[1], DOOR[2] + 8, FIRE2, 0))

# ---------------------------------------------------------------- cape (side drapes of chainmail and iron)
def cape():
    s = "".join(P(p, IRON, 5) for p in DRAPE_OUT) + "".join(P(p, IRON2, 3) for p in DRAPE_IN)
    clip = "".join('<clipPath id="brdcape%d"><path d="%s"/></clipPath>' % (i, p) for i, p in enumerate(DRAPE_OUT))
    pat = "".join('<path d="M %d %d q 5 5 10 0" fill="none" stroke="%s" stroke-width="2"/>' % (x + (5 if (y // 8) % 2 else 0), y, IRONL, ) for y in range(104, 216, 8) for x in range(24, 236, 10))
    s += clip + '<g clip-path="url(#brdcape0)">%s</g><g clip-path="url(#brdcape1)">%s</g>' % (pat, pat)
    for side in DRAPE_EDGE:   # a forge-heated hem
        out = -1 if side[0][0] < 128 else 1
        s += LN(hem(side, out, -6), INK, 9) + LN(hem(side, out, -6), FIRE2, 5)
    # iron plates hanging along the outer edges
    for side in DRAPE_EDGE:
        out = -1 if side[0][0] < 128 else 1
        for i, (x, y) in enumerate(qpts(*side, n=7)[1:]):
            s += '<g transform="translate(%.1f %.1f) rotate(%d)">%s</g>' % (x + out * 2, y, out * 20, P("M -7 -6 L 7 -6 L 7 6 L -7 6 Z", IRON2, 3) + CI(0, -1, 2, BRASSL, 1.5))
    for x in (84, 172): s += gear(x, 118, 9, 10, BRASS, 6)
    return s

def hem(side, out, off):
    return "M " + " L ".join("%.1f %.1f" % (x + out * off, y) for x, y in qpts(*side, n=10))

def cape_glow():
    s = ""
    for side in DRAPE_EDGE:
        out = -1 if side[0][0] < 128 else 1
        s += LN(hem(side, out, -6), HOT, 7)
    return glow(s, .9) + "".join(LN(hem(side, -1 if side[0][0] < 128 else 1, -6), WHITEHOT, 2.5) for side in DRAPE_EDGE)

# ---------------------------------------------------------------- anvil hammer (right paw)
HL = 140
HX = -36   # the head sits left of the haft so the striking face stays inside the canvas
FACE = "M 38 %d L 52 %d L 52 %d L 38 %d Z" % (-HL - 40, -HL - 40, -HL + 4, -HL + 4)
def hammer():
    s = RC(-6, -HL, 12, HL + 28, "#4a3a30", 4)
    for y in (-26, -62, -98): s += RC(-8, y - 6, 16, 10, BRASS, 3, 3)
    s += CI(0, 22, 8, IRON, 4) + CI(0, 22, 3.5, BRASSL, 0)
    y = -HL
    h = ""
    # an anvil for a head: horn to the left, flat striking face to the right
    head = ("M -16 %d L 40 %d L 40 %d L 22 %d L 22 %d L -14 %d L -14 %d Q -40 %d -64 %d Q -38 %d -16 %d Z"
            % (y - 40, y - 40, y - 22, y - 16, y + 4, y + 4, y - 16, y - 20, y - 34, y - 34, y - 40))
    h += P(head, IRON, 5)
    h += LN("M -14 %d L 36 %d" % (y - 34, y - 34), IRONL, 3.5)
    h += P(FACE, "#8a6a5a", 4)
    s += '<g transform="translate(%d 0)">%s</g>' % (HX, h)
    s += RC(-7, y - 44, 14, 52, BRASS, 3, 4) + rivets([(0, y - 34), (0, y - 4)], 2.4, BRASS2)
    return RHAND(s)

def hammer_glow():
    y = -HL
    g = glow(P(FACE, HOT, 0)) + P(FACE, FIRE2, 0) + LN("M 45 %d L 45 %d" % (y - 36, y), WHITEHOT, 4)
    return RHAND('<g transform="translate(%d 0)">%s</g>' % (HX, g))

def hammer_sparks(rnd, k):
    """a burst of sparks flying off the striking face"""
    y = -HL - 18
    s = ""
    for i in range(7):
        a = math.radians(-85 + rnd.random() * 120)
        d0 = 4 + ((k * 6 + i * 9) % 20)
        ln = 5 + rnd.random() * 7
        x0, y0 = 56 + HX + math.cos(a) * d0, y + math.sin(a) * d0
        x1, y1 = x0 + math.cos(a) * ln, y0 + math.sin(a) * ln
        s += LN("M %.1f %.1f L %.1f %.1f" % (x0, y0, x1, y1), FIRE2, 4) + LN("M %.1f %.1f L %.1f %.1f" % (x0, y0, x1, y1), WHITEHOT, 1.8)
    return RHAND(s)

# ---------------------------------------------------------------- particles
SMOKE = {"kind": "particles", "sprite": "a_glow", "color": [0.42, 0.42, 0.48], "color2": [0.22, 0.22, 0.27], "alpha": 0.8}
SPARKS = {"kind": "particles", "sprite": "a_spark", "blend": "ADD", "color": [1.0, 0.92, 0.6], "color2": [1.0, 0.45, 0.1]}

SET = {
    "key": "brd", "name": "Blackrock Depths", "zone": "brd", "lua": "BlackrockDepths", "file": "blackrock_depths",
    "about": "Blackrock Depths set: the Dark Iron forge, each piece guaranteed from one Blackrock Depths boss in Adventure until owned.",
    "preview_fur": "fur_ginger",
    "pieces": [
        {"id": "set_brd_crown", "slot": "head", "kind": "head", "art": "brd_crown", "name": "Thaurissan's Forge Crown", "rarity": 5,
         "icon": "INV_Crown_01", "boss": "Emperor Dagran Thaurissan", "word": "forge crown",
         "svg": crown(), "layers": dict(frames(4, crown_fire), glow=crown_glow()),
         "anim": [
             {"kind": "flip", "keys": [K("brd_crown", "fl%d" % i) for i in range(1, 5)], "fps": 9},
             {"kind": "pulse", "key": K("brd_crown", "glow"), "a": [0.25, 1.0], "speed": 3.0, "blend": "ADD", "flicker": True},
             dict(SMOKE, n=4, box=[88, 2, 112, 18], vx=[-34, -16], vy=[-30, -14], life=[1.4, 2.0], size=[30, 40], grow=1.6, sway=4, at="front"),
             dict(SMOKE, n=4, box=[400, 2, 424, 18], vx=[16, 34], vy=[-30, -14], life=[1.4, 2.0], size=[30, 40], grow=1.6, sway=4, at="front"),
             dict(SPARKS, n=6, box=[80, 0, 432, 40], vx=[-40, 40], vy=[-70, -30], life=[0.5, 0.9], size=[10, 16], at="front"),
         ]},
        {"id": "set_brd_shoulders", "slot": "shoulder", "kind": "shoulder", "art": "brd_shoulders", "name": "Bael'Gar's Furnace Pauldrons", "rarity": 4,
         "icon": "INV_Shoulder_15", "boss": "Bael'Gar", "word": "shoulders",
         "svg": pauldron(), "layers": dict(frames(3, pauldron_gears), glow=pauldron_glow()),
         "anim": [
             {"kind": "flip", "keys": [K("brd_shoulders", "fl%d" % i) for i in range(1, 4)], "fps": 6},
             {"kind": "pulse", "key": K("brd_shoulders", "glow"), "a": [0.05, 0.6], "speed": 2.4, "blend": "ADD", "flicker": True},
             dict(SMOKE, n=3, box=[58, 150, 76, 166], vx=[-20, -6], vy=[-34, -20], life=[1.2, 1.8], size=[24, 30], grow=1.4, sway=3, at="front"),
             dict(SMOKE, n=3, box=[436, 150, 454, 166], vx=[6, 20], vy=[-34, -20], life=[1.2, 1.8], size=[24, 30], grow=1.4, sway=3, at="front"),
         ]},
        {"id": "set_brd_chest", "slot": "chest", "kind": "chest", "art": "brd_chest", "name": "Incendius' Forge-Heart Cuirass", "rarity": 4,
         "icon": "INV_Chest_Plate11", "boss": "Lord Incendius", "word": "chest",
         "svg": chest(), "layers": dict(frames(3, chest_fire), glow=chest_glow()),
         "anim": [
             {"kind": "pulse", "key": K("brd_chest", "glow"), "a": [0.2, 0.85], "speed": 2.6, "blend": "ADD", "flicker": True},
             {"kind": "flip", "keys": [K("brd_chest", "fl%d" % i) for i in range(1, 4)], "fps": 8},
         ]},
        {"id": "set_brd_cape", "slot": "back", "kind": "back", "art": "brd_cape", "name": "Anub'shiah's Chainweave Drape", "rarity": 4,
         "icon": "INV_Misc_Cape_20", "boss": "Anub'shiah", "word": "cape",
         "svg": cape(), "layers": {"glow": cape_glow()},
         "anim": [
             {"kind": "pulse", "key": K("brd_cape", "glow"), "a": [0.15, 1.0], "speed": 2.2, "blend": "ADD", "flicker": True},
             dict(SPARKS, n=4, box=[44, 280, 90, 400], vx=[-20, 0], vy=[30, 80], life=[0.6, 1.0], size=[8, 12], at="behind"),
             dict(SPARKS, n=4, box=[422, 280, 468, 400], vx=[0, 20], vy=[30, 80], life=[0.6, 1.0], size=[8, 12], at="behind"),
         ]},
        {"id": "set_brd_hammer", "slot": "main", "kind": "weapon", "art": "brd_hammer", "name": "Angerforge's Anvil Hammer", "rarity": 5,
         "icon": "INV_Hammer_09", "boss": "General Angerforge", "word": "hammer",
         "svg": hammer(), "layers": dict(frames(4, hammer_sparks), glow=hammer_glow()),
         "anim": [
             {"kind": "pulse", "key": K("brd_hammer", "glow"), "a": [0.3, 1.0], "speed": 3.2, "blend": "ADD", "flicker": True},
             {"kind": "flip", "keys": [K("brd_hammer", "fl%d" % i) for i in range(1, 5)], "fps": 10, "blend": "ADD"},
         ]},
        {"id": "set_brd_aura", "slot": "effect", "kind": "effect", "art": "fx_brd_forge", "name": "Flamelash's Forge Sparks", "rarity": 4,
         "icon": "Spell_Fire_Incinerate", "boss": "Ambassador Flamelash", "word": "aura", "glow": (1.0, 0.5, 0.15),
         "fx": {"layer": "back", "anim": "flicker"},
         "anim": [
             {"kind": "pulse", "sprite": "a_catglow", "rect": [0, 0, 512, 512], "color": [1.0, 0.4, 0.1], "a": [0.15, 0.4], "speed": 2.4, "blend": "ADD", "flicker": True, "at": "behind"},
             dict(SPARKS, n=8, box=[110, 380, 402, 460], vx=[-90, 90], vy=[-140, -60], life=[0.6, 1.1], size=[10, 18], at="front"),
             dict(SPARKS, n=6, box=[60, 100, 452, 300], vx=[-30, 30], vy=[40, 90], life=[0.7, 1.2], size=[8, 13], at="behind"),
             dict(SMOKE, n=5, box=[80, 300, 432, 440], vx=[-12, 12], vy=[-40, -24], life=[2.2, 3.2], size=[40, 56], grow=1.5, sway=8, alpha=0.45, at="behind"),
         ]},
    ],
}

if __name__ == "__main__":
    main(SET)
