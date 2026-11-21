#!/usr/bin/env python3
"""
Builds GearData.lua from real Classic (Vanilla) item data:
  - wow-classic-items (MIT, npm): items, stats, which boss/zone drops them, drop chances
  - wago.tools DB2 exports: Creature.csv (creature model display IDs),
    JournalInstance.csv (dungeon/raid artwork file IDs)

Usage: python3 tools/make_gear.py <data-dir>
  <data-dir> must contain package/data/json/data.json, Creature.csv, JournalInstance.csv,
  JournalEncounterCreature.csv
"""
import csv, json, os, re, sys, collections

DATA = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "GearData.lua")

# ------------------------------------------------------------------ tiers
# key, name, zone area id, min level, max level, difficulty, raid, journal instance id, final boss, trash names
# difficulty is the internal level used for enemy scaling (raids go past 60).
TIERS = [
    ("elwynn",   "Elwynn Forest",            12,   1, 10, 6,   False, None, "Hogger", ["Kobold Tunneler", "Murloc Forager", "Prowler", "Defias Thug"]),
    ("westfall", "Westfall",                 40,  10, 18, 14,  False, None, "Foe Reaper 4000", ["Harvest Watcher", "Riverpaw Gnoll", "Defias Pathstalker", "Coyote"]),
    ("rfc",      "Ragefire Chasm",           2437, 13, 18, 16,  False, 226, "Taragaman the Hungerer", ["Ragefire Trogg", "Searing Blade Cultist", "Molten Elemental"]),
    ("wc",       "Wailing Caverns",          718, 17, 24, 20,  False, 240, "Mutanus the Devourer", ["Deviate Raptor", "Druid of the Fang", "Deviate Stalker"]),
    ("dm",       "The Deadmines",            1581, 17, 26, 21, False, 63,  "Edwin VanCleef", ["Defias Miner", "Defias Pirate", "Goblin Engineer"]),
    ("sfk",      "Shadowfang Keep",          209, 22, 30, 25,  False, 64,  "Archmage Arugal", ["Shadowfang Moonwalker", "Haunted Servitor", "Shadowfang Darksoul"]),
    ("bfd",      "Blackfathom Deeps",        719, 24, 32, 27,  False, 227, "Aku'mai", ["Blackfathom Myrmidon", "Twilight Acolyte", "Aku'mai Fisher"]),
    ("stocks",   "The Stockade",             717, 24, 32, 28,  False, 238, "Bazil Thredd", ["Defias Convict", "Defias Inmate", "Defias Captive"]),
    ("gnomer",   "Gnomeregan",               721, 29, 38, 32,  False, 231, "Mekgineer Thermaplugg", ["Leper Gnome", "Mechanized Sentry", "Dark Iron Agent"]),
    ("rfk",      "Razorfen Kraul",           491, 29, 38, 33,  False, 234, "Charlga Razorflank", ["Razorfen Defender", "Death's Head Acolyte", "Kraul Bat"]),
    ("sm",       "Scarlet Monastery",        796, 30, 45, 38,  False, 316, "High Inquisitor Whitemane", ["Scarlet Monk", "Scarlet Wizard", "Scarlet Champion"]),
    ("rfd",      "Razorfen Downs",           722, 37, 46, 41,  False, 233, "Amnennar the Coldbringer", ["Skeletal Shadowcaster", "Death's Head Necromancer", "Withered Quilguard"]),
    ("uld",      "Uldaman",                  1337, 41, 51, 45, False, 239, "Archaedas", ["Stone Steward", "Shadowforge Ambusher", "Earthen Rocksmasher"]),
    ("zf",       "Zul'Farrak",               1176, 42, 48, 46, False, 241, "Chief Ukorz Sandscalp", ["Sandfury Blood Drinker", "Sandfury Soul Eater", "Zul'Farrak Zombie"]),
    ("mara",     "Maraudon",                 2100, 46, 55, 49, False, 232, "Princess Theradras", ["Celebrian Dryad", "Constrictor Vine", "Poison Sprite"]),
    ("st",       "Sunken Temple",            1477, 50, 56, 52, False, 237, "Shade of Eranikus", ["Atal'ai Witch Doctor", "Nightmare Wyrmkin", "Hukku's Voidwalker"]),
    ("brd",      "Blackrock Depths",         1584, 52, 60, 56, False, 228, "Emperor Dagran Thaurissan", ["Anvilrage Guardsman", "Fireguard", "Shadowforge Senator"]),
    ("brs",      "Blackrock Spire",          1583, 55, 60, 58, False, 229, "General Drakkisath", ["Blackhand Dragon Handler", "Rage Talon Dragonspawn", "Smolderthorn Shadow Priest"]),
    ("dim",      "Dire Maul",                2557, 56, 60, 59, False, 230, "Immol'thar", ["Gordok Brute", "Warpwood Treant", "Eldreth Spectre"]),
    ("scholo",   "Scholomance",              2057, 58, 60, 60, False, 246, "Darkmaster Gandling", ["Risen Guard", "Scholomance Necromancer", "Spectral Tutor"]),
    ("strat",    "Stratholme",               2017, 58, 60, 61, False, 236, "Baron Rivendare", ["Crimson Guardsman", "Plagued Ghoul", "Thuzadin Shadowcaster"]),
    ("zg",       "Zul'Gurub",                1977, 60, 60, 63, True,  76,  "Hakkar", ["Gurubashi Berserker", "Hakkari Priest", "Razzashi Serpent"]),
    ("mc",       "Molten Core",              2717, 60, 60, 66, True,  741, "Ragnaros", ["Core Hound", "Lava Surger", "Firelord"]),
    ("ony",      "Onyxia's Lair",            2159, 60, 60, 67, True,  760, "Onyxia", ["Onyxian Warder", "Onyxian Whelp"]),
    ("aq20",     "Ruins of Ahn'Qiraj",       3429, 60, 60, 68, True,  743, "Ossirian the Unscarred", ["Qiraji Swarmguard", "Anubisath Guardian", "Hive'Zara Stinger"]),
    ("bwl",      "Blackwing Lair",           2677, 60, 60, 71, True,  742, "Nefarian", ["Death Talon Wyrmguard", "Blackwing Technician", "Chromatic Drakonid"]),
    ("aq40",     "Temple of Ahn'Qiraj",      3428, 60, 60, 74, True,  744, "C'Thun", ["Anubisath Sentinel", "Vekniss Soldier", "Qiraji Champion"]),
    ("naxx",     "Naxxramas",                3456, 60, 60, 78, True,  754, "Kel'Thuzad", ["Patchwork Golem", "Plagued Ghoul", "Crypt Reaver", "Death Knight Captain"]),
]
OUTDOOR_ART = 343001  # Eastern Kingdoms wide loading screen
MAX_BOSSES = 6

