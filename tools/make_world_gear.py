#!/usr/bin/env python3
"""
Builds WorldGearData.lua: many more low and mid level world drops, from wow-classic-items
(MIT, npm) data.json. Loaded right after GearData.lua (see TapCatForever.toc).

Usage: python3 tools/make_world_gear.py [path/to/data.json] [--icons-out new_icons.txt]
       (prints the counts, the file size and the icons of new visible items that have no
       cartoon drawing yet: Art/v/i_<icon>.tga)

What it adds
------------
1. Random-suffix greens. Classic has ~1,600 world greens that say "<Random enchantment>"
   (Bandit Cinch, Ivycloth Robe...). GearData.lua holds them as bare items with armor only.
   Here every such green gets 2-4 real Classic suffixes that fit its armor or weapon type
   (cloth: caster suffixes, leather: agility, mail: hybrid, plate: strength and stamina,
   cloaks, necks and rings: anything, weapons by type), each one a gear item of its own:
     "Bandit Cinch of the Monkey"  (+Agility +Stamina)
   The bare base item stays known (old saves keep showing it) but leaves every loot pool,
   so only the suffix versions drop (Gear.lua TCF.AddSuffixGear).

   Ids: suffix item id = 10000000 + base item id * 100 + suffix number (SUFFIXES below,
   1-based), e.g. Bandit Cinch (9775) of the Monkey (1) = 10977501. Real item ids are below
   100000 (Classic ones below 24000) and some random-suffix bases are below 1000 (Notched
   Shortsword is 727), so the 10000000 offset keeps every suffix id (10000101 .. 12399999)
   clear of real ids. Base id = floor((id - 10000000) / 100), suffix = id % 100 (Gear.lua
   sets it.base and it.suffix). SUFFIXES is append-only: never reorder or remove an entry,
   or saved gear changes meaning.

   Stats: Classic's item budget. A suffix gets  budget = SLOT_RATE[slot] * itemLevel * 0.92,
   where SLOT_RATE is the median "stat budget per item level" of the fixed-stat world greens
   in GearData.lua for that slot (so suffix greens come out a little below the hand-made
   world greens of the same level, never above). Budget is spent the Classic way: stats add
   as (sum of (points ^ 1.5)) ^ (2/3), so a two-stat suffix gets budget / 2^(2/3) in each
   stat (+5 Agility +5 Stamina) and a one-stat suffix the whole budget in one (+8 Agility).
   Points per stat: primary stats 1, spell power 0.86, healing 0.45, attack power 0.5,
   ranged attack power 0.4, defense 1 (so 1 point = 1.16 spell power, 2.2 healing, 2 AP).
   Each base's suffixes are picked with a random generator seeded by the base id, so
   re-running gives the same items.

2. White (Common) gear: the classic white armor and weapons (vendor, quest and starter
   items) with real armor or damage and no bonus stats. They go to the world pools only
   (never boss or zone loot, never chests: chests roll Uncommon or better). Adventure's small
   finds (Gear.lua TCF:TrashSmallFind) hand them out, mostly at low level. Items a
   profession makes (createdBy), novelty items without armor or damage, test and GM items
   (item level 0-1), holiday costumes and Burning Crusade starting-zone gear (ids 20800 and
   up) are left out.

Format (WorldGearData.lua)
--------------------------
  TCF.GEAR_SUFFIXES = { "of the Monkey", ... }            -- suffix names by number
  G(id, name, icon, 1, itemLevel, reqLevel, slot, type, stats, 0, 0, 0, classes)  -- whites
  S(baseId, k1, "stats", k2, "stats", ...)                 -- suffix versions of one base
"""
import json, os, re, sys, random, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import make_gear as MG  # slot/type maps and tooltip stat parsing, exactly as GearData.lua was made

DEFAULT_DATA = "/tmp/claude-0/-home-user-tapcatforever/698bae0f-78dc-58a7-8d06-da2ec75e148f/scratchpad/data/package/data/json/data.json"
OUT = os.path.join(ROOT, "WorldGearData.lua")

