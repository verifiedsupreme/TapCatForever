"""Casino art (UI_Casino.lua): slot symbols, the cat slot machine and its lever, playing cards
(face, back, suits, the cat court cards), the blackjack table, the slots room, lights and sparkles.
Flat sticker / kawaii style with thick dark outlines like the cat (INK). Drawn as SVG, rendered by
tools/render_svg.js (headless Chromium) and written as .tga by PIL.
usage: python3 tools/make_casino_art.py [work_dir] -> Art/casino/<name>.tga
"""
import math, os, shutil, subprocess, sys, tempfile
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_art import write_tga

INK = "#3b2620"
FUR, CREAM, PINK, RED, RED2 = "#f5a04a", "#fff1d6", "#ff9fb2", "#e8505b", "#ff7d87"
GOLD, GOLD2, TEAL, PURPLE, GREEN = "#ffcf3f", "#e0a21b", "#4cc3c9", "#8e6bd8", "#2f9e6b"


def P(d, fill, w=6, op=1, extra=""):
    return '<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round" opacity="%s" %s/>' % (d, fill, INK, w, op, extra)


def L(d, col=INK, w=4, op=1):
    return '<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round" opacity="%s"/>' % (d, col, w, op)


def C(x, y, r, fill, w=6, op=1):
    return '<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="%s" opacity="%s"/>' % (x, y, r, fill, INK if w else "none", w, op)


def E(x, y, rx, ry, fill, w=6, op=1, rot=0):
    return '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" stroke="%s" stroke-width="%s" opacity="%s" transform="rotate(%s %s %s)"/>' % (
        x, y, rx, ry, fill, INK if w else "none", w, op, rot, x, y)


def R(x, y, w, h, rx, fill, sw=6, op=1, stroke=INK):
    return '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" stroke="%s" stroke-width="%s" opacity="%s"/>' % (x, y, w, h, rx, fill, stroke, sw, op)


def shine(x, y, rx, ry, rot=-30, op=.75):
    return E(x, y, rx, ry, "#ffffff", 0, op, rot)


def star(n, r1, r2, cx, cy, rot=-90):
    pts = []
    for k in range(n * 2):
        a = math.radians(rot + k * 180 / n); r = r1 if k % 2 == 0 else r2
        pts.append("%.1f %.1f" % (cx + math.cos(a) * r, cy + math.sin(a) * r))
    return "M " + " L ".join(pts) + " Z"


def paw_print(cx, cy, s, fill, pad=None, w=5):
    """a paw print (main pad and four toes), s = scale (1 = about 60 px wide)"""
    out = P("M %s %s Q %s %s %s %s Q %s %s %s %s Q %s %s %s %s Z" % (
        cx - 20 * s, cy + 12 * s, cx - 22 * s, cy - 8 * s, cx, cy - 8 * s, cx + 22 * s, cy - 8 * s, cx + 20 * s, cy + 12 * s,
        cx, cy + 26 * s, cx - 20 * s, cy + 12 * s), fill, w)
    for dx, dy, r in ((-24, -20, 8.5), (-9, -32, 9), (9, -32, 9), (24, -20, 8.5)):
        out += E(cx + dx * s, cy + dy * s, r * s, r * 1.2 * s, fill, w)
    if pad:
        out += E(cx, cy + 8 * s, 11 * s, 8 * s, pad, 0)
        for dx, dy, r in ((-24, -20, 4), (-9, -32, 4.5), (9, -32, 4.5), (24, -20, 4)):
            out += E(cx + dx * s, cy + dy * s, r * s, r * 1.2 * s, pad, 0)
    return out


