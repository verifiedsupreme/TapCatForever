-- TapCatForever: companion cats (1.7.4). Real WoW cat models (PlayerModel:SetDisplayInfo) that keep
-- your cat company. Bought with TapCoins (50,000 to 1,000,000) or earned by clearing big dungeons and raids
-- in Adventure. Owned companions are the account's: every class cat can pick any of them, its own one.
-- They show on the character panel; a very expensive upgrade (Companion Stroll) lets the companion walk
-- back and forth beside your cat on screen, on the other side from the party cats, and can be turned off.
local ADDON, TCF = ...

TCF.COMPANION_WALK_PRICE = 500000   -- (1.7.5) half a million (1,000,000 in 1.7.4)

-- key, name, display id (CreatureDisplayInfo), price (0: earned only), rarity (1-5), tier key whose clear
-- in Adventure earns it, a short line about it.
-- (1.7.5) Every display id here is in WoW: Forever's own game data (build 1.60.1, CreatureDisplayInfo):
-- 1.7.4's list took 37 from the current retail game, which the Forever client doesn't have (they showed
-- an empty box). tools/tests/test_companions.py checks the ids against tools/forever_cat_displays.txt.
-- (1.7.5) No companion comes free: it's bought, or (the dungeon ones) earned by clearing that dungeon or
-- raid in Adventure, on the clear itself. Progress made before doesn't hand them out.
local C = {
  -- house cats
  { "orange",      "Orange Tabby",            5554,    50000, 1, nil, "A classic Elwynn house cat." },
  { "silver",      "Silver Tabby",            5555,    50000, 1, nil, "Grey stripes and a judging look." },
  { "blacktabby",  "Maine Coon",              5448,    50000, 1, nil, "Big, fluffy and very gentle." },
  { "bombay",      "Bombay",                  5556,    60000, 1, nil, "Sleek, black and very smug." },
  { "siamese",     "Siamese",                 5585,    60000, 1, nil, "Loud opinions about everything." },
  { "cornishrex",  "Cornish Rex",             5586,    60000, 1, nil, "Curly coat, curious nose." },
  { "calico",      "Calico",                  11709,   75000, 1, nil, "Three colours of trouble." },
  { "snowcub",     "Snow Cub",                16942,  125000, 2, nil, "A Winterspring cub with icy whiskers." },
  -- tigers and lions
  { "stvtiger",    "Stranglethorn Tiger",     320,    150000, 2, nil, "Straight out of the jungle." },
  { "leopard",     "Jungle Leopard",          917,    150000, 2, nil, "Golden coat, quiet paws." },
  { "shadowstripe","Shadow-Striped Tiger",    321,    160000, 2, nil, "Black stripes on a dark coat." },
  { "savannah",    "Savannah Tiger",          1056,   160000, 2, nil, "Dusty brown, built for the plains." },
  { "lion",        "Pride Lion",              1973,   175000, 2, nil, "King of the Barrens." },
  { "dusktiger",   "Dusk Tiger",              3029,   180000, 2, nil, "The colour of the sky after sunset." },
  { "snowtiger",   "Snow Tiger",              748,    200000, 2, nil, "Pale stripes for the deep snow." },
  { "midnight",    "Midnight Tiger",          599,    200000, 2, nil, "Black as a moonless night." },
  -- sabers and big cats
  { "frostsaber",  "Striped Frostsaber",      6080,   200000, 3, nil, "A Night Elf classic." },
  { "nightsaber",  "Striped Nightsaber",      6448,   200000, 3, nil, "Born under Darnassus moons." },
  { "whitetiger",  "White Tiger",             616,    225000, 3, nil, "Rare, proud and hard to miss." },
  { "spotsaber",   "Spotted Frostsaber",      6444,   225000, 3, nil, "Every spot counted." },
  { "blacksaber",  "Black Nightsaber",        9991,   225000, 3, nil, "Shadow with teeth." },
  { "snowleopard", "Snow Leopard",            11448,  225000, 3, nil, "Black spots on a snowy coat." },
  { "shadowmane",  "Shadowmane Lion",         4424,   250000, 3, nil, "A lion with a dark mane." },
  { "tawnysaber",  "Tawny Saber",             6442,   250000, 3, nil, "Warm brown and always alert." },
  { "dawnsaber",   "Striped Dawnsaber",       4805,   250000, 3, nil, "Golden stripes at first light." },
  { "flaxensaber", "Flaxen Saber",            144509, 275000, 3, nil, "A coat the colour of summer wheat." },
  { "puresaber",   "Pure White Saber",        6079,   275000, 3, nil, "Not a single stripe." },
  { "wildfrost",   "Wild Frostsaber",         9956,   275000, 3, nil, "Never wore a saddle, never will." },
  { "wildnight",   "Wild Nightsaber",         139029, 275000, 3, nil, "Runs free in the night." },
  { "whitelion",   "White Lion",              10114,  300000, 3, nil, "Rare as a Barrens rain." },
  { "midprowler",  "Midnight Prowler",        140639, 300000, 3, nil, "A druid's dark blue cat form." },
  { "snowprowler", "Snow Prowler",            140640, 300000, 3, nil, "A druid's white cat form." },
  { "vioprowler",  "Violet Prowler",          140641, 325000, 4, nil, "A druid's violet cat form." },
  { "twiprowler",  "Twilight Prowler",        140642, 325000, 4, nil, "A druid's purple cat form." },
  { "icetiger",    "Ice Tiger",               9949,   350000, 4, nil, "Frost in its fur and its stare." },
  { "goldsaber",   "Golden Sabercat",         9714,   350000, 4, nil, "Shines like a pile of gold." },
  { "winterspring","Winterspring Frostsaber", 10426,  400000, 4, nil, "The pride of Winterspring." },
  { "aquasaber",   "Aqua Frostsaber",         10054,  400000, 4, nil, "Blue as a mountain lake." },
  { "lavsaber",    "Wild Lavender Saber",     9954,   400000, 4, nil, "Soft purple, sharp claws." },
  { "diamondtiger","Diamond Tiger",           146848, 450000, 4, nil, "Glitters with every step." },
  { "ironpanther", "Ironclad Panther",        137311, 450000, 4, nil, "A panther in heavy iron armor." },
  { "goldwar",     "Golden War Saber",        14329,  500000, 4, nil, "Armored for battle, eyes like embers." },
  { "whitewar",    "White War Saber",         14331,  500000, 4, nil, "Armored for battle, eyes glowing green." },
  -- Skyborne cats, from WoW: Forever's own Skyborne
  { "skygrey",     "Skyborne Grey Cat",       143623, 450000, 4, nil, "A cat of the Skyborne, grey as storm clouds." },
  { "skyblue",     "Skyborne Blue Cat",       143624, 450000, 4, nil, "A cat of the Skyborne, blue as the open sky." },
  { "skygreen",    "Skyborne Green Cat",      143625, 450000, 4, nil, "A cat of the Skyborne, green as spring leaves." },
  { "skywhite",    "Skyborne White Cat",      143626, 500000, 4, nil, "A cat of the Skyborne, white as high clouds." },
  { "skyrider",    "Skyborne Riding Cat",     146769, 600000, 5, nil, "Saddled and ready to fly the Skyborne way." },
  -- the rarest
  { "flamecat",    "Flamecat",                121996, 650000, 5, nil, "A cat made of living flame." },
  { "spectralcat", "Spectral Cat",            138740, 800000, 5, nil, "A ghostly cat that shimmers in and out." },
  { "spectral",    "Armored Spectral Tiger",  124765, 1000000, 5, nil, "The legend everyone wants." },
  -- earned by clearing the dungeon or raid in Adventure
  { "alleycat",    "Alley Cat",               9209,        0, 2, "dm",     "Snuck out of the Deadmines." },
  { "hallowcat",   "Shadowfang Prowler",      892,         0, 3, "sfk",    "Eyes glowing in Shadowfang Keep's halls." },
  { "crusaderlion","Lioness of Lordaeron",    1933,        0, 3, "sm",     "A proud lioness of the Scarlet Crusade." },
  { "atalai",      "Atal'ai Tiger",           9230,        0, 4, "st",     "Green as the Sunken Temple's swamp." },
  { "embercat",    "Ember Saber",             6443,        0, 4, "brd",    "Born in the forges of Blackrock Depths." },
  { "ghostkit",    "Ghostly Tiger",           9958,        0, 4, "scholo", "Haunts Scholomance's halls." },
  { "zulpanther",  "Swift Zulian Panther",    137225,      0, 5, "zg",     "Hakkar's own hunting cat." },
  { "firecat",     "Molten Firecat",          122028,      0, 5, "mc",     "Armored and burning, forged in Molten Core." },
  { "onyx",        "Onyx War Saber",          14330,       0, 5, "ony",    "Black armor and violet eyes, from Onyxia's lair." },
  { "chromatic",   "Chromatic War Saber",     14333,       0, 5, "bwl",    "Purple armor from Blackwing Lair." },
  { "bigglesworth","Mr. Bigglesworth",        9989,        0, 5, "naxx",   "Kel'Thuzad's beloved cat." },
}
-- (1.7.5) companions 1.7.4 had that WoW: Forever can't show (or, the White Kitten, that look the same
-- as another one): taken away, and what was paid comes back
TCF.COMPANION_REFUNDS = {
  pudge = 80000, shaggy = 80000, lynxkit = 100000, snowlynxkit = 100000, sandcub = 100000, sunkit = 125000,
  pinkcub = 150000, clockcub = 150000, bengal = 175000, panther = 250000, emberlynx = 250000, amanilynx = 300000,
  jadepanther = 350000, primal = 350000, mechtiger = 400000, shadowstalk = 450000, automaton = 500000,
  felkitten = 500000, felsaber = 750000, manasaber = 750000, spiritcat = 800000, dreamsaber = 850000,
  flamesaber = 900000, celestial = 1000000, whitekitten = 70000,
}

