# 1.8.0 Heroic Cache: price and odds, the opening reel's speed (full speed, then a brake onto the
# prize) and what the Heroic Cache's reel shows (a set mix of what the chest can really hold for
# the cat, plus a few locked big prizes, never the same item twice on screen). Real drops are
# unchanged: a young cat still can't win gear far above its level or a legendary.
def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    res = lua.execute(r'''
      local T = TapCatForever
      local problems = {}
      local function ck(ok, msg) if not ok then problems[#problems + 1] = msg end end
      local function near(a, b, eps) return math.abs(a - b) <= (eps or 0.01) end
      local heroic = T.CHEST_BY_KEY.heroic

      -- price, real odds and the chest's colour
      ck(heroic.cost == 1600, "Heroic Cache costs 1,600: " .. tostring(heroic.cost))
      ck(heroic.weights[3] == 54 and heroic.weights[4] == 38 and heroic.weights[5] == 8, "weights 54/38/8")
      ck(heroic.legendary == 0.002, "legendary still 1 in 500")
      ck(T.ChestQuality(heroic) == 3, "Heroic Cache is still a blue chest")
      ck(not heroic.desc:find("!") and not heroic.desc:find("\226\128\148"), "desc: no exclamation marks or em dashes")
      ck(#T:UnownedShopSkins() > 0, "a new player has shop skins left")
      local function odds(level)
        local o, sum = {}, 0
        for _, row in ipairs(T:ChestOdds(heroic, level)) do o[row[1]] = row[2]; sum = sum + row[2] end
        return o, sum
      end
      local o, sum = odds(60)
      ck(near(o["Rare gear"] or 0, 47.047), "level 60 Rare 47.05: " .. tostring(o["Rare gear"]))
      ck(near(o["Epic gear"] or 0, 40.078), "level 60 Epic 40.08: " .. tostring(o["Epic gear"]))
      ck(near(o["Legendary gear"] or 0, 0.194, 0.001), "level 60 Legendary 0.194: " .. tostring(o["Legendary gear"]))
      ck(near(o["Cat skin from the shop"] or 0, 3), "skin 3%")
      ck(near(sum, 100, 1e-6), "level 60 odds sum to 100: " .. sum)
      ck(T.OddsText(o["Legendary gear"] or 0) == "0.2%", "Legendary shown as 0.2%")
      o, sum = odds(55)
      ck(o["Legendary gear"] == nil, "no Legendary line below 60")
      ck(near(o["Rare gear"] or 0, 47.142) and near(o["Epic gear"] or 0, 40.158), "level 55 Rare/Epic: " .. tostring(o["Rare gear"]) .. "/" .. tostring(o["Epic gear"]))
      ck(near(sum, 100, 1e-6), "level 55 odds sum to 100: " .. sum)
      -- no Epic gear near level 30: the Epic share folds into Rare, as before
      o, sum = odds(30)
      ck(near(o["Rare gear"] or 0, 87.3) and o["Epic gear"] == nil, "level 30 Rare: " .. tostring(o["Rare gear"]))
      ck(near(sum, 100, 1e-6), "level 30 odds sum to 100: " .. sum)

      -- the reel's deck, for many levels and classes
      local LAND, COUNT, NEAR = 40, 44, 8
      local function spin(level, key, prize, rarity)
        if T.reel then T.reel:Hide(); T.reel.queue = {}; T.reel.pending = {} end
        T:CD().level = level
        T:PlayChestReel(prize, rarity, key, { prize, true, 0, "test", key, prize.q ~= nil }, level)
        return T.reel.deck
      end
      local function deckChecks(tag, deck, prize, level, isHeroic)
        ck(#deck == COUNT, tag .. ": " .. COUNT .. " cards, got " .. #deck)
        ck(deck[LAND].it == prize, tag .. ": the prize sits under the marker")
        local others, kinds = 0, {}
        for i, d in ipairs(deck) do
          if i ~= LAND then
            others = others + 1
            ck(d.it ~= prize, tag .. ": the prize shows only once (card " .. i .. ")")
            kinds[d.kind] = (kinds[d.kind] or 0) + 1
            local r = (d.rarity or 0) >= 4 and "purple" or "blue"
            kinds[r] = (kinds[r] or 0) + 1
          end
          for j = i + 1, math.min(COUNT, i + NEAR - 1) do
            ck(deck[j].it ~= d.it, tag .. ": " .. tostring(d.it.name) .. " twice on screen (" .. i .. ", " .. j .. ")")
          end
          if isHeroic and i ~= LAND then
            if not d.locked and d.it.q then
              ck((d.it.req or 0) <= level + 3 or (level >= 55 and d.it.q == 4),
                tag .. ": unlocked gear the chest can't give: " .. d.it.name .. " req " .. tostring(d.it.req))
              ck(d.it.q < 5 or level >= 60, tag .. ": an unlocked legendary below 60")
            end
            if d.it.q == 5 and level < 60 then ck(d.locked and d.need == 60, tag .. ": a legendary below 60 is locked at 60") end
            if d.kind == "chase" and level < 55 then ck(d.locked, tag .. ": big prizes are locked below 55 (" .. d.it.name .. ")") end
            if level >= 60 then ck(not d.locked, tag .. ": nothing is locked at 60 (" .. d.it.name .. ")") end
            if d.locked then ck(i < LAND - 4 or i > LAND + 4, tag .. ": a locked card next to the prize (" .. i .. ")") end
            if d.kind == "chase" then ck(i < LAND - 4, tag .. ": a big prize among the last cards on screen (" .. i .. ")") end
            -- the card itself
            local c = T.reel.cards[i]
            ck(c.lock:IsShown() == (d.locked == true) and c.lvl:IsShown() == (d.locked == true), tag .. ": lock shown on locked cards only")
            if d.locked then ck(c.lvl:GetText() == tostring(d.need), tag .. ": lock level text") end
            ck(c.shine:IsShown() == ((d.rarity or 0) >= 4), tag .. ": Epics shine")
          end
        end
        ck(others == COUNT - 1, tag .. ": " .. (COUNT - 1) .. " cards besides the prize")
        return kinds
      end
      local totals = { chase = 0, skin = 0, cosmetic = 0, epic = 0, rare = 0, purple = 0, blue = 0 }
      local allDistinct = 0
      for _, class in ipairs({ "MAGE", "WARRIOR", "HUNTER", "PRIEST", "ROGUE", "PALADIN" }) do
        T.db.class = class
        T.db.classData[class] = T.db.classData[class] or {}
        T:CD(class)
        for _, level in ipairs({ 1, 10, 20, 30, 45, 52, 55, 58, 60 }) do
          local pool = T:ChestGearPool(class, level, 3)
          local prize = pool[1] or T:ChestGearPool(class, level, 2)[1]
          if prize then
            local tag = class .. " lv" .. level
            local deck = spin(level, "heroic", prize, prize.q)
            local kinds = deckChecks(tag, deck, prize, level, true)
            for k, n in pairs(kinds) do if totals[k] then totals[k] = totals[k] + n end end
            ck((kinds.chase or 0) == 4, tag .. ": 4 big prizes, got " .. tostring(kinds.chase))
            ck((kinds.skin or 0) == 2, tag .. ": 2 shop skins, got " .. tostring(kinds.skin))
            -- two of the big prizes are legendaries the class can use, at every level
            local legs = 0
            for _, d in ipairs(deck) do if d.kind == "chase" and d.it.q == 5 then legs = legs + 1 end end
            ck(legs == math.min(2, #T:LegendariesFor()), tag .. ": legendaries among the big prizes: " .. legs)
            local seen, dup = {}, false
            for _, d in ipairs(deck) do if seen[d.it] then dup = true end; seen[d.it] = true end
            if not dup then allDistinct = allDistinct + 1 end
            -- the hint names the level, and the lock level when there are locked cards
            local hint = T.reel.hint:GetText()
            ck(hint:find("level " .. level .. "%.") ~= nil, tag .. ": hint " .. hint)
            local anyLocked = false
            for _, d in ipairs(deck) do if d.locked then anyLocked = true end end
            ck((hint:find("Locked prizes need level") ~= nil) == anyLocked, tag .. ": lock hint " .. hint)
            ck(not hint:find("!") and not hint:find("\226\128\148"), tag .. ": hint wording")
          end
        end
      end
      -- big enough pools: every card on the strip is different
      ck(allDistinct >= 40, "decks with every card different: " .. allDistinct .. " of 54")
      -- Epics or better on about half the strip, even for cats too young for Epic gear (Epic
      -- cosmetics they can really win fill in)
      ck(totals.purple > totals.blue * 0.8, "the strip shows plenty of Epics: " .. totals.purple .. " vs " .. totals.blue)

      -- other chests keep their random strip, still never the same item twice on screen
      T.db.class = "MAGE"
      for _, key in ipairs({ "pouch", "strong", "dungeon", "raid" }) do
        for _, level in ipairs({ 5, 30, 60 }) do
          local g = T:ChestGearPool("MAGE", level, 2)[1] or T:ChestGearPool("MAGE", level, 3)[1]
          local deck = spin(level, key, g, g.q)
          deckChecks(key .. " lv" .. level, deck, g, level, false)
        end
      end

      -- the motion: full speed, then a brake that lands on the prize; never more than half a card
      -- a frame at 60 fps; done after about 2.65 seconds
      T.db.class = "MAGE"
      local prize = T:ChestGearPool("MAGE", 60, 3)[1]
      for run = 1, 6 do
        spin(60, "heroic", prize, 3)
        local f = T.reel
        local xs = {}
        local landCard = f.cards[LAND]
        landCard.SetPoint = function(self, a, rel, b, x) xs[#xs + 1] = x end
        local OnUpdate = f:GetScript("OnUpdate")
        local last, maxStep, back, steps = nil, 0, false, 0
        local shownAt1 = nil
        while f:IsShown() and steps < 400 do
          OnUpdate(f, 1 / 60); steps = steps + 1
          local x = xs[#xs]
          if x and last then
            if x > last + 1e-6 then back = true end
            maxStep = math.max(maxStep, last - x)
          end
          if x then last = x end
          if steps == 60 then shownAt1 = f:IsShown() end
        end
        landCard.SetPoint = nil
        ck(not back, "the reel never runs backwards")
        ck(maxStep <= 32, "at most half a card a frame: " .. maxStep)
        ck(shownAt1 == true, "still spinning after one second")
        ck(steps >= 155 and steps <= 162, "done after about 2.65 s: " .. steps / 60)
        -- landed: the prize card's middle within 16 px of the marker
        ck(last and math.abs(last + 28 - 248) <= 16.01, "lands on the prize: " .. tostring(last))
      end
      -- a click skips to the landing
      spin(60, "heroic", prize, 3)
      T.reel:GetScript("OnMouseUp")(T.reel)
      T.reel:GetScript("OnUpdate")(T.reel, 0.01)
      ck(T.reel.cards[LAND].glow:IsShown(), "a click lands at once")
      for _ = 1, 6 do _update(0.1) end
      ck(not T.reel:IsShown(), "and closes after the short hold")
      -- _update steps like the rest of the harness: shown at 1.0 s, gone after 2.7 s
      spin(60, "heroic", prize, 3)
      for _ = 1, 10 do _update(0.1) end
      ck(T.reel:IsShown(), "shown at 1.0 s")
      for _ = 1, 17 do _update(0.1) end
      ck(not T.reel:IsShown(), "finished after 2.7 s")

      -- the real drops are unchanged: no gear far above the level and no legendary for young cats
      T.reel:Hide()
      local saveAnim = T.db.ui.chestAnim
      T.db.ui.chestAnim = false
      T.openingAll = true
      local oReveal, oToast = T.ShowLootRevealDirect, T.ShowLootToast
      T.ShowLootRevealDirect = function() end
      T.ShowLootToast = function() end
      for _, level in ipairs({ 10, 30 }) do
        T:CD().level = level
        local bad = 0
        for _ = 1, 400 do
          local g = T:OpenChestContents(heroic, "heroic")
          if g and g.q and ((g.req or 0) > level + 3 or g.q == 5) then bad = bad + 1 end
        end
        ck(bad == 0, "real Heroic Cache drops at level " .. level .. ": " .. bad .. " too strong")
      end
      T.ShowLootRevealDirect, T.ShowLootToast = oReveal, oToast
      T.openingAll = nil
      T.db.ui.chestAnim = saveAnim
      return table.concat(problems, "\n"), string.format("strip mix: chase %d, skin %d, cosmetic %d, epic %d, rare %d (Epic or better %d, below %d)",
        totals.chase, totals.skin, totals.cosmetic, totals.epic, totals.rare, totals.purple, totals.blue)
    ''')
    problems, mix = res[0], res[1]
    if problems:
        raise AssertionError("heroic cache:\n" + problems)
    print(mix)
    print("heroic cache section (price 1,600, odds, reel speed, reel deck with locked big prizes, real drops unchanged): all checks passed")
