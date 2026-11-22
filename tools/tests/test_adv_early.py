# Adventure track C: Auto-advance tries a zone 2 levels early (raids still wait for 60), starter-zone
# final bosses have 1.1x health, and a new cat's first half hour of Adventure is measured.
def check(seed, load_addon):
    lua = load_addon()
    lua.execute("_seed = %d; math.randomseed(_seed)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local bad = {}
      local function ck(c, m) if not c then bad[#bad + 1] = m end end
      ck(T:AdvAutoLevel(2) == 8, "Westfall opens for Auto-advance at 8: " .. tostring(T:AdvAutoLevel(2)))
      for i, t in ipairs(T.TIERS) do
        if t.raid then ck(T:AdvAutoLevel(i) == 60, t.name .. " waits for 60") end
      end
      -- final boss health: 1.1x in zones under level 20, 1.3x elsewhere (compared with the other bosses)
      local function finalRatio(ti)
        local n = T:AdvStages(ti)
        local p1 = T:AdvPack(ti, n)
        local hp, _ = T.AdvMobBase(T:AdvLevel(ti, n))
        local mult = T.TIERS[ti].raid and T.ADV.RAIDBOSS or T.ADV.BOSS
        return p1[1].max / (hp * mult.hp)
      end
      ck(math.abs(finalRatio(1) - 1.1) < 0.01, "Hogger has 1.1x health: " .. finalRatio(1))
      local sfk
      for i, t in ipairs(T.TIERS) do if t.key == "sfk" then sfk = i end end
      ck(math.abs(finalRatio(sfk) - 1.3) < 0.01, "Arugal keeps 1.3x health: " .. finalRatio(sfk))
      -- a new cat: Adventure with about 1.8 key presses a second, equipping what it finds
      local cls = T.CLASSES[_seed % #T.CLASSES + 1].key
      T:SetClass(cls)
      local orig = T.GrantGear
      local toasts = 0
      local origToast = T.ShowLootToast
      T.GrantGear = function(self, it, reason, ...)
        local slot = T:BestGearSlot(it, cls)
        local wasEmpty = slot and not T:GearEquipped(cls)[slot]
        local res = orig(self, it, reason, ...)
        if slot and T:CanEquipGear(it, cls) and (wasEmpty or (T:GearUpgrade(it, cls) or 0) > 0) then T:EquipGear(it.id, slot, cls) end
        return res
      end
      T:AdvStart()
      local kb = TapCatForeverKeyListener
      local t, acc, tW, t10 = 0, 0, nil, nil
      while t < 45 * 60 and not (tW and t10) do
        _clock = _clock + 0.25; t = t + 0.25
        T:AdvTick(0.25)
        acc = acc + 1.8 * 0.25
        while acc >= 1 do kb.scripts.OnKeyDown(kb, "Q"); acc = acc - 1 end
        if not tW and T:CD().adv.tier >= 2 then tW = t end
        if not t10 and T:CD().level >= 10 then t10 = t end
      end
      T.GrantGear = orig
      T:AdvRetreat()
      ck(tW and tW <= 30 * 60, cls .. ": Auto-advance reaches Westfall within 30 minutes: " .. tostring(tW and tW / 60))
      ck(t10 and t10 <= 35 * 60, cls .. ": level 10 within 35 minutes: " .. tostring(t10 and t10 / 60))
      _advEarly = string.format("%s: Westfall at %.0f min, level 10 at %.0f min", cls, (tW or 0) / 60, (t10 or 0) / 60)
      return table.concat(bad, "; ")
    ''')
    if r:
        raise AssertionError("adventure early: " + r)
    print("adventure early section (Auto-advance 2 levels early, raids wait for 60, starter final bosses 1.1x, %s): all checks passed"
          % lua.globals()._advEarly)
