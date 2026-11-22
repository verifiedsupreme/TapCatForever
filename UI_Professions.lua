-- TapCatForever: Professions page. The tab row is { your class's main profession, Herbalism,
-- First Aid, Fishing, Cooking } (TCF:ProfList()). The main profession is one of three families
-- (Mining, Skinning, Tailoring; see TCF.FAMILIES in Professions.lua) and has three views: its
-- gathering spots (Veins / Hunting Grounds / Cloth Spots), Upgrades, and its crafting skill
-- (Blacksmithing / Leatherworking / Tailoring). Every name, verb and tool comes from
-- TCF.FAMILIES, never hard-coded. Herbalism (garden), First Aid (bandages), Fishing (the dock
-- scene with the bobber) and Cooking (pot) have their own main view plus Crafting and Renown.
--
-- Every class's cat has its own trade (Trade Gold, Renown, spots, skills, materials): the page
-- always shows the current class's, read fresh from TCF:ProfState() on every refresh.
--
-- Visibility rule: a view is shown or hidden only when the selected profession, view or
-- family changes (see refresh at the bottom). Re-showing views on every refresh tick made
-- buttons stop taking clicks before.
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

-- change a region's visibility only when it really changes
local function vis(f, want)
  want = want and true or false
  if (f:IsShown() and true or false) ~= want then f:SetShown(want) end
end

-- the hand tool's icon per family (FAMILIES[fam].toolIcon wins when the engine sets one)
local TOOL_ICON = { mining = "INV_Pick_02", skinning = "INV_Weapon_ShortBlade_05", cloth = "Trade_Tailoring" }
local function toolIcon(fam) local f = TCF.FAMILIES[fam]; return (f and f.toolIcon) or TOOL_ICON[fam] or "INV_Pick_02" end

