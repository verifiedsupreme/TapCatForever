# 1.6.2: the goods a gathering spot gives (ore, leather, cloth) grow with the x3 profit upgrades and with
# Renown (+2% each), like its Trade Gold. Fractions of a good are kept for the next cycle, so nothing is
# lost to rounding and nothing is made up.
# Run on its own through the harness.

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      local s = T:ProfState()
      local fam = "cloth"
      local cloth = T.FAMILIES[fam].ops[1][2]
      local st = s.ops[fam][1]
      st.n, st.mgr, st.p = 1, true, 0
      -- (1.7.0) this test is about upgrades and Renown: leave the helper's own bonus out (test_prof2.py has it)
      local helperGoods = T.HelperGoodsMult
      T.HelperGoodsMult = function() return 1 end
      -- plain: 1 a cycle, as before
      ck(T:OpMatsPerCycle(fam, 1) == 1, "plain spot: 1 good a cycle: " .. T:OpMatsPerCycle(fam, 1))
      local m0 = s.mats[cloth] or 0
      T:ProfAdvance(T:OpCycleTime(fam, 1) * 10 + 0.001)
      ck((s.mats[cloth] or 0) - m0 == 10, "10 plain cycles give 10: " .. ((s.mats[cloth] or 0) - m0))
      -- one x3 upgrade for this spot and one for all spots: 9 a cycle
      s.upgrades[fam .. "1_0"], s.upgrades[fam .. "_all0"] = true, true
      ck(T:OpMatsPerCycle(fam, 1) == 9, "two x3 upgrades: 9 a cycle: " .. T:OpMatsPerCycle(fam, 1))
      ck(T:OpMatsPerCycle(fam, 2) == T:OpMatsBase(fam, 2) * 3, "the all-spots upgrade counts for the other spots too")
      -- Renown 25: +50%
      s.renown = 25
      ck(math.abs(T:OpMatsPerCycle(fam, 1) - 13.5) < 1e-9, "Renown 25 adds 50%: " .. T:OpMatsPerCycle(fam, 1))
      m0 = s.mats[cloth] or 0
      local c0 = (s.matCarry and s.matCarry[cloth]) or 0
      for _ = 1, 7 do T:ProfAdvance(T:OpCycleTime(fam, 1) + 1e-6) end
      local got = (s.mats[cloth] or 0) - m0
      local carry = s.matCarry[cloth]
      ck(got == math.floor(7 * 13.5 + c0) and math.abs(got + carry - c0 - 7 * 13.5) < 1e-6 and carry >= 0 and carry < 1,
        "7 cycles at 13.5: whole goods now, the half kept: " .. got .. " + " .. tostring(carry))
      ck(math.floor(s.mats[cloth]) == s.mats[cloth], "only whole goods in the bag")
      -- the upgrade rows and Renown say so
      local u
      for _, x in ipairs(T.UPGRADES[fam]) do if x.id == fam .. "1_0" then u = x end end
      ck(u and u.name:find("goods x3", 1, true) and not u.name:find("!", 1, true), "upgrade name: " .. tostring(u and u.name))
      T.HelperGoodsMult = helperGoods
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("profession goods: " + r)
    print("profession goods section (x3 upgrades and Renown multiply goods like Trade Gold, fractions kept): all checks passed")
