#!/usr/bin/env python3
"""
Balance simulator: loads the real addon code (mocked WoW API), gives a cat
"typical" real gear for a level, learns its abilities, and runs Adventure on
each tier. Prints clear times and defeats so enemy scaling can be tuned.

  python3 tools/balance.py [CLASS ...]
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

def main():
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
