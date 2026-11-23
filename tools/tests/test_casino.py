# Casino (Casino.lua, UI_Casino.lua): bet limits, stakes and payouts, slots pay table and exact
# return to player, blackjack rules (dealer stands on soft 17, blackjack 3 to 2, double, split,
# push, busts), a hand that survives closing the window and a reload, and the Casino tab.
# Run on its own with the long simulations:  python3 tools/tests/test_casino.py --sim
import os, sys

# Basic strategy for 6 decks, dealer stands on soft 17, double after split, no surrender.
# Returns "H", "S", "D" (double, else hit), "Ds" (double, else stand) or "P" (split).
STRATEGY = r'''
local T = TapCatForever
function _bjStrategy(cards, up, canSplit)
  local v1, v2 = T.BJCardValue(cards[1]), cards[2] and T.BJCardValue(cards[2])
  local u = T.BJCardValue(up)          -- 2-10, ace = 11
  if canSplit and #cards == 2 and v1 == v2 then
    if v1 == 11 or v1 == 8 then return "P" end
    if v1 == 9 and u ~= 7 and u ~= 10 and u ~= 11 then return "P" end
    if v1 == 7 and u <= 7 then return "P" end
    if v1 == 6 and u <= 6 then return "P" end
    if v1 == 4 and (u == 5 or u == 6) then return "P" end
    if (v1 == 2 or v1 == 3) and u <= 7 then return "P" end
  end
  local t, soft = T.BJTotal(cards)
  if soft then
    if t >= 19 then return "S" end
    if t == 18 then
      if u >= 3 and u <= 6 then return "Ds" end
      if u <= 8 then return "S" end
      return "H"
    end
    if t == 17 then return (u >= 3 and u <= 6) and "D" or "H" end
    if t == 15 or t == 16 then return (u >= 4 and u <= 6) and "D" or "H" end
    if t == 13 or t == 14 then return (u >= 5 and u <= 6) and "D" or "H" end
    return "H"
  end
  if t >= 17 then return "S" end
  if t >= 13 then return u <= 6 and "S" or "H" end
  if t == 12 then return (u >= 4 and u <= 6) and "S" or "H" end
  if t == 11 then return u <= 10 and "D" or "H" end
  if t == 10 then return u <= 9 and "D" or "H" end
  if t == 9 then return (u >= 3 and u <= 6) and "D" or "H" end
  return "H"
end
-- play n hands of bet each with basic strategy; returns won / wagered and the hands played
function _bjSim(n, bet)
  local c = T:CasinoData()
  local w0, p0 = c.blackjack.wagered, c.blackjack.won
  local doubles, splits, naturals = 0, 0, 0
  for i = 1, n do
    T.db.coins = 1e9
    local st = assert(T:BJDeal(bet))
    if st.natural == "player" then naturals = naturals + 1 end
    local guard = 0
    while st.phase == "player" do
      guard = guard + 1; assert(guard < 50, "hand never ends")
      local h = st.hands[st.active]
      local a = _bjStrategy(h.cards, st.dealer[1], T:BJCanSplit())
      if a == "P" then assert(T:BJSplit()); splits = splits + 1
      elseif (a == "D" or a == "Ds") and T:BJCanDouble() then assert(T:BJDouble()); doubles = doubles + 1
      elseif a == "S" or a == "Ds" then T:BJStand()
      else T:BJHit() end
    end
    T:CasinoCollect("blackjack")
  end
  return (c.blackjack.won - p0) / (c.blackjack.wagered - w0), c.blackjack.wagered - w0, doubles, splits, naturals
end
function _slotSim(n, bet)
  local c = T:CasinoData()
  local w0, p0 = c.slots.wagered, c.slots.won
  local hits = 0
  for i = 1, n do
    T.db.coins = 1e9
    local r = assert(T:SlotsSpin(bet))
    if r.win > 0 then hits = hits + 1 end
    T:CasinoCollect("slots")
  end
  return (c.slots.won - p0) / (c.slots.wagered - w0), hits / n
end
'''


def exact_rtp(lua):
    """The slots' return to player, worked out in Python from the reel strips and pay table."""
    reels = [list(lua.eval("TapCatForever.SLOT_REELS[%d]" % i).values()) for i in (1, 2, 3)]
    pay3 = dict(lua.eval("TapCatForever.SLOT_PAY3").items())
    two, one = lua.eval("TapCatForever.SLOT_PAY_TWO_CATS"), lua.eval("TapCatForever.SLOT_PAY_ONE_CAT")
    total = ret = hits = 0
    var = 0
    for a in reels[0]:
        for b in reels[1]:
            for c in reels[2]:
                if a == b == c:
                    m = pay3[a]
                else:
                    k = (a, b, c).count("cat")
                    m = two if k == 2 else one if k == 1 else 0
                total += 1; ret += m; var += m * m; hits += m > 0
    mean = ret / total
    return mean, hits / total, (var / total - mean * mean) ** 0.5, reels


