# 1.6.1.1 / 1.6.1.2: WoW: Forever allows a space inside a character name ("Ziggu Trip", "Its Caffeinated").
# There GetNormalizedRealmName / GetRealmName come back "" and the game splits the two words for its own
# player: UnitName("player") is "Ziggu" and UnitFullName("player") is ("Ziggu", "Trip"), while the name
# on addon messages (what every other player sees) is the whole "Ziggu Trip". Before 1.6.1.1 the
# leaderboard refused every message from such a sender (no name key), and the own key became
# "ziggu-trip" (the second word taken for the realm), which no other player could ever match.
# Two clients named that way, messages passed with the plain sender name and echoed to the sender as the
# game does: own keys spell the whole name on the stand-in realm, the two see each other by the real
# messages and by the party feed, a row saved under the old wrong key goes at login, and nothing is
# shared before the own name is learned from an echo. Also with UnitName("player") hidden (secret).
# Run on its own:  python3 tools/tests/test_lb_names.py
import sys

NAMES = ("Ziggu Trip", "Its Caffeinated")
FOREVER = '''
GetNormalizedRealmName = function() return "" end
GetRealmName = function() return "" end
function UnitFullName(u) local a, b = _charName:match("^(%S+)%s+(%S+)$"); return a, b end
local realUnitName = UnitName
function UnitName(u)
  if u == "player" then
    if _ownSecret then return _SECRET end
    return (_charName:match("^(%S+)")) -- Forever: only the first word of a two-word name
  end
  return realUnitName(u)
end
'''

def ck(c, m):
    if not c: raise AssertionError("lb names: " + m)

def check(seed, load_addon):
    _run(seed, load_addon, False)
    _run(seed, load_addon, True)
    print("leaderboard two-word names section (Forever names with a space, empty realm, the own name split by the game or hidden, echoed messages): all checks passed")