SLOT_MAP = {
    "Head": "HEAD", "Neck": "NECK", "Shoulder": "SHOULDER", "Back": "BACK", "Chest": "CHEST", "Wrist": "WRIST",
    "Hands": "HANDS", "Waist": "WAIST", "Legs": "LEGS", "Feet": "FEET", "Finger": "FINGER", "Trinket": "TRINKET",
    "Main Hand": "MH", "One-Hand": "1H", "Two-Hand": "2H", "Off Hand": "OH", "Held In Off-hand": "HOLD",
    "Ranged": "RANGED", "Thrown": "RANGED",
}
SUB_MAP = {
    "Cloth": "cloth", "Leather": "leather", "Mail": "mail", "Plate": "plate", "Shield": "shield", "Miscellaneous": "misc",
    "Sword": "sword", "Mace": "mace", "Axe": "axe", "Dagger": "dagger", "Staff": "staff", "Wand": "wand", "Bow": "bow",
    "Gun": "gun", "Polearm": "polearm", "Fist Weapon": "fist", "Crossbow": "xbow", "Thrown": "thrown",
}
QUALITY = {"Uncommon": 2, "Rare": 3, "Epic": 4, "Legendary": 5}
CLASS_KEY = {"Warrior": "WARRIOR", "Paladin": "PALADIN", "Hunter": "HUNTER", "Rogue": "ROGUE", "Priest": "PRIEST",
             "Shaman": "SHAMAN", "Mage": "MAGE", "Warlock": "WARLOCK", "Druid": "DRUID"}

