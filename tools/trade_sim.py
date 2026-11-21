#!/usr/bin/env python3
"""Simulates the Professions idle tycoon: 1 key press/second, greedy buying every 5 s."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_harness as H

SIM = r'''
local TCF = TapCatForever
local hours = ...
local ps = TCF:ProfState()
for k = 1, 4 do TCF:MineClick(1) end
TCF:BuyOp("mining", 1, 1)
local marks, out = { 0.5, 1, 2, 4, 8, 12, 24, 48 }, {}
local mi = 1
local t = 0
local unlockAt = {}
while t < hours * 3600 do
  for k = 1, 20 do TCF:ProfTap(); TCF:ProfAdvance(0.25) end  -- 5 seconds
  t = t + 5
  for _, u in ipairs(TCF.UPGRADES.mining) do TCF:BuyUpgrade(u.id) end
  for i = 1, 6 do TCF:HireForeman("mining", i) end
  for i = 6, 1, -1 do TCF:BuyOp("mining", i, "max") end
  for _, p in ipairs(TCF.PROFESSIONS) do
    if p.renown > 0 and not unlockAt[p.key] and TCF:RenownOnReset() >= p.renown then unlockAt[p.key] = t / 3600 end
  end
  if t >= marks[mi] * 3600 then
    local o = ps.ops.mining
    out[#out + 1] = string.format("%5.1fh lifetime %-9s mining %d/%d/%d/%d/%d/%d  renown-on-reset %d  thorium %d arcane %d",
      marks[mi], TCF.FormatBig(ps.lifetime), o[1].n, o[2].n, o[3].n, o[4].n, o[5].n, o[6].n, TCF:RenownOnReset(), ps.mats.thorium or 0, ps.mats.arcane or 0)
    mi = mi + 1
    if not marks[mi] then break end
  end
end
for k, v in pairs(unlockAt) do out[#out + 1] = string.format("first sale would unlock %s after %.1fh", k, v) end
return table.concat(out, "\n")
'''

lua = H.load_addon()
f = lua.execute("return function(...) local f = assert(loadstring([==[" + SIM + "]==])); return f(...) end")
print(f(float(sys.argv[1]) if len(sys.argv) > 1 else 12))
