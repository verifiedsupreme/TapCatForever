# 1.6.1.1: WoW: Forever allows a space inside a character name ("Ziggu Trip", "Its Caffeinated"), and its
# GetNormalizedRealmName / GetRealmName come back empty while UnitFullName("player") splits the two words
# ("Ziggu", "Trip"). Before this version the leaderboard refused every message from such a sender (no name
# key) and took "Trip" for the realm. Two clients named that way, no realm from the game, messages passed
# with the plain sender name as Forever sends it: both see each other, by the real messages and by the
# party feed; the own key spells the whole name; a row saved under the old wrong key goes away.
# Run on its own:  python3 tools/tests/test_lb_names.py
import sys

NAMES = ("Ziggu Trip", "Its Caffeinated")
FOREVER = '''
GetNormalizedRealmName = function() return "" end
GetRealmName = function() return "" end
function UnitFullName(u) local a, b = _charName:match("^(%S+)%s+(%S+)$"); return a, b end
'''

def ck(c, m):
    if not c: raise AssertionError("lb names: " + m)

def check(seed, load_addon):
    LB_CLIENT = sys.modules["__main__"].LB_CLIENT
    srv = [1800000000]
    clients = []
    def make(name, cls, stale=None):
        lua = load_addon(login=False)
        lua.execute(LB_CLIENT)
        lua.execute('function JoinTemporaryChannel() _joins = _joins + 1 end; _group = {}; '
                    'function GetNumGroupMembers() return 2 end; function IsInRaid() return false end')
        lua.execute("math.randomseed(%d)" % ((seed + sum(map(ord, name))) % 2147483647))
        lua.execute('_charName = "%s"; _srv = %d' % (name, srv[0]))
        lua.execute(FOREVER)
        if stale:
            # a board saved by 1.6.1 with the own row under the wrong key ("ziggu-trip")
            lua.execute('TapCatForeverDB = TapCatForeverDB or {}; TapCatForeverDB.lb = { Realm = { e = { ["%s"] = { n = "%s", c = "MAGE", l = 3, t = 50, a = 0, z = 0, v = "1.6.1", ts = %d } }, rm = {} } }'
                        % (stale[0], stale[1], srv[0]))
        lua.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
        lua.execute('TapCatForever.db.class = "%s"; TapCatForever.db.taps = %d' % (cls, 1000 + len(name)))
        lua.execute("_optIn(true)")
        clients.append((name, lua))
        return lua
    A = make(NAMES[0], "MAGE", stale=("ziggu-trip", "Ziggu-Trip"))
    B = make(NAMES[1], "WARRIOR")
    realm = A.eval("TapCatForever.LeaderboardRealm()")
    ck(realm == "Realm", "an empty realm from the game is the stand-in realm, not the second word of the name: %r" % realm)
    ck(A.eval("TapCatForever.DevFullKey(_charName)") == "ziggutrip-realm", "own key spells the whole name: %r" % A.eval("TapCatForever.DevFullKey(_charName)"))
    ck(A.eval("TapCatForever.DevFullKey('Its Caffeinated')") == "itscaffeinated-realm", "friend's key from the plain sender name")
    ck(A.eval("TapCatForever.LeaderboardValidName('Its Caffeinated-Realm')") is True, "a two-word name travels")
    ck(A.eval("TapCatForever.LeaderboardValidName('Its  Caffeinated-Realm')") is False, "two spaces are not a name")
    ck(A.eval("TapCatForever.LeaderboardValidName(' Its-Realm')") is False, "a leading space is not a name")
    # the stale own row went at login
    ck("ziggu-trip" not in A.eval("_boardKeys()"), "the old wrong-key own row is gone at login: %r" % A.eval("_boardKeys()"))
    A.execute('_fire("GROUP_ROSTER_UPDATE")'); B.execute('_fire("GROUP_ROSTER_UPDATE")')
    for _ in range(150):
        for name, lua in clients: lua.globals()._tick(1, srv[0])
        srv[0] += 1
        for name, lua in clients:
            out = lua.globals()._takeOut()
            for i in range(1, len(out) + 1):
                p, msg, ch = out[i][1], out[i][2], out[i][3]
                if msg[:3] not in ("L1;", "L2;", "R1;", "X1;") or ch != "PARTY": continue
                for other, olua in clients:
                    if other != name:
                        olua.globals()._deliver(p, msg, name, "PARTY", "")   # Forever: the plain name, no realm
    a, b = A.eval("_boardKeys()"), B.eval("_boardKeys()")
    ck("itscaffeinated-realm" in a, "A sees B by the real messages: %r" % a)
    ck("ziggutrip-realm" in b, "B sees A by the real messages: %r" % b)
    e = A.eval('_entry("itscaffeinated-realm")')
    ck(e["n"] == "Its Caffeinated-Realm" and e["t"] == 1000 + len(NAMES[1]) and e["c"] == "WARRIOR", "the row keeps the name with its space and the right numbers: %r %r %r" % (e["n"], e["t"], e["c"]))
    ck(A.eval('TapCatForever.LeaderboardDisplayName("Its Caffeinated-Realm")') == "Its Caffeinated", "shown without the stand-in realm")
    rows = A.eval('(function() local l = TapCatForever:LeaderboardSection("taps", "taps"); local t = {}; for _, r in ipairs(l) do t[#t + 1] = (r.self and "*" or "") .. TapCatForever.LeaderboardDisplayName(r.n) end; return table.concat(t, ",") end)()')
    ck(rows == "Its Caffeinated,*Ziggu Trip", "Total taps shows the friend and your own row: %r" % rows)
    # the party feed path (Party.lua hands a member to the leaderboard) with the same kind of sender
    C = make("Big Whiskers", "HUNTER")
    res = C.eval('(function() local r, why = TapCatForever.LeaderboardFromParty({ sender = "Its Caffeinated", name = "ItsCaffeinated", joined = true, class = "WARRIOR", level = 7, taps = 4242, ach = 2, zones = 1, version = "1_6_1" }); return tostring(r) .. "/" .. tostring(why) end)()')
    ck(res.startswith("added"), "a party member with a two-word name goes on the board: %r" % res)
    e = C.eval('_entry("itscaffeinated-realm")')
    ck(e and e["t"] == 4242 and e["n"] == "Its Caffeinated-Realm", "the party row has the right taps and name")
    # dropped-message counters stay quiet for these senders
    dbg = A.eval('(function() local d = TapCatForever.LeaderboardDebug; return (d.drop and d.drop.nokey or 0) end)()')
    ck(dbg == 0, "no message from a two-word name was dropped for its name: %r" % dbg)
    print("leaderboard two-word names section (Forever names with a space, empty realm): all checks passed")
