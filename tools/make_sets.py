#!/usr/bin/env python3
"""
Builds SetData.lua: the real Classic item sets whose pieces are in the addon's gear
(GearData.lua, WorldGearData.lua, CraftData.lua), with their set bonuses by piece count.

Source: wow-classic-items (MIT, npm), the same data.json tools/make_gear.py reads. Each item's
tooltip carries its set: "Defias Leather (0/5)", the member names, then "(2) Set : ..." bonus
lines. Members are the items whose own tooltip names the set (so ids are exact).

Bonus lines we can model become stats in the addon's keys (the ones TCF:CombatStats adds up:
str agi sta int spi arm ap rap sp heal crit critr hit hitr def dodger mp5 blk). Anything else
(procs, class spell tweaks, resistances, later-expansion stats such as resilience or
expertise) is kept as text and shown greyed as "(no effect on your cat)".

Usage: python3 tools/make_sets.py <data-dir>
  <data-dir> must contain package/data/json/data.json
"""
import json, os, re, sys

DATA = sys.argv[1] if len(sys.argv) > 1 else "."
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "SetData.lua")

CLASSIC_MAX_ID, CLASSIC_MAX_ILVL = 24000, 92

SET_RE = re.compile(r"^(.+) \((\d+)/(\d+)\)$")
BONUS_RE = re.compile(r"^\((\d+)\) Set ?: (.+)$")

# set bonus text -> (stat key, multiplier); the first number in the text is the amount
STAT_RES = [
    (re.compile(r"^\+(\d+) Strength\.?$"), "str"), (re.compile(r"^\+(\d+) Agility\.?$"), "agi"),
    (re.compile(r"^\+(\d+) Stamina\.?$"), "sta"), (re.compile(r"^\+(\d+) Intellect\.?$"), "int"),
    (re.compile(r"^\+(\d+) Spirit\.?$"), "spi"), (re.compile(r"^\+(\d+) Armor\.?$"), "arm"),
    (re.compile(r"^Increases your (?:Stamina|stamina) by (\d+)\.?$"), "sta"),
    (re.compile(r"^Increases (?:your )?spell power by (\d+)\.?$"), "sp"),
    (re.compile(r"^Increases damage and healing done by magical spells and effects by up to (\d+)\.?$"), "sp"),
    (re.compile(r"^Increases (?:your )?attack power by (\d+)\.?$"), "ap"), (re.compile(r"^\+(\d+) Attack Power\.?$"), "ap"),
    (re.compile(r"^Increases (?:your )?ranged attack power by (\d+)\.?$"), "rap"),
    (re.compile(r"^(?:Increases|Improves) (?:your )?critical strike rating by (\d+)\.?$"), "critr"),
    (re.compile(r"^(?:Increases|Improves) (?:your )?hit rating by (\d+)\.?$"), "hitr"),
    (re.compile(r"^Improves your chance to get a critical strike by (\d+)%\.?$"), "crit"),
    (re.compile(r"^Improves your chance to hit by (\d+)%\.?$"), "hit"),
    (re.compile(r"^Increases (?:your )?defense rating by (\d+)\.?$"), "def"),
    (re.compile(r"^Increases (?:your )?dodge rating by (\d+)\.?$"), "dodger"),
    (re.compile(r"^Restores (\d+) mana per 5 sec\.?$"), "mp5"),
    (re.compile(r"^Increases healing done by (?:spells and effects )?by up to (\d+)\.?$"), "heal"),
    (re.compile(r"^Increases healing done by spells and effects by up to (\d+)\.?$"), "heal"),
    (re.compile(r"^Increases the block value of your shield by (\d+)\.?$"), "blk"),
]

def lua_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

def our_gear_ids():
    """Item ids the addon knows as gear: id -> (name, item level, required level), from
    G(id, name, icon, quality, ilvl, req, ...)."""
    ids = {}
    rx = re.compile(r'^G\((\d+),"((?:[^"\\]|\\.)*)","[^"]*",\d+,(\d+),(\d+),')
    for fn in ("GearData.lua", "WorldGearData.lua", "CraftData.lua"):
        for line in open(os.path.join(ROOT, fn), encoding="utf-8"):
            m = rx.match(line)
            if m:
                ids[int(m.group(1))] = (m.group(2), int(m.group(3)), int(m.group(4)))
    return ids

