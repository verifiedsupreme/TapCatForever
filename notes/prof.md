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
- None needed for the starter sets: every new piece in a slot the cat shows (chest, belt, cloak, weapons) already has a drawing.

## Hand speed
- A new upgrade on the gathering page, next to your tool: Hand speed. Each level makes your clicks by hand come faster, on every spot of your profession.
- It goes from one click every 1.5 seconds (0.75 with a well upgraded tool) down to 0.25 seconds: 4 clicks a second at level 15.
- The first levels are cheap. Each level costs a lot more than the last, and the last ones take many business sales to afford.
- Hand speed is kept when you sell the business, like your skills.
- The page shows how many clicks a second you make now and with the next level.

## For the developer: hand speed numbers
- Cooldown = max(0.25, tool cooldown x (1/3)^(level/15)); the tool cooldown is the old one (1.5 x 0.985^tool level, at least 0.75).
- Level n+1 costs 10K x 10^(0.5n + 0.0306n^2), two significant digits: 10K, 34K, 130K, 600K, 3.1M, 18M, 130M, 1B, 9.1B, 95B, 1.1T, 16T, 250T, 4.7Qa, 99Qa.
- tools/trade_sim.py --speed 2 56 (one cat, 2 h a day, selling whenever it doubles its Renown, buying a level when it costs at most a quarter of the gold in hand): levels 1-6 on day 0-1, 7 on day 4, 8 on day 11, 9 on day 17, 10 on day 26, 11 on day 32, 12 on day 45; 13-15 later than 8 weeks. Profession unlocks are where they were (First Aid day 22, Fishing day 31, Cooking day 48).
- Clicking pays a share of a spot's cycle, so faster hands mean more gold for players who click a lot. Upper bound, clicking nonstop for the whole 2 hours every day (--clicker): 72T earned after 3 weeks with hand speed against 30T without. Helpers and idle income do not change.

## Crafted cosmetics cost more
- Cosmetic only recipes (fur colours and the other cosmetics in every profession) now need a lot more of the materials they are made from: 5 times as much for uncommon ones, 10 times for rare ones and fur colours, 20 times for epic and 40 times for legendary ones.
- Rare ingredients stay as they were: Black Lotus, Mr. Pinchy, bandages, dishes and bought spices.
- Gear recipes cost the same as before.

## For the developer: cosmetic costs
- Professions.lua TCF.COSMETIC_MAT_MULT by item rarity { 3, 5, 10, 20, 40 }; kept materials in TCF.COSMETIC_MAT_KEEP plus every d_ (dish) and b_ (bandage) key. Applied once at load to every cosmetic recipe; a skin's recipe shares its table with the skin's get.mats, so the Compendium shows the same amounts.
- Examples: Linen Scarf 300 linen, Runestitched Cat 5000 mageweave + 9000 runecloth, Felcloth Wings 16000 felcloth + 48000 runecloth, Lotus Bloom 24000 dreamfoil + 60 Black Lotus.
- tools/trade_sim.py --speed 2 28 (a Mage that sells; it keeps all its cloth, nothing else spends it): materials for the Linen Scarf on day 0, Silk Wizard Hat day 1, Runestitched Cat day 6, Runecloth Top Hat day 7, Felcloth Wings day 19. Real players also spend cloth on crafting levels and First Aid, so expect later. Herbalism and Fishing cosmetics were checked by hand from the garden and fishing buddy rates (Lotus Bloom and Pinchy's gift: about one to two weeks of a full garden or the best buddy at Azshara).
