"""Death roll art (Casino tab > Death roll), in the sticker style of the cat and the Adventure
backgrounds (tools/make_backgrounds.py): flat colours, soft shapes far away, thick ink outlines up close.
usage: python3 tools/make_duel_art.py [work_dir] [preview.png]   -> Art/casino/*.tga
  colosseum.tga      512x256 arena: sand floor, stone arches, banners, a crowd of cat silhouettes, warm light
                     (kept for a future duel mode)
  tavern.tga         512x256 the death roll tavern: plank floor and wall, a stone hearth with a fire, the bar
                     with mugs and bottles, barrels, a dartboard, two lanterns and a cat-head sign
  dr_flop_fur.tga    256x256 a cat lying on its back, fur parts only (white, tinted to the cat's fur in game)
  dr_flop_line.tga   256x256 the same cat's outlines, belly, pads and nose (fixed colours, drawn on top)
  dr_xeyes.tga       256x256 the X eyes for that cat (same canvas, so all three turn together)
                     The three are drawn on the cat's own 64-pixel grid (4 texels a pixel, hard edges),
                     like Art/cat_fur.tga, so the flop looks like the same cat.
  dr_plate.tga       256x128 the dark plate behind the range in the middle of the arena
  dr_ghost.tga       128x128 a little ghost cat that floats up and fades
  dr_pop.tga         128x128 the bubble behind a roll number (white, tinted in game)
  dr_conf1..3.tga    32x32 confetti pieces: a ribbon, a paw and a star (white with an ink outline, tinted in game)
"""
import math, os, random, shutil, subprocess, sys, tempfile
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from make_art import write_tga
INK = "#3b2620"
OUT = os.path.join(ROOT, "Art", "casino")

def rect(x, y, w, h, c, op=1, sw=0):
    st = ' stroke="%s" stroke-width="%s"' % (INK, sw) if sw else ""
    return '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" opacity="%s"%s/>' % (x, y, w, h, c, op, st)
def path(d, c, sw=0, op=1, stroke=INK):
    st = ' stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"' % (stroke, sw) if sw else ""
    return '<path d="%s" fill="%s"%s opacity="%s"/>' % (d, c, st, op)
def line(d, c, sw, op=1):
    return '<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round" opacity="%s"/>' % (d, c, sw, op)
def circ(x, y, r, c, sw=0, op=1):
    st = ' stroke="%s" stroke-width="%s"' % (INK, sw) if sw else ""
    return '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"%s opacity="%s"/>' % (x, y, r, c, st, op)
def ell(x, y, rx, ry, c, sw=0, op=1, rot=0):
    st = ' stroke="%s" stroke-width="%s"' % (INK, sw) if sw else ""
    tr = ' transform="rotate(%.1f %.1f %.1f)"' % (rot, x, y) if rot else ""
    return '<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="%s"%s opacity="%s"%s/>' % (x, y, rx, ry, c, st, op, tr)

