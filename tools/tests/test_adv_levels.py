# 1.6.0 test feedback: "why would a lvl 31 cat have a chance in a lvl 60 raid?" Adventure fights
# now count the level difference like WoW (Adventure.lua TCF.AdvLevelMods, TCF.AdvEnemyLevel).
# Checks:
#   - the rules: nothing up to 3 levels above, then 0.94x damage, 1.06x damage taken and 5% + 2%
#     a level misses per level, the 5% damage floor and 60% miss cap, a small bonus below the cat
#   - enemy levels: a zone's first packs at its lowest level, its last boss 2-3 levels higher,
#     raids at 60
#   - a level 31 cat with level 31 gear in Molten Core loses within seconds and kills nothing
#     (it killed dozens before), and a cat at a zone's Auto-advance level still wins there
#   - misses show as "Miss" in the fight; the plain line on the Adventure page from 5 levels,
#     in the fight panel's top strip, away from the status line at the bottom
# Run on its own:  python3 tools/tests/test_adv_levels.py [seed]
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

def ck(c, m):
    if not c: raise AssertionError("adventure levels: " + m)

def check(seed, load_addon):
    import balance
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    E = lua.eval
    mods = lambda d: tuple(E("{ TapCatForever.AdvLevelMods(%d) }" % d).values())
    near = lambda a, b: abs(a - b) < 1e-9
    for d in (1, 2, 3):
        ck(mods(d) == (1, 0, 1), "%d levels above: as before" % d)
    m4 = mods(4)
    ck(near(m4[0], 0.94) and near(m4[1], 0.07) and near(m4[2], 1.06), "4 levels above: %r" % (m4,))
    m10 = mods(10)
    ck(near(m10[0], 0.94 ** 7) and near(m10[1], 0.19) and near(m10[2], 1.06 ** 7), "10 levels above: %r" % (m10,))
    m29 = mods(29)
    ck(near(m29[0], 0.94 ** 26) and near(m29[1], 0.57) and m29[2] > 4, "29 levels above: %r" % (m29,))
    m59 = mods(59)
    ck(near(m59[0], 0.05) and near(m59[1], 0.6), "the floor and the cap: %r" % (m59,))
    ck(near(mods(-3)[0], 1.03) and near(mods(-20)[0], 1.05) and mods(-20)[1:] == (0, 1), "a small bonus below the cat")
    # enemy levels
    lua.execute('''
      local T = TapCatForever
      _lv = {}
      for i, t in ipairs(T.TIERS) do
        local n = T:AdvStages(i)
        _lv[t.key] = { first = T:AdvStageEnemyLevel(i, 1), last = T:AdvStageEnemyLevel(i, n), min = t.min, raid = t.raid and true or false }
      end
    ''')
    for k, v in E("_lv").items():
        if v.raid:
            ck(v.first == 60 and v.last == 60, "%s counts as level 60: %d %d" % (k, v.first, v.last))
        else:
            ck(v.first == v.min and v.min + 2 <= v.last <= min(60, v.min + 6), "%s: first packs %d (zone from %d), last boss %d" % (k, v.first, v.min, v.last))
    ck(E("_lv.westfall.last") == 12, "Westfall's last boss counts as level 12: %r" % E("_lv.westfall.last"))

    # a level 31 cat in Molten Core, and a cat at a zone's Auto-advance level
    def run(code, *args):
        l2 = load_addon()
        l2.execute("math.randomseed(%d)" % seed)
        f = l2.execute("return function(...) local f = assert(loadstring([==[" + code + "]==])); return f(...) end")
        return f(*args), l2
    mc = E("(function() for i, t in ipairs(TapCatForever.TIERS) do if t.key == 'mc' then return i end end end)()")
    cls = E("TapCatForever.CLASSES[%d].key" % (seed % 9 + 1))
    (off, _), (on, _) = run(balance.FIXED, cls, 31, mc, False, 300), run(balance.FIXED, cls, 31, mc, True, 300)
    ck(off[2] >= 10, "before: a level 31 %s killed %d Molten Core enemies in 5 minutes" % (cls, off[2]))
    ck(on[2] == 0 and 0 <= on[1] <= 20 and on[3] == 29, "now: it kills none and loses within 20 s: %r" % (on,))
    for key in ("westfall", "sfk", "sm", "strat"):
        ti = E("(function() for i, t in ipairs(TapCatForever.TIERS) do if t.key == %r then return i end end end)()" % key)
        lvl = E("TapCatForever:AdvAutoLevel(%d)" % ti)
        (r, _) = run("TapCatForever:CD(%r).adv.auto = true\n" % cls + balance.FIXED, cls, lvl, ti, True, 300)
        (b, _) = run("TapCatForever:CD(%r).adv.auto = true\n" % cls + balance.FIXED, cls, lvl, ti, False, 300)
        ck(r[2] >= 0.85 * b[2] and r[0] <= b[0] + 1, "%s at its Auto-advance level %d still wins: %d kills (%d before), %d defeats (%d before)" % (key, lvl, r[2], b[2], r[0], b[0]))

    # the fight shows misses; the page line from 5 levels
    (res, L) = run(balance.FIXED, cls, 31, mc, True, 1)
    L.execute('''
      local T = TapCatForever
      T:CreateWindow(); T.window:Show(); T.window:SelectTab(2)
      T.advWatching = true
      _misses = 0
      local ev = T.AdvEvent
      T.AdvEvent = function(self, kind, ...) if kind == "miss" then _misses = _misses + 1 end return ev(self, kind, ...) end
      local adv = T:CD().adv
      for i = 1, 400 do T:AdvTick(0.25); adv.tier, adv.active = %d, true end
      T.AdvEvent = ev
    ''' % mc)
    ck(L.eval("_misses") > 10, "misses happen: %d" % L.eval("_misses"))
    L.execute('''
      local T = TapCatForever
      _page = nil
      for _, f in ipairs(_frames) do if f.advGapBar then _page = f end end
      if _page then T.window:Refresh() end
    ''')
    if L.eval("_page ~= nil"):
        txt = L.eval("_page.advGapText:GetText()")
        ck(L.eval("_page.advGapBar:IsShown()") and txt == "Enemies here are 29 levels above your cat: it hits much less and takes far more damage.",
           "the line in Molten Core: %r" % txt)
        ck("!" not in txt, "plain text")
        L.execute('''
          local T = TapCatForever
          local cd = T:CD()
          cd.level = 60; T.advRun = nil; T.window:Refresh()
        ''')
        ck(not L.eval("_page.advGapBar:IsShown()"), "hidden when the cat is level 60 in Molten Core")
        L.execute('''
          local T = TapCatForever
          local cd = T:CD()
          for i, t in ipairs(T.TIERS) do if t.key == "westfall" then cd.adv.tier, cd.adv.stage = i, 1 end end
          T.advRun = nil
          cd.level = 6; T.window:Refresh(); _g6 = T:AdvLevelGap(); _hidden6 = not _page.advGapBar:IsShown()
          cd.level = 5; T.window:Refresh(); _g5 = T:AdvLevelGap()
        ''')
        ck(L.eval("_g6") == 4 and L.eval("_hidden6"), "4 levels: no line (%r)" % L.eval("_g6"))
        ck(L.eval("_g5") == 5 and L.eval("_page.advGapBar:IsShown()") and "are 5 levels above" in L.eval("_page.advGapText:GetText()"), "5 levels: the line")
    else:
        raise AssertionError("adventure levels: the Adventure page wasn't found")
    print("adventure levels section (no change up to 3 levels above, then 0.94x damage, 1.06x taken, 5%% + 2%% misses a level, "
          "floor and cap, small bonus below; zones from their lowest level, raids at 60; a level 31 %s in Molten Core: %d kills before, "
          "none now, lost in %.0f s; Auto-advance levels still win; Miss in the fight, the page line from 5 levels): all checks passed"
          % (cls, off[2], on[1]))

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(HERE, ".."))
    import test_harness
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
