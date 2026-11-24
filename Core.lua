-- TapCatForever: core (saved data, input, progression, loot, shop, achievements)
local ADDON, TCF = ...
_G.TapCatForever = TCF

local floor, min, max, random = math.floor, math.min, math.max, math.random
local GetTime = GetTime

local GetMeta = (C_AddOns and C_AddOns.GetAddOnMetadata) or GetAddOnMetadata
TCF.version = GetMeta and GetMeta(ADDON, "Version") or "dev"

-- WoW: Forever runs the modern (Midnight 12.x) addon API, which can hand addons
-- "secret" values during combat. TapCatForever never reads combat data, but any
-- value that comes from the game is checked before use.
local function isSecret(v) return issecretvalue ~= nil and issecretvalue(v) end
TCF.IsSecret = isSecret

---------------------------------------------------------------- utils
local function copyDefaults(src, dst)
  for k, v in pairs(src) do
    if type(v) == "table" then
      if type(dst[k]) ~= "table" then dst[k] = {} end
      copyDefaults(v, dst[k])
    elseif dst[k] == nil then
      dst[k] = v
    end
  end
  return dst
end

function TCF.Commas(n)
  n = floor(n or 0)
  if BreakUpLargeNumbers then return BreakUpLargeNumbers(n) end
  local s = tostring(n)
  local k
  repeat s, k = s:gsub("^(-?%d+)(%d%d%d)", "%1,%2") until k == 0
  return s
end

function TCF.ItemLink(it)
  if not it then return "?" end
  return "|c" .. TCF.RARITY[it.rarity].hex .. "[" .. it.name .. "]|r"
end

-- Resolves a game icon name; falls back to a safe icon if this client lacks it.
local iconCache = {}
local FALLBACK_ICON = "Interface\\Icons\\INV_Misc_QuestionMark"
function TCF.Icon(path, fallback)
  local full = TCF.ICON .. path
  local cached = iconCache[full]
  if cached then return cached end
  local ok = true
  if GetFileIDFromPath then ok = GetFileIDFromPath(full) ~= nil end
  cached = ok and full or (TCF.ICON .. (fallback or "Ability_Druid_CatForm"))
  iconCache[full] = cached
  return cached
end

-- The "Chat messages" setting only mutes passive notifications. force = true is for
-- direct replies to the player's own click or command, which must always show.
function TCF:Print(msg, force)
  if not force and self.db and not self.db.ui.chat then return end
  DEFAULT_CHAT_FRAME:AddMessage("|cffffb84dTapCat|r|cffffffffForever|r: " .. msg)
end

function TCF:PlaySound(kind)
  if not self.db.ui.sound or not PlaySound then return end
  local map = {
    level = { "UI_EPICLOOT_TOAST", "LEVELUPSOUND", "IG_QUEST_LIST_COMPLETE" },
    loot  = { "LOOTWINDOWCOINSOUND", "IG_BACKPACK_COIN_SELECT" },
    rare  = { "UI_EPICLOOT_TOAST", "IG_QUEST_LIST_COMPLETE" },
    legendary = { "UI_LEGENDARY_LOOT_TOAST", "UI_EPICLOOT_TOAST", "IG_QUEST_LIST_COMPLETE" },
    click = { "IG_MAINMENU_OPTION_CHECKBOX_ON", "IG_CHARACTER_INFO_TAB" },
    ach   = { "ACHIEVEMENT_MENU_OPEN", "IG_QUEST_LIST_COMPLETE" },
    buy   = { "LOOTWINDOWCOINSOUND", "IG_BACKPACK_COIN_SELECT" },
  }
  for _, name in ipairs(map[kind] or {}) do
    local id = SOUNDKIT and SOUNDKIT[name]
    if id then pcall(PlaySound, id, "Master"); return end
  end
end

---------------------------------------------------------------- saved variables (account-wide)
local DEFAULTS = {
  version = 2,
  taps = 0,
  classData = {},   -- per class: level, xp, adventure progress
  coins = 0, coinsEarned = 0, coinsSpent = 0, coinFrac = 0,
  -- owned: (1.6.0) the cosmetics of each class's cat are in classData[class].owned (TCF:Owned)
  gear = {},        -- real gear: itemID -> count
  class = nil,
  loadouts = {},
  -- look: (1.6.0) each class cat's look is in looks[class] (TCF:LookOf); db.look is the current cat's
  achievements = {},
  stats = { chests = 0, drops = 0, frenzies = 0, pets = 0, peakTPS = 0, classesPlayed = {} },
  daily = { last = "", streak = 0, best = 0 },
  shop = { day = "", rerolls = 0, stock = {}, bought = {} },
  keys = { pouch = 0, strong = 0, heroic = 0, raid = 0 },  -- free (unopened) chests
  ui = {
    point = { "BOTTOM", "BOTTOM", 0, 160 },
    scale = 1.0, alpha = 1.0, textScale = 1.0, shown = true,
    locked = false, clickThrough = false,
    showLevel = true, showXP = true, showTaps = true, showCoins = true, catOnly = false,
    mouse = true, popups = true, sound = false, chat = false, racial = true, cartoon = true, chestAnim = true, textAbove = true, cat3d = true, show3dWeapons = true,
    minimap = { angle = 215, hide = false },
  },
}

-- Saved data that belonged to the current character before 1.6.0. Everything else (TapCoins,
-- quests, daily streak, achievements, settings) is shared by the whole account. Since 1.6.0 the
-- cats themselves are the account's too (TCF.ACCOUNT_CATS, AccountCats.lua): what is left per
-- character is which cat it plays, the Shop and real WoW lockouts (see AccountCats.lua).
-- The Daily Wares (shop) are per character: the stock is picked for this character's
-- cat class and collection, and keeping it per character means relogging can't reroll it.
-- Professions live in classData (each class's cat has its own trade since 1.5.1); "trade" is
-- the old shared trade of 1.5.0 and older, split once per character (tradeSplit) and removed.
TCF.PER_CHARACTER = {
  owned = true, gear = true, loadouts = true, look = true, looks = true, keys = true, classData = true,
  trade = true, tradeSplit = true, expeditions = true, class = true, prof = true, dungeonRun = true, shop = true,
}

-- (1.6.0) the account's cats: these keys read and write TapCatForeverDB.cats (AccountCats.lua)
TCF.ACCOUNT_CATS = { classData = true, loadouts = true, looks = true, expeditions = true }

-- (1.6.0) keys that read something else than a saved table of their own (see bindCharacter):
-- db.owned is the collection of the cat things are given to now, db.look the look of the cat played
TCF.VIRTUAL = {
  owned = function() return TCF:Owned() end,
  look = function() return TCF:LookOf() end,
}

local function characterKey()
  local name = UnitName and UnitName("player")
  local realm = GetRealmName and GetRealmName()
  if TCF.IsSecret(name) or not name or name == "" then name = "Unknown" end
  if TCF.IsSecret(realm) or not realm then realm = "" end
  return name .. "-" .. realm
end

-- Point the per-character keys of the saved table at this character's own data.
local function bindCharacter(sv)
  setmetatable(sv, nil)
  sv.chars = sv.chars or {}
  local key = characterKey()
  local char = sv.chars[key]
  if not char then
    char = {}
    sv.chars[key] = char
    -- the first character after this update inherits the old shared data
    if not sv.charsMigrated then
      for k in pairs(TCF.PER_CHARACTER) do char[k] = sv[k] end
      char.migrated = true
    else
      char.fresh = true
    end
  end
  sv.charsMigrated = true
  -- a key that just became per-character (e.g. the Daily Wares shop) moves to the first
  -- character that logs in after the update instead of being dropped
  for k in pairs(TCF.PER_CHARACTER) do
    local v = rawget(sv, k)
    if v ~= nil and char[k] == nil then char[k] = v end
  end
  for k in pairs(TCF.PER_CHARACTER) do rawset(sv, k, nil) end
  -- (1.6.0) TCF.VIRTUAL keys stand for something else: db.owned is the collection of the cat
  -- things are given to right now (TCF:Owned)
  setmetatable(sv, {
    __index = function(t, k)
      local virt = TCF.VIRTUAL[k]
      if virt then return virt(char) end
      if TCF.ACCOUNT_CATS[k] then
        local cats = rawget(t, "cats")
        return type(cats) == "table" and cats[k] or nil
      end
      if TCF.PER_CHARACTER[k] then return char[k] end
    end,
    __newindex = function(t, k, v)
      if TCF.VIRTUAL[k] then return end   -- (never replaced as a whole)
      if TCF.ACCOUNT_CATS[k] then
        local cats = rawget(t, "cats")
        if type(cats) ~= "table" then cats = {}; rawset(t, "cats", cats) end
        cats[k] = v
      elseif TCF.PER_CHARACTER[k] then char[k] = v else rawset(t, k, v) end
    end,
  })
  TCF.charKey, TCF.charData = key, char
  return char
end

-- Wipe saved progress and reload. scope "cats" (or the old "char"): the account's nine cats (gear,
-- cosmetics, professions, levels, abilities, adventures and expeditions) for every character;
-- TapCoins, quests and achievements are kept. scope "all": everything on the account (settings
-- and position are kept).
function TCF:ResetProgress(scope)
  local sv = TapCatForeverDB
  if scope == "all" then
    local ui = rawget(sv, "ui")
    setmetatable(sv, nil)
    for k in pairs(sv) do sv[k] = nil end
    sv.ui, sv.charsMigrated = ui, true
  else
    rawset(sv, "cats", nil)
    local chars = rawget(sv, "chars")
    for _, ch in pairs(type(chars) == "table" and chars or {}) do
      -- (cats an older version saved on a character would come back with the next merge)
      if type(ch) == "table" then for _, k in ipairs(TCF.CHAR_CAT_KEYS or {}) do ch[k] = nil end end
    end
  end
  if ReloadUI then ReloadUI() end
end

