#!/usr/bin/env python3
"""CurseForge gallery images (media/promo_*.png): a dark card with a small label, a title, a line of
text and a few bullet points on the left, and a framed in-game picture on the right.
Pictures come from media/feat_*.png (window renders cropped to one feature).
Fonts (SIL Open Font License, from github.com/google/fonts): Cinzel for titles, Lato for text.
usage: make_promo.py <font dir with Cinzel.ttf, Lato-Regular.ttf, Lato-Bold.ttf>"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA = os.path.join(ROOT, "media")
FONTS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "tools", "fonts")
W, H = 1800, 880

GOLD = (214, 168, 92)
CREAM = (240, 226, 200)
GREY = (176, 168, 156)
LIGHT = (232, 226, 216)

CARDS = [
    ("promo_1_cat", "feat_cat", "Your companion", "A cat for every key",
     "A little cartoon cat sits on your screen and taps its paws along with everything you do.",
     ["Taps along with every key and spell", "A cat for each class, level 1 to 60",
      "Pet it 100 times in a row: Happy Purrs", "27 pet effects to unlock"]),
    ("promo_2_sets", "feat_sets", "Cosmetics", "Dress it up",
     "Hats, capes, skins and animated dungeon sets, plus the real gear your cat wears.",
     ["Hundreds of cosmetics to collect", "Animated sets: fire, frost and stars",
      "Shift-click anything to try it on", "Rare skins from the biggest bosses"]),
    ("promo_3_garden", "feat_garden", "Herbalism", "Grow a garden",
     "Plant real Classic herbs that grow while you play, even while you're offline.",
     ["26 herbs from Peacebloom to Icecap", "A different seed in every plot",
      "Train Bramble the gardener to Master", "Rare Swiftthistle, Wildvine, Black Lotus"]),
    ("promo_4_potions", "feat_potions", "Alchemy", "Brew potions",
     "Turn your herbs into classic elixirs and flasks, then drink them for buffs.",
     ["17 potions, elixirs and flasks", "More damage, health, XP or gold",
      "Stacks with your Well Fed food", "Brewing raises your Herbalism"]),
    ("promo_5_casino", "feat_casino", "TapCat Casino", "Try your luck",
     "Spend your TapCoins on cat-themed games against the house cat or your friends.",
     ["Lucky Paws slots and blackjack", "Death roll a friend in the tavern",
      "Rock paper scissors, best of 1, 3 or 5", "Fair and in the open, just for fun"]),
    ("promo_6_friends", "feat_friends", "Multiplayer", "Better with friends",
     "Group up with friends who have the addon and your cats play together.",
     ["Your taps count up to 50% more", "Party expeditions and cat profiles",
      "A realm leaderboard, opt in", "Challenge friends in the casino"]),
    ("promo_7_window", "feat_window", "Your window", "Your way",
     "Everything about your cat in one window, sized the way you like it.",
     ["Gear, Adventure, Professions and more", "Fold the character panel away",
      "A phone-sized view with big buttons", "Drag the corner to resize"]),
]


def font(name, size, bold=False):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if name.startswith("Cinzel"):
        try:
            f.set_variation_by_name("Bold" if bold else "SemiBold")
        except Exception:
            pass
    return f


def background():
    # warm dark brown, lighter at the top left, with a soft vignette
    bg = Image.new("RGB", (W, H), (18, 14, 11))
    glow = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(glow)
    d.ellipse([-500, -600, 1300, 900], fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(260))
    warm = Image.new("RGB", (W, H), (52, 38, 26))
    bg = Image.composite(warm, bg, glow)
    d = ImageDraw.Draw(bg)
    d.rectangle([0, 0, W - 1, H - 1], outline=(70, 58, 46), width=2)
    return bg


def rounded_mask(size, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], r, fill=255)
    return m


def frame(bg, box, pic):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    # drop shadow
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).rounded_rectangle([x0 + 10, y0 + 18, x1 + 10, y1 + 18], 40, fill=170)
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    bg.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), sh)
    # bronze frame: a vertical gradient, darker edges
    fr = Image.new("RGB", (w, h))
    fd = ImageDraw.Draw(fr)
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(a + (b - a) * t) for a, b in zip((196, 146, 82), (120, 80, 40)))
        fd.line([(0, y), (w, y)], fill=c)
    bg.paste(fr, (x0, y0), rounded_mask((w, h), 40))
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle([x0, y0, x1, y1], 40, outline=(236, 196, 128), width=3)
    b = 26
    inner = [x0 + b, y0 + b, x1 - b, y1 - b]
    d.rounded_rectangle(inner, 26, fill=(22, 18, 15), outline=(70, 46, 24), width=4)
    # screws in the corners
    for cx, cy in ((x0 + 14, y0 + 14), (x1 - 14, y0 + 14), (x0 + 14, y1 - 14), (x1 - 14, y1 - 14)):
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(60, 40, 22), outline=(230, 190, 120), width=2)
    # the picture, fitted inside with a margin, rounded corners
    iw, ih = inner[2] - inner[0] - 28, inner[3] - inner[1] - 28
    s = min(iw / pic.width, ih / pic.height)
    pw, ph = int(pic.width * s), int(pic.height * s)
    p = pic.resize((pw, ph), Image.LANCZOS)
    px = inner[0] + 14 + (iw - pw) // 2
    py = inner[1] + 14 + (ih - ph) // 2
    bg.paste(p, (px, py), rounded_mask((pw, ph), 14))
    d.rounded_rectangle([px, py, px + pw - 1, py + ph - 1], 14, outline=(96, 74, 50), width=2)


def wrap(d, text, f, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= width: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def card(out, pic_name, label, title, blurb, bullets, logo):
    bg = background()
    d = ImageDraw.Draw(bg)
    X, TW = 96, 700
    # the label: the addon's logo in a small box, then the label in gold small capitals
    lb = logo.resize((60, 60), Image.LANCZOS)
    d.rounded_rectangle([X - 4, 92, X + 64, 160], 8, fill=(40, 30, 22), outline=(150, 112, 62), width=2)
    bg.paste(lb, (X, 96), lb)
    d.text((X + 88, 126), label.upper(), font=font("Cinzel.ttf", 30), fill=GOLD, anchor="lm")
    d.line([(X - 4, 196), (X + 380, 196)], fill=(150, 112, 62), width=3)
    # the title
    f_title = font("Cinzel.ttf", 76, bold=True)
    size = 76
    while d.textlength(title, font=f_title) > TW and size > 50:
        size -= 2; f_title = font("Cinzel.ttf", size, bold=True)
    d.text((X, 290), title, font=f_title, fill=CREAM, anchor="ls")
    # the line of text
    f_body = font("Lato-Regular.ttf", 30)
    y = 350
    for ln in wrap(d, blurb, f_body, TW):
        d.text((X, y), ln, font=f_body, fill=GREY, anchor="ls"); y += 42
    # the bullet points, gold diamonds
    f_b = font("Lato-Bold.ttf", 30)
    y += 36
    for b in bullets:
        cy = y - 11
        d.polygon([(X + 10, cy - 10), (X + 20, cy), (X + 10, cy + 10), (X, cy)], fill=GOLD)
        d.text((X + 40, y), b, font=f_b, fill=LIGHT, anchor="ls")
        y += 56
    # the picture
    pic = Image.open(os.path.join(MEDIA, pic_name + ".png")).convert("RGB")
    frame(bg, (880, 70, 1720, 810), pic)
    bg.save(os.path.join(MEDIA, out + ".png"), optimize=True)
    print("wrote media/%s.png" % out)


if __name__ == "__main__":
    logo = Image.open(os.path.join(MEDIA, "logo_small.png")).convert("RGBA")
    for c in CARDS:
        card(*c, logo)
