-- TapCatForever: chest opening reel. Random possible loot (rolled with the chest's own
-- rarity odds, never the same item twice) scrolls by, slows down and lands on the real reward.
local ADDON, TCF = ...
local floor, random, min, max = math.floor, math.random, math.min, math.max

local CARD, GAP, VISIBLE, COUNT, LAND = 56, 6, 8, 34, 30
local STEP = CARD + GAP
local DUR, HOLD = 2.4, 0.45

-- gear by quality, built once from the loot pools, so it is only gear chests can hold: never
-- crafted gear, retired random-suffix bases or Blizzard's placeholder items
local gearByQ
local function gearPool(q)
  if not gearByQ then
    gearByQ = {}
    local function add(list)
      for _, g in ipairs(list or {}) do
        if not g.crafted and not g.retired then
          gearByQ[g.q] = gearByQ[g.q] or {}; table.insert(gearByQ[g.q], g)
        end
      end
    end
    for _, list in pairs(TCF.WORLD_POOL) do add(list) end
    for _, list in pairs(TCF.TIER_POOL) do add(list) end
    for _, bosses in pairs(TCF.BOSS_LOOT) do for _, list in pairs(bosses) do add(list) end end
  end
  return gearByQ[q] or {}
end

-- a random thing this chest could hold: gear (90%) or a cosmetic (10%) of a rolled rarity,
-- the same split as TCF:OpenChest. A Legendary roll shows a real legendary (now and then,
-- at the chest's own odds); gear-only chests show what they can hold: the raid epics for a
-- Raider's Hoard, the dungeon loot near the cat's level for a Dungeon Chest.
local function randomLoot(ch, seen, raidPool, legends, dungeonPool)
  local class = TCF.db.class
  for _ = 1, 30 do
    local r = TCF:RollRarity(ch.weights)
    local it, rarity
    if (ch.legendary or 0) > 0 and #legends > 0 and random() < ch.legendary then
      local g = legends[random(#legends)]
      it, rarity = g, g.q
    elseif ch.gearOnly or random() < (TCF.CHEST_GEAR_CHANCE or 0.9) then
      local g
      local dpool = ch.dungeonLoot and dungeonPool and dungeonPool[max(2, min(4, r))]
      if (ch.raidLoot or r >= 5) and #raidPool > 0 then
        g = raidPool[random(#raidPool)]   -- the Legendary rarity roll is a raid boss Epic (cats 55+)
      elseif dpool and #dpool > 0 then
        g = dpool[random(#dpool)]
      else
        -- what this chest can really give the cat now: gear near its level (TCF:ChestGearPool),
        -- one quality lower when there is none of the rolled one
        local level = (TCF:CD() and TCF:CD().level) or 1
        for q = max(2, min(4, (ch.raidLoot or r >= 5) and 4 or r)), 2, -1 do
          local pool = TCF.ChestGearPool and TCF:ChestGearPool(class, level, q) or gearPool(q)
          if #pool > 0 then g = pool[random(#pool)]; break end
        end
      end
      if g and TCF:GearUsable(g, class) then it, rarity = g, g.q end
    else
      local c = TCF.ITEM_LIST[random(#TCF.ITEM_LIST)]
      if c.source == "loot" and c.rarity == r and (c.class == nil or c.class == class) then it, rarity = c, c.rarity end
    end
    if it and not seen[it] then seen[it] = true; return it, rarity end
  end
  local c = TCF.ITEM_LIST[random(#TCF.ITEM_LIST)]
  return c, c.rarity
end

local function makeCard(parent)
  local c = CreateFrame("Frame", nil, parent)
  c:SetSize(CARD, CARD)
  c.bg = c:CreateTexture(nil, "BACKGROUND"); c.bg:SetAllPoints(); c.bg:SetColorTexture(0.08, 0.07, 0.1, 1)
  c.edge = c:CreateTexture(nil, "BORDER"); c.edge:SetAllPoints()
  c.icon = c:CreateTexture(nil, "ARTWORK"); c.icon:SetPoint("TOPLEFT", 4, -4); c.icon:SetPoint("BOTTOMRIGHT", -4, 4)
  c.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
  -- cosmetics get a purple corner badge so they're easy to tell from gear
  c.tag = c:CreateTexture(nil, "OVERLAY", nil, 2); c.tag:SetSize(14, 14); c.tag:SetPoint("TOPRIGHT", -2, -2); c.tag:SetColorTexture(0.75, 0.45, 1, 1)
  c.glow = c:CreateTexture(nil, "OVERLAY"); c.glow:SetPoint("TOPLEFT", -10, 10); c.glow:SetPoint("BOTTOMRIGHT", 10, -10)
  c.glow:SetTexture("Interface\\Buttons\\CheckButtonHilight"); c.glow:SetBlendMode("ADD"); c.glow:Hide()
  return c
end

local function setCard(c, it, rarity)
  local col = TCF.RARITY[rarity] and TCF.RARITY[rarity].color or { 1, 1, 1 }
  c.edge:SetColorTexture(col[1], col[2], col[3], 1)
  c.icon:SetTexture(TCF.Icon(it.icon or "INV_Misc_QuestionMark"))
  c.tag:SetShown(it.q == nil)
  c.glow:Hide()
end

local function createReel()
  local f = CreateFrame("Frame", "TapCatForeverReel", UIParent, TCF.UI.BT)
  f:SetSize(VISIBLE * STEP + 40, 150); f:SetPoint("CENTER", 0, 80)
  f:SetFrameStrata("FULLSCREEN_DIALOG"); f:SetToplevel(true); f:EnableMouse(true)
  if f.SetBackdrop then f:SetBackdrop(TCF.UI.BACKDROP_DIALOG) end
  f.title = TCF.UI.Text(f, "GameFontNormalLarge"); f.title:SetPoint("TOP", 0, -16)
  f.hint = TCF.UI.Text(f, "GameFontDisableSmall", "Click to skip"); f.hint:SetPoint("BOTTOM", 0, 10)
  local strip = CreateFrame("Frame", nil, f)
  strip:SetSize(VISIBLE * STEP, CARD + 8); strip:SetPoint("CENTER", 0, -4)
  if strip.SetClipsChildren then strip:SetClipsChildren(true) end
  f.strip = strip
  f.cards = {}
  for i = 1, COUNT do f.cards[i] = makeCard(strip) end
  -- the gold marker in the middle
  local mk = f:CreateTexture(nil, "OVERLAY"); mk:SetSize(4, CARD + 16); mk:SetPoint("CENTER", strip, "CENTER", 0, 0); mk:SetColorTexture(1, 0.82, 0.2, 0.9)
  f:SetScript("OnMouseUp", function(s) if s.t < DUR then s.t = DUR end end)
  f:SetScript("OnUpdate", function(s, e)
    s.t = s.t + e
    local p = min(1, s.t / DUR)
    local ease = 1 - (1 - p) ^ 3
    local off = s.endOff * ease
    local center = VISIBLE * STEP / 2
    for i, c in ipairs(s.cards) do
      c:ClearAllPoints()
      c:SetPoint("LEFT", s.strip, "LEFT", (i - 1) * STEP + GAP / 2 - off, 0)
    end
    -- a soft tick each time a new card passes the marker
    local idx = floor((off + center) / STEP)
    if idx ~= s.lastIdx then s.lastIdx = idx; if p < 1 then TCF:PlaySound("click") end end
    if p >= 1 and not s.landed then
      s.landed = true
      s.cards[LAND].glow:Show()
      TCF:PlaySound(s.rarity >= 5 and "legendary" or s.rarity >= 4 and "rare" or "loot")
    end
    if s.t >= DUR + HOLD then s:Finish() end
  end)
  function f:Finish()
    self:Hide()
    local queue = self.queue
    self.queue = {}
    local lr = TCF.lootReveal
    for i, args in ipairs(queue) do
      -- the item the reel landed on takes over a loot box that is already up, so the box
      -- shows what you just watched (everything else still queues behind it)
      -- every chest you open shows its loot box when the reel ends, whatever the quality
      if i == 1 and lr and lr:IsShown() and lr.ShowFront then lr:ShowFront(args)
      else TCF.ShowLootRevealDirect(TCF, unpack(args, 1, 7)) end
    end
  end
  f.queue = {}
  f:Hide()
  return f
end

-- Play the reel for a chest reward, then show the usual loot box.
function TCF:PlayChestReel(it, rarity, chestKey, args)
  local f = self.reel or createReel(); self.reel = f
  if f:IsShown() then table.insert(f.queue, args); return end
  local ch = TCF.CHEST_BY_KEY[chestKey]
  f.title:SetText("Opening " .. (ch and ch.name or "chest") .. "...")
  local seen = { [it] = true }
  -- built once per reel: raid epics for a Raider's Hoard (the ones it can hold for this cat)
  -- or for a Legendary rarity roll (any raid), and the legendaries this class can use
  local raidPool, legends, dungeonPool = {}, {}, nil
  local level = (self:CD() and self:CD().level) or 1
  if ch and TCF.RaidHoardPool and level >= 55 then raidPool = TCF:RaidHoardPool(nil, not ch.raidLoot) end
  if ch and TCF.LegendariesFor and level >= 60 then legends = TCF:LegendariesFor() end
  -- and for a Dungeon Chest: the dungeon loot it can hold for this cat, by quality
  if ch and ch.dungeonLoot and TCF.DungeonChestPool then dungeonPool = TCF:DungeonChestPool() end
  for i, c in ipairs(f.cards) do
    if i == LAND then setCard(c, it, rarity)
    elseif ch then local r, rr = randomLoot(ch, seen, raidPool, legends, dungeonPool); setCard(c, r, rr)
    else local r = TCF.ITEM_LIST[random(#TCF.ITEM_LIST)]; setCard(c, r, r.rarity) end
  end
  local center = VISIBLE * STEP / 2
  f.endOff = (LAND - 1) * STEP + GAP / 2 + CARD / 2 - center + random(-CARD * 0.3, CARD * 0.3)
  f.t, f.landed, f.lastIdx, f.rarity = 0, false, nil, rarity
  f.queue = { args }
  f:Show()
end

-- TapCoins a chest gave (Core.lua's OpenChest sets TCF.chestCoins while the chest opens). They go
-- with the chest's first reward only (a skin found in the same chest doesn't repeat them); a
-- chest opening is told apart by the chest count, which goes up once per chest.
local coinsTaken
local function takeChestCoins(self, chestKey)
  local c = chestKey and tonumber(self.chestCoins)
  if not c or c < 1 then return nil end
  local opening = self.db and self.db.stats and self.db.stats.chests
  if opening and opening == coinsTaken then return nil end
  coinsTaken = opening
  return floor(c)
end

-- Hook the loot box: chest rewards spin first (unless turned off, or opening many at once).
TCF.ShowLootRevealDirect = TCF.ShowLootReveal
function TCF:ShowLootReveal(it, isNew, salvage, title, chestKey, isGear, coins)
  coins = coins or takeChestCoins(self, chestKey)
  local args = { it, isNew, salvage, title, chestKey, isGear, coins }
  -- only chest openings (your own click) get the reel and the loot box; everything else goes
  -- straight into your bags with at most a slim line (LootToast.lua). "Open all" still lists
  -- everything in the loot window.
  if self.ShowLootToast and not chestKey and not self.forceReveal then
    return self:ShowLootToast(it, isNew, salvage, title, isGear)
  end
  local quality = it and (isGear and it.q or it.rarity) or 1
  local ch = chestKey and TCF.CHEST_BY_KEY[chestKey]
  -- every chest you open yourself spins the reel (unless turned off), then shows the loot box
  if ch and it and self.db.ui.chestAnim ~= false and not self.openingAll then
    return self:PlayChestReel(it, quality, chestKey, args)
  end
  if self.reel and self.reel:IsShown() then table.insert(self.reel.queue, args); return end
  -- no reel (animation off): a single chest opened while the box is up still shows at once
  if ch and it and not self.openingAll and self.lootReveal and self.lootReveal:IsShown() and self.lootReveal.ShowFront then
    return self.lootReveal:ShowFront(args)
  end
  return TCF.ShowLootRevealDirect(self, unpack(args, 1, 7))
end