function TCF:InitDB()
  TapCatForeverDB = TapCatForeverDB or {}
  local sv = TapCatForeverDB
  local char = bindCharacter(sv)
  -- 1.5.4 care package (CarePackage.lua): only for an account and a character that existed before
  self.saveExisted = rawget(sv, "version") ~= nil
  self.charExisted = self.saveExisted and not (char.fresh and not char.started)
  -- (1.6.0) the nine class cats are the account's: characters that still have cats of their own
  -- (every one, the first time) are merged in (AccountCats.lua)
  local merged = self:MergeAccountCats(sv)
  local cats = rawget(sv, "cats")
  self.db = sv
  local db = copyDefaults(DEFAULTS, sv)
  self.db = db
  if merged > 0 and self.saveExisted and not cats.notice then
    cats.notice = true
    self.catsNotice = true   -- (printed at login, CarePackage.lua's event)
  end
  -- 1.3: the level text moved above the cat (once, for saves made before that)
  if not db.ui.textAboveSet then db.ui.textAbove = true; db.ui.textAboveSet = true end
  -- default class = the character's own class the very first time
  if not db.class then
    local _, cls = UnitClass("player")
    if isSecret(cls) then cls = nil end
    db.class = (cls and TCF.CLASS_BY_KEY[cls]) and cls or "WARRIOR"
  end
  -- (1.6.0) each class's cat wears its own fur, pattern, skin and tap effect (db.looks[class],
  -- TCF:LookOf). A brand-new cat starts in its class fur with the basic dust puffs.
  for _, cl in ipairs(TCF.CLASSES) do
    local l = self:LookOf(cl.key)
    if not l.tapSet then l.tap = l.tap or "tap_puff"; l.tapSet = true end
    if not (l.fur and TCF.ITEMS[l.fur]) then l.fur = "fur_ginger" end
    for _, slot in ipairs({ "pattern", "skin", "tap", "pet" }) do if l[slot] and not TCF.ITEMS[l[slot]] then l[slot] = nil end end
  end
  for k in pairs(db.looks) do if not TCF.CLASS_BY_KEY[k] then db.looks[k] = nil end end
  -- cosmetic overrides per class (empty = the cat shows its real gear)
  for _, cl in ipairs(TCF.CLASSES) do db.loadouts[cl.key] = db.loadouts[cl.key] or {} end
  -- drop references to items that no longer exist
  for _, lo in pairs(db.loadouts) do
    for slot, id in pairs(lo) do if not TCF.ITEMS[id] then lo[slot] = nil end end
  end
  if self.MigrateRaceSlot then self:MigrateRaceSlot(db) end  -- 1.6: the racial accessory has its own slot
  -- v1 -> v2: levels became per-class; the old shared level goes to the current class
  if db.level then
    local cur = db.classData[db.class]
    if type(cur) ~= "table" or (tonumber(cur.level) or 1) < db.level then
      db.classData[db.class] = { level = db.level, xp = db.xp or 0 }
    end
    db.level, db.xp = nil, nil
  end
  for _, cl in ipairs(TCF.CLASSES) do
    local cd = db.classData[cl.key] or {}
    db.classData[cl.key] = cd
    cd.level = cd.level or 1
    cd.xp = cd.xp or 0
    cd.gear = cd.gear or {}
    cd.abilities = cd.abilities or {}
    cd.adv = cd.adv or {}
    local adv = cd.adv
    adv.tier = adv.tier or 1
    adv.stage = adv.stage or 1
    adv.best = adv.best or 0         -- highest stage index ever cleared (tier*10 scale)
    if adv.auto == nil then adv.auto = true end
    adv.kills = adv.kills or 0
    adv.bossKills = adv.bossKills or 0
    adv.cleared = adv.cleared or {}
    adv.newStages = adv.newStages or 0
    -- 1.5.3: levels stop at 60. A cat above it becomes 60 and keeps everything else.
    if cd.level >= TCF.MAX_LEVEL then cd.level, cd.xp = TCF.MAX_LEVEL, TCF.XPForLevel(TCF.MAX_LEVEL) end
    -- 1.5.3: the XP curve changed. A cat keeps the same share of its current level (never a full
    -- bar, so no free levels): 2,100 of 1.5.2's 2,133 at level 10 becomes 927 of 942. Once per cat;
    -- a cat made later gets the flag with 0 XP, so it is never rescaled.
    if not cd.xpCurve2 then
      if cd.level < TCF.MAX_LEVEL and cd.xp > 0 then
        local oldNeed = floor(120 * cd.level ^ 1.25)
        cd.xp = floor(TCF.XPForLevel(cd.level) * min(0.99, cd.xp / max(1, oldNeed)))
      end
      cd.xpCurve2 = true
    end
  end
  self:InitOwned(char)
  -- quests that count the cats go on from the merged cats (Quests.lua)
  if self.questSnap and self.QuestCatRebase then self.QuestCatRebase(sv, self.questSnap, db.classData) end
  self.questSnap = nil
  -- 1.5.3: level-up rewards are paid once per class and level for the whole account. Every
  -- level any character's cat already reached was paid, so it starts from the highest of them.
  if type(db.levelPaid) ~= "table" then
    local paid = {}
    local chars = rawget(TapCatForeverDB, "chars")
    for _, ch in pairs(type(chars) == "table" and chars or {}) do
      if type(ch) == "table" and type(ch.classData) == "table" then
        for cl, cd in pairs(ch.classData) do
          local lv = type(cd) == "table" and tonumber(cd.level)
          if lv then paid[cl] = min(TCF.MAX_LEVEL, max(paid[cl] or 1, floor(lv))) end
        end
      end
    end
    db.levelPaid = paid
  end
  for cl, cd in pairs(db.classData) do
    if (db.levelPaid[cl] or 1) < cd.level then db.levelPaid[cl] = cd.level end
  end
  -- v2 -> v3: real gear. Every class starts with a simple weapon (also brand-new cats: a new
  -- account, or after "Reset your cats").
  if ((db.version or 0) < 3 or not cats.started) and self.StarterGear then
    for _, cl in ipairs(TCF.CLASSES) do
      self:StarterGear(cl.key)
      db.loadouts[cl.key] = {}   -- show real gear instead of the old starter cosmetics
      -- Adventure now runs through real dungeons with new stage numbering
      local adv = db.classData[cl.key].adv
      adv.tier, adv.stage, adv.best, adv.cleared = 1, 1, 0, {}
    end
  end
  -- cats still holding the old lowest-numbered starter get their class weapon (once)
  if self.FixStarterWeapons then self:FixStarterWeapons() end
  self:InitChests(char)   -- 1.5.4: chests belong to each class's cat
  char.started = true
  cats.started = true
  db.version = 3
  db.stats.classesPlayed[db.class] = true
end

-- Per-class progress (level, xp, adventure)
function TCF:CD(class) return self.db.classData[class or self.db.class] end

---------------------------------------------------------------- cosmetics per class cat (1.6.0)
-- Every class's cat has its own collection of cosmetics (skins, fur, patterns, hats, capes,
-- effects, tap effects, accessories, racial pieces, set pieces, crafted cosmetics):
-- classData[class].owned = { [item id] = copies }. db.owned (TCF.VIRTUAL) is the collection of the
-- cat things are given to right now (TCF:OwnerClass): the cat a crafting job, an expedition being
-- claimed or a class achievement is for (TCF:WithOwner), else the cat you are playing. So every
-- unlock goes to that cat, and the Appearance tab, Shop, Compendium and try-on show its collection.

-- the class whose cat gets what is given right now
function TCF:OwnerClass()
  local db = self.db
  local all = db and db.classData
  if not all then return db and db.class end
  local c = self.ownerClass
  if not (c and all[c]) then c = self.claimChests and self.claimChests.owner end
  if not (c and all[c]) then c = self.tradeClass end
  if not (c and all[c]) then c = db.class end
  return c
end

-- a class cat's cosmetics (default: TCF:OwnerClass). A class without a cat (never in a real
-- save) gets a table that is not saved.
function TCF:Owned(class)
  local db = self.db
  class = class or self:OwnerClass()
  local cd = db and db.classData and class and db.classData[class]
  if type(cd) ~= "table" then return {} end
  if type(cd.owned) ~= "table" then cd.owned = {} end
  return cd.owned
end

-- runs fn(self, ...) with everything given going to class's cat
function TCF:WithOwner(class, fn, ...)
  local prev = self.ownerClass
  self.ownerClass = class
  local ok, a, b, c = pcall(fn, self, ...)
  self.ownerClass = prev
  if not ok then error(a, 0) end
  return a, b, c
end

-- does any class's cat own this cosmetic?
function TCF:AnyCatOwns(id)
  for _, cl in ipairs(TCF.CLASSES) do
    local cd = self.db.classData[cl.key]
    if type(cd) == "table" and type(cd.owned) == "table" and cd.owned[id] then return cl.key end
  end
end

-- Once per load: the cosmetics a character owned before 1.6.0 (char.owned, also a collection an
-- older version wrote after going back) go to every class's cat, so nobody loses anything.
-- Every cat owns the starter cosmetics; an account achievement already earned whose reward no
-- cat has (a new character, a reset) gives it to the cat being played.
function TCF:InitOwned(char)
  local db = self.db
  local legacy = char and rawget(char, "owned")
  for _, cl in ipairs(TCF.CLASSES) do
    local cd = db.classData[cl.key]
    if type(cd.owned) ~= "table" then cd.owned = {} end
    local o = cd.owned
    if type(legacy) == "table" then
      for id, n in pairs(legacy) do
        if type(id) == "string" then o[id] = max(tonumber(o[id]) or 0, tonumber(n) or 1) end
      end
    end
    for id in pairs(o) do if not TCF.ITEMS[id] then o[id] = nil end end
  end
  if char then char.owned = nil end
  -- (ItemSources.lua: a cosmetic given here for the first time records where it came from)
  local function give(id, src, class)
    local o = self:Owned(class)
    if o[id] then return end
    o[id] = 1
    if self.NoteItemSource then self:NoteItemSource(id, src, nil, nil, class) end
  end
  for _, cl in ipairs(TCF.CLASSES) do
    for _, id in ipairs(TCF.STARTER) do give(id, "Starter cosmetic", cl.key) end
    -- every cat owns a basic Orange Tabby skin
    give("skin_orange", "Starter cosmetic", cl.key)
  end
  for _, a in ipairs(TCF.ACHIEVEMENTS) do
    if db.achievements[a.id] then
      for _, id in ipairs({ a.item or false, a.skin or false }) do
        if id and TCF.ITEMS[id] and not self:AnyCatOwns(id) then give(id, "Achievement: " .. a.name, db.class) end
      end
    end
  end
end

---------------------------------------------------------------- appearance
function TCF:GetLoadout(class) return self.db.loadouts[class or self.db.class] end

-- the fur, pattern, skin and tap effect slots (TCF.SLOTS entries with look = true) of one cat
local LOOK_FIELDS = { "fur", "pattern", "skin", "tap", "tapSet", "pet" }
function TCF.CopyLook(l)
  local out = {}
  for _, k in ipairs(LOOK_FIELDS) do out[k] = l and l[k] end
  return out
end
-- (1.6.0) the worn look of a class's cat (default: the cat being played): db.looks[class], the
-- account's. A cat without one starts in its class fur with the basic dust puffs. db.look is the
-- look of the cat being played.
function TCF:LookOf(class)
  local db = self.db
  if not db then return TCF.CopyLook(nil) end
  class = class or db.class
  local looks = db.looks
  if type(looks) ~= "table" then looks = {}; db.looks = looks end
  if not class then return TCF.CopyLook(nil) end
  local l = looks[class]
  if type(l) ~= "table" then
    local cl = TCF.CLASS_BY_KEY[class]
    l = { fur = cl and cl.fur or "fur_ginger", tap = "tap_puff", tapSet = true }
    looks[class] = l
  end
  return l
end

-- Returns a flat table slot -> item for drawing, optionally with one item previewed.
-- The cat wears its real gear; a cosmetic chosen for a slot overrides it (transmog).
function TCF:GetAppearance(class, previewItem, previewGear)
  local lo = self:GetLoadout(class)
  local out = self.GearAppearance and self:GearAppearance(class, previewGear) or {}
  for slot, id in pairs(lo) do out[slot] = TCF.ITEMS[id] end
  local look = self:LookOf(class)
  out.fur = TCF.ITEMS[look.fur] or TCF.ITEMS.fur_ginger
  out.pattern = look.pattern and TCF.ITEMS[look.pattern] or nil
  out.skin = look.skin and TCF.ITEMS[look.skin] or nil
  out.tap = look.tap and TCF.ITEMS[look.tap] or nil
  out.pet = look.pet and TCF.ITEMS[look.pet] or nil   -- (1.6.6) nil: hearts
  -- racial accessory can be hidden in Settings (since 1.6 it has its own slot, "race")
  if not self.db.ui.racial and out.acc and out.acc.source == "race" then out.acc = nil end
  if not self.db.ui.racial then out.race = nil end
  if previewItem then out[previewItem.slot] = previewItem end
  return out
