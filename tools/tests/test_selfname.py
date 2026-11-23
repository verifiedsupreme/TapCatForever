# 1.6.0: the game may not let an addon read its own name (UnitName("player") is a protected value on
# WoW: Forever), and the name it puts on addon messages is "Name-Realm". Each addon learns its own
# name from its own messages coming back (Party.lua: the exact text and the session tag "z=";
# DeathRoll.lua: its "D0" hello with a random id; a "N1" probe on the leaderboard's routes).
# Two (or three) simulated clients whose UnitName("player") is a secret value, every message heard by
# the whole group including its sender (the game echoes your own messages):
#   - the party row shows only friends' cats, never your own
#   - a death roll duel end to end (challenge names the target as "Name-Realm", your own /roll
#     lines are yours), and rock paper scissors end to end
#   - the Casino's friend line: "Ready to play", "Checking their TapCatForever...", and "didn't
#     answer (they need the newest version)" for a friend whose addon is older (no D0 answer)
#   - a challenge while your name isn't known yet is refused with a plain line, and works once your
#     hello came back; a /roll by someone else in the group is never taken for yours
#   - a party message you sent before a /reload (old tag) leaves the row as soon as your name is known
#   - old stand-in leaderboard rows ("You-<realm>") are dropped and never taken in
#   - a raid of 10: one roster change costs each addon one hello and at most one answer
#   - a party expedition invite, accept and start (names in the start match the learned names)
#   - the leaderboard: both opted in, in a party, see each other's rows under their real names
#     (nothing is shared under a stand-in name while the name isn't known)
# Run on its own:  python3 tools/tests/test_selfname.py [seed]
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
import test_deathroll as TD

EXTRA = r'''
_srv = 1800000000
function GetServerTime() return _srv end
function GetNormalizedRealmName() return "Forever" end
_chanId, _joins = 0, 0
function JoinTemporaryChannel() _joins = _joins + 1 end
function LeaveChannelByName() _chanId = 0 end
function GetChannelName() return _chanId end
-- the protected own name
local realUnitName = UnitName
function UnitName(u)
  if u == "player" then return _SECRET end
  return realUnitName(u)
end
function UnitFullName(u) if u == "player" then return _SECRET, _SECRET end end
'''

def two(r): return r if isinstance(r, tuple) else (r, None)

def ck(c, m):
    if not c: raise AssertionError("own name: " + m)

class Net(TD.Net):
    """TD.Net with secret own names, a realm clock, and `old` clients that drop casino messages
    (an addon before 1.6.0 answers no hello)"""
    def __init__(self, *a):
        super().__init__(*a)
        self.old = set()
        self.srv = 1800000000
    def add(self, name, coins=2000, cls=None, level=None, old=False):
        lua = super().add(name, coins, extra=EXTRA)
        if cls: lua.execute('TapCatForever:SetClass("%s")' % cls)
        if level: lua.execute('TapCatForever.db.classData.%s.level = %d' % (cls, level))
        if old: self.old.add(name)
        return lua
    def deliver(self):
        moved = True
        while moved:
            moved = False
            for name, lua in list(self.c.items()):
                out = lua.eval("_takeOut()")
                for i in range(1, len(out) + 1):
                    p, msg, ch, target = out[i][1], out[i][2], out[i][3], out[i][4]
                    moved = True
                    self.log.append((name, msg, ch))
                    ck(p == "TapCatFvr" and len(msg) <= 255, "prefix and length")
                    if ch not in ("PARTY", "RAID", "INSTANCE_CHAT"): continue
                    for other, olua in self.c.items():   # the whole group hears it, the sender too (echo)
                        if not (self.grouped(other) and self.grouped(name)): continue
                        # an addon before 1.6.0: no casino hello, no challenge from it either
                        if other in self.old and msg[:1] in ("D", "R"): continue
                        if name in self.old and msg[:1] in ("D", "R"): continue
                        olua.globals()._deliver(p, msg, name + "-Forever", ch)
                rolls = lua.eval("_takeRolls()")
                for i in range(1, len(rolls) + 1):
                    lo, hi = rolls[i][1], rolls[i][2]
                    v = self.forced.pop(0) if self.forced else self.rnd.randint(lo, hi)
                    self.sys("%s rolls %d (%d-%d)" % (name, max(lo, min(hi, v)), lo, hi))
                    moved = True
    def pump(self, seconds=1, dt=0.5):
        for _ in range(int(seconds / dt)):
            self.srv += dt
            for lua in self.c.values(): lua.execute("_srv = %d; _update(%f)" % (int(self.srv), dt))
            self.deliver()

