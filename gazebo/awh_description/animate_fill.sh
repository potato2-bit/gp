#!/usr/bin/env bash
# Render the nested-cube AWH with a rising tank water level -> frames, GIF, labeled shot.
set +e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
export DISPLAY=:0
source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null; conda activate awh
FR="$HERE/frames"; rm -rf "$FR"; mkdir -p "$FR"
N=10; WMAX=0.40

# loadable static world (half-full) for interactive viewing
python make_cube_sdf.py --water 0.18 --out awh_cube_world.sdf >/dev/null

for i in $(seq 0 $((N-1))); do
  WH=$(python -c "print(round($WMAX*$i/($N-1),4))")
  python make_cube_sdf.py --water "$WH" --camera --out _cube_shot.sdf >/dev/null
  rm -rf /tmp/awhfill; mkdir -p /tmp/awhfill
  gzserver --verbose _cube_shot.sdf > /tmp/gzfill.log 2>&1 &
  GZ=$!; sleep 9; kill "$GZ" 2>/dev/null; pkill -x gzserver 2>/dev/null; sleep 1
  python3 -c "import glob,os,shutil; fs=sorted(glob.glob('/tmp/awhfill/*.jpg'),key=os.path.getmtime); shutil.copy(fs[-1], '$FR/frame_$(printf %02d $i).png') if fs else print('frame $i NONE')"
  echo "frame $i  water=$WH"
done

echo "=== stitching GIF + labels ==="
python3 - "$FR" "$HERE" <<'PY'
import sys, glob, os
from PIL import Image
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fr, here = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(os.path.join(fr, "frame_*.png")))
print("frames:", len(files))
imgs = [Image.open(f).convert("RGB") for f in files]
if not imgs:
    print("NO FRAMES"); sys.exit(0)
# animated GIF (forward, hold last)
small = [im.resize((900, int(900*im.height/im.width))) for im in imgs]
seq = small + [small[-1]]*5
seq[0].save(os.path.join(here, "awh_fill.gif"), save_all=True, append_images=seq[1:], duration=320, loop=0)
imgs[0].save(os.path.join(here, "awh_fill_empty.png"))
imgs[-1].save(os.path.join(here, "awh_fill_full.png"))
print("wrote awh_fill.gif, awh_fill_empty.png, awh_fill_full.png")

# labeled hero shot (annotate the full-tank frame)
im = imgs[-1]; W, H = im.size
fig, ax = plt.subplots(figsize=(W/130, H/130), dpi=130)
ax.imshow(im); ax.axis("off")
def lab(text, xy, xytext, c="black"):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=12, fontweight="bold", color=c,
                ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color=c, lw=2),
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=c, alpha=0.9))
sx, sy = W/1500.0, H/1000.0
lab("Stack chimney\n(warm moist air out)",        (745*sx, 175*sy),  (1090*sx, 110*sy))
lab("Transparent solar enclosure\n(glass cube)",  (985*sx, 360*sy),  (1140*sx, 330*sy))
lab("Silica-gel adsorbent bed\n(inner cube)",     (760*sx, 430*sy),  (40*sx, 330*sy))
lab("Base intake louvres\n(cool night air in)",   (645*sx, 600*sy),  (40*sx, 800*sy))
lab("Collection tank",                            (760*sx, 685*sy),  (1100*sx, 745*sy))
lab("Condensed water",                            (700*sx, 555*sy),  (40*sx, 560*sy), c="navy")
ax.set_title("Family-scale nested-cube AWH (box-in-box) with stack ventilation", fontsize=13)
fig.tight_layout()
fig.savefig(os.path.join(here, "awh_cube_labeled.png"), dpi=130, bbox_inches="tight")
print("wrote awh_cube_labeled.png")
PY
echo "done"
