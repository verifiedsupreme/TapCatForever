#!/usr/bin/env python3
"""
Builds SpellKitData.lua: the real game spell visuals (SpellVisualKit IDs) that Adventure plays on
the 3D enemies when the cat uses an ability, plus the damage school of every wand (for the colour
of its bolts).

Data: wago.tools DB2 exports for the World of Warcraft: Forever client (product "wowf",
build 1.60.1.71037, interface 16001) and, for wands it has no row for, Classic Era (1.15.9.70576):
  https://wago.tools/db2/<Table>/csv?build=<build>
Tables: SpellName, SpellXSpellVisual, SpellVisual, SpellVisualEvent, SpellVisualKit (Forever),
        ItemSparse (Forever, saved as ItemSparse.csv, and Classic Era, saved as ItemSparse_era.csv)

usage: python3 tools/make_spell_kits.py <data-dir>

How a spell's look is put together (SpellVisualEvent): StartEvent 6 = the impact, 7 = the aura
while it lasts, 11 = a channel; TargetType 1 = the caster, 2 = the target, 4 = the ground.
Only target-side kits are kept: the cat is a cartoon drawing, so its own effects are sprites.
"""
import csv, collections, os, re, sys

DATA = sys.argv[1] if len(sys.argv) > 1 else "."
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "SpellKitData.lua")

# Abilities.lua key -> the real Classic spell (rank 1) it stands for, and spells to borrow a target
# kit from when the spell itself has none (the damage of many area spells is a second spell).
SPELLS = {
    "WARRIOR": {"hs": 78, "bs": 6673, "rend": 772, "tc": 6343, "exe": 5308, "sw": 871, "ww": 1680, "ms": 12294, "reck": 1719},
    "PALADIN": {"sor": 21084, "hl": 635, "judge": (20271, 20187), "hoj": 853, "dev": 465, "cons": (26573, 20116), "ds": 642,
                "bom": 19740, "hs": (20473, 25912)},
    "HUNTER": {"as": 3044, "ss": 1978, "cs": 5116, "pet": 883, "ms": 2643, "aim": 19434, "rf": 3045, "fd": 5384, "ts": 19506},
    "ROGUE": {"ss": 1752, "evis": 2098, "gouge": 1776, "evas": 5277, "snd": 5171, "rupt": 1943, "ks": 408, "bf": 13877, "ar": 13750},
    "PRIEST": {"smite": 585, "swp": 589, "pws": 17, "renew": 139, "mb": 8092, "if": 588, "scream": 8122, "nova": (15237, 23455),
               "sf": 15473},
    "SHAMAN": {"lb": 403, "es": 8042, "hw": 331, "ls": 324, "fs": 8050, "st": (3599, 3606), "wf": 8232, "cl": 421, "storm": 17364},
    "MAGE": {"fb": 133, "fa": 168, "blast": 2136, "nova": 122, "ae": 1449, "bliz": (10, 42208), "pyro": 11366, "block": 11958,
             "barrier": 11426, "ap": 12042},
    "WARLOCK": {"sb": 686, "immo": 348, "corr": 172, "fear": 5782, "vw": 697, "dl": 689, "rof": (5740, 42223), "burn": 17877,
                "coil": 6789},
    "DRUID": {"wrath": 5176, "ht": 5185, "mf": 8921, "roots": 339, "rejuv": 774, "cat": 768, "fb": 22568, "hurr": (16914, 42231),
              "bark": 22812},
}
# the expected spell names, to catch a wrong ID
NAMES = {
    78: "Heroic Strike", 6673: "Battle Shout", 772: "Rend", 6343: "Thunder Clap", 5308: "Execute", 871: "Shield Wall",
    1680: "Whirlwind", 12294: "Mortal Strike", 1719: "Recklessness", 21084: "Seal of Righteousness", 635: "Holy Light",
    20271: "Judgement", 853: "Hammer of Justice", 465: "Devotion Aura", 26573: "Consecration", 642: "Divine Shield",
    19740: "Blessing of Might", 20473: "Holy Shock", 3044: "Arcane Shot", 1978: "Serpent Sting", 5116: "Concussive Shot",
    883: "Call Pet", 2643: "Multi-Shot", 19434: "Aimed Shot", 3045: "Rapid Fire", 5384: "Feign Death", 19506: "Trueshot Aura",
    1752: "Sinister Strike", 2098: "Eviscerate", 1776: "Gouge", 5277: "Evasion", 5171: "Slice and Dice", 1943: "Rupture",
    408: "Kidney Shot", 13877: "Blade Flurry", 13750: "Adrenaline Rush", 585: "Smite", 589: "Shadow Word: Pain",
    17: "Power Word: Shield", 139: "Renew", 8092: "Mind Blast", 588: "Inner Fire", 8122: "Psychic Scream", 15237: "Holy Nova",
    15473: "Shadowform", 403: "Lightning Bolt", 8042: "Earth Shock", 331: "Healing Wave", 324: "Lightning Shield",
    8050: "Flame Shock", 3599: "Searing Totem", 8232: "Windfury Weapon", 421: "Chain Lightning", 17364: "Stormstrike",
    133: "Fireball", 168: "Frost Armor", 2136: "Fire Blast", 122: "Frost Nova", 1449: "Arcane Explosion", 10: "Blizzard",
    11366: "Pyroblast", 11958: "Ice Block", 11426: "Ice Barrier", 12042: "Arcane Power", 686: "Shadow Bolt", 348: "Immolate",
    172: "Corruption", 5782: "Fear", 697: "Summon Voidwalker", 689: "Drain Life", 5740: "Rain of Fire", 17877: "Shadowburn",
    6789: "Death Coil", 5176: "Wrath", 5185: "Healing Touch", 8921: "Moonfire", 339: "Entangling Roots", 774: "Rejuvenation",
    768: "Cat Form", 22568: "Ferocious Bite", 16914: "Hurricane", 22812: "Barkskin",
}
# a wand bolt lands with the impact of a small spell of its school
SCHOOL_SPELLS = {"fire": 2136, "frost": 116, "shadow": 686, "arcane": (5143, 7268), "holy": 585, "nature": 5176,
                 "physical": 78}
