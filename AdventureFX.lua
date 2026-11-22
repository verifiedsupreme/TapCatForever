-- TapCatForever: Adventure fight visuals. The cat's basic attacks (arrows, bullets, bolts, thrown
-- weapons, wand bolts, plain spells, melee swipes), every ability's effect, and the passive
-- abilities that are always on. Effects on the cat are cartoon sprites; effects on the 3D enemies
-- also play the game's own spell visuals (SpellVisualKit IDs in SpellKitData.lua) through the
-- model actor's SetSpellVisualKit, falling back to sprites only when that is missing or fails.
-- Sprites come from a fixed pool and nothing is allocated per frame.
local ADDON, TCF = ...
local min, max, sin, cos, pi, random, atan2 = math.min, math.max, math.sin, math.cos, math.pi, math.random, math.atan2

local FX = {}
FX.__index = FX
TCF.AdvFX = FX

local ANIM_STAND, ANIM_WOUND, ANIM_STUN = 0, 9, 14
local POOL = 48

-- tint by damage school (wand bolts, plain spells, kit-less impacts)
FX.SCHOOL_TINT = {
  fire = { 1, 0.55, 0.15 }, frost = { 0.55, 0.85, 1 }, shadow = { 0.72, 0.4, 1 }, arcane = { 1, 0.55, 0.95 },
  holy = { 1, 0.92, 0.45 }, nature = { 0.45, 1, 0.35 }, physical = { 1, 1, 1 },
}
-- the school of a caster's plain spell when it has no wand (and of a hybrid that casts)
FX.CLASS_SCHOOL = { MAGE = "arcane", PRIEST = "holy", WARLOCK = "shadow", SHAMAN = "nature", DRUID = "nature" }
-- basic ranged shots by weapon type: sprite, size, flight time (s), arc height, spin, muzzle flash, and
-- where the shot leaves the weapon in the cat's right paw (raised as it shoots; from the vector art boxes)
FX.SHOT = {
  bow = { "arrow", 34, 0.28, 12, 0, false, 128, 74 }, xbow = { "bolt", 30, 0.2, 4, 0, false, 128, 76 },
  gun = { "bullet", 22, 0.14, 0, 0, true, 136, 102 }, thrown = { "thrown", 30, 0.32, 16, 14, false, 124, 62 },
  wand = { "wandbolt", 30, 0.3, 8, 0, false, 131, 88 },
}
-- where things sit in the fight panel (from its bottom-left corner)
FX.MUZZLE = { 128, 70 }      -- where abilities are cast from (they leave 8 left and 20 above it)
FX.CAT = { 95, 72 }          -- the cat's middle
FX.FEET = { 95, 30 }         -- under the cat
FX.TOTEM = { 176, 34 }       -- Searing Totem stands between the cat and the enemies
FX.PET_EVERY, FX.TOTEM_EVERY, FX.GUARD_EVERY = 2.0, 2.5, 4.0

