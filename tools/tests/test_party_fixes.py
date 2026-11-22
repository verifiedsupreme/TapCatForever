# Party track review fixes (PartyExpeditions.lua, UI_PartyExpeditions.lua, ClassAchievements.lua):
# - a start the group can't hear (sends refused for 30 s to 3 minutes, as in combat in an instance)
#   never splits the group: the starter only saves it once the start went out, and an accepted
#   player still takes a late start; past the limit nobody has it
# - in combat the invite shows as a small box (it never runs out unseen) and can be accepted
# - player names in a start are cleaned, the starter must come first, a player twice is refused
# - the chance curve starts at 5% (no Power can't farm Heroic raids)
# - members on an older version (no "seen" answer) don't hold an invite up for 60 seconds
# - the prompt sits below a casino invite that sits below the cat
# - new cat picks after accepting go out once, after the clicking stops
# - chests name the cat they are for (party expeditions: the first cat that went)
# - class achievement text: "Cosmetic only" label, no "(s)" plurals, the open-world zone names,
#   the Normal difficulty tooltip; the stat cache gives the same numbers
# Run on its own:  python3 tools/tests/test_party_fixes.py [seed]
import os, sys, time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_party_expeditions as P

ck = P.ck

class OldNet(P.Net):
    """Clients listed in .old run an older version: they never hear G messages."""
    def __init__(self, *a):
        P.Net.__init__(self, *a)
        self.old = set()
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
                    if self.drop and msg[:2] in self.drop: continue
                    for other, olua in self.c.items():
                        if other in self.old and msg[:1] == "G": continue
                        if self.grouped(other) and self.grouped(name):
                            olua.globals()._deliver(p, msg, name + "-Forever", ch)

def check(seed, load_addon):
    late = _refused(seed, load_addon)
    _combat(seed, load_addon)
    _names(seed, load_addon)
    _oldClients(seed, load_addon)
    _misc(seed, load_addon)
    ms = _classach(load_addon)
    print("party fixes section (a start refused for 30 s to 3 min never splits the group, %s; small invite in combat; clean names; 5%% floor; older members don't hold it up; casino placement; one repick message; chest owner; class achievement text; class check %.2f ms): all checks passed" % (late, ms))

def three(load_addon, seed, cls=("MAGE", "WARRIOR", "PRIEST"), net_cls=P.Net):
    net = net_cls(load_addon, seed)
    for n, c in zip(("Alice", "Bob", "Carol"), cls): net.add(n, cls=c, level=20)
    net.group(["Alice", "Bob", "Carol"])
    return net

