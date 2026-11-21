-- TapCatForever: daily and weekly quests, the main way to earn TapCoins.
local ADDON, TCF = ...

local floor, random, max = math.floor, math.random, math.max

-- Counters that quests track. Each returns an ever-increasing number; a quest
-- stores the value when it was offered and counts progress from there.
local COUNTERS = {
  taps      = function(db) return db.taps end,
  kills     = function(db) local n = 0; for _, cd in pairs(db.classData) do n = n + cd.adv.kills end; return n end,
  bosses    = function(db) local n = 0; for _, cd in pairs(db.classData) do n = n + cd.adv.bossKills end; return n end,
  chests    = function(db) return db.stats.chests end,
  pets      = function(db) return db.stats.pets end,
  frenzies  = function(db) return db.stats.frenzies end,
  levels    = function(db) local n = 0; for _, cd in pairs(db.classData) do n = n + cd.level end; return n end,
  dungeons  = function(db) return db.stats.dungeons or 0 end,
  expeditions = function(db) return db.stats.expeditionsSent or 0 end,
  stages    = function(db) local n = 0; for _, cd in pairs(db.classData) do n = n + (cd.adv.newStages or 0) end; return n end,
}
-- These counters read classData, which belongs to the logged-in character, while
-- quests are shared by the whole account. Their progress is kept per character
-- (see charProgress) so switching characters neither breaks nor finishes a quest.
local PER_CHAR = { kills = true, bosses = true, levels = true, stages = true }

-- name, description (%s = goal), counter, goals, coin reward per goal step, icon
TCF.QUEST_TEMPLATES = {
  daily = {
    { "Paws of Fury",        "Press %s keys.",                          "taps",     { 600, 1200, 2000 },  { 25, 45, 70 },  "Ability_Druid_Dash" },
    { "Monster Hunter",      "Defeat %s enemies in Adventure.",         "kills",    { 20, 40, 70 },       { 25, 45, 70 },  "Ability_Hunter_Pet_Wolf" },
    { "Boss Bounty",         "Defeat %s Adventure bosses.",             "bosses",   { 6, 12 },            { 50, 90 },      "INV_Misc_Head_Dragon_01" },
    { "Treasure Seeker",     "Open %s chest(s).",                       "chests",   { 1, 2 },             { 30, 55 },      "INV_Box_02" },
    { "Good Kitty",          "Pet your cat %s times.",                  "pets",     { 10, 20 },           { 15, 25 },      "INV_ValentinesCandy" },
    { "Frenzied Paws",       "Enter a Paw Frenzy %s times.",            "frenzies", { 2, 5 },             { 25, 45 },      "Ability_Druid_Berserk" },
    { "Growing Up",          "Gain %s level(s) on any class.",          "levels",   { 1, 2 },             { 35, 60 },      "Spell_Holy_SealOfMight" },
    { "Dungeon Run",         "Finish %s real dungeon(s) in WoW.",       "dungeons", { 1 },                { 60 },          "INV_Misc_Key_03" },
    { "Send Them Off",       "Send %s expedition(s).",                  "expeditions", { 1, 2 },          { 30, 55 },      "INV_Misc_Map_01" },
    { "Into the Unknown",    "Clear %s new Adventure stage(s).",        "stages",   { 3, 6 },             { 30, 55 },      "INV_Misc_Map_01" },
  },
  weekly = {
    { "Tireless Tapper",     "Press %s keys this week.",                "taps",     { 12000 },            { 350 },         "Ability_Druid_Ravage" },
    { "Dungeon Delver",      "Defeat %s Adventure bosses this week.",   "bosses",   { 100 },              { 400 },         "INV_Misc_Bone_HumanSkull_01" },
    { "Seasoned Adventurer", "Defeat %s enemies this week.",            "kills",    { 300 },              { 350 },         "Ability_Warrior_BattleShout" },
  },
}
TCF.QUEST_COUNTERS = COUNTERS

local function weekKey()
  -- weeks start on Tuesday, like WoW's weekly reset (US)
  local t = time()
  local wday = tonumber(date("%w", t)) -- 0 = Sunday
  local sinceTue = (wday - 2) % 7
  return date("%Y%m%d", t - sinceTue * 86400)
end

