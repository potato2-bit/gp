#!/usr/bin/env python3
"""
demo_render.py -- the integrated AWH <-> PV-cleaning-robot simulation, rendered
as a video plus labelled multi-view screenshots. SELF-CONTAINED: reads only this
deliverable's results/, so it runs straight from here.

It shows the full loop the integration closes:
  1. AWH HARVESTING  -- the solar-desiccant dock fills its tank over several
     fast-forwarded days. The fill rate is the REAL climate-driven harvest from
     the co-simulation data (NAC: ~4.7 L/day for a 45 kg silica bed), so the dock
     takes ~5 nights to fill its 27.6 L reservoir. Column height = reservoir
     level (real geometry).
  2. CLEANING WASH   -- the carriage descends the 24 deg panel; the spray fan
     plays onto the glass and the panel turns dust-tan -> PV-blue behind the
     brush; the dock tank drops as the carriage draws the 13.8 L cleaning event.
  3. RETURN + TOP-UP -- the carriage climbs back and the tank refills over the
     next nights' harvest -- the loop is closed.

Gazebo Classic carries no fluid solver, so the tank fill is real geometry while
the spray is a visual cue -- the honest depiction. The scene geometry is the
same the integrated-world SDF loads in Gazebo.

Output (into ../figures):
  awh_pvbot_sim.mp4, awh_pvbot_sim.gif, frames/        -- the animation
  view_iso_labeled.png, view_top_labeled.png,
  view_front_labeled.png                               -- labelled, multi-view
  sim_fill_full.png, sim_washing.png, sim_clean_done.png
Run:  python demo_render.py
"""
from __future__ import annotations
import csv
import json
import math
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import proj3d

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.normpath(os.path.join(HERE, "..", "figures"))
RES = os.path.normpath(os.path.join(HERE, "..", "results"))
FR = os.path.join(FIG, "frames")
os.makedirs(FR, exist_ok=True)

# -- scene constants (match the SDF builders) --------------------------------
TILT = math.radians(24.0)
PANEL_L, PANEL_W, PZ0 = 2.0, 1.0, 0.50
DOCK_X = -1.05
TANK_MAX = 0.20            # max modelled water-column height (make_awh_dock_sdf)
SITE_KEY = "nac"
SITE = "New Administrative Capital   (9.9 kWp, 46 m2 array)"


# ---------------------------------------------------------------------------
# REAL harvest data from the co-simulation (the fill rate)
# ---------------------------------------------------------------------------
def load_harvest():
    """Per-day AWH harvest (L) for the NAC-sized silica bed, plus the reservoir
    cap and cleaning-event volume -- straight from the co-sim outputs."""
    per_kg = json.load(open(os.path.join(RES, "site_yield_per_kg.json")))[SITE_KEY]
    shape = [float(r[SITE_KEY]) for r in
             csv.DictReader(open(os.path.join(RES, "site_yield_shape.csv")))]
    gel_kg = event_L = cap_L = None
    for r in csv.DictReader(open(os.path.join(RES, "integration_sweep.csv"))):
        if r["site"] == SITE_KEY and r["scale"] == "Residential rooftop":
            gel_kg = float(r["gel_kg"]); event_L = float(r["event_L"])
            cap_L = float(r["reservoir_cap_L"])
            break
    daily_L = [gel_kg * per_kg * s for s in shape]      # L harvested each climate day
    return daily_L, gel_kg, event_L, cap_L


DAILY_L, GEL_KG, EVENT_L, CAP_L = load_harvest()
AVG_LDAY = sum(DAILY_L) / len(DAILY_L)


def water_h(reservoir_L):
    """Map reservoir litres to the modelled water-column height."""
    return TANK_MAX * max(0.0, min(1.0, reservoir_L / CAP_L))


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
    c = {(int(i > 0), int(j > 0), int(k > 0)): corners[n]
         for n, (i, j, k) in enumerate(
             [(a, b, d) for a in (-1, 1) for b in (-1, 1) for d in (-1, 1)])}
    return [
        [c[0, 0, 0], c[1, 0, 0], c[1, 1, 0], c[0, 1, 0]],
        [c[0, 0, 1], c[1, 0, 1], c[1, 1, 1], c[0, 1, 1]],
        [c[0, 0, 0], c[1, 0, 0], c[1, 0, 1], c[0, 0, 1]],
        [c[0, 1, 0], c[1, 1, 0], c[1, 1, 1], c[0, 1, 1]],
        [c[0, 0, 0], c[0, 1, 0], c[0, 1, 1], c[0, 0, 1]],
        [c[1, 0, 0], c[1, 1, 0], c[1, 1, 1], c[1, 0, 1]],
    ]


