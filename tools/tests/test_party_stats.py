# 1.6.1: the party message carries the player's stats (total taps, achievements, zones cleared, on the
# leaderboard or not, version) as extra code=value entries after the gear slots. The party profile
# window shows them, and the leaderboard is fed from party members who joined it, so it works where
# the leaderboard's own messages (L1, L2, R1, X1) never get through. Two clients with a secret
# UnitName("player") in a party, every leaderboard message dropped by the net (WoW: Forever):
#   - after the hellos each board holds the other's row with the right taps, class and level, in
#     Total taps and Per class
#   - the member record holds the stats (m.taps, m.ach, m.zones, m.joined, m.version) and the
#     profile window prints them in plain English
#   - a friend who has not joined the leaderboard: taps in the profile, no row on the board
#   - a 1.6.0 parser (tools/tests/fixtures/Party_1_6_0.lua, git show main:Party.lua at 1.6.0) reads
#     the new payload and still gets all twelve gear slots
#   - the payload stays within 240 bytes with every slot filled and 15-digit taps
#   - a resend goes out once the taps grew by TAPS_STEP and 60 s passed since the last message, not
#     before, and never while nothing changed; the friend's board follows
#   - /tcf lbdebug counts the rows fed from the party and why heard messages were dropped
# Run on its own:  python3 tools/tests/test_party_stats.py [seed]
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, HERE)
import test_selfname as TS

# the leaderboard's own messages never arrive (what players on WoW: Forever see); the party ones do
DROP_LB = r'''
local inner = _deliver
_lbDropped = 0
function _deliver(p, msg, sender, chan)
  if msg:match("^L1;") or msg:match("^L2;") or msg:match("^X1;") or msg:match("^R1;%d+$") then
    _lbDropped = _lbDropped + 1
    return
  end
  return inner(p, msg, sender, chan)
end
_printed = {}
local print0 = TapCatForever.Print
TapCatForever.Print = function(self, msg, ...) _printed[#_printed + 1] = msg; return print0(self, msg, ...) end
'''

def ck(c, m):
    if not c: raise AssertionError("party stats: " + m)

ROWS = '''(function() local t = {} for _, r in ipairs(TapCatForever:LeaderboardSection(%r, %r)) do t[#t + 1] = r.n .. (r.self and "*" or "") .. "=" .. tostring(r.val) end table.sort(t) return table.concat(t, ",") end)()'''

def rows(L, section="taps", sub="taps"): return L.eval(ROWS % (section, sub))

def member(L, name):
    return L.eval('(function() for _, m in ipairs(TapCatForever:PartyMembers()) do if m.name == %r then return m end end end)()' % name)

def msgs(net, sender, kind, start=0):
    return [m for (n, m, ch) in net.log[start:] if n == sender and m.startswith(kind + ";")]

