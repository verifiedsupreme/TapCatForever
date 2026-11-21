-- TapCatForever: the welcome tour, shown once on first login (and from Settings or /tcf welcome)
local ADDON, TCF = ...

local PAGES = {
  { "Welcome to TapCatForever!",
    "Meet your cat! Every key you press in WoW, your cat taps along.\n\n" ..
    "A, left arrow and left-click tap its left paw; D, right arrow and right-click tap its right paw. Every other key alternates.\n\n" ..
    "Taps earn XP and a trickle of TapCoins." },
  { "A cat for every class",
    "Each class has its own cat, starting at level 1, with its own levels, abilities and gear.\n\n" ..
    "Your cat wears real WoW items, every one drawn in cartoon style. Find them in chests, Adventure and real dungeons and raids, then equip them around your cat in the Gear tab." },
  { "Adventure & Expeditions",
    "In the Adventure tab, press Start and your cat fights its way through WoW's zones, dungeons and raids, from Elwynn Forest to Naxxramas. Bosses drop chests and rare cats.\n\n" ..
    "In Expeditions, send a party of three cats away for chests and XP while you play." },
  { "Professions",
    "Run a little business: Mining, Herbalism, First Aid, Fishing and Cooking, each played its own way and each able to run on its own.\n\n" ..
    "Sell your business for Renown to grow faster and unlock new professions. Materials craft exclusive items." },
  { "Chests, Shop & Style",
    "Open chests from the Treasure Bag. Buy daily wares in the Shop, and collect hats, capes, fur patterns, cat skins and Tap Effects in Appearance.\n\n" ..
    "Daily and weekly quests and achievements reward TapCoins and more chests." },
  { "Getting around",
    "Right-click your cat to open the main window. Left-click it to pet it.\n\n" ..
    "Drag the cat to move it (lock it in Settings). Ctrl + mouse wheel resizes it, Shift + wheel fades it.\n\n" ..
    "Type /tcf for commands. Have fun, and tap forever!" },
}

function TCF:ShowWelcome()
  local f = self.welcome
  if not f then
    local U = TCF.UI
    f = CreateFrame("Frame", "TapCatForeverWelcome", UIParent, U.BT)
    f:SetSize(640, 420); f:SetPoint("CENTER")
    f:SetFrameStrata("DIALOG"); f:SetToplevel(true)
    f:EnableMouse(true); f:SetMovable(true); f:RegisterForDrag("LeftButton")
    f:SetScript("OnDragStart", f.StartMoving); f:SetScript("OnDragStop", f.StopMovingOrSizing)
    if f.SetBackdrop then f:SetBackdrop(U.BACKDROP_DIALOG) end
    tinsert(UISpecialFrames, "TapCatForeverWelcome")
    local close = CreateFrame("Button", nil, f, "UIPanelCloseButton"); close:SetPoint("TOPRIGHT", -6, -6)

    local logo = f:CreateTexture(nil, "ARTWORK"); logo:SetSize(196, 196); logo:SetPoint("TOPLEFT", 18, -14)
    logo:SetTexture(TCF.ART_PATH .. "logo")
    -- a live cat that taps along under the logo
    local cat = TCF.CreateCat(f, 150, { preview = true })
    cat.frame:SetPoint("TOP", logo, "BOTTOM", 0, 6)
    local look = TCF:GetAppearance()
    cat:ApplyAppearance(look)
    f.cat = cat

    f.title = U.Text(f, "GameFontNormalHuge", nil, "LEFT"); f.title:SetPoint("TOPLEFT", 236, -34); f.title:SetWidth(380)
    f.body = U.Text(f, "GameFontHighlight", nil, "LEFT"); f.body:SetPoint("TOPLEFT", f.title, "BOTTOMLEFT", 0, -16)
    f.body:SetWidth(370); f.body:SetJustifyV("TOP"); if f.body.SetSpacing then f.body:SetSpacing(3) end
    f.dots = U.Text(f, "GameFontNormalLarge"); f.dots:SetPoint("BOTTOM", 120, 22)
    f.back = U.Button(f, "Back", 90, 24, function() f.page = math.max(1, f.page - 1); f:Show2() end)
    f.back:SetPoint("BOTTOMLEFT", 236, 18)
    f.next = U.Button(f, "Next", 110, 24, function()
      if f.page < #PAGES then f.page = f.page + 1; f:Show2() else f:Hide() end
    end)
    f.next:SetPoint("BOTTOMRIGHT", -20, 18)
    function f:Show2()
      local p = PAGES[self.page]
      self.title:SetText(p[1]); self.body:SetText(p[2])
      local d = {}
      for i = 1, #PAGES do d[i] = (i == self.page) and "|cffffd100o|r" or "|cff666666o|r" end
      self.dots:SetText(table.concat(d, " "))
      self.back:SetEnabled(self.page > 1)
      self.next:SetText(self.page < #PAGES and "Next" or "Let's tap!")
      self.cat:SetFaceFor("happy", 1.5)
    end
    -- the cat taps on its own while the tour is open
    local acc, side = 0, "L"
    f:SetScript("OnUpdate", function(_, e)
      acc = acc + e
      if acc > 0.32 then acc = 0; side = side == "L" and "R" or "L"; cat:Tap(side) end
    end)
    f:SetScript("OnHide", function() TCF.db.welcomed = true end)
    self.welcome = f
  end
  f.cat:ApplyAppearance(TCF:GetAppearance())
  f.page = 1
  f:Show2()
  f:Show()
end
