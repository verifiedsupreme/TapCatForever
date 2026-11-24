"""Builds the cartoon-style game art: the vector cat and one drawing per item icon.

Renders every SVG at 512px (Chromium via tools/render_svg.js), crops it to its contents,
pads to power-of-two sizes and writes RLE TGAs to Art/v/. Writes VectorData.lua with each
texture's position in the 512 canvas so the addon can place the cropped pieces.

usage: python3 tools/build_vector_art.py [work_dir]
"""
import json, os, re, shutil, subprocess, sys, tempfile
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import vector_items as V
from make_art import write_tga

WORK = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
CAT_DIR, ITEM_DIR = os.path.join(WORK, "cat"), os.path.join(WORK, "items")
OUT = os.path.join(ROOT, "Art", "v")
for d in (CAT_DIR, ITEM_DIR): shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)

# ---- cat layers (make_vector.py writes the SVGs); fill layers get the cel shading
subprocess.check_call([sys.executable, os.path.join(HERE, "make_vector.py"), CAT_DIR])
CAT_LAYERS = ["body_t", "body_marks_t", "belly", "body_line", "head_t", "head_marks_t",
              "paw_L_down_t", "paw_L_down", "paw_R_down_t", "paw_R_down"] + ["face_" + k for k in ("normal", "blink", "happy", "sparkle", "focus")] + ["face_tap%d" % i for i in range(1, 11)] + ["face_pet%d" % i for i in range(1, 11)]
import glob
CAT_LAYERS += sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(CAT_DIR, "*.svg"))
                     if os.path.basename(f).startswith(("pat_", "iris_", "mane")))
CEL_LAYERS = {"body_t", "head_t", "paw_L_down_t", "paw_R_down_t"}
for n in CAT_LAYERS:
    src = open(os.path.join(CAT_DIR, n + ".svg")).read()
    if n in CEL_LAYERS:
        src = src.replace("<defs>", V.DEFS[:-7], 1)  # add the cel filter to the existing defs
        src = re.sub(r'(</defs>)(.*)(</svg>)', r'\1<g filter="url(#cel)">\2</g>\3', src, count=1, flags=re.S)
    open(os.path.join(CAT_DIR, n + ".svg"), "w").write(src)
subprocess.check_call(["node", os.path.join(HERE, "render_svg.js"), CAT_DIR, "512"])

# ---- items: one drawing per icon from tools/item_specs/<group>.txt
groups = json.load(open(os.path.join(HERE, "item_specs", "groups.json")))
two = set(json.load(open(os.path.join(HERE, "item_specs", "two_handed.json"))))
KIND = {"head": "head", "back": "back", "chest": "chest", "belt": "belt", "neck": "neck", "ring": "ring", "shield": "shield", "held": "held",
        "shoulder": "shoulder"}
FAM = {"w_sword": "sword", "w_axe": "axe", "w_mace": "mace", "w_dagger": "dagger", "w_staff": "staff", "w_polearm": "polearm", "w_fist": "fist", "w_bow": "bow"}
items = {}
for g, keys in groups.items():
    specs = {}
    for l in open(os.path.join(HERE, "item_specs", g + ".txt")):
        l = l.strip()
        if l and not l.startswith("#"):
            i, sp = l.split(":", 1); specs[int(i)] = sp.strip()
    fam = FAM.get(g) or KIND[g]
    for i, key in enumerate(keys):
        sp = specs[i]
        first = sp.split()[0]
        if ":" not in first or "=" in first:
            sp = fam + ":" + sp if "=" not in first else fam + ": " + sp
        kind = KIND.get(g) or ("weapon2" if key in two else "weapon1")
        layers = V.render(sp, kind, key)
        if kind == "ring": layers = {"": layers["_down"]}
        cls = {"weapon1": "weapon", "weapon2": "weapon"}.get(kind, kind)
        items[key] = cls
        open(os.path.join(ITEM_DIR, key + ".svg"), "w").write(V.svg(layers[""]))
# real gear shoulders (1.6): one drawing per shoulder icon, from tools/shoulders/specs.txt ("icon: spec")
SH_SPECS = os.path.join(HERE, "shoulders", "specs.txt")
if os.path.exists(SH_SPECS):
    for l in open(SH_SPECS):
        l = l.strip()
        if l and not l.startswith("#"):
            key, sp = [x.strip() for x in l.split(":", 1)]
            if not sp.startswith("shoulder:"): sp = "shoulder:" + sp
            items[key] = "shoulder"
            open(os.path.join(ITEM_DIR, key + ".svg"), "w").write(V.svg(V.render(sp, "shoulder", key)[""]))
subprocess.check_call(["node", os.path.join(HERE, "render_svg.js"), ITEM_DIR, "256"])

