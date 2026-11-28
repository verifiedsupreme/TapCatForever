"""The made-up Legendary items (1.7.7, CustomGear.lua): their own drawings on the cat and their own icons.

Each item is drawn here by hand in the same sticker style as every other item (tools/vector_items.py's
helpers: ink outline, cel shading, glows), in the same 256x256 cat canvas (weapons in the right paw,
chest pieces on the body). Writes:
  Art/v/i_tcf_<key>.tga    the drawing on the cat (cropped, power-of-two padded, like build_vector_art.py)
  Art/v/ic_tcf_<key>.tga   a 64x64 icon made from the drawing (legendary frame)
  Art/v/a_tcf_*.tga        their own effect sprites (paw prints, coffee beans, music notes, feathers...)
  CustomGearArt.lua        TCF.VEC entries "tcf:<key>" for the drawings
and, with --poster <file>, a promo picture of all five.

usage: python3 tools/make_custom_legendaries.py [--poster out.png] [--fonts dir]
"""
import math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import vector_items as V
from vector_items import P, LN, CI, EL, RC, GEM, GLOW, INK, light, darker, mirror, RIGHT_HAND, BODY_OUT
from make_art import write_tga

OUT = os.path.join(ROOT, "Art", "v")

# ------------------------------------------------------------------ Caffeinated's bow: a double espresso
def bow_espresso():
    roast, cream, cup, coffee = "#4a2c1c", "#f3e2c4", "#fbf7ef", "#6b3e22"
    p0, p1, p2 = (4, -162), (44, -76), (4, 10)
    def at(u): return tuple((1 - u) ** 2 * p0[k] + 2 * (1 - u) * u * p1[k] + u * u * p2[k] for k in (0, 1))
    limb = "M %d %d Q %d %d %d %d" % (p0 + p1 + p2)
    s = LN("M %d %d L %d %d" % (p0 + p2), "#f4f0e0", 1.8)
    s += LN(limb, INK, 13) + LN(limb, roast, 8)
    # cream swirls wrapped round the limb, like milk poured in
    for u in (0.1, 0.2, 0.3, 0.7, 0.8, 0.9):
        x, y = at(u)
        s += '<path d="M %.1f %.1f q 6 -3 9 3" fill="none" stroke="%s" stroke-width="3" stroke-linecap="round"/>' % (x - 5, y, cream)
    # coffee-bean tips
    for (x, y), rot in ((p0, -30), (p2, 30)):
        s += EL(x + 3, y, 9, 6, roast, 3.5, rot) + LN("M %.1f %.1f q 3 1 6 0" % (x, y - 1, ), cream, 2)
    # the grip: a little espresso cup with its handle, coffee inside, a heart in the crema
    gx, gy = at(0.5)
    s += RC(gx - 9, gy - 10, 22, 22, cup, 5, 3.5)
    s += '<path d="M %.1f %.1f q 11 2 0 14" fill="none" stroke="%s" stroke-width="7"/>' % (gx + 13, gy - 6, INK)
    s += '<path d="M %.1f %.1f q 11 2 0 14" fill="none" stroke="%s" stroke-width="3.5"/>' % (gx + 13, gy - 6, cup)
    s += EL(gx + 2, gy - 10, 11, 4, coffee, 3)
    s += P("M %.1f %.1f q -3 -3 0 -4 q 3 1 0 4 q -3 -3 0 -4" % (gx + 2, gy - 9), cream, 1.2)
    s += RC(gx - 11, gy + 12, 26, 5, cup, 2, 3)
    # steam curling up from the cup (it glows warm)
    steam = ""
    for dx, k in ((-4, 0), (4, 1), (11, 0)):
        x = gx + dx
        steam += LN("M %.1f %.1f q -7 -9 0 -17 q 7 -8 0 -17" % (x, gy - 14 - k * 4), "#ffffff", 3.5, 0.85)
    s += GLOW(steam, "#ffb46a") + steam
    # two coffee beans on the string's knot
    s += EL(-2, -78, 5, 3.5, roast, 2.5, 60) + EL(-2, -66, 5, 3.5, roast, 2.5, -60)
    return '<g %s>%s</g>' % (RIGHT_HAND, s)

