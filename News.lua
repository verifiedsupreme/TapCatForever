-- TapCatForever: "What's new" after a big update, and the Patch notes page.
-- After a big update (a version with a highlight in NewsData.lua), the first time you open
-- the TapCatForever window a slim strip sits above it with a one-line summary, a "Read more"
-- button and a close button. It never shows during play, only when you open the window
-- yourself, and it goes away once you close it, read the notes, or have seen it 3 times.
-- New players don't get it (they get the welcome tour instead). The full notes for every
-- version are in Settings > Patch notes, or /tcf news.
local ADDON, TCF = ...

local STRIP_SHOWS = 3

local function majorOf(v) return (tostring(v or ""):match("^(%d+%.%d+)")) end

-- the news entry for the version you're running, if it is a big update
function TCF:CurrentNews()
  local cur = majorOf(TCF.version)
  if not cur or not TCF.NEWS then return nil end
  for _, n in ipairs(TCF.NEWS) do
    if majorOf(n.version) == cur and n.highlight then return n end
  end
end

function TCF:NewsPending()
  local n = self:CurrentNews()
  return n and self.db and self.db.newsSeen ~= majorOf(n.version) or false
end

function TCF:MarkNewsSeen()
  local n = self:CurrentNews()
  if n and self.db then self.db.newsSeen = majorOf(n.version); self.db.newsShows = nil end
  if self.newsStrip then self.newsStrip:Hide() end
end

---------------------------------------------------------------- the strip above the window
local function createStrip(win)
  local U = TCF.UI
  local f = CreateFrame("Frame", "TapCatForeverNewsStrip", win, U.BT)
  f:SetSize(760, 46)
  f:SetPoint("BOTTOM", win, "TOP", 0, 2)
  if f.SetBackdrop then f:SetBackdrop(U.BACKDROP_DIALOG) end
  if f.SetBackdropBorderColor then f:SetBackdropBorderColor(1, 0.82, 0.2, 1) end
  f.icon = f:CreateTexture(nil, "ARTWORK"); f.icon:SetSize(28, 28); f.icon:SetPoint("LEFT", 12, 0)
  f.icon:SetTexture(TCF.Icon("INV_Scroll_03")); f.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
  f.text = U.Text(f, "GameFontHighlight", nil, "LEFT")
  f.text:SetPoint("LEFT", f.icon, "RIGHT", 10, 0); f.text:SetWidth(520)
  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton"); close:SetPoint("RIGHT", -4, 0)
  close:SetScript("OnClick", function() TCF:MarkNewsSeen() end)
  local more = U.Button(f, "Read more", 100, 22, function() TCF:MarkNewsSeen(); TCF:ShowPatchNotes() end)
  more:SetPoint("RIGHT", close, "LEFT", -6, 0)
  f:Hide()
  return f
end

-- called whenever the main window opens
function TCF:CheckNews()
  local win = self.window
  if not win or not self:NewsPending() then
    if self.newsStrip then self.newsStrip:Hide() end
    return
  end
  local n = self:CurrentNews()
  self.newsStrip = self.newsStrip or createStrip(win)
  self.newsStrip.text:SetText("|cffffd100What's new in " .. majorOf(n.version) .. ":|r " .. n.highlight)
  self.newsStrip:Show()
  self.db.newsShows = (self.db.newsShows or 0) + 1
  if self.db.newsShows >= STRIP_SHOWS then
    -- shown enough: this is the last time it appears (it stays up until the window closes)
    self.db.newsSeen = majorOf(n.version); self.db.newsShows = nil
  end
end

-- watch the window: a hidden child gets OnShow whenever the window is shown
do
  local create = TCF.CreateWindow
  function TCF:CreateWindow(...)
    local r = create(self, ...)
    local win = self.window
    if win and not win.newsWatch then
      win.newsWatch = CreateFrame("Frame", nil, win)
      win.newsWatch:SetScript("OnShow", function() TCF:CheckNews() end)
    end
    return r
  end
end

