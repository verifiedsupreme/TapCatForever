-- TapCatForever: the cartoon (vector-drawn) cat. Every visible gear piece has its own drawing,
-- made from its in-game icon (see tools/item_specs). Textures are cropped; TCF.VEC holds where
-- each one sits on the 512-unit canvas.
local ADDON, TCF = ...
local Cat = TCF.CatClass
local ART = TCF.ART_PATH .. "v\\"
local CANVAS = 512
local LIFT = 44          -- how far a resting paw hovers above its tapping spot (canvas units)
local STRIPE = 0.8       -- tabby stripes are the fur colour, darker

-- draw order: name -> { frame, layer, sublevel }. Frame 1 holds everything behind the head gear
-- (cape, body, chest, shoulders, head, face); frame 2 sits above it (accessories, racial
-- accessory, head gear, held items, paws). Slots with _a/_b/_f hold either a gear drawing (full
-- colour, in _f) or a cosmetic (_a main colour, _b trim colour, _f fixed colours); _x is where a
-- piece's animated layers go (CatAnim.lua), right above the piece.
local ORDER = {
  back_a = { 1, "BACKGROUND", -7 }, back_b = { 1, "BACKGROUND", -6 }, back_f = { 1, "BACKGROUND", -5 }, back_x = { 1, "BACKGROUND", -4 },
  body_t = { 1, "BACKGROUND", -3 }, belly = { 1, "BACKGROUND", -2 }, patB = { 1, "BACKGROUND", -1 }, patB2 = { 1, "BACKGROUND", 0 },
  body_marks_t = { 1, "BACKGROUND", 1 }, body_x = { 1, "BACKGROUND", 2 }, body_x2 = { 1, "BACKGROUND", 3 }, body_line = { 1, "BACKGROUND", 4 },
  chest_a = { 1, "BORDER", -8 }, chest_b = { 1, "BORDER", -7 }, chest_f = { 1, "BORDER", -6 }, chest_x = { 1, "BORDER", -5 },
  belt = { 1, "BORDER", -4 }, neck = { 1, "BORDER", -3 }, mane = { 1, "BORDER", -2 },
  -- shoulders: over the cape, chest and mane, under the head (it sits on them) and everything in frame 2
  shoulder_a = { 1, "BORDER", -1 }, shoulder_b = { 1, "BORDER", 0 }, shoulder_f = { 1, "BORDER", 1 }, shoulder_x = { 1, "BORDER", 2 },
  head_t = { 1, "ARTWORK", -8 }, patH = { 1, "ARTWORK", -7 }, patH2 = { 1, "ARTWORK", -6 }, head_marks_t = { 1, "ARTWORK", -5 },
  head_x = { 1, "ARTWORK", -4 }, head_x2 = { 1, "ARTWORK", -3 }, face = { 1, "ARTWORK", -2 }, iris = { 1, "ARTWORK", -1 },
  -- accessories: neck pieces (bow tie, scarf...) under the racial accessory, face pieces (shades,
  -- monocle...) over it (VecAccLayer moves them), so a dwarf beard covers a bow tie and shades sit on tusks
  acc_a = { 2, "BACKGROUND", -8 }, acc_b = { 2, "BACKGROUND", -7 }, acc_f = { 2, "BACKGROUND", -6 },
  race_a = { 2, "BACKGROUND", -4 }, race_b = { 2, "BACKGROUND", -3 }, race_f = { 2, "BACKGROUND", -2 },
  head_a = { 2, "BORDER", -8 }, head_b = { 2, "BORDER", -7 }, head_f = { 2, "BORDER", -6 },
  main_a = { 2, "ARTWORK", -8 }, main_b = { 2, "ARTWORK", -7 }, main_f = { 2, "ARTWORK", -6 }, main_x = { 2, "ARTWORK", -5 },
  offw_a = { 2, "ARTWORK", -4 }, offw_b = { 2, "ARTWORK", -3 }, offw_f = { 2, "ARTWORK", -2 }, offw_x = { 2, "ARTWORK", -1 },
  paw_L_t = { 2, "OVERLAY", -8 }, patPL = { 2, "OVERLAY", -7 }, paw_L_x = { 2, "OVERLAY", -6 }, paw_L = { 2, "OVERLAY", -5 },
  paw_R_t = { 2, "OVERLAY", -4 }, patPR = { 2, "OVERLAY", -3 }, paw_R_x = { 2, "OVERLAY", -2 }, paw_R = { 2, "OVERLAY", -1 },
  ring = { 2, "OVERLAY", 0 }, off_a = { 2, "OVERLAY", 1 }, off_b = { 2, "OVERLAY", 2 }, off_f = { 2, "OVERLAY", 3 }, off_x = { 2, "OVERLAY", 4 },
}
-- animated layers of head gear (the slot name head_x is the skin's head layer in frame 1)
ORDER.hat_x = { 2, "BORDER", -5 }
-- skin glow behind the whole cat, and particles behind it and in front of everything
ORDER.behind = { 1, "BACKGROUND", -8 }
ORDER.front = { 2, "OVERLAY", 6 }
TCF.VEC_ORDER = ORDER
-- which paw each piece follows
local FOLLOW = { paw_L_t = "L", paw_L = "L", patPL = "L", paw_L_x = "L", ring = "L", paw_R_t = "R", paw_R = "R", patPR = "R", paw_R_x = "R" }
for _, p in ipairs({ "_a", "_b", "_f", "_x" }) do FOLLOW["off" .. p] = "L"; FOLLOW["offw" .. p] = "L"; FOLLOW["main" .. p] = "R" end
TCF.VEC_FOLLOW = FOLLOW
-- face accessories draw over the racial accessory, neck accessories under it
local FACE_ACC = { acc_shades = true, acc_monocle = true, acc_eyepatch = true, acc_mustache = true, acc_flower = true }
local ANIM_ONLY = { body_x = true, body_x2 = true, head_x = true, head_x2 = true, paw_L_x = true, paw_R_x = true, hat_x = true,
  behind = true, front = true, back_x = true, chest_x = true, shoulder_x = true, main_x = true, offw_x = true, off_x = true }

function Cat:VecActive()
  return TCF.VEC and not self.opts.pixelOnly
end

function Cat:VecInit()
  if not TCF.VEC then return end
  local v = CreateFrame("Frame", nil, self.frame)
  v:SetAllPoints(self.frame)
  if v.SetFrameLevel and self.frame.GetFrameLevel then pcall(v.SetFrameLevel, v, (self.frame:GetFrameLevel() or 1) + 1) end
  v:Hide()
  -- a second frame just above for what is worn on and in front of the head (more draw sublevels)
  local v2 = CreateFrame("Frame", nil, v)
  v2:SetAllPoints(v)
  if v2.SetFrameLevel and v.GetFrameLevel then pcall(v2.SetFrameLevel, v2, (v:GetFrameLevel() or 1) + 1) end
  self.vec, self.vec2, self.vt, self.vplace = v, v2, {}, {}
  self.vframes = { v, v2 }
  for name, o in pairs(ORDER) do
    if not ANIM_ONLY[name] then
      local t = self.vframes[o[1]]:CreateTexture(nil, o[2], nil, o[3])
      t:Hide()
      self.vt[name] = t
    end
  end
  -- the cat itself
  local base = { body_t = "body_t", body_marks_t = "body_marks_t", belly = "belly", body_line = "body_line",
    head_t = "head_t", head_marks_t = "head_marks_t",
    paw_L_t = "paw_L_down_t", paw_L = "paw_L_down", paw_R_t = "paw_R_down_t", paw_R = "paw_R_down" }
  for slot, art in pairs(base) do self:VecSet(slot, "cat:" .. art) end
  self:VecFace(self.faceKind or "normal")
end

-- put art (a TCF.VEC key) into a slot texture; flip mirrors it left-right (off-hand weapons)
function Cat:VecSet(slot, key, flip)
  local t, e = self.vt[slot], key and TCF.VEC[key]
  if not e then t:Hide(); self.vplace[slot] = nil; return false end
  t:SetTexture(ART .. e[1])
  if flip then t:SetTexCoord(e[6], 0, 0, e[7]) else t:SetTexCoord(0, e[6], 0, e[7]) end
  self.vplace[slot] = { x = flip and (CANVAS - e[2] - e[4]) or e[2], y = e[3], w = e[4], h = e[5] }
  t:Show()
  self:VecPlace(slot)
  return true
end

function Cat:VecPlace(slot)
  local p, t = self.vplace[slot], self.vt[slot]
  if not p then return end
  local s = self.size / CANVAS
  local side = FOLLOW[slot]
  local lift = (side and not (self.pawState and self.pawState[side])) and LIFT or 0
  t:ClearAllPoints()
  t:SetSize(p.w * s, p.h * s)
  t:SetPoint("TOPLEFT", self.vec, "TOPLEFT", p.x * s, -(p.y - lift) * s)
end

function Cat:VecLayout()
  if not self.vec then return end
  for slot in pairs(self.vplace) do self:VecPlace(slot) end
  if self.AnimLayout then self:AnimLayout() end
end

function Cat:VecPaws()
  if not self.vec then return end
  for slot in pairs(FOLLOW) do self:VecPlace(slot) end
  if self.AnimPaws then self:AnimPaws() end
end

function Cat:VecFace(kind)
  if not self.vec then return end
  if not self:VecSet("face", "cat:face_" .. kind) then self:VecSet("face", "cat:face_normal") end
  -- coloured eyes (some skins) on the open-eyed faces
  local eyes = self.eyeColor
  if eyes and self:VecSet("iris", "cat:iris_" .. kind) then self.vt.iris:SetVertexColor(eyes[1], eyes[2], eyes[3])
  else self:VecSet("iris", nil) end
end

-- markings: a pattern item or a skin's overlay draws its own shapes; otherwise plain tabby stripes
local function patternOf(look)
  local skin = look.skin
  if skin then
    local ov = skin.overlay
    if ov then return ov[1], ov[2], ov[3] end
    return nil
  end
  local pat = look.pattern
  if pat then return pat.art, pat.c1, pat.c2 end
end

function Cat:VecMarkings(look, fur)
  local art, c1, c2 = patternOf(look)
  local name = art and art:gsub("^pat_", ""):gsub("^skin_", "")
  local key = name and ("cat:pat_" .. name .. "_")
  local any = key and (TCF.VEC[key .. "body"] or TCF.VEC[key .. "head"])
  c2 = c2 or c1
  for slot, part, col in pairs({ patB = { "body", c1 }, patB2 = { "body2", c2 }, patH = { "head", c1 }, patH2 = { "head2", c2 },
                                 patPL = { "paw_L", c1 }, patPR = { "paw_R", c1 } }) do
    local k = any and key .. part[1]
    if k and self:VecSet(slot, k) then self.vt[slot]:SetVertexColor(part[2][1], part[2][2], part[2][3])
    else self:VecSet(slot, nil) end
  end
  -- plain stripes only when no pattern is drawn (a plain skin like Bombay has none)
  local plain = not any and not look.skin
  self.vt.body_marks_t:SetShown(plain); self.vt.head_marks_t:SetShown(plain)
  -- lion's mane and eye colour come from the skin
  local skin = look.skin
  if skin and skin.mane and self:VecSet("mane", "cat:mane") then self.vt.mane:SetVertexColor(skin.mane[1], skin.mane[2], skin.mane[3])
  else self:VecSet("mane", nil) end
  self.eyeColor = skin and skin.eyes
  self:VecFace(self.faceKind or "normal")
end

function Cat:VecTint(r, g, b, a)
  for _, n in ipairs({ "body_t", "head_t", "paw_L_t", "paw_R_t" }) do
    self.vt[n]:SetVertexColor(r, g, b); self.vt[n]:SetAlpha(a or 1)
  end
  for _, n in ipairs({ "body_marks_t", "head_marks_t" }) do
    self.vt[n]:SetVertexColor(r * STRIPE, g * STRIPE, b * STRIPE); self.vt[n]:SetAlpha(a or 1)
  end
end

local function iconOf(it)
  return it and it.icon and string.lower(it.icon)
end

-- which drawing kinds each slot accepts. Real items often reuse another slot's icon (a belt icon
-- on a helm, a hood icon on a cape); that drawing sits where its own slot belongs, so refuse it.
local SLOT_KIND = { head = { head = true }, chest = { chest = true }, back = { back = true }, main = { weapon = true },
  off = { shield = true, held = true, weapon = true }, offw = { weapon = true }, shoulder = { shoulder = true }, race = { acc = true } }

