"""
Bench plumbing schematic for a SUBMERSIBLE brushless centrifugal pump
(DC-1238B, 12 V, IP68, 240 L/H, 3 m head): bowl (pump inside) -> spray bar
on the moving carriage. Solar-AWH PV-cleaning robot bench prototype.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, Circle, FancyBboxPatch, PathPatch
from matplotlib.path import Path

fig, ax = plt.subplots(figsize=(13, 7.5), dpi=150)
ax.set_xlim(0, 100); ax.set_ylim(0, 62); ax.axis("off")

WATER = "#2b8cbe"; TUBE = "#1f6fb0"; STEEL = "#8a8f98"
RED = "#d62728"; INK = "#222222"; PANEL = "#274b6d"; GRN = "#3a7a35"

def tube(pts, lw=5, color=TUBE, z=4):
    xs, ys = zip(*pts); ax.plot(xs, ys, color=color, lw=lw, solid_capstyle="round", zorder=z)

def flow(p0, p1, color=WATER):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=18, color=color, lw=0, zorder=8))

def joint(x, y):
    ax.add_patch(Circle((x, y), 1.1, fc="white", ec=RED, lw=2, zorder=9))

def callout(x, y, tx, ty, text, color=INK):
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=9.3, color=color, ha="center", va="center",
                zorder=11, arrowprops=dict(arrowstyle="->", color=color, lw=1.3),
                bbox=dict(boxstyle="round,pad=0.3", fc="#fffbe6", ec=color, lw=1))

ax.text(50, 59, "Bench water path:  SUBMERSIBLE pump sits in the bowl  ->  spray bar",
        fontsize=15, fontweight="bold", ha="center", color=INK)

# ---------------- BOWL with water ----------------
ax.add_patch(Rectangle((4, 6), 30, 28, fc="none", ec=INK, lw=2))
ax.add_patch(Rectangle((4.4, 6.3), 29.2, 23.5, fc=WATER, alpha=0.28, ec="none"))
ax.text(19, 2.8, "BOWL / RESERVOIR  (open, refill by hand)", fontsize=9.5, ha="center", color=INK)
ax.text(31.5, 28.5, "water line", fontsize=8, ha="right", color=WATER, style="italic")

# ---------------- SUBMERGED PUMP ----------------
ax.add_patch(FancyBboxPatch((12, 11), 12, 9, boxstyle="round,pad=0.2",
                            fc="#eaeef3", ec=INK, lw=2, zorder=5))
ax.text(18, 16.5, "DC-1238B PUMP", fontsize=8.7, ha="center", fontweight="bold", zorder=6)
ax.text(18, 13.8, "12 V · IP68 · 0.4 A\n4 L/min · 3 m head", fontsize=7.6, ha="center", zorder=6)
# little feet (raise off bottom)
ax.add_patch(Rectangle((13.5, 9.4), 2.2, 1.6, fc="#555", ec="k", zorder=5))
ax.add_patch(Rectangle((20.3, 9.4), 2.2, 1.6, fc="#555", ec="k", zorder=5))
# intake screen (bottom hole)
for sx in range(0, 5):
    ax.plot([15.4 + sx*1.1, 15.4 + sx*1.1], [11.0, 12.0], color=GRN, lw=1.4, zorder=6)
# outlet barb (top hole) + tube up, out of bowl, to the right
ax.add_patch(Rectangle((17, 20), 2, 1.6, fc=STEEL, ec="k", zorder=6))   # barb
tube([(18, 21.5), (18, 40), (44, 40)])
flow((18, 30), (18, 35))                      # water rising in the single outlet line

# ---------------- service loop -> carriage ----------------
loop = Path([(44, 40), (48, 24), (54, 24), (58, 40)],
            [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
ax.add_patch(PathPatch(loop, fill=False, ec=TUBE, lw=5, zorder=3))
tube([(58, 40), (80, 40), (80, 35)])
flow((63, 40), (69, 40))

# ---------------- RAIL + CARRIAGE ----------------
ax.add_patch(Rectangle((56, 30.5), 42, 2.2, fc=STEEL, ec="k", lw=1, zorder=2))
ax.text(96.5, 31.6, "rail", fontsize=8.5, ha="right", va="center", color="white")
ax.add_patch(FancyBboxPatch((75, 32.7), 11, 6.5, boxstyle="round,pad=0.15",
                            fc="#d9e6f2", ec=INK, lw=1.8, zorder=5))
ax.text(80.5, 36.0, "CARRIAGE\n(moves)", fontsize=8.5, ha="center", va="center", zorder=6)
for wx in (77.5, 83.5):
    ax.add_patch(Circle((wx, 32.5), 1.0, fc="#444", ec="k", zorder=6))
# spray bar + 3 nozzles
ax.add_patch(Rectangle((75.5, 28.8), 10, 1.6, fc=TUBE, ec="k", lw=1, zorder=5))
tube([(80, 32.7), (80, 30.4)]); joint(80, 30.4)
for nx in (77.5, 80.5, 83.5):
    ax.add_patch(plt.Polygon([(nx-0.8, 28.8), (nx+0.8, 28.8), (nx, 27.3)], fc="#444", ec="k", zorder=6))
    for dx in (-2.2, 0, 2.2):
        flow((nx, 27.2), (nx+dx, 22.5))
ax.add_patch(plt.Polygon([(72, 14), (92, 18), (91, 21.5), (71, 17.5)], fc=PANEL, ec="k", lw=1.5, zorder=2))
ax.text(81.5, 12.7, "PV PANEL / COUPON (tilted)", fontsize=9, ha="center", color=INK)

# ---------------- CALLOUTS ----------------
callout(18, 11.5, 8, 40, "Top hole = OUTLET\n(the one that JETS when\npowered) -> tube goes here")
callout(15.9, 11.4, 30, 9, "Bottom hole = INTAKE screen\n(raise off the floor; the bowl\nIS the filter -- keep it clean)", color=GRN)
callout(22, 18, 44, 49, "Pump stays SUBMERGED (IP68).  Centrifugal = must be flooded,\nit will NOT self-prime sitting in air.")
callout(51, 25, 52, 12, "Service loop:\ntube flexes as\ncarriage moves")
callout(83.5, 27.6, 94, 25, "Fine fan spray\nonto the glass")
ax.text(50, 54.5, "red rings = clamp every joint (push fully on + zip-tie).   Only ONE tube leaves the bowl: the outlet.",
        fontsize=9.4, ha="center", color=RED, bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=RED, lw=1.3))

plt.tight_layout()
out = "firmware/bench_cleaner/plumbing_diagram.png"
plt.savefig(out, bbox_inches="tight", facecolor="white")
print("saved", out)
