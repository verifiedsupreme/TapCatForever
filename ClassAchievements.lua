-- TapCatForever: class achievements. Next to the account-wide achievements (Data.lua, Core.lua),
-- every class's cat has its own set: levels, Adventure zones, dungeons and raids cleared, every
-- ability learned, a full set of Rare or Epic gear worn, crafting skill and crafted gear worn,
-- expeditions and party expeditions.
--
-- Each class earns each one once per account (db.classAch[class][id] = time, shared by every
-- character), so an alt of the same class can't earn it again. Progress is read from the cats of
-- the character you are playing (levels, gear and Adventure are per character), except the
-- expedition counts, which are kept for the whole account (db.classProgress[class]).
--
-- Rewards: a few TapCoins (kept small on purpose) and a chest for that class's cat. The chest is
-- goes straight into that class cat's own Treasure Bag (TCF:AwardChest with its class); only a class
-- with no cat on this character keeps its chests waiting (db.classAchPending[class]). Reaching level 60 also
-- gives that class's Legendary main hand cosmetic (cosmetic only).
--
-- Existing saves: everything is checked at login, so cats get credit for what they already did.
-- The Achievements tab shows these with its "This class" filter (TCF:ClassAchBuild/ClassAchRefresh,
-- called from UI.lua).
local ADDON, TCF = ...
local floor, min, max = math.floor, math.min, math.max

-- the nine slots a "full set" is checked on: every armor slot you can see and the main hand
TCF.CLASS_SET_SLOTS = { "HEAD", "SHOULDER", "CHEST", "WRIST", "HANDS", "WAIST", "LEGS", "FEET", "MAINHAND" }
TCF.CLASS_CRAFTED_SET = 5   -- crafted pieces worn at once for "Homemade Outfit"

-- stat: what TCF:ClassStat reads; goal; coins; chest: TCF.CHESTS key; legend: the class's
-- Legendary main hand cosmetic
TCF.CLASS_ACHIEVEMENTS = {
  { id = "c_lvl10",    name = "Finding Its Feet",      stat = "level",      goal = 10, coins = 10, chest = "pouch",   icon = "Spell_Holy_SealOfMight" },
  { id = "c_lvl20",    name = "Seasoned Paws",         stat = "level",      goal = 20, coins = 15, chest = "pouch",   icon = "Spell_Holy_SealOfMight" },
  { id = "c_lvl30",    name = "Halfway There",         stat = "level",      goal = 30, coins = 20, chest = "strong",  icon = "Spell_Holy_SealOfWisdom" },
  { id = "c_lvl40",    name = "Veteran Whiskers",      stat = "level",      goal = 40, coins = 25, chest = "strong",  icon = "Spell_Holy_SealOfWisdom" },
  { id = "c_lvl50",    name = "Old Hand",              stat = "level",      goal = 50, coins = 30, chest = "strong",  icon = "Spell_Holy_SealOfSalvation" },
  { id = "c_lvl60",    name = "Top of the Class",      stat = "level",      goal = 60, coins = 50, chest = "heroic",  icon = "Spell_Holy_DivineIntervention", legend = true },
  { id = "c_world",    name = "Out and About",         stat = "world",      goal = "all", coins = 10, chest = "pouch",   icon = "INV_Misc_Map_01" },
  { id = "c_dung1",    name = "First Delve",           stat = "dungeons",   goal = 1,  coins = 10, chest = "pouch",   icon = "INV_Misc_Key_03" },
  { id = "c_dung5",    name = "Dungeon Delver",        stat = "dungeons",   goal = 5,  coins = 20, chest = "dungeon", icon = "INV_Misc_Key_03" },
  { id = "c_dung10",   name = "Deep Delver",           stat = "dungeons",   goal = 10, coins = 25, chest = "dungeon", icon = "INV_Misc_Key_10" },
  { id = "c_dungall",  name = "Every Dungeon Door",    stat = "dungeons",   goal = "all", coins = 40, chest = "dungeon", icon = "INV_Misc_Key_10" },
  { id = "c_raid1",    name = "Raid Debut",            stat = "raids",      goal = 1,  coins = 30, chest = "raid",    icon = "INV_Misc_Key_14" },
  { id = "c_raidall",  name = "Raid Conqueror",        stat = "raids",      goal = "all", coins = 60, chest = "raid", icon = "Spell_Shadow_AbominationExplosion" },
  { id = "c_abil",     name = "Fully Trained",         stat = "abilities",  goal = "all", coins = 25, chest = "strong", icon = "INV_Misc_Book_09" },
  { id = "c_blue",     name = "Dressed in Blue",       stat = "rareSet",    goal = 9,  coins = 20, chest = "strong",  icon = "INV_Chest_Chain" },
  { id = "c_epic",     name = "Purple Through and Through", stat = "epicSet", goal = 9, coins = 50, chest = "heroic", icon = "INV_Chest_Plate09" },
  { id = "c_craft150", name = "Handy Paws",            stat = "craftSkill", goal = 150, coins = 15, chest = "pouch",  icon = "Trade_BlackSmithing" },
  { id = "c_craft300", name = "Master of the Trade",   stat = "craftSkill", goal = 300, coins = 30, chest = "strong", icon = "Trade_BlackSmithing" },
  { id = "c_craftset", name = "Homemade Outfit",       stat = "craftedWorn", goal = 5, coins = 20, chest = "strong",  icon = "INV_Chest_Cloth_17" },
  { id = "c_exp10",    name = "Seasoned Traveller",    stat = "exp",        goal = 10, coins = 15, chest = "pouch",   icon = "INV_Misc_Map_01" },
  { id = "c_exp50",    name = "Globetrotter",          stat = "exp",        goal = 50, coins = 30, chest = "strong",  icon = "INV_Misc_Map02" },
  { id = "c_party1",   name = "Better Together",       stat = "party",      goal = 1,  coins = 15, chest = "pouch",   icon = "Achievement_GuildPerk_EverybodysFriend" },
  { id = "c_party10",  name = "Party Regular",         stat = "party",      goal = 10, coins = 30, chest = "strong",  icon = "INV_Misc_GroupNeedMore" },
}
TCF.CLASS_ACH_BY_ID = {}
for _, a in ipairs(TCF.CLASS_ACHIEVEMENTS) do TCF.CLASS_ACH_BY_ID[a.id] = a end

