# 1.6.1: who is still in the group during a duel. On WoW: Forever the roster's names (UnitName on
# party1..4 / raid1..40) can come back as protected values, "Unknown", nil or in another form, so
# 1.6.0's death rolls and rock paper scissors games ended with "<friend> is no longer in your group."
# the moment they started. Now the addon's own knowledge decides (DeathRoll.lua OppPresent, shared
# with RPS.lua): the opponent is present while Party.lua lists them; once Party.lua has them missing
# from a roster it could read in full, or forgot them, they get a grace period counted from their
# last message or roll; UnitName never says "gone" on its own. Two simulated clients with secret own
# names (test_selfname.Net, the game echoes your messages back) whose roster names come back as
#   (a) a protected value, (b) "Unknown", (c) "Bob-Forever" in one string, (d) nil, and
#   (e) a protected value on a client without issecretvalue (it then just isn't a string):
#   a death roll and a rock paper scissors game each run to the end and settle, with roster events
#   mid-game and more than the grace period of play time
# and, on readable rosters:
#   - a roster blink (one roster read without the friend, the next with them) never ends a duel
#   - a message from the friend restarts the grace period
#   - the friend really gone (roster complete without them, Party.lua forgets them 3 s later, no
#     message): the duel still runs through the grace period, then it is called off with "g" and
#     the stake comes back; the same for rock paper scissors
#   - offline: a unit whose plain-string name is the friend's with UnitIsConnected false ends the
#     duel after the grace period (a loading screen reads as offline for a second or two: a blink
#     changes nothing); with an unreadable name it doesn't
#   - the roster can only confirm the friend: a stale "missing" flag (one roster read without them,
#     no roster event after they are back) never ends a duel while UnitName reads their name
#   - a protected IsInGroup counts as grouped: the duel goes on
# Run on its own:  python3 tools/tests/test_duel_presence.py [seed]
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
import test_deathroll as TD
import test_selfname as TS

def two(r): return r if isinstance(r, tuple) else (r, None)

def ck(c, m):
    if not c: raise AssertionError("duel presence: " + m)

# how UnitName answers for group units (g = { name, realm } from the mock's _group)
NAME_CASES = [
    ("secret", "_SECRET"),
    ("unknown", '"Unknown"'),
    ("realm", 'g[1] .. "-Forever"'),
    ("nil", "nil"),
    ("readable", "g[1], g[2]"),
]

def set_names(lua, mode):
    lua.execute('''
      function UnitName(u)
        if u == "player" then return _SECRET end
        if type(u) == "string" and (u:match("^party%%d") or u:match("^raid%%d")) then
          local g = _group and _group[u]
          if not g then return nil end
          return %s
        end
        return _charName
      end''' % mode)

def rst(net, name, k): return net.c[name].eval("(function() local d = TapCatForever.RPS.duel; return d and d[%r] end)()" % k)
def grace(net): return int(net.c["Alice"].eval("TapCatForever.DR.OPP_GONE_GRACE"))

def roster_events(net, names=("Alice", "Bob")):
    for n in names: net.c[n].execute('_fire("GROUP_ROSTER_UPDATE")')

def start_dr(net, a, b, bet=100):
    net.pump(4)
    ok, err = two(net.ex(a, 'return TapCatForever:DeathRollChallenge(%r, %d, 1000)' % (b, bet)))
    ck(ok, "%s challenges %s: %r" % (a, b, err))
    net.pump(1)
    ck(net.st(b, "state") == "invited", "%s got the challenge" % b)
    ok, err = two(net.ex(b, "return TapCatForever:DeathRollAnswer(true)"))
    ck(ok, "%s accepts: %r" % (b, err))
    net.pump(1)
    ck(net.st(a, "state") == "rolling" and net.st(b, "state") == "rolling", "the duel runs (%s %s)" % (net.st(a, "state"), net.st(b, "state")))

