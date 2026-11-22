-- TapCatForever: real Classic item sets and their set bonuses (SetData.lua, built by
-- tools/make_sets.py). Wearing enough pieces of a set gives its bonuses: the ones we can model
-- (Strength, Stamina, attack power, spell power, armor, crit and hit ratings...) are added in
-- TCF:CombatStats, so Power, Adventure, Equip best and every comparison include them. The rest
-- (procs, class spell tweaks, resistances) are shown greyed as having no effect on the cat.
local ADDON, TCF = ...
local floor, min, max = math.floor, math.min, math.max

TCF.ITEM_SETS = TCF.ITEM_SETS or {}
-- item id -> set index
TCF.SET_OF = {}
for si, set in ipairs(TCF.ITEM_SETS) do
  for _, id in ipairs(set.items) do TCF.SET_OF[id] = si end
end

-- Counts the set pieces in a list of worn item ids (each item once) and adds the active
-- bonuses' stats to t (a stat table such as TCF:CombatStats builds). Returns { [set] = pieces }
-- or nil when no set piece is worn.
function TCF.SetBonusTotals(ids, t)
  local setOf, counts, seen = TCF.SET_OF, nil, nil
  for _, id in ipairs(ids) do
    local si = setOf[id]
    if si then
      seen = seen or {}
      if not seen[id] then
        seen[id] = true
        counts = counts or {}
        counts[si] = (counts[si] or 0) + 1
      end
    end
  end
  if counts and t then
    for si, n in pairs(counts) do
      for _, b in ipairs(TCF.ITEM_SETS[si].bonuses) do
        local k, v = b[3], b[4]
        if k and n >= b[1] and t[k] then t[k] = t[k] + v end
      end
    end
  end
  return counts
end

-- the set an item belongs to (and its index), or nil
function TCF.ItemSetOf(id)
  local si = TCF.SET_OF[id]
  return si and TCF.ITEM_SETS[si], si
end

-- pieces of a set the class's cat wears now
function TCF:SetPiecesWorn(si, class)
  local eq = self:GearEquipped(class or self.db.class)
  local seen, n = {}, 0
  for _, id in pairs(eq) do
    if TCF.SET_OF[id] == si and not seen[id] then seen[id] = true; n = n + 1 end
  end
  return n, seen
end

-- how many bonuses of a set are active with n pieces
function TCF.SetBonusesActive(set, n)
  local a = 0
  for _, b in ipairs(set.bonuses) do if n >= b[1] then a = a + 1 end end
  return a
end

-- a set bonus line: "(2) Set: +200 Armor."; modelled bonuses green when active, grey when not;
-- the others always grey with "(no effect on your cat)"
function TCF.SetBonusLine(b, active)
  local text = "(" .. b[1] .. ") Set: " .. b[2]
  if not b[3] then return text .. " (no effect on your cat)", 0.5, 0.5, 0.5 end
  if active then return text, 0.12, 1, 0 end
  return text, 0.5, 0.5, 0.5
end

-- The set part of a gear tooltip: the set's name with pieces worn / total, every member (worn
-- white, the rest grey), then the bonuses.
function TCF:AddSetTooltip(tt, it, class)
  local set, si = TCF.ItemSetOf(it.id)
  if not set then return end
  class = class or self.db.class
  local n, worn = self:SetPiecesWorn(si, class)
  tt:AddLine(" ")
  tt:AddLine(string.format("%s (%d/%d)", set.name, n, set.total), 1, 0.82, 0)
  for _, id in ipairs(set.items) do
    local g = TCF.GEAR[id]
    if g then
      if worn[id] then tt:AddLine("  " .. g.name, 1, 1, 1) else tt:AddLine("  " .. g.name, 0.5, 0.5, 0.5) end
    end
  end
  for _, name in ipairs(set.missing or {}) do tt:AddLine("  " .. name, 0.5, 0.5, 0.5) end
  for _, b in ipairs(set.bonuses) do
    local text, r, g, bl = TCF.SetBonusLine(b, n >= b[1])
    tt:AddLine(text, r, g, bl, true)
  end
