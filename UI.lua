-- TapCatForever: HUD cat, main window (wardrobe / shop / achievements / settings), minimap button
local ADDON, TCF = ...

local floor, min, max = math.floor, math.min, math.max
local BT = BackdropTemplateMixin and "BackdropTemplate" or nil
local ART = TCF.ART_PATH
local function coinStr(n, size) return "|T" .. ART .. "ui_coin:" .. (size or 14) .. ":" .. (size or 14) .. "|t " .. TCF.Commas(n) end

local BACKDROP_PANEL = {
  bgFile = "Interface\\Tooltips\\UI-Tooltip-Background", edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border",
  tile = true, tileSize = 16, edgeSize = 14, insets = { left = 3, right = 3, top = 3, bottom = 3 },
}
local BACKDROP_DIALOG = {
  bgFile = "Interface\\DialogFrame\\UI-DialogBox-Background-Dark", edgeFile = "Interface\\DialogFrame\\UI-DialogBox-Border",
  tile = true, tileSize = 32, edgeSize = 32, insets = { left = 11, right = 12, top = 12, bottom = 11 },
}

local function Panel(parent, w, h, alpha)
  local f = CreateFrame("Frame", nil, parent, BT)
  if w then f:SetSize(w, h) end
  if f.SetBackdrop then
    f:SetBackdrop(BACKDROP_PANEL)
    f:SetBackdropColor(0.06, 0.05, 0.09, alpha or 0.85)
    f:SetBackdropBorderColor(0.45, 0.40, 0.55, 1)
  end
  return f
end

local function Text(parent, font, txt, justify)
  local fs = parent:CreateFontString(nil, "OVERLAY", font or "GameFontHighlight")
  if txt then fs:SetText(txt) end
  if justify then fs:SetJustifyH(justify) end
  return fs
end

local function Button(parent, txt, w, h, onClick)
  local b = CreateFrame("Button", nil, parent, "UIPanelButtonTemplate")
  b:SetSize(w or 100, h or 22)
  b:SetText(txt)
  b:SetScript("OnClick", onClick)
  return b
end

local function Tip(owner, fn)
  owner:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT"); fn(GameTooltip, self); GameTooltip:Show()
  end)
  owner:SetScript("OnLeave", function() GameTooltip:Hide() end)
end

-- noSource: leave out the "how to get" lines (the Compendium adds its own section)
function TCF:ItemTooltip(tt, it, noSource)
  local col = TCF.RARITY[it.rarity].color
  tt:AddLine("|T" .. TCF.Icon(it.icon) .. ":20:20|t " .. it.name, col[1], col[2], col[3])
  tt:AddLine(TCF.RARITY[it.rarity].name .. " " .. TCF.SLOT_BY_KEY[it.slot].name, 1, 1, 1)
  -- crafted cosmetics and skins (Compendium.lua knows the recipes)
  local crafted = TCF.CraftSourceOf and TCF.CraftSourceOf(it)
  if crafted then
    tt:AddLine("Cosmetic only (no stats)", 0.82, 0.55, 1)
  else
    tt:AddLine("Cosmetic: changes your cat's look only, no stats", 0.82, 0.55, 1)
  end
  if it.class then
    local cl = TCF.CLASS_BY_KEY[it.class]
    tt:AddLine(cl.name .. " only", cl.color[1], cl.color[2], cl.color[3])
  else
    tt:AddLine("Any class", 0.7, 0.7, 0.7)
  end
  local owned = self.db.owned[it.id]
  if owned then
    tt:AddLine("Collected" .. (owned > 1 and (" (x" .. owned .. ")") or ""), 0.3, 1, 0.3)
    -- the full recipe is in "how to get"; once collected, just say how it is made
    local how = crafted and not noSource and TCF.CraftShortLine and TCF.CraftShortLine(it)
    if how then tt:AddLine(how, 1, 0.82, 0, true) end
  elseif not noSource and self.HowToGet then
    -- how to get it (Compendium.lua), the same lines the Compendium shows
    for _, line in ipairs(self:HowToGet(it)) do tt:AddLine(line, 1, 0.82, 0, true) end
  end
end

---------------------------------------------------------------- item preview cell
local function CropToBounds(tex, art)
  local b = TCF.ArtBounds[art] or { 0, 0, 1, 1 }
  local w, h = b[3] - b[1], b[4] - b[2]
  local s = min(1, max(w, h) + 0.06)
  local cx, cy = (b[1] + b[3]) / 2, (b[2] + b[4]) / 2
  local l, t = cx - s / 2, cy - s / 2
  l = max(0, min(1 - s, l)); t = max(0, min(1 - s, t))
  tex:SetTexCoord(l, l + s, t, t + s)
end

-- Cartoon cat pictures (skins, fur colours, fur patterns): the same drawings as the cat on
-- screen (TCF.VEC "cat:" keys), tinted and fitted to the box. Draw order follows CatVector.lua.
-- { texture slot, layer, sublevel }. ARTWORK 0-2 belong to the cosmetic layers (hidden here).
local CAT_LAYERS = {
  { "body_t", "BORDER", -5 }, { "belly", "BORDER", -4 }, { "body_marks_t", "BORDER", -3 }, { "patB", "BORDER", -2 },
  { "patB2", "BORDER", -1 }, { "body_line", "BORDER", 0 }, { "mane", "BORDER", 1 },
  { "head_t", "ARTWORK", 3 }, { "head_marks_t", "ARTWORK", 4 }, { "patH", "ARTWORK", 5 }, { "patH2", "ARTWORK", 6 },
  { "face", "ARTWORK", 7 }, { "iris", "OVERLAY", -8 },
  { "paw_L_t", "OVERLAY", -6 }, { "patPL", "OVERLAY", -5 }, { "paw_L", "OVERLAY", -4 },
  { "paw_R_t", "OVERLAY", -3 }, { "patPR", "OVERLAY", -2 }, { "paw_R", "OVERLAY", -1 },
}
local CAT_STRIPE = 0.8  -- plain tabby stripes: the fur colour, darker (as in CatVector.lua)

-- fur colour, fur alpha, pattern art, pattern colours, eye colour, mane colour, plain stripes?
local function catLook(it)
  if it.slot == "skin" then
    local ov = it.overlay
    return it.c1, it.alpha or 1, ov and ov[1], ov and ov[2], ov and (ov[3] or ov[2]), it.eyes, it.mane, false
  elseif it.slot == "fur" then
    return it.c1, it.alpha or 1, nil, nil, nil, nil, nil, true
  end
  -- a fur pattern on its own: shown on a fur that makes its colour stand out
  local c = it.c1
  local light = 0.3 * c[1] + 0.59 * c[2] + 0.11 * c[3] > 0.7
  return light and { 0.36, 0.34, 0.40 } or { 1.00, 0.92, 0.80 }, 1, it.art, it.c1, it.c2 or it.c1, nil, nil, false
end

local function SetCatPicture(self, it, desat)
  local V = TCF.VEC
  local T = self.catTex
  if not T then
    T = {}
    for _, l in ipairs(CAT_LAYERS) do T[l[1]] = self:CreateTexture(nil, l[2], nil, l[3]) end
    self.catTex = T
  end
  local fur, alpha, art, c1, c2, eyes, mane, plain = catLook(it)
  local white = { 1, 1, 1 }
  local want = {
    body_t = { "cat:body_t", fur, alpha }, belly = { "cat:belly" }, body_line = { "cat:body_line" },
    head_t = { "cat:head_t", fur, alpha }, face = { "cat:face_normal" },
    paw_L_t = { "cat:paw_L_down_t", fur, alpha }, paw_L = { "cat:paw_L_down" },
    paw_R_t = { "cat:paw_R_down_t", fur, alpha }, paw_R = { "cat:paw_R_down" },
  }
  if plain then
    local dark = { fur[1] * CAT_STRIPE, fur[2] * CAT_STRIPE, fur[3] * CAT_STRIPE }
    want.body_marks_t = { "cat:body_marks_t", dark, alpha }; want.head_marks_t = { "cat:head_marks_t", dark, alpha }
  end
  if art then
    local name = art:gsub("^pat_", ""):gsub("^skin_", "")
    local k = "cat:pat_" .. name .. "_"
    want.patB, want.patB2 = { k .. "body", c1 }, { k .. "body2", c2 }
    want.patH, want.patH2 = { k .. "head", c1 }, { k .. "head2", c2 }
    want.patPL, want.patPR = { k .. "paw_L", c1 }, { k .. "paw_R", c1 }
  end
  if mane then want.mane = { "cat:mane", mane } end
  if eyes then want.iris = { "cat:iris_normal", eyes } end
  -- fit everything that is drawn into the box
  local x0, y0, x1, y1 = 1e9, 1e9, -1e9, -1e9
  for _, w in pairs(want) do
    local e = V[w[1]]
    if e then x0 = min(x0, e[2]); y0 = min(y0, e[3]); x1 = max(x1, e[2] + e[4]); y1 = max(y1, e[3] + e[5]) end
  end
  local size = self:GetWidth()
  local k = size * 0.96 / max(x1 - x0, y1 - y0)
  local ox, oy = (size - (x1 - x0) * k) / 2, (size - (y1 - y0) * k) / 2
  for slot, t in pairs(T) do
    local w = want[slot]
    local e = w and V[w[1]]
    if e then
      local c = w[2] or white
      t:SetTexture(ART .. "v\\" .. e[1]); t:SetTexCoord(0, e[6], 0, e[7])
      t:ClearAllPoints(); t:SetSize(e[4] * k, e[5] * k)
      t:SetPoint("TOPLEFT", self, "TOPLEFT", ox + (e[2] - x0) * k, -(oy + (e[3] - y0) * k))
      t:SetVertexColor(c[1], c[2], c[3]); t:SetAlpha(w[3] or 1); t:SetDesaturated(desat); t:Show()
    else
      t:Hide()
    end
  end
end

local function ItemPicture(parent, size)
  local f = CreateFrame("Frame", nil, parent)
  f:SetSize(size, size)
  f.base = f:CreateTexture(nil, "ARTWORK", nil, 0); f.base:SetAllPoints()
  f.a = f:CreateTexture(nil, "ARTWORK", nil, 1); f.a:SetAllPoints()
  f.b = f:CreateTexture(nil, "ARTWORK", nil, 2); f.b:SetAllPoints()
  function f:SetItem(it, desat)
    self.base:Hide(); self.b:Hide()
    if self.model then self.model:Hide() end
    if self.catTex then for _, t in pairs(self.catTex) do t:Hide() end end
    desat = desat and true or false
    -- skins, fur colours and fur patterns: the cartoon cat itself
    if (it.slot == "skin" or it.slot == "fur" or it.slot == "pattern") and not (TCF.USE_3D and it.display3d)
      and TCF.VEC and TCF.VEC["cat:body_t"] then
      self.a:Hide()
      SetCatPicture(self, it, desat)
      return
    end
    local art = it.art
    if TCF.USE_3D and it.slot == "skin" and it.display3d then
      -- cats show as their real 3D model
      if not self.model then
        self.model = CreateFrame("PlayerModel", nil, self); self.model:SetAllPoints()
      end
      self.a:Hide()
      local ok = pcall(self.model.SetDisplayInfo, self.model, it.display3d)
      if ok then
        pcall(self.model.SetFacing, self.model, 0.5)
        pcall(self.model.SetPortraitZoom, self.model, 0.3)
        self.model:SetAlpha(desat and 0.45 or 1)
        self.model:Show()
        return
      end
    end
    -- cartoon cosmetics: fit their tinted layers into the box
    local vb = TCF.VEC and it.art and ("cos:" .. it.art .. ":")
    if vb and (TCF.VEC[vb .. "a"] or TCF.VEC[vb .. "f"]) then
      local x0, y0, x1, y1 = 1e9, 1e9, -1e9, -1e9
      for _, p in ipairs({ "a", "b", "f" }) do
        local e = TCF.VEC[vb .. p]
        if e then x0 = math.min(x0, e[2]); y0 = math.min(y0, e[3]); x1 = math.max(x1, e[2] + e[4]); y1 = math.max(y1, e[3] + e[5]) end
      end
      local size = self:GetWidth()
      local k = size * 0.92 / math.max(x1 - x0, y1 - y0)
      local ox, oy = (size - (x1 - x0) * k) / 2, (size - (y1 - y0) * k) / 2
      local c2 = it.c2 or it.c1
      for p, t in pairs({ a = self.base, b = self.a, f = self.b }) do
        local e = TCF.VEC[vb .. p]
        if e then
          t:SetTexture(TCF.ART_PATH .. "v\\" .. e[1]); t:SetTexCoord(0, e[6], 0, e[7])
          t:ClearAllPoints(); t:SetSize(e[4] * k, e[5] * k); t:SetPoint("TOPLEFT", self, "TOPLEFT", ox + (e[2] - x0) * k, -(oy + (e[3] - y0) * k))
          local c = p == "a" and it.c1 or p == "b" and c2 or { 1, 1, 1 }
          t:SetVertexColor(c[1], c[2], c[3]); t:SetDesaturated(desat); t:Show()
        else t:Hide() end
      end
      self.restore = true
      return
    end
    if self.restore then
      -- back to full-box layers for pixel-style pictures
      self.restore = nil
      for _, t in ipairs({ self.base, self.a, self.b }) do t:ClearAllPoints(); t:SetAllPoints(self) end
    end
    if it.slot == "tap" then
      self.a:SetTexture(ART .. "v\\t_" .. art); self.a:SetTexCoord(0, 1, 0, 1)
      self.a:SetVertexColor(it.c1[1], it.c1[2], it.c1[3]); self.a:SetDesaturated(desat); self.a:Show()
      return
    end
    if it.slot == "skin" then
      self.base:SetTexture(ART .. "cat_fur", nil, nil, "NEAREST"); CropToBounds(self.base, "cat_fur")
      self.base:SetVertexColor(it.c1[1], it.c1[2], it.c1[3]); self.base:SetDesaturated(desat); self.base:Show()
      local ov = it.overlay or (it.mane and { "skin_mane", it.mane })
      if ov then
        local pb = TCF.PART_B[ov[1]]
        self.a:SetTexture(ART .. ov[1] .. (pb and "_a" or ""), nil, nil, "NEAREST"); CropToBounds(self.a, "cat_fur")
        self.a:SetVertexColor(ov[2][1], ov[2][2], ov[2][3]); self.a:SetDesaturated(desat); self.a:Show()
        if pb and ov[3] then
          self.b:SetTexture(ART .. ov[1] .. "_b", nil, nil, "NEAREST"); CropToBounds(self.b, "cat_fur")
          self.b:SetVertexColor(ov[3][1], ov[3][2], ov[3][3]); self.b:SetDesaturated(desat); self.b:Show()
        end
      else self.a:Hide() end
      return
    end
    if it.slot == "fur" or it.slot == "pattern" then
      self.base:SetTexture(ART .. "cat_fur", nil, nil, "NEAREST")
      CropToBounds(self.base, "cat_fur")
      local c = it.slot == "fur" and it.c1 or { 0.85, 0.85, 0.85 }
      self.base:SetVertexColor(c[1], c[2], c[3]); self.base:Show()
      if it.slot == "fur" then self.a:Hide(); self.base:SetDesaturated(desat); return end
      self.base:SetDesaturated(desat)
      CropToBounds(self.a, "cat_fur"); CropToBounds(self.b, "cat_fur")
    else
      CropToBounds(self.a, art); CropToBounds(self.b, art)
    end
    local pb = TCF.PART_B[art]
    if it.slot == "effect" then
      self.a:SetTexture(ART .. art); self.a:SetTexCoord(0, 1, 0, 1)
    else
      self.a:SetTexture(ART .. art .. (pb and "_a" or ""), nil, nil, "NEAREST")
    end
    self.a:SetVertexColor(it.c1[1], it.c1[2], it.c1[3]); self.a:SetDesaturated(desat); self.a:Show()
    if pb then
      local c2 = it.c2 or it.c1
      self.b:SetTexture(ART .. art .. "_b", nil, nil, "NEAREST")
      self.b:SetVertexColor(c2[1], c2[2], c2[3]); self.b:SetDesaturated(desat); self.b:Show()
    end
  end
  return f
