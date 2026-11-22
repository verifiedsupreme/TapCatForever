# Party expeditions (PartyExpeditions.lua, UI_PartyExpeditions.lua): group members with the addon send
# their cats out together. 3-5 simulated clients pass addon messages through the party/raid channel.
# Checks: the invite prompt above the screen cat (text, Accept / Decline, 60 s timeout that counts as
# a decline, smaller during combat, sits above a casino invite), one pending invite at a time, the
# start (everyone stores the same expedition: id, start, length, difficulty, seed, players, Power,
# chance), it keeps running after the group breaks up and through a /reload, everyone gets the same
# result and claims their own rewards once (XP, TapCoins, chests, class achievement counts), its own
# slot next to the two solo slots, cats on it can't go elsewhere, a lost start asked for again,
# withdraw, nobody joined, a full group of 5 with long names, raid channel, refused sends retried,
# spoofed and odd messages, the numbers (Power needed, rewards, TapCoins per hour), the Party view of
# the Expeditions tab, and plain text.
# Run on its own:  python3 tools/tests/test_party_expeditions.py [seed]
import os, random, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

CLIENT = r'''
_out = {}
_srv = 1800000000
function GetServerTime() return _srv end
C_ChatInfo.SendAddonMessage = function(p, msg, ch, target)
  if _sendResult == 0 then table.insert(_out, { p, msg, ch, target or "" }) end
  return _sendResult
end
function _takeOut() local o = _out; _out = {}; return o end
function _deliver(p, msg, sender, chan) _fire("CHAT_MSG_ADDON", p, msg, chan, sender, "", 0, 0, "", 0) end
function _ser(v)
  local t = type(v)
  if t == "string" then return string.format("%q", v) end
  if t == "number" or t == "boolean" then return tostring(v) end
  if t ~= "table" then return "nil" end
  local parts = {}
  for k, x in pairs(v) do
    local tk = type(k)
    if (tk == "string" or tk == "number") and type(x) ~= "function" then parts[#parts + 1] = "[" .. _ser(k) .. "]=" .. _ser(x) end
  end
  return "{" .. table.concat(parts, ",") .. "}"
end
function _dbString() setmetatable(TapCatForeverDB, nil); return _ser(TapCatForeverDB) end
function _g(k) local g = TapCatForever:GroupExp(); if not g then return nil end; return g[k] end
function _inv(k) local x = TapCatForever.GX.inv; return x and x[k] end
function _keys() return TapCatForever:ChestCount() end
function _prompt() local p = TapCatForeverGroupExpPrompt; return p ~= nil and p:IsShown() end
'''

def ck(c, m):
    if not c: raise AssertionError("party expeditions: " + m)

class Net:
    def __init__(self, load_addon, seed):
        self.load_addon, self.seed = load_addon, seed
        self.c, self.log, self.raid, self.drop = {}, [], False, None
        self.srv = 1800000000
    def add(self, name, db=None, cls="MAGE", level=None):
        lua = self.load_addon(login=False)
        lua.execute(CLIENT)
        lua.execute('_charName = "%s"; _srv = %d; math.randomseed(%d)' % (name, self.srv, (self.seed + sum(map(ord, name)) * 7919) % 2147483647))
        if db: lua.execute("TapCatForeverDB = loadstring(%r)()" % ("return " + db))
        lua.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
        lua.execute("TapCatForever.db.ui.chat = true")
        if not db:
            lua.execute('TapCatForever:SetClass("%s")' % cls)
            if level: lua.execute('TapCatForever.db.classData.%s.level = %d' % (cls, level))
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
    def ungroup(self, name): self.c[name].execute('_group = nil; _raid = false; _fire("GROUP_ROSTER_UPDATE")')
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
                    ck(p == "TapCatFvr" and len(msg) <= 255, "prefix and length: %d" % len(msg))
                    if msg[:1] == "G": ck(ch == ("RAID" if self.raid else "PARTY"), "party expedition messages go to the group: %s" % ch)
                    if self.drop and msg[:2] in self.drop: continue
                    for other, olua in self.c.items():   # the whole group hears it, the sender too (echo)
                        if self.grouped(other) and self.grouped(name):
                            olua.globals()._deliver(p, msg, name + "-Forever", ch)
    def pump(self, seconds=1, dt=0.5):
        for _ in range(int(seconds / dt)):
            self.srv += dt
            for lua in self.c.values(): lua.execute("_srv = %d; _update(%f)" % (int(self.srv), dt))
            self.deliver()
    def ex(self, name, code): return self.c[name].execute(code)
    def ev(self, name, expr): return self.c[name].eval(expr)
    def gmsgs(self, kind=None): return [m for (n, m, ch) in self.log if m[:1] == "G" and (kind is None or m[:2] == kind)]

