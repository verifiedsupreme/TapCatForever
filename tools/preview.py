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

RACES = [("Human", (0.25, 0.4, 0.85), (1, 0.82, 0.3)), ("Dwarf", (0.8, 0.4, 0.15), (1, 0.8, 0.3)),
         ("Night Elf", (0.72, 0.58, 0.92), (0.35, 0.85, 0.75)), ("Gnome", (0.75, 0.55, 0.3), (0.6, 0.9, 1)),
         ("Orc", (0.95, 0.92, 0.82), (0.65, 0.15, 0.15)), ("Undead", (0.25, 0.22, 0.28), (0.9, 0.88, 0.8)),
         ("Tauren", (0.95, 0.9, 0.78), (1, 0.8, 0.3)), ("Troll", (0.95, 0.92, 0.82), (0.9, 0.3, 0.25)),
         ("Skyborne", (0.55, 0.8, 1), (1, 1, 1))]

def race_sheet(path, scale=3):
    cols = 5; rows = 2
    W = 96 * scale; H = 96 * scale + 20
    out = Image.new("RGBA", (cols * W, rows * H), (38, 34, 46, 255))
    d = ImageDraw.Draw(out)
    furs = [(1, .75, .45), (.85, .85, .9), (.45, .42, .5), (1, 1, 1), (.75, .55, .4)]
    for i, (name, c1, c2) in enumerate(RACES):
        key = "acc_race_" + name.lower().replace(" ", "")
        c = cat(fur=furs[i % len(furs)], g={"acc": (key, c1, c2)})
        c = c.resize((96 * scale, 96 * scale), Image.NEAREST)
        x, y = (i % cols) * W, (i // cols) * H
        out.alpha_composite(c, (x, y + 16))
        d.text((x + 8, y + 4), name, fill=(255, 220, 120, 255))
    out.save(path)

SKINS = [
    ("Striped Frostsaber", (0.95, 0.97, 1), ("skin_stripes", (0.55, 0.62, 0.75)), (0.5, 0.8, 1), None, 1),
    ("Striped Nightsaber", (0.36, 0.28, 0.46), ("skin_stripes", (0.16, 0.12, 0.22)), (0.8, 0.6, 1), None, 1),
    ("Spotted Frostsaber", (0.95, 0.97, 1), ("pat_leopard", (0.55, 0.6, 0.72)), (0.5, 0.8, 1), None, 1),
    ("Black Panther", (0.16, 0.15, 0.18), None, (1, 0.85, 0.2), None, 1),
    ("Swift Zulian Tiger", (1, 0.55, 0.15), ("skin_stripes", (0.12, 0.08, 0.05)), (0.4, 1, 0.4), None, 1),
    ("Winterspring Frostsaber", (0.82, 0.92, 1), ("skin_stripes", (0.62, 0.8, 1)), (0.4, 0.9, 1), None, 1),
    ("Spectral Tiger", (0.45, 1, 0.9), ("skin_stripes", (0.2, 0.6, 0.6)), (0.6, 1, 1), None, 0.6),
    ("Skeletal Cat", (0.24, 0.22, 0.27), ("skin_bones", (0.92, 0.9, 0.82)), (0.4, 1, 0.6), None, 1),
    ("Mechanical Kitty", (0.6, 0.63, 0.68), ("skin_plates", (0.35, 0.37, 0.42), (0.95, 0.8, 0.4)), (1, 0.3, 0.2), None, 1),
    ("Fel Kitty", (0.38, 0.85, 0.3), ("skin_stripes", (0.15, 0.42, 0.1)), (0.9, 1, 0.3), None, 1),
    ("Darkmoon Kitty", (0.92, 0.58, 0.88), ("skin_stars", (1, 1, 0.7)), None, None, 1),
    ("Golden Lion", (1, 0.82, 0.42), None, None, ("skin_mane", (0.78, 0.46, 0.16)), 1),
]

def skin_cat(fur, overlay, eyes, mane, alpha):
    c = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    if mane: layer(c, mane[0], mane[1])
    layer(c, "cat_fur", fur, alpha=alpha)
    if overlay:
        if overlay[0] + "_a" in A.ART: layer(c, overlay[0] + "_a", overlay[1]); layer(c, overlay[0] + "_b", overlay[2])
        else: layer(c, overlay[0], overlay[1])
    layer(c, "face_normal")
    if eyes: layer(c, "skin_eyes", eyes)
    layer(c, "paw_L_up_a", fur, alpha=alpha); layer(c, "paw_L_up_b", (1, .6, .7))
    layer(c, "paw_R_down_a", fur, alpha=alpha); layer(c, "paw_R_down_b", (1, .6, .7))
    return c

def skin_sheet(path, scale=3):
    cols = 4; rows = 3
    W = 96 * scale; H = 96 * scale + 20
    out = Image.new("RGBA", (cols * W, rows * H), (38, 34, 46, 255))
    d = ImageDraw.Draw(out)
    for i, (name, fur, ov, eyes, mane, alpha) in enumerate(SKINS):
        c = skin_cat(fur, ov, eyes, mane, alpha).resize((96 * scale, 96 * scale), Image.NEAREST)
        x, y = (i % cols) * W, (i // cols) * H
        out.alpha_composite(c, (x, y + 16))
        d.text((x + 8, y + 4), name, fill=(255, 220, 120, 255))
    out.save(path)

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "skins":
        skin_sheet(sys.argv[1]); sys.exit(0)
    if len(sys.argv) > 2 and sys.argv[2] == "races":
        race_sheet(sys.argv[1]); sys.exit(0)
    sheet(sys.argv[1] if len(sys.argv) > 1 else "showcase.png")
