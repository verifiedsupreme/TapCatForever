-- TapCatForever: the cartoon (vector-drawn) cat. Every visible gear piece has its own drawing,
-- made from its in-game icon (see tools/item_specs). Textures are cropped; TCF.VEC holds where
-- each one sits on the 512-unit canvas.
local ADDON, TCF = ...
local Cat = TCF.CatClass
local ART = TCF.ART_PATH .. "v\\"
local CANVAS = 512
local LIFT = 20          -- how far a resting paw hovers above its tapping spot (canvas units)
local STRIPE = 0.8       -- tabby stripes are the fur colour, darker

-- draw order: name -> { layer, sublevel }
local ORDER = {
  body_t = { "BACKGROUND", 0 }, body_marks_t = { "BACKGROUND", 1 }, belly = { "BACKGROUND", 2 }, body_line = { "BACKGROUND", 3 },
  chest = { "BORDER", 0 }, belt = { "BORDER", 1 }, neck = { "BORDER", 2 },
  head_t = { "BORDER", 3 }, head_marks_t = { "BORDER", 4 }, face = { "BORDER", 5 },
  head = { "ARTWORK", 0 }, main = { "ARTWORK", 1 }, offw = { "ARTWORK", 2 },
  paw_L_t = { "OVERLAY", 0 }, paw_L = { "OVERLAY", 1 }, paw_R_t = { "OVERLAY", 2 }, paw_R = { "OVERLAY", 3 },
  ring = { "OVERLAY", 4 }, off = { "OVERLAY", 5 },
}
-- which paw each piece follows
local FOLLOW = { paw_L_t = "L", paw_L = "L", ring = "L", off = "L", offw = "L", paw_R_t = "R", paw_R = "R", main = "R" }

function Cat:VecActive()
  return TCF.VEC and not self.opts.pixelOnly
end

function Cat:VecInit()
  if not TCF.VEC then return end
  local v = CreateFrame("Frame", nil, self.frame)
  v:SetAllPoints(self.frame)
  if v.SetFrameLevel and self.frame.GetFrameLevel then pcall(v.SetFrameLevel, v, (self.frame:GetFrameLevel() or 1) + 1) end
  v:Hide()
  self.vec, self.vt, self.vplace = v, {}, {}
  for name, o in pairs(ORDER) do
    local t = v:CreateTexture(nil, o[1], nil, o[2])
    t:Hide()
    self.vt[name] = t
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
end

function Cat:VecPaws()
  if not self.vec then return end
  for slot in pairs(FOLLOW) do self:VecPlace(slot) end
end

function Cat:VecFace(kind)
  if not self.vec then return end
  if not self:VecSet("face", "cat:face_" .. kind) then self:VecSet("face", "cat:face_normal") end
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

-- look: slot -> item (from TCF:GetAppearance). Real gear shows its own drawing.
function Cat:VecApply(look)
  self.is3d = false; self.disp3d = nil
  self.m3d:Hide(); self.pix:Hide()
  for _, m in pairs(self.held) do m:Hide() end
  self.vec:Show()
  local fur = look.skin or look.fur or TCF.ITEMS.fur_ginger
  self.rainbowFur = fur.rainbow
  self:VecTint(fur.c1[1], fur.c1[2], fur.c1[3], fur.alpha or 1)
  for _, slot in ipairs({ "head", "chest", "neck", "belt", "ring" }) do
    self:VecSet(slot, iconOf(look[slot]))
  end
  -- main hand in the right paw
  self:VecSet("main", iconOf(look.main))
  -- off hand: weapons are mirrored into the left paw; shields and held items have their own place
  local off = iconOf(look.off)
  local e = off and TCF.VEC[off]
  if e and e[8] == "weapon" then
    self:VecSet("offw", off, true); self:VecSet("off", nil)
  else
    self:VecSet("off", off); self:VecSet("offw", nil)
  end
  self:VecPaws()
end
