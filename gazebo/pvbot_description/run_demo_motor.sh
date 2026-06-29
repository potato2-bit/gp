#!/usr/bin/env bash
# run_demo_motor.sh - the rack-and-pinion drive done RIGHT (gazebo_ros2_control).
#
# The carriage is constrained to the rail by a PRISMATIC joint and driven by an
# effort-limited velocity controller. The effort ceiling is the real motor force
# (45 N, from scripts/rack_pinion_drive.py: two GA25-370 1:71 -> Ø30 mm pinions),
# so it climbs the 24 deg rail because 45 N > 35.5 N load - smoothly, because the
# joint is a hard constraint and the velocity loop is in the controller.
#
# Validated headless: smooth controlled sweep, down 0.20 and up 1.20 along the
# rail at ~0.09 m/s (the motor's real rail speed). Needs:
#   ros-humble-gazebo-ros2-control ros-humble-velocity-controllers
#
#   cd "/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/gazebo/pvbot_description"
#   bash run_demo_motor.sh
source /opt/ros/humble/setup.bash
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pkill -9 -f gzserver 2>/dev/null; pkill -9 -f gzclient 2>/dev/null; sleep 1
exec ros2 launch "$HERE/pvbot_control.launch.py" gui:=true
