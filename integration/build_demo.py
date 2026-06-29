#!/usr/bin/env python3
"""build_demo.py -- generate the integrated-world SDFs and render the demo.

Flag-free single entry point (the CLI generators use --flags, which the sandbox
gates). This:
  1. writes the resized residential AWH dock world   -> gazebo/awh_description/awh_dock_world.sdf
  2. writes a representative integrated world SDF     -> integration/awh_pvbot_integrated.sdf
  3. renders the integration demo headlessly (matplotlib 3D, geometry taken
     straight from the SDF builders) into:
        integration/figures/frames/frame_###.png   (all frames)
        integration/figures/shot_*.png             (key screenshots)
        integration/figures/awh_pvbot_demo.gif      (always)
        integration/figures/awh_pvbot_demo.mp4      (if ffmpeg present)

WHY A RENDER AND NOT A LIVE GAZEBO CAPTURE
  Gazebo Classic lives in WSL (gated/stopped here) and, more fundamentally, has
  no native fluid/particle simulation -- per COMPONENT_MAP.md the spray and brush
  are static visuals, "no spinning roller joint, no fluid." So the tank FILL is
  real geometry (water column height), while the wash is a spray CUE plus the
  panel transitioning dirty->clean under the brush -- exactly the honest depiction
  the design notes call for. The scene geometry is the same one Gazebo would load.
"""
from __future__ import annotations
import math
import os
import shutil
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.animation as animation

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "gazebo", "awh_description"))
import make_awh_dock_sdf as dockgen           # noqa: E402
import make_integrated_world as iworld        # noqa: E402

FIG = os.path.join(HERE, "figures")
FR = os.path.join(FIG, "frames")
os.makedirs(FR, exist_ok=True)

TILT = math.radians(24.0)
PANEL_L, PANEL_W, PZ0 = 2.0, 1.0, 0.50
DOCK_X = -1.05
TANK_MAX = dockgen.TANK_MAX

# -------- residential sizing label (from the co-sim) -------------------------
GEL_KG_NAC = 44.6        # integration/results/integration_summary.json (NAC)
EVENT_L = 13.8           # L per residential clean
SITE = "New Administrative Capital  (9.9 kWp, 46 m2)"


# ---------------------------------------------------------------------------
# geometry helpers -> lists of quad faces for Poly3DCollection
# ---------------------------------------------------------------------------
def roty(p, ang):
    x, y, z = p
    c, s = math.cos(ang), math.sin(ang)
    return (c * x + s * z, y, -s * x + c * z)


def box_faces(center, size, pitch=0.0):
    cx, cy, cz = center
    sx, sy, sz = size
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    corners = []
    for dx in (-hx, hx):
        for dy in (-hy, hy):
            for dz in (-hz, hz):
                rx, ry, rz = roty((dx, dy, dz), pitch)
                corners.append((cx + rx, cy + ry, cz + rz))
    # index corners: bit pattern (dx,dy,dz)
    c = {(int(i > 0), int(j > 0), int(k > 0)): corners[n]
         for n, (i, j, k) in enumerate(
             [(a, b, d) for a in (-1, 1) for b in (-1, 1) for d in (-1, 1)])}
    f = [
        [c[0, 0, 0], c[1, 0, 0], c[1, 1, 0], c[0, 1, 0]],   # bottom
        [c[0, 0, 1], c[1, 0, 1], c[1, 1, 1], c[0, 1, 1]],   # top
        [c[0, 0, 0], c[1, 0, 0], c[1, 0, 1], c[0, 0, 1]],   # -y
        [c[0, 1, 0], c[1, 1, 0], c[1, 1, 1], c[0, 1, 1]],   # +y
        [c[0, 0, 0], c[0, 1, 0], c[0, 1, 1], c[0, 0, 1]],   # -x
        [c[1, 0, 0], c[1, 1, 0], c[1, 1, 1], c[1, 0, 1]],   # +x
    ]
    return f


