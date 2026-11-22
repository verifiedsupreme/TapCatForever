-- TapCatForever: animated effects on the expensive skins and cosmetics (1.6), as CatAnim.lua layers
-- by item id. Every Legendary cosmetic piece without its own entry gets a shine sweeping across it.
-- Positions are in the 512-unit canvas of CatVector.lua: the body is about x 114-398, y 256-460,
-- the head x 123-389, y 64-288.
local ADDON, TCF = ...
local A = TCF.ITEM_ANIM

-- spots inside the cat for glints
local FUR = { { 170, 300, 340, 440 }, { 160, 110, 350, 260 } }
local function glints(col, n, size, gap) return { kind = "glint", sprite = "a_spark", n = n or 3, spots = FUR, size = size or { 22, 34 }, life = 0.7, gap = gap or { 0.3, 1.6 }, color = col, blend = "ADD" } end
local function sweep(col, alpha, speed) return { kind = "scroll", sprite = "a_shine", regions = { "body", "head", "paws" }, scale = 300, vx = speed or 110, vy = 0, color = col, alpha = alpha or 0.65, blend = "ADD" } end
local function stars(col, alpha) return { kind = "scroll", sprite = "a_stars", regions = { "body", "head", "paws" }, scale = 210, vx = 9, vy = -5, color = col, alpha = alpha or 0.9, blend = "ADD" } end
local function glow(col, lo, hi, speed) return { kind = "pulse", sprite = "a_catglow", rect = { 0, 0, 512, 512 }, color = col, a = { lo or 0.25, hi or 0.6 }, speed = speed or 1.8, blend = "ADD", at = "behind" } end
local function embers(col, col2, n) return { kind = "particles", sprite = "a_ember", n = n or 6, box = { 130, 250, 382, 450 }, vx = { -10, 10 }, vy = { -80, -45 }, life = { 1.2, 2.0 }, size = { 11, 18 }, sway = 8, color = col, color2 = col2, blend = "ADD", at = "front" } end
local function wisps(col, n, at) return { kind = "particles", sprite = "a_wisp", n = n or 4, box = { 120, 200, 392, 440 }, vx = { -8, 8 }, vy = { -55, -30 }, life = { 1.8, 2.8 }, size = { 30, 46 }, sway = 10, color = col, alpha = 0.7, blend = "ADD", at = at or "front" } end
local function falling(sprite, col, n, size) return { kind = "particles", sprite = sprite, n = n or 4, box = { 90, 20, 422, 120 }, vx = { -14, 14 }, vy = { 50, 80 }, life = { 3.0, 4.2 }, size = size or { 18, 26 }, sway = 16, spin = { -1.5, 1.5 }, color = col, at = "front" } end
local function rising(sprite, col, n, size) return { kind = "particles", sprite = sprite, n = n or 4, box = { 150, 330, 362, 450 }, vx = { -8, 8 }, vy = { -70, -45 }, life = { 2.0, 3.0 }, size = size or { 16, 24 }, sway = 10, color = col, at = "front" } end
local function crownGlints(col) return { kind = "glint", sprite = "a_spark", n = 3, spots = { { 180, 40, 340, 120 } }, size = { 18, 28 }, life = 0.7, gap = { 0.3, 1.4 }, color = col, blend = "ADD", at = "front" } end

