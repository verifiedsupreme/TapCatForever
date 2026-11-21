-- TapCatForever: the animated cat widget (used for the HUD cat and the wardrobe preview)
local ADDON, TCF = ...

local sin, floor, random = math.sin, math.floor, math.random
local ART = TCF.ART_PATH

-- logical pixel offsets (64px canvas) of a raised paw relative to its lowered pose
local PAW_UP_OFFSET = { L = { -6, -14 }, R = { 6, -14 } }
local PAD_COLOR = { 1.0, 0.62, 0.72 }

local function setTex(t, file)
  -- "NEAREST" keeps the pixel art crisp on clients that support a filter mode
  t:SetTexture(ART .. file, nil, nil, "NEAREST")
end

local function hsv(h)
  local i = floor(h * 6) % 6
  local f = h * 6 - floor(h * 6)
  local q, t = 1 - f, f
  if i == 0 then return 1, t, 0 elseif i == 1 then return q, 1, 0 elseif i == 2 then return 0, 1, t
  elseif i == 3 then return 0, q, 1 elseif i == 4 then return t, 0, 1 else return 1, 0, q end
end

local Cat = {}
Cat.__index = Cat

-- parent: frame to attach to; size: on-screen size of the 64px canvas
function TCF.CreateCat(parent, size, opts)
  opts = opts or {}
  local self = setmetatable({}, Cat)
  local f = CreateFrame("Frame", nil, parent)
  f:SetSize(size, size)
  self.frame, self.size, self.opts = f, size, opts
  self.tex = {}

  local function T(name, layer, sub)
    local t = f:CreateTexture(nil, layer, nil, sub)
    t:SetAllPoints(f)
    t:Hide()
    self.tex[name] = t
    return t
  end
  local function FX(name, layer, sub)
    local t = f:CreateTexture(nil, layer, nil, sub)
    t:SetSize(size * 1.25, size * 1.25)
    t:SetPoint("CENTER", f, "CENTER", 0, 0)
    t:Hide()
    self.tex[name] = t
    return t
  end

  FX("fxBack", "BACKGROUND", -8)
  T("back_a", "BACKGROUND", 0);  T("back_b", "BACKGROUND", 1)
  T("fur", "BORDER", 0)
  T("pattern_a", "BORDER", 1);   T("pattern_b", "BORDER", 2)
  T("chest_a", "BORDER", 3);     T("chest_b", "BORDER", 4)
  T("chest_glow", "BORDER", 5)
  T("face", "ARTWORK", 0)
  T("acc_a", "ARTWORK", 1);      T("acc_b", "ARTWORK", 2)
  T("head_a", "ARTWORK", 3);     T("head_b", "ARTWORK", 4)
  T("head_glow", "ARTWORK", 5)
  -- paws first, then held items, so weapons/shields sit in front of the paws
  for _, side in ipairs({ "L", "R" }) do
    for _, pose in ipairs({ "up", "down" }) do
      local a = T("paw" .. side .. pose .. "_a", "OVERLAY", 0)
      local b = T("paw" .. side .. pose .. "_b", "OVERLAY", 1)
      setTex(a, "paw_" .. side .. "_" .. pose .. "_a")
      setTex(b, "paw_" .. side .. "_" .. pose .. "_b")
      b:SetVertexColor(PAD_COLOR[1], PAD_COLOR[2], PAD_COLOR[3])
    end
  end
  T("main_a", "OVERLAY", 2);     T("main_b", "OVERLAY", 3)
  T("off_a", "OVERLAY", 4);      T("off_b", "OVERLAY", 5)
  FX("fxFront", "OVERLAY", 7)
  for _, n in ipairs({ "head_glow", "chest_glow" }) do self.tex[n]:SetBlendMode("ADD") end

  setTex(self.tex.fur, "cat_fur"); self.tex.fur:Show()
  self.tex.face:Show()

  -- weapon textures move with the paws, so give them explicit anchors
  for _, n in ipairs({ "main_a", "main_b", "off_a", "off_b" }) do
    local t = self.tex[n]; t:ClearAllPoints(); t:SetSize(size, size)
  end

  self.pawDown = { L = 0, R = 0 }
  self.blinkAt = GetTime() + 2 + random() * 3
  self.faceUntil, self.faceOverride = 0, nil
  self.t = 0
  self:SetPaw("L", false); self:SetPaw("R", false)
  self:SetFace("normal")

  if not opts.static then
    self.floaters = {}
    f:SetScript("OnUpdate", function(_, e) self:OnUpdate(e) end)
  end
  return self
end

function Cat:SetSize(size)
  self.size = size
  self.frame:SetSize(size, size)
  for _, n in ipairs({ "main_a", "main_b", "off_a", "off_b" }) do self.tex[n]:SetSize(size, size) end
  self.tex.fxBack:SetSize(size * 1.25, size * 1.25)
  self.tex.fxFront:SetSize(size * 1.25, size * 1.25)
  self:SetPaw("L", self.pawState and self.pawState.L)
  self:SetPaw("R", self.pawState and self.pawState.R)
end

