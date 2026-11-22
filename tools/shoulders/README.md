# Real gear shoulders on the cat

Since 1.6 the cat has a shoulder slot (CatVector.lua `shoulder_a/_b/_f/_x`): pauldrons on both
shoulders, mirrored. Real shoulder gear shows there. Until an icon has its own drawing, the cat
wears a fallback by armour type, tinted with the item's colours (`cos:shoulder_plate`, `_mail`,
`_leather`, `_cloth`, drawn from `tools/item_specs/cosmetics.txt`). This folder is for the next
step: one cartoon drawing per shoulder icon, the way head, chest and cape icons already have theirs.

## Where pauldrons sit and what covers them
- Draw order (CatVector.lua `ORDER`): cape (back) < body < chest < belt < neck < lion mane <
  **shoulders** < head < face < accessories < racial accessory < head gear < weapons < paws.
- So capes, chest pieces and the mane go under the pauldrons; the head sits on their inner part;
  hoods and big helms cover them where they overlap; paws (tapping or raised) are always in front.
- Keep the outer half of each pauldron outside the hood's rim (about x < 50 in body space) so it
  still shows under a hood, and keep spikes below head-top height so they don't fight with helms.

## Spec format
One line per icon in `tools/shoulders/specs.txt`:

    inv_shoulder_23: shoulder:cloth m=crimson t=gold
    inv_shoulder_22: shoulder:spiked m=steel t=gold g=silver rivets

`icon` is the lowercase icon name as `TCF.GEAR` has it. The spec is read by `shoulder_one()` in
`tools/vector_items.py`, which draws the left pauldron around `SH_C` (64, 131) in body space;
`shoulder()` mirrors it onto the right shoulder.
- variants: `plate` (domed), `spiked` (dome with three spikes), `mail` (layered lames), `leather`
  (spaulder with a strap and buckle), `cloth` (padded mantle roll), `mantle` (fluffy ruff), `bone`
  (skull cap), `crystal` (crystal shards). Add new variants in `shoulder_one()` when an icon needs one.
- colours: `m` main, `t` trim or rim, `g` second colour (spikes, horns, fur), `e` gem; palette names
  from `PAL` in vector_items.py or `#rrggbb`.
- flags: `spikes`, `rivets`, `gem`, `fur`, `horns`, `skull`; `glow=<colour>` adds a soft glow.
- `tools/shoulders/specs.example.txt` has a few sample lines.

## Preview (does not touch Art/v)

    python3 tools/shoulders/preview.py out.png --specs tools/shoulders/specs.txt --icons <icon jpg folder> [--only inv_shoulder_02,inv_shoulder_08]

One tile per icon: the real icon (from the folder, `<icon>.jpg`), the pauldrons alone on the cat
and with a helm, chest and cape (greathelm, hood, wizard hat, horned helm in turn), drawn with the
real CatVector code (`tools/catrender.py`).

## Ship
Write `tools/shoulders/specs.txt`, then the art track runs the global build
(`python3 tools/build_vector_art.py`), which draws every line as `Art/v/i_<icon>.tga` with kind
`shoulder` in VectorData.lua. CatVector then uses the icon's drawing for any shoulder item with that
icon (`SLOT_KIND.shoulder`) and the tinted fallback for the rest.

