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

function TCF:Print(msg)
  if self.db and not self.db.ui.chat then return end
  DEFAULT_CHAT_FRAME:AddMessage("|cffffb84dTapCat|r|cffffffffForever|r: " .. msg)
end

function TCF:PlaySound(kind)
  if not self.db.ui.sound or not PlaySound then return end
  local map = {
    level = { "UI_EPICLOOT_TOAST", "LEVELUPSOUND", "IG_QUEST_LIST_COMPLETE" },
    loot  = { "LOOTWINDOWCOINSOUND", "IG_BACKPACK_COIN_SELECT" },
    rare  = { "UI_EPICLOOT_TOAST", "IG_QUEST_LIST_COMPLETE" },
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
  owned = {},       -- cosmetics
  gear = {},        -- real gear: itemID -> count
  class = nil,
  loadouts = {},
  look = { fur = "fur_ginger", pattern = nil },
  achievements = {},
  stats = { chests = 0, drops = 0, frenzies = 0, pets = 0, peakTPS = 0, classesPlayed = {} },
  daily = { last = "", streak = 0, best = 0 },
  shop = { day = "", rerolls = 0, stock = {}, bought = {} },
  keys = { pouch = 0, strong = 0, heroic = 0 },  -- free (unopened) chests
  ui = {
    point = { "BOTTOM", "BOTTOM", 0, 160 },
    scale = 1.0, alpha = 1.0, textScale = 1.0, shown = true,
    locked = false, clickThrough = false,
    showLevel = true, showXP = true, showTaps = true, showCoins = true, catOnly = false,
    mouse = true, popups = true, sound = true, chat = true, racial = true, cat3d = true, show3dWeapons = true,
    minimap = { angle = 215, hide = false },
  },
}