def cat_face(cx, cy, s, fur=FUR, inner=PINK, eyes="open", hat=""):
    """kawaii cat head; s = 1 is about 100 px wide"""
    o = ""
    o += P("M %s %s L %s %s L %s %s Z" % (cx - 42 * s, cy - 8 * s, cx - 36 * s, cy - 50 * s, cx - 8 * s, cy - 30 * s), fur, 6 * s)
    o += P("M %s %s L %s %s L %s %s Z" % (cx + 42 * s, cy - 8 * s, cx + 36 * s, cy - 50 * s, cx + 8 * s, cy - 30 * s), fur, 6 * s)
    o += P("M %s %s L %s %s L %s %s Z" % (cx - 34 * s, cy - 16 * s, cx - 32 * s, cy - 40 * s, cx - 17 * s, cy - 29 * s), inner, 0)
    o += P("M %s %s L %s %s L %s %s Z" % (cx + 34 * s, cy - 16 * s, cx + 32 * s, cy - 40 * s, cx + 17 * s, cy - 29 * s), inner, 0)
    o += E(cx, cy, 46 * s, 36 * s, fur, 6 * s)
    o += E(cx, cy + 14 * s, 20 * s, 13 * s, CREAM, 0)
    if eyes == "open":
        for sx in (-1, 1):
            o += E(cx + sx * 18 * s, cy - 4 * s, 6.5 * s, 8.5 * s, INK, 0)
            o += C(cx + sx * 18 * s + 2.5 * s, cy - 7.5 * s, 2.6 * s, "#ffffff", 0)
    else:  # happy closed eyes
        for sx in (-1, 1):
            o += L("M %s %s Q %s %s %s %s" % (cx + sx * 18 * s - 8 * s, cy - 2 * s, cx + sx * 18 * s, cy - 13 * s, cx + sx * 18 * s + 8 * s, cy - 2 * s), INK, 4.5 * s)
    o += E(cx - 31 * s, cy + 9 * s, 7 * s, 4.5 * s, PINK, 0, .85)
    o += E(cx + 31 * s, cy + 9 * s, 7 * s, 4.5 * s, PINK, 0, .85)
    o += P("M %s %s L %s %s L %s %s Z" % (cx - 4.5 * s, cy + 6 * s, cx + 4.5 * s, cy + 6 * s, cx, cy + 11 * s), "#ff6f8e", 2.5 * s)
    o += L("M %s %s Q %s %s %s %s Q %s %s %s %s" % (cx - 9 * s, cy + 14 * s, cx - 4.5 * s, cy + 19 * s, cx, cy + 13 * s,
                                                  cx + 4.5 * s, cy + 19 * s, cx + 9 * s, cy + 14 * s), INK, 3 * s)
    for sx in (-1, 1):
        for dy in (-2, 5):
            o += L("M %s %s L %s %s" % (cx + sx * 40 * s, cy + (8 + dy) * s, cx + sx * 56 * s, cy + (6 + dy * 1.6) * s), INK, 2.5 * s)
    return o + hat


# ---------------------------------------------------------------- slot symbols (128)
def sym_cat():
    return cat_face(64, 74, 1.0)


def sym_gem():
    o = P("M 24 50 L 42 26 L 86 26 L 104 50 L 64 108 Z", "#5fd9f0")
    o += P("M 24 50 L 104 50", "none", 5) + P("M 42 26 L 52 50 L 64 26 L 76 50 L 86 26", "none", 4)
    o += P("M 52 50 L 64 108 L 76 50", "none", 4)
    o += P("M 30 50 L 44 30 L 50 50 Z", "#b9f4ff", 0) + P("M 54 54 L 62 96 L 58 54 Z", "#b9f4ff", 0, .9)
    o += P(star(4, 10, 3, 98, 22), "#ffffff", 2.5)
    return o


def sym_bell():
    o = P("M 64 20 C 36 20 32 46 32 66 C 32 80 24 86 20 92 L 108 92 C 104 86 96 80 96 66 C 96 46 92 20 64 20 Z", GOLD)
    o += C(64, 100, 9, GOLD2, 5)
    o += P("M 20 92 L 108 92", "none", 6)
    o += P("M 44 32 C 40 42 40 56 40 70", "none", 0) + L("M 44 34 C 40 44 39 56 40 68", "#fff6c0", 6, .9)
    o += P("M 50 14 Q 64 26 78 14 Q 74 30 64 24 Q 54 30 50 14 Z", RED, 4)
    o += C(64, 18, 6, RED2, 4)
    return o


def sym_coin():
    o = C(64, 64, 46, GOLD)
    o += C(64, 64, 35, "#ffdb6b", 4)
    o += paw_print(64, 66, 0.58, GOLD2, None, 0)
    o += shine(42, 40, 11, 6)
    return o


def sym_fish():
    o = P("M 98 64 L 120 42 L 116 64 L 120 86 Z", "#3d8fe0")
    o += P("M 12 64 C 26 34 74 30 100 64 C 74 98 26 94 12 64 Z", "#5aaef7")
    o += P("M 50 38 Q 62 24 76 40", "#3d8fe0", 5)
    o += L("M 60 46 Q 66 64 60 82", INK, 4) + L("M 72 48 Q 78 64 72 80", INK, 4)
    o += C(32, 58, 7, "#ffffff", 4) + C(33, 59, 3.5, INK, 0)
    o += L("M 16 68 Q 22 72 28 70", INK, 3.5)
    o += shine(44, 48, 8, 4, -20, .6)
    return o


