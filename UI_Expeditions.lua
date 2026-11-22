-- TapCatForever: Expeditions page (send 3 cats away for real time)
local ADDON, TCF = ...
local floor, max, min = math.floor, math.max, math.min

TCF.UI.Builders.expeditions = function(page, win)
  local U = TCF.UI
  local Text, Button, Tip, Panel = U.Text, U.Button, U.Tip, U.Panel
  local title = Text(page, "GameFontNormalLarge", "Expeditions", "LEFT"); title:SetPoint("TOPLEFT", 16, -12)
  -- two views: Solo (three of your own cats, two slots) and Party (with group members, its own slot;
  -- built by TCF.UI.BuildPartyExpeditions below)
  local soloPage = CreateFrame("Frame", nil, page); soloPage:SetAllPoints()
  local root = page
  page = soloPage
  local sub = Text(page, "GameFontDisableSmall", "Send three of your class cats away. They return with TapCoins, XP and chests, even while you're offline.", "LEFT")
  sub:SetPoint("TOPLEFT", 16, -30); sub:SetWidth(530)

  -- active expeditions
  local act = {}
  for i = 1, TCF.MAX_EXPEDITIONS do
    local r = Panel(page, 528, 50, 0.9); r:SetPoint("TOP", 0, -50 - (i - 1) * 54)
    r.icon = r:CreateTexture(nil, "ARTWORK"); r.icon:SetSize(36, 36); r.icon:SetPoint("LEFT", 7, 0)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("TOPLEFT", r.icon, "TOPRIGHT", 8, -1)
    r.party = {}
    for k = 1, 3 do
      local t = r:CreateTexture(nil, "ARTWORK"); t:SetSize(18, 18); t:SetPoint("BOTTOMLEFT", r.icon, "BOTTOMRIGHT", 8 + (k - 1) * 20, 0)
      r.party[k] = t
    end
    r.bar = CreateFrame("StatusBar", nil, r); r.bar:SetSize(190, 12); r.bar:SetPoint("BOTTOMLEFT", r.icon, "BOTTOMRIGHT", 72, 2)
    r.bar:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar"); r.bar:SetStatusBarColor(0.9, 0.7, 0.2)
    local bg = r.bar:CreateTexture(nil, "BACKGROUND"); bg:SetAllPoints(); bg:SetColorTexture(0, 0, 0, 0.6)
    r.barText = Text(r.bar, "GameFontHighlightSmall"); r.barText:SetPoint("CENTER")
    r.chance = Text(r, "GameFontHighlightSmall", nil, "RIGHT"); r.chance:SetPoint("RIGHT", -96, 0)
    r.claim = Button(r, "Claim", 80, 22, function() if r.index then TCF:ClaimExpedition(r.index) end end)
    r.claim:SetPoint("RIGHT", -8, 0)
    r.empty = Text(r, "GameFontDisable", "Free expedition slot", "LEFT"); r.empty:SetPoint("LEFT", 16, 0)
    act[i] = r
  end

  -- party picker
  win.party = win.party or {}
  local pickLabel = Text(page, "GameFontNormal", "Choose 3 cats:", "LEFT"); pickLabel:SetPoint("TOPLEFT", 16, -162)
  local partyPower = Text(page, "GameFontHighlight", nil, "RIGHT"); partyPower:SetPoint("TOPRIGHT", -16, -162)
  local picks = {}
  for i, cl in ipairs(TCF.CLASSES) do
    local b = CreateFrame("Button", nil, page)
    b:SetSize(40, 40); b:SetPoint("TOPLEFT", 16 + (i - 1) * 58, -182)
    local t = b:CreateTexture(nil, "ARTWORK"); t:SetAllPoints(); TCF.SetClassIcon(t, cl.key)
    b.tex = t
    b.sel = b:CreateTexture(nil, "OVERLAY"); b.sel:SetPoint("TOPLEFT", -6, 6); b.sel:SetPoint("BOTTOMRIGHT", 6, -6)
    b.sel:SetTexture("Interface\\Buttons\\CheckButtonHilight"); b.sel:SetBlendMode("ADD")
    b.power = Text(page, "GameFontHighlightSmall"); b.power:SetPoint("TOP", b, "BOTTOM", 0, -2)
    b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    b:SetScript("OnClick", function()
      if TCF:IsOnExpedition(cl.key) then return end
      if win.party[cl.key] then win.party[cl.key] = nil
      else
        local n = 0
        for _ in pairs(win.party) do n = n + 1 end
        if n < 3 then win.party[cl.key] = true end
      end
      TCF:PlaySound("click"); win:Refresh()
    end)
    Tip(b, function(tt)
      local cs = TCF:CombatStats(cl.key)
      tt:AddLine(cl.name, cl.color[1], cl.color[2], cl.color[3])
      tt:AddLine(string.format("Level %d   Power %d", TCF:CD(cl.key).level, cs.power), 1, 1, 1)
      tt:AddLine("Power comes from gear and level.", 0.7, 0.7, 0.7)
      if TCF:IsOnExpedition(cl.key) then tt:AddLine("Away on an expedition", 1, 0.6, 0.2) end
    end)
    b.class = cl.key
    picks[i] = b
  end

  -- expedition list
  local rows = {}
  for i, e in ipairs(TCF.EXPEDITIONS) do
    local r = Panel(page, 528, 26, 0.8); r:SetPoint("TOP", 0, -240 - (i - 1) * 27)
    local ic = r:CreateTexture(nil, "ARTWORK"); ic:SetSize(20, 20); ic:SetPoint("LEFT", 4, 0); ic:SetTexture(TCF.Icon(e.icon))
    r.name = Text(r, "GameFontNormalSmall", e.name, "LEFT"); r.name:SetPoint("LEFT", ic, "RIGHT", 6, 0)
    r.info = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.info:SetPoint("LEFT", 200, 0)
    r.chance = Text(r, "GameFontHighlightSmall", nil, "RIGHT"); r.chance:SetPoint("RIGHT", -76, 0)
    r.go = Button(r, "Send", 64, 19, function()
      local members = {}
      for _, cl in ipairs(TCF.CLASSES) do if win.party[cl.key] then members[#members + 1] = cl.key end end
      local ok, why = TCF:StartExpedition(e.key, members)
      if ok then win.party = {} elseif why then TCF:Print(why, true) end
      win:Refresh()
    end)
    r.go:SetPoint("RIGHT", -6, 0)
    Tip(r, function(tt)
      tt:AddLine(e.name, 1, 0.82, 0)
      tt:AddLine(string.format("Duration: %s   Recommended party power: %d", TCF.FormatDuration(e.dur), e.rec), 1, 1, 1)
      local chestName = TCF.CHEST_BY_KEY[e.chest[1]].name
      local function an(n) return (n:match("^[AEIOUaeiou]") and "an " or "a ") .. n end
      local rewards = string.format("Rewards: %d XP for each cat, about %d TapCoins and a %d%% chance of %s.",
        floor(e.dur / 60 * 5), floor(e.coins * 0.5), floor(e.chest[2] * 100 + 0.5), an(chestName))
      if e.rolls > 0 then
        local bonusName = TCF.CHEST_BY_KEY[e.chest[1] == "heroic" and "strong" or "pouch"].name
        rewards = rewards .. string.format(" Also %d bonus roll%s with a %d%% chance each of %s.", e.rolls, e.rolls == 1 and "" or "s",
          floor(TCF.ExpeditionBonusChance(e) * 100 + 0.5), an(bonusName))
      else
        rewards = rewards .. " Short trips are mostly for XP and TapCoins; longer ones bring more chests."
      end
      if e.dchest then
        rewards = rewards .. string.format(" Also a %d%% chance of %s.", floor(e.dchest * 100 + 0.5), an(TCF.CHEST_BY_KEY.dungeon.name))
      end
      if e.hoard then
        rewards = rewards .. string.format(" Also a %d%% chance of %s.", floor(e.hoard * 100 + 0.5), an(TCF.CHEST_BY_KEY.raid.name))
      end
      tt:AddLine(rewards, 0.8, 0.8, 0.8, true)
      tt:AddLine("A failed expedition brings back half the XP and only a few TapCoins.", 0.7, 0.7, 0.7, true)
    end)
    r.exp = e
    rows[i] = r
  end

  local function refresh()
    local st = TCF.db.expeditions or { active = {} }
    local now = time()
    for i, r in ipairs(act) do
      local ex = st.active[i]
      r.index = ex and i
      local show = ex ~= nil
      r.icon:SetShown(show); r.name:SetShown(show); r.bar:SetShown(show); r.chance:SetShown(show); r.claim:SetShown(show)
      for _, t in ipairs(r.party) do t:SetShown(show) end
      r.empty:SetShown(not show)
      if ex then
        local e = TCF.EXPEDITION_BY_KEY[ex.key]
        r.icon:SetTexture(TCF.Icon(e.icon))
        r.name:SetText(e.name)
        for k, c in ipairs(ex.members) do TCF.SetClassIcon(r.party[k], c) end
        local total = ex.finish - ex.start
        local left = ex.finish - now
        r.bar:SetMinMaxValues(0, total); r.bar:SetValue(min(total, now - ex.start))
        r.barText:SetText(left > 0 and (TCF.FormatDuration(left) .. " left") or "Back home")
        r.chance:SetText(string.format("%d%% success", floor(ex.chance * 100 + 0.5)))
        r.claim:SetEnabled(left <= 0)
      end
    end
    local members, n = {}, 0
    for _, b in ipairs(picks) do
      local away = TCF:IsOnExpedition(b.class)
      b.tex:SetDesaturated(away and true or false)
      b.sel:SetShown(win.party[b.class] and true or false)
      b.power:SetText(away and "|cffff9933away|r" or tostring(TCF:CombatStats(b.class).power))
      if win.party[b.class] then n = n + 1; members[#members + 1] = b.class end
    end
    local power = n > 0 and TCF:PartyPower(members) or 0
    partyPower:SetText(n == 3 and string.format("Party power |cffffd100%d|r", power) or string.format("|cff888888%d / 3 chosen|r", n))
    local full = #st.active >= TCF.MAX_EXPEDITIONS
    for _, r in ipairs(rows) do
      local e = r.exp
      r.info:SetText(string.format("|cffaaaaaa%s   rec. power %d|r", TCF.FormatDuration(e.dur), e.rec))
      if n == 3 then
        local c = TCF:ExpeditionChance(power, e.rec)
        local col = c >= 0.8 and "|cff20ff20" or c >= 0.5 and "|cffffd100" or "|cffff5050"
        r.chance:SetText(col .. floor(c * 100 + 0.5) .. "%|r")
      else
        r.chance:SetText("")
      end
      r.go:SetEnabled(n == 3 and not full)
    end
  end

  -- keep the countdown and the Claim button current while this page is open
  -- (OnUpdate only runs while the page is shown)
  local acc = 0
  page:HookScript("OnUpdate", function(_, elapsed)
    acc = acc + elapsed
    if acc < 1 then return end
    acc = 0
    if TCF.db and TCF.db.expeditions and #TCF.db.expeditions.active > 0 then refresh() end
  end)

  -- Solo / Party switch, top right
  local partyPage = CreateFrame("Frame", nil, root); partyPage:SetAllPoints(); partyPage:Hide()
  local partyRefresh = TCF.UI.BuildPartyExpeditions(partyPage, win)
  win.expView = win.expView or "solo"
  local bSolo, bParty
  local function refreshAll()
    local party = win.expView == "party"
    soloPage:SetShown(not party); partyPage:SetShown(party)
    bSolo:SetEnabled(party); bParty:SetEnabled(not party)
    local inv = TCF.GX and TCF.GX.inv
    local waiting = (inv and inv.state == "invited") or (TCF.GroupExpReady and TCF:GroupExpReady())
    bParty:SetText(waiting and "Party |cff20ff20(1)|r" or "Party")
    if party then partyRefresh() else refresh() end
  end
  local function setView(v) win.expView = v; TCF:PlaySound("click"); refreshAll() end
  bParty = Button(root, "Party", 74, 20, function() setView("party") end)
  bParty:SetPoint("TOPRIGHT", -16, -10)
  bSolo = Button(root, "Solo", 64, 20, function() setView("solo") end)
  bSolo:SetPoint("RIGHT", bParty, "LEFT", -4, 0)
  Tip(bSolo, function(tt) tt:AddLine("Solo expeditions", 1, 0.82, 0); tt:AddLine("Send three of your own cats. Two at a time.", 1, 1, 1, true) end)
  Tip(bParty, function(tt)
    tt:AddLine("Party expeditions", 1, 0.82, 0)
    tt:AddLine("Send cats out together with group members who have TapCatForever. They have their own slot, so your solo slots stay free.", 1, 1, 1, true)
  end)
  win.expSwitch = { solo = bSolo, party = bParty, soloPage = soloPage, partyPage = partyPage }
  -- an invite or a party back home refreshes the page (PartyExpeditions.lua calls this)
  TCF.GX.OnChange = function()
    if root:IsVisible() then refreshAll() end
  end
  return refreshAll
end
