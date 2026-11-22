"""Death roll art (Casino tab > Death roll), in the sticker style of the cat and the Adventure
backgrounds (tools/make_backgrounds.py): flat colours, soft shapes far away, thick ink outlines up close.
usage: python3 tools/make_duel_art.py [work_dir] [preview.png]   -> Art/casino/*.tga
  colosseum.tga      512x256 arena: sand floor, stone arches, banners, a crowd of cat silhouettes, warm light
  dr_flop_fur.tga    256x256 a cat lying on its back, fur parts only (white, tinted to the cat's fur in game)
  dr_flop_line.tga   256x256 the same cat's outlines, belly, pads and nose (fixed colours, drawn on top)
  dr_xeyes.tga       256x256 the X eyes for that cat (same canvas, so all three turn together)
  dr_ghost.tga       128x128 a little ghost cat that floats up and fades
  dr_pop.tga         128x128 the bubble behind a roll number (white, tinted in game)
  dr_conf1..3.tga    32x32 confetti pieces (white, tinted in game)
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

# ---------------------------------------------------------------- the flopped cat (256x256, on its back)
# One shape list drawn three ways: fur fills (white, tinted in game), fixed parts and outlines, X eyes.
# Everything stays inside a circle of radius ~118 around the centre, so it can spin without clipping.
FUR = "#ffffff"
HX, HY, HR = 64, 148, 40
TAIL = "M 200 146 Q 238 146 236 116 Q 234 98 218 100 Q 214 108 222 112 Q 228 118 224 128 Q 220 138 198 136 Z"
LEGS = [(104, 118, -16), (128, 110, -5), (158, 110, 5), (182, 118, 16)]
BODY = "M 74 160 Q 68 120 112 114 L 176 114 Q 214 118 208 160 Q 202 180 140 180 Q 80 180 74 160 Z"
EARS = ["M %d %d L %d %d L %d %d Z" % (HX - 22, HY - 30, HX - 50, HY - 22, HX - 34, HY - 2),
        "M %d %d L %d %d L %d %d Z" % (HX - 24, HY + 26, HX - 50, HY + 40, HX - 20, HY + 44)]
def leg(x, y): return "M %d %d L %d %d Q %d %d %d %d Q %d %d %d %d L %d %d Z" % (x - 9, y + 4, x - 9, y - 34, x - 9, y - 46, x, y - 46, x + 9, y - 46, x + 9, y - 34, x + 9, y + 4)
def rot(a, x, y, body): return '<g transform="rotate(%d %d %d)">%s</g>' % (a, x, y, body)
def flop_svg(part):
    """part: fur (white fills, tinted in game), line (outlines and fixed colours, drawn over the fur), xeyes.
    Outlines of parts behind others are masked by the shapes in front (head > body > legs, tail; head > ears)."""
    if part == "fur":
        s = path(TAIL, FUR) + "".join(rot(a, x, y, path(leg(x, y), FUR)) for x, y, a in LEGS)
        return s + path(BODY, FUR) + "".join(path(e, FUR) for e in EARS) + circ(HX, HY, HR, FUR)
    if part == "xeyes":
        s = ""
        for ex, ey in ((HX + 2, HY - 15), (HX + 2, HY + 15)):
            s += line("M %d %d L %d %d M %d %d L %d %d" % (ex - 7, ey - 7, ex + 7, ey + 7, ex - 7, ey + 7, ex + 7, ey - 7), INK, 5.5)
        return s
    head = circ(HX, HY, HR, "#000")
    defs = ('<defs><mask id="nohead"><rect width="256" height="256" fill="#fff"/>%s</mask>'
            '<mask id="nobody"><rect width="256" height="256" fill="#fff"/>%s%s</mask></defs>') % (head, head, path(BODY, "#000"))
    behind_body = path(TAIL, "none", 7) + "".join(rot(a, x, y, path(leg(x, y), "none", 7)) for x, y, a in LEGS)
    s = defs + '<g mask="url(#nobody)">%s</g>' % behind_body
    for x, y, a in LEGS:  # pink toe beans on the raised paws
        s += rot(a, x, y, ell(x, y - 37, 5.5, 4, "#f6a3b4") + circ(x - 4, y - 44, 1.8, "#f6a3b4") + circ(x + 4, y - 44, 1.8, "#f6a3b4"))
    s += '<g mask="url(#nohead)">%s%s%s</g>' % (
        path("M 104 150 Q 108 128 142 126 Q 176 128 180 150 Q 172 166 142 166 Q 112 166 104 150 Z", "#fff6ea"),
        path(BODY, "none", 8),
        "".join(path(e, "none", 7) for e in EARS)
        + path("M %d %d L %d %d L %d %d Z" % (HX - 27, HY - 23, HX - 43, HY - 19, HX - 33, HY - 9), "#f6a3b4")
        + path("M %d %d L %d %d L %d %d Z" % (HX - 26, HY + 30, HX - 43, HY + 38, HX - 25, HY + 39), "#f6a3b4"))
    s += circ(HX, HY, HR, "none", 8)
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
    if k == 1: return '<rect x="9" y="5" width="14" height="22" rx="3" fill="#ffffff" stroke="%s" stroke-width="2.5"/>' % INK
    if k == 2: return circ(16, 16, 9, "#ffffff", 2.5)
    pts = []
    for i in range(10):
        r = 13 if i % 2 == 0 else 6
        a = -math.pi / 2 + i * math.pi / 5
        pts.append("%.1f %.1f" % (16 + r * math.cos(a), 16 + r * math.sin(a)))
    return path("M " + " L ".join(pts) + " Z", "#ffffff", 2.5)

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
    out.update(render({"colosseum": colosseum()}, 512, 256, work))
    out.update(render({"dr_flop_fur": flop_svg("fur"), "dr_flop_line": flop_svg("line"), "dr_xeyes": flop_svg("xeyes")}, 256, 256, work))
    out.update(render({"dr_ghost": ghost_svg(), "dr_pop": pop_svg()}, 128, 128, work))
    out.update(render({"dr_conf%d" % k: confetti_svg(k) for k in (1, 2, 3)}, 32, 32, work))
    for name, im in out.items():
        write_tga(im, os.path.join(OUT, name + ".tga"))
    if len(sys.argv) > 2:
        # preview: the arena with a tinted flopped cat, the ghost, a pop and confetti
        bg = out["colosseum"].resize((1024, 512), Image.LANCZOS)
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