def sym_yarn():
    o = L("M 100 96 Q 116 104 108 118 Q 102 126 116 124", INK, 9) + L("M 100 96 Q 116 104 108 118 Q 102 126 116 124", "#ff7fb0", 5)
    o += C(62, 62, 44, "#ff8fbf")
    for d in ("M 26 46 Q 62 30 98 56", "M 22 66 Q 62 46 104 72", "M 30 90 Q 62 66 98 86", "M 46 22 Q 34 62 58 104",
              "M 70 20 Q 92 58 80 104"):
        o += L(d, "#e0609a", 4.5)
    o += shine(44, 38, 10, 6, -35, .7)
    o += L("M 20 104 L 44 86", "#c9ced8", 5) + C(18, 106, 4, "#c9ced8", 3)  # a knitting needle
    return o


def sym_paw():
    return paw_print(64, 72, 1.2, FUR, PINK, 6)


SYMBOLS = {"sym_cat": sym_cat, "sym_gem": sym_gem, "sym_bell": sym_bell, "sym_coin": sym_coin,
           "sym_fish": sym_fish, "sym_yarn": sym_yarn, "sym_paw": sym_paw}


# ---------------------------------------------------------------- slot machine (viewBox 420, rendered 512)
# The reel window is x 60-360, y 118-334 in the 420 box (UI_Casino.lua MACHINE_* use the same numbers).
def machine():
    o = ""
    o += R(26, 96, 368, 318, 34, RED, 7)                       # body
    o += R(40, 108, 340, 294, 26, RED2, 0, .55)
    o += R(48, 106, 324, 240, 20, "#ffd65a", 7)               # gold frame around the reels
    o += R(60, 118, 300, 216, 12, "#fff8ea", 7)               # reel window
    # the cat head on top (ears, face) holding the marquee
    o += P("M 92 70 L 96 8 L 156 44 Z", FUR, 7) + P("M 328 70 L 324 8 L 264 44 Z", FUR, 7)
    o += P("M 104 56 L 106 24 L 140 44 Z", PINK, 0) + P("M 316 56 L 314 24 L 280 44 Z", PINK, 0)
    o += R(78, 30, 264, 78, 38, FUR, 7)
    o += R(110, 46, 200, 46, 23, "#3b2a4a", 6)                # marquee panel (UI_Casino.lua writes on it)
    for sx in (-1, 1):
        o += E(210 + sx * 118, 74, 10, 6, PINK, 0, .9)
    # coin tray and buttons
    o += R(116, 356, 188, 40, 14, "#7a2b35", 7)
    o += R(132, 366, 156, 18, 9, "#3b1d22", 0)
    o += C(70, 376, 13, "#5ad17a", 5) + C(350, 376, 13, "#58b6ff", 5)
    o += shine(64, 370, 4, 3, -30, .8) + shine(344, 370, 4, 3, -30, .8)
    # feet
    o += R(48, 406, 54, 12, 6, "#7a2b35", 5) + R(318, 406, 54, 12, 6, "#7a2b35", 5)
    o += shine(52, 130, 5, 24, 0, .35)
    return o


def lever_ball():
    return C(32, 32, 24, RED, 5) + shine(24, 23, 7, 4, -35, .85)


def lever_rod():
    return R(10, 4, 12, 120, 6, "#c9cdd6", 4) + R(13, 8, 3, 108, 2, "#ffffff", 0, .7)


def lever_hub():
    return C(32, 32, 24, "#8a8f9c", 5) + C(32, 32, 10, "#5d616c", 4) + shine(24, 22, 6, 4, -35, .6)


# ---------------------------------------------------------------- cards (128 x 256: the card is the top 128 x 180)
def card_face():
    return R(5, 5, 118, 170, 14, "#fffaf0", 6) + R(12, 12, 104, 156, 9, "none", 2.5, .25, stroke="#c8b9a0")


def card_back():
    o = R(5, 5, 118, 170, 14, RED, 6) + R(14, 14, 100, 152, 9, RED2, 3, 1, stroke="#ffe3e6")
    for row in range(5):
        for col in range(3):
            x, y = 34 + col * 30, 32 + row * 29
            if (row, col) in ((2, 1), (1, 1), (3, 1)):
                continue
            o += paw_print(x, y, 0.16, "#ffe3e6", None, 0)
    o += C(64, 90, 25, CREAM, 5) + paw_print(64, 92, 0.42, FUR, PINK, 3)
    return o


