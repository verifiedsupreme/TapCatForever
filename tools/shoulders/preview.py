"""Preview real gear shoulder drawings on the cat without touching Art/v.

usage: python3 tools/shoulders/preview.py OUT.png [--specs tools/shoulders/specs.txt] [--icons DIR] [--only inv_shoulder_02,...]
Reads "icon: spec" lines (see tools/shoulders/README.md), draws each spec with tools/vector_items.py,
and lays out one tile per icon: the real icon (from --icons DIR/<icon>.jpg if given), the pauldrons
alone on the cat, and with a full outfit (helm, chest, cape) so clashes show up. Uses the real
CatVector code through tools/catrender.py.
"""
import argparse, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)
import vector_items as V
import setlib

OUTFITS = [  # helm, chest, cape by armour type, to check the layering
    {"head": "WARRIOR:head_greathelm:3", "chest": "WARRIOR:chest_plate:3", "back": "WARRIOR:back_cape:3"},
    {"head": "ROGUE:head_hood:3", "chest": "ROGUE:chest_leather:3", "back": "ROGUE:back_cape:3"},
    {"head": "MAGE:head_wizard:3", "chest": "MAGE:chest_robe:3"},
    {"head": "WARRIOR:head_hornhelm:3", "chest": "WARRIOR:chest_mail:3", "back": "WARRIOR:back_cape:4"},
]


def read_specs(path):
    out = []
    for l in open(path):
        l = l.strip()
        if l and not l.startswith("#"):
            k, sp = [x.strip() for x in l.split(":", 1)]
            if not sp.startswith("shoulder:"): sp = "shoulder:" + sp
            out.append((k, sp))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--specs", default=os.path.join(HERE, "specs.txt"))
    ap.add_argument("--icons"); ap.add_argument("--only")
    ap.add_argument("--size", type=int, default=150); ap.add_argument("--showcase", help="icons to show large in full outfits (helm, chest, cape) under the sheet"); ap.add_argument("--cols", type=int, default=3)
    a = ap.parse_args()
    specs = read_specs(a.specs)
    if a.only: specs = [s for s in specs if s[0] in a.only.split(",")]
    scratch = os.path.join(os.path.dirname(os.path.abspath(a.out)), ".shoulder_build")
    SET = {"key": "shprev", "name": "Shoulder preview", "lua": "ShoulderPreview", "file": "shoulders/preview", "pieces": [
        {"id": "shprev_" + k, "slot": "shoulder", "kind": "shoulder", "art": "shprev_" + k, "name": k, "rarity": 3, "icon": k,
         "svg": V.render(sp, "shoulder", k)[""]} for k, sp in specs]}
    lua = setlib.build(SET, out=scratch, work=os.path.join(scratch, "work"))
    from catrender import CatRender
    r = CatRender(extra_art=[scratch], extra_lua=[lua])
    tiles = []
    for i, (k, sp) in enumerate(specs):
        alone = r.cat(a.size); r.apply(alone, {"fur": "fur_ginger", "shoulder": "shprev_" + k})
        dressed = r.cat(a.size); r.apply(dressed, dict(OUTFITS[i % len(OUTFITS)], fur="fur_silver", shoulder="shprev_" + k))
        a1, a2 = r.paint(alone, margin=0.08), r.paint(dressed, margin=0.08)
        W, H = a1.size
        tile = Image.new("RGB", (W * 2 + 70, H), (30, 26, 38))
        if a.icons and os.path.exists(os.path.join(a.icons, k + ".jpg")):
            tile.paste(Image.open(os.path.join(a.icons, k + ".jpg")).convert("RGB").resize((56, 56)), (6, 24))
        tile.paste(a1, (70, 0)); tile.paste(a2, (70 + W, 0))
        d = ImageDraw.Draw(tile); d.text((4, 4), k, fill=(255, 225, 140)); d.text((4, H - 16), sp[:60], fill=(190, 185, 205))
        tiles.append(tile)
    W, H = tiles[0].size
    cols = a.cols
    rows = (len(tiles) + cols - 1) // cols
    show = []
    if a.showcase:  # full outfits, large: every one with a helm, a chest piece and a cape
        for i, k in enumerate(a.showcase.split(",")):
            o = dict(OUTFITS[i % len(OUTFITS)]); o.setdefault("back", "MAGE:back_cape:4")
            c = r.cat(int(a.size * 1.6)); r.apply(c, dict(o, fur=("fur_silver", "fur_ginger", "fur_midnight", "fur_cream")[i % 4], shoulder="shprev_" + k))
            im = r.paint(c, margin=0.06); ImageDraw.Draw(im).text((6, 6), k, fill=(255, 225, 140)); show.append(im)
    SW, SH = (show[0].size if show else (0, 0))
    scols = max(1, (cols * W) // SW) if show else 1
    srows = (len(show) + scols - 1) // scols if show else 0
    sheet = Image.new("RGB", (max(cols * W, scols * SW), rows * H + srows * SH), (22, 19, 28))
    for i, t in enumerate(tiles): sheet.paste(t, ((i % cols) * W, (i // cols) * H))
    for i, t in enumerate(show): sheet.paste(t, ((i % scols) * SW, rows * H + (i // scols) * SH))
    sheet.save(a.out)
    print("shoulder preview:", len(tiles), "drawings ->", a.out)


if __name__ == "__main__":
    main()
