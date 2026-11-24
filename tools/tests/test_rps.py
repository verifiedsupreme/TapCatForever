# Rock paper scissors (RPS.lua, UI_RPS.lua): the hash, the game against the house cat (odds and the
# house edge measured over many games, ties replay for free, bookkeeping, limits, a game that survives
# a reload) and the game with party members (2-3 simulated clients passing addon messages, the same way
# test_deathroll.py does): challenge, accept, commit, reveal, a tie replays, win and lose settle once on
# each side with matching amounts, a commit that hides the pick, a bad reveal and a missing reveal call
# it off with no TapCoins moved, a lost "I lose" only ever takes TapCoins out, pick timeouts, withdraw,
# decline, busy with a death roll, /reload, spoofed and odd messages, and the scene.
# Run on its own:  python3 tools/tests/test_rps.py [seed]
import os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
import test_deathroll as TD

T = "TapCatForever"

def ck(c, m):
    if not c: raise AssertionError("rock paper scissors: " + m)

def fnv1a(s):
    h = 2166136261
    for ch in s.encode():
        h ^= ch
        h = (h * 16777619) % 2 ** 32
    return "%08x" % h

def check(seed, load_addon):
    rnd = random.Random(seed)
    if not os.environ.get("ONLY_BEST"): _hash(load_addon, rnd)
    if not os.environ.get("ONLY_BEST"): _house(seed, load_addon, rnd)
    if not os.environ.get("ONLY_BEST"): _duels(seed, load_addon, rnd)
    _best(seed, load_addon, rnd)
    _scene(seed, load_addon)

# ---------------------------------------------------------------------------- the hash
def _hash(load_addon, rnd):
    lua = load_addon()
    ck(lua.eval('%s.RPS.Hash("a")' % T) == "e40c292c", "FNV-1a of 'a'")
    ck(lua.eval('%s.RPS.Hash("")' % T) == "811c9dc5", "FNV-1a of ''")
    for _ in range(200):
        s = "".join(rnd.choice("abcdefXYZ0123456789:;-") for _ in range(rnd.randint(1, 40)))
        ck(lua.eval("%s.RPS.Hash(%r)" % (T, s)) == fnv1a(s), "FNV-1a matches for %r" % s)
    print("rock paper scissors hash section (32-bit FNV-1a in plain Lua 5.1, 202 strings): all checks passed")

