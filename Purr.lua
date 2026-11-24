-- TapCatForever: Happy Purrs (1.6.6). Pet your cat (left-click it on your screen, or its picture in
-- the window) 100 times in a row and it purrs: +5% XP for an hour. While it purrs, 50 pets in a row
-- start the hour again. "In a row" means no pause longer than TCF.PURR.GAP seconds between pets.
-- Each class's cat purrs on its own (classData[class].purr), and its pet effects (Data.lua, slot "pet":
-- what floats up when you pet it, hearts until you pick another) come from consistency with that cat:
-- Happy Purrs on more days, and on more days in a row (TCF.PURR_UNLOCKS).
-- Kept out of the way: a tiny heart by the XP bar while it purrs, a line in the cat's tooltip, a heart
-- by the class name in the window (grey until it purrs), and a one-time hint over the cat picture.
local ADDON, TCF = ...
local floor, max = math.floor, math.max

TCF.PURR = { NAME = "Happy Purrs", NEED = 100, REFRESH = 50, GAP = 4, DUR = 3600, XP = 0.05 }
local P = TCF.PURR

-- pet effects: days with Happy Purrs (days), or days in a row (run)
TCF.PURR_UNLOCKS = {
  { id = "pet_paw", days = 1 },  { id = "pet_note", days = 3 },  { id = "pet_star", run = 3 },
  { id = "pet_bubble", days = 7 }, { id = "pet_leaf", run = 7 },  { id = "pet_sparkle", days = 14 },
  { id = "pet_snow", run = 14 },  { id = "pet_coin", days = 30 }, { id = "pet_rainbow", run = 30 },
  -- (1.6.7) the full-colour ones, from a second day to a whole year
  { id = "pet_yarn", days = 2 },      { id = "pet_fish", days = 5 },       { id = "pet_mouse", run = 5 },
  { id = "pet_fireball", days = 10 }, { id = "pet_lightning", run = 10 },  { id = "pet_catnip", days = 12 },
  { id = "pet_poison", days = 20 },   { id = "pet_butterfly", days = 25 }, { id = "pet_frost", run = 21 },
  { id = "pet_shadow", days = 40 },   { id = "pet_holy", run = 45 },       { id = "pet_felfire", days = 50 },
  { id = "pet_blood", days = 60 },    { id = "pet_arcane", days = 75 },    { id = "pet_ghost", days = 90 },
  { id = "pet_moon", run = 90 },      { id = "pet_crown", days = 180 },    { id = "pet_gem", days = 365 },
}

local streak, lastPet, streakClass = 0, -1e9, nil
local function now() return GetTime and GetTime() or 0 end

-- this cat's purr record: until (the real clock), days, last (YYYYMMDD), run, best
local function rec(self, class)
  local cd = self:CD(class)
  if not cd then return nil end
  if type(cd.purr) ~= "table" then cd.purr = { days = 0, run = 0, best = 0 } end
  return cd.purr
end
TCF.PurrRecord = rec

