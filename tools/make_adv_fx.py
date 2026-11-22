"""Adventure track: stand-in drawings for the six boss-unlocked back effects (BossEffects.lua).

Simple near-white glow sprites in the style of the existing Art/fx_*.tga (soft white shapes the
game tints with the item colour), each its own shape so none looks like a class effect:
  fx_boss_storm   a crackling ring of zig-zag bolts with small storm clouds on top
  fx_boss_fire    a crown of flame tongues all around the cat, with embers
  fx_boss_frost   a ring of ice shards and little snowflakes in a frosty mist
  fx_boss_shadow  smoky tendrils curling around the cat
  fx_boss_holy    a halo with a cross of light and diamond sparkles
  fx_boss_nature  a leafy vine ring with glowing wisp orbs
The art track can replace them with full sticker-style drawings (tools/art_specs_adv/boss_effects.txt).

usage: python3 tools/make_adv_fx.py [preview.png] -> Art/adv/fx_boss_*.tga
"""
import math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_art import write_tga

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "Art", "adv")
S = 4            # supersampling
N = 256 * S      # working size
C = N / 2


def new():
    return Image.new("L", (N, N), 0)


def finish(shape, glow=10, glow_alpha=0.55, core=None):
    """shape: L mask of the solid parts. Adds a soft glow around it (and an optional brighter core
    mask) and returns a 256 x 256 white RGBA image."""
    glow_mask = shape.filter(ImageFilter.GaussianBlur(glow * S)).point(lambda v: int(min(255, v * glow_alpha * 1.6)))
    solid = shape.point(lambda v: int(v * 0.86))
    out = ImageChops_lighter(glow_mask, solid)
    if core is not None:
        out = ImageChops_lighter(out, core)
    out = out.resize((256, 256), Image.LANCZOS)
    rgba = Image.new("RGBA", (256, 256), (255, 255, 255, 0))
    rgba.putalpha(out)
    return rgba


def ImageChops_lighter(a, b):
    from PIL import ImageChops
    return ImageChops.lighter(a, b)


def pol(r, ang):
    return (C + r * math.cos(ang), C - r * math.sin(ang))


def zigzag(d, r0, r1, ang, width, kinks=4, jitter=0.12, rnd=None):
    pts = []
    for i in range(kinks + 1):
        t = i / kinks
        r = r0 + (r1 - r0) * t
        off = (jitter if i % 2 else -jitter) * (1 if i not in (0, kinks) else 0)
        pts.append(pol(r, ang + off))
    d.line(pts, fill=255, width=int(width * S), joint="curve")
    for p in pts:
        rr = width * S / 2
        d.ellipse((p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr), fill=255)


def bolt(d, ang, r0, length, width, fill=255):
    # a chunky cartoon lightning bolt pointing outward (u: along the radius, v: across it)
    shape = [(0.0, -0.22), (0.52, -0.50), (0.47, -0.12), (1.0, -0.34), (0.46, 0.42), (0.52, 0.06), (0.0, 0.26)]
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for u, v in shape:
        x = r0 + u * length
        y = v * width
        pts.append((C + x * ca - y * sa, C - (x * sa + y * ca)))
    d.polygon(pts, fill=fill)


def storm():
    m = new(); d = ImageDraw.Draw(m)
    # a thin crackling ring
    pts = []
    for k in range(97):
        ang = 2 * math.pi * k / 96
        pts.append(pol((100 + (6 if k % 2 else -6)) * S, ang))
    d.line(pts, fill=200, width=3 * S, joint="curve")
    # eight chunky bolts around the cat, the top ones bigger
    for i in range(8):
        ang = 2 * math.pi * i / 8 + math.pi / 8
        big = 1 + 0.25 * max(0, math.sin(ang))
        bolt(d, ang, 86 * S, 34 * S * big, 30 * S * big)
    # storm clouds over the top
    cl = new(); dc = ImageDraw.Draw(cl)
    for cx, cy, r in ((-62, 104, 16), (-44, 112, 19), (-24, 104, 14), (30, 106, 15), (50, 114, 19), (70, 104, 14)):
        x, y = C + cx * S, C - cy * S
        dc.ellipse((x - r * S, y - r * S * 0.8, x + r * S, y + r * S * 0.8), fill=210)
    m = ImageChops_lighter(m, cl)
    # sparks
    rnd = random.Random(7)
    d = ImageDraw.Draw(m)
    for _ in range(12):
        ang, r = rnd.random() * 2 * math.pi, (92 + rnd.random() * 30) * S
        x, y = pol(r, ang)
        s = (1.5 + rnd.random() * 2) * S
        d.ellipse((x - s, y - s, x + s, y + s), fill=255)
    return finish(m, glow=9, glow_alpha=0.6)