end

function TCF:CanEquip(it, class)
  class = class or self.db.class
  return it and (not it.class or it.class == class)
end

function TCF:IsEquipped(it, class)
  if not it then return false end
  if TCF.SLOT_BY_KEY[it.slot].look then return self:LookOf(class)[it.slot] == it.id end
  return self:GetLoadout(class)[it.slot] == it.id
end

function TCF:Equip(it, class)
  if not it or not self:Owned(class or self.db.class)[it.id] or not self:CanEquip(it, class) then return end
  if TCF.SLOT_BY_KEY[it.slot].look then
    self:LookOf(class)[it.slot] = it.id
  else
    self:GetLoadout(class)[it.slot] = it.id
  end
  self:RefreshAll()
end

function TCF:Unequip(slot, class)
  if slot == "fur" then return end
  if TCF.SLOT_BY_KEY[slot].look then self:LookOf(class)[slot] = nil
  else self:GetLoadout(class)[slot] = nil end
  self:RefreshAll()
end

function TCF:SetClass(key)
  if not TCF.CLASS_BY_KEY[key] then return end
  -- every other cat's idle professions catch up first, so none skips or repeats any time
  if self.ProfCatchUp and key ~= self.db.class then self:ProfCatchUp() end
  self.db.class = key
  self.db.stats.classesPlayed[key] = true
  -- professions this cat unlocked while you played another one are announced now
  if self.CheckProfUnlocks then self:CheckProfUnlocks() end
  self:MarkDirty()
  self:RefreshAll()
end

---------------------------------------------------------------- progression
-- Cat levels stop at 60, like Classic. The XP (key presses and expedition XP) from one level to
-- the next grows like WoW's: a new cat levels every minute or two, then each level takes a little
-- longer than the last. Playing about 2 hours a day at about one key press a second, a cat reaches
-- level 10 in about an hour, 20 in a few days, 40 in a few weeks and 60 in a few months
-- (tools/test_harness.py prints the timeline). 1.5.2 and older: 120 * level^1.25, with no cap.
TCF.MAX_LEVEL = 60
TCF.XP_CURVE = { base = 25, perLevel = 45, k = 1.66, exp = 2.45 }
function TCF.XPForLevel(level)
  local c = TCF.XP_CURVE
  level = max(1, min(TCF.MAX_LEVEL, level or 1))
  return floor(c.base + c.perLevel * level + c.k * level ^ c.exp)
end

function TCF:IsMaxLevel(class)
  local cd = self:CD(class)
  return cd ~= nil and cd.level >= TCF.MAX_LEVEL
end

-- Levels a class's cat up while it has enough XP. A cat at the cap keeps a full XP bar and
-- gains no more XP (its level, gear, abilities and titles stay as they are).
function TCF:SettleXP(class)
  local cd = self:CD(class)
  if not cd then return end
  while cd.level < TCF.MAX_LEVEL and cd.xp >= TCF.XPForLevel(cd.level) do
    cd.xp = cd.xp - TCF.XPForLevel(cd.level)
    self:LevelUp(class)
  end
  if cd.level >= TCF.MAX_LEVEL then cd.level, cd.xp = TCF.MAX_LEVEL, TCF.XPForLevel(TCF.MAX_LEVEL) end
end

function TCF:GetTitle(level)
  level = level or self:CD().level
  local t = TCF.TITLES[1][2]
  for _, e in ipairs(TCF.TITLES) do if level >= e[1] then t = e[2] end end
  return t
end

function TCF:AddCoins(n, silent)
  if n <= 0 then return end
  self.db.coins = self.db.coins + n
  self.db.coinsEarned = self.db.coinsEarned + n
  self:MarkDirty()
end

function TCF:SpendCoins(n)
  if self.db.coins < n then return false end
  self.db.coins = self.db.coins - n
  self.db.coinsSpent = self.db.coinsSpent + n
  self:MarkDirty()
  return true
end

-- The highest level each class's cat has been paid for on this account (db.levelPaid, shared by
-- every character). Level-up TapCoins and level chests are paid once per class and level for the
-- whole account, so "Reset your cats" (or an older alt) can't collect them again.
function TCF:LevelPaid(class)
  local paid = self.db.levelPaid
  if type(paid) ~= "table" then paid = {}; self.db.levelPaid = paid end
  return paid[class] or 1, paid
end

-- The level-up rewards: TapCoins, and a chest every 5 levels (a Heroic Cache every 20)
function TCF.LevelReward(level)
  local chest
  if level % 20 == 0 then chest = "heroic" elseif level % 5 == 0 then chest = "strong" end
  return 10 + 2 * level, chest
end

function TCF:LevelUp(class)
  local db = self.db
  class = class or db.class
  local cd = self:CD(class)
  if cd.level >= TCF.MAX_LEVEL then return end
  cd.level = cd.level + 1
  local reward, chest = TCF.LevelReward(cd.level)
  local best, paid = self:LevelPaid(class)
  local cl = TCF.CLASS_BY_KEY[class]
  local top = ""
  if cd.level >= TCF.MAX_LEVEL then
    cd.xp = TCF.XPForLevel(TCF.MAX_LEVEL)   -- the cap: a full XP bar, no more XP
    top = " That is the highest level."
  end
  if cd.level > best then
    paid[class] = cd.level
    self:AddCoins(reward)
    self:Print(string.format("Your %s cat reached |cffffd100level %d|r: +%d TapCoins.%s", cl.name, cd.level, reward, top))
  else
    -- this account already had a cat of this class at this level: no coins or chest this time
    chest = nil
    self:Print(string.format("Your %s cat reached |cffffd100level %d|r.%s |cff999999(Your account already got this level's rewards for a %s.)|r", cl.name, cd.level, top, cl.name))
  end
  if self.cat and class == db.class then self.cat:Celebrate("Level " .. cd.level, 1, 0.82, 0.1) end
  self:PlaySound("level")
  if chest then self:AwardChest(chest, "Level " .. cd.level, nil, class, cd.level) end
end

-- XP for any class cat (expeditions level up the cats that went, not just the current one)
function TCF:AddClassXP(class, n)
  local cd = self:CD(class)
  if not cd or n <= 0 or cd.level >= TCF.MAX_LEVEL then return end
  -- (1.6.6) Happy Purrs (Purr.lua): the cat you play gets 5% more
  if self.PurrMult then n = n * self:PurrMult(class) end
  cd.xp = (cd.xp or 0) + n
  self:SettleXP(class)
  self:MarkDirty()
end

---------------------------------------------------------------- tapping
local TAP_CAP = 20          -- max counted taps per second (anti-macro)
local FRENZY_TPS = 7        -- taps/second to trigger frenzy face
local DROP_CHANCE = 1 / 3000
local COINS_PER_TAP = 0.02  -- 1 TapCoin per 50 taps (quests and Adventure are the main income)
TCF.TAP_COIN_CAP = 10       -- at most this many taps in any one second earn TapCoins; the rest still count (up to TAP_CAP)

local recent, recentHead = {}, 0     -- ring buffer of tap times
for i = 1, 32 do recent[i] = 0 end
-- times of the last TAP_COIN_CAP taps that earned TapCoins: a tap earns while fewer than
-- TAP_COIN_CAP taps earned in the last second, so the first 10 taps of every second always earn
local paid, paidHead, paidCap = {}, 0, 0
local lastInput = 0

function TCF:TapsLastSecond(now)
  local n = 0
  for i = 1, 32 do if now - recent[i] <= 1 then n = n + 1 end end
  return n
end

function TCF:Tap(side)
  local db = self.db
  if not db then return end
  local now = GetTime()
  lastInput = now
  if self.cat then self.cat:Tap(side) end
  local tps = self:TapsLastSecond(now)
  if tps >= TAP_CAP then return end
  recentHead = recentHead % 32 + 1
  recent[recentHead] = now
  tps = tps + 1

  -- party bonus (Party.lua TCF:PartyTapMult): friends with the addon in your group make each tap
  -- count a little more (tap count, cat XP and TapCoins from tapping; lucky finds are unchanged)
  local mult = self.PartyTapMult and self:PartyTapMult() or 1
  self.tapCarry = (self.tapCarry or 0) + mult
  local credit = floor(self.tapCarry + 1e-6)   -- 1.2 x 10 must count 12, not 11.999
  self.tapCarry = self.tapCarry - credit
  db.taps = db.taps + credit
  local cd = self:CD()
  if cd.level < TCF.MAX_LEVEL then
    cd.xp = cd.xp + (self.FoodBuff and self:FoodBuff("xp") or 1) * mult * (self.PurrMult and self:PurrMult() or 1)
    self:SettleXP()
  end
  local cap = TCF.TAP_COIN_CAP
  if paidCap ~= cap then   -- (re)built when the cap changes
    paid, paidHead, paidCap = {}, 0, cap
    for i = 1, cap do paid[i] = -10 end
  end
  local nextSlot = paidHead % cap + 1   -- the oldest of the last `cap` paid taps
  if now - paid[nextSlot] >= 0.999 then   -- (a hair under 1: steady 10 a second all earn despite timer rounding)
    paidHead = nextSlot; paid[nextSlot] = now
    db.coinFrac = db.coinFrac + COINS_PER_TAP * mult
    if db.coinFrac >= 1 then
      local whole = floor(db.coinFrac)
      db.coinFrac = db.coinFrac - whole
      self:AddCoins(whole)
    end
  end
  if self.AdvTapStrike then self:AdvTapStrike() end
  if self.ProfTap then self:ProfTap() end
  if tps > db.stats.peakTPS then db.stats.peakTPS = tps end
  if tps >= FRENZY_TPS then
    if not self.inFrenzy then
      self.inFrenzy = true
      db.stats.frenzies = db.stats.frenzies + 1
    end
    self.frenzyUntil = now + 0.6
  end
  if random() < DROP_CHANCE then
    db.stats.drops = db.stats.drops + 1
    local it = self:RollItem(self:RollRarity({ 45, 32, 16, 6, 1 }), true)
    if it then self:GrantItem(it, "Lucky find while tapping") end
  end
  self:MarkDirty()
end

-- Paw mapping: A / left arrow = left paw, D / right arrow = right paw (like
-- strafing); every other key alternates paws.
local LEFT_KEYS = { A = true, LEFT = true }
local RIGHT_KEYS = { D = true, RIGHT = true }
local IGNORE = { LSHIFT = true, RSHIFT = true, LCTRL = true, RCTRL = true, LALT = true, RALT = true, LMETA = true, RMETA = true, UNKNOWN = true }

function TCF:OnKey(key)
  if IGNORE[key] then return end
  self:Tap(LEFT_KEYS[key] and "L" or RIGHT_KEYS[key] and "R" or nil)
end

