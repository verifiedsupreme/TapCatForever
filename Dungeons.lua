-- TapCatForever: rewards for real dungeon and raid runs in WoW.
--
-- A run starts when you enter a dungeon/raid instance. Every boss kill
-- (ENCOUNTER_END with success) pays a few TapCoins. The run counts as finished
-- when the group finder reports completion (LFG_COMPLETION_REWARD), or when
-- you leave after killing enough bosses: then you get a free chest.
-- Each dungeon pays its chest once a day and each raid once a week (per
-- character), and at most DUNGEON_CHESTS_PER_DAY dungeon chests a day, so
-- walking out and back in or resetting old dungeons can't farm chests.
local ADDON, TCF = ...

local MIN_BOSSES = { party = 2, raid = 3 }
local MIN_SECONDS = 300           -- at least 5 minutes inside
local BOSS_COINS = { party = 5, raid = 10 }
local RESUME_SECONDS = 30 * 60    -- coming back within this keeps the run (bosses and time) going
local DUNGEON_REPEAT = 18 * 3600  -- the same dungeon pays its chest again after this
local WEEK = 7 * 86400
local DUNGEON_CHESTS_PER_DAY = 2  -- account-wide; raids are limited by their weekly lockout instead

local function safeEq(a, b)
  if TCF.IsSecret(a) then return false end
  local ok, eq = pcall(function() return a == b end)
  return ok and eq
end

local function currentInstance()
  if not IsInInstance then return nil end
  local inInstance, itype = IsInInstance()
  if not inInstance or (itype ~= "party" and itype ~= "raid") then return nil end
  local name, _, _, _, _, _, _, instanceID = GetInstanceInfo()
  if TCF.IsSecret(name) then name = itype == "raid" and "a raid" or "a dungeon" end
  -- the id is used as a table key below, so it must never be a secret value
  if TCF.IsSecret(instanceID) or type(instanceID) ~= "number" then instanceID = -1 end
  return { id = instanceID, name = name, type = itype }
end

function TCF.DungeonChestFor(kind, level)
  if TCF.IsSecret(level) then level = 60 end
  if kind == "raid" then return "heroic" end
  if level < 20 then return "pouch" end
  if math.random() < (level >= 50 and 0.25 or 0.10) then return "heroic" end
  return "strong"
end
TCF.DUNGEON_CHEST_TEXT = "Finish a real dungeon in WoW: below level 20 you get a Cat Treat Pouch; from level 20 an Adventurer's Strongbox (10% chance of a Heroic Cache, 25% from level 50). Raids always give a Heroic Cache. Each dungeon gives a chest once a day and each raid once a week, and up to " .. DUNGEON_CHESTS_PER_DAY .. " dungeon chests a day across all your characters."

-- When the current weekly reset started (raids pay once per reset).
local function lastWeeklyReset(now)
  if C_DateAndTime and C_DateAndTime.GetSecondsUntilWeeklyReset then
    local ok, left = pcall(C_DateAndTime.GetSecondsUntilWeeklyReset)
    if ok and type(left) == "number" and not TCF.IsSecret(left) then return now + left - WEEK end
  end
  return now - WEEK
end

-- Per-character record of which instances already paid a chest. Lockouts are per
-- character, so this lives in the character's own saved table (Core.lua bindCharacter).
local function paidLog(db)
  local holder = TCF.charData or db
  holder.dungeonPaid = holder.dungeonPaid or {}
  local log = holder.dungeonPaid
  local now = time()
  for k, t in pairs(log) do if now - t > WEEK + 86400 then log[k] = nil end end
  return log
end

-- Why this run can't pay a chest right now, or nil if it can.
local function chestBlocked(db, run)
  local now = time()
  if run.id ~= -1 then
    local paidAt = paidLog(db)[run.type .. ":" .. run.id]
    if paidAt then
      if run.type == "raid" and paidAt >= lastWeeklyReset(now) then return "You already got this week's chest from " .. (run.name or "this raid") .. "." end
      if run.type ~= "raid" and now - paidAt < DUNGEON_REPEAT then return "You already got today's chest from " .. (run.name or "this dungeon") .. "." end
    end
  end
  if run.type == "party" then
    local day = db.dungeonDay
    if day and day.day == date("%Y%m%d") and day.n >= DUNGEON_CHESTS_PER_DAY then
      return "Your characters already got " .. DUNGEON_CHESTS_PER_DAY .. " dungeon chests today. Come back tomorrow for more."
    end
  end
