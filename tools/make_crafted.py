#!/usr/bin/env python3
"""
Builds CraftData.lua: the real Classic gear that Blacksmithing, Leatherworking and Tailoring
make, from wow-classic-items (MIT, npm) data.json.

Usage:
  python3 tools/make_crafted.py [path/to/data.json]   writes CraftData.lua
  python3 tools/trade_sim.py --craft 1 2 4             how long leveling 1 -> 300 takes (real addon)

Items
-----
The recipe lists below are hand-picked (~40 per craft) from every Classic recipe whose
createdBy category is the craft and whose requiredSkill is 1..300 (TBC/Wrath items, and items
that use TBC materials, are left out). They are spread so a new recipe unlocks at least every
~15-25 skill points (an orange recipe is always there), favour items with real stats, cover
the visible slots (helms, chests, belts, cloaks, weapons, a shield) and only use slots and
armor/weapon types the game supports:
  blacksmithing  mail and plate armor, one- and two-handed weapons, a shield
  leatherworking leather and mail armor, cloaks
  tailoring      cloth armor and cloaks (no bags, no dresses)
Stats, slots and types are parsed with tools/make_gear.py's own functions, so the entries are
exactly what GearData.lua would hold. Items GearData.lua already has (all Uncommon+ crafted
items are there as world drops) are only marked crafted: C(id, craft) (Gear.lua's
TCF.MarkCrafted) takes them out of every loot pool. New items (the white starter recipes)
are registered with G(...) like GearData.lua does, with the crafting key as the last argument.
Either way the item gets crafted = "<craft key>" and tier = boss = dc = 0, and CraftData.lua
sets craftSkill on it so tooltips can say "Crafted by Blacksmithing (skill 125)".

Materials
---------
Each recipe costs the family's own material of its skill band (FIXED KEYS in the design):
  skill   1-74  tier 1 (copper / light leather / linen)
  skill  75-124 tier 2 (tin / medium leather / wool)
  skill 125-174 tier 3 (iron / heavy leather / silk)
  skill 175-229 tier 4 (mithril / thick leather / mageweave)
  skill 230-274 tier 5 (thorium / rugged leather / runecloth)
  skill 275-300 tier 5 plus a little tier 6 (arcane crystal / devilsaur leather / felcloth)
Amount = BASE[tier] x size factor, where the size factor is the recipe's real reagent count
(bars / leather / bolts, with thread, dye, flux and stones counting half) divided by the
average of its craft's recipes in the same band, clamped to 0.6 .. 2.0. So the three crafts
cost the same on average (same numbers for every family) while big real recipes (a breastplate
of 20 bars) still cost more than small ones (bracers of 4). Tier 6 on 275-300 recipes is
T6_BASE x size factor. Amounts are rounded to tidy numbers.

The numbers (BASE) and why
--------------------------
  BASE = { 1: 8, 2: 120, 3: 1300, 4: 6000, 5: 8500 },  T6_BASE = 850  (per craft, before size)
so a craft costs 5-16 tier-1 mats at skill 1-74, about 70-240 tier 2, 800-2600 tier 3,
3600-12000 tier 4, 5100-17000 tier 5, and at 275-300 tier 5 plus 500-1700 tier 6 (the three
families in about the same ranges). Tiers 1-2 stay cheap so the first recipes come quickly.

1.6 skill-up curve (Professions.lua TCF.SKILLUP_BANDS, the same for every profession): a recipe
gives a point every time while your skill is less than 5 above it, half the time up to 15 above,
1 in 5 up to 30, 1 in 20 up to 50, and never after that. Recipes unlock at most 25 skill apart, so
the newest recipe is always orange or yellow; each one gives only a few sure points, so a level
takes more crafts than before 1.6 (when the first 25 were sure) and BASE was lowered to about
0.4-0.65 of the 1.5 amounts to keep the same pace.

The source of truth for the pace is the real addon: python3 tools/trade_sim.py --craft 1 2 4
(the casual player: online N hours a day, helpers working offline, offline Trade Gold and the
Trade Gold from selling crafted gear spent on spots and helpers, always the best skill-up recipe,
no prestige, nothing else spending the mats). With the numbers above, 1 -> 300 takes:
  1 h a day: 43-49 days    2 h a day: 41-44 days    4 h a day: 41-53 days
  (2 h a day: skill 125 on day 2, 175 on day 4-5, 230 on day 14-15, 275 on day 31-32)
Online time matters little after the first days because the hires do most of the work around
the clock. Real players also spend these mats on cosmetics, skins, First Aid and Cooking,
prestige (which resets their spots for a while) and skip days, so expect longer: the first
bands are a quick start, and 230 -> 300 is the long-term goal (weeks to months). Re-run
trade_sim.py --craft after changing BASE.
Crafted gear sells for Trade Gold only (half its material value, Gear.lua), which is always less
than selling the materials, so crafting is never a gold exploit.
"""
import json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import make_gear as MG  # stat / slot / type parsing, exactly as GearData.lua was made

