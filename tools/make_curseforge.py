#!/usr/bin/env python3
"""Writes the CurseForge page text in three forms from one source, so they never drift apart:
CURSEFORGE.md (Markdown, with the summary), CURSEFORGE.html (for the HTML editor) and
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
    ("tile_cats.png", "A cat that taps with you",
     "Every key you press, every click and every spell you cast, your cat taps its paws along. Left paw on A, right paw on D. "
     "It pulls faces, bursts hearts and stars from its paws, and quietly earns XP and TapCoins while you play the real game."),
    ("tile_farm.png", "Nine cats, one adventure",
     "One cat for every class, each levelling from 1 to 60 with its own real WoW gear and abilities. Send it through Elwynn Forest, "
     "the Deadmines, Molten Core and all the way to Naxxramas: real bosses, real loot tables, bosses you can farm, all while you play."),
    ("tile_sets.png", "Dress it up",
     "Hundreds of hats, capes, skins and tap effects, eleven animated dungeon sets with flames, frost and stars, and real gear that "
     "shows on your cat. Shift-click anything to try it on first. The rarest skins drop from Ragnaros, Nefarian and Kel'Thuzad."),
    ("tile_professions.png", "Run a business",
     "Mining, skinning or tailoring for your class, with spots, helpers and upgrades that work even while you're offline. Craft real "
     "gear, unlock herbalism, first aid, fishing and cooking, and sell up for Renown to grow even faster."),
    ("tile_casino.png", "The cat casino",
     "Lucky Paws slots, blackjack, a death roll in a cosy tavern and rock paper scissors on a snowy mountaintop. Play the house cat, "
     "or challenge a friend in your party for TapCoins."),
    ("tile_party.png", "Better with friends",
     "Group up with friends who have the addon: their cats sit beside yours, your taps count up to 50% more, you can send your cats "
     "on party expeditions together, check out each other's cats and climb the realm leaderboard."),
    ("tile_window.png", "Your window, your way",
     "A big window with your cat and its gear, fold the character panel away, or switch to a phone-sized view with big round buttons. "
     "Quests, achievements, chests with a loot reel, and a Compendium of every item and how to get it."),
]

# the newest update: its version and a few highlights
LATEST = ("1.6", [
    "Gear that fits your class: Equip best now picks Spell Power and Intellect for casters, Strength for Warriors and Paladins and Agility for Hunters and Rogues, like WoW.",
    "Shift-click any item to try it on your cat before you wear or buy it.",
    "Multiplayer works: death roll and rock paper scissors with a friend, party cat profiles with their taps, and a realm leaderboard that fills in from your party.",
    "A bigger phone view with a fold-away tab menu, a tidier header, and profession buttons that are easy to hit.",
    "Your x3 profession upgrades and Renown now multiply the ore, leather and cloth you gather too.",
    "The cat Casino, animated cosmetic sets, a resizable window, and your cats shared by every character on your account.",
])

# big moments from earlier updates, one line each
HISTORY = [
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
    o = ["# CurseForge page text", "", "## Summary (under 256 characters)", "", SUMMARY, "", "## Description", "",
         "![TapCatForever]({})".format(LOGO_SMALL), "",
         "### " + INTRO_BOLD, "", INTRO.strip() + " " + INTRO2, "", "*" + PERSONAL + "*", "",
         "---", "", "## What your cat gets up to", ""]
    # cards: a picture beside each, in a table so it reads like a web page
    o += ["| | |", "|:---:|:---|"]
    for img, head, text in CARDS:
        o.append("| ![{0}]({1}{2}) | **{0}**<br>{3} |".format(head, MEDIA, img, text))
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
        o.append('<tr><td style="text-align:center"><img src="{}{}" alt="{}" /></td><td><strong>{}</strong><br />{}</td></tr>'
                 .format(MEDIA, img, h(head), h(head), h(text)))
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
