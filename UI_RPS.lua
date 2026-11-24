-- TapCatForever: rock paper scissors in the Death roll scene (the rules and money are in RPS.lua;
-- the scene, the cats, the top bar and the confetti are UI_DeathRoll.lua's). A snowy mountaintop:
-- each cat holds up its paw, both shake it three times ("rock, paper, scissors") and then show
-- their sign (a fist paw, an open paw, or two toes up), drawn in the cat's own fur colour. The
-- winner hops in confetti and the loser flops over, like the death roll; a tie plays again.
-- (1.6.7) Best of 1, 3 or 5: the button in the top bar picks it before a game; a round won in a longer
-- game gets a small cheer and the score, the hop and flop wait for the last one.
local ADDON, TCF = ...
local floor, min, max, sin, pi, abs = math.floor, math.min, math.max, math.sin, math.pi, math.abs
local DR = TCF.DR
local R = TCF.RPS
local UIX = DR.UI
local Scene, coins, shortName, safeName, now = UIX.Scene, UIX.coins, UIX.shortName, UIX.safeName, UIX.now
local ART = UIX.ART
local NAME = { rock = "Rock", paper = "Paper", scissors = "Scissors" }
local BEAT = 0.42                 -- one shake of the paw
local SHAKES = 3                  -- "rock, paper, scissors", then the reveal
local CHANT = { "Rock", "Paper", "Scissors" }
local RESULT_HOLD = 0.7           -- after the reveal, the winner hops and the loser flops

-- "Paper beats rock" / "Scissors beat paper" / "Rock beats scissors"
local function beats(w, l)
  return string.format("%s %s %s", NAME[w], w == "scissors" and "beat" or "beats", l)
end
R.BeatsText = beats

---------------------------------------------------------------- building
local function sideSign(v, s)
  local scene, CAT = v.scene, v.CAT
  local f = CreateFrame("Frame", nil, scene)
  local lvl = scene.GetFrameLevel and scene:GetFrameLevel() or 1
  if f.SetFrameLevel then pcall(f.SetFrameLevel, f, lvl + 12) end
  local sz = floor(CAT * 0.52)
  f:SetSize(sz, sz)
  f.fur = f:CreateTexture(nil, "ARTWORK"); f.fur:SetAllPoints(f)
  f.line = f:CreateTexture(nil, "OVERLAY"); f.line:SetAllPoints(f)
  f.size = sz
  f:Hide()
  s.sign = f
end

local function setSign(v, s, sign)
  local f = s.sign
  f.fur:SetTexture(ART .. "rps_" .. sign .. "_fur")
  f.line:SetTexture(ART .. "rps_" .. sign .. "_line")
  local r, g, b = UIX.furColor(s.look)
  f.fur:SetVertexColor(r, g, b)
  -- the left cat's paw leans right, toward the other cat, and the right one leans left
  for _, t in ipairs({ f.fur, f.line }) do t:SetRotation(s.side == "R" and 0.3 or -0.3) end
  f.shown = sign
end

local function placeSign(v, s, dy, scale)
  local f = s.sign
  local dir = s.side == "L" and 1 or -1
  f:SetScale(scale or 1)
  f:ClearAllPoints()
  f:SetPoint("CENTER", v.scene, "BOTTOM", (s.x + dir * v.CAT * 0.42) / (scale or 1), (s.y + v.CAT * 0.45 + (dy or 0)) / (scale or 1))
end

function Scene:BuildRPS()
  local U = TCF.UI
  local v = self
  sideSign(v, v.L); sideSign(v, v.R)
  -- the three picks, in place of the big button
  v.picks = {}
  local w, gap = 108, 8
  for i, sign in ipairs(R.SIGNS) do
    local b = U.Button(v.scene, NAME[sign], w, 30, function() v:Pick(sign) end)
    b:SetPoint("BOTTOM", v.scene, "BOTTOM", (i - 2) * (w + gap), 8)
    b.ico = b:CreateTexture(nil, "OVERLAY"); b.ico:SetSize(24, 24); b.ico:SetPoint("LEFT", 6, 0)
    b.ico:SetTexture(ART .. "rps_" .. sign .. "_fur"); b.ico:SetVertexColor(1, 0.78, 0.52)
    b.icoL = b:CreateTexture(nil, "OVERLAY", nil, 1); b.icoL:SetAllPoints(b.ico); b.icoL:SetTexture(ART .. "rps_" .. sign .. "_line")
    local fs = b.GetFontString and b:GetFontString()
    if fs and fs.ClearAllPoints then fs:ClearAllPoints(); fs:SetPoint("CENTER", 12, 0) end
    U.Tip(b, function(tt)
      tt:AddLine(NAME[sign], 1, 0.82, 0)
      tt:AddLine(beats(sign, R.BEATS[sign]) .. ".", 1, 1, 1, true)
    end)
    b:Hide()
    v.picks[sign] = b
  end
  -- in the top bar, where the death roll's range buttons are: best of 1, 3 or 5 (a click goes to
  -- the next), or the game's score while one runs
  local st = DR.Store and DR.Store()
  v.bestOf = (st and R.ValidBest(st.rpsBest)) and st.rpsBest or 1
  v.bestBtn = U.Button(v.bar, "Best of 1", 96, 22, function()
    TCF:PlaySound("click")
    local nxt = { [1] = 3, [3] = 5, [5] = 1 }
    v.bestOf = nxt[v.bestOf] or 1
    local s2 = DR.Store and DR.Store()
    if s2 then s2.rpsBest = v.bestOf end
    v.msg = nil
    v:Refresh(true)
  end)
  v.bestBtn:SetPoint("TOPRIGHT", v.bar, "TOPRIGHT", -12, -6)
  U.Tip(v.bestBtn, function(tt)
    tt:AddLine("Best of 1, 3 or 5", 1, 0.82, 0)
    tt:AddLine("Click to change. In best of 3 the first to win 2 rounds takes the game, in best of 5 the first to win 3. Ties don't count.", 1, 1, 1, true)
    tt:AddLine("The bet is the same for the whole game.", 0.8, 0.8, 0.8, true)
  end)
  v.rpsInfo = U.Text(v.bar, "GameFontNormal", "Best of 1", "RIGHT"); v.rpsInfo:SetPoint("TOPRIGHT", v.bar, "TOPRIGHT", -12, -10)
  v.rpsInfo2 = U.Text(v.bar, "GameFontHighlightSmall", "A tie plays again", "RIGHT"); v.rpsInfo2:SetPoint("TOPRIGHT", v.bar, "TOPRIGHT", -12, -32)
  v.rpsInfo:Hide(); v.rpsInfo2:Hide(); v.bestBtn:Hide()
  v.rps = {}
