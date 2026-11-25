-- TapCatForever: companion cats on screen and in their window (1.7.4, Companions.lua has the data).
--  * the walker: with Companion Stroll, your cat's companion (a real WoW cat model) walks back and forth
--    beside your cat, party-cat sized, on the other side from the party cats' row
--  * the Companion Cats window: every companion as its real model, bought or chosen from here
local ADDON, TCF = ...
local floor, max, min, random = math.floor, math.max, math.min, math.random

-- PlayerModel facing in radians: 0 looks at you; FACE_RIGHT turns the model to walk toward the
-- right of the screen
TCF.COMPANION_FACE_RIGHT = math.pi / 2
local ANIM_STAND = 0
-- WoW animation ids (AnimationData): a model without one plays its stand instead
TCF.COMPANION_ANIM = { stand = 0, walk = 4, sit = 97, sleep = 100 }
TCF.COMPANION_CURIOUS = 6        -- tapping face level (1-10) that makes it curious: a long fast streak, never a single tap
local WALK_W, WALK_H, MODEL = 168, 44, 44   -- the strip: as wide as four party cats, party-cat tall
local SPEED = 13                             -- pixels a second
local CHECK_AFTER = 0.6                      -- seconds before asking whether the model loaded

-- show a companion's model in a PlayerModel frame; remembers it so it can be checked and set again
local function setModel(m, c, facing, anim)
  if m.settingModel then return end      -- Show() below can run the frame's OnShow, which sets it again
  m.comp = c
  if m.ClearModel then pcall(m.ClearModel, m) end
  if not c then m:Hide(); return end
  m.settingModel = true
  m:Show()
  m.settingModel = nil
  pcall(m.SetDisplayInfo, m, c.display)
  pcall(m.SetPortraitZoom, m, 0)
  pcall(m.SetCamDistanceScale, m, 1)
  pcall(m.SetFacing, m, facing or 0)
  pcall(m.SetAnimation, m, anim or ANIM_STAND)
  m.check, m.retried = CHECK_AFTER, nil
end
TCF.CompanionSetModel = setModel

-- 0.6 s after showing it: a model the game can't load is remembered and hidden (true: it was missing)
local function checkModel(m, e)
  if not m.check then return false end
  m.check = m.check - e
  if m.check > 0 then return false end
  m.check = nil
  if not m.GetModelFileID or not m.comp then return false end
  local ok, file = pcall(m.GetModelFileID, m)
  if ok and not file and not m.retried then
    -- maybe still loading: set it again and look once more a little later
    m.retried = true
    pcall(m.SetDisplayInfo, m, m.comp.display)
    m.check = 2
    return false
  end
  if ok and not file then
    TCF:CompanionModelMissing(m.comp.key)
    m:Hide()
    return true
  end
  return false
end
TCF.CompanionCheckModel = checkModel

---------------------------------------------------------------- the walker
local walker

