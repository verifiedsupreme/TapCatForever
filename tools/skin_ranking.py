"""Skin ranking sheet and proposal (1.6 preview, nothing here changes the game).

Renders every cat skin (TCF.ITEMS, slot "skin") with the real cartoon code (tools/catrender.py),
with its new animated effect if it has one, sorted by how impressive it looks (RANK, scored by
eye from the sheet), labelled with its current source and the proposed one.
usage: python3 tools/skin_ranking.py OUT_DIR   -> OUT_DIR/skins_ranked.png, OUT_DIR/skins_proposal.md
"""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# how impressive each skin looks on the cat (10 = best), with its 1.6 effect
RANK = {
    "skin_galaxy": 10, "skin_rainbow": 9.5, "skin_emberheart": 9.5, "skin_diamond": 9.5, "skin_onyxian": 9, "skin_qiraji": 9,
    "skin_runebound": 9, "skin_lion": 9, "skin_golden": 9, "skin_spectral": 9, "skin_flamesaber": 8.5, "skin_scarlet": 8.5,
    "skin_dreamsaber": 8.5, "skin_skeletal": 8, "skin_strawberry": 8, "skin_maraudon": 8, "skin_ragefire": 8,
    "skin_onyxpanther": 8, "skin_maincoon": 7.5, "skin_mainecoon": 7.5, "skin_darkmoon": 7.5, "skin_clockwork": 7.5,
    "skin_manasaber": 7.5, "skin_fel": 7.5, "skin_mechanocat": 7, "skin_mech": 7, "skin_patchwork": 7, "skin_koi": 7,
    "skin_luckycat": 7, "skin_defias": 7, "skin_stonewatcher": 7, "skin_zulpanther": 7, "skin_winterspring": 7,
    "skin_turnin": 6.5, "skin_questgiver": 6.5, "skin_raidleader": 6.5, "skin_party": 6.5, "skin_clover": 6.5, "skin_lynx": 6.5,
    "skin_zulian": 6.5, "skin_bengal": 6.5, "skin_runestitch": 6.5, "skin_bigglesworth": 6, "skin_tortie": 6, "skin_snowshoe": 6,
    "skin_dalmatian": 6, "skin_cow": 6, "skin_spotted": 6, "skin_moss": 6, "skin_coal": 6, "skin_tanned": 6,
    "skin_tuxedo": 5.5, "skin_frostsaber": 5.5, "skin_nightsaber": 5.5, "skin_calico": 5.5, "skin_mittens": 5,
    "skin_russianblue": 5, "skin_panther": 5, "skin_siamese": 5, "skin_bombay": 4.5, "skin_whitekitten": 4,
    "skin_cornishrex": 4, "skin_blacktabby": 4, "skin_silvertabby": 4, "skin_orange": 4,
}

# the coolest looks move behind the hardest content (Adventure raid and top dungeon final bosses,
# real WoW top dungeon bosses); WoW: Forever has no raids yet, so raids are Adventure only
MOVES = {
    "skin_galaxy": "Adventure: Kel'Thuzad (Naxxramas), 2% a kill. Leaves the Shop.",
    "skin_rainbow": "Adventure: C'Thun (Temple of Ahn'Qiraj), 2% a kill. Leaves the Adventurer's Strongbox.",
    "skin_emberheart": "Adventure: Ragnaros (Molten Core), 3% a kill. The Molten Core expedition keeps a 1% chance.",
    "skin_diamond": "Real WoW: kill General Drakkisath (Blackrock Spire), 5%; Adventure: Nefarian (Blackwing Lair), 2%. Leaves the Heroic Cache.",
    "skin_runebound": "Adventure: Darkmaster Gandling (Scholomance), 3%; real WoW: kill Darkmaster Gandling, 5%. The Stratholme expedition keeps 0.5%.",
    "skin_golden": "Real WoW: kill Emperor Dagran Thaurissan (Blackrock Depths), 4%. The Heroic Cache keeps 1%.",
}
# shop skins: new prices (TapCoins). Income for an active player is about 250-400 TapCoins a day
# (three daily quests of 15-90, a weekly quest of 400, plus Adventure, level-ups and the login bonus),
# so 2,000 is about a week, 7,000 about a month and 30,000 a season.
PRICES = {
    "skin_silvertabby": 350, "skin_blacktabby": 350, "skin_mittens": 300, "skin_tuxedo": 400, "skin_cow": 450,
    "skin_bombay": 500, "skin_siamese": 600, "skin_cornishrex": 500, "skin_whitekitten": 600, "skin_russianblue": 600,
    "skin_dalmatian": 700, "skin_tortie": 800, "skin_snowshoe": 800,
    "skin_calico": 1800, "skin_frostsaber": 1800, "skin_nightsaber": 1800, "skin_spotted": 2000, "skin_panther": 1800,
    "skin_darkmoon": 2500, "skin_bengal": 2000, "skin_mainecoon": 2500, "skin_strawberry": 2500,
    "skin_winterspring": 7000, "skin_mech": 6000, "skin_fel": 7000, "skin_lion": 9000, "skin_lynx": 6500, "skin_manasaber": 7500,
    "skin_spectral": 30000,
}
CHEST = {"pouch": "Cat Treat Pouch", "strong": "Adventurer's Strongbox", "heroic": "Heroic Cache", "dungeon": "Dungeon Chest", "raid": "Raider's Hoard"}