-- chest-only and boss cats
A.skin_diamond = { sweep({ 0.75, 0.9, 1 }, 0.75, 120), glints({ 0.85, 0.95, 1 }, 4, { 26, 40 }, { 0.2, 1.0 }) }
A.skin_golden = { sweep({ 1, 0.85, 0.45 }, 0.7, 100), glints({ 1, 0.9, 0.5 }, 3) }
local rb = glints(nil, 3); rb.rainbow = true
A.skin_rainbow = { { kind = "hue", target = "pattern", speed = 0.12 }, rb }
A.skin_clover = { falling("t_leaf", { 0.45, 0.85, 0.35 }, 3, { 16, 22 }) }
A.skin_zulian = { falling("t_leaf", { 0.5, 0.9, 0.3 }, 3, { 16, 22 }), glints({ 0.6, 1, 0.5 }, 2) }
A.skin_skeletal = { glow({ 0.35, 1, 0.5 }, 0.15, 0.45), wisps({ 0.45, 1, 0.55 }, 4) }
A.skin_onyxian = { embers({ 1, 0.7, 0.25 }, { 0.9, 0.2, 0.1 }, 6) }
A.skin_qiraji = { sweep({ 1, 0.85, 0.4 }, 0.6, 90), glints({ 0.4, 1, 0.9 }, 3) }
A.skin_patchwork = { rising("t_bubble", { 0.55, 1, 0.55 }, 4, { 14, 22 }) }
A.skin_scarlet = { glow({ 1, 0.85, 0.45 }, 0.15, 0.4, 1.4), glints({ 1, 0.9, 0.55 }, 3) }
A.skin_clockwork = { glints({ 1, 0.85, 0.4 }, 3, { 16, 26 }, { 0.1, 0.9 }) }
A.skin_ragefire = { embers({ 1, 0.65, 0.2 }, { 0.8, 0.15, 0.05 }, 4) }
A.skin_stonewatcher = { glints({ 0.45, 0.9, 1 }, 2, { 18, 28 }) }
A.skin_maraudon = { glints({ 0.85, 0.6, 1 }, 3, { 20, 32 }) }
-- achievement cats (the hardest goals)
A.skin_flamesaber = { { kind = "scroll", sprite = "a_firetile", regions = { "body", "head" }, scale = 200, vx = 0, vy = 45, alpha = 0.35, blend = "ADD" },
  embers({ 1, 0.75, 0.3 }, { 1, 0.25, 0.05 }, 7), glow({ 1, 0.45, 0.1 }, 0.15, 0.4, 2.4) }
A.skin_dreamsaber = { stars({ 0.85, 0.7, 1 }, 0.95), glints({ 0.85, 0.65, 1 }, 2), wisps({ 0.6, 0.4, 1 }, 3, "behind") }
A.skin_onyxpanther = { sweep({ 0.8, 1, 0.9 }, 0.55, 90), glints({ 0.7, 1, 0.8 }, 4, { 24, 36 }, { 0.2, 1.0 }) }
A.skin_bigglesworth = { falling("t_snow", { 0.8, 0.93, 1 }, 4, { 16, 22 }), glints({ 0.7, 0.9, 1 }, 2) }
A.skin_luckycat = { sweep({ 1, 0.85, 0.4 }, 0.55, 80), glints({ 1, 0.85, 0.35 }, 3), falling("t_coin", { 1, 0.85, 0.35 }, 2, { 18, 22 }) }
A.skin_zulpanther = { wisps({ 0.8, 0.35, 0.95 }, 4), glow({ 0.7, 0.2, 0.8 }, 0.12, 0.35) }
A.skin_mechanocat = { glints({ 0.4, 0.9, 1 }, 3, { 16, 26 }, { 0.1, 0.8 }) }
-- shop cats at the top of the price list
A.skin_spectral = { glow({ 0.45, 1, 0.95 }, 0.3, 0.75, 1.6), wisps({ 0.55, 1, 0.95 }, 4), wisps({ 0.55, 1, 0.95 }, 2, "behind") }
A.skin_galaxy = { stars({ 1, 1, 0.95 }, 1.0), { kind = "scroll", sprite = "a_nebula", regions = { "body", "head" }, scale = 260, vx = -6, vy = 3, alpha = 0.55, blend = "ADD" }, glints({ 0.9, 0.85, 1 }, 2) }
A.skin_manasaber = { stars({ 0.7, 0.9, 1 }, 0.8), glints({ 0.6, 0.85, 1 }, 2) }
A.skin_winterspring = { falling("t_snow", { 0.85, 0.95, 1 }, 4, { 16, 22 }), glints({ 0.7, 0.9, 1 }, 2) }
A.skin_fel = { embers({ 0.6, 1, 0.3 }, { 0.2, 0.7, 0.1 }, 6), glow({ 0.4, 1, 0.2 }, 0.12, 0.35) }
A.skin_mech = { glints({ 1, 0.4, 0.25 }, 2, { 16, 24 }, { 0.2, 1.2 }) }
A.skin_lion = { sweep({ 1, 0.85, 0.5 }, 0.5, 80) }
A.skin_lynx = { sweep({ 1, 0.6, 0.4 }, 0.45, 80), embers({ 1, 0.6, 0.3 }, { 0.8, 0.2, 0.1 }, 3) }
-- quest, expedition and crafted cats
A.skin_emberheart = { embers({ 1, 0.75, 0.3 }, { 1, 0.25, 0.05 }, 6), glow({ 1, 0.4, 0.1 }, 0.1, 0.3, 2.6) }
A.skin_runebound = { { kind = "pulse", key = "cat:pat_runes_body", color = { 0.4, 0.9, 1 }, a = { 0.0, 0.9 }, speed = 2.2, blend = "ADD", at = "body_x" },
  { kind = "pulse", key = "cat:pat_runes_head", color = { 0.4, 0.9, 1 }, a = { 0.0, 0.9 }, speed = 2.2, blend = "ADD", at = "head_x" } }