def dr_to_end(net, a, b, bet, label):
    a0, b0 = net.coins(a) + bet, net.coins(b) + bet   # the stakes are held already
    # roster events mid-duel, and more play time than the grace period: nothing ends it
    roster_events(net)
    net.pump(grace(net) + 2)
    roster_events(net)
    net.pump(1)
    ck(net.st(a, "state") == "rolling" and net.st(b, "state") == "rolling",
       "%s: still rolling after roster events and the grace period (%s/%s %s/%s)" % (label, net.st(a, "state"), net.st(a, "reason"), net.st(b, "state"), net.st(b, "reason")))
    TD._play_to_end(net, a, b, [700, 300, 40, 1])
    ra, rb = net.st(a, "result"), net.st(b, "result")
    ck({ra, rb} == {"win", "lose"}, "%s: one wins, one loses (%s %s)" % (label, ra, rb))
    ck(TD.settled(net.coins(a) - a0, net.coins(b) - b0, bet, ra), "%s: both settle (%d %d)" % (label, net.coins(a) - a0, net.coins(b) - b0))
    ck(net.st(a, "reason") != "g" and net.st(b, "reason") != "g", "%s: nobody was declared gone" % label)

def start_rps(net, a, b, bet=50):
    net.pump(4)
    ok, err = two(net.ex(a, 'return TapCatForever:RPSChallenge(%r, %d)' % (b, bet)))
    ck(ok, "%s challenges %s to rock paper scissors: %r" % (a, b, err))
    net.pump(1)
    ck(rst(net, b, "state") == "invited", "%s got the rps challenge" % b)
    ok, err = two(net.ex(b, "return TapCatForever:RPSAnswer(true)"))
    ck(ok, "%s accepts rps: %r" % (b, err))
    net.pump(1)
    ck(rst(net, a, "state") == "picking" and rst(net, b, "state") == "picking", "both picking")

def rps_to_end(net, a, b, bet, label):
    a0, b0 = net.coins(a) + bet, net.coins(b) + bet
    roster_events(net)
    net.pump(grace(net) + 2)
    roster_events(net)
    net.pump(1)
    ck(rst(net, a, "state") == "picking" and rst(net, b, "state") == "picking",
       "%s: still picking after roster events and the grace period (%s/%s %s/%s)" % (label, rst(net, a, "state"), rst(net, a, "reason"), rst(net, b, "state"), rst(net, b, "reason")))
    net.ex(a, 'TapCatForever:RPSPick("rock")'); net.pump(1)
    net.ex(b, 'TapCatForever:RPSPick("scissors")'); net.pump(3)
    ra, rb = rst(net, a, "result"), rst(net, b, "result")
    ck((ra, rb) == ("win", "lose"), "%s: rock beats scissors (%s %s)" % (label, ra, rb))
    ck(net.coins(a) - a0 == bet and net.coins(b) - b0 == -bet, "%s: rps settled (%d %d)" % (label, net.coins(a) - a0, net.coins(b) - b0))

