# Party track notes

## Class achievements
- The Achievements tab has two views: Account (the achievements you know, shared by every character) and This class.
- In This class, every class's cat has its own 23 achievements: levels 10 to 60, Elwynn Forest and Westfall, Adventure dungeons and raids cleared, every ability learned, a full Rare set and a full Epic set worn, crafting skill 150 and 300, five crafted pieces worn at once, expeditions finished and party expeditions finished.
- Pick a class with the class icons at the bottom of the page to see its progress. Hover a row for the details.
- Each class earns each one once for your whole account, so an alt of the same class can't earn it again.
- Rewards are a few TapCoins (595 for all 23 of one class) and a chest for that class's cat, which goes straight into that cat's own Treasure Bag.
- Level 60 with a class also gives that class's Legendary main hand look, on every character. It is labelled Cosmetic only: it changes how your cat looks, not its Power.
- Already played a lot? At login your cats get credit for what they have already done, with one chat line.
- Expeditions count for every cat that went, from this update on.

## Party expeditions
- In a party or raid with friends who have TapCatForever, open Expeditions and pick Party (top right).
- Choose your cats (up to 3; with none picked your current cat goes), a dungeon or raid, a length (15 min, 30 min, 1 h, 2 h or 4 h) and a difficulty (Normal, Hard or Heroic), then press Invite my group.
- Your friends get a small invite just above their cat: "<Name> invites your cat: <place>, 30 min, Hard" with Accept and Decline. It goes away after 60 seconds, which counts as a no. In combat it shrinks to a smaller box with the same buttons, so it never runs out unseen. It is also shown in the Party view, where you can pick more cats before you accept.
- It sets off as soon as everyone has answered, or after 60 seconds with at least one player. The one who invited can also press Start now, or Call off. Up to 5 players go.
- If your group can't get addon messages for a while (in combat in an instance, for example), it sets off as soon as they can, up to a few minutes later. Nobody ends up on an expedition the others don't know about.
- Everyone's cats add up their Power. A harder difficulty and more players need more Power. The Party view shows what each place needs and what it gives.
- Once it has set off it keeps going for everyone, even if the group breaks up or someone logs out. Everyone gets the same result.
- Each player claims their own rewards with Claim: XP for each cat that went, a few TapCoins, chest rolls (one per hour away, part of one for shorter trips; one more with 3 or more players) and +10% XP and TapCoins for every other player. Heroic also has a small chance of a Dungeon Chest or a Raider's Hoard. A failure brings half the XP and a few TapCoins.
- Party expeditions have their own slot: your two solo expedition slots stay free. A cat on a party expedition can't go on a solo one (or into Adventure) until it is back.
- One invite at a time. Party members need the newest TapCatForever to join. Members on an older version don't hold the invite up.
- Party expeditions count for the class achievements Better Together and Party Regular, and as expeditions for the expedition ones.

## Numbers (for checking)
- Chance of success: 5% with no Power at all, rising to 97% at the Power needed.
- Power needed for the best odds: the solo expeditions' scale by zone difficulty (about 1,300 for Ragefire Chasm up to 12,500 for Naxxramas), times 1 / 1.6 / 2.5 for Normal / Hard / Heroic, times 1.5 with 2 players up to 3 with 5.
- TapCoins: 10 an hour on Normal with 2 players (11 with the group bonus), at most about 24 an hour (Heroic, 5 players). XP: 5 per minute away for each cat, more on harder difficulties.

## Art to build
- None. The party slot uses a WoW icon.

## Merge notes (for the loot track)
- Loot's `TCF:AwardChest(key, source, force, class, level)` puts a chest in a class cat's bag. Party expeditions already pass the first cat that went as `class`, and class achievements pass their class (ignored before the merge).
- After the merge, class achievements can hand a chest straight to its class's bag (`AwardChest(a.chest, label, nil, class)` whenever `db.classData[class]` exists) and drop the `db.classAchPending` waiting list, or keep it only as a fallback for classes this character hasn't played.

## Decisions to confirm
- Party expeditions can go to any dungeon or raid, whatever your Adventure progress. The chance now starts at 5% with no Power (it was 20%), so a group with no progress can't farm Heroic raids. Limiting places to ones you have reached in Adventure would be the stricter option.
- A veteran account gets every class achievement it already earned at its first login after the update, with one chat line (for an account with every class at 60 and every raid cleared: about 5,355 TapCoins and dozens of chests, among them 18 Heroic Caches, 18 Raider's Hoards and 27 Dungeon Chests). Worth deciding together with the loot track's care package.
