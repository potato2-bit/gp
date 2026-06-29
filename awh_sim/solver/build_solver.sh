#!/usr/bin/env bash
# Compile the custom adsorpSilicaFoam solver. Output -> _build.log (Windows-readable).
source /usr/lib/openfoam/openfoam2406/etc/bashrc
exec > "/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/solver/_build.log" 2>&1
cd "/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/solver/adsorpSilicaFoam"
echo "=== wclean ==="
wclean || true
echo "=== wmake ==="
wmake
echo "WMAKE_EXIT=$?"
echo "=== binary check ==="
ls -la "$FOAM_USER_APPBIN/adsorpSilicaFoam" 2>&1 || echo "NO BINARY"
