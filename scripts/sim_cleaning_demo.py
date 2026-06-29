#!/usr/bin/env python3
"""
sim_cleaning_demo.py - offline animation of the RAIL-GUIDED PV-cleaning robot.

Matches the Gazebo demo: a rail-guided carriage with a full-width brush rides
the 24 deg panel on guide rails and cleans in fall-line sweeps - down the slope
(spray + brush on), then back up. One pass of the full-width brush clears the
whole panel width, so there is no turning. The on-board TEC module tops up the
tank while it works.

Runs anywhere matplotlib is installed (no ROS, no Gazebo). Writes
figures/sim_cleaning_demo.gif.

    python scripts/sim_cleaning_demo.py
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from matplotlib.animation import FuncAnimation, PillowWriter

# ---- panel + sweep plan ---------------------------------------------------
PANEL_X, PANEL_Y = 2.0, 1.0            # slope length, width [m]
TILT_DEG = 24.0
BRUSH = 0.96                            # full-width brush span [m]
V = 0.08                               # m/s sweep speed
N_SWEEPS = 2                           # down + up
FR_FULL = 60                           # frames per full-length pass

x_lo, x_hi = 0.12, PANEL_X - 0.12       # travel limits along the slope
path = []                               # (x, spraying, going_down)
for s in range(N_SWEEPS):
    down = (s % 2 == 0)
    xs0, xe0 = (x_hi, x_lo) if down else (x_lo, x_hi)
    n = FR_FULL
    for x in np.linspace(xs0, xe0, n):
        path.append((x, True, down))
path = np.array(path, dtype=float)
N = len(path)

# dust grid (cleared in full-width bands as the brush passes)
GX, GY = 200, 100
dust = np.ones((GY, GX))
xs = np.linspace(0, PANEL_X, GX)

# ---- figure ---------------------------------------------------------------
fig = plt.figure(figsize=(10.5, 5.6))
fig.suptitle("Rail-Guided TEC PV-Cleaning Robot - fall-line sweep on a 24$^\\circ$ panel",
             fontsize=13, fontweight="bold")
ax = fig.add_axes([0.05, 0.10, 0.60, 0.80])    # top view
axs = fig.add_axes([0.69, 0.55, 0.29, 0.34])   # side view (tilt)
axi = fig.add_axes([0.69, 0.10, 0.29, 0.34])   # status / TEC gauge
for a in (ax, axs, axi):
    a.set_xticks([]); a.set_yticks([])

ax.set_xlim(-0.2, PANEL_X + 0.2); ax.set_ylim(-0.2, PANEL_Y + 0.2)
ax.set_aspect("equal")
ax.set_title("top view - full-width brush clears each pass", fontsize=10)
dust_im = ax.imshow(dust, extent=[0, PANEL_X, 0, PANEL_Y], origin="lower",
                    cmap="YlOrBr", vmin=0, vmax=1.4, alpha=0.9, zorder=1)
ax.add_patch(Rectangle((0, 0), PANEL_X, PANEL_Y, fill=False, ec="#102a55", lw=2.5, zorder=2))
# guide rails along the two long edges
ax.add_patch(Rectangle((0, -0.05), PANEL_X, 0.04, color="#444", zorder=2))
ax.add_patch(Rectangle((0, PANEL_Y + 0.01), PANEL_X, 0.04, color="#444", zorder=2))
robot_artists = []

# side view: 24 deg tilt with the carriage riding the slope
axs.set_title("side view - 24$^\\circ$ tilt, carriage on rails", fontsize=9)
axs.set_xlim(-0.15, 2.3); axs.set_ylim(-0.15, 1.15); axs.set_aspect("equal")
ang = np.deg2rad(TILT_DEG)
pX = np.array([0, PANEL_X * np.cos(ang)]); pY = np.array([0, PANEL_X * np.sin(ang)])
axs.plot(pX, pY, color="#1b3a6b", lw=5, solid_capstyle="round")
axs.plot([0, 0.18], [0, 0], color="#555", lw=2)          # ground / post
side_car, = axs.plot([], [], "s", color="crimson", ms=11)

# status + TEC tank gauge
axi.set_xlim(0, 1); axi.set_ylim(0, 1)
axi.set_title("TEC harvest + status", fontsize=9)
axi.add_patch(Rectangle((0.08, 0.15), 0.18, 0.6, fill=False, ec="k", lw=1.5))
tank_fill = Rectangle((0.08, 0.15), 0.18, 0.0, color="#2f73d9"); axi.add_patch(tank_fill)
axi.text(0.17, 0.80, "tank", ha="center", fontsize=8)
status_txt = axi.text(0.34, 0.66, "", fontsize=9, va="top", family="monospace")


def draw_robot(x, spraying, down):
    """Full-width carriage spanning the panel, brush at the leading edge."""
    for a in robot_artists:
        a.remove()
    robot_artists.clear()
    L = 0.34                                   # carriage length along the slope
    body = Rectangle((x - L / 2, 0.02), L, PANEL_Y - 0.04, color="#8a8f99",
                     ec="k", lw=1.2, zorder=5)
    ax.add_patch(body); robot_artists.append(body)
    # TEC module band (cyan, hatched) across the carriage
    tec = Rectangle((x - L / 2 + 0.03, 0.18), 0.12, PANEL_Y - 0.36,
                    color="#7fd4ec", ec="#155e75", lw=1.0, hatch="||", zorder=6)
    ax.add_patch(tec); robot_artists.append(tec)
    robot_artists.append(ax.text(x, PANEL_Y / 2, "TEC", ha="center", va="center",
                                 fontsize=7, fontweight="bold", color="#0b3a47", zorder=7))
    # full-width brush at the leading (down-slope) edge
    edge = (x - L / 2) if down else (x + L / 2 - 0.04)
    br = Rectangle((edge, 0.02), 0.04, PANEL_Y - 0.04, color="#f2f2e6",
                   ec="#555", lw=1.0, zorder=6)
    ax.add_patch(br); robot_artists.append(br)
    # spray fan ahead of the brush
    if spraying:
        bx = edge + (-0.03 if down else 0.05)
        for j in np.linspace(0.08, PANEL_Y - 0.08, 9):
            d = Circle((bx + (np.random.rand() - 0.5) * 0.02, j + (np.random.rand() - 0.5) * 0.03),
                       0.006, color="#3aa0ff", alpha=0.8, zorder=7)
            ax.add_patch(d); robot_artists.append(d)


def update(k):
    x, spraying, down = path[k]
    if spraying:                                # clear a full-width band
        mx = (np.abs(xs - x) <= 0.06)
        dust[:, mx] = 0.0
    dust_im.set_data(dust)
    draw_robot(x, bool(spraying), bool(down))
    s = x / PANEL_X
    side_car.set_data([PANEL_X * np.cos(ang) * s], [PANEL_X * np.sin(ang) * s])
    frac = (k + 1) / N
    tank_fill.set_height(0.6 * frac)
    cleaned = 100.0 * (1.0 - dust.mean())
    status_txt.set_text(
        "mode  : sweep %s\nspeed : %.2f m/s\nbrush : full width\nclean : %4.0f %%\nTEC   : harvesting"
        % ("DOWN" if down else "UP", V, cleaned))
    return robot_artists + [dust_im, side_car, tank_fill, status_txt]


def main():
    import os
    os.makedirs("figures", exist_ok=True)
    anim = FuncAnimation(fig, update, frames=N, interval=70, blit=False)
    out = "figures/sim_cleaning_demo.gif"
    anim.save(out, writer=PillowWriter(fps=15))
    print("wrote %s  (%d frames, %d sweeps)" % (out, N, N_SWEEPS))


if __name__ == "__main__":
    main()
