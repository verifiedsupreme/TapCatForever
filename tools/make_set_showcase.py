#!/usr/bin/env python3
"""Pictures of the 1.7.0 crafted sets for the Discord patch notes (patch-notes/media/1.7.0_sets_*.png,
1200x675): every set worn by the cartoon cat (the addon's own drawing code), with its name, profession
and title. usage: make_set_showcase.py <font dir with Cinzel.ttf and Lato-Bold.ttf>"""
import os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_cards as mc
from make_cards import ROOT, glow, paste, shadow, sprite, cat_image, set_look, font

W, H, S = 1200, 675, 2
CW, CH = W * S, H * S
OUT = os.path.join(ROOT, "patch-notes", "media")

# key, set name, profession, title, fur, glow colour
GROUPS = [
    ("1.7.0_sets_tailoring", "Tailoring", (60, 40, 110), (16, 10, 34), [
        ("moonreg", "Mooncloth Regalia", "Tailoring", "Moonweaver", "fur_snow", (170, 200, 255)),
        ("felweave", "Felweave Shroud", "Tailoring", "Felweaver", "fur_midnight", (90, 255, 90)),
        ("spellfire", "Spellfire", "Tailoring", "Spellfire Savant", "fur_ginger", (255, 120, 60)),
    ]),
    ("1.7.0_sets_smithing_leather", "Blacksmithing and Leatherworking", (70, 34, 22), (20, 10, 8), [
        ("sulfuron", "Sulfuron Forgemaster", "Blacksmithing", "Forgemaster", "fur_ember", (255, 110, 30)),
        ("darkiron", "Dark Iron Bulwark", "Blacksmithing", "Dark Iron Warden", "fur_silver", (255, 80, 60)),
        ("blackscale", "Black Dragonscale", "Leatherworking", "Dragonscale Stalker", "fur_midnight", (255, 70, 40)),
        ("devilsaur", "Devilsaur Hunter", "Leatherworking", "Devilsaur Hunter", "fur_ginger", (120, 220, 90)),
    ]),
    ("1.7.0_sets_gathering", "Herbalism, Fishing, Cooking and First Aid", (30, 70, 60), (8, 22, 20), [
        ("lotus", "Lotus Bloom", "Herbalism", "Lotus Keeper", "fur_cream", (255, 150, 220)),
        ("pinchy", "Pinchy's Wish", "Fishing", "Angler of Legend", "fur_silver", (80, 200, 255)),
        ("feast", "Feast of the Ages", "Cooking", "Master Chef", "fur_ginger", (255, 200, 90)),
        ("medic", "Field Medic", "First Aid", "Field Medic", "fur_snow", (255, 90, 90)),
    ]),
]


def gradient(top, bottom):
    im = Image.new("RGB", (CW, CH))
    d = ImageDraw.Draw(im)
    for y in range(CH):
        t = y / (CH - 1)
        d.line([(0, y), (CW, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
    return im.convert("RGBA")


def text(d, xy, s, size, fill, title=False, maxw=None):
    f = font(size, title=title)
    while maxw and size > 20 and d.textlength(s, font=f) > maxw:
        size -= 2; f = font(size, title=title)
    for dx, dy in ((4, 4), (0, 4), (4, 0)):
        d.text((xy[0] + dx, xy[1] + dy), s, font=f, fill=(10, 6, 4), anchor="mm")
    d.text(xy, s, font=f, fill=fill, anchor="mm")


def border(im):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([3, 3, CW - 4, CH - 4], 40, outline=(210, 165, 90), width=7)
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, CW - 1, CH - 1], 42, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im, (0, 0), m)
    return out


def showcase(heading, top, bottom, sets):
    im = gradient(top, bottom)
    n = len(sets)
    slot = CW / n
    cat_h = 760 if n == 3 else 640
    for i, (key, name, prof, title, fur, col) in enumerate(sets):
        cx = slot * (i + 0.5)
        glow(im, (cx - slot * 0.42, CH * 0.18, cx + slot * 0.42, CH * 0.92), col, 90, 0.55)
        shadow(im, cx, CH - 250, cat_h * 0.62)
        paste(im, cat_image(set_look(key, fur), cat_h), cx, CH - 246)
    d = ImageDraw.Draw(im)
    text(d, (CW / 2, 92), heading, 84, (255, 226, 150), title=True)
    for i, (key, name, prof, title, fur, col) in enumerate(sets):
        cx = slot * (i + 0.5)
        text(d, (cx, CH - 188), name, 56 if n == 3 else 50, (255, 240, 210), title=True, maxw=slot * 0.92)
        text(d, (cx, CH - 122), prof, 40, tuple(min(255, c + 60) for c in col))
        text(d, (cx, CH - 68), "Title: " + title, 36, (230, 230, 230))
    for x, y in ((90, 60), (CW - 150, 80), (CW / 2 - 520, 150), (CW / 2 + 470, 140)):
        im.alpha_composite(sprite("sparkle", 60, (255, 240, 200)), (int(x), int(y)))
    return border(im)


def promo():
    """all 11 sets together under a big banner"""
    allsets = [x for g in GROUPS for x in g[4]]
    im = gradient((44, 24, 78), (10, 6, 20))
    glow(im, (CW * 0.15, -300, CW * 0.85, 520), (255, 190, 90), 140, 0.45)
    rows = [allsets[:6], allsets[6:]]
    cat_h = 400
    tops = [CH * 0.60, CH * 0.95]
    for r, row in enumerate(rows):
        slot = CW / len(row) if r == 0 else CW / 6
        x0 = 0 if r == 0 else slot / 2
        for i, (key, name, prof, title, fur, col) in enumerate(row):
            cx = x0 + slot * (i + 0.5)
            bottom = tops[r] - 70
            glow(im, (cx - 190, bottom - cat_h - 40, cx + 190, bottom + 40), col, 70, 0.6)
            shadow(im, cx, bottom + 4, cat_h * 0.62)
            paste(im, cat_image(set_look(key, fur), cat_h), cx, bottom)
    d = ImageDraw.Draw(im)
    for r, row in enumerate(rows):
        slot = CW / len(row) if r == 0 else CW / 6
        x0 = 0 if r == 0 else slot / 2
        for i, (key, name, prof, title, fur, col) in enumerate(row):
            cx = x0 + slot * (i + 0.5)
            text(d, (cx, tops[r] - 34), name, 38, (255, 240, 210), title=True, maxw=slot * 0.94)
    text(d, (CW / 2, 120), "11 NEW LEGENDARY SETS", 130, (255, 214, 110), title=True)
    text(d, (CW / 2, 228), "TapCatForever 1.7  \u2022  Professions 2.0  \u2022  Craft them, wear them, earn their titles", 46, (240, 230, 255))
    for x, y, sz in ((110, 70, 70), (CW - 190, 90, 64), (CW / 2 - 40, 20, 40)):
        im.alpha_composite(sprite("sparkle", sz, (255, 240, 200)), (int(x), int(y)))
    return border(im)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    promo().resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "1.7.0_new_sets.png"), optimize=True)
    print("wrote patch-notes/media/1.7.0_new_sets.png")
    if os.environ.get("PROMO_ONLY"): sys.exit(0)
    for fname, heading, top, bottom, sets in GROUPS:
        im = showcase(heading, top, bottom, sets)
        im.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, fname + ".png"), optimize=True)
        print("wrote patch-notes/media/%s.png" % fname)
