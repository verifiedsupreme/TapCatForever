# 1.6.0 test feedback: Adventure enemies were sometimes cut off by an invisible box. WoW cuts a
# model off at its frame's edges: each enemy's ModelScene was only a little bigger than the model,
# so tall bosses, wide models and attack or death animations reached its edge.
# Now every enemy's scene covers the whole fight panel and more, and the fit leaves room for
# animations. This runs the real fit (UI_Adventure.lua sceneLoad / sceneStep) against a mock
# ModelScene with a level perspective camera, for every Adventure creature display with bounds
# data, in every slot of every pack size, at several window scales (full, compact, small, big),
# and checks the fitted model plus its animation room stays inside its scene, and inside the
# fight panel's visible edge, animation room included (the panel clips).
# Run on its own:  python3 tools/tests/test_adv_fit.py [seed]
import os, sys

def ck(c, m):
    if not c: raise AssertionError("adventure fit: " + m)

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      local L = T.UI.AdvFitLab
      local FIT = L.FIT
      local function noop() end
      local function obj(t) return setmetatable(t, { __index = function(_, k) if type(k) == "string" and k:match("^%u") then return noop end end }) end
      local out = { fits = 0, ids = 0, worst = 0, worstWhy = "", fails = {}, coverFail = nil }
      local function fail(m) if #out.fails < 12 then out.fails[#out.fails + 1] = m end end

      -- every display the Adventure fights show, with its bounds data
      local ids, seen = {}, {}
      for _, t in ipairs(T.TIERS) do
        for _, list in ipairs({ t.mobs or {}, t.bosses or {} }) do
          for _, x in ipairs(list) do
            local id = x[2]
            if id and not seen[id] and T.MODEL_BOUNDS[id] then seen[id] = true; ids[#ids + 1] = id end
          end
        end
      end
      out.ids = #ids

      local function newScene(es)
        local sc = obj({ W = 0, H = 0, es = es, cam = { -FIT.CAM_DIST, 0, 0 } })
        function sc:GetWidth() return self.W end
        function sc:GetHeight() return self.H end
        function sc:SetSize(w, h) self.W, self.H = w, h end
        function sc:GetEffectiveScale() return self.es end
        function sc:SetCameraPosition(x, y, z) self.cam = { x, y, z } end
        -- the camera looks along +X, Z up, screen-right is -Y; the field of view spans the height
        function sc:Project3DPointTo2D(x, y, z)
          local d = x - self.cam[1]
          if d <= 0 then return nil end
          local f = (self.H / 2) / math.tan(FIT.FOV / 2)
          return (self.W / 2 - (y - self.cam[2]) * f / d) * self.es, (self.H / 2 + (z - self.cam[3]) * f / d) * self.es, d
        end
        return sc
      end
      local function newActor()
        local a = obj({ s = 1, yaw = 0 })
        function a:SetModelByCreatureDisplayID(id) self.id = id; return true end
        function a:SetScale(s) self.s = s end
        function a:GetScale() return self.s end
        function a:SetYaw(y) self.yaw = y end
        function a:IsLoaded() return true end
        -- the game's measured box at scale 1 (what is drawn: the bounds data includes the display scale)
        function a:GetActiveBoundingBox()
          local d = T.MODEL_BOUNDS[self.id]
          return -d[2] / 2, -d[3] / 2, d[4], d[2] / 2, d[3] / 2, d[4] + d[1]
        end
        return a
      end
      -- where the drawn model lands in its scene (UI units, from the scene's bottom-left)
      local function drawnRect(sc, a)
        local d = T.MODEL_BOUNDS[a.id]
        local c, s_ = math.cos(a.yaw), math.sin(a.yaw)
        local u1, u2, v1, v2 = math.huge, -math.huge, math.huge, -math.huge
        for _, x in ipairs({ -d[2] / 2, d[2] / 2 }) do
          for _, y in ipairs({ -d[3] / 2, d[3] / 2 }) do
            for _, z in ipairs({ d[4], d[4] + d[1] }) do
              local rx, ry = x * c - y * s_, x * s_ + y * c
              local u, v = sc:Project3DPointTo2D(rx * a.s, ry * a.s, z * a.s)
              u, v = u / sc.es, v / sc.es
              u1, u2, v1, v2 = math.min(u1, u), math.max(u2, u), math.min(v1, v), math.max(v2, v)
            end
          end
        end
        return u1, u2, v1, v2
      end

      local layouts = { { 1, 1, true }, { 1, 1, false }, { 2, 1 }, { 2, 2 }, { 3, 1 }, { 3, 2 }, { 3, 3 } }
      -- full window, compact (pages at 0.69), the smallest and the biggest window sizes
      local scales = { 1, 388 / 560, 0.6 * 388 / 560, 1.4 }
      for _, lay in ipairs(layouts) do
        local n, i, boss = lay[1], lay[2], lay[3] and true or false
        local g = L.slotGeometry(n, i, boss)
        -- the scene covers the whole fight panel and more (also while the slot shakes 4 px)
        local sl, sr = g.cx - g.sceneW / 2, g.cx + g.sceneW / 2
        local sb, st = g.gy - g.sceneH / 2, g.gy + g.sceneH / 2
        if not (sl <= -8 and sr >= L.PANEL_W + 8 and sb <= -8 and st >= L.PANEL_H + 8) then
          out.coverFail = string.format("pack %d slot %d: scene %.0f..%.0f x %.0f..%.0f", n, i, sl, sr, sb, st)
        end
        for _, es in ipairs(scales) do
          for _, id in ipairs(ids) do
            L.clearCache()
            local sc, a = newScene(es), newActor()
            sc:SetSize(g.sceneW, g.sceneH)
            local f = obj({ scene = sc, actor = a, icon = obj({}), slotW = g.w, slotH = g.h, isBoss = boss,
              roomLeft = g.roomLeft, roomRight = g.roomRight, roomTop = g.roomTop, mode = "scene" })
            local res = L.sceneLoad(f, id)
            local steps = 0
            while res == "ok" and not f.placed and steps < 60 do
              local ok, keep = pcall(L.sceneStep, f, 0.05)
              if not ok then fail(id .. ": " .. tostring(keep)); break end
              steps = steps + 1
            end
            if not f.placed then fail(string.format("%d not placed (%s)", id, tostring(res)))
            else
              out.fits = out.fits + 1
              local W, H = sc.W, sc.H
              local u1, u2, v1, v2 = drawnRect(sc, a)
              local uc, halfW, h = (u1 + u2) / 2, (u2 - u1) / 2, v2 - v1
              local side, top = L.animEnvelope(h, halfW)
              local where = string.format("display %d, pack %d slot %d%s, scale %.2f", id, n, i, boss and " (boss)" or "", es)
              -- 1. with its animation room, inside its own scene
              local el, er, eb, et = uc - side, uc + side, v1 - h * 0.1, v1 + top
              if not (el >= 0 and er <= W and eb >= 0 and et <= H) then
                fail(string.format("%s: model and animations %.0f..%.0f x %.0f..%.0f outside its scene %dx%d", where, el, er, eb, et, W, H))
              end
              -- 1b. and inside the fight panel's visible edge (its border is 4 px; the panel clips),
              -- with room for the 4 px shake on the right (1.5 px for the fit's rounding)
              local pl, pr, pt = g.cx + (el - W / 2), g.cx + (er - W / 2), g.gy + (et - H / 2)
              if pl < 4 - 0.5 or pr > L.PANEL_W - 4 - FIT.EDGE + 1.5 or pt > L.PANEL_H - 4 + 0.5 then
                fail(string.format("%s: model and animations %.0f..%.0f, top %.0f, cross the fight panel's edge", where, pl, pr, pt))
              end
              out.maxShift = math.max(out.maxShift or 0, math.abs(f.fitDX or 0))
              -- 2. at rest inside the fight panel (right of the cat, left of the panel's edge), feet on
              -- the ground, and with its room above it under the panel's top
              local px1, px2 = g.cx + (u1 - W / 2), g.cx + (u2 - W / 2)
              local pfeet, ptop = g.gy + (v1 - H / 2), g.gy + (v1 - H / 2) + top
              if px1 < FIT.CAT_EDGE - 1 or px2 > L.PANEL_W - 4 + 1 then
                fail(string.format("%s: at rest %.0f..%.0f across the panel's side", where, px1, px2))
              end
              if ptop > L.PANEL_H + 0.5 then fail(string.format("%s: animation room reaches %.1f, over the panel's top", where, ptop)) end
              if math.abs(pfeet - g.gy) > 1.5 then fail(string.format("%s: feet at %.1f, ground at %.1f", where, pfeet, g.gy)) end
              -- the tightest fit: how close the animation room comes to the scene's edge
              local slack = math.min(pl - 4, L.PANEL_W - 4 - pr, L.PANEL_H - 4 - pt)
              if out.worst == 0 or slack < out.worst then out.worst, out.worstWhy = slack, where end
              -- not shrunk to nothing
              if h < 20 then fail(string.format("%s: only %.0f px tall", where, h)) end
            end
          end
        end
      end
      return out
    ''')
    fails = [r.fails[k] for k in range(1, len(r.fails) + 1)]
    ck(r.coverFail is None, "a scene doesn't cover the fight panel: %s" % r.coverFail)
    ck(r.ids >= 100, "Adventure creature displays with bounds data: %d" % r.ids)
    ck(not fails, "; ".join(fails))
    ck(r.fits == r.ids * 7 * 4, "every display fitted in every layout: %d of %d" % (r.fits, r.ids * 7 * 4))
    print("adventure fit section (%d creature displays x 7 slots x 4 window sizes: every enemy's scene covers the fight panel, the model "
          "and its animation room stay inside its scene and inside the fight panel's edge, at least %.0f px from it (largest slide %.0f px); at rest inside the panel, feet on the ground): all checks passed"
          % (r.ids, r.worst, r.maxShift or 0))

if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(HERE, ".."))
    import test_harness
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
