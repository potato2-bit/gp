#!/usr/bin/env bash
# V2 — Ergun Dp verification gate (Appendix A 8.1 / 8.4).
# Runs the wedge porous bed at u = 0.1/0.5/1.0 m/s, extracts the CFD pressure drop,
# and compares to the hand Ergun curve. Gate: <2% across the velocity range.
source /usr/lib/openfoam/openfoam2406/etc/bashrc
# all output -> a Windows-side log the orchestrator can read back
exec > "/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/cases/_v2_run.log" 2>&1
set -e

SRC="/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/cases/v2_ergun"
WORK="$HOME/awh_runs/v2_ergun"
RES="/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/results"
mkdir -p "$RES"

# physical constants used in the Ergun hand calc / unit conversion
RHO=1.2; MU=1.8e-5; EPS=0.38; DP=0.002; L=0.09
DARCY=2.6269e8; FORCH=1.9773e4

rm -rf "$WORK"; mkdir -p "$(dirname "$WORK")"
cp -r "$SRC" "$WORK"
cd "$WORK"

echo "######## blockMesh ########"
blockMesh > log.blockMesh 2>&1 || { echo "blockMesh FAILED"; tail -30 log.blockMesh; exit 1; }
echo "######## checkMesh ########"
checkMesh > log.checkMesh 2>&1 || true
grep -E "cells:|Mesh OK|FAILED|wedge|non-orthogonal|skewness|\*\*\*" log.checkMesh | head -40
echo
echo "######## topoSet (zone bed) ########"
topoSet > log.topoSet 2>&1 || { echo "topoSet FAILED"; tail -20 log.topoSet; exit 1; }
grep -E "Created|cellZone|cells" log.topoSet | tail -5
echo

OUT="$WORK/ergun_results.csv"
echo "u_mps,dp_cfd_Pa,dp_ergun_Pa,err_pct" > "$OUT"

for U in 0.1 0.5 1.0; do
    echo "######## simpleFoam  u=$U m/s ########"
    # reset to 0 and set the velocity in internalField + inlet
    rm -rf [1-9]* 0.[0-9]*  2>/dev/null || true
    sed -i "s/(0\.5 0 0)/($U 0 0)/g; s/([0-9.]* 0 0)/($U 0 0)/g" 0/U
    simpleFoam > log.simpleFoam.$U 2>&1 || { echo "simpleFoam FAILED u=$U"; tail -25 log.simpleFoam.$U; exit 1; }
    # inlet kinematic pressure (outlet p fixed at 0 => Dp_kin = p_inlet)
    postProcess -func "patchAverage(name=inlet,p)" -latestTime > log.pp.$U 2>&1 || true
    PKIN=$(grep -iE "average\(inlet\).* of p" log.pp.$U | tail -1 | sed -E 's/.*=[[:space:]]*//' | tr -d '() ')
    python3 - "$U" "$PKIN" "$RHO" "$MU" "$DARCY" "$FORCH" "$L" >> "$OUT" <<'PY'
import sys
u, pkin, rho, mu, d, f, L = map(float, sys.argv[1:8])
dp_cfd = rho*pkin                                  # kinematic -> Pa
dp_erg = (mu*d*u + 0.5*rho*f*u*u)*L                # Ergun hand calc
err = 100.0*abs(dp_cfd-dp_erg)/dp_erg
print(f"{u},{dp_cfd:.3f},{dp_erg:.3f},{err:.3f}")
PY
    echo "  u=$U  p_kin=$PKIN"
done

echo
echo "######## V2 Ergun comparison ########"
column -t -s, "$OUT"
cp "$OUT" "$RES/v2_ergun_results.csv"
python3 - "$OUT" <<'PY'
import csv,sys
rows=list(csv.DictReader(open(sys.argv[1])))
mx=max(float(r["err_pct"]) for r in rows)
print(f"\nmax error = {mx:.2f}%   ->  V2 GATE: {'PASS (<2%)' if mx<2.0 else 'FAIL'}")
PY
echo "saved -> results/v2_ergun_results.csv"
