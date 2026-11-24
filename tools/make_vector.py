"""Flat 2D vector cat (kawaii sticker style): thick brown outlines, flat fills, cream muzzle.

Writes one SVG per layer, renders them with tools/render_svg.js (Playwright/Chromium), and
composes a preview sheet. Layers ending in _t are greyscale and get tinted in game
(fur colour, gear colour); every other layer keeps its own colours. Outlines live in
untinted layers so they stay dark brown whatever the fur colour.

usage: python3 tools/make_vector.py <out_dir> [preview.png]
"""
import math, os, subprocess, sys
from PIL import Image, ImageChops, ImageDraw

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
INK, W = "#3b2620", 6
PINK, BLUSH, CREAM = "#f3a3a0", "#f6a5a5", "#fff7ec"
L = {}

HEAD = "M 58 28 L 94 56 Q 128 49 162 56 L 198 28 Q 212 70 211 106 Q 210 166 128 168 Q 46 166 45 106 Q 44 70 58 28 Z"
BODY = "M 78 112 Q 54 160 58 214 L 198 214 Q 202 160 178 112 Z"
# the head is drawn in its own 256 space and shrunk onto the body; head gear uses the same space
HEAD_TF = 'transform="translate(128 16) scale(0.8) translate(-128 -28)"'
def H(s): return "<g %s>%s</g>" % (HEAD_TF, s)
MIRROR = 'transform="translate(256,0) scale(-1,1)"'
def both(s): return s + "<g %s>%s</g>" % (MIRROR, s)
def line(p, w=W): return '<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"/>' % (p, INK, w)
def fill(p, c, w=0): return '<path d="%s" fill="%s"%s/>' % (p, c, (' stroke="%s" stroke-width="%s" stroke-linejoin="round"' % (INK, w)) if w else "")
CLIPS = '<defs><clipPath id="head"><path d="%s"/></clipPath><clipPath id="body"><path d="%s"/></clipPath></defs>' % (HEAD, BODY)

# ---- cat
L["desk"] = ('<rect x="-10" y="206" width="276" height="60" fill="#d9a477" stroke="%s" stroke-width="%d"/>'
             '<rect x="-10" y="206" width="276" height="12" fill="#e8b88a" stroke="%s" stroke-width="%d"/>') % (INK, W, INK, W)
L["body_t"] = fill(BODY, "#e8e8e8")
L["body_marks_t"] = '<g clip-path="url(#body)">%s</g>' % both('<rect x="50" y="150" width="26" height="8" rx="4" fill="#a8a8a8"/><rect x="50" y="166" width="22" height="8" rx="4" fill="#a8a8a8"/><rect x="50" y="182" width="18" height="8" rx="4" fill="#a8a8a8"/>')
L["belly"] = '<g clip-path="url(#body)"><ellipse cx="128" cy="186" rx="38" ry="58" fill="%s"/></g>' % CREAM
L["body_line"] = line(BODY)
L["head_t"] = H(fill(HEAD, "#e8e8e8"))
L["head_marks_t"] = H('<g clip-path="url(#head)">%s%s</g>' % (
    '<rect x="123" y="52" width="10" height="24" rx="5" fill="#a8a8a8"/>',
    both('<rect x="104" y="57" width="9" height="18" rx="4.5" fill="#a8a8a8"/>'
         '<rect x="38" y="98" width="22" height="7" rx="3.5" fill="#a8a8a8"/><rect x="38" y="111" width="17" height="7" rx="3.5" fill="#a8a8a8"/>')))
def eyes(kind):
    if kind == "blink":
        return both(line("M 88 113 Q 98 118 108 113", 4))
    if kind == "happy":
        return both(line("M 86 116 Q 98 102 110 116", 4.5))
    if kind == "focus":
        return both('<circle cx="98" cy="114" r="9" fill="%s"/><circle cx="95" cy="110.5" r="3" fill="#fff"/>' % INK + line("M 84 100 L 110 106", 4))
    if kind == "sparkle":
        star = "M 98 98 L 102 108 L 113 112 L 102 116 L 98 126 L 94 116 L 83 112 L 94 108 Z"
        return both(fill(star, "#ffd23c", 2.5) + '<circle cx="98" cy="112" r="2.4" fill="#fff"/>')
    return both('<circle cx="98" cy="112" r="10.5" fill="%s"/><circle cx="94.5" cy="107.5" r="3.8" fill="#fff"/><circle cx="101" cy="116" r="1.7" fill="#fff"/>' % INK)
def mouth(kind):
    if kind in ("happy", "sparkle"):
        return (fill("M 112 133 Q 128 140 144 133 Q 142 158 128 159 Q 114 158 112 133 Z", "#f0706a", 3.5)
                + fill("M 117 135 L 120 142 L 123 136 Z", "#fff", 0) + fill("M 133 136 L 136 142 L 139 135 Z", "#fff", 0))
    if kind == "focus":
        return line("M 118 138 Q 128 134 138 138", 3.5)
    return line("M 114 134 Q 121 142 128 134 Q 135 142 142 134", 3.5)
FACE_BASE = ('<g clip-path="url(#head)"><ellipse cx="128" cy="154" rx="60" ry="30" fill="%s"/></g>' % CREAM
    + both(fill("M 66 42 L 88 60 Q 75 64 70 78 Z", PINK)
           + fill("M 70 74 Q 74 62 80 66 Q 78 56 86 60 Q 84 68 90 64 Q 86 76 74 80 Z", "#ffffff", 0)   # ear fluff
           + '<ellipse cx="78" cy="132" rx="12" ry="6.5" fill="%s" opacity=".9"/>' % BLUSH
           + line("M 46 118 L 18 112", 3) + line("M 46 127 L 16 131", 3))
    + fill("M 121 124 Q 128 121 135 124 Q 131 131 128 131 Q 125 131 121 124 Z", "#f08f8f", 2))
FACES = ("normal", "blink", "happy", "sparkle", "focus")
for k in FACES:
    L["face_" + k] = H(FACE_BASE + eyes(k) + mouth(k) + line(HEAD))

# ---- (1.6.8) tapping faces: tap1 (a little keen) to tap10 (legendary), shown by how fast you tap
SWEAT, STEAM = "#8fd3ff", "#ffffff"
def brows(tilt, y=98, w=4):
    # tilt > 0: angry (inner ends lower)
    return both(line("M 84 %.1f L 110 %.1f" % (y - tilt, y + tilt), w))
def round_eyes(r=10.5, extra_shine=False):
    s = '<circle cx="98" cy="112" r="%.1f" fill="%s"/><circle cx="94" cy="107" r="%.1f" fill="#fff"/><circle cx="101.5" cy="116.5" r="1.9" fill="#fff"/>' % (r, INK, r * 0.38)
    if extra_shine: s += '<circle cx="103" cy="106" r="1.6" fill="#fff"/>'
    return both(s)
def narrow_eyes():
    # half-closed, intense: a flat lid over a dark eye
    return both(fill("M 87 112 Q 98 104 109 112 Q 109 122 98 122 Q 87 122 87 112 Z", INK) + '<circle cx="95" cy="114" r="2.4" fill="#fff"/>')
def star_eyes(c="#ffd23c", s=1.25):
    star = "M 0 -14 L 4.5 -4.5 L 14 0 L 4.5 4.5 L 0 14 L -4.5 4.5 L -14 0 L -4.5 -4.5 Z"
    return both('<g transform="translate(98 112) scale(%.2f)">%s</g>' % (s, fill(star, c, 2.2)) + '<circle cx="98" cy="112" r="2.6" fill="#fff"/>')
def flame_eyes():
    fl = ("M 98 124 Q 86 122 88 110 Q 90 102 96 96 Q 96 104 100 106 Q 102 98 108 94 Q 112 106 110 114 Q 108 124 98 124 Z")
    inner = "M 98 122 Q 92 120 93 113 Q 95 108 98 105 Q 99 110 102 111 Q 105 116 103 120 Q 101 122 98 122 Z"
    return both(fill(fl, "#ff7a1a", 2.5) + fill(inner, "#ffe14a", 0))
def swirl_eyes():
    g = '<circle cx="98" cy="112" r="15" fill="#c07bff" opacity=".45"/><circle cx="98" cy="112" r="11" fill="#7b2cff" stroke="%s" stroke-width="2.5"/>' % INK
    sp = line("M 98 112 Q 98 106 103 108 Q 107 112 102 117 Q 96 120 92 114 Q 90 106 98 103", 2.4).replace(INK, "#f2e6ff")
    return both(g + sp)