function Cat:SetFace(kind)
  if self.faceKind == kind then return end
  self.faceKind = kind
  setTex(self.tex.face, "face_" .. kind)
end

-- down = true when the paw is tapping
function Cat:SetPaw(side, down)
  self.pawState = self.pawState or {}
  self.pawState[side] = down
  local up, dn = self.tex["paw" .. side .. "up_a"], self.tex["paw" .. side .. "down_a"]
  local upb, dnb = self.tex["paw" .. side .. "up_b"], self.tex["paw" .. side .. "down_b"]
  if down then up:Hide(); upb:Hide(); dn:Show(); dnb:Show()
  else dn:Hide(); dnb:Hide(); up:Show(); upb:Show() end
  -- the held item follows the paw
  local s = self.size / 64
  local ox, oy = 0, 0
  if not down then ox, oy = PAW_UP_OFFSET[side][1] * s, -PAW_UP_OFFSET[side][2] * s end
  local slot = side == "R" and "main" or "off"
  for _, part in ipairs({ "_a", "_b" }) do
    local t = self.tex[slot .. part]
    t:ClearAllPoints()
    t:SetPoint("TOPLEFT", self.frame, "TOPLEFT", ox, oy)
  end
end

function Cat:Tap(side)
  side = side or ((self.lastSide == "L") and "R" or "L")
  self.lastSide = side
  self:SetPaw(side, true)
  self.pawDown[side] = GetTime() + 0.09
end

local function applyPart(t, art, color, alpha)
  if not art then t:Hide(); return end
  setTex(t, art)
  t:SetVertexColor(color[1], color[2], color[3])
  t:SetAlpha(alpha or 1)
  t:Show()
end

-- look: slot -> item (from TCF:GetAppearance)
function Cat:ApplyAppearance(look)
  self.look = look
  local tex = self.tex
  -- fur
  local fur = look.fur or TCF.ITEMS.fur_ginger
  self.rainbowFur = fur.rainbow
  local fa = fur.alpha or 1
  tex.fur:SetVertexColor(fur.c1[1], fur.c1[2], fur.c1[3]); tex.fur:SetAlpha(fa)
  for _, side in ipairs({ "L", "R" }) do
    for _, pose in ipairs({ "up", "down" }) do
      local t = tex["paw" .. side .. pose .. "_a"]
      t:SetVertexColor(fur.c1[1], fur.c1[2], fur.c1[3]); t:SetAlpha(fa)
    end
  end
  -- two-part gear slots
  for _, slot in ipairs({ "back", "pattern", "chest", "acc", "head", "main", "off" }) do
    local it = look[slot]
    local a, b = tex[slot .. "_a"], tex[slot .. "_b"]
    if it then
      if TCF.PART_B[it.art] then
        applyPart(a, it.art .. "_a", it.c1)
        applyPart(b, it.art .. "_b", it.c2 or it.c1)
      else
        applyPart(a, it.art, it.c1); b:Hide()
      end
    else
      a:Hide(); b:Hide()
    end
  end
  -- legendary shimmer on head/chest
  for _, slot in ipairs({ "head", "chest" }) do
    local it, g = look[slot], tex[slot .. "_glow"]
    if it and it.rarity == 5 then
      setTex(g, it.art .. (TCF.PART_B[it.art] and "_a" or ""))
      g:SetVertexColor(1, 0.85, 0.5); g:Show()
    else g:Hide() end
  end
  -- effect
  tex.fxBack:Hide(); tex.fxFront:Hide()
  local fx = look.effect
  self.fx = nil
  if fx then
    local t = (fx.fxLayer == "back") and tex.fxBack or tex.fxFront
    t:SetTexture(ART .. fx.art)  -- smooth filtering for soft effects
    t:SetVertexColor(fx.c1[1], fx.c1[2], fx.c1[3])
    t:SetRotation(0)
    t:Show()
    self.fx = { tex = t, anim = fx.fxAnim, item = fx }
  end
end

