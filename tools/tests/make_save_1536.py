# Writes tools/tests/fixtures/save_1536.lua: a TapCatForeverDB saved by the real 1.5.3.6 release
# (commit c35eabd, taken with git archive and run with its own test harness), for
# tools/tests/test_account_real_save.py. Three characters play in turn on one account:
#   Ann  - Mage (40,000 XP) and a Warrior (20,000 XP); 2 Small Pouches and 1 Strong Box; lion skin, snow fur
#   Bob  - Mage (20,000 XP); 3 Small Pouches; frostsaber and lion skins
#   Cid  - Hunter (30,000 XP) and a Mage (15,000 XP); 2 Heroic Caches and 3 Strong Boxes; diamond skin
# Each also gets four green items its cat can wear and 1,000 TapCoins. 1.5.x saves every
# character's chests in chars[name].keys and all nine cats in chars[name].classData.
# Run:  python3 tools/tests/make_save_1536.py
import os, sys, subprocess, tempfile, tarfile, io, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
REV = "c35eabd"

SER = r'''
function _ser(v, ind)
  local t = type(v)
  if t == "string" then return string.format("%q", v) end
  if t == "number" or t == "boolean" then return tostring(v) end
  if t ~= "table" then return "nil" end
  local keys = {}
  for k, x in next, v do
    local tk = type(k)
    if (tk == "string" or tk == "number") and type(x) ~= "function" then keys[#keys + 1] = k end
  end
  table.sort(keys, function(a, b)
    if type(a) ~= type(b) then return type(a) == "number" end
    return a < b
  end)
  local parts = {}
  for _, k in ipairs(keys) do parts[#parts + 1] = "[" .. _ser(k) .. "]=" .. _ser(v[k]) end
  return "{" .. table.concat(parts, ",") .. "}"
end
function _dbString() setmetatable(TapCatForeverDB, nil); return _ser(TapCatForeverDB) end
'''

PLAY = r'''
local cls, xp, chests, skins, seed = ...
local T = TapCatForever
math.randomseed(seed)
T.Print = function() end
T:SetClass(cls)
T:AddClassXP(cls, xp)
local n = 0
for _, it in ipairs(T.WORLD_POOL[4] or {}) do
  if it.q == 2 and T:GearUsable(it, cls) and n < 4 then n = n + 1; T:GrantGear(it, "test") end
end
for k, c in pairs(chests) do for i = 1, c do T:AwardChest(k, "test") end end
for _, id in ipairs(skins) do T:GrantItem(T.ITEMS[id], "test") end
T.db.coins = T.db.coins + 1000
'''

def old_harness(dst):
    data = subprocess.check_output(["git", "-C", ROOT, "archive", REV])
    tarfile.open(fileobj=io.BytesIO(data)).extractall(dst)
    spec = importlib.util.spec_from_file_location("harness_1536", os.path.join(dst, "tools", "test_harness.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def play(H, name, cls, db, xp, chests, skins, seed, also=None):
    lua = H.load_addon(login=False)
    lua.execute(SER)
    lua.execute('_charName = "%s"; UnitClass = function() return "%s", "%s" end' % (name, cls.title(), cls))
    if db:
        lua.execute("TapCatForeverDB = loadstring(%r)()" % ("return " + db))
    lua.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    f = lua.execute("return function(...) local f = assert(loadstring([==[" + PLAY + "]==])); return f(...) end")
    f(cls, xp, lua.table_from(chests), lua.table_from(skins), seed)
    if also:
        f(also, xp // 2, lua.table_from({}), lua.table_from([]), seed + 1)
        lua.execute('TapCatForever:SetClass("%s")' % cls)
    return lua.eval("_dbString()")

def main():
    with tempfile.TemporaryDirectory() as tmp:
        H = old_harness(tmp)
        db = None
        db = play(H, "Ann", "MAGE", db, 40000, {"pouch": 2, "strong": 1}, ["skin_lion", "fur_snow"], 1, also="WARRIOR")
        db = play(H, "Bob", "MAGE", db, 20000, {"pouch": 3}, ["skin_frostsaber", "skin_lion"], 2)
        db = play(H, "Cid", "HUNTER", db, 30000, {"heroic": 2, "strong": 3}, ["skin_diamond"], 3, also="MAGE")
    os.makedirs(os.path.join(HERE, "fixtures"), exist_ok=True)
    out = os.path.join(HERE, "fixtures", "save_1536.lua")
    with open(out, "w") as fh:
        fh.write("-- TapCatForeverDB saved by TapCatForever 1.5.3.6 (" + REV + "): made by tools/tests/make_save_1536.py\n")
        fh.write("return " + db + "\n")
    print("wrote", os.path.relpath(out, ROOT), len(db), "bytes")

if __name__ == "__main__":
    main()
