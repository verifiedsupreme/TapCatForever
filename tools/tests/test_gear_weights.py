# 1.6.5: Equip best and every "+N Power" comparison follow each class's own stats, like WoW: a Mage takes
# the Intellect piece over the Stamina piece, a Warrior the Strength piece, a Hunter the Agility piece.
# Two copies of a real item of the right armour type get the same item level and different stats.

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      local function pair(class, sub, slot, good, bad)
        local base
        for _, it in ipairs(T.GEAR_LIST) do
          if it.slot == slot and it.sub == sub and it.req <= 30 and it.req >= 20 and T:GearUsable(it, class) then base = it; break end
        end
        if not base then return nil end
        local function copy(id, stats)
          local c = {}
          for k, v in pairs(base) do c[k] = v end
          c.id, c.stats, c.base, c.name = id, stats, nil, "Test " .. id
          c.stats.arm = base.stats and base.stats.arm or (T.GearStats(base).arm)
          T.GEAR[id] = c
          return c
        end
        return copy(9900001, good), copy(9900002, bad)
      end
      local cases = {
        { "MAGE", "cloth", "HEAD", { int = 16, sta = 4 }, { sta = 20 } },
        { "WARLOCK", "cloth", "HEAD", { int = 10, sp = 6, sta = 4 }, { sta = 20 } },
        { "PRIEST", "cloth", "HEAD", { int = 12, spi = 8 }, { sta = 20 } },
        { "WARRIOR", "mail", "CHEST", { str = 16, sta = 4 }, { sta = 20 } },
        { "HUNTER", "mail", "CHEST", { agi = 16, sta = 4 }, { sta = 20 } },
        { "ROGUE", "leather", "CHEST", { agi = 16, sta = 4 }, { sta = 20 } },
      }
      for _, c in ipairs(cases) do
        local class = c[1]
        T:SetClass(class)
        local cd = T:CD(class)
        cd.level = 30
        cd.gear = {}
        if class == "HUNTER" then
          -- a hunter shoots: its Agility goes into its shots (a bow from the list)
          for _, it in ipairs(T.GEAR_LIST) do
            if it.slot == "RANGED" and it.sub == "bow" and it.req <= 30 and it.req >= 20 then cd.gear.RANGED = it.id; break end
          end
        end
        local bag = T:Bag(class)
        for k in pairs(bag) do bag[k] = nil end
        local good, bad = pair(class, c[2], c[3], c[4], c[5])
        ck(good, class .. ": a test item")
        if good then
          bag[good.id], bag[bad.id] = 1, 1
          local keepRanged = cd.gear.RANGED
          T:EquipBestGear(class)
          ck(cd.gear[c[3]] == good.id, class .. " takes its own stat over Stamina (wears " .. tostring(cd.gear[c[3]]) .. ")")
          cd.gear = { RANGED = keepRanged }
          local dg, db = T:GearUpgrade(good, class), T:GearUpgrade(bad, class)
          ck(dg and db and dg > db, class .. ": the +N Power arrows agree: " .. tostring(dg) .. " > " .. tostring(db))
        end
        T.GEAR[9900001], T.GEAR[9900002] = nil, nil
      end
      -- a caster's own gear Intellect adds to its spells; without gear it fights as before
      T:SetClass("MAGE")
      local cd = T:CD("MAGE"); cd.gear = {}
      local s0 = T:CombatStats("MAGE")
      ck(s0.dps > 0 and s0.power > 0, "a bare mage has damage and Power")
      return table.concat(fails, "; ")
    ''')
    if r:
        raise AssertionError("gear weights: " + r)
    print("gear weights section (Equip best and the +N Power arrows follow each class's stats: Intellect for casters, Strength for warriors, Agility for hunters and rogues, over Stamina): all checks passed")