def parse_bonus(text):
    t = text.strip()
    for rx, key in STAT_RES:
        m = rx.match(t)
        if m:
            return key, int(m.group(1))
    return None, None

def main():
    items = json.load(open(os.path.join(DATA, "package/data/json/data.json")))
    gear = our_gear_ids()
    sets = {}   # (name, total) -> {members: {id: name}, bonuses: [(n, text)]}
    for x in items:
        # only wearable pieces (a recipe's tooltip shows the set of the item it makes)
        if x.get("class") not in ("Armor", "Weapon") or x.get("slot") in (None, "Non-equippable"):
            continue
        tt = x.get("tooltip") or []
        for i, t in enumerate(tt):
            m = SET_RE.match(t["label"].strip())
            if not (m and t.get("format") == "Misc"):
                continue
            key = (m.group(1), int(m.group(3)))
            s = sets.setdefault(key, {"members": {}, "bonuses": None})
            s["members"][x["itemId"]] = x["name"]
            bon = []
            for u in tt[i + 1:]:
                b = BONUS_RE.match(u["label"].strip())
                if b:
                    bon.append((int(b.group(1)), b.group(2).strip()))
            if s["bonuses"] is None or len(bon) > len(s["bonuses"]):
                s["bonuses"] = bon
            break
    out, n_members, n_modeled, n_text = [], 0, 0, 0
    for (name, total), s in sorted(sets.items()):
        # members the addon has as Classic gear
        ours = sorted(i for i in s["members"] if i in gear and i < CLASSIC_MAX_ID and gear[i][2] <= CLASSIC_MAX_ILVL)
        if len(ours) < 2 or not s["bonuses"]:
            continue
        # every member must be Classic too (a Burning Crusade set with two old pieces is not a Classic set)
        if any(i >= CLASSIC_MAX_ID for i in s["members"]):
            continue
        n_members += len(ours)
        bonuses = []
        for n, text in sorted(s["bonuses"]):
            key, val = parse_bonus(text)
            if key:
                n_modeled += 1
            else:
                n_text += 1
            bonuses.append((n, text, key, val))
        # members in the item data that the addon has no gear for (shown greyed by name)
        missing = sorted(nm for i, nm in s["members"].items() if i not in ours)
        lvl = max(gear[i][1] for i in ours)   # (item level: sorts the sets from early to late)
        out.append((lvl, name, total, ours, missing, bonuses))
    out.sort(key=lambda r: (r[0], r[1]))
    lines = [
        "-- Generated by tools/make_sets.py from wow-classic-items (MIT). Do not edit by hand.",
        "-- Real Classic item sets whose pieces are in the addon's gear. Each set: name, total pieces,",
        "-- member item ids (the addon's gear), names of members the addon doesn't have, and bonuses",
        "-- { pieces, text, stat, amount } (stat nil: not modelled, shown as no effect on your cat).",
        "local _, TCF = ...",
        "TCF.ITEM_SETS = {",
    ]
    for lvl, name, total, ours, missing, bonuses in out:
        b = ", ".join("{%d,%s%s}" % (n, lua_str(text), (",%s,%d" % (lua_str(k), v)) if k else "") for n, text, k, v in bonuses)
        mi = (", missing = {%s}" % ",".join(lua_str(m) for m in missing)) if missing else ""
        lines.append("  { name = %s, total = %d, items = {%s}%s, bonuses = {%s} }," % (
            lua_str(name), total, ",".join(str(i) for i in ours), mi, b))
    lines.append("}")
    open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("sets:", len(out), "members:", n_members, "bonus lines modelled:", n_modeled, "text only:", n_text,
          "bytes:", os.path.getsize(OUT))

if __name__ == "__main__":
    main()
