"""Shared pipeline for cosmetic sets: one file per set (tools/sets/<set>.py) builds its own
drawings and data without the global art build (tools/build_vector_art.py).

A set file defines SET (see tools/sets/README.md) and ends with `if __name__ == "__main__": main(SET)`.
  python3 tools/sets/<set>.py            writes Art/v/k_<art>_<layer>.tga, Art/<art>.tga (small fallback
                                          for the old pixel cat) and Sets/<Lua>.lua
  python3 tools/sets/<set>.py --out DIR   writes the same into DIR (DIR/v, DIR/<Lua>.lua), for previews
Everything is drawn in the 256-unit cosmetics canvas of tools/vector_items.py (the cat's body
space; head pieces in head space with HEAD), rendered with Chromium (tools/render_svg.js), cropped
and placed on the 512-unit canvas of CatVector.lua. Main drawings get the cel shading; animation
layers (flipbook frames, glows, masks) don't unless they ask for it.
"""
import argparse, os, shutil, subprocess, sys, tempfile
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import vector_items as V
from make_art import write_tga

# drawing helpers for set files
from vector_items import P, LN, CI, EL, RC, GEM, GLOW, INK, C, light, darker, mirror, HEAD_TF, RIGHT_HAND, LEFT_HAND, DRAPE_OUT, DRAPE_IN, DRAPE_EDGE, BODY_OUT, qpts, shoulder_one, SH_C
def HEAD(s): return "<g %s>%s</g>" % (HEAD_TF, s)
def RHAND(s): return "<g %s>%s</g>" % (RIGHT_HAND, s)
def BOTH(s): return s + mirror(s, 128)
def K(art, layer="f"): return "cos:%s:%s" % (art, layer)

def pow2(n):
    p = 8
    while p < n: p *= 2
    return p

def lua(v, ind=""):
    """Python data -> Lua table literal"""
    if v is None: return "nil"
    if v is True: return "true"
    if v is False: return "false"
    if isinstance(v, (int,)): return str(v)
    if isinstance(v, float): return ("%.4f" % v).rstrip("0").rstrip(".")
    if isinstance(v, str): return '"%s"' % v.replace("\\", "\\\\").replace('"', '\\"')
    if isinstance(v, (list, tuple)):
        inner = [lua(x, ind + "  ") for x in v]
        one = "{ " + ", ".join(inner) + " }"
        if len(one) < 110 and "\n" not in one: return one
        return "{\n" + "".join(ind + "  " + x + ",\n" for x in inner) + ind + "}"
    if isinstance(v, dict):
        def key(k): return k if k.isidentifier() else "[%s]" % lua(k)
        inner = ["%s = %s" % (key(k), lua(x, ind + "  ")) for k, x in v.items() if x is not None]
        one = "{ " + ", ".join(inner) + " }"
        if len(one) < 110 and "\n" not in one: return one
        return "{\n" + "".join(ind + "  " + x + ",\n" for x in inner) + ind + "}"
    raise TypeError(v)

def emit(png, tex_path):
    """crop to the drawing, pad to powers of two, write a TGA; returns (x, y, w, h, u, v) in the 512 canvas"""
    im = Image.open(png).convert("RGBA")
    bb = im.getbbox()
    if not bb: return None
    x0, y0, x1, y1 = bb
    w, h = x1 - x0, y1 - y0
    tw, th = pow2(w), pow2(h)
    c = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); c.paste(im.crop(bb), (0, 0))
    write_tga(c, tex_path)
    return (x0 * 2, y0 * 2, w * 2, h * 2, w / tw, h / th)

def pixel_fallback(png, path):
    """the old pixel cat's 64x64 texture: the drawing shrunk from the 256 canvas"""
    im = Image.open(png).convert("RGBA").resize((64, 64), Image.LANCZOS)
    write_tga(im, path)