DEFAULT_DATA = "/tmp/claude-0/-home-user-tapcatforever/698bae0f-78dc-58a7-8d06-da2ec75e148f/scratchpad/data/package/data/json/data.json"
OUT = os.path.join(ROOT, "CraftData.lua")

CRAFTS = [
    # craft key, data category, family mats tier 1..6
    ("blacksmithing", "Blacksmithing", ["copper", "tin", "iron", "mithril", "thorium", "arcane"]),
    ("leatherworking", "Leatherworking", ["lightleather", "mediumleather", "heavyleather", "thickleather", "ruggedleather", "devilsaur"]),
    ("tailoring", "Tailoring", ["linen", "wool", "silk", "mageweave", "runecloth", "felcloth"]),
]

# hand-picked recipes (item ids), see the docstring
PICKS = {
    "blacksmithing": [
        10421, 2852, 2853, 2403, 3469, 2851, 2845, 2844, 2847, 7955, 3471, 3488, 3472, 3474, 6214, 2857, 2864, 3487, 6731, 2866, 5540,
        2849, 2850, 7956, 2870, 3851, 3849, 3836, 3850, 3853, 3837, 3845, 3854, 7919, 7921,
        7922, 7943, 7930, 7935, 7937, 12405, 7960, 12424, 12410, 11604, 19051, 12427,
        12422, 12784, 22198, 12640,
    ],
    "leatherworking": [
        5957, 2302, 7276, 7277, 797, 2303, 4237, 7280, 2300, 2309, 2311, 7281, 4242, 4243, 2307, 5781, 2317, 6467,
        2316, 6468, 2314, 4252, 4254, 4255, 4455, 5963, 7374, 4262, 5739, 8174, 8175, 8189, 8203,
        8345, 8193, 8207, 8348, 8367, 15083, 15076, 15061, 15064, 15086, 15056, 15063, 15080,
        15062, 18509,
    ],
    "tailoring": [
        10045, 2570, 793, 3603, 2568, 7026, 10046, 6238, 4307, 2572, 2580, 2569, 4309, 2582, 5542, 2583,
        6263, 2585, 4314, 6264, 4317, 5766, 7048, 5770, 7050, 7065, 4323, 7055, 7058, 7054, 4327,
        9998, 10004, 10021, 10024, 10025, 10041, 13868, 14042, 13860, 14107, 13864, 14136,
        14111, 13866, 14138, 14152, 18405,
    ],
}