-- seconds of purring left for a cat (0 when it doesn't purr)
function TCF:PurrLeft(class)
  if not self.db then return 0 end
  local r = rec(self, class)
  local u = r and tonumber(r["until"])
  if not u then return 0 end
  local left = u - time()
  return left > 0 and left or 0
end
function TCF:PurrActive(class) return self:PurrLeft(class) > 0 end
-- the XP multiplier (Core.lua: taps and the cat's other XP)
function TCF:PurrMult(class) return self:PurrActive(class) and (1 + P.XP) or 1 end
-- pets in the current run (0 after a pause or a class change) and how many it needs
function TCF:PurrStreak()
  local cls = self.db and self.db.class
  local need = self:PurrActive() and P.REFRESH or P.NEED
  if now() - lastPet > P.GAP or streakClass ~= cls then return 0, need end
  return streak, need
end

local function refreshShown()
  if TCF.hud and TCF.hud.RefreshPurr then TCF.hud:RefreshPurr() end
  local win = TCF.window
  if win and win.RefreshPurr then win:RefreshPurr() end
end
TCF.PurrRefreshShown = refreshShown

local function dayKey(t) return date("%Y%m%d", t) end

-- a day with Happy Purrs for this cat: counts days and days in a row, then unlocks pet effects
local function countDay(self, r)
  local today = dayKey(time())
  if r.last == today then return end
  local yesterday = dayKey(time() - 86400)
  r.run = (r.last == yesterday) and ((r.run or 0) + 1) or 1
  r.days = (r.days or 0) + 1
  r.best = max(r.best or 0, r.run)
  r.last = today
  local owned = self.db.owned
  for _, u in ipairs(TCF.PURR_UNLOCKS) do
    local it = TCF.ITEMS[u.id]
    if it and not owned[u.id] and ((u.days and r.days >= u.days) or (u.run and r.best >= u.run)) then
      self:GrantItem(it, P.NAME)
    end
  end
end

-- one pet: every left-click on the cat
function TCF:PurrPet()
  if not self.db then return false end
  local t, cls = now(), self.db.class
  if t - lastPet > P.GAP or streakClass ~= cls then streak = 0 end
  lastPet, streakClass = t, cls
  streak = streak + 1
  local r = rec(self)
  if not r then return false end
  local was = self:PurrActive()
  local need = was and P.REFRESH or P.NEED
  if streak < need then return false end
  streak = 0
  r["until"] = time() + P.DUR
  self:MarkDirty()
  -- one small note on the cat (only with "Popups on cat" on), and nothing else
  if self.cat and self.cat.Celebrate then
    self.cat:Celebrate(was and "Purring for another hour" or "+5% XP for an hour", 1, 0.6, 0.8, P.NAME)
  end
  countDay(self, r)
  refreshShown()
  return true
end

-- "52 min" / "less than a minute"
function TCF.PurrTimeText(sec)
  local m = floor(sec / 60 + 0.5)
  if m < 1 then return "less than a minute" end
  if m >= 60 then return "1 hour" end
  return m .. " min"
end

-- how a pet effect is unlocked (Compendium "how to get it")
function TCF:PurrUnlockLine(it)
  for _, u in ipairs(TCF.PURR_UNLOCKS) do
    if u.id == it.id then
      if u.days then
        return u.days == 1 and "Give your cat Happy Purrs (pet it 100 times in a row)"
          or string.format("Give this cat Happy Purrs on %d different days", u.days)
      end
      return string.format("Give this cat Happy Purrs %d days in a row", u.run)
    end
  end
  return "Happy Purrs"
end

-- the tooltip lines, the same everywhere
function TCF:PurrTooltip(tt, full)
  local active = self:PurrActive()
  local n, need = self:PurrStreak()
  if active then
    tt:AddLine(string.format("%s: +5%% XP (%s left)", P.NAME, TCF.PurrTimeText(self:PurrLeft())), 1, 0.6, 0.8)
  elseif full then
    tt:AddLine(P.NAME, 1, 0.6, 0.8)
  end
  if full then
    tt:AddLine(string.format("Pet your cat %d times in a row and it purrs: +5%% XP for an hour. While it purrs, %d pets in a row start the hour again.", P.NEED, P.REFRESH), 1, 1, 1, true)
    tt:AddLine("Left-click your cat on your screen (or its picture here) to pet it. A short pause is fine, a long one starts the count again.", 0.8, 0.8, 0.8, true)
    local r = rec(self)
    if r and (r.days or 0) > 0 then
      tt:AddLine(string.format("Days with Happy Purrs: %d (best run %d in a row). New pet effects come with more days.", r.days, r.best or 0), 0.8, 0.8, 0.8, true)
    else
      tt:AddLine("Coming back on more days, and on days in a row, unlocks new pet effects for this cat.", 0.8, 0.8, 0.8, true)
    end
  end
  if n > 0 then tt:AddLine(string.format("Pets in a row: %d / %d", n, need), 1, 0.82, 0) end
end

-- test hooks
TCF.PurrTest = {
  reset = function() streak, lastPet, streakClass = 0, -1e9, nil end,
}
