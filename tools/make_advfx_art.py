"""Small cartoon sprites for Adventure fight visuals (AdventureFX.lua): shots from bows, guns,
crossbows, thrown weapons and wands, and the auras, totem and pet claws of passive abilities.
Same flat sticker style as tools/make_spellfx.py (thick dark outlines); projectiles point right.
White parts are tinted in game (wand bolts take the wand's school colour).
usage: python3 tools/make_advfx_art.py [work_dir] -> Art/advfx/<name>.tga (64x64)
"""
import math, os, subprocess, sys, tempfile
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_art import write_tga
INK = "#3b2620"


def P(d, fill, w=3, op=1, ink=INK):
    return '<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round" opacity="%s"/>' % (d, fill, ink, w, op)


def C(x, y, r, fill, w=3, op=1):
    return '<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="%s" opacity="%s"/>' % (x, y, r, fill, INK, w, op)


def glow(col, r=26, cx=32, cy=32, op=.35):
    return '<circle cx="%d" cy="%d" r="%d" fill="%s" opacity="%s" filter="url(#b)"/>' % (cx, cy, r, col, op)


def star(n, r1, r2, cx=32, cy=32, rot=-90):
    pts = []
    for k in range(n * 2):
        a = math.radians(rot + k * 180 / n); r = r1 if k % 2 == 0 else r2
        pts.append("%.1f %.1f" % (cx + math.cos(a) * r, cy + math.sin(a) * r))
    return "M " + " L ".join(pts) + " Z"


def lines(col, ys, x1=4, x2=20, w=3):
    return "".join('<path d="M %d %d L %d %d" stroke="%s" stroke-width="%d" stroke-linecap="round" opacity=".8"/>' % (x1, y, x2, y, col, w) for y in ys)


FX = {
    # a lead bullet with speed lines (guns)
    "bullet": lines("#ffe9a8", (26, 32, 38)) + P("M 26 25 L 44 25 Q 56 25 58 32 Q 56 39 44 39 L 26 39 Z", "#b9a27a")
              + P("M 30 28 L 46 28", "none", 2, .8, "#fff6d8"),
    # muzzle flash at the gun's barrel
    "muzzle": glow("#ffd24a", 24) + P(star(7, 26, 11), "#ffcf3a") + P(star(7, 13, 6, rot=-60), "#fff6c8", 2),
    # a short, thick crossbow bolt with metal vanes
    "bolt": P("M 10 28 L 46 28 L 46 36 L 10 36 Z", "#6e5038", 3.5) + P("M 46 23 L 60 32 L 46 41 Z", "#d5dde8", 3.5)
            + P("M 7 23 L 18 28 L 18 36 L 7 41 Z", "#9aa6b5", 3.5),
    # a throwing knife (spins in flight)
    "thrown": P("M 8 32 L 22 26 L 58 32 L 22 38 Z", "#dfe6ee") + P("M 22 26 L 58 32 L 26 32 Z", "#ffffff", 0, .7)
              + P("M 4 28 L 14 28 L 14 36 L 4 36 Z", "#8a5a36", 2.5),
    # a wand bolt: a small bright star with a sparkly tail (tinted by the wand's school)
    "wandbolt": glow("#ffffff", 22, 40, 32, .45) + P("M 32 24 Q 12 26 2 32 Q 12 38 32 40 Z", "#ffffff", 0, .55)
                + C(12, 30, 2.5, "#ffffff", 0, .8) + C(20, 36, 2, "#ffffff", 0, .8)
                + P(star(5, 15, 7, 40, 32), "#f4f4f4") + C(40, 32, 4.5, "#ffffff", 0),
    # a ring at the cat's feet for auras (Devotion Aura, Trueshot Aura, Frost Armor...), tinted
    "aura": '<ellipse cx="32" cy="40" rx="29" ry="13" fill="#ffffff" fill-opacity=".18" stroke="%s" stroke-width="7"/>' % INK
            + '<ellipse cx="32" cy="40" rx="29" ry="13" fill="none" stroke="#ffffff" stroke-width="4"/>'
            + "".join(P(star(4, 7, 2.5, x, y), "#ffffff", 2) for x, y in ((10, 22), (52, 18), (32, 10))),
    # Searing Totem: a little carved pole with a flame on top
    "totem": glow("#ff8a1e", 14, 32, 12, .5) + P("M 32 2 Q 42 12 36 20 Q 32 24 28 20 Q 22 12 32 2 Z", "#ff9a2a", 2.5)
             + P("M 24 20 L 40 20 L 42 60 L 22 60 Z", "#a0683c") + P("M 18 26 L 46 26 L 46 32 L 18 32 Z", "#c94a2a", 2.5)
             + C(28, 42, 2.5, INK, 0) + C(36, 42, 2.5, INK, 0) + P("M 27 50 Q 32 54 37 50", "none", 2.5),
    # three claw marks (the hunter's pet attacking), tinted
    "claw": "".join(P("M %d 8 Q %d 32 %d 58" % (x, x + 10, x - 4), "none", 7) + P("M %d 8 Q %d 32 %d 58" % (x, x + 10, x - 4), "none", 3.5, 1, "#ffffff")
                    for x in (18, 32, 46)),
    # a round orb (Lightning Shield circles the cat with these), tinted
    "orb": glow("#ffffff", 20, op=.5) + C(32, 32, 14, "#e8f4ff") + C(28, 27, 5, "#ffffff", 0)
           + P("M 24 34 L 31 30 L 30 37 L 40 31", "none", 2.5, 1, "#5a8fd8"),
    # a four-point sparkle (seal procs, casters' plain spell hits, Cat Form), tinted
    "sparkle": glow("#ffffff", 18, op=.5) + P(star(4, 26, 7), "#ffffff") + P(star(4, 12, 4, rot=-45), "#ffffff", 2),
}
DEFS = '<defs><filter id="b" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter></defs>'


def main():
    work = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
    os.makedirs(work, exist_ok=True)
    out = os.path.join(os.path.dirname(HERE), "Art", "advfx")
    os.makedirs(out, exist_ok=True)
    for name, body in FX.items():
        open(os.path.join(work, name + ".svg"), "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">%s%s</svg>' % (DEFS, body))
    subprocess.check_call(["node", os.path.join(HERE, "render_svg.js"), work, "64"])
    for name in FX:
        write_tga(Image.open(os.path.join(work, name + ".png")).convert("RGBA"), os.path.join(out, name + ".tga"))
    print("adventure fx sprites:", len(FX))


if __name__ == "__main__":
    main()
