-- TapCatForever: Adventure page (idle fights with 3D creature models over the zone's artwork)
local ADDON, TCF = ...
local floor, max, min, random = math.floor, math.max, math.min, math.random

local ANIM_STAND, ANIM_DEATH, ANIM_ATTACK, ANIM_WOUND = 0, 1, 16, 9
local ICON_FALLBACK = "INV_Misc_Bone_HumanSkull_01"

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
  Tip(nextTier, function(tt) tt:AddLine("Next zone", 1, 0.82, 0); tt:AddLine("Unlocks when you clear the current zone and meet its level.", 1, 1, 1, true) end)

  -- scene
  local scene = Panel(page, 532, 250, 1); scene:SetPoint("TOP", 0, -50)
  scene:SetClipsChildren(true)
  local fallbackSky = scene:CreateTexture(nil, "BACKGROUND", nil, 0); fallbackSky:SetPoint("TOPLEFT", 4, -4); fallbackSky:SetPoint("BOTTOMRIGHT", -4, 4)
  fallbackSky:SetColorTexture(0.16, 0.14, 0.22, 1)
  local art = scene:CreateTexture(nil, "BACKGROUND", nil, 1); art:SetPoint("TOPLEFT", 4, -4); art:SetPoint("BOTTOMRIGHT", -4, 4)
  local shade = scene:CreateTexture(nil, "BACKGROUND", nil, 2); shade:SetPoint("BOTTOMLEFT", 4, 4); shade:SetPoint("BOTTOMRIGHT", -4, 4)
  shade:SetHeight(70); shade:SetColorTexture(0, 0, 0, 0.45)

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
    f.icon = f:CreateTexture(nil, "ARTWORK"); f.icon:SetSize(60, 60); f.icon:SetPoint("BOTTOM", 0, 20)
    f.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
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

  local stats = Text(page, "GameFontHighlight", nil, "LEFT"); stats:SetPoint("TOPLEFT", 18, -308); stats:SetWidth(520)
  local autoCB = CreateFrame("CheckButton", nil, page, "UICheckButtonTemplate")
  autoCB:SetSize(24, 24); autoCB:SetPoint("TOPLEFT", 14, -326)
  local autoText = Text(page, "GameFontHighlightSmall", "Auto-advance"); autoText:SetPoint("LEFT", autoCB, "RIGHT", 0, 1)
  autoCB:SetScript("OnClick", function(s) TCF:CD().adv.auto = s:GetChecked() and true or false end)
  Tip(autoCB, function(tt)
    tt:AddLine("Auto-advance", 1, 0.82, 0)
    tt:AddLine("On: move on after each win and into the next zone when your level allows. Off: keep farming this stage.", 1, 1, 1, true)
  end)
  local nextStage = Button(page, "Stage >", 76, 22, function() TCF:AdvStep(1); win:Refresh() end)
  nextStage:SetPoint("TOPRIGHT", -14, -327)
  local prevStage = Button(page, "< Stage", 76, 22, function() TCF:AdvStep(-1); win:Refresh() end)
  prevStage:SetPoint("RIGHT", nextStage, "LEFT", -6, 0)
  local logText = Text(page, "GameFontHighlightSmall", nil, "LEFT"); logText:SetPoint("TOPLEFT", 18, -356)
  logText:SetWidth(524); logText:SetSpacing(3); logText:SetJustifyV("TOP")
  local help = Text(page, "GameFontDisableSmall", nil, "LEFT"); help:SetPoint("BOTTOMLEFT", 16, 10); help:SetWidth(524)
  help:SetText("Your cat fights with this class's gear, level and learned abilities. Every key you press lands a bonus paw strike. Bosses drop their real loot.")

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
        local ok = false
        if m.display and m.display > 0 then
          ok = pcall(f.model.SetDisplayInfo, f.model, m.display)
          pcall(f.model.SetFacing, f.model, -0.7)
          pcall(f.model.SetCamDistanceScale, f.model, boss and 1.3 or 1.15)
          pcall(f.model.SetAnimation, f.model, ANIM_STAND)
        end
        f.model:SetShown(ok)
        f.icon:SetShown(not ok)
        f.icon:SetTexture(TCF.Icon(ICON_FALLBACK))
        f.modelCheck = ok and 0.6 or nil
      else
        f:Hide()
      end
    end
  end

  local function refresh()
    local cd = TCF:CD()
    local adv = cd.adv
    local t = TCF:AdvTier(adv.tier)
    zoneText:SetText(t.name .. (t.raid and "  |cffff8000(Raid)|r" or ""))
    zoneSub:SetText(string.format("Levels %d-%d   Stage %d / %d   %s", t.min, t.max, adv.stage, TCF:AdvStages(adv.tier),
      adv.stage % 2 == 0 and ("|cffff8000Boss: " .. t.bosses[adv.stage / 2][1] .. "|r") or "|cffaaaaaaTrash pack|r"))
    if t.art and t.art > 0 then
      art:SetTexture(t.art)
      if t.art == 343001 then art:SetTexCoord(0, 1, 0.12, 0.88) else art:SetTexCoord(0, 0.78, 0.05, 0.62) end
      art:Show()
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
    prevTier:SetEnabled(adv.tier > 1)
    logText:SetText(table.concat(TCF.advLog or { "|cff888888Your cat sets out on an adventure...|r" }, "\n"))
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
            if okFile and not file then f.model:Hide(); f.icon:Show() end
          end
        end
      end
    end
    if abilityT > 0 then abilityT = abilityT - e; abilityText:SetAlpha(min(1, abilityT * 2)) end
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
