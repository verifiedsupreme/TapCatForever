# TapCatForever

Built for **World of Warcraft: Forever** (interface 16001). A small pixel-art cat lives on your WoW screen and taps its paws every time you press a key.
Every key press earns XP and TapCoins. Level the cat up, collect class-themed gear, and dress it as any of the nine classic classes.

![showcase](media/showcase.png)

## Features
- **Tapping cat.** Keys on the left half of the keyboard tap the left paw, the rest tap the right paw. Mouse clicks count too (this can be turned off). The cat blinks, makes a "focus" face during a Paw Frenzy (7+ taps a second) and sparkles when it gets loot.
- **9 classes.** Warrior, Paladin, Hunter, Rogue, Priest, Shaman, Mage, Warlock and Druid. Each class has its own gear (head, chest, back, main hand, off hand) in five material tiers, from Rusty or Novice's up to Titanforged, Ashbringer, Dragonstalker and the rest. Each class also has its own effects, and keeps its own saved outfit.
- **612 cosmetics** in Common, Uncommon, Rare, Epic and Legendary. They include fur colours (with animated Prismatic and Spectral furs), fur patterns, accessories, party hats, crowns, fishing poles and more. Legendary head and chest pieces shimmer.
- **Progression.** Levels and titles (Kitten up to Eternal Tapper), a lifetime tap counter, TapCoins (1 per 10 taps, plus level-up rewards and a daily login treat with a streak bonus).
- **Loot.** Random drops while you tap, three kinds of treasure chest, free chest keys every 5 and every 20 levels, and duplicates salvaged into TapCoins.
- **Daily shop.** Six items a day, with a re-roll option.
- **43 achievements**, with TapCoin rewards and exclusive cosmetics such as the Crown of the Tapmaster.
- **Shared progression.** Every character on the account shares the same level, coins, collection and achievements.
- **Fits around your UI.** Drag it anywhere, scale it from 0.3x to 3x, change its opacity, hide every counter (cat-only mode), and make it click-through when locked.

## Install
Copy the `TapCatForever` folder to `World of Warcraft\_forever_\Interface\AddOns\`, or install it through the CurseForge app with your Forever installation selected.

## Usage
- Left-click the cat to pet it. Right-click it to open the wardrobe, shop, achievements and settings. Drag it to move it.
- Ctrl + mouse wheel over the cat resizes it. Shift + mouse wheel changes its opacity.
- `/tapcat` (or `/tcf`) opens the window. Subcommands: `show`, `hide`, `toggle`, `lock`, `unlock`, `reset`, `scale <n>`, `stats`.
- Minimap button: left-click opens the window, right-click shows or hides the cat.

## Development
- `python3 tools/make_art.py` regenerates every texture in `Art/` and `ArtData.lua`.
- `python3 tools/preview.py out.png` renders a sheet of outfits.
- `python3 tools/test_harness.py` runs the addon against a mocked WoW API (needs `pip install lupa`).
- Releases: pushing a tag like `v1.0.1` runs `.github/workflows/release.yml`, which packages the addon and uploads it to CurseForge.