def glow_fallback(col, path):
    """an effect's base texture (drawn by Cat.lua behind or over the cat): a soft ring of colour"""
    import math
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0)); px = im.load()
    for y in range(64):
        for x in range(64):
            d = math.hypot(x - 31.5, y - 33.5) / 30
            a = max(0.0, 1 - abs(d - 0.72) / 0.28) ** 1.6 * 0.75 + max(0.0, 1 - d) ** 2 * 0.25
            px[x, y] = (int(col[0] * 255), int(col[1] * 255), int(col[2] * 255), int(255 * min(1, a)))
    write_tga(im, path)

def build(SET, out=None, work=None):
    """renders every piece and layer of SET. out=None writes into the addon (Art/v, Art, Sets);
    out=DIR writes DIR/v/*.tga, DIR/<art>.tga and DIR/<Lua>.lua instead. Returns the Lua file path."""
    art_dir = os.path.join(out, "v") if out else os.path.join(ROOT, "Art", "v")
    pix_dir = out if out else os.path.join(ROOT, "Art")
    lua_dir = out if out else os.path.join(ROOT, "Sets")
    for d in (art_dir, pix_dir, lua_dir): os.makedirs(d, exist_ok=True)
    work = work or tempfile.mkdtemp(prefix="set_%s_" % SET["key"])
    shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
    jobs = []   # (art, layer name, kind)
    for p in SET["pieces"]:
        art = p["art"]
        if p.get("svg"):
            open(os.path.join(work, "%s__f.svg" % art), "w").write(V.svg(p["svg"], cel=True))
            jobs.append((art, "f", p["kind"]))
        for name, body in (p.get("layers") or {}).items():
            cel = False
            if isinstance(body, tuple): body, cel = body
            open(os.path.join(work, "%s__%s.svg" % (art, name)), "w").write(V.svg(body, cel=cel))
            jobs.append((art, name, "anim"))
    subprocess.check_call(["node", os.path.join(HERE, "render_svg.js"), work, "256"])
    vec = {}
    for art, name, kind in jobs:
        tex = "k_%s_%s" % (art, name)
        r = emit(os.path.join(work, "%s__%s.png" % (art, name)), os.path.join(art_dir, tex + ".tga"))
        if r: vec[K(art, name)] = [tex, r[0], r[1], r[2], r[3], round(r[4], 4), round(r[5], 4), kind]
    pieces = []
    for p in SET["pieces"]:
        art = p["art"]
        if p["slot"] == "effect":
            glow_fallback(p.get("glow", (1, 0.6, 0.2)), os.path.join(pix_dir, art + ".tga"))
        else:
            pixel_fallback(os.path.join(work, "%s__f.png" % art), os.path.join(pix_dir, art + ".tga"))
        pieces.append({k: p.get(k) for k in ("id", "slot", "art", "name", "rarity", "icon", "boss", "word", "fx", "anim")})
    path = os.path.join(lua_dir, SET["lua"] + ".lua")
    with open(path, "w") as f:
        f.write("-- Generated by tools/sets/%s.py (tools/setlib.py). Do not edit by hand: change the set file and run it again.\n" % SET["file"])
        f.write("-- %s\n" % SET.get("about", SET["name"] + " set"))
        f.write("local ADDON, TCF = ...\n")
        body = {"key": SET["key"], "name": SET["name"], "zone": SET.get("zone"), "vec": vec, "pieces": pieces}
        # (1.7.0) a crafted set (a profession's long chase): no zone or bosses, its recipes are in ProfSets.lua
        for k in ("prof", "spec", "title"):
            if SET.get(k): body[k] = SET[k]
        f.write("TCF.AddCosmeticSet(%s)\n" % lua(body))
    print("set %s: %d pieces, %d textures -> %s" % (SET["key"], len(pieces), len(vec), path))
    return path

def main(SET):
    ap = argparse.ArgumentParser(description="Build the %s cosmetic set" % SET["name"])
    ap.add_argument("--out", help="write into this folder instead of the addon (for previews)")
    a = ap.parse_args()
    build(SET, a.out)