end

function Scene:ShowRPSParts(on)
  if not self.picks then return end
  self.rpsInfo:SetShown(on); self.rpsInfo2:SetShown(on)
  if not on then
    self.bestBtn:Hide()
    for _, b in pairs(self.picks) do b:Hide() end
    self.L.sign:Hide(); self.R.sign:Hide()
  end
end

---------------------------------------------------------------- which game, the rules
function Scene:ShowingRPS()
  local d = R.duel
  if d and (d.state ~= "over" or self.mode == "friend") then return "duel", d end
  local g = TCF:RPSSolo()
  if g and self.mode == "house" then return "solo", g end
  return nil
end

function Scene:HowToRPS()
  if self.mode == "friend" then
    return { "1. Both players bet the same amount.",
             "2. Each picks rock, paper or scissors in secret.",
             "3. Rock beats scissors, scissors beat paper, paper beats rock.",
             "4. A tie plays again. Best of 3 or 5: first to 2 or 3 round wins. The winner gets the bet." }
  end
  return { "1. Choose your bet and pick rock, paper or scissors.",
           "2. The house cat picks at random.",
           "3. Rock beats scissors, scissors beat paper, paper beats rock.",
           "4. A tie plays again for free. Best of 3 or 5: first to 2 or 3 round wins. Win and you get 1.9 times your bet back." }
