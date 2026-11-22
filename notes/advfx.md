# Adventure fight visuals

## Shots look like shots
- Hunters with a bow, gun, crossbow or thrown weapon now shoot it: arrows, bullets (with a muzzle flash), bolts and spinning throwing knives fly from the cat to the enemy, and the damage number shows when the shot lands.
- Mages, priests and warlocks with a wand equipped shoot wand bolts between their spells. The bolt takes the colour of the wand's damage (fire, frost, shadow, arcane, holy or nature) and lands with the game's own spell effect of that school.
- Casters without a wand do not shoot wand bolts: they cast a small spell instead. Warriors, rogues and paladins keep their melee swings, now with a small swipe on the enemy.
- While it fights, a cat that shoots holds its bow, gun or wand in its paw (a cosmetic weapon of the same kind is kept).
- A hunter with nothing in its ranged slot fights in melee (it used to get a pretend ranged weapon). Hunters still get their starter bow.

## Every ability has an animation
- Abilities that hit enemies now play the game's real spell effects on the enemy models (Fireball's explosion, Corruption's shadow while it lasts, Frost Nova's ice while enemies are frozen, and so on), on top of the cartoon effects.
- Stunned, frozen, rooted or feared enemies stand dazed for as long as it lasts, and enemies flinch when a big hit lands.
- Passive abilities show too: auras (Devotion Aura, Trueshot Aura, Inner Fire, Shadowform, Frost Armor, Blessing of Might) glow at the cat's feet when a pack appears, Seal of Righteousness sparkles with every hit, the hunter's pet claws at the enemy, the Searing Totem stands by the cat and throws fire, Lightning Shield orbs circle the cat, the Voidwalker's shield flashes when the cat is hit, and Cat Form sparkles.
- Buffs, heals and shields on the cat stay cartoon effects.

## For testing
- `/run TapCatForever:AdvFxDebug()` says whether the game's spell effects can play on the enemies and how the cat's basic attack lands.
- `/run TapCatForeverDB.cartoonSpellFx = true` turns the game's spell effects off (only the cartoon ones play); set it to nil to turn them back on.

## Art to build
- None. The new sprites (Art/advfx: arrow-style bolt, bullet, muzzle flash, throwing knife, wand bolt, aura ring, totem, claws, orb, sparkle) are made by tools/make_advfx_art.py in the same sticker style.
