# Adventure fight visuals (AdventureFX.lua): ranged attacks look ranged, every ability shows something,
# the game's spell visuals play on the 3D enemies (with fallbacks), no per-frame allocations.
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")


def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ok(c, msg) if not c then fails[#fails + 1] = msg end end
      local function wear(class, id)
        local eq = T:GearEquipped(class)
        eq.RANGED = id
      end
      local function firstOf(sub, class)
        for _, g in ipairs(T.GEAR_LIST) do
          if g.slot == "RANGED" and g.sub == sub and T:GearUsable(g, class) and not g.placeholder then return g end
        end
      end

      ------------------------------------------------ A. how basic attacks land (CombatStats)
      for _, c in ipairs(T.CLASSES) do T:CD(c.key).level = 30 end
      local bow, gun, xbow, thrown = firstOf("bow", "HUNTER"), firstOf("gun", "HUNTER"), firstOf("xbow", "HUNTER"), firstOf("thrown", "HUNTER")
      ok(bow and gun and xbow and thrown, "test data has a bow, gun, crossbow and thrown weapon")
      for _, w in ipairs({ bow, gun, xbow, thrown }) do
        wear("HUNTER", w.id)
        local st = T:CombatStats("HUNTER")
        ok(st.attack == "shoot" and st.shot == w.sub, "a hunter with a " .. w.sub .. " shoots it: " .. tostring(st.attack) .. "/" .. tostring(st.shot))
      end
      wear("HUNTER", bow.id)
      local withBow = T:CombatStats("HUNTER").dps
      wear("HUNTER", nil)
      local bare = T:CombatStats("HUNTER")
      ok(bare.attack == "melee" and bare.shot == nil, "a hunter with no ranged weapon fights in melee: " .. tostring(bare.attack))
      -- the hunter's damage comes from the ranged weapon only when it has one
      local better
      for _, g in ipairs(T.GEAR_LIST) do
        if g.slot == "RANGED" and g.sub == "bow" and (T.GearStats(g).dps or 0) > (T.GearStats(bow).dps or 0) * 1.5 then better = g; break end
      end
      ok(better, "test data has a better bow")
      if better then wear("HUNTER", better.id); ok(T:CombatStats("HUNTER").dps > withBow, "a better bow means harder shots") end
      wear("HUNTER", bow.id)
      -- casters: a wand shoots bolts of its school; without one they cast
      local wands = { [5069] = "fire", [5071] = "shadow", [7514] = "frost" }
      for id, school in pairs(wands) do
        for _, cl in ipairs({ "MAGE", "PRIEST", "WARLOCK" }) do
          wear(cl, id)
          local st = T:CombatStats(cl)
          ok(st.attack == "wand" and st.shot == "wand" and st.school == school,
            cl .. " with " .. T.GEAR[id].name .. ": " .. tostring(st.attack) .. " " .. tostring(st.school))
        end
      end
      local n, known = 0, 0
      for id, s in pairs(T.WAND_SCHOOL) do
        n = n + 1
        ok(T.GEAR[id] and T.GEAR[id].sub == "wand", "WAND_SCHOOL lists only wands: " .. id)
        ok(T.AdvFX.SCHOOL_TINT[s] and s ~= "physical", "a wand's school has a colour: " .. tostring(s))
      end
      for _, g in ipairs(T.GEAR_LIST) do
        if g.sub == "wand" then known = known + 1; ok(T.WAND_SCHOOL[g.base or g.id], "every wand has a school: " .. g.name) end
      end
      ok(n >= 100, "wand schools: " .. n)
      wear("MAGE", 7514)
      local withWand = T:CombatStats("MAGE").dps
      wear("MAGE", nil)
      local noWand = T:CombatStats("MAGE")
      ok(noWand.attack == "spell" and not noWand.school, "a mage with no wand casts, no wand bolts: " .. tostring(noWand.attack))
      ok(withWand > noWand.dps, "the wand adds to the bolts' damage")
      for _, cl in ipairs({ "WARRIOR", "ROGUE", "PALADIN" }) do
        wear(cl, (cl == "PALADIN") and nil or bow.id)
        ok(T:CombatStats(cl).attack == "melee", cl .. " keeps melee swings even with a bow")
      end
      local sh = T:CombatStats("SHAMAN").attack
      ok(sh == "melee" or sh == "spell", "shaman: melee or spell")

      ------------------------------------------------ the cat holds its ranged weapon while it fights
      wear("MAGE", 5069)
      T:SetClass("MAGE")
      local st = T:CombatStats("MAGE")
      local look = T:GetAppearance("MAGE")
      local fight = T.AdvFX.FightLook(look, st, "MAGE", true)
      ok(fight.main and fight.main.id == "gear:5069" and fight.main.art == "wpn_wand", "a wand mage holds the wand in fights: " .. tostring(fight.main and fight.main.id))
      ok(T.AdvFX.FightLook(look, st, "MAGE", false) == look, "out of fights the normal look")
      ok(look.main == nil or look.main.id ~= "gear:5069", "the look itself is not changed")
      local cos = { id = "cos_wand", art = "wpn_wand", slot = "main", c1 = { 1, 1, 1 } }
      local l2 = {}; for k, v in pairs(look) do l2[k] = v end; l2.main = cos
      ok(T.AdvFX.FightLook(l2, st, "MAGE", true).main == cos, "a cosmetic wand is kept")
      ok(T.AdvFX.FightLook(look, noWand, "MAGE", true) == look, "no wand, nothing to hold")
      wear("HUNTER", gun.id)
      local hl = T.AdvFX.FightLook(T:GetAppearance("HUNTER"), T:CombatStats("HUNTER"), "HUNTER", true)
      ok(hl.main and hl.main.art == "wpn_rifle", "a hunter holds its gun")

      ------------------------------------------------ B. every ability shows something
      local missing = {}
      for class, list in pairs(T.ABILITIES) do
        for _, a in ipairs(list) do
          local vis
          if a.kind == "passive" or a.kind == "ward" then vis = T.SPELL_FX.Passive(class, a.key)
          else vis = T.SPELL_FX.For(class, a.key, a.kind) end
          if not vis then missing[#missing + 1] = class .. ":" .. a.key end
          local row = T.SPELL_KITS[class] and T.SPELL_KITS[class][a.key]
          ok(row and type(row[1]) == "number" and row[1] > 0, "a real spell for " .. class .. " " .. a.name)
        end
      end
      ok(#missing == 0, "abilities with no animation: " .. table.concat(missing, ", "))
      for s, k in pairs(T.SCHOOL_KITS) do ok(k > 0, "a game visual for " .. s .. " impacts") end

      ------------------------------------------------ the effects themselves, on fake enemies
      -- three fake enemy slots: a 3D actor that records the game visuals played on it
      local kitLog, anims, floats, shakes = {}, {}, {}, {}
      local slots = {}
      for i = 1, 3 do
        local actor = { SetSpellVisualKit = function(self, kit, one) kitLog[#kitLog + 1] = { i, kit, one } end }
        slots[i] = { mode = "scene", actor = actor, placed = "k", IsShown = function() return true end }
      end
      local layer = CreateFrame("Frame")
      local made = {}
      layer.CreateTexture = function()
        local t = CreateFrame("Frame"); t.paths = {}
        local set = t.SetTexture
        t.SetTexture = function(self, p) self.paths[#self.paths + 1] = p; return set(self, p) end
        t.SetVertexColor = function(self, r, g, b) self.color = { r, g, b } end
        made[#made + 1] = t
        return t
      end
      local alive = 3
      local fx = T.AdvFX.New(layer, CreateFrame("Frame"), {
        slotPos = function(i) if i and i >= 1 and i <= alive then return 300 + i * 60, 100 end end,
        slotFrame = function(i) return slots[i] end,
        float = function(txt) floats[#floats + 1] = txt end,
        shake = function(i) shakes[#shakes + 1] = i end,
        anim = function(i, id, t) anims[#anims + 1] = { i, id, t } end,
        target = function() return 1 end,
      })
      local function used(path)
        for _, t in ipairs(made) do for _, p in ipairs(t.paths) do if p:find(path, 1, true) then return t end end end
      end
      local function reset() for _, t in ipairs(made) do t.paths = {} end; kitLog = {}; anims = {}; floats = {} end
      local function run(sec) for k = 1, math.floor(sec / 0.05 + 0.5) do fx:Update(0.05) end end

      -- arrows, bullets, bolts, thrown weapons fly from the cat to the target
      for _, w in ipairs({ { "bow", "s_arrow" }, { "gun", "advfx\\bullet" }, { "xbow", "advfx\\bolt" }, { "thrown", "advfx\\thrown" } }) do
        reset()
        local shot = fx:Swing(2, { attack = "shoot", shot = w[1] }, "HUNTER")
        ok(shot, w[1] .. ": the cat shoots")
        ok(used(w[2]), w[1] .. " shot uses " .. w[2])
        if w[1] == "gun" then ok(used("advfx\\muzzle"), "a gun flashes at the barrel") end
        local p = fx:TakePending(2)
        ok(p and p.mode == "proj" and p.ax < p.bx, w[1] .. ": the shot flies toward the enemy")
        T.AdvFX.Carry(p, "123", 360, 140, 1, 1, 1, false, 2)
        ok(#floats == 0, "the number waits for the shot")
        run(0.5)
        ok(#floats == 1 and floats[1] == "123", w[1] .. ": the number shows when it lands")
        fx:EndBatch()
      end
      -- wand bolts take their wand's colour and land with the game's visual of that school
      for school, tint in pairs(T.AdvFX.SCHOOL_TINT) do
        if school ~= "physical" then
          reset()
          fx:Swing(1, { attack = "wand", shot = "wand", school = school }, "MAGE")
          local t = used("advfx\\wandbolt")
          ok(t and t.color and t.color[1] == tint[1] and t.color[3] == tint[3], "a " .. school .. " wand bolt is " .. school .. " coloured")
          run(0.5)
          ok(#kitLog == 1 and kitLog[1][2] == T.SCHOOL_KITS[school] and kitLog[1][3] == true, school .. " wand bolt plays the game's " .. school .. " impact once")
          fx:EndBatch()
        end
      end
      -- no wand: no wand bolt; melee: a swipe, no projectile
      reset()
      ok(not fx:Swing(1, { attack = "spell" }, "PRIEST") and not used("wandbolt") and used("advfx\\sparkle"), "a caster with no wand casts (no wand bolt)")
      ok(not fx:TakePending(1), "a plain spell lands at once")
      reset()
      ok(not fx:Swing(1, { attack = "melee" }, "WARRIOR") and used("s_slash") and not fx:TakePending(1), "a melee swing")

      -- every ability of every class: sprites, and the game's visual on the enemy for the hostile ones
      local ENEMY = { nuke = true, execute = true, drain = true, aoe = true, dot = true, stun = true }
      local noKit, played = {}, 0
      for class, list in pairs(T.ABILITIES) do
        for _, a in ipairs(list) do
          if a.kind ~= "passive" and a.kind ~= "ward" then
            reset()
            local before = 0
            fx:Ability({ key = a.key, kind = a.kind, target = 1, class = class })
            run(1.6)
            local any = false
            for _, t in ipairs(made) do if #t.paths > 0 then any = true end end
            ok(any, class .. " " .. a.name .. " shows a sprite")
            if ENEMY[a.kind] then
              if #kitLog == 0 then noKit[#noKit + 1] = class .. " " .. a.name else played = played + 1 end
              if a.kind == "aoe" then
                local hit = {}
                for _, k in ipairs(kitLog) do hit[k[1]] = true end
                ok(hit[1] and hit[2] and hit[3], class .. " " .. a.name .. " plays on every enemy")
              end
              if a.kind == "stun" then
                local st = 0
                for _, x in ipairs(anims) do if x[2] == 14 and x[3] == a.dur then st = st + 1 end end
                ok(st == 3, class .. " " .. a.name .. " stuns every enemy's model for " .. a.dur .. " s: " .. st)
              end
            end
            fx:EndBatch()
            for i = 1, 3 do fx:ClearAura(i) end
          end
        end
      end
      ok(#noKit == 0, "hostile abilities with no game visual: " .. table.concat(noKit, ", "))
      -- a lasting visual (damage over time) is cleared when it runs out
      reset()
      fx:Ability({ key = "corr", kind = "dot", target = 2, class = "WARLOCK" })
      local corr = T.SPELL_KITS.WARLOCK.corr
      local lasting
      for _, k in ipairs(kitLog) do if k[2] == corr[3] and k[3] == false and k[1] == 2 then lasting = true end end
      ok(lasting, "Corruption stays on its target")
      run(19)
      ok(kitLog[#kitLog][1] == 2 and kitLog[#kitLog][2] == 0, "and is cleared when it ends")
      -- a dead enemy's lasting visual ends at once
      fx:Ability({ key = "corr", kind = "dot", target = 3, class = "WARLOCK" }); fx:Gone(3)
      ok(kitLog[#kitLog][1] == 3 and kitLog[#kitLog][2] == 0, "a dead enemy loses its lasting visual")

      -- passives: auras when a pack appears, the pet and the totem keep acting, the Voidwalker guards
      for _, c in ipairs({ "PALADIN", "HUNTER", "PRIEST", "SHAMAN", "MAGE", "WARLOCK", "DRUID" }) do
        T:CD(c).level = 60
        for _, a in ipairs(T.ABILITIES[c]) do T:CD(c).abilities[a.key] = true end
      end
      reset(); fx:Spawn("PALADIN"); run(0.1)
      ok(used("advfx\\aura"), "Devotion Aura: a ring at the cat's feet")
      reset(); fx:Swing(1, { attack = "melee" }, "PALADIN")
      ok(used("advfx\\sparkle"), "Seal of Righteousness: a sparkle with every hit")
      reset(); fx:Spawn("HUNTER"); run(5)
      ok(used("advfx\\claw"), "Call Pet: claws strike the target")
      reset(); fx:Spawn("SHAMAN"); run(0.1)
      ok(used("advfx\\orb") and used("advfx\\totem"), "Lightning Shield orbs and Searing Totem")
      run(5)
      ok(used("s_fire"), "the totem throws fire")
      fx:Stand(); run(0.1)
      ok(not fx.totem, "the totem leaves when the fight stops")
      reset(); fx:Spawn("WARLOCK"); run(0.1); reset(); fx:Hurt(); ok(used("s_shield"), "the Voidwalker guards"); reset(); fx:Hurt()
      ok(not used("s_shield"), "but not on every hit")
      reset(); fx:Spawn("DRUID"); run(0.1); ok(used("advfx\\sparkle"), "Cat Form: a sparkle when a pack appears")
      reset(); fx:Spawn("MAGE"); run(0.1); ok(used("advfx\\aura"), "Frost Armor: a frosty ring")

      -- the game visuals can be turned off, and a missing API never breaks the fight
      kitLog = {}
      TapCatForeverDB.cartoonSpellFx = true
      fx:Ability({ key = "fb", kind = "nuke", target = 1, class = "MAGE" }); run(1)
      ok(#kitLog == 0, "cartoonSpellFx: only sprites")
      TapCatForeverDB.cartoonSpellFx = nil
      slots[1].actor = { SetSpellVisualKit = function() error("no such kit") end }
      slots[2].actor = {}
      slots[3] = { mode = "classic", model = { ApplySpellVisualKit = function(self, k, o) kitLog[#kitLog + 1] = { 3, k, o } end }, IsShown = function() return true end }
      fx:Ability({ key = "ae", kind = "aoe", target = 1, class = "MAGE" }); run(1)
      ok(#kitLog == 1 and kitLog[1][1] == 3, "the old model frame plays them too; errors are caught")

      -- no tables are made per frame while effects play
      fx:Spawn("SHAMAN")
      for k = 1, 3 do fx:Swing(k, { attack = "wand", shot = "wand", school = "fire" }, "MAGE") end
      fx:Ability({ key = "bliz", kind = "aoe", target = 1, class = "MAGE" })
      run(0.05)
      collectgarbage("collect"); collectgarbage("stop")
      local m0 = collectgarbage("count")
      for k = 1, 200 do fx:Update(0.0005) end -- 0.1 s: everything still flying, nothing lands
      local grew = collectgarbage("count") - m0
      collectgarbage("restart")
      ok(grew < 1, string.format("per-frame memory: %.2f KB over 200 frames", grew))

      ------------------------------------------------ the real page: a hunter and a wand mage fight
      T:CreateWindow(); T.window:Show(); T.window:SelectTab(2)
      local shotPaths = {}
      local function fight(class, sec)
        T:SetClass(class)
        T.advFx.pool = {}
        local layer = T.advFx.layer
        local mk = layer.CreateTexture
        layer.CreateTexture = function(...)
          local t = mk(...)
          local set = t.SetTexture
          t.SetTexture = function(self, p) shotPaths[p] = (shotPaths[p] or 0) + 1; return set(self, p) end
          return t
        end
        T:AdvGoTo(1, 1); T:AdvStart()
        for k = 1, math.floor(sec / 0.05) do _update(0.05) end
        T:AdvRetreat(); _update(0.05)
        layer.CreateTexture = mk
      end
      wear("HUNTER", bow.id); T:CD("HUNTER").level = 5
      fight("HUNTER", 20)
      local arrows = shotPaths[T.AdvFX.PATH.arrow] or 0
      ok(arrows >= 10, "a hunter's fight is full of arrows: " .. arrows)
      shotPaths = {}
      wear("MAGE", 5069); T:CD("MAGE").level = 5
      fight("MAGE", 20)
      local bolts = shotPaths[T.AdvFX.PATH.wandbolt] or 0
      ok(bolts >= 10, "a wand mage shoots wand bolts: " .. bolts)
      shotPaths = {}
      wear("MAGE", nil)
      fight("MAGE", 20)
      ok((shotPaths[T.AdvFX.PATH.wandbolt] or 0) == 0, "no wand, no wand bolts")
      shotPaths = {}
      T:CD("WARRIOR").level = 5
      fight("WARRIOR", 20)
      ok((shotPaths[T.AdvFX.PATH.arrow] or 0) == 0 and (shotPaths[T.AdvFX.PATH.slash] or 0) > 5, "a warrior swings")
      ok(not T.advFx.fighting and not T.advFx.totem, "after Retreat the effects stop")
      _G._advfxStats = string.format("%d arrows, %d wand bolts in 20 s; %d hostile abilities with a game visual", arrows, bolts, played)
      return table.concat(fails, "\n")
    ''')
    if r:
        raise AssertionError("adventure fx:\n" + r)
    for name in ("aura", "bolt", "bullet", "claw", "muzzle", "orb", "sparkle", "thrown", "totem", "wandbolt"):
        assert os.path.exists(os.path.join(ROOT, "Art", "advfx", name + ".tga")), "missing Art/advfx/" + name
    print("adventure fx section (%s; ranged shots, wand schools, every ability animated, game spell visuals with fallbacks, no per-frame tables): all checks passed" % lua.globals()._advfxStats)
