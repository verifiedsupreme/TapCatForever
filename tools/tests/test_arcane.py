# 1.6.0 test feedback: "my arcane explosion doesn't seem to be going off". Area spells (Arcane
# Explosion, Thunder Clap, ...) were only cast when two or more enemies were up, so against bosses
# and the last enemy of a pack they never went off. Now an area spell is also cast at a lone enemy
# when no single-target spell is ready, and Arcane Explosion rings out from the cat before it pops
# on every enemy.
# A level 14 Mage that learned Fireball, Fire Blast, Frost Nova and Arcane Explosion fights
# Ragefire Chasm (packs of two and its bosses): Arcane Explosion is cast against packs and bosses,
# hits every living enemy for its damage, not before it is learned, and shows its ring and bursts.
# Run on its own:  python3 tools/tests/test_arcane.py [seed]
import os, sys

def ck(c, m):
    if not c: raise AssertionError("arcane explosion: " + m)

def check(seed, load_addon):
    lua = load_addon()
    lua.execute("math.randomseed(%d)" % (seed % 2147483647))
    r = lua.execute(r'''
      local T = TapCatForever
      local out = {}
      T:SetClass("MAGE")
      local cd = T:CD()
      cd.level = 14
      local function tierOf(k) for i, t in ipairs(T.TIERS) do if t.key == k then return i end end end
      local adv = cd.adv
      local rfc = tierOf("rfc")
      adv.best = T.AdvStageCode(rfc, T:AdvStages(rfc))
      T.advWatching = true
      local function fight(stage, seconds, learned)
        for k in pairs(cd.abilities) do cd.abilities[k] = nil end
        for _, k in ipairs(learned) do cd.abilities[k] = true end
        adv.tier, adv.stage, adv.auto, adv.active = rfc, stage, false, true
        T:AdvReset()
        local uses, aeHits, aeTargets, packs = 0, 0, 0, 0
        for step = 1, seconds * 10 do
          T:AdvTick(0.1)
          local run = T.advRun
          local evs = run.events
          for j, e in ipairs(evs) do
            if e[1] == "ability" and e[4] and e[4].key == "ae" then
              uses = uses + 1
              -- the hits right after the cast: one per living enemy
              local n = 0
              for j2 = j + 1, #evs do
                local k = evs[j2][1]
                if k == "hit" then n = n + 1 elseif k ~= "mobdie" then break end
              end
              aeHits = aeHits + n
            end
          end
          run.events = {}
          run.catHP = run.catMax   -- this test is about the spell, not about winning
        end
        return uses, aeHits
      end
      local all = { "fb", "fa", "blast", "nova", "ae" }
      out.packUses, out.packHits = fight(1, 300, all)
      out.bossUses, out.bossHits = fight(2, 300, all)
      out.unlearned = fight(1, 120, { "fb", "fa", "blast", "nova" })
      -- the look: a ring from the cat, then a burst and the game's impact on every enemy
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
      local kits = 0
      local fx = T.AdvFX.New(layer, CreateFrame("Frame"), {
        slotPos = function(i) if i and i >= 1 and i <= 2 then return 300 + i * 60, 100 end end,
        slotFrame = function(i) return { mode = "scene", placed = "k", IsShown = function() return true end,
          actor = { SetSpellVisualKit = function() kits = kits + 1 end } } end,
        float = function() end, shake = function() end, anim = function() end, target = function() return 1 end,
      })
      fx:Ability({ key = "ae", kind = "aoe", target = 1, class = "MAGE" })
      for k = 1, 4 do fx:Update(0.05) end
      local ring, bursts = 0, 0
      for _, t in ipairs(made) do
        for _, p in ipairs(t.paths) do
          if p:find("aura", 1, true) then ring = ring + 1 end
          if p:find("arcane", 1, true) then bursts = bursts + 1 end
        end
      end
      out.ring, out.bursts, out.kits = ring, bursts, kits
      out.mode = T.SPELL_FX.For("MAGE", "ae", "aoe")[2]
      return out
    ''')
    ck(r.packUses >= 30, "cast against packs of two: %d times in 5 minutes" % r.packUses)
    ck(r.packHits >= r.packUses, "each cast hits the pack (%d hits for %d casts)" % (r.packHits, r.packUses))
    ck(r.bossUses >= 15 and r.bossHits >= r.bossUses, "cast against a lone boss too: %d casts, %d hits" % (r.bossUses, r.bossHits))
    ck(r.unlearned == 0, "never cast before it is learned")
    ck(r.mode == "nova" and r.ring >= 1 and r.bursts >= 2 and r.kits >= 2, "the look: ring %d, bursts %d, game impacts %d" % (r.ring, r.bursts, r.kits))
    print("arcane explosion section (level 14 Mage in Ragefire Chasm: %d casts on packs, %d on a lone boss, every enemy hit, a ring from the cat and a burst on each enemy): all checks passed"
          % (r.packUses, r.bossUses))

if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(HERE, ".."))
    import test_harness
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
