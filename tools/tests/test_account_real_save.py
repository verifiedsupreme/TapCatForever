# 1.6.0: the account's cats, from a save the real 1.5.3.6 release wrote (tools/tests/fixtures/
# save_1536.lua, made by tools/tests/make_save_1536.py with the c35eabd code). In every real 1.5.x
# save the unopened chests are the character's (chars[name].keys), not the cats', and every
# character has all nine cats. Checks:
#   - every character's chests are merged when the account first logs in on 1.6.0, also those of
#     characters that never log in again: each to the cat that character was playing, stamped with
#     that cat's level, counted once (not again when the others log in), and kept in the backup
#   - an even older character: its pre-1.3.1 gear pool and its pre-1.5.1 one trade are folded in
#   - nobody loses a cosmetic: every class cat owns what any character owned (by design: before
#     1.6.0 cosmetics were the character's, so each of its nine cats gets all of them)
#   - Trade Gold earned by the businesses that weren't kept still counts toward the account total
#   - expeditions: more trips than the two rows are all kept (the page says how many more), and
#     the cats of a party expedition waiting its turn count as away
# Run on its own:  python3 tools/tests/test_account_real_save.py [seed]
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import test_deathroll as TD

def ck(c, m):
    if not c: raise AssertionError("account cats (1.5.3.6 save): " + m)

def boot(load_addon, name, db, cls):
    lua = load_addon(login=False)
    lua.execute(TD.CLIENT)
    lua.execute('_charName = "%s"; UnitClass = function() return "%s", "%s" end' % (name, cls.title(), cls))
    lua.execute("TapCatForeverDB = loadstring(%r)()" % db)
    lua.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    lua.execute("T = TapCatForever")
    return lua

# chests (all kinds) in each cat's Treasure Bag, and on the characters still
COUNT = r'''
local sv = TapCatForeverDB
local cats = rawget(sv, "cats")
local per, tot = {}, {}
for cls, cd in pairs(cats.classData) do
  per[cls] = {}
  for k, st in pairs(type(cd.chests) == "table" and cd.chests or {}) do
    for _, n in pairs(st) do per[cls][k] = (per[cls][k] or 0) + n; tot[k] = (tot[k] or 0) + n end
  end
end
local left = 0
for _, ch in pairs(sv.chars) do
  local keys = rawget(ch, "keys")
  if type(keys) == "table" then for _, v in pairs(keys) do if type(v) == "number" then left = left + v end end end
end
return per, tot, left
'''

def tbl(t):
    return {k: t[k] for k in t} if t is not None else {}

