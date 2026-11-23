-- TapCatForever: Adventure rewards that grow by zone, farmable bosses, boss cosmetics and the
-- plain-English status of the Adventure page.
--
--  * First kills: the first time a cat beats each Adventure boss it gets a reward that grows
--    with the zone (ADV_FIRST below). Gear comes from the boss's real loot (class-usable, never
--    Legendary), chests go to the Treasure Bag through TCF:AwardChest.
--  * Repeat kills: every later kill of a boss has a small chance to drop a piece of its real
--    loot (ADV_FARM): each piece min(0.4%, real drop chance x 0.012), all together at most 0.6%,
--    and never under 1 in 5,000 kills. A cat farming one boss kills it about 150-250 times an
--    hour (no trash in between), so a piece with a 16% real drop chance (Cruel Barb) takes about
--    3-4 hours of farming, and the rarest pieces about a day.
--  * Farming: "Farm this" keeps the cat on one boss's stage (Auto-advance off) until a wanted
--    piece drops (one chat line) or the player stops it.
--  * TCF.BOSS_COSMETICS: cosmetics an Adventure boss gives on every kill until owned.
local ADDON, TCF = ...

local floor, min, max, random = math.floor, math.min, math.max, math.random

-- TCF.BOSS_COSMETICS: filled by data files (the art track's own file).
--   key:   the Adventure boss's display name exactly as TCF.TIERS names it (the first field of
--          an entry in a tier's bosses list), e.g. "Ragnaros", "Edwin VanCleef", "Hogger"
--   value: a list of TCF.ITEMS keys, e.g. { "head_molten_crown", "fx_lava" }
-- On every Adventure kill of that boss, each listed item the player doesn't own yet is given,
-- quietly: no notice for cosmetics, one chat line if chat messages are on.
TCF.BOSS_COSMETICS = TCF.BOSS_COSMETICS or {}

---------------------------------------------------------------- zone bands
-- open-world zones, early dungeons (under level 30), mid dungeons (30-44), late dungeons (45+), raids
function TCF.AdvBand(t)
  if type(t) == "number" then t = TCF.TIERS[t] end
  if not t then return "world" end
  if t.raid then return "raid" end
  if not TCF.IsDungeonTier(t) then return "world" end
  if t.min < 30 then return "early" end
  if t.min < 45 then return "mid" end
  return "late"
end

-- What a first kill gives in each band. pieces: gear from the boss's loot; minQ: lowest quality;
-- chest/chance: a chest on top (non-final bosses: the zone clear already gives the final boss's
-- chest); orChest: instead of the gear. Final bosses use the "final" fields.
TCF.ADV_FIRST = {
  world = { pieces = 1, worldGreen = true, orChest = "pouch", orChance = 0.3, finalPieces = 1,
            text = "a green piece of gear or a Cat Treat Pouch" },
  early = { pieces = 1, chest = "pouch", chance = 0.25, finalPieces = 1,
            text = "a piece of its loot, and sometimes a Cat Treat Pouch" },
  mid   = { pieces = 1, minQ = 3, chest = "strong", chance = 0.2, finalPieces = 1,
            text = "a Rare or better piece of its loot, with a chance of an Adventurer's Strongbox" },
  late  = { pieces = 1, extraPiece = 0.5, chest = "dungeon", finalPieces = 2,
            text = "two pieces of its loot, or one piece and a Dungeon Chest" },
  raid  = { pieces = 2, chest = "raid", chance = 0.2, finalPieces = 2, finalExtra = 0.5,
            text = "two pieces of its loot, with a chance of a Raider's Hoard" },
}
TCF.ADV_FIRST_FINAL_RAID_TEXT = "two or three pieces of its loot and a Raider's Hoard"

-- Repeat kills: chance per piece = min(ITEM_MAX, real drop chance x SCALE), at least ITEM_MIN;
-- all pieces together at most TOTAL_MAX (the pieces above ITEM_MIN are scaled down evenly when a
-- boss has many). Measured with tools/tests/test_adv_rewards.py: farming one boss is 150-250
-- kills an hour, so ITEM_MIN (1 in 5,000) is about a day of farming.
TCF.ADV_FARM = { SCALE = 0.012, ITEM_MAX = 0.004, TOTAL_MAX = 0.006, ITEM_MIN = 0.0002 }

-- "a Cat Treat Pouch", "an Adventurer's Strongbox" (the same check as TCF:AwardChest)
function TCF.WithArticle(name)
  return (name:find("^[AEIOUaeiou]") and "an " or "a ") .. name
end

---------------------------------------------------------------- loot picks
local QDAMP = { 1, 1, 1, 0.35, 0 }  -- never a Legendary from a boss kill here

local function bossList(tier, boss)
  local list = TCF.BOSS_LOOT[tier] and TCF.BOSS_LOOT[tier][boss]
  if list and #list > 0 then return list, true end
  return TCF.TIER_POOL[tier], false
end

local function eligible(self, it, class)
  return it and not it.crafted and not it.retired and not it.placeholder and it.q <= 4 and self:GearUsable(it, class)
end

-- a weighted pick from a boss's loot: made-for-class pieces 4x as likely, real drop chances
local function pickLoot(self, list, class, minQ, exclude)
  local total, cands = 0, {}
  for _, it in ipairs(list or {}) do
    if eligible(self, it, class) and it.q >= (minQ or 0) and not (exclude and exclude[it.id]) then
      local w = max(5, it.dc or 0) * (QDAMP[it.q] or 1) * (self:GearSuits(it, class) and 4 or 1)
      if w > 0 then total = total + w; cands[#cands + 1] = { it, w } end
    end
  end
  if total <= 0 then return nil end
  local r = random() * total
  for _, c in ipairs(cands) do
    r = r - c[2]
    if r <= 0 then return c[1] end
  end
  return cands[#cands][1]
end

local function rollPiece(self, tier, m, class, minQ, exclude)
  local t = self:AdvTier(tier)
  local band = TCF.AdvBand(t)
  if band == "world" then
    -- open-world bosses have no loot tables: a green for the zone's level
    return self.RollWorldLoot and self:RollWorldLoot(max(t.min, m.level or t.min), class, { 100, 0, 0 }, tier)
  end
  local list = bossList(tier, m.boss)
  local it = pickLoot(self, list, class, minQ, exclude)
  if not it and minQ then it = pickLoot(self, list, class, nil, exclude) end
  if not it and exclude then it = pickLoot(self, list, class, minQ) end
  if not it and self.RollWorldLoot then
    it = self:RollWorldLoot(max(t.min, m.level or t.min), class, { 55, 38, 7 }, tier)
  end
  return it
end

---------------------------------------------------------------- first kills
-- The first-kill reward of a boss in this zone, in words (for the guide and tooltips).
function TCF:AdvFirstKillText(tier, final)
  local t = self:AdvTier(tier)
  local band = TCF.AdvBand(t)
  local R = TCF.ADV_FIRST[band]
  if final then
    if band == "raid" then return TCF.ADV_FIRST_FINAL_RAID_TEXT end
    if band == "late" then return "two pieces of its loot (the zone clear adds a Dungeon Chest)" end
    if band == "world" then return "a green piece of gear (the zone clear adds an Adventurer's Strongbox)" end
    if band == "mid" then return "a Rare or better piece of its loot (the zone clear adds a Dungeon Chest)" end
    return "a piece of its loot (the zone clear adds a Dungeon Chest)"
  end
  return R.text
end

-- Gives the first-kill reward for boss m (called by TCF:AdvMobKilled before the zone clear
-- chest). Returns a short description for the Adventure log.
function TCF:AdvFirstKillReward(tier, m)
  local class = self.db.class
  local t = self:AdvTier(tier)
  local band = TCF.AdvBand(t)
  local R = TCF.ADV_FIRST[band]
  local final = m.final
  local reason = m.name .. " (first kill)"
  local nPieces, chest = R.pieces, nil
  if final then
    nPieces = R.finalPieces or 1
    if R.finalExtra and random() < R.finalExtra then nPieces = nPieces + 1 end
  else
    if R.orChest and random() < R.orChance then nPieces, chest = 0, R.orChest end
    if R.extraPiece then
      if random() < R.extraPiece then nPieces = nPieces + 1 else chest = R.chest end
    elseif R.chest and random() < (R.chance or 0) then
      chest = R.chest
    end
  end
  local got, seen, items = {}, {}, {}
  for _ = 1, nPieces do
    local it = rollPiece(self, tier, m, class, R.minQ, seen)
    if it then
      seen[it.id] = true
      self:GrantGear(it, reason)
      items[#items + 1] = it
      got[#got + 1] = TCF.GearLink and TCF.GearLink(it) or it.name
    end
  end
  -- a first kill made while farming this boss counts too (and can be the wanted piece)
  if self.CD and self:CD().adv.farm then self:AdvFarmKill(tier, m, nil, items) end
  -- a zone whose bosses have nothing this class can use: a Pouch instead of nothing
  if #got == 0 and not chest and not final then chest = "pouch" end
  if chest then
    self:AwardChest(chest, reason)
    got[#got + 1] = TCF.WithArticle(TCF.CHEST_BY_KEY[chest].name)
  end
  return table.concat(got, " and ")
end

---------------------------------------------------------------- repeat kills (farming)
-- The pieces a boss can drop on a repeat kill for this class: { { item, chance }, ... } and the
-- total chance per kill. Only class-usable pieces; open-world bosses have none.
function TCF:AdvFarmTable(tier, boss, class)
  class = class or self.db.class
  local F = TCF.ADV_FARM
  local list, own = bossList(tier, boss)
  local out, total = {}, 0
  if not own then return out, 0 end
  for _, it in ipairs(list) do
    if eligible(self, it, class) then
      local p = min(F.ITEM_MAX, (it.dc or 0) / 1000 * F.SCALE)
      if p > 0 then out[#out + 1] = { it, max(p, F.ITEM_MIN or 0) }; total = total + out[#out][2] end
    end
  end
  -- over the cap: scale the pieces above the floor down evenly (a few rounds, as a scaled piece
  -- can reach the floor); the floor itself stays, so a wanted piece is never hopeless
  local lo = F.ITEM_MIN or 0
  for _ = 1, 6 do
    if total <= F.TOTAL_MAX + 1e-12 then break end
    local fixed, free = 0, 0
    for _, e in ipairs(out) do if e[2] <= lo then fixed = fixed + e[2] else free = free + e[2] end end
    if free <= 0 then break end
    local k = max(0, F.TOTAL_MAX - fixed) / free
    total = 0
    for _, e in ipairs(out) do
      if e[2] > lo then e[2] = max(lo, e[2] * k) end
      total = total + e[2]
    end
  end
  table.sort(out, function(a, b)
    if a[2] ~= b[2] then return a[2] > b[2] end
    return a[1].name < b[1].name
  end)
  return out, total
end

-- the chance per kill of one piece (0 if this class can't get it from this boss)
function TCF:AdvFarmChance(tier, boss, itemId, class)
  local list = self:AdvFarmTable(tier, boss, class)
  for _, e in ipairs(list) do if e[1].id == itemId then return e[2] end end
  return 0
end

-- rolls the repeat-kill drop; returns the item or nil
function TCF:AdvRepeatLoot(tier, m)
  local list = self:AdvFarmTable(tier, m.boss)
  local r = random()
  for _, e in ipairs(list) do
    r = r - e[2]
    if r < 0 then
      self:GrantGear(e[1], m.name)
      return e[1]
    end
  end
end

-- "4%", "0.3%", "0.15%" (two digits that mean something); "under 0.01%" for less
function TCF.AdvPct(p)
  p = (p or 0) * 100
  if p > 0 and p < 0.01 then return "under 0.01%" end
  if p > 0 and p < 0.1 then return string.format("%.2f%%", p) end
  if p > 0 and p < 1 then return string.format("%.1f%%", p) end
  return string.format("%d%%", floor(p + 0.5))
end

-- (1.6.0) a drop chance per kill as players read it: "0.4% a kill", "12% a kill", "under 0.1% a kill"
-- (no "after so many minutes of fighting": the chance per kill says it plainly)
function TCF.AdvKillChance(p)
  p = (p or 0) * 100
  if p <= 0 then return "0% a kill" end
  if p < 0.1 then return "under 0.1% a kill" end
  if p < 10 then
    local s = string.format("%.1f", p):gsub("%.0$", "")
    return s .. "% a kill"
  end
  return string.format("%d%% a kill", floor(p + 0.5))
end

-- "about 1 in 650 kills" for a chance per kill
function TCF.AdvOneIn(p)
  if not p or p <= 0 then return "never" end
  local n = 1 / p
  if n >= 100 then n = floor(n / 10 + 0.5) * 10 else n = floor(n + 0.5) end
  return "1 in " .. TCF.Commas(n) .. " kills"
end

---------------------------------------------------------------- farming
local function bossStage(bi) return bi * 2 end

-- Starts farming boss bi of a zone, optionally for one piece (item id). The cat must have
-- reached that boss. Turns Auto-advance off (it comes back on when farming stops).
function TCF:AdvStartFarm(tier, bi, itemId)
  local adv = self:CD().adv
  local t = TCF.TIERS[tier]
  local b = t and t.bosses[bi]
  if not b then return false, "No such boss." end
  local stage = bossStage(bi)
  if not self:AdvCanGoTo(tier, stage) then return false, "Your cat hasn't reached " .. b[1] .. " yet." end
  local prevAuto = adv.auto
  if adv.farm then prevAuto = adv.farm.prevAuto end
  self.advFarmMove = true
  local ok = self:AdvGoTo(tier, stage)
  self.advFarmMove = nil
  if not ok then return false, "Your cat can't go there right now." end
  adv.auto = false
  adv.farm = { tier = tier, stage = stage, boss = bi, name = b[1], item = itemId, kills = 0, prevAuto = prevAuto }
  local it = itemId and TCF.GEAR[itemId]
  local p = itemId and self:AdvFarmChance(tier, bi, itemId) or select(2, self:AdvFarmTable(tier, bi))
  self:AdvLog(string.format("|cffffd100Farming %s%s (%s).|r", b[1], it and (" for " .. it.name) or "", TCF.AdvKillChance(p)))
  if not adv.active and not (self.IsOnExpedition and self:IsOnExpedition(self.db.class)) then self:AdvStart() end
  self:MarkDirty()
  return true
end

-- Stops farming. why: a short chat line (printed even with chat messages off: the player asked
-- for the farming), or nil for none. Auto-advance goes back to what it was.
function TCF:AdvStopFarm(why)
  local adv = self:CD().adv
  local f = adv.farm
  if not f then return end
  adv.farm = nil
  if f.prevAuto ~= nil then adv.auto = f.prevAuto end
  if why then self:Print(why, true) end
  self:MarkDirty()
end

-- after a pack is cleared: keep the cat on the farmed boss (a drop-back after losses returns
-- to it after the easier pack); turning Auto-advance on, or the zone changing, ends farming
function TCF:AdvFarmAfterClear()
  local adv = self:CD().adv
  local f = adv.farm
  if not f then return end
  if adv.auto then adv.farm = nil; return end
  if adv.tier ~= f.tier then self:AdvStopFarm(); return end
  if adv.stage ~= f.stage then adv.stage = f.stage end
end

-- turning Auto-advance on ends farming at once (Auto-advance stays on); the page checks this
-- twice a second, the pack-cleared step after every pack
function TCF:AdvFarmCheckAuto()
  local adv = self:CD().adv
  if adv.farm and adv.auto then adv.farm = nil; self:MarkDirty(); return true end
end

-- called on every boss kill: repeat kills from TCF:AdvMobKilled with their drop (or nil), first
-- kills from TCF:AdvFirstKillReward with the pieces they gave (gotList)
function TCF:AdvFarmKill(tier, m, dropped, gotList)
  local adv = self:CD().adv
  local f = adv.farm
  if not f or f.tier ~= tier or f.boss ~= m.boss then return end
  f.kills = f.kills + 1
  if f.item and not (dropped and dropped.id == f.item) then
    for _, it in ipairs(gotList or {}) do if it.id == f.item then dropped = it end end
  end
  if f.item and dropped and dropped.id == f.item then
    self:AdvLog(string.format("|cff20ff20%s dropped %s after %d kills. Farming stopped.|r", m.name, dropped.name, f.kills))
    self:AdvStopFarm(string.format("%s dropped %s after %d %s. Farming stopped.", m.name, TCF.GearLink and TCF.GearLink(dropped) or dropped.name,
      f.kills, f.kills == 1 and "kill" or "kills"))
  end
end

-- moving by hand (zone arrows, stage buttons) ends farming
do
  local goTo = TCF.AdvGoTo
  function TCF:AdvGoTo(tier, stage)
    local ok = goTo(self, tier, stage)
    if ok and not self.advFarmMove and self:CD().adv.farm then self:AdvStopFarm() end
    return ok
  end
end

---------------------------------------------------------------- boss cosmetics
function TCF:AdvBossCosmetics(m)
  local list = TCF.BOSS_COSMETICS[m.name]
  if type(list) ~= "table" then return end
  local t = self:AdvTier(self:CD().adv.tier)
  for _, id in ipairs(list) do
    local it = TCF.ITEMS[id]
    if it and not self.db.owned[id] then
      local reason = "Dropped by " .. m.name .. " in " .. t.name
      if it.slot == "skin" then self:GrantSkin(id, reason) else self:GrantItem(it, reason) end
    end
  end
end

-- The Adventure bosses that give this cosmetic (for "how to get it"): { { boss, zone name }, ... }
function TCF:BossCosmeticSources(id)
  local out = {}
  for boss, list in pairs(TCF.BOSS_COSMETICS) do
    if type(list) == "table" then
      for _, x in ipairs(list) do
        if x == id then
          local zone
          for _, t in ipairs(TCF.TIERS) do
            for _, b in ipairs(t.bosses) do if b[1] == boss then zone = zone or t.name end end
          end
          out[#out + 1] = { boss, zone }
        end
      end
    end
  end
  table.sort(out, function(a, b) return a[1] < b[1] end)
  return out
end

---------------------------------------------------------------- what's left to earn, status
-- Lines for the zone tooltip: what this cat can still earn in a zone.
function TCF:AdvZoneSummary(tier)
  local cd = self:CD()
  local adv = cd.adv
  local t = self:AdvTier(tier)
  local lines = {}
  local left = {}
  for bi, b in ipairs(t.bosses) do
    if not adv.cleared[TCF.AdvStageCode(tier, bi * 2)] then left[#left + 1] = b[1] end
  end
  if #left > 0 then
    lines[#lines + 1] = string.format("First kills left (%d of %d): %s.", #left, #t.bosses, table.concat(left, ", "))
    lines[#lines + 1] = "Each first kill gives " .. self:AdvFirstKillText(tier) .. "."
  else
    lines[#lines + 1] = "Every boss here is beaten: first-kill rewards are done."
  end
  local finalCode = TCF.AdvStageCode(tier, self:AdvStages(tier))
  local chestName = t.raid and "Raider's Hoard" or TCF.IsDungeonTier(t) and "Dungeon Chest" or "Adventurer's Strongbox"
  if not adv.cleared[finalCode] then
    lines[#lines + 1] = string.format("Zone clear (first time for this cat): %s TapCoins and %s.", TCF.Commas(self:AdvClearCoins(tier)), TCF.WithArticle(chestName))
  else
    lines[#lines + 1] = "Zone cleared."
  end
  -- chests on the fighting-time clocks: the chance per kill right now (it grows while the cat fights)
  local cA, cD = self:AdvChestChances(tier)
  local chest = t.raid and "Raider's Hoard" or "Cat Treat Pouch"
  lines[#lines + 1] = string.format("%s from boss kills: %s right now (it grows the longer your cat fights, until one drops).", chest, TCF.AdvKillChance(cA))
  if cD then
    lines[#lines + 1] = string.format("Dungeon Chest from finishing this dungeon again: %s right now (it grows with dungeon fighting).", TCF.AdvKillChance(cD))
  end
  local farmable = 0
  for bi = 1, #t.bosses do
    local _, p = self:AdvFarmTable(tier, bi)
    if p > 0 then farmable = farmable + 1 end
  end
  if farmable > 0 then
    lines[#lines + 1] = string.format("%d %s here can drop loot for your cat on repeat kills (see Bosses and loot).", farmable, farmable == 1 and "boss" or "bosses")
  end
  return lines
end

-- the chance a boss kill drops a chest right now (the fighting-time clocks, Adventure.lua), and for
-- a dungeon the chance its final boss gives a Dungeon Chest (nil outside dungeons)
function TCF:AdvChestChances(tier)
  local adv = self:CD().adv
  local t = self:AdvTier(tier or adv.tier)
  local A = TCF.ADV
  local lo, ramp = A.CHEST_MIN, A.CHEST_RAMP
  if t.raid then lo, ramp = A.RAID_CHEST_MIN, A.RAID_CHEST_RAMP end
  local c = min(1, max(0, ((adv.chestClock or 0) - lo) / ramp))
  local d
  if TCF.IsDungeonTier(t) then d = min(1, max(0, ((adv.dungeonClock or 0) - A.DUNGEON_CHEST_MIN) / A.DUNGEON_CHEST_RAMP)) end
  return c, d
end

-- The status line under the fight: what the cat is doing and why, in plain English.
function TCF:AdvStatusText()
  local cd = self:CD()
  local adv = cd.adv
  local t = self:AdvTier(adv.tier)
  local f = adv.farm
  if f and not adv.auto then
    local it = f.item and TCF.GEAR[f.item]
    local p = it and self:AdvFarmChance(f.tier, f.boss, f.item) or select(2, self:AdvFarmTable(f.tier, f.boss))
    return string.format("Farming %s for %s (%s), kills so far: %d.", f.name,
      it and it.name or "any of its loot", TCF.AdvKillChance(p), f.kills)
  end
  local n = self:AdvStages(adv.tier)
  local cleared = adv.best >= TCF.AdvStageCode(adv.tier, n)
  local nt = TCF.TIERS[adv.tier + 1]
  if not cleared then
    local final = t.bosses[#t.bosses][1]
    local s = string.format("Stage %d of %d in %s. Beat the final boss, %s, to clear the zone.", adv.stage, n, t.name, final)
    if not adv.auto then s = s .. " Auto-advance is off, so your cat repeats this stage." end
    return s
  end
  if not nt then
    return t.name .. " cleared. This is the last zone: your cat keeps fighting here, and its bosses can still drop their loot."
  end
  local need = self:AdvAutoLevel(adv.tier + 1)
  if not adv.auto then
    return string.format("%s cleared. Auto-advance is off, so your cat stays on this stage. Turn it on, or use > to go to %s.", t.name, nt.name)
  end
  if cd.level < need then
    return string.format("%s cleared. Next: %s opens at level %d (your cat is %d). Farming here until then.", t.name, nt.name, need, cd.level)
  end
  return string.format("%s cleared. Your cat moves on to %s after this run.", t.name, nt.name)
end
