# 1.5.3.2: the leaderboard shares through the party (and guild) when the hidden channel can't be
# used (WoW: Forever may refuse addon messages on custom channels).
import sys

def check(seed, load_addon):
    LB_CLIENT = sys.modules["__main__"].LB_CLIENT
    srv = [1800000000]
    clients = []
    def make(name, cls):
        lua = load_addon(login=False)
        lua.execute(LB_CLIENT)
        # the channel never joins; the two are in a party together
        lua.execute('function JoinTemporaryChannel() _joins = _joins + 1 end; _group = {}; '
                    'function GetNumGroupMembers() return 2 end; function IsInRaid() return false end')
        lua.execute("math.randomseed(%d)" % ((seed + sum(map(ord, name))) % 2147483647))
        lua.execute('_charName = "%s"; _srv = %d' % (name, srv[0]))
        lua.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
        lua.execute('TapCatForever.db.class = "%s"; TapCatForever.db.taps = %d' % (cls, 1000 + len(name)))
        lua.execute("_optIn(true)")
        clients.append((name, lua))
        return lua
    A = make("Partya", "MAGE")
    B = make("Partyb", "WARRIOR")
    A.execute('_fire("GROUP_ROSTER_UPDATE")'); B.execute('_fire("GROUP_ROSTER_UPDATE")')
    routes = set()
    for _ in range(150):
        for name, lua in clients: lua.globals()._tick(1, srv[0])
        srv[0] += 1
        for name, lua in clients:
            out = lua.globals()._takeOut()
            for i in range(1, len(out) + 1):
                p, msg, ch = out[i][1], out[i][2], out[i][3]
                if msg[:3] not in ("L1;", "L2;", "R1;", "X1;"): continue
                routes.add(ch)
                if ch != "PARTY": continue
                for other, olua in clients:
                    if other != name:
                        olua.globals()._deliver(p, msg, name + "-Forever", "PARTY", "")
    if routes != {"PARTY"}:
        raise AssertionError("lb party: routes used %r" % routes)
    a, b = A.eval("_boardKeys()"), B.eval("_boardKeys()")
    if "partyb-forever" not in a or "partya-forever" not in b:
        raise AssertionError("lb party: boards A=%r B=%r" % (a, b))
    # a stranger's message over WHISPER is not leaderboard traffic
    A.globals()._deliver("TapCatFvr", "L1;Strang-Forever;MAGE;5;10;0;0;1.5.3;%d" % srv[0], "Strang-Forever", "WHISPER", "")
    if "strang" in A.eval("_boardKeys()"):
        raise AssertionError("lb party: whisper accepted")
    print("leaderboard party section (shares through the party without the channel): all checks passed")

def _own_row_odd_realms(load_addon):
    import sys
    LB_CLIENT = sys.modules["__main__"].LB_CLIENT
    for realm in ("Forever (US)", "Forever.EU", "Living Flame", "Forever-1", "Nightslayer"):
        lua = load_addon(login=False)
        lua.execute(LB_CLIENT)
        lua.execute('_charName = "Ziggu"; GetNormalizedRealmName = function() return "%s" end; GetRealmName = GetNormalizedRealmName' % realm.replace(" ", ""))
        lua.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
        lua.execute("_optIn(true)")
        n = lua.eval('(function() local l = TapCatForever:LeaderboardSection("taps", "taps"); local c = 0; for _, r in ipairs(l) do if r.self then c = c + 1 end end; return c end)()')
        if n != 1:
            raise AssertionError("own row missing on realm %r" % realm)
_orig_check = check
def check(seed, load_addon):
    _orig_check(seed, load_addon)
    _own_row_odd_realms(load_addon)
    print("leaderboard own row section (odd realm names): all checks passed")