end

local function ItemCell(parent, size)
  local b = CreateFrame("Button", nil, parent, BT)
  b:SetSize(size, size)
  if b.SetBackdrop then b:SetBackdrop(BACKDROP_PANEL) end
  b.pic = ItemPicture(b, size - 8); b.pic:SetPoint("CENTER")
  b.check = b:CreateTexture(nil, "OVERLAY"); b.check:SetSize(18, 18)
  b.check:SetPoint("TOPRIGHT", 2, 2); b.check:SetTexture("Interface\\Buttons\\UI-CheckBox-Check")
  b.count = Text(b, "NumberFontNormalSmall", nil, "RIGHT"); b.count:SetPoint("BOTTOMRIGHT", -4, 4)
  b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  function b:SetItem(it, owned, equipped)
    self.item = it
    local col = TCF.RARITY[it.rarity].color
    if self.SetBackdrop then
      self:SetBackdropColor(0.05, 0.05, 0.08, owned and 0.95 or 0.6)
      self:SetBackdropBorderColor(col[1], col[2], col[3], owned and 1 or 0.45)
    end
    self.pic:SetItem(it, not owned)
    self.pic:SetAlpha(owned and 1 or 0.35)
    self.check:SetShown(equipped and true or false)
    local n = TCF.db.owned[it.id]
    self.count:SetText((n and n > 1) and ("x" .. n) or "")
    self:Show()
  end
  return b
end

-- shared with the page files (UI_*.lua)
TCF.UI = TCF.UI or {}
TCF.UI.Panel, TCF.UI.Text, TCF.UI.Button, TCF.UI.Tip = Panel, Text, Button, Tip
TCF.UI.ItemCell, TCF.UI.ItemPicture, TCF.UI.coinStr = ItemCell, ItemPicture, coinStr
TCF.UI.BACKDROP_PANEL, TCF.UI.BACKDROP_DIALOG, TCF.UI.BT = BACKDROP_PANEL, BACKDROP_DIALOG, BT
TCF.UI.Builders = TCF.UI.Builders or {}

-- A square button showing a real gear item (WoW icon, quality border)
function TCF.UI.GearButton(parent, size)
  local b = CreateFrame("Button", nil, parent, BT)
  b:SetSize(size, size)
  if b.SetBackdrop then b:SetBackdrop(BACKDROP_PANEL) end
  b.icon = b:CreateTexture(nil, "ARTWORK"); b.icon:SetPoint("TOPLEFT", 4, -4); b.icon:SetPoint("BOTTOMRIGHT", -4, 4)
  b.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
  b.count = Text(b, "NumberFontNormalSmall", nil, "RIGHT"); b.count:SetPoint("BOTTOMRIGHT", -3, 3)
  b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  function b:SetGear(it, emptyIcon)
    self.item = it
    if it then
      self.icon:SetTexture(TCF.Icon(it.icon)); self.icon:SetDesaturated(false); self.icon:SetAlpha(1)
      local col = TCF.RARITY[it.q].color
      if self.SetBackdropBorderColor then self:SetBackdropBorderColor(col[1], col[2], col[3], 1); self:SetBackdropColor(0.05, 0.05, 0.08, 0.95) end
    else
      self.icon:SetTexture(TCF.Icon(emptyIcon or "INV_Misc_QuestionMark")); self.icon:SetDesaturated(true); self.icon:SetAlpha(0.35)
      if self.SetBackdropBorderColor then self:SetBackdropBorderColor(0.35, 0.32, 0.42, 1); self:SetBackdropColor(0.05, 0.05, 0.08, 0.8) end
    end
  end
  return b
end

-- Full tooltip for a real gear item
local STAT_LINES = {
  { "str", "+%d Strength" }, { "agi", "+%d Agility" }, { "sta", "+%d Stamina" }, { "int", "+%d Intellect" }, { "spi", "+%d Spirit" },
}
local EQUIP_LINES = {
  { "ap", "Equip: +%d Attack Power." }, { "rap", "Equip: +%d Ranged Attack Power." }, { "sp", "Equip: Increases spell power by %d." },
  { "heal", "Equip: Increases healing by up to %d." }, { "critr", "Equip: Improves critical strike rating by %d." },
  { "crit", "Equip: Improves your chance to get a critical strike by %d%%." }, { "hitr", "Equip: Improves hit rating by %d." },
  { "hit", "Equip: Improves your chance to hit by %d%%." }, { "def", "Equip: Increases defense rating by %d." },
  { "dodger", "Equip: Increases your dodge rating by %d." }, { "mp5", "Equip: Restores %d mana per 5 sec." },
}
function TCF:GearTooltip(tt, it, class)
  class = class or self.db.class
  local st = TCF.GearStats(it)
  local col = TCF.RARITY[it.q].color
  tt:AddLine(it.name, col[1], col[2], col[3])
  tt:AddLine("Item Level " .. it.ilvl, 1, 0.82, 0)
  tt:AddDoubleLine(TCF.ITEM_SLOT_NAMES[it.slot] or "", TCF.ITEM_TYPE_NAMES[it.sub] or "", 1, 1, 1, 1, 1, 1)
  if st.min then
    tt:AddDoubleLine(string.format("%d - %d Damage", st.min, st.max), st.spd and string.format("Speed %.2f", st.spd) or "", 1, 1, 1, 1, 1, 1)
    if st.dps then tt:AddLine(string.format("(%.1f damage per second)", st.dps), 1, 1, 1) end
  end
  if st.arm then tt:AddLine(st.arm .. " Armor", 1, 1, 1) end
  if st.blk then tt:AddLine(st.blk .. " Block", 1, 1, 1) end
  for _, l in ipairs(STAT_LINES) do if st[l[1]] then tt:AddLine(string.format(l[2], st[l[1]]), 1, 1, 1) end end
  if it.cls then tt:AddLine("Classes: " .. it.cls:gsub(",", ", "):lower():gsub("(%a)(%a*)", function(a, b) return a:upper() .. b end), 1, 1, 1) end
  if it.req > 0 then
    local ok = self:CD(class).level >= it.req
    tt:AddLine("Requires class level " .. it.req, ok and 1 or 1, ok and 1 or 0.2, ok and 1 or 0.2)
  end
  for _, l in ipairs(EQUIP_LINES) do if st[l[1]] then tt:AddLine(string.format(l[2], st[l[1]]), 0.12, 1, 0) end end
  if it.crafted then
    -- "Crafted by Blacksmithing (skill 125)"; its Sell gives Trade Gold, not TapCoins
    local p = TCF.PROF_BY_KEY and TCF.PROF_BY_KEY[it.crafted]
    local skill = it.craftSkill
    tt:AddLine(string.format("Crafted by %s%s", p and p.name or "a profession", (skill and skill > 0) and (" (skill " .. skill .. ")") or ""), 0.6, 0.8, 1, true)
  elseif it.tier > 0 then
    local t = TCF.TIERS[it.tier]
    local src = it.boss > 0 and t.bosses[it.boss][1] or "enemies"
    tt:AddLine(string.format("Drops from %s (%s)%s", src, t.name, it.dc > 0 and string.format(" - %.1f%%", it.dc / 10) or ""), 0.6, 0.8, 1, true)
  else
    tt:AddLine("World drop", 0.6, 0.8, 1)
  end
  if not self:GearUsable(it, class) then tt:AddLine("Your " .. TCF.CLASS_BY_KEY[class].name .. " can't use this.", 1, 0.2, 0.2)
  elseif not self:GearSuits(it, class) then tt:AddLine("Not ideal for a " .. TCF.CLASS_BY_KEY[class].name .. " (wrong stats or weapon type).", 1, 0.6, 0.2, true) end
  local have = TCF:Bag()[it.id]
  if have then tt:AddLine("In your collection" .. (have > 1 and (" (x" .. have .. ")") or ""), 0.3, 1, 0.3) end
end

---------------------------------------------------------------- HUD (the cat on screen)
local CAT_SIZE = 120