-- the drawing keys for a look item: gear -> its icon drawing when it has one that fits the slot,
-- otherwise (most bows, guns and capes) the cosmetic version tinted with the gear's colours
local function artOf(it, slot)
  if not it then return nil end
  if it.gear then
    local k = iconOf(it)
    local e, ok = k and TCF.VEC[k], SLOT_KIND[slot]
    if e and (not ok or ok[e[8]]) then return k, nil end
  end
  local base = it.art and ("cos:" .. it.art .. ":")
  if base and (TCF.VEC[base .. "a"] or TCF.VEC[base .. "f"]) then return nil, base end
end

-- fill a three-part slot (prefix_a/_b/_f) from a look item
function Cat:VecSlot(prefix, it, flip)
  local gearKey, cosBase = artOf(it, prefix)
  if gearKey then
    self:VecSet(prefix .. "_f", gearKey, flip); self.vt[prefix .. "_f"]:SetVertexColor(1, 1, 1)
    self:VecSet(prefix .. "_a", nil); self:VecSet(prefix .. "_b", nil)
  elseif cosBase then
    local c1, c2 = it.c1 or { 1, 1, 1 }, it.c2 or it.c1 or { 1, 1, 1 }
    if self:VecSet(prefix .. "_a", cosBase .. "a", flip) then self.vt[prefix .. "_a"]:SetVertexColor(c1[1], c1[2], c1[3]) end
    if self:VecSet(prefix .. "_b", cosBase .. "b", flip) then self.vt[prefix .. "_b"]:SetVertexColor(c2[1], c2[2], c2[3]) end
    if self:VecSet(prefix .. "_f", cosBase .. "f", flip) then self.vt[prefix .. "_f"]:SetVertexColor(1, 1, 1) end
  else
    for _, p in ipairs({ "_a", "_b", "_f" }) do self:VecSet(prefix .. p, nil) end
  end