def check(seed, load_addon):
    import random
    rnd = random.Random(seed)
    net = TS.Net(load_addon, seed, rnd)
    A, B = net.add("Alice", cls="MAGE", level=20), net.add("Bob", cls="WARRIOR", level=33)
    for L, taps in ((A, 12345), (B, 777000)):
        L.execute(DROP_LB)
        L.execute("TapCatForever.db.taps = %d; TapCatForever.db.ui.shareDev = true; TapCatForever:DevShareChanged()" % taps)
    B.execute("TapCatForever.db.achievements = TapCatForever.db.achievements or {}; local n = 0 "
              "for _, a in ipairs(TapCatForever.ACHIEVEMENTS) do if n < 7 then TapCatForever.db.achievements[a.id] = true; n = n + 1 end end")
    net.group(["Alice", "Bob"])
    net.pump(70)   # the first ticks award achievements (taps), and the update that follows has gone out
    achA, achB = A.eval("TapCatForever.LeaderboardAchievements()"), B.eval("TapCatForever.LeaderboardAchievements()")
    ck(achB >= 7 and achB == B.eval("(function() local n = 0 for _ in pairs(TapCatForever.db.achievements) do n = n + 1 end return n end)()"),
       "the achievements count is exposed (%r)" % achB)

    # --- the payload: slots first, then the stats, then the tag
    pa = A.eval("TapCatForever:PartyPayload()")
    ck(pa.endswith("z=" + pa.rsplit("z=", 1)[1]) and ",v=1_1_0,z=" in pa, "stats before the tag, version with underscores: %s" % pa)
    ck(",t=12345,u=%d,d=0,l=1," % achA in pa, "Alice's stats travel: %s" % pa)
    for c in "tudlv":
        ck(c not in "hcmobaenwrsxz", "stat code %s is no slot code" % c)
    ck(all(len(m) <= 240 for (n, m, ch) in net.log if m[:3] in ("H1;", "U1;")), "every party message fits 240 bytes")
    ck(A.eval("_lbDropped") > 0 and B.eval("_lbDropped") > 0, "the net dropped the leaderboard's own messages")

    # --- each board holds the other, fed by the party message alone
    ck(rows(A) == "Alice-Forever*=12345,Bob-Forever=777000", "Alice's board: %s" % rows(A))
    ck(rows(B) == "Alice-Forever=12345,Bob-Forever*=777000", "Bob's board: %s" % rows(B))
    e = A.eval("TapCatForever.LeaderboardBoard(false).e['bob-forever']")
    ck(e.c == "WARRIOR" and e.l == 33 and e.t == 777000 and e.a == achB and e.v == "1.1.0" and e.d is True, "Bob's entry: class, level, taps, achievements, version, heard from him")
    # (your own row is always on every class board, at level 1 for a cat you never played)
    ck(rows(A, "class", "WARRIOR") == "Alice-Forever*=1,Bob-Forever=33", "Per class, Warrior: %s" % rows(A, "class", "WARRIOR"))
    ck(rows(B, "class", "MAGE") == "Alice-Forever=20,Bob-Forever*=1", "Per class, Mage: %s" % rows(B, "class", "MAGE"))
    ck(A.eval("TapCatForever.LeaderboardDebug.party") >= 1 and B.eval("TapCatForever.LeaderboardDebug.party") >= 1, "the party counter counts")

    # --- the member record and the profile window
    m = member(A, "Bob")
    ck(m.taps == 777000 and m.ach == achB and m.zones == 0 and m.joined is True and m.version == "1.1.0", "Bob's stats on the member")
    A.execute("BreakUpLargeNumbers = nil")   # the mock's returns plain digits; the game puts in the commas
    A.execute('(function() for _, m in ipairs(TapCatForever:PartyMembers()) do if m.name == "Bob" then TapCatForever:ShowPartyProfile(m) end end end)()')
    info = A.eval("TapCatForeverPartyProfile.info.text")
    for line in ("Total taps: 777,000", "Achievements: %d" % achB, "Zones cleared: 0", "On the leaderboard", "Gear worn:"):
        ck(line in info, "profile shows %r: %r" % (line, info))
    ck("!" not in info, "plain text")
    sub = A.eval("TapCatForeverPartyProfile.sub.text")
    ck("Level 33 Warrior" in sub, "class and level: %r" % sub)

    # --- a friend who hasn't joined: stats in the profile, nothing on the board
    C = net.add("Cara", cls="ROGUE", level=5)
    C.execute(DROP_LB)
    C.execute("TapCatForever.db.taps = 4321")
    net.group(["Alice", "Bob", "Cara"])
    m = member(A, "Cara")
    ck(m is not None and m.taps == 4321 and m.joined is False, "Cara's stats arrived")
    A.execute('(function() for _, m in ipairs(TapCatForever:PartyMembers()) do if m.name == "Cara" then TapCatForever:ShowPartyProfile(m) end end end)()')
    info = A.eval("TapCatForeverPartyProfile.info.text")
    ck("Total taps: 4,321" in info and "Not on the leaderboard yet" in info, "Cara's profile: %r" % info)
    ck(rows(A) == "Alice-Forever*=12345,Bob-Forever=777000", "Cara is not on Alice's board: %s" % rows(A))
    ck(C.eval("TapCatForever.LeaderboardBoard(false) == nil or next(TapCatForever.LeaderboardBoard(false).e) == nil"), "Cara, not sharing, keeps no board")
    ck(C.eval("TapCatForever.LeaderboardDebug.party") == 0, "nothing fed on Cara's side")
    # the function itself refuses what it should
    ck(A.eval("select(2, TapCatForever.LeaderboardFromParty({ joined = false }))") == "not joined", "not joined refused")
    ck(A.eval("select(2, TapCatForever.LeaderboardFromParty({ joined = true, sender = 'Zed-Forever', class = 'MAGE', level = 5, taps = -5, ach = 0, zones = 0, version = '1' }))") == "invalid", "odd numbers refused")
    ck(A.eval("select(2, TapCatForever.LeaderboardFromParty({ joined = true, sender = _SECRET, name = 'x', class = 'MAGE', level = 5, taps = 5, ach = 0, zones = 0, version = '1' }))") == "name", "a secret sender is no name")

    # --- a resend once the taps grew and 60 s passed, not before, none while nothing changes
    net.pump(70)
    start = len(net.log)
    net.pump(120)
    ck(not msgs(net, "Alice", "U1", start), "nothing changed: no update in two minutes")
    A.execute("TapCatForever.db.taps = TapCatForever.db.taps + 5")
    net.pump(10)
    ck(not msgs(net, "Alice", "U1", start), "5 taps are not worth a message")
    A.execute("TapCatForever.db.taps = TapCatForever.db.taps + 495")
    net.pump(3)
    ck(len(msgs(net, "Alice", "U1", start)) == 1 and ",t=12845," in msgs(net, "Alice", "U1", start)[0], "grown taps, a minute since the last message: one update")
    ck(member(B, "Alice").taps == 12845 and rows(B) == "Alice-Forever=12845,Bob-Forever*=777000", "Bob's profile and board follow: %s" % rows(B))
    start = len(net.log)
    A.execute("TapCatForever.db.taps = TapCatForever.db.taps + 1000")
    net.pump(40)
    ck(not msgs(net, "Alice", "U1", start), "no second update within the minute")
    net.pump(25)
    ck(len(msgs(net, "Alice", "U1", start)) == 1 and ",t=13845," in msgs(net, "Alice", "U1", start)[0], "and one once the minute is up")
    start = len(net.log)
    net.pump(90)
    ck(not msgs(net, "Alice", "U1", start), "then quiet again")
    # a look change still goes out at once
    A.execute("TapCatForever:Owned().acc_shades = 1; TapCatForever:Equip(TapCatForever.ITEMS.acc_shades)")
    net.pump(3)
    ck(len(msgs(net, "Alice", "U1", start)) == 1 and "a=acc_shades" in msgs(net, "Alice", "U1", start)[0], "a new look is an update at once")

    # --- /tcf lbdebug: rows from the party, and why heard messages were dropped
    # (straight to the event: the net's drop filter above sits on _deliver)
    A.execute('_fire("CHAT_MSG_ADDON", "TapCatFvr", "L1;garbage", "PARTY", "Bob-Forever", "", 0, 0, "", 0)')
    A.execute('_fire("CHAT_MSG_ADDON", "TapCatFvr", "L1;Strang-Forever;MAGE;5;10;0;0;1.5.3;1800000000", "WHISPER", "Strang-Forever", "", 0, 0, "", 0)')
    dbg = A.eval("TapCatForever.LeaderboardDebug")
    ck(dbg.drop.parse == 1 and dbg.drop.route == 1, "drop reasons counted: parse %r route %r" % (dbg.drop.parse, dbg.drop.route))
    A.execute("_printed = {}; TapCatForever:LeaderboardDebugPrint()")
    out = " | ".join(A.eval("_printed").values())
    ck("Rows from party messages: %d" % dbg.party in out and "parse 1" in out and "route 1" in out and "!" not in out, "lbdebug prints them: %r" % out)

    # --- a 1.6.0 reader (the fixture is 1.6.0's Party.lua) still gets every gear slot
    _old_reader(load_addon)
    print("party stats section (stats in the party message, boards fed from the party with every leaderboard "
          "message dropped, profile lines, a friend not on the board, 1.6.0 reads all slots, 240 bytes with 12 "
          "slots, resend after 60 s and grown taps, lbdebug reasons): all checks passed")

