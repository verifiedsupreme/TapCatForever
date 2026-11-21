-- TapCatForever: Professions page (idle tycoon: operations, foremen, upgrades, crafting, renown)
local ADDON, TCF = ...
local floor, max, min = math.floor, math.max, math.min

TCF.UI.Builders.professions = function(page, win)
  local U = TCF.UI
  local Text, Button, Tip, Panel = U.Text, U.Button, U.Tip, U.Panel
  win.profSel = win.profSel or "mining"
  win.profView = win.profView or "ops"

  -- profession tabs
  local ptabs = {}
  for i, p in ipairs(TCF.PROFESSIONS) do
    local b = CreateFrame("Button", nil, page)
    b:SetSize(30, 30); b:SetPoint("TOPLEFT", 12 + (i - 1) * 36, -10)
    b.tex = b:CreateTexture(nil, "ARTWORK"); b.tex:SetAllPoints(); b.tex:SetTexture(TCF.Icon(p.icon))
    b.sel = b:CreateTexture(nil, "OVERLAY"); b.sel:SetPoint("TOPLEFT", -4, 4); b.sel:SetPoint("BOTTOMRIGHT", 4, -4)
    b.sel:SetTexture("Interface\\Buttons\\CheckButtonHilight"); b.sel:SetBlendMode("ADD")
    b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    b:SetScript("OnClick", function() win.profSel = p.key; TCF:PlaySound("click"); win:Refresh() end)
    Tip(b, function(tt)
      tt:AddLine(p.name, 1, 0.82, 0)
      if not TCF:ProfUnlocked(p.key) then tt:AddLine("Unlock for " .. TCF.GoldStr(p.unlock), 1, 1, 1) end
    end)
    b.prof = p
    ptabs[i] = b
  end
  local profName = Text(page, "GameFontNormalLarge", nil, "LEFT"); profName:SetPoint("TOPLEFT", 162, -12)
  local goldText = Text(page, "GameFontHighlightLarge", nil, "RIGHT"); goldText:SetPoint("TOPRIGHT", -14, -10)
  local renownText = Text(page, "GameFontHighlightSmall", nil, "RIGHT"); renownText:SetPoint("TOPRIGHT", -14, -30)

  -- view buttons + buy mode
  local views = { { "ops", "Operations" }, { "upg", "Upgrades" }, { "craft", "Crafting" }, { "renown", "Renown" } }
  local vbtns = {}
  for i, v in ipairs(views) do
    local b = Button(page, v[2], 92, 22, function() win.profView = v[1]; win:Refresh() end)
    b:SetPoint("TOPLEFT", 12 + (i - 1) * 95, -46)
    b.key = v[1]
    vbtns[i] = b
  end
  local BUY_MODES = { 1, 10, 100, "max" }
  local buyMode = Button(page, "Buy x1", 76, 22, function()
    local s = TCF:ProfState()
    local idx = 1
    for k, m in ipairs(BUY_MODES) do if m == s.buy then idx = k end end
    s.buy = BUY_MODES[idx % #BUY_MODES + 1]
    win:Refresh()
  end)
  buyMode:SetPoint("TOPRIGHT", -14, -46)
  Tip(buyMode, function(tt) tt:AddLine("How many to buy per click", 1, 0.82, 0); tt:AddLine("x1, x10, x100 or Max (as many as you can afford).", 1, 1, 1) end)

  -- locked overlay
  local locked = CreateFrame("Frame", nil, page); locked:SetPoint("TOPLEFT", 0, -74); locked:SetPoint("BOTTOMRIGHT")
  local lockText = Text(locked, "GameFontNormalLarge"); lockText:SetPoint("CENTER", 0, 40); lockText:SetWidth(460)
  local unlockBtn = Button(locked, "Unlock", 160, 26, function() TCF:UnlockProfession(win.profSel) end)
  unlockBtn:SetPoint("TOP", lockText, "BOTTOM", 0, -14)

  ------------------------------------------------ operations view
  local opsView = CreateFrame("Frame", nil, page); opsView:SetPoint("TOPLEFT", 0, -74); opsView:SetPoint("BOTTOMRIGHT")
  local rows = {}
  for i = 1, 6 do
    local r = Panel(opsView, 532, 62, 0.85); r:SetPoint("TOP", 0, -(i - 1) * 66)
    r.btn = CreateFrame("Button", nil, r); r.btn:SetSize(46, 46); r.btn:SetPoint("LEFT", 6, 0)
    r.icon = r.btn:CreateTexture(nil, "ARTWORK"); r.icon:SetAllPoints()
    r.count = Text(r.btn, "NumberFontNormalLarge", nil, "RIGHT"); r.count:SetPoint("BOTTOMRIGHT", 2, -2)
    r.btn:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    r.btn:SetScript("OnClick", function() TCF:RunOp(win.profSel, i); TCF:PlaySound("click") end)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("TOPLEFT", r.btn, "TOPRIGHT", 8, 0)
    r.mats = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.mats:SetPoint("LEFT", r.name, "RIGHT", 8, 0)
    r.bar = CreateFrame("StatusBar", nil, r); r.bar:SetSize(250, 16); r.bar:SetPoint("LEFT", r.btn, "RIGHT", 8, -2)
    r.bar:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar"); r.bar:SetStatusBarColor(0.25, 0.75, 0.3)
    local bg = r.bar:CreateTexture(nil, "BACKGROUND"); bg:SetAllPoints(); bg:SetColorTexture(0, 0, 0, 0.6)
    r.barText = Text(r.bar, "GameFontHighlightSmall"); r.barText:SetPoint("CENTER")
    r.bar:EnableMouse(true)
    r.bar:SetScript("OnMouseUp", function() TCF:RunOp(win.profSel, i) end)
    r.info = Text(r, "GameFontDisableSmall", nil, "LEFT"); r.info:SetPoint("BOTTOMLEFT", r.btn, "BOTTOMRIGHT", 8, 0)
    r.buy = Button(r, "Buy", 112, 22, function()
      local s = TCF:ProfState()
      if TCF:BuyOp(win.profSel, i, s.buy) then TCF:PlaySound("buy") end
      win:Refresh()
    end)
    r.buy:SetPoint("TOPRIGHT", -6, -6)
    r.mgr = Button(r, "Foreman", 112, 20, function() TCF:HireForeman(win.profSel, i); win:Refresh() end)
    r.mgr:SetPoint("BOTTOMRIGHT", -6, 6)
    Tip(r.mgr, function(tt)
      tt:AddLine("Hire a foreman", 1, 0.82, 0)
      tt:AddLine("Runs this operation automatically, forever, even while you're offline (up to 24 hours).", 1, 1, 1, true)
    end)
    Tip(r.btn, function(tt)
      local p = TCF.PROF_BY_KEY[win.profSel]; local o = p.ops[i]
      tt:AddLine(o[1], 1, 0.82, 0)
      tt:AddLine("Click (or press any key in game) to run a cycle: earns Trade Gold and " .. o[3] .. ".", 1, 1, 1, true)
      tt:AddLine("Owning 25, 50, 100, 200... doubles its speed each time. 100 and 300 owned give extra materials.", 0.8, 0.8, 0.8, true)
      tt:AddLine("Reaching 25, 100 and 300 also gives a free chest (once).", 0.3, 1, 0.3, true)
    end)
    rows[i] = r
  end

  ------------------------------------------------ upgrades view
  local upgView = CreateFrame("Frame", nil, page); upgView:SetPoint("TOPLEFT", 0, -74); upgView:SetPoint("BOTTOMRIGHT")
  local urows = {}
  for i = 1, 9 do
    local r = Panel(upgView, 532, 40, 0.85); r:SetPoint("TOP", 0, -(i - 1) * 43)
    r.icon = r:CreateTexture(nil, "ARTWORK"); r.icon:SetSize(30, 30); r.icon:SetPoint("LEFT", 6, 0)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("LEFT", r.icon, "RIGHT", 8, 0)
    r.buy = Button(r, "Buy", 130, 22, function() if r.u then TCF:BuyUpgrade(r.u.id); win:Refresh() end end)
    r.buy:SetPoint("RIGHT", -6, 0)
    urows[i] = r
  end
  local upgNote = Text(upgView, "GameFontDisableSmall", "Showing the next upgrades you haven't bought.", "LEFT"); upgNote:SetPoint("BOTTOMLEFT", 14, 12)

  ------------------------------------------------ crafting view
  local craftView = CreateFrame("Frame", nil, page); craftView:SetPoint("TOPLEFT", 0, -74); craftView:SetPoint("BOTTOMRIGHT")
  local crows = {}
  for i = 1, 5 do
    local r = Panel(craftView, 532, 62, 0.85); r:SetPoint("TOP", 0, -(i - 1) * 66)
    r.cell = U.ItemCell(r, 50); r.cell:SetPoint("LEFT", 6, 0)
    r.cell:SetScript("OnEnter", function(s)
      if not s.item then return end
      GameTooltip:SetOwner(s, "ANCHOR_RIGHT"); TCF:ItemTooltip(GameTooltip, s.item); GameTooltip:Show()
      if TCF:CanEquip(s.item) then win.preview:ApplyAppearance(TCF:GetAppearance(nil, s.item)) end
    end)
    r.cell:SetScript("OnLeave", function() GameTooltip:Hide(); win.preview:ApplyAppearance(TCF:GetAppearance()) end)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("TOPLEFT", r.cell, "TOPRIGHT", 8, -4)
    r.need = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.need:SetPoint("BOTTOMLEFT", r.cell, "BOTTOMRIGHT", 8, 4); r.need:SetWidth(360)
    r.craft = Button(r, "Craft", 80, 22, function() if r.recipe then TCF:Craft(r.recipe) end end)
    r.craft:SetPoint("RIGHT", -8, 0)
    crows[i] = r
  end
  local craftNote = Text(craftView, "GameFontDisableSmall", "These cosmetics can only be crafted. Materials come from your operations.", "LEFT")
  craftNote:SetPoint("BOTTOMLEFT", 14, 12)

  ------------------------------------------------ renown view
  local renView = CreateFrame("Frame", nil, page); renView:SetPoint("TOPLEFT", 0, -74); renView:SetPoint("BOTTOMRIGHT")
  local renInfo = Text(renView, "GameFontHighlight", nil, "LEFT"); renInfo:SetPoint("TOPLEFT", 16, -10); renInfo:SetWidth(520); renInfo:SetSpacing(4)
  local renBtn = Button(renView, "Sell the business", 180, 26, function()
    if IsShiftKeyDown() then TCF:PrestigeTrade() else TCF:Print("Shift-click to sell your whole business for Renown.") end
  end)
  renBtn:SetPoint("TOPLEFT", 16, -150)
  Tip(renBtn, function(tt)
    tt:AddLine("Sell the business (shift-click)", 1, 0.82, 0)
    tt:AddLine("Resets Trade Gold, operations, foremen, upgrades and unlocked professions. You keep materials, crafted items and all Renown.", 1, 1, 1, true)
  end)

  local function setView(v)
    opsView:SetShown(v == "ops"); upgView:SetShown(v == "upg"); craftView:SetShown(v == "craft"); renView:SetShown(v == "renown")
    for _, b in ipairs(vbtns) do if b.key == v then b:LockHighlight() else b:UnlockHighlight() end end
  end

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
    for _, b in ipairs(ptabs) do
      b.sel:SetShown(b.prof.key == prof)
      b.tex:SetDesaturated(not TCF:ProfUnlocked(b.prof.key))
    end
    profName:SetText(p.name)
    goldText:SetText(TCF.GoldStr(s.gold, 16))
    renownText:SetText(string.format("Renown %d (+%d%% profits)", s.renown, s.renown * 2))
    buyMode:SetText(s.buy == "max" and "Buy Max" or ("Buy x" .. s.buy))
    local unlocked = TCF:ProfUnlocked(prof)
    if not unlocked and win.profView ~= "renown" then
      opsView:Hide(); upgView:Hide(); craftView:Hide(); renView:Hide()
      locked:Show()
      lockText:SetText(string.format("Your cat hasn't learned %s yet.\nUnlock it for %s Trade Gold.", p.name, TCF.GoldStr(p.unlock, 16)))
      unlockBtn:SetEnabled(s.gold >= p.unlock)
      return
    end
    locked:Hide()
    setView(win.profView)
    if win.profView == "ops" then
      for i, r in ipairs(rows) do
        local o = p.ops[i]
        local st = s.ops[prof][i]
        r.icon:SetTexture(TCF.Icon(o[4])); r.icon:SetDesaturated(st.n == 0)
        r.count:SetText(st.n > 0 and st.n or "")
        r.name:SetText(o[1])
        local have = s.mats[o[2]] or 0
        local bonus = o.bonus and ("  |cffa335ee" .. (s.mats[o.bonus[1]] or 0) .. " " .. o.bonus[2] .. "|r") or ""
        r.mats:SetText("|cffaaaaaa" .. TCF.FormatBig(have) .. " " .. o[3] .. "|r" .. bonus)
        local ct = TCF:OpCycleTime(prof, i)
        r.bar:SetMinMaxValues(0, 1)
        if st.n > 0 then
          r.bar:SetValue(st.mgr and (ct < 0.3 and 1 or st.p) or (st.run and st.p or 0))
          r.barText:SetText(TCF.GoldStr(TCF:OpRevenue(prof, i), 10) .. " / " .. (ct >= 1 and string.format("%.1fs", ct) or string.format("%.2fs", ct)))
        else
          r.bar:SetValue(0); r.barText:SetText("|cff888888Buy one to start|r")
        end
        local nextMs
        for _, ms in ipairs(TCF.MILESTONES) do if st.n < ms then nextMs = ms; break end end
        r.info:SetText(nextMs and string.format("Next speed boost at %d", nextMs) or "Max speed")
        local count = s.buy == "max" and max(1, TCF:OpMaxBuy(prof, i)) or s.buy
        local cost = TCF:OpCost(prof, i, count)
        r.buy:SetText("x" .. count .. "  " .. TCF.GoldStr(cost, 10))
        r.buy:SetEnabled(s.gold >= cost)
        local fcost = TCF.PROF_OPS[i].foreman * p.scale
        if st.mgr then r.mgr:SetText("|cff20ff20Automated|r"); r.mgr:SetEnabled(false)
        else r.mgr:SetText("Foreman " .. TCF.GoldStr(fcost, 10)); r.mgr:SetEnabled(st.n > 0 and s.gold >= fcost) end
      end
    elseif win.profView == "upg" then
      local list = {}
      for _, u in ipairs(TCF.UPGRADES[prof]) do if not s.upgrades[u.id] then list[#list + 1] = u end end
      for i, r in ipairs(urows) do
        local u = list[i]
        r.u = u
        if u then
          r:Show()
          r.icon:SetTexture(TCF.Icon(u.icon))
          r.name:SetText(u.name)
          r.buy:SetText(TCF.GoldStr(u.cost, 10)); r.buy:SetEnabled(s.gold >= u.cost)
        else r:Hide() end
      end
    elseif win.profView == "craft" then
      for i, r in ipairs(crows) do
        local rec = TCF.RECIPES[prof][i]
        r.recipe = rec
        local it = TCF.ITEMS[rec.item]
        r.cell:SetItem(it, true, false)
        r.name:SetText("|c" .. TCF.RARITY[it.rarity].hex .. it.name .. "|r" .. (TCF.db.owned[it.id] and "  |cff20ff20(owned)|r" or ""))
        local parts = {}
        for mk, need in pairs(rec.mats) do
          local have = s.mats[mk] or 0
          parts[#parts + 1] = string.format("%s%s/%s|r %s", have >= need and "|cff20ff20" or "|cffff5050", TCF.FormatBig(min(have, need)), TCF.FormatBig(need), TCF.MAT_BY_KEY[mk].name)
        end
        r.need:SetText(table.concat(parts, ",  "))
        r.craft:SetEnabled(TCF:CanCraft(rec))
      end
    else
      local gain = TCF:RenownOnReset()
      renInfo:SetText(string.format(
        "|cffffd100Renown|r is a permanent bonus: every point adds +2%% to all profession profits.\n\n" ..
        "Current Renown: |cffffffff%d|r (+%d%% profits)\nTrade Gold earned in total: |cffffffff%s|r\nRenown you'd gain by selling now: |cff20ff20%d|r  (+%d TapCoins)\n\n" ..
        "Selling resets your operations, foremen, upgrades and unlocked professions, then you rebuild much faster. Materials and crafted items are kept.",
        s.renown, s.renown * 2, TCF.GoldStr(s.lifetime, 12), gain, min(1000, gain * 3)))
      renBtn:SetEnabled(gain >= 5)
    end
  end
  return refresh
end
