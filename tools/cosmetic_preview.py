"""Review sheet: every cartoon cosmetic on the cat, tinted the way the game tints it.
usage: python3 tools/cosmetic_preview.py out.png"""
import os, re, sys
from PIL import Image, ImageChops, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = {}
for m in re.finditer(r'V\["([^"]+)"\]=\{"([^"]+)",(\d+),(\d+),(\d+),(\d+),([\d.]+),([\d.]+),"(\w+)"\}', open(os.path.join(ROOT, "VectorData.lua")).read()):
    k, t, x, y, w, h, u, v, kind = m.groups(); V[k] = (t, int(x), int(y), int(w), int(h), float(u), float(v), kind)
cache = {}
def piece(key):
    if key not in cache:
        t, x, y, w, h, u, v, kind = V[key]; im = Image.open(os.path.join(ROOT, "Art", "v", t + ".tga")).convert("RGBA")
        cache[key] = (im.crop((0, 0, round(u * im.width), round(v * im.height))).resize((w, h), Image.LANCZOS), x, y, kind)
    return cache[key]
def tint(im, c):
    m = ImageChops.multiply(im, Image.new("RGBA", im.size, tuple(int(v * 255) for v in c) + (255,))); m.putalpha(im.getchannel("A")); return m
FUR = (1, .72, .45); ST = tuple(c * .8 for c in FUR); C1 = (.35, .55, .95); C2 = (1, .8, .3); LIFT = 44
arts = [l.split("|")[0].strip() for l in open(os.path.join(ROOT, "tools", "item_specs", "cosmetics.txt")) if l.strip() and not l.startswith("#")]
def put(c, key, col=None, flip=False, lift=0):
    if key not in V: return
    im, x, y, kind = piece(key)
    if col: im = tint(im, col)
    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT); x = 512 - x - im.width
    c.alpha_composite(im, (x, y - lift))
def cos(c, art, flip=False, lift=0):
    for p, col in (("a", C1), ("b", C2), ("f", None)): put(c, "cos:%s:%s" % (art, p), col, flip, lift)
S, cols = 200, 10
rows = (len(arts) + cols - 1) // cols
sheet = Image.new("RGBA", (cols * S, rows * (S + 16)), (245, 236, 226, 255)); d = ImageDraw.Draw(sheet)
for i, art in enumerate(arts):
    kind = V.get("cos:%s:a" % art, V.get("cos:%s:f" % art))[7]
    c = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    if kind == "back": cos(c, art)
    for k, col in (("body_t", FUR), ("body_marks_t", ST), ("belly", None), ("body_line", None)): put(c, "cat:" + k, col)
    if kind == "chest": cos(c, art)
    for k, col in (("head_t", FUR), ("head_marks_t", ST), ("face_normal", None)): put(c, "cat:" + k, col)
    if kind in ("acc", "head"): cos(c, art)
    if kind == "weapon": cos(c, art, flip=art.startswith("off_"), lift=LIFT)
    for k, col in (("paw_L_down_t", FUR), ("paw_L_down", None), ("paw_R_down_t", FUR), ("paw_R_down", None)): put(c, "cat:" + k, col, lift=LIFT)
    if kind in ("shield", "held"): cos(c, art, lift=LIFT)
    x, y = (i % cols) * S, (i // cols) * (S + 16)
    sheet.alpha_composite(c.resize((S, S), Image.LANCZOS), (x, y + 16)); d.text((x + 4, y + 2), art, fill=(110, 60, 30, 255))
sheet.save(sys.argv[1])