def check(seed, load_addon):
    path = os.path.join(HERE, "fixtures", "save_1536.lua")
    src = open(path).read()
    src = src[src.index("return "):]

    # what the 1.5.3.6 save holds
    S = load_addon(login=False)
    S.execute("_old = loadstring(%r)()" % src)
    keys = {}
    for name in ("Ann-Forever", "Bob-Forever", "Cid-Forever"):
        k = S.eval('_old.chars["%s"].keys' % name)
        keys[name] = {x: k[x] for x in k if k[x] > 0}
        ck(S.eval('_old.chars["%s"].classData.MAGE ~= nil and _old.chars["%s"].classData.PALADIN ~= nil' % (name, name)),
           "a 1.5.x character has all nine cats: %s" % name)
    ck(keys["Ann-Forever"].get("pouch") == 2 and keys["Bob-Forever"].get("pouch") == 3 and keys["Cid-Forever"].get("heroic", 0) >= 2,
       "the save's chests are on the characters: %r" % keys)
    want = {}
    for k in keys.values():
        for x, n in k.items(): want[x] = want.get(x, 0) + n
    levels = {name: (S.eval('_old.chars["%s"].class' % name), S.eval('_old.chars["%s"].classData[_old.chars["%s"].class].level' % (name, name)))
              for name in keys}

    # an even older character added to it: Dee, last played on 1.5.0 or older (a Warlock wearing
    # one item, the pre-1.3.1 gear pool, the pre-1.5.1 one trade, and chests of its own)
    S.execute(r'''
      local T = TapCatForever
      local wear, extra
      for _, it in ipairs(T.WORLD_POOL[4] or {}) do
        if it.q == 2 and not it.crafted and not it.retired and T:GearUsable(it, "WARLOCK") then
          if not wear and it.slot == "CHEST" then wear = it.id elseif not extra and it.slot ~= "CHEST" then extra = it.id end
        end
      end
      _ids = { wear = wear, extra = extra }
      _old.chars["Dee-Forever"] = { class = "WARLOCK", started = true,
        keys = { pouch = 4, strong = 0 },
        gear = { [wear] = 1, [extra] = 2 },
        trade = { gold = 300, lifetime = 7000, renown = 0, mats = { linen = 6 }, skill = { cloth = 40 } },
        owned = { skin_calico = 1 },
        classData = { WARLOCK = { level = 14, xp = 10, gear = { CHEST = wear }, xpCurve2 = true }, MAGE = { level = 3, xp = 0, xpCurve2 = true } } }
      -- two Mage businesses: Ann's (1,000 earned) and Bob's (5,000, kept)
      _old.chars["Ann-Forever"].classData.MAGE.trade = { gold = 10, lifetime = 1000, renown = 0, mats = { linen = 1 } }
      _old.chars["Bob-Forever"].classData.MAGE.trade = { gold = 20, lifetime = 5000, renown = 0, mats = { linen = 2 } }
    ''')
    ids = {k: S.eval("_ids.%s" % k) for k in ("wear", "extra")}
    ck(all(ids.values()), "Dee's test gear: %r" % ids)
    S.execute(TD.CLIENT)  # (the serializer)
    db = "return " + S.eval("_ser(_old)")
    want["pouch"] = want.get("pouch", 0) + 4
    # (the login itself pays some chests: class achievements the old save earned, the care package;
    # the same save with no chests on any character says how many)
    S.execute("for _, ch in pairs(_old.chars) do ch.keys = {} end")
    Z = boot(load_addon, "Ann", "return " + S.eval("_ser(_old)"), "MAGE")
    Z.execute("T = TapCatForever")
    zper, base, _ = Z.execute(COUNT)
    zper = {c: tbl(zper[c]) for c in zper}
    base = tbl(base)
    for k, n in want.items(): base[k] = base.get(k, 0) + n
    want = base

    # --- Ann logs in first on 1.6.0: every character is merged, Bob, Cid and Dee too
    A = boot(load_addon, "Ann", db, "MAGE")
    per, tot, left = A.execute(COUNT)
    per = {c: tbl(per[c]) for c in per}
    tot = tbl(tot)
    ck(all(tot.get(k, 0) == n for k, n in want.items()) and sum(tot.values()) == sum(want.values()),
       "every character's chests are in the cats' Treasure Bags, once: %r, the save had %r" % (tot, want))
    ck(left == 0, "no chest left on a character: %d" % left)
    # each to the cat its character was playing, stamped with that cat's level
    def mine(cls, k): return per[cls].get(k, 0) - zper.get(cls, {}).get(k, 0)
    ck(mine("MAGE", "pouch") == keys["Ann-Forever"]["pouch"] + keys["Bob-Forever"]["pouch"],
       "Ann's and Bob's pouches to the Mage: %r" % per["MAGE"])
    ck(mine("HUNTER", "heroic") == keys["Cid-Forever"]["heroic"], "Cid's Heroic Caches to the Hunter it plays: %r" % per["HUNTER"])
    ck(mine("WARLOCK", "pouch") == 4, "Dee's pouches to its Warlock: %r" % per["WARLOCK"])
    annLv, bobLv = levels["Ann-Forever"][1], levels["Bob-Forever"][1]
    stamp = lambda L, lv: L.eval("T:CD('MAGE').chests.pouch and T:CD('MAGE').chests.pouch[%d] or 0" % lv)
    ck(annLv != bobLv and stamp(A, annLv) - stamp(Z, annLv) == 2 and stamp(A, bobLv) - stamp(Z, bobLv) == 3,
       "stamped with each character's own cat level (Ann %d, Bob %d)" % (annLv, bobLv))
    ck(A.eval("T:CD('WARLOCK').chests.pouch[14]") - Z.eval("T:CD('WARLOCK').chests.pouch and T:CD('WARLOCK').chests.pouch[14] or 0") == 4, "Dee's stamped 14")
    ck(A.eval('TapCatForeverDB.preAccountBackup["Cid-Forever"].keys.heroic') == keys["Cid-Forever"]["heroic"]
       and A.eval('TapCatForeverDB.preAccountBackup["Dee-Forever"].gear ~= nil and TapCatForeverDB.preAccountBackup["Dee-Forever"].trade.lifetime') == 7000,
       "the backup keeps the old chests, gear pool and trade")
    # Dee's gear pool: the worn copy stays with the wearer, the rest to the cat it played
    ck(A.eval("T:Bag('WARLOCK')[%d]" % ids["wear"]) == 1 and A.eval("T:Bag('WARLOCK')[%d]" % ids["extra"]) == 2 and A.eval("T:CD('WARLOCK').gear.CHEST") == ids["wear"],
       "Dee's old gear pool: %r %r" % (A.eval("T:Bag('WARLOCK')[%d]" % ids["wear"]), A.eval("T:Bag('WARLOCK')[%d]" % ids["extra"])))
    ck(A.eval('rawget(TapCatForeverDB.chars["Dee-Forever"], "gear") == nil and rawget(TapCatForeverDB.chars["Dee-Forever"], "trade") == nil'), "Dee's old pool and trade folded in")
    # Dee's one trade went to its cats (Warlock's family), and nothing was lost
    life, _ = A.execute("return T:TradeTotals()")
    ck(life >= 1000 + 5000 + 7000, "Trade Gold earned on the account counts every business: %r" % life)
    ck(A.eval("T:ProfState('MAGE').lifetime") == 5000 and A.eval("T:ProfState('MAGE').lifetimeMerged") == 1000,
       "the Mage keeps Bob's business; Ann's 1,000 still counts toward the total, not its unlocks")
    ck(A.eval("T:ProfState('MAGE').mats.linen") == 3, "materials added up")
    # cosmetics: every class cat owns what any character owned (nobody loses anything)
    for cls in ("MAGE", "PALADIN", "HUNTER", "WARLOCK"):
        ck(A.eval("T:Owned('%s').skin_lion and T:Owned('%s').skin_frostsaber and T:Owned('%s').skin_diamond and true or false" % (cls, cls, cls)),
           "the %s cat owns every character's cosmetics" % cls)
    ck(A.eval("T:Owned('WARLOCK').skin_calico and T:Owned('MAGE').skin_calico and true or false"), "and Dee's, on the cats Dee had")
    db2 = A.eval("_ser(TapCatForeverDB)")

    # --- Bob and Cid log in later: nothing is added again
    B = boot(load_addon, "Bob", "return " + db2, "MAGE")
    per2, tot2, _ = B.execute(COUNT)
    ck(tbl(tot2) == tot, "Bob's login adds no chests: %r vs %r" % (tbl(tot2), tot))
    ck(B.eval('TapCatForeverDB.preAccountBackup["Bob-Forever (2)"] == nil'), "and isn't merged twice")
    db3 = B.eval("_ser(TapCatForeverDB)")
    C = boot(load_addon, "Cid", "return " + db3, "HUNTER")
    _, tot3, _ = C.execute(COUNT)
    ck(tbl(tot3) == tot, "Cid's login adds no chests: %r" % tbl(tot3))
    ck(C.eval("T:ChestsOf('heroic')") == keys["Cid-Forever"]["heroic"], "Cid opens his Heroic Caches from the Hunter's Treasure Bag")

    # --- expeditions: four solo trips merged (two rows), and a party expedition waiting its turn
    C.execute(r'''
      local st = T.db.expeditions
      st.active = {}
      local now = time()
      local function trip(f, m) table.insert(st.active, { key = "elwynn", members = m, start = now - 100, finish = now + f, power = 1, chance = 1 }) end
      trip(500, { "MAGE", "WARRIOR", "PRIEST" }); trip(-5, { "ROGUE", "DRUID", "SHAMAN" })
      trip(900, { "MAGE", "PALADIN", "PRIEST" }); trip(50, { "WARLOCK", "DRUID", "ROGUE" })
      st.group = nil
      st.groupQueue = { { id = "cccccc", place = "dm", len = 1, diff = 1, start = now, finish = now + 600, seed = 1, players = {}, mine = { "HUNTER" }, chance = 1 } }
      _busy = T:IsOnExpedition("HUNTER") and true or false
      T:CreateWindow(); T.window:Show(); T.window:SelectTab(4); T.window:Refresh()
      _more = nil
      for _, f in ipairs(_frames) do
        if f.kind == "FontString" and type(f.text) == "string" and f.text:find("more under way", 1, true) and f:IsShown() then _more = f.text end
      end
    ''')
    ck(C.eval("_busy"), "the cats of a party expedition waiting its turn count as away")
    ck(C.eval("_more") == "2 more under way, shown when a row is free", "the page says 2 more trips: %r" % C.eval("_more"))
    ck(C.eval("#T.db.expeditions.active") == 4, "all four trips kept")
    # the trip that is back has a row: claim it from the page's first row
    C.execute(r'''
      _claimed = nil
      local ce = T.ClaimExpedition
      T.ClaimExpedition = function(self, i) _claimed = i end
      for _, f in ipairs(_frames) do
        if f.kind == "Button" and f.text == "Claim" and f:IsShown() and f.isEnabled ~= false then
          local ok = pcall(f.scripts.OnClick, f)
          if _claimed then break end
        end
      end
      T.ClaimExpedition = ce
    ''')
    ck(C.eval("_claimed") == 2, "the finished trip (the second saved) is on a row and can be claimed: %r" % C.eval("_claimed"))
    print("account cats from a real 1.5.3.6 save section (every character's chests merged once to the cat it played, with its level; "
          "the older gear pool and trade folded in; every cat keeps every character's cosmetics; merged Trade Gold still counts; "
          "extra expeditions kept and shown, queued party cats away): all checks passed")

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(HERE, ".."))
    import test_harness
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
