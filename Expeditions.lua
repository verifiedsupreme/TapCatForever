-- TapCatForever: Expeditions. Send a party of 3 of your class cats away for
-- real time (it keeps going while you're offline); they come back with
-- TapCoins, XP and sometimes chests. Stronger parties succeed more often.
-- Short trips are mostly for XP and TapCoins; chests come from the long ones.
local ADDON, TCF = ...

local floor, min, max, random = math.floor, math.min, math.max, math.random

-- rec: recommended total party power; tier: which Adventure tier's loot they find
-- chest: { chest key, chance on success }; rolls: bonus chest rolls (see ExpeditionBonusChance).
-- The trips under 2 hours can be re-sent all day, so they give no bonus rolls and only a
-- small chest chance (about 0.3 Pouches per slot-hour), well below the long trips.
TCF.EXPEDITIONS = {
  { key = "elwynn", name = "Scout Elwynn Forest",       dur = 15 * 60,    rec = 700,   coins = 12,  tier = 1,  rolls = 0, chest = { "pouch", 0.08 },  icon = "INV_Misc_Map_01" },
  { key = "westfall", name = "Westfall Bounty Hunt",    dur = 30 * 60,    rec = 1000,  coins = 25,  tier = 2,  rolls = 0, chest = { "pouch", 0.15 },  icon = "INV_Misc_Bandana_03" },
  { key = "dm", name = "Raid the Deadmines",             dur = 60 * 60,    rec = 1600,  coins = 45,  tier = 5,  rolls = 0, chest = { "pouch", 0.3 },   icon = "INV_Misc_Bandana_03" },
  { key = "sm", name = "Storm Scarlet Monastery",        dur = 2 * 3600,   rec = 3400,  coins = 90,  tier = 11, rolls = 2, chest = { "strong", 0.25 }, icon = "INV_Shield_03" },
  { key = "brd", name = "Delve Blackrock Depths",        dur = 4 * 3600,   rec = 5800,  coins = 160, tier = 17, rolls = 2, chest = { "strong", 0.5 },  icon = "INV_Hammer_09" },
  { key = "strat", name = "Purge Stratholme",            dur = 6 * 3600,   rec = 6600,  coins = 230, tier = 21, rolls = 2, chest = { "strong", 0.7 },  icon = "Spell_Shadow_RaiseDead" },
  { key = "mc", name = "Assault Molten Core",            dur = 8 * 3600,   rec = 7600,  coins = 320, tier = 23, rolls = 3, chest = { "heroic", 0.25 }, icon = "Spell_Fire_Elemental_Totem" },
  { key = "bwl", name = "Siege Blackwing Lair",          dur = 12 * 3600,  rec = 9400,  coins = 480, tier = 26, rolls = 3, chest = { "heroic", 0.4 },  icon = "INV_Misc_Head_Dragon_Black" },
  { key = "naxx", name = "Storm Naxxramas",              dur = 24 * 3600,  rec = 12500, coins = 900, tier = 28, rolls = 3, chest = { "heroic", 0.6 },  icon = "Spell_Shadow_AbominationExplosion" },
}
TCF.EXPEDITION_BY_KEY = {}
for _, e in ipairs(TCF.EXPEDITIONS) do TCF.EXPEDITION_BY_KEY[e.key] = e end
TCF.MAX_EXPEDITIONS = 2

-- Chance for each bonus chest roll. It grows with time away (full 50% from 4 hours),
-- so chests per hour don't reward re-sending short trips over and over.
function TCF.ExpeditionBonusChance(e)
  return 0.5 * min(1, e.dur / (4 * 3600))
end

local function state(self)
  self.db.expeditions = self.db.expeditions or { active = {} }
  return self.db.expeditions
end

function TCF:IsOnExpedition(class)
  for _, ex in ipairs(state(self).active) do
    for _, m in ipairs(ex.members) do if m == class then return ex end end
  end
end

function TCF:PartyPower(members)
  local p = 0
  for _, c in ipairs(members) do p = p + self:CombatStats(c).power end
  return p
end

function TCF:ExpeditionChance(power, rec)
  local r = power / rec
  return max(0.05, min(0.97, 0.2 + 0.77 * r * r))
end

function TCF:StartExpedition(key, members)
  local e = TCF.EXPEDITION_BY_KEY[key]
  local st = state(self)
  if not e or #members ~= 3 then return false, "Choose 3 cats." end
  if #st.active >= TCF.MAX_EXPEDITIONS then return false, "You can only run " .. TCF.MAX_EXPEDITIONS .. " expeditions at once." end
  local seen = {}
  for _, c in ipairs(members) do
    if seen[c] then return false, "Each cat can only go once." end
    if self:IsOnExpedition(c) then return false, TCF.CLASS_BY_KEY[c].name .. " is already away." end
    seen[c] = true
  end
  local power = self:PartyPower(members)
  local now = time()
  table.insert(st.active, { key = key, members = { members[1], members[2], members[3] }, start = now,
    finish = now + e.dur, power = power, chance = self:ExpeditionChance(power, e.rec) })
  self.db.stats.expeditionsSent = (self.db.stats.expeditionsSent or 0) + 1
  self:Print(string.format("Your party set out: |cffffd100%s|r (back in %s).", e.name, TCF.FormatDuration(e.dur)), true)
  self:MarkDirty(); self:RefreshAll()
  return true
end

function TCF.FormatDuration(s)
  s = max(0, floor(s))
  if s >= 3600 then return string.format("%dh %02dm", floor(s / 3600), floor(s % 3600 / 60)) end
  if s >= 60 then return string.format("%dm %02ds", floor(s / 60), s % 60) end
  return s .. "s"
end

-- Collect a finished expedition: roll success and hand out rewards.
function TCF:ClaimExpedition(index)
  local st = state(self)
  local ex = st.active[index]
  if not ex or time() < ex.finish then return end
  table.remove(st.active, index)
  local e = TCF.EXPEDITION_BY_KEY[ex.key]
  st.done = (st.done or 0) + 1
  self.db.stats.expeditions = (self.db.stats.expeditions or 0) + 1
  -- every cat that went earns a little XP (5 per minute away; half if it failed)
  local won = random() <= ex.chance
  local xp = floor(e.dur / 60 * 5 * (won and 1 or 0.5))
  for _, c in ipairs(ex.members) do self:AddClassXP(c, xp) end
  if not won then
    local coins = floor(e.coins * 0.1)
    self:AddCoins(coins)
    self:Print(string.format("|cffff6060%s failed.|r Your cats limped home with %d TapCoins and %d XP each. Stronger gear raises the odds.", e.name, coins, xp), true)
    self:MarkDirty(); self:RefreshAll()
    return false
  end
  self.db.stats.expeditionWins = (self.db.stats.expeditionWins or 0) + 1
  local coins = floor(e.coins * 0.5 * (0.8 + random() * 0.4))
  self:AddCoins(coins)
  self:Print(string.format("|cff20ff20%s succeeded!|r +%d TapCoins, +%d XP for each cat.", e.name, coins, xp), true)
  if random() < e.chest[2] then self:AwardChest(e.chest[1], e.name) end
  -- extra chests instead of loose gear
  local bonus = TCF.ExpeditionBonusChance(e)
  for i = 1, e.rolls do
    if random() < bonus then self:AwardChest(e.chest[1] == "heroic" and "strong" or "pouch", e.name) end
  end
  -- a few skins are only brought home by expeditions (some by one expedition, some by any)
  self:RollSkinSource("expedition", function(g) return g.expedition == ex.key or g.expedition == "any" end,
    "Your party brought it home from " .. e.name, true)
  self:MarkDirty(); self:RefreshAll()
  return true
end

function TCF:ExpeditionsReady()
  local n, now = 0, time()
  for _, ex in ipairs(state(self).active) do if now >= ex.finish then n = n + 1 end end
  return n
end

-- Tell the player once when a party is back (also for parties that came home while
-- they were offline), and keep the window's countdown and Claim button current.
local notifier = CreateFrame("Frame")
local notifyAcc = 0
notifier:SetScript("OnUpdate", function(_, elapsed)
  notifyAcc = notifyAcc + elapsed
  if notifyAcc < 1 then return end
  notifyAcc = 0
  local db = TCF.db
  if not db or not db.expeditions then return end
  local now = time()
  for _, ex in ipairs(db.expeditions.active) do
    if now >= ex.finish and not ex.notified then
      ex.notified = true
      local e = TCF.EXPEDITION_BY_KEY[ex.key]
      TCF:Print(string.format("Your party is back from |cffffd100%s|r. Open the Expeditions tab to claim the rewards.", e and e.name or "an expedition"))
      -- chat is off by default, so also say it over the cat
      if TCF.cat and TCF.cat.Toast then TCF.cat:Toast((e and e.name or "Expedition") .. ": party is back!", 1, 0.82, 0.2) end
      TCF:MarkDirty()
    end
  end
end)
