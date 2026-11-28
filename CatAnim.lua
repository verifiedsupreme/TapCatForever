-- TapCatForever: animated layers on the cartoon cat (cosmetic set pieces, expensive skins and
-- cosmetics, effects). Data-driven: an art name in TCF.VEC_ANIM (set pieces, Sets/*.lua) or an
-- item id in TCF.ITEM_ANIM (skins and cosmetics, CosmeticFX.lua) lists the layers to add:
--   flip       { kind = "flip", keys = { VEC keys }, fps }                       flipbook (flickering flames)
--   pulse      { kind = "pulse", key = VEC key | sprite = "a_glow", rect = { x, y, w, h }, a = { lo, hi }, speed, flicker }
--   scroll     { kind = "scroll", sprite = "a_stars", mask = VEC key | regions = { "body", "head", "paws" },
--                scale, vx, vy }                                               a tile drifting inside a shape
--   particles  { kind = "particles", sprite, n, box = { x0, y0, x1, y1 }, vx = { lo, hi }, vy = { lo, hi },
--                life = { lo, hi }, size = { lo, hi }, color2, sway, spin, grow }  rising embers, snow, leaves...
--   glint      { kind = "glint", sprite, n, spots = { { x0, y0, x1, y1 }, ... }, life, size, gap = { lo, hi } }
--   hue        { kind = "hue", target = "fur" | "pattern", speed }               colour cycling
-- Every layer may also have color = { r, g, b } (or rainbow = true), alpha, blend ("ADD" or "BLEND") and
-- at = "behind" | "front" (draw behind the whole cat or in front of everything; a piece's layers default to
-- just above the piece). Positions are in the 512-unit canvas of CatVector.lua; sprites live in
-- Art/v/<sprite>.tga (tools/make_animfx.py). Cheap: a few textures per piece, nothing on small cats but
-- flips, pulses and scrolls, and nothing at all while the cat is hidden.
local ADDON, TCF = ...
local Cat = TCF.CatClass
local ART = TCF.ART_PATH .. "v\\"
local CANVAS, LIFT = 512, 44
local sin, floor, random, min, max = math.sin, math.floor, math.random, math.min, math.max

TCF.VEC_ANIM = TCF.VEC_ANIM or {}    -- art name -> layers
TCF.ITEM_ANIM = TCF.ITEM_ANIM or {}  -- item id -> layers
local SMALL = 90                     -- cats smaller than this get no particles or glints
local MASK_WRAP = "CLAMPTOBLACKADDITIVE"

local function animOf(it)
  if not it then return nil end
  -- (1.7.7) gear has no effects, except the made-up Legendaries (CustomGear.lua)
  if it.gear then return it.custom and TCF.ITEM_ANIM[it.id] or nil end
  return TCF.ITEM_ANIM[it.id] or (it.art and TCF.VEC_ANIM[it.art])
end
TCF.AnimOf = animOf

local function hsv(h)
  local i = floor(h * 6) % 6
  local f = h * 6 - floor(h * 6)
  local q = 1 - f
  if i == 0 then return 1, f, 0 elseif i == 1 then return q, 1, 0 elseif i == 2 then return 0, 1, f
  elseif i == 3 then return 0, q, 1 elseif i == 4 then return f, 0, 1 else return 1, 0, q end
end
local function rr(r, def) if type(r) == "table" then return r[1] + random() * (r[2] - r[1]) end return r or def end

-- where a worn piece's own layers go (its _x draw level) and which paw it follows
local PIECE_ORDER = { back = "back_x", chest = "chest_x", shoulder = "shoulder_x", head = "hat_x", main = "main_x", off = "off_x", offw = "offw_x" }
-- skin regions: the cat's own shapes used as masks, and where their layers draw
local REGION = {
  body = { mask = "cat:body_t", order = { "body_x", "body_x2" } },
  head = { mask = "cat:head_t", order = { "head_x", "head_x2" } },
  pawL = { mask = "cat:paw_L_down_t", order = { "paw_L_x" }, side = "L" },
  pawR = { mask = "cat:paw_R_down_t", order = { "paw_R_x" }, side = "R" },
}

---------------------------------------------------------------- texture pools
local function pool(self)
  local a = self.anim
  if not a then
    a = { tex = {}, used = {}, masks = {}, mused = {}, layers = {}, t = 0 }
    self.anim, self.aplace = a, {}
  end
  return a
end

-- a texture at a named draw level (TCF.VEC_ORDER), reused across appearances
local function getTex(self, order)
  local a = pool(self)
  local o = TCF.VEC_ORDER[order]
  local list = a.tex[order]
  if not list then list = {}; a.tex[order] = list end
  local n = (a.used[order] or 0) + 1
  a.used[order] = n
  local t = list[n]
  if not t then
    t = self.vframes[o[1]]:CreateTexture(nil, o[2], nil, o[3])
    list[n] = t
  end
  t:SetBlendMode("BLEND"); t:SetVertexColor(1, 1, 1); t:SetAlpha(1)
  if t.SetRotation then t:SetRotation(0) end
  if t.amask and t.RemoveMaskTexture then t:RemoveMaskTexture(t.amask) end
  t.amask = nil
  t:Show()
  return t
end

local function getMask(self, order)
  local frame = self.vframes[TCF.VEC_ORDER[order][1]]
  if not frame.CreateMaskTexture then return nil end
  local a = pool(self)
  local n = (a.mused[order] or 0) + 1
  a.mused[order] = n
  local list = a.masks[order]
  if not list then list = {}; a.masks[order] = list end
  local m = list[n]
  if not m then
    local o = TCF.VEC_ORDER[order]
    m = frame:CreateMaskTexture(nil, o[2], nil, o[3])
    if not m then return nil end
    list[n] = m
  end
  m:Show()
  return m
end

-- place a texture (or mask) at a canvas rectangle, following a paw when side is set
local function place(self, t, x, y, w, h, side)
  self.aplace[t] = { x = x, y = y, w = w, h = h, side = side }
  local s = self.size / CANVAS
  local lift = (side and not (self.pawState and self.pawState[side])) and LIFT or 0
  t:ClearAllPoints()
  t:SetSize(w * s, h * s)
  t:SetPoint("TOPLEFT", self.vec, "TOPLEFT", x * s, -(y - lift) * s)
end

function Cat:AnimLayout()
  if not self.aplace then return end
  -- particles and glints come and go with the cat's size (SMALL): build them again when it crosses
  if self.animLook and ((self.size < SMALL) ~= self.animSmall) then self:AnimApply(self.animLook); return end
  for t, p in pairs(self.aplace) do place(self, t, p.x, p.y, p.w, p.h, p.side) end
end

function Cat:AnimPaws()
  if not self.aplace then return end
  for t, p in pairs(self.aplace) do if p.side then place(self, t, p.x, p.y, p.w, p.h, p.side) end end
end

-- show a TCF.VEC drawing in a texture at its own place (mirrored for an off-hand weapon)
local function setKey(self, t, key, side, flip)
  local e = TCF.VEC[key]
  if not e then t:Hide(); return false end
  t:SetTexture(ART .. e[1])
  if flip then t:SetTexCoord(e[6], 0, 0, e[7]) else t:SetTexCoord(0, e[6], 0, e[7]) end
  place(self, t, flip and (CANVAS - e[2] - e[4]) or e[2], e[3], e[4], e[5], side)
  return true
end

local function colour(t, L, a)
  local c = L.color
  if c then t:SetVertexColor(c[1], c[2], c[3]) end
  t:SetAlpha((L.alpha or 1) * (a or 1))
  if L.blend then t:SetBlendMode(L.blend) end
end

---------------------------------------------------------------- layer kinds
local KIND = {}

KIND.flip = function(self, L, ctx)
  local t = getTex(self, ctx.order)
  colour(t, L)
  return { t = t, keys = L.keys, fps = L.fps or 8, cur = 0, side = ctx.side, flip = ctx.flip,
    update = function(st, now)
      local i = floor(now * st.fps) % #st.keys + 1
      if i ~= st.cur then st.cur = i; setKey(self, st.t, st.keys[i], st.side, st.flip) end
    end }
end

KIND.pulse = function(self, L, ctx)
  local t = getTex(self, ctx.order)
  if L.key then
    if not setKey(self, t, L.key, ctx.side, ctx.flip) then t:Hide(); return nil end
  else
    t:SetTexture(ART .. L.sprite); t:SetTexCoord(0, 1, 0, 1)
    local r = L.rect or { 0, 0, CANVAS, CANVAS }
    local x = ctx.flip and (CANVAS - r[1] - r[3]) or r[1]
    place(self, t, x, r[2], r[3], r[4], ctx.side)
  end
  colour(t, L)
  local lo, hi = (L.a or { 0.4, 1 })[1], (L.a or { 0.4, 1 })[2]
  return { t = t, update = function(st, now)
    local k = 0.5 + 0.5 * sin(now * (L.speed or 2) + (L.phase or 0))
    if L.flicker then k = k * (0.8 + 0.2 * sin(now * 13.1) * sin(now * 7.7)) end
    st.t:SetAlpha((L.alpha or 1) * (lo + (hi - lo) * k))
    if L.rainbow then st.t:SetVertexColor(hsv((now * 0.1) % 1)) end
  end }
end

-- a tile drifting inside shapes: one tile texture and one mask per shape
KIND.scroll = function(self, L, ctx)
  local parts = {}
  local shapes = {}
  if ctx.regions then
    for _, r in ipairs(ctx.regions) do shapes[#shapes + 1] = r end
  else
    shapes[1] = { mask = L.mask or ctx.mask, order = ctx.order, side = ctx.side, flip = ctx.flip }
  end
  for _, sh in ipairs(shapes) do
    local e = sh.mask and TCF.VEC[sh.mask]
    local m = e and getMask(self, sh.order)
    if m then
      local t = getTex(self, sh.order)
      t:SetTexture(ART .. L.sprite, "REPEAT", "REPEAT")
      local x = sh.flip and (CANVAS - e[2] - e[4]) or e[2]
      place(self, t, x, e[3], e[4], e[5], sh.side)
      -- the mask uses the whole power-of-two texture, so it spans past the drawing's own box
      m:SetTexture(ART .. e[1], MASK_WRAP, MASK_WRAP)
      if sh.flip and m.SetTexCoord then m:SetTexCoord(1, 0, 0, 1) end
      local mw, mh = e[4] / e[6], e[5] / e[7]
      place(self, m, sh.flip and (CANVAS - e[2] - mw) or e[2], e[3], mw, mh, sh.side)
      t:AddMaskTexture(m); t.amask = m
      colour(t, L)
      parts[#parts + 1] = { t = t, x = x, y = e[3], w = e[4], h = e[5] }
    end
  end
  if #parts == 0 then return nil end
  local scale = L.scale or 160
  return { update = function(st, now)
    local ox, oy = (L.vx or 0) * now, (L.vy or 0) * now
    for _, p in ipairs(parts) do
      local u, v = (p.x - ox) / scale, (p.y - oy) / scale
      p.t:SetTexCoord(u, u + p.w / scale, v, v + p.h / scale)
      if L.pulse then p.t:SetAlpha((L.alpha or 1) * (0.55 + 0.45 * sin(now * L.pulse))) end
      if L.rainbow then p.t:SetVertexColor(hsv((now * 0.1) % 1)) end
    end
  end }
end

local function spawnIn(box) return box[1] + random() * (box[3] - box[1]), box[2] + random() * (box[4] - box[2]) end

KIND.particles = function(self, L, ctx)
  if self.size < SMALL then return nil end
  local list = {}
  local n = L.n or 5
  for i = 1, n do
    local t = getTex(self, ctx.order == "behind" and "behind" or "front")
    t:SetTexture(ART .. L.sprite); t:SetTexCoord(0, 1, 0, 1)
    colour(t, L, 0)
    local life = rr(L.life, 1.5)
    list[i] = { t = t, age = -life * (i - 1) / n, life = life }
  end
  local c1, c2 = L.color or { 1, 1, 1 }, L.color2
  return { update = function(st, now, dt)
    local s = self.size / CANVAS
    for _, p in ipairs(list) do
      p.age = p.age + dt
      if p.age >= 0 and (not p.x or p.age >= p.life) then
        if p.x then p.age = p.age - p.life end
        p.life = rr(L.life, 1.5)
        p.x, p.y = spawnIn(L.box)
        p.vx, p.vy, p.size, p.spin, p.ph = rr(L.vx, 0), rr(L.vy, -50), rr(L.size, 14), rr(L.spin, 0), random() * 6.28
      end
      if p.age < 0 or not p.x then p.t:Hide()
      else
        local k = p.age / p.life
        local x = p.x + p.vx * p.age + (L.sway and sin(p.age * 3 + p.ph) * L.sway or 0)
        local y = p.y + p.vy * p.age
        local sz = p.size * (L.grow and (1 + L.grow * k) or 1)
        p.t:ClearAllPoints()
        p.t:SetSize(sz * s, sz * s)
        p.t:SetPoint("CENTER", self.vec, "TOPLEFT", x * s, -y * s)
        local a = k < 0.15 and k / 0.15 or (k > 0.6 and (1 - k) / 0.4 or 1)
        p.t:SetAlpha((L.alpha or 1) * a)
        if c2 then p.t:SetVertexColor(c1[1] + (c2[1] - c1[1]) * k, c1[2] + (c2[2] - c1[2]) * k, c1[3] + (c2[3] - c1[3]) * k)
        elseif L.rainbow then p.t:SetVertexColor(hsv((now * 0.15 + p.ph) % 1)) end
        if p.spin ~= 0 and p.t.SetRotation then p.t:SetRotation(p.spin * p.age) end
        p.t:Show()
      end
    end
  end }
end

-- glints: a sparkle pops up somewhere in a spot, grows, turns a little and fades, then waits
KIND.glint = function(self, L, ctx)
  if self.size < SMALL then return nil end
  local list = {}
  for i = 1, L.n or 3 do
    local t = getTex(self, ctx.order == "behind" and "behind" or "front")
    t:SetTexture(ART .. (L.sprite or "a_spark")); t:SetTexCoord(0, 1, 0, 1)
    colour(t, L, 0)
    list[i] = { t = t, age = -rr(L.gap, 0.8) * i, life = L.life or 0.7 }
  end
  local spots = L.spots
  if spots == "piece" or spots == "pieceSides" then
    -- inside the worn piece's own drawing (inset, so glints land on the piece, not its empty corners);
    -- "pieceSides": its outer thirds only (a pair of pauldrons drawn as one picture)
    local e = ctx.mask and TCF.VEC[ctx.mask]
    if not e then for _, p in ipairs(list) do p.t:Hide() end return nil end
    local x0, y0, w, h = e[2], e[3], e[4], e[5]
    if spots == "piece" then
      spots = { { x0 + w * 0.2, y0 + h * 0.2, x0 + w * 0.8, y0 + h * 0.8 } }
    else
      spots = { { x0 + w * 0.08, y0 + h * 0.2, x0 + w * 0.3, y0 + h * 0.75 }, { x0 + w * 0.7, y0 + h * 0.2, x0 + w * 0.92, y0 + h * 0.75 } }
    end
  end
  return { update = function(st, now, dt)
    local s = self.size / CANVAS
    for _, p in ipairs(list) do
      p.age = p.age + dt
      if p.age >= p.life then
        p.age = -rr(L.gap, 0.8); p.x = nil
      elseif p.age >= 0 and not p.x then
        p.x, p.y = spawnIn(spots[random(#spots)])
        p.size = rr(L.size, 26)
      end
      if p.age < 0 or not p.x then p.t:Hide()
      else
        local k = p.age / p.life
        local g = sin(k * math.pi)
        local sz = p.size * (0.3 + 0.7 * g)
        p.t:ClearAllPoints(); p.t:SetSize(sz * s, sz * s)
        p.t:SetPoint("CENTER", self.vec, "TOPLEFT", p.x * s, -p.y * s)
        p.t:SetAlpha((L.alpha or 1) * g)
        if p.t.SetRotation then p.t:SetRotation(k * 0.8) end
        p.t:Show()
      end
    end
  end }
end

-- colour cycling: the fur tint (pastel, like the Prismatic fur) or the skin's markings
KIND.hue = function(self, L, ctx)
  local look = ctx.look
  return { update = function(st, now)
    local r, g, b = hsv((now * (L.speed or 0.08)) % 1)
    if L.target == "fur" then
      local k = L.soft or 0.45
      self:VecTint(1 - k + k * r, 1 - k + k * g, 1 - k + k * b, look and look.skin and look.skin.alpha)
    else
      for _, n in ipairs({ "patB", "patB2", "patH", "patH2", "patPL", "patPR" }) do
        local t = self.vt[n]
        if t and t:IsShown() then t:SetVertexColor(0.35 + 0.65 * r, 0.35 + 0.65 * g, 0.35 + 0.65 * b) end
      end
    end
  end }
end

---------------------------------------------------------------- apply / update
local function addLayers(self, layers, ctx)
  local a = self.anim
  for _, L in ipairs(layers) do
    local mk = KIND[L.kind]
    local c = ctx
    if L.at then c = setmetatable({ order = L.at, side = nil }, { __index = ctx }) end
    local st = mk and mk(self, L, c)
    if st then a.layers[#a.layers + 1] = st end
  end
end

-- every cat that has shown a look, so the Appearance tab's "Animated cosmetics" box can redraw them all
local CATS = setmetatable({}, { __mode = "k" })

-- animations on unless the player turned them off (db.ui.anim, Appearance tab)
function TCF:AnimEnabled()
  local ui = self.db and self.db.ui
  return not (ui and ui.anim == false)
end

function TCF:SetAnimEnabled(on)
  if self.db and self.db.ui then self.db.ui.anim = on and true or false end
  -- draw each cat's look again (undoing a colour-cycling skin's last tint); that calls AnimApply
  for c in pairs(CATS) do if c.look and c.ApplyAppearance then c:ApplyAppearance(c.look) end end
end

-- look: what VecApply drew. Hides last look's layers and builds this one's.
function Cat:AnimApply(look)
  local a = pool(self)
  for _, list in pairs(a.tex) do for _, t in ipairs(list) do t:Hide() end end
  for _, list in pairs(a.masks) do for _, m in ipairs(list) do m:Hide() end end
  wipe(a.used); wipe(a.mused); wipe(a.layers); wipe(self.aplace)
  CATS[self] = true
  self.animLook, self.animSmall = look, self.size < SMALL
  if not TCF:AnimEnabled() then return end
  -- worn pieces
  local offIsWeapon = self.vt.offw_f:IsShown() or self.vt.offw_a:IsShown()
  for _, slot in ipairs({ "back", "chest", "shoulder", "head", "main", "off" }) do
    local it = look[slot]
    local layers = TCF.AnimOf(it)
    if layers then
      local drawSlot = (slot == "off" and offIsWeapon) and "offw" or slot
      local side = TCF.VEC_FOLLOW[drawSlot .. "_x"]
      local base = it.vec or (it.art and ("cos:" .. it.art .. ":f"))
      if base and not it.vec and not TCF.VEC[base] then base = "cos:" .. it.art .. ":a" end
      addLayers(self, layers, { order = PIECE_ORDER[drawSlot], side = side, flip = drawSlot == "offw", mask = base, look = look })
    end
  end
  -- effect (auras): their layers say where they draw
  local fx = TCF.AnimOf(look.effect)
  if fx then addLayers(self, fx, { order = "behind", look = look }) end
  -- skin: layers inside the cat's own shapes (scroll), glints, particles, glows, colour cycling
  local skin = TCF.AnimOf(look.skin) or (not look.skin and TCF.AnimOf(look.fur))
  if skin then
    local nScroll = 0
    for _, L in ipairs(skin) do
      local ctx = { order = "front", look = look }
      if L.kind == "scroll" then
        nScroll = nScroll + 1
        local regions = {}
        for _, rn in ipairs(L.regions or { "body", "head" }) do
          if rn == "paws" then
            if nScroll == 1 then
              regions[#regions + 1] = { mask = REGION.pawL.mask, order = "paw_L_x", side = "L" }
              regions[#regions + 1] = { mask = REGION.pawR.mask, order = "paw_R_x", side = "R" }
            end
          else
            local R = REGION[rn]
            local order = R and R.order[min(nScroll, #R.order)]
            if order then regions[#regions + 1] = { mask = R.mask, order = order } end
          end
        end
        ctx.regions = regions
      end
      addLayers(self, { L }, ctx)
    end
  end
  a.t = 0
  if #a.layers > 0 then self:AnimUpdate(0) end
end

function Cat:AnimUpdate(elapsed)
  local a = self.anim
  if not a or #a.layers == 0 or not (self.vec and self.vec:IsShown()) then return end
  a.t = a.t + elapsed
  for _, st in ipairs(a.layers) do st:update(a.t, elapsed) end
end

---------------------------------------------------------------- Appearance tab: on or off
-- "Animated cosmetics" check box right of the slot title (UI.lua calls this while building the page)
TCF.UI = TCF.UI or {}
function TCF.UI.AnimCheck(page)
  local cb = CreateFrame("CheckButton", nil, page, "UICheckButtonTemplate")
  cb:SetSize(22, 22); cb:SetPoint("TOPRIGHT", page, "TOPRIGHT", -132, -50)
  local t = TCF.UI.Text(cb, "GameFontHighlight", "Animated cosmetics", "LEFT"); t:SetPoint("LEFT", cb, "RIGHT", 2, 1)
  cb:SetScript("OnShow", function(s) s:SetChecked(TCF:AnimEnabled()) end)
  cb:SetScript("OnClick", function(s)
    TCF:SetAnimEnabled(s:GetChecked() and true or false)
    TCF:PlaySound("click")
  end)
  TCF.UI.Tip(cb, function(tt)
    tt:AddLine("Animated cosmetics", 1, 0.82, 0)
    tt:AddLine("Moving effects on cosmetics and skins: flames, drifting stars, sparkles, embers and glows. Turn it off for still pictures. You keep everything either way.", 1, 1, 1, true)
  end)
  cb:SetChecked(TCF:AnimEnabled())
  page.animCheck, TCF.UI.animCheckBox = cb, cb
  return cb
end