def _run(seed, load_addon, secret):
    LB_CLIENT = sys.modules["__main__"].LB_CLIENT
    srv = [1800000000]
    clients = []
    def make(name, cls, stale=None):
        lua = load_addon(login=False)
        lua.execute(LB_CLIENT)
        lua.execute('function JoinTemporaryChannel() _joins = _joins + 1 end; _group = {}; '
                    'function GetNumGroupMembers() return 2 end; function IsInRaid() return false end')
        lua.execute("math.randomseed(%d)" % ((seed + sum(map(ord, name))) % 2147483647))
        lua.execute('_charName = "%s"; _srv = %d; _ownSecret = %s' % (name, srv[0], "true" if secret else "false"))
        lua.execute(FOREVER)
        if stale:
            # a board saved by 1.6.1 with the own row under the wrong key ("ziggu-trip")
            lua.execute('TapCatForeverDB = TapCatForeverDB or {}; TapCatForeverDB.board = { realm = { e = { ["%s"] = { n = "%s", c = "MAGE", l = 3, t = 50, a = 0, z = 0, v = "1.6.1", ts = %d, d = true } }, rm = {}, rmn = {} } }'
                        % (stale[0], stale[1], srv[0]))
        lua.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
        lua.execute('TapCatForever.db.class = "%s"; TapCatForever.db.taps = %d' % (cls, 1000 + len(name)))
        lua.execute("_optIn(true)")
        clients.append((name, lua))
        return lua
    A = make(NAMES[0], "MAGE", stale=("ziggu-trip", "Ziggu-Trip"))
    B = make(NAMES[1], "WARRIOR")
    realm = A.eval("TapCatForever.LeaderboardRealm()")
    ck(realm == "Realm", "an empty realm from the game is the stand-in realm, never the second word of the name: %r" % realm)
    ck(A.eval("TapCatForever.DevFullKey('Its Caffeinated')") == "itscaffeinated-realm", "friend's key from the plain sender name")
    ck(A.eval("TapCatForever.LeaderboardValidName('Its Caffeinated-Realm')") is True, "a two-word name travels")
    ck(A.eval("TapCatForever.LeaderboardValidName('Its  Caffeinated-Realm')") is False, "two spaces are not a name")
    ck(A.eval("TapCatForever.LeaderboardValidName(' Its-Realm')") is False, "a leading space is not a name")
    # before the own name is learned nothing is shared under a guess: the own row shows, the key is unknown
    ck(A.eval("TapCatForever:LeaderboardOwnEntry().guess") is True, "own entry is a guess until the own name is learned (secret=%s)" % secret)
    ck("ziggu-trip" not in A.eval("_boardKeys()"), "the stale row is gone at once (1.6.5: a known leftover)")
    A.execute('_fire("GROUP_ROSTER_UPDATE")'); B.execute('_fire("GROUP_ROSTER_UPDATE")')
    sent_before_name = []
    for _ in range(150):
        for name, lua in clients: lua.globals()._tick(1, srv[0])
        srv[0] += 1
        for name, lua in clients:
            out = lua.globals()._takeOut()
            for i in range(1, len(out) + 1):
                p, msg, ch = out[i][1], out[i][2], out[i][3]
                if msg[:3] in ("L1;", "L2;", "R1;", "X1;") and not lua.eval("TapCatForever.SelfSender"):
                    sent_before_name.append(msg)
                if ch != "PARTY": continue
                for other, olua in clients:   # the whole party hears it, the sender too (Forever: the plain name, no realm)
                    olua.globals()._deliver(p, msg, name, "PARTY", "")
    ck(not sent_before_name, "no leaderboard message went out before the own name was known: %r" % sent_before_name[:2])
    ck(A.eval("TapCatForever.SelfSender") == NAMES[0], "the own name is learned from the echo: %r" % A.eval("TapCatForever.SelfSender"))
    ck(A.eval("TapCatForever.SelfName()") == NAMES[0], "SelfName is the whole name, not the game's first word: %r" % A.eval("TapCatForever.SelfName()"))
    own = A.eval("(function() local e = TapCatForever:LeaderboardOwnEntry(); return e.n .. '/' .. tostring(e.guess) end)()")
    ck(own == "Ziggu Trip-Realm/nil", "own entry under the whole name on the stand-in realm: %r" % own)
    a, b = A.eval("_boardKeys()"), B.eval("_boardKeys()")
    ck("ziggu-trip" not in a, "the old wrong-key own row is gone once the own name is known: %r" % a)
    ck(a == "itscaffeinated-realm", "A's board holds exactly the friend (no own row, no junk): %r" % a)
    ck(b == "ziggutrip-realm", "B's board holds exactly the friend: %r" % b)
    e = A.eval('_entry("itscaffeinated-realm")')
    ck(e["n"] == "Its Caffeinated-Realm" and e["t"] == 1000 + len(NAMES[1]) and e["c"] == "WARRIOR" and e["d"] is True,
       "the row keeps the name with its space, the right numbers, and counts as heard from the player: %r %r %r %r" % (e["n"], e["t"], e["c"], e["d"]))
    ck(A.eval('TapCatForever.LeaderboardDisplayName("Its Caffeinated-Realm")') == "Its Caffeinated", "shown without the stand-in realm")
    rows = A.eval('(function() local l = TapCatForever:LeaderboardSection("taps", "taps"); local t = {}; for _, r in ipairs(l) do t[#t + 1] = (r.self and "*" or "") .. TapCatForever.LeaderboardDisplayName(r.n) end; return table.concat(t, ",") end)()')
    ck(rows == "Its Caffeinated,*Ziggu Trip", "Total taps shows the friend and your own row: %r" % rows)
    # the own echo is recognised as own, nothing from these senders was dropped for its name
    dbg = A.eval('(function() local d = TapCatForever.LeaderboardDebug.drop; return (d.nokey or 0) .. "/" .. (d.own or 0) end)()')
    ck(dbg.split("/")[0] == "0" and int(dbg.split("/")[1]) > 0, "no name drops, own echoes recognised: %r" % dbg)
    # the party feed path (Party.lua hands a member to the leaderboard) with the same kind of sender
    C = make("Big Whiskers", "HUNTER")
    res = C.eval('(function() local r, why = TapCatForever.LeaderboardFromParty({ sender = "Its Caffeinated", name = "ItsCaffeinated", joined = true, class = "WARRIOR", level = 7, taps = 4242, ach = 2, zones = 1, version = "1_6_1" }); return tostring(r) .. "/" .. tostring(why) end)()')
    ck(res.startswith("added"), "a party member with a two-word name goes on the board: %r" % res)
    e = C.eval('_entry("itscaffeinated-realm")')
    ck(e and e["t"] == 4242 and e["n"] == "Its Caffeinated-Realm", "the party row has the right taps and name")
    # a friend still on 1.6.1.1 calls themselves by the split name ("Its-Caffeinated"): their own L1, L2 and
    # a passed-on X1 about that name are theirs, land under their sender key, and the stray row goes
    D = make("Lone Wolf", "PRIEST")
    D.execute('TapCatForever.LearnSelf("Lone Wolf")')
    D.execute('(function() local b = TapCatForever.LeaderboardBoard(true); b.e["its-caffeinated"] = { n = "Its-Caffeinated", c = "HUNTER", l = 26, t = 77487, a = 0, z = 0, v = "1.6.1.1", ts = _srv } end)()')
    D.execute('_deliver("TapCatFvr", "L1;Its-Caffeinated;HUNTER;26;77515;3;1;1.6.1.1;" .. _srv, "Its Caffeinated", "PARTY", "")')
    keys = D.eval("_boardKeys()")
    ck(keys == "itscaffeinated-realm", "the split-name row is theirs and the stray row is gone: %r" % keys)
    e = D.eval('_entry("itscaffeinated-realm")')
    ck(e["t"] == 77515 and e["n"] == "Its Caffeinated-Realm" and e["d"] is True, "under the sender's name, as heard from them: %r %r" % (e["n"], e["t"]))
    D.execute('_deliver("TapCatFvr", "L2;Its-Caffeinated;" .. _srv .. ";0.0.0.26.0.0.0.0.0;5e3;1.1.1.1.1.1.1", "Its Caffeinated", "PARTY", "")')
    ck(D.eval('(function() local e = _entry("itscaffeinated-realm"); return e.x ~= nil and e.x.lv[4] end)()') == 26, "their L2 lands on the same row")
    ck("its-caffeinated" not in D.eval("_boardKeys()"), "no stray row after the L2 either")
    # the party feed for the same friend removes a stray split-name row too
    D.execute('(function() local b = TapCatForever.LeaderboardBoard(true); b.e["its-caffeinated"] = { n = "Its-Caffeinated", c = "HUNTER", l = 26, t = 1, a = 0, z = 0, v = "?", ts = _srv } end)()')
    D.eval('TapCatForever.LeaderboardFromParty({ sender = "Its Caffeinated", name = "ItsCaffeinated", joined = true, class = "HUNTER", level = 26, taps = 77600, ach = 3, zones = 1, version = "1_6_1" })')
    ck(D.eval("_boardKeys()") == "itscaffeinated-realm", "the party feed clears the stray row: %r" % D.eval("_boardKeys()"))
    # ForgetSelf only takes the one exact wrong key, never a friend's row
    C.execute('TapCatForever.LearnSelf("Big Whiskers")')
    C.execute('(function() local b = TapCatForever.LeaderboardBoard(true); b.e["big-whiskers"] = { n = "Big-Whiskers", c = "MAGE", l = 1, t = 1, a = 0, z = 0, v = "?", ts = _srv }; '
              'b.e["bigwhis-kers"] = { n = "Bigwhis-kers", c = "MAGE", l = 1, t = 1, a = 0, z = 0, v = "?", ts = _srv }; TapCatForever.LeaderboardForgetSelf() end)()')
    keys = C.eval("_boardKeys()")
    ck("big-whiskers" not in keys and "bigwhis-kers" in keys and "itscaffeinated-realm" in keys, "only the exact old own key goes: %r" % keys)
