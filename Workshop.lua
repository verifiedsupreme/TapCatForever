-- TapCatForever: Workshop (1.7.0). Reasons to work your gathering spots by hand, and helpers with a
-- name. For the three main professions (mining, skinning, cloth):
--   * Rare finds: a click by hand (never a helper) can find a rare material, better ones at later
--     spots: Black Diamond / Star Ruby / Blood of the Mountain, Warbear Leather / Black Dragonscale /
--     Pristine Hide of the Beast, Essence of Undeath / Demonic Rune / Righteous Orb. They go into the
--     long-chase profession sets (ProfSets.lua) and the guild's work orders (ProfDepth.lua).
--   * Glints: while the spots page is open, a spot sometimes sparkles for a moment. A click by hand
--     on it in time pays 5 times as much and adds to a combo; the combo makes rare finds likelier.
--     Missing a glint ends the combo.
--   * Spot events, every few minutes while the page is open: a stash to grab (click the spot fast),
--     a rich spot (clicks by hand there pay 3 times as much for 30 seconds) or a patrol to hide from
--     (no clicks for a few seconds: helpers work twice as fast for a minute).
--   * Named helpers: every foreman, trapper or scavenger has a name and a trait, and brings more
--     goods (ore, leather, cloth) as it works, up to level 20. Gold stays the same, so the pace of
--     the later professions doesn't change.
-- Glints and events only happen for the cat you play, on its own family, while you look at the page.
local ADDON, TCF = ...
local floor, min, max, random = math.floor, math.min, math.max, math.random

---------------------------------------------------------------- rare finds
-- spot = the first spot (1-9) that can give it; w = weight among the finds a spot can give
TCF.RARE_FINDS = {
  mining = {
    { key = "blackdiamond",  name = "Black Diamond",              icon = "INV_Misc_Gem_06",          spot = 2, w = 60 },
    { key = "starruby",      name = "Star Ruby",                  icon = "INV_Misc_Gem_Ruby_02",     spot = 4, w = 30 },
    { key = "bloodmountain", name = "Blood of the Mountain",      icon = "INV_Misc_Gem_Bloodstone_01", spot = 7, w = 10 },
  },
  skinning = {
    { key = "warbear",       name = "Warbear Leather",            icon = "INV_Misc_LeatherScrap_06", spot = 2, w = 60 },
    { key = "blackscale",    name = "Black Dragonscale",          icon = "INV_Misc_MonsterScales_10", spot = 4, w = 30 },
    { key = "pristinehide",  name = "Pristine Hide of the Beast", icon = "INV_Misc_Pelt_Bear_Ruin_02", spot = 7, w = 10 },
  },
  cloth = {
    { key = "essundeath",    name = "Essence of Undeath",         icon = "INV_Misc_Dust_02",         spot = 2, w = 60 },
    { key = "demonicrune",   name = "Demonic Rune",               icon = "INV_Misc_Rune_04",         spot = 4, w = 30 },
    { key = "righteousorb",  name = "Righteous Orb",              icon = "INV_Misc_Gem_Pearl_04",    spot = 7, w = 10 },
  },
}
TCF.RARE_FIND_CHANCE = 1 / 250     -- per click by hand on a spot that can give one
TCF.RARE_FIND_BY_KEY = {}
for fam, list in pairs(TCF.RARE_FINDS) do
  for _, r in ipairs(list) do
    r.fam = fam
    TCF.RARE_FIND_BY_KEY[r.key] = r
    TCF.AddMat(r.key, r.name, r.icon, 0, fam)
  end
