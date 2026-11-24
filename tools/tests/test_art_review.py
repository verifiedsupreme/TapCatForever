# 1.6 art, review fixes: a set piece names its boss once (this track's line, or Adventure's once
# the adv track is merged), set pieces keep their boss in it.bossName (it.boss is a number on gear),
# the "Animated cosmetics" check box on the Appearance tab, particles following a cat resize, the
# light glints on Epic cosmetics, and the racial slot's short name and own tooltip.


def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(ok, msg) if not ok then fails[#fails + 1] = msg end end
      local db, cat = T.db, T.cat
      local function nLayers(c) return c.anim and #c.anim.layers or 0 end
      local function shownAnimTex(c)
        local n = 0
        for _, list in pairs(c.anim and c.anim.tex or {}) do for _, t in ipairs(list) do if t:IsShown() then n = n + 1 end end end
        return n
      end
      local function count(s, sub) local _, n = s:gsub((sub:gsub("%p", "%%%0")), ""); return n end

      -- 1. set pieces: bossName (a string), never it.boss (gear's number), and code comparing it.boss stays safe
      local nSet = 0
      for _, it in ipairs(T.ITEM_LIST) do
        if it.source == "set" then
          ck(it.boss == nil, it.id .. ": no it.boss on a set piece")
          -- (1.7.0) the crafted profession sets (it.craftSet) come from a profession, not a boss
          if it.craftSet then ck(it.bossName == nil, it.id .. ": a crafted set piece has no boss")
          else nSet = nSet + 1; ck(type(it.bossName) == "string", it.id .. ": bossName") end
          local ok = pcall(function() return it.boss and it.boss > 0 end)
          ck(ok, it.id .. ": comparing it.boss does not error")
        end
      end
      ck(nSet == 66, "66 set pieces: " .. nSet)

      -- 2. the boss line once, on its own and with the Adventure track's line for TCF.BOSS_COSMETICS
      local crown = T.ITEMS.set_mc_crown
      local how = table.concat(T:HowToGet(crown), " | ")
      ck(count(how, "Ragnaros in Molten Core") == 1, "alone: the boss named once: " .. how)
      ck(how:find("Molten Core set (0/6), cosmetic only", 1, true), "alone: the set line: " .. how)
      if not T.BossCosmeticSources then
        -- what the adv track adds (AdventureSources.lua): its own boss line from TCF.BOSS_COSMETICS
        T.BossCosmeticSources = function(self, id)
          local out = {}
          for boss, list in pairs(T.BOSS_COSMETICS) do for _, x in ipairs(list) do if x == id then out[#out + 1] = { boss, "Molten Core" } end end end
          return out
        end
        local how0 = T.HowToGet
        T.HowToGet = function(self, it)
          local out = how0(self, it)
          for _, s in ipairs(self:BossCosmeticSources(it.id)) do
            out[#out + 1] = string.format("Adventure: %s in %s gives it every time you beat it, until you have it", s[1], s[2])
          end
          return out
        end
        how = table.concat(T:HowToGet(crown), " | ")
        ck(count(how, "Ragnaros in Molten Core") == 1, "with Adventure's line: the boss named once: " .. how)
        ck(how:find("Molten Core set (0/6)", 1, true), "with Adventure's line: the set line stays: " .. how)
        T.HowToGet, T.BossCosmeticSources = how0, nil
      end

      -- 3. animations on or off (db.ui.anim, the Appearance tab's check box)
      ck(T:AnimEnabled(), "animations on by default")
      for _, it in ipairs(T.COSMETIC_SET_BY_KEY.mc.items) do db.owned[it.id] = 1; T:Equip(it) end
      db.owned.skin_diamond = 1; db.look.skin = "skin_diamond"
      cat:ApplyAppearance(T:GetAppearance())
      for i = 1, 10 do _update(0.05) end
      local on = nLayers(cat)
      ck(on >= 6, "layers with the Molten Core set and Diamond Cat: " .. on)
      if not T.window then T:ToggleWindow() end
      local box = T.UI.animCheckBox
      ck(box and box:GetChecked(), "the Appearance tab has the Animated cosmetics box, ticked")
      if box then box:SetChecked(false); box:GetScript("OnClick")(box) end
      ck(db.ui.anim == false and not T:AnimEnabled(), "unticking turns animations off")
      ck(nLayers(cat) == 0 and shownAnimTex(cat) == 0, "no animated layers while off: " .. nLayers(cat) .. ", " .. shownAnimTex(cat))
      cat:ApplyAppearance(T:GetAppearance()); for i = 1, 10 do _update(0.05) end
      ck(nLayers(cat) == 0 and shownAnimTex(cat) == 0, "a new look stays still while off")
      ck(cat.vt.head_f:IsShown() or cat.vt.head_a:IsShown(), "the pieces themselves still show")
      if box then box:SetChecked(true); box:GetScript("OnClick")(box) end
      ck(T:AnimEnabled() and nLayers(cat) == on, "ticking it again brings them back: " .. nLayers(cat))

      -- 4. particles and glints follow a resize across the small-cat size
      local size0 = cat.size
      cat:SetSize(60)
      local smallN = nLayers(cat)
      cat:SetSize(160)
      local bigN = nLayers(cat)
      ck(smallN < bigN, "growing a cat past the small size adds its glints (" .. smallN .. " < " .. bigN .. ")")
      cat:SetSize(60); ck(nLayers(cat) == smallN, "shrinking takes them away again")
      cat:SetSize(size0)
      for i = 1, 10 do _update(0.05) end

      -- 5. Epic cosmetics: helms, chest pieces and shoulders glint; capes, held items and set pieces do not
      local nEpic, nGlint = 0, 0
      for _, it in ipairs(T.ITEM_LIST) do
        if it.rarity == 4 and not it.gear and it.source ~= "set" and it.slot ~= "skin" and it.slot ~= "fur" and it.slot ~= "effect" then
          nEpic = nEpic + 1
          local a = T.AnimOf(it)
          if it.slot == "head" or it.slot == "chest" or it.slot == "shoulder" then
            ck(a, "Epic " .. it.slot .. " has an effect: " .. it.id)
            if a then nGlint = nGlint + 1 end
          end
        end
      end
      ck(nGlint >= 20, "Epic pieces with glints: " .. nGlint .. " of " .. nEpic)
      local epicHead
      for _, it in ipairs(T.ITEM_LIST) do
        if not epicHead and it.rarity == 4 and it.slot == "head" and not it.gear and it.source ~= "set" and not it.class and T.ITEM_ANIM[it.id] == nil then epicHead = it end
      end
      ck(epicHead, "an Epic helm to wear")
      if epicHead then
        for _, it in ipairs(T.COSMETIC_SET_BY_KEY.mc.items) do T:Unequip(it.slot) end
        db.look.skin = nil
        db.owned[epicHead.id] = 1; T:Equip(epicHead)
        cat:ApplyAppearance(T:GetAppearance())
        ck(nLayers(cat) == 1, "the Epic helm adds one light layer: " .. nLayers(cat))
        local e = T.VEC["cos:" .. epicHead.art .. ":f"] or T.VEC["cos:" .. epicHead.art .. ":a"]
        -- where the glints are put (the mock's GetPoint does not keep points)
        local inside, seen = true, 0
        for _, list in pairs(cat.anim.tex) do
          for _, t in ipairs(list) do
            local set = t.SetPoint
            t.SetPoint = function(self, p, rel, rp, x, y)
              if p == "CENTER" and x and e then
                seen = seen + 1
                local s = cat.size / 512
                local cx, cy = x / s, -y / s
                if cx < e[2] - 1 or cx > e[2] + e[4] + 1 or cy < e[3] - 1 or cy > e[3] + e[5] + 1 then inside = false end
              end
              return set(self, p, rel, rp, x, y)
            end
          end
        end
        for i = 1, 80 do _update(0.1) end
        ck(seen > 0 and inside, "Epic glints stay on the helm (" .. seen .. " placed)")
        T:Unequip("head")
      end

      -- 6. the racial slot: a short name that fits the Compendium, and its own tooltip line
      local race = T.SLOT_BY_KEY.race
      ck(race.name == "Racial", "short slot name: " .. race.name)
      ck(race.desc and race.desc:find("accessory", 1, true) and not race.desc:find("real gear", 1, true) and not race.desc:find("!", 1, true), "racial slot tooltip")
      return table.concat(fails, "\n")
    ''')
    if r:
        raise AssertionError("art review section:\n" + r)
    # the Epic glint uses a sprite that exists
    import os
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    assert os.path.exists(os.path.join(root, "Art", "v", "a_spark.tga")), "art review section: a_spark.tga"
    print("art review section (boss named once with or without Adventure's line, bossName on 66 set pieces, Animated cosmetics box, resize across the small size, Epic glints, racial slot name): all checks passed")
