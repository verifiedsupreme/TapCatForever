#!/usr/bin/env python3
"""Pictures beside the features on the CurseForge page (media/card_*.png, 420x260): small
illustrations made from the addon's own art (the cartoon cat in different looks, the zone
backgrounds, the casino symbols, tap effects) and WoW icons, so they don't repeat the gallery
screenshots (media/promo_*.png, tools/make_promo.py).
usage: make_cards.py <font dir with Cinzel.ttf and Lato-Bold.ttf>"""
import math, os, random, sys, urllib.request, io
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
FONTS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "fonts")
ICONS = os.path.join(os.environ.get("TMPDIR", "/tmp"), "tcf_icons")
W, H, S = 420, 260, 2          # drawn at twice the size, then scaled down
CW, CH = W * S, H * S
random.seed(7)


def font(size, title=False):
    if title:
        f = ImageFont.truetype(os.path.join(FONTS, "Cinzel.ttf"), size)
        try: f.set_variation_by_name("Bold")
        except Exception: pass
        return f
    return ImageFont.truetype(os.path.join(FONTS, "Lato-Bold.ttf"), size)


def tga(name):
    return Image.open(os.path.join(ROOT, "Art", name + ".tga")).convert("RGBA")


def icon(name, size):
    """a WoW icon (cached), with its border trimmed and rounded corners"""
    os.makedirs(ICONS, exist_ok=True)
    p = os.path.join(ICONS, name.lower() + ".jpg")
    if not os.path.exists(p):
        data = urllib.request.urlopen("https://wow.zamimg.com/images/wow/icons/large/%s.jpg" % name.lower(), timeout=20).read()
        open(p, "wb").write(data)
    im = Image.open(p).convert("RGBA")
    w, h = im.size
    im = im.crop((int(w * 0.07), int(h * 0.07), int(w * 0.93), int(h * 0.93))).resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], size // 6, fill=255)
    im.putalpha(m)
    return im


_render = None
def cat_image(look, height):
    """the cartoon cat drawn by the addon's own code, transparent, cropped, scaled to height"""
    global _render
    from catrender import CatRender
    import numpy as np
    if _render is None: _render = CatRender()
    r = _render
    c = r.cat(size=420)
    r.apply(c, look)
    a = r.paint(c, bg=(0, 0, 0)); b = r.paint(c, bg=(1, 1, 1))
    A = np.asarray(a).astype(np.float32) / 255; B = np.asarray(b).astype(np.float32) / 255
    alpha = np.clip(1 - (B - A).mean(axis=2), 0, 1)
    rgb = np.where(alpha[..., None] > 1e-3, A / np.maximum(alpha[..., None], 1e-3), 0)
    out = Image.fromarray((np.concatenate([np.clip(rgb, 0, 1), alpha[..., None]], axis=2) * 255).astype("uint8"), "RGBA")
    out = out.crop(out.getbbox())
    return out.resize((round(out.width * height / out.height), height), Image.LANCZOS)


def set_look(key, fur="fur_ginger"):
    """every piece of a dungeon set, worn"""
    global _render
    if _render is None: cat_image({}, 10)
    T = _render.TCF
    look = {"fur": fur}
    for it in T.ITEM_LIST.values():
        if it.id and str(it.id).startswith("set_" + key + "_"):
            look[it.slot] = it.id
    return look