end

function Scene:Pick(sign)
  TCF:PlaySound("click")
  self.msg = nil
  local d = R.duel
  local ok, err
  if self.mode == "friend" or (d and d.state ~= "over") then
    ok, err = TCF:RPSPick(sign)
  else
    local _, running = TCF:RPSSolo()
    if not running then self:ResetAnims() end
    ok, err = TCF:RPSSoloPlay(sign, self.bet, self.bestOf)   -- bet and best-of only count when no game is running
  end
  if err then self.msg = err end
  self:Refresh(true)
end

-- the big button in this game: challenge a friend, or withdraw the challenge
function Scene:ActionRPS()
  TCF:PlaySound("click")
  self.msg = nil
  local d = R.duel
  local ok, err
  if d and d.state == "asking" then
    TCF:RPSWithdraw()
  elseif self.mode == "friend" then
    local f = self:Friends()
    local m = f[self:FriendIndex(#f)]
    if m then ok, err = TCF:RPSChallenge(m.name, self.bet, self.bestOf) end
    if ok then self:ResetAnims() end
  end
  if err then self.msg = err end
  self:Refresh(true)
end

---------------------------------------------------------------- the reveal animation
-- rps = { shakeT (the shake started), pending = { me, opp, res } (the picks, once known),
--   revealT (the signs are shown), game (the game they belong to) }
function Scene:ResetRPS()
  local a = self.rps
  if not a then return end
  a.shakeT, a.pending, a.revealT, a.collected = nil, nil, nil, nil
  self.rpsLast = nil
  for _, s in ipairs({ self.L, self.R }) do
    if s.sign then s.sign:Hide(); s.sign.shown = nil end
  end
end

function Scene:StartShake()
  local a = self.rps
  if a.shakeT and not a.revealT then return end
  a.shakeT, a.revealT, a.collected = now(), nil, nil
  self.rpsLast = nil
  for _, s in ipairs({ self.L, self.R }) do
    setSign(self, s, "rock")
    s.sign:Show()
  end
end

-- the picks are known: show them when the shake ends (starts the shake if it isn't running)
function Scene:OnReveal(me, opp, res, game, point)
  local a = self.rps
  if not a.shakeT or a.revealT then a.shakeT, a.revealT = nil, nil; self:StartShake() end
  a.pending = { me = me, opp = opp, res = res, point = point == "point" }
  a.game = game
end

-- a game is between its first shake and its result on screen
function Scene:RPSAnimating()
  local a = self.rps
  return a and a.shakeT ~= nil and (a.revealT == nil or now() - a.revealT < RESULT_HOLD) or false
end

function Scene:AnimateRPS(t, e)
  local a = self.rps
  if not a or self.game ~= "rps" then return end
  if a.shakeT and not a.revealT then
    local el = t - a.shakeT
    local beat = floor(el / BEAT) + 1
    if beat <= SHAKES then
      local p = (el % BEAT) / BEAT
      local dy = abs(sin(p * pi)) * 20
      placeSign(self, self.L, dy); placeSign(self, self.R, dy)
      self.rangeCap:SetText(string.format("Round %d", self.rpsRound or 1))
      self.rangeNum:SetText(CHANT[beat]); self.rangeNum:SetTextColor(1, 0.86, 0.35)
    elseif a.pending then
      -- the reveal: both signs pop in
      a.revealT = t
      local pd = a.pending
      setSign(self, self.L, pd.me); setSign(self, self.R, pd.opp)
      TCF:PlaySound("click")
      if pd.res == "tie" then
        self.rpsLast = { cap = string.format("Both picked %s", pd.me), num = "Tie", r = 1, g = 1, b = 1, game = a.game }
        self.L.cat:SetFaceFor("focus", 1); self.R.cat:SetFaceFor("focus", 1)
      elseif pd.point then
        -- a round of a longer game: a small cheer, the game goes on
        local win = pd.res == "win"
        local w, l = win and pd.me or pd.opp, win and pd.opp or pd.me
        self.rpsLast = { cap = beats(w, l), num = win and "Your round" or "Their round", r = win and 0.4 or 1, g = win and 1 or 0.6, b = win and 0.4 or 0.3, game = a.game }
        local ws, ls = win and self.L or self.R, win and self.R or self.L
        ws.cat:SetFaceFor("happy", 1); ls.cat:SetFaceFor("focus", 1)
        if win then TCF:PlaySound("buy") end
      else
        local win = pd.res == "win"
        local w, l = win and pd.me or pd.opp, win and pd.opp or pd.me
        self.rpsLast = { cap = beats(w, l), num = win and "You win" or "You lose", r = win and 0.4 or 1, g = win and 1 or 0.35, b = win and 0.4 or 0.3, game = a.game }
        self:OnEnd(win and "R" or "L")
      end
      self:Refresh(true)
    else
      -- still waiting for the other pick: hold the fists up
      placeSign(self, self.L, 0); placeSign(self, self.R, 0)
    end
  end
  if a.revealT then
    local el = t - a.revealT
    local sc = el < 0.12 and (0.4 + el / 0.12 * 0.85) or (el < 0.25 and (1.25 - (el - 0.12) / 0.13 * 0.25) or 1)
    for _, s in ipairs({ self.L, self.R }) do
      -- the loser's sign goes when it flops over
      if s.defeatT and t >= s.defeatT + 0.35 then s.sign:Hide() end
      placeSign(self, s, 0, sc)
    end
    if el >= RESULT_HOLD and not a.collected then
      a.collected = true
      -- the house cat's payout waits for the reveal on screen (RPS.lua holds it)
      TCF:CasinoCollect(R.GAME)
      self:Refresh(true)
    end
  end
end

-- held back while a visible scene is still showing the reveal
function R.Animating()
  for _, v in ipairs(UIX.views) do
    if v.game == "rps" and v.scene:IsVisible() and v:RPSAnimating() then return true end
  end
  return false
end

---------------------------------------------------------------- texts and buttons
-- " Best of 3: 2 - 1." after a longer game, "" after best of 1
local function finalScore(g)
  if (g.bo or 1) <= 1 or not g.wins then return "" end
  return string.format(" Best of %d: %d - %d.", g.bo, g.wins.me or 0, g.wins.opp or 0)
end
function Scene:RefreshRPS(kind, g, fm, friends, lo, hi)
  local a = self.rps
  local t = now()
  local friendMode = self.mode == "friend"
  local animating = a.shakeT ~= nil and a.revealT == nil
  local status, btn, btnOn, picks, picksOn = "", nil, true, false, false
  self.inv:Hide()
  local last = g and g.rounds and g.rounds[#g.rounds]
  self.rpsRound = g and g.round or 1
  local cap, num = "Rock paper scissors", friendMode and ("Best of " .. (self.bestOf or 1)) or "Pick one"
  -- the score of a longer game ("You 1 - 0 Bob"), or the best-of button before one starts
  local running = (kind == "solo" and not g.over) or (kind == "duel" and g.state ~= "over")
  local bo = running and (g.bo or 1) or (self.bestOf or 1)
  local wins = g and g.wins
  local scoreText
  if running and bo > 1 and wins then
    local oname = kind == "solo" and safeName(g.house.name) or shortName(g.opp)
    scoreText = string.format("You %d - %d %s", wins.me or 0, wins.opp or 0, oname)
  end
  self.bestBtn:SetShown(not running)
  self.bestBtn:SetText("Best of " .. (self.bestOf or 1))
  self.rpsInfo:SetShown(running)
  self.rpsInfo:SetText("Best of " .. bo)
  self.rpsInfo2:SetText(scoreText or (bo > 1 and string.format("First to %d wins", R.Need(bo)) or "A tie plays again"))
  local cr, cg, cb = 1, 0.86, 0.35
  if kind == "solo" then
    picks, picksOn = true, hi >= lo or not g.over
    if animating then
      status = "Rock, paper, scissors..."
      picksOn = false
    elseif not g.over then
      if last and last.res == "tie" then
        status = string.format("Tie: you both picked %s. Pick again, it's free.", last.me)
      elseif last and last.res == "win" then
        status = string.format("You take that round (%s). Pick for the next one.", scoreText or "")
      elseif last then
        status = string.format("%s takes that round (%s). Pick for the next one.", safeName(g.house.name), scoreText or "")
      else
        status = "Pick rock, paper or scissors."
      end
      cap, num = string.format("Round %d", g.round), "Pick one"
    elseif g.result == "win" then
      status = string.format("|cff40ff40You win %s|r (%s back). %s.%s Pick again to play another round.",
        coins((g.paid or 0) - g.bet), coins(g.paid or 0), beats(g.me, g.opp), finalScore(g))
    else
      status = string.format("%s wins this time. %s.%s Pick again to play another round.", safeName(g.house.name), beats(g.opp, g.me), finalScore(g))
    end
  elseif kind == "duel" then
    local opp = shortName(g.opp)
    local left = g.roundAt and max(0, floor(g.roundAt + R.PICK_TIME - t)) or 0
    if animating then
      status = "Rock, paper, scissors..."
    elseif g.state == "asking" then
      status = string.format("Waiting for %s to answer (%d s).", opp, max(0, floor(g.expires - t)))
      btn = "Withdraw"
    elseif g.state == "invited" then
      self.inv.text:SetText(string.format("%s challenges you to rock paper scissors%s for %s each (%d s).",
        opp, (g.bo or 1) > 1 and (", best of " .. g.bo) or "", coins(g.bet), max(0, floor(g.expires - t))))
      self.inv:Show()
    elseif g.state == "picking" then
      picks = true
      cap = string.format("Round %d", g.round)
      if g.myPick then
        status = string.format("You picked %s. Waiting for %s to pick (%d s).", g.myPick, opp, left)
        num = "Locked in"
      else
        local tie = ""
        if last and last.res == "tie" then tie = string.format("Tie: you both picked %s. ", last.me)
        elseif last and scoreText then
          tie = last.res == "win" and string.format("You take that round (%s). ", scoreText) or string.format("%s takes that round (%s). ", opp, scoreText)
        end
        status = string.format("%sPick rock, paper or scissors (%d s left).", tie, left)
        num, picksOn = "Pick one", true
      end
    elseif g.state == "reveal" then
      status = "Both picks are locked in. Showing them..."
      cap, num = string.format("Round %d", g.round), "Locked in"
    elseif g.state == "done" then
      status = string.format("Waiting for %s's addon to agree on the result...", opp)
    else
      local r = g.result
      if r == "win" then status = string.format("|cff40ff40You win %s|r. %s.%s", coins(g.bet), beats(g.me, g.opp_), finalScore(g))
      elseif r == "lose" then status = string.format("%s wins. %s, and you lose %s.%s", opp, beats(g.opp_, g.me), coins(g.bet), finalScore(g))
      elseif r == "declined" then status = g.by == "me" and "You declined." or string.format("%s declined.", opp)
      elseif r == "busy" then status = string.format("%s is busy with another game right now.", opp)
      elseif r == "toohigh" then status = g.role == "out" and string.format("%s can't bet that much right now.", opp)
                                    or string.format("%s wanted a game for %s, more than you can bet right now.", opp, coins(g.bet))
      elseif r == "expired" then status = string.format("You didn't answer %s in time.", opp)
      else
        local why = (g.by == "me" and R.REASONS_ME[g.reason or ""]) or R.REASONS[g.reason or "t"] or R.REASONS.t
        status = why:format(opp) .. " No TapCoins moved."
        if g.reason == "x" and g.by == "me" then status = "You withdrew the challenge. No TapCoins moved." end
        if a.shakeT and not a.revealT then self:ResetRPS() end
      end
      btn = fm and ("Challenge " .. shortName(fm.name)) or "Challenge"
      btnOn = fm ~= nil and hi >= lo
    end
  elseif friendMode then
    if #friends == 0 then
      status = "Nobody in your group has TapCatForever yet. Group up with a friend who has it to challenge them."
      btn, btnOn = "Challenge", false
    else
      status = string.format("Challenge %s%s: you both bet %s. The winner gets %s.", shortName(fm.name),
        (self.bestOf or 1) > 1 and (" to best of " .. self.bestOf) or "", coins(self.bet), coins(self.bet))
      btn, btnOn = "Challenge " .. shortName(fm.name), hi >= lo
    end
  else
    status = string.format("Pick rock, paper or scissors to play %sfor %s. The house cat picks at random.",
      (self.bestOf or 1) > 1 and ("best of " .. self.bestOf .. " ") or "", coins(self.bet or lo))
    picks, picksOn = true, hi >= lo
  end
  if hi < lo and not kind then status = string.format("You need at least %s to play.", coins(lo * 2)) end
  if self.msg then status = "|cffff8080" .. self.msg .. "|r" end
  if DR.refunded and DR.refunded > 0 then
    status = string.format("Your game with a friend was called off by the reload. Your %s bet came back.", coins(DR.refunded))
    if t - (self.refundShownAt or t) > 8 then DR.refunded = nil end
    self.refundShownAt = self.refundShownAt or t
  end
  self.status:SetText(status)
  -- the big button, or the three picks in its place
  if picks then btn = nil end
  self.action:SetText(btn or "Challenge")
  self.action:SetEnabled(btnOn and true or false)
  self.action:SetShown(btn ~= nil)
  for _, b in pairs(self.picks) do
    b:SetShown(picks)
    b:SetEnabled(picksOn and true or false)
  end
  -- the plate in the middle: the round, or the last result
  if not animating then
    -- the last reveal stays on the plate until the next pick is locked in or a new game starts
    local last2 = self.rpsLast
    if last2 and last2.game == g and num ~= "Locked in" then cap, num, cr, cg, cb = last2.cap, last2.num, last2.r, last2.g, last2.b end
    self.rangeCap:SetText(cap)
    self.rangeNum:SetText(num)
    self.rangeNum:SetTextColor(cr, cg, cb)
  end
  -- the signs: a raised fist for your locked-in pick while you wait, hidden when nothing is going on
  if not a.shakeT then
    local waiting = kind == "duel" and g.state == "picking" and g.myPick
    if waiting then
      setSign(self, self.L, "rock"); placeSign(self, self.L, 0); self.L.sign:Show(); self.R.sign:Hide()
    else
      self.L.sign:Hide(); self.R.sign:Hide()
    end
  end
  if friendMode then
    self.note:SetText("Both picks are locked in before either is shown, so nobody can peek.")
    self.note2:SetText("Each pick has 60 seconds. A reload or leaving the group calls the game off, and no TapCoins move.")
  else
    self.note:SetText("The house cat picks at random. A tie plays again for free.")
    self.note2:SetText("TapCoins are scarce: the house keeps a little of every bet on average.")
  end
end

---------------------------------------------------------------- events from RPS.lua
R.OnChange = function(ev, kind, a, b, c, dd)
  UIX.updatePrompt()
  for _, v in ipairs(UIX.views) do
    local showing = v:ShowingRPS()
    local visible = v.scene:IsVisible() and v.game == "rps"
    local _, g = v:ShowingRPS()
    if ev == "reveal" and showing == kind and visible then
      v:OnReveal(a, b, c, g, dd)
    elseif ev == "locked" and kind == "duel" and visible then
      v:StartShake()
    elseif ev == "state" or ev == "invite" then
      v:ResetAnims()
    end
    v.msg = nil
    v:Refresh(true)
  end
end
