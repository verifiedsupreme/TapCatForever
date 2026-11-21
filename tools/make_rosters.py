"""Enemy rosters for every Adventure zone from a full Classic creature database.

Source: AzerothCore's world database (creature_template, creature_template_model, creature),
which lists every creature with its model (display) ID and where it spawns. For each zone we
take the creatures actually spawned there, skip bosses, rares, critters, vendors and quest
givers, keep them near the zone's level, and rank them by how often they spawn.

usage: python3 tools/make_rosters.py <acdb_dir>  -> tools/rosters.json
"""
import json, os, re, sys
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
DB = sys.argv[1]

def rows(table):
    sql = open(os.path.join(DB, table + ".sql"), encoding="utf-8", errors="replace").read()
    cols = re.findall(r"^\s*`(\w+)`", sql[sql.index("CREATE TABLE"):sql.index("ENGINE")], re.M)
    for m in re.finditer(r"INSERT INTO `\w+` VALUES\s*(.*?);\s*\n", sql, re.S):
        body = m.group(1)
        # split "(...),(...)" respecting quoted strings
        i, n = 0, len(body)
        while i < n:
            if body[i] != "(":
                i += 1; continue
            i += 1; vals, cur, q = [], "", False
            while i < n:
                c = body[i]
                if q:
                    if c == "\\": cur += body[i + 1]; i += 2; continue
                    if c == "'": q = False
                    else: cur += c
                elif c == "'": q = True
                elif c == ",": vals.append(cur); cur = ""
                elif c == ")": vals.append(cur); i += 1; break
                else: cur += c
                i += 1
            yield dict(zip(cols, vals))

tmpl = {}
for r in rows("creature_template"):
    tmpl[int(r["entry"])] = r
models = defaultdict(list)
for r in rows("creature_template_model"):
    models[int(r["CreatureID"])].append((int(r["Idx"]), int(r["CreatureDisplayID"])))
# open-world zones aren't tagged in this database, so they're found by map coordinates
BOXES = {"elwynn": (0, -10100, -8600, -1450, 350), "westfall": (0, -11500, -9800, 650, 2150)}
spawns = defaultdict(Counter)   # (kind, id) -> Counter(creature entry)
for r in rows("creature"):
    e = int(r["id1"])
    spawns[("map", int(r["map"]))][e] += 1
    x, y, mp = float(r["position_x"]), float(r["position_y"]), int(r["map"])
    for key, (bm, x0, x1, y0, y1) in BOXES.items():
        if mp == bm and x0 <= x <= x1 and y0 <= y <= y1: spawns[("box", key)][e] += 1
# Dungeon Journal boss names never appear as trash
import csv
JOURNAL = set()
jpath = os.path.join(os.path.dirname(DB), "data", "JournalEncounterCreature.csv")
if os.path.exists(jpath):
    for r in csv.DictReader(open(jpath, encoding="utf-8")): JOURNAL.add(r["Name_lang"])

# Adventure tiers -> where their creatures live (instance map, or open-world zone)
WHERE = {
    "elwynn": ("box", "elwynn"), "westfall": ("box", "westfall"), "rfc": ("map", 389), "wc": ("map", 43), "dm": ("map", 36),
    "sfk": ("map", 33), "bfd": ("map", 48), "stocks": ("map", 34), "gnomer": ("map", 90), "rfk": ("map", 47),
    "sm": ("map", 189), "rfd": ("map", 129), "uld": ("map", 70), "zf": ("map", 209), "mara": ("map", 349),
    "st": ("map", 109), "brd": ("map", 230), "brs": ("map", 229), "dim": ("map", 429), "scholo": ("map", 289),
    "strat": ("map", 329), "zg": ("map", 309), "mc": ("map", 409), "ony": ("map", 249), "aq20": ("map", 509),
    "bwl": ("map", 469), "aq40": ("map", 531), "naxx": ("map", 533),
}
LEVELS = {}
gd = open(os.path.join(os.path.dirname(HERE), "GearData.lua")).read()
for m in re.finditer(r'key = "(\w+)", name = "[^"]+", min = (\d+), max = (\d+).*?bosses = \{(.*?)\},\n', gd, re.S):
    LEVELS[m.group(1)] = (int(m.group(2)), int(m.group(3)), set(re.findall(r'\{"([^"]+)"', m.group(4))))

BAD_TYPES = {8, 10, 11, 12}          # critter, not specified, totem, non-combat pet
out = {}
for key, where in WHERE.items():
    lo, hi, bosses = LEVELS[key]
    cands = []
    for e, n in spawns[where].most_common():
        t = tmpl.get(e)
        if not t or not models.get(e): continue
        name = t["name"]
        if name in bosses or name in JOURNAL or "Trigger" in name or "Invisible" in name or "[" in name or "(" in name or "DND" in name.upper(): continue
        if int(t["rank"]) in (2, 3, 4): continue                      # rare elite, boss, rare
        if where[0] == "map" and n < 2: continue                     # one-off spawns in instances are named bosses
        if int(t["type"]) in BAD_TYPES: continue
        if int(t["npcflag"]) != 0: continue                          # vendors, quest givers, trainers
        if int(t["unit_flags"]) & 0x2000000 or int(t["unit_flags"]) & 0x2: continue   # not selectable / non attackable
        mn, mx = int(t["minlevel"]), int(t["maxlevel"])
        # raids keep every level (Naxxramas and Ahn'Qiraj creatures sit above 60 in this database)
        if lo < 60 and (mx < lo - 3 or mn > hi + 3): continue
        disp = sorted(models[e])[0][1]
        if any(c["name"] == name for c in cands): continue
        cands.append({"name": name, "display": disp, "spawns": n, "type": int(t["type"])})
        if len(cands) >= 14: break
    out[key] = cands
# raid trash that the database spawns by script rather than placing in the world
EXTRA = {"aq40": ["Qiraji Lasher", "Anubisath Defender", "Vekniss Drone", "Obsidian Eradicator", "Spawn of Fankriss"],
         "ony": ["Onyxian Whelp", "Onyxian Lair Guard"]}
by_name = {}
for e in sorted(tmpl):
    if models.get(e) and tmpl[e]["name"] not in by_name: by_name[tmpl[e]["name"]] = sorted(models[e])[0][1]
for key, names in EXTRA.items():
    for nm in names:
        if nm in by_name and not any(c["name"] == nm for c in out[key]):
            out[key].append({"name": nm, "display": by_name[nm], "spawns": 0, "type": 0})
json.dump(out, open(os.path.join(HERE, "rosters.json"), "w"), indent=1)
# every creature's model by name (lowest entry that has one): real boss models instead of stand-ins
disp_by_name = {}
for e in sorted(tmpl):
    nm = tmpl[e]["name"]
    if nm not in disp_by_name and models.get(e): disp_by_name[nm] = sorted(models[e])[0][1]
json.dump(disp_by_name, open(os.path.join(HERE, "creature_displays.json"), "w"), separators=(",", ":"), sort_keys=True)
for k, v in out.items():
    print("%-8s %2d  %s" % (k, len(v), ", ".join(c["name"] for c in v[:8])))
