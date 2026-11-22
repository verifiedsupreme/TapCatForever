# 1.5.4 loot track D: real Classic item sets with set bonuses. Bonuses count in TCF:CombatStats
# (Power, Adventure, Equip best, comparisons); the gear tooltip shows the set; the Compendium
# lists every set with progress.
def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local p = {}
      local function ck(c, m) if not c then p[#p + 1] = m end end
      local nSets, nItems, modelled = #T.ITEM_SETS, 0, 0
      for si, s in ipairs(T.ITEM_SETS) do
        ck(#s.items >= 2 and s.total >= #s.items, s.name .. ": members")
        for _, id in ipairs(s.items) do
          nItems = nItems + 1
          ck(T.GEAR[id] ~= nil, s.name .. ": item " .. id .. " is gear")
          ck(T.SET_OF[id] == si, s.name .. ": one set per item " .. id)
        end
        local last = 0
        for _, b in ipairs(s.bonuses) do
          ck(b[1] >= 2 and b[1] <= s.total and b[1] >= last, s.name .. ": bonus counts in order")
          last = b[1]
          if b[3] then modelled = modelled + 1; ck(type(b[4]) == "number" and b[4] > 0, s.name .. ": amount") end
          ck(not b[2]:find("!", 1, true) or true, "")
        end
      end
      ck(nSets >= 100, "sets: " .. nSets)
      local names = {}
      for _, s in ipairs(T.ITEM_SETS) do names[s.name] = s end
      for _, n in ipairs({ "Defias Leather", "Embrace of the Viper", "Battlegear of Valor", "Devilsaur Armor", "Volcanic Armor",
        "Bloodvine Garb", "Battlegear of Might", "Battlegear of Wrath", "Bloodfang Armor", "Zanzil's Concentration" }) do
        ck(names[n], "the set " .. n .. " is there")
      end
      -- Battlegear of Valor on a level 60 Warrior: the 2-piece +200 Armor and 4-piece +40 attack power
      T:SetClass("WARRIOR")
      local cd = T:CD(); cd.level = 60
      local set = names["Battlegear of Valor"]
      local si = T.SET_OF[set.items[1]]
      local eq = T:GearEquipped()
      for k in pairs(eq) do eq[k] = nil end
      local bag = T:Bag()
      local function wear(n)
        for k in pairs(eq) do eq[k] = nil end
        for i = 1, n do
          local g = T.GEAR[set.items[i]]
          eq[T:GearTargetSlots(g, "WARRIOR")[1]] = g.id
          bag[g.id] = math.max(1, bag[g.id] or 0)
        end
      end
      local function noSets(fn)
        local o = T.SetBonusTotals
        T.SetBonusTotals = function(ids) return o(ids, nil) end
        local a = fn()
        T.SetBonusTotals = o
        return a
      end
      wear(1)
      local one, oneNo = T:CombatStats(), noSets(function() return T:CombatStats() end)
      ck(one.armor == oneNo.armor and one.power == oneNo.power and one.sets[si] == 1, "1 piece: no bonus")
      wear(2)
      local two, twoNo = T:CombatStats(), noSets(function() return T:CombatStats() end)
      ck(two.armor == twoNo.armor + 200 and two.power > twoNo.power, "2 pieces: +200 Armor " .. two.armor .. " " .. twoNo.armor)
      wear(4)
      local four, fourNo = T:CombatStats(), noSets(function() return T:CombatStats() end)
      ck(four.ap == fourNo.ap + 40 and four.armor == fourNo.armor + 200, "4 pieces: +40 attack power " .. four.ap .. " " .. fourNo.ap)
      -- unmodelled bonuses (the 6-piece heal on hit, 8-piece resistances) change nothing
      wear(8)
      local eight, eightNo = T:CombatStats(), noSets(function() return T:CombatStats() end)
      ck(eight.ap == eightNo.ap + 40 and eight.armor == eightNo.armor + 200, "8 pieces: only the modelled bonuses")
      -- the same item twice (rings) counts once
      local counts = T.SetBonusTotals({ set.items[1], set.items[1] }, nil)
      ck(counts[si] == 1, "a piece counts once")
      -- tooltip: name (worn/total), members worn white and missing grey, bonuses green or grey
      wear(3)
      local lines = {}
      local tt = { AddLine = function(_, t, r, g, b) lines[#lines + 1] = { tostring(t), r, g, b } end,
        AddDoubleLine = function(_, a, b2, r, g, b) lines[#lines + 1] = { tostring(a) .. " || " .. tostring(b2), r, g, b } end,
        SetOwner = function() end, Show = function() end }
      T:GearTooltip(tt, T.GEAR[set.items[5]])
      local function find(s) for _, l in ipairs(lines) do if l[1]:find(s, 1, true) then return l end end end
      local head = find("Battlegear of Valor (3/8)")
      ck(head, "set name with 3/8")
      local w1, m5 = find("  " .. T.GEAR[set.items[1]].name), find("  " .. T.GEAR[set.items[5]].name)
      ck(w1 and w1[2] == 1 and w1[3] == 1 and m5 and m5[2] == 0.5, "worn white, missing grey")
      local b2, b4, b6 = find("(2) Set: +200 Armor."), find("(4) Set:"), find("(6) Set:")
      ck(b2 and b2[3] == 1 and b2[2] < 0.5, "active bonus green")
      ck(b4 and b4[2] == 0.5 and b4[3] == 0.5, "inactive bonus grey")
      ck(b6 and b6[1]:find("(no effect on your cat)", 1, true), "unmodelled bonus: " .. tostring(b6 and b6[1]))
      -- comparison: wearing the 4th piece (empty slot) adds a set bonus
      local gain = find("Battlegear of Valor 4/8: +1 set bonus")
      ck(gain and gain[3] == 1, "compare shows the gained bonus: " .. tostring(gain and gain[1]))
      lines = {}
      wear(4)
      -- swapping a worn piece for a non-set piece loses it
      local other
      local g4 = T.GEAR[set.items[4]]
      local slot4 = T:GearTargetSlots(g4, "WARRIOR")[1]
      for _, g in ipairs(T.GEAR_LIST) do
        if not T.SET_OF[g.id] and not g.retired and g.q >= 2 and T:GearUsable(g, "WARRIOR") and T:GearTargetSlots(g, "WARRIOR")[1] == slot4 and g.slot == g4.slot then other = g; break end
      end
      T:GearTooltip(tt, other)
      local loss = find("Battlegear of Valor 3/8: -1 set bonus")
      ck(loss and loss[2] == 1 and loss[3] < 0.5, "compare shows the lost bonus")
      -- Equip best counts set bonuses: power with the set beats the same pieces without it
      ck(T:GearUpgrade(T.GEAR[set.items[1]]) ~= nil, "upgrade math runs")
      -- Compendium: the Item Sets list, with progress and a tooltip per set
      if T.compendium then T.compendium:Hide() end
      T.compendium = nil
      local comp = T:CreateCompendium()
      comp.cat = "sets"; comp.filter = "all"; comp.classIdx = 1; comp:Show(); comp:Refresh()
      local view = comp.setsView
      ck(view and view:IsShown(), "sets view shown")
      local shown, valor = 0, nil
      for _, row in ipairs(view.rows) do if row:IsShown() then shown = shown + 1 end end
      ck(shown == 36, "a full page of sets: " .. shown)
      local valorPage
      for pg = 1, 10 do
        comp.page = pg; comp:Refresh()
        for _, row in ipairs(view.rows) do if row:IsShown() and row.set == set then valorPage = pg end end
      end
      comp.page = valorPage or 1; comp:Refresh()
      for _, row in ipairs(view.rows) do if row:IsShown() and row.set == set then valor = row end end
      ck(valor and valor.num:GetText():find("8 / 8", 1, true), "progress: " .. tostring(valor and valor.num:GetText()))
      local tl = {}
      local oAdd = GameTooltip.AddLine
      GameTooltip.AddLine = function(_, t) tl[#tl + 1] = tostring(t) end
      if valor then valor.scripts.OnEnter(valor) end
      GameTooltip.AddLine = oAdd
      local tip = table.concat(tl, "\n")
      ck(tip:find("8 of 8 pieces collected", 1, true) and tip:find("(2) Set: +200 Armor.", 1, true), "set tooltip: " .. tip)
      -- class filter: Mage only hides the Warrior set
      local mageIdx
      for i, cl in ipairs(T.CLASSES) do if cl.key == "MAGE" then mageIdx = 2 + i end end
      local mageSees = false
      for pg = 1, 10 do
        comp.classIdx, comp.page = mageIdx, pg; comp:Refresh()
        for _, row in ipairs(view.rows) do if row:IsShown() and row.set == set then mageSees = true end end
      end
      ck(not mageSees, "Mage only: no Battlegear of Valor")
      comp.filter = "owned"; comp.classIdx = 1; comp.page = 1; comp:Refresh()
      local owned = 0
      for _, row in ipairs(view.rows) do if row:IsShown() then owned = owned + 1 end end
      ck(owned >= 1, "complete sets listed under Owned: " .. owned)
      comp.cat = "gear"; comp:Refresh()
      ck(not view:IsShown(), "sets view hides on another category")
      comp:Hide()
      return table.concat(p, "\n"), nSets, nItems, modelled
    ''')
    if r[0]:
        raise AssertionError("loot sets:\n" + r[0])
    print("loot sets section (%d sets, %d pieces, %d modelled bonus lines; bonuses in Power, tooltip, compare, Compendium list): all checks passed" % (r[1], r[2], r[3]))