local DESC = {
  level = "Reach level %s.",
  dungeons = "Clear %s Adventure dungeons.",
  raids = "Clear %s Adventure raids.",
  abilities = "Learn every ability of this class.",
  rareSet = "Wear Rare or better gear on head, shoulders, chest, wrists, hands, waist, legs, feet and main hand.",
  epicSet = "Wear Epic gear on head, shoulders, chest, wrists, hands, waist, legs, feet and main hand.",
  craftSkill = "Reach %s skill in this cat's crafting profession.",
  craftedWorn = "Wear %s pieces of crafted gear at once.",
  exp = "Finish %s expeditions (solo or party) with this cat.",
  party = "Finish %s party expeditions with this cat.",
}
local DESC_ONE = { dungeons = "Clear an Adventure dungeon.", raids = "Clear an Adventure raid.",
  exp = "Finish an expedition (solo or party) with this cat.", party = "Finish a party expedition with this cat.",
  craftedWorn = "Wear a piece of crafted gear." }
local DESC_ALL = { dungeons = "Clear every Adventure dungeon.", raids = "Clear every Adventure raid." }

-- "Clear Elwynn Forest and Westfall in Adventure.": the open-world Adventure zones, by name
local worldDesc
local function worldText()
  if worldDesc then return worldDesc end
  local names = {}
  for _, t in ipairs(TCF.TIERS or {}) do
    if not t.raid and not (TCF.IsDungeonTier and TCF.IsDungeonTier(t)) then names[#names + 1] = t.name end
  end
  local list = #names <= 1 and (names[1] or "every zone")
    or table.concat(names, ", ", 1, #names - 1) .. " and " .. names[#names]
  worldDesc = "Clear " .. list .. " in Adventure."
  return worldDesc
end

-- tier counts, worked out once the tier data has loaded
local counts
local function tierCounts()
  if counts then return counts end
  counts = { world = 0, dungeons = 0, raids = 0 }
  for _, t in ipairs(TCF.TIERS or {}) do
    if t.raid then counts.raids = counts.raids + 1
    elseif TCF.IsDungeonTier and TCF.IsDungeonTier(t) then counts.dungeons = counts.dungeons + 1
    else counts.world = counts.world + 1 end
  end
  return counts
end

-- the goal as a number ("all" goals depend on the class or the tier data)
function TCF:ClassAchGoal(a, class)
  if a.goal ~= "all" then return a.goal end
  if a.stat == "abilities" then
    local list = TCF.ABILITIES and TCF.ABILITIES[class or self.db.class]
    return list and #list or 1
  end
  return max(1, tierCounts()[a.stat] or 1)
end

function TCF:ClassAchDesc(a, class)
  if a.stat == "world" then return worldText() end
  if a.goal == "all" then return DESC_ALL[a.stat] or DESC[a.stat] end
  if a.goal == 1 and DESC_ONE[a.stat] then return DESC_ONE[a.stat] end
  return string.format(DESC[a.stat] or "%s", BreakUpLargeNumbers and BreakUpLargeNumbers(a.goal) or tostring(a.goal))
end

-- the Legendary main hand cosmetic a class's level 60 achievement gives
function TCF:ClassAchItem(a, class)
  if not a.legend then return nil end
  local cl = TCF.CLASS_BY_KEY[class]
  if not cl then return nil end
  for _, g in ipairs(cl.gear) do
    if g[1] == "main" then
      local it = TCF.ITEMS[cl.key .. ":" .. g[2] .. ":5"]
      if it then return it end
    end
  end
end

---------------------------------------------------------------- saved data (account-wide)
local function store(self)
  local db = self.db
  if type(db.classAch) ~= "table" then db.classAch = {} end
  if type(db.classProgress) ~= "table" then db.classProgress = {} end
  if type(db.classAchPending) ~= "table" then db.classAchPending = {} end
  return db.classAch, db.classProgress, db.classAchPending
end

function TCF:ClassAchEarned(class, id)
  local earned = store(self)
  return earned[class] and earned[class][id]
end

-- account-wide per-class counters ("exp": expeditions finished, "party": party expeditions)
function TCF:ClassCount(class, key, add)
  if not TCF.CLASS_BY_KEY[class] then return 0 end
  local _, prog = store(self)
  prog[class] = prog[class] or {}
  if add then prog[class][key] = (prog[class][key] or 0) + add end
  return prog[class][key] or 0
end

---------------------------------------------------------------- progress
local function cleared(cd, ti, t)
  local best = cd and cd.adv and cd.adv.best or 0
  return best >= ti * 100 + #t.bosses * 2
end

-- zones, dungeons and raids cleared, in one pass over the tiers
local function clearedCounts(cd)
  local c = { world = 0, dungeons = 0, raids = 0 }
  for ti, t in ipairs(TCF.TIERS or {}) do
    if cleared(cd, ti, t) then
      local kind = t.raid and "raids" or ((TCF.IsDungeonTier and TCF.IsDungeonTier(t)) and "dungeons" or "world")
      c[kind] = c[kind] + 1
    end
  end
  return c
end

-- cache: a table filled during one check, so each stat is read once per class
function TCF:ClassStat(stat, class, cache)
  if cache and cache[stat] ~= nil then return cache[stat] end
  local v = self:ClassStatRaw(stat, class, cache)
  if cache then cache[stat] = v end
  return v
end

function TCF:ClassStatRaw(stat, class, cache)
  class = class or self.db.class
  local cd = self.db.classData[class]
  if not cd then return 0 end
  if stat == "level" then return cd.level or 1
  elseif stat == "world" or stat == "dungeons" or stat == "raids" then
    local c = clearedCounts(cd)
    if cache then for k, v in pairs(c) do cache[k] = v end end
    return c[stat]
  elseif stat == "abilities" then
    local n = 0
    for _, ab in ipairs(TCF.ABILITIES and TCF.ABILITIES[class] or {}) do
      if cd.abilities and cd.abilities[ab.key] == true then n = n + 1 end
    end
    return n
  elseif stat == "rareSet" or stat == "epicSet" then
    local q, n = stat == "rareSet" and 3 or 4, 0
    local eq = cd.gear or {}
    for _, slot in ipairs(TCF.CLASS_SET_SLOTS) do
      local it = eq[slot] and TCF.GEAR and TCF.GEAR[eq[slot]]
      -- a two-handed weapon fills the main hand like any other
      if it and (it.q or 0) >= q then n = n + 1 end
    end
    return n
  elseif stat == "craftSkill" then
    local s = type(cd.trade) == "table" and cd.trade.skill
    local key = self.CraftProf and self:CraftProf(class)
    return (type(s) == "table" and key and tonumber(s[key])) or 1
  elseif stat == "craftedWorn" then
    local n = 0
    for _, id in pairs(cd.gear or {}) do
      local it = TCF.GEAR and TCF.GEAR[id]
      if it and it.crafted then n = n + 1 end
    end
    return n
  elseif stat == "exp" or stat == "party" then
    return self:ClassCount(class, stat)
  end
  return 0
end

---------------------------------------------------------------- earning
-- every class cat has its own Treasure Bag, so a chest goes straight to its cat's bag
-- quiet: no chat line per chest (the login check prints one summary line)
local function deliver(self, class, quiet)
  local _, _, pending = store(self)
  local list = pending[class]
  if not list or #list == 0 or not (self.db.classData and self.db.classData[class]) then return end
  pending[class] = nil
  for _, id in ipairs(list) do
    local a = TCF.CLASS_ACH_BY_ID[id]
    if a and a.chest and TCF.CHEST_BY_KEY[a.chest] then
      if quiet then
        self:AddChests(a.chest, 1, class)
      else
        self:AwardChest(a.chest, TCF.CLASS_BY_KEY[class].name .. " achievement " .. a.name, nil, class)
      end
    end
  end
end
TCF.ClassAchDeliver = function(self, class) deliver(self, class or self.db.class) end

-- Checks every class's achievements. quiet: no chat line per achievement (the login check, which
-- prints one summary line instead). Returns how many were earned.
function TCF:CheckClassAchievements(quiet)
  if not self.db or not self.db.classData then return 0 end
  local earned, _, pending = store(self)
  local n = 0
  for _, cl in ipairs(TCF.CLASSES) do
    local class = cl.key
    earned[class] = earned[class] or {}
    local cache = {}
    for _, a in ipairs(TCF.CLASS_ACHIEVEMENTS) do
      if not earned[class][a.id] and self:ClassStat(a.stat, class, cache) >= self:ClassAchGoal(a, class) then
        earned[class][a.id] = time()
        n = n + 1
        if a.coins and a.coins > 0 then self:AddCoins(a.coins) end
        if a.chest then
          pending[class] = pending[class] or {}
          table.insert(pending[class], a.id)
        end
        local it = self:ClassAchItem(a, class)
        local extra = ""
        if it and not self.db.owned[it.id] then
          self.db.owned[it.id] = 1
          extra = " and " .. TCF.ItemLink(it) .. " (Cosmetic only)"
        end
        if not quiet then
          local wait = (a.chest and class ~= self.db.class) and string.format(" Its chest goes to your %s cat's Treasure Bag.", cl.name) or ""
          self:Print(string.format("%s achievement earned: |cffffd100%s|r. Reward: %d TapCoins%s.%s", cl.name, a.name, a.coins or 0, extra, wait))
        end
      end
    end
  end
  for _, cl in ipairs(TCF.CLASSES) do deliver(self, cl.key, quiet) end
  if n > 0 then
    if not quiet then self:PlaySound("ach") end
    self:MarkDirty()
  end
  return n
end

-- on every character: the level 60 cosmetic of a class that already earned it on another character
local function grantOwned(self)
  local earned = store(self)
  for _, cl in ipairs(TCF.CLASSES) do
    for id in pairs(earned[cl.key] or {}) do
      local a = TCF.CLASS_ACH_BY_ID[id]
      local it = a and self:ClassAchItem(a, cl.key)
      if it then self.db.owned[it.id] = self.db.owned[it.id] or 1 end
    end
  end
end

-- account achievements are checked whenever something changed; class achievements go with them
local baseCheck = TCF.CheckAchievements
function TCF:CheckAchievements(...)
  if baseCheck then baseCheck(self, ...) end
  self:CheckClassAchievements()
end

local ev = CreateFrame("Frame")
ev:RegisterEvent("PLAYER_LOGIN")
ev:SetScript("OnEvent", function()
  local self = TCF
  if not self.db then return end
  grantOwned(self)
  -- existing saves: credit for everything the cats already did, with one line instead of many
  local n = self:CheckClassAchievements(true)
  if n > 0 then
    self:Print(string.format("Your cats earned %d class achievement%s for what they have already done. See them in the Achievements tab (This class). Their chests are in each cat's Treasure Bag.",
      n, n == 1 and "" or "s"))
  end
end)

-- switching to a class hands over the chests it was waiting for
local lastClass
local acc = 0
ev:SetScript("OnUpdate", function(_, e)
  acc = acc + e
  if acc < 1 then return end
  acc = 0
  local self = TCF
  if not self.db or not self.db.class then return end
  if self.db.class ~= lastClass then
    lastClass = self.db.class
    deliver(self, lastClass)
  end
end)

---------------------------------------------------------------- the Achievements tab: "This class"
-- UI.lua calls ClassAchBuild once when it builds the page (with its rows) and ClassAchRefresh at the
-- start of every refresh: it returns true when the class view drew the rows.
function TCF:ClassAchBuild(win, page, rows, header, pageText, nRows)
  local U = TCF.UI
  win.achMode = win.achMode or "account"
  local function setMode(m)
    win.achMode = m
    win.acScroll = 0
    TCF:PlaySound("click")
    win:RefreshAchievements()
  end
  local bAcc = U.Button(page, "Account", 74, 20, function() setMode("account") end)
  local bCls = U.Button(page, "This class", 84, 20, function() setMode("class") end)
  bCls:SetPoint("TOPRIGHT", -16, -12)
  bAcc:SetPoint("RIGHT", bCls, "LEFT", -4, 0)
  U.Tip(bAcc, function(tt)
    tt:AddLine("Account achievements", 1, 0.82, 0)
    tt:AddLine("Shared by every character and every cat.", 1, 1, 1, true)
  end)
  U.Tip(bCls, function(tt)
    tt:AddLine("Class achievements", 1, 0.82, 0)
    tt:AddLine("Every class's cat has its own set. Each class earns each one once for your account, and its rewards go to that class's cat.", 1, 1, 1, true)
  end)
  -- the class picker, along the bottom of the page in the class view
  local picks = {}
  for i, cl in ipairs(TCF.CLASSES) do
    local b = CreateFrame("Button", nil, page)
    b:SetSize(22, 22)
    b:SetPoint("BOTTOMLEFT", 16 + (i - 1) * 26, 8)
    local t = b:CreateTexture(nil, "ARTWORK"); t:SetAllPoints(); TCF.SetClassIcon(t, cl.key)
    b.tex = t
    b.sel = b:CreateTexture(nil, "OVERLAY"); b.sel:SetPoint("TOPLEFT", -4, 4); b.sel:SetPoint("BOTTOMRIGHT", 4, -4)
    b.sel:SetTexture("Interface\\Buttons\\CheckButtonHilight"); b.sel:SetBlendMode("ADD")
    b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    b:SetScript("OnClick", function()
      win.achClass = cl.key; win.acScroll = 0
      TCF:PlaySound("click"); win:RefreshAchievements()
    end)
    U.Tip(b, function(tt)
      local done = 0
      for _, a in ipairs(TCF.CLASS_ACHIEVEMENTS) do if TCF:ClassAchEarned(cl.key, a.id) then done = done + 1 end end
      tt:AddLine(cl.name, cl.color[1], cl.color[2], cl.color[3])
      tt:AddLine(string.format("%d / %d class achievements", done, #TCF.CLASS_ACHIEVEMENTS), 1, 1, 1)
    end)
    b.class = cl.key
    picks[i] = b
  end
  win.achUI = { acc = bAcc, cls = bCls, picks = picks, rows = rows, header = header, pageText = pageText, nRows = nRows or #rows }
end

function TCF:ClassAchRefresh(win)
  local ui = win.achUI
  if not ui then return false end
  local classMode = win.achMode == "class"
  ui.acc:SetEnabled(classMode)
  ui.cls:SetEnabled(not classMode)
  for _, b in ipairs(ui.picks) do b:SetShown(classMode) end
  ui.pageText:ClearAllPoints()
  if not classMode then
    ui.pageText:SetPoint("BOTTOM", 0, 12)
    return false
  end
  ui.pageText:SetPoint("BOTTOMRIGHT", -16, 12)
  local class = win.achClass
  if not TCF.CLASS_BY_KEY[class or ""] then class = self.db.class end
  local cl = TCF.CLASS_BY_KEY[class]
  for _, b in ipairs(ui.picks) do b.sel:SetShown(b.class == class) end
  local list, done = TCF.CLASS_ACHIEVEMENTS, 0
  for _, a in ipairs(list) do if self:ClassAchEarned(class, a.id) then done = done + 1 end end
  local hex = string.format("%02x%02x%02x", cl.color[1] * 255, cl.color[2] * 255, cl.color[3] * 255)
  ui.header:SetText(string.format("|cff%s%s|r achievements  |cffffffff%d / %d|r", hex, cl.name, done, #list))
  local nRows = ui.nRows
  local maxScroll = max(0, #list - nRows)
  win.acScroll = min(win.acScroll or 0, maxScroll)
  local coinStr = TCF.UI.coinStr
  for i, r in ipairs(ui.rows) do
    local a = list[i + win.acScroll]
    if a then
      r:Show()
      local got = self:ClassAchEarned(class, a.id)
      local goal = self:ClassAchGoal(a, class)
      local cur = min(self:ClassStat(a.stat, class), goal)
      r.icon:SetTexture(TCF.Icon(a.icon)); r.icon:SetDesaturated(not got)
      r.name:SetText(got and ("|cffffd100" .. a.name .. "|r") or ("|cffaaaaaa" .. a.name .. "|r"))
      r.desc:SetText(self:ClassAchDesc(a, class))
      r.bar:SetMinMaxValues(0, goal); r.bar:SetValue(got and goal or cur)
      r.bar:SetStatusBarColor(got and 0.2 or 0.15, got and 0.8 or 0.45, got and 0.2 or 0.9)
      r.barText:SetText(got and "Complete" or (TCF.Commas(cur) .. " / " .. TCF.Commas(goal)))
      local ch = a.chest and TCF.CHEST_BY_KEY[a.chest]
      local rw = coinStr(a.coins or 0, 12)
      if ch then rw = rw .. " + " .. ch.name end
      local it = self:ClassAchItem(a, class)
      if it then rw = rw .. " + " .. TCF.ItemLink(it) .. " |cffaaaaaa(Cosmetic only)|r" end
      r.reward:SetText(rw)
      if r.SetBackdropBorderColor then
        if got then r:SetBackdropBorderColor(1, 0.82, 0.2, 1) else r:SetBackdropBorderColor(0.45, 0.40, 0.55, 1) end
      end
      r:SetScript("OnEnter", function(s)
        GameTooltip:SetOwner(s, "ANCHOR_RIGHT")
        GameTooltip:AddLine(a.name, 1, 0.82, 0)
        GameTooltip:AddLine(self:ClassAchDesc(a, class), 1, 1, 1, true)
        if ch then
          local waiting = false
          local _, _, pending = store(self)
          for _, id in ipairs(pending[class] or {}) do if id == a.id then waiting = true end end
          GameTooltip:AddLine(string.format("Reward: %d TapCoins and %s %s for your %s cat.", a.coins or 0,
            ch.name:find("^[AEIOU]") and "an" or "a", ch.name, cl.name), 0.8, 0.8, 0.8, true)
          if waiting then GameTooltip:AddLine("The chest waits until you play this cat on this character.", 1, 0.6, 0.2, true) end
        end
        if it then GameTooltip:AddLine(it.name .. ": Cosmetic only. It changes how your cat looks, not its Power.", 0.8, 0.8, 0.8, true) end
        if got then GameTooltip:AddLine("Earned for your account: no other " .. cl.name .. " cat can earn it again.", 0.6, 0.8, 1, true) end
        GameTooltip:Show()
      end)
    else
      r:Hide()
    end
  end
  ui.pageText:SetText(maxScroll > 0 and "Scroll for more" or "")
  return true
end
