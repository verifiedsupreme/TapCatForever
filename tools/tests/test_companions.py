# 1.7.4 companion cats (Companions.lua, UI_Companions.lua): real WoW cat models bought with TapCoins or
# earned by clearing dungeons, owned by the account, chosen per class cat; the character panel slot; the
# Companion Cats window; Companion Stroll (250,000 TapCoins since 1.7.8) walks the companion beside the cat on the
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
      ck(T.COMPANION_WALK_PRICE == 250000, "Companion Stroll: 250,000 (1.7.8)")

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
      ck(T:BuyCompanion("skyrider") and db.coins == 1350000, "Skyborne Riding Cat 600,000")
      local other = (me == "MAGE") and "WARRIOR" or "MAGE"
      ck(T:CD(other).companion == nil, "another cat has none until it chooses")
      ck(T:SetCompanion("skyrider", other) and T:Companion(other).key == "skyrider" and T:Companion().key == "orange", "each cat its own companion")
      ck(not T:SetCompanion("spectral", other), "only owned companions can be chosen")
      ck(T:SetCompanion(nil) and T:Companion() == nil, "a cat can go without")
      T:SetCompanion("orange")

      -- (1.7.5) earned in Adventure only by a clear: progress made before doesn't hand it out
      local ti = T.CompanionTier(T.COMPANION_BY_KEY.bigglesworth)
      local chat0 = #_chat
      T:CD(other).adv.best = T.AdvStageCode(ti, T:AdvStages(ti))
      T:CheckCompanionUnlocks()
      ck(not T:CompanionOwned("bigglesworth"), "past progress alone gives nothing")
      -- clearing Naxxramas's last stage (a re-clear or a farm run counts too) brings Mr. Bigglesworth
      local cd = T:CD()
      cd.adv.tier, cd.adv.stage, cd.adv.auto, cd.adv.farm = ti, T:AdvStages(ti), false, nil
      T.advRun = { catHP = 10, catMax = 10, shield = 0, losses = 0 }
      T:AdvPackCleared()
      ck(T:CompanionOwned("bigglesworth"), "cleared Naxxramas: Mr. Bigglesworth")
      local told = false
      for i = chat0 + 1, #_chat do if _chat[i]:find("Mr. Bigglesworth", 1, true) then told = true end end
      ck(told, "told in chat")
      T:AdvPackCleared()
      local n = 0
      for i = chat0 + 1, #_chat do if _chat[i]:find("Mr. Bigglesworth", 1, true) then n = n + 1 end end
      ck(n == 1, "told once")
      -- an earlier stage isn't a clear
      local ti2 = T.CompanionTier(T.COMPANION_BY_KEY.alleycat)
      cd.adv.tier, cd.adv.stage = ti2, 1
      T:AdvPackCleared()
      ck(not T:CompanionOwned("alleycat") or T:AdvStages(ti2) == 1, "the first stage of the Deadmines isn't a clear")
      T.advRun = nil; cd.adv.tier, cd.adv.stage = 1, 1

      -- Companion Stroll: the walker only with the upgrade, and it can be turned off
      T:CompanionRefresh()
      local w = T.CompanionWalkerFrame()
      ck(not (w and w:IsShown()), "no walker without Companion Stroll")
      db.coins = 249999
      ck(not T:BuyCompanionWalk(), "250,000 needed")
      db.coins = 300000
      ck(T:BuyCompanionWalk() and db.coins == 50000 and T:CompanionWalkOn(), "Companion Stroll bought")
      w = T.CompanionWalkerFrame()
      ck(w and w:IsShown() and w.comp and w.comp.key == "orange", "the companion walks beside the cat")
      -- the walker is party-cat sized and on the left (the party cats' row is on the right)
      ck(w.right == false, "on the left of the cat, away from the party cats")
      -- (1.7.5) close to your cat, level with it, a little bigger, with room so nothing is cut off
      ck(T.COMPANION_SPAN <= 40, "it never walks far from your cat: " .. T.COMPANION_SPAN)
      ck(T.COMPANION_VIS > 44, "a little bigger than before")
      -- (without the 3D scene API, as in this mock) the PlayerModel fallback: room all round, the
      -- camera set again once the model has loaded, its feet level with your cat's
      local G = T.COMPANION_GEOM
      ck(w.mode == "classic" and w.model, "this mock has no ModelScene: the PlayerModel fallback (" .. tostring(w.classicWhy) .. ")")
      ck(G.modelH >= T.COMPANION_VIS * 1.5 and G.modelW >= T.COMPANION_VIS * 3.2 and w.model.camScale == T.COMPANION_ROOM,
         "the model frame has room all round, camera further back: " .. G.modelW .. "x" .. G.modelH)
      ck(math.abs(G.modelH / T.COMPANION_ROOM - T.COMPANION_VIS) < 1, "so the cat still looks its size")
      local feet = G.baseY + (G.modelH - T.COMPANION_VIS) / 2
      ck(math.abs(feet - G.feet) < 1 and G.feet > 0, "its feet are level with your cat's: " .. feet)
      ck(w.model.scripts and w.model.scripts.OnModelLoaded, "the camera is set again when the model loads")
      -- it walks beside your cat's drawing: the anchor is INSET into your cat's frame
      ck(w.edge == -G.inset, "beside your cat's drawing: " .. tostring(w.edge))
      -- (1.7.5) Settings: which side the party cats stand on; the companion takes the other
      local ui = db.ui
      ck(ui.partySide == "right", "party cats on the right by default")
      ui.partySide = "left"; T:CompanionRefresh()
      ck(w.right == true, "party cats on the left: the companion on the right")
      T.db.ui.testMode = true; T:PartyTestInject(2); T.db.ui.testMode = false
      T.PartyRefresh()
      local row = T.PartyRowFrame()
      ck(row and row:IsShown() and row.left == true, "the party cats' row goes on the left")
      T:CompanionRefresh()
      ck(w.right == true, "with the row showing, the companion is on the right")
      ui.partySide = "right"; T.PartyRefresh(); T:CompanionRefresh()
      ck(row.left == false and w.right == false, "and back: party cats right, companion left")
      T:ToggleWindow(); T.window:SelectTab(T.window.TAB_SETTINGS); T.window:Refresh()
      local sb = T.window.partySideButton
      ck(sb and sb:IsShown() and sb:GetText() == "On the right", "the Settings button: " .. tostring(sb and sb:GetText()))
      sb.scripts.OnClick(sb)
      ck(ui.partySide == "left" and sb:GetText() == "On the left" and row.left == true and w.right == true, "clicked: party cats left, companion right")
      sb.scripts.OnClick(sb)
      ck(ui.partySide == "right" and row.left == false and w.right == false, "clicked again: back to the right")
      T.window:Hide()
      -- (1.7.5) near the left screen edge with one party cat on the right: the companion moves to the
      -- right and walks just past that one cat (not past the row's whole four-cat frame)
      do
        local hud = T.hud
        local gl, gr, uw, ue, he = hud.GetLeft, hud.GetRight, UIParent.GetWidth, UIParent.GetEffectiveScale, hud.GetEffectiveScale
        hud.GetLeft = function() return 5 end; hud.GetRight = function() return 125 end
        hud.GetEffectiveScale = function() return 1 end
        UIParent.GetWidth = function() return 1200 end; UIParent.GetEffectiveScale = function() return 1 end
        T.db.ui.testMode = true; T:PartyTestInject(1); T.db.ui.testMode = false
        T.PartyRefresh(); T:CompanionRefresh()
        local G = T.COMPANION_GEOM
        ck(row.left == false and w.right == true, "no room on the left: the companion goes right, with the party cat")
        ck(w.beyond == row.usedW and row.usedW <= 50, "past the one party cat really shown: " .. tostring(w.beyond) .. " " .. tostring(row.usedW))
        ck(w.edge == row.usedW - G.miniInset, "it walks beside that cat's drawing: " .. tostring(w.edge))
        -- no room on either side: it stays opposite the party cats
        hud.GetRight = function() return 1195 end
        w.placed = false; T:CompanionRefresh()
        ck(w.right == false, "no room anywhere: back opposite the party cats")
        hud.GetLeft, hud.GetRight, UIParent.GetWidth, UIParent.GetEffectiveScale, hud.GetEffectiveScale = gl, gr, uw, ue, he
      end
      T.db.ui.testMode = true; T:PartyTestInject(0); T.db.ui.testMode = false; T.PartyRefresh(); T:CompanionRefresh()
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
        ck(w.mood == "pet" and not w.walking and w.anim == T.COMPANION_ANIM.sit, "being petted: it sits by your cat")
        ck(math.abs(w.x - (w.right and 0 or T.COMPANION_SPAN)) < 1, "right next to your cat: " .. w.x)
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

    # (1.7.6) the 3D scene fit (in the game: a ModelScene like the Adventure enemies). A mock ModelScene
    # with a level perspective camera (tools/tests/test_adv_fit.py's) and an actor whose measured box is
    # the companion's size data: every companion, at several cat sizes, is drawn VIS tall with its feet
    # level with your cat's, its whole body (any turn) well inside the scene, and its nose GAP from your
    # cat's drawing at the near end of its walk
    S = load_addon()
    r = S.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c and #fails < 12 then fails[#fails + 1] = m end end
      local FIT = T.UI.ModelFit.FIT
      local G = T.COMPANION_GEOM
      local function noop() end
      local function obj(t) return setmetatable(t, { __index = function(_, k) if type(k) == "string" and k:match("^%u") then return noop end end }) end
      local es = 1
      local scenes = {}
      local realCreate = CreateFrame
      CreateFrame = function(kind, name, parent, ...)
        if kind ~= "ModelScene" then return realCreate(kind, name, parent, ...) end
        local sc = realCreate("Frame", name, parent)
        sc.W, sc.H, sc.cam = 0, 0, { -FIT.CAM_DIST, 0, 0 }
        function sc:GetWidth() return self.W end
        function sc:GetHeight() return self.H end
        function sc:SetSize(w, h) self.W, self.H = w, h end
        function sc:GetEffectiveScale() return es end
        function sc:SetCameraPosition(x, y, z) self.cam = { x, y, z } end
        function sc:SetCameraOrientationByYawPitchRoll() end
        function sc:Project3DPointTo2D(x, y, z)
          local d = x - self.cam[1]
          if d <= 0 then return nil end
          local f = (self.H / 2) / math.tan(FIT.FOV / 2)
          return (self.W / 2 - (y - self.cam[2]) * f / d) * es, (self.H / 2 + (z - self.cam[3]) * f / d) * es, d
        end
        function sc:CreateActor()
          local a = obj({ s = 1, yaw = 0 })
          function a:SetModelByCreatureDisplayID(id) self.id = id; return true end
          function a:SetScale(v) self.s = v end
          function a:GetScale() return self.s end
          function a:SetYaw(y) self.yaw = y end
          function a:IsLoaded() return true end
          function a:SetAnimation(id) self.animNow = id end
          function a:GetActiveBoundingBox()
            -- what it's measured in: standing and unturned
            self.measuredAnim, self.measuredYaw = self.animNow, self.yaw
            local d = T.MODEL_BOUNDS[self.id]
            return -d[2] / 2, -d[3] / 2, d[4], d[2] / 2, d[3] / 2, d[4] + d[1]
          end
          sc.actor = a
          return a
        end
        scenes[#scenes + 1] = sc
        return sc
      end
      -- the drawn box of the actor in its scene (UI units from the scene's bottom-left), turned by yaw
      local function drawn(sc, a, yaw)
        local d = T.MODEL_BOUNDS[a.id]
        local c, s_ = math.cos(yaw), math.sin(yaw)
        local u1, u2, v1, v2 = math.huge, -math.huge, math.huge, -math.huge
        for _, x in ipairs({ -d[2] / 2, d[2] / 2 }) do
          for _, y in ipairs({ -d[3] / 2, d[3] / 2 }) do
            for _, z in ipairs({ d[4], d[4] + d[1] }) do
              local rx, ry = x * c - y * s_, x * s_ + y * c
              local u, v = sc:Project3DPointTo2D(rx * a.s, ry * a.s, z * a.s)
              u, v = u / es, v / es
              u1, u2, v1, v2 = math.min(u1, u), math.max(u2, u), math.min(v1, v), math.max(v2, v)
            end
          end
        end
        return u1, u2, v1, v2
      end
      local db = T.db
      db.coins = 1e9
      T:BuyCompanionWalk()
      local n, worst = 0, 0
      for _, scale in ipairs({ 0.5, 1, 2, 3 }) do
        es = scale
        for _, c in ipairs(T.COMPANIONS) do
          T:CompanionState().owned[c.key] = 1
          T:SetCompanion(c.key)
          local w = T.CompanionWalkerFrame()
          ck(w and w.mode == "scene", "the 3D scene is used: " .. tostring(w and w.classicWhy))
          for _ = 1, 30 do if w.fit then w.scripts.OnUpdate(w, 0.05) end end
          ck(not w.fit and w:IsShown(), c.key .. ": fitted")
          ck(w.actor.measuredAnim == 0 and w.actor.measuredYaw == 0, c.key .. ": measured standing and unturned: "
            .. tostring(w.actor.measuredAnim) .. " " .. tostring(w.actor.measuredYaw))
          ck(w.scene.ownAlpha == nil, "it follows your cat's transparency")
          local sc, a = w.scene, w.actor
          if not w.fit and a and a.id == c.display then
            n = n + 1
            local W, H = sc.W, sc.H
            -- side-on (walking) and the turns it rests in
            for _, yaw in ipairs({ math.pi, math.pi / 2, -math.pi / 2, math.pi * 0.8 }) do
              local u1, u2, v1, v2 = drawn(sc, a, yaw)
              local tall = v2 - v1
              -- feet on the middle row, as tall as VIS (a very long cat a little smaller)
              ck(math.abs(v1 - H / 2) < 1, string.format("%s x%.1f: feet on the ground line (%.1f, %.1f)", c.key, scale, v1, H / 2))
              ck(tall <= T.COMPANION_VIS + 1 and tall >= T.COMPANION_VIS * 0.55, string.format("%s x%.1f: %.0f px tall", c.key, scale, tall))
              -- the whole body (and room for a hop and a stretch) well inside the scene
              local room = math.min(u1, W - u2, H - v2)
              worst = math.max(worst, 1 - room / (W / 2))
              ck(room >= T.COMPANION_VIS * 0.8, string.format("%s x%.1f: room to the scene's edge %.0f", c.key, scale, room))
              ck(u2 - u1 <= G.maxLen + 2 or yaw ~= math.pi / 2, string.format("%s: %.0f px long side-on", c.key, u2 - u1))
            end
            -- at the near end of its walk, side-on, its nose is GAP from your cat's drawing: the scene's
            -- centre is GAP + halfLen + 0 out from the edge, and half its side-on length is halfLen
            local u1, u2 = drawn(sc, a, math.pi / 2)
            ck(math.abs((u2 - u1) / 2 - w.halfLen) < 2, string.format("%s: half its length %.1f vs %.1f", c.key, (u2 - u1) / 2, w.halfLen))
          end
        end
      end
      -- (1.7.6) the previews: every companion in a Companion Cats window cell and in the panel slot,
      -- its whole body inside its box at every point of its sway, never turned away
      es = 1
      T:ToggleCompanions()
      local f = T.companionWin
      local P = T.COMPANION_PREVIEW
      local np = 0
      local function checkPreview(pv, tag)
        for _ = 1, 30 do if pv.fit or not pv.cal then pv.scripts.OnUpdate(pv, 0.05) end end
        ck(pv.mode == "scene" and not pv.fit and pv.cal, tag .. ": fitted in its box")
        if pv.fit or not pv.cal then return end
        local sc, a = pv.scene, pv.actor
        local side = pv.cal.side
        for _, sw in ipairs({ -P.sway, 0, P.sway }) do
          local yaw = math.pi - (P.turn + sw) * side
          local u1, u2, v1, v2 = drawn(sc, a, yaw)
          ck(u1 >= 0 and u2 <= sc.W and v1 >= 0 and v2 <= sc.H, string.format("%s: inside its %dx%d box (%.0f..%.0f x %.0f..%.0f)",
            tag, sc.W, sc.H, u1, u2, v1, v2))
          -- big enough to see: in the middle of its sway it fills most of the box one way or the other
          if sw == 0 then ck((u2 - u1) >= sc.W * 0.6 or (v2 - v1) >= sc.H * 0.6, tag .. ": fills its box") end
          -- three-quarters toward you: never turned more than a quarter turn from the front
          ck(math.abs(P.turn + sw) < math.pi / 2 - 0.3, tag .. ": faces you")
        end
        np = np + 1
      end
      for page = 1, math.ceil(#T.COMPANIONS / 8) do
        f.page = page; f:Refresh()
        for _, cell in ipairs(f.cells) do
          if cell:IsShown() and cell.comp then checkPreview(cell.model, "window " .. cell.comp.key) end
        end
      end
      T:ToggleCompanions()
      T:ToggleWindow()
      local win = T.window
      for _, c in ipairs(T.COMPANIONS) do
        T:SetCompanion(c.key); win:Refresh()
        local pv = win.companionModel
        if pv:IsShown() then checkPreview(pv, "panel " .. c.key) else ck(false, "panel " .. c.key .. " shown") end
      end
      _out = string.format("%d fits, %d previews", n, np)
      return table.concat(fails, "; ")
    ''')
    assert r == "", "companions (3D fit): " + r
    fits = S.eval("_out")

    # (1.7.5) every companion is a cat in WoW: Forever's own game data, no two the same look
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    looks = {}
    for line in open(os.path.join(here, "..", "forever_cat_displays.txt")):
        if line.startswith("#") or not line.strip(): continue
        p = line.rstrip("\n").split("\t")
        looks[int(p[0])] = (p[1], p[2] if len(p) > 2 else "")
    n = int(lua.eval("#TapCatForever.COMPANIONS"))
    used = {}
    for i in range(1, n + 1):
        key = lua.eval("TapCatForever.COMPANIONS[%d].key" % i)
        d = int(lua.eval("TapCatForever.COMPANIONS[%d].display" % i))
        assert d in looks, "companions: %s's display %d isn't in WoW: Forever" % (key, d)
        look = looks[d] if looks[d][1] else (looks[d][0] + str(d),)
        assert look not in used, "companions: %s looks the same as %s (%s)" % (key, used.get(look), look)
        used[look] = key

    # (1.7.5) an old save: the dungeon companions 1.7.4 handed out for past progress go back, ones this
    # game can't show are refunded; bought ones stay
    import sys
    sys.path.insert(0, here)
    import savehelp, test_deathroll as TD
    L = load_addon(login=False)
    L.execute(TD.CLIENT)
    L.execute('_charName = "Compcat"')
    L.execute('TapCatForeverDB = { companions = { owned = { orange = 1, alleycat = 1, felsaber = 1, pudge = 1 }, walk = true }, '
              'cats = { classData = { WARRIOR = { companion = "alleycat" }, MAGE = { companion = "felsaber" }, ROGUE = { companion = "orange" } } } }')
    L.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    r = L.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      local coins0 = T.db.coins
      ck(T:CompanionOwned("orange") and T:CompanionWalkOwned(), "a bought companion and Stroll stay")
      ck(not T:CompanionOwned("alleycat"), "the Alley Cat from past progress goes back")
      ck(not T:CompanionOwned("felsaber") and not T:CompanionOwned("pudge"), "ones this game can't show are gone")
      ck(T:CompanionState().v175, "done once")
      local cdata = T.db.classData
      ck(cdata.WARRIOR.companion == nil and cdata.MAGE.companion == nil, "choices of cats that went away are cleared: "
        .. tostring(cdata.WARRIOR.companion) .. " " .. tostring(cdata.MAGE.companion))
      ck(cdata.ROGUE.companion == "orange", "a bought one stays chosen")
      -- a cat that had chosen a cat that went away: none chosen (choosing one still works)
      local cd = T:CD()
      cd.companion = "alleycat"
      ck(T:Companion() == nil, "a removed choice shows nothing")
      ck(T:SetCompanion("orange") and T:Companion().key == "orange", "and it can choose again")
      return table.concat(fails, "; ")
    ''')
    assert r == "", "companions (old save): " + r
    coins = L.eval("TapCatForever.db.coins")
    assert coins >= 750000 + 80000, "companions (old save): refunded %s" % coins

    # (1.7.6) a 1.7.5 save (its migration already done) that bought the Flamecat: refunded once, the
    # Molten Firecat (earned) stays, and the Flamecat isn't sold any more
    L = load_addon(login=False)
    L.execute(TD.CLIENT)
    L.execute('_charName = "Flamecat"')
    L.execute('TapCatForeverDB = { coins = 100, companions = { v175 = true, owned = { flamecat = 1, firecat = 1, orange = 1 } }, '
              'cats = { classData = { WARRIOR = { companion = "flamecat" } } } }')
    L.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    r = L.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      ck(T.COMPANION_BY_KEY.flamecat == nil, "the Flamecat isn't in the list")
      ck(not T:CompanionOwned("flamecat") and T:CompanionOwned("firecat") and T:CompanionOwned("orange"), "Flamecat gone, the Molten Firecat and the rest stay")
      local c1 = T.db.coins
      ck(c1 >= 650100 and c1 < 651100, "650,000 back: " .. tostring(c1))
      ck(T.db.classData.WARRIOR.companion == nil, "a cat that had chosen it goes without")
      T:CompanionState(); T:CompanionState()
      ck(T.db.coins == c1, "refunded only once: " .. tostring(T.db.coins))
      local fire = 0
      for _, c in ipairs(T.COMPANIONS) do if c.name:lower():find("fire", 1, true) or c.name:lower():find("flame", 1, true) then fire = fire + 1 end end
      ck(fire == 1, "one fire cat, from Molten Core: " .. fire)
      return table.concat(fails, "; ")
    ''')
    assert r == "", "companions (1.7.5 save): " + r
    print("companion cats section (%s; 3D fit: %s): all checks passed" % ("50,000 to 1,000,000 TapCoins, earned by clearing dungeons, per-class choice, Companion Stroll walker on the far side from the party cats, missing models, the window and the panel slot", fits))