def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    lua.execute(STRATEGY)
    fails = []

    def ck(cond, what):
        if not cond:
            fails.append(what)

    ev = lua.eval
    ex = lua.execute

    # ---- limits
    ex("T = TapCatForever; C = T:CasinoData()")
    # 1.6.0: at least 10, at most half your TapCoins rounded down to the bet step, no fixed top
    ex("T.db.coins = 19")
    lo, hi = ex("return T:CasinoLimits()")
    ck(lo == 10 and hi < 10, "19 coins: can't play (%s, %s)" % (lo, hi))
    ck(not ev("T:CasinoBet(10, 'slots')") and ev("T.db.coins") == 19, "19 coins: no bet taken")
    for coins, top in ((20, 10), (39, 10), (40, 20), (999, 450), (1000, 500), (1234, 600), (3333, 1600), (5000, 2500),
                       (12345, 6000), (100000, 50000), (2500000, 1200000), (7777777, 3750000)):
        ex("T.db.coins = %d" % coins)
        ck(ex("return T:CasinoLimits()") == (10, top), "%d coins: 10 to %d (%r)" % (coins, top, ex("return T:CasinoLimits()")))
        ck(top <= coins // 2 and top % ev("T.CasinoBetStep(%d)" % top) == 0, "%d: half or less, on the step" % coins)
    ex("T.db.coins = 100000")
    ck(ev("T:CasinoClampBet(99999)") == 50000 and ev("T:CasinoClampBet(1)") == 10, "bets clamp to the limits")
    ck(ev("T:CasinoBet(50000, 'slots')") and ev("T.db.coins") == 50000, "half of 100000 can be bet")
    ck(ev("T.CASINO_MAX_BET") is None, "no fixed top bet")
    steps = [(10, 10), (99, 10), (100, 25), (249, 25), (250, 50), (999, 50), (1000, 100), (2499, 100), (2500, 250), (5000, 500), (10000, 1000), (250000, 25000)]
    for b, s in steps:
        ck(ev("T.CasinoBetStep(%d)" % b) == s, "step at %d is %d (%r)" % (b, s, ev("T.CasinoBetStep(%d)" % b)))
    ex("C.slots = nil; C.total = nil; C = T:CasinoData()")

    # ---- bet and pay bookkeeping (stakes and winnings stay out of TapCoins earned and spent)
    ex("T.db.coins = 1000; _e, _s = T.db.coinsEarned, T.db.coinsSpent")
    ck(not ev("T:CasinoBet(501, 'slots')"), "over the limit (half of 1000): refused")
    ck(not ev("T:CasinoBet(9, 'slots')"), "under the limit: refused")
    ck(not ev("T:CasinoBet(10.5, 'slots')"), "not a whole number: refused")
    ck(not ev("T:CasinoBet(10, 'roulette')"), "unknown game: refused")
    for key in ("bj", "shoe", "bet", "total", "pending", "view"):
        ck(not ev("T:CasinoBet(10, '%s')" % key), "a saved key is not a game: %s" % key)
    ck(ev("T.db.coins") == 1000, "no coins taken by odd game names")
    ck(not ev("T:CasinoBet(_SECRET, 'slots')"), "secret amount: refused")
    ck(ev("T:CasinoBet(100, 'slots')") and ev("T.db.coins") == 900, "bet 100 takes 100")
    ck(ev("C.slots.played") == 1 and ev("C.slots.wagered") == 100 and ev("C.total.wagered") == 100, "bet counted in the stats")
    ck(ev("T:CasinoPay(250, 'slots')") == 250 and ev("T.db.coins") == 1150, "pay 250")
    ck(ev("C.slots.won") == 250 and ev("C.slots.biggest") == 250 and ev("C.total.won") == 250, "win counted in the stats")
    ck(ev("T.db.coinsEarned == _e and T.db.coinsSpent == _s"), "casino money is not TapCoins earned or spent")
    # "Biggest win" is the profit: a push or a small line doesn't count as a big win
    ex("C.blackjack.biggest = 0; C.total.biggest = 0; T:CasinoPay(500, 'blackjack', 500)")
    ck(ev("C.blackjack.biggest") == 0 and ev("C.total.biggest") == 0, "a push is not a win (biggest %s)" % ev("C.blackjack.biggest"))
    ex("T:CasinoHold(20, 'slots', nil, 10); T:CasinoCollect('slots')")
    ck(ev("C.slots.biggest") == 250, "a one-cat line on 10 doesn't beat 250")
    ex("C.slots.biggest = 0; T:CasinoHold(20, 'slots', nil, 10); T:CasinoCollect('slots')")
    ck(ev("C.slots.biggest") == 10, "a one-cat line on 10 is a 10 TapCoin win (%s)" % ev("C.slots.biggest"))
    ex("T.db.coins = T.db.coins - 540")
    ck(ev("T:CasinoPay(-5, 'slots')") == 0 and ev("T.db.coins") == 1150, "no negative pay")
    ck(ev("T:CasinoStatsLine('slots')").find("Played 1") >= 0 and "Paid back" in ev("T:CasinoStatsLine('slots')"), "stats line")
    # held winnings are paid when collected (and at login)
    ex("T:CasinoHold(40, 'slots')")
    ck(ev("T.db.coins") == 1150, "held winnings wait")
    ck(ev("T:CasinoCollect('slots')") == 40 and ev("T.db.coins") == 1190, "collect pays them")
    ex("T:CasinoHold(30, 'slots'); _fire('PLAYER_LOGIN')")
    ck(ev("T.db.coins") == 1220 and ev("next(C.pending)") is None, "login pays what was owed")
    # duel settlement
    ex("T.db.coins = 100")
    ck(ev("T:CasinoSettleDuel(-60, 'Bob-Forever')") == -60 and ev("T.db.coins") == 40, "duel loss debits")
    ck(ev("T:CasinoSettleDuel(-60, 'Bob-Forever')") == -40 and ev("T.db.coins") == 0, "never below zero")
    ck(ev("T:CasinoSettleDuel(120, _SECRET)") == 120 and ev("T.db.coins") == 120, "duel win credits")
    ck(ev("T:CasinoSettleDuel(99999, 'Bob', 300)") == 300 and ev("T.db.coins") == 420, "at most the bet both sides agreed")
    ck(ev("T:CasinoSettleDuel(-99999, 'Bob', 300)") == -300 and ev("T.db.coins") == 120, "a loss at most the bet too")
    ex("T.db.coins = 120")
    ck(ev("T:CasinoSettleDuel(_SECRET, 'Bob')") == 0, "secret delta ignored")
    ck(ev("#C.duels") == 5 and ev("C.duels[3].opp") == "another player", "duels logged")
    ex("T.db.coins = 10000000")
    ck(ev("T:CasinoSettleDuel(2000000, 'Bob', 2000000)") == 2000000 and ev("T.db.coins") == 12000000, "big agreed bets settle in full (no 500 cap)")
    ck(ev("T:CasinoSettleDuel(-2000000, 'Bob', 2000000)") == -2000000 and ev("T.db.coins") == 10000000, "and lose in full")
    # duel stats with the stake (duels are even): a win of 100 on a bet of 100 counts as bet 100, paid back 200
    ex("C.deathroll = nil; C.total = nil; C = T:CasinoData(); T.db.coins = 1000")
    ex("T:CasinoSettleDuel(100, 'Bob', 100)")
    ck(ev("C.deathroll.wagered") == 100 and ev("C.deathroll.won") == 200 and ev("C.deathroll.biggest") == 100, "duel win stats")
    ex("T:CasinoSettleDuel(-100, 'Bob', 100)")
    ck(ev("C.deathroll.wagered") == 200 and ev("C.deathroll.won") == 200, "duel loss stats")
    ck("Net |cff40ff40+0" in ev("T:CasinoStatsLine('deathroll')"), "duel net 0: " + ev("T:CasinoStatsLine('deathroll')"))

    # ---- slots: every line pays what the table says
    pays = {"cat": 100, "gem": 40, "bell": 25, "coin": 15, "fish": 10, "yarn": 5, "paw": 3}
    for s, m in pays.items():
        ck(ex("return T.SlotsPay('%s', '%s', '%s')" % (s, s, s)) == (m, "three"), "three %s pays %d" % (s, m))
    ck(ex("return T.SlotsPay('cat', 'cat', 'paw')") == (5, "twocats"), "two cats pay 5")
    ck(ex("return T.SlotsPay('gem', 'cat', 'cat')") == (5, "twocats"), "two cats anywhere")
    ck(ex("return T.SlotsPay('paw', 'cat', 'gem')") == (2, "onecat"), "one cat pays 2")
    ck(ex("return T.SlotsPay('paw', 'gem', 'gem')")[0] == 0, "no line pays nothing")
    ck(ex("return T.SlotsPay('gem', 'gem', 'bell')")[0] == 0, "two gems pay nothing")
    # a spin with chosen stops: three cats on the middle row (reel 1 stop 1, reel 2 stop 5, reel 3 stop 4)
    ex("T.db.coins = 1000; _a0 = T.db.achievements.casino_cats")
    r = ev("T:SlotsSpin(20, { 1, 5, 4 })")
    ck(r is not None and r.win == 2000 and r.kind == "three", "three cats on 20 wins 2000")
    ck(ev("T.db.coins") == 980, "the win waits for the reels")
    ck(ev("T:CasinoCollect('slots')") == 2000 and ev("T.db.coins") == 2980, "reels landed: paid")
    ck(ev("T.db.stats.casinoCats") == 1, "three cats counted for the achievement")
    ex("_c0 = T.db.coins; T:CheckAchievements()")
    ck(ev("T.db.achievements.casino_cats ~= nil") and ev("T.db.coins") >= ev("_c0") + 100, "Three Cats in a Row earned (100 TapCoins): %s" % (ev("T.db.coins - _c0"),))
    ex("T.db.coins = _c0")
    ck(ev("T:SlotsSpin(5000)") is None, "a spin over the limit is refused")
    # exact return to player, worked out twice (Python here, Lua in the addon)
    mean, hit, sd, reels = exact_rtp(lua)
    lmean, lhit = ex("return T:SlotsExactRTP()")
    ck(abs(mean - lmean) < 1e-12 and abs(hit - lhit) < 1e-12, "RTP agrees: %s %s" % (mean, lmean))
    ck(0.92 <= mean <= 0.95, "slots RTP in 92-95%%: %.4f" % mean)
    ck(all(len(r) == 20 for r in reels), "20 stops per reel")
    # the rarer a line, the more it pays
    odds = {s: reels[0].count(s) * reels[1].count(s) * reels[2].count(s) for s in pays}
    order = sorted(pays, key=lambda s: -pays[s])
    ck(all(odds[order[i]] < odds[order[i + 1]] for i in range(len(order) - 1)), "rarer lines pay more: %r" % odds)
    sim, simhit = ex("return _slotSim(20000, 10)")
    ck(0.80 < sim < 1.10 and abs(simhit - hit) < 0.02, "slots simulation near the exact RTP: %.4f" % sim)

    # ---- blackjack rules. Cards: code = (suit - 1) * 13 + rank (1 ace, 11-13 J Q K)
    def deal(cards, bet=100, coins=10000):
        ex("T:CasinoCollect(); T.db.coins = %d; C.bj = nil; C.shoe = nil" % coins)   # a fresh shoe: stacked cards are there
        return ev("T:BJDeal(%d, { %s })" % (bet, ", ".join(map(str, cards))))

    def dealer_draws(*codes):
        # stack the next cards the shoe gives (Casino.lua's draw takes them first)
        ex("T.bjTestStack = { %s }" % ", ".join(map(str, codes)))

    def undraw():
        ex("T.bjTestStack = nil")

    # blackjack pays 3 to 2
    st = deal([1, 9, 13, 7])  # A, 9 / K, 7
    ck(st.phase == "done" and st.natural == "player" and st.pay == 250, "blackjack pays 3 to 2 (250 back on 100)")
    ck(ev("T:CasinoCollect('blackjack')") == 250 and ev("T.db.coins") == 10150, "blackjack paid when collected")
    ck(ev("T.db.stats.casinoBlackjacks") == 1, "blackjack counted for the achievement")
    ck("Blackjack" in st.text and "You win 150 TapCoins" in st.text, "blackjack text: " + st.text)
    # the dealer's blackjack ends the hand at once (no insurance)
    st = deal([10, 1, 7, 13])  # 10, A / 7, K
    ck(st.phase == "done" and st.natural == "dealer" and st.pay == 0 and "You lose 100" in st.text, "dealer blackjack: " + str(st.text))
    st = deal([1, 1 + 13, 12, 11])  # A, A / Q, J: both blackjack
    ck(st.pay == 100 and st.natural == "both", "both blackjack: push")
    # dealer stands on soft 17: player 10 + 8 = 18 against A + 6
    st = deal([10, 1, 8, 6])
    ck(st.phase == "player", "no blackjack: the hand goes on")
    ck(ev("T:BJStand()") and st.phase == "done" and len(list(st.dealer.values())) == 2, "dealer stands on soft 17")
    ck(st.hands[1].result == "win" and st.pay == 200 and st.text == "You win 100 TapCoins", "18 beats 17: " + st.text)
    # push
    st = deal([10, 10 + 13, 8, 8 + 13])
    ex("T:BJStand()")
    ck(st.hands[1].result == "push" and st.pay == 100 and st.text == "Push", "18 against 18 is a push: " + st.text)
    # player busts
    st = deal([10, 10 + 13, 6, 8 + 13])
    dealer_draws(9)
    ex("T:BJHit()"); undraw()
    ck(st.phase == "done" and st.hands[1].result == "bust" and st.pay == 0 and len(list(st.dealer.values())) == 2,
       "player busts, dealer doesn't draw: " + str(st.text))
    ck(st.text == "Bust. You lose 100 TapCoins", "bust text: " + st.text)
    # dealer busts: 10 + 6 draws a king
    st = deal([10, 10 + 13, 8, 6 + 13])
    dealer_draws(13)
    ex("T:BJStand()"); undraw()
    ck(st.dealerBust and st.pay == 200 and st.text == "Dealer busts. You win 100 TapCoins", "dealer busts: " + str(st.text))
    # dealer hits hard 16 and soft 16
    st = deal([10, 1, 9, 5])  # dealer A + 5 = soft 16
    dealer_draws(2)
    ex("T:BJStand()"); undraw()
    ck(len(list(st.dealer.values())) == 3 and ev("(T.BJTotal(T:BJState().dealer))") == 18, "dealer hits soft 16")
    # double: one card, twice the bet
    st = deal([5, 10, 6, 7])  # 11 against 10 + 7
    dealer_draws(9)
    ck(ev("T:BJCanDouble()") and ev("T:BJDouble()"), "double on 11")
    undraw()
    h = st.hands[1]
    ck(h.bet == 200 and h.doubled and len(list(h.cards.values())) == 3 and st.phase == "done", "double: one card, bet 200")
    ck(st.pay == 400 and ev("T.db.coins") == 10000 - 200, "double win pays 400 (collected later)")
    ex("T:CasinoCollect()")
    ck(ev("T.db.coins") == 10200, "double win: +200")
    # double on any two cards (soft 13 too), not with three
    st = deal([1, 10, 2, 7])
    ck(ev("T:BJCanDouble()"), "double on any two cards")
    dealer_draws(3); ex("T:BJHit()"); undraw()
    ck(not ev("T:BJCanDouble()"), "no double on three cards")
    # can't double without the TapCoins
    st = deal([5, 10, 6, 7], bet=100, coins=150)
    ck(not ev("T:BJCanDouble()") and not ev("T:BJDouble()"), "no double without the coins")
    ex("T:BJStand(); T:CasinoCollect()")
    # split once: 8, 8 against 6
    st = deal([8, 6, 8 + 13, 10])
    ck(ev("T:BJCanSplit()"), "pair of eights can split")
    dealer_draws(3, 10, 9)   # hand 1 gets a 3, hand 2 a 10, dealer draws a 9 (16 + 9 busts)
    ck(ev("T:BJSplit()"), "split")
    ck(len(list(st.hands.values())) == 2 and st.hands[1].bet == 100 and st.hands[2].bet == 100, "two hands of 100")
    ck(not ev("T:BJCanSplit()"), "no re-split")
    ck(ev("T:BJCanDouble()"), "double after split")
    ex("T:BJStand()")   # hand 1: 8 + 3 = 11, stand
    ck(st.active == 2 and st.phase == "player", "on to hand 2")
    ex("T:BJStand()"); undraw()
    ck(st.phase == "done" and st.dealerBust and st.pay == 400, "both split hands win when the dealer busts")
    ck("Hand 1: win, hand 2: win" in st.text and "You win 200" in st.text, "split text: " + st.text)
    # split aces: one card each, 21 after a split is not a blackjack
    st = deal([1, 9, 1 + 26, 7])
    dealer_draws(13, 5, 10)   # hand 1 gets a K (21), hand 2 a 5; the dealer's 16 draws a 10 and busts
    ex("T:BJSplit()"); undraw()
    ck(st.phase == "done" and st.hands[1].result == "win" and st.hands[1].pay == 200, "split aces: one card each, 21 pays 1 to 1")
    ck(len(list(st.hands[1].cards.values())) == 2 and len(list(st.hands[2].cards.values())) == 2, "split aces: exactly one card each")
    # no split of two different cards
    st = deal([9, 6, 8, 10])
    ck(not ev("T:BJCanSplit()") and not ev("T:BJSplit()"), "9 and 8 don't split")
    # ten-value cards split as a pair (K, Q)
    ex("T:BJStand(); T:CasinoCollect()")
    st = deal([13, 6, 12, 10])
    ck(ev("T:BJCanSplit()"), "king and queen split")
    ex("T:BJStand(); T:CasinoCollect()")
    # no new hand while one is being played; a hand needs a bet within the limits
    st = deal([9, 6, 8, 10])
    ck(ev("T:BJDeal(100)") is None, "no new deal mid-hand")
    ex("T:BJStand(); T:CasinoCollect()")
    ck(ev("T:BJDeal(9)") is None and ev("T:BJDeal(100000)") is None, "deal needs a bet within the limits")
    # the shoe: 6 decks, a new shoe once a quarter is left
    ex("C.shoe = nil; C.bj = nil; T.db.coins = 1e6")
    ex("T:BJDeal(10); T:BJStand(); T:CasinoCollect()")
    ck(ev("C.shoe.left") <= 312 - 4 and ev("T:BJState().shuffled"), "a fresh shoe of 312 cards")
    ex("for i = 1, 52 do C.shoe.counts[i] = (i <= 12) and 6 or 0 end; C.shoe.left = 72")
    ex("T:BJDeal(10); T:BJStand(); T:CasinoCollect()")
    ck(ev("T:BJState().shuffled") and ev("C.shoe.left") > 250, "reshuffled under 25%")
    ck(ev("C.shoe.order") is None, "the saved shoe holds only counts, not the order")

    # ---- state survives closing the window and a reload
    ex("T.db.coins = 5000; T:CasinoCollect(); C.bj = nil")
    st = deal([9, 6, 8, 10], bet=100, coins=5000)
    ex("T:CreateWindow(); T.window:Show(); T.window:SelectTab(T.window.TAB_CASINO)")
    ex("T.window:Hide(); T.window:Show()")
    ck(ev("T:BJInPlay()") and ev("T:BJState().id") == st.id, "closing the window keeps the hand")
    # a reload: the saved table goes to a fresh copy of the addon
    import copy
    lua2 = load_addon(login=False)
    saved = lua.eval("TapCatForeverDB")
    # copy the saved variables table across Lua states through a serializer
    ser = lua.execute(r'''
      local function ser(v, seen)
        local t = type(v)
        if t == "number" then return string.format("%.17g", v) elseif t == "boolean" then return tostring(v)
        elseif t == "string" then return string.format("%q", v) elseif t ~= "table" then return "nil" end
        local out = {}
        for k, x in pairs(v) do out[#out + 1] = "[" .. ser(k) .. "]=" .. ser(x) end
        return "{" .. table.concat(out, ",") .. "}"
      end
      local mt = getmetatable(TapCatForeverDB); setmetatable(TapCatForeverDB, nil)
      local s = ser(TapCatForeverDB)
      setmetatable(TapCatForeverDB, mt)
      return s''')
    lua2.execute("TapCatForeverDB = " + ser)
    lua2.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    lua2.execute(STRATEGY)
    ck(lua2.eval("TapCatForever:BJInPlay()") and lua2.eval("TapCatForever:BJState().id") == st.id, "the hand is still there after a reload")
    ck(lua2.eval("TapCatForever.db.coins") == 4900, "the stake stays taken")
    lua2.execute("TapCatForever:BJStand()")
    ck(lua2.eval("TapCatForever:BJState().phase") == "done", "and can be finished")
    # a finished hand whose win was never collected is paid at login
    lua2.execute("TapCatForever:CasinoCollect(); TapCatForever.db.coins = 1000; TapCatForever:CasinoHold(200, 'blackjack'); _fire('PLAYER_LOGIN')")
    ck(lua2.eval("TapCatForever.db.coins") == 1200, "unpaid win paid at the next login")

    # ---- the Casino tab: the 12 tabs still work, Settings is last, Casino right before it
    names = [ev("T.window.tabNames[%d]" % i) for i in range(1, ev("#T.window.tabNames") + 1)]
    ck(len(names) == 12 and names[-1] == "Settings" and names[-2] == "Casino" and names[9] == "Leaderboard", "tabs: %r" % names)
    ck(ev("T.window.TAB_CASINO") == 11 and ev("T.window.TAB_SETTINGS") == 12 and ev("T.window.TAB_LEADERBOARD") == 10, "tab numbers")
    for i in range(1, 13):
        ex("T.window:SelectTab(%d); for k = 1, 5 do _update(0.1) end" % i)
        ck(ev("T.window.tab") == i, "tab %d opens" % i)
    ex("T:OpenTab('gear')"); ck(ev("T.window.tab") == 1, "loot toast opens Gear")
    ex("T:OpenTab('appearance')"); ck(ev("T.window.tab") == 6, "loot toast opens Appearance")
    # the casino page: sub-views, bet chooser, spin, deal and buttons
    ex("T.window:SelectTab(T.window.TAB_CASINO)")
    cv = ev("T.casinoView")
    ck(cv is not None, "the casino page is built")
    if cv is not None:
        ex("T.db.coins = 2000; T:CasinoCollect(); C.bj = nil")
        for view in ("slots", "blackjack", "deathroll", "slots"):
            ex("T.casinoView:SetView('%s')" % view)
            ck(ev("T.casinoView.view") == view, "sub-view " + view)
        ex("T.casinoView:SetBet(9999)"); ck(ev("C.bet") == 1000, "bet chooser clamps to the max (half of 2000)")
        ex("T.casinoView:SetBet(3)"); ck(ev("C.bet") == 10, "bet chooser clamps to the min")
        ex("T.casinoView:StepBet(1)"); ck(ev("C.bet") > 10, "plus button")
        ex("T.casinoView:SetBet(50)")
        ex("_lastId = C.slotsLast and C.slotsLast.id or 0; T.casinoView.slots:Spin()")
        ck(ev("C.slotsLast.id") == ev("_lastId") + 1 and ev("T.db.coins") == 1950, "Spin takes the bet")
        ex("for k = 1, 80 do _update(0.05) end")
        ck(ev("next(C.pending)") is None, "the reels landed and the win (if any) is paid")
        ck(ev("T.db.coins") == 1950 + ev("C.slotsLast.win"), "coins after the spin")
        # the reels: at most about half a row a frame at 60 fps, never running backwards more than
        # the small landing bounce, stopping left to right
        motion = ex(r'''
          local S = T.casinoView.slots
          T.db.coins = 2000; T:CasinoCollect()
          local worstStep, worstBack, frames = 0, 0, 0
          for spin = 1, 12 do
            S:Spin()
            local prev, low = {}, {}
            for r = 1, 3 do prev[r] = S.pos[r]; low[r] = S.pos[r] end
            assert(S.stopAt[1] < S.stopAt[2] and S.stopAt[2] < S.stopAt[3], "reels stop left to right")
            for k = 1, 400 do
              _update(1 / 60); frames = frames + 1
              if not S.spinning then break end
              for r = 1, 3 do
                worstStep = math.max(worstStep, prev[r] - S.pos[r])
                low[r] = math.min(low[r], S.pos[r])
                worstBack = math.max(worstBack, S.pos[r] - low[r])
                prev[r] = S.pos[r]
              end
            end
            assert(not S.spinning, "the reels stop")
            for r = 1, 3 do assert(S.pos[r] == C.slotsLast.stops[r], "reel lands on the result") end
          end
          T.db.coins = 2000; T:CasinoCollect()
          return worstStep, worstBack, frames / 12
        ''')
        ck(motion[0] <= 0.5 and motion[1] <= 0.25, "reel motion: step %.3f rows a frame, back %.3f rows" % motion[:2])
        ck(motion[2] / 60 <= 3.8, "a spin lasts %.2f s" % (motion[2] / 60))
        # Stop lands every reel at once, with one click
        ex("_clicks = 0; local ps = T.PlaySound; T.PlaySound = function(self, k) if k == 'click' then _clicks = _clicks + 1 end end; "
           "T.casinoView.slots:Spin(); _clicks = 0; _update(0.1); T.casinoView.slots:Spin(); _update(0.02); T.PlaySound = ps")
        ck(not ev("T.casinoView.slots.spinning") and ev("_clicks") == 1, "Stop: one click (%s)" % ev("_clicks"))
        ex("T.db.coins = 1950 + 0; T:CasinoCollect(); T.db.coins = 1950")
        # a spin, then the window closes before the reels stop: paid anyway
        ex("T.casinoView.slots:Spin(); _w = C.slotsLast.win; _c = T.db.coins; T.window:Hide(); T.casinoView:GetScript('OnHide')(T.casinoView)")
        ck(ev("T.db.coins") == ev("_c + _w"), "closing mid-spin pays the win")
        ex("T.window:Show(); T.window:SelectTab(T.window.TAB_CASINO); T.casinoView:SetView('blackjack')")
        ex("T.casinoView.bj:Deal()")
        ck(ev("T:BJState() ~= nil"), "Deal deals")
        ex("for k = 1, 40 do _update(0.05) end")
        guard = 0
        while ev("T:BJInPlay()") and guard < 20:
            ex("T.casinoView.bj:Action('stand'); for k = 1, 60 do _update(0.05) end"); guard += 1
        ck(not ev("T:BJInPlay()") and ev("next(C.pending)") is None, "hand played out and paid through the buttons")
        ck(ev("T.casinoView.bj.result:GetText()") == ev("T:BJState().text"), "result text shown")
        # a blackjack: the banner takes the result line's place, and the line comes back after it
        ex("T.db.coins = 2000; T.bjTestStack = { 1, 9, 13, 7 }; T.casinoView.bj:Deal(); T.bjTestStack = nil")
        ex("for k = 1, 45 do _update(0.05) end")
        ck(ev("T:BJState().natural") == "player", "stacked blackjack")
        ck(not ev("T.casinoView.bj.result:IsShown()"), "the banner replaces the result line")
        ex("for k = 1, 40 do _update(0.1) end")
        ck(ev("T.casinoView.bj.result:IsShown()") and "Blackjack" in ev("T.casinoView.bj.result:GetText()"), "the result line comes back")
        # a fresh shoe is announced
        ex("for i = 1, 52 do C.shoe.counts[i] = (i <= 12) and 6 or 0 end; C.shoe.left = 72; T.bjTestStack = { 9, 6, 8, 10 }")
        ex("T.casinoView.bj:Deal(); T.bjTestStack = nil")
        ck(ev("T.casinoView.bj.result:GetText()") == "A fresh shoe.", "a fresh shoe: %r" % ev("T.casinoView.bj.result:GetText()"))
        ex("for k = 1, 30 do _update(0.05) end; T.casinoView.bj:Action('stand'); for k = 1, 60 do _update(0.05) end")
        # too few TapCoins: the page says so
        ex("T.db.coins = 19; T.casinoView:Refresh()")
        ck("20 TapCoins" in (ev("T.casinoView.limits:GetText()") or "") and "half" in ev("T.casinoView.limits:GetText()"), "fewer than 20 coins: told why")
        ex("T.casinoView.slots:Spin()"); ck(ev("T.db.coins") == 19, "no spin without the coins")
        ex("T.db.coins = 5000; T.casinoView:Refresh()")
        lim = ev("T.casinoView.limits:GetText()") or ""
        ck(("10 to 2,500" in lim or "10 to 2500" in lim) and "half" in lim and "500)" not in lim and "quarter" not in lim, "the limits line: %r" % lim)
        # the death roll view is a plain container of about 870 x 452
        ck(ev("T.casinoView.deathroll ~= nil"), "death roll container")
    # every casino texture exists
    ex("_casArt = {}; for p in pairs(_textures) do local f = p:match('Art\\\\(casino\\\\.+)$'); if f then _casArt[#_casArt + 1] = f end end")
    art = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Art")
    used = list(ev("_casArt").values())
    gone = [f for f in used if not os.path.exists(os.path.join(art, f.replace("\\", "/") + ".tga"))]
    ck(len(used) >= 10 and not gone, "casino art: %d used, missing %r" % (len(used), gone))
    # plain English: no exclamation marks in the casino's chat lines and texts
    for i in range(1, ev("#_chat") + 1):
        line = ev("_chat[%d]" % i)
        ck("!" not in line, "chat line: " + line)
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "UI_Casino.lua")).read()
    import re
    for s in re.findall(r'"([^"\n]*)"', src):
        ck("!" not in s or s.startswith("|") or "~=" in s, "exclamation mark in UI_Casino.lua: " + s)

    if fails:
        raise AssertionError("casino: " + "; ".join(fails))
    print("casino section (limits, bets and pays, slots pay table and exact RTP %.2f%%, blackjack rules: soft 17, 3 to 2, "
          "double, split, push, busts, the shoe, a hand that survives a reload, 12 tabs, the Casino page): all checks passed" % (mean * 100))


