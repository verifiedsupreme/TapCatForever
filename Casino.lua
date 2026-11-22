-- TapCatForever: the Casino's money and its games' rules (the tab is drawn by UI_Casino.lua).
--   Money: TCF:CasinoLimits(), TCF:CasinoBet(), TCF:CasinoPay(), TCF:CasinoSettleDuel() and the
--   stats in TCF.db.casino (account-wide, like TapCoins). Every game here keeps a house edge, so on
--   average the casino takes TapCoins out of the game, never puts them in. There is no free spin.
--   Winnings and stakes are kept out of "TapCoins earned" and "TapCoins spent" (achievements and
--   the leaderboard), so playing can't farm those.
--   Slots: three reel strips and a pay table (RTP worked out exactly by TCF:SlotsExactRTP()).
--   Blackjack: a 6-deck shoe, dealer stands on soft 17, blackjack pays 3 to 2, double on any two
--   cards, split once, no insurance. The hand lives in TCF.db.casino.bj, so it survives closing the
--   window or a reload.
--   Payouts wait in TCF.db.casino.pending until the game's animation ends (UI_Casino.lua collects
--   them); anything still waiting is paid at login, when the tab closes, or on the next bet.
local ADDON, TCF = ...
local floor, min, max, random = math.floor, math.min, math.max, math.random

TCF.CASINO_GAMES = {
  { key = "slots", name = "Slots" },
  { key = "blackjack", name = "Blackjack" },
  { key = "deathroll", name = "Death roll" },
  { key = "rps", name = "Rock paper scissors" },
}
TCF.CASINO_MIN_BET, TCF.CASINO_MAX_BET = 10, 500

local function num(v)
  if TCF.IsSecret(v) then return nil end
  v = tonumber(v)
  if not v or v ~= v or v == math.huge or v == -math.huge then return nil end
  return v
end

local function newStats() return { played = 0, wagered = 0, won = 0, biggest = 0 } end
local GAME_KEY = {}
for _, g in ipairs(TCF.CASINO_GAMES) do GAME_KEY[g.key] = true end

-- TCF.db.casino, made and repaired on first use
function TCF:CasinoData()
  local db = self.db
  local c = db.casino
  if type(c) ~= "table" then c = {}; db.casino = c end
  for _, g in ipairs(TCF.CASINO_GAMES) do
    if type(c[g.key]) ~= "table" then c[g.key] = newStats() end
  end
  if type(c.total) ~= "table" then c.total = newStats() end
  for _, k in ipairs({ "total", "slots", "blackjack", "deathroll", "rps" }) do
    local s = c[k]
    for _, f in ipairs({ "played", "wagered", "won", "biggest" }) do s[f] = num(s[f]) or 0 end
  end
  if type(c.pending) ~= "table" then c.pending = {} end
  return c
end

-- Bet limits: at least 10, at most the lower of 500 and a quarter of your TapCoins.
-- max < min means you can't play right now (fewer than 40 TapCoins).
function TCF:CasinoLimits()
  local coins = num(self.db and self.db.coins) or 0
  return TCF.CASINO_MIN_BET, min(TCF.CASINO_MAX_BET, floor(coins / 4))
end

