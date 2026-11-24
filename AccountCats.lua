-- TapCatForever: the nine class cats belong to the whole account (1.6.0).
-- Any character of a class plays the account's cat of that class: its level and XP, gear and bag,
-- Treasure Bag, professions, look and cosmetics, Adventure (with farming), abilities and
-- expeditions. They live in TapCatForeverDB.cats (classData, loadouts, looks, expeditions); Core.lua
-- points db.classData, db.loadouts, db.looks and db.expeditions there.
--
-- Still per WoW character (TapCatForeverDB.chars[name]): which cat it is playing (db.class), the
-- Daily Wares in the Shop, real WoW dungeon and raid chest limits and the run in progress
-- (dungeonPaid, dungeonRun), real WoW boss kill counts (realBosses), the once-a-day professions
-- glitch (profGlitchDay) and the 1.5.4 care package flag. TapCoins, quests, achievements, class
-- achievements, level-up rewards and settings (the screen cat's place too) were already shared.
--
-- Merging (once per account, and again for any character that comes with cats of its own, such as
-- one saved by an older version later): for each class the cat with the highest level (then the
-- most XP; the account's own cat on a full tie) is the base and keeps its level, XP, worn gear,
-- look, cosmetic slots, Adventure place and abilities. The other cats of that class add: bag items
-- (their worn gear goes to the bag), unopened chests, cosmetics and their sources, Adventure kill
-- counts and first kills, the furthest stage reached and every ability learned. Professions: the
-- business with the most Trade Gold earned is kept, every skill takes the highest, Renown the
-- highest, materials are added up and unlocks, milestones and upgrades kept by any stay kept.
-- Expeditions under way all keep going. Unopened chests, which 1.5.3 kept per character
-- (chars[name].keys), go to the cat that character was playing first, stamped with its level, so
-- an alt that never logs in again loses none (also the pre-1.3.1 gear pool and the pre-1.5.1
-- trade: foldCharThings). A copy of each character's old cats stays in
-- TapCatForeverDB.preAccountBackup[name].
local ADDON, TCF = ...
local floor, min, max = math.floor, math.min, math.max

-- the per-character keys that held the cats before 1.6.0
TCF.CHAR_CAT_KEYS = { "classData", "loadouts", "look", "looks", "expeditions", "owned", "itemSources" }
local LOOK_FIELDS = { "fur", "pattern", "skin", "tap", "tapSet", "pet" }

local function copy(v, seen)
  if type(v) ~= "table" then return v end
  seen = seen or {}
  if seen[v] then return seen[v] end
  local out = {}
  seen[v] = out
  for k, x in pairs(v) do out[copy(k, seen)] = copy(x, seen) end
  return out
end
TCF.DeepCopy = copy

local function num(v) return tonumber(v) or 0 end
local function tbl(t, k) if type(t[k]) ~= "table" then t[k] = {} end; return t[k] end

-- adds item counts (bag, cosmetics, materials) from src into dst
local function addCounts(dst, src)
  if type(src) ~= "table" then return end
  for id, n in pairs(src) do
    if type(n) == "number" and n > 0 then dst[id] = num(dst[id]) + n end
  end
end

-- "where it came from" records: the earliest first source and the latest copy
local function mergeSources(dst, src)
  if type(src) ~= "table" then return end
  for id, rec in pairs(src) do
    if type(rec) == "table" and type(rec.first) == "table" then
      local d = dst[id]
      if type(d) ~= "table" or type(d.first) ~= "table" then dst[id] = copy(rec)
      else
        -- ("before this was tracked" counts as earliest)
        local df, sf = num(d.first[2]), num(rec.first[2])
        if sf < df then d.first = copy(rec.first) end
        if type(rec.last) == "table" and (type(d.last) ~= "table" or num(rec.last[2]) > num(d.last[2])) then d.last = copy(rec.last) end
      end
    end
  end
end
TCF.MergeItemSources = mergeSources

-- professions of two cats of the same class: base keeps its business; skills, Renown, unlocks,
-- milestones and upgrades take the best of both, materials are added up
local function mergeTrade(base, o)
  if type(o) ~= "table" then return end
  addCounts(tbl(base, "mats"), o.mats)
  local sk = tbl(base, "skill")
  for k, v in pairs(type(o.skill) == "table" and o.skill or {}) do
    if type(v) == "number" then sk[k] = max(num(sk[k]), v) end
  end
  base.renown = max(num(base.renown), num(o.renown))
  base.renownEver = max(num(base.renownEver), num(o.renownEver), num(o.renown))
  base.prestiges = max(num(base.prestiges), num(o.prestiges))
  for _, t in ipairs({ "announced", "milestones" }) do
    if type(o[t]) == "table" then
      local d = tbl(base, t)
      for k, v in pairs(o[t]) do if v and d[k] == nil then d[k] = v end end
    end
  end
  if type(o.speed) == "table" then
    local d = tbl(base, "speed")
    for k, v in pairs(o.speed) do if type(v) == "number" then d[k] = max(num(d[k]), v) end end
  end
  -- garden plots, First Aid, fishing and cooking: every upgrade and known dish either one had
  for _, k in ipairs({ "garden", "aid", "fish", "cook" }) do
    local a, b = o[k], base[k]
    if type(a) == "table" then
      if type(b) ~= "table" then base[k] = copy(a)
      else
        for _, t in ipairs({ "up", "known" }) do
          if type(a[t]) == "table" then
            local d = tbl(b, t)
            for key, v in pairs(a[t]) do if v and not d[key] then d[key] = v end end
          end
        end
        if type(a.n) == "number" then b.n = max(num(b.n), a.n) end
        if type(a.buddy) == "number" then b.buddy = max(num(b.buddy), a.buddy) end
      end
    end
  end
end

-- adds cat o (same class) into the base cat
local function mergeCat(base, o)
  -- bag: worn copies are in the bag already (Gear.lua); make sure, then add
  local bag = tbl(base, "bag")
  local obag = copy(type(o.bag) == "table" and o.bag or {})
  local worn = {}
  for _, id in pairs(type(o.gear) == "table" and o.gear or {}) do worn[id] = (worn[id] or 0) + 1 end
  for id, w in pairs(worn) do if num(obag[id]) < w then obag[id] = w end end
  addCounts(bag, obag)
  -- unopened chests, by kind and level stamp
  if type(o.chests) == "table" then
    local ch = tbl(base, "chests")
    for key, stamps in pairs(o.chests) do
      if type(stamps) == "table" then addCounts(tbl(ch, key), stamps) end
    end
  end
  addCounts(tbl(base, "owned"), o.owned)
  mergeSources(tbl(base, "itemSources"), o.itemSources)
  if type(o.abilities) == "table" then
    local ab = tbl(base, "abilities")
    for k, v in pairs(o.abilities) do if v == true then ab[k] = true end end
  end
  if type(o.adv) == "table" then
    local a, b = tbl(base, "adv"), o.adv
    for _, k in ipairs({ "kills", "bossKills", "newStages" }) do a[k] = num(a[k]) + num(b[k]) end
    a.best = max(num(a.best), num(b.best))
    if type(b.cleared) == "table" then
      local c = tbl(a, "cleared")
      for k, v in pairs(b.cleared) do if v and not c[k] then c[k] = v end end
    end
  end
end

local function score(c)
  local cd = c.cd
  return num(cd.level), num(cd.xp)
end

-- the one cat of a class made from every candidate { cd, loadout, look, account }
local function mergeClass(cands)
  table.sort(cands, function(a, b)
    local la, xa = score(a)
    local lb, xb = score(b)
    if la ~= lb then return la > lb end
    if xa ~= xb then return xa > xb end
    if (a.account and 1 or 0) ~= (b.account and 1 or 0) then return a.account and true or false end
    return (a.key or "") < (b.key or "")
  end)
  local base = cands[1]
  local cd = base.cd
  -- professions: the business with the most Trade Gold earned
  local bestTrade, trades = nil, {}
  for _, c in ipairs(cands) do
    local t = c.cd.trade
    if type(t) == "table" then
      trades[#trades + 1] = t
      if not bestTrade or num(t.lifetime) > num(bestTrade.lifetime) then bestTrade = t end
    end
  end
  for i = 2, #cands do mergeCat(cd, cands[i].cd) end
  if bestTrade then
    cd.trade = bestTrade
    for _, t in ipairs(trades) do
      if t ~= bestTrade then
        mergeTrade(bestTrade, t)
        -- the Trade Gold the other businesses earned still counts toward account totals (achievements,
        -- the leaderboard; TCF:TradeTotals), never toward this cat's profession unlocks
        bestTrade.lifetimeMerged = num(bestTrade.lifetimeMerged) + num(t.lifetime) + num(t.lifetimeMerged)
      end
    end
  end
  return cd, base.loadout, base.look
end

local function mergeExpeditions(dst, src)
  if type(src) ~= "table" then return end
  local act = tbl(dst, "active")
  for _, ex in ipairs(type(src.active) == "table" and src.active or {}) do act[#act + 1] = ex end
  dst.done = num(dst.done) + num(src.done)
  dst.groupDone = num(dst.groupDone) + num(src.groupDone)
  if type(src.group) == "table" then
    if dst.group == nil then dst.group = src.group
    else local q = tbl(dst, "groupQueue"); q[#q + 1] = src.group end
  end
  for _, g in ipairs(type(src.groupQueue) == "table" and src.groupQueue or {}) do local q = tbl(dst, "groupQueue"); q[#q + 1] = g end
end

-- Things 1.5.3 and older kept per character that belong to its cats, folded into that character's
-- own cats (copies) before they are merged, the way its next login would have done it:
-- unopened chests (keys: one bag per character, every 1.5.x save) go to the cat it was playing,
-- stamped with that cat's level; the pre-1.3.1 gear pool (gear) to the cats wearing it, the rest
-- to the cat it was playing; the pre-1.5.1 one trade (trade) is split between its cats
-- (Professions.lua). A stand-in (a table with a metatable) is never one of these.
local function plain(t) return type(t) == "table" and getmetatable(t) == nil end
local function foldCharThings(self, sv, ch, mine)
  local cur = ch.class
  if not mine[cur] then
    -- (a character whose played cat is missing: its highest cat)
    cur = nil
    for cls, c in pairs(mine) do
      if not cur or num(c.level) > num(mine[cur].level) or (num(c.level) == num(mine[cur].level) and cls < cur) then cur = cls end
    end
  end
  local target = cur and mine[cur]
  if not target then return end
  local keys = rawget(ch, "keys")
  if plain(keys) then
    local lv = min(TCF.MAX_LEVEL or 60, max(1, floor(num(target.level))))
    for k, v in pairs(keys) do
      local n = floor(num(v))
      if TCF.CHEST_BY_KEY and TCF.CHEST_BY_KEY[k] and n > 0 then
        local t = tbl(tbl(target, "chests"), k)
        t[lv] = num(t[lv]) + n
      end
    end
    ch.keys = nil
  end
  local pool = rawget(ch, "gear")
  -- (1.3.1 and later leave an empty table here: nothing to do)
  if plain(pool) and next(pool) == nil then ch.gear = nil
  elseif plain(pool) then
    pool = copy(pool)
    for _, c in pairs(mine) do
      local bag = tbl(c, "bag")
      local worn = {}
      for _, id in pairs(type(c.gear) == "table" and c.gear or {}) do worn[id] = (worn[id] or 0) + 1 end
      for id, w in pairs(worn) do
        local take = min(w, max(0, num(pool[id])))
        if take > 0 then pool[id] = num(pool[id]) - take end
        bag[id] = max(num(bag[id]), 0) + take
        -- (the old shared bag let several cats wear one copy: each wearer keeps one)
        if num(bag[id]) < w then bag[id] = w end
      end
    end
    addCounts(tbl(target, "bag"), pool)
    ch.gear = nil
  end
  if plain(rawget(ch, "trade")) and self.SplitOldTrade then
    local ctx = { trade = ch.trade, class = cur, classData = mine, stats = rawget(sv, "stats") }
    local ok = pcall(self.SplitOldTrade, self, ctx)
    if ok then ch.trade = nil; ch.tradeSplit = true end
  end
end

-- the look a character's cat of class cls wore (1.5.x saves: one look for every cat)
local function lookOf(ch, cls)
  local l
  if cls == ch.class or type(ch.looks) ~= "table" then l = ch.look else l = ch.looks[cls] end
  if type(l) ~= "table" then return nil end
  local out = {}
  for _, k in ipairs(LOOK_FIELDS) do out[k] = l[k] end
  return out
end

-- Makes sure TapCatForeverDB.cats exists and merges in every character that still has cats of its
-- own. Returns how many characters were merged.
function TCF:MergeAccountCats(sv)
  local cats = rawget(sv, "cats")
  if type(cats) ~= "table" then cats = {}; rawset(sv, "cats", cats) end
  tbl(cats, "classData"); tbl(cats, "loadouts"); tbl(cats, "looks")
  if type(cats.expeditions) ~= "table" then cats.expeditions = { active = {} } end
  tbl(cats.expeditions, "active")
  local chars = rawget(sv, "chars")
  local joiners = {}
  for key, ch in pairs(type(chars) == "table" and chars or {}) do
    if type(ch) == "table" and type(rawget(ch, "classData")) == "table" then joiners[#joiners + 1] = key end
  end
  if #joiners == 0 then return 0 end
  table.sort(joiners)
  -- quests that count the cats keep their progress (Quests.lua)
  local snap = self.QuestCatProgress and self.QuestCatProgress(sv, cats.classData)
  local backup = rawget(sv, "preAccountBackup")
  if type(backup) ~= "table" then backup = {}; rawset(sv, "preAccountBackup", backup) end
  local cands = {}
  for _, cl in ipairs(TCF.CLASSES) do
    local list = {}
    local acd = cats.classData[cl.key]
    if type(acd) == "table" then
      list[1] = { cd = acd, loadout = cats.loadouts[cl.key], look = cats.looks[cl.key], account = true }
    end
    cands[cl.key] = list
  end
  local oldSources = tbl(cats, "oldItemSources")
  for _, key in ipairs(joiners) do
    local ch = chars[key]
    -- a copy of the old cats, untouched (a character merged twice keeps both copies)
    local b = { time = time and time() or 0, class = ch.class }
    for _, k in ipairs(TCF.CHAR_CAT_KEYS) do b[k] = copy(rawget(ch, k)) end
    -- (and the older per-character chests, gear pool and trade, folded in below)
    for _, k in ipairs({ "keys", "gear", "trade" }) do if plain(rawget(ch, k)) then b[k] = copy(rawget(ch, k)) end end
    local bkey, n = key, 1
    while backup[bkey] ~= nil do n = n + 1; bkey = key .. " (" .. n .. ")" end
    backup[bkey] = b
    local charOwned = rawget(ch, "owned")
    local mine = {}
    for cls, cd in pairs(ch.classData) do
      if TCF.CLASS_BY_KEY[cls] and type(cd) == "table" then
        local c = copy(cd)
        -- (CarePackage.lua: a cat whose character already had its 1.5.4 care package)
        if ch.carePackage then c.carePackage = true end
        -- before 1.6.0 the cosmetics were the character's: each of its cats gets all of them
        if type(charOwned) == "table" then
          local o = tbl(c, "owned")
          for id, cnt in pairs(charOwned) do if type(cnt) == "number" then o[id] = max(num(o[id]), cnt) end end
        end
        local lo = type(ch.loadouts) == "table" and ch.loadouts[cls]
        table.insert(cands[cls], { cd = c, loadout = copy(lo), look = lookOf(ch, cls), key = key })
        mine[cls] = c
      end
    end
    foldCharThings(self, sv, ch, mine)
    mergeExpeditions(cats.expeditions, copy(rawget(ch, "expeditions")))
    mergeSources(oldSources, rawget(ch, "itemSources"))
    for _, k in ipairs(TCF.CHAR_CAT_KEYS) do ch[k] = nil end
  end
  for _, cl in ipairs(TCF.CLASSES) do
    local list = cands[cl.key]
    if #list > 0 then
      local cd, lo, look = mergeClass(list)
      cats.classData[cl.key] = cd
      cats.loadouts[cl.key] = type(lo) == "table" and lo or cats.loadouts[cl.key] or {}
      if type(look) == "table" then cats.looks[cl.key] = look end
    end
  end
  cats.started = true
  -- (rebased by Core.lua's InitDB once every class has its cat: TCF.QuestCatRebase)
  self.questSnap = snap
  self.catsMerged = (self.catsMerged or 0) + #joiners
  return #joiners
end

-- the account's records of where cosmetics came from, kept from before 1.6.0 (ItemSources.lua)
function TCF:oldItemSources()
  local sv = TapCatForeverDB
  local cats = type(sv) == "table" and rawget(sv, "cats")
  return type(cats) == "table" and cats.oldItemSources or nil
end

-- once per account, after the first merge: one chat line
local ev = CreateFrame("Frame")
ev:RegisterEvent("PLAYER_LOGIN")
ev:SetScript("OnEvent", function()
  if TCF.db and TCF.catsNotice then
    TCF.catsNotice = nil
    TCF:Print("Your cats are now shared by all your characters: each class has one cat, with everything your characters had.", true)
  end
end)