def suit_heart():
    return P("M 32 56 C 10 40 6 30 6 22 C 6 12 14 6 22 6 C 28 6 31 10 32 14 C 33 10 36 6 42 6 C 50 6 58 12 58 22 C 58 30 54 40 32 56 Z", "#ef4a5d", 5) + shine(18, 18, 5, 3, -35, .7)


def suit_diamond():
    return P("M 32 4 L 56 32 L 32 60 L 8 32 Z", "#ef4a5d", 5) + shine(24, 24, 4, 7, 40, .6)


def suit_spade():
    return (P("M 32 4 C 26 16 6 26 6 38 C 6 46 12 50 18 50 C 24 50 28 46 30 42 L 26 58 L 38 58 L 34 42 C 36 46 40 50 46 50 C 52 50 58 46 58 38 C 58 26 38 16 32 4 Z", "#3a3550", 5)
            + shine(20, 32, 4, 2.5, -35, .5))


def suit_club():
    return (C(32, 18, 12, "#3a3550", 5) + C(18, 38, 12, "#3a3550", 5) + C(46, 38, 12, "#3a3550", 5)
            + P("M 28 40 L 24 58 L 40 58 L 36 40 Z", "#3a3550", 5) + C(32, 34, 8, "#3a3550", 0) + shine(28, 14, 3.5, 2.5, -35, .5))


def crown(cx, cy, s, fill=GOLD, gems=RED):
    o = P("M %s %s L %s %s L %s %s L %s %s L %s %s L %s %s L %s %s Z" % (
        cx - 26 * s, cy + 12 * s, cx - 30 * s, cy - 14 * s, cx - 13 * s, cy - 2 * s, cx, cy - 20 * s, cx + 13 * s, cy - 2 * s,
        cx + 30 * s, cy - 14 * s, cx + 26 * s, cy + 12 * s), fill, 5 * s)
    o += C(cx, cy + 4 * s, 4.5 * s, gems, 3 * s) + C(cx - 30 * s, cy - 15 * s, 3.5 * s, fill, 3 * s) + C(cx + 30 * s, cy - 15 * s, 3.5 * s, fill, 3 * s) + C(cx, cy - 21 * s, 3.5 * s, fill, 3 * s)
    return o


def court_k():
    return cat_face(64, 76, 0.95, FUR) + crown(64, 30, 1.0)


def court_q():
    tiara = P("M 36 36 Q 64 14 92 36 L 86 40 Q 64 26 42 40 Z", "#d9dde8", 4) + C(64, 22, 6, "#ff6fae", 3.5) + C(48, 29, 3.5, "#7ad9ff", 2.5) + C(80, 29, 3.5, "#7ad9ff", 2.5)
    return cat_face(64, 78, 0.95, "#c9c3d6", PINK) + tiara


def court_j():
    cap = (P("M 30 42 Q 34 12 64 10 Q 94 12 98 42 Q 64 30 30 42 Z", "#55b86a", 5)
           + P("M 78 14 Q 104 2 114 20 Q 98 14 88 24 Z", "#ffcf3f", 4))
    return cat_face(64, 80, 0.95, "#f7e3c0") + cap


# ---------------------------------------------------------------- rooms (1024 x 512)
def felt():
    o = R(0, 0, 1024, 512, 0, "#4a2d22", 0)
    o += R(14, 14, 996, 484, 70, "#8a5634", 8)                      # wooden rail
    o += R(28, 28, 968, 456, 58, "#a8683d", 0, .5)
    o += R(40, 40, 944, 432, 48, GREEN, 6)                          # felt
    o += R(52, 52, 920, 408, 40, "none", 3, .35, stroke="#bff0d2")
    o += L("M 150 330 Q 512 450 874 330", "#bff0d2", 4, .45)        # the betting arc
    o += L("M 190 300 Q 512 410 834 300", "#bff0d2", 2.5, .3)
    for x, y, r in ((110, 110, -20), (914, 110, 20), (110, 402, 15), (914, 402, -15)):
        o += '<g transform="rotate(%d %d %d)" opacity=".18">%s</g>' % (r, x, y, paw_print(x, y, 0.5, "#ffffff", None, 0))
    return o


