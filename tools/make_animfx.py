"""Shared sprites and tiles for the animated cosmetic layers (CatAnim.lua).

Sprites (white, so the game tints them): a_spark (four-point glint), a_ember (soft glowing dot),
a_flame (flame tongue), a_wisp (soft ghost wisp), a_glow (round soft glow).
Tiles (256x256, seamless, scrolled inside a shape by a mask): a_stars (star field), a_shine
(one diagonal shine band), a_nebula (soft coloured clouds), a_lava (molten blobs, own colours),
a_firetile (rising flame tongues, own colours), a_frost (frost crystals), a_swirl (water swirls).
a_catglow: a blurred white silhouette of the whole cat, for glows behind it (placed on the
full 512 canvas).
The ink-outlined sticker sprites of the tap effects (Art/v/t_<shape>) are used too: leaves,
snow, bubbles, coins, stars.

usage: python3 tools/make_animfx.py [out_dir]   (default Art/v)
"""
import math, os, random, re, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from make_art import write_tga

SS = 4  # supersampling

def canvas(n): return Image.new("RGBA", (n * SS, n * SS), (0, 0, 0, 0))
def down(im, n): return im.resize((n, n), Image.LANCZOS)

def star_pts(cx, cy, r1, r2, n=4, rot=-90):
    pts = []
    for k in range(n * 2):
        a = math.radians(rot + k * 180 / n); r = r1 if k % 2 == 0 else r2
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts

def soft_dot(n, core=0.18, falloff=2.2):
    im = Image.new("RGBA", (n, n), (255, 255, 255, 0)); px = im.load(); c = (n - 1) / 2
    for y in range(n):
        for x in range(n):
            d = math.hypot(x - c, y - c) / c
            a = 1.0 if d < core else max(0.0, 1 - (d - core) / (1 - core)) ** falloff
            px[x, y] = (255, 255, 255, int(255 * a))
    return im

def spark():
    n = 64; im = canvas(n); d = ImageDraw.Draw(im)
    glow = soft_dot(n * SS, 0.0, 3.0); glow.putalpha(glow.getchannel("A").point(lambda v: v * 0.55))
    im.alpha_composite(glow)
    d.polygon(star_pts(n * SS / 2, n * SS / 2, n * SS * 0.48, n * SS * 0.07), fill=(255, 255, 255, 255))
    d.polygon(star_pts(n * SS / 2, n * SS / 2, n * SS * 0.26, n * SS * 0.06, rot=-45), fill=(255, 255, 255, 230))
    return down(im, n)

def flame():
    n = 64; im = canvas(n); d = ImageDraw.Draw(im); S = SS
    def tongue(scale, col):
        pts = []
        for k in range(41):
            t = k / 40 * 2 * math.pi
            # teardrop: round bottom, pointed wavy top
            x = math.sin(t) * (1 - 0.0) * (0.5 + 0.5 * math.cos(t)) ** 0.8
            y = -math.cos(t)
            pts.append((32 * S + x * 22 * S * scale, 40 * S + (y * 26 - (8 if y < 0 else 0) * -y) * S * scale))
        d.polygon(pts, fill=col)
    tongue(1.0, (255, 140, 40, 235)); tongue(0.68, (255, 210, 70, 245)); tongue(0.36, (255, 250, 210, 255))
    return down(im.filter(ImageFilter.GaussianBlur(S * 0.8)), n).transpose(Image.FLIP_TOP_BOTTOM)

def wisp():
    n = 64; im = Image.new("RGBA", (n, n), (255, 255, 255, 0)); px = im.load()
    for y in range(n):
        for x in range(n):
            # a soft blob with a curling tail upwards
            dx, dy = (x - 32) / 18, (y - 40) / 16
            tail = math.exp(-((x - 32 - 8 * math.sin((40 - y) / 9)) / 6) ** 2) * (1 if y < 40 else 0) * max(0, (y - 6) / 34)
            a = max(math.exp(-(dx * dx + dy * dy) * 1.6), tail * 0.8)
            px[x, y] = (255, 255, 255, int(255 * min(1, a)))
    return im