def check(seed, load_addon):
    rnd = random.Random(seed)
    _numbers(load_addon)
    _flow(seed, load_addon)
    _edges(seed, load_addon)
    _five(seed, load_addon)
    _ui(seed, load_addon)
    print("party expeditions section (%s; 3 clients: invite prompt, accept, decline, start, same result after the group broke up and a reload, own slot, claim once; timeouts, combat, casino invite, mute, lost start asked again, spoofed and odd messages, refused sends, withdraw, fake cats; %s; the Party view): all checks passed"
          % (_numbers.summary, _five.summary))

# ------------------------------------------------------------------ numbers
def _numbers(load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      local GX = T.GX
      local out = {}
      local places = T:GroupExpPlaces()
      local nd, nr = 0, 0
      for i, p in ipairs(places) do
        if p.raid then nr = nr + 1 else nd = nd + 1 end
        if i > 1 and p.rec < places[i - 1].rec then return "the needed Power grows place by place: " .. p.name end
      end
      if nd < 15 or nr < 5 then return "dungeons and raids: " .. nd .. " " .. nr end
      if places[1].raid or not places[#places].raid then return "easiest first" end
      -- more players and harder difficulties need more
      local p = places[5].key
      if not (T.GroupExpNeed(p, 1, 2) < T.GroupExpNeed(p, 1, 3) and T.GroupExpNeed(p, 1, 3) < T.GroupExpNeed(p, 2, 3) and T.GroupExpNeed(p, 2, 3) < T.GroupExpNeed(p, 3, 3)) then return "need order" end
      if T.GroupExpChance(0, 100) ~= 50 or T.GroupExpChance(100, 100) ~= 970 or T.GroupExpChance(1e9, 100) ~= 970 then return "chance curve" end
      -- rewards grow with length, difficulty and players; TapCoins stay scarce
      local function coins(l, d, n) local _, c = T.GroupExpRewards(p, l, d, n); return c end
      if not (coins(1, 1, 2) < coins(5, 1, 2) and coins(5, 1, 2) < coins(5, 3, 2) and coins(5, 3, 2) < coins(5, 3, 5)) then return "rewards grow" end
      local best = coins(5, 3, 5) / 4
      if best > 40 then return "TapCoins per hour at most: " .. best end
      local xp1 = T.GroupExpRewards(p, 3, 1, 2)
      if xp1 < 300 or xp1 > 400 then return "XP for an hour: " .. xp1 end
      local _, _, rolls2, ch2 = T.GroupExpRewards(p, 5, 1, 2)
      local _, _, rolls3 = T.GroupExpRewards(p, 5, 1, 3)
      if rolls2 ~= 4 or rolls3 ~= 5 or ch2 <= 0 or ch2 > 0.5 then return "chest rolls " .. rolls2 .. " " .. rolls3 .. " " .. ch2 end
      local main, extra = T.GroupExpChests(places[#places].key, 3)
      if main ~= "heroic" or extra ~= "raid" then return "raid heroic chests" end
      main, extra = T.GroupExpChests(places[1].key, 1)
      if main ~= "pouch" or extra then return "dungeon normal chests" end
      -- the shared roll: the same on every client, spread over 0..999
      local hits = 0
      for s = 1, 4000 do local v = T.GroupExpRoll(s * 7777, "a1b2c3"); if v < 0 or v > 999 then return "roll range" end; if v < 500 then hits = hits + 1 end end
      if hits < 1700 or hits > 2300 then return "roll spread " .. hits end
      if T.GroupExpRoll(12345, "abcdef") ~= T.GroupExpRoll(12345, "abcdef") then return "same roll" end
      -- class codes round trip
      local cats = GX.CatsOf(GX.CodesOf({ "MAGE", "WARRIOR", "PRIEST" }))
      if not cats or cats[1] ~= "MAGE" or cats[3] ~= "PRIEST" then return "class codes" end
      if GX.CatsOf("MM") or GX.CatsOf("MWPD") or GX.CatsOf("X") then return "bad class codes" end
      return string.format("ok %d dungeons %d raids, at most %.1f TapCoins an hour, %d XP an hour", nd, nr, best, xp1)
    ''')
    ck(r.startswith("ok"), r)
    _numbers.summary = r[3:]

# ------------------------------------------------------------------ the main flow
def _flow(seed, load_addon):
    net = Net(load_addon, seed)
    A, B, C = net.add("Alice", cls="MAGE", level=20), net.add("Bob", cls="WARRIOR", level=20), net.add("Carol", cls="PRIEST", level=20)
    # without a group (or without addon friends) nothing starts
    ok = net.ex("Alice", 'return (TapCatForever:GroupExpInvite("dm", 1, 1, { "MAGE" }))')
    ck(not ok, "no invite without a group")
    net.group(["Alice", "Bob", "Carol"])
    ck(net.ex("Alice", "return TapCatForever:GroupExpFriends()") == 2, "Alice sees two addon friends")
    # the starter also has two solo slots: one of them busy
    net.ex("Alice", 'TapCatForever.db.classData.ROGUE.level = 20; TapCatForever.db.classData.DRUID.level = 20; TapCatForever.db.classData.HUNTER.level = 20')
    ck(net.ex("Alice", 'return (TapCatForever:StartExpedition("elwynn", { "ROGUE", "DRUID", "HUNTER" }))'), "a solo expedition")
    # a cat on a solo expedition can't go
    ok, why = net.ex("Alice", 'return TapCatForever:GroupExpInvite("dm", 1, 1, { "ROGUE" })')
    ck(not ok and "away" in why, "a solo cat can't go: %s" % why)
    a0 = net.ex("Alice", "return TapCatForever:GroupExpPower({ 'MAGE', 'PALADIN' })")
    ok = net.ex("Alice", 'return (TapCatForever:GroupExpInvite("dm", 1, 2, { "MAGE", "PALADIN" }))')
    ck(ok, "Alice invites")
    ck(net.ex("Alice", "return TapCatForever:IsOnExpedition('PALADIN') ~= nil"), "the invited cats are kept for it")
    net.pump(1)
    g1 = net.gmsgs("G1")
    ck(len(g1) == 1 and g1[0].startswith("G1;1;") and g1[0].endswith(";%d;MP" % a0), "one invite message: %s" % g1)
    for n in ("Bob", "Carol"):
        ck(net.ev(n, "_inv('state')") == "invited", "%s is invited" % n)
        ck(net.ev(n, "_prompt()"), "%s sees the prompt above the cat" % n)
        txt = net.ev(n, "TapCatForeverGroupExpPrompt.text:GetText()")
        ck(txt.startswith("Alice invites your cat: The Deadmines, 15 min, Hard") and "!" not in txt, "prompt text: %r" % txt)
    ck(not net.ev("Alice", "_prompt()"), "no prompt for the starter")
    # a second invite while one is pending: busy
    ok, why = net.ex("Bob", 'return TapCatForever:GroupExpInvite("dm", 1, 1)')
    ck(not ok and "invite" in why, "one pending invite at a time: %s" % why)
    # Bob accepts (his current cat), Carol declines: it sets off at once
    ck(net.ex("Bob", "return (TapCatForever:GroupExpAnswer(true))"), "Bob accepts")
    ck(net.ev("Bob", "_inv('state')") == "accepted" and not net.ev("Bob", "_prompt()"), "Bob's prompt goes away")
    net.pump(1)
    ck(net.ex("Carol", "return (TapCatForever:GroupExpAnswer(false))"), "Carol declines")
    net.pump(2)
    ck(net.ev("Alice", "TapCatForever.GX.out == nil"), "Alice's invite is done")
    for n in ("Alice", "Bob"):
        ck(net.ev(n, "_g('id')") is not None, "%s has the expedition" % n)
    ck(net.ev("Carol", "_g('id')") is None, "Carol stays home")
    same = ("id", "place", "len", "diff", "start", "finish", "seed", "power", "need", "chance")
    for k in same:
        ck(net.ev("Alice", "_g(%r)" % k) == net.ev("Bob", "_g(%r)" % k), "same %s on both: %s %s" % (k, net.ev("Alice", "_g(%r)" % k), net.ev("Bob", "_g(%r)" % k)))
    bp = net.ex("Bob", "return TapCatForever:GroupExpPower({ 'WARRIOR' })")
    ck(net.ev("Alice", "_g('power')") == a0 + bp, "the Power adds up: %s" % net.ev("Alice", "_g('power')"))
    ck(net.ev("Alice", "_g('finish') - _g('start')") == 15 * 60, "15 minutes")
    ck(net.ev("Bob", "#_g('players')") == 2 and net.ev("Bob", "_g('players')[1].name") == "Alice", "players")
    ck(net.ex("Bob", "return TapCatForever:IsOnExpedition('WARRIOR') ~= nil and TapCatForever:IsOnExpedition('MAGE') == nil"), "Bob's Warrior is away, his Mage isn't")
    ck(net.ex("Alice", "return #TapCatForever.db.expeditions.active") == 1, "the solo slot is untouched")
    ck(net.ex("Alice", 'return (TapCatForever:StartExpedition("westfall", { "WARLOCK", "SHAMAN", "PRIEST" }))'), "the second solo slot still works")
    ok, why = net.ex("Alice", 'return TapCatForever:StartExpedition("elwynn", { "MAGE", "WARRIOR", "PALADIN" })')
    ck(not ok, "a cat on the party expedition can't go solo")
    # the starter resends the start a couple of times; Bob keeps one copy
    net.pump(15)
    ck(len(net.gmsgs("G3")) == 3, "the start was sent three times: %d" % len(net.gmsgs("G3")))
    ck(net.ev("Bob", "TapCatForever.db.stats.groupExpeditionsSent") == 1, "Bob stored it once")
    # a second party expedition can't start while one runs
    ok, why = net.ex("Bob", 'return TapCatForever:GroupExpInvite("dm", 1, 1, { "MAGE" })')
    ck(not ok and "Claim" in why, "one at a time: %s" % why)
    # the group breaks up and Bob reloads: it keeps going
    for n in ("Alice", "Bob", "Carol"): net.ungroup(n)
    net.pump(4)
    ck(net.ev("Alice", "_g('id')") == net.ev("Bob", "_g('id')"), "still running after the group broke up")
    db = net.ex("Bob", "return _dbString()")
    del net.c["Bob"]
    B = net.add("Bob", db=db)
    ck(net.ev("Bob", "_g('id')") == net.ev("Alice", "_g('id')"), "kept through a reload")
    ck(net.ex("Bob", "return TapCatForever:GroupExpClaim()") is None, "not before it's back")
    net.pump(15 * 60)
    ck(net.ex("Alice", "return TapCatForever:GroupExpReady()"), "back home")
    backLines = [l for l in (net.ev("Bob", "_chat[%d]" % i) for i in range(1, net.ev("Bob", "#_chat") + 1)) if "Your party expedition is back" in l]
    ck(len(backLines) == 1, "told once that it's back")
    res = {}
    for n in ("Alice", "Bob"):
        cls = "MAGE" if n == "Alice" else "WARRIOR"
        xp0 = net.ev(n, "TapCatForever.db.classData.%s.xp + TapCatForever.db.classData.%s.level * 1000000" % (cls, cls))
        k0, c0 = net.ev(n, "_keys()"), net.ev(n, "TapCatForever.db.coins")
        res[n] = net.ex(n, "return TapCatForever:GroupExpClaim()")
        ck(res[n] in (True, False), "%s claims" % n)
        ck(net.ex(n, "return TapCatForever:GroupExpClaim()") is None and net.ev(n, "_g('id')") is None, "%s claims once" % n)
        xp1 = net.ev(n, "TapCatForever.db.classData.%s.xp + TapCatForever.db.classData.%s.level * 1000000" % (cls, cls))
        ck(xp1 > xp0, "%s's cat got XP" % n)
        dc = net.ev(n, "TapCatForever.db.coins") - c0
        ck(1 <= dc <= 40, "%s: a few TapCoins (%d)" % (n, dc))
        ck(net.ex(n, "return TapCatForever:ClassCount('%s', 'party')" % cls) == 1, "%s: the class achievement count" % n)
        if not res[n]: ck(net.ev(n, "_keys()") == k0, "no chest on a failure")
    ck(res["Alice"] == res["Bob"], "the same result for everyone: %s" % res)
    ck(net.ex("Alice", "return TapCatForever:ClassCount('PALADIN', 'party')") == 1, "Alice's second cat counts too")
    for n in ("Alice", "Bob"):
        net.ex(n, "TapCatForever:CheckAchievements()")
        ck(net.ex(n, "return TapCatForever:ClassAchEarned('%s', 'c_party1') ~= nil" % ("MAGE" if n == "Alice" else "WARRIOR")), "Better Together for %s" % n)
    _chat_ok(net)
    _flow.summary = "%s" % ("success" if res["Alice"] else "failure")

def _chat_ok(net):
    for n in net.c:
        for i in range(1, net.ev(n, "#_chat") + 1):
            line = net.ev(n, "_chat[%d]" % i)
            ck("!" not in line, "chat line: " + line)

# ------------------------------------------------------------------ timeouts, combat, lost and odd messages
def _edges(seed, load_addon):
    net = Net(load_addon, seed + 1)
    for n, c in (("Alice", "MAGE"), ("Bob", "WARRIOR"), ("Carol", "PRIEST")): net.add(n, cls=c, level=30)
    net.group(["Alice", "Bob", "Carol"])
    # nobody answers: after 60 s the invites run out (a decline), the prompts go and nothing starts
    net.ex("Alice", 'TapCatForever:GroupExpInvite("sm", 2, 1)'); net.pump(1)
    ck(net.ev("Bob", "_prompt()") and net.ev("Carol", "_prompt()"), "prompts up")
    net.pump(58)
    ck(net.ev("Bob", "_prompt()"), "still up at 59 s")
    net.pump(4)
    ck(not net.ev("Bob", "_prompt()") and net.ev("Bob", "_inv('result')") == "timeout", "gone after 60 s")
    ck(net.ev("Alice", "TapCatForever.GX.out == nil") and net.ev("Alice", "_g('id')") is None, "nothing started")
    ck(len([m for m in net.gmsgs("G2") if m.split(";")[3] == "n"]) == 2 and len(net.gmsgs("G4")) == 1, "two declines, one call-off")
    net.pump(30)
    # a player you declined waits a little before inviting you again
    net.ex("Bob", 'TapCatForever:GroupExpInvite("sm", 1, 1)'); net.pump(1)
    ck(net.ev("Alice", "_inv('state')") == "invited", "Bob's invite reaches Alice")
    net.ex("Alice", "TapCatForever:GroupExpAnswer(false)"); net.ex("Carol", "TapCatForever:GroupExpAnswer(false)"); net.pump(2)
    ck(net.ev("Bob", "TapCatForever.GX.out == nil"), "everyone said no: called off at once")
    net.ex("Bob", 'TapCatForever:GroupExpInvite("sm", 1, 1)'); net.pump(1)
    ck(net.ev("Alice", "_inv('state')") != "invited", "muted for a little while after a no")
    net.pump(62)
    net.pump(30)
    # combat: the prompt waits, the invite is still there; after combat it shows
    net.ex("Bob", "_combat = true")
    net.ex("Alice", 'TapCatForever:GroupExpInvite("sm", 1, 1)'); net.pump(1)
    ck(net.ev("Bob", "_inv('state')") == "invited" and net.ev("Bob", "_prompt() and TapCatForeverGroupExpPrompt.small"), "a small prompt in combat")
    net.ex("Bob", '_combat = false; _fire("PLAYER_REGEN_ENABLED")')
    ck(net.ev("Bob", "_prompt() and not TapCatForeverGroupExpPrompt.small"), "the full prompt after combat")
    # above a casino invite when both are open
    net.ex("Bob", 'local f = CreateFrame("Frame", "TapCatForeverDeathRollPrompt"); f:Show(); TapCatForever.GX.UpdatePrompt()')
    ck(net.ev("Bob", "TapCatForeverGroupExpPrompt.over") == "casino", "above the casino invite")
    net.ex("Bob", "TapCatForeverDeathRollPrompt:Hide(); TapCatForever.GX.UpdatePrompt()")
    ck(net.ev("Bob", "TapCatForeverGroupExpPrompt.over") == "cat", "above the cat again")
    # a lost start: Bob accepted but never hears G3; he asks and gets it
    net.drop = {"G3"}
    net.ex("Bob", "TapCatForever:GroupExpAnswer(true)"); net.ex("Carol", "TapCatForever:GroupExpAnswer(false)")
    net.pump(20)
    ck(net.ev("Alice", "_g('id')") is not None and net.ev("Bob", "_g('id')") is None, "Bob missed the start")
    net.drop = None
    net.pump(70)
    ck(net.ev("Bob", "_g('id')") == net.ev("Alice", "_g('id')"), "Bob asked again and got it")
    ck(len(net.gmsgs("G5")) >= 1, "asked with G5")
    gid = net.ev("Alice", "_g('id')")
    # spoofed and odd messages change nothing
    odd = [
        "G3;1;%s;sm;1;1;%d;5;Mallory:99999:M,Carol:1:I" % (gid, int(net.srv)),     # a start Carol never accepted
        "G1;2;abcdef;sm;1;1;100;M",           # another version
        "G1;1;abcdef;nowhere;1;1;100;M",      # unknown place
        "G1;1;abcdef;sm;9;1;100;M",           # unknown length
        "G1;1;abcdef;sm;1;1;-5;M",            # bad Power
        "G1;1;abcdef;sm;1;1;100;MM",          # a cat twice
        "G1;1;abcdef;sm;1;1;100",             # missing field
        "G1;1;xyz;sm;1;1;100;M",              # bad id
        "G9;1;abcdef", "G", "G1;1;abcdef;sm;1;1;100;M;extra",
    ]
    for m in odd: net.ex("Carol", "_deliver('TapCatFvr', %r, 'Alice-Forever', 'PARTY')" % m)
    net.ex("Carol", "_deliver('TapCatFvr', 'G1;1;abcdef;sm;1;1;100;M', 'Alice-Forever', 'WHISPER')")
    net.ex("Carol", "_deliver('TapCatFvr', 'G1;1;abcdef;sm;1;1;100;M', 'Mallory-Forever', 'PARTY')")   # not in the group
    net.ex("Carol", "_deliver('TapCatFvr', 'G1;1;abcdef;sm;1;1;100;M', _SECRET, 'PARTY')")
    net.ex("Carol", "_deliver('TapCatFvr', _SECRET, 'Alice-Forever', 'PARTY')")
    net.ex("Carol", "_deliver('TapCatFvr', 'G1;1;abcdef;sm;1;1;100;M', 'Carol-Forever', 'PARTY')")   # your own echo
    ck(net.ev("Carol", "_g('id')") is None and net.ev("Carol", "_inv('state')") != "invited", "odd messages ignored")
    # a start from someone who isn't the inviter is ignored
    net.ex("Bob", "TapCatForever.db.expeditions.group = nil")
    net.ex("Bob", "TapCatForever.GX.inv = { id = 'abcdef', fromBase = 'alice', from = 'Alice', place = 'sm', len = 1, diff = 1, state = 'accepted', cats = { 'WARRIOR' }, expires = GetTime() + 30, waitUntil = GetTime() + 60 }")
    net.ex("Bob", "_deliver('TapCatFvr', 'G3;1;abcdef;sm;1;1;%d;5;Alice:1:M,Bob:1:W', 'Carol-Forever', 'PARTY')" % int(net.srv))
    ck(net.ev("Bob", "_g('id')") is None, "a start from the wrong player is ignored")
    net.ex("Bob", "_deliver('TapCatFvr', 'G3;1;abcdef;sm;1;1;%d;5;Alice:1:M,Bob:1:W', 'Alice-Forever', 'PARTY')" % (int(net.srv) + 90000))
    ck(net.ev("Bob", "_g('id')") is None, "a start time far off is ignored")
    net.ex("Bob", "_deliver('TapCatFvr', 'G3;1;abcdef;sm;1;1;%d;5;Alice:1:M,Bob:1:W', 'Alice-Forever', 'PARTY')" % int(net.srv))
    ck(net.ev("Bob", "_g('id')") == "abcdef", "the right one is stored")
    # refused sends are tried again
    net.ex("Bob", "TapCatForever.db.expeditions.group = nil; TapCatForever.GX.inv = nil")
    net.ex("Alice", "TapCatForever.db.expeditions.group = nil")
    net.pump(5)
    for n in net.c: net.ex(n, "_sendResult = 9")
    ok = net.ex("Alice", 'return (TapCatForever:GroupExpInvite("sm", 1, 1))')
    ck(ok, "an invite while sending is refused")
    net.pump(1)
    ck(net.ev("Bob", "_inv('state')") != "invited", "nothing went out")
    for n in net.c: net.ex(n, "_sendResult = 0")
    net.pump(3)
    ck(net.ev("Bob", "_inv('state')") == "invited", "sent again once allowed")
    # withdraw
    ck(net.ex("Alice", "return TapCatForever:GroupExpWithdraw()"), "withdraw")
    net.pump(1)
    ck(net.ev("Bob", "_inv('result')") == "cancel" and not net.ev("Bob", "_prompt()"), "withdrawn: Bob's prompt goes")
    # test-mode fake party cats don't count as friends
    solo = Net(load_addon, seed + 2)
    solo.add("Dave")
    solo.ex("Dave", '_group = { party1 = { "Eve", "Forever" } }; _fire("GROUP_ROSTER_UPDATE"); TapCatForever.db.ui.testMode = true; TapCatForever:PartyTestInject(3)')
    solo.pump(2)
    ok, why = solo.ex("Dave", 'return TapCatForever:GroupExpInvite("sm", 1, 1)')
    ck(not ok and "Nobody else" in why, "needs another player with the addon: %s" % why)
    _chat_ok(net)

# ------------------------------------------------------------------ a full group of five, long names, raid
def _five(seed, load_addon):
    net = Net(load_addon, seed + 3)
    names = ["Abcdefghijkl", "Bcdefghijklm", "Cdefghijklmn", "Defghijklmno", "Efghijklmnop", "Fghijklmnopq"]
    classes = ["MAGE", "WARRIOR", "PRIEST", "ROGUE", "DRUID", "HUNTER"]
    for n, c in zip(names, classes): net.add(n, cls=c, level=60)
    net.group(names, raid=True)
    net.ex(names[0], 'TapCatForever:GroupExpInvite("naxx", 5, 3, { "MAGE", "PALADIN", "WARLOCK" })'); net.pump(1)
    for n in names[1:]:
        net.ex(n, "TapCatForever.GX.picked = { [TapCatForever.db.class] = true, SHAMAN = true }")
        net.ex(n, "TapCatForever:GroupExpAnswer(true)"); net.pump(0.5)
    net.pump(3)
    g3 = net.gmsgs("G3")
    ck(len(g3) >= 1 and all(len(m) <= 250 for m in g3), "the start fits in one message")
    ck(net.ev(names[0], "#_g('players')") == 5, "five players at most")
    ck(net.ev(names[5], "_g('id')") is None and net.ev(names[5], "_inv('result')") == "full", "the sixth stays home")
    ck(net.ev(names[1], "#_g('players')") == 5 and net.ev(names[1], "#_g('mine')") == 2, "two cats each")
    ck(net.ev(names[1], "_g('need')") == net.ev(names[0], "TapCatForever.GroupExpNeed('naxx', 3, 5)"), "need for five on Heroic")
    net.pump(4 * 3600, dt=60)
    chance = net.ev(names[0], "_g('chance')")
    won = [net.ex(n, "return TapCatForever:GroupExpClaim()") for n in names[:5]]
    ck(len(set(won)) == 1, "same result for five: %s" % won)
    _five.summary = "5 of 6 players on Heroic Naxxramas, %.1f%% chance, start message %d bytes" % (chance / 10.0, max(len(m) for m in g3))

# ------------------------------------------------------------------ the Party view of the Expeditions tab
def _ui(seed, load_addon):
    net = Net(load_addon, seed + 4)
    net.add("Alice", cls="MAGE", level=25); net.add("Bob", cls="WARRIOR", level=25)
    net.group(["Alice", "Bob"])
    for n in ("Alice", "Bob"):
        net.ex(n, "TapCatForever:CreateWindow(); TapCatForever.window:Show(); TapCatForever.window:SelectTab(4)")
    sw = "TapCatForever.window.expSwitch"
    ck(net.ev("Alice", sw + ".soloPage:IsShown() and not " + sw + ".partyPage:IsShown()"), "solo view first")
    net.ex("Alice", sw + ".party.scripts.OnClick(" + sw + ".party)")
    ck(net.ev("Alice", sw + ".partyPage:IsShown() and not " + sw + ".soloPage:IsShown()"), "party view")
    ui = "TapCatForever.window.partyExpUI"
    note = net.ev("Alice", ui + ".note:GetText()")
    ck("1 group member" in note, "friends counted: %s" % note)
    info = net.ev("Alice", ui + ".info:GetText()")
    ck("Power needed" in info and "XP" in info and "!" not in info, "what it needs and gives: %s" % info)
    # pick two cats, a place, length and difficulty, then invite
    net.ex("Alice", "local p = %s.picks; p[1].scripts.OnClick(p[1]); p[8].scripts.OnClick(p[8])" % ui)
    ck(net.ev("Alice", "#TapCatForever:GroupExpDefaultCats()") == 2, "two cats picked")
    net.ex("Alice", "%s.next.scripts.OnClick(%s.next); local l = %s.lenBtns[2]; l.scripts.OnClick(l); local d = %s.diffBtns[2]; d.scripts.OnClick(d)" % (ui, ui, ui, ui))
    place = net.ev("Alice", ui + ".placeName:GetText()")
    net.ex("Alice", "%s.go.scripts.OnClick(%s.go)" % (ui, ui))
    net.pump(1)
    ck(net.ev("Bob", "_inv('state')") == "invited" and net.ev("Bob", "_inv('len')") == 2 and net.ev("Bob", "_inv('diff')") == 2, "the invite from the tab")
    ck(place in net.ev("Bob", "TapCatForeverGroupExpPrompt.text:GetText()"), "the place: %s" % place)
    ck(net.ev("Alice", ui + ".inv:IsShown()") and net.ev("Alice", ui + ".inv.yes:GetText()") == "Start now", "the starter sees Start now")
    # Bob opens the party view: the invite shows there with Accept / Decline
    net.ex("Bob", sw + ".party.scripts.OnClick(" + sw + ".party)")
    ck(net.ev("Bob", ui + ".inv:IsShown()") and "Alice invites your cat" in net.ev("Bob", ui + ".inv.text:GetText()"), "invite in Bob's tab")
    net.ex("Bob", "local p = %s.picks; p[2].scripts.OnClick(p[2])" % ui)   # also send a Paladin
    net.ex("Bob", "local y = %s.inv.yes; y.scripts.OnClick(y)" % ui)
    net.pump(2)
    ck(net.ev("Bob", "_g('id')") is not None and net.ev("Bob", "#_g('mine')") == 1, "accepted from the tab: %s cats" % net.ev("Bob", "#_g('mine')"))
    net.ex("Alice", "TapCatForever.window:Refresh()")
    ck(net.ev("Alice", ui + ".slot.claim:IsShown()") and "left" in net.ev("Alice", ui + ".slot.barText:GetText()"), "the slot with its countdown")
    ck("Claim" in net.ev("Alice", ui + ".note:GetText()"), "no second invite: %s" % net.ev("Alice", ui + ".note:GetText()"))
    ck("Party" in net.ev("Bob", sw + ".party:GetText()"), "Party button")
    _chat_ok(net)

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    os.chdir(ROOT)
    import test_harness
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
    print("ok")