# ------------------------------------------------------------------ suffixes (APPEND-ONLY)
SUFFIXES = [
    ("monkey", "of the Monkey", ("agi", "sta")),      # 1
    ("bear", "of the Bear", ("str", "sta")),          # 2
    ("eagle", "of the Eagle", ("sta", "int")),        # 3
    ("owl", "of the Owl", ("int", "spi")),            # 4
    ("tiger", "of the Tiger", ("str", "agi")),        # 5
    ("falcon", "of the Falcon", ("agi", "int")),      # 6
    ("wolf", "of the Wolf", ("agi", "spi")),          # 7
    ("boar", "of the Boar", ("str", "spi")),          # 8
    ("gorilla", "of the Gorilla", ("str", "int")),    # 9
    ("whale", "of the Whale", ("sta", "spi")),        # 10
    ("strength", "of Strength", ("str",)),            # 11
    ("agility", "of Agility", ("agi",)),              # 12
    ("stamina", "of Stamina", ("sta",)),              # 13
    ("intellect", "of Intellect", ("int",)),          # 14
    ("spirit", "of Spirit", ("spi",)),                # 15
    ("healing", "of Healing", ("heal",)),             # 16
    ("wrath", "of Fiery Wrath", ("sp",)),             # 17
    ("power", "of Power", ("ap",)),                   # 18
    ("marks", "of Marksmanship", ("rap",)),           # 19
    ("defense", "of Defense", ("def",)),              # 20
]
SUFFIX_ID_BASE = 10000000   # must match Gear.lua TCF.SUFFIX_ID_BASE
SUFFIX_NO = {key: i + 1 for i, (key, _, _) in enumerate(SUFFIXES)}
POINTS = {"str": 1, "agi": 1, "sta": 1, "int": 1, "spi": 1, "sp": 0.86, "heal": 0.45, "ap": 0.5, "rap": 0.4, "def": 1}

# which suffixes fit which kind of item (each base gets 2-4 of its list)
CASTER = ["eagle", "owl", "intellect", "spirit", "wrath", "healing", "whale"]
FAMILY = {
    "cloth":   CASTER,
    "leather": ["monkey", "tiger", "falcon", "wolf", "agility", "power"],
    "mail":    ["eagle", "falcon", "monkey", "gorilla", "tiger", "bear", "wolf"],
    "plate":   ["bear", "tiger", "strength", "stamina", "boar", "gorilla", "defense"],
    "any":     ["monkey", "bear", "eagle", "owl", "tiger", "falcon", "whale", "stamina", "intellect", "strength", "agility", "spirit"],
    "shield":  ["bear", "gorilla", "eagle", "stamina", "strength", "defense"],
    "held":    ["eagle", "owl", "intellect", "spirit", "wrath", "healing"],
    "dagger":  ["monkey", "tiger", "agility", "power", "eagle", "wrath"],
    "sword":   ["tiger", "bear", "monkey", "strength", "agility", "power", "eagle"],
    "axe":     ["tiger", "bear", "monkey", "strength", "agility", "power"],
    "mace":    ["tiger", "bear", "strength", "power", "eagle", "healing", "gorilla"],
    "fist":    ["monkey", "tiger", "agility", "power", "strength"],
    "two":     ["tiger", "bear", "monkey", "strength", "agility", "power", "boar"],
    "mace2":   ["tiger", "bear", "strength", "power", "gorilla", "boar"],
    "staff":   ["owl", "eagle", "intellect", "wrath", "healing", "spirit", "monkey", "whale"],
    "wand":    ["eagle", "owl", "intellect", "wrath", "spirit"],
    "ranged":  ["monkey", "falcon", "agility", "marks", "wolf"],
    "thrown":  ["monkey", "tiger", "agility", "power"],
}

# median stat budget per item level of fixed-stat world greens (tools: see the docstring)
SLOT_RATE = {
    "HEAD": 0.42, "CHEST": 0.38, "LEGS": 0.38, "2H": 0.35, "SHOULDER": 0.31, "HANDS": 0.30, "WAIST": 0.29,
    "FEET": 0.29, "NECK": 0.24, "FINGER": 0.22, "BACK": 0.21, "WRIST": 0.22, "HOLD": 0.22, "OH": 0.21,
    "TRINKET": 0.22, "1H": 0.14, "MH": 0.14, "RANGED": 0.13, "WAND": 0.14,
}
SUFFIX_SHARE = 0.92

# Whites: ids from 20800 up are Burning Crusade starting-zone gear (Sunstrider, Exodar...);
# item level 0-1 whites are test, GM and costume items ("Shadow Sword", "Gamemaster Hood").
WHITE_MAX_ID = 20800
NOT_GEAR = re.compile(r"Gamemaster|Fire Festival|Festive|Monster|\bTest\b|Deprecated|\b[A-Z]\d\d\b|Engineer's Shield \d")

VISIBLE = {"HEAD", "CHEST", "WAIST", "NECK", "FINGER", "BACK", "MH", "1H", "2H", "OH", "HOLD", "RANGED"}

G_RE = re.compile(r'^G\((\d+),"((?:[^"\\]|\\.)*)","([^"]*)",(\d),(\d+),(\d+),"(\w+)","(\w+)","([^"]*)",(\d+),(\d+),(\d+),(nil|"[^"]*")')