def tile_blobs(n, seed, count, rmin, rmax, colours, blur, alpha=1.0):
    """seamless: draw on a 3x3 tiled canvas, keep the centre"""
    rnd = random.Random(seed); big = Image.new("RGBA", (n * 3, n * 3), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    for _ in range(count):
        x, y, r = rnd.random() * n, rnd.random() * n, rmin + rnd.random() * (rmax - rmin)
        col = colours[rnd.randrange(len(colours))]
        for ox in (0, n, 2 * n):
            for oy in (0, n, 2 * n):
                d.ellipse((x + ox - r, y + oy - r, x + ox + r, y + oy + r), fill=col)
    if blur: big = big.filter(ImageFilter.GaussianBlur(blur))
    out = big.crop((n, n, 2 * n, 2 * n))
    if alpha < 1: out.putalpha(out.getchannel("A").point(lambda v: int(v * alpha)))
    return out

def stars_tile():
    n = 256; rnd = random.Random(7); big = Image.new("RGBA", (n * 3 * 2, n * 3 * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    pts = [(rnd.random() * n, rnd.random() * n, rnd.random()) for _ in range(46)]
    for x, y, s in pts:
        for ox in (0, n, 2 * n):
            for oy in (0, n, 2 * n):
                cx, cy = (x + ox) * 2, (y + oy) * 2
                if s > 0.78: d.polygon(star_pts(cx, cy, 16 + s * 6, 3.2), fill=(255, 255, 255, 255))
                elif s > 0.45: d.ellipse((cx - 3.4, cy - 3.4, cx + 3.4, cy + 3.4), fill=(255, 255, 255, 235))
                else: d.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=(255, 255, 255, 170))
    big = big.resize((n * 3, n * 3), Image.LANCZOS)
    glow = big.filter(ImageFilter.GaussianBlur(3)); glow.putalpha(glow.getchannel("A").point(lambda v: min(255, v * 2)))
    out = Image.alpha_composite(glow, big)
    return out.crop((n, n, 2 * n, 2 * n))

def shine_tile():
    # one soft diagonal band per tile; scrolled sideways it sweeps across the fur now and then
    n = 256; im = Image.new("RGBA", (n, n), (255, 255, 255, 0)); px = im.load()
    for y in range(n):
        for x in range(n):
            u = ((x + y) % n) / n                 # position across the band, wraps both ways
            dd = min(abs(u - 0.5), 1 - abs(u - 0.5))  # distance to the band centre
            a = max(0.0, 1 - dd / 0.07) ** 1.5 * 0.85 + max(0.0, 1 - abs(u - 0.62) / 0.02) * 0.5
            px[x, y] = (255, 255, 255, int(255 * min(1, a)))
    return im

def frost_tile():
    n = 256; rnd = random.Random(11); big = Image.new("RGBA", (n * 3, n * 3), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    for _ in range(14):
        x, y, r = rnd.random() * n, rnd.random() * n, 10 + rnd.random() * 16
        for ox in (0, n, 2 * n):
            for oy in (0, n, 2 * n):
                cx, cy = x + ox, y + oy
                for k in range(6):
                    a = math.radians(k * 60 + 15)
                    ex, ey = cx + math.cos(a) * r, cy + math.sin(a) * r
                    d.line((cx, cy, ex, ey), fill=(255, 255, 255, 230), width=3)
                    for f in (0.55,):
                        bx, by = cx + math.cos(a) * r * f, cy + math.sin(a) * r * f
                        for s in (-1, 1):
                            b2 = a + s * math.radians(40)
                            d.line((bx, by, bx + math.cos(b2) * r * 0.35, by + math.sin(b2) * r * 0.35), fill=(255, 255, 255, 210), width=2)
    big = Image.alpha_composite(big.filter(ImageFilter.GaussianBlur(2.5)), big)
    return big.crop((n, n, 2 * n, 2 * n))

def swirl_tile():
    n = 256; im = Image.new("RGBA", (n, n), (255, 255, 255, 0)); px = im.load()
    for y in range(n):
        for x in range(n):
            u, v = x / n * 2 * math.pi, y / n * 2 * math.pi
            w = math.sin(u * 2 + math.sin(v * 2) * 1.6) + math.sin(v * 3 + math.cos(u) * 1.2)
            a = max(0.0, 1 - abs(w - 0.9) / 0.22) * 0.9
            px[x, y] = (255, 255, 255, int(255 * a))
    return im.filter(ImageFilter.GaussianBlur(1))

def fire_tile():
    # rising flame tongues in their own colours, seamless top to bottom and side to side
    n = 256; rnd = random.Random(5); big = Image.new("RGBA", (n * 3, n * 3), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    for _ in range(26):
        x, y, h = rnd.random() * n, rnd.random() * n, 40 + rnd.random() * 50
        for ox in (0, n, 2 * n):
            for oy in (0, n, 2 * n):
                cx, cy = x + ox, y + oy
                for s, col in ((1.0, (255, 110, 30, 200)), (0.62, (255, 190, 60, 225)), (0.3, (255, 245, 190, 240))):
                    w = h * 0.32 * s
                    d.polygon([(cx - w, cy), (cx - w * 0.6, cy - h * s * 0.5), (cx, cy - h * s), (cx + w * 0.6, cy - h * s * 0.5), (cx + w, cy), (cx, cy + w * 0.8)], fill=col)
    big = big.filter(ImageFilter.GaussianBlur(3))
    return big.crop((n, n, 2 * n, 2 * n))

def cat_glow():
    """a soft white silhouette of the cat (body, head, both paws) on the full 512 canvas, stored at 256"""
    vec = {}
    for m in re.finditer(r'V\["([^"]+)"\]=\{"([^"]+)",(\d+),(\d+),(\d+),(\d+),([\d.]+),([\d.]+),"(\w+)"\}', open(os.path.join(ROOT, "VectorData.lua")).read()):
        k, t, x, y, w, h, u, v, kind = m.groups(); vec[k] = (t, int(x), int(y), int(w), int(h), float(u), float(v))
    sil = Image.new("L", (512, 512), 0)
    for k in ("cat:body_t", "cat:head_t", "cat:paw_L_down_t", "cat:paw_R_down_t"):
        t, x, y, w, h, u, v = vec[k]
        im = Image.open(os.path.join(ROOT, "Art", "v", t + ".tga")).convert("RGBA")
        im = im.crop((0, 0, round(u * im.width), round(v * im.height))).resize((w, h), Image.LANCZOS)
        sil.paste(255, (x, y), im.getchannel("A"))
    sil = sil.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(14))
    out = Image.new("RGBA", (512, 512), (255, 255, 255, 0)); out.putalpha(sil)
    return out.resize((256, 256), Image.LANCZOS)

SPRITES = {
    "a_spark": spark, "a_ember": lambda: soft_dot(32, 0.22, 1.8), "a_glow": lambda: soft_dot(64, 0.0, 2.0),
    "a_flame": flame, "a_wisp": wisp,
    "a_stars": stars_tile, "a_shine": shine_tile,
    "a_nebula": lambda: tile_blobs(256, 3, 26, 18, 46, [(160, 90, 255, 150), (90, 150, 255, 140), (255, 110, 200, 120), (120, 230, 255, 90)], 18),
    "a_lava": lambda: tile_blobs(256, 9, 34, 10, 30, [(255, 120, 20, 255), (255, 190, 40, 255), (255, 240, 160, 255), (230, 60, 10, 255)], 5),
    "a_firetile": fire_tile, "a_frost": frost_tile, "a_swirl": swirl_tile,
    "a_catglow": cat_glow,
}

def main(out=None):
    out = out or (sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "Art", "v"))
    os.makedirs(out, exist_ok=True)
    for name, fn in SPRITES.items():
        write_tga(fn().convert("RGBA"), os.path.join(out, name + ".tga"))
    print("animation sprites:", len(SPRITES))

if __name__ == "__main__":
    main()
