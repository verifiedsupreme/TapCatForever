# 1.6.4: a death roll never needs a /reload. When it's the other player's turn and their roll doesn't
# come for DR.STALL_CALL_OFF seconds, you may call it off (both bets come back); never on your own
# turn. After the 1 the wait for the other addon is DR.DONE_WAIT (20 s) and the screen counts it down.
# Then the next challenge works straight away.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import test_selfname as TS
import test_deathroll as TD

def ck(c, m):
    if not c: raise AssertionError("death roll stall: " + m)

def check(seed, load_addon):
    import random
    net = TS.Net(load_addon, seed, random.Random(seed))
    A, B = net.add("Alice", cls="MAGE", level=20), net.add("Bob", cls="WARRIOR", level=20)
    net.group(["Alice", "Bob"])
    net.pump(2)
    ck(A.eval("TapCatForever.DR.DONE_WAIT") == 20, "the wait after the 1 is 20 s")
    a0, b0 = net.coins("Alice"), net.coins("Bob")
    ok = A.eval('(TapCatForever:DeathRollChallenge("Bob", 100, 1000))')
    ck(ok, "challenge")
    net.pump(1)
    ck(B.eval("(TapCatForever:DeathRollAnswer(true))"), "accepted")
    net.pump(1)
    # whoever rolls first stalls: the other side waits
    staller = "Alice" if net.st("Alice", "turn") == "me" else "Bob"
    waiter = "Bob" if staller == "Alice" else "Alice"
    W, S = net.c[waiter], net.c[staller]
    ck(not S.eval("TapCatForever.DR.CanCallOff()"), "no call off on your own turn")
    ck(not W.eval("TapCatForever.DR.CanCallOff()"), "not right away")
    net.pump(21)
    ck(net.st(waiter, "state") == "rolling" and W.eval("TapCatForever.DR.CanCallOff()"), "after 20 s with no roll the waiter may call it off")
    ck(not S.eval("TapCatForever.DR.CanCallOff()") and not S.eval("(TapCatForever:DeathRollCallOff())"), "the stalling player still can't")
    ck(W.eval("(TapCatForever:DeathRollCallOff())"), "called off")
    net.pump(2)
    ck(net.st(waiter, "result") == "cancel" and net.st(staller, "result") == "cancel", "both sides end it: %s %s" % (net.st(waiter, "result"), net.st(staller, "result")))
    ck(net.coins("Alice") == a0 and net.coins("Bob") == b0, "both bets came back")
    # and the next game starts at once, no /reload
    ok = W.eval('(TapCatForever:DeathRollChallenge(%r, 50, 100))' % staller)
    ck(ok, "a new challenge right away")
    net.pump(1)
    ck(S.eval("(TapCatForever:DeathRollAnswer(true))"), "accepted again")
    net.pump(1)
    TD._play_to_end(net, waiter, staller, [60, 30, 5, 1])
    ck({net.st("Alice", "result"), net.st("Bob", "result")} == {"win", "lose"}, "the second game finishes")
    print("death roll stall section (call off on their stalled turn only, bets back, 20 s wait after the 1, next game straight away): all checks passed")
