# 1.8.0 companion cats (Companions.lua, UI_Companions.lua): real WoW cat models bought with TapCoins or
# earned by clearing dungeons, owned by the account, chosen per class cat; the character panel slot; the
# Companion Cats window; Companion Stroll (250,000 TapCoins) walks the companion beside the cat on the
# other side from the party cats, and can be turned off; models the game can't load are hidden.

def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      local db = T.db
      -- the list: prices 5,000 to 100,000, every one with a real display id, earned ones tied to a tier
      local cheapest, dearest, nEarned, seen = math.huge, 0, 0, {}
      for _, c in ipairs(T.COMPANIONS) do
        ck(not seen[c.key] and type(c.display) == "number" and c.display > 0, "a display id: " .. c.key); seen[c.key] = true
        if c.price > 0 then cheapest = math.min(cheapest, c.price); dearest = math.max(dearest, c.price)
        else
          nEarned = nEarned + 1
          ck(T.CompanionTier(c), "an earned companion names a real Adventure tier: " .. c.key)
        end
      end
      ck(#T.COMPANIONS >= 40, "lots of companions: " .. #T.COMPANIONS)
      ck(cheapest == 50000 and dearest == 1000000, "50,000 to 1,000,000: " .. cheapest .. " " .. dearest)
      ck(nEarned >= 8, "some only from dungeons and raids: " .. nEarned)
      ck(T.COMPANION_WALK_PRICE == 1000000, "Companion Stroll is a huge investment")

      -- buying: not enough coins, then bought; it goes on the cat you're playing
      db.coins = 40000
      local ok, why = T:BuyCompanion("orange")
      ck(not ok and why and why:find(T.Commas(50000), 1, true), "Orange Tabby costs 50,000: " .. tostring(why))
      db.coins = 2000000
      ck(T:BuyCompanion("orange") and T:CompanionOwned("orange") and db.coins == 1950000, "bought")
      local me = db.class
      ck(T:Companion() and T:Companion().key == "orange", "the cat you're playing takes it")
      ck(not T:BuyCompanion("orange"), "can't buy it twice")
      ck(not T:BuyCompanion("bigglesworth"), "an earned companion can't be bought")
      -- every class can choose any owned companion, its own one
      ck(T:BuyCompanion("felsaber") and db.coins == 1200000, "Felsaber 750,000")
      local other = (me == "MAGE") and "WARRIOR" or "MAGE"
      ck(T:CD(other).companion == nil, "another cat has none until it chooses")
      ck(T:SetCompanion("felsaber", other) and T:Companion(other).key == "felsaber" and T:Companion().key == "orange", "each cat its own companion")
      ck(not T:SetCompanion("spectral", other), "only owned companions can be chosen")
      ck(T:SetCompanion(nil) and T:Companion() == nil, "a cat can go without")
      T:SetCompanion("orange")

      -- earned in Adventure: clearing Naxxramas brings Mr. Bigglesworth (any class's clear counts)
      local ti = T.CompanionTier(T.COMPANION_BY_KEY.bigglesworth)
      local chat0 = #_chat
      T:CD(other).adv.best = T.AdvStageCode(ti, T:AdvStages(ti))
      T:CheckCompanionUnlocks()
      ck(T:CompanionOwned("bigglesworth"), "cleared Naxxramas: Mr. Bigglesworth")
      local told = false
      for i = chat0 + 1, #_chat do if _chat[i]:find("Mr. Bigglesworth", 1, true) then told = true end end
      ck(told, "told in chat")
      T:CheckCompanionUnlocks()
      local n = 0
      for i = chat0 + 1, #_chat do if _chat[i]:find("Mr. Bigglesworth", 1, true) then n = n + 1 end end
      ck(n == 1, "told once")

      -- Companion Stroll: the walker only with the upgrade, and it can be turned off
      T:CompanionRefresh()
      local w = T.CompanionWalkerFrame()
      ck(not (w and w:IsShown()), "no walker without Companion Stroll")
      db.coins = 999999
      ck(not T:BuyCompanionWalk(), "1,000,000 needed")
      db.coins = 1050000
      ck(T:BuyCompanionWalk() and db.coins == 50000 and T:CompanionWalkOn(), "Companion Stroll bought")
      w = T.CompanionWalkerFrame()
      ck(w and w:IsShown() and w.comp and w.comp.key == "orange", "the companion walks beside the cat")
      -- the walker is party-cat sized and on the left (the party cats' row is on the right)
      ck(w.right == false, "on the left of the cat, away from the party cats")
      -- the game loads the model (the mock's GetModelFileID would say it didn't)
      w.model.GetModelFileID = function() return 123456 end
      -- walking: it moves and turns, then rests
      local fn = w.scripts and w.scripts.OnUpdate
      if fn then
        local x0 = w.x
        for _ = 1, 400 do fn(w, 0.05) end
        ck(w.x ~= x0 or w.walking ~= nil, "it walks back and forth")
      end
      -- moods: petting brings it over to sit by your cat; a long hard tapping streak makes it run;
      -- a single tap (or a short burst) changes nothing
      if fn then
        local pet0, tap0 = T.PurrFaceLevel, T.TapFaceLevel
        T.TapFaceLevel = function() return 2 end
        for _ = 1, 10 do fn(w, 0.05) end
        ck(w.mood == "calm" and not w.running, "a few taps: calm")
        T.PurrFaceLevel = function() return 4 end
        for _ = 1, 400 do fn(w, 0.05) end
        local catEnd = w.right and 0 or (w:GetWidth() > 0 and nil)
        ck(w.mood == "pet" and not w.walking and w.anim == T.COMPANION_ANIM.sit, "being petted: it sits by your cat")
        ck(math.abs(w.x - (w.right and 0 or 124)) < 1, "right next to your cat: " .. w.x)
        T.PurrFaceLevel = function() return 0 end
        for _ = 1, 100 do fn(w, 0.05) end
        T.TapFaceLevel = function() return 9 end
        local x0 = w.x
        for _ = 1, 200 do fn(w, 0.05) end
        ck(w.mood == "curious" and not w.walking and w.anim == T.COMPANION_ANIM.sit, "tapping hard: curious, it sits and watches")
        ck(w.right and w.x <= x0 + 0.01 or w.x >= x0 - 0.01, "curious: never further from your cat")
        T.TapFaceLevel = function() return 0 end
        for _ = 1, 200 do fn(w, 0.05) end
        ck(w.mood == "calm", "and goes back to wandering")
        T.PurrFaceLevel, T.TapFaceLevel = pet0, tap0
      end
      ck(T:SetCompanionWalkShown(false) and not w:IsShown(), "turned off")
      ck(T:SetCompanionWalkShown(true) and w:IsShown(), "and on again")
      T:SetCompanion(nil)
      ck(not w:IsShown(), "no companion chosen: nothing walks")
      T:SetCompanion("orange")

      -- a model the game can't load: remembered, hidden, not sold
      T:CompanionModelMissing("spectral")
      ck(T:CompanionMissing("spectral") and T:CompanionBuyProblem("spectral"):find("game version", 1, true), "a missing model isn't sold")

      -- the window and the character panel slot
      T:ToggleCompanions()
      local f = T.companionWin
      ck(f and f:IsShown(), "the Companion Cats window opens")
      f:Refresh()
      ck(f.cells[1].comp and T:CompanionOwned(f.cells[1].comp.key), "owned companions first")
      -- Unchoose takes the companion away; Choose puts it back
      local cell
      for _, c in ipairs(f.cells) do if c.comp and c.comp == T:Companion() then cell = c end end
      if cell then
        cell.btn.scripts.OnClick(cell.btn)
        ck(T:Companion() == nil, "Unchoose clears it")
        cell.btn.scripts.OnClick(cell.btn)
        ck(T:Companion() == cell.comp, "Choose puts it back")
      else ck(false, "the chosen companion's cell") end
      -- the Buy buttons follow TapCoins while the window is open
      local cheap
      for _, c in ipairs(f.cells) do if c.comp and not T:CompanionOwned(c.comp.key) and c.comp.price > 0 then cheap = c; break end end
      if cheap then
        cheap.btn.Disable = function(b) b.disabled = true end
        cheap.btn.Enable = function(b) b.disabled = false end
        db.coins = 0; f:RefreshLight()
        ck(cheap.btn.disabled == true, "Buy greyed out without coins")
        db.coins = 5000000; f:RefreshLight()
        ck(cheap.btn.disabled == false, "and lit up once coins come in")
      end
      f.page = 99; f:Refresh()
      ck(f.page == math.ceil(#T.COMPANIONS / 8), "pages")
      T:ToggleCompanions()
      local shownBefore = f:IsShown()
      SlashCmdList.TAPCATFOREVER("companions")
      ck(not shownBefore and f:IsShown(), "/tcf companions: " .. tostring(shownBefore) .. " " .. tostring(f:IsShown()))
      T:ToggleCompanions()
      T:ToggleWindow()
      local win = T.window
      ck(win.companionButton and win.companionModel, "a companion slot on the character panel")
      win:Refresh()
      ck(win.companionModel:IsShown() and win.companionModel.comp.key == "orange", "the companion beside the cat on the panel")
      T:SetCompanion(nil); win:Refresh()
      ck(not win.companionModel:IsShown(), "empty slot: no model")
      return table.concat(fails, "; ")
    ''')
    assert r == "", "companions: " + r
    print("companion cats section (%s): all checks passed" % "50,000 to 1,000,000 TapCoins, earned by clearing dungeons, per-class choice, Companion Stroll walker on the far side from the party cats, missing models, the window and the panel slot")
