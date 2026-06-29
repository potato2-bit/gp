#!/usr/bin/env python3
"""
make_pvbot_3d_dxf.py
Best-effort 3D DXF of the rail-guided TEC PV-cleaning robot + rail/panel
scene, built as faceted MESH entities (ezdxf does not write licensed ACIS
solids, so boxes and cylinders are emitted as closed triangulated meshes).
Opens in AutoCAD 2026 (MESH), LibreCAD/QCAD (3D view), FreeCAD.

Geometry and layer scheme mirror cad/3d/pvbot_3d_assembly.scr and
cad/3d/rail_and_panel_3d.scr. Units: millimetres. Frame: +X fall-line,
+Y brush axis, +Z up; deck top at z=0, glass plane at z=-50.

Basis: output/rail_guided_design.json + gazebo/pvbot_description/pvbot.urdf.
Run:  python cad/3d/make_pvbot_3d_dxf.py
Out:  cad/3d/pvbot_3d.dxf
"""
import math
import os
import ezdxf
from ezdxf.render import MeshBuilder

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "pvbot_3d.dxf")

doc = ezdxf.new("R2018")
msp = doc.modelspace()

# ---- layers: name -> AutoCAD Color Index (match the .scr files) ----
LAYERS = {
    "CHASSIS": 8, "FRAME": 9, "TEC_COLD": 4, "TEC_TILE": 1,
    "TEC_SINK": 254, "TEC_FAN": 250, "TANK": 150, "BRUSH": 51,
    "SPRAY": 130, "NOZZLE": 42, "DRIVE": 30, "WHEEL": 250,
    "GLASS": 140, "PFRAME": 8, "POST": 18, "RAIL": 5, "RACK": 30,
    "STOP": 1, "TEXT": 7,
}
for name, col in LAYERS.items():
    if name not in doc.layers:
        doc.layers.add(name, color=col)


def add_mesh(mb, layer):
    mb.render_mesh(msp, dxfattribs={"layer": layer})


def box(p1, p2, layer):
    """Axis-aligned box from corner p1 to corner p2 as a closed MESH."""
    (x0, y0, z0), (x1, y1, z1) = p1, p2
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    mb = MeshBuilder()
    v = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    f = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    for face in f:
        mb.add_face([v[i] for i in face])
    add_mesh(mb, layer)


def cylinder(base, radius, height, axis, layer, n=24):
    """Closed faceted cylinder. axis in {'x','y','z'} from base point,
    extruded by +height along that axis."""
    bx, by, bz = base
    ring0, ring1 = [], []
    for k in range(n):
        a = 2 * math.pi * k / n
        c, s = radius * math.cos(a), radius * math.sin(a)
        if axis == "z":
            ring0.append((bx + c, by + s, bz))
            ring1.append((bx + c, by + s, bz + height))
        elif axis == "y":
            ring0.append((bx + c, by, bz + s))
            ring1.append((bx + c, by + height, bz + s))
        else:  # x
            ring0.append((bx, by + c, bz + s))
            ring1.append((bx + height, by + c, bz + s))
    mb = MeshBuilder()
    for k in range(n):
        k2 = (k + 1) % n
        mb.add_face([ring0[k], ring0[k2], ring1[k2], ring1[k]])
    # caps (fan triangulation)
    for k in range(1, n - 1):
        mb.add_face([ring0[0], ring0[k], ring0[k + 1]])
        mb.add_face([ring1[0], ring1[k + 1], ring1[k]])
    add_mesh(mb, layer)


def txt(s, pos, h, layer):
    msp.add_text(s, height=h, dxfattribs={"layer": layer}).set_placement(pos)


# ===================== ROBOT (pvbot_3d_assembly) =====================
# 1. chassis plate 400 x 300 x 10, top at z=0
box((-200, -150, -10), (200, 150, 0), "CHASSIS")

# 2. TEC AWG module (centre x=-75)
box((-160, -115, 6), (10, 115, 18), "TEC_COLD")          # cold plate
for (cx, cy) in [(-43, 55), (-43, -55), (-108, 55), (-108, -55)]:
    box((cx - 10, cy - 20, 20), (cx + 10, cy + 20, 26), "TEC_TILE")  # 4 tiles
