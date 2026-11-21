#!/usr/bin/env python3
"""Composite cat layers the same way the addon does, for a showcase sheet."""
import os, sys
from PIL import Image, ImageDraw, ImageChops
sys.path.insert(0, os.path.dirname(__file__))
import make_art as A

A.main() if not A.ART else None

def tint(im, c):
    if c is None: return im
    r, g, b = [int(v * 255) for v in c]
    solid = Image.new("RGBA", im.size, (r, g, b, 255))
    out = ImageChops.multiply(im, solid)
    out.putalpha(im.getchannel("A"))
    return out

def layer(canvas, name, c=None, dx=0, dy=0, alpha=1.0):
    im = A.ART.get(name)
    if im is None: return
    if im.size != (64, 64): im = im.resize((64, 64), Image.BILINEAR)
    im = tint(im, c)
    if alpha < 1: im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    tmp = Image.new("RGBA", (96, 96), (0, 0, 0, 0)); tmp.paste(im, (16 + dx, 16 + dy), im)
    canvas.alpha_composite(tmp)

def two(canvas, base, c1, c2, dx=0, dy=0):
    if base + "_a" in A.ART:
        layer(canvas, base + "_a", c1, dx, dy); layer(canvas, base + "_b", c2 or c1, dx, dy)
    else:
        layer(canvas, base, c1, dx, dy)

def cat(fur=(1, .78, .5), face="normal", L="down", Rp="up", g=None):
    g = g or {}
    c = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    if "fx_back" in g: layer(c, g["fx_back"][0], g["fx_back"][1], alpha=.7)
    if "back" in g: two(c, *g["back"])
    layer(c, "cat_fur", fur)
    if "pattern" in g: two(c, *g["pattern"])
    if "chest" in g: two(c, *g["chest"])
    layer(c, "face_" + face)
    if "acc" in g: two(c, *g["acc"])
    if "head" in g: two(c, *g["head"])
    rdx, rdy = (6, -14) if Rp == "up" else (0, 0)
    ldx, ldy = (-6, -14) if L == "up" else (0, 0)
    layer(c, "paw_L_%s_a" % L, fur); layer(c, "paw_L_%s_b" % L, (1, .6, .7))
    layer(c, "paw_R_%s_a" % Rp, fur); layer(c, "paw_R_%s_b" % Rp, (1, .6, .7))
    if "main" in g: two(c, *g["main"], dx=rdx, dy=rdy)
    if "off" in g: two(c, *g["off"], dx=ldx, dy=ldy)
    if "fx_front" in g: layer(c, g["fx_front"][0], g["fx_front"][1], alpha=.8)
    return c

STEEL = (.75, .8, .9); GOLD = (1, .82, .3); DARK = (.35, .3, .4); RED = (.8, .2, .2)
PURPLE = (.55, .3, .9); GREEN = (.35, .75, .3); BROWN = (.55, .38, .22); WHITE = (1, 1, 1); BLUE = (.3, .5, 1)

LOOKS = [
    ("Base", dict(), (1, 1, 1)),
    ("Warrior", dict(head=("head_hornhelm", STEEL, (.95, .9, .8)), chest=("chest_plate", STEEL, GOLD),
                     main=("wpn_sword", STEEL, BROWN), off=("off_roundshield", RED, GOLD), back=("back_cape", RED, GOLD)), (1, .7, .4)),
    ("Mage", dict(head=("head_wizard", BLUE, GOLD), chest=("chest_robe", BLUE, GOLD), main=("wpn_staff", (.6, .9, 1), BROWN),
                  off=("off_tome", PURPLE, WHITE), fx_front=("fx_sparkles", (.6, .8, 1))), (.85, .85, .9)),
    ("Rogue", dict(head=("head_mask", DARK, DARK), chest=("chest_leather", BROWN, (.8, .7, .5)), main=("wpn_dagger", STEEL, DARK),
                   off=("off_dagger", STEEL, DARK), back=("back_cape", DARK, STEEL)), (.3, .3, .35)),
    ("Hunter", dict(head=("head_featcap", GREEN, (1, .4, .3)), chest=("chest_furmantle", BROWN, WHITE), main=("wpn_bow", BROWN, WHITE),
                    back=("back_quiver", BROWN, WHITE)), (.95, .75, .5)),
    ("Warlock", dict(head=("head_horns", DARK, RED), chest=("chest_spiked", PURPLE, DARK), main=("wpn_scythe", (.5, 1, .4), DARK),
                     off=("off_skull", (.9, .9, .8), DARK), back=("back_batwings", PURPLE, DARK), fx_back=("fx_wisps", (.5, 1, .3))), (.25, .2, .3)),
    ("Priest", dict(head=("head_halo", GOLD, GOLD), chest=("chest_vestment", WHITE, GOLD), main=("wpn_wand", GOLD, WHITE),
                    off=("off_lantern", GOLD, (1, 1, .7)), back=("back_angelwings", WHITE, GOLD), fx_back=("fx_rays", (1, .9, .5))), (1, 1, 1)),
    ("Paladin", dict(head=("head_winghelm", GOLD, WHITE), chest=("chest_plate", GOLD, WHITE), main=("wpn_hammer", GOLD, BROWN),
                     off=("off_kiteshield", BLUE, GOLD), fx_back=("fx_aura", (1, .85, .4))), (1, .85, .6)),
    ("Druid", dict(head=("head_antlers", BROWN, GREEN), chest=("chest_leaves", GREEN, BROWN), main=("wpn_staff", (.6, 1, .5), BROWN),
                   back=("back_vines", GREEN, (.6, 1, .5)), fx_front=("fx_leaves", (.5, .9, .4))), (.8, .6, .4)),
    ("Shaman", dict(head=("head_headdress", BROWN, (.4, .7, 1)), chest=("chest_furmantle", BROWN, (.4, .8, 1)), main=("wpn_totem", BROWN, BROWN),
                    off=("off_totem", (.4, .6, 1), DARK), fx_front=("fx_lightning", (.5, .8, 1))), (.6, .6, .65)),
    ("Party", dict(head=("head_partyhat", (1, .4, .7), WHITE), acc=("acc_shades", DARK, WHITE), pattern=("pat_tabby", (.8, .5, .2), None),
                   fx_front=("fx_notes", (1, .9, .5))), (1, .75, .4)),
    ("Royal", dict(head=("head_crown", GOLD, (1, .3, .4)), acc=("acc_monocle", GOLD, GOLD), chest=("chest_tabard", PURPLE, GOLD),
                   main=("wpn_fishpole", BROWN, WHITE), fx_back=("fx_runes", PURPLE)), (.95, .95, .95)),
]

def sheet(path, scale=3):
    cols = 4; rows = (len(LOOKS) + cols - 1) // cols
    W = 96 * scale; H = 96 * scale + 20
    out = Image.new("RGBA", (cols * W, rows * H), (38, 34, 46, 255))
    d = ImageDraw.Draw(out)
    for i, (title, g, fur) in enumerate(LOOKS):
        c = cat(fur=fur, g=g, L="down" if i % 2 else "up", Rp="up" if i % 2 else "down")
        c = c.resize((96 * scale, 96 * scale), Image.NEAREST)
        x, y = (i % cols) * W, (i // cols) * H
        out.alpha_composite(c, (x, y + 16))
        d.text((x + 8, y + 4), title, fill=(255, 220, 120, 255))
    out.save(path)

if __name__ == "__main__":
    sheet(sys.argv[1] if len(sys.argv) > 1 else "showcase.png")