# 1.6 starter sets: at least one WHITE piece for every armour slot Classic had a low-level white
# for, so a new cat can wear a full crafted set (no rings, necks or trinkets). Real Classic white
# crafted items where they exist (their real skill and reagents); where Classic had no crafted
# white for a slot (gloves for all three, cloth bracers) a real Classic vendor white of the same
# armour type is made at a low skill instead (STARTER_VENDOR: item -> skill). Classic has no
# white helm or shoulders below level 15 at all, so the sets have none (see notes/prof.md).
# Each set is a list of slots; a slot is a list of items (any one of them counts), easiest first.
STARTER = {
    "blacksmithing": [[2853], [2852], [10421], [2403], [3469], [2851], [2844, 2845, 2847, 7955]],
    "leatherworking": [[7277], [2302], [5957], [7276], [797], [2303], [4237]],
    "tailoring": [[10045], [2570], [793], [2568], [3603], [7026], [10046]],
}
STARTER_VENDOR = {2403: 5, 797: 5, 793: 5, 3603: 10}

BANDS = [(1, 74, 1), (75, 124, 2), (125, 174, 3), (175, 229, 4), (230, 274, 5), (275, 300, 5)]
BASE = {1: 8, 2: 120, 3: 1300, 4: 6000, 5: 8500}
T6_BASE = 850
SIZE_CLAMP = (0.6, 2.0)
HALF = ("Thread", "Dye", "Flux", "Bleach", "Grinding Stone", "Buckle")

QUALITY = dict(MG.QUALITY, Common=1)
VISIBLE = {"HEAD", "CHEST", "WAIST", "NECK", "FINGER", "BACK", "MH", "1H", "2H", "OH", "HOLD", "RANGED"}
# drawing kind CatVector wants for each visible slot (VectorData.lua's 8th field)
KIND = {"HEAD": "head", "CHEST": "chest", "WAIST": "belt", "NECK": "neck", "FINGER": "ring", "BACK": "back",
        "OH": "shield", "HOLD": "held"}


def band_of(skill):
    for i, (lo, hi, tier) in enumerate(BANDS):
        if lo <= skill <= hi:
            return i, tier
    raise ValueError(skill)


def tidy(n):
    n = max(1, n)
    step = 1 if n < 30 else 5 if n < 200 else 10 if n < 1000 else 50 if n < 5000 else 100
    return int(max(step, round(n / step) * step))


def is_classic(x, cb, by_id):
    if x["itemId"] >= 24000 or (x.get("itemLevel") or 0) > 85 or (x.get("requiredLevel") or 0) > 60:
        return False
    for r in cb.get("reagents", []):
        n = by_id.get(r["itemId"], {}).get("name", "")
        if r["itemId"] >= 23000 or any(w in n for w in ("Fel Iron", "Netherweave", "Knothide", "Adamantite", "Primal ")):
            return False
    return True


def reagent_size(cb, by_id):
    s = 0.0
    for r in cb.get("reagents", []):
        n = by_id.get(r["itemId"], {}).get("name", "")
        s += r["amount"] * (0.5 if any(w in n for w in HALF) else 1.0)
    return max(1.0, s)


def gear_data_ids():
    ids = {}
    # WorldGearData.lua too: the vendor whites of the starter sets are there (it loads before CraftData.lua)
    for fn in ("GearData.lua", "WorldGearData.lua"):
        for l in open(os.path.join(ROOT, fn), encoding="utf-8"):
            if l.startswith("G("):
                ids.setdefault(int(l[2:l.index(",")]), l.strip())
    return ids


def vec_icons():
    p = os.path.join(ROOT, "VectorData.lua")
    return dict(re.findall(r'^V\["([a-z0-9_]+)"\]=\{.*,"([a-z]+)"\}$', open(p, encoding="utf-8").read(), re.M))


def g_line(x, stats, classes, craft):
    st = ",".join("%s=%s" % (k, ("%g" % v)) for k, v in stats.items())
    cls = MG.lua_str(",".join(MG.CLASS_KEY.get(c, c.upper()) for c in classes)) if classes else "nil"
    g = lambda k: x.get(k) or 0
    return "G(%d,%s,%s,%d,%d,%d,%s,%s,%s,%d,%d,%d,%s,%s)" % (
        x["itemId"], MG.lua_str(x["name"]), MG.lua_str(x["icon"]), QUALITY[x["quality"]], g("itemLevel"),
        g("requiredLevel"), MG.lua_str(MG.SLOT_MAP[x["slot"]]), MG.lua_str(MG.SUB_MAP[x["subclass"]]),
        MG.lua_str(st), 0, 0, 0, cls, MG.lua_str(craft))


