#!/usr/bin/env bash
# V1 — box / mass-balance + sign test (Appendix A 8.1).
# Closed, no-flow bed. Adsorption box: expect Y down, T up. Desorption box: Y up, T down.
# Water-balance closure |D(gas+solid water)| / initial water < 0.5%.
source /usr/lib/openfoam/openfoam2406/etc/bashrc
exec > "/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/cases/_v1_run.log" 2>&1
set -e

SRC="/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/cases/v1_box"
RES="/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/results"

run_box () {
    local tag="$1" T0="$2" q0="$3" Y0="$4"
    local W="$HOME/awh_runs/v1_$tag"
    rm -rf "$W"; mkdir -p "$(dirname "$W")"; cp -r "$SRC" "$W"; cd "$W"
    sed -i "s/uniform 295;/uniform $T0;/"   0/T
    sed -i "s/uniform 0;/uniform $q0;/"     0/q
    sed -i "s/uniform 0.013;/uniform $Y0;/" 0/Y
    echo "######## $tag box: T0=$T0 q0=$q0 Y0=$Y0 ########"
    blockMesh           > log.blockMesh 2>&1
    topoSet             > log.topoSet   2>&1
    adsorpSilicaFoam    > log.solve      2>&1 || { echo "SOLVER FAILED"; tail -25 log.solve; exit 1; }
    echo "  solver done ($(grep -c '^Time =' log.solve) steps)"
}

run_box ads 295 0   0.013
run_box des 355 0.12 0.002

echo
echo "######## V1 analysis ########"
python3 - "$HOME/awh_runs/v1_ads" 0.013 0 295 "$HOME/awh_runs/v1_des" 0.002 0.12 355 "$RES" <<'PY'
import sys, os, glob
eps, rhoG, rhoS = 0.38, 1.2, 750.0

def lastval(case, fo, col=-1):
    f = glob.glob(os.path.join(case,"postProcessing",fo,"*","volFieldValue.dat"))[0]
    V = None
    rows=[]
    for l in open(f):
        if l.startswith('#'):
            if 'Volume' in l: V = float(l.split(':')[1])
            continue
        if l.strip(): rows.append(l.split())
    return float(rows[-1][col]), V

def analyse(case, name, Y0, q0, T0):
    iY1,V = lastval(case,"intY")               # integral of Y over volume [m3] (final)
    iQ1,_ = lastval(case,"intQ")               # integral of q over volume [m3] (final)
    Ta1,_ = lastval(case,"Tavg")
    Ya1,_ = lastval(case,"Yavg")
    # analytic initial water from uniform ICs over the same volume V
    gas0, gas1 = eps*rhoG*Y0*V, eps*rhoG*iY1
    sol0, sol1 = (1-eps)*rhoS*q0*V, (1-eps)*rhoS*iQ1
    tot0, tot1 = gas0+sol0, gas1+sol1
    closure = 100.0*abs(tot1-tot0)/tot0
    dY, dT = Ya1-Y0, Ta1-T0
    print(f"\n[{name}]  V={V:.4e} m3")
    print(f"  Y: {Y0:.5f} -> {Ya1:.5f}  (dY={dY:+.5f})")
    print(f"  T: {T0:.2f} -> {Ta1:.2f} K (dT={dT:+.2f})")
    print(f"  water gas:   {gas0:.6e} -> {gas1:.6e} kg")
    print(f"  water solid: {sol0:.6e} -> {sol1:.6e} kg")
    print(f"  total water: {tot0:.6e} -> {tot1:.6e} kg   closure={closure:.4f}%")
    return closure, dY, dT

ca,dYa,dTa = analyse(sys.argv[1], "adsorption", float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]))
cd,dYd,dTd = analyse(sys.argv[5], "desorption", float(sys.argv[6]), float(sys.argv[7]), float(sys.argv[8]))

sign_ok = (dYa<0 and dTa>0) and (dYd>0 and dTd<0)
clos_ok = (ca<0.5 and cd<0.5)
print(f"\nsign discipline : ads(Y-,T+) des(Y+,T-) -> {'OK' if sign_ok else 'FAIL'}")
print(f"mass closure    : ads={ca:.3f}%  des={cd:.3f}%  (<0.5%?) -> {'OK' if clos_ok else 'FAIL'}")
print(f"\nV1 GATE: {'PASS' if (sign_ok and clos_ok) else 'FAIL'}")
PY
echo "done"
