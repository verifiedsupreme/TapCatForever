# 1.6.0 skin moves and Shop prices: the three best-looking skins moved behind hard content
# (Galaxy Cat from Kel'Thuzad, Diamond Cat from Nefarian and the real General Drakkisath,
# Emberheart Cat from Ragnaros with a smaller Molten Core expedition chance), players who own
# them keep them, the other chest and expedition skins stay where they were, and the Shop skins
# have their new prices (Epic and Legendary cosmetic prices unchanged).
def check(seed, load_addon):
    lua = load_addon()
    lua.execute("_seed = %d; math.randomseed(_seed)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local bad = {}
      local function ck(c, m) if not c then bad[#bad + 1] = m end end
      local function how(id) return table.concat(T:HowToGet(T.ITEMS[id]), " / ") end
      local function zoneOf(boss)
        for _, t in ipairs(T.TIERS) do for _, b in ipairs(t.bosses) do if b[1] == boss then return t.name end end end
      end
      local function drop(boss) local d = T.SKIN_DROPS[boss]; return d and d.id, d and d.chance end

      -- the boss names are the Adventure bosses' own names
      ck(zoneOf("Kel'Thuzad") == "Naxxramas", "Kel'Thuzad is in Naxxramas")
      ck(zoneOf("Nefarian") == "Blackwing Lair", "Nefarian is in Blackwing Lair")
      ck(zoneOf("Ragnaros") == "Molten Core", "Ragnaros is in Molten Core")
      ck(T.REAL_BOSS_BY_KEY.drakkisath.name == "General Drakkisath" and T.REAL_BOSS_BY_KEY.drakkisath.place == "Blackrock Spire", "real General Drakkisath")

      -- Galaxy Cat: left the Shop, Kel'Thuzad 2%
      local g = T.ITEMS.skin_galaxy
      local id, ch = drop("Kel'Thuzad")
      ck(g.skinPrice == nil and g.get == nil, "Galaxy Cat is not sold")
      ck(id == "skin_galaxy" and ch == 0.02, "Kel'Thuzad drops the Galaxy Cat at 2%")
      for _, it in ipairs(T:UnownedShopSkins()) do ck(it.id ~= "skin_galaxy", "the Heroic Cache no longer gives the Galaxy Cat as a shop skin") end
      local h = how("skin_galaxy")
      ck(h:find("Adventure: dropped by Kel'Thuzad in Naxxramas, 2% chance", 1, true) and not h:find("Buy in", 1, true) and not h:find("Heroic Cache", 1, true), "Galaxy Cat: " .. h)
      ck(T.SkinSourceTag(g) == "drop", "Galaxy Cat cell tag: " .. tostring(T.SkinSourceTag(g)))
      T.db.coins = 1e6
      ck(not T:BuySkin("skin_galaxy") and not T.db.owned.skin_galaxy, "the Galaxy Cat can't be bought")

      -- Diamond Cat: left the Heroic Cache, Nefarian 2% and the real General Drakkisath 5%
      local d = T.ITEMS.skin_diamond
      id, ch = drop("Nefarian")
      ck(d.get == nil and d.skinPrice == nil, "Diamond Cat is not in the Heroic Cache")
      ck(id == "skin_diamond" and ch == 0.02, "Nefarian drops the Diamond Cat at 2%")
      local rw = T:RealBossRewardsFor("skin_diamond")
      ck(#rw == 1 and rw[1][1].key == "drakkisath" and rw[1][2].chance == 0.05, "the real General Drakkisath gives the Diamond Cat at 5%")
      h = how("skin_diamond")
      ck(h:find("Adventure: dropped by Nefarian in Blackwing Lair, 2% chance", 1, true)
        and h:find("In WoW: kill General Drakkisath in Blackrock Spire with TapCatForever on, 5% chance each kill", 1, true)
        and not h:find("Heroic Cache", 1, true), "Diamond Cat: " .. h)

      -- Emberheart Cat: Ragnaros 3%, the Molten Core expedition keeps 1%
      local e = T.ITEMS.skin_emberheart
      id, ch = drop("Ragnaros")
      ck(id == "skin_emberheart" and ch == 0.03, "Ragnaros drops the Emberheart Cat at 3%")
      ck(e.get and e.get.kind == "expedition" and e.get.expedition == "mc" and e.get.chance == 0.01, "the Molten Core expedition keeps 1%")
      h = how("skin_emberheart")
      ck(h:find("Adventure: dropped by Ragnaros in Molten Core, 3% chance", 1, true) and h:find("Expedition reward: 1% chance", 1, true), "Emberheart Cat: " .. h)
      ck(T.SkinSourceTag(e) == "drop", "Emberheart Cat cell tag: " .. tostring(T.SkinSourceTag(e)))

      -- the others stay where they are
      local function get(it) return it.get or {} end
      ck(get(T.ITEMS.skin_rainbow).chest == "strong" and get(T.ITEMS.skin_rainbow).chance == 0.005, "Rainbow Cat stays in the Strongbox")
      ck(get(T.ITEMS.skin_golden).chest == "heroic" and get(T.ITEMS.skin_golden).chance == 0.02, "Golden Treasure Cat stays in the Heroic Cache")
      ck(get(T.ITEMS.skin_runebound).expedition == "strat" and get(T.ITEMS.skin_runebound).chance == 0.01, "Runebound Cat stays on Stratholme")
      for boss, dd in pairs(T.SKIN_DROPS) do
        for _, x in ipairs(dd.id and { dd } or dd) do
          ck(x.id ~= "skin_rainbow" and x.id ~= "skin_golden" and x.id ~= "skin_runebound", boss .. " should not drop " .. x.id)
        end
      end

      -- the drops work: Adventure kills and the real Drakkisath
      local function farm(fn, skin)
        for i = 1, 3000 do if T.db.owned[skin] then return true end fn() end
        return T.db.owned[skin]
      end
      ck(farm(function() T:AdvMobKilled({ name = "Kel'Thuzad", boss = 4, level = 63 }) end, "skin_galaxy"), "Kel'Thuzad can drop the Galaxy Cat")
      ck(farm(function() T:AdvMobKilled({ name = "Nefarian", boss = 8, level = 63 }) end, "skin_diamond"), "Nefarian can drop the Diamond Cat")
      ck(farm(function() T:AdvMobKilled({ name = "Ragnaros", boss = 6, level = 63 }) end, "skin_emberheart"), "Ragnaros can drop the Emberheart Cat")
      T.db.owned.skin_diamond = nil
      ck(farm(function() T:RealBossKilled(T.REAL_BOSS_BY_KEY.drakkisath, "test") end, "skin_diamond"), "the real General Drakkisath can drop the Diamond Cat")

      -- owners keep theirs and can still wear them
      for _, sid in ipairs({ "skin_galaxy", "skin_diamond", "skin_emberheart" }) do
        T.db.owned[sid] = 1
        T.db.look.skin = sid
        local look = T:GetAppearance()
        ck(T.db.owned[sid] and look.skin and look.skin.id == sid, sid .. " stays owned and worn")
      end
      T.db.look.skin = nil

      -- Shop prices
      local PRICES = {
        skin_lion = 12000, skin_spectral = 12000, skin_manasaber = 8000, skin_fel = 7000, skin_winterspring = 7000,
        skin_lynx = 6500, skin_mech = 6000,
        skin_strawberry = 2500, skin_darkmoon = 2500, skin_mainecoon = 2500, skin_bengal = 2000, skin_spotted = 2000,
        skin_calico = 1800, skin_frostsaber = 1800, skin_nightsaber = 1800, skin_panther = 1800,
        skin_snowshoe = 800, skin_tortie = 800, skin_dalmatian = 700, skin_russianblue = 600, skin_siamese = 600,
        skin_whitekitten = 600, skin_bombay = 500, skin_cornishrex = 500, skin_cow = 450, skin_tuxedo = 400,
        skin_blacktabby = 350, skin_silvertabby = 350, skin_mittens = 300,
      }
      local n = 0
      for _, it in ipairs(T.ITEM_LIST) do
        if it.slot == "skin" and it.skinPrice then
          n = n + 1
          ck(PRICES[it.id] == it.skinPrice, it.id .. " costs " .. it.skinPrice .. ", expected " .. tostring(PRICES[it.id]))
        end
      end
      local want = 0
      for _ in pairs(PRICES) do want = want + 1 end
      ck(n == want, "shop skins: " .. n .. ", expected " .. want)
      h = how("skin_lion")
      ck(h:find("Buy in the Appearance tab for " .. T.Commas(12000) .. " TapCoins", 1, true), "price line: " .. h)
      -- Epic and Legendary cosmetics keep their prices
      ck(T.RARITY[4].price == 1500 and T.RARITY[5].price == 5000, "Epic and Legendary cosmetic prices unchanged")

      for _, sid in ipairs({ "skin_galaxy", "skin_diamond", "skin_emberheart", "skin_lion" }) do
        ck(not how(sid):find("!", 1, true), sid .. ": no exclamation marks")
      end
      return table.concat(bad, "; ")
    ''')
    if r:
        raise AssertionError("skin moves: " + r)
    print("skin moves section (Galaxy, Diamond and Emberheart behind raid bosses and General Drakkisath, owners keep them, Rainbow, Golden Treasure and Runebound unchanged, new Shop prices, cosmetic prices unchanged): all checks passed")
