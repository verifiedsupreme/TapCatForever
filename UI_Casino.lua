-- TapCatForever: the Casino tab. The money and the rules are in Casino.lua; this file draws them.
--   The page covers the whole window under the tabs (the profile column too), with a sign where
--   the profile cat sits. Sub-views: Slots, Blackjack and Death roll (DeathRoll.lua and
--   UI_DeathRoll.lua fill that one through TCF.UI.CasinoDeathRoll(container, win); it also plays
--   rock paper scissors, RPS.lua and UI_RPS.lua).
--   Slots: a cartoon cat slot machine; the reels scroll, slow down and stop left to right, the
--   lever pulls, the bulbs chase, and a win glows on the line and bursts coins (a big win does a
--   bigger show, inside the window only). Blackjack: cards slide from the shoe, the hole card flips.
--   Winnings are paid when the animation ends (TCF:CasinoCollect), or at once if the tab closes.
local ADDON, TCF = ...
local floor, min, max, random = math.floor, math.min, math.max, math.random
local sin, cos, abs, pi = math.sin, math.cos, math.abs, math.pi

local CART = TCF.ART_PATH .. "casino\\"
local CW, CH = 870, 456            -- each game's area (the Death roll container is this size too)
TCF.CASINO_AREA = { CW, CH }

local function tex(parent, name, w, h, layer, sub)
  local t = parent:CreateTexture(nil, layer or "ARTWORK", nil, sub or 0)
  if name then t:SetTexture(CART .. name) end
  if w then t:SetSize(w, h) end
  return t
end
-- place by centre, x right and y down from the parent's top left
local function at(r, parent, x, y, point)
  r:ClearAllPoints(); r:SetPoint(point or "CENTER", parent, "TOPLEFT", x, -y)
end
local function easeOut(p) return 1 - (1 - p) ^ 3 end
local function level(f, parent, plus)
  if f.SetFrameLevel and parent.GetFrameLevel then pcall(f.SetFrameLevel, f, (parent:GetFrameLevel() or 1) + plus) end
end

---------------------------------------------------------------- coin bursts (inside the window)
local function Burst(parent)
  local layer = CreateFrame("Frame", nil, parent)
  layer:SetAllPoints()
  level(layer, parent, 40)
  local B = { live = {}, pool = {}, layer = layer }
  -- x, y from the bottom left of the parent
  function B:Emit(x, y, n, power, sparkles)
    for _ = 1, n do
      local p = table.remove(self.pool) or { t = layer:CreateTexture(nil, "OVERLAY") }
      local spark = sparkles and random() < 0.3
      p.t:SetTexture(CART .. (spark and "sparkle" or "sym_coin"))
      local size = spark and random(16, 28) or random(16, 26)
      p.t:SetSize(size, size)
      local a = pi / 2 + (random() - 0.5) * 2.0
      local sp = (220 + random() * 280) * (power or 1)
      p.x, p.y, p.vx, p.vy = x, y, cos(a) * sp, sin(a) * sp
      p.rot, p.vr, p.age, p.life = random() * 6, (random() - 0.5) * 12, 0, 1.1 + random() * 0.8
      p.t:SetAlpha(1); p.t:Show()
      table.insert(self.live, p)
    end
  end
  function B:Update(e)
    for i = #self.live, 1, -1 do
      local p = self.live[i]
      p.age = p.age + e
      if p.age >= p.life then
        p.t:Hide(); table.remove(self.live, i); table.insert(self.pool, p)
      else
        p.vy = p.vy - 950 * e
        p.x, p.y, p.rot = p.x + p.vx * e, p.y + p.vy * e, p.rot + p.vr * e
        p.t:ClearAllPoints(); p.t:SetPoint("CENTER", layer, "BOTTOMLEFT", p.x, p.y)
        if p.t.SetRotation then p.t:SetRotation(p.rot) end
        local f = p.age / p.life
        p.t:SetAlpha(f < 0.7 and 1 or (1 - f) / 0.3)
      end
    end
  end
  function B:Clear()
    for i = #self.live, 1, -1 do local p = self.live[i]; p.t:Hide(); table.insert(self.pool, p); self.live[i] = nil end
  end
  return B
end

-- a "Big win" style banner that pops in, holds and fades (a frame, so it can scale)
local function Banner(parent, x, y)
  local f = CreateFrame("Frame", nil, parent)
  f:SetSize(360, 70); at(f, parent, x, y)
  level(f, parent, 45)
  local g = tex(f, "glow", 420, 120, "BACKGROUND"); g:SetPoint("CENTER"); g:SetBlendMode("ADD"); g:SetVertexColor(1, 0.75, 0.2)
  f.text = TCF.UI.Text(f, "GameFontNormalHuge"); f.text:SetPoint("CENTER")
  f.sub = TCF.UI.Text(f, "GameFontHighlightLarge"); f.sub:SetPoint("TOP", f.text, "BOTTOM", 0, -4)
  f:Hide()
  function f:Play(text, sub, r, g2, b)
    self.text:SetText(text); self.text:SetTextColor(r or 1, g2 or 0.85, b or 0.2)
    self.sub:SetText(sub or "")
    self.t = 0; self:SetAlpha(1); self:Show()
  end
  function f:Update(e)
    if not self:IsShown() or not self.t then return end
    self.t = self.t + e
    local t = self.t
    local s = t < 0.25 and (0.3 + 0.95 * t / 0.25) or t < 0.4 and (1.25 - (t - 0.25) / 0.15 * 0.25) or (1 + 0.04 * sin(t * 6))
    if self.SetScale then self:SetScale(max(0.05, s)) end
    if t > 2.6 then self:SetAlpha(max(0, 1 - (t - 2.6) / 0.5)) end
    if t > 3.1 then self:Hide(); self.t = nil end
  end
  return f
end

---------------------------------------------------------------- bet chooser (shared by the games)
-- TCF.UI.CasinoBetChooser(parent, onChange): - and + buttons, the bet, and quick 10 / 50 / 100 / Max.
-- The bet is TCF.db.casino.bet, clamped to TCF:CasinoLimits(). f:SetLocked(true) while a round runs.
local function stepFor(bet) return TCF.CasinoBetStep(bet) end

-- a bet short enough for the bet box: 4,500 / 125.5K / 4.5M (the bet box is 100 px wide)
function TCF.CasinoShortBet(n)
  local function trim(x) return (x:gsub("%.?0+$", "")) end
  if n >= 1e9 then return trim(string.format("%.2f", n / 1e9)) .. "B" end
  if n >= 1e6 then return trim(string.format("%.2f", n / 1e6)) .. "M" end
  if n >= 1e5 then return trim(string.format("%.1f", n / 1e3)) .. "K" end
  return TCF.Commas(n)
end