def panel_pt(u, y, lift=0.012):
    s = (u - 0.5) * PANEL_L
    return (s * math.cos(TILT), y, PZ0 + s * math.sin(TILT) + lift)


def panel_quad(u0, u1):
    return [[panel_pt(u0, -PANEL_W / 2), panel_pt(u1, -PANEL_W / 2),
             panel_pt(u1, PANEL_W / 2), panel_pt(u0, PANEL_W / 2)]]


def add(ax, faces, color, alpha=1.0, ec="k", lw=0.3, zorder=1):
    pc = Poly3DCollection(faces, facecolors=color, edgecolors=ec,
                          linewidths=lw, alpha=alpha)
    pc.set_zorder(zorder)
    ax.add_collection3d(pc)


# ---------------------------------------------------------------------------
# the dock (AWH) with its rising water column
# ---------------------------------------------------------------------------
def draw_dock(ax, wh, glow=False):
    bx = DOCK_X
    add(ax, box_faces((bx, 0, 0.03), (0.40, 0.70, 0.06)), (0.30, 0.32, 0.36), 1, zorder=2)
    add(ax, box_faces((bx, 0, 0.09), (0.48, 0.48, 0.06)), (0.10, 0.45, 0.55), 1, zorder=2)
    wh = max(0.0, min(TANK_MAX, wh))
    if wh > 0.003:
        zc = 0.12 + wh / 2
        col = (0.15, 0.62, 1.0) if glow else (0.12, 0.55, 0.95)
        add(ax, box_faces((bx, 0, zc), (0.44, 0.44, wh)),
            col, 0.88, ec=(0.1, 0.4, 0.8), lw=0.5, zorder=3)
        add(ax, box_faces((bx, 0, 0.12 + wh), (0.44, 0.44, 0.004)),
            (0.7, 0.9, 1.0), 0.9, ec=(0.6, 0.85, 1.0), lw=0.3, zorder=4)
    for sx, sy in ((0.13, 0.13), (-0.13, 0.13), (0.13, -0.13), (-0.13, -0.13)):
        add(ax, box_faces((bx + sx, sy, 0.20), (0.025, 0.025, 0.16)),
            (0.2, 0.2, 0.22), 1, zorder=3)
    add(ax, box_faces((bx, 0, 0.40), (0.40, 0.40, 0.40)),
        (0.12, 0.40, 0.85), 1, ec=(0.05, 0.2, 0.5), lw=0.4, zorder=3)
    g = (0.62, 0.74, 0.88)
    for cx, cy, sx, sy in ((0, -0.25, 0.50, 0.02), (0, 0.25, 0.50, 0.02),
                           (-0.25, 0, 0.02, 0.50), (0.25, 0, 0.02, 0.50)):
        add(ax, box_faces((bx + cx, cy, 0.40), (sx, sy, 0.52)), g, 0.16, ec=g, lw=0.3, zorder=6)
    add(ax, box_faces((bx, 0, 0.66), (0.50, 0.50, 0.02)), g, 0.18, ec=g, lw=0.3, zorder=6)
    add(ax, box_faces((bx, 0, 0.80), (0.08, 0.08, 0.26)), (0.30, 0.30, 0.33), 1, zorder=4)
    add(ax, box_faces((bx, 0, 0.94), (0.12, 0.12, 0.02)), (0.22, 0.22, 0.24), 1, zorder=4)
    add(ax, box_faces((bx + 0.45, 0, 0.12), (0.55, 0.02, 0.02)), (0.15, 0.55, 0.85), 1, zorder=4)


def carriage_u(s):
    return 0.20 + 0.62 * s


