#!/usr/bin/env bash
# Aggregate all 6 sites (measured irradiance) and run the 1 m3 gel annual sweep.
source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/miniforge3/etc/profile.d/conda.sh 2>/dev/null
conda activate awh
cd "/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim"
exec > "_6sites_run.log" 2>&1
set -e
SITES="aswan_benban mansoura new_alamein hurghada siwa nac"
echo "######## aggregate_cycles (measured irradiance) ########"
for s in $SITES; do
  python climate/aggregate_cycles.py --site "$s" --hourly "data/climate/nasa_power_hourly_${s}.csv"
done
echo
echo "######## run_annual  gel = 1 m3 ########"
python climate/run_annual.py --sites $SITES --gel-m3 1.0
echo "done"
