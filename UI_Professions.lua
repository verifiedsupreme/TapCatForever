-- TapCatForever: Professions page (gathering over time, crafting exclusive cosmetics)
local ADDON, TCF = ...
local floor, max, min = math.floor, math.max, math.min

TCF.UI.Builders.professions = function(page, win)
  local U = TCF.UI
  local Text, Button, Tip, Panel = U.Text, U.Button, U.Tip, U.Panel
  local title = Text(page, "GameFontNormalLarge", "Professions", "LEFT"); title:SetPoint("TOPLEFT", 16, -12)
  local sub = Text(page, "GameFontDisableSmall", "Your cat gathers every 6 minutes, even offline (up to 12 hours). Craft cosmetics you can't get anywhere else.", "LEFT")
  sub:SetPoint("TOPLEFT", 16, -30); sub:SetWidth(530)

  local cols = {}
  for c = 1, 2 do
    local col = Panel(page, 262, 440, 0.85); col:SetPoint("TOPLEFT", 12 + (c - 1) * 270, -48)
    -- learn view
    col.learn = {}
    local lt = Text(col, "GameFontNormal", "Learn a profession", "LEFT"); lt:SetPoint("TOPLEFT", 10, -10)
    col.learnTitle = lt
    for i, p in ipairs(TCF.PROFESSIONS) do
      local b = Button(col, p.name, 200, 26, function() TCF:LearnProfession(p.key) end)
      b:SetPoint("TOPLEFT", 40, -36 - (i - 1) * 34)
      local ic = col:CreateTexture(nil, "ARTWORK"); ic:SetSize(26, 26); ic:SetPoint("RIGHT", b, "LEFT", -4, 0); ic:SetTexture(TCF.Icon(p.icon))
      b.icon = ic; b.prof = p
      Tip(b, function(tt)
        tt:AddLine(p.name, 1, 0.82, 0)
        local names = {}
        for _, m in ipairs(p.mats) do names[#names + 1] = m[2] .. (m[6] and " (rare)" or "") end
        tt:AddLine("Gathers: " .. table.concat(names, ", "), 1, 1, 1, true)
      end)
      col.learn[i] = b
    end
    -- known view
    col.icon = col:CreateTexture(nil, "ARTWORK"); col.icon:SetSize(30, 30); col.icon:SetPoint("TOPLEFT", 8, -8)
    col.name = Text(col, "GameFontNormal", nil, "LEFT"); col.name:SetPoint("TOPLEFT", col.icon, "TOPRIGHT", 6, 0)
    col.unlearn = Button(col, "Unlearn", 64, 18, function()
      if col.prof then
        if IsShiftKeyDown() then TCF:UnlearnProfession(col.prof)
        else TCF:Print("Shift-click Unlearn to forget " .. TCF.PROF_BY_KEY[col.prof].name .. " (skill is lost; materials are kept).") end
      end
    end)
    col.unlearn:SetPoint("TOPRIGHT", -6, -8)
    local function Bar(y, r, g, b)
      local bar = CreateFrame("StatusBar", nil, col); bar:SetSize(244, 12); bar:SetPoint("TOPLEFT", 9, y)
      bar:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar"); bar:SetStatusBarColor(r, g, b)
      local bg = bar:CreateTexture(nil, "BACKGROUND"); bg:SetAllPoints(); bg:SetColorTexture(0, 0, 0, 0.6)
      bar.text = Text(bar, "GameFontHighlightSmall"); bar.text:SetPoint("CENTER")
      return bar
    end
    col.skill = Bar(-44, 0.2, 0.5, 0.95)
    col.gather = Bar(-60, 0.85, 0.7, 0.2)
    col.matLabel = Text(col, "GameFontNormalSmall", "Materials (click to sell 5)", "LEFT"); col.matLabel:SetPoint("TOPLEFT", 10, -80)
    col.mats = {}
    for i = 1, 7 do
      local b = CreateFrame("Button", nil, col)
      b:SetSize(30, 30); b:SetPoint("TOPLEFT", 10 + (i - 1) * 34, -96)
      b.tex = b:CreateTexture(nil, "ARTWORK"); b.tex:SetAllPoints()
      b.count = Text(b, "NumberFontNormal", nil, "RIGHT"); b.count:SetPoint("BOTTOMRIGHT", 2, -2)
      b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
      b:SetScript("OnClick", function() if b.mat then TCF:SellMaterial(b.mat.key, 5) end end)
      Tip(b, function(tt)
        if not b.mat then return end
        tt:AddLine(b.mat.name, 1, 1, 1)
        tt:AddLine("Needs skill " .. b.mat.skill .. (b.mat.rare and "   (rare find)" or ""), 0.8, 0.8, 0.8)
        tt:AddLine("Click: sell 5", 0, 1, 0)
      end)
      col.mats[i] = b
    end
    col.recLabel = Text(col, "GameFontNormalSmall", "Recipes", "LEFT"); col.recLabel:SetPoint("TOPLEFT", 10, -136)
    col.recipes = {}
    for i = 1, 5 do
      local r = CreateFrame("Frame", nil, col)
      r:SetSize(244, 54); r:SetPoint("TOPLEFT", 9, -152 - (i - 1) * 56)
      r.cell = U.ItemCell(r, 44); r.cell:SetPoint("LEFT", 0, 0)
      r.cell:SetScript("OnEnter", function(s)
        if not s.item then return end
        GameTooltip:SetOwner(s, "ANCHOR_RIGHT"); TCF:ItemTooltip(GameTooltip, s.item); GameTooltip:Show()
        if TCF:CanEquip(s.item) then win.preview:ApplyAppearance(TCF:GetAppearance(nil, s.item)) end
      end)
      r.cell:SetScript("OnLeave", function() GameTooltip:Hide(); win.preview:ApplyAppearance(TCF:GetAppearance()) end)
      r.name = Text(r, "GameFontNormalSmall", nil, "LEFT"); r.name:SetPoint("TOPLEFT", r.cell, "TOPRIGHT", 6, -2); r.name:SetWidth(130)
      r.need = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.need:SetPoint("BOTTOMLEFT", r.cell, "BOTTOMRIGHT", 6, 2); r.need:SetWidth(140)
      r.craft = Button(r, "Craft", 52, 20, function() if r.recipe then TCF:Craft(r.recipe) end end)
      r.craft:SetPoint("RIGHT", 0, 0)
      col.recipes[i] = r
    end
    cols[c] = col
  end

  local function showKnown(col, show)
    for _, w in ipairs({ col.icon, col.name, col.unlearn, col.skill, col.gather, col.matLabel, col.recLabel }) do w:SetShown(show) end
    for _, b in ipairs(col.mats) do b:SetShown(show and b.mat ~= nil) end
    for _, r in ipairs(col.recipes) do r:SetShown(show) end
    col.learnTitle:SetShown(not show)
    for _, b in ipairs(col.learn) do b:SetShown(not show); b.icon:SetShown(not show) end
  end

  return function()
    local ps = TCF:ProfState()
    local known = {}
    for _, p in ipairs(TCF.PROFESSIONS) do if ps.known[p.key] then known[#known + 1] = p end end
    for c, col in ipairs(cols) do
      local p = known[c]
      col.prof = p and p.key
      if p then
        col.icon:SetTexture(TCF.Icon(p.icon))
        col.name:SetText(p.name)
        local skill = ps.skill[p.key]
        col.skill:SetMinMaxValues(0, 300); col.skill:SetValue(skill); col.skill.text:SetText("Skill " .. skill .. " / 300")
        local prog = TCF:GatherProgress(p.key)
        col.gather:SetMinMaxValues(0, 1); col.gather:SetValue(prog)
        col.gather.text:SetText("Next gather in " .. TCF.FormatDuration(TCF.GATHER_SECONDS * (1 - prog)))
        for i, b in ipairs(col.mats) do
          local m = p.mats[i] and TCF.MAT_BY_KEY[p.mats[i][1]]
          b.mat = m
          if m then
            b.tex:SetTexture(TCF.Icon(m.icon)); b.tex:SetDesaturated(skill < m.skill)
            local n = ps.mats[m.key] or 0
            b.count:SetText(n > 0 and n or "")
          end
        end
        for i, r in ipairs(col.recipes) do
          local rec = TCF.RECIPES[p.key][i]
          r.recipe = rec
          if rec then
            local it = TCF.ITEMS[rec.item]
            r.cell:SetItem(it, TCF.db.owned[it.id] and true or skill >= rec.skill, false)
            local col2 = TCF.RARITY[it.rarity]
            r.name:SetText("|c" .. col2.hex .. it.name .. "|r")
            local parts = {}
            for mk, need in pairs(rec.mats) do
              local have = ps.mats[mk] or 0
              parts[#parts + 1] = string.format("%s%d/%d|r %s", have >= need and "|cff20ff20" or "|cffff5050", min(have, need), need, TCF.MAT_BY_KEY[mk].name)
            end
            r.need:SetText((skill < rec.skill and ("|cffff5050Skill " .. rec.skill .. "|r  ") or "") .. table.concat(parts, ", "))
            r.craft:SetEnabled(TCF:CanCraft(rec))
            r.craft:SetText(TCF.db.owned[it.id] and "Again" or "Craft")
          end
        end
        showKnown(col, true)
      else
        showKnown(col, false)
        for i, b in ipairs(col.learn) do
          local already = ps.known[b.prof.key]
          b:SetEnabled(not already and #known < TCF.MAX_PROFESSIONS)
        end
      end
    end
  end
end
