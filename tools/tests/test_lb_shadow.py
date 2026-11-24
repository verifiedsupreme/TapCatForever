# 1.6.5: rows the 1.6.1.1 two-word-name bug left on boards ("Its Caffeinated-Trip", "Ziggu Trip-Caffeinated":
# a player under the second word of someone's name taken for a realm) go when the board loads, are not taken
# in again from older addons passing them on, and never show. Real rows stay.
import sys

def ck(c, m):
    if not c: raise AssertionError("lb shadow: " + m)

def check(seed, load_addon):
    LB_CLIENT = sys.modules["__main__"].LB_CLIENT
    srv = 1800000000
    lua = load_addon(login=False)
    lua.execute(LB_CLIENT)
    lua.execute('''
      GetNormalizedRealmName = function() return "" end
      GetRealmName = function() return "" end
      _charName = "Ziggu"; _srv = %d
      local function row(n, t) return { n = n, c = "MAGE", l = 20, t = t, a = 5, z = 1, v = "1.6.1.1", ts = %d, d = true } end
      TapCatForeverDB = TapCatForeverDB or {}
      TapCatForeverDB.board = { realm = { e = {
        ["itscaffeinated-realm"] = row("Its Caffeinated-Realm", 90679),
        ["itscaffeinated-trip"] = row("Its Caffeinated-Trip", 77707),
        ["ziggutrip-caffeinated"] = row("Ziggu Trip-Caffeinated", 17590),
        ["holyworduwu-realm"] = row("Holyword Uwu-Realm", 11533),
        ["kelsirose-otherrealm"] = row("Kelsi Rose-Otherrealm", 31471),
        ["ziggu-trip"] = row("Ziggu-Trip", 22558),
        ["its-caffeinated"] = row("Its-Caffeinated", 91947),
        ["averysky-claw"] = row("Averysky-Claw", 100),
        ["averyskyclaw-realm"] = row("Avery Skyclaw-Realm", 29172),
      }, rm = {}, rmn = {} } }
    ''' % (srv, srv))
    lua.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    lua.execute('TapCatForever.LearnSelf("Ziggu Trip"); TapCatForever.db.class = "MAGE"; _optIn(true)')
    keys = lua.eval("_boardKeys()")
    for gone in ("itscaffeinated-trip", "ziggutrip-caffeinated", "ziggu-trip", "its-caffeinated", "averysky-claw"):
        ck(gone not in keys.split(","), "leftover row %s is gone: %r" % (gone, keys))
    ck("itscaffeinated-realm" in keys and "holyworduwu-realm" in keys and "kelsirose-otherrealm" in keys, "real rows stay: %r" % keys)
    # an older addon passes one on again: not taken in
    lua.globals()._deliver("TapCatFvr", "L1;Its Caffeinated-Trip;HUNTER;27;77707;38;9;1.6.1.1;%d" % srv, "Old Friend", "PARTY", "")
    ck("itscaffeinated-trip" not in lua.eval("_boardKeys()"), "not taken in again")
    rows = lua.eval('(function() local l = TapCatForever:LeaderboardSection("taps", "taps"); local t = {}; for _, r in ipairs(l) do t[#t + 1] = r.n end; return table.concat(t, ",") end)()')
    names = rows.split(",")
    ck(sorted(names) == sorted(["Its Caffeinated-Realm", "Kelsi Rose-Otherrealm", "Holyword Uwu-Realm", "Avery Skyclaw-Realm", "Ziggu Trip-Realm"]), "the list shows each player once: %r" % rows)
    print("leaderboard leftover rows section (the 1.6.1.1 rows under a wrong realm go and stay gone, real rows stay): all checks passed")
