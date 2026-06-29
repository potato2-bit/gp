#!/usr/bin/env bash
# Generate the DoE, run the CADET low-fi subset, report. Output -> _doe_run.log.
source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/miniforge3/etc/profile.d/conda.sh 2>/dev/null
conda activate awh
cd "/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim"
exec > "_doe_run.log" 2>&1
set -e
# clean leftover probe scripts from earlier sessions
rm -f cadet/_probe_*.py isotherm/_probe_*.py isotherm/_env_probe.py 2>/dev/null || true
echo "######## sample_doe ########"
python doe/sample_doe.py
echo
echo "######## run_cadet_doe (limit 120) ########"
python cadet/run_cadet_doe.py --limit 120
echo
echo "######## responses summary ########"
python - <<'PY'
import csv, statistics as st
rows=list(csv.DictReader(open("data/cadet_responses.csv")))
print(f"rows: {len(rows)}")
for k in ("m_w_kg","removal_frac","SEC_kWh_per_kg","dP_Pa"):
    v=[float(r[k]) for r in rows if r[k] not in ("","inf","nan")]
    if v: print(f"  {k:16s} min={min(v):.4g}  median={st.median(v):.4g}  max={max(v):.4g}")
PY
echo "done"