def draw_frame(ax):
    """The ground-mount that carries the panel -- tall back posts + short front
    legs + top/low cross beams + two under-panel purlin rails. Without this the
    tilted panel would appear to float (matches panel_frame in the SDF)."""
    col = (0.34, 0.36, 0.41)
    xh = (0.95 - 0.5) * PANEL_L * math.cos(TILT)
    zh = PZ0 + (0.95 - 0.5) * PANEL_L * math.sin(TILT)     # underside, high end
    xl = (0.05 - 0.5) * PANEL_L * math.cos(TILT)
    zl = PZ0 + (0.05 - 0.5) * PANEL_L * math.sin(TILT)     # underside, low end
    for sy in (0.46, -0.46):
        add(ax, box_faces((xh, sy, zh / 2), (0.06, 0.06, zh)), col, 1, zorder=1)
        add(ax, box_faces((xl, sy, zl / 2), (0.06, 0.06, zl)), col, 1, zorder=1)
        add(ax, box_faces((0.0, sy, PZ0 - 0.055), (1.85, 0.04, 0.05), pitch=-TILT),
            col, 1, zorder=1)                              # under-panel purlin
    add(ax, box_faces((xh, 0, zh + 0.02), (0.06, 1.0, 0.05)), col, 1, zorder=1)
    add(ax, box_faces((xl, 0, zl + 0.0), (0.06, 1.0, 0.04)), col, 1, zorder=1)


# ---------------------------------------------------------------------------
# the panel + carriage + the spray WASH
# ---------------------------------------------------------------------------
def draw_panel_and_carriage(ax, s, spray, clean_frac, frame_seed=0):
    cu = carriage_u(s)
    add(ax, panel_quad(min(0.999, cu), 1.0), (0.12, 0.26, 0.55), 1,
        ec=(0.35, 0.5, 0.8), lw=0.25, zorder=1)            # clean PV-blue
    add(ax, panel_quad(0.0, max(0.001, cu)), (0.72, 0.63, 0.44), 1,
        ec=(0.5, 0.42, 0.3), lw=0.25, zorder=1)            # dusty tan
    if spray:
        add(ax, panel_quad(min(0.998, cu), min(1.0, cu + 0.08)),
            (0.45, 0.78, 1.0), 0.6, ec=(0.5, 0.85, 1.0), lw=0.2, zorder=2)
    for sgn in (1, -1):
        add(ax, box_faces((0, 0.51 * sgn, PZ0 + 0.05), (2.0, 0.04, 0.09), pitch=-TILT),
            (0.25, 0.27, 0.30), 1, zorder=2)
    s_loc = (cu - 0.5) * PANEL_L
    x = s_loc * math.cos(TILT)
    z = PZ0 + s_loc * math.sin(TILT)
    add(ax, box_faces((x, 0, z + 0.10), (0.30, 0.92, 0.12), pitch=-TILT),
        (0.86, 0.87, 0.90), 1, ec=(0.4, 0.4, 0.5), lw=0.4, zorder=7)
    add(ax, box_faces((x, 0, z + 0.18), (0.18, 0.40, 0.10), pitch=-TILT),
        (0.20, 0.45, 0.75), 1, zorder=7)
    fu = cu - 0.10
    fs = (fu - 0.5) * PANEL_L
    fx, fz = fs * math.cos(TILT), PZ0 + fs * math.sin(TILT)
    add(ax, box_faces((fx, 0, fz + 0.06), (0.05, 0.90, 0.05), pitch=-TILT),
        (0.95, 0.85, 0.30), 1, zorder=7)                   # brush
    add(ax, box_faces((fx + 0.02, 0, fz + 0.085), (0.02, 0.90, 0.02), pitch=-TILT),
        (0.75, 0.78, 0.82), 1, zorder=7)                   # spray bar
    if spray:
        rng = np.random.default_rng(frame_seed)
        su = fu - 0.04
        add(ax, panel_quad(max(0.0, su - 0.10), su + 0.02),
            (0.40, 0.75, 1.0), 0.5, ec=(0.4, 0.75, 1.0), lw=0.2, zorder=5)
        ny = 22
        ys = np.linspace(-0.46, 0.46, ny) + rng.uniform(-0.02, 0.02, ny)
        for yy in ys:
            for du in (0.0, -0.035, -0.07, -0.105):
                uu = su + du - rng.uniform(0.0, 0.02)
                px, py, pz = panel_pt(uu, yy, lift=0.02 + rng.uniform(0, 0.03))
                ax.scatter([px], [py], [pz], s=rng.uniform(14, 40),
                           c="#2aa8ff", alpha=0.9, depthshade=False, zorder=9,
                           edgecolors="none")
        for yy in np.linspace(-0.42, 0.42, 10):
            bx_, by_, bz_ = panel_pt(fu - 0.02, yy, lift=0.09)
            tx_, ty_, tz_ = panel_pt(su - 0.04, yy, lift=0.02)
            ax.plot([bx_, tx_], [by_, ty_], [bz_, tz_], color="#6cc8ff",
                    lw=1.1, alpha=0.7, zorder=6)


