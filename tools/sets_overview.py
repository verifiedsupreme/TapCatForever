"""All cosmetic sets on the cat side by side, drawn with the addon as it ships (Art/v and the
Sets/*.lua files in the TOC, so run it after tools/build_vector_art.py). Nothing is changed.

usage: python3 tools/sets_overview.py OUT_DIR [--size 200] [--cols 4] [--seconds 3]
  OUT_DIR/sets_overview.gif   every set worn in full, animated (paws tapping now and then)
  OUT_DIR/sets_overview.png   a still of the same, with each set's bosses under its cat
"""
import argparse, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from catrender import CatRender, save_gif

FPS = 12


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--size", type=int, default=200); ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--seconds", type=float, default=3.0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    r = CatRender()
    T = r.TCF
    sets = []
    for i in range(1, len(T.COSMETIC_SETS) + 1):
        d = T.COSMETIC_SETS[i]
        look = {}
        for j in range(1, len(d["items"]) + 1):
            it = d["items"][j]
            look[it["slot"]] = it
        c = r.cat(a.size); r.apply(c, look)
        sets.append((d["name"], d["key"], c))
    zone = {}
    for i in range(1, len(T.TIERS) + 1):
        zone[T.TIERS[i]["key"]] = T.TIERS[i]["name"]
    cols = a.cols
    frames = []
    for f in range(int(a.seconds * FPS)):
        tiles = []
        for name, key, c in sets:
            k = (f + len(tiles) * 5) % 18
            r.paws(c, left_down=not (3 <= k < 7), right_down=not (11 <= k < 15))
            im = r.frame(c, 1.0 / FPS)
            ImageDraw.Draw(im).text((8, 6), name + " set", fill=(255, 220, 140))
            tiles.append(im)
        W, H = tiles[0].size
        sheet = Image.new("RGB", (cols * W, ((len(tiles) + cols - 1) // cols) * H), (30, 26, 38))
        for i, t in enumerate(tiles): sheet.paste(t, ((i % cols) * W, (i // cols) * H))
        frames.append(sheet)
    save_gif(frames, os.path.join(a.out, "sets_overview.gif"), FPS)
    frames[len(frames) // 3].save(os.path.join(a.out, "sets_overview.png"))
    print("wrote", os.path.join(a.out, "sets_overview.gif"), "with", len(sets), "sets")


if __name__ == "__main__":
    main()
