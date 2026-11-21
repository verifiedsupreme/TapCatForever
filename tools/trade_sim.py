#!/usr/bin/env python3
"""Professions economy simulations, run on the real addon code (mocked WoW API, see test_harness.py).

  python3 tools/trade_sim.py [hours]
      The idle tycoon of the current class's family (the test cat is a Mage: Tailoring cloth spots):
      1 key press/second, greedy buying every 5 s, for `hours` of online play (default 12).

  python3 tools/trade_sim.py --parity [hours_online_per_day] [days]
      Plays the same player (same random numbers) once as a Warrior (Mining), a Rogue (Skinning)
      and a Mage (Tailoring), online N hours a day and idle the rest, and compares Trade Gold,
      lifetime gold, spots and materials. They must be identical (exit code 1 if not).

  python3 tools/trade_sim.py --craft [hours_online_per_day ...] [--days N] [--attentive] [--grinder]
      How long a normal player takes to level Blacksmithing, Leatherworking and Tailoring 1 -> 300.
      The player is online N hours a day (default 1, 2 and 4) and idle the rest (helpers keep working
      offline; a daily login collects the full day, the cap is 24 h).
      Casual player (default): looks at the Professions window every 15 minutes while online; then it
      buys everything affordable (upgrades, helpers, spots), restarts spots without a helper and
      crafts. It clicks the hand tool 20% of the online time.
      --attentive: buys every 5 s and clicks the tool whenever it is ready (the best case).
      Crafting: always the gear recipe with the best skill-up chance, and among those the cheapest in
      hours of production; it also crafts after each idle stretch. Crafted gear is sold once a day
      (Trade Gold). It never crafts grey recipes (75+ below its skill): a normal player stops making
      those. --grinder also crafts grey recipes when they are cheaper per expected skill point, using
      the grey chance measured from the real TCF:ProfSkillUp, to show what grinding greys is worth.
      No prestige is modelled (a prestige resets the spots, so a player who sells the business
      levels more slowly) and nothing else spends the materials (cosmetics, First Aid, Cooking).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_harness as H

# ---------------------------------------------------------------- the original tycoon run
SIM = r'''
local TCF = TapCatForever
local hours = ...
local ps = TCF:ProfState()
local fam = TCF:MainProf()
for k = 1, 4 do _clock = _clock + 2; TCF:GatherClick(fam, 1) end
TCF:BuyOp(fam, 1, 1)
local marks, out = { 0.5, 1, 2, 4, 8, 12, 24, 48 }, {}
local mi = 1
local t = 0
local unlockAt = {}
while t < hours * 3600 do
  for k = 1, 20 do TCF:ProfTap(); _clock = _clock + 0.25; TCF:ProfAdvance(0.25) end  -- 5 seconds
  t = t + 5
  TCF:GatherClick(fam, 1)
  for i = 1, 6 do TCF:RunOp(fam, i) end
  for _, u in ipairs(TCF.UPGRADES[fam]) do if not ps.upgrades[u.id] and u.cost <= ps.gold then TCF:BuyUpgrade(u.id) end end
  for i = 1, 6 do TCF:HireForeman(fam, i) end
  for i = 6, 1, -1 do TCF:BuyOp(fam, i, "max") end
  for _, p in ipairs(TCF.PROFESSIONS) do
    if p.renown > 0 and not unlockAt[p.key] and TCF:RenownOnReset() >= p.renown then unlockAt[p.key] = t / 3600 end
  end
  if t >= marks[mi] * 3600 then
    local o = ps.ops[fam]
    local m = TCF.FAMILIES[fam].ops
    out[#out + 1] = string.format("%5.1fh lifetime %-9s %s %d/%d/%d/%d/%d/%d  renown-on-reset %d  %s %d %s %d",
      marks[mi], TCF.FormatBig(ps.lifetime), fam, o[1].n, o[2].n, o[3].n, o[4].n, o[5].n, o[6].n, TCF:RenownOnReset(),
      m[5][2], ps.mats[m[5][2]] or 0, m[6][2], ps.mats[m[6][2]] or 0)
    mi = mi + 1
    if not marks[mi] then break end
  end
end
for k, v in pairs(unlockAt) do out[#out + 1] = string.format("first sale would unlock %s after %.1fh", k, v) end
return table.concat(out, "\n")
'''

# ---------------------------------------------------------------- shared player model
PLAYER = r'''
local TCF = TapCatForever
local P = {}
_SIMP = P
-- quiet and fast: no chat lines, sounds, loot notices or window refreshes in a simulation
TCF.Print = function() end
TCF.PlaySound = function() end
TCF.RefreshAll = function() end
TCF.ShowLootReveal = function() end
TCF.MarkDirty = function() end

function P.start(class, seed)
  TCF:SetClass(class)
  TCF.db.trade = nil
  P.s = TCF:ProfState()
  P.fam, P.craft = TCF:MainProf(), TCF:CraftProf()
  P.ops = P.s.ops[P.fam]
  math.randomseed(seed or 1)
  P.t = 0          -- real seconds since the start
  P.online = 0     -- online seconds since the start
end

local function allAutomated()
  for i = 1, 6 do local o = P.ops[i]; if o.n > 0 and not o.mgr then return false end end
  return P.ops[1].n > 0
end

-- greedy buying, as tools/trade_sim.py always did: upgrades, helpers, then spots (best first)
local function buy()
  local s, fam = P.s, P.fam
  for _, u in ipairs(TCF.UPGRADES[fam]) do if not s.upgrades[u.id] and u.cost <= s.gold then TCF:BuyUpgrade(u.id) end end
  for i = 1, 6 do if not P.ops[i].mgr and P.ops[i].n > 0 then TCF:HireForeman(fam, i) end end
  for i = 6, 1, -1 do TCF:BuyOp(fam, i, "max") end
end

-- online play for `sec` seconds. every = how often (seconds) the player looks at the Professions
-- window: buys, restarts spots without a helper and runs onCheck() (crafting). click = share of
-- the online time the tool is clicked whenever it is ready (an attentive player 1, a casual one less).
function P.play(sec, onCheck, every, click)
  local fam = P.fam
  every, click = every or 5, click or 1
  local done, nextCheck = 0, 0
  while done < sec do
    local dt = allAutomated() and 5 or 1
    _clock = _clock + dt
    if click >= 1 or (done % 100) < click * 100 then
      -- the tool on the best spot owned (the first spot works from the start)
      local best = 1
      for i = 6, 2, -1 do if P.ops[i].n > 0 then best = i; break end end
      TCF:GatherClick(fam, best)
    end
    local check = done >= nextCheck
    if check or every <= 5 then
      for i = 1, 6 do local o = P.ops[i]; if o.n > 0 and not o.mgr and not o.run then TCF:RunOp(fam, i) end end
    end
    TCF:ProfAdvance(dt)
    done = done + dt; P.t = P.t + dt; P.online = P.online + dt
    if check then
      nextCheck = nextCheck + every
      buy()
      if onCheck then onCheck() end
    end
  end
end

-- idle for `sec` seconds: what a login after that time gives (helpers only, 24 h cap)
function P.idle(sec)
  TCF:ProfAdvance(math.min(sec, TCF.PROF_OFFLINE_CAP), true)
  P.t = P.t + sec
end
'''

PARITY = r'''
local P = _SIMP
local TCF = TapCatForever
local class, online, days = ...
P.start(class, 4242)
for d = 1, days do
  P.play(online * 3600, nil, 5, 1)
  P.idle((24 - online) * 3600)
end
local s = P.s
local mats = {}
for i, o in ipairs(TCF.FAMILIES[P.fam].ops) do mats[i] = string.format("%d", s.mats[o[2]] or 0) end
local n = {}
for i = 1, 6 do n[i] = P.ops[i].n end
return P.fam, s.gold, s.lifetime, TCF:GatherIncome(P.fam), table.concat(n, "/"), table.concat(mats, "/")
'''

CRAFT = r'''
local P = _SIMP
local TCF = TapCatForever
local class, online, maxDays, grinder, every, click = ...
P.start(class, 99)
local s, craft = P.s, P.craft
-- the skill-up chance of a grey recipe, measured from the real TCF:ProfSkillUp
local ups, N = 0, 4000
for k = 1, N do s.skill[craft] = 200; if TCF:ProfSkillUp(craft, 1) then ups = ups + 1 end end
s.skill[craft] = nil
local grey = ups / N
local recipes = {}
for _, r in ipairs(TCF.RECIPES[craft]) do if r.gear then recipes[#recipes + 1] = r end end
local tierOf = {}
for i, o in ipairs(TCF.FAMILIES[P.fam].ops) do tierOf[o[2]] = i end
local function chance(skill, need)
  local gap = skill - need
  if gap < 25 then return 1 elseif gap < 50 then return 0.5 elseif gap < 75 then return 0.25 end
  return grinder and grey or 0
end
local function matRate(tier)   -- materials a second from that spot (helper or not)
  local i = tier
  if P.ops[i].n < 1 then return 1e-6 end
  return TCF:OpMatsPerCycle(P.fam, i) / TCF:OpCycleTime(P.fam, i)
end
local crafts, goldBack, marks, firstGear = 0, 0, {}, nil
local MARKS = { 25, 75, 125, 175, 230, 275, 300 }
local function note()
  local sk = TCF:ProfSkill(craft)
  for _, m in ipairs(MARKS) do if sk >= m and not marks[m] then marks[m] = { P.t, P.online } end end
end
local function craftAll()
  for guard = 1, 5000 do
    local sk = TCF:ProfSkill(craft)
    if sk >= 300 then return end
    local best, bestKey
    for _, r in ipairs(recipes) do
      if r.skill <= sk then
        local ch = chance(sk, r.skill)
        if ch > 0 and TCF:CanCraft(r) then
          local cost = 0
          for m, n in pairs(r.mats) do cost = cost + n / matRate(tierOf[m]) end
          -- normal player: best chance first, then cheapest; grinder: cheapest per expected point
          local key = grinder and (cost / ch) or (-ch * 1e15 + cost)
          if not bestKey or key < bestKey then best, bestKey = r, key end
        end
      end
    end
    if not best then return end
    TCF:Craft(best)
    crafts = crafts + 1
    if not firstGear then firstGear = { P.t, P.online } end
    note()
  end
end
local function sellCrafted()
  for id, n in pairs(TCF:Bag()) do
    local it = TCF.GEAR[id]
    if it and it.crafted then local _, g = TCF:SellGear(id, true); goldBack = goldBack + (g or 0) end
  end
end
local day = 0
while day < maxDays and TCF:ProfSkill(craft) < 300 do
  day = day + 1
  P.play(online * 3600, craftAll, every, click)
  craftAll(); sellCrafted()
  P.idle((24 - online) * 3600)
  craftAll()
end
sellCrafted()
local out = {}
local function when(m)
  if not m then return "not reached" end
  local t, on = m[1], m[2]
  local real = t < 2 * 3600 and string.format("%.0f min", t / 60) or t < 48 * 3600 and string.format("%.1f h", t / 3600) or string.format("day %.1f", t / 86400)
  return string.format("%-10s (%.1f h online)", real, on / 3600)
end
out[#out + 1] = string.format("  first gear crafted: %s", when(firstGear))
for _, m in ipairs(MARKS) do out[#out + 1] = string.format("  skill %3d: %s", m, when(marks[m])) end
out[#out + 1] = string.format("  %d crafts, skill %d after %d days; grey skill-up chance measured %.1f%%; crafted gear sold for %s Trade Gold",
  crafts, TCF:ProfSkill(craft), day, grey * 100, TCF.FormatBig(goldBack))
return table.concat(out, "\n"), marks[300] and marks[300][1] or -1
'''

CLASS_OF = {"blacksmithing": "WARRIOR", "leatherworking": "ROGUE", "tailoring": "MAGE"}


def run_parity(argv):
    nums = [float(a) for a in argv if not a.startswith("--")]
    online = nums[0] if nums else 2.0
    days = int(nums[1]) if len(nums) > 1 else 3
    lua = H.load_addon()
    lua.execute(PLAYER)
    f = lua.execute("return function(...) local f = assert(loadstring([==[" + PARITY + "]==])); return f(...) end")
    rows = []
    for cls in ("WARRIOR", "ROGUE", "MAGE"):
        rows.append(f(cls, online, days))
    print("Same player, %.1f h online a day for %d days (idle the rest):" % (online, days))
    for fam, gold, life, inc, n, mats in rows:
        print("  %-8s Trade Gold %.6g  lifetime %.6g  income %.6g/s  spots %s  materials %s" % (fam, gold, life, inc, n, mats))
    same = all(r[1:] == rows[0][1:] for r in rows)
    print("identical across families:", "yes" if same else "NO")
    return 0 if same else 1


def run_craft(argv):
    grinder = "--grinder" in argv
    # casual (default): looks at the window every 15 minutes, clicks the tool 20% of the time
    every, click, style = (5, 1, "attentive") if "--attentive" in argv else (900, 0.2, "casual")
    days = 120
    if "--days" in argv:
        days = int(argv[argv.index("--days") + 1])
    nums = []
    skip = False
    for i, a in enumerate(argv):
        if skip:
            skip = False
            continue
        if a == "--days":
            skip = True
            continue
        if not a.startswith("--"):
            nums.append(float(a))
    onlines = nums or [1.0, 2.0, 4.0]
    lua = H.load_addon()
    lua.execute(PLAYER)
    f = lua.execute("return function(...) local f = assert(loadstring([==[" + CRAFT + "]==])); return f(...) end")
    for online in onlines:
        for craft, cls in CLASS_OF.items():
            text, t300 = f(cls, online, days, grinder, every, click)
            print("%s (%s cat), %s player online %.1f h a day%s:" % (craft, cls.title(), style, online, ", grinding grey recipes" if grinder else ""))
            print(text)
            sys.stdout.flush()
    return 0


def main():
    argv = sys.argv[1:]
    if "--parity" in argv:
        return run_parity([a for a in argv if a != "--parity"])
    if "--craft" in argv:
        return run_craft([a for a in argv if a != "--craft"])
    lua = H.load_addon()
    f = lua.execute("return function(...) local f = assert(loadstring([==[" + SIM + "]==])); return f(...) end")
    print(f(float(argv[0]) if argv else 12))
    return 0


if __name__ == "__main__":
    sys.exit(main())
