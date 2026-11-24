-- TapCatForever: the Shop tab. Prices, stock and buying are in Core.lua; this file draws them.
--   A row of sub-tabs at the top: Featured (the Heroic Cache, the Daily Wares and three offers:
--   the Skin of the Day, the racial heritage piece and the companion cats), Cat Skins (every shop
--   skin in a grid, with filters) and Chests (the three chests you can buy and the Treasure Bag).
--   Companions opens the companion window (UI_Companions.lua) instead of a view.
--   No animation groups: the glows pulse from an OnUpdate on the view they are in, which only
--   runs while that view is on screen.
local ADDON, TCF = ...
local floor, min, max, sin, pi = math.floor, math.min, math.max, math.sin, math.pi

local GOLD = { 1, 0.82, 0.2 }
local EPIC = { 0.64, 0.21, 0.93 }
local LOCK_TEX = "Interface\\Buttons\\LockButton-Locked-Up"
local GLOW_TEX = "Interface\\Buttons\\CheckButtonHilight"
local SKINS_PER_PAGE = 15
-- TCF.SkinSourceTag's short words (Compendium.lua), spelled out on the Cat Skins buttons
local SOURCE_WORD = { drop = "Boss drop", ["ach."] = "Achievement", ["exped."] = "Expedition", craft = "Crafted",
  chest = "Chest find", quest = "Quest", dungeon = "Dungeon", raid = "Raid" }

local function rarityColor(q)
  local r = TCF.RARITY[q] or TCF.RARITY[1]
  return r.color, r.hex
end

