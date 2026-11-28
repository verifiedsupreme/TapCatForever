# 1.7.4 Shop revamp: the Skin of the Day (a fifth off one shop skin a day, per cat), the Daily
# Wares' third slot (any-class pieces only), and the Shop page's three views (Featured, Cat Skins,
# Chests) plus its Companions button: they build, refresh, buy and stay cheap on the quick refresh.
def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    res = lua.execute(r'''
      local T = TapCatForever
      local problems = {}
      local function ck(ok, msg) if not ok then problems[#problems + 1] = msg end end
      local function round50(n) return math.max(50, math.floor(n * 0.8 / 50 + 0.5) * 50) end
      T.db.ui.chat = false

      ---------------------------------------------------------------- Skin of the Day
      local shop = T.db.shop
      shop.day, shop.featuredDay, shop.featured = "", "19990101", { MAGE = "skin_lion" }
      T:BuildShop(true)
      local f = T:FeaturedSkin()
      ck(f and f.slot == "skin" and f.skinPrice and not T.db.owned[f.id], "a new day picks an unowned shop skin: " .. tostring(f and f.id))
      ck(type(shop.featured) == "table" and shop.featured[T.db.class] == f.id, "kept per cat in db.shop.featured")
      ck(T:FeaturedSkin() == f, "the same skin all day")
      T:RerollShop()
      ck(T:FeaturedSkin() == f, "rerolling the Daily Wares keeps the Skin of the Day")
      ck(T:SkinPrice(f) == round50(f.skinPrice) and T:SkinPrice(f) < f.skinPrice, "a fifth off: " .. T:SkinPrice(f) .. " for " .. f.skinPrice)
      local others = 0
      for _, it in ipairs(T.ITEM_LIST) do
        if it.slot == "skin" and it.skinPrice and it ~= f then
          others = others + 1
          ck(T:SkinPrice(it) == it.skinPrice, it.id .. " keeps its price")
        end
      end
      ck(others > 20, "the other shop skins: " .. others)
      ck(T:SkinPrice(T.ITEMS.skin_galaxy) == nil, "an unsold skin has no price")
      -- the rounding, on known prices
      local today = shop.featuredDay
      shop.featured[T.db.class] = "skin_lion"
      ck(T:SkinPrice(T.ITEMS.skin_lion) == 9600, "12,000 becomes 9,600: " .. T:SkinPrice(T.ITEMS.skin_lion))
      shop.featured[T.db.class] = "skin_mittens"
      ck(T:SkinPrice(T.ITEMS.skin_mittens) == 250, "300 becomes 250: " .. T:SkinPrice(T.ITEMS.skin_mittens))
      shop.featured[T.db.class] = f.id
      -- an old day's pick is not discounted
      shop.featuredDay = "19990101"; shop.featured = { [T.db.class] = "skin_lion" }
      T:FeaturedSkin()
      ck(shop.featuredDay == today and shop.featured[T.db.class] ~= nil, "yesterday's pick is dropped, a new one made")
      f = T:FeaturedSkin()
      -- another cat gets its own pick, and the first one's stays
      T:SetClass("HUNTER")
      local hf = T:FeaturedSkin()
      ck(hf and not T:Owned("HUNTER")[hf.id], "the Hunter's own Skin of the Day")
      T:SetClass("MAGE")
      ck(T:FeaturedSkin() == f, "the Mage's pick is kept")
      -- buying it: the discounted price, "Bought in the Shop", and the discount doesn't move
      T.db.coins = 100000
      local before = T.db.coins
      local price = T:SkinPrice(f)
      ck(T:BuySkin(f.id, "shop"), "buy the Skin of the Day")
      ck(T.db.coins == before - price, "charged " .. price .. ": " .. (before - T.db.coins))
      ck(T:ItemSourceRecord(f.id).first[1] == "Bought in the Shop", "source: " .. tostring(T:ItemSourceRecord(f.id).first[1]))
      ck(T.db.owned[f.id] and T:FeaturedSkin() == f, "owned, and still today's pick (no new discount)")
      for _, it in ipairs(T.ITEM_LIST) do
        if it.slot == "skin" and it.skinPrice and it ~= f and T:SkinPrice(it) ~= it.skinPrice then ck(false, "the discount moved to " .. it.id) end
      end
      -- the Appearance tab still says so
      local other
      for _, it in ipairs(T:UnownedShopSkins()) do if it ~= f then other = it; break end end
      ck(T:BuySkin(other.id) and T:ItemSourceRecord(other.id).first[1] == "Bought in the Appearance tab", "Appearance tab source")

      ---------------------------------------------------------------- Daily Wares: slot 3
      T.db.coins = 1e7
      for _, cls in ipairs({ "MAGE", "WARRIOR", "HUNTER" }) do
        T:SetClass(cls)
        for _ = 1, 12 do
          shop.rerolls = 0
          T:RerollShop()
          local st = shop.stock
          ck(#st == 3, cls .. ": three wares")
          ck(st[3] and T.ITEMS[st[3]].class == nil, cls .. ": the third ware is for any class: " .. tostring(st[3]))
          ck(st[1] and T.ITEMS[st[1]].class == cls and st[2] and T.ITEMS[st[2]].class == cls, cls .. ": the first two are the class's")
        end
      end
      T:SetClass("MAGE")

      ---------------------------------------------------------------- the Shop page
      local from = #_frames
      local build = T.UI.Builders.shop
      local shopFrom, shopTo
      T.UI.Builders.shop = function(...) shopFrom = #_frames; local r = build(...); shopTo = #_frames; return r end
      T:ToggleWindow()
      T.UI.Builders.shop = build
      local win = T.window
      local S = win.shopUI
      ck(S and shopFrom and shopTo > shopFrom, "the Shop page is built with the window")
      win:SelectTab(8)
      ck(win.shopView == "featured" and S.views.featured:IsShown() and not S.views.skins:IsShown() and not S.views.chests:IsShown(), "opens on Featured")
      -- plain, friendly text: no exclamation marks or em dashes anywhere on the page
      local function scanText()
        for i = shopFrom + 1, shopTo do
          local fr = _frames[i]
          local t = type(fr.text) == "string" and fr.text or nil
          if t and (t:find("!", 1, true) or t:find("\226\128\148", 1, true)) then ck(false, "text: " .. t) end
        end
      end
      -- every chest you can buy shows its plain name, twice at most (the banner and its card)
      local names = {}
      for i = shopFrom + 1, shopTo do
        local fr = _frames[i]
        if fr.kind == "FontString" and type(fr.text) == "string" then names[fr.text] = (names[fr.text] or 0) + 1 end
      end
      for _, ch in ipairs(T.CHESTS) do
        ck((names[ch.name] ~= nil) == (ch.cost ~= nil), ch.name .. (ch.cost and " is sold" or " is not sold"))
      end
      ck(S.banner.name:GetText() == "Heroic Cache", "the banner's name")

      -- Featured at level 34: the odds chips, the top prizes (1.7.6: only gear this cat can win now,
      -- best first, nothing locked) and the offers
      T:CD().level = 34
      win:Refresh()
      local chips = {}
      for _, c in ipairs(S.banner.chips) do chips[#chips + 1] = c:GetText() or "" end
      local all = table.concat(chips, " | ")
      ck(all:find("Rare gear", 1, true) and all:find("Legendary: level 60", 1, true) and all:find("Cat skin", 1, true), "chips at 34: " .. all)
      local shown, lastQ, lastI = 0, 9, 9999
      local lv = T:ChestLevel()
      local pool = {}
      for _, q in ipairs({ 2, 3, 4 }) do for _, it in ipairs(T:ChestGearPool(T.db.class, lv, q)) do pool[it] = true end end
      for _, b in ipairs(S.banner.prizes) do
        if b:IsShown() then
          shown = shown + 1
          ck(not b.lock:IsShown() and (b.lvl:GetText() or "") == "", "level 34: no lock on " .. b.item.name)
          ck(pool[b.item], "level 34: a prize this cat can win now: " .. b.item.name)
          ck(b.item.q < 5 and (b.item.req or 0) <= lv, "level 34: only gear it can wear now: " .. b.item.name .. " req " .. tostring(b.item.req))
          ck(b.item.q < lastQ or (b.item.q == lastQ and (b.item.ilvl or 0) <= lastI), "best first")
          lastQ, lastI = b.item.q, b.item.ilvl or 0
        end
      end
      ck(shown >= 4, "level 34: top prizes shown: " .. shown)
      -- a young cat (the chest's gear is Uncommon below 10) still sees its best prizes
      T:CD().level = 5
      win:Refresh()
      local young = 0
      for _, b in ipairs(S.banner.prizes) do
        if b:IsShown() then young = young + 1; ck((b.item.req or 0) <= T:ChestLevel(), "level 5: wearable: " .. b.item.name) end
      end
      ck(young >= 4, "level 5: top prizes shown: " .. young)
      T:CD().level = 60
      win:Refresh()
      chips = {}
      for _, c in ipairs(S.banner.chips) do chips[#chips + 1] = c:GetText() or "" end
      all = table.concat(chips, " | ")
      ck(all:find("Legendary|r  0.2%", 1, true) and all:find("Epic gear", 1, true), "chips at 60: " .. all)
      for _, b in ipairs(S.banner.prizes) do if b:IsShown() then ck(not b.lock:IsShown(), "level 60: nothing locked") end end
      T:CD().level = 34
      -- open a Heroic Cache from the banner
      T.db.coins = 5000
      win:Refresh()
      ck(S.banner.open:GetText():find("1,600", 1, true) or S.banner.open:GetText():find("1600", 1, true), "Open shows the price: " .. S.banner.open:GetText())
      local n0 = T.db.stats.chests
      S.banner.open:GetScript("OnClick")(S.banner.open)
      -- (a chest can hold a few TapCoins on top)
      ck(T.db.stats.chests == n0 + 1 and T.db.coins >= 5000 - 1600 and T.db.coins <= 5000 - 1600 + 300, "the banner opens a Heroic Cache: " .. T.db.coins)
      if T.reel then T.reel:Hide(); T.reel.queue = {}; T.reel.pending = {} end
      -- the Daily Wares buy
      T.db.coins = 1e6
      win:Refresh()
      local card = S.wares[3]
      ck(card:IsShown() and card.id, "a third ware")
      card.buy:GetScript("OnClick")(card.buy)
      ck(T.db.owned[card.id], "Buy on a ware card")
      win:Refresh()
      ck(card.price:GetText():find("Owned", 1, true), "it shows Owned")
      -- the Skin of the Day tile
      shop.featured[T.db.class] = nil
      local sk = T:FeaturedSkin()
      win:Refresh()
      ck(sk and S.sotd.cell.item == sk and S.sotd.badge:IsShown(), "the tile shows the Skin of the Day with its badge")
      ck(S.sotd.buy:GetText():find(T.Commas(T:SkinPrice(sk)), 1, true), "the tile's price: " .. tostring(S.sotd.buy:GetText()))
      S.sotd.buy:GetScript("OnClick")(S.sotd.buy)
      ck(T.db.owned[sk.id] and T:ItemSourceRecord(sk.id).first[1] == "Bought in the Shop", "Buy on the tile (no confirm in the test)")
      win:Refresh()
      ck(S.sotd.buy:GetText() == "Owned" and not S.sotd.badge:IsShown(), "then it reads Owned")
      -- heritage and companions tiles
      ck(S.heritage:IsShown() and S.heritage.title:GetText() == "Orc Heritage", "racial heritage tile: " .. tostring(S.heritage.title:GetText()))
      local own, total = 0, #T.COMPANIONS
      for _, c in ipairs(T.COMPANIONS) do if T:CompanionOwned(c.key) then own = own + 1 end end
      ck(S.companions.owned:GetText() == own .. " / " .. total .. " owned", "companions: " .. tostring(S.companions.owned:GetText()))
      ck(S.companions.cheapest and S.companions.cheapest.price > 0 and not T:CompanionOwned(S.companions.cheapest.key), "the cheapest companion you can buy")
      for _, c in ipairs(T.COMPANIONS) do
        if c.price > 0 and not T:CompanionOwned(c.key) then ck(c.price >= S.companions.cheapest.price, "cheapest: " .. c.key) end
      end
      -- Companions (the sub-tab and the tile's button) open the companion window
      local toggled = 0
      local oToggle = T.ToggleCompanions
      T.ToggleCompanions = function() toggled = toggled + 1 end
      S.nav[4]:GetScript("OnClick")(S.nav[4])
      S.companions.browse:GetScript("OnClick")(S.companions.browse)
      T.ToggleCompanions = oToggle
      ck(toggled == 2 and win.shopView == "featured", "Companions opens the companion window, the view stays")
      ck(oToggle ~= nil, "TCF:ToggleCompanions exists")

      -- the quick refresh (every tap) doesn't work out chest odds or rebuild lists
      local odds, unowned = 0, 0
      local oOdds, oUn = T.ChestOdds, T.UnownedShopSkins
      T.ChestOdds = function(...) odds = odds + 1; return oOdds(...) end
      T.UnownedShopSkins = function(...) unowned = unowned + 1; return oUn(...) end
      for _, v in ipairs({ "featured", "skins", "chests" }) do
        S.nav[v == "featured" and 1 or v == "skins" and 2 or 3]:GetScript("OnClick")(nil)
        ck(win.shopView == v and S.views[v]:IsShown(), "sub-tab " .. v)
        odds, unowned = 0, 0
        for _ = 1, 20 do win:RefreshLight() end
        ck(odds == 0 and unowned == 0, v .. ": the quick refresh is cheap (" .. odds .. " odds, " .. unowned .. " skin lists)")
      end
      T.ChestOdds, T.UnownedShopSkins = oOdds, oUn
      -- a full refresh with nothing changed reuses the odds
      win:SetShopView("chests"); win:Refresh()
      odds = 0
      T.ChestOdds = function(...) odds = odds + 1; return oOdds(...) end
      win:Refresh()
      T.ChestOdds = oOdds
      ck(odds == 0, "odds cached between full refreshes: " .. odds)

      -- Chests: three cards, prices, odds and the Treasure Bag
      ck(#S.chests == 3, "three chests for sale")
      for _, c in ipairs(S.chests) do
        ck(c.odds:GetText() and select(2, c.odds:GetText():gsub("\n", "")) == 2, c.chest.name .. ": three odds lines")
        ck(c.open:GetText():find("Open", 1, true), c.chest.name .. ": Open button")
      end
      ck(S.freeText:GetText():find("Free chests", 1, true) and S.freeText:GetText() ~= "Dungeon Chest", "the free chest text is a sentence")
      T.db.coins = 1e6
      local strong = S.chests[2]
      local c0 = T.db.stats.chests
      strong.open:GetScript("OnClick")(strong.open)
      ck(T.db.stats.chests == c0 + 1, "Open on a chest card")
      if T.reel then T.reel:Hide(); T.reel.queue = {}; T.reel.pending = {} end
      win:Refresh()
      ck(S.lastLoot:IsShown() and S.lastLoot:GetText():find("Last chest", 1, true), "the last chest line: " .. tostring(S.lastLoot:GetText()))
      ck(S.bagText:GetText():find("Treasure Bag: " .. T:ChestCount() .. " unopened", 1, true), "bag line: " .. S.bagText:GetText())

      -- Cat Skins
      win:SetShopView("skins")
      ck(not S.lastLoot:IsShown(), "no last chest line under the skins")
      local list = S.skinList()
      ck(#list == #T:UnownedShopSkins(), "For sale lists every unowned shop skin: " .. #list .. " / " .. #T:UnownedShopSkins())
      for i = 2, #list do
        if list[i - 1] ~= T:FeaturedSkin() then ck(list[i - 1].skinPrice <= list[i].skinPrice, "cheapest first: " .. list[i - 1].id .. ", " .. list[i].id) end
      end
      ck(S.skinCount:GetText():find("/ 29 shop skins owned", 1, true), "count: " .. S.skinCount:GetText())
      local pages = math.ceil(#list / 15)
      ck(S.pageText:GetText() == "Page 1 / " .. pages, "pages: " .. S.pageText:GetText())
      -- the Skin of the Day goes first while it is for sale
      shop.featured[T.db.class] = list[#list].id
      win:SetShopView("skins")
      list = S.skinList()
      ck(list[1] == T:FeaturedSkin() and S.skinCards[1].badge:IsShown(), "the Skin of the Day leads For sale, with its badge")
      ck(S.skinCards[1].btn:GetText():find(T.Commas(T:SkinPrice(list[1])), 1, true), "its button shows today's price")
      -- a plain click on an affordable card buys it (the game asks first; the test has no popup)
      T.db.coins = 1e6
      local c1 = S.skinCards[2]
      local it = c1.item
      c1.cell:GetScript("OnClick")(c1.cell)
      ck(T.db.owned[it.id], "a click buys " .. it.id)
      ck(#S.skinList() == #T:UnownedShopSkins(), "and it leaves For sale")
      -- too poor: nothing happens
      T.db.coins = 0
      win:Refresh()
      local c2 = S.skinCards[2]
      local it2 = c2.item
      c2.cell:GetScript("OnClick")(c2.cell)
      ck(not T.db.owned[it2.id], "no TapCoins, no skin")
      -- Owned: wear and take off
      S.filters[2]:GetScript("OnClick")(S.filters[2])
      ck(win.shopSkinFilter == "owned", "Owned filter")
      local ow = S.skinList()
      ck(#ow >= 3, "owned skins listed: " .. #ow)
      for i = 2, #ow do ck(ow[i - 1].rarity >= ow[i].rarity, "owned: rarest first") end
      local oc
      for _, c in ipairs(S.skinCards) do if c:IsShown() and not T:IsEquipped(c.item) then oc = c; break end end
      ck(oc and oc.btn:GetText() == "Wear", "Wear on an owned skin")
      oc.btn:GetScript("OnClick")(oc.btn)
      ck(T:IsEquipped(oc.item), "Wear puts it on")
      win:Refresh()
      ck(oc.btn:GetText() == "Take off", "then Take off")
      oc.btn:GetScript("OnClick")(oc.btn)
      ck(not T:IsEquipped(oc.item), "Take off removes it")
      -- All skins: every skin for this class; unsold ones say where they come from
      S.filters[3]:GetScript("OnClick")(S.filters[3])
      local everyone = 0
      for _, s in ipairs(T.ITEM_LIST) do if s.slot == "skin" and (not s.class or s.class == T.db.class) then everyone = everyone + 1 end end
      ck(#S.skinList() == everyone, "All skins: " .. #S.skinList() .. " / " .. everyone)
      local seenGroup, lastGroup = {}, 0
      for _, s in ipairs(S.skinList()) do
        local g = T.db.owned[s.id] and 3 or (s.skinPrice and 1 or 2)
        ck(g >= lastGroup, "All skins: for sale, then found elsewhere, then owned")
        lastGroup = g
      end
      win.shopSkinPage = 99; win:SetShopView("skins")
      ck(win.shopSkinPage == math.ceil(everyone / 15), "the page stays in range")
      local tagged = false
      for _, c in ipairs(S.skinCards) do
        if c:IsShown() and not c.item.skinPrice and not T.db.owned[c.item.id] then tagged = true; ck(c.btn:GetText():find("|cffff8000", 1, true), "an unsold skin shows its source") end
      end
      for p = 1, math.ceil(everyone / 15) do
        win.shopSkinPage = p; win:SetShopView("skins")
        for _, c in ipairs(S.skinCards) do
          if c:IsShown() and not c.item.skinPrice and not T.db.owned[c.item.id] then tagged = true end
        end
      end
      ck(tagged, "some skins are found, not sold")
      win.shopSkinFilter = "sale"

      -- every view in compact mode too
      win:SetCompact(true)
      win:SelectTab(8)
      for _, v in ipairs({ "featured", "skins", "chests" }) do win:SetShopView(v); win:Refresh(); win:RefreshLight() end
      win:SetCompact(false)
      -- the glows pulse while their view is up
      win:SetShopView("featured")
      for _ = 1, 5 do _update(0.2) end
      scanText()
      return table.concat(problems, "\n")
    ''')
    if res:
        raise AssertionError("shop:\n" + res)
    print("shop section (Skin of the Day, Daily Wares slot 3, Featured, Cat Skins and Chests views, Companions button, cheap quick refresh): all checks passed")
