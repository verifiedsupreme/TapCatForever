-- TapCatForever: Professions page. Five professions, each with its own screen:
-- Mining (veins + pickaxe), Herbalism (garden), First Aid (bandages), Fishing
-- (bobber), Cooking (pot + recipe book), plus shared Crafting and Renown views.
local ADDON, TCF = ...
local floor, max, min = math.floor, math.max, math.min

local function Bar(parent, w, h, r, g, b)
  local bar = CreateFrame("StatusBar", nil, parent)
  bar:SetSize(w, h); bar:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar"); bar:SetStatusBarColor(r, g, b)
  local bg = bar:CreateTexture(nil, "BACKGROUND"); bg:SetAllPoints(); bg:SetColorTexture(0, 0, 0, 0.6)
  bar.text = TCF.UI.Text(bar, "GameFontHighlightSmall"); bar.text:SetPoint("CENTER")
  return bar
end

local function IconButton(parent, size)
  local b = CreateFrame("Button", nil, parent)
  b:SetSize(size, size)
  b.tex = b:CreateTexture(nil, "ARTWORK"); b.tex:SetAllPoints()
  b.count = TCF.UI.Text(b, "NumberFontNormal", nil, "RIGHT"); b.count:SetPoint("BOTTOMRIGHT", 2, -2)
  b.sel = b:CreateTexture(nil, "OVERLAY"); b.sel:SetPoint("TOPLEFT", -4, 4); b.sel:SetPoint("BOTTOMRIGHT", 4, -4)
  b.sel:SetTexture("Interface\\Buttons\\CheckButtonHilight"); b.sel:SetBlendMode("ADD"); b.sel:Hide()
  b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  return b
end

local function UpgradeButton(parent, w, getUp, buy, owned)
  local U = TCF.UI
  local b = U.Button(parent, "", w, 22, function() buy() end)
  U.Tip(b, function(tt)
    local u = getUp()
    tt:AddLine(u.name, 1, 0.82, 0); tt:AddLine(u.desc, 1, 1, 1, true)
    tt:AddLine("Cost: " .. TCF.GoldStr(u.cost), 1, 1, 1)
  end)
  function b:Update()
    local u = getUp()
    if owned() then self:SetText("|cff20ff20" .. u.name .. "|r"); self:SetEnabled(false)
    else self:SetText(u.name .. "  " .. TCF.GoldStr(u.cost, 10)); self:SetEnabled(TCF:ProfState().gold >= u.cost) end
  end
  return b
end