DAMAGE_TYPE = {0: "physical", 1: "holy", 2: "fire", 3: "nature", 4: "frost", 5: "shadow", 6: "arcane"}
# wands with no damage type in either client table: guessed from words in the name (a word that
# starts with the given text; "light" only as a whole word, so "Lightweight" is not holy), then arcane
WAND_WORDS = [(r"fire", "fire"), (r"flame", "fire"), (r"burn", "fire"), (r"blaz", "fire"), (r"ember", "fire"),
              (r"cinder", "fire"), (r"scorch", "fire"), (r"smolder", "fire"), (r"charr", "fire"), (r"pyr", "fire"),
              (r"torch", "fire"), (r"frost", "frost"), (r"ice\b", "frost"), (r"icy\b", "frost"), (r"chill", "frost"),
              (r"freez", "frost"), (r"glacia", "frost"), (r"shadow", "shadow"), (r"gloom", "shadow"), (r"umbral", "shadow"),
              (r"doom", "shadow"), (r"necro", "shadow"), (r"dark", "shadow"), (r"decay", "shadow"), (r"bone", "shadow"),
              (r"skull", "shadow"), (r"sorrow", "shadow"), (r"banshee", "shadow"), (r"desolat", "shadow"), (r"hoodoo", "shadow"),
              (r"holy", "holy"), (r"light\b", "holy"), (r"consecrat", "holy"), (r"sun\b", "holy"), (r"nature", "nature"),
              (r"thorn", "nature"), (r"leaf", "nature"), (r"lightning", "nature"), (r"storm", "nature"),
              (r"thunder", "nature"), (r"shock", "nature")]
WAND_WORDS = [(re.compile(r"\b" + w), sch) for w, sch in WAND_WORDS]


