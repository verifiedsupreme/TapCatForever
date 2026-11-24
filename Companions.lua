-- TapCatForever: companion cats (1.8.0). Real WoW cat models (PlayerModel:SetDisplayInfo) that keep
-- your cat company. Bought with TapCoins (50,000 to 1,000,000) or earned by clearing big dungeons and raids
-- in Adventure. Owned companions are the account's: every class cat can pick any of them, its own one.
-- They show on the character panel; a very expensive upgrade (Companion Stroll) lets the companion walk
-- back and forth beside your cat on screen, on the other side from the party cats, and can be turned off.
local ADDON, TCF = ...

TCF.COMPANION_WALK_PRICE = 1000000

-- key, name, display id (CreatureDisplayInfo), price (0: earned only), rarity (1-5), tier key that
-- unlocks it when cleared (Adventure), a short line about it
local C = {
  -- house cats
  { "orange",      "Orange Tabby",            5554,   50000, 1, nil, "A classic Elwynn house cat." },
  { "silver",      "Silver Tabby",            5555,   50000, 1, nil, "Grey stripes and a judging look." },
  { "blacktabby",  "Black Tabby",             5448,   50000, 1, nil, "Dark stripes, warm heart." },
  { "bombay",      "Bombay",                  5556,   60000, 1, nil, "Sleek, black and very smug." },
  { "siamese",     "Siamese",                 5585,   60000, 1, nil, "Loud opinions about everything." },
  { "cornishrex",  "Cornish Rex",             5586,   60000, 1, nil, "Curly coat, curious nose." },
  { "whitekitten", "White Kitten",            9990,   70000, 1, nil, "Small, white and always underfoot." },
  { "calico",      "Calico",                  11709,  75000, 1, nil, "Three colours of trouble." },
  { "pudge",       "Pudge",                   74797,  80000, 2, nil, "Has never missed a meal." },
  { "shaggy",      "Shaggy Tom",              74798,  80000, 2, nil, "A long coat and a longer nap." },
  -- kittens and cubs
  { "lynxkit",     "Lynx Kitten",             116278, 100000, 2, nil, "Big ears, bigger pounce." },
  { "snowlynxkit", "Snowy Lynx Kitten",       116279, 100000, 2, nil, "Soft as fresh snow." },
  { "sandcub",     "Sand Cub",                31121,  100000, 2, nil, "Found napping in Tanaris." },
  { "snowcub",     "Snow Cub",                16942,  125000, 2, nil, "A Winterspring cub with icy whiskers." },
  { "sunkit",      "Sunfire Kitten",          138230, 125000, 2, nil, "An Eversong lynx kitten, warm as a hearth." },
  { "pinkcub",     "Bubblegum Cub",           64588,  150000, 3, nil, "Unbearably pink." },
  { "clockcub",    "Clockwork Cub",           46947,  150000, 3, nil, "Wind it up and let it roam." },
  -- big cats
  { "stvtiger",    "Stranglethorn Tiger",     320,    150000, 2, nil, "Straight out of the jungle." },
  { "leopard",     "Jungle Leopard",          917,    150000, 2, nil, "Spots for days." },
  { "bengal",      "Bengal Tiger",            39577,  175000, 2, nil, "Orange, black and proud." },
  { "lion",        "Pride Lion",              1973,   175000, 2, nil, "King of the Barrens." },
  { "frostsaber",  "Striped Frostsaber",      6080,   200000, 3, nil, "A Night Elf classic." },
  { "nightsaber",  "Striped Nightsaber",      6448,   200000, 3, nil, "Born under Darnassus moons." },
  { "spotsaber",   "Spotted Frostsaber",      6444,   225000, 3, nil, "Every spot counted." },
  { "blacksaber",  "Black Nightsaber",        9991,   225000, 3, nil, "Shadow with teeth." },
  { "shadowmane",  "Shadowmane Lion",         4424,   250000, 3, nil, "A lion with a dark mane." },
  { "panther",     "Shadow Panther",          19607,  250000, 3, nil, "Red eyes in the dark." },
  { "emberlynx",   "Ember Lynx",              117860, 250000, 3, nil, "A red Arathi lynx." },
  { "amanilynx",   "Amani Lynx",              124943, 300000, 3, nil, "From the Zul'Aman war bands." },
  { "whitelion",   "White Lion",              10114,  300000, 3, nil, "Rare as a Barrens rain." },
  { "jadepanther", "Jade Panther",            39179,  350000, 4, nil, "Green as a carved jade idol." },
  { "primal",      "Primal Sabertooth",       105442, 350000, 4, nil, "Old as the ice." },
  { "mechtiger",   "Mechanical Tiger",        74804,  400000, 4, nil, "Gnomish engineering, mostly safe." },
  { "winterspring","Winterspring Frostsaber", 10426,  400000, 4, nil, "The pride of Winterspring." },
  { "shadowstalk", "Shadowstalker Panther",   76587,  450000, 4, nil, "Crystals grow along its back." },
  { "automaton",   "Golden Automaton",        92661,  500000, 4, nil, "A gilded lion of gears." },
  -- glowing, fel and spectral cats
  { "felkitten",   "Fel Kitten",              73353,  500000, 5, nil, "Green fire and a tiny attitude." },
  { "flamecat",    "Flamecat",                38150,  650000, 5, nil, "A cat made of living flame." },
  { "felsaber",    "Felsaber",                67575,  750000, 5, nil, "Fel-touched and unstoppable." },
  { "manasaber",   "Arcanist's Manasaber",    81468,  750000, 5, nil, "Glowing with arcane power." },
  { "spiritcat",   "Spirit Cat",              74794,  800000, 5, nil, "A cat of pure starlight." },
  { "dreamsaber",  "Dreamsaber",              112561, 850000, 5, nil, "Walks out of the Emerald Dream." },
  { "flamesaber",  "Primal Flamesaber",       74298,  900000, 5, nil, "Its fur is fire." },
  { "spectral",    "Spectral Tiger",          21973, 1000000, 5, nil, "The legend everyone wants." },
  { "celestial",   "Celestial Cat",           120475, 1000000, 5, nil, "Stars in its eyes, and its fur." },
  -- earned in Adventure: clear the dungeon or raid
  { "alleycat",    "Alley Cat",               51414,  0, 2, "dm",     "Snuck out of the Deadmines." },
  { "hallowcat",   "Shadowfang Black Cat",    64794,  0, 3, "sfk",    "Prowls the halls of Shadowfang Keep." },
  { "crusaderlion","Lion of Lordaeron",       37168,  0, 3, "sm",     "A proud lion of the Scarlet Crusade." },
  { "atalai",      "Atal'ai Panther",         39441,  0, 4, "st",     "From the Sunken Temple's shadows." },
  { "embercat",    "Ember Cat",               38417,  0, 4, "brd",    "Born in the forges of Blackrock Depths." },
  { "ghostkit",    "Ghostly Kitten",          59330,  0, 4, "scholo", "Haunts Scholomance's library." },
  { "zulpanther",  "Swift Zulian Panther",    37799,  0, 5, "zg",     "Hakkar's own hunting cat." },
  { "firecat",     "Molten Firecat",          38208,  0, 5, "mc",     "Forged in Molten Core." },
  { "onyx",        "Jeweled Onyx Panther",    42185,  0, 5, "ony",    "Onyx and jewels from Onyxia's hoard." },
  { "chromatic",   "Chromatic Saber",         61926,  0, 5, "bwl",    "Shimmers like a chromatic scale." },
  { "bigglesworth","Mr. Bigglesworth",        46897,  0, 5, "naxx",   "Kel'Thuzad's beloved cat." },
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

-- Adventure clears unlock the earned companions (any class's best clear counts)
function TCF:CheckCompanionUnlocks(quiet)
  if not self.db or not self.db.classData then return end
  local s = self:CompanionState()
  local code = TCF.AdvStageCode
  if not code or not self.AdvStages then return end
  for _, c in ipairs(TCF.COMPANIONS) do
    if c.tier and not s.owned[c.key] then
      local ti, t = tierIndex(c.tier)
      if ti then
        local need = code(ti, self:AdvStages(ti))
        for _, cd in pairs(self.db.classData) do
          if type(cd) == "table" and type(cd.adv) == "table" and (cd.adv.best or 0) >= need then
            s.owned[c.key] = time and time() or true
            self.companionsChanged = true
            if not quiet then
              self:Print(string.format("You cleared %s: |cffffd100%s|r joins you as a companion. Choose it on the character panel.", t.name, c.name), true)
              if self.PlaySound then self:PlaySound("ach") end
            end
            break
          end
        end
      end
    end
  end
  if self.companionsChanged then self.companionsChanged = nil; self:CompanionNotify() end
end

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