## Every shoulder icon in TCF.GEAR (960 items, 43 icons)
| Icon | Items | Armour types | Example item |
|---|---|---|---|
| inv_shoulder_23 | 103 | mail 39, leather 29, plate 18, cloth 17 | Crimson Silk Shoulders |
| inv_shoulder_02 | 94 | cloth 81, plate 7, mail 6 | Aurora Mantle |
| inv_shoulder_08 | 88 | leather 82, plate 4, mail 1, cloth 1 | Mantle of Thieves |
| inv_shoulder_18 | 66 | leather 30, cloth 17, mail 14, plate 5 | Forest Tracker Epaulets |
| inv_shoulder_09 | 52 | cloth 23, mail 21, plate 7, leather 1 | Ghostly Mantle |
| inv_shoulder_05 | 50 | cloth 33, mail 8, plate 6, leather 3 | Silk Mantle of Gamn |
| inv_shoulder_01 | 43 | leather 14, plate 11, mail 10, cloth 8 | Cabalist Spaulders |
| inv_shoulder_13 | 38 | cloth 13, leather 12, plate 7, mail 6 | Flintrock Shoulders |
| inv_shoulder_25 | 35 | cloth 20, leather 10, plate 3, mail 2 | Glyphed Epaulets |
| inv_shoulder_07 | 33 | leather 17, mail 16 | Cutthroat Pauldrons |
| inv_shoulder_14 | 30 | cloth 12, mail 9, plate 5, leather 4 | Chief Brigadier Pauldrons |
| inv_shoulder_24 | 27 | leather 16, mail 5, cloth 4, plate 2 | Mighty Spaulders |
| inv_shoulder_06 | 22 | cloth 13, leather 6, mail 3 | Palm Frond Mantle |
| inv_shoulder_11 | 22 | plate 11, leather 8, mail 3 | Nightshade Spaulders |
| inv_shoulder_22 | 20 | mail 11, plate 6, leather 3 | Champion's Pauldrons |
| inv_shoulder_26 | 20 | mail 8, cloth 5, plate 5, leather 2 | Elder's Mantle |
| inv_shoulder_15 | 19 | mail 12, leather 6, plate 1 | Banded Pauldrons |
| inv_shoulder_29 | 19 | mail 9, plate 6, leather 4 | Sanguine Pauldrons |
| inv_shoulder_27 | 18 | mail 9, cloth 4, leather 4, plate 1 | Azure Shoulders |
| inv_shoulder_28 | 18 | plate 11, mail 6, leather 1 | Valorous Pauldrons |
| inv_shoulder_30 | 18 | mail 10, plate 6, leather 2 | Lord's Pauldrons |
| inv_shoulder_21 | 17 | mail 7, cloth 5, leather 5 | Mystical Mantle |
| inv_shoulder_10 | 15 | mail 9, cloth 3, plate 2, leather 1 | Elegant Mantle |
| inv_shoulder_16 | 15 | plate 10, mail 4, leather 1 | Wyrmhide Spaulders |
| inv_shoulder_19 | 14 | mail 7, cloth 5, leather 2 | Sheepshear Mantle |
| inv_shoulder_20 | 14 | plate 13, mail 1 | Glimmering Mail Pauldrons |
| inv_shoulder_03 | 11 | mail 5, cloth 4, leather 2 | Brigand's Pauldrons |
| inv_shoulder_12 | 7 | cloth 3, mail 2, leather 1, plate 1 | Dark Leather Shoulders |
| inv_shoulder_17 | 6 | cloth 5, plate 1 | Gaea's Amice |
| inv_shoulder_04 | 5 | mail 5 | Tough Scorpid Shoulders |
| inv_shoulder_74 | 3 | leather 3 | Vigorous Shoulderguards |
| inv_shoulder_77 | 3 | mail 3 | Earthbound Shoulders |
| inv_misc_bone_taurenskull_01 | 2 | cloth 2 | Dreadmist Mantle |
| inv_shoulder_35 | 2 | plate 2 | Conqueror's Spaulders |
| inv_shoulder_71 | 2 | plate 2 | Stalwart Shoulderguards |
| inv_shoulder_80 | 2 | cloth 2 | Enumerated Shoulders |
| inv_shoulder_32 | 1 | cloth 1 | Netherwind Mantle |
| inv_shoulder_33 | 1 | mail 1 | Epaulets of Ten Storms |
| inv_shoulder_34 | 1 | plate 1 | Pauldrons of Wrath |
| inv_shoulder_36 | 1 | mail 1 | Striker's Pauldrons |
| inv_shoulder_37 | 1 | plate 1 | Judgement Spaulders |
| inv_shoulder_78 | 1 | plate 1 | Blood-soaked Saronite Plated Spaulders |
| inv_shoulder_92 | 1 | plate 1 | Acherus Knight's Pauldrons |

Counted from the addon's own data (`TCF.GEAR_LIST`, slot SHOULDER). Many icons are shared across
armour types, so draw what the icon shows, not the armour type.