def family(slot, sub):
    if sub == "shield":
        return "shield"
    if slot in ("BACK", "NECK", "FINGER", "TRINKET") or sub == "misc":
        return "held" if slot == "HOLD" else "any"
    if sub in ("cloth", "leather", "mail", "plate"):
        return sub
    if sub == "staff":
        return "staff"
    if sub == "wand":
        return "wand"
    if sub in ("bow", "gun", "xbow"):
        return "ranged"
    if sub == "thrown":
        return "thrown"
    if slot == "2H":
        return "mace2" if sub == "mace" else "two"
    if sub == "polearm":
        return "two"
    return sub if sub in FAMILY else "any"


def suffix_stats(key, slot, sub, ilvl):
    rate = SLOT_RATE["WAND"] if sub == "wand" else SLOT_RATE.get(slot, 0.2)
    budget = max(1.0, rate * ilvl * SUFFIX_SHARE)
    stats = SUFFIXES[SUFFIX_NO[key] - 1][2]
    each = budget / (len(stats) ** (2.0 / 3.0))
    out = collections.OrderedDict()
    for s in stats:
        out[s] = max(1, int(round(each / POINTS[s])))
    return out


def stat_str(d):
    return ",".join("%s=%s" % (k, "%g" % v) for k, v in d.items())


def read_gear_lines(path):
    out = {}
    for l in open(path, encoding="utf-8"):
        m = G_RE.match(l)
        if m:
            g = m.groups()
            out[int(g[0])] = dict(id=int(g[0]), name=g[1], icon=g[2], q=int(g[3]), ilvl=int(g[4]), req=int(g[5]),
                                  slot=g[6], sub=g[7], stats=g[8], tier=int(g[9]), boss=int(g[10]), dc=int(g[11]))
    return out


def crafted_ids():
    ids = set()
    p = os.path.join(ROOT, "CraftData.lua")
    if os.path.exists(p):
        for l in open(p, encoding="utf-8"):
            m = re.match(r'^[GC]\((\d+),', l)
            if m:
                ids.add(int(m.group(1)))
    return ids


def vec_icons():
    p = os.path.join(ROOT, "VectorData.lua")
    if not os.path.exists(p):
        return {}
    return dict(re.findall(r'^V\["([a-z0-9_]+)"\]=\{.*,"([a-z]+)"\}$', open(p, encoding="utf-8").read(), re.M))


def is_random(x):
    return any("<Random enchantment>" in t.get("label", "") for t in x.get("tooltip", []))


def usable_base(x, g):
    if x.get("itemId", 0) >= 24000 or g(x, "requiredLevel") > 60 or g(x, "itemLevel") > 100 or g(x, "contentPhase", 1) > 6:
        return False
    if x.get("class") not in ("Armor", "Weapon"):
        return False
    slot, sub = MG.SLOT_MAP.get(x.get("slot")), MG.SUB_MAP.get(x.get("subclass"))
    if not slot or not sub or (x["class"] == "Weapon" and sub == "misc"):
        return False
    return True


def build(data_path):
    items = json.load(open(data_path))
    g = lambda x, k, d=0: x.get(k) if x.get(k) is not None else d
    gear = read_gear_lines(os.path.join(ROOT, "GearData.lua"))
    crafted = crafted_ids()

    # ---- random-suffix greens
    suffix_rows = []   # (base, [(k, statstr)])
    skipped = collections.Counter()
    for x in sorted(items, key=lambda x: x["itemId"]):
        if x.get("quality") != "Uncommon" or not is_random(x) or not usable_base(x, g):
            continue
        b = gear.get(x["itemId"])
        if not b:
            skipped["not in GearData.lua"] += 1; continue
        if x["itemId"] in crafted or x.get("createdBy"):
            skipped["crafted"] += 1; continue
        if b["ilvl"] == 0 or b["name"].startswith("zz") or "OLD" in b["name"] or b["name"].startswith("Bland "):
            skipped["placeholder"] += 1; continue
        assert SUFFIX_ID_BASE + x["itemId"] * 100 + len(SUFFIXES) < 100000000, x["name"]
        fam = FAMILY[family(b["slot"], b["sub"])]
        base_keys = set(k for k, _ in re.findall(r"(\w+)=([\d.]+)", b["stats"]))
        rng = random.Random(x["itemId"])
        n = 2 + rng.randrange(3)
        picks = [k for k in rng.sample(fam, min(n, len(fam)))]
        picks.sort(key=lambda k: SUFFIX_NO[k])
        vs = []
        for key in picks:
            st = suffix_stats(key, b["slot"], b["sub"], b["ilvl"])
            if base_keys & set(st):
                continue
            vs.append((SUFFIX_NO[key], stat_str(st)))
        if vs:
            suffix_rows.append((b, vs))

    # ---- whites
    whites = []
    seen = set()
    for x in sorted(items, key=lambda x: x["itemId"]):
        if x.get("quality") != "Common" or not usable_base(x, g):
            continue
        if x["itemId"] in gear or x["itemId"] in crafted or x.get("createdBy"):
            continue
        stats, classes = MG.parse_item(x)
        if not (stats.get("arm") or stats.get("dps")):
            continue  # dresses, masks, torches, plain rings: no armor or damage
        if g(x, "itemLevel") <= 1 or x["itemId"] >= WHITE_MAX_ID or NOT_GEAR.search(x["name"]):
            continue  # test and GM items (item level 1), holiday costumes, Burning Crusade starter gear
        slot, sub = MG.SLOT_MAP[x["slot"]], MG.SUB_MAP[x["subclass"]]
        sig = (x["name"], slot, sub, stat_str(stats))
        if sig in seen:
            continue   # the same starter item under several ids
        seen.add(sig)
        whites.append((x, stats, classes, slot, sub))
    return suffix_rows, whites, skipped


