#!/usr/bin/env python3
"""
Proof of concept: pre-rendered 3D cat + gear layers made in Blender (bpy).

Builds a stylized sitting cat (same front-facing pose as the pixel cat) and a
few gear pieces, then renders every part as its own transparent, greyscale
layer from one fixed camera, so the addon can stack and tint them exactly like
the pixel layers. Parts hidden behind other parts are masked (holdout), so a
helm correctly tucks behind the ears and a sword sits in the paw.

Run with Blender's Python:  <venv>/bin/python tools/render3d.py <out-dir>
"""
import math, os, sys
import bpy
from mathutils import Vector

OUT = sys.argv[1] if len(sys.argv) > 1 else "render3d_out"
os.makedirs(OUT, exist_ok=True)
RES = 256

# ------------------------------------------------------------------ scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 48
scene.cycles.use_denoising = False
scene.render.resolution_x = scene.render.resolution_y = RES
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "Standard"
scene.render.use_freestyle = True
scene.render.line_thickness_mode = "ABSOLUTE"
scene.render.line_thickness = 1.6

world = bpy.data.worlds.new("World"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.55, 0.6, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.9

cam_data = bpy.data.cameras.new("Cam"); cam_data.type = "ORTHO"; cam_data.ortho_scale = 3.2
cam = bpy.data.objects.new("Cam", cam_data); scene.collection.objects.link(cam)
cam.location = (0, -10, 0.25); cam.rotation_euler = (math.radians(90), 0, 0)
scene.camera = cam

sun = bpy.data.lights.new("Sun", "SUN"); sun.energy = 3.2; sun.angle = math.radians(25)
sun_o = bpy.data.objects.new("Sun", sun); scene.collection.objects.link(sun_o)
sun_o.rotation_euler = (math.radians(55), math.radians(-30), math.radians(-25))
rim = bpy.data.lights.new("Rim", "SUN"); rim.energy = 2.2
rim_o = bpy.data.objects.new("Rim", rim); scene.collection.objects.link(rim_o)
rim_o.rotation_euler = (math.radians(-60), math.radians(40), math.radians(160))

# ------------------------------------------------------------------ helpers
COLL = {}
def coll(name):
    if name not in COLL:
        c = bpy.data.collections.new(name); scene.collection.children.link(c); COLL[name] = c
    return COLL[name]

MATS = {}
def mat(name, rgb, rough=0.6, metal=0.0, toon=True):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if toon:
        # cel-shaded look: mostly flat toon shading with a little soft light
        t = nt.nodes.new("ShaderNodeBsdfToon"); t.inputs["Color"].default_value = (*rgb, 1)
        t.inputs["Size"].default_value = 0.75; t.inputs["Smooth"].default_value = 0.12
        mix = nt.nodes.new("ShaderNodeMixShader"); mix.inputs["Fac"].default_value = 0.35
        nt.links.new(t.outputs[0], mix.inputs[1]); nt.links.new(b.outputs[0], mix.inputs[2])
        out = nt.nodes["Material Output"]; nt.links.new(mix.outputs[0], out.inputs["Surface"])
    MATS[name] = m
    return m

def place(obj, layer, material):
    for c in obj.users_collection: c.objects.unlink(obj)
    coll(layer).objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.select_set(False)
    return obj

def blob(layer, material, family, elements, threshold=0.6):
    """A soft organic shape from metaballs. elements: (co, radius, (sx, sy, sz) or None)."""
    mb = bpy.data.metaballs.new(family); mb.resolution = 0.03; mb.render_resolution = 0.015; mb.threshold = threshold
    for co, r, size in elements:
        e = mb.elements.new()
        e.co = co; e.radius = r
        if size: e.type = "ELLIPSOID"; e.size_x, e.size_y, e.size_z = size
    o = bpy.data.objects.new(family, mb)
    coll(layer).objects.link(o)
    mb.materials.append(material)
    return o

def tube(layer, material, points, radius, taper=None, order=4):
    """A smooth tube through points (tails, horns), optionally tapering to a point."""
    cu = bpy.data.curves.new("tube", "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("NURBS"); sp.points.add(len(points) - 1)
    for i, p in enumerate(points): sp.points[i].co = (*p, 1)
    sp.use_endpoint_u = True; sp.order_u = min(order, len(points))
    cu.bevel_depth = radius; cu.bevel_resolution = 6; cu.use_fill_caps = True
    if taper:
        for i, w in enumerate(taper): sp.points[i].radius = w
    o = bpy.data.objects.new("tube", cu); coll(layer).objects.link(o)
    cu.materials.append(material)
    return o

def sphere(layer, material, loc, scale, r=1.0, seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.active_object; o.scale = scale
    return place(o, layer, material)

def cone(layer, material, loc, r1, r2, depth, rot):
    bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
    return place(bpy.context.active_object, layer, material)

def cyl(layer, material, loc, r, depth, rot, verts=40):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    return place(bpy.context.active_object, layer, material)

def cube(layer, material, loc, scale, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.scale = scale
    return place(o, layer, material)

def torus(layer, material, loc, major, minor, rot=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, location=loc, rotation=rot,
                                     major_segments=64, minor_segments=16)
    o = bpy.context.active_object; o.scale = scale
    return place(o, layer, material)

# greyscale materials so the addon can tint each layer (like the pixel art)
FUR = mat("fur", (0.92, 0.92, 0.92), 0.9)
METAL_A = mat("metalA", (0.85, 0.85, 0.85), 0.35, 0.6)
METAL_B = mat("metalB", (0.85, 0.85, 0.85), 0.3, 0.8)
WOOD = mat("wood", (0.8, 0.8, 0.8), 0.8)
# face details keep their own colours
EYE = mat("eye", (0.02, 0.02, 0.03), 0.1, toon=False)
WHITE = mat("white", (1, 1, 1), 0.3)
PINK = mat("pink", (1.0, 0.55, 0.65), 0.6)
BLUSH = mat("blush", (1.0, 0.45, 0.6), 0.6, toon=False)
PAD = mat("pad", (0.95, 0.95, 0.95), 0.7)

# ------------------------------------------------------------------ cat (soft chibi shape from metaballs)
HEAD_Z = 0.85
blob("fur", FUR, "Body", [
    ((0, 0.1, -0.4), 1.0, (0.9, 0.66, 0.72)),          # body
    ((0, -0.05, HEAD_Z), 1.0, (0.86, 0.68, 0.66)),      # head
    ((0.62, -0.2, HEAD_Z - 0.22), 0.45, None),          # cheek fluff
    ((-0.62, -0.2, HEAD_Z - 0.22), 0.45, None),
    ((0, -0.42, 0.18), 0.5, (1.0, 0.6, 0.7)),           # chest fluff
])
tube("fur", FUR, [(0.6, 0.4, -0.85), (0.95, 0.2, -0.85), (1.05, -0.15, -0.65), (0.95, -0.3, -0.45)], 0.075,
     taper=[1.0, 1.0, 0.95, 0.8])                        # tail curling round the side
for sx in (-1, 1):
    cone("fur", FUR, (sx * 0.55, 0.0, HEAD_Z + 0.6), 0.27, 0.04, 0.56, (math.radians(-6), math.radians(sx * 24), 0))
    cone("face", PINK, (sx * 0.54, -0.14, HEAD_Z + 0.56), 0.16, 0.02, 0.38, (math.radians(-6), math.radians(sx * 24), 0))
    sphere("face", EYE, (sx * 0.32, -0.66, HEAD_Z + 0.02), (0.11, 0.05, 0.15))           # big glossy eyes
    sphere("face", WHITE, (sx * 0.32 - 0.035, -0.71, HEAD_Z + 0.08), (0.035, 0.02, 0.045))
    sphere("face", WHITE, (sx * 0.32 + 0.03, -0.71, HEAD_Z - 0.05), (0.018, 0.01, 0.022))
    sphere("face", BLUSH, (sx * 0.55, -0.56, HEAD_Z - 0.17), (0.12, 0.03, 0.06))        # blush
sphere("face", PINK, (0, -0.74, HEAD_Z - 0.13), (0.06, 0.03, 0.04))                     # nose
bpy.ops.object.text_add(location=(0, -0.76, HEAD_Z - 0.27), rotation=(math.radians(90), 0, 0))
mouth = bpy.context.active_object; mouth.data.body = "w"; mouth.data.align_x = "CENTER"; mouth.data.align_y = "CENTER"
mouth.data.size = 0.22; mouth.data.extrude = 0.01
bpy.ops.object.convert(target="MESH"); place(bpy.context.active_object, "face", EYE)

# paws: down = resting on the ground in front with toes, up = a soft raised arm
for side, sx in (("R", 1), ("L", -1)):
    fam = "Paw" + side
    blob("paw_%s_down_a" % side, FUR, fam + "d", [
        ((sx * 0.5, -0.58, -0.8), 0.6, (0.42, 0.34, 0.22)),
        ((sx * 0.5 - 0.11, -0.78, -0.82), 0.2, None), ((sx * 0.5, -0.81, -0.82), 0.2, None), ((sx * 0.5 + 0.11, -0.78, -0.82), 0.2, None),
    ])
    for k in (-1, 0, 1):
        sphere("paw_%s_down_b" % side, PAD, (sx * 0.5 + k * 0.11, -0.9, -0.86), (0.04, 0.02, 0.03))
    blob("paw_%s_up_a" % side, FUR, fam + "u", [
        ((sx * 0.6, -0.1, -0.2), 0.3, None),     # shoulder
        ((sx * 0.8, -0.25, 0.0), 0.27, None),     # forearm
        ((sx * 0.95, -0.36, 0.22), 0.5, (0.34, 0.28, 0.36)),  # paw
    ])
    sphere("paw_%s_up_b" % side, PAD, (sx * 0.96, -0.6, 0.18), (0.1, 0.03, 0.08))
    for k in (-1, 0, 1):
        sphere("paw_%s_up_b" % side, PAD, (sx * 0.96 + k * 0.08, -0.6, 0.33), (0.035, 0.02, 0.035))

# ------------------------------------------------------------------ gear (grey, tinted in game)
# great helm: dome (a) with brim, nose guard and horns (b)
helm = sphere("helm_a", METAL_A, (0, -0.05, HEAD_Z + 0.1), (0.95, 0.8, 0.72))
bpy.context.view_layer.objects.active = helm
bpy.ops.object.modifier_add(type="BOOLEAN")
cutter = cube("cut", METAL_A, (0, 0, HEAD_Z - 0.55), (3, 3, 1.0)); cutter.hide_render = True
helm.modifiers[-1].object = cutter; helm.modifiers[-1].operation = "DIFFERENCE"
torus("helm_b", METAL_B, (0, -0.05, HEAD_Z + 0.0), 0.93, 0.055, (0, 0, 0), (1, 0.82, 1))
cube("helm_b", METAL_B, (0, -0.8, HEAD_Z + 0.25), (0.07, 0.05, 0.5))
for sx in (-1, 1):
    tube("helm_b", METAL_B, [(sx * 0.8, -0.05, HEAD_Z + 0.25), (sx * 1.15, -0.05, HEAD_Z + 0.45),
                             (sx * 1.25, -0.05, HEAD_Z + 0.8), (sx * 1.12, -0.05, HEAD_Z + 1.05)], 0.11,
         taper=[1.0, 0.8, 0.45, 0.05])

# plate chest: a breastplate on the front of the body (a), pauldrons and belt (b)
sphere("chest_a", METAL_A, (0, -0.12, -0.4), (0.68, 0.5, 0.55))
for k, z in enumerate((-0.25, -0.45)):                    # plate lames
    torus("chest_b", METAL_B, (0, -0.12, z), 0.62 - k * 0.02, 0.025, (0, 0, 0), (1, 0.75, 1))
torus("chest_b", METAL_B, (0, 0.05, -0.72), 0.7, 0.05, (0, 0, 0), (1, 0.75, 1))
for sx in (-1, 1):
    sphere("chest_b", METAL_B, (sx * 0.68, 0.0, 0.05), (0.3, 0.28, 0.2))

# sword gripped in the right paw (resting pose): blade (a), guard, grip and pommel (b)
def along(g, a, d):  # point d along a direction tilted a degrees right of vertical
    r = math.radians(a)
    return (g[0] + math.sin(r) * d, g[1], g[2] + math.cos(r) * d)
G, A = (0.5, -0.85, -0.72), 22
rot = (0, math.radians(A), 0)
blade = cube("sword_a", METAL_A, along(G, A, 0.9), (0.1, 0.03, 1.1), rot)
bpy.context.view_layer.objects.active = blade
bpy.ops.object.modifier_add(type="BEVEL"); blade.modifiers[-1].width = 0.012; blade.modifiers[-1].segments = 2
cone("sword_a", METAL_A, along(G, A, 1.55), 0.07, 0.0, 0.22, rot)       # point
cube("sword_b", METAL_B, along(G, A, 0.3), (0.42, 0.06, 0.07), rot)
cyl("sword_b", WOOD, along(G, A, 0.12), 0.05, 0.3, rot)
sphere("sword_b", METAL_B, along(G, A, -0.06), (0.08, 0.08, 0.08))

# ------------------------------------------------------------------ signature item lookalike: Thunderfury
# Not Blizzard's model: a chibi lookalike built from its well-known traits (long silver blade with a
# glowing blue core, swept golden wings at the guard, blue gems, crackling lightning). Full colour, untinted.
def glow(name, rgb, strength):
    m = mat(name, rgb, 0.3, 0.0, toon=False)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*rgb, 1); b.inputs["Emission Strength"].default_value = strength
    return m
TF_STEEL = mat("tfSteel", (0.78, 0.88, 1.0), 0.25, 0.6)
TF_GOLD = mat("tfGold", (1.0, 0.76, 0.25), 0.3, 0.8)
TF_GRIP = mat("tfGrip", (0.12, 0.2, 0.5), 0.6)
TF_CORE = glow("tfCore", (0.35, 0.75, 1.0), 2.5)
TF_BOLT = glow("tfBolt", (0.6, 0.9, 1.0), 6.0)
def side(g, a, d, off, y=0.0):  # along the blade by d, then sideways by off
    r = math.radians(a); x, yy, z = along(g, a, d)
    return (x + math.cos(r) * off, yy + y, z - math.sin(r) * off)
TA = 22
trot = (0, math.radians(TA), 0)
tb = cube("tf", TF_STEEL, along(G, TA, 1.0), (0.14, 0.03, 1.3), trot)
bpy.context.view_layer.objects.active = tb
bpy.ops.object.modifier_add(type="BEVEL"); tb.modifiers[-1].width = 0.02; tb.modifiers[-1].segments = 2
cone("tf", TF_STEEL, along(G, TA, 1.78), 0.085, 0.0, 0.26, trot)                 # point
cube("tf", TF_CORE, side(G, TA, 1.0, 0, -0.035), (0.05, 0.01, 1.1), trot)        # glowing core
for sx in (-1, 1):                                                                # swept wings
    for k, (reach, rise, w) in enumerate(((0.42, 0.45, 0.07), (0.32, 0.3, 0.05))):
        tube("tf", TF_GOLD, [side(G, TA, 0.32, 0.05 * sx, -0.02), side(G, TA, 0.3 + rise * 0.2, (reach * 0.8) * sx, -0.02),
                             side(G, TA, 0.32 + rise * 0.7, reach * sx, -0.02), side(G, TA, 0.32 + rise, (reach * 0.75) * sx, -0.02)],
             w, taper=[1.0, 1.0, 0.6, 0.05])
sphere("tf", TF_GOLD, side(G, TA, 0.3, 0, -0.02), (0.14, 0.07, 0.11))              # guard centre
sphere("tf", TF_CORE, side(G, TA, 0.3, 0, -0.09), (0.07, 0.04, 0.07))             # guard gem
cyl("tf", TF_GRIP, along(G, TA, 0.12), 0.055, 0.32, trot)
for d in (0.02, 0.12, 0.22): torus("tf", TF_GOLD, along(G, TA, d), 0.058, 0.012, trot)
sphere("tf", TF_GOLD, along(G, TA, -0.07), (0.09, 0.09, 0.09))
sphere("tf", TF_CORE, side(G, TA, -0.07, 0, -0.07), (0.045, 0.03, 0.045))
import random
for frame in (1, 2):                                                              # two lightning frames to flip between
    random.seed(frame * 7)
    for arc in range(2):
        d0 = 0.55 + arc * 0.55 + random.random() * 0.2; sgn = 1 if (arc + frame) % 2 else -1; pts = []
        for k in range(4):
            pts.append(side(G, TA, d0 + k * 0.14, sgn * (0.1 + (k % 2) * 0.12 + random.random() * 0.04), -0.08))
        tube("tf_fx%d" % frame, TF_BOLT, pts, 0.02, taper=[0.4, 1.0, 1.0, 0.3], order=2)

# round shield on the left paw: face (a), rim and boss (b)
cyl("shield_a", WOOD, (-0.7, -0.95, -0.45), 0.46, 0.08, (math.radians(90), 0, 0), 64)
torus("shield_b", METAL_B, (-0.7, -1.0, -0.45), 0.46, 0.05, (math.radians(90), 0, 0))
sphere("shield_b", METAL_B, (-0.7, -1.03, -0.45), (0.13, 0.08, 0.13))

# ------------------------------------------------------------------ rendering per layer
lineset = scene.view_layers[0].freestyle_settings.linesets.new("outline")
lineset.select_by_collection = True
lineset.select_by_visibility = True
lineset.linestyle.color = (0.12, 0.09, 0.14)
lineset.linestyle.thickness = 1.6

def render_layer(name, occluders):
    for cname, c in COLL.items():
        for o in c.objects:
            if cname == "cut": continue
            o.hide_render = not (cname == name or cname in occluders)
            o.is_holdout = cname in occluders
    lineset.collection = COLL[name]
    lineset.show_render = not name.startswith("tf_fx")
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name)

BODY = ["fur"]
layers = [
    ("fur", []),
    ("face", ["fur"]),
    ("paw_R_down_a", BODY), ("paw_R_down_b", BODY + ["paw_R_down_a"]),
    ("paw_L_down_a", BODY), ("paw_L_down_b", BODY + ["paw_L_down_a"]),
    ("paw_R_up_a", BODY), ("paw_R_up_b", BODY + ["paw_R_up_a"]),
    ("paw_L_up_a", BODY), ("paw_L_up_b", BODY + ["paw_L_up_a"]),
    ("chest_a", ["fur"]), ("chest_b", ["chest_a"]),
    ("helm_a", ["face"]), ("helm_b", ["helm_a"]),
    ("sword_a", []), ("sword_b", ["sword_a"]),
    ("tf", []), ("tf_fx1", []), ("tf_fx2", []),
    ("shield_a", []), ("shield_b", ["shield_a"]),
]
for name, occ in layers:
    render_layer(name, occ)
