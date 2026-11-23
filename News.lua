-- TapCatForever: "What's new" after a big update, and the Patch notes page.
-- After a big update (a version with a highlight in NewsData.lua), the first time you open
-- the TapCatForever window a slim strip sits above it with a one-line summary, a "Read more"
-- button and a close button. It never shows during play, only when you open the window
-- yourself, and it goes away once you close it, read the notes, or have seen it 3 times.
-- New players don't get it (they get the welcome tour instead). The full notes for every
-- version are in Settings > Patch notes, or /tcf news.
-- 1.6.0 has a pop-up instead of the strip (TCF.NEWS_POPUPS): a small box over the middle of the
-- window with six pictures of what is new, one line on multiplayer, "Read the full patch notes"
-- and Close. It shows once per account, the first time the window opens.
local ADDON, TCF = ...

local STRIP_SHOWS = 3

-- versions whose What's new is a pop-up with pictures (Art/news, tools/make_news_art.py)
TCF.NEWS_POPUPS = {
  ["1.6.0"] = {
    title = "What's new in 1.6",
    tiles = {
      { "casino", "Cat Casino" }, { "window", "Resize your window" }, { "sets", "Animated dungeon sets" },
      { "professions", "Professions level like WoW" }, { "farm", "Farm your favourite bosses" }, { "party", "Party expeditions" },
    },
    note = "Multiplayer is still in the works: party death roll, rock paper scissors and the leaderboard may not work yet.",
  },
}

local function majorOf(v) return (tostring(v or ""):match("^(%d+%.%d+)")) end

-- the news entry for the version you're running, if it is a big update
function TCF:CurrentNews()
  local cur = majorOf(TCF.version)
  if not cur or not TCF.NEWS then return nil end
  for _, n in ipairs(TCF.NEWS) do
    if majorOf(n.version) == cur and n.highlight then return n end
  end
end

-- the id a news entry is remembered by: its full version (1.5.1); saves from 1.5.0 stored
-- just the major version ("1.5"), which still counts as having seen 1.5.0
local function seenId(n) return n.version end
local function wasSeen(db, n)
  local seen = db.newsSeen
  return seen == n.version or (seen == majorOf(n.version) and n.version == seen .. ".0")
end
-- what the strip calls the update: "1.5" for 1.5.0, "1.5.1" for later ones
local function label(n)
  local m = majorOf(n.version)
  return n.version == m .. ".0" and m or n.version
end

function TCF:NewsPending()
  local n = self:CurrentNews()
  return n and self.db and not wasSeen(self.db, n) or false
end

function TCF:MarkNewsSeen()
  local n = self:CurrentNews()
  if n and self.db then self.db.newsSeen = seenId(n); self.db.newsShows = nil end
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

---------------------------------------------------------------- the pop-up over the window
local POP_W, POP_H, TILE_W, TILE_H, GAP = 404, 334, 120, 60, 8
local function createPopup(win, P)
  local U = TCF.UI
  local f = CreateFrame("Frame", "TapCatForeverWhatsNew", win, U.BT)
  f:SetSize(POP_W, POP_H)
  if f.SetBackdrop then f:SetBackdrop(U.BACKDROP_DIALOG) end
  if f.SetBackdropBorderColor then f:SetBackdropBorderColor(1, 0.82, 0.2, 1) end
  f:EnableMouse(true) -- clicks on it don't reach the page under it
  -- its own nearly solid fill (the dialog backdrop alone lets the page behind show through)
  f.fill = f:CreateTexture(nil, "BACKGROUND", nil, 1)
  f.fill:SetPoint("TOPLEFT", 11, -12); f.fill:SetPoint("BOTTOMRIGHT", -12, 11)
  f.fill:SetColorTexture(0.06, 0.05, 0.09, 0.97)
  -- and the rest of the window dimmed behind it while it is up
  local veil = CreateFrame("Frame", nil, win)
  veil:SetPoint("TOPLEFT", win, "TOPLEFT", 4, -4); veil:SetPoint("BOTTOMRIGHT", win, "BOTTOMRIGHT", -4, 4)
  veil.tex = veil:CreateTexture(nil, "BACKGROUND"); veil.tex:SetAllPoints(); veil.tex:SetColorTexture(0, 0, 0, 0.55)
  veil:Hide()
  f.veil = veil
  f:SetScript("OnShow", function() veil:Show() end)
  f:SetScript("OnHide", function() veil:Hide() end)
  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton"); close:SetPoint("TOPRIGHT", -4, -4)
  close:SetScript("OnClick", function() f:Hide() end)
  f.title = U.Text(f, "GameFontNormalHuge", P.title); f.title:SetPoint("TOP", 0, -18)
  -- six pictures in two rows of three, each with its few words under it
  f.tiles = {}
  local x0 = (POP_W - 3 * TILE_W - 2 * GAP) / 2
  for i, t in ipairs(P.tiles) do
    local col, row = (i - 1) % 3, math.floor((i - 1) / 3)
    local tile = CreateFrame("Frame", nil, f)
    tile:SetSize(TILE_W, TILE_H + 30)
    tile:SetPoint("TOPLEFT", x0 + col * (TILE_W + GAP), -54 - row * (TILE_H + 38))
    tile.pic = tile:CreateTexture(nil, "ARTWORK"); tile.pic:SetSize(TILE_W, TILE_H); tile.pic:SetPoint("TOP")
    tile.pic:SetTexture(TCF.ART_PATH .. "news\\" .. t[1])
    tile.label = U.Text(tile, "GameFontNormalSmall", t[2]); tile.label:SetPoint("TOP", tile.pic, "BOTTOM", 0, -3)
    tile.label:SetWidth(TILE_W + GAP - 2)
    f.tiles[i] = tile
  end
  f.note = U.Text(f, "GameFontHighlightSmall", P.note); f.note:SetPoint("TOP", 0, -54 - 2 * (TILE_H + 38) - 2)
  f.note:SetWidth(POP_W - 40)
  -- the notes of the version this pop-up is about (a hotfix after it sits beside them)
  f.more = U.Button(f, "Read the full patch notes", 190, 24, function() f:Hide(); TCF:ShowPatchNotes(f.newsVersion) end)
  f.more:SetPoint("BOTTOMLEFT", 22, 18)
  f.done = U.Button(f, "Close", 100, 24, function() f:Hide() end)
  f.done:SetPoint("BOTTOMRIGHT", -22, 18)
  f:Hide()
  return f