local function makeQuest(tpl, db, tier)
  tier = math.min(tier, #tpl[4])
  local counter = tpl[3]
  return {
    name = tpl[1], desc = string.format(tpl[2], TCF.Commas(tpl[4][tier])), counter = counter,
    goal = tpl[4][tier], reward = tpl[5][tier], icon = tpl[6],
    base = COUNTERS[counter](db), claimed = false,
    char = PER_CHAR[counter] and TCF.charKey or nil,  -- whose counter "base" was read from
  }
end

-- Progress on a per-character counter, summed over every character that worked on
-- the quest. Each character keeps its own starting value (the character that rolled
-- the quest uses quest.base); "bank" keeps what a character earned before a reset.
local function charProgress(quest, v)
  local key = TCF.charKey or "?"
  local e
  if quest.char == key then e = quest
  else
    quest.others = quest.others or {}
    e = quest.others[key]
    if not e then e = { base = v }; quest.others[key] = e end
  end
  if v < (e.last or e.base) then
    -- this character was reset: keep what it already earned, count on from here
    e.bank = (e.bank or 0) + max(0, (e.last or e.base) - e.base)
    e.base = v
  end
  e.last = v
  local function earned(o) return (o.bank or 0) + max(0, (o.last or o.base) - o.base) end
  local n = earned(e)
  if e ~= quest and quest.char then n = n + earned(quest) end
  for _, o in pairs(quest.others or {}) do if o ~= e then n = n + earned(o) end end
  return n
end

-- Record this character's current value on every open per-character quest.
local function saveCharProgress(db)
  local q = db.quests
  if not q then return end
  for _, list in ipairs({ q.daily or {}, q.weekly or {} }) do
    for _, quest in ipairs(list) do
      if not quest.claimed and quest.char and PER_CHAR[quest.counter] then charProgress(quest, COUNTERS[quest.counter](db)) end
    end
  end
end

-- Quests rolled before per-character tracking don't know which character their
-- base came from. Keep progress that looks like it belongs to this character and
-- start the rest over, so a quest rolled on another character can't finish at once.
local function migrateQuest(quest, db)
  if quest.char or quest.claimed or not PER_CHAR[quest.counter] then return end
  local v = COUNTERS[quest.counter](db)
  local d = v - quest.base
  if d < 0 or d > quest.goal * 3 then quest.base = v end
  quest.char = TCF.charKey
end

function TCF:EnsureQuests()
  local db = self.db
  db.quests = db.quests or { day = "", week = "", daily = {}, weekly = {} }
  local q = db.quests
  local today = date("%Y%m%d")
  if q.day ~= today then
    q.day = today
    q.daily = {}
    local pool = {}
    for i = 1, #TCF.QUEST_TEMPLATES.daily do pool[i] = i end
    for n = 1, 3 do
      local pick = table.remove(pool, random(#pool))
      local tpl = TCF.QUEST_TEMPLATES.daily[pick]
      q.daily[n] = makeQuest(tpl, db, random(#tpl[4]))
      q.daily[n].key = "pouch"     -- every daily quest also gives a small chest
      q.daily[n].kind = "daily"
    end
  end
  local wk = weekKey()
  if q.week ~= wk then
    q.week = wk
    local tpl = TCF.QUEST_TEMPLATES.weekly[random(#TCF.QUEST_TEMPLATES.weekly)]
    q.weekly = { makeQuest(tpl, db, 1) }
    q.weekly[1].key = "strong"   -- weekly quests also give a free Strongbox key
    q.weekly[1].kind = "weekly"
  end
  if (q.v or 1) < 2 then
    for _, list in ipairs({ q.daily, q.weekly }) do
      for _, quest in ipairs(list) do migrateQuest(quest, db) end
    end
    q.v = 2
  end
  -- note this character's starting values now (EnsureQuests runs at login), so
  -- kills made before the quest list is next looked at still count
  saveCharProgress(db)
end

-- Save this character's progress so alts see it even if the Quests page was never
-- opened this session: on logout (which also fires on /reload, before saved data
-- is written) and every few seconds as a backstop for crashes and disconnects.
local saver = CreateFrame("Frame")
pcall(saver.RegisterEvent, saver, "PLAYER_LOGOUT") -- pcall: the test mock doesn't list this event
saver:SetScript("OnEvent", function()
  if TCF.db and TCF.charKey then saveCharProgress(TCF.db) end
end)
local saveAcc = 0
saver:SetScript("OnUpdate", function(_, elapsed)
  saveAcc = saveAcc + elapsed
  if saveAcc < 10 then return end
  saveAcc = 0
  if TCF.db and TCF.charKey then saveCharProgress(TCF.db) end
end)

function TCF:QuestProgress(quest)
  local v = COUNTERS[quest.counter](self.db)
  local n = (PER_CHAR[quest.counter] and quest.char) and charProgress(quest, v) or (v - quest.base)
  return math.min(quest.goal, max(0, n))
end

function TCF:ClaimQuest(quest)
  if quest.claimed or self:QuestProgress(quest) < quest.goal then return end
  quest.claimed = true
  self:AddCoins(quest.reward)
  local extra = ""
  if quest.key then extra = " and a " .. TCF.CHEST_BY_KEY[quest.key].name end
  self.db.stats.questsDone = (self.db.stats.questsDone or 0) + 1
  self:Print(string.format("Quest complete: |cffffd100%s|r! +%d TapCoins%s.", quest.name, quest.reward, extra), true)
  if self.cat then self.cat:Celebrate(quest.name, 1, 0.82, 0.1, "Quest complete!") end
  self:PlaySound("ach")
  if quest.key then self:AwardChest(quest.key, quest.name) end
  -- a few skins are rare quest rewards (quests rolled before this have no kind saved)
  local kind = quest.kind
  if not kind then
    kind = "daily"
    for _, w in ipairs(self.db.quests and self.db.quests.weekly or {}) do if w == quest then kind = "weekly" end end
  end
  if self.RollSkinSource then
    self:RollSkinSource("quest", function(g) return g.quest == kind end,
      (kind == "weekly" and "Weekly" or "Daily") .. " quest reward (" .. quest.name .. ")", true)
  end
  self:MarkDirty()
  self:RefreshAll()
end

-- quests that are finished but not yet claimed
function TCF:QuestsReady()
  self:EnsureQuests()
  local n = 0
  for _, list in ipairs({ self.db.quests.daily, self.db.quests.weekly }) do
    for _, q in ipairs(list) do if not q.claimed and self:QuestProgress(q) >= q.goal then n = n + 1 end end
  end
  return n
end
