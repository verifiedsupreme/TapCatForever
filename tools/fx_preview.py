"""Previews of the 1.6 cosmetic effects, the racial accessory slot and the shoulder layer, drawn
with the real addon code (tools/catrender.py). Nothing in the addon is changed.

usage: python3 tools/fx_preview.py OUT_DIR
  skins_fx.gif         every skin with an effect, animated (grid)
  cosmetics_fx.gif     Legendary and Epic cosmetics with their effects (grid)
  fx_<skin>.gif        a big animated preview of the top skins
  racial_slot.png      every racial accessory worn together with shades, a monocle or a bow tie
  shoulders_layer.png  the shoulder fallbacks for real gear (plate, mail, leather, cloth) with capes,
                       chest pieces, hoods and big helms, plus the Molten Core pauldrons
"""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from catrender import CatRender, save_gif

FPS = 12


def grid_gif(r, entries, path, size=150, cols=6, seconds=3.0):
    cats = []
    for title, look in entries:
        c = r.cat(size); r.apply(c, look); cats.append((title, c))
    frames = []
    for i in range(int(seconds * FPS)):
        tiles = []
        for title, c in cats:
            k = i % 18
            r.paws(c, left_down=not (3 <= k < 6), right_down=not (11 <= k < 14))
            im = r.frame(c, 1.0 / FPS, margin=0.1)
            ImageDraw.Draw(im).text((4, 2), title, fill=(255, 225, 140))
            tiles.append(im)
        W, H = tiles[0].size
        sheet = Image.new("RGB", (cols * W, ((len(tiles) + cols - 1) // cols) * H), (30, 26, 38))
        for j, t in enumerate(tiles): sheet.paste(t, ((j % cols) * W, (j // cols) * H))
        frames.append(sheet)
    save_gif(frames, path, FPS)


def one_gif(r, look, path, size=280, seconds=3.0):
    c = r.cat(size); r.apply(c, look)
    save_gif([r.frame(c, 1.0 / FPS) for _ in range(int(seconds * FPS))], path, FPS)


def sheet(tiles, cols, path, title=None):
    W, H = tiles[0].size
    top = 26 if title else 0
    out = Image.new("RGB", (cols * W, top + ((len(tiles) + cols - 1) // cols) * H), (30, 26, 38))
    if title: ImageDraw.Draw(out).text((8, 6), title, fill=(255, 255, 255))
    for j, t in enumerate(tiles): out.paste(t, ((j % cols) * W, top + (j // cols) * H))
    out.save(path)


def still(r, look, title, size=180, t=0.8, sub=None):
    c = r.cat(size); r.apply(c, look)
    for _ in range(int(t * 10)): r.step(c, 0.1)
    im = r.paint(c, margin=0.1)
    d = ImageDraw.Draw(im); d.text((4, 2), title, fill=(255, 225, 140))
    if sub: d.text((4, 16), sub, fill=(200, 195, 215))
    return im


def main(out):
    os.makedirs(out, exist_ok=True)
    r = CatRender()
    T = r.TCF
    items = list(T.ITEM_LIST.values())
    skins = [it for it in items if it.slot == "skin" and T.AnimOf(it) is not None]
    skins.sort(key=lambda it: (-int(it.rarity), it.name))
    grid_gif(r, [(it.name, {"skin": it.id}) for it in skins], os.path.join(out, "skins_fx.gif"), size=140, cols=7)
    for sid in ("skin_diamond", "skin_galaxy", "skin_spectral", "skin_golden", "skin_flamesaber", "skin_rainbow", "skin_dreamsaber", "skin_emberheart"):
        one_gif(r, {"skin": sid}, os.path.join(out, "fx_%s.gif" % sid))
    cos = [("Frozen Throne Crown", {"fur": "fur_snow", "head": "head_crown_ice"}), ("Crown of the Tapmaster", {"fur": "fur_ginger", "head": "ach_crown"}),
           ("Wings of the Eternal Tapper", {"fur": "fur_cream", "back": "ach_wings"}), ("Felcloth Wings", {"fur": "fur_shadow", "back": "craft_tl_felwings"}),
           ("Black Lotus", {"fur": "fur_lilac", "acc": "acc_blacklotus"}), ("Spectral fur", {"fur": "fur_spectral"}), ("Starlight fur", {"fur": "ach_fur"}),
           ("Titanforged look (shine)", {"fur": "fur_ginger", "head": "WARRIOR:head_greathelm:5", "chest": "WARRIOR:chest_plate:5", "main": "WARRIOR:wpn_sword:5"}),
           ("Ashbringer look (shine)", {"fur": "fur_cream", "chest": "PALADIN:chest_plate:5", "main": "PALADIN:wpn_hammer:5", "off": "PALADIN:off_kiteshield:5"}),
           ("Arcanite Reaper (shine)", {"fur": "fur_silver", "main": "craft_arcanite_reaper"}),
           ("Epic: King's Crown (glints)", {"fur": "fur_ginger", "head": "head_crown"}),
           ("Epic: Judgement look (glints)", {"fur": "fur_cream", "head": "PALADIN:head_winghelm:4", "chest": "PALADIN:chest_plate:4"}),
           ("Epic: Spellfire look (glints)", {"fur": "fur_silver", "head": "MAGE:head_wizard:4", "chest": "MAGE:chest_robe:4"}),
           ("Epic: Stormrage look (glints)", {"fur": "fur_chocolate", "head": "DRUID:head_antlers:4", "chest": "DRUID:chest_leaves:4"}),
           ("Epic: Collector's Top Hat", {"fur": "fur_midnight", "head": "ach_tophat"})]
    grid_gif(r, cos, os.path.join(out, "cosmetics_fx.gif"), size=160, cols=5)

    # racial accessory next to an accessory
    tiles = []
    races = [it for it in items if it.source == "race"]
    accs = ["acc_shades", "acc_monocle", "acc_bowtie", "acc_scarf_red", "acc_mustache"]
    furs = ["fur_ginger", "fur_silver", "fur_midnight", "fur_cream", "fur_chocolate"]
    for i, it in enumerate(races):
        a = accs[i % len(accs)]
        tiles.append(still(r, {"fur": furs[i % len(furs)], "race": it.id, "acc": a}, it.name, sub="with " + T.ITEMS[a].name))
    sheet(tiles, 5, os.path.join(out, "racial_slot.png"), "Racial accessory in its own slot, worn together with an accessory (face pieces sit on top, neck pieces under a beard)")

    # shoulders on outfits
    def gear(art, c1, c2, slot): return r.gear_look(art, c1, c2, slot)
    steel, gold, red, blue, leather, purple = (0.8, 0.83, 0.9), (1, 0.82, 0.3), (0.75, 0.15, 0.15), (0.3, 0.45, 0.9), (0.62, 0.42, 0.25), (0.5, 0.3, 0.8)
    outfits = [
        ("Plate shoulders", {"fur": "fur_ginger", "shoulder": gear("shoulder_plate", steel, gold, "shoulder")}),
        ("Plate + greathelm + plate + cape", {"fur": "fur_ginger", "shoulder": gear("shoulder_plate", steel, gold, "shoulder"), "head": "WARRIOR:head_greathelm:3",
                                              "chest": "WARRIOR:chest_plate:3", "back": "WARRIOR:back_cape:4", "main": "WARRIOR:wpn_sword:3"}),
        ("Mail shoulders", {"fur": "fur_silver", "shoulder": gear("shoulder_mail", (0.6, 0.65, 0.7), blue, "shoulder")}),
        ("Mail + horned helm + mail", {"fur": "fur_silver", "shoulder": gear("shoulder_mail", (0.6, 0.65, 0.7), blue, "shoulder"), "head": "SHAMAN:head_headdress:3" if T.ITEMS["SHAMAN:head_headdress:3"] else "WARRIOR:head_hornhelm:3",
                                       "chest": "WARRIOR:chest_mail:3", "back": "SHAMAN:back_cape:3" if T.ITEMS["SHAMAN:back_cape:3"] else "WARRIOR:back_cape:3"}),
        ("Leather shoulders", {"fur": "fur_chocolate", "shoulder": gear("shoulder_leather", leather, (0.4, 0.26, 0.15), "shoulder")}),
        ("Leather + hood + cloak", {"fur": "fur_chocolate", "shoulder": gear("shoulder_leather", leather, (0.4, 0.26, 0.15), "shoulder"), "head": "ROGUE:head_hood:3",
                                    "chest": "ROGUE:chest_leather:3", "back": "ROGUE:back_cape:3", "main": "ROGUE:wpn_dagger:3"}),
        ("Cloth shoulders", {"fur": "fur_cream", "shoulder": gear("shoulder_cloth", purple, gold, "shoulder")}),
        ("Cloth + wizard hat + robe", {"fur": "fur_cream", "shoulder": gear("shoulder_cloth", purple, gold, "shoulder"), "head": "MAGE:head_wizard:3",
                                       "chest": "MAGE:chest_robe:3", "main": "MAGE:wpn_staff:3"}),
        ("With a lion's mane", {"skin": "skin_lion", "shoulder": gear("shoulder_plate", gold, (1, 1, 1), "shoulder")}),
        ("Molten Core pauldrons", {"fur": "fur_midnight", "shoulder": "set_mc_shoulders", "chest": "set_mc_chest", "back": "set_mc_cape"}),
    ]
    tiles = [still(r, look, title, size=200) for title, look in outfits]
    for i, (title, look) in enumerate(outfits):
        if i in (1, 5):   # tapping: the paws stay in front of the pauldrons
            c = r.cat(200); r.apply(c, look); r.paws(c, True, False)
            im = r.paint(c, margin=0.1); ImageDraw.Draw(im).text((4, 2), title + ", tapping", fill=(255, 225, 140)); tiles.append(im)
    sheet(tiles, 4, os.path.join(out, "shoulders_layer.png"), "Shoulder layer: real gear shoulders by armour type (fallback drawings until each icon has its own), with capes, chest pieces, hoods and big helms")
    print("fx previews written to", out)


if __name__ == "__main__":
    main(sys.argv[1])
