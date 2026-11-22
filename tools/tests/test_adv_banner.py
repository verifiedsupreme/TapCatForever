# Adventure track E: the in-dungeon banner inside the main window (not a pop-up): shown only
# inside a real dungeon or raid, updates live (bosses this run, chest limits), hidden outside.
def check(seed, load_addon):
    lua = load_addon()
    lua.execute("_seed = %d; math.randomseed(_seed)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local bad = {}
      local function ck(c, m) if not c then bad[#bad + 1] = m end end
      T:ToggleWindow()
      T:RefreshDungeonBanner()
      ck(not (T.dungeonBanner and T.dungeonBanner.shown), "no banner outside instances")
      _inInstance = "party"
      _fire("PLAYER_ENTERING_WORLD")
      local b = T.dungeonBanner
      ck(b and b.shown, "the banner shows inside a dungeon while the window is open")
      local txt = b and b.text:GetText() or ""
      ck(txt:find("You're in The Deadmines.", 1, true) and txt:find("Finish it for a Dungeon Chest; 5 TapCoins a boss.", 1, true)
        and txt:find("Bosses this run: 0.", 1, true), "banner text: " .. txt)
      ck(txt:find("Real boss rewards: hover.", 1, true), "it says there are real boss rewards here: " .. txt)
      ck(not txt:find("!", 1, true), "no exclamation marks: " .. txt)
      -- it stays three short lines in a fixed height (the stats above it end about 55 px over
      -- the column's bottom), and the full lines are in its tooltip
      local function shortLines(t)
        local n, long = 0, 0
        for l in (t .. "\n"):gmatch("(.-)\n") do
          n = n + 1
          local plain = l:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", "")
          long = math.max(long, #plain)
        end
        return n, long
      end
      local nl, longest = shortLines(txt)
      ck(nl <= 3 and longest <= 52 and T.DUNGEON_BANNER_H <= 50, string.format("three short lines (%d lines, longest %d, height %s)", nl, longest, tostring(T.DUNGEON_BANNER_H)))
      ck(b:GetParent() ~= T.window, "the banner belongs to the character column")
      -- a boss dies: the count goes up while it is open
      _fire("ENCOUNTER_END", 1, "Miner Johnson", 1, 5, 1)
      txt = b.text:GetText()
      ck(txt:find("Bosses this run: 1.", 1, true), "live boss count: " .. txt)
      -- the daily limit is reached
      T.db.dungeonDay = { day = date("%Y%m%d"), n = T.DUNGEON_CHESTS_PER_DAY }
      T:RefreshDungeonBanner()
      txt = b.text:GetText()
      ck(txt:find("No chest this time", 1, true) and select(2, shortLines(txt)) <= 52, "daily limit shown: " .. txt)
      local tip0 = {}
      local G0 = GameTooltip
      GameTooltip = { AddLine = function(_, l) tip0[#tip0 + 1] = l end, SetOwner = function() end, Show = function() end }
      b.scripts.OnEnter(b)
      GameTooltip = G0
      ck(table.concat(tip0, " / "):find("dungeon chests today", 1, true), "the reason is in the tooltip: " .. table.concat(tip0, " / "))
      -- every place and state stays short
      for _, nm in ipairs({ "Scarlet Monastery", "Blackrock Depths", "Ruins of Ahn'Qiraj" }) do
        local CI = T.CurrentInstance
        T.CurrentInstance = function() local h = CI(); if h then h.name = nm end; return h end
        T:RefreshDungeonBanner()
        local _, lg = shortLines(b.text:GetText())
        ck(lg <= 52, nm .. ": lines stay short: " .. b.text:GetText())
        T.CurrentInstance = CI
      end
      T.db.dungeonDay = nil
      -- the tooltip lists the real boss rewards
      local tip = {}
      local tt = { AddLine = function(_, l) tip[#tip + 1] = l end, SetOwner = function() end, Show = function() end }
      local G = GameTooltip
      GameTooltip = tt
      b.scripts.OnEnter(b)
      GameTooltip = G
      local all = table.concat(tip, " / ")
      ck(all:find("Edwin VanCleef (Defias Bandit Cat, 15% each kill)", 1, true), "tooltip lists real boss rewards: " .. all)
      -- a raid says Raider's Hoard
      _inInstance = "raid"
      _fire("ZONE_CHANGED_NEW_AREA")
      txt = b.text:GetText()
      ck(txt:find("Finish it for a Raider's Hoard; 10 TapCoins a boss.", 1, true), "raid banner: " .. txt)
      -- the window closed: hidden; leaving: hidden
      T.window:Hide()
      T:RefreshDungeonBanner()
      ck(not b.shown, "hidden while the window is closed")
      T.window:Show()
      _inInstance = false
      _fire("ZONE_CHANGED_NEW_AREA")
      ck(not b.shown, "hidden outside instances")
      return table.concat(bad, "; ")
    ''')
    if r:
        raise AssertionError("adventure banner: " + r)
    print("adventure dungeon banner section (inside the window only in dungeons and raids, live boss count, chest limits, real boss rewards in its tooltip): all checks passed")
