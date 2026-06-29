#!/usr/bin/env python
"""Render the 3-step demo simulation from a FRONT-SIDE ISOMETRIC view, with clear
part labels. Reuses the scene geometry from integration/build_demo.py. Outputs
exhibition/story1.png (harvest), story2.png (clean), story3.png (done) + a montage.
"""
import sys, os, math
import numpy as np
sys.path.insert(0, r"C:/Users/rizk/Desktop/GRADUATION PROJECT/integration")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import proj3d
import build_demo as bd

OUT = r"C:/Users/rizk/Desktop/GRADUATION PROJECT/exhibition"
ELEV, AZIM = 24, 125          # front-side isometric
NAVY = "#0B2A4A"

def setup(ax):
    ax.clear(); ax.set_box_aspect((1, 1, 0.62))
    ax.set_xlim(-1.7, 1.3); ax.set_ylim(-1.0, 1.0); ax.set_zlim(0, 1.45)
    try: ax.set_proj_type('ortho')
    except Exception: pass
    ax.view_init(elev=ELEV, azim=AZIM); ax.set_axis_off()
    gx, gy = np.meshgrid([-1.7, 1.3], [-1.0, 1.0])
    ax.plot_surface(gx, gy, np.zeros_like(gx), color=(0.82, 0.82, 0.85),
                    alpha=0.45, zorder=0)

def label(ax, xyz, text, xytext, ha='left', color=NAVY):
    x2, y2, _ = proj3d.proj_transform(xyz[0], xyz[1], xyz[2], ax.get_proj())
    ax.annotate(text, xy=(x2, y2), xycoords='data', xytext=xytext,
                textcoords='axes fraction', fontsize=12.5, ha=ha, va='center',
                fontweight='bold', color=color,
                bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=color, lw=1.2, alpha=0.96),
                arrowprops=dict(arrowstyle='-', color=color, lw=1.3))

def carriage_xyz(s):
    cu = bd.carriage_u(s); s_loc = (cu - 0.5) * bd.PANEL_L
    return (s_loc * math.cos(bd.TILT), 0, bd.PZ0 + s_loc * math.sin(bd.TILT) + 0.18)

def draw_shot(ax, k, step, title):
    phase, wh, s, spray, clean, used = bd.timeline()[k]
    setup(ax); bd.draw_dock(ax, wh); bd.draw_panel_and_carriage(ax, s, spray, clean)
    ax.figure.canvas.draw()
    # part labels (leaders point inward from the margins)
    label(ax, (-1.05, 0, 0.92), "Solar-regenerated\nsilica-gel dock", (0.965, 0.86), ha='right')
    label(ax, (-1.02, 0, 0.16), "Water tank\n(fills from air)", (1.0, 0.30), ha='right')
    label(ax, (0.62, 0, 0.78), "PV panel (24° tilt)", (0.60, 0.97), ha='center')
    label(ax, (0.42, 0, 0.70), "clean", (0.30, 0.90), ha='center', color="#1b4f72")
    label(ax, (-0.35, 0, 0.36), "dusty", (0.05, 0.66), ha='left', color="#7a5a22")
    label(ax, carriage_xyz(s), "Cleaning head\n(spray + roller)", (0.03, 0.34), ha='left')
    label(ax, (0.0, 0.5, 0.55), "Guide rail", (0.50, 0.04), ha='center')
    # title + HUD
    ax.text2D(0.5, 1.03, title, transform=ax.transAxes, ha='center', va='bottom',
              fontsize=15, fontweight='bold', color=NAVY)
    ax.text2D(0.015, 0.15,
              f"tank {100*wh/bd.TANK_MAX:3.0f}%   panel cleaned {100*clean:3.0f}%   "
              f"water used {used:.1f} L / {bd.EVENT_L:.0f} L",
              transform=ax.transAxes, fontsize=10.5, family="monospace", va='bottom',
              bbox=dict(boxstyle="round,pad=0.4", fc="#EAF4FA", ec="#888", alpha=0.95))

SHOTS = [
    (25, "1", "Harvest — silica gel pulls water from the air, tank fills"),
    (40, "2", "Clean — the robot drives the rail, sprays 0.3 L/m² and wipes"),
    (54, "3", "Done — panel cleaned with the water it made (13 L)"),
]

# individual shots — fixed identical canvas so the 3 frames are uniform on the poster
for k, step, title in SHOTS:
    fig = plt.figure(figsize=(8.6, 6.8), dpi=150)
    ax = fig.add_axes([0.02, 0.04, 0.96, 0.88], projection='3d')
    draw_shot(ax, k, step, title)
    fig.savefig(os.path.join(OUT, f"story{step}.png"), dpi=150, facecolor='white')
    plt.close(fig)
    print("wrote story%s.png" % step)

# montage for review
fig = plt.figure(figsize=(20, 7), dpi=80)
for i, (k, step, title) in enumerate(SHOTS):
    ax = fig.add_subplot(1, 3, i+1, projection='3d')
    draw_shot(ax, k, step, title)
fig.savefig(os.path.join(OUT, "sim_montage.png"), dpi=80, bbox_inches='tight', facecolor='white')
print("wrote sim_montage.png")
