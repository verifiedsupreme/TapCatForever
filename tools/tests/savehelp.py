# Helpers for the save migration tests (not a test section itself).
# AS_OLD: Lua that turns the logged-in save into what a 1.5.x save looked like for this character:
# its cats (classData, loadouts) under TapCatForeverDB.chars[name], one collection of cosmetics
# (char.owned), one look for every cat (char.look, no char.looks), no account cats.
# _as15(class) uses that class's look as the shared one (default: the cat being played).
AS_OLD = r'''
function _as15(lookClass)
  local T = TapCatForever
  local sv = TapCatForeverDB
  local db = T.db
  local cls = db.class
  local cats = rawget(sv, "cats")
  local char = T.charData
  local owned = {}
  for _, cd in pairs(cats.classData) do
    for id, n in pairs(cd.owned or {}) do owned[id] = math.max(owned[id] or 0, n) end
    cd.owned, cd.itemSources = nil, nil
  end
  local look = cats.looks[lookClass or cls] or {}
  setmetatable(sv, nil)
  char.classData, char.loadouts, char.expeditions = cats.classData, cats.loadouts, cats.expeditions
  char.owned = owned
  char.look = { fur = look.fur, pattern = look.pattern, skin = look.skin, tap = look.tap, tapSet = look.tapSet }
  char.looks = nil
  char.class = cls
  sv.cats = nil
  sv.preAccountBackup = nil
end
'''
