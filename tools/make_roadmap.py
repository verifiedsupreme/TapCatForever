#!/usr/bin/env python3
"""Pictures for ROADMAP.md (media/roadmap_*.png, 420x260): what's coming next, drawn like the
CurseForge feature cards (tools/make_cards.py) from the addon's own cat and WoW icons.
usage: make_roadmap.py <font dir with Cinzel.ttf and Lato-Bold.ttf>"""
import os, random, sys
from PIL import Image, ImageDraw, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_cards as mc                       # reads the font dir from sys.argv[1] too
from make_cards import (CW, CH, W, H, ROOT, bg_gradient, glow, zone, paste, shadow, sprite, label, icon,
                        icon_tile, cat_image, set_look, frame_border, mini_window, font)

random.seed(11)
RARITY = {"common": (230, 230, 230), "uncommon": (30, 255, 0), "rare": (0, 112, 221), "epic": (163, 53, 238),
          "legendary": (255, 128, 0)}


def tag(im, text, xy, fill=(40, 24, 10, 235), ring=(230, 170, 70), color=(255, 226, 150), size=30, anchor="l"):
    d = ImageDraw.Draw(im)
    f = font(size)
    tw = d.textlength(text, font=f)
    x, y = xy
    if anchor == "c": x -= (tw + 36) / 2
    d.rounded_rectangle([x, y, x + tw + 36, y + size + 18], (size + 18) // 2, fill=fill, outline=ring, width=3)
    d.text((x + 18, y + (size + 18) / 2), text, font=f, fill=color, anchor="lm")


def coming(im, text):
    """a small corner ribbon: Next, Later or Idea"""
    cols = {"Next": ((30, 90, 40), (130, 230, 130)), "Later": ((40, 50, 100), (140, 170, 255)), "Idea": ((80, 40, 90), (220, 150, 255))}
    bg, fg = cols[text]
    d = ImageDraw.Draw(im)
    f = font(26)
    tw = d.textlength(text.upper(), font=f)
    x1 = CW - 28; x0 = x1 - tw - 36
    d.rounded_rectangle([x0, 24, x1, 68], 22, fill=bg + (235,), outline=fg, width=3)
    d.text(((x0 + x1) / 2, 46), text.upper(), font=f, fill=fg, anchor="mm")


def tint(im, color, amount=0.55):
    """recolour a sprite toward a colour (keeps its alpha)"""
    r, g, b, a = im.split()
    base = Image.merge("RGB", (r, g, b))
    over = Image.new("RGB", im.size, color)
    out = Image.blend(base, over, amount).convert("RGBA")
    out.putalpha(a)
    return out


# ------------------------------------------------------------------------------ the cards
def wow_model(display, height):
    """a render of a real WoW creature model (Wowhead's model viewer thumbnail for that display id),
    transparent, cropped and scaled to height: the cats the addon shows with SetDisplayInfo"""
    import urllib.request
    os.makedirs(mc.ICONS, exist_ok=True)
    p = os.path.join(mc.ICONS, "model_%d.webp" % display)
    if not os.path.exists(p):
        url = "https://wow.zamimg.com/modelviewer/live/webthumbs/npc/%d/%d.webp" % (display % 256, display)
        open(p, "wb").write(urllib.request.urlopen(url, timeout=20).read())
    im = Image.open(p).convert("RGBA")
    im = im.crop(im.getbbox())
    return im.resize((round(im.width * height / im.height), height), Image.LANCZOS)


def card_companions():
    im = zone("elwynn")
    shade = Image.new("RGBA", im.size, (10, 6, 20, 140)); im.alpha_composite(shade)
    glow(im, (CW * 0.28, CH * 0.25, CW * 0.72, CH * 1.05), (80, 255, 90), 70, 0.5)
    # your cat, and its companion: a real WoW Felsaber
    shadow(im, 150, CH - 34, 200)
    paste(im, cat_image({"fur": "fur_ginger"}, 260), 150, CH - 30)
    shadow(im, 400, CH - 34, 300)
    paste(im, ImageOps.mirror(wow_model(67575, 250)), 400, CH - 30)
    # cats you can buy (real WoW models) and their prices
    for i, (disp, price, ring) in enumerate(((5554, "5,000", (30, 255, 0)), (6080, "25,000", (0, 112, 221)),
                                             (21973, "100,000", (163, 53, 238)))):
        y = 88 + i * 124
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([CW - 330, y - 6, CW - 214, y + 110], 20, fill=(16, 12, 20, 220), outline=ring, width=4)
        paste(im, wow_model(disp, 96), CW - 272, y + 102)
        tag(im, price, (CW - 200, y + 30), size=28)
    label(im, "Companion Cats", (40, 30), 46)
    tag(im, "Real WoW cat models", (40, 96), size=26)
    coming(im, "Next")
    return im


def card_shop():
    im = bg_gradient((70, 24, 60), (18, 8, 22))
    glow(im, (CW * 0.15, -60, CW * 0.85, CH * 0.8), (255, 170, 60), 80, 0.45)
    d = ImageDraw.Draw(im)
    # the Heroic Cache reel: a strip of items, the winner in the middle
    items = [("INV_Sword_39", "rare"), ("INV_Helmet_08", "uncommon"), ("INV_Chest_Plate16", "epic"),
             ("INV_Staff_13", "legendary"), ("INV_Shield_06", "epic"), ("INV_Boots_Plate_06", "rare"), ("INV_Misc_Cape_18", "uncommon")]
    size, gap = 96, 18
    x0 = (CW - (len(items) * size + (len(items) - 1) * gap)) // 2
    y = 150
    d.rounded_rectangle([x0 - 24, y - 30, CW - x0 + 24, y + size + 30], 24, fill=(14, 8, 14), outline=(200, 150, 80), width=4)
    for i, (n, r) in enumerate(items):
        x = x0 + i * (size + gap)
        if r == "legendary":
            glow(im, (x - 50, y - 50, x + size + 50, y + size + 50), RARITY[r], 30, 0.8)
        icon_tile(im, n, x, y, size, ring=RARITY[r])
    mid = x0 + 3 * (size + gap) + size // 2
    d = ImageDraw.Draw(im)
    d.polygon([(mid - 18, y - 46), (mid + 18, y - 46), (mid, y - 20)], fill=(255, 220, 120))
    d.polygon([(mid - 18, y + size + 46), (mid + 18, y + size + 46), (mid, y + size + 20)], fill=(255, 220, 120))
    label(im, "Heroic Cache", (40, 30), 46)
    tag(im, "A snazzier Shop, new skins, more epics", (CW / 2, CH - 96), size=28, anchor="c")
    coming(im, "Next")
    return im


def card_duel():
    im = zone("arena") if os.path.exists(os.path.join(ROOT, "Art", "v", "bg_arena.tga")) else zone("st")
    shade = Image.new("RGBA", im.size, (20, 6, 6, 110)); im.alpha_composite(shade)
    glow(im, (CW * 0.3, CH * 0.1, CW * 0.7, CH * 0.9), (255, 90, 60), 70, 0.5)
    left = cat_image(set_look("mc", "fur_ember"), 300)
    right = ImageOps.mirror(cat_image(set_look("scholo", "fur_midnight"), 300))
    shadow(im, 220, CH - 34, 230); paste(im, left, 220, CH - 30)
    shadow(im, CW - 220, CH - 34, 230); paste(im, right, CW - 220, CH - 30)
    label(im, "VS", (CW / 2 - 50, CH / 2 - 60), 80, fill=(255, 200, 90))
    label(im, "Duel Mode", (40, 30), 46)
    coming(im, "Later")
    return im


def card_themes():
    im = bg_gradient((30, 34, 50), (12, 12, 20))
    glow(im, (0, 0, CW, CH), (120, 130, 200), 90, 0.3)
    d = ImageDraw.Draw(im)
    themes = [((120, 20, 20), (210, 160, 60), "INV_BannerPVP_01"),     # Horde
              ((20, 40, 110), (200, 200, 230), "INV_BannerPVP_02"),    # Alliance
              ((24, 24, 28), (120, 200, 255), None)]                   # sleek modern
    for i, (bar, ring, ico) in enumerate(themes):
        x0 = 50 + i * 260; y0 = 120 + (i % 2) * 30
        x1, y1 = x0 + 230, y0 + 300
        d.rounded_rectangle([x0, y0, x1, y1], 18, fill=(18, 16, 24), outline=ring, width=5)
        d.rounded_rectangle([x0 + 10, y0 + 10, x1 - 10, y0 + 44], 10, fill=bar)
        for k in range(3):
            d.rounded_rectangle([x0 + 18 + k * 68, y0 + 54, x0 + 78 + k * 68, y0 + 74], 6, fill=tuple(min(255, c + 40) for c in bar))
        if ico:
            icon_tile(im, ico, x0 + 75, y0 + 110, 80, ring=ring)
        else:
            paste(im, cat_image({"fur": "fur_silver"}, 150), (x0 + x1) / 2, y1 - 20)
        d = ImageDraw.Draw(im)
    label(im, "Window Themes", (40, 30), 46)
    coming(im, "Later")
    return im


def card_class():
    im = bg_gradient((44, 36, 28), (16, 12, 10))
    glow(im, (CW * 0.3, 0, CW * 0.7, CH), (255, 210, 120), 80, 0.35)
    classes = ["warrior", "paladin", "hunter", "rogue", "priest", "shaman", "mage", "warlock", "druid"]
    for i, c in enumerate(classes):
        r, k = divmod(i, 5)
        x = 50 + k * 92 + r * 46; y = 110 + r * 110
        icon_tile(im, "ClassIcon_" + c.capitalize(), x, y, 72)
    shadow(im, CW - 160, CH - 34, 200)
    paste(im, cat_image(set_look("st", "fur_silver"), 300), CW - 160, CH - 30)
    label(im, "Class Cosmetics", (40, 30), 46)
    coming(im, "Later")
    return im


def card_tavern():
    im = bg_gradient((70, 40, 20), (24, 14, 8))
    glow(im, (CW * 0.2, CH * 0.1, CW * 0.8, CH), (255, 170, 70), 80, 0.5)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([30, CH - 150, CW - 30, CH - 110], 10, fill=(110, 66, 34), outline=(60, 34, 16), width=4)  # the bar
    for i, n in enumerate(("INV_Drink_04", "INV_Misc_Dice_01", "INV_Misc_Coin_01", "INV_Drink_05")):
        icon_tile(im, n, 60 + i * 118, CH - 250, 84, ring=(220, 170, 90))
    shadow(im, CW - 150, CH - 34, 180)
    paste(im, cat_image({"fur": "fur_cream"}, 240), CW - 150, CH - 30)
    label(im, "The Tavern", (40, 30), 46)
    coming(im, "Idea")
    return im


def card_itemart():
    im = bg_gradient((26, 30, 44), (10, 12, 18))
    glow(im, (0, 0, CW, CH), (110, 150, 255), 90, 0.25)
    names = ["INV_Sword_04", "INV_Helmet_25", "INV_Shoulder_25", "INV_Chest_Cloth_17", "INV_Staff_08", "INV_Axe_09",
             "INV_Mace_01", "INV_Shield_04", "INV_Misc_Cape_06", "INV_Weapon_Bow_07"]
    for i, n in enumerate(names):
        r, k = divmod(i, 5)
        icon_tile(im, n, 46 + k * 104, 120 + r * 120, 80)
    shadow(im, CW - 150, CH - 34, 190)
    paste(im, cat_image(set_look("sm", "fur_snow"), 280), CW - 150, CH - 30)
    label(im, "Every Item, Drawn", (40, 30), 46)
    coming(im, "Idea")
    return im


def card_warlock():
    im = bg_gradient((40, 10, 40), (10, 4, 14))
    glow(im, (CW * 0.4, CH * 0.1, CW * 1.0, CH), (160, 60, 255), 80, 0.5)
    for i, n in enumerate(("Spell_Shadow_SummonImp", "Spell_Shadow_SummonVoidWalker", "Spell_Shadow_SummonSuccubus", "Spell_Shadow_SummonFelHunter")):
        icon_tile(im, n, 50 + i * 110, 150, 88, ring=(170, 90, 255))
    shadow(im, CW - 150, CH - 34, 190)
    paste(im, cat_image({"fur": "fur_midnight"}, 260), CW - 150, CH - 30)
    label(im, "Warlock Demons", (40, 30), 46)
    tag(im, "Tiny demons for Warlock cats", (50, CH - 110), size=26)
    coming(im, "Idea")
    return im


CARDS = [("roadmap_companions", card_companions), ("roadmap_shop", card_shop), ("roadmap_duel", card_duel),
         ("roadmap_themes", card_themes), ("roadmap_class", card_class), ("roadmap_tavern", card_tavern),
         ("roadmap_itemart", card_itemart), ("roadmap_warlock", card_warlock)]

if __name__ == "__main__":
    only = os.environ.get("ONLY")
    for name, fn in CARDS:
        if only and only not in name: continue
        im = frame_border(fn())
        im.resize((W, H), Image.LANCZOS).save(os.path.join(ROOT, "media", name + ".png"), optimize=True)
        print("wrote media/%s.png" % name)