def build(data_path):
    items = json.load(open(data_path))
    by_id = {x["itemId"]: x for x in items}
    known = gear_data_ids()
    vec = vec_icons()
    recipes = {}
    new_lines, mark_lines, new_icons, wrong, mismatch = [], [], set(), [], []
    for craft, cat, mats in CRAFTS:
        rows = []
        for iid in PICKS[craft]:
            x = by_id[iid]
            if iid in STARTER_VENDOR:
                # a vendor white for a slot Classic had no crafted white for: made at a low skill
                cb = {"requiredSkill": STARTER_VENDOR[iid], "reagents": []}
            else:
                cb = next(c for c in x.get("createdBy") or [] if c.get("category") == cat)
            skill = cb.get("requiredSkill") or 0
            slot, sub = MG.SLOT_MAP.get(x.get("slot")), MG.SUB_MAP.get(x.get("subclass"))
            assert 1 <= skill <= 300 and slot and sub and x.get("class") in ("Armor", "Weapon"), x["name"]
            assert is_classic(x, cb, by_id), x["name"]
            assert x["quality"] in QUALITY, x["name"]
            if craft == "blacksmithing":
                assert sub in ("mail", "plate", "shield") or x["class"] == "Weapon", x["name"]
            elif craft == "leatherworking":
                assert sub in ("leather", "mail") or slot == "BACK", x["name"]
            else:
                assert sub == "cloth", x["name"]
            stats, classes = MG.parse_item(x)
            rows.append(dict(x=x, skill=skill, size=reagent_size(cb, by_id) if cb["reagents"] else None, stats=stats, classes=classes, slot=slot))
        rows.sort(key=lambda r: (r["skill"], r["x"]["itemId"]))
        # average real size per band, then each recipe's size factor
        acc = collections.defaultdict(list)
        for r in rows:
            if r["size"] is not None:
                acc[band_of(r["skill"])[0]].append(r["size"])
        starter_ids = set(i for slot in STARTER[craft] for i in slot)
        out = []
        for r in rows:
            b, tier = band_of(r["skill"])
            # a vendor white (no real reagents) costs the smallest amount of its band
            f = SIZE_CLAMP[0] if r["size"] is None else r["size"] / (sum(acc[b]) / len(acc[b]))
            f = min(SIZE_CLAMP[1], max(SIZE_CLAMP[0], f))
            m = collections.OrderedDict()
            m[mats[tier - 1]] = tidy(BASE[tier] * f)
            if r["skill"] >= 275:
                m[mats[5]] = tidy(T6_BASE * f)
            x = r["x"]
            out.append({"gear": x["itemId"], "skill": r["skill"], "mats": m, "name": x["name"], "q": QUALITY[x["quality"]],
                        "starter": x["itemId"] in starter_ids})
            if x["itemId"] in starter_ids:
                assert QUALITY[x["quality"]] == 1 and r["slot"] not in ("FINGER", "NECK", "TRINKET"), x["name"]
            if x["itemId"] in known:
                # sanity: the existing entry must be what make_gear.py's parsing gives
                mine = g_line(x, r["stats"], r["classes"], craft)
                if known[x["itemId"]].split(",")[:9] != mine.split(",")[:9]:
                    wrong.append(x["name"])
                mark_lines.append('C(%d,"%s") -- %s' % (x["itemId"], craft, x["name"]))
            else:
                new_lines.append(g_line(x, r["stats"], r["classes"], craft))
            ic = x["icon"].lower()
            if r["slot"] in VISIBLE and ic not in vec:
                new_icons.add(ic)
            elif r["slot"] in VISIBLE and vec[ic] != KIND.get(r["slot"], "weapon"):
                mismatch.append("%s (%s, drawn as %s)" % (x["name"], ic, vec[ic]))
        # no long gaps: something new unlocks at least every 25 skill
        last = 1
        for o in out:
            assert o["skill"] - last <= 25, (craft, o["skill"], last)
            last = o["skill"]
        recipes[craft] = out
    return recipes, new_lines, mark_lines, sorted(new_icons), wrong, mismatch


