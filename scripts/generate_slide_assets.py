#!/usr/bin/env python3
"""
generate_slide_assets.py - figures for the thesis-defence deck.

Produces, in figures/slides/:
  sim_still_1..4.png   - four stills from the rail-guided cleaning sweep
  robot_3d.png         - 3D isometric of the rail-guided carriage on the panel
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT = "figures/slides"
os.makedirs(OUT, exist_ok=True)

# ---------- 1. stills from the cleaning animation ----------
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim_cleaning_demo as demo
for label, frac in [(1, 0.02), (2, 0.30), (3, 0.55), (4, 0.95)]:
    for k in range(int(demo.N * frac)):
        demo.update(k)
    demo.fig.savefig(f"{OUT}/sim_still_{label}.png", dpi=110, bbox_inches="tight")
    # reset dust between stills so each shows cumulative progress correctly
print("sim stills written")

# ---------- 2. 3D isometric of the rail-guided carriage ----------
TILT = np.deg2rad(24.0)


def Ry(p):
    c, s = np.cos(p), np.sin(p)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def box_faces(center, size):
    cx, cy, cz = center
    lx, ly, lz = np.array(size) / 2.0
    pts = np.array([[sx, sy, sz] for sx in (-lx, lx) for sy in (-ly, ly) for sz in (-lz, lz)])
    pts = pts + np.array([cx, cy, cz])
    idx = [[0,1,3,2],[4,5,7,6],[0,1,5,4],[2,3,7,6],[0,2,6,4],[1,3,7,5]]
    return [[pts[i] for i in f] for f in idx]


def on_panel(local_center, size, R, panel_origin):
    """place a box that sits on the tilted panel (local frame -> world)."""
    c = R @ np.array(local_center) + panel_origin
    faces = box_faces([0, 0, 0], size)
    faces = [[R @ np.array(v) + c for v in f] for f in faces]
    return faces


fig = plt.figure(figsize=(9, 6.2))
ax = fig.add_subplot(111, projection="3d")
R = Ry(-TILT)
origin = np.array([0, 0, 0.5])

# panel (2 x 1) glass
panel = box_faces([0, 0, 0], [2.0, 1.0, 0.04])
panel = [[R @ np.array(v) + origin for v in f] for f in panel]
ax.add_collection3d(Poly3DCollection(panel, facecolor="#23304a", edgecolor="#11203a", alpha=0.95))

# two guide rails along the slope
for yy in (-0.5, 0.5):
    rail = on_panel([0, yy, 0.05], [2.04, 0.04, 0.06], R, origin)
    ax.add_collection3d(Poly3DCollection(rail, facecolor="#555", edgecolor="#333"))

# support legs (vertical, world frame)
for lx in (0.88, -0.88):
    h = 0.88 if lx > 0 else 0.10
    for ly in (-0.42, 0.42):
        leg = box_faces([lx, ly, h / 2], [0.05, 0.05, h])
        ax.add_collection3d(Poly3DCollection(leg, facecolor="#3a3a3c", edgecolor="#222"))

# --- carriage at mid-panel ---
cpos = [0.1, 0, 0.13]            # local on panel, slightly up the slope
def part(local_dc, size, color, alpha=1.0, ec="k"):
    c0 = [cpos[0] + local_dc[0], cpos[1] + local_dc[1], cpos[2] + local_dc[2]]
    f = on_panel(c0, size, R, origin)
    ax.add_collection3d(Poly3DCollection(f, facecolor=color, edgecolor=ec, alpha=alpha))

part([0, 0, 0],        [0.34, 0.92, 0.08], "#8a8f99")        # chassis
part([-0.02, 0, 0.10], [0.17, 0.23, 0.10], "#7fd4ec", ec="#155e75")  # TEC module
# TEC fins
for fx in np.linspace(-0.06, 0.06, 5):
    part([-0.02 + fx, 0, 0.18], [0.008, 0.22, 0.05], "#cfd6dd", ec="#9aa")
part([0.06, 0, 0.08],  [0.14, 0.20, 0.07], "#2f73d9", 0.5, ec="#1b3a6b")  # tank
part([0.17, 0, -0.02], [0.04, 0.96, 0.08], "#f2f2e6", ec="#666")  # full-width brush
part([0.13, 0, -0.04], [0.012, 0.96, 0.02], "#b9892e")       # spray bar

ax.text(*(R @ np.array([cpos[0]-0.02, 0, 0.27]) + origin), "TEC AWG",
        fontsize=8, fontweight="bold", color="#0b3a47")
ax.text(*(R @ np.array([0.6, 0, 0.06]) + origin), "full-width brush + spray",
        fontsize=8, color="#333")
ax.text(*(R @ np.array([-0.7, 0.55, 0.10]) + origin), "guide rail", fontsize=8, color="#333")

ax.set_xlim(-1.2, 1.2); ax.set_ylim(-0.9, 0.9); ax.set_zlim(0, 1.4)
ax.set_box_aspect((2.4, 1.8, 1.4))
ax.view_init(elev=22, azim=-58)
ax.set_axis_off()
ax.set_title("Rail-guided TEC PV-cleaning carriage on a 24$^\\circ$ panel",
             fontsize=12, fontweight="bold")
fig.savefig(f"{OUT}/robot_3d.png", dpi=130, bbox_inches="tight")
print("robot_3d.png written")
print("done ->", OUT)
