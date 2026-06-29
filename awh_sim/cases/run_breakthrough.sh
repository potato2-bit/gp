#!/usr/bin/env bash
# VA2 / representative adsorption breakthrough with the custom solver.
# Extracts the outlet-humidity S-curve, t50, peak bed temperature (heat of adsorption).
source /usr/lib/openfoam/openfoam2406/etc/bashrc
exec > "/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/cases/_breakthrough_run.log" 2>&1
set -e

SRC="/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/cases/breakthrough"
RES="/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/results"
W="$HOME/awh_runs/breakthrough"
mkdir -p "$RES"

rm -rf "$W"; mkdir -p "$(dirname "$W")"; cp -r "$SRC" "$W"; cd "$W"
echo "######## blockMesh / topoSet ########"
blockMesh        > log.blockMesh 2>&1
topoSet          > log.topoSet   2>&1
echo "######## adsorpSilicaFoam ########"
adsorpSilicaFoam > log.solve 2>&1 || { echo "SOLVER FAILED"; tail -30 log.solve; exit 1; }
echo "  done ($(grep -c '^Time =' log.solve) steps)"

echo "######## breakthrough analysis ########"
python3 - "$W" "$RES" 0.013 <<'PY'
import sys, os, glob
W, RES, Yin = sys.argv[1], sys.argv[2], float(sys.argv[3])

def series(fo, col=-1):
    f = glob.glob(os.path.join(W,"postProcessing",fo,"*","*.dat"))[0]
    t=[]; v=[]
    for l in open(f):
        if l.startswith('#') or not l.strip(): continue
        p=l.split(); t.append(float(p[0])); v.append(float(p[col]))
    return t, v

tY, Yout = series("outletY")
tT, Tmax = series("Tmax")
_,  Tav  = series("Tavg")
_,  qav  = series("qavg")

# t50 = first time outlet/inlet ratio crosses 0.5 (linear interp)
t50=None
for i in range(1,len(tY)):
    r0,r1 = Yout[i-1]/Yin, Yout[i]/Yin
    if r0 < 0.5 <= r1:
        t50 = tY[i-1] + (0.5-r0)*(tY[i]-tY[i-1])/(r1-r0); break

Tpeak = max(Tmax)
print(f"  inlet Y       = {Yin:.4f}")
print(f"  outlet ratio  : start {Yout[0]/Yin:.3f} -> end {Yout[-1]/Yin:.3f}")
print(f"  t50 (C/C0=0.5): {('%.0f s (%.2f h)' % (t50, t50/3600)) if t50 else 'not reached in window'}")
print(f"  peak bed T    : {Tpeak:.2f} K  (dT_peak = {Tpeak-295:.2f} K from heat of adsorption)")
print(f"  final mean q  : {qav[-1]:.4f} kg/kg   final mean T: {Tav[-1]:.2f} K")

# write a tidy CSV of the breakthrough curve
import csv
with open(os.path.join(RES,"va2_breakthrough.csv"),"w",newline="") as f:
    wr=csv.writer(f); wr.writerow(["time_s","Cout_over_Cin","Tmax_K"])
    for i in range(len(tY)):
        wr.writerow([tY[i], Yout[i]/Yin, Tmax[i] if i<len(Tmax) else ""])
print(f"  saved -> results/va2_breakthrough.csv")

ok = (Yout[0]/Yin < 0.1) and (Yout[-1]/Yin > 0.3) and (Tpeak > 295.0)
print(f"\nVA2 sanity (dry start, breakthrough rises, thermal front present): {'PASS' if ok else 'CHECK'}")
PY
echo "done"