def flame(d, ang, r0, length, width):
    # a teardrop flame tongue pointing outward, tip bent a little
    base_l, base_r = pol(r0, ang - width), pol(r0, ang + width)
    tip = pol(r0 + length, ang + 0.08)
    mid_l, mid_r = pol(r0 + length * 0.45, ang - width * 1.15), pol(r0 + length * 0.45, ang + width * 1.05)
    d.polygon([base_l, mid_l, tip, mid_r, base_r], fill=255)
    rr = math.hypot(base_l[0] - base_r[0], base_l[1] - base_r[1]) / 2
    cx, cy = pol(r0, ang)
    d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=255)


def fire():
    m = new(); d = ImageDraw.Draw(m)
    n = 14
    core = new(); dc = ImageDraw.Draw(core)
    for i in range(n):
        ang = 2 * math.pi * i / n + math.pi / 2
        up = max(0.0, math.sin(ang))          # a bonfire crown: taller flames at the top
        big = 1.0 if i % 2 == 0 else 0.72
        length = (26 + 18 * up) * big * S
        flame(d, ang, 84 * S, length, 0.2 * big)
        flame(dc, ang, 86 * S, length * 0.5, 0.09 * big)
    d.ellipse((C - 90 * S, C - 90 * S, C + 90 * S, C + 90 * S), outline=255, width=8 * S)
    rnd = random.Random(3)
    for _ in range(14):
        ang = rnd.random() * math.pi * 0.9 + math.pi * 0.05   # embers float up
        x, y = pol((112 + rnd.random() * 12) * S, ang)
        s = (1.5 + rnd.random() * 2.5) * S
        d.ellipse((x - s, y - s, x + s, y + s), fill=230)
    return finish(m, glow=10, glow_alpha=0.6, core=core)


def shard(d, ang, r0, length, width):
    a = pol(r0, ang); b = pol(r0 + length * 0.35, ang - width); tip = pol(r0 + length, ang); c = pol(r0 + length * 0.35, ang + width)
    d.polygon([a, b, tip, c], fill=255)


def snowflake(d, x, y, r, w):
    for k in range(3):
        ang = math.pi / 3 * k
        dx, dy = r * math.cos(ang), r * math.sin(ang)
        d.line((x - dx, y - dy, x + dx, y + dy), fill=255, width=int(w))
        for sgn in (-1, 1):
            bx, by = x + sgn * dx * 0.55, y + sgn * dy * 0.55
            for t in (-1, 1):
                a2 = ang + t * math.pi / 4 + (math.pi if sgn < 0 else 0)
                d.line((bx, by, bx + r * 0.35 * math.cos(a2), by + r * 0.35 * math.sin(a2)), fill=255, width=int(w * 0.8))


def frost():
    m = new(); d = ImageDraw.Draw(m)
    for i in range(8):
        ang = 2 * math.pi * i / 8 + math.pi / 8
        shard(d, ang, 92 * S, (34 if i % 2 == 0 else 24) * S, 0.07)
    for i in range(8):
        ang = 2 * math.pi * i / 8
        x, y = pol(108 * S, ang)
        snowflake(d, x, y, 10 * S, 2.6 * S)
    mist = new(); dm = ImageDraw.Draw(mist)
    dm.ellipse((C - 100 * S, C - 100 * S, C + 100 * S, C + 100 * S), outline=150, width=14 * S)
    mist = mist.filter(ImageFilter.GaussianBlur(6 * S))
    m = ImageChops_lighter(m, mist)
    return finish(m, glow=7, glow_alpha=0.5)


def shadow():
    m = new(); d = ImageDraw.Draw(m)
    # five smoky tendrils spiralling around the cat, thick at the root, thin at the tip
    for k in range(5):
        a0 = 2 * math.pi * k / 5
        steps = 40
        for i in range(steps):
            t = i / steps
            ang = a0 + t * 1.9
            r = (84 + 40 * t) * S
            w = (13 * (1 - t) + 2) * S
            x, y = pol(r, ang)
            d.ellipse((x - w, y - w, x + w, y + w), fill=int(235 - 60 * t))
    # little wisps
    rnd = random.Random(11)
    for _ in range(10):
        ang, r = rnd.random() * 2 * math.pi, (96 + rnd.random() * 26) * S
        x, y = pol(r, ang)
        s = (3 + rnd.random() * 3) * S
        d.ellipse((x - s, y - s * 1.4, x + s, y + s * 1.4), fill=190)
    m = m.filter(ImageFilter.GaussianBlur(1.5 * S))
    return finish(m, glow=12, glow_alpha=0.65)