def setup_axes(ax, azim, elev, aspect_z=0.62):
    ax.clear()
    ax.set_box_aspect((1, 1, aspect_z))
    ax.set_xlim(-1.55, 1.15)
    ax.set_ylim(-0.85, 0.85)
    ax.set_zlim(0, 1.25)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    gx, gy = np.meshgrid([-1.55, 1.15], [-0.85, 0.85])
    ax.plot_surface(gx, gy, np.zeros_like(gx), color=(0.80, 0.80, 0.82),
                    alpha=0.5, zorder=0)


def hud(ax, fig, phase, tank_pct, clean_pct, water_used, sub=""):
    fig.suptitle("AWH  <->  PV-cleaning robot   |   integrated simulation",
                 fontsize=15, fontweight="bold", y=0.97)
    ax.text2D(0.015, 0.93, SITE, transform=ax.transAxes, fontsize=9, color="#333")
    box = dict(boxstyle="round,pad=0.45", fc="white", ec="#888", alpha=0.93)
    ax.text2D(0.015, 0.15,
              f"PHASE: {phase}\n"
              f"AWH dock tank : {tank_pct:5.0f} %\n"
              f"panel cleaned : {clean_pct:5.0f} %\n"
              f"water drawn   : {water_used:4.1f} L  (event {EVENT_L:.0f} L)",
              transform=ax.transAxes, fontsize=9.5, family="monospace",
              va="bottom", bbox=box)
    if sub:
        ax.text2D(0.015, 0.10, sub, transform=ax.transAxes, fontsize=9,
                  family="monospace", color="#1a5", va="top")
    ax.text2D(0.66, 0.05,
              f"silica bed ~{GEL_KG:.0f} kg  |  harvest ~{AVG_LDAY:.1f} L/day (real climate data)\n"
              "fill = real water column  |  spray = visual cue (no fluid in Gazebo)",
              transform=ax.transAxes, fontsize=7.5, color="#666", va="bottom")


# ---------------------------------------------------------------------------
# component callouts for the labelled multi-view screenshots
# ---------------------------------------------------------------------------
def labels_at(s_ready):
    """(text, anchor3d) for the scene's components at the given carriage state."""
    cu = carriage_u(s_ready)
    cx = (cu - 0.5) * PANEL_L * math.cos(TILT)
    cz = PZ0 + (cu - 0.5) * PANEL_L * math.sin(TILT)
    fu = cu - 0.10
    fx = (fu - 0.5) * PANEL_L * math.cos(TILT)
    fz = PZ0 + (fu - 0.5) * PANEL_L * math.sin(TILT)
    xl = (0.06 - 0.5) * PANEL_L * math.cos(TILT)
    zl = PZ0 + (0.06 - 0.5) * PANEL_L * math.sin(TILT)
    return [
        ("silica-gel AWH bed", (DOCK_X, 0, 0.46)),
        ("condensate tank (fill)", (DOCK_X, 0, 0.14)),
        ("night-vent chimney", (DOCK_X, 0, 0.95)),
        ("water feed to robot", (DOCK_X + 0.55, 0, 0.12)),
        ("24 deg PV panel", panel_pt(0.42, 0.0, 0.02)),
        ("guide rail", (-0.10, 0.51, PZ0 + 0.08)),
        ("cleaning carriage", (cx, 0, cz + 0.16)),
        ("brush + spray bar", (fx, 0, fz + 0.06)),
        ("mounting frame (carries the panel)", (xl, -0.46, zl / 2)),
    ]


def _axfrac(ax, x, y, z):
    """3D world point -> axes-fraction (x,y) under the current projection."""
    xp, yp, _ = proj3d.proj_transform(x, y, z, ax.get_proj())
    xd, yd = ax.transData.transform((xp, yp))
    return ax.transAxes.inverted().transform((xd, yd))