STAT_RES = [
    (re.compile(r"^(\d+) Armor$"), "arm"),
    (re.compile(r"^\+(\d+) Strength$"), "str"), (re.compile(r"^\+(\d+) Agility$"), "agi"),
    (re.compile(r"^\+(\d+) Stamina$"), "sta"), (re.compile(r"^\+(\d+) Intellect$"), "int"),
    (re.compile(r"^\+(\d+) Spirit$"), "spi"), (re.compile(r"^(\d+) Block$"), "blk"),
    (re.compile(r"Increases spell power by (\d+)"), "sp"),
    (re.compile(r"damage and healing done by magical spells and effects by up to (\d+)"), "sp"),
    (re.compile(r"Increases attack power by (\d+)"), "ap"), (re.compile(r"^\+(\d+) Attack Power"), "ap"),
    (re.compile(r"[Ii]ncreases ranged attack power by (\d+)"), "rap"),
    (re.compile(r"critical strike rating by (\d+)"), "critr"), (re.compile(r"hit rating by (\d+)"), "hitr"),
    (re.compile(r"chance to get a critical strike by (\d+)%"), "crit"), (re.compile(r"chance to hit by (\d+)%"), "hit"),
    (re.compile(r"defense rating by (\d+)"), "def"), (re.compile(r"dodge rating by (\d+)"), "dodger"),
    (re.compile(r"Restores (\d+) mana per 5 sec"), "mp5"),
    (re.compile(r"healing done by spells and effects by up to (\d+)"), "heal"),
]
DMG_RE = re.compile(r"^(\d+) - (\d+) Damage$")
SPD_RE = re.compile(r"^Speed (\d+\.\d+)$")
DPS_RE = re.compile(r"^\(([\d.]+) damage per second\)$")
CLS_RE = re.compile(r"^Classes: (.+)$")

def lua_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

def parse_item(x):
    stats = collections.OrderedDict()
    classes = None
    set_section = False
    for t in x.get("tooltip", []):
        l = t["label"].strip()
        if re.match(r"^\(\d+\) Set", l) or t.get("format") == "indent":
            continue  # skip set bonuses/names
        m = CLS_RE.match(l)
        if m:
            classes = [c.strip() for c in m.group(1).split(",")]
            continue
        m = DMG_RE.match(l)
        if m:
            stats["min"], stats["max"] = int(m.group(1)), int(m.group(2)); continue
        m = SPD_RE.match(l)
        if m:
            stats["spd"] = float(m.group(1)); continue
        m = DPS_RE.match(l)
        if m:
            stats["dps"] = float(m.group(1)); continue
        for rx, key in STAT_RES:
            m = rx.search(l)
            if m:
                stats[key] = stats.get(key, 0) + int(m.group(1))
                break
    return stats, classes