def open_mouth(big=False, tongue=False):
    if big:
        m = fill("M 108 132 Q 128 140 148 132 Q 147 166 128 168 Q 109 166 108 132 Z", "#d9534f", 3.5)
    else:
        m = fill("M 112 133 Q 128 140 144 133 Q 142 158 128 159 Q 114 158 112 133 Z", "#f0706a", 3.5)
    if tongue:
        m += fill("M 118 %d Q 128 %d 138 %d Q 136 %d 128 %d Q 120 %d 118 %d Z" % ((158, 150, 158, 166, 166, 166, 158) if big else (152, 146, 152, 158, 158, 158, 152)), "#ff9aa6", 0)
    return m
def grin_teeth(w=18, grit=False):
    x0, x1 = 128 - w, 128 + w
    m = fill("M %d 133 Q 128 %d %d 133 Q %d 150 128 151 Q %d 150 %d 133 Z" % (x0, 138, x1, x1 - 2, x0 + 2, x0), "#fff", 3.2)
    if grit:
        for x in range(x0 + 8, x1 - 2, 7): m += line("M %d 135 L %d 149" % (x, x), 2)
        m += line("M %d 142 L %d 142" % (x0 + 2, x1 - 2), 2)
    return m
def sweat(x, y, s=1.0):
    d = "M 0 -12 Q 8 0 6 6 Q 3 11 0 11 Q -3 11 -6 6 Q -8 0 0 -12 Z"
    return '<g transform="translate(%.1f %.1f) scale(%.2f)">%s<circle cx="-1.5" cy="4" r="2" fill="#fff"/></g>' % (x, y, s, fill(d, SWEAT, 2.5))
def steam(x, y):
    return ''.join('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" stroke-width="2.5" opacity=".95"/>' % (x + dx, y + dy, r, STEAM, INK)
                   for dx, dy, r in ((0, 0, 9), (10, -8, 7), (-9, -9, 6)))
def bolt(x, y, flip=False):
    d = "M 0 0 L 10 -2 L 4 12 L 14 10 L -2 34 L 2 18 L -8 20 Z"
    tf = 'translate(%.1f %.1f)%s' % (x, y, ' scale(-1 1)' if flip else '')
    return '<g transform="%s">%s</g>' % (tf, fill(d, "#ffe14a", 2.5))
def blush(strength):
    return both('<ellipse cx="78" cy="132" rx="13" ry="7" fill="#ff7c8a" opacity="%.2f"/>' % strength)

TAP_FACES = {
    # level: eyes, mouth, overlays drawn above the head (sweat, steam, sparks), in the head's space
    1: (round_eyes(10.5), line("M 114 134 Q 121 143 128 135 Q 135 143 142 134", 3.5), ""),
    2: (round_eyes(11.5, True), open_mouth(), blush(.35)),
    3: (both('<circle cx="98" cy="114" r="9" fill="%s"/><circle cx="95" cy="110.5" r="3" fill="#fff"/>' % INK) + brows(2), line("M 116 137 Q 128 142 140 137", 3.5), ""),
    4: (both('<circle cx="98" cy="114" r="9" fill="%s"/><circle cx="95" cy="110.5" r="3" fill="#fff"/>' % INK) + brows(5), grin_teeth(14), ""),
    5: (round_eyes(12.5, True), open_mouth(tongue=True), blush(.5)),
    6: (both('<circle cx="98" cy="114" r="9.5" fill="%s"/><circle cx="95" cy="110.5" r="3" fill="#fff"/>' % INK) + brows(6), open_mouth(), sweat(196, 74)),
    7: (narrow_eyes() + brows(8, 96, 5), grin_teeth(18, grit=True), sweat(198, 72) + sweat(60, 80, 0.8)),
    8: (star_eyes(), open_mouth(big=True, tongue=True), blush(.6) + sweat(200, 70, 0.9)),
    9: (flame_eyes() + brows(7, 94, 5), grin_teeth(20), steam(70, 22) + steam(186, 22)),
    10: (swirl_eyes() + brows(9, 93, 5), open_mouth(big=True, tongue=True), bolt(30, 50) + bolt(226, 50, True) + steam(128, 6) + blush(.6)),
}
def flush(lv):
    # mad cheeks: a red flush that grows with the tapping level (none at the first two)
    a = max(0, lv - 2) * 0.09
    if a <= 0: return ""
    return both('<ellipse cx="80" cy="131" rx="%.1f" ry="%.1f" fill="#ff2d2d" opacity="%.2f"/>' % (13 + lv * 0.5, 7 + lv * 0.3, a))
for lv, (e, m, extra) in TAP_FACES.items():
    extra = extra.replace(blush(.35), "").replace(blush(.5), "").replace(blush(.6), "")
    L["face_tap%d" % lv] = H(FACE_BASE + flush(lv) + e + m + line(HEAD) + extra)

# ---- (1.6.8) petting faces: pet1 (curious) to pet10 (pure love), shown as a petting streak grows
HEART = "M 0 10 C -14 0 -12 -12 -5 -12 C -2 -12 0 -9 0 -7 C 0 -9 2 -12 5 -12 C 12 -12 14 0 0 10 Z"
def heart(x, y, s=1.0, c="#ff6f91", w=2.2, rot=0):
    return '<g transform="translate(%.1f %.1f) rotate(%d) scale(%.2f)">%s</g>' % (x, y, rot, s, fill(HEART, c, w))
def heart_eyes(s=1.15, glow=False):
    g = '<circle cx="98" cy="112" r="16" fill="#ffb3c8" opacity=".5"/>' if glow else ""
    return both(g + heart(98, 112, s) + '<circle cx="94" cy="106" r="2.2" fill="#fff"/>')
def joy_eyes():      # ^ ^ (the happy face's eyes)
    return both(line("M 86 116 Q 98 102 110 116", 4.5))
def cosy_eyes():     # closed, relaxed: gentle downward curves
    return both(line("M 86 111 Q 98 121 110 111", 4.5))
CAT_MOUTH = line("M 114 134 Q 121 142 128 134 Q 135 142 142 134", 3.5)
SMALL_W = line("M 118 135 Q 123 140 128 135 Q 133 140 138 135", 3)
def purr_lines():
    return both(line("M 30 128 Q 24 136 30 144", 3) + line("M 22 124 Q 14 136 22 148", 3))
def sparkle_at(x, y, s=1.0):
    st = "M 0 -9 L 2.5 -2.5 L 9 0 L 2.5 2.5 L 0 9 L -2.5 2.5 L -9 0 L -2.5 -2.5 Z"
    return '<g transform="translate(%.1f %.1f) scale(%.2f)">%s</g>' % (x, y, s, fill(st, "#fff3a8", 1.8))