end

-- what kind of drawing an item is (weapon, shield, held, ...)
local function kindOf(it, slot)
  local gearKey, cosBase = artOf(it, slot)
  local e = gearKey and TCF.VEC[gearKey] or cosBase and (TCF.VEC[cosBase .. "a"] or TCF.VEC[cosBase .. "f"])
  return e and e[8]
end

-- look: slot -> item (from TCF:GetAppearance). Real gear shows its own drawing,
-- cosmetics show their cartoon version tinted with their colours.
function Cat:VecApply(look)
  self.is3d = false; self.disp3d = nil
  self.m3d:Hide(); self.pix:Hide()
  for _, m in pairs(self.held) do m:Hide() end
  self.vec:Show()
  local fur = look.skin or look.fur or TCF.ITEMS.fur_ginger
  self.rainbowFur = fur.rainbow
  self:VecTint(fur.c1[1], fur.c1[2], fur.c1[3], fur.alpha or 1)
  self:VecMarkings(look, fur)
  -- small pieces: only a drawing made for this very slot (no belt on the ring finger)
  for _, slot in ipairs({ "neck", "belt", "ring" }) do
    local it = look[slot]
    local k = it and it.gear and iconOf(it)
    local e = k and TCF.VEC[k]
    self:VecSet(slot, e and e[8] == slot and k or nil)
  end
  for _, slot in ipairs({ "head", "chest", "back", "shoulder", "acc", "race", "main" }) do self:VecSlot(slot, look[slot]) end
  self:VecAccLayer(look.acc)
  -- off hand: weapons are mirrored into the left paw; shields and held items have their own place
  if kindOf(look.off, "off") == "weapon" then
    self:VecSlot("offw", look.off, true); self:VecSlot("off", nil)
  else
    self:VecSlot("off", look.off); self:VecSlot("offw", nil)
  end
  self:VecPaws()
  -- animated layers (CatAnim.lua): set pieces, expensive skins and cosmetics, effects
  if self.AnimApply then self:AnimApply(look) end
