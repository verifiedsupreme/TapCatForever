# Your cats on every character (1.6.0)

## What players get
- The nine class cats belong to the account. Any character plays the account's cat of its class (or the one picked with the class buttons): level, XP, gear and bags, Treasure Bag, professions, look and cosmetics, Adventure (with farming), abilities and expeditions.
- A new character starts on the account's cat of its class.
- The first login on 1.6.0 puts every character's cats together, once, with one chat line: "Your cats are now shared by all your characters: each class has one cat, with everything your characters had."

## How cats are put together
- For each class the cat with the highest level is the base (ties: most XP; then the cat already in the account). It keeps its level, XP, worn gear, look, cosmetic slots, place in Adventure (zone, stage, farming, Auto-advance) and its other settings.
- The other cats of that class add: bag items (their worn gear goes to the bag; the bag counts worn copies already), unopened chests with their level stamps, cosmetics (copies added up) and where they came from, Adventure kills, boss kills and new stages, first kills (so no first-kill reward is paid twice), the furthest stage reached, and every ability learned.
- Professions: the business with the most Trade Gold earned is kept (its spots, helpers, tools, upgrades, gold). Every skill takes the highest of the cats, Renown the highest, materials are added up, and unlocks, milestones, hand speed, garden, First Aid, fishing and cooking upgrades and known dishes that any cat had stay.
- Expeditions under way all keep going. Two party expeditions under way on two characters: the second waits and takes the party slot when the first is claimed.
- Before 1.6.0 cosmetics belonged to the character: each of its cats gets all of them first (so every cat owns everything that character owned), then the cats are put together.
- Quests that count the cats (enemies, bosses, levels, new stages) keep the progress they had.
- A copy of every character's old cats stays in the save: TapCatForeverDB.preAccountBackup["Name-Realm"].
- A character that still has cats of its own when it logs in later (one played on an older version after the update) is put together the same way, with its own backup copy. The chat line comes only once.

## Still per WoW character
- Which cat it plays (db.class).
- The Daily Wares in the Shop: picked for that character's cat and refreshed per character, as before.
- Real WoW dungeon and raid chests: once a day per dungeon and once a week per raid for each character, as the game's lockouts are, and the run in progress (dungeonPaid, dungeonRun). "Up to 2 a day across your characters" is unchanged.
- How many times you killed each real WoW boss (realBosses), as the tooltips say "on this character".
- The once-a-day professions glitch (profGlitchDay), by design.
- The 1.5.4 care package flag. Each cat gets its white pieces once (classData[class].carePackage); a cat whose character already had its package is marked when it is merged.
- Already shared before: TapCoins, quests, achievements, class achievements, level-up rewards, settings and the screen cat's place (db.ui.point).

## Settings
- "Reset this character" is now "Reset your cats": all nine cats start over for every character (TapCatForeverDB.cats is cleared). TapCoins, quests and achievements are kept. The backup copy stays.

## For code
- TapCatForeverDB.cats = { classData, loadouts, looks, expeditions, oldItemSources, started, notice }. Core.lua's metatable sends db.classData, db.loadouts, db.looks and db.expeditions there (TCF.ACCOUNT_CATS). db.look is the look of the cat being played (TCF:LookOf(), TCF.VIRTUAL).
- AccountCats.lua: TCF:MergeAccountCats(sv), run first thing in InitDB. Quests.lua: TCF.QuestCatProgress / TCF.QuestCatRebase.
- The main harness's older sections log test characters in with _loginAs(name), which keeps a copy of the cats per test character, so those sections keep starting on fresh cats. The sharing itself is tested in tools/tests/test_account_cats.py.
