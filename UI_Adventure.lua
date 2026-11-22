-- TapCatForever: Adventure page (idle fights with 3D creature models over the zone's artwork)
local ADDON, TCF = ...
local floor, max, min, random = math.floor, math.max, math.min, math.random

local ANIM_STAND, ANIM_DEATH, ANIM_ATTACK, ANIM_WOUND = 0, 1, 16, 9
-- if a creature model can't load, borrow another enemy's model from the zone;
-- as a last resort show a pixel-art monster (never an icon)
local PIXEL_MONSTER = "Interface\\AddOns\\TapCatForever\\Art\\mob_shadow"

local function short(n)
  n = floor(n + 0.5)
  if n >= 1e6 then return string.format("%.1fM", n / 1e6) end
  if n >= 1e4 then return string.format("%.1fK", n / 1e3) end
  return tostring(n)
end

------------------------------------------------ enemy models: measure each one and fit it on screen
-- Each enemy is an actor in its own ModelScene (an invisible frame much bigger than the slot,
-- so models are never cut off and can overlap). When the model loads we read its bounding box,
-- scale it to a set on-screen height, stand its feet on the ground line and aim our own camera
-- at it. The scene is centred on the ground line and the camera sits at ground height, looking
-- level, so the ground is one flat line at every depth (nothing sinks below it) and the
-- scene's lower half stays empty. If the ModelScene API is missing or fails, the slot falls back
-- to the old PlayerModel with a fixed camera distance.
local FIT = {
  TRASH_PX = 112, BOSS_PX = 165, -- on-screen height of a fitted model (before the small size nudge)
  GROUND = 5,                    -- feet stand this far above the slot's bottom edge
  HEADROOM = 14,                 -- the model's top stays this far under the slot's top (name, health bar)
  EDGE = 4,                      -- models stay this far inside their scene and the fight panel
  CAT_EDGE = 170,                -- models stay right of this x in the fight panel (the cat and its bar)
  TURN = 0.7,                    -- turned toward the cat, like the old SetFacing(-0.7)
  CAM_DIST = 50, FOV = 0.2,      -- far camera, narrow view: level feet, little perspective
  TYPICAL_H = 2.46,              -- median trash height in yards (reference for the size nudge)
  CHECK = 0.6,                   -- seconds until the model-file check (only if the client can't say whether a model loaded)
  SETTLE = 0.5,                  -- seconds to wait for bounds after the model loads
  GIVEUP = 6,                    -- seconds to wait for a model to load before trying the zone's next model
  TRUST_LO = 0.7, TRUST_HI = 1.4, -- a measured box this far off the size table (after the display-scale check) isn't used
  -- The size table includes each creature's display scale (CreatureDisplayInfo.CreatureModelScale),
  -- and the game draws a creature with it. If the game's measured box leaves that scale out (the
  -- debug print shows "no display scale"), the box is multiplied by it. Set this to false only if
  -- the game turns out to draw creatures without their display scale.
  DRAWN_WITH_DISPLAY_SCALE = true,
}
-- known offenders, used when neither the measured bounds nor ModelBoundsData.lua are available:
-- { height, length, width, bottom, display scale } in yards; cam tunes the old PlayerModel fallback
local MODEL_OVERRIDE = {
  [548] = { 4.40, 2.34, 3.82, -0.01, 1.30, cam = 2.6 }, -- Foe Reaper 4000: tall harvest golem
  [383] = { 2.02, 1.74, 1.68, 0.00, 1.15, cam = 2.1 },  -- Sergeant Brashclaw (gnoll)
  [384] = { 2.02, 1.74, 1.68, 0.00, 1.15, cam = 2.1 },  -- Hogger (the same gnoll model)
  [540] = { 1.71, 1.35, 1.32, -0.04, 1.30, cam = 2.1 }, -- Slark (murloc)
}
local DEFAULT_BOX = { x1 = -0.75, x2 = 0.75, y1 = -0.6, y2 = 0.6, z1 = 0, z2 = FIT.TYPICAL_H }
local FIT_CACHE = {} -- layout key -> finished fit, so reopening the page doesn't re-measure
local BAD_MODEL = {} -- display IDs this client has no model for (skipped from then on)

local function call(o, method, ...)
  local fn = o and o[method]
  if type(fn) ~= "function" then return false end
  return pcall(fn, o, ...)
end

local function boundsRow(id)
  return (TCF.MODEL_BOUNDS and TCF.MODEL_BOUNDS[id]) or MODEL_OVERRIDE[id]
end

local function displayScale(id)
  local d = boundsRow(id)
  local ds = d and tonumber(d[5])
  return ds and ds > 0 and ds or 1
end

local function tableBox(id)
  local d = boundsRow(id)
  if d and d[1] and d[1] > 0 then
    return { x1 = -d[2] / 2, x2 = d[2] / 2, y1 = -d[3] / 2, y2 = d[3] / 2, z1 = d[4], z2 = d[4] + d[1] },
      (TCF.MODEL_BOUNDS and TCF.MODEL_BOUNDS[id]) and "table" or "override"
  end
end

local function scaleBox(b, m)
  if m == 1 then return b end
  return { x1 = b.x1 * m, x2 = b.x2 * m, y1 = b.y1 * m, y2 = b.y2 * m, z1 = b.z1 * m, z2 = b.z2 * m }
end

-- the actor's bounding box at scale 1; both return shapes (6 numbers, or two vectors) are handled
local function measuredBox(a)
  for _, getter in ipairs({ "GetActiveBoundingBox", "GetMaxBoundingBox" }) do
    local r = { call(a, getter) }
    if r[1] then
      local p = { r[2], r[3], r[4], r[5], r[6], r[7] }
      if type(r[2]) == "table" and type(r[3]) == "table" then
        local lo, hi = r[2], r[3]
        if lo.GetXYZ and hi.GetXYZ then
          local ok1, ax, ay, az = pcall(lo.GetXYZ, lo)
          local ok2, bx, by, bz = pcall(hi.GetXYZ, hi)
          if ok1 and ok2 then p = { ax, ay, az, bx, by, bz } end
        else
          p = { lo.x, lo.y, lo.z, hi.x, hi.y, hi.z }
        end
      end
      local good = true
      for i = 1, 6 do if type(p[i]) ~= "number" or p[i] ~= p[i] or math.abs(p[i]) > 1e4 then good = false end end
      if good and p[6] - p[3] > 0.05 and p[4] >= p[1] and p[5] >= p[2] then
        return { x1 = p[1], y1 = p[2], z1 = p[3], x2 = p[4], y2 = p[5], z2 = p[6] }
      end
    end
  end
end

-- The box to fit: how big the model is drawn at actor scale 1. mb is the game's measured box (or nil).
-- Returns the box, where it came from, and the measured/table height ratio (for the debug print).
local function chooseBox(id, mb)
  local tb, tsrc = tableBox(id)
  if not tb then
    if mb then return mb, "measured (no table entry)" end
    return DEFAULT_BOX, "default"
  end
  local ds = displayScale(id)
  local drawn = FIT.DRAWN_WITH_DISPLAY_SCALE ~= false
  -- what a box without the display scale is multiplied by to match what is drawn
  local rawMul = drawn and ds or 1
  if mb then
    local r = (mb.z2 - mb.z1) / (tb.z2 - tb.z1)
    -- nearer the table divided by the display scale than the table itself: measured without it
    local raw = ds ~= 1 and math.abs(math.log(r * ds)) < math.abs(math.log(r))
    local rr = raw and r * ds or r
    if rr >= FIT.TRUST_LO and rr <= FIT.TRUST_HI then
      if raw then return scaleBox(mb, rawMul), "measured, no display scale", r end
      return mb, "measured", r
    end
    -- far off the creature's data (spell effects, odd bounds): use the data
    if not raw then return tb, tsrc .. " (measured box off)", r end
    return scaleBox(tb, rawMul / ds), tsrc .. " (measured box off, no display scale)", r
  end
  -- nothing measured: the table (without the display scale if the game draws without it)
  return scaleBox(tb, drawn and 1 or 1 / ds), tsrc
end

local function project(sc, x, y, z)
  local ok, u, v = call(sc, "Project3DPointTo2D", x, y, z)
  if ok and type(u) == "number" and type(v) == "number" then return u, v end
end

-- pixels per yard at the camera's focus, where the scene's centre is, and which way is screen-right.
-- Measured by projecting test points a frame after the test camera is set (the projection may use
-- the last drawn frame's camera). Returns nil while that is pending; with final, it doesn't wait and
-- works it out from the field of view instead.
local function calibrate(sc, final)
  local W, H = sc:GetWidth() or 0, sc:GetHeight() or 0
  local es = sc.GetEffectiveScale and sc:GetEffectiveScale() or 1
  local key = string.format("%.1f:%.1f:%.4f", W, H, es or 1)
  if sc.cal and sc.cal.key == key and (sc.cal.how == "projected" or final) then return sc.cal end
  local D = FIT.CAM_DIST
  local u0, v0, v1, u1, _
  if sc.calArmed == key then
    u0, v0 = project(sc, 0, 0, 0)
    _, v1 = project(sc, 0, 0, 1)
    u1 = project(sc, 0, 1, 0)
  end
  local cal
  if u0 and v0 and v1 and u1 then
    -- Blizzard's code divides by the effective scale (physical pixels); accept plain UI units too.
    -- The test point (0,0,0) is on the camera's axis, so it must land on the scene's centre
    -- (if the projection still uses the last drawn frame's camera it won't, and we try again).
    local bestErr = 0.05
    for _, div in ipairs({ es, 1 }) do
      if type(div) == "number" and div > 0 then
        local cu, cv, k, ku = u0 / div, v0 / div, (v1 - v0) / div, (u1 - u0) / div
        local flip = k < 0
        if flip then cv, k = H - cv, -k end -- y measured from the top
        local err = max(math.abs(cu / W - 0.5), math.abs(cv / H - 0.5))
        if k > 0.5 and err < bestErr and math.abs(math.abs(ku) - k) <= k * 0.25 then
          bestErr = err
          cal = { k = k, u0 = cu, v0 = cv, side = ku < 0 and -1 or 1, div = div, flip = flip, how = "projected" }
        end
      end
    end
  end
  if not cal and not final then
    call(sc, "SetCameraPosition", -D, 0, 0)
    call(sc, "SetCameraOrientationByYawPitchRoll", 0, 0, 0)
    sc.calArmed = key
    return nil
  end
  if not cal then
    -- camera looks along +X with Z up, so screen-right is -Y. Whether the field of view spans the
    -- height or the width isn't known: assume the one that gives more pixels per yard, so models
    -- come out a little small rather than too big.
    cal = { k = max(W, H) / (2 * D * math.tan(FIT.FOV / 2)), u0 = W / 2, v0 = H / 2, side = -1, how = "estimated" }
  end
  cal.key, cal.W, cal.H = key, W, H
  -- light from the camera, a little from above and from the cat's side
  call(sc, "SetLightDirection", 0.75, 0.35 * cal.side, -0.55)
  sc.cal = cal
  return cal
end

local function newScene(f)
  if type(TapCatForeverDB) == "table" and rawget(TapCatForeverDB, "classicEnemyModels") then return nil, nil, "classicEnemyModels is on" end
  local ok, sc = pcall(CreateFrame, "ModelScene", nil, f)
  if not ok or type(sc) ~= "table" then return nil, nil, "no ModelScene" end
  for _, n in ipairs({ "CreateActor", "SetCameraPosition", "SetCameraOrientationByYawPitchRoll" }) do
    if type(sc[n]) ~= "function" then sc:Hide(); return nil, nil, "ModelScene has no " .. n end
  end
  local okA, a = pcall(sc.CreateActor, sc)
  if not okA or type(a) ~= "table" then sc:Hide(); return nil, nil, "CreateActor failed" end
  for _, n in ipairs({ "SetModelByCreatureDisplayID", "SetScale", "SetYaw", "SetAnimation" }) do
    if type(a[n]) ~= "function" then sc:Hide(); return nil, nil, "actor has no " .. n end
  end
  call(sc, "SetCameraFieldOfView", FIT.FOV)
  call(sc, "SetCameraNearClip", 1)
  call(sc, "SetCameraFarClip", 400)
  call(sc, "SetLightVisible", true)
  call(sc, "SetLightType", Enum and Enum.ModelLightType and Enum.ModelLightType.Directional or 0)
  call(sc, "SetLightAmbientColor", 0.7, 0.7, 0.7)
  call(sc, "SetLightDiffuseColor", 0.8, 0.8, 0.8)
  call(sc, "SetLightDirection", 0.75, -0.35, -0.55)
  -- the model's transparency is driven only through the actor (see modelAlpha), so the death fade
  -- isn't applied twice and "hidden until placed" works whatever the scene does with frame alpha
  sc.ownAlpha = (call(sc, "SetIgnoreParentAlpha", true))
  return sc, a
end

-- how see-through the fitted model should be: the death fade, times the window's own transparency
-- when the scene ignores its parents' alpha
local function modelAlpha(f)
  local a = f.gone and 0 or ((f.fade or 0) > 0 and min(1, f.fade * 1.5) or 1)
  if f.scene and f.scene.ownAlpha then
    local ok, pa = call(f:GetParent(), "GetEffectiveAlpha")
    if ok and type(pa) == "number" then a = a * pa end
  end
  return a
end

-- what a fit depends on: the model, the scene's size and UI scale, and the room around the slot
local function layoutKey(f, id)
  local sc = f.scene
  local es = sc.GetEffectiveScale and sc:GetEffectiveScale() or 1
  return string.format("%d:%.1f:%.1f:%d:%s:%.1f:%.1f:%.4f", id, sc:GetWidth() or 0, sc:GetHeight() or 0, f.slotH or 0,
    tostring(f.isBoss and true or false), f.roomLeft or 0, f.roomRight or 0, es or 1)
end

-- width: stay inside the scene frame, left of the panel's right edge and right of the cat;
-- a model too wide for its side slides the other way (over its neighbours is fine) or shrinks
local function widthFit(f, G, s)
  local S = G.W / 2 - FIT.EDGE
  local Rr, Ll = max(10, min(S, f.roomRight or S)), max(10, min(S, f.roomLeft or S))
  local halfW = (G.ymax - G.ymin) / 2 * s * G.k * G.persp
  local maxHalf = (Rr + Ll) / 2
  if halfW > maxHalf then s = s * maxHalf / halfW; halfW = maxHalf end
  G.Ll, G.Rr = Ll, Rr
  return s, max(0, halfW - Ll) - max(0, halfW - Rr)
end

-- the camera for scale s: the model's middle at the slot's centre (+ shift), its lowest point on
-- the ground line (the scene's middle row), at the same height as the camera
local function pose(G, s, shift)
  return { s = s, yaw = G.yaw, shift = shift, fitH = G.h * s * G.k * G.persp,
    camX = (G.xmin + G.xmax) / 2 * s - FIT.CAM_DIST,
    camY = (G.ymin + G.ymax) / 2 * s - shift / (G.side * G.k),
    camZ = G.z1 * s - (G.H / 2 - G.v0) / G.k }
end

local function placeActor(f, p)
  local sc, a = f.scene, f.actor
  call(a, "SetScale", p.s); call(a, "SetYaw", p.yaw); call(a, "SetPosition", 0, 0, 0)
  call(sc, "SetCameraPosition", p.camX, p.camY, p.camZ)
  call(sc, "SetCameraOrientationByYawPitchRoll", 0, 0, 0)
  sc.calArmed = nil -- the test camera has moved
  f.fitH, f.fitDX, f.fitScale = p.fitH, p.shift, p.s
end

-- scale, turn and frame one loaded actor (still hidden). box: how big it is drawn at scale 1.
local function fitActor(f, box, src, ratio)
  local cal = calibrate(f.scene, true)
  local G = { W = cal.W, H = cal.H, k = cal.k, side = cal.side, v0 = cal.v0, cal = cal, how = cal.how,
    z1 = box.z1, z2 = box.z2, h = box.z2 - box.z1, src = src, ratio = ratio, ds = displayScale(f.fitId) }
  G.yaw = math.pi + FIT.TURN * G.side -- face the camera, turned toward the cat (screen-left)
  local c, s_ = math.cos(G.yaw), math.sin(G.yaw)
  G.xmin, G.xmax, G.ymin, G.ymax = math.huge, -math.huge, math.huge, -math.huge
  for _, x in ipairs({ box.x1, box.x2 }) do
    for _, y in ipairs({ box.y1, box.y2 }) do
      local rx, ry = x * c - y * s_, x * s_ + y * c
      G.xmin, G.xmax, G.ymin, G.ymax = min(G.xmin, rx), max(G.xmax, rx), min(G.ymin, ry), max(G.ymax, ry)
    end
  end
  -- a small size nudge from the creature's real height: wolves a bit shorter than ogres
  local ref = boundsRow(f.fitId)
  local nudge = ref and ref[1] and ref[1] > 0 and max(0.8, min(1.15, (ref[1] / FIT.TYPICAL_H) ^ 0.3)) or 1
  local target = min((f.isBoss and FIT.BOSS_PX or FIT.TRASH_PX) * nudge, f.slotH - FIT.HEADROOM - FIT.GROUND, G.H / 2 - FIT.EDGE)
  local s = target / (G.h * G.k)
  -- the front of a deep model is nearer the camera and looks a little bigger
  G.persp = FIT.CAM_DIST / max(FIT.CAM_DIST * 0.5, FIT.CAM_DIST - (G.xmax - G.xmin) / 2 * s)
  s = s / G.persp
  local shift
  s, shift = widthFit(f, G, s)
  f.fitG, f.fitP = G, pose(G, s, shift)
  placeActor(f, f.fitP)
  return cal.how == "projected"
end

-- one frame after placing (so the projection uses the camera that was drawn): project the box's
-- corners and shrink once if any of it would be cut off or reach the name bar
local function verifyFit(f)
  local G, p, sc = f.fitG, f.fitP, f.scene
  local cal, W, H, s = G.cal, G.W, G.H, p.s
  local top, left, right = -math.huge, math.huge, -math.huge
  for _, x in ipairs({ G.xmin, G.xmax }) do
    for _, y in ipairs({ G.ymin, G.ymax }) do
      local u, v = project(sc, x * s, y * s, G.z2 * s)
      if not u then return end
      u, v = u / cal.div, v / cal.div
      if cal.flip then v = H - v end
      top, left, right = max(top, v), min(left, u), max(right, u)
    end
  end
  -- extents from the aim point; scaling by q scales them by about q, and the slide can change
  local cu = W / 2 + p.shift
  local L0, R0 = max(1, cu - left), max(1, right - cu)
  local topLimit = min(H - FIT.EDGE, H / 2 + f.slotH - FIT.GROUND - FIT.HEADROOM / 2)
  local q = min(1, (topLimit - H / 2) / max(1, top - H / 2), (G.Ll + G.Rr) / (L0 + R0))
  q = max(0.3, q)
  -- the slide nearest the middle that keeps both sides inside (right of the cat, left of the panel's edge)
  local shift = max(q * L0 - G.Ll, min(G.Rr - q * R0, 0))
  if q >= 0.999 and math.abs(shift - p.shift) < 0.5 then return end
  if q < 0.999 then G.shrunk = q end
  f.fitP = pose(G, s * q, shift)
  placeActor(f, f.fitP)
end

-- show the placed model, and remember the fit for next time
local function revealFit(f, info)
  local p = f.fitP
  -- a scale the actor didn't take would leave it the wrong size: use the plain model instead
  local okS, got = call(f.actor, "GetScale")
  if okS and type(got) == "number" and math.abs(got - p.s) > p.s * 0.01 then error("actor scale not applied") end
  if not info then
    local G = f.fitG
    info = string.format("%s, h %.2f yd%s, scale %.3f, %d px tall, %s camera (%.1f px/yd)%s", G.src or "?", G.h,
      G.ratio and string.format(" (measured/table %.2f, display scale %.2f)", G.ratio, G.ds) or "", p.s,
      floor(p.fitH + 0.5), G.how, G.k, G.shrunk and string.format(", shrunk x%.2f after the corner check", G.shrunk) or "")
    -- (a fit from the estimated camera isn't kept if the scene can project: next time may measure)
    if G.how == "projected" or type(f.scene.Project3DPointTo2D) ~= "function" then FIT_CACHE[f.fitKey] = { p = p, info = info } end
  end
  f.fitInfo, f.placed = info, f.fitKey
  call(f.scene, "SetAlpha", 1)
  f.shownAlpha = modelAlpha(f)
  call(f.actor, "SetAlpha", f.shownAlpha)
end

-- the old way: a PlayerModel with a fixed camera distance (made only when a slot needs it)
local function ensureClassic(f, why)
  if f.scene then f.scene:Hide() end
  f.mode, f.fit, f.placed = "classic", nil, nil
  if why then f.classicWhy = why end
  if not f.model then
    local m = CreateFrame("PlayerModel", nil, f)
    m:SetPoint("BOTTOM", f, "BOTTOM", 0, 0)
    f.model = m
  end
  f.model:SetSize((f.slotW or 110) * 2.3, (f.slotH or 140) * 1.35)
end

local function setAnim(f, anim)
  if f.mode == "scene" then call(f.actor, "SetAnimation", anim)
  elseif f.model then call(f.model, "SetAnimation", anim) end
end

-- the same model is already placed for this exact layout (e.g. the page was reopened): keep it
local function sceneReuse(f, id)
  if not (f.placed and f.fitId == id and f.fitP and f.placed == layoutKey(f, id)) then return false end
  local okL, loaded = call(f.actor, "IsLoaded")
  if okL and not loaded then return false end
  call(f.actor, "SetAnimation", ANIM_STAND)
  f.scene:Show(); f.icon:Hide()
  f.fit, f.shownAlpha = nil, nil -- the per-frame alpha sync sets it
  f.fitH, f.fitDX = f.fitP.fitH, f.fitP.shift
  return true
end

-- returns "ok", "bad" (this display ID has no model) or "error" (the 3D scene API failed)
local function sceneLoad(f, id)
  local a = f.actor
  f.placed, f.fitG, f.fitP = nil, nil, nil
  call(a, "ClearModel")
  -- hidden until it has been measured and placed (the actor's alpha; the scene's too, in case)
  call(a, "SetAlpha", 0); call(f.scene, "SetAlpha", 0); f.shownAlpha = 0
  -- measured unturned at scale 1, so the box reads the same whether or not it follows the yaw
  call(a, "SetScale", 1); call(a, "SetPosition", 0, 0, 0); call(a, "SetYaw", 0)
  local ok, res = pcall(a.SetModelByCreatureDisplayID, a, id)
  if not ok then return "error", tostring(res) end
  if res == false then return "bad" end
  call(a, "SetAlpha", 0)
  call(a, "SetAnimation", ANIM_STAND)
  f.scene:Show(); f.icon:Hide()
  f.fit, f.fitId, f.fitDX, f.fitH, f.fitInfo = { t = 0 }, id, 0, nil, nil
  f.fitKey = layoutKey(f, id)
  return "ok"
end

-- runs every frame while a slot's model is loading; returns false if the slot must move on
local function sceneStep(f, e)
  local st, a = f.fit, f.actor
  st.t = st.t + e
  if st.verify then
    verifyFit(f)
    f.fit = nil; revealFit(f)
    return true
  end
  local okL, loaded = call(a, "IsLoaded")
  if okL then loaded = loaded and true or false else loaded = nil end -- nil: the client can't tell us
  if loaded == nil then
    if st.t < FIT.CHECK then return true end
    if not st.checked then
      st.checked = true
      local okF, file = call(a, "GetModelFileID")
      if okF and (not file or file == 0) then BAD_MODEL[f.fitId] = true; return false end
    end
  elseif not loaded then
    -- never loaded: try the zone's next model rather than leave the slot empty
    return st.t < FIT.GIVEUP
  end
  local hit = FIT_CACHE[f.fitKey]
  if hit then
    f.fitP, f.fitG, f.fit = hit.p, nil, nil
    placeActor(f, hit.p)
    revealFit(f, hit.info .. ", reused")
    return true
  end
  st.lt = (st.lt or 0) + e
  local mb = measuredBox(a)
  if not mb and st.lt < FIT.SETTLE then return true end
  -- the scene may need a frame or two before it can project points: wait a moment for it
  if type(f.scene.Project3DPointTo2D) == "function" and (st.ct or 0) < 0.3 and not calibrate(f.scene) then
    st.ct = (st.ct or 0) + e
    return true
  end
  local box, src, ratio = chooseBox(f.fitId, mb)
  if fitActor(f, box, src, ratio) then st.verify = true else f.fit = nil; revealFit(f) end
  return true
end

local function classicLoad(f, id)
  local m = f.model
  -- clear first so the model-file check can't see the previous enemy's model
  call(m, "ClearModel")
  local ok = pcall(m.SetDisplayInfo, m, id)
  local o = MODEL_OVERRIDE[id]
  call(m, "SetFacing", -0.7)
  -- pulled back to match the bigger box (a touch smaller than before, with headroom)
  call(m, "SetCamDistanceScale", o and o.cam or (f.isBoss and 1.85 or 1.65))
  call(m, "SetPosition", 0, 0, 0)
  call(m, "SetAnimation", ANIM_STAND)
  m:Show(); f.icon:Hide()
  f.modelCheck = 0.6
  f.fitDX, f.fitH = 0, nil
  return ok
end

local debugSlots
-- /run TapCatForever:AdvModelDebug()  prints how each enemy model was fitted
function TCF:AdvModelDebug()
  for i, f in ipairs(debugSlots or {}) do
    if f:IsShown() and f.mob then
      local how
      if f.mode == "scene" then how = f.fitInfo or (f.fit and "loading") or "-"
      else how = "fixed camera (" .. tostring(f.classicWhy or "?") .. ")" end
      local id = f.mode == "scene" and f.fitId or (f.cands and f.cands[f.candIdx])
      print(string.format("TapCat enemy %d: %s (display %s) %s: %s", i, f.mob.name or "?", tostring(id),
        f.mode or "?", how))
    end
  end
end

TCF.UI.Builders.adventure = function(page, win)
  local U = TCF.UI
  local Text, Button, Tip, Panel = U.Text, U.Button, U.Tip, U.Panel

  local zoneText = Text(page, "GameFontNormalLarge", nil, "LEFT"); zoneText:SetPoint("TOPLEFT", 16, -12)
  local zoneSub = Text(page, "GameFontHighlightSmall", nil, "LEFT"); zoneSub:SetPoint("TOPLEFT", 16, -32)
  local prevTier = Button(page, "<", 26, 22, function()
    local adv = TCF:CD().adv
    for t = adv.tier - 1, 1, -1 do if TCF:AdvGoTo(t, 1) then break end end
    win:Refresh()
  end)
  local nextTier = Button(page, ">", 26, 22, function()
    local adv = TCF:CD().adv
    TCF:AdvGoTo(adv.tier + 1, 1); win:Refresh()
  end)
  nextTier:SetPoint("TOPRIGHT", -12, -12); prevTier:SetPoint("RIGHT", nextTier, "LEFT", -4, 0)
  local tierLabel = Text(page, "GameFontDisableSmall", "Zone", "RIGHT"); tierLabel:SetPoint("RIGHT", prevTier, "LEFT", -6, 0)
  Tip(nextTier, function(tt) tt:AddLine("Next zone", 1, 0.82, 0); tt:AddLine("Unlocks when you've beaten every stage of this zone, including its final boss. You can go even if your cat is under-levelled. With Auto-advance on, your cat moves on by itself once it reaches the zone's level.", 1, 1, 1, true) end)

  -- scene
  local scene = Panel(page, 532, 250, 1); scene:SetPoint("TOP", 0, -50)
  scene:SetClipsChildren(true)
  local fallbackSky = scene:CreateTexture(nil, "BACKGROUND", nil, 0); fallbackSky:SetPoint("TOPLEFT", 4, -4); fallbackSky:SetPoint("BOTTOMRIGHT", -4, 4)
  fallbackSky:SetColorTexture(0.16, 0.14, 0.22, 1)
  local art = scene:CreateTexture(nil, "BACKGROUND", nil, 1); art:SetPoint("TOPLEFT", 4, -4); art:SetPoint("BOTTOMRIGHT", -4, 4)
  local shade = scene:CreateTexture(nil, "BACKGROUND", nil, 2); shade:SetPoint("BOTTOMLEFT", 4, 4); shade:SetPoint("BOTTOMRIGHT", -4, 4)
  shade:SetHeight(70); shade:SetColorTexture(0, 0, 0, 0.15)

  local catHolder = CreateFrame("Frame", nil, scene)
  catHolder:SetSize(130, 130); catHolder:SetPoint("BOTTOMLEFT", 30, 10)
  local advCat = TCF.CreateCat(catHolder, 130, { preview = true })
  advCat.frame:SetPoint("CENTER")
  local function Bar(parent, w, r, g, b)
    local bar = CreateFrame("StatusBar", nil, parent)
    bar:SetSize(w, 10); bar:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar"); bar:SetStatusBarColor(r, g, b)
    local bg = bar:CreateTexture(nil, "BACKGROUND"); bg:SetAllPoints(); bg:SetColorTexture(0, 0, 0, 0.7)
    bar.text = Text(bar, "GameFontHighlightSmall"); bar.text:SetPoint("CENTER", 0, 0)
    return bar
  end
  local catBar = Bar(scene, 120, 0.2, 0.85, 0.25); catBar:SetPoint("BOTTOM", catHolder, "TOP", 0, 2)
  local abilityText = Text(scene, "GameFontNormal"); abilityText:SetPoint("BOTTOM", catBar, "TOP", 0, 4)
  local abilityT = 0

  -- up to 3 enemies: a 3D model each, with an icon fallback
  local slots = {}
  for i = 1, 3 do
    local f = CreateFrame("Frame", nil, scene)
    f:SetSize(110, 140); f.slotW, f.slotH = 110, 140
    -- the model draws in a much bigger, invisible box than its slot: WoW cuts a model off at
    -- its frame's edges, so a slot-sized box sliced big creatures with a straight line
    local why
    f.scene, f.actor, why = newScene(f)
    if f.scene then
      f.mode = "scene"
      f.scene:SetPoint("CENTER", f, "BOTTOM", 0, FIT.GROUND); f.scene:SetSize(330, 290)
    else
      ensureClassic(f, why)
    end
    f.icon = f:CreateTexture(nil, "ARTWORK"); f.icon:SetSize(96, 96); f.icon:SetPoint("BOTTOM", 0, 10)
    f.icon:SetTexture(PIXEL_MONSTER, nil, nil, "NEAREST")
    -- name and health bar sit on their own layer above the (now taller) model
    local top = CreateFrame("Frame", nil, f); top:SetAllPoints(f)
    if top.SetFrameLevel and f.GetFrameLevel then pcall(top.SetFrameLevel, top, (f:GetFrameLevel() or 1) + 10) end
    f.top = top
    f.bar = Bar(top, 96, 0.85, 0.15, 0.15); f.bar:SetPoint("TOP", 0, 8)
    f.name = Text(top, "GameFontNormalSmall"); f.name:SetPoint("BOTTOM", f.bar, "TOP", 0, 2); f.name:SetWidth(130)
    f.shake, f.fade, f.anim = 0, 0, 0
    f:Hide()
    slots[i] = f
  end
  debugSlots = slots

  -- spell effects and floating numbers play above the models (child frames of the
  -- scene draw over the scene's own font strings, so they need their own raised layer)
  local fxLayer = CreateFrame("Frame", nil, scene); fxLayer:SetAllPoints(scene)
  if fxLayer.SetFrameLevel then fxLayer:SetFrameLevel((scene:GetFrameLevel() or 1) + 20) end

  local floats = {}
  local function FloatText(txt, x, y, r, g, b, big)
    local fs
    for _, f in ipairs(floats) do if not f.active then fs = f; break end end
    if not fs then
      fs = fxLayer:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge"); fs:SetShadowOffset(1, -1)
      floats[#floats + 1] = fs
    end
    fs:SetFontObject(big and "GameFontNormalHuge" or "GameFontNormalLarge")
    fs:SetText(txt); fs:SetTextColor(r, g, b); fs:Show()
    fs.active, fs.age, fs.x, fs.y = true, 0, x + random(-12, 12), y
  end

  local awayText = Text(scene, "GameFontNormalLarge"); awayText:SetPoint("CENTER", 60, 30); awayText:SetWidth(300)
  local startPanel = CreateFrame("Frame", nil, scene); startPanel:SetAllPoints()
  local startDim = startPanel:CreateTexture(nil, "OVERLAY", nil, -1); startDim:SetAllPoints(); startDim:SetColorTexture(0, 0, 0, 0.45)
  local startText = Text(startPanel, "GameFontHighlightLarge"); startText:SetPoint("CENTER", 0, 26); startText:SetWidth(420)
  local startBtn = Button(startPanel, "Start Adventure", 170, 30, function() TCF:AdvStart(); win:Refresh() end)
  startBtn:SetPoint("TOP", startText, "BOTTOM", 0, -12)

  local stats = Text(page, "GameFontHighlight", nil, "LEFT"); stats:SetPoint("TOPLEFT", 18, -342); stats:SetWidth(520)
  local autoCB = CreateFrame("CheckButton", nil, page, "UICheckButtonTemplate")
  autoCB:SetSize(24, 24); autoCB:SetPoint("TOPLEFT", 14, -360)
  local autoText = Text(page, "GameFontHighlightSmall", "Auto-advance"); autoText:SetPoint("LEFT", autoCB, "RIGHT", 0, 1)
  autoCB:SetScript("OnClick", function(s) TCF:CD().adv.auto = s:GetChecked() and true or false end)
  Tip(autoCB, function(tt)
    tt:AddLine("Auto-advance", 1, 0.82, 0)
    tt:AddLine("On: move on after each win and into the next zone when your level allows. Off: keep farming this stage (after 3 losses in a row your cat drops back to an easier pack).", 1, 1, 1, true)
  end)
  local retreat = Button(page, "Retreat", 76, 22, function() TCF:AdvRetreat(); win:Refresh() end)
  retreat:SetPoint("TOPLEFT", 130, -361)
  Tip(retreat, function(tt) tt:AddLine("Retreat", 1, 0.82, 0); tt:AddLine("Stop fighting. Your cat rests until you press Start again.", 1, 1, 1, true) end)
  local nextStage = Button(page, "Stage >", 76, 22, function() TCF:AdvStep(1); win:Refresh() end)
  nextStage:SetPoint("TOPRIGHT", -14, -361)
  local prevStage = Button(page, "< Stage", 76, 22, function() TCF:AdvStep(-1); win:Refresh() end)
  prevStage:SetPoint("RIGHT", nextStage, "LEFT", -6, 0)
  local logText = Text(page, "GameFontHighlightSmall", nil, "LEFT"); logText:SetPoint("TOPLEFT", 18, -390)
  logText:SetWidth(524); logText:SetSpacing(3); logText:SetJustifyV("TOP")
  local help = Text(page, "GameFontDisableSmall", nil, "LEFT"); help:SetPoint("BOTTOMLEFT", 16, 10); help:SetWidth(524)
  help:SetText("Your cat fights with this class's gear, level and learned abilities. Every key you press lands a bonus paw strike. Bosses and zone clears drop chests that can hold the zone's real loot.")

  ------------------------------------------------ ability bar (under the fight) and spell effects
  local SPELL = TCF.SPELL_FX
  local abar, abtns = CreateFrame("Frame", nil, page), {}
  abar:SetSize(532, 32); abar:SetPoint("TOP", scene, "BOTTOM", 0, -2)
  local function abilityButton(i)
    local b = CreateFrame("Frame", nil, abar); b:SetSize(30, 30)
    b.icon = b:CreateTexture(nil, "ARTWORK"); b.icon:SetAllPoints(); b.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
    -- cooldown: a dark cover that shrinks as the ability comes back, plus seconds left
    b.cover = b:CreateTexture(nil, "OVERLAY", nil, 1); b.cover:SetPoint("BOTTOMLEFT"); b.cover:SetPoint("BOTTOMRIGHT"); b.cover:SetColorTexture(0, 0, 0, 0.7)
    b.cd = Text(b, "NumberFontNormal"); b.cd:SetPoint("CENTER", 0, 0)
    b.flash = b:CreateTexture(nil, "OVERLAY", nil, 2); b.flash:SetAllPoints(); b.flash:SetTexture("Interface\\Buttons\\ButtonHilight-Square"); b.flash:SetBlendMode("ADD"); b.flash:SetAlpha(0)
    b:EnableMouse(true)
    b:SetScript("OnEnter", function(s)
      if not s.a then return end
      GameTooltip:SetOwner(s, "ANCHOR_TOP"); GameTooltip:AddLine(s.a.name, 1, 0.82, 0)
      GameTooltip:AddLine(s.a.desc, 1, 1, 1, true)
      if s.a.cd > 0 then GameTooltip:AddLine(string.format("Cooldown: %ds", s.a.cd), 0.7, 0.7, 0.7) end
      GameTooltip:AddLine("Your cat casts it on its own during fights.", 0.6, 0.8, 1, true)
      GameTooltip:Show()
    end)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    abtns[i] = b
    return b
  end
  local function layoutAbilities()
    local class = TCF.db.class
    local list = {}
    for _, a in ipairs(TCF.ABILITIES[class] or {}) do
      if TCF:AbilityKnown(class, a.key) and a.kind ~= "passive" and a.kind ~= "ward" then list[#list + 1] = a end
    end
    for i, b in ipairs(abtns) do b:Hide(); b.a = nil end
    local w = #list * 34 - 4
    for i, a in ipairs(list) do
      local b = abtns[i] or abilityButton(i)
      b.a = a; b.icon:SetTexture(TCF.Icon(a.icon))
      b:ClearAllPoints(); b:SetPoint("LEFT", abar, "CENTER", -w / 2 + (i - 1) * 34, 0)
      b:Show()
    end
    abar.class, abar.count = class, #list
  end
  local function updateAbilities()
    local run = TCF.advRun
    for _, b in ipairs(abtns) do
      if b:IsShown() and b.a then
        local left = run and run.cds and run.cds[b.a.key] and (run.cds[b.a.key] - run.t) or 0
        if left > 0 and b.a.cd > 0 then
          b.cover:SetHeight(max(1, 30 * min(1, left / b.a.cd))); b.cover:Show()
          b.cd:SetText(left >= 10 and floor(left) or string.format("%.1f", left))
          b.icon:SetDesaturated(true)
        else
          b.cover:Hide(); b.cd:SetText(""); b.icon:SetDesaturated(false)
        end
        if (b.flashA or 0) > 0 then b.flashA = max(0, b.flashA - 0.06); b.flash:SetAlpha(b.flashA) end
      end
    end
  end

  -- fight visuals (AdventureFX.lua): shots, ability effects (with the game's own spell visuals on the
  -- enemies), passive abilities. Positions are from the fight panel's bottom-left corner.
  local function slotPos(i)
    local f = i and slots[i]
    -- a just-killed enemy still gets the killing blow; long-faded corpses are skipped
    if f and f:IsShown() and f.mob and (f.mob.alive or not f.gone) then
      -- aim at the fitted model's chest; the old fixed spot for the fallback model
      return 532 + f.baseX - (f.slotW or 110) / 2 + (f.fitDX or 0), f.fitH and (8 + FIT.GROUND + f.fitH * 0.55) or 80
    end
  end
  local FX = TCF.AdvFX.New(fxLayer, scene, {
    slotPos = slotPos,
    slotFrame = function(i) return slots[i] end,
    float = function(txt, x, y, r, g, b, big) FloatText(txt, x, y, r, g, b, big) end,
    shake = function(i, t) local f = slots[i]; if f then f.shake = max(f.shake or 0, t) end end,
    -- a flinch never cuts a stun short
    anim = function(i, id, t)
      local f = slots[i]
      if not (f and f:IsShown() and f.mob and f.mob.alive) then return end
      if f.animId == 14 and (f.anim or 0) > 0 and id ~= 14 then return end
      setAnim(f, id); f.anim, f.animId = t, id
    end,
    target = function()
      local run = TCF.advRun
      local m = run and run.pack and run.pack[run.target]
      if m and m.alive then return run.target end
      for i, x in ipairs(run and run.pack or {}) do if x.alive then return i end end
    end,
  })
  TCF.advFx = FX

  local function layoutSlots(pack)
    local n = pack and #pack or 0
    local boss = n == 1 and pack[1].boss
    for i, f in ipairs(slots) do
      local m = pack and pack[i]
      f:ClearAllPoints()
      -- the slot keeps its own enemy, so a dying enemy can finish its death fade
      -- (and take its killing-blow effect) after the sim has moved on
      f.mob = m
      if m and not m.alive then
        -- died while the window was closed: don't stand it back up
        f.fade, f.modelCheck, f.fit, f.gone = 0, nil, nil, true
        f:SetAlpha(0); f:Hide()
      elseif m then
        local w, h = boss and 170 or 110, boss and 200 or 140
        f:SetSize(w, h); f.slotW, f.slotH = w, h
        f.baseX = boss and -50 or (-12 - (n - i) * 112)
        -- room from the slot's centre to the fight panel's right edge (models slide left, never past it)
        f.roomRight = -f.baseX + w / 2 - 4 - FIT.EDGE
        -- and from the slot's centre to the cat (models may overlap each other, not the cat)
        f.roomLeft = 532 + f.baseX - w / 2 - FIT.CAT_EDGE
        -- scene: centred on the ground line, so its top half holds the model (with headroom)
        if f.mode == "scene" then f.scene:SetSize(boss and w * 2.3 or w * 3, (h + 10) * 2) else ensureClassic(f) end
        f:SetPoint("BOTTOMRIGHT", scene, "BOTTOMRIGHT", f.baseX, 8)
        f.name:SetText(m.boss and ("|cffff8000" .. m.name .. "|r") or m.name)
        f.bar:SetWidth(boss and 150 or 96)
        f.fade, f.gone = 0, false
        f:SetAlpha(1)
        f:Show()
        -- candidate models: this enemy's own, then the zone's other enemies (each ID once,
        -- so a broken ID isn't retried)
        local cands, seen = {}, {}
        local function add(id) if id and id > 0 and not seen[id] then seen[id] = true; cands[#cands + 1] = id end end
        add(m.display)
        local t = TCF:AdvTier(TCF:CD().adv.tier)
        for _, x in ipairs(t.mobs) do add(x[2]) end
        for _, x in ipairs(t.bosses) do add(x[2]) end
        f.cands, f.candIdx, f.isBoss = cands, 0, boss
        f.tryNext = function()
          f.candIdx = f.candIdx + 1
          local id = f.cands[f.candIdx]
          f.fit, f.modelCheck = nil, nil
          if id and f.candIdx <= 6 then
            if BAD_MODEL[id] then return f.tryNext() end
            if f.mode == "scene" then
              if sceneReuse(f, id) then return end
              local r, err = sceneLoad(f, id)
              if r == "bad" then BAD_MODEL[id] = true; return f.tryNext() end
              if r == "ok" then return end
              -- the 3D scene API failed: this slot uses the plain model frame from now on
              ensureClassic(f, "3D model load failed: " .. tostring(err))
            end
            if not classicLoad(f, id) then f.tryNext() end
          else
            if f.scene then f.scene:Hide() end
            if f.model then f.model:Hide() end
            f.icon:Show(); f.fitDX, f.fitH = 0, nil
          end
        end
        f.tryNext()
      else
        f:Hide()
      end
    end
  end

  local function refresh()
    layoutAbilities()
    local cd = TCF:CD()
    local adv = cd.adv
    local t = TCF:AdvTier(adv.tier)
    zoneText:SetText(t.name .. (t.raid and "  |cffff8000(Raid)|r" or ""))
    zoneSub:SetText(string.format("Levels %d-%d   Stage %d / %d   %s", t.min, t.max, adv.stage, TCF:AdvStages(adv.tier),
      adv.stage % 2 == 0 and ("|cffff8000Boss: " .. t.bosses[adv.stage / 2][1] .. "|r") or "|cffaaaaaaTrash pack|r"))
    if t.key then
      -- hand-drawn cartoon scene for every zone
      art:SetTexture(TCF.ART_PATH .. "v\\bg_" .. t.key); art:SetTexCoord(0, 1, 0, 1); art:Show()
    elseif type(t.art) == "string" then
      art:SetTexture("Interface\\AddOns\\TapCatForever\\Art\\" .. t.art, nil, nil, "NEAREST")
      art:SetTexCoord(0, 1, 0, 1); art:Show()
    elseif t.art and t.art > 0 then
      art:SetTexture(t.art); art:SetTexCoord(0, 0.78, 0.05, 0.62); art:Show()
    else art:Hide() end
    local run = TCF.advRun
    -- a cat that shoots holds its bow, gun or wand while it fights
    local fighting = adv.active and run and run.pack and not run.away
    advCat:ApplyAppearance(TCF.AdvFX.FightLook(TCF:GetAppearance(), run and run.stats, TCF.db.class, fighting))
    if not fighting and FX.fighting and not (run and run.respawn > 0 and adv.active) then FX:Stand() end
    local st = TCF:CombatStats()
    local known = 0
    for _, a in ipairs(TCF.ABILITIES[TCF.db.class]) do if TCF:AbilityKnown(TCF.db.class, a.key) then known = known + 1 end end
    stats:SetText(string.format("DPS |cffffffff%s|r   Health |cffffffff%s|r   Armor |cffffffff%s|r   Crit |cffffffff%.1f%%|r   Item level |cffffffff%d|r   Abilities |cffffffff%d|r",
      short(st.dps), short(st.hp), short(st.armor), st.crit, st.ilvl, known))
    autoCB:SetChecked(adv.auto)
    local n = TCF:AdvStages(adv.tier)
    prevStage:SetEnabled(adv.stage > 1 or adv.tier > 1)
    nextStage:SetEnabled(TCF:AdvCanGoTo(adv.stage < n and adv.tier or adv.tier + 1, adv.stage < n and adv.stage + 1 or 1))
    nextTier:SetEnabled(TCF:AdvCanGoTo(adv.tier + 1, 1))
    -- say what the next zone needs
    local nt = TCF.TIERS[adv.tier + 1]
    if not nt then
      tierLabel:SetText("|cffaaaaaaLast zone|r")
    elseif TCF:AdvCanGoTo(adv.tier + 1, 1) and TCF:CD().level >= nt.min then
      tierLabel:SetText("|cff20ff20Next: " .. nt.name .. " is open >|r")
    else
      local cleared = adv.best >= TCF.AdvStageCode(adv.tier, TCF:AdvStages(adv.tier))
      local lvl = TCF:CD().level
      if not cleared then
        tierLabel:SetText("|cffaaaaaaNext: " .. nt.name .. " (clear this zone's final boss first)|r")
      else
        tierLabel:SetText(string.format("|cffffd100Next: %s (made for level %d, you're %d) >|r", nt.name, nt.min, lvl))
      end
    end
    prevTier:SetEnabled(adv.tier > 1)
    logText:SetText(table.concat(TCF.advLog or { "|cff888888Your cat sets out on an adventure...|r" }, "\n"))
    local active = adv.active
    startPanel:SetShown(not active and not TCF:IsOnExpedition(TCF.db.class))
    startText:SetText(string.format("Your %s cat is resting.\nPress Start to fight through %s.", TCF.CLASS_BY_KEY[TCF.db.class].name, t.name))
    retreat:SetEnabled(active and true or false)
    local away = TCF:IsOnExpedition(TCF.db.class)
    awayText:SetText(away and ("|cffffd100Your " .. TCF.CLASS_BY_KEY[TCF.db.class].name .. " cat is away on an expedition.|r\nPick another class, or wait for it to return.") or "")
    -- between packs the slots stay up so the last enemy can play its death fade;
    -- the next "spawn" lays them out again. Only clear them once the cat stops.
    if run and not run.pack and (not active or away) then layoutSlots(nil) end
  end

  local refreshT = 0
  page:SetScript("OnShow", function()
    TCF.advWatching = true
    if TCF.advRun then
      TCF.advRun.events = {}; layoutSlots(TCF.advRun.pack)
      -- passives that keep acting (pet, totem) pick up again mid-fight
      if TCF.advRun.pack and TCF:CD().adv.active then FX:Spawn(TCF.advRun.class) end
    end
  end)
  page:SetScript("OnHide", function() TCF.advWatching = false end)
  page:SetScript("OnUpdate", function(_, e)
    local run = TCF.advRun
    if not run then return end
    for _, ev in ipairs(run.events) do
      local kind, amt, idx = ev[1], ev[2], ev[3]
      local f = idx and slots[idx]
      -- over the model's middle (it may have slid left to stay inside the panel)
      local fx = f and f:IsShown() and (532 + f.baseX - (f.slotW or 110) / 2 + (f.fitDX or 0)) or 400
      if kind == "spawn" then
        layoutSlots(run.pack); refresh(); FX:Spawn(run.class)
      elseif kind == "swing" then
        -- a basic attack: a shot flies (the right paw holds the ranged weapon), or a swipe or plain spell
        if FX:Swing(idx, run.stats, run.class) then advCat:Tap("R") end
      elseif kind == "hit" or kind == "crit" or kind == "dot" then
        -- a shot or spell on its way carries the number and the flinch until it lands
        local p = kind ~= "dot" and FX:TakePending(idx)
        if p then
          if kind == "crit" then FX.Carry(p, short(amt), fx, 150, 1, 0.82, 0.1, true, idx)
          else FX.Carry(p, short(amt), fx, 140, 1, 1, 1, false, idx) end
        else
          if kind ~= "dot" then advCat:Tap() end
          if f then f.shake = 0.2 end
          if kind == "crit" then FloatText(short(amt), fx, 150, 1, 0.82, 0.1, true)
          elseif kind == "hit" then FloatText(short(amt), fx, 140, 1, 1, 1)
          elseif amt >= 1 and random() < 0.25 then FloatText(short(amt * 4), fx, 120, 0.9, 0.8, 0.3) end
        end
      elseif kind == "tap" then
        if f then f.shake = max(f.shake, 0.1) end
        FloatText(short(amt), fx, 115, 0.55, 0.85, 1)
      elseif kind == "hurt" then
        FloatText("-" .. short(amt), 95, 150, 1, 0.25, 0.25)
        if f then setAnim(f, ANIM_ATTACK); f.anim, f.animId = 0.7, ANIM_ATTACK end
        FX:Hurt()
      elseif kind == "heal" then
        FloatText("+" .. short(amt), 95, 160, 0.3, 1, 0.3)
      elseif kind == "ability" then
        abilityText:SetText("|T" .. TCF.Icon(ev[3]) .. ":16:16|t " .. amt); abilityT = 1.2
        local info = ev[4]
        if info then
          advCat:Tap()
          FX:Ability(info)
          for _, b in ipairs(abtns) do if b.a and b.a.key == info.key then b.flashA = 1; b.flash:SetAlpha(1) end end
        end
      elseif kind == "mobdie" then
        local d = slots[amt]
        if d then setAnim(d, ANIM_DEATH); d.fade = 1.0; d.anim, d.animId = 0, ANIM_DEATH end
        FX:Gone(amt)
      elseif kind == "kill" then
        refresh()
      elseif kind == "defeat" then
        advCat:SetFaceFor("blink", 2); FX:Stand(); layoutSlots(nil); refresh()
      end
    end
    FX:EndBatch()
    if #run.events > 0 then run.events = {} end
    catBar:SetMinMaxValues(0, run.catMax); catBar:SetValue(max(0, run.catHP))
    catBar.text:SetText(short(max(0, run.catHP)) .. " / " .. short(run.catMax) .. (run.shield > 0 and (" |cff99ccff+" .. short(run.shield) .. "|r") or ""))
    for i, f in ipairs(slots) do
      local m = f.mob
      if f:IsShown() and m then
        f.bar:SetMinMaxValues(0, m.max); f.bar:SetValue(max(0, m.hp))
        f.bar.text:SetText(short(max(0, m.hp)))
        f.shake = max(0, f.shake - e)
        f:ClearAllPoints()
        f:SetPoint("BOTTOMRIGHT", scene, "BOTTOMRIGHT", f.baseX + (f.shake > 0 and random(-4, 4) or 0), 8)
        if f.fade > 0 then
          f.fade = max(0, f.fade - e); f:SetAlpha(min(1, f.fade * 1.5))
          if f.fade == 0 then f.gone = true end -- faded out: AoE effects skip it now
        end
        if f.anim > 0 then f.anim = f.anim - e; if f.anim <= 0 and m.alive then setAnim(f, ANIM_STAND) end end
        if f.fit then
          -- 3D scene: wait for the model, then measure and fit it; a failure falls back to the plain model
          local ok, keep = pcall(sceneStep, f, e)
          if not ok then f.fit = nil; f.candIdx = f.candIdx - 1; ensureClassic(f, "3D fit failed: " .. tostring(keep)); f.tryNext()
          elseif not keep then f.tryNext() end
        end
        if f.mode == "scene" and not f.fit and f.placed then
          -- the model's transparency (death fade, window opacity) goes through the actor only
          local want = modelAlpha(f)
          if want ~= f.shownAlpha then call(f.actor, "SetAlpha", want); f.shownAlpha = want end
        end
        if f.modelCheck and f.model then
          f.modelCheck = f.modelCheck - e
          if f.modelCheck <= 0 then
            f.modelCheck = nil
            local okFile, file = pcall(f.model.GetModelFileID, f.model)
            if okFile and not file then f.tryNext() end
          end
        end
      end
    end
    if abilityT > 0 then abilityT = abilityT - e; abilityText:SetAlpha(min(1, abilityT * 2)) end
    if abar.class ~= TCF.db.class or abar.count == nil then layoutAbilities() end
    updateAbilities(); FX:Update(e)
    for _, fs in ipairs(floats) do
      if fs.active then
        fs.age = fs.age + e
        if fs.age > 1 then fs.active = false; fs:Hide()
        else
          fs:ClearAllPoints(); fs:SetPoint("CENTER", scene, "BOTTOMLEFT", fs.x, fs.y + fs.age * 40)
          fs:SetAlpha(fs.age < 0.6 and 1 or (1 - fs.age) / 0.4)
        end
      end
    end
    refreshT = refreshT + e
    if refreshT > 1 then refreshT = 0; refresh() end
  end)

  return function() refresh() end
end
