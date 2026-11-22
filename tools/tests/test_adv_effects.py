# Adventure track F: boss-unlocked back effects and the one approved notice over the cat.
def check(seed, load_addon):
    lua = load_addon()
    lua.execute("_seed = %d; math.randomseed(_seed)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local bad = {}
      local function ck(c, m) if not c then bad[#bad + 1] = m end end
      ck(#T.BOSS_EFFECTS == 6, "six boss effects")
      for _, e in ipairs(T.BOSS_EFFECTS) do
        local it = T.ITEMS[e[1]]
        ck(it and it.slot == "effect" and it.fxLayer == "back" and it.source == "bosseffect", e[1] .. " is a back effect")
        local how = table.concat(T:HowToGet(it), " / ")
        ck(how:find("In WoW: kill ", 1, true) and how:find("Adventure: beat ", 1, true) and not how:find("!", 1, true), e[1] .. " sources: " .. how)
        local lines = {}
        T:ItemTooltip({ AddLine = function(_, l) lines[#lines + 1] = l end }, it)
        ck(table.concat(lines, " "):find("Cosmetic", 1, true), e[1] .. " is labelled cosmetic")
      end
      -- each has a drawing of its own (no class or other effect uses it) and a name unlike the class effects
      local names = {}
      for _, cl in ipairs(T.CLASSES) do for _, f in ipairs(cl.fx or {}) do names[#names + 1] = f[2] end end
      for _, e in ipairs(T.BOSS_EFFECTS) do
        local it = T.ITEMS[e[1]]
        for _, o in ipairs(T.ITEM_LIST) do
          ck(o == it or o.art ~= it.art, e[1] .. " shares its drawing with " .. o.id)
        end
        for _, nm in ipairs(names) do
          local first = it.name:match("^(%S+)")
          ck(not nm:find(first, 1, true) and not it.name:find(nm, 1, true), it.name .. " is too close to the class effect " .. nm)
        end
      end
      -- every Adventure source is a real final boss
      for boss, id in pairs(T.ADV_BOSS_EFFECTS) do
        local found = false
        for _, t in ipairs(T.TIERS) do if t.bosses[#t.bosses][1] == boss then found = true end end
        ck(found and T.ITEMS[id], boss .. " is an Adventure final boss")
      end
      local how = table.concat(T:HowToGet(T.ITEMS.fx_boss_storm), " / ")
      ck(how:find("In WoW: kill Mekgineer Thermaplugg in Gnomeregan", 1, true) and how:find("Adventure: beat Ossirian the Unscarred in Ruins of Ahn'Qiraj", 1, true), "storm sources: " .. how)
      -- beating Ragnaros in Adventure: unlocked, notice over the cat, then it fades
      local adv = T:CD().adv
      local mc
      for i, t in ipairs(T.TIERS) do if t.key == "mc" then mc = i end end
      adv.tier, adv.stage = mc, T:AdvStages(mc)
      adv.cleared[T.AdvStageCode(mc, adv.stage)] = true
      T:AdvMobKilled({ name = "Ragnaros", boss = 6, final = true, level = 69 })
      local n = T.effectNotice
      ck(T.db.owned.fx_boss_fire and n and n.shown and n.text.shown, "Ragnaros unlocks Firelord's Blaze with a notice")
      ck(n and n.text:GetText() == "|cffffffffYou unlocked|r\nFirelord's Blaze", "notice text: " .. tostring(n and n.text:GetText()))
      ck(n and n.fx.shown and tostring(n.fx.tex):find("adv\\fx_boss_fire", 1, true), "the effect plays behind the cat during the notice")
      -- it sits over the cat's own level and XP text (above the cat by default), not on it
      local rel
      if n then
        local sp = n.text.SetPoint
        n.text.SetPoint = function(self, a, r, ...) rel = r end
        _update(0.2)
        n.text.SetPoint = sp
      end
      ck(rel == T.hud, "the notice sits above the cat's own text")
      for i = 1, 30 do _update(0.2) end
      ck(n and not n.shown and not n.text.shown and not n.fx.shown, "the notice fades and hides after a few seconds")
      -- a second kill: nothing new, no notice
      T:AdvMobKilled({ name = "Ragnaros", boss = 6, final = true, level = 69 })
      ck(not n.shown, "no notice once owned")
      -- a real boss: Baron Rivendare in Stratholme
      _inInstance = "party"
      _fire("PLAYER_ENTERING_WORLD")
      _fire("ENCOUNTER_END", 1, "Baron Rivendare", 1, 5, 1)
      ck(T.db.owned.fx_boss_shadow and n.shown and n.text:GetText():find("Umbral Shroud", 1, true), "the real Baron Rivendare unlocks Umbral Shroud with a notice")
      -- two at once: the second waits for the first
      _fire("ENCOUNTER_END", 2, "Ras Frostwhisper", 1, 5, 1)
      ck(T.db.owned.fx_boss_frost and n.text:GetText():find("Umbral Shroud", 1, true) and #n.queue == 1, "a second unlock waits its turn")
      for i = 1, 30 do _update(0.2) end
      ck(n.shown and n.text:GetText():find("Frostwhisper Chill", 1, true), "then the second one shows")
      for i = 1, 30 do _update(0.2) end
      ck(not n.shown, "and fades")
      -- other rewards never show it (skins, cosmetics)
      for i = 1, 60 do if not T.db.owned.skin_defias then _fire("ENCOUNTER_END", 3, "Edwin VanCleef", 1, 5, 1) end end
      ck(not n.shown, "a skin from a real boss shows no notice")
      -- with Popups on cat off: unlocked quietly
      T.db.ui.popups = false
      _fire("ENCOUNTER_END", 4, "Emperor Dagran Thaurissan", 1, 5, 1)
      ck(T.db.owned.fx_boss_fire and not n.shown, "Popups on cat off: no notice")
      T.db.ui.popups = true
      _fire("ENCOUNTER_END", 5, "Mekgineer Thermaplugg", 1, 5, 1)
      ck(T.db.owned.fx_boss_storm and n.shown, "Thermaplugg unlocks Storm Aura")
      for i = 1, 30 do _update(0.2) end
      _inInstance = false
      _fire("ZONE_CHANGED_NEW_AREA")
      -- wearing one: it draws behind the cat
      T:GetLoadout().effect = "fx_boss_storm"
      T:RefreshAll()
      if T.cat and T.cat.ApplyAppearance then T.cat:ApplyAppearance(T:GetAppearance()) end
      local back = T.cat and T.cat.tex and T.cat.tex.fxBack
      ck(back and back.shown and tostring(back.tex):find("adv\\fx_boss_storm", 1, true), "Storm Aura draws on the back layer")
      return table.concat(bad, "; ")
    ''')
    if r:
        raise AssertionError("adventure boss effects: " + r)
    print("adventure boss effects section (6 back effects from real and Adventure bosses, the notice over the cat fades and queues, nothing else shows it, Popups on cat respected): all checks passed")