def source(r, it):
    TCF = r.TCF
    if it.skinPrice: return "Shop %s" % format(int(it.skinPrice), ",")
    for boss, d in TCF.SKIN_DROPS.items():
        if d.id == it.id: return "Adventure drop: %s, %g%%" % (boss, d.chance * 100)
    if it.skinAch:
        for a in TCF.ACHIEVEMENTS.values():
            if a.skin == it.id or a.id == it.skinAch: return "Achievement: %s" % a.name
        return "Achievement"
    g = it.get
    if g:
        if g.kind == "chest": return "%s, %g%%" % (CHEST.get(g.chest, g.chest), g.chance * 100)
        if g.kind == "quest": return "%s quest, %g%%" % (g.quest.capitalize(), g.chance * 100)
        if g.kind == "expedition": return "%s expedition, %g%%" % (zone_name(r, g.expedition), g.chance * 100)
        if g.kind == "realdungeon": return "Real WoW %s, %g%%" % ("dungeon" if g.run == "party" else "dungeon or raid", g.chance * 100)
        if g.kind == "craft": return "Crafted (%s %d)" % (g.prof, g.skill)
    if it.id == "skin_orange": return "Every cat starts with it"
    return "?"


def zone_name(r, key):
    """the player-facing name for an Adventure zone or expedition key (mc -> Molten Core)"""
    for t in r.TCF.TIERS.values():
        if t.key == key: return t.name
    ex = r.TCF.EXPEDITION_BY_KEY and r.TCF.EXPEDITION_BY_KEY[key]
    return ex.name if ex else key


# cosmetics (not skins): proposed prices per rarity, like the skins above (TCF.RARITY, used by the
# Shop's Daily Wares); salvage stays the same so TapCoins stay scarce
COSMETIC_PRICES = {4: 2500, 5: 9000}


def cosmetics_md(r):
    TCF = r.TCF
    names = ["", "Common", "Uncommon", "Rare", "Epic", "Legendary"]
    slots = {}
    fx = {4: 0, 5: 0}
    n = {4: 0, 5: 0}
    for it in TCF.ITEM_LIST.values():
        if it.gear or it.slot in ("skin", "fur") or it.source == "set" or int(it.rarity or 0) < 4: continue
        q = int(it.rarity)
        n[q] += 1
        slots.setdefault(q, {}).setdefault(it.slot, 0); slots[q][it.slot] += 1
        if TCF.AnimOf(it) is not None: fx[q] += 1
    L = ["## Cosmetics (not skins): effects and proposed prices", "",
         "Epic and Legendary cosmetics are the expensive ones (the Shop's Daily Wares sell them at their rarity's price; chests can also drop them). What moves with 1.6:", "",
         "- Legendary helms, chest pieces, shoulders, capes and held items: a shine sweeps across the piece (a few have their own effect: Ice Crown, Achiever's Crown, Wings, Felwings, Black Lotus).",
         "- Epic helms, chest pieces and shoulders: two small glints now and then, lighter than the Legendary shine, so Legendary still stands out.",
         "- Epic capes and held items stay still (a cape's picture is mostly the cat's body, and held items move with the paws). Accessories and patterns stay still. Auras and tap effects already move on their own.",
         "- The dungeon set pieces have their own animations and are not sold.", "",
         "If you would rather keep the Epic ones still, that is one line to take out (CosmeticFX.lua).", "",
         "| Rarity | Pieces | With a 1.6 effect | Slots | Price now | Proposed |", "|---|---|---|---|---|---|"]
    for q in (4, 5):
        sl = ", ".join("%s %d" % (k, v) for k, v in sorted(slots.get(q, {}).items(), key=lambda kv: -kv[1]))
        L.append("| %s | %d | %d | %s | %s | %s |" % (names[q], n[q], fx[q], sl, format(int(TCF.RARITY[q].price), ","), format(COSMETIC_PRICES[q], ",")))
    L += ["", "At about 250-400 TapCoins a day, 2,500 is about a week and 9,000 about a month. Common (60), Uncommon (180) and Rare (500) stay as they are. Salvage values stay the same.", ""]
    return L