end

function TCF:DungeonComplete(run, how)
  if run.rewarded then return end
  run.rewarded = true
  local db = self.db
  local blocked = chestBlocked(db, run)
  if blocked then
    -- boss TapCoins were already paid; repeats don't count as new runs
    self:Print(blocked .. " Bosses still give TapCoins.", true)
    if self.cat and self.cat.Toast then self.cat:Toast("No chest this time", 1, 0.6, 0.2) end
    return
  end
  if run.id ~= -1 then paidLog(db)[run.type .. ":" .. run.id] = time() end
  if run.type == "party" then
    local today = date("%Y%m%d")
    if not db.dungeonDay or db.dungeonDay.day ~= today then db.dungeonDay = { day = today, n = 0 } end
    db.dungeonDay.n = db.dungeonDay.n + 1
  end
  -- chest by character level: Pouch below 20, Strongbox from 20 (chance of a
  -- Heroic Cache from 50), raids always give a Heroic Cache
  local chestKey = TCF.DungeonChestFor(run.type, UnitLevel and UnitLevel("player") or 60)
  local stat = run.type == "raid" and "raids" or "dungeons"
  db.stats[stat] = (db.stats[stat] or 0) + 1
  if self.cat then self.cat:Celebrate((run.name or "Dungeon"), 0.2, 1, 0.2, (run.type == "raid" and "Raid" or "Dungeon") .. " complete!") end
  self:AwardChest(chestKey, (run.name or "Dungeon") .. " complete")
end

function TCF:DungeonCheck()
  local db = self.db
  local here = currentInstance()
  local run = db.dungeonRun
  local now = time()
  if run and not run.leftAt and (not here or here.id ~= run.id) then
    -- left the instance: finished if enough bosses died
    if not run.rewarded and run.bosses >= MIN_BOSSES[run.type] and now - run.start >= MIN_SECONDS then
      self:DungeonComplete(run, "left")
    end
    if run.rewarded then
      db.dungeonRun = nil
      run = nil
    else
      -- not finished yet (stepped out, or released after a wipe): keep it so coming
      -- back in carries on with the bosses already killed instead of starting over
      run.leftAt = now
    end
  end
  if run and run.leftAt then
    if here and here.id == run.id and now - run.leftAt <= RESUME_SECONDS then
      run.leftAt = nil
    elseif here or now - run.leftAt > RESUME_SECONDS then
      db.dungeonRun = nil
      run = nil
    end
  end
  if here and not run then
    db.dungeonRun = { id = here.id, name = here.name, type = here.type, bosses = 0, start = now, rewarded = false }
  end
end

local ev = CreateFrame("Frame")
for _, e in ipairs({ "PLAYER_ENTERING_WORLD", "ZONE_CHANGED_NEW_AREA", "ENCOUNTER_END", "LFG_COMPLETION_REWARD" }) do
  pcall(ev.RegisterEvent, ev, e)
end
ev:SetScript("OnEvent", function(_, event, ...)
  if not TCF.db then return end
  if event == "ENCOUNTER_END" then
    local _, _, _, _, success = ...
    local run = TCF.db.dungeonRun
    if run and not run.leftAt and safeEq(success, 1) then
      run.bosses = run.bosses + 1
      TCF:AddCoins(BOSS_COINS[run.type])
      TCF:Print(string.format("Boss defeated! +%d TapCoins (%d boss%s this run).", BOSS_COINS[run.type], run.bosses, run.bosses == 1 and "" or "es"))
    end
  elseif event == "LFG_COMPLETION_REWARD" then
    local run = TCF.db.dungeonRun
    if run and not run.leftAt then TCF:DungeonComplete(run, "lfg") end
  else
    TCF:DungeonCheck()
  end
end)
