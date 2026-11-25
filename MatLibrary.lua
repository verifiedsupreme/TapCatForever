-- TapCatForever: the materials library (1.7.3). Every material in the game, where it comes from and what
-- it's for, searchable, in the Compendium's Materials category. TCF:MatSource(key) also adds a "from"
-- line to recipe tooltips and the Profession Bag.
local ADDON, TCF = ...
local floor, min, max = math.floor, math.min, math.max

local PROF_WORD = { herbalism = "Herbalism", fishing = "Fishing", cooking = "Cooking", firstaid = "First Aid" }

-- where a material comes from: one short line (or nil when unknown)
function TCF:MatSource(key)
  local m = TCF.MAT_BY_KEY[key]
  if not m then return nil end
  -- a gathering spot's material
  for fk, f in pairs(TCF.FAMILIES or {}) do
    for i, op in ipairs(f.ops or {}) do
      if op[2] == key then
        return string.format("Gathered at %s (%s, spot %d)", op[1], f.skillName or f.tab or fk, i),
          string.format("%s, spot %d", f.skillName or f.tab or fk, i)
      end
    end
  end
  -- a rare find: clicking the spots by hand
  for fk, list in pairs(TCF.RARE_FINDS or {}) do
    for _, r in ipairs(list) do
      if r.key == key then
        local f = TCF.FAMILIES[fk]
        local op = f and f.ops[r.spot]
        return string.format("Rare find: click %s spots by hand, from %s on (about 1 in %d clicks)",
          f and (f.skillName or f.tab) or fk, op and op[1] or ("spot " .. r.spot), floor(1 / (TCF.RARE_FIND_CHANCE or 0.004) + 0.5)),
          string.format("Rare: %s spot %d+", ({ mining = "Mining", skinning = "Skinning", cloth = "Cloth" })[fk] or fk, r.spot)
      end
    end
  end
  -- a daily craft material: a specialization's
  if TCF.DAILY_MATS and TCF.DAILY_MATS[key] then
    for craft, list in pairs(TCF.SPECS or {}) do
      for _, sp in ipairs(list) do
        if sp.daily == key then
          return string.format("Daily craft of the %s specialization (Guild page, from %s skill %d)", sp.name,
            TCF.PROF_BY_KEY[craft] and TCF.PROF_BY_KEY[craft].name or craft, TCF.SPEC_SKILL or 225), "Daily: " .. sp.name:gsub(" Tailoring$", ""):gsub(" Leatherworking$", "")
        end
      end
    end
    return "A specialization's daily craft (Guild page)", "Daily craft"
  end
  -- Herbalism: a rare herb, or a seed's herb
  if TCF.RARE_BY_KEY and TCF.RARE_BY_KEY[key] then
    return "Rare herb: comes with some harvests of " .. TCF.RareSources(key), "Rare herb, Garden"
  end
  -- potions and flasks are brewed from herbs (Alchemy.lua), not grown
  if TCF.POTION_BY_KEY and TCF.POTION_BY_KEY[key] then return "Brewed from herbs (Herbalism crafting)", "Brewed" end
  if m.prof == "herbalism" then return "Grown in the Garden (Herbalism)", "Garden" end
  if key == "pinchy" then return "Fishing: a rare catch at any spot", "Rare catch, Fishing" end
  if m.prof == "fishing" then return "Caught while Fishing", "Fishing" end
  if m.prof == "cooking" then return "Cooked (Cooking)", "Cooking" end
  if m.prof == "firstaid" then return "Made with First Aid", "First Aid" end
  if m.prof and PROF_WORD[m.prof] then return "From " .. PROF_WORD[m.prof], PROF_WORD[m.prof] end
  return nil
end

