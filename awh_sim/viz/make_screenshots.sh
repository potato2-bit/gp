#!/usr/bin/env bash
# Rerun the breakthrough with time frames, write cell centres, render field screenshots.
source /usr/lib/openfoam/openfoam2406/etc/bashrc
exec > "/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/viz/_viz_run.log" 2>&1
set -e

SRC="/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/cases/breakthrough"
W="$HOME/awh_runs/breakthrough_viz"
SHOTS="/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/results/screenshots"

rm -rf "$W"; cp -r "$SRC" "$W"; cd "$W"
echo "######## run with frames ########"
blockMesh        > log.blockMesh 2>&1
topoSet          > log.topoSet   2>&1
adsorpSilicaFoam > log.solve      2>&1
echo "  steps: $(grep -c '^Time =' log.solve)   time dirs: $(ls -d [0-9]* | tr '\n' ' ')"
echo "######## writeCellCentres ########"
postProcess -func writeCellCentres -latestTime > log.cc 2>&1

echo "######## render (awh env) ########"
source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/miniforge3/etc/profile.d/conda.sh 2>/dev/null
conda activate awh
python "/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/viz/render_fields.py" --case "$W" --out "$SHOTS"
echo "######## screenshots ########"
ls -la "$SHOTS"
echo "done"
