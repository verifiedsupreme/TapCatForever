-- TapCatForever: the death roll scene (Casino tab > Death roll; the rules and money are in DeathRoll.lua).
-- A cartoon cat tavern: your cat on the left in its real look, the house cat or your friend's cat on
-- the right. Each roll pops up over the roller's head and the range in the middle shrinks; numbers
-- of 10 and below turn red and shake. On a 1 the loser spins and flops onto its back with X eyes, a
-- little ghost cat floats up, and a few seconds later it pops back up fine; the winner jumps in a
-- burst of confetti. Everything is drawn inside the window and animated from one OnUpdate with
-- preallocated pieces (no tables made per frame).
--
-- Also here: the one allowed pop-up during play, a tiny Accept/Decline prompt just above the screen
-- cat when a party member challenges you (it goes away after 60 seconds), for a death roll or a game
-- of rock paper scissors. The same scene plays rock paper scissors (RPS.lua) on a mountaintop: the
-- "Death roll / Rock paper scissors" switch under the top bar picks the game, and UI_RPS.lua adds
-- that game's parts (paw signs, pick buttons, its texts) to the scene.
local ADDON, TCF = ...
local floor, min, max, sin, cos, random, pi, abs = math.floor, math.min, math.max, math.sin, math.cos, math.random, math.pi, math.abs
local ART = TCF.ART_PATH .. "casino\\"
local DR = TCF.DR
local FONT = STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF"
local CONFETTI = 36
local CONF_COLORS = { { 1, 0.36, 0.36 }, { 1, 0.8, 0.2 }, { 0.35, 0.75, 1 }, { 0.5, 0.9, 0.4 }, { 1, 0.55, 0.85 }, { 0.75, 0.55, 1 } }
local HOW_W = 356   -- the How to play box: as wide as the gap between the two cats' roll bubbles
local NOTE_ROLL = "Rolls with a friend use the game's /roll, so they also show in chat for your group like a normal /roll."

local function now() return GetTime and GetTime() or 0 end
local function coins(n) return TCF.UI.coinStr(n, 13) end
local function safeName(n) return (tostring(n or "?"):gsub("|", "||")) end
-- a name without its realm ("Thrallbeard-ArgentDawn" -> "Thrallbeard"), for the scene's texts
local function shortName(n)
  if type(n) ~= "string" or TCF.IsSecret(n) then return "?" end
  return safeName(n:match("^[^%-]+") or n)
end

---------------------------------------------------------------- opening the death roll view
local function openView()
  if TCF.ShowCasino then TCF:ShowCasino("deathroll"); return end
  if TCF.CasinoData then TCF:CasinoData().view = "deathroll" end   -- the view a new Casino page opens on
  if not TCF.window and TCF.CreateWindow then TCF:CreateWindow() end
  local win = TCF.window
  if not win then return end
  win:Show()
  local idx = win.TAB_CASINO
  if not idx and win.tabNames then for i, n in ipairs(win.tabNames) do if n == "Casino" then idx = i end end end
  if idx and win.SelectTab then win:SelectTab(idx) end
  local cv = TCF.casinoView
  if cv and cv.SetView then cv:SetView("deathroll") end
end
DR.OpenView = openView

---------------------------------------------------------------- the prompt above the screen cat
-- the challenge waiting for your answer: "dr" (death roll) or "rps", and its game
local function pendingInvite()
  local d = DR.duel
  if d and d.state == "invited" then return "dr", d end
  local R = TCF.RPS
  local r = R and R.duel
  if r and r.state == "invited" then return "rps", r end
end
local function answer(kind, yes)
  if kind == "rps" then return TCF:RPSAnswer(yes) end
  return TCF:DeathRollAnswer(yes)
end

local prompt
local function buildPrompt()
  local U = TCF.UI
  local f = CreateFrame("Frame", "TapCatForeverDeathRollPrompt", UIParent, U.BT)
  f:SetSize(250, 64)
  f:SetFrameStrata("MEDIUM")
  if f.SetBackdrop then
    f:SetBackdrop(U.BACKDROP_PANEL)
    f:SetBackdropColor(0.08, 0.06, 0.1, 0.92); f:SetBackdropBorderColor(0.95, 0.75, 0.35, 1)
  end
  f:EnableMouse(true)
  if f.SetClampedToScreen then f:SetClampedToScreen(true) end
  f.text = U.Text(f, "GameFontHighlightSmall"); f.text:SetPoint("TOP", 0, -8); f.text:SetWidth(236)
  f.yes = U.Button(f, "Accept", 72, 20, function()
    local ok, err = answer(pendingInvite(), true)
    if err then TCF:Print(err, true) end
    TCF:PlaySound("click")
    if ok then openView() end
  end)
  f.yes:SetPoint("BOTTOMLEFT", 10, 8)
  f.no = U.Button(f, "Decline", 72, 20, function() answer(pendingInvite(), false); TCF:PlaySound("click") end)
  f.no:SetPoint("LEFT", f.yes, "RIGHT", 6, 0)
  f.left = U.Text(f, "GameFontDisableSmall", nil, "RIGHT"); f.left:SetPoint("BOTTOMRIGHT", -12, 12)
  local acc = 0
  f:SetScript("OnUpdate", function(self, e)
    acc = acc + e
    if acc < 0.25 then return end
    acc = 0
    local _, d = pendingInvite()
    if not d then self:Hide(); return end
    self.left:SetText(string.format("%d s", max(0, floor(d.expires - now()))))
  end)
  f:Hide()
  return f
end

local function placePrompt()
  prompt:ClearAllPoints()
  -- as tall as its text needs, so long names never run into the buttons
  local th = prompt.text.GetStringHeight and prompt.text:GetStringHeight()
  local h = (type(th) == "number" and th > 0) and floor(th + 0.5) + 40 or 64
  prompt:SetHeight(max(64, h))
  local hud = TCF.hud
  if hud and hud:IsShown() then
    -- above the screen cat, or below it when it sits too close to the top of the screen
    local top, ptop = hud.GetTop and hud:GetTop(), UIParent.GetTop and UIParent:GetTop()
    if type(top) == "number" and type(ptop) == "number" and top + 22 + h > ptop then
      prompt:SetPoint("TOP", hud, "BOTTOM", 0, -8)
    else
      prompt:SetPoint("BOTTOM", hud, "TOP", 0, 22)
    end
  else prompt:SetPoint("BOTTOM", UIParent, "BOTTOM", 0, 260) end
