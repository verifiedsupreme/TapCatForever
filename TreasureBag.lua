-- TapCatForever: the Treasure Bag (1.5.4). Every class's cat has its own bag of unopened chests,
-- each stamped with the level of the cat that earned it (Core.lua: TCF:AwardChest, TCF:ChestStamps).
-- One row per kind of chest and level ("Lv 20", the count on the icon), five rows a page. TCF:CreateBag and
-- TCF:OpenAllChests live here (UI.lua keeps TCF:ToggleBag).
local ADDON, TCF = ...
local floor, min, max = math.floor, math.min, math.max

local PER_PAGE = 5

-- every (kind, level) the cat holds, in chest order then highest level first
function TCF:BagEntries(class)
  local out = {}
  for _, ch in ipairs(TCF.CHESTS) do
    for _, s in ipairs(self:ChestStamps(ch.key, class or self.db.class)) do
      out[#out + 1] = { chest = ch, level = s.level, n = s.n }
    end
  end
  return out
end

-- { [chest key] = count } for one cat's bag (default: the cat you are playing), as a plain table.
-- db.keys is a stand-in whose counts are read through a metatable, so pairs(db.keys) sees
-- nothing in Lua 5.1: code that sums every chest uses this or TCF:ChestCount() instead.
function TCF:ChestCounts(class)
  local out = {}
  for _, ch in ipairs(TCF.CHESTS) do
    local n = self:ChestsOf(ch.key, class or self.db.class)
    if n > 0 then out[ch.key] = n end
  end
  return out
end

-- "Mage 2, Rogue 1": chests waiting in the bags of the cats you aren't playing
function TCF:OtherCatsChestText()
  local parts = {}
  for _, cl in ipairs(TCF.CLASSES) do
    if cl.key ~= self.db.class and self.db.classData[cl.key] then
      local n = self:ChestCount(cl.key)
      if n > 0 then parts[#parts + 1] = cl.name .. " " .. n end
    end
  end
  return table.concat(parts, ", ")
end

function TCF:CreateBag()
  local U = TCF.UI
  local Text, Button, Panel, Tip = U.Text, U.Button, U.Panel, U.Tip
  local f = CreateFrame("Frame", "TapCatForeverBag", UIParent, U.BT)
  -- five rows 56 tall every 62 from 44 down, a line about the other cats, then the buttons
  f:SetSize(400, 106 + 62 * PER_PAGE); f:SetPoint("CENTER", 310, 0)
  f:SetFrameStrata("DIALOG"); f:SetToplevel(true)
  f:EnableMouse(true); f:SetMovable(true); f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving); f:SetScript("OnDragStop", f.StopMovingOrSizing)
  if f.SetBackdrop then f:SetBackdrop(U.BACKDROP_DIALOG) end
  f:Hide()
  tinsert(UISpecialFrames, "TapCatForeverBag")
  f.title = Text(f, "GameFontNormalLarge", "Treasure Bag"); f.title:SetPoint("TOP", 0, -18)
  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton"); close:SetPoint("TOPRIGHT", -6, -6)
  local empty = Text(f, "GameFontDisable", "No unopened chests.\nEarn them from quests, dungeons,\nraids and class levels.")
  empty:SetPoint("CENTER", 0, -10)
  f.page = 1
  f.rows = {}
  for i = 1, PER_PAGE do
    local r = Panel(f, 360, 56, 0.9); r:SetPoint("TOP", 0, -44 - (i - 1) * 62)
    r.icon = r:CreateTexture(nil, "ARTWORK"); r.icon:SetSize(40, 40); r.icon:SetPoint("LEFT", 8, 0)
    r.count = Text(r, "NumberFontNormalLarge", nil, "RIGHT"); r.count:SetPoint("BOTTOMRIGHT", r.icon, "BOTTOMRIGHT", 2, -2)
    -- text stops 8px short of the Open button (row x 56 to 252; Open starts at 256)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("TOPLEFT", r.icon, "TOPRIGHT", 8, -2); r.name:SetWidth(192)
    r.desc = Text(r, "GameFontDisableSmall", nil, "LEFT"); r.desc:SetPoint("BOTTOMLEFT", r.icon, "BOTTOMRIGHT", 8, 2); r.desc:SetWidth(192)
    if r.name.SetWordWrap then r.name:SetWordWrap(false); r.desc:SetWordWrap(false) end
    r.all = Button(r, "All", 40, 22, function() if r.chest then TCF:OpenAllChests(r.chest.key) end end); r.all:SetPoint("RIGHT", -8, 0)
    Tip(r.all, function(tt)
      local ch = r.chest
      if not ch then return end
      tt:AddLine("Open all " .. (ch.plural or ch.name .. "s"), 1, 0.82, 0)
      tt:AddLine("Every level of them in this cat's bag.", 1, 1, 1, true)
    end)
    r.open = Button(r, "Open", 52, 22, function() if r.chest then TCF:OpenChest(r.chest.key, true, r.level) end end)
    r.open:SetPoint("RIGHT", r.all, "LEFT", -4, 0)
    Tip(r.open, function(tt)
      if not r.chest then return end
      tt:AddLine("Open one", 1, 0.82, 0)
      tt:AddLine("A level " .. (r.level or 1) .. " " .. r.chest.name .. ".", 1, 1, 1, true)
    end)
    Tip(r, function(tt)
      if not r.chest then return end
      TCF:ChestOddsTooltip(tt, r.chest, nil, r.level)
      local from = TCF.CHEST_BAG_TEXT and TCF.CHEST_BAG_TEXT[r.chest.key]
      if from then tt:AddLine(" "); tt:AddLine("Comes from: " .. from, 0.7, 0.7, 0.7, true) end
    end)
    r:Hide()
    f.rows[i] = r
  end
  f.others = Text(f, "GameFontDisableSmall", nil, "CENTER"); f.others:SetPoint("BOTTOM", 0, 42); f.others:SetWidth(360)
  if f.others.SetWordWrap then f.others:SetWordWrap(false) end
  local openAll = Button(f, "Open everything", 140, 22, function() TCF:OpenAllChests() end)
  openAll:SetPoint("BOTTOM", 0, 14)
  f.prev = Button(f, "<", 24, 22, function() f.page = f.page - 1; f:Refresh() end); f.prev:SetPoint("BOTTOMLEFT", 18, 14)
  f.pageText = Text(f, "GameFontHighlightSmall", nil, "CENTER"); f.pageText:SetPoint("LEFT", f.prev, "RIGHT", 2, 0); f.pageText:SetWidth(40)
  f.next = Button(f, ">", 24, 22, function() f.page = f.page + 1; f:Refresh() end); f.next:SetPoint("LEFT", f.pageText, "RIGHT", 2, 0)
  if f.EnableMouseWheel then f:EnableMouseWheel(true) end
  f:SetScript("OnMouseWheel", function(s, delta) s.page = s.page - (delta > 0 and 1 or -1); s:Refresh() end)

  function f:Refresh()
    local class = TCF.db.class
    local cl = TCF.CLASS_BY_KEY[class]
    local cd = TCF:CD()
    self.title:SetText((cl and (cl.name .. " cat's ") or "") .. "Treasure Bag")
    local list = TCF:BagEntries(class)
    local pages = max(1, math.ceil(#list / PER_PAGE))
    self.page = max(1, min(pages, self.page or 1))
    local first = (self.page - 1) * PER_PAGE
    local y = -44
    for i, r in ipairs(self.rows) do
      local e = list[first + i]
      if e then
        local ch = e.chest
        r.chest, r.level = ch, e.level
        r.icon:SetTexture(TCF.Icon(ch.icon))
        r.count:SetText(e.n > 1 and e.n or "")
        r.name:SetText(ch.name)
        -- the level stamp (grey once the cat has outgrown it); the count is on the icon and where
        -- the chest comes from is in the row's tooltip
        local far = cd and e.level < (cd.level or 1) - 10
        r.desc:SetText(string.format("|cff%sLv %d|r", far and "999999" or "ffd100", e.level))
        r.open:SetEnabled(true); r.all:SetEnabled(TCF:ChestsOf(ch.key, class) > 1)
        r:ClearAllPoints(); r:SetPoint("TOP", 0, y); y = y - 62
        r:Show()
      else
        r:Hide()   -- (keeps its last chest for a tooltip that is still up)
      end
    end
    local any = #list > 0
    empty:SetShown(not any)
    openAll:SetShown(any)
    local paged = pages > 1
    self.prev:SetShown(paged); self.next:SetShown(paged); self.pageText:SetShown(paged)
    self.prev:SetEnabled(self.page > 1); self.next:SetEnabled(self.page < pages)
    self.pageText:SetText(self.page .. "/" .. pages)
    local others = TCF:OtherCatsChestText()
    self.others:SetText(others ~= "" and ("Chests in your other cats' bags: " .. others .. ". Play that class to open them.") or "")
  end
  f:SetScript("OnShow", function(s) s:Refresh() end)
  self.bag = f
  return f
end

-- Open every chest of one kind (or every chest) in this cat's bag at once; the loot window queues
-- the results. level: only the chests of that level stamp. Every grant normally refreshes the
-- whole UI, plays a sound and prints a line; for hundreds of chests in one click that freezes the
-- client, so those are muted for the batch and done once after.
function TCF:OpenAllChests(key, level)
  local refreshAll, playSound, print = self.RefreshAll, self.PlaySound, self.Print
  local opened, lines, best = 0, {}, nil
  local RANK = { loot = 1, rare = 2, legendary = 3 }
  self.RefreshAll = function() end
  -- muted for the batch, but remember the best loot sound any drop asked for
  self.PlaySound = function(_, kind)
    if RANK[kind] and (not best or RANK[kind] > RANK[best]) then best = kind end
  end
  self.Print = function(s, msg, force)
    if force then return print(s, msg, force) end
    lines[#lines + 1] = msg
  end
  self.openingAll = true
  local ok, err = pcall(function()
    for _, ch in ipairs(TCF.CHESTS) do
      if not key or ch.key == key then
        for _, s in ipairs(self:ChestStamps(ch.key, self.db.class)) do
          if not level or s.level == level then
            for _ = 1, min(s.n, 200) do
              local before = self:ChestsOf(ch.key, self.db.class)
              self:OpenChest(ch.key, true, s.level)
              if self:ChestsOf(ch.key, self.db.class) >= before then return end
              opened = opened + 1
            end
          end
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
  self:PlaySound((best == "legendary" or best == "rare") and best or "loot")
  self:RefreshAll()
end

-- Expedition chests go to a cat that went: the one you are playing if it was in the party,
-- otherwise the party's first cat (or the cat you are playing when the party is unknown).
if TCF.ClaimExpedition then
  local claim = TCF.ClaimExpedition
  function TCF:ClaimExpedition(index, ...)
    local st = self.db and self.db.expeditions
    local ex = st and type(st.active) == "table" and st.active[index]
    local owner
    if type(ex) == "table" and type(ex.members) == "table" then
      for _, m in ipairs(ex.members) do
        if m == self.db.class then owner = m end
      end
      local m1 = ex.members[1]
      if not owner and type(m1) == "string" and self.db.classData[m1] then owner = m1 end
    end
    -- only the expedition's own chests (source: its name, see TCF:AwardChest); a level-up or an
    -- achievement during the claim still goes to its own cat
    local e = type(ex) == "table" and TCF.EXPEDITION_BY_KEY and TCF.EXPEDITION_BY_KEY[ex.key]
    local prev = self.claimChests
    self.claimChests = (owner and e) and { owner = owner, source = e.name } or nil
    local ok, a, b, c = pcall(claim, self, index, ...)
    self.claimChests = prev
    if not ok then error(a, 0) end
    return a, b, c
  end
end