-- The listener propagates every key to the game, so it never swallows input.
-- SetPropagateKeyboardInput is restricted in combat on some clients, so set up
-- only out of combat, and only enable the keyboard once propagation is set.
function TCF:SetupKeyboard()
  if self.kbReady then return true end
  local f = self.kbFrame
  if not f then
    f = CreateFrame("Frame", "TapCatForeverKeyListener", UIParent)
    f:SetSize(1, 1); f:SetPoint("TOPLEFT"); f:Show()
    self.kbFrame = f
  end
  if not f.SetPropagateKeyboardInput or not f.EnableKeyboard then return false end
  if InCombatLockdown and InCombatLockdown() then return false end
  local ok = pcall(f.SetPropagateKeyboardInput, f, true)
  if not ok then return false end
  ok = pcall(f.EnableKeyboard, f, true)
  if not ok then return false end
  f:SetScript("OnKeyDown", function(_, key) TCF:OnKey(key) end)
  self.kbReady = true
  return true
end

---------------------------------------------------------------- loot
function TCF:RollRarity(weights)
  local total = 0
  for i = 1, 5 do total = total + (weights[i] or 0) end
  local r = random() * total
  for i = 1, 5 do
    r = r - (weights[i] or 0)
    if r <= 0 and (weights[i] or 0) > 0 then return i end
  end
  return 1
end

