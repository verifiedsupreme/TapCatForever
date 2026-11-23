"""The picture tiles of the 1.6 What's new pop-up (News.lua): Art/news/<name>.tga, 256x128.

usage: python3 tools/make_news_art.py [--review DIR] [--preview OUT.png]

Three tiles come from screenshots of the addon (the slots jackpot, the three window layouts, the
animated dungeon sets). --review DIR (the review160 preview folder) crops them again into
tools/news_src/*.png; without it the crops already there are used. The other three are drawn here
from the addon's own art: the cat (tools/catrender.py), the Adventure backgrounds in Art/v and
WoW's skill colours.

Each tile is a 24-bit RLE TGA, 256x128 (power-of-two sides, under 100 KB). --preview writes a
sheet of all six for a look.
"""
import argparse, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
SRC = os.path.join(HERE, "news_src")
OUT = os.path.join(ROOT, "Art", "news")
W, H = 256, 128
S = 2  # drawn at twice the size, then scaled down

TILES = ["casino", "window", "sets", "professions", "farm", "party"]


def font(size, bold=True):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"):
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def crop_to(im, box, size=(W * S, H * S)):
    return im.convert("RGB").crop(box).resize(size, Image.LANCZOS)


def recrop(review):
    """screenshots -> tools/news_src/*.png (512x256)"""
    os.makedirs(SRC, exist_ok=True)
    # the slot machine with its jackpot and the pay table
    im = Image.open(os.path.join(review, "casino", "final_slots_jackpot.png"))
    crop_to(im, (40, 300, 1800, 1180)).save(os.path.join(SRC, "casino.png"))
    # the narrow and the compact window side by side
    im = Image.open(os.path.join(review, "window", "0_overview.png"))
    crop_to(im, (1940, 110, 4100, 1190)).save(os.path.join(SRC, "window.png"))
    # two dungeon sets (Molten Core and Scarlet Monastery), from the animated overview
    im = Image.open(os.path.join(review, "art", "sets_overview.gif")); im.seek(10)
    crop_to(im, (20, 16, 548, 280)).save(os.path.join(SRC, "sets.png"))


def tga(name):
    return Image.open(os.path.join(ROOT, "Art", name + ".tga")).convert("RGBA")


_render = None
def cat_image(look, size=300):
    """the cartoon cat on a transparent background, cropped to the cat"""
    global _render
    from catrender import CatRender
    import numpy as np
    if _render is None: _render = CatRender()
    r = _render
    cat = r.cat(size=size)
    r.apply(cat, look)
    a = r.paint(cat, bg=(0, 0, 0))
    b = r.paint(cat, bg=(1, 1, 1))
    A = np.asarray(a).astype(np.float32) / 255; B = np.asarray(b).astype(np.float32) / 255
    alpha = np.clip(1 - (B - A).mean(axis=2), 0, 1)
    rgb = np.where(alpha[..., None] > 1e-3, A / np.maximum(alpha[..., None], 1e-3), 0)
    out = Image.fromarray((np.concatenate([np.clip(rgb, 0, 1), alpha[..., None]], axis=2) * 255).astype("uint8"), "RGBA")
    return out.crop(out.getbbox())


