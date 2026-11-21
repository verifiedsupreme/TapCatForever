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
PAD = mat("pad", (0.95, 0.95, 0.95), 0.7)

# ------------------------------------------------------------------ cat (chibi: big head, small body)
HEAD_Z = 0.85
sphere("fur", FUR, (0, 0.1, -0.35), (0.8, 0.62, 0.72))                   # body
sphere("fur", FUR, (0, -0.05, HEAD_Z), (0.9, 0.72, 0.72))               # head
for sx in (-1, 1):
    cone("fur", FUR, (sx * 0.55, 0.0, HEAD_Z + 0.62), 0.26, 0.03, 0.55, (math.radians(-6), math.radians(sx * 24), 0))
    cone("face", PINK, (sx * 0.54, -0.13, HEAD_Z + 0.58), 0.15, 0.02, 0.38, (math.radians(-6), math.radians(sx * 24), 0))
    sphere("face", EYE, (sx * 0.32, -0.68, HEAD_Z + 0.02), (0.11, 0.05, 0.15))           # big glossy eyes
    sphere("face", WHITE, (sx * 0.32 - 0.035, -0.73, HEAD_Z + 0.08), (0.035, 0.02, 0.045))
    sphere("face", WHITE, (sx * 0.32 + 0.03, -0.73, HEAD_Z - 0.05), (0.018, 0.01, 0.022))
    sphere("face", PINK, (sx * 0.55, -0.55, HEAD_Z - 0.16), (0.12, 0.03, 0.06))         # blush
sphere("face", PINK, (0, -0.76, HEAD_Z - 0.13), (0.06, 0.03, 0.04))                     # nose
bpy.ops.object.text_add(location=(0, -0.79, HEAD_Z - 0.27), rotation=(math.radians(90), 0, 0))
mouth = bpy.context.active_object; mouth.data.body = "w"; mouth.data.align_x = "CENTER"; mouth.data.align_y = "CENTER"
mouth.data.size = 0.22; mouth.data.extrude = 0.01
bpy.ops.object.convert(target="MESH"); place(bpy.context.active_object, "face", EYE)

# paws: down = resting on the ground in front, up = raised beside the body
for side, sx in (("R", 1), ("L", -1)):
    sphere("paw_%s_down_a" % side, FUR, (sx * 0.5, -0.6, -0.78), (0.26, 0.22, 0.16))
    for k in (-1, 0, 1):
        sphere("paw_%s_down_b" % side, PAD, (sx * 0.5 + k * 0.09, -0.81, -0.82), (0.035, 0.02, 0.03))
    sphere("paw_%s_up_a" % side, FUR, (sx * 0.98, -0.4, 0.2), (0.24, 0.2, 0.26))
    cyl("paw_%s_up_a" % side, FUR, (sx * 0.78, -0.2, -0.12), 0.15, 0.6, (0, math.radians(sx * -35), 0))
    sphere("paw_%s_up_b" % side, PAD, (sx * 0.98, -0.6, 0.17), (0.1, 0.03, 0.08))
    for k in (-1, 0, 1):
        sphere("paw_%s_up_b" % side, PAD, (sx * 0.98 + k * 0.08, -0.6, 0.32), (0.035, 0.02, 0.035))

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
    cone("helm_b", METAL_B, (sx * 0.92, -0.05, HEAD_Z + 0.5), 0.12, 0.02, 0.62, (0, math.radians(sx * 48), 0))

# plate chest: a breastplate on the front of the body (a), pauldrons and belt (b)
sphere("chest_a", METAL_A, (0, -0.12, -0.4), (0.68, 0.5, 0.55))
torus("chest_b", METAL_B, (0, 0.05, -0.72), 0.7, 0.05, (0, 0, 0), (1, 0.75, 1))
for sx in (-1, 1):
    sphere("chest_b", METAL_B, (sx * 0.68, 0.0, 0.05), (0.3, 0.28, 0.2))

# sword gripped in the right paw (resting pose): blade (a), guard, grip and pommel (b)
def along(g, a, d):  # point d along a direction tilted a degrees right of vertical
    r = math.radians(a)
    return (g[0] + math.sin(r) * d, g[1], g[2] + math.cos(r) * d)
G, A = (0.5, -0.85, -0.72), 22
rot = (0, math.radians(A), 0)
cube("sword_a", METAL_A, along(G, A, 0.95), (0.1, 0.025, 1.25), rot)
cube("sword_b", METAL_B, along(G, A, 0.3), (0.42, 0.06, 0.07), rot)
cyl("sword_b", WOOD, along(G, A, 0.12), 0.05, 0.3, rot)
sphere("sword_b", METAL_B, along(G, A, -0.06), (0.08, 0.08, 0.08))

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
    ("shield_a", []), ("shield_b", ["shield_a"]),
]
for name, occ in layers:
    render_layer(name, occ)
