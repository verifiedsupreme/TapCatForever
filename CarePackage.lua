-- TapCatForever: a care package for players who were playing before this update (1.5.4).
-- Once per character: every class cat with some progress gets a plain white (Common) piece for
-- each empty gear slot it can use at its level, in that cat's gear bag (not equipped). Once per
-- account: a small TapCoin gift. One chat line, no pop-up. Brand-new characters and accounts
-- get nothing (Core.lua's InitDB says which saves existed: TCF.charExisted, TCF.saveExisted).
local ADDON, TCF = ...
local floor, min, max, random = math.floor, math.min, math.max, math.random

TCF.CARE_COINS = 150
local ARMOR_RANK = { cloth = 1, leather = 2, mail = 3, plate = 4 }
local CARE_SLOTS = { "HEAD", "NECK", "SHOULDER", "BACK", "CHEST", "WRIST", "WAIST", "HANDS", "LEGS", "FEET",
  "FINGER1", "FINGER2", "MAINHAND", "OFFHAND", "RANGED" }

-- has this class's cat ever been played on this character?
function TCF:CatHasProgress(class)
  local cd = self.db.classData[class]
  if type(cd) ~= "table" then return false end
  local adv = type(cd.adv) == "table" and cd.adv or {}
  return (cd.level or 1) > 1 or (cd.xp or 0) > 0 or (adv.kills or 0) > 0 or (adv.best or 0) > 0
end

-- A white piece for one slot at this level: the class can use it now, as close to the level as
-- there is, the heaviest armor the class wears, made for the class first. nil when there is none.
function TCF:CarePiece(class, level, slot, taken)
  level = min(60, max(1, floor(level or 1)))
  local best, bestKey
  for b = 0, floor(level / 5) do
    for _, it in ipairs(TCF.WORLD_POOL[b] or {}) do
      if it.q == 1 and (it.req or 0) <= level and not it.crafted and not it.retired and not taken[it.id]
        and self:GearUsable(it, class) then
        local fits = false
        for _, s in ipairs(self:GearTargetSlots(it, class)) do if s == slot then fits = true end end
        -- a two-hander needs the off hand empty: only offered for the main hand
        if fits and slot == "OFFHAND" and it.slot == "2H" then fits = false end
        if fits then
          -- within 10 levels of the cat first, then the heaviest armor, then the closest to the
          -- level, then made for the class, then the lowest id
          local req = it.req or 0
          local key = (req >= level - 10 and 1e6 or 0) + (ARMOR_RANK[it.sub] or 0) * 1e4 + req * 10 + (self:GearSuits(it, class) and 1 or 0)
          if not bestKey or key > bestKey or (key == bestKey and it.id < best.id) then best, bestKey = it, key end
        end
      end
    end
  end
  return best
end

-- the white pieces a cat would get: { item, ... } for its empty slots
function TCF:CarePieces(class)
  local cd = self.db.classData[class]
  local level = cd and cd.level or 1
  local empty = self:SmallFindNeed(class)
  local isEmpty = {}
  for _, s in ipairs(empty) do isEmpty[s] = true end
  local out, taken = {}, {}
  for _, s in ipairs(CARE_SLOTS) do
    -- a two-hander given for the main hand leaves no room for an off-hand piece
    local twoHand = out[#out] and out[#out].slot == "2H"
    if isEmpty[s] and not (s == "OFFHAND" and twoHand) then
      local it = self:CarePiece(class, level, s, taken)
      -- one copy of a ring or a one-hander per slot (a second ring is a different ring)
      if it then out[#out + 1] = it; taken[it.id] = true end
    end
  end
  return out
end

-- Runs once at login. Returns pieces given, TapCoins given.
function TCF:CarePackage()
  local db = self.db
  local char = self.charData
  if not db or not char then return 0, 0 end
  local pieces, coins, perCat = 0, 0, {}
  if not char.carePackage then
    char.carePackage = true
    if self.charExisted then
      for _, cl in ipairs(TCF.CLASSES) do
        if self:CatHasProgress(cl.key) then
          local bag = self:Bag(cl.key)
          local n = 0
          for _, it in ipairs(self:CarePieces(cl.key)) do
            bag[it.id] = (bag[it.id] or 0) + 1
            n = n + 1
          end
          if n > 0 then pieces = pieces + n; perCat[#perCat + 1] = cl.name .. " " .. n end
        end
      end
    end
  end
  if not db.careCoins then
    db.careCoins = true
    if self.saveExisted then
      coins = TCF.CARE_COINS
      self:AddCoins(coins)
    end
  end
  if pieces > 0 or coins > 0 then
    local parts = {}
    if coins > 0 then parts[#parts + 1] = coins .. " TapCoins" end
    if pieces > 0 then
      local one = #perCat == 1
      parts[#parts + 1] = string.format("%d plain white piece%s for your %s empty gear slots (%s), waiting in %s",
        pieces, pieces == 1 and "" or "s", one and "cat's" or "cats'", table.concat(perCat, ", "), one and "its gear bag" or "their gear bags")
    end
    self:Print("A care package for playing before this update: " .. table.concat(parts, ", and ") .. ".", true)
    self:MarkDirty()
  end
  return pieces, coins
end

local ev = CreateFrame("Frame")
ev:RegisterEvent("PLAYER_LOGIN")
ev:SetScript("OnEvent", function()
  if TCF.db then
    local ok, err = pcall(TCF.CarePackage, TCF)
    if not ok and geterrorhandler then geterrorhandler()(err) end
  end
end)
