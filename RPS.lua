-- TapCatForever: rock paper scissors (Casino tab > Death roll view > Rock paper scissors; the scene
-- is UI_DeathRoll.lua and UI_RPS.lua). Rock beats scissors, scissors beat paper, paper beats rock.
--
-- Against the house cat: you pick, the house cat picks at random. A tie plays again for free (the
-- bet stays on the table). The bet goes through Casino.lua's TCF:CasinoBet, and a win pays 1.9 times
-- the bet (rounded to the nearest TapCoin) through TCF:CasinoPay (held with TCF:CasinoHold until the
-- reveal has played on screen, see R.Animating). Ties replay, so you win exactly half the games: the
-- house keeps 1 - 1.9 / 2 = 5% of every bet on average (3.33% to 6.25% on bets that are not a
-- multiple of 10, because of the rounding), the same as the death roll. tools/tests/test_rps.py
-- measures it.
--
-- Against a party member who has the addon (best of 1, a tie plays again): commit, then reveal, so
-- neither addon can see the other's pick first. Each side picks, then sends only a hash of its pick
-- and a random secret (R4). Once both hashes are in, each side sends its pick and secret (R5), and
-- each checks that the other's pick and secret give the hash it was sent. A reveal that doesn't
-- match, or no reveal within 30 seconds, calls the game off and no TapCoins move. The bets are held
-- while the game runs (the same hold as the death roll duel, in db.deathRoll.hold). The result is
-- settled with TCF:CasinoSettleDuel, even (no fee), each side once: when a side has checked the other's
-- pick it says who lost (R6). The loser pays only once both sides agree (its own check and the
-- winner's R6), then says so (R7); the winner is paid only when that R7 arrives. So a missing reveal
-- moves nothing, and a lost message or a tampered addon can only take TapCoins out, never put them in.
--
-- Protocol (prefix "TapCatFvr", party/raid/instance channel, every field checked; v = 1):
--   R1;v;id;target;bet          challenge (target as in death roll's D1: "Name-Realm" as the game sends it)
--   R2;v;id;answer              y accept, n decline, b busy, c can't bet that much
--   R3;v;id;reason              called off (see R.REASONS)
--   R4;v;id;round;hash          my pick is locked in (hash: 8 hex digits)
--   R5;v;id;round;pick;secret   my pick (r, p or s) and the secret behind the hash
--   R6;v;id;round;loser         I checked both picks: c (challenger) or t (target) loses
--   R7;v;id;round;loser         I am that loser and I have paid
local ADDON, TCF = ...
local floor, max, random = math.floor, math.max, math.random
local DR = TCF.DR
TCF.RPS = TCF.RPS or {}
local R = TCF.RPS

local GAME = "rps"
local VER = "1"
R.GAME = GAME
R.SIGNS = { "rock", "paper", "scissors" }
local CODE = { rock = "r", paper = "p", scissors = "s" }
local SIGN = { r = "rock", p = "paper", s = "scissors" }
local BEATS = { rock = "scissors", scissors = "paper", paper = "rock" }
R.BEATS = BEATS
R.PAY_NUM, R.PAY_DEN = 19, 10    -- house cat: a win pays 1.9x the bet
R.INVITE_TIME = 60               -- a challenge waits this long for an answer
R.PICK_TIME = 60                 -- each round: time to pick
R.REVEAL_TIME = 30               -- both picks locked in: each reveal must arrive within this
R.DONE_WAIT = 30                 -- after both picks: wait this long for the other side's R6 (and the winner for R7)
local PICK_GRACE = 10            -- you picked: wait this much longer for the other pick
local RESEND = 4                 -- resend my reveal this often while waiting
local CHALLENGE_GAP = 3
local MUTE_AFTER_NO = 20
local MAX_ROUNDS = 99

local function isSecret(v) return TCF.IsSecret and TCF.IsSecret(v) end
local function now() return GetTime and GetTime() or 0 end
local function send(kind, ...) return DR.Send(kind, ...) end
local base, isMe, inGroup = DR.Base, DR.IsMe, DR.InGroup

function R.Payout(bet) return floor(bet * R.PAY_NUM / R.PAY_DEN + 0.5) end
-- who wins: "win" (a beats b), "lose" or "tie"
function R.Outcome(a, b)
  if a == b then return "tie" end
  return BEATS[a] == b and "win" or "lose"
end

---------------------------------------------------------------- the hash (commit-reveal)
-- 32-bit FNV-1a, in plain Lua 5.1 arithmetic (no bit library needed). It is not a cryptographic
-- hash: with a 16-character random secret it stops casual peeking (another addon reading the
-- message can't tell the pick from the hash), not a determined cheater who rewrites the addon.
local function xor8(a, b)
  local r, p = 0, 1
  for _ = 1, 8 do
    local x, y = a % 2, b % 2
    if x ~= y then r = r + p end
    a, b, p = (a - x) / 2, (b - y) / 2, p * 2
  end
  return r
end

function R.Hash(s)
  local h = 2166136261
  for i = 1, #s do
    local lo = h % 256
    h = h - lo + xor8(lo, s:byte(i))
    -- h * 16777619 mod 2^32, split so it stays exact in a double: 16777619 = 2^24 + 403
    h = ((h % 256) * 16777216 + h * 403) % 4294967296
  end
  return string.format("%08x", h)
end

local ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
local function newSecret()
  local t = {}
  for i = 1, 16 do
    local k = random(#ALPHA)
    t[i] = ALPHA:sub(k, k)
  end
  return table.concat(t)
end
local function commitOf(id, round, code, secret)
  return R.Hash(id .. ":" .. round .. ":" .. code .. ":" .. secret)
end
R.CommitOf = commitOf

---------------------------------------------------------------- listeners (the scene)
local function notify(ev, ...)
  local fn = R.OnChange
  if fn then fn(ev, ...) end
  if TCF.MarkDirty then TCF:MarkDirty() end
end

local function store() return DR.Store() end

---------------------------------------------------------------- against the house cat
local solo, lastSolo

local function soloSave() store().rpsSolo = solo end

local function collect()
  -- the win is paid once the reveal has played on screen (UI_RPS.lua collects it then)
  if not (R.Animating and R.Animating()) then TCF:CasinoCollect(GAME) end
end

-- pick a sign against the house cat. Starts a game for bet (the bet is placed) unless one is
-- waiting after a tie (then it is free). Returns true, or false and a message.
function TCF:RPSSoloPlay(sign, bet)
  if not self.db or not CODE[sign] then return false end
  local g = solo
  if not g then
    if DR.Busy and DR.Busy() then return false, "Finish your death roll first." end
    local d = R.duel
    if d and d.state ~= "over" then return false, "Finish your game with your friend first." end
    bet = tonumber(bet)
    if not bet or not DR.ValidBet(bet) then
      local lo, hi = DR.Limits()
      if hi < lo then return false, string.format("You need at least %d TapCoins to play.", lo * 2) end
      return false, string.format("Bets go from %s to %s TapCoins right now.", TCF.Commas(lo), TCF.Commas(hi))
    end
    local ok = self.CasinoBet and self:CasinoBet(bet, GAME) or (not self.CasinoBet and self:SpendCoins(bet))
    if not ok then return false, "That bet can't be placed right now." end
    g = { bet = bet, house = DR.PickHouse(), round = 1, rounds = {} }
    solo, lastSolo = g, nil
  end
  local house = R.SIGNS[random(3)]
  local res = R.Outcome(sign, house)
  g.rounds[#g.rounds + 1] = { me = sign, opp = house, res = res }
  while #g.rounds > 20 do table.remove(g.rounds, 1) end
  g.me, g.opp, g.res = sign, house, res
  if res == "tie" then
    g.round = g.round + 1
    soloSave()
    notify("reveal", "solo", sign, house, "tie")
    return true
  end
  g.over, g.result = true, res
  local paid = 0
  if res == "win" then
    paid = R.Payout(g.bet)
    if self.CasinoHold then self:CasinoHold(paid, GAME, nil, g.bet) else self:AddCoins(paid) end
  end
  g.paid = paid
  local st = store()
  st.rpsPlayed = (st.rpsPlayed or 0) + 1
  if res == "win" then st.rpsWon = (st.rpsWon or 0) + 1 end
  solo, lastSolo = nil, g
  st.rpsSolo = nil
  notify("reveal", "solo", sign, house, res)
  notify("end", "solo", res == "win" and "house" or "me", paid)
  if paid > 0 and self.CasinoCollect then collect() end
  return true
end

-- the game on screen (the running one, or the last one) and whether one is running
function TCF:RPSSolo() return solo or lastSolo, solo ~= nil end

---------------------------------------------------------------- the game with a party member
-- R.duel = { id, role = "out" (you challenged) or "in", opp, oppBase, bet, state = "asking" /
--   "invited" / "picking" / "reveal" / "done" / "over", round, roundAt, expires, myPick, mySecret,
--   oppHash, oppPick, revealAt, doneAt, rounds = { { me, opp, res } }, loser = "me" / "opp",
--   result, reason, by }
local muted = {}
local function roleOf(who, d)
  if who == "me" then return d.role == "out" and "c" or "t" end
  return d.role == "out" and "t" or "c"
end
local function whoOf(r, d)
  if r == "c" then return d.role == "out" and "me" or "opp" end
  return d.role == "out" and "opp" or "me"
end

local REASONS = {
  x = "%s called it off.",
  t = "Time ran out, so the game was called off.",
  r = "%s reloaded or logged out, so the game was called off.",
  c = "%s doesn't have enough TapCoins for that bet any more.",
  g = "%s is no longer in your group.",
  m = "%s's pick didn't match the one locked in, so the game was called off.",
  v = "%s's pick never came through, so the game was called off.",
  n = "%s's addon never confirmed the result, so the game was called off.",
  p = "%s didn't pick in time, so the game was called off.",
  e = "The game couldn't be played to the end, so it was called off.",
}
R.REASONS = REASONS
R.REASONS_ME = {
  x = "You called it off.",
  r = "You reloaded or logged out, so the game was called off.",
  c = "You don't have enough TapCoins for that bet any more.",
  g = "You left the group, so the game was called off.",
  p = "You didn't pick in time, so the game was called off.",
}

local function saveDuel(d)
  local st = store()
  if d and d.state ~= "over" and d.state ~= "invited" then st.rps = { id = d.id, opp = d.opp } else st.rps = nil end
end

local function finish(d, result, reason, by)
  d.state, d.result, d.reason, d.by = "over", result, reason, by
  d.endedAt = now()
  if result ~= "win" and result ~= "lose" then DR.Release(d.id) end
  saveDuel(nil)
  notify("end", "duel", result, reason)
end

local function callOff(reason, tell, by)
  local d = R.duel
  if not d or d.state == "over" then return end
  if tell then send("R3", d.id, reason) end
  finish(d, "cancel", reason, by or "me")
end
R.CallOff = callOff

-- the loser pays the bet, the winner gets it (even, no fee). Each side once.
local function settle(d)
  if d.settled or d.state == "over" then return end
  d.settled = true
  local won = d.loser == "opp"
  DR.Release(d.id)
  local delta = won and d.bet or -d.bet
  if TCF.CasinoSettleDuel then TCF:CasinoSettleDuel(delta, d.opp, d.bet, GAME)
  elseif delta > 0 then TCF:AddCoins(delta) else TCF:SpendCoins(-delta) end
  local st = store()
  st.rpsDuels = (st.rpsDuels or 0) + 1
  if won then st.rpsDuelsWon = (st.rpsDuelsWon or 0) + 1 end
  d.replies = 0
  finish(d, won and "win" or "lose")
end

local function newId() return string.format("%06x", random(0, 0xffffff)) end

local function busy()
  local d = R.duel
  return solo ~= nil or (d ~= nil and d.state ~= "over")
end
R.Busy = busy
-- the death roll waits while a game here runs (and the other way round)
DR.OtherBusy = busy

local function lockdown()
  if C_ChatInfo and C_ChatInfo.InChatMessagingLockdown then
    local ok, v = pcall(C_ChatInfo.InChatMessagingLockdown)
    if ok and v and not isSecret(v) then return true end
  end
  return false
end

local function startRound(d, round)
  d.state, d.round, d.roundAt = "picking", round, now()
  d.myPick, d.mySecret, d.oppHash, d.oppPick, d.revealAt, d.sentAt = nil, nil, nil, nil, nil, nil
  local early = d.nextHash
  if early and early.round == round then d.oppHash = early.hash end
  d.nextHash = nil
end

-- challenge a party member (name from TCF:PartyMembers) for bet TapCoins
function TCF:RPSChallenge(name, bet)
  if not self.db then return false end
  bet = tonumber(bet)
  if busy() then return false, "You already have a game of rock paper scissors going." end
  if DR.Busy and DR.Busy() then return false, "Finish your death roll first." end
  if not inGroup() then return false, "Join a party or raid with a friend who has TapCatForever." end
  if InCombatLockdown and InCombatLockdown() then return false, "Games can't start in combat." end
  if lockdown() then return false, "The game is blocking addon messages right now. Try again in a moment." end
  local m = DR.Member(name)
  if not m or isMe(m.name) then return false, "Pick a friend in your group who has TapCatForever." end
  -- (1.6.0) same check as death roll: their addon must have the casino
  if DR.CheckFriend then
    local okFriend, why = DR.CheckFriend(m.name)
    if not okFriend then return false, why end
  end
  if not bet or not DR.ValidBet(bet) then
    local lo, hi = DR.Limits()
    return false, string.format("Bets go from %s to %s TapCoins right now.", TCF.Commas(lo), TCF.Commas(max(lo, hi)))
  end
  local d = { id = newId(), role = "out", opp = m.name, oppBase = base(m.name), bet = bet, state = "asking",
              expires = now() + R.INVITE_TIME, round = 1, rounds = {} }
  R.duel = d
  saveDuel(d)
  send("R1", d.id, DR.TargetName and DR.TargetName(m) or m.name, bet)
  notify("state", "duel")
  return true
end

-- answer the challenge you were sent
function TCF:RPSAnswer(accept)
  local d = R.duel
  if not d or d.state ~= "invited" then return false end
  if not accept then
    send("R2", d.id, "n")
    muted[d.oppBase or ""] = now() + MUTE_AFTER_NO
    finish(d, "declined", nil, "me")
    return true
  end
  if solo or (DR.Busy and DR.Busy()) then
    send("R2", d.id, "b")
    finish(d, "cancel", "x", "me")
    return false, "Finish your other game first."
  end
  if not DR.ValidBet(d.bet) or not DR.Hold(d.id, d.bet) then
    send("R2", d.id, "c")
    finish(d, "cancel", "c", "me")
    return false, "You don't have enough TapCoins for that bet any more."
  end
  startRound(d, 1)
  send("R2", d.id, "y")
  saveDuel(d)
  notify("state", "duel")
  return true
end

function TCF:RPSWithdraw()
  local d = R.duel
  if not d or d.state ~= "asking" then return false end
  callOff("x", true)
  return true
end

local function sendReveal(d)
  d.sentAt = now()
  send("R5", d.id, d.round, CODE[d.myPick], d.mySecret)
end

-- both picks are locked in: show mine
local function toReveal(d)
  d.state, d.revealAt = "reveal", now()
  sendReveal(d)
  notify("locked", "duel")
end

-- your pick in the game with your friend: only its hash leaves your addon for now
function TCF:RPSPick(sign)
  local d = R.duel
  if not d or d.state ~= "picking" or d.myPick or not CODE[sign] then return false end
  d.myPick, d.mySecret = sign, newSecret()
  send("R4", d.id, d.round, commitOf(d.id, d.round, CODE[sign], d.mySecret))
  notify("picked", "duel")
  if d.oppHash then toReveal(d) end
  return true
end

function TCF:RPSDuel() return R.duel end

---------------------------------------------------------------- incoming addon messages
local function onChallenge(sender, id, target, bet, s)
  if not isMe(target) then return end
  bet = tonumber(bet)
  if not bet or bet ~= floor(bet) or bet < 1 or bet > (DR.MSG_BET_MAX or 1e15) then return end
  local t = now()
  if s.lastRps and t - s.lastRps < CHALLENGE_GAP then return end
  s.lastRps = t
  local b = base(sender)
  if muted[b] and t < muted[b] then return end
  muted[b] = nil
  local m = DR.Member(sender)
  if not m then return end
  local d = R.duel
  if d and d.state ~= "over" then
    if d.id ~= id then send("R2", id, "b") end
    return
  end
  if solo or (DR.Busy and DR.Busy()) or (InCombatLockdown and InCombatLockdown()) or lockdown() then send("R2", id, "b"); return end
  if not DR.ValidBet(bet) then
    send("R2", id, "c")
    R.duel = { id = id, role = "in", opp = m.name, oppBase = base(m.name), bet = bet, state = "over", result = "toohigh",
               round = 1, rounds = {}, endedAt = t }
    notify("end", "duel", "toohigh")
    return
  end
  R.duel = { id = id, role = "in", opp = m.name, oppBase = base(m.name), bet = bet, state = "invited",
             expires = t + R.INVITE_TIME, round = 1, rounds = {} }
  if TCF.PlaySound then TCF:PlaySound("click") end
  notify("invite", "duel")
end

local function onAnswer(d, answer)
  if d.state ~= "asking" then
    if answer == "y" and d.state == "over" and d.result ~= "win" and d.result ~= "lose" and not d.toldOff then
      d.toldOff = true
      send("R3", d.id, d.reason or "t")
    end
    return
  end
  if answer == "y" then
    if not DR.ValidBet(d.bet) or not DR.Hold(d.id, d.bet) then
      send("R3", d.id, "c")
      finish(d, "cancel", "c", "me")
      return
    end
    startRound(d, 1)
    saveDuel(d)
    if TCF.PlaySound then TCF:PlaySound("click") end
    notify("state", "duel")
  elseif answer == "n" then finish(d, "declined", nil, "opp")
  elseif answer == "b" then finish(d, "busy", nil, "opp")
  elseif answer == "c" then finish(d, "toohigh", nil, "opp") end
end

local function onCommit(d, round, hash)
  if not hash:match("^%x%x%x%x%x%x%x%x$") then return end
  if d.state == "picking" and round == d.round then
    if d.oppHash and d.oppHash ~= hash then callOff("m", true); return end
    d.oppHash = hash
    notify("oppPicked", "duel")
    if d.myPick then toReveal(d) end
  elseif (d.state == "picking" or d.state == "reveal") and round == d.round + 1 then
    d.nextHash = { round = round, hash = hash }   -- they are a round ahead (our reveal reached them first)
  end
end

local function onReveal(d, round, code, secret)
  local sign = SIGN[code]
  if not sign or not secret:match("^[%w]+$") or #secret < 12 or #secret > 32 then return end
  if round == d.round and (d.state == "reveal" or d.state == "picking") then
    if not d.oppHash then return end                      -- a reveal before its commit: ignored
    if commitOf(d.id, round, code, secret) ~= d.oppHash then callOff("m", true); return end
    if d.state ~= "reveal" then return end                -- we haven't picked: can't be (they only reveal after our commit)
    d.oppPick = sign
    local res = R.Outcome(d.myPick, sign)
    d.rounds[#d.rounds + 1] = { me = d.myPick, opp = sign, res = res }
    d.me, d.opp_, d.res = d.myPick, sign, res
    if res == "tie" then
      d.prev = { round = round, code = CODE[d.myPick], secret = d.mySecret }
      notify("reveal", "duel", d.myPick, sign, "tie")
      if round >= MAX_ROUNDS then callOff("e", true); return end
      startRound(d, round + 1)
      saveDuel(d)
      return
    end
    d.prev = { round = round, code = CODE[d.myPick], secret = d.mySecret }
    -- a result: say who lost, then wait for the other side to agree (see settleIfAgreed)
    d.loser, d.state, d.doneAt = res == "lose" and "me" or "opp", "done", now()
    d.seenAt = now()
    send("R6", d.id, round, roleOf(d.loser, d))
    saveDuel(d)
    notify("reveal", "duel", d.myPick, sign, res)
    local early = d.peerSeen
    d.peerSeen = nil
    if early and early.round == round then R.OnSeen(d, round, early.loser) end
  elseif d.prev and round == d.prev.round and (d.state ~= "over" or d.result == "lose") then
    -- they are still waiting for our reveal of that round: say it again (a few times at most)
    d.replies = (d.replies or 0) + 1
    if d.replies <= 6 then send("R5", d.id, d.prev.round, d.prev.code, d.prev.secret) end
  end
end

-- R6: the other side checked both picks and names the loser
local function onSeen(d, round, loser)
  if round ~= d.round then return end
  if d.state == "reveal" then
    d.peerSeen = { round = round, loser = loser }      -- their word came before their pick: keep it
  elseif d.state == "done" then
    if whoOf(loser, d) ~= d.loser then callOff("m", true); return end
    if d.loser == "me" and not d.settled then
      -- both sides agree I lost: pay, then tell the winner (its addon pays it only on this)
      send("R7", d.id, round, roleOf("me", d))
      settle(d)
    end
  elseif d.state == "over" and d.result == "lose" then
    -- the winner didn't hear that I paid: say it again (a few times at most)
    d.replies = (d.replies or 0) + 1
    if d.replies <= 6 then send("R7", d.id, round, roleOf("me", d)) end
  end
end
R.OnSeen = onSeen

-- R7: the loser paid; the winner is paid now
local function onPaid(d, round, loser)
  if d.state ~= "done" or round ~= d.round or d.loser ~= "opp" then return end
  if whoOf(loser, d) ~= "opp" then callOff("m", true); return end
  settle(d)
end

local function onAddon(prefix, text, channel, sender)
  if isSecret(prefix) or prefix ~= "TapCatFvr" then return end
  if isSecret(text) or type(text) ~= "string" or text:sub(1, 1) ~= "R" or #text > 200 then return end
  if isSecret(channel) or (channel ~= "PARTY" and channel ~= "RAID" and channel ~= "INSTANCE_CHAT") then return end
  if isSecret(sender) or type(sender) ~= "string" or sender == "" or isMe(sender) then return end
  local kind, ver, id, a, b, c = text:match("^(R%d);(%d+);(%x%x%x%x%x%x);([^;]*);?([^;]*);?([^;]*)$")
  if not kind or ver ~= VER then return end
  local ok, s = DR.Allow(sender)
  if not ok then return end
  if kind == "R1" then
    if a ~= "" and b ~= "" and c == "" then onChallenge(sender, id, a, b, s) end
    return
  end
  local d = R.duel
  if not d or d.id ~= id or base(sender) ~= d.oppBase then return end
  if d.state ~= "over" and DR.OppHeard then DR.OppHeard(d) end   -- they are here right now
  local round = tonumber(a)
  if kind == "R2" then
    if d.role == "out" then onAnswer(d, a) end
  elseif kind == "R3" then
    if REASONS[a] and d.state ~= "over" then
      if d.state == "invited" and a == "t" then muted[d.oppBase or ""] = now() + MUTE_AFTER_NO end
      finish(d, "cancel", a, "opp")
    end
  elseif not round or round ~= floor(round) or round < 1 or round > MAX_ROUNDS then
    return
  elseif kind == "R4" then
    if b ~= "" and c == "" then onCommit(d, round, b) end
  elseif kind == "R5" then
    if b ~= "" and c ~= "" then onReveal(d, round, b, c) end
  elseif kind == "R6" then
    if (b == "c" or b == "t") and c == "" then onSeen(d, round, b) end
  elseif kind == "R7" then
    if (b == "c" or b == "t") and c == "" then onPaid(d, round, b) end
  end
end
R.OnAddon = onAddon

---------------------------------------------------------------- timers
local function tick()
  local t = now()
  local d = R.duel
  if not d or d.state == "over" then return end
  if d.state == "asking" and t >= d.expires then
    callOff("t", true)
  elseif d.state == "invited" and t >= d.expires then
    send("R2", d.id, "n")
    muted[d.oppBase or ""] = t + MUTE_AFTER_NO
    finish(d, "expired", nil, "me")
  elseif d.state == "picking" or d.state == "reveal" then
    if not inGroup() then callOff("g", false)
    -- gone by the addon's own knowledge (Party.lua, after a grace period: DeathRoll.lua's OppPresent)
    elseif DR.OppPresent and not DR.OppPresent(d) then callOff("g", false, "opp")
    elseif d.state == "picking" then
      if not d.myPick and t - d.roundAt >= R.PICK_TIME then callOff("p", true)
      elseif d.myPick and t - d.roundAt >= R.PICK_TIME + PICK_GRACE then callOff("t", true) end
    else
      -- the other pick must be shown within R.REVEAL_TIME of both being locked in
      if t - d.revealAt >= R.REVEAL_TIME then callOff("v", true)
      elseif t - (d.sentAt or 0) >= RESEND then sendReveal(d) end
    end
  elseif d.state == "done" then
    -- both picks checked: wait for the other side's word (the loser pays on it, the winner is paid
    -- on the loser's "I paid"); nothing else moves TapCoins, and running out of time moves none
    if t - d.doneAt >= R.DONE_WAIT then callOff("n", true)
    elseif t - (d.sentAt or 0) >= RESEND then
      sendReveal(d)
      send("R6", d.id, d.round, roleOf(d.loser, d))
    end
  end
end
R.Tick = tick

---------------------------------------------------------------- login: a /reload calls a game with a friend off
local function restore()
  local st = store()
  if type(st.rpsSolo) == "table" and not solo then
    local g = st.rpsSolo
    if tonumber(g.bet) and type(g.house) == "table" and type(g.rounds) == "table" and tonumber(g.round) then
      solo = g
    else
      st.rpsSolo = nil
    end
  end
  -- the held bet comes back through DeathRoll.lua's restore (one hold for both games); tell them
  local sd = st.rps
  if type(sd) == "table" and type(sd.id) == "string" and sd.id:match("^%x%x%x%x%x%x$") then
    R.reloadCancel = { id = sd.id }
  end
  st.rps = nil
end

local ev = CreateFrame("Frame")
R.frame = ev
for _, e in ipairs({ "CHAT_MSG_ADDON", "GROUP_ROSTER_UPDATE", "PLAYER_LOGIN" }) do pcall(ev.RegisterEvent, ev, e) end

local restored = false
ev:SetScript("OnEvent", function(_, event, a1, a2, a3, a4)
  if not TCF.db then return end
  if not restored then restored = true; restore() end
  if event == "CHAT_MSG_ADDON" then onAddon(a1, a2, a3, a4)
  elseif event == "GROUP_ROSTER_UPDATE" then
    local d = R.duel
    if d and (d.state == "asking" or d.state == "invited" or d.state == "picking" or d.state == "reveal") and not inGroup() then
      callOff("g", false)
    end
  end
end)

local acc = 0
ev:SetScript("OnUpdate", function(_, elapsed)
  acc = acc + elapsed
  if acc < 0.2 then return end
  acc = 0
  if not TCF.db then return end
  if not restored then restored = true; restore() end
  local rc = R.reloadCancel
  if rc and inGroup() then
    R.reloadCancel = nil
    send("R3", rc.id, "r")
  end
  tick()
end)