end

-- Lines for a comparison: how wearing it in that slot changes the set bonuses.
-- baseSets / newSets: the "sets" of TCF:CombatStats before and after. { { text, r, g, b }, ... }
function TCF.SetChangeLines(baseSets, newSets)
  local out, touched = {}, {}
  for si in pairs(baseSets or {}) do touched[si] = true end
  for si in pairs(newSets or {}) do touched[si] = true end
  local list = {}
  for si in pairs(touched) do list[#list + 1] = si end
  table.sort(list)
  for _, si in ipairs(list) do
    local set = TCF.ITEM_SETS[si]
    local a, b = (baseSets or {})[si] or 0, (newSets or {})[si] or 0
    local before, after = TCF.SetBonusesActive(set, a), TCF.SetBonusesActive(set, b)
    if after ~= before then
      local d = after - before
      local word = math.abs(d) == 1 and "set bonus" or "set bonuses"
      if d > 0 then
        out[#out + 1] = { string.format("  %s %d/%d: +%d %s", set.name, b, set.total, d, word), 0.12, 1, 0 }
      else
        out[#out + 1] = { string.format("  %s %d/%d: %d %s", set.name, b, set.total, d, word), 1, 0.25, 0.25 }
      end
    end
  end
  return out
end

-- every gear tooltip shows its set (wraps UI.lua's; UI_Gear.lua adds the comparison after it)
do
  local base = TCF.GearTooltip
  if base then
    function TCF:GearTooltip(tt, it, class)
      base(self, tt, it, class)
      if it then self:AddSetTooltip(tt, it, class) end
    end
  end
end

---------------------------------------------------------------- Compendium: Item Sets
-- One row per set: its name and level, how many pieces this character has (any cat's bag or
-- worn) out of the set's total. Hover for the members and bonuses. Compendium.lua shows this
-- view for its "Item Sets" category and passes its paging helpers in ctx.
local SROWS, SCOLS, SROW_H = 18, 2, 24

local function ownedGear()
  local set = {}
  for _, cd in pairs(TCF.db.classData or {}) do
    for id, n in pairs(cd.bag or {}) do if n and n > 0 then set[id] = true end end
    for _, id in pairs(cd.gear or {}) do set[id] = true end
  end
  return set
end

-- does any piece of the set fit this class? (classKey nil: every set; "ANY": sets anyone can wear)
local function setFits(set, classKey)
  if not classKey then return true end
  for _, id in ipairs(set.items) do
    local g = TCF.GEAR[id]
    if g then
      if classKey == "ANY" then
        if g.cls then return false end
      elseif TCF:GearUsable(g, classKey) then
        return true
      end
    end
  end
  return classKey == "ANY"
end

function TCF:SetTooltip(tt, set, got)
  tt:AddLine(set.name, 1, 0.82, 0)
  local have, lv = 0, 0
  for _, id in ipairs(set.items) do
    local g = TCF.GEAR[id]
    if g then
      lv = max(lv, g.req or 0)
      if got[id] then have = have + 1 end
    end
  end
  tt:AddLine(string.format("%d of %d pieces collected. Pieces need level %d or lower.", have, set.total, lv), 1, 1, 1, true)
  for _, id in ipairs(set.items) do
    local g = TCF.GEAR[id]
    if g then
      local col = got[id] and TCF.RARITY[g.q].color or { 0.5, 0.5, 0.5 }
      tt:AddLine("  " .. g.name, col[1], col[2], col[3])
    end
  end
  for _, name in ipairs(set.missing or {}) do tt:AddLine("  " .. name, 0.5, 0.5, 0.5) end
  local n = 0
  for _, id in ipairs(set.items) do if got[id] then n = n + 1 end end
  for _, b in ipairs(set.bonuses) do
    local text, r, g, bl = TCF.SetBonusLine(b, false)
    tt:AddLine(text, b[3] and 1 or r, b[3] and 1 or g, b[3] and 1 or bl, true)
  end
  local si = TCF.SET_OF[set.items[1]]
  local worn = si and self:SetPiecesWorn(si) or 0
  if worn > 0 then
    tt:AddLine(string.format("Your %s cat wears %d: %d bonus%s active.", TCF.CLASS_BY_KEY[self.db.class].name, worn,
      TCF.SetBonusesActive(set, worn), TCF.SetBonusesActive(set, worn) == 1 and "" or "es"), 0.3, 1, 0.3, true)
  end
  tt:AddLine("Set bonuses count the pieces your cat wears.", 0.7, 0.7, 0.7, true)
end

function TCF:RefreshCompendiumSets(f, ctx)
  local view = f.setsView
  if not view then
    local UI = TCF.UI
    view = CreateFrame("Frame", nil, f)
    view:SetPoint("TOPLEFT", 18, ctx.top); view:SetSize(ctx.width, SROWS * SROW_H)
    view.rows = {}
    local colW = floor((ctx.width - 8) / SCOLS)
    for i = 1, SROWS * SCOLS do
      local r = CreateFrame("Button", nil, view)
      r:SetSize(colW - 4, SROW_H - 2)
      r:SetPoint("TOPLEFT", floor((i - 1) / SROWS) * colW, -((i - 1) % SROWS) * SROW_H)
      r.bg = r:CreateTexture(nil, "BACKGROUND"); r.bg:SetAllPoints(); r.bg:SetColorTexture(1, 1, 1, 0.05)
      r:SetHighlightTexture("Interface\\QuestFrame\\UI-QuestTitleHighlight", "ADD")
      r.name = UI.Text(r, "GameFontHighlight", nil, "LEFT"); r.name:SetPoint("LEFT", 6, 0); r.name:SetWidth(colW - 90)
      r.num = UI.Text(r, "GameFontHighlight", nil, "RIGHT"); r.num:SetPoint("RIGHT", -6, 0); r.num:SetWidth(70)
      if r.name.SetWordWrap then r.name:SetWordWrap(false) end
      r:SetScript("OnEnter", function(s)
        if not s.set then return end
        GameTooltip:SetOwner(s, "ANCHOR_RIGHT")
        TCF:SetTooltip(GameTooltip, s.set, ownedGear())
        GameTooltip:Show()
      end)
      r:SetScript("OnLeave", function() GameTooltip:Hide() end)
      r:Hide()
      view.rows[i] = r
    end
    f.setsView = view
  end
  view:Show()
  local got = ownedGear()
  local list, complete, fits = {}, 0, 0
  for _, set in ipairs(TCF.ITEM_SETS) do
    if setFits(set, ctx.classKey) then
      fits = fits + 1
      local have = 0
      for _, id in ipairs(set.items) do if got[id] then have = have + 1 end end
      local done = have >= #set.items
      if done then complete = complete + 1 end
      if ctx.passes(done) then list[#list + 1] = { set = set, have = have } end
    end
  end
  ctx.collected(complete, fits)
  local first = ctx.setPages(#list, SROWS * SCOLS)
  for i, r in ipairs(view.rows) do
    local e = list[first + i]
    if e then
      local set, lv, q = e.set, 0, 1
      for _, id in ipairs(set.items) do
        local g = TCF.GEAR[id]
        if g then lv = max(lv, g.req or 0); q = max(q, g.q) end
      end
      local col = TCF.RARITY[q].hex
      r.set = set
      r.name:SetText(string.format("|c%s%s|r  |cff999999Lv %d|r", col, set.name, lv))
      r.num:SetText(string.format("%s%d / %d|r", e.have >= #set.items and "|cff20ff20" or "|cffffffff", e.have, set.total))
      r:Show()
    else
      r:Hide()
    end
  end
  return #list
end
