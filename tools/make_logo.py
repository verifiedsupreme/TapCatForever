"""The TapCatForever logo in the cartoon style: gold-and-red shield, the happy cat in a red
cape with a gold paw clasp, glowing paw taps and the gold title ribbon.
Uses the cat layers from build_vector_art.py (Art/v + VectorData.lua) and the Lilita One font.
usage: python3 tools/make_logo.py <work_dir>  -> Art/logo.tga (256), media/logo.png (1024)
"""
import os, re, subprocess, sys
from PIL import Image, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from make_art import write_tga
WORK = sys.argv[1]; os.makedirs(WORK, exist_ok=True)
INK = "#3b2620"; GOLD = "#f6c73e"; GOLD2 = "#e09a1c"; RED = "#b3161e"; RED2 = "#7d0b12"

SHIELD = "M 256 18 L 452 84 L 446 270 Q 436 404 256 494 Q 76 404 66 270 L 60 84 Z"
INNER = "M 256 46 L 426 104 L 420 268 Q 410 384 256 462 Q 102 384 92 268 L 86 104 Z"
back = ('<path d="%s" fill="%s" stroke="%s" stroke-width="9" stroke-linejoin="round"/>' % (SHIELD, GOLD, INK)
        + '<path d="%s" fill="%s" stroke="%s" stroke-width="5" stroke-linejoin="round"/>' % (INNER, RED, INK)
        + '<path d="M 256 46 L 426 104 L 420 268 Q 340 220 256 200 Z" fill="#ffffff" opacity=".08"/>'
        + '<path d="M 70 96 L 256 30 L 442 96" fill="none" stroke="#fff6c8" stroke-width="5" opacity=".7"/>')
# red cape over the shoulders with a gold paw clasp
cape = ('<path d="M 150 300 Q 256 262 362 300 Q 410 330 420 392 L 330 352 Q 256 330 182 352 L 92 392 Q 102 330 150 300 Z" fill="%s" stroke="%s" stroke-width="7" stroke-linejoin="round"/>' % (RED, INK)
        + '<path d="M 160 300 Q 256 268 352 300 L 344 316 Q 256 290 168 316 Z" fill="%s" stroke="%s" stroke-width="5"/>' % (GOLD, INK)
        + '<circle cx="256" cy="316" r="26" fill="%s" stroke="%s" stroke-width="6"/><circle cx="256" cy="316" r="17" fill="%s"/>' % (GOLD, INK, RED2)
        + '<ellipse cx="256" cy="322" rx="7" ry="6" fill="%s"/>' % GOLD
        + "".join('<circle cx="%d" cy="%d" r="3.4" fill="%s"/>' % (x, y, GOLD) for x, y in ((247, 312), (253, 308), (259, 308), (265, 312))))
# glowing tap rings under the paws, sparkle lines, title ribbon
def rings(x):
    return ('<ellipse cx="%d" cy="420" rx="56" ry="15" fill="none" stroke="#ffe36a" stroke-width="10" opacity=".55"/>' % x
            + '<ellipse cx="%d" cy="420" rx="46" ry="11" fill="none" stroke="#fff3b0" stroke-width="4"/>' % x)
spark = "".join('<path d="M %d %d L %d %d" stroke="%s" stroke-width="9" stroke-linecap="round"/><path d="M %d %d L %d %d" stroke="#ffe36a" stroke-width="5" stroke-linecap="round"/>' % (a, b, c, d, INK, a, b, c, d)
                for a, b, c, d in ((106, 368, 84, 352), (112, 344, 100, 318), (406, 368, 428, 352), (400, 344, 412, 318)))
RIB = "M 18 420 L 64 404 L 448 404 L 494 420 L 478 448 L 494 476 L 448 492 L 64 492 L 18 476 L 34 448 Z"
front = (rings(186) + rings(326) + spark
         + '<path d="%s" fill="%s" stroke="%s" stroke-width="8" stroke-linejoin="round"/>' % (RIB, GOLD, INK)
         + '<path d="M 46 418 L 466 418 L 466 478 L 46 478 Z" fill="%s" stroke="%s" stroke-width="4"/>' % (RED, INK)
         + '<text x="256" y="469" text-anchor="middle" font-family="Lilita One" font-size="62" fill="%s" stroke="%s" stroke-width="10" paint-order="stroke" letter-spacing="1">TapCatForever</text>' % (GOLD, INK)
         + '<text x="256" y="469" text-anchor="middle" font-family="Lilita One" font-size="62" fill="url(#g)" letter-spacing="1">TapCatForever</text>')
DEFS = '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff2a0"/><stop offset=".55" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient></defs>' % (GOLD, GOLD2)
for name, body in (("back", back), ("cape", cape), ("front", front)):
    open(os.path.join(WORK, name + ".svg"), "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">%s%s</svg>' % (DEFS, body))
subprocess.check_call(["node", os.path.join(HERE, "render_svg.js"), WORK, "1024"])

# cat pieces from the game art
V = {}
for m in re.finditer(r'V\["([^"]+)"\]=\{"([^"]+)",(\d+),(\d+),(\d+),(\d+),([\d.]+),([\d.]+),"(\w+)"\}', open(os.path.join(ROOT, "VectorData.lua")).read()):
    k, t, x, y, w, h, u, v, kind = m.groups(); V[k] = (t, int(x), int(y), int(w), int(h), float(u), float(v))
S, OX, OY = 2 * 0.86, 2 * 36, 2 * 26   # cat canvas (512) -> logo (1024)
def piece(key, col=None):
    t, x, y, w, h, u, v = V["cat:" + key]
    im = Image.open(os.path.join(ROOT, "Art", "v", t + ".tga")).convert("RGBA")
    im = im.crop((0, 0, round(u * im.width), round(v * im.height))).resize((round(w * S), round(h * S)), Image.LANCZOS)
    if col:
        m2 = ImageChops.multiply(im, Image.new("RGBA", im.size, tuple(int(c * 255) for c in col) + (255,))); m2.putalpha(im.getchannel("A")); im = m2
    return im, round(x * S + OX), round(y * S + OY)
FUR = (0.66, 0.62, 0.66); STRIPE = tuple(c * 0.72 for c in FUR)
logo = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
def put(im_xy): im, x, y = im_xy; logo.alpha_composite(im, (x, y))
logo.alpha_composite(Image.open(os.path.join(WORK, "back.png")).convert("RGBA"))
for k, c in (("body_t", FUR), ("belly", None), ("body_marks_t", STRIPE), ("body_line", None)): put(piece(k, c))
logo.alpha_composite(Image.open(os.path.join(WORK, "cape.png")).convert("RGBA"))
for k, c in (("head_t", FUR), ("head_marks_t", STRIPE), ("face_happy", None)): put(piece(k, c))
front = Image.open(os.path.join(WORK, "front.png")).convert("RGBA")
logo.alpha_composite(front)
for side in "LR":
    put(piece("paw_%s_down_t" % side, (1, 0.97, 0.94))); put(piece("paw_%s_down" % side))
os.makedirs(os.path.join(ROOT, "media"), exist_ok=True)
logo.save(os.path.join(ROOT, "media", "logo.png"))
write_tga(logo.resize((256, 256), Image.LANCZOS), os.path.join(ROOT, "Art", "logo.tga"))
print("logo written")
