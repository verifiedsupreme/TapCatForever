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

## Adventure help
- The Help guide now says the right thing about losing: with Auto-advance on, a loss sends your cat back to the last trash pack; with it off, your cat drops back to an easier pack after 3 losses in a row.
- The next-zone tooltip says Auto-advance moves on 2 levels before a zone's level.
