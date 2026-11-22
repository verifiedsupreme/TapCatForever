-- TapCatForever: Gear page (your real WoW items for the current class)
local ADDON, TCF = ...
local floor, max, min = math.floor, math.max, math.min

local SHORT = { str = "Str", agi = "Agi", sta = "Sta", int = "Int", spi = "Spi", ap = "AP", rap = "Ranged AP", sp = "SP", heal = "Healing", critr = "Crit", hitr = "Hit", def = "Def" }
function TCF.GearSummary(it)
  local st = TCF.GearStats(it)
  local parts = {}
  if st.dps then parts[#parts + 1] = string.format("%.1f DPS", st.dps) end
  if st.arm then parts[#parts + 1] = st.arm .. " Armor" end
  for _, k in ipairs({ "str", "agi", "sta", "int", "spi", "ap", "rap", "sp", "heal", "critr", "hitr", "def" }) do
    if st[k] then parts[#parts + 1] = "+" .. st[k] .. " " .. SHORT[k] end
  end
  return table.concat(parts, "  ")
end

-- Power change if this item were equipped with the Equip button (same slot choice)
function TCF:GearUpgrade(it, class)
  class = class or self.db.class
  if not self:GearUsable(it, class) then return nil end
  local base = self:CombatStats(class).power
  return self:CombatStats(class, it, self:BestGearSlot(it, class)).power - base
end

-- Every gear tooltip ends with a comparison against what the cat is wearing in that slot
-- (both slots for rings, trinkets and one-handers), as a Power change.
function TCF:GearCompareLines(tt, it, class)
  class = class or self.db.class
  if not self:GearUsable(it, class) then return end
  local eq = self:GearEquipped(class)
  local base = self:CombatStats(class).power
  local lines = {}
  for _, slot in ipairs(self:GearTargetSlots(it, class)) do
    if eq[slot] ~= it.id then
      local d = self:CombatStats(class, it, slot).power - base
      local cur = eq[slot] and TCF.GEAR[eq[slot]]
      local slotName = TCF.GEAR_SLOT_BY_KEY[slot] and TCF.GEAR_SLOT_BY_KEY[slot].name or slot
      local what = cur and ("|c" .. TCF.RARITY[cur.q].hex .. cur.name .. "|r") or ("|cff888888empty " .. slotName .. " slot|r")
      local diff = d > 0 and ("|cff20ff20+" .. d .. " Power|r") or d < 0 and ("|cffff4040" .. d .. " Power|r") or "|cffaaaaaano change|r"
      lines[#lines + 1] = { "Instead of " .. what, diff }
    end
  end
  if #lines == 0 then
    tt:AddLine(" "); tt:AddLine("Your cat is wearing this.", 0.3, 1, 0.3)
    return
  end
  tt:AddLine(" ")
  tt:AddLine("Compared with what you're wearing:", 1, 0.82, 0)
  for _, l in ipairs(lines) do tt:AddDoubleLine(l[1], l[2], 1, 1, 1, 1, 1, 1) end
  if it.req > self:CD(class).level then
    tt:AddLine("You can equip it at class level " .. it.req .. ".", 1, 0.5, 0.25)
  end
end
-- Side-by-side comparison, like WoW's own: next to the main tooltip, a second tooltip shows
-- the item your cat wears in that slot (both for rings, trinkets and one-handers) with its
-- stats, so you can read them against each other.
local compareTips = {}
local function compareTip(i)
  local t = compareTips[i]
  if not t then
    t = CreateFrame("GameTooltip", "TapCatForeverCompareTip" .. i, UIParent, "GameTooltipTemplate")
    if t.SetFrameStrata then t:SetFrameStrata("TOOLTIP") end
    compareTips[i] = t
  end
  return t
end
local function hideCompare() for _, t in pairs(compareTips) do t:Hide() end end
if GameTooltip and GameTooltip.HookScript then
  pcall(GameTooltip.HookScript, GameTooltip, "OnHide", hideCompare)
  pcall(GameTooltip.HookScript, GameTooltip, "OnTooltipCleared", hideCompare)
end

function TCF:ShowGearCompare(tt, it, class, baseTooltip)
  hideCompare()
  if tt ~= GameTooltip then return end
  class = class or self.db.class
  if not self:GearUsable(it, class) then return end
  local eq = self:GearEquipped(class)
  local worn, seen = {}, {}
  for _, slot in ipairs(self:GearTargetSlots(it, class)) do
    local id = eq[slot]
    if id and id ~= it.id and not seen[id] and TCF.GEAR[id] then seen[id] = true; worn[#worn + 1] = TCF.GEAR[id] end
  end
  -- a two-hander replaces the main hand and the off hand: show both
  if it.slot == "2H" and eq.OFFHAND and not seen[eq.OFFHAND] and TCF.GEAR[eq.OFFHAND] then worn[#worn + 1] = TCF.GEAR[eq.OFFHAND] end
  if #worn == 0 then return end
  -- put the comparison on the side of the screen with more room
  local owner = tt.GetOwner and tt:GetOwner()
  local ox = owner and owner.GetCenter and owner:GetCenter()
  local sw = UIParent.GetWidth and UIParent:GetWidth()
  local onLeft = not (type(ox) == "number" and type(sw) == "number" and ox < sw * 0.4)
  local prev = tt
  for i = 1, math.min(2, #worn) do
    local c = compareTip(i)
    c:SetOwner(tt, "ANCHOR_NONE")
    c:ClearAllPoints()
    if onLeft then c:SetPoint("TOPRIGHT", prev, "TOPLEFT", -4, 0) else c:SetPoint("TOPLEFT", prev, "TOPRIGHT", 4, 0) end
    c:AddLine("Your cat is wearing", 0.6, 0.6, 0.6)
    baseTooltip(self, c, worn[i], class)
    c:Show()
    prev = c
  end
end

do
  local base = TCF.GearTooltip
  function TCF:GearTooltip(tt, it, class)
    base(self, tt, it, class)
    self:GearCompareLines(tt, it, class)
    if it then self:ShowGearCompare(tt, it, class, base) end
  end
end

-- Hover preview: the cat on the left tries the item on
function TCF.UI.ShowTryOn(win, it)
  if not win.preview then return end
  local out = TCF:GetAppearance(nil, nil, it)
  -- a chosen cosmetic would hide the previewed piece: show the item in the slots it changes
  local with, without = TCF:GearAppearance(nil, it), TCF:GearAppearance()
  for k, v in pairs(with) do
    if not without[k] or without[k].id ~= v.id then out[k] = v end
  end
  win.preview:ApplyAppearance(out)
end

function TCF.UI.HideTryOn(win)
  if win.preview then win.preview:ApplyAppearance(TCF:GetAppearance()) end
end

TCF.UI.Builders.gear = function(page, win)
  local U = TCF.UI
  local Text, Button, Tip, Panel = U.Text, U.Button, U.Tip, U.Panel
  local title = Text(page, "GameFontNormalLarge", nil, "LEFT"); title:SetPoint("TOPLEFT", 16, -14)
  local hint = Text(page, "GameFontDisableSmall", "Click a slot around your cat to filter. Real WoW items with real stats.", "LEFT")
  hint:SetPoint("TOPLEFT", 16, -34)
  win.gearUsable = true
  local allBtn = Button(page, "All slots", 80, 22, function() win.gearSlot = nil; win.gearPage = 1; win:Refresh() end)
  allBtn:SetPoint("TOPRIGHT", -14, -12)
  local usable = CreateFrame("CheckButton", nil, page, "UICheckButtonTemplate")
  usable:SetSize(24, 24); usable:SetPoint("TOPRIGHT", -200, -10); usable:SetChecked(true)
  local ut = Text(page, "GameFontHighlightSmall", "Usable only"); ut:SetPoint("LEFT", usable, "RIGHT", 0, 1)
  usable:SetScript("OnClick", function(s) win.gearUsable = s:GetChecked() and true or false; win.gearPage = 1; win:Refresh() end)

  local ROWS = 8
  local rows = {}
  for i = 1, ROWS do
    local r = Panel(page, 528, 44, 0.85); r:SetPoint("TOP", 0, -54 - (i - 1) * 47)
    r.btn = U.GearButton(r, 36); r.btn:SetPoint("LEFT", 5, 0)
    r.name = Text(r, "GameFontNormal", nil, "LEFT"); r.name:SetPoint("TOPLEFT", r.btn, "TOPRIGHT", 8, -1); r.name:SetWidth(300)
    -- one line only (long random-bonus names would run into the info line); the Equipped /
    -- Not ideal tags sit in their own text at the right so they are never cut off
    r.name:SetWordWrap(false)
    r.tag = Text(r, "GameFontNormalSmall", nil, "RIGHT"); r.tag:SetPoint("TOPRIGHT", r, "TOPLEFT", 380, -6)
    r.tag:SetWordWrap(false)
    r.info = Text(r, "GameFontHighlightSmall", nil, "LEFT"); r.info:SetPoint("BOTTOMLEFT", r.btn, "BOTTOMRIGHT", 8, 1); r.info:SetWidth(330)
    r.delta = Text(r, "GameFontNormal", nil, "RIGHT"); r.delta:SetPoint("RIGHT", -148, 0)
    r.equip = Button(r, "Equip", 58, 20, function() if r.item then TCF:EquipGear(r.item.id) end end)
    r.equip:SetPoint("RIGHT", -84, 0)
    r.sell = Button(r, "Sell", 76, 20, function()
      local it = r.item
      if not it then return end
      -- gear is scarce: ask before selling the only copy of a rare or better item
      if it.q >= 3 and (TCF:Bag()[it.id] or 0) <= 1 then
        StaticPopupDialogs.TAPCATFOREVER_SELL_LAST = {
          text = "Sell your only %s for %s?\n\nThis can't be undone.",
          button1 = "Sell", button2 = CANCEL or "Cancel",
          OnAccept = function(_, id) if id then TCF:SellGear(id) end end,
          timeout = 0, whileDead = true, hideOnEscape = true, showAlert = true, preferredIndex = 3,
        }
        StaticPopup_Show("TAPCATFOREVER_SELL_LAST", TCF.GearLink(it), TCF:GearSellText(it), it.id)
      else
        TCF:SellGear(it.id)
      end
    end)
    r.sell:SetPoint("RIGHT", -6, 0)
    Tip(r.sell, function(tt)
      if not r.item then return end
      tt:AddLine("Sell", 1, 0.82, 0)
      tt:AddLine(string.format("Sells one copy for %s. Copies your cat is wearing are kept. You'll be asked first before selling your only copy of a rare or epic item.", TCF:GearSellText(r.item)), 1, 1, 1, true)
      if r.item.crafted then
        tt:AddLine("Crafted gear sells for Trade Gold (half the value of its materials), not TapCoins.", 0.7, 0.7, 0.7, true)
      end
    end)
    local function enter(self)
      if not r.item then return end
      TCF.UI.ShowTryOn(win, r.item)
      GameTooltip:SetOwner(self, "ANCHOR_RIGHT"); TCF:GearTooltip(GameTooltip, r.item)
      GameTooltip:AddLine("Sells for " .. TCF:GearSellText(r.item) .. " (worn copies are kept).", 0.7, 0.7, 0.7)
      GameTooltip:Show()
    end
    local function leave() GameTooltip:Hide(); TCF.UI.HideTryOn(win) end
    r.btn:SetScript("OnEnter", enter); r.btn:SetScript("OnLeave", leave)
    r:SetScript("OnEnter", enter); r:SetScript("OnLeave", leave)
    rows[i] = r
  end
  local pageText = Text(page, "GameFontHighlightSmall"); pageText:SetPoint("BOTTOM", 0, 14)
  local prev = Button(page, "<", 28, 22, function() win.gearPage = max(1, (win.gearPage or 1) - 1); win:Refresh() end)
  prev:SetPoint("RIGHT", pageText, "LEFT", -10, 0)
  local nextB = Button(page, ">", 28, 22, function() win.gearPage = (win.gearPage or 1) + 1; win:Refresh() end)
  nextB:SetPoint("LEFT", pageText, "RIGHT", 10, 0)
  -- "12 TapCoins", "40 Trade Gold" or "12 TapCoins and 40 Trade Gold"
  local function junkValue(coins, gold)
    local parts = {}
    if coins > 0 or gold <= 0 then parts[#parts + 1] = TCF.Commas(coins) .. " TapCoins" end
    if gold > 0 then parts[#parts + 1] = TCF.Commas(gold) .. " Trade Gold" end
    return table.concat(parts, " and ")
  end
  local sellAll = Button(page, "Sell junk", 100, 22, function()
    local _, n, coins, gold = TCF:JunkGear()
    if n == 0 then TCF:Print("No junk to sell right now.", true); return end
    StaticPopupDialogs.TAPCATFOREVER_SELL_JUNK = {
      text = "Sell %s of junk for %s?\n\nJunk is gear that would lower your Power, extra copies you can't wear, and gear your class can't use. Better items are kept, even ones you're not high enough level for yet.",
      button1 = "Sell", button2 = CANCEL or "Cancel",
      OnAccept = function() TCF:SellJunk() end,
      timeout = 0, whileDead = true, hideOnEscape = true, showAlert = true, preferredIndex = 3,
    }
    StaticPopup_Show("TAPCATFOREVER_SELL_JUNK", n == 1 and "1 item" or (n .. " items"), junkValue(coins, gold or 0))
  end)
  sellAll:SetPoint("BOTTOMLEFT", 12, 10)
  Tip(sellAll, function(tt)
    local _, n, coins, gold = TCF:JunkGear()
    tt:AddLine("Sell junk", 1, 0.82, 0)
    tt:AddLine("Sells gear that would lower your cat's Power, extra copies beyond what your cat can wear at once, and gear your class can't use. Worn gear and upgrades (even ones you need a higher level for) are kept. You'll be asked to confirm.", 1, 1, 1, true)
    tt:AddLine("Crafted gear sells for Trade Gold instead of TapCoins.", 1, 1, 1, true)
    tt:AddLine(string.format("Right now: %d items for %s.", n, junkValue(coins, gold or 0)), 0.7, 0.7, 0.7)
  end)
  page:EnableMouseWheel(true)
  page:SetScript("OnMouseWheel", function(_, d) win.gearPage = max(1, (win.gearPage or 1) - d); win:Refresh() end)

  local function matchesSlot(it, slotKey, class)
    for _, s in ipairs(TCF:GearTargetSlots(it, class)) do if s == slotKey then return true end end
    return false
  end

  return function(full)
    if not full then return end
    local class = TCF.db.class
    local slot = win.gearSlot
    title:SetText(slot and (TCF.GEAR_SLOT_BY_KEY[slot].name .. " gear") or "All gear")
    local list = {}
    local eq = TCF:GearEquipped(class)
    for id, n in pairs(TCF:Bag()) do
      local it = TCF.GEAR[id]
      if it and n > 0 and (not slot or matchesSlot(it, slot, class)) and (not win.gearUsable or TCF:GearUsable(it, class)) then
        list[#list + 1] = it
      end
    end
    table.sort(list, function(a, b)
      if a.ilvl ~= b.ilvl then return a.ilvl > b.ilvl end
      if a.q ~= b.q then return a.q > b.q end
      return a.name < b.name
    end)
    local pagesN = max(1, math.ceil(#list / ROWS))
    win.gearPage = min(max(1, win.gearPage or 1), pagesN)
    local level = TCF:CD(class).level
    for i, r in ipairs(rows) do
      local it = list[(win.gearPage - 1) * ROWS + i]
      r.item = it
      if it then
        r:Show()
        r.btn:SetGear(it)
        local n = TCF:Bag()[it.id]
        r.btn.count:SetText(n > 1 and n or "")
        local worn = TCF.GearEquippedCount(eq, it.id)
        -- a second ring/trinket/one-hander can be worn too, if you own another copy
        local canWearMore = worn == 0 or (worn < n and #TCF:GearTargetSlots(it, class) > 1)
        local col = TCF.RARITY[it.q]
        local notIdeal = not TCF:GearSuits(it, class) and TCF:GearUsable(it, class)
        local tag = (worn > 0 and "|cff20ff20Equipped|r" or "")
          .. (notIdeal and ((worn > 0 and "  " or "") .. "|cffff9933Not ideal|r") or "")
        r.tag:SetText(tag)
        r.name:SetWidth(330 - (tag ~= "" and ((r.tag:GetStringWidth() or 90) + 8) or 0))
        r.name:SetText("|c" .. col.hex .. it.name .. "|r")
        r.info:SetText(string.format("|cffffd100%d|r  %s %s  |cff999999%s|r", it.ilvl, TCF.ITEM_TYPE_NAMES[it.sub] or "",
          TCF.ITEM_SLOT_NAMES[it.slot] or "", TCF.GearSummary(it)))
        local d = TCF:GearUpgrade(it)
        if d and canWearMore then
          r.delta:SetText(d > 0 and ("|cff20ff20+" .. d .. "|r") or d < 0 and ("|cffff4040" .. d .. "|r") or "|cff999999=|r")
        else r.delta:SetText("") end
        local can = TCF:CanEquipGear(it, class)
        r.equip:SetEnabled(can and canWearMore)
        r.equip:SetText(it.req > level and ("Lv " .. it.req) or "Equip")
        local spare = n - worn
        local value, currency = TCF:GearSellValue(it)
        r.sell:SetText("Sell " .. ((currency == "gold" and TCF.GoldStr) and TCF.GoldStr(value, 12) or U.coinStr(value, 12)))
        r.sell:SetEnabled(spare > 0)
      else
        r:Hide()
      end
    end
    pageText:SetText(#list > 0 and string.format("Page %d / %d  (%d items)", win.gearPage, pagesN, #list)
      or "|cff888888No gear here yet. Enemies and bosses in Adventure, chests and expeditions drop real items, and your crafting profession makes them.|r")
    prev:SetEnabled(win.gearPage > 1); nextB:SetEnabled(win.gearPage < pagesN)
  end
end
