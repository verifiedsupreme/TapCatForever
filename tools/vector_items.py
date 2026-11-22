"""Vector item drawings in the flat sticker style, driven by a short spec per item icon.

A spec looks like:  "sword:flame guard=wings m=steel t=gold g=red e=ruby glow=fire"
  family:variant   what kind of item and its silhouette
  m / t / g / e    main colour, trim colour, grip/secondary colour, gem/accent colour
  glow=            optional magical glow colour
  bare words       extra features (plume, horns, spikes, gem, fur, emblem, ...)
Colours are palette names (below) or hex like #ff8800.

Every drawing is in the 256x256 cat canvas: head gear in the head's own space (the cat
shrinks it onto the body), weapons in the right paw (mirrored in game for the left paw),
shields and held items in the left paw.
"""
import math, random, re, zlib

INK = "#3b2620"
HEAD_TF = 'transform="translate(128 16) scale(0.8) translate(-128 -28)"'
RIGHT_HAND = 'transform="translate(166 200) rotate(14)"'
LEFT_HAND = (88, 172)

PAL = {
    "steel": "#c9d3e0", "iron": "#8e98a6", "dark": "#4a4e5a", "black": "#2e2e36", "silver": "#e4e9f0", "mithril": "#d6f0ff",
    "gold": "#f2c14e", "bronze": "#c88a42", "copper": "#d77a4a", "brass": "#d9b25a", "thorium": "#8fb3a0", "arcanite": "#9fd0ff",
    "red": "#d8443a", "crimson": "#a92a3a", "maroon": "#6e2230", "orange": "#ef8a35", "yellow": "#f6d64a", "tan": "#d9b98c",
    "brown": "#8a5a36", "leather": "#a2683e", "darkleather": "#6b4428", "wood": "#9a6a3e", "darkwood": "#5e3d24", "cream": "#fff3dc",
    "white": "#f6f6f2", "bone": "#efe6cc", "grey": "#a8a8ae", "green": "#4fae4a", "forest": "#2f7a3a", "lime": "#9be05a",
    "teal": "#2fa59a", "cyan": "#4fd6e8", "sky": "#7cc4f2", "blue": "#3d6fd8", "navy": "#283e86", "purple": "#8a4fd0",
    "violet": "#b47cf0", "pink": "#f08cc0", "magenta": "#d24aa8", "ruby": "#e0283c", "sapphire": "#2f6ff0", "emerald": "#2fc46a",
    "amethyst": "#a05af0", "topaz": "#f5b82e", "pearl": "#f4eefa",
    # glows
    "fire": "#ff8a2a", "frost": "#8fe2ff", "fel": "#8cff3a", "shadow": "#9a4aff", "arcane": "#ff7ae0", "holy": "#fff27a",
    "nature": "#7cf07a", "storm": "#7fd4ff", "blood": "#ff3a3a",
}
def C(v, default):
    if not v: return PAL.get(default, default)
    return v if v.startswith("#") else PAL.get(v, PAL.get(default, default))
def light(hexc, f=0.45):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(int(c + (255 - c) * f) for c in (r, g, b))
def darker(hexc, f=0.7):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(int(c * f) for c in (r, g, b))

def P(d, fill, w=4, extra=""):
    return '<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"%s/>' % (d, fill, INK, w, extra)
def LN(d, col=INK, w=3, op=1):
    return '<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round" opacity="%s"/>' % (d, col, w, op)
def CI(x, y, r, fill, w=4):
    return '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" stroke-width="%s"/>' % (x, y, r, fill, INK, w)
def EL(x, y, rx, ry, fill, w=4, rot=0):
    return '<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="%s" stroke="%s" stroke-width="%s" transform="rotate(%s %.1f %.1f)"/>' % (x, y, rx, ry, fill, INK, w, rot, x, y)
def RC(x, y, w, h, fill, r=3, sw=4):
    return '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % (x, y, w, h, r, fill, INK, sw)
def GEM(x, y, r, col):
    return CI(x, y, r, col, 3) + '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#fff" opacity=".8"/>' % (x - r * 0.35, y - r * 0.35, max(1.2, r * 0.3))
def GLOW(inner, col):
    """Soft magical glow behind a drawing: a blurred, recoloured copy of it."""
    return ('<g filter="url(#blur)" opacity=".85"><g style="fill:%s;stroke:%s;stroke-width:10">%s</g></g>' % (col, col, re.sub(r'(fill|stroke)="[^"]*"', '', inner)))
# "cel": logo-style shading on a whole drawing: a darker band along the lower-right edges, a soft highlight top-left
CEL = ('<filter id="cel" x="-10%" y="-10%" width="120%" height="120%">'
       '<feOffset in="SourceAlpha" dx="-5" dy="-7" result="o1"/><feComposite in="SourceAlpha" in2="o1" operator="out" result="e1"/>'
       '<feFlood flood-color="#1a0c18" flood-opacity=".22"/><feComposite in2="e1" operator="in" result="sh"/>'
       '<feOffset in="SourceAlpha" dx="4" dy="5" result="o2"/><feComposite in="SourceAlpha" in2="o2" operator="out" result="e2"/>'
       '<feGaussianBlur in="e2" stdDeviation="1.5" result="e2b"/><feFlood flood-color="#ffffff" flood-opacity=".38"/><feComposite in2="e2b" operator="in" result="hl"/>'
       '<feComposite in="sh" in2="SourceAlpha" operator="in" result="sh2"/><feComposite in="hl" in2="SourceAlpha" operator="in" result="hl2"/>'
       '<feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="sh2"/><feMergeNode in="hl2"/></feMerge></filter>')
DEFS = '<defs><filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5"/></filter>' + CEL + '</defs>'
def mirror(s, cx=0): return '<g transform="translate(%s,0) scale(-1,1)">%s</g>' % (2 * cx, s)

def parse(spec, default_family=None):
    toks = spec.split()
    if default_family and (":" not in toks[0] and "=" not in toks[0] and toks[0] not in FAMILIES):
        toks[0] = default_family + ":" + toks[0]
    elif default_family and "=" in toks[0]:
        toks.insert(0, default_family + ":")
    fam, _, var = toks[0].partition(":")
    o = {"family": fam, "variant": var, "flags": set()}
    for t in toks[1:]:
        if "=" in t: k, v = t.split("=", 1); o[k] = v
        else: o["flags"].add(t)
    return o

# ======================================================================== weapons (right paw, blade up)
def grip(o, length=30):
    g, t = C(o.get("g"), "leather"), C(o.get("t"), "gold")
    s = RC(-5, -12, 10, length, g, 3)
    for k in range(3): s += LN("M -5 %d L 5 %d" % (-6 + k * 8, -2 + k * 8), darker(g), 2)
    s += CI(0, length - 6, 6.5, t) if "e" not in o else CI(0, length - 6, 7, t) + GEM(0, length - 6, 3.5, C(o["e"], "ruby"))
    return s

def blade_path(v, L, w, seed):
    h = w / 2
    if v == "curved":
        return "M %s -18 C %s %s, %s %s, %s %s C %s %s, %s %s, %s -18 Z" % (-h, -h - 2, -L * .5, -2, -L * .85, -h - 6, -L, h + 10, -L * .8, h + 12, -L * .4, h)
    if v == "katana":
        return "M %s -18 Q %s %s %s %s Q %s %s %s -18 Z" % (-h, -h + 2, -L * .6, -h - 8, -L, h + 4, -L * .55, h)
    if v in ("flame", "jagged", "serrated"):
        rnd = random.Random(seed); n = 7; pts_l, pts_r = [], []
        for k in range(n + 1):
            y = -18 - (L - w) * k / n
            a = math.sin(k * 1.9) * 2.2 if v == "flame" else 0
            jag = (rnd.random() * 6 if v == "jagged" else 0)
            pts_l.append((-h + a - (jag if k % 2 else 0) - (5 if v == "serrated" and k % 2 else 0), y))
            pts_r.append((h + a + (jag if not k % 2 else 0), y))
        d = "M " + " L ".join("%.1f %.1f" % p for p in pts_l) + " L %.1f %.1f " % (pts_l[-1][0] * .3 + 2, -L)
        d += " L " + " L ".join("%.1f %.1f" % p for p in reversed(pts_r)) + " Z"
        return d
    if v == "cleaver":
        return "M %s -18 L %s %s L %s %s L %s %s L %s -18 Z" % (-h, -h, -L + 10, -h + 6, -L, h + 8, -L + 20, h)
    tip = w * (1.2 if v == "broad" else 1.0)
    return "M %s -18 L %s %s L 0 %s L %s %s L %s -18 Z" % (-h, -h, -(L - tip), -L, h, -(L - tip), h)

def guard(o, v, w):
    t = C(o.get("t"), "gold"); e = o.get("e")
    hw = max(22, w + 12)
    if v == "wings":
        wing = P("M -6 -12 Q -30 -14 -40 -44 Q -32 -36 -24 -40 Q -24 -28 -8 -24 Z", t)
        return wing + mirror(wing) + CI(0, -16, 8, t) + (GEM(0, -16, 4, C(e, "sapphire")) if e else "")
    if v == "cross":
        return P("M %s -8 Q %s -20 0 -20 Q %s -20 %s -8 L %s -14 Q 0 -24 %s -14 Z" % (-hw, -hw / 2, hw / 2, hw, hw - 6, -hw + 6), t)
    if v == "round":
        return EL(0, -16, 14, 7, t)
    if v == "ornate":
        s = RC(-hw, -22, hw * 2, 10, t, 5)
        s += P("M %s -22 L %s -32 L %s -20 Z" % (-hw, -hw - 6, -hw + 8), t) + P("M %s -22 L %s -32 L %s -20 Z" % (hw, hw + 6, hw - 8), t)
        return s + CI(0, -17, 7, t) + GEM(0, -17, 4, C(e, "ruby"))
    if v == "spiked":
        s = RC(-hw, -21, hw * 2, 9, t, 4)
        return s + P("M %s -17 L %s -24 L %s -13 Z" % (-hw, -hw - 12, -hw), t) + P("M %s -17 L %s -24 L %s -13 Z" % (hw, hw + 12, hw), t)
    return RC(-hw, -21, hw * 2, 9, t, 4.5) + (GEM(0, -16.5, 3.5, C(e, "ruby")) if e else "")

def draw_sword(o, two=False):
    v = o["variant"] or "straight"
    L = 165 if two else 135
    w = {"broad": 22, "katana": 10, "cleaver": 24, "curved": 15}.get(v, 18 if two else 14)
    m = C(o.get("m"), "steel")
    b = P(blade_path(v, L, w, zlib.crc32(o.get("_key", "").encode()) & 0xffff), m, 4.5)
    if v not in ("curved", "katana", "flame", "jagged"):
        b += LN("M 0 -24 L 0 %d" % -(L - w - 8), light(m, .55) if "rune" not in o["flags"] else C(o.get("e"), "sky"), 3 if "rune" not in o["flags"] else 4)
    s = grip(o) + guard(o, o.get("guard", "bar"), w) + b
    return s, b

def draw_axe(o, two=False):
    v = o["variant"] or "single"; L = 150 if two else 120
    m, t, g = C(o.get("m"), "steel"), C(o.get("t"), "iron"), C(o.get("g"), "wood")
    s = RC(-4.5, -L - 4, 9, L + 30, g, 4)
    big = 1.35 if two else 1.0
    def blade(sgn):
        k = big
        if v == "cleaver":
            return P("M %s %s L %s %s L %s %s L %s %s Z" % (4 * sgn, -L + 4, 40 * k * sgn, -L - 2, 40 * k * sgn, -L + 44 * k, 4 * sgn, -L + 40 * k), m)
        if v == "bearded":
            return P("M %s %s Q %s %s %s %s Q %s %s %s %s Q %s %s %s %s Z" % (4 * sgn, -L + 2, 30 * k * sgn, -L - 4, 42 * k * sgn, -L + 18 * k, 40 * k * sgn, -L + 60 * k, 22 * k * sgn, -L + 66 * k, 14 * sgn, -L + 30 * k, 4 * sgn, -L + 26 * k), m)
        r = 1.3 if v == "crescent" else 1.0
        return P("M %s %s Q %s %s %s %s Q %s %s %s %s Q %s %s %s %s Z" % (
            4 * sgn, -L + 4, 30 * k * r * sgn, -L - 10 * r, 44 * k * r * sgn, -L + 22 * k, 30 * k * r * sgn, -L + 56 * k * r, 4 * sgn, -L + 40 * k,
            22 * k * sgn, -L + 22 * k, 4 * sgn, -L + 4), m)
    if v == "pick":
        b = P("M -4 %s Q 30 %s 46 %s Q 26 %s -4 %s Z" % (-L + 2, -L - 6, -L + 26, -L + 2, -L + 12), m) + P("M 4 %s Q -30 %s -46 %s Q -26 %s 4 %s Z" % (-L + 2, -L - 6, -L + 26, -L + 2, -L + 12), m)
        b += RC(-8, -L - 4, 16, 20, t, 4)
        return s + b, b
    b = blade(1) + (blade(-1) if v == "double" or "double" in o["flags"] else "")
    b += RC(-8, -L - 2, 16, 26 * big, t, 4)
    if "spike" in o["flags"]: b += P("M -5 %d L 0 %d L 5 %d Z" % (-L - 4, -L - 26, -L - 4), C(o.get("t"), "iron"))
    if "e" in o: b += GEM(0, -L + 11 * big, 4.5, C(o["e"], "ruby"))
    s += RC(-6, -14, 12, 28, darker(g, .8), 3)
    return s + b, b

