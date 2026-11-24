#!/usr/bin/env python3
"""(1.6.8) Builds only the cat's tapping faces (face_tap1..10) and petting faces (face_pet1..10) from tools/make_vector.py into
Art/v/c_face_tap*.tga and their VectorData.lua lines, the same way tools/build_vector_art.py does
for every layer, without rebuilding all the other art. A full build_vector_art.py run makes them too.
usage: python3 tools/make_faces.py [work_dir]"""
import os, re, subprocess, sys, tempfile
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from make_art import write_tga

WORK = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
subprocess.check_call([sys.executable, os.path.join(HERE, "make_vector.py"), WORK])
OUT = os.path.join(ROOT, "Art", "v")


def pow2(n):
    p = 8
    while p < n: p *= 2
    return p


lines = {}
for n in ["face_tap%d" % i for i in range(1, 11)] + ["face_pet%d" % i for i in range(1, 11)]:
    im = Image.open(os.path.join(WORK, n + ".png")).convert("RGBA")
    x0, y0, x1, y1 = im.getbbox()
    w, h = x1 - x0, y1 - y0
    tw, th = pow2(w), pow2(h)
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    canvas.paste(im.crop((x0, y0, x1, y1)), (0, 0))
    write_tga(canvas, os.path.join(OUT, "c_" + n + ".tga"))
    lines["cat:" + n] = 'V["cat:%s"]={"c_%s",%d,%d,%d,%d,%.4f,%.4f,"cat"}' % (n, n, x0, y0, w, h, w / tw, h / th)

# VectorData.lua: replace or add these lines, keeping the file sorted by key
path = os.path.join(ROOT, "VectorData.lua")
src = open(path).read().split("\n")
head = [l for l in src if not l.startswith('V["')]
body = {re.match(r'V\["([^"]+)"\]', l).group(1): l for l in src if l.startswith('V["')}
body.update(lines)
header = [l for l in head if l != ""]
with open(path, "w") as f:
    f.write("\n".join(header) + "\n")
    for k in sorted(body): f.write(body[k] + "\n")
print("wrote %d faces" % len(lines))
