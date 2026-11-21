-- TapCatForever: daily and weekly quests, the main way to earn TapCoins.
local ADDON, TCF = ...

local floor, random = math.floor, math.random

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

-- name, description (%s = goal), counter, goals, coin reward per goal step, icon
TCF.QUEST_TEMPLATES = {
  daily = {
    { "Paws of Fury",        "Press %s keys.",                          "taps",     { 600, 1200, 2000 },  { 25, 45, 70 },  "Ability_Druid_Dash" },
    { "Monster Hunter",      "Defeat %s enemies in Adventure.",         "kills",    { 20, 40, 70 },       { 25, 45, 70 },  "Ability_Hunter_Pet_Wolf" },
    { "Boss Bounty",         "Defeat %s Adventure boss(es).",           "bosses",   { 1, 2 },             { 50, 90 },      "INV_Misc_Head_Dragon_01" },
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
    { "Dungeon Delver",      "Defeat %s Adventure bosses this week.",   "bosses",   { 6 },                { 400 },         "INV_Misc_Bone_HumanSkull_01" },
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
  }
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
    end
  end
  local wk = weekKey()
  if q.week ~= wk then
    q.week = wk
    local tpl = TCF.QUEST_TEMPLATES.weekly[random(#TCF.QUEST_TEMPLATES.weekly)]
    q.weekly = { makeQuest(tpl, db, 1) }
    q.weekly[1].key = "strong"   -- weekly quests also give a free Strongbox key
  end
end

function TCF:QuestProgress(quest)
  local fn = COUNTERS[quest.counter]
  return math.min(quest.goal, fn(self.db) - quest.base)
end

function TCF:ClaimQuest(quest)
  if quest.claimed or self:QuestProgress(quest) < quest.goal then return end
  quest.claimed = true
  self:AddCoins(quest.reward)
  local extra = ""
  if quest.key then extra = " and a " .. TCF.CHEST_BY_KEY[quest.key].name end
  self.db.stats.questsDone = (self.db.stats.questsDone or 0) + 1
  self:Print(string.format("Quest complete: |cffffd100%s|r! +%d TapCoins%s.", quest.name, quest.reward, extra))
  if self.cat then self.cat:Celebrate(quest.name, 1, 0.82, 0.1, "Quest complete!") end
  self:PlaySound("ach")
  if quest.key then self:AwardChest(quest.key, quest.name) end
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
