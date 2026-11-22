# Death roll (DeathRoll.lua, UI_DeathRoll.lua): the solo game against the house cat (edge measured
# over many games, bookkeeping, limits, a game that survives a reload) and the duel with party members
# (2-3 simulated clients passing addon messages, with /roll results as localized system chat lines):
# challenge, accept, decline, timeouts, turn order, wrong-range and stray rolls ignored, both sides
# settle exactly once with matching amounts, not enough TapCoins, busy, /reload mid-duel (called off,
# or finished when the 1 was already seen), hidden (secret) roll text, spoofed and odd messages, raid,
# other languages' roll text, the scene and the prompt above the screen cat.
# Run on its own:  python3 tools/tests/test_deathroll.py [seed]
import os, random, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

CLIENT = r'''
_out = {}
C_ChatInfo.SendAddonMessage = function(p, msg, ch, target)
  if _sendResult == 0 then table.insert(_out, { p, msg, ch, target or "" }) end
  return _sendResult
end
function _takeOut() local o = _out; _out = {}; return o end
_rollReq = {}
function RandomRoll(lo, hi) table.insert(_rollReq, { lo, hi }) end
function _takeRolls() local o = _rollReq; _rollReq = {}; return o end
RANDOM_ROLL_RESULT = "%s rolls %d (%d-%d)"
function _deliver(p, msg, sender, chan) _fire("CHAT_MSG_ADDON", p, msg, chan, sender, "", 0, 0, "", 0) end
function _sys(text) _fire("CHAT_MSG_SYSTEM", text, "", "", "", "", "", 0, 0, "", 0) end
-- a small serializer, to carry the saved variables over a /reload
function _ser(v, seen)
  local t = type(v)
  if t == "string" then return string.format("%q", v) end
  if t == "number" or t == "boolean" then return tostring(v) end
  if t ~= "table" then return "nil" end
  local parts = {}
  for k, x in pairs(v) do
    local tk = type(k)
    if (tk == "string" or tk == "number") and type(x) ~= "function" then
      parts[#parts + 1] = "[" .. _ser(k) .. "]=" .. _ser(x)
    end
  end
  return "{" .. table.concat(parts, ",") .. "}"
end
function _dbString() setmetatable(TapCatForeverDB, nil); return _ser(TapCatForeverDB) end
function _duel() return TapCatForever.DR.duel end
function _st(k) local d = TapCatForever.DR.duel; return d and d[k] end
function _coins() return TapCatForever.db.coins end
function _duels() local c = TapCatForever:CasinoData(); return c.duels and #c.duels or 0 end
function _duelSum() local c = TapCatForever:CasinoData(); local s = 0; for _, e in ipairs(c.duels or {}) do s = s + e.delta end; return s end
'''

def check(seed, load_addon):
    rnd = random.Random(seed)
    _solo(seed, load_addon, rnd)
    _pattern(load_addon)
    _duels(seed, load_addon, rnd)
    _scene(seed, load_addon)

def win_of(bet): return bet   # duels between friends are even: the winner gets the whole bet (no table fee)

def settled(da, db, bet, ra):
    """da, db: the two players' coin changes; ra: the first player's result"""
    w = win_of(bet)
    return (da, db) == ((w, -bet) if ra == "win" else (-bet, w))

def ck(c, m):
    if not c: raise AssertionError("death roll: " + m)

def _client(load_addon, name, seed, db=None, extra=""):
    lua = load_addon(login=False)
    lua.execute(CLIENT)
    lua.execute('_charName = "%s"; math.randomseed(%d)' % (name, (seed + sum(map(ord, name)) * 7919) % 2147483647))
    if extra: lua.execute(extra)
    if db: lua.execute("TapCatForeverDB = loadstring(%r)()" % ("return " + db))
    lua.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    # the mock only knows some events; the duel reads the system chat lines
    lua.execute("TapCatForever.DR.frame.events.CHAT_MSG_SYSTEM = true")
    return lua