def _old_reader(load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      _group = { party1 = { "Alice", nil } }
      _fire("GROUP_ROSTER_UPDATE")
      T:SetClass("WARRIOR")
      local eq = T:GearEquipped()
      -- one real item for every gear slot the party message carries
      local want = { HEAD = "HEAD", CHEST = "CHEST", BACK = "BACK", NECK = "NECK", WAIST = "WAIST", FINGER1 = "FINGER1", SHOULDER = "SHOULDER", MAINHAND = "MAINHAND", OFFHAND = "OFFHAND" }
      for key in pairs(want) do
        for _, g in ipairs(T.GEAR_LIST) do
          local slots = T:GearTargetSlots(g, "WARRIOR") or {}
          if not g.suffix and #slots >= 1 and slots[1] == key and (key ~= "OFFHAND" or g.slot == "HOLD" or g.slot == "SHIELD") then eq[key] = g.id; break end
        end
        if not eq[key] then
          for _, g in ipairs(T.GEAR_LIST) do
            local slots = T:GearTargetSlots(g, "WARRIOR") or {}
            for _, s in ipairs(slots) do if s == key and not g.suffix then eq[key] = g.id end end
            if eq[key] then break end
          end
        end
        if not eq[key] then return "no item for " .. key end
      end
      local look0 = T:GetAppearance("WARRIOR")
      local owned = T:Owned("WARRIOR")
      owned.acc_shades, owned.race_human = 1, 1
      T:Equip(T.ITEMS.acc_shades, "WARRIOR"); T:Equip(T.ITEMS.race_human, "WARRIOR")
      local fx
      for _, it in ipairs(T.ITEM_LIST) do if it.slot == "effect" and (not it.class or it.class == "WARRIOR") then fx = it; break end end
      if not fx then return "no effect item" end
      owned[fx.id] = 1
      T:Equip(fx, "WARRIOR")
      local lk = T:GetAppearance("WARRIOR")
      if not (lk.acc and lk.race and lk.effect) then return "cosmetics worn: " .. tostring(lk.acc and lk.acc.id) .. " " .. tostring(lk.race and lk.race.id) .. " " .. tostring(lk.effect and lk.effect.id) end
      T.db.taps = 999999999999999
      T.db.achievements = T.db.achievements or {}
      for _, a in ipairs(T.ACHIEVEMENTS) do T.db.achievements[a.id] = true end
      local payload, lookPart, stats = T:PartyPayloadParts("WARRIOR")
      if #payload > 240 then return "payload too long: " .. #payload end
      local codes = {}
      for c in lookPart:gmatch("[;,](%l)=") do codes[#codes + 1] = c end
      if #codes ~= 12 then return "not all 12 slots in the payload (" .. #codes .. "): " .. payload end
      if not payload:find(",t=999999999999999,", 1, true) then return "the taps are in it: " .. payload end
      -- the new reader: every slot and every stat
      local kind, class, level, look, eqIn, st = T.PartyParse("U1;" .. payload)
      local n = 0
      for _ in pairs(eqIn) do n = n + 1 end
      if n ~= 9 then return "new reader: 9 gear slots, got " .. n end
      if not (st and st.taps == 999999999999999 and st.ach == #T.ACHIEVEMENTS and st.joined == false and st.version == "1.1.0") then return "new reader: stats" end
      if not (look.acc and look.race and look.effect) then return "new reader: cosmetics" end
      _payload, _lookPart = payload, lookPart
      -- a payload with the stats in front (another order) still reads the stats, and no more than 12 slots
      local front = payload:gsub("^(%u+;%d+;[^;]*;[^;]*;[^;]*;)", "%1t=5,u=1,d=2,l=1,v=9_9,")
      local _, _, _, look2, eq2, st2 = T.PartyParse("U1;" .. front)
      n = 0
      for _ in pairs(eq2) do n = n + 1 end
      if not (st2 and st2.taps == 999999999999999 and n == 9) then return "stats anywhere: taps " .. tostring(st2 and st2.taps) .. " slots " .. n end
      local many = "U1;WARRIOR;5;;;;" .. string.rep("h=#" .. eq.HEAD .. ",", 30) .. "t=7,z=abcde"
      local _, _, _, _, eq3, st3 = T.PartyParse(many)
      if not (st3 == nil or st3.taps == nil) then return "30 slot entries: the stats behind entry 24 are not read (that is the cap)" end
      return ""
    ''')
    ck(r == "", r)
    # the very same payload through 1.6.0's parser
    old = open(os.path.join(HERE, "fixtures", "Party_1_6_0.lua"), encoding="utf-8").read()
    chunk = lua.execute("return function(src) return assert(loadstring(src, '@Party_1_6_0.lua')) end")(old)
    chunk("TapCatForever", lua.globals().TapCatForever)
    r = lua.execute(r'''
      local T = TapCatForever
      local kind, class, level, look, eq = T.PartyParse("U1;" .. _payload)
      if kind ~= "U1" or class ~= "WARRIOR" then return "1.6.0 reads the header: " .. tostring(kind) end
      local n = 0
      for _ in pairs(eq) do n = n + 1 end
      if n ~= 9 then return "1.6.0 gets all 9 gear slots, got " .. n end
      if not (look.acc and look.acc.id == "acc_shades" and look.race and look.race.id == "race_human" and look.effect) then return "1.6.0 gets the cosmetics" end
      -- and a 1.6.0 payload still reads on the new side (nothing required)
      return ""
    ''')
    ck(r == "", "old reader: " + r)

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import test_harness
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