def main(out):
    from catrender import CatRender
    os.makedirs(out, exist_ok=True)
    r = CatRender()
    skins = [it for it in r.TCF.ITEM_LIST.values() if it.slot == "skin"]
    rank = sorted(skins, key=lambda it: (-RANK.get(it.id, 5), it.name))
    tiles = []
    S = 150
    for i, it in enumerate(rank):
        c = r.cat(S); r.apply(c, {"skin": it.id})
        for _ in range(8): r.step(c, 0.1)
        im = r.paint(c, margin=0.04)
        W, H = im.size
        card = Image.new("RGB", (W + 175, H), (30, 26, 38)); card.paste(im, (0, 0))
        d = ImageDraw.Draw(card)
        fx = r.TCF.AnimOf(it) is not None
        d.text((W - 4, 6), "#%d  %s" % (i + 1, it.name), fill=(255, 225, 140))
        d.text((W - 4, 22), "look %.1f / 10%s" % (RANK.get(it.id, 5), "  +effect" if fx else ""), fill=(190, 230, 190) if fx else (200, 200, 200))
        y = 40
        for line in wrap("now: " + source(r, it), 30): d.text((W - 4, y), line, fill=(205, 200, 220)); y += 13
        if it.id in MOVES:
            for line in wrap("move: " + MOVES[it.id], 30)[:7]: d.text((W - 4, y), line, fill=(255, 160, 90)); y += 13
        elif it.id in PRICES and it.skinPrice and PRICES[it.id] != it.skinPrice:
            d.text((W - 4, y), "price: %s -> %s" % (format(int(it.skinPrice), ","), format(PRICES[it.id], ",")), fill=(255, 210, 90))
        tiles.append(card)
    W, H = tiles[0].size
    cols = 6
    sheet = Image.new("RGB", (cols * W, ((len(tiles) + cols - 1) // cols) * H + 30), (22, 19, 28))
    ImageDraw.Draw(sheet).text((10, 8), "Cat skins ranked by how impressive they look (with the 1.6 effects). Orange: proposed move. Yellow: proposed price. Preview only.", fill=(255, 255, 255))
    for i, t in enumerate(tiles): sheet.paste(t, ((i % cols) * W, 30 + (i // cols) * H))
    sheet.save(os.path.join(out, "skins_ranked.png"))
    write_md(r, rank, os.path.join(out, "skins_proposal.md"))
    print("skins ranked:", len(rank))


def wrap(text, n):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur: lines.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    if cur: lines.append(cur)
    return lines


def write_md(r, rank, path):
    L = ["# Cat skins: ranking and proposal (preview, not applied)", "",
         "Every cat skin, ranked by how impressive it looks on the cat with its new animated effect (scored by eye from skins_ranked.png).",
         "Nothing below is in the game yet: the moves and prices are applied only after you approve them.", "",
         "## Proposed moves: the coolest looks behind the hardest content", "",
         "WoW: Forever has no raids yet, so raid bosses are Adventure only. Real WoW kills use the top dungeons.", "",
         "| Rank | Skin | Now | Proposed |", "|---|---|---|---|"]
    pos = {it.id: i + 1 for i, it in enumerate(rank)}
    for it in rank:
        if it.id in MOVES: L.append("| %d | %s | %s | %s |" % (pos[it.id], it.name, source(r, it), MOVES[it.id]))
    L += ["", "Already behind hard content and staying there: Onyxian Whelpling Cat (Onyxia), Qiraji Scarab Cat (Ossirian), Scarlet Crusader Cat (Whitemane), Skeletal Cat (Baron Rivendare), and the raid achievement cats (Primal Flamesaber, Shadow Dusk Dreamsaber, Jeweled Onyx Panther, Swift Zulian Panther, Mr. Bigglesworth).",
          "Primal Flamesaber and Mr. Bigglesworth look plain for the hardest achievements: with 1.6 they get fire in the fur and falling frost. A later art pass could give them stronger markings.", "",
          "## Staying in the Shop, with new prices", "",
          "Income for an active player is about 250-400 TapCoins a day (three daily quests of 15-90 TapCoins, a weekly quest of 400, plus Adventure, level-ups and the login bonus), so 2,000 is about a week, 7,000 about a month and 30,000 a season. The cheap starter cats stay cheap; the ones with effects cost a lot more.", "",
          "| Rank | Skin | Effect | Now | Proposed |", "|---|---|---|---|---|"]
    for it in rank:
        if it.skinPrice and it.id not in MOVES:
            fx = "yes" if r.TCF.AnimOf(it) is not None else ""
            L.append("| %d | %s | %s | %s | %s |" % (pos[it.id], it.name, fx, format(int(it.skinPrice), ","), format(PRICES.get(it.id, int(it.skinPrice)), ",")))
    L += [""] + cosmetics_md(r)
    L += ["## Effects added in 1.6 (already built, shown in the previews)", "",
          "Every Epic and Legendary skin now has an animated effect, drawn with the new animation layers: Diamond Cat sparkles with glints and a shine sweep, Galaxy Cat has stars and nebula clouds drifting inside its fur, Spectral Tiger glows and trails ghostly wisps, Golden Treasure Cat shimmers, fire cats give off embers (Primal Flamesaber has fire moving in its fur), frost cats have falling snow and frost glints, shadow cats trail wisps, Rainbow Cat's markings shift colour, Runebound Cat's runes pulse.", "",
          "## Full ranking", "", "| Rank | Skin | Rarity | Look | Effect | Now |", "|---|---|---|---|---|---|"]
    names = ["", "Common", "Uncommon", "Rare", "Epic", "Legendary"]
    for it in rank:
        fx = "yes" if r.TCF.AnimOf(it) is not None else ""
        L.append("| %d | %s | %s | %.1f | %s | %s |" % (pos[it.id], it.name, names[int(it.rarity)], RANK.get(it.id, 5), fx, source(r, it)))
    open(path, "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