-- Pick an item of a rarity that the current class can wear: its own class sets (65%)
-- or universal cosmetics; favours unowned items.
function TCF:RollItem(rarity, preferUnowned)
  local class = self.db.class
  local wantClass = random() < 0.65
  local pools = { {}, {} } -- [1] unowned, [2] all
  for _, it in ipairs(TCF.ITEM_LIST) do
    if it.rarity == rarity and it.source == "loot" then
      local fits = (wantClass and it.class == class) or (not wantClass and it.class == nil)
      if fits then
        pools[2][#pools[2] + 1] = it
        if not self.db.owned[it.id] then pools[1][#pools[1] + 1] = it end
      end
    end
  end
  if #pools[2] == 0 then -- fallback: anything of that rarity this class can wear
    for _, it in ipairs(TCF.ITEM_LIST) do
      if it.rarity == rarity and it.source == "loot" and (it.class == nil or it.class == class) then pools[2][#pools[2] + 1] = it end
    end
  end
  local pool = (preferUnowned and #pools[1] > 0 and random() < 0.85) and pools[1] or pools[2]
  if #pool == 0 then return nil end
  return pool[random(#pool)]
end

-- Gives an item; duplicates are salvaged into TapCoins. Returns isNew, salvage.
-- reveal: show the loot box popup (chests); otherwise it only pops up when the
-- window is open, so passive drops never interrupt gameplay.
function TCF:GrantItem(it, reason, reveal, chestKey)
  local db = self.db
  local salvage = 0
  local isNew = not db.owned[it.id]
  if self.NoteItemSource then self:NoteItemSource(it.id, reason, nil, not isNew) end
  if isNew then
    db.owned[it.id] = 1
  else
    db.owned[it.id] = db.owned[it.id] + 1
    salvage = TCF.RARITY[it.rarity].salvage
    self:AddCoins(salvage)
  end
  local msg = (reason and (reason .. ": ") or "") .. TCF.ItemLink(it)
  if not isNew then msg = msg .. string.format(" (duplicate, salvaged for %d TapCoins)", salvage) end
  self:Print(msg)
  -- chests show the loot box; anything else gets a small notice (ChestReel.lua decides)
  if self.ShowLootReveal then self:ShowLootReveal(it, isNew, salvage, reason, chestKey) end
  if self.cat and self.cat.SetFaceFor then self.cat:SetFaceFor(it.rarity >= 4 and "sparkle" or "happy", 2.5) end
  self:PlaySound(it.rarity >= 4 and "rare" or "loot")
  self:MarkDirty()
  self:RefreshAll()
  return isNew, salvage
end

-- The gear quality a chest most often holds (same mapping as TCF:ChestOdds): it colours the
-- chest's name in chat. Pouch and Strongbox: green, Heroic Cache and Dungeon Chest: blue,
-- Raider's Hoard: purple.
function TCF.ChestQuality(ch)
  if ch.raidLoot then return 4 end
  local byQ, bestQ, bestW = {}, 2, -1
  for r = 1, 5 do
    local q = max(2, min(4, r))
    byQ[q] = (byQ[q] or 0) + (ch.weights[r] or 0)
  end
  for q = 2, 4 do if (byQ[q] or 0) > bestW then bestQ, bestW = q, byQ[q] end end
  return bestQ
end

---------------------------------------------------------------- chests per cat (1.5.4)
-- Every class's cat has its own Treasure Bag: classData[class].chests[key][level] = count. Each
-- chest is stamped with the level of the cat that earned it and holds gear for that level
-- (TCF:ChestLevel while it opens), so a chest kept for later still holds the same gear.
-- db.keys is a stand-in that reads and writes the current cat's counts (old code and saves).
local function clampLevel(l) return min(TCF.MAX_LEVEL or 60, max(1, floor(tonumber(l) or 1))) end
TCF.ClampChestLevel = clampLevel

-- whose bag a chest goes to: the class asked for, else the cat an expedition or a trade is for,
-- else the cat you are playing
function TCF:ChestOwner(class)
  class = class or self.chestOwner or self.tradeClass or self.db.class
  if not (class and self.db.classData[class]) then class = self.db.class end
  return class
end

local function stampTable(self, class, key, create)
  local cd = self.db.classData[class]
  if not cd then return nil end
  if type(cd.chests) ~= "table" then
    if not create then return nil end
    cd.chests = {}
  end
  local t = cd.chests[key]
  if type(t) ~= "table" then
    if not create then return nil end
    t = {}; cd.chests[key] = t
  end
  return t
end

-- unopened chests of one kind in a cat's bag
function TCF:ChestsOf(key, class)
  local t = stampTable(self, self:ChestOwner(class), key)
  local n = 0
  for _, c in pairs(t or {}) do n = n + (tonumber(c) or 0) end
  return n
end

-- { { level = 20, n = 2 }, ... } highest level first
function TCF:ChestStamps(key, class)
  local out = {}
  for lv, c in pairs(stampTable(self, self:ChestOwner(class), key) or {}) do
    if (tonumber(c) or 0) > 0 then out[#out + 1] = { level = tonumber(lv), n = c } end
  end
  table.sort(out, function(a, b) return a.level > b.level end)
  return out
end

function TCF:AddChests(key, n, class, level)
  if not TCF.CHEST_BY_KEY[key] or (n or 0) <= 0 then return end
  class = self:ChestOwner(class)
  level = clampLevel(level or self.db.classData[class].level)
  local t = stampTable(self, class, key, true)
  t[level] = (t[level] or 0) + n
end

-- Takes one chest out of a cat's bag and returns its level stamp: the level asked for, else the
-- level of the last one of that kind opened (Open another), else the highest.
function TCF:TakeChest(key, class, level)
  local t = stampTable(self, self:ChestOwner(class), key)
  if not t then return nil end
  -- (a level asked for that has none left, such as a stale Open button, opens nothing)
  if level then
    if (t[level] or 0) <= 0 then return nil end
    t[level] = t[level] - 1
    if t[level] <= 0 then t[level] = nil end
    return level
  end
  local pick
  local last = self.lastStamp and self.lastStamp[key]
  if not pick and last and (t[last] or 0) > 0 then pick = last end
  if not pick then
    for lv, c in pairs(t) do if (tonumber(c) or 0) > 0 and (not pick or lv > pick) then pick = lv end end
  end
  if not pick then return nil end
  t[pick] = t[pick] - 1
  if t[pick] <= 0 then t[pick] = nil end
  return pick
end

-- db.keys: the current cat's chest counts. Setting a count adds chests stamped with the cat's
-- level or takes some out.
local keysMeta = {
  __index = function(_, k)
    if TCF.CHEST_BY_KEY[k] then return (TCF.db and TCF.db.classData) and TCF:ChestsOf(k) or 0 end
  end,
  __newindex = function(t, k, v)
    if not TCF.CHEST_BY_KEY[k] then rawset(t, k, v); return end
    if not (TCF.db and TCF.db.classData) then return end
    local want, have = max(0, floor(tonumber(v) or 0)), TCF:ChestsOf(k)
    if want > have then TCF:AddChests(k, want - have)
    else for _ = 1, have - want do TCF:TakeChest(k) end end
  end,
}

-- Once per load: chests saved by 1.5.3 and older (db.keys, one bag per character) move to the
-- cat you are playing, stamped with its level, and db.keys becomes the stand-in. A save that
-- has none left (or was already moved) changes nothing.
function TCF:InitChests(char)
  char = char or self.charData
  local old = char and char.keys
  if type(old) == "table" and getmetatable(old) ~= keysMeta then
    local cd = self.db.classData[self.db.class]
    for k, v in pairs(old) do
      local n = floor(tonumber(v) or 0)
      if TCF.CHEST_BY_KEY[k] and n > 0 then self:AddChests(k, n, self.db.class, cd and cd.level) end
    end
  end
  if char then char.keys = setmetatable({}, keysMeta) end
end

-- Puts an unopened chest in a cat's Treasure Bag, stamped with that cat's level. force = true
-- prints the chat line even with chat messages off (only for a reward the player's own click
-- earned, such as joining the leaderboard). class: the cat it goes to (default: TCF:ChestOwner),
-- level: its stamp (default: that cat's level).
function TCF:AwardChest(key, source, force, class, level)
  local ch = TCF.CHEST_BY_KEY[key]
  -- an expedition being claimed (TreasureBag.lua): only its own chests go to a cat that went
  local claim = self.claimChests
  if not class and claim and source == claim.source then class = claim.owner end
  class = self:ChestOwner(class)
  level = clampLevel(level or self.db.classData[class].level)
  self:AddChests(key, 1, class, level)
  -- "(level 25)", unless the source already says it ("Level 25")
  local lvText = (source == "Level " .. level) and "" or string.format(" (level %d)", level)
  local col = TCF.RARITY[TCF.ChestQuality(ch)]
  local hex = ch.color or (col and col.hex) or "ff1eff00"
  local art = ch.name:find("^[AEIOUaeiou]") and "an" or "a"
  if class ~= self.db.class then
    local cl = TCF.CLASS_BY_KEY[class]
    self:Print(string.format("%s: your %s cat earned %s |c%s%s|r%s. It waits in that cat's Treasure Bag.", source or "Reward", cl and cl.name or class, art, hex, ch.name, lvText), force)
  else
    self:Print(string.format("%s: you earned %s |c%s%s|r%s. Open it from your Treasure Bag.", source or "Reward", art, hex, ch.name, lvText), force)
  end
  self:PlaySound("loot")
  self:MarkDirty()
  self:RefreshAll()
end

-- unopened chests in a cat's bag (default: the cat you are playing)
function TCF:ChestCount(class)
  local n = 0
  for _, ch in ipairs(TCF.CHESTS) do n = n + self:ChestsOf(ch.key, class or self.db.class) end
  return n
end

-- The level a chest's gear is for: the stamp of the chest being opened, else the cat's level.
function TCF:ChestLevel()
  if self.openStamp then return clampLevel(self.openStamp) end
  local cd = self:CD()
  return clampLevel(cd and cd.level)
end

-- Skins are bought from the Appearance tab
function TCF:BuySkin(id)
  local it = TCF.ITEMS[id]
  if not it or it.slot ~= "skin" or self.db.owned[id] or not it.skinPrice then return false end
  if not self:SpendCoins(it.skinPrice) then return false end
  self.db.owned[id] = 1
  if self.NoteItemSource then self:NoteItemSource(id, "Bought in the Appearance tab") end
  self.db.look.skin = id
  self:Print("Your cat is now a " .. TCF.ItemLink(it) .. ".", true)
  if self.ShowLootReveal then self:ShowLootReveal(it, true, 0, "New skin") end
  self:PlaySound("buy")
  self:MarkDirty(); self:RefreshAll()
  return true
end

-- Gives a skin found somewhere in the game (boss drop, chest, quest, expedition, dungeon).
-- Skins found in a chest show in the chest's loot box; any other find gets a small notice
-- (LootToast.lua). force = true prints the chat line even
-- with chat messages off: only for the player's own actions (opening a chest, claiming
-- a quest or expedition, crafting), not for boss drops or dungeon runs.
function TCF:GrantSkin(id, reason, force)
  local it = TCF.ITEMS[id]
  if not it or self.db.owned[id] then return false end
  self.db.owned[id] = 1
  reason = reason or "Rare drop"
  if self.NoteItemSource then self:NoteItemSource(id, reason) end
  self:Print(reason .. ": the " .. TCF.ItemLink(it) .. " cat skin. Wear it from the Appearance tab.", force)
  -- chests show the loot box; anything else gets a small notice (ChestReel.lua decides)
  if self.ShowLootReveal then self:ShowLootReveal(it, true, 0, reason, self.skinChestKey) end
  self:PlaySound("rare")
  self:MarkDirty(); self:RefreshAll()
  return true
end

-- Rolls the skins whose "get" source matches (see SKINS in Data.lua): each unowned
-- matching skin rolls its own chance, and at most one is given per event (a random
-- one of the winners). match(get) says whether a skin's source fits this event.
-- Returns the skin item given, or nil. force is passed on to GrantSkin.
function TCF:RollSkinSource(kind, match, reason, force)
  local won
  local n = 0
  for _, it in ipairs(TCF.ITEM_LIST) do
    local g = it.get
    if it.slot == "skin" and g and g.kind == kind and not self.db.owned[it.id] and (not match or match(g))
      and random() < (g.chance or 0) then
      n = n + 1
      if random(n) == 1 then won = it end -- keeps an even pick among the winners
    end
  end
  if won and self:GrantSkin(won.id, reason, force) then return won end
end

-- chests hold gear this often, otherwise a cosmetic (also used by the chest reel and the Shop text)
TCF.CHEST_GEAR_CHANCE = 0.9

-- A few TapCoins on top of what a chest holds, now and then: most chests hold none, about a
-- third hold a tiny amount and about 1 in 20 a big handful (amounts per chest: ch.coins in Data.lua).
-- On average that is a few TapCoins per chest, a small part of a day's TapCoins.
TCF.CHEST_COIN_ODDS = { tiny = 0.35, big = 0.05 }
function TCF:RollChestCoins(ch)
  local c = ch and ch.coins
  if not c then return 0 end
  local r = random()
  local span = (r < TCF.CHEST_COIN_ODDS.big and c.big) or (r < TCF.CHEST_COIN_ODDS.big + TCF.CHEST_COIN_ODDS.tiny and c.tiny) or nil
  if not span then return 0 end
  return random(span[1], span[2])
end

-- useKey: open one from the current cat's Treasure Bag (level: the stamp to open, see
-- TCF:TakeChest); otherwise buy one for the cat you are playing, at its level.
function TCF:OpenChest(key, useKey, level)
  local ch = TCF.CHEST_BY_KEY[key]
  if not ch then return end
  local stamp
  if useKey then
    stamp = self:TakeChest(key, self.db.class, level)
    if not stamp then return end
  elseif not ch.cost or not self:SpendCoins(ch.cost) then
    return   -- (a chest with no price, like the Dungeon Chest or Raider's Hoard, is never sold)
  else
    stamp = self:ChestLevel()
  end
  self.lastStamp = self.lastStamp or {}
  self.lastStamp[key] = stamp
  self.openStamp = stamp   -- the chest's gear is for its level stamp (TCF:ChestLevel)
  self.db.stats.chests = self.db.stats.chests + 1
  if ch.raidLoot then self.db.stats.hoards = (self.db.stats.hoards or 0) + 1 end
  if ch.dungeonLoot then self.db.stats.dungeonChests = (self.db.stats.dungeonChests or 0) + 1 end
  self.skinChestKey = key   -- a skin found in this chest shows in the chest's loot box
  -- now and then a few TapCoins too. Rolled first so the loot box can show them while it opens
  -- (TCF.chestCoins, only during the opening); afterwards on TCF.lastChest.coins (nil when none).
  local coins = self:RollChestCoins(ch)
  self.chestCoins = coins > 0 and coins or nil
  local ok, a, b, c = pcall(function()
    local a, b, c = self:OpenChestContents(ch, key)
    -- a few skins are only found in one kind of chest (rolled on top of the chest's
    -- normal contents; at most one skin per chest)
    if not (self.lastChest and self.lastChest.skin) then
      self:RollSkinSource("chest", function(g) return g.chest == key end, "Found in a " .. ch.name, true)
    end
    if coins > 0 then
      self.lastChest = self.lastChest or {}
      self.lastChest.coins = coins
      self:AddCoins(coins)
      self:Print(string.format("Also in the %s: %d TapCoins.", ch.name, coins))
    end
    return a, b, c
  end)
  self.skinChestKey, self.chestCoins, self.openStamp = nil, nil, nil   -- always cleared, even if something above failed
  if not ok then error(a, 0) end
  if self.lastChest then self.lastChest.stamp = stamp end
  return a, b, c
end

---------------------------------------------------------------- chest gear
-- Real legendaries (q == 5), from the loot pools so Blizzard's placeholder copies (Gear.lua
-- keeps them out of every pool) and crafted gear never show up.
local legendaries
function TCF:Legendaries()
  if not legendaries then
    legendaries = {}
    local seen = {}
    local function scan(list)
      for _, it in ipairs(list or {}) do
        if it.q == 5 and not it.crafted and not it.retired and not seen[it] then seen[it] = true; legendaries[#legendaries + 1] = it end
      end
    end
    for _, list in pairs(TCF.WORLD_POOL or {}) do scan(list) end
    for _, list in pairs(TCF.TIER_POOL or {}) do scan(list) end
    for _, bosses in pairs(TCF.BOSS_LOOT or {}) do for _, list in pairs(bosses) do scan(list) end end
    table.sort(legendaries, function(a, b) return a.id < b.id end)
  end
  return legendaries
end

-- The legendaries a class can use: the ones made for it (Atiesh for a Mage) when there are
-- any, otherwise every one it can wield.
function TCF:LegendariesFor(class)
  class = class or self.db.class
  local suits, usable = {}, {}
  for _, it in ipairs(self:Legendaries()) do
    if self:GearUsable(it, class) then
      usable[#usable + 1] = it
      if self:GearSuits(it, class) then suits[#suits + 1] = it end
    end
  end
  return #suits > 0 and suits or usable
end

function TCF:RollLegendary(class)
  local pool = self:LegendariesFor(class)
  if #pool > 0 then return pool[random(#pool)] end
end

-- Adventure tier numbers of the raids a class's cat has reached (its current zone or any zone
-- up to its best stage). all = every raid. A cat that hasn't reached one gets the first raid.
function TCF:RaidTiers(class, all)
  local cd = self.db.classData[class or self.db.class]
  local adv = cd and cd.adv
  local upTo = adv and max(floor((adv.best or 0) / 100), adv.tier or 0) or 0
  local list, first = {}, nil
  for ti, t in ipairs(TCF.TIERS or {}) do
    if t.raid then
      first = first or ti
      if all or ti <= upTo then list[#list + 1] = ti end
    end
  end
  if #list == 0 and first then list[1] = first end
  return list
end

-- Adventure tiers come in three kinds: raids (t.raid), open-world zones (Elwynn Forest and
-- Westfall: no instance, so their art is one of the addon's own scenes, a file name instead of
-- a WoW file id) and dungeons (everything else). Takes a tier table or a tier number.
function TCF.IsDungeonTier(t)
  if type(t) == "number" then t = TCF.TIERS and TCF.TIERS[t] end
  return t ~= nil and not t.raid and type(t.art) ~= "string"
end

-- Adventure tier numbers of the dungeons a class's cat has reached (its current zone or any
-- zone up to its best stage), like RaidTiers. A cat that hasn't reached one gets the first.
function TCF:DungeonTiers(class)
  local cd = self.db.classData[class or self.db.class]
  local adv = cd and cd.adv
  local upTo = adv and max(floor((adv.best or 0) / 100), adv.tier or 0) or 0
  local list, first = {}, nil
  for ti, t in ipairs(TCF.TIERS or {}) do
    if TCF.IsDungeonTier(t) then
      first = first or ti
      if ti <= upTo then list[#list + 1] = ti end
    end
  end
  if #list == 0 and first then list[1] = first end
  return list
end

-- Dungeon loot of quality q from these dungeons that the class can use (own = only gear made
-- for the class): boss loot, or when the bosses drop none of that quality (few dungeon bosses
-- drop Uncommon or Epic gear) the dungeons' other loot.
local function dungeonGear(self, tiers, class, q, own)
  local out = {}
  local function scan(list)
    for _, it in ipairs(list or {}) do
      if it.q == q and not it.crafted and not it.retired
        and (own and self:GearSuits(it, class) or not own and self:GearUsable(it, class)) then
        out[#out + 1] = it
      end
    end
  end
  for _, ti in ipairs(tiers) do
    for _, list in pairs(TCF.BOSS_LOOT[ti] or {}) do scan(list) end
  end
  if #out == 0 then
    for _, ti in ipairs(tiers) do scan(TCF.TIER_POOL[ti]) end
  end
  return out
end

-- The pieces of a list close to the level: required level from 10 below to 3 above it (empty
-- when the dungeons reached have nothing that close). Never gear more than 3 levels above the cat.
local function nearLevel(list, level)
  local near = {}
  for _, it in ipairs(list) do
    local r = it.req or 0
    if r >= level - 10 and r <= level + 3 then near[#near + 1] = it end
  end
  return near
end

-- Chest gear (1.5.3.1): what a chest can give a cat of this level, by quality. Required level
-- from 10 below to 3 above the cat (never more than 3 above), not crafted or retired, usable by
-- the class. World and dungeon loot near the level; raid loot only for cats of 55 and up.
-- Built once per class, level and quality.
local CHEST_UP, CHEST_DOWN = 3, 10
local bossSet, chestPools, chestPoolsKey
local function isBossLoot(it)
  if not bossSet then
    bossSet = {}
    for _, bosses in pairs(TCF.BOSS_LOOT or {}) do
      for _, list in pairs(bosses) do for _, g in ipairs(list) do bossSet[g] = true end end
    end
  end
  return bossSet[it]
end
function TCF:ChestGearPool(class, level, q)
  class = class or self.db.class
  level = min(60, max(1, floor(level or 1)))
  local key = class .. ":" .. level
  if chestPoolsKey ~= key then chestPools, chestPoolsKey = {}, key end
  if chestPools[q] then return chestPools[q] end
  local out, seen = {}, {}
  local function scan(list, lo, hi)
    for _, it in ipairs(list or {}) do
      local r = it.req or 0
      -- Epics only from boss loot: the few open-world Epics (Staff of Jordan and the like) are
      -- famously rare drops and never come from chests
      if it.q == q and not seen[it] and not it.crafted and not it.retired and r <= hi and r >= lo
        and (q < 4 or isBossLoot(it)) and self:GearUsable(it, class) then
        seen[it] = true; out[#out + 1] = it
      end
    end
  end
  local function fill(lo)
    local hi = level + CHEST_UP
    for b = floor(max(0, lo) / 5), floor(hi / 5) do scan(TCF.WORLD_POOL[b], lo, hi) end
    for ti, t in ipairs(TCF.TIERS or {}) do
      if not t.raid or level >= 55 then
        scan(TCF.TIER_POOL[ti], lo, hi)
        for _, list in pairs(TCF.BOSS_LOOT[ti] or {}) do scan(list, lo, hi) end
      end
    end
  end
  fill(level - CHEST_DOWN)
  if #out == 0 then fill(level - 25) end
  chestPools[q] = out
  return out
end

-- A piece from ChestGearPool, by weight: gear made for the class counts more, and a piece the
-- cat already has is rolled again (twice); an Epic it already has becomes a Rare. Nothing of that quality near the level: one quality lower.
function TCF:RollChestGear(class, level, q)
  class = class or self.db.class
  for wq = max(2, min(4, q or 2)), 2, -1 do
    local pool = self:ChestGearPool(class, level, wq)
    if #pool > 0 then
      local total, w = 0, {}
      for i, it in ipairs(pool) do
        local x = self:GearSuits(it, class) and 4 or 1
        w[i] = x; total = total + x
      end
      local pick
      for _ = 1, 3 do
        local r = random() * total
        for i, it in ipairs(pool) do
          r = r - w[i]
          if r <= 0 then pick = it; break end
        end
        pick = pick or pool[#pool]
        if not self:GearOwned(pick.id, class) then break end
      end
      -- never a second copy of an Epic: one the cat already has gives a Rare instead
      if not (wq >= 4 and self:GearOwned(pick.id, class)) then return pick end
    end
  end
end

-- Every piece a Dungeon Chest could hold for this class right now, by quality (the chest reel
-- shows these): { [2] = {...}, [3] = {...}, [4] = {...} }.
function TCF:DungeonChestPool(class, level)
  class = class or self.db.class
  level = level and clampLevel(level) or self:ChestLevel()
  local tiers = self:DungeonTiers(class)
  local out = {}
  for q = 2, 4 do out[q] = nearLevel(dungeonGear(self, tiers, class, q, false), level) end
  return out
end

-- Epic boss loot from one raid that the class can use. own = only gear made for the class.
local function raidEpics(self, ti, class, own)
  local out = {}
  for _, list in pairs(TCF.BOSS_LOOT[ti] or {}) do
    for _, it in ipairs(list) do
      if it.q == 4 and not it.crafted and (own and self:GearSuits(it, class) or not own and self:GearUsable(it, class)) then
        out[#out + 1] = it
      end
    end
  end
  return out
end

-- Every epic a Raider's Hoard could hold for this class right now (the chest reel shows these).
-- all = from every raid instead (a Legendary rarity roll in other chests).
function TCF:RaidHoardPool(class, all)
  class = class or self.db.class
  local out = {}
  for _, ti in ipairs(self:RaidTiers(class, all)) do
    for _, it in ipairs(raidEpics(self, ti, class, false)) do out[#out + 1] = it end
  end
  return out
end

-- An epic from a raid boss: a random raid of the list (default: the raids the cat has reached),
-- then a random epic of its bosses, made for the class 80% of the time like boss loot.
function TCF:RollRaidEpic(class, raids)
  class = class or self.db.class
  raids = raids or self:RaidTiers(class)
  if #raids == 0 then return nil end
  for _ = 1, 6 do
    local ti = raids[random(#raids)]
    local own = random() < 0.8
    local cands = raidEpics(self, ti, class, own)
    if #cands == 0 and own then cands = raidEpics(self, ti, class, false) end
    if #cands > 0 then return cands[random(#cands)] end
  end
  -- unlucky picks (a raid with nothing for this class): any epic from any of the raids
  local cands = {}
  for _, ti in ipairs(raids) do
    for _, it in ipairs(raidEpics(self, ti, class, false)) do cands[#cands + 1] = it end
  end
  if #cands > 0 then return cands[random(#cands)] end
end

-- World gear of quality q near the level. RollWorldLoot quietly drops a quality when nothing
-- of it is near the level (there is no blue in the level-9 window, for example), so look a few
-- levels higher before settling for less.
local function worldGearOfQuality(self, level, q)
  local w = { q == 2 and 1 or 0, q == 3 and 1 or 0, q == 4 and 1 or 0 }
  local fallback
  for _, up in ipairs({ 0, 3, 6, 10 }) do
    local g = self:RollWorldLoot(level + up, nil, w)
    if g and g.q == q then return g end
    fallback = fallback or g
    if level + up >= 60 then break end
  end
  return fallback
end

-- Gear of quality q (2 to 4) for a Dungeon Chest: loot from the dungeons the cat has reached in
-- Adventure, required level from 10 below to 3 above the cat's, made for the class 80% of the
-- time like boss loot. When those dungeons have nothing of that quality that close to the level
-- (the early ones drop no Epics, few dungeons drop Uncommon gear, and a cat can level far ahead
-- of its Adventure progress) it is world gear of that quality near the level instead, so the
-- odds the chest shows hold. Never a Legendary.
function TCF:RollDungeonGear(class, q)
  class = class or self.db.class
  local level = self:ChestLevel()
  local tiers = self:DungeonTiers(class)
  local fallback
  for wq = max(2, min(4, q or 3)), 2, -1 do
    local own = random() < 0.8
    local cands = nearLevel(dungeonGear(self, tiers, class, wq, own), level)
    if #cands == 0 and own then cands = nearLevel(dungeonGear(self, tiers, class, wq, false), level) end
    if #cands > 0 then return cands[random(#cands)] end
    local g = self:RollChestGear(class, level, wq)
    if g and g.q == wq then return g end
    fallback = fallback or g
  end
  return fallback
end

-- Gear for a chest's rarity roll: Uncommon to Epic near the cat's level (half the time boss loot
-- from zones it has cleared), or a raid boss Epic for a Legendary roll.
function TCF:ChestGear(ch, rarity)
  local class = self.db.class
  local level = self:ChestLevel()
  -- raid epics are level 60 gear: a Raider's Hoard or a Legendary roll gives them to cats of 55
  -- and up; younger cats get the best gear near their level instead
  if ch.raidLoot or rarity >= 5 then
    if level >= 55 then
      local g = ch.raidLoot and self:RollRaidEpic(class) or self:RollRaidEpic(class, self:RaidTiers(class, true))
      if g then return g end
    end
    return self:RollChestGear(class, level, 4)
  end
  if ch.dungeonLoot then return self:RollDungeonGear(class, rarity) end
  local q = max(2, min(4, rarity))
  local gear
  -- half the time: real boss loot from a zone this class has cleared, if it fits the level
  local adv = self:CD().adv
  local bestTier = floor(adv.best / 100)
  if bestTier >= 1 and random() < 0.5 then
    for _ = 1, 6 do
      local ti = random(max(1, bestTier - 3), bestTier)
      local t = TCF.TIERS[ti]
      local it = t and (not t.raid or level >= 55) and self:RollBossLoot(ti, random(#t.bosses))
      if it and it.q == q and (it.req or 0) <= level + CHEST_UP and (it.req or 0) >= level - CHEST_DOWN then gear = it; break end
    end
  end
  return gear or self:RollChestGear(class, level, q)
end

-- Odds of what a chest holds, per opening, in the order they are listed in tooltips:
-- { { label, percent, hex colour }, ... }. Same rules as TCF:OpenChestContents.
-- level: the chest's level stamp (default: TCF:ChestLevel).
function TCF:ChestOdds(ch, level)
  local out = {}
  level = level and clampLevel(level) or self:ChestLevel()
  local skin = (ch.key == "heroic" and #self:UnownedShopSkins() > 0) and TCF.CHEST_SKIN_CHANCE or 0
  local rest = 1 - skin
  local legend = (level >= 60) and rest * (ch.legendary or 0) or 0
  rest = rest - legend
  local gearShare = ch.gearOnly and 1 or TCF.CHEST_GEAR_CHANCE
  local total = 0
  for r = 1, 5 do total = total + (ch.weights[r] or 0) end
  local byQ = {}
  for r = 1, 5 do
    local q = ch.raidLoot and 4 or max(2, min(4, r))
    byQ[q] = (byQ[q] or 0) + (ch.weights[r] or 0) / total
  end
  -- a quality with no gear near the cat's level gives the next one down (TCF:RollChestGear)
  if self.ChestGearPool and not ch.dungeonLoot then
    for q = 4, 3, -1 do
      if (byQ[q] or 0) > 0 and not ((ch.raidLoot or q == 4 and ch.legendary) and level >= 55)
        and #self:ChestGearPool(nil, level, q) == 0 then
        byQ[q - 1] = (byQ[q - 1] or 0) + byQ[q]; byQ[q] = 0
      end
    end
  end
  for q = 2, 4 do
    if (byQ[q] or 0) > 0 then
      local col = TCF.RARITY[q]
      out[#out + 1] = { col.name .. " gear", rest * gearShare * byQ[q] * 100, col.hex }
    end
  end
  if legend > 0 then out[#out + 1] = { "Legendary gear", legend * 100, TCF.RARITY[5].hex } end
  if gearShare < 1 then out[#out + 1] = { "Cosmetic", rest * (1 - gearShare) * 100, "ffd28cff" } end
  if skin > 0 then out[#out + 1] = { "Cat skin from the shop", skin * 100, "ffffd100" } end
  return out
end

-- "81%", "8.1%", "0.2%"
function TCF.OddsText(pct)
  if pct >= 10 then return string.format("%d%%", floor(pct + 0.5)) end
  local s = string.format("%.1f", pct):gsub("%.0$", "")
  return s .. "%"
end

-- a Heroic Cache holds a cat skin from the shop you don't own yet this often
TCF.CHEST_SKIN_CHANCE = 0.03

-- shop skins this player does not own yet (what a Heroic Cache can give). ChestOdds and
-- OpenChestContents both use it, so the odds shown and the real roll always agree.
function TCF:UnownedShopSkins()
  local pool, owned = {}, (self.db and self.db.owned) or {}
  for _, it in ipairs(TCF.ITEM_LIST) do
    if it.slot == "skin" and it.skinPrice and not owned[it.id] then pool[#pool + 1] = it end
  end
  return pool
end

-- What is inside a chest (the chest is already paid for).
function TCF:OpenChestContents(ch, key)
  self.lastChest = nil
  local rarity = self:RollRarity(ch.weights)
  if key == "heroic" and random() < TCF.CHEST_SKIN_CHANCE then
    local pool = self:UnownedShopSkins()
    if #pool > 0 then
      local it = pool[random(#pool)]
      self:GrantSkin(it.id, "Found in a " .. ch.name, true)
      self.lastChest = { item = it, isNew = true, salvage = 0, skin = true }
      return it, true
    end
  end
  local gear
  if self.RollWorldLoot then
    -- a real Legendary: about 1 in 500 Heroic Caches and 1 in 100 Raider's Hoards. A class
    -- that can use none of them gets the raid boss Epic instead.
    if (ch.legendary or 0) > 0 and self:ChestLevel() >= 60 and random() < ch.legendary then
      gear = self:RollLegendary()
      if not gear then rarity = 5 end
    end
    -- 90%: real gear for your current class and level; 10%: a cosmetic (gearOnly: always gear)
    if not gear and (ch.gearOnly or random() < TCF.CHEST_GEAR_CHANCE) then
      gear = self:ChestGear(ch, rarity)
    end
  end
  if gear then
    local isNew = self:GrantGear(gear, ch.name, true, key)
    self.lastChest = { gear = gear, isNew = isNew }
    return gear, isNew
  end
  -- a gear-only chest with nothing to give (should not happen): a cosmetic of its best rarity
  local it = self:RollItem(rarity, true)
  local isNew, salvage = self:GrantItem(it, ch.name, true, key)
  self.lastChest = { item = it, isNew = isNew, salvage = salvage }
  return it, isNew, salvage
end

---------------------------------------------------------------- daily shop
local function today() return date("%Y%m%d") end

local function seededRandom(seed)
  local s = seed % 2147483647
  if s <= 0 then s = s + 2147483646 end
  return function(n)
    s = (s * 16807) % 2147483647
    return n and (s % n) + 1 or s / 2147483647
  end
end

function TCF:SecondsUntilReset()
  local t = date("*t")
  return (23 - t.hour) * 3600 + (59 - t.min) * 60 + (60 - t.sec)
end

function TCF:RerollCost() return 50 * (2 ^ min(self.db.shop.rerolls, 5)) end

function TCF:BuildShop(force)
  local shop = self.db.shop
  local day = today()
  if shop.day ~= day then
    shop.day = day; shop.rerolls = 0; force = true
  end
  if not force and #shop.stock > 0 then return end
  local seed = tonumber(day) * 7 + shop.rerolls * 7919 + (self.db.taps % 997)
  local rnd = seededRandom(seed)
  local weights = { 30, 30, 22, 13, 5 }
  local stock, used = {}, {}
  local attempts = 0
  while #stock < 3 and attempts < 400 do
    attempts = attempts + 1
    local r, roll, acc = 1, rnd() * 100, 0
    for i = 1, 5 do acc = acc + weights[i]; if roll <= acc then r = i; break end end
    local wantClass = #stock < 2
    local cands = {}
    for _, it in ipairs(TCF.ITEM_LIST) do
      if it.rarity == r and it.source == "loot" and not used[it.id] and not self.db.owned[it.id]
        and ((wantClass and it.class == self.db.class) or (not wantClass and it.class ~= self.db.class)) then
        cands[#cands + 1] = it
      end
    end
    if #cands > 0 then
      local it = cands[rnd(#cands)]
      used[it.id] = true
      stock[#stock + 1] = it.id
    end
  end
  shop.stock = stock
  shop.bought = {}
end

function TCF:RerollShop()
  local cost = self:RerollCost()
  if not self:SpendCoins(cost) then return false end
  self.db.shop.rerolls = self.db.shop.rerolls + 1
  self:BuildShop(true)
  self:RefreshAll()
  return true
end

function TCF:BuyItem(id)
  local it = TCF.ITEMS[id]
  if not it or self.db.owned[id] then return false end
  if not self:SpendCoins(it.price) then return false end
  self.db.owned[id] = 1
  if self.NoteItemSource then self:NoteItemSource(id, "Daily Wares in the Shop") end
  self.db.shop.bought[id] = true
  self:Print("Purchased " .. TCF.ItemLink(it) .. ".", true)
  if self.ShowLootReveal then self:ShowLootReveal(it, true, 0, "Purchased") end
  self:PlaySound("buy")
  self:MarkDirty()
  self:RefreshAll()
  return true
end

---------------------------------------------------------------- daily login
-- Racial heritage: the accessory for this character's race, bought in the Shop.
TCF.RACE_PRICE = 600

function TCF:RaceItemForPlayer()
  if not UnitRace then return end
  local raceName, raceFile = UnitRace("player")
  if self.IsSecret(raceName) or self.IsSecret(raceFile) then return end
  local id = raceFile and TCF.RACE_ITEM[raceFile]
  if not id then
    local n = ((raceName or "") .. " " .. (raceFile or "")):lower()
    if n:find("sky") or n:find("high order") or n:find("windshaper") then id = "race_skyborne" end
  end
  return id and TCF.ITEMS[id], raceName
end

function TCF:BuyRaceAccessory()
  local it, raceName = self:RaceItemForPlayer()
  if not it or self.db.owned[it.id] then return false end
  if not self:SpendCoins(TCF.RACE_PRICE) then return false end
  self.db.owned[it.id] = 1
  if self.NoteItemSource then self:NoteItemSource(it.id, "Racial heritage in the Shop") end
  self.db.ui.racial = true
  -- (1.6.0) it belongs to the cat you are playing, which puts it on
  local lo = self:GetLoadout()
  if not lo[it.slot] then lo[it.slot] = it.id end
  self:Print(string.format("Your cat shows its %s pride: %s.", raceName or "racial", TCF.ItemLink(it)), true)
  if self.ShowLootReveal then self:ShowLootReveal(it, true, 0, (raceName or "Racial") .. " heritage") end
  self:PlaySound("buy")
  self:MarkDirty(); self:RefreshAll()
  return true
end

function TCF:CheckDaily()
  local d = self.db.daily
  local t = today()
  if d.last == t then return end
  -- noon of the previous calendar day, so 23/25-hour DST days can't skip or repeat a day
  local y = date("*t")
  y.day, y.hour, y.min, y.sec, y.isdst = y.day - 1, 12, 0, 0, nil
  local yesterday = date("%Y%m%d", time(y))
  d.streak = (d.last == yesterday) and (d.streak + 1) or 1
  d.best = max(d.best, d.streak)
  d.last = t
  local bonus = 15 + 3 * min(d.streak, 10)
  self:AddCoins(bonus)
  self:Print(string.format("Daily treat: +%d TapCoins (streak: %d day%s).", bonus, d.streak, d.streak == 1 and "" or "s"))
end

---------------------------------------------------------------- stats & achievements
-- a class cat's collection (default: the cat you are playing): owned, total, owned per rarity
function TCF:CountOwned(class)
  local n, total, r = 0, 0, { 0, 0, 0, 0, 0 }
  local mine = self:Owned(class or self.db.class)
  -- A character can only buy its own race's heritage piece, so other races' pieces
  -- count toward the total only if this cat already owns them.
  local myRace = self:RaceItemForPlayer()
  for _, it in ipairs(TCF.ITEM_LIST) do
    if it.source ~= "retired" then
      local owned = mine[it.id]
      if it.source ~= "race" or owned or (myRace and myRace.id == it.id) then
        total = total + 1
        if owned then n = n + 1; r[it.rarity] = r[it.rarity] + 1 end
      end
    end
  end
  return n, total, r
end

function TCF:GetStat(stat)
  local db = self.db
  if stat == "taps" then return db.taps
  elseif stat == "level" then
    local best = 1
    for _, cd in pairs(db.classData) do if cd.level > best then best = cd.level end end
    return best
  elseif stat:match("^clear:") then
    local key = stat:sub(7)
    for ti, t in ipairs(TCF.TIERS) do
      if t.key == key then
        local code = ti * 100 + #t.bosses * 2
        for _, cd in pairs(db.classData) do if cd.adv.best >= code then return 1 end end
      end
    end
    return 0
  elseif stat == "skins" or stat == "dropSkins" then
    -- dropSkins: rare skins that can't be bought or earned from an achievement: Adventure
    -- boss drops (TCF.SKIN_DROPS: one entry or a list per boss) and skins with a "get"
    -- source (chest, quest, expedition, real dungeon or crafted)
    local drops = {}
    for _, d in pairs(TCF.SKIN_DROPS or {}) do
      if d.id then drops[d.id] = true else for _, e in ipairs(d) do drops[e.id] = true end end
    end
    -- (1.6.0) cosmetics belong to each class's cat: the best cat's collection counts
    local best = 0
    for _, cl in ipairs(TCF.CLASSES) do
      local mine, n = self:Owned(cl.key), 0
      for _, it in ipairs(TCF.ITEM_LIST) do
        if it.slot == "skin" and mine[it.id] and (stat == "skins" or drops[it.id] or it.get ~= nil) then n = n + 1 end
      end
      best = max(best, n)
    end
    return best
  elseif stat == "tradeGold" or stat == "renown" then
    -- every class's cat has its own trade: Trade Gold earned by all of them, the best Renown of one
    if not self.TradeTotals then return 0 end
    local life, renown = self:TradeTotals()
    return stat == "tradeGold" and life or renown
  elseif stat == "races" then
    -- heritage pieces are bought per race, so count distinct pieces any cat on the account owns
    local seen, n = {}, 0
    local function scan(owned)
      if type(owned) ~= "table" then return end
      for id in pairs(owned) do
        local it = TCF.ITEMS[id]
        if it and it.source == "race" and not seen[id] then seen[id] = true; n = n + 1 end
      end
    end
    local function scanCats(classData)
      if type(classData) ~= "table" then return end
      for _, cd in pairs(classData) do if type(cd) == "table" then scan(cd.owned) end end
    end
    scanCats(db.classData)
    local chars = TapCatForeverDB and rawget(TapCatForeverDB, "chars") or {}
    for _, ch in pairs(chars) do
      if type(ch) == "table" then scan(rawget(ch, "owned")); scanCats(rawget(ch, "classData")) end
    end
    return n
  elseif stat == "epicGear" or stat == "legendGear" then
    local q, n = stat == "epicGear" and 4 or 5, 0
    local seen = {}
    for key in pairs(db.classData) do
      for id in pairs(self:Bag(key)) do local it = TCF.GEAR[id]; if it and it.q == q and not seen[id] then seen[id] = true; n = n + 1 end end
    end
    return n
  elseif stat == "advTier" or stat == "bossKills" then
    local best, kills = 0, 0
    for _, cd in pairs(db.classData) do
      local b = cd.adv.best
      local bt = floor(b / 100)
      if bt >= 1 and TCF.TIERS[bt] and b < bt * 100 + #TCF.TIERS[bt].bosses * 2 then bt = bt - 1 end
      best = max(best, bt)
      kills = kills + cd.adv.bossKills
    end
    return stat == "advTier" and best or kills
  elseif stat == "coinsEarned" then return db.coinsEarned
  elseif stat == "coinsSpent" then return db.coinsSpent
  elseif stat == "streak" then return db.daily.best
  elseif stat == "owned" or stat == "ownedPct" or stat == "rares" or stat == "epics" or stat == "legends" then
    -- (1.6.0) the best class cat's collection counts, so playing another cat never loses progress
    local best = 0
    for _, cl in ipairs(TCF.CLASSES) do
      local n, total, r = self:CountOwned(cl.key)
      local v
      if stat == "owned" then v = n
      elseif stat == "ownedPct" then v = floor(n / max(1, total) * 100)
      elseif stat == "rares" then v = r[3] + r[4] + r[5]
      elseif stat == "epics" then v = r[4]
      else v = r[5] end
      best = max(best, v)
    end
    return best
  elseif stat == "classesPlayed" then
    local n = 0
    for _ in pairs(db.stats.classesPlayed) do n = n + 1 end
    return n
  elseif stat == "outfits" then
    local n = 0
    for _, lo in pairs(db.loadouts) do if lo.head and lo.chest and lo.main then n = n + 1 end end
    return n
  end
  return db.stats[stat] or 0
end

function TCF:CheckAchievements()
  local db = self.db
  for _, a in ipairs(TCF.ACHIEVEMENTS) do
    if not db.achievements[a.id] and self:GetStat(a.stat) >= a.goal then
      db.achievements[a.id] = time()
      self:AddCoins(a.coins)
      local extra = ""
      if a.item and TCF.ITEMS[a.item] and not db.owned[a.item] then
        db.owned[a.item] = 1
        if self.NoteItemSource then self:NoteItemSource(a.item, "Achievement: " .. a.name) end
        extra = " and " .. TCF.ItemLink(TCF.ITEMS[a.item])
      end
      if a.skin and TCF.ITEMS[a.skin] and not db.owned[a.skin] then
        db.owned[a.skin] = 1
        if self.NoteItemSource then self:NoteItemSource(a.skin, "Achievement: " .. a.name) end
        extra = extra .. " and the " .. TCF.ItemLink(TCF.ITEMS[a.skin]) .. " cat"
        if self.ShowLootReveal then self:ShowLootReveal(TCF.ITEMS[a.skin], true, 0, a.name) end
      end
      self:Print(string.format("Achievement earned: |cffffd100%s|r. Reward: %d TapCoins%s.", a.name, a.coins, extra))
      if self.cat then self.cat:Celebrate(a.name, 1, 0.82, 0.1, "Achievement earned") end
      self:PlaySound("ach")
      self:RefreshAll()
    end
  end
end

---------------------------------------------------------------- refresh plumbing
function TCF:MarkDirty() self.dirty = true end

function TCF:RefreshAll()
  if self.cat then self.cat:ApplyAppearance(self:GetAppearance()) end
  self:RefreshHUD()
  self:UpdateMinimapButton()
  if self.window and self.window:IsShown() then self.window:Refresh() end
  if self.bag and self.bag:IsShown() then self.bag:Refresh() end
end

function TCF:RefreshHUD()
  if self.hud and self.hud.Refresh then self.hud:Refresh() end
end

-- 4x per second housekeeping
local ticker = CreateFrame("Frame")
local acc, dailyAcc = 0, 0
ticker:SetScript("OnUpdate", function(_, elapsed)
  acc = acc + elapsed
  if acc < 0.25 then return end
  acc = 0
  local self = TCF
  if not self.db then return end
  if self.inFrenzy and GetTime() > (self.frenzyUntil or 0) then self.inFrenzy = false end
  if self.AdvTick then self:AdvTick(0.25) end
  if self.ProfessionsTick then self:ProfessionsTick(false, 0.25) end
  -- a session that runs past midnight still collects the new day's treat and keeps the streak
  dailyAcc = dailyAcc + 0.25
  if dailyAcc >= 60 then dailyAcc = 0; self:CheckDaily() end
  if self.dirty then
    self.dirty = false
    self:CheckAchievements()
    self:RefreshHUD()
    if self.window and self.window:IsShown() then self.window:RefreshLight() end
  end
end)

---------------------------------------------------------------- events
local ev = CreateFrame("Frame")
ev:RegisterEvent("ADDON_LOADED")
ev:RegisterEvent("PLAYER_LOGIN")
ev:RegisterEvent("PLAYER_REGEN_ENABLED")
pcall(ev.RegisterEvent, ev, "GLOBAL_MOUSE_DOWN")
-- Cast fallback (only used when no key press was seen): prefer SENT, else SUCCEEDED.
local CAST_EVENT
for _, e in ipairs({ "UNIT_SPELLCAST_SENT", "UNIT_SPELLCAST_SUCCEEDED" }) do
  local ok = pcall(ev.RegisterUnitEvent or ev.RegisterEvent, ev, e, "player")
  if ok then CAST_EVENT = e; break end
end

ev:SetScript("OnEvent", function(_, event, a1)
  if event == "ADDON_LOADED" and a1 == ADDON then
    TCF:InitDB()
  elseif event == "PLAYER_LOGIN" then
    TCF:CreateHUD()
    TCF:CreateMinimapButton()
    TCF:RegisterSettingsPanel()
    TCF:SetupKeyboard()
    TCF:CheckDaily()
    TCF:EnsureQuests()
    TCF:ProfessionsTick(true)
    TCF:BuildShop()
    TCF:RefreshAll()
    TCF:MarkDirty()
    if not TCF.db.welcomed and TCF.ShowWelcome then TCF:ShowWelcome() end
  elseif event == "PLAYER_REGEN_ENABLED" then
    TCF:SetupKeyboard()
  elseif event == "GLOBAL_MOUSE_DOWN" then
    if TCF.db and TCF.db.ui.mouse then
      TCF:Tap(a1 == "LeftButton" and "L" or a1 == "RightButton" and "R" or nil)
    end
  elseif event == CAST_EVENT then
    -- Fallback for when the keyboard listener isn't available: count casts
    -- that weren't already counted as a key press.
    -- Registered for the player only, so the (possibly secret) unit arg is never inspected.
    if GetTime() - lastInput > 0.35 then TCF:Tap() end
  end
end)

---------------------------------------------------------------- test mode
-- Shortcuts for trying every part of the game quickly. Turned on with /tcf testmode.
-- Locked to the developer's character, or a password on any other character.
-- Only hashes are stored here.
local TEST_KEY, DEV_NAMES = 282723659, { [282723659] = true, [1306739114] = true }
local function keyHash(s)
  local x = 5381
  for i = 1, #s do x = (x * 33 + s:byte(i)) % 4294967296 end
  return x
end
local function isDevCharacter()
  local name = UnitName and UnitName("player")
  if not name or TCF.IsSecret(name) then return false end
  return DEV_NAMES[keyHash(name:lower())] or false
end

function TCF:TestCheat(kind)
  local db = self.db
  if not db.ui.testMode then return end
  if kind == "coins" then self:AddCoins(5000)
  elseif kind == "gold" then local s = self:ProfState(); s.gold = s.gold + 1e7; s.lifetime = s.lifetime + 1e7
  elseif kind == "renown" then
    -- professions unlock with the Trade Gold a cat has earned in total
    local s = self:ProfState(); s.lifetime = math.max(s.lifetime, 2e12)
    self:Print("All professions unlocked.", true)
    self:CheckProfUnlocks()
  elseif kind == "chests" then for _, ch in ipairs(TCF.CHESTS) do db.keys[ch.key] = (db.keys[ch.key] or 0) + 5 end
  elseif kind == "levels" then
    local cd = self:CD()
    for _ = 1, 10 do if cd.level < TCF.MAX_LEVEL then cd.xp = 0; self:LevelUp() end end
    self:SettleXP()
  elseif kind == "hour" then
    for _ = 1, 360 do
      if self.AdvTick then self:AdvTick(10) end
      if self.ProfAdvance then self:ProfAdvance(10) end
    end
    -- the other cats' helpers get the hour too
    if self.TradeClasses then
      for _, cl in ipairs(self.TradeClasses(self)) do
        if cl ~= db.class then self:WithTradeClass(cl, self.ProfAdvance, 3600, true) end
      end
    end
    self:Print("Skipped one hour of Adventure and professions.", true)
  end
  self:MarkDirty(); self:RefreshAll()
end

---------------------------------------------------------------- slash commands
SLASH_TAPCATFOREVER1 = "/tapcat"
SLASH_TAPCATFOREVER2 = "/tcf"
SlashCmdList.TAPCATFOREVER = function(msg)
  local cmd, arg = (msg or ""):lower():match("^(%S*)%s*(.-)$")
  local ui = TCF.db.ui
  if cmd == "" or cmd == "open" or cmd == "config" then
    TCF:ToggleWindow()
  elseif cmd == "show" then ui.shown = true; TCF.hud:ApplySettings()
  elseif cmd == "hide" then ui.shown = false; TCF.hud:ApplySettings()
  elseif cmd == "toggle" then ui.shown = not ui.shown; TCF.hud:ApplySettings()
  elseif cmd == "lock" then ui.locked = true; TCF.hud:ApplySettings(); TCF:Print("Cat locked.", true)
  elseif cmd == "unlock" then ui.locked = false; TCF.hud:ApplySettings(); TCF:Print("Cat unlocked - drag to move.", true)
  elseif cmd == "reset" then TCF.hud:ResetPosition(); TCF:Print("Position reset.", true)
  elseif cmd == "scale" and tonumber(arg) then
    ui.scale = max(0.3, min(3, tonumber(arg))); TCF.hud:ApplySettings()
  elseif cmd == "bag" then TCF:ToggleBag()
  elseif cmd == "welcome" then TCF:ShowWelcome()
  elseif cmd == "testmode" then
    if not ui.testMode and not isDevCharacter() and keyHash(arg or "") ~= TEST_KEY then
      TCF:Print("/tapcat - open window | bag | welcome | show | hide | toggle | lock | unlock | reset | scale <0.3-3> | stats", true)
      return
    end
    ui.testMode = not ui.testMode
    if not ui.testMode and TCF.PartyTestClear then TCF:PartyTestClear() end
    TCF:Print(ui.testMode and "Test mode ON: shortcuts are in Settings." or "Test mode off.", true)
    if TCF.window and TCF.window:IsShown() then TCF.window:Refresh() end
  elseif cmd == "name" then
    -- (1.6.0) what the addon knows about your name, for checking the party row and casino games
    local n = UnitName and UnitName("player")
    local readable = type(n) == "string" and not TCF.IsSecret(n) and n ~= ""
    TCF:Print(string.format("The game %s addons read your name. Name learned from your own messages: %s. Saves are kept under: %s.",
      readable and "lets" or "doesn't let", TCF.SelfSender or "not yet (join a group with a friend)",
      readable and "your character" or "a shared save for this realm"), true)
  elseif cmd == "stats" then
    local n, total = TCF:CountOwned()
    TCF:Print(string.format("Level %d (%s), %s lifetime taps, %s TapCoins, %d/%d cosmetics.",
      TCF:CD().level, TCF:GetTitle(), TCF.Commas(TCF.db.taps), TCF.Commas(TCF.db.coins), n, total), true)
  else
    TCF:Print("/tapcat - open window | bag | welcome | show | hide | toggle | lock | unlock | reset | scale <0.3-3> | stats", true)
  end
end

-- Retail addon compartment
function TapCatForever_OnAddonCompartmentClick() TCF:ToggleWindow() end
