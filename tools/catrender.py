"""Draws the cartoon cat exactly as the addon does, outside the game, for previews.

Loads the addon in the Lua mock of tools/test_harness.py, swaps CreateFrame for a recorder that
keeps every texture's file, place, size, colour, alpha, blend mode, rotation, draw layer and masks,
lets the real Cat / CatVector / CatAnim code dress and animate the cat, and paints the recorded
textures with PIL/numpy in WoW's draw order (frame level, layer, sublevel).

  r = CatRender(extra_art=[dir], extra_lua=[file])   # extra textures and data first (set previews)
  cat = r.cat(size=320)
  r.apply(cat, look)              # look: {slot: item id or a Lua table}, as TCF:GetAppearance returns
  im = r.frame(cat, dt=1/12)      # advances the animation and returns a PIL image
"""
import math, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

RECORDER = r'''
_rec = { tex = {}, now = 1000 }
function GetTime() return _rec.now end
local function noop() end
local Tex, Frame = {}, {}
local TexMT = { __index = function(t, k) return Tex[k] or (type(k) == "string" and k:match("^%u") and noop or nil) end }
local FrameMT = { __index = function(t, k) return Frame[k] or (type(k) == "string" and k:match("^%u") and noop or nil) end }
function Tex:SetTexture(p, wh, wv) if p == nil or type(p) == "string" then self.path = p end; self.color = nil; self.wrap = wh end
function Tex:SetColorTexture(r, g, b, a) self.path = nil; self.color = { r, g, b, a or 1 } end
function Tex:SetTexCoord(...) self.tc = { ... } end
function Tex:ClearAllPoints() self.pt = nil; self.all = nil end
function Tex:SetPoint(p, rel, rp, x, y)
  if type(rel) ~= "table" then rel, rp, x, y = nil, p, rel, rp end
  self.pt = { p, rel or self.parent, rp or p, x or 0, y or 0 }
end
function Tex:SetAllPoints(f) self.all = f or self.parent end
function Tex:SetSize(w, h) self.w, self.h = w, h end
function Tex:SetWidth(w) self.w = w end
function Tex:SetHeight(h) self.h = h end
function Tex:GetWidth() return self.w or 0 end
function Tex:GetHeight() return self.h or 0 end
function Tex:SetVertexColor(r, g, b, a) self.vc = { r, g, b }; if a then self.va = a end end
function Tex:SetAlpha(a) self.alpha = a end
function Tex:GetAlpha() return self.alpha or 1 end
function Tex:Show() self.shown = true end
function Tex:Hide() self.shown = false end
function Tex:SetShown(v) self.shown = v and true or false end
function Tex:IsShown() return self.shown end
function Tex:SetBlendMode(m) self.blend = m end
function Tex:SetDrawLayer(l, s) self.layer, self.sub = l, s or 0 end
function Tex:SetRotation(r) self.rot = r end
function Tex:SetDesaturated(d) self.desat = d end
function Tex:AddMaskTexture(m) self.masks = self.masks or {}; table.insert(self.masks, m) end
function Tex:RemoveMaskTexture(m)
  for i, x in ipairs(self.masks or {}) do if x == m then table.remove(self.masks, i); break end end
end
local function newTex(f, layer, sub, mask)
  local t = setmetatable({ parent = f, layer = layer or "ARTWORK", sub = sub or 0, shown = true, vc = { 1, 1, 1 }, alpha = 1,
    isMask = mask, idx = #_rec.tex + 1 }, TexMT)
  table.insert(_rec.tex, t)
  return t
end
function Frame:CreateTexture(name, layer, tmpl, sub) return newTex(self, layer, sub) end
function Frame:CreateMaskTexture(name, layer, tmpl, sub) return newTex(self, layer, sub, true) end
function Frame:CreateFontString() return setmetatable({}, { __index = function() return noop end }) end
function Frame:SetFrameLevel(l) self.level = l end
function Frame:GetFrameLevel() return self.level end
function Frame:Show() self.shown = true end
function Frame:Hide() self.shown = false end
function Frame:SetShown(v) self.shown = v and true or false end
function Frame:IsShown() return self.shown end
function Frame:IsVisible() return self.shown end
function Frame:SetScript(k, f) self.scripts[k] = f end
function Frame:GetScript(k) return self.scripts[k] end
function Frame:SetSize(w, h) self.w, self.h = w, h end
function Frame:GetWidth() return self.w or 0 end
function Frame:GetHeight() return self.h or 0 end
function Frame:SetAllPoints(f) self.all = f end
function Frame:SetPoint(...) self.pt = { ... } end
function Frame:SetAlpha(a) self.alpha = a end
function CreateFrame(kind, name, parent)
  local f = setmetatable({ kind = kind, parent = parent, level = (parent and parent.level or 0) + 1, shown = true, scripts = {} }, FrameMT)
  return f
end
_rec.root = CreateFrame("Frame")
-- the textures of one cat (every texture whose frame sits under root)
function _rec.texOf(root)
  local out = {}
  for _, t in ipairs(_rec.tex) do
    local f = t.parent
    while f and f ~= root do f = f.parent end
    if f then out[#out + 1] = t end
  end
  return out
end
function _rec.cat(size, opts) return TapCatForever.CreateCat(_rec.root, size, opts or { preview = true }) end
'''