# ------------------------------------------------------------------ Battledancer's Hammer of Justice
def hammer_justice():
    gold, deep, white, blue, pink = "#f6c64a", "#c88a1e", "#fff8e8", "#5aa6ff", "#ff7ab8"
    L = 118   # a little shorter than other two-handers, so the wings stay on the canvas
    # the haft: white wrapped in a blue spiral ribbon, a gold pommel
    s = RC(-5, -L, 10, L + 30, white, 4)
    for k in range(7):
        y = -L + 16 + k * 20
        s += LN("M -5 %d L 5 %d" % (y, y + 10), blue, 3.5)
    s += CI(0, 26, 8, gold) + GEM(0, 26, 3.5, blue)
    # dancer's ribbons trailing from under the head
    rib = P("M -4 %d q -26 18 -18 52 q 8 20 -6 40 l 6 2 q 14 -20 6 -40 q -8 -30 16 -50 Z" % (-L + 6), pink, 3)
    rib += P("M 4 %d q 30 22 18 54 q -8 20 6 38 l -6 3 q -14 -20 -6 -40 q 8 -30 -18 -52 Z" % (-L + 6), blue, 3)
    # wings flaring from the head
    wing = ""
    for k, (len_, ang) in enumerate(((40, -48), (34, -30), (26, -12))):   # swept up and back
        wing += '<g transform="rotate(%d 26 %d)">%s</g>' % (ang, -L - 30, EL(26 + len_ / 2.0, -L - 30, len_ / 2.0, 8 - k, white, 3.5))
    head = mirror(wing) + wing
    # the head: a big rounded gold block with dark bands, a radiant sun gem in the middle
    head += RC(-34, -L - 52, 68, 50, gold, 10, 4.5)
    head += RC(-38, -L - 52, 10, 50, deep, 4, 3.5) + RC(28, -L - 52, 10, 50, deep, 4, 3.5)
    sun = ""
    for k in range(12):
        a = k * math.pi / 6
        x1, y1 = math.cos(a) * 12, math.sin(a) * 12 - L - 27
        x2, y2 = math.cos(a) * (19 if k % 2 else 23), math.sin(a) * (19 if k % 2 else 23) - L - 27
        sun += LN("M %.1f %.1f L %.1f %.1f" % (x1, y1, x2, y2), "#fff27a", 3)
    head += sun + CI(0, -L - 27, 11, "#fff6c0", 3.5) + GEM(0, -L - 27, 7, "#ffcf3a")
    head += RC(-10, -L - 4, 20, 10, deep, 3, 3)
    # held a little more upright than other weapons (turned round the grip), so the right wing stays on the canvas
    return '<g %s><g transform="rotate(-12)">%s%s%s</g></g>' % (RIGHT_HAND, rib, GLOW(head, "#fff27a"), s + head)

# ------------------------------------------------------------------ Ziggu's Wand of Endless Taps
def wand_ziggu():
    orange, cream, crys, crys2 = "#ef8a35", "#fff3dc", "#c07cff", "#ff8ce0"
    # tabby-striped rod and a paw-print pommel
    s = RC(-5, -84, 10, 100, orange, 4)
    for y in (-74, -60, -46, -32, -18, -4):
        s += LN("M -5 %d L 5 %d" % (y, y - 5), "#9a4a1c", 3)
    s += CI(0, 20, 9, cream) + CI(0, 22, 3.8, "#f08cc0", 0)
    for dx, dy in ((-4.5, 15.5), (0, 13.5), (4.5, 15.5)): s += CI(dx, dy, 1.8, "#f08cc0", 0)
    s += RC(-8, -88, 16, 8, "#f2c14e", 3, 3)
    # the crystal cat head: ears, a glowing face, two sparkling eyes
    hy = -108
    head = P("M -20 %d L -22 %d L -9 %d Z" % (hy - 6, hy - 30, hy - 16), crys, 3.5) + P("M 20 %d L 22 %d L 9 %d Z" % (hy - 6, hy - 30, hy - 16), crys, 3.5)
    head += P("M -21 %d Q -24 %d 0 %d Q 24 %d 21 %d Q 18 %d 0 %d Q -18 %d -21 %d Z" % (hy - 8, hy + 14, hy + 20, hy + 14, hy - 8, hy - 22, hy - 22, hy - 22, hy - 8), crys)
    head += P("M -14 %d Q 0 %d 14 %d" % (hy + 2, hy - 14, hy + 2), "none", 0) + LN("M -12 %d L -4 %d L -12 %d" % (hy - 12, hy - 4, hy + 4), crys2, 2.5)
    head += GEM(-8, hy - 2, 4.5, "#fff27a") + GEM(8, hy - 2, 4.5, "#fff27a")
    head += P("M -3 %d L 3 %d L 0 %d Z" % (hy + 6, hy + 6, hy + 10), crys2, 1.5)
    head += LN("M 0 %d q -5 5 -9 2 M 0 %d q 5 5 9 2" % (hy + 10, hy + 10), INK, 2)
    for side in (-1, 1):
        head += LN("M %d %d L %d %d M %d %d L %d %d" % (side * 12, hy + 6, side * 30, hy + 3, side * 12, hy + 9, side * 30, hy + 12), "#ffffff", 1.6)
    # sparkles orbiting the head
    spark = ""
    for x, y, r in ((-30, hy - 26, 6), (28, hy - 34, 5), (32, hy + 10, 4), (-30, hy + 14, 4)):
        spark += P("M %d %d L %.1f %.1f L %d %d L %.1f %.1f Z" % (x, y - r * 1.6, x + r * 0.4, y - r * 0.4, x + r * 1.6, y, x + r * 0.4, y + r * 0.4), "#fff6a0", 2) + \
                 P("M %d %d L %.1f %.1f L %d %d L %.1f %.1f Z" % (x, y + r * 1.6, x - r * 0.4, y + r * 0.4, x - r * 1.6, y, x - r * 0.4, y - r * 0.4), "#fff6a0", 2)
    return '<g %s>%s%s%s%s</g>' % (RIGHT_HAND, GLOW(head, "#ff7ae0"), s, head, GLOW(spark, "#fff27a") + spark)