def draw_mace(o, two=False):
    v = o["variant"] or "ball"; L = 140 if two else 105
    m, t, g = C(o.get("m"), "iron"), C(o.get("t"), "bronze"), C(o.get("g"), "wood")
    s = RC(-4.5, -L, 9, L + 28, g, 4) + RC(-6, -14, 12, 28, darker(g, .8), 3)
    r = 24 if two else 17
    y = -L - r + 6
    if v == "club":
        b = P("M -6 %s Q -16 %s 0 %s Q 16 %s 6 %s Z" % (-L + 40, -L - 20, -L - 34, -L - 20, -L + 40), C(o.get("m"), "wood"))
        for k in range(3): b += LN("M -6 %d Q 0 %d 6 %d" % (-L - 14 + k * 14, -L - 10 + k * 14, -L - 14 + k * 14), darker(C(o.get("m"), "wood"), .7), 2)
        if "spikes" in o["flags"]:
            for dx, dy in ((-13, -L - 8), (13, -L - 2), (-12, -L + 14), (12, -L + 20)):
                b += P("M %d %d L %d %d L %d %d Z" % (dx, dy - 4, dx + (8 if dx > 0 else -8), dy, dx, dy + 4), C(o.get("t"), "steel"), 2.5)
        return s + b, b
    if v == "bone":
        bone = C(o.get("m"), "bone")
        b = RC(-6, -L - 10, 12, L, bone, 6) + CI(-8, -L - 12, 9, bone) + CI(8, -L - 12, 9, bone) + RC(-6, -L - 10, 12, 20, bone, 4, 0)
        return s + b, b
    if v == "skullhead":
        bone = C(o.get("m"), "bone")
        b = P("M -18 %d Q -20 %d 0 %d Q 20 %d 18 %d L 11 %d L -11 %d Z" % (-L + 4, -L - 36, -L - 36, -L - 36, -L + 4, -L + 14, -L + 14), bone)
        b += CI(-7, -L - 14, 5, C(o.get("e"), "dark"), 2.5) + CI(7, -L - 14, 5, C(o.get("e"), "dark"), 2.5)
        return s + b, b
    if v == "fish":
        fm = C(o.get("m"), "teal")
        b = P("M 0 %d Q -22 %d 0 %d Q 22 %d 0 %d Z" % (-L + 10, -L - 20, -L - 56, -L - 20, -L + 10), fm) + P("M 0 %d L -12 %d L 12 %d Z" % (-L + 8, -L + 24, -L + 24), fm, 3.5)
        b += CI(-5, -L - 38, 3.5, "#fff", 2) + LN("M -10 %d Q 0 %d 10 %d" % (-L - 26, -L - 20, -L - 26), darker(fm, .7), 2)
        return s + b, b
    if v == "torch":
        b = RC(-9, -L - 6, 18, 14, C(o.get("t"), "iron"), 3)
        fl = P("M -12 %d Q -16 %d -2 %d Q 2 %d 8 %d Q 18 %d 12 %d Z" % (-L - 6, -L - 28, -L - 46, -L - 32, -L - 40, -L - 20, -L - 6), C(o.get("e"), "orange"), 3)
        return s + GLOW(fl, C(o.get("glow"), "fire")) + b + fl, b
    if v == "mug":
        mm = C(o.get("m"), "wood")
        b = RC(-18, -L - 30, 36, 40, mm, 5) + '<path d="M 18 %d q 16 4 0 22" fill="none" stroke="%s" stroke-width="7"/>' % (-L - 22, INK)
        b += EL(0, -L - 30, 18, 6, C(o.get("e"), "cream"), 4)
        for x in (-8, 4): b += LN("M %d %d L %d %d" % (x, -L - 22, x, -L + 4), darker(mm, .7), 2)
        return s + b, b
    if v == "gear":
        gm = C(o.get("m"), "steel"); y = -L - 18; b = ""
        for k in range(8):
            a = k * math.pi / 4
            b += '<rect x="-5" y="%d" width="10" height="12" fill="%s" stroke="%s" stroke-width="3" transform="rotate(%d 0 %d)"/>' % (y - 26, gm, INK, math.degrees(a), y)
        b += CI(0, y, 19, gm) + CI(0, y, 7, C(o.get("t"), "dark"), 3)
        return s + b, b
    if v == "hammer" or v == "maul":
        hw = 34 if v == "maul" or two else 24
        b = RC(-hw, y - r * .8, hw * 2, r * 1.6, m, 5) + RC(-6, y - r * .8, 12, r * 1.6, t, 3)
    elif v == "scepter":
        b = P("M -16 %s L -20 %s L -8 %s L 0 %s L 8 %s L 20 %s L 16 %s Z" % (y + 14, y - 14, y - 4, y - 22, y - 4, y - 14, y + 14), m) + GEM(0, y, 7, C(o.get("e"), "ruby"))
    else:
        b = ""
        if v in ("spiked", "star"):
            n, ln = (8, r * (1.7 if v == "star" else 1.45))
            for k in range(n):
                a = k * 2 * math.pi / n
                b += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (math.cos(a + .25) * r * .8, y + math.sin(a + .25) * r * .8, math.cos(a) * ln, y + math.sin(a) * ln, math.cos(a - .25) * r * .8, y + math.sin(a - .25) * r * .8), C(o.get("t"), "steel"), 3)
        if v == "flanged":
            for k in range(6):
                a = k * math.pi / 3
                b += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (math.cos(a + .4) * r * .6, y + math.sin(a + .4) * r * .6, math.cos(a) * r * 1.35, y + math.sin(a) * r * 1.35, math.cos(a - .4) * r * .6, y + math.sin(a - .4) * r * .6), m, 3.5)
        b += CI(0, y, r, m, 4.5) + EL(0, y + r - 2, r * .55, 5, t, 3)
        b += '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#fff" opacity=".35"/>' % (-r * .35, y - r * .35, r * .3)
        if "e" in o: b += GEM(0, y, r * .35, C(o["e"], "sapphire"))
    if "spike" in o["flags"]: b += P("M -5 %s L 0 %s L 5 %s Z" % (y - r, y - r - 20, y - r), C(o.get("t"), "steel"))
    return s + b, b

def draw_dagger(o, two=False):
    v = o["variant"] or "straight"; L = 78; w = 12
    m = C(o.get("m"), "steel")
    if v == "kris": bp = blade_path("flame", L, w, 3)
    elif v in ("curved", "fang"):
        bp = "M -6 -18 C -8 -45, %s -65, %s %s C 12 -60, 10 -40, 6 -18 Z" % (4 if v == "curved" else 10, 14 if v == "curved" else 16, -L)
        if v == "fang": m = C(o.get("m"), "bone")
    else: bp = blade_path("straight", L, w, 1)
    b = P(bp, m, 4)
    if v == "straight": b += LN("M 0 -24 L 0 -%d" % (L - 18), light(m, .55), 2.5)
    return grip(o, 26) + guard(o, o.get("guard", "bar"), 8) + b, b

def draw_staff(o, two=True):
    v = o["variant"] or "orb"; L = 165
    g, t, e = C(o.get("g"), "wood"), C(o.get("t"), "gold"), C(o.get("e"), "sky")
    s = RC(-4.5, -L, 9, L + 34, g, 4)
    for y in (-L + 8, -60, 18): s += RC(-7, y, 14, 7, t, 2, 3)
    y = -L - 6; b = ""
    if v == "orb":
        claw = P("M -4 %s Q -24 %s -14 %s Q -10 %s -4 %s Z" % (y + 10, y - 4, y - 26, y - 10, y - 2), t, 3.5)
        b = claw + mirror(claw) + GEM(0, y - 12, 13, e)
    elif v == "moon":
        b = P("M -4 %s Q -30 %s -8 %s Q -18 %s -4 %s Z" % (y + 6, y - 20, y - 44, y - 20, y + 6), t) + P("M 4 %s Q 30 %s 8 %s Q 18 %s 4 %s Z" % (y + 6, y - 20, y - 44, y - 20, y + 6), t)
        b += GEM(0, y - 8, 7, e)
    elif v == "pole":
        b = LN("M 0 %s L 28 %s L 28 %s" % (y + 10, y - 2, y + 60), "#f6f6f2", 2) + LN("M 28 %s q 0 8 -6 6" % (y + 60), INK, 2.5) + CI(28, y + 44, 5, C(o.get("e"), "red"), 2.5)
    elif v == "crystal":
        b = P("M 0 %s L -12 %s L 0 %s L 12 %s Z" % (y - 42, y - 16, y + 6, y - 16), e) + LN("M 0 %s L 0 %s" % (y - 38, y + 2), light(e, .6), 2) + RC(-10, y - 2, 20, 8, t, 3, 3)
    elif v == "crook":
        b = LN("M 0 %s Q 0 %s 18 %s Q 30 %s 24 %s Q 18 %s 10 %s" % (y + 8, y - 30, y - 34, y - 30, y - 16, y - 10, y - 16), INK, 13) + LN("M 0 %s Q 0 %s 18 %s Q 30 %s 24 %s Q 18 %s 10 %s" % (y + 8, y - 30, y - 34, y - 30, y - 16, y - 10, y - 16), g, 7)
        if "e" in o: b += GEM(16, y - 22, 6, e)
    elif v == "skull":
        b = P("M -15 %s Q -16 %s 0 %s Q 16 %s 15 %s L 9 %s L -9 %s Z" % (y - 4, y - 32, y - 32, y - 32, y - 4, y + 4, y + 4), C(o.get("m"), "bone"))
        b += CI(-6, y - 14, 4, e, 2) + CI(6, y - 14, 4, e, 2)
    elif v == "branch":
        for a, ln in ((-40, 30), (-10, 36), (30, 28)):
            x2, y2 = math.sin(math.radians(a)) * ln, y - math.cos(math.radians(a)) * ln
            b += LN("M 0 %s L %.1f %.1f" % (y + 8, x2, y2), INK, 9) + LN("M 0 %s L %.1f %.1f" % (y + 8, x2, y2), g, 4.5)
            b += EL(x2, y2, 7, 4, e, 3, a)
    elif v == "ring":
        b = '<circle cx="0" cy="%s" r="18" fill="none" stroke="%s" stroke-width="11"/><circle cx="0" cy="%s" r="18" fill="none" stroke="%s" stroke-width="5"/>' % (y - 16, INK, y - 16, t) + GEM(0, y - 16, 7, e)
    elif v == "blade":
        b = P("M -8 %s L 0 %s L 8 %s L 4 %s L -4 %s Z" % (y + 4, y - 44, y + 4, y + 8, y + 8), C(o.get("m"), "steel")) + RC(-12, y + 2, 24, 8, t, 3, 3)
    else:  # knot: gnarled wooden head
        b = P("M -6 %s Q -22 %s -12 %s Q 0 %s 12 %s Q 22 %s 6 %s Z" % (y + 8, y - 8, y - 28, y - 20, y - 28, y - 8, y + 8), g) + (GEM(0, y - 12, 6, e) if "e" in o else "")
    return s + b, b

def draw_polearm(o, two=True):
    v = o["variant"] or "spear"; L = 160
    m, t, g = C(o.get("m"), "steel"), C(o.get("t"), "iron"), C(o.get("g"), "wood")
    s = RC(-4, -L, 8, L + 34, g, 4) + RC(-6, -14, 12, 26, darker(g, .8), 3)
    y = -L
    if v == "halberd":
        b = P("M -5 %s L 0 %s L 5 %s Z" % (y, y - 40, y), m) + P("M 4 %s Q 34 %s 38 %s Q 34 %s 4 %s Z" % (y + 6, y + 2, y + 22, y + 44, y + 38), m) + P("M -4 %s L -22 %s L -4 %s Z" % (y + 14, y + 22, y + 28), m)
    elif v == "scythe":
        b = P("M -4 %s Q 20 %s 58 %s Q 30 %s 4 %s Z" % (y + 4, y - 22, y + 10, y - 2, y + 18), m)
    elif v == "glaive":
        b = P("M -5 %s Q -10 %s 8 %s Q 16 %s 6 %s Z" % (y + 6, y - 30, y - 56, y - 26, y + 6), m)
    elif v == "trident":
        b = RC(-18, y - 4, 36, 8, t, 3)
        for x in (-15, 0, 15): b += P("M %s %s L %s %s L %s %s Z" % (x - 4, y - 2, x, y - (36 if x == 0 else 26), x + 4, y - 2), m)
    else:
        b = P("M -4 %s Q -14 %s 0 %s Q 14 %s 4 %s Z" % (y + 2, y - 18, y - 46, y - 18, y + 2), m) + LN("M 0 %s L 0 %s" % (y - 4, y - 36), light(m, .55), 2.5)
    b += RC(-7, y - 2, 14, 12, t, 3, 3)
    if "e" in o: b += GEM(0, y + 4, 4, C(o["e"], "ruby"))
    return s + b, b

def draw_fist(o, two=False):
    m, t = C(o.get("m"), "steel"), C(o.get("t"), "leather")
    b = ""
    if o["variant"] == "knuckle":
        for x in (-14, -5, 5, 14): b += P("M %d -8 L %d -22 L %d -8 Z" % (x - 4, x, x + 4), m, 3)
        s = b + RC(-22, -12, 44, 22, t, 6)
        if "e" in o: s += GEM(0, -1, 5, C(o["e"], "ruby"))
        return s, b
    for x, a in ((-12, -12), (0, 0), (12, 12)):
        b += '<g transform="rotate(%d %d -6)">%s</g>' % (a, x, P("M %d -6 L %d -52 L %d -6 Z" % (x - 5, x, x + 5), m, 3.5))
    s = b + RC(-20, -10, 40, 18, t, 5)
    if "e" in o: s += GEM(0, -1, 5, C(o["e"], "ruby"))
    return s, b

