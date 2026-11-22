# Adventure fight visuals

## Shots look like shots
- Hunters with a bow, gun, crossbow or thrown weapon now shoot it: arrows, bullets (with a muzzle flash), bolts and spinning throwing knives fly from the cat to the enemy. The damage number shows when the shot lands, and a killing shot lands before the enemy falls.
- Mages, priests and warlocks with a wand equipped shoot wand bolts between their spells. The bolt takes the colour of the wand's damage (fire, frost, shadow, arcane, holy or nature) and lands with the game's own spell effect of that school.
- Casters without a wand do not shoot wand bolts: they cast a small spell instead. Warriors, rogues and paladins keep their melee swings, now with a small swipe on the enemy. A druid in Cat Form swipes too.
- While it is out fighting, a cat that shoots holds its bow, gun or wand in its paw, also between packs. A cosmetic weapon stays in its paw only when it is the same kind (a cosmetic bow for a bow or crossbow, a rifle for a gun, a wand for a wand).
- A hunter with nothing in its ranged slot fights in melee (it used to get a pretend ranged weapon). Hunters still get their starter bow. For such a hunter the Power number used by expeditions and the leaderboard is a little lower than before.

## Every ability has an animation
- Abilities that hit enemies now play the game's real spell effects on the enemy models (Fireball's explosion, Corruption's shadow while it lasts, Frost Nova's ice while enemies are frozen, and so on), on top of the cartoon effects.
- Effects of spells that hit one enemy (Moonfire, Shadow Word: Pain, Fireball) play only on that enemy. Area spells play on every enemy.
- A lasting effect stays on when other spells or wand bolts hit the same enemy. When two lasting effects meet (Corruption, then Fear), the newer one shows and the other comes back when it ends.
- Stunned, frozen, rooted or feared enemies stand dazed for as long as it lasts. Other enemies flinch when an ability hits them.
- Passive abilities show too: auras (Devotion Aura, Trueshot Aura, Inner Fire, Shadowform, Frost Armor, Blessing of Might) glow at the cat's feet when a pack appears, Seal of Righteousness sparkles with every hit, the hunter's pet claws at the enemy, the Searing Totem stands by the cat and throws fire, Lightning Shield orbs circle the cat, the Voidwalker's shield flashes when the cat is hit, and Cat Form sparkles.
- Buffs, heals and shields on the cat stay cartoon effects.

## For developers (not player notes)
- `/run TapCatForever:AdvFxDebug()` says whether the game's spell effects can play on the enemies and how the cat's basic attack lands.
- `/run TapCatForeverDB.cartoonSpellFx = true` turns the game's spell effects off (only the cartoon ones play); set it to nil to turn them back on.
- `python3 tools/make_spell_kits.py <data-dir>` rebuilds SpellKitData.lua and lists the 17 wands whose school is guessed from the name.

## Art to build
- None. The new sprites (Art/advfx: crossbow bolt, bullet, muzzle flash, throwing knife, wand bolt, aura ring, totem, claws, orb, sparkle) are made by tools/make_advfx_art.py in the same sticker style.