def load(name):
    path = os.path.join(DATA, name + ".csv")
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    names = {int(r["ID"]): r["Name_lang"] for r in load("SpellName")}
    sx = collections.defaultdict(list)
    for r in load("SpellXSpellVisual"):
        sx[int(r["SpellID"])].append(r)
    events = collections.defaultdict(list)
    for r in load("SpellVisualEvent"):
        events[int(r["SpellVisualID"])].append(r)
    kits = {int(r["ID"]) for r in load("SpellVisualKit")}

    def visual(spell):
        rows = [r for r in sx.get(spell, []) if r["DifficultyID"] == "0"] or sx.get(spell, [])
        plain = [r for r in rows if all(r.get(k, "0") == "0" for k in ("CasterUnitConditionID", "CasterPlayerConditionID",
                                                                       "ViewerUnitConditionID", "ViewerPlayerConditionID"))]
        rows = plain or rows
        rows.sort(key=lambda r: (-int(r.get("Priority") or 0), int(r["ID"])))
        return int(rows[0]["SpellVisualID"]) if rows else None

    def kit(spell, start, targets):
        v = visual(spell)
        if not v:
            return None
        for t in targets:
            for e in sorted(events.get(v, []), key=lambda e: int(e["ID"])):
                k = int(e["SpellVisualKitID"])
                if e["StartEvent"] == str(start) and e["TargetType"] == str(t) and k in kits:
                    return k
        return None

    def kits_for(ids):
        ids = ids if isinstance(ids, tuple) else (ids,)
        impact = aura = chan = None
        for s in ids:
            impact = impact or kit(s, 6, (2, 4))
            aura = aura or kit(s, 7, (2,))
            chan = chan or kit(s, 11, (2,))
        return ids[0], impact or chan, aura

    problems = []
    lines = ["-- Generated by tools/make_spell_kits.py from wago.tools DB2 exports (World of Warcraft: Forever 1.60.1.71037;",
             "-- wand damage types also from Classic Era 1.15.9.70576). Do not edit by hand.",
             "-- TCF.SPELL_KITS[class][ability] = { spell ID, impact kit on the target, aura kit on the target while it lasts }",
             "-- (0 = none). AdventureFX.lua plays them on the 3D enemies with SetSpellVisualKit.",
             "local _, TCF = ...", "", "TCF.SPELL_KITS = {"]
    counts = collections.Counter()
    for cls in ("WARRIOR", "PALADIN", "HUNTER", "ROGUE", "PRIEST", "SHAMAN", "MAGE", "WARLOCK", "DRUID"):
        parts = []
        for key, ids in SPELLS[cls].items():
            sid, impact, aura = kits_for(ids)
            if names.get(sid) != NAMES.get(sid):
                problems.append("%s %s: spell %d is %r, expected %r" % (cls, key, sid, names.get(sid), NAMES.get(sid)))
            counts["impact" if impact else "no impact"] += 1
            counts["aura" if aura else "no aura"] += 1
            parts.append('%s = { %d, %d, %d }' % (key if re.match(r"^[a-z]+$", key) and key not in ("if",) else '["%s"]' % key,
                                                  sid, impact or 0, aura or 0))
        lines.append("  %s = { %s }," % (cls, ", ".join(parts)))
    lines.append("}")
    lines.append("-- impact kit by damage school, for wand bolts and abilities with no kit of their own")
    sk = []
    for school, ids in SCHOOL_SPELLS.items():
        _, impact, _ = kits_for(ids)
        if not impact:
            problems.append("school %s: no impact kit" % school)
        sk.append("%s = %d" % (school, impact or 0))
    lines.append("TCF.SCHOOL_KITS = { %s }" % ", ".join(sk))

    # wand damage schools
    wands = {}
    for fn in ("GearData.lua", "WorldGearData.lua"):
        for m in re.finditer(r'G\((\d+),"((?:[^"\\]|\\.)*)","[^"]*",\d+,\d+,\d+,"RANGED","wand"', open(os.path.join(ROOT, fn), encoding="utf-8").read()):
            wands[int(m.group(1))] = m.group(2)
    types = {}
    for fn in ("ItemSparse_era.csv", "ItemSparse.csv"):   # Forever wins where both have the item
        p = os.path.join(DATA, fn)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    i = int(r["ID"])
                    if i in wands and r.get("DamageType", "") != "":
                        types[i] = DAMAGE_TYPE.get(int(r["DamageType"]), "arcane")
    guessed = 0
    guesses = []
    out = []
    for i in sorted(wands):
        s = types.get(i)
        if not s or s == "physical":
            low = wands[i].lower()
            s = next((sch for w, sch in WAND_WORDS if w.search(low)), "arcane")
            guessed += 1
            guesses.append("%d %s -> %s" % (i, wands[i], s))
        out.append("[%d]=%s" % (i, '"%s"' % s))
    lines.append("-- damage school of every wand (item ID -> school); %d from the client tables, %d guessed from the name" % (len(wands) - guessed, guessed))
    lines.append("TCF.WAND_SCHOOL = {")
    for k in range(0, len(out), 10):
        lines.append("  " + ", ".join(out[k:k + 10]) + ",")
    lines.append("}")
    open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("spell kits:", dict(counts), "schools:", len(sk), "wands:", len(wands), "guessed:", guessed)
    for g in guesses:
        print("  guessed:", g)
    for p in problems:
        print("  problem:", p)


if __name__ == "__main__":
    main()