local function placeWalker()
  local cat = TCF.cat
  if not walker or not cat or not cat.frame then return end
  -- the opposite side from the party cats' row (on the right unless the screen edge moved it left),
  -- unless that side is off the screen: then the other side (beyond the row, if it's there)
  local row = TCF.PartyRowFrame and TCF.PartyRowFrame()
  local rowShown = row and row:IsShown()
  local right = rowShown and row.left and true or false
  local hud = TCF.hud
  local l, r = hud and hud.GetLeft and hud:GetLeft(), hud and hud.GetRight and hud:GetRight()
  local sw = UIParent and UIParent.GetWidth and UIParent:GetWidth()
  local hs = hud and hud.GetEffectiveScale and hud:GetEffectiveScale()
  local us = UIParent and UIParent.GetEffectiveScale and UIParent:GetEffectiveScale()
  local beyond = 0
  if type(l) == "number" and type(r) == "number" and type(sw) == "number" and type(hs) == "number" and type(us) == "number" and us > 0 then
    local need = (WALK_W + 4) * hs / us
    local roomL, roomR = l * hs / us, sw - r * hs / us
    if right and roomR < need and roomL >= need then right = false
    elseif not right and roomL < need and roomR >= need then right = true end
    -- on the same side as the party cats: past them
    if rowShown and (row.left and true or false) == (not right) then beyond = row:GetWidth() or 0 end
  end
  if walker.right == right and walker.beyond == beyond and walker.placed then return end
  walker.beyond = beyond
  walker.right, walker.placed = right, true
  walker:ClearAllPoints()
  if right then walker:SetPoint("BOTTOMLEFT", cat.frame, "BOTTOMRIGHT", 2 + beyond, 0)
  else walker:SetPoint("BOTTOMRIGHT", cat.frame, "BOTTOMLEFT", -2 - beyond, 0) end
end

local function face(dir)
  local m = walker.model
  pcall(m.SetFacing, m, dir * TCF.COMPANION_FACE_RIGHT)
end
local function anim(id)
  if walker.anim == id then return end
  walker.anim = id
  pcall(walker.model.SetAnimation, walker.model, id)
end

-- the end of the strip next to your cat, and which way your cat is from the companion
local function catEnd() return walker.right and 0 or (WALK_W - MODEL) end
local function towardCat() return walker.right and -1 or 1 end

-- resting: stand, sit or (now and then, for longer) lie down for a nap
local function startIdle()
  walker.walking = false
  local r = random()
  if r < 0.18 then
    walker.wait = 8 + random() * 8; anim(TCF.COMPANION_ANIM.sleep)
  elseif r < 0.55 then
    walker.wait = 4 + random() * 6; anim(TCF.COMPANION_ANIM.sit)
  else
    walker.wait = 2 + random() * 4; anim(TCF.COMPANION_ANIM.stand)
  end
  face(towardCat() * 0.35)          -- a little turn toward your cat while it rests
end

local function startWalk(target)
  local span = WALK_W - MODEL
  if not target then
    target = random() * span
    if math.abs(target - walker.x) < 20 then target = (walker.x < span / 2) and span or 0 end
  end
  walker.target = target
  walker.walking = true
  anim(TCF.COMPANION_ANIM.walk)
  face(target > walker.x and 1 or -1)
end

-- what your cat is doing: being petted (Purr.lua), or a long fast tapping streak (the tapping faces,
-- Core.lua). Single taps and short bursts never reach it.
local function mood()
  local now = GetTime and GetTime() or 0
  local pet = TCF.PurrFaceLevel and TCF:PurrFaceLevel() or 0
  if pet > 0 then return "pet", pet end
  local tap = TCF.TapFaceLevel and TCF:TapFaceLevel(now) or 0
  if tap >= TCF.COMPANION_CURIOUS then return "curious", tap end
  return "calm", 0
end

local function hop(self, e, height)
  self.hopT = (self.hopT or 0) + e
  return math.abs(math.sin(self.hopT * 9)) * height
end

-- go to a spot, then sit there watching your cat (petting: right beside it; curious: a few steps closer)
local function goSitWatch(self, spot, sway, e)
  if self.walking and math.abs(self.target - spot) > 1 then self.walking = false end
  if not self.walking and math.abs(self.x - spot) > 1 then startWalk(spot); return end
  if not self.walking then
    anim(TCF.COMPANION_ANIM.sit)
    self.lookT = (self.lookT or 0) + e
    -- its eyes on your cat; curious: a little head-turn now and then
    face(towardCat() * (0.85 + (sway and math.sin(self.lookT * 1.3) * 0.25 or 0)))
    self.wait = 1.5 + random() * 2     -- when the mood passes, it rests a moment before wandering
  end
end

local function walkerUpdate(self, e)
  if checkModel(self.model, e) then self:Hide(); return end
  self.placeT = (self.placeT or 0) - e
  if self.placeT <= 0 then self.placeT = 1; placeWalker() end
  local m, level = mood()
  local was = self.mood
  self.mood = m
  local lift = 0
  local span = WALK_W - MODEL
  if m == "pet" then
    goSitWatch(self, catEnd(), false, e)
    if level >= 10 and not self.walking then lift = hop(self, e, 6) end   -- a happy hop when your cat purrs
  elseif m == "curious" then
    -- a few steps closer to your cat (never further away), then sits and looks
    if was ~= "curious" then
      local toward = towardCat()
      local spot = self.x + toward * span * 0.35
      if toward > 0 then spot = min(span, spot) else spot = max(0, spot) end
      self.curiousSpot = spot
    end
    goSitWatch(self, self.curiousSpot or self.x, true, e)
  elseif was == "pet" or was == "curious" then
    startIdle()       -- the moment passed: a fresh rest, then wandering again
  end
  if self.walking then
    local d = self.target - self.x
    local step = SPEED * e
    if math.abs(d) <= step then
      self.x = self.target
      if m == "calm" then startIdle() else self.walking = false end
    else
      self.x = self.x + (d > 0 and step or -step)
    end
  elseif m == "calm" then
    self.wait = (self.wait or 0) - e
    if self.wait <= 0 then startWalk() end
  end
  if lift == 0 then self.hopT = 0 end
  self.model:ClearAllPoints()
  self.model:SetPoint("BOTTOMLEFT", self, "BOTTOMLEFT", self.x, lift)
end

local function createWalker()
  local hud = TCF.hud
  if not hud or not TCF.cat then return nil end
  local f = CreateFrame("Frame", "TapCatForeverCompanion", hud)
  f:SetSize(WALK_W, WALK_H)
  local m = CreateFrame("PlayerModel", nil, f)
  m:SetSize(MODEL, MODEL)
  m:SetPoint("BOTTOMLEFT", f, "BOTTOMLEFT", 0, 0)
  f.model = m
  f.x = (WALK_W - MODEL) / 2
  f:SetScript("OnUpdate", walkerUpdate)
  -- set the model again whenever it comes back (a hidden model can come back empty)
  f:SetScript("OnShow", function(self) if self.comp then setModel(self.model, self.comp); self.anim = nil; startIdle() end end)
  f:Hide()
  return f
end

-- shows, hides or changes the walker for the cat you're playing (called on every change)
function TCF:CompanionRefresh()
  local c = self.db and self:Companion()
  local want = c and self:CompanionWalkOn() and not self:CompanionMissing(c.key) and self.hud ~= nil
  if not want then
    if walker then walker.comp = nil; walker:Hide() end
    return
  end
  if not walker then walker = createWalker(); if not walker then return end end
  local changed = walker.comp ~= c
  walker.comp = c
  walker.placed = false
  placeWalker()
  if changed or not walker:IsShown() then
    setModel(walker.model, c)
    walker.anim = nil
    walker.model:ClearAllPoints()
    walker.model:SetPoint("BOTTOMLEFT", walker, "BOTTOMLEFT", walker.x, 0)
    startIdle()
  end
  walker:Show()
end
TCF.CompanionWalkerFrame = function() return walker end

---------------------------------------------------------------- the Companion Cats window
local PER_PAGE, COLS = 8, 4
local CELL_W, CELL_H = 128, 150

function TCF:CreateCompanionWindow()
  local U = TCF.UI
  local Text, Button, Panel, Tip = U.Text, U.Button, U.Panel, U.Tip
  local f = CreateFrame("Frame", "TapCatForeverCompanions", UIParent, U.BT)
  f:SetSize(COLS * (CELL_W + 8) + 40, 2 * (CELL_H + 8) + 204)
  f:SetPoint("CENTER", 0, 30)
  f:SetFrameStrata("DIALOG"); f:SetToplevel(true)
  f:EnableMouse(true); f:SetMovable(true); f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving); f:SetScript("OnDragStop", f.StopMovingOrSizing)
  if f.SetBackdrop then f:SetBackdrop(U.BACKDROP_DIALOG) end
  f:Hide()
  if UISpecialFrames then tinsert(UISpecialFrames, "TapCatForeverCompanions") end
  f.title = Text(f, "GameFontNormalLarge", "Companion Cats"); f.title:SetPoint("TOP", 0, -18)
  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton"); close:SetPoint("TOPRIGHT", -6, -6)
  f.sub = Text(f, "GameFontHighlightSmall", nil, "CENTER"); f.sub:SetPoint("TOP", f.title, "BOTTOM", 0, -6)
  f.sub:SetWidth(COLS * (CELL_W + 8) - 20)
  f.page = 1
  f.cells = {}
  for i = 1, PER_PAGE do
    local col, row = (i - 1) % COLS, floor((i - 1) / COLS)
    local cell = Panel(f, CELL_W, CELL_H, 0.9)
    cell:SetPoint("TOPLEFT", 20 + col * (CELL_W + 8), -78 - row * (CELL_H + 8))
    cell.model = CreateFrame("PlayerModel", nil, cell)
    cell.model:SetPoint("TOPLEFT", 4, -4); cell.model:SetPoint("TOPRIGHT", -4, -4); cell.model:SetHeight(88)
    cell.name = Text(cell, "GameFontNormalSmall", nil, "CENTER"); cell.name:SetPoint("TOP", cell.model, "BOTTOM", 0, -2)
    cell.name:SetWidth(CELL_W - 8)
    if cell.name.SetWordWrap then cell.name:SetWordWrap(false) end
    cell.info = Text(cell, "GameFontHighlightSmall", nil, "CENTER"); cell.info:SetPoint("TOP", cell.name, "BOTTOM", 0, -2)
    cell.info:SetWidth(CELL_W - 8)
    if cell.info.SetWordWrap then cell.info:SetWordWrap(false) end
    cell.btn = Button(cell, "Buy", CELL_W - 16, 20, function()
      local c = cell.comp
      if not c then return end
      if TCF:CompanionOwned(c.key) then
        if TCF:Companion() == c then TCF:SetCompanion(nil) else TCF:SetCompanion(c.key) end
        TCF:PlaySound("click")
      else
        local ok, why = TCF:BuyCompanion(c.key)
        if not ok and why then TCF:Print(why, true) end
      end
      f:Refresh()
    end)
    cell.btn:SetPoint("BOTTOM", 0, 6)
    cell.hover = CreateFrame("Frame", nil, cell)
    cell.hover:SetAllPoints(cell.model)
    cell.hover:EnableMouse(true)
    Tip(cell.hover, function(tt) if cell.comp then TCF:CompanionTooltip(tt, cell.comp) end end)
    Tip(cell.btn, function(tt) if cell.comp then TCF:CompanionTooltip(tt, cell.comp) end end)
    f.cells[i] = cell
  end
  local prev = Button(f, "<", 28, 22, function() f.page = max(1, f.page - 1); f:Refresh() end)
  local nextB = Button(f, ">", 28, 22, function() f.page = f.page + 1; f:Refresh() end)
  f.pageText = Text(f, "GameFontHighlightSmall", nil, "CENTER")
  f.pageText:SetPoint("TOP", 0, -78 - 2 * (CELL_H + 8) - 4)
  prev:SetPoint("RIGHT", f.pageText, "LEFT", -10, 0)
  nextB:SetPoint("LEFT", f.pageText, "RIGHT", 10, 0)
  f:EnableMouseWheel(true)
  f:SetScript("OnMouseWheel", function(_, d) f.page = max(1, f.page - d); f:Refresh() end)

  -- Companion Stroll: buy it, then turn it on or off
  local stroll = Panel(f, COLS * (CELL_W + 8) - 8, 76, 0.9)
  stroll:SetPoint("BOTTOM", 0, 18)
  stroll.title = Text(stroll, "GameFontNormal", "Companion Stroll", "LEFT"); stroll.title:SetPoint("TOPLEFT", 12, -10)
  stroll.text = Text(stroll, "GameFontHighlightSmall", nil, "LEFT"); stroll.text:SetPoint("TOPLEFT", stroll.title, "BOTTOMLEFT", 0, -4)
  stroll.text:SetWidth(COLS * (CELL_W + 8) - 8 - 200)
  stroll.buy = Button(stroll, "", 160, 22, function()
    if TCF:CompanionWalkOwned() then
      TCF:SetCompanionWalkShown(not TCF:CompanionWalkOn())
    else
      local ok, why = TCF:BuyCompanionWalk()
      if not ok and why then TCF:Print(why, true) end
    end
    TCF:PlaySound("click")
    f:Refresh()
  end)
  stroll.buy:SetPoint("RIGHT", -12, 0)
  f.stroll = stroll

  f.spin = 0
  f:SetScript("OnUpdate", function(self, e)
    self.spin = self.spin + e * 0.5
    for _, cell in ipairs(self.cells) do
      if cell.comp and cell.model:IsShown() then
        if checkModel(cell.model, e) then self:Refresh()
        else pcall(cell.model.SetFacing, cell.model, 0.5 + math.sin(self.spin) * 0.6) end
      end
    end
  end)
  f:SetScript("OnShow", function(self)
    for _, cell in ipairs(self.cells) do cell.comp = nil end   -- a hidden model can come back empty: set them all again
    self:Refresh()
  end)

  -- TapCoins change while it's open: the Buy buttons follow (Core.lua's ticker calls this)
  function f:RefreshLight()
    if (TCF.db.coins or 0) ~= self.lastCoins then self.lastCoins = TCF.db.coins; self:Refresh() end
  end

  function f:Refresh()
    local cl = TCF.CLASS_BY_KEY and TCF.CLASS_BY_KEY[TCF.db.class]
    local mine = TCF:Companion()
    self.sub:SetText(string.format("Your %s cat's companion: %s\nEach of your cats chooses its own. Companions you own are for all of them.",
      cl and cl.name or "", mine and ("|cffffd100" .. mine.name .. "|r") or "none yet"))
    local list = TCF:CompanionList()
    local pages = max(1, math.ceil(#list / PER_PAGE))
    self.page = min(self.page, pages)
    self.pageText:SetText(string.format("%d / %d", self.page, pages))
    for i, cell in ipairs(self.cells) do
      local c = list[(self.page - 1) * PER_PAGE + i]
      if c then
        cell:Show()
        if cell.comp ~= c then setModel(cell.model, c, 0.5) end
        cell.comp = c
        local col = TCF.RARITY and TCF.RARITY[c.rarity] and TCF.RARITY[c.rarity].color or { 1, 1, 1 }
        cell.name:SetText(c.name); cell.name:SetTextColor(col[1], col[2], col[3])
        local owned = TCF:CompanionOwned(c.key)
        local missing = TCF:CompanionMissing(c.key)
        if missing then cell.model:Hide() end
        if owned then
          cell.info:SetText(mine == c and "|cff66ff66With your cat|r" or "|cff66ff66Owned|r")
          cell.btn:SetText(mine == c and "Unchoose" or "Choose"); cell.btn:Enable()
        elseif c.price > 0 then
          cell.info:SetText(missing and "|cffff5555Not in your game|r" or string.format("|cffffa040%s TapCoins|r", TCF.Commas(c.price)))
          cell.btn:SetText("Buy")
          if missing or (TCF.db.coins or 0) < c.price then cell.btn:Disable() else cell.btn:Enable() end
        else
          local _, t = TCF.CompanionTier(c)
          cell.info:SetText("|cffffd100Clear " .. (t and t.name or "a dungeon") .. "|r")
          cell.btn:SetText("Earned in Adventure"); cell.btn:Disable()
        end
      else
        cell.comp = nil; cell:Hide()
      end
    end
    local st = self.stroll
    if TCF:CompanionWalkOwned() then
      st.text:SetText("Your companion walks beside your cat on screen, on the other side from the party cats. Turn it off any time.")
      st.buy:SetText(TCF:CompanionWalkOn() and "Turn off" or "Turn on"); st.buy:Enable()
    else
      st.text:SetText(string.format("Your companion walks back and forth beside your cat on screen. A huge investment: %s TapCoins, for your whole account.",
        TCF.Commas(TCF.COMPANION_WALK_PRICE)))
      st.buy:SetText(string.format("Buy: %s", TCF.Commas(TCF.COMPANION_WALK_PRICE)))
      if (TCF.db.coins or 0) < TCF.COMPANION_WALK_PRICE then st.buy:Disable() else st.buy:Enable() end
    end
  end
  return f
end

function TCF:ToggleCompanions()
  local f = self.companionWin or self:CreateCompanionWindow()
  self.companionWin = f
  if f:IsShown() then f:Hide() else f:Show() end
end
