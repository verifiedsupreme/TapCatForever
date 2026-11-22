-- TapCatForever: a slim banner inside the main window while you are in a real WoW dungeon or
-- raid. It is part of the window (not a pop-up): it sits at the bottom of the character column,
-- under the stats, so it never covers the tabs or the What's new strip. It says where you are,
-- what finishing gives, the bosses killed this run, whether today's chest is still to come, and
-- the real boss rewards there. It updates while the window is open and hides outside instances.
local ADDON, TCF = ...

-- The banner's lines: { headline, line, ... } or nil outside a dungeon or raid.
function TCF:DungeonBannerLines()
  local here = TCF.CurrentInstance and TCF.CurrentInstance()
  if not here or not self.db then return nil end
  local raid = here.type == "raid"
  local chest = raid and "a Raider's Hoard" or "a Dungeon Chest"
  local coins = TCF.DUNGEON_BOSS_COINS and TCF.DUNGEON_BOSS_COINS[here.type] or (raid and 10 or 5)
  local name = here.name or (raid and "a raid" or "a dungeon")
  local lines = {
    string.format("You're in %s.", name),
    string.format("Finish it for %s; each boss gives %d TapCoins.", chest, coins),
  }
  local run = self.db.dungeonRun
  local progress
  if run and run.id == here.id and not run.leftAt then
    progress = string.format("Bosses this run: %d.", run.bosses or 0)
    if run.rewarded then
      progress = progress .. " Your chest for this run is in the Treasure Bag."
    else
      local why = self.DungeonChestBlockedReason and self:DungeonChestBlockedReason(run)
      if why then
        progress = progress .. " |cffff8060No chest this time:|r " .. why
      end
    end
  end
  if progress then lines[#lines + 1] = progress end
  -- real boss rewards here that this character doesn't have yet
  local parts = {}
  for _, b in ipairs(self.RealBossesIn and self:RealBossesIn(here.name) or {}) do
    for _, r in ipairs(b.rewards) do
      local it = TCF.ITEMS[r.id]
      if it and not self.db.owned[r.id] then
        parts[#parts + 1] = string.format("%s (%s, %s)", b.name, it.name,
          (r.chance or 0) >= 1 and "first kill" or (math.floor(r.chance * 100 + 0.5) .. "% each kill"))
      end
    end
  end
  if #parts > 0 then lines[#lines + 1] = "Real boss rewards here: " .. table.concat(parts, "; ") .. "." end
  return lines, #parts
end

local function leftColumn(win)
  -- the character column: the profile cat's stage sits in it (UI.lua)
  local ok, col = pcall(function() return win.preview.frame:GetParent():GetParent() end)
  if ok and type(col) == "table" and col.GetWidth then return col end
end

local function createBanner(win)
  local U = TCF.UI
  local f = CreateFrame("Frame", "TapCatForeverDungeonBanner", win, U.BT)
  if f.SetBackdrop then
    f:SetBackdrop(U.BACKDROP_PANEL)
    f:SetBackdropColor(0.10, 0.08, 0.02, 0.92)
    f:SetBackdropBorderColor(1, 0.82, 0.2, 1)
  end
  local col = leftColumn(win)
  if col then
    f:SetPoint("BOTTOMLEFT", col, "BOTTOMLEFT", 6, 6); f:SetPoint("BOTTOMRIGHT", col, "BOTTOMRIGHT", -6, 6)
  else
    f:SetPoint("BOTTOMLEFT", win, "BOTTOMLEFT", 22, 26); f:SetSize(304, 52)
  end
  f:SetHeight(52)
  if f.SetFrameLevel and win.GetFrameLevel then pcall(f.SetFrameLevel, f, (win:GetFrameLevel() or 1) + 20) end
  f.text = U.Text(f, "GameFontHighlightSmall", nil, "LEFT")
  f.text:SetPoint("TOPLEFT", 8, -6); f.text:SetPoint("TOPRIGHT", -8, -6)
  if f.text.SetJustifyV then f.text:SetJustifyV("TOP") end
  if f.text.SetSpacing then f.text:SetSpacing(1) end
  f:EnableMouse(true)
  U.Tip(f, function(tt)
    local lines = TCF:DungeonBannerLines()
    if not lines then return end
    tt:AddLine(lines[1], 1, 0.82, 0)
    for i = 2, #lines do tt:AddLine(lines[i], 1, 1, 1, true) end
    if TCF.DUNGEON_CHEST_TEXT then tt:AddLine(TCF.DUNGEON_CHEST_TEXT, 0.7, 0.7, 0.7, true) end
  end)
  local acc = 0
  f:SetScript("OnUpdate", function(_, e)
    acc = acc + e
    if acc < 1 then return end
    acc = 0
    TCF:RefreshDungeonBanner()
  end)
  f:Hide()
  return f
end

-- shows, updates or hides the banner (called when the window opens, on dungeon events and
-- every second while it is up)
function TCF:RefreshDungeonBanner()
  local win = self.window
  if not win then return end
  local lines, nRewards
  if win:IsShown() then lines, nRewards = self:DungeonBannerLines() end
  local f = self.dungeonBanner
  if not lines then
    if f then f:Hide() end
    return
  end
  f = f or createBanner(win)
  self.dungeonBanner = f
  -- the banner keeps to three short lines; the real boss rewards are in its tooltip
  local shown = { "|cffffd100" .. lines[1] .. "|r", lines[2] }
  for i = 3, #lines - ((nRewards or 0) > 0 and 1 or 0) do shown[#shown + 1] = lines[i] end
  if (nRewards or 0) > 0 then shown[#shown + 1] = "|cff99ccffReal boss rewards here: hover to see them.|r" end
  f.text:SetText(table.concat(shown, " "))
  local h = f.text.GetStringHeight and f.text:GetStringHeight()
  if type(h) == "number" and h > 0 then f:SetHeight(math.min(66, h + 12)) end
  f:Show()
end

-- watch the window: a hidden child gets OnShow whenever the window is shown
do
  local create = TCF.CreateWindow
  function TCF:CreateWindow(...)
    local r = create(self, ...)
    local win = self.window
    if win and not win.dungeonWatch then
      win.dungeonWatch = CreateFrame("Frame", nil, win)
      win.dungeonWatch:SetScript("OnShow", function() TCF:RefreshDungeonBanner() end)
      if win.IsShown and win:IsShown() then TCF:RefreshDungeonBanner() end
    end
    return r
  end
end