TCF.COMPANIONS, TCF.COMPANION_BY_KEY = {}, {}
for i, c in ipairs(C) do
  local e = { key = c[1], name = c[2], display = c[3], price = c[4], rarity = c[5], tier = c[6], desc = c[7], index = i }
  TCF.COMPANIONS[i] = e
  TCF.COMPANION_BY_KEY[e.key] = e
end

local function tierIndex(key)
  for i, t in ipairs(TCF.TIERS or {}) do if t.key == key then return i, t end end
end
function TCF.CompanionTier(c)
  if not c.tier then return nil end
  return tierIndex(c.tier)
end

-- account-wide state: owned companions, the stroll upgrade, and models this game can't load
function TCF:CompanionState()
  local db = self.db
  local s = db.companions
  if type(s) ~= "table" then s = {}; db.companions = s end
  s.owned = type(s.owned) == "table" and s.owned or {}
  -- (1.7.5) no companion without buying or really earning it. 1.7.4 handed the dungeon ones out for
  -- progress made before (at login), so those go back: clearing the dungeon again earns them. Ones
  -- this game can't show are taken away and refunded.
  if not s.v175 then
    s.v175 = true
    local refund, took = 0, 0
    for key in pairs(s.owned) do
      local c = TCF.COMPANION_BY_KEY[key]
      if not c then
        refund = refund + (TCF.COMPANION_REFUNDS[key] or 0)
        s.owned[key] = nil
      elseif c.tier then
        s.owned[key] = nil; took = took + 1
      end
    end
    if refund > 0 then db.coins = (db.coins or 0) + refund end
    if refund > 0 or took > 0 then
      local msg = {}
      if took > 0 then msg[#msg + 1] = "dungeon companions now join you only when you clear their dungeon in Adventure, so clear it again to get yours back" end
      if refund > 0 then msg[#msg + 1] = string.format("companions this game can't show were removed and you got your %s TapCoins back", TCF.Commas(refund)) end
      local text = "Companion cats: " .. table.concat(msg, "; ") .. "."
      if C_Timer and C_Timer.After then C_Timer.After(6, function() TCF:Print(text, true) end) else TCF:Print(text, true) end
    end
  end
  -- models this game couldn't load: for this session only (never saved, so a slow load can't hide a cat for good)
  s.missing = nil
  TCF.companionMissing = TCF.companionMissing or {}
  return s
end

function TCF:CompanionOwned(key) return self:CompanionState().owned[key] and true or false end
function TCF:CompanionMissing(key) return TCF.companionMissing and TCF.companionMissing[key] and true or false end

-- the companion this class's cat has chosen (nil: none)
function TCF:Companion(class)
  local cd = self:CD(class)
  local key = cd and cd.companion
  if key and TCF.COMPANION_BY_KEY[key] and self:CompanionOwned(key) then return TCF.COMPANION_BY_KEY[key] end
  return nil
end

function TCF:CompanionNotify()
  if self.CompanionRefresh then self:CompanionRefresh() end
  if self.MarkDirty then self:MarkDirty() end
  if self.RefreshAll then self:RefreshAll() end
end

function TCF:SetCompanion(key, class)
  local cd = self:CD(class)
  if not cd then return false end
  if key ~= nil and not (TCF.COMPANION_BY_KEY[key] and self:CompanionOwned(key)) then return false end
  cd.companion = key
  self:CompanionNotify()
  return true
end

-- why a companion can't be bought now (nil: it can)
function TCF:CompanionBuyProblem(key)
  local c = TCF.COMPANION_BY_KEY[key]
  if not c then return "Unknown companion." end
  if self:CompanionOwned(key) then return "You already have " .. c.name .. "." end
  if c.price <= 0 then
    local _, t = TCF.CompanionTier(c)
    return string.format("Earned by clearing %s in Adventure.", t and t.name or "a dungeon")
  end
  if self:CompanionMissing(key) then return "This cat's model isn't in your game version." end
  if (self.db.coins or 0) < c.price then return string.format("%s costs %s TapCoins.", c.name, TCF.Commas(c.price)) end
  return nil
end

function TCF:BuyCompanion(key)
  local why = self:CompanionBuyProblem(key)
  if why then return false, why end
  local c = TCF.COMPANION_BY_KEY[key]
  if not self:SpendCoins(c.price) then return false, "Not enough TapCoins." end
  self:CompanionState().owned[key] = time and time() or true
  -- the cat you're playing takes it right away when it has none
  if not self:CD().companion then self:CD().companion = key end
  self:Print(string.format("New companion: |cffffd100%s|r. Every one of your cats can choose it.", c.name), true)
  if self.PlaySound then self:PlaySound("buy") end
  self:CompanionNotify()
  return true
end

-- the stroll upgrade: the companion walks beside your cat on screen
function TCF:CompanionWalkOwned() return self:CompanionState().walk and true or false end
function TCF:CompanionWalkOn()
  local s = self:CompanionState()
  return s.walk and s.walkShown ~= false and true or false
end
function TCF:BuyCompanionWalk()
  local s = self:CompanionState()
  if s.walk then return false, "You already have Companion Stroll." end
  if (self.db.coins or 0) < TCF.COMPANION_WALK_PRICE then
    return false, string.format("Companion Stroll costs %s TapCoins.", TCF.Commas(TCF.COMPANION_WALK_PRICE))
  end
  if not self:SpendCoins(TCF.COMPANION_WALK_PRICE) then return false, "Not enough TapCoins." end
  s.walk, s.walkShown = true, true
  self:Print("Companion Stroll: your companion now walks beside your cat. Turn it off any time in the companion window.", true)
  if self.PlaySound then self:PlaySound("buy") end
  self:CompanionNotify()
  return true
end
function TCF:SetCompanionWalkShown(on)
  local s = self:CompanionState()
  if not s.walk then return false end
  s.walkShown = on and true or false
  self:CompanionNotify()
  return true
end

-- (1.7.5) a clear in Adventure (the last stage of a dungeon or raid, a first clear, a re-clear or a farm
-- run): the companion of that dungeon joins you. This is the only way they're given (AdvPackCleared).
function TCF:CompanionEarnFromClear(tierIdx)
  local t = TCF.TIERS and TCF.TIERS[tierIdx]
  if not (self.db and t) then return end
  local s = self:CompanionState()
  for _, c in ipairs(TCF.COMPANIONS) do
    if c.tier == t.key and not s.owned[c.key] then
      s.owned[c.key] = time and time() or true
      self:Print(string.format("You cleared %s: |cffffd100%s|r joins you as a companion. Choose it on the character panel.", t.name, c.name), true)
      if self.PlaySound then self:PlaySound("ach") end
      self:CompanionNotify()
    end
  end
end

-- (1.7.4 gave dungeon companions for past progress here; 1.7.5 gives them only on a clear, above)
function TCF:CheckCompanionUnlocks() end

-- a model the game couldn't load (the walker and the window check 0.6 s after showing it)
function TCF:CompanionModelMissing(key)
  TCF.companionMissing = TCF.companionMissing or {}
  TCF.companionMissing[key] = true
end

-- the companions in the order the window lists them: owned first, then by price, earned ones last
function TCF:CompanionList()
  local list = {}
  for _, c in ipairs(TCF.COMPANIONS) do list[#list + 1] = c end
  local owned = self:CompanionState().owned
  table.sort(list, function(a, b)
    local oa, ob = owned[a.key] and 1 or 0, owned[b.key] and 1 or 0
    if oa ~= ob then return oa > ob end
    local ea, eb = a.price <= 0 and 1 or 0, b.price <= 0 and 1 or 0
    if ea ~= eb then return ea < eb end
    if a.price ~= b.price then return a.price < b.price end
    return a.index < b.index
  end)
  return list
end

function TCF:CompanionTooltip(tt, c)
  local col = TCF.RARITY and TCF.RARITY[c.rarity] and TCF.RARITY[c.rarity].color or { 1, 1, 1 }
  tt:AddLine(c.name, col[1], col[2], col[3])
  tt:AddLine("Companion cat", 1, 1, 1)
  if c.desc then tt:AddLine(c.desc, 0.8, 0.8, 0.8, true) end
  if self:CompanionOwned(c.key) then
    tt:AddLine("Owned: every one of your cats can choose it.", 0.4, 1, 0.4, true)
  elseif c.price > 0 then
    tt:AddLine(string.format("%s TapCoins", TCF.Commas(c.price)), 1, 0.65, 0.2)
  else
    local _, t = TCF.CompanionTier(c)
    tt:AddLine(string.format("Clear %s in Adventure to earn it.", t and t.name or "a dungeon"), 1, 0.82, 0, true)
  end
  if self:CompanionMissing(c.key) then tt:AddLine("This cat's model isn't in your game version.", 1, 0.3, 0.3, true) end
end
