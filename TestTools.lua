-- TapCatForever: test tools (1.8.0). Test mode only (Core.lua: only ever on the developer's character).
--  * saved states: copy the whole save into one of three slots, and put it back later (reloads the UI)
--  * open or close anything: professions and gathering spots forced open or closed, or left to the game
--  * quick setters: cat level, skills, guild rank, Renown points, bag, Adventure, companions, TapCoins
-- Opened with the "Test tools" button in Settings (test mode) or /tcf tools.
local ADDON, TCF = ...
local floor, max, min = math.floor, math.max, math.min

TCF.TEST_SNAP_SLOTS = 3

---------------------------------------------------------------- saved states
-- a plain copy (no metatables, no shared tables, no cycles)
local function copy(v, seen)
  if type(v) ~= "table" then return v end
  seen = seen or {}
  if seen[v] then return seen[v] end
  local out = {}
  seen[v] = out
  for k, x in next, v do out[copy(k, seen)] = copy(x, seen) end
  return out
end
TCF.TestCopy = copy

local function snaps()
  local sv = TapCatForeverDB
  local s = rawget(sv, "testSnaps")
  if type(s) ~= "table" then s = {}; rawset(sv, "testSnaps", s) end
  return s
end

function TCF:TestSnapInfo(slot)
  local s = rawget(TapCatForeverDB, "testSnaps")
  return type(s) == "table" and s[slot] or nil
end

function TCF:TestSnapSave(slot)
  if not self:TestModeOn() or not slot or slot < 1 or slot > TCF.TEST_SNAP_SLOTS then return false end
  local sv = TapCatForeverDB
  local data = {}
  for k, v in next, sv do if k ~= "testSnaps" then data[k] = copy(v) end end
  local cd = self:CD()
  local cl = TCF.CLASS_BY_KEY and TCF.CLASS_BY_KEY[self.db.class]
  snaps()[slot] = { when = time(), data = data,
    label = string.format("%s, level %d, %s coins", cl and cl.name or "?", cd and cd.level or 1, TCF.Commas(self.db.coins or 0)) }
  self:Print(string.format("Test: saved this state in slot %d.", slot), true)
  return true
end

-- puts a saved state back: everything but the saved slots themselves, then reloads the UI
function TCF:TestSnapLoad(slot, noReload)
  if not self:TestModeOn() then return false end
  local snap = self:TestSnapInfo(slot)
  if not snap or type(snap.data) ~= "table" then return false end
  local sv = TapCatForeverDB
  local keep = rawget(sv, "testSnaps")
  setmetatable(sv, nil)
  local keys = {}
  for k in next, sv do keys[#keys + 1] = k end
  for _, k in ipairs(keys) do sv[k] = nil end
  for k, v in next, snap.data do sv[k] = copy(v) end
  rawset(sv, "testSnaps", keep)
  -- test mode stays on (you're testing), whatever the saved state had
  if type(sv.ui) == "table" then sv.ui.testMode = true end
  self:Print(string.format("Test: restored slot %d. Reloading.", slot), true)
  if not noReload and ReloadUI then ReloadUI() end
  return true
end

function TCF:TestSnapDelete(slot)
  if not self:TestModeOn() then return false end
  local s = rawget(TapCatForeverDB, "testSnaps")
  if type(s) == "table" then s[slot] = nil end
  return true
end

---------------------------------------------------------------- open or close anything
-- forced state for a key: true (open), false (closed) or nil (the game decides). Test mode only.
function TCF:TestForced(key)
  if not (self.db and self.TestModeOn and self:TestModeOn()) then return nil end
  local f = self.db.testForce
  if type(f) ~= "table" then return nil end
  return f[key]
end

-- Auto -> Open -> Closed -> Auto
function TCF:TestCycleForce(key)
  if not self:TestModeOn() then return nil end
  local f = self.db.testForce
  if type(f) ~= "table" then f = {}; self.db.testForce = f end
  if f[key] == nil then f[key] = true elseif f[key] == true then f[key] = false else f[key] = nil end
  if self.CheckProfUnlocks then self:CheckProfUnlocks() end
  self:MarkDirty(); self:RefreshAll()
  return f[key]
end

function TCF:TestClearForces()
  if not self:TestModeOn() then return end
  self.db.testForce = nil
  self:MarkDirty(); self:RefreshAll()
end

TCF.TEST_FORCES = {
  { "prof:herbalism", "Herbalism" }, { "prof:firstaid", "First Aid" }, { "prof:fishing", "Fishing" },
  { "prof:cooking", "Cooking" }, { "spots", "Gathering spots" },
}

---------------------------------------------------------------- quick setters
TCF.TEST_SETTERS = {
  { "level1",     "Cat level 1" },
  { "level60",    "Cat level 60" },
  { "skillmax",   "Skills to 300" },
  { "skill1",     "Skills to 1" },
  { "rankup",     "Guild rank up" },
  { "rankdown",   "Guild rank down" },
  { "rp",         "+5 Renown points" },
  { "runearned",  "+1T Trade Gold" },
  { "bagup",      "Bigger bag" },
  { "bagdown",    "Smaller bag" },
  { "advall",     "Adventure: all" },
  { "advreset",   "Adventure: reset" },
  { "compall",    "All companions" },
  { "compnone",   "No companions" },
  { "coins1m",    "+1M TapCoins" },
  { "coins0",     "TapCoins to 0" },
}

function TCF:TestSet(kind)
  if not self:TestModeOn() then return false end
  local db, cd = self.db, self:CD()
  local s = self.ProfState and self:ProfState()
  if kind == "level1" or kind == "level60" then
    cd.level = kind == "level1" and 1 or TCF.MAX_LEVEL; cd.xp = 0
    if self.SettleXP then self:SettleXP() end
  elseif (kind == "skillmax" or kind == "skill1") and s then
    local v = kind == "skillmax" and 300 or 1
    s.skill = type(s.skill) == "table" and s.skill or {}
    for k in pairs(TCF.FAMILIES or {}) do
      s.skill[k] = v
      s.skill[TCF.FAMILIES[k].craft] = v
      if v == 300 then s.skillBest = type(s.skillBest) == "table" and s.skillBest or {}; s.skillBest[k] = 300 end
    end
    for _, p in ipairs(TCF.PROFESSIONS or {}) do if not p.family then s.skill[p.key] = v end end
  elseif (kind == "rankup" or kind == "rankdown") and self.GuildRank and self.DepthState then
    local craft = self:CraftProf()
    local d = self:DepthState()
    local r = self:GuildRank(craft)
    local nr = max(1, min(#TCF.GUILD_RANKS, r + (kind == "rankup" and 1 or -1)))
    d.rep[craft] = TCF.GUILD_RANKS[nr].rep
    if self.CheckGuildTitle then self:CheckGuildTitle(craft) end
  elseif kind == "rp" and self.DepthState then
    local d = self:DepthState(); d.rp = (d.rp or 0) + 5
  elseif kind == "runearned" and s then
    s.runEarned = (s.runEarned or 0) + 1e12; s.lifetime = max(s.lifetime or 0, s.runEarned)
    if self.CheckProfUnlocks then self:CheckProfUnlocks() end
  elseif kind == "bagup" or kind == "bagdown" then
    local lv = self.MatBagLevel and self:MatBagLevel() or 1
    db.matBag = max(1, min(#(TCF.MAT_BAGS or { 1 }), lv + (kind == "bagup" and 1 or -1)))
  elseif kind == "advall" and TCF.AdvStageCode then
    local n = #TCF.TIERS
    cd.adv.best = TCF.AdvStageCode(n, self:AdvStages(n))
    if self.CheckCompanionUnlocks then self:CheckCompanionUnlocks() end
  elseif kind == "advreset" then
    cd.adv.best = 0; cd.adv.tier, cd.adv.stage = 1, 1
  elseif kind == "compall" then
    self:TestCheat("companions")
  elseif kind == "compnone" and self.CompanionState then
    local cs = self:CompanionState()
    cs.owned, cs.walk, cs.walkShown = {}, nil, nil
    for _, c in pairs(db.classData or {}) do if type(c) == "table" then c.companion = nil end end
  elseif kind == "coins1m" then
    db.coins = (db.coins or 0) + 1000000
  elseif kind == "coins0" then
    db.coins = 0
  else
    return false
  end
  self:Print("Test: " .. kind .. ".", false)
  self:MarkDirty(); self:RefreshAll()
  return true
end

---------------------------------------------------------------- the window
local function stateText(v)
  if v == true then return "|cff66ff66Open|r" elseif v == false then return "|cffff5555Closed|r" end
  return "|cffaaaaaaAuto|r"
end

function TCF:CreateTestTools()
  local U = TCF.UI
  local Text, Button, Panel = U.Text, U.Button, U.Panel
  local W, H = 560, 470
  local f = CreateFrame("Frame", "TapCatForeverTestTools", UIParent, U.BT)
  f:SetSize(W, H); f:SetPoint("CENTER", 0, 40)
  f:SetFrameStrata("DIALOG"); f:SetToplevel(true)
  f:EnableMouse(true); f:SetMovable(true); f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving); f:SetScript("OnDragStop", f.StopMovingOrSizing)
  if f.SetBackdrop then f:SetBackdrop(U.BACKDROP_DIALOG) end
  f:Hide()
  if UISpecialFrames then tinsert(UISpecialFrames, "TapCatForeverTestTools") end
  local title = Text(f, "GameFontNormalLarge", "|cffff6060Test tools|r"); title:SetPoint("TOP", 0, -16)
  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton"); close:SetPoint("TOPRIGHT", -6, -6)

  -- saved states
  local snapBox = Panel(f, W - 32, 112, 0.9); snapBox:SetPoint("TOP", 0, -44)
  local st = Text(snapBox, "GameFontNormal", "Saved states", "LEFT"); st:SetPoint("TOPLEFT", 10, -8)
  local sh = Text(snapBox, "GameFontDisableSmall", "Restore puts the whole save back and reloads.", "RIGHT"); sh:SetPoint("TOPRIGHT", -10, -10)
  f.snapRows = {}
  for i = 1, TCF.TEST_SNAP_SLOTS do
    local y = -28 - (i - 1) * 26
    local lab = Text(snapBox, "GameFontHighlightSmall", nil, "LEFT"); lab:SetPoint("TOPLEFT", 10, y - 4); lab:SetWidth(W - 32 - 230)
    if lab.SetWordWrap then lab:SetWordWrap(false) end
    local save = Button(snapBox, "Save", 64, 20, function() TCF:TestSnapSave(i); f:Refresh() end)
    save:SetPoint("TOPRIGHT", -150, y)
    local load = Button(snapBox, "Restore", 70, 20, function()
      StaticPopupDialogs.TAPCATFOREVER_TESTRESTORE = {
        text = "Restore test slot " .. i .. "? Everything goes back to that saved state, and your UI reloads.",
        button1 = "Restore", button2 = CANCEL or "Cancel",
        OnAccept = function() TCF:TestSnapLoad(i) end,
        timeout = 0, whileDead = true, hideOnEscape = true, preferredIndex = 3,
      }
      StaticPopup_Show("TAPCATFOREVER_TESTRESTORE")
    end)
    load:SetPoint("LEFT", save, "RIGHT", 4, 0)
    local del = Button(snapBox, "X", 26, 20, function() TCF:TestSnapDelete(i); f:Refresh() end)
    del:SetPoint("LEFT", load, "RIGHT", 4, 0)
    f.snapRows[i] = { label = lab, load = load, del = del }
  end

  -- open or close
  local forceBox = Panel(f, W - 32, 92, 0.9); forceBox:SetPoint("TOP", snapBox, "BOTTOM", 0, -8)
  local ft = Text(forceBox, "GameFontNormal", "Open or close (click: Auto, Open, Closed)", "LEFT"); ft:SetPoint("TOPLEFT", 10, -8)
  local reset = Button(forceBox, "All auto", 80, 20, function() TCF:TestClearForces(); f:Refresh() end)
  reset:SetPoint("TOPRIGHT", -10, -6)
  f.forceBtns = {}
  local BW = floor((W - 32 - 20 - 8) / 3)
  for i, e in ipairs(TCF.TEST_FORCES) do
    local col, row = (i - 1) % 3, floor((i - 1) / 3)
    local b = Button(forceBox, "", BW, 22, function() TCF:TestCycleForce(e[1]); f:Refresh() end)
    b:SetPoint("TOPLEFT", 10 + col * (BW + 4), -32 - row * 26)
    b.entry = e
    f.forceBtns[i] = b
  end

  -- quick setters: four to a row
  local setBox = Panel(f, W - 32, 148, 0.9); setBox:SetPoint("TOP", forceBox, "BOTTOM", 0, -8)
  local qt = Text(setBox, "GameFontNormal", "Quick setters (the cat you're playing)", "LEFT"); qt:SetPoint("TOPLEFT", 10, -8)
  local SW = floor((W - 32 - 20 - 12) / 4)
  for i, e in ipairs(TCF.TEST_SETTERS) do
    local col, row = (i - 1) % 4, floor((i - 1) / 4)
    local b = Button(setBox, e[2], SW, 22, function() TCF:TestSet(e[1]); f:Refresh() end)
    b:SetPoint("TOPLEFT", 10 + col * (SW + 4), -30 - row * 28)
  end

  f.note = Text(f, "GameFontDisableSmall", nil, "CENTER"); f.note:SetPoint("BOTTOM", 0, 16); f.note:SetWidth(W - 40)
  f.note:SetText("Test mode only. These change your real save: keep a saved state to come back to.")

  function f:Refresh()
    for i, r in ipairs(self.snapRows) do
      local snap = TCF:TestSnapInfo(i)
      if snap then
        r.label:SetText(string.format("%d. %s |cffaaaaaa%s|r", i, snap.label or "", date and date("%m/%d %H:%M", snap.when or 0) or ""))
        r.load:Enable(); r.del:Enable()
      else
        r.label:SetText(string.format("%d. |cff777777empty|r", i))
        r.load:Disable(); r.del:Disable()
      end
    end
    for _, b in ipairs(self.forceBtns) do
      b:SetText(b.entry[2] .. ": " .. stateText(TCF:TestForced(b.entry[1])))
    end
  end
  f:SetScript("OnShow", function(self) self:Refresh() end)
  return f
end

function TCF:ToggleTestTools()
  if not self:TestModeOn() then
    if self.testTools then self.testTools:Hide() end
    return false
  end
  local f = self.testTools or self:CreateTestTools()
  self.testTools = f
  if f:IsShown() then f:Hide() else f:Show() end
  return true
end

---------------------------------------------------------------- give yourself anything (1.8.0)
-- Ctrl-click in the Compendium (test mode): a cosmetic or skin is yours, a gear piece goes in the bag,
-- a set gives every piece. Quietly, without salvage or achievements.
function TCF:TestGive(it)
  if not self:TestModeOn() or type(it) ~= "table" then return false end
  if TCF.GEAR and TCF.GEAR[it.id] == it then
    local bag = self:Bag()
    bag[it.id] = (bag[it.id] or 0) + 1
    self:Print("Test: " .. (TCF.GearLink and TCF.GearLink(it) or it.name) .. " is in your bag.", true)
  elseif TCF.ITEMS and TCF.ITEMS[it.id] then
    if not self.db.owned[it.id] then self.db.owned[it.id] = 1 end
    if self.NoteItemSource then self:NoteItemSource(it.id, "Test mode") end
    self:Print("Test: " .. TCF.ItemLink(it) .. " is yours.", true)
  else
    return false
  end
  self:MarkDirty(); self:RefreshAll()
  return true
end

function TCF:TestGiveSet(set)
  if not self:TestModeOn() or type(set) ~= "table" then return false end
  local bag, n = self:Bag(), 0
  if type((set.items or {})[1]) == "table" then
    -- a cosmetic set
    for _, it in ipairs(set.items) do if not self.db.owned[it.id] then self.db.owned[it.id] = 1; n = n + 1 end end
    self:Print(string.format("Test: %s (%d pieces) is yours.", set.name or "the set", n), true)
    self:MarkDirty(); self:RefreshAll()
    return true
  end
  for _, id in ipairs(set.items or {}) do
    if TCF.GEAR[id] and (bag[id] or 0) == 0 then bag[id] = 1; n = n + 1 end
  end
  self:Print(string.format("Test: %s (%d pieces) is in your bag.", set.name or "the set", n), true)
  self:MarkDirty(); self:RefreshAll()
  return true
end
