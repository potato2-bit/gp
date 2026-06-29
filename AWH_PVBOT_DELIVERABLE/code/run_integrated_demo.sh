#!/usr/bin/env bash
# run_integrated_demo.sh - the AWH <-> PVbot coupling, LIVE in Gazebo + ROS 2.
# Target: Gazebo Classic 11 + ROS 2 Humble on WSL2 (Ubuntu 22.04) with WSLg.
#
#   cd "/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/integration"
#   bash run_integrated_demo.sh            # defaults: site=nac, gel=45 kg
#   SITE=aswan_benban GEL=68 bash run_integrated_demo.sh
#
# Brings up the tilted panel world (which already carries the AWG dock at the
# rail base), spawns the cleaning carriage, starts the fall-line cleaning sweep,
# and -- the new piece -- starts awh_water_bus.py, which listens to the sweep's
# `spray_on` topic and closes the water loop: AWH harvest fills the dock, the
# spray drains the tank, the dock tops the tank up, and a running balance is
# logged. Ctrl-C stops everything and prints the final water balance.
#
# No `set -e`: a transient non-zero from a background tool must not kill the demo.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GZ="$HERE/../gazebo/pvbot_description"
source /opt/ros/humble/setup.bash

SITE="${SITE:-nac}"
GEL="${GEL:-45}"
AREA="${AREA:-46.0}"
DAY_SECONDS="${DAY_SECONDS:-3.0}"     # compress one climate day into 3 wall-seconds
SPRAY_RATE="${SPRAY_RATE:-0.05}"      # L/s design spray rate

URDF="$GZ/pvbot.urdf"
WORLD="$GZ/panel_world_tilt.sdf"      # 24 deg panel + guide rails + AWG dock
SPAWN="-x 0.65 -y 0 -z 0.91 -P -0.41888"

cleanup() { kill $(jobs -p) 2>/dev/null; pkill -f gzserver 2>/dev/null; pkill -f gzclient 2>/dev/null; }
trap cleanup EXIT INT TERM

echo "[1/5] starting Gazebo with the tilted panel + AWG dock world..."
gazebo --verbose "$WORLD" \
  -s libgazebo_ros_init.so -s libgazebo_ros_factory.so &

echo "[2/5] waiting for the spawn service..."
for i in $(seq 1 40); do
  ros2 service list 2>/dev/null | grep -q /spawn_entity && { echo "      spawn up."; break; }
  sleep 1
done
sleep 2

echo "[3/5] spawning the cleaning carriage on the rails..."
ros2 run gazebo_ros spawn_entity.py -entity pvbot -file "$URDF" $SPAWN
sleep 2

echo "[4/5] starting the AWH water bus (site=$SITE, gel=$GEL kg, 1 day/${DAY_SECONDS}s)..."
python3 "$HERE/awh_water_bus.py" --ros-args \
  -p site:="$SITE" -p gel_kg:="$GEL" -p area_m2:="$AREA" \
  -p day_seconds:="$DAY_SECONDS" -p spray_rate_Lps:="$SPRAY_RATE" &
sleep 1

echo "[5/5] running the fall-line cleaning sweep (publishes spray_on -> water bus)."
echo "      watch:  ros2 topic echo /awh/dock_reservoir   and  /awh/self_supply"
echo "      Ctrl-C to stop and print the final water balance."
python3 "$GZ/pvbot_coverage.py" --ros-args \
  -p mode:=sweep -p clean_speed:=0.06 -p stroke_len:=1.4 -p n_sweeps:=8
