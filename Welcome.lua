-- TapCatForever: a short welcome, shown once on first login (and from Settings or /tcf welcome).
-- Two pages: the logo with your tapping cat, then a picture grid of what there is to do.
local ADDON, TCF = ...

local TILES = {
  { "INV_Helmet_08",        "Real gear",   "Every WoW item, drawn for your cat" },
  { "INV_Sword_04",         "Adventure",   "Fight through dungeons and raids" },
  { "INV_Misc_Map_01",      "Expeditions", "Send three cats out for loot" },
  { "Trade_Mining",         "Professions", "Gather, craft real gear and run a business" },
  { "INV_Box_02",           "Collect",     "Open chests for gear, skins and hats" },
  { "INV_Misc_GroupNeedMore", "Play with friends", "Group with friends who have the addon: every tap counts as 1.5" },
}

function TCF:ShowWelcome()
  local f = self.welcome
  if not f then
    local U = TCF.UI
    f = CreateFrame("Frame", "TapCatForeverWelcome", UIParent, U.BT)
    f:SetSize(600, 380); f:SetPoint("CENTER")
    f:SetFrameStrata("DIALOG"); f:SetToplevel(true)
    f:EnableMouse(true); f:SetMovable(true); f:RegisterForDrag("LeftButton")
    f:SetScript("OnDragStart", f.StartMoving); f:SetScript("OnDragStop", f.StopMovingOrSizing)
    if f.SetBackdrop then f:SetBackdrop(U.BACKDROP_DIALOG) end
    tinsert(UISpecialFrames, "TapCatForeverWelcome")
    local close = CreateFrame("Button", nil, f, "UIPanelCloseButton"); close:SetPoint("TOPRIGHT", -6, -6)

    -- page 1: the logo and your cat, tapping away
    local p1 = CreateFrame("Frame", nil, f); p1:SetAllPoints()
    local logo = p1:CreateTexture(nil, "ARTWORK"); logo:SetSize(250, 250); logo:SetPoint("TOPLEFT", 26, -22)
    logo:SetTexture(TCF.ART_PATH .. "logo")
    local cat = TCF.CreateCat(p1, 170, { preview = true })
    cat.frame:SetPoint("TOPRIGHT", -70, -40)
    f.cat = cat
    local hello = U.Text(p1, "GameFontNormalHuge", "Meet your cat!"); hello:SetPoint("TOP", cat.frame, "BOTTOM", 0, -6)
    local line = U.Text(p1, "GameFontHighlight", "Every key you press, it taps too.\nTaps earn XP and TapCoins.")
    line:SetPoint("TOP", hello, "BOTTOM", 0, -8); line:SetWidth(240)
    local go1 = U.Button(p1, "Next", 120, 26, function() f:Page(2) end); go1:SetPoint("BOTTOMRIGHT", -24, 20)

    -- page 2: a picture grid of the things to do
    local p2 = CreateFrame("Frame", nil, f); p2:SetAllPoints(); p2:Hide()
    local t2 = U.Text(p2, "GameFontNormalHuge", "So much to do"); t2:SetPoint("TOP", 0, -24)
    for i, t in ipairs(TILES) do
      local col, row = (i - 1) % 3, math.floor((i - 1) / 3)
      local tile = U.Panel(p2, 176, 104, 0.9); tile:SetPoint("TOPLEFT", 22 + col * 188, -62 - row * 114)
      local ic = tile:CreateTexture(nil, "ARTWORK"); ic:SetSize(44, 44); ic:SetPoint("TOP", 0, -10); ic:SetTexture(TCF.Icon(t[1]))
      if t[2] == "Professions" then f.profIcon = ic end
      local name = U.Text(tile, "GameFontNormalLarge", t[2]); name:SetPoint("TOP", ic, "BOTTOM", 0, -4)
      local d = U.Text(tile, "GameFontHighlightSmall", t[3]); d:SetPoint("TOP", name, "BOTTOM", 0, -2); d:SetWidth(166)
    end
    local tip = U.Text(p2, "GameFontNormal", "Right-click your cat to open the window. Drag it to move it.")
    -- sits between the tiles and the buttons so nothing overlaps it
    tip:SetPoint("BOTTOM", 0, 58); tip:SetWidth(540)
    local back = U.Button(p2, "Back", 80, 26, function() f:Page(1) end); back:SetPoint("BOTTOMRIGHT", -154, 20)
    local go2 = U.Button(p2, "Let's tap!", 120, 26, function() f:Hide() end); go2:SetPoint("BOTTOMRIGHT", -24, 20)

    function f:Page(n)
      p1:SetShown(n == 1); p2:SetShown(n == 2)
      if n == 1 then self.cat:SetFaceFor("happy", 1.5) end
    end
    -- the cat taps on its own while the welcome is open
    local acc, side = 0, "L"
    f:SetScript("OnUpdate", function(_, e)
      acc = acc + e
      if acc > 0.3 then acc = 0; side = side == "L" and "R" or "L"; cat:Tap(side) end
    end)
    f:SetScript("OnHide", function() TCF.db.welcomed = true end)
    self.welcome = f
  end
  f.cat:ApplyAppearance(TCF:GetAppearance())
  -- the Professions tile shows the cat's own main profession (Mining, Skinning or Tailoring)
  local fam = TCF.MainProf and TCF.FAMILIES and TCF.FAMILIES[TCF:MainProf(TCF.db.class)]
  if f.profIcon and fam and type(fam.icon) == "string" then
    f.profIcon:SetTexture(TCF.Icon(fam.icon:match("([^\\/]+)$") or fam.icon))
  end
  f:Page(1)
  f:Show()
end
