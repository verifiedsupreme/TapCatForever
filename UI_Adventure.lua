-- TapCatForever: Adventure page (idle fights with 3D creature models over the zone's artwork)
local ADDON, TCF = ...
local floor, max, min, random = math.floor, math.max, math.min, math.random

local ANIM_STAND, ANIM_DEATH, ANIM_ATTACK, ANIM_WOUND = 0, 1, 16, 9
-- if a creature model can't load, borrow another enemy's model from the zone;
-- as a last resort show a pixel-art monster (never an icon)
local PIXEL_MONSTER = "Interface\\AddOns\\TapCatForever\\Art\\mob_shadow"

local function short(n)
  n = floor(n + 0.5)
  if n >= 1e6 then return string.format("%.1fM", n / 1e6) end
  if n >= 1e4 then return string.format("%.1fK", n / 1e3) end
  return tostring(n)
end

TCF.UI.Builders.adventure = function(page, win)
  local U = TCF.UI
  local Text, Button, Tip, Panel = U.Text, U.Button, U.Tip, U.Panel

  local zoneText = Text(page, "GameFontNormalLarge", nil, "LEFT"); zoneText:SetPoint("TOPLEFT", 16, -12)
  local zoneSub = Text(page, "GameFontHighlightSmall", nil, "LEFT"); zoneSub:SetPoint("TOPLEFT", 16, -32)
  local prevTier = Button(page, "<", 26, 22, function()
    local adv = TCF:CD().adv
    for t = adv.tier - 1, 1, -1 do if TCF:AdvGoTo(t, 1) then break end end
    win:Refresh()
  end)
  local nextTier = Button(page, ">", 26, 22, function()
    local adv = TCF:CD().adv
    TCF:AdvGoTo(adv.tier + 1, 1); win:Refresh()
  end)
  nextTier:SetPoint("TOPRIGHT", -12, -12); prevTier:SetPoint("RIGHT", nextTier, "LEFT", -4, 0)
  local tierLabel = Text(page, "GameFontDisableSmall", "Zone", "RIGHT"); tierLabel:SetPoint("RIGHT", prevTier, "LEFT", -6, 0)
  Tip(nextTier, function(tt) tt:AddLine("Next zone", 1, 0.82, 0); tt:AddLine("Unlocks when you've beaten every stage of this zone (including its final boss) and your cat is at least the next zone's level. With Auto-advance on, your cat moves on by itself.", 1, 1, 1, true) end)

  -- scene
  local scene = Panel(page, 532, 250, 1); scene:SetPoint("TOP", 0, -50)
  scene:SetClipsChildren(true)
  local fallbackSky = scene:CreateTexture(nil, "BACKGROUND", nil, 0); fallbackSky:SetPoint("TOPLEFT", 4, -4); fallbackSky:SetPoint("BOTTOMRIGHT", -4, 4)
  fallbackSky:SetColorTexture(0.16, 0.14, 0.22, 1)
  local art = scene:CreateTexture(nil, "BACKGROUND", nil, 1); art:SetPoint("TOPLEFT", 4, -4); art:SetPoint("BOTTOMRIGHT", -4, 4)
  local shade = scene:CreateTexture(nil, "BACKGROUND", nil, 2); shade:SetPoint("BOTTOMLEFT", 4, 4); shade:SetPoint("BOTTOMRIGHT", -4, 4)
  shade:SetHeight(70); shade:SetColorTexture(0, 0, 0, 0.15)

  local catHolder = CreateFrame("Frame", nil, scene)
  catHolder:SetSize(130, 130); catHolder:SetPoint("BOTTOMLEFT", 30, 10)
  local advCat = TCF.CreateCat(catHolder, 130, { preview = true })
  advCat.frame:SetPoint("CENTER")
  local function Bar(parent, w, r, g, b)
    local bar = CreateFrame("StatusBar", nil, parent)
    bar:SetSize(w, 10); bar:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar"); bar:SetStatusBarColor(r, g, b)
    local bg = bar:CreateTexture(nil, "BACKGROUND"); bg:SetAllPoints(); bg:SetColorTexture(0, 0, 0, 0.7)
    bar.text = Text(bar, "GameFontHighlightSmall"); bar.text:SetPoint("CENTER", 0, 0)
    return bar
  end
  local catBar = Bar(scene, 120, 0.2, 0.85, 0.25); catBar:SetPoint("BOTTOM", catHolder, "TOP", 0, 2)
  local abilityText = Text(scene, "GameFontNormal"); abilityText:SetPoint("BOTTOM", catBar, "TOP", 0, 4)
  local abilityT = 0

  -- up to 3 enemies: a 3D model each, with an icon fallback
  local slots = {}
  for i = 1, 3 do
    local f = CreateFrame("Frame", nil, scene)
    f:SetSize(110, 140)
    local m = CreateFrame("PlayerModel", nil, f)
    m:SetAllPoints()
    f.model = m
    f.icon = f:CreateTexture(nil, "ARTWORK"); f.icon:SetSize(96, 96); f.icon:SetPoint("BOTTOM", 0, 10)
    f.icon:SetTexture(PIXEL_MONSTER, nil, nil, "NEAREST")
    f.bar = Bar(f, 96, 0.85, 0.15, 0.15); f.bar:SetPoint("TOP", 0, 8)
    f.name = Text(f, "GameFontNormalSmall"); f.name:SetPoint("BOTTOM", f.bar, "TOP", 0, 2); f.name:SetWidth(130)
    f.shake, f.fade, f.anim = 0, 0, 0
    f:Hide()
    slots[i] = f
  end

  local floats = {}
  local function FloatText(txt, x, y, r, g, b, big)
    local fs
    for _, f in ipairs(floats) do if not f.active then fs = f; break end end
    if not fs then
      fs = scene:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge"); fs:SetShadowOffset(1, -1)
      floats[#floats + 1] = fs
    end
    fs:SetFontObject(big and "GameFontNormalHuge" or "GameFontNormalLarge")
    fs:SetText(txt); fs:SetTextColor(r, g, b); fs:Show()
    fs.active, fs.age, fs.x, fs.y = true, 0, x + random(-12, 12), y
  end

  local awayText = Text(scene, "GameFontNormalLarge"); awayText:SetPoint("CENTER", 60, 30); awayText:SetWidth(300)
  local startPanel = CreateFrame("Frame", nil, scene); startPanel:SetAllPoints()
  local startDim = startPanel:CreateTexture(nil, "OVERLAY", nil, -1); startDim:SetAllPoints(); startDim:SetColorTexture(0, 0, 0, 0.45)
  local startText = Text(startPanel, "GameFontHighlightLarge"); startText:SetPoint("CENTER", 0, 26); startText:SetWidth(420)
  local startBtn = Button(startPanel, "Start Adventure", 170, 30, function() TCF:AdvStart(); win:Refresh() end)
  startBtn:SetPoint("TOP", startText, "BOTTOM", 0, -12)

  local stats = Text(page, "GameFontHighlight", nil, "LEFT"); stats:SetPoint("TOPLEFT", 18, -342); stats:SetWidth(520)
  local autoCB = CreateFrame("CheckButton", nil, page, "UICheckButtonTemplate")
  autoCB:SetSize(24, 24); autoCB:SetPoint("TOPLEFT", 14, -360)
  local autoText = Text(page, "GameFontHighlightSmall", "Auto-advance"); autoText:SetPoint("LEFT", autoCB, "RIGHT", 0, 1)
  autoCB:SetScript("OnClick", function(s) TCF:CD().adv.auto = s:GetChecked() and true or false end)
  Tip(autoCB, function(tt)
    tt:AddLine("Auto-advance", 1, 0.82, 0)
    tt:AddLine("On: move on after each win and into the next zone when your level allows. Off: keep farming this stage.", 1, 1, 1, true)
  end)
  local retreat = Button(page, "Retreat", 76, 22, function() TCF:AdvRetreat(); win:Refresh() end)
  retreat:SetPoint("TOPLEFT", 130, -361)
  Tip(retreat, function(tt) tt:AddLine("Retreat", 1, 0.82, 0); tt:AddLine("Stop fighting. Your cat rests until you press Start again.", 1, 1, 1, true) end)
  local nextStage = Button(page, "Stage >", 76, 22, function() TCF:AdvStep(1); win:Refresh() end)
  nextStage:SetPoint("TOPRIGHT", -14, -361)
  local prevStage = Button(page, "< Stage", 76, 22, function() TCF:AdvStep(-1); win:Refresh() end)
  prevStage:SetPoint("RIGHT", nextStage, "LEFT", -6, 0)
  local logText = Text(page, "GameFontHighlightSmall", nil, "LEFT"); logText:SetPoint("TOPLEFT", 18, -390)
  logText:SetWidth(524); logText:SetSpacing(3); logText:SetJustifyV("TOP")
  local help = Text(page, "GameFontDisableSmall", nil, "LEFT"); help:SetPoint("BOTTOMLEFT", 16, 10); help:SetWidth(524)
  help:SetText("Your cat fights with this class's gear, level and learned abilities. Every key you press lands a bonus paw strike. Bosses and zone clears drop chests that can hold the zone's real loot.")

  ------------------------------------------------ ability bar (under the fight) and spell effects
  local SPELL = TCF.SPELL_FX
  local abar, abtns = CreateFrame("Frame", nil, page), {}
  abar:SetSize(532, 32); abar:SetPoint("TOP", scene, "BOTTOM", 0, -2)
  local function abilityButton(i)
    local b = CreateFrame("Frame", nil, abar); b:SetSize(30, 30)
    b.icon = b:CreateTexture(nil, "ARTWORK"); b.icon:SetAllPoints(); b.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
    -- cooldown: a dark cover that shrinks as the ability comes back, plus seconds left
    b.cover = b:CreateTexture(nil, "OVERLAY", nil, 1); b.cover:SetPoint("BOTTOMLEFT"); b.cover:SetPoint("BOTTOMRIGHT"); b.cover:SetColorTexture(0, 0, 0, 0.7)
    b.cd = Text(b, "NumberFontNormal"); b.cd:SetPoint("CENTER", 0, 0)
    b.flash = b:CreateTexture(nil, "OVERLAY", nil, 2); b.flash:SetAllPoints(); b.flash:SetTexture("Interface\Buttons\ButtonHilight-Square"); b.flash:SetBlendMode("ADD"); b.flash:SetAlpha(0)
    b:EnableMouse(true)
    b:SetScript("OnEnter", function(s)
      if not s.a then return end
      GameTooltip:SetOwner(s, "ANCHOR_TOP"); GameTooltip:AddLine(s.a.name, 1, 0.82, 0)
      GameTooltip:AddLine(s.a.desc, 1, 1, 1, true)
      if s.a.cd > 0 then GameTooltip:AddLine(string.format("Cooldown: %ds", s.a.cd), 0.7, 0.7, 0.7) end
      GameTooltip:AddLine("Your cat casts it on its own during fights.", 0.6, 0.8, 1, true)
      GameTooltip:Show()
    end)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    abtns[i] = b
    return b
  end
  local function layoutAbilities()
    local class = TCF.db.class
    local list = {}
    for _, a in ipairs(TCF.ABILITIES[class] or {}) do
      if TCF:AbilityKnown(class, a.key) and a.kind ~= "passive" and a.kind ~= "ward" then list[#list + 1] = a end
    end
    for i, b in ipairs(abtns) do b:Hide(); b.a = nil end
    local w = #list * 34 - 4
    for i, a in ipairs(list) do
      local b = abtns[i] or abilityButton(i)
      b.a = a; b.icon:SetTexture(TCF.Icon(a.icon))
      b:ClearAllPoints(); b:SetPoint("LEFT", abar, "CENTER", -w / 2 + (i - 1) * 34, 0)
      b:Show()
    end
    abar.class, abar.count = class, #list
  end
  local function updateAbilities()
    local run = TCF.advRun
    for _, b in ipairs(abtns) do
      if b:IsShown() and b.a then
        local left = run and run.cds and run.cds[b.a.key] and (run.cds[b.a.key] - run.t) or 0
        if left > 0 and b.a.cd > 0 then
          b.cover:SetHeight(max(1, 30 * min(1, left / b.a.cd))); b.cover:Show()
          b.cd:SetText(left >= 10 and floor(left) or string.format("%.1f", left))
          b.icon:SetDesaturated(true)
        else
          b.cover:Hide(); b.cd:SetText(""); b.icon:SetDesaturated(false)
        end
        if (b.flashA or 0) > 0 then b.flashA = max(0, b.flashA - 0.06); b.flash:SetAlpha(b.flashA) end
      end
    end
  end

  -- spell effects play above the models
  local fxLayer = CreateFrame("Frame", nil, scene); fxLayer:SetAllPoints(scene)
  if fxLayer.SetFrameLevel then fxLayer:SetFrameLevel((scene:GetFrameLevel() or 1) + 20) end
  local fxPool = {}
  local function fxSprite()
    for _, f in ipairs(fxPool) do if not f.on then return f end end
    if #fxPool >= 40 then return nil end
    local f = { tex = fxLayer:CreateTexture(nil, "OVERLAY") }
    fxPool[#fxPool + 1] = f
    return f
  end
  -- mode: proj (fly a to b), burst (pop at a), rise (float up at a), fall (drop onto a)
  local function playFx(sprite, mode, ax, ay, bx, by, size, dur, tint)
    local f = fxSprite(); if not f then return end
    f.on, f.age, f.mode, f.dur = true, 0, mode, dur or 0.45
    f.ax, f.ay, f.bx, f.by, f.size = ax, ay, bx or ax, by or ay, size or 40
    f.tex:SetTexture(TCF.ART_PATH .. "v\\s_" .. sprite)
    if tint then f.tex:SetVertexColor(tint[1], tint[2], tint[3]) else f.tex:SetVertexColor(1, 1, 1) end
    f.tex:SetRotation(0)
    if mode == "proj" and bx then f.tex:SetRotation(math.atan2(-(by - ay), bx - ax)) end
    f.impact = (mode == "proj" or mode == "fall") and sprite
    f.tint = tint
    f.tex:Show()
  end
  local function updateFx(e)
    for _, f in ipairs(fxPool) do
      if f.on then
        f.age = f.age + e
        local t = f.age / f.dur
        if t >= 1 then
          f.on = false; f.tex:Hide()
          if f.impact then playFx("impact", "burst", f.bx, f.by, nil, nil, 46, 0.3, SPELL.TINT[f.impact]) end
        else
          local x, y, sz, a = f.ax, f.ay, f.size, 1
          if f.mode == "proj" then x = f.ax + (f.bx - f.ax) * t; y = f.ay + (f.by - f.ay) * t + math.sin(t * math.pi) * 18
          elseif f.mode == "fall" then x = f.bx - 30 * (1 - t); y = f.by + 130 * (1 - t)
          elseif f.mode == "burst" then sz = f.size * (0.5 + t); a = 1 - t
          elseif f.mode == "rise" then y = f.ay + 40 * t; sz = f.size * (0.8 + 0.4 * t); a = t < 0.6 and 1 or (1 - t) / 0.4
          elseif f.mode == "bubble" then sz = f.size * (0.9 + 0.1 * math.sin(t * 12)); a = t < 0.7 and 0.9 or (1 - t) / 0.3 * 0.9 end
          f.tex:ClearAllPoints(); f.tex:SetSize(sz, sz); f.tex:SetPoint("CENTER", scene, "BOTTOMLEFT", x, y); f.tex:SetAlpha(a)
        end
      end
    end
  end
  local CAT_X, CAT_Y = 120, 90
  local function castFx(info, slotPos)
    local fx = SPELL.For(info.class, info.key, info.kind)
    if not fx then return end
    local sprite, mode = fx[1], fx[2]
    local targets = {}
    if mode == "each" or mode == "multi" or mode == "rain" then
      for i = 1, 3 do local x, y = slotPos(i); if x then targets[#targets + 1] = { x, y } end end
    else
      local x, y = slotPos(info.target); if x then targets[1] = { x, y } end
    end
    if mode == "proj" or mode == "multi" then
      for k, p in ipairs(targets) do playFx(sprite, "proj", CAT_X, CAT_Y, p[1], p[2], 40, 0.35 + k * 0.05) end
    elseif mode == "drain" then
      if targets[1] then playFx(sprite, "proj", targets[1][1], targets[1][2], CAT_X, CAT_Y, 36, 0.45) end
    elseif mode == "hit" or mode == "each" then
      for _, p in ipairs(targets) do playFx(sprite, "burst", p[1], p[2], nil, nil, 60, 0.4) end
    elseif mode == "rain" then
      for _, p in ipairs(targets) do
        for k = 1, 2 do playFx(sprite, "fall", p[1], p[2], p[1] + (k - 1.5) * 24, p[2], 34, 0.4 + k * 0.08) end
      end
    elseif mode == "stun" then
      for _, p in ipairs(targets) do playFx("stun", "rise", p[1], p[2] + 46, nil, nil, 46, 1.2) end
    elseif mode == "self" then playFx(sprite, "rise", CAT_X - 20, CAT_Y, nil, nil, 50, 0.9)
    elseif mode == "bubble" then playFx(sprite, "bubble", CAT_X - 25, CAT_Y - 10, nil, nil, 120, 1.4, fx[3]) end
  end

  local function layoutSlots(pack)
    local n = pack and #pack or 0
    local boss = n == 1 and pack[1].boss
    for i, f in ipairs(slots) do
      local m = pack and pack[i]
      f:ClearAllPoints()
      if m then
        local w, h = boss and 170 or 110, boss and 200 or 140
        f:SetSize(w, h)
        f.baseX = boss and -50 or (-12 - (n - i) * 112)
        f:SetPoint("BOTTOMRIGHT", scene, "BOTTOMRIGHT", f.baseX, 8)
        f.name:SetText(m.boss and ("|cffff8000" .. m.name .. "|r") or m.name)
        f.bar:SetWidth(boss and 150 or 96)
        f.fade = 0
        f:SetAlpha(1)
        f:Show()
        -- candidate models: this enemy's own, then the zone's other enemies
        local cands = { m.display }
        local t = TCF:AdvTier(TCF:CD().adv.tier)
        for _, x in ipairs(t.mobs) do cands[#cands + 1] = x[2] end
        for _, x in ipairs(t.bosses) do cands[#cands + 1] = x[2] end
        f.cands, f.candIdx, f.isBoss = cands, 0, boss
        f.tryNext = function()
          f.candIdx = f.candIdx + 1
          local id = f.cands[f.candIdx]
          while id and id <= 0 do f.candIdx = f.candIdx + 1; id = f.cands[f.candIdx] end
          if id and f.candIdx <= 4 then
            local ok = pcall(f.model.SetDisplayInfo, f.model, id)
            pcall(f.model.SetFacing, f.model, -0.7)
            pcall(f.model.SetCamDistanceScale, f.model, f.isBoss and 1.3 or 1.15)
            pcall(f.model.SetAnimation, f.model, ANIM_STAND)
            f.model:Show(); f.icon:Hide()
            f.modelCheck = 0.6
            if not ok then f.tryNext() end
          else
            f.model:Hide(); f.icon:Show(); f.modelCheck = nil
          end
        end
        f.tryNext()
      else
        f:Hide()
      end
    end
  end

  local function refresh()
    layoutAbilities()
    local cd = TCF:CD()
    local adv = cd.adv
    local t = TCF:AdvTier(adv.tier)
    zoneText:SetText(t.name .. (t.raid and "  |cffff8000(Raid)|r" or ""))
    zoneSub:SetText(string.format("Levels %d-%d   Stage %d / %d   %s", t.min, t.max, adv.stage, TCF:AdvStages(adv.tier),
      adv.stage % 2 == 0 and ("|cffff8000Boss: " .. t.bosses[adv.stage / 2][1] .. "|r") or "|cffaaaaaaTrash pack|r"))
    if t.key then
      -- hand-drawn cartoon scene for every zone
      art:SetTexture(TCF.ART_PATH .. "v\\bg_" .. t.key); art:SetTexCoord(0, 1, 0, 1); art:Show()
    elseif type(t.art) == "string" then
      art:SetTexture("Interface\\AddOns\\TapCatForever\\Art\\" .. t.art, nil, nil, "NEAREST")
      art:SetTexCoord(0, 1, 0, 1); art:Show()
    elseif t.art and t.art > 0 then
      art:SetTexture(t.art); art:SetTexCoord(0, 0.78, 0.05, 0.62); art:Show()
    else art:Hide() end
    advCat:ApplyAppearance(TCF:GetAppearance())
    local run = TCF.advRun
    local st = TCF:CombatStats()
    local known = 0
    for _, a in ipairs(TCF.ABILITIES[TCF.db.class]) do if TCF:AbilityKnown(TCF.db.class, a.key) then known = known + 1 end end
    stats:SetText(string.format("DPS |cffffffff%s|r   Health |cffffffff%s|r   Armor |cffffffff%s|r   Crit |cffffffff%.1f%%|r   Item level |cffffffff%d|r   Abilities |cffffffff%d|r",
      short(st.dps), short(st.hp), short(st.armor), st.crit, st.ilvl, known))
    autoCB:SetChecked(adv.auto)
    local n = TCF:AdvStages(adv.tier)
    prevStage:SetEnabled(adv.stage > 1 or adv.tier > 1)
    nextStage:SetEnabled(TCF:AdvCanGoTo(adv.stage < n and adv.tier or adv.tier + 1, adv.stage < n and adv.stage + 1 or 1))
    nextTier:SetEnabled(TCF:AdvCanGoTo(adv.tier + 1, 1))
    -- say what the next zone needs
    local nt = TCF.TIERS[adv.tier + 1]
    if not nt then
      tierLabel:SetText("|cffaaaaaaLast zone|r")
    elseif TCF:AdvCanGoTo(adv.tier + 1, 1) then
      tierLabel:SetText("|cff20ff20Next: " .. nt.name .. " ready! >|r")
    else
      local cleared = adv.best >= TCF.AdvStageCode(adv.tier, TCF:AdvStages(adv.tier))
      local lvl = TCF:CD().level
      if not cleared then
        tierLabel:SetText("|cffaaaaaaNext: " .. nt.name .. " (clear this zone's final boss first)|r")
      else
        tierLabel:SetText(string.format("|cffffd100Next: %s needs level %d (you're %d)|r", nt.name, nt.min, lvl))
      end
    end
    prevTier:SetEnabled(adv.tier > 1)
    logText:SetText(table.concat(TCF.advLog or { "|cff888888Your cat sets out on an adventure...|r" }, "\n"))
    local active = adv.active
    startPanel:SetShown(not active and not TCF:IsOnExpedition(TCF.db.class))
    startText:SetText(string.format("Your %s cat is resting.\nPress Start to fight through %s.", TCF.CLASS_BY_KEY[TCF.db.class].name, t.name))
    retreat:SetEnabled(active and true or false)
    local away = TCF:IsOnExpedition(TCF.db.class)
    awayText:SetText(away and ("|cffffd100Your " .. TCF.CLASS_BY_KEY[TCF.db.class].name .. " cat is away on an expedition.|r\nPick another class, or wait for it to return.") or "")
    if run and not run.pack then layoutSlots(nil) end
  end

  local refreshT = 0
  page:SetScript("OnShow", function()
    TCF.advWatching = true
    if TCF.advRun then TCF.advRun.events = {}; layoutSlots(TCF.advRun.pack) end
  end)
  page:SetScript("OnHide", function() TCF.advWatching = false end)
  page:SetScript("OnUpdate", function(_, e)
    local run = TCF.advRun
    if not run then return end
    for _, ev in ipairs(run.events) do
      local kind, amt, idx = ev[1], ev[2], ev[3]
      local f = idx and slots[idx]
      local fx = f and f:IsShown() and (532 + f.baseX - f:GetWidth() / 2) or 400
      if kind == "spawn" then
        layoutSlots(run.pack); refresh()
      elseif kind == "hit" or kind == "crit" or kind == "dot" then
        if kind ~= "dot" then advCat:Tap() end
        if f then f.shake = 0.2 end
        if kind == "crit" then FloatText(short(amt) .. "!", fx, 150, 1, 0.82, 0.1, true)
        elseif kind == "hit" then FloatText(short(amt), fx, 140, 1, 1, 1)
        elseif amt >= 1 and random() < 0.25 then FloatText(short(amt * 4), fx, 120, 0.9, 0.8, 0.3) end
      elseif kind == "tap" then
        if f then f.shake = max(f.shake, 0.1) end
        FloatText(short(amt), fx, 115, 0.55, 0.85, 1)
      elseif kind == "hurt" then
        FloatText("-" .. short(amt), 95, 150, 1, 0.25, 0.25)
        if f then pcall(f.model.SetAnimation, f.model, ANIM_ATTACK); f.anim = 0.7 end
      elseif kind == "heal" then
        FloatText("+" .. short(amt), 95, 160, 0.3, 1, 0.3)
      elseif kind == "ability" then
        abilityText:SetText("|T" .. TCF.Icon(ev[3]) .. ":16:16|t " .. amt); abilityT = 1.2
        local info = ev[4]
        if info then
          castFx(info, function(i)
            local f = i and slots[i]
            if f and f:IsShown() and run.pack and run.pack[i] and run.pack[i].alive then return 532 + f.baseX - 55, 80 end
          end)
          for _, b in ipairs(abtns) do if b.a and b.a.key == info.key then b.flashA = 1; b.flash:SetAlpha(1) end end
        end
      elseif kind == "mobdie" then
        local d = slots[amt]
        if d then pcall(d.model.SetAnimation, d.model, ANIM_DEATH); d.fade = 1.0; d.anim = 0 end
      elseif kind == "kill" then
        refresh()
      elseif kind == "defeat" then
        advCat:SetFaceFor("blink", 2); layoutSlots(nil); refresh()
      end
    end
    if #run.events > 0 then run.events = {} end
    catBar:SetMinMaxValues(0, run.catMax); catBar:SetValue(max(0, run.catHP))
    catBar.text:SetText(short(max(0, run.catHP)) .. " / " .. short(run.catMax) .. (run.shield > 0 and (" |cff99ccff+" .. short(run.shield) .. "|r") or ""))
    for i, f in ipairs(slots) do
      local m = run.pack and run.pack[i]
      if f:IsShown() and m then
        f.bar:SetMinMaxValues(0, m.max); f.bar:SetValue(max(0, m.hp))
        f.bar.text:SetText(short(max(0, m.hp)))
        f.shake = max(0, f.shake - e)
        f:ClearAllPoints()
        f:SetPoint("BOTTOMRIGHT", scene, "BOTTOMRIGHT", f.baseX + (f.shake > 0 and random(-4, 4) or 0), 8)
        if f.fade > 0 then f.fade = max(0, f.fade - e); f:SetAlpha(min(1, f.fade * 1.5)) end
        if f.anim > 0 then f.anim = f.anim - e; if f.anim <= 0 and m.alive then pcall(f.model.SetAnimation, f.model, ANIM_STAND) end end
        if f.modelCheck then
          f.modelCheck = f.modelCheck - e
          if f.modelCheck <= 0 then
            f.modelCheck = nil
            local okFile, file = pcall(f.model.GetModelFileID, f.model)
            if okFile and not file then f.tryNext() end
          end
        end
      end
    end
    if abilityT > 0 then abilityT = abilityT - e; abilityText:SetAlpha(min(1, abilityT * 2)) end
    if abar.class ~= TCF.db.class or abar.count == nil then layoutAbilities() end
    updateAbilities(); updateFx(e)
    for _, fs in ipairs(floats) do
      if fs.active then
        fs.age = fs.age + e
        if fs.age > 1 then fs.active = false; fs:Hide()
        else
          fs:ClearAllPoints(); fs:SetPoint("CENTER", scene, "BOTTOMLEFT", fs.x, fs.y + fs.age * 40)
          fs:SetAlpha(fs.age < 0.6 and 1 or (1 - fs.age) / 0.4)
        end
      end
    end
    refreshT = refreshT + e
    if refreshT > 1 then refreshT = 0; refresh() end
  end)

  return function() refresh() end
end