-- Clamp a bet to the limits (nil when you can't play)
function TCF:CasinoClampBet(amount)
  local lo, hi = self:CasinoLimits()
  if hi < lo then return nil end
  amount = floor(num(amount) or lo)
  return max(lo, min(hi, amount))
end

local function addStat(c, game, field, n)
  local s = c[game]
  if s then s[field] = (s[field] or 0) + n end
  c.total[field] = (c.total[field] or 0) + n
end

-- Takes a stake. extra = true for a blackjack double or split: the same stake again, which only
-- needs the TapCoins (the limits are for the bet you start a round with). Returns true or false.
function TCF:CasinoBet(amount, game, extra)
  amount = num(amount)
  if not amount or amount ~= floor(amount) or amount <= 0 then return false end
  local c = self:CasinoData()
  if not GAME_KEY[game] then return false end
  self:CasinoCollect(game)
  if not extra then
    local lo, hi = self:CasinoLimits()
    if amount < lo or amount > hi then return false end
  end
  if (num(self.db.coins) or 0) < amount then return false end
  self.db.coins = self.db.coins - amount
  addStat(c, game, "wagered", amount)
  if not extra then addStat(c, game, "played", 1) end
  self:MarkDirty()
  return true
end

-- Pays winnings (the whole amount handed back, stake included) at once. stake: what was bet for
-- them, so "Biggest win" counts the profit (a push or a 2x line on a small bet is not a big win).
function TCF:CasinoPay(amount, game, stake)
  amount = floor(num(amount) or 0)
  if amount <= 0 then return 0 end
  local c = self:CasinoData()
  if not GAME_KEY[game] then game = nil end
  self.db.coins = self.db.coins + amount
  local profit = amount - max(0, floor(num(stake) or 0))
  if game then
    addStat(c, game, "won", amount)
    if profit > 0 then c[game].biggest = max(c[game].biggest, profit) end
  else
    c.total.won = c.total.won + amount
  end
  if profit > 0 then c.total.biggest = max(c.total.biggest, profit) end
  self:MarkDirty()
  return amount
end

-- Winnings that wait for the game's animation. stat: an achievement counter (db.stats) to add
-- one to when it is paid. stake: the bet those winnings were for (see CasinoPay).
function TCF:CasinoHold(amount, game, stat, stake)
  local c = self:CasinoData()
  local p = c.pending[game]
  if type(p) ~= "table" then p = { amount = 0 }; c.pending[game] = p end
  p.amount = (num(p.amount) or 0) + floor(num(amount) or 0)
  p.stake = (num(p.stake) or 0) + floor(num(stake) or 0)
  if stat then p.stats = p.stats or {}; table.insert(p.stats, stat) end
end

-- Pays what a game (or every game, game = nil) still owes. Returns the TapCoins paid.
function TCF:CasinoCollect(game)
  local c = self:CasinoData()
  local paid = 0
  for g, p in pairs(c.pending) do
    if game == nil or g == game then
      c.pending[g] = nil
      if type(p) == "table" then
        paid = paid + self:CasinoPay(p.amount, g, p.stake)
        for _, st in ipairs(type(p.stats) == "table" and p.stats or {}) do
          if type(st) == "string" then self.db.stats[st] = (self.db.stats[st] or 0) + 1 end
        end
      end
    end
  end
  if game == nil or game == "blackjack" then
    local st = c.bj
    if type(st) == "table" and st.phase == "done" then st.collected = true end
  end
  return paid
end

-- Party death roll and rock paper scissors: moves TapCoins between you and another player. delta > 0
-- credits you, < 0 debits you (never below zero), at most the top bet either way. stake: the bet of
-- the duel (for the stats: it counts as bet, and a win counts stake + delta as paid back, so the net
-- is right). game: "deathroll" (the default) or "rps", for the stats. Logged in TCF.db.casino.duels
-- (the last 20). Returns the change really made.
function TCF:CasinoSettleDuel(delta, opponent, stake, game)
  delta = num(delta)
  if not delta then return 0 end
  delta = floor(delta + 0.5)
  delta = max(-TCF.CASINO_MAX_BET, min(TCF.CASINO_MAX_BET, delta))
  local c = self:CasinoData()
  local coins = num(self.db.coins) or 0
  if delta < 0 then delta = -min(-delta, coins) end
  if delta == 0 then return 0 end
  self.db.coins = coins + delta
  stake = num(stake)
  stake = stake and max(0, min(TCF.CASINO_MAX_BET, floor(stake))) or (delta < 0 and -delta or 0)
  if game ~= "rps" then game = "deathroll" end
  local s = c[game]
  s.duels = (s.duels or 0) + 1
  s.net = (s.net or 0) + delta
  addStat(c, game, "played", 1)
  addStat(c, game, "wagered", stake)
  local back = max(0, stake + delta)
  if back > 0 then addStat(c, game, "won", back) end
  if delta > 0 then
    s.biggest = max(s.biggest, delta); c.total.biggest = max(c.total.biggest, delta)
  end
  if type(opponent) ~= "string" or TCF.IsSecret(opponent) or opponent == "" then opponent = "another player" end
  c.duels = type(c.duels) == "table" and c.duels or {}
  table.insert(c.duels, { t = time and time() or 0, opp = opponent:sub(1, 48), delta = delta, game = game })
  while #c.duels > 20 do table.remove(c.duels, 1) end
  self:MarkDirty()
  return delta
end

-- One line for the stats bar: a game's numbers, or the account totals (game = nil)
function TCF:CasinoStatsLine(game)
  local c = self:CasinoData()
  local s = (game and c[game]) or c.total
  local C = TCF.Commas
  local net = s.won - s.wagered
  return string.format("Played %s   Total bet %s   Paid back %s   Net %s%s|r   Biggest win %s",
    C(s.played), C(s.wagered), C(s.won), net >= 0 and "|cff40ff40+" or "|cffff6060-", C(math.abs(net)), C(s.biggest))
end

---------------------------------------------------------------- slots
-- Three reel strips of 20 stops, each with its own mix, so the rarer a line the more it pays:
-- three cats 1 in 1,000, gems 1 in 667, bells 1 in 500, coins 1 in 400, fish 1 in 296,
-- yarn balls 1 in 222, paws 1 in 178. Two cats on each reel. One line: the middle row.
TCF.SLOT_SYMBOLS = {
  cat = { name = "Cat", art = "sym_cat" }, gem = { name = "Gem", art = "sym_gem" },
  bell = { name = "Bell", art = "sym_bell" }, coin = { name = "Coin", art = "sym_coin" },
  fish = { name = "Fish", art = "sym_fish" }, yarn = { name = "Yarn ball", art = "sym_yarn" },
  paw = { name = "Paw", art = "sym_paw" },
}
TCF.SLOT_REELS = {
  { "cat", "paw", "yarn", "fish", "paw", "bell", "yarn", "coin", "paw", "gem", "fish", "yarn", "paw", "cat", "fish", "paw", "yarn", "bell", "coin", "gem" },
  { "paw", "gem", "coin", "fish", "cat", "coin", "yarn", "bell", "coin", "paw", "fish", "gem", "coin", "yarn", "cat", "fish", "paw", "bell", "yarn", "coin" },
  { "yarn", "bell", "paw", "cat", "fish", "gem", "bell", "yarn", "coin", "paw", "bell", "fish", "gem", "cat", "yarn", "bell", "paw", "fish", "gem", "coin" },
}
-- what a line pays, as times your bet (your bet included)
TCF.SLOT_PAY3 = { cat = 100, gem = 40, bell = 25, coin = 15, fish = 10, yarn = 5, paw = 3 }
TCF.SLOT_PAY_TWO_CATS, TCF.SLOT_PAY_ONE_CAT = 5, 2
TCF.SLOT_ORDER = { "cat", "gem", "bell", "coin", "fish", "yarn", "paw" }
TCF.SLOT_BIG_WIN = 10  -- this many times the bet or more: the big celebration

-- multiplier and the kind of line ("three", "twocats", "onecat" or nil)
function TCF.SlotsPay(a, b, c)
  if a == b and b == c and TCF.SLOT_PAY3[a] then return TCF.SLOT_PAY3[a], "three" end
  local cats = (a == "cat" and 1 or 0) + (b == "cat" and 1 or 0) + (c == "cat" and 1 or 0)
  if cats == 2 then return TCF.SLOT_PAY_TWO_CATS, "twocats" end
  if cats == 1 then return TCF.SLOT_PAY_ONE_CAT, "onecat" end
  return 0, nil
end

-- the symbol at a stop (wraps around the strip)
function TCF.SlotSymbol(reel, stop)
  local strip = TCF.SLOT_REELS[reel]
  return strip[(stop - 1) % #strip + 1]
end

-- the exact return to player (every stop combination) and how often a line pays
function TCF:SlotsExactRTP()
  local R = TCF.SLOT_REELS
  local total, ret, hits = 0, 0, 0
  for _, a in ipairs(R[1]) do
    for _, b in ipairs(R[2]) do
      for _, c in ipairs(R[3]) do
        local m = TCF.SlotsPay(a, b, c)
        total = total + 1; ret = ret + m
        if m > 0 then hits = hits + 1 end
      end
    end
  end
  return ret / total, hits / total
end

-- Spin: takes the bet, picks the stops and holds the win for the reels to land.
-- Returns the result table (also TCF.db.casino.slotsLast) or nil when the bet can't be taken.
function TCF:SlotsSpin(bet, stops)
  if not self:CasinoBet(bet, "slots") then return nil end
  local c = self:CasinoData()
  -- stops: tests pass them in; play rolls them
  local s = {}
  for i = 1, 3 do
    local n = #TCF.SLOT_REELS[i]
    s[i] = (stops and stops[i]) and ((floor(stops[i]) - 1) % n + 1) or random(n)
  end
  local a, b, cc = TCF.SlotSymbol(1, s[1]), TCF.SlotSymbol(2, s[2]), TCF.SlotSymbol(3, s[3])
  local mult, kind = TCF.SlotsPay(a, b, cc)
  local last = c.slotsLast
  local res = { id = ((type(last) == "table" and num(last.id)) or 0) + 1, stops = s, symbols = { a, b, cc },
                bet = bet, mult = mult, kind = kind, win = mult * bet }
  c.slotsLast = res
  if res.win > 0 then
    self:CasinoHold(res.win, "slots", (kind == "three" and a == "cat") and "casinoCats" or nil, bet)
  end
  return res
end

---------------------------------------------------------------- blackjack
TCF.BJ_DECKS = 6
TCF.BJ_RESHUFFLE = 0.25   -- a new shoe when a quarter of it is left
local SHOE_SIZE = 52 * 6
TCF.BJ_RANKS = { "A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K" }
TCF.BJ_SUITS = { "spades", "hearts", "clubs", "diamonds" }

-- card codes 1-52: rank (1 = ace ... 13 = king) and suit (1-4)
function TCF.BJCard(code) return (code - 1) % 13 + 1, floor((code - 1) / 13) + 1 end
local function cardValue(code)
  local r = (code - 1) % 13 + 1
  if r == 1 then return 11 end
  return r >= 10 and 10 or r
end
TCF.BJCardValue = cardValue

-- total, soft (an ace still counted as 11)
function TCF.BJTotal(cards)
  local t, aces = 0, 0
  for _, code in ipairs(cards) do
    local v = cardValue(code)
    t = t + v
    if v == 11 then aces = aces + 1 end
  end
  while t > 21 and aces > 0 do t = t - 10; aces = aces - 1 end
  return t, aces > 0
end

-- The shoe is kept as how many of each card are left (never the order, so the saved file can't
-- show the next card). Drawing picks one of the cards left at random: the same as a shuffled shoe.
local function newShoe(c)
  local counts = {}
  for i = 1, 52 do counts[i] = TCF.BJ_DECKS end
  c.shoe = { counts = counts, left = 52 * TCF.BJ_DECKS }
end

local function validShoe(c)
  local sh = c.shoe
  if type(sh) ~= "table" or type(sh.counts) ~= "table" then return false end
  local n = 0
  for i = 1, 52 do
    local k = num(sh.counts[i])
    if not k or k < 0 or k > TCF.BJ_DECKS then return false end
    n = n + k
  end
  sh.left = n
  return n > 0
end

local function draw(c)
  local sh = c.shoe
  if not validShoe(c) then newShoe(c); sh = c.shoe end
  -- tools/tests/test_casino.py stacks the next cards here (never set in play)
  local stacked = type(TCF.bjTestStack) == "table" and table.remove(TCF.bjTestStack, 1)
  if stacked and sh.counts[stacked] and sh.counts[stacked] > 0 then
    sh.counts[stacked] = sh.counts[stacked] - 1; sh.left = sh.left - 1
    return stacked
  end
  local r = random(sh.left)
  for i = 1, 52 do
    r = r - sh.counts[i]
    if r <= 0 then
      sh.counts[i] = sh.counts[i] - 1
      sh.left = sh.left - 1
      return i
    end
  end
  return 1  -- not reached
end
TCF.BJDrawForTests = function() return draw(TCF:CasinoData()) end

function TCF:BJState()
  local st = self:CasinoData().bj
  if type(st) ~= "table" or type(st.hands) ~= "table" or type(st.dealer) ~= "table" then return nil end
  return st
end

function TCF:BJInPlay()
  local st = self:BJState()
  return st and st.phase == "player" or false
end

local function isPair(h)
  return #h.cards == 2 and cardValue(h.cards[1]) == cardValue(h.cards[2])
end

-- what the active hand may do now
function TCF:BJCanHit()
  local st = self:BJState()
  local h = st and st.phase == "player" and st.hands[st.active]
  return h and not h.done or false
end
function TCF:BJCanDouble()
  local st = self:BJState()
  local h = st and st.phase == "player" and st.hands[st.active]
  return (h and not h.done and #h.cards == 2 and (num(self.db.coins) or 0) >= h.bet) and true or false
end
function TCF:BJCanSplit()
  local st = self:BJState()
  local h = st and st.phase == "player" and st.hands[st.active]
  return (h and not h.done and #st.hands == 1 and isPair(h) and (num(self.db.coins) or 0) >= h.bet) and true or false
end

local RESULT_TEXT = { win = "Win", lose = "Lose", push = "Push", bust = "Bust", bj = "Blackjack" }

-- dealer plays (stands on every 17, soft or hard), then every hand is paid
local function finish(self, st, c)
  st.phase = "done"
  st.holeShown = true
  local live = false
  for _, h in ipairs(st.hands) do if h.result ~= "bust" then live = true end end
  if live then
    while true do
      local t = TCF.BJTotal(st.dealer)
      if t >= 17 then break end
      table.insert(st.dealer, draw(c))
    end
  end
  local d = TCF.BJTotal(st.dealer)
  local dealerBust = d > 21
  st.dealerBust = live and dealerBust or false
  local pay, staked = 0, 0
  for _, h in ipairs(st.hands) do
    staked = staked + h.bet
    if h.result ~= "bust" then
      local p = TCF.BJTotal(h.cards)
      if dealerBust or p > d then h.result, h.pay = "win", h.bet * 2
      elseif p == d then h.result, h.pay = "push", h.bet
      else h.result, h.pay = "lose", 0 end
    else
      h.pay = 0
    end
    pay = pay + h.pay
  end
  st.pay, st.staked = pay, staked
  if pay > 0 then self:CasinoHold(pay, "blackjack", nil, staked) end
  st.collected = pay <= 0
  st.text = TCF.BJResultText(st)
end

-- "You win 100 TapCoins", "Push", "Dealer busts. You win 200 TapCoins", ...
function TCF.BJResultText(st)
  local net = (st.pay or 0) - (st.staked or 0)
  local parts = {}
  if st.natural == "both" then parts[#parts + 1] = "You both have blackjack"
  elseif st.natural == "dealer" then parts[#parts + 1] = "Dealer has blackjack"
  elseif st.natural == "player" then parts[#parts + 1] = "Blackjack"
  elseif st.dealerBust then parts[#parts + 1] = "Dealer busts"
  elseif #st.hands == 1 and st.hands[1].result == "bust" then parts[#parts + 1] = "Bust" end
  if #st.hands > 1 then
    local hs = {}
    for i, h in ipairs(st.hands) do hs[i] = "hand " .. i .. ": " .. (RESULT_TEXT[h.result] or "?"):lower() end
    parts[#parts + 1] = (table.concat(hs, ", "):gsub("^h", "H"))
  end
  if net > 0 then parts[#parts + 1] = "You win " .. TCF.Commas(net) .. " TapCoins"
  elseif net < 0 then parts[#parts + 1] = "You lose " .. TCF.Commas(-net) .. " TapCoins"
  elseif #parts == 0 then parts[1] = "Push"
  else parts[#parts + 1] = "You get your bet back" end
  return table.concat(parts, ". ")
end

local function advance(self, st, c)
  for i, h in ipairs(st.hands) do
    if not h.done then st.active = i; return end
  end
  finish(self, st, c)
end

local function hitHand(st, c, h)
  table.insert(h.cards, draw(c))
  local t = TCF.BJTotal(h.cards)
  if t > 21 then h.done, h.result = true, "bust"
  elseif t == 21 then h.done = true end
end

-- Start a hand. cards: tests can pass the first four cards (player, dealer, player, dealer).
-- Returns the state, or nil when the bet can't be taken or a hand is still being played.
function TCF:BJDeal(bet, cards)
  if self:BJInPlay() then return nil end
  self:CasinoCollect("blackjack")
  if not self:CasinoBet(bet, "blackjack") then return nil end
  local c = self:CasinoData()
  local shuffled = false
  if not validShoe(c) or c.shoe.left < SHOE_SIZE * TCF.BJ_RESHUFFLE then newShoe(c); shuffled = true end
  local function card(i)
    if cards and cards[i] then
      local code = cards[i]
      if c.shoe.counts[code] and c.shoe.counts[code] > 0 then c.shoe.counts[code] = c.shoe.counts[code] - 1; c.shoe.left = c.shoe.left - 1 end
      return code
    end
    return draw(c)
  end
  local p1, d1, p2, d2 = card(1), card(2), card(3), card(4)
  local old = self:BJState()
  local st = { id = ((old and num(old.id)) or 0) + 1, phase = "player", bet = bet, active = 1, shuffled = shuffled,
               hands = { { cards = { p1, p2 }, bet = bet } }, dealer = { d1, d2 }, holeShown = false }
  c.bj = st
  local h = st.hands[1]
  local pBJ = TCF.BJTotal(h.cards) == 21
  -- the dealer peeks under an ace or a ten
  local dBJ = (cardValue(d1) >= 10) and TCF.BJTotal(st.dealer) == 21
  if pBJ or dBJ then
    st.phase, st.holeShown, h.done = "done", true, true
    if pBJ and dBJ then h.result, h.pay, st.natural = "push", bet, "both"
    elseif pBJ then h.result, h.pay, st.natural = "bj", bet + floor(bet * 3 / 2), "player"   -- 3 to 2, half a TapCoin rounded down
    else h.result, h.pay, st.natural = "lose", 0, "dealer" end
    st.pay, st.staked = h.pay, bet
    if h.pay > 0 then self:CasinoHold(h.pay, "blackjack", pBJ and not dBJ and "casinoBlackjacks" or nil, bet) end
    st.collected = h.pay <= 0
    st.text = TCF.BJResultText(st)
  end
  return st
end

function TCF:BJHit()
  if not self:BJCanHit() then return false end
  local st, c = self:BJState(), self:CasinoData()
  hitHand(st, c, st.hands[st.active])
  if st.hands[st.active].done then advance(self, st, c) end
  return true
end

function TCF:BJStand()
  local st = self:BJState()
  if not (st and st.phase == "player") then return false end
  st.hands[st.active].done = true
  advance(self, st, self:CasinoData())
  return true
end

function TCF:BJDouble()
  if not self:BJCanDouble() then return false end
  local st, c = self:BJState(), self:CasinoData()
  local h = st.hands[st.active]
  if not self:CasinoBet(h.bet, "blackjack", true) then return false end
  h.bet, h.doubled = h.bet * 2, true
  hitHand(st, c, h)
  h.done = true
  advance(self, st, c)
  return true
end

function TCF:BJSplit()
  if not self:BJCanSplit() then return false end
  local st, c = self:BJState(), self:CasinoData()
  local h = st.hands[1]
  if not self:CasinoBet(h.bet, "blackjack", true) then return false end
  local aces = cardValue(h.cards[1]) == 11
  local h2 = { cards = { h.cards[2] }, bet = h.bet, split = true }
  h.cards, h.split = { h.cards[1] }, true
  st.hands[2] = h2
  st.split = true
  for _, x in ipairs({ h, h2 }) do
    hitHand(st, c, x)
    -- split aces get one card each
    if aces then x.done = true end
  end
  advance(self, st, c)
  return true
end

---------------------------------------------------------------- login: pay what was left owing
local ev = CreateFrame("Frame")
ev:RegisterEvent("PLAYER_LOGIN")
ev:SetScript("OnEvent", function()
  if TCF.db then TCF:CasinoCollect() end
end)