def background(key, box=None):
    im = tga("v/bg_" + key).convert("RGB")
    w, h = im.size
    if box is None:
        # the lower middle, at 2:1
        ch = min(h, w // 2)
        box = (0, h - ch, w, h) if w // 2 >= ch else (0, 0, w, h)
        cw = ch * 2
        x0 = (w - cw) // 2
        box = (x0, h - ch, x0 + cw, h)
    return im.crop(box).resize((W * S, H * S), Image.LANCZOS)


def pill(d, xy, text, fill, size=26, color=(255, 255, 255)):
    f = font(size)
    x, y = xy
    tw = d.textlength(text, font=f)
    d.rounded_rectangle((x, y, x + tw + 28, y + size + 16), radius=(size + 16) // 2, fill=fill, outline=(40, 20, 10), width=3)
    d.text((x + 14, y + 6), text, font=f, fill=color)
    return x + tw + 28


def shadow_text(d, xy, text, f, fill=(255, 210, 80)):
    x, y = xy
    for dx, dy in ((2, 2), (-1, 2), (2, -1), (0, 3)):
        d.text((x + dx, y + dy), text, font=f, fill=(20, 10, 10))
    d.text((x, y), text, font=f, fill=fill)


def draw_professions():
    im = Image.new("RGB", (W * S, H * S), (30, 24, 40))
    d = ImageDraw.Draw(im)
    # a soft spotlight and the skill bar
    glow = Image.new("RGB", im.size, (0, 0, 0))
    ImageDraw.Draw(glow).ellipse((-60, -120, 380, 260), fill=(70, 55, 90))
    im = Image.blend(im, glow.filter(ImageFilter.GaussianBlur(60)), 0.6)
    d = ImageDraw.Draw(im)
    shadow_text(d, (22, 14), "Mining  87 / 300", font(30))
    d.rounded_rectangle((22, 58, 490, 76), radius=8, fill=(15, 10, 20))
    d.rounded_rectangle((22, 58, 22 + int(468 * 87 / 300), 76), radius=8, fill=(40, 150, 220))
    rows = [("Copper Vein", (255, 128, 64)), ("Tin Vein", (255, 220, 0)), ("Silver Vein", (64, 191, 64)), ("Iron Deposit", (128, 128, 128))]
    f = font(26)
    for i, (n, c) in enumerate(rows):
        y = 92 + i * 40
        d.rounded_rectangle((22, y, 360, y + 34), radius=8, fill=(45, 36, 58), outline=(80, 66, 100), width=2)
        d.ellipse((32, y + 8, 50, y + 26), fill=c)
        d.text((62, y + 2), n, font=f, fill=c)
    # the pickaxe-swinging cat on the right
    try:
        cat = cat_image({"fur": "fur_ginger"}, 260)
        cat.thumbnail((170, 170), Image.LANCZOS)
        im.paste(cat, (W * S - cat.width - 16, H * S - cat.height - 8), cat)
    except Exception as e:
        print("cat render skipped:", e)
    return im


def draw_farm():
    im = background("dm")
    im = Image.blend(im, Image.new("RGB", im.size, (0, 0, 0)), 0.15)
    try:
        cat = cat_image({"fur": "fur_ginger"}, 260)
        cat.thumbnail((150, 150), Image.LANCZOS)
        im.paste(cat, (26, H * S - cat.height - 14), cat)
    except Exception as e:
        print("cat render skipped:", e)
    # the boss: the pixel monster, big, with an orange name
    mob = tga("mob_shadow")
    mob = mob.crop(mob.getbbox()).resize((170, 170), Image.NEAREST)
    im.paste(mob, (W * S - 200, H * S - 186), mob)
    d = ImageDraw.Draw(im)
    shadow_text(d, (W * S - 250, 12), "Edwin VanCleef", font(26), fill=(255, 128, 0))
    d.rounded_rectangle((W * S - 250, 46, W * S - 30, 58), radius=6, fill=(20, 10, 10))
    d.rounded_rectangle((W * S - 250, 46, W * S - 110, 58), radius=6, fill=(210, 40, 40))
    pill(d, (180, 150), "Farm", (150, 25, 20), 30, (255, 210, 0))
    shadow_text(d, (180, 206), "0.2% a kill", font(28), fill=(255, 255, 255))
    return im


def draw_party():
    im = background("brd")
    im = Image.blend(im, Image.new("RGB", im.size, (0, 0, 0)), 0.2)
    looks = [{"skin": "skin_siamese"}, {"fur": "fur_ginger"}, {"skin": "skin_nightsaber"}]
    xs = [40, 186, 332]
    for x, look in zip(xs, looks):
        try:
            cat = cat_image(look, 260)
            cat.thumbnail((140, 140), Image.LANCZOS)
            im.paste(cat, (x, H * S - cat.height - 10), cat)
        except Exception as e:
            print("cat render skipped:", e)
    d = ImageDraw.Draw(im)
    shadow_text(d, (20, 12), "Blackrock Depths", font(30))
    shadow_text(d, (20, 50), "3 cats together", font(24), fill=(255, 255, 255))
    return im


def save_tga(im, name):
    os.makedirs(OUT, exist_ok=True)
    im = im.convert("RGB").resize((W, H), Image.LANCZOS)
    # a thin dark frame so tiles read as pictures
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=(10, 8, 14))
    p = os.path.join(OUT, name + ".tga")
    # the same 32-bit RLE, top-left-origin TGA as all the other art (PIL's own TGA writer picks
    # 24-bit and a bottom-left or top-left origin depending on the source picture)
    from make_art import write_tga
    write_tga(im.convert("RGBA"), p)
    return p, im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--review", help="the review160 preview folder: crop the screenshots again")
    ap.add_argument("--preview", help="write a sheet of all tiles here")
    a = ap.parse_args()
    if a.review: recrop(a.review)
    made = []
    for name in TILES:
        if name in ("casino", "window", "sets"):
            im = Image.open(os.path.join(SRC, name + ".png"))
        else:
            im = {"professions": draw_professions, "farm": draw_farm, "party": draw_party}[name]()
        p, small = save_tga(im, name)
        made.append(small)
        print("%s: %d bytes" % (os.path.relpath(p, ROOT), os.path.getsize(p)))
    if a.preview:
        sheet = Image.new("RGB", (3 * (W + 8) + 8, 2 * (H + 8) + 8), (20, 16, 26))
        for i, im in enumerate(made):
            sheet.paste(im, (8 + (i % 3) * (W + 8), 8 + (i // 3) * (H + 8)))
        sheet.save(a.preview)


if __name__ == "__main__":
    main()