TCF.UI.Builders.shop = function(page, win)
  local U = TCF.UI
  local Text, Button, Tip, Panel, ItemCell, coinStr = U.Text, U.Button, U.Tip, U.Panel, U.ItemCell, U.coinStr
  local db = function() return TCF.db end

  -- a solid colour texture
  local function Fill(parent, r, g, b, a, layer, sub)
    local t = parent:CreateTexture(nil, layer or "BACKGROUND", nil, sub or 1)
    t:SetColorTexture(r, g, b, a or 1)
    return t
  end
  -- the panel's inside, tinted (inset 4 keeps the border clear)
  local function Tint(parent, r, g, b, a)
    local t = Fill(parent, r, g, b, a, "BACKGROUND", 1)
    t:SetPoint("TOPLEFT", 4, -4); t:SetPoint("BOTTOMRIGHT", -4, 4)
    return t
  end
  local function Border(f, c, a)
    if f.SetBackdropBorderColor then f:SetBackdropBorderColor(c[1], c[2], c[3], a or 1) end
  end
  -- a soft glow behind something (pulsed by its view, see Pulse)
  local function Glow(parent, anchor, size, c)
    local g = parent:CreateTexture(nil, "BACKGROUND", nil, 3)
    g:SetTexture(GLOW_TEX); g:SetBlendMode("ADD")
    g:SetSize(size, size); g:SetPoint("CENTER", anchor, "CENTER")
    if c then g:SetVertexColor(c[1], c[2], c[3]) end
    return g
  end
  -- a small "-20%" ribbon
  local function Badge(parent)
    local b = CreateFrame("Frame", nil, parent)
    b:SetSize(36, 15)
    if b.SetFrameLevel and parent.GetFrameLevel and parent:GetFrameLevel() then b:SetFrameLevel(parent:GetFrameLevel() + 5) end
    local bg = Fill(b, 0.95, 0.70, 0.10, 1, "ARTWORK", 0); bg:SetAllPoints()
    local hi = Fill(b, 1, 0.92, 0.55, 1, "ARTWORK", 1); hi:SetPoint("TOPLEFT"); hi:SetPoint("TOPRIGHT"); hi:SetHeight(4)
    b.text = Text(b, "GameFontNormalSmall", "-" .. floor(TCF.FEATURED_SKIN_DISCOUNT * 100 + 0.5) .. "%")
    b.text:SetPoint("CENTER", 0, 0); b.text:SetTextColor(0.18, 0.08, 0.02)
    return b
  end

  local function setCoinsButton(b, price, size)
    b:SetText(coinStr(price, size or 12))
    b:SetEnabled((db().coins or 0) >= price)
  end
  -- the item tooltip with the try-on line, as on the Appearance tab
  local function itemEnter(s)
    if not s.item then return end
    GameTooltip:SetOwner(s, "ANCHOR_RIGHT"); TCF:ItemTooltip(GameTooltip, s.item)
    if s.extraTip then s.extraTip(GameTooltip, s.item) end
    if TCF:CanEquip(s.item) then TCF.UI.PreviewHint(GameTooltip, win, s.item) end
    GameTooltip:Show()
    if TCF:CanEquip(s.item) then TCF.UI.ShowTryOn(win, s.item) end
  end
  local function itemLeave() GameTooltip:Hide(); TCF.UI.HideTryOn(win) end
  local function tryOnCell(cell)
    cell:SetScript("OnEnter", itemEnter)
    cell:SetScript("OnLeave", itemLeave)
    cell:SetScript("OnClick", function(s)
      if s.item and TCF:CanEquip(s.item) and TCF.UI.PreviewClick(win, s.item) then itemEnter(s) end
    end)
  end

  ------------------------------------------------------------------ header
  local views, navBtns = {}, {}
  win.shopView = win.shopView or "featured"
  local NAV = {
    { key = "featured", label = "Featured" },
    { key = "skins", label = "Cat Skins" },
    { key = "chests", label = "Chests" },
    { key = "companions", label = "Companions" },
  }
  local refresh  -- below
  for k, n in ipairs(NAV) do
    local b = Button(page, n.label, 104, 24, function()
      if n.key == "companions" then
        if TCF.ToggleCompanions then TCF:ToggleCompanions() end
      else
        win:SetShopView(n.key)
      end
      TCF:PlaySound("click")
    end)
    b:SetPoint("TOPLEFT", 14 + (k - 1) * 108, -12)
    b.under = Fill(b, GOLD[1], GOLD[2], GOLD[3], 0.9, "OVERLAY", 0)
    b.under:SetSize(96, 2); b.under:SetPoint("BOTTOM", 0, -3); b.under:Hide()
    b.key = n.key
    navBtns[k] = b
  end
  Tip(navBtns[1], function(tt)
    tt:AddLine("Featured", 1, 0.82, 0)
    tt:AddLine("The Heroic Cache, today's Daily Wares and offers.", 1, 1, 1, true)
  end)
  Tip(navBtns[2], function(tt)
    tt:AddLine("Cat Skins", 1, 0.82, 0)
    tt:AddLine("Every cat skin sold for TapCoins. The Skin of the Day costs less.", 1, 1, 1, true)
  end)
  Tip(navBtns[3], function(tt)
    tt:AddLine("Chests", 1, 0.82, 0)
    tt:AddLine("Buy and open chests, and see what each one holds.", 1, 1, 1, true)
  end)
  Tip(navBtns[4], function(tt)
    local owned, total = 0, #(TCF.COMPANIONS or {})
    for _, c in ipairs(TCF.COMPANIONS or {}) do if TCF:CompanionOwned(c.key) then owned = owned + 1 end end
    tt:AddLine("Companions", 1, 0.82, 0)
    tt:AddLine(string.format("Companion cats walk beside your cat. %d of %d owned.", owned, total), 1, 1, 1, true)
  end)
  local balance = Text(page, "GameFontNormalLarge", nil, "RIGHT")
  balance:SetPoint("TOPRIGHT", -16, -16); balance:SetWidth(100)
  local divider = Fill(page, 0.45, 0.40, 0.55, 0.6, "ARTWORK", 0)
  divider:SetSize(532, 1); divider:SetPoint("TOPLEFT", 14, -42)

  for _, key in ipairs({ "featured", "skins", "chests" }) do
    local v = CreateFrame("Frame", nil, page); v:SetAllPoints(); v:Hide()
    v.glows = {}
    v.t = 0
    -- the glows breathe: 0.4 to 0.9 over 1.6 s
    v:SetScript("OnUpdate", function(s, e)
      s.t = (s.t + (e or 0)) % 1.6
      local a = 0.65 + 0.25 * sin(s.t / 1.6 * 2 * pi)
      for _, g in ipairs(s.glows) do if g:IsShown() then g:SetAlpha(a) end end
    end)
    views[key] = v
  end
  local function Pulse(view, g) view.glows[#view.glows + 1] = g; g:SetAlpha(0.65); return g end

  -- the last chest you opened (Featured and Chests)
  local lastLoot = Text(page, "GameFontHighlight", nil, "LEFT"); lastLoot:SetPoint("BOTTOMLEFT", 16, 14); lastLoot:SetWidth(528)

  ------------------------------------------------------------------ odds (cached)
  local heroic = TCF.CHEST_BY_KEY and TCF.CHEST_BY_KEY.heroic
  local oddsCache = {}
  local function oddsFor(ch)
    local d = db()
    local key = ch.key .. ":" .. tostring(d.class) .. ":" .. TCF:ChestLevel() .. ":" .. tostring(d.stats and d.stats.chests) .. ":" .. #TCF:UnownedShopSkins()
    local c = oddsCache[ch.key]
    if not c or c.key ~= key then
      c = { key = key, rows = TCF:ChestOdds(ch) }
      oddsCache[ch.key] = c
    end
    return c.rows
  end

  ------------------------------------------------------------------ Featured
  local fv = views.featured
  -- the Heroic Cache banner
  local ban = Panel(fv, 532, 150, 0.95); ban:SetPoint("TOPLEFT", 14, -48)
  Border(ban, EPIC)
  Tint(ban, 0.16, 0.07, 0.24, 0.9)
  local banHi = Fill(ban, 0.55, 0.30, 0.85, 0.18, "BACKGROUND", 2)
  banHi:SetPoint("TOPLEFT", 4, -4); banHi:SetPoint("TOPRIGHT", -4, -4); banHi:SetHeight(46)
  local banIcon = ban:CreateTexture(nil, "ARTWORK"); banIcon:SetSize(64, 64); banIcon:SetPoint("TOPLEFT", 16, -18)
  if heroic then banIcon:SetTexture(TCF.Icon(heroic.icon)) end
  Pulse(fv, Glow(ban, banIcon, 92, { 0.85, 0.55, 1 }))
  local banName = Text(ban, "GameFontNormalLarge", heroic and heroic.name or "Heroic Cache", "LEFT")
  banName:SetPoint("TOPLEFT", 94, -14)
  local banTag = Text(ban, "GameFontHighlightSmall", "Rare and Epic gear for your level, a cosmetic, or a shop cat skin.", "LEFT")
  banTag:SetPoint("TOPLEFT", 94, -34); banTag:SetWidth(268); banTag:SetJustifyV("TOP")
  local chips = {}
  for i = 1, 4 do
    local c = Text(ban, "GameFontHighlightSmall", nil, "LEFT")
    c:SetPoint("TOPLEFT", 94 + ((i - 1) % 2) * 134, -62 - floor((i - 1) / 2) * 14); c:SetWidth(130)
    chips[i] = c
  end
  local prizeLabel = Text(ban, "GameFontDisableSmall", "Top prizes", "LEFT"); prizeLabel:SetPoint("TOPLEFT", 94, -94)
  local prizeCells = {}
  for i = 1, 6 do
    local b = TCF.UI.GearButton(ban, 30)
    b:SetPoint("TOPLEFT", 94 + (i - 1) * 34, -107)
    b.lock = b:CreateTexture(nil, "OVERLAY"); b.lock:SetSize(13, 13); b.lock:SetPoint("BOTTOMLEFT", 1, 1); b.lock:SetTexture(LOCK_TEX)
    b.lvl = Text(b, "NumberFontNormalSmall", nil, "RIGHT"); b.lvl:SetPoint("BOTTOMRIGHT", -2, 2)
    b:SetScript("OnEnter", function(s)
      if not s.item then return end
      GameTooltip:SetOwner(s, "ANCHOR_RIGHT"); TCF:GearTooltip(GameTooltip, s.item)
      if s.need then
        GameTooltip:AddLine(string.format("A Heroic Cache opened by a level-%d cat can hold this.", s.need), 1, 0.82, 0, true)
      else
        GameTooltip:AddLine("In this chest's prize pool.", 0.3, 1, 0.3, true)
      end
      GameTooltip:Show()
    end)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    prizeCells[i] = b
  end
  -- right column: a ribbon, the Bag and Open buttons
  local ribbon = Text(ban, "GameFontNormalSmall", "|cffd8a8ffBest chest in the Shop|r", "RIGHT")
  ribbon:SetPoint("TOPRIGHT", -16, -18); ribbon:SetWidth(150)
  local banBag = Button(ban, "Bag (0)", 150, 22, function() TCF:ToggleBag() end)
  banBag:SetPoint("BOTTOMRIGHT", -16, 56)
  local banOpen = Button(ban, "Open", 150, 32, function() if heroic then TCF:OpenChest(heroic.key) end end)
  banOpen:SetPoint("BOTTOMRIGHT", -16, 16)
  local function bagTip(tt)
    tt:AddLine("Your unopened chests (Treasure Bag)", 1, 0.82, 0)
    for _, line in ipairs(TCF.CHEST_SOURCES) do tt:AddLine(line, 1, 1, 1, true) end
  end
  Tip(banBag, bagTip)
  Tip(ban, function(tt) if heroic then TCF:ChestOddsTooltip(tt, heroic, true) end end)
  Tip(banOpen, function(tt) if heroic then TCF:ChestOddsTooltip(tt, heroic, true) end end)

  local prizeKey
  local function needFor(it, level, raid)
    if it.q == 5 and level < 60 then return 60 end
    if raid[it] and level < 55 then return 55 end
  end
  local function refreshPrizes()
    local level = TCF:ChestLevel()
    local key = tostring(db().class) .. ":" .. (level >= 60 and 2 or level >= 55 and 1 or 0)
    if key == prizeKey then return end
    prizeKey = key
    local legends = {}
    for _, it in ipairs(TCF.LegendariesFor and TCF:LegendariesFor() or {}) do legends[#legends + 1] = it end
    local raidList, raid = {}, {}
    for _, it in ipairs(TCF.RaidHoardPool and TCF:RaidHoardPool(nil, true) or {}) do
      if not raid[it] then raid[it] = true; raidList[#raidList + 1] = it end
    end
    local byIlvl = function(a, b)
      if (a.ilvl or 0) ~= (b.ilvl or 0) then return (a.ilvl or 0) > (b.ilvl or 0) end
      return (a.id or 0) < (b.id or 0)
    end
    table.sort(legends, byIlvl); table.sort(raidList, byIlvl)
    local list = {}
    for i = 1, min(2, #legends) do list[#list + 1] = legends[i] end
    for i = 1, #raidList do if #list >= 6 then break end; list[#list + 1] = raidList[i] end
    table.sort(list, byIlvl)
    for i, b in ipairs(prizeCells) do
      local it = list[i]
      if it then
        b:Show(); b:SetGear(it)
        local need = needFor(it, level, raid)
        b.need = need
        b.lock:SetShown(need ~= nil)
        b.lvl:SetText(need and tostring(need) or "")
        b.icon:SetVertexColor(need and 0.75 or 1, need and 0.75 or 1, need and 0.75 or 1)
      else
        b:Hide(); b.item = nil
      end
    end
    prizeLabel:SetShown(#list > 0)
  end

  local function refreshChips()
    if not heroic then return end
    local level = TCF:ChestLevel()
    local by = {}
    for _, o in ipairs(oddsFor(heroic)) do by[o[1]] = o end
    local function chip(label, row, hex)
      return row and string.format("|c%s%s|r  %s", hex or row[3], label, TCF.OddsText(row[2])) or nil
    end
    local list = {}
    local function add(s) if s then list[#list + 1] = s end end
    add(chip("Rare gear", by["Rare gear"]))
    add(chip("Epic gear", by["Epic gear"]))
    if by["Legendary gear"] then add(chip("Legendary", by["Legendary gear"]))
    elseif (heroic.legendary or 0) > 0 and level < 60 then add("|cff888888Legendary: level 60|r") end
    add(chip("Cat skin", by["Cat skin from the shop"]))
    add(chip("Cosmetic", by["Cosmetic"]))
    for i, c in ipairs(chips) do c:SetText(list[i] or "") end
  end

  -- Daily Wares
  local waresTitle = Text(fv, "GameFontNormal", "Daily Wares", "LEFT"); waresTitle:SetPoint("TOPLEFT", 16, -210)
  local resetText = Text(fv, "GameFontDisableSmall", nil, "LEFT"); resetText:SetPoint("LEFT", waresTitle, "RIGHT", 8, 0)
  local reroll = Button(fv, "New Stock", 140, 20, function()
    if TCF:RerollShop() then TCF:PlaySound("buy") end
  end)
  reroll:SetPoint("TOPRIGHT", -14, -206)
  Tip(reroll, function(tt)
    tt:AddLine("Refresh the daily wares", 1, 0.82, 0)
    tt:AddLine("The price doubles with each refresh, and resets at midnight.", 1, 1, 1, true)
  end)
  local cards = {}
  for i = 1, 3 do
    local c = Panel(fv, 172, 112, 0.92)
    c:SetPoint("TOPLEFT", 14 + (i - 1) * 180, -232)
    c.tint = Tint(c, 1, 1, 1, 0.06)
    c.band = Fill(c, 1, 1, 1, 1, "ARTWORK", 0)
    c.band:SetPoint("TOPLEFT", 4, -4); c.band:SetPoint("TOPRIGHT", -4, -4); c.band:SetHeight(3)
    c.cell = ItemCell(c, 56); c.cell:SetPoint("TOPLEFT", 8, -10)
    tryOnCell(c.cell)
    c.glow = Pulse(fv, Glow(c, c.cell, 72, { 1, 0.6, 0.15 }))
    c.name = Text(c, "GameFontNormalSmall", nil, "LEFT"); c.name:SetPoint("TOPLEFT", c.cell, "TOPRIGHT", 6, 0)
    c.name:SetWidth(96); c.name:SetHeight(40); c.name:SetJustifyV("TOP")
    c.cls = Text(c, "GameFontDisableSmall", nil, "LEFT"); c.cls:SetPoint("BOTTOMLEFT", c.cell, "BOTTOMRIGHT", 6, 2)
    c.price = Text(c, "GameFontHighlight", nil, "LEFT"); c.price:SetPoint("BOTTOMLEFT", 10, 12)
    c.buy = Button(c, "Buy", 64, 20, function() if c.id then TCF:BuyItem(c.id) end end)
    c.buy:SetPoint("BOTTOMRIGHT", -8, 8)
    cards[i] = c
  end

  -- three offers
  local function Tile(i)
    local t = Panel(fv, 172, 90, 0.92)
    t:SetPoint("TOPLEFT", 14 + (i - 1) * 180, -352)
    return t
  end
  -- a) Skin of the Day
  local sotd = Tile(1)
  sotd.tint = Tint(sotd, 1, 0.82, 0.2, 0.07)
  sotd.cell = ItemCell(sotd, 60); sotd.cell:SetPoint("LEFT", 8, 0)
  tryOnCell(sotd.cell)
  sotd.cell.extraTip = function(tt, it)
    if not TCF.db.owned[it.id] then
      tt:AddLine(string.format("Skin of the Day: %s TapCoins today (usually %s).", TCF.Commas(TCF:SkinPrice(it)), TCF.Commas(it.skinPrice)), 1, 0.82, 0, true)
    end
  end
  sotd.badge = Badge(sotd); sotd.badge:SetPoint("TOPLEFT", sotd.cell, "TOPLEFT", -5, 5)
  sotd.title = Text(sotd, "GameFontNormalSmall", "Skin of the Day", "LEFT"); sotd.title:SetPoint("TOPLEFT", 74, -9)
  sotd.name = Text(sotd, "GameFontHighlightSmall", nil, "LEFT"); sotd.name:SetPoint("TOPLEFT", 74, -23)
  sotd.name:SetWidth(92); sotd.name:SetHeight(24); sotd.name:SetJustifyV("TOP")
  sotd.was = Text(sotd, "GameFontDisableSmall", nil, "LEFT"); sotd.was:SetPoint("TOPLEFT", 74, -48); sotd.was:SetWidth(92)
  sotd.buy = Button(sotd, "Buy", 84, 20, function()
    local it = TCF:FeaturedSkin()
    if it then TCF.UI.ConfirmBuySkin(it, "shop") end
  end)
  sotd.buy:SetPoint("BOTTOMRIGHT", -8, 8)
  sotd.none = Text(sotd, "GameFontHighlightSmall", "Every shop skin is yours. Nice collection.", "LEFT")
  sotd.none:SetPoint("TOPLEFT", 74, -26); sotd.none:SetWidth(92)
  -- b) Racial Heritage
  local her = Tile(2)
  her.tint = Tint(her, 0.2, 0.5, 1, 0.06)
  her.cell = ItemCell(her, 46); her.cell:SetPoint("LEFT", 8, 0)
  tryOnCell(her.cell)
  her.title = Text(her, "GameFontNormalSmall", nil, "LEFT"); her.title:SetPoint("TOPLEFT", 62, -9); her.title:SetWidth(104)
  her.title:SetHeight(12); if her.title.SetWordWrap then her.title:SetWordWrap(false) end
  her.desc = Text(her, "GameFontHighlightSmall", nil, "LEFT"); her.desc:SetPoint("TOPLEFT", 62, -23)
  her.desc:SetWidth(104); her.desc:SetHeight(36); her.desc:SetJustifyV("TOP")
  her.buy = Button(her, "Buy", 84, 20, function() TCF:BuyRaceAccessory() end); her.buy:SetPoint("BOTTOMRIGHT", -8, 8)
  -- c) Companion Cats
  local comp = Tile(3)
  comp.tint = Tint(comp, 0.3, 0.9, 0.4, 0.05)
  comp.icon = comp:CreateTexture(nil, "ARTWORK"); comp.icon:SetSize(40, 40); comp.icon:SetPoint("LEFT", 10, 4)
  comp.icon:SetTexture(TCF.Icon("INV_Box_PetCarrier_01"))
  comp.title = Text(comp, "GameFontNormalSmall", "Companion Cats", "LEFT"); comp.title:SetPoint("TOPLEFT", 58, -9)
  comp.owned = Text(comp, "GameFontHighlightSmall", nil, "LEFT"); comp.owned:SetPoint("TOPLEFT", 58, -23); comp.owned:SetWidth(108)
  comp.from = Text(comp, "GameFontDisableSmall", nil, "LEFT"); comp.from:SetPoint("TOPLEFT", 58, -37); comp.from:SetWidth(108)
  comp.browse = Button(comp, "Browse", 84, 20, function() if TCF.ToggleCompanions then TCF:ToggleCompanions() end; TCF:PlaySound("click") end)
  comp.browse:SetPoint("BOTTOMRIGHT", -8, 8)
  local function compTip(tt)
    tt:AddLine("Companion Cats", 1, 0.82, 0)
    if comp.cheapest and TCF.CompanionTooltip then
      tt:AddLine(" ")
      TCF:CompanionTooltip(tt, comp.cheapest)
    else
      tt:AddLine("A second cat that walks beside yours.", 1, 1, 1, true)
    end
  end
  Tip(comp, compTip)
  Tip(comp.browse, compTip)

  local function refreshFeatured(light)
    local d = db()
    local secs = TCF:SecondsUntilReset()
    resetText:SetText(string.format("new wares in %dh %dm", floor(secs / 3600), floor(secs % 3600 / 60)))
    reroll:SetText("New Stock " .. coinStr(TCF:RerollCost(), 12))
    reroll:SetEnabled(d.coins >= TCF:RerollCost())
    if heroic then
      banOpen:SetText("Open  " .. coinStr(heroic.cost, 16))
      banOpen:SetEnabled(d.coins >= heroic.cost)
      local n = TCF:ChestsOf(heroic.key)
      banBag:SetText("Bag (" .. n .. ")"); banBag:SetEnabled(n > 0)
    end
    if not light then refreshChips(); refreshPrizes() end
    -- Daily Wares
    local stock = d.shop.stock
    for i, c in ipairs(cards) do
      local id = stock[i]
      local it = id and TCF.ITEMS[id]
      if it then
        c:Show(); c.id = id
        local owned = d.owned[id]
        local col, hex = rarityColor(it.rarity)
        if not light then
          c.cell:SetItem(it, true, false)
          c.name:SetText("|c" .. hex .. it.name .. "|r")
          local cl = it.class and TCF.CLASS_BY_KEY[it.class]
          c.cls:SetText(cl and cl.name or "Any class")
          c.band:SetColorTexture(col[1], col[2], col[3], 1)
          c.tint:SetColorTexture(col[1], col[2], col[3], 0.07)
          Border(c, col, it.rarity >= 4 and 1 or 0.7)
          c.glow:SetShown(it.rarity >= 5)
        end
        c.price:SetText(owned and "|cff20ff20Owned|r" or coinStr(it.price, 13))
        c.buy:SetEnabled(not owned and d.coins >= it.price)
      else
        c:Hide()
      end
    end
    -- Skin of the Day
    local sk = TCF:FeaturedSkin()
    sotd.cell:SetShown(sk ~= nil); sotd.name:SetShown(sk ~= nil); sotd.was:SetShown(sk ~= nil)
    sotd.buy:SetShown(sk ~= nil); sotd.none:SetShown(sk == nil)
    if sk then
      local owned = d.owned[sk.id]
      local col, hex = rarityColor(sk.rarity)
      if not light then
        sotd.cell:SetItem(sk, true, TCF:IsEquipped(sk))
        sotd.name:SetText("|c" .. hex .. sk.name .. "|r")
        Border(sotd, col, 0.8)
      end
      local price = TCF:SkinPrice(sk)
      sotd.badge:SetShown(not owned and price < sk.skinPrice)
      if owned then
        sotd.was:SetText("|cff20ff20Yours now|r")
        sotd.buy:SetText("Owned"); sotd.buy:SetEnabled(false)
      else
        sotd.was:SetText("was " .. TCF.Commas(sk.skinPrice))
        setCoinsButton(sotd.buy, price)
      end
    else
      sotd.badge:Hide()
    end
    -- Racial Heritage
    if not light then
      local rit, raceName = TCF:RaceItemForPlayer()
      her.item = rit
      if rit then
        her:Show()
        her.cell:SetItem(rit, true, false)
        her.title:SetText((raceName or "Racial") .. " Heritage")
        local owned = d.owned[rit.id]
        her.desc:SetText(owned and "Yours. Show or hide it in Settings."
          or ("|c" .. TCF.RARITY[rit.rarity].hex .. rit.name .. "|r, " .. (raceName or "your race") .. " pride for this character's cats."))
        her.owned = owned
      else
        her:Hide()
      end
    end
    if her.item then
      if her.owned then her.buy:SetText("Owned"); her.buy:SetEnabled(false)
      else setCoinsButton(her.buy, TCF.RACE_PRICE) end
    end
    -- Companion Cats
    if not light and TCF.COMPANIONS then
      local owned, total, cheapest = 0, #TCF.COMPANIONS, nil
      for _, c in ipairs(TCF:CompanionList()) do
        if TCF:CompanionOwned(c.key) then owned = owned + 1
        elseif not cheapest and c.price > 0 then cheapest = c end
      end
      comp.cheapest = cheapest
      comp.owned:SetText(string.format("%d / %d owned", owned, total))
      comp.from:SetText(cheapest and ("From " .. TCF.Commas(cheapest.price)) or "")
    end
  end

  ------------------------------------------------------------------ Cat Skins
  local sv = views.skins
  win.shopSkinFilter = win.shopSkinFilter or "sale"
  win.shopSkinPage = win.shopSkinPage or 1
  local FILTERS = { { "sale", "For sale" }, { "owned", "Owned" }, { "all", "All skins" } }
  local filterBtns = {}
  local skinList, skinTotal = {}, 0
  local rebuildSkins, refreshSkins
  for i, f in ipairs(FILTERS) do
    local b = Button(sv, f[2], 90, 20, function()
      win.shopSkinFilter = f[1]; win.shopSkinPage = 1; win.shopSkinsDirty = true
      refreshSkins(); TCF:PlaySound("click")
    end)
    b:SetPoint("TOPLEFT", 14 + (i - 1) * 94, -50)
    b.key = f[1]
    filterBtns[i] = b
  end
  local skinCount = Text(sv, "GameFontDisableSmall", nil, "RIGHT"); skinCount:SetPoint("TOPRIGHT", -16, -55); skinCount:SetWidth(220)
  local skinCards = {}
  local function skinAction(card)
    local it = card.item
    if not it then return end
    if TCF.db.owned[it.id] then
      if TCF:IsEquipped(it) then TCF:Unequip("skin") else TCF:Equip(it) end
      win.shopSkinsDirty = true
      TCF:PlaySound("click")
    elseif it.skinPrice then
      win.shopSkinsDirty = true
      TCF.UI.ConfirmBuySkin(it, "shop")
    end
  end
  for i = 1, SKINS_PER_PAGE do
    local c = Panel(sv, 102, 118, 0.92)
    local col, row = (i - 1) % 5, floor((i - 1) / 5)
    c:SetPoint("TOPLEFT", 17 + col * 106, -76 - row * 122)
    c.tint = Tint(c, 1, 1, 1, 0.12)
    c.cell = ItemCell(c, 58); c.cell:SetPoint("TOP", 0, -6)
    c.cell:SetScript("OnEnter", function(s)
      if not s.item then return end
      GameTooltip:SetOwner(s, "ANCHOR_RIGHT"); TCF:ItemTooltip(GameTooltip, s.item)
      local it = s.item
      if TCF.db.owned[it.id] then
        GameTooltip:AddLine(TCF:IsEquipped(it) and "Click to take it off" or "Click to wear it", 0, 1, 0)
      elseif it.skinPrice then
        local p = TCF:SkinPrice(it)
        if p < it.skinPrice then
          GameTooltip:AddLine(string.format("Skin of the Day: %s TapCoins today (usually %s).", TCF.Commas(p), TCF.Commas(it.skinPrice)), 1, 0.82, 0, true)
        end
        GameTooltip:AddLine("Click to buy", 0, 1, 0)
      end
      TCF.UI.PreviewHint(GameTooltip, win, it)
      GameTooltip:Show()
      TCF.UI.ShowTryOn(win, it)
    end)
    c.cell:SetScript("OnLeave", itemLeave)
    c.cell:SetScript("OnClick", function(s)
      if s.item and TCF.UI.PreviewClick(win, s.item) then s:GetScript("OnEnter")(s); return end
      skinAction(c)
    end)
    c.name = Text(c, "GameFontNormalSmall", nil, "CENTER"); c.name:SetPoint("TOP", c.cell, "BOTTOM", 0, -2)
    c.name:SetWidth(96); c.name:SetHeight(25); c.name:SetJustifyV("TOP")
    c.btn = Button(c, "", 94, 20, function() skinAction(c) end)
    c.btn:SetPoint("BOTTOM", 0, 5)
    c.badge = Badge(c); c.badge:SetPoint("TOPRIGHT", c, "TOPRIGHT", -3, -3)
    skinCards[i] = c
  end
  local pageText = Text(sv, "GameFontHighlightSmall"); pageText:SetPoint("BOTTOM", 0, 22)
  local prevB = Button(sv, "<", 28, 22, function() win.shopSkinPage = max(1, win.shopSkinPage - 1); refreshSkins() end)
  prevB:SetPoint("RIGHT", pageText, "LEFT", -10, 0)
  local nextB = Button(sv, ">", 28, 22, function() win.shopSkinPage = win.shopSkinPage + 1; refreshSkins() end)
  nextB:SetPoint("LEFT", pageText, "RIGHT", 10, 0)
  local emptySkins = Text(sv, "GameFontHighlight", nil, "CENTER"); emptySkins:SetPoint("CENTER", 0, 0); emptySkins:SetWidth(420)
  sv:EnableMouseWheel(true)
  sv:SetScript("OnMouseWheel", function(_, dd) win.shopSkinPage = max(1, win.shopSkinPage - dd); refreshSkins() end)

  -- the list for the current filter (sorted; built only when something changed)
  rebuildSkins = function()
    local d = db()
    local class = d.class
    local featured = TCF:FeaturedSkin()
    local owned = d.owned
    local f = win.shopSkinFilter
    local list, total, have = {}, 0, 0
    for _, it in ipairs(TCF.ITEM_LIST) do
      if it.slot == "skin" and (not it.class or it.class == class) then
        if it.skinPrice then total = total + 1; if owned[it.id] then have = have + 1 end end
        local mine = owned[it.id]
        if (f == "sale" and it.skinPrice and not mine) or (f == "owned" and mine) or f == "all" then
          list[#list + 1] = it
        end
      end
    end
    local function group(it)
      if owned[it.id] then return 3 end
      return it.skinPrice and 1 or 2
    end
    table.sort(list, function(a, b)
      if f == "sale" then
        if (a == featured) ~= (b == featured) then return a == featured end
      end
      if f == "owned" then
        if a.rarity ~= b.rarity then return a.rarity > b.rarity end
        return a.name < b.name
      end
      local ga, gb = group(a), group(b)
      if ga ~= gb then return ga < gb end
      if ga == 1 then
        if a.skinPrice ~= b.skinPrice then return a.skinPrice < b.skinPrice end
      elseif a.rarity ~= b.rarity then
        return a.rarity > b.rarity
      end
      return a.name < b.name
    end)
    skinList, skinTotal = list, total
    skinCount:SetText(string.format("%d / %d shop skins owned", have, total))
    win.shopSkinsDirty = nil
  end

  local function skinButton(c, light)
    local it = c.item
    local d = db()
    if d.owned[it.id] then
      c.btn:SetText(TCF:IsEquipped(it) and "Take off" or "Wear"); c.btn:SetEnabled(true)
    elseif it.skinPrice then
      setCoinsButton(c.btn, TCF:SkinPrice(it))
    else
      local tag = TCF.SkinSourceTag and TCF.SkinSourceTag(it) or "?"
      c.btn:SetText("|cffff8000" .. (SOURCE_WORD[tag] or tag) .. "|r"); c.btn:SetEnabled(false)
    end
  end

  refreshSkins = function(light)
    if light then
      for _, c in ipairs(skinCards) do if c.item and c:IsShown() then skinButton(c, true) end end
      return
    end
    rebuildSkins()
    for _, b in ipairs(filterBtns) do
      if b.key == win.shopSkinFilter then b:LockHighlight() else b:UnlockHighlight() end
    end
    local d = db()
    local featured = TCF:FeaturedSkin()
    local pages = max(1, math.ceil(#skinList / SKINS_PER_PAGE))
    win.shopSkinPage = min(max(1, win.shopSkinPage or 1), pages)
    for i, c in ipairs(skinCards) do
      local it = skinList[(win.shopSkinPage - 1) * SKINS_PER_PAGE + i]
      c.item = it
      if it then
        c:Show()
        local col, hex = rarityColor(it.rarity)
        c.tint:SetColorTexture(col[1], col[2], col[3], 0.12)
        Border(c, col, it.rarity >= 4 and 1 or 0.7)
        c.cell:SetItem(it, true, TCF:IsEquipped(it))
        c.name:SetText("|c" .. hex .. it.name .. "|r")
        c.badge:SetShown(it == featured and not d.owned[it.id] and TCF:SkinPrice(it) < it.skinPrice)
        skinButton(c)
      else
        c:Hide()
      end
    end
    local empty = #skinList == 0
    emptySkins:SetShown(empty)
    emptySkins:SetText(win.shopSkinFilter == "owned" and "|cff888888No cat skins yet. Pick one from For sale.|r"
      or "|cff888888You own every shop skin. Nice collection.|r")
    pageText:SetText(string.format("Page %d / %d", win.shopSkinPage, pages))
    pageText:SetShown(not empty); prevB:SetShown(not empty); nextB:SetShown(not empty)
    prevB:SetEnabled(win.shopSkinPage > 1); nextB:SetEnabled(win.shopSkinPage < pages)
  end

  ------------------------------------------------------------------ Chests
  local cv = views.chests
  local shopChests = {}
  for _, ch in ipairs(TCF.CHESTS) do if ch.cost then shopChests[#shopChests + 1] = ch end end
  local chestCards = {}
  for i, ch in ipairs(shopChests) do
    local c = Panel(cv, 172, 240, 0.92)
    c:SetPoint("TOPLEFT", 14 + (i - 1) * 180, -50)
    local q = TCF.ChestQuality(ch)
    local col = rarityColor(q)
    Border(c, col, 1)
    Tint(c, col[1], col[2], col[3], 0.08)
    local hi = Fill(c, col[1], col[2], col[3], 0.16, "BACKGROUND", 2)
    hi:SetPoint("TOPLEFT", 4, -4); hi:SetPoint("TOPRIGHT", -4, -4); hi:SetHeight(52)
    local ic = c:CreateTexture(nil, "ARTWORK"); ic:SetSize(44, 44); ic:SetPoint("TOP", 0, -10)
    ic:SetTexture(TCF.Icon(ch.icon))
    if ch.key == "heroic" then Pulse(cv, Glow(c, ic, 72, { 0.85, 0.55, 1 })) end
    -- the name stays exactly the chest's name (the tests look for it)
    -- fixed places, so a name or text on two lines never pushes into the odds
    local n = Text(c, "GameFontNormal", ch.name, "CENTER"); n:SetPoint("TOP", 0, -58); n:SetWidth(160)
    n:SetHeight(28); n:SetJustifyV("TOP")
    local d = Text(c, "GameFontDisableSmall", ch.desc, "CENTER"); d:SetPoint("TOP", 0, -88); d:SetWidth(156)
    d:SetHeight(50); d:SetJustifyV("TOP")
    c.odds = Text(c, "GameFontHighlightSmall", nil, "LEFT"); c.odds:SetPoint("TOPLEFT", 14, -140); c.odds:SetWidth(144)
    c.odds:SetSpacing(1)
    c.open = Button(c, "Open", 156, 24, function() TCF:OpenChest(ch.key) end)
    c.open:SetPoint("BOTTOM", 0, 34)
    c.bag = Button(c, "Bag (0)", 156, 20, function() TCF:ToggleBag() end)
    c.bag:SetPoint("BOTTOM", 0, 10)
    Tip(c.bag, bagTip)
    Tip(c, function(tt) TCF:ChestOddsTooltip(tt, ch, true) end)
    Tip(c.open, function(tt) TCF:ChestOddsTooltip(tt, ch, true) end)
    c.chest = ch
    chestCards[i] = c
  end
  local gearPct = floor((TCF.CHEST_GEAR_CHANCE or 0.9) * 100 + 0.5)  -- same odds as TCF:OpenChest
  local freeText = Text(cv, "GameFontHighlightSmall", nil, "LEFT"); freeText:SetPoint("TOPLEFT", 16, -298); freeText:SetWidth(528)
  freeText:SetText("|cffffd100Free chests:|r " .. TCF.DUNGEON_CHEST_TEXT .. " Quests, levels, zone clears and expeditions give chests too. Chests hold gear (" .. gearPct .. "%) or a cosmetic (" .. (100 - gearPct) .. "%); Dungeon Chests and Raider's Hoards only gear.")
  local bagRow = Panel(cv, 532, 56, 0.92); bagRow:SetPoint("TOPLEFT", 14, -368)
  Tint(bagRow, 0.85, 0.65, 0.3, 0.06)
  local bagIcon = bagRow:CreateTexture(nil, "ARTWORK"); bagIcon:SetSize(36, 36); bagIcon:SetPoint("LEFT", 12, 0)
  bagIcon:SetTexture(TCF.Icon("INV_Misc_Bag_10"))
  local bagText = Text(bagRow, "GameFontNormal", nil, "LEFT"); bagText:SetPoint("TOPLEFT", bagIcon, "TOPRIGHT", 10, -2)
  local bagSub = Text(bagRow, "GameFontDisableSmall", "Chests you earned wait here. Open them any time.", "LEFT")
  bagSub:SetPoint("BOTTOMLEFT", bagIcon, "BOTTOMRIGHT", 10, 2)
  local bagOpen = Button(bagRow, "Open Bag", 110, 22, function() TCF:ToggleBag(); TCF:PlaySound("click") end)
  bagOpen:SetPoint("RIGHT", -12, 0)
  Tip(bagOpen, bagTip)

  local function refreshChests(light)
    local d = db()
    for _, c in ipairs(chestCards) do
      local ch = c.chest
      c.open:SetText("Open  " .. coinStr(ch.cost, 13))
      c.open:SetEnabled(d.coins >= ch.cost)
      local k = TCF:ChestsOf(ch.key)
      c.bag:SetText("Bag (" .. k .. ")"); c.bag:SetEnabled(k > 0)
      if not light then
        local lines = {}
        for j, o in ipairs(oddsFor(ch)) do
          if j > 3 then break end
          -- short names, one line each (the card is narrow)
          local name = o[1] == "Cat skin from the shop" and "Cat skin" or o[1]
          lines[#lines + 1] = string.format("|c%s%s|r  %s", o[3], name, TCF.OddsText(o[2]))
        end
        c.odds:SetText(table.concat(lines, "\n"))
      end
    end
    local n = TCF:ChestCount()
    bagText:SetText(string.format("Treasure Bag: %d unopened %s", n, n == 1 and "chest" or "chests"))
  end

  ------------------------------------------------------------------ switching views, refresh
  function win:SetShopView(key)
    if not views[key] then return end
    self.shopView = key
    if key == "skins" then self.shopSkinsDirty = true end
    refresh(false)
  end

  local function refreshLastLoot()
    local lc = TCF.lastChest
    if lc and lc.gear then
      lastLoot:SetText("Last chest: " .. TCF.GearLink(lc.gear) .. (lc.isNew and " |cff20ff20New|r" or ""))
    elseif lc and lc.item then
      lastLoot:SetText("Last chest: " .. TCF.ItemLink(lc.item) .. (lc.isNew and " |cff20ff20New|r" or
        string.format(" |cffaaaaaa(duplicate, +%d TapCoins)|r", lc.salvage or 0)))
    else
      lastLoot:SetText("|cff888888Earn TapCoins from quests, Adventure bosses, level-ups and daily logins.|r")
    end
  end

  -- light: the window's quick refresh (every tap): only what follows your TapCoins
  refresh = function(light)
    local d = db()
    if not d then return end
    TCF:BuildShop()
    -- the stock or the Skin of the Day changed (midnight, a reroll): draw everything again
    local sh = d.shop or {}
    local feat = TCF.FeaturedSkin and TCF:FeaturedSkin()
    local sig = tostring(sh.day) .. ":" .. tostring(sh.rerolls) .. ":" .. table.concat(sh.stock or {}, ",") .. ":" .. tostring(feat and feat.id) .. ":" .. tostring(d.class)
    if sig ~= win.shopSig then win.shopSig = sig; light = false; win.shopSkinsDirty = true end
    local cur = win.shopView
    if not views[cur] then cur = "featured"; win.shopView = cur end
    for key, v in pairs(views) do v:SetShown(key == cur) end
    for _, b in ipairs(navBtns) do
      local on = b.key == cur
      if on then b:LockHighlight() else b:UnlockHighlight() end
      b.under:SetShown(on)
    end
    -- (a million or more: "1.23M", as in the window's header, so it stays on one line)
    local c = d.coins or 0
    balance:SetText(c < 1e6 and coinStr(c, 16) or ("|T" .. TCF.ART_PATH .. "ui_coin:16:16|t " .. TCF.FormatBig(c)))
    lastLoot:SetShown(cur ~= "skins")
    if not light then refreshLastLoot() end
    if cur == "featured" then refreshFeatured(light)
    elseif cur == "skins" then refreshSkins(light and not win.shopSkinsDirty)
    else refreshChests(light) end
  end
  win.RefreshShop = function() refresh(false) end
  -- the parts, for the tests
  win.shopUI = {
    views = views, nav = navBtns, balance = balance, lastLoot = lastLoot,
    banner = { frame = ban, name = banName, chips = chips, prizes = prizeCells, open = banOpen, bag = banBag },
    wares = cards, reroll = reroll, sotd = sotd, heritage = her, companions = comp,
    filters = filterBtns, skinCards = skinCards, skinCount = skinCount, pageText = pageText,
    skinList = function() return skinList end,
    chests = chestCards, freeText = freeText, bagText = bagText, bagOpen = bagOpen,
  }
  return refresh
end