end

local function updatePrompt()
  local kind, d = pendingInvite()
  if not d then
    if prompt then prompt:Hide() end
    return
  end
  if not prompt then prompt = buildPrompt() end
  if kind == "rps" then
    prompt.text:SetText(string.format("%s challenges you to rock paper scissors\n%s each, best of 1",
      shortName(d.opp), coins(d.bet)))
  else
    prompt.text:SetText(string.format("%s challenges you to a death roll\n%s each, rolls from 1 to %s",
      shortName(d.opp), coins(d.bet), TCF.Commas(d.range)))
  end
  prompt.left:SetText(string.format("%d s", max(0, floor(d.expires - now()))))
  placePrompt()
  prompt:Show()
end
DR.UpdatePrompt = updatePrompt

---------------------------------------------------------------- the scene
local views = {}   -- built scenes (normally one)
DR.views = views

local function furColor(look)
  local f = look and (look.skin or look.fur)
  local c = f and f.c1
  if c then return c[1], c[2], c[3] end
  return 1, 0.72, 0.42
end

local function lookKey(look)
  local parts = {}
  for _, slot in ipairs({ "fur", "skin", "pattern", "head", "chest", "back", "acc", "main", "off" }) do
    local it = look[slot]
    parts[#parts + 1] = it and it.id or "-"
  end
  return table.concat(parts, ",")
end

local Scene = {}
Scene.__index = Scene

local function buildSide(v, side)
  local scene, CAT = v.scene, v.CAT
  local s = { side = side }
  local holder = CreateFrame("Frame", nil, scene)
  holder:SetSize(CAT, CAT)
  s.holder = holder
  s.cat = TCF.CreateCat(holder, CAT, { preview = true })
  s.cat.frame:SetPoint("BOTTOM", holder, "BOTTOM", 0, 0)
  -- the flop (a cat on its back: tinted fur, outlines, X eyes), all three turn together
  local lvl = scene.GetFrameLevel and scene:GetFrameLevel() or 1
  local fx = CreateFrame("Frame", nil, scene)
  fx:SetSize(CAT * 1.1, CAT * 1.1)
  if fx.SetFrameLevel then pcall(fx.SetFrameLevel, fx, lvl + 10) end
  s.fx = fx
  fx:SetSize(CAT, CAT)   -- the flop art is drawn on the cat's own 64-pixel grid (4 texels a pixel)
  local function layer(file, sub)
    local t = fx:CreateTexture(nil, "ARTWORK", nil, sub)
    t:SetAllPoints(fx); t:SetTexture(ART .. file); t:Hide()
    return t
  end
  s.flop = { layer("dr_flop_fur", 1), layer("dr_flop_line", 2), layer("dr_xeyes", 3) }
  s.ghost = fx:CreateTexture(nil, "OVERLAY")
  s.ghost:SetSize(CAT * 0.5, CAT * 0.5); s.ghost:SetTexture(ART .. "dr_ghost"); s.ghost:Hide()
  -- the roll number over the head
  local pop = CreateFrame("Frame", nil, scene)
  pop:SetSize(110, 92)
  if pop.SetFrameLevel then pcall(pop.SetFrameLevel, pop, lvl + 15) end
  pop.bg = pop:CreateTexture(nil, "ARTWORK"); pop.bg:SetAllPoints(pop); pop.bg:SetTexture(ART .. "dr_pop")
  pop.num = pop:CreateFontString(nil, "OVERLAY", "GameFontNormalHuge")
  pop.num:SetFont(FONT, 30, "")
  pop.num:SetPoint("CENTER", 0, 1)
  pop:Hide()
  s.pop = pop
  s.name = TCF.UI.Text(scene, "GameFontNormal"); s.name:SetPoint("TOP", holder, "BOTTOM", 0, -2)
  s.bet = TCF.UI.Text(scene, "GameFontHighlightSmall"); s.bet:SetPoint("TOP", s.name, "BOTTOM", 0, -1)
  s.name:SetShadowOffset(1, -1); s.bet:SetShadowOffset(1, -1)
  -- animation state
  s.hopT, s.popT, s.defeatT, s.winT = nil, nil, nil, nil
  return s
end

local function place(v)
  local cw, ch = v.cw, v.ch
  local floorY = floor(ch * 0.17)
  for _, s in ipairs({ v.L, v.R }) do
    local x = (s.side == "L" and -1 or 1) * cw * 0.27
    s.x, s.y = x, floorY
    s.holder:ClearAllPoints(); s.holder:SetPoint("BOTTOM", v.scene, "BOTTOM", x, floorY)
    s.fx:ClearAllPoints(); s.fx:SetPoint("CENTER", s.holder, "BOTTOM", 0, v.CAT * 0.3)
    s.ghost:ClearAllPoints(); s.ghost:SetPoint("CENTER", s.fx, "CENTER", 0, 0)
    s.pop:ClearAllPoints(); s.pop:SetPoint("BOTTOM", s.holder, "TOP", 0, 4)
  end
end

function TCF.UI.CasinoDeathRoll(container, win)
  local U = TCF.UI
  local v = setmetatable({ container = container, win = win }, Scene)
  local cw, ch = container:GetWidth(), container:GetHeight()
  if type(cw) ~= "number" or cw < 400 then cw = 870 end
  if type(ch) ~= "number" or ch < 300 then ch = 470 end
  v.cw, v.ch = cw, ch
  v.CAT = floor(min(170, ch * 0.36))
  local scene = CreateFrame("Frame", nil, container)
  scene:SetAllPoints(container)
  v.scene = scene
  -- background: the tavern (2:1), cropped to the container's shape (colosseum.tga is kept for a
  -- future duel mode)
  local bg = scene:CreateTexture(nil, "BACKGROUND")
  bg:SetAllPoints(scene); bg:SetTexture(ART .. "tavern")
  v.bg, v.bgName = bg, "tavern"
  local aspect = cw / ch
  if aspect < 2 then
    local cut = (1 - aspect / 2) / 2
    bg:SetTexCoord(cut, 1 - cut, 0, 1)
  else
    local cut = (1 - 2 / aspect) / 2
    bg:SetTexCoord(0, 1, cut, 1 - cut)
  end
  -- a soft dark strip along the floor so the names and text stay readable
  local strip = scene:CreateTexture(nil, "BORDER")
  strip:SetPoint("BOTTOMLEFT", 0, 0); strip:SetPoint("BOTTOMRIGHT", 0, 0); strip:SetHeight(floor(ch * 0.17) + 4)
  strip:SetColorTexture(0.12, 0.07, 0.04, 0.6)
  v.L, v.R = buildSide(v, "L"), buildSide(v, "R")
  place(v)

  -- confetti (on top of everything in the scene)
  local top = CreateFrame("Frame", nil, scene)
  top:SetAllPoints(scene)
  if top.SetFrameLevel and scene.GetFrameLevel then pcall(top.SetFrameLevel, top, (scene:GetFrameLevel() or 1) + 20) end
  v.top = top
  v.conf = {}
  for i = 1, CONFETTI do
    local t = top:CreateTexture(nil, "OVERLAY")
    t:SetTexture(ART .. "dr_conf" .. (i % 3 + 1)); t:SetSize(12, 12); t:Hide()
    local c = CONF_COLORS[i % #CONF_COLORS + 1]
    t:SetVertexColor(c[1], c[2], c[3])
    v.conf[i] = { tex = t, x = 0, y = 0, vx = 0, vy = 0, r = 0, vr = 0, age = 0, life = 0, on = false }
  end

  -- top bar: mode, friend, bet, range
  local bar = U.Panel(scene, cw - 16, 58, 0.72)
  bar:SetPoint("TOP", 0, -6)
  v.bar = bar
  v.modeHouse = U.Button(bar, "House cat", 96, 22, function() v:SetMode("house"); TCF:PlaySound("click") end)
  v.modeHouse:SetPoint("TOPLEFT", 8, -6)
  v.modeFriend = U.Button(bar, "Friend", 96, 22, function() v:SetMode("friend"); TCF:PlaySound("click") end)
  v.modeFriend:SetPoint("LEFT", v.modeHouse, "RIGHT", 4, 0)
  U.Tip(v.modeHouse, function(tt)
    tt:AddLine("Against the house cat", 1, 0.82, 0)
    tt:AddLine("A coin flip decides who rolls first. Win and you get 1.9 times your bet back.", 1, 1, 1, true)
  end)
  U.Tip(v.modeFriend, function(tt)
    tt:AddLine("Against a friend", 1, 0.82, 0)
    tt:AddLine("Challenge someone in your party or raid who has TapCatForever. You both bet the same amount. Whoever rolls the 1 loses it, and the winner gets the whole bet.", 1, 1, 1, true)
    tt:AddLine(NOTE_ROLL, 0.7, 0.85, 1, true)
  end)
  -- friend picker (friend mode)
  v.prev = U.Button(bar, "<", 24, 22, function() v.friendIdx = (v.friendIdx or 1) - 1; v:Refresh(true); TCF:PlaySound("click") end)
  v.prev:SetPoint("TOPLEFT", 8, -31)
  v.friend = U.Text(bar, "GameFontHighlight"); v.friend:SetPoint("LEFT", v.prev, "RIGHT", 4, 0); v.friend:SetWidth(144)
  if v.friend.SetWordWrap then v.friend:SetWordWrap(false) end
  v.next = U.Button(bar, ">", 24, 22, function() v.friendIdx = (v.friendIdx or 1) + 1; v:Refresh(true); TCF:PlaySound("click") end)
  v.next:SetPoint("LEFT", v.friend, "RIGHT", 4, 0)
  -- (1.6.0) whether the picked friend's addon can play: a short line just under the bar on the right
  v.friendState = U.Text(scene, "GameFontHighlightSmall", nil, "RIGHT")
  v.friendState:SetPoint("TOPRIGHT", scene, "TOPRIGHT", -12, -68)
  v.friendState:SetWidth(max(120, floor((cw - HOW_W) / 2) - 20))
  v.friendState:SetShadowOffset(1, -1)
  -- bet: the same chooser as the other Casino games (- / + and 10 / 50 / 100 / Max), the same bet
  if TCF.UI.CasinoBetChooser then
    v.chooser = TCF.UI.CasinoBetChooser(bar, function() v:Refresh() end)
    v.chooser:SetPoint("TOPLEFT", bar, "TOP", -126, -3)
  else
    v.betText = U.Text(bar, "GameFontHighlight"); v.betText:SetPoint("TOP", bar, "TOP", 0, -20)
  end
  -- roll range
  v.rangeLabel = U.Text(bar, "GameFontNormal"); v.rangeLabel:SetPoint("TOPRIGHT", bar, "TOPRIGHT", -60, -8)
  v.rangeLabel:SetText("Start the rolls at")
  v.rangeBtns = {}
  local prevBtn
  for i = #DR.RANGES, 1, -1 do
    local r = DR.RANGES[i]
    local b = U.Button(bar, TCF.Commas(r), 58, 20, function() v.range = r; v:Save(); v:Refresh(); TCF:PlaySound("click") end)
    if prevBtn then b:SetPoint("RIGHT", prevBtn, "LEFT", -2, 0) else b:SetPoint("TOPRIGHT", bar, "TOPRIGHT", -8, -30) end
    U.Tip(b, function(tt)
      tt:AddLine("Start at 1 to " .. TCF.Commas(r), 1, 0.82, 0)
      tt:AddLine("Higher numbers make longer games. The odds are the same.", 1, 1, 1, true)
    end)
    prevBtn = b
    v.rangeBtns[r] = b
  end

  -- middle: the current range, on a dark plate so it reads over the bar and its shelves
  v.plate = scene:CreateTexture(nil, "ARTWORK")
  v.plate:SetTexture(ART .. "dr_plate"); v.plate:SetSize(200, 100); v.plate:SetPoint("CENTER", scene, "CENTER", 0, 6)
  v.rangeCap = U.Text(scene, "GameFontNormal"); v.rangeCap:SetPoint("CENTER", scene, "CENTER", 0, 22)
  v.rangeCap:SetShadowOffset(1, -1)
  v.rangeNum = scene:CreateFontString(nil, "OVERLAY", "GameFontNormalHuge")
  v.rangeNum:SetFont(FONT, 34, "THICKOUTLINE"); v.rangeNum:SetPoint("CENTER", scene, "CENTER", 0, -8)

  -- How to play: a small box between the top bar and the plate, clear of the cats, their roll
  -- bubbles and the buttons; hovering it shows the same text as a tooltip
  local how = U.Panel(scene, HOW_W, 76, 0.8)
  how:SetPoint("TOP", scene, "TOP", 0, -68)
  how:EnableMouse(true)
  how.title = U.Text(how, "GameFontNormalSmall", "How to play", "LEFT"); how.title:SetPoint("TOPLEFT", 10, -7)
  how.body = U.Text(how, "GameFontHighlightSmall", "", "LEFT"); how.body:SetPoint("TOPLEFT", how.title, "BOTTOMLEFT", 0, -3)
  how.body:SetWidth(HOW_W - 20)
  if how.body.SetJustifyV then how.body:SetJustifyV("TOP") end
  U.Tip(how, function(tt)
    tt:AddLine("How to play", 1, 0.82, 0)
    for _, l in ipairs(v:HowTo()) do tt:AddLine(l, 1, 1, 1, true) end
  end)
  v.how = how

  -- the game: death roll in the tavern, or rock paper scissors on the mountaintop (UI_RPS.lua)
  v.gameDR = U.Button(scene, "Death roll", 90, 22, function() v:SetGame("dr"); TCF:PlaySound("click") end)
  v.gameDR:SetPoint("TOPLEFT", scene, "TOPLEFT", 8, -68)
  v.gameRPS = U.Button(scene, "Rock paper scissors", 140, 22, function() v:SetGame("rps"); TCF:PlaySound("click") end)
  v.gameRPS:SetPoint("LEFT", v.gameDR, "RIGHT", 4, 0)
  U.Tip(v.gameDR, function(tt)
    tt:AddLine("Death roll", 1, 0.82, 0)
    tt:AddLine("Take turns rolling, each roll 1 to the last number. Whoever rolls a 1 loses.", 1, 1, 1, true)
  end)
  U.Tip(v.gameRPS, function(tt)
    tt:AddLine("Rock paper scissors", 1, 0.82, 0)
    tt:AddLine("Pick rock, paper or scissors. Rock beats scissors, scissors beat paper, paper beats rock. A tie plays again.", 1, 1, 1, true)
  end)

  -- invite (when a friend challenges you)
  local inv = U.Panel(scene, 330, 78, 0.92)
  inv:SetPoint("CENTER", scene, "CENTER", 0, 10)
  if inv.SetFrameLevel and scene.GetFrameLevel then pcall(inv.SetFrameLevel, inv, (scene:GetFrameLevel() or 1) + 25) end
  inv.text = U.Text(inv, "GameFontHighlight"); inv.text:SetPoint("TOP", 0, -10); inv.text:SetWidth(310)
  inv.yes = U.Button(inv, "Accept", 90, 22, function()
    local _, err = answer(pendingInvite(), true)
    if err then v.msg = err end
    TCF:PlaySound("click"); v:Refresh(true)
  end)
  inv.yes:SetPoint("BOTTOM", inv, "BOTTOM", -50, 10)
  inv.no = U.Button(inv, "Decline", 90, 22, function() answer(pendingInvite(), false); TCF:PlaySound("click"); v:Refresh(true) end)
  inv.no:SetPoint("LEFT", inv.yes, "RIGHT", 10, 0)
  inv:Hide()
  v.inv = inv

  -- bottom: status, the big button, rules
  v.status = U.Text(scene, "GameFontHighlight"); v.status:SetPoint("BOTTOM", scene, "BOTTOM", 0, 44); v.status:SetWidth(floor(cw * 0.36))
  v.status:SetShadowOffset(1, -1)
  v.action = U.Button(scene, "Start", 170, 28, function() v:Action(); end)
  v.action:SetPoint("BOTTOM", scene, "BOTTOM", 0, 10)
  v.note = U.Text(scene, "GameFontHighlightSmall", nil, "LEFT"); v.note:SetPoint("BOTTOMLEFT", scene, "BOTTOMLEFT", 10, 6)
  v.note:SetWidth(max(160, cw * 0.27)); v.note:SetShadowOffset(1, -1); v.note:SetAlpha(0.85)
  v.note2 = U.Text(scene, "GameFontHighlightSmall", nil, "RIGHT"); v.note2:SetPoint("BOTTOMRIGHT", scene, "BOTTOMRIGHT", -10, 6)
  v.note2:SetWidth(max(160, cw * 0.27)); v.note2:SetShadowOffset(1, -1); v.note2:SetAlpha(0.85)

  -- saved choices
  local st = TCF.db.deathRoll
  if type(st) ~= "table" then st = {}; TCF.db.deathRoll = st end
  v.mode = (st.mode == "friend") and "friend" or "house"
  v.game = (st.game == "rps" and TCF.RPS and v.BuildRPS) and "rps" or "dr"
  if v.BuildRPS then v:BuildRPS() end
  v.range = tonumber(st.range) or DR.DEFAULT_RANGE
  -- the bet is shared with the other Casino games (TCF.db.casino.bet) when there is one
  local cd = TCF.CasinoData and TCF:CasinoData()
  v.bet = tonumber(cd and cd.bet) or tonumber(st.bet) or 50

  local acc = 0
  scene:SetScript("OnUpdate", function(_, e)
    v:Animate(e)
    acc = acc + e
    if acc >= 0.25 then acc = 0; v:Refresh() end
  end)
  scene:SetScript("OnShow", function() v:ResetAnims(); v:Refresh(true) end)
  views[#views + 1] = v
  v:Refresh(true)
  -- UI_Casino.lua calls this with light = true for its quick refreshes
  return function(light) v:Refresh(not light) end
end

function Scene:Save()
  local st = TCF.db.deathRoll
  if type(st) ~= "table" then st = {}; TCF.db.deathRoll = st end
  st.mode, st.range, st.bet, st.game = self.mode, self.range, self.bet, self.game
  if TCF.CasinoData then TCF:CasinoData().bet = self.bet end
end

function Scene:SetMode(m)
  if self:Locked() then return end
  self.mode = m
  self.msg = nil
  self:Save()
  self:Refresh(true)
end

function Scene:SetGame(g)
  if self:Locked() or (g == "rps" and not self.BuildRPS) then return end
  if self.game ~= g then
    self.game = g
    self:ResetAnims()
  end
  self.msg = nil
  self:Save()
  self:Refresh(true)
end

-- a game is running (either game): the mode and the game can't change
function Scene:Locked()
  if DR.Busy() then return true end
  local R = TCF.RPS
  return R and R.Busy() or false
end


function Scene:Friends()
  local list = {}
  for _, m in ipairs(TCF.PartyMembers and TCF:PartyMembers() or {}) do
    if not m.fake then list[#list + 1] = m end
  end
  return list
end

function Scene:Action()
  if self.game == "rps" and self.ActionRPS then return self:ActionRPS() end
  TCF:PlaySound("click")
  self.msg = nil
  local d = DR.duel
  local g, running = TCF:DeathRollSolo()
  local ok, err
  if d and d.state == "rolling" and d.turn == "opp" and DR.CanCallOff and DR.CanCallOff() then
    ok = TCF:DeathRollCallOff()
  elseif d and d.state == "rolling" then
    ok = TCF:DeathRollRoll()
  elseif d and d.state == "asking" then
    TCF:DeathRollWithdraw()
  elseif running then
    ok = TCF:DeathRollSoloRoll()
  elseif self.mode == "house" then
    ok, err = TCF:DeathRollSoloStart(self.bet, self.range)
    if ok then self:ResetAnims() end
  else
    local f = self:Friends()
    local m = f[self:FriendIndex(#f)]
    if m then ok, err = TCF:DeathRollChallenge(m.name, self.bet, self.range) end
    if ok then self:ResetAnims() end
  end
  if err then self.msg = err end
  self:Refresh(true)
end

function Scene:FriendIndex(n)
  if n == 0 then return 0 end
  local i = ((self.friendIdx or 1) - 1) % n + 1
  self.friendIdx = i
  return i
end

-- which game the scene shows: "duel" (with a friend) or "solo", for the death roll or rock paper scissors
function Scene:Showing()
  if self.game == "rps" then return self:ShowingRPS() end
  local d = DR.duel
  if d and (d.state ~= "over" or self.mode == "friend") then return "duel", d end
  local g = TCF:DeathRollSolo()
  if g and self.mode == "house" then return "solo", g end
  return nil
end

local function setLook(s, look, key)
  if s.lookKey ~= key then
    s.lookKey = key
    s.cat:ApplyAppearance(look)
  end
  s.look = look
end

function Scene:Refresh(full)
  if not TCF.db then return end
  local L, R = self.L, self.R
  -- a game that is running (or an invite) shows its own game
  local RPS = TCF.RPS
  if RPS and self.BuildRPS and self.game ~= "rps" and RPS.Busy() then self.game = "rps"; self:ResetAnims()
  elseif self.game ~= "dr" and DR.Busy() then self.game = "dr"; self:ResetAnims() end
  local rps = self.game == "rps"
  local bgName = rps and "mountain" or "tavern"
  if self.bgName ~= bgName then self.bgName = bgName; self.bg:SetTexture(ART .. bgName) end
  if rps then self.gameRPS:LockHighlight(); self.gameDR:UnlockHighlight()
  else self.gameDR:LockHighlight(); self.gameRPS:UnlockHighlight() end
  local kind, g = self:Showing()
  if kind == "duel" and self.mode ~= "friend" then self.mode = "friend" end
  local lo, hi = DR.Limits()
  local locked = self:Locked()
  -- the bet is the Casino's shared bet (the Slots and Blackjack choosers change it too)
  local cd = TCF.CasinoData and TCF:CasinoData()
  if cd and not locked and tonumber(cd.bet) then self.bet = tonumber(cd.bet) end
  if hi >= lo then self.bet = max(lo, min(hi, self.bet or lo)) end
  local friendMode = self.mode == "friend"

  -- top bar
  if self.mode == "house" then self.modeHouse:LockHighlight(); self.modeFriend:UnlockHighlight()
  else self.modeFriend:LockHighlight(); self.modeHouse:UnlockHighlight() end
  self.modeHouse:SetEnabled(not locked); self.modeFriend:SetEnabled(not locked)
  self.gameDR:SetEnabled(not locked); self.gameRPS:SetEnabled(not locked and self.BuildRPS ~= nil)
  local friends = self:Friends()
  self.prev:SetShown(friendMode); self.next:SetShown(friendMode); self.friend:SetShown(friendMode)
  local fm
  if friendMode then
    if kind == "duel" then
      fm = DR.Member(g.opp)
      self.friend:SetText(shortName(g.opp))
    else
      fm = friends[self:FriendIndex(#friends)]
      self.friend:SetText(fm and shortName(fm.name) or "|cff999999Nobody yet|r")
    end
    self.prev:SetEnabled(#friends > 1 and not locked); self.next:SetEnabled(#friends > 1 and not locked)
  end
  -- the picked friend: can their addon play (DeathRoll.lua asks it with a hello)
  local stateText = ""
  if friendMode and fm and not fm.fake and DR.FriendStatus and not (kind == "duel" and g.state ~= "over") then
    local text, st = DR.FriendStatus(fm.name)
    if st == "checking" and DR.AskFriend then DR.AskFriend(fm.name) end
    local col = st == "ready" and "|cff60ff60" or st == "old" and "|cffff9070" or "|cffd0d0d0"
    stateText = col .. text .. "|r"
  end
  self.friendState:SetText(stateText)
  self.friendState:SetShown(stateText ~= "")
  if self.chooser then
    self.chooser:SetLocked(locked and true or false)
    if locked and g and g.bet then self.chooser.val:SetText(TCF.UI.coinStr(g.bet, 16)) end
  elseif self.betText then
    self.betText:SetText(coins((locked and g and g.bet) or self.bet or lo))
  end
  for r, b in pairs(self.rangeBtns) do
    local sel = (locked and g and g.range or self.range) == r
    if sel then b:LockHighlight() else b:UnlockHighlight() end
    b:SetEnabled(not locked)
    b:SetShown(not rps)
  end
  self.rangeLabel:SetShown(not rps)

  -- the two cats
  if full or not L.lookKey then
    local look = TCF:GetAppearance(TCF.db.class)
    setLook(L, look, lookKey(look))
  end
  local me = TCF.SelfName and TCF.SelfName()
  L.name:SetText((type(me) == "string" and not TCF.IsSecret(me)) and shortName(me) or "You")
  local rightName, rightLook, rightKey
  if kind == "solo" then
    rightName, rightLook = g.house.name, DR.HouseLook(g.house)
    rightKey = "house:" .. g.house.name .. (g.house.skin or "") .. (g.house.fur or "") .. (g.house.head or "")
  elseif kind == "duel" then
    rightName = g.opp
    fm = fm or DR.Member(g.opp)
    if fm then rightLook, rightKey = fm.look, "m:" .. tostring(fm.text) end
  elseif friendMode then
    if fm then rightName, rightLook, rightKey = fm.name, fm.look, "m:" .. tostring(fm.text) end
  else
    self.idleHouse = self.idleHouse or { name = "Lucky Paws", skin = TCF.ITEMS and TCF.ITEMS.skin_tuxedo and "skin_tuxedo" or nil }
    rightName, rightLook, rightKey = self.idleHouse.name, DR.HouseLook(self.idleHouse), "house:idle"
  end
  if rightLook then setLook(R, rightLook, rightKey); R.holder:Show() else R.holder:Hide() end
  R.name:SetText(rightName and shortName(rightName) or "")
  local stake = g and g.bet
  L.bet:SetText(stake and ("Bet " .. coins(stake)) or "")
  R.bet:SetText((stake and rightName) and ("Bet " .. coins(stake)) or "")
  self:RefreshHowTo()
  if self.ShowRPSParts then self:ShowRPSParts(rps) end
  if rps then return self:RefreshRPS(kind, g, fm, friends, lo, hi) end

  -- the range in the middle
  local cur = g and g.cur or self.range
  if self.rangeTween then cur = self.rangeShown or cur end
  self.rangeNum:SetText("1 - " .. TCF.Commas(floor(cur)))
  if cur <= 10 then self.rangeNum:SetTextColor(1, 0.25, 0.2) else self.rangeNum:SetTextColor(1, 0.86, 0.35) end
  self.rangeCap:SetText(g and "Next roll" or "Rolls start at")

  -- invite, status, buttons
  self.inv:Hide()
  local status, btn, btnOn = "", nil, true
  local t = now()
  if kind == "solo" then
    if g.over then
      if g.loser == "house" then status = string.format("|cff40ff40You win %s|r (%s back). %s rolled the 1.", coins((g.paid or 0) - g.bet), coins(g.paid or 0), safeName(g.house.name))
      else status = string.format("%s wins this time. You rolled the 1.", safeName(g.house.name)) end
      btn = "Play again"
    elseif g.turn == "me" then
      status = (g.n or 0) == 0 and "The coin flip says you roll first." or "Your turn."
      btn = "Roll 1 - " .. TCF.Commas(g.cur)
    else
      status = string.format("%s is rolling...", safeName(g.house.name))
      btn, btnOn = "Roll 1 - " .. TCF.Commas(g.cur), false
    end
  elseif kind == "duel" then
    local opp = shortName(g.opp)
    if g.state == "asking" then
      status = string.format("Waiting for %s to answer (%d s).", opp, max(0, floor(g.expires - t)))
      btn = "Withdraw"
    elseif g.state == "invited" then
      self.inv.text:SetText(string.format("%s challenges you to a death roll for %s each, rolls from 1 to %s (%d s).",
        opp, coins(g.bet), TCF.Commas(g.range), max(0, floor(g.expires - t))))
      self.inv:Show()
    elseif g.state == "rolling" then
      local left = max(0, floor(g.turnAt + DR.TURN_TIME - t))
      if g.turn == "me" then
        status = string.format("%sYour turn (%d s left).", g.n == 0 and "You roll first. " or "", left)
        btn = "Roll 1 - " .. TCF.Commas(g.cur)
      elseif DR.CanCallOff and DR.CanCallOff() then
        -- (1.6.4) their roll hasn't come for a while: a way out without a /reload
        status = string.format("%s's turn (%d s left). Their roll hasn't come through: you can call it off and both bets come back.", opp, left)
        btn, btnOn = "Call off", true
      else
        status = string.format("%s's turn (%d s left).", opp, left)
        btn, btnOn = "Roll 1 - " .. TCF.Commas(g.cur), false
      end
    elseif g.state == "done" then
      status = "Settling the result..."
      btn, btnOn = "Roll", false
    else
      local r = g.result
      if r == "win" and g.reason == "f" then status = string.format("|cff40ff40You win %s|r. %s ran out of time on their turn.", coins(DR.DuelWin(g.bet)), opp)
      elseif r == "lose" and g.reason == "f" then status = string.format("You ran out of time on your turn and lose %s.", coins(g.bet))
      elseif r == "win" then status = string.format("|cff40ff40You win %s|r. %s rolled the 1.", coins(DR.DuelWin(g.bet)), opp)
      elseif r == "lose" then status = string.format("%s wins. You rolled the 1 and lose %s.", opp, coins(g.bet))
      elseif r == "declined" then status = g.by == "me" and "You declined." or string.format("%s declined.", opp)
      elseif r == "busy" then status = string.format("%s is busy with another game right now.", opp)
      elseif r == "toohigh" then status = g.role == "out" and string.format("%s can't bet that much right now.", opp)
                                    or string.format("%s wanted a death roll for %s, more than you can bet right now.", opp, coins(g.bet))
      elseif r == "expired" then status = string.format("You didn't answer %s in time.", opp)
      else
        local why = (g.by == "me" and DR.REASONS_ME[g.reason or ""]) or DR.REASONS[g.reason or "t"] or DR.REASONS.t
        status = why:format(opp) .. " No TapCoins moved."
        if g.reason == "x" and g.by == "me" then status = "You withdrew the challenge. No TapCoins moved." end
      end
      btn = fm and ("Challenge " .. shortName(fm.name)) or "Challenge"
      btnOn = fm ~= nil and hi >= lo
    end
  elseif friendMode then
    if #friends == 0 then
      status = "Nobody in your group has TapCatForever yet. Group up with a friend who has it to challenge them."
      btn, btnOn = "Challenge", false
    else
      status = string.format("Challenge %s: you both bet %s. Whoever rolls the 1 loses it, and the winner gets %s.",
        shortName(fm.name), coins(self.bet), coins(DR.DuelWin(self.bet)))
      btn, btnOn = "Challenge " .. shortName(fm.name), hi >= lo
    end
  else
    status = "Take turns rolling. Each roll goes from 1 to the last number. Whoever rolls a 1 loses."
    btn, btnOn = "Start", hi >= lo
  end
  if hi < lo and not kind then status = string.format("You need at least %s to play.", coins(lo * 2)) end
  if self.msg then status = "|cffff8080" .. self.msg .. "|r" end
  if DR.refunded and DR.refunded > 0 then
    status = string.format("Your game with a friend was called off by the reload. Your %s bet came back.", coins(DR.refunded))
    if t - (self.refundShownAt or t) > 8 then DR.refunded = nil end
    self.refundShownAt = self.refundShownAt or t
  end
  self.status:SetText(status)
  self.action:SetText(btn or "Start")
  self.action:SetEnabled(btnOn and true or false)
  self.action:SetShown(btn ~= nil)
  if friendMode then
    self.note:SetText(NOTE_ROLL)
    self.note2:SetText("Each turn has 60 seconds: if you don't roll in time, you lose. A reload or leaving the group calls the duel off.")
  else
    self.note:SetText("Who rolls first is a coin flip. Win and you get 1.9 times your bet back.")
    self.note2:SetText("TapCoins are scarce: the house keeps a little of every bet on average.")
  end
end

-- the How to play lines for the game and opponent on screen
function Scene:HowTo()
  if self.game == "rps" and self.HowToRPS then return self:HowToRPS() end
  if self.mode == "friend" then
    return { "1. Both players bet the same amount.",
             "2. The first player rolls 1 to 1,000 (or the start you picked).",
             "3. Each next roll is 1 to the number just rolled.",
             "4. Whoever rolls a 1 loses, and the other player gets the bet." }
  end
  return { "1. You and the house cat bet the same amount.",
           "2. A coin flip picks who rolls first: 1 to 1,000 (or the start you picked).",
           "3. Each next roll is 1 to the number just rolled.",
           "4. Whoever rolls a 1 loses. Beat the house cat and you get 1.9 times your bet back." }
end

function Scene:RefreshHowTo()
  local how = self.how
  local text = table.concat(self:HowTo(), "\n")
  if how.text ~= text then
    how.text = text
    how.body:SetText(text)
  end
  -- as tall as the text needs (long lines wrap)
  local th = how.body.GetStringHeight and how.body:GetStringHeight()
  local h = (type(th) == "number" and th > 0) and floor(th + 0.5) + 30 or 76
  how:SetHeight(min(104, max(52, h)))
end

---------------------------------------------------------------- animation
function Scene:ResetAnims()
  for _, s in ipairs({ self.L, self.R }) do
    s.hopT, s.popT, s.defeatT, s.winT, s.flopped = nil, nil, nil, nil, false
    s.pop:Hide(); s.ghost:Hide()
    for _, t in ipairs(s.flop) do t:Hide() end
    s.cat.frame:SetAlpha(1); s.cat.frame:SetScale(1)
    s.cat.frame:ClearAllPoints(); s.cat.frame:SetPoint("BOTTOM", s.holder, "BOTTOM", 0, 0)
  end
  for _, c in ipairs(self.conf) do c.on = false; c.tex:Hide() end
  self.rangeTween = nil
  if self.ResetRPS then self:ResetRPS() end
end

-- a roll: the number pops over the roller's head and the range in the middle counts down to it
function Scene:OnRoll(who, value, hi)
  local s = (who == "me") and self.L or self.R
  local t = now()
  s.hopT = t
  s.popT, s.popV = t, value
  s.pop.num:SetText(TCF.Commas(value))
  if value <= 10 then
    s.pop.num:SetTextColor(0.9, 0.1, 0.08); s.pop.bg:SetVertexColor(1, 0.82, 0.82)
  else
    s.pop.num:SetTextColor(0.23, 0.15, 0.12); s.pop.bg:SetVertexColor(1, 1, 1)
  end
  s.pop:SetScale(0.3); s.pop:SetAlpha(1); s.pop:Show()
  if s.cat.Tap then s.cat:Tap() end
  s.cat:SetFaceFor(value <= 10 and "focus" or "happy", 1)
  self.rangeTween, self.rangeFrom, self.rangeTo, self.rangeShown = t, hi, value, hi
  TCF:PlaySound("click")
end

-- the end: loser flops, winner jumps in confetti
function Scene:OnEnd(loserSide)
  local t = now() + 0.7    -- after the last number has popped
  local loser = loserSide == "L" and self.L or self.R
  local winner = loserSide == "L" and self.R or self.L
  loser.defeatT = t
  local r, g, b = furColor(loser.look)
  loser.flop[1]:SetVertexColor(r, g, b)
  winner.winT = t
  self.confAt, self.confSide = t, winner
  if winner == self.L then TCF:PlaySound("loot") end
end

local function burst(v, s)
  local cx, cy = s.x + v.cw / 2, s.y + v.CAT * 0.9
  for i, c in ipairs(v.conf) do
    local a = pi * (0.15 + 0.7 * random())
    local sp = 160 + random() * 220
    c.x, c.y = cx + (random() - 0.5) * 30, cy
    c.vx, c.vy = cos(a) * sp, sin(a) * sp
    c.r, c.vr = random() * 6, (random() - 0.5) * 14
    c.age, c.life, c.on = 0, 1.6 + random() * 0.9, true
    c.tex:SetSize(14 + (i % 4) * 2, 14 + (i % 4) * 2)
    c.tex:SetAlpha(1); c.tex:Show()
  end
end

local function animSide(v, s, t)
  local cat = s.cat.frame
  local x, y = 0, 0
  -- a little hop when rolling
  if s.hopT then
    local p = (t - s.hopT) / 0.28
    if p >= 1 then s.hopT = nil else y = y + sin(p * pi) * 10 end
  end
  -- the number pop: overshoot, settle, hold, fade; small numbers shake
  if s.popT then
    local a = t - s.popT
    local pop = s.pop
    if a >= 2.6 then s.popT = nil; pop:Hide()
    else
      local sc
      if a < 0.12 then sc = 0.3 + (a / 0.12) * 0.95
      elseif a < 0.24 then sc = 1.25 - ((a - 0.12) / 0.12) * 0.25
      else sc = 1 end
      pop:SetScale(sc)
      pop:SetAlpha(a > 2.1 and (2.6 - a) / 0.5 or 1)
      local sx = 0
      if s.popV <= 10 then sx = sin(a * 48) * (s.popV == 1 and 6 or 4) * max(0.3, 1 - a / 2.6) end
      pop:ClearAllPoints(); pop:SetPoint("BOTTOM", s.holder, "TOP", sx / sc, 4 / sc)
    end
  end
  -- winner: three happy hops
  if s.winT and t >= s.winT then
    local a = t - s.winT
    if a >= 1.6 then s.winT = nil
    else
      y = y + abs(sin(a * pi / 0.53)) * 26 * (1 - a / 2)
      s.cat:SetFaceFor("sparkle", 0.3)
    end
  end
  -- loser: shake, spin up and flop onto its back (X eyes), ghost floats off, then pop back up
  if s.defeatT and t >= s.defeatT then
    local a = t - s.defeatT
    local flop, ghost = s.flop, s.ghost
    if a < 0.35 then
      x = x + sin(a * 60) * 6
      s.cat:SetFaceFor("focus", 0.3)
    elseif a < 3.7 then
      if not s.flopped then
        s.flopped = true
        cat:SetAlpha(0)
        for _, tex in ipairs(flop) do tex:Show() end
      end
      local b = a - 0.35
      local rot, fy = 0, 0
      if b < 0.75 then
        rot = (b / 0.75) * 4 * pi                    -- two spins in the air
        fy = sin((b / 0.75) * pi) * v.CAT * 0.35
      elseif b < 0.95 then
        fy = sin(((b - 0.75) / 0.2) * pi) * 6        -- a little bounce on landing
      end
      for _, tex in ipairs(flop) do tex:SetRotation(rot) end
      s.fx:ClearAllPoints(); s.fx:SetPoint("CENTER", s.holder, "BOTTOM", 0, v.CAT * 0.3 + fy)
      if b >= 0.9 and b < 3.0 then
        local gp = (b - 0.9) / 2.1
        if not ghost:IsShown() then ghost:Show() end
        ghost:ClearAllPoints(); ghost:SetPoint("CENTER", s.fx, "CENTER", sin(gp * 9) * 6, 10 + gp * v.CAT * 0.75)
        ghost:SetAlpha(gp < 0.15 and gp / 0.15 * 0.9 or 0.9 * (1 - gp) / 0.85)
      elseif ghost:IsShown() then ghost:Hide() end
    elseif a < 4.15 then
      if s.flopped then
        s.flopped = false
        for _, tex in ipairs(flop) do tex:Hide(); tex:SetRotation(0) end
        ghost:Hide()
        cat:SetAlpha(1)
        s.cat:SetFaceFor("happy", 1.6)
      end
      local p = (a - 3.7) / 0.45
      cat:SetScale(p < 0.6 and (0.4 + p / 0.6 * 0.75) or (1.15 - (p - 0.6) / 0.4 * 0.15))
    else
      cat:SetScale(1); s.defeatT = nil
    end
  end
  cat:ClearAllPoints(); cat:SetPoint("BOTTOM", s.holder, "BOTTOM", x, y)
end

function Scene:Animate(e)
  local t = now()
  animSide(self, self.L, t)
  animSide(self, self.R, t)
  if self.AnimateRPS then self:AnimateRPS(t, e) end
  if self.rangeTween then
    local p = (t - self.rangeTween) / 0.45
    if p >= 1 then self.rangeTween = nil; self.rangeShown = self.rangeTo
    else self.rangeShown = self.rangeFrom + (self.rangeTo - self.rangeFrom) * (1 - (1 - p) * (1 - p)) end
    local cur = floor(self.rangeShown + 0.5)
    self.rangeNum:SetText("1 - " .. TCF.Commas(cur))
    if cur <= 10 then self.rangeNum:SetTextColor(1, 0.25, 0.2) end
  end
  if self.confAt and t >= self.confAt then
    burst(self, self.confSide)
    self.confAt = nil
  end
  local h = self.ch
  for _, c in ipairs(self.conf) do
    if c.on then
      c.age = c.age + e
      if c.age >= c.life then c.on = false; c.tex:Hide()
      else
        c.vy = c.vy - 520 * e
        c.vx = c.vx * (1 - 0.8 * e)
        c.x, c.y = c.x + c.vx * e, max(8, c.y + c.vy * e)
        c.r = c.r + c.vr * e
        c.tex:ClearAllPoints(); c.tex:SetPoint("CENTER", self.top, "BOTTOMLEFT", c.x, c.y)
        c.tex:SetRotation(c.r)
        local left = c.life - c.age
        c.tex:SetAlpha(left < 0.4 and left / 0.4 or 1)
      end
    end
  end
end

---------------------------------------------------------------- events from DeathRoll.lua
DR.OnChange = function(ev, kind, a, b, c)
  updatePrompt()
  for _, v in ipairs(views) do
    local showing = v:Showing()
    local visible = v.scene:IsVisible() and v.game == "dr"
    if ev == "roll" and showing == kind and visible then
      v:OnRoll(a, b, c)
    elseif ev == "end" and showing == kind and visible then
      if kind == "solo" then v:OnEnd(a == "me" and "R" or "L")
      elseif a == "win" then v:OnEnd("R")
      elseif a == "lose" then v:OnEnd("L") end
    elseif ev == "start" or ev == "invite" then
      if ev == "start" then v:ResetAnims() end
    end
    v.msg = nil
    v:Refresh(true)
  end
end

-- for UI_RPS.lua: the scene and the helpers it shares
DR.UI = { Scene = Scene, views = views, coins = coins, shortName = shortName, safeName = safeName, now = now,
          ART = ART, FONT = FONT, furColor = furColor, pendingInvite = pendingInvite, answer = answer,
          updatePrompt = updatePrompt, burst = burst }
-- the game the Death roll view shows, for the Casino's stats line: "deathroll" or "rps"
function DR.ViewGame()
  local v = views[1]
  return (v and v.game == "rps") and "rps" or "deathroll"
end
