-- TapCatForever: a slim banner inside the main window while you are in a real WoW dungeon or
-- raid. It is part of the window (not a pop-up): a child of the character column at its bottom,
-- under the stats, so it never covers the tabs, the page or the What's new strip. Three short
-- lines: where you are, what finishing gives (or that this run gives no chest), the bosses
-- killed this run and a hint when real bosses there have rewards; the details are in its
-- tooltip. It updates while the window is open and hides outside instances.
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

-- The three short lines shown in the banner itself (the full lines are in its tooltip):
-- where you are; the chest (or why not) and the coins; bosses this run and the real boss
-- rewards hint. Each stays under about 50 characters so it fits the character column.
function TCF:DungeonBannerShort()
  local here = TCF.CurrentInstance and TCF.CurrentInstance()
  if not here or not self.db then return nil end
  local raid = here.type == "raid"
  local coins = TCF.DUNGEON_BOSS_COINS and TCF.DUNGEON_BOSS_COINS[here.type] or (raid and 10 or 5)
  local name = here.name or (raid and "a raid" or "a dungeon")
  local l1 = "|cffffd100" .. string.format("You're in %s.", name) .. "|r"
  local l2 = string.format("Finish it for %s; %d TapCoins a boss.", raid and "a Raider's Hoard" or "a Dungeon Chest", coins)
  local l3
  local run = self.db.dungeonRun
  if run and run.id == here.id and not run.leftAt then
    if run.rewarded then
      l2 = "This run's chest is in your Treasure Bag."
    elseif self.DungeonChestBlockedReason and self:DungeonChestBlockedReason(run) then
      l2 = "|cffff8060No chest this time|r (hover to see why)."
    end
    l3 = string.format("Bosses this run: %d.", run.bosses or 0)
  end
  local _, nRewards = self:DungeonBannerLines()
  if (nRewards or 0) > 0 then
    l3 = (l3 and (l3 .. " ") or "") .. "|cff99ccffReal boss rewards: hover.|r"
  end
  return { l1, l2, l3 }
end

local function leftColumn(win)
  -- the character column: the profile cat's stage sits in it (UI.lua)
  local ok, col = pcall(function() return win.preview.frame:GetParent():GetParent() end)
  if ok and type(col) == "table" and col.GetWidth then return col end
end

TCF.DUNGEON_BANNER_H = 48   -- three short lines; the stats above end about 55 px over the column's bottom

local function createBanner(win)
  local U = TCF.UI
  -- a child of the character column: it shows and hides with it, and never reaches the tabs,
  -- the page or the What's new strip (which sits outside the window)
  local col = leftColumn(win)
  local f = CreateFrame("Frame", "TapCatForeverDungeonBanner", col or win, U.BT)
  if f.SetBackdrop then
    f:SetBackdrop(U.BACKDROP_PANEL)
    f:SetBackdropColor(0.10, 0.08, 0.02, 0.92)
    f:SetBackdropBorderColor(1, 0.82, 0.2, 1)
  end
  if col then
    f:SetPoint("BOTTOMLEFT", col, "BOTTOMLEFT", 6, 4); f:SetPoint("BOTTOMRIGHT", col, "BOTTOMRIGHT", -6, 4)
  else
    f:SetPoint("BOTTOMLEFT", win, "BOTTOMLEFT", 22, 24); f:SetSize(304, TCF.DUNGEON_BANNER_H)
  end
  f:SetHeight(TCF.DUNGEON_BANNER_H)
  local base = col or win
  if f.SetFrameLevel and base.GetFrameLevel then pcall(f.SetFrameLevel, f, (base:GetFrameLevel() or 1) + 20) end
  if f.SetClipsChildren then f:SetClipsChildren(true) end
  f.text = U.Text(f, "GameFontHighlightSmall", nil, "LEFT")
  f.text:SetPoint("TOPLEFT", 8, -5); f.text:SetPoint("BOTTOMRIGHT", -8, 5)
  if f.text.SetJustifyV then f.text:SetJustifyV("TOP") end
  if f.text.SetWordWrap then f.text:SetWordWrap(false) end   -- a too-long line ends in "..." instead of wrapping
  if f.text.SetMaxLines then f.text:SetMaxLines(3) end
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
  local short
  if win:IsShown() then short = self:DungeonBannerShort() end
  local f = self.dungeonBanner
  if not short then
    if f then f:Hide() end
    return
  end
  f = f or createBanner(win)
  self.dungeonBanner = f
  local shown = {}
  for i = 1, 3 do if short[i] then shown[#shown + 1] = short[i] end end
  f.text:SetText(table.concat(shown, "\n"))
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