# ------------------------------------------------------------------ refused sends around the start
def _refused(seed, load_addon):
    res = []
    # everyone's sends refused from t=51 (the reviewer's case), Carol never answers
    for refuse in (30, 60, 90, 150):
        net = three(load_addon, seed + refuse)
        net.ex("Alice", 'TapCatForever:GroupExpInvite("dm", 1, 1, { "MAGE" })'); net.pump(1)
        net.ex("Bob", "TapCatForever:GroupExpAnswer(true)")
        net.pump(50)
        for n in net.c: net.ex(n, "_sendResult = 9")
        net.pump(refuse)
        for n in net.c: net.ex(n, "_sendResult = 0")
        net.pump(120)
        a, b = net.ev("Alice", "_g('id')"), net.ev("Bob", "_g('id')")
        ck(a is not None and a == b, "refused %d s: both have it (%s / %s)" % (refuse, a, b))
        ck(net.ev("Bob", "#_g('players')") == 2 and net.ev("Bob", "_g('players')[2].name") == "Bob", "Bob is in the list")
        ck(net.ev("Alice", "_g('start')") == net.ev("Bob", "_g('start')") and net.ev("Alice", "_g('seed')") == net.ev("Bob", "_g('seed')"), "same start and seed")
    # only the starter's sends refused for 2 minutes after the invite ran out: Bob stopped waiting,
    # then takes the late start
    net = three(load_addon, seed + 7)
    net.ex("Alice", 'TapCatForever:GroupExpInvite("dm", 1, 1, { "MAGE" })'); net.pump(1)
    net.ex("Bob", "TapCatForever:GroupExpAnswer(true)")
    net.pump(55)
    net.ex("Alice", "_sendResult = 9")
    net.pump(120)
    ck(net.ev("Alice", "_g('id')") is None and net.ev("Alice", "TapCatForever.GX.out ~= nil"), "the starter waits, saves nothing")
    ck(net.ev("Bob", "_inv('result')") == "nostart", "Bob stopped waiting: %s" % net.ev("Bob", "_inv('result')"))
    # Start now while refused: a clear answer, nothing saved
    ok, why, wait = net.ex("Alice", "return TapCatForever:GroupExpStartNow()")
    ck(not ok and wait and "!" not in why and "as soon as" in why, "Start now while refused: %s" % why)
    net.ex("Alice", "_sendResult = 0")
    net.pump(5)
    ck(net.ev("Alice", "_g('id')") is not None and net.ev("Alice", "_g('id')") == net.ev("Bob", "_g('id')"), "Bob took the late start")
    ck(net.ev("Bob", "TapCatForever:IsOnExpedition('WARRIOR') ~= nil"), "Bob's cat went")
    # refused past the limit: the starter gives up and nobody has it
    net = three(load_addon, seed + 8)
    net.ex("Alice", 'TapCatForever:GroupExpInvite("dm", 1, 1, { "MAGE" })'); net.pump(1)
    net.ex("Bob", "TapCatForever:GroupExpAnswer(true)")
    net.pump(55)
    for n in net.c: net.ex(n, "_sendResult = 9")
    net.pump(320)
    ck(net.ev("Alice", "TapCatForever.GX.out == nil") and net.ev("Alice", "_g('id')") is None, "the starter gave up")
    for n in net.c: net.ex(n, "_sendResult = 0")
    net.pump(30)
    ck(net.ev("Bob", "_g('id')") is None and net.ev("Alice", "_g('id')") is None, "nobody has it")
    ck(net.ev("Bob", "TapCatForever:IsOnExpedition('WARRIOR') == nil"), "Bob's cat is free again")
    P._chat_ok(net)
    return "late start taken after 2 min, given up after 4"

# ------------------------------------------------------------------ the invite in combat
def _combat(seed, load_addon):
    net = three(load_addon, seed + 20)
    net.ex("Bob", "_combat = true")
    net.ex("Alice", 'TapCatForever:GroupExpInvite("dm", 1, 1, { "MAGE" })'); net.pump(1)
    ck(net.ev("Bob", "_prompt() and TapCatForeverGroupExpPrompt.small"), "a small invite in combat")
    txt = net.ev("Bob", "TapCatForeverGroupExpPrompt.text:GetText()")
    ck(txt == "Alice invites your cat", "short text: %r" % txt)
    net.pump(20)
    ck(net.ev("Bob", "_prompt()"), "still there in combat")
    net.ex("Bob", "local y = TapCatForeverGroupExpPrompt.yes; y.scripts.OnClick(y)")
    ck(net.ev("Bob", "_inv('state')") == "accepted" and not net.ev("Bob", "_prompt()"), "accepted in combat")
    net.ex("Carol", "TapCatForever:GroupExpAnswer(false)")
    net.pump(3)
    ck(net.ev("Bob", "_g('id')") is not None and net.ev("Bob", "_g('id')") == net.ev("Alice", "_g('id')"), "set off with Bob")

