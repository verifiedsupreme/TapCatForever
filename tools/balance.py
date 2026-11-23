#!/usr/bin/env python3
"""
Balance simulator: loads the real addon code (mocked WoW API), gives a cat
"typical" real gear for a level, learns its abilities, and runs Adventure on
each tier. Prints clear times and defeats so enemy scaling can be tuned.

  python3 tools/balance.py [CLASS ...]
  python3 tools/balance.py --levels [HOURS] [CLASS ...]
      (1.6.0 level difference) a new cat on Auto-advance with ~1.8 key presses a second, with and
      without the level difference rules: when it reaches each zone, kills, boss kills, defeats;
      then a level 31 cat in Molten Core and a cat at each zone's Auto-advance level.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_harness as H
from lupa import lua51 as L

SIM = r'''
local TCF = TapCatForever
local class, level, quality, minutes, tierIdx, fromTiers = ...
TCF:SetClass(class)
local cd = TCF:CD(class)
cd.level = level
cd.gear = {}
TCF.db.gear = {}
-- typical gear: median item level among usable items of this quality near this level
local function pickFor(slotKey)
  local cands = {}
  for _, it in ipairs(TCF.GEAR_LIST) do
    local ok = it.q == quality and it.req <= level and it.req >= level - 8 and TCF:GearUsable(it, class)
    if ok and fromTiers then
      ok = false
      for _, tt in ipairs(fromTiers) do if it.tier == tt then ok = true end end
    end
    if ok then
      for _, s in ipairs(TCF:GearTargetSlots(it, class)) do if s == slotKey then cands[#cands + 1] = it end end
    end
  end
  table.sort(cands, function(a, b) return a.ilvl < b.ilvl end)
  return cands[math.max(1, math.floor(#cands * 0.5))]
end
for _, s in ipairs(TCF.GEAR_SLOTS) do
  local it = pickFor(s.key)
  if it then
    TCF.db.gear[it.id] = (TCF.db.gear[it.id] or 0) + 1
    if not (s.key == "OFFHAND" and cd.gear.MAINHAND and TCF.GEAR[cd.gear.MAINHAND].slot == "2H") then cd.gear[s.key] = it.id end
  end
end
cd.abilities = {}
for _, a in ipairs(TCF.ABILITIES[class]) do if a.level <= level then cd.abilities[a.key] = true end end
local st = TCF:CombatStats(class)
local adv = cd.adv
adv.tier, adv.stage, adv.auto, adv.best, adv.cleared, adv.active = tierIdx, 1, true, 0, {}, true
TCF.advRun = nil
local deaths = 0
local oldDefeat = TCF.AdvDefeat
TCF.AdvDefeat = function(self) deaths = deaths + 1; return oldDefeat(self) end
local clearedAt
local steps = minutes * 60 * 4
for i = 1, steps do
  TCF:AdvTick(0.25)
  if adv.tier ~= tierIdx or (adv.best >= tierIdx * 100 + TCF:AdvStages(tierIdx)) then clearedAt = i / 4; break end
end
TCF.AdvDefeat = oldDefeat
return st.dps, st.hp, st.armor, st.ilvl, clearedAt or -1, deaths, adv.best
'''

PROG = r'''
local cls, hours, on, seed = ...
math.randomseed(seed)
local T = TapCatForever
T.ADV.LEVEL_DIFF = on
T:SetClass(cls)
T.RefreshAll = function() end
T.Print = function() end
local orig = T.GrantGear
T.GrantGear = function(self, it, reason, ...)   -- equips what it finds when it is better
  local slot = T:BestGearSlot(it, cls)
  local wasEmpty = slot and not T:GearEquipped(cls)[slot]
  local res = orig(self, it, reason, ...)
  if slot and T:CanEquipGear(it, cls) and (wasEmpty or (T:GearUpgrade(it, cls) or 0) > 0) then T:EquipGear(it.id, slot, cls) end
  return res
end
local deaths = 0
local od = T.AdvDefeat
T.AdvDefeat = function(self) deaths = deaths + 1; return od(self) end
T:AdvStart()
local kb = TapCatForeverKeyListener
local t, acc, last = 0, 0, 0
local reach = {}
while t < hours * 3600 do
  _clock = _clock + 0.25; t = t + 0.25
  T:AdvTick(0.25)
  acc = acc + 1.8 * 0.25
  while acc >= 1 do kb.scripts.OnKeyDown(kb, "Q"); acc = acc - 1 end
  local adv = T:CD().adv
  if adv.tier ~= last then
    last = adv.tier
    local k = T.TIERS[adv.tier].key
    if not reach[k] then reach[k] = math.floor(t / 60) end
  end
  if t % 600 == 0 then   -- every 10 minutes: open chests, learn the abilities of its level
    for _, ch in ipairs(T.CHESTS) do local n = 0; while (T.db.keys[ch.key] or 0) > 0 and n < 50 do n = n + 1; pcall(T.OpenChest, T, ch.key, true) end end
    for _, a in ipairs(T.ABILITIES[cls]) do if a.level <= T:CD().level then T:CD().abilities[a.key] = true end end
  end
end
return reach, deaths, T:CD().adv.kills, T:CD().adv.bossKills, T:CD().level
'''

FIXED = r'''
local cls, level, tierIdx, on, secs = ...
local T = TapCatForever
T.ADV.LEVEL_DIFF = on
T:SetClass(cls)
T.RefreshAll = function() end
T.Print = function() end
local cd = T:CD(cls)
cd.level = level; cd.gear = {}
local bag = T:Bag(cls)
local q = level < 30 and 2 or 3
local function pickFor(slotKey)   -- typical gear: the median item of this quality near the level
  local cands = {}
  for _, it in ipairs(T.GEAR_LIST) do
    if it.q == q and it.req <= level and it.req >= level - 8 and T:GearUsable(it, cls) then
      for _, s in ipairs(T:GearTargetSlots(it, cls)) do if s == slotKey then cands[#cands + 1] = it end end
    end
  end
  table.sort(cands, function(a, b) return a.ilvl < b.ilvl end)
  return cands[math.max(1, math.floor(#cands * 0.5))]
end
for _, s in ipairs(T.GEAR_SLOTS) do
  local it = pickFor(s.key)
  if it then bag[it.id] = (bag[it.id] or 0) + 1
    if not (s.key == "OFFHAND" and cd.gear.MAINHAND and T.GEAR[cd.gear.MAINHAND].slot == "2H") then cd.gear[s.key] = it.id end end
end
cd.abilities = {}
for _, a in ipairs(T.ABILITIES[cls]) do if a.level <= level then cd.abilities[a.key] = true end end
local adv = cd.adv
adv.tier, adv.stage, adv.auto, adv.active, adv.best = tierIdx, 1, false, true, tierIdx * 100 + 99
T.advRun = nil
local deaths, first, t = 0, nil, 0
local od = T.AdvDefeat
T.AdvDefeat = function(self) deaths = deaths + 1; first = first or t; adv.tier, adv.stage = tierIdx, 1; return od(self) end
local k0, gap = adv.kills, T:AdvLevelGap(cls)
while t < secs do t = t + 0.25; T:AdvTick(0.25) end
T.AdvDefeat = od
return deaths, first or -1, adv.kills - k0, gap
'''

def levels(hours, classes, seeds=(1, 2)):
    def fn(code):
        lua = H.load_addon()
        return lua, lua.execute("return function(...) local f = assert(loadstring([==[" + code + "]==])); return f(...) end")
    keys = ["westfall", "rfc", "wc", "dm", "sfk", "bfd", "gnomer", "sm", "rfd", "uld", "zf", "mara", "st", "brd"]
    tot = {False: [0, 0, 0], True: [0, 0, 0]}
    print("Auto-advance from level 1, %g hours, ~1.8 key presses a second: minutes to reach each zone, off -> on" % hours)
    for c in classes:
        for sd in seeds:
            res = {}
            for on in (False, True):
                lua, f = fn(PROG)
                reach, deaths, kills, boss, lvl = f(c, hours, on, sd)
                res[on] = ({k: reach[k] for k in keys if reach[k] is not None}, deaths, kills, boss, lvl)
                for i, v in enumerate((kills, boss, deaths)): tot[on][i] += v
            a, b = res[False], res[True]
            zones = " ".join("%s %d>%d" % (k, a[0][k], b[0][k]) for k in keys if k in a[0] and k in b[0])
            print(f"{c:8s} seed {sd}: level {a[4]}>{b[4]} kills {a[2]}>{b[2]} boss kills {a[3]}>{b[3]} defeats {a[1]}>{b[1]} | {zones}")
    print("all: kills x%.3f, boss kills x%.3f, defeats x%.2f" % (tot[True][0] / tot[False][0], tot[True][1] / tot[False][1], tot[True][2] / max(1, tot[False][2])))
    lua, f = fn(FIXED)
    tiers = lua.eval("TapCatForever.TIERS"); n = len(tiers)
    mc = [i for i in range(1, n + 1) if tiers[i].key == "mc"][0]
    print("\nA level 31 cat with typical level 31 gear in Molten Core, 10 minutes: off -> on")
    for c in classes:
        r = {}
        for on in (False, True):
            lua, f = fn(FIXED)
            r[on] = f(c, 31, mc, on, 600)
        print(f"{c:8s} kills {r[False][2]}>{r[True][2]}  defeats {r[False][0]}>{r[True][0]}  first defeat {r[False][1]:.0f}s>{r[True][1]:.0f}s  (enemies {r[True][3]} levels above)")
    print("\nA cat at each zone's Auto-advance level with typical gear, 10 minutes on stage 1 onward: kills off -> on (defeats)")
    for ti in range(2, n + 1):
        t = tiers[ti]
        if t.raid: continue
        lvl = lua.eval("TapCatForever:AdvAutoLevel(%d)" % ti)
        row = []
        for c in classes:
            r = {}
            for on in (False, True):
                l2, f = fn(FIXED)
                l2.execute("TapCatForever:CD(%r).adv.auto = true" % c)
                r[on] = f(c, lvl, ti, on, 600)
            row.append("%s %d>%d (%d>%d)" % (c[:3], r[False][2], r[True][2], r[False][0], r[True][0]))
        print(f"{t.key:8s} L{lvl:2d}: " + "  ".join(row))

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--levels":
        rest = sys.argv[2:]
        hours = float(rest.pop(0)) if rest and rest[0].replace(".", "").isdigit() else 20
        levels(hours, rest or ["WARRIOR", "MAGE", "ROGUE", "PRIEST", "HUNTER"])
        return
    lua = H.load_addon()
    sim = lua.execute("return function(...) local f = assert(loadstring([==[" + SIM + "]==])); return f(...) end")
    classes = sys.argv[1:] or ["WARRIOR", "MAGE", "ROGUE", "PRIEST", "HUNTER"]
    tiers = lua.eval("TapCatForever.TIERS")
    n = len(tiers)
    rows = []
    for c in classes:
        print("\n==", c)
        for ti in range(1, n + 1):
            t = tiers[ti]
            raid = t.raid
            if not raid:
                level = min(60, (t.min + t.max) // 2 + 1)
                q = 2 if level < 30 else 3
                frm = None
            else:
                level, q = 60, 4
                prev = {"zg": None, "mc": None, "ony": None, "aq20": ["zg", "mc"], "bwl": ["mc", "ony"], "aq40": ["mc", "bwl", "zg"], "naxx": ["bwl", "aq40"]}[t.key]
                if prev is None: q = 3
                frm = None
                if prev:
                    idx = [i for i in range(1, n + 1) if tiers[i].key in prev]
                    frm = lua.table_from(idx)
            dps, hp, arm, ilvl, clear, deaths, best = sim(c, level, q, 30, ti, frm)
            print(f"{t.key:9s} L{level:2d} q{q} ilvl{ilvl:3d}  dps {dps:7.1f} hp {hp:6.0f} arm {arm:5.0f}  clear {('%5.0fs' % clear) if clear > 0 else ' FAIL':>6} deaths {deaths:2d}  best {best}")

if __name__ == "__main__":
    main()
