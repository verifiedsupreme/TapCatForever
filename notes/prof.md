# Professions (1.6)

## Skill-ups work like WoW
- The first few crafts or clicks on something new always give a skill point. After that it slows down a lot, and once your skill is 50 above it, it teaches you nothing more. Move on to the next spot or recipe to keep learning.
- Recipes, gathering spots, seeds, bandages, fishing spots and dishes are coloured like in WoW: orange always teaches you, yellow often, green sometimes, pale green rarely, grey no longer.
- Hover one to see "Still teaches you: often" (or sometimes, rarely, no longer).
- Gathering spots count too: your first spot teaches up to 50, the second up to 100, and so on.
- Recipe materials were lowered so levelling a craft to 300 still takes about six weeks of normal play.

## White starter sets
- Blacksmithing, Leatherworking and Tailoring can each make a cheap white starter set at low skill, so a new cat can wear a full crafted set.
- Blacksmithing: Copper Bracers, Copper Chain Pants, Rough Copper Vest, Light Chain Gloves, Copper Chain Boots, Copper Chain Belt and a copper weapon (mace, axe, shortsword or claymore).
- Leatherworking: Handstitched Leather Bracers, Boots, Vest, Cloak, Pants and Belt, and Rough Leather Gloves.
- Tailoring: Linen Cloak, Simple Linen Pants, Knitted Gloves, Brown Linen Vest, Knitted Bracers, Linen Belt and Simple Linen Boots.
- Each piece costs about 5 to 9 of your first material.
- While your crafting skill is under 75 the set is shown first on the Crafting page, with "Starter set 3/7 made" at the top. Pieces you made, have in your bag or wear count.
- All the higher crafted gear is still there.

## For the developer: starter sets
- Real Classic white crafted items where Classic had them, with their real skill levels. Classic had no crafted white gloves (any craft) or cloth bracers, so those slots use real Classic vendor whites of the same armour type (Light Chain Gloves, Rough Leather Gloves, Knitted Gloves, Knitted Bracers) made at skill 5 or 10. They no longer drop as loot.
- Classic has no white helm or shoulders below level 15 at all (the only one is the Worn Fishing Hat at 15), so the sets have no head or shoulder piece. Say if you want made-up pieces for those slots.
- Data: tools/make_crafted.py STARTER / STARTER_VENDOR, written to CraftData.lua as TCF.CRAFT_STARTER and starter = true on the recipes.

## Art to build
- None needed. The new starter items use existing item icons; pieces without a cat drawing show the plain look (Copper Chain Pants, Copper Bracers and the other non-visible slots are not drawn anyway).