function TCF:CreateHUD()
  local ui = self.db.ui
  local f = CreateFrame("Frame", "TapCatForeverFrame", UIParent)
  f:SetSize(CAT_SIZE, CAT_SIZE + 40)
  f:SetFrameStrata("MEDIUM")
  f:SetMovable(true); f:SetClampedToScreen(true)
  f:RegisterForDrag("LeftButton")
  self.hud = f

  local cat = TCF.CreateCat(f, CAT_SIZE)
  cat.frame:SetPoint("TOP", f, "TOP", 0, 0)
  self.cat = cat

  -- info block
  local info = CreateFrame("Frame", nil, f)
  info:SetSize(CAT_SIZE + 40, 40); info:SetPoint("TOP", cat.frame, "BOTTOM", 0, -4)
  f.info = info
  f.level = Text(info, "GameFontNormalSmall"); f.level:SetPoint("TOP", 0, 0)
  local xp = CreateFrame("StatusBar", nil, info, BT)
  xp:SetSize(CAT_SIZE - 20, 6); xp:SetPoint("TOP", f.level, "BOTTOM", 0, -2)
  xp:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar")
  xp:SetStatusBarColor(0.58, 0.0, 0.55)
  local xbg = xp:CreateTexture(nil, "BACKGROUND"); xbg:SetAllPoints(); xbg:SetColorTexture(0, 0, 0, 0.55)
  f.xp = xp
  f.stats = Text(info, "GameFontHighlightSmall"); f.stats:SetPoint("TOP", xp, "BOTTOM", 0, -2)

  -- unopened-chest badge (click to open the Treasure Bag)
  local badge = CreateFrame("Button", nil, f)
  badge:SetSize(26, 26); badge:SetPoint("BOTTOMRIGHT", cat.frame, "BOTTOMRIGHT", 6, 4)
  local bi = badge:CreateTexture(nil, "ARTWORK"); bi:SetAllPoints(); bi:SetTexture(TCF.Icon("INV_Box_02"))
  badge.count = Text(badge, "NumberFontNormal", nil, "RIGHT"); badge.count:SetPoint("BOTTOMRIGHT", 3, -3)
  badge:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  badge:SetScript("OnClick", function() TCF:ToggleBag() end)
  Tip(badge, function(tt)
    tt:AddLine("Unopened chests", 1, 0.82, 0)
    tt:AddLine("Click to open your Treasure Bag.", 1, 1, 1)
  end)
  f.badge = badge

  -- input
  f:SetScript("OnDragStart", function(s)
    if not ui.locked then s.dragging = true; s:StartMoving() end
  end)
  f:SetScript("OnDragStop", function(s)
    s:StopMovingOrSizing()
    local p, _, rp, x, y = s:GetPoint()
    ui.point = { p, rp, x, y }
    s.justDragged = true
    s.dragging = false
  end)
  f:SetScript("OnMouseUp", function(s, button)
    if s.justDragged then s.justDragged = false; return end
    if button == "RightButton" then
      TCF:ToggleWindow()
    elseif button == "LeftButton" then
      TCF.db.stats.pets = TCF.db.stats.pets + 1
      TCF:MarkDirty()
      cat:Pet()
    end
  end)
  f:SetScript("OnMouseWheel", function(s, delta)
    if IsControlKeyDown() then
      ui.scale = max(0.3, min(3, ui.scale + delta * 0.05)); s:ApplySettings()
    elseif IsShiftKeyDown() then
      ui.alpha = max(0.1, min(1, ui.alpha + delta * 0.05)); s:ApplySettings()
    end
    if TCF.window and TCF.window:IsShown() then TCF.window:RefreshSettings() end
  end)
  Tip(f, function(tt)
    tt:AddLine("TapCatForever", 1, 0.72, 0.3)
    local cl = TCF.CLASS_BY_KEY[TCF.db.class]
    tt:AddLine(string.format("Level %d %s %s", TCF:CD().level, cl.name, TCF:GetTitle()), 1, 1, 1)
    local friends = TCF.PartyCount and TCF:PartyCount() or 0
    if friends > 0 then
      tt:AddLine(string.format("Party bonus: your taps count +%d%%", floor((TCF:PartyTapMult() - 1) * 100 + 0.5)), 0.4, 1, 0.4)
      tt:AddLine(string.format(friends == 1 and "%d party member has TapCatForever" or "%d party members have TapCatForever", friends), 0.8, 0.8, 0.8)
    end
    tt:AddLine(" ")
    tt:AddLine("Left-click: pet the cat", 0.8, 0.8, 0.8)
    tt:AddLine("Right-click: wardrobe, shop & settings", 0.8, 0.8, 0.8)
    if not ui.locked then tt:AddLine("Drag: move", 0.8, 0.8, 0.8) end
    tt:AddLine("Ctrl+wheel: size   Shift+wheel: opacity", 0.8, 0.8, 0.8)
  end)

  -- A wheel-enabled frame swallows every scroll, so the wheel is only taken while Ctrl or
  -- Shift is held; plain scrolls over the cat still reach the camera zoom.
  function f:UpdateWheel()
    local want = self.interactive and (IsControlKeyDown() or IsShiftKeyDown()) and true or false
    if want ~= self.wheelOn and self.EnableMouseWheel then self.wheelOn = want; self:EnableMouseWheel(want) end
  end
  if pcall(f.RegisterEvent, f, "MODIFIER_STATE_CHANGED") then
    f:SetScript("OnEvent", function(s) s:UpdateWheel() end)
  else
    -- no modifier event in this client: check the keys only while the mouse is over the cat
    f:HookScript("OnEnter", function(s) s:SetScript("OnUpdate", s.UpdateWheel) end)
    f:HookScript("OnLeave", function(s) s:SetScript("OnUpdate", nil); s:UpdateWheel() end)
  end

  function f:ResetPosition()
    ui.point = { "BOTTOM", "BOTTOM", 0, 160 }
    self:ApplySettings()
  end

  function f:ApplySettings()
    self:SetScale(ui.scale)
    self:SetAlpha(ui.alpha)
    -- text keeps its own size no matter how small the cat is
    self.info:SetScale((ui.textScale or 1) / ui.scale)
    -- text block below the cat or above it (default). The cat moves to the other end of the
    -- frame so the frame always covers cat + text: no empty click-eating strip, and the
    -- screen clamp keeps the text on screen too. With no text shown the frame shrinks to the cat.
    local showInfo = not ui.catOnly
    self:SetHeight((showInfo and (ui.showLevel or ui.showXP or ui.showTaps or ui.showCoins)) and CAT_SIZE + 40 or CAT_SIZE)
    self.info:ClearAllPoints(); cat.frame:ClearAllPoints()
    if ui.textAbove then
      cat.frame:SetPoint("BOTTOM", self, "BOTTOM", 0, 0)
      self.info:SetPoint("BOTTOM", cat.frame, "TOP", 0, 4)
    else
      cat.frame:SetPoint("TOP", self, "TOP", 0, 0)
      self.info:SetPoint("TOP", cat.frame, "BOTTOM", 0, -4)
    end
    -- keep the cat's feet where they were when the frame's layout changes (text above/below,
    -- text hidden, or the first load after 1.3.3, when the frame was 160 tall with the cat on top)
    local height = (showInfo and (ui.showLevel or ui.showXP or ui.showTaps or ui.showCoins)) and CAT_SIZE + 40 or CAT_SIZE
    local p = ui.point
    local function catBottom(h, above)
      local a = p[1]
      local frameBottom = a:find("BOTTOM") and 0 or a:find("TOP") and -h or -h / 2
      return frameBottom + (above and 0 or h - CAT_SIZE)
    end
    local was = ui.hudLayout or { CAT_SIZE + 40, false }
    local now = { height, ui.textAbove and true or false }
    if was[1] ~= now[1] or was[2] ~= now[2] then
      p[4] = p[4] + catBottom(was[1], was[2]) - catBottom(now[1], now[2])
      ui.hudLayout = now
    end
    self:ClearAllPoints()
    self:SetPoint(p[1], UIParent, p[2], p[3], p[4])
    self:SetShown(ui.shown)
    local interactive = not (ui.locked and ui.clickThrough)
    self.interactive = interactive
    self:EnableMouse(interactive)
    self:UpdateWheel()
    self.level:SetShown(showInfo and ui.showLevel)
    self.xp:SetShown(showInfo and ui.showXP)
    self.stats:SetShown(showInfo and (ui.showTaps or ui.showCoins))
    self:Refresh()
  end

  function f:Refresh()
    local db = TCF.db
    local cd = TCF:CD()
    local cl = TCF.CLASS_BY_KEY[db.class]
    self.level:SetText(string.format("Lv %d |cff%02x%02x%02x%s|r", cd.level, cl.color[1] * 255, cl.color[2] * 255, cl.color[3] * 255, cl.name))
    self.xp:SetMinMaxValues(0, TCF.XPForLevel(cd.level))
    self.xp:SetValue(cd.xp)
    local parts = {}
    if ui.showTaps then parts[#parts + 1] = TCF.Commas(db.taps) .. " taps" end
    if ui.showCoins then parts[#parts + 1] = coinStr(db.coins, 11) end
    self.stats:SetText(table.concat(parts, "   "))
    local n = TCF:ChestCount()
    self.badge:Hide()  -- chests are opened from the window's Treasure Bag button
    self.badge.count:SetText(n)
  end

  f:ApplySettings()
end

---------------------------------------------------------------- main window
function TCF:ToggleWindow()
  if not self.window then self:CreateWindow() end
  if self.window:IsShown() then self.window:Hide() else self.window:Show() end
end

function TCF:CreateWindow()
  local W, H = 920, 620
  local win = CreateFrame("Frame", "TapCatForeverWindow", UIParent, BT)
  win:SetSize(W, H); win:SetPoint("CENTER")
  win:SetFrameStrata("HIGH"); win:SetToplevel(true)
  win:SetMovable(true); win:EnableMouse(true); win:SetClampedToScreen(true)
  win:RegisterForDrag("LeftButton")
  win:SetScript("OnDragStart", win.StartMoving)
  win:SetScript("OnDragStop", win.StopMovingOrSizing)
  if win.SetBackdrop then win:SetBackdrop(BACKDROP_DIALOG) end
  win:Hide()
  tinsert(UISpecialFrames, "TapCatForeverWindow")
  self.window = win

  local title = Text(win, "GameFontNormalLarge", "|cffffb84dTapCat|r|cffffffffForever|r")
  title:SetPoint("TOPLEFT", 22, -18)
  local ver = Text(win, "GameFontDisableSmall", "v" .. TCF.version); ver:SetPoint("LEFT", title, "RIGHT", 8, -1)
  local close = CreateFrame("Button", nil, win, "UIPanelCloseButton"); close:SetPoint("TOPRIGHT", -6, -6)
  local coins = Text(win, "GameFontHighlightLarge"); coins:SetPoint("TOPRIGHT", -44, -18)
  local bagBtn = CreateFrame("Button", nil, win)
  bagBtn:SetSize(30, 30); bagBtn:SetPoint("RIGHT", coins, "LEFT", -18, 0)
  local bagIcon = bagBtn:CreateTexture(nil, "ARTWORK"); bagIcon:SetAllPoints(); bagIcon:SetTexture(TCF.Icon("INV_Misc_Bag_10"))
  bagBtn:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
  local bagCount = Text(bagBtn, "NumberFontNormal", nil, "RIGHT"); bagCount:SetPoint("BOTTOMRIGHT", 2, -2)
  local bagLabel = Text(win, "GameFontNormalSmall", "Treasure Bag"); bagLabel:SetPoint("RIGHT", bagBtn, "LEFT", -4, 0)
  bagBtn:SetScript("OnClick", function() TCF:ToggleBag(); TCF:PlaySound("click") end)
  Tip(bagBtn, function(tt)
    tt:AddLine("Treasure Bag", 1, 0.82, 0)
    tt:AddLine("Unopened chests from quests, dungeons, raids, expeditions and level-ups.", 1, 1, 1, true)
  end)

  -- the Compendium (Compendium.lua): every item in the game and how to get it
  local compBtn = Button(win, "Compendium", 120, 22, function() TCF:ToggleCompendium(); TCF:PlaySound("click") end)
  compBtn:SetPoint("TOP", 0, -15)  -- between the title (ends near x 200) and the Treasure Bag label (starts near x 610)
  Tip(compBtn, function(tt)
    tt:AddLine("Compendium", 1, 0.82, 0)
    tt:AddLine("Every skin, cosmetic, effect and piece of gear, what you have, and how to get the rest.", 1, 1, 1, true)
  end)

  local fbBtn = Button(win, "Feedback", 84, 22, function() TCF:ShowFeedback(); TCF:PlaySound("click") end)
  fbBtn:SetPoint("LEFT", compBtn, "RIGHT", 8, 0)
  Tip(fbBtn, function(tt)
    tt:AddLine("Send feedback", 1, 0.82, 0)
    tt:AddLine("Found a bug or have an idea? This shows links to report it.", 1, 1, 1, true)
  end)

  local tabs, pages = {}, {}
  local TAB_GEAR, TAB_ADVENTURE, TAB_ABILITIES, TAB_EXPEDITIONS, TAB_PROFESSIONS = 1, 2, 3, 4, 5
  local TAB_WARDROBE, TAB_QUESTS, TAB_SHOP, TAB_ACH, TAB_SETTINGS = 6, 7, 8, 9, 10
  local tabNames = { "Gear", "Adventure", "Abilities", "Expeditions", "Professions",
                     "Appearance", "Quests", "Shop", "Achievements", "Settings" }
  local builderKeys = { [TAB_GEAR] = "gear", [TAB_ADVENTURE] = "adventure", [TAB_ABILITIES] = "abilities",
                        [TAB_EXPEDITIONS] = "expeditions", [TAB_PROFESSIONS] = "professions" }
  local pageRefresh = {}
  win.TAB_GEAR = TAB_GEAR
  local SelectTab -- defined below
  function win:SelectTab(i) SelectTab(i) end

  ------------------------------------------------ left column: gear paperdoll, class, stats
  local left = Panel(win, 316, H - 66); left:SetPoint("TOPLEFT", 16, -46)
  local stage = Panel(left, 212, 252, 0.95); stage:SetPoint("TOP", 0, -10)
  local stageBg = stage:CreateTexture(nil, "BACKGROUND", nil, 1); stageBg:SetPoint("TOPLEFT", 4, -4); stageBg:SetPoint("BOTTOMRIGHT", -4, 4)
  stageBg:SetColorTexture(0.12, 0.10, 0.18, 1)
  -- the profile cat sits still (it only blinks); it taps on the Adventure tab
  local preview = TCF.CreateCat(stage, 200, { preview = true })
  preview.frame:SetPoint("CENTER", 0, -2)
  win.preview = preview

  local DOLL_LEFT = { "HEAD", "NECK", "SHOULDER", "BACK", "CHEST", "WRIST", "WAIST" }
  local DOLL_RIGHT = { "HANDS", "LEGS", "FEET", "FINGER1", "FINGER2", "TRINKET1", "TRINKET2" }
  local DOLL_BOTTOM = { "MAINHAND", "OFFHAND", "RANGED" }
  local dollBtns = {}
  win.gearSlot = nil
  local function DollButton(key)
    local s = TCF.GEAR_SLOT_BY_KEY[key]
    local b = TCF.UI.GearButton(left, 34)
    b.key = key
    b.sel = b:CreateTexture(nil, "OVERLAY", nil, 2); b.sel:SetPoint("TOPLEFT", -4, 4); b.sel:SetPoint("BOTTOMRIGHT", 4, -4)
    b.sel:SetTexture("Interface\\Buttons\\CheckButtonHilight"); b.sel:SetBlendMode("ADD")
    b:RegisterForClicks("LeftButtonUp", "RightButtonUp")
    b:SetScript("OnClick", function(_, button)
      if button == "RightButton" then TCF:UnequipGear(key)
      else win.gearSlot = key; win.gearPage = 1; SelectTab(TAB_GEAR) end
      TCF:PlaySound("click")
    end)
    b:SetScript("OnEnter", function(self)
      GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
      if self.item then TCF:GearTooltip(GameTooltip, self.item) else GameTooltip:AddLine(s.name, 1, 0.82, 0); GameTooltip:AddLine("Empty", 0.6, 0.6, 0.6) end
      GameTooltip:AddLine(" ")
      GameTooltip:AddLine("Left-click: choose gear for this slot", 0, 1, 0)
      GameTooltip:AddLine("Right-click: take it off", 0, 1, 0)
      GameTooltip:Show()
    end)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    function b:Update()
      local id = TCF:GearEquipped()[key]
      self:SetGear(id and TCF.GEAR[id], s.icon)
      self.sel:SetShown(win.tab == TAB_GEAR and win.gearSlot == key)
    end
    dollBtns[#dollBtns + 1] = b
    return b
  end
  for i, k in ipairs(DOLL_LEFT) do DollButton(k):SetPoint("TOPRIGHT", stage, "TOPLEFT", -6, -(i - 1) * 36) end
  for i, k in ipairs(DOLL_RIGHT) do DollButton(k):SetPoint("TOPLEFT", stage, "TOPRIGHT", 6, -(i - 1) * 36) end
  for i, k in ipairs(DOLL_BOTTOM) do DollButton(k):SetPoint("TOP", stage, "BOTTOM", (i - 2) * 40, -6) end

  local className = Text(left, "GameFontNormal"); className:SetPoint("TOP", stage, "BOTTOM", 0, -46)
  local classBtns = {}
  for i, cl in ipairs(TCF.CLASSES) do
    local b = CreateFrame("Button", nil, left)
    b:SetSize(28, 28)
    b:SetPoint("TOPLEFT", left, "TOPLEFT", 11 + (i - 1) * 33, -326)
    local t = b:CreateTexture(nil, "ARTWORK"); t:SetAllPoints()
    TCF.SetClassIcon(t, cl.key)
    b.sel = b:CreateTexture(nil, "OVERLAY"); b.sel:SetPoint("TOPLEFT", -5, 5); b.sel:SetPoint("BOTTOMRIGHT", 5, -5)
    b.sel:SetTexture("Interface\\Buttons\\CheckButtonHilight"); b.sel:SetBlendMode("ADD")
    b.away = b:CreateTexture(nil, "OVERLAY", nil, 2); b.away:SetSize(14, 14); b.away:SetPoint("BOTTOMRIGHT", 3, -3)
    b.away:SetTexture(TCF.Icon("INV_Misc_Map_01"))
    b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    b:SetScript("OnClick", function() TCF:SetClass(cl.key); TCF:PlaySound("click") end)
    Tip(b, function(tt)
      local cd = TCF:CD(cl.key)
      local cs = TCF:CombatStats(cl.key)
      tt:AddLine(cl.name, cl.color[1], cl.color[2], cl.color[3])
      tt:AddLine(string.format("Level %d %s", cd.level, TCF:GetTitle(cd.level)), 1, 1, 1)
      tt:AddLine(string.format("Power %d  (DPS %d, Health %d, item level %d)", cs.power, cs.dps, cs.hp, cs.ilvl), 0.8, 0.8, 0.8)
      if TCF:IsOnExpedition(cl.key) then tt:AddLine("Away on an expedition", 1, 0.6, 0.2) end
      tt:AddLine("Each class has its own level, gear, abilities and Adventure progress.", 0.7, 0.7, 0.7, true)
    end)
    classBtns[i] = b
  end

  local lvl = Text(left, "GameFontHighlight", nil, "LEFT"); lvl:SetPoint("TOPLEFT", 12, -362)
  local xp = CreateFrame("StatusBar", nil, left)
  xp:SetSize(292, 14); xp:SetPoint("TOPLEFT", 12, -380)
  xp:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar"); xp:SetStatusBarColor(0.58, 0.0, 0.55)
  local xbg = xp:CreateTexture(nil, "BACKGROUND"); xbg:SetAllPoints(); xbg:SetColorTexture(0, 0, 0, 0.6)
  local xpText = Text(xp, "GameFontHighlightSmall"); xpText:SetPoint("CENTER")
  local statLines = Text(left, "GameFontHighlightSmall", nil, "LEFT")
  statLines:SetPoint("TOPLEFT", 12, -402); statLines:SetWidth(292); statLines:SetSpacing(3)

  ------------------------------------------------ right column: two rows of tabs
  local right = Panel(win, W - 360, H - 126); right:SetPoint("TOPLEFT", left, "TOPRIGHT", 12, -60)
  SelectTab = function(i)
    win.tab = i
    for j, p in ipairs(pages) do p:SetShown(j == i) end
    for j, t in ipairs(tabs) do if j == i then t:LockHighlight() else t:UnlockHighlight() end end
    win:Refresh()
  end
  for i, n in ipairs(tabNames) do
    local b = Button(win, n, 104, 24, function() SelectTab(i); TCF:PlaySound("click") end)
    local col, row = (i - 1) % 5, i <= 5 and 1 or 0
    b:SetPoint("BOTTOMLEFT", right, "TOPLEFT", col * 107, 4 + row * 27)
    tabs[i] = b
    local p = CreateFrame("Frame", nil, right); p:SetAllPoints(); p:Hide()
    pages[i] = p
  end
  -- pages built by UI_*.lua files
  for i, key in pairs(builderKeys) do
    local build = TCF.UI.Builders[key]
    if build then pageRefresh[i] = build(pages[i], win) end
  end

  ------------------------------------------------ Appearance (cosmetics you've collected)
  local wd = pages[TAB_WARDROBE]
  win.slot = "head"
  local slotBtns = {}
  for i, s in ipairs(TCF.SLOTS) do
    local b = CreateFrame("Button", nil, wd)
    b:SetSize(34, 34); b:SetPoint("TOPLEFT", 12 + (i - 1) * 38, -12)
    local t = b:CreateTexture(nil, "ARTWORK"); t:SetAllPoints(); t:SetTexture(TCF.Icon(s.icon))
    t:SetTexCoord(0.07, 0.93, 0.07, 0.93)
    b.sel = b:CreateTexture(nil, "OVERLAY"); b.sel:SetAllPoints()
    b.sel:SetTexture("Interface\\Buttons\\CheckButtonHilight"); b.sel:SetBlendMode("ADD")
    b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    b:SetScript("OnClick", function() win.slot = s.key; win.page = 1; win:RefreshWardrobe(); TCF:PlaySound("click") end)
    Tip(b, function(tt)
      tt:AddLine(s.name, 1, 0.82, 0)
      tt:AddLine(s.look and "Shared by every class." or "Saved separately for each class. Shows over your real gear.", 0.8, 0.8, 0.8, true)
    end)
    b.key = s.key
    slotBtns[i] = b
  end
  local slotTitle = Text(wd, "GameFontNormal", nil, "LEFT"); slotTitle:SetPoint("TOPLEFT", 14, -54)

  local COLS, ROWS, CELL, GAP = 8, 6, 54, 5
  local cells = {}
  local grid = CreateFrame("Frame", nil, wd)
  grid:SetSize(COLS * (CELL + GAP), ROWS * (CELL + GAP)); grid:SetPoint("TOP", 0, -76)
  for i = 1, COLS * ROWS do
    local c = ItemCell(grid, CELL)
    c:SetPoint("TOPLEFT", ((i - 1) % COLS) * (CELL + GAP), -floor((i - 1) / COLS) * (CELL + GAP))
    c:RegisterForClicks("LeftButtonUp", "RightButtonUp")
    c:SetScript("OnClick", function(s)
      local it = s.item
      if it and it.slot == "skin" and not TCF.db.owned[it.id] then
        if not it.skinPrice then
          local how = TCF.HowToGet and TCF:HowToGet(it) or {}
          local line = how[1] or "see its tooltip for how to get it"
          if not line:find("[%.!?%)]$") then line = line .. "." end
          TCF:Print(it.name .. ": " .. line, true)
          return
        end
        if TCF.db.coins < it.skinPrice then TCF:Print("You need " .. TCF.Commas(it.skinPrice) .. " TapCoins for " .. it.name .. ".", true) return end
        if StaticPopup_Show then
          StaticPopupDialogs.TAPCATFOREVER_BUY_SKIN = StaticPopupDialogs.TAPCATFOREVER_BUY_SKIN or {
            text = "Buy the %s skin for %s TapCoins?", button1 = YES or "Yes", button2 = NO or "No",
            OnAccept = function(_, data) TCF:BuySkin(data) end, timeout = 0, whileDead = true, hideOnEscape = true,
          }
          local dlg = StaticPopup_Show("TAPCATFOREVER_BUY_SKIN", it.name, TCF.Commas(it.skinPrice))
          if dlg then dlg.data = it.id end
        else
          TCF:BuySkin(it.id)
        end
        return
      end
      if not it or not TCF.db.owned[it.id] then return end
      if TCF:IsEquipped(it) then TCF:Unequip(it.slot) else TCF:Equip(it) end
      TCF:PlaySound("click")
    end)
    c:SetScript("OnEnter", function(s)
      GameTooltip:SetOwner(s, "ANCHOR_RIGHT"); TCF:ItemTooltip(GameTooltip, s.item)
      if TCF.db.owned[s.item.id] then
        GameTooltip:AddLine(TCF:IsEquipped(s.item) and "Click to unequip" or "Click to equip", 0, 1, 0)
      end
      GameTooltip:Show()
      win.preview:ApplyAppearance(TCF:GetAppearance(nil, s.item))
    end)
    c:SetScript("OnLeave", function() GameTooltip:Hide(); win.preview:ApplyAppearance(TCF:GetAppearance()) end)
    cells[i] = c
  end
  local pageText = Text(wd, "GameFontHighlightSmall"); pageText:SetPoint("BOTTOM", 0, 16)
  local prev = Button(wd, "<", 28, 22, function() win.page = max(1, (win.page or 1) - 1); win:RefreshWardrobe() end)
  prev:SetPoint("RIGHT", pageText, "LEFT", -10, 0)
  local nextB = Button(wd, ">", 28, 22, function() win.page = (win.page or 1) + 1; win:RefreshWardrobe() end)
  nextB:SetPoint("LEFT", pageText, "RIGHT", 10, 0)
  local unequip = Button(wd, "Show real gear", 120, 22, function() TCF:Unequip(win.slot) end)
  unequip:SetPoint("BOTTOMLEFT", 12, 12)
  local collected = Text(wd, "GameFontDisableSmall", nil, "RIGHT"); collected:SetPoint("BOTTOMRIGHT", -14, 18)
  -- shown in the middle of the empty grid (not in the page line, where it would push the arrows onto the buttons)
  local emptyText = Text(wd, "GameFontHighlight", "|cff888888Nothing collected for this slot yet.\nOpen chests, craft, or visit the Shop.|r")
  emptyText:SetPoint("CENTER", 0, 0); emptyText:SetWidth(420)
  wd:EnableMouseWheel(true)
  wd:SetScript("OnMouseWheel", function(_, d) win.page = max(1, (win.page or 1) - d); win:RefreshWardrobe() end)

  function win:WardrobeItems()
    local list = {}
    local class = TCF.db.class
    for _, it in ipairs(TCF.ITEM_LIST) do
      if it.slot == self.slot and (not it.class or it.class == class) and (TCF.db.owned[it.id] or it.slot == "skin") then
        list[#list + 1] = it
      end
    end
    table.sort(list, function(a, b)
      local ao, bo = TCF.db.owned[a.id] and 1 or 0, TCF.db.owned[b.id] and 1 or 0
      if ao ~= bo then return ao > bo end
      if (a.class and 1 or 0) ~= (b.class and 1 or 0) then return a.class ~= nil end
      if a.art ~= b.art then return a.art < b.art end
      if a.rarity ~= b.rarity then return a.rarity < b.rarity end
      return a.name < b.name
    end)
    return list
  end

  function win:RefreshWardrobe()
    for _, b in ipairs(slotBtns) do b.sel:SetShown(b.key == self.slot) end
    local s = TCF.SLOT_BY_KEY[self.slot]
    local cl = TCF.CLASS_BY_KEY[TCF.db.class]
    slotTitle:SetText(s.name .. (s.look and "  |cff888888(all classes)|r" or ("  |cff888888(" .. cl.name .. ")|r")))
    local list = self:WardrobeItems()
    local per = COLS * ROWS
    local pagesN = max(1, math.ceil(#list / per))
    self.page = min(max(1, self.page or 1), pagesN)
    local owned = 0
    for _, it in ipairs(list) do if TCF.db.owned[it.id] then owned = owned + 1 end end
    for i = 1, per do
      local it = list[(self.page - 1) * per + i]
      if it then
        cells[i]:SetItem(it, TCF.db.owned[it.id], TCF:IsEquipped(it))
        if it.slot == "skin" and not TCF.db.owned[it.id] then
          cells[i].count:SetText(it.skinPrice and ("|cffffd100" .. TCF.Commas(it.skinPrice) .. "|r") or ("|cffff8000" .. TCF.SkinSourceTag(it) .. "|r"))
          cells[i].pic:SetAlpha(0.7)
        end
      else cells[i]:Hide() end
    end
    pageText:SetText(string.format("Page %d / %d", self.page, pagesN))
    prev:SetEnabled(self.page > 1); nextB:SetEnabled(self.page < pagesN)
    unequip:SetEnabled(self.slot ~= "fur")
    unequip:SetText(self.slot == "skin" and "Remove skin" or "Show real gear")
    collected:SetText(string.format("%d collected", owned))
    local empty = #list == 0
    emptyText:SetShown(empty)
    pageText:SetShown(not empty); prev:SetShown(not empty); nextB:SetShown(not empty)
  end

  ------------------------------------------------ Quests
  local qp = pages[TAB_QUESTS]
  local qHeader = Text(qp, "GameFontNormalLarge", "Daily Quests", "LEFT"); qHeader:SetPoint("TOPLEFT", 16, -14)
  local qReset = Text(qp, "GameFontDisableSmall", nil, "LEFT"); qReset:SetPoint("LEFT", qHeader, "RIGHT", 10, -1)
  local wHeader = Text(qp, "GameFontNormalLarge", "Weekly Quest", "LEFT"); wHeader:SetPoint("TOPLEFT", 16, -262)
  local wReset = Text(qp, "GameFontDisableSmall", nil, "LEFT"); wReset:SetPoint("LEFT", wHeader, "RIGHT", 10, -1)
  local qRows = {}
  local function QuestRow(y)
    local r = Panel(qp, 508, 64, 0.85); r:SetPoint("TOP", 0, y)
    r.icon = r:CreateTexture(nil, "ARTWORK"); r.icon:SetSize(40, 40); r.icon:SetPoint("LEFT", 10, 0)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("TOPLEFT", r.icon, "TOPRIGHT", 10, -2)
    r.desc = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.desc:SetPoint("TOPLEFT", r.name, "BOTTOMLEFT", 0, -3)
    r.bar = CreateFrame("StatusBar", nil, r); r.bar:SetSize(200, 12); r.bar:SetPoint("BOTTOMLEFT", r.icon, "BOTTOMRIGHT", 10, 0)
    r.bar:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar"); r.bar:SetStatusBarColor(0.15, 0.45, 0.9)
    local bg = r.bar:CreateTexture(nil, "BACKGROUND"); bg:SetAllPoints(); bg:SetColorTexture(0, 0, 0, 0.6)
    r.barText = Text(r.bar, "GameFontHighlightSmall"); r.barText:SetPoint("CENTER")
    r.reward = Text(r, "GameFontHighlight", nil, "RIGHT"); r.reward:SetPoint("TOPRIGHT", -12, -12)
    r.claim = Button(r, "Claim", 80, 22, function() if r.quest then TCF:ClaimQuest(r.quest) end end)
    r.claim:SetPoint("BOTTOMRIGHT", -10, 8)
    qRows[#qRows + 1] = r
    return r
  end
  for i = 1, 3 do QuestRow(-40 - (i - 1) * 70) end
  QuestRow(-288)
  local qHelp = Text(qp, "GameFontDisableSmall", nil, "LEFT"); qHelp:SetPoint("BOTTOMLEFT", 16, 12); qHelp:SetWidth(500)
  qHelp:SetText("Quests are your main source of TapCoins. Three daily quests (each with a free Cat Treat Pouch) appear every day, and a bigger weekly quest (with a free Adventurer's Strongbox) every Tuesday. Open free chests from the Treasure Bag (the Bag button in the Shop or at the top of this window).")

  function win:RefreshQuests()
    TCF:EnsureQuests()
    local q = TCF.db.quests
    local secs = TCF:SecondsUntilReset()
    qReset:SetText(string.format("new quests in %dh %dm", floor(secs / 3600), floor(secs % 3600 / 60)))
    wReset:SetText("resets on Tuesday")
    local list = { q.daily[1], q.daily[2], q.daily[3], q.weekly[1] }
    for i, r in ipairs(qRows) do
      local quest = list[i]
      r.quest = quest
      if quest then
        r:Show()
        local prog = TCF:QuestProgress(quest)
        local done = prog >= quest.goal
        r.icon:SetTexture(TCF.Icon(quest.icon)); r.icon:SetDesaturated(quest.claimed)
        r.name:SetText(quest.claimed and ("|cff888888" .. quest.name .. "|r") or quest.name)
        r.desc:SetText(quest.desc)
        r.bar:SetMinMaxValues(0, quest.goal); r.bar:SetValue(prog)
        r.bar:SetStatusBarColor(done and 0.2 or 0.15, done and 0.8 or 0.45, done and 0.2 or 0.9)
        r.barText:SetText(quest.claimed and "Claimed" or (TCF.Commas(prog) .. " / " .. TCF.Commas(quest.goal)))
        local ch = quest.key and TCF.CHEST_BY_KEY[quest.key]
        r.reward:SetText(coinStr(quest.reward, 13) .. (ch and ("  |T" .. TCF.Icon(ch.icon) .. ":14:14|t") or ""))
        r.claim:SetEnabled(done and not quest.claimed)
        r.claim:SetText(quest.claimed and "Done" or "Claim")
      else
        r:Hide()
      end
    end
  end

  ------------------------------------------------ Shop
  local sh = pages[TAB_SHOP]
  local shopTitle = Text(sh, "GameFontNormalLarge", "Daily Wares"); shopTitle:SetPoint("TOPLEFT", 16, -14)
  local resetText = Text(sh, "GameFontDisableSmall", nil, "LEFT"); resetText:SetPoint("LEFT", shopTitle, "RIGHT", 10, -1)
  local reroll = Button(sh, "New Stock", 150, 22, function()
    if TCF:RerollShop() then TCF:PlaySound("buy") end
  end)
  reroll:SetPoint("TOPRIGHT", -14, -12)
  Tip(reroll, function(tt)
    tt:AddLine("Refresh the daily wares", 1, 0.82, 0)
    tt:AddLine("The price doubles with each refresh, and resets at midnight.", 1, 1, 1, true)
  end)
  local cards = {}
  for i = 1, 3 do
    local c = Panel(sh, 160, 112, 0.9)
    c:SetPoint("TOPLEFT", 14 + (i - 1) * 166, -42)
    c.cell = ItemCell(c, 56); c.cell:SetPoint("TOPLEFT", 8, -8)
    c.cell:SetScript("OnEnter", function(s)
      GameTooltip:SetOwner(s, "ANCHOR_RIGHT"); TCF:ItemTooltip(GameTooltip, s.item); GameTooltip:Show()
      if TCF:CanEquip(s.item) then win.preview:ApplyAppearance(TCF:GetAppearance(nil, s.item)) end
    end)
    c.cell:SetScript("OnLeave", function() GameTooltip:Hide(); win.preview:ApplyAppearance(TCF:GetAppearance()) end)
    c.name = Text(c, "GameFontNormalSmall", nil, "LEFT"); c.name:SetPoint("TOPLEFT", c.cell, "TOPRIGHT", 6, 0)
    c.name:SetWidth(84); c.name:SetHeight(42); c.name:SetJustifyV("TOP")
    c.cls = Text(c, "GameFontDisableSmall", nil, "LEFT"); c.cls:SetPoint("BOTTOMLEFT", c.cell, "BOTTOMRIGHT", 6, 2)
    c.price = Text(c, "GameFontHighlight", nil, "LEFT"); c.price:SetPoint("BOTTOMLEFT", 10, 12)
    c.buy = Button(c, "Buy", 60, 20, function() if c.id then TCF:BuyItem(c.id) end end)
    c.buy:SetPoint("BOTTOMRIGHT", -8, 8)
    cards[i] = c
  end
  local chestTitle = Text(sh, "GameFontNormalLarge", "Treasure Chests"); chestTitle:SetPoint("TOPLEFT", 16, -176)
  local chestCards = {}
  for i, ch in ipairs(TCF.CHESTS) do
    local c = Panel(sh, 160, 118, 0.9)
    c:SetPoint("TOPLEFT", 14 + (i - 1) * 166, -200)
    local ic = c:CreateTexture(nil, "ARTWORK"); ic:SetSize(40, 40); ic:SetPoint("TOPLEFT", 10, -10)
    ic:SetTexture(TCF.Icon(ch.icon))
    local n = Text(c, "GameFontNormalSmall", ch.name, "LEFT"); n:SetPoint("TOPLEFT", ic, "TOPRIGHT", 6, 0); n:SetWidth(96)
    local d = Text(c, "GameFontDisableSmall", ch.desc, "LEFT"); d:SetPoint("TOPLEFT", 10, -54); d:SetWidth(140)
    c.open = Button(c, coinStr(ch.cost, 12), 72, 20, function() TCF:OpenChest(ch.key) end)
    c.open:SetPoint("BOTTOMLEFT", 8, 8)
    c.key = Button(c, "Bag", 66, 20, function() TCF:ToggleBag() end)
    c.key:SetPoint("BOTTOMRIGHT", -8, 8)
    Tip(c.key, function(tt)
      tt:AddLine("Your unopened chests (Treasure Bag)", 1, 0.82, 0)
      tt:AddLine("Cat Treat Pouch: each daily quest.", 1, 1, 1, true)
      tt:AddLine("Adventurer's Strongbox: weekly quest, finishing a dungeon, every 5 class levels.", 1, 1, 1, true)
      tt:AddLine("Heroic Cache: finishing a raid, every 20 class levels.", 1, 1, 1, true)
    end)
    Tip(c, function(tt)
      tt:AddLine(ch.name, 1, 0.82, 0)
      local names = {}
      for r = 1, 5 do
        if ch.weights[r] > 0 then
          local col = TCF.RARITY[r]
          tt:AddDoubleLine("|c" .. col.hex .. col.name .. "|r", ch.weights[r] .. "%", 1, 1, 1, 1, 1, 1)
        end
      end
      tt:AddLine("Duplicates are salvaged into TapCoins.", 0.7, 0.7, 0.7, true)
    end)
    c.chest = ch
    chestCards[i] = c
  end
  local gearPct = floor((TCF.CHEST_GEAR_CHANCE or 0.9) * 100 + 0.5)  -- same odds as TCF:OpenChest
  local dungeonText = Text(sh, "GameFontHighlightSmall", nil, "LEFT"); dungeonText:SetPoint("TOPLEFT", 16, -326); dungeonText:SetWidth(520)
  -- kept to about five lines so it clears the heritage panel below
  dungeonText:SetText("|cffffd100Free chests:|r " .. TCF.DUNGEON_CHEST_TEXT .. " Quests, levels, zone clears and expeditions give chests too. Chests hold gear (" .. gearPct .. "%) or a cosmetic (" .. (100 - gearPct) .. "%).")
  -- racial heritage offer for the current character's race
  local her = Panel(sh, 528, 58, 0.9); her:SetPoint("TOPLEFT", 14, -384)
  her.cell = ItemCell(her, 46); her.cell:SetPoint("LEFT", 6, 0)
  her.cell:SetScript("OnEnter", function(s)
    if not s.item then return end
    GameTooltip:SetOwner(s, "ANCHOR_RIGHT"); TCF:ItemTooltip(GameTooltip, s.item); GameTooltip:Show()
    win.preview:ApplyAppearance(TCF:GetAppearance(nil, s.item))
  end)
  her.cell:SetScript("OnLeave", function() GameTooltip:Hide(); win.preview:ApplyAppearance(TCF:GetAppearance()) end)
  her.title = Text(her, "GameFontNormal", nil, "LEFT"); her.title:SetPoint("TOPLEFT", her.cell, "TOPRIGHT", 8, -4)
  her.desc = Text(her, "GameFontHighlightSmall", nil, "LEFT"); her.desc:SetPoint("BOTTOMLEFT", her.cell, "BOTTOMRIGHT", 8, 4); her.desc:SetWidth(330)
  her.buy = Button(her, "Buy", 100, 22, function() TCF:BuyRaceAccessory() end); her.buy:SetPoint("RIGHT", -8, 0)
  local lastLoot = Text(sh, "GameFontHighlight", nil, "LEFT"); lastLoot:SetPoint("BOTTOMLEFT", 16, 14); lastLoot:SetWidth(480)

  function win:RefreshShop()
    TCF:BuildShop()
    local secs = TCF:SecondsUntilReset()
    resetText:SetText(string.format("new wares in %dh %dm", floor(secs / 3600), floor(secs % 3600 / 60)))
    reroll:SetText("New Stock " .. coinStr(TCF:RerollCost(), 12))
    reroll:SetEnabled(TCF.db.coins >= TCF:RerollCost())
    local stock = TCF.db.shop.stock
    for i, c in ipairs(cards) do
      local id = stock[i]
      local it = id and TCF.ITEMS[id]
      if it then
        c:Show(); c.id = id
        local owned = TCF.db.owned[id]
        c.cell:SetItem(it, true, false)
        local col = TCF.RARITY[it.rarity]
        c.name:SetText("|c" .. col.hex .. it.name .. "|r")
        local cl = it.class and TCF.CLASS_BY_KEY[it.class]
        c.cls:SetText(cl and cl.name or "Any class")
        c.price:SetText(owned and "|cff20ff20Owned|r" or coinStr(it.price, 13))
        c.buy:SetEnabled(not owned and TCF.db.coins >= it.price)
      else
        c:Hide()
      end
    end
    for _, c in ipairs(chestCards) do
      c.open:SetEnabled(TCF.db.coins >= c.chest.cost)
      local k = TCF.db.keys[c.chest.key] or 0
      c.key:SetText("Bag (" .. k .. ")"); c.key:SetEnabled(k > 0)
    end
    local rit, raceName = TCF:RaceItemForPlayer()
    if rit then
      her:Show()
      her.cell:SetItem(rit, true, false)
      her.title:SetText("Racial Heritage: |c" .. TCF.RARITY[rit.rarity].hex .. rit.name .. "|r")
      local owned = TCF.db.owned[rit.id]
      her.desc:SetText(owned and "Owned. Hide or show it with \"Show racial accessory\" in Settings."
        or ("Show your " .. (raceName or "") .. " pride on this character's cats."))
      her.buy:SetText(owned and "Owned" or coinStr(TCF.RACE_PRICE, 12))
      her.buy:SetEnabled(not owned and TCF.db.coins >= TCF.RACE_PRICE)
    else her:Hide() end
    local lc = TCF.lastChest
    if lc and lc.gear then
      lastLoot:SetText("Last chest: " .. TCF.GearLink(lc.gear) .. (lc.isNew and " |cff20ff20NEW!|r" or ""))
    elseif lc and lc.item then
      lastLoot:SetText("Last chest: " .. TCF.ItemLink(lc.item) .. (lc.isNew and " |cff20ff20NEW!|r" or
        string.format(" |cffaaaaaa(duplicate, +%d TapCoins)|r", lc.salvage)))
    else
      lastLoot:SetText("|cff888888Earn TapCoins from quests, Adventure bosses, level-ups and daily logins.|r")
    end
  end

  ------------------------------------------------ Achievements
  local ac = pages[TAB_ACH]
  local acHeader = Text(ac, "GameFontNormalLarge"); acHeader:SetPoint("TOPLEFT", 16, -14)
  local ROWS_A = 8
  local rows = {}
  for i = 1, ROWS_A do
    local r = Panel(ac, 488, 46, 0.85)
    r:SetPoint("TOPLEFT", 12, -40 - (i - 1) * 49)
    r.icon = r:CreateTexture(nil, "ARTWORK"); r.icon:SetSize(34, 34); r.icon:SetPoint("LEFT", 6, 0)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("TOPLEFT", r.icon, "TOPRIGHT", 8, -1)
    r.desc = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.desc:SetPoint("BOTTOMLEFT", r.icon, "BOTTOMRIGHT", 8, 2)
    r.bar = CreateFrame("StatusBar", nil, r); r.bar:SetSize(150, 12); r.bar:SetPoint("TOPRIGHT", -10, -8)
    r.bar:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar")
    local bg = r.bar:CreateTexture(nil, "BACKGROUND"); bg:SetAllPoints(); bg:SetColorTexture(0, 0, 0, 0.6)
    r.barText = Text(r.bar, "GameFontHighlightSmall"); r.barText:SetPoint("CENTER")
    r.reward = Text(r, "GameFontHighlightSmall", nil, "RIGHT"); r.reward:SetPoint("BOTTOMRIGHT", -10, 6)
    r:SetScript("OnLeave", function() GameTooltip:Hide() end)
    rows[i] = r
  end
  local acPage = Text(ac, "GameFontHighlightSmall"); acPage:SetPoint("BOTTOM", 0, 12)
  ac:EnableMouseWheel(true)
  ac:SetScript("OnMouseWheel", function(_, d) win.acScroll = max(0, (win.acScroll or 0) - d); win:RefreshAchievements() end)

  function win:RefreshAchievements()
    local list, done = {}, 0
    for _, a in ipairs(TCF.ACHIEVEMENTS) do
      list[#list + 1] = a
      if TCF.db.achievements[a.id] then done = done + 1 end
    end
    acHeader:SetText(string.format("Achievements  |cffffffff%d / %d|r", done, #list))
    local maxScroll = max(0, #list - ROWS_A)
    self.acScroll = min(self.acScroll or 0, maxScroll)
    for i, r in ipairs(rows) do
      local a = list[i + self.acScroll]
      if a then
        r:Show()
        local got = TCF.db.achievements[a.id]
        local cur = min(TCF:GetStat(a.stat), a.goal)
        r.icon:SetTexture(TCF.Icon(a.icon)); r.icon:SetDesaturated(not got)
        r.name:SetText(got and ("|cffffd100" .. a.name .. "|r") or ("|cffaaaaaa" .. a.name .. "|r"))
        r.desc:SetText(a.desc)
        r.bar:SetMinMaxValues(0, a.goal); r.bar:SetValue(cur)
        r.bar:SetStatusBarColor(got and 0.2 or 0.15, got and 0.8 or 0.45, got and 0.2 or 0.9)
        r.barText:SetText(got and "Complete" or (TCF.Commas(cur) .. " / " .. TCF.Commas(a.goal)))
        local rw = coinStr(a.coins, 12)
        local rid = a.item or a.skin
        if rid and TCF.ITEMS[rid] then rw = rw .. " + " .. TCF.ItemLink(TCF.ITEMS[rid]) end
        r.reward:SetText(rw)
        if r.SetBackdropBorderColor then
          if got then r:SetBackdropBorderColor(1, 0.82, 0.2, 1) else r:SetBackdropBorderColor(0.45, 0.40, 0.55, 1) end
        end
        r:SetScript("OnEnter", function(s)
          local rit = TCF.ITEMS[a.item or a.skin or ""]
          if not rit then return end
          GameTooltip:SetOwner(s, "ANCHOR_RIGHT"); TCF:ItemTooltip(GameTooltip, rit); GameTooltip:Show()
        end)
      else
        r:Hide()
      end
    end
    acPage:SetText(maxScroll > 0 and "Scroll for more" or "")
  end

  ------------------------------------------------ Settings
  local st = pages[TAB_SETTINGS]
  local ui = TCF.db.ui
  local stTitle = Text(st, "GameFontNormalLarge", "Settings"); stTitle:SetPoint("TOPLEFT", 16, -14)
  -- party cats (Party.lua): a short note beside the title, with the bonus you have right now
  local partyNote = Text(st, "GameFontHighlightSmall", nil, "LEFT")
  partyNote:SetPoint("TOPLEFT", 120, -12); partyNote:SetWidth(420)
  local checks = {}
  local function Check(label, key, col, row, tip, after)
    local cb = CreateFrame("CheckButton", nil, st, "UICheckButtonTemplate")
    cb:SetSize(26, 26); cb:SetPoint("TOPLEFT", 14 + col * 250, -44 - row * 30)
    local t = Text(cb, "GameFontHighlight", label, "LEFT"); t:SetPoint("LEFT", cb, "RIGHT", 2, 1)
    cb:SetScript("OnClick", function(s)
      ui[key] = s:GetChecked() and true or false
      TCF.hud:ApplySettings()
      if after then after() end
      TCF:PlaySound("click")
    end)
    if tip then Tip(cb, function(tt) tt:AddLine(label, 1, 0.82, 0); tt:AddLine(tip, 1, 1, 1, true) end) end
    cb.key = key
    checks[#checks + 1] = cb
  end
  Check("Show cat", "shown", 0, 0, "Show or hide the cat on your screen.")
  Check("Lock position", "locked", 0, 1, "Stop the cat being dragged.")
  Check("Click-through when locked", "clickThrough", 0, 2, "When locked, mouse clicks pass straight through the cat.")
  Check("Cat only (hide all text)", "catOnly", 0, 3, "Hide the level, XP bar and counters.")
  Check("Count mouse clicks", "mouse", 0, 4, "Mouse clicks also make the cat tap and earn progress.")
  Check("Show level", "showLevel", 1, 0)
  Check("Show XP bar", "showXP", 1, 1)
  Check("Show tap counter", "showTaps", 1, 2)
  Check("Show TapCoins", "showCoins", 1, 3)
  Check("Popups on cat", "popups", 1, 4, "Floating text for level ups, loot and achievements.")
  Check("Sounds", "sound", 0, 5)
  Check("Show racial accessory", "racial", 0, 6, "Show your race's accessory (tusks, horns, ears...). You keep it either way.", function() TCF:RefreshAll() end)
  Check("Chat messages", "chat", 1, 5)
  Check("Chest opening animation", "chestAnim", 1, 7, "Opening a chest spins a reel of possible loot before it lands on your reward.")
  Check("Text above the cat", "textAbove", 0, 7, "Put the level, XP bar and counters above the cat instead of below. (\"Cat only\" hides them.)")

  local function Slider(label, minV, maxV, step, y, get, set, fmt)
    local s = CreateFrame("Slider", nil, st, BT)
    s:SetOrientation("HORIZONTAL"); s:SetSize(220, 16); s:SetPoint("TOPLEFT", 22, y)
    if s.SetBackdrop then
      s:SetBackdrop({ bgFile = "Interface\\Buttons\\UI-SliderBar-Background", edgeFile = "Interface\\Buttons\\UI-SliderBar-Border",
        tile = true, tileSize = 8, edgeSize = 8, insets = { left = 3, right = 3, top = 6, bottom = 6 } })
    end
    s:SetThumbTexture("Interface\\Buttons\\UI-SliderBar-Button-Horizontal")
    s:SetMinMaxValues(minV, maxV); s:SetValueStep(step)
    if s.SetObeyStepOnDrag then s:SetObeyStepOnDrag(true) end
    local t = Text(s, "GameFontHighlight", nil, "LEFT"); t:SetPoint("BOTTOMLEFT", s, "TOPLEFT", 0, 3)
    s:SetScript("OnValueChanged", function(_, v)
      v = floor(v / step + 0.5) * step
      set(v); t:SetText(string.format(fmt, label, v)); TCF.hud:ApplySettings()
    end)
    s.Sync = function() s:SetValue(get()); t:SetText(string.format(fmt, label, get())) end
    return s
  end
  local scaleS = Slider("Cat size", 0.3, 3, 0.05, -300, function() return ui.scale end, function(v) ui.scale = v end, "%s: %.2fx")
  local alphaS = Slider("Opacity", 0.1, 1, 0.05, -348, function() return ui.alpha end, function(v) ui.alpha = v end, "%s: %.2f")
  local textS = Slider("Text size", 0.5, 2.5, 0.05, -396, function() return ui.textScale or 1 end, function(v) ui.textScale = v end, "%s: %.2fx")
  local resetB = Button(st, "Reset position", 130, 22, function() TCF.hud:ResetPosition() end)
  resetB:SetPoint("TOPLEFT", 280, -296)
  local mmB = Button(st, "Toggle minimap icon", 160, 22, function()
    ui.minimap.hide = not ui.minimap.hide; TCF:UpdateMinimapButton()
  end)
  mmB:SetPoint("TOPLEFT", 280, -328)
  local welB = Button(st, "Welcome tour", 130, 22, function() TCF:ShowWelcome() end)
  welB:SetPoint("TOPLEFT", 280, -352)
  local pnB = Button(st, "Patch notes", 110, 22, function() TCF:ShowPatchNotes() end)
  pnB:SetPoint("LEFT", mmB, "RIGHT", 8, 0)
  Tip(pnB, function(tt)
    tt:AddLine("Patch notes", 1, 0.82, 0)
    tt:AddLine("What changed in every version of TapCatForever. Also /tcf news.", 1, 1, 1, true)
  end)
  local fbB = Button(st, "Send feedback", 130, 22, function() TCF:ShowFeedback() end)
  fbB:SetPoint("LEFT", welB, "RIGHT", 8, 0)
  Tip(fbB, function(tt)
    tt:AddLine("Send feedback", 1, 0.82, 0)
    tt:AddLine("Report a bug or suggest an idea. Shows links you can copy into your browser.", 1, 1, 1, true)
  end)
  local function ConfirmReset(which, text)
    StaticPopupDialogs.TAPCATFOREVER_RESET = {
      text = text, button1 = "Reset", button2 = CANCEL or "Cancel",
      OnAccept = function() TCF:ResetProgress(which) end,
      timeout = 0, whileDead = true, hideOnEscape = true, showAlert = true, preferredIndex = 3,
    }
    StaticPopup_Show("TAPCATFOREVER_RESET")
  end
  local resetCharB = Button(st, "Reset this character", 160, 22, function()
    ConfirmReset("char", "Reset TapCatForever progress for THIS character?\n\nGear, cosmetics, professions, cat levels, abilities and adventures go back to the start. TapCoins, quests and achievements are kept.\n\nYour UI will reload.")
  end)
  resetCharB:SetPoint("TOPLEFT", 280, -376)
  local resetAllB = Button(st, "|cffff5555Reset ALL progress|r", 160, 22, function()
    ConfirmReset("all", "Reset ALL TapCatForever progress on EVERY character?\n\nEverything goes back to level 1: TapCoins, gear, cosmetics, professions, renown, quests and achievements. Your settings are kept.\n\nThis cannot be undone. Your UI will reload.")
  end)
  resetAllB:SetPoint("TOPLEFT", 280, -404)
  local help = Text(st, "GameFontDisableSmall", nil, "LEFT"); help:SetPoint("BOTTOMLEFT", 16, 14); help:SetWidth(490)
  help:SetText("Ctrl + mouse wheel over the cat resizes it, Shift + wheel changes opacity.\n" ..
    "Slash commands: /tapcat (or /tcf) show | hide | lock | unlock | reset | scale <n> | stats | compendium | news | feedback\n" ..
    "TapCoins, quests and achievements are shared; gear, cosmetics, professions and cat levels are per character.")

  -- test mode shortcuts (/tcf testmode)
  local testBox = CreateFrame("Frame", nil, st)
  testBox:SetSize(512, 72); testBox:SetPoint("TOPLEFT", 16, -418)  -- takes the help text's spot
  local tt = Text(testBox, "GameFontNormal", "|cffff6060Test mode|r (/tcf testmode to hide)", "LEFT"); tt:SetPoint("TOPLEFT", 0, 0)
  local cheats = { { "+5,000 TapCoins", "coins" }, { "+10M Trade Gold", "gold" }, { "Unlock professions", "renown" },
                   { "+5 of each chest", "chests" }, { "+10 cat levels", "levels" }, { "Skip 1 hour", "hour" },
                   { "Fake party cats", "party" } }
  -- four per row, so the extra buttons stay inside the page
  for i, c in ipairs(cheats) do
    local b = Button(testBox, c[1], 124, 22, function()
      if c[2] == "party" then
        -- 1, 2, 3, 4, 5 (shows "+1"), then none again
        if TCF.PartyTestInject then TCF:PartyTestInject(((TCF:PartyTestCount() or 0) + 1) % 6) end
        win:RefreshSettings()
      else
        TCF:TestCheat(c[2])
      end
    end)
    b:SetPoint("TOPLEFT", ((i - 1) % 4) * 128, -18 - math.floor((i - 1) / 4) * 24)
    if c[2] == "party" then
      Tip(b, function(t)
        t:AddLine("Fake party cats", 1, 0.82, 0)
        t:AddLine("Shows pretend party cats beside your cat, as if friends with TapCatForever were in your group. Each click adds one, up to five, then clears them.", 1, 1, 1, true)
      end)
    end
  end

  function win:RefreshSettings()
    testBox:SetShown(ui.testMode and true or false)
    local note = "Play with friends: each group member who also has TapCatForever makes your taps count 10% more, up to +50%."
    local friends = TCF.PartyCount and TCF:PartyCount() or 0
    if friends > 0 then note = note .. string.format(" |cff66ff66Now: +%d%%.|r", floor((TCF:PartyTapMult() - 1) * 100 + 0.5)) end
    partyNote:SetText(note)
    help:SetShown(not ui.testMode)
    for _, cb in ipairs(checks) do cb:SetChecked(ui[cb.key] and true or false) end
    scaleS.Sync(); alphaS.Sync(); textS.Sync()
  end

  ------------------------------------------------ refresh
  function win:RefreshLight()
    local db = TCF.db
    coins:SetText(coinStr(db.coins, 18))
    local nChests = TCF:ChestCount()
    bagCount:SetText(nChests > 0 and nChests or "")
    bagIcon:SetDesaturated(nChests == 0)
    local cd = TCF:CD()
    lvl:SetText(string.format("Level %d  |cffbbbbbb%s|r", cd.level, TCF:GetTitle()))
    local need = TCF.XPForLevel(cd.level)
    xp:SetMinMaxValues(0, need); xp:SetValue(cd.xp)
    xpText:SetText(TCF.Commas(cd.xp) .. " / " .. TCF.Commas(need))
    local n, total = TCF:CountOwned()
    local cs = TCF:CombatStats()
    local nGear = 0
    for _ in pairs(TCF:Bag()) do nGear = nGear + 1 end
    statLines:SetText(string.format(
      "|cffffd100Power %d|r   DPS |cffffffff%d|r   Health |cffffffff%d|r\nArmor |cffffffff%d|r   Crit |cffffffff%.1f%%|r   Item level |cffffffff%d|r\nGear owned: |cffffffff%d|r   Cosmetics: |cffffffff%d / %d|r\nLifetime taps: |cffffffff%s|r\nTapCoins earned: |cffffffff%s|r\nDaily streak: |cffffffff%d|r (best %d)",
      cs.power, cs.dps, cs.hp, cs.armor, cs.crit, cs.ilvl, nGear, n, total,
      TCF.Commas(db.taps), TCF.Commas(db.coinsEarned), db.daily.streak, db.daily.best))
    if self.tab == TAB_SHOP then self:RefreshShop()
    elseif self.tab == TAB_ACH then self:RefreshAchievements()
    elseif self.tab == TAB_QUESTS then self:RefreshQuests()
    elseif pageRefresh[self.tab] then pageRefresh[self.tab](true) end
    local ready = TCF:QuestsReady()
    tabs[TAB_QUESTS]:SetText(ready > 0 and ("Quests |cff20ff20(" .. ready .. ")|r") or "Quests")
  end

  function win:Refresh()
    local cl = TCF.CLASS_BY_KEY[TCF.db.class]
    className:SetText(cl.name)
    className:SetTextColor(cl.color[1], cl.color[2], cl.color[3])
    for i, b in ipairs(classBtns) do b.sel:SetShown(TCF.CLASSES[i].key == TCF.db.class) end
    self.preview:ApplyAppearance(TCF:GetAppearance())
    for _, b in ipairs(dollBtns) do b:Update() end
    for i, b in ipairs(classBtns) do b.away:SetShown(TCF:IsOnExpedition(TCF.CLASSES[i].key) and true or false) end
    if self.tab == TAB_WARDROBE then self:RefreshWardrobe()
    elseif self.tab == TAB_SETTINGS then self:RefreshSettings()
    elseif pageRefresh[self.tab] then pageRefresh[self.tab](false) end
    self:RefreshLight()
  end

  win:SetScript("OnShow", function(s) s:Refresh() end)
  SelectTab(TAB_ADVENTURE)
end

---------------------------------------------------------------- class icons
-- Modern clients (WoW: Forever / Midnight) ship class icons as atlases.
function TCF.SetClassIcon(t, key)
  local atlas = "classicon-" .. key:lower()
  if t.SetAtlas and C_Texture and C_Texture.GetAtlasInfo and C_Texture.GetAtlasInfo(atlas) then
    t:SetAtlas(atlas)
    return
  end
  t:SetTexture("Interface\\TargetingFrame\\UI-Classes-Circles")
  local tc = CLASS_ICON_TCOORDS and CLASS_ICON_TCOORDS[key]
  if tc then t:SetTexCoord(unpack(tc)) end
end

---------------------------------------------------------------- game options panel (Esc > Options > AddOns)
function TCF:RegisterSettingsPanel()
  if self.settingsCategory or not (Settings and Settings.RegisterCanvasLayoutCategory and Settings.RegisterAddOnCategory) then return end
  local panel = CreateFrame("Frame")
  panel:Hide()
  local title = Text(panel, "GameFontNormalHuge", "|cffffb84dTapCat|r|cffffffffForever|r")
  title:SetPoint("TOPLEFT", 16, -16)
  local desc = Text(panel, "GameFontHighlight", nil, "LEFT")
  desc:SetPoint("TOPLEFT", title, "BOTTOMLEFT", 0, -10); desc:SetWidth(560)
  desc:SetText("Your tapping cat companion. The wardrobe, shop, achievements and all settings live in the TapCatForever window.\n\nRight-click the cat, click the minimap button, or type /tapcat to open it.")
  local open = Button(panel, "Open TapCatForever", 180, 26, function()
    if SettingsPanel and SettingsPanel.Close then pcall(SettingsPanel.Close, SettingsPanel, true) end
    if not TCF.window or not TCF.window:IsShown() then TCF:ToggleWindow() end
  end)
  open:SetPoint("TOPLEFT", desc, "BOTTOMLEFT", 0, -16)
  local ok, category = pcall(Settings.RegisterCanvasLayoutCategory, panel, "TapCatForever")
  if ok and category then
    pcall(Settings.RegisterAddOnCategory, category)
    self.settingsCategory = category
  end
end

---------------------------------------------------------------- minimap button
function TCF:CreateMinimapButton()
  if not Minimap then return end
  local b = CreateFrame("Button", "TapCatForeverMinimapButton", Minimap)
  b:SetSize(31, 31); b:SetFrameStrata("MEDIUM"); b:SetFrameLevel(8)
  b:RegisterForClicks("LeftButtonUp", "RightButtonUp"); b:RegisterForDrag("LeftButton")
  local bg = b:CreateTexture(nil, "BACKGROUND"); bg:SetSize(20, 20); bg:SetPoint("CENTER")
  bg:SetTexture("Interface\\Minimap\\UI-Minimap-Background")
  local fur = b:CreateTexture(nil, "ARTWORK", nil, 0); fur:SetSize(20, 20); fur:SetPoint("CENTER", 0, 1)
  fur:SetTexture(ART .. "cat_fur", nil, nil, "NEAREST"); fur:SetTexCoord(0.2, 0.8, 0.1, 0.7)
  local face = b:CreateTexture(nil, "ARTWORK", nil, 1); face:SetAllPoints(fur)
  face:SetTexture(ART .. "face_happy", nil, nil, "NEAREST"); face:SetTexCoord(0.2, 0.8, 0.1, 0.7)
  b.fur = fur
  local border = b:CreateTexture(nil, "OVERLAY"); border:SetSize(53, 53); border:SetPoint("TOPLEFT")
  border:SetTexture("Interface\\Minimap\\MiniMap-TrackingBorder")
  b:SetHighlightTexture("Interface\\Minimap\\UI-Minimap-ZoomButton-Highlight")
  self.minimapButton = b

  local function place()
    local a = math.rad(TCF.db.ui.minimap.angle)
    local r = (Minimap:GetWidth() / 2) + 10
    b:ClearAllPoints(); b:SetPoint("CENTER", Minimap, "CENTER", math.cos(a) * r, math.sin(a) * r)
  end
  b:SetScript("OnDragStart", function(s)
    s:SetScript("OnUpdate", function()
      local mx, my = Minimap:GetCenter()
      local cx, cy = GetCursorPosition()
      local sc = Minimap:GetEffectiveScale()
      TCF.db.ui.minimap.angle = math.deg(math.atan2(cy / sc - my, cx / sc - mx))
      place()
    end)
  end)
  b:SetScript("OnDragStop", function(s) s:SetScript("OnUpdate", nil) end)
  b:SetScript("OnClick", function(_, button)
    if button == "RightButton" then
      TCF.db.ui.shown = not TCF.db.ui.shown; TCF.hud:ApplySettings()
      if TCF.window and TCF.window:IsShown() then TCF.window:RefreshSettings() end
    elseif IsShiftKeyDown and IsShiftKeyDown() and TCF.ToggleCompendium then
      TCF:ToggleCompendium()
    else
      TCF:ToggleWindow()
    end
  end)
  Tip(b, function(tt)
    tt:AddLine("TapCatForever", 1, 0.72, 0.3)
    tt:AddLine(string.format("Level %d  |  %s TapCoins", TCF:CD().level, TCF.Commas(TCF.db.coins)), 1, 1, 1)
    tt:AddLine("Left-click: open window", 0.8, 0.8, 0.8)
    tt:AddLine("Shift-click: Compendium", 0.8, 0.8, 0.8)
    tt:AddLine("Right-click: show / hide cat", 0.8, 0.8, 0.8)
    tt:AddLine("Drag: move this button", 0.8, 0.8, 0.8)
  end)
  place()
  self:UpdateMinimapButton()
end

function TCF:UpdateMinimapButton()
  local b = self.minimapButton
  if not b then return end
  b:SetShown(not self.db.ui.minimap.hide)
  local fur = TCF.ITEMS[self.db.look.fur]
  if fur then b.fur:SetVertexColor(fur.c1[1], fur.c1[2], fur.c1[3]) end
end

---------------------------------------------------------------- loot reveal box
-- Pops up above everything (including the main window) and shows what you got.
local revealQueue = {}

function TCF:CreateLootReveal()
  local f = CreateFrame("Frame", "TapCatForeverLootReveal", UIParent, BT)
  f:SetSize(470, 360); f:SetPoint("CENTER", 0, 60)  -- wide enough for Open another, Equip, OK to all and OK side by side
  f:SetFrameStrata("FULLSCREEN_DIALOG"); f:SetToplevel(true)
  f:EnableMouse(true); f:SetMovable(true); f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving); f:SetScript("OnDragStop", f.StopMovingOrSizing)
  if f.SetBackdrop then f:SetBackdrop(BACKDROP_DIALOG) end
  f:Hide()
  tinsert(UISpecialFrames, "TapCatForeverLootReveal")

  f.title = Text(f, "GameFontNormalLarge"); f.title:SetPoint("TOP", 0, -20)
  local stage = CreateFrame("Frame", nil, f); stage:SetSize(120, 120); stage:SetPoint("TOP", 0, -48)
  f.rays = stage:CreateTexture(nil, "BACKGROUND"); f.rays:SetSize(190, 190); f.rays:SetPoint("CENTER")
  f.rays:SetTexture(ART .. "fx_rays"); f.rays:SetBlendMode("ADD")
  f.box = CreateFrame("Frame", nil, stage, BT); f.box:SetSize(104, 104); f.box:SetPoint("CENTER")
  if f.box.SetBackdrop then f.box:SetBackdrop(BACKDROP_PANEL); f.box:SetBackdropColor(0.04, 0.04, 0.07, 1) end
  f.pic = ItemPicture(f.box, 94); f.pic:SetPoint("CENTER")
  f.gearIcon = f.box:CreateTexture(nil, "ARTWORK"); f.gearIcon:SetPoint("TOPLEFT", 8, -8); f.gearIcon:SetPoint("BOTTOMRIGHT", -8, 8)
  f.gearIcon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
  f.box:EnableMouse(true)
  f.box:SetScript("OnEnter", function(self)
    if not f.item then return end
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    if f.isGear then TCF:GearTooltip(GameTooltip, f.item) else TCF:ItemTooltip(GameTooltip, f.item) end
    GameTooltip:Show()
  end)
  f.box:SetScript("OnLeave", function() GameTooltip:Hide() end)
  f.icon = f:CreateTexture(nil, "ARTWORK"); f.icon:SetSize(22, 22)
  f.name = Text(f, "GameFontNormalLarge"); f.name:SetPoint("TOP", stage, "BOTTOM", 12, -10); f.name:SetWidth(270)
  f.icon:SetPoint("RIGHT", f.name, "LEFT", 0, 0)
  f.kind = Text(f, "GameFontHighlight"); f.kind:SetPoint("TOP", f.name, "BOTTOM", -12, -4)
  f.status = Text(f, "GameFontNormal"); f.status:SetPoint("TOP", f.kind, "BOTTOM", 0, -6); f.status:SetWidth(430)
  f.ok = Button(f, "OK", 80, 24, function() f:Next() end); f.ok:SetPoint("BOTTOMRIGHT", -18, 16)
  -- drops waiting behind this one
  f.queueLabel = Text(f, "GameFontDisableSmall", nil, "LEFT"); f.queueLabel:SetPoint("BOTTOMLEFT", 22, 76)
  f.queueIcons = {}
  for i = 1, 8 do
    local q = CreateFrame("Frame", nil, f, BT); q:SetSize(30, 30); q:SetPoint("BOTTOMLEFT", 20 + (i - 1) * 34, 44)
    if q.SetBackdrop then q:SetBackdrop(BACKDROP_PANEL) end
    q.tex = q:CreateTexture(nil, "ARTWORK"); q.tex:SetPoint("TOPLEFT", 4, -4); q.tex:SetPoint("BOTTOMRIGHT", -4, 4)
    q.tex:SetTexCoord(0.07, 0.93, 0.07, 0.93)
    q:Hide()
    f.queueIcons[i] = q
  end
  f.more = Text(f, "GameFontHighlightSmall", nil, "LEFT"); f.more:SetPoint("LEFT", f.queueIcons[8], "RIGHT", 6, 0)
  f.okAll = Button(f, "OK to all", 90, 24, function() f:Next(true) end)
  f.okAll:SetPoint("RIGHT", f.ok, "LEFT", -6, 0)
  Tip(f.okAll, function(tt) tt:AddLine("OK to all", 1, 0.82, 0); tt:AddLine("Close this and everything waiting behind it. All of it is already in your inventory.", 1, 1, 1, true) end)
  f.equip = Button(f, "Equip", 90, 24, function()
    if f.item then
      if f.isGear then TCF:EquipGear(f.item.id) else TCF:Equip(f.item) end
      TCF:PlaySound("click")
    end
    f:Next()
  end)
  f.equip:SetPoint("RIGHT", f.okAll, "LEFT", -6, 0)
  f.again = Button(f, "Open another", 110, 24, function()
    local key = f.chestKey
    f:Next(true)
    -- the box is hidden for the reel, so tell the pop-up gate this open came from a click here
    if key then TCF.forceReveal = true; TCF:OpenChest(key, true); TCF.forceReveal = nil end
  end)
  f.again:SetPoint("BOTTOMLEFT", 18, 16)
  function f:UpdateQueue()
    local waiting = #revealQueue - 1
    self.okAll:SetShown(waiting > 0)
    self.queueLabel:SetText(waiting > 0 and ("Also found (" .. waiting .. " more):") or "")
    for i, q in ipairs(self.queueIcons) do
      local e = revealQueue[i + 1]
      if e then
        local it, isGear = e[1], e[6]
        q.tex:SetTexture(TCF.Icon(it.icon))
        local col = TCF.RARITY[isGear and it.q or it.rarity].color
        if q.SetBackdropBorderColor then q:SetBackdropBorderColor(col[1], col[2], col[3], 1) end
        q:Show()
      else q:Hide() end
    end
    self.more:SetText(waiting > 8 and ("+" .. (waiting - 8)) or "")
  end

  local t = 0
  f:SetScript("OnUpdate", function(_, e)
    t = t + e
    f.rays:SetRotation(t * 0.6)
    local pop = math.min(1, (f.age or 1) / 0.25)
    f.age = (f.age or 0) + e
    f.box:SetScale(0.6 + 0.4 * pop)
  end)

  function f:Show1(entry)
    local it, isNew, salvage, title, chestKey, isGear = unpack(entry)
    self.item, self.chestKey, self.isGear = it, chestKey, isGear
    if isGear then self:ShowGear(it, isNew, title, chestKey); self:UpdateQueue(); return end
    self.pic:Show(); self.gearIcon:Hide()
    local col = TCF.RARITY[it.rarity].color
    self.title:SetText(title or "Loot!")
    self.rays:SetVertexColor(col[1], col[2], col[3]); self.rays:SetAlpha(it.rarity >= 3 and 0.9 or 0.45)
    if self.box.SetBackdropBorderColor then self.box:SetBackdropBorderColor(col[1], col[2], col[3], 1) end
    self.pic:SetItem(it, false)
    self.icon:SetTexture(TCF.Icon(it.icon))
    self.name:SetText(it.name); self.name:SetTextColor(col[1], col[2], col[3])
    local cl = it.class and TCF.CLASS_BY_KEY[it.class]
    self.kind:SetText("|cffd28cffCOSMETIC|r  " .. TCF.RARITY[it.rarity].name .. " " .. TCF.SLOT_BY_KEY[it.slot].name .. "  |cffaaaaaa" .. (cl and cl.name or "Any class") .. "|r")
    local note = "\n|cffd28cffAppearance only, no stats. Wear it from the Appearance tab.|r"
    if isNew then self.status:SetText("|cff20ff20NEW! Added to your collection|r" .. note)
    else self.status:SetText(string.format("|cffaaaaaaDuplicate: salvaged for|r %s", coinStr(salvage, 14)) .. note) end
    local canEquip = TCF.db.owned[it.id] and TCF:CanEquip(it) and not TCF:IsEquipped(it)
    self.equip:SetShown(canEquip and true or false)
    local left = chestKey and (TCF.db.keys[chestKey] or 0) or 0
    self.again:SetShown(left > 0)
    self.again:SetText("Open another (" .. left .. ")")
    self.age = 0
    self:Show()
    self:UpdateQueue()
    if it.rarity >= 4 then TCF:PlaySound("rare") end
  end

  function f:ShowGear(it, isNew, title, chestKey)
    local col = TCF.RARITY[it.q].color
    self.title:SetText(title or "Loot!")
    self.rays:SetVertexColor(col[1], col[2], col[3]); self.rays:SetAlpha(it.q >= 3 and 0.9 or 0.45)
    if self.box.SetBackdropBorderColor then self.box:SetBackdropBorderColor(col[1], col[2], col[3], 1) end
    self.pic:Hide(); self.gearIcon:Show(); self.gearIcon:SetTexture(TCF.Icon(it.icon))
    self.icon:SetTexture(nil)
    self.name:SetText(it.name); self.name:SetTextColor(col[1], col[2], col[3])
    self.kind:SetText(string.format("|cff40ff40GEAR|r  %s %s %s  |cffffd100Item Level %d|r", TCF.RARITY[it.q].name, TCF.ITEM_TYPE_NAMES[it.sub] or "", TCF.ITEM_SLOT_NAMES[it.slot] or "", it.ilvl))
    local d = TCF.GearUpgrade and TCF:GearUpgrade(it)
    local status = isNew and "|cff20ff20NEW gear!|r" or ("|cffaaaaaaAnother copy (you have " .. (TCF:Bag()[it.id] or 1) .. ")|r")
    if d and d > 0 then status = status .. "  |cff20ff20Upgrade: +" .. d .. " Power|r"
    elseif d and d < 0 then status = status .. "  |cffff4040" .. d .. " Power if worn|r"
    elseif d then status = status .. "  |cffaaaaaaSame Power as what you wear|r" end
    if not TCF:GearUsable(it, TCF.db.class) then status = status .. "\n|cffff8040Your current class can't use it.|r" end
    self.status:SetText(status)
    local canEquip = TCF:CanEquipGear(it, TCF.db.class)
    self.equip:SetShown(canEquip and true or false)
    local left = chestKey and (TCF.db.keys[chestKey] or 0) or 0
    self.again:SetShown(left > 0)
    self.again:SetText("Open another (" .. left .. ")")
    self.age = 0
    self:Show()
    if it.q >= 4 then TCF:PlaySound("rare") end
  end

  function f:Next(skipQueue)
    table.remove(revealQueue, 1)
    if not skipQueue and revealQueue[1] then self:Show1(revealQueue[1]) else self:Hide() end
  end
  -- Show a fresh chest reward right away in place of the item on show (already in your bags),
  -- keeping anything else that is waiting. Used when you open a chest while the box is up.
  function f:ShowFront(entry)
    if not self:IsShown() or not revealQueue[1] then return (TCF.ShowLootRevealDirect or TCF.ShowLootReveal)(TCF, unpack(entry)) end
    revealQueue[1] = entry
    self:Show1(entry)
  end
  f:SetScript("OnHide", function() wipe(revealQueue) end)
  self.lootReveal = f
  return f
end

function TCF:ShowLootReveal(it, isNew, salvage, title, chestKey, isGear)
  local f = self.lootReveal or self:CreateLootReveal()
  if not f:IsShown() then wipe(revealQueue) end
  table.insert(revealQueue, { it, isNew, salvage, title, chestKey, isGear })
  if #revealQueue == 1 then f:Show1(revealQueue[1]) else f:UpdateQueue() end
end

---------------------------------------------------------------- Treasure Bag (unopened chests)
function TCF:CreateBag()
  local f = CreateFrame("Frame", "TapCatForeverBag", UIParent, BT)
  f:SetSize(400, 290); f:SetPoint("CENTER", 310, 0)
  f:SetFrameStrata("DIALOG"); f:SetToplevel(true)
  f:EnableMouse(true); f:SetMovable(true); f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving); f:SetScript("OnDragStop", f.StopMovingOrSizing)
  if f.SetBackdrop then f:SetBackdrop(BACKDROP_DIALOG) end
  f:Hide()
  tinsert(UISpecialFrames, "TapCatForeverBag")
  local title = Text(f, "GameFontNormalLarge", "Treasure Bag"); title:SetPoint("TOP", 0, -18)
  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton"); close:SetPoint("TOPRIGHT", -6, -6)
  local empty = Text(f, "GameFontDisable", "No unopened chests.\nEarn them from quests, dungeons,\nraids and class levels.")
  empty:SetPoint("CENTER", 0, -10)
  f.rows = {}
  for i, ch in ipairs(TCF.CHESTS) do
    local r = Panel(f, 360, 56, 0.9); r:SetPoint("TOP", 0, -44 - (i - 1) * 62)
    local ic = r:CreateTexture(nil, "ARTWORK"); ic:SetSize(40, 40); ic:SetPoint("LEFT", 8, 0); ic:SetTexture(TCF.Icon(ch.icon))
    r.count = Text(r, "NumberFontNormalLarge", nil, "RIGHT"); r.count:SetPoint("BOTTOMRIGHT", ic, "BOTTOMRIGHT", 2, -2)
    -- text stops 8px short of the Open button (row x 56 to 252; Open starts at 256)
    local n = Text(r, "GameFontNormal", ch.name, "LEFT"); n:SetPoint("TOPLEFT", ic, "TOPRIGHT", 8, -2); n:SetWidth(192)
    local d = Text(r, "GameFontDisableSmall", nil, "LEFT"); d:SetPoint("BOTTOMLEFT", ic, "BOTTOMRIGHT", 8, 2); d:SetWidth(192)
    if n.SetWordWrap then n:SetWordWrap(false); d:SetWordWrap(false) end
    d:SetText(({ pouch = "Daily quests, dungeons below 20", strong = "Dungeons 20+, weekly quest, levels", heroic = "Raids, zone clears, 20 levels" })[ch.key])
    r.all = Button(r, "All", 40, 22, function() TCF:OpenAllChests(ch.key) end); r.all:SetPoint("RIGHT", -8, 0)
    Tip(r.all, function(tt) tt:AddLine("Open all " .. ch.name .. "s", 1, 0.82, 0) end)
    r.open = Button(r, "Open", 52, 22, function() TCF:OpenChest(ch.key, true) end); r.open:SetPoint("RIGHT", r.all, "LEFT", -4, 0)
    Tip(r, function(tt)
      tt:AddLine(ch.name, 1, 0.82, 0)
      for rr = 1, 5 do
        if ch.weights[rr] > 0 then
          local col = TCF.RARITY[rr]
          tt:AddDoubleLine("|c" .. col.hex .. col.name .. "|r", ch.weights[rr] .. "%", 1, 1, 1, 1, 1, 1)
        end
      end
    end)
    r.chest = ch
    f.rows[i] = r
  end
  local openAll = Button(f, "Open everything", 140, 22, function() TCF:OpenAllChests() end)
  openAll:SetPoint("BOTTOM", 0, 14)
  function f:Refresh()
    local any = false
    for _, r in ipairs(self.rows) do
      local k = TCF.db.keys[r.chest.key] or 0
      r.count:SetText(k > 0 and k or "")
      r.open:SetEnabled(k > 0); r.all:SetEnabled(k > 1)
      r:SetShown(k > 0)
      any = any or k > 0
    end
    -- stack visible rows from the top
    local y = -44
    for _, r in ipairs(self.rows) do
      if r:IsShown() then r:ClearAllPoints(); r:SetPoint("TOP", 0, y); y = y - 62 end
    end
    empty:SetShown(not any)
    openAll:SetShown(any)
  end
  f:SetScript("OnShow", function(s) s:Refresh() end)
  self.bag = f
  return f
end

-- Open every chest of one kind (or every chest) at once; the loot window queues the results.
-- Every grant normally refreshes the whole UI, plays a sound and prints a line; for hundreds of
-- chests in one click that freezes the client, so those are muted for the batch and done once after.
function TCF:OpenAllChests(key)
  local refreshAll, playSound, print = self.RefreshAll, self.PlaySound, self.Print
  local opened, lines, rare = 0, {}, false
  self.RefreshAll = function() end
  -- muted for the batch, but remember if any drop asked for the rare sound
  self.PlaySound = function(_, kind) if kind == "rare" then rare = true end end
  self.Print = function(s, msg, force)
    if force then return print(s, msg, force) end
    lines[#lines + 1] = msg
  end
  self.openingAll = true
  local ok, err = pcall(function()
    for _, ch in ipairs(TCF.CHESTS) do
      if not key or ch.key == key then
        for _ = 1, math.min(TCF.db.keys[ch.key] or 0, 200) do
          self:OpenChest(ch.key, true); opened = opened + 1
        end
      end
    end
  end)
  self.openingAll = nil
  self.RefreshAll, self.PlaySound, self.Print = refreshAll, playSound, print
  if not ok then error(err, 0) end
  if opened == 0 then return end
  -- a few lines go to chat as usual; a big batch gets one summary instead of a wall of text
  if #lines <= 5 then
    for _, msg in ipairs(lines) do self:Print(msg) end
  else
    self:Print(string.format("Opened %d chests. Everything is already yours; the loot window lists it all.", opened), true)
  end
  self:PlaySound(rare and "rare" or "loot")
  self:RefreshAll()
end

function TCF:ToggleBag()
  local f = self.bag or self:CreateBag()
  if f:IsShown() then f:Hide() else f:Show() end
end