TCF.UI.Builders.professions = function(page, win)
  local U = TCF.UI
  local Text, Button, Tip, Panel = U.Text, U.Button, U.Tip, U.Panel
  win.profSel = win.profSel or "mining"
  win.profView = win.profView or "main"

  ------------------------------------------------ header
  local ptabs = {}
  for i, p in ipairs(TCF.PROFESSIONS) do
    local b = IconButton(page, 30)
    b:SetPoint("TOPLEFT", 12 + (i - 1) * 36, -10)
    b.tex:SetTexture(TCF.Icon(p.icon))
    b:SetScript("OnClick", function() win.profSel = p.key; win.profView = "main"; TCF:PlaySound("click"); win:Refresh() end)
    Tip(b, function(tt)
      tt:AddLine(p.name, 1, 0.82, 0)
      if p.renown > 0 then tt:AddLine(TCF:ProfUnlocked(p.key) and "Learned" or ("Unlocks at " .. p.renown .. " Renown"), 1, 1, 1) end
    end)
    b.prof = p
    ptabs[i] = b
  end
  local profName = Text(page, "GameFontNormalLarge", nil, "LEFT"); profName:SetPoint("TOPLEFT", 200, -10)
  local skillBar = Bar(page, 140, 12, 0.2, 0.5, 0.95); skillBar:SetPoint("TOPLEFT", 200, -30)
  local goldText = Text(page, "GameFontHighlightLarge", nil, "RIGHT"); goldText:SetPoint("TOPRIGHT", -14, -10)
  local renownText = Text(page, "GameFontHighlightSmall", nil, "RIGHT"); renownText:SetPoint("TOPRIGHT", -14, -30)

  local VIEW_NAMES = { main = "", upg = "Upgrades", craft = "Crafting", renown = "Renown" }
  local vbtns = {}
  for i, key in ipairs({ "main", "upg", "craft", "renown" }) do
    local b = Button(page, VIEW_NAMES[key], 92, 22, function() win.profView = key; win:Refresh() end)
    b:SetPoint("TOPLEFT", 12 + (i - 1) * 95, -48)
    b.key = key
    vbtns[i] = b
  end
  local buyMode = Button(page, "Buy x1", 76, 22, function()
    local s = TCF:ProfState()
    local modes = { 1, 10, 100, "max" }
    local idx = 1
    for k, m in ipairs(modes) do if m == s.buy then idx = k end end
    s.buy = modes[idx % #modes + 1]
    win:Refresh()
  end)
  buyMode:SetPoint("TOPRIGHT", -14, -48)

  local function View() local f = CreateFrame("Frame", nil, page); f:SetPoint("TOPLEFT", 0, -76); f:SetPoint("BOTTOMRIGHT"); f:Hide(); return f end
  local views = {}

  ------------------------------------------------ locked
  local locked = View()
  local lockText = Text(locked, "GameFontNormalLarge"); lockText:SetPoint("CENTER", 0, 40); lockText:SetWidth(480)

  ------------------------------------------------ Mining: veins
  local mineView = View()
  local rows = {}
  for i = 1, 6 do
    local r = Panel(mineView, 532, 62, 0.85); r:SetPoint("TOP", 0, -(i - 1) * 66)
    r.btn = IconButton(r, 46); r.btn:SetPoint("LEFT", 6, 0)
    r.btn:SetScript("OnClick", function() TCF:RunOp("mining", i); TCF:PlaySound("click") end)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("TOPLEFT", r.btn, "TOPRIGHT", 8, 0)
    r.mats = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.mats:SetPoint("LEFT", r.name, "RIGHT", 8, 0)
    r.bar = Bar(r, 290, 16, 0.25, 0.75, 0.3); r.bar:SetPoint("LEFT", r.btn, "RIGHT", 8, -2)
    r.bar:EnableMouse(true); r.bar:SetScript("OnMouseUp", function() TCF:RunOp("mining", i) end)
    r.info = Text(r, "GameFontDisableSmall", nil, "LEFT"); r.info:SetPoint("BOTTOMLEFT", r.btn, "BOTTOMRIGHT", 8, 0)
    -- your pickaxe: click to mine by hand
    r.pick = IconButton(r, 40); r.pick:SetPoint("RIGHT", -124, 0); r.pick.tex:SetTexture(TCF.Icon("INV_Pick_02"))
    -- a little "+gold +ore" popup rises from the pickaxe on every click
    r.pop = Text(r, "GameFontNormal"); r.pop:SetPoint("BOTTOM", r.pick, "TOP", 0, 0); r.pop:Hide()
    r.pick:SetScript("OnUpdate", function(b, e)
      if not r.popT then return end
      r.popT = r.popT - e
      if r.popT <= 0 then r.popT = nil; r.pop:Hide(); b.tex:SetSize(40, 40); return end
      local t = 1 - r.popT / 0.9
      r.pop:ClearAllPoints(); r.pop:SetPoint("BOTTOM", b, "TOP", 0, t * 22); r.pop:SetAlpha(t < 0.6 and 1 or (1 - t) / 0.4)
      local bump = t < 0.15 and 46 or 40
      b.tex:ClearAllPoints(); b.tex:SetPoint("CENTER"); b.tex:SetSize(bump, bump)
    end)
    r.pick.cd = CreateFrame("Cooldown", nil, r.pick, "CooldownFrameTemplate"); r.pick.cd:SetAllPoints()
    r.pick:SetScript("OnClick", function()
      if TCF:MineClick(i) then
        -- one pickaxe: every vein's button shows the same cooldown
        for _, row in ipairs(rows) do if row.pick.cd.SetCooldown then row.pick.cd:SetCooldown(GetTime(), TCF:PickCooldown()) end end
        r.pop:SetText(string.format("|cffffd100+%s|r  |cffcccccc+%d %s|r", TCF.GoldStr(TCF.lastMineGold or 0, 10), TCF:PickOre(), TCF.MINING_OPS[i][3]))
        r.pop:Show(); r.popT = 0.9
        TCF:PlaySound("click")
      end
    end)
    Tip(r.pick, function(tt)
      tt:AddLine(TCF:PickName(), 1, 0.82, 0)
      tt:AddLine(string.format("Click to mine %s by hand: %s and %d ore each click.", TCF.MINING_OPS[i][1],
        TCF.GoldStr(TCF.PROF_OPS[i].rev * TCF:PickMult() * TCF:UpgradeMult("mining", i)), TCF:PickOre()), 1, 1, 1, true)
      tt:AddLine(string.format("One swing every %.2fs.", TCF:PickCooldown()), 0.7, 0.7, 0.7)
      tt:AddLine("Upgrade your pickaxe with the button below the veins.", 0.7, 0.7, 0.7, true)
    end)
    r.buy = Button(r, "Buy", 112, 22, function() TCF:BuyOp("mining", i, TCF:ProfState().buy); win:Refresh() end)
    r.buy:SetPoint("TOPRIGHT", -6, -6)
    r.mgr = Button(r, "Foreman", 112, 20, function() TCF:HireForeman("mining", i); win:Refresh() end)
    r.mgr:SetPoint("BOTTOMRIGHT", -6, 6)
    Tip(r.mgr, function(tt) tt:AddLine("Hire a foreman", 1, 0.82, 0); tt:AddLine("Runs this vein automatically, forever, even offline (up to 24 hours).", 1, 1, 1, true) end)
    rows[i] = r
  end
  -- one pickaxe for every vein, upgraded forever
  local pickBtn = Button(mineView, "", 300, 24, function() TCF:UpgradePick(); win:Refresh() end)
  pickBtn:SetPoint("TOP", 0, -6 * 66 - 4)
  Tip(pickBtn, function(tt)
    tt:AddLine("Upgrade your pickaxe", 1, 0.82, 0)
    tt:AddLine(string.format("%s -> Lv %d: +15%% gold per hand-mined click on every vein.", TCF:PickName(), TCF:PickLevel() + 1), 1, 1, 1, true)
    tt:AddLine(string.format("Every 15 levels also mines one more ore per click. Swing cooldown: %.2fs (shortens a little each level).", TCF:PickCooldown()), 0.7, 0.7, 0.7, true)
  end)
  local function refreshPick()
    local cost = TCF:PickCost()
    pickBtn:SetText(string.format("%s  |  Upgrade %s", TCF:PickName(), TCF.GoldStr(cost, 10)))
    pickBtn:SetEnabled(TCF:ProfState().gold >= cost)
  end

  local function refreshMining()
    refreshPick()
    local s = TCF:ProfState()
    for i, r in ipairs(rows) do
      local o, st = TCF.MINING_OPS[i], s.ops.mining[i]
      r.btn.tex:SetTexture(TCF.Icon(o[4])); r.btn.tex:SetDesaturated(st.n == 0)
      r.btn.count:SetText(st.n > 0 and st.n or "")
      r.name:SetText(o[1])
      r.mats:SetText("|cffaaaaaa" .. TCF.FormatBig(s.mats[o[2]] or 0) .. " " .. o[3] .. "|r")
      local ct = TCF:OpCycleTime("mining", i)
      r.bar:SetMinMaxValues(0, 1)
      if st.n > 0 then
        r.bar:SetValue(st.mgr and (ct < 0.3 and 1 or st.p) or (st.run and st.p or 0))
        r.bar.text:SetText(TCF.GoldStr(TCF:OpRevenue("mining", i), 10) .. " / " .. (ct >= 1 and string.format("%.1fs", ct) or string.format("%.2fs", ct)))
      else
        r.bar:SetValue(0); r.bar.text:SetText(i == 1 and "|cffffd100Mine by hand with your pickaxe ->|r" or "|cff888888Buy one to start|r")
      end
      local nextMs
      for _, ms in ipairs(TCF.MILESTONES) do if st.n < ms then nextMs = ms; break end end
      r.info:SetText(nextMs and string.format("Next speed boost at %d", nextMs) or "Max speed")
      local canPick = i == 1 or st.n > 0
      r.pick:SetEnabled(canPick); r.pick.tex:SetDesaturated(not canPick)
      r.pick.count:SetText(TCF:PickLevel() > 0 and TCF:PickLevel() or "")
      local count = s.buy == "max" and max(1, TCF:OpMaxBuy("mining", i)) or s.buy
      local cost = TCF:OpCost("mining", i, count)
      r.buy:SetText("x" .. count .. "  " .. TCF.GoldStr(cost, 10)); r.buy:SetEnabled(s.gold >= cost)
      local fcost = TCF.PROF_OPS[i].foreman
      if st.mgr then r.mgr:SetText("|cff20ff20Automated|r"); r.mgr:SetEnabled(false)
      else r.mgr:SetText("Foreman " .. TCF.GoldStr(fcost, 10)); r.mgr:SetEnabled(st.n > 0 and s.gold >= fcost) end
    end
  end

  ------------------------------------------------ Mining: upgrades
  local upgView = View()
  local urows = {}
  for i = 1, 9 do
    local r = Panel(upgView, 532, 40, 0.85); r:SetPoint("TOP", 0, -(i - 1) * 43)
    r.icon = r:CreateTexture(nil, "ARTWORK"); r.icon:SetSize(30, 30); r.icon:SetPoint("LEFT", 6, 0)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("LEFT", r.icon, "RIGHT", 8, 0); r.name:SetWidth(360)
    r.buy = Button(r, "Buy", 130, 22, function() if r.u then TCF:BuyUpgrade(r.u.id); win:Refresh() end end)
    r.buy:SetPoint("RIGHT", -6, 0)
    urows[i] = r
  end
  local function refreshUpgrades()
    local s = TCF:ProfState()
    local list = {}
    for _, u in ipairs(TCF.UPGRADES.mining) do
      if not s.upgrades[u.id] then list[#list + 1] = u end
    end
    for i, r in ipairs(urows) do
      local u = list[i]; r.u = u
      if u then r:Show(); r.icon:SetTexture(TCF.Icon(u.icon)); r.name:SetText(u.name)
        r.buy:SetText(TCF.GoldStr(u.cost, 10)); r.buy:SetEnabled(s.gold >= u.cost)
      else r:Hide() end
    end
  end

  ------------------------------------------------ Herbalism: garden
  local gardenView = View()
  win.seedSel = win.seedSel or "peacebloom"
  local seedBtns = {}
  for i, sd in ipairs(TCF.SEEDS) do
    local b = IconButton(gardenView, 32); b:SetPoint("TOPLEFT", 26 + (i - 1) * 64, -4)
    b.tex:SetTexture(TCF.Icon(sd[3]))
    b.price = Text(gardenView, "GameFontHighlightSmall"); b.price:SetPoint("TOP", b, "BOTTOM", 0, -2); b.price:SetWidth(64)
    b:SetScript("OnClick", function()
      if TCF:ProfSkill("herbalism") >= sd[7] then win.seedSel = sd[1]; win.gardenMsg = nil
      else win.gardenMsg = { "|cffff5050" .. sd[2] .. " unlocks at Herbalism skill " .. sd[7] .. ". Harvest herbs to raise your skill.|r", GetTime() + 4 } end
      win:Refresh()
    end)
    Tip(b, function(tt)
      tt:AddLine(sd[2] .. " seeds", 1, 0.82, 0)
      tt:AddLine(string.format("Grows in %s. Seed: %s. Sells for %s per herb.", TCF.FormatDuration(sd[4]), TCF.GoldStr(sd[5]), TCF.GoldStr(sd[6])), 1, 1, 1, true)
      if TCF:ProfSkill("herbalism") < sd[7] then tt:AddLine("Needs Herbalism " .. sd[7], 1, 0.3, 0.3) end
    end)
    b.seed = sd
    seedBtns[i] = b
  end
  local seedHint = Text(gardenView, "GameFontHighlightSmall", nil, "LEFT")
  seedHint:SetPoint("TOPLEFT", 12, -56); seedHint:SetWidth(520)
  local plots = {}
  for i = 1, TCF.GARDEN_MAX_PLOTS do
    local p = CreateFrame("Button", nil, gardenView, U.BT)
    p:SetSize(126, 62); p:SetPoint("TOPLEFT", 12 + ((i - 1) % 4) * 131, -88 - floor((i - 1) / 4) * 66)
    if p.SetBackdrop then p:SetBackdrop(U.BACKDROP_PANEL); p:SetBackdropColor(0.20, 0.14, 0.08, 0.95) end
    p.icon = p:CreateTexture(nil, "ARTWORK"); p.icon:SetSize(28, 28); p.icon:SetPoint("TOPLEFT", 6, -6)
    p.name = Text(p, "GameFontNormalSmall", nil, "LEFT"); p.name:SetPoint("LEFT", p.icon, "RIGHT", 4, 0); p.name:SetWidth(84)
    p.bar = Bar(p, 112, 12, 0.3, 0.8, 0.3); p.bar:SetPoint("BOTTOM", 0, 8)
    p:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    p:SetScript("OnClick", function()
      local g = TCF:GardenState()
      local ok, why
      if i > g.n then
        ok = TCF:BuyPlot()
        if not ok then why = "Not enough Trade Gold for this plot (" .. TCF.GoldStr(TCF:PlotCost(i)) .. ")." end
      else ok, why = TCF:PlotClick(i, win.seedSel) end
      win.gardenMsg = (not ok and why) and { "|cffff5050" .. why .. "|r", GetTime() + 4 } or nil
      win:Refresh()
    end)
    plots[i] = p
  end
  local gUps = {}
  for i, u in ipairs(TCF.GARDEN_UPGRADES) do
    local b = UpgradeButton(gardenView, 258, function() return u end, function() TCF:BuyGardenUpgrade(u.key); win:Refresh() end,
      function() return TCF:GardenState().up[u.key] end)
    b:SetPoint("TOPLEFT", 12 + ((i - 1) % 2) * 264, -292 - floor((i - 1) / 2) * 26)
    gUps[i] = b
  end
  local gardenNote = Text(gardenView, "GameFontHighlightSmall", nil, "LEFT"); gardenNote:SetPoint("TOPLEFT", 12, -348); gardenNote:SetWidth(520)
  local function refreshGarden()
    local g, s = TCF:GardenState()
    local skill = TCF:ProfSkill("herbalism")
    for _, b in ipairs(seedBtns) do
      b.sel:SetShown(win.seedSel == b.seed[1]); b.tex:SetDesaturated(skill < b.seed[7])
      b.count:SetText((s.mats[b.seed[1]] or 0) > 0 and TCF.FormatBig(s.mats[b.seed[1]]) or "")
      b.price:SetText(skill < b.seed[7] and ("|cff888888Skill " .. b.seed[7] .. "|r")
        or ((s.gold >= b.seed[5] and "|cffffd100" or "|cffff5050") .. TCF.FormatBig(b.seed[5]) .. "|r"))
    end
    -- what clicking an empty plot will do (or why the last click didn't work)
    local sel = TCF.SEED_BY_KEY[win.seedSel]
    if win.gardenMsg and GetTime() < win.gardenMsg[2] then
      seedHint:SetText(win.gardenMsg[1])
    elseif sel then
      seedHint:SetText(string.format("Planting |cffffd100%s|r: seeds cost %s (you have %s). Grows in %s, sells for %s. Click an empty plot to plant; click growing plots to water them.",
        sel[2], TCF.GoldStr(sel[5]), TCF.GoldStr(s.gold), TCF.FormatDuration(sel[4]), TCF.GoldStr(sel[6])))
    end
    for i, p in ipairs(plots) do
      local plot = g.plots[i]
      if i > g.n then
        p.icon:SetTexture(TCF.Icon("INV_Misc_Bag_10")); p.icon:SetDesaturated(true)
        p.name:SetText(i == g.n + 1 and ("Buy plot\n" .. TCF.GoldStr(TCF:PlotCost(i), 10)) or "|cff666666Locked|r")
        p.bar:Hide()
      elseif plot and plot.seed then
        local sd = TCF.SEED_BY_KEY[plot.seed]
        p.icon:SetTexture(TCF.Icon(sd[3])); p.icon:SetDesaturated(false)
        p.bar:Show(); p.bar:SetMinMaxValues(0, sd[4]); p.bar:SetValue(plot.grown)
        local left = (sd[4] - plot.grown) / TCF:GardenSpeed()
        p.name:SetText(sd[2]); p.bar.text:SetText(left <= 0 and "|cff20ff20Harvest!|r" or TCF.FormatDuration(left))
      else
        p.icon:SetTexture(TCF.Icon("INV_Misc_Flower_02")); p.icon:SetDesaturated(true)
        p.name:SetText("|cffaaaaaaEmpty plot|r"); p.bar:Hide()
      end
    end
    for _, b in ipairs(gUps) do b:Update() end
    gardenNote:SetText(string.format("Black Lotus: |cffa335ee%d|r   (ripe Sungrass and Dreamfoil sometimes mutate into it)", s.mats.lotus or 0))
  end

  ------------------------------------------------ First Aid: bandages
  local aidView = View()
  local clothBtns = {}
  for i, c in ipairs(TCF.CLOTH) do
    local b = IconButton(aidView, 30); b:SetPoint("TOPLEFT", 12 + (i - 1) * 104, -4)
    b.tex:SetTexture(TCF.Icon(c[3]))
    local buy = Button(aidView, "Buy 10", 62, 18, function() TCF:BuyCloth(c[1], 10); win:Refresh() end)
    buy:SetPoint("LEFT", b, "RIGHT", 4, 0)
    Tip(b, function(tt) tt:AddLine(c[2], 1, 1, 1); tt:AddLine("Drops from Adventure enemies around level " .. c[5] .. "+, or buy 10 for " .. TCF.GoldStr(c[4] * 10), 0.8, 0.8, 0.8, true) end)
    b.cloth = c; b.buyBtn = buy
    clothBtns[i] = b
  end
  local queueBar = Bar(aidView, 520, 16, 0.85, 0.2, 0.2); queueBar:SetPoint("TOPLEFT", 12, -42)
  local brows = {}
  for i, bd in ipairs(TCF.BANDAGES) do
    local r = CreateFrame("Frame", nil, aidView); r:SetSize(532, 24); r:SetPoint("TOPLEFT", 6, -64 - (i - 1) * 25)
    r.icon = r:CreateTexture(nil, "ARTWORK"); r.icon:SetSize(22, 22); r.icon:SetPoint("LEFT", 4, 0); r.icon:SetTexture(TCF.Icon(bd[3]))
    r.name = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.name:SetPoint("LEFT", r.icon, "RIGHT", 6, 0); r.name:SetWidth(270)
    r.stock = Text(r, "GameFontNormalSmall", nil, "RIGHT"); r.stock:SetPoint("RIGHT", -150, 0)
    r.m5 = Button(r, "Make 5", 66, 20, function() TCF:QueueBandages(bd[1], 5); win:Refresh() end); r.m5:SetPoint("RIGHT", -76, 0)
    r.m20 = Button(r, "Make 20", 68, 20, function() TCF:QueueBandages(bd[1], 20); win:Refresh() end); r.m20:SetPoint("RIGHT", -4, 0)
    r.bd = bd
    brows[i] = r
  end
  local aUps = {}
  for i, u in ipairs(TCF.AID_UPGRADES) do
    local b = UpgradeButton(aidView, 172, function() return u end, function() TCF:BuyAidUpgrade(u.key); win:Refresh() end,
      function() return TCF:AidState().up[u.key] end)
    b:SetPoint("TOPLEFT", 12 + (i - 1) * 176, -320)
    aUps[i] = b
  end
  local aidNote = Text(aidView, "GameFontDisableSmall", "In Adventure your cat uses its best bandage when its health drops below 40% (every 20 seconds).", "LEFT")
  aidNote:SetPoint("TOPLEFT", 12, -350); aidNote:SetWidth(520)
  local function refreshAid()
    local a, s = TCF:AidState()
    local skill = TCF:ProfSkill("firstaid")
    for _, b in ipairs(clothBtns) do
      b.count:SetText(TCF.FormatBig(s.mats[b.cloth[1]] or 0)); b.buyBtn:SetEnabled(s.gold >= b.cloth[4] * 10)
    end
    if a.queue and a.queue.left > 0 then
      local bd = TCF.BANDAGE_BY_KEY[a.queue.key]
      queueBar:SetMinMaxValues(0, 1); queueBar:SetValue(a.queue.p)
      queueBar.text:SetText("Making " .. bd[2] .. (a.queue.auto and " (field medic)" or ("  -  " .. a.queue.left .. " left")))
    else
      queueBar:SetValue(0); queueBar.text:SetText("|cffaaaaaaNothing being made. Pick a bandage below.|r")
    end
    for _, r in ipairs(brows) do
      local bd = r.bd
      local can = skill >= bd[7]
      r.icon:SetDesaturated(not can)
      r.name:SetText(string.format("%s%s|r  |cff999999heals %d%%, %d %s%s|r", can and "|cffffffff" or "|cff777777", bd[2], bd[8] * 100, bd[5],
        TCF.MAT_BY_KEY[bd[4]].name, can and "" or (", skill " .. bd[7])))
      r.stock:SetText((s.mats[bd[1]] or 0) > 0 and ("x" .. (s.mats[bd[1]] or 0)) or "")
      r.m5:SetEnabled(can); r.m20:SetEnabled(can)
    end
    for _, b in ipairs(aUps) do b:Update() end
  end

  ------------------------------------------------ Fishing: bobber
  local fishView = View()
  local pond = Panel(fishView, 528, 180, 1); pond:SetPoint("TOP", 0, -4)
  local water = pond:CreateTexture(nil, "BACKGROUND", nil, 1); water:SetPoint("TOPLEFT", 4, -4); water:SetPoint("BOTTOMRIGHT", -4, 4)
  water:SetTexture(TCF.ART_PATH .. "bg_fishing", nil, nil, "NEAREST")
  local bobber = pond:CreateTexture(nil, "ARTWORK"); bobber:SetSize(48, 48)
  bobber:SetTexture(TCF.ART_PATH .. "ui_bobber", nil, nil, "NEAREST")
  local splash = Text(pond, "GameFontNormalHuge"); splash:SetPoint("TOP", 0, -20)
  local castBtn = Button(fishView, "Cast", 150, 30, function() TCF:FishCast() end); castBtn:SetPoint("TOPLEFT", 40, -192)
  local reelBtn = Button(fishView, "Reel in!", 150, 30, function() TCF:FishReel() end); reelBtn:SetPoint("LEFT", castBtn, "RIGHT", 20, 0)
  local resultText = Text(fishView, "GameFontHighlight", nil, "LEFT"); resultText:SetPoint("LEFT", reelBtn, "RIGHT", 16, 0); resultText:SetWidth(170)
  local spotBtns = {}
  for i, sp in ipairs(TCF.FISHING_SPOTS) do
    local b = Button(fishView, sp.name, 102, 22, function() TCF:SetFishingSpot(i); win:Refresh() end)
    b:SetPoint("TOPLEFT", 12 + (i - 1) * 105, -230)
    Tip(b, function(tt)
      tt:AddLine(sp.name, 1, 0.82, 0)
      local names = {}
      for _, k in ipairs(sp.fish) do names[#names + 1] = TCF.MAT_BY_KEY[k].name end
      tt:AddLine(table.concat(names, ", "), 1, 1, 1, true)
      if TCF:ProfSkill("fishing") < sp.skill then tt:AddLine("Needs Fishing " .. sp.skill, 1, 0.3, 0.3) end
    end)
    b.spot = sp
    spotBtns[i] = b
  end
  local catchBtns = {}
  local CATCH_KEYS = { "smallfish", "longjaw", "bristle", "blackmouth", "trout", "rockscale", "nightfin", "sunscale", "eel", "whitescale", "pinchy", "boot" }
  for i, k in ipairs(CATCH_KEYS) do
    local b = IconButton(fishView, 30); b:SetPoint("TOPLEFT", 12 + (i - 1) * 43, -262)
    b.tex:SetTexture(TCF.Icon(TCF.MAT_BY_KEY[k].icon)); b.key = k
    b:SetScript("OnClick", function() TCF:SellMat(k, 10); win:Refresh() end)
    Tip(b, function(tt) tt:AddLine(TCF.MAT_BY_KEY[k].name, 1, 1, 1); tt:AddLine("Click: sell 10 for " .. TCF.GoldStr(TCF.MAT_BY_KEY[k].value * 10), 0, 1, 0) end)
    catchBtns[i] = b
  end
  local buddyBtn = Button(fishView, "Fishing Buddy", 300, 24, function() TCF:BuyBuddy(); win:Refresh() end); buddyBtn:SetPoint("TOPLEFT", 12, -306)
  Tip(buddyBtn, function(tt) tt:AddLine("Fishing buddy", 1, 0.82, 0); tt:AddLine("Catches fish at your chosen spot all by himself, even offline. Each upgrade makes him faster.", 1, 1, 1, true) end)
  local buddyText = Text(fishView, "GameFontHighlightSmall", nil, "LEFT"); buddyText:SetPoint("LEFT", buddyBtn, "RIGHT", 10, 0); buddyText:SetWidth(210)
  local fishT = 0
  fishView:SetScript("OnUpdate", function(_, e)
    fishT = fishT + e
    local run = TCF.fishRun
    local st = run and run.state
    local bob = 0
    if st == "waiting" then bob = math.sin(fishT * 3) * 2
    elseif st == "bite" then bob = -6 + math.sin(fishT * 30) * 5 end
    bobber:ClearAllPoints(); bobber:SetPoint("CENTER", pond, "CENTER", 90, -40 + bob)
    bobber:SetShown(st == "waiting" or st == "bite")
    splash:SetText(st == "bite" and "|cffffffffSPLASH!|r" or "")
    reelBtn:SetEnabled(st == "waiting" or st == "bite")
    castBtn:SetEnabled(st ~= "waiting" and st ~= "bite")
    if st == "result" then
      local col = run.kind == "miss" and "|cffff6060" or run.kind == "pinchy" and "|cffa335ee" or run.kind == "treasure" and "|cff20ff20" or "|cffffffff"
      resultText:SetText(col .. (run.result or "") .. "|r")
    elseif st == "waiting" then resultText:SetText("|cffaaaaaaWait for the splash...|r")
    elseif st == "bite" then resultText:SetText("|cffffd100Click Reel in!|r")
    else resultText:SetText("") end
  end)
  local function refreshFishing()
    local f, s = TCF:FishState()
    local skill = TCF:ProfSkill("fishing")
    for i, b in ipairs(spotBtns) do
      b:SetEnabled(skill >= b.spot.skill)
      if i == f.spot then b:LockHighlight() else b:UnlockHighlight() end
    end
    for _, b in ipairs(catchBtns) do b.count:SetText((s.mats[b.key] or 0) > 0 and TCF.FormatBig(s.mats[b.key]) or "") end
    local nextLvl = TCF.BUDDY_LEVELS[f.buddy + 1]
    if nextLvl then
      buddyBtn:SetText((f.buddy == 0 and "Hire " or "Upgrade to ") .. nextLvl.name .. "  " .. TCF.GoldStr(nextLvl.cost, 10))
      buddyBtn:SetEnabled(s.gold >= nextLvl.cost)
    else buddyBtn:SetText("|cff20ff20" .. TCF.BUDDY_LEVELS[f.buddy].name .. "|r"); buddyBtn:SetEnabled(false) end
    buddyText:SetText(f.buddy > 0 and string.format("%s catches a fish every %ds.", TCF.BUDDY_LEVELS[f.buddy].name, TCF.BUDDY_LEVELS[f.buddy].every) or "No buddy yet.")
  end

  ------------------------------------------------ Cooking: pot and recipe book
  local cookView = View()
  local ING = { "smallfish", "longjaw", "rockscale", "nightfin", "eel", "whitescale", "pinchy",
    "wolfmeat", "boarmeat", "raptor", "egg", "mystery", "peacebloom", "mageroyal", "kingsblood", "sungrass", "dreamfoil", "lotus",
    "mildspice", "hotspice" }
  local ingBtns = {}
  for i, k in ipairs(ING) do
    local b = IconButton(cookView, 28); b:SetPoint("TOPLEFT", 12 + ((i - 1) % 10) * 32, -4 - floor((i - 1) / 10) * 32)
    b.tex:SetTexture(TCF.Icon(TCF.MAT_BY_KEY[k].icon)); b.key = k
    b:SetScript("OnClick", function() TCF:PotAdd(k); win:Refresh() end)
    Tip(b, function(tt) tt:AddLine(TCF.MAT_BY_KEY[k].name, 1, 1, 1); tt:AddLine("Click to put it in the pot.", 0, 1, 0) end)
    ingBtns[i] = b
  end
  local spiceBtns = {}
  for i, sp in ipairs(TCF.SPICES) do
    local b = Button(cookView, "", 190, 20, function() TCF:BuySpice(sp[1], 10); win:Refresh() end)
    b:SetPoint("TOPLEFT", 340, -4 - (i - 1) * 24)
    b.sp = sp
    Tip(b, function(tt)
      local s = TCF:ProfState()
      tt:AddLine(sp[2], 1, 0.82, 0)
      tt:AddLine(string.format("Buy 10 for %s. You have %d.", TCF.GoldStr(sp[4] * 10), s.mats[sp[1]] or 0), 1, 1, 1)
      tt:AddLine("A cooking ingredient: put it in the pot with meat, fish or herbs to discover spiced dishes. "
        .. (i == 1 and "Mild Spices go into simpler dishes." or "Hot Spices go into fiery, high-level dishes."), 0.8, 0.8, 0.8, true)
      local c = TCF:CookState()
      local uses = {}
      for _, r in ipairs(TCF.COOK_RECIPES) do
        for _, ing in ipairs(r[4]) do if ing == sp[1] and c.known[r[1]] then uses[#uses + 1] = r[2]; break end end
      end
      tt:AddLine(#uses > 0 and ("Used in: " .. table.concat(uses, ", ")) or "Experiment in the pot to find out what uses it!", 0.5, 1, 0.5, true)
    end)
    spiceBtns[i] = b
  end
  local potSlots = {}
  for i = 1, 3 do
    local b = IconButton(cookView, 34); b:SetPoint("TOPLEFT", 12 + (i - 1) * 40, -72)
    if b.tex then b.tex:SetTexture(TCF.Icon("INV_Misc_Food_15")) end
    potSlots[i] = b
  end
  local cookBtn = Button(cookView, "Cook!", 80, 26, function()
    local text = TCF:CookPot(); win.cookResult = text; win:Refresh()
  end)
  cookBtn:SetPoint("TOPLEFT", 140, -76)
  local clearBtn = Button(cookView, "Empty pot", 80, 26, function() TCF:PotClear(); win:Refresh() end); clearBtn:SetPoint("LEFT", cookBtn, "RIGHT", 6, 0)
  local cookResult = Text(cookView, "GameFontHighlight", nil, "LEFT"); cookResult:SetPoint("LEFT", clearBtn, "RIGHT", 10, 0); cookResult:SetWidth(220)
  local buffText = Text(cookView, "GameFontNormalSmall", nil, "LEFT"); buffText:SetPoint("TOPLEFT", 12, -112); buffText:SetWidth(520)
  local crows = {}
  for i, r in ipairs(TCF.COOK_RECIPES) do
    local row = CreateFrame("Frame", nil, cookView); row:SetSize(532, 20); row:SetPoint("TOPLEFT", 6, -128 - (i - 1) * 21)
    row.icon = row:CreateTexture(nil, "ARTWORK"); row.icon:SetSize(18, 18); row.icon:SetPoint("LEFT", 4, 0)
    row.name = Text(row, "GameFontHighlightSmall", nil, "LEFT"); row.name:SetPoint("LEFT", row.icon, "RIGHT", 6, 0); row.name:SetWidth(300)
    row.count = Text(row, "GameFontNormalSmall", nil, "RIGHT"); row.count:SetPoint("RIGHT", -184, 0)
    row.eat = Button(row, "Eat", 44, 18, function() TCF:EatDish(r[1]); win:Refresh() end); row.eat:SetPoint("RIGHT", -132, 0)
    row.cook = Button(row, "Cook", 52, 18, function() TCF:CookKnown(r[1]); win:Refresh() end); row.cook:SetPoint("RIGHT", -74, 0)
    row.chef = Button(row, "Chef", 64, 18, function() TCF:CookState().chefRecipe = r[1]; win:Refresh() end); row.chef:SetPoint("RIGHT", -4, 0)
    Tip(row.chef, function(tt) tt:AddLine("Sous-chef recipe", 1, 0.82, 0); tt:AddLine("Your sous-chef keeps cooking this one (needs the Sous-Chef upgrade).", 1, 1, 1, true) end)
    row.r = r
    crows[i] = row
  end
  local cUps = {}
  for i, u in ipairs(TCF.COOK_UPGRADES) do
    local b = UpgradeButton(cookView, 258, function() return u end, function() TCF:BuyCookUpgrade(u.key); win:Refresh() end,
      function() return TCF:CookState().up[u.key] end)
    b:SetPoint("TOPLEFT", 12 + (i - 1) * 264, -384)
    cUps[i] = b
  end
  local function refreshCooking()
    local c, s = TCF:CookState()
    local skill = TCF:ProfSkill("cooking")
    local inPot = {}
    for _, k in ipairs(c.pot) do inPot[k] = (inPot[k] or 0) + 1 end
    for _, b in ipairs(ingBtns) do
      local have = (s.mats[b.key] or 0) - (inPot[b.key] or 0)
      b.count:SetText(have > 0 and TCF.FormatBig(have) or ""); b.tex:SetDesaturated(have <= 0)
    end
    for _, b in ipairs(spiceBtns) do
      local cost = b.sp[4] * 10
      b:SetText(string.format("Buy 10 %s  %s%s|r", b.sp[2], s.gold >= cost and "|cffffd100" or "|cffff5050", TCF.FormatBig(cost)))
      b:SetEnabled(s.gold >= cost)
    end
    for i, b in ipairs(potSlots) do
      local k = c.pot[i]
      b.tex:SetTexture(TCF.Icon(k and TCF.MAT_BY_KEY[k].icon or "INV_Misc_Food_15")); b.tex:SetDesaturated(not k); b.tex:SetAlpha(k and 1 or 0.3)
    end
    cookBtn:SetEnabled(#c.pot > 0)
    cookResult:SetText(win.cookResult or "|cffaaaaaaPut up to 3 ingredients in the pot and cook.|r")
    local b = c.buff
    if b and b["until"] > time() then
      buffText:SetText(string.format("|cff20ff20Well Fed:|r %s (+%d%% %s, %s left)", TCF.COOK_BY_KEY[b.key][2], b.value * 100, TCF.BUFF_TEXT[b.kind], TCF.FormatDuration(b["until"] - time())))
    else buffText:SetText("|cffaaaaaaNot Well Fed. Eat a dish for a buff (one at a time).|r") end
    for _, row in ipairs(crows) do
      local r = row.r
      local known = c.known[r[1]]
      row.icon:SetTexture(TCF.Icon(known and r[3] or "INV_Misc_QuestionMark")); row.icon:SetDesaturated(not known)
      if known then
        row.name:SetText(string.format("|cffffffff%s|r  |cff999999+%d%% %s, %dm|r", r[2], r[7] * 100, TCF.BUFF_TEXT[r[6]], r[8]))
      else
        row.name:SetText(string.format("|cff888888??? (%d ingredients, skill %d): %s|r", #r[4], r[5], r[9]))
      end
      row.count:SetText((s.mats[r[1]] or 0) > 0 and ("x" .. s.mats[r[1]]) or "")
      row.eat:SetEnabled((s.mats[r[1]] or 0) > 0)
      row.cook:SetEnabled(known and skill >= r[5])
      row.chef:SetEnabled(known and true or false)
      row.chef:SetText(c.chefRecipe == r[1] and "|cff20ff20Chef|r" or "Chef")
    end
    for _, b2 in ipairs(cUps) do b2:Update() end
  end

  ------------------------------------------------ crafting (all professions)
  local craftView = View()
  local crafts = {}
  for i = 1, 5 do
    local r = Panel(craftView, 532, 62, 0.85); r:SetPoint("TOP", 0, -(i - 1) * 66)
    r.cell = U.ItemCell(r, 50); r.cell:SetPoint("LEFT", 6, 0)
    r.cell:SetScript("OnEnter", function(s)
      if not s.item then return end
      GameTooltip:SetOwner(s, "ANCHOR_RIGHT"); TCF:ItemTooltip(GameTooltip, s.item); GameTooltip:Show()
      win.preview:ApplyAppearance(TCF:GetAppearance(nil, s.item))
    end)
    r.cell:SetScript("OnLeave", function() GameTooltip:Hide(); win.preview:ApplyAppearance(TCF:GetAppearance()) end)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("TOPLEFT", r.cell, "TOPRIGHT", 8, -4)
    r.need = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.need:SetPoint("BOTTOMLEFT", r.cell, "BOTTOMRIGHT", 8, 4); r.need:SetWidth(360)
    r.craft = Button(r, "Craft", 80, 22, function() if r.recipe then TCF:Craft(r.recipe) end end); r.craft:SetPoint("RIGHT", -8, 0)
    crafts[i] = r
  end
  local function refreshCraft(prof)
    local s = TCF:ProfState()
    local list = TCF.RECIPES[prof] or {}
    for i, r in ipairs(crafts) do
      local rec = list[i]
      r.recipe = rec
      if rec then
        r:Show()
        local it = TCF.ITEMS[rec.item]
        r.cell:SetItem(it, true, false)
        r.name:SetText("|c" .. TCF.RARITY[it.rarity].hex .. it.name .. "|r" .. (TCF.db.owned[it.id] and "  |cff20ff20(owned)|r" or ""))
        local parts = {}
        for mk, need in pairs(rec.mats) do
          local have = s.mats[mk] or 0
          parts[#parts + 1] = string.format("%s%s/%s|r %s", have >= need and "|cff20ff20" or "|cffff5050", TCF.FormatBig(min(have, need)), TCF.FormatBig(need), TCF.MAT_BY_KEY[mk] and TCF.MAT_BY_KEY[mk].name or mk)
        end
        r.need:SetText(table.concat(parts, ",  "))
        r.craft:SetEnabled(TCF:CanCraft(rec))
      else r:Hide() end
    end
  end

  ------------------------------------------------ renown
  local renView = View()
  local renInfo = Text(renView, "GameFontHighlight", nil, "LEFT"); renInfo:SetPoint("TOPLEFT", 16, -10); renInfo:SetWidth(520); renInfo:SetSpacing(4)
  local renBtn = Button(renView, "Sell the business", 180, 26, function()
    if IsShiftKeyDown() then TCF:PrestigeTrade() else TCF:Print("Shift-click to sell everything you bought with Trade Gold for Renown.") end
  end)
  renBtn:SetPoint("TOPLEFT", 16, -250)
  local function refreshRenown()
    local s = TCF:ProfState()
    local gain = TCF:RenownOnReset()
    local unlocks = {}
    for _, p in ipairs(TCF.PROFESSIONS) do
      if p.renown > 0 then unlocks[#unlocks + 1] = string.format("%s%s at %d Renown|r", TCF:ProfUnlocked(p.key) and "|cff20ff20" or "|cffaaaaaa", p.name, p.renown) end
    end
    renInfo:SetText(string.format(
      "|cffffd100Renown|r is permanent: each point adds +2%% to all Trade Gold, and Renown unlocks new professions.\n\n" ..
      "Current Renown: |cffffffff%d|r (highest ever %d)\nTrade Gold earned in total: |cffffffff%s|r\nRenown you'd gain by selling now: |cff20ff20%d|r  (+%d TapCoins)\n\n" ..
      "Unlocks: %s\n\nSelling resets Trade Gold, mine veins, pickaxes, garden plots, foremen, helpers and upgrades. " ..
      "You keep skills, recipes, materials, bandages, dishes and unlocked professions.",
      s.renown, s.renownEver, TCF.GoldStr(s.lifetime, 12), gain, min(1000, gain * 3), table.concat(unlocks, ", ")))
    renBtn:SetEnabled(gain >= 5)
  end

  ------------------------------------------------ refresh
  local MAIN = { mining = { mineView, refreshMining, "Veins" }, herbalism = { gardenView, refreshGarden, "Garden" },
    firstaid = { aidView, refreshAid, "Bandages" }, fishing = { fishView, refreshFishing, "Fishing" },
    cooking = { cookView, refreshCooking, "Kitchen" } }
  local allViews = { locked, mineView, upgView, gardenView, aidView, fishView, cookView, craftView, renView }

  local refresh
  local acc = 0
  page:SetScript("OnUpdate", function(_, e)
    acc = acc + e
    if acc > 0.15 and refresh then acc = 0; refresh() end
  end)

  refresh = function()
    local s = TCF:ProfState()
    local prof = win.profSel
    local p = TCF.PROF_BY_KEY[prof]
    for _, b in ipairs(ptabs) do b.sel:SetShown(b.prof.key == prof); b.tex:SetDesaturated(not TCF:ProfUnlocked(b.prof.key)) end
    profName:SetText(p.name)
    local skill = TCF:ProfSkill(prof)
    skillBar:SetMinMaxValues(0, 300); skillBar:SetValue(skill); skillBar.text:SetText("Skill " .. skill .. " / 300")
    goldText:SetText(TCF.GoldStr(s.gold, 16))
    renownText:SetText(string.format("Renown %d (+%d%% gold)", s.renown, s.renown * 2))
    buyMode:SetText(s.buy == "max" and "Buy Max" or ("Buy x" .. s.buy))
    buyMode:SetShown(prof == "mining" and win.profView == "main")
    vbtns[1]:SetText(MAIN[prof][3])
    vbtns[2]:SetShown(prof == "mining")
    if win.profView == "upg" and prof ~= "mining" then win.profView = "main" end
    for _, b in ipairs(vbtns) do if b.key == win.profView then b:LockHighlight() else b:UnlockHighlight() end end
    -- show only the current view; never hide a visible view mid-refresh, or clicks get lost
    local function only(view) for _, v in ipairs(allViews) do v:SetShown(v == view) end end
    if not TCF:ProfUnlocked(prof) and win.profView ~= "renown" then
      only(locked)
      lockText:SetText(string.format("%s unlocks at |cffffd100%d Renown|r (you have %d).\n\nEarn Renown by selling your business in the Renown view.", p.name, p.renown, s.renownEver))
      return
    end
    if win.profView == "main" then only(MAIN[prof][1]); MAIN[prof][2]()
    elseif win.profView == "upg" then only(upgView); refreshUpgrades()
    elseif win.profView == "craft" then only(craftView); refreshCraft(prof)
    else only(renView); refreshRenown() end
  end
  return refresh
end