def draw_bow(o, two=False):
    m, t = C(o.get("m"), "wood"), C(o.get("t"), "leather")
    if o["variant"] == "crossbow":
        # wooden stock pointing up, a bow limb across its top, the string drawn back to the nut, a bolt on top
        st, e = C(o.get("g"), "#f4f0e0"), C(o.get("e"), "steel")
        b = RC(-7, -112, 14, 122, t, 4) + RC(-10, -4, 20, 30, darker(t, .8), 6)
        b += LN("M -46 -84 Q 0 -128 46 -84", INK, 12) + LN("M -46 -84 Q 0 -128 46 -84", m, 7)
        b += LN("M -45 -86 L 0 -66 L 45 -86", st, 1.8) + RC(-5, -70, 10, 8, darker(t, .7), 2, 2.5)
        if "bolt" in o["flags"]:
            b += LN("M 0 -66 L 0 -136", INK, 6) + LN("M 0 -66 L 0 -136", C("wood", "wood"), 3)
            b += P("M -7 -134 L 0 -152 L 7 -134 Z", e, 3) + P("M -6 -66 L 0 -76 L 6 -66 Z", C("white", "white"), 2.5)
        b += '<path d="M 7 -40 Q 20 -32 7 -20" fill="none" stroke="%s" stroke-width="7" stroke-linecap="round"/>' % INK
        b += '<path d="M 7 -40 Q 20 -32 7 -20" fill="none" stroke="%s" stroke-width="3.5" stroke-linecap="round"/>' % C("iron", "iron")
        return b, b
    v, fl = o["variant"], o["flags"]
    if not v:  # the plain bow (cosmetic wpn_bow, whose build adds g): kept exactly as before
        b = LN("M 4 -150 Q 40 -70 4 10", INK, 11) + LN("M 4 -150 Q 40 -70 4 10", m, 6) + LN("M 4 -150 L 4 10", "#f4f0e0", 1.6)
        b += RC(-2, -78, 12, 22, t, 3, 3)
        return b, b
    # limb as a quadratic curve p0 -> p2 bulging out through p1; the string joins the two tips
    top, bot, bulge = (-174, 6, 34) if v == "long" else (-150, 10, 40)
    p0, p1, p2 = (4, top), (bulge, (top + bot) / 2.0), (4, bot)
    def at(u):
        return tuple((1 - u) ** 2 * p0[k] + 2 * (1 - u) * u * p1[k] + u * u * p2[k] for k in (0, 1))
    limb = "M %d %d Q %d %d %d %d" % (p0 + p1 + p2)
    thick = 9 if v == "horn" else 6
    st = C(o.get("g"), "#f4f0e0")
    b = LN("M %d %d L %d %d" % (p0 + p2), st, 1.8)
    if v == "spiked":  # spikes along the back of the limb
        for u in (0.12, 0.3, 0.7, 0.88):
            x, y = at(u)
            b += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x + 2, y - 7, x + 16, y + (6 if u > .5 else -6), x + 2, y + 7), m, 3)
    b += LN(limb, INK, thick + 5) + LN(limb, m, thick)
    if v == "horn":  # ridges across a thick horn limb
        for u in (0.1, 0.22, 0.34, 0.66, 0.78, 0.9):
            x, y = at(u); b += LN("M %.1f %.1f L %.1f %.1f" % (x - 4, y, x + 4, y), darker(m, .7), 2)
    if v == "recurve":  # tips flick forward
        for (x, y), d in ((p0, -1), (p2, 1)):
            b += LN("M %d %d q 5 %d 11 %d" % (x, y, d * 2, d * 7), INK, 10) + LN("M %d %d q 5 %d 11 %d" % (x, y, d * 2, d * 7), m, 5)
    if v == "wrapped":  # bands of the wrap colour along the limb
        for u in (0.2, 0.32, 0.68, 0.8):
            x, y = at(u); b += LN("M %.1f %.1f L %.1f %.1f" % (x - 4, y - 2, x + 4, y + 2), INK, 7) + LN("M %.1f %.1f L %.1f %.1f" % (x - 4, y - 2, x + 4, y + 2), t, 3.5)
    gx, gy = at(0.5)
    b += RC(gx - 6, gy - 11, 12, 22, t, 3, 3)
    if v == "disc":  # a round plate at the grip with a coloured rim
        b += CI(gx + 4, gy, 12, t, 3) + CI(gx + 4, gy, 7, C(o.get("e"), "ruby"), 2.5) + CI(gx + 4, gy, 3, t, 2)
    if "ribbons" in fl:  # two ribbon tails hanging from the grip
        e = C(o.get("e"), "red")
        b += P("M %.1f %.1f q -8 14 -2 30 l 5 -2 q -4 -14 3 -26 Z" % (gx - 2, gy + 8), e, 2.5)
        b += P("M %.1f %.1f q 4 16 -6 28 l 5 2 q 9 -12 5 -28 Z" % (gx + 2, gy + 8), darker(e, .85), 2.5)
    if "fur" in fl:  # a fur pom hanging from the grip
        e = C(o.get("e"), "white")
        b += LN("M %.1f %.1f L %.1f %.1f" % (gx - 4, gy + 6, gx - 10, gy + 20), INK, 2)
        for dx, dy in ((-12, 24), (-6, 28), (-14, 31), (-8, 34)): b += CI(gx + dx, gy + dy, 5, e, 2.5)
    return b, b

def draw_rifle(o, two=False):
    m, t = C(o.get("m"), "iron"), C(o.get("t"), "wood")
    v, fl = o["variant"], o["flags"]
    b = RC(-6, -150, 12, 120, m, 3) + RC(-9, -40, 18, 60, t, 5) + RC(-12, -10, 24, 34, t, 6)
    if v == "bell":  # blunderbuss: the barrel flares into a wide mouth
        b += P("M -6 -146 L -15 -170 L 15 -170 L 6 -146 Z", m, 3.5) + EL(0, -170, 15, 4.5, darker(m, .45), 3)
        if "e" in o: b += LN("M -14 -165 L 14 -165", C(o["e"], "teal"), 3.5)
    else:
        b += RC(-10, -156, 20, 10, m, 2, 3)
    if "bands" in fl:
        for y in (-128, -100, -72): b += RC(-8, y, 16, 6, C(o.get("g"), "gold"), 2, 2.5)
    if "sight" in fl: b += RC(5, -138, 10, 5, C(o.get("g"), "iron"), 1, 2.5) + RC(12, -152, 5, 18, C(o.get("g"), "iron"), 2, 2.5)
    if v == "scope":  # a scope tube along the barrel with a bright lens at the front
        g = C(o.get("g"), "gold")
        b += RC(8, -120, 10, 56, g, 3, 3) + RC(6, -126, 14, 10, g, 3, 3) + RC(7, -70, 12, 8, g, 3, 3)
        b += GEM(13, -128, 6, C(o.get("e"), "cyan"))
    b += CI(0, -52, 5, darker(t, .7), 2.5)
    if v:  # trigger guard (left off the plain cosmetic rifle so its art stays the same)
        b += '<path d="M 9 -26 Q 22 -18 9 -6" fill="none" stroke="%s" stroke-width="7" stroke-linecap="round"/>' % INK
        b += '<path d="M 9 -26 Q 22 -18 9 -6" fill="none" stroke="%s" stroke-width="3.5" stroke-linecap="round"/>' % C(o.get("g"), "iron")
    return b, b

def draw_wand(o, two=False):
    m, t = C(o.get("m"), "wood"), C(o.get("t"), "gold")
    b = RC(-4, -70, 8, 86, m, 3) + RC(-6, -72, 12, 8, t, 2, 3)
    top = GEM(0, -84, 10, C(o.get("e"), t))
    return b + GLOW(top, C(o.get("glow"), o.get("e") or "arcane")) + top, b + top

def draw_totem(o, two=True):
    m, t = C(o.get("m"), "wood"), C(o.get("t"), "red")
    s = RC(-5, -110, 10, 140, m, 4)
    b = RC(-20, -168, 40, 30, m, 6) + RC(-16, -140, 32, 26, t, 5)
    b += CI(-7, -156, 4, INK, 0) + CI(7, -156, 4, INK, 0) + LN("M -8 -146 L 8 -146", INK, 3)
    b += P("M -20 -164 L -40 -176 L -20 -150 Z", t, 3) + P("M 20 -164 L 40 -176 L 20 -150 Z", t, 3)
    return s + b, b

WEAPONS = {"sword": draw_sword, "axe": draw_axe, "mace": draw_mace, "dagger": draw_dagger, "staff": draw_staff,
           "polearm": draw_polearm, "fist": draw_fist, "bow": draw_bow, "rifle": draw_rifle, "wand": draw_wand, "totem": draw_totem}

def weapon(o, two):
    s, glow_part = WEAPONS[o["family"]](o, two)
    if "glow" in o: s = GLOW(glow_part, C(o["glow"], "frost")) + s
    return "<g %s>%s</g>" % (RIGHT_HAND, s)

# ======================================================================== shield & held items (left paw)
def shield(o):
    v = o["variant"] or "round"
    m, t, e = C(o.get("m"), "wood"), C(o.get("t"), "iron"), C(o.get("e"), "gold")
    cx, cy = 74, 178
    if v in ("round", "buckler", "spiked"):
        r = 32 if v == "buckler" else 42
        shape = "M %d %d m -%d 0 a %d %d 0 1 0 %d 0 a %d %d 0 1 0 -%d 0" % (cx, cy, r, r, r, 2 * r, r, r, 2 * r)
        inner = "M %d %d m -%d 0 a %d %d 0 1 0 %d 0 a %d %d 0 1 0 -%d 0" % (cx, cy, r - 8, r - 8, r - 8, 2 * (r - 8), r - 8, r - 8, 2 * (r - 8))
    elif v == "kite":
        shape = "M %d %d Q %d %d %d %d L %d %d L %d %d Q %d %d %d %d Z" % (cx - 40, cy - 46, cx, cy - 56, cx + 40, cy - 46, cx + 36, cy - 6, cx, cy + 58, cx - 36, cy - 6, cx - 40, cy - 46)
        inner = "M %d %d Q %d %d %d %d L %d %d L %d %d Q %d %d %d %d Z" % (cx - 31, cy - 39, cx, cy - 47, cx + 31, cy - 39, cx + 28, cy - 6, cx, cy + 45, cx - 28, cy - 6, cx - 31, cy - 39)
    elif v == "tower":
        shape = "M %d %d L %d %d L %d %d Q %d %d %d %d Z" % (cx - 40, cy - 56, cx + 40, cy - 56, cx + 40, cy + 40, cx, cy + 62, cx - 40, cy + 40)
        inner = "M %d %d L %d %d L %d %d Q %d %d %d %d Z" % (cx - 31, cy - 47, cx + 31, cy - 47, cx + 31, cy + 34, cx, cy + 52, cx - 31, cy + 34)
    else:  # heater
        shape = "M %d %d L %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx - 42, cy - 48, cx + 42, cy - 48, cx + 44, cy + 22, cx, cy + 54, cx - 44, cy + 22, cx - 42, cy - 48)
        inner = "M %d %d L %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx - 33, cy - 39, cx + 33, cy - 39, cx + 34, cy + 18, cx, cy + 43, cx - 34, cy + 18, cx - 33, cy - 39)
    s = ""
    if v == "spiked":
        for k in range(10):
            a = k * math.pi / 5
            s += P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (cx + math.cos(a + .2) * 38, cy + math.sin(a + .2) * 38, cx + math.cos(a) * 56, cy + math.sin(a) * 56, cx + math.cos(a - .2) * 38, cy + math.sin(a - .2) * 38), C(o.get("t"), "steel"), 3)
    s += P(shape, t, 5) + P(inner, m, 3)
    em = o.get("emblem", "boss")
    if em == "boss": s += CI(cx, cy - 4, 12, e) + '<circle cx="%d" cy="%d" r="4" fill="#fff" opacity=".5"/>' % (cx - 4, cy - 8)
    elif em == "cross": s += RC(cx - 6, cy - 34, 12, 66, e, 2, 3) + RC(cx - 26, cy - 14, 52, 12, e, 2, 3)
    elif em == "stripe": s += '<g clip-path="url(#sh)">%s</g>' % P("M %d %d L %d %d L %d %d L %d %d Z" % (cx - 50, cy - 20, cx - 30, cy - 40, cx + 50, cy + 30, cx + 30, cy + 50), e, 3)
    elif em == "chevron": s += P("M %d %d L %d %d L %d %d L %d %d L %d %d L %d %d Z" % (cx - 28, cy - 6, cx, cy + 16, cx + 28, cy - 6, cx + 28, cy + 8, cx, cy + 30, cx - 28, cy + 8), e, 3)
    elif em == "skull":
        s += P("M %d %d Q %d %d %d %d Q %d %d %d %d L %d %d L %d %d Z" % (cx - 16, cy + 2, cx - 17, cy - 26, cx, cy - 26, cx + 17, cy - 26, cx + 16, cy + 2, cx + 9, cy + 12, cx - 9, cy + 12), C("bone", "bone"), 3)
        s += CI(cx - 7, cy - 10, 4.5, INK, 0) + CI(cx + 7, cy - 10, 4.5, INK, 0)
    elif em == "lion":
        for k in range(10):
            a = k * math.pi / 5
            s += EL(cx + math.cos(a) * 16, cy - 4 + math.sin(a) * 16, 8, 6, darker(e, .85), 2.5, math.degrees(a))
        s += CI(cx, cy - 4, 14, e, 3) + CI(cx - 5, cy - 7, 2, INK, 0) + CI(cx + 5, cy - 7, 2, INK, 0) + LN("M %d %d Q %d %d %d %d" % (cx - 4, cy + 2, cx, cy + 5, cx + 4, cy + 2), INK, 2)
    elif em == "sun":
        for k in range(12):
            a = k * math.pi / 6
            s += LN("M %.1f %.1f L %.1f %.1f" % (cx + math.cos(a) * 14, cy - 4 + math.sin(a) * 14, cx + math.cos(a) * 26, cy - 4 + math.sin(a) * 26), e, 4)
        s += CI(cx, cy - 4, 12, e, 3)
    elif em == "star":
        pts = " L ".join("%.1f %.1f" % (cx + math.cos(-math.pi / 2 + k * math.pi / 5) * (22 if k % 2 == 0 else 9), cy - 4 + math.sin(-math.pi / 2 + k * math.pi / 5) * (22 if k % 2 == 0 else 9)) for k in range(10))
        s += P("M " + pts + " Z", e, 3)
    elif em == "gem": s += GEM(cx, cy - 4, 11, e)
    if "glow" in o: s = GLOW(P(shape, "#000"), C(o["glow"], "holy")) + s
    return s