def bg_gradient(top, bottom):
    im = Image.new("RGB", (CW, CH))
    d = ImageDraw.Draw(im)
    for y in range(CH):
        t = y / (CH - 1)
        d.line([(0, y), (CW, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
    return im.convert("RGBA")


def glow(im, box, color, blur=60, strength=0.8):
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse(box, fill=color + (int(255 * strength),))
    g = g.filter(ImageFilter.GaussianBlur(blur))
    im.alpha_composite(g)


def zone(key):
    im = tga("v/bg_" + key).convert("RGB")
    w, h = im.size
    s = max(CW / w, CH / h)
    im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    x = (im.width - CW) // 2; y = im.height - CH
    return im.crop((x, y, x + CW, y + CH)).convert("RGBA")


def paste(im, sprite, cx, bottom):
    im.alpha_composite(sprite, (int(cx - sprite.width / 2), int(bottom - sprite.height)))


def shadow(im, cx, y, w):
    s = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(s).ellipse([cx - w / 2, y - w * 0.09, cx + w / 2, y + w * 0.09], fill=(0, 0, 0, 120))
    im.alpha_composite(s.filter(ImageFilter.GaussianBlur(8)))


def sprite(name, size, color=None, angle=0):
    sp = tga("v/t_" + name)
    if color:
        r, g, b, a = sp.split()
        sp = Image.merge("RGBA", (r.point(lambda v: v * color[0] // 255), g.point(lambda v: v * color[1] // 255),
                                  b.point(lambda v: v * color[2] // 255), a))
    sp = sp.resize((size, size), Image.LANCZOS)
    return sp.rotate(angle, resample=Image.BICUBIC, expand=True) if angle else sp


def label(im, text, xy, size=40, fill=(255, 226, 150)):
    d = ImageDraw.Draw(im)
    f = font(size, title=True)
    for dx, dy in ((3, 3), (0, 3), (3, 0)):
        d.text((xy[0] + dx, xy[1] + dy), text, font=f, fill=(20, 12, 8))
    d.text(xy, text, font=f, fill=fill)


def keycap(im, x, y, ch, pressed=False):
    d = ImageDraw.Draw(im)
    s = 92
    off = 8 if pressed else 0
    d.rounded_rectangle([x, y + 10, x + s, y + s + 10], 16, fill=(30, 26, 40))
    d.rounded_rectangle([x, y + off, x + s, y + s + off - 4], 16, fill=(236, 232, 246) if not pressed else (255, 214, 120),
                        outline=(60, 50, 80), width=4)
    d.text((x + s / 2, y + off + s / 2 - 4), ch, font=font(52), fill=(50, 40, 70), anchor="mm")


def frame_border(im):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 2, CW - 3, CH - 3], 26, outline=(210, 165, 90), width=5)
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, CW - 1, CH - 1], 28, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im, (0, 0), m)
    return out


# ------------------------------------------------------------------------------ the cards
def card_cat():
    im = bg_gradient((54, 40, 92), (22, 18, 40))
    glow(im, (CW * 0.25, CH * 0.05, CW * 0.75, CH * 1.1), (150, 110, 220), 70, 0.7)
    shadow(im, CW / 2, CH - 34, 300)
    paste(im, cat_image({"fur": "fur_ginger"}, 400), CW / 2, CH - 30)
    keycap(im, 60, CH - 170, "A", pressed=True)
    keycap(im, CW - 152, CH - 170, "D")
    for name, col, x, y, s, a in (("heart", (255, 110, 150), 250, 70, 64, -15), ("star", (255, 220, 90), 560, 40, 58, 10),
                                  ("heart", (255, 130, 170), 620, 150, 46, 20), ("sparkle", (180, 220, 255), 200, 190, 48, 0),
                                  ("note", (200, 170, 255), 660, 260, 44, -10), ("star", (255, 230, 120), 150, 40, 40, 0)):
        im.alpha_composite(sprite(name, s, col, a), (x, y))
    return im


def card_adventure():
    im = zone("mc")
    glow(im, (CW * 0.45, -100, CW * 1.2, CH * 0.8), (255, 120, 40), 80, 0.35)
    shadow(im, 230, CH - 34, 260)
    paste(im, cat_image(set_look("mc", "fur_ember"), 380), 230, CH - 28)
    label(im, "Molten Core", (CW - 380, 34), 46)
    d = ImageDraw.Draw(im)
    f = font(30)
    for i, (t, c) in enumerate((("Level 1 to 60", (255, 255, 255)), ("28 zones", (255, 220, 120)), ("Real bosses and loot", (255, 180, 90)))):
        y = 120 + i * 56
        tw = d.textlength(t, font=f)
        d.rounded_rectangle([CW - 380, y, CW - 380 + tw + 36, y + 44], 22, fill=(30, 14, 10, 220), outline=(200, 110, 50), width=3)
        d.text((CW - 362, y + 22), t, font=f, fill=c, anchor="lm")
    return im


def card_sets():
    im = bg_gradient((70, 36, 70), (20, 12, 26))
    glow(im, (60, 40, 360, 520), (255, 120, 60), 60, 0.45)
    glow(im, (300, 30, 560, 520), (120, 200, 255), 60, 0.45)
    glow(im, (520, 40, 820, 520), (200, 120, 255), 60, 0.45)
    for cx, key, fur, h in ((200, "mc", "fur_ember", 330), (CW / 2, "scholo", "fur_midnight", 370), (CW - 200, "st", "fur_silver", 330)):
        shadow(im, cx, CH - 34, 220)
        paste(im, cat_image(set_look(key, fur), h), cx, CH - 30)
    for x, y, s in ((90, 50, 40), (440, 30, 36), (760, 70, 44), (330, 120, 30), (620, 140, 32)):
        im.alpha_composite(sprite("sparkle", s, (255, 240, 200)), (x, y))
    return im


def icon_tile(im, name, x, y, size, ring=(230, 190, 110)):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x - 6, y - 6, x + size + 6, y + size + 6], size // 5, fill=(16, 12, 10), outline=ring, width=4)
    im.alpha_composite(icon(name, size), (x, y))


def card_business():
    im = bg_gradient((60, 44, 30), (24, 18, 14))
    glow(im, (CW * 0.4, -60, CW * 1.1, CH), (255, 200, 90), 80, 0.35)
    names = ["INV_Ore_Copper_01", "INV_Ore_Iron_01", "INV_Ore_Thorium_02", "INV_Misc_LeatherScrap_03",
             "INV_Misc_LeatherScrap_02", "INV_Fabric_Linen_01", "INV_Fabric_Silk_01", "INV_Fabric_Mageweave_01", "INV_Fabric_Felcloth_Ebon"]
    for i, n in enumerate(names):
        r, c = divmod(i, 3)
        icon_tile(im, n, 60 + c * 120, 46 + r * 140, 96)
    # a pile of gold
    for i in range(14):
        x = 480 + random.randint(0, 120); y = CH - 70 - random.randint(0, 50)
        d = ImageDraw.Draw(im)
        d.ellipse([x, y, x + 70, y + 30], fill=(250, 200, 60), outline=(150, 100, 20), width=3)
    shadow(im, 680, CH - 30, 220)
    paste(im, cat_image({"fur": "fur_golden"}, 300), 690, CH - 26)
    label(im, "Trade Gold", (430, 40), 44)
    return im


def card_garden():
    im = bg_gradient((120, 190, 240), (180, 220, 160))
    d = ImageDraw.Draw(im)
    glow(im, (CW - 260, -120, CW + 80, 200), (255, 240, 160), 50, 0.9)
    # three rows of soil, herbs growing in them
    herbs = ["INV_Misc_Flower_02", "INV_Misc_Herb_10", "INV_Misc_Herb_07", "INV_Jewelry_Talisman_03", "INV_Misc_Herb_03",
             "INV_Misc_Herb_18", "INV_Misc_Herb_17", "INV_Misc_Herb_19", "INV_Misc_Herb_DreamFoil", "INV_Misc_Herb_IceCap",
             "INV_Misc_Herb_MountainSilverSage", "INV_Misc_Herb_BlackLotus"]
    for row in range(3):
        y = 230 + row * 100
        d.rounded_rectangle([30 + row * 20, y + 40, 560 - row * 10, y + 92], 26, fill=(112, 74, 44), outline=(70, 44, 24), width=4)
        for k in range(4):
            n = herbs[row * 4 + k]
            x = 60 + row * 20 + k * 124
            icon_tile(im, n, x, y - 10, 74, ring=(120, 200, 90) if n != "INV_Misc_Herb_BlackLotus" else (190, 120, 255))
    shadow(im, 700, CH - 30, 220)
    paste(im, cat_image({"fur": "fur_cream", "head": "fishing_hat"} if False else {"fur": "fur_cream"}, 300), 700, CH - 26)
    label(im, "26 herbs", (600, 40), 46, fill=(255, 255, 235))
    return im


def card_potions():
    im = bg_gradient((34, 26, 56), (12, 10, 22))
    d = ImageDraw.Draw(im)
    pots = [("INV_Potion_15", (255, 120, 80)), ("INV_Potion_43", (200, 120, 255)), ("INV_Potion_95", (120, 230, 120)),
            ("INV_Potion_08", (255, 170, 90)), ("INV_Potion_62", (255, 90, 90)), ("INV_Potion_41", (140, 150, 255)), ("INV_Potion_97", (120, 220, 255))]
    # a shelf
    d.rounded_rectangle([20, 330, CW - 20, 356], 8, fill=(110, 70, 40), outline=(60, 36, 20), width=3)
    d.rounded_rectangle([20, 160, CW - 20, 186], 8, fill=(110, 70, 40), outline=(60, 36, 20), width=3)
    for i, (n, c) in enumerate(pots):
        top = i % 2 == 1                        # three on the top shelf, four on the bottom one
        k = i // 2
        x = (180 + k * 200) if top else (70 + k * 200)
        yb = 160 if top else 330
        glow(im, (x - 30, yb - 130, x + 130, yb + 20), c, 30, 0.55)
        icon_tile(im, n, x, yb - 106, 96, ring=(220, 190, 140))
    label(im, "Elixirs and Flasks", (60, CH - 130), 44)
    for x, y in ((700, 60), (120, 40), (520, 400)):
        im.alpha_composite(sprite("sparkle", 40, (255, 240, 200)), (x, y))
    return im


def card_casino():
    im = zone("dm") if False else bg_gradient((120, 20, 40), (40, 8, 18))
    glow(im, (CW * 0.2, -80, CW * 0.8, CH * 0.9), (255, 190, 90), 80, 0.5)
    d = ImageDraw.Draw(im)
    # three reels with cat-themed symbols
    syms = [n for n in ("sym_cat", "sym_diamond", "sym_cat") ]
    reel = 170
    x0 = (CW - 3 * reel - 40) // 2
    for i in range(3):
        x = x0 + i * (reel + 20)
        d.rounded_rectangle([x, 70, x + reel, 70 + reel + 40], 24, fill=(250, 240, 220), outline=(90, 30, 40), width=6)
    available = sorted(f[:-4] for f in os.listdir(os.path.join(ROOT, "Art", "casino")) if f.startswith("sym_"))
    pick = [n for n in ("sym_cat", "sym_cat", "sym_cat") if n in available] or available[:3]
    if len(pick) < 3: pick = (pick * 3)[:3]
    for i, n in enumerate(pick):
        s = tga("casino/" + n).resize((140, 140), Image.LANCZOS)
        im.alpha_composite(s, (x0 + i * (reel + 20) + 15, 90))
    label(im, "JACKPOT", (CW // 2 - 150, CH - 150), 64)
    for n, x, y, a in (("suit_hearts", 40, 40, -15), ("suit_spades", 760, 50, 15), ("suit_diamonds", 60, 330, 10), ("suit_clubs", 750, 340, -10)):
        im.alpha_composite(tga("casino/" + n).resize((70, 70), Image.LANCZOS).rotate(a, expand=True, resample=Image.BICUBIC), (x, y))
    return im


def card_friends():
    im = zone("elwynn")
    glow(im, (0, CH * 0.5, CW, CH * 1.4), (255, 230, 180), 60, 0.35)
    looks = [{"fur": "fur_ginger"}, {"fur": "fur_silver"}, {"fur": "fur_midnight"}, {"fur": "fur_cream"}, {"fur": "fur_lilac"}]
    xs = [110, 270, 430, 590, 750]
    hs = [210, 230, 260, 230, 210]
    for x, lk, h in zip(xs, looks, hs):
        shadow(im, x, CH - 30, 150)
        paste(im, cat_image(lk, h), x, CH - 26)
    for x, y, s in ((190, 60, 56), (370, 30, 46), (520, 70, 52), (660, 40, 44)):
        im.alpha_composite(sprite("heart", s, (255, 110, 150)), (x, y))
    d = ImageDraw.Draw(im)
    f = font(38)
    t = "+50% taps"
    tw = d.textlength(t, font=f)
    d.rounded_rectangle([CW - tw - 70, 26, CW - 26, 86], 30, fill=(20, 60, 20, 230), outline=(120, 230, 120), width=4)
    d.text((CW - 48 - tw / 2, 56), t, font=f, fill=(200, 255, 200), anchor="mm")
    return im


def mini_window(im, box, cat_h, title=True):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, 18, fill=(20, 16, 30), outline=(150, 130, 110), width=5)
    d.rounded_rectangle([x0 + 10, y0 + 10, x1 - 10, y0 + 44], 10, fill=(60, 30, 30))
    if title: d.text((x0 + 24, y0 + 27), "TapCatForever", font=font(22), fill=(255, 200, 90), anchor="lm")
    # tab buttons
    bw = (x1 - x0 - 40) / 4
    for i in range(4):
        bx = x0 + 14 + i * (bw + 4)
        d.rounded_rectangle([bx, y0 + 52, bx + bw, y0 + 76], 6, fill=(160, 40, 30) if i else (210, 80, 40))
    return (x0 + x1) / 2


def card_window():
    im = bg_gradient((40, 46, 70), (16, 18, 30))
    glow(im, (CW * 0.1, 0, CW * 0.9, CH), (110, 130, 220), 80, 0.4)
    cx = mini_window(im, (40, 40, 560, 480), 0)
    paste(im, cat_image(set_look("sm", "fur_snow"), 270), 200, 462)
    d = ImageDraw.Draw(im)
    for i in range(6):
        y = 100 + i * 60
        d.rounded_rectangle([370, y, 540, y + 44], 8, fill=(40, 34, 56), outline=(90, 80, 120), width=2)
    # the phone view
    px0, py0, px1, py1 = 610, 110, 790, 470
    d.rounded_rectangle([px0, py0, px1, py1], 30, fill=(10, 10, 14), outline=(180, 180, 200), width=5)
    d.rounded_rectangle([px0 + 12, py0 + 30, px1 - 12, py1 - 30], 14, fill=(26, 20, 36))
    paste(im, cat_image({"fur": "fur_ginger"}, 150), (px0 + px1) / 2, py0 + 200)
    for i in range(2):
        for j in range(2):
            bx = px0 + 26 + j * 70; by = py0 + 230 + i * 70
            d.ellipse([bx, by, bx + 56, by + 56], fill=(180, 50, 40), outline=(255, 200, 120), width=3)
    return im


CARDS = [("card_cat", card_cat), ("card_adventure", card_adventure), ("card_sets", card_sets), ("card_business", card_business),
         ("card_garden", card_garden), ("card_potions", card_potions), ("card_casino", card_casino),
         ("card_friends", card_friends), ("card_window", card_window)]

if __name__ == "__main__":
    only = os.environ.get("ONLY")
    for name, fn in CARDS:
        if only and only not in name: continue
        im = frame_border(fn())
        im.resize((W, H), Image.LANCZOS).save(os.path.join(ROOT, "media", name + ".png"), optimize=True)
        print("wrote media/%s.png" % name)
