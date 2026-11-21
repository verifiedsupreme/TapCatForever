-- TapCatForever: Fishing. A bobber mini-game: cast, wait, and click "Reel in"
-- the moment the bobber splashes. Better spots unlock with skill. A fishing buddy
-- catches fish for you (also offline). Rare catches include Mr. Pinchy (a wish)
-- and Messages in a Bottle (a chest).
local ADDON, TCF = ...

local floor, min, max, random = math.floor, math.min, math.max, math.random

-- fish: key, name, icon, sell gold
local FISH = {
  { "smallfish",  "Raw Brilliant Smallfish",     "INV_Misc_Fish_02", 2e3 },
  { "longjaw",    "Raw Longjaw Mud Snapper",     "INV_Misc_Fish_04", 4e3 },
  { "bristle",    "Raw Bristle Whisker Catfish", "INV_Misc_Fish_05", 2e4 },
  { "blackmouth", "Oily Blackmouth",             "INV_Misc_Fish_07", 3e4 },
  { "trout",      "Raw Mithril Head Trout",      "INV_Misc_Fish_08", 1.5e5 },
  { "rockscale",  "Raw Rockscale Cod",           "INV_Misc_Fish_16", 2e5 },
  { "nightfin",   "Raw Nightfin Snapper",        "INV_Misc_Fish_03", 1e6 },
  { "sunscale",   "Raw Sunscale Salmon",         "INV_Misc_Fish_20", 1.3e6 },
  { "eel",        "Stonescale Eel",              "INV_Misc_Fish_36", 6e6 },
  { "whitescale", "Raw Whitescale Salmon",       "INV_Misc_Fish_21", 7e6 },
  { "boot",       "Old Boot",                    "INV_Boots_02",     50 },
  { "pinchy",     "Mr. Pinchy",                  "INV_Misc_Fish_35", 1e7 },
}
for _, f in ipairs(FISH) do TCF.AddMat(f[1], f[2], f[3], f[4], "fishing") end

TCF.FISHING_SPOTS = {
  { key = "pond",     name = "Goldshire Pond",      skill = 1,   fish = { "smallfish", "longjaw" } },
  { key = "westfall", name = "Westfall Coast",      skill = 50,  fish = { "bristle", "blackmouth" } },
  { key = "stv",      name = "Stranglethorn Vale",  skill = 125, fish = { "trout", "rockscale" } },
  { key = "feralas",  name = "Feralas",             skill = 200, fish = { "nightfin", "sunscale" } },
  { key = "azshara",  name = "Azshara",             skill = 250, fish = { "eel", "whitescale" } },
}
TCF.BUDDY_LEVELS = {
  { name = "Fishing Buddy",        every = 120, cost = 2e6 },
  { name = "Seasoned Angler",      every = 90,  cost = 1.2e7 },
  { name = "Master Angler",        every = 60,  cost = 7e7 },
  { name = "Fishing Legend",       every = 45,  cost = 4e8 },
  { name = "Nat Pagle's Apprentice", every = 30, cost = 2.5e9 },
}

local function F(self)
  local s = TCF:ProfState()
  s.fish = s.fish or { spot = 1, buddy = 0, bp = 0 }
  return s.fish, s
end
TCF.FishState = F

function TCF:FishLuck() return self.FoodBuff and self:FoodBuff("fishing") or 1 end

-- Rare catch odds. The buddy fishes all day (and offline), so his rare odds are much
-- lower and food luck doesn't help him; luck only boosts your own Reel in catches.
TCF.FISH_ODDS = { pinchy = 0.004, treasure = 0.011, buddyPinchy = 0.0005, buddyTreasure = 0.0015 }
-- Mr. Pinchy's gold wish: this many seconds of your mines' output
TCF.PINCHY_GOLD_SECONDS = 600

-- a chest from fishing; with a bag (offline catch-up) it is collected quietly for one summary line
local function giveChest(self, key, source, bag)
  if bag then
    self.db.keys[key] = (self.db.keys[key] or 0) + 1
    bag[key] = (bag[key] or 0) + 1
    self:MarkDirty()
  else self:AwardChest(key, source) end
end

