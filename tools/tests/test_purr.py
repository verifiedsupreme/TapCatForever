# 1.6.6 Happy Purrs: pet your cat 100 times in a row (pauses up to TCF.PURR.GAP seconds) and it purrs,
# +5% XP for an hour; while it purrs, 50 pets in a row start the hour again. Each class's cat purrs on its
# own. Pet effects (slot "pet": what floats up when you pet, hearts until you pick another) unlock with
# Happy Purrs on more days and more days in a row. Small indicators only: a heart by the XP bar while it
# purrs, a heart by the class name in the window (grey until then), a one-time hint over the picture.

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      local P = T.PURR
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      local clockT = os.time({ year = 2026, month = 11, day = 2, hour = 12 })
      time = function() return clockT end
      local function pets(n, gap) for _ = 1, n do _clock = _clock + (gap or 0.3); T:PurrPet() end end
      T.PurrTest.reset()
      T:SetClass("MAGE")
      ck(not T:PurrActive() and T:PurrMult() == 1, "no purring to start")
      pets(99)
      ck(not T:PurrActive() and select(1, T:PurrStreak()) == 99, "99 pets: not yet, the count shows 99")
      _clock = _clock + P.GAP + 1
      ck(select(1, T:PurrStreak()) == 0, "a long pause starts the count again")
      pets(99)
      ck(not T:PurrActive(), "99 after the pause: not yet")
      pets(1)
      ck(T:PurrActive() and math.abs(T:PurrMult() - 1.05) < 1e-9 and T:PurrLeft() == 3600, "100 in a row: purring for an hour, +5% XP")
      -- XP from taps and the cat's other XP
      local cd = T:CD("MAGE"); cd.level = 10; cd.xp = 0
      T:AddClassXP("MAGE", 100)
      ck(math.abs(cd.xp - 105) < 1e-6, "the purring cat gets 5% more XP: " .. cd.xp)
      local wcd = T:CD("WARRIOR"); wcd.level = 10; wcd.xp = 0
      T:AddClassXP("WARRIOR", 100)
      ck(wcd.xp == 100 and not T:PurrActive("WARRIOR"), "another cat doesn't purr: no bonus")
      -- refresh with 50 while it purrs
      clockT = clockT + 1800
      ck(T:PurrLeft() == 1800, "half an hour left")
      pets(49)
      ck(T:PurrLeft() == 1800, "49 pets don't refresh it")
      pets(1)
      ck(T:PurrLeft() == 3600, "50 in a row while purring: the hour starts again")
      clockT = clockT + 3601
      ck(not T:PurrActive() and T:PurrMult() == 1, "after the hour it stops")
      -- days and unlocks
      local rr = T.PurrRecord(T)
      ck(rr.days == 1 and rr.run == 1, "one day counted (the refresh on the same day counts once): " .. tostring(rr.days) .. " " .. tostring(rr.run))
      ck(T.db.owned.pet_paw, "the first Happy Purrs unlocks Paw Prints")
      ck(not T.db.owned.pet_note and not T.db.owned.pet_star, "not the later ones yet")
      clockT = clockT + 86400; pets(100)
      clockT = clockT + 86400; pets(100)
      ck(rr.days == 3 and rr.run == 3 and rr.best == 3, "three days in a row: " .. rr.days .. " " .. rr.run)
      ck(T.db.owned.pet_note and T.db.owned.pet_star, "3 days: Purr Notes, 3 in a row: Little Stars")
      clockT = clockT + 2 * 86400; pets(100)
      ck(rr.days == 4 and rr.run == 1 and rr.best == 3, "a day missed starts the run again, the best is kept")
      -- the warrior has its own record and its own unlocks
      T:SetClass("WARRIOR")
      ck(not T.db.owned.pet_paw and not T:PurrActive(), "the Warrior's cat has its own pet effects and purr")
      T:SetClass("MAGE")
      -- the pet effect replaces the hearts
      T:Equip(T.ITEMS.pet_star)
      local look = T:GetAppearance()
      ck(look.pet == T.ITEMS.pet_star, "the pet effect is part of the look")
      local cat = T.cat
      cat:ApplyAppearance(look)
      cat:Pet()
      local used
      for _, o in ipairs(cat.pool.tex) do if o.inUse and o.tex and o.tex:find("t_star", 1, true) then used = true end end
      ck(used, "petting shows Little Stars")
      T:Unequip("pet")
      cat:ApplyAppearance(T:GetAppearance())
      for _, o in ipairs(cat.pool.tex) do o.inUse = false end
      cat:Pet()
      local hearts = true
      for _, o in ipairs(cat.pool.tex) do if o.inUse and o.tex and not o.tex:find("ui_heart", 1, true) then hearts = false end end
      ck(hearts, "with none picked: hearts")
      -- the slot and the how-to-get line
      ck(T.SLOT_BY_KEY.pet and T.SLOT_BY_KEY.pet.look, "a Pet Effect slot")
      ck(T:PurrUnlockLine(T.ITEMS.pet_rainbow):find("30 days in a row", 1, true), "how to get Rainbow Hearts")
      -- the small indicators
      local hud = T.hud
      clockT = clockT + 86400; pets(100)
      hud:Refresh()
      ck(hud.purr:IsShown(), "a heart by the XP bar while it purrs")
      clockT = clockT + 4000; hud:Refresh()
      ck(not hud.purr:IsShown(), "gone when it stops")
      T.db.purrHintSeen = nil
      T:ToggleWindow()
      local win = T.window
      ck(win.purrHint:IsShown(), "the first time the window opens: the hint over the picture")
      win:Hide(); win:Show()
      ck(T.db.purrHintSeen, "only once")
      win.purrButton.SetAlpha = function(f, a) f._alpha = a end
      win:RefreshPurr()
      ck((win.purrButton._alpha or 1) < 1, "the window's heart is grey while the cat doesn't purr")
      local n0 = T.db.stats.pets
      win.petPicture.scripts.OnClick(win.petPicture)
      ck(T.db.stats.pets == n0 + 1 and select(1, T:PurrStreak()) == 1, "the window's picture can be petted")
      -- the tooltip words
      local lines = {}
      local tt = { AddLine = function(_, s) lines[#lines + 1] = s end }
      T:PurrTooltip(tt, true)
      local all = table.concat(lines, " ")
      ck(all:find("100 times in a row", 1, true) and not all:find("!", 1, true), "tooltip: " .. all)
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("happy purrs: " + r)
    print("happy purrs section (100 pets in a row, pauses, +5% XP for an hour, 50 to refresh, per cat, days and runs unlock pet effects, the effect replaces the hearts, small indicators, one hint): all checks passed")