def write(recipes, new_lines, mark_lines):
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("-- Generated by tools/make_crafted.py from wow-classic-items (MIT). Do not edit by hand.\n")
        f.write("-- Real Classic gear made by Blacksmithing, Leatherworking and Tailoring.\n")
        f.write("local _, TCF = ...\n\n")
        f.write("-- New items, in GearData.lua's format plus the crafting key:\n")
        f.write("-- id, name, icon, quality(1-5), itemLevel, reqLevel, slot, type, stats, tier, boss, dropChance, classes, craft\n")
        f.write("local G, C = TCF.AddGear, TCF.MarkCrafted\n")
        for l in new_lines:
            f.write(l + "\n")
        f.write("\n-- Items GearData.lua already has: crafted from now on, never loot.\n")
        for l in mark_lines:
            f.write(l + "\n")
        f.write("\n-- { gear = itemId, skill = required crafting skill, mats = { matKey = amount } }, easiest first\n")
        f.write("TCF.CRAFT_RECIPES = {\n")
        for craft, _, _ in CRAFTS:
            f.write("  %s = {\n" % craft)
            for r in recipes[craft]:
                mats = ", ".join("%s = %d" % (k, v) for k, v in r["mats"].items())
                f.write("    { gear = %d, skill = %d, mats = { %s }%s }, -- %s\n" % (r["gear"], r["skill"], mats,
                        ", starter = true" if r["starter"] else "", r["name"]))
            f.write("  },\n")
        f.write("}\n\n")
        f.write("-- 1.6 starter sets: white pieces a new cat can wear, one list per slot (any item of it counts)\n")
        f.write("TCF.CRAFT_STARTER = {\n")
        for craft, _, _ in CRAFTS:
            f.write("  %s = { %s },\n" % (craft, ", ".join("{ " + ", ".join(str(i) for i in slot) + " }" for slot in STARTER[craft])))
        f.write("}\n\n")
        f.write("-- material tier (1-6) of every family material, for crafted gear's Trade Gold value\n")
        f.write("TCF.CRAFT_MAT_TIER = {\n")
        for _, _, mats in CRAFTS:
            f.write("  " + ", ".join("%s = %d" % (m, i + 1) for i, m in enumerate(mats)) + ",\n")
        f.write("}\n\n")
        f.write("for craft, list in pairs(TCF.CRAFT_RECIPES) do\n")
        f.write("  for _, r in ipairs(list) do\n")
        f.write("    local it = TCF.GEAR[r.gear]\n")
        f.write("    if it then it.crafted = craft; it.craftSkill = r.skill; it.craftMats = r.mats end\n")
        f.write("  end\n")
        f.write("end\n")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    data = args[0] if args else DEFAULT_DATA
    recipes, new_lines, mark_lines, new_icons, wrong, mismatch = build(data)
    if "--sim" in sys.argv:
        print("The leveling simulation runs the real addon now: python3 tools/trade_sim.py --craft 1 2 4")
        return
    write(recipes, new_lines, mark_lines)
    for craft, _, _ in CRAFTS:
        r = recipes[craft]
        print("%s: %d recipes, skill %d..%d" % (craft, len(r), r[0]["skill"], r[-1]["skill"]))
    print("new items:", len(new_lines), "marked crafted:", len(mark_lines))
    if wrong:
        print("WARNING: GearData.lua entries differ from make_gear.py parsing:", wrong)
    if mismatch:
        print("drawn with another slot's drawing (the cat shows the plain look instead):", "; ".join(mismatch))
    print("NEW_ICONS:", " ".join(new_icons))


if __name__ == "__main__":
    main()
