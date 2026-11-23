# Loot

## Every cat has its own Treasure Bag
- Chests now belong to the class cat that earned them. Each cat has its own Treasure Bag.
- Chests earned while you play a class go to that cat. Level-up chests go to the cat that levelled, even when expedition XP levelled it while you played another cat.
- Professions helpers and fishing buddies put their chests in their own cat's bag.
- Expedition chests go to a cat that went: the cat you are playing if it was in the party, otherwise the party's first cat. Any other chest you earn while claiming (a level-up, an achievement) still goes to its own cat.
- Bought chests are for the cat you are playing.
- Chests you already had move once to the cat you are playing when you log in, stamped with its level.

## Chests are stamped with a level
- Every chest is stamped with the level of the cat that earned it ("Lv 20").
- A chest holds gear for its level, even if you open it much later. A level 20 chest opened at level 40 still holds level 20 gear.
- Gear is never more than 3 levels above the chest's level. When there is nothing of the rolled quality near that level, you get the next quality down instead.
- Raid gear only comes from chests of level 55 and up. A real Legendary only from level 60 chests.
- The opening reel shows gear for the chest's level.

## Treasure Bag
- One row per kind of chest and level, for example "Lv 20". How many you have is on the chest's icon. The level turns grey once your cat is well past it.
- Five rows a page, with page buttons (or the mouse wheel) when there are more.
- Hover a row for "Holds gear for about level 20", that chest's odds and where that kind of chest comes from.
- Open opens one chest of that row's level. If that level is already used up, it opens nothing. All opens every chest of that kind. Open everything empties this cat's bag.
- The title says whose bag it is, and a line lists chests waiting in your other cats' bags.

## A care package for players who were already playing
- The first time a character that played before this update logs in, every class cat on it that has been played gets a plain white piece for each empty gear slot it can use at its level.
- The pieces go into that cat's gear bag. Nothing is equipped for you.
- Once per account there are also 150 TapCoins.
- One chat line says what you got. No pop-up, and it never comes twice.
- Brand-new characters and accounts don't get one.

## Item sets and set bonuses
- 171 real Classic item sets are in the game, from Defias Leather and Embrace of the Viper to Battlegear of Valor, Zul'Gurub, Ahn'Qiraj and tier 1 to 3, plus crafted sets like Devilsaur, Volcanic and Bloodvine.
- Wear enough pieces of a set and its set bonuses count: they add to Power, Adventure and expeditions, and Equip best and every upgrade check include them.
- Bonuses a cat can't use (procs, class spell changes, resistances, defense, dodge, block value, mana per 5 sec) are shown in grey with "(no effect on your cat)". They never count as an active bonus.
- The gear tooltip shows the set: its name with how many pieces your cat wears, every piece (worn in white, the rest in grey) and the bonuses (active in green, not yet in grey). On a party member's cat it counts the pieces that cat wears.
- Comparing gear now also says when a swap gains or loses a set bonus.
- The Compendium has a new Item Sets list: every set with how many pieces you have, a class filter, and Owned for complete sets. Hover a set for its pieces and bonuses.

## Where every cosmetic came from
- Skins, effects, tap effects and other cosmetics now remember where you got them.
- Hover one in the Appearance tab or the Compendium: "Got it from: Heroic Cache, 3 days ago".
- When you got another copy later, a second line says where the latest one came from.
- Sources include chests, Adventure bosses, real dungeon runs, expeditions, quests, achievements, crafting, the Shop and the Appearance tab.
- Cosmetics you had before this update say "Got before this was tracked". Another copy of one later adds "Latest one from: ..." under it.
- The cosmetics every cat starts with say "Got it from: Starter cosmetic".

## Cosmetics belong to each class's cat (1.6.0)
- Every class's cat has its own collection: skins, furs, patterns, tap effects, hats, capes, effects, accessories, racial pieces, set pieces and crafted cosmetics. Its look was already its own.
- After the update every cat owns everything your characters owned, with where it came from, so nobody loses anything (the cats are the account's since the same update: notes/cats.md).
- New cosmetics go to the cat being played (chests, Adventure drops, real WoW bosses, quests, achievements, the Shop with its skins and racial piece). Crafting, expeditions and class achievements give it to the cat that earned it. Duplicates are salvaged per cat.
- The Appearance tab, the Shop (owned marks, Heroic Cache skins), the Compendium, try on and "Got it from" show the cat being played.
- Achievements that count cosmetics count the best cat's collection (decided so switching cats never loses progress and no achievement goes backwards). The racial heritage one counts different pieces on any cat.
- For code: `classData[class].owned`; `db.owned` stands for the collection of `TCF:OwnerClass()` (the cat a crafting job, a claimed expedition or `TCF:WithOwner` is for, else the cat being played). `TCF:Owned(class)` reads any cat's. `classData[class].itemSources` keeps where each came from; the old per-character records are still read as a fallback.

## For the merge (not for players)
- `db.keys` is a stand-in for the current cat's bag: reading or writing `db.keys[key]` works, but `pairs(db.keys)` sees nothing in Lua 5.1. Code or tests that sum every chest use `TCF:ChestCount(class)` or `pairs(TCF:ChestCounts(class))`. On t-party this means two test helpers (checked on a scratch merge of t-loot and t-party: both party tests then pass, and so do all loot tests):
  - tools/tests/test_party_classach.py: `local function keys() local n = 0; for _, cl in ipairs(TCF.CLASSES) do n = n + TCF:ChestCount(cl.key) end; return n end` (every cat's bag, since each cat now holds its own chests).
  - tools/tests/test_party_expeditions.py: `function _keys() return TapCatForever:ChestCount() end`.
- `TCF:AwardChest(key, source, force, class, level)`: pass the class for a chest meant for a cat you might not be playing (party: party expedition chests, class achievement chests, which could then drop the `classAchPending` queue). Cosmetics given outside `GrantItem`/`GrantSkin` should call `TCF:NoteItemSource(id, source)`, or they show "Got before this was tracked".
- Gear.lua `CombatStats`: loot no longer touches the return table (ItemSets.lua adds `sets` by wrapping it), so it merges cleanly with t-advfx's `attack`/`shot`/`school` line.
- UI.lua `TCF:CreateBag` and `TCF:OpenAllChests` are replaced by TreasureBag.lua (loaded after UI.lua). Changes made to the old bag in UI.lua on other branches have no effect: move them to TreasureBag.lua, then delete the old functions.
