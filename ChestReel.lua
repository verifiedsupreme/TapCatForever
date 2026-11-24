-- TapCatForever: chest opening reel. Possible loot (rolled with the chest's own rarity odds, or
-- for the Heroic Cache a set mix of what it can hold; never the same item twice on screen)
-- scrolls by at full speed, brakes and lands on the real reward.
local ADDON, TCF = ...
local floor, random, min, max = math.floor, math.random, math.min, math.max

local CARD, GAP, VISIBLE, COUNT, LAND = 56, 6, 8, 44, 40
local STEP = CARD + GAP
-- the reel runs at full speed for CRUISE seconds, then brakes onto the prize for BRAKE seconds
local CRUISE, BRAKE = 0.7, 1.4
local DUR, HOLD = CRUISE + BRAKE, 0.55
local TICK_GAP = 0.045   -- at most one tick sound this often, however fast the cards go
local NEAR = VISIBLE     -- the same item never shows twice this close together (on screen at once)
local LOCK_TEX = "Interface\\Buttons\\LockButton-Locked-Up"

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

local function rarityOf(it) return it.q or it.rarity or 1 end

-- when nothing new is left to show: an item already on the strip that is not within NEAR cards
-- of position i (so never twice on screen), and never the prize
local function repeatPick(placed, i, prize)
  local near, cands, seen = {}, {}, {}
  for j = i - NEAR + 1, i + NEAR - 1 do if placed[j] then near[placed[j]] = true end end
  for j = 1, COUNT do
    local it = placed[j]
    if it and it ~= prize and not near[it] and not seen[it] then seen[it] = true; cands[#cands + 1] = it end
  end
  if #cands > 0 then return cands[random(#cands)] end
end

-- a random thing this chest could hold: gear (90%) or a cosmetic (10%) of a rolled rarity,
-- the same split as TCF:OpenChest. A Legendary roll shows a real legendary (now and then,
-- at the chest's own odds); gear-only chests show what they can hold: the raid epics for a
-- Raider's Hoard, the dungeon loot near the cat's level for a Dungeon Chest.
local function randomLoot(ch, seen, raidPool, legends, dungeonPool, level, placed, pos, prize)
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
        level = level or (TCF:CD() and TCF:CD().level) or 1
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
  -- nothing new found: repeat something already on the strip, but never on screen twice
  local it = placed and repeatPick(placed, pos, prize)
  if it then return it, rarityOf(it) end
  for _ = 1, 50 do
    local c = TCF.ITEM_LIST[random(#TCF.ITEM_LIST)]
    if c.source == "loot" and (c.class == nil or c.class == class) then return c, c.rarity end
  end
  local c = TCF.ITEM_LIST[random(#TCF.ITEM_LIST)]
  return c, c.rarity
end

local function shuffle(t)
  for i = #t, 2, -1 do local j = random(i); t[i], t[j] = t[j], t[i] end
  return t
end
local function copy(list, into)
  into = into or {}
  for _, it in ipairs(list or {}) do into[#into + 1] = it end
  return into
end
-- up to n random items from the best `top` of a list by item level
local function bestOf(list, top, n)
  local l = copy(list)
  table.sort(l, function(a, b)
    if (a.ilvl or 0) ~= (b.ilvl or 0) then return (a.ilvl or 0) > (b.ilvl or 0) end
    return (a.id or 0) < (b.id or 0)
  end)
  for i = #l, top + 1, -1 do l[i] = nil end
  shuffle(l)
  for i = #l, n + 1, -1 do l[i] = nil end
  return l
end

-- The level a chest needs to really give this item, when this cat is too young for it: a
-- legendary needs 60, a raid boss Epic 55 (anything else is in the cat's own gear window).
local function lockLevel(it, level, raid)
  if it.q == 5 and level < 60 then return 60 end
  if raid[it] then return level < 55 and 55 or nil end   -- the Legendary rarity roll gives these at 55+
  if it.q and (it.req or 0) > level + 3 then return it.req end
end

-- The Heroic Cache's strip (ch.reel): a mix chosen to show what the chest can really hold
-- for this cat, plus a few big prizes it can't win yet (locked, with the level they need).
-- Returns COUNT entries { it, rarity, locked, kind } with the prize at LAND.
local function buildDeck(ch, prize, prizeRarity, level)
  local class = TCF.db.class
  local mix = ch.reel
  local raid = {}
  local raidAll = TCF.RaidHoardPool and TCF:RaidHoardPool(nil, true) or {}
  for _, it in ipairs(raidAll) do raid[it] = true end
  local legends = TCF.LegendariesFor and TCF:LegendariesFor() or {}
  -- the pools, each shuffled; ChestGearPool is asked for this cat's own class and level only
  -- (the real roll uses the same), and copied since it is a shared cache
  local pools = {}
  pools.rare = shuffle(copy(TCF:ChestGearPool(class, level, 3)))
  pools.epic = copy(TCF:ChestGearPool(class, level, 4))
  if level >= 55 then copy(raidAll, pools.epic) end
  shuffle(pools.epic)
  pools.cosmetic = {}
  for _, it in ipairs(TCF.ITEM_LIST) do
    if it.source == "loot" and (it.rarity or 0) >= 3 and (it.class == nil or it.class == class) then
      pools.cosmetic[#pools.cosmetic + 1] = it
    end
  end
  shuffle(pools.cosmetic)
  pools.skin = shuffle(TCF:UnownedShopSkins())
  -- the big prizes: two legendaries, then raid boss Epics (the best ones while the cat is
  -- young). Cards are drawn from the end of a pool, so the legendaries go last.
  local nChase = mix.chase or 0
  local bigLegends = bestOf(legends, 8, min(2, nChase))
  local wantRaid = nChase - #bigLegends
  if level >= 55 then pools.chase = shuffle(copy(raidAll))
  else pools.chase = bestOf(raidAll, 8, wantRaid) end
  copy(bigLegends, pools.chase)
  -- where a card goes when its own pool has run dry ("cosmetic4": an Epic or better cosmetic,
  -- so a cat too young for Epic gear still sees Epics it can really win)
  local fallback = {
    chase = { "chase", "epic", "cosmetic4", "rare", "cosmetic" },
    epic = { "epic", "cosmetic4", "rare", "cosmetic" },
    rare = { "rare", "epic", "cosmetic" },
    skin = { "skin", "cosmetic", "epic", "rare" },
    cosmetic = { "cosmetic", "epic", "rare" },
  }
  -- where each kind goes: big prizes where the reel is braking (6 and 11 before the prize) and
  -- early on, never among the cards still on screen when it stops (no fake near miss); shop
  -- skins anywhere before the last few; the rest shuffled into what is left
  local kindAt = { [LAND] = "prize" }
  local function freeIn(lo, hi)
    local out = {}
    for p = max(1, lo), min(COUNT, hi) do if not kindAt[p] then out[#out + 1] = p end end
    return out
  end
  local function put(kind, n, lo, hi)
    local free = shuffle(freeIn(lo, hi))
    for k = 1, min(n, #free) do kindAt[free[k]] = kind end
    return max(0, n - #free)
  end
  local chaseLeft = nChase
  for _, p in ipairs({ LAND - 6, LAND - 11 }) do
    if chaseLeft > 0 and p >= 1 and not kindAt[p] then kindAt[p] = "chase"; chaseLeft = chaseLeft - 1 end
  end
  local extra = put("chase", chaseLeft, 6, LAND - 15)
  extra = put("chase", extra, 1, LAND - NEAR / 2 - 1)
  local rest = {}
  for _ = 1, extra do rest[#rest + 1] = "epic" end   -- no room left for a big prize
  local skinsLeft = put("skin", mix.skin or 0, 6, LAND - 3)
  for _ = 1, skinsLeft do rest[#rest + 1] = "cosmetic" end
  for _, kind in ipairs({ "cosmetic", "epic", "rare" }) do
    for _ = 1, mix[kind] or 0 do rest[#rest + 1] = kind end
  end
  shuffle(rest)
  local free = freeIn(1, COUNT)
  for k, p in ipairs(free) do kindAt[p] = rest[k] or "rare" end

  local seen = { [prize] = true }
  local placed = { [LAND] = prize }
  -- many cosmetics share one icon, so a card also avoids an icon already shown nearby (when the
  -- pool has anything else), or the strip would look like the same item over and over
  local function draw(kind, p)
    local near = {}
    for j = p - NEAR + 1, p + NEAR - 1 do if placed[j] then near[placed[j].icon or "?"] = true end end
    for _, from in ipairs(fallback[kind] or fallback.rare) do
      local pool, minRarity = pools[from], 0
      if from == "cosmetic4" then pool, minRarity = pools.cosmetic, 4 end
      for pass = 1, 2 do
        for k = #pool, 1, -1 do
          local it = pool[k]
          if seen[it] then table.remove(pool, k)
          elseif rarityOf(it) >= minRarity and (pass == 2 or not near[it.icon or "?"]) then
            table.remove(pool, k); seen[it] = true
            return it, from == "cosmetic4" and "cosmetic" or from
          end
        end
      end
    end
  end
  local deck = {}
  for p = 1, COUNT do
    if p == LAND then
      deck[p] = { it = prize, rarity = prizeRarity, kind = "prize" }
    else
      local it, from = draw(kindAt[p], p)
      if not it then it, from = repeatPick(placed, p, prize), "repeat" end
      if not it then
        -- next to nothing to show (should not happen): a cosmetic this cat could find
        for _ = 1, 50 do
          local c = TCF.ITEM_LIST[random(#TCF.ITEM_LIST)]
          if c.source == "loot" and c ~= prize and (c.class == nil or c.class == class) then it = c; break end
        end
        it, from = it or prize, "repeat"
      end
      placed[p] = it
      local need = lockLevel(it, level, raid)
      deck[p] = { it = it, rarity = rarityOf(it), locked = need ~= nil, need = need, kind = from }
    end
  end
  return deck
end

-- the chests' own random strip (every chest without a ch.reel mix)
local function randomDeck(ch, prize, prizeRarity, level)
  local seen = { [prize] = true }
  -- built once per reel: raid epics for a Raider's Hoard (the ones it can hold for this cat)
  -- or for a Legendary rarity roll (any raid), and the legendaries this class can use
  local raidPool, legends, dungeonPool = {}, {}, nil
  if ch and TCF.RaidHoardPool and level >= 55 then raidPool = TCF:RaidHoardPool(nil, not ch.raidLoot) end
  if ch and TCF.LegendariesFor and level >= 60 then legends = TCF:LegendariesFor() end
  -- and for a Dungeon Chest: the dungeon loot it can hold for this cat, by quality
  if ch and ch.dungeonLoot and TCF.DungeonChestPool then dungeonPool = TCF:DungeonChestPool(nil, level) end
  local deck, placed = {}, { [LAND] = prize }
  for i = 1, COUNT do
    if i == LAND then deck[i] = { it = prize, rarity = prizeRarity, kind = "prize" }
    elseif ch then
      local r, rr = randomLoot(ch, seen, raidPool, legends, dungeonPool, level, placed, i, prize)
      placed[i] = r; deck[i] = { it = r, rarity = rr, kind = "random" }
    else
      local r = TCF.ITEM_LIST[random(#TCF.ITEM_LIST)]
      deck[i] = { it = r, rarity = r.rarity, kind = "random" }
    end
  end
  return deck
end

local function makeCard(parent)
  local c = CreateFrame("Frame", nil, parent)
  c:SetSize(CARD, CARD)
  c.bg = c:CreateTexture(nil, "BACKGROUND"); c.bg:SetAllPoints(); c.bg:SetColorTexture(0.08, 0.07, 0.1, 1)
  c.edge = c:CreateTexture(nil, "BORDER"); c.edge:SetAllPoints()
  c.icon = c:CreateTexture(nil, "ARTWORK"); c.icon:SetPoint("TOPLEFT", 4, -4); c.icon:SetPoint("BOTTOMRIGHT", -4, 4)
  c.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
  -- Epics and better get a soft shine so they stand out while the strip scrolls
  c.shine = c:CreateTexture(nil, "OVERLAY", nil, 1); c.shine:SetAllPoints(c.icon)
  c.shine:SetTexture("Interface\\Buttons\\CheckButtonHilight"); c.shine:SetBlendMode("ADD"); c.shine:SetAlpha(0.35); c.shine:Hide()
  -- cosmetics get a purple corner badge so they're easy to tell from gear
  c.tag = c:CreateTexture(nil, "OVERLAY", nil, 2); c.tag:SetSize(14, 14); c.tag:SetPoint("TOPRIGHT", -2, -2); c.tag:SetColorTexture(0.75, 0.45, 1, 1)
  -- a prize this cat can't win yet: a lock and the level it needs
  c.lock = c:CreateTexture(nil, "OVERLAY", nil, 3); c.lock:SetSize(16, 16); c.lock:SetPoint("BOTTOMLEFT", 2, 2)
  c.lock:SetTexture(LOCK_TEX); c.lock:Hide()
  c.lvl = c:CreateFontString(nil, "OVERLAY", "NumberFontNormalSmall"); c.lvl:SetPoint("BOTTOMRIGHT", -3, 3); c.lvl:Hide()
  c.glow = c:CreateTexture(nil, "OVERLAY"); c.glow:SetPoint("TOPLEFT", -10, 10); c.glow:SetPoint("BOTTOMRIGHT", 10, -10)
  c.glow:SetTexture("Interface\\Buttons\\CheckButtonHilight"); c.glow:SetBlendMode("ADD"); c.glow:Hide()
  return c
end

local function setCard(c, it, rarity, locked, need)
  local col = TCF.RARITY[rarity] and TCF.RARITY[rarity].color or { 1, 1, 1 }
  c.edge:SetColorTexture(col[1], col[2], col[3], 1)
  c.icon:SetTexture(TCF.Icon(it.icon or "INV_Misc_QuestionMark"))
  c.tag:SetShown(it.q == nil)
  c.shine:SetShown((rarity or 0) >= 4)
  if locked then
    c.icon:SetVertexColor(0.75, 0.75, 0.75)
    c.lvl:SetText(tostring(need or 60))
    c.lock:Show(); c.lvl:Show()
  else
    c.icon:SetVertexColor(1, 1, 1)
    c.lock:Hide(); c.lvl:Hide()
  end
  c.glow:Hide()
end

local function createReel()
  local f = CreateFrame("Frame", "TapCatForeverReel", UIParent, TCF.UI.BT)
  f:SetSize(VISIBLE * STEP + 40, 170); f:SetPoint("CENTER", 0, 80)
  f:SetFrameStrata("FULLSCREEN_DIALOG"); f:SetToplevel(true); f:EnableMouse(true)
  if f.SetBackdrop then f:SetBackdrop(TCF.UI.BACKDROP_DIALOG) end
  f.title = TCF.UI.Text(f, "GameFontNormalLarge"); f.title:SetPoint("TOP", 0, -16)
  f.hint = TCF.UI.Text(f, "GameFontDisableSmall", "Click to skip"); f.hint:SetPoint("BOTTOM", 0, 10)
  local strip = CreateFrame("Frame", nil, f)
  strip:SetSize(VISIBLE * STEP, CARD + 8); strip:SetPoint("CENTER", 0, -6)
  if strip.SetClipsChildren then strip:SetClipsChildren(true) end
  f.strip = strip
  f.cards = {}
  for i = 1, COUNT do f.cards[i] = makeCard(strip) end
  -- the gold marker in the middle, with an arrow above and below it
  local mk = f:CreateTexture(nil, "OVERLAY"); mk:SetSize(4, CARD + 16); mk:SetPoint("CENTER", strip, "CENTER", 0, 0); mk:SetColorTexture(1, 0.82, 0.2, 0.9)
  local up = f:CreateTexture(nil, "OVERLAY"); up:SetSize(16, 16); up:SetPoint("CENTER", strip, "TOP", 0, 12)
  up:SetTexture("Interface\\Buttons\\UI-MicroStream-Yellow")
  local down = f:CreateTexture(nil, "OVERLAY"); down:SetSize(16, 16); down:SetPoint("CENTER", strip, "BOTTOM", 0, -12)
  down:SetTexture("Interface\\Buttons\\UI-MicroStream-Yellow"); down:SetTexCoord(0, 1, 1, 0)
  f.arrows = { up, down }
  f:SetScript("OnMouseUp", function(s) if s.t < DUR then s.t = DUR end end)
  f:SetScript("OnUpdate", function(s, e)
    s.t = s.t + e
    -- full speed for CRUISE seconds, then an ease-out brake that starts at that same speed and
    -- stops exactly on the prize at DUR
    local off
    if s.t <= CRUISE then off = s.vmax * s.t
    else
      local u = min(1, (s.t - CRUISE) / BRAKE)
      off = s.vmax * CRUISE + s.vmax * BRAKE / 3 * (1 - (1 - u) ^ 3)
    end
    local center = VISIBLE * STEP / 2
    for i, c in ipairs(s.cards) do
      local x = (i - 1) * STEP + GAP / 2 - off
      if x > -STEP and x < VISIBLE * STEP then
        c:ClearAllPoints()
        c:SetPoint("LEFT", s.strip, "LEFT", x, 0)
        c:Show()
      else
        c:Hide()
      end
    end
    -- a soft tick each time a new card passes the marker (not more often than TICK_GAP)
    local idx = floor((off + center) / STEP)
    if idx ~= s.lastIdx then
      s.lastIdx = idx
      if s.t < DUR and s.t - (s.lastTick or -1) >= TICK_GAP then s.lastTick = s.t; TCF:PlaySound("click") end
    end
    if s.t >= DUR and not s.landed then
      s.landed = true
      local col = TCF.RARITY[s.rarity] and TCF.RARITY[s.rarity].color or { 1, 1, 1 }
      s.cards[LAND].glow:SetVertexColor(col[1], col[2], col[3])
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
    -- the next chest waiting for its spin
    local nxt = table.remove(self.pending, 1)
    if nxt then TCF:PlayChestReel(nxt[1], nxt[2], nxt[3], nxt[4], nxt[5]) end
  end
  f.queue, f.pending = {}, {}
  f:Hide()
  return f
end

-- Play the reel for a chest reward, then show the usual loot box. level: the chest's level stamp
-- (default: the chest being opened, TCF:ChestLevel); the reel shows gear for that level.
function TCF:PlayChestReel(it, rarity, chestKey, args, level)
  local f = self.reel or createReel(); self.reel = f
  level = level or (self.ChestLevel and self:ChestLevel()) or (self:CD() and self:CD().level) or 1
  -- 1.5.3.4: a chest opened while the reel is still spinning gets its own spin right after this
  -- one (it used to skip its spin and only queue its loot box)
  if f:IsShown() then table.insert(f.pending, { it, rarity, chestKey, args, level }); return end
  local ch = TCF.CHEST_BY_KEY[chestKey]
  f.title:SetText("Opening " .. (ch and ch.name or "chest") .. "...")
  local deck
  if ch and ch.reel and self.ChestGearPool then deck = buildDeck(ch, it, rarity, level)
  else deck = randomDeck(ch, it, rarity, level) end
  f.deck = deck
  local needs = {}
  for i, c in ipairs(f.cards) do
    local d = deck[i]
    setCard(c, d.it, d.rarity, d.locked, d.need)
    if d.locked and d.need then needs[d.need] = true end
  end
  local hint = "Click to skip"
  if ch then
    local lockText = ""
    if needs[55] and needs[60] then lockText = " Locked prizes need level 55 or 60."
    elseif next(needs) then lockText = " Locked prizes need level " .. next(needs) .. "." end
    hint = "Gear for about level " .. level .. "." .. lockText .. " Click to skip"
  end
  f.hint:SetText(hint)
  local center = VISIBLE * STEP / 2
  f.endOff = (LAND - 1) * STEP + GAP / 2 + CARD / 2 - center + random(-16, 16)
  f.vmax = f.endOff / (CRUISE + BRAKE / 3)
  f.t, f.landed, f.lastIdx, f.lastTick, f.rarity = 0, false, nil, nil, rarity
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