def main():
    items = json.load(open(os.path.join(DATA, "package/data/json/data.json")))
    g = lambda x, k, d=0: x.get(k) if x.get(k) is not None else d

    # creature display ids by name (lowest creature id = original classic NPC)
    disp = {}
    with open(os.path.join(DATA, "Creature.csv")) as f:
        for r in csv.DictReader(f):
            name = r["Name_lang"]; did = int(r["DisplayID_0"] or 0)
            if did and (name not in disp or int(r["ID"]) < disp[name][0]):
                disp[name] = (int(r["ID"]), did)
    # dungeon journal boss models (exact names)
    jdisp = {}
    with open(os.path.join(DATA, "JournalEncounterCreature.csv")) as f:
        for r in csv.DictReader(f):
            did = int(r["CreatureDisplayInfoID"] or 0)
            if did and r["Name_lang"] not in jdisp:
                jdisp[r["Name_lang"]] = did
    # hand-picked stand-ins for creatures missing from the client tables
    STAND_IN = {
        "Hogger": "Gnoll", "Kobold Tunneler": "Kobold Miner", "Murloc Forager": "Murloc", "Prowler": "Timber Wolf",
        "Coyote": "Coyote", "Harvest Watcher": "Harvest Golem", "Foe Reaper 4000": "Harvest Reaper",
    }
    def lookup(name):
        if name in disp: return disp[name][1]
        if name in jdisp: return jdisp[name]
        alt = STAND_IN.get(name)
        if alt and alt in disp: return disp[alt][1]
        # same family by word, e.g. "Defias Convict" -> any "Defias ..." creature
        words = [w for w in re.split(r"[ '\-]", name) if len(w) > 3]
        for w in reversed(words):
            best = None
            for n, (cid, did) in disp.items():
                if re.search(r"\b" + re.escape(w) + r"\b", n) and (best is None or cid < best[0]):
                    best = (cid, did)
            if best: return best[1]
        return 0

    art = {}
    with open(os.path.join(DATA, "JournalInstance.csv")) as f:
        for r in csv.DictReader(f):
            art[int(r["ID"])] = (int(r["BackgroundFileDataID"] or 0), int(r["LoreFileDataID"] or 0))

    zone_to_tier = {t[2]: i for i, t in enumerate(TIERS)}
    eq = []
    for x in items:
        if x.get("class") not in ("Armor", "Weapon"): continue
        if x.get("quality") not in QUALITY: continue
        if g(x, "requiredLevel") > 60 or g(x, "itemLevel") > 100 or g(x, "contentPhase", 1) > 6: continue
        slot = SLOT_MAP.get(x.get("slot")); sub = SUB_MAP.get(x.get("subclass"))
        if not slot or not sub: continue
        if x["class"] == "Weapon" and sub == "misc": continue
        eq.append(x)

    # bosses per tier (from boss drop sources)
    boss_items = collections.defaultdict(lambda: collections.defaultdict(list))
    for x in eq:
        s = x.get("source") or {}
        if s.get("category") == "Boss Drop" and s.get("zone") in zone_to_tier:
            boss_items[zone_to_tier[s["zone"]]][s.get("name")].append(x)
    tier_bosses = []
    for i, t in enumerate(TIERS):
        bi = boss_items[i]
        final = t[8]
        others = sorted([b for b in bi if b != final], key=lambda b: (-len(bi[b]), b))[:MAX_BOSSES - 1]
        # order by the level of their loot (roughly the order you meet them)
        others.sort(key=lambda b: sum(g(x, "itemLevel") for x in bi[b]) / len(bi[b]))
        tier_bosses.append(others + [final])

    # assign items: boss loot, else tier pool (zone drops / leftover bosses), else world pool by level
    out_items = []
    for x in eq:
        s = x.get("source") or {}
        tier = boss = 0; dc = 0
        if s.get("zone") in zone_to_tier:
            ti = zone_to_tier[s["zone"]]
            tier = ti + 1
            if s.get("category") == "Boss Drop" and s.get("name") in tier_bosses[ti]:
                boss = tier_bosses[ti].index(s["name"]) + 1
            dc = int(round((s.get("dropChance") or 0) * 1000))
        stats, classes = parse_item(x)
        out_items.append((x, stats, classes, tier, boss, dc))

    # balance sanity: report per tier counts
    counts = collections.Counter(t for *_, t, b, d in out_items)
    with open(OUT, "w") as f:
        f.write("-- Generated by tools/make_gear.py from wow-classic-items (MIT) and WoW client data tables.\n")
        f.write("-- Do not edit by hand.\nlocal _, TCF = ...\n\n")
        f.write("-- Adventure tiers: real zones, dungeons and raids in level order.\n")
        f.write("-- { key, name, minLevel, maxLevel, difficulty, raid, artFileID, loreFileID, bosses = {{name, displayID}}, mobs = {{name, displayID}} }\n")
        f.write("TCF.TIERS = {\n")
        missing = []
        for i, t in enumerate(TIERS):
            key, name, zone, lo, hi, diff, raid, jid, final, trash = t
            bg, lore = art.get(jid, (OUTDOOR_ART, 0)) if jid else (OUTDOOR_ART, 0)
            def d(n):
                v = lookup(n)
                if not v: missing.append(n)
                return v
            bosses = ", ".join("{%s, %d}" % (lua_str(b), d(b)) for b in tier_bosses[i])
            mobs = ", ".join("{%s, %d}" % (lua_str(m), d(m)) for m in trash)
            f.write("  { key = %s, name = %s, min = %d, max = %d, diff = %d, raid = %s, art = %d, lore = %d,\n    bosses = { %s },\n    mobs = { %s } },\n"
                    % (lua_str(key), lua_str(name), lo, hi, diff, "true" if raid else "false", bg, lore, bosses, mobs))
        f.write("}\n\n")
        f.write("-- Items: id, name, icon, quality(2-5), itemLevel, reqLevel, slot, type, stats, tier, boss, dropChance(per mille), classes\n")
        f.write("local G = TCF.AddGear\nTCF.GEAR_LIST = {}\n")
        for x, stats, classes, tier, boss, dc in sorted(out_items, key=lambda r: r[0]["itemId"]):
            st = ",".join("%s=%s" % (k, ("%g" % v)) for k, v in stats.items())
            cls = lua_str(",".join(CLASS_KEY.get(c, c.upper()) for c in classes)) if classes else "nil"
            f.write("G(%d,%s,%s,%d,%d,%d,%s,%s,%s,%d,%d,%d,%s)\n" % (
                x["itemId"], lua_str(x["name"]), lua_str(x["icon"]), QUALITY[x["quality"]], g(x, "itemLevel"),
                g(x, "requiredLevel"), lua_str(SLOT_MAP[x["slot"]]), lua_str(SUB_MAP[x["subclass"]]), lua_str(st),
                tier, boss, dc, cls))
    q = collections.Counter(QUALITY[r[0]["quality"]] for r in out_items)
    print("items:", len(out_items), "by quality:", dict(q))
    print("tier item counts:", {TIERS[k - 1][0] if k else "world": v for k, v in sorted(counts.items())})
    for i, t in enumerate(TIERS): print(" ", t[0], tier_bosses[i])
    print("models missing:", missing)
    print("size KB:", os.path.getsize(OUT) // 1024)

if __name__ == "__main__":
    main()
