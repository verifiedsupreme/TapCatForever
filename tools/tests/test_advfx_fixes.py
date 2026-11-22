# Adventure fight visuals, review fixes: the held weapon doesn't flicker between packs, lasting game
# visuals survive one-time impacts and each other, single-target abilities stay on their target,
# cosmetic weapons are kept only when they match, the killing shot lands before the enemy falls,
# one tap per cast, Cat Form claws, plain debug text.
def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local FXC = T.AdvFX
      local fails = {}
      local function ok(c, msg) if not c then fails[#fails + 1] = msg end end
      local function wear(class, id) T:GearEquipped(class).RANGED = id end
      local function firstOf(sub, class)
        for _, g in ipairs(T.GEAR_LIST) do
          if g.slot == "RANGED" and g.sub == sub and T:GearUsable(g, class) and not g.placeholder then return g end
        end
      end
      for _, c in ipairs(T.CLASSES) do T:CD(c.key).level = 30 end

      ------------------------------------------------ fake enemies (3D actors that log the game visuals)
      local kitLog, anims, floats, deaths = {}, {}, {}, {}
      local slots = {}
      local function sceneSlot(i)
        return { mode = "scene", placed = "k", IsShown = function() return true end,
          actor = { SetSpellVisualKit = function(self, kit, one) kitLog[#kitLog + 1] = { i, kit, one } end } }
      end
      for i = 1, 3 do slots[i] = sceneSlot(i) end
      local layer = CreateFrame("Frame")
      local made = {}
      layer.CreateTexture = function()
        local t = CreateFrame("Frame"); t.paths = {}
        local set = t.SetTexture
        t.SetTexture = function(self, p) self.paths[#self.paths + 1] = p; return set(self, p) end
        t.SetVertexColor = function() end
        made[#made + 1] = t
        return t
      end
      local fx = FXC.New(layer, CreateFrame("Frame"), {
        slotPos = function(i) if i and i >= 1 and i <= 3 then return 300 + i * 60, 100 end end,
        slotFrame = function(i) return slots[i] end,
        float = function(txt) floats[#floats + 1] = txt end,
        shake = function() end,
        anim = function(i, id, t) anims[#anims + 1] = { i, id, t } end,
        target = function() return 1 end,
        die = function(i, mob) deaths[#deaths + 1] = { i, mob } end,
      })
      local function used(path)
        for _, t in ipairs(made) do for _, p in ipairs(t.paths) do if p:find(path, 1, true) then return true end end end
      end
      local function reset()
        for _, t in ipairs(made) do t.paths = {} end
        kitLog, anims, floats, deaths = {}, {}, {}, {}
      end
      local function run(sec) for k = 1, math.floor(sec / 0.05 + 0.5) do fx:Update(0.05) end end
      local function last(i)
        for k = #kitLog, 1, -1 do if kitLog[k][1] == i then return kitLog[k] end end
      end
      local function clearAll() fx:EndBatch(); for i = 1, 3 do fx:ClearAura(i); fx.stun[i] = 0 end; run(1) end

      local CORR, FEAR = T.SPELL_KITS.WARLOCK.corr[3], T.SPELL_KITS.WARLOCK.fear[3]
      ok(CORR > 0 and FEAR > 0, "Corruption and Fear have lasting game visuals")

      ------------------------------------------------ a one-time impact doesn't wipe a lasting visual
      reset()
      fx:Ability({ key = "corr", kind = "dot", target = 2, class = "WARLOCK" })
      fx:Swing(2, { attack = "wand", shot = "wand", school = "shadow" }, "WARLOCK")
      run(0.4) -- the bolt lands: a one-time impact on enemy 2
      local hitAt = #kitLog
      ok(kitLog[hitAt] and kitLog[hitAt][3] == true, "the wand bolt's impact plays once")
      run(0.8)
      local l = last(2)
      ok(l and l[2] == CORR and l[3] == false, "Corruption goes back on after the impact: " .. tostring(l and l[2]))
      ok(#kitLog == hitAt + 1, "and only once")
      clearAll()

      ------------------------------------------------ two lasting visuals: the longer one comes back
      reset()
      fx:Ability({ key = "corr", kind = "dot", target = 1, class = "WARLOCK" })  -- 18 s
      fx:Ability({ key = "fear", kind = "stun", target = 1, class = "WARLOCK" }) -- 3 s, on every enemy
      l = last(1)
      ok(l and l[2] == FEAR and l[3] == false, "Fear shows over Corruption")
      run(3.5)
      l = last(1)
      ok(l and l[2] == CORR and l[3] == false, "Corruption comes back when Fear ends: " .. tostring(l and l[2]))
      local cleared = false
      for _, k in ipairs(kitLog) do if k[1] == 1 and k[2] == 0 then cleared = true end end
      ok(not cleared, "Fear ending doesn't clear Corruption")
      l = last(2)
      ok(l and l[2] == 0, "an enemy with only Fear is cleared when it ends")
      run(15)
      l = last(1)
      ok(l and l[2] == 0, "Corruption is cleared when it ends")
      clearAll()

      ------------------------------------------------ the older model frame: lasting visuals play once
      reset()
      slots[3] = { mode = "classic", IsShown = function() return true end,
        model = { ApplySpellVisualKit = function(self, k, o) kitLog[#kitLog + 1] = { 3, k, o } end } }
      fx:Ability({ key = "corr", kind = "dot", target = 3, class = "WARLOCK" })
      local lasting = false
      for _, k in ipairs(kitLog) do if k[2] == CORR and k[3] == false then lasting = true end end
      ok(not lasting, "no lasting visual on the model frame (it couldn't be taken off)")
      ok(last(3) and last(3)[2] == CORR and last(3)[3] == true, "it plays once instead")
      run(20)
      local zero = false
      for _, k in ipairs(kitLog) do if k[1] == 3 and k[2] == 0 then zero = true end end
      ok(not zero, "nothing to clear later")
      slots[3] = sceneSlot(3)
      clearAll()

      ------------------------------------------------ single-target abilities stay on their target
      reset()
      fx:Ability({ key = "mf", kind = "dot", target = 2, class = "DRUID" }) -- Moonfire: falls from the sky
      run(1)
      local on = {}
      for _, k in ipairs(kitLog) do on[k[1]] = true end
      ok(on[2] and not on[1] and not on[3], "Moonfire plays only on its target")
      clearAll(); reset()
      fx:Ability({ key = "immo", kind = "dot", target = 3, class = "WARLOCK" })
      ok(last(3) and last(3)[2] == T.SPELL_KITS.WARLOCK.immo[3], "a damage over time's lasting visual goes on its target")
      ok(not last(1) and not last(2), "and on no other enemy")
      clearAll(); reset()
      fx:Ability({ key = "ae", kind = "aoe", target = 1, class = "MAGE" }); run(1)
      on = {}
      for _, k in ipairs(kitLog) do on[k[1]] = true end
      ok(on[1] and on[2] and on[3], "Arcane Explosion still plays on every enemy")
      clearAll()

      ------------------------------------------------ a stun is never cut short by a flinch
      reset()
      fx:Ability({ key = "nova", kind = "stun", target = 1, class = "MAGE" })
      fx:Ability({ key = "blast", kind = "nuke", target = 1, class = "MAGE" })
      local flinch = false
      for _, a in ipairs(anims) do if a[1] == 1 and a[2] == 9 then flinch = true end end
      ok(not flinch, "no flinch on a frozen enemy")
      run(4.5); reset()
      fx:Ability({ key = "blast", kind = "nuke", target = 1, class = "MAGE" })
      ok(anims[1] and anims[1][2] == 9, "flinches again once the stun ends")
      clearAll()

      ------------------------------------------------ the killing shot lands before the enemy falls
      reset()
      local mob = { name = "Kobold" }
      fx:Swing(1, { attack = "shoot", shot = "bow" }, "HUNTER")
      ok(fx:CarryHit(1, "99", 360, false), "the arrow carries the hit")
      ok(fx:DieOnLand(1, mob), "and the death")
      ok(#deaths == 0 and #floats == 0, "nothing yet while the arrow flies")
      run(0.5)
      ok(#floats == 1 and #deaths == 1 and deaths[1][1] == 1 and deaths[1][2] == mob, "the enemy falls when the arrow lands")
      fx:EndBatch()
      ok(not fx:DieOnLand(1, mob), "no shot on its way: it falls at once")
      ok(not fx:CarryHit(2, "5", 360, false), "a hit with no shot on its way shows at once")
      fx:Swing(1, { attack = "shoot", shot = "bow" }, "HUNTER"); fx:CarryHit(1, "1", 360, false); fx:EndBatch()
      ok(not fx:DieOnLand(1, mob), "a shot from an earlier batch doesn't carry a later death")
      clearAll()

      ------------------------------------------------ one tap per cast
      local tapNow = {
        { "MAGE", "fb", "nuke", true },      -- flies: the hit waits for it, so the cast taps
        { "MAGE", "blast", "nuke", false },  -- pops at once: the hit that follows taps
        { "MAGE", "ae", "aoe", false },
        { "WARLOCK", "corr", "dot", true },  -- no hit follows
        { "PRIEST", "renew", "heal", true },
        { "MAGE", "nova", "stun", true },
      }
      for _, c in ipairs(tapNow) do
        local got = fx:Ability({ key = c[2], kind = c[3], target = 1, class = c[1] })
        ok(got == c[4], c[1] .. " " .. c[2] .. ": tap for the cast " .. tostring(c[4]) .. ", got " .. tostring(got))
        clearAll()
      end

      ------------------------------------------------ a druid in Cat Form claws
      reset()
      T:CD("DRUID").abilities.cat = nil
      fx:Swing(1, { attack = "spell" }, "DRUID")
      ok(used("advfx\\sparkle") and not used("s_slash"), "a druid without Cat Form casts")
      reset()
      T:CD("DRUID").abilities.cat = true
      fx:Swing(1, { attack = "spell" }, "DRUID")
      ok(used("s_slash"), "a druid in Cat Form swipes")
      T:CD("DRUID").abilities.cat = nil
      clearAll()

      ------------------------------------------------ cosmetic weapons kept only when they match
      local bow, gun, xbow = firstOf("bow", "HUNTER"), firstOf("gun", "HUNTER"), firstOf("xbow", "HUNTER")
      local function runFor(class) return { class = class, stats = T:CombatStats(class), away = false } end
      local function withMain(look, art)
        local l = {}; for k, v in pairs(look) do l[k] = v end
        l.main = { id = "cos_" .. art, art = art, slot = "main", c1 = { 1, 1, 1 } }
        return l
      end
      T:SetClass("HUNTER")
      local base = T:GetAppearance("HUNTER")
      local cases = {
        { gun, "wpn_bow", "wpn_rifle", false },   -- a cosmetic bow on a gun hunter: the gun shows
        { bow, "wpn_dagger", "wpn_bow", false },  -- a cosmetic dagger on a bow hunter: the bow shows
        { bow, "wpn_bow", "wpn_bow", true },      -- a cosmetic bow on a bow hunter: kept
        { xbow, "wpn_bow", "wpn_bow", true },     -- crossbows are drawn as bows: kept
        { gun, "wpn_rifle", "wpn_rifle", true },
      }
      for _, c in ipairs(cases) do
        wear("HUNTER", c[1].id)
        local look = withMain(base, c[2])
        local out = FXC.FightLook(look, runFor("HUNTER"), "HUNTER", true)
        ok(out.main and out.main.art == c[3] and ((out.main == look.main) == c[4]),
          c[1].sub .. " hunter with a cosmetic " .. c[2] .. ": holds " .. tostring(out.main and out.main.art))
      end
      wear("HUNTER", bow.id)
      local look = withMain(base, "wpn_bow")
      ok(FXC.FightLook(look, runFor("HUNTER"), "HUNTER", false) == look, "not started: the normal look")
      local away = runFor("HUNTER"); away.away = true
      ok(FXC.FightLook(look, away, "HUNTER", true) == look, "away on an expedition: the normal look")
      ok(FXC.FightLook(look, runFor("MAGE"), "HUNTER", true) == look, "another class's fight: the normal look")

      ------------------------------------------------ debug text in plain words
      local printed = {}
      local oldPrint = print
      print = function(s) printed[#printed + 1] = s end
      T.advFx = fx
      wear("HUNTER", xbow.id); T:SetClass("HUNTER"); T:AdvFxDebug()
      T:SetClass("MAGE"); wear("MAGE", 5069); T:AdvFxDebug()
      wear("MAGE", nil); T:AdvFxDebug()
      print = oldPrint
      local all = table.concat(printed, "\n")
      ok(all:find("shoots a crossbow", 1, true) and all:find("wand bolts (fire)", 1, true) and all:find("basic attack: casts", 1, true),
        "debug text: " .. all)
      ok(not all:find("xbow", 1, true) and not all:find("!", 1, true), "no internal words or exclamation marks: " .. all)
      T.advFx = nil

      ------------------------------------------------ the real page: the held wand doesn't flicker between packs
      T:CreateWindow(); T.window:Show(); T.window:SelectTab(2)
      local orig = FXC.FightLook
      local held, changes, fighting = nil, 0, false
      FXC.FightLook = function(...)
        local out = orig(...)
        local id = out.main and out.main.id or "none"
        if fighting and held and id ~= held then changes = changes + 1 end
        held = id
        return out
      end
      local function fight(class, sec)
        T:SetClass(class)
        T:AdvGoTo(1, 1); T:AdvStart()
        for k = 1, 30 do _update(0.05) end -- the first pack appears (the weapon comes out)
        fighting = true; changes = 0
        local kills0 = T:CD(class).adv.kills
        for k = 1, math.floor(sec / 0.05) do _update(0.05) end
        fighting = false
        local during = held
        local kills = T:CD(class).adv.kills - kills0
        T:AdvRetreat(); _update(0.05)
        return kills, during
      end
      wear("MAGE", 5069); T:CD("MAGE").level = 5
      local kills, during = fight("MAGE", 60)
      ok(kills >= 3, "the wand mage kills several enemies: " .. kills)
      ok(changes == 0 and during == "gear:5069", "the wand stays in the paw across " .. kills .. " kills: " .. changes .. " changes, " .. tostring(during))
      ok(held ~= "gear:5069", "after Retreat the wand is put away: " .. tostring(held))
      wear("HUNTER", gun.id); T:CD("HUNTER").level = 5
      local hk, hd = fight("HUNTER", 40)
      ok(changes == 0 and hd == "gear:" .. gun.id, "the hunter's gun stays in the paw across " .. hk .. " kills: " .. changes .. " changes")
      FXC.FightLook = orig
      _G._advfxFixStats = string.format("%d kills with a steady wand", kills)
      return table.concat(fails, "\n")
    ''')
    if r:
        raise AssertionError("adventure fx fixes:\n" + r)
    print("adventure fx fixes section (steady held weapon, lasting visuals kept, single-target kits, matching cosmetics, killing shot lands first, one tap per cast): all checks passed")
