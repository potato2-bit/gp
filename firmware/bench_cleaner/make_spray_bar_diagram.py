"""
Spray-bar detail: how to mount 0.4 mm 3D-printer nozzles (M6) on the cleaning bar,
plus the no-nozzle drilled-manifold alternative. Bench prototype, Solar-AWH robot.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, Polygon, FancyBboxPatch

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.2), dpi=150,
                               gridspec_kw={"width_ratios": [1.45, 1]})
TUBE = "#1f6fb0"; STEEL = "#8a8f98"; BRASS = "#c9a227"; INK = "#222"; RED = "#d62728"
WATER = "#2b8cbe"; GRN = "#3a7a35"; PANEL = "#274b6d"

# =================== LEFT: the whole spray bar ===================
ax1.set_xlim(0, 100); ax1.set_ylim(0, 70); ax1.axis("off")
ax1.set_title("The spray bar (carriage view)", fontsize=13, fontweight="bold")

# manifold bar
ax1.add_patch(FancyBboxPatch((10, 42), 80, 7, boxstyle="round,pad=0.1",
                             fc="#dfe7ef", ec=INK, lw=2))
ax1.text(50, 45.5, "rigid bar / pipe  (the manifold — must be thick enough to tap)",
         fontsize=9, ha="center", va="center")
# end cap (right)
ax1.add_patch(Rectangle((90, 41), 3.5, 9, fc=STEEL, ec="k", lw=1.5))
ax1.text(92, 53, "CAP\nthe end", fontsize=8, ha="center", color=INK)
# feed from pump (left)
ax1.plot([2, 10], [45.5, 45.5], color=TUBE, lw=6, solid_capstyle="round")
ax1.add_patch(plt.Circle((10, 45.5), 1.2, fc="white", ec=RED, lw=2, zorder=6))
ax1.annotate("feed from\npump (clamp)", xy=(6, 45.5), xytext=(6, 60),
             fontsize=8.5, ha="center", arrowprops=dict(arrowstyle="->", lw=1.2),
             bbox=dict(boxstyle="round,pad=0.25", fc="#fffbe6", ec=INK))
# three nozzles pointing down
xs = [28, 50, 72]
for x in xs:
    ax1.add_patch(Polygon([(x-2, 42), (x+2, 42), (x+2, 39), (x+1, 38), (x-1, 38), (x-2, 39)],
                          fc=BRASS, ec="k", lw=1.2, zorder=5))      # hex body
    ax1.add_patch(Polygon([(x-1, 38), (x+1, 38), (x, 35.5)], fc=BRASS, ec="k", zorder=5))  # tip
    for dx in (-3.2, 0, 3.2):                                       # fan
        ax1.add_patch(FancyArrowPatch((x, 35.2), (x+dx, 27), arrowstyle="-|>",
                                      mutation_scale=13, color=WATER, lw=0, zorder=4))
# coupon
ax1.add_patch(Rectangle((16, 18), 74, 6, fc=PANEL, ec="k", lw=1.4))
ax1.text(53, 21, "coupon / panel", fontsize=9, color="white", ha="center", va="center")
# spacing + aim notes
ax1.annotate("", xy=(28, 31), xytext=(50, 31), arrowprops=dict(arrowstyle="<->", lw=1.2, color=GRN))
ax1.text(39, 33, "even spacing =\ncoupon width / N", fontsize=8.3, ha="center", color=GRN)
ax1.text(50, 8, "Aim the bar so spray lands just AHEAD of the brush\n"
                "(wet the glass before the microfibre reaches it).",
         fontsize=9, ha="center", color=INK,
         bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=INK))

# =================== RIGHT: nozzle mounting detail ===================
ax2.set_xlim(0, 50); ax2.set_ylim(0, 70); ax2.axis("off")
ax2.set_title("Mounting one nozzle  (cross-section)", fontsize=13, fontweight="bold")

# bar wall (cross-hatched), top = inside the manifold (water), bottom = outside
ax2.add_patch(Rectangle((8, 30), 34, 10, fc="#dfe7ef", ec=INK, lw=2, hatch="////"))
ax2.text(25, 47, "water inside the bar", fontsize=9, ha="center", color=WATER)
ax2.add_patch(Rectangle((9, 40), 32, 6, fc=WATER, alpha=0.25, ec="none"))

# tapped hole + nozzle screwed in
nx = 25
# threaded shank (zig-zag threads) through the wall
ax2.add_patch(Rectangle((nx-3, 24), 6, 12, fc=BRASS, ec="k", lw=1.2, zorder=5))
for ty in range(25, 36, 2):
    ax2.plot([nx-3, nx+3], [ty, ty+1], color="k", lw=0.7, zorder=6)
# hex body below the wall
ax2.add_patch(Polygon([(nx-4.5, 24), (nx+4.5, 24), (nx+4.5, 20), (nx+2.5, 17),
                       (nx-2.5, 17), (nx-4.5, 20)], fc=BRASS, ec="k", lw=1.2, zorder=5))
# converging tip + 0.4 mm orifice
ax2.add_patch(Polygon([(nx-2.5, 17), (nx+2.5, 17), (nx+0.4, 13), (nx-0.4, 13)],
                      fc=BRASS, ec="k", zorder=5))
ax2.plot([nx, nx], [36, 13], color="white", lw=1.4, zorder=7)   # internal channel
for dx in (-2.5, 0, 2.5):
    ax2.add_patch(FancyArrowPatch((nx, 12.8), (nx+dx, 6), arrowstyle="-|>",
                                  mutation_scale=12, color=WATER, lw=0, zorder=4))

ax2.annotate("M6×1 thread\n(tap the hole: 5.0 mm drill, then M6 tap)",
             xy=(nx+3, 30), xytext=(44, 36), fontsize=8.5, ha="center",
             arrowprops=dict(arrowstyle="->", lw=1.2),
             bbox=dict(boxstyle="round,pad=0.25", fc="#fffbe6", ec=INK))
ax2.annotate("wrap PTFE (plumber's) tape\non the thread = no leak",
             xy=(nx-3, 33), xytext=(11, 58), fontsize=8.5, ha="center", color=GRN,
             arrowprops=dict(arrowstyle="->", lw=1.2, color=GRN),
             bbox=dict(boxstyle="round,pad=0.25", fc="#eef7ea", ec=GRN))
ax2.annotate("0.4 mm orifice\n(faces the glass)",
             xy=(nx, 13), xytext=(40, 12), fontsize=8.5, ha="center",
             arrowprops=dict(arrowstyle="->", lw=1.2),
             bbox=dict(boxstyle="round,pad=0.25", fc="#fffbe6", ec=INK))
ax2.text(25, 66, "No tap / no brass nozzle?  Just drill the tube wall\n"
                 "Ø0.6–0.8 mm straight through — overlapping jets work too.",
         fontsize=8.6, ha="center", color=RED,
         bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=RED, lw=1.2))

plt.tight_layout()
out = "firmware/bench_cleaner/spray_bar_diagram.png"
plt.savefig(out, bbox_inches="tight", facecolor="white")
print("saved", out)