# ------------------------------------------------------------------ N8 Dawg's Alpha Pack Harness (druid chest)
def chest_n8():
    hide, strap, gold, fur, green = "#7a4a2a", "#2e1e16", "#f2c14e", "#d9d4cc", "#4fae4a"
    s = P(BODY_OUT, hide, 5)
    # leaf trim along the hem, for the druid
    for k, x in enumerate(range(68, 196, 16)):
        s += '<g clip-path="url(#chestclip)">%s</g>' % EL(x, 210, 9, 5, green if k % 2 else "#2f7a3a", 2.5, 25 if k % 2 else -25)
    # crossed harness straps with gold studs
    for d in ("M 78 122 L 182 206", "M 178 122 L 74 206"):
        s += '<g clip-path="url(#chestclip)">%s%s</g>' % (LN(d, INK, 16), LN(d, strap, 11))
    for t in (0.18, 0.36, 0.64, 0.82):
        for (x0, y0, x1, y1) in ((78, 122, 182, 206), (178, 122, 74, 206)):
            s += CI(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 3.2, gold, 2)
    # the wolf emblem: a grey dog's head with glowing green eyes, on a gold ring
    cx, cy = 128, 164
    s += CI(cx, cy, 23, gold, 4.5)
    dog = P("M %d %d L %d %d L %d %d Z" % (cx - 15, cy - 6, cx - 13, cy - 24, cx - 4, cy - 12), "#8e8a86", 3)
    dog += P("M %d %d L %d %d L %d %d Z" % (cx + 15, cy - 6, cx + 13, cy - 24, cx + 4, cy - 12), "#8e8a86", 3)
    dog += P("M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx - 16, cy - 6, cx - 16, cy + 8, cx, cy + 18, cx + 16, cy + 8, cx + 16, cy - 6, cx, cy - 16, cx - 16, cy - 6), "#a8a4a0", 3)
    dog += EL(cx, cy + 9, 7, 6, "#e9e4dc", 2.5) + EL(cx, cy + 5, 3.5, 2.5, INK, 0)
    eyes = CI(cx - 7, cy - 2, 3.2, "#9bff5a", 2) + CI(cx + 7, cy - 2, 3.2, "#9bff5a", 2)
    s += dog + GLOW(eyes, "#7cf07a") + eyes
    # paw-print studs on each side
    for px in (88, 168):
        s += CI(px, 196, 5, gold, 2) + "".join(CI(px + dx, 188 + dy, 2.2, gold, 1.5) for dx, dy in ((-5, 0), (0, -3), (5, 0)))
    # the fur collar
    s += P("M 70 124 Q 128 150 186 124 Q 192 106 176 104 Q 128 128 80 104 Q 64 106 70 124 Z", fur, 4)
    for x in range(82, 178, 12):
        s += LN("M %d %d l 3 6" % (x, 122 + abs(x - 128) // 8), darker(fur, .75), 2)
    return GLOW(P(BODY_OUT, "#000"), "#5ad65a") + s

# ------------------------------------------------------------------ Shua's Vestments of the Dawn (priest robe)
def robe_shua():
    white, gold, sky, gem = "#fbf8f0", "#f2c14e", "#8fd2ff", "#2f6ff0"
    s = P(BODY_OUT, white, 5)
    # star embroidery
    for x, y in ((80, 150), (176, 150), (74, 186), (182, 186), (96, 206), (160, 206)):
        s += '<g clip-path="url(#chestclip)">%s</g>' % P("M %d %d l 2 5 l 5 1 l -4 3 l 1 5 l -4 -3 l -4 3 l 1 -5 l -4 -3 l 5 -1 Z" % (x, y - 7), gold, 1.2)
    # gold front panel and hem
    s += '<g clip-path="url(#chestclip)">%s%s</g>' % (RC(116, 120, 24, 100, gold, 3, 3), RC(50, 204, 160, 12, gold, 2, 3))
    # the sunburst on the chest, a sapphire in its heart
    cx, cy = 128, 160
    rays = ""
    for k in range(16):
        a = k * math.pi / 8
        r1, r2 = 15, (34 if k % 2 == 0 else 26)
        rays += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (cx + math.cos(a - 0.12) * r1, cy + math.sin(a - 0.12) * r1,
                   cx + math.cos(a) * r2, cy + math.sin(a) * r2, cx + math.cos(a + 0.12) * r1, cy + math.sin(a + 0.12) * r1), "#ffe27a", 2)
    sun = rays + CI(cx, cy, 15, gold, 3.5) + GEM(cx, cy, 8, gem)
    # the sky-blue sash under the sunburst, and the gold collar
    s += P("M 70 130 L 84 124 L 194 196 L 186 210 Z", sky, 3.5)
    s += GLOW(sun, "#fff27a") + sun
    s += P("M 100 120 L 128 146 L 156 120 L 146 116 L 128 134 L 110 116 Z", gold, 3)
    return GLOW(P(BODY_OUT, "#000"), "#fff6b0") + s

# ------------------------------------------------------------------ Iverson's Headband (1.7.9): a pink mullet under a sweatband
def headband_iverson():
    from vector_items import HEAD_TF
    pink, light_, deep, band, red, blue = "#ff6fb5", "#ffb8dc", "#d8478f", "#fbfbf6", "#e0283c", "#2f6ff0"
    s = ""
    # the mullet: long pink locks spilling down both sides, past the cheeks onto the shoulders
    lock = "M 50 84 Q 24 112 30 150 Q 34 176 22 204 Q 40 200 46 186 Q 50 206 40 226 Q 62 214 64 190 Q 70 160 62 120 Z"
    s += P(lock, pink, 5) + mirror(P(lock, pink, 5), 128)
    for d in ("M 40 120 Q 36 160 30 196", "M 52 130 Q 50 170 48 210"):
        s += LN(d, deep, 3) + mirror(LN(d, deep, 3), 128)
    s += LN("M 46 104 Q 40 140 38 170", light_, 3) + mirror(LN("M 46 104 Q 40 140 38 170", light_, 3), 128)
    # big fluffy hair on top, a fringe of points over the band
    top = ("M 42 96 Q 30 40 76 22 Q 100 6 128 12 Q 160 4 186 24 Q 226 42 214 96 "
           "L 200 104 L 190 92 L 176 104 L 164 92 L 150 104 L 138 92 L 128 104 L 118 92 L 106 104 L 94 92 L 80 104 L 68 92 L 56 104 Z")
    s += P(top, pink, 5)
    for d in ("M 70 40 Q 84 30 98 32", "M 120 24 Q 136 18 150 24", "M 168 36 Q 182 42 190 56"):
        s += LN(d, light_, 4)
    s += LN("M 96 60 Q 128 46 160 60", deep, 3)
    # the sweatband: white, with a red and a blue stripe, a little logo in the middle
    s += P("M 40 78 Q 128 58 216 78 L 216 98 Q 128 78 40 98 Z", band, 4.5)
    s += LN("M 42 84 Q 128 64 214 84", red, 3) + LN("M 42 92 Q 128 72 214 92", blue, 3)
    s += RC(118, 68, 20, 14, band, 3, 3) + LN("M 122 75 L 134 75", red, 3)
    return "<g %s>%s</g>" % (HEAD_TF, s)

# ------------------------------------------------------------------ their own effect sprites (new, used by nothing else)
# White shapes are tinted by the effect's colour; the coffee bean keeps its own colours.
W = "#ffffff"
def _sv(body, vb=64): return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d">%s</svg>' % (vb, vb, body)
SPRITES = {
    # a paw print (N8 Dawg)
    "a_tcf_paw": _sv('<ellipse cx="32" cy="40" rx="13" ry="11" fill="%s"/>' % W + "".join(
        '<ellipse cx="%d" cy="%d" rx="5.5" ry="7" fill="%s"/>' % (x, y, W) for x, y in ((16, 24), (26, 15), (38, 15), (48, 24)))),
    # a druid leaf with its vein
    "a_tcf_leaf": _sv('<path d="M 32 6 Q 54 26 32 58 Q 10 26 32 6 Z" fill="%s"/><path d="M 32 12 L 32 54" stroke="#bbbbbb" stroke-width="2.5"/>' % W),
    # a coffee bean, in its own colours (Caffeinated)
    "a_tcf_bean": _sv('<ellipse cx="32" cy="32" rx="16" ry="22" fill="#5a3420" stroke="#2a1a10" stroke-width="3" transform="rotate(25 32 32)"/>'
                      '<path d="M 26 14 Q 38 32 28 50" fill="none" stroke="#e8c9a0" stroke-width="3.5" transform="rotate(25 32 32)"/>'),
    # a curl of steam
    "a_tcf_steam": _sv('<path d="M 32 60 Q 14 46 32 32 Q 50 18 32 4" fill="none" stroke="%s" stroke-width="7" stroke-linecap="round"/>' % W),
    # a music note (Battledancer)
    "a_tcf_note": _sv('<ellipse cx="22" cy="48" rx="10" ry="8" fill="%s" transform="rotate(-20 22 48)"/><rect x="29" y="10" width="5" height="40" fill="%s"/>'
                      '<path d="M 31 10 Q 50 14 50 30 Q 44 20 33 22 Z" fill="%s"/>' % (W, W, W)),
    # a holy rune: a cross in a ring, with four little rays
    "a_tcf_rune": _sv('<circle cx="32" cy="32" r="20" fill="none" stroke="%s" stroke-width="4"/><rect x="29" y="14" width="6" height="36" fill="%s"/>'
                      '<rect x="18" y="26" width="28" height="6" fill="%s"/>' % (W, W, W) + "".join(
                      '<rect x="30" y="0" width="4" height="9" fill="%s" transform="rotate(%d 32 32)"/>' % (W, a) for a in (45, 135, 225, 315))),
    # a feather (Shua)
    "a_tcf_feather": _sv('<path d="M 46 6 Q 58 30 22 56 Q 14 40 46 6 Z" fill="%s"/><path d="M 44 10 L 16 60" stroke="#cccccc" stroke-width="2.5"/>' % W
                         + "".join('<path d="M %d %d l 9 3" stroke="#cccccc" stroke-width="1.5"/>' % (36 - k * 5, 22 + k * 7) for k in range(4))),
    # a sun-ray halo, drawn big behind the robe
    "a_tcf_halo": _sv('<circle cx="64" cy="64" r="30" fill="none" stroke="%s" stroke-width="6" opacity=".9"/>' % W + "".join(
                      '<path d="M 62 4 L 64 26 L 66 4 Z" fill="%s" transform="rotate(%d 64 64)"/>' % (W, a) for a in range(0, 360, 20)), 128),
    # a tiny cat head (Ziggu)
    "a_tcf_cat": _sv('<path d="M 12 30 L 10 6 L 26 18 Q 32 16 38 18 L 54 6 L 52 30 Q 56 54 32 58 Q 8 54 12 30 Z" fill="%s"/>'
                     '<circle cx="24" cy="34" r="4" fill="#cccccc"/><circle cx="40" cy="34" r="4" fill="#cccccc"/>' % W),
    # a heart (Iverson)
    "a_tcf_heart": _sv('<path d="M 32 56 Q 6 38 8 22 Q 10 8 22 8 Q 30 8 32 18 Q 34 8 42 8 Q 54 8 56 22 Q 58 38 32 56 Z" fill="%s"/>' % W),
    # a little basketball, in its own colours
    "a_tcf_ball": _sv('<circle cx="32" cy="32" r="24" fill="#f08a2c" stroke="#3b2620" stroke-width="3.5"/>'
                      '<path d="M 8 32 L 56 32 M 32 8 L 32 56 M 15 15 Q 26 32 15 49 M 49 15 Q 38 32 49 49" fill="none" stroke="#3b2620" stroke-width="2.5"/>'),
    # a four-point tap star
    "a_tcf_star": _sv('<path d="M 32 2 Q 36 28 62 32 Q 36 36 32 62 Q 28 36 2 32 Q 28 28 32 2 Z" fill="%s"/>' % W),
}

def build_sprites():
    work = tempfile.mkdtemp()
    for name, svgtxt in SPRITES.items():
        open(os.path.join(work, name + ".svg"), "w").write(svgtxt)
    subprocess.check_call(["node", os.path.join(HERE, "render_svg.js"), work, "128"])
    for name in SPRITES:
        im = Image.open(os.path.join(work, name + ".png")).convert("RGBA")
        write_tga(im.resize((64, 64), Image.LANCZOS), os.path.join(OUT, name + ".tga"))
    return len(SPRITES)

ITEMS = [  # key, drawing, kind (the VEC kind), icon framing (zoom into the drawing's crop)
    ("n8_harness", chest_n8, "chest"),
    ("caff_bow", bow_espresso, "weapon"),
    ("bd_hammer", hammer_justice, "weapon"),
    ("shua_robe", robe_shua, "chest"),
    ("ziggu_wand", wand_ziggu, "weapon"),
    ("iverson_band", headband_iverson, "head"),
]

def pow2(n):
    p = 8
    while p < n: p *= 2
    return p

def icon_from(im, size=64):
    """a WoW-style square icon: a dark rich background, the drawing fitted in, a legendary orange frame"""
    bg = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(bg)
    for y in range(size):
        t = y / (size - 1)
        d.line([(0, y), (size, y)], fill=(int(58 - 30 * t), int(30 - 16 * t), int(64 - 30 * t), 255))
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([size * 0.12, size * 0.12, size * 0.88, size * 0.88], fill=(255, 150, 60, 90))
    bg = Image.alpha_composite(bg, glow.filter(ImageFilter.GaussianBlur(size / 8)))
    pic = im.copy()
    pic.thumbnail((int(size * 0.84), int(size * 0.84)), Image.LANCZOS)
    bg.alpha_composite(pic, ((size - pic.width) // 2, (size - pic.height) // 2))
    d = ImageDraw.Draw(bg)
    d.rectangle([0, 0, size - 1, size - 1], outline=(255, 128, 0, 255), width=3)
    d.rectangle([3, 3, size - 4, size - 4], outline=(120, 50, 0, 255), width=1)
    return bg

def build():
    work = tempfile.mkdtemp()
    for key, fn, kind in ITEMS:
        open(os.path.join(work, key + ".svg"), "w").write(V.svg(fn()))
    subprocess.check_call(["node", os.path.join(HERE, "render_svg.js"), work, "256"])
    # big versions for the icons and the poster
    big = os.path.join(work, "big"); os.makedirs(big)
    for key, fn, kind in ITEMS:
        open(os.path.join(big, key + ".svg"), "w").write(V.svg(fn()))
    subprocess.check_call(["node", os.path.join(HERE, "render_svg.js"), big, "768"])
    lines = ["-- Generated by tools/make_custom_legendaries.py: the made-up Legendaries' own drawings (CustomGear.lua).",
             "-- texture, x, y, w, h (512 canvas), used u, v of the texture, kind (as VectorData.lua)",
             "local ADDON, TCF = ...", "local V = TCF.VEC"]
    crops = {}
    for key, fn, kind in ITEMS:
        im = Image.open(os.path.join(work, key + ".png")).convert("RGBA")
        bb = im.getbbox()
        x0, y0, x1, y1 = bb
        w, h = x1 - x0, y1 - y0
        tw, th = pow2(w), pow2(h)
        canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        canvas.paste(im.crop(bb), (0, 0))
        write_tga(canvas, os.path.join(OUT, "i_tcf_" + key + ".tga"))
        lines.append('V["tcf:%s"]={"i_tcf_%s",%d,%d,%d,%d,%.4f,%.4f,"%s"}' % (key, key, x0 * 2, y0 * 2, w * 2, h * 2, w / tw, h / th, kind))
        bigim = Image.open(os.path.join(big, key + ".png")).convert("RGBA")
        crops[key] = bigim.crop(bigim.getbbox())
        write_tga(icon_from(crops[key]), os.path.join(OUT, "ic_tcf_" + key + ".tga"))
    open(os.path.join(ROOT, "CustomGearArt.lua"), "w", newline="\n").write("\n".join(lines) + "\n")
    print("wrote %d drawings and icons" % len(ITEMS))
    return crops

if __name__ == "__main__":
    build()
    print("wrote %d effect sprites" % build_sprites())