-- One catch at the current spot. Returns name, kind ("fish", "junk", "treasure", "pinchy")
function TCF:CatchFish(byBuddy, bag)
  local f, s = F(self)
  local spot = TCF.FISHING_SPOTS[f.spot]
  local odds, luck = TCF.FISH_ODDS, self:FishLuck()
  local pPinchy = byBuddy and odds.buddyPinchy or odds.pinchy * luck
  local pTreasure = byBuddy and odds.buddyTreasure or odds.treasure * luck
  local r = random()
  local key, kind
  if r < pPinchy then key, kind = "pinchy", "pinchy"
  elseif r < pPinchy + pTreasure then kind = "treasure"
  elseif r < 0.10 then key, kind = "boot", "junk"
  else key, kind = spot.fish[random(#spot.fish)], "fish" end
  if key then s.mats[key] = (s.mats[key] or 0) + 1 end
  self:ProfSkillUp("fishing", spot.skill)
  if kind == "treasure" then
    giveChest(self, "pouch", "Message in a Bottle", bag)
    return "Message in a Bottle", kind
  elseif kind == "pinchy" then
    -- Mr. Pinchy grants a wish
    local w, wish = random(3)
    -- the chest announces itself (or joins the offline summary), so it needs no wish line
    if w == 1 then giveChest(self, "strong", "Mr. Pinchy's wish", bag)
    elseif w == 2 then self:AddCoins(25); wish = "25 TapCoins"
    else
      -- gold based on what your gathering spots make, not on the gold you hold (that would snowball)
      local g = self:EarnGold(max(1e4, self:GatherIncome() * TCF.PINCHY_GOLD_SECONDS))
      wish = TCF.GoldStr(g) .. " Trade Gold"
    end
    if not byBuddy and wish then self:Print("You caught |cffa335eeMr. Pinchy|r. His wish gives you " .. wish .. ".", true) end
    return "Mr. Pinchy", kind
  end
  return TCF.MAT_BY_KEY[key].name, kind
end

function TCF:SetFishingSpot(i)
  local f = F(self)
  local spot = TCF.FISHING_SPOTS[i]
  if spot and self:ProfSkill("fishing") >= spot.skill then f.spot = i; return true end
end

function TCF:BuyBuddy()
  local f = F(self)
  local nextLvl = TCF.BUDDY_LEVELS[f.buddy + 1]
  if not nextLvl or not self:SpendGold(nextLvl.cost) then return false end
  f.buddy = f.buddy + 1
  self:MarkDirty()
  return true
end

---------------------------------------------------------------- the bobber mini-game (not saved)
-- states: idle -> waiting (bobber floats) -> bite (splash: click now) -> result
function TCF:FishCast()
  local run = self.fishRun or {}
  self.fishRun = run
  if run.state == "waiting" or run.state == "bite" then return end
  run.state, run.t, run.biteAt = "waiting", 0, 2 + random() * 5
  run.result = nil
end

function TCF:FishReel()
  local run = self.fishRun
  if not run then return end
  if run.state == "bite" then
    local name, kind = self:CatchFish(false)
    run.state, run.result, run.kind = "result", name, kind
    self.db.stats.fishCaught = (self.db.stats.fishCaught or 0) + 1
    self:MarkDirty()
  elseif run.state == "waiting" then
    run.state, run.result, run.kind = "result", "Too soon. You scared the fish away.", "miss"
  end
end

function TCF:FishUpdate(dt)
  local run = self.fishRun
  if not run or (run.state ~= "waiting" and run.state ~= "bite") then return end
  run.t = run.t + dt
  if run.state == "waiting" and run.t >= run.biteAt then
    run.state, run.biteT = "bite", 0
    self:PlaySound("click")
  elseif run.state == "bite" then
    run.biteT = run.biteT + dt
    if run.biteT > 1.4 then run.state, run.result, run.kind = "result", "It got away...", "miss" end
  end
end

local function advance(self, dt, offline)
  local f = F(self)
  if f.buddy > 0 then
    local every = TCF.BUDDY_LEVELS[f.buddy].every
    f.bp = (f.bp or 0) + dt
    local guard = 0
    local bag = offline and {} or nil
    while f.bp >= every and guard < 2000 do
      guard = guard + 1
      f.bp = f.bp - every
      self:CatchFish(true, bag)
    end
    -- offline catch-up: one line for every chest the buddy fished up
    if bag and next(bag) then
      local parts = {}
      for _, ch in ipairs(TCF.CHESTS) do
        if bag[ch.key] then parts[#parts + 1] = "|cff1eff00" .. ch.name .. "|r x" .. bag[ch.key] end
      end
      self:Print("While you were away your fishing buddy found " .. table.concat(parts, ", ") .. ". Open them from your Treasure Bag.")
    end
  end
  if not offline then self:FishUpdate(dt) end
end

table.insert(TCF.PROF_MODULES, { key = "fishing", advance = advance,
  reset = function(self, s) if s.fish then s.fish.buddy = 0; s.fish.bp = 0 end end })
