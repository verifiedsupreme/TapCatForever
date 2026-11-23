# 1.6 art: the shoulder slot, the racial accessory's own slot, the animation layers (CatAnim.lua),
# the Molten Core set (Sets/MoltenCore.lua) and the effects on expensive skins and cosmetics.
import os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")


def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(ok, msg) if not ok then fails[#fails + 1] = msg end end
      local cat = T.cat
      -- the cat's frames get mask textures (the mock has none) so scrolling layers are built and checked
      local masks = 0
      local function withMasks(c)
        for _, f in ipairs(c.vframes) do
          f.CreateMaskTexture = function(self, ...) local m = self:CreateTexture(...); m.isMask = true; return m end
        end
      end
      local function spyMasks(c)
        for _, list in pairs(c.anim and c.anim.tex or {}) do
          for _, t in ipairs(list) do t.AddMaskTexture = function(self, m) assert(m.isMask, "masked with a mask texture"); masks = masks + 1 end end
        end
      end
      local function nLayers(c) return c.anim and #c.anim.layers or 0 end
      local function shownAnimTex(c)
        local n = 0
        for _, list in pairs(c.anim and c.anim.tex or {}) do for _, t in ipairs(list) do if t:IsShown() then n = n + 1 end end end
        return n
      end
      withMasks(cat)

      -- 1. slots: shoulders after back, the racial accessory after the accessory
      local order = {}
      for i, s in ipairs(T.SLOTS) do order[s.key] = i end
      ck(order.shoulder == order.back + 1, "shoulder slot after back")
      ck(order.race == order.acc + 1, "racial slot after accessory")
      ck(T.SLOT_BY_KEY.race and not T.SLOT_BY_KEY.race.look and not T.SLOT_BY_KEY.shoulder.look, "both slots are saved per class")
      for _, it in ipairs(T.ITEM_LIST) do
        if it.source == "race" then ck(it.slot == "race", "racial item in the racial slot: " .. it.id) end
      end

      -- 2. racial accessory and sunglasses together
      local db = T.db
      db.coins = db.coins + 5000
      ck(T:BuyRaceAccessory(), "buy the racial accessory")
      local lo = T:GetLoadout()
      ck(lo.race == "race_orc" and lo.acc == nil, "bought racial piece goes to its own slot")
      db.owned.acc_shades = 1
      T:Equip(T.ITEMS.acc_shades)
      local look = T:GetAppearance()
      ck(look.acc and look.acc.id == "acc_shades" and look.race and look.race.id == "race_orc", "shades and tusks worn together")
      ck(cat.vt.race_a:IsShown() or cat.vt.race_f:IsShown(), "the cat draws the racial accessory")
      ck(cat.vt.acc_a:IsShown() or cat.vt.acc_f:IsShown(), "the cat draws the shades")
      -- face accessories sit over the racial accessory, neck ones under it
      local dl = {}
      cat.vt.acc_a.SetDrawLayer = function(self, l, s) dl.l, dl.s = l, s end
      T:RefreshAll(); cat:ApplyAppearance(T:GetAppearance())
      ck(dl.s and dl.s > -2, "shades drawn above the racial accessory (sublevel " .. tostring(dl.s) .. ")")
      db.owned.acc_bowtie = 1; T:Equip(T.ITEMS.acc_bowtie); cat:ApplyAppearance(T:GetAppearance())
      ck(dl.s and dl.s < -4, "bow tie drawn under the racial accessory (sublevel " .. tostring(dl.s) .. ")")
      T:Equip(T.ITEMS.acc_shades)
      -- the setting hides the racial piece only
      db.ui.racial = false
      look = T:GetAppearance()
      ck(look.race == nil and look.acc and look.acc.id == "acc_shades", "hiding the racial accessory keeps the shades")
      db.ui.racial = true
      -- an old save wore the racial piece as the accessory
      lo.acc, lo.race = "race_orc", nil
      T:MigrateRaceSlot(db)
      ck(lo.race == "race_orc" and lo.acc == nil, "old saves move the racial piece to its slot")
      T:Equip(T.ITEMS.acc_shades)

      -- 3. party: both travel, old messages still show the racial piece
      local payload = T:PartyPayload()
      ck(payload:find("x=race_orc", 1, true) and payload:find("a=acc_shades", 1, true), "payload carries shades and racial piece: " .. payload)
      _group = { party1 = { "Alice", nil } }
      _fire("GROUP_ROSTER_UPDATE")
      _fire("CHAT_MSG_ADDON", "TapCatFvr", "U1;" .. payload:gsub("z=%x+$", "z=abcde"), "PARTY", "Alice-Forever")   -- Alice has her own session tag
      local m = T:PartyMembers()[1]
      ck(m and m.look.race and m.look.race.id == "race_orc" and m.look.acc and m.look.acc.id == "acc_shades", "a friend sees both")
      _fire("CHAT_MSG_ADDON", "TapCatFvr", "U1;MAGE;20;;;;a=race_troll", "PARTY", "Alice-Forever")
      m = T:PartyMembers()[1]
      ck(m and m.look.race and m.look.race.id == "race_troll" and not m.look.acc, "a pre-1.6 message (a=racial) shows it in the racial slot")

      -- 4. shoulders: real shoulder gear shows as pauldrons, and travels to friends
      local sh
      for _, g in ipairs(T.GEAR_LIST) do
        if g.q >= 2 and g.sub == "plate" and (T:GearTargetSlots(g, T.db.class) or {})[1] == "SHOULDER" then sh = g; break end
      end
      if not sh then for _, g in ipairs(T.GEAR_LIST) do if g.slot == "SHOULDER" then sh = g; break end end end
      ck(sh ~= nil, "a shoulder item exists")
      local eq = T:GearEquipped()
      eq.SHOULDER = sh.id
      look = T:GetAppearance()
      ck(look.shoulder and look.shoulder.gear and look.shoulder.art:find("^shoulder_"), "gear shoulders in the look: " .. tostring(look.shoulder and look.shoulder.art))
      cat:ApplyAppearance(look)
      ck(cat.vt.shoulder_a:IsShown() or cat.vt.shoulder_f:IsShown(), "the cat draws the pauldrons")
      payload = T:PartyPayload()
      ck(payload:find("s=#" .. sh.id, 1, true), "payload carries the shoulders")
      _fire("CHAT_MSG_ADDON", "TapCatFvr", "U1;" .. payload:gsub("z=%x+$", "z=abcde"), "PARTY", "Alice-Forever")   -- Alice has her own session tag
      m = T:PartyMembers()[1]
      ck(m and m.look.shoulder and m.look.shoulder.gear, "a friend sees the shoulders")
      _group = nil; _fire("GROUP_ROSTER_UPDATE")

      -- 5. the Molten Core set
      local set = T.COSMETIC_SET_BY_KEY.mc
      ck(set and #set.items == 6, "Molten Core set has 6 pieces")
      local mcBosses = {}
      for _, t in ipairs(T.TIERS) do if t.key == "mc" then for _, b in ipairs(t.bosses) do mcBosses[b[1]] = true end end end
      local slots, bosses = {}, {}
      for _, it in ipairs(set.items) do
        ck(it.source == "set" and T.ITEMS[it.id] == it, "set piece registered: " .. it.id)
        ck(mcBosses[it.bossName], "boss is a Molten Core boss in Adventure: " .. tostring(it.bossName))
        ck(not bosses[it.bossName], "one piece per boss: " .. tostring(it.bossName)); bosses[it.bossName] = true
        slots[it.slot] = true
        local list = T.BOSS_COSMETICS[it.bossName]
        local found = false
        for _, id in ipairs(list or {}) do if id == it.id then found = true end end
        ck(found, "BOSS_COSMETICS lists " .. it.id)
        if it.slot ~= "effect" then ck(T.VEC["cos:" .. it.art .. ":f"], "drawing for " .. it.id) end
        ck(T.AnimOf(it), "animated: " .. it.id)
        local how = table.concat(T:HowToGet(it), " | ")
        ck(how:find("Molten Core set (", 1, true) and how:find("Adventure: " .. it.bossName .. " in Molten Core", 1, true), "how to get " .. it.id .. ": " .. how)
        ck(not how:find("!", 1, true), "plain text: " .. how)
      end
      for _, s in ipairs({ "head", "shoulder", "chest", "back", "main", "effect" }) do ck(slots[s], "set has a " .. s) end
      ck(T.ITEMS.set_mc_crown.bossName == "Ragnaros" and T.ITEMS.set_mc_cape.bossName == "Magmadar" and T.ITEMS.set_mc_chest.bossName == "Garr", "bosses as designed")
      -- set pieces never come from chests, the shop or random finds
      for i = 1, 200 do
        local it = T:RollItem(4, true) or T:RollItem(5, true)
        ck(not it or it.source ~= "set", "chests never roll a set piece")
      end
      -- wear the whole set: every layer kind runs, nothing errors, and it stays cheap
      for _, it in ipairs(set.items) do db.owned[it.id] = 1; T:Equip(it) end
      look = T:GetAppearance()
      ck(look.head.id == "set_mc_crown" and look.shoulder.id == "set_mc_shoulders" and look.effect.id == "set_mc_aura", "whole set worn")
      cat:ApplyAppearance(look)
      spyMasks(cat); cat:ApplyAppearance(look)
      local layersMC = nLayers(cat)
      ck(layersMC >= 12, "set layers built: " .. layersMC)
      for i = 1, 40 do _update(0.05) end
      ck(shownAnimTex(cat) <= 60, "the full set uses few textures: " .. shownAnimTex(cat))
      ck(masks >= 1, "lava flows inside the chest's seams (a masked scroll)")
      -- paws: the hammer's flames follow the paw up and down
      cat:SetPaw("R", true); cat:SetPaw("R", false)
      -- the old pixel cat still has a texture for every piece
      for _, it in ipairs(set.items) do ck(it.art, "pixel art name") end

      -- every set (tools/sets/*.py): pieces from different bosses of its own zone, drawings and animations present
      for _, def in ipairs(T.COSMETIC_SETS) do
        local zoneBosses = {}
        for _, t in ipairs(T.TIERS) do if t.key == def.zone then for _, b in ipairs(t.bosses) do zoneBosses[b[1]] = true end end end
        ck(next(zoneBosses), def.key .. ": zone " .. tostring(def.zone) .. " is an Adventure zone")
        local seen = {}
        for _, it in ipairs(def.items) do
          ck(it.bossName and zoneBosses[it.bossName], def.key .. ": " .. it.id .. " comes from a boss of the zone (" .. tostring(it.bossName) .. ")")
          ck(not seen[it.bossName], def.key .. ": one piece per boss"); seen[it.bossName or "?"] = true
          ck(it.id:find("^set_" .. def.key .. "_"), def.key .. ": item ids start with set_" .. def.key .. "_")
          ck(it.slot == "effect" or T.VEC["cos:" .. it.art .. ":f"], def.key .. ": drawing for " .. it.id)
          ck(not it.name:find("!", 1, true), def.key .. ": plain name " .. it.name)
          local layers = T.AnimOf(it) or {}
          ck(#layers <= 6, def.key .. ": at most 6 animated layers on " .. it.id)
          for _, L in ipairs(layers) do
            ck(not L.n or L.n <= 8, def.key .. ": at most 8 particles a layer on " .. it.id)
            ck(not L.keys or #L.keys <= 4, def.key .. ": at most 4 flipbook frames on " .. it.id)
          end
        end
      end

      -- 6. skins with effects, and the shine on other Legendary cosmetics
      local n = 0
      for id in pairs(T.ITEM_ANIM) do
        n = n + 1
        ck(T.ITEMS[id], "effect for a real item: " .. id)
      end
      ck(n >= 35, "effects on the expensive skins and cosmetics: " .. n)
      for _, it in ipairs(T.ITEM_LIST) do
        if it.slot == "skin" and it.rarity >= 4 then ck(T.AnimOf(it), "Epic or Legendary skin has an effect: " .. it.id) end
      end
      for _, id in ipairs({ "skin_diamond", "skin_galaxy", "skin_spectral", "skin_golden", "skin_rainbow", "skin_flamesaber" }) do
        masks = 0
        db.owned[id] = 1; db.look.skin = id
        cat:ApplyAppearance(T:GetAppearance()); spyMasks(cat); cat:ApplyAppearance(T:GetAppearance())
        ck(nLayers(cat) >= 1, "layers for " .. id)
        for i = 1, 30 do _update(0.05) end
        ck(shownAnimTex(cat) <= 70, id .. " is cheap: " .. shownAnimTex(cat))
      end
      local legend = T.ITEMS["WARRIOR:chest_plate:5"]
      ck(legend and T.AnimOf(legend) == T.ANIM_LEGENDARY, "a Legendary cosmetic shines")
      ck(T.AnimOf({ gear = true, rarity = 5, slot = "chest", art = "chest_plate" }) == nil, "real gear has no cosmetic effect")
      -- small cats (party row) skip particles and glints
      local small = T.CreateCat(UIParent, 40, { preview = true })
      withMasks(small)
      small:ApplyAppearance(T:GetAppearance())
      local smallParticles = 0
      for _, st in ipairs(small.anim and small.anim.layers or {}) do smallParticles = smallParticles + 1 end
      local bigN = nLayers(cat)
      ck(smallParticles < bigN, "small cats get fewer layers (" .. smallParticles .. " < " .. bigN .. ")")
      -- the window hides: no work while hidden
      cat.vec:Hide(); local t0 = cat.anim.t; _update(0.5); ck(cat.anim.t == t0, "no animation while hidden"); cat.vec:Show()
      db.look.skin = nil
      return table.concat(fails, "\n")
    ''')
    if r:
        raise AssertionError("art section:\n" + r)

    # every texture an animation layer or set names exists in Art/v
    V = {}
    for m in re.finditer(r'V\["([^"]+)"\]=\{"([^"]+)"', open(os.path.join(ROOT, "VectorData.lua")).read()):
        V[m.group(1)] = m.group(2)
    names = lua.execute(r'''
      local out = {}
      local function walk(layers)
        for _, L in ipairs(layers) do
          if L.sprite then out[#out + 1] = "s:" .. L.sprite end
          if L.key then out[#out + 1] = "k:" .. L.key end
          if L.mask then out[#out + 1] = "k:" .. L.mask end
          for _, k in ipairs(L.keys or {}) do out[#out + 1] = "k:" .. k end
        end
      end
      for _, a in pairs(TapCatForever.ITEM_ANIM) do walk(a) end
      for _, a in pairs(TapCatForever.VEC_ANIM) do walk(a) end
      walk(TapCatForever.ANIM_LEGENDARY)
      for k, e in pairs(TapCatForever.VEC) do out[#out + 1] = "t:" .. e[1] end
      return out''')
    missing = set()
    for n in names.values():
        kind, name = n.split(":", 1)
        if kind == "s" and not os.path.exists(os.path.join(ROOT, "Art", "v", name + ".tga")): missing.add(name)
        if kind == "k" and lua.eval('TapCatForever.VEC["%s"]' % name) is None: missing.add(name)
        if kind == "t" and not os.path.exists(os.path.join(ROOT, "Art", "v", name + ".tga")): missing.add(name)
    assert not missing, "art section: missing textures %s" % sorted(missing)
    for f in ("cos:shoulder_plate:a", "cos:shoulder_mail:a", "cos:shoulder_leather:a", "cos:shoulder_cloth:a"):
        assert f in V, "art section: no drawing for " + f
    print("art section (shoulder slot, racial slot with shades, party payload, Molten Core set: 6 pieces from 6 bosses, %d animated items, masks, small cats, %d textures checked): all checks passed"
          % (lua.eval("(function() local n = 0 for _ in pairs(TapCatForever.ITEM_ANIM) do n = n + 1 end return n end)()"), len(names)))