def draw_labels(ax, fig, s_ready):
    """Edge-anchored callouts that adapt to any view: project each anchor, then
    stack the labels down the left/right margins with leader lines."""
    fig.canvas.draw()
    items = [(t, a, *map(float, _axfrac(ax, *a))) for t, a in labels_at(s_ready)]
    left = sorted([it for it in items if it[2] < 0.5], key=lambda t: -t[3])
    right = sorted([it for it in items if it[2] >= 0.5], key=lambda t: -t[3])

    def place(group, tx, ha):
        ys = np.linspace(0.88, 0.14, len(group)) if len(group) > 1 else [0.5]
        for (text, _a, fx, fy), ty in zip(group, ys):
            ax.annotate(text, xy=(fx, fy), xycoords="axes fraction",
                        xytext=(tx, ty), textcoords="axes fraction",
                        fontsize=8.5, ha=ha, va="center",
                        bbox=dict(boxstyle="round,pad=0.28", fc="white",
                                  ec="#555", alpha=0.93),
                        arrowprops=dict(arrowstyle="-", color="#333", lw=0.8,
                                        shrinkA=3, shrinkB=4,
                                        connectionstyle="arc3,rad=0.08"),
                        zorder=20)
    place(left, 0.015, "left")
    place(right, 0.985, "right")


def render_labeled_view(name, title, elev, azim, aspect_z=0.62):
    """One labelled still of the integrated scene from a named view."""
    fig = plt.figure(figsize=(12, 7.6), dpi=130)
    ax = fig.add_subplot(111, projection="3d")
    setup_axes(ax, azim, elev, aspect_z)
    draw_frame(ax)
    draw_dock(ax, water_h(CAP_L), glow=True)               # tank full
    draw_panel_and_carriage(ax, 0.55, 1, 0.45)             # carriage mid-panel, spray on
    draw_labels(ax, fig, 0.55)
    fig.suptitle(f"AWH <-> PV-cleaning robot   |   {title}",
                 fontsize=14, fontweight="bold", y=0.97)
    ax.text2D(0.30, 0.95, SITE, transform=ax.transAxes, fontsize=9, color="#333")
    ax.text2D(0.62, 0.03,
              f"silica bed ~{GEL_KG:.0f} kg, fills in ~5 nights at ~{AVG_LDAY:.1f} L/night\n"
              "fill = real water column  |  spray = visual cue (no fluid in Gazebo)",
              transform=ax.transAxes, fontsize=7.5, color="#666", va="bottom")
    fig.savefig(os.path.join(FIG, name), dpi=130, facecolor="white")
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------------------
# timeline -- DATA-DRIVEN fill over many fast-forwarded days
# ---------------------------------------------------------------------------
def timeline():
    """(phase, water_h, carriage_s, spray, clean_frac, water_used, azim, elev, sub)."""
    frames = []
    az0, el0 = 150.0, 26.0       # angled front/side: panel face toward viewer

    # Phase 1: harvest night by night until the reservoir is full. Each day adds
    # the REAL harvest; the column rises over a few sub-frames (fast-forward).
    reservoir, day, SUB = 0.0, 0, 4
    while reservoir < 0.985 * CAP_L and day < len(DAILY_L):
        prev = reservoir
        reservoir = min(CAP_L, reservoir + DAILY_L[day])
        day += 1
        for j in range(SUB):
            f = (j + 1) / SUB
            lvl = prev + (reservoir - prev) * f
            sub = f"night {day}: +{DAILY_L[day-1]:.1f} L harvested"
            frames.append(("AWH harvesting (filling, fast-forward)",
                           water_h(lvl), 1.0, 0, 0.0, 0.0, az0, el0, sub))
    for _ in range(5):                                    # hold full
        frames.append(("AWH tank full - ready to clean", water_h(CAP_L),
                       1.0, 0, 0.0, 0.0, az0, el0, f"{day} nights of harvest"))

    # Phase 2: cleaning wash -- descend, spray, tan->blue, reservoir drains by EVENT
    N_CLEAN = 44
    for i in range(N_CLEAN):
        f = i / (N_CLEAN - 1)
        s = 1.0 - f
        az = az0 + 9.0 * math.sin(math.pi * f)
        el = el0 + 3.0 * math.sin(math.pi * f)
        lvl = CAP_L - EVENT_L * f
        frames.append(("cleaning wash (spray ON)", water_h(lvl), s, 1, f,
                       EVENT_L * f, az, el, "drawing the 13.8 L cleaning event"))

    # Phase 3: return + the tank tops back up over the next nights' harvest
    reservoir = CAP_L - EVENT_L
    d2 = day
    N_TOP = 16
    for i in range(N_TOP):
        f = i / (N_TOP - 1)
        s = f
        # advance ~one harvest night every few frames
        if i % 5 == 0 and d2 < len(DAILY_L):
            reservoir = min(CAP_L, reservoir + DAILY_L[d2]); d2 += 1
        frames.append(("return + top-up (loop closed)", water_h(reservoir),
                       s, 0, 1.0, EVENT_L * (1 - f), az0, el0,
                       f"re-harvesting: night {d2}"))
    return frames


