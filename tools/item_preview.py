"""Draws item specs onto the vector cat for review.
usage: python3 tools/item_preview.py <cat_layer_dir> <work_dir> <out.png> <specfile|-> [cols]
spec lines: kind | spec | label      (kind: head chest belt neck ring weapon1 weapon2 shield held)
"""
import os, subprocess, sys
from PIL import Image, ImageChops, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import vector_items as V

CAT, WORK, OUT, SPECS = sys.argv[1:5]
COLS = int(sys.argv[5]) if len(sys.argv) > 5 else 6
os.makedirs(WORK, exist_ok=True)
lines = [l.strip() for l in (sys.stdin if SPECS == "-" else open(SPECS)) if l.strip() and not l.startswith("#")]
items = []
for i, l in enumerate(lines):
    kind, spec, *label = [p.strip() for p in l.split("|")]
    for suffix, body in V.render(spec, kind, str(i)).items():
        open(os.path.join(WORK, "it%03d%s.svg" % (i, suffix)), "w").write(V.svg(body))
    items.append((kind, spec, label[0] if label else spec))
subprocess.check_call(["node", os.path.join(os.path.dirname(__file__), "render_svg.js"), WORK, "512"])

def layer(n, c=None):
    im = Image.open(n).convert("RGBA")
    if c is None: return im
    out = ImageChops.multiply(im, Image.new("RGBA", im.size, tuple(int(v * 255) for v in c) + (255,)))
    out.putalpha(im.getchannel("A")); return out
def cl(n, c=None): return layer(os.path.join(CAT, n + ".png"), c)
FUR = (.78, .78, .8); STRIPE = tuple(v * .8 for v in FUR)
S = 260
rows = (len(items) + COLS - 1) // COLS
sheet = Image.new("RGBA", (COLS * S, rows * (S + 26)), (245, 236, 226, 255)); d = ImageDraw.Draw(sheet)
for i, (kind, spec, label) in enumerate(items):
    it = lambda suf="": layer(os.path.join(WORK, "it%03d%s.png" % (i, suf)))
    c = Image.new("RGBA", (512, 512), (0, 0, 0, 0)); put = c.alpha_composite
    put(cl("body_t", FUR)); put(cl("body_marks_t", STRIPE)); put(cl("belly")); put(cl("body_line"))
    if kind == "chest": put(it())
    if kind == "belt": put(it())
    if kind == "neck": put(it())
    put(cl("head_t", FUR)); put(cl("head_marks_t", STRIPE)); put(cl("face"))
    if kind == "head": put(it())
    put(cl("desk"))
    if kind in ("weapon1", "weapon2"): put(it())
    lp = "up" if kind == "ring" else "down"
    put(cl("paw_L_%s_t" % lp, FUR)); put(cl("paw_L_%s" % lp)); put(cl("paw_R_down_t", FUR)); put(cl("paw_R_down"))
    if kind == "ring": put(it("_up"))
    if kind in ("shield", "held"): put(it())
    x, y = (i % COLS) * S, (i // COLS) * (S + 26)
    sheet.alpha_composite(c.resize((S - 10, S - 10), Image.LANCZOS), (x + 5, y + 24))
    d.text((x + 6, y + 6), label[:40], fill=(110, 60, 30, 255))
    icon_dir = os.environ.get("ICONS")
    if icon_dir and len(label.split()) > 1 and os.path.exists(os.path.join(icon_dir, label.split()[1] + ".jpg")):
        sheet.paste(Image.open(os.path.join(icon_dir, label.split()[1] + ".jpg")).convert("RGB").resize((56, 56)), (x + S - 62, y + 26))
sheet.save(OUT)