# ---------------------------------------------------------------------------- the house cat
def _house(seed, load_addon, rnd):
    lua = TD._client(load_addon, "Solocat", seed)
    ev = lua.eval
    lua.execute("%s.db.coins = 19" % T)
    ok, err = lua.execute('return %s:RPSSoloPlay("rock", 10)' % T)
    ck(not ok and "20" in err, "fewer than 20 TapCoins: no game (%r)" % err)
    lua.execute("%s.db.coins = 1000" % T)
    for bad in (5, 9, 501, 10.5):
        ok, err = lua.execute('return %s:RPSSoloPlay("rock", %s)' % (T, bad))
        ck(not ok and ev("%s.db.coins" % T) == 1000, "bet %s refused (limits 10 to 500)" % bad)
    ck(not lua.eval('(%s:RPSSoloPlay("lizard", 100))' % T) and ev("%s.db.coins" % T) == 1000, "an unknown sign is refused")
    lua.execute('''
      function _playRps(n, bet)
        local T = TapCatForever
        local signs = { "rock", "paper", "scissors" }
        local wins, ties, rounds, paid, house = 0, 0, 0, 0, { rock = 0, paper = 0, scissors = 0 }
        local freeTies = true
        for i = 1, n do
          T.db.coins = 100000
          local before = T.db.coins
          assert(T:RPSSoloPlay(signs[math.random(3)], bet))
          while true do
            local g, running = T:RPSSolo()
            rounds = rounds + 1
            house[g.opp] = house[g.opp] + 1
            if not running then
              if g.result == "win" then wins = wins + 1; paid = paid + g.paid end
              break
            end
            ties = ties + 1
            if T.db.coins ~= before - bet then freeTies = false end
            assert(T:RPSSoloPlay(signs[math.random(3)]))   -- after a tie: no new bet
          end
        end
        return wins, ties, rounds, paid, house.rock, house.paper, house.scissors, freeTies
      end''')
    c0 = ev("(function() local c = TapCatForever:CasinoData().rps; return c.played .. ',' .. c.wagered .. ',' .. c.won end)()")
    N, BET = 30000, 100
    wins, ties, rounds, paid, hr, hp, hs, free = lua.eval("{_playRps(%d, %d)}" % (N, BET)).values()
    p, sd = wins / N, (0.25 / N) ** 0.5
    ck(abs(p - 0.5) < 4 * sd, "you win half the games (%.4f)" % p)
    ck(abs(ties / rounds - 1 / 3) < 0.02, "a third of the rounds tie (%.4f)" % (ties / rounds))
    for k, n in (("rock", hr), ("paper", hp), ("scissors", hs)):
        ck(abs(n / rounds - 1 / 3) < 0.02, "the house cat picks %s a third of the time (%.4f)" % (k, n / rounds))
    ck(free, "a tie replays for free")
    ck(paid == wins * 190, "a win pays 1.9x")
    ck(lua.eval("TapCatForever.RPS.Payout(15)") == 29 and lua.eval("TapCatForever.RPS.Payout(11)") == 21, "payout rounded to the nearest TapCoin")
    p0, w0, won0 = map(int, c0.split(","))
    c1 = ev("(function() local c = TapCatForever:CasinoData().rps; return c.played .. ',' .. c.wagered .. ',' .. c.won end)()")
    p1, w1, won1 = map(int, c1.split(","))
    ck(p1 - p0 == N and w1 - w0 == N * BET and won1 - won0 == paid, "stats: played, wagered, won (%s -> %s)" % (c0, c1))
    edge = 1 - paid / (N * BET)
    exact = {b: 1 - ((b * 19 + 5) // 10) / (2 * b) for b in range(10, 501)}
    ck(abs(edge - exact[100]) < 4 * 1.9 * sd, "measured edge %.4f near %.4f" % (edge, exact[100]))
    ck(min(exact.values()) > 0.03, "always a house edge")
    # one game's coins: the bet leaves at the start, ties cost nothing, a win pays 190 on 100
    lua.execute("%s.db.coins = 1000; math.randomseed(%d)" % (T, seed))
    ck(lua.eval('(%s:RPSSoloPlay("paper", 100))' % T), "a game against the house cat")
    g, running = lua.execute("return %s:RPSSolo()" % T)
    want = 900 + (190 if (not running and g.result == "win") else 0)
    ck(running or ev("%s.db.coins" % T) == want, "coins after one round")
    # a game waiting after a tie survives a /reload; the other games wait for it
    for _ in range(200):
        g, running = lua.execute("return %s:RPSSolo()" % T)
        if running: break
        lua.execute('%s.db.coins = 1000; %s:RPSSoloPlay("rock", 100)' % (T, T))
    ck(running, "a tie came up")
    ok, err = lua.execute("return %s:DeathRollSoloStart(100, 1000)" % T)
    ck(not ok and "rock paper scissors" in err, "the death roll waits for the game after a tie (%r)" % err)
    db = lua.eval("_dbString()")
    lua2 = TD._client(load_addon, "Solocat", seed + 1, db)
    g2, running2 = lua2.execute("return %s:RPSSolo()" % T)
    ck(running2 and g2.bet == 100 and lua2.eval("%s.db.coins" % T) == 900, "the game after a tie is restored after a reload")
    for _ in range(100):
        if not lua2.execute("return select(2, %s:RPSSolo())" % T): break
        lua2.execute('%s:RPSSoloPlay("scissors")' % T)
    g2 = lua2.eval("(%s:RPSSolo())" % T)
    ck(lua2.eval("%s.db.coins" % T) == 900 + (190 if g2.result == "win" else 0), "the restored game pays right")
    ck(lua2.eval("%s.db.deathRoll.rpsSolo == nil" % T), "finished game cleared")
    # a death roll running: no rock paper scissors
    lua2.execute("%s.db.coins = 1000" % T)
    ck(lua2.eval("(%s:DeathRollSoloStart(100, 1000))" % T), "a death roll starts")
    ok, err = lua2.execute('return %s:RPSSoloPlay("rock", 100)' % T)
    ck(not ok and "death roll" in err and lua2.eval("%s.db.coins" % T) == 900, "rock paper scissors waits for the death roll (%r)" % err)
    print("rock paper scissors house cat section (%d games at %d: you win %.2f%%, %.2f%% of rounds tie, measured house edge %.2f%%, "
          "exact %.2f%% at bets that are a multiple of 10 (%.2f%% to %.2f%% at other bets), ties free, reload): all checks passed"
          % (N, BET, p * 100, ties / rounds * 100, edge * 100, exact[100] * 100, min(exact.values()) * 100, max(exact.values()) * 100))

# ---------------------------------------------------------------------------- party games
class RNet(TD.Net):
    """TD.Net, but the drop and edit hooks act on the rock paper scissors messages"""
    def __init__(self, *a):
        super().__init__(*a)
        self.rdrop = None      # fn(sender, msg) -> True to drop an R message
        self.redit = None      # fn(sender, msg) -> the message delivered instead
    def deliver(self):
        moved = True
        while moved:
            moved = False
            for name, lua in list(self.c.items()):
                out = lua.eval("_takeOut()")
                for i in range(1, len(out) + 1):
                    p, msg, ch = out[i][1], out[i][2], out[i][3]
                    moved = True
                    self.log.append((name, msg, ch))
                    ck(p == "TapCatFvr" and len(msg) <= 255, "prefix and length")
                    if msg[:1] == "R": ck(ch == ("RAID" if self.raid else "PARTY"), "game messages go to the group: %s" % ch)
                    if msg[:1] == "R" and self.rdrop and self.rdrop(name, msg): continue
                    if msg[:1] == "R" and self.redit: msg = self.redit(name, msg)
                    for other, olua in self.c.items():
                        if self.grouped(other) and self.grouped(name):
                            olua.globals()._deliver(p, msg, name + "-Forever", ch)
    def g(self, name, k): return self.c[name].eval("(function() local d = TapCatForever.RPS.duel; return d and d[%r] end)()" % k)

def _duels(seed, load_addon, rnd):
    net = RNet(load_addon, seed, rnd)
    A, B = net.add("Alice"), net.add("Bob")
    net.group(["Alice", "Bob"])
    g, coins = net.g, net.coins

    def two(r): return r if isinstance(r, tuple) else (r, None)
    def start(a, b, bet=100):
        net.pump(4)
        ok, err = two(net.ex(a, 'return TapCatForever:RPSChallenge(%r, %d)' % (b, bet)))
        ck(ok, "challenge %s (%r)" % (b, err)); net.pump(1)
        ck(g(b, "state") == "invited" and g(a, "state") == "asking", "invite arrives")
        ok, err = two(net.ex(b, "return TapCatForever:RPSAnswer(true)"))
        ck(ok, "accept (%r)" % err); net.pump(1)
        ck(g(a, "state") == "picking" and g(b, "state") == "picking", "both picking")

    # --- challenge, accept, commit, reveal, a tie replays, then a win: both settle once
    a0, b0 = coins("Alice"), coins("Bob")
    net.ex("Alice", 'TapCatForever:RPSChallenge("Bob", 100)'); net.pump(1)
    ck(B.eval("TapCatForeverDeathRollPrompt ~= nil and TapCatForeverDeathRollPrompt:IsShown()"), "prompt above Bob's screen cat")
    ptxt = B.eval("TapCatForeverDeathRollPrompt.text:GetText()")
    ck("Alice" in ptxt and "rock paper scissors" in ptxt, "the prompt names the game: %r" % ptxt)
    ck(B.eval("(TapCatForever:RPSAnswer(true))"), "accept"); net.pump(1)
    ck(not B.eval("TapCatForeverDeathRollPrompt:IsShown()"), "prompt gone after answering")
    ck(coins("Alice") == a0 - 100 and coins("Bob") == b0 - 100, "both bets held")
    ok, err = net.ex("Alice", 'return TapCatForever:DeathRollChallenge("Bob", 100, 1000)')
    ck(not ok and "rock paper scissors" in err, "no death roll while a game runs (%r)" % err)
    # Alice picks: only a hash leaves her addon, so Bob's addon can't see her pick yet
    n0 = len(net.log)
    ck(net.ex("Alice", 'return TapCatForever:RPSPick("rock")'), "Alice picks"); net.pump(1)
    sent = [m for (n, m, ch) in net.log[n0:] if n == "Alice"]
    ck(len(sent) == 1 and re.match(r"^R4;1;[0-9a-f]{6};1;[0-9a-f]{8}$", sent[0]), "a commit and nothing else: %r" % sent)
    ck(B.eval("TapCatForever.RPS.duel.oppPick == nil") and "rock" not in sent[0], "Bob doesn't know Alice's pick")
    ck(not net.ex("Alice", 'return TapCatForever:RPSPick("paper")'), "one pick a round")
    ck(net.ex("Bob", 'return TapCatForever:RPSPick("rock")'), "Bob picks the same"); net.pump(1)
    reveals = [m for (n, m, ch) in net.log[n0:] if m.startswith("R5;")]
    ck(len(reveals) >= 2, "both reveal once both commits are in")
    ck(g("Alice", "state") == "picking" and g("Alice", "round") == 2 and g("Bob", "round") == 2, "a tie: round 2")
    ck(coins("Alice") == a0 - 100 and coins("Bob") == b0 - 100, "a tie moves nothing")
    net.ex("Alice", 'TapCatForever:RPSPick("paper")'); net.ex("Bob", 'TapCatForever:RPSPick("rock")'); net.pump(2)
    ck(g("Alice", "result") == "win" and g("Bob", "result") == "lose", "paper beats rock (%s %s)" % (g("Alice", "result"), g("Bob", "result")))
    ck((coins("Alice") - a0, coins("Bob") - b0) == (100, -100), "even: the winner gets the whole bet (%d %d)" % (coins("Alice") - a0, coins("Bob") - b0))
    duels = lambda n: net.ex(n, "local c = TapCatForever:CasinoData(); local k = 0; for _, e in ipairs(c.duels or {}) do if e.game == 'rps' then k = k + 1 end end; return k")
    ck(duels("Alice") == 1 and duels("Bob") == 1, "settled exactly once each")
    net.pump(40)
    ck((coins("Alice") - a0, coins("Bob") - b0) == (100, -100) and duels("Alice") == 1 and duels("Bob") == 1, "no second settlement")
    ck(A.eval("TapCatForever.db.deathRoll.hold == nil") and B.eval("TapCatForever.db.deathRoll.hold == nil"), "holds released")
    ck("Net |cff40ff40+100" in net.ex("Alice", "return TapCatForever:CasinoStatsLine('rps')"), "Alice's rps stats")
    ck("Net |cffff6060-100" in net.ex("Bob", "return TapCatForever:CasinoStatsLine('rps')"), "Bob's rps stats")

    # --- every pair of picks, from both sides: matching amounts, the right winner
    for pa, pb in (("rock", "scissors"), ("scissors", "paper"), ("paper", "scissors"), ("scissors", "rock")):
        a0, b0 = coins("Alice"), coins("Bob")
        start("Bob", "Alice", 50)
        net.ex("Bob", "TapCatForever:RPSPick(%r)" % pb); net.pump(0.5)
        net.ex("Alice", "TapCatForever:RPSPick(%r)" % pa); net.pump(2)
        aw = {"rock": "scissors", "scissors": "paper", "paper": "rock"}[pa] == pb
        ck(g("Alice", "result") == ("win" if aw else "lose") and g("Bob", "result") == ("lose" if aw else "win"), "%s vs %s" % (pa, pb))
        ck((coins("Alice") - a0, coins("Bob") - b0) == ((50, -50) if aw else (-50, 50)), "%s vs %s: matching amounts" % (pa, pb))

    # --- a bad reveal (the pick changed after the commit): called off, no coins moved
    a0, b0 = coins("Alice"), coins("Bob")
    start("Alice", "Bob")
    def cheat(sender, msg):
        m = re.match(r"^R5;1;(\w+);(\d+);(\w);(\w+)$", msg)
        if sender == "Bob" and m:
            return "R5;1;%s;%s;%s;%s" % (m.group(1), m.group(2), {"r": "p", "p": "s", "s": "r"}[m.group(3)], m.group(4))
        return msg
    net.redit = cheat
    net.ex("Alice", 'TapCatForever:RPSPick("rock")'); net.ex("Bob", 'TapCatForever:RPSPick("scissors")'); net.pump(2)
    net.redit = None
    ck(g("Alice", "result") == "cancel" and g("Alice", "reason") == "m", "Alice sees the reveal doesn't match (%s %s)" % (g("Alice", "result"), g("Alice", "reason")))
    ck(g("Bob", "result") == "cancel" and g("Bob", "reason") == "m", "Bob is told (%s %s)" % (g("Bob", "result"), g("Bob", "reason")))
    ck(coins("Alice") == a0 and coins("Bob") == b0, "bad reveal: no coins moved")
    ck("didn't match" in A.eval("TapCatForever.RPS.REASONS.m"), "the reason says why")

    # --- a missing reveal: called off after 30 seconds, no coins moved
    a0, b0 = coins("Alice"), coins("Bob")
    start("Alice", "Bob")
    net.rdrop = lambda sender, msg: sender == "Bob" and msg.startswith("R5;")
    net.ex("Alice", 'TapCatForever:RPSPick("paper")'); net.ex("Bob", 'TapCatForever:RPSPick("rock")'); net.pump(1)
    ck(g("Alice", "state") == "reveal", "Alice waits for Bob's pick")
    net.pump(25)
    ck(g("Alice", "state") == "reveal", "still waiting before the 30 s")
    net.pump(8)
    net.rdrop = None; net.pump(2)
    ck(g("Alice", "result") == "cancel" and g("Alice", "reason") == "v", "no reveal in 30 s: called off (%s %s)" % (g("Alice", "result"), g("Alice", "reason")))
    ck(g("Bob", "result") == "cancel", "Bob's side too (%s)" % g("Bob", "result"))
    ck(coins("Alice") == a0 and coins("Bob") == b0, "missing reveal: no coins moved")

    # --- a lost reveal comes through on a resend
    a0, b0 = coins("Alice"), coins("Bob")
    start("Alice", "Bob")
    lost = {"n": 0}
    def lose_first(sender, msg):
        if sender == "Alice" and msg.startswith("R5;") and lost["n"] == 0:
            lost["n"] = 1; return True
        return False
    net.rdrop = lose_first
    net.ex("Alice", 'TapCatForever:RPSPick("scissors")'); net.ex("Bob", 'TapCatForever:RPSPick("paper")'); net.pump(10)
    net.rdrop = None
    ck(g("Alice", "result") == "win" and g("Bob", "result") == "lose", "resent reveal: finished (%s %s)" % (g("Alice", "result"), g("Bob", "result")))
    ck((coins("Alice") - a0, coins("Bob") - b0) == (100, -100), "resent reveal: matching amounts")

    # --- neither side's "who lost" arrives: nobody pays
    a0, b0 = coins("Alice"), coins("Bob")
    start("Alice", "Bob")
    net.rdrop = lambda sender, msg: msg.startswith("R6;")
    net.ex("Alice", 'TapCatForever:RPSPick("rock")'); net.ex("Bob", 'TapCatForever:RPSPick("paper")'); net.pump(1)
    ck(g("Bob", "state") == "done" and g("Alice", "state") == "done", "both wait for the other's word")
    net.pump(40); net.rdrop = None; net.pump(2)
    ck(g("Alice", "result") == "cancel" and g("Bob", "result") == "cancel", "no word: called off (%s %s)" % (g("Alice", "result"), g("Bob", "result")))
    ck(coins("Alice") == a0 and coins("Bob") == b0, "no word: no coins moved")

    # --- the loser's "I paid" never arrives: the loser pays, the winner gets its own bet back (a coin sink, never a faucet)
    a0, b0 = coins("Alice"), coins("Bob")
    start("Alice", "Bob")
    net.rdrop = lambda sender, msg: msg.startswith("R7;")
    net.ex("Alice", 'TapCatForever:RPSPick("rock")'); net.ex("Bob", 'TapCatForever:RPSPick("paper")'); net.pump(1)
    ck(g("Bob", "state") == "done" and g("Alice", "result") == "lose", "the winner waits for the loser's word")
    net.pump(40); net.rdrop = None; net.pump(2)
    ck(g("Bob", "result") == "cancel" and g("Bob", "reason") == "n", "no word: called off for the winner (%s %s)" % (g("Bob", "result"), g("Bob", "reason")))
    ck(coins("Alice") - a0 == -100 and coins("Bob") == b0, "no word: coins only leave (%d %d)" % (coins("Alice") - a0, coins("Bob") - b0))

    # --- nobody picks: called off after 60 s, no coins moved; one side picks, the other doesn't
    for who in (None, "Alice"):
        a0, b0 = coins("Alice"), coins("Bob")
        start("Alice", "Bob")
        if who: net.ex(who, 'TapCatForever:RPSPick("rock")')
        net.pump(55)
        ck(g("Alice", "state") in ("picking",) and g("Bob", "state") == "picking", "still picking before the 60 s")
        net.pump(20)
        ck(g("Alice", "result") == "cancel" and g("Bob", "result") == "cancel", "pick timeout: called off (%s %s)" % (g("Alice", "result"), g("Bob", "result")))
        ck(g("Bob", "reason") == "p", "the slow side says it didn't pick (%s)" % g("Bob", "reason"))
        ck(coins("Alice") == a0 and coins("Bob") == b0, "pick timeout: no coins moved")

    # --- decline, withdraw, invite timeout
    a0, b0 = coins("Alice"), coins("Bob")
    net.pump(25); net.ex("Bob", 'TapCatForever:RPSChallenge("Alice", 50)'); net.pump(1)
    net.ex("Alice", "TapCatForever:RPSAnswer(false)"); net.pump(1)
    ck(g("Bob", "result") == "declined" and g("Alice", "result") == "declined", "declined")
    net.pump(25); net.ex("Alice", 'TapCatForever:RPSChallenge("Bob", 50)'); net.pump(1)
    ck(net.ex("Alice", "return TapCatForever:RPSWithdraw()"), "withdraw"); net.pump(1)
    ck(g("Bob", "state") == "over" and g("Bob", "reason") == "x", "withdrawn")
    net.pump(4); net.ex("Alice", 'TapCatForever:RPSChallenge("Bob", 50)'); net.pump(1)
    net.pump(62)
    ck(g("Alice", "state") == "over" and g("Bob", "result") in ("expired", "cancel"), "invite timed out")
    ck(coins("Alice") == a0 and coins("Bob") == b0, "decline, withdraw, timeout: no coins moved")

    # --- busy: a death roll running on the other side
    net.pump(25)
    net.ex("Bob", "TapCatForever.db.coins = 2000")
    ck(net.c["Bob"].eval("(TapCatForever:DeathRollSoloStart(50, 100))"), "Bob plays a death roll")
    net.ex("Alice", 'TapCatForever:RPSChallenge("Bob", 50)'); net.pump(1)
    ck(g("Alice", "result") == "busy", "busy with a death roll (%s)" % g("Alice", "result"))
    for _ in range(400):
        if not net.c["Bob"].eval("select(2, TapCatForever:DeathRollSolo())"): break
        net.ex("Bob", "TapCatForever:DeathRollSoloRoll()"); net.pump(1.5)

    # --- not enough TapCoins
    net.ex("Bob", "TapCatForever.db.coins = 150")    # can bet up to 70
    net.pump(4); net.ex("Alice", 'TapCatForever:RPSChallenge("Bob", 100)'); net.pump(1)
    ck(g("Alice", "result") == "toohigh" and g("Bob", "result") == "toohigh", "bet above Bob's limit refused")
    net.ex("Bob", "TapCatForever.db.coins = 2000")

    # --- /reload mid-game: called off, both bets back
    a0, b0 = coins("Alice"), coins("Bob")
    start("Alice", "Bob")
    net.ex("Alice", 'TapCatForever:RPSPick("rock")'); net.pump(1)
    db = net.c["Alice"].eval("_dbString()")
    del net.c["Alice"]
    net.add("Alice", db=db)
    ck(coins("Alice") == a0, "bet back at login")
    net.c["Alice"].execute('_group = { party1 = { "Bob", "Forever" } }; _fire("GROUP_ROSTER_UPDATE")')
    net.pump(2)
    ck(g("Bob", "result") == "cancel" and g("Bob", "reason") == "r", "Bob told about the reload (%s %s)" % (g("Bob", "result"), g("Bob", "reason")))
    ck(coins("Bob") == b0 and coins("Alice") == a0, "reload: no coins moved")

    # --- left the group mid-game
    a0, b0 = coins("Alice"), coins("Bob")
    start("Bob", "Alice")
    net.ungroup("Bob"); net.c["Alice"].execute("_group = {}; _fire('GROUP_ROSTER_UPDATE')"); net.pump(1)
    ck(g("Bob", "reason") == "g", "left the group: called off")
    # 1.6.1: the other side goes by Party.lua's roster knowledge plus a grace period, never by UnitName
    ck(g("Alice", "state") == "picking", "the other side waits the grace period first")
    net.pump(TD.TapGrace(net.c["Alice"]) + 1)
    ck(g("Alice", "result") == "cancel" and g("Alice", "reason") == "g", "the other side sees them gone")
    ck(coins("Alice") == a0 and coins("Bob") == b0, "left the group: no coins moved")
    net.group(["Alice", "Bob"])

    # --- spoofed and odd messages (Cara is in the group too)
    net.add("Cara")
    net.group(["Alice", "Bob", "Cara"])
    a0, b0, c0 = coins("Alice"), coins("Bob"), coins("Cara")
    start("Alice", "Bob")
    gid = g("Alice", "id")
    net.ex("Alice", 'TapCatForever:RPSPick("rock")'); net.pump(1)
    def spoof(msg, sender="Cara-Forever", ch="PARTY", to="Alice"):
        net.c[to].globals()._deliver("TapCatFvr", msg, sender, ch)
    good = net.c["Cara"].eval('TapCatForever.RPS.Hash("x")')
    spoof("R3;1;%s;x" % gid)                                   # someone else calls it off
    spoof("R4;1;%s;1;%s" % (gid, good))                        # someone else commits
    spoof("R6;1;%s;1;c" % gid)                                 # someone else claims a result
    spoof("R3;1;%s;x" % gid, "Bob-Forever", "WHISPER")         # wrong channel
    spoof("R3;1;%s;x" % gid, "Alice-Forever")                  # yourself
    spoof("R3;2;%s;x" % gid, "Bob-Forever")                    # unknown version
    spoof("R3;1;%s;zz" % gid, "Bob-Forever")                   # unknown reason
    spoof("R3;1;abcdef;x", "Bob-Forever")                      # another game
    spoof("R7;1;%s;1;t" % gid)                                 # someone else says they paid
    for odd in ("R", "R1", "R1;1", "R1;1;zzzzzz;Alice;100", "R1;1;123456;Alice;-5", "R1;1;123456;Alice;1e9", "R1;1;123456;Alice;100;x",
                "R9;1;%s;x" % gid, "R4;1;%s;1;xyz" % gid, "R4;1;%s;0;%s" % (gid, good), "R4;1;%s;100;%s" % (gid, good),
                "R4;1;%s;1.5;%s" % (gid, good), "R5;1;%s;1;q;abcdefghijkl" % gid, "R5;1;%s;1;r;short" % gid,
                "R5;1;%s;1;r;" % gid + "a" * 40, "R5;1;%s;1;r;abc-defghijkl" % gid, "R6;1;%s;1;q" % gid, "R6;1;%s;x;c" % gid, "R7;1;%s;1;t" % gid, "R7;1;%s;1;z" % gid,
                "R1;1;123456;" + "A" * 300 + ";100"):
        spoof(odd, "Bob-Forever")
    A.execute("_fire('CHAT_MSG_ADDON', _SECRET, 'R3;1;%s;x', 'PARTY', 'Bob-Forever')" % gid)
    A.execute("_fire('CHAT_MSG_ADDON', 'TapCatFvr', _SECRET, 'PARTY', 'Bob-Forever')")
    A.execute("_fire('CHAT_MSG_ADDON', 'TapCatFvr', 'R3;1;%s;x', 'PARTY', _SECRET)" % gid)
    A.execute("_fire('CHAT_MSG_ADDON', 'TapCatFvr', 'R3;1;%s;x', _SECRET, 'Bob-Forever')" % gid)
    net.pump(1)
    ck(g("Alice", "state") == "picking" and g("Alice", "id") == gid and g("Alice", "oppHash") is None, "spoofed and odd messages ignored")
    # a reveal before its commit is ignored, and a second, different commit for the round calls it off
    spoof("R5;1;%s;1;r;abcdefghijklmnop" % gid, "Bob-Forever")
    ck(g("Alice", "state") == "picking", "a reveal before the commit is ignored")
    # a stranger outside the group can't challenge
    net.ex("Cara", "TapCatForever.RPS.duel = nil")
    spoof("R1;1;0a0b0c;Cara;50", "Zed-Forever", to="Cara")
    ck(net.c["Cara"].eval("TapCatForever.RPS.duel == nil"), "challenge from an unknown player ignored")
    # Cara challenges Alice mid-game: busy
    net.pump(4); net.ex("Cara", 'TapCatForever:RPSChallenge("Alice", 50)'); net.pump(1)
    ck(net.c["Cara"].eval("TapCatForever.RPS.duel.result") == "busy" and g("Alice", "id") == gid, "busy player answers busy")
    net.ex("Bob", 'TapCatForever:RPSPick("scissors")'); net.pump(2)
    ck(g("Alice", "result") == "win" and g("Bob", "result") == "lose", "three in the group: rock beats scissors")
    ck((coins("Alice") - a0, coins("Bob") - b0) == (100, -100) and coins("Cara") == c0, "three in the group: Cara's coins untouched")

    # --- raid
    net.group(["Alice", "Bob", "Cara"], raid=True)
    a0, c0 = coins("Alice"), coins("Cara")
    start("Cara", "Alice", 40)
    net.ex("Cara", 'TapCatForever:RPSPick("paper")'); net.ex("Alice", 'TapCatForever:RPSPick("scissors")'); net.pump(2)
    ck((coins("Alice") - a0, coins("Cara") - c0) == (40, -40), "raid game settled")
    msgs = len([1 for l in net.log if l[1][:1] == "R"])
    print("rock paper scissors party section (3 clients, %d game messages: challenge, accept, commit hides the pick, reveal, a tie replays, "
          "every pair of picks, settle once and even, a bad reveal, a missing reveal, a resent reveal, a lost result (coins only leave), "
          "no agreement, pick timeouts, decline, withdraw, invite timeout, busy with a death roll, not enough TapCoins, reload, left the group, "
          "spoofed and odd messages, raid): all checks passed" % msgs)

# ---------------------------------------------------------------------------- 1.6.7: best of 3 and 5
def _best(seed, load_addon, rnd):
    # the house cat: the game runs until one side has won 2 (or 3) rounds; one bet, one payout
    lua = TD._client(load_addon, "Bestcat", seed)
    out = lua.execute(r"""
      local T = TapCatForever
      local signs = { "rock", "paper", "scissors" }
      local res = { bad = {}, games = 0, wins = 0, points = 0 }
      for _, bo in ipairs({ 3, 5 }) do
        local need = (bo + 1) / 2
        for i = 1, 1500 do
          T.db.coins = 100000
          assert(T:RPSSoloPlay(signs[math.random(3)], 100, bo))
          local g = T:RPSSolo()
          if g.bo ~= bo then res.bad[#res.bad + 1] = "bo " .. tostring(g.bo) end
          while select(2, T:RPSSolo()) do
            if T.db.coins ~= 100000 - 100 then res.bad[#res.bad + 1] = "coins moved mid-game" end
            assert(T:RPSSoloPlay(signs[math.random(3)], 999999, 1))   -- mid-game: bet and best-of are ignored
          end
          g = T:RPSSolo()
          res.games = res.games + 1
          local top = math.max(g.wins.me, g.wins.opp)
          if top ~= need or math.min(g.wins.me, g.wins.opp) >= need then res.bad[#res.bad + 1] = "score " .. g.wins.me .. "-" .. g.wins.opp end
          if (g.result == "win") ~= (g.wins.me == need) then res.bad[#res.bad + 1] = "winner" end
          local want = 100000 - 100 + (g.result == "win" and 190 or 0)
          if T.db.coins ~= want then res.bad[#res.bad + 1] = "paid " .. T.db.coins end
          if g.result == "win" then res.wins = res.wins + 1 end
          res.points = res.points + g.wins.me + g.wins.opp
        end
      end
      -- a best-of that doesn't exist plays best of 1
      T.db.coins = 1000
      assert(T:RPSSoloPlay("rock", 100, 2))
      res.bo2 = T:RPSSolo().bo
      return res""")
    bad = list(out.bad.values())
    ck(not bad, "house best of 3 and 5: %r" % bad[:5])
    p = out.wins / out.games
    ck(abs(p - 0.5) < 4 * (0.25 / out.games) ** 0.5, "still half the games won (%.3f)" % p)
    ck(out.bo2 == 1, "best of 2 isn't a thing: best of 1")

    # with a friend
    net = RNet(load_addon, seed + 7, rnd)
    A, B = net.add("Alice"), net.add("Bob")
    net.group(["Alice", "Bob"])
    g, coins = net.g, net.coins
    net.pump(4)
    # (the test clients report version 1.1.0 to each other: say they are on this version)
    for n in ("Alice", "Bob"):
        net.ex(n, "for _, m in ipairs(TapCatForever:PartyMembers()) do m.version = '1.6.7' end")
    a0, b0 = coins("Alice"), coins("Bob")
    n0 = len(net.log)
    r = net.ex("Alice", 'return TapCatForever:RPSChallenge("Bob", 100, 3)')
    ck(r is True or (isinstance(r, tuple) and r[0]), "best of 3 challenge (%r)" % (r,)); net.pump(1)
    r1 = [m for (n, m, ch) in net.log[n0:] if m.startswith("R1;")]
    ck(len(r1) == 1 and r1[0].endswith(";100;3"), "the challenge carries best of 3: %r" % r1)
    ck(g("Bob", "bo") == 3 and g("Bob", "state") == "invited", "Bob sees best of 3")
    ck(net.ex("Bob", "return TapCatForever:RPSAnswer(true)"), "accept"); net.pump(1)
    def throw(pa, pb):
        net.ex("Alice", "TapCatForever:RPSPick(%r)" % pa); net.ex("Bob", "TapCatForever:RPSPick(%r)" % pb); net.pump(2)
    def score(n): return net.ex(n, "local w = TapCatForever.RPS.duel.wins; return w.me .. '-' .. w.opp")
    throw("paper", "rock")
    ck(g("Alice", "state") == "picking" and g("Bob", "state") == "picking" and g("Alice", "round") == 2, "a round won: the game goes on")
    ck(score("Alice") == "1-0" and score("Bob") == "0-1", "both count the round (%s %s)" % (score("Alice"), score("Bob")))
    ck(coins("Alice") == a0 - 100 and coins("Bob") == b0 - 100, "no coins move mid-game")
    throw("rock", "paper")
    ck(score("Alice") == "1-1" and g("Alice", "state") == "picking", "1-1")
    throw("rock", "rock")
    ck(score("Alice") == "1-1" and g("Alice", "round") == 4, "a tie doesn't count")
    throw("scissors", "paper")
    ck(g("Alice", "result") == "win" and g("Bob", "result") == "lose", "2-1: Alice takes the game")
    ck((coins("Alice") - a0, coins("Bob") - b0) == (100, -100), "the bet once, even (%d %d)" % (coins("Alice") - a0, coins("Bob") - b0))
    net.pump(40)
    ck((coins("Alice") - a0, coins("Bob") - b0) == (100, -100), "settled once")
    # best of 5 the other way round
    a0, b0 = coins("Alice"), coins("Bob")
    net.pump(4)
    ck(net.ex("Bob", 'return TapCatForever:RPSChallenge("Alice", 50, 5)'), "best of 5"); net.pump(1)
    ck(g("Alice", "bo") == 5, "Alice sees best of 5")
    net.ex("Alice", "TapCatForever:RPSAnswer(true)"); net.pump(1)
    for i in range(3):
        throw("rock", "paper")
        if i < 2: ck(g("Alice", "state") == "picking", "best of 5 goes on after %d" % (i + 1))
    ck(g("Bob", "result") == "win" and (coins("Alice") - a0, coins("Bob") - b0) == (-50, 50), "3-0: Bob takes best of 5")
    # best of 1 still sends the old message (older versions take it)
    net.pump(4)
    n0 = len(net.log)
    net.ex("Alice", 'TapCatForever:RPSChallenge("Bob", 20, 1)'); net.pump(1)
    r1 = [m for (n, m, ch) in net.log[n0:] if m.startswith("R1;")]
    ck(len(r1) == 1 and r1[0].endswith(";20"), "best of 1: the old challenge message: %r" % r1)
    net.ex("Bob", "TapCatForever:RPSAnswer(false)"); net.pump(1)
    # a friend on an older version: best of 3 is refused with the reason, best of 1 still works
    net.pump(10)
    net.ex("Alice", "for _, m in ipairs(TapCatForever:PartyMembers()) do if m.name:find('Bob') then m.version = '1.6.6' end end")
    ok, err = net.ex("Alice", 'return TapCatForever:RPSChallenge("Bob", 20, 3)')
    ck(not ok and "1.6.7" in err and "Bob" in err, "an older friend: best of 3 refused (%r)" % err)
    ck(net.ex("Alice", 'return TapCatForever:RPSChallenge("Bob", 20, 1)'), "best of 1 with the older friend")
    net.pump(1); net.ex("Bob", "TapCatForever:RPSAnswer(false)"); net.pump(1)
    ck(net.c["Alice"].eval("TapCatForever.RPS.VersionAtLeast('1.6.10', '1.6.7')") is True and
       net.c["Alice"].eval("TapCatForever.RPS.VersionAtLeast('1.6.6.2', '1.6.7')") is False, "version compare")
    print("rock paper scissors best of 3 and 5 section (house: %d games, the score ends at 2 or 3 wins, one bet and one payout; friends: "
          "the challenge carries it, both count the rounds, ties don't count, settles once; best of 1 keeps the old message; an older friend is told why): all checks passed" % out.games)

# ---------------------------------------------------------------------------- scene
def _scene(seed, load_addon):
    lua = TD._client(load_addon, "Scenecat", seed)
    lua.execute('''
      _textures = {}
      local T = TapCatForever
      T.db.coins = 4000
      local box = CreateFrame("Frame", nil, UIParent)
      _drRefresh = T.UI.CasinoDeathRoll(box, nil)
      local v = T.DR.views[1]
      v:SetGame("rps"); v:SetMode("house")
    ''')
    ck(lua.eval("TapCatForever.DR.views[1].game") == "rps", "the game switch picks rock paper scissors")
    ck(lua.eval("TapCatForever.DR.views[1].bgName") == "mountain", "on the mountaintop")
    ck(lua.eval("TapCatForever.DR.ViewGame()") == "rps", "the Casino's stats line follows the game")
    # a few rounds through the scene's pick buttons: the payout waits for the reveal on screen
    out = lua.execute('''
      local T = TapCatForever
      local v = T.DR.views[1]
      local res = { held = 0, paidAfter = 0, games = 0 }
      local C = T:CasinoData().rps
      for i = 1, 24 do
        local won0 = C.won    -- paid back by rock paper scissors (other rewards can't blur it)
        local b = v.picks[({ "rock", "paper", "scissors" })[i % 3 + 1]]; b:GetScript("OnClick")(b)
        local g = T:RPSSolo()
        if g.over and g.result == "win" then
          res.wins = (res.wins or 0) + 1
          if C.won == won0 then res.held = res.held + 1 end
        end
        for k = 1, 40 do _update(0.1) end   -- the shake, the reveal and the result play out
        if g.over and g.result == "win" and C.won == won0 + g.paid then res.paidAfter = res.paidAfter + 1 end
        if g.over then res.games = res.games + 1 end
      end
      for i = 1, 50 do   -- finish a game left waiting after a tie
        if not select(2, T:RPSSolo()) then break end
        v:Pick("paper"); for k = 1, 40 do _update(0.1) end
      end
      return res''')
    ck((out.wins or 0) >= 1 and out.held == out.wins and out.paidAfter == out.wins, "a win is held during the reveal and paid after it (%s %d %d)" % (out.wins, out.held, out.paidAfter))
    ck(out.games >= 3, "games played through the scene (%d)" % out.games)
    ck(lua.eval("TapCatForever:CasinoData().pending.rps == nil"), "nothing left waiting")
    # every state and result reads as plain text
    texts = lua.execute('''
      local T, R = TapCatForever, TapCatForever.RPS
      local v = T.DR.views[1]
      local out = {}
      local function snap() v:Refresh(true); out[#out + 1] = tostring(v.status:GetText()) .. " | " .. tostring(v.action:GetText()) .. " | " .. tostring(v.rangeCap:GetText()) .. " " .. tostring(v.rangeNum:GetText()) end
      local base = { id = "abcdef", opp = "Bob", oppBase = "bob", bet = 100, round = 1, rounds = {}, expires = _clock + 30, roundAt = _clock, doneAt = _clock }
      local function duel(fields) local d = {} for k, x in pairs(base) do d[k] = x end for k, x in pairs(fields) do d[k] = x end R.duel = d; snap() end
      v:SetMode("friend")
      duel({ state = "asking", role = "out" })
      duel({ state = "invited", role = "in" }); out[#out + 1] = v.inv.text:GetText()
      duel({ state = "picking", role = "out" })
      duel({ state = "picking", role = "out", myPick = "rock" })
      duel({ state = "picking", role = "out", round = 2, rounds = { { me = "rock", opp = "rock", res = "tie" } } })
      duel({ state = "reveal", role = "in", myPick = "paper" })
      duel({ state = "done", role = "in", myPick = "paper", loser = "opp" })
      for _, r in ipairs({ "win", "lose", "declined", "busy", "toohigh", "expired" }) do
        duel({ state = "over", role = "out", result = r, by = "opp", me = "rock", opp_ = "scissors" })
        duel({ state = "over", role = "in", result = r, by = "me", me = "scissors", opp_ = "rock" })
      end
      duel({ state = "over", role = "out", result = "win", opp = "Thrallbeard-ArgentDawn", oppBase = "thrallbeard", me = "paper", opp_ = "rock" })
      for k in pairs(R.REASONS) do
        duel({ state = "over", role = "out", result = "cancel", reason = k, by = "opp" })
        duel({ state = "over", role = "out", result = "cancel", reason = k, by = "me" })
      end
      -- 1.6.7: best of 3 and 5 texts
      duel({ state = "invited", role = "in", bo = 3, wins = { me = 0, opp = 0 } }); out[#out + 1] = v.inv.text:GetText()
      duel({ state = "picking", role = "out", bo = 3, round = 2, wins = { me = 1, opp = 0 }, rounds = { { me = "paper", opp = "rock", res = "win" } } })
      out[#out + 1] = v.rpsInfo:GetText() .. " / " .. v.rpsInfo2:GetText()
      duel({ state = "over", role = "out", result = "win", bo = 3, wins = { me = 2, opp = 1 }, me = "rock", opp_ = "scissors" })
      duel({ state = "picking", role = "out", bo = 5, round = 3, wins = { me = 1, opp = 1 }, rounds = { { me = "rock", opp = "paper", res = "lose" } } })
      out[#out + 1] = v.rpsInfo:GetText() .. " / " .. v.rpsInfo2:GetText()
      R.duel = nil
      v:SetMode("friend"); snap()
      v:SetMode("house"); snap()
      local bb = v.bestBtn
      bb:GetScript("OnClick")(bb); snap(); out[#out + 1] = bb:GetText() .. " / " .. v.rpsInfo2:GetText()
      _bestAfterClick = v.bestOf .. "," .. tostring(T.db.deathRoll.rpsBest)
      bb:GetScript("OnClick")(bb); bb:GetScript("OnClick")(bb)
      _bestCycle = v.bestOf
      bb:GetScript("OnClick")(bb)
      out[#out + 1] = v.how.body:GetText()
      v:SetMode("friend"); snap(); out[#out + 1] = v.how.body:GetText()
      v:SetGame("dr"); snap()
      out[#out + 1] = tostring(v.bgName)
      return out''')
    texts = list(texts.values())
    if os.environ.get("RPS_TEXTS"): print("\n".join(texts))
    for t in texts:
        ck("!" not in t and "%s" not in t and "%d" not in t and "nil" not in t, "scene text: %r" % t)
    ck(any("You win" in t for t in texts) and any("Pick rock, paper or scissors" in t for t in texts) and any("No TapCoins moved" in t for t in texts), "scene texts")
    ck(any("didn't match" in t for t in texts) and any("never came through" in t for t in texts), "the reasons say why")
    ck(any("Rock beats scissors" in t for t in texts) and any("Paper beats rock" in t for t in texts), "who beats whom")
    ck(not any("ArgentDawn" in t for t in texts), "names without their realm")
    ck(any("The house cat picks at random" in t for t in texts) and any("Each picks rock, paper or scissors in secret" in t for t in texts), "How to play for both opponents")
    ck(texts[-1] == "tavern", "back to the tavern for the death roll")
    ck(any("rock paper scissors, best of 3 for" in t for t in texts), "the invite says best of 3")
    ck(any(t == "Best of 3 / You 1 - 0 Bob" for t in texts) and any(t == "Best of 5 / You 1 - 1 Bob" for t in texts), "the score in the top bar")
    ck(any("You take that round (You 1 - 0 Bob)" in t for t in texts) and any("Bob takes that round (You 1 - 1 Bob)" in t for t in texts), "who took the last round")
    ck(any(t == "Best of 3 / First to 2 wins" for t in texts), "the best-of button")
    ck(any("Rock beats scissors. Best of 3: 2 - 1." in t for t in texts), "the final score after a longer game")
    ck(lua.eval("_bestAfterClick") == "3,3" and lua.eval("_bestCycle") == 1, "the button goes 1, 3, 5, 1 and is remembered")
    # every texture exists, and the paw signs are used
    art = os.path.join(ROOT, "Art")
    used = [p for p in lua.eval("(function() local t = {} for p in pairs(_textures) do t[#t + 1] = p end return t end)()").values()]
    casino = [p.split("Art\\", 1)[1] for p in used if "\\casino\\" in p]
    for need in ("mountain", "rps_rock_fur", "rps_paper_line", "rps_scissors_fur"):
        ck(any(p.endswith(need) for p in casino), "texture used: %s" % need)
    missing = [p for p in casino if not os.path.exists(os.path.join(art, p.replace("\\", "/") + ".tga"))]
    ck(not missing, "missing art: %r" % missing)
    for fn in ("RPS.lua", "UI_RPS.lua"):
        src = open(os.path.join(ROOT, fn), encoding="utf-8").read()
        for s in re.findall(r'"((?:[^"\\]|\\.)*)"', src):
            ck("!" not in s, "exclamation mark in %s: %r" % (fn, s))
    print("rock paper scissors scene section (the game switch, the mountaintop, picks through the scene with the payout after the reveal, "
          "plain text, %d textures in Art/casino): all checks passed" % len(casino))

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import test_harness
    sys.modules["__main__"].LB_CLIENT = test_harness.LB_CLIENT
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