-- Saved data that belongs to the current character. Everything else (TapCoins,
-- quests, daily streak, achievements, settings) is shared by the whole account.
TCF.PER_CHARACTER = {
  owned = true, gear = true, loadouts = true, look = true, keys = true, classData = true,
  trade = true, expeditions = true, class = true, prof = true, dungeonRun = true,
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
  for k in pairs(TCF.PER_CHARACTER) do rawset(sv, k, nil) end
  setmetatable(sv, {
    __index = function(_, k) if TCF.PER_CHARACTER[k] then return char[k] end end,
    __newindex = function(t, k, v) if TCF.PER_CHARACTER[k] then char[k] = v else rawset(t, k, v) end end,
  })
  TCF.charKey, TCF.charData = key, char
  return char
end

function TCF:InitDB()
  TapCatForeverDB = TapCatForeverDB or {}
  local char = bindCharacter(TapCatForeverDB)
  local db = copyDefaults(DEFAULTS, TapCatForeverDB)
  self.db = db
  -- default class = the character's own class the very first time
  if not db.class then
    local _, cls = UnitClass("player")
    if isSecret(cls) then cls = nil end
    db.class = (cls and TCF.CLASS_BY_KEY[cls]) and cls or "WARRIOR"
    local cl = TCF.CLASS_BY_KEY[db.class]
    db.look.fur = cl.fur
  end
  for _, id in ipairs(TCF.STARTER) do db.owned[id] = db.owned[id] or 1 end
  -- every character owns a basic Orange Tabby skin
  db.owned.skin_orange = db.owned.skin_orange or 1
  -- cosmetic overrides per class (empty = the cat shows its real gear)
  for _, cl in ipairs(TCF.CLASSES) do db.loadouts[cl.key] = db.loadouts[cl.key] or {} end
  -- drop references to items that no longer exist
  for id in pairs(db.owned) do if not TCF.ITEMS[id] then db.owned[id] = nil end end
  for _, lo in pairs(db.loadouts) do
    for slot, id in pairs(lo) do if not TCF.ITEMS[id] then lo[slot] = nil end end
  end
  if db.look.fur and not TCF.ITEMS[db.look.fur] then db.look.fur = "fur_ginger" end
  if db.look.pattern and not TCF.ITEMS[db.look.pattern] then db.look.pattern = nil end
  -- v1 -> v2: levels became per-class; the old shared level goes to the current class
  if db.level then
    db.classData[db.class] = { level = db.level, xp = db.xp or 0 }
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
  end
  -- v2 -> v3: real gear. Every class starts with a simple weapon (also for new characters).
  if ((db.version or 0) < 3 or (char.fresh and not char.started)) and self.StarterGear then
    for _, cl in ipairs(TCF.CLASSES) do
      self:StarterGear(cl.key)
      db.loadouts[cl.key] = {}   -- show real gear instead of the old starter cosmetics
      -- Adventure now runs through real dungeons with new stage numbering
      local adv = db.classData[cl.key].adv
      adv.tier, adv.stage, adv.best, adv.cleared = 1, 1, 0, {}
    end
  end
  char.started = true
  db.version = 3
  db.stats.classesPlayed[db.class] = true
end

-- Per-class progress (level, xp, adventure)
function TCF:CD(class) return self.db.classData[class or self.db.class] end

---------------------------------------------------------------- appearance
function TCF:GetLoadout(class) return self.db.loadouts[class or self.db.class] end

-- Returns a flat table slot -> item for drawing, optionally with one item previewed.
-- The cat wears its real gear; a cosmetic chosen for a slot overrides it (transmog).
function TCF:GetAppearance(class, previewItem)
  local lo = self:GetLoadout(class)
  local out = self.GearAppearance and self:GearAppearance(class) or {}
  for slot, id in pairs(lo) do out[slot] = TCF.ITEMS[id] end
  out.fur = TCF.ITEMS[self.db.look.fur]
  out.pattern = self.db.look.pattern and TCF.ITEMS[self.db.look.pattern] or nil
  out.skin = self.db.look.skin and TCF.ITEMS[self.db.look.skin] or nil
  -- racial accessory can be hidden in Settings
  if not self.db.ui.racial and out.acc and out.acc.source == "race" then out.acc = nil end
  if previewItem then out[previewItem.slot] = previewItem end
  return out
end

function TCF:CanEquip(it, class)
  class = class or self.db.class
  return it and (not it.class or it.class == class)
end

function TCF:IsEquipped(it, class)
  if not it then return false end
  if TCF.SLOT_BY_KEY[it.slot].look then return self.db.look[it.slot] == it.id end
  return self:GetLoadout(class)[it.slot] == it.id
end

function TCF:Equip(it, class)
  if not it or not self.db.owned[it.id] or not self:CanEquip(it, class) then return end
  if TCF.SLOT_BY_KEY[it.slot].look then
    self.db.look[it.slot] = it.id
  else
    self:GetLoadout(class)[it.slot] = it.id
  end
  self:RefreshAll()
end

function TCF:Unequip(slot, class)
  if slot == "fur" then return end
  if TCF.SLOT_BY_KEY[slot].look then self.db.look[slot] = nil
  else self:GetLoadout(class)[slot] = nil end
  self:RefreshAll()
end

function TCF:SetClass(key)
  if not TCF.CLASS_BY_KEY[key] then return end
  self.db.class = key
  self.db.stats.classesPlayed[key] = true
  self:MarkDirty()
  self:RefreshAll()
end

---------------------------------------------------------------- progression
function TCF.XPForLevel(level) return floor(120 * level ^ 1.25) end

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

function TCF:LevelUp()
  local db = self.db
  local cd = self:CD()
  cd.level = cd.level + 1
  local reward = 10 + 2 * cd.level
  self:AddCoins(reward)
  local extra, chest = "", nil
  if cd.level % 20 == 0 then chest = "heroic" elseif cd.level % 5 == 0 then chest = "strong" end
  local cl = TCF.CLASS_BY_KEY[db.class]
  self:Print(string.format("Your %s cat reached |cffffd100level %d|r (%s)! +%d TapCoins%s.", cl.name, cd.level, self:GetTitle(), reward, extra))
  if self.cat then self.cat:Celebrate("LEVEL " .. cd.level .. "!", 1, 0.82, 0.1) end
  self:PlaySound("level")
  if chest then self:AwardChest(chest, "Level " .. cd.level) end
end

---------------------------------------------------------------- tapping
local TAP_CAP = 20          -- max counted taps per second (anti-macro)
local FRENZY_TPS = 7        -- taps/second to trigger frenzy face
local DROP_CHANCE = 1 / 3000
local COINS_PER_TAP = 0.02  -- 1 TapCoin per 50 taps (quests and Adventure are the main income)

local recent, recentHead = {}, 0     -- ring buffer of tap times
for i = 1, 32 do recent[i] = 0 end
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

  db.taps = db.taps + 1
  local cd = self:CD()
  cd.xp = cd.xp + (self.FoodBuff and self:FoodBuff("xp") or 1)
  db.coinFrac = db.coinFrac + COINS_PER_TAP
  if db.coinFrac >= 1 then
    local whole = floor(db.coinFrac)
    db.coinFrac = db.coinFrac - whole
    self:AddCoins(whole)
  end
  while cd.xp >= TCF.XPForLevel(cd.level) do
    cd.xp = cd.xp - TCF.XPForLevel(cd.level)
    self:LevelUp()
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

-- Pick an item of a rarity: favours the current class and unowned items.
function TCF:RollItem(rarity, preferUnowned)
  local class = self.db.class
  local wantClass = random() < 0.65
  local pools = { {}, {} } -- [1] unowned, [2] all
  for _, it in ipairs(TCF.ITEM_LIST) do
    if it.rarity == rarity and it.source == "loot" then
      local fits = wantClass and (it.class == class) or (not wantClass and it.class ~= class)
      if fits then
        pools[2][#pools[2] + 1] = it
        if not self.db.owned[it.id] then pools[1][#pools[1] + 1] = it end
      end
    end
  end
  if #pools[2] == 0 then -- fallback to anything of that rarity
    for _, it in ipairs(TCF.ITEM_LIST) do
      if it.rarity == rarity and it.source == "loot" then pools[2][#pools[2] + 1] = it end
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
  if self.ShowLootReveal and (reveal or (self.window and self.window:IsShown())) then
    self:ShowLootReveal(it, isNew, salvage, reason, chestKey)
  elseif self.cat then
    self.cat:ShowLoot(it, isNew)
  end
  self:PlaySound(it.rarity >= 4 and "rare" or "loot")
  self:MarkDirty()
  self:RefreshAll()
  return isNew, salvage
end

-- Puts an unopened chest in the Treasure Bag.
function TCF:AwardChest(key, source)
  local ch = TCF.CHEST_BY_KEY[key]
  self.db.keys[key] = (self.db.keys[key] or 0) + 1
  self:Print(string.format("%s: you earned a |cff1eff00%s|r! Open it from your Treasure Bag.", source or "Reward", ch.name))
  if self.cat and self.cat.Toast then self.cat:Toast("|T" .. TCF.Icon(ch.icon) .. ":18:18|t " .. ch.name .. "!", 0.2, 1, 0.2) end
  self:PlaySound("loot")
  self:MarkDirty()
  self:RefreshAll()
end

function TCF:ChestCount()
  local n = 0
  for _, ch in ipairs(TCF.CHESTS) do n = n + (self.db.keys[ch.key] or 0) end
  return n
end

-- Skins are bought from the Appearance tab
function TCF:BuySkin(id)
  local it = TCF.ITEMS[id]
  if not it or it.slot ~= "skin" or self.db.owned[id] or not it.skinPrice then return false end
  if not self:SpendCoins(it.skinPrice) then return false end
  self.db.owned[id] = 1
  self.db.look.skin = id
  self:Print("Your cat is now a " .. TCF.ItemLink(it) .. "!")
  if self.ShowLootReveal then self:ShowLootReveal(it, true, 0, "New skin") end
  self:PlaySound("buy")
  self:MarkDirty(); self:RefreshAll()
  return true
end

function TCF:GrantSkin(id, reason)
  local it = TCF.ITEMS[id]
  if not it or self.db.owned[id] then return false end
  self.db.owned[id] = 1
  self:Print((reason or "Rare drop") .. ": the " .. TCF.ItemLink(it) .. " skin!")
  if self.ShowLootReveal then self:ShowLootReveal(it, true, 0, reason or "Rare skin!") end
  self:PlaySound("rare")
  self:MarkDirty(); self:RefreshAll()
  return true
end

function TCF:OpenChest(key, useKey)
  local ch = TCF.CHEST_BY_KEY[key]
  if not ch then return end
  if useKey then
    if (self.db.keys[key] or 0) <= 0 then return end
    self.db.keys[key] = self.db.keys[key] - 1
  elseif not self:SpendCoins(ch.cost) then
    return
  end
  self.db.stats.chests = self.db.stats.chests + 1
  local rarity = self:RollRarity(ch.weights)
  if key == "heroic" and random() < 0.03 then
    local pool = {}
    for _, it in ipairs(TCF.ITEM_LIST) do
      if it.slot == "skin" and it.skinPrice and not self.db.owned[it.id] then pool[#pool + 1] = it end
    end
    if #pool > 0 then
      local it = pool[random(#pool)]
      self:GrantSkin(it.id, ch.name)
      self.lastChest = { item = it, isNew = true, salvage = 0 }
      return it, true
    end
  end
  -- 65%: real gear for your current class and level; 35%: a cosmetic
  if self.RollWorldLoot and random() < 0.65 then
    local level = self:CD().level
    local gear
    if rarity >= 5 then
      -- legendary roll: a raid boss item
      local raids = {}
      for i, t in ipairs(TCF.TIERS) do if t.raid then raids[#raids + 1] = i end end
      local ti = raids[random(#raids)]
      gear = self:RollBossLoot(ti, random(#TCF.TIERS[ti].bosses))
    else
      local q = max(2, min(4, rarity))
      -- half the time: real boss loot from a zone this class has cleared
      local adv = self:CD().adv
      local bestTier = floor(adv.best / 100)
      if bestTier >= 1 and random() < 0.5 then
        for _ = 1, 6 do
          local ti = random(max(1, bestTier - 3), bestTier)
          local t = TCF.TIERS[ti]
          local it = t and self:RollBossLoot(ti, random(#t.bosses))
          if it and it.q == q then gear = it; break end
        end
      end
      gear = gear or self:RollWorldLoot(level, nil, { q == 2 and 1 or 0, q == 3 and 1 or 0, q == 4 and 1 or 0 })
    end
    if gear then
      local isNew = self:GrantGear(gear, ch.name, true, key)
      self.lastChest = { gear = gear, isNew = isNew }
      return gear, isNew
    end
  end
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
  self.db.shop.bought[id] = true
  self:Print("Purchased " .. TCF.ItemLink(it) .. ".")
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
  self.db.ui.racial = true
  for _, cl in ipairs(TCF.CLASSES) do
    local lo = self:GetLoadout(cl.key)
    if not lo.acc then lo.acc = it.id end
  end
  self:Print(string.format("Your cat shows its %s pride: %s!", raceName or "racial", TCF.ItemLink(it)))
  if self.ShowLootReveal then self:ShowLootReveal(it, true, 0, (raceName or "Racial") .. " heritage") end
  self:PlaySound("buy")
  self:MarkDirty(); self:RefreshAll()
  return true
end

function TCF:CheckDaily()
  local d = self.db.daily
  local t = today()
  if d.last == t then return end
  local yesterday = date("%Y%m%d", time() - 86400)
  d.streak = (d.last == yesterday) and (d.streak + 1) or 1
  d.best = max(d.best, d.streak)
  d.last = t
  local bonus = 15 + 3 * min(d.streak, 10)
  self:AddCoins(bonus)
  self:Print(string.format("Daily treat: +%d TapCoins (streak: %d day%s).", bonus, d.streak, d.streak == 1 and "" or "s"))
end

---------------------------------------------------------------- stats & achievements
function TCF:CountOwned()
  local n, total, r = 0, 0, { 0, 0, 0, 0, 0 }
  for _, it in ipairs(TCF.ITEM_LIST) do
    if it.source ~= "retired" then
      total = total + 1
      if self.db.owned[it.id] then n = n + 1; r[it.rarity] = r[it.rarity] + 1 end
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
    local n = 0
    for _, it in ipairs(TCF.ITEM_LIST) do
      if it.slot == "skin" and db.owned[it.id] and (stat == "skins" or it.source == "skin" and not it.skinPrice and not it.skinAch and it.id ~= "skin_orange") then n = n + 1 end
    end
    return n
  elseif stat == "tradeGold" then
    return db.trade and db.trade.lifetime or 0
  elseif stat == "renown" then
    return db.trade and db.trade.renown or 0
  elseif stat == "races" then
    local n = 0
    for _, id in pairs(TCF.RACE_ITEM) do if db.owned[id] then n = n + 1 end end
    if db.owned.race_undead and TCF.RACE_ITEM.Undead then n = n - 1 end -- Scourge/Undead share one item
    if db.owned.race_skyborne then n = n + 1 end
    return n
  elseif stat == "epicGear" or stat == "legendGear" then
    local q, n = stat == "epicGear" and 4 or 5, 0
    for id in pairs(db.gear) do local it = TCF.GEAR[id]; if it and it.q == q then n = n + 1 end end
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
    local n, total, r = self:CountOwned()
    if stat == "owned" then return n end
    if stat == "ownedPct" then return floor(n / total * 100) end
    if stat == "rares" then return r[3] + r[4] + r[5] end
    if stat == "epics" then return r[4] end
    return r[5]
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
        extra = " and " .. TCF.ItemLink(TCF.ITEMS[a.item])
      end
      if a.skin and TCF.ITEMS[a.skin] and not db.owned[a.skin] then
        db.owned[a.skin] = 1
        extra = extra .. " and the " .. TCF.ItemLink(TCF.ITEMS[a.skin]) .. " cat"
        if self.ShowLootReveal then self:ShowLootReveal(TCF.ITEMS[a.skin], true, 0, a.name) end
      end
      self:Print(string.format("Achievement earned: |cffffd100%s|r! Reward: %d TapCoins%s.", a.name, a.coins, extra))
      if self.cat then self.cat:Celebrate(a.name, 1, 0.82, 0.1, "Achievement!") end
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
local acc = 0
ticker:SetScript("OnUpdate", function(_, elapsed)
  acc = acc + elapsed
  if acc < 0.25 then return end
  acc = 0
  local self = TCF
  if not self.db then return end
  if self.inFrenzy and GetTime() > (self.frenzyUntil or 0) then self.inFrenzy = false end
  if self.AdvTick then self:AdvTick(0.25) end
  if self.ProfessionsTick then self:ProfessionsTick(false, 0.25) end
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
  elseif cmd == "lock" then ui.locked = true; TCF.hud:ApplySettings(); TCF:Print("Cat locked.")
  elseif cmd == "unlock" then ui.locked = false; TCF.hud:ApplySettings(); TCF:Print("Cat unlocked - drag to move.")
  elseif cmd == "reset" then TCF.hud:ResetPosition(); TCF:Print("Position reset.")
  elseif cmd == "scale" and tonumber(arg) then
    ui.scale = max(0.3, min(3, tonumber(arg))); TCF.hud:ApplySettings()
  elseif cmd == "bag" then TCF:ToggleBag()
  elseif cmd == "stats" then
    local n, total = TCF:CountOwned()
    TCF:Print(string.format("Level %d (%s), %s lifetime taps, %s TapCoins, %d/%d cosmetics.",
      TCF:CD().level, TCF:GetTitle(), TCF.Commas(TCF.db.taps), TCF.Commas(TCF.db.coins), n, total))
  else
    TCF:Print("/tapcat - open window | bag | show | hide | toggle | lock | unlock | reset | scale <0.3-3> | stats")
  end
end

-- Retail addon compartment
function TapCatForever_OnAddonCompartmentClick() TCF:ToggleWindow() end