def room():
    o = R(0, 0, 1024, 512, 0, "#3e2a5c", 0)
    for i in range(0, 1024, 64):
        o += R(i + 32, 0, 32, 512, 0, "#46306a", 0)
    o += R(0, 420, 1024, 92, 0, "#7a2b35", 0)                      # carpet
    for i in range(-40, 1024, 80):
        o += P("M %d 420 L %d 466 L %d 512 L %d 466 Z" % (i + 40, i + 80, i + 40, i), "#8f3842", 0)
    o += R(0, 412, 1024, 12, 0, GOLD2, 0)
    # curtain swags at the top
    o += R(0, 0, 1024, 26, 0, "#b8323f", 0)
    for i in range(0, 1024, 128):
        o += P("M %d 20 Q %d 84 %d 20 Z" % (i, i + 64, i + 128), "#d4414e", 4)
        o += C(i, 22, 8, GOLD, 4)
    for x, y, s in ((90, 150, 9), (300, 110, 6), (520, 170, 7), (700, 120, 10), (930, 180, 7), (180, 300, 6), (820, 320, 8), (430, 330, 5)):
        o += P(star(4, s * 1.6, s * 0.5, x, y), "#ffe58a", 2, .8)
    return o


# ---------------------------------------------------------------- bits
def bulb():
    return C(16, 16, 11, "#ffffff", 3) + shine(12, 11, 3.5, 2, -35, .9)


def glow():
    return ('<defs><radialGradient id="g"><stop offset="0" stop-color="#fff" stop-opacity="1"/>'
            '<stop offset=".45" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient></defs>'
            '<rect width="128" height="128" fill="url(#g)"/>')


def sparkle():
    return P(star(4, 28, 7, 32, 32), "#fff3a0", 3) + C(32, 32, 4, "#ffffff", 0)


def sign():
    o = P("M 30 40 L 38 6 L 74 28 Z", FUR, 5) + P("M 482 40 L 474 6 L 438 28 Z", FUR, 5)
    o += P("M 40 30 L 42 14 L 62 26 Z", PINK, 0) + P("M 472 30 L 470 14 L 450 26 Z", PINK, 0)
    o += R(8, 22, 496, 100, 30, RED, 6) + R(22, 34, 468, 76, 20, "#3b2a4a", 5)
    return o


def shoe():
    o = P("M 14 98 L 26 40 L 114 40 L 114 98 Z", "#8a5634", 5)
    o += P("M 30 46 L 22 92 L 108 92 L 108 46 Z", "#a8683d", 0)
    o += P("M 28 30 L 92 18 L 98 46 L 34 58 Z", RED, 4)            # the top card, face down
    o += paw_print(63, 39, 0.16, "#ffe3e6", None, 0)
    o += R(14, 96, 100, 12, 5, "#6b3f26", 4)
    return o


GROUPS = [
    # (size, height, {name: fn})
    (128, 128, dict(SYMBOLS, court_k=court_k, court_q=court_q, court_j=court_j, glow=glow, shoe=shoe)),
    (512, 512, {"machine": machine}),
    (64, 64, {"lever_ball": lever_ball, "lever_hub": lever_hub, "suit_hearts": suit_heart, "suit_diamonds": suit_diamond,
              "suit_spades": suit_spade, "suit_clubs": suit_club, "sparkle": sparkle}),
    (32, 128, {"lever_rod": lever_rod}),
    (32, 32, {"bulb": bulb}),
    (128, 256, {"card_face": card_face, "card_back": card_back}),
    (1024, 512, {"felt": felt, "room": room}),
    (512, 128, {"sign": sign}),
]
VIEWBOX = {"machine": (420, 420)}


def main():
    work = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
    out = os.path.join(os.path.dirname(HERE), "Art", "casino")
    os.makedirs(out, exist_ok=True)
    n = 0
    for gi, (w, h, items) in enumerate(GROUPS):
        d = os.path.join(work, "g%d" % gi)
        shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        for name, fn in items.items():
            vw, vh = VIEWBOX.get(name, (w, h))
            open(os.path.join(d, name + ".svg"), "w").write(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d">%s</svg>' % (vw, vh, fn()))
        subprocess.check_call(["node", os.path.join(HERE, "render_svg.js"), d, str(w), str(h)])
        for name in items:
            write_tga(Image.open(os.path.join(d, name + ".png")).convert("RGBA"), os.path.join(out, name + ".tga"))
            n += 1
    print("casino art:", n, "files in", out)


if __name__ == "__main__":
    main()