def render():
    states = timeline()
    fig = plt.figure(figsize=(11, 7), dpi=120)
    ax = fig.add_subplot(111, projection="3d")

    def draw(k):
        phase, wh, s, spray, clean, used, az, el, sub = states[k]
        setup_axes(ax, az, el)
        draw_frame(ax)
        draw_dock(ax, wh, glow=(spray == 0 and wh > 0.6 * TANK_MAX))
        draw_panel_and_carriage(ax, s, spray, clean, frame_seed=k)
        hud(ax, fig, phase, 100 * wh / TANK_MAX, 100 * clean, used, sub)

    paths = []
    for k in range(len(states)):
        draw(k)
        p = os.path.join(FR, f"frame_{k:03d}.png")
        fig.savefig(p, dpi=120, facecolor="white")
        paths.append(p)
    # action stills
    n = len(states)
    shots = {"sim_fill_full": None, "sim_washing": None, "sim_clean_done": None}
    for k in range(n):
        if states[k][0].startswith("AWH tank full"):
            shots["sim_fill_full"] = k
        if states[k][3] == 1 and states[k][4] > 0.45 and shots["sim_washing"] is None:
            shots["sim_washing"] = k
        if states[k][4] >= 0.999:
            shots["sim_clean_done"] = k
    for name, k in shots.items():
        if k is None:
            continue
        draw(k)
        fig.savefig(os.path.join(FIG, f"{name}.png"), dpi=130, facecolor="white")
        print("wrote", f"{name}.png")
    plt.close(fig)

    # assemble MP4 + GIF
    import imageio.v2 as imageio
    imgs = [imageio.imread(p) for p in paths]
    try:
        imageio.mimsave(os.path.join(FIG, "awh_pvbot_sim.mp4"), imgs, fps=12,
                        quality=8, macro_block_size=None)
        print("wrote awh_pvbot_sim.mp4")
    except Exception as e:                                # noqa: BLE001
        print("mp4 failed:", e)
    from PIL import Image
    pil = [Image.open(p).convert("P", palette=Image.ADAPTIVE) for p in paths]
    pil[0].save(os.path.join(FIG, "awh_pvbot_sim.gif"), save_all=True,
                append_images=pil[1:], duration=90, loop=0)
    print("wrote awh_pvbot_sim.gif")


if __name__ == "__main__":
    # labelled multi-view screenshots -- the four views, correctly oriented
    render_labeled_view("view_side_labeled.png",
                        "SIDE view - 24 deg tilt profile (labelled)",
                        elev=8, azim=-90, aspect_z=0.50)
    render_labeled_view("view_top_labeled.png", "TOP view (labelled)",
                        elev=89, azim=-90, aspect_z=0.32)
    render_labeled_view("view_angled_labeled.png",
                        "ANGLED front/side view (labelled)",
                        elev=28, azim=150, aspect_z=0.62)
    render_labeled_view("view_front_labeled.png",
                        "FRONT view - panel face-on, dock in front (labelled)",
                        elev=20, azim=180, aspect_z=0.72)
    # the animation
    render()
    print(f"\nDONE -> {FIG}\n  awh_pvbot_sim.mp4/.gif, frames/, "
          f"view_{{side,top,angled,front}}_labeled.png, sim_*.png")