-- skill-up colour of a recipe, spot, seed or bandage, WoW style (TCF:ProfSkillUp's own bands)
local function skillColor(cur, need) return (TCF.SkillUpColor(cur, need)) end
-- one tooltip line: "Still teaches you: often", in its colour
local function addTeachLine(tt, cur, need)
  local line, col = TCF.SkillUpLine(cur, need)
  tt:AddLine(col .. line .. "|r")
end
TCF.UI.AddTeachLine = addTeachLine

-- where the pole tip of the cartoon fishing pole sits on the cat's 512-unit canvas
-- (Art/v/k_wpn_fishpole_f, main hand, resting paw lifted by 44 units)
local POLE_TIP_X, POLE_TIP_Y, PAW_LIFT = 470, 108, 44

-- 1.6: the round Professions button in the main window's header, next to the Casino (coin) and
-- Settings (cog) icons. It shows the cat's own profession (Mining, Skinning or Tailoring) and opens
-- the Professions tab. A glitched spot (the patch secret) makes it flicker purple.
function TCF.UI.ProfQuickButton(win, after, open)
  local b = CreateFrame("Button", nil, win)
  b:SetSize(26, 26)
  b:SetPoint("LEFT", after, "RIGHT", 6, 0)
  b.ic = b:CreateTexture(nil, "ARTWORK"); b.ic:SetAllPoints(); b.ic:SetTexCoord(0.07, 0.93, 0.07, 0.93)
  b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  b.sel = b:CreateTexture(nil, "OVERLAY"); b.sel:SetPoint("TOPLEFT", -3, 3); b.sel:SetPoint("BOTTOMRIGHT", 3, -3)
  b.sel:SetTexture("Interface\\Buttons\\CheckButtonHilight"); b.sel:SetBlendMode("ADD"); b.sel:Hide()
  local function update()
    local f = TCF.db and TCF.FAMILIES[TCF:MainProf()]
    local icon = f and f.icon or "Trade_Mining"
    if b.icon ~= icon then b.icon = icon; b.ic:SetTexture(TCF.Icon(icon)) end
    local onTab = win.tab and win.tabNames and win.tabNames[win.tab] == "Professions"
    if (b.sel:IsShown() and true or false) ~= (onTab and true or false) then b.sel:SetShown(onTab) end
    local g = TCF.Glitch and TCF:Glitch()
    b.ic:SetVertexColor(1, g and (0.5 + 0.5 * math.sin(GetTime() * 10)) or 1, 1)
  end
  local acc = 0
  b:SetScript("OnUpdate", function(_, e) acc = acc + e; if acc > 0.1 then acc = 0; update() end end)
  b:SetScript("OnShow", update)
  b:SetScript("OnClick", function() open(); TCF:PlaySound("click"); update() end)
  TCF.UI.Tip(b, function(tt)
    local f = TCF.FAMILIES[TCF:MainProf()]
    tt:AddLine("Professions", 1, 0.82, 0)
    -- only what this cat has learned (the gathering skill's own name, so cloth cats don't read "Tailoring" twice)
    local have, later = { f.skillName or f.name }, {}
    if f.craftName and f.craftName ~= have[1] then have[#have + 1] = f.craftName end
    for _, p in ipairs(TCF.PROFESSIONS) do
      if not p.family then
        local list = TCF:ProfUnlocked(p.key) and have or later
        list[#list + 1] = p.name
      end
    end
    local function join(t) return #t > 1 and (table.concat(t, ", ", 1, #t - 1) .. " and " .. t[#t]) or (t[1] or "") end
    tt:AddLine("Your " .. join(have) .. ".", 1, 1, 1, true)
    if #later > 0 then tt:AddLine("Learned later: " .. join(later) .. ".", 0.7, 0.7, 0.7, true) end
  end)
  update()
  return b
end

TCF.UI.Builders.professions = function(page, win)
  local U = TCF.UI
  local Text, Button, Tip, Panel = U.Text, U.Button, U.Tip, U.Panel
  win.profView = win.profView or "main"

  -- the current class's family key and table
  local function FAM() return TCF:MainProf() end
  local function FT() return TCF.FAMILIES[TCF:MainProf()] end
  local function className() return (TCF.CLASS_BY_KEY[TCF.db.class] or {}).name or "" end
  local PER_CLASS = "Each class has its own Trade Gold and professions."

  ------------------------------------------------ header
  local ptabs = {}
  for i = 1, 5 do
    local b = IconButton(page, 30)
    b:SetPoint("TOPLEFT", 12 + (i - 1) * 36, -10)
    b:SetScript("OnClick", function(s)
      if not s.prof then return end
      win.profSel = s.prof.key; win.profView = "main"; TCF:PlaySound("click"); win:Refresh()
    end)
    Tip(b, function(tt, s)
      local p = (s or b).prof
      if not p then return end
      tt:AddLine(p.name, 1, 0.82, 0)
      local f = TCF.FAMILIES[p.key]
      if f then
        tt:AddLine(string.format("Your %s cat's profession: gather from %s and craft with %s.",
          (TCF.CLASS_BY_KEY[TCF.db.class] or {}).name or "", f.spotsTitle:lower(), f.craftName), 1, 1, 1, true)
      elseif (p.gold or 0) > 0 then
        local have, need, done = TCF:ProfUnlockProgress(p.key)
        if done then tt:AddLine("Learned", 1, 1, 1)
        else
          tt:AddLine(string.format("Unlocks when this cat has earned %s Trade Gold.", TCF.GoldStr(need)), 1, 1, 1, true)
          tt:AddLine(string.format("So far: %s (%d%%)", TCF.GoldStr(have), min(99, floor(100 * have / need))), 0.8, 0.8, 0.8)
        end
      end
      tt:AddLine(PER_CLASS, 0.7, 0.7, 0.7, true)
    end)
    ptabs[i] = b
  end
  local profName = Text(page, "GameFontNormalLarge", nil, "LEFT"); profName:SetPoint("TOPLEFT", 200, -10)
  local skillBar = Bar(page, 160, 12, 0.2, 0.5, 0.95); skillBar:SetPoint("TOPLEFT", 200, -30)
  local goldText = Text(page, "GameFontHighlightLarge", nil, "RIGHT"); goldText:SetPoint("TOPRIGHT", -14, -10)
  local renownText = Text(page, "GameFontHighlightSmall", nil, "RIGHT"); renownText:SetPoint("TOPRIGHT", -14, -30)
  -- hover the gold and Renown for whose they are
  local goldHover = CreateFrame("Frame", nil, page); goldHover:SetSize(180, 36); goldHover:SetPoint("TOPRIGHT", -10, -6)
  goldHover:EnableMouse(true)
  Tip(goldHover, function(tt)
    local s = TCF:ProfState()
    tt:AddLine(string.format("Your %s cat's Trade Gold", className()), 1, 0.82, 0)
    tt:AddLine(string.format("%s Trade Gold, Renown %d (+%d%% gold).", TCF.GoldStr(s.gold), s.renown, s.renown * 2), 1, 1, 1, true)
    tt:AddLine(string.format("Trade Gold earned in total: %s. New professions unlock as this grows.", TCF.GoldStr(s.lifetime)), 1, 1, 1, true)
    tt:AddLine(PER_CLASS .. " Your other cats' helpers keep working while you play this one, and what they earn stays with them.", 0.7, 0.7, 0.7, true)
  end)

  local vbtns = {}
  for i, key in ipairs({ "main", "upg", "craft", "renown" }) do
    local b = Button(page, "", 108, 22, function() win.profView = key; TCF:PlaySound("click"); win:Refresh() end)
    b:SetPoint("TOPLEFT", 12 + (i - 1) * 111, -48)
    b.key = key
    vbtns[i] = b
  end
  vbtns[2]:SetText("Upgrades"); vbtns[4]:SetText("Renown")
  local buyMode = Button(page, "Buy x1", 76, 22, function()
    local s = TCF:ProfState()
    local modes = { 1, 10, 100, "max" }
    local idx = 1
    for k, m in ipairs(modes) do if m == s.buy then idx = k end end
    s.buy = modes[idx % #modes + 1]
    win:Refresh()
  end)
  buyMode:SetPoint("TOPRIGHT", -14, -48)
  Tip(buyMode, function(tt)
    tt:AddLine("How many to buy", 1, 0.82, 0)
    tt:AddLine("Click to switch between buying 1, 10, 100 or as many as you can afford with each Buy button.", 1, 1, 1, true)
  end)

  -- a label that would run past its button (or set width) switches to the small font; measured in
  -- the client's own font, so nothing changes where it already fits
  -- the text's full width on one line (GetUnboundedStringWidth where the client has it)
  local function textWidth(fs)
    if not fs then return nil end
    local w = fs.GetUnboundedStringWidth and fs:GetUnboundedStringWidth()
    if type(w) ~= "number" then w = fs.GetStringWidth and fs:GetStringWidth() end
    return w
  end
  local function fitText(obj)
    local btn = obj.GetFontString and true or false
    local fs = btn and obj:GetFontString() or obj
    local w = textWidth(fs)
    local room = obj.GetWidth and obj:GetWidth()
    if type(w) ~= "number" or type(room) ~= "number" or room <= 0 then return end
    if obj.fitSmall then w = w * 1.2 end   -- the normal font is about 12/10 of the small one
    local small = w > room - (btn and 14 or 2)
    if small == (obj.fitSmall or false) then return end
    obj.fitSmall = small
    if btn then
      obj:SetNormalFontObject(small and "GameFontNormalSmall" or "GameFontNormal")
      obj:SetHighlightFontObject(small and "GameFontHighlightSmall" or "GameFontHighlight")
      obj:SetDisabledFontObject(small and "GameFontDisableSmall" or "GameFontDisable")
    else
      obj:SetFontObject(small and "GameFontNormalSmall" or "GameFontNormal")
    end
  end
  local function View() local f = CreateFrame("Frame", nil, page); f:SetPoint("TOPLEFT", 0, -76); f:SetPoint("BOTTOMRIGHT"); f:Hide(); return f end

  ------------------------------------------------ locked
  local locked = View()
  local lockText = Text(locked, "GameFontNormalLarge"); lockText:SetPoint("CENTER", 0, 40); lockText:SetWidth(480)

  ------------------------------------------------ main profession: gathering spots
  -- Veins (ore icon), Hunting Grounds and Cloth Spots (the creature's 3D model in its box)
  -- 1.6: up to 9 spots per family in 6 rows; the mouse wheel (or the arrows below) scrolls them.
  -- Each row shows spot r.spot (set in refreshSpots from win.spotScroll).
  local spotView = View()
  local rows = {}
  local BOX_W, BOX_H = 92, 54
  local SPOT_ROWS = 6
  for i = 1, SPOT_ROWS do
    local r = Panel(spotView, 532, 58, 0.85); r:SetPoint("TOP", 0, -(i - 1) * 61)
    r.spot = i
    -- the picture box: click it to run one cycle
    r.box = CreateFrame("Button", nil, r, U.BT); r.box:SetSize(BOX_W, BOX_H); r.box:SetPoint("LEFT", 2, 0)
    if r.box.SetBackdrop then
      r.box:SetBackdrop(U.BACKDROP_PANEL); r.box:SetBackdropColor(0.10, 0.12, 0.16, 1); r.box:SetBackdropBorderColor(0.45, 0.40, 0.55, 1)
    end
    r.box:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    r.box:SetScript("OnClick", function() TCF:RunOp(FAM(), r.spot); TCF:PlaySound("click"); win:Refresh() end)
    r.icon = r.box:CreateTexture(nil, "ARTWORK"); r.icon:SetSize(44, 44); r.icon:SetPoint("CENTER")
    -- the model fills the box (inside its border) and is pulled back so the whole creature fits:
    -- WoW cuts a model off at its frame's edges
    r.model = CreateFrame("PlayerModel", nil, r.box)
    r.model:SetPoint("TOPLEFT", 3, -3); r.model:SetPoint("BOTTOMRIGHT", -3, 3)
    if r.model.EnableMouse then r.model:EnableMouse(false) end
    r.model:Hide()
    -- material icon, count and the "click me" glow sit above the model
    r.cover = CreateFrame("Frame", nil, r.box); r.cover:SetAllPoints(r.box)
    if r.cover.SetFrameLevel and r.box.GetFrameLevel then pcall(r.cover.SetFrameLevel, r.cover, (r.box:GetFrameLevel() or 1) + 5) end
    r.mat = r.cover:CreateTexture(nil, "OVERLAY"); r.mat:SetSize(18, 18); r.mat:SetPoint("BOTTOMLEFT", 4, 4); r.mat:Hide()
    r.count = Text(r.cover, "NumberFontNormal", nil, "RIGHT"); r.count:SetPoint("BOTTOMRIGHT", -4, 4)
    r.sel = r.cover:CreateTexture(nil, "OVERLAY"); r.sel:SetPoint("TOPLEFT", -4, 4); r.sel:SetPoint("BOTTOMRIGHT", 4, -4)
    r.sel:SetTexture("Interface\\Buttons\\CheckButtonHilight"); r.sel:SetBlendMode("ADD"); r.sel:Hide()
    Tip(r.box, function(tt)
      local f = FT()
      local i = r.spot
      local o, st = f.ops[i], TCF:ProfState().ops[FAM()][i]
      tt:AddLine(o[1], 1, 0.82, 0)
      local open, why = TCF:SpotUnlocked(FAM(), i)
      if not open then tt:AddLine(why, 1, 0.5, 0.3, true); tt:AddLine("Gives " .. o[3] .. ".", 0.8, 0.8, 0.8); return end
      local g = TCF:Glitch()
      if g and g.fam == FAM() and g.i == i then
        tt:AddLine(string.format("Something is wrong with it. Work it by hand while it lasts (%ds).", TCF:GlitchLeft()), 0.8, 0.4, 1, true)
      end
      tt:AddLine(string.format("Gives %s. You own %d.", o[3], st.n), 1, 1, 1)
      if TCF.MatUsedInRecipe and not TCF.MatUsedInRecipe(o[2]) then tt:AddLine(o[3] .. " is not used in any recipe yet.", 0.7, 0.7, 0.7, true) end
      addTeachLine(tt, TCF:ProfSkill(FAM()), TCF.SpotDifficulty(i))
      if st.n > 0 and not st.mgr then tt:AddLine(string.format("Click to %s one cycle.", f.verb:lower()), 0, 1, 0) end
      if st.mgr then tt:AddLine(string.format("Your %s works it on its own.", f.hire:lower()), 0.6, 1, 0.6) end
    end)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("TOPLEFT", r.box, "TOPRIGHT", 8, -2); r.name:SetWidth(258)
    if r.name.SetWordWrap then r.name:SetWordWrap(false) end
    r.bar = Bar(r, 258, 16, 0.25, 0.75, 0.3); r.bar:SetPoint("LEFT", r.box, "RIGHT", 8, 0)
    r.bar:EnableMouse(true); r.bar:SetScript("OnMouseUp", function() TCF:RunOp(FAM(), r.spot); win:Refresh() end)
    r.info = Text(r, "GameFontDisableSmall", nil, "LEFT"); r.info:SetPoint("BOTTOMLEFT", r.box, "BOTTOMRIGHT", 8, 2); r.info:SetWidth(258)
    if r.info.SetWordWrap then r.info:SetWordWrap(false) end
    -- the hand tool: click to gather by hand
    r.pick = IconButton(r, 40); r.pick:SetPoint("RIGHT", -124, 0)
    -- a little "+gold +material" pop-up rises from the tool on every click
    r.pop = Text(r, "GameFontNormal"); r.pop:SetPoint("BOTTOM", r.pick, "TOP", 0, 0); r.pop:Hide()
    r.pickLabel = Text(r, "GameFontDisableSmall", "By hand"); r.pickLabel:SetPoint("TOP", r.pick, "BOTTOM", 0, -1)
    r.pick:SetScript("OnUpdate", function(b, e)
      if not r.popT then return end
      r.popT = r.popT - e
      if r.popT <= 0 then r.popT = nil; r.pop:Hide(); b.tex:ClearAllPoints(); b.tex:SetAllPoints(); return end
      local t = 1 - r.popT / 0.9
      r.pop:ClearAllPoints(); r.pop:SetPoint("BOTTOM", b, "TOP", 0, t * 22); r.pop:SetAlpha(t < 0.6 and 1 or (1 - t) / 0.4)
      local bump = t < 0.15 and 46 or 40
      b.tex:ClearAllPoints(); b.tex:SetPoint("CENTER"); b.tex:SetSize(bump, bump)
    end)
    r.pick.cd = CreateFrame("Cooldown", nil, r.pick, "CooldownFrameTemplate"); r.pick.cd:SetAllPoints()
    r.pick:SetScript("OnClick", function()
      local fam, i = FAM(), r.spot
      if TCF:GatherClick(fam, i) then
        -- one tool per family: every spot's button shows the same cooldown
        for _, row in ipairs(rows) do if row.pick.cd.SetCooldown then row.pick.cd:SetCooldown(GetTime(), TCF:ToolCooldown(fam)) end end
        local mf = TCF.FAMILIES[TCF.lastMineFamily or fam] or TCF.FAMILIES[fam]
        local got = TCF.lastMineOre or 0
        r.pop:SetText(string.format("|cffffd100+%s|r%s", TCF.GoldStr(TCF.lastMineGold or 0, 10),
          got > 0 and string.format("  |cffcccccc+%d %s|r", got, mf.ops[i][3]) or ""))
        r.pop:Show(); r.popT = 0.9
        TCF:PlaySound("click")
      end
    end)
    Tip(r.pick, function(tt)
      local fam, f, i = FAM(), FT(), r.spot
      tt:AddLine(TCF:ToolName(fam), 1, 0.82, 0)
      -- show what a click really pays against a full cycle (the first spot's starter floor can beat the share)
      local cycle = TCF:OpRevenue(fam, i)
      local gold = TCF:ToolGold(fam, i)
      local share = cycle > 0 and gold / cycle or TCF:ToolCycleShare(fam, i)
      local rolls = TCF:ToolRolls(fam)
      tt:AddLine(string.format("Click to %s %s by hand: %s per click (%d%% of a full cycle of all your %s here) and a %d%% chance of %s%s.",
        f.verb:lower(), f.ops[i][1], TCF.GoldStr(gold), floor(share * 100 + 0.5), f.spotNounPlural, TCF.PICK_ORE_CHANCE * 100,
        f.matNoun, rolls > 1 and (" (x" .. rolls .. " rolls)") or ""), 1, 1, 1, true)
      tt:AddLine(string.format("One click every %.2fs.", TCF:ToolCooldown(fam)), 0.7, 0.7, 0.7)
      addTeachLine(tt, TCF:ProfSkill(fam), TCF.SpotDifficulty(i))
      tt:AddLine(string.format("Upgrade your %s with the button below the %s.", f.toolNoun:lower(), f.spotNounPlural), 0.7, 0.7, 0.7, true)
    end)
    r.buy = Button(r, "Buy", 112, 22, function() TCF:BuyOp(FAM(), r.spot, TCF:ProfState().buy); win:Refresh() end)
    r.buy:SetPoint("TOPRIGHT", -6, -6)
    Tip(r.buy, function(tt)
      local f = FT()
      tt:AddLine("Buy " .. f.ops[r.spot][1], 1, 0.82, 0)
      local open, why = TCF:SpotUnlocked(FAM(), r.spot)
      if not open then tt:AddLine(why, 1, 0.5, 0.3, true) end
      tt:AddLine("Each one you own adds to the gold of every cycle here. Owning 25, 50, 100 and more makes the cycle twice as fast each time.", 1, 1, 1, true)
    end)
    r.mgr = Button(r, "", 112, 20, function() TCF:HireForeman(FAM(), r.spot); win:Refresh() end)
    r.mgr:SetPoint("BOTTOMRIGHT", -6, 6)
    Tip(r.mgr, function(tt)
      local f = FT()
      tt:AddLine("Hire a " .. f.hire:lower(), 1, 0.82, 0)
      tt:AddLine(f.hireDesc or "Works this spot automatically, forever, even offline (up to 24 hours).", 1, 1, 1, true)
    end)
    rows[i] = r
  end
  -- one hand tool for every spot of the family, upgraded forever
  local toolBtn = Button(spotView, "", 196, 24, function() TCF:UpgradeTool(FAM()); win:Refresh() end)
  toolBtn:SetPoint("TOPLEFT", 14, -6 * 61 - 2)
  -- 1.6 Hand speed: its own upgrade, kept when the business is sold
  local speedBtn = Button(spotView, "", 180, 24, function() if TCF:UpgradeSpeed(FAM()) then TCF:PlaySound("buy") end; win:Refresh() end)
  speedBtn:SetPoint("LEFT", toolBtn, "RIGHT", 6, 0)
  Tip(speedBtn, function(tt)
    local fam, f = FAM(), FT()
    local lvl = TCF:SpeedLevel(fam)
    tt:AddLine(string.format("Hand speed (level %d of %d)", lvl, TCF.SPEED_MAX), 1, 0.82, 0)
    tt:AddLine(string.format("You work faster by hand on every %s: one click every %.2fs (%.1f a second).",
      f.spotNoun, TCF:ToolCooldown(fam), TCF:ClicksPerSecond(fam)), 1, 1, 1, true)
    local cost = TCF:SpeedCost(fam)
    if cost then
      tt:AddLine(string.format("Next level: one click every %.2fs (%.1f a second) for %s.", TCF:ToolCooldown(fam, nil, lvl + 1),
        TCF:ClicksPerSecond(fam, nil, lvl + 1), TCF.GoldStr(cost)), 0.2, 1, 0.2, true)
    else tt:AddLine("Fully upgraded.", 0.2, 1, 0.2) end
    tt:AddLine(string.format("Each level costs a lot more than the last. Upgrading your %s also shortens the click a little. With a well upgraded %s, clicks can get down to 0.25s.", f.toolNoun:lower(), f.toolNoun:lower()), 0.7, 0.7, 0.7, true)
    tt:AddLine("Kept when you sell the business.", 1, 0.82, 0, true)
  end)
  local spotHint = Text(spotView, "GameFontDisableSmall", nil, "LEFT")
  spotHint:SetPoint("TOPLEFT", toolBtn, "BOTTOMLEFT", 2, -4); spotHint:SetWidth(520)
  Tip(toolBtn, function(tt)
    local fam, f = FAM(), FT()
    tt:AddLine("Upgrade your " .. f.toolNoun:lower(), 1, 0.82, 0)
    tt:AddLine(string.format("%s -> Lv %d: each click is worth 15%% more of a %s's cycle, on every %s.", TCF:ToolName(fam), TCF:ToolLevel(fam) + 1,
      f.spotNoun, f.spotNoun), 1, 1, 1, true)
    tt:AddLine(string.format("Every 15 levels also adds another roll for %s. Click cooldown: %.2fs (shortens a little each level, down to 0.75s; Hand speed shortens it more).", f.matNoun,
      TCF:ToolCooldown(fam)), 0.7, 0.7, 0.7, true)
  end)

  -- 3D creature models for Hunting Grounds and Cloth Spots (set when the view or family changes)
  local function setSpotPicture(r, o)
    local id = o[5]
    if id and id > 0 then
      r.icon:Hide()
      r.mat:SetTexture(TCF.Icon(o[4])); r.mat:Show()
      -- set again every time the view opens: a model can come back empty after its frame was hidden
      r.modelId = id
      if r.model.ClearModel then pcall(r.model.ClearModel, r.model) end
      vis(r.model, true)
      local ok = pcall(r.model.SetDisplayInfo, r.model, id)
      pcall(r.model.SetPortraitZoom, r.model, 0)
      pcall(r.model.SetCamDistanceScale, r.model, 1.9)
      pcall(r.model.SetFacing, r.model, -0.6)
      pcall(r.model.SetAnimation, r.model, 0)
      r.modelCheck = ok and 0.6 or 0
    else
      -- veins: the ore itself
      r.modelId = nil; r.modelCheck = nil
      if r.model.ClearModel then pcall(r.model.ClearModel, r.model) end
      vis(r.model, false); vis(r.mat, false)
      r.icon:SetTexture(TCF.Icon(o[4])); r.icon:Show()
    end
  end
  -- a display ID that loads no model falls back to the material's picture
  spotView:SetScript("OnUpdate", function(_, e)
    for _, r in ipairs(rows) do
      if r.modelCheck then
        r.modelCheck = r.modelCheck - e
        if r.modelCheck <= 0 then
          r.modelCheck = nil
          local okFile, file = pcall(r.model.GetModelFileID, r.model)
          if not okFile or not file then
            r.model:Hide(); r.mat:Hide()
            r.icon:SetTexture(r.mat:GetTexture() or TCF.Icon("INV_Misc_QuestionMark")); r.icon:Show()
          end
        end
      end
    end
  end)
  -- which spots the rows show: rows start at spot win.spotScroll + 1
  local function spotTotal() return TCF:SpotCount() end
  local function placeRows(fam, force)
    local f = TCF.FAMILIES[fam]
    local off = min(max(0, win.spotScroll or 0), max(0, spotTotal() - SPOT_ROWS))
    win.spotScroll = off
    for k, r in ipairs(rows) do
      local i = off + k
      if force or r.spot ~= i or r.spotFam ~= fam then
        r.spot, r.spotFam = i, fam
        setSpotPicture(r, f.ops[i]); r.pick.tex:SetTexture(TCF.Icon(toolIcon(fam)))
        r.popT = nil; r.pop:Hide()
      end
    end
  end
  local spotPage = Text(spotView, "GameFontHighlightSmall", nil, "CENTER")
  local spotUp = Button(spotView, "<", 26, 22, function() win.spotScroll = (win.spotScroll or 0) - 3; TCF:PlaySound("click"); win:Refresh() end)
  local spotDown = Button(spotView, ">", 26, 22, function() win.spotScroll = (win.spotScroll or 0) + 3; TCF:PlaySound("click"); win:Refresh() end)
  spotDown:SetPoint("TOPRIGHT", spotView, "TOPRIGHT", -14, -6 * 61 - 2)
  spotPage:SetPoint("RIGHT", spotDown, "LEFT", -4, 0); spotPage:SetWidth(64)
  spotUp:SetPoint("RIGHT", spotPage, "LEFT", -4, 0)
  for _, b in ipairs({ spotUp, spotDown }) do
    Tip(b, function(tt)
      tt:AddLine("More " .. FT().spotNounPlural, 1, 0.82, 0)
      tt:AddLine("Scroll with the mouse wheel too. The later ones open up as your business grows.", 1, 1, 1, true)
    end)
  end
  spotView:EnableMouseWheel(true)
  spotView:SetScript("OnMouseWheel", function(_, d) win.spotScroll = (win.spotScroll or 0) - d; win:Refresh() end)
  local function enterSpots(fam)
    local f = TCF.FAMILIES[fam]
    -- open on the newest spot this cat owns
    local s, top = TCF:ProfState(), 1
    for i = 1, spotTotal() do if s.ops[fam][i] and s.ops[fam][i].n > 0 then top = i end end
    if top < spotTotal() and TCF:SpotUnlocked(fam, top + 1) then top = top + 1 end
    win.spotScroll = max(0, top - SPOT_ROWS)
    placeRows(fam, true)
    spotView.clickHint = f.clickHint or ""
  end

  local function refreshSpots(fam)
    local f = TCF.FAMILIES[fam]
    local s = TCF:ProfState()
    local cost = TCF:ToolCost(fam)
    -- the last word of the tool ("Knife" for the Skinning Knife) keeps the label inside the button
    toolBtn:SetText(string.format("Upgrade %s  %s", f.toolNoun:match("(%S+)$") or f.toolNoun, TCF.GoldStr(cost, 10)))
    fitText(toolBtn)
    toolBtn:SetEnabled(s.gold >= cost)
    local slvl, scost = TCF:SpeedLevel(fam), TCF:SpeedCost(fam)
    if scost then speedBtn:SetText(string.format("Hand speed %d  %s", slvl + 1, TCF.GoldStr(scost, 10))); speedBtn:SetEnabled(s.gold >= scost)
    else speedBtn:SetText("|cff20ff20Hand speed max|r"); speedBtn:SetEnabled(false) end
    fitText(speedBtn)
    -- a new cat sees how spots work; after that, how fast it clicks by hand
    local owned = false
    for i = 1, #s.ops[fam] do if s.ops[fam][i].n > 0 then owned = true; break end end
    if not owned then spotHint:SetText(spotView.clickHint or "")
    else
      local nextTxt = scost and string.format(" (%.1f with the next Hand speed level)", TCF:ClicksPerSecond(fam, nil, slvl + 1)) or ""
      spotHint:SetText(string.format("By hand: %.1f clicks a second%s. Hand speed is kept when you sell the business.", TCF:ClicksPerSecond(fam), nextTxt))
    end
    local lvl = TCF:ToolLevel(fam)
    local gskill = TCF:ProfSkill(fam)
    placeRows(fam)
    local total = spotTotal()
    vis(spotPage, total > SPOT_ROWS); vis(spotUp, total > SPOT_ROWS); vis(spotDown, total > SPOT_ROWS)
    spotPage:SetText(string.format("%d-%d of %d", win.spotScroll + 1, win.spotScroll + SPOT_ROWS, total))
    spotUp:SetEnabled(win.spotScroll > 0); spotDown:SetEnabled(win.spotScroll < total - SPOT_ROWS)
    local glitch = TCF:Glitch()
    for _, r in ipairs(rows) do
      local i = r.spot
      local o, st = f.ops[i], s.ops[fam][i]
      local open, why = TCF:SpotUnlocked(fam, i)
      local glitched = glitch and glitch.fam == fam and glitch.i == i
      if r.icon:IsShown() then r.icon:SetDesaturated(st.n == 0) end
      if r.model:IsShown() and r.model.SetAlpha then r.model:SetAlpha(st.n == 0 and 0.5 or 1) end
      r.count:SetText(st.n > 0 and st.n or "")
      if glitched then
        -- the patch secret: the row's name flickers while the spot is glitched
        r.name:SetText((math.sin(GetTime() * 18) > 0 and "|cffcc66ff" or "|cff66ffee") .. o[1] .. "?|r")
      elseif not open then r.name:SetText("|cff777777" .. o[1] .. "|r")
      else r.name:SetText(skillColor(gskill, TCF.SpotDifficulty(i)) .. o[1] .. "|r") end
      local ct = TCF:OpCycleTime(fam, i)
      r.bar:SetMinMaxValues(0, 1)
      local idle = false
      if glitched then
        r.bar:SetValue(TCF:GlitchLeft() / TCF.GLITCH_SECONDS)
        r.bar.text:SetText(string.format("|cffcc66ffWork it by hand: %ds|r", TCF:GlitchLeft()))
      elseif not open then
        r.bar:SetValue(0)
        r.bar.text:SetText("|cff999999Opens later (hover for how)|r")
      elseif st.n > 0 then
        r.bar:SetValue(st.mgr and (ct < 0.3 and 1 or st.p) or (st.run and st.p or 0))
        idle = not st.mgr and not st.run
        if idle then
          -- an idle spot waits for you: say so, and make it pulse
          r.bar.text:SetText(string.format("|cffffd100Click to %s a cycle:|r %s", f.verb:lower(), TCF.GoldStr(TCF:OpRevenue(fam, i), 10)))
          r.sel:SetAlpha(0.45 + 0.4 * math.sin(GetTime() * 5))
        else
          r.bar.text:SetText(TCF.GoldStr(TCF:OpRevenue(fam, i), 10) .. " / " .. (ct >= 1 and string.format("%.1fs", ct) or string.format("%.2fs", ct)))
        end
      else
        r.bar:SetValue(0)
        r.bar.text:SetText(i == 1 and string.format("|cffffd100%s by hand with your %s ->|r", f.verb, f.toolNoun:lower()) or "|cff888888Buy one to start|r")
      end
      vis(r.sel, idle)
      local nextMs
      for _, ms in ipairs(TCF.MILESTONES) do if st.n < ms then nextMs = ms; break end end
      r.info:SetText(string.format("|cffcccccc%s %s|r   %s", TCF.FormatBig(s.mats[o[2]] or 0), o[3],
        nextMs and string.format("Next speed boost at %d", nextMs) or "Max speed"))
      local canPick = i == 1 or st.n > 0
      r.pick:SetEnabled(canPick); r.pick.tex:SetDesaturated(not canPick)
      r.pick.count:SetText(lvl > 0 and lvl or "")
      local count = s.buy == "max" and max(1, TCF:OpMaxBuy(fam, i)) or s.buy
      local bcost = TCF:OpCost(fam, i, count)
      if open then r.buy:SetText("x" .. count .. "  " .. TCF.GoldStr(bcost, 10)); r.buy:SetEnabled(s.gold >= bcost)
      else r.buy:SetText("|cff888888Locked|r"); r.buy:SetEnabled(false) end
      local fcost = TCF.PROF_OPS[i].foreman
      if st.mgr then r.mgr:SetText("|cff20ff20Automated|r"); r.mgr:SetEnabled(false)
      else r.mgr:SetText(f.hire .. " " .. TCF.GoldStr(fcost, 10)); r.mgr:SetEnabled(st.n > 0 and s.gold >= fcost) end
    end
  end

  ------------------------------------------------ main profession: upgrades
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
  local upgNote = Text(upgView, "GameFontDisableSmall", nil, "LEFT"); upgNote:SetPoint("TOPLEFT", 16, -9 * 43 - 4); upgNote:SetWidth(520)
  local function refreshUpgrades(fam)
    local s = TCF:ProfState()
    local list, total = {}, 0
    for _, u in ipairs(TCF.UPGRADES[fam] or {}) do
      total = total + 1
      if not s.upgrades[u.id] and (u.op == 0 or TCF:SpotUnlocked(fam, u.op)) then list[#list + 1] = u end
    end
    for i, r in ipairs(urows) do
      local u = list[i]; r.u = u
      vis(r, u)
      if u then
        r.icon:SetTexture(TCF.Icon(u.icon)); r.name:SetText(u.name)
        r.buy:SetText(TCF.GoldStr(u.cost, 10)); r.buy:SetEnabled(s.gold >= u.cost)
      end
    end
    local bought = 0
    for _, u in ipairs(TCF.UPGRADES[fam] or {}) do if s.upgrades[u.id] then bought = bought + 1 end end
    upgNote:SetText(bought >= total and "|cff20ff20Every upgrade bought.|r"
      or string.format("%d of %d upgrades bought.%s", bought, total, #list + bought < total and " More come with the later spots." or ""))
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
      if TCF:ProfSkill("herbalism") < sd[7] then tt:AddLine("Needs Herbalism " .. sd[7], 1, 0.3, 0.3)
      else addTeachLine(tt, TCF:ProfSkill("herbalism"), sd.teach or sd[7]) end
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
      if i == g.n + 1 then
        ok = TCF:BuyPlot()
        if not ok then why = "Not enough Trade Gold for this plot (" .. TCF.GoldStr(TCF:PlotCost(g.n + 1)) .. ")." end
      elseif i > g.n + 1 then
        -- plots are bought in order: a locked plot further out does nothing
        ok, why = false, "Buy plot " .. (g.n + 1) .. " first."
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
        p.name:SetText(sd[2]); p.bar.text:SetText(left <= 0 and "|cff20ff20Ready to harvest|r" or TCF.FormatDuration(left))
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
    r:EnableMouse(true)
    Tip(r, function(tt)
      tt:AddLine(bd[2], 1, 0.82, 0)
      local sk = TCF:ProfSkill("firstaid")
      if sk < bd[7] then tt:AddLine("Needs First Aid " .. bd[7], 1, 0.3, 0.3) else addTeachLine(tt, sk, bd.teach or bd[7]) end
    end)
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
      -- a manual queue waits when its cloth runs out and the contract can't buy more
      -- (not owned, or not enough Trade Gold): say so
      local cloth
      for _, c in ipairs(TCF.CLOTH) do if c[1] == bd[4] then cloth = c end end
      local short = (s.mats[bd[4]] or 0) < bd[5] and not (a.up.contract and cloth and s.gold >= cloth[4] * bd[5] * 10)
      queueBar.text:SetText("Making " .. bd[2] .. (a.queue.auto and " (field medic)" or ("  -  " .. a.queue.left .. " left"))
        .. (short and ("  |cffff5050(needs " .. TCF.MAT_BY_KEY[bd[4]].name .. ")|r") or ""))
    else
      queueBar:SetValue(0); queueBar.text:SetText("|cffaaaaaaNothing being made. Pick a bandage below.|r")
    end
    for _, r in ipairs(brows) do
      local bd = r.bd
      local can = skill >= bd[7]
      r.icon:SetDesaturated(not can)
      r.name:SetText(string.format("%s%s|r  |cff999999heals %d%%, %d %s%s|r", can and skillColor(skill, bd.teach or bd[7]) or "|cff777777", bd[2], bd[8] * 100, bd[5],
        TCF.MAT_BY_KEY[bd[4]].name, can and "" or (", skill " .. bd[7])))
      r.stock:SetText((s.mats[bd[1]] or 0) > 0 and ("x" .. (s.mats[bd[1]] or 0)) or "")
      r.m5:SetEnabled(can); r.m20:SetEnabled(can)
    end
    for _, b in ipairs(aUps) do b:Update() end
  end

  ------------------------------------------------ Fishing: the dock
  -- A cartoon dock over a lake (Art/v/bg_dock, 512x256 like the Adventure backgrounds). Your cat
  -- sits on the dock with a fishing pole; once hired, the Fishing Buddy sits beside it. The
  -- bobber floats out in the water.
  local fishView = View()
  local SCENE_W, SCENE_H = 528, 246
  local scene = Panel(fishView, SCENE_W, SCENE_H, 1); scene:SetPoint("TOP", 0, -2)
  if scene.SetClipsChildren then scene:SetClipsChildren(true) end
  local lake = scene:CreateTexture(nil, "BACKGROUND", nil, 0); lake:SetPoint("TOPLEFT", 4, -4); lake:SetPoint("BOTTOMRIGHT", -4, 4)
  lake:SetColorTexture(0.28, 0.52, 0.70, 1)
  local dockArt = scene:CreateTexture(nil, "BACKGROUND", nil, 1); dockArt:SetPoint("TOPLEFT", 4, -4); dockArt:SetPoint("BOTTOMRIGHT", -4, 4)
  dockArt:SetTexture(TCF.ART_PATH .. "v\\bg_dock"); dockArt:SetTexCoord(0, 1, 0, 1)

  -- where things sit, in pixels from the scene's bottom-left corner. In bg_dock the dock runs
  -- from the left edge to x ~200 of 512 with its planks at y ~175 of 256 (about 77 px up here);
  -- open water is to the right of it, lily pads at x 220-270 and reeds from x 460.
  local DECK = 77
  -- the cartoon cat's body ends 46 units above the bottom of its 512-unit canvas
  local function seat(size) return DECK - floor(size * 46 / 512 + 0.5) end
  local CAT_SIZE, CAT_X = 112, 94           -- your cat, near the end of the dock
  local BUDDY_SIZE, BUDDY_X = 84, 28        -- the buddy, beside it further back
  local BOB_X, BOB_Y = 350, 72              -- your bobber, out in the water
  local BBOB_X, BBOB_Y = 300, 50            -- the buddy's bobber, closer in

  -- fishing lines are drawn on the scene itself, under the cats (they go behind your cat)
  local function MakeLine()
    local l = scene.CreateLine and scene:CreateLine(nil, "ARTWORK")
    if not l then return nil end
    if l.SetThickness then l:SetThickness(1.5) end
    l:SetColorTexture(0.95, 0.95, 0.90, 0.75)
    l:Hide()
    return l
  end
  local catLine, buddyLine = MakeLine(), MakeLine()
  local function placeLine(l, x1, y1, x2, y2)
    if not l then return end
    l:SetStartPoint("BOTTOMLEFT", scene, x1, y1); l:SetEndPoint("BOTTOMLEFT", scene, x2, y2)
  end
  local function poleTip(cat, x, size)
    local up = not (cat.pawState and cat.pawState.R)
    local y = POLE_TIP_Y - (up and PAW_LIFT or 0)
    return x + POLE_TIP_X / 512 * size, seat(size) + size - y / 512 * size
  end

  -- bobbers, splashes and catch text play above everything
  local fx = CreateFrame("Frame", nil, scene); fx:SetAllPoints(scene)
  if fx.SetFrameLevel and scene.GetFrameLevel then pcall(fx.SetFrameLevel, fx, (scene:GetFrameLevel() or 1) + 20) end
  local buddyHolder = CreateFrame("Button", nil, scene); buddyHolder:SetSize(BUDDY_SIZE, BUDDY_SIZE)
  buddyHolder:SetPoint("BOTTOMLEFT", BUDDY_X, seat(BUDDY_SIZE))
  local buddyCat = TCF.CreateCat(buddyHolder, BUDDY_SIZE, { preview = true })
  buddyCat.frame:SetPoint("CENTER")
  buddyHolder:Hide()
  local buddyName = Text(fx, "GameFontNormalSmall"); buddyName:SetPoint("BOTTOM", buddyHolder, "TOP", 0, -2); buddyName:Hide()
  Tip(buddyHolder, function(tt)
    local f = TCF:FishState()
    local lv = TCF.BUDDY_LEVELS[f.buddy]
    if not lv then return end
    tt:AddLine(lv.name, 1, 0.82, 0)
    tt:AddLine(string.format("Catches a fish at %s every %ds, even while you're offline.", TCF.FISHING_SPOTS[f.spot].name, lv.every), 1, 1, 1, true)
    tt:AddLine(string.format("Next catch in %ds.", max(0, floor(lv.every - (f.bp or 0)))), 0.7, 0.7, 0.7)
  end)
  local catHolder = CreateFrame("Frame", nil, scene); catHolder:SetSize(CAT_SIZE, CAT_SIZE)
  catHolder:SetPoint("BOTTOMLEFT", CAT_X, seat(CAT_SIZE))
  local dockCat = TCF.CreateCat(catHolder, CAT_SIZE, { preview = true })
  dockCat.frame:SetPoint("CENTER")

  local bobber = fx:CreateTexture(nil, "ARTWORK"); bobber:SetSize(36, 36)
  bobber:SetTexture(TCF.ART_PATH .. "ui_bobber", nil, nil, "NEAREST"); bobber:Hide()
  local buddyBobber = fx:CreateTexture(nil, "ARTWORK"); buddyBobber:SetSize(24, 24)
  buddyBobber:SetTexture(TCF.ART_PATH .. "ui_bobber", nil, nil, "NEAREST"); buddyBobber:Hide()
  local splash = Text(fx, "GameFontNormalLarge"); splash:SetPoint("BOTTOM", fx, "BOTTOMLEFT", BOB_X, BOB_Y + 22)
  local buddyPop = Text(fx, "GameFontNormalSmall"); buddyPop:Hide()
  local sceneHint = Text(fx, "GameFontHighlight"); sceneHint:SetPoint("TOPRIGHT", -14, -12); sceneHint:SetWidth(240); sceneHint:SetJustifyH("RIGHT")

  local castBtn = Button(fishView, "Cast", 150, 28, function() TCF:FishCast(); win:Refresh() end); castBtn:SetPoint("TOPLEFT", 40, -254)
  local reelBtn = Button(fishView, "Reel in", 150, 28, function()
    TCF:FishReel(); dockCat:Tap("R")
    local run = TCF.fishRun
    if run and run.kind and run.kind ~= "miss" then dockCat:SetFaceFor("happy", 1.5) end
    win:Refresh()
  end)
  reelBtn:SetPoint("LEFT", castBtn, "RIGHT", 20, 0)
  local resultText = Text(fishView, "GameFontHighlight", nil, "LEFT"); resultText:SetPoint("LEFT", reelBtn, "RIGHT", 16, 0); resultText:SetWidth(170)
  local spotBtns = {}
  for i, sp in ipairs(TCF.FISHING_SPOTS) do
    local b = Button(fishView, sp.name, 102, 22, function() TCF:SetFishingSpot(i); win:Refresh() end)
    b:SetPoint("TOPLEFT", 12 + (i - 1) * 105, -288)
    Tip(b, function(tt)
      tt:AddLine(sp.name, 1, 0.82, 0)
      local names = {}
      for _, k in ipairs(sp.fish) do names[#names + 1] = TCF.MAT_BY_KEY[k].name end
      tt:AddLine(table.concat(names, ", "), 1, 1, 1, true)
      if TCF:ProfSkill("fishing") < sp.skill then tt:AddLine("Needs Fishing " .. sp.skill, 1, 0.3, 0.3)
      else addTeachLine(tt, TCF:ProfSkill("fishing"), sp.teach or sp.skill) end
    end)
    b.spot = sp
    spotBtns[i] = b
  end
  local catchBtns = {}
  local CATCH_KEYS = { "smallfish", "longjaw", "bristle", "blackmouth", "trout", "rockscale", "nightfin", "sunscale", "eel", "whitescale", "pinchy", "boot" }
  for i, k in ipairs(CATCH_KEYS) do
    local b = IconButton(fishView, 30); b:SetPoint("TOPLEFT", 12 + (i - 1) * 43, -316)
    b.tex:SetTexture(TCF.Icon(TCF.MAT_BY_KEY[k].icon)); b.key = k
    b:SetScript("OnClick", function() TCF:SellMat(k, 10); win:Refresh() end)
    Tip(b, function(tt) tt:AddLine(TCF.MAT_BY_KEY[k].name, 1, 1, 1); tt:AddLine("Click: sell 10 for " .. TCF.GoldStr(TCF.MAT_BY_KEY[k].value * 10), 0, 1, 0) end)
    catchBtns[i] = b
  end
  local buddyBtn = Button(fishView, "Fishing Buddy", 300, 24, function() TCF:BuyBuddy(); win:Refresh() end); buddyBtn:SetPoint("TOPLEFT", 12, -356)
  Tip(buddyBtn, function(tt) tt:AddLine("Fishing buddy", 1, 0.82, 0); tt:AddLine("Sits beside your cat on the dock and catches fish at your chosen spot all by himself, even offline. Each upgrade makes him faster.", 1, 1, 1, true) end)
  local buddyText = Text(fishView, "GameFontHighlightSmall", nil, "LEFT"); buddyText:SetPoint("LEFT", buddyBtn, "RIGHT", 10, 0); buddyText:SetWidth(210)

  -- your cat holds a fishing pole (your own fishing pole cosmetic if you wear one)
  local function dockLook()
    local look = TCF:GetAppearance()
    local m = look.main
    if not (m and not m.gear and m.art == "wpn_fishpole") then look.main = TCF.ITEMS.wpn_fishpole end
    look.off = nil
    return look
  end
  -- the buddy: another fur than yours, a pole, and a hat once he's a Seasoned Angler
  local function buddyLook(level)
    local mine = TCF.db.look.fur
    local fur = TCF.ITEMS[mine == "fur_ginger" and "fur_snow" or "fur_ginger"]
    return { fur = fur, main = TCF.ITEMS[level >= 4 and "wpn_fishpole_a" or "wpn_fishpole"] or TCF.ITEMS.wpn_fishpole,
      head = level >= 2 and TCF.ITEMS.craft_fishing_hat or nil }
  end
  local lookT, buddyLevelShown, lastBp, lastFish = 0, -1, nil, nil   -- lastFish: whose buddy lastBp is
  local function applyDockLooks(f)
    dockCat:ApplyAppearance(dockLook())
    if f.buddy > 0 then buddyCat:ApplyAppearance(buddyLook(f.buddy)) end
    lookT = 0
  end

  local fishT, buddyPopT = 0, 0
  fishView:SetScript("OnUpdate", function(_, e)
    fishT = fishT + e
    local run = TCF.fishRun
    local st = run and run.state
    local cast = st == "waiting" or st == "bite"
    local bob = 0
    if st == "waiting" then bob = math.sin(fishT * 3) * 2
    elseif st == "bite" then bob = -6 + math.sin(fishT * 30) * 5 end
    bobber:ClearAllPoints(); bobber:SetPoint("CENTER", fx, "BOTTOMLEFT", BOB_X, BOB_Y + bob)
    vis(bobber, cast)
    if catLine then
      if cast then
        local x, y = poleTip(dockCat, CAT_X, CAT_SIZE)
        placeLine(catLine, x, y, BOB_X, BOB_Y + bob + 10)
      end
      vis(catLine, cast)
    end
    splash:SetText(st == "bite" and "|cffffffffSplash|r" or "")
    reelBtn:SetEnabled(cast)
    castBtn:SetEnabled(not cast)
    if st == "result" then
      local col = run.kind == "miss" and "|cffff6060" or run.kind == "pinchy" and "|cffa335ee" or run.kind == "treasure" and "|cff20ff20" or "|cffffffff"
      resultText:SetText(col .. (run.result or "") .. "|r")
    elseif st == "waiting" then resultText:SetText("|cffaaaaaaWait for the splash...|r")
    elseif st == "bite" then resultText:SetText("|cffffd100A bite. Click Reel in.|r")
    else resultText:SetText("|cffaaaaaaClick Cast to throw your line.|r") end
    -- the buddy's own bobber bobs gently; it dips and shows the fish when he catches one
    local f = TCF:FishState()
    if f.buddy > 0 then
      local bb = math.sin(fishT * 2.2 + 1) * 1.5
      if buddyPopT > 0 then bb = bb - 4 end
      buddyBobber:ClearAllPoints(); buddyBobber:SetPoint("CENTER", fx, "BOTTOMLEFT", BBOB_X, BBOB_Y + bb)
      if buddyLine then
        local x, y = poleTip(buddyCat, BUDDY_X, BUDDY_SIZE)
        placeLine(buddyLine, x, y, BBOB_X, BBOB_Y + bb + 7)
      end
      -- a catch: the progress counter went back down
      if lastBp and lastFish == f and (f.bp or 0) + 0.001 < lastBp then
        buddyPopT = 1.2
        buddyCat:SetFaceFor("happy", 1.2)
        buddyPop:SetText("|cffffffff+1 fish|r")
      end
      lastBp, lastFish = f.bp or 0, f
    else lastBp, lastFish = nil, nil end
    if buddyPopT > 0 then
      buddyPopT = buddyPopT - e
      buddyPop:ClearAllPoints(); buddyPop:SetPoint("BOTTOM", fx, "BOTTOMLEFT", BBOB_X, BBOB_Y + 14 + (1.2 - buddyPopT) * 16)
      buddyPop:SetAlpha(min(1, buddyPopT * 2))
    end
    vis(buddyPop, buddyPopT > 0)
    lookT = lookT + e
    if lookT > 1 then applyDockLooks(f) end
  end)
  local function enterFishing()
    applyDockLooks(TCF:FishState())
  end
  local function refreshFishing()
    local f, s = TCF:FishState()
    local skill = TCF:ProfSkill("fishing")
    for i, b in ipairs(spotBtns) do
      b:SetEnabled(skill >= b.spot.skill)
      if i == f.spot then b:LockHighlight() else b:UnlockHighlight() end
    end
    for _, b in ipairs(catchBtns) do b.count:SetText((s.mats[b.key] or 0) > 0 and TCF.FormatBig(s.mats[b.key]) or "") end
    -- the buddy appears on the dock once hired (and changes look as he levels up)
    if f.buddy ~= buddyLevelShown then
      buddyLevelShown = f.buddy
      local has = f.buddy > 0
      vis(buddyHolder, has); vis(buddyName, has); vis(buddyBobber, has)
      if buddyLine then vis(buddyLine, has) end
      if has then buddyCat:ApplyAppearance(buddyLook(f.buddy)) end
    end
    buddyName:SetText(f.buddy > 0 and TCF.BUDDY_LEVELS[f.buddy].name or "")
    sceneHint:SetText(TCF.FISHING_SPOTS[f.spot].name)
    local nextLvl = TCF.BUDDY_LEVELS[f.buddy + 1]
    if nextLvl then
      buddyBtn:SetText((f.buddy == 0 and "Hire " or "Upgrade to ") .. nextLvl.name .. "  " .. TCF.GoldStr(nextLvl.cost, 10))
      buddyBtn:SetEnabled(s.gold >= nextLvl.cost)
    else buddyBtn:SetText("|cff20ff20" .. TCF.BUDDY_LEVELS[f.buddy].name .. "|r"); buddyBtn:SetEnabled(false) end
    buddyText:SetText(f.buddy > 0 and string.format("%s catches a fish every %ds.", TCF.BUDDY_LEVELS[f.buddy].name, TCF.BUDDY_LEVELS[f.buddy].every) or "No buddy yet. Hire one to fish beside your cat.")
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
      tt:AddLine(#uses > 0 and ("Used in: " .. table.concat(uses, ", ")) or "Experiment in the pot to find out what uses it.", 0.5, 1, 0.5, true)
    end)
    spiceBtns[i] = b
  end
  local potSlots = {}
  for i = 1, 3 do
    local b = IconButton(cookView, 34); b:SetPoint("TOPLEFT", 12 + (i - 1) * 40, -72)
    if b.tex then b.tex:SetTexture(TCF.Icon("INV_Misc_Food_15")) end
    potSlots[i] = b
  end
  local cookBtn = Button(cookView, "Cook", 80, 26, function()
    local text = TCF:CookPot(); win.cookResult = text; win:Refresh()
  end)
  cookBtn:SetPoint("TOPLEFT", 140, -76)
  local clearBtn = Button(cookView, "Empty pot", 80, 26, function() TCF:PotClear(); win:Refresh() end); clearBtn:SetPoint("LEFT", cookBtn, "RIGHT", 6, 0)
  local cookResult = Text(cookView, "GameFontHighlight", nil, "LEFT"); cookResult:SetPoint("LEFT", clearBtn, "RIGHT", 10, 0); cookResult:SetWidth(220)
  local buffText = Text(cookView, "GameFontNormalSmall", nil, "LEFT"); buffText:SetPoint("TOPLEFT", 12, -112); buffText:SetWidth(520)
  local crows = {}
  for i, r in ipairs(TCF.COOK_RECIPES) do
    local row = CreateFrame("Frame", nil, cookView); row:SetSize(532, 18); row:SetPoint("TOPLEFT", 6, -128 - (i - 1) * 19)
    row.icon = row:CreateTexture(nil, "ARTWORK"); row.icon:SetSize(18, 18); row.icon:SetPoint("LEFT", 4, 0)
    row.name = Text(row, "GameFontHighlightSmall", nil, "LEFT"); row.name:SetPoint("LEFT", row.icon, "RIGHT", 6, 0); row.name:SetWidth(300)
    row.count = Text(row, "GameFontNormalSmall", nil, "RIGHT"); row.count:SetPoint("RIGHT", -184, 0)
    row.eat = Button(row, "Eat", 44, 18, function() TCF:EatDish(r[1]); win:Refresh() end); row.eat:SetPoint("RIGHT", -132, 0)
    row.cook = Button(row, "Cook", 52, 18, function() TCF:CookKnown(r[1]); win:Refresh() end); row.cook:SetPoint("RIGHT", -74, 0)
    row.chef = Button(row, "Chef", 64, 18, function() TCF:CookState().chefRecipe = r[1]; win:Refresh() end); row.chef:SetPoint("RIGHT", -4, 0)
    Tip(row.chef, function(tt) tt:AddLine("Sous-chef recipe", 1, 0.82, 0); tt:AddLine("Your sous-chef keeps cooking this one (needs the Sous-Chef upgrade).", 1, 1, 1, true) end)
    row.r = r
    row:EnableMouse(true)
    Tip(row, function(tt)
      local sk = TCF:ProfSkill("cooking")
      tt:AddLine(TCF:CookState().known[r[1]] and r[2] or "Unknown recipe", 1, 0.82, 0)
      if sk < r[5] then tt:AddLine("Needs Cooking " .. r[5], 1, 0.3, 0.3) else addTeachLine(tt, sk, r.teach or r[5]) end
    end)
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
        row.name:SetText(string.format("%s%s|r  |cff999999+%d%% %s, %dm|r", skill >= r[5] and skillColor(skill, r.teach or r[5]) or "|cff888888", r[2], r[7] * 100, TCF.BUFF_TEXT[r[6]], r[8]))
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
  -- Every recipe of the profession: the ones you can make first (by skill), then the locked
  -- ones greyed out with the skill they need. Gear recipes show the real item and how it
  -- compares with what your cat wears; cosmetic recipes say "Cosmetic only (no stats)".
  -- Scroll with the mouse wheel or the arrow buttons.
  local craftView = View()
  local CROWS = 7
  local craftHead = Text(craftView, "GameFontNormal", nil, "LEFT"); craftHead:SetPoint("TOPLEFT", 14, -2); craftHead:SetWidth(282)
  if craftHead.SetWordWrap then craftHead:SetWordWrap(false) end
  local craftLegend = Text(craftView, "GameFontDisableSmall", nil, "RIGHT"); craftLegend:SetPoint("TOPRIGHT", -14, -4); craftLegend:SetWidth(240)
  if craftLegend.SetWordWrap then craftLegend:SetWordWrap(false) end
  local crafts = {}
  local craftList = {}
  local powerCache = {}
  local function powerDelta(it)
    local c = powerCache[it.id]
    local now = GetTime()
    if not c or now - c.t > 2 then
      c = { t = now, d = TCF.GearUpgrade and TCF:GearUpgrade(it) or nil }
      powerCache[it.id] = c
    end
    return c.d
  end
  local function recipeEnter(r, owner)
    local rec = r.recipe
    if not rec then return end
    local it = TCF:RecipeItem(rec)
    if not it then return end
    GameTooltip:SetOwner(owner, "ANCHOR_RIGHT")
    if rec.gear then
      TCF:GearTooltip(GameTooltip, it)
      if TCF.UI.ShowTryOn then TCF.UI.ShowTryOn(win, it) end
    else
      TCF:ItemTooltip(GameTooltip, it, true)   -- already says "Cosmetic only (no stats)"
      win.preview:ApplyAppearance(TCF:GetAppearance(nil, it))
    end
    local p = TCF.PROF_BY_KEY[rec.prof]
    GameTooltip:AddLine(" ")
    GameTooltip:AddLine(string.format("Recipe: %s%s", p and p.name or rec.prof, rec.skill and (" " .. rec.skill) or ""), 1, 0.82, 0)
    local s = TCF:ProfState()
    for mk, need in pairs(rec.mats) do
      local m = TCF.MAT_BY_KEY[mk]
      local have = s.mats[mk] or 0
      GameTooltip:AddDoubleLine((m and m.name) or mk, TCF.FormatBig(have) .. " / " .. TCF.FormatBig(need),
        1, 1, 1, have >= need and 0.2 or 1, have >= need and 1 or 0.3, have >= need and 0.2 or 0.3)
    end
    if rec.gear then GameTooltip:AddLine("Crafted gear goes straight into your bag.", 0.7, 0.7, 0.7, true) end
    if rec.starter then
      local done, total = TCF:StarterProgress(rec.prof)
      GameTooltip:AddLine(string.format("Starter set (%d/%d made): a cheap white piece for each slot, so a new cat can wear a full crafted set.", done, total), 0.88, 0.75, 0.5, true)
    end
    GameTooltip:Show()
  end
  local function recipeLeave()
    GameTooltip:Hide()
    win.preview:ApplyAppearance(TCF:GetAppearance())
  end
  for i = 1, CROWS do
    local r = Panel(craftView, 532, 48, 0.85); r:SetPoint("TOP", 0, -22 - (i - 1) * 50)
    r.gearBtn = U.GearButton(r, 40); r.gearBtn:SetPoint("LEFT", 5, 0); r.gearBtn:Hide()
    r.cell = U.ItemCell(r, 40); r.cell:SetPoint("LEFT", 5, 0); r.cell:Hide()
    for _, b in ipairs({ r.gearBtn, r.cell }) do
      b:SetScript("OnEnter", function(s) recipeEnter(r, s) end)
      b:SetScript("OnLeave", recipeLeave)
    end
    r:SetScript("OnEnter", function(s) recipeEnter(r, s) end)
    r:SetScript("OnLeave", recipeLeave)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("TOPLEFT", 52, -4); r.name:SetWidth(350)
    r.info = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.info:SetPoint("LEFT", 52, -1); r.info:SetWidth(350)
    r.need = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.need:SetPoint("BOTTOMLEFT", 52, 4); r.need:SetWidth(350)
    for _, fs in ipairs({ r.name, r.info, r.need }) do if fs.SetWordWrap then fs:SetWordWrap(false) end end
    r.delta = Text(r, "GameFontNormal", nil, "RIGHT"); r.delta:SetPoint("RIGHT", -124, 0)
    r.craft = Button(r, "Craft", 62, 22, function()
      if r.recipe and TCF:Craft(r.recipe) then TCF:PlaySound("click"); win:Refresh() end
    end)
    r.craft:SetPoint("RIGHT", -52, 0)
    r.all = Button(r, "All", 42, 22, function()
      if r.recipe and TCF:CraftAll(r.recipe) > 0 then TCF:PlaySound("click"); win:Refresh() end
    end)
    r.all:SetPoint("RIGHT", -6, 0)
    Tip(r.all, function(tt)
      local rec = r.recipe
      if not rec then return end
      local n = TCF:CraftCount(rec)
      tt:AddLine("Craft all", 1, 0.82, 0)
      if n > 0 then tt:AddLine(string.format("Makes %d with the materials you have (up to %d at once).", n, TCF.CRAFT_ALL_MAX), 1, 1, 1, true)
      else tt:AddLine("You don't have enough materials yet.", 1, 0.3, 0.3, true) end
    end)
    Tip(r.craft, function(tt)
      local rec = r.recipe
      if not rec then return end
      local it = TCF:RecipeItem(rec)
      tt:AddLine("Craft " .. (it and it.name or ""), 1, 0.82, 0)
      local why = TCF:CraftBlocked(rec)
      if why then tt:AddLine(why, 1, 0.3, 0.3, true)
      elseif not TCF:CanCraft(rec) then tt:AddLine("You don't have enough materials yet.", 1, 0.3, 0.3, true)
      else tt:AddLine(rec.gear and "Uses the materials and puts the item in your bag." or "Uses the materials and adds it to your collection.", 1, 1, 1, true) end
      if TCF.CRAFT_FAMILY[rec.prof] then addTeachLine(tt, TCF:ProfSkill(rec.prof), rec.skill or 1) end
    end)
    crafts[i] = r
  end
  local craftPage = Text(craftView, "GameFontHighlightSmall"); craftPage:SetPoint("TOP", 0, -22 - CROWS * 50 - 6)
  local craftUp = Button(craftView, "<", 28, 20, function() win.craftScroll = max(0, (win.craftScroll or 0) - CROWS); win:Refresh() end)
  craftUp:SetPoint("RIGHT", craftPage, "LEFT", -10, 0)
  local craftDown = Button(craftView, ">", 28, 20, function() win.craftScroll = (win.craftScroll or 0) + CROWS; win:Refresh() end)
  craftDown:SetPoint("LEFT", craftPage, "RIGHT", 10, 0)
  craftView:EnableMouseWheel(true)
  craftView:SetScript("OnMouseWheel", function(_, d) win.craftScroll = max(0, (win.craftScroll or 0) - d * 2); win:Refresh() end)

  local function recipeLocked(rec)
    return rec.skill and TCF:ProfSkill(rec.prof) < rec.skill and true or false
  end
  -- the starter set sits at the top while the crafting skill is low
  local function starterFirst(key) return TCF.CRAFT_FAMILY[key] and TCF:ProfSkill(key) < TCF.STARTER_SET_SKILL end
  -- the sorted list: makeable first (by skill), then locked (by skill)
  local lastCraftSig
  local function buildCraftList(key)
    -- the page refreshes several times a second: only rebuild when the craft, skill or recipes change
    local sig = key .. ":" .. TCF:ProfSkill(key) .. ":" .. #(TCF.RECIPES[key] or {})
    if sig == lastCraftSig and #craftList > 0 then
      local open = 0
      for _, e in ipairs(craftList) do if not e.locked then open = open + 1 end end
      return open
    end
    lastCraftSig = sig
    wipe(craftList)
    for idx, rec in ipairs(TCF.RECIPES[key] or {}) do
      if TCF:RecipeItem(rec) then craftList[#craftList + 1] = { rec = rec, idx = idx, locked = recipeLocked(rec) } end
    end
    local first = starterFirst(key)
    table.sort(craftList, function(a, b)
      if first and (a.rec.starter and true or false) ~= (b.rec.starter and true or false) then return a.rec.starter and true or false end
      if a.locked ~= b.locked then return not a.locked end
      local sa, sb = a.rec.skill or 0, b.rec.skill or 0
      if sa ~= sb then return sa < sb end
      return a.idx < b.idx
    end)
    local open = 0
    for _, e in ipairs(craftList) do if not e.locked then open = open + 1 end end
    return open
  end
  -- opening the list scrolls to your newest recipes and the next ones to unlock
  local function enterCraft(key)
    local open = buildCraftList(key)
    win.craftScroll = starterFirst(key) and 0 or max(0, open - (CROWS - 2))
  end

  local function refreshCraft(key)
    local s = TCF:ProfState()
    buildCraftList(key)
    local p = TCF.PROF_BY_KEY[key]
    local isCraft = TCF.CRAFT_FAMILY[key] and true or false
    local skill = TCF:ProfSkill(key)
    if isCraft then
      local fam = TCF.CRAFT_FAMILY[key]
      local f = TCF.FAMILIES[fam]
      if starterFirst(key) then
        local done, total = TCF:StarterProgress(key)
        craftHead:SetText(string.format("%s |cffffffff%d / 300|r   %sStarter set %d/%d made|r", f.craftName, skill,
          done >= total and "|cff20ff20" or "|cffffd100", done, total))
      else
        craftHead:SetText(string.format("%s |cffffffff%d / 300|r    |cffaaaaaa%s %d / 300|r", f.craftName, skill, f.skillName or f.tab, TCF:ProfSkill(fam)))
      end
      local legend = "|cffff8040always|r  |cffffff00often|r  |cff40c040sometimes|r  |cff70a070rarely|r  |cff808080no longer|r"
      craftLegend:SetText("Teaches: " .. legend)
      local lw = textWidth(craftLegend)
      if type(lw) == "number" and lw > 238 then craftLegend:SetText(legend) end
    else
      craftHead:SetText(string.format("%s crafting  |cffffffff(skill %d / 300)|r", p and p.name or key, skill))
      craftLegend:SetText("Cosmetics change your cat's look only.")
    end
    fitText(craftHead)
    local maxScroll = max(0, #craftList - CROWS)
    win.craftScroll = min(max(0, win.craftScroll or 0), maxScroll)
    local off = win.craftScroll
    local level = TCF:CD().level
    for i, r in ipairs(crafts) do
      local e = craftList[off + i]
      local rec = e and e.rec
      r.recipe = rec
      vis(r, rec)
      if rec then
        local it = TCF:RecipeItem(rec)
        local lockedRow = e.locked
        local skillTxt = ""
        if rec.skill then
          skillTxt = "  " .. (lockedRow and "|cffff5050" or (isCraft and skillColor(skill, rec.skill) or "|cffaaaaaa")) .. "Skill " .. rec.skill .. "|r"
        end
        if rec.gear then
          vis(r.cell, false); vis(r.gearBtn, true)
          r.gearBtn:SetGear(it)
          r.gearBtn.icon:SetDesaturated(lockedRow); r.gearBtn.icon:SetAlpha(lockedRow and 0.55 or 1)
          local n = TCF:Bag()[it.id] or 0
          r.gearBtn.count:SetText(n > 0 and n or "")
          local col = lockedRow and "|cff888888" or ("|c" .. TCF.RARITY[it.q].hex)
          local note = ""
          if not TCF:RecipeUsable(rec) then note = "  |cffff9933(your class can't wear this)|r"
          elseif n > 0 then note = "  |cff20ff20(you have " .. n .. ")|r" end
          r.name:SetText(col .. it.name .. "|r" .. skillTxt .. note)
          local summary = TCF.GearSummary and TCF.GearSummary(it) or ""
          r.info:SetText(string.format("%s|cffffd100%d|r  %s %s%s  |cff999999%s|r", rec.starter and "|cffe0c080Starter set|r  " or "", it.ilvl, TCF.ITEM_TYPE_NAMES[it.sub] or "",
            TCF.ITEM_SLOT_NAMES[it.slot] or "", (it.req or 0) > level and ("  |cffff9933level " .. it.req .. "|r") or "", summary))
          local d = (not lockedRow) and powerDelta(it) or nil
          if d then r.delta:SetText(d > 0 and ("|cff20ff20+" .. d .. "|r") or d < 0 and ("|cffff4040" .. d .. "|r") or "|cff999999=|r")
          else r.delta:SetText("") end
        else
          vis(r.gearBtn, false)
          r.cell:SetItem(it, TCF.db.owned[it.id] and true or false, false)
          if lockedRow then r.cell.pic:SetAlpha(0.3) end
          local col = lockedRow and "|cff888888" or ("|c" .. TCF.RARITY[it.rarity].hex)
          r.name:SetText(col .. it.name .. "|r" .. skillTxt .. (TCF.db.owned[it.id] and "  |cff20ff20(owned)|r" or ""))
          local slot = TCF.SLOT_BY_KEY[it.slot]
          r.info:SetText("|cffd38cffCosmetic only (no stats)|r  |cff999999" .. (it.slot == "skin" and "Cat skin" or (slot and slot.name or "")) .. "|r")
          r.delta:SetText("")
        end
        -- materials: have / need, then why it can't be made yet
        local keys, parts, plain = {}, {}, {}
        for mk in pairs(rec.mats) do keys[#keys + 1] = mk end
        table.sort(keys)
        for _, mk in ipairs(keys) do
          local need, have = rec.mats[mk], s.mats[mk] or 0
          local m = TCF.MAT_BY_KEY[mk]
          local nm = m and m.name or mk
          parts[#parts + 1] = string.format("%s%s/%s|r %s", have >= need and "|cff20ff20" or "|cffff5050",
            TCF.FormatBig(min(have, need)), TCF.FormatBig(need), nm)
          plain[#plain + 1] = TCF.FormatBig(need) .. " " .. nm
        end
        local why = TCF:CraftBlocked(rec)
        if why then r.need:SetText("|cffff5050" .. why .. "|r  |cff888888Uses " .. table.concat(plain, ", ") .. "|r")
        else r.need:SetText(table.concat(parts, ",  ")) end
        r.craft:SetEnabled(TCF:CanCraft(rec))
        r.all:SetEnabled(TCF:CraftCount(rec) > 1)
      end
    end
    if #craftList == 0 then craftPage:SetText("|cff888888No recipes yet.|r")
    else
      craftPage:SetText(string.format("Recipes %d-%d of %d  (mouse wheel to scroll)", off + 1, min(#craftList, off + CROWS), #craftList))
    end
    craftUp:SetEnabled(off > 0); craftDown:SetEnabled(off < maxScroll)
  end

  ------------------------------------------------ renown
  local renView = View()
  local renInfo = Text(renView, "GameFontHighlight", nil, "LEFT"); renInfo:SetPoint("TOPLEFT", 16, -10); renInfo:SetWidth(520); renInfo:SetSpacing(4)
  local renBtn = Button(renView, "Sell the business", 180, 26, function()
    if IsShiftKeyDown() then TCF:PrestigeTrade() else TCF:Print("Shift-click to sell everything you bought with Trade Gold for Renown.", true) end
  end)
  renBtn:SetPoint("TOPLEFT", 16, -250)
  local function refreshRenown()
    local s = TCF:ProfState()
    local gain = TCF:RenownOnReset()
    local unlocks = {}
    for _, p in ipairs(TCF:ProfList()) do
      if (p.gold or 0) > 0 then unlocks[#unlocks + 1] = string.format("%s%s at %s|r", TCF:ProfUnlocked(p.key) and "|cff20ff20" or "|cffaaaaaa", p.name, TCF.FormatBig(p.gold)) end
    end
    renInfo:SetText(string.format(
      "%s Your %s cat's business:\n\n" ..
      "|cffffd100Renown|r is permanent: each point adds +2%% to this cat's Trade Gold, so it earns faster.\n\n" ..
      "Current Renown: |cffffffff%d|r (highest ever %d)\nTrade Gold earned in total: |cffffffff%s|r\nRenown you'd gain by selling now: |cff20ff20%d|r  (+%d TapCoins)\n\n" ..
      "New professions unlock at Trade Gold earned in total (selling never lowers it): %s\n\nSelling resets this cat's Trade Gold, %s, %s, garden plots, %s, helpers and upgrades. " ..
      "You keep skills, Hand speed, recipes, materials, crafted gear, bandages, dishes and unlocked professions. Your other cats keep their own business.",
      PER_CLASS, className(), s.renown, s.renownEver, TCF.GoldStr(s.lifetime, 12), gain, min(1000, gain * 3), table.concat(unlocks, ", "),
      FT().spotsTitle:lower(), FT().toolNoun:lower(), FT().hirePlural:lower()))
    renBtn:SetEnabled(gain >= 5)
  end

  ------------------------------------------------ refresh
  local MAIN = { herbalism = { gardenView, refreshGarden, "Garden" },
    firstaid = { aidView, refreshAid, "Bandages" }, fishing = { fishView, refreshFishing, "Fishing", enterFishing },
    cooking = { cookView, refreshCooking, "Kitchen" } }
  local allViews = { locked, spotView, upgView, gardenView, aidView, fishView, cookView, craftView, renView }

  local refresh
  local acc = 0
  page:SetScript("OnUpdate", function(_, e)
    acc = acc + e
    if acc > 0.15 and refresh then acc = 0; refresh() end
  end)

  -- the profession to show: a family tab always means the current class's family
  local function currentProf()
    local main = TCF:MainProf()
    local sel = win.profSel
    local p = sel and TCF.PROF_BY_KEY[sel]
    if not p or p.craft or TCF.FAMILIES[sel] then sel = main end
    win.profSel = sel
    return sel
  end

  ------------------------------------------------ "How it works" guide (opens by itself the first time)
  local GUIDE_OTHER = {
    herbalism = "|cffffd100Grow|r: plant seeds in your garden plots. Herbs grow in real time, even while you're offline, and a gardener can replant for you.\n\n|cffffd100Use|r: sell herbs for Trade Gold, cook with them, or craft herbal cosmetics in Crafting (cosmetic only: they change your cat's look, no stats).",
    firstaid = "|cffffd100Make bandages|r: turn cloth into bandages. Cloth drops from enemies in Adventure and can be bought from the cloth merchant.\n\n|cffffd100Use|r: in Adventure your cat uses its best bandage when it gets hurt. Crafting has First Aid cosmetics (cosmetic only, no stats).",
    fishing = "|cffffd100Fish|r: cast and click when the bobber dips. A fishing buddy sits on the dock and catches fish for you, even while you're offline.\n\n|cffffd100Use|r: fish go into Cooking, sell for Trade Gold, and rare catches unlock fishing cosmetics in Crafting (cosmetic only, no stats).",
    cooking = "|cffffd100Cook|r: combine ingredients (meat, fish, herbs, spices) to discover recipes. Dishes give your cat a Well Fed buff, such as more Adventure damage or more cat XP.\n\n|cffffd100Use|r: eat dishes for buffs, or craft chef cosmetics in Crafting (cosmetic only, no stats).",
  }
  local guide = CreateFrame("Frame", nil, page, U.BT)
  guide:SetPoint("TOPLEFT", 10, -74); guide:SetPoint("BOTTOMRIGHT", -10, 10)
  if guide.SetFrameLevel and page.GetFrameLevel and page:GetFrameLevel() then guide:SetFrameLevel(page:GetFrameLevel() + 30) end
  if guide.SetBackdrop then guide:SetBackdrop(U.BACKDROP_DIALOG) end
  guide:EnableMouse(true)
  guide.title = Text(guide, "GameFontNormalLarge", nil, "LEFT"); guide.title:SetPoint("TOPLEFT", 22, -20)
  guide.body = Text(guide, "GameFontHighlight", nil, "LEFT"); guide.body:SetPoint("TOPLEFT", 22, -48); guide.body:SetWidth(490)
  if guide.body.SetSpacing then guide.body:SetSpacing(3) end
  if guide.body.SetJustifyV then guide.body:SetJustifyV("TOP") end
  local gotIt = Button(guide, "Got it", 100, 24, function() guide:Hide() end); gotIt:SetPoint("BOTTOMRIGHT", -18, 16)
  guide:Hide()
  local function showGuide(prof)
    guide.prof = prof
    local fam = TCF.FAMILIES[prof]
    local p = TCF.PROF_BY_KEY[prof]
    if fam then
      guide.title:SetText("How " .. fam.tab .. " works")
      guide.body:SetText(string.format(
        "|cffffd100Gather|r: buy %s, then hire %s so they keep working on their own, even while you're offline. Click a %s to %s by hand with your %s. Every cycle earns Trade Gold and %s.\n\n" ..
        "|cffffd100Craft|r: open %s to turn your %s into |cff20ff20real gear with stats|r for this class (it goes to your Gear tab) or |cffcc88ffcosmetics|r that only change your cat's look (marked Cosmetic only; they go to Appearance). Crafting raises your skill and unlocks new recipes up to 300. Locked recipes show the skill they need.\n\n" ..
        "|cffffd100Grow|r: spend Trade Gold on Upgrades. As this cat earns Trade Gold it unlocks Herbalism, First Aid, Fishing and Cooking. When your business is big, sell it for Renown: each point adds 2%% Trade Gold, so the gold comes faster. Selling never lowers the Trade Gold earned that unlocks professions, and you need a few rounds of selling to reach the later ones.\n\n" ..
        "|cff999999Each class has its own Trade Gold and professions.|r",
        fam.spotNounPlural, fam.hirePlural:lower(), fam.spotNoun, fam.verb:lower(), fam.toolNoun:lower(), fam.matNoun,
        fam.craftName, fam.matNoun))
    else
      guide.title:SetText("How " .. (p and p.name or "this profession") .. " works")
      guide.body:SetText((GUIDE_OTHER[prof] or "") .. "\n\n|cff999999Each class has its own Trade Gold and professions.|r")
    end
    guide:Show()
  end
  -- a small Help button right after the profession's name (the header has no room for more)
  local helpBtn = Button(page, "Help", 54, 20, function() showGuide(win.profSel or TCF:MainProf()) end)
  helpBtn:SetPoint("LEFT", profName, "RIGHT", 8, 0)
  Tip(helpBtn, function(tt)
    tt:AddLine("How it works", 1, 0.82, 0)
    tt:AddLine("What this profession does and how it gets you gear and cosmetics.", 1, 1, 1, true)
  end)
  TCF.ShowProfessionGuide = function(_, prof) showGuide(prof or win.profSel or TCF:MainProf()) end

  local shownKey
  refresh = function()
    local s = TCF:ProfState()
    local prof = currentProf()
    local fam = TCF.FAMILIES[prof]
    local p = TCF.PROF_BY_KEY[prof]
    local list = TCF:ProfList()
    for i, b in ipairs(ptabs) do
      local bp = list[i]
      if b.prof ~= bp then b.prof = bp; if bp then b.tex:SetTexture(TCF.Icon(bp.icon)) end end
      vis(b, bp)
      if bp then vis(b.sel, bp.key == prof); b.tex:SetDesaturated(not TCF:ProfUnlocked(bp.key)) end
    end
    if win.profView == "upg" and not fam then win.profView = "main" end
    local view = win.profView
    local unlocked = TCF:ProfUnlocked(prof)
    -- the first time each profession is opened, its guide explains it (remembered per account)
    TCF.db.profGuides = TCF.db.profGuides or {}
    local gkey = fam and "family" or prof
    if unlocked and not TCF.db.profGuides[gkey] then TCF.db.profGuides[gkey] = true; showGuide(prof)
    elseif guide:IsShown() and guide.prof ~= prof then guide:Hide() end
    -- header
    profName:SetText(p.name)
    local skillKey = (fam and view == "craft") and fam.craft or prof
    local skillProf = TCF.PROF_BY_KEY[skillKey] or p
    local skillName = skillProf.skillName or skillProf.name   -- "Cloth Scavenging", not a second "Tailoring"
    local skill = TCF:ProfSkill(skillKey)
    skillBar:SetMinMaxValues(0, 300); skillBar:SetValue(skill); skillBar.text:SetText(skillName .. " " .. skill .. " / 300")
    goldText:SetText(TCF.GoldStr(s.gold, 16))
    renownText:SetText(string.format("%s: Renown %d (+%d%% gold)", className(), s.renown, s.renown * 2))
    buyMode:SetText(s.buy == "max" and "Buy Max" or ("Buy x" .. s.buy))
    vis(buyMode, fam and view == "main" and unlocked)
    vbtns[1]:SetText(fam and fam.spotsTitle or MAIN[prof][3])
    vbtns[3]:SetText(fam and fam.craftName or "Crafting")
    vis(vbtns[2], fam)
    for _, b in ipairs(vbtns) do if b.key == view then b:LockHighlight() else b:UnlockHighlight() end end

    -- which view, and change visibility only when it changes
    local target, enter
    if not unlocked and view ~= "renown" then target = locked
    elseif view == "main" then
      if fam then target, enter = spotView, function() enterSpots(prof) end
      else target, enter = MAIN[prof][1], MAIN[prof][4] end
    elseif view == "upg" then target = upgView
    elseif view == "craft" then target, enter = craftView, function() enterCraft(fam and fam.craft or prof) end
    else target = renView end
    local key = prof .. ":" .. view .. ":" .. (unlocked and "1" or "0")
    if key ~= shownKey then
      shownKey = key
      for _, v in ipairs(allViews) do if v ~= target then vis(v, false) end end
      vis(target, true)
      if enter then enter() end
    end

    if target == locked then
      local have, need = TCF:ProfUnlockProgress(prof)
      lockText:SetText(string.format("%s unlocks when your %s cat has earned |cffffd100%s|r Trade Gold in total.\n\nSo far: %s (%d%%)\n\n" ..
        "Every bit of Trade Gold your professions earn counts, and selling your business for Renown never lowers it. It takes a few rounds of selling: each sale's Renown makes the gold come faster.\n\n|cffaaaaaa%s|r",
        p.name, className(), TCF.GoldStr(need), TCF.GoldStr(have), min(99, floor(100 * have / max(1, need))), PER_CLASS))
    elseif target == spotView then refreshSpots(prof)
    elseif target == upgView then refreshUpgrades(prof)
    elseif target == craftView then refreshCraft(fam and fam.craft or prof)
    elseif target == renView then refreshRenown()
    else MAIN[prof][2]() end
  end
  return refresh
end
