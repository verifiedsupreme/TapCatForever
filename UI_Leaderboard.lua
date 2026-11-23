-- TapCatForever: the Leaderboard tab. The board, its saved data and the messages between players
-- are in Leaderboard.lua; this file only draws them.
--   Not joined: the opt-in panel (what the leaderboard is, what is shared and with whom, the one-time
--   Heroic Cache) and a big Join button, which turns on the same option as the Settings checkbox.
--   Joined: three sections (Total taps, Per class, Professions), your own row highlighted in each,
--   last seen, the mouse wheel to scroll, the limits note, and a Leave button that asks first.
local ADDON, TCF = ...
local floor, max, min = math.floor, math.max, math.min

local ROWS, ROW_H = 14, 18
local X0 = 16          -- left edge of the columns on the 560 x 494 page
local HEAD_Y = 104     -- the column headings, from the top of the page
local SECTIONS = { { "taps", "Total taps" }, { "class", "Per class" }, { "prof", "Professions" } }

-- columns per section: { heading, x, width, sort key (Total taps only), what the cell shows }
local COLS = {
  taps = { { "#", 0, 28, nil, "rank" }, { "Name", 30, 142, nil, "name" }, { "Cat level", 174, 58, "level", "l" },
           { "Taps", 234, 88, "taps", "t" }, { "Achievements", 324, 84, "ach", "a" }, { "Zones", 410, 44, "zones", "z" },
           { "Last seen", 456, 72, nil, "seen" } },
  class = { { "#", 0, 28, nil, "rank" }, { "Name", 30, 170, nil, "name" }, { "Level", 202, 70, nil, "val" },
            { "Taps", 274, 110, nil, "t" }, { "Playing", 386, 68, nil, "playing" }, { "Last seen", 456, 72, nil, "seen" } },
  prof = { { "#", 0, 28, nil, "rank" }, { "Name", 30, 170, nil, "name" }, { "Skill", 202, 90, nil, "val" },
           { "Taps", 294, 90, nil, "t" }, { "Playing", 386, 68, nil, "playing" }, { "Last seen", 456, 72, nil, "seen" } },
}
local MAX_COLS = 7
TCF.LB_COLS = COLS

local function hex(c) return string.format("|cff%02x%02x%02x", floor(c[1] * 255), floor(c[2] * 255), floor(c[3] * 255)) end