def check(seed, load_addon):
    import random
    rnd = random.Random(seed)
    net = Net(load_addon, seed, rnd)
    A, B = net.add("Alice", cls="MAGE", level=20), net.add("Bob", cls="WARRIOR", level=20)
    ck(A.eval("TapCatForever.SelfName() == nil"), "no name known before any message")
    net.group(["Alice", "Bob"])

    # --- learned names and the party row
    for me, other in (("Alice", "Bob"), ("Bob", "Alice")):
        L = net.c[me]
        ck(L.eval("TapCatForever.SelfSender") == me + "-Forever", "%s learned the name the game uses: %s" % (me, L.eval("TapCatForever.SelfSender")))
        ck(L.eval("TapCatForever.SelfName()") == me, "%s: SelfName" % me)
        ck(L.eval("TapCatForever:PartyCount()") == 1, "%s's party row has one cat" % me)
        ck(L.eval("TapCatForever:PartyMembers()[1].name") == other, "%s's row shows %s, not their own cat" % (me, other))
        ck(L.eval("TapCatForever.PartyIsMe(%r)" % (me + "-Forever")) and not L.eval("TapCatForever.PartyIsMe(%r)" % (other + "-Forever")), "%s: PartyIsMe" % me)
        ck(L.eval("(TapCatForever.DR.FriendStatus(%r))" % other) == "Ready to play", "%s: friend line says ready" % me)
    # a friend with the very same look (same class, level and cosmetics) is still a friend: the tag differs
    pa = A.eval("TapCatForever:PartyPayload()")
    ck(";z=" in pa or ",z=" in pa, "the session tag is in the party message")
    tagA = pa.rsplit("z=", 1)[1]
    ck(tagA != B.eval("TapCatForever:PartyPayload()").rsplit("z=", 1)[1], "each client has its own tag")

    # --- death roll: the challenge names Bob as the game sends it, Bob's addon matches it
    a0, b0 = net.coins("Alice"), net.coins("Bob")
    ok, err = two(A.execute('return TapCatForever:DeathRollChallenge("Bob", 100, 1000)'))
    ck(ok, "challenge sent: %r" % (err,))
    net.pump(1)
    d1 = [m for (n, m, ch) in net.log if m.startswith("D1;")][-1]
    ck(";Bob-Forever;100;1000" in d1, "the target is Bob's sender name: %s" % d1)
    ck(net.st("Bob", "state") == "invited", "Bob's addon took the challenge as his")
    ck(B.eval("(TapCatForever:DeathRollAnswer(true))"), "Bob accepts")
    net.pump(1)
    ck(net.st("Alice", "state") == "rolling" and net.st("Bob", "state") == "rolling", "the duel runs")
    TD._play_to_end(net, "Alice", "Bob", [700, 300, 40, 1])
    ra, rb = net.st("Alice", "result"), net.st("Bob", "result")
    ck({ra, rb} == {"win", "lose"}, "one wins, one loses (%s %s)" % (ra, rb))
    ck(TD.settled(net.coins("Alice") - a0, net.coins("Bob") - b0, 100, ra), "both settle the same amount")

    # --- a challenge before your name is known: a plain "try again", then it works once your hello is back
    C = net.add("Cara")
    net.group(["Alice", "Bob", "Cara"])
    ck(C.eval("TapCatForever.SelfSender") == "Cara-Forever", "Cara learned her name too")
    # Cara's addon forgets it (as if her own messages hadn't come back yet)
    C.execute("TapCatForever.SelfSender, TapCatForever.SelfBase = nil, nil")
    net.pump(4)
    ok, err = two(C.execute('return TapCatForever:DeathRollChallenge("Alice", 30, 100)'))
    ck(not ok and "still getting your name" in err and "!" not in err, "no challenge before the name is known: %r" % (err,))
    ck(not [m for (n, m, ch) in net.log[-20:] if n == "Cara" and m.startswith("D1;")], "no D1 went out")
    net.pump(2)
    ck(C.eval("TapCatForever.SelfBase") == "cara", "her hello came back and taught her the name again")
    a0, c0 = net.coins("Alice"), net.coins("Cara")
    ok, err = two(C.execute('return TapCatForever:DeathRollChallenge("Alice", 30, 100)'))
    ck(ok, "Cara's challenge: %r" % (err,))
    net.pump(1)
    ck(A.eval("(TapCatForever:DeathRollAnswer(true))"), "Alice accepts Cara's challenge")
    net.pump(1)
    # Bob (in the group, not in the duel) rolls the same range just after the roller pressed Roll,
    # even while the roller's name is unknown: never counted, and nobody learns "bob" as their name
    roller = "Cara" if net.st("Cara", "turn") == "me" else "Alice"
    R = net.c[roller]
    R.execute("TapCatForever.SelfSender, TapCatForever.SelfBase = nil, nil")
    R.execute("local d = TapCatForever.DR.duel; d.rolledAt, d.rolledHi = GetTime(), d.cur")
    net.sys("Bob rolls 7 (1-100)")
    ck(net.st("Cara", "n") == 0 and net.st("Alice", "n") == 0, "Bob's roll is no part of the duel")
    ck(R.eval("TapCatForever.SelfBase") is None, "%s didn't take Bob's name for theirs" % roller)
    ck(not R.eval("TapCatForever.PartyIsMe('Bob-Forever')"), "Bob is still Bob for %s" % roller)
    R.execute("TapCatForever.DR.duel.rolledAt = nil; TapCatForever.LearnSelf('%s-Forever')" % roller)
    TD._play_to_end(net, "Cara", "Alice", [60, 30, 9, 1])
    rc, ra = net.st("Cara", "result"), net.st("Alice", "result")
    ck({rc, ra} == {"win", "lose"} and TD.settled(net.coins("Cara") - c0, net.coins("Alice") - a0, 30, rc), "Cara's duel settles (%s %s)" % (rc, ra))

    # --- rock paper scissors end to end
    net.pump(4)
    a0, b0 = net.coins("Alice"), net.coins("Bob")
    ok, err = two(B.execute('return TapCatForever:RPSChallenge("Alice", 50)'))
    ck(ok, "rps challenge sent: %r" % (err,))
    net.pump(1)
    r1 = [m for (n, m, ch) in net.log if m.startswith("R1;")][-1]
    ck(";Alice-Forever;50" in r1, "rps target is Alice's sender name: %s" % r1)
    ck(A.eval("(TapCatForever:RPSAnswer(true))"), "Alice accepts the game")
    net.pump(1)
    A.execute('TapCatForever:RPSPick("rock")'); B.execute('TapCatForever:RPSPick("scissors")'); net.pump(3)
    ra = A.eval("TapCatForever.RPS.duel.result"); rb = B.eval("TapCatForever.RPS.duel.result")
    ck((ra, rb) == ("win", "lose"), "rock beats scissors on both sides (%s %s)" % (ra, rb))
    ck(net.coins("Alice") - a0 == 50 and net.coins("Bob") - b0 == -50, "rps settled")

    # --- party expedition: invite, accept, start; the start lists the learned names
    net.pump(4)
    ok, err = two(A.execute('return TapCatForever:GroupExpInvite("dm", 1, 1, { "MAGE" })'))
    ck(ok, "party expedition invite: %r" % (err,))
    net.pump(1)
    ck(B.eval("TapCatForever.GX.inv and TapCatForever.GX.inv.state") == "invited", "Bob is invited")
    ck(B.eval("(TapCatForever:GroupExpAnswer(true))"), "Bob accepts the expedition")
    net.pump(1)
    ck(C.eval("(TapCatForever:GroupExpAnswer(false))"), "Cara declines")
    net.pump(3)
    g3 = [m for (n, m, ch) in net.log if m.startswith("G3;")]
    ck(g3 and "Alice:" in g3[-1] and "Bob:" in g3[-1] and "?" not in g3[-1], "the start names both players: %s" % (g3[-1] if g3 else None))
    for n in ("Alice", "Bob"):
        ck(net.c[n].eval("TapCatForever:GroupExp() ~= nil"), "%s has the expedition" % n)
    ck(C.eval("TapCatForever:GroupExp() == nil"), "Cara stays home")

    # --- the leaderboard: both opted in, in a party, each sees the other under the real name
    for n in ("Alice", "Bob"):
        net.c[n].execute("TapCatForever.db.ui.shareDev = true; TapCatForever:DevShareChanged()")
    net.pump(80)
    lb = [m for (n, m, ch) in net.log if m.startswith("L1;")]
    ck(lb, "summaries went out")
    ck(all(m.split(";")[1] in ("Alice-Forever", "Bob-Forever") for m in lb), "only real names are shared: %r" % sorted(set(m.split(";")[1] for m in lb)))
    rows = lambda L: L.eval('(function() local t = {} for _, r in ipairs(TapCatForever:LeaderboardSection("taps", "taps")) do t[#t + 1] = r.n .. (r.self and "*" or "") end table.sort(t) return table.concat(t, ",") end)()')
    ck(rows(A) == "Alice-Forever*,Bob-Forever", "Alice's board: %s" % rows(A))
    ck(rows(B) == "Alice-Forever,Bob-Forever*", "Bob's board: %s" % rows(B))

    # --- a party message Alice sent before a /reload comes back with the old session's tag while her
    # new session doesn't know her name yet: her cat shows for a moment, and goes as soon as she knows
    A.execute("TapCatForever.SelfSender, TapCatForever.SelfBase = nil, nil")
    mine = [m for (n, m, ch) in net.log if n == "Alice" and m[:3] in ("H1;", "U1;")][-1]
    oldtag = "fffff" if not mine.endswith("z=fffff") else "eeeee"
    stale = mine.rsplit("z=", 1)[0] + "z=" + oldtag
    before = A.eval("TapCatForever:PartyCount()")
    A.globals()._deliver("TapCatFvr", stale, "Alice-Forever", "PARTY")
    ck(A.eval("TapCatForever:PartyCount()") == before + 1, "the stale message put her own cat up (the case being fixed)")
    A.execute("TapCatForever.DR.SayHello(true)")
    net.pump(1)
    ck(A.eval("TapCatForever.SelfBase") == "alice", "Alice's hello taught her name")
    rowNames = lambda: A.eval('(function() local t = {} for _, m in ipairs(TapCatForever:PartyMembers()) do t[#t + 1] = m.name end return table.concat(t, ",") end)()')
    ck(A.eval("TapCatForever:PartyCount()") == before and "Alice" not in rowNames(),
       "her own cat left the row as soon as the name was known: %s" % rowNames())
    A.globals()._deliver("TapCatFvr", stale, "Alice-Forever", "PARTY")
    ck(A.eval("TapCatForever:PartyCount()") == before, "and doesn't come back")

    # --- stand-in leaderboard rows from older versions ("You-<realm>", "Unknown-<realm>")
    A.execute("""
      local b = TapCatForever.LeaderboardBoard(true)
      local t = TapCatForever.LeaderboardServerNow()
      for _, n in ipairs({ "You-Forever", "Unknown-Forever" }) do
        b.e[n:lower()] = { n = n, c = "MAGE", l = 10, t = 5000, a = 0, z = 0, v = "1.5.3", ts = t - 60 }
      end
      TapCatForever.LeaderboardTest.prune(b, t)
    """)
    ck(A.eval("TapCatForever.LeaderboardBoard(true).e['you-forever'] == nil and TapCatForever.LeaderboardBoard(true).e['unknown-forever'] == nil"),
       "stand-in rows are dropped from the saved board")
    ck(rows(A) == "Alice-Forever*,Bob-Forever", "the board is just the two players: %s" % rows(A))
    ts = A.eval("TapCatForever.LeaderboardServerNow()")
    A.globals()._deliver("TapCatFvr", "L1;You-Forever;MAGE;10;5000;0;0;1.5.3;%d" % (ts - 30), "Bob-Forever", "PARTY")
    ck(A.eval("TapCatForever.LeaderboardBoard(true).e['you-forever'] == nil"), "a stand-in row passed on is not taken in")
    ck(A.eval("select(2, TapCatForever.LeaderboardMerge(TapCatForever.LeaderboardBoard(true), { n = 'You-Forever', c = 'MAGE', l = 1, t = 0, a = 0, z = 0, v = '1', ts = %d }, %d))" % (ts, ts)) == "name",
       "merge refuses a stand-in name")
    for n in ("Alice", "Bob"):
        net.c[n].execute("TapCatForever.db.ui.shareDev = false; TapCatForever:DevShareChanged()")
    net.pump(4)

    # --- a raid of 10: one roster change costs each addon one hello and at most one answer, and
    # every addon still learns that every other one can play
    net3 = Net(load_addon, seed + 2, rnd)
    names = ["P%s" % ch for ch in "abcdefghij"]
    for n in names: net3.add(n)
    net3.group(names, raid=True)
    net3.pump(30)
    start = len(net3.log)
    for n in names: net3.c[n].execute('_fire("GROUP_ROSTER_UPDATE")')
    net3.pump(10)
    d0 = [(n, m) for (n, m, ch) in net3.log[start:] if m.startswith("D0;")]
    per = {n: len([1 for (x, m) in d0 if x == n]) for n in names}
    ck(max(per.values()) <= 2, "at most a hello and an answer per addon: %r" % per)
    ck(len(d0) <= 2 * len(names), "D0 messages for one roster change: %d" % len(d0))
    for n in names:
        L = net3.c[n]
        ck(L.eval("TapCatForever.SelfBase") == n.lower(), "%s learned its name" % n)
        for o in names:
            if o != n: ck(L.eval("TapCatForever:CasinoCanPlay(%r)" % (o + "-Forever")) is True, "%s knows %s can play" % (n, o))
    # a newcomer's hello right after our last answer still gets one (a little later), so they see us
    net3.c["Pa"].execute("TapCatForever.DR.SayHello(true)")
    net3.pump(6)
    oks = [n for (n, m, ch) in net3.log[-60:] if m.startswith("D0;") and m.endswith(";ok")]
    ck(len(oks) >= len(names) - 1, "everyone answered the new hello: %r" % oks)
    # a refused hello is never queued: nothing of it goes out later
    L = net3.c["Pb"]
    L.execute("_sendResult = 9")
    L.execute("TapCatForever.DR.SayHello(true)")
    L.execute("_sendResult = 0")
    start = len(net3.log)
    net3.pump(10)
    ck(not [m for (n, m, ch) in net3.log[start:] if n == "Pb" and m.startswith("D0;") and m.endswith(";hi")], "a refused hello is dropped, not sent later")

    # --- a friend on an older version: the line says so instead of waiting for nothing
    net2 = Net(load_addon, seed + 1, rnd)
    X, Y = net2.add("Xan"), net2.add("Yorr", old=True)
    net2.group(["Xan", "Yorr"])
    ck(X.eval("TapCatForever:PartyCount()") == 1, "the old friend's cat shows (party cats work on older versions)")
    st = X.eval("(TapCatForever.DR.FriendStatus('Yorr'))")
    ck(st == "Checking their TapCatForever...", "first: checking (%s)" % st)
    ok, err = two(X.execute('return TapCatForever:DeathRollChallenge("Yorr", 50, 1000)'))
    ck(not ok and "Checking" in err and "!" not in err, "a challenge waits for the check: %r" % err)
    net2.pump(8)
    st = X.eval("(TapCatForever.DR.FriendStatus('Yorr'))")
    ck(st == "Their TapCatForever didn't answer (they need the newest version)", "then: didn't answer (%s)" % st)
    ok, err = two(X.execute('return TapCatForever:DeathRollChallenge("Yorr", 50, 1000)'))
    ck(not ok and "need the newest TapCatForever" in err and "!" not in err, "the challenge explains it: %r" % err)
    ok, err = two(X.execute('return TapCatForever:RPSChallenge("Yorr", 50)'))
    ck(not ok and "need the newest TapCatForever" in err, "rock paper scissors too: %r" % err)
    # the line in the Casino's friend view
    X.execute("_drRefresh = TapCatForever.UI.CasinoDeathRoll(CreateFrame('Frame', nil, UIParent), nil)")
    X.execute("local v = TapCatForever.DR.views[#TapCatForever.DR.views]; v:SetMode('friend'); v:Refresh(true)")
    line = X.eval("TapCatForever.DR.views[#TapCatForever.DR.views].friendState:GetText()")
    ck(line and "didn't answer (they need the newest version)" in line, "the friend line in the Casino: %r" % line)
    print("own name section (secret UnitName on every client, senders as Name-Realm: names learned from echoed "
          "messages, party row without your own cat, a death roll and rock paper scissors end to end, a party "
          "expedition start, leaderboard rows under real names, the Casino's friend line for ready, checking and "
          "an older version, no challenge or roll guessing before the name is known, an old-session party message, "
          "stand-in leaderboard rows, hellos in a raid of 10): all checks passed")

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import test_harness
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
