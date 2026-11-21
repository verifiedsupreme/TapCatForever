"""Flat 2D vector cat (kawaii sticker style): thick brown outlines, flat fills, cream muzzle.

Writes one SVG per layer, renders them with tools/render_svg.js (Playwright/Chromium), and
composes a preview sheet. Layers ending in _t are greyscale and get tinted in game
(fur colour, gear colour); every other layer keeps its own colours. Outlines live in
untinted layers so they stay dark brown whatever the fur colour.

usage: python3 tools/make_vector.py <out_dir> [preview.png]
"""
import os, subprocess, sys
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
