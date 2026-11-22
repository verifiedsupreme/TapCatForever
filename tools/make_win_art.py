#!/usr/bin/env python3
"""Sprites for the main window's compact layout (window track): the ring around the round tab
buttons, their glow, and the two layout icons (a cat-eared phone for compact, a wide window for
the full layout). Flat sticker style with thick dark outlines, like the cat.
usage: python3 tools/make_win_art.py  ->  Art/win/<name>.tga"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_art import write_tga

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "Art", "win")
INK = (59, 38, 32, 255)
GOLD, GOLD_HI, GOLD_LO = (242, 186, 72, 255), (255, 226, 140, 255), (196, 132, 40, 255)
CREAM, FUR, SKY, PINK = (255, 241, 214, 255), (245, 160, 74, 255), (150, 210, 255, 255), (255, 159, 178, 255)
SS = 4  # supersampling


def canvas(n):
    return Image.new("RGBA", (n * SS, n * SS), (0, 0, 0, 0))


def done(im, n):
    return im.resize((n, n), Image.LANCZOS)


def circle(d, cx, cy, r, fill):
    d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=fill)


def ring():
    # outer ink, gold band with a lighter top and darker bottom, inner ink; the middle stays clear
    n = 128
    im = canvas(n); d = ImageDraw.Draw(im)
    circle(d, 64, 64, 63, INK)
    circle(d, 64, 64, 57.5, GOLD_LO)
    band = canvas(n); bd = ImageDraw.Draw(band)
    circle(bd, 64, 62.5, 57, GOLD)
    im.alpha_composite(band)
    hi = canvas(n); hd = ImageDraw.Draw(hi)
    hd.arc([14 * SS, 12 * SS, 114 * SS, 112 * SS], 200, 340, fill=GOLD_HI, width=5 * SS)
    im.alpha_composite(hi)
    circle(d, 64, 64, 49, INK)
    hole = Image.new("L", im.size, 0)
    ImageDraw.Draw(hole).ellipse([(64 - 45.5) * SS, (64 - 45.5) * SS, (64 + 45.5) * SS, (64 + 45.5) * SS], fill=255)
    im.putalpha(Image.composite(Image.new("L", im.size, 0), im.getchannel("A"), hole))
    return done(im, n)


def glow():
    n = 128
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    px = im.load()
    for y in range(n):
        for x in range(n):
            r = ((x - 63.5) ** 2 + (y - 63.5) ** 2) ** 0.5
            # brightest just outside the ring, fading out to the edge and in toward the icon
            t = max(0.0, 1 - abs(r - 54) / 12)
            px[x, y] = (255, 214, 110, int(255 * t ** 1.6))
    return im


def rrect(d, box, r, fill, outline=None, w=0):
    d.rounded_rectangle([v * SS for v in box], radius=r * SS, fill=fill, outline=outline, width=w * SS)


def compact_icon():
    # a phone with cat ears
    n = 64
    im = canvas(n); d = ImageDraw.Draw(im)
    for sx in (-1, 1):
        cx = 32 + sx * 9
        d.polygon([((cx - 9) * SS, 16 * SS), ((cx + sx * 4) * SS, 1 * SS), ((cx + 9) * SS, 16 * SS)], fill=INK)
        d.polygon([((cx - 4.5) * SS, 14 * SS), ((cx + sx * 3) * SS, 6 * SS), ((cx + 4.5) * SS, 14 * SS)], fill=PINK)
    rrect(d, (17, 9, 47, 61), 7, CREAM, INK, 4)
    rrect(d, (22, 15, 42, 49), 3, SKY, INK, 2)
    circle(d, 32, 55, 2.6, INK)
    # a little paw on the screen
    circle(d, 32, 35, 4.2, CREAM)
    for dx, dy in ((-4.5, -4), (-1.5, -6.5), (1.5, -6.5), (4.5, -4)):
        circle(d, 32 + dx, 35 + dy, 1.7, CREAM)
    return done(im, n)


def wide_icon():
    # a wide window: orange title bar, a column on the left, a page on the right
    n = 64
    im = canvas(n); d = ImageDraw.Draw(im)
    rrect(d, (3, 12, 61, 54), 6, CREAM, INK, 4)
    rrect(d, (5, 14, 59, 23), 3, FUR)
    d.line([(4 * SS, 23 * SS), (60 * SS, 23 * SS)], fill=INK, width=3 * SS)
    rrect(d, (9, 27, 24, 49), 2, PINK, INK, 2)
    rrect(d, (28, 27, 55, 49), 2, SKY, INK, 2)
    return done(im, n)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, im in (("tab_ring", ring()), ("tab_glow", glow()), ("layout_compact", compact_icon()), ("layout_wide", wide_icon())):
        write_tga(im, os.path.join(OUT, name + ".tga"))
        print("wrote", name)


if __name__ == "__main__":
    main()
