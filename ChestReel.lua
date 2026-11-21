-- TapCatForever: chest opening reel. Random possible loot (rolled with the chest's own
-- rarity odds, never the same item twice) scrolls by, slows down and lands on the real reward.
local ADDON, TCF = ...
local floor, random, min, max = math.floor, math.random, math.min, math.max

local CARD, GAP, VISIBLE, COUNT, LAND = 56, 6, 8, 34, 30
local STEP = CARD + GAP
local DUR, HOLD = 2.4, 0.45

-- gear by quality, built once
local gearByQ
local function gearPool(q)
  if not gearByQ then
    gearByQ = {}
    for _, g in pairs(TCF.GEAR) do gearByQ[g.q] = gearByQ[g.q] or {}; table.insert(gearByQ[g.q], g) end
  end
  return gearByQ[q] or {}
end

-- a random thing this chest could hold: gear (90%) or a cosmetic (10%) of a rolled rarity
local function randomLoot(ch, seen)
  local class = TCF.db.class
  for _ = 1, 30 do
    local r = TCF:RollRarity(ch.weights)
    local it, rarity
    if random() < 0.9 then
      local pool = gearPool(max(2, r))
      local g = pool[random(max(1, #pool))]
      if g and TCF:GearUsable(g, class) then it, rarity = g, g.q end
    else
      local c = TCF.ITEM_LIST[random(#TCF.ITEM_LIST)]
      if c.source == "loot" and c.rarity == r and (c.class == nil or c.class == class) then it, rarity = c, c.rarity end
    end
    if it and not seen[it] then seen[it] = true; return it, rarity end
  end
  local c = TCF.ITEM_LIST[random(#TCF.ITEM_LIST)]
  return c, c.rarity
end

local function makeCard(parent)
  local c = CreateFrame("Frame", nil, parent)
  c:SetSize(CARD, CARD)
  c.bg = c:CreateTexture(nil, "BACKGROUND"); c.bg:SetAllPoints(); c.bg:SetColorTexture(0.08, 0.07, 0.1, 1)
  c.edge = c:CreateTexture(nil, "BORDER"); c.edge:SetAllPoints()
  c.icon = c:CreateTexture(nil, "ARTWORK"); c.icon:SetPoint("TOPLEFT", 4, -4); c.icon:SetPoint("BOTTOMRIGHT", -4, 4)
  c.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
  -- cosmetics get a purple corner badge so they're easy to tell from gear
  c.tag = c:CreateTexture(nil, "OVERLAY", nil, 2); c.tag:SetSize(14, 14); c.tag:SetPoint("TOPRIGHT", -2, -2); c.tag:SetColorTexture(0.75, 0.45, 1, 1)
  c.glow = c:CreateTexture(nil, "OVERLAY"); c.glow:SetPoint("TOPLEFT", -10, 10); c.glow:SetPoint("BOTTOMRIGHT", 10, -10)
  c.glow:SetTexture("Interface\\Buttons\\CheckButtonHilight"); c.glow:SetBlendMode("ADD"); c.glow:Hide()
  return c
end

local function setCard(c, it, rarity)
  local col = TCF.RARITY[rarity] and TCF.RARITY[rarity].color or { 1, 1, 1 }
  c.edge:SetColorTexture(col[1], col[2], col[3], 1)
  c.icon:SetTexture(TCF.Icon(it.icon or "INV_Misc_QuestionMark"))
  c.tag:SetShown(it.q == nil)
  c.glow:Hide()
end

local function createReel()
  local f = CreateFrame("Frame", "TapCatForeverReel", UIParent, TCF.UI.BT)
  f:SetSize(VISIBLE * STEP + 40, 150); f:SetPoint("CENTER", 0, 80)
  f:SetFrameStrata("FULLSCREEN_DIALOG"); f:SetToplevel(true); f:EnableMouse(true)
  if f.SetBackdrop then f:SetBackdrop(TCF.UI.BACKDROP_DIALOG) end
  f.title = TCF.UI.Text(f, "GameFontNormalLarge"); f.title:SetPoint("TOP", 0, -16)
  f.hint = TCF.UI.Text(f, "GameFontDisableSmall", "Click to skip"); f.hint:SetPoint("BOTTOM", 0, 10)
  local strip = CreateFrame("Frame", nil, f)
  strip:SetSize(VISIBLE * STEP, CARD + 8); strip:SetPoint("CENTER", 0, -4)
  if strip.SetClipsChildren then strip:SetClipsChildren(true) end
  f.strip = strip
  f.cards = {}
  for i = 1, COUNT do f.cards[i] = makeCard(strip) end
  -- the gold marker in the middle
  local mk = f:CreateTexture(nil, "OVERLAY"); mk:SetSize(4, CARD + 16); mk:SetPoint("CENTER", strip, "CENTER", 0, 0); mk:SetColorTexture(1, 0.82, 0.2, 0.9)
  f:SetScript("OnMouseUp", function(s) if s.t < DUR then s.t = DUR end end)
  f:SetScript("OnUpdate", function(s, e)
    s.t = s.t + e
    local p = min(1, s.t / DUR)
    local ease = 1 - (1 - p) ^ 3
    local off = s.endOff * ease
    local center = VISIBLE * STEP / 2
    for i, c in ipairs(s.cards) do
      c:ClearAllPoints()
      c:SetPoint("LEFT", s.strip, "LEFT", (i - 1) * STEP + GAP / 2 - off, 0)
    end
    -- a soft tick each time a new card passes the marker
    local idx = floor((off + center) / STEP)
    if idx ~= s.lastIdx then s.lastIdx = idx; if p < 1 then TCF:PlaySound("click") end end
    if p >= 1 and not s.landed then
      s.landed = true
      s.cards[LAND].glow:Show()
      TCF:PlaySound(s.rarity >= 4 and "rare" or "loot")
    end
    if s.t >= DUR + HOLD then s:Finish() end
  end)
  function f:Finish()
    self:Hide()
    local queue = self.queue
    self.queue = {}
    for _, args in ipairs(queue) do TCF.ShowLootRevealDirect(TCF, unpack(args)) end
  end
  f.queue = {}
  f:Hide()
  return f
end

-- Play the reel for a chest reward, then show the usual loot box.
function TCF:PlayChestReel(it, rarity, chestKey, args)
  local f = self.reel or createReel(); self.reel = f
  if f:IsShown() then table.insert(f.queue, args); return end
  local ch = TCF.CHEST_BY_KEY[chestKey]
  f.title:SetText("Opening " .. (ch and ch.name or "chest") .. "...")
  local seen = { [it] = true }
  for i, c in ipairs(f.cards) do
    if i == LAND then setCard(c, it, rarity)
    else local r, rr = randomLoot(ch, seen); setCard(c, r, rr) end
  end
  local center = VISIBLE * STEP / 2
  f.endOff = (LAND - 1) * STEP + GAP / 2 + CARD / 2 - center + random(-CARD * 0.3, CARD * 0.3)
  f.t, f.landed, f.lastIdx, f.rarity = 0, false, nil, rarity
  f.queue = { args }
  f:Show()
end

-- Hook the loot box: chest rewards spin first (unless turned off, or opening many at once).
TCF.ShowLootRevealDirect = TCF.ShowLootReveal
function TCF:ShowLootReveal(it, isNew, salvage, title, chestKey, isGear)
  local args = { it, isNew, salvage, title, chestKey, isGear }
  local ch = chestKey and TCF.CHEST_BY_KEY[chestKey]
  if ch and it and self.db.ui.chestAnim ~= false and not self.openingAll then
    local rarity = isGear and it.q or it.rarity or 1
    return self:PlayChestReel(it, rarity, chestKey, args)
  end
  if self.reel and self.reel:IsShown() then table.insert(self.reel.queue, args); return end
  return TCF.ShowLootRevealDirect(self, unpack(args))
end
