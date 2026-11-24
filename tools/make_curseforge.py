#!/usr/bin/env python3
"""Writes the CurseForge page text in three forms from one source, so they never drift apart:
CURSEFORGE.md (Markdown, starting with the logo, ready to paste), CURSEFORGE.html (for the HTML editor) and
CURSEFORGE.txt (plain text to paste into the WYSIWYG editor).

usage: python3 tools/make_curseforge.py
"""
import html, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LOGO = "https://raw.githubusercontent.com/verifiedsupreme/TapCatForever/main/media/logo.png"
LOGO_SMALL = "https://raw.githubusercontent.com/verifiedsupreme/TapCatForever/main/media/logo_small.png"   # the page header
ISSUES = "https://github.com/verifiedsupreme/TapCatForever/issues"

SUMMARY = ("A cartoon cat taps along with every key you press. Level a cat for each class to 60, dress it in real "
           "WoW gear and animated dungeon sets, fight through dungeons and raids, craft gear, send party expeditions and try the cat Casino. "
           "Made for WoW: Forever.")

TITLE = "TapCatForever"
INTRO_BOLD = "A little cartoon cat lives on your screen and taps its paws every time you press a key."
INTRO = (" Every keystroke you already make in World of Warcraft earns your cat XP and TapCoins, and behind it "
         "is a whole collection game: real WoW gear, class abilities, an idle Adventure through Azeroth's dungeons "
         "and raids, class professions that craft real gear, loot chests and hundreds of things to collect.")
PERSONAL = ("This is my first addon, and I'm so glad you're here. I update it often, so keep it up to date for the "
            "newest features and fixes. If you have an idea or find a bug, I'd love to hear it: type /tcf feedback in "
            "game or use the link at the bottom of this page.")
INTRO2 = "It never touches your gameplay. It just watches your key presses and makes them a little more fun."

MEDIA = "https://raw.githubusercontent.com/verifiedsupreme/TapCatForever/main/media/"

# The fun part first: what your cat gets up to, one card each (picture, title, a few lines)
CARDS = [
    ("art_cat.png", "A cat that taps with you",
     "Every key you press, every click and every spell you cast, your cat taps its paws along. Left paw on A, right paw on D. "
     "It pulls faces, bursts hearts and stars from its paws, and quietly earns XP and TapCoins while you play the real game."),
    ("art_adventure.png", "Nine cats, one adventure",
     "One cat for every class, each levelling from 1 to 60 with its own real WoW gear and abilities. Send it through Elwynn Forest, "
     "the Deadmines, Molten Core and all the way to Naxxramas: real bosses, real loot tables, bosses you can farm, all while you play."),
    ("art_sets.png", "Dress it up",
     "Hundreds of hats, capes, skins and tap effects, eleven animated dungeon sets with flames, frost and stars, and real gear that "
     "shows on your cat. Shift-click anything to try it on first. The rarest skins drop from Ragnaros, Nefarian and Kel'Thuzad."),
    ("art_business.png", "Run a business",
     "Mining, skinning or tailoring for your class, with spots, helpers and upgrades that work even while you're offline. Craft real "
     "gear, unlock herbalism, first aid, fishing and cooking, and sell up for Renown to grow even faster."),
    ("art_garden.png", "Grow a garden",
     "26 real Classic herbs from Peacebloom to Icecap, a different seed in every plot, and Bramble the gardener, who harvests and "
     "replants while you're away and trains from Apprentice to Master. Lucky harvests bring Swiftthistle, Wildvine and Black Lotus."),
    ("art_potions.png", "Brew potions",
     "Turn your herbs into 17 classic elixirs and flasks, from Elixir of Lion's Strength to Flask of the Titans, and drink them for "
     "more damage, health, XP or gold. They stack with your Well Fed food."),
    ("art_casino.png", "The cat casino",
     "Lucky Paws slots, blackjack, a death roll in a cosy tavern and rock paper scissors (best of 1, 3 or 5) on a snowy mountaintop. Play the house cat, "
     "or challenge a friend in your party for TapCoins."),
    ("art_friends.png", "Better with friends",
     "Group up with friends who have the addon: their cats sit beside yours, your taps count up to 50% more, you can send your cats "
     "on party expeditions together, check out each other's cats and climb the realm leaderboard."),
    ("art_window.png", "Your window, your way",
     "A big window with your cat and its gear, fold the character panel away, or switch to a phone-sized view with big round buttons. "
     "Quests, achievements, chests with a loot reel, and a Compendium of every item and how to get it."),
]

