# Adventure track D: rewards for killing specific real WoW bosses. Dungeon bosses through
# ENCOUNTER_END, open-world bosses (Hogger) through the units the game lets addons read, secret
# values never compared (the mock knows few events, so units are scanned directly as the
# target-changed and health events would), kill counts per character, "In WoW:" source lines, and the skins that
# moved from Adventure drops to the real bosses.
def check(seed, load_addon):
    lua = load_addon()
    lua.execute("_seed = %d; math.randomseed(_seed)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local bad = {}
      local function ck(c, m) if not c then bad[#bad + 1] = m end end
      -- nothing needs a raid: every real boss is in a dungeon or the open world
      for _, b in ipairs(T.REAL_BOSSES) do
        for _, t in ipairs(T.TIERS) do ck(not (t.raid and t.name == b.place), b.name .. " is not in a raid") end
        for _, rw in ipairs(b.rewards) do ck(T.ITEMS[rw.id] or rw.id:find("^fx_boss_"), "reward item exists: " .. rw.id) end
      end
      -- the moved skins: no longer Adventure drops, now "In WoW:"
      for _, id in ipairs({ "skin_defias", "skin_ragefire", "skin_stonewatcher" }) do
        local how = table.concat(T:HowToGet(T.ITEMS[id]), " / ")
        ck(how:find("In WoW: kill ", 1, true) and not how:find("Adventure: dropped by", 1, true), id .. ": " .. how)
        ck(T.SkinSourceTag(T.ITEMS[id]) == "WoW", id .. " cell tag")
      end
      local how = table.concat(T:HowToGet(T.ITEMS.skin_scarlet), " / ")
      ck(how:find("Adventure: dropped by High Inquisitor Whitemane", 1, true), "Adventure keeps its own boss skins: " .. how)
      for _, boss in ipairs({ "Edwin VanCleef", "Taragaman the Hungerer", "Archaedas" }) do ck(not T.SKIN_DROPS[boss], boss .. " no longer drops its skin in Adventure") end
      ck(T.SKIN_DROPS["High Inquisitor Whitemane"], "Whitemane still drops the Scarlet skin in Adventure")
      -- dungeon bosses: ENCOUNTER_END inside the instance
      _inInstance = "party"
      _fire("PLAYER_ENTERING_WORLD")
      local skinOwned = function() return T.db.owned.skin_defias end
      local n0 = T:RealBossKills("vancleef")
      _fire("ENCOUNTER_END", 1, "Edwin VanCleef", 1, 5, 0)
      ck(T:RealBossKills("vancleef") == n0, "a wipe (success 0) is not a kill")
      _fire("ENCOUNTER_END", 1, _SECRET, 1, 5, 1)
      _fire("ENCOUNTER_END", 1, "Edwin VanCleef", 1, 5, _SECRET)
      ck(T:RealBossKills("vancleef") == n0, "secret names or results are skipped without comparing them")
      for i = 1, 80 do if not skinOwned() then _fire("ENCOUNTER_END", 1, "Edwin VanCleef", 1, 5, 1) end end
      ck(skinOwned() and T:RealBossKills("vancleef") >= 1, "killing the real Edwin VanCleef can give the Defias Bandit Cat")
      local k = T:RealBossKills("vancleef")
      how = table.concat(T:HowToGet(T.ITEMS.rb_arugal_hood), " / ")
      ck(how:find("In WoW: kill Archmage Arugal in Shadowfang Keep with TapCatForever on, 20% chance each kill", 1, true), "Arugal's hood source: " .. how)
      _fire("ENCOUNTER_END", 2, "Arugal", 1, 5, 1)
      ck(T:RealBossKills("arugal") == 1, "an alias name counts")
      how = table.concat(T:HowToGet(T.ITEMS.rb_arugal_hood), " / ")
      ck(T.db.owned.rb_arugal_hood or how:find("You have killed Archmage Arugal once on this character", 1, true), "kills are tracked: " .. how)
      _inInstance = false
      _fire("ZONE_CHANGED_NEW_AREA")
      -- open-world: Hogger through the target
      local unit = { name = "Hogger", dead = false, denied = false, combat = true, guid = "Creature-0-1-2-3-448-0001" }
      local saved = { UnitExists, UnitName, UnitIsDead, UnitIsTapDenied, UnitAffectingCombat, UnitGUID }
      UnitExists = function(u) return u == "player" or (u == "target" and unit ~= nil) end
      UnitName = function(u) if u == "target" and unit then return unit.name end return _charName end
      UnitIsDead = function(u) return u == "target" and unit and unit.dead or false end
      UnitIsTapDenied = function(u) return u == "target" and unit and unit.denied end
      UnitAffectingCombat = function(u) return unit and unit.combat end
      UnitGUID = function(u) if u == "target" and unit then return unit.guid end end
      local h0 = T:RealBossKills("hogger")
      -- dead without being fought first: not yours
      unit.dead = true
      T:RealBossScanUnit("target")
      ck(T:RealBossKills("hogger") == h0, "a dead Hogger you never fought doesn't count")
      -- fought and seen dead: counts once, gives the bandana
      unit.dead = false
      T:RealBossScanUnit("target")
      _clock = _clock + 20
      unit.dead = true
      T:RealBossScanUnit("target")
      _fire("PLAYER_REGEN_ENABLED")
      ck(T:RealBossKills("hogger") == h0 + 1 and T.db.owned.rb_hogger_bandana, "killing Hogger counts once and gives the bandana: " .. T:RealBossKills("hogger"))
      -- tapped by someone else: not yours
      unit.guid, unit.dead, unit.denied = "Creature-0-1-2-3-448-0002", false, true
      T:RealBossScanUnit("target")
      unit.dead = true
      T:RealBossScanUnit("target")
      ck(T:RealBossKills("hogger") == h0 + 1, "someone else's Hogger doesn't count")
      -- a secret name is skipped (comparing it would raise an error in the mock)
      unit.name, unit.dead, unit.denied = _SECRET, false, false
      T:RealBossScanUnit("target")
      -- PARTY_KILL with the boss's GUID counts too
      _clock = _clock + 400
      unit.name, unit.guid, unit.dead, unit.denied = "Hogger", "Creature-0-1-2-3-448-0003", false, false
      T:RealBossScanUnit("target")
      T:RealBossPartyKill("Player-1", "Creature-0-1-2-3-448-0003")
      ck(T:RealBossKills("hogger") == h0 + 2, "PARTY_KILL with the boss's GUID counts")
      UnitExists, UnitName, UnitIsDead, UnitIsTapDenied, UnitAffectingCombat, UnitGUID = unpack(saved)
      -- the new cosmetics are cosmetic only and labelled "In WoW:"
      for _, id in ipairs({ "rb_hogger_bandana", "rb_arugal_hood", "rb_drakkisath_crown" }) do
        local it = T.ITEMS[id]
        ck(it and it.source == "realboss", id .. " exists")
        local lines = {}
        local tt = { AddLine = function(_, l) lines[#lines + 1] = l end }
        T.db.owned[id] = nil
        T:ItemTooltip(tt, it)
        local all = table.concat(lines, " / ")
        ck(all:find("Cosmetic", 1, true) and all:find("In WoW: kill ", 1, true) and not all:find("!", 1, true), id .. " tooltip: " .. all)
      end
      return table.concat(bad, "; ")
    ''')
    if r:
        raise AssertionError("adventure real bosses: " + r)
    print("adventure real bosses section (ENCOUNTER_END kills, Hogger by target and PARTY_KILL, secret values skipped, kill counts, In WoW: lines, 3 skins moved from Adventure): all checks passed")