end

-- centred on the window, over everything on it; a little bigger in the wide windows
function TCF:FitNewsPopup()
  local f, win = self.newsPopup, self.window
  if not f or not win then return end
  f:ClearAllPoints(); f:SetPoint("CENTER", win, "CENTER", 0, 0)
  local compact = win.IsCompact and win:IsCompact()
  if f.SetScale then f:SetScale(compact and 1 or 1.2) end
  if f.SetFrameLevel and win.GetFrameLevel then pcall(f.SetFrameLevel, f, (win:GetFrameLevel() or 1) + 120) end
  if f.veil and f.veil.SetFrameLevel and win.GetFrameLevel then pcall(f.veil.SetFrameLevel, f.veil, (win:GetFrameLevel() or 1) + 119) end
end

function TCF:ShowNewsPopup(n)
  local P = n and TCF.NEWS_POPUPS[n.version]
  if not P or not self.window then return end
  self.newsPopup = self.newsPopup or createPopup(self.window, P)
  self.newsPopup.newsVersion = n.version
  self:FitNewsPopup()
  self.newsPopup:Show()
end

-- called whenever the main window opens
function TCF:CheckNews()
  local win = self.window
  if not win or not self:NewsPending() then
    if self.newsStrip then self.newsStrip:Hide() end
    return
  end
  local n = self:CurrentNews()
  if TCF.NEWS_POPUPS[n.version] then
    -- a pop-up update: shown this once (per account), never the strip
    if self.newsStrip then self.newsStrip:Hide() end
    self.db.newsSeen = seenId(n); self.db.newsShows = nil
    self:ShowNewsPopup(n)
    return
  end
  self.newsStrip = self.newsStrip or createStrip(win)
  -- above the window when there's room, otherwise below it, otherwise just inside its top edge
  local strip = self.newsStrip
  strip:ClearAllPoints()
  local top, bottom = win.GetTop and win:GetTop(), win.GetBottom and win:GetBottom()
  local ptop = UIParent.GetTop and UIParent:GetTop()
  if type(top) == "number" and type(ptop) == "number" and top + 50 > ptop then
    if type(bottom) == "number" and bottom - 50 >= 0 then strip:SetPoint("TOP", win, "BOTTOM", 0, -2)
    else
      strip:SetPoint("TOP", win, "TOP", 0, -44)
      -- inside the window: above everything on it (the Casino tab's sign sits there too)
      if strip.SetFrameLevel and win.GetFrameLevel then pcall(strip.SetFrameLevel, strip, (win:GetFrameLevel() or 1) + 80) end
    end
  else
    strip:SetPoint("BOTTOM", win, "TOP", 0, 2)
  end
  self.newsStrip.text:SetText("|cffffd100What's new in " .. label(n) .. ":|r " .. n.highlight)
  self.newsStrip:Show()
  self.db.newsShows = (self.db.newsShows or 0) + 1
  if self.db.newsShows >= STRIP_SHOWS then
    -- shown enough: this is the last time it appears (it stays up until the window closes)
    self.db.newsSeen = seenId(n); self.db.newsShows = nil
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
      -- the pop-up is shown once: closing the window (Esc, its X) closes it too
      win.newsWatch:SetScript("OnHide", function() if TCF.newsPopup then TCF.newsPopup:Hide() end end)
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
    if db and not db.welcomed and (db.taps or 0) == 0 then
      local n = TCF:CurrentNews()
      if n then db.newsSeen = seenId(n) end
    end
  end)
end

-- /tcf news (wraps the slash handler when this file loads, like Compendium.lua)
do
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
end