# the newest update: its version and a few highlights
LATEST = ("1.7", [
    "Professions 2.0: work your spots by hand for rare finds (Black Diamond, Black Dragonscale, Righteous Orb and more), sparkling glints worth 5 times the reward, and stashes, rich veins and patrols to react to.",
    "Named helpers with their own traits who level up as they work, specializations at 225 with daily crafts like Mooncloth and Arcanite, and a guild for every craft with work orders and seven ranks up to a Grand Master title.",
    "Masterwork gear: any crafted piece can come out better than the recipe.",
    "A Renown shop: every sale for Renown now also gives Renown points to spend on sharper tools, a keener eye, busier helpers, more work orders and more Masterworks.",
    "11 legendary crafted sets with their own animated effects and titles, from the Mooncloth Regalia and Sulfuron Forgemaster to Pinchy's Wish and the Feast of the Ages. They take a long, long time to make.",
    "A Profession Bag for every material, with tabs, what each one is for, and bigger bags to buy with TapCoins.",
    "TapCoins are orange now, so you can tell them from gold at a glance.",
    "Earlier in 1.6: tapping and petting faces, a deep Herbalism with 17 potions, rock paper scissors best of 5, Happy Purrs, class-smart gear, and multiplayer death rolls and leaderboards.",
])

# big moments from earlier updates, one line each
HISTORY = [
    ("1.6", "The cat Casino with death rolls and rock paper scissors against friends, animated cosmetic sets, tapping and petting faces, a deep Herbalism with potions, and your cats shared by every character on your account."),
    ("1.5", "Class professions that craft real gear, real legendaries, party cats with a tap bonus, a fishing dock, 33 new skins, the Compendium, party expeditions and the realm leaderboard."),
    ("1.4", "Every zone filled with its real Classic creatures and bosses, death animations and floating damage numbers."),
    ("1.3", "Hand-drawn Adventure backgrounds for all 28 zones, the chest opening reel and spell effects in fights."),
    ("1.2", "The cartoon cat, a drawing for every visible item, real WoW gear with real stats, Adventure through Azeroth, expeditions, professions and cat skins."),
]

GETTING_STARTED = ("Install, log in, and the welcome tour shows you around. Right-click the cat to open the main window. "
                   "Start in the Adventure tab, and check the Treasure Bag whenever you earn a chest. After a big update, "
                   "a short What's new note appears at the top of the window.")

COMMANDS = [
    ("/tcf or /tapcat", "open the main window"),
    ("/tcf compendium", "every item and how to get it"),
    ("/tcf news", "patch notes"),
    ("/tcf top", "the Leaderboard tab"),
    ("/tcf feedback", "report a bug or suggest an idea"),
    ("/tcf welcome", "show the welcome tour again"),
    ("/tcf bag", "open the Treasure Bag"),
    ("/tcf show, /tcf hide, /tcf toggle", "show or hide the cat"),
    ("/tcf lock, /tcf unlock", "lock the cat in place"),
    ("/tcf reset", "move the cat back to the bottom middle of the screen"),
    ("/tcf scale 0.3-3", "resize the cat"),
    ("/tcf stats", "your totals"),
]

FAQ = [
    ("Does it change how I play?", "No. It only listens to your key presses and mouse clicks and never presses anything for you."),
    ("What counts as a tap?", "Every key press (movement, abilities, everything except typing in chat), every mouse click, and your spell casts."),
    ("Can I turn off the sounds, chat messages or chest animation?", "Yes, all of them are in Settings (right-click the cat, then the Settings tab). Sounds and chat messages start off."),
    ("Where are the patch notes?", "In Settings > Patch notes, or type /tcf news."),
    ("Does it send anything about me?", "Only if you turn on Share my cat's progress in Settings > Help and info, which is off by default. Then your character's name and realm, cat class, cat level, the level of each of your class cats, total taps, achievements earned, Adventure zones cleared, Trade Gold earned, your best profession skills and addon version are sent to other TapCatForever players who turned it on when you are in a party, raid or guild with them (and on an addon channel where the game allows it), and they see them on the leaderboard, passed between players inside the game. Other addons in your group or guild could read what is shared. The option is for your whole account, and since taps and achievements are shared between your characters, other players may be able to tell your characters on the same realm belong together. When you play death roll or rock paper scissors with a friend, your addon sends the challenge, the bet, the rolls or the locked-in picks to your party or raid. When you invite your group on a party expedition or answer an invite, it sends the invite or your answer, the cats you picked and their Power to your party or raid. When the developer asks, it also answers with your addon version, cat class, cat level, zones cleared and TapCoins. Nothing else is sent, and nothing goes over the internet."),
    ("Can I start over?", "Settings has \"Reset this character\" and \"Reset ALL progress\"."),
]

FEEDBACK = ("Found a bug or have an idea? Type /tcf feedback in game, leave a comment here, or open an issue on GitHub "
            "({}). If you can, include the error text (type /console scriptErrors 1 to see errors).")


