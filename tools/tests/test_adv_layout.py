# 1.6.0 test feedback: the bottom of the Adventure page was jumbled. The fight log and the status
# line under it have their own rows (the status line owns the bottom row, the log shows as many of
# its newest lines as fit above it), the status line for a cleared zone is short, and the
# "<next zone> opens at level N. Running <zone> again" line is logged once per change, not after
# every run of the zone.
# Run on its own:  python3 tools/tests/test_adv_layout.py [seed]
import os, sys

def ck(c, m):
    if not c: raise AssertionError("adventure layout: " + m)

def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % (seed % 2147483647))
    r = lua.execute(r'''
      local T = TapCatForever
      local out = {}
      T:SetClass("MAGE")
      local cd = T:CD()
      local adv = cd.adv
      local function tierOf(k) for i, t in ipairs(T.TIERS) do if t.key == k then return i end end end
      local rfc = tierOf("rfc")
      cd.level = 14
      adv.tier, adv.stage, adv.auto = rfc, T:AdvStages(rfc), true
      adv.best = T.AdvStageCode(rfc, T:AdvStages(rfc))
      T.advLog = {}
      T:AdvReset()
      -- five runs of the cleared zone, each ending at its final stage
      for run = 1, 5 do
        adv.stage = T:AdvStages(rfc)
        T:AdvPackCleared()
        T:AdvLog("Something else happened in run " .. run)
      end
      local waits = 0
      for _, l in ipairs(T.advLog) do if l:find("opens at level", 1, true) then waits = waits + 1 end end
      out.waits = waits
      out.status = T:AdvStatusText()
      -- at the level it needs, the cat moves on
      cd.level = 15
      adv.stage = T:AdvStages(rfc)
      T:AdvPackCleared()
      out.moved = adv.tier ~= rfc
      -- the log fits its rows: long lines count as two
      local long = "|cffff6060Taragaman the Hungerer was too strong.|r Your cat retreats to heal. |cff999999(Better gear, levels and abilities help.)|r and then some more words to make it wrap"
      local list = { long, long, "short", "short", "short", "short" }
      local text = T.UI.AdvLogFit(list, nil, 62)
      local n = 0
      for _ in (text .. "\n"):gmatch("([^\n]*)\n") do n = n + 1 end
      out.fitLines = n
      text = T.UI.AdvLogFit({ long, "short", "short", "short", "short" }, nil, 62)
      n = 0
      for _ in (text .. "\n"):gmatch("([^\n]*)\n") do n = n + 1 end
      out.fitLines2 = n
      out.fitOne = T.UI.AdvLogFit({ "a" }, nil, 62)
      -- the page: the log above the status row, nothing shared
      T:CreateWindow(); T.window:Show(); T.window:SelectTab(2); T.window:Refresh()
      local page
      for _, f in ipairs(_frames) do if f.advLogText then page = f end end
      out.page = page ~= nil
      if page then
        local row = page.advStatusRow
        out.logBottom = 390 + page.advLogH
        out.statusTop = 494 - (row[1] + row[2])
        out.statusSet = page.advStatus ~= nil
      end
      return out
    ''')
    ck(r.waits == 1, "the wait line is logged once over five runs: %d" % r.waits)
    ck(r.status == "Next: Wailing Caverns at level 15 (you are 14). Farming Ragefire Chasm.", "short status: %s" % r.status)
    ck(len(r.status) <= 90 and "!" not in r.status, "the status fits one line")
    ck(r.fitLines == 2 and r.fitLines2 == 3, "four rows: two wrapped lines, or one wrapped and two short (%d, %d)" % (r.fitLines, r.fitLines2))
    ck(r.fitOne == "a", "a short log shows whole")
    ck(r.page and r.statusSet, "the Adventure page has its log and status line")
    ck(r.logBottom <= r.statusTop - 4, "the log ends above the status row (%d, %d)" % (r.logBottom, r.statusTop))
    print("adventure layout section (log above its own status row, %d px apart, newest lines that fit, short cleared status, the wait line once per change): all checks passed"
          % (r.statusTop - r.logBottom))

if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(HERE, ".."))
    import test_harness
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