# ---------------------------------------------------------------------------- solo
def _solo(seed, load_addon, rnd):
    lua = _client(load_addon, "Solocat", seed)
    T = "TapCatForever"
    ev = lua.eval
    lua.execute("%s.db.coins = 39" % T)
    ok, err = lua.execute("return %s:DeathRollSoloStart(10, 1000)" % T)
    ck(not ok and "40" in err, "fewer than 40 TapCoins: no game (%r)" % err)
    lua.execute("%s.db.coins = 1000" % T)
    for bad in (5, 9, 251, 10.5):
        ok, err = lua.execute("return %s:DeathRollSoloStart(%s, 1000)" % (T, bad))
        ck(not ok and ev("%s.db.coins" % T) == 1000, "bet %s refused (limits 10 to 250)" % bad)
    ok, err = lua.execute("return %s:DeathRollSoloStart(100, 777)" % T)
    ck(not ok, "odd range refused")
    # many games at 100 each (fast: the timer is driven directly)
    lua.execute('''
      function _playSolo(n, bet, range)
        local T = TapCatForever
        local wins, houseFirst, rolls, paid = 0, 0, 0, 0
        for i = 1, n do
          T.db.coins = 100000
          assert(T:DeathRollSoloStart(bet, range))
          local g = T:DeathRollSolo()
          if g.turn == "house" then houseFirst = houseFirst + 1 end
          local guard = 0
          while true do
            local cur, running = T:DeathRollSolo()
            if not running then
              if cur.loser == "house" then wins = wins + 1; paid = paid + cur.paid end
              rolls = rolls + cur.n
              break
            end
            if cur.turn == "me" then assert(T:DeathRollSoloRoll())
            else
              assert(not T:DeathRollSoloRoll(), "rolled on the house cat's turn")
              _clock = _clock + 2; T.DR.Tick()
            end
            guard = guard + 1; assert(guard < 5000)
          end
        end
        return wins, houseFirst, rolls, paid
      end''')
    c0 = lua.eval("(function() local c = TapCatForever:CasinoData().deathroll; return c.played .. ',' .. c.wagered .. ',' .. c.won end)()")
    N, BET = 30000, 100
    wins, hf, rolls, paid = lua.eval("{_playSolo(%d, %d, 1000)}" % (N, BET)).values()
    p, sd = wins / N, (0.25 / N) ** 0.5
    ck(abs(p - 0.5) < 4 * sd, "you win half the games (%.4f)" % p)
    ck(abs(hf / N - 0.5) < 4 * sd, "the house cat rolls first half the time (%.4f)" % (hf / N))
    ck(paid == wins * 190, "a win pays 1.9x")
    ck(lua.eval("TapCatForever.DR.Payout(15)") == 29 and lua.eval("TapCatForever.DR.Payout(11)") == 21, "payout rounded to the nearest TapCoin")
    p0, w0, won0 = map(int, c0.split(","))
    c1 = lua.eval("(function() local c = TapCatForever:CasinoData().deathroll; return c.played .. ',' .. c.wagered .. ',' .. c.won end)()")
    p1, w1, won1 = map(int, c1.split(","))
    ck(p1 - p0 == N and w1 - w0 == N * BET and won1 - won0 == paid, "stats: played, wagered, won (%s -> %s)" % (c0, c1))
    edge = 1 - paid / (N * BET)
    # exact: the coin flip makes the win chance exactly 1/2, so the edge is 1 - floor(1.9 bet) / (2 bet)
    exact = {b: 1 - ((b * 19 + 5) // 10) / (2 * b) for b in range(10, 501)}
    ck(abs(edge - exact[100]) < 4 * 1.9 * sd, "measured edge %.4f near %.4f" % (edge, exact[100]))
    ck(min(exact.values()) > 0.03, "always a house edge (%.4f at worst)" % min(exact.values()))
    # exact first-roller odds for the report: P(first roller loses) from 1000
    f = [0.0, 1.0]; S = 0.0
    for n in range(2, 1001):
        f.append((n - S) / (n + 1)); S += f[n]
    # one game's coins: the stake leaves at the start, the payout comes on a win
    lua.execute("%s.db.coins = 1000" % T)
    lua.execute("math.randomseed(%d)" % seed)
    ck(lua.eval("(%s:DeathRollSoloStart(100, 100))" % T), "start at 100")
    ck(ev("%s.db.coins" % T) == 900, "stake taken")
    ok, err = lua.execute("return %s:DeathRollSoloStart(100, 100)" % T)
    ck(not ok, "one game at a time")
    # a game survives a /reload, mid-way, and finishes with the right money
    g = lua.eval("(TapCatForever:DeathRollSolo())")
    if g.turn == "me": lua.execute("%s:DeathRollSoloRoll()" % T)
    if lua.eval("select(2, TapCatForever:DeathRollSolo())"):
        cur = lua.eval("TapCatForever:DeathRollSolo().cur")
        db = lua.eval("_dbString()")
        lua2 = _client(load_addon, "Solocat", seed + 1, db)
        g2, running = lua2.execute("return TapCatForever:DeathRollSolo()")
        ck(running and g2.cur == cur and g2.bet == 100, "solo game restored after a reload")
        ck(lua2.eval("TapCatForever.db.coins") == 900, "no coins moved by the reload")
        for _ in range(500):
            g2, running = lua2.execute("return TapCatForever:DeathRollSolo()")
            if not running: break
            if g2.turn == "me": lua2.execute("TapCatForever:DeathRollSoloRoll()")
            else: lua2.execute("_clock = _clock + 2; TapCatForever.DR.Tick()")
        g2 = lua2.eval("(TapCatForever:DeathRollSolo())")
        ck(lua2.eval("TapCatForever.db.coins") == 900 + (190 if g2.loser == "house" else 0), "restored game pays right")
        ck(lua2.eval("TapCatForever.db.deathRoll.solo == nil"), "finished game cleared")
    print("death roll solo section (%d games at %d: you win %.2f%%, house cat first %.2f%%, %.2f rolls a game, "
          "measured house edge %.2f%%, exact %.2f%% at bets that are a multiple of 10 (%.2f%% to %.2f%% at other bets), "
          "first roller from 1,000 loses %.5f%%): all checks passed"
          % (N, BET, p * 100, hf / N * 100, rolls / N, edge * 100, exact[100] * 100, min(exact.values()) * 100, max(exact.values()) * 100, f[1000] * 100))

# ---------------------------------------------------------------------------- roll text
def _pattern(load_addon):
    lua = load_addon()
    P = "TapCatForever.DR.ParseRoll"
    def parse(fmt, text):
        lua.execute("RANDOM_ROLL_RESULT = %r" % fmt)
        r = lua.execute("return %s(%r)" % (P, text))
        return r if isinstance(r, tuple) else (r,)
    ck(parse("%s rolls %d (%d-%d)", "Bob rolls 612 (1-1000)") == ("Bob", 612, 1, 1000), "english")
    ck(parse("%s rolls %d (%d-%d)", "Bob-Other Realm rolls 5 (1-100)") == ("Bob-Other Realm", 5, 1, 100), "cross-realm name")
    ck(parse("%s würfelt. Ergebnis: %d (%d-%d)", "Bob würfelt. Ergebnis: 7 (1-88)") == ("Bob", 7, 1, 88), "german")
    ck(parse("(%3$d-%4$d) %2$d : %1$s", "(1-1000) 44 : Bob") == ("Bob", 44, 1, 1000), "positional, reordered")
    ck(parse("%s obtient un %d (%d-%d).", "Bob obtient un 3 (1-9).") == ("Bob", 3, 1, 9), "french with a dot")
    ck(parse("%s rolls %d (%d-%d)", "Bob says rolls 5 (1-100) lol")[0] is None, "other text")
    ck(parse("%s rolls %d (%d-%d)", "Bob rolls x (1-100)")[0] is None, "not a number")
    lua.execute("RANDOM_ROLL_RESULT = nil")
    ck(lua.execute("return %s('Bob rolls 2 (1-3)')" % P) == ("Bob", 2, 1, 3), "fallback without the global")
    ck(lua.execute("return %s(_SECRET)" % P) is None, "secret text is not read")
    print("death roll text section (English, cross-realm, German, French, reordered positions, fallback, secret): all checks passed")

# ---------------------------------------------------------------------------- duels
class Net:
    def __init__(self, load_addon, seed, rnd):
        self.load_addon, self.seed, self.rnd = load_addon, seed, rnd
        self.c = {}            # name -> lua
        self.forced = []       # roll values to hand out next
        self.drop = False      # drop every addon message (lost messages)
        self.log = []
        self.raid = False
    def add(self, name, coins=2000, db=None, extra=""):
        lua = _client(self.load_addon, name, self.seed, db, extra)
        if db is None: lua.execute("TapCatForever.db.coins = %d" % coins)
        self.c[name] = lua
        return lua
    def group(self, names, raid=False):
        self.raid = raid
        for n in names:
            others = [o for o in names if o != n]
            units = ", ".join('%s%d = { "%s", "Forever" }' % ("raid" if raid else "party", i + 1, o) for i, o in enumerate(others))
            self.c[n].execute("_group = { %s }; _raid = %s" % (units, "true" if raid else "false"))
        for n in names: self.c[n].execute('_fire("GROUP_ROSTER_UPDATE")')
        self.pump(12)
    def ungroup(self, name):
        self.c[name].execute('_group = nil; _raid = false; _fire("GROUP_ROSTER_UPDATE")')
    def grouped(self, name): return self.c[name].eval("_group ~= nil")
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
                    if msg[:1] == "D": ck(ch == ("RAID" if self.raid else "PARTY"), "duel messages go to the group: %s" % ch)
                    if self.drop and msg[:1] == "D": continue
                    for other, olua in self.c.items():   # the whole group hears it, the sender too (echo)
                        if self.grouped(other) and self.grouped(name):
                            olua.globals()._deliver(p, msg, name + "-Forever", ch)
                rolls = lua.eval("_takeRolls()")
                for i in range(1, len(rolls) + 1):
                    lo, hi = rolls[i][1], rolls[i][2]
                    v = self.forced.pop(0) if self.forced else self.rnd.randint(lo, hi)
                    v = max(lo, min(hi, v))
                    self.sys("%s rolls %d (%d-%d)" % (name, v, lo, hi))
                    moved = True
    def sys(self, text):
        for lua in self.c.values():
            if lua.eval("_group ~= nil"): lua.globals()._sys(text)
    def pump(self, seconds=1, dt=0.5):
        for _ in range(int(seconds / dt)):
            for lua in self.c.values(): lua.execute("_update(%f)" % dt)
            self.deliver()
    def st(self, name, k): return self.c[name].eval("_st(%r)" % k)
    def coins(self, name): return self.c[name].eval("_coins()")
    def ex(self, name, code): return self.c[name].execute(code)

def _play_to_end(net, a, b, values, check_turns=True):
    """rolls for whoever's turn it is until the 1; values are handed out in order"""
    net.forced = list(values)
    for _ in range(60):
        if net.st(a, "state") != "rolling": break
        roller = a if net.st(a, "turn") == "me" else b
        other = b if roller == a else a
        if check_turns:
            ck(net.st(other, "turn") == "opp", "both agree whose turn it is")
            ck(not net.ex(other, "return TapCatForever:DeathRollRoll()"), "no roll on the other's turn")
        ck(net.ex(roller, "return TapCatForever:DeathRollRoll()"), "roll on your turn")
        net.pump(1)
    net.pump(2)

def _duels(seed, load_addon, rnd):
    net = Net(load_addon, seed, rnd)
    A, B = net.add("Alice"), net.add("Bob")
    net.group(["Alice", "Bob"])
    ck(net.ex("Alice", "return #TapCatForever:PartyMembers()") == 1, "Alice sees Bob's cat")
    msgs = 0

    # --- challenge, accept, play to the 1, both settle once
    a0, b0 = net.coins("Alice"), net.coins("Bob")
    ok = A.eval('(TapCatForever:DeathRollChallenge("Bob", 100, 1000))')
    ck(ok, "challenge sent")
    net.pump(1)
    ck(net.st("Bob", "state") == "invited" and net.st("Alice", "state") == "asking", "invite arrives")
    ck(B.eval("TapCatForeverDeathRollPrompt ~= nil and TapCatForeverDeathRollPrompt:IsShown()"), "prompt above Bob's screen cat")
    ck("Alice" in B.eval("TapCatForeverDeathRollPrompt.text:GetText()"), "prompt names the challenger")
    ck(B.eval("(TapCatForever:DeathRollAnswer(true))"), "accept")
    net.pump(1)
    ck(not B.eval("TapCatForeverDeathRollPrompt:IsShown()"), "prompt gone after answering")
    ck(net.st("Alice", "state") == "rolling" and net.st("Bob", "state") == "rolling", "duel running")
    ck(net.coins("Alice") == a0 - 100 and net.coins("Bob") == b0 - 100, "both stakes held")
    ck(net.st("Alice", "turn") != net.st("Bob", "turn"), "one turn each")
    # stray rolls: wrong player, wrong range, someone else, a normal chat line
    roller = "Alice" if net.st("Alice", "turn") == "me" else "Bob"
    other = "Bob" if roller == "Alice" else "Alice"
    net.sys("%s rolls 500 (1-1000)" % other)          # not their turn
    net.sys("%s rolls 50 (1-100)" % roller)           # wrong range
    net.sys("%s rolls 50 (2-1000)" % roller)          # wrong low end
    net.sys("Stranger rolls 1 (1-1000)")              # not in the duel
    net.sys("%s rolls 1001 (1-1000)" % roller)        # impossible
    net.sys("%s has gone offline." % roller)
    ck(net.st("Alice", "cur") == 1000 and net.st("Alice", "n") == 0 and net.st("Bob", "n") == 0, "stray rolls ignored")
    _play_to_end(net, "Alice", "Bob", [612, 88, 9, 1])
    ck(net.st("Alice", "state") == "over" and net.st("Bob", "state") == "over", "both done")
    ra, rb = net.st("Alice", "result"), net.st("Bob", "result")
    ck({ra, rb} == {"win", "lose"}, "one wins, one loses (%s %s)" % (ra, rb))
    da, db_ = net.coins("Alice") - a0, net.coins("Bob") - b0
    ck(settled(da, db_, 100, ra), "matching amounts (%d %d)" % (da, db_))
    ck(net.ex("Alice", "return _duels()") == 1 and net.ex("Bob", "return _duels()") == 1, "settled exactly once each")
    loser = "Alice" if ra == "lose" else "Bob"
    rolls = [m for (n, m, ch) in net.log if m.startswith("D4;")]
    # resent D4s and more time change nothing
    net.pump(20)
    ck(net.coins("Alice") - a0 == da and net.coins("Bob") - b0 == db_, "no second settlement")
    ck(net.ex("Alice", "return _duels()") == 1 and net.ex("Bob", "return _duels()") == 1, "still once")
    ck(A.eval("TapCatForever.db.deathRoll.hold == nil") and B.eval("TapCatForever.db.deathRoll.hold == nil"), "holds released")
    ck(net.ex("Alice", "return _duelSum()") + net.ex("Bob", "return _duelSum()") == 0, "duel log: even, no table fee")
    ck(A.eval("TapCatForever.DR.DuelWin(100)") == 100 and A.eval("TapCatForever.DR.DuelWin(37)") == 37, "DuelWin: the whole bet")
    # the stats count the bet and what came back, so a win shows its profit
    for n in ("Alice", "Bob"):
        line = net.ex(n, "return TapCatForever:CasinoStatsLine('deathroll')")
        want = "Net |cff40ff40+100" if net.st(n, "result") == "win" else "Net |cffff6060-100"
        ck(want in line, "%s's stats line: %s" % (n, line))

    # --- decline
    a0, b0 = net.coins("Alice"), net.coins("Bob")
    net.pump(4); net.ex("Bob", 'TapCatForever:DeathRollChallenge("Alice", 50, 100)'); net.pump(1)
    ck(net.st("Alice", "state") == "invited", "second invite")
    net.ex("Alice", "TapCatForever:DeathRollAnswer(false)"); net.pump(1)
    ck(net.st("Bob", "result") == "declined" and net.st("Alice", "result") == "declined", "declined both sides")
    ck(net.coins("Alice") == a0 and net.coins("Bob") == b0, "decline: no coins moved")

    # --- invite timeout
    net.pump(4); net.ex("Alice", 'TapCatForever:DeathRollChallenge("Bob", 50, 1000)'); net.pump(1)
    net.pump(62)
    ck(net.st("Alice", "state") == "over" and net.st("Bob", "state") == "over", "invite timed out")
    ck(net.st("Bob", "result") in ("expired", "cancel") and net.st("Alice", "result") in ("cancel", "declined"), "timeout results")
    ck(not B.eval("TapCatForeverDeathRollPrompt:IsShown()"), "prompt gone after 60 s")
    ck(net.coins("Alice") == a0 and net.coins("Bob") == b0, "timeout: no coins moved")

    # --- a player you said no to waits a little before challenging again
    net.pump(4); net.ex("Alice", 'TapCatForever:DeathRollChallenge("Bob", 50, 1000)'); net.pump(1)
    ck(net.st("Bob", "state") == "over", "no new prompt right after letting one run out")
    net.pump(70)
    # --- withdraw
    net.pump(4); net.ex("Alice", 'TapCatForever:DeathRollChallenge("Bob", 50, 1000)'); net.pump(1)
    ck(net.ex("Alice", "return TapCatForever:DeathRollWithdraw()"), "withdraw"); net.pump(1)
    ck(net.st("Bob", "state") == "over" and net.st("Bob", "reason") == "x", "withdrawn")

    # --- turn timeout: the player who doesn't roll in time loses (their own addon pays)
    def start(a, b, bet=100, rng=1000):
        net.pump(4)   # one challenge per player every few seconds
        net.ex(a, 'TapCatForever:DeathRollChallenge(%r, %d, %d)' % (b, bet, rng)); net.pump(1)
        ck(net.c[b].eval("(TapCatForever:DeathRollAnswer(true))"), "accept %s" % b); net.pump(1)
        ck(net.st(a, "state") == "rolling" and net.st(b, "state") == "rolling", "duel %s-%s running" % (a, b))
    a0, b0 = net.coins("Alice"), net.coins("Bob")
    start("Alice", "Bob")
    net.forced = [400]
    r = "Alice" if net.st("Alice", "turn") == "me" else "Bob"
    net.ex(r, "TapCatForever:DeathRollRoll()"); net.pump(1)
    ck(net.st("Alice", "cur") == 400 and net.st("Bob", "cur") == 400, "first roll counted")
    slow = "Bob" if r == "Alice" else "Alice"
    net.pump(55)
    ck(net.st("Alice", "state") == "rolling" and net.st("Bob", "state") == "rolling", "still running before the 60 s")
    net.pump(7)
    ck(net.st(slow, "result") == "lose" and net.st(slow, "reason") == "f", "turn timeout: the slow player loses (%s %s)" % (net.st(slow, "result"), net.st(slow, "reason")))
    ck(net.st(r, "result") == "win" and net.st(r, "reason") == "f", "turn timeout: the other player wins")
    d_r, d_s = net.coins(r) - (a0 if r == "Alice" else b0), net.coins(slow) - (a0 if slow == "Alice" else b0)
    ck((d_r, d_s) == (100, -100), "turn timeout: paid like a lost duel (%d %d)" % (d_r, d_s))
    a0, b0 = net.coins("Alice"), net.coins("Bob")
    # the forfeit message is lost: the slow player still pays, the other gets their own stake back (coins only leave)
    start("Alice", "Bob")
    slow = "Alice" if net.st("Alice", "turn") == "me" else "Bob"
    other = "Bob" if slow == "Alice" else "Alice"
    net.pump(55); net.drop = True; net.pump(25); net.drop = False; net.pump(2)
    ck(net.st(slow, "result") == "lose" and net.st(other, "result") == "cancel", "lost forfeit message: %s %s" % (net.st(slow, "result"), net.st(other, "result")))
    ck(net.coins(slow) - (a0 if slow == "Alice" else b0) == -100 and net.coins(other) == (a0 if other == "Alice" else b0), "lost forfeit message: a coin sink, never a faucet")
    a0, b0 = net.coins("Alice"), net.coins("Bob")
    # Roll was pressed but its line never came (the roll didn't go through): called off, nobody loses
    start("Alice", "Bob")
    r = "Alice" if net.st("Alice", "turn") == "me" else "Bob"
    net.ex(r, "TapCatForever:DeathRollRoll()"); net.c[r].eval("_takeRolls()")
    net.pump(70)
    ck(net.st(r, "result") == "cancel" and net.st(r, "reason") == "e", "pressed but no roll line: called off (%s %s)" % (net.st(r, "result"), net.st(r, "reason")))
    ck(net.coins("Alice") == a0 and net.coins("Bob") == b0, "no roll line: no coins moved")

    # --- secret system text: called off on both sides
    start("Bob", "Alice")
    net.c["Bob"].execute('_fire("CHAT_MSG_SYSTEM", _SECRET)'); net.pump(1)
    ck(net.st("Bob", "reason") == "s" and net.st("Alice", "result") == "cancel", "hidden roll text calls it off")
    ck(net.coins("Alice") == a0 and net.coins("Bob") == b0, "secret text: no coins moved")

    # --- not enough TapCoins
    net.ex("Bob", "TapCatForever.db.coins = 300")      # can bet up to 75
    net.pump(4); net.ex("Alice", 'TapCatForever:DeathRollChallenge("Bob", 100, 1000)'); net.pump(1)
    ck(net.st("Alice", "result") == "toohigh" and net.st("Bob", "result") == "toohigh", "bet above Bob's limit refused")
    ck(not net.c["Bob"].eval('(TapCatForever:DeathRollChallenge("Alice", 100, 1000))'), "can't challenge above your own limit")
    net.ex("Bob", "TapCatForever.db.coins = 2000")
    # coins spent between the invite and the accept
    net.pump(4); net.ex("Alice", 'TapCatForever:DeathRollChallenge("Bob", 100, 1000)'); net.pump(1)
    net.ex("Bob", "TapCatForever.db.coins = 100")
    ok, err = net.ex("Bob", "return TapCatForever:DeathRollAnswer(true)"); net.pump(1)
    ck(not ok and net.st("Alice", "state") == "over" and net.coins("Bob") == 100, "accept without the coins refused (%r)" % err)
    net.ex("Bob", "TapCatForever.db.coins = 2000")
    # the challenger spent theirs before the answer came
    net.pump(4); net.ex("Alice", 'TapCatForever:DeathRollChallenge("Bob", 100, 1000)'); net.pump(1)
    a1 = 150; net.ex("Alice", "TapCatForever.db.coins = %d" % a1)
    net.ex("Bob", "TapCatForever:DeathRollAnswer(true)"); net.pump(1)
    ck(net.st("Alice", "reason") == "c" and net.st("Bob", "result") == "cancel", "challenger short: called off")
    ck(net.coins("Alice") == a1 and net.coins("Bob") == 2000, "challenger short: Bob's stake back")
    net.ex("Alice", "TapCatForever.db.coins = 2000")

    # --- spoofed and odd messages (Cara is in the group too)
    net.add("Cara")
    net.group(["Alice", "Bob", "Cara"])
    a0, b0, cara0 = net.coins("Alice"), net.coins("Bob"), net.coins("Cara")
    start("Alice", "Bob")
    did = net.st("Alice", "id")
    C = net.c["Cara"]
    def spoof(msg, sender="Cara-Forever", ch="PARTY", to="Alice"):
        net.c[to].globals()._deliver("TapCatFvr", msg, sender, ch)
    spoof("D3;1;%s;x" % did)                                  # someone else calls it off
    spoof("D4;1;%s;c;1" % did)                                # someone else claims a result
    spoof("D3;1;%s;x" % did, "Bob-Forever", "WHISPER")        # wrong channel
    spoof("D3;1;%s;x" % did, "Alice-Forever")                 # yourself
    spoof("D3;2;%s;x" % did, "Bob-Forever")                   # unknown version
    spoof("D3;1;%s;zz" % did, "Bob-Forever")                  # unknown reason
    spoof("D3;1;abcdef;x", "Bob-Forever")                     # another duel
    for odd in ("D", "D1", "D1;1", "D1;1;zzzzzz;Alice;100;1000", "D1;1;123456;Alice;-5;1000", "D1;1;123456;Alice;100;999",
                "D9;1;%s;x" % did, "D2;1;%s;y;q" % did, "D4;1;%s;q;3" % did, "D4;1;%s;c;x" % did, "D1;1;123456;Alice;1e9;1000",
                "D1;1;123456;" + "A" * 300 + ";100;1000"):
        spoof(odd, "Bob-Forever")
    C.execute("_fire('CHAT_MSG_ADDON', _SECRET, 'D3;1;%s;x', 'PARTY', 'Bob-Forever')" % did)
    C.execute("_fire('CHAT_MSG_ADDON', 'TapCatFvr', _SECRET, 'PARTY', 'Bob-Forever')")
    A.execute("_fire('CHAT_MSG_ADDON', 'TapCatFvr', 'D3;1;%s;x', 'PARTY', _SECRET)" % did)
    A.execute("_fire('CHAT_MSG_ADDON', 'TapCatFvr', 'D3;1;%s;x', _SECRET, 'Bob-Forever')" % did)
    net.pump(1)
    ck(net.st("Alice", "state") == "rolling" and net.st("Alice", "id") == did, "spoofed and odd messages ignored")
    # a stranger outside the group (no hello) can't challenge
    net.ex("Cara", "TapCatForever.DR.duel = nil")
    spoof("D1;1;0a0b0c;Cara;50;1000", "Zed-Forever", to="Cara")
    ck(net.st("Cara", "state") is None, "challenge from an unknown player ignored")
    # Cara challenges Alice mid-duel: busy
    net.pump(4); net.ex("Cara", 'TapCatForever:DeathRollChallenge("Alice", 50, 1000)'); net.pump(1)
    ck(net.st("Cara", "result") == "busy" and net.st("Alice", "id") == did, "busy player answers busy")
    # Cara's rolls don't count, and Cara never saw a D1 addressed to her
    net.sys("Cara rolls 1 (1-1000)")
    ck(net.st("Alice", "n") == 0, "a third player's roll is ignored")
    _play_to_end(net, "Alice", "Bob", [999, 500, 2, 1])
    ra = net.st("Alice", "result")
    ck(settled(net.coins("Alice") - a0, net.coins("Bob") - b0, 100, ra), "three in the group: settled")
    ck(net.coins("Cara") == cara0, "Cara's coins untouched (%d %d)" % (net.coins("Cara"), cara0))

    # --- raid
    net.group(["Alice", "Bob", "Cara"], raid=True)
    a0, c0 = net.coins("Alice"), net.coins("Cara")
    start("Cara", "Alice", 40, 100)
    ck(net.st("Bob", "state") == "over", "Bob not part of the raid duel")
    _play_to_end(net, "Cara", "Alice", [50, 20, 10, 5, 1])
    rc = net.st("Cara", "result")
    ck(settled(net.coins("Cara") - c0, net.coins("Alice") - a0, 40, rc), "raid duel settled")
    net.group(["Alice", "Bob"])
    net.c["Cara"].execute('_group = nil; _fire("GROUP_ROSTER_UPDATE")')
    del net.c["Cara"]

    # --- /reload mid-duel: called off, both stakes back
    a0, b0 = net.coins("Alice"), net.coins("Bob")
    start("Alice", "Bob")
    net.forced = [300]
    r = "Alice" if net.st("Alice", "turn") == "me" else "Bob"
    net.ex(r, "TapCatForever:DeathRollRoll()"); net.pump(1)
    ck(net.coins("Alice") == a0 - 100, "held before the reload")
    db = net.c["Alice"].eval("_dbString()")
    net.c["Alice"] = None; del net.c["Alice"]
    A2 = net.add("Alice", db=db)
    ck(A2.eval("TapCatForever.db.coins") == a0, "stake back at login")
    net.c["Alice"].execute('_group = { party1 = { "Bob", "Forever" } }; _fire("GROUP_ROSTER_UPDATE")')
    net.pump(2)
    ck(net.st("Bob", "result") == "cancel" and net.st("Bob", "reason") == "r", "Bob told about the reload")
    ck(net.coins("Bob") == b0 and net.coins("Alice") == a0, "reload: no coins moved")

    # --- /reload after the 1 was seen, before the other addon agreed: finishes the duel
    a0, b0 = net.coins("Alice"), net.coins("Bob")
    start("Alice", "Bob")
    net.forced = [3, 2, 1]
    net.drop = True          # the "I saw the 1" messages get lost
    for _ in range(3):
        r = "Alice" if net.st("Alice", "turn") == "me" else "Bob"
        if net.st("Alice", "state") != "rolling": break
        net.ex(r, "TapCatForever:DeathRollRoll()"); net.pump(0.5)
    ck(net.st("Alice", "state") == "done" and net.st("Bob", "state") == "done", "both saw the 1")
    db = net.c["Alice"].eval("_dbString()")
    del net.c["Alice"]
    net.add("Alice", db=db)
    ck(net.st("Alice", "state") == "done" and net.st("Alice", "restored"), "waiting again after the reload")
    net.c["Alice"].execute('_group = { party1 = { "Bob", "Forever" } }; _fire("GROUP_ROSTER_UPDATE")')
    net.drop = False
    net.pump(12)
    ra, rb = net.st("Alice", "result"), net.st("Bob", "result")
    ck({ra, rb} == {"win", "lose"}, "finished after the reload (%s %s)" % (ra, rb))
    ck(settled(net.coins("Alice") - a0, net.coins("Bob") - b0, 100, ra), "reload after the 1: matching amounts")
    net.pump(20)
    ck(settled(net.coins("Alice") - a0, net.coins("Bob") - b0, 100, ra), "still settled once")

    # --- results that don't match: called off
    a0, b0 = net.coins("Alice"), net.coins("Bob")
    start("Alice", "Bob")
    net.drop = True
    net.forced = [1]
    r = "Alice" if net.st("Alice", "turn") == "me" else "Bob"
    net.ex(r, "TapCatForever:DeathRollRoll()"); net.pump(0.5)
    did = net.st("Alice", "id")
    other = "Bob" if r == "Alice" else "Alice"
    wrong = "t" if (net.st(r, "role") == "out") else "c"      # names the wrong loser
    net.c[r].globals()._deliver("TapCatFvr", "D4;1;%s;%s;1" % (did, wrong), other + "-Forever", "PARTY")
    net.drop = False
    net.pump(2)
    ck(net.st(r, "result") == "cancel" and net.st(r, "reason") == "m", "mismatch calls it off")
    ck(net.st(other, "result") == "cancel", "the other side too")
    ck(net.coins("Alice") == a0 and net.coins("Bob") == b0, "mismatch: no coins moved")

    # --- the other addon never agrees: the loser pays (it saw its own 1), the winner gets its stake
    # back but nothing more. Coins only ever leave.
    start("Alice", "Bob")
    net.drop = True
    net.forced = [1]
    r = "Alice" if net.st("Alice", "turn") == "me" else "Bob"
    other = "Bob" if r == "Alice" else "Alice"
    net.ex(r, "TapCatForever:DeathRollRoll()"); net.pump(0.5)
    net.pump(95)
    net.drop = False
    net.pump(2)
    ck(net.st(r, "result") == "lose" and net.st(other, "result") == "cancel", "no agreement: %s %s" % (net.st(r, "result"), net.st(other, "result")))
    base = {"Alice": a0, "Bob": b0}
    ck(net.coins(r) - base[r] == -100 and net.coins(other) == base[other], "no agreement: the loser pays, the winner's stake comes back")
    a0, b0 = net.coins("Alice"), net.coins("Bob")

    # --- after the 1 the winner is paid only if the loser pays too (two ways it used to make coins)
    for case in ("leave", "lockdown"):
        a0, b0 = net.coins("Alice"), net.coins("Bob")
        base = {"Alice": a0, "Bob": b0}
        start("Alice", "Bob")
        lo = "Alice" if net.st("Alice", "turn") == "me" else "Bob"
        wi = "Bob" if lo == "Alice" else "Alice"
        net.ex(lo, "TapCatForever:DeathRollRoll()"); net.c[lo].eval("_takeRolls()")
        net.sys("%s rolls 1 (1-1000)" % lo)
        out = net.c[lo].eval("_takeOut()")                      # the loser's "I saw the 1" reaches the winner
        for i in range(1, len(out) + 1): net.c[wi].globals()._deliver(out[i][1], out[i][2], lo + "-Forever", out[i][3])
        net.c[wi].eval("_takeOut()")                            # the winner's answer is lost on the way
        if case == "leave":
            net.ungroup(lo); net.c[wi].execute("_group = nil; _fire('GROUP_ROSTER_UPDATE')")   # the party breaks up
        else:
            net.ex(wi, "_sendResult = 11")                      # the winner's messages are refused from now on
        net.pump(100)
        net.ex(wi, "_sendResult = 0")
        ck(net.st(wi, "result") == "win" and net.st(lo, "result") == "lose", "%s after the 1: %s %s" % (case, net.st(wi, "result"), net.st(lo, "result")))
        dw, dl = net.coins(wi) - base[wi], net.coins(lo) - base[lo]
        ck((dw, dl) == (100, -100), "%s after the 1: no coins made (%d %d)" % (case, dw, dl))
        net.group(["Alice", "Bob"])

    # --- leaving the group mid-duel (before the 1): called off on both sides
    a0, b0 = net.coins("Alice"), net.coins("Bob")
    start("Bob", "Alice")
    net.ungroup("Bob"); net.c["Alice"].execute("_group = {}; _fire('GROUP_ROSTER_UPDATE')"); net.pump(1)
    ck(net.st("Bob", "reason") == "g", "left the group: called off")
    ck(net.st("Alice", "result") == "cancel" and net.st("Alice", "reason") == "g", "the other side sees them gone")
    ck(net.coins("Alice") == a0 and net.coins("Bob") == b0, "left the group: no coins moved")
    net.group(["Alice", "Bob"])

    # --- their first roll arrives before their "accept": it still counts
    early_done = False
    for _ in range(12):
        net.pump(4)
        net.ex("Alice", 'TapCatForever:DeathRollChallenge("Bob", 100, 1000)'); net.pump(1)
        net.ex("Bob", "TapCatForever:DeathRollAnswer(true)")
        held = net.c["Bob"].eval("_takeOut()")
        if net.st("Bob", "turn") != "me":
            for i in range(1, len(held) + 1): net.c["Alice"].globals()._deliver(held[i][1], held[i][2], "Bob-Forever", held[i][3])
            net.pump(1)
            _play_to_end(net, "Alice", "Bob", [5, 1])     # Alice rolls first this time: play it out, try again
            continue
        net.forced = [612]
        net.ex("Bob", "TapCatForever:DeathRollRoll()"); net.c["Bob"].eval("_takeRolls()")
        net.sys("Bob rolls 612 (1-1000)")
        ck(net.st("Alice", "state") == "asking", "the roll came first")
        for i in range(1, len(held) + 1): net.c["Alice"].globals()._deliver(held[i][1], held[i][2], "Bob-Forever", held[i][3])
        ck(net.st("Alice", "cur") == 612 and net.st("Alice", "turn") == "me" and net.st("Bob", "turn") == "opp", "the early roll is played when the accept arrives")
        _play_to_end(net, "Alice", "Bob", [300, 1])
        ck({net.st("Alice", "result"), net.st("Bob", "result")} == {"win", "lose"}, "early roll: finished")
        early_done = True
        break
    ck(early_done, "Bob rolled first in one of 12 tries")

    # --- the challenger reloads while waiting for the answer: the invite is withdrawn
    net.pump(25)
    b0 = net.coins("Bob")
    net.ex("Alice", 'TapCatForever:DeathRollChallenge("Bob", 100, 1000)'); net.pump(1)
    ck(net.st("Bob", "state") == "invited", "invite before the reload")
    db = net.c["Alice"].eval("_dbString()")
    del net.c["Alice"]
    net.add("Alice", db=db)
    net.c["Alice"].execute('_group = { party1 = { "Bob", "Forever" } }; _fire("GROUP_ROSTER_UPDATE")')
    net.pump(3)
    ck(net.st("Bob", "state") == "over" and net.st("Bob", "reason") == "r", "the reload withdraws the invite (%s %s)" % (net.st("Bob", "state"), net.st("Bob", "reason")))
    ck(net.coins("Bob") == b0, "nothing held after the reload")

    # --- a replayed accept gets one "it's off" answer, not one per copy
    net.pump(25)
    net.ex("Alice", 'TapCatForever:DeathRollChallenge("Bob", 100, 1000)'); net.pump(1)
    net.ex("Bob", "TapCatForever:DeathRollAnswer(false)"); net.pump(1)
    did = net.st("Alice", "id")
    net.c["Alice"].eval("_takeOut()")
    for _ in range(30): net.c["Alice"].globals()._deliver("TapCatFvr", "D2;1;%s;y;c" % did, "Bob-Forever", "PARTY")
    ck(len(net.c["Alice"].eval("_takeOut()")) <= 1, "30 replayed accepts get one answer at most")

    # --- no duels where the game hides the roll lines (dungeons, raids, battlegrounds, lockdown)
    net.pump(25)
    net.ex("Alice", '_inInstance = "party"')
    ok, err = net.ex("Alice", 'return TapCatForever:DeathRollChallenge("Bob", 100, 1000)')
    ck(not ok and "dungeons" in err, "no challenge inside an instance: %r" % err)
    net.ex("Alice", '_inInstance = false')
    net.ex("Bob", 'C_ChatInfo.InChatMessagingLockdown = function() return true end')
    net.ex("Alice", 'TapCatForever:DeathRollChallenge("Bob", 100, 1000)'); net.pump(1)
    ck(net.st("Alice", "result") == "busy" and net.st("Bob", "state") in (None, "over"), "a player in chat lockdown answers busy")
    net.ex("Bob", 'C_ChatInfo.InChatMessagingLockdown = nil')

    # --- a refused send is retried
    net.ex("Alice", "_sendResult = 9")
    net.pump(4); net.ex("Alice", 'TapCatForever:DeathRollChallenge("Bob", 50, 1000)'); net.pump(1)
    ck(net.st("Bob", "state") in (None, "over"), "nothing sent while refused")
    net.ex("Alice", "_sendResult = 0"); net.pump(3)
    ck(net.st("Bob", "state") == "invited", "sent once allowed")
    net.ex("Bob", "TapCatForever:DeathRollAnswer(false)"); net.pump(22)

    # --- other languages: German roll text on both clients
    for n in ("Alice", "Bob"): net.ex(n, 'RANDOM_ROLL_RESULT = "%1$s würfelt. Ergebnis: %2$d (%3$d-%4$d)"')
    saved_sys = net.sys
    def de_sys(text):
        import re
        m = re.match(r"^(.+) rolls (\d+) \((\d+)-(\d+)\)$", text)
        saved_sys("%s würfelt. Ergebnis: %s (%s-%s)" % m.groups() if m else text)
    net.sys = de_sys
    a0, b0 = net.coins("Alice"), net.coins("Bob")
    start("Alice", "Bob", 60, 100)
    _play_to_end(net, "Alice", "Bob", [40, 1])
    ra = net.st("Alice", "result")
    ck(settled(net.coins("Alice") - a0, net.coins("Bob") - b0, 60, ra), "German roll text")
    net.sys = saved_sys
    msgs = len([1 for l in net.log if l[1][:1] == "D"])
    print("death roll duel section (%d clients, %d duel messages: challenge, accept, decline, timeouts, withdraw, turn order, "
          "stray rolls, settle once, not enough TapCoins, busy, spoofed and odd messages, raid, reload, mismatch, "
          "lost messages, left the group, refused sends, German, a turn that runs out loses, no coins made after the 1 "
          "(leaving the group, refused sends), an early first roll, a reload while asking, no duels in instances): all checks passed" % (3, msgs))

# ---------------------------------------------------------------------------- scene
def _scene(seed, load_addon):
    lua = _client(load_addon, "Scenecat", seed)
    lua.execute('''
      _textures = {}
      local T = TapCatForever
      T.db.coins = 4000
      local box = CreateFrame("Frame", nil, UIParent)
      _drRefresh = T.UI.CasinoDeathRoll(box, nil)
    ''')
    lua.execute("_drRefresh()")
    # a whole solo game through the scene's button
    lua.execute('''
      local T = TapCatForever
      local guard = 0
      assert(T:DeathRollSoloStart(100, 100))
      while select(2, T:DeathRollSolo()) and guard < 400 do
        guard = guard + 1
        local g = T:DeathRollSolo()
        if g.turn == "me" then T:DeathRollSoloRoll() end
        _update(0.4)
      end
      for i = 1, 40 do _update(0.25) end   -- the end animation runs out
    ''')
    ck(not lua.eval("select(2, TapCatForever:DeathRollSolo())"), "solo game through the scene finished")
    # the Casino tab opens on the Death roll view (the prompt's Accept does this)
    lua.execute("TapCatForever.DR.OpenView()")
    if lua.eval("TapCatForever.casinoView ~= nil"):
        ck(lua.eval("TapCatForever.casinoView.view") == "deathroll", "Casino tab opens on the Death roll view")
        ck(lua.eval("TapCatForever.window.tab == TapCatForever.window.TAB_CASINO"), "Casino tab selected")
        lua.execute("for i = 1, 8 do _update(0.25) end; TapCatForever.window:Refresh()")
    # every duel state and result reads as plain text in the scene
    texts = lua.execute('''
      local T, DR = TapCatForever, TapCatForever.DR
      local v = DR.views[1]
      local out = {}
      local function snap() v:Refresh(true); out[#out + 1] = tostring(v.status:GetText()) .. " | " .. tostring(v.action:GetText()) end
      local base = { id = "abcdef", opp = "Bob", oppBase = "bob", bet = 100, range = 1000, cur = 612, rolls = {}, n = 1,
                     expires = _clock + 30, turnAt = _clock, doneAt = _clock }
      local function duel(fields) local d = {} for k, x in pairs(base) do d[k] = x end for k, x in pairs(fields) do d[k] = x end DR.duel = d; snap() end
      duel({ state = "asking", role = "out" })
      duel({ state = "invited", role = "in" }); out[#out + 1] = v.inv.text:GetText()
      duel({ state = "rolling", role = "out", turn = "me" })
      duel({ state = "rolling", role = "in", turn = "opp" })
      duel({ state = "done", role = "in", loser = "me" })
      for _, r in ipairs({ "win", "lose", "declined", "busy", "toohigh", "expired" }) do
        duel({ state = "over", role = "out", result = r, by = "opp" }); duel({ state = "over", role = "in", result = r, by = "me" })
      end
      duel({ state = "over", role = "out", result = "win", reason = "f", by = "opp" })
      duel({ state = "over", role = "out", result = "lose", reason = "f", by = "me" })
      duel({ state = "over", role = "out", result = "win", opp = "Thrallbeard-ArgentDawn", oppBase = "thrallbeard" })
      for k in pairs(DR.REASONS) do
        duel({ state = "over", role = "out", result = "cancel", reason = k, by = "opp" })
        duel({ state = "over", role = "out", result = "cancel", reason = k, by = "me" })
      end
      DR.duel = nil
      v:SetMode("friend"); snap()
      v:SetMode("house"); snap()
      return out''')
    texts = list(texts.values())
    for t in texts:
        ck("!" not in t and "%s" not in t and "%d" not in t and "nil" not in t, "scene text: %r" % t)
    ck(any("You win" in t for t in texts) and any("Your turn" in t for t in texts) and any("No TapCoins moved" in t for t in texts), "scene texts")
    ck(any("ran out of time" in t for t in texts), "forfeit texts")
    ck(not any("ArgentDawn" in t for t in texts), "the scene shows names without their realm")
    # every texture the scene uses exists
    art = os.path.join(ROOT, "Art")
    used = [p for p in lua.eval("(function() local t = {} for p in pairs(_textures) do t[#t + 1] = p end return t end)()").values()]
    casino = [p.split("Art\\", 1)[1] for p in used if "\\casino\\" in p]
    ck(len(casino) >= 9, "scene textures used: %r" % casino)
    missing = [p for p in casino if not os.path.exists(os.path.join(art, p.replace("\\", "/") + ".tga"))]
    ck(not missing, "missing art: %r" % missing)
    # no exclamation marks in the player-facing texts of the two files
    for fn in ("DeathRoll.lua", "UI_DeathRoll.lua"):
        src = open(os.path.join(ROOT, fn), encoding="utf-8").read()
        import re
        for s in re.findall(r'"((?:[^"\\]|\\.)*)"', src):
            ck("!" not in s, "exclamation mark in %s: %r" % (fn, s))
    print("death roll scene section (solo game through the scene, %d textures in Art/casino, plain text): all checks passed" % len(casino))

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import test_harness
    sys.modules["__main__"].LB_CLIENT = test_harness.LB_CLIENT
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