def txt():
    o = [TITLE.upper(), "", INTRO_BOLD + INTRO, "", INTRO2, "", PERSONAL, "", "WHAT YOUR CAT GETS UP TO", ""]
    for img, head, text in CARDS:
        o += [head, text, ""]
    o += ["WHAT'S NEW IN {}".format(LATEST[0]), ""]
    o += ["• " + i for i in LATEST[1]]
    o += ["", "EARLIER HIGHLIGHTS", ""]
    o += ["• {}: {}".format(v, t) for v, t in HISTORY]
    o += ["", "Getting started", "", GETTING_STARTED, "", "Slash commands", ""]
    o += ["• {}: {}".format(c, d) for c, d in COMMANDS]
    o += ["", "FAQ", ""]
    for q, a in FAQ:
        o += [q, a, ""]
    o += ["Feedback and bugs", "", FEEDBACK.format(ISSUES)]
    return "\n".join(o) + "\n"


def md():
    # starts with the logo: the whole file is pasted into CurseForge's Markdown editor as it is
    o = ["![TapCatForever]({})".format(LOGO_SMALL), "",
         "### " + INTRO_BOLD, "", INTRO.strip() + " " + INTRO2, "", "*" + PERSONAL + "*", "",
         "---", "", "## What your cat gets up to", ""]
    # cards: a picture beside each (420x260, cut from the game's own screens), in a table so it reads like a web page
    o += ["| | |", "|:---:|:---|"]
    for img, head, text in CARDS:
        pic = "![{0}]({1}{2})".format(head, MEDIA, img) if img else ""
        o.append("| {} | **{}**<br>{} |".format(pic, head, text))
    o += ["", "---", "", "## What's new in {}".format(LATEST[0]), ""]
    o += ["- " + i for i in LATEST[1]]
    o += ["", "Full patch notes are in the game: Settings > Patch notes, or type `/tcf news`.", "",
          "### Earlier highlights", ""]
    o += ["- **{}**: {}".format(v, t) for v, t in HISTORY]
    o += ["", "---", "", "## Getting started", "", GETTING_STARTED, "", "## Slash commands", ""]
    o += ["- `{}`: {}".format(c, d) for c, d in COMMANDS]
    o += ["", "## FAQ", ""]
    for q, a in FAQ:
        o += ["**{}**".format(q), a, ""]
    o += ["## Feedback and bugs", "", FEEDBACK.format("[{0}]({0})".format(ISSUES))]
    return "\n".join(o) + "\n"


def h(s):
    return html.escape(s, quote=False)


def htm():
    o = ['<p style="text-align:center"><img src="{}" alt="TapCatForever" width="320" /></p>'.format(LOGO_SMALL),
         "<h3>{}</h3>".format(h(INTRO_BOLD)), "<p>{} {}</p>".format(h(INTRO.strip()), h(INTRO2)),
         "<p><em>{}</em></p>".format(h(PERSONAL)), "<hr />", "<h2>What your cat gets up to</h2>", "<table>"]
    for img, head, text in CARDS:
        pic = '<img src="{}{}" alt="{}" width="420" />'.format(MEDIA, img, h(head)) if img else ""
        o.append('<tr><td style="text-align:center">{}</td><td><strong>{}</strong><br />{}</td></tr>'.format(pic, h(head), h(text)))
    o += ["</table>", "<hr />", "<h2>What's new in {}</h2>".format(h(LATEST[0])), "<ul>"]
    o += ["<li>{}</li>".format(h(i)) for i in LATEST[1]]
    o += ["</ul>", "<p>Full patch notes are in the game: Settings &gt; Patch notes, or type <code>/tcf news</code>.</p>",
          "<h3>Earlier highlights</h3>", "<ul>"]
    o += ["<li><strong>{}</strong>: {}</li>".format(h(v), h(t)) for v, t in HISTORY]
    o += ["</ul>", "<hr />", "<h2>Getting started</h2>", "<p>{}</p>".format(h(GETTING_STARTED)), "<h2>Slash commands</h2>", "<ul>"]
    o += ["<li><code>{}</code>: {}</li>".format(h(c), h(d)) for c, d in COMMANDS]
    o += ["</ul>", "<h2>FAQ</h2>"]
    for q, a in FAQ:
        o += ["<p><strong>{}</strong><br />{}</p>".format(h(q), h(a))]
    o += ["<h2>Feedback and bugs</h2>",
          "<p>{}</p>".format(h(FEEDBACK).format('<a href="{0}">{0}</a>'.format(ISSUES)))]
    return "\n".join(o) + "\n"


if __name__ == "__main__":
    assert len(SUMMARY) < 256, len(SUMMARY)
    for name, fn in (("CURSEFORGE.txt", txt), ("CURSEFORGE.md", md), ("CURSEFORGE.html", htm)):
        open(os.path.join(ROOT, name), "w", encoding="utf-8").write(fn())
    print("summary:", len(SUMMARY), "characters")