end

-- face accessories (shades, monocle...) sit over the racial accessory, neck ones (bow tie, scarf...) under it
function Cat:VecAccLayer(it)
  local face = it and FACE_ACC[it.art]
  for i, p in ipairs({ "_a", "_b", "_f" }) do
    local t = self.vt["acc" .. p]
    if t.SetDrawLayer then t:SetDrawLayer("BACKGROUND", face and (i - 1) or (i - 9)) end
  end
end

---------------------------------------------------------------- tap effects
-- A few sprites burst from the paw on every tap; the equipped Tap Effect picks shape and colour.
local PAW_SPOT = { L = { 180, 464 }, R = { 332, 464 } }
local MAX_PARTS, LIFE, GRAVITY = 18, 0.55, 520

local function hue(h)
  local i = math.floor(h * 6) % 6
  local f = h * 6 - math.floor(h * 6)
  local q = 1 - f
  if i == 0 then return 1, f, 0 elseif i == 1 then return q, 1, 0 elseif i == 2 then return 0, 1, f
  elseif i == 3 then return 0, q, 1 elseif i == 4 then return f, 0, 1 else return 1, 0, q end
end

function Cat:VecBurst(side)
  local it = self.look and self.look.tap
  if not (it and self.vec and self.vec:IsShown()) then return end
  self.parts = self.parts or {}
  local spot = PAW_SPOT[side] or PAW_SPOT.L
  local out = side == "R" and 1 or -1
  for k = 1, 3 do
    local p
    for _, q in ipairs(self.parts) do if not q.on then p = q; break end end
    if not p then
      if #self.parts >= MAX_PARTS then return end
      p = { tex = (self.vec2 or self.vec):CreateTexture(nil, "OVERLAY", nil, 7) }
      self.parts[#self.parts + 1] = p
    end
    -- fan out upwards, leaning away from the body
    local a = math.rad(-90 + out * (15 + (k - 1) * 28) + (math.random() - 0.5) * 20)
    local speed = 170 + math.random() * 90
    p.on, p.age = true, 0
    p.x, p.y = spot[1] + out * 10, spot[2]
    p.vx, p.vy = math.cos(a) * speed, math.sin(a) * speed
    p.spin = (math.random() - 0.5) * 6
    p.size = 30 + math.random() * 10
    p.tex:SetTexture(ART .. "t_" .. it.art)
    if it.rainbow then p.tex:SetVertexColor(hue(math.random())) else p.tex:SetVertexColor(it.c1[1], it.c1[2], it.c1[3]) end
    p.tex:Show()
  end
end

function Cat:VecUpdate(elapsed)
  if self.AnimUpdate then self:AnimUpdate(elapsed) end
  if not self.parts then return end
  local s = self.size / CANVAS
  for _, p in ipairs(self.parts) do
    if p.on then
      p.age = p.age + elapsed
      local t = p.age / LIFE
      if t >= 1 then
        p.on = false; p.tex:Hide()
      else
        local x = p.x + p.vx * p.age
        local y = p.y + p.vy * p.age + GRAVITY * p.age * p.age * 0.5
        local sz = p.size * (0.6 + 0.6 * math.min(1, t * 4))
        p.tex:ClearAllPoints()
        p.tex:SetSize(sz * s, sz * s)
        p.tex:SetPoint("CENTER", self.vec, "TOPLEFT", x * s, -y * s)
        p.tex:SetAlpha(t < 0.55 and 1 or (1 - t) / 0.45)
        if p.tex.SetRotation then p.tex:SetRotation(p.spin * p.age) end
      end
    end
  end
end