end
-- the finds spot i of a family can give
function TCF.RareFindsAt(fam, i)
  local out = {}
  for _, r in ipairs(TCF.RARE_FINDS[fam] or {}) do if i >= r.spot then out[#out + 1] = r end end
  return out
end

local function S(self) return self:ProfState() end
local function W(self)
  local s = S(self)
  if type(s.ws) ~= "table" then s.ws = { combo = 0, best = 0, found = 0 } end
  return s.ws, s
end
TCF.WorkshopState = W
local function now() return GetTime and GetTime() or 0 end
local function perk(self, key) return self.RenownPerk and self:RenownPerk(key) or 0 end
-- playing this family on the cat you play (not a catch-up of another cat)
local function live(self, f)
  return self.db and not self.tradeQuiet and not (self.tradeClass and self.tradeClass ~= self.db.class) and f == self:MainProf()
end

-- the chance a click by hand on spot i finds something rare (combo and Keen Eye count)
function TCF:RareFindChance(f, i)
  if #TCF.RareFindsAt(f, i) == 0 then return 0 end
  local ws = W(self)
  local combo = min(3, 1 + 0.25 * (ws.combo or 0))
  return TCF.RARE_FIND_CHANCE * combo * (1 + 0.2 * perk(self, "keeneye"))
end

local function rollFind(self, f, i, force)
  local list = TCF.RareFindsAt(f, i)
  if #list == 0 then return nil end
  if not force and random() >= self:RareFindChance(f, i) then return nil end
  local total = 0
  for _, r in ipairs(list) do total = total + r.w end
  local x = random() * total
  for _, r in ipairs(list) do
    x = x - r.w
    if x <= 0 then return r end
  end
  return list[#list]
end

local function giveFind(self, r)
  local ws, s = W(self)
  s.mats[r.key] = (s.mats[r.key] or 0) + 1
  ws.found = (ws.found or 0) + 1
  self.lastRareFind = { key = r.key, at = now() }
  self:Print(string.format("Rare find: |cffa335ee%s|r. It goes into your profession's best recipes and work orders.", r.name), true)
  self:PlaySound("rare")
end

---------------------------------------------------------------- glints and spot events
TCF.GLINT_TIME, TCF.GLINT_GAP = 2.5, { 10, 25 }     -- seconds a glint lasts; seconds between glints
TCF.GLINT_MULT, TCF.RICH_MULT = 5, 3
TCF.EVENT_GAP = { 120, 240 }                          -- seconds between spot events
TCF.STASH_CLICKS, TCF.STASH_TIME, TCF.RICH_TIME, TCF.HIDE_TIME, TCF.HIDE_BUFF = 10, 8, 30, 6, 60

local glint, event, nextGlint, nextEvent, buffUntil = nil, nil, nil, nil, {}
TCF.WorkshopTest = { reset = function() glint, event, nextGlint, nextEvent, buffUntil = nil, nil, nil, nil, {} end,
  setGlint = function(g) glint = g end, setEvent = function(e) event = e end }

-- the event texts, by family: stash, rich, patrol
local EVENT_TEXT = {
  mining = { stash = "A kobold is guarding a stash of ore at %s. Click it %d times in %d seconds to chase it off.",
             rich = "A rich vein opened up at %s: clicks by hand there pay 3 times as much for %d seconds.",
             patrol = "A Dark Iron patrol is coming. Don't click anything for %d seconds and your %s work twice as fast for a minute." },
  skinning = { stash = "A poacher dropped a bundle of hides at %s. Click it %d times in %d seconds before he comes back.",
               rich = "A rare beast was spotted at %s: clicks by hand there pay 3 times as much for %d seconds.",
               patrol = "A pack of hungry wolves is coming. Don't click anything for %d seconds and your %s work twice as fast for a minute." },
  cloth = { stash = "A Defias thief is sitting on a chest of stolen cloth at %s. Click it %d times in %d seconds to shoo him away.",
            rich = "A merchant's wagon tipped over at %s: clicks by hand there pay 3 times as much for %d seconds.",
            patrol = "A town guard patrol is coming. Don't click anything for %d seconds and your %s work twice as fast for a minute." },
}
TCF.WORKSHOP_EVENT_TEXT = EVENT_TEXT

-- the open spots of the family you play, from the ones shown (visible: list of spot numbers)
local function openSpots(self, f, visible)
  local s = S(self)
  local out = {}
  for _, i in ipairs(visible or {}) do
    local st = s.ops[f] and s.ops[f][i]
    if st and (i == 1 or st.n > 0) and st.n > 0 then out[#out + 1] = i end
  end
  return out
end

-- called by the spots page while it is shown (visible: the spot numbers on screen)
function TCF:WorkshopTick(visible, t)
  local f = self:MainProf()
  if not live(self, f) then return end
  t = t or now()
  local ws = W(self)
  -- glints
  if glint and t >= glint.ends then
    if (ws.combo or 0) > 0 then self:Print(string.format("Your combo ended at %d.", ws.combo)) end
    ws.combo, glint = 0, nil
  end
  if not glint then
    nextGlint = nextGlint or (t + TCF.GLINT_GAP[1])
    if t >= nextGlint then
      local spots = openSpots(self, f, visible)
      if #spots > 0 then glint = { fam = f, i = spots[random(#spots)], ends = t + TCF.GLINT_TIME } end
      local gap = TCF.GLINT_GAP[1] + random() * (TCF.GLINT_GAP[2] - TCF.GLINT_GAP[1])
      nextGlint = t + gap / (1 + 0.25 * perk(self, "glints"))
    end
  end
  -- events
  if event and t >= event.ends then
    if event.kind == "stash" then self:Print("The stash got away this time.")
    elseif event.kind == "patrol" then
      local fam = TCF.FAMILIES[f]
      buffUntil[f] = t + TCF.HIDE_BUFF
      self:Print(string.format("You stayed hidden. Your %s work twice as fast for a minute.", fam.hirePlural:lower()), true)
      self:PlaySound("click")
    end
    event = nil
    nextEvent = t + TCF.EVENT_GAP[1] + random() * (TCF.EVENT_GAP[2] - TCF.EVENT_GAP[1])
  end
  if not event then
    nextEvent = nextEvent or (t + TCF.EVENT_GAP[1])
    if t >= nextEvent then
      local spots = openSpots(self, f, visible)
      if #spots > 0 then
        local kinds = { "stash", "rich", "patrol" }
        local kind = kinds[random(3)]
        local i = spots[random(#spots)]
        local fam = TCF.FAMILIES[f]
        local spot = fam.ops[i][1]
        local txt
        if kind == "stash" then
          event = { kind = kind, fam = f, i = i, ends = t + TCF.STASH_TIME, clicks = 0 }
          txt = EVENT_TEXT[f].stash:format(spot, TCF.STASH_CLICKS, TCF.STASH_TIME)
        elseif kind == "rich" then
          event = { kind = kind, fam = f, i = i, ends = t + TCF.RICH_TIME }
          txt = EVENT_TEXT[f].rich:format(spot, TCF.RICH_TIME)
        else
          event = { kind = kind, fam = f, ends = t + TCF.HIDE_TIME }
          txt = EVENT_TEXT[f].patrol:format(TCF.HIDE_TIME, fam.hirePlural:lower())
        end
        event.text = txt
        self:Print(txt, true)
        self:PlaySound("click")
      else
        nextEvent = t + 30
      end
    end
  end
end

function TCF:WorkshopGlint() return glint end
function TCF:WorkshopEvent() return event end
function TCF:WorkshopCombo() return (W(self).combo or 0) end

-- any click on a spot row (before the cooldown check): stash clicks count here, and a patrol sees you
function TCF:WorkshopRowClick(f, i, t)
  if not live(self, f) or not event then return end
  t = t or now()
  if event.kind == "stash" and event.i == i and t < event.ends then
    event.clicks = event.clicks + 1
    if event.clicks >= TCF.STASH_CLICKS then
      -- the stash: two minutes of this family's spots' income, and a good chance of a rare find
      local inc = self.GatherIncome and self:GatherIncome(f) or 0
      local gold = self:EarnGold(max(inc * 120, self:ToolGold(f, i) * 20))
      local s = S(self)
      local op = TCF.FAMILIES[f].ops[i]
      local mats = 5 + floor(self:OpMatsPerCycle(f, i) * 10)
      s.mats[op[2]] = (s.mats[op[2]] or 0) + mats
      self:Print(string.format("You grabbed the stash: %s and %d %s.", TCF.GoldStr(gold), mats, op[3]), true)
      if random() < 0.5 then local r = rollFind(self, f, i, true); if r then giveFind(self, r) end end
      self:PlaySound("loot")
      event = nil
      nextEvent = t + TCF.EVENT_GAP[1] + random() * (TCF.EVENT_GAP[2] - TCF.EVENT_GAP[1])
    end
  elseif event.kind == "patrol" and t < event.ends then
    self:Print("The patrol spotted you. Maybe next time.")
    event = nil
    nextEvent = t + TCF.EVENT_GAP[1] + random() * (TCF.EVENT_GAP[2] - TCF.EVENT_GAP[1])
  end
end

-- a successful click by hand (Professions.lua TCF:GatherClick): glint, rich spot, Sharp Tools perk,
-- and the rare find roll. Adds the extra itself; returns the extra gold and material for the line.
function TCF:WorkshopClick(f, i, gold, got)
  if not live(self, f) then return 0, 0 end
  local t = now()
  local ws, s = W(self)
  local mult = 1 + 0.25 * perk(self, "sharptools")
  if glint and glint.fam == f and glint.i == i and t < glint.ends then
    mult = mult * TCF.GLINT_MULT
    ws.combo = (ws.combo or 0) + 1
    ws.best = max(ws.best or 0, ws.combo)
    glint = nil
    self.lastGlintHit = t
    self:PlaySound("loot")
  end
  if event and event.kind == "rich" and event.i == i and t < event.ends then mult = mult * TCF.RICH_MULT end
  local g2, m2 = 0, 0
  if mult > 1 then
    g2 = self:EarnGold(gold * (mult - 1))
    m2 = floor(got * (mult - 1) + random())
    local op = TCF.FAMILIES[f].ops[i]
    if m2 > 0 then s.mats[op[2]] = (s.mats[op[2]] or 0) + m2 end
  end
  local r = rollFind(self, f, i)
  if r then giveFind(self, r) end
  return g2, m2
end

---------------------------------------------------------------- named helpers
local NAMES = {
  mining = { "Gorm", "Brannik", "Dagna", "Thurg", "Kragg", "Bolli", "Hilda", "Durgan", "Muradin Jr.", "Grimble", "Tova", "Rokk" },
  skinning = { "Tavi", "Ryn", "Kesh", "Mara", "Grath", "Oona", "Sable", "Wren", "Tarok", "Fen", "Lysa", "Bruk" },
  cloth = { "Pip", "Wendle", "Marla", "Fizzik", "Odo", "Nessa", "Quill", "Bertie", "Lark", "Tilly", "Corwin", "Mabel" },
}
-- trait: name, text, and what it does (goods: more ore, leather or cloth; learning: levels faster)
TCF.HELPER_TRAITS = {
  { key = "strong", name = "Strong",      text = "brings 8% more goods" },
  { key = "lucky",  name = "Lucky",       text = "brings 10% more goods" },
  { key = "eager",  name = "Eager",       text = "learns twice as fast" },
  { key = "steady", name = "Steady",      text = "brings 5% more goods and learns a bit faster" },
}
local TRAIT_BY_KEY = {}
for _, tr in ipairs(TCF.HELPER_TRAITS) do TRAIT_BY_KEY[tr.key] = tr end
TCF.HELPER_MAX_LEVEL = 20
-- cycles worked to reach a level: level L needs 25 * L^2 cycles (a few hours at the first spots)
local function levelOf(xp) return min(TCF.HELPER_MAX_LEVEL, 1 + floor(math.sqrt((xp or 0) / 25))) end

-- give a spot's helper a name and a trait (once)
function TCF:HelperHired(f, i)
  local st = S(self).ops[f] and S(self).ops[f][i]
  if not st or not st.mgr then return end
  if not st.hname then
    local list = NAMES[f] or NAMES.cloth
    st.hname = list[random(#list)]
    st.htrait = TCF.HELPER_TRAITS[random(#TCF.HELPER_TRAITS)].key
    st.hxp = st.hxp or 0
  end
end
-- name, level, trait of a spot's helper (nil without one)
function TCF:HelperInfo(f, i)
  local st = S(self).ops[f] and S(self).ops[f][i]
  if not st or not st.mgr then return nil end
  if not st.hname then self:HelperHired(f, i) end
  return { name = st.hname, level = levelOf(st.hxp), trait = TRAIT_BY_KEY[st.htrait] or TCF.HELPER_TRAITS[1], xp = st.hxp or 0,
           next = 25 * levelOf(st.hxp) ^ 2 }
end
-- a helper worked some cycles (Professions.lua produce)
function TCF:HelperWorked(f, i, cycles)
  local st = S(self).ops[f] and S(self).ops[f][i]
  if not st or not st.mgr then return end
  if not st.hname then self:HelperHired(f, i) end
  local gain = cycles
  if st.htrait == "eager" then gain = gain * 2 elseif st.htrait == "steady" then gain = gain * 1.3 end
  local before = levelOf(st.hxp)
  st.hxp = (st.hxp or 0) + gain
  local after = levelOf(st.hxp)
  if after > before and not self.tradeQuiet and not (self.tradeClass and self.tradeClass ~= self.db.class) then
    self:Print(string.format("%s, your %s at %s, reached level %d.", st.hname, TCF.FAMILIES[f].hire:lower(), TCF.FAMILIES[f].ops[i][1], after))
  end
end
-- goods multiplier of a spot's helper: 2% a level, its trait, and the Busy Hands perk
function TCF:HelperGoodsMult(f, i)
  local st = S(self).ops[f] and S(self).ops[f][i]
  if not (st and st.mgr) then return 1 end
  local m = 1 + 0.02 * (levelOf(st.hxp) - 1)
  if st.htrait == "lucky" then m = m * 1.1 elseif st.htrait == "strong" then m = m * 1.08 elseif st.htrait == "steady" then m = m * 1.05 end
  return m * (1 + 0.1 * perk(self, "helpers"))
end

-- speed of a spot: twice as fast for a minute after hiding from a patrol
function TCF:WorkshopSpeedMult(f, i)
  if buffUntil[f] and now() < buffUntil[f] then return 2 end
  return 1
end
function TCF:WorkshopBuffLeft(f) return buffUntil[f] and max(0, buffUntil[f] - now()) or 0 end
