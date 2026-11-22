-- TapCatForever: the Party view of the Expeditions tab (the rules and messages are in
-- PartyExpeditions.lua). From top to bottom: the party expedition slot (its players, a countdown and
-- Claim), the invite you got or sent (Accept / Decline, or Start now / Call off), your cats for it,
-- the place, length and difficulty, what it needs and gives, and the Invite button.
local ADDON, TCF = ...
local floor, max, min = math.floor, math.max, math.min

TCF.UI.BuildPartyExpeditions = function(page, win)
  local U = TCF.UI
  local Text, Button, Tip, Panel = U.Text, U.Button, U.Tip, U.Panel
  local GX = TCF.GX
  GX.picked = GX.picked or {}
  GX.choice = GX.choice or { place = 1, len = 3, diff = 1 }
  local ch = GX.choice

  local sub = Text(page, "GameFontDisableSmall", "Send cats out together with group members who have TapCatForever. Once it starts it keeps going for everyone, even if the group breaks up.", "LEFT")
  sub:SetPoint("TOPLEFT", 16, -30); sub:SetWidth(530)

  ------------------------------------------------ the party slot
  local slot = Panel(page, 528, 56, 0.9); slot:SetPoint("TOP", 0, -52)
  slot.icon = slot:CreateTexture(nil, "ARTWORK"); slot.icon:SetSize(38, 38); slot.icon:SetPoint("LEFT", 8, 0)
  slot.icon:SetTexture(TCF.Icon("INV_Misc_GroupNeedMore", "INV_Misc_Map_01"))
  slot.name = Text(slot, "GameFontNormal", nil, "LEFT"); slot.name:SetPoint("TOPLEFT", slot.icon, "TOPRIGHT", 8, -1)
  slot.who = Text(slot, "GameFontHighlightSmall", nil, "LEFT"); slot.who:SetPoint("TOPLEFT", slot.name, "BOTTOMLEFT", 0, -2); slot.who:SetWidth(300)
  slot.bar = CreateFrame("StatusBar", nil, slot); slot.bar:SetSize(190, 11); slot.bar:SetPoint("BOTTOMLEFT", slot.icon, "BOTTOMRIGHT", 8, 0)
  slot.bar:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar"); slot.bar:SetStatusBarColor(0.35, 0.7, 1)
  local sbg = slot.bar:CreateTexture(nil, "BACKGROUND"); sbg:SetAllPoints(); sbg:SetColorTexture(0, 0, 0, 0.6)
  slot.barText = Text(slot.bar, "GameFontHighlightSmall"); slot.barText:SetPoint("CENTER")
  slot.chance = Text(slot, "GameFontHighlightSmall", nil, "RIGHT"); slot.chance:SetPoint("RIGHT", -96, 0)
  slot.claim = Button(slot, "Claim", 80, 22, function()
    TCF:GroupExpClaim(); TCF:PlaySound("click"); win:Refresh()
  end)
  slot.claim:SetPoint("RIGHT", -8, 0)
  slot.empty = Text(slot, "GameFontDisable", "Free party expedition slot", "LEFT"); slot.empty:SetPoint("LEFT", 16, 0)
  Tip(slot, function(tt)
    local g = TCF:GroupExp()
    if not g then
      tt:AddLine("Party expedition slot", 1, 0.82, 0)
      tt:AddLine("One party expedition at a time. Your two solo slots stay free.", 1, 1, 1, true)
      return
    end
    tt:AddLine(GX.Describe(g.place, g.len, g.diff), 1, 0.82, 0)
    for _, p in ipairs(g.players or {}) do
      local names = {}
      for _, c in ipairs(p.cats) do names[#names + 1] = TCF.CLASS_BY_KEY[c].name end
      tt:AddDoubleLine(p.name, string.format("%s  Power %s", table.concat(names, ", "), TCF.Commas(p.power)), 1, 1, 1, 0.8, 0.8, 0.8)
    end
    tt:AddLine(string.format("Power %s of %s needed: %d%% chance.", TCF.Commas(g.power), TCF.Commas(g.need), floor(g.chance / 10 + 0.5)), 0.8, 0.8, 0.8, true)
    tt:AddLine("Everybody gets the same result and claims their own rewards.", 0.7, 0.7, 0.7, true)
  end)

  ------------------------------------------------ the invite (in or out)
  local inv = Panel(page, 528, 44, 0.9); inv:SetPoint("TOP", 0, -112)
  inv.text = Text(inv, "GameFontHighlightSmall", nil, "LEFT"); inv.text:SetPoint("LEFT", 12, 0); inv.text:SetWidth(300)
  -- Accept / Decline for an invite you got; Start now / Call off for the one you sent
  inv.yes = Button(inv, "Accept", 80, 22, function()
    local ok, err
    if GX.out then ok, err = TCF:GroupExpStartNow()
    else ok, err = TCF:GroupExpAnswer(true) end
    if err then TCF:Print(err, true) end
    TCF:PlaySound("click"); win:Refresh()
  end)
  inv.no = Button(inv, "Decline", 80, 22, function()
    if GX.out then TCF:GroupExpWithdraw() else TCF:GroupExpAnswer(false) end
    TCF:PlaySound("click"); win:Refresh()
  end)
  inv.no:SetPoint("RIGHT", -8, 0); inv.yes:SetPoint("RIGHT", inv.no, "LEFT", -4, 0)
  inv.left = Text(inv, "GameFontDisableSmall", nil, "RIGHT"); inv.left:SetPoint("RIGHT", inv.yes, "LEFT", -8, 0)

  ------------------------------------------------ your cats
  local pickLabel = Text(page, "GameFontNormal", "Your cats (up to 3):", "LEFT"); pickLabel:SetPoint("TOPLEFT", 16, -164)
  local myPower = Text(page, "GameFontHighlight", nil, "RIGHT"); myPower:SetPoint("TOPRIGHT", -16, -164)
  local picks = {}
  for i, cl in ipairs(TCF.CLASSES) do
    local b = CreateFrame("Button", nil, page)
    b:SetSize(36, 36); b:SetPoint("TOPLEFT", 16 + (i - 1) * 58, -182)
    local t = b:CreateTexture(nil, "ARTWORK"); t:SetAllPoints(); TCF.SetClassIcon(t, cl.key)
    b.tex = t
    b.sel = b:CreateTexture(nil, "OVERLAY"); b.sel:SetPoint("TOPLEFT", -6, 6); b.sel:SetPoint("BOTTOMRIGHT", 6, -6)
    b.sel:SetTexture("Interface\\Buttons\\CheckButtonHilight"); b.sel:SetBlendMode("ADD")
    b.power = Text(page, "GameFontHighlightSmall"); b.power:SetPoint("TOP", b, "BOTTOM", 0, -2)
    b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    b:SetScript("OnClick", function()
      if TCF:SoloExpeditionOf(cl.key) then return end
      if GX.picked[cl.key] then GX.picked[cl.key] = nil
      else
        local n = 0
        for _ in pairs(GX.picked) do n = n + 1 end
        if n < GX.MAX_CATS then GX.picked[cl.key] = true end
      end
      -- after accepting, a new choice goes to the starter until the expedition sets off
      TCF:GroupExpRepick()
      TCF:PlaySound("click"); win:Refresh()
    end)
    Tip(b, function(tt)
      local cs = TCF:CombatStats(cl.key)
      tt:AddLine(cl.name, cl.color[1], cl.color[2], cl.color[3])
      tt:AddLine(string.format("Level %d   Power %d", TCF:CD(cl.key).level, cs.power), 1, 1, 1)
      if TCF:SoloExpeditionOf(cl.key) then tt:AddLine("Away on an expedition", 1, 0.6, 0.2) end
      tt:AddLine("With none picked, your current cat goes.", 0.7, 0.7, 0.7, true)
    end)
    b.class = cl.key
    picks[i] = b
  end

  ------------------------------------------------ place, length, difficulty
  local places = TCF:GroupExpPlaces()
  ch.place = max(1, min(#places, ch.place))
  local placeLabel = Text(page, "GameFontNormal", "Place:", "LEFT"); placeLabel:SetPoint("TOPLEFT", 16, -244)
  local prev = Button(page, "<", 24, 20, function() ch.place = ch.place > 1 and ch.place - 1 or #places; TCF:PlaySound("click"); win:Refresh() end)
  prev:SetPoint("TOPLEFT", 110, -241)
  local placeName = Text(page, "GameFontHighlight"); placeName:SetPoint("LEFT", prev, "RIGHT", 6, 0); placeName:SetWidth(200)
  local nextB = Button(page, ">", 24, 20, function() ch.place = ch.place < #places and ch.place + 1 or 1; TCF:PlaySound("click"); win:Refresh() end)
  nextB:SetPoint("LEFT", placeName, "RIGHT", 6, 0)
  local placeKind = Text(page, "GameFontDisableSmall", nil, "LEFT"); placeKind:SetPoint("LEFT", nextB, "RIGHT", 10, 0)

  local lenLabel = Text(page, "GameFontNormal", "Length:", "LEFT"); lenLabel:SetPoint("TOPLEFT", 16, -272)
  local lenBtns = {}
  for i, L in ipairs(GX.LENGTHS) do
    local b = Button(page, L[2], 64, 20, function() ch.len = i; TCF:PlaySound("click"); win:Refresh() end)
    b:SetPoint("TOPLEFT", 110 + (i - 1) * 68, -269)
    lenBtns[i] = b
  end
  local diffLabel = Text(page, "GameFontNormal", "Difficulty:", "LEFT"); diffLabel:SetPoint("TOPLEFT", 16, -300)
  local diffBtns = {}
  for i, D in ipairs(GX.DIFFS) do
    local b = Button(page, D.name, 80, 20, function() ch.diff = i; TCF:PlaySound("click"); win:Refresh() end)
    b:SetPoint("TOPLEFT", 110 + (i - 1) * 84, -297)
    Tip(b, function(tt)
      tt:AddLine(D.name, 1, 0.82, 0)
      if i == 1 then
        tt:AddLine("Needs the usual Power. Usual rewards.", 1, 1, 1, true)
      else
        tt:AddLine(string.format("Needs %s times the Power of Normal. Rewards: %d%% more XP, TapCoins and chest chance.", D.req,
          floor((D.reward - 1) * 100 + 0.5)), 1, 1, 1, true)
      end
      if i == 3 then tt:AddLine("Heroic also has a chance of a Dungeon Chest (dungeons) or a Raider's Hoard (raids).", 0.8, 0.8, 0.8, true) end
    end)
    diffBtns[i] = b
  end

  local info = Text(page, "GameFontHighlightSmall", nil, "LEFT"); info:SetPoint("TOPLEFT", 16, -330); info:SetWidth(528)
  if info.SetJustifyV then info:SetJustifyV("TOP") end

  local go = Button(page, "Invite my group", 150, 24, function()
    local cats = TCF:GroupExpDefaultCats()
    local ok, err = TCF:GroupExpInvite(places[ch.place].key, ch.len, ch.diff, cats)
    if not ok and err then TCF:Print(err, true) end
    TCF:PlaySound("click"); win:Refresh()
  end)
  go:SetPoint("TOPLEFT", 16, -418)
  Tip(go, function(tt)
    tt:AddLine("Invite my group", 1, 0.82, 0)
    tt:AddLine("Group members with TapCatForever get a small invite above their cat for 60 seconds. It sets off when everyone has answered, or after 60 seconds with at least one player.", 1, 1, 1, true)
    tt:AddLine("Group members on an older TapCatForever can't join.", 0.7, 0.7, 0.7, true)
  end)
  local note = Text(page, "GameFontDisableSmall", nil, "LEFT"); note:SetPoint("LEFT", go, "RIGHT", 10, 0); note:SetWidth(360)

  local function chosenCats()
    local list = TCF:GroupExpDefaultCats()
    -- a picked cat that left on a solo expedition meanwhile is dropped
    for i = #list, 1, -1 do if TCF:SoloExpeditionOf(list[i]) then table.remove(list, i) end end
    return list
  end

  local function refresh()
    if not TCF.db then return end
    local t = GX.ServerNow()
    local g = TCF:GroupExp()
    -- the slot
    local show = g ~= nil
    slot.name:SetShown(show); slot.who:SetShown(show); slot.bar:SetShown(show); slot.chance:SetShown(show); slot.claim:SetShown(show)
    slot.empty:SetShown(not show)
    slot.icon:SetDesaturated(not show)
    if g then
      slot.name:SetText(GX.Describe(g.place, g.len, g.diff))
      local names = {}
      for _, p in ipairs(g.players or {}) do names[#names + 1] = p.name end
      slot.who:SetText("|cffaaaaaa" .. table.concat(names, ", ") .. "|r")
      local total = max(1, g.finish - g.start)
      local left = g.finish - t
      slot.bar:SetMinMaxValues(0, total); slot.bar:SetValue(min(total, max(0, t - g.start)))
      slot.barText:SetText(left > 0 and (TCF.FormatDuration(left) .. " left") or "Back home")
      slot.chance:SetText(string.format("%d%% success", floor(g.chance / 10 + 0.5)))
      slot.claim:SetEnabled(left <= 0)
    end
    -- the invite
    local x, out = GX.inv, GX.out
    local now = GetTime and GetTime() or 0
    if x and x.state == "invited" then
      inv:Show(); inv.yes:Show(); inv.no:Show(); inv.yes:SetText("Accept")
      inv.text:SetText(string.format("%s invites your cat: |cffffd100%s|r", x.from, GX.Describe(x.place, x.len, x.diff)))
      inv.left:SetText(string.format("%d s", max(0, floor(x.expires - now))))
    elseif x and x.state == "accepted" then
      inv:Show(); inv.yes:Hide(); inv.no:Hide()
      inv.text:SetText(string.format("You joined %s's party expedition: |cffffd100%s|r. Waiting for %s to send it off.", x.from, GX.Describe(x.place, x.len, x.diff), x.from))
      inv.left:SetText("")
    elseif out then
      inv:Show(); inv.yes:Show(); inv.no:Show()
      inv.yes:SetText("Start now"); inv.no:SetText("Call off")
      local joined, no = {}, {}
      for _, a in pairs(out.answers) do
        if a.ans == "y" then joined[#joined + 1] = a.name else no[#no + 1] = a.name end
      end
      table.sort(joined); table.sort(no)
      local txt = "Waiting for answers."
      if #joined > 0 then txt = "Joined: " .. table.concat(joined, ", ") .. "." end
      if #no > 0 then txt = txt .. " |cff999999Not coming: " .. table.concat(no, ", ") .. ".|r" end
      inv.text:SetText(txt)
      inv.yes:SetEnabled(#joined > 0)
      inv.left:SetText(string.format("%d s", max(0, floor(out.expires - now))))
    else
      inv:Hide()
    end
    if not out then inv.no:SetText("Decline") end
    -- your cats
    local cats = chosenCats()
    local chosen = {}
    for _, c in ipairs(cats) do chosen[c] = true end
    for _, b in ipairs(picks) do
      local away = TCF:SoloExpeditionOf(b.class)
      local busyG = g and TCF:GroupExpBusy(b.class)
      b.tex:SetDesaturated((away or busyG) and true or false)
      b.sel:SetShown(chosen[b.class] and true or false)
      b.power:SetText(away and "|cffff9933away|r" or busyG and "|cff66bbffparty|r" or tostring(TCF:CombatStats(b.class).power))
    end
    local power = TCF:GroupExpPower(cats)
    myPower:SetText(string.format("Your Power |cffffd100%s|r", TCF.Commas(power)))
    -- place, length, difficulty
    local p = places[ch.place]
    placeName:SetText(p.name)
    placeKind:SetText(p.raid and "Raid" or "Dungeon")
    for i, b in ipairs(lenBtns) do b:SetEnabled(i ~= ch.len) end
    for i, b in ipairs(diffBtns) do b:SetEnabled(i ~= ch.diff) end
    local need2, need5 = TCF.GroupExpNeed(p.key, ch.diff, 2), TCF.GroupExpNeed(p.key, ch.diff, 5)
    local xp, coins, rolls, chance, extra = TCF.GroupExpRewards(p.key, ch.len, ch.diff, 2)
    local main, extraKey = TCF.GroupExpChests(p.key, ch.diff)
    local lines = {
      string.format("Power needed for the best odds: %s with 2 players, up to %s with 5. Everyone's cats add up.", TCF.Commas(need2), TCF.Commas(need5)),
      string.format("Each player, on success with 2 players: %d XP for each cat, about %d TapCoins, %d chest roll%s with a %d%% chance each of %s%s.",
        xp, coins, rolls, rolls == 1 and "" or "s", floor(chance * 100 + 0.5), TCF.CHEST_BY_KEY[main].name,
        extraKey and string.format(", and a %d%% chance of %s", floor(extra * 100 + 0.5), TCF.CHEST_BY_KEY[extraKey].name) or ""),
      "More players: +10% XP and TapCoins for every other player, and one more chest roll with 3 or more. A failure brings half the XP and a few TapCoins.",
    }
    info:SetText(table.concat(lines, "\n"))
    -- the Invite button
    local friends = TCF:GroupExpFriends()
    local why
    if g then why = "Claim your party expedition first."
    elseif x and (x.state == "invited" or x.state == "accepted") then why = "Answer your invite first."
    elseif out then why = "Waiting for your group to answer."
    elseif friends == 0 then why = "Nobody in your group has TapCatForever yet."
    elseif #cats == 0 then why = "All your picked cats are away." end
    go:SetEnabled(why == nil)
    note:SetText(why or string.format("%d group member%s with TapCatForever.", friends, friends == 1 and "" or "s"))
  end

  local acc = 0
  page:HookScript("OnUpdate", function(_, e)
    acc = acc + e
    if acc < 1 then return end
    acc = 0
    if TCF:GroupExp() or GX.inv or GX.out then refresh() end
  end)
  win.partyExpUI = { slot = slot, inv = inv, picks = picks, go = go, note = note, info = info, placeName = placeName,
    prev = prev, next = nextB, lenBtns = lenBtns, diffBtns = diffBtns, myPower = myPower }
  return refresh
end