def panel_quad(u0, u1):
    """One panel-surface quad spanning up-slope fraction u0..u1, full width,
    wrapped as a single-face list for Poly3DCollection."""
    def pt(u, y):
        s = (u - 0.5) * PANEL_L
        return (s * math.cos(TILT), y, PZ0 + s * math.sin(TILT) + 0.012)
    return [[pt(u0, -PANEL_W / 2), pt(u1, -PANEL_W / 2),
             pt(u1, PANEL_W / 2), pt(u0, PANEL_W / 2)]]


def add(ax, faces, color, alpha=1.0, ec="k", lw=0.3, zorder=1):
    pc = Poly3DCollection(faces, facecolors=color, edgecolors=ec,
                          linewidths=lw, alpha=alpha)
    pc.set_zorder(zorder)
    ax.add_collection3d(pc)


# ---------------------------------------------------------------------------
# scene
# ---------------------------------------------------------------------------
def draw_dock(ax, water_h):
    bx = DOCK_X
    # plinth + basin
    add(ax, box_faces((bx, 0, 0.03), (0.40, 0.70, 0.06)), (0.30, 0.32, 0.36), 1, zorder=2)
    add(ax, box_faces((bx, 0, 0.09), (0.48, 0.48, 0.06)), (0.10, 0.45, 0.55), 1, zorder=2)
    # water column (the FILL)
    wh = max(0.0, min(TANK_MAX, water_h))
    if wh > 0.003:
        zc = 0.12 + wh / 2
        add(ax, box_faces((bx, 0, zc), (0.44, 0.44, wh)),
            (0.12, 0.55, 0.95), 0.85, ec=(0.1, 0.4, 0.8), lw=0.4, zorder=3)
    # legs
    for sx, sy in ((0.13, 0.13), (-0.13, 0.13), (0.13, -0.13), (-0.13, -0.13)):
        add(ax, box_faces((bx + sx, sy, 0.20), (0.025, 0.025, 0.16)),
            (0.2, 0.2, 0.22), 1, zorder=3)
    # gel cube
    add(ax, box_faces((bx, 0, 0.40), (0.40, 0.40, 0.40)),
        (0.12, 0.40, 0.85), 1, ec=(0.05, 0.2, 0.5), lw=0.4, zorder=3)
    # glass enclosure (translucent) - draw last-ish so it veils the gel
    g = (0.62, 0.74, 0.88)
    for cx, cy, sx, sy in ((0, -0.25, 0.50, 0.02), (0, 0.25, 0.50, 0.02),
                           (-0.25, 0, 0.02, 0.50), (0.25, 0, 0.02, 0.50)):
        add(ax, box_faces((bx + cx, cy, 0.40), (sx, sy, 0.52)), g, 0.16, ec=g, lw=0.3, zorder=6)
    add(ax, box_faces((bx, 0, 0.66), (0.50, 0.50, 0.02)), g, 0.18, ec=g, lw=0.3, zorder=6)
    # chimney
    add(ax, box_faces((bx, 0, 0.80), (0.08, 0.08, 0.26)), (0.30, 0.30, 0.33), 1, zorder=4)
    add(ax, box_faces((bx, 0, 0.94), (0.12, 0.12, 0.02)), (0.22, 0.22, 0.24), 1, zorder=4)
    # feed line cue toward the panel
    add(ax, box_faces((bx + 0.45, 0, 0.12), (0.55, 0.02, 0.02)), (0.15, 0.55, 0.85), 1, zorder=4)


def carriage_u(s):
    return 0.20 + 0.62 * s