# ---- cosmetics: drawn with main = red, trim = green, then split into tintable layers
COS_DIR = os.path.join(WORK, "cos")
shutil.rmtree(COS_DIR, ignore_errors=True); os.makedirs(COS_DIR)
cos = {}
for l in open(os.path.join(HERE, "item_specs", "cosmetics.txt")):
    l = l.strip()
    if not l or l.startswith("#"): continue
    art, kind, sp = [x.strip() for x in l.split("|")]
    have = {t.split("=")[0] for t in sp.split() if "=" in t}
    for k, v in (("m", "#ff0000"), ("t", "#00ff00"), ("g", "#00ff00"), ("e", "#d8f0ff")):
        if k not in have: sp += " %s=%s" % (k, v)
    body = V.render(sp, kind, art)[""]
    open(os.path.join(COS_DIR, art + ".svg"), "w").write(V.svg(body))
    cos[art] = {"weapon1": "weapon", "weapon2": "weapon"}.get(kind, kind)
subprocess.check_call(["node", os.path.join(HERE, "render_svg.js"), COS_DIR, "256"])

def split_layers(png):
    """main (red) and trim (green) become greyscale layers; everything else keeps its colour."""
    im = Image.open(png).convert("RGBA")
    A, B, F = (Image.new("RGBA", im.size, (0, 0, 0, 0)) for _ in range(3))
    pa, pb, pf, src = A.load(), B.load(), F.load(), im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, al = src[x, y]
            if al == 0: continue
            if r - max(g, b) > 40: v = int(min(255, r) * 0.92); pa[x, y] = (v, v, v, al)
            elif g - max(r, b) > 40: v = int(min(255, g) * 0.92); pb[x, y] = (v, v, v, al)
            else: pf[x, y] = (r, g, b, al)
    return A, B, F

# ---- crop, pad, write
def pow2(n):
    p = 8
    while p < n: p *= 2
    return p
entries = {}
def emit(name, png, tex_name, scale=1):
    im = Image.open(png).convert("RGBA")
    bb = im.getbbox()
    if not bb: return
    x0, y0, x1, y1 = bb
    w, h = x1 - x0, y1 - y0
    tw, th = pow2(w), pow2(h)
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    canvas.paste(im.crop(bb), (0, 0))
    write_tga(canvas, os.path.join(OUT, tex_name + ".tga"))
    # position and size in the 512 canvas, plus the used part of the texture (u, v)
    entries[name] = (tex_name, x0 * scale, y0 * scale, w * scale, h * scale, w / tw, h / th)
for n in CAT_LAYERS:
    emit("cat:" + n, os.path.join(CAT_DIR, n + ".png"), "c_" + n)
for key in sorted(items):
    emit(key, os.path.join(ITEM_DIR, key + ".png"), "i_" + key, 2)
for art in sorted(cos):
    for part, im in zip("abf", split_layers(os.path.join(COS_DIR, art + ".png"))):
        path = os.path.join(COS_DIR, "%s_%s.png" % (art, part)); im.save(path)
        emit("cos:%s:%s" % (art, part), path, "k_%s_%s" % (art, part), 2)
        items["cos:%s:%s" % (art, part)] = cos[art]

with open(os.path.join(ROOT, "VectorData.lua"), "w") as f:
    f.write("-- Generated by tools/build_vector_art.py. Cartoon art: texture, x, y, w, h (512 canvas), used u, v of the texture, kind\n")
    f.write("local ADDON, TCF = ...\nlocal V = {}\nTCF.VEC = V\n")
    for name, (tex, x, y, w, h, u, v) in sorted(entries.items()):
        kind = items.get(name, "cat")
        f.write('V["%s"]={"%s",%d,%d,%d,%d,%.4f,%.4f,"%s"}\n' % (name, tex, x, y, w, h, u, v, kind))
# tap-effect sprites live in the same folder
subprocess.check_call([sys.executable, os.path.join(HERE, "make_tapfx.py"), os.path.join(WORK, "tapfx")])
subprocess.check_call([sys.executable, os.path.join(HERE, "make_spellfx.py"), os.path.join(WORK, "spellfx")])
subprocess.check_call([sys.executable, os.path.join(HERE, "make_backgrounds.py"), os.path.join(WORK, "bg")])
# animation sprites (CatAnim.lua) and the cosmetic sets, each built by its own file (tools/sets/README.md)
subprocess.check_call([sys.executable, os.path.join(HERE, "make_animfx.py")])
for setfile in sorted(glob.glob(os.path.join(HERE, "sets", "*.py"))):
    subprocess.check_call([sys.executable, setfile])
total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
print("textures:", len(entries), "size: %.1f MB" % (total / 1e6))
