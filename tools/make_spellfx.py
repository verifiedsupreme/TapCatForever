"""Cartoon spell effects for Adventure fights (projectiles point right, toward the enemies).
usage: python3 tools/make_spellfx.py [work_dir] -> Art/v/s_<name>.tga (64x64)
"""
import math, os, subprocess, sys, tempfile
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_art import write_tga
INK = "#3b2620"
def P(d, fill, w=3, op=1): return '<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round" opacity="%s"/>' % (d, fill, INK, w, op)
def C(x, y, r, fill, w=3, op=1): return '<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="%s" opacity="%s"/>' % (x, y, r, fill, INK, w, op)
def glow(col, r=26): return '<circle cx="32" cy="32" r="%d" fill="%s" opacity=".35" filter="url(#b)"/>' % (r, col)
def star(n, r1, r2, cx=32, cy=32, rot=-90):
    pts = []
    for k in range(n * 2):
        a = math.radians(rot + k * 180 / n); r = r1 if k % 2 == 0 else r2
        pts.append("%.1f %.1f" % (cx + math.cos(a) * r, cy + math.sin(a) * r))
    return "M " + " L ".join(pts) + " Z"
def orb(core, mid, tail, trail=True):
    s = glow(mid)
    if trail: s += P("M 30 20 Q 8 24 2 32 Q 8 40 30 44 Z", tail, 0, .85)
    return s + C(36, 32, 15, mid) + C(39, 29, 7, core, 0)
FX = {
    "fire": orb("#fff3a0", "#ff8a1e", "#ff5a14"),
    "frost": glow("#9fe4ff") + P("M 4 32 L 18 26 L 58 32 L 18 38 Z", "#bdf0ff") + P("M 18 26 L 58 32 L 26 32 Z", "#ffffff", 0, .7),
    "shadow": orb("#e6b8ff", "#7a2fd0", "#3a1260"),
    "arcane": glow("#ff9cf2") + P(star(4, 20, 6, 38, 32), "#ff9cf2") + P("M 4 30 L 22 31 L 4 34 Z", "#ffd0f8", 0, .8),
    "holy": glow("#fff27a", 28) + "".join(P("M 32 32 L %.1f %.1f" % (32 + math.cos(math.radians(a)) * 28, 32 + math.sin(math.radians(a)) * 28), "none", 3)
                                          .replace('stroke="%s"' % INK, 'stroke="#ffe066"') for a in range(0, 360, 45)) + C(32, 32, 14, "#ffe066") + C(29, 29, 6, "#fffbe0", 0),
    "nature": orb("#e6ffb0", "#5cd84a", "#2f8f2a"),
    "lightning": glow("#9fd8ff") + P("M 2 30 L 22 22 L 26 32 L 46 22 L 40 34 L 62 32 L 40 42 L 36 34 L 18 44 Z", "#e9f8ff", 3),
    "arrow": P("M 4 30 L 44 30 L 44 34 L 4 34 Z", "#a2683e", 2.5) + P("M 44 24 L 60 32 L 44 40 Z", "#c9d3e0") + P("M 4 26 L 14 30 L 14 34 L 4 38 L 8 32 Z", "#e8e8e8", 2.5),
    "slash": glow("#ffffff", 22) + P("M 6 58 Q 50 50 56 4 Q 34 38 6 58 Z", "#ffffff") + P("M 14 54 Q 44 44 52 14", "none", 2).replace('stroke="%s"' % INK, 'stroke="#9fd0ff"'),
    "poison": glow("#9cff5a") + P("M 36 10 Q 52 34 46 44 Q 36 56 26 44 Q 20 34 36 10 Z", "#7be04a") + C(32, 40, 4, "#e6ffb0", 0),
    "moon": glow("#cfe0ff") + '<mask id="m"><rect width="64" height="64" fill="#fff"/><circle cx="44" cy="26" r="20" fill="#000"/></mask>'
            + '<g mask="url(#m)"><circle cx="32" cy="32" r="26" fill="#e6ecff" stroke="%s" stroke-width="3"/></g>' % INK
            + '<path d="M 25.6 11 A 20 20 0 0 0 57.5 36.3" fill="none" stroke="%s" stroke-width="3"/>' % INK,
    "rock": P("M 14 40 L 20 20 L 40 14 L 54 26 L 50 46 L 30 52 Z", "#a08060") + P("M 24 26 L 38 22 L 46 30", "none", 2.5),
    "impact": P(star(8, 28, 12), "#ffffff"),
    "heal": glow("#7cf07a") + P("M 26 10 L 38 10 L 38 26 L 54 26 L 54 38 L 38 38 L 38 54 L 26 54 L 26 38 L 10 38 L 10 26 L 26 26 Z", "#7cf07a"),
    "shield": '<circle cx="32" cy="32" r="28" fill="#9fd8ff" fill-opacity=".25" stroke="#9fd8ff" stroke-width="5"/>' + '<path d="M 16 20 Q 24 10 36 8" fill="none" stroke="#ffffff" stroke-width="4" stroke-linecap="round" opacity=".8"/>',
    "stun": "".join(P(star(5, 10, 4, 32 + math.cos(math.radians(a)) * 18, 32 + math.sin(math.radians(a)) * 8), "#ffe066", 2.5) for a in (90, 210, 330)),
    "buff": P("M 12 40 L 32 22 L 52 40 L 52 50 L 32 32 L 12 50 Z", "#ffb02e") + P("M 12 22 L 32 4 L 52 22 L 52 32 L 32 14 L 12 32 Z", "#ffd24a"),
}
DEFS = '<defs><filter id="b" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter></defs>'

def main():
    work = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
    os.makedirs(work, exist_ok=True)
    out = os.path.join(os.path.dirname(HERE), "Art", "v")
    os.makedirs(out, exist_ok=True)
    for name, body in FX.items():
        open(os.path.join(work, name + ".svg"), "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">%s%s</svg>' % (DEFS, body))
    subprocess.check_call(["node", os.path.join(HERE, "render_svg.js"), work, "64"])
    for name in FX:
        write_tga(Image.open(os.path.join(work, name + ".png")).convert("RGBA"), os.path.join(out, "s_" + name + ".tga"))
    print("spell effects:", len(FX))

if __name__ == "__main__":
    main()