---------------------------------------------------------------- animation
function Cat:OnUpdate(elapsed)
  local now = GetTime()
  self.t = self.t + elapsed
  local t = self.t
  -- paws
  for side, untilT in pairs(self.pawDown) do
    if untilT > 0 and now >= untilT then self.pawDown[side] = 0; self:SetPaw(side, false) end
  end
  -- face
  local face = "normal"
  if self.faceOverride and now < self.faceUntil then face = self.faceOverride
  elseif not self.opts.preview and TCF.inFrenzy then face = "focus" end
  if face == "normal" then
    if now >= self.blinkAt then
      face = "blink"
      if now >= self.blinkAt + 0.13 then self.blinkAt = now + 2.5 + random() * 4 end
    end
  end
  self:SetFace(face)
  -- effects
  local fx = self.fx
  if fx then
    local tex, a = fx.tex, fx.anim
    if a == "pulse" then tex:SetAlpha(0.55 + 0.3 * sin(t * 2.2))
    elseif a == "spin" then tex:SetRotation(t * 0.35); tex:SetAlpha(0.85)
    elseif a == "spinslow" then tex:SetRotation(t * 0.15); tex:SetAlpha(0.8 + 0.15 * sin(t * 1.3))
    elseif a == "flicker" then tex:SetAlpha(0.6 + 0.25 * sin(t * 9) * sin(t * 3.7))
    elseif a == "twinkle" then tex:SetAlpha(0.55 + 0.4 * sin(t * 3.1)); tex:SetRotation(sin(t * 0.5) * 0.15)
    elseif a == "float" then
      tex:ClearAllPoints(); tex:SetPoint("CENTER", self.frame, "CENTER", 0, (t * 6 % 12) - 6)
      tex:SetAlpha(0.75 + 0.2 * sin(t * 2))
    end
    if fx.item.rainbow then tex:SetVertexColor(hsv((t * 0.12) % 1)) end
  end
  if self.rainbowFur then
    local r, g, b = hsv((t * 0.06) % 1)
    r, g, b = 0.55 + 0.45 * r, 0.55 + 0.45 * g, 0.55 + 0.45 * b
    self.tex.fur:SetVertexColor(r, g, b)
    for _, side in ipairs({ "L", "R" }) do
      for _, pose in ipairs({ "up", "down" }) do self.tex["paw" .. side .. pose .. "_a"]:SetVertexColor(r, g, b) end
    end
  end
  local glowA = 0.25 + 0.2 * sin(t * 2.5)
  self.tex.head_glow:SetAlpha(glowA); self.tex.chest_glow:SetAlpha(glowA)
  -- floaters (hearts, text)
  if self.floaters then
    for i = #self.floaters, 1, -1 do
      local fl = self.floaters[i]
      fl.age = fl.age + elapsed
      local p = fl.age / fl.life
      if p >= 1 then
        fl.obj:Hide(); fl.obj.inUse = false; table.remove(self.floaters, i)
      else
        fl.obj:ClearAllPoints()
        fl.obj:SetPoint("CENTER", self.frame, "CENTER", fl.x + sin(fl.age * 4 + fl.x) * fl.wobble, fl.y + p * fl.rise)
        fl.obj:SetAlpha(p < 0.7 and 1 or (1 - p) / 0.3)
      end
    end
  end
end

function Cat:SetFaceFor(kind, seconds)
  self.faceOverride, self.faceUntil = kind, GetTime() + seconds
end

---------------------------------------------------------------- floating hearts / text
function Cat:GetFloater(kind)
  self.pool = self.pool or { tex = {}, text = {} }
  for _, o in ipairs(self.pool[kind]) do if not o.inUse then o.inUse = true; o:Show(); return o end end
  local o
  if kind == "tex" then
    o = self.frame:CreateTexture(nil, "OVERLAY", nil, 7)
    setTex(o, "ui_heart")
  else
    o = self.frame:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    o:SetShadowOffset(1, -1)
  end
  o.inUse = true
  table.insert(self.pool[kind], o)
  return o
end

function Cat:Float(obj, life, x, y, rise, wobble)
  if not self.floaters then return end
  table.insert(self.floaters, { obj = obj, age = 0, life = life, x = x, y = y, rise = rise, wobble = wobble or 0 })
end

function Cat:Pet()
  local s = self.size
  for i = 1, 3 do
    local h = self:GetFloater("tex")
    local sz = s * (0.14 + random() * 0.08)
    h:SetSize(sz, sz)
    self:Float(h, 1.4 + random() * 0.4, (random() - 0.5) * s * 0.6, s * 0.15, s * 0.5, s * 0.05)
  end
  self:SetFaceFor("happy", 1.2)
end

function Cat:Celebrate(text, r, g, b, header)
  self:SetFaceFor("happy", 2.5)
  if not TCF.db.ui.popups or not self.floaters then return end
  local fs = self:GetFloater("text")
  fs:SetText((header and ("|cffffffff" .. header .. "|r\n") or "") .. text)
  fs:SetTextColor(r, g, b)
  self:Float(fs, 3, 0, self.size * 0.55, self.size * 0.35)
  for i = 1, 5 do
    local h = self:GetFloater("tex")
    local sz = self.size * 0.12
    h:SetSize(sz, sz)
    self:Float(h, 1.6, (random() - 0.5) * self.size, self.size * 0.1, self.size * 0.6, self.size * 0.06)
  end
end

function Cat:ShowLoot(it, isNew)
  self:SetFaceFor(it.rarity >= 4 and "sparkle" or "happy", 2.5)
  if not TCF.db.ui.popups or not self.floaters then return end
  local fs = self:GetFloater("text")
  local col = TCF.RARITY[it.rarity].color
  fs:SetText("|T" .. TCF.Icon(it.icon) .. ":18:18|t " .. it.name .. (isNew and "" or " |cffaaaaaa(dupe)|r"))
  fs:SetTextColor(col[1], col[2], col[3])
  self:Float(fs, 3.5, 0, self.size * 0.45, self.size * 0.3)
end

function Cat:Toast(text, r, g, b)
  if not TCF.db.ui.popups or not self.floaters then return end
  local fs = self:GetFloater("text")
  fs:SetText(text); fs:SetTextColor(r or 1, g or 1, b or 1)
  self:Float(fs, 3, 0, self.size * 0.45, self.size * 0.3)
end