LAYER = {"BACKGROUND": 0, "BORDER": 1, "ARTWORK": 2, "OVERLAY": 3, "HIGHLIGHT": 4}
PREFIX = "Interface\\AddOns\\TapCatForever\\Art\\"


class CatRender:
    def __init__(self, extra_art=(), extra_lua=(), login=True):
        import test_harness as H
        self.lua = H.load_addon(login=login)
        for path in extra_lua:
            src = open(path, encoding="utf-8").read()
            chunk = self.lua.execute("return function(src, name) return assert(loadstring(src, name)) end")(src, "@" + os.path.basename(path))
            chunk("TapCatForever", self.lua.eval("TapCatForever"))
        self.lua.execute(RECORDER)
        self.art_dirs = list(extra_art) + [os.path.join(ROOT, "Art")]
        self.cache = {}
        self.TCF = self.lua.eval("TapCatForever")

    # ---------------------------------------------------------------- cat and looks
    def cat(self, size=320, opts=None):
        return self.lua.eval("_rec.cat")(size, self.lua.table_from(opts or {"preview": True}))

    def item(self, x):
        if x is None or not isinstance(x, str): return x
        it = self.TCF.ITEMS[x]
        assert it is not None, "no item " + x
        return it

    def gear_look(self, art, c1, c2, slot, name="gear", icon=None):
        """a look item for real gear drawn with a cosmetic fallback art (tinted)"""
        return self.lua.table_from({"id": "gear:0", "art": art, "c1": self.lua.table_from(c1), "c2": self.lua.table_from(c2),
                                    "rarity": 3, "slot": slot, "name": name, "icon": icon, "gear": True})

    def apply(self, cat, look):
        t = {}
        for k, v in look.items():
            t[k] = self.item(v) if isinstance(v, str) else v
        if "fur" not in t and "skin" not in t: t["fur"] = self.TCF.ITEMS["fur_ginger"]
        cat.ApplyAppearance(cat, self.lua.table_from(t))

    def paws(self, cat, left_down=True, right_down=True):
        cat.SetPaw(cat, "L", left_down); cat.SetPaw(cat, "R", right_down)

    def step(self, cat, dt):
        rec = self.lua.eval("_rec")
        rec.now = rec.now + dt
        cat.OnUpdate(cat, dt)

    # ---------------------------------------------------------------- painting
    def load(self, path):
        if path in self.cache: return self.cache[path]
        rel = path[len(PREFIX):] if path.startswith(PREFIX) else path
        rel = rel.replace("\\", "/")
        im = None
        for d in self.art_dirs:
            f = os.path.join(d, rel + ".tga")
            if os.path.exists(f): im = Image.open(f).convert("RGBA"); break
        if im is None: raise FileNotFoundError(path)
        arr = np.asarray(im).astype(np.float32) / 255.0
        self.cache[path] = arr
        return arr

    def frame_of(self, t):
        return t.parent

    def visible(self, t):
        if not t.shown: return False
        f = t.parent
        while f is not None:
            if f.shown is False: return False
            f = f.parent
        return True

    def rect(self, t, size):
        """screen rect (x0, y0, w, h), y down, of a texture in a cat frame at (0,0) of the given size"""
        if t.all is not None:
            return 0.0, 0.0, float(size), float(size)
        pt = t.pt
        if pt is None or t.w is None: return None
        p, rel, rp, x, y = pt[1], pt[2], pt[3], pt[4], pt[5]
        w, h = float(t.w), float(t.h)
        # every frame of the cat covers the cat's own square
        ax = {"TOPLEFT": 0, "TOP": .5, "TOPRIGHT": 1, "LEFT": 0, "CENTER": .5, "RIGHT": 1, "BOTTOMLEFT": 0, "BOTTOM": .5, "BOTTOMRIGHT": 1}
        ay = {"TOPLEFT": 0, "TOP": 0, "TOPRIGHT": 0, "LEFT": .5, "CENTER": .5, "RIGHT": .5, "BOTTOMLEFT": 1, "BOTTOM": 1, "BOTTOMRIGHT": 1}
        rx, ry = ax[rp] * size + x, ay[rp] * size - y
        return rx - ax[p] * w, ry - ay[p] * h, w, h

    def sample(self, arr, tc, wrap, w, h):
        """the part of a texture between its tex coords, resized to w x h (wraps when REPEAT)"""
        H, W = arr.shape[:2]
        if tc is None: l, r, tp, b = 0.0, 1.0, 0.0, 1.0
        else:
            v = [tc[i] for i in range(1, len(tc) + 1)]
            l, r, tp, b = v[0], v[1], v[2], v[3]
        w, h = max(1, int(round(w))), max(1, int(round(h)))
        xs = l + (np.arange(w) + 0.5) / w * (r - l)
        ys = tp + (np.arange(h) + 0.5) / h * (b - tp)
        if wrap == "REPEAT":
            xs = np.mod(xs, 1.0); ys = np.mod(ys, 1.0)
        else:
            xs = np.clip(xs, 0, 1); ys = np.clip(ys, 0, 1)
        # bilinear sampling
        fx = xs * W - 0.5; fy = ys * H - 0.5
        x0 = np.floor(fx).astype(int); y0 = np.floor(fy).astype(int)
        ax = (fx - x0)[None, :, None]; ay = (fy - y0)[:, None, None]
        if wrap == "REPEAT":
            x0m, x1m = np.mod(x0, W), np.mod(x0 + 1, W); y0m, y1m = np.mod(y0, H), np.mod(y0 + 1, H)
        else:
            x0m, x1m = np.clip(x0, 0, W - 1), np.clip(x0 + 1, 0, W - 1); y0m, y1m = np.clip(y0, 0, H - 1), np.clip(y0 + 1, 0, H - 1)
        # premultiplied, so transparent texels don't bleed colour
        pre = arr.copy(); pre[..., :3] *= pre[..., 3:4]
        a = pre[y0m][:, x0m]; b_ = pre[y0m][:, x1m]; c = pre[y1m][:, x0m]; d = pre[y1m][:, x1m]
        out = (a * (1 - ax) + b_ * ax) * (1 - ay) + (c * (1 - ax) + d * ax) * ay
        al = out[..., 3:4]
        out[..., :3] = np.where(al > 1e-6, out[..., :3] / np.maximum(al, 1e-6), 0)
        return out

    def paint(self, cat, bg=(0.12, 0.10, 0.18), margin=0.22):
        size = float(cat.size)
        m = int(size * margin)
        S = int(size) + 2 * m
        canvas = np.zeros((S, S, 3), np.float32); canvas[:] = bg
        texs = [t for t in self.lua.eval("_rec.texOf")(cat.frame).values() if not t.isMask and self.visible(t) and (t.path or t.color)]
        def key(t):
            return (t.parent.level or 0, LAYER.get(t.layer, 2), t.sub or 0, t.idx)
        for t in sorted(texs, key=key):
            r = self.rect(t, size)
            if r is None: continue
            x0, y0, w, h = r
            if w < 0.5 or h < 0.5: continue
            alpha = (t.alpha if t.alpha is not None else 1.0) * (t.va if t.va is not None else 1.0)
            if alpha <= 0.003: continue
            if t.color:
                c = [t.color[i] for i in (1, 2, 3, 4)]
                img = np.zeros((max(1, int(round(h))), max(1, int(round(w))), 4), np.float32); img[:] = c
            else:
                img = self.sample(self.load(t.path), t.tc, t.wrap, w, h)
            vc = t.vc
            img[..., :3] *= np.array([vc[1], vc[2], vc[3]], np.float32)
            img[..., 3] *= alpha
            if t.rot:
                pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), "RGBA").rotate(math.degrees(t.rot), resample=Image.BICUBIC)
                img = np.asarray(pil).astype(np.float32) / 255.0
            X0, Y0 = int(round(x0)) + m, int(round(y0)) + m
            hh, ww = img.shape[:2]
            # masks: the mask texture's alpha, laid where the mask sits
            if t.masks:
                for mk in t.masks.values():
                    mr = self.rect(mk, size)
                    if mr is None: continue
                    marr = self.sample(self.load(mk.path), mk.tc, None, mr[2], mr[3])[..., 3]
                    full = np.zeros((S, S), np.float32)
                    MX, MY = int(round(mr[0])) + m, int(round(mr[1])) + m
                    full = self.blit_alpha(full, marr, MX, MY)
                    sub = np.zeros((hh, ww), np.float32)
                    ys0, xs0 = max(0, Y0), max(0, X0)
                    ys1, xs1 = min(S, Y0 + hh), min(S, X0 + ww)
                    if ys1 > ys0 and xs1 > xs0:
                        sub[ys0 - Y0:ys1 - Y0, xs0 - X0:xs1 - X0] = full[ys0:ys1, xs0:xs1]
                    img[..., 3] *= sub
            self.composite(canvas, img, X0, Y0, t.blend == "ADD")
        return Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8), "RGB")

    @staticmethod
    def blit_alpha(full, a, X, Y):
        S = full.shape[0]; h, w = a.shape
        ys0, xs0, ys1, xs1 = max(0, Y), max(0, X), min(S, Y + h), min(S, X + w)
        if ys1 > ys0 and xs1 > xs0: full[ys0:ys1, xs0:xs1] = a[ys0 - Y:ys1 - Y, xs0 - X:xs1 - X]
        return full

    @staticmethod
    def composite(canvas, img, X, Y, add):
        S = canvas.shape[0]; h, w = img.shape[:2]
        ys0, xs0, ys1, xs1 = max(0, Y), max(0, X), min(S, Y + h), min(S, X + w)
        if ys1 <= ys0 or xs1 <= xs0: return
        src = img[ys0 - Y:ys1 - Y, xs0 - X:xs1 - X]
        a = src[..., 3:4]
        dst = canvas[ys0:ys1, xs0:xs1]
        if add: dst += src[..., :3] * a
        else: dst[:] = dst * (1 - a) + src[..., :3] * a

    def frame(self, cat, dt=0.0, **kw):
        if dt: self.step(cat, dt)
        return self.paint(cat, **kw)


def save_gif(frames, path, fps=12):
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=255, dither=Image.FLOYDSTEINBERG) for f in frames]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=int(1000 / fps), loop=0, disposal=2, optimize=False)