TCF.UI.Builders.leaderboard = function(page, win)
  local U = TCF.UI
  local Text, Button, Tip, Panel = U.Text, U.Button, U.Tip, U.Panel
  TCF.leaderboardView = page
  win.lbSection, win.lbSort, win.lbProf, win.lbScroll = win.lbSection or "taps", "taps", "gold", 0
  local confirming = false

  ------------------------------------------------ not joined: the opt-in panel
  local join = CreateFrame("Frame", nil, page); join:SetAllPoints()
  page.join = join
  local jTitle = Text(join, "GameFontNormalLarge", "Realm leaderboard", "LEFT"); jTitle:SetPoint("TOPLEFT", 16, -14)
  local function Para(y, head, body)
    local h = Text(join, "GameFontNormal", head, "LEFT"); h:SetPoint("TOPLEFT", 16, -y)
    local t = Text(join, "GameFontHighlightSmall", body, "LEFT"); t:SetPoint("TOPLEFT", 16, -(y + 18)); t:SetWidth(528)
    if t.SetSpacing then t:SetSpacing(2) end
    return t
  end
  local intro = Text(join, "GameFontHighlight", "See how your cats compare with other TapCatForever players on your realm: " ..
    "total taps, the level of each class cat, Trade Gold and profession skills. Join to see the leaderboard and be on it.", "LEFT")
  intro:SetPoint("TOPLEFT", 16, -42); intro:SetWidth(528)
  page.joinText = {
    intro,
    Para(96, "What is shared", "Your character's name and realm, your cat's class and cat level, the level of each of your " ..
      "class cats, your total taps, achievements earned, Adventure zones cleared, Trade Gold earned, your best profession " ..
      "skills and the addon version. Nothing else."),
    Para(166, "Who sees it", "Only TapCatForever players on your realm who joined too. Your cat is shared with them when " ..
      "you are in a party, raid or guild together, through the addon (the same way party cats work): no internet, and " ..
      "nothing shows in your chat. They pass on the players they know, so the board grows as you group up. " ..
      "Other addons in your group or guild could read what is shared."),
    Para(250, "Good to know", "Joining turns on Share my cat's progress in Settings > Help and info, for every character " ..
      "on your account. The same option lets the addon's developer see your addon version, cat class, cat level, zones " ..
      "cleared and TapCoins when they ask. You can leave at any time from this tab, and other players are then asked " ..
      "to take you off their leaderboard."),
  }
  local chest = join:CreateTexture(nil, "ARTWORK"); chest:SetSize(36, 36); chest:SetPoint("TOPLEFT", 16, -350)
  local heroic = TCF.CHEST_BY_KEY and TCF.CHEST_BY_KEY.heroic
  chest:SetTexture(TCF.Icon(heroic and heroic.icon or "INV_Box_04"))
  local reward = Text(join, "GameFontNormal", nil, "LEFT"); reward:SetPoint("LEFT", chest, "RIGHT", 10, 0); reward:SetWidth(470)
  page.joinReward = reward
  local joinBtn = Button(join, "Join the leaderboard", 260, 38, function()
    TCF:SetShareProgress(true)
    win.lbSection, win.lbScroll = "taps", 0
    TCF:PlaySound("click")
    page:Refresh()
  end)
  joinBtn:SetPoint("TOP", 0, -406)
  if joinBtn.SetNormalFontObject then
    joinBtn:SetNormalFontObject("GameFontNormalLarge"); joinBtn:SetHighlightFontObject("GameFontHighlightLarge")
  end
  page.joinBtn = joinBtn
  Tip(joinBtn, function(tt)
    tt:AddLine("Join the leaderboard", 1, 0.82, 0)
    tt:AddLine("Turns on Share my cat's progress for your account. You can leave again at any time.", 1, 1, 1, true)
  end)

  ------------------------------------------------ joined: the board
  local board = CreateFrame("Frame", nil, page); board:SetAllPoints()
  page.board = board
  local function T(font, parent) return (parent or board):CreateFontString(nil, "OVERLAY", font) end
  page.title = Text(board, "GameFontNormalLarge", nil, "LEFT"); page.title:SetPoint("TOPLEFT", 16, -14)
  page.count = Text(board, "GameFontDisableSmall", nil, "RIGHT"); page.count:SetPoint("TOPRIGHT", -96, -18)
  local leaveBtn = Button(board, "Leave", 70, 20, function() confirming = true; TCF:PlaySound("click"); page:Refresh() end)
  leaveBtn:SetPoint("TOPRIGHT", -16, -12)
  page.leaveBtn = leaveBtn
  Tip(leaveBtn, function(tt)
    tt:AddLine("Leave the leaderboard", 1, 0.82, 0)
    tt:AddLine("Stops sharing your cat's progress and asks other players to take you off their leaderboard. Asks first.", 1, 1, 1, true)
  end)

  -- sections, like small tabs
  page.sectionBtns = {}
  for i, s in ipairs(SECTIONS) do
    local b = Button(board, s[2], 110, 22, function()
      win.lbSection, win.lbScroll = s[1], 0
      TCF:PlaySound("click"); page:Refresh()
    end)
    b:SetPoint("TOPLEFT", 16 + (i - 1) * 114, -40)
    b.section = s[1]
    page.sectionBtns[i] = b
  end

  -- the short confirm for Leave, in place of the section buttons
  local confirm = CreateFrame("Frame", nil, board); confirm:SetSize(528, 24); confirm:SetPoint("TOPLEFT", 16, -39)
  page.confirm = confirm
  local cText = Text(confirm, "GameFontHighlight", "Leave the leaderboard? Others are asked to take you off.", "LEFT")
  cText:SetPoint("LEFT", 0, 0)
  page.confirmText = cText
  local cYes = Button(confirm, "Leave", 80, 22, function()
    confirming = false
    TCF:SetShareProgress(false)
    TCF:PlaySound("click"); page:Refresh()
  end)
  cYes:SetPoint("RIGHT", -86, 0)
  local cNo = Button(confirm, "Stay", 80, 22, function() confirming = false; TCF:PlaySound("click"); page:Refresh() end)
  cNo:SetPoint("RIGHT", 0, 0)
  page.confirmYes, page.confirmNo = cYes, cNo
  -- leaving the tab (or closing the window) drops the question; it isn't waiting when you come back
  page:HookScript("OnHide", function() confirming = false end)

  -- the row under the sections: class icons, profession icons, or a hint
  local subLabel = Text(board, "GameFontNormal", nil, "LEFT")
  page.subLabel = subLabel
  local function IconButton(i, setIcon, onClick, tip)
    local b = CreateFrame("Button", nil, board)
    b:SetSize(26, 26); b:SetPoint("TOPLEFT", 16 + (i - 1) * 30, -70)
    local t = b:CreateTexture(nil, "ARTWORK"); t:SetAllPoints(); setIcon(t)
    b.sel = b:CreateTexture(nil, "OVERLAY"); b.sel:SetPoint("TOPLEFT", -5, 5); b.sel:SetPoint("BOTTOMRIGHT", 5, -5)
    b.sel:SetTexture("Interface\\Buttons\\CheckButtonHilight"); b.sel:SetBlendMode("ADD")
    b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    b:SetScript("OnClick", function() onClick(); win.lbScroll = 0; TCF:PlaySound("click"); page:Refresh() end)
    Tip(b, tip)
    return b
  end
  page.classBtns = {}
  for i, cl in ipairs(TCF.CLASSES) do
    local b = IconButton(i, function(t) TCF.SetClassIcon(t, cl.key) end, function() win.lbClass = cl.key end, function(tt)
      tt:AddLine(cl.name, cl.color[1], cl.color[2], cl.color[3])
      tt:AddLine("Players' " .. cl.name .. " cats by cat level. Ties go to the player with more taps.", 1, 1, 1, true)
    end)
    b.class = cl.key
    page.classBtns[i] = b
  end
  page.profBtns = {}
  for i, pb in ipairs(TCF.LB_PROF_BOARDS) do
    local b = IconButton(i, function(t) t:SetTexture(TCF.Icon(pb[4])); t:SetTexCoord(0.07, 0.93, 0.07, 0.93) end,
      function() win.lbProf = pb[1] end, function(tt)
        tt:AddLine(pb[2], 1, 0.82, 0)
        tt:AddLine(pb[1] == "gold" and "Trade Gold earned in total by all of a player's cats." or
          ("The best " .. pb[2] .. " skill of any of a player's cats."), 1, 1, 1, true)
      end)
    b.board = pb[1]
    page.profBtns[i] = b
  end

  -- column headings (buttons where they sort) and the rows
  page.heads = {}
  for i = 1, MAX_COLS do
    local h = CreateFrame("Button", nil, board)
    h.label = T("GameFontNormalSmall", h); h.label:SetPoint("LEFT", 0, 0); h.label:SetJustifyH("LEFT")
    h:SetScript("OnClick", function(s)
      if win.lbSection ~= "taps" or not s.sortKey then return end
      win.lbSort, win.lbScroll = s.sortKey, 0
      TCF:PlaySound("click"); page:Refresh()
    end)
    Tip(h, function(tt, s)
      if s.sortKey then tt:AddLine("Sort by " .. TCF.LB_SORTS[s.sortKey][2]:lower(), 1, 0.82, 0)
      else tt:AddLine(s.label:GetText() or "", 1, 0.82, 0) end
    end)
    page.heads[i] = h
  end
  page.rows = {}
  for r = 1, ROWS do
    local row = { cells = {} }
    local y = -HEAD_Y - r * ROW_H
    row.y = y
    row.hl = board:CreateTexture(nil, "BACKGROUND")
    row.hl:SetPoint("TOPLEFT", 12, y + 2); row.hl:SetSize(536, ROW_H)
    row.hl:SetColorTexture(1, 0.82, 0.2, 0.18)
    for i = 1, MAX_COLS do
      local t = T("GameFontHighlightSmall"); t:SetJustifyH("LEFT")
      if t.SetWordWrap then t:SetWordWrap(false) end
      row.cells[i] = t
    end
    page.rows[r] = row
  end

  page.empty = T("GameFontHighlight"); page.empty:SetPoint("TOP", 0, -HEAD_Y - 2 * ROW_H - 18); page.empty:SetWidth(480)
  if page.empty.SetJustifyH then page.empty:SetJustifyH("CENTER") end
  page.note = T("GameFontDisableSmall"); page.note:SetPoint("BOTTOMLEFT", 16, 12); page.note:SetWidth(528); page.note:SetJustifyH("LEFT")

  page:EnableMouseWheel(true)
  page:SetScript("OnMouseWheel", function(_, d)
    if not TCF.LeaderboardOptedIn() then return end
    win.lbScroll = max(0, (win.lbScroll or 0) - d)
    page:Refresh()
  end)

  -- puts the headings and cells of a section's columns in place; the rest hide
  local shownCols
  local function layout(cols)
    if shownCols == cols then return end
    shownCols = cols
    for i, h in ipairs(page.heads) do
      local c = cols[i]
      if c then
        h:ClearAllPoints(); h:SetPoint("TOPLEFT", board, "TOPLEFT", X0 + c[2], -HEAD_Y); h:SetSize(c[3], 16)
      end
      h.col = c
    end
    for _, row in ipairs(page.rows) do
      for i, t in ipairs(row.cells) do
        local c = cols[i]
        if c then t:ClearAllPoints(); t:SetPoint("TOPLEFT", board, "TOPLEFT", X0 + c[2], row.y); t:SetWidth(c[3]) end
      end
    end
  end

  local function cellText(e, field, sec, sub, st)
    if field == "rank" then return e.rank
    elseif field == "name" then return (TCF.LeaderboardDisplayName(e.n):gsub("|", "||")) .. (e.self and " (you)" or "")
    elseif field == "t" then return TCF.Commas(e.t)
    elseif field == "val" then
      if sec == "prof" and sub == "gold" then return TCF.FormatBig(e.val) end
      return e.val
    elseif field == "playing" then
      local cl = TCF.CLASS_BY_KEY[e.c]
      return cl and (hex(cl.color) .. cl.name .. "|r") or ""
    elseif field == "seen" then return e.self and "now" or TCF.LeaderboardAgo(e.ts, st)
    end
    return e[field]
  end

  local NOTE = "Only players on your realm who joined are listed. You share with them when you are in a party, raid or " ..
    "guild together, and they pass on the players they know. Players not seen for 30 days drop off, and at most " ..
    TCF.LB_MAX_ENTRIES .. " are kept. Scroll with the mouse wheel."
  local SECTION_NOTE = {
    taps = " Taps count all of a player's characters. Click a heading to sort.",
    class = " Ties go to the player with more taps. Players on an older version of the addon only show under the class they play.",
    prof = " Trade Gold counts all of a player's cats, and a skill is the best of any of their cats. Players on an older version of the addon only show under Total taps.",
  }

  -- 1.5.3.3: any error while drawing shows on the page (and once in chat) instead of an empty board
  local drawPage
  function page:Refresh()
    local ok, err = pcall(drawPage, self)
    if not ok then
      board:Show()
      page.empty:SetText("The leaderboard hit an error. Please send this to the developer: " .. tostring(err))
      page.empty:Show()
      if not page.errShown then page.errShown = true; TCF:Print("Leaderboard error: " .. tostring(err), true) end
    end
  end
  function drawPage(page)
    TCF.LeaderboardDirty(true)
    local on = TCF.LeaderboardOptedIn()
    join:SetShown(not on)
    board:SetShown(on)
    if not on then
      confirming = false
      local got = TCF.db.ui.lbSignupChest
      reward:SetText(got and "Your account already got its Heroic Cache for joining." or
        "The first time you join, your cat gets a Heroic Cache in its Treasure Bag.")
      chest:SetDesaturated(got and true or false)
      return
    end
    local sec = win.lbSection
    if sec ~= "class" and sec ~= "prof" then sec = "taps"; win.lbSection = sec end
    win.lbClass = TCF.CLASS_BY_KEY[win.lbClass or ""] and win.lbClass or TCF.db.class
    local sub = sec == "taps" and win.lbSort or sec == "class" and win.lbClass or win.lbProf
    local list = TCF:LeaderboardSection(sec, sub)
    win.lbScroll = max(0, min(win.lbScroll or 0, #list - ROWS))
    page.list = list
    local realm = TCF.LeaderboardRealm()
    page.title:SetText("Realm leaderboard" .. (realm and (" - " .. realm) or ""))
    page.count:SetText(string.format("%d %s", #list, #list == 1 and "player" or "players"))

    -- sections, or the Leave confirm in their place
    for _, b in ipairs(page.sectionBtns) do
      b:SetShown(not confirming)
      if b.section == sec then b:LockHighlight() else b:UnlockHighlight() end
    end
    confirm:SetShown(confirming)
    leaveBtn:SetShown(not confirming)

    -- the row under the sections
    for _, b in ipairs(page.classBtns) do b:SetShown(sec == "class"); b.sel:SetShown(b.class == win.lbClass) end
    for _, b in ipairs(page.profBtns) do b:SetShown(sec == "prof"); b.sel:SetShown(b.board == win.lbProf) end
    subLabel:ClearAllPoints()
    local pbName, pbHead
    for _, pb in ipairs(TCF.LB_PROF_BOARDS) do if pb[1] == win.lbProf then pbName, pbHead = pb[2], pb[3] end end
    if sec == "class" then
      local cl = TCF.CLASS_BY_KEY[win.lbClass]
      subLabel:SetPoint("TOPLEFT", 16 + #page.classBtns * 30 + 6, -76)
      subLabel:SetText(hex(cl.color) .. cl.name .. "|r cats by cat level")
    elseif sec == "prof" then
      subLabel:SetPoint("TOPLEFT", 16 + #page.profBtns * 30 + 6, -76)
      subLabel:SetText(pbHead or "")
    else
      subLabel:SetPoint("TOPLEFT", 16, -76)
      local sortName = win.lbSort == "taps" and "total taps" or TCF.LB_SORTS[win.lbSort][2]:lower()
      subLabel:SetText("Everyone by " .. sortName .. ". Click a heading to sort by another column.")
    end

    -- headings
    local cols = COLS[sec]
    layout(cols)
    for i, h in ipairs(page.heads) do
      local c = cols[i]
      h:SetShown(c ~= nil)
      h.sortKey = c and sec == "taps" and c[4] or nil
      if c then
        local title = c[1]
        if c[5] == "val" and sec == "prof" then title = win.lbProf == "gold" and "Trade Gold" or (pbName or "Skill") end
        h.label:SetText(title)
        if h.sortKey and h.sortKey == win.lbSort then h.label:SetTextColor(1, 1, 1)
        else h.label:SetTextColor(1, 0.82, 0) end
      end
    end

    -- rows
    local st = TCF.LeaderboardServerNow()
    for r, row in ipairs(page.rows) do
      local e = list[r + win.lbScroll]
      for i, cell in ipairs(row.cells) do
        local c = cols[i]
        if e and c then
          cell:SetText(cellText(e, c[5], sec, sub, st))
          if c[5] == "name" then
            local cl = TCF.CLASS_BY_KEY[e.c]
            if cl then cell:SetTextColor(cl.color[1], cl.color[2], cl.color[3]) end
          else
            cell:SetTextColor(1, 1, 1)
          end
          cell:Show()
        else
          cell:Hide()
        end
      end
      row.hl:SetShown(e and e.self and true or false)
      row.entry = e
    end

    local others = #list - ((function() for _, e in ipairs(list) do if e.self then return 1 end end return 0 end)())
    if others <= 0 then
      if sec == "class" then
        page.empty:SetText("No other players with a " .. TCF.CLASS_BY_KEY[win.lbClass].name .. " cat above level 1 yet.")
      elseif sec == "prof" then
        page.empty:SetText(win.lbProf == "gold" and "No other players with Trade Gold yet." or
          ("No other players with " .. (pbName or "this") .. " skill yet."))
      else
        page.empty:SetText("No other players yet. Group up or be in a guild with friends who joined, " ..
          "and you show up on each other's leaderboard.")
      end
    end
    page.empty:SetShown(others <= 0)
    page.note:SetText(NOTE .. (SECTION_NOTE[sec] or ""))
  end

  local acc = 0
  page:SetScript("OnUpdate", function(_, e)
    acc = acc + e
    if acc >= 5 or (TCF.LeaderboardDirty() and acc >= 0.5) then acc = 0; page:Refresh() end
  end)

  -- the window's refresh: a full one draws the page; the light one (every tap) leaves it to OnUpdate
  return function(light)
    if light then return end
    page:Refresh()
  end
end