function TCF.UI.CasinoBetChooser(parent, onChange)
  local U = TCF.UI
  local f = CreateFrame("Frame", nil, parent); f:SetSize(232, 54)
  local function set(n)
    local c = TCF:CasinoData()
    c.bet = TCF:CasinoClampBet(n) or TCF.CASINO_MIN_BET
    TCF:PlaySound("click")
    if onChange then onChange() end
  end
  local label = U.Text(f, "GameFontNormal", "Bet", "LEFT"); label:SetPoint("TOPLEFT", 0, -4)
  local minus = U.Button(f, "-", 28, 24, function()
    local b = TCF:CasinoData().bet or 10; local s = stepFor(b - 1); set(math.ceil(b / s) * s - s)
  end)
  minus:SetPoint("TOPLEFT", 34, 0)
  local val = U.Text(f, "GameFontHighlightLarge"); val:SetPoint("LEFT", minus, "RIGHT", 4, 0); val:SetWidth(100)
  if val.SetWordWrap then val:SetWordWrap(false) end
  local plus = U.Button(f, "+", 28, 24, function()
    local b = TCF:CasinoData().bet or 10; local s = stepFor(b); set(floor(b / s) * s + s)
  end)
  plus:SetPoint("LEFT", minus, "RIGHT", 108, 0)
  f.minus, f.plus, f.val = minus, plus, val
  local quick = {}
  for i, q in ipairs({ 10, 50, 100, "Max" }) do
    local b = U.Button(f, tostring(q), 54, 22, function()
      if q == "Max" then local _, hi = TCF:CasinoLimits(); set(hi) else set(q) end
    end)
    b:SetPoint("TOPLEFT", (i - 1) * 58, -30)
    b.q = q
    quick[i] = b
  end
  f.quick = quick
  function f:SetLocked(v) self.locked = v; self:Refresh() end
  function f:Refresh()
    local c = TCF:CasinoData()
    local lo, hi = TCF:CasinoLimits()
    local ok = hi >= lo and not self.locked
    if hi >= lo then c.bet = TCF:CasinoClampBet(c.bet or lo) end
    local bet = c.bet or lo
    val:SetText(hi >= lo and ("|T" .. TCF.ART_PATH .. "ui_coin:16:16|t " .. TCF.CasinoShortBet(bet)) or "|cff888888-|r")
    local function en(b, v) if v then b:Enable() else b:Disable() end end
    en(minus, ok and bet > lo); en(plus, ok and bet < hi)
    for _, b in ipairs(quick) do en(b, ok and (b.q == "Max" or b.q <= hi)) end
  end
  return f
end

---------------------------------------------------------------- slots
local SYM_PLURAL = { cat = "cats", gem = "gems", bell = "bells", coin = "coins", fish = "fish", yarn = "yarn balls", paw = "paws" }
local MACHINE_X, MACHINE_Y, MACHINE = 14, 18, 420    -- the machine art (viewBox 420, tools/make_casino_art.py)
local WIN_X, WIN_Y, WIN_W, WIN_H = 60, 118, 300, 216 -- the reel window inside it
local ROW = 72                                       -- a reel row
-- reel motion: full speed (rows per second), then a cubic ease-out to the stop, then a small
-- fixed bounce. Each reel stops at least REEL_GAP after the one to its left; the first one no
-- sooner than FIRST_STOP. 28 rows a second is about half a row per frame at 60 fps.
local REEL_SPEED, REEL_EASE, REEL_BOUNCE, BOUNCE_ROWS = 28, 0.45, 0.14, 0.22
local FIRST_STOP, REEL_GAP = 0.75, 0.32

-- how often each line comes up (for the odds on hover), from the reel strips
local function slotOdds()
  local R = TCF.SLOT_REELS
  local n, count = 0, {}
  for _, a in ipairs(R[1]) do for _, b in ipairs(R[2]) do for _, c in ipairs(R[3]) do
    n = n + 1
    local m, kind = TCF.SlotsPay(a, b, c)
    local key = kind == "three" and a or kind
    if key then count[key] = (count[key] or 0) + 1 end
  end end end
  return n, count
end