---------------------------------------------------------------- Patch notes window
local function createNotes()
  local U = TCF.UI
  local f = CreateFrame("Frame", "TapCatForeverPatchNotes", UIParent, U.BT)
  f:SetSize(640, 480); f:SetPoint("CENTER")
  f:SetFrameStrata("DIALOG"); f:SetToplevel(true)
  f:EnableMouse(true); f:SetMovable(true); f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving); f:SetScript("OnDragStop", f.StopMovingOrSizing)
  if f.SetBackdrop then f:SetBackdrop(U.BACKDROP_DIALOG) end
  tinsert(UISpecialFrames, "TapCatForeverPatchNotes")
  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton"); close:SetPoint("TOPRIGHT", -6, -6)
  local title = U.Text(f, "GameFontNormalLarge", "Patch notes"); title:SetPoint("TOP", 0, -18)

  -- versions down the left
  f.vbtns = {}
  for i, n in ipairs(TCF.NEWS or {}) do
    if i > 14 then break end
    local b = U.Button(f, n.version, 96, 22, function() f:ShowVersion(i) end)
    b:SetPoint("TOPLEFT", 18, -50 - (i - 1) * 26)
    f.vbtns[i] = b
  end

  -- the notes, scrolled with the mouse wheel
  local sf = CreateFrame("ScrollFrame", nil, f)
  sf:SetPoint("TOPLEFT", 128, -50); sf:SetPoint("BOTTOMRIGHT", -24, 40)
  local content = CreateFrame("Frame", nil, sf)
  content:SetSize(480, 10)
  sf:SetScrollChild(content)
  f.body = U.Text(content, "GameFontHighlight", nil, "LEFT")
  f.body:SetPoint("TOPLEFT", 0, 0); f.body:SetWidth(470)
  if f.body.SetJustifyV then f.body:SetJustifyV("TOP") end
  if f.body.SetSpacing then f.body:SetSpacing(2) end
  sf:EnableMouseWheel(true)
  sf:SetScript("OnMouseWheel", function(s, d)
    local range = (s.GetVerticalScrollRange and s:GetVerticalScrollRange()) or 0
    local cur = (s.GetVerticalScroll and s:GetVerticalScroll()) or 0
    s:SetVerticalScroll(math.max(0, math.min(range, cur - d * 40)))
  end)
  f.scroll, f.content = sf, content
  local hint = U.Text(f, "GameFontDisableSmall", "Scroll with the mouse wheel. Older versions are on the left.")
  hint:SetPoint("BOTTOM", 60, 16)

  function f:ShowVersion(i)
    local n = TCF.NEWS and TCF.NEWS[i]
    if not n then return end
    for k, b in ipairs(self.vbtns) do
      if b.LockHighlight then if k == i then b:LockHighlight() else b:UnlockHighlight() end end
    end
    self.body:SetText("|cffffffffVersion " .. n.version .. "|r\n\n" .. n.text)
    local h = (self.body.GetStringHeight and self.body:GetStringHeight()) or 0
    self.content:SetHeight(math.max(10, (tonumber(h) or 0) + 20))
    if self.scroll.SetVerticalScroll then self.scroll:SetVerticalScroll(0) end
  end
  f:Hide()
  return f
end

function TCF:ShowPatchNotes(version)
  self.patchNotes = self.patchNotes or createNotes()
  local idx = 1
  for i, n in ipairs(TCF.NEWS or {}) do if n.version == version then idx = i end end
  self.patchNotes:Show()
  self.patchNotes:ShowVersion(idx)
end

---------------------------------------------------------------- login: new players skip the strip; /tcf news
do
  local ev = CreateFrame("Frame")
  ev:RegisterEvent("PLAYER_LOGIN")
  ev:SetScript("OnEvent", function()
    local db = TCF.db
    -- brand-new players see the welcome tour, not "what's new"
    if db and not db.welcomed then
      local n = TCF:CurrentNews()
      if n then db.newsSeen = majorOf(n.version) end
    end
    local orig = SlashCmdList and SlashCmdList.TAPCATFOREVER
    if orig and not TCF.newsSlash then
      TCF.newsSlash = true
      local WORDS = { news = true, patchnotes = true, notes = true, changelog = true, whatsnew = true }
      SlashCmdList.TAPCATFOREVER = function(msg, ...)
        local cmd = (msg or ""):lower():match("^%s*(%S*)")
        if WORDS[cmd] then return TCF:ShowPatchNotes() end
        return orig(msg, ...)
      end
    end
  end)
end