def simulate():
    """The long simulations for the report: 1,000,000 spins and 200,000 hands of basic strategy."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    import test_harness, time
    lua = test_harness.load_addon()
    seed = int(time.time())
    lua.execute("math.randomseed(%d)" % seed)
    lua.execute(STRATEGY)
    mean, hit, sd, _ = exact_rtp(lua)
    print("slots exact RTP %.4f%%, hit rate %.2f%%, std dev %.2f bets" % (mean * 100, hit * 100, sd))
    n = int(os.environ.get("SLOTS_N", "1000000"))
    t = time.time()
    rtp, h = lua.execute("return _slotSim(%d, 10)" % n)
    print("slots simulated %d spins: RTP %.4f%% (+/- %.2f%%), hit rate %.2f%% (%.0f s)" % (n, rtp * 100, 196 * sd / n ** 0.5, h * 100, time.time() - t))
    n = int(os.environ.get("BJ_N", "200000"))
    t = time.time()
    ret, wag, dbl, spl, nat = lua.execute("return _bjSim(%d, 100)" % n)
    won = ret * wag
    print("blackjack %d hands: won/wagered %.4f, house edge per starting bet %.3f%%, doubles %d, splits %d, blackjacks %d (%.0f s)"
          % (n, ret, (wag - won) / (n * 100) * 100, dbl, spl, nat, time.time() - t))


if __name__ == "__main__":
    if "--sim" in sys.argv:
        simulate()
