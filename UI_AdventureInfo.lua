-- TapCatForever: the Adventure page's explanations and farming (on top of UI_Adventure.lua).
--  * a Help button and a quiet "How Adventure works" guide that opens by itself the first time
--  * a status line under the fight that says what the cat is doing and what it waits for
--  * the zone name's tooltip: what is still left to earn in this zone
--  * Bosses and loot: each boss's first-kill reward and its loot for this class, with "Farm"
--  * while farming: the farming line and a Stop farming button
local ADDON, TCF = ...
local floor, max, min = math.floor, math.max, math.min

local GUIDE = {
  { title = "How Adventure works: fights and zones", body =
    "|cffffd100Fights|r: press Start and your cat fights by itself with this class's gear, level and learned abilities. Every key you press lands a bonus paw strike. If it loses, it heals and tries again.\n\n" ..
    "|cffffd100Stages and zones|r: each zone has trash packs and bosses in turn, for example 12 stages in Shadowfang Keep. The last stage is the zone's final boss. Beating it clears the zone.\n\n" ..
    "|cffffd100Auto-advance on|r: after each win your cat moves to the next stage. After the final boss it goes on to the next zone once it is within 2 levels of that zone's level (raids wait for level 60). Until then it runs the cleared zone again from the start and farms it. After 3 losses in a row it drops back to an easier pack.\n\n" ..
    "|cffffd100Auto-advance off|r: your cat stays on its stage and farms it.\n\n" ..
    "|cffffd100Going back or ahead|r: use < and > by the zone name to visit an earlier zone or go on to the next one (no level limit, but the enemies may be too strong), and < Stage and Stage > to pick a stage.\n\n" ..
    "The line under the fight always says what your cat is doing and what it waits for. Hover the zone name to see what is left to earn there." },
  { title = "How Adventure works: rewards", body =
    "|cffffd100First kills|r: the first time your cat beats each boss it gets a reward that grows with the zone:\n" ..
    "- Open-world zones: a green piece of gear or a Cat Treat Pouch\n" ..
    "- Early dungeons: a piece of the boss's loot, sometimes with a Pouch\n" ..
    "- Dungeons from level 30: a Rare or better piece, with a chance of an Adventurer's Strongbox\n" ..
    "- Dungeons from level 45: two pieces, or a piece and a Dungeon Chest\n" ..
    "- Raids: two pieces with a chance of a Raider's Hoard. Final bosses: two or three pieces and a Hoard\n\n" ..
    "|cffffd100Zone clears|r: TapCoins and a chest the first time each cat clears a zone (a quarter of the TapCoins if another of your cats cleared it first).\n\n" ..
    "|cffffd100Chests for fighting time|r: boss kills drop a Cat Treat Pouch about every 18 minutes of fighting (raids: a Raider's Hoard about every 3 hours). Finishing a dungeon again gives a Dungeon Chest about every 2 to 3 hours of dungeon fighting.\n\n" ..
    "|cffffd100Small finds|r: regular enemies now and then drop plain gear, cloth and meat.\n\n" ..
    "|cffffd100Farming|r: bosses can drop their real loot again on later kills, with a small chance each time (a typical piece about 1 in 500 kills, a few hours of farming). Open Bosses and loot, pick a piece and press Farm: your cat stays on that boss until it drops.\n\n" ..
    "Some bosses also drop cat skins and effects (Cosmetic only)." },
}

local ROWS = 9

