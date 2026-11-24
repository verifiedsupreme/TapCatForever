"""Pet-effect sprites (1.6.7): full-colour little stickers that float up when you pet your cat (Purr.lua,
slot "pet"). Unlike the tap-effect shapes (make_tapfx.py, white and tinted in the game) these carry their
own colours, so their items use a white tint. Spell-school ones (fire, lightning, poison, frost, shadow,
holy, arcane, fel, blood) and cat things (yarn, fish, toy mouse, catnip, butterfly, ghost, crown, gem, moon).
usage: python3 tools/make_petfx.py [work_dir]  -> Art/v/t_<name>.tga (64x64)
"""
import math, os, subprocess, sys, tempfile
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_art import write_tga

INK = "#3b2620"

def grad(gid, stops, kind="radial", **kw):
    st = "".join('<stop offset="%s" stop-color="%s"/>' % (o, c) for o, c in stops)
    if kind == "radial":
        a = " ".join('%s="%s"' % (k, v) for k, v in (kw or {"cx": "50%", "cy": "45%", "r": "60%"}).items())
        return '<radialGradient id="%s" %s>%s</radialGradient>' % (gid, a, st)
    a = " ".join('%s="%s"' % (k, v) for k, v in (kw or {"x1": "0", "y1": "0", "x2": "0", "y2": "1"}).items())
    return '<linearGradient id="%s" %s>%s</linearGradient>' % (gid, a, st)

GLOW = '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'

def path(d, fill, w=3, extra=""):
    return '<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round" %s/>' % (d, fill, INK, w, extra)
def circ(x, y, r, fill, w=3, extra=""):
    return '<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="%s" %s/>' % (x, y, r, fill, INK, w, extra)
def star(n, r1, r2, cx=32, cy=32, rot=-90):
    pts = []
    for k in range(n * 2):
        a = math.radians(rot + k * 180 / n); r = r1 if k % 2 == 0 else r2
        pts.append("%.1f %.1f" % (cx + math.cos(a) * r, cy + math.sin(a) * r))
    return "M " + " L ".join(pts) + " Z"
def shine(x, y, rx=4, ry=2.5, rot=-30):
    return '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="#fff" opacity=".75" transform="rotate(%s %s %s)"/>' % (x, y, rx, ry, rot, x, y)

FLAME = "M 32 58 C 14 56 10 38 20 26 C 22 34 26 36 28 34 C 24 22 30 12 38 6 C 36 18 52 26 50 42 C 48 52 40 58 32 58 Z"
INNER = "M 32 54 C 23 52 21 43 26 36 C 28 41 31 41 32 38 C 31 31 34 26 38 23 C 38 30 45 35 43 44 C 42 50 37 54 32 54 Z"
DROP = "M 32 6 C 32 6 12 30 12 42 C 12 53 21 59 32 59 C 43 59 52 53 52 42 C 52 30 32 6 32 6 Z"

