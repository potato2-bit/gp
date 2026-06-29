#!/usr/bin/env bash
# run_demo.sh - one command to see the rail-guided TEC PV-cleaning gantry work.
# Target: Gazebo Classic 11 + ROS 2 Humble on WSL2 (Ubuntu 22.04) with WSLg.
#
#   cd "/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/gazebo/pvbot_description"
#   bash run_demo.sh
#
# Brings up the 24 deg panel with guide rails, spawns the gantry carriage
# (TEC module + tank + brush + spray, riding the rails), then loops a
# fall-line cleaning sweep. Ctrl-C stops everything.
#
# NOTE: no `set -e` on purpose - a transient non-zero from a background tool
# must not tear down the whole demo.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source /opt/ros/humble/setup.bash

# Default demo uses the SMOOTH kinematic glide. The ACTUAL-MOTOR physics model
# (pvbot_railed.urdf + pvbot_motor_drive.py: a real 45 N rack-and-pinion thrust
# capped at the GA25-370/1:71/Ø30mm ceiling) lives alongside - see README and
# run_demo_motor.sh. It climbs under real force but the free-body controller is
# lively; the smooth glide below moves at the motor's real rail speed.
URDF="$HERE/pvbot.urdf"
WORLD="$HERE/panel_world_tilt.sdf"
SPAWN="-x 0.65 -y 0 -z 0.91 -P -0.41888"

cleanup() { kill $(jobs -p) 2>/dev/null; pkill -f gzserver 2>/dev/null; pkill -f gzclient 2>/dev/null; }
trap cleanup EXIT INT TERM

echo "[1/4] starting Gazebo (GUI) with the panel world..."
gazebo --verbose "$WORLD" \
  -s libgazebo_ros_init.so -s libgazebo_ros_factory.so &

echo "[2/4] waiting for the spawn service (GUI can take a while to come up)..."
for i in $(seq 1 40); do
  if ros2 service list 2>/dev/null | grep -q /spawn_entity; then
    echo "      spawn service is up."
    break
  fi
  sleep 1
done
sleep 2

echo "[3/4] spawning the gantry on the rails (foreground - waits until it exists)..."
ros2 run gazebo_ros spawn_entity.py -entity pvbot -file "$URDF" $SPAWN
# robot_state_publisher (for TF / RViz; optional for the visual demo)
ros2 run robot_state_publisher robot_state_publisher \
  --ros-args -p robot_description:="$(cat "$URDF")" &
sleep 2

echo "[4/4] rack-and-pinion drive DOWN and UP the 24 deg rail at the motor's real"
echo "      rail speed (~0.09 m/s). Ctrl-C to stop..."
# Speed = the GA25-370/1:71/Ø30mm output (0.094 m/s no-load); the climb is
# validated by scripts/rack_pinion_drive.py (45 N thrust > 35.5 N load).
python3 "$HERE/pvbot_rail_drive.py" --ros-args -p speed:=0.12 -p hz:=30.0
