# Adventure

## Faster start
- Auto-advance now tries the next zone 2 levels before its level (raids still wait for level 60). Travelling by hand still has no level limit.
- The last boss of each starter zone (Elwynn Forest, Westfall, Ragefire Chasm, Wailing Caverns and The Deadmines) is a little easier: 10% extra health instead of 30%.
- A new cat that presses about 2 keys a second now reaches Westfall after about 18 minutes of Adventure (it was about 32) and level 10 after about 31 minutes.

## Adventure explained
- A Help button next to Bosses and loot opens "How Adventure works": two short pages, one on fights, stages, zones and Auto-advance, one on every reward. It also opens by itself the first time you visit the Adventure tab.
- The line under the fight now says what your cat is doing and what it waits for, for example "Shadowfang Keep cleared. Next: Blackfathom Deeps opens at level 22 (your cat is 19). Farming here until then."
- Hover the zone name to see what is left to earn there: bosses still to beat for the first time and what they give, the zone clear bonus, how long until the next fighting-time chest, and which bosses can drop loot again.

## First kills give more in bigger zones
- The first time your cat beats a boss, the reward now grows with the zone:
  - Elwynn Forest and Westfall: a green piece of gear or a Cat Treat Pouch.
  - Dungeons up to level 29: a piece of the boss's loot, sometimes with a Cat Treat Pouch.
  - Dungeons from level 30: a Rare or better piece, with a chance of an Adventurer's Strongbox.
  - Dungeons from level 45: two pieces, or a piece and a Dungeon Chest.
  - Raids: two pieces with a chance of a Raider's Hoard. Final raid bosses give two or three pieces and the Hoard.
- Final bosses keep their zone clear chest and TapCoins. TapCoins are unchanged.
- First-kill gear is always something your cat's class can use, and never Legendary.

## Farm a boss for its loot
- Bosses can now drop their real loot again after the first kill. The chance is small: a piece usually takes between 1 in 350 and 1 in 3,000 kills, about 2 to 15 hours of farming one boss. Even the rarest piece is at least 1 in 5,000 kills (about a day of farming).
- Bosses and loot (next to Help) lists each boss in the zone, its first-kill reward, and the pieces it can drop for your cat with the chance per kill.
- Press Farm on a piece (or Farm this boss): your cat stays on that boss and fights it again and again. Auto-advance turns off while you farm and comes back when you stop.
- The line under the fight shows "Farming Edwin VanCleef for Cruel Barb (about 0.2% per kill), kills so far: 12."
- You can farm a boss you have reached but not beaten yet. Its first kill counts, and if the first-kill reward is the piece you want, farming stops there.
- When the piece drops, farming stops with one chat line. Stop farming, moving to another stage or zone, or turning Auto-advance on also stops it (at once).
- Fighting-time chests keep their own timers while you farm.
- Gear tooltips in the Compendium say how often a boss drops the piece for your cat on later kills, and what that boss's first kill gives.
- The Treasure Bag's list of where chests come from now mentions first kills.

## Rewards for real WoW bosses
- Some rewards now come from killing certain bosses in real World of Warcraft with TapCatForever on. Tooltips and the Compendium say "In WoW: kill <boss> in <place>" for these, and how many times you have killed that boss on this character.
- Dungeon bosses count when the game says the encounter was won. They are recognised by the boss itself, so this works in every game language.
- Hogger, out in Elwynn Forest, counts when you fought him and then see him dead (as your target, focus or nameplate). If someone else tagged him, he doesn't count.
- Hogger: Hogger's Chewed Bandana, always on your first kill.
- Archmage Arugal (Shadowfang Keep): Arugal's Worgen Cowl, 20% each kill.
- General Drakkisath (Blackrock Spire): Drakkisath's Ember Crown, 20% each kill.
- These skins moved from Adventure drops to the real bosses: Defias Bandit Cat (Edwin VanCleef, The Deadmines, 15%), Ragefire Cinder Cat (Taragaman the Hungerer, Ragefire Chasm, 15%) and Stone Watcher Cat (Archaedas, Uldaman, 10%). They still count for Tiger King. Adventure keeps its other boss skins, such as the Scarlet Crusader Cat and the Wind-Up Clockwork Cat.
- Nothing needs a raid: WoW: Forever has no raids yet.
- All of these are Cosmetic only.

## For other tracks: TCF.BOSS_COSMETICS
- TCF.BOSS_COSMETICS = TCF.BOSS_COSMETICS or {} (AdventureRewards.lua).
- Key: the Adventure boss's display name exactly as TCF.TIERS names it (the first field of an entry in a tier's bosses list), for example "Ragnaros", "Edwin VanCleef", "Hogger".
- Value: a list of TCF.ITEMS keys. On every Adventure kill of that boss, each listed item the player doesn't own yet is given quietly (no notice for cosmetics, one chat line if chat messages are on). The Compendium and tooltips then say "Adventure: <boss> in <zone> gives it every time you beat it, until you have it".

## The window knows when you're in a dungeon
- While you are inside a real dungeon, opening the TapCatForever window shows a slim banner at the bottom of the character column, in three short lines, for example "You're in The Deadmines. / Finish it for a Dungeon Chest; 5 TapCoins a boss. / Bosses this run: 2."
- It also says when this run can't give a chest (hover to see why: today's chest from this dungeon already earned, or the daily limit reached), and when the chest for this run is already in your Treasure Bag.
- When real bosses there have rewards you don't have yet, the banner says so. Hover it to see them.
- In a raid it says Raider's Hoard and 10 TapCoins a boss (for when WoW: Forever opens raids).
- It updates while the window is open and is hidden outside dungeons and raids. It is part of the window, not a pop-up.