PET_FACES = {
    1: (round_eyes(10.5), CAT_MOUTH, blush(.35)),
    2: (joy_eyes(), CAT_MOUTH, blush(.4)),
    3: (joy_eyes(), SMALL_W, blush(.8)),
    4: (cosy_eyes(), open_mouth(), blush(.6)),
    5: (cosy_eyes(), CAT_MOUTH, blush(.6) + purr_lines()),
    6: (heart_eyes(), CAT_MOUTH, blush(.7)),
    7: (cosy_eyes(), open_mouth(), blush(.8) + heart(190, 30, 0.9, rot=15) + purr_lines()),
    8: (heart_eyes(1.3), open_mouth(tongue=True), blush(.8) + heart(66, 26, 0.8, rot=-15) + heart(192, 24, 0.9, rot=15)),
    9: (joy_eyes(), open_mouth(tongue=True), blush(.95) + heart(60, 30, 0.8, rot=-20) + heart(128, 6, 1.0) + heart(196, 30, 0.8, rot=20) + sparkle_at(30, 70) + sparkle_at(226, 70)),
    10: (heart_eyes(1.45, glow=True), open_mouth(big=True, tongue=True), blush(1.0) + purr_lines()
         + "".join(heart(128 + 92 * math.cos(a), 62 - 66 * math.sin(a), 0.75, rot=int(math.degrees(math.pi / 2 - a)) // 3)
                   for a in [math.pi * (0.15 + 0.7 * k / 4) for k in range(5)]) + sparkle_at(26, 60) + sparkle_at(230, 60)),
}
def kawaii_blush(lv):
    # cute cheeks: a soft pink blush that deepens, with little blush lines from the third face on
    a = 0.25 + lv * 0.065
    s = '<ellipse cx="79" cy="131" rx="%.1f" ry="%.1f" fill="#ff8fb1" opacity="%.2f"/>' % (12.5 + lv * 0.35, 6.8 + lv * 0.2, min(.95, a))
    if lv >= 3:
        n = 2 if lv < 6 else 3
        for k in range(n):
            x = 72 + k * 6
            s += '<path d="M %.1f 135 L %.1f 127" fill="none" stroke="#e0507a" stroke-width="2.2" stroke-linecap="round"/>' % (x, x + 4)
    return both(s)
for lv, (e, m, extra) in PET_FACES.items():
    for k in (.35, .4, .6, .7, .8, .95, 1.0):
        extra = extra.replace(blush(k), "")
    L["face_pet%d" % lv] = H(FACE_BASE + kawaii_blush(lv) + e + m + line(HEAD) + extra)
L["face"] = L["face_normal"]

# paws: down = resting on the desk, up = raised showing toe beans
PAW_DOWN = "M 66 216 Q 64 192 90 191 Q 116 192 114 216 Z"
PAW_UP = "M 62 206 Q 40 160 44 128 Q 46 104 66 104 Q 88 106 86 130 Q 84 166 100 206 Z"
for side, tf in (("L", ""), ("R", MIRROR)):
    g = lambda s: "<g %s>%s</g>" % (tf, s) if tf else s
    L["paw_%s_down_t" % side] = g(fill(PAW_DOWN, "#e8e8e8"))
    L["paw_%s_down" % side] = g(line(PAW_DOWN) + line("M 83 203 L 83 213", 3.5) + line("M 97 203 L 97 213", 3.5))
    L["paw_%s_up_t" % side] = g(fill(PAW_UP, "#e8e8e8"))
    L["paw_%s_up" % side] = g(line(PAW_UP) + '<ellipse cx="65" cy="132" rx="11" ry="8.5" fill="%s"/>' % PINK
                               + "".join('<circle cx="%d" cy="%d" r="4.8" fill="%s"/>' % (x, y, PINK) for x, y in ((51, 117), (64, 112), (78, 117))))

# ---- gear (greyscale, tinted: _a main colour, _b trim colour)
G = "#e6e6e6"
L["helm_a_t"] = H(fill("M 44 98 Q 42 28 128 24 Q 214 28 212 98 Z", G, 5))
L["helm_b_t"] = H(both(fill("M 54 72 Q 12 62 20 14 Q 34 46 64 52 Z", G, 5))
                 + '<rect x="38" y="86" width="180" height="17" rx="8.5" fill="%s" stroke="%s" stroke-width="5"/>' % (G, INK)
                 + '<rect x="121" y="28" width="14" height="60" rx="7" fill="%s" stroke="%s" stroke-width="4"/>' % (G, INK))
L["chest_a_t"] = fill("M 76 116 Q 128 128 180 116 Q 202 160 196 214 L 60 214 Q 54 160 76 116 Z", G, 5)
L["chest_b_t"] = (both('<ellipse cx="70" cy="128" rx="28" ry="18" fill="%s" stroke="%s" stroke-width="5"/>' % (G, INK))
                  + '<rect x="60" y="188" width="136" height="11" rx="5.5" fill="%s" stroke="%s" stroke-width="4"/>' % (G, INK)
                  + '<rect x="119" y="184" width="18" height="18" rx="4" fill="%s" stroke="%s" stroke-width="4"/>' % (G, INK))
SWORD_TF = 'transform="rotate(14 168 204)"'
L["sword_a_t"] = '<g %s>%s%s</g>' % (SWORD_TF, fill("M 160 184 L 160 62 L 168 42 L 176 62 L 176 184 Z", G, 5), line("M 168 64 L 168 176", 2.5))
L["sword_b_t"] = '<g %s><rect x="142" y="180" width="52" height="11" rx="5.5" fill="%s" stroke="%s" stroke-width="5"/><rect x="162" y="190" width="12" height="22" rx="3" fill="%s" stroke="%s" stroke-width="4"/></g>' % (SWORD_TF, G, INK, G, INK)
L["shield_a_t"] = '<circle cx="74" cy="184" r="42" fill="%s" stroke="%s" stroke-width="5"/>' % (G, INK)
L["shield_b_t"] = '<circle cx="74" cy="184" r="34" fill="none" stroke="%s" stroke-width="14"/><circle cx="74" cy="184" r="41" fill="none" stroke="%s" stroke-width="4"/><circle cx="74" cy="184" r="27" fill="none" stroke="%s" stroke-width="4"/><circle cx="74" cy="184" r="12" fill="%s" stroke="%s" stroke-width="4"/>' % (G, INK, INK, G, INK)

# ---- signature lookalike: Thunderfury (full colour): pale blue blade with a glowing core, gold swept wings, blue gems
WING = "M 166 188 Q 136 190 128 166 Q 124 150 134 140 Q 138 162 160 174 Z"
L["tf"] = '<g %s>%s%s%s%s%s%s%s</g>' % (
    SWORD_TF,
    fill("M 157 186 L 157 52 L 168 28 L 179 52 L 179 186 Z", "#dcecff", 5),
    '<rect x="164.5" y="56" width="7" height="124" rx="3.5" fill="#5ec8ff"/><rect x="166.5" y="60" width="3" height="116" rx="1.5" fill="#e8f8ff"/>',
    fill(WING, "#f3c04a", 4), '<g transform="translate(336,0) scale(-1,1)">%s</g>' % fill(WING, "#f3c04a", 4),
    '<circle cx="168" cy="188" r="10" fill="#f3c04a" stroke="%s" stroke-width="4"/><circle cx="168" cy="188" r="5" fill="#4fb8ff"/>' % INK,
    '<rect x="162" y="197" width="12" height="18" rx="3" fill="#2f4fa0" stroke="%s" stroke-width="4"/>' % INK,
    "")
def bolt(points):
    d = "M " + " L ".join("%d %d" % p for p in points)
    return ('<path d="%s" fill="none" stroke="#7fd4ff" stroke-width="7" stroke-linejoin="round" stroke-linecap="round" opacity=".55"/>'
            '<path d="%s" fill="none" stroke="#f2fbff" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>') % (d, d)
L["tf_fx1"] = '<g %s>%s%s</g>' % (SWORD_TF, bolt([(150, 70), (138, 84), (149, 90), (136, 106)]), bolt([(186, 120), (199, 132), (188, 138), (201, 154)]))
L["tf_fx2"] = '<g %s>%s%s</g>' % (SWORD_TF, bolt([(186, 62), (199, 76), (188, 82), (200, 98)]), bolt([(150, 128), (137, 140), (148, 146), (135, 162)]))

# ---- fur patterns and skin details (greyscale, tinted by the item's colours)
import math, random
PT = "#e8e8e8"
CLIPS = CLIPS.replace("</defs>", '<clipPath id="pawL"><path d="%s"/></clipPath><clipPath id="pawR"><path d="%s" transform="translate(256,0) scale(-1,1)"/></clipPath></defs>' % (PAW_DOWN, PAW_DOWN))
def body_clip(x): return '<g clip-path="url(#body)">%s</g>' % x
def head_clip(x): return H('<g clip-path="url(#head)">%s</g>' % x)
def paws(x_fn):
    return {"paw_L": '<g clip-path="url(#pawL)">%s</g>' % x_fn(), "paw_R": '<g clip-path="url(#pawR)"><g %s>%s</g></g>' % (MIRROR, x_fn())}
def rect(x, y, w, h, r=None): return '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"/>' % (x, y, w, h, h / 2 if r is None else r, PT)
def circ(x, y, r): return '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (x, y, r, PT)
def ring(x, y, r, w): return '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="%s"/>' % (x, y, r, PT, w)
def star4(x, y, r): return '<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z" fill="%s"/>' % (
    x, y - r, x + r * .3, y - r * .3, x + r, y, x + r * .3, y + r * .3, x, y + r, x - r * .3, y + r * .3, x - r, y, x - r * .3, y - r * .3, PT)
def scatter(seed, n, box, fn):
    rnd = random.Random(seed); x0, y0, x1, y1 = box
    return "".join(fn(rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd) for _ in range(n))
PAT = {}
# tabby: bold side stripes, forehead M, cheek stripes
PAT["tabby"] = {"body": body_clip(both(rect(48, 140, 34, 10) + rect(48, 158, 30, 10) + rect(48, 176, 26, 10) + rect(48, 194, 22, 10))),
                "head": head_clip('<path d="M 112 50 L 120 78 L 128 56 L 136 78 L 144 50 L 150 52 L 140 88 L 128 68 L 116 88 L 106 52 Z" fill="%s"/>' % PT
                                  + both(rect(34, 96, 30, 9) + rect(34, 112, 24, 9)))}
# tuxedo: white bib, chin and paws
PAT["tuxedo"] = {"body": body_clip('<ellipse cx="128" cy="176" rx="54" ry="74" fill="%s"/>' % PT),
                 "head": head_clip('<path d="M 128 96 Q 100 128 66 150 Q 128 182 190 150 Q 156 128 128 96 Z" fill="%s"/>' % PT)}
PAT["tuxedo"].update(paws(lambda: '<rect x="60" y="180" width="60" height="40" fill="%s"/>' % PT))
# star blaze: white blaze up the face and white toes
PAT["socks"] = {"head": head_clip('<path d="M 128 132 Q 116 96 120 60 L 128 40 L 136 60 Q 140 96 128 132 Z" fill="%s"/>' % PT + star4(128, 52, 14))}
PAT["socks"].update(paws(lambda: '<rect x="60" y="202" width="60" height="20" fill="%s"/>' % PT))
# calico: two colours of patches
PAT["calico"] = {"body": body_clip('<path d="M 50 120 Q 90 130 96 160 Q 80 190 50 190 Z" fill="%s"/>' % PT + '<ellipse cx="180" cy="196" rx="30" ry="22" fill="%s"/>' % PT),
                 "head": head_clip('<path d="M 40 30 L 110 40 Q 112 90 80 104 Q 50 104 40 90 Z" fill="%s"/>' % PT),
                 "body2": body_clip('<ellipse cx="190" cy="136" rx="26" ry="20" fill="%s"/>' % PT + '<ellipse cx="66" cy="206" rx="22" ry="14" fill="%s"/>' % PT),
                 "head2": head_clip('<path d="M 216 30 L 150 40 Q 150 80 176 96 Q 206 98 216 84 Z" fill="%s"/>' % PT)}
# Siamese points: dark face mask, ears and paws
PAT["points"] = {"head": head_clip('<ellipse cx="128" cy="124" rx="56" ry="42" fill="%s" opacity=".85"/>' % PT
                                   + both('<path d="M 50 20 L 100 56 L 70 84 Z" fill="%s"/>' % PT))}
PAT["points"].update(paws(lambda: '<rect x="60" y="180" width="60" height="40" fill="%s"/>' % PT))
# leopard: rosettes
rose = lambda x, y, rnd: ring(x, y, rnd.uniform(5, 8), 4) if rnd.random() < .7 else circ(x, y, rnd.uniform(3, 5))
PAT["leopard"] = {"body": body_clip(scatter(1, 34, (52, 120, 204, 214), rose)), "head": head_clip(scatter(2, 16, (44, 30, 212, 100), rose))}
# tiger stripes: bold pointed stripes
def tstripe(x, y, w, h, flip): 
    d = "M %d %d Q %d %d %d %d Q %d %d %d %d Z" % (x, y, x + w * .6 * flip, y - 3, x + w * flip, y + h / 2, x + w * .6 * flip, y + h - 2, x, y + h)
    return '<path d="%s" fill="%s"/>' % (d, PT)
PAT["stripes"] = {"body": body_clip("".join(tstripe(46, y, 44, 12, 1) + tstripe(210, y, 44, 12, -1) for y in range(122, 214, 20))),
                  "head": head_clip('<path d="M 118 30 L 128 74 L 138 30 Z" fill="%s"/>' % PT + both(tstripe(30, 92, 38, 10, 1) + tstripe(30, 112, 32, 10, 1) + tstripe(84, 36, 20, 30, 1)))}
# stars
PAT["stars"] = {"body": body_clip(scatter(3, 16, (52, 120, 204, 214), lambda x, y, rnd: star4(x, y, rnd.uniform(5, 9)))),
                "head": head_clip(scatter(4, 8, (44, 30, 212, 96), lambda x, y, rnd: star4(x, y, rnd.uniform(5, 8))))}
# mech plates: panel lines and a forehead plate; rivets in the second colour
PAT["plates"] = {"body": body_clip(both('<path d="M 60 130 L 110 130 L 110 214 L 60 214" fill="none" stroke="%s" stroke-width="6"/>' % PT) + rect(60, 168, 136, 6, 3)),
                 "head": head_clip('<path d="M 56 44 L 200 44 L 192 76 L 64 76 Z" fill="%s"/>' % PT),
                 "body2": body_clip(both(circ(68, 140, 4) + circ(68, 200, 4) + circ(100, 140, 4) + circ(100, 200, 4))),
                 "head2": head_clip(circ(70, 60, 5) + circ(186, 60, 5) + circ(128, 60, 5))}
# bones: ribs on the body, skull markings around the eyes
PAT["bones"] = {"body": body_clip(rect(122, 122, 12, 92, 6) + both("".join('<path d="M 124 %d Q 96 %d 74 %d" fill="none" stroke="%s" stroke-width="7" stroke-linecap="round"/>' % (y, y - 4, y + 8, PT) for y in (136, 156, 176, 196)))),
                "head": head_clip(both(ring(98, 112, 18, 6)) + '<path d="M 120 130 L 128 120 L 136 130 Z" fill="%s"/>' % PT)}

# ---- more fur patterns (skins). Shapes are greyscale (tinted by the skin's colours); ink-coloured
# lines stay dark after tinting, and a pattern whose colour is white keeps its own colours.
def P(d, op=None): return '<path d="%s" fill="%s"%s/>' % (d, PT, ' opacity="%s"' % op if op else "")
def inkline(d, w=3): return '<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round"/>' % (d, INK, w)
def ptline(d, w=4, op=None): return '<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round"%s/>' % (d, PT, w, ' opacity="%s"' % op if op else "")
def blob(cx, cy, rx, ry, seed, n=8, j=.28, op=None):
    """a smooth, lumpy patch"""
    rnd = random.Random(seed); pts = []
    for k in range(n):
        a = k * 2 * math.pi / n + rnd.uniform(-.2, .2); f = 1 + rnd.uniform(-j, j)
        pts.append((cx + math.cos(a) * rx * f, cy + math.sin(a) * ry * f))
    mid = lambda p, q: ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    m0 = mid(pts[-1], pts[0]); d = "M %.1f %.1f" % m0
    for k in range(n):
        p, m = pts[k], mid(pts[k], pts[(k + 1) % n]); d += " Q %.1f %.1f %.1f %.1f" % (p[0], p[1], m[0], m[1])
    return P(d + " Z", op)
def heart(x, y, s, col=PT, ink=0):
    d = "M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f Z" % (
        x, y + s * .9, x - s * 1.4, y + s * .05, x - s * .8, y - s * 1.05, x, y - s * .38, x + s * .8, y - s * 1.05, x + s * 1.4, y + s * .05, x, y + s * .9)
    return '<path d="%s" fill="%s"%s/>' % (d, col, ' stroke="%s" stroke-width="%s"' % (INK, ink) if ink else "")
def poly(pts, col=PT, ink=0, op=None):
    return '<path d="M %s Z" fill="%s"%s%s/>' % (" L ".join("%.1f %.1f" % p for p in pts), col,
        ' stroke="%s" stroke-width="%s" stroke-linejoin="round"' % (INK, ink) if ink else "", ' opacity="%s"' % op if op else "")
def ngon(x, y, r, n, rot=0, inner=None):
    pts = []
    for k in range(n * (2 if inner else 1)):
        a = rot + k * math.pi * (1 if inner else 2) / n
        rr = (inner if inner and k % 2 else r)
        pts.append((x + math.sin(a) * rr, y - math.cos(a) * rr))
    return pts
def cog(x, y, r, teeth=8):
    pts = []
    for k in range(teeth * 4):
        a = k * 2 * math.pi / (teeth * 4) + math.pi / (teeth * 4)
        rr = r if (k % 4) in (1, 2) else r * .76
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    return poly(pts, PT, 2.5) + '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (x, y, r * .3, INK)
def jag(x, y, steps, seed, dx=(-9, 9), dy=(8, 14)):
    rnd = random.Random(seed); d = "M %.1f %.1f" % (x, y)
    for _ in range(steps):
        x += rnd.uniform(*dx); y += rnd.uniform(*dy); d += " L %.1f %.1f" % (x, y)
    return d
def sparkle(x, y, r): return star4(x, y, r)
def body_spots(seed, n, fn, box=(54, 122, 202, 214)): return body_clip(scatter(seed, n, box, fn))

# tortoiseshell: mottled patches in two colours, a split face
PAT["tortie"] = {"body": body_clip("".join(blob(x, y, 22, 16, s) for s, (x, y) in enumerate(((70, 132), (176, 150), (110, 196), (190, 204), (140, 132), (66, 182))))),
                 "body2": body_clip("".join(blob(x, y, 12, 9, 20 + s) for s, (x, y) in enumerate(((96, 156), (160, 186), (70, 210), (186, 128))))),
                 "head": head_clip('<path d="M 40 20 L 128 20 L 128 60 Q 118 96 128 170 L 40 170 Z" fill="%s"/>' % PT + blob(178, 70, 20, 14, 7)),
                 "head2": head_clip(blob(70, 64, 14, 10, 8) + blob(190, 104, 12, 9, 9) + blob(150, 46, 10, 8, 10))}
PAT["tortie"].update(paws(lambda: blob(92, 206, 16, 10, 11)))
# snowshoe: dark Siamese mask and ears, white upside-down V up the face
PAT["snowshoe"] = {"head": head_clip('<ellipse cx="128" cy="120" rx="62" ry="44" fill="%s" opacity=".9"/>' % PT + both('<path d="M 50 20 L 100 56 L 68 86 Z" fill="%s"/>' % PT)),
                   "head2": head_clip('<path d="M 128 86 Q 136 120 176 170 L 80 170 Q 120 120 128 86 Z" fill="%s"/>' % PT),
                   "body": body_clip('<path d="M 50 110 Q 128 150 206 110 L 206 100 L 50 100 Z" fill="%s" opacity=".45"/>' % PT)}
# bengal: broken rosettes with glowing orange centres
def ros(x, y, rnd):
    r = rnd.uniform(5.5, 8.5)
    return '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="3.6" stroke-dasharray="%.1f 4" transform="rotate(%d %.1f %.1f)"/>' % (x, y, r, PT, r * 1.6, rnd.randint(0, 360), x, y)
def ros_c(x, y, rnd):
    r = rnd.uniform(5.5, 8.5); rnd.randint(0, 360)
    return '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (x, y, r - 1.5, PT)
PAT["bengal"] = {"body": body_spots(31, 26, ros), "body2": body_spots(31, 26, ros_c),
                 "head": head_clip(scatter(32, 12, (48, 32, 208, 96), ros) + rect(122, 44, 12, 30, 6)),
                 "head2": head_clip(scatter(32, 12, (48, 32, 208, 96), ros_c))}
PAT["bengal"].update(paws(lambda: circ(80, 205, 4) + circ(98, 200, 3.5)))
# dalmatian: bold black spots and one dark ear
spot = lambda x, y, rnd: '<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="%s"/>' % (x, y, rnd.uniform(4, 9), rnd.uniform(4, 8), PT)
PAT["dalmatian"] = {"body": body_spots(41, 24, spot), "head": head_clip(scatter(42, 9, (60, 50, 200, 100), spot) + '<path d="M 40 10 L 104 52 Q 80 70 50 80 Z" fill="%s"/>' % PT)}
PAT["dalmatian"].update(paws(lambda: '<circle cx="86" cy="204" r="5" fill="%s"/>' % PT))
# cow: big patches, one over an eye
PAT["cow"] = {"body": body_clip(blob(64, 150, 30, 26, 51) + blob(180, 190, 30, 24, 52) + blob(140, 136, 18, 12, 53)),
              "head": head_clip(blob(176, 96, 34, 30, 54) + blob(72, 44, 26, 20, 55))}
PAT["cow"]["paw_L"] = '<g clip-path="url(#pawL)">%s</g>' % blob(102, 210, 16, 12, 56)
# strawberry: little hearts and a leafy green cap
hrt = lambda x, y, rnd: heart(x, y, rnd.uniform(5, 8))
CALYX = '<g transform="translate(128 54) scale(1 .6)">%s</g>' % poly(ngon(0, 0, 58, 7, math.pi, 20), PT, 4) + '<path d="M 128 40 Q 126 30 132 22" fill="none" stroke="%s" stroke-width="9" stroke-linecap="round"/>' % INK
PAT["hearts"] = {"body": body_spots(61, 14, hrt), "head": head_clip(heart(80, 140, 7) + heart(176, 140, 7) + heart(102, 84, 5) + heart(154, 84, 5)),
                 "head2": head_clip(CALYX)}
PAT["hearts"].update(paws(lambda: heart(90, 205, 5)))
# galaxy: a purple nebula band with twinkling stars on top
PAT["galaxy"] = {"body": body_clip(P("M 40 150 Q 90 120 140 150 Q 190 176 220 140 L 220 186 Q 180 212 130 186 Q 84 164 40 196 Z", ".75")
                                   + P("M 40 172 Q 100 150 150 176 Q 190 196 220 176 L 220 186 Q 180 212 130 186 Q 84 164 40 196 Z", ".6")),
                 "head": head_clip(P("M 30 70 Q 90 40 150 64 Q 200 84 230 50 L 230 80 Q 190 110 140 88 Q 90 68 30 100 Z", ".7")),
                 "body2": body_clip(scatter(63, 12, (56, 122, 200, 214), lambda x, y, rnd: star4(x, y, rnd.uniform(4, 8))) + scatter(64, 22, (56, 122, 200, 214), lambda x, y, rnd: circ(x, y, rnd.uniform(1, 2)))),
                 "head2": head_clip(scatter(65, 6, (52, 36, 204, 96), lambda x, y, rnd: star4(x, y, rnd.uniform(4, 7))) + scatter(66, 10, (52, 36, 204, 96), lambda x, y, rnd: circ(x, y, 1.5)))}
# lava cracks: glowing seams and embers on dark fur
def cracks(seed, starts, steps, w):
    return "".join(ptline(jag(x, y, steps, seed + i), w * 3, ".3") + ptline(jag(x, y, steps, seed + i), w) for i, (x, y) in enumerate(starts))
PAT["lava"] = {"body": body_clip(cracks(71, ((80, 124), (128, 126), (176, 124), (104, 176), (156, 176), (66, 180), (190, 180)), 5, 3.5)),
               "body2": body_spots(72, 10, lambda x, y, rnd: circ(x, y, rnd.uniform(1.5, 3))),
               "head": head_clip(cracks(73, ((128, 26), (70, 40), (190, 40)), 4, 3)),
               "head2": head_clip(scatter(74, 5, (60, 40, 200, 90), lambda x, y, rnd: circ(x, y, 2.2)))}
PAT["lava"].update(paws(lambda: ptline("M 80 196 L 86 204 L 82 212", 3)))
# Defias bandit: red eye mask and neckerchief, dark leather strap
PAT["bandit"] = {"head": head_clip('<path d="M 44 96 Q 128 84 212 96 L 214 126 Q 172 132 140 124 Q 128 120 116 124 Q 84 132 42 126 Z" fill="%s"/>' % PT
                                   + '<path d="M 44 104 L 18 92 L 22 112 L 4 120 L 44 120 Z" fill="%s"/>' % PT),
                 "body": body_clip('<path d="M 60 112 L 196 112 L 128 178 Z" fill="%s"/>' % PT + inkline("M 96 128 L 128 164 L 160 128", 2.5)),
                 "body2": body_clip('<path d="M 64 214 L 184 112 L 202 124 L 82 214 Z" fill="%s"/>' % PT + circ(150, 150, 5))}
# Scarlet Crusade: red tabard with a golden sun, red hood
PAT["crusader"] = {"body": body_clip('<path d="M 96 112 L 160 112 L 164 214 L 92 214 Z" fill="%s"/>' % PT),
                   "body2": body_clip(poly(ngon(128, 160, 18, 8, 0, 9)) + ring(128, 160, 7, 3) + rect(94, 112, 4, 102, 2) + rect(158, 112, 4, 102, 2)),
                   "head": head_clip('<path d="M 30 10 L 226 10 L 226 92 Q 210 70 128 64 Q 46 70 30 92 Z" fill="%s"/>' % PT),
                   "head2": head_clip(poly(ngon(128, 56, 9, 6, 0, 4.5)) + '<path d="M 30 92 Q 46 70 128 64 Q 210 70 226 92" fill="none" stroke="%s" stroke-width="4"/>' % PT)}
# Gnomeregan clockwork: brass cogs, copper rivets
PAT["cogs"] = {"body": body_clip(cog(80, 150, 24, 9) + cog(170, 196, 20, 8) + cog(150, 132, 12, 7)),
               "body2": body_clip(rect(124, 170, 8, 44, 4) + both(circ(116, 180, 3.5) + circ(116, 200, 3.5))),
               "head": head_clip(cog(128, 58, 16, 8) + rect(60, 74, 40, 6) + rect(156, 74, 40, 6)),
               "head2": head_clip(circ(66, 77, 3) + circ(190, 77, 3))}
# Onyxia's brood: scale rows, bronze belly plates, little horn nubs
scl = lambda y0, y1, x0, x1, r: "".join('<path d="M %.1f %.1f A %.1f %.1f 0 0 0 %.1f %.1f" fill="none" stroke="%s" stroke-width="3.2" stroke-linecap="round"/>' % (x - r, y, r, r, x + r, y, PT)
                                     for j, y in enumerate(range(y0, y1, int(r * 1.1))) for x in [x0 + (r if j % 2 else 0) + k * r * 2 for k in range(int((x1 - x0) / (r * 2)) + 1)])
PAT["scales"] = {"body": body_clip(scl(116, 216, 44, 216, 9)),
                 "body2": body_clip("".join('<rect x="%d" y="%d" width="%d" height="11" rx="5.5" fill="%s" stroke="%s" stroke-width="1.5"/>' % (128 - w / 2, y, w, PT, INK) for y, w in ((136, 34), (151, 40), (166, 42), (181, 42), (196, 38)))),
                 "head": head_clip(scl(30, 92, 40, 220, 8)),
                 "head2": head_clip(both('<path d="M 98 80 L 108 48 L 118 76 Z" fill="%s" stroke="%s" stroke-width="2.5" stroke-linejoin="round"/>' % (PT, INK)))}
# Naxxramas patchwork: sewn-on patches and stitched scars
def stitches(d_pts, n=6):
    s = inkline("M " + " L ".join("%.1f %.1f" % p for p in d_pts), 2.5)
    for (x0, y0), (x1, y1) in zip(d_pts, d_pts[1:]):
        for k in range(1, n):
            t = k / n; x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            nx, ny = -(y1 - y0), (x1 - x0); ln = math.hypot(nx, ny) or 1; nx, ny = nx / ln * 5, ny / ln * 5
            s += inkline("M %.1f %.1f L %.1f %.1f" % (x - nx, y - ny, x + nx, y + ny), 2.2)
    return s
patch1 = [(56, 128), (104, 122), (110, 168), (60, 176)]
patch2 = [(150, 170), (196, 164), (204, 212), (150, 214)]
PAT["patchwork"] = {"body": body_clip(poly(patch1) + stitches(patch1 + [patch1[0]], 4) + stitches([(124, 130), (134, 178), (126, 214)], 4)),
                    "body2": body_clip(poly(patch2) + stitches(patch2 + [patch2[0]], 4)),
                    "head": head_clip(poly([(140, 74), (196, 66), (210, 124), (150, 132)]) + stitches([(140, 74), (196, 66), (210, 124), (150, 132), (140, 74)], 3)
                                      + stitches([(72, 52), (110, 74)], 4))}
# Uldaman stone: cracks and glowing titan runes
PAT["cracks"] = {"body": body_clip(ptline(jag(70, 112, 5, 81), 3) + ptline(jag(184, 120, 5, 82), 3) + ptline(jag(140, 160, 3, 83), 3) + ptline("M 66 196 L 80 186 L 92 192", 3)),
                 "body2": body_clip(ptline("M 128 130 L 128 150 M 116 150 L 140 150 M 118 162 L 128 172 L 138 162 M 128 172 L 128 196", 4) + ring(128, 162, 26, 3.5)),
                 "head": head_clip(ptline(jag(80, 30, 4, 84), 3) + ptline(jag(180, 40, 3, 85), 3)),
                 "head2": head_clip(ptline("M 118 50 L 128 40 L 138 50 L 128 60 Z M 128 60 L 128 84", 4))}
# Ahn'Qiraj: a golden scarab on the chest, gold circlet with a gem
PAT["scarab"] = {"body": body_clip('<ellipse cx="128" cy="168" rx="24" ry="30" fill="%s" stroke="%s" stroke-width="2.5"/>' % (PT, INK)
                                   + '<path d="M 112 140 Q 128 124 144 140 Z" fill="%s" stroke="%s" stroke-width="2.5"/>' % (PT, INK) + inkline("M 128 140 L 128 198", 2.5)
                                   + both(ptline("M 106 156 L 90 148 M 104 172 L 86 172 M 106 188 L 90 198", 4))
                                   + both('<path d="M 50 130 Q 70 160 60 214" fill="none" stroke="%s" stroke-width="6"/>' % PT)),
                 "body2": body_clip(circ(128, 160, 6)),
                 "head": head_clip('<path d="M 46 60 Q 128 40 210 60 L 210 70 Q 128 52 46 70 Z" fill="%s"/>' % PT + poly([(116, 52), (140, 52), (128, 76)], PT, 2.5)),
                 "head2": head_clip(circ(128, 60, 5))}
# Maraudon crystals: purple shards with bright facets
def shard(x, y, w, h, tilt):
    return poly([(x - w / 2, y), (x - w / 2 + tilt * .3, y - h * .7), (x + tilt, y - h), (x + w / 2 + tilt * .3, y - h * .7), (x + w / 2, y)], PT, 2.5)
def facet(x, y, w, h, tilt):
    return poly([(x, y), (x + tilt * .6, y - h * .7), (x + tilt, y - h), (x + w / 2 + tilt * .3, y - h * .7), (x + w / 2, y)])
SHARDS_B = [(86, 168, 16, 40, -10), (100, 168, 12, 26, 2), (170, 166, 16, 42, 10), (156, 166, 11, 24, -2), (128, 214, 16, 44, 0), (116, 214, 10, 24, -8), (140, 214, 10, 26, 8),
            (64, 214, 14, 32, -6), (192, 214, 14, 30, 6)]
SHARDS_H = [(172, 84, 13, 32, 8), (186, 86, 9, 18, 12), (84, 84, 10, 22, -8)]
PAT["crystals"] = {"body": body_clip("".join(shard(*s) for s in SHARDS_B)), "body2": body_clip("".join(facet(*s) for s in SHARDS_B)),
                   "head": head_clip("".join(shard(*s) for s in SHARDS_H)), "head2": head_clip("".join(facet(*s) for s in SHARDS_H))}
# sparkles: glittering stars and dots (golden cat)
def star4i(x, y, r): return star4(x, y, r).replace("/>", ' stroke="%s" stroke-width="2" stroke-linejoin="round"/>' % INK)
def coin(x, y, r): return '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" stroke-width="2.5"/><circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="1.5" opacity=".6"/>' % (x, y, r, PT, INK, x, y, r * .62, INK)
PAT["sparkles"] = {"body": body_clip(star4i(92, 142, 11) + star4i(166, 150, 9) + star4i(128, 196, 10) + star4i(74, 204, 7) + star4i(186, 200, 7)) + body_spots(92, 18, lambda x, y, rnd: circ(x, y, rnd.uniform(1.2, 2.4))),
                   "body2": body_clip(coin(138, 140, 8) + coin(112, 176, 7) + coin(150, 214, 9) + coin(66, 170, 6) + coin(190, 172, 6)),
                   "head": head_clip(star4i(84, 66, 10) + star4i(174, 58, 8) + circ(106, 50, 2.4) + circ(194, 88, 2.4) + circ(150, 86, 2))}
PAT["sparkles"].update(paws(lambda: star4i(96, 205, 6)))
# diamonds: a cut gem on the chest and on the brow, small glints around
def gem(x, y, s):
    out = [(x - s, y - s * .35), (x - s * .55, y - s * .8), (x + s * .55, y - s * .8), (x + s, y - s * .35), (x, y + s)]
    return poly(out, PT, 2.5)
def gemfacets(x, y, s):
    return (poly([(x - s * .55, y - s * .8), (x + s * .55, y - s * .8), (x + s * .3, y - s * .35), (x - s * .3, y - s * .35)])
            + poly([(x - s * .3, y - s * .35), (x + s * .3, y - s * .35), (x, y + s)], PT, 0, ".6"))
rh = lambda x, y, rnd: poly([(x, y - 6), (x + 4, y), (x, y + 6), (x - 4, y)])
PAT["gems"] = {"body": body_clip(gem(128, 160, 22) + scatter(93, 12, (56, 124, 200, 214), rh)), "body2": body_clip(gemfacets(128, 160, 22)),
               "head": head_clip(gem(128, 62, 13) + rh(80, 60, None) + rh(178, 56, None)), "head2": head_clip(gemfacets(128, 62, 13))}
# four-leaf clovers and lucky coins
def clover(x, y, s, rot=0):
    leaves = "".join(heart(0, -s * .55, s * .55) .replace("<path", '<path transform="rotate(%d)"' % a) for a in (0, 90, 180, 270))
    return '<g transform="translate(%.1f %.1f) rotate(%d)">%s<path d="M 0 0 Q %.1f %.1f %.1f %.1f" fill="none" stroke="%s" stroke-width="2.5" stroke-linecap="round"/></g>' % (x, y, rot, leaves, s * .4, s * .9, s * .2, s * 1.4, PT)
PAT["clover"] = {"body": body_clip(clover(82, 150, 16, 12) + clover(176, 140, 12, -20) + clover(170, 200, 14, 30) + clover(108, 200, 10, -10)),
                 "body2": body_clip(ring(128, 150, 7, 3.5) + ring(66, 196, 6, 3) + ring(196, 172, 6, 3) + circ(128, 150, 3)),
                 "head": head_clip(clover(128, 62, 15, 0))}
PAT["clover"].update(paws(lambda: clover(92, 205, 7, 10)))
# rainbow: full-colour arcs (tinted white)
RB = ["#ff5a5a", "#ffa040", "#ffe14a", "#5ad85a", "#4aa8ff", "#a070ff"]
def rainbow(cx, cy, r0, w):
    return "".join('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="%.1f"/>' % (cx, cy, r0 - k * w, col, w + .6) for k, col in enumerate(RB))
PAT["rainbow"] = {"body": body_clip(rainbow(128, 232, 108, 7) + '<ellipse cx="74" cy="200" rx="18" ry="10" fill="#ffffff" stroke="%s" stroke-width="2.5"/><ellipse cx="182" cy="200" rx="18" ry="10" fill="#ffffff" stroke="%s" stroke-width="2.5"/>' % (INK, INK)),
                  "head": head_clip(rainbow(128, 116, 76, 5.5))}
# quest-giver: a big golden "!" (weekly) or "?" (daily) on the forehead
def bang():
    return (poly([(119, 32), (137, 32), (133, 76), (123, 76)], PT, 3.5) + '<circle cx="128" cy="88" r="7.5" fill="%s" stroke="%s" stroke-width="3.5"/>' % (PT, INK))
def qmark():
    d = "M 113 48 Q 114 30 129 30 Q 145 30 145 46 Q 145 58 133 64 Q 128 67 128 76"
    return ('<path d="%s" fill="none" stroke="%s" stroke-width="17" stroke-linecap="round" stroke-linejoin="round"/>' % (d, INK)
            + '<path d="%s" fill="none" stroke="%s" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>' % (d, PT)
            + '<circle cx="128" cy="89" r="7.5" fill="%s" stroke="%s" stroke-width="3.5"/>' % (PT, INK))
PAT["quest"] = {"head": head_clip(bang()), "body": body_spots(101, 8, lambda x, y, rnd: star4(x, y, rnd.uniform(3, 5)))}
PAT["questq"] = {"head": head_clip(qmark()), "body": body_spots(102, 8, lambda x, y, rnd: star4(x, y, rnd.uniform(3, 5)))}
# flames licking up from below, hotter inner flames
def flames(x0, x1, base, h, seed, inner=False):
    rnd = random.Random(seed); d = "M %d %d" % (x0, base + 10); x = x0
    while x < x1:
        w = rnd.uniform(16, 26); hh = h * rnd.uniform(.6, 1.0) * (.6 if inner else 1)
        d += " Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f" % (x + w * .1, base - hh * .5, x + w * .5 + rnd.uniform(-4, 4), base - hh, x + w * .6, base - hh * .4, x + w, base)
        x += w
    return P(d + " L %d %d Z" % (x1, base + 10))
PAT["flames"] = {"body": body_clip(flames(40, 220, 216, 70, 111)), "body2": body_clip(flames(40, 220, 216, 70, 112, True)),
                 "head": head_clip(flames(90, 166, 92, 46, 113) + both('<path d="M 46 150 Q 56 120 50 96 Q 66 118 66 150 Z" fill="%s"/>' % PT)),
                 "head2": head_clip(flames(100, 156, 92, 46, 114, True))}
# arcane runes: a glowing rune circle and glyphs
GLYPHS = ["M -6 -8 L 6 -8 L -6 8 L 6 8", "M 0 -9 L 0 9 M -7 -3 L 0 3 L 7 -3", "M -7 8 L 0 -8 L 7 8 M -4 2 L 4 2", "M -6 -8 L -6 8 L 6 0 Z", "M 6 -8 L -4 -8 L 4 0 L -4 8", "M -7 0 L 0 -8 L 7 0 L 0 8 Z M 0 -8 L 0 8"]
def glyph(x, y, i, s=1, w=3): return '<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round" transform="translate(%.1f %.1f) scale(%s)"/>' % (GLYPHS[i % len(GLYPHS)], PT, w, x, y, s)
PAT["runes"] = {"body": body_clip(ring(128, 168, 36, 8).replace('stroke-width="8"', 'stroke-width="10" opacity=".3"') + ring(128, 168, 36, 3) + ring(128, 168, 26, 2)
                                  + "".join(glyph(128 + math.cos(a) * 31, 168 + math.sin(a) * 31, k, .45, 4) for k, a in enumerate([j * math.pi / 4 for j in range(8)]))
                                  + glyph(70, 140, 0) + glyph(188, 140, 2) + glyph(70, 200, 4) + glyph(188, 204, 5) + glyph(128, 168, 1, 1.3, 3.5)),
                "head": head_clip(glyph(128, 60, 5, 1.6, 4) + glyph(76, 72, 3, .9) + glyph(180, 72, 4, .9))}
# party animal: full-colour confetti (tinted white)
CONF = ["#ff5a7a", "#ffd23c", "#4ac8ff", "#7ae05a", "#b080ff", "#ff9a3c"]
def confetti(x, y, rnd):
    col = rnd.choice(CONF)
    if rnd.random() < .6:
        return '<rect x="%.1f" y="%.1f" width="9" height="4.5" rx="1.5" fill="%s" transform="rotate(%d %.1f %.1f)"/>' % (x - 4.5, y - 2.2, col, rnd.randint(0, 180), x, y)
    return '<circle cx="%.1f" cy="%.1f" r="3" fill="%s"/>' % (x, y, col)
PAT["confetti"] = {"body": body_spots(121, 34, confetti), "head": head_clip(scatter(122, 14, (50, 34, 206, 98), confetti))}
PAT["confetti"].update(paws(lambda: '<rect x="84" y="200" width="9" height="4.5" rx="1.5" fill="#ffd23c" transform="rotate(30 88 202)"/>'))
# raid leader: the skull marker on the brow and the other raid markers (full colour, tinted white)
def mk_star(x, y): return poly(ngon(x, y, 9, 5, 0, 4), "#ffd23c", 2.2)
def mk_circle(x, y): return '<circle cx="%.1f" cy="%.1f" r="7.5" fill="#ff8a1c" stroke="%s" stroke-width="2.2"/>' % (x, y, INK)
def mk_diamond(x, y): return poly([(x, y - 9), (x + 7, y), (x, y + 9), (x - 7, y)], "#c05cff", 2.2)
def mk_tri(x, y): return poly([(x, y - 9), (x + 8.5, y + 6.5), (x - 8.5, y + 6.5)], "#3ec83e", 2.2)
def mk_moon(x, y): return '<path d="M %.1f %.1f A 8.5 8.5 0 1 0 %.1f %.1f A 6.5 6.5 0 1 1 %.1f %.1f Z" fill="#dfe6f2" stroke="%s" stroke-width="2.2"/>' % (x + 3, y - 8, x + 3, y + 8, x + 3, y - 8, INK)
def mk_square(x, y): return '<rect x="%.1f" y="%.1f" width="15" height="15" fill="#3a8cff" stroke="%s" stroke-width="2.2"/>' % (x - 7.5, y - 7.5, INK)
def mk_cross(x, y): return poly([(x - 8, y - 5), (x - 5, y - 8), (x, y - 3), (x + 5, y - 8), (x + 8, y - 5), (x + 3, y), (x + 8, y + 5), (x + 5, y + 8), (x, y + 3), (x - 5, y + 8), (x - 8, y + 5), (x - 3, y)], "#ff3a3a", 2.2)
def mk_skull(x, y, s=1):
    return ('<g transform="translate(%.1f %.1f) scale(%s)"><path d="M -12 2 Q -13 -14 0 -14 Q 13 -14 12 2 Q 12 8 7 9 L 7 14 L -7 14 L -7 9 Q -12 8 -12 2 Z" fill="#fbfbf4" stroke="%s" stroke-width="2.5" stroke-linejoin="round"/>'
            '<circle cx="-5" cy="-1" r="3.6" fill="%s"/><circle cx="5" cy="-1" r="3.6" fill="%s"/><path d="M 0 4 L -2 8 L 2 8 Z" fill="%s"/></g>') % (x, y, s, INK, INK, INK, INK)
PAT["raidmarks"] = {"body": body_clip(mk_star(92, 134) + mk_circle(164, 134) + mk_diamond(128, 136) + mk_tri(106, 156) + mk_moon(150, 156) + mk_square(128, 178) + mk_cross(128, 206)),
                    "head": head_clip(mk_skull(128, 60, 1.4))}
# koi pond: Tancho red cap, orange and black koi patches
PAT["koi"] = {"body": body_clip(blob(76, 140, 22, 15, 131) + blob(178, 182, 24, 18, 132) + blob(120, 204, 16, 10, 133)),
              "body2": body_clip(blob(150, 134, 10, 7, 134) + blob(84, 190, 10, 8, 135) + blob(196, 140, 7, 5, 136)),
              "head": head_clip('<circle cx="128" cy="70" r="20" fill="%s"/>' % PT),
              "head2": head_clip(blob(70, 56, 9, 7, 137))}
# moss: soft green moss over the back and head, a few little flowers
def flower(x, y, s=1):
    return ('<g transform="translate(%.1f %.1f) scale(%s)">' % (x, y, s) + "".join('<ellipse cx="0" cy="-5" rx="3.6" ry="5" fill="%s" transform="rotate(%d)"/>' % (PT, a) for a in range(0, 360, 72))
            + '<circle cx="0" cy="0" r="2.6" fill="%s"/></g>' % INK)
PAT["moss"] = {"body": body_clip(blob(80, 140, 28, 18, 141, 12, .35) + blob(178, 146, 26, 18, 142, 12, .35) + blob(150, 206, 22, 12, 143, 10, .35) + blob(62, 200, 14, 14, 144, 10, .35)),
               "body2": body_clip(flower(86, 138) + flower(176, 146, .9) + flower(152, 206, .8) + flower(64, 196, .7)),
               "head": head_clip(blob(128, 46, 84, 26, 145, 14, .25) + blob(186, 72, 24, 18, 146, 10, .3)),
               "head2": head_clip(flower(104, 62, 1.1) + flower(150, 58, .9) + flower(188, 76, .8))}
PAT["moss"]["paw_R"] = '<g clip-path="url(#pawR)"><g %s>%s</g></g>' % (MIRROR, blob(84, 208, 14, 9, 147))
# coal miner: soot smudges, a headlamp strap and a bright lamp
PAT["soot"] = {"body": body_clip(blob(70, 170, 20, 14, 151, 9, .35, ".7") + blob(186, 140, 18, 12, 152, 9, .35, ".7") + blob(150, 206, 16, 10, 153, 9, .35, ".6")),
               "head": head_clip('<path d="M 40 68 Q 128 50 216 68 L 216 82 Q 128 62 40 82 Z" fill="%s"/>' % PT + '<circle cx="128" cy="66" r="16" fill="%s" stroke="%s" stroke-width="3"/>' % (PT, INK)
                                 + blob(186, 140, 14, 9, 154, 9, .3, ".7") + blob(70, 96, 10, 7, 155, 8, .3, ".6")),
               "head2": head_clip('<circle cx="128" cy="66" r="10" fill="%s" stroke="%s" stroke-width="2"/><circle cx="124.5" cy="62.5" r="3" fill="#ffffff"/>' % (PT, INK))}
PAT["soot"].update(paws(lambda: blob(90, 208, 12, 7, 156, 8, .3, ".7")))

for name, parts in PAT.items():
    for part, body in parts.items():
        L["pat_%s_%s" % (name, part)] = body
# eye colour (iris) for the open-eyed faces, and a lion's mane behind the head
L["iris_normal"] = H(both(circ(98, 112, 10.5) ) + both('<circle cx="98" cy="113" r="5.5" fill="%s"/><circle cx="94.5" cy="107.5" r="3.8" fill="#fff"/><circle cx="101" cy="116" r="1.7" fill="#fff"/>' % INK))
L["iris_focus"] = H(both(circ(98, 114, 9) + '<circle cx="98" cy="115" r="4.8" fill="%s"/><circle cx="95" cy="110.5" r="3" fill="#fff"/>' % INK) + both(line("M 84 100 L 110 106", 4)))
mane = "".join('<circle cx="%.1f" cy="%.1f" r="26" fill="%s" stroke="%s" stroke-width="5"/>' % (128 + math.cos(a) * 96, 104 + math.sin(a) * 82, PT, INK)
               for a in [k * 2 * math.pi / 18 for k in range(18)] if not (1.05 < a < 2.1))
L["mane"] = H(mane)

for name, body in L.items():
    with open(os.path.join(OUT, name + ".svg"), "w") as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">%s<g transform="translate(0 16)">%s</g></svg>' % (CLIPS, body))
subprocess.check_call(["node", os.path.join(os.path.dirname(__file__), "render_svg.js"), OUT, "512"])

# ---- preview sheet
def layer(n, c=None):
    im = Image.open(os.path.join(OUT, n + ".png")).convert("RGBA")
    if c is None: return im
    out = ImageChops.multiply(im, Image.new("RGBA", im.size, tuple(int(v * 255) for v in c) + (255,)))
    out.putalpha(im.getchannel("A")); return out
def cat(fur, gear={}, lp="down", rp="down"):
    c = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    def put(n, col=None): c.alpha_composite(layer(n, col))
    stripe = tuple(v * 0.8 for v in fur)
    put("body_t", fur); put("body_marks_t", stripe); put("belly"); put("body_line")
    if "chest" in gear: put("chest_a_t", gear["chest"][0]); put("chest_b_t", gear["chest"][1])
    put("head_t", fur); put("head_marks_t", stripe); put("face")
    if "helm" in gear: put("helm_a_t", gear["helm"][0]); put("helm_b_t", gear["helm"][1])
    put("desk")
    if "sword" in gear and rp == "down": put("sword_a_t", gear["sword"][0]); put("sword_b_t", gear["sword"][1])
    if "tf" in gear and rp == "down": put("tf"); put("tf_fx%d" % gear["tf"])
    for side, pose in (("L", lp), ("R", rp)):
        put("paw_%s_%s_t" % (side, pose), fur); put("paw_%s_%s" % (side, pose))
    if "shield" in gear and lp == "down": put("shield_a_t", gear["shield"][0]); put("shield_b_t", gear["shield"][1])
    return c
if len(sys.argv) > 2:
    ORANGE, GREY, BLACK = (1, .72, .42), (.78, .78, .8), (.42, .4, .46)
    STEEL, GOLD, RED, BLUE, PURPLE = (.82, .86, .95), (1, .8, .35), (.85, .25, .25), (.3, .45, .85), (.65, .4, .95)
    war = {"helm": (STEEL, GOLD), "chest": (STEEL, GOLD), "sword": (STEEL, (.6, .4, .25)), "shield": (RED, GOLD)}
    sheet = [("Orange tabby", cat(ORANGE, {}, "up", "down")), ("Grey tabby", cat(GREY, {}, "down", "up")),
             ("Warrior gear", cat(ORANGE, war)), ("Epic set", cat(BLACK, {"helm": (PURPLE, GOLD), "chest": (PURPLE, GOLD), "sword": ((.6, .9, 1), (.3, .2, .3)), "shield": ((.35, .25, .55), GOLD)})),
             ("Thunderfury 1", cat(GREY, {"helm": (STEEL, GOLD), "chest": (STEEL, GOLD), "tf": 1, "shield": (BLUE, GOLD)})),
             ("Thunderfury 2", cat(ORANGE, {"tf": 2}, "up", "down"))]
    S = 300
    out = Image.new("RGBA", (S * 3, (S + 30) * 2), (245, 236, 226, 255)); d = ImageDraw.Draw(out)
    for i, (t, im) in enumerate(sheet):
        x, y = (i % 3) * S, (i // 3) * (S + 30)
        out.alpha_composite(im.resize((S - 20, S - 20), Image.LANCZOS), (x + 10, y + 34)); d.text((x + 12, y + 10), t, fill=(120, 70, 40, 255))
    out.save(sys.argv[2])
