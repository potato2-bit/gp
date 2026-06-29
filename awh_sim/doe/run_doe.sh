#!/usr/bin/env bash
# Run the high-fidelity OpenFOAM DoE under WSL2.
# Each case is small (2-D axisymmetric) so parallelise ACROSS cases, not within.
# Run on ext4 (~/awh_runs), NOT /mnt/c.  See docs/DESIGN_SPEC.md §9, Appendix A §9.
set -euo pipefail

CASES_DIR="${1:-cases}"
JOBS="${2:-$(nproc)}"

run_one() {
  local d="$1"
  cd "$d"
  blockMesh > log.blockMesh 2>&1
  checkMesh > log.checkMesh 2>&1
  # <solver> > log.solve 2>&1     # TODO Step 4: custom adsorption solver name
  postProcess -func 'patchAverage(name=outlet,fields=(H2O T))' > log.post 2>&1 || true
  cd - >/dev/null
}
export -f run_one

# Batch ACROSS cases with xargs -P (always available — no GNU parallel install needed).
# Optional GNU parallel equivalent: parallel -j "${JOBS}" run_one ::: "${CASES_DIR}"/run_*
echo "STUB: would run cases in ${CASES_DIR} across ${JOBS} jobs (xargs -P)."
# ls -d "${CASES_DIR}"/run_* | xargs -P "${JOBS}" -I{} bash -c 'run_one "$1"' _ {}