SPRITES = {
    # spell schools
    "fireball": grad("g", [("0", "#fff6b0"), ("0.45", "#ffb02e"), ("1", "#e2361b")], cy="70%", r="70%")
        + path(FLAME, "url(#g)") + path(INNER, "#ffe680", 0),
    "lightning": GLOW + grad("g", [("0", "#ffffff"), ("0.5", "#fff27a"), ("1", "#ffc21a")], "linear")
        + '<g filter="url(#glow)">' + path("M 38 3 L 13 36 L 29 36 L 22 61 L 52 23 L 35 23 Z", "url(#g)", 3) + '</g>'
        + '<path d="M 36 9 L 21 31" stroke="#fff" stroke-width="2.5" stroke-linecap="round" opacity=".9"/>',
    "poison": grad("g", [("0", "#e8ff8a"), ("0.5", "#7ed321"), ("1", "#2f7a10")], cx="40%", cy="40%", r="70%")
        + path(DROP, "url(#g)") + shine(24, 36, 4, 7, 20)
        + circ(41, 45, 4.5, "#c8ff6a", 2) + circ(33, 51, 2.8, "#c8ff6a", 1.8) + circ(46, 34, 2.4, "#c8ff6a", 1.6),
    "frost": grad("g", [("0", "#ffffff"), ("0.5", "#9be8ff"), ("1", "#3a9fe0")], "linear", x1="0", y1="0", x2="1", y2="1")
        + path("M 32 3 L 41 24 L 32 61 L 23 24 Z", "url(#g)") + path("M 10 22 L 26 30 L 20 46 L 6 34 Z", "url(#g)", 2.5)
        + path("M 54 22 L 58 34 L 44 46 L 38 30 Z", "url(#g)", 2.5) + '<path d="M 32 8 L 32 50" stroke="#fff" stroke-width="2" opacity=".8"/>',
    "shadow": GLOW + grad("g", [("0", "#8a5bd6"), ("0.6", "#3d2269"), ("1", "#160b29")], cy="40%")
        + path("M 32 6 C 48 6 56 20 54 34 C 52 48 44 52 46 60 C 38 56 36 60 32 54 C 28 60 26 56 18 60 C 20 52 12 48 10 34 C 8 20 16 6 32 6 Z", "url(#g)")
        + '<g filter="url(#glow)">' + '<ellipse cx="24" cy="28" rx="4.5" ry="6" fill="#e9b6ff"/><ellipse cx="40" cy="28" rx="4.5" ry="6" fill="#e9b6ff"/>' + '</g>',
    "holy": GLOW + grad("g", [("0", "#ffffff"), ("0.4", "#fff3b0"), ("1", "#f5b800")])
        + '<g filter="url(#glow)">' + path(star(8, 29, 12), "url(#g)", 2.5) + '</g>'
        + '<circle cx="32" cy="32" r="9" fill="#fffbe0" stroke="%s" stroke-width="2"/>' % INK,
    "arcane": GLOW + grad("g", [("0", "#ffd6ff"), ("0.5", "#c66bff"), ("1", "#6a2bd8")])
        + '<g filter="url(#glow)">' + circ(32, 32, 25, "none", 4.5) + '<circle cx="32" cy="32" r="25" fill="none" stroke="#d49cff" stroke-width="2.5"/>'
        + path(star(6, 20, 9), "url(#g)", 2.5) + '</g>' + circ(32, 32, 4, "#ffffff", 1.5),
    "felfire": grad("g", [("0", "#f4ffb0"), ("0.45", "#8cff2e"), ("1", "#1d8a12")], cy="70%", r="70%")
        + path(FLAME, "url(#g)") + path(INNER, "#e4ff9a", 0),
    "blood": grad("g", [("0", "#ff8a8a"), ("0.5", "#d8192b"), ("1", "#7a0712")], cx="40%", cy="40%", r="70%")
        + path(DROP, "url(#g)") + shine(25, 36, 4, 7, 20),
    # cat things
    "yarn": grad("g", [("0", "#ffd0e4"), ("1", "#f0609e")])
        + circ(30, 32, 22, "url(#g)") + '<path d="M 12 26 C 24 34 36 34 48 22 M 10 36 C 24 44 40 42 50 32 M 18 48 C 28 40 40 40 46 46 M 22 12 C 30 24 30 40 24 52" stroke="#b02a6b" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
        + '<path d="M 50 40 C 56 46 54 56 60 58" stroke="%s" stroke-width="3" fill="none" stroke-linecap="round"/>' % INK,
    "fish": grad("g", [("0", "#c6f0ff"), ("1", "#3e8fd6")], "linear")
        + path("M 6 32 C 18 14 40 14 50 32 C 40 50 18 50 6 32 Z", "url(#g)") + path("M 48 32 L 60 20 L 58 32 L 60 44 Z", "#3e8fd6", 3)
        + circ(18, 29, 3.2, INK, 0) + '<circle cx="17.2" cy="28" r="1.1" fill="#fff"/>' + '<path d="M 30 22 C 34 28 34 36 30 42" stroke="%s" stroke-width="2" fill="none"/>' % INK,
    "mouse": grad("g", [("0", "#e6e6ee"), ("1", "#8e8e9e")])
        + path("M 8 44 C 8 26 26 18 40 26 C 50 32 50 44 44 48 L 12 48 C 9 48 8 46 8 44 Z", "url(#g)")
        + circ(30, 22, 7, "#f7a8c4", 2.5) + circ(16, 36, 2.4, INK, 0) + circ(8, 43, 2.6, "#f7a8c4", 1.5)
        + '<path d="M 46 46 C 56 46 58 36 52 32" stroke="%s" stroke-width="2.6" fill="none" stroke-linecap="round"/>' % INK,
    "catnip": grad("g", [("0", "#c9f59b"), ("1", "#3f9a2a")], "linear")
        + '<path d="M 32 60 L 32 18" stroke="#3a7a20" stroke-width="3.5" stroke-linecap="round"/>'
        + path("M 32 20 C 22 4 10 10 12 22 C 16 30 28 26 32 20 Z", "url(#g)", 2.5) + path("M 32 30 C 42 14 56 20 54 32 C 50 40 38 36 32 30 Z", "url(#g)", 2.5)
        + path("M 32 44 C 22 30 8 36 10 46 C 14 54 28 50 32 44 Z", "url(#g)", 2.5) + circ(32, 14, 3, "#d58cff", 1.5),
    "butterfly": grad("g", [("0", "#ffe08a"), ("1", "#ff7a3c")]) + grad("h", [("0", "#ffd0f0"), ("1", "#e65ab8")])
        + path("M 32 30 C 22 8 4 10 8 26 C 10 34 24 34 32 30 Z", "url(#g)", 2.5) + path("M 32 30 C 42 8 60 10 56 26 C 54 34 40 34 32 30 Z", "url(#g)", 2.5)
        + path("M 32 32 C 22 40 12 56 22 56 C 30 56 32 42 32 32 Z", "url(#h)", 2.5) + path("M 32 32 C 42 40 52 56 42 56 C 34 56 32 42 32 32 Z", "url(#h)", 2.5)
        + '<rect x="30" y="18" width="4" height="30" rx="2" fill="%s"/>' % INK + circ(18, 22, 2.5, "#fff6d0", 0) + circ(46, 22, 2.5, "#fff6d0", 0),
    "ghost": grad("g", [("0", "#ffffff"), ("1", "#cfe3ff")])
        + path("M 12 56 L 12 28 C 12 14 22 6 32 6 C 42 6 52 14 52 28 L 52 56 L 45 50 L 38 56 L 32 50 L 26 56 L 19 50 Z", "url(#g)")
        + circ(24, 28, 3.5, INK, 0) + circ(40, 28, 3.5, INK, 0) + '<ellipse cx="20" cy="36" rx="3.5" ry="2" fill="#ff9fc0" opacity=".8"/><ellipse cx="44" cy="36" rx="3.5" ry="2" fill="#ff9fc0" opacity=".8"/>'
        + '<path d="M 28 37 Q 32 41 36 37" stroke="%s" stroke-width="2" fill="none" stroke-linecap="round"/>' % INK,
    "crown": grad("g", [("0", "#fff4b0"), ("0.5", "#ffcf3a"), ("1", "#d38a00")], "linear")
        + path("M 8 50 L 6 18 L 20 32 L 32 10 L 44 32 L 58 18 L 56 50 Z", "url(#g)") + path("M 8 50 L 56 50 L 56 56 L 8 56 Z", "#e6a800", 2.5)
        + circ(32, 38, 4.5, "#e8344f", 2) + circ(18, 42, 3.2, "#3aa0ff", 1.8) + circ(46, 42, 3.2, "#3ad17a", 1.8),
    "gem": grad("g", [("0", "#e6f6ff"), ("0.5", "#5fb8ff"), ("1", "#3a3fe0")], "linear", x1="0", y1="0", x2="1", y2="1")
        + path("M 16 8 L 48 8 L 60 24 L 32 60 L 4 24 Z", "url(#g)")
        + '<path d="M 4 24 L 60 24 M 16 8 L 24 24 L 32 60 L 40 24 L 48 8 M 24 24 L 32 8 L 40 24" stroke="%s" stroke-width="1.8" fill="none" stroke-linejoin="round"/>' % INK
        + shine(20, 15, 4, 2, -20),
    "moon": GLOW + grad("g", [("0", "#fffbe0"), ("1", "#ffd24a")])
        + '<g filter="url(#glow)">' + path("M 40 6 C 22 8 10 22 12 38 C 14 52 28 60 42 58 C 30 52 24 40 28 28 C 30 18 36 10 40 6 Z", "url(#g)") + '</g>'
        + path(star(4, 7, 2.5, 48, 20), "#ffffff", 1.5) + path(star(4, 5, 2, 52, 40), "#ffffff", 1.2),
}

def main():
    work = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
    os.makedirs(work, exist_ok=True)
    out = os.path.join(os.path.dirname(HERE), "Art", "v")
    os.makedirs(out, exist_ok=True)
    for name, body in SPRITES.items():
        open(os.path.join(work, name + ".svg"), "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs></defs>%s</svg>' % body)
    subprocess.check_call(["node", os.path.join(HERE, "render_svg.js"), work, "64"])
    for name in SPRITES:
        write_tga(Image.open(os.path.join(work, name + ".png")).convert("RGBA"), os.path.join(out, "t_" + name + ".tga"))
    print("pet effects:", len(SPRITES))

if __name__ == "__main__":
    main()