def write(suffix_rows, whites):
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("-- Generated by tools/make_world_gear.py from wow-classic-items (MIT). Do not edit by hand.\n")
        f.write("-- More world gear: random-suffix greens and white (Common) armor and weapons.\n")
        f.write("-- Suffix item id = 10000000 + base item id * 100 + suffix number (never a real item id: those are < 100000).\n")
        f.write("local _, TCF = ...\n\n")
        f.write("-- suffix names by number (append-only: saved gear ids depend on the numbers)\n")
        f.write("TCF.GEAR_SUFFIXES = {\n")
        for i, (key, name, stats) in enumerate(SUFFIXES):
            f.write('  "%s", -- %d: %s\n' % (name, i + 1, " + ".join(stats)))
        f.write("}\n\n")
        f.write("local G, S = TCF.AddGear, TCF.AddSuffixGear\n\n")
        f.write("-- White gear: id, name, icon, quality 1, itemLevel, reqLevel, slot, type, stats, tier 0, boss 0, dropChance 0, classes\n")
        for x, stats, classes, slot, sub in whites:
            cls = MG.lua_str(",".join(MG.CLASS_KEY.get(c, c.upper()) for c in classes)) if classes else "nil"
            f.write("G(%d,%s,%s,1,%d,%d,%s,%s,%s,0,0,0,%s)\n" % (
                x["itemId"], MG.lua_str(x["name"]), MG.lua_str(x["icon"]), x.get("itemLevel") or 0,
                x.get("requiredLevel") or 0, MG.lua_str(slot), MG.lua_str(sub), MG.lua_str(stat_str(stats)), cls))
        f.write("\n-- Random-suffix greens: S(baseId, suffixNumber, \"bonus stats\", ...). The base item's name, icon,\n")
        f.write("-- levels, slot, type, armor/damage and loot source are reused; the bare base never drops again.\n")
        for b, vs in suffix_rows:
            f.write("S(%d,%s) -- %s\n" % (b["id"], ",".join('%d,"%s"' % (k, s) for k, s in vs), b["name"].replace('\\"', '"')))
        f.write("\n-- the bare bases leave every loot pool\nTCF.DropRetiredGear()\n")


def main():
    argv = sys.argv[1:]
    if "--icons-out" in argv:
        i = argv.index("--icons-out"); argv = argv[:i] + argv[i + 2:]
    args = [a for a in argv if not a.startswith("--")]
    data = args[0] if args else DEFAULT_DATA
    suffix_rows, whites, skipped = build(data)
    write(suffix_rows, whites)
    nvar = sum(len(vs) for _, vs in suffix_rows)
    print("suffix bases:", len(suffix_rows), "suffix items:", nvar, "skipped:", dict(skipped))
    print("white items:", len(whites), "by slot:", dict(collections.Counter(w[3] for w in whites)))
    print("size KB:", os.path.getsize(OUT) // 1024)
    # icons of NEW visible items with no cartoon drawing yet
    art = os.path.join(ROOT, "Art", "v")
    need = set()
    for b, vs in suffix_rows:
        if b["slot"] in VISIBLE and not os.path.exists(os.path.join(art, "i_" + b["icon"].lower() + ".tga")):
            need.add(b["icon"].lower())
    for x, stats, classes, slot, sub in whites:
        if slot in VISIBLE and not os.path.exists(os.path.join(art, "i_" + x["icon"].lower() + ".tga")):
            need.add(x["icon"].lower())
    print("NEW_ICONS (%d):" % len(need), " ".join(sorted(need)))
    if "--icons-out" in sys.argv:
        with open(sys.argv[sys.argv.index("--icons-out") + 1], "w") as f:
            f.write("".join(i + "\n" for i in sorted(need)))
    return sorted(need)


if __name__ == "__main__":
    main()