-- the library's list: every material, sorted by name, filtered by a search and by owned/missing
function TCF:MatLibraryList(search, filter)
  local q = (search or ""):lower():gsub("^%s+", ""):gsub("%s+$", "")
  local s = self.ProfState and self:ProfState()
  local list = {}
  for key, m in pairs(TCF.MAT_BY_KEY) do
    local have = s and floor(s.mats[key] or 0) or 0
    local ok = q == "" or (m.name or key):lower():find(q, 1, true)
    if ok and filter == "owned" and have <= 0 then ok = false end
    if ok and filter == "missing" and have > 0 then ok = false end
    if ok then list[#list + 1] = { key = key, m = m, have = have } end
  end
  table.sort(list, function(a, b) return (a.m.name or a.key) < (b.m.name or b.key) end)
  return list
end

function TCF:MatTooltip(tt, key)
  local m = TCF.MAT_BY_KEY[key]
  if not m then return end
  local s = self.ProfState and self:ProfState()
  tt:AddLine(m.name or key, 1, 0.82, 0)
  tt:AddLine(string.format("This cat has %s.", TCF.Commas(s and floor(s.mats[key] or 0) or 0)), 1, 1, 1)
  local src = self:MatSource(key)
  tt:AddLine("Where it comes from", 1, 0.82, 0)
  tt:AddLine(src or "Not found anywhere yet.", 0.6, 0.8, 1, true)
  local uses = self.MatUses and self:MatUses(key) or {}
  if #uses > 0 then
    local shown = {}
    for i = 1, min(8, #uses) do shown[i] = uses[i] end
    tt:AddLine("Used in: " .. table.concat(shown, ", ") .. (#uses > 8 and string.format(" and %d more", #uses - 8) or ""), 0.4, 1, 0.4, true)
  else
    tt:AddLine("Not used in anything yet.", 0.6, 0.6, 0.6)
  end
end

---------------------------------------------------------------- Compendium: Materials
local MROWS, MCOLS, MROW_H = 16, 2, 26

function TCF:RefreshCompendiumMats(f, ctx)
  local view = f.matsView
  if not view then
    local UI = TCF.UI
    view = CreateFrame("Frame", nil, f)
    view:SetPoint("TOPLEFT", 18, ctx.top); view:SetSize(ctx.width, MROWS * MROW_H + 30)
    -- the search box
    local search = CreateFrame("EditBox", nil, view, "InputBoxTemplate")
    search:SetSize(220, 20); search:SetPoint("TOPLEFT", 8, 0)
    if search.SetAutoFocus then search:SetAutoFocus(false) end
    if search.SetMaxLetters then search:SetMaxLetters(40) end
    local hint = UI.Text(search, "GameFontDisableSmall", "Search materials", "LEFT"); hint:SetPoint("LEFT", 2, 0)
    search:SetScript("OnTextChanged", function(self)
      local t = self:GetText() or ""
      hint:SetShown(t == "")
      if t ~= (view.search or "") then view.search = t; f.page = 1; f:Refresh() end
    end)
    search:SetScript("OnEscapePressed", function(self) if self.ClearFocus then self:ClearFocus() end end)
    search:SetScript("OnEnterPressed", function(self) if self.ClearFocus then self:ClearFocus() end end)
    view.box = search
    view.rows = {}
    local colW = floor((ctx.width - 8) / MCOLS)
    for i = 1, MROWS * MCOLS do
      local r = CreateFrame("Button", nil, view)
      r:SetSize(colW - 4, MROW_H - 2)
      r:SetPoint("TOPLEFT", floor((i - 1) / MROWS) * colW, -28 - ((i - 1) % MROWS) * MROW_H)
      r.bg = r:CreateTexture(nil, "BACKGROUND"); r.bg:SetAllPoints(); r.bg:SetColorTexture(1, 1, 1, 0.05)
      r:SetHighlightTexture("Interface\\QuestFrame\\UI-QuestTitleHighlight", "ADD")
      r.icon = r:CreateTexture(nil, "ARTWORK"); r.icon:SetSize(20, 20); r.icon:SetPoint("LEFT", 3, 0)
      r.name = UI.Text(r, "GameFontHighlight", nil, "LEFT"); r.name:SetPoint("LEFT", 28, 0); r.name:SetWidth(170)
      r.src = UI.Text(r, "GameFontDisableSmall", nil, "LEFT"); r.src:SetPoint("LEFT", 204, 0); r.src:SetWidth(colW - 272)
      r.num = UI.Text(r, "GameFontHighlightSmall", nil, "RIGHT"); r.num:SetPoint("RIGHT", -6, 0); r.num:SetWidth(60)
      for _, fs in ipairs({ r.name, r.src }) do if fs.SetWordWrap then fs:SetWordWrap(false) end end
      r:SetScript("OnEnter", function(s)
        if not s.key then return end
        GameTooltip:SetOwner(s, "ANCHOR_RIGHT")
        TCF:MatTooltip(GameTooltip, s.key)
        GameTooltip:Show()
      end)
      r:SetScript("OnLeave", function() GameTooltip:Hide() end)
      r:Hide()
      view.rows[i] = r
    end
    f.matsView = view
  end
  view:Show()
  local list = self:MatLibraryList(view.search, f.filter)
  local nHave = 0
  for _, e in ipairs(self:MatLibraryList(nil, "owned")) do nHave = nHave + 1 end
  local total = 0
  for _ in pairs(TCF.MAT_BY_KEY) do total = total + 1 end
  ctx.collected(nHave, total)
  local first = ctx.setPages(#list, MROWS * MCOLS)
  for i, r in ipairs(view.rows) do
    local e = list[first + i]
    if e then
      r.key = e.key
      r.icon:SetTexture(TCF.Icon(e.m.icon or "INV_Misc_QuestionMark"))
      r.icon:SetDesaturated(e.have <= 0)
      r.name:SetText(e.m.name or e.key)
      local _, short = self:MatSource(e.key)
      r.src:SetText(short or "")
      r.num:SetText(e.have > 0 and (e.have < 1e7 and TCF.Commas(e.have) or TCF.FormatBig(e.have)) or "|cff6666660|r")
      r:Show()
    else
      r.key = nil; r:Hide()
    end
  end
  return #list
end