# ---------------------------------------------------------------- the colosseum (512x256, floor at 192)
W, H, FLOOR = 512, 256, 192
def cat_head(x, y, r, c):
    """a crowd silhouette: round head with two ears, and shoulders"""
    return (path("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x - r * 0.95, y - r * 0.2, x - r * 0.75, y - r * 1.45, x - r * 0.15, y - r * 0.85), c)
            + path("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x + r * 0.95, y - r * 0.2, x + r * 0.75, y - r * 1.45, x + r * 0.15, y - r * 0.85), c)
            + circ(x, y, r, c) + ell(x, y + r * 1.5, r * 1.5, r * 0.9, c))

def colosseum():
    rnd = random.Random(7)
    s = ""
    # warm evening sky above the stands
    for i, c in enumerate(("#f3a96a", "#f6bd7f", "#f9d197")):
        s += rect(0, i * 14, W, 15, c)
    s += circ(256, 30, 60, "#fff1b8", op=0.35) + circ(256, 30, 34, "#fff3c4", op=0.5)
    # upper stands: three rows of cheering cats (silhouettes), lighter rows further back
    s += rect(0, 26, W, 52, "#c4895c")
    for row, (y, r, cols) in enumerate(((36, 5.5, ("#a86a48", "#9c6044", "#b07250")),
                                        (50, 6.5, ("#8e5840", "#84503a", "#965e44")),
                                        (66, 7.5, ("#74462f", "#6a402c", "#7c4c34")))):
        x = -6 + row * 6
        while x < W + 10:
            s += cat_head(x + rnd.uniform(-2, 2), y + rnd.uniform(-1.5, 1.5), r * rnd.uniform(0.9, 1.1), rnd.choice(cols))
            x += r * 2.6 + rnd.uniform(0, 3)
        s += rect(0, y + r * 1.9, W, 2.5, "#5a3426", 0.45)
    # little pennants waved in the crowd
    for x, c in ((60, "#e0473c"), (148, "#f2c14e"), (228, "#3d8fd8"), (300, "#e0473c"), (382, "#f2c14e"), (458, "#3d8fd8")):
        y = 44 + rnd.uniform(-4, 6)
        s += line("M %.1f %.1f L %.1f %.1f" % (x, y + 16, x, y - 4), INK, 2) + path("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x, y - 4, x + 14, y + 1, x, y + 6), c, 1.5)
    # cornice between the stands and the arches
    s += rect(-4, 76, W + 8, 9, "#e7c08c", sw=3) + rect(-4, 85, W + 8, 4, "#b98352")
    # the arches: stone wall with dark openings, warm light inside
    s += rect(-4, 89, W + 8, 84, "#d59f6a", sw=3)
    for k in range(-1, 8):
        x = 36 + k * 64
        s += path("M %.1f 168 L %.1f 120 Q %.1f 98 %.1f 98 Q %.1f 98 %.1f 120 L %.1f 168 Z" % (x - 20, x - 20, x - 20, x, x + 20, x + 20, x + 20), "#5e3527", 3)
        s += ell(x, 160, 16, 8, "#ffb45a", op=0.55) + ell(x, 158, 9, 5, "#ffe08a", op=0.6)
        # stone blocks on the wall between arches
        for j, yy in enumerate((100, 118, 136, 154)):
            s += line("M %.1f %d L %.1f %d" % (x + 24, yy, x + 40, yy), "#b07a4a", 2)
            s += line("M %.1f %d L %.1f %d" % (x + 32 + (j % 2) * 4, yy, x + 32 + (j % 2) * 4, yy + 18), "#b07a4a", 2, 0.6)
    # pillars with torches and banners between the arches
    for k in range(0, 8):
        x = 68 + k * 64
        s += rect(x - 7, 92, 14, 78, "#e3b47e", sw=3) + rect(x - 10, 89, 20, 7, "#f0cb94", sw=2.5)
        if k % 2 == 0:
            col, trim = ("#c8362f", "#f2c14e") if k % 4 == 0 else ("#2f6fb8", "#f2c14e")
            s += path("M %.1f 96 L %.1f 96 L %.1f 140 L %.1f 132 L %.1f 140 Z" % (x - 12, x + 12, x + 12, x, x - 12), col, 3)
            s += rect(x - 14, 92, 28, 6, trim, sw=2)
            # a paw print on the banner
            s += circ(x, 120, 4.5, trim) + "".join(circ(x + dx, 112 + dy, 2, trim) for dx, dy in ((-5, 1), (-2, -2), (2, -2), (5, 1)))
        else:
            s += circ(x, 104, 14, "#ffb347", op=0.35) + circ(x, 104, 8, "#ffd77a", op=0.5)
            s += path("M %.1f 112 L %.1f 112 L %.1f 120 L %.1f 120 Z" % (x - 6, x + 6, x + 4, x - 4), "#6a4026", 2)
            s += path("M %.1f 110 Q %.1f 100 %.1f 94 Q %.1f 100 %.1f 110 Z" % (x - 6, x - 7, x, x + 7, x + 6), "#ff8a2a", 2)
            s += path("M %.1f 109 Q %.1f 103 %.1f 99 Q %.1f 103 %.1f 109 Z" % (x - 3, x - 3, x, x + 3, x + 3), "#ffe066")
    # low podium wall around the sand
    s += rect(-4, 168, W + 8, 26, "#b9804c", sw=3) + rect(-4, 172, W + 8, 4, "#d9a36a")
    for x in range(10, W, 46): s += rect(x, 180, 30, 9, "#a46e40", 0.8)
    # sand floor with a faint ring, little stones and paw prints
    s += rect(0, FLOOR, W, H - FLOOR, "#efcd8c") + rect(0, FLOOR, W, 7, "#f6dca6")
    s += line("M 0 %d L %d %d" % (FLOOR, W, FLOOR), INK, 3)
    s += ell(256, 228, 210, 22, "none", op=1).replace('fill="none"', 'fill="none" stroke="#d9b06a" stroke-width="3" stroke-dasharray="10 8"')
    for _ in range(40):
        s += circ(rnd.uniform(0, W), rnd.uniform(FLOOR + 10, H - 4), rnd.uniform(1, 2.4), rnd.choice(("#d8b070", "#e2bd7e", "#c99e5c")), op=0.9)
    for x, y, a in ((150, 236, -20), (176, 226, -10), (330, 238, 15), (356, 228, 5)):
        g = circ(x, y, 4.2, "#d3a964") + "".join(circ(x + dx, y + dy, 1.8, "#d3a964") for dx, dy in ((-5, -4), (-2, -7), (2, -7), (5, -4)))
        s += '<g transform="rotate(%d %d %d)">%s</g>' % (a, x, y, g)
    # warm light from above and a soft vignette
    defs = ('<defs><radialGradient id="warm" cx="50%" cy="35%" r="65%"><stop offset="0" stop-color="#ffd98a" stop-opacity=".35"/>'
            '<stop offset="1" stop-color="#ffd98a" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="vg" cx="50%" cy="55%" r="70%"><stop offset=".65" stop-color="#000" stop-opacity="0"/>'
            '<stop offset="1" stop-color="#000" stop-opacity=".35"/></radialGradient></defs>')
    s += '<rect width="%d" height="%d" fill="url(#warm)"/><rect width="%d" height="%d" fill="url(#vg)"/>' % (W, H, W, H)
    return defs + s

# ---------------------------------------------------------------- the tavern (512x256, floor at 192)
# Death roll is played here: a cosy cat tavern with a wooden floor and back wall, a stone hearth on
# the left, the bar with mugs in the middle (between the two cats), barrels and a dartboard on the
# right, two lanterns hanging from the beam and a cat-head sign over the bar. The cats stand on the
# floor in the lower third (about x 118 and x 394), in front of plain planks so they read well.
def mug(x, y, s=1.0, foam=True, body="#e2a94f"):
    """a little tankard standing on (x, y): body, handle, hoops and a foam top"""
    w, h = 12 * s, 15 * s
    out = line("M %.1f %.1f Q %.1f %.1f %.1f %.1f" % (x + w / 2, y - h * 0.75, x + w / 2 + 7 * s, y - h * 0.55, x + w / 2, y - h * 0.2), INK, 2.2 * s)
    out += rect(x - w / 2, y - h, w, h, body, sw=2.2 * s)
    out += rect(x - w / 2, y - h * 0.78, w, 2 * s, "#8a5a2e") + rect(x - w / 2, y - h * 0.32, w, 2 * s, "#8a5a2e")
    if foam:
        out += path("M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z"
                    % (x - w / 2 - 1, y - h, x - w / 4, y - h - 6 * s, x, y - h - 2 * s, x + w / 4, y - h - 7 * s, x + w / 2 + 1, y - h,
                       x, y - h + 2 * s, x - w / 2 - 1, y - h), "#fff8e6", 1.8 * s)
    return out

def bottle(x, y, c, h=18):
    """a bottle standing on (x, y)"""
    return (path("M %.1f %.1f L %.1f %.1f Q %.1f %.1f %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Q %.1f %.1f %.1f %.1f L %.1f %.1f Z"
                 % (x - 5, y, x - 5, y - h * 0.55, x - 5, y - h * 0.7, x - 2, y - h * 0.72, x - 2, y - h, x + 2, y - h,
                    x + 2, y - h * 0.72, x + 5, y - h * 0.7, x + 5, y - h * 0.55, x + 5, y), c, 2)
            + rect(x - 3.5, y - h * 0.45, 7, 5, "#f3e2b8") + rect(x - 2, y - h - 2, 4, 3, "#8a5a2e"))

def barrel_end(x, y, r):
    """a barrel lying down, seen from its end: wood rings and a dark hoop"""
    return (circ(x, y, r, "#a8683a", 2.5) + circ(x, y, r * 0.78, "#c2834e") + circ(x, y, r * 0.78, "none", 0).replace('fill="none"', 'fill="none" stroke="#6e4026" stroke-width="2.5"')
            + circ(x, y, r * 0.5, "#b47643") + circ(x, y, r * 0.22, "#9c5f35")
            + line("M %.1f %.1f L %.1f %.1f" % (x - r * 0.75, y, x + r * 0.75, y), "#8a5432", 1.5, 0.7)
            + circ(x, y, r, "none", 0).replace('fill="none"', 'fill="none" stroke="#4a3a34" stroke-width="3.5"'))

def lantern(x, top, y):
    """a lantern hanging from the beam at (x, top) down to y, with a warm glow"""
    out = circ(x, y + 12, 34, "#ffcf6a", op=0.18) + circ(x, y + 12, 20, "#ffe08a", op=0.25)
    out += line("M %.1f %.1f L %.1f %.1f" % (x, top, x, y), INK, 2)
    out += path("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x - 8, y + 4, x + 8, y + 4, x, y - 3), "#4a3a34", 2)
    out += rect(x - 7, y + 4, 14, 18, "#ffd86a", sw=2.5)
    out += rect(x - 4, y + 7, 8, 12, "#fff3b0")
    out += line("M %.1f %.1f L %.1f %.1f" % (x, y + 4, x, y + 22), INK, 1.8)
    out += rect(x - 9, y + 21, 18, 4, "#4a3a34", sw=2)
    return out

def tavern():
    rnd = random.Random(11)
    s = ""
    # back wall: vertical planks, warm brown, with seams and a few knots
    s += rect(0, 0, W, FLOOR, "#b9794a")
    x, k = 0, 0
    while x < W:
        pw = 22 + (k % 3) * 2
        s += rect(x, 14, pw, FLOOR - 14, ("#b47446", "#bf8150", "#b97a4b")[k % 3])
        s += line("M %.1f 14 L %.1f %d" % (x, x, FLOOR), "#8a5232", 2, 0.8)
        if k % 4 == 1: s += ell(x + pw / 2, 60 + (k * 37) % 70, 2.5, 4, "#91583a", op=0.7)
        x += pw; k += 1
    # ceiling beam with rafter ends
    s += rect(-4, -4, W + 8, 20, "#6e4026", sw=3)
    for x in range(20, W, 64):
        s += circ(x, 10, 8, "#a8683a", 2.5) + circ(x, 10, 4.5, "none", 0).replace('fill="none"', 'fill="none" stroke="#7a4728" stroke-width="1.5"')
    # wainscot: a rail and darker panels along the lower wall
    s += rect(-4, 150, W + 8, FLOOR - 150, "#8f5733", sw=3)
    s += rect(-4, 147, W + 8, 7, "#d39a5e", sw=2.5)
    for x in range(6, W, 40):
        s += rect(x, 160, 30, 26, "#7f4b2b", op=0.75)
    # a round window with the night sky (upper left, between the hearth and the left lantern)
    s += circ(130, 74, 20, "#2d3a66", 3) + circ(124, 69, 6, "#fff2b8") + circ(127, 67, 5, "#2d3a66")
    for sx, sy in ((140, 64), (138, 84), (118, 82), (146, 76)):
        s += circ(sx, sy, 1.4, "#fff6cc")
    s += line("M 110 74 L 150 74 M 130 54 L 130 94", "#6e4026", 3) + circ(130, 74, 20, "none", 0).replace('fill="none"', 'fill="none" stroke="#6e4026" stroke-width="4"')
    s += circ(130, 74, 22, "none", 0).replace('fill="none"', 'fill="none" stroke="%s" stroke-width="3"' % INK)
    # shelves behind the bar with bottles and mugs
    for y in (72, 104):
        s += rect(176, y, 160, 6, "#7a4728", sw=2.5)
        s += path("M 186 %d L 192 %d L 186 %d Z" % (y + 6, y + 6, y + 14), "#6e4026", 1.5) + path("M 326 %d L 320 %d L 326 %d Z" % (y + 6, y + 6, y + 14), "#6e4026", 1.5)
    for i, (bx, c) in enumerate(((186, "#4f9a5c"), (198, "#c0473c"), (210, "#e0a21b"), (224, "#4a7cc0"), (288, "#9a5cc0"), (300, "#4f9a5c"), (314, "#c0473c"), (326, "#e0a21b"))):
        s += bottle(bx, 72, c, 16 + (i % 3) * 3)
    for bx in (190, 206, 222, 292, 308, 324):
        s += mug(bx, 104, 0.8, foam=False, body="#d9a35a")
    # the sign over the bar: a cat head on a hanging board
    s += line("M 236 14 L 240 34 M 276 14 L 272 34", INK, 2)
    s += rect(226, 32, 60, 30, "#d8a868", sw=3) + rect(230, 36, 52, 22, "#c99556")
    cx, cy = 256, 50
    s += path("M %d %d L %d %d L %d %d Z" % (cx - 11, cy - 3, cx - 9, cy - 14, cx - 3, cy - 8), "#3b2620")
    s += path("M %d %d L %d %d L %d %d Z" % (cx + 11, cy - 3, cx + 9, cy - 14, cx + 3, cy - 8), "#3b2620")
    s += ell(cx, cy, 11, 8.5, "#3b2620") + circ(cx - 4, cy - 1, 1.6, "#ffd86a") + circ(cx + 4, cy - 1, 1.6, "#ffd86a")
    s += mug(cx - 20, 56, 0.55, body="#e2a94f") + mug(cx + 20, 56, 0.55, body="#e2a94f")
    # the stone hearth (left) with a fire: warm rounded stones on dark mortar
    s += rect(6, 14, 78, FLOOR - 14, "#6a4a3a", sw=3)
    for row, y in enumerate(range(17, FLOOR - 4, 13)):
        x = 8 - (row % 2) * 12
        while x < 82:
            w = rnd.choice((20, 24, 26))
            x0, x1 = max(9, x + 1), min(81, x + w - 1)
            if x1 - x0 > 5:
                s += '<rect x="%.1f" y="%.1f" width="%.1f" height="11" rx="3" fill="%s" stroke="#4a3a34" stroke-width="1.2"/>' % (
                    x0, y, x1 - x0, rnd.choice(("#d0a882", "#c49a74", "#d9b48c", "#bf9470")))
            x += w
    s += rect(6, 14, 78, FLOOR - 14, "none").replace('fill="none"', 'fill="none" stroke="%s" stroke-width="3"' % INK)
    s += rect(0, 104, 90, 10, "#7a4728", sw=3)    # mantel
    s += mug(22, 104, 0.7, foam=False, body="#c9a06a") + bottle(68, 104, "#4f9a5c", 15)
    s += path("M 20 %d L 20 140 Q 20 122 45 122 Q 70 122 70 140 L 70 %d Z" % (FLOOR, FLOOR), "#2e1c18", 3)
    s += ell(45, 180, 40, 22, "#ff8a2a", op=0.35) + ell(45, 198, 60, 10, "#ffb04a", op=0.35)
    s += rect(26, 178, 38, 7, "#6e4026", sw=2) + rect(30, 172, 30, 7, "#7f4b2b", sw=2)
    s += path("M 30 176 Q 28 160 36 150 Q 36 160 42 162 Q 40 146 48 136 Q 50 150 56 154 Q 60 146 58 140 Q 66 154 60 176 Z", "#ff7a26", 2.5)
    s += path("M 37 176 Q 36 166 42 158 Q 44 166 48 166 Q 48 156 53 150 Q 58 164 54 176 Z", "#ffc23a")
    s += path("M 42 176 Q 42 170 46 164 Q 50 170 50 176 Z", "#fff1a8")
    # a dartboard on the right wall
    s += circ(448, 76, 20, "#2e2a2a", 3)
    for r, c in ((16, "#f1e2c0"), (12, "#c8362f"), (8.5, "#f1e2c0"), (5, "#3f8a4e"), (2.2, "#c8362f")):
        s += circ(448, 76, r, c)
    for a in range(0, 360, 45):
        s += line("M 448 76 L %.1f %.1f" % (448 + 16 * math.cos(math.radians(a)), 76 + 16 * math.sin(math.radians(a))), "#2e2a2a", 1, 0.6)
    for dx, dy, a in ((-4, -3, -30), (5, 2, -20)):
        x0, y0 = 448 + dx, 76 + dy
        s += line("M %.1f %.1f L %.1f %.1f" % (x0, y0, x0 + 12 * math.cos(math.radians(a)), y0 + 12 * math.sin(math.radians(a))), INK, 2)
        s += path("M %.1f %.1f l 5 -4 l 1 6 Z" % (x0 + 12 * math.cos(math.radians(a)), y0 + 12 * math.sin(math.radians(a))), "#e0473c", 1.2)
    # lanterns on the beam, above the two cats
    s += lantern(150, 16, 36) + lantern(362, 16, 36)
    # the bar counter between the cats
    s += rect(168, 146, 176, FLOOR - 146, "#8a4f2c", sw=3)
    for x in range(176, 340, 34):
        s += rect(x, 154, 26, 32, "#9d5d34", sw=2)
    s += rect(162, 136, 188, 11, "#d9a066", sw=3) + rect(166, 138, 180, 3, "#f0c48a")
    s += mug(182, 136) + mug(198, 136, 0.9) + mug(316, 136, 0.9) + mug(332, 136)
    # barrels (right), seen from their ends, one with a tap
    s += barrel_end(452, 172, 19) + barrel_end(492, 172, 19) + barrel_end(472, 137, 19)
    s += rect(468, 133, 8, 6, "#8a8a8a", sw=1.8) + rect(470, 139, 4, 6, "#8a8a8a", sw=1.5)
    # floor: warm planks with staggered joints, a lighter edge under the wall
    s += rect(0, FLOOR, W, H - FLOOR, "#c98b52")
    for i, y in enumerate(range(FLOOR + 6, H, 12)):
        s += line("M 0 %d L %d %d" % (y, W, y), "#a96d3c", 2, 0.9)
        for x in range((i * 53) % 90, W, 90):
            s += line("M %d %d L %d %d" % (x, y - 12 if y - 12 > FLOOR else FLOOR, x, y), "#a96d3c", 2, 0.8)
    s += rect(0, FLOOR, W, 5, "#e0a86c")
    s += line("M 0 %d L %d %d" % (FLOOR, W, FLOOR), INK, 3)
    # a round rug where the cats stand
    s += ell(256, 226, 214, 24, "#b8423a", 3) + ell(256, 226, 200, 18, "none").replace('fill="none"', 'fill="none" stroke="#f2c14e" stroke-width="3" stroke-dasharray="9 7"')
    s += ell(256, 226, 180, 13, "#c9564a", op=0.6)
    for x, y, a in ((150, 236, -20), (176, 226, -10), (330, 238, 15), (356, 228, 5)):
        g = circ(x, y, 3.8, "#e7b65c") + "".join(circ(x + dx, y + dy, 1.6, "#e7b65c") for dx, dy in ((-5, -4), (-2, -7), (2, -7), (5, -4)))
        s += '<g transform="rotate(%d %d %d)" opacity=".8">%s</g>' % (a, x, y, g)
    # warm light from the hearth and the lanterns, and a soft vignette
    defs = ('<defs><radialGradient id="fire" cx="9%" cy="70%" r="45%"><stop offset="0" stop-color="#ffb04a" stop-opacity=".45"/>'
            '<stop offset="1" stop-color="#ffb04a" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="warm" cx="50%" cy="30%" r="65%"><stop offset="0" stop-color="#ffd98a" stop-opacity=".28"/>'
            '<stop offset="1" stop-color="#ffd98a" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="vg" cx="50%" cy="55%" r="70%"><stop offset=".62" stop-color="#1a0c06" stop-opacity="0"/>'
            '<stop offset="1" stop-color="#1a0c06" stop-opacity=".42"/></radialGradient></defs>')
    s += '<rect width="%d" height="%d" fill="url(#fire)"/><rect width="%d" height="%d" fill="url(#warm)"/><rect width="%d" height="%d" fill="url(#vg)"/>' % (W, H, W, H, W, H)
    return defs + s

# ---------------------------------------------------------------- the flopped cat (256x256, on its back)
# One shape list drawn three ways: fur fills (white, tinted in game), fixed parts and outlines, X eyes.
# Everything stays inside a circle of radius ~118 around the centre, so it can spin without clipping.
FUR = "#ffffff"
HX, HY, HR = 64, 148, 40
TAIL = "M 200 146 Q 238 146 236 116 Q 234 98 218 100 Q 214 108 222 112 Q 228 118 224 128 Q 220 138 198 136 Z"
# legs in the air, splayed out: (x, y, angle, length, paw tip bent this way); front legs (by the
# head) longer than the back ones
LEGS = [(102, 120, -38, 50, -1), (126, 112, -13, 54, -1), (160, 112, 14, 44, 1), (184, 120, 36, 40, 1)]
BODY = "M 74 160 Q 68 120 112 114 L 176 114 Q 214 118 208 160 Q 202 180 140 180 Q 80 180 74 160 Z"
EARS = ["M %d %d L %d %d L %d %d Z" % (HX - 22, HY - 30, HX - 50, HY - 22, HX - 34, HY - 2),
        "M %d %d L %d %d L %d %d Z" % (HX - 24, HY + 26, HX - 50, HY + 40, HX - 20, HY + 44)]
def leg(x, y, n, bend):
    """a leg n long pointing up from (x, y), with a round paw bent a little to one side"""
    top = y - n
    return ("M %d %d L %d %d Q %d %d %d %d Q %d %d %d %d L %d %d Z"
            % (x - 9, y + 4, x - 9, top + 10, x - 11 + bend * 2, top - 5, x + bend * 4, top - 5,
               x + 11 + bend * 2, top - 5, x + 9, top + 10, x + 9, y + 4))
def rot(a, x, y, body): return '<g transform="rotate(%d %d %d)">%s</g>' % (a, x, y, body)
def flop_svg(part):
    """part: fur (white fills, tinted in game), line (outlines and fixed colours, drawn over the fur), xeyes.
    Outlines of parts behind others are masked by the shapes in front (head > body > legs, tail; head > ears)."""
    if part == "fur":
        s = path(TAIL, FUR) + "".join(rot(a, x, y, path(leg(x, y, n, b), FUR)) for x, y, a, n, b in LEGS)
        return s + path(BODY, FUR) + "".join(path(e, FUR) for e in EARS) + circ(HX, HY, HR, FUR)
    if part == "xeyes":
        return ""   # drawn pixel by pixel in xeyes_pixels()
    head = circ(HX, HY, HR, "#000")
    defs = ('<defs><mask id="nohead"><rect width="256" height="256" fill="#fff"/>%s</mask>'
            '<mask id="nobody"><rect width="256" height="256" fill="#fff"/>%s%s</mask></defs>') % (head, head, path(BODY, "#000"))
    behind_body = path(TAIL, "none", 5.5) + "".join(rot(a, x, y, path(leg(x, y, n, b), "none", 5.5)) for x, y, a, n, b in LEGS)
    s = defs + '<g mask="url(#nobody)">%s</g>' % behind_body
    for x, y, a, n, b in LEGS:  # pink toe beans on the raised paws
        s += rot(a, x, y, ell(x + b * 2, y - n + 7, 6, 4.5, "#f6a3b4"))
    s += '<g mask="url(#nohead)">%s%s%s</g>' % (
        path("M 104 150 Q 108 128 142 126 Q 176 128 180 150 Q 172 166 142 166 Q 112 166 104 150 Z", "#fff6ea"),
        path(BODY, "none", 5.5),
        "".join(path(e, "none", 5.5) for e in EARS)
        + path("M %d %d L %d %d L %d %d Z" % (HX - 27, HY - 23, HX - 43, HY - 19, HX - 33, HY - 9), "#f6a3b4")
        + path("M %d %d L %d %d L %d %d Z" % (HX - 26, HY + 30, HX - 43, HY + 38, HX - 25, HY + 39), "#f6a3b4"))
    s += circ(HX, HY, HR, "none", 5.5)
    s += ell(HX + 12, HY + 22, 7, 5, "#f7a6a6", op=0.8) + ell(HX + 12, HY - 22, 7, 5, "#f7a6a6", op=0.8)   # blush
    s += path("M %d %d L %d %d L %d %d Z" % (HX + 17, HY - 5, HX + 17, HY + 5, HX + 24, HY), "#f08aa0", 2)  # nose
    s += path("M %d %d Q %d %d %d %d Q %d %d %d %d Z" % (HX + 26, HY - 6, HX + 36, HY - 7, HX + 35, HY, HX + 36, HY + 7, HX + 26, HY + 6), "#a8444a", 2.5)  # open mouth
    for dy in (-10, 10):  # whiskers
        s += line("M %d %d L %d %d" % (HX + 4, HY + dy, HX - 2, HY + dy * 3.2), INK, 2.5)
    return s

def ghost_svg():
    """a little ghost cat (128x128): round head with ears, wavy bottom, sleepy face"""
    d = ("M 34 62 L 30 28 L 50 42 Q 64 36 78 42 L 98 28 L 94 62 Q 98 86 94 104 Q 88 112 82 104 Q 76 112 70 104 "
         "Q 64 112 58 104 Q 52 112 46 104 Q 40 112 34 104 Q 30 86 34 62 Z")
    s = path(d, "#f4f8ff", 5, 0.92)
    s += path("M 36 34 L 47 44 L 38 52 Z", "#cfe0ff", op=0.8) + path("M 92 34 L 81 44 L 90 52 Z", "#cfe0ff", op=0.8)
    s += line("M 48 64 Q 54 58 60 64 M 68 64 Q 74 58 80 64", INK, 3.5)
    s += ell(64, 76, 4, 3, "#8aa0c8") + ell(46, 72, 5, 3.5, "#c8d6f8", op=0.9) + ell(82, 72, 5, 3.5, "#c8d6f8", op=0.9)
    s += line("M 104 30 Q 112 22 118 30", "#cfe0ff", 3) + line("M 10 44 Q 16 36 22 44", "#cfe0ff", 3)
    return s

def pop_svg():
    """the bubble behind a roll number (128x128): a puffy cloud burst, white with an ink outline"""
    pts = []
    n = 12
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        r0, r1 = 50, 58
        pts.append((64 + r0 * math.cos(a0), 64 + r0 * math.sin(a0) * 0.82))
        am = (a0 + a1) / 2
        pts.append((64 + r1 * 1.1 * math.cos(am), 64 + r1 * 1.1 * math.sin(am) * 0.82))
    d = "M %.1f %.1f" % pts[0]
    for i in range(0, len(pts), 2):
        c = pts[i + 1]; e = pts[(i + 2) % len(pts)]
        d += " Q %.1f %.1f %.1f %.1f" % (c[0], c[1], e[0], e[1])
    s = path(d + " Z", "#ffffff", 6)
    s += line("M 30 54 Q 36 36 54 30", "#e6e6e6", 5, 0.9)
    return s

def confetti_svg(k):
    """32x32 pieces, white with an ink outline (tinted in game): a curly ribbon, a paw, a star"""
    if k == 1:
        return path("M 6 22 Q 10 8 16 16 Q 22 24 26 10 L 29 12 Q 24 30 16 21 Q 10 14 9 24 Z", "#ffffff", 2.5)
    if k == 2:
        s = ell(16, 20, 7, 6, "#ffffff", 2.5)
        for dx, dy in ((-8, 10), (-3, 6), (3, 6), (8, 10)):
            s += circ(16 + dx, dy + 1, 3, "#ffffff", 2)
        return s
    pts = []
    for i in range(10):
        r = 14 if i % 2 == 0 else 6.5
        a = -math.pi / 2 + i * math.pi / 5
        pts.append("%.1f %.1f" % (16 + r * math.cos(a), 17 + r * math.sin(a)))
    return path("M " + " L ".join(pts) + " Z", "#ffffff", 2.5)

def plate_svg():
    """256x128: the dark rounded plate behind the range numbers, with a gold rim"""
    return ('<rect x="8" y="8" width="240" height="112" rx="34" fill="#2a1a22" opacity=".78" stroke="%s" stroke-width="6"/>'
            '<rect x="18" y="18" width="220" height="92" rx="26" fill="none" stroke="#e0a21b" stroke-width="3" opacity=".8"/>' % INK)

def xeyes_pixels():
    """the X eyes on the 64-pixel grid: a cream X five pixels wide with an ink rim, so they read on
    black fur as well as on white"""
    small = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    px = small.load()
    cream, ink = (255, 244, 220, 255), (59, 38, 32, 255)
    for cx, cy in ((HX // 4 + 1, (HY - 20) // 4), (HX // 4 + 1, (HY + 20) // 4 + 1)):
        x_ = {(cx + d, cy + d) for d in range(-2, 3)} | {(cx + d, cy - d) for d in range(-2, 3)}
        for (x, y) in x_:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if (x + dx, y + dy) not in x_: px[x + dx, y + dy] = ink
        for (x, y) in x_: px[x, y] = cream
    return small.resize((256, 256), Image.NEAREST)

def pixelize(im, grid=64, cut=110):
    """the cat's look: draw on a 64-pixel grid with hard edges, then scale each pixel up to 4x4"""
    small = im.resize((grid, grid), Image.BOX)
    r, g, b, a = small.split()
    a = a.point(lambda v: 255 if v >= cut else 0)
    small = Image.merge("RGBA", (r, g, b, a))
    return small.resize(im.size, Image.NEAREST)

def render(items, w, h, work):
    """items: name -> svg body; renders them at w x h and returns name -> PIL image"""
    d = os.path.join(work, "%dx%d" % (w, h))
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d): os.remove(os.path.join(d, f))
    for name, body in items.items():
        open(os.path.join(d, name + ".svg"), "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d">%s</svg>' % (w, h, body))
    subprocess.check_call(["node", os.path.join(HERE, "render_svg.js"), d, str(w), str(h)])
    return {name: Image.open(os.path.join(d, name + ".png")).convert("RGBA") for name in items}

def main():
    work = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="duelart")
    os.makedirs(OUT, exist_ok=True)
    out = {}
    out.update(render({"colosseum": colosseum(), "tavern": tavern()}, 512, 256, work))
    flop = render({"dr_flop_fur": flop_svg("fur"), "dr_flop_line": flop_svg("line"), "dr_xeyes": flop_svg("xeyes")}, 256, 256, work)
    out.update({k: pixelize(v) for k, v in flop.items()})
    out["dr_xeyes"] = xeyes_pixels()
    out.update(render({"dr_ghost": ghost_svg(), "dr_pop": pop_svg()}, 128, 128, work))
    out.update(render({"dr_plate": plate_svg()}, 256, 128, work))
    out.update(render({"dr_conf%d" % k: confetti_svg(k) for k in (1, 2, 3)}, 32, 32, work))
    for name, im in out.items():
        write_tga(im, os.path.join(OUT, name + ".tga"))
    if len(sys.argv) > 2:
        # preview: the tavern with a tinted flopped cat, the ghost, a pop and confetti
        bg = out["tavern"].resize((1024, 512), Image.LANCZOS)
        fur = out["dr_flop_fur"]
        r, g, b, a = fur.split()
        tinted = Image.merge("RGBA", (r.point(lambda p: p), g.point(lambda p: p * 184 // 255), b.point(lambda p: p * 107 // 255), a))
        bg.alpha_composite(tinted, (620, 250)); bg.alpha_composite(out["dr_flop_line"], (620, 250)); bg.alpha_composite(out["dr_xeyes"], (620, 250))
        bg.alpha_composite(out["dr_ghost"], (690, 120)); bg.alpha_composite(out["dr_pop"], (180, 120))
        for i, k in enumerate((1, 2, 3, 1, 2, 3)): bg.alpha_composite(out["dr_conf%d" % k], (200 + i * 40, 300 + (i % 2) * 30))
        bg.save(sys.argv[2])
    if len(sys.argv) <= 1: shutil.rmtree(work, ignore_errors=True)
    print("duel art:", len(out), "files in Art/casino")

if __name__ == "__main__":
    main()