local build = TCF.UI.Builders.adventure
TCF.UI.Builders.adventure = function(page, win)
  local refresh = build(page, win)
  local U = TCF.UI
  local Text, Button, Tip = U.Text, U.Button, U.Tip
  local function raise(f, by)
    if f.SetFrameLevel and page.GetFrameLevel and page:GetFrameLevel() then f:SetFrameLevel(page:GetFrameLevel() + by) end
  end

  ------------------------------------------------ status line (the old help text) and Stop farming
  local status = page.advHelp or Text(page, "GameFontDisableSmall", nil, "LEFT")
  status:ClearAllPoints(); status:SetPoint("BOTTOMLEFT", 16, 10); status:SetWidth(524)
  if status.SetFontObject then status:SetFontObject("GameFontHighlightSmall") end
  page.advStatus = status
  local stopFarm = Button(page, "Stop farming", 96, 20, function()
    TCF:AdvStopFarm(); TCF:AdvLog("Farming stopped."); win:Refresh()
  end)
  stopFarm:SetPoint("BOTTOMRIGHT", -14, 8); stopFarm:Hide()
  Tip(stopFarm, function(tt)
    tt:AddLine("Stop farming", 1, 0.82, 0)
    tt:AddLine("Your cat stops staying on this boss. Auto-advance goes back to how it was.", 1, 1, 1, true)
  end)
  page.advStopFarm = stopFarm

  ------------------------------------------------ the zone name's tooltip: what's left to earn
  local zoneHover = CreateFrame("Frame", nil, page)
  zoneHover:SetPoint("TOPLEFT", 12, -8); zoneHover:SetSize(330, 38)
  zoneHover:EnableMouse(true)
  Tip(zoneHover, function(tt)
    local adv = TCF:CD().adv
    local t = TCF:AdvTier(adv.tier)
    tt:AddLine(t.name .. ": left to earn", 1, 0.82, 0)
    for _, line in ipairs(TCF:AdvZoneSummary(adv.tier)) do tt:AddLine(line, 1, 1, 1, true) end
  end)
  page.advZoneHover = zoneHover

  ------------------------------------------------ the guide
  local guide = CreateFrame("Frame", nil, page, U.BT)
  guide:SetPoint("TOPLEFT", 10, -50); guide:SetPoint("BOTTOMRIGHT", -10, 10)
  raise(guide, 50)
  if guide.SetBackdrop then guide:SetBackdrop(U.BACKDROP_DIALOG) end
  guide:EnableMouse(true)
  guide.title = Text(guide, "GameFontNormalLarge", nil, "LEFT"); guide.title:SetPoint("TOPLEFT", 22, -20)
  guide.body = Text(guide, "GameFontHighlightSmall", nil, "LEFT"); guide.body:SetPoint("TOPLEFT", 22, -46); guide.body:SetWidth(496)
  if guide.body.SetSpacing then guide.body:SetSpacing(2) end
  if guide.body.SetJustifyV then guide.body:SetJustifyV("TOP") end
  local gotIt = Button(guide, "Got it", 90, 22, function() guide:Hide() end); gotIt:SetPoint("BOTTOMRIGHT", -18, 14)
  local more = Button(guide, "Rewards >", 100, 22, nil); more:SetPoint("RIGHT", gotIt, "LEFT", -8, 0)
  local function showGuide(i)
    guide.pageNo = i
    guide.title:SetText(GUIDE[i].title); guide.body:SetText(GUIDE[i].body)
    more:SetText(i == 1 and "Rewards >" or "< Fights")
    guide:Show()
  end
  more:SetScript("OnClick", function() showGuide(guide.pageNo == 1 and 2 or 1) end)
  guide:Hide()
  page.advGuide = guide
  TCF.ShowAdventureGuide = function(_, i) showGuide(i or 1) end

  ------------------------------------------------ Bosses and loot (with Farm)
  local loot = CreateFrame("Frame", nil, page, U.BT)
  loot:SetPoint("TOPLEFT", 10, -50); loot:SetPoint("BOTTOMRIGHT", -10, 10)
  raise(loot, 50)
  if loot.SetBackdrop then loot:SetBackdrop(U.BACKDROP_DIALOG) end
  loot:EnableMouse(true)
  loot.title = Text(loot, "GameFontNormalLarge", nil, "LEFT"); loot.title:SetPoint("TOPLEFT", 20, -18)
  local closeLoot = Button(loot, "Close", 70, 22, function() loot:Hide() end); closeLoot:SetPoint("TOPRIGHT", -16, -14)
  loot.bossBtns = {}
  for i = 1, 6 do
    local b = Button(loot, "", 150, 22, function() loot.boss = i; loot:Refresh() end)
    b:SetPoint("TOPLEFT", 16, -48 - (i - 1) * 26)
    Tip(b, function(tt)
      local tier = loot.tier
      local t = TCF.TIERS[tier]
      local bb = t and t.bosses[i]
      if not bb then return end
      tt:AddLine(bb[1], 1, 0.82, 0)
      local beaten = TCF:CD().adv.cleared[TCF.AdvStageCode(tier, i * 2)]
      tt:AddLine(beaten and "Beaten: first-kill reward done." or ("First kill: " .. TCF:AdvFirstKillText(tier, i == #t.bosses) .. "."), 1, 1, 1, true)
      if not TCF:AdvCanGoTo(tier, i * 2) then tt:AddLine("Your cat hasn't reached this boss yet.", 1, 0.4, 0.4, true) end
    end)
    loot.bossBtns[i] = b
  end
  loot.head = Text(loot, "GameFontHighlightSmall", nil, "LEFT"); loot.head:SetPoint("TOPLEFT", 182, -48); loot.head:SetWidth(330)
  if loot.head.SetJustifyV then loot.head:SetJustifyV("TOP") end
  loot.farmBoss = Button(loot, "Farm this boss", 120, 20, function()
    local ok, why = TCF:AdvStartFarm(loot.tier, loot.boss, nil)
    if ok then loot:Hide() elseif why then TCF:Print(why, true) end
    win:Refresh()
  end)
  loot.farmBoss:SetPoint("TOPLEFT", 182, -104)
  Tip(loot.farmBoss, function(tt)
    tt:AddLine("Farm this boss", 1, 0.82, 0)
    tt:AddLine("Your cat stays on this boss's stage and fights it again and again (Auto-advance turns off until you stop). Each kill has a small chance of one of the pieces below.", 1, 1, 1, true)
  end)
  loot.rows = {}
  for r = 1, ROWS do
    local row = CreateFrame("Button", nil, loot)
    row:SetSize(340, 26); row:SetPoint("TOPLEFT", 180, -130 - (r - 1) * 28)
    row.icon = row:CreateTexture(nil, "ARTWORK"); row.icon:SetSize(22, 22); row.icon:SetPoint("LEFT", 2, 0)
    row.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
    row.name = Text(row, "GameFontHighlightSmall", nil, "LEFT"); row.name:SetPoint("LEFT", row.icon, "RIGHT", 6, 0); row.name:SetWidth(180)
    if row.name.SetWordWrap then row.name:SetWordWrap(false) end
    row.pct = Text(row, "GameFontHighlightSmall", nil, "RIGHT"); row.pct:SetPoint("RIGHT", -58, 0); row.pct:SetWidth(70)
    row.farm = Button(row, "Farm", 52, 20, function()
      if not row.item then return end
      local ok, why = TCF:AdvStartFarm(loot.tier, loot.boss, row.item.id)
      if ok then loot:Hide() elseif why then TCF:Print(why, true) end
      win:Refresh()
    end)
    row.farm:SetPoint("RIGHT", 0, 0)
    row:SetScript("OnEnter", function(s)
      if not s.item then return end
      GameTooltip:SetOwner(s, "ANCHOR_RIGHT")
      TCF:GearTooltip(GameTooltip, s.item)
      GameTooltip:AddLine(string.format("Later kills of %s: about %s per kill (%s).", s.bossName or "this boss", TCF.AdvPct(s.p), TCF.AdvOneIn(s.p)), 0.6, 0.8, 1, true)
      GameTooltip:Show()
    end)
    row:SetScript("OnLeave", function() GameTooltip:Hide() end)
    row:Hide()
    loot.rows[r] = row
  end
  loot.pageText = Text(loot, "GameFontHighlightSmall"); loot.pageText:SetPoint("BOTTOM", 90, 18)
  loot.prev = Button(loot, "<", 26, 20, function() loot.page = max(1, (loot.page or 1) - 1); loot:Refresh() end)
  loot.prev:SetPoint("RIGHT", loot.pageText, "LEFT", -6, 0)
  loot.next = Button(loot, ">", 26, 20, function() loot.page = (loot.page or 1) + 1; loot:Refresh() end)
  loot.next:SetPoint("LEFT", loot.pageText, "RIGHT", 6, 0)
  loot.empty = Text(loot, "GameFontHighlightSmall", nil, "LEFT"); loot.empty:SetPoint("TOPLEFT", 182, -134); loot.empty:SetWidth(330)

  function loot:Refresh()
    local tier = self.tier
    local t = TCF.TIERS[tier]
    local adv = TCF:CD().adv
    self.boss = min(max(1, self.boss or 1), #t.bosses)
    self.title:SetText(t.name .. ": bosses and loot")
    for i, b in ipairs(self.bossBtns) do
      local bb = t.bosses[i]
      if bb then
        local beaten = adv.cleared[TCF.AdvStageCode(tier, i * 2)]
        local reached = TCF:AdvCanGoTo(tier, i * 2)
        b:SetText((i == self.boss and "> " or "") .. (reached and "" or "|cff888888") .. bb[1] .. (reached and "" or "|r"))
        b.beaten = beaten
        b:Show()
      else b:Hide() end
    end
    local bi = self.boss
    local bName = t.bosses[bi][1]
    local list, total = TCF:AdvFarmTable(tier, bi)
    local beaten = adv.cleared[TCF.AdvStageCode(tier, bi * 2)]
    local reached = TCF:AdvCanGoTo(tier, bi * 2)
    local first = beaten and "|cff20ff20First kill done.|r" or ("First kill: " .. TCF:AdvFirstKillText(tier, bi == #t.bosses) .. ".")
    local again = #list > 0 and string.format("Later kills: about %s per kill for one of these pieces.", TCF.AdvPct(total))
      or "No loot of its own for your cat on later kills."
    self.head:SetText(bName .. "\n" .. first .. "\n" .. again .. (reached and "" or "\n|cffff6060Your cat hasn't reached this boss yet.|r"))
    self.farmBoss:SetEnabled(reached and #list > 0)
    local pages = max(1, math.ceil(#list / ROWS))
    self.page = min(max(1, self.page or 1), pages)
    local off = (self.page - 1) * ROWS
    for r, row in ipairs(self.rows) do
      local e = list[off + r]
      if e then
        local it = e[1]
        row.item, row.p, row.bossName = it, e[2], bName
        row.icon:SetTexture(TCF.Icon(it.icon))
        row.name:SetText(TCF.GearLink(it))
        row.pct:SetText("about " .. TCF.AdvPct(e[2]))
        row.farm:SetEnabled(reached)
        row:Show()
      else
        row.item = nil; row:Hide()
      end
    end
    self.empty:SetText(#list == 0 and (TCF.AdvBand(t) == "world"
      and "Open-world bosses have no loot tables of their own. Their first kill gives a green piece or a Cat Treat Pouch, and chests can hold this zone's gear."
      or "Nothing from this boss suits your cat's class.") or "")
    self.pageText:SetText(pages > 1 and string.format("%d / %d", self.page, pages) or "")
    self.prev:SetShown(pages > 1); self.next:SetShown(pages > 1)
    self.prev:SetEnabled(self.page > 1); self.next:SetEnabled(self.page < pages)
  end
  loot:Hide()
  page.advLoot = loot
  TCF.advLootPanel = loot
  local function showLoot()
    local adv = TCF:CD().adv
    guide:Hide()
    loot.tier = adv.tier
    loot.boss = adv.stage % 2 == 0 and adv.stage / 2 or min(#TCF:AdvTier(adv.tier).bosses, floor(adv.stage / 2) + 1)
    if adv.farm and adv.farm.tier == adv.tier then loot.boss = adv.farm.boss end
    loot.page = 1
    loot:Refresh(); loot:Show()
  end
  TCF.ShowAdventureLoot = function() showLoot() end

  ------------------------------------------------ the two buttons on the right of the zone line
  -- (under the zone arrows, above the fight panel at -50)
  local lootBtn = Button(page, "Bosses and loot", 112, 17, function()
    if loot:IsShown() then loot:Hide() else showLoot() end
  end)
  lootBtn:SetPoint("TOPRIGHT", -12, -34)
  Tip(lootBtn, function(tt)
    tt:AddLine("Bosses and loot", 1, 0.82, 0)
    tt:AddLine("Each boss in this zone, its first-kill reward and the loot it can drop for your cat. Pick a piece and press Farm to stay on that boss until it drops.", 1, 1, 1, true)
  end)
  local helpBtn = Button(page, "Help", 50, 17, function()
    if guide:IsShown() then guide:Hide() else loot:Hide(); showGuide(1) end
  end)
  helpBtn:SetPoint("RIGHT", lootBtn, "LEFT", -4, 0)
  Tip(helpBtn, function(tt)
    tt:AddLine("How Adventure works", 1, 0.82, 0)
    tt:AddLine("Fights, stages and zones, what Auto-advance does, and every reward.", 1, 1, 1, true)
  end)
  page.advLootBtn, page.advHelpBtn = lootBtn, helpBtn

  ------------------------------------------------ keeping it current
  local function update()
    local adv = TCF:CD().adv
    local farming = adv.farm ~= nil
    status:SetText(TCF:AdvStatusText())
    status:SetWidth(farming and 420 or 524)
    stopFarm:SetShown(farming)
    if loot:IsShown() and loot.tier then loot:Refresh() end
    -- the guide opens by itself the first time the Adventure page is seen (once per account)
    if page:IsVisible() and not TCF.db.advGuideSeen then
      TCF.db.advGuideSeen = true
      showGuide(1)
    end
  end
  local ticker = CreateFrame("Frame", nil, page)
  local acc = 0
  ticker:SetScript("OnUpdate", function(_, e)
    acc = acc + e
    if acc < 0.5 then return end
    acc = 0
    if page:IsVisible() then update() end
  end)

  return function(light)
    refresh(light)
    update()
  end
end