# ------------------------------------------------------------------ names in a start
def _names(seed, load_addon):
    net = three(load_addon, seed + 30)
    net.ex("Alice", 'TapCatForever:GroupExpInvite("dm", 1, 1, { "MAGE" })'); net.pump(1)
    gid = net.ev("Bob", "_inv('id')")
    net.ex("Bob", "TapCatForever:GroupExpAnswer(true)")
    net.drop = {"G3"}
    net.ex("Carol", "TapCatForever:GroupExpAnswer(false)")
    net.pump(2)
    net.drop = None
    srv = int(net.srv)
    bad = [
        "G3;1;%s;dm;1;1;%d;5;|cffff0000Evil|r|TX|t:5000:M,Bob:100:W" % (gid, srv),     # the starter isn't first
        "G3;1;%s;dm;1;1;%d;5;Bob:100:W,Alice:5000:M" % (gid, srv),                     # the starter isn't first
        "G3;1;%s;dm;1;1;%d;5;Alice:5000:M,Bob:100:W,Bob:100:W" % (gid, srv),           # a player twice
        "G3;1;%s;dm;1;1;%d;5;Alice:5000:M,|r:100:W,Bob:100:W" % (gid, srv),            # an empty name
    ]
    for m in bad:
        net.ex("Bob", "_deliver('TapCatFvr', %r, 'Alice-Forever', 'PARTY')" % m)
        ck(net.ev("Bob", "_g('id')") is None, "refused: %s" % m)
    m = "G3;1;%s;dm;1;1;%d;5;Alice:5000:M,|cffff0000Ev|Hx|hil|r|TX|t:1:R,Bob:100:W" % (gid, srv)
    net.ex("Bob", "_deliver('TapCatFvr', %r, 'Alice-Forever', 'PARTY')" % m)
    ck(net.ev("Bob", "_g('id')") == gid, "a start with a messy name is stored")
    names = [net.ev("Bob", "_g('players')[%d].name" % i) for i in (1, 2, 3)]
    ck(names == ["Alice", "Evil", "Bob"], "names cleaned: %s" % names)
    last = net.ev("Bob", "_chat[#_chat]")
    ck("|c" not in last.split("Your party expedition")[-1].replace("|cffffd100", "").replace("|r", "") and "Evil" in last, "chat line: %r" % last)

# ------------------------------------------------------------------ members on an older version
def _oldClients(seed, load_addon):
    net = OldNet(load_addon, seed + 40)
    for n, c in (("Alice", "MAGE"), ("Bob", "WARRIOR"), ("Oldie", "PRIEST")): net.add(n, cls=c, level=20)
    net.old.add("Oldie")
    net.group(["Alice", "Bob", "Oldie"])
    ck(net.ex("Alice", "return TapCatForever:GroupExpFriends()") == 2, "Oldie said hello")
    net.ex("Alice", 'TapCatForever:GroupExpInvite("dm", 1, 1, { "MAGE" })'); net.pump(1)
    net.ex("Bob", "TapCatForever:GroupExpAnswer(true)")
    net.pump(6)
    ck(net.ev("Alice", "_g('id')") is not None and net.ev("Bob", "_g('id')") == net.ev("Alice", "_g('id')"), "it set off without waiting for Oldie")
    # only an older member in the group: called off in a few seconds, with a reason
    net2 = OldNet(load_addon, seed + 41)
    for n, c in (("Alice", "MAGE"), ("Oldie", "PRIEST")): net2.add(n, cls=c, level=20)
    net2.old.add("Oldie")
    net2.group(["Alice", "Oldie"])
    net2.ex("Alice", 'TapCatForever:GroupExpInvite("dm", 1, 1, { "MAGE" })')
    net2.pump(7)
    ck(net2.ev("Alice", "TapCatForever.GX.out == nil"), "called off without waiting a minute")
    last = net2.ev("Alice", "_chat[#_chat]")
    ck("newest TapCatForever" in last and "!" not in last, "why: %r" % last)

