"""Tap-effect sprites: little sticker shapes that burst from the paw on every tap.
Drawn white with a dark outline so the game can tint them any colour.
usage: python3 tools/make_tapfx.py [work_dir]  -> Art/v/t_<shape>.tga (64x64)
"""
import math, os, subprocess, sys, tempfile
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_art import write_tga

INK, F = "#3b2620", "#ffffff"
def P(d, w=3): return '<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"/>' % (d, F, INK, w)
def C(x, y, r, w=3, fill=F): return '<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % (x, y, r, fill, INK, w)
def star(n, r1, r2, cx=32, cy=32, rot=-90):
    pts = []
    for k in range(n * 2):
        a = math.radians(rot + k * 180 / n); r = r1 if k % 2 == 0 else r2
        pts.append("%.1f %.1f" % (cx + math.cos(a) * r, cy + math.sin(a) * r))
    return "M " + " L ".join(pts) + " Z"
SHAPES = {
    "puff": C(22, 36, 11) + C(40, 36, 11) + C(31, 25, 13),
    "star": P(star(5, 26, 11)),
    "heart": P("M 32 54 C 8 38 6 20 18 13 C 26 9 31 15 32 19 C 33 15 38 9 46 13 C 58 20 56 38 32 54 Z"),
    "coin": C(32, 32, 24) + C(32, 32, 16, 2.5) + P("M 32 22 L 35 29 L 42 29 L 36 34 L 38 41 L 32 37 L 26 41 L 28 34 L 22 29 L 29 29 Z", 2),
    "note": P("M 26 46 L 26 12 L 48 8 L 48 40", 4).replace('fill="#ffffff"', 'fill="none"') + C(21, 46, 8) + C(43, 41, 8),
    "sparkle": P(star(4, 27, 7, rot=-90)),
    "flame": P("M 32 58 C 14 56 10 38 20 26 C 22 34 26 36 28 34 C 24 22 30 12 38 6 C 36 18 52 26 50 42 C 48 52 40 58 32 58 Z"),
    "snow": "".join('<path d="M 32 32 L %.1f %.1f" stroke="%s" stroke-width="9" stroke-linecap="round"/><path d="M 32 32 L %.1f %.1f" stroke="%s" stroke-width="4" stroke-linecap="round"/>' % (
        32 + math.cos(math.radians(a)) * 24, 32 + math.sin(math.radians(a)) * 24, INK, 32 + math.cos(math.radians(a)) * 24, 32 + math.sin(math.radians(a)) * 24, F) for a in range(0, 360, 60)) + C(32, 32, 6, 3),
    "bolt": P("M 36 4 L 14 36 L 30 36 L 24 60 L 50 24 L 34 24 Z"),
    "bubble": C(32, 32, 22, 3, "#ffffff") + '<circle cx="32" cy="32" r="18" fill="#000" opacity=".12"/>' + C(24, 24, 5, 0),
    "leaf": P("M 10 54 C 10 24 30 8 56 8 C 56 34 40 54 10 54 Z") + '<path d="M 12 52 L 46 18" stroke="%s" stroke-width="2.5"/>' % INK,
    "paw": C(32, 40, 13) + C(16, 24, 6.5) + C(26, 15, 6.5) + C(38, 15, 6.5) + C(48, 24, 6.5),
    "skull": P("M 14 34 C 12 14 22 8 32 8 C 42 8 52 14 50 34 L 44 40 L 44 52 L 20 52 L 20 40 Z") + C(24, 30, 6, 0, INK) + C(40, 30, 6, 0, INK),
}

def main():
    work = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
    os.makedirs(work, exist_ok=True)
    out = os.path.join(os.path.dirname(HERE), "Art", "v")
    os.makedirs(out, exist_ok=True)
    for name, body in SHAPES.items():
        open(os.path.join(work, name + ".svg"), "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">%s</svg>' % body)
    subprocess.check_call(["node", os.path.join(HERE, "render_svg.js"), work, "64"])
    for name in SHAPES:
        write_tga(Image.open(os.path.join(work, name + ".png")).convert("RGBA"), os.path.join(out, "t_" + name + ".tga"))
    print("tap effects:", len(SHAPES))

if __name__ == "__main__":
    main()
