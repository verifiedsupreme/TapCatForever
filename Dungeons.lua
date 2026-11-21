-- TapCatForever: rewards for real dungeon and raid runs in WoW.
--
-- A run starts when you enter a dungeon/raid instance. Every boss kill
-- (ENCOUNTER_END with success) pays a few TapCoins. The run counts as finished
-- when the group finder reports completion (LFG_COMPLETION_REWARD), or when
-- you leave after killing enough bosses: then you get a free chest.
local ADDON, TCF = ...

local MIN_BOSSES = { party = 2, raid = 3 }
local MIN_SECONDS = 300           -- at least 5 minutes inside
local BOSS_COINS = { party = 5, raid = 10 }

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
  return { id = instanceID, name = name, type = itype }
end

function TCF.DungeonChestFor(kind, level)
  if TCF.IsSecret(level) then level = 60 end
  if kind == "raid" then return "heroic" end
  if level < 20 then return "pouch" end
  if math.random() < (level >= 50 and 0.25 or 0.10) then return "heroic" end
  return "strong"
end
TCF.DUNGEON_CHEST_TEXT = "Finish a real dungeon in WoW: below level 20 you get a Cat Treat Pouch; from level 20 an Adventurer's Strongbox (10% chance of a Heroic Cache, 25% from level 50). Raids always give a Heroic Cache."

function TCF:DungeonComplete(run, how)
  if run.rewarded then return end
  run.rewarded = true
  local db = self.db
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
  if run and (not here or here.id ~= run.id) then
    -- left the instance: finished if enough bosses died
    if not run.rewarded and run.bosses >= MIN_BOSSES[run.type] and time() - run.start >= MIN_SECONDS then
      self:DungeonComplete(run, "left")
    end
    db.dungeonRun = nil
    run = nil
  end
  if here and not run then
    db.dungeonRun = { id = here.id, name = here.name, type = here.type, bosses = 0, start = time(), rewarded = false }
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
    if run and safeEq(success, 1) then
      run.bosses = run.bosses + 1
      TCF:AddCoins(BOSS_COINS[run.type])
      TCF:Print(string.format("Boss defeated! +%d TapCoins (%d boss%s this run).", BOSS_COINS[run.type], run.bosses, run.bosses == 1 and "" or "es"))
    end
  elseif event == "LFG_COMPLETION_REWARD" then
    local run = TCF.db.dungeonRun
    if run then TCF:DungeonComplete(run, "lfg") end
  else
    TCF:DungeonCheck()
  end
end)