## Boss effects
- Six new back effects play behind your cat. Each is unlocked by a big boss kill, in real WoW or in Adventure:
  - Storm Aura: In WoW, kill Mekgineer Thermaplugg in Gnomeregan. Adventure: beat Ossirian the Unscarred in Ruins of Ahn'Qiraj.
  - Firelord's Blaze: In WoW, kill Emperor Dagran Thaurissan in Blackrock Depths. Adventure: beat Ragnaros in Molten Core.
  - Frostwhisper Chill: In WoW, kill Ras Frostwhisper in Scholomance. Adventure: beat Kel'Thuzad in Naxxramas.
  - Umbral Shroud: In WoW, kill Baron Rivendare in Stratholme. Adventure: beat Nefarian in Blackwing Lair.
  - Crusader's Radiance: In WoW, kill High Inquisitor Whitemane in Scarlet Monastery. Adventure: beat C'Thun in Ahn'Qiraj.
  - Verdant Wisps: In WoW, kill Princess Theradras in Maraudon. Adventure: beat Hakkar in Zul'Gurub.
- The first such kill always unlocks the effect. Wear it from Appearance like any effect. Cosmetic only.
- Each has a look of its own: a crackling ring of lightning with storm clouds, a crown of flames, ice shards and snowflakes, curling shadow smoke, a halo with a cross of light, and a leafy vine with glowing wisps.
- These unlocks are the one big moment that shows over your cat: "You unlocked Storm Aura" appears above it (over its level and XP text) with the effect playing behind it, then fades after about 5 seconds. Two unlocks at once show one after the other. Nothing else pops up. The "Popups on cat" setting turns it off.

## Art to build
- tools/art_specs_adv/boss_effects.txt: six back-effect drawings in the full sticker style (fx_storm_aura, fx_firelord, fx_frost_chill, fx_shadow_shroud, fx_holy_radiance, fx_verdant_wisps). Until they exist, the effects use simple glow stand-ins of their own (Art/adv/fx_boss_*.tga, made by tools/make_adv_fx.py), soft white shapes tinted like the other effects. When built, change the art field in BossEffects.lua (TCF.BOSS_EFFECTS).

## Enemies never cut off
- Enemies are no longer cut off by an invisible box: each one is drawn in a space that covers the whole fight scene, and is sized with room for its attacks and its fall when it dies.
- For the developer: UI_Adventure.lua slotGeometry gives every enemy's ModelScene twice the fight panel's size, centred on its slot and the ground line, so the panel's own (visible) edge is the only clip. The fit keeps 20% of the model's height free above it under the panel's top (FIT.ANIM_TOP); FIT.ANIM_SIDE / ANIM_WIDE give the sideways room the test checks. The old PlayerModel fallback's frame is 1.5x bigger with its camera 1.5x further back. tools/tests/test_adv_fit.py runs the real fit on a mock scene for every display.
- Review fix: the panel's visible edge clips too, so the animation room has to stay inside it. widthFit and verifyFit now keep the model at rest right of the cat and the whole animation envelope (animEnvelope: FIT.ANIM_SIDE / ANIM_WIDE) left of the panel's edge, sliding or shrinking the model. To keep the slide small the slots moved left: trash slots at baseX -30 - (n - i) * 106 (were -12 - (n - i) * 112), the boss at -70 (was -50). Median slide of the rightmost trash slot: 8 px; the largest slides are no bigger than before. test_adv_fit.py now checks the envelope against the panel's inner edge (4..524 plus 1.5 px rounding, top under 246).

## Adventure help
- The Help guide now says the right thing about losing: with Auto-advance on, a loss sends your cat back to the last trash pack; with it off, your cat drops back to an easier pack after 3 losses in a row.
- The next-zone tooltip says Auto-advance moves on 2 levels before a zone's level.

## Enemies above your cat's level (1.6.0)
- Fights count the level difference, like WoW (Adventure.lua TCF.AdvLevelMods, TCF.AdvEnemyLevel). Enemies up to 3 levels above the cat fight as before.
- For each level past 3: the cat's damage x0.94 (never under 5%), damage it takes x1.06, and it misses 5% + 2% for each level above 3 (7% at 4 levels, at most 60%). Damage over time ticks never miss. Below the cat: +1% damage a level, at most +5%.
- An enemy's level: the zone's lowest level (the "Levels 10-18" on the page) for its first packs, one more for every 2 levels of the pack's difficulty above the zone's first stage, so the last boss is 2-3 levels higher. Raids count as level 60: their difficulty above 60 is for gear.
- Why 3 free levels and not the formula from the first level: with the zone levels, Auto-advance enters zones 2 levels early and the cat often fights bosses 3-4 levels above it while it levels there. Counting from the first level cost 10-16% of all kills, 15-20% of boss kills and 3-4 times the defeats over 30 hours (Warrior, Mage, Rogue). From 4 levels, over 20 hours of Auto-advance from level 1 (Warrior, Mage, Rogue, Priest, Hunter, 2 runs each): kills x1.00, boss kills x0.995, defeats x1.18; every zone is reached at the same time except The Deadmines, now and then up to 20 minutes later (it is reached right after Wailing Caverns is cleared, not by level). A cat at each zone's Auto-advance level with typical gear: the same kills in 10 minutes and no defeats, in every zone and class (tools/balance.py --levels).
- The line in the fight panel's top-left corner (296x34, over the cat's side, above its bar) shows from 5 levels above: "Enemies here are 29 levels above your cat: it hits much less and takes far more damage." It is clear of every enemy's name and health bar (the boss slot's name starts right of it) and of the log and status line at the bottom (test_adv_levels.py checks the clearance).
- A level 31 cat with level 31 gear in Molten Core used to kill 60 to 85 enemies in 10 minutes; now it kills none and loses within 2 to 11 seconds. Travelling by hand is still free.