# ------------------------------------------------------------------ chance floor, placement, repick, chest owner, Normal tooltip
def _misc(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      if T.GroupExpChance(0, 46875) ~= 50 then return "no Power: " .. T.GroupExpChance(0, 46875) end
      if T.GroupExpChance(46875, 46875) ~= 970 then return "at the need" end
      local half = T.GroupExpChance(50, 100)
      if half ~= 280 then return "half the Power: " .. half end
      return "ok"
    ''')
    ck(r == "ok", r)
    net = three(load_addon, seed + 50)
    # the prompt below a casino invite that sits below the cat
    net.ex("Alice", 'TapCatForever:GroupExpInvite("dm", 1, 1, { "MAGE" })'); net.pump(1)
    net.ex("Bob", 'local f = CreateFrame("Frame", "TapCatForeverDeathRollPrompt"); f:Show(); f.GetTop = function() return 500 end; '
                  'TapCatForever.hud:Show(); TapCatForever.hud.GetTop = function() return 700 end; TapCatForever.GX.UpdatePrompt()')
    ck(net.ev("Bob", "TapCatForeverGroupExpPrompt.over") == "casino-below", "below the casino invite: %s" % net.ev("Bob", "TapCatForeverGroupExpPrompt.over"))
    net.ex("Bob", 'TapCatForeverDeathRollPrompt.GetTop = function() return 900 end; TapCatForever.GX.UpdatePrompt()')
    ck(net.ev("Bob", "TapCatForeverGroupExpPrompt.over") == "casino", "above the casino invite")
    net.ex("Bob", "TapCatForeverDeathRollPrompt:Hide()")
    # after accepting, quick new picks in the Party view go out as one answer
    net.ex("Bob", "TapCatForever:CreateWindow(); TapCatForever.window:Show(); TapCatForever.window:SelectTab(4)")
    net.ex("Bob", "TapCatForever:GroupExpAnswer(true)"); net.pump(0.5)
    n0 = len([m for m in net.gmsgs("G2") if m.split(";")[3] == "y"])
    ui = "TapCatForever.window.partyExpUI"
    net.ex("Bob", "local p = %s.picks; p[1].scripts.OnClick(p[1]); p[2].scripts.OnClick(p[2]); p[3].scripts.OnClick(p[3])" % ui)
    net.pump(0.5)
    ck(len([m for m in net.gmsgs("G2") if m.split(";")[3] == "y"]) == n0, "no answer while clicking")
    net.pump(2)
    ys = [m for m in net.gmsgs("G2") if m.split(";")[3] == "y"]
    ck(len(ys) == n0 + 1 and ys[-1].endswith(";WPH"), "one answer with the new cats: %s" % ys[n0:])
    # the Normal difficulty tooltip
    net.ex("Bob", "_tt = {}; GameTooltip.AddLine = function(_, t) table.insert(_tt, t) end")
    net.ex("Bob", "local b = %s.diffBtns[1]; b.scripts.OnEnter(b)" % ui)
    lines = list(net.ev("Bob", "_tt").values())
    ck(any("usual Power" in l for l in lines) and not any("the the" in l for l in lines), "Normal tooltip: %s" % lines)
    # chests go to the first cat that went (4th argument of AwardChest)
    net.ex("Carol", "TapCatForever:GroupExpAnswer(false)"); net.pump(3)
    ck(net.ev("Bob", "_g('id')") is not None, "it set off")
    net.ex("Bob", "TapCatForever.GX.picked = {}")
    net.pump(15 * 60, dt=30)
    net.ex("Bob", "_owners = {}; local o = TapCatForever.AwardChest; TapCatForever.AwardChest = function(s, k, src, f, cls) table.insert(_owners, cls or 'none'); return o(s, k, src, f, cls) end")
    net.ex("Bob", "TapCatForever.db.expeditions.group.chance = 1000; TapCatForever.GroupExpRewards = function() return 10, 5, 2, 1, 0 end")
    mine = net.ev("Bob", "_g('mine')[1]")
    ck(net.ex("Bob", "return TapCatForever:GroupExpClaim()") is True, "a win")
    owners = list(net.ev("Bob", "_owners").values())
    ck(len(owners) >= 1 and all(o == mine for o in owners), "chests for %s: %s" % (mine, owners))

# ------------------------------------------------------------------ class achievement text and the stat cache
def _classach(load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      for _, a in ipairs(T.CLASS_ACHIEVEMENTS) do
        local d = T:ClassAchDesc(a, "MAGE")
        if d:find("(s)", 1, true) or d:find("!", 1, true) then return "plural or mark: " .. d end
      end
      if T:ClassAchDesc(T.CLASS_ACH_BY_ID.c_dung1, "MAGE") ~= "Clear an Adventure dungeon." then return "one dungeon" end
      if T:ClassAchDesc(T.CLASS_ACH_BY_ID.c_dung5, "MAGE") ~= "Clear 5 Adventure dungeons." then return "five dungeons" end
      if not T:ClassAchDesc(T.CLASS_ACH_BY_ID.c_exp10, "MAGE"):find("solo or party", 1, true) then return "expeditions text" end
      -- the open-world zones by name, and the goal is all of them
      local names, n = {}, 0
      for _, t in ipairs(T.TIERS) do
        if not t.raid and not T.IsDungeonTier(t) then n = n + 1; names[#names + 1] = t.name end
      end
      local w = T.CLASS_ACH_BY_ID.c_world
      if T:ClassAchGoal(w, "MAGE") ~= n then return "world goal" end
      for _, nm in ipairs(names) do if not T:ClassAchDesc(w, "MAGE"):find(nm, 1, true) then return "world text: " .. T:ClassAchDesc(w, "MAGE") end end
      -- the cache gives the same numbers as reading each stat
      local cd = T.db.classData.MAGE
      cd.adv.best = 1999
      local cache = {}
      for _, s in ipairs({ "level", "world", "dungeons", "raids", "abilities", "rareSet", "epicSet", "craftSkill", "craftedWorn", "exp", "party" }) do
        if T:ClassStat(s, "MAGE", cache) ~= T:ClassStatRaw(s, "MAGE") then return "cache " .. s end
      end
      -- Top of the Class: "Cosmetic only" in the row, the chat line and the tooltip
      T.db.classData.PRIEST.level = 60
      T.db.ui.chat = true
      T:CheckClassAchievements()
      local said
      for _, l in ipairs(_chat) do if l:find("Top of the Class", 1, true) and l:find("achievement earned", 1, true) then said = l end end
      if not said or not said:find("(Cosmetic only)", 1, true) then return "chat: " .. tostring(said) end
      T:CreateWindow(); T.window:Show()
      T.window.achMode = "class"; T.window.achClass = "PRIEST"; T.window.acScroll = 5
      T.window:RefreshAchievements()
      local row
      for _, r in ipairs(T.window.achUI.rows) do if r:IsShown() and (r.name:GetText() or ""):find("Top of the Class", 1, true) then row = r end end
      if not row then return "no level 60 row" end
      if not row.reward:GetText():find("Cosmetic only", 1, true) then return "row: " .. row.reward:GetText() end
      _tt = {}
      GameTooltip.AddLine = function(_, t) table.insert(_tt, t) end
      row.scripts.OnEnter(row)
      local tip = table.concat(_tt, " | ")
      if not tip:find("Cosmetic only", 1, true) then return "tooltip: " .. tip end
      return "ok"
    ''')
    ck(r == "ok", "class achievements: %s" % r)
    # how long one check takes on a fresh character (it runs whenever something changed)
    lua = load_addon()
    lua.execute("TapCatForever:CheckClassAchievements(true)")
    t0 = time.perf_counter()
    for _ in range(200): lua.execute("TapCatForever:CheckClassAchievements(true)")
    ms = (time.perf_counter() - t0) / 200 * 1000
    ck(ms < 5, "class check %.2f ms" % ms)
    return ms

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    os.chdir(ROOT)
    import test_harness
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
    print("ok")