local function SlotsView(box, cv)
  local U = TCF.UI
  local S = { reels = {}, pos = {}, spinning = false }
  local bg = tex(box, "room", CW, CH, "BACKGROUND"); bg:SetAllPoints(); bg:SetTexCoord(0, 1, 0, 0.92)

  local m = CreateFrame("Frame", nil, box); m:SetSize(MACHINE, MACHINE); at(m, box, MACHINE_X, MACHINE_Y, "TOPLEFT")
  local body = tex(m, "machine", MACHINE, MACHINE, "BORDER"); body:SetAllPoints()
  -- reels (each a clipped strip of five symbols scrolling past three rows)
  local last = TCF:CasinoData().slotsLast
  for r = 1, 3 do
    local clip = CreateFrame("Frame", nil, m)
    clip:SetSize(WIN_W / 3, WIN_H); at(clip, m, WIN_X + (r - 1) * WIN_W / 3, WIN_Y, "TOPLEFT")
    if clip.SetClipsChildren then clip:SetClipsChildren(true) end
    local cells = {}
    for k = -2, 2 do
      local t = clip:CreateTexture(nil, "ARTWORK"); t:SetSize(64, 64)
      cells[k] = t
    end
    local shadeTop = clip:CreateTexture(nil, "OVERLAY"); shadeTop:SetPoint("TOPLEFT"); shadeTop:SetPoint("TOPRIGHT"); shadeTop:SetHeight(26); shadeTop:SetColorTexture(0.23, 0.15, 0.12, 0.16)
    local shadeBot = clip:CreateTexture(nil, "OVERLAY"); shadeBot:SetPoint("BOTTOMLEFT"); shadeBot:SetPoint("BOTTOMRIGHT"); shadeBot:SetHeight(26); shadeBot:SetColorTexture(0.23, 0.15, 0.12, 0.16)
    S.reels[r] = { clip = clip, cells = cells }
    local stop = type(last) == "table" and type(last.stops) == "table" and tonumber(last.stops[r]) or random(#TCF.SLOT_REELS[r])
    S.pos[r] = stop
  end
  for i = 1, 2 do   -- the dividers between the reels (over the symbols)
    local d = tex(m, "reel_divider", 12, WIN_H, "OVERLAY", 2); at(d, m, WIN_X + i * WIN_W / 3, WIN_Y + WIN_H / 2)
  end
  -- the pay line (over the reels) and its win glow
  local glowLayer = CreateFrame("Frame", nil, m); glowLayer:SetAllPoints(); level(glowLayer, m, 6)
  local line = glowLayer:CreateTexture(nil, "OVERLAY", nil, 3); line:SetSize(WIN_W - 8, 3); at(line, m, WIN_X + WIN_W / 2, WIN_Y + WIN_H / 2)
  line:SetColorTexture(0.91, 0.31, 0.36, 0.45)
  for _, sx in ipairs({ -1, 1 }) do   -- the pay line arrows on both sides of the window
    local mk = tex(glowLayer, "payline", 24, 24, "OVERLAY", 4)
    at(mk, m, WIN_X + WIN_W / 2 + sx * (WIN_W / 2 + 2), WIN_Y + WIN_H / 2)
    if sx > 0 then mk:SetTexCoord(1, 0, 0, 1) end
  end
  local glow = tex(glowLayer, "glow", WIN_W + 40, ROW + 50, "OVERLAY"); at(glow, m, WIN_X + WIN_W / 2, WIN_Y + WIN_H / 2)
  glow:SetBlendMode("ADD"); glow:SetVertexColor(1, 0.8, 0.25); glow:Hide()
  S.glow = glow
  -- the marquee and its chase lights
  local marquee = U.Text(m, "GameFontNormalLarge", "Lucky Paws"); at(marquee, m, 210, 69)
  marquee:SetTextColor(1, 0.85, 0.3)
  local bulbs = {}
  for i = 0, 7 do
    for _, x in ipairs({ 37, 383 }) do
      local b = tex(m, "bulb", 16, 16, "OVERLAY", 5); at(b, m, x, 132 + i * 28)
      b.i = #bulbs; bulbs[#bulbs + 1] = b
    end
  end
  for i = 0, 5 do
    local b = tex(m, "bulb", 14, 14, "OVERLAY", 5); at(b, m, 120 + i * 36, 36)
    b.i = #bulbs; bulbs[#bulbs + 1] = b
  end
  S.bulbs = bulbs
  -- the lever: hub on the side, a rod and a red ball that comes down when pulled
  local HUB_X, HUB_Y, LEN = 400, 236, 118
  local rod = tex(m, "lever_rod", 20, LEN, "BORDER", -1); rod:SetTexCoord(0.19, 0.81, 0, 1)
  local hub = tex(m, "lever_hub", 30, 30, "BORDER", 1); at(hub, m, HUB_X, HUB_Y)
  local ball = tex(m, "lever_ball", 38, 38, "ARTWORK", 2)
  local function setLever(d)  -- d = 0 up ... 1 pulled down
    local dy = LEN * (1 - 1.5 * d)
    at(ball, m, HUB_X, HUB_Y - dy)
    rod:ClearAllPoints()
    if dy >= 0 then rod:SetPoint("BOTTOM", hub, "CENTER", 0, 0); rod:SetHeight(max(1, dy))
    else rod:SetPoint("TOP", hub, "CENTER", 0, 0); rod:SetHeight(max(1, -dy)) end
  end
  setLever(0)
  local leverBtn = CreateFrame("Button", nil, m); leverBtn:SetSize(48, 60); at(leverBtn, m, HUB_X, HUB_Y - LEN + 10)
  level(leverBtn, m, 8)
  leverBtn:SetScript("OnClick", function() S:Spin() end)
  U.Tip(leverBtn, function(tt) tt:AddLine("Pull the lever", 1, 0.82, 0); tt:AddLine("Spins the reels for your bet.", 1, 1, 1) end)
  -- click the reels to stop them at once
  local skip = CreateFrame("Button", nil, m); skip:SetSize(WIN_W, WIN_H); at(skip, m, WIN_X, WIN_Y, "TOPLEFT"); level(skip, m, 7)
  skip:SetScript("OnClick", function() if S.spinning then S:StopNow() end end)

  local burst = Burst(box)
  -- the big-win banner sits on the marquee, so the winning line stays in view
  local banner = Banner(box, MACHINE_X + MACHINE / 2, MACHINE_Y + 72)
  S.burst, S.banner = burst, banner

  ------------------------------------------------ right side: title, how it works, pay table, cat, bet, spin
  local RX = 470
  -- a dark card behind the right column, so its text never sits on the busy room art
  local card = tex(box, nil, 408, 444, "BACKGROUND", 2); at(card, box, RX - 12, 6, "TOPLEFT")
  card:SetColorTexture(0.07, 0.05, 0.11, 0.72)
  local title = U.Text(box, "GameFontNormalHuge", "Lucky Paws slots", "LEFT"); at(title, box, RX, 16, "TOPLEFT")
  local how = U.Text(box, "GameFontHighlightSmall", "|cffffd100How it works:|r pick a bet and pull the lever. Three of a kind on the middle line wins, " ..
    "and every cat on it pays. Hover here for the odds.", "LEFT")
  at(how, box, RX, 44, "TOPLEFT"); how:SetWidth(380); if how.SetSpacing then how:SetSpacing(2) end
  local howHit = CreateFrame("Frame", nil, box); howHit:SetSize(380, 30); at(howHit, box, RX, 42, "TOPLEFT")
  local hh = how.GetStringHeight and how:GetStringHeight()
  if type(hh) == "number" and hh > 0 then howHit:SetHeight(hh + 6) end
  howHit:EnableMouse(true)
  U.Tip(howHit, function(tt)
    local n, count = slotOdds()
    local rtp = TCF:SlotsExactRTP()
    tt:AddLine("Lucky Paws slots", 1, 0.82, 0)
    tt:AddLine("Three reels of 20 symbols. Only the middle line counts.", 1, 1, 1, true)
    tt:AddLine(" ")
    for _, s in ipairs(TCF.SLOT_ORDER) do
      local c = count[s] or 0
      tt:AddDoubleLine("Three " .. SYM_PLURAL[s], string.format("%dx   (1 in %s)", TCF.SLOT_PAY3[s], TCF.Commas(floor(n / max(1, c) + 0.5))), 1, 1, 1, 1, 0.82, 0)
    end
    tt:AddDoubleLine("Two cats", string.format("%dx   (1 in %d)", TCF.SLOT_PAY_TWO_CATS, floor(n / max(1, count.twocats or 1) + 0.5)), 1, 1, 1, 1, 0.82, 0)
    tt:AddDoubleLine("One cat", string.format("%dx   (1 in %d)", TCF.SLOT_PAY_ONE_CAT, floor(n / max(1, count.onecat or 1) + 0.5)), 1, 1, 1, 1, 0.82, 0)
    tt:AddLine(" ")
    tt:AddLine(string.format("Over many spins the machine pays back about %.1f%% of what is bet: the house keeps %.1f%%.", rtp * 100, 100 - rtp * 100), 0.8, 0.8, 0.8, true)
    tt:AddLine("The pays include your bet: 2x on a bet of 50 hands back 100, so you win 50.", 0.8, 0.8, 0.8, true)
  end)
  -- the pay table
  local rows = {}
  local function payRow(i, syms, mult)
    local y = 86 + (i - 1) * 25
    for k = 1, 3 do
      local t
      if syms[k] then t = tex(box, TCF.SLOT_SYMBOLS[syms[k]].art, 22, 22)
      else t = tex(box, "bulb", 10, 10); t:SetVertexColor(0.6, 0.55, 0.7) end
      at(t, box, RX + 12 + (k - 1) * 24, y + 11)
    end
    local txt = U.Text(box, "GameFontHighlight", string.format("|cffffd100%dx|r  your bet", mult), "LEFT")
    at(txt, box, RX + 82, y + 11, "LEFT")
    rows[i] = txt
  end
  for i, s in ipairs(TCF.SLOT_ORDER) do payRow(i, { s, s, s }, TCF.SLOT_PAY3[s]) end
  payRow(8, { "cat", "cat" }, TCF.SLOT_PAY_TWO_CATS)
  payRow(9, { "cat" }, TCF.SLOT_PAY_ONE_CAT)
  local anyNote = U.Text(box, "GameFontHighlightSmall", "Cats pay anywhere on the line.", "LEFT"); at(anyNote, box, RX + 12, 314, "TOPLEFT")
  anyNote:SetTextColor(0.75, 0.72, 0.85)

  -- the cat (your own look) cheers you on
  local cat = TCF.CreateCat(box, 128, { preview = true })
  at(cat.frame, box, 790, 190)
  S.cat = cat

  local result = U.Text(box, "GameFontNormalLarge", "", "LEFT"); at(result, box, RX, 334, "TOPLEFT"); result:SetWidth(390)
  S.result = result
  local bet = TCF.UI.CasinoBetChooser(box, function() cv:Refresh(true) end); at(bet, box, RX, 368, "TOPLEFT")
  S.bet = bet
  local spin = U.Button(box, "Spin", 140, 34, function() S:Spin() end); at(spin, box, RX + 248, 378, "TOPLEFT")
  S.spinBtn = spin

  ------------------------------------------------ drawing the reels
  local function drawReel(r)
    local reel, pos = S.reels[r], S.pos[r]
    local idx = floor(pos)
    local frac = pos - idx
    for k = -2, 2 do
      local t = reel.cells[k]
      local sym = TCF.SlotSymbol(r, idx + k)
      if t.sym ~= sym then t.sym = sym; t:SetTexture(CART .. TCF.SLOT_SYMBOLS[sym].art) end
      local size = 64
      if t.bounce and k == 0 then size = 64 * (1 + 0.12 * abs(sin(t.bounce * 7))) end
      t:SetSize(size, size)
      at(t, reel.clip, WIN_W / 6, WIN_H / 2 + (k - frac) * ROW)
    end
  end
  for r = 1, 3 do drawReel(r) end

  local function bulbsUpdate(mode, t)
    for _, b in ipairs(bulbs) do
      local on
      if mode == "big" then on = floor(t * 8) % 2 == 0
      elseif mode == "spin" then on = (b.i + floor(t * 12)) % 3 == 0
      else on = (b.i + floor(t * 2)) % 2 == 0 end
      if on then b:SetVertexColor(1, 0.86, 0.3) else b:SetVertexColor(0.55, 0.32, 0.3) end
    end
  end

  -- where reel r is t seconds into the spin (rows; the strip moves down, so the position falls)
  local function reelPos(r, t)
    local from, T1, P = S.from[r], S.t1[r], S.to[r]
    if t < T1 then return from - REEL_SPEED * t end
    local q = t - T1
    if q < REEL_EASE then
      local e = q / REEL_EASE
      return from - REEL_SPEED * T1 - (REEL_SPEED * REEL_EASE / 3) * (1 - (1 - e) ^ 3)
    end
    q = q - REEL_EASE
    if q < REEL_BOUNCE then return P - BOUNCE_ROWS * sin(pi * q / REEL_BOUNCE) end
    return P
  end
  S.ReelPos = reelPos

  function S:Spin()
    if self.spinning then self:StopNow(); return end
    local c = TCF:CasinoData()
    local lo, hi = TCF:CasinoLimits()
    if hi < lo then
      result:SetText("|cffff7070You need at least " .. TCF.CASINO_MIN_COINS .. " TapCoins to play.|r"); return
    end
    local res = TCF:SlotsSpin(TCF:CasinoClampBet(c.bet or lo))
    if not res then result:SetText("|cffff7070That bet can't be taken right now.|r"); return end
    self.res, self.spinning, self.t, self.stopped = res, true, 0, {}
    self.from, self.to, self.t1, self.stopAt = {}, {}, {}, {}
    -- each reel runs at full speed, eases into its stop and bounces a little; the travel is the
    -- shortest that lands on the result no sooner than FIRST_STOP (and REEL_GAP after the last reel)
    local easeRows = REEL_SPEED * REEL_EASE / 3
    local earliest = FIRST_STOP
    for r = 1, 3 do
      local n = #TCF.SLOT_REELS[r]
      local start = self.pos[r]
      local dist = (start - res.stops[r]) % n
      local need = easeRows + REEL_SPEED * max(0, earliest - REEL_EASE)
      while dist < need do dist = dist + n end
      self.from[r], self.to[r] = start, start - dist
      self.t1[r] = (dist - easeRows) / REEL_SPEED
      self.stopAt[r] = self.t1[r] + REEL_EASE
      earliest = self.stopAt[r] + REEL_GAP
      for k = -2, 2 do self.reels[r].cells[k].bounce = nil end
    end
    self.endAt = self.stopAt[3] + REEL_BOUNCE
    glow:Hide()
    result:SetText("")
    self.leverT = 0
    if cat.Tap then cat:Tap("R") end
    TCF:PlaySound("click")
    cv:Refresh(true)
  end

  -- the reels land: pay, then the show
  function S:Land(quiet)
    self.spinning = false
    local res = self.res
    for r = 1, 3 do self.pos[r] = res.stops[r]; drawReel(r) end
    local paid = TCF:CasinoCollect("slots")
    local win = res.win
    if win > 0 then
      local s1 = res.symbols[1]
      local what = res.kind == "three" and ("Three " .. SYM_PLURAL[s1]) or res.kind == "twocats" and "Two cats" or "One cat"
      result:SetText(string.format("|cffffd100%s. You win %s TapCoins|r", what, TCF.Commas(win - res.bet)))
      for r = 1, 3 do if res.kind == "three" or res.symbols[r] == "cat" then self.reels[r].cells[0].bounce = 0 end end
      self.glowT = 0; glow:Show()
      if not quiet then
        local big = res.mult >= TCF.SLOT_BIG_WIN
        local tx, ty = MACHINE_X + 210, CH - (MACHINE_Y + 376)
        if big then
          burst:Emit(tx, ty, 34, 1.25, true)
          burst:Emit(MACHINE_X + WIN_X + WIN_W / 2, CH - (MACHINE_Y + WIN_Y + WIN_H / 2), 16, 1.1, true)
          banner:Play(res.mult >= 100 and "Jackpot" or "Big win", "+" .. TCF.Commas(win - res.bet) .. " TapCoins")
          self.bigT = 0
          cat:SetFaceFor("sparkle", 3); if cat.Pet then cat:Pet() end
          TCF:PlaySound(res.mult >= 40 and "legendary" or "rare")
        else
          burst:Emit(tx, ty, res.mult >= 5 and 14 or 7, 0.85)
          cat:SetFaceFor("happy", 2)
          TCF:PlaySound("loot")
        end
      end
    else
      result:SetText("|cffbbbbbbNo win this time.|r")
    end
    cv:Refresh(true)
    return paid
  end

  -- Stop (or a click on the reels): every reel lands now, with one click
  function S:StopNow()
    if not self.spinning then return end
    self.t = self.endAt
    for r = 1, 3 do self.stopped[r] = true end
    TCF:PlaySound("click")
  end

  -- the tab or the window closes mid-spin: land at once and pay
  function S:Finish()
    if self.spinning then self:Land(true) end
    burst:Clear(); banner:Hide(); self.leverT = nil; setLever(0)
  end

  box:SetScript("OnUpdate", function(_, e)
    S.clock = (S.clock or 0) + e
    if S.leverT then
      S.leverT = S.leverT + e
      local p = S.leverT / 0.5
      setLever(p < 0.4 and easeOut(p / 0.4) or p < 1 and 1 - easeOut((p - 0.4) / 0.6) or 0)
      if p >= 1 then S.leverT = nil end
    end
    if S.spinning then
      S.t = S.t + e
      for r = 1, 3 do
        S.pos[r] = reelPos(r, S.t)
        -- each reel lands with a click
        if S.t >= S.stopAt[r] and not S.stopped[r] then S.stopped[r] = true; TCF:PlaySound("click") end
        drawReel(r)
      end
      if S.t >= S.endAt then S:Land(false) end
    end
    -- the winning symbols bounce and the line glows for a while
    if S.glowT then
      S.glowT = S.glowT + e
      glow:SetAlpha(0.45 + 0.4 * sin(S.glowT * 6))
      for r = 1, 3 do
        local c0 = S.reels[r].cells[0]
        if c0.bounce then c0.bounce = c0.bounce + e; drawReel(r) end
      end
      if S.glowT > 2.4 then
        S.glowT = nil; glow:Hide()
        for r = 1, 3 do S.reels[r].cells[0].bounce = nil; drawReel(r) end
      end
    end
    if S.bigT then S.bigT = S.bigT + e; if S.bigT > 3 then S.bigT = nil end end
    bulbsUpdate(S.bigT and "big" or S.spinning and "spin" or "idle", S.clock)
    burst:Update(e)
    banner:Update(e)
    -- the banner sits on the marquee: its name comes back when the banner is gone
    local free = not banner:IsShown()
    if marquee:IsShown() ~= free then marquee:SetShown(free) end
  end)

  function S:Refresh(light)
    local lo, hi = TCF:CasinoLimits()
    self.bet:SetLocked(self.spinning)
    self.bet:Refresh()
    if hi >= lo then spin:Enable() else spin:Disable() end
    spin:SetText(self.spinning and "Stop" or "Spin")
    if not light then cat:ApplyAppearance(TCF:GetAppearance()) end
  end
  return S
end

---------------------------------------------------------------- blackjack
local CARD_W, CARD_H = 72, 101
local SHOE_X, SHOE_Y = 790, 64
local RED, BLACK = { 0.86, 0.2, 0.28 }, { 0.18, 0.15, 0.26 }

local function Card(parent)
  local c = CreateFrame("Frame", nil, parent)
  c:SetSize(CARD_W, CARD_H)
  local sh = tex(c, "card_face", nil, nil, "BACKGROUND"); sh:SetPoint("TOPLEFT", 3, -4); sh:SetPoint("BOTTOMRIGHT", 3, -4)
  sh:SetTexCoord(0, 1, 0, 180 / 256); sh:SetVertexColor(0, 0, 0); sh:SetAlpha(0.3)
  c.face = tex(c, "card_face", nil, nil, "BORDER"); c.face:SetAllPoints(); c.face:SetTexCoord(0, 1, 0, 180 / 256)
  c.back = tex(c, "card_back", nil, nil, "BORDER", 1); c.back:SetAllPoints(); c.back:SetTexCoord(0, 1, 0, 180 / 256)
  c.rank = c:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge"); c.rank:SetPoint("TOPLEFT", 8, -7)
  c.rank2 = c:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge"); c.rank2:SetPoint("BOTTOMRIGHT", -8, 7)
  for _, fs in ipairs({ c.rank, c.rank2 }) do if fs.SetShadowOffset then fs:SetShadowOffset(0, 0) end end
  c.small = tex(c, nil, 13, 13, "OVERLAY"); c.small:SetPoint("TOPLEFT", 7, -26)
  c.big = tex(c, nil, 40, 40, "ARTWORK"); c.big:SetPoint("CENTER", 0, -2)
  function c:Set(code, up)
    self.code = code
    local r, s = TCF.BJCard(code)
    local col = (s == 2 or s == 4) and RED or BLACK
    local rk = TCF.BJ_RANKS[r]
    for _, fs in ipairs({ self.rank, self.rank2 }) do fs:SetText(rk); fs:SetTextColor(col[1], col[2], col[3]) end
    local suit = "suit_" .. TCF.BJ_SUITS[s]
    self.small:SetTexture(CART .. suit)
    if r >= 11 then
      -- the court cat sits a little low and right, clear of the corner rank and suit
      self.big:SetTexture(CART .. (r == 11 and "court_j" or r == 12 and "court_q" or "court_k")); self.big:SetSize(54, 54)
      self.big:ClearAllPoints(); self.big:SetPoint("CENTER", 4, -8)
    else
      self.big:SetTexture(CART .. suit); local sz = r == 1 and 46 or 36; self.big:SetSize(sz, sz)
      self.big:ClearAllPoints(); self.big:SetPoint("CENTER", 0, -2)
    end
    self:Face(up)
  end
  function c:Face(up)
    self.up = up
    self.back:SetShown(not up); self.face:SetShown(up)
    for _, r in ipairs({ self.rank, self.rank2, self.small, self.big }) do r:SetShown(up) end
  end
  return c
end

local function BlackjackView(box, cv)
  local U = TCF.UI
  local B = { cards = {}, planned = {}, queue = {}, pool = {} }
  local bg = tex(box, "felt", CW, CH, "BACKGROUND"); bg:SetAllPoints()
  local shoe = tex(box, "shoe", 96, 96, "BORDER"); at(shoe, box, SHOE_X, SHOE_Y)
  local table_ = CreateFrame("Frame", nil, box); table_:SetAllPoints(); level(table_, box, 2)
  B.table = table_
  local rules = U.Text(box, "GameFontNormal", "Blackjack pays 3 to 2      Dealer stands on soft 17")
  at(rules, box, CW / 2, 178); rules:SetTextColor(0.75, 0.95, 0.82); rules:SetAlpha(0.8)
  local dealerLabel = U.Text(box, "GameFontHighlight", "Dealer"); at(dealerLabel, box, 396, 22)
  local resultFrame = CreateFrame("Frame", nil, box); resultFrame:SetAllPoints(); level(resultFrame, box, 30)
  local result = U.Text(resultFrame, "GameFontNormalHuge", ""); at(result, box, CW / 2, 206)
  B.result = result
  local labels, marks = {}, {}
  for h = 1, 2 do
    labels[h] = U.Text(box, "GameFontHighlight", ""); marks[h] = tex(box, "sparkle", 22, 22, "OVERLAY")
    marks[h]:Hide()
  end
  local cat = TCF.CreateCat(box, 120, { preview = true }); at(cat.frame, box, 92, 286)
  B.cat = cat
  local burst = Burst(box)
  -- the blackjack banner takes the result line's place while it shows (the line comes back after)
  local banner = Banner(box, CW / 2, 176)   -- between the dealer's cards and yours
  level(banner, box, 250); level(burst.layer, box, 240)

  local bet = TCF.UI.CasinoBetChooser(box, function() cv:Refresh(true) end); at(bet, box, 24, 376, "TOPLEFT")
  B.bet = bet
  local deal = U.Button(box, "Deal", 150, 34, function() B:Deal() end); at(deal, box, 470, 384, "TOPLEFT")
  local btns = {}
  for i, a in ipairs({ { "hit", "Hit" }, { "stand", "Stand" }, { "double", "Double" }, { "split", "Split" } }) do
    local b = U.Button(box, a[2], 86, 30, function() B:Action(a[1]) end)
    at(b, box, 300 + (i - 1) * 92, 386, "TOPLEFT")
    btns[a[1]] = b
  end
  U.Tip(btns.double, function(tt) tt:AddLine("Double", 1, 0.82, 0); tt:AddLine("Double your bet and take exactly one more card.", 1, 1, 1, true) end)
  U.Tip(btns.split, function(tt) tt:AddLine("Split", 1, 0.82, 0); tt:AddLine("Split the pair into two hands, each with its own bet (once per hand). Split aces get one card each.", 1, 1, 1, true) end)
  B.deal, B.btns = deal, btns
  local how = U.Text(box, "GameFontHighlightSmall", "|cffffd100How it works:|r get closer to 21 than the dealer without going over. Hover here for the rules.", "LEFT")
  at(how, box, 300, 428, "TOPLEFT"); how:SetWidth(470)
  local howHit = CreateFrame("Frame", nil, box); howHit:SetSize(470, 18); at(howHit, box, 300, 424, "TOPLEFT"); howHit:EnableMouse(true)
  U.Tip(howHit, function(tt)
    tt:AddLine("Blackjack", 1, 0.82, 0)
    for _, l in ipairs({
      "Get closer to 21 than the dealer without going over. Picture cards count 10, aces 1 or 11.",
      "A win pays 1 to 1. A blackjack (an ace and a 10 card as your first two cards) pays 3 to 2 (half a TapCoin is rounded down).",
      "A tie is a push: you get your bet back.",
      "The dealer draws to 17 and stands on every 17, soft 17 too. The dealer checks for blackjack first.",
      "Double: double your bet on your first two cards and take one more card.",
      "Split: split a pair into two hands once. Split aces get one card each.",
      "No insurance. Six decks, shuffled again when a quarter of the shoe is left.",
      "With perfect play the house keeps about half a percent.",
      "A hand in play waits for you if you close the window.",
    }) do tt:AddLine(l, 1, 1, 1, true) end
  end)

  ------------------------------------------------ card positions
  -- 50 px apart, closer after the fifth card, so long hands stay clear of the shoe and of the
  -- other split hand
  local function fan(i) return i <= 5 and (i - 1) * 50 or 200 + (i - 5) * 26 end
  B.fan = fan
  local function posOf(key)
    local who, h, i = key:match("^(%a)(%d)c(%d+)$")
    if not who then who, i = "d", key:match("^d(%d+)$"); h = 0 end
    h, i = tonumber(h), tonumber(i)
    if who == "d" then return 360 + fan(i), 36 end
    local x0 = B.split and (h == 1 and 160 or 500) or 360
    return x0 + fan(i), 226
  end
  local function newCard()
    local c = table.remove(B.pool) or Card(table_)
    c:Show(); c:SetWidth(CARD_W)
    return c
  end
  local z = 0
  local function place(c, x, y) c.x, c.y = x, y; c:ClearAllPoints(); c:SetPoint("TOPLEFT", table_, "TOPLEFT", x, -y) end
  local function moveTo(c, key, dur)
    local x, y = posOf(key)
    if dur <= 0 then c.anim = nil; place(c, x, y); return end
    c.anim = { fx = c.x or x, fy = c.y or y, tx = x, ty = y, t = 0, dur = dur }
  end

  function B:Clear()
    z = 0
    for k, c in pairs(self.cards) do c:Hide(); c.anim, c.flip = nil, nil; table.insert(self.pool, c); self.cards[k] = nil end
    self.planned, self.queue, self.cur = {}, {}, nil
    self.split, self.holeUp, self.resultShown, self.shownId = false, false, false, nil
    self.plannedSplit, self.plannedHole, self.plannedResult = false, false, false
    result:SetText("")
  end

  local function push(step) table.insert(B.queue, step) end

  -- compare what the table shows with the hand in Casino.lua and queue what is missing
  function B:Sync(animate)
    local st = TCF:BJState()
    if not st then self:Clear(); self:Labels(); return end
    if st.id ~= self.shownId then
      self:Clear()
      self.shownId = st.id
      local h1 = st.hands[1].cards
      -- a split hand starts from its first two cards
      local first = st.split and { h1[1], st.hands[2].cards[1] } or { h1[1], h1[2] }
      for _, s in ipairs({ { "h1c1", first[1], true }, { "d1", st.dealer[1], true }, { "h1c2", first[2], true }, { "d2", st.dealer[2], false } }) do
        push({ kind = "deal", key = s[1], code = s[2], up = s[3], dur = 0.32 }); self.planned[s[1]] = true
      end
    end
    if #st.hands == 2 and not self.plannedSplit then
      self.plannedSplit = true
      push({ kind = "split", dur = 0.35 }); self.planned.h1c2 = nil; self.planned.h2c1 = true
    end
    for h, hand in ipairs(st.hands) do
      for i, code in ipairs(hand.cards) do
        local key = "h" .. h .. "c" .. i
        if not self.planned[key] then push({ kind = "deal", key = key, code = code, up = true, dur = 0.32 }); self.planned[key] = true end
      end
    end
    if st.holeShown and not self.plannedHole then
      self.plannedHole = true
      push({ kind = "flip", dur = 0.4 })
    end
    for i = 3, #st.dealer do
      local key = "d" .. i
      if not self.planned[key] then
        push({ kind = "wait", dur = 0.35 })
        push({ kind = "deal", key = key, code = st.dealer[i], up = true, dur = 0.32 }); self.planned[key] = true
      end
    end
    if st.phase == "done" and not self.plannedResult then
      self.plannedResult = true
      push({ kind = "result", dur = 0, quiet = not animate })
    end
    if not animate then self:RunAll() end
    self:Labels()
  end

  local function startStep(s, instant)
    local d = instant and 0 or s.dur
    if s.kind == "deal" then
      local c = newCard()
      c:Set(s.code, s.up)
      z = z + 1; level(c, table_, min(z, 30) + 1)
      B.cards[s.key] = c
      if d > 0 then place(c, SHOE_X - CARD_W / 2 - 10, SHOE_Y - CARD_H / 2 - 6); TCF:PlaySound("click") end
      moveTo(c, s.key, d)
    elseif s.kind == "split" then
      B.split = true
      B.cards.h2c1, B.cards.h1c2 = B.cards.h1c2, nil
      for k, c in pairs(B.cards) do if k:sub(1, 1) == "h" then moveTo(c, k, d) end end
    elseif s.kind == "flip" then
      B.holeUp = true
      local c = B.cards.d2
      if c then
        if d > 0 then c.flip = { t = 0, dur = d } else c:Face(true) end
      end
    elseif s.kind == "result" then
      B:ShowResult(s.quiet or instant)
    end
  end

  local function endStep(s)
    if s.kind == "flip" and B.cards.d2 then local c = B.cards.d2; c.flip = nil; c:SetWidth(CARD_W); c:Face(true) end
    if s.kind == "deal" or s.kind == "split" then
      for k, c in pairs(B.cards) do if c.anim then c.anim.t = c.anim.dur end end
    end
    B:Labels()
  end

  -- everything left at once (reopened window, the tab closing)
  function B:RunAll()
    if self.cur then endStep(self.cur); self.cur = nil end
    while #self.queue > 0 do
      local s = table.remove(self.queue, 1)
      startStep(s, true); endStep(s)
    end
    for k, c in pairs(self.cards) do
      if c.anim then local a = c.anim; place(c, a.tx, a.ty); c.anim = nil end
      if c.flip then c.flip = nil; c:SetWidth(CARD_W); c:Face(true) end
    end
    self:Labels()
  end

  function B:Busy() return self.cur ~= nil or #self.queue > 0 end

  function B:ShowResult(quiet)
    local st = TCF:BJState()
    if not st then return end
    TCF:CasinoCollect("blackjack")
    self.resultShown = true
    local net = (st.pay or 0) - (st.staked or 0)
    result:SetText(st.text or "")
    result:Show(); rules:Show()
    if net > 0 then result:SetTextColor(1, 0.85, 0.2) elseif net < 0 then result:SetTextColor(1, 0.55, 0.5) else result:SetTextColor(0.9, 0.9, 0.9) end
    if quiet or net <= 0 then return end
    local hx = B.split and 430 or 400
    local bj = st.natural == "player"
    burst:Emit(hx, CH - 270, bj and 26 or min(24, 8 + floor(net / max(1, st.bet) * 6)), bj and 1.1 or 0.9, bj)
    if bj then
      -- the banner shows in the result line's place; the line (and the rules) come back after it
      banner:Play("Blackjack", "You win " .. TCF.Commas(net) .. " TapCoins")
      result:Hide(); rules:Hide()
    end
    cat:SetFaceFor(bj and "sparkle" or "happy", 2.5); if cat.Pet then cat:Pet() end
    TCF:PlaySound(bj and "rare" or "loot")
  end

  -- hand totals and the dealer's, from the cards on the table
  local function totalText(codes, natural)
    if #codes == 0 then return "" end
    local t, soft = TCF.BJTotal(codes)
    if t > 21 then return "|cffff7070Bust|r" end
    if natural then return "|cffffd100Blackjack|r" end
    if soft and t < 21 then return "Soft " .. t end
    return tostring(t)
  end
  function B:Labels()
    local st = TCF:BJState()
    local d = {}
    for i = 1, 12 do
      local c = self.cards["d" .. i]
      if c and (i ~= 2 or self.holeUp) then d[#d + 1] = c.code end
    end
    dealerLabel:SetText(#d > 0 and ("Dealer   " .. totalText(d, self.holeUp and #d == 2 and st and st.natural and st.natural ~= "player" and TCF.BJTotal(d) == 21)) or "Dealer")
    for h = 1, 2 do
      local codes = {}
      for i = 1, 12 do local c = self.cards["h" .. h .. "c" .. i]; if c then codes[#codes + 1] = c.code end end
      local hand = st and st.hands[h]
      if #codes > 0 and hand then
        local x = (self.split and (h == 1 and 160 or 500) or 360) + (CARD_W + fan(#codes)) / 2
        at(labels[h], box, x, 342)
        labels[h]:SetText(totalText(codes, st.natural == "player" or st.natural == "both" and h == 1) ..
          "   |cffbbbbbb" .. TCF.UI.coinStr(hand.bet, 12) .. (hand.doubled and " (doubled)" or "") .. "|r")
        labels[h]:Show()
        local active = st.phase == "player" and #st.hands == 2 and st.active == h and not self:Busy()
        marks[h]:SetShown(active)
        if active then at(marks[h], box, x, 216) end
      else
        labels[h]:Hide(); marks[h]:Hide()
      end
    end
  end

  function B:Deal()
    if self:Busy() or TCF:BJInPlay() then return end
    local c = TCF:CasinoData()
    local lo, hi = TCF:CasinoLimits()
    if hi < lo then result:SetText("You need at least " .. TCF.CASINO_MIN_COINS .. " TapCoins to play."); result:SetTextColor(1, 0.55, 0.5); return end
    -- the last hand's win is paid before the next deal
    TCF:CasinoCollect("blackjack")
    banner:Hide(); result:Show(); rules:Show()
    local st = TCF:BJDeal(TCF:CasinoClampBet(c.bet or lo))
    if not st then result:SetText("That bet can't be taken right now."); result:SetTextColor(1, 0.55, 0.5); return end
    self:Sync(true)
    if st.shuffled and not st.text then result:SetText("A fresh shoe."); result:SetTextColor(0.8, 0.95, 0.85) end
    cv:Refresh(true)
  end

  function B:Action(a)
    if self:Busy() then return end
    local ok
    if a == "hit" then ok = TCF:BJHit()
    elseif a == "stand" then ok = TCF:BJStand()
    elseif a == "double" then ok = TCF:BJDouble()
    elseif a == "split" then ok = TCF:BJSplit() end
    if ok then TCF:PlaySound("click"); self:Sync(true) end
    cv:Refresh(true)
  end

  function B:Finish()
    self:RunAll()
    burst:Clear(); banner:Hide(); result:Show(); rules:Show()
  end

  box:SetScript("OnUpdate", function(_, e)
    -- card movement and flips
    for _, c in pairs(B.cards) do
      local a = c.anim
      if a then
        a.t = min(a.dur, a.t + e)
        local p = easeOut(a.t / a.dur)
        place(c, a.fx + (a.tx - a.fx) * p, a.fy + (a.ty - a.fy) * p)
        if a.t >= a.dur then c.anim = nil end
      end
      local f = c.flip
      if f then
        f.t = min(f.dur, f.t + e)
        local p = f.t / f.dur
        c:SetWidth(max(1, CARD_W * abs(cos(p * pi))))
        if p >= 0.5 and not c.up then c:Face(true); c.rank:Hide(); c.rank2:Hide(); c.small:Hide(); c.big:Hide() end
        if p >= 1 then c.flip = nil; c:SetWidth(CARD_W); c:Face(true) end
      end
    end
    -- the queue of deals, flips and the result
    if not B.cur and #B.queue > 0 then
      B.cur = table.remove(B.queue, 1); B.cur.t = 0
      startStep(B.cur, false)
    end
    if B.cur then
      B.cur.t = B.cur.t + e
      if B.cur.t >= B.cur.dur then
        local s = B.cur; B.cur = nil
        endStep(s)
        if not B:Busy() then cv:Refresh(true) end
      end
    end
    burst:Update(e)
    banner:Update(e)
    if not banner:IsShown() and not result:IsShown() then result:Show(); rules:Show() end
  end)

  function B:Refresh(light)
    local inPlay = TCF:BJInPlay()
    local busy = self:Busy()
    -- a hand that changed while the tab was closed (or a reload): show it as it is now
    if not busy then
      local st = TCF:BJState()
      if (st and st.id ~= self.shownId) or (not st and self.shownId) then
        local old = st and st.phase == "done" and st.collected
        self:Sync(false)
        -- a hand that ended (and was paid) long ago shows its cards without the old result
        if old then result:SetText("") end
      elseif st and st.phase == "done" and not self.resultShown and not self.plannedResult then
        self:Sync(false)
      end
    end
    self.bet:SetLocked(inPlay or busy)
    self.bet:Refresh()
    local lo, hi = TCF:CasinoLimits()
    deal:SetShown(not inPlay)
    if not busy and hi >= lo then deal:Enable() else deal:Disable() end
    for a, b in pairs(btns) do
      b:SetShown(inPlay)
      local can = not busy and (a == "hit" and TCF:BJCanHit() or a == "stand" and inPlay or a == "double" and TCF:BJCanDouble() or a == "split" and TCF:BJCanSplit())
      if can then b:Enable() else b:Disable() end
    end
    self:Labels()
    if not light then cat:ApplyAppearance(TCF:GetAppearance()) end
  end
  return B
end

---------------------------------------------------------------- the tab
TCF.UI.Builders.casino = function(page, win)
  local U = TCF.UI
  -- the page covers the whole window under the tabs, the profile column too
  local cv = U.Panel(page, 888, 494, 1)
  cv:ClearAllPoints(); cv:SetPoint("TOPLEFT", win, "TOPLEFT", 16, -106)
  level(cv, win, 60)
  cv:EnableMouse(true)
  TCF.casinoView = cv
  -- the sign where the profile cat's stage starts (left of the tabs)
  local sign = U.Panel(cv, 316, 60, 1)
  sign:ClearAllPoints(); sign:SetPoint("TOPLEFT", win, "TOPLEFT", 16, -46)
  level(sign, win, 60)
  sign:EnableMouse(true)
  cv.sign = sign   -- the window's compact layout moves and scales the sign with the table (UI_Window.lua)
  local plate = tex(sign, "sign", 300, 56, "ARTWORK"); plate:SetPoint("CENTER", 0, -1); plate:SetTexCoord(0, 1, 0.1, 1)
  local sTitle = U.Text(sign, "GameFontNormalLarge", "TapCat Casino"); sTitle:SetPoint("CENTER", 0, 5); sTitle:SetTextColor(1, 0.85, 0.3)
  local sSub = U.Text(sign, "GameFontHighlightSmall", "Just for fun"); sSub:SetPoint("TOP", sTitle, "BOTTOM", 0, -2)
  sSub:SetTextColor(0.85, 0.8, 0.95)
  local signBulbs = {}
  for i = 0, 9 do
    local b = tex(sign, "bulb", 9, 9, "OVERLAY"); b:SetPoint("CENTER", sign, "TOPLEFT", 30 + i * 28.5, -8)
    signBulbs[#signBulbs + 1] = b
  end

  local c = TCF:CasinoData()
  cv.view = c.view or "slots"
  -- sub-view buttons, the limits and the stats
  local VIEWS = { { "slots", "Slots" }, { "blackjack", "Blackjack" }, { "deathroll", "Death roll" } }
  local vbtns = {}
  for i, v in ipairs(VIEWS) do
    local b = U.Button(cv, v[2], 104, 24, function() cv:SetView(v[1]); TCF:PlaySound("click") end)
    b:SetPoint("TOPLEFT", 9 + (i - 1) * 108, -5)
    vbtns[v[1]] = b
  end
  local limits = U.Text(cv, "GameFontHighlightSmall", "", "LEFT"); limits:SetPoint("TOPLEFT", 346, -5); limits:SetWidth(534)
  local stats = U.Text(cv, "GameFontDisableSmall", "", "LEFT"); stats:SetPoint("TOPLEFT", 346, -19); stats:SetWidth(534)
  cv.limits, cv.stats = limits, stats
  local statsHit = CreateFrame("Frame", nil, cv); statsHit:SetSize(534, 28); statsHit:SetPoint("TOPLEFT", 346, -3); statsHit:EnableMouse(true)
  U.Tip(statsHit, function(tt)
    tt:AddLine("Casino stats", 1, 0.82, 0)
    for _, g in ipairs(TCF.CASINO_GAMES) do
      tt:AddLine(g.name, 1, 1, 1)
      tt:AddLine(TCF:CasinoStatsLine(g.key), 0.8, 0.8, 0.8, true)
    end
    tt:AddLine("All games", 1, 1, 1)
    tt:AddLine(TCF:CasinoStatsLine(nil), 0.8, 0.8, 0.8, true)
    tt:AddLine("Bets are at least 10 TapCoins and at most half your TapCoins.", 0.7, 0.7, 0.7, true)
  end)

  local function Area()
    local f = CreateFrame("Frame", nil, cv); f:SetSize(CW, CH); f:SetPoint("TOPLEFT", 9, -32)
    if f.SetClipsChildren then f:SetClipsChildren(true) end
    f:Hide()
    return f
  end
  local slotsBox, bjBox, drBox = Area(), Area(), Area()
  cv.slotsBox, cv.bjBox, cv.deathroll = slotsBox, bjBox, drBox
  cv.slots = SlotsView(slotsBox, cv)
  cv.bj = BlackjackView(bjBox, cv)
  -- the Death roll view (DeathRoll.lua / UI_DeathRoll.lua)
  local drRefresh
  if TCF.UI.CasinoDeathRoll then
    local ok, fn = pcall(TCF.UI.CasinoDeathRoll, drBox, win)
    if ok and type(fn) == "function" then drRefresh = fn
    elseif not ok then
      local err = U.Text(drBox, "GameFontRedSmall", "The death roll table could not be set up: " .. tostring(fn)); err:SetPoint("CENTER"); err:SetWidth(700)
    end
  else
    local soon = U.Text(drBox, "GameFontNormalLarge", "The death roll table is being built."); soon:SetPoint("CENTER")
  end

  local boxes = { slots = slotsBox, blackjack = bjBox, deathroll = drBox }
  function cv:SetView(v)
    if not boxes[v] then v = "slots" end
    -- leaving a game mid-animation finishes it (and pays)
    if self.view ~= v then
      if self.view == "slots" then self.slots:Finish() elseif self.view == "blackjack" then self.bj:Finish() end
    end
    self.view = v
    TCF:CasinoData().view = v
    for k, b in pairs(boxes) do b:SetShown(k == v) end
    for k, b in pairs(vbtns) do if k == v then b:LockHighlight() else b:UnlockHighlight() end end
    self:Refresh(false)
  end
  function cv:SetBet(n)
    TCF:CasinoData().bet = TCF:CasinoClampBet(n) or TCF.CASINO_MIN_BET
    self:Refresh(true)
  end
  function cv:StepBet(dir)
    local b = TCF:CasinoData().bet or TCF.CASINO_MIN_BET
    if dir > 0 then local s = stepFor(b); self:SetBet(floor(b / s) * s + s)
    else local s = stepFor(b - 1); self:SetBet(math.ceil(b / s) * s - s) end
  end
  function cv:Refresh(light)
    local lo, hi = TCF:CasinoLimits()
    if hi >= lo then
      limits:SetText(string.format("Bets: %s to %s TapCoins |cff999999(at most half your TapCoins)|r", lo, TCF.Commas(hi)))
    else
      limits:SetText("|cffff8080You need at least " .. TCF.CASINO_MIN_COINS .. " TapCoins to play: a bet is at most half your TapCoins.|r")
    end
    -- the Death roll view also plays rock paper scissors: the stats of the game on screen
    local key = self.view
    if key == "deathroll" and TCF.DR and TCF.DR.ViewGame then key = TCF.DR.ViewGame() end
    stats:SetText(TCF:CasinoStatsLine(key))
    if self.view == "slots" then self.slots:Refresh(light)
    elseif self.view == "blackjack" then self.bj:Refresh(light)
    elseif drRefresh then drRefresh(light) end
  end
  -- the tab or the window closes: finish any spin or deal and pay what it won
  cv:SetScript("OnHide", function()
    cv.slots:Finish(); cv.bj:Finish()
    TCF:CasinoCollect("slots"); TCF:CasinoCollect("blackjack"); TCF:CasinoCollect("rps")
  end)
  cv:SetScript("OnUpdate", function(_, e)
    cv.clock = (cv.clock or 0) + e
    for i, b in ipairs(signBulbs) do
      if (i + floor(cv.clock * 2.5)) % 2 == 0 then b:SetVertexColor(1, 0.86, 0.3) else b:SetVertexColor(0.55, 0.32, 0.3) end
    end
  end)
  cv:SetView(cv.view)
  return function(light) cv:Refresh(light) end
end