def draw_panel_and_carriage(ax, s, spray, clean_frac):
    # cleaned region = swept band ABOVE the descending carriage (toward the top)
    cu = carriage_u(s)
    # clean strip: from carriage up to top (u=1); soiled: from bottom (0) to carriage
    add(ax, panel_quad(min(0.999, cu), 1.0), (0.06, 0.10, 0.28), 1,
        ec=(0.2, 0.3, 0.5), lw=0.2, zorder=1)            # clean PV blue
    add(ax, panel_quad(0.0, max(0.001, cu)), (0.66, 0.58, 0.42), 1,
        ec=(0.4, 0.35, 0.25), lw=0.2, zorder=1)          # dusty tan
    # guide rails
    for sgn in (1, -1):
        s_mid = 0.0
        cx = s_mid * math.cos(TILT)
        cz = PZ0 + s_mid * math.sin(TILT)
        add(ax, box_faces((cx, 0.51 * sgn, cz + 0.05), (2.0, 0.04, 0.09), pitch=-TILT),
            (0.25, 0.27, 0.30), 1, zorder=2)
    # carriage
    s_loc = (cu - 0.5) * PANEL_L
    x = s_loc * math.cos(TILT)
    z = PZ0 + s_loc * math.sin(TILT)
    add(ax, box_faces((x, 0, z + 0.10), (0.30, 0.92, 0.12), pitch=-TILT),
        (0.86, 0.87, 0.90), 1, ec=(0.4, 0.4, 0.5), lw=0.4, zorder=7)
    add(ax, box_faces((x, 0, z + 0.18), (0.18, 0.40, 0.10), pitch=-TILT),
        (0.20, 0.45, 0.75), 1, zorder=7)                 # tec/tank block
    # brush + spray bar on the down-slope (front, lower) edge
    fu = cu - 0.10
    fs = (fu - 0.5) * PANEL_L
    fx, fz = fs * math.cos(TILT), PZ0 + fs * math.sin(TILT)
    add(ax, box_faces((fx, 0, fz + 0.06), (0.05, 0.90, 0.05), pitch=-TILT),
        (0.95, 0.85, 0.30), 1, zorder=7)                 # brush
    if spray:
        # spray cue: translucent sheet hugging the glass just below the brush
        su = fu - 0.05
        add(ax, panel_quad(max(0.0, su - 0.04), su + 0.02),
            (0.30, 0.66, 0.96), 0.5, ec=(0.3, 0.66, 0.96), lw=0.2, zorder=5)
        # a few droplet cues
        for dy in np.linspace(-0.38, 0.38, 7):
            ss = (su - 0.5) * PANEL_L
            dx = ss * math.cos(TILT)
            dz = PZ0 + ss * math.sin(TILT)
            ax.scatter([dx], [dy], [dz + 0.03], s=14, c="#39a8f0",
                       alpha=0.8, depthshade=False)


def setup_axes(ax):
    ax.clear()
    ax.set_box_aspect((1, 1, 0.6))
    ax.set_xlim(-1.7, 1.3)
    ax.set_ylim(-1.0, 1.0)
    ax.set_zlim(0, 1.4)
    ax.view_init(elev=20, azim=-62)
    ax.set_axis_off()
    # ground
    gx, gy = np.meshgrid([-1.7, 1.3], [-1.0, 1.0])
    ax.plot_surface(gx, gy, np.zeros_like(gx), color=(0.80, 0.80, 0.82),
                    alpha=0.5, zorder=0)


def hud(ax, fig, phase, tank_pct, clean_pct, water_used):
    fig.suptitle("AWH  <->  PV-cleaning robot  -  integrated Gazebo scene",
                 fontsize=15, fontweight="bold", y=0.97)
    ax.text2D(0.015, 0.93, SITE, transform=ax.transAxes, fontsize=9, color="#333")
    box = dict(boxstyle="round,pad=0.4", fc="white", ec="#888", alpha=0.92)
    ax.text2D(0.015, 0.16,
              f"PHASE: {phase}\n"
              f"AWH dock tank : {tank_pct:5.0f} %\n"
              f"panel cleaned : {clean_pct:5.0f} %\n"
              f"water drawn   : {water_used:4.1f} L  (event {EVENT_L:.0f} L)",
              transform=ax.transAxes, fontsize=9.5, family="monospace",
              va="bottom", bbox=box)
    ax.text2D(0.66, 0.02,
              "silica bed ~45 kg  -  fill = real water column\n"
              "spray = visual cue (Gazebo has no fluid)",
              transform=ax.transAxes, fontsize=7.5, color="#666", va="bottom")


