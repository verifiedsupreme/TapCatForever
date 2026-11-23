# Main window

## Window size
- The main window can now be made bigger or smaller: drag the grip in its bottom-right corner. Everything inside grows or shrinks with it, and the top-left corner stays where it is.
- The size follows how far you drag, so just clicking the grip no longer changes it.
- The window always fits on your screen: on smaller screens the largest size is a little under 140%.
- Double-click the grip to go back to normal size.
- Settings > Cat and display has Window size - and + buttons too (5% a click, from 60% to 140%).
- The size is remembered. The compact window (below) remembers its own size, so making it bigger to read does not make the wide window too big.

## Fold away the character column
- A new cat button at the top, the one nearest the left column, folds away that column (your cat, gear slots, class and stats). The window gets narrower and the tabs slide left. Click it again to bring the column back.
- In the narrow window the Compendium is a book icon next to the layout button, and the Treasure Bag shows without its label.
- The Casino still uses the whole window: on that tab the window grows to the left, so the tabs stay where they are, and it goes back when you leave.
- With the column folded away, hovering an item on the Appearance, Shop, Gear or Professions page shows it on a small cat beside the window, so you can still try things on.
- Going to the Casino and back puts the window exactly where it was, even near the edge of the screen.
- The Gear page still says to click a slot around your cat to filter: open the column with the cat button to see the slots.
- Your choice is remembered.

## Compact window
- A new layout button (a little phone, between the cat button and the Compendium button) switches the main window to a compact layout: narrow and tall, about the shape of a phone screen. Click it again (it shows a wide window then) to go back.
- The tabs become big round buttons in two rows of five, each with its name under it and a tooltip. Quests shows how many are ready to hand in, as before. Achievements and Settings stay as the round icons by the title.
- Every page is shown smaller to fit the narrow window and works the same as before. The Casino is shown smaller still so the whole table fits.
- The character column has its own view: click the cat button, or the level line at the bottom, to see your cat, gear slots, class and stats. Click the cat button again, or any tab, to go back.
- A line at the bottom shows your class, level, title, Power and XP.
- Your TapCoins sit next to the Treasure Bag on the second row, so big numbers have room.
- The Shop's round button is a chest, so it doesn't look like the Treasure Bag next to it.
- Trying on items works here too: a small cat beside the window shows the item while you hover it.
- Text gets small in the compact window: drag the grip in the corner (or use Window size in Settings) to make the whole window bigger.
- Your choice is remembered. Leaving the compact window goes back to the wide window, with the character column open or folded as you left it.
- The What's new strip over the window takes the width of the narrow and compact windows, and grows taller for its text. If the taller strip no longer fits above the window, it goes below it.

## Tabs (1.6.0)
- The Casino is a text tab where Achievements was (second row, between Shop and Leaderboard); Achievements is the round achievement emblem by the title, next to Settings. No round Professions button any more: the Professions tab opens it.
- Header order: the cat (character column) button first, nearest the column it folds, then the layout (phone) button, then the Compendium, in all three layouts.

## For merging (not for players)
- Header buttons added by other parts: call `win:AddHeaderButton(button, placeFull)` after `TCF.UI.SetupWindowLayout(win)` (or put `{ frame = button, placeFull = fn }` in `win.headerExtras` before it). `placeFull(button)` anchors it in the full header; the narrow header puts it after the Compendium icon, the compact header after the Compendium button.
- Window size is stored in `db.ui.winScale` (full and narrow) and `db.ui.winScaleCompact` (compact).
- Tab numbers did not change (SelectTab(9) is still Achievements, 11 the Casino): UI.lua `win.tabOrder` gives where each text tab sits, `win.TAB_ACH` the icon tab.
- Window size sits in Settings > Cat and display, CB Row 6: a track that wants that spot must move it.

## What's new pop-up (1.6.0)
- The first time the window opens on 1.6.0 (once per account, db.newsSeen), a small box over the middle of the window shows six pictures with a few words each (Cat Casino, Resize your window, Animated dungeon sets, Professions level like WoW, Farm your favourite bosses, Party expeditions), the line "Multiplayer is still in the works: party death roll, rock paper scissors and the leaderboard may not work yet.", "Read the full patch notes" and Close. It is part of the window (never over the screen cat), and only shows when the player opens the window.
- Brand-new players skip it (they get the welcome tour). Later versions with a highlight keep the slim strip.
- For the developer: News.lua TCF.NEWS_POPUPS keys a version to its pop-up; pictures are Art/news/*.tga (256x128, 24-bit RLE) from tools/make_news_art.py (crops in tools/news_src, --review DIR crops the screenshots again).

## Review fixes (1.6.0)
- What's new pop-up: a nearly solid fill of its own inside the dialog border (the dialog backdrop alone let the page show through), a dark veil over the rest of the window while it is up, and it closes when the window closes (newsWatch OnHide).
- The news tiles are written with make_art.write_tga: 32-bit RLE, top-left origin, like every other picture in Art (PIL's TGA writer chose 24-bit and a bottom-left origin for some). test_news_popup.py checks the header.
