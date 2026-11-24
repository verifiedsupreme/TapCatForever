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
    local b = IconButton(page, 34)   -- (1.6.2) 34 (was 30): easier to hit in the small window
    b:SetPoint("TOPLEFT", 10 + (i - 1) * 36, -8)
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
    tt:AddLine(string.format("%s Trade Gold, Renown %d (+%d%% Trade Gold and goods).", TCF.GoldStr(s.gold), s.renown, s.renown * 2), 1, 1, 1, true)
    tt:AddLine(string.format("Trade Gold earned in total: %s. New professions unlock as this grows.", TCF.GoldStr(s.lifetime)), 1, 1, 1, true)
    tt:AddLine(PER_CLASS .. " Your other cats' helpers keep working while you play this one, and what they earn stays with them.", 0.7, 0.7, 0.7, true)
  end)

  local vbtns = {}
  -- (1.7.0) a fifth view for the main profession: Guild (ProfDepth.lua)
  for i, key in ipairs({ "main", "upg", "craft", "guild", "renown" }) do
    local b = Button(page, "", 86, 24, function() win.profView = key; TCF:PlaySound("click"); win:Refresh() end)
    b:SetPoint("TOPLEFT", 12 + (i - 1) * 88, -47)
    b.key = key
    vbtns[i] = b
  end
  vbtns[2]:SetText("Upgrades"); vbtns[4]:SetText("Guild"); vbtns[5]:SetText("Renown")
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
    r.box:SetScript("OnClick", function()
      if TCF.WorkshopRowClick then TCF:WorkshopRowClick(FAM(), r.spot) end
      TCF:RunOp(FAM(), r.spot); TCF:PlaySound("click"); win:Refresh()
    end)
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
    r.bar:EnableMouse(true); r.bar:SetScript("OnMouseUp", function()
      if TCF.WorkshopRowClick then TCF:WorkshopRowClick(FAM(), r.spot) end
      TCF:RunOp(FAM(), r.spot); win:Refresh()
    end)
    r.info = Text(r, "GameFontDisableSmall", nil, "LEFT"); r.info:SetPoint("BOTTOMLEFT", r.box, "BOTTOMRIGHT", 8, 2); r.info:SetWidth(258)
    if r.info.SetWordWrap then r.info:SetWordWrap(false) end
    -- the hand tool: click to gather by hand
    r.pick = IconButton(r, 40); r.pick:SetPoint("RIGHT", -130, 0)
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
    -- (1.7.0) a glint: the tool sparkles gold for a moment (Workshop.lua)
    r.glint = r:CreateTexture(nil, "OVERLAY", nil, 6); r.glint:SetSize(64, 64); r.glint:SetPoint("CENTER", r.pick, "CENTER")
    r.glint:SetTexture(TCF.ART_PATH .. "v\\t_sparkle"); r.glint:SetVertexColor(1, 0.85, 0.3); r.glint:SetBlendMode("ADD"); r.glint:Hide()
    r.pick:SetScript("OnClick", function()
      local fam, i = FAM(), r.spot
      if TCF.WorkshopRowClick then TCF:WorkshopRowClick(fam, i) end
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
    -- (1.6.2) both buttons as tall as the row allows, so they are easy to hit in the small window too
    r.buy = Button(r, "Buy", 116, 24, function() TCF:BuyOp(FAM(), r.spot, TCF:ProfState().buy); win:Refresh() end)
    r.buy:SetPoint("TOPRIGHT", -5, -4)
    Tip(r.buy, function(tt)
      local f = FT()
      tt:AddLine("Buy " .. f.ops[r.spot][1], 1, 0.82, 0)
      local open, why = TCF:SpotUnlocked(FAM(), r.spot)
      if not open then tt:AddLine(why, 1, 0.5, 0.3, true) end
      tt:AddLine("Each one you own adds to the gold of every cycle here. Owning 25, 50, 100 and more makes the cycle twice as fast each time.", 1, 1, 1, true)
    end)
    r.mgr = Button(r, "", 116, 24, function() TCF:HireForeman(FAM(), r.spot); win:Refresh() end)
    r.mgr:SetPoint("BOTTOMRIGHT", -5, 4)
    Tip(r.mgr, function(tt)
      local f = FT()
      local h = TCF.HelperInfo and TCF:HelperInfo(FAM(), r.spot)
      if h then
        -- (1.7.0) the helper: name, level, trait (Workshop.lua)
        tt:AddLine(string.format("%s, your %s (level %d)", h.name, f.hire:lower(), h.level), 1, 0.82, 0)
        tt:AddLine(string.format("%s: %s.", h.trait.name, h.trait.text), 0.4, 1, 0.4, true)
        tt:AddLine(string.format("Brings %d%% more goods from its level. Gets better as it works, up to level %d.", (h.level - 1) * 2, TCF.HELPER_MAX_LEVEL), 1, 1, 1, true)
        if h.level < TCF.HELPER_MAX_LEVEL then tt:AddLine(string.format("Next level: %s / %s cycles worked.", TCF.FormatBig(floor(h.xp)), TCF.FormatBig(h.next)), 0.7, 0.7, 0.7) end
        return
      end
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
  speedBtn:Hide(); speedBtn.Show = function() end   -- Hand speed taken out in 1.6 testing
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
    tt:AddLine(string.format("Every 15 levels also adds another roll for %s. Click cooldown: %.2fs (shortens a little each level, down to 0.75s).", f.matNoun,
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
      spotHint:SetText(string.format("By hand: %.1f clicks a second. A better %s makes each click a little faster.", TCF:ClicksPerSecond(fam), f.toolNoun:lower()))
    end
    local lvl = TCF:ToolLevel(fam)
    local gskill = TCF:ProfSkill(fam)
    placeRows(fam)
    local total = spotTotal()
    vis(spotPage, total > SPOT_ROWS); vis(spotUp, total > SPOT_ROWS); vis(spotDown, total > SPOT_ROWS)
    spotPage:SetText(string.format("%d-%d of %d", win.spotScroll + 1, win.spotScroll + SPOT_ROWS, total))
    spotUp:SetEnabled(win.spotScroll > 0); spotDown:SetEnabled(win.spotScroll < total - SPOT_ROWS)
    local glitch = TCF:Glitch()
    -- (1.7.0) glints and spot events while the page is open (Workshop.lua)
    local shown = {}
    for _, r in ipairs(rows) do shown[#shown + 1] = r.spot end
    if TCF.WorkshopTick then TCF:WorkshopTick(shown) end
    local gl = TCF.WorkshopGlint and TCF:WorkshopGlint()
    local ev = TCF.WorkshopEvent and TCF:WorkshopEvent()
    local combo = TCF.WorkshopCombo and TCF:WorkshopCombo() or 0
    if ev and ev.text then
      local left = max(0, floor(ev.ends - GetTime() + 0.5))
      local extra = ev.kind == "stash" and string.format("  |cffffffff%d / %d|r", ev.clicks, TCF.STASH_CLICKS) or ""
      spotHint:SetText(string.format("|cffffd100%s|r%s  |cff999999(%ds)|r", ev.text, extra, left))
    elseif combo > 0 then
      spotHint:SetText(string.format("|cffffd100Glint combo %d|r: rare finds are %d%% likelier. Click the next sparkling %s by hand in time to keep it going.",
        combo, floor(min(3, 1 + 0.25 * combo) * 100 - 100 + 0.5), f.toolNoun:lower()))
    end
    for _, r in ipairs(rows) do
      local i = r.spot
      local glinting = gl and gl.fam == fam and gl.i == i and GetTime() < gl.ends
      if glinting then
        r.glint:Show(); r.glint:SetAlpha(0.6 + 0.4 * math.sin(GetTime() * 12))
        if r.glint.SetRotation then r.glint:SetRotation(GetTime() * 2) end
        r.pick.sel:Show(); r.pick.sel:SetVertexColor(1, 0.8, 0.2); r.pick.sel:SetAlpha(0.7 + 0.3 * math.sin(GetTime() * 14))
        r.pickLabel:SetText("|cffffd100Glint x5|r")
      else
        r.glint:Hide(); r.pick.sel:Hide()
        r.pickLabel:SetText("By hand")
      end
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
      elseif ev and ev.i == i and ev.kind == "rich" then r.name:SetText("|cffffd100x3|r " .. skillColor(gskill, TCF.SpotDifficulty(i)) .. o[1] .. "|r")
      elseif ev and ev.i == i and ev.kind == "stash" then r.name:SetText("|cffff8040Stash|r " .. skillColor(gskill, TCF.SpotDifficulty(i)) .. o[1] .. "|r")
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
      -- (1.7.0) the exact count below 10 million, so every click shows
      local have = floor(s.mats[o[2]] or 0)
      r.info:SetText(string.format("|cffcccccc%s %s|r   %s", have < 1e7 and TCF.Commas(have) or TCF.FormatBig(have), o[3],
        nextMs and string.format("Next speed boost at %d", nextMs) or "Max speed"))
      local canPick = i == 1 or st.n > 0
      r.pick:SetEnabled(canPick); r.pick.tex:SetDesaturated(not canPick)
      r.pick.count:SetText(lvl > 0 and lvl or "")
      local count = s.buy == "max" and max(1, TCF:OpMaxBuy(fam, i)) or s.buy
      local bcost = TCF:OpCost(fam, i, count)
      if open then r.buy:SetText("x" .. count .. "  " .. TCF.GoldStr(bcost, 10)); r.buy:SetEnabled(s.gold >= bcost)
      else r.buy:SetText("|cff888888Locked|r"); r.buy:SetEnabled(false) end
      local fcost = TCF.PROF_OPS[i].foreman
      local h = st.mgr and TCF.HelperInfo and TCF:HelperInfo(fam, i)
      if h then r.mgr:SetText(string.format("|cff20ff20%s|r  Lv %d", h.name, h.level)); r.mgr:SetEnabled(false)
      elseif st.mgr then r.mgr:SetText("|cff20ff20Automated|r"); r.mgr:SetEnabled(false)
      -- (1.6.2) "Hire" and the price fit the button on one line; the tooltip names the helper
      else r.mgr:SetText("Hire " .. TCF.GoldStr(fcost, 10)); r.mgr:SetEnabled(st.n > 0 and s.gold >= fcost) end
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
  -- (1.6.7) 26 seeds in pages of 8, a seed per plot (right-click: grow the picked seed there next,
  -- shift-right-click: dig up and plant it now), and a button to grow it in every plot. The
  -- gardener and the garden upgrades have their own view (the second button: Gardener).
  local gardenView = View()
  win.seedSel = win.seedSel or "peacebloom"
  local SEED_PAGE = 8
  local seedBtns = {}
  local function seedPages() return math.ceil(#TCF.SEEDS / SEED_PAGE) end
  local function pageOf(key) local sd = TCF.SEED_BY_KEY[key]; return sd and floor((sd.index - 1) / SEED_PAGE) or 0 end
  local seedPrev = Button(gardenView, "<", 22, 32, function() win.seedPage = max(0, (win.seedPage or 0) - 1); win:Refresh() end)
  seedPrev:SetPoint("TOPLEFT", 6, -4)
  local seedNext = Button(gardenView, ">", 22, 32, function() win.seedPage = min(seedPages() - 1, (win.seedPage or 0) + 1); win:Refresh() end)
  seedNext:SetPoint("TOPRIGHT", -10, -4)
  gardenView:EnableMouseWheel(true)
  gardenView:SetScript("OnMouseWheel", function(_, d)
    win.seedPage = min(seedPages() - 1, max(0, (win.seedPage or 0) - d)); win:Refresh()
  end)
  for i = 1, SEED_PAGE do
    local b = IconButton(gardenView, 32); b:SetPoint("TOPLEFT", 40 + (i - 1) * 61, -4)
    b.price = Text(gardenView, "GameFontHighlightSmall"); b.price:SetPoint("TOP", b, "BOTTOM", 0, -2); b.price:SetWidth(62)
    b:SetScript("OnClick", function()
      local sd = b.seed
      if not sd then return end
      if TCF:ProfSkill("herbalism") >= sd[7] then win.seedSel = sd[1]; win.gardenMsg = nil
      else win.gardenMsg = { "|cffff5050" .. sd[2] .. " unlocks at Herbalism skill " .. sd[7] .. ". Harvest herbs (or brew potions) to raise your skill.|r", GetTime() + 4 } end
      win:Refresh()
    end)
    Tip(b, function(tt)
      local sd = b.seed
      if not sd then return end
      tt:AddLine(sd[2] .. " seeds", 1, 0.82, 0)
      tt:AddLine(string.format("Grows in %s. Seed: %s. Sells for %s per herb.", TCF.FormatDuration(sd[4]), TCF.GoldStr(sd[5]), TCF.GoldStr(sd[6])), 1, 1, 1, true)
      if sd.rare then
        local rh = TCF.RARE_BY_KEY[sd.rare[1]]
        tt:AddLine("Sometimes brings " .. (rh and rh.name or sd.rare[1]) .. " too.", 0.64, 0.4, 1, true)
      end
      if TCF:ProfSkill("herbalism") < sd[7] then tt:AddLine("Needs Herbalism " .. sd[7], 1, 0.3, 0.3)
      else addTeachLine(tt, TCF:ProfSkill("herbalism"), sd.teach or sd[7]) end
    end)
    seedBtns[i] = b
  end
  local seedHint = Text(gardenView, "GameFontHighlightSmall", nil, "LEFT")
  seedHint:SetPoint("TOPLEFT", 12, -56); seedHint:SetWidth(520)
  local plots = {}
  local function plotMsg(ok, why) win.gardenMsg = (not ok and why) and { "|cffff5050" .. why .. "|r", GetTime() + 4 } or nil end
  for i = 1, TCF.GARDEN_MAX_PLOTS do
    local p = CreateFrame("Button", nil, gardenView, U.BT)
    p:SetSize(126, 62); p:SetPoint("TOPLEFT", 12 + ((i - 1) % 4) * 131, -88 - floor((i - 1) / 4) * 66)
    if p.SetBackdrop then p:SetBackdrop(U.BACKDROP_PANEL); p:SetBackdropColor(0.20, 0.14, 0.08, 0.95) end
    p.icon = p:CreateTexture(nil, "ARTWORK"); p.icon:SetSize(28, 28); p.icon:SetPoint("TOPLEFT", 6, -6)
    p.name = Text(p, "GameFontNormalSmall", nil, "LEFT"); p.name:SetPoint("LEFT", p.icon, "RIGHT", 4, 0); p.name:SetWidth(70)
    -- the seed it grows next, when that's not what grows now
    p.nextIcon = p:CreateTexture(nil, "OVERLAY"); p.nextIcon:SetSize(16, 16); p.nextIcon:SetPoint("TOPRIGHT", -5, -5); p.nextIcon:Hide()
    p.bar = Bar(p, 112, 12, 0.3, 0.8, 0.3); p.bar:SetPoint("BOTTOM", 0, 8)
    p:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    if p.RegisterForClicks then p:RegisterForClicks("LeftButtonUp", "RightButtonUp") end
    p:SetScript("OnClick", function(_, button)
      local g = TCF:GardenState()
      local ok, why
      if i == g.n + 1 then
        ok = TCF:BuyPlot()
        if not ok then why = "Not enough Trade Gold for this plot (" .. TCF.GoldStr(TCF:PlotCost(g.n + 1)) .. ")." end
      elseif i > g.n + 1 then
        -- plots are bought in order: a locked plot further out does nothing
        ok, why = false, "Buy plot " .. (g.n + 1) .. " first."
      elseif button == "RightButton" then
        if IsShiftKeyDown and IsShiftKeyDown() then ok, why = TCF:PlotDig(i, win.seedSel)
        else ok, why = TCF:PlotSetNext(i, win.seedSel) end
      else
        local plot = g.plots[i]
        -- an empty plot plants the seed you picked (and remembers it)
        ok, why = TCF:PlotClick(i, (plot and plot.seed) and nil or win.seedSel)
      end
      plotMsg(ok, why)
      win:Refresh()
    end)
    Tip(p, function(tt)
      local g = TCF:GardenState()
      if i > g.n then
        tt:AddLine(i == g.n + 1 and "Buy this plot" or "Locked plot", 1, 0.82, 0)
        tt:AddLine(i == g.n + 1 and ("Costs " .. TCF.GoldStr(TCF:PlotCost(i)) .. ".") or ("Buy plot " .. (g.n + 1) .. " first."), 1, 1, 1, true)
        return
      end
      local plot = g.plots[i]
      local sd = plot and TCF.SEED_BY_KEY[plot.seed]
      local want = TCF.SEED_BY_KEY[TCF:PlotWant(i) or ""]
      tt:AddLine(string.format("Plot %d%s", i, sd and (": " .. sd[2]) or ""), 1, 0.82, 0)
      if want and (not sd or want ~= sd) then
        tt:AddLine(string.format("Grows %s next%s.", want[2], TCF:GardenerLevel() >= 1 and " (Bramble plants it)" or ""), 0.4, 1, 0.4, true)
      end
      local sel = TCF.SEED_BY_KEY[win.seedSel]
      tt:AddLine(sd and "Click: water it, or harvest it when it's ripe." or ("Click: plant " .. (sel and sel[2] or "the seed you picked") .. "."), 1, 1, 1, true)
      if sel then
        tt:AddLine("Right-click: grow " .. sel[2] .. " here from the next harvest on.", 0.8, 0.8, 0.8, true)
        if sd then tt:AddLine("Shift-right-click: dig it up and plant " .. sel[2] .. " now (what grows is lost).", 0.8, 0.8, 0.8, true) end
      end
    end)
    plots[i] = p
  end
  -- grow the picked seed in every plot
  local plantAll = Button(gardenView, "Grow it in every plot", 258, 22, function()
    local ok, why = TCF:GardenPlantAll(win.seedSel)
    plotMsg(ok, why)
    win:Refresh()
  end)
  plantAll:SetPoint("TOPLEFT", 12, -292)
  Tip(plantAll, function(tt)
    local sel = TCF.SEED_BY_KEY[win.seedSel]
    tt:AddLine("Grow " .. (sel and sel[2] or "it") .. " in every plot", 1, 0.82, 0)
    tt:AddLine("Empty plots are planted now. Growing plots finish what they have, then grow this one from their next harvest on (Bramble the gardener replants them).", 1, 1, 1, true)
  end)
  local gardenerLine = Text(gardenView, "GameFontHighlightSmall", nil, "LEFT")
  gardenerLine:SetPoint("LEFT", plantAll, "RIGHT", 10, 0); gardenerLine:SetWidth(258)
  -- rare herbs and the potion you're under
  local rareLine = Text(gardenView, "GameFontHighlightSmall", nil, "LEFT"); rareLine:SetPoint("TOPLEFT", 12, -324); rareLine:SetWidth(520)
  local gardenNote = Text(gardenView, "GameFontHighlightSmall", nil, "LEFT"); gardenNote:SetPoint("TOPLEFT", 12, -344); gardenNote:SetWidth(520)
  local function refreshGarden()
    local g, s = TCF:GardenState()
    local skill = TCF:ProfSkill("herbalism")
    if win.seedPage == nil then win.seedPage = pageOf(win.seedSel) end
    win.seedPage = min(max(0, win.seedPage), seedPages() - 1)
    seedPrev:SetEnabled(win.seedPage > 0); seedNext:SetEnabled(win.seedPage < seedPages() - 1)
    for k, b in ipairs(seedBtns) do
      local sd = TCF.SEEDS[win.seedPage * SEED_PAGE + k]
      b.seed = sd
      vis(b, sd); vis(b.price, sd)
      if sd then
        b.tex:SetTexture(TCF.Icon(sd[3]))
        b.sel:SetShown(win.seedSel == sd[1]); b.tex:SetDesaturated(skill < sd[7])
        b.count:SetText((s.mats[sd[1]] or 0) > 0 and TCF.FormatBig(s.mats[sd[1]]) or "")
        b.price:SetText(skill < sd[7] and ("|cff888888Skill " .. sd[7] .. "|r")
          or ((s.gold >= sd[5] and "|cffffd100" or "|cffff5050") .. TCF.FormatBig(sd[5]) .. "|r"))
      end
    end
    -- what clicking an empty plot will do (or why the last click didn't work)
    local sel = TCF.SEED_BY_KEY[win.seedSel]
    if win.gardenMsg and GetTime() < win.gardenMsg[2] then
      seedHint:SetText(win.gardenMsg[1])
    elseif sel then
      seedHint:SetText(string.format("Planting |cffffd100%s|r: seeds cost %s, grows in %s, sells for %s. Click an empty plot to plant, right-click a plot to grow it there next. Click growing plots to water them.",
        sel[2], TCF.GoldStr(sel[5]), TCF.FormatDuration(sel[4]), TCF.GoldStr(sel[6])))
    end
    plantAll:SetText(sel and ("Grow " .. sel[2] .. " in every plot") or "Grow it in every plot")
    fitText(plantAll)
    for i, p in ipairs(plots) do
      local plot = g.plots[i]
      local want = i <= g.n and TCF.SEED_BY_KEY[TCF:PlotWant(i) or ""]
      if i > g.n then
        p.icon:SetTexture(TCF.Icon("INV_Misc_Bag_10")); p.icon:SetDesaturated(true)
        p.name:SetText(i == g.n + 1 and ("Buy plot\n" .. TCF.GoldStr(TCF:PlotCost(i), 10)) or "|cff666666Locked|r")
        p.bar:Hide(); p.nextIcon:Hide()
      elseif plot and plot.seed then
        local sd = TCF.SEED_BY_KEY[plot.seed]
        p.icon:SetTexture(TCF.Icon(sd[3])); p.icon:SetDesaturated(false)
        p.bar:Show(); p.bar:SetMinMaxValues(0, sd[4]); p.bar:SetValue(plot.grown)
        local left = (sd[4] - plot.grown) / TCF:GardenSpeed()
        p.name:SetText(sd[2]); p.bar.text:SetText(left <= 0 and "|cff20ff20Ready to harvest|r" or TCF.FormatDuration(left))
        if want and want ~= sd then p.nextIcon:SetTexture(TCF.Icon(want[3])); p.nextIcon:Show() else p.nextIcon:Hide() end
      else
        p.icon:SetTexture(TCF.Icon(want and want[3] or "INV_Misc_Flower_02")); p.icon:SetDesaturated(true)
        p.name:SetText(want and ("|cffaaaaaaEmpty|r\n|cff888888" .. want[2] .. "|r") or "|cffaaaaaaEmpty plot|r"); p.bar:Hide(); p.nextIcon:Hide()
      end
    end
    local gl = TCF:GardenerLevel()
    gardenerLine:SetText(gl >= 1 and string.format("|cff20ff20%s|r, %s Gardener, tends the garden.", TCF.GARDENER_NAME, TCF.GARDENER[gl].rank)
      or "|cffaaaaaaNo gardener yet: hire Bramble in Gardener.|r")
    local parts = {}
    for _, r in ipairs(TCF.RARE_HERBS) do
      parts[#parts + 1] = string.format("%s |cffa335ee%d|r", r.name, s.mats[r.key] or 0)
    end
    rareLine:SetText("Rare herbs:  " .. table.concat(parts, "   "))
    local pot = TCF:PotionLine()
    gardenNote:SetText(pot and ("|cff20ff20" .. pot .. "|r") or "|cff999999Brew potions from your herbs in Crafting.|r")
  end

  ------------------------------------------------ Herbalism: the gardener and the garden upgrades (1.6.7)
  local gardenerView = View()
  local gCard = Panel(gardenerView, 532, 150, 0.85); gCard:SetPoint("TOP", 0, -2)
  gCard.icon = gCard:CreateTexture(nil, "ARTWORK"); gCard.icon:SetSize(44, 44); gCard.icon:SetPoint("TOPLEFT", 10, -10)
  gCard.icon:SetTexture(TCF.Icon("Trade_Herbalism"))
  gCard.title = Text(gCard, "GameFontNormalLarge", nil, "LEFT"); gCard.title:SetPoint("TOPLEFT", 64, -10); gCard.title:SetWidth(280)
  gCard.sub = Text(gCard, "GameFontHighlightSmall", nil, "LEFT"); gCard.sub:SetPoint("TOPLEFT", 64, -34); gCard.sub:SetWidth(440)
  gCard.perks = {}
  for k = 1, #TCF.GARDENER do
    local fs = Text(gCard, "GameFontHighlightSmall", nil, "LEFT"); fs:SetPoint("TOPLEFT", 14, -58 - (k - 1) * 17); fs:SetWidth(504)
    if fs.SetWordWrap then fs:SetWordWrap(false) end
    gCard.perks[k] = fs
  end
  local trainBtn = Button(gCard, "Hire", 170, 24, function()
    local ok, why = TCF:TrainGardener()
    if not ok and why then win.gardenerMsg = { "|cffff5050" .. why .. "|r", GetTime() + 4 } else win.gardenerMsg = nil end
    TCF:PlaySound("click")
    win:Refresh()
  end)
  trainBtn:SetPoint("TOPRIGHT", -10, -12)
  Tip(trainBtn, function(tt)
    local gl = TCF:GardenerLevel()
    local nxt = TCF.GARDENER[gl + 1]
    if not nxt then tt:AddLine("Bramble is a Master Gardener", 1, 0.82, 0); return end
    tt:AddLine(gl == 0 and "Hire Bramble" or ("Train Bramble to " .. nxt.rank), 1, 0.82, 0)
    tt:AddLine(nxt.perk, 1, 1, 1, true)
    tt:AddLine("Cost: " .. TCF.GoldStr(nxt.cost), 1, 1, 1)
  end)
  local upHead = Text(gardenerView, "GameFontNormal", nil, "LEFT"); upHead:SetPoint("TOPLEFT", 14, -162); upHead:SetText("Garden upgrades")
  local gUps = {}
  for i, u in ipairs(TCF.GARDEN_UPGRADES) do
    local b = UpgradeButton(gardenerView, 258, function() return u end, function() TCF:BuyGardenUpgrade(u.key); win:Refresh() end,
      function() return TCF:GardenState().up[u.key] end)
    b:SetPoint("TOPLEFT", 12 + ((i - 1) % 2) * 264, -182 - floor((i - 1) / 2) * 26)
    gUps[i] = b
  end
  local gStats = Text(gardenerView, "GameFontHighlightSmall", nil, "LEFT"); gStats:SetPoint("TOPLEFT", 14, -266); gStats:SetWidth(516)
  local gRare = Text(gardenerView, "GameFontHighlightSmall", nil, "LEFT"); gRare:SetPoint("TOPLEFT", 14, -290); gRare:SetWidth(516)
  local function refreshGardener()
    local g, s = TCF:GardenState()
    local gl = TCF:GardenerLevel()
    gCard.title:SetText(gl >= 1 and string.format("%s, %s Gardener", TCF.GARDENER_NAME, TCF.GARDENER[gl].rank) or "No gardener yet")
    fitText(gCard.title)
    gCard.icon:SetDesaturated(gl < 1)
    if win.gardenerMsg and GetTime() < win.gardenerMsg[2] then gCard.sub:SetText(win.gardenerMsg[1])
    else
      gCard.sub:SetText(gl >= 1 and "Tends your garden, even while you're offline."
        or "Hire Bramble to tend your garden, even offline.")
    end
    for k, fs in ipairs(gCard.perks) do
      local e = TCF.GARDENER[k]
      local col = k <= gl and "|cff20ff20" or (k == gl + 1 and "|cffffd100" or "|cff888888")
      fs:SetText(string.format("%s%s:|r %s%s|r", col, e.rank, k <= gl and "|cffffffff" or "|cff999999", e.perk))
    end
    local nxt = TCF.GARDENER[gl + 1]
    if nxt then
      trainBtn:SetText((gl == 0 and "Hire  " or ("Train: " .. nxt.rank .. "  ")) .. TCF.GoldStr(nxt.cost, 10))
      trainBtn:SetEnabled(s.gold >= nxt.cost)
    else
      trainBtn:SetText("|cff20ff20Master Gardener|r"); trainBtn:SetEnabled(false)
    end
    fitText(trainBtn)
    for _, b in ipairs(gUps) do b:Update() end
    gStats:SetText(string.format("Harvests: |cffffffff%s|r   Rare herbs found: |cffa335ee%s|r   Seeds Bramble saved: |cffffffff%s|r   Growth speed: |cffffffff%d%%|r",
      TCF.FormatBig(g.harvests or 0), TCF.FormatBig(g.rares or 0), TCF.FormatBig(g.saved or 0), floor(TCF:GardenSpeed() * 100 + 0.5)))
    local parts = {}
    for _, r in ipairs(TCF.RARE_HERBS) do parts[#parts + 1] = string.format("|cffa335ee%s|r from %s", r.name, TCF.RareSources(r.key)) end
    gRare:SetText("Rare herbs come with some harvests: " .. table.concat(parts, "; ") .. ". They go into the best potions.")
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
    if rec.potion then
      -- (1.6.7) a potion: what it does, how long, and the one-at-a-time rule
      GameTooltip:AddLine("|c" .. TCF.RARITY[it.rarity].hex .. it.name .. "|r")
      GameTooltip:AddLine("Drink: " .. TCF.PotionEffectText(it, TCF:PotionMinutes(it)) .. ".", 0.2, 1, 0.2, true)
      GameTooltip:AddLine("One potion at a time: drinking another replaces it. It counts on top of a Well Fed dish.", 0.8, 0.8, 0.8, true)
      local have = TCF:ProfState().mats[it.id] or 0
      GameTooltip:AddLine(string.format("You have %d.", have), 1, 1, 1)
    elseif rec.gear then
      TCF:GearTooltip(GameTooltip, it)
    else
      TCF:ItemTooltip(GameTooltip, it, true)   -- already says "Cosmetic only (no stats)"
    end
    if not rec.potion then TCF.UI.ShowTryOn(win, it) end
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
    if rec.potion then GameTooltip:AddLine("Brewing raises your Herbalism skill.", 0.7, 0.7, 0.7, true)
    else TCF.UI.PreviewHint(GameTooltip, win, it) end
    if rec.starter then
      local done, total = TCF:StarterProgress(rec.prof)
      GameTooltip:AddLine(string.format("Starter set (%d/%d made): a cheap white piece for each slot, so a new cat can wear a full crafted set.", done, total), 0.88, 0.75, 0.5, true)
    end
    GameTooltip:Show()
  end
  local function recipeLeave()
    GameTooltip:Hide()
    TCF.UI.HideTryOn(win)
  end
  for i = 1, CROWS do
    local r = Panel(craftView, 532, 48, 0.85); r:SetPoint("TOP", 0, -22 - (i - 1) * 50)
    r.gearBtn = U.GearButton(r, 40); r.gearBtn:SetPoint("LEFT", 5, 0); r.gearBtn:Hide()
    r.cell = U.ItemCell(r, 40); r.cell:SetPoint("LEFT", 5, 0); r.cell:Hide()
    for _, b in ipairs({ r.gearBtn, r.cell }) do
      b:SetScript("OnEnter", function(s) recipeEnter(r, s) end)
      b:SetScript("OnLeave", recipeLeave)
      -- (1.6.3) shift-click the picture: try the item on the cat
      b:SetScript("OnClick", function(s)
        local it = r.recipe and TCF:RecipeItem(r.recipe)
        if it and TCF.UI.PreviewClick(win, it) then recipeEnter(r, s) end
      end)
    end
    r:SetScript("OnEnter", function(s) recipeEnter(r, s) end)
    r:SetScript("OnLeave", recipeLeave)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("TOPLEFT", 52, -4); r.name:SetWidth(350)
    r.info = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.info:SetPoint("LEFT", 52, -1); r.info:SetWidth(350)
    r.need = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.need:SetPoint("BOTTOMLEFT", 52, 4); r.need:SetWidth(350)
    for _, fs in ipairs({ r.name, r.info, r.need }) do if fs.SetWordWrap then fs:SetWordWrap(false) end end
    r.delta = Text(r, "GameFontNormal", nil, "RIGHT"); r.delta:SetPoint("RIGHT", -124, 0)
    -- (1.6.7) potions: their icon, and a Drink button left of Brew
    r.pot = CreateFrame("Button", nil, r); r.pot:SetSize(40, 40); r.pot:SetPoint("LEFT", 5, 0)
    r.pot.tex = r.pot:CreateTexture(nil, "ARTWORK"); r.pot.tex:SetAllPoints()
    r.pot.count = Text(r.pot, "NumberFontNormal", nil, "RIGHT"); r.pot.count:SetPoint("BOTTOMRIGHT", 2, -2)
    r.pot:SetScript("OnEnter", function(s) recipeEnter(r, s) end)
    r.pot:SetScript("OnLeave", recipeLeave)
    r.pot:Hide()
    r.drink = Button(r, "Drink", 58, 22, function()
      if r.recipe and r.recipe.potion then
        local ok, why = TCF:DrinkPotion(r.recipe.potion)
        if not ok and why then TCF:Print(why) end
        win:Refresh()
      end
    end)
    r.drink:SetPoint("RIGHT", -120, 0); r.drink:Hide()
    Tip(r.drink, function(tt)
      local it = r.recipe and TCF:RecipeItem(r.recipe)
      if not it then return end
      tt:AddLine("Drink " .. it.name, 1, 0.82, 0)
      tt:AddLine(TCF.PotionEffectText(it, TCF:PotionMinutes(it)) .. ".", 1, 1, 1, true)
      local cur = TCF:PotionLine()
      if cur then tt:AddLine("Replaces " .. cur .. ".", 1, 0.5, 0.3, true) end
    end)
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
      tt:AddLine(n > 1 and string.format("Craft %d", n) or "Craft many", 1, 0.82, 0)
      if n > 0 then tt:AddLine(string.format("Makes %d with the materials you have (at most %d with one click).", n, TCF.CRAFT_ALL_MAX), 1, 1, 1, true)
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
      if key == "herbalism" then
        -- (1.6.7) potions are here too: the one you're under, or how they work
        local b = TCF:PotionActive()
        local pit = b and TCF.POTION_BY_KEY[b.key]
        if pit then
          craftLegend:SetText(string.format("|cff20ff20%s|r (%s left)", pit.name, TCF.FormatDuration(b["until"] - time())))
          local lw = textWidth(craftLegend)
          if type(lw) == "number" and lw > 238 then craftLegend:SetText(string.format("|cff20ff20Potion:|r %s left", TCF.FormatDuration(b["until"] - time()))) end
        else
          craftLegend:SetText("Brew potions, drink one for a buff.")
        end
      else
        craftLegend:SetText("Cosmetics change your cat's look only.")
      end
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
        vis(r.pot, rec.potion); vis(r.drink, rec.potion and (s.mats[rec.potion] or 0) > 0)
        r.craft:SetText(rec.potion and "Brew" or "Craft")
        if rec.potion then
          vis(r.cell, false); vis(r.gearBtn, false)
          r.pot.tex:SetTexture(TCF.Icon(it.icon)); r.pot.tex:SetDesaturated(lockedRow); r.pot.tex:SetAlpha(lockedRow and 0.55 or 1)
          local have = s.mats[it.id] or 0
          r.pot.count:SetText(have > 0 and have or "")
          local col = lockedRow and "|cff888888" or ("|c" .. TCF.RARITY[it.rarity].hex)
          r.name:SetText(col .. it.name .. "|r" .. skillTxt)
          r.info:SetText("|cff66ccffPotion|r  |cffcccccc" .. TCF.PotionEffectText(it, TCF:PotionMinutes(it)) .. "|r")
          r.delta:SetText("")
          r.drink:SetEnabled(have > 0)
        elseif rec.gear then
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
        -- (1.6.7) the button says how many it makes ("x12", "x50"), so "All" never means 50
        local nAll = TCF:CraftCount(rec)
        r.all:SetText("x" .. nAll)
        r.all:SetEnabled(nAll > 1)
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
  local renInfo = Text(renView, "GameFontHighlightSmall", nil, "LEFT"); renInfo:SetPoint("TOPLEFT", 16, -8); renInfo:SetWidth(520); renInfo:SetSpacing(3)
  local renBtn = Button(renView, "Sell the business", 180, 26, function()
    if IsShiftKeyDown() then TCF:PrestigeTrade() else TCF:Print("Shift-click to sell everything you bought with Trade Gold for Renown.", true) end
  end)
  renBtn:SetPoint("TOPLEFT", 16, -234)
  local function refreshRenown()
    local s = TCF:ProfState()
    local gain = TCF:RenownOnReset()
    local unlocks = {}
    for _, p in ipairs(TCF:ProfList()) do
      if (p.gold or 0) > 0 then unlocks[#unlocks + 1] = string.format("%s%s at %s|r", TCF:ProfUnlocked(p.key) and "|cff20ff20" or "|cffaaaaaa", p.name, TCF.FormatBig(p.gold)) end
    end
    renInfo:SetText(string.format(
      "%s Your %s cat's business:\n\n" ..
      "|cffffd100Renown|r is permanent: each point adds +2%% to this cat's Trade Gold and to the goods its spots gather (ore, leather, cloth), so it earns faster.\n\n" ..
      "Current Renown: |cffffffff%d|r (highest ever %d)\nTrade Gold earned in total: |cffffffff%s|r\nRenown you'd gain by selling now: |cff20ff20%d|r  (+%d TapCoins)\n\n" ..
      "New professions unlock at Trade Gold earned in total (selling never lowers it): %s\n\nSelling resets this cat's Trade Gold, %s, %s, garden plots, %s, helpers and upgrades. " ..
      "You keep skills, recipes, materials, crafted gear, bandages, dishes and unlocked professions. Your other cats keep their own business.",
      PER_CLASS, className(), s.renown, s.renownEver, TCF.GoldStr(s.lifetime, 12), gain, min(1000, gain * 3), table.concat(unlocks, ", "),
      FT().spotsTitle:lower(), FT().toolNoun:lower(), FT().hirePlural:lower()))
    renBtn:SetEnabled(gain >= 5)
  end


  ------------------------------------------------ (1.7.0) Renown shop: perks bought with Renown points (ProfDepth.lua)
  local perkBtns = {}
  local perkHead = Text(renView, "GameFontNormal", nil, "LEFT"); perkHead:SetPoint("TOPLEFT", 16, -266); perkHead:SetWidth(520)
  for k, p in ipairs(TCF.RENOWN_PERKS) do
    local b = Button(renView, "", 258, 22, function()
      local ok, why = TCF:BuyRenownPerk(p.key)
      if not ok and why then TCF:Print(why) end
      win:Refresh()
    end)
    b:SetPoint("TOPLEFT", 12 + ((k - 1) % 2) * 264, -284 - floor((k - 1) / 2) * 25)
    Tip(b, function(tt)
      local rank = TCF:RenownPerk(p.key)
      tt:AddLine(string.format("%s (rank %d of %d)", p.name, rank, #p.costs), 1, 0.82, 0)
      tt:AddLine(p.text, 1, 1, 1, true)
      local cost = p.costs[rank + 1]
      if cost then tt:AddLine(string.format("Next rank: %d Renown points (you have %d).", cost, TCF:RenownPoints()), 0.4, 1, 0.4) end
      tt:AddLine("Perks stay when you sell the business.", 0.7, 0.7, 0.7, true)
    end)
    b.perk = p
    perkBtns[k] = b
  end
  local function refreshPerks()
    perkHead:SetText(string.format("Renown shop  |cffffffff%d points|r  |cff999999(each sale gives points too; perks stay forever)|r", TCF:RenownPoints()))
    for _, b in ipairs(perkBtns) do
      local p = b.perk
      local rank = TCF:RenownPerk(p.key)
      local cost = p.costs[rank + 1]
      if cost then b:SetText(string.format("%s %d/%d  |cffffd100%d|r", p.name, rank, #p.costs, cost)); b:SetEnabled(TCF:RenownPoints() >= cost)
      else b:SetText(string.format("|cff20ff20%s %d/%d|r", p.name, rank, #p.costs)); b:SetEnabled(false) end
      fitText(b)
    end
  end

  ------------------------------------------------ (1.7.0) Guild: rank, specialization, daily craft, work orders
  local guildView = View()
  local gHead = Panel(guildView, 532, 54, 0.85); gHead:SetPoint("TOP", 0, -2)
  gHead.icon = gHead:CreateTexture(nil, "ARTWORK"); gHead.icon:SetSize(40, 40); gHead.icon:SetPoint("LEFT", 8, 0)
  gHead.name = Text(gHead, "GameFontNormalLarge", nil, "LEFT"); gHead.name:SetPoint("TOPLEFT", 56, -5); gHead.name:SetWidth(460)
  if gHead.name.SetWordWrap then gHead.name:SetWordWrap(false) end
  gHead.bar = Bar(gHead, 300, 14, 0.3, 0.55, 0.95); gHead.bar:SetPoint("BOTTOMLEFT", 56, 7)
  gHead.note = Text(gHead, "GameFontHighlightSmall", nil, "RIGHT"); gHead.note:SetPoint("BOTTOMRIGHT", -10, 7); gHead.note:SetWidth(150)
  Tip(gHead, function(tt)
    local craft = TCF:CraftProf()
    local g = TCF.GUILDS[craft]
    tt:AddLine(g.name, 1, 0.82, 0)
    tt:AddLine("Fill work orders to earn reputation. Ranks: Initiate, Apprentice, Journeyman, Expert, Artisan, Master and Grand Master. The legendary recipes need a high rank, and Grand Master gives the title " .. g.master .. ".", 1, 1, 1, true)
  end)
  -- specialization
  local gSpec = Panel(guildView, 532, 44, 0.85); gSpec:SetPoint("TOP", 0, -60)
  gSpec.text = Text(gSpec, "GameFontHighlightSmall", nil, "LEFT"); gSpec.text:SetPoint("LEFT", 10, 0); gSpec.text:SetWidth(512)
  gSpec.btns = {}
  for k = 1, 3 do
    local b = Button(gSpec, "", 168, 24, function()
      local sp = gSpec.btns[k].spec
      if not sp then return end
      local ok, why = TCF:ChooseSpec(sp.key)
      if not ok and why then TCF:Print(why, true) end
      win:Refresh()
    end)
    b:SetPoint("LEFT", 8 + (k - 1) * 174, 0)
    Tip(b, function(tt)
      local sp = b.spec
      if not sp then return end
      tt:AddLine(sp.name, 1, 0.82, 0)
      tt:AddLine(sp.perk, 1, 1, 1, true)
      tt:AddLine(string.format("Daily craft: %s. Long-chase set: %s.", TCF.DAILY_MATS[sp.daily].name,
        (TCF.COSMETIC_SET_BY_KEY[sp.set] and TCF.COSMETIC_SET_BY_KEY[sp.set].name) or "coming"), 0.4, 1, 0.4, true)
      if TCF:Spec(sp.craft) then tt:AddLine(string.format("Changing costs %d TapCoins.", TCF.SPEC_SWITCH_COINS), 1, 0.5, 0.3) end
    end)
    gSpec.btns[k] = b
  end
  -- the daily craft
  local gDaily = Panel(guildView, 532, 44, 0.85); gDaily:SetPoint("TOP", 0, -108)
  gDaily.icon = gDaily:CreateTexture(nil, "ARTWORK"); gDaily.icon:SetSize(32, 32); gDaily.icon:SetPoint("LEFT", 8, 0)
  gDaily.text = Text(gDaily, "GameFontHighlightSmall", nil, "LEFT"); gDaily.text:SetPoint("LEFT", 48, 0); gDaily.text:SetWidth(370)
  gDaily.btn = Button(gDaily, "Make", 96, 24, function()
    local ok, why = TCF:DailyCraft()
    if not ok and why then TCF:Print(why, true) end
    win:Refresh()
  end)
  gDaily.btn:SetPoint("RIGHT", -8, 0)
  -- work orders
  local gOrdHead = Text(guildView, "GameFontNormal", nil, "LEFT"); gOrdHead:SetPoint("TOPLEFT", 14, -158); gOrdHead:SetWidth(520)
  local orderRows = {}
  for k = 1, 5 do
    local r = Panel(guildView, 532, 38, 0.85); r:SetPoint("TOP", 0, -176 - (k - 1) * 40)
    r.icon = r:CreateTexture(nil, "ARTWORK"); r.icon:SetSize(28, 28); r.icon:SetPoint("LEFT", 6, 0)
    r.text = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.text:SetPoint("TOPLEFT", 42, -5); r.text:SetWidth(380)
    r.reward = Text(r, "GameFontDisableSmall", nil, "LEFT"); r.reward:SetPoint("BOTTOMLEFT", 42, 5); r.reward:SetWidth(380)
    for _, fs in ipairs({ r.text, r.reward }) do if fs.SetWordWrap then fs:SetWordWrap(false) end end
    r.btn = Button(r, "Deliver", 90, 24, function()
      if not r.order then return end
      local ok, why = TCF:FillOrder(r.order.id)
      if not ok and why then TCF:Print(why) end
      win:Refresh()
    end)
    r.btn:SetPoint("RIGHT", -6, 0)
    orderRows[k] = r
  end
  local gRare = Text(guildView, "GameFontHighlightSmall", nil, "LEFT"); gRare:SetPoint("TOPLEFT", 14, -380); gRare:SetWidth(520)
  local function refreshGuild()
    local craft = TCF:CraftProf()
    local fam = TCF:MainProf()
    local g = TCF.GUILDS[craft]
    local s = TCF:ProfState()
    local rank, rname, rep, nextRep = TCF:GuildRank(craft)
    gHead.icon:SetTexture(TCF.Icon(g.icon))
    gHead.name:SetText(string.format("%s  |cffffffff%s|r", g.name, rname))
    local lo = TCF.GUILD_RANKS[rank].rep
    gHead.bar:SetMinMaxValues(0, 1); gHead.bar:SetValue(nextRep and (rep - lo) / (nextRep - lo) or 1)
    gHead.bar.text:SetText(nextRep and string.format("%s / %s reputation", TCF.Commas(rep), TCF.Commas(nextRep)) or "Grand Master")
    gHead.note:SetText(string.format("|cff999999Orders filled: %d|r", (TCF:DepthState().filled or 0)))
    -- specialization
    local skill = TCF:ProfSkill(craft)
    local mine = TCF:Spec(craft)
    local list = TCF.SPECS[craft] or {}
    if skill < TCF.SPEC_SKILL then
      gSpec.text:SetText(string.format("|cffffd100Specializations|r open at %s %d (you have %d): %s. Each has its own daily craft, perk and legendary set.",
        TCF:CraftName(craft), TCF.SPEC_SKILL, skill, (function() local t = {} for _, sp in ipairs(list) do t[#t + 1] = sp.name end return table.concat(t, ", ") end)()))
      vis(gSpec.text, true)
      for _, b in ipairs(gSpec.btns) do vis(b, false) end
    elseif not mine or win.specPick then
      vis(gSpec.text, false)
      for k, b in ipairs(gSpec.btns) do
        local sp = list[k]
        b.spec = sp
        vis(b, sp)
        if sp then b:SetText((mine and mine.key == sp.key) and ("|cff20ff20" .. sp.name .. "|r") or sp.name); fitText(b) end
      end
    else
      gSpec.text:SetText(string.format("|cffffd100%s|r  %s  |cff999999(hover a recipe to see what it needs)|r", mine.name, mine.perk))
      vis(gSpec.text, true)
      for _, b in ipairs(gSpec.btns) do vis(b, false) end
    end
    -- daily craft
    if mine then
      local dm = TCF.DAILY_MATS[mine.daily]
      gDaily.icon:SetTexture(TCF.Icon(dm.icon)); gDaily.icon:SetDesaturated(false)
      local parts = {}
      for m, n in pairs(dm.mats) do
        local have = s.mats[m] or 0
        local mat = TCF.MAT_BY_KEY[m]
        parts[#parts + 1] = string.format("%s%s/%s|r %s", have >= n and "|cff20ff20" or "|cffff5050", TCF.FormatBig(min(have, n)), n, mat and mat.name or m)
      end
      table.sort(parts)
      local wait = TCF:DailyReadyIn(craft)
      gDaily.text:SetText(string.format("|cffffd100Daily craft: %s|r  (you have %d)\n%s", dm.name, s.mats[mine.daily] or 0, table.concat(parts, ",  ")))
      if wait > 0 then gDaily.btn:SetText(TCF.FormatDuration(wait)); gDaily.btn:SetEnabled(false)
      else gDaily.btn:SetText("Make"); gDaily.btn:SetEnabled(true) end
      vis(gDaily.btn, true)
    else
      gDaily.icon:SetTexture(TCF.Icon("INV_Misc_QuestionMark")); gDaily.icon:SetDesaturated(true)
      gDaily.text:SetText("|cff999999Daily craft: choose a specialization to make a special material once a day. The legendary sets need many of them.|r")
      vis(gDaily.btn, false)
    end
    -- orders
    local orders = TCF:WorkOrders(craft)
    local wait = TCF:NextOrderIn(craft)
    gOrdHead:SetText(string.format("Work orders  |cff999999%d of %d%s|r", #orders, TCF:OrderSlots(),
      (#orders < TCF:OrderSlots() and wait > 0) and string.format(", a new one in %s", TCF.FormatDuration(wait)) or ""))
    for k, r in ipairs(orderRows) do
      local o = orders[k]
      r.order = o
      vis(r, o)
      if o then
        local icon
        if o.kind == "gear" then local it = TCF.GEAR and TCF.GEAR[o.key]; icon = it and it.icon
        else local m = TCF.MAT_BY_KEY[o.key]; icon = m and m.icon end
        r.icon:SetTexture(TCF.Icon(icon or "INV_Misc_QuestionMark"))
        local have = TCF:OrderHave(o)
        r.text:SetText(TCF:OrderText(o) .. string.format("  %s(%d/%d)|r", have >= o.n and "|cff20ff20" or "|cffff5050", min(have, o.n), o.n))
        r.reward:SetText(string.format("%s,  +%d reputation%s  |cff777777(leaves in %s)|r", TCF.GoldStr(o.gold, 10), o.rep,
          (o.coins or 0) > 0 and string.format(",  %d TapCoins", o.coins) or "", TCF.FormatDuration(max(0, o.expires - time()))))
        r.btn:SetEnabled(have >= o.n)
      end
    end
    -- rare finds
    local parts = {}
    for _, rf in ipairs(TCF.RARE_FINDS[fam] or {}) do parts[#parts + 1] = string.format("%s |cffa335ee%d|r", rf.name, s.mats[rf.key] or 0) end
    local ws = TCF:WorkshopState()
    gRare:SetText(string.format("Rare finds (clicks by hand only):  %s   |cff999999Best glint combo %d|r", table.concat(parts, "   "), ws.best or 0))
  end

  ------------------------------------------------ refresh
  local MAIN = { herbalism = { gardenView, refreshGarden, "Garden" },
    firstaid = { aidView, refreshAid, "Bandages" }, fishing = { fishView, refreshFishing, "Fishing", enterFishing },
    cooking = { cookView, refreshCooking, "Kitchen" } }
  local allViews = { locked, spotView, upgView, gardenView, gardenerView, aidView, fishView, cookView, craftView, renView, guildView }

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
    herbalism = "|cffffd100Grow|r: pick a seed and plant it in your garden plots. Herbs grow in real time, even while you're offline. Right-click a plot to grow the seed you picked there next, so each plot can grow something different.\n\n|cffffd100Gardener|r: hire Bramble to harvest and replant for you, then train it from Apprentice to Master for faster growth, free seeds, more herbs and more rare herbs.\n\n|cffffd100Use|r: every harvest pays Trade Gold. Brew herbs into potions in Crafting and drink them for buffs, cook with them, or craft herbal cosmetics (cosmetic only, no stats).",
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
        "|cffffd100Grow|r: spend Trade Gold on Upgrades. As this cat earns Trade Gold it unlocks Herbalism, First Aid, Fishing and Cooking. When your business is big, sell it for Renown: each point adds 2%% Trade Gold and goods, so they come faster. Selling never lowers the Trade Gold earned that unlocks professions, and you need a few rounds of selling to reach the later ones.\n\n" ..
        "|cff999999Each class has its own Trade Gold and professions.|r",
        fam.spotNounPlural, fam.hirePlural:lower(), fam.spotNoun, fam.verb:lower(), fam.toolNoun:lower(), fam.matNoun,
        fam.craftName, fam.matNoun))
    else
      guide.title:SetText("How " .. (p and p.name or "this profession") .. " works")
      guide.body:SetText((GUIDE_OTHER[prof] or "") .. "\n\n|cff999999Each class has its own Trade Gold and professions.|r")
    end
    guide:Show()
  end

  ------------------------------------------------ (1.7.0) the Profession Bag (Bag.lua): every material, by tab
  local bagFrame = CreateFrame("Frame", nil, page, U.BT)
  bagFrame:SetPoint("TOPLEFT", 10, -74); bagFrame:SetPoint("BOTTOMRIGHT", -10, 10)
  if bagFrame.SetFrameLevel and page.GetFrameLevel and page:GetFrameLevel() then bagFrame:SetFrameLevel(page:GetFrameLevel() + 25) end
  if bagFrame.SetBackdrop then bagFrame:SetBackdrop(U.BACKDROP_DIALOG) end
  bagFrame.bg = bagFrame:CreateTexture(nil, "BACKGROUND"); bagFrame.bg:SetPoint("TOPLEFT", 6, -6); bagFrame.bg:SetPoint("BOTTOMRIGHT", -6, 6)
  bagFrame.bg:SetColorTexture(0.06, 0.05, 0.09, 0.98)
  bagFrame:EnableMouse(true)
  bagFrame:Hide()
  bagFrame.title = Text(bagFrame, "GameFontNormalLarge", nil, "LEFT"); bagFrame.title:SetPoint("TOPLEFT", 20, -16); bagFrame.title:SetWidth(330)
  bagFrame.sub = Text(bagFrame, "GameFontHighlightSmall", nil, "LEFT"); bagFrame.sub:SetPoint("TOPLEFT", 20, -40); bagFrame.sub:SetWidth(500)
  local bagClose = Button(bagFrame, "Close", 70, 22, function() bagFrame:Hide() end); bagClose:SetPoint("TOPRIGHT", -14, -14)
  local bagUp = Button(bagFrame, "", 200, 22, function()
    local ok, why = TCF:BuyMatBag()
    if not ok and why then TCF:Print(why, true) end
    win:Refresh()
  end)
  bagUp:SetPoint("RIGHT", bagClose, "LEFT", -6, 0)
  Tip(bagUp, function(tt)
    local nxt = TCF.MAT_BAGS[TCF:MatBagLevel() + 1]
    if not nxt then tt:AddLine("The biggest bag", 1, 0.82, 0); return end
    tt:AddLine(nxt.name, 1, 0.82, 0)
    tt:AddLine(string.format("Stacks hold %s. Costs %s TapCoins (for all your cats).", nxt.cap == math.huge and "any amount" or TCF.Commas(nxt.cap), TCF.Commas(nxt.coins)), 1, 1, 1, true)
  end)
  win.bagTab = win.bagTab or "gathered"
  local bagTabs = {}
  for k, tb in ipairs(TCF.BAG_TABS) do
    local b = Button(bagFrame, tb.name, 82, 20, function() win.bagTab = tb.key; win.bagScroll = 0; win:Refresh() end)
    b:SetPoint("TOPLEFT", 16 + (k - 1) * 84, -66)
    b.key = tb.key
    bagTabs[k] = b
  end
  local BAG_COLS, BAG_ROWS = 10, 5
  local cells = {}
  for k = 1, BAG_COLS * BAG_ROWS do
    local c = IconButton(bagFrame, 40)
    c:SetPoint("TOPLEFT", 22 + ((k - 1) % BAG_COLS) * 50, -96 - floor((k - 1) / BAG_COLS) * 50)
    if c.RegisterForClicks then c:RegisterForClicks("LeftButtonUp", "RightButtonUp") end
    c:SetScript("OnClick", function()
      if c.key and IsShiftKeyDown and IsShiftKeyDown() then TCF:SellMatStack(c.key); win:Refresh() end
    end)
    Tip(c, function(tt)
      local key = c.key
      if not key then return end
      local m = TCF.MAT_BY_KEY[key]
      local s = TCF:ProfState()
      local n = floor(s.mats[key] or 0)
      tt:AddLine(m and m.name or key, 1, 0.82, 0)
      local cap = TCF:MatCapFor(key)
      tt:AddLine(string.format("%s%s", TCF.Commas(n), cap == math.huge and "" or (" / " .. TCF.Commas(cap))), 1, 1, 1)
      local uses = TCF:MatUses(key)
      if #uses == 0 then tt:AddLine("Not used by anything yet: sell it if you like.", 0.7, 0.7, 0.7, true)
      else
        local shown = {}
        for i = 1, min(5, #uses) do shown[i] = uses[i] end
        tt:AddLine("Used in: " .. table.concat(shown, ", ") .. (#uses > 5 and string.format(" and %d more", #uses - 5) or ""), 0.4, 1, 0.4, true)
      end
      if (m and m.value or 0) > 0 then tt:AddLine(string.format("Sells for %s each. Shift-click to sell the whole stack.", TCF.GoldStr(m.value)), 0.8, 0.8, 0.8, true) end
    end)
    cells[k] = c
  end
  local bagPage = Text(bagFrame, "GameFontHighlightSmall", nil, "CENTER"); bagPage:SetPoint("BOTTOM", 0, 44)
  local bagPrev = Button(bagFrame, "<", 26, 20, function() win.bagScroll = max(0, (win.bagScroll or 0) - 1); win:Refresh() end)
  bagPrev:SetPoint("RIGHT", bagPage, "LEFT", -8, 0)
  local bagNext = Button(bagFrame, ">", 26, 20, function() win.bagScroll = (win.bagScroll or 0) + 1; win:Refresh() end)
  bagNext:SetPoint("LEFT", bagPage, "RIGHT", 8, 0)
  local bagNote = Text(bagFrame, "GameFontDisableSmall", nil, "LEFT"); bagNote:SetPoint("BOTTOMLEFT", 20, 18); bagNote:SetWidth(500)
  local function refreshBag()
    if not bagFrame:IsShown() then return end
    local s = TCF:ProfState()
    local bag = TCF:MatBag()
    bagFrame.title:SetText(string.format("%s's bag  |cffffffff%s|r", className(), bag.name))
    bagFrame.sub:SetText(string.format("Every kind of material always fits. Stacks hold %s; more than that is sold for Trade Gold right away.",
      bag.cap == math.huge and "any amount" or TCF.Commas(bag.cap)))
    local nxt = TCF.MAT_BAGS[TCF:MatBagLevel() + 1]
    if nxt then bagUp:SetText(string.format("%s  %s", nxt.name, TCF.Commas(nxt.coins))); bagUp:SetEnabled((TCF.db.coins or 0) >= nxt.coins)
    else bagUp:SetText("|cff20ff20Biggest bag|r"); bagUp:SetEnabled(false) end
    fitText(bagUp)
    for _, b in ipairs(bagTabs) do if b.key == win.bagTab then b:LockHighlight() else b:UnlockHighlight() end; fitText(b) end
    local list = TCF:BagList(win.bagTab)
    local per = BAG_COLS * BAG_ROWS
    local pages = math.max(1, math.ceil(#list / per))
    win.bagScroll = min(max(0, win.bagScroll or 0), pages - 1)
    for k, c in ipairs(cells) do
      local key = list[win.bagScroll * per + k]
      c.key = key
      vis(c, key)
      if key then
        local m = TCF.MAT_BY_KEY[key]
        c.tex:SetTexture(TCF.Icon(m and m.icon or "INV_Misc_QuestionMark"))
        -- short counts that fit under a 40px icon: 950, 12K, 3.4M
        local n = floor(s.mats[key] or 0)
        c.count:SetText(n < 1000 and tostring(n) or (n < 1e6 and (floor(n / 1000) .. "K") or (n < 1e9 and string.format("%.1fM", n / 1e6) or TCF.FormatBig(n))))
      end
    end
    vis(bagPage, pages > 1); vis(bagPrev, pages > 1); vis(bagNext, pages > 1)
    bagPage:SetText(string.format("%d / %d", win.bagScroll + 1, pages))
    if #list == 0 then bagNote:SetText("Nothing here yet.")
    else
      bagNote:SetText(string.format("Hover a material to see what it's for. Shift-click sells a stack.%s",
        (s.bagSold or 0) > 0 and string.format("  Extra sold so far: %s.", TCF.GoldStr(s.bagSold)) or ""))
    end
  end
  win.profBag = bagFrame

  -- a small Help button right after the profession's name (the header has no room for more)
  local helpBtn = Button(page, "Help", 54, 20, function() showGuide(win.profSel or TCF:MainProf()) end)
  helpBtn:SetPoint("LEFT", profName, "RIGHT", 8, 0)
  local bagBtn = Button(page, "Bag", 48, 20, function() bagFrame:SetShown(not bagFrame:IsShown()); TCF:PlaySound("click"); win:Refresh() end)
  bagBtn:SetPoint("LEFT", helpBtn, "RIGHT", 4, 0)
  Tip(bagBtn, function(tt)
    tt:AddLine("Profession Bag", 1, 0.82, 0)
    tt:AddLine("Every material this cat has, what it's for, and selling leftovers. Bigger bags (TapCoins) hold bigger stacks.", 1, 1, 1, true)
  end)
  Tip(helpBtn, function(tt)
    tt:AddLine("How it works", 1, 0.82, 0)
    tt:AddLine("What this profession does and how it gets you gear and cosmetics.", 1, 1, 1, true)
  end)
  TCF.ShowProfessionGuide = function(_, prof) showGuide(prof or win.profSel or TCF:MainProf()) end

  local shownKey
  refresh = function()
    refreshBag()
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
    -- the second view button: Upgrades for the main profession, Gardener for Herbalism (1.6.7)
    local hasSecond = fam or prof == "herbalism"
    if win.profView == "upg" and not hasSecond then win.profView = "main" end
    if win.profView == "guild" and not fam then win.profView = "main" end
    local view = win.profView
    local unlocked = TCF:ProfUnlocked(prof)
    -- the first time each profession is opened, its guide explains it (remembered per account)
    TCF.db.profGuides = TCF.db.profGuides or {}
    local gkey = fam and "family" or prof
    if unlocked and not TCF.db.profGuides[gkey] then TCF.db.profGuides[gkey] = true; showGuide(prof)
    elseif guide:IsShown() and guide.prof ~= prof then guide:Hide() end
    -- header
    profName:SetText(p.name)
    local skillKey = (fam and (view == "craft" or view == "guild")) and fam.craft or prof
    local skillProf = TCF.PROF_BY_KEY[skillKey] or p
    local skillName = skillProf.skillName or skillProf.name   -- "Cloth Scavenging", not a second "Tailoring"
    local skill = TCF:ProfSkill(skillKey)
    skillBar:SetMinMaxValues(0, 300); skillBar:SetValue(skill); skillBar.text:SetText(skillName .. " " .. skill .. " / 300")
    goldText:SetText(TCF.GoldStr(s.gold, 16))
    renownText:SetText(string.format("%s: Renown %d (+%d%%)", className(), s.renown, s.renown * 2))
    buyMode:SetText(s.buy == "max" and "Buy Max" or ("Buy x" .. s.buy))
    vis(buyMode, fam and view == "main" and unlocked)
    vbtns[1]:SetText(fam and fam.spotsTitle or MAIN[prof][3])
    vbtns[3]:SetText(fam and fam.craftName or "Crafting")
    vbtns[2]:SetText(fam and "Upgrades" or "Gardener")
    vis(vbtns[2], hasSecond)
    vis(vbtns[4], fam)
    for _, b in ipairs(vbtns) do fitText(b) end
    for _, b in ipairs(vbtns) do if b.key == view then b:LockHighlight() else b:UnlockHighlight() end end

    -- which view, and change visibility only when it changes
    local target, enter
    if not unlocked and view ~= "renown" then target = locked
    elseif view == "main" then
      if fam then target, enter = spotView, function() enterSpots(prof) end
      else target, enter = MAIN[prof][1], MAIN[prof][4] end
    elseif view == "upg" then target = fam and upgView or gardenerView
    elseif view == "guild" then target = guildView
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
    elseif target == gardenerView then refreshGardener()
    elseif target == craftView then refreshCraft(fam and fam.craft or prof)
    elseif target == renView then refreshRenown(); refreshPerks()
    elseif target == guildView then refreshGuild()
    else MAIN[prof][2]() end
  end
  return refresh
end