# ---------------------------------------------------------------------------
# timeline
# ---------------------------------------------------------------------------
def timeline():
    """Return list of frame states: (phase, water_h, carriage_s, spray, clean, used)."""
    frames = []
    N_FILL, N_CLEAN, N_TOP = 26, 30, 10
    # Phase 1: AWH harvests overnight -> tank fills. Carriage parked at top.
    for i in range(N_FILL):
        f = i / (N_FILL - 1)
        frames.append(("AWH harvesting (tank filling)",
                       f * TANK_MAX, 1.0, 0, 0.0, 0.0))
    # Phase 2: cleaning sweep -- carriage descends, spray on, panel cleans,
    # dock water drops as the carriage tank draws the event volume.
    for i in range(N_CLEAN):
        f = i / (N_CLEAN - 1)
        s = 1.0 - f                       # top -> bottom
        clean = f                         # cleaned fraction grows
        used = EVENT_L * f
        wlev = TANK_MAX * (1 - 0.45 * f)  # dock drains ~ event/ buffer
        frames.append(("cleaning sweep (spray on)", wlev, s, 1, clean, used))
    # Phase 3: carriage returns to dock and the tank tops back up (loop closed)
    for i in range(N_TOP):
        f = i / (N_TOP - 1)
        s = f                             # climb back to top
        wlev = TANK_MAX * (0.55 + 0.45 * f)
        frames.append(("return + top-up (loop closed)", wlev, s, 0, 1.0,
                       EVENT_L * (1 - f) + 0.0))
    return frames


def render():
    states = timeline()
    fig = plt.figure(figsize=(11, 7), dpi=120)
    ax = fig.add_subplot(111, projection="3d")

    shot_idx = {"fill_empty": 0, "fill_full": 25, "mid_clean": 25 + 15,
                "clean_done": 25 + 29}

    def draw(k):
        phase, wh, s, spray, clean, used = states[k]
        setup_axes(ax)
        draw_dock(ax, wh)
        draw_panel_and_carriage(ax, s, spray, clean)
        hud(ax, fig, phase, 100 * wh / TANK_MAX, 100 * clean, used)

    # write all frames + key screenshots
    for k in range(len(states)):
        draw(k)
        fig.savefig(os.path.join(FR, f"frame_{k:03d}.png"),
                    dpi=120, bbox_inches="tight", facecolor="white")
    for name, k in shot_idx.items():
        draw(min(k, len(states) - 1))
        fig.savefig(os.path.join(FIG, f"shot_{name}.png"),
                    dpi=130, bbox_inches="tight", facecolor="white")
        print("wrote", f"shot_{name}.png")

    # animation: GIF always, MP4 if ffmpeg
    def upd(k):
        draw(k)
        return []
    anim = animation.FuncAnimation(fig, upd, frames=len(states), interval=160)
    gif = os.path.join(FIG, "awh_pvbot_demo.gif")
    anim.save(gif, writer=animation.PillowWriter(fps=7), dpi=110)
    print("wrote", gif)
    if shutil.which("ffmpeg"):
        try:
            mp4 = os.path.join(FIG, "awh_pvbot_demo.mp4")
            anim.save(mp4, writer=animation.FFMpegWriter(fps=8, bitrate=2400), dpi=120)
            print("wrote", mp4)
        except Exception as e:           # noqa: BLE001
            print("mp4 skipped:", e)
    else:
        print("ffmpeg not found -> mp4 skipped (GIF written)")
    plt.close(fig)


def write_sdfs():
    dock_world = os.path.join(ROOT, "gazebo", "awh_description", "awh_dock_world.sdf")
    open(dock_world, "w").write(dockgen.world(0.12))
    print("wrote", dock_world)
    integ = os.path.join(HERE, "awh_pvbot_integrated.sdf")
    open(integ, "w").write(iworld.build(carriage=0.55, water=0.12, spray=1, clean=0.5))
    print("wrote", integ)


if __name__ == "__main__":
    write_sdfs()
    render()
    print("\nDONE. screenshots + gif in integration/figures/, frames in figures/frames/")
