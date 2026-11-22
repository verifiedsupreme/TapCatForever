"""Preview one cosmetic set on the cat without touching Art/v or the addon's data.

usage: python3 tools/set_preview.py tools/sets/<set>.py OUT_DIR [--fur fur_ginger] [--skin skin_x] [--seconds 3]
Builds the set into a scratch folder (tools/setlib.py --out), loads the addon in the Lua mock with
that set's data, draws the cat with the real CatVector/CatAnim code (tools/catrender.py) and writes
  OUT_DIR/sets_<key>.gif        the whole set worn, animated (paws tapping now and then)
  OUT_DIR/sets_<key>.png        a still of the same
  OUT_DIR/sets_<key>_pieces.png each piece on its own, plus the full set
"""
import argparse, importlib.util, os, sys, tempfile
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def load_set(path):
    spec = importlib.util.spec_from_file_location("setdef", path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.SET


def build_scratch(SET, scratch=None):
    import setlib
    scratch = scratch or tempfile.mkdtemp(prefix="setprev_%s_" % SET["key"])
    lua = setlib.build(SET, out=scratch, work=os.path.join(scratch, "work"))
    return scratch, lua


def renderer_for(sets):
    """a CatRender with these (SET, scratch, lua) builds loaded on top of the addon"""
    from catrender import CatRender
    return CatRender(extra_art=[s[1] for s in sets], extra_lua=[s[2] for s in sets])


def label(im, text, sub=None):
    d = ImageDraw.Draw(im)
    d.text((8, 6), text, fill=(255, 220, 140))
    if sub: d.text((8, 20), sub, fill=(200, 190, 210))
    return im


def animate(r, cat, seconds=3.0, fps=12, tap=True):
    frames = []
    n = int(seconds * fps)
    for i in range(n):
        if tap:
            k = i % 18
            r.paws(cat, left_down=not (3 <= k < 7), right_down=not (11 <= k < 15))
        frames.append(r.frame(cat, 1.0 / fps))
    return frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("set"); ap.add_argument("out")
    ap.add_argument("--fur", default=None); ap.add_argument("--skin", default=None)
    ap.add_argument("--seconds", type=float, default=3.0); ap.add_argument("--size", type=int, default=300)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    SET = load_set(a.set)
    scratch, lua = build_scratch(SET, os.path.join(a.out, ".build_" + SET["key"]))
    r = renderer_for([(SET, scratch, lua)])
    look = {p["slot"]: p["id"] for p in SET["pieces"]}
    base = {}
    if a.skin or SET.get("preview_skin"): base["skin"] = a.skin or SET.get("preview_skin")
    else: base["fur"] = a.fur or SET.get("preview_fur", "fur_ginger")
    cat = r.cat(a.size)
    r.apply(cat, dict(base, **look))
    frames = animate(r, cat, a.seconds)
    from catrender import save_gif
    save_gif(frames, os.path.join(a.out, "sets_%s.gif" % SET["key"]))
    still = r.frame(cat, 0.0)
    label(still, SET["name"] + " set").save(os.path.join(a.out, "sets_%s.png" % SET["key"]))
    # pieces sheet: each piece alone (after a moment of animation), then the whole set
    tiles = []
    for p in SET["pieces"]:
        c = r.cat(220)
        r.apply(c, dict(base, **{p["slot"]: p["id"]}))
        for _ in range(7): r.step(c, 0.1)
        tiles.append(label(r.paint(c), p["name"], "%s, from %s" % (p.get("word") or p["slot"], p.get("boss"))))
    c = r.cat(220); r.apply(c, dict(base, **look))
    for _ in range(7): r.step(c, 0.1)
    tiles.append(label(r.paint(c), "Full set"))
    W, H = tiles[0].size
    cols = 4
    sheet = Image.new("RGB", (cols * W, ((len(tiles) + cols - 1) // cols) * H), (30, 26, 38))
    for i, t in enumerate(tiles): sheet.paste(t, ((i % cols) * W, (i // cols) * H))
    sheet.save(os.path.join(a.out, "sets_%s_pieces.png" % SET["key"]))
    print("wrote", os.path.join(a.out, "sets_%s.gif" % SET["key"]))


if __name__ == "__main__":
    main()