box((-160, -115, 31), (10, 115, 49), "TEC_SINK")          # sink base
for fx in (-145, -117, -89, -61, -33, -5):                # 6 fins
    box((fx - 6, -110, 49), (fx + 6, 110, 99), "TEC_SINK")
cylinder((-75, 58, 108), 36, 12, "z", "TEC_FAN")          # 2 fans
cylinder((-75, -58, 108), 36, 12, "z", "TEC_FAN")

# 3. water tank 3.6 L (front)
box((-8, -113, 0), (158, 113, 70), "TANK")

# 4. full-width brush roller 0.96 m, core r25 + bristle shell r40, axis Y
cylinder((220, -480, -50), 40, 960, "y", "BRUSH")         # bristle shell
cylinder((220, -480, -50), 25, 960, "y", "BRUSH")         # core

# 5. spray bar r6 axis Y + 9 nozzles
cylinder((170, -480, -35), 6, 960, "y", "SPRAY")
for ny in (400, 300, 200, 100, 0, -100, -200, -300, -400):
    cylinder((170, ny, -44), 9, 18, "z", "NOZZLE")

# 6. carriage side-frames + V-groove wheels
box((-160, 150, -60), (160, 170, 10), "FRAME")
box((-160, 490, -60), (160, 510, 10), "FRAME")
box((-160, 150, -60), (-130, 510, -40), "FRAME")
box((130, 150, -60), (160, 510, -40), "FRAME")
box((-160, -170, -60), (160, -150, 10), "FRAME")
box((-160, -510, -60), (160, -490, 10), "FRAME")
box((-160, -510, -60), (-130, -150, -40), "FRAME")
box((130, -510, -60), (160, -150, -40), "FRAME")
for (wx, wy) in [(-130, 500), (130, 500), (-130, -500), (130, -500)]:
    cylinder((wx, wy, -52), 12, 16, "z", "WHEEL")

# 7. rack-and-pinion drive (left rail)
cylinder((-150, 425, -30), 14, 78, "y", "DRIVE")          # motor body
cylinder((-150, 503, -30), 15, 12, "y", "DRIVE")          # pinion D30

# ===================== PANEL + RAILS (rail_and_panel) ================
box((-1000, -500, -54), (1000, 500, -50), "GLASS")        # glass 2.0x1.0 m
box((-1000, -500, -89), (1000, -465, -50), "PFRAME")
box((-1000, 465, -89), (1000, 500, -50), "PFRAME")
box((-1000, -500, -89), (-965, 500, -50), "PFRAME")
box((965, -500, -89), (1000, 500, -50), "PFRAME")
for (px, py) in [(-875, -425), (875, -425), (-875, 425), (875, 425)]:
    box((px - 25, py - 25, -650), (px + 25, py + 25, -89), "POST")
# rails 2 x 2400 (no V-rib here; the box reads as the 2040 section)
box((-1200, 500, -50), (1200, 520, -10), "RAIL")
box((-1200, -520, -50), (1200, -500, -10), "RAIL")
# rack strips 2 x 2400
box((-1200, 496, -36), (1200, 500, -24), "RACK")
box((-1200, -500, -36), (1200, -496, -24), "RACK")
# end stops
box((-1210, 496, -50), (-1180, 524, -2), "STOP")
box((1180, 496, -50), (1210, 524, -2), "STOP")
box((-1210, -524, -50), (-1180, -496, -2), "STOP")
box((1180, -524, -50), (1210, -496, -2), "STOP")

# ---- title text ----
txt("RAIL-GUIDED TEC PV-CLEANING ROBOT - 3D MESH MODEL", (-1000, -580, -50), 30, "TEXT")
txt("REE598 GRADUATION PROJECT  2026-06-13  UNITS MM  CARRIAGE 8.0 kg",
    (-1000, -625, -50), 22, "TEXT")
txt("BASIS: output/rail_guided_design.json + gazebo/pvbot.urdf",
    (-1000, -665, -50), 22, "TEXT")

doc.saveas(OUT)
print("wrote", OUT)

# audit
try:
    auditor = doc.audit()
    print("audit errors:", len(auditor.errors), " fixes:", len(auditor.fixes))
except Exception as e:  # noqa
    print("audit skipped:", e)
