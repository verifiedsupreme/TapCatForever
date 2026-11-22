# 1.5.4 loot track E: every cosmetic remembers where it came from (first and latest), shown as
# "Got it from: Heroic Cache, 3 days ago" in item tooltips (Appearance tab, Compendium).
def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local p = {}
      local function ck(c, m) if not c then p[#p + 1] = m end end
      local function tip(it)
        local lines = {}
        local tt = { AddLine = function(_, t) lines[#lines + 1] = tostring(t) end, AddDoubleLine = function() end }
        T:ItemTooltip(tt, it)
        return table.concat(lines, "\n")
      end
      T.RefreshAll = function() end
      -- an item owned before tracking
      local old
      for _, it in ipairs(T.ITEM_LIST) do if it.source == "loot" and not T.db.owned[it.id] and it.slot == "head" then old = it; break end end
      T.db.owned[old.id] = 1
      ck(tip(old):find("Got before this was tracked", 1, true), "old item: " .. tip(old))
      -- a cosmetic from a chest
      local cos
      for _, it in ipairs(T.ITEM_LIST) do if it.source == "loot" and not T.db.owned[it.id] and it.slot == "back" then cos = it; break end end
      T:GrantItem(cos, "Heroic Cache", true, "heroic")
      local rec = T:ItemSourceRecord(cos.id)
      ck(rec and rec.first[1] == "Heroic Cache" and rec.last[1] == "Heroic Cache", "chest source")
      ck(tip(cos):find("Got it from: Heroic Cache, just now", 1, true), "tooltip: " .. tip(cos))
      -- three days later another copy from a lucky find
      rec.first[2] = rec.first[2] - 3 * 86400; rec.last[2] = rec.first[2]
      T:GrantItem(cos, "Lucky find while tapping")
      local t = tip(cos)
      ck(t:find("Got it from: Heroic Cache, 3 days ago", 1, true) and t:find("Latest one from: Lucky find while tapping, just now", 1, true), "first and latest: " .. t)
      -- skins: found in a chest, a boss drop, bought
      local skins = {}
      for _, it in ipairs(T.ITEM_LIST) do if it.slot == "skin" and not T.db.owned[it.id] then skins[#skins + 1] = it end end
      T:GrantSkin(skins[1].id, "Found in a Heroic Cache", true)
      ck(T:ItemSourceRecord(skins[1].id).first[1] == "Heroic Cache", "skin from a chest")
      T:GrantSkin(skins[2].id, "Dropped by Hakkar in Zul'Gurub")
      ck(T:ItemSourceRecord(skins[2].id).first[1] == "Hakkar (Zul'Gurub)", "boss drop: " .. T:ItemSourceRecord(skins[2].id).first[1])
      local buy
      for _, it in ipairs(skins) do if it.skinPrice and not T.db.owned[it.id] then buy = it; break end end
      T.db.coins = 1e6
      ck(T:BuySkin(buy.id) and T:ItemSourceRecord(buy.id).first[1] == "Bought in the Appearance tab", "bought skin")
      -- a crafted cosmetic, an expedition, a real dungeon run, a quest
      local function nextSkin() for _, it in ipairs(skins) do if not T.db.owned[it.id] then return it end end end
      local s3 = nextSkin(); T:GrantSkin(s3.id, "Your party brought it home from Fishing Trip")
      ck(T:ItemSourceRecord(s3.id).first[1] == "Expedition: Fishing Trip", "expedition")
      local s4 = nextSkin(); T:GrantSkin(s4.id, "Found after The Deadmines")
      ck(T:ItemSourceRecord(s4.id).first[1] == "The Deadmines (real dungeon run)", "real dungeon")
      local s5 = nextSkin(); T:GrantSkin(s5.id, "Daily quest reward (Tap a lot)")
      ck(T:ItemSourceRecord(s5.id).first[1] == "Daily quest reward (Tap a lot)", "quest")
      -- Daily Wares in the Shop
      T:BuildShop(true)
      local id = T.db.shop.stock[1]
      if id and T:BuyItem(id) then ck(T:ItemSourceRecord(id).first[1] == "Daily Wares in the Shop", "shop") end
      -- an achievement reward
      local ach
      for _, a in ipairs(T.ACHIEVEMENTS) do if a.item and not T.db.owned[a.item] and not T.db.achievements[a.id] then ach = a; break end end
      if ach then
        local o = T.GetStat
        T.GetStat = function(self, stat) if stat == ach.stat then return ach.goal end return o(self, stat) end
        T:CheckAchievements()
        T.GetStat = o
        ck(T:ItemSourceRecord(ach.item) and T:ItemSourceRecord(ach.item).first[1] == "Achievement: " .. ach.name, "achievement")
      end
      -- a brand-new character: its starters say where they came from
      _charName = "Sourcealt"; _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")
      ck(T:ItemSourceRecord("skin_orange") and T:ItemSourceRecord("skin_orange").first[1] == "Every cat starts with it", "starter skin")
      ck(T:ItemSourceRecord(cos.id) == nil, "sources are per character")
      -- time words
      local now = 1000000000
      local words = { T.TimeAgo(now - 30, now), T.TimeAgo(now - 120, now), T.TimeAgo(now - 3 * 3600, now), T.TimeAgo(now - 30 * 3600, now),
        T.TimeAgo(now - 5 * 86400, now), T.TimeAgo(now - 90 * 86400, now) }
      ck(table.concat(words, ",") == "just now,2 minutes ago,3 hours ago,yesterday,5 days ago,3 months ago", "time words: " .. table.concat(words, ","))
      for _, l in ipairs(p) do ck(not l:find("!", 1, true), "") end
      return table.concat(p, "\n")
    ''')
    if r:
        raise AssertionError("loot sources:\n" + r)
    print("loot sources section (chests, boss drops, bought, expeditions, real dungeons, quests, shop, achievements, starters; first and latest; per character): all checks passed")