def diamond(d, x, y, r):
    d.polygon([(x, y - r), (x + r * 0.45, y), (x, y + r), (x - r * 0.45, y)], fill=255)
    d.polygon([(x - r, y), (x, y - r * 0.45), (x + r, y), (x, y + r * 0.45)], fill=255)


def holy():
    m = new(); d = ImageDraw.Draw(m)
    # halo: two rings
    d.ellipse((C - 104 * S, C - 104 * S, C + 104 * S, C + 104 * S), outline=255, width=6 * S)
    d.ellipse((C - 92 * S, C - 92 * S, C + 92 * S, C + 92 * S), outline=170, width=3 * S)
    # a cross of light: four long tapered beams, four short ones between
    for i in range(8):
        ang = math.pi / 4 * i + math.pi / 2
        long = i % 2 == 0
        r0, r1, w = 104 * S, (128 if long else 118) * S, (0.09 if long else 0.06)
        d.polygon([pol(r0, ang - w), pol(r1, ang), pol(r0, ang + w)], fill=255)
    for x, y, r in ((-78, 86, 9), (84, 74, 7), (0, -120, 6)):
        diamond(d, C + x * S, C - y * S, r * S)
    return finish(m, glow=11, glow_alpha=0.6)


def leaf(d, x, y, ang, length, width):
    tip = (x + length * math.cos(ang), y - length * math.sin(ang))
    mx, my = (x + tip[0]) / 2, (y + tip[1]) / 2
    nx, ny = -math.sin(ang) * width, -math.cos(ang) * width
    d.polygon([(x, y), (mx + nx, my + ny), tip, (mx - nx, my - ny)], fill=255)


def nature():
    m = new(); d = ImageDraw.Draw(m)
    # a wavy vine ring
    pts = []
    for i in range(361):
        ang = math.radians(i)
        r = (104 + 6 * math.sin(ang * 7)) * S
        pts.append(pol(r, ang))
    d.line(pts, fill=255, width=5 * S, joint="curve")
    # leaves along it
    for i in range(14):
        ang = 2 * math.pi * i / 14
        r = (104 + 6 * math.sin(ang * 7)) * S
        x, y = pol(r, ang)
        out = ang + (0.6 if i % 2 else -0.6)
        leaf(d, x, y, out, 22 * S, 7 * S)
    # glowing wisp orbs
    core = new(); dc = ImageDraw.Draw(core)
    for i in range(5):
        ang = 2 * math.pi * i / 5 + 0.3
        x, y = pol(124 * S, ang)
        r = 7 * S
        d.ellipse((x - r * 1.6, y - r * 1.6, x + r * 1.6, y + r * 1.6), fill=150)
        dc.ellipse((x - r, y - r, x + r, y + r), fill=255)
    return finish(m, glow=9, glow_alpha=0.55, core=core)


def main():
    os.makedirs(OUT, exist_ok=True)
    made = []
    for name, fn in (("fx_boss_storm", storm), ("fx_boss_fire", fire), ("fx_boss_frost", frost),
                     ("fx_boss_shadow", shadow), ("fx_boss_holy", holy), ("fx_boss_nature", nature)):
        im = fn()
        write_tga(im, os.path.join(OUT, name + ".tga"))
        made.append((name, im))
    print("wrote", len(made), "sprites to", OUT)
    if len(sys.argv) > 1:
        # a preview: each tinted with its item colour on a dark background
        cols = {"fx_boss_storm": (0.55, 0.65, 1.0), "fx_boss_fire": (1.0, 0.55, 0.12), "fx_boss_frost": (0.70, 0.95, 1.0),
                "fx_boss_shadow": (0.55, 0.25, 0.85), "fx_boss_holy": (1.0, 0.92, 0.55), "fx_boss_nature": (0.45, 1.0, 0.55)}
        sheet = Image.new("RGBA", (256 * 3, 256 * 2), (40, 36, 60, 255))
        for i, (name, im) in enumerate(made):
            r, g, b = cols[name]
            tinted = Image.merge("RGBA", (im.getchannel("R").point(lambda v: int(v * r)), im.getchannel("G").point(lambda v: int(v * g)),
                                          im.getchannel("B").point(lambda v: int(v * b)), im.getchannel("A")))
            cell = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            cell.alpha_composite(tinted)
            # a cat-sized placeholder in the middle, as the cat covers it in game
            dd = ImageDraw.Draw(cell)
            dd.ellipse((128 - 64, 128 - 70, 128 + 64, 128 + 76), fill=(70, 60, 80, 255), outline=(20, 16, 26, 255), width=4)
            sheet.alpha_composite(cell, ((i % 3) * 256, (i // 3) * 256))
        sheet.save(sys.argv[1])
        print("preview:", sys.argv[1])


if __name__ == "__main__":
    main()