def held(o):
    v = o["variant"] or "orb"
    m, t, e = C(o.get("m"), "purple"), C(o.get("t"), "gold"), C(o.get("e"), "sky")
    x, y = LEFT_HAND
    if v == "book":
        s = '<g transform="rotate(-10 %d %d)">' % (x, y)
        s += RC(x - 28, y - 32, 56, 64, m, 5, 5) + RC(x - 22, y - 30, 48, 58, "#fff3dc", 3, 3) + RC(x - 28, y - 32, 50, 64, m, 5, 5)
        s += RC(x - 22, y - 26, 38, 52, darker(m, .85), 3, 2.5) + GEM(x - 3, y, 8, e) + RC(x + 16, y - 6, 10, 12, t, 2, 3) + "</g>"
    elif v == "torch":
        s = RC(x - 5, y - 20, 10, 56, C(o.get("g"), "wood"), 3) + RC(x - 8, y - 24, 16, 10, t, 3, 3)
        fl = P("M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (x - 12, y - 26, x - 16, y - 48, x - 2, y - 64, x + 2, y - 50, x + 8, y - 58, x + 18, y - 40, x + 12, y - 26), C(o.get("e"), "orange"), 3)
        s = GLOW(fl, C(o.get("glow"), "fire")) + s + fl
    elif v == "mug":
        s = RC(x - 20, y - 26, 40, 46, m, 6, 5) + '<path d="M %d %d q 18 4 0 26" fill="none" stroke="%s" stroke-width="8"/>' % (x + 20, y - 16, INK)
        s += EL(x, y - 26, 20, 7, C(o.get("e"), "cream"), 4) + RC(x - 20, y - 14, 40, 7, t, 2, 3) + RC(x - 20, y + 6, 40, 7, t, 2, 3)
    elif v == "pouch":
        s = P("M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (x - 8, y - 22, x - 30, y, x - 20, y + 22, x, y + 28, x + 20, y + 22, x + 30, y, x + 8, y - 22), m)
        s += LN("M %d %d L %d %d" % (x - 10, y - 20, x + 10, y - 20), C(o.get("t"), "gold"), 4) + P("M %d %d L %d %d L %d %d Z" % (x - 8, y - 22, x - 14, y - 34, x, y - 26), m, 3) + P("M %d %d L %d %d L %d %d Z" % (x + 8, y - 22, x + 14, y - 34, x, y - 26), m, 3)
    elif v == "wand":
        s = RC(x - 4, y - 30, 8, 62, C(o.get("g"), "wood"), 3) + RC(x - 7, y - 30, 14, 8, t, 2, 3)
        top = GEM(x, y - 42, 11, e) if "star" not in o["flags"] else P("M " + " L ".join("%.1f %.1f" % (x + math.cos(-math.pi / 2 + k * math.pi / 5) * (16 if k % 2 == 0 else 7), y - 44 + math.sin(-math.pi / 2 + k * math.pi / 5) * (16 if k % 2 == 0 else 7)) for k in range(10)) + " Z", e, 3)
        s = GLOW(top, C(o.get("glow"), e)) + s + top if "glow" in o else s + top
    elif v == "bone":
        bone = C(o.get("m"), "bone")
        s = '<g transform="rotate(-30 %d %d)">%s%s%s%s%s</g>' % (x, y, RC(x - 6, y - 30, 12, 60, bone, 6), CI(x - 8, y - 32, 9, bone), CI(x + 8, y - 32, 9, bone), CI(x - 8, y + 32, 9, bone), CI(x + 8, y + 32, 9, bone))
    elif v == "lantern":
        s = LN("M %d %d Q %d %d %d %d" % (x - 10, y - 40, x, y - 54, x + 10, y - 40), INK, 4) + RC(x - 16, y - 40, 32, 10, t, 3) + RC(x - 13, y - 30, 26, 32, C(o.get("e"), "yellow"), 4) + RC(x - 16, y + 2, 32, 8, t, 3)
        s = GLOW(RC(x - 13, y - 30, 26, 32, "#000"), C(o.get("glow"), "holy")) + s
    elif v == "crystal":
        s = ""
        for dx, h, a in ((-12, 34, -16), (12, 30, 18), (0, 48, 0)):
            s += '<g transform="rotate(%d %d %d)">%s</g>' % (a, x + dx, y + 6, P("M %d %d L %d %d L %d %d L %d %d Z" % (x + dx - 8, y + 6, x + dx, y + 6 - h, x + dx + 8, y + 6, x + dx, y + 14), e, 3.5))
        s = GLOW(s, C(o.get("glow"), e)) + s + RC(x - 20, y + 6, 40, 12, t, 4)
    elif v == "skull":
        s = P("M %d %d Q %d %d %d %d Q %d %d %d %d L %d %d L %d %d Z" % (x - 20, y + 4, x - 22, y - 34, x, y - 34, x + 22, y - 34, x + 20, y + 4, x + 12, y + 16, x - 12, y + 16), C(o.get("m"), "bone"))
        s += CI(x - 8, y - 12, 6, e, 2.5) + CI(x + 8, y - 12, 6, e, 2.5) + LN("M %d %d L %d %d M %d %d L %d %d" % (x - 4, y + 8, x - 4, y + 15, x + 4, y + 8, x + 4, y + 15), INK, 2.5)
    elif v == "flower":
        s = LN("M %d %d Q %d %d %d %d" % (x, y + 30, x - 6, y, x, y - 26), "#2f7a3a", 5) + EL(x - 10, y + 4, 9, 4, "#4fae4a", 2.5, -30)
        for k in range(6):
            a = k * math.pi / 3
            s += EL(x + math.cos(a) * 11, y - 30 + math.sin(a) * 11, 8, 5.5, e, 3, math.degrees(a))
        s += CI(x, y - 30, 6, C(o.get("t"), "yellow"), 3)
    elif v == "bottle":
        s = P("M %d %d L %d %d Q %d %d %d %d Q %d %d %d %d L %d %d Z" % (x - 6, y - 40, x - 6, y - 24, x - 24, y - 14, x - 22, y + 14, x + 22, y + 14, x + 24, y - 14, x + 6, y - 24), "#e8f4ff")
        s += P("M %d %d Q %d %d %d %d Q %d %d %d %d Z" % (x - 21, y - 2, x, y - 8, x + 21, y - 2, x + 20, y + 12, x - 20, y + 12), e, 0) + RC(x - 8, y - 48, 16, 10, C(o.get("t"), "brown"), 3, 3)
    elif v == "scroll":
        s = RC(x - 20, y - 30, 40, 54, "#f3e4bf", 3) + CI(x - 20, y - 30, 7, "#e3cf9f", 3) + CI(x + 20, y - 30, 7, "#e3cf9f", 3)
        for k in range(4): s += LN("M %d %d L %d %d" % (x - 12, y - 16 + k * 10, x + 12, y - 16 + k * 10), "#9a7a50", 2.5)
        s += CI(x, y + 26, 6, e, 3)
    elif v == "idol":
        s = P("M %d %d Q %d %d %d %d Q %d %d %d %d L %d %d L %d %d Z" % (x - 12, y + 18, x - 16, y - 10, x, y - 36, x + 16, y - 10, x + 12, y + 18, x + 18, y + 24, x - 18, y + 24), m) + GEM(x, y - 14, 6, e)
    elif v == "fan":
        s = ""
        for k in range(7):
            a = -70 + k * 23
            s += '<g transform="rotate(%d %d %d)">%s</g>' % (a, x, y + 10, P("M %d %d L %d %d L %d %d Z" % (x - 6, y + 10, x, y - 34, x + 6, y + 10), m if k % 2 else light(m, .3), 3))
        s += CI(x, y + 10, 6, t, 3)
    elif v == "shard":
        s = P("M %d %d L %d %d L %d %d L %d %d Z" % (x - 14, y + 10, x - 4, y - 40, x + 16, y - 12, x + 6, y + 20), e)
        s = GLOW(s, C(o.get("glow"), e)) + s
    else:  # orb on a claw stand
        claw = P("M %d %d Q %d %d %d %d L %d %d Z" % (x - 4, y + 14, x - 26, y + 4, x - 18, y - 16, x - 8, y + 2), t, 3)
        orb = GEM(x, y - 12, 18, e)
        s = GLOW(CI(x, y - 12, 18, "#000"), C(o.get("glow"), e)) + orb + claw + mirror(claw, x) + RC(x - 10, y + 10, 20, 12, t, 4)
    return s

# ======================================================================== head (head space)
def head(o):
    v = o["variant"] or "helm"
    m, t, e = C(o.get("m"), "steel"), C(o.get("t"), "gold"), C(o.get("e"), "ruby")
    f = o["flags"]; s = ""
    if v == "none":
        pass
    elif v in ("hood", "cowl"):
        top = "Q 128 -6 128 -6" if v == "hood" and "point" in f else ""
        outer = ("M 34 128 Q 22 40 112 10 L 128 -10 L 144 10 Q 234 40 222 128 Q 228 176 196 182 L 60 182 Q 28 176 34 128 Z" if "point" in f
                 else "M 34 128 Q 26 26 128 14 Q 230 26 222 128 Q 228 176 196 182 L 60 182 Q 28 176 34 128 Z")
        hole = "M 58 122 Q 60 62 128 58 Q 196 62 198 122 Q 196 170 128 172 Q 60 170 58 122 Z"
        s += '<path d="%s %s" fill="%s" fill-rule="evenodd" stroke="%s" stroke-width="5" stroke-linejoin="round"/>' % (outer, hole, m, INK)
        s += LN(hole, t, 7) + LN(hole, INK, 2.5)
        if "gem" in f: s += GEM(128, 62, 7, e)
        if "mask" in f: s += P("M 58 128 Q 128 150 198 128 Q 196 170 128 172 Q 60 170 58 128 Z", darker(m, .85))
    elif v in ("cap", "skullcap"):
        s += P("M 44 98 Q 44 30 128 26 Q 212 30 212 98 Q 128 84 44 98 Z", m, 5) + P("M 42 96 Q 128 80 214 96 L 212 108 Q 128 94 44 108 Z", t, 4)
        for x in (90, 128, 166): s += LN("M %d 34 Q %d 60 %d 88" % (x, x + (x - 128) * .15, x + (x - 128) * .2), darker(m, .8), 2.5)
        if "gem" in f: s += GEM(128, 98, 7, e)
    elif v == "mitre":
        s += P("M 74 78 Q 76 22 128 -8 Q 180 22 182 78 Q 128 88 74 78 Z", m, 5) + RC(120, -2, 16, 82, t, 4, 3.5)
        s += P("M 72 70 Q 128 82 184 70 L 184 80 Q 128 92 72 80 Z", t, 3.5)
    elif v == "turban":
        s += P("M 40 96 Q 30 22 128 16 Q 226 22 216 96 Q 128 78 40 96 Z", m, 5)
        for k in range(3): s += LN("M %d %d Q 128 %d %d %d" % (50 + k * 8, 78 - k * 18, 30 - k * 14, 206 - k * 8, 78 - k * 18), darker(m, .75), 3)
        s += GEM(128, 60, 9, e) + P("M 128 50 Q 120 20 140 6 Q 136 30 134 50 Z", C(o.get("g"), "white"), 3)
    elif v == "tricorn":
        s += P("M 74 72 Q 76 22 128 18 Q 180 22 182 72 Z", m, 5) + P("M 24 66 Q 128 30 232 66 Q 220 86 196 80 Q 128 98 60 80 Q 36 86 24 66 Z", m, 5)
        s += LN("M 30 68 Q 128 34 226 68", t, 3)
        if "skull" in f: s += P("M 118 60 Q 117 44 128 44 Q 139 44 138 60 L 133 65 L 123 65 Z", "#f6f6f2", 3) + CI(124, 54, 2.5, INK, 0) + CI(132, 54, 2.5, INK, 0)
    elif v == "santa":
        s += P("M 50 84 Q 70 16 140 10 Q 200 14 214 60 Q 222 90 236 96 Q 200 40 176 76 Z", m, 5)
        s += P("M 44 88 Q 128 62 212 88 L 212 104 Q 128 80 44 104 Z", "#ffffff", 5) + CI(236, 100, 13, "#ffffff", 5)
    elif v == "pumpkin":
        s += EL(128, 104, 96, 82, "#f08a24", 5) + LN("M 128 24 Q 100 104 128 184 M 128 24 Q 156 104 128 184 M 80 34 Q 50 104 84 178 M 176 34 Q 206 104 172 178", "#c4621a", 3)
        s += RC(118, 6, 20, 24, "#4a7a2a", 4, 4)
        for x in (92, 164): s += P("M %d 112 L %d 88 L %d 112 Z" % (x - 16, x, x + 16), "#ffd24a", 3)
        s += P("M 84 140 L 100 150 L 116 140 L 128 152 L 140 140 L 156 150 L 172 140 Q 128 176 84 140 Z", "#ffd24a", 3)
    elif v == "monocle":
        s += '<circle cx="158" cy="112" r="19" fill="%s" fill-opacity=".25" stroke="%s" stroke-width="5"/><circle cx="158" cy="112" r="19" fill="none" stroke="%s" stroke-width="2.5"/>' % (e, INK, t)
        s += LN("M 172 126 Q 190 160 176 184", t, 2.5)
    elif v == "eyepatch":
        s += LN("M 40 92 Q 128 70 216 92", INK, 4) + EL(98, 112, 17, 14, m, 4)
    elif v == "antlers":
        for sx in (-1, 1):
            ant = P("M 92 60 Q 70 30 60 0 Q 66 4 70 14 Q 74 0 84 -8 Q 82 10 78 22 Q 86 36 100 54 Z", m, 4)
            s += ant if sx < 0 else mirror(ant, 128)
    elif v == "flowers":
        s += P("M 50 84 Q 128 52 206 84 L 204 94 Q 128 64 52 94 Z", C(o.get("g"), "green"), 3.5)
        for k, x in enumerate(range(62, 200, 24)):
            y = 82 - math.sin((x - 50) / 156 * math.pi) * 24
            col = m if k % 2 == 0 else t
            for j in range(5):
                a = j * 2 * math.pi / 5
                s += CI(x + math.cos(a) * 6, y + math.sin(a) * 6, 5.5, col, 2.5)
            s += CI(x, y, 4, "#fff6a0", 2)
    elif v == "halo":
        ring = '<ellipse cx="128" cy="24" rx="62" ry="14" fill="none" stroke="%s" stroke-width="12"/><ellipse cx="128" cy="24" rx="62" ry="14" fill="none" stroke="%s" stroke-width="6"/>' % (INK, m)
        s += GLOW(ring, m) + ring
    elif v == "headdress":
        for k in range(9):
            a = math.radians(-60 + k * 15)
            x1, y1 = 128 + math.sin(a) * 70, 74 - math.cos(a) * 70
            fe = P("M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" % (128 + math.sin(a) * 30, 74 - math.cos(a) * 30, x1 - 10, y1 + 6, x1, y1 - 30, x1 + 10, y1 + 6, 128 + math.sin(a) * 30 + 2, 74 - math.cos(a) * 30), m if k % 2 else t, 3)
            s += fe
        s += P("M 44 94 Q 128 64 212 94 L 212 108 Q 128 80 44 108 Z", t, 4)
        for x in (80, 128, 176): s += GEM(x, 96 - (14 if x == 128 else 8), 5, C(o.get("e"), "teal"))
    elif v == "partyhat":
        s += P("M 92 70 L 128 -16 L 164 70 Z", m, 5)
        for y in (10, 34, 56): s += LN("M %d %d L %d %d" % (128 - (y + 16) * 0.42, y, 128 + (y + 16) * 0.42, y), t, 7)
        s += CI(128, -18, 9, t, 4)
    elif v == "featcap":
        s += P("M 56 92 Q 60 40 128 34 Q 196 40 200 92 Q 128 80 56 92 Z", m, 5) + P("M 50 90 Q 128 74 206 90 L 204 100 Q 128 86 52 100 Z", darker(m, .85), 4)
        s += P("M 176 64 Q 230 30 232 -6 Q 210 30 168 56 Z", t, 4) + LN("M 172 60 Q 214 30 228 2", darker(t, .7), 2)
    elif v == "circlet":
        s += P("M 46 86 Q 128 54 210 86 L 208 98 Q 128 68 48 98 Z", t, 4) + GEM(128, 72, 8, e)
        if "gem" in f: s += GEM(88, 80, 4.5, e) + GEM(168, 80, 4.5, e)
    elif v == "crown":
        s += P("M 70 70 L 64 26 L 88 46 L 106 16 L 128 40 L 150 16 L 168 46 L 192 26 L 186 70 Q 128 60 70 70 Z", t, 5)
        s += GEM(128, 58, 7, e) + GEM(97, 60, 4.5, C(o.get("g"), "sapphire")) + GEM(159, 60, 4.5, C(o.get("g"), "sapphire"))
        for x, y in ((64, 26), (106, 16), (150, 16), (192, 26)): s += CI(x, y, 4, light(t, .3), 3)
    elif v == "wizard":
        s += EL(128, 74, 98, 22, m, 5) + P("M 72 72 Q 100 30 120 -4 Q 136 -26 168 -14 Q 140 -6 150 20 Q 160 50 184 72 Q 128 86 72 72 Z", m, 5)
        s += P("M 74 66 Q 128 82 182 66 L 184 76 Q 128 92 72 76 Z", t, 3.5)
        if "gem" in f or "star" in f: s += GEM(128, 40, 7, e)
    elif v == "tophat":
        s += EL(128, 66, 78, 14, m, 5) + RC(84, -4, 88, 70, m, 6, 5) + RC(84, 44, 88, 12, t, 2, 4)
    elif v == "chef":
        s += RC(70, 40, 116, 30, "#fff", 6, 5)
        for cx, cy, r in ((86, 26, 24), (128, 14, 30), (170, 26, 24)): s += CI(cx, cy, r, "#fff", 5)
        s += RC(70, 40, 116, 30, "#fff", 6, 0) + LN("M 72 40 L 184 40", INK, 0)
    elif v == "bandana":
        s += P("M 44 92 Q 46 36 128 30 Q 210 36 212 92 Q 128 76 44 92 Z", m, 5)
        s += P("M 206 80 L 236 70 L 230 94 Z", m, 4) + P("M 206 86 L 232 102 L 214 108 Z", m, 4)
        for x, y in ((90, 50), (150, 46), (120, 66), (178, 64)): s += CI(x, y, 4, light(m, .5), 0)
    elif v == "goggles":
        s += P("M 44 84 Q 128 70 212 84 L 212 96 Q 128 82 44 96 Z", C(o.get("g"), "leather"), 4)
        for x in (100, 156): s += CI(x, 80, 18, t, 5) + CI(x, 80, 11, e, 3) + '<circle cx="%d" cy="76" r="4" fill="#fff" opacity=".8"/>' % (x - 4)
    elif v == "mask":
        s += P("M 40 100 Q 128 84 216 100 L 214 126 Q 128 112 42 126 Z", m, 4) + EL(98, 112, 16, 9, "#000", 0) + EL(158, 112, 16, 9, "#000", 0)
    elif v == "hat":  # wide-brimmed adventurer hat
        s += EL(128, 74, 104, 18, m, 5) + P("M 70 74 Q 72 20 128 16 Q 184 20 186 74 Q 128 84 70 74 Z", m, 5) + P("M 72 60 Q 128 72 184 60 L 185 70 Q 128 82 71 70 Z", t, 3.5)
        if "plume" in f: s += P("M 176 60 Q 220 20 214 -6 Q 196 30 168 54 Z", e, 4)
    elif v == "skull":
        s += P("M 44 98 Q 40 20 128 16 Q 216 20 212 98 Z", C(o.get("m"), "bone"), 5)
        s += EL(98, 64, 16, 14, INK, 0) + EL(158, 64, 16, 14, INK, 0) + P("M 122 80 L 128 70 L 134 80 Z", INK, 0)
        for k in range(8): s += RC(64 + k * 16, 90, 12, 14, C(o.get("m"), "bone"), 2, 3)
    else:  # helm, greathelm (open-faced, cheek guards), all with optional horns / wings / plume / crest / spikes
        s += P("M 44 100 Q 42 26 128 22 Q 214 26 212 100 Z", m, 5)
        if v == "greathelm":
            cheek = P("M 40 92 L 70 92 Q 74 130 62 158 Q 42 150 38 120 Z", m, 5)
            s += cheek + mirror(cheek, 128)
        s += RC(36, 88, 184, 17, t, 8.5, 5)
        if "ridge" in f or v == "greathelm" or v == "helm":
            s += RC(121, 26, 14, 64, t, 7, 4)
        if "gem" in f: s += GEM(128, 70, 8, e)
    # extras that sit on any hat
    if "horns" in f:
        horn = P("M 54 70 Q 12 60 20 12 Q 34 44 64 50 Z", C(o.get("g"), "bone"), 5)
        s = horn + mirror(horn, 128) + s
    if "bighorns" in f:
        horn = P("M 56 76 Q 0 76 6 24 Q 12 0 34 6 Q 18 18 26 40 Q 36 58 66 54 Z", C(o.get("g"), "bone"), 5)
        s = horn + mirror(horn, 128) + s
    if "wings" in f:
        wing = P("M 46 70 Q 10 50 4 14 Q 22 30 30 26 Q 24 44 50 52 Z", C(o.get("g"), "white"), 4.5)
        s = wing + mirror(wing, 128) + s
    if "plume" in f and v != "hat":
        s = P("M 122 28 Q 110 -14 150 -24 Q 136 -2 140 26 Z", e, 4) + s
    if "crest" in f:
        s = P("M 96 30 Q 128 -16 160 30 Z", e, 4) + s
    if "spikes" in f:
        sp = "".join(P("M %d %d L %d %d L %d %d Z" % (x - 7, y + 4, x + dx, y - 22, x + 7, y + 4), C(o.get("t"), "steel"), 3.5) for x, y, dx in ((76, 44, -8), (128, 28, 0), (180, 44, 8)))
        s = sp + s
    if "glow" in o: s = GLOW(s, C(o["glow"], "frost")) + s
    return "<g %s>%s</g>" % (HEAD_TF, s)

# ======================================================================== chest, belt, neck, ring (body space)
BODY_OUT = "M 76 116 Q 128 128 180 116 Q 202 160 196 214 L 60 214 Q 54 160 76 116 Z"
def chest(o):
    v = o["variant"] or "robe"
    m, t, e = C(o.get("m"), "purple"), C(o.get("t"), "gold"), C(o.get("e"), "ruby")
    f = o["flags"]; s = ""
    if v == "vest":
        left = "M 76 116 Q 104 124 116 126 L 110 214 L 60 214 Q 54 160 76 116 Z"
        s += P(left, m, 5) + mirror(P(left, m, 5), 128)
        for y in (140, 160, 180, 200): s += LN("M 112 %d L 144 %d M 144 %d L 112 %d" % (y, y + 10, y, y + 10), C(o.get("t"), "tan"), 2.5)
        s += LN("M 70 140 Q 80 170 72 206", darker(m, .75), 2.5) + mirror(LN("M 70 140 Q 80 170 72 206", darker(m, .75), 2.5), 128)
    else:
        s += P(BODY_OUT, m, 5)
        if v == "scale":
            pat = "".join('<path d="M %d %d q 7 10 14 0" fill="none" stroke="%s" stroke-width="2.2"/>' % (x + (7 if (y // 9) % 2 else 0), y, darker(m, .65)) for y in range(122, 214, 9) for x in range(46, 206, 14))
            s += '<g clip-path="url(#chestclip)">%s</g>' % pat
        if v == "shirt":
            col = P("M 100 118 L 128 150 L 112 158 L 92 124 Z", C(o.get("t"), "cream"), 3.5)
            s += col + mirror(col, 128) + LN("M 128 150 L 128 212", darker(m, .7), 2.5)
            for y in (164, 182, 200): s += CI(128, y, 3, C(o.get("t"), "cream"), 2)
        if "pauldrons" in f and v not in ("plate",):
            pa = EL(70, 128, 28, 18, C(o.get("t"), "steel"), 5, -10)
            s += pa + mirror(pa, 128)
        if v == "mail":
            pat = "".join('<path d="M %d %d q 6 6 12 0" fill="none" stroke="%s" stroke-width="2"/>' % (x + (6 if (y // 10) % 2 else 0), y, darker(m, .7)) for y in range(126, 214, 10) for x in range(48, 206, 12))
            s += '<g clip-path="url(#chestclip)">%s</g>' % pat
        if v == "plate":
            s += LN("M 128 126 L 128 210", light(m, .5), 4) + LN("M 86 150 Q 128 166 170 150", darker(m, .75), 3)
            pa = EL(70, 128, 30, 19, t, 5, -10) + EL(66, 120, 18, 8, light(t, .35), 0, -10)
            s += pa + mirror(pa, 128)
            if "spikes" in f:
                sp = P("M 56 118 L 46 92 L 70 112 Z", C(o.get("e"), "steel"), 3.5)
                s += sp + mirror(sp, 128)
        if v in ("robe", "tabard"):
            s += LN("M 128 128 L 128 214", t, 7) + LN("M 128 128 L 128 214", INK, 2)
            s += P("M 100 120 L 128 160 L 156 120 L 146 118 L 128 144 L 110 118 Z", t, 3)
        if v == "tabard" or "emblem" in f:
            s += RC(108, 150, 40, 46, t, 4, 4) + RC(114, 156, 28, 34, e, 3, 3)
        if v == "leather":
            s += LN("M 80 150 Q 128 164 176 150", darker(m, .7), 3) + LN("M 128 128 L 128 212", darker(m, .7), 3)
            for y in (136, 156, 176, 196): s += CI(128, y, 3, C(o.get("t"), "brass"), 2)
    if v == "leaves":
        for row, y in enumerate(range(128, 214, 18)):
            for x in range(62 + (row % 2) * 12, 200, 24):
                s += '<g clip-path="url(#chestclip)">%s</g>' % EL(x, y, 13, 8, m if (x // 24 + row) % 2 else t, 2.5, 30 if row % 2 else -30)
    if "fur" in f:
        s += P("M 70 124 Q 128 146 186 124 Q 190 110 176 108 Q 128 128 80 108 Q 66 110 70 124 Z", C(o.get("g"), "cream"), 4)
    if "sash" in f:
        s += P("M 70 130 L 84 124 L 194 196 L 186 210 Z", C(o.get("g"), "red"), 3.5)
    if "glow" in o: s = GLOW(P(BODY_OUT, "#000"), C(o["glow"], "arcane")) + s
    return s

def belt(o):
    v = o["variant"] or "square"
    m, t, e = C(o.get("m"), "leather"), C(o.get("t"), "gold"), C(o.get("e"), "ruby")
    s = '<g clip-path="url(#bodyclip)">%s</g>' % P("M 40 186 Q 128 196 216 186 L 216 202 Q 128 212 40 202 Z", m, 4)
    if v == "sash":
        s = '<g clip-path="url(#bodyclip)">%s</g>' % P("M 40 184 Q 128 196 216 184 L 216 204 Q 128 214 40 204 Z", m, 4)
        s += P("M 148 194 L 162 226 L 150 228 L 142 200 Z", m, 3.5) + P("M 150 194 L 176 220 L 166 226 L 144 200 Z", m, 3.5) + CI(146, 196, 7, darker(m, .85), 3)
        return s
    if v == "chain":
        s = '<g clip-path="url(#bodyclip)">%s</g>' % "".join(EL(x, 194 + 0.0006 * (x - 128) ** 2 * -1, 8, 5, t, 3) for x in range(44, 216, 13))
        return s + RC(118, 186, 20, 18, t, 4, 4)
    if v == "studded":
        s += '<g clip-path="url(#bodyclip)">%s</g>' % "".join(CI(x, 194 + (128 - abs(x - 128)) * 0.055, 2.6, t, 1.5) for x in range(50, 210, 11))
        s += RC(116, 187, 24, 18, t, 3, 4) + RC(122, 192, 12, 8, m, 1, 2.5)
    elif v == "plates":
        s += '<g clip-path="url(#bodyclip)">%s</g>' % "".join(RC(x - 9, 186 + (128 - abs(x - 128)) * 0.05, 18, 16, t, 2, 3) for x in range(52, 212, 22))
        s += RC(114, 185, 28, 22, t, 3, 4) + (GEM(128, 196, 6, e) if "e" in o else "")
    elif v == "round": s += CI(128, 196, 11, t, 4) + CI(128, 196, 5, m, 2.5)
    elif v == "skull":
        s += P("M 116 200 Q 115 182 128 182 Q 141 182 140 200 L 134 206 L 122 206 Z", C(o.get("t"), "bone"), 3.5) + CI(123, 194, 3, INK, 0) + CI(133, 194, 3, INK, 0)
    elif v == "gem": s += RC(114, 186, 28, 20, t, 5, 4) + GEM(128, 196, 6, e)
    elif v == "plate": s += P("M 108 186 L 148 186 L 144 208 L 128 214 L 112 208 Z", t, 4) + GEM(128, 198, 5, e)
    elif v == "rope": s = '<g clip-path="url(#bodyclip)">%s%s</g>' % (P("M 40 188 Q 128 198 216 188 L 216 198 Q 128 208 40 198 Z", m, 3.5), "".join(LN("M %d 189 L %d 200" % (x, x + 6), darker(m, .7), 2) for x in range(48, 210, 9)))
    else: s += RC(116, 187, 24, 18, t, 3, 4) + RC(122, 192, 12, 8, m, 1, 2.5)
    if "pouch" in o["flags"]: s += RC(156, 196, 22, 20, darker(m, .9), 5, 4) + LN("M 156 204 L 178 204", INK, 2.5)
    return s

def neck(o):
    v = o["variant"] or "gem"
    t, e, m = C(o.get("t"), "gold"), C(o.get("e"), "sapphire"), C(o.get("m"), "gold")
    s = ""
    chain = "M 98 130 Q 108 152 128 156 Q 148 152 158 130"
    if v == "pearls":
        for k in range(11):
            a = k / 10; x = 98 + 60 * a; y = 130 + 26 * math.sin(math.pi * a)
            s += CI(x, y, 4.2, C(o.get("e"), "pearl"), 2.5)
        return s
    s += LN(chain, INK, 6) + LN(chain, t, 3)
    y = 166
    if v == "medal": s += CI(128, y, 11, m, 4) + CI(128, y, 5.5, e, 2.5)
    elif v == "fang": s += P("M 122 156 Q 128 186 136 158 Z", C(o.get("m"), "bone"), 3.5)
    elif v == "skull": s += P("M 119 170 Q 118 154 128 154 Q 138 154 137 170 L 133 176 L 123 176 Z", C(o.get("m"), "bone"), 3.5) + CI(124, 164, 2.5, INK, 0) + CI(132, 164, 2.5, INK, 0)
    elif v == "cross": s += RC(124, 156, 8, 26, m, 2, 3) + RC(117, 162, 22, 8, m, 2, 3) + GEM(128, 166, 3, e)
    elif v == "star":
        pts = " L ".join("%.1f %.1f" % (128 + math.cos(-math.pi / 2 + k * math.pi / 5) * (12 if k % 2 == 0 else 5), y + math.sin(-math.pi / 2 + k * math.pi / 5) * (12 if k % 2 == 0 else 5)) for k in range(10))
        s += P("M " + pts + " Z", m, 3)
    elif v == "leaf": s += EL(128, y, 7, 12, C(o.get("m"), "green"), 3) + LN("M 128 156 L 128 176", darker(C(o.get("m"), "green"), .6), 2)
    elif v == "tear": s += P("M 128 154 Q 140 170 128 180 Q 116 170 128 154 Z", e, 3.5)
    else: s += P("M 128 154 L 140 166 L 128 182 L 116 166 Z", e, 3.5) + '<path d="M 124 162 L 128 158 L 132 162" stroke="#fff" stroke-width="2" fill="none" opacity=".8"/>' + RC(123, 150, 10, 6, t, 2, 2.5)
    if "glow" in o: s = GLOW(s, C(o["glow"], e)) + s
    return s

def ring(o, pose):
    t, e = C(o.get("t"), "gold"), o.get("e")
    x, y = (90, 203) if pose == "down" else (64, 120)
    s = '<path d="M %d %d q 10 6 20 0" fill="none" stroke="%s" stroke-width="7" stroke-linecap="round"/><path d="M %d %d q 10 6 20 0" fill="none" stroke="%s" stroke-width="3.5" stroke-linecap="round"/>' % (x - 10, y, INK, x - 10, y, t)
    if e: s += GEM(x, y + 2, 4.5, C(e, "ruby"))
    if "glow" in o: s = GLOW(s, C(o["glow"], "arcane")) + s
    return s

def qpts(p0, p1, p2, n):
    """n+1 points along a quadratic curve"""
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]) for u in (k / n for k in range(n + 1))]

# side drapes (user choice "A", 1.5.3): the cape hangs down both sides of the body from the shoulders and its
# rounded hem tucks in behind the body, so nothing runs across the bottom under the paws
DRAPE_OUT = ("M 74 108 Q 30 150 30 196 Q 40 214 62 210 Q 60 170 96 120 Z",
             "M 182 108 Q 226 150 226 196 Q 216 214 194 210 Q 196 170 160 120 Z")
DRAPE_IN = ("M 76 116 Q 40 154 40 194 Q 48 204 60 202 Q 60 168 92 124 Z",
            "M 180 116 Q 216 154 216 194 Q 208 204 196 202 Q 196 168 164 124 Z")
DRAPE_EDGE = (((74, 108), (30, 150), (30, 196)), ((182, 108), (226, 150), (226, 196)))  # outer edges, for fur and studs

def cloak(o):
    """Gear cloaks (real item icons): a cape hanging behind the body, seen as two drapes down its sides.
    m = cloth, t = edge trim, g = hood lining / fur. Flags: hood (a hood resting behind the head),
    fur (fluffy fur edge), studs (studded leather edge)."""
    m, t, g = C(o.get("m"), "red"), C(o.get("t"), "gold"), o.get("g")
    f = o["flags"]; s = ""
    if "hood" in f:
        # the hood lies behind the head and shoulders: only its rim shows around them
        hood = "M 40 138 Q 26 74 70 46 Q 128 18 186 46 Q 230 74 216 138 Z"
        s += P(hood, m, 5) + LN("M 50 128 Q 40 80 78 56 Q 128 32 178 56 Q 216 80 206 128", C(g, darker(m, .55)), 6)
    for pth in DRAPE_OUT: s += P(pth, t, 5)
    for pth in DRAPE_IN: s += P(pth, m, 3)
    # cloth folds on the drapes
    s += LN("M 56 150 Q 46 172 48 194", darker(m, .72), 3) + LN("M 200 150 Q 210 172 208 194", darker(m, .72), 3)
    if "fur" in f:
        fur = C(g, "cream")
        for side in DRAPE_EDGE:
            for x, y in qpts(*side, n=6)[1:]:
                s += CI(x + (4 if x < 128 else -4), y, 8, fur, 3)
    if "studs" in f:
        for side in DRAPE_EDGE:
            for x, y in qpts(*side, n=5)[1:]:
                s += CI(x + (6 if x < 128 else -6), y, 3.2, C(o.get("e"), "brass"), 2)
    return s

def back(o):
    v = o["variant"] or "cape"
    m, t = C(o.get("m"), "red"), C(o.get("t"), "gold")
    if v == "cloak": return cloak(o)
    if v == "cape":
        # cosmetic capes use the same side drapes as gear cloaks: main = cloth, trim = lining
        return "".join(P(pth, m, 5) for pth in DRAPE_OUT) + "".join(P(pth, t, 3) for pth in DRAPE_IN)
    if v in ("angelwings", "batwings"):
        if v == "angelwings":
            w = P("M 84 140 Q 40 86 4 64 Q 8 96 20 106 Q 0 116 4 138 Q 22 140 30 146 Q 12 162 22 180 Q 48 172 86 172 Z", m, 4)
            w += LN("M 70 140 Q 40 116 16 100", t, 2.5) + LN("M 72 152 Q 40 140 14 132", t, 2.5) + LN("M 74 164 Q 46 160 28 164", t, 2.5)
        else:
            w = P("M 86 140 L 12 64 L 22 112 L 2 124 L 28 148 L 14 176 L 86 172 Z", m, 4)
            w += LN("M 86 142 L 12 64 M 70 152 L 22 112 M 62 160 L 2 124 M 70 166 L 28 148", t, 3)
        return w + mirror(w, 128)
    if v == "quiver":
        q = RC(160, 50, 30, 100, m, 6, 5)
        for k, x in enumerate((164, 174, 184)):
            q = P("M %d 52 L %d 18 L %d 52 Z" % (x - 4, x, x + 4), t, 3) + LN("M %d 52 L %d 24" % (x, x), INK, 2.5) + q
        return '<g transform="rotate(24 175 100)">%s%s</g>' % (q, RC(158, 70, 34, 10, t, 3, 3))
    if v == "totempack":
        g = RC(46, 40, 34, 110, m, 4) + RC(40, 30, 46, 30, t, 6) + CI(55, 44, 4, INK, 0) + CI(71, 44, 4, INK, 0)
        g += P("M 40 34 L 20 22 L 40 52 Z", t, 3) + P("M 86 34 L 106 22 L 86 52 Z", t, 3)
        return '<g transform="rotate(-14 63 120)">%s</g>' % g
    # vines: leafy vines climbing behind the body
    s = LN("M 40 226 Q 30 160 70 112 Q 96 90 128 98", m, 7) + mirror(LN("M 40 226 Q 30 160 70 112 Q 96 90 128 98", m, 7), 128)
    for x, y, a in ((44, 190, -30), (40, 150, 20), (60, 122, -40), (92, 100, 10)):
        leaf = EL(x, y, 13, 7, t, 3, a)
        s += leaf + mirror(leaf, 128)
    return s

def acc(o):
    v = o["variant"] or "bowtie"
    m, t = C(o.get("m"), "red"), C(o.get("t"), "gold")
    H = lambda body: "<g %s>%s</g>" % (HEAD_TF, body)
    if v == "bowtie":
        return P("M 128 140 L 104 128 L 104 154 Z", m, 4) + P("M 128 140 L 152 128 L 152 154 Z", m, 4) + RC(121, 133, 14, 14, t, 4, 3.5)
    if v == "bell":
        return P("M 92 128 Q 128 142 164 128 L 164 138 Q 128 152 92 138 Z", m, 3.5) + CI(128, 150, 10, t, 4) + LN("M 122 152 L 134 152", INK, 2.5) + CI(128, 156, 2, INK, 0)
    if v == "medal":
        return P("M 116 128 L 124 158 L 132 158 L 140 128 Z", m, 3.5) + CI(128, 166, 11, t, 4) + CI(128, 166, 5, light(t, .4), 2)
    if v == "scarf":
        return (P("M 84 124 Q 128 146 172 124 L 176 140 Q 128 162 80 140 Z", m, 4) + P("M 150 140 L 168 196 L 150 200 L 138 146 Z", m, 4)
                + LN("M 146 162 L 160 158 M 150 178 L 164 174", t, 4))
    if v == "bandolier":
        s = '<g clip-path="url(#bodyclip)">%s</g>' % P("M 66 118 L 84 112 L 196 204 L 180 214 Z", m, 4)
        for k in range(5): s += RC(92 + k * 18, 128 + k * 15, 10, 14, t, 2, 3)
        return s
    if v == "eyepatch":
        return H(LN("M 40 92 Q 128 70 216 92", INK, 4) + EL(98, 112, 17, 14, m, 4))
    if v == "monocle":
        return H('<circle cx="158" cy="112" r="19" fill="#d8f0ff" fill-opacity=".3" stroke="%s" stroke-width="5"/><circle cx="158" cy="112" r="19" fill="none" stroke="%s" stroke-width="2.5"/>' % (INK, t) + LN("M 172 126 Q 190 160 176 184", t, 2.5))
    if v == "mustache":
        return H(P("M 128 128 Q 110 120 98 132 Q 88 142 76 134 Q 86 150 104 142 Q 118 136 128 134 Q 138 136 152 142 Q 170 150 180 134 Q 168 142 158 132 Q 146 120 128 128 Z", m, 3.5))
    if v == "shades":
        return H(LN("M 70 104 L 186 104", INK, 5) + RC(74, 98, 46, 28, m, 8, 4) + RC(136, 98, 46, 28, m, 8, 4) + LN("M 82 106 L 92 106", "#ffffff", 3, .7) + LN("M 144 106 L 154 106", "#ffffff", 3, .7))
    if v == "flower":
        s = ""
        for j in range(6):
            a = j * math.pi / 3
            s += EL(182 + math.cos(a) * 11, 62 + math.sin(a) * 11, 9, 6, m, 3, math.degrees(a))
        return H(s + CI(182, 62, 7, t, 3))
    if v == "race_human":
        return CI(128, 156, 15, m, 4) + P("M 120 150 L 128 144 L 136 150 L 134 162 L 128 166 L 122 162 Z", t, 2.5)
    if v == "race_dwarf":
        beard = P("M 70 132 Q 76 176 104 190 L 114 214 L 128 196 L 142 214 L 152 190 Q 180 176 186 132 Q 160 150 128 150 Q 96 150 70 132 Z", m, 4)
        return H(beard + CI(114, 212, 5, t, 2.5) + CI(142, 212, 5, t, 2.5) + LN("M 100 160 Q 110 176 108 186 M 156 160 Q 146 176 148 186", darker(m, .7), 2.5))
    if v == "race_nightelf":
        ear = P("M 48 104 Q 6 70 -6 40 Q 26 60 54 86 Z", m, 4)
        return H(ear + mirror(ear, 128) + P("M 86 92 Q 98 84 112 90", t, 3) + mirror(P("M 86 92 Q 98 84 112 90", t, 3), 128))
    if v == "race_gnome":
        return H(P("M 44 84 Q 128 70 212 84 L 212 96 Q 128 82 44 96 Z", m, 4) + CI(100, 80, 18, m, 5) + CI(100, 80, 11, t, 3) + CI(156, 80, 18, m, 5) + CI(156, 80, 11, t, 3))
    if v == "race_orc":
        tusk = P("M 106 138 Q 100 120 92 116 Q 108 116 114 136 Z", m, 3)
        return H(tusk + mirror(tusk, 128))
    if v == "race_undead":
        return H(LN("M 62 120 L 82 138", m, 3) + "".join(LN("M %d %d L %d %d" % (64 + k * 6, 132 - k * 6 + 8, 72 + k * 6, 132 - k * 6 + 2), m, 2.5) for k in range(3))
                 + LN("M 170 70 L 188 96", m, 3) + "".join(LN("M %d %d L %d %d" % (168 + k * 6, 82 + k * 8, 180 + k * 6, 78 + k * 8), m, 2.5) for k in range(3)))
    if v == "race_tauren":
        horn = P("M 60 64 Q 14 58 10 20 Q 26 40 66 46 Z", m, 4)
        return H(horn + mirror(horn, 128) + '<circle cx="128" cy="134" r="9" fill="none" stroke="%s" stroke-width="7"/><circle cx="128" cy="134" r="9" fill="none" stroke="%s" stroke-width="3.5"/>' % (INK, t))
    if v == "race_troll":
        tusk = P("M 104 140 Q 92 112 80 104 Q 104 106 112 138 Z", m, 3)
        return H(tusk + mirror(tusk, 128) + P("M 104 40 Q 128 -10 152 40 Q 140 30 128 34 Q 116 30 104 40 Z", t, 4))
    if v == "race_skyborne":
        fe = P("M 60 70 Q 24 40 20 6 Q 44 30 70 56 Z", m, 3.5) + P("M 66 76 Q 30 64 14 40 Q 46 52 72 64 Z", t, 3)
        return H(fe + mirror(fe, 128))
    return ""

# ======================================================================== shoulders (1.6)
# One pauldron drawn on the cat's right shoulder (left of the picture) and mirrored onto the other,
# tucked under the head's lower corner and over the top of the body, cape and chest. In body space.
SH_C = (64, 131)  # centre of the left pauldron
def _sh_mail(cx, cy, col):
    """a short mail skirt hanging under a pauldron: scalloped rows of rings"""
    s = P("M %d %d Q %d %d %d %d Q %d %d %d %d L %d %d Z" % (cx - 36, cy + 2, cx - 40, cy + 28, cx - 22, cy + 32,
          cx + 2, cy + 34, cx + 26, cy + 20, cx + 28, cy, ), col, 4)
    for r, (x0, x1) in enumerate(((cx - 32, cx + 22), (cx - 32, cx + 16), (cx - 24, cx + 6))):
        y = cy + 12 + r * 7
        s += "".join(LN("M %.1f %.1f Q %.1f %.1f %.1f %.1f" % (x - 3, y, x, y + 5, x + 3, y), darker(col, .55), 1.8)
                     for x in range(x0 + (r % 2) * 3, x1, 7))
    return s

def _sh_dome(cx, cy, m, w=5, tall=0):
    return P("M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 30, cy + 8, cx + 26, cy - 22 - tall, cx - 4, cy - 22 - tall,
             cx - 34, cy - 20 - tall, cx - 36, cy + 12, cx - 4, cy + 22, cx + 30, cy + 8), m, w)

def _sh_zigband(cx, cy, col, n=7, amp=7):
    """a trim band along the dome's lower rim whose lower edge zigzags down (the dome-over-mail look)"""
    top = qpts((cx - 35, cy - 2), (cx - 6, cy + 10), (cx + 29, cy - 4), n * 2)
    low = qpts((cx - 35, cy + 6), (cx - 6, cy + 18), (cx + 29, cy + 4), n * 2)
    low = [(x, y + (amp if k % 2 else 0)) for k, (x, y) in enumerate(low)]
    return P("M " + " L ".join("%.1f %.1f" % q for q in top + low[::-1]) + " Z", col, 3.5)

def _sh_spiral(x, y, r, col, w=3.5):
    return LN("M %.1f %.1f A %.1f %.1f 0 1 1 %.1f %.1f A %.1f %.1f 0 1 1 %.1f %.1f A %.1f %.1f 0 0 1 %.1f %.1f" % (
        x + r, y, r, r, x - r * 0.2, y - r, r * 0.6, r * 0.6, x + r * 0.15, y - r * 0.15, r * 0.25, r * 0.25, x, y - r * 0.45), col, w)

def shoulder_one(o):
    """the left pauldron. variants: plate (domed), spiked, mail (layered lames), leather (spaulder
    with a strap), cloth (padded mantle roll), bone (skull cap), crystal, mantle (fur ruff).
    m = main, t = trim/rim, g = second colour, e = gem. Flags: spikes, gem, fur, rivets, horns, skull, glow=."""
    v = o["variant"] or "plate"
    m, t, g, e = C(o.get("m"), "steel"), C(o.get("t"), "gold"), C(o.get("g"), "leather"), C(o.get("e"), "ruby")
    f = o["flags"]; s = ""; cx, cy = SH_C
    if v in ("plate", "spiked"):
        dome = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 30, cy + 8, cx + 26, cy - 22, cx - 4, cy - 22,
            cx - 34, cy - 20, cx - 36, cy + 12, cx - 4, cy + 22, cx + 30, cy + 8)
        s += P(dome, m, 5)
        s += LN("M %d %d Q %d %d %d %d" % (cx - 34, cy + 6, cx - 6, cy + 18, cx + 28, cy + 4), t, 7) + LN("M %d %d Q %d %d %d %d" % (cx - 34, cy + 6, cx - 6, cy + 18, cx + 28, cy + 4), INK, 2)
        s += LN("M %d %d Q %d %d %d %d" % (cx - 22, cy - 8, cx - 8, cy - 16, cx + 8, cy - 13), light(m, .6), 4)
        if v == "spiked" or "spikes" in f:
            for k, (x, y, a) in enumerate(((cx - 22, cy - 14, -40), (cx - 2, cy - 20, -12), (cx + 18, cy - 16, 16))):
                ln = 26 if k == 1 else 20
                s = P("M %d %d L %.1f %.1f L %d %d Z" % (x - 6, y + 6, x + math.sin(math.radians(a)) * ln, y - math.cos(math.radians(a)) * ln, x + 6, y + 6), C(o.get("g"), "steel"), 3.5) + s
    elif v == "mail":
        for k in range(3):
            y = cy - 14 + k * 11; w = 30 - k * 2
            s += P("M %d %d Q %d %d %d %d L %d %d Q %d %d %d %d Z" % (cx - w - 4, y + 10, cx - 4, y - 14, cx + w - 2, y + 4, cx + w - 4, y + 12,
                   cx - 4, y - 4, cx - w - 2, y + 18), m if k % 2 == 0 else darker(m, .85), 4)
        s += LN("M %d %d Q %d %d %d %d" % (cx - 32, cy + 18, cx - 4, cy + 4, cx + 24, cy + 14), t, 5)
    elif v == "leather":
        cap = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 24, cy + 6, cx + 18, cy - 18, cx - 4, cy - 18, cx - 30, cy - 16, cx - 30, cy + 10, cx - 4, cy + 18, cx + 24, cy + 6)
        s += P(cap, m, 5) + LN("M %d %d Q %d %d %d %d" % (cx - 24, cy + 4, cx - 4, cy + 12, cx + 18, cy + 2), darker(m, .6), 2.5) + '<path d="M %d %d Q %d %d %d %d" fill="none" stroke="%s" stroke-width="2" stroke-dasharray="4 4"/>' % (cx - 22, cy - 6, cx - 4, cy - 12, cx + 14, cy - 8, light(m, .5))
        s += RC(cx - 6, cy - 4, 10, 26, t, 3, 3) + RC(cx - 7, cy + 8, 12, 8, C(o.get("e"), "brass"), 2, 2.5)
    elif v == "cloth":
        roll = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 30, cy + 2, cx + 22, cy - 18, cx - 2, cy - 16,
            cx - 28, cy - 14, cx - 32, cy + 6, cx - 30, cy + 22, cx - 10, cy + 20, cx + 10, cy + 16, cx + 30, cy + 2)
        s += P(roll, m, 5) + LN("M %d %d Q %d %d %d %d" % (cx - 30, cy + 14, cx - 2, cy + 18, cx + 26, cy + 4), t, 6) + LN("M %d %d Q %d %d %d %d" % (cx - 30, cy + 14, cx - 2, cy + 18, cx + 26, cy + 4), INK, 2)
        for x in (cx - 18, cx - 4, cx + 10): s += LN("M %d %d Q %d %d %d %d" % (x, cy - 12, x - 2, cy, x - 1, cy + 12), darker(m, .78), 2.5)
    elif v == "mantle":
        for k, (x, y, r) in enumerate(((cx + 18, cy - 4, 13), (cx + 2, cy - 10, 15), (cx - 16, cy - 6, 15), (cx - 26, cy + 8, 13), (cx - 8, cy + 10, 14), (cx + 12, cy + 8, 12))):
            s += CI(x, y, r, m if k % 2 == 0 else light(m, .2), 4)
    elif v == "bone":
        s += P("M %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 26, cy + 10, cx + 20, cy - 26, cx - 8, cy - 22, cx - 40, cy - 14, cx - 32, cy + 14), C(o.get("m"), "bone"), 5)
        s += EL(cx - 14, cy - 6, 7, 6, INK, 0) + EL(cx + 4, cy - 8, 7, 6, INK, 0) + P("M %d %d L %d %d L %d %d Z" % (cx - 6, cy + 2, cx - 4, cy - 4, cx - 2, cy + 2), INK, 0)
        for k in range(4): s += RC(cx - 20 + k * 9, cy + 6, 7, 8, C(o.get("m"), "bone"), 1.5, 2.5)
    elif v == "crystal":
        for x, y, w, h, a in ((cx - 18, cy - 4, 12, 34, -30), (cx - 2, cy - 8, 14, 40, -6), (cx + 14, cy - 2, 11, 30, 20)):
            s += '<g transform="rotate(%d %d %d)">%s</g>' % (a, x, y + 14, P("M %d %d L %d %d L %d %d L %d %d Z" % (x - w / 2, y + 14, x, y + 14 - h, x + w / 2, y + 14, x, y + 22), m, 3.5))
        s += P("M %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx - 30, cy + 14, cx - 4, cy - 2, cx + 26, cy + 10, cx - 2, cy + 24, cx - 30, cy + 14), t, 4)
    elif v == "domemail":
        # smooth dome over a mail skirt, its rim cut in a zigzag (inv_shoulder_10..16)
        s += _sh_mail(cx, cy + 4, C(o.get("k"), "iron"))
        s += _sh_dome(cx, cy, m) + LN("M %d %d Q %d %d %d %d" % (cx - 22, cy - 8, cx - 8, cy - 16, cx + 8, cy - 13), light(m, .55), 4)
        s += _sh_zigband(cx, cy + 2, t)
    elif v == "swirl":
        # mantle with a broad rim and a big scroll curl (inv_shoulder_02, 05)
        s += P("M %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx - 34, cy + 6, cx - 30, cy + 30, cx - 8, cy + 30, cx + 18, cy + 28, cx + 26, cy + 6), C(o.get("g"), "purple"), 4)
        s += _sh_dome(cx, cy - 2, m)
        s += LN("M %d %d Q %d %d %d %d" % (cx - 34, cy + 4, cx - 6, cy + 16, cx + 28, cy + 2), INK, 11) + LN("M %d %d Q %d %d %d %d" % (cx - 34, cy + 4, cx - 6, cy + 16, cx + 28, cy + 2), t, 6)
        s += LN("M %d %d Q %d %d %d %d" % (cx - 30, cy - 4, cx - 30, cy - 20, cx - 10, cy - 22), INK, 9) + LN("M %d %d Q %d %d %d %d" % (cx - 30, cy - 4, cx - 30, cy - 20, cx - 10, cy - 22), t, 4.5)
        s += _sh_spiral(cx - 2, cy - 6, 9, INK, 8) + _sh_spiral(cx - 2, cy - 6, 9, t, 4)
    elif v == "drape":
        # layered cloth mantle: a top flap and a lower flap, both with a trimmed edge (inv_shoulder_09)
        low = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx - 36, cy + 2, cx - 38, cy + 30, cx - 16, cy + 32, cx + 6, cy + 32, cx + 24, cy + 20, cx + 30, cy + 2, cx + 28, cy)
        s += P(low, darker(m, .82), 4) + LN("M %d %d Q %d %d %d %d" % (cx - 34, cy + 26, cx - 6, cy + 34, cx + 22, cy + 20), t, 4.5)
        top = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 30, cy + 4, cx + 24, cy - 22, cx - 4, cy - 20, cx - 32, cy - 18, cx - 36, cy + 8, cx - 6, cy + 20, cx + 30, cy + 4)
        s += P(top, m, 5) + LN("M %d %d Q %d %d %d %d" % (cx - 34, cy + 6, cx - 6, cy + 18, cx + 28, cy + 3), INK, 10) + LN("M %d %d Q %d %d %d %d" % (cx - 34, cy + 6, cx - 6, cy + 18, cx + 28, cy + 3), t, 5)
        s += LN("M %d %d Q %d %d %d %d" % (cx - 22, cy - 8, cx - 8, cy - 14, cx + 8, cy - 11), light(m, .6), 4)
    elif v == "ridge":
        # swept pauldron with a tall arched fin rising from its outer edge (inv_shoulder_23..25)
        s += P("M %d %d Q %d %d %d %d Q %d %d %d %d L %d %d Z" % (cx - 32, cy + 6, cx - 32, cy + 30, cx - 8, cy + 30, cx + 18, cy + 28, cx + 24, cy + 6, cx, cy + 2), C(o.get("g"), darker(m, .75)), 4)
        fin = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx - 34, cy + 8, cx - 40, cy - 30, cx - 14, cy - 40, cx + 2, cy - 30, cx + 4, cy - 4, cx - 14, cy + 4, cx - 34, cy + 8)
        s += P(fin, t, 5) + P("M %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx - 26, cy + 2, cx - 30, cy - 26, cx - 13, cy - 31, cx - 4, cy - 22, cx - 4, cy - 2), darker(m, .7), 2.5)
        s += P("M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 28, cy + 8, cx + 24, cy - 12, cx + 2, cy - 12, cx - 24, cy - 8, cx - 30, cy + 10, cx - 4, cy + 20, cx + 28, cy + 8), m, 5)
        s += LN("M %d %d Q %d %d %d %d" % (cx - 30, cy + 8, cx - 4, cy + 18, cx + 26, cy + 6), INK, 10) + LN("M %d %d Q %d %d %d %d" % (cx - 30, cy + 8, cx - 4, cy + 18, cx + 26, cy + 6), t, 5)
        s += LN("M %d %d Q %d %d %d %d" % (cx - 16, cy - 2, cx - 2, cy - 7, cx + 14, cy - 4), light(m, .5), 3.5)
    elif v == "wedge":
        # angular plate with a thick riveted rim along the outer and lower edge (inv_shoulder_26..28)
        s += P("M %d %d L %d %d L %d %d L %d %d Z" % (cx - 30, cy + 10, cx - 20, cy + 30, cx + 18, cy + 22, cx + 24, cy + 4), darker(m, .7), 4)
        s += P("M %d %d L %d %d Q %d %d %d %d L %d %d L %d %d Z" % (cx - 38, cy + 4, cx - 24, cy - 20, cx, cy - 26, cx + 24, cy - 14, cx + 30, cy + 4, cx - 4, cy + 20), m, 5)
        s += LN("M %d %d L %d %d L %d %d L %d %d" % (cx - 24, cy - 20, cx - 38, cy + 4, cx - 4, cy + 20, cx + 30, cy + 4), INK, 13) + LN("M %d %d L %d %d L %d %d L %d %d" % (cx - 24, cy - 20, cx - 38, cy + 4, cx - 4, cy + 20, cx + 30, cy + 4), t, 8)
        s += LN("M %d %d Q %d %d %d %d" % (cx - 16, cy - 8, cx, cy - 18, cx + 14, cy - 10), light(m, .55), 4)
        for x, y in ((cx - 30, cy + 3), (cx - 6, cy + 16), (cx + 22, cy + 5)): s += CI(x, y, 2.6, light(t, .35), 1.8)
    elif v == "lames":
        # stacked plates, each with a bright edge, and a strap with a buckle (inv_shoulder_29, 30, 71)
        for k in range(3)[::-1]:
            y = cy - 16 + k * 12; w = 32 - k * 3
            band = "M %d %d Q %d %d %d %d L %d %d Q %d %d %d %d Z" % (cx - w - 2, y + 12, cx - 4, y - 16, cx + w - 4, y + 6, cx + w - 6, y + 16, cx - 4, y, cx - w, y + 22)
            s += P(band, m if k != 1 else darker(m, .88), 4) + LN("M %d %d Q %d %d %d %d" % (cx - w, y + 20, cx - 4, y + 1, cx + w - 6, y + 14), t, 4)
        s += LN("M %d %d Q %d %d %d %d" % (cx - 18, cy - 14, cx - 6, cy - 22, cx + 10, cy - 18), light(m, .55), 3.5)
        s += RC(cx + 8, cy - 6, 9, 30, C(o.get("g"), "darkleather"), 2, 3) + RC(cx + 6, cy + 6, 13, 9, t, 2, 2.5)
    elif v == "quilted":
        # leather dome with diamond quilting and a rivet at each crossing (inv_shoulder_06)
        s += _sh_dome(cx, cy, m)
        lat = "".join(LN("M %d %d L %d %d" % (cx - 26 + k * 12, cy - 18, cx - 6 + k * 12, cy + 16), darker(m, .62), 2.2)
                      + LN("M %d %d L %d %d" % (cx + 14 + k * 12, cy - 18, cx - 6 + k * 12, cy + 16), darker(m, .62), 2.2) for k in range(-3, 4))
        dome = "M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 30, cy + 8, cx + 26, cy - 22, cx - 4, cy - 22, cx - 34, cy - 20, cx - 36, cy + 12, cx - 4, cy + 22, cx + 30, cy + 8)
        s += '<clipPath id="shquilt"><path d="%s"/></clipPath><g clip-path="url(#shquilt)">%s</g>' % (dome, lat) + P(dome, "none", 5)
        for x, y in ((cx - 16, cy - 8), (cx + 8, cy - 8), (cx - 4, cy + 4), (cx - 22, cy + 6), (cx + 16, cy + 2)): s += CI(x, y, 2.6, light(t, .3), 1.8)
    elif v == "banded":
        # leather dome with a riveted band across it (inv_shoulder_07, 08, 74)
        s += _sh_dome(cx, cy, m) + LN("M %d %d Q %d %d %d %d" % (cx - 22, cy - 10, cx - 8, cy - 17, cx + 8, cy - 14), light(m, .5), 4)
        s += LN("M %d %d Q %d %d %d %d" % (cx - 35, cy + 2, cx - 6, cy + 10, cx + 29, cy - 2), INK, 13) + LN("M %d %d Q %d %d %d %d" % (cx - 35, cy + 2, cx - 6, cy + 10, cx + 29, cy - 2), t, 8)
        for x, y in qpts((cx - 30, cy + 3), (cx - 6, cy + 10), (cx + 24, cy - 1), 4): s += CI(x, y, 2.6, light(t, .45), 1.8)
    elif v == "orbs":
        # rough mantle with dripping ends and two ringed orbs (inv_shoulder_17..19)
        drip = ("M %d %d Q %d %d %d %d Q %d %d %d %d L %d %d L %d %d L %d %d L %d %d L %d %d L %d %d L %d %d L %d %d Q %d %d %d %d Z"
                % (cx + 30, cy + 6, cx + 26, cy - 22, cx - 4, cy - 22, cx - 34, cy - 20, cx - 36, cy + 8, cx - 34, cy + 26, cx - 26, cy + 14,
                   cx - 18, cy + 28, cx - 10, cy + 16, cx - 2, cy + 26, cx + 6, cy + 14, cx + 14, cy + 22, cx + 20, cy + 10, cx + 28, cy + 12, cx + 30, cy + 6))
        s += P(drip, m, 5)
        for k in range(5): s += LN("M %d %d L %d %d" % (cx - 26 + k * 10, cy - 12 + (k % 2) * 3, cx - 20 + k * 10, cy - 6 + (k % 2) * 3), light(m, .4), 2)
        for x, y, r in ((cx - 18, cy - 4, 8), (cx + 10, cy - 8, 7)):
            s += CI(x, y, r + 3, t, 3.5) + GEM(x, y, r - 1.5, C(o.get("e"), "black"))
    elif v == "ornate":
        # rounded plate over mail with gold scrollwork (inv_shoulder_20..22, 78)
        s += _sh_mail(cx, cy + 4, C(o.get("k"), "iron"))
        s += _sh_dome(cx, cy - 2, m) + LN("M %d %d Q %d %d %d %d" % (cx - 22, cy - 12, cx - 8, cy - 19, cx + 8, cy - 16), light(m, .55), 4)
        s += LN("M %d %d Q %d %d %d %d" % (cx - 35, cy + 6, cx - 6, cy + 16, cx + 29, cy + 2), INK, 12) + LN("M %d %d Q %d %d %d %d" % (cx - 35, cy + 6, cx - 6, cy + 16, cx + 29, cy + 2), t, 7)
        sc = "M %d %d Q %d %d %d %d Q %d %d %d %d" % (cx - 24, cy + 8, cx - 22, cy - 4, cx - 8, cy - 4, cx + 8, cy - 4, cx + 10, cy - 14)
        s += LN(sc, INK, 9) + LN(sc, t, 4.5) + _sh_spiral(cx + 12, cy - 15, 5, INK, 7) + _sh_spiral(cx + 12, cy - 15, 5, t, 3.5)
    elif v == "flare":
        # swept, flame-like blades fanning out and up (inv_shoulder_35)
        s += _sh_dome(cx, cy + 2, C(o.get("g"), "maroon"))
        for k, (dx, dy, col) in enumerate(((-30, -14, t), (-18, -26, m), (-2, -30, light(m, .35)))):
            s += P("M %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx + 26, cy + 6 - k * 4, cx + dx + 20, cy + dy + 4, cx + dx - 10, cy + dy - 6,
                   cx + dx + 4, cy + dy + 14, cx - 20 + k * 6, cy + 14 - k * 3), col, 4)
        s += LN("M %d %d Q %d %d %d %d" % (cx - 32, cy + 10, cx - 4, cy + 22, cx + 28, cy + 8), INK, 11) + LN("M %d %d Q %d %d %d %d" % (cx - 32, cy + 10, cx - 4, cy + 22, cx + 28, cy + 8), C(o.get("e"), "gold"), 6)
    if "zigzag" in f:
        z = qpts((cx - 28, cy - 6), (cx - 6, cy - 14), (cx + 20, cy - 8), 6)
        s += LN("M " + " L ".join("%.1f %.1f" % (x, y + (5 if k % 2 else 0)) for k, (x, y) in enumerate(z)), t, 3.5)
        z = qpts((cx - 30, cy + 14), (cx - 6, cy + 24), (cx + 22, cy + 10), 6)
        s += LN("M " + " L ".join("%.1f %.1f" % (x, y - (5 if k % 2 else 0)) for k, (x, y) in enumerate(z)), t, 3)
    if "teeth" in f:
        tt = qpts((cx - 40, cy + 12), (cx - 34, cy - 34), (cx + 30, cy - 18), 9)
        s = "".join(P("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" % (x - 5, y + 4, x - 4 - (cx - x) * 0.12, y - 9, x + 5, y + 2), C(o.get("g"), "darkleather"), 3) for x, y in tt) + s
    if "horn" in f:
        # one horn spike on the outer half, where hoods and helms leave it showing
        s += P("M %d %d Q %d %d %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx - 32, cy - 12, cx - 40, cy - 34, cx - 30, cy - 50, cx - 26, cy - 36,
               cx - 12, cy - 24, cx - 18, cy - 14, cx - 32, cy - 12), C(o.get("h"), "brass"), 4)
        s += LN("M %d %d Q %d %d %d %d" % (cx - 28, cy - 18, cx - 32, cy - 32, cx - 29, cy - 42), light(C(o.get("h"), "brass"), .5), 2.5)
    if "claws" in f:
        for x, y, a in ((cx - 30, cy - 6, -50), (cx - 18, cy - 18, -24), (cx + 2, cy - 22, 2)):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            tip = (x + sa * 22, y - ca * 22); mid = (x + sa * 15 + ca * 7, y - ca * 15 + sa * 7)
            s += P("M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" % (x - ca * 7, y - sa * 7, mid[0], mid[1], tip[0], tip[1], mid[0] - ca * 6, mid[1] - sa * 6, x + ca * 7, y + sa * 7), C(o.get("g"), "purple"), 3.5)
    if "runes" in f:
        for k, (x, y) in enumerate(((cx - 20, cy - 4), (cx - 6, cy - 9), (cx + 8, cy - 6), (cx - 13, cy + 7), (cx + 2, cy + 4))):
            s += LN(("M %d %d L %d %d L %d %d", "M %d %d L %d %d M %d %d L %d %d", "M %d %d L %d %d L %d %d")[k % 3] %
                    ((x - 3, y - 4, x, y + 4, x + 3, y - 4), (x - 3, y, x + 3, y, x, y - 4, x, y + 4), (x - 3, y + 3, x - 3, y - 3, x + 3, y + 3))[k % 3],
                    C(o.get("e"), "cyan"), 2.4)
    if "bolts" in f:
        for x, y, sg in ((cx - 30, cy - 18, 1), (cx + 10, cy - 30, -1)):
            s += LN("M %d %d L %d %d L %d %d L %d %d" % (x, y, x + 6 * sg, y + 8, x, y + 10, x + 7 * sg, y + 20), INK, 6) + LN("M %d %d L %d %d L %d %d L %d %d" % (x, y, x + 6 * sg, y + 8, x, y + 10, x + 7 * sg, y + 20), C(o.get("e"), "storm"), 3)
    if "rivets" in f:
        for x, y in ((cx - 24, cy + 8), (cx - 6, cy + 12), (cx + 14, cy + 8)): s += CI(x, y, 3, light(t, .3), 2)
    if "gem" in f: s += GEM(cx - 4, cy - 4, 6.5, e)
    if "fur" in f:
        for x, y in ((cx + 22, cy + 10), (cx + 8, cy + 18), (cx - 8, cy + 20), (cx - 24, cy + 16), (cx - 36, cy + 6)): s += CI(x, y, 7.5, C(o.get("g"), "cream"), 3)
    if "horns" in f:
        s = P("M %d %d Q %d %d %d %d Q %d %d %d %d Z" % (cx - 18, cy - 10, cx - 44, cy - 20, cx - 40, cy - 46, cx - 32, cy - 28, cx - 10, cy - 18), C(o.get("g"), "bone"), 4) + s
    if "skull" in f:
        s += P("M %d %d Q %d %d %d %d Q %d %d %d %d L %d %d L %d %d Z" % (cx - 12, cy + 4, cx - 13, cy - 14, cx - 2, cy - 14, cx + 9, cy - 14, cx + 8, cy + 4, cx + 4, cy + 8, cx - 8, cy + 8), "#f6f6f2", 3) + CI(cx - 6, cy - 4, 2.6, INK, 0) + CI(cx + 2, cy - 4, 2.6, INK, 0)
    if "glow" in o: s = GLOW(s, C(o["glow"], "fire")) + s
    return s

def shoulder(o):
    one = shoulder_one(o)
    return one + mirror(one, 128)

CLIPS = ('<defs><clipPath id="bodyclip"><path d="M 78 112 Q 54 160 58 214 L 198 214 Q 202 160 178 112 Z"/></clipPath>'
         '<clipPath id="chestclip"><path d="%s"/></clipPath></defs>' % BODY_OUT)

FAMILIES = {"sword", "axe", "mace", "dagger", "staff", "polearm", "fist", "shield", "held", "head", "chest", "belt", "neck", "ring",
            "bow", "rifle", "wand", "totem", "back", "acc", "shoulder"}
def render(spec, kind, key=""):
    """Returns {layer_name: svg_body} for one item spec. kind: head chest belt neck ring weapon1 weapon2 shield held."""
    o = parse(spec); o["_key"] = key
    if kind == "head": return {"": head(o)}
    if kind == "chest": return {"": chest(o)}
    if kind == "belt": return {"": belt(o)}
    if kind == "neck": return {"": neck(o)}
    if kind == "ring": return {"_down": ring(o, "down"), "_up": ring(o, "up")}
    if kind == "shield": return {"": shield(o)}
    if kind == "held": return {"": held(o)}
    if kind == "back": return {"": back(o)}
    if kind == "acc": return {"": acc(o)}
    if kind == "shoulder": return {"": shoulder(o)}
    return {"": weapon(o, kind == "weapon2")}

# everything sits a little lower on the canvas so tall hats fit above the head
DROP = 16
def svg(body, cel=True):
    if cel: body = '<g filter="url(#cel)">%s</g>' % body
    body = '<g transform="translate(0 %d)">%s</g>' % (DROP, body)
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">%s%s%s</svg>' % (DEFS, CLIPS, body)