A.skin_questgiver = { glints({ 1, 0.85, 0.3 }, 2) }
A.skin_turnin = { glints({ 1, 0.85, 0.3 }, 2) }
A.skin_raidleader = { glints({ 1, 1, 1 }, 2, { 18, 28 }) }
A.skin_koi = { rising("t_bubble", { 0.6, 0.85, 1 }, 4, { 12, 20 }) }
-- furs
A.fur_spectral = { glow({ 0.5, 1, 0.95 }, 0.2, 0.55, 1.6) }
A.ach_fur = { stars({ 0.8, 0.85, 1 }, 0.8) }

-- Legendary cosmetics with their own effect
A.head_crown_ice = { crownGlints({ 0.7, 0.9, 1 }), falling("t_snow", { 0.85, 0.95, 1 }, 2, { 12, 18 }) }
A.ach_crown = { crownGlints({ 1, 0.9, 0.5 }) }
A.ach_wings = { { kind = "glint", sprite = "a_spark", n = 3, spots = { { 20, 130, 150, 330 }, { 362, 130, 492, 330 } }, size = { 20, 30 }, life = 0.8, gap = { 0.3, 1.4 }, color = { 1, 0.95, 0.7 }, blend = "ADD", at = "front" } }
A.craft_tl_felwings = { embers({ 0.6, 1, 0.3 }, { 0.2, 0.7, 0.1 }, 4) }
A.craft_tl_felwings[1].box = { 30, 150, 482, 330 }
A.acc_blacklotus = { { kind = "glint", sprite = "a_spark", n = 2, spots = { { 330, 90, 400, 150 } }, size = { 16, 24 }, life = 0.7, gap = { 0.5, 1.8 }, color = { 0.85, 0.5, 1 }, blend = "ADD", at = "front" } }

-- every other Legendary cosmetic piece (class Legendary looks, crafted Legendaries...): a shine sweeping across it
local SHINE = { { kind = "scroll", sprite = "a_shine", scale = 220, vx = 90, vy = 0, color = { 1, 0.95, 0.8 }, alpha = 0.7, blend = "ADD" } }
local SHINE_SLOTS = { head = true, chest = true, back = true, shoulder = true, main = true, off = true }
TCF.ANIM_LEGENDARY = SHINE
local animOf = TCF.AnimOf
function TCF.AnimOf(it)
  local a = animOf(it)
  if a then return a end
  if it and not it.gear and it.rarity == 5 and SHINE_SLOTS[it.slot] and it.source ~= "set" then return SHINE end
end