-- sprite name -> texture path (the old s_* spell sprites, or this track's own Art/advfx ones)
local OWN = { aura = true, bolt = true, bullet = true, claw = true, muzzle = true, orb = true, sparkle = true, thrown = true,
  totem = true, wandbolt = true }
local PATH = setmetatable({}, { __index = function(t, k)
  local p = TCF.ART_PATH .. (OWN[k] and ("advfx\\" .. k) or ("v\\s_" .. k))
  t[k] = p
  return p
end })
FX.PATH = PATH

local function call(o, method, ...)
  local fn = o and o[method]
  if type(fn) ~= "function" then return false end
  return pcall(fn, o, ...)
end

-- hooks: slotPos(i) -> x, y (the enemy's chest), slotFrame(i) -> the slot frame (model, actor),
-- float(text, x, y, r, g, b, big), shake(i, secs), anim(i, animID, secs), target() -> slot index,
-- die(i, mob) -> the enemy in slot i (still that mob) plays its death
function FX.New(layer, anchor, hooks)
  local self = setmetatable({ layer = layer, anchor = anchor, hooks = hooks, pool = {}, pending = {}, carried = {}, auras = {},
    stun = { 0, 0, 0 }, clock = 0, passives = {}, petT = 0, totemT = 0, guardT = 0, fighting = false, stats = nil }, FX)
  -- kit/left: the lasting effect shown now; kit2/left2: one waiting under it (shown again when the first
  -- ends); restore: re-apply the shown one shortly after a one-time effect on the same enemy
  for i = 1, 3 do self.auras[i] = { kit = 0, left = 0, kit2 = 0, left2 = 0, restore = 0 } end
  return self
end

-- enemy animations: a flinch never cuts a stun short (stunned, frozen, rooted or feared)
function FX:Anim(i, id, secs)
  if not self.stun[i] then return end
  if id == ANIM_STUN then self.stun[i] = max(self.stun[i], secs)
  elseif self.stun[i] > 0 then return end
  self.hooks.anim(i, id, secs)
end

---------------------------------------------------------------- the game's spell visuals on enemies
-- off with /run TapCatForeverDB.cartoonSpellFx = true (then only the cartoon sprites play)
function FX:KitsOn()
  return not (type(TapCatForeverDB) == "table" and rawget(TapCatForeverDB, "cartoonSpellFx"))
end

-- plays a SpellVisualKit on an enemy's 3D model; oneShot false keeps it on until cleared
function FX:Kit(i, kit, oneShot)
  if not kit or kit == 0 or not self:KitsOn() then return false end
  local f = self.hooks.slotFrame(i)
  if not f or not f:IsShown() then return false end
  local ok
  if f.mode == "scene" and f.actor and f.placed then ok = call(f.actor, "SetSpellVisualKit", kit, oneShot and true or false)
  elseif f.mode == "classic" and f.model then ok = call(f.model, "ApplySpellVisualKit", kit, oneShot and true or false) end
  if ok then self.kitsPlayed = (self.kitsPlayed or 0) + 1 end
  -- an actor may hold only one kit: a one-time effect can wipe the lasting one, so it goes back on soon after
  local a = self.auras[i]
  if ok and oneShot and a and a.kit ~= 0 then a.restore = 0.6 end
  return ok
end

-- a lasting effect (damage over time, stun) on enemy i for secs, cleared when it ends or the enemy dies.
-- Only the 3D actors keep one on: the older model frame has no documented way to take a kit off again,
-- so there it plays once. One lasting effect shows at a time; the other waits and comes back when the
-- shown one ends (Fear over Corruption, then Corruption again).
function FX:Aura(i, kit, secs)
  local a = self.auras[i]
  if not a or not kit or kit == 0 then return end
  local f = self.hooks.slotFrame(i)
  if not (f and f.mode == "scene") then self:Kit(i, kit, true) return end
  if a.kit == kit then a.left = max(a.left, secs) return end
  if a.kit2 == kit then a.kit2, a.left2 = 0, 0 end
  if self:Kit(i, kit, false) then
    if a.kit ~= 0 and a.left > a.left2 then a.kit2, a.left2 = a.kit, a.left end
    a.kit, a.left, a.restore = kit, secs, 0
  end
end

function FX:ClearAura(i)
  local a = self.auras[i]
  if a and (a.kit ~= 0 or a.kit2 ~= 0) then
    local f = self.hooks.slotFrame(i)
    if a.kit ~= 0 and f and f.mode == "scene" and f.actor then call(f.actor, "SetSpellVisualKit", 0, false) end
    a.kit, a.left, a.kit2, a.left2, a.restore = 0, 0, 0, 0, 0
  end
end

-- counts lasting effects down: the shown one ends (the waiting one comes back) or goes back on after a
-- one-time effect
function FX:UpdateAuras(e)
  for i, a in ipairs(self.auras) do
    if a.kit2 ~= 0 then a.left2 = a.left2 - e; if a.left2 <= 0 then a.kit2, a.left2 = 0, 0 end end
    if a.kit ~= 0 then
      a.left = a.left - e
      if a.left <= 0 then
        if a.kit2 ~= 0 then
          a.kit, a.left, a.kit2, a.left2, a.restore = a.kit2, a.left2, 0, 0, 0
          if not self:Kit(i, a.kit, false) then self:ClearAura(i) end
        else self:ClearAura(i) end
      elseif a.restore > 0 then
        a.restore = a.restore - e
        if a.restore <= 0 then
          a.restore = 0
          if not self:Kit(i, a.kit, false) then self:ClearAura(i) end
        end
      end
    end
    if self.stun[i] > 0 then self.stun[i] = max(0, self.stun[i] - e) end
  end
end

---------------------------------------------------------------- sprite pool
function FX:Sprite()
  for _, s in ipairs(self.pool) do if not s.on then return s end end
  if #self.pool >= POOL then return nil end
  local s = { tex = self.layer:CreateTexture(nil, "OVERLAY") }
  self.pool[#self.pool + 1] = s
  return s
end

-- mode: proj (fly a to b), burst (pop at a), rise (float up at a), fall (drop onto a), bubble (around
-- the cat), ring (an aura at the cat's feet), orbit (circle the cat), stay (stand still until removed)
function FX:Play(sprite, mode, ax, ay, bx, by, size, dur, tint)
  local s = self:Sprite(); if not s then return nil end
  s.on, s.age, s.mode, s.dur = true, 0, mode, dur or 0.45
  s.ax, s.ay, s.bx, s.by, s.size = ax, ay, bx or ax, by or ay, size or 40
  s.arc, s.spin, s.phase = (mode == "proj") and 18 or 0, 0, 0
  s.impact, s.impactTint, s.impactSize, s.kitSlot, s.kit, s.txt, s.shakeSlot, s.anim = nil, nil, 46, nil, nil, nil, nil, nil
  s.dieSlot, s.dieMob = nil, nil
  s.tex:SetTexture(PATH[sprite])
  if tint then s.tex:SetVertexColor(tint[1], tint[2], tint[3]) else s.tex:SetVertexColor(1, 1, 1) end
  s.rot = (mode == "proj" and bx) and atan2(by - ay, bx - ax) or 0
  s.tex:SetRotation(s.rot)
  if mode == "proj" or mode == "fall" then s.impact, s.impactTint = sprite, tint end
  s.tex:ClearAllPoints(); s.tex:SetSize(1, 1); s.tex:SetAlpha(0)
  s.tex:Show()
  return s
end

function FX:Stop(s)
  if s and s.on then s.on = false; s.tex:Hide() end
end

-- what happens when a projectile or falling sprite arrives: the impact burst, the game's visual on
-- the enemy, the damage number and the enemy's flinch
function FX:Land(s)
  local tint = s.impactTint or (s.impact and TCF.SPELL_FX.TINT[s.impact])
  if s.impact then self:Play("impact", "burst", s.bx, s.by, nil, nil, s.impactSize or 46, 0.3, tint) end
  if s.kit and s.kitSlot then self:Kit(s.kitSlot, s.kit, true) end
  if s.txt then self.hooks.float(s.txt, s.tx, s.ty, s.tr, s.tg, s.tb, s.big) end
  if s.shakeSlot then self.hooks.shake(s.shakeSlot, 0.2) end
  if s.anim and s.kitSlot then self:Anim(s.kitSlot, s.anim, 0.35) end
  -- the killing blow: the enemy falls when the shot arrives, not before
  if s.dieMob then self.hooks.die(s.dieSlot, s.dieMob); s.dieMob = nil end
end

function FX:Update(e)
  self.clock = self.clock + e
  for _, s in ipairs(self.pool) do
    if s.on then
      s.age = s.age + e
      local t = s.age / s.dur
      if t >= 1 and s.mode ~= "stay" then
        -- (lands while still taken, so the impact burst can't reuse this sprite and wipe what it carries)
        if s.mode == "proj" or s.mode == "fall" then self:Land(s) end
        s.on = false; s.tex:Hide()
      else
        local x, y, sz, a = s.ax, s.ay, s.size, 1
        local mode = s.mode
        if mode == "proj" then
          x = s.ax + (s.bx - s.ax) * t; y = s.ay + (s.by - s.ay) * t + sin(t * pi) * s.arc
          if s.spin ~= 0 then s.tex:SetRotation(s.rot - s.spin * s.age) end
        elseif mode == "fall" then x = s.bx - 30 * (1 - t); y = s.by + 130 * (1 - t)
        elseif mode == "burst" then sz = s.size * (0.5 + t); a = 1 - t
        elseif mode == "rise" then y = s.ay + 40 * t; sz = s.size * (0.8 + 0.4 * t); a = t < 0.6 and 1 or (1 - t) / 0.4
        elseif mode == "bubble" then sz = s.size * (0.9 + 0.1 * sin(t * 12)); a = t < 0.7 and 0.9 or (1 - t) / 0.3 * 0.9
        elseif mode == "ring" then sz = s.size * (0.75 + 0.35 * t); y = s.ay + 6 * t; a = t < 0.25 and t * 4 or (t < 0.6 and 1 or (1 - t) / 0.4)
        elseif mode == "orbit" then
          local ang = s.phase + t * pi * 3
          x = s.ax + cos(ang) * 58; y = s.ay + sin(ang) * 20
          sz = s.size * (0.85 + 0.15 * sin(ang))
          a = t < 0.15 and t / 0.15 or (t < 0.8 and 1 or (1 - t) / 0.2)
        elseif mode == "stay" then a = min(1, s.age * 3); y = s.ay + sin(s.age * 2) * 1.5 end
        s.tex:ClearAllPoints(); s.tex:SetSize(sz, sz); s.tex:SetPoint("CENTER", self.anchor, "BOTTOMLEFT", x, y); s.tex:SetAlpha(a)
      end
    end
  end
  -- lasting effects on enemies run out
  self:UpdateAuras(e)
  if self.fighting then self:UpdatePassives(e) end
end

---------------------------------------------------------------- damage numbers that wait for the shot
-- A shot or spell that flies to enemy i carries the number of the hit that follows it in the same
-- batch of fight events, so it shows when the shot lands.
function FX:TakePending(i)
  local s = i and self.pending[i]
  if s then self.pending[i] = nil end
  if s and s.on then self.carried[i] = s; return s end
end

function FX:EndBatch()
  for i in pairs(self.pending) do self.pending[i] = nil end
  for i in pairs(self.carried) do self.carried[i] = nil end
end

-- a "hit" or "crit" on enemy i with a shot or spell on its way: it carries the number (shown at x) and
-- the flinch until it lands; false when nothing is on its way (the hit shows at once)
function FX:CarryHit(i, txt, x, crit)
  local s = self:TakePending(i)
  if not s then return false end
  if crit then FX.Carry(s, txt, x, 150, 1, 0.82, 0.1, true, i) else FX.Carry(s, txt, x, 140, 1, 1, 1, false, i) end
  return true
end

-- the enemy in slot i (mob) died from a shot that is still flying: it falls when the shot lands
function FX:DieOnLand(i, mob)
  local s = i and self.carried[i]
  if not (s and s.on and mob) then return false end
  s.dieSlot, s.dieMob = i, mob
  return true
end

-- for TakePending: carry this number (shown at x, y) and enemy slot's flinch until the shot lands
function FX.Carry(s, txt, x, y, r, g, b, big, slot)
  s.txt, s.tx, s.ty, s.tr, s.tg, s.tb, s.big, s.shakeSlot = txt, x, y, r, g, b, big, slot
end

---------------------------------------------------------------- basic attacks
-- st: TCF:CombatStats() of the fighting cat (attack, shot, school); i: the enemy hit
-- returns true when the cat shot (its right paw holds the ranged weapon)
function FX:Swing(i, st, class)
  local tx, ty = self.hooks.slotPos(i)
  if not tx then return false end
  local attack = st and st.attack or "melee"
  -- a druid in Cat Form claws (its damage may still count as spell damage)
  if attack == "spell" and class == "DRUID" and TCF:AbilityKnown("DRUID", "cat") then attack = "melee" end
  if attack == "shoot" or attack == "wand" then
    local def = FX.SHOT[st.shot] or FX.SHOT.bow
    local tint = attack == "wand" and FX.SCHOOL_TINT[st.school or "arcane"] or nil
    local mx, my = def[7], def[8]
    local s = self:Play(def[1], "proj", mx, my, tx, ty, def[2], def[3], tint)
    if s then
      s.arc, s.spin = def[4], def[5]
      s.impact, s.impactTint, s.impactSize = attack == "wand" and "sparkle" or "impact", tint, attack == "wand" and 40 or 30
      s.kitSlot = i
      s.kit = attack == "wand" and TCF.SCHOOL_KITS and TCF.SCHOOL_KITS[st.school or "arcane"] or nil
      self.pending[i] = s
    end
    if def[6] then self:Play("muzzle", "burst", mx + 6, my, nil, nil, 30, 0.14) end
    return true
  end
  if attack == "spell" then
    local school = FX.CLASS_SCHOOL[class] or "arcane"
    self:Play("sparkle", "burst", tx, ty, nil, nil, 38, 0.3, FX.SCHOOL_TINT[school])
  else
    self:Play("slash", "burst", tx + random(-6, 6), ty + random(-6, 6), nil, nil, 34, 0.22)
  end
  -- Seal of Righteousness and the like: a sparkle with every basic hit
  for _, p in ipairs(self.passives) do
    if p[2] == "proc" then self:Play(p[1], "burst", tx + 10, ty + 14, nil, nil, 30, 0.35, p[3]) end
  end
  return false
end

---------------------------------------------------------------- abilities
local targets = { {}, {}, {} } -- reused: no tables made per cast
local function collect(self, info, all)
  local n = 0
  if all then
    for i = 1, 3 do
      local x, y = self.hooks.slotPos(i)
      if x then n = n + 1; targets[n].i, targets[n].x, targets[n].y = i, x, y end
    end
  else
    local x, y = self.hooks.slotPos(info.target)
    if x then n = 1; targets[1].i, targets[1].x, targets[1].y = info.target, x, y end
  end
  return n
end

local ENEMY_KINDS = { nuke = true, execute = true, drain = true, aoe = true, dot = true, stun = true }
-- abilities that hit only the target (whatever their sprite looks like)
local SINGLE_KINDS = { nuke = true, execute = true, drain = true, dot = true }
-- abilities whose damage comes as a "hit" event right after (that hit taps the cat, unless a shot carries it)
local HIT_KINDS = { nuke = true, execute = true, drain = true, aoe = true }

-- the game's kits for an ability: impact (when it lands) and aura (while it lasts)
function FX.KitsFor(class, key, sprite)
  local row = TCF.SPELL_KITS and TCF.SPELL_KITS[class] and TCF.SPELL_KITS[class][key]
  local impact, aura = row and row[2] or 0, row and row[3] or 0
  if impact == 0 and TCF.SCHOOL_KITS then impact = TCF.SCHOOL_KITS[TCF.SPELL_FX.SCHOOL[sprite] or "physical"] or 0 end
  return impact, aura
end

-- info: { key, kind, target, class } from the fight's "ability" event
-- returns true when the cat should tap for the cast now (no hit event will tap for it)
function FX:Ability(info)
  local fx = TCF.SPELL_FX.For(info.class, info.key, info.kind)
  if not fx then return true end
  local sprite, mode = fx[1], fx[2]
  local ab
  for _, a in ipairs(TCF.ABILITIES[info.class] or {}) do if a.key == info.key then ab = a; break end end
  local dur = ab and ab.dur or 0
  local onEnemy = ENEMY_KINDS[info.kind]
  local impact, aura = 0, 0
  if onEnemy then impact, aura = FX.KitsFor(info.class, info.key, sprite) end
  local n = collect(self, info, not SINGLE_KINDS[info.kind]
    and (mode == "each" or mode == "multi" or mode == "rain" or (mode == "stun" and info.kind == "stun")))
  local carried = false
  local cx, cy = FX.MUZZLE[1] - 8, FX.MUZZLE[2] + 20
  if mode == "proj" or mode == "multi" then
    for k = 1, n do
      local p = targets[k]
      local s = self:Play(sprite, "proj", cx, cy, p.x, p.y, 40, 0.35 + k * 0.05)
      if s then s.kitSlot, s.kit, s.anim = p.i, impact, ANIM_WOUND; self.pending[p.i] = s; carried = true end
    end
  elseif mode == "drain" then
    if n > 0 then
      self:Play(sprite, "proj", targets[1].x, targets[1].y, cx, cy, 36, 0.45)
      self:Kit(targets[1].i, impact, true)
    end
  elseif mode == "hit" or mode == "each" then
    for k = 1, n do
      local p = targets[k]
      self:Play(sprite, "burst", p.x, p.y, nil, nil, 60, 0.4)
      self:Kit(p.i, impact, true)
      self:Anim(p.i, ANIM_WOUND, 0.35)
    end
  elseif mode == "rain" then
    for k = 1, n do
      local p = targets[k]
      for j = 1, 2 do
        local s = self:Play(sprite, "fall", p.x, p.y, p.x + (j - 1.5) * 24, p.y, 34, 0.4 + j * 0.08)
        if s and j == 1 then s.kitSlot, s.kit = p.i, impact end
      end
    end
  elseif mode == "stun" then
    for k = 1, n do
      local p = targets[k]
      self:Play("stun", "rise", p.x, p.y + 46, nil, nil, 46, 1.2)
      if aura ~= 0 then self:Aura(p.i, aura, dur) else self:Kit(p.i, impact, true) end
      if info.kind == "stun" then self:Anim(p.i, ANIM_STUN, dur) end
    end
  elseif mode == "self" then self:Play(sprite, "rise", FX.CAT[1] + 5, FX.CAT[2] + 18, nil, nil, 50, 0.9)
  elseif mode == "bubble" then self:Play(sprite, "bubble", FX.CAT[1], FX.CAT[2] + 8, nil, nil, 120, 1.4, fx[3]) end
  -- damage over time: the game's aura on the enemy while it burns or bleeds
  if info.kind == "dot" and aura ~= 0 and n > 0 then self:Aura(info.target, aura, dur) end
  return not (HIT_KINDS[info.kind] and not carried)
end

---------------------------------------------------------------- passive abilities
-- called when a pack appears: the known passives play, and the ones that keep acting are kept
function FX:Spawn(class)
  for i = 1, 3 do self:ClearAura(i); self.stun[i] = 0 end
  local list = self.passives
  for k = #list, 1, -1 do list[k] = nil end
  if self.totem then self:Stop(self.totem); self.totem = nil end
  for _, a in ipairs(TCF.ABILITIES[class] or {}) do
    if (a.kind == "passive" or a.kind == "ward") and TCF:AbilityKnown(class, a.key) then
      local p = TCF.SPELL_FX.Passive(class, a.key)
      if p then
        list[#list + 1] = p
        local m = p[2]
        if m == "aura" then self:Play(p[1], "ring", FX.FEET[1], FX.FEET[2], nil, nil, 130, 1.3, p[3])
        elseif m == "form" then self:Play(p[1], "burst", FX.CAT[1], FX.CAT[2], nil, nil, 110, 0.7, p[3])
        elseif m == "orbs" then
          for k = 0, 2 do
            local s = self:Play(p[1], "orbit", FX.CAT[1], FX.CAT[2], nil, nil, 22, 2.5, p[3])
            if s then s.phase = k * 2 * pi / 3 end
          end
        elseif m == "totem" then
          self.totem = self:Play(p[1], "stay", FX.TOTEM[1], FX.TOTEM[2], nil, nil, 40, 1)
          self.totemT = 1
        elseif m == "guard" then self:Play(p[1], "bubble", FX.CAT[1], FX.CAT[2] + 8, nil, nil, 110, 0.8, p[3])
        elseif m == "pet" then self.petT = 0.8 end
      end
    end
  end
  self.fighting = true
end

-- the cat stops fighting (retreat, defeat, away): the totem goes, lasting effects end
function FX:Stand()
  self.fighting = false
  if self.totem then self:Stop(self.totem); self.totem = nil end
  for i = 1, 3 do self:ClearAura(i); self.stun[i] = 0 end
end

function FX:UpdatePassives(e)
  for _, p in ipairs(self.passives) do
    local m = p[2]
    if m == "pet" then
      self.petT = self.petT - e
      if self.petT <= 0 then
        self.petT = FX.PET_EVERY
        local i = self.hooks.target()
        local x, y
        if i then x, y = self.hooks.slotPos(i) end
        if x then
          self:Play(p[1], "burst", x - 6, y - 10, nil, nil, 44, 0.3, p[3])
          self.hooks.shake(i, 0.12)
        end
      end
    elseif m == "totem" and self.totem then
      self.totemT = self.totemT - e
      if self.totemT <= 0 then
        self.totemT = FX.TOTEM_EVERY
        local i = self.hooks.target()
        local x, y
        if i then x, y = self.hooks.slotPos(i) end
        if x then
          local s = self:Play("fire", "proj", FX.TOTEM[1], FX.TOTEM[2] + 16, x, y, 24, 0.3)
          if s then s.impactSize = 30 end
        end
      end
    end
  end
  if self.guardT > 0 then self.guardT = self.guardT - e end
end

-- the cat was hit: a guarding pet (the Voidwalker) shows its shield now and then
function FX:Hurt()
  if self.guardT > 0 then return end
  for _, p in ipairs(self.passives) do
    if p[2] == "guard" then
      self.guardT = FX.GUARD_EVERY
      self:Play(p[1], "bubble", FX.CAT[1], FX.CAT[2] + 8, nil, nil, 110, 0.6, p[3])
      return
    end
  end
end

-- the enemy in slot i died or left: its lasting effect ends, a shot on its way still lands
function FX:Gone(i)
  self:ClearAura(i)
  if self.stun[i] then self.stun[i] = 0 end
end

---------------------------------------------------------------- the cat holds its ranged weapon
-- While a cat that shoots is in a fight (also between packs, so its paw doesn't swap back and forth),
-- its right paw holds the bow, gun, crossbow, thrown weapon or wand it shoots with. A cosmetic weapon
-- is kept only when it is the same kind (a cosmetic bow for a bow or crossbow, a rifle for a gun...).
-- look: TCF:GetAppearance(); run: TCF.advRun; active: the fight is started.
FX.SHOT_ART = { bow = "wpn_bow", xbow = "wpn_bow", gun = "wpn_rifle", thrown = "wpn_dagger", wand = "wpn_wand" }
function FX.FightLook(look, run, class, active)
  local st = run and run.stats
  if not (active and st and not run.away and run.class == class) then return look end
  if (st.attack ~= "shoot" and st.attack ~= "wand") or not TCF.RangedLook then return look end
  local main = look.main
  if main and not main.gear and main.art == FX.SHOT_ART[st.shot] then return look end
  local rl = TCF:RangedLook(class)
  if not rl or (main and main.id == rl.id) then return look end
  local out = {}
  for k, v in pairs(look) do out[k] = v end
  out.main = rl
  return out
end

-- /run TapCatForever:AdvFxDebug()  (for testing) says whether the game's spell visuals can play on the
-- enemies, and how the cat's basic attack lands
local SHOT_WORDS = { bow = "shoots a bow", xbow = "shoots a crossbow", gun = "shoots a gun", thrown = "throws its weapon" }
function TCF:AdvFxDebug()
  local fx = self.advFx
  if not fx then print("TapCat fight visuals: open the Adventure tab first.") return end
  local f = fx.hooks.slotFrame(1)
  local api = f and ((f.mode == "scene" and f.actor and type(f.actor.SetSpellVisualKit) == "function" and "model actor")
    or (f.model and type(f.model.ApplySpellVisualKit) == "function" and "model frame")) or "none"
  local st = self:CombatStats()
  local how = st.attack == "shoot" and (SHOT_WORDS[st.shot] or "shoots")
    or st.attack == "wand" and ("wand bolts (" .. tostring(st.school or "arcane") .. ")")
    or st.attack == "spell" and "casts" or "melee"
  print(string.format("TapCat fight visuals: game spell visuals %s (API: %s), %d played; basic attack: %s",
    fx:KitsOn() and "on" or "off (cartoonSpellFx)", api, fx.kitsPlayed or 0, how))
end