def check(seed, load_addon):
    import random
    rnd = random.Random(seed)
    net = TS.Net(load_addon, seed, rnd)
    A, B = net.add("Alice"), net.add("Bob")
    net.group(["Alice", "Bob"])
    G = grace(net)
    ck(G >= 5, "a grace period of a few seconds (%d)" % G)

    # --- (a) to (d): unreadable or odd roster names, a death roll and an rps game each
    for label, mode in NAME_CASES[:4]:
        for L in (A, B): set_names(L, mode)
        roster_events(net); net.pump(4); roster_events(net); net.pump(1)
        ck(A.eval("TapCatForever:PartyCount()") == 1 and B.eval("TapCatForever:PartyCount()") == 1, "%s: the party row keeps the friend" % label)
        ck(A.eval("TapCatForever.DR.OppPresent({ opp = 'Bob', oppBase = 'bob' })"), "%s: present by Party.lua's knowledge" % label)
        start_dr(net, "Alice", "Bob")
        dr_to_end(net, "Alice", "Bob", 100, "death roll, roster names " + label)
        start_rps(net, "Bob", "Alice")
        rps_to_end(net, "Bob", "Alice", 50, "rps, roster names " + label)

    # --- (e) a protected value on a client without issecretvalue: it just isn't a string
    for L in (A, B):
        set_names(L, "_SECRET")
        L.execute("_issv = issecretvalue; issecretvalue = nil")
    roster_events(net); net.pump(4); roster_events(net); net.pump(1)
    ck(A.eval("TapCatForever:PartyCount()") == 1, "no issecretvalue: the party row keeps the friend")
    start_dr(net, "Alice", "Bob")
    dr_to_end(net, "Alice", "Bob", 100, "death roll, no issecretvalue")
    start_rps(net, "Alice", "Bob")
    rps_to_end(net, "Alice", "Bob", 50, "rps, no issecretvalue")
    for L in (A, B): L.execute("issecretvalue = _issv")

    # --- readable roster from here on
    for L in (A, B): set_names(L, NAME_CASES[4][1])
    roster_events(net); net.pump(1)

    # a roster blink: one read without Bob, the next (within 3 s) with him: the duel goes on
    start_dr(net, "Alice", "Bob")
    A.execute('_keep = _group; _group = {}; _fire("GROUP_ROSTER_UPDATE")')
    net.pump(1)
    ck(A.eval("TapCatForever:PartyMembers()[1].missing ~= nil"), "Party.lua has Bob missing after one roster read")
    ck(net.st("Alice", "state") == "rolling", "a roster read without Bob doesn't end the duel")
    A.execute('_group = _keep; _fire("GROUP_ROSTER_UPDATE")')
    net.pump(G + 2)
    ck(A.eval("TapCatForever:PartyMembers()[1].missing == nil"), "the next read cleared it")
    ck(net.st("Alice", "state") == "rolling", "the blink changed nothing")
    dr_to_end(net, "Alice", "Bob", 100, "death roll after a roster blink")

    # a message from Bob while Alice's roster has him missing restarts the grace period
    start_dr(net, "Bob", "Alice")
    t0 = A.eval("GetTime()")
    A.execute('_keep = _group; _group = {}; _fire("GROUP_ROSTER_UPDATE")')
    net.pump(G - 3)
    ck(net.st("Alice", "state") == "rolling", "still in the grace period")
    B.execute("TapCatForever.DR.SayHello(true)"); net.pump(1)     # a hello of Bob's reaches Alice
    ck(A.eval("TapCatForever.DR.duel.oppHeardAt") > t0, "Alice heard from Bob")
    net.pump(4)
    ck(net.st("Alice", "state") == "rolling", "his message restarted the grace period (%s %s)" % (net.st("Alice", "state"), net.st("Alice", "reason")))
    A.execute('_group = _keep; _fire("GROUP_ROSTER_UPDATE")')
    net.pump(1)
    dr_to_end(net, "Bob", "Alice", 100, "death roll after a message in the grace period")

    # Bob really leaves: his addon calls his side off at once; Alice's roster is complete without
    # him, Party.lua forgets him on the second read 3 s later, nothing arrives from him: her duel
    # runs through the grace period, then "g", and her stake comes back
    a0 = net.coins("Alice")
    start_dr(net, "Alice", "Bob")
    ck(net.coins("Alice") == a0 - 100, "stake held")
    net.ungroup("Bob")
    ck(net.st("Bob", "result") == "cancel" and net.st("Bob", "reason") == "g", "Bob left: his side is called off at once")
    A.execute('_group = {}; _fire("GROUP_ROSTER_UPDATE")')
    net.pump(3.5)
    A.execute('_fire("GROUP_ROSTER_UPDATE")')
    ck(A.eval("TapCatForever:PartyCount()") == 0, "Party.lua forgot Bob")
    ck(net.st("Alice", "state") == "rolling", "the grace period is still running")
    net.pump(G + 1)
    ck(net.st("Alice", "result") == "cancel" and net.st("Alice", "reason") == "g" and net.st("Alice", "by") == "opp",
       "then the duel is called off, Bob gone (%s %s)" % (net.st("Alice", "result"), net.st("Alice", "reason")))
    ck(net.coins("Alice") == a0, "the stake came back")
    msg = A.eval("string.format(TapCatForever.DR.REASONS.g, 'Bob')")
    ck(msg == "Bob is no longer in your group.", "the line: %r" % msg)
    net.group(["Alice", "Bob"])

    # the same for rock paper scissors
    a0 = net.coins("Alice")
    start_rps(net, "Bob", "Alice")
    net.ungroup("Bob")
    ck(rst(net, "Bob", "reason") == "g", "rps: Bob's side called off at once")
    A.execute('_group = {}; _fire("GROUP_ROSTER_UPDATE")')
    net.pump(3.5)
    A.execute('_fire("GROUP_ROSTER_UPDATE")')
    ck(rst(net, "Alice", "state") == "picking", "rps: the grace period is still running")
    net.pump(G + 1)
    ck(rst(net, "Alice", "result") == "cancel" and rst(net, "Alice", "reason") == "g", "rps: then called off, Bob gone (%s %s)" % (rst(net, "Alice", "result"), rst(net, "Alice", "reason")))
    ck(net.coins("Alice") == a0, "rps: the bet came back")
    net.group(["Alice", "Bob"])

    # offline: only a unit whose plain-string name is Bob's and UnitIsConnected == false, and only
    # after the grace period (a loading screen reads as offline for a moment)
    a0 = net.coins("Alice")
    start_dr(net, "Alice", "Bob")
    set_names(A, "_SECRET")
    A.execute("function UnitIsConnected(u) return u ~= 'party1' end")
    net.pump(G + 2)
    ck(net.st("Alice", "state") == "rolling", "offline with an unreadable name: not gone")
    set_names(A, NAME_CASES[4][1])
    net.pump(1)
    ck(net.st("Alice", "state") == "rolling" and A.eval("TapCatForever.DR.RosterSays(TapCatForever.DR.duel) == 'offline'"),
       "offline with his readable name: the grace period runs first (%s %s)" % (net.st("Alice", "state"), net.st("Alice", "reason")))
    A.execute("UnitIsConnected = nil")   # back after a second: a loading screen
    net.pump(G + 1)
    ck(net.st("Alice", "state") == "rolling", "a moment offline changed nothing (%s %s)" % (net.st("Alice", "state"), net.st("Alice", "reason")))
    A.execute("function UnitIsConnected(u) return u ~= 'party1' end")
    net.pump(G - 2)
    ck(net.st("Alice", "state") == "rolling", "still in the grace period")
    net.pump(3)
    ck(net.st("Alice", "result") == "cancel" and net.st("Alice", "reason") == "g" and net.st("Alice", "by") == "opp",
       "offline for the whole grace period: gone (%s %s)" % (net.st("Alice", "state"), net.st("Alice", "reason")))
    ck(net.coins("Alice") == a0, "the stake came back")
    A.execute("UnitIsConnected = nil")
    net.ex("Bob", "TapCatForever.DR.CallOff('x', true)"); net.pump(1)
    net.pump(4)

    # the roster can confirm Bob but never deny him: Party.lua has him missing from one roster read
    # and no roster event follows (he is back, the game said nothing); UnitName("party1") reads his
    # name, so the duel survives Alice thinking for longer than the grace period on her turn
    roster_events(net); net.pump(2)
    A.execute('_keep = _group; _group = {}; _fire("GROUP_ROSTER_UPDATE"); _group = _keep')
    net.pump(1)
    ck(A.eval("TapCatForever:PartyMembers()[1].missing ~= nil"), "Party.lua has Bob missing (stale)")
    start_dr(net, "Alice", "Bob")
    if net.st("Alice", "turn") != "me":
        net.forced = [500]; net.ex("Bob", "TapCatForever:DeathRollRoll()"); net.pump(1)
    ck(net.st("Alice", "turn") == "me", "Alice's turn")
    net.pump(G + 3)
    ck(net.st("Alice", "state") == "rolling", "a stale missing flag with his name on the roster: the duel goes on (%s %s)" % (net.st("Alice", "state"), net.st("Alice", "reason")))
    ck(A.eval("TapCatForever.DR.RosterSays(TapCatForever.DR.duel) == 'here'"), "the roster confirms him")
    dr_to_end(net, "Alice", "Bob", 100, "death roll with a stale missing flag")
    roster_events(net); net.pump(1)

    # a protected IsInGroup is "unknown", not "alone": the duel goes on (Party.lua reads it the same way)
    start_dr(net, "Alice", "Bob")
    A.execute("_isInGroup = IsInGroup; function IsInGroup() return _SECRET end")
    net.pump(3)
    ck(net.st("Alice", "state") == "rolling" and A.eval("TapCatForever.DR.InGroup()"), "a protected IsInGroup keeps the duel (%s %s)" % (net.st("Alice", "state"), net.st("Alice", "reason")))
    A.execute("IsInGroup = _isInGroup")
    dr_to_end(net, "Alice", "Bob", 100, "death roll after a protected IsInGroup")
    print("duel presence section (roster names as a protected value, Unknown, Name-Realm, nil and a protected value "
          "without issecretvalue: a death roll and a rock paper scissors game each run to the end; a roster blink and "
          "a message in the grace period keep the duel; a friend really gone is called off with g after the grace "
          "period in both games; offline only on a readable name and only after the grace period; a readable name "
          "confirms the friend over a stale missing flag; a protected IsInGroup keeps the duel): all checks passed")

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import test_harness
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
