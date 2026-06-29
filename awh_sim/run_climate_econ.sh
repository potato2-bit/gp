#!/usr/bin/env bash
# Climate -> annual water -> LCOW for the cached sites. Output -> _climate_run.log.
source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/miniforge3/etc/profile.d/conda.sh 2>/dev/null
conda activate awh
cd "/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim"
exec > "_climate_run.log" 2>&1
set -e
echo "######## aggregate_cycles ########"
python climate/aggregate_cycles.py --site aswan_benban --hourly ../output/nasa_power_hourly.csv
python climate/aggregate_cycles.py --site nac          --hourly ../output/nac_nasa_power_hourly.csv
echo
echo "######## run_annual ########"
python climate/run_annual.py --sites aswan_benban nac
echo
echo "######## LCOW ########"
python economics/lcow.py
echo "done"
