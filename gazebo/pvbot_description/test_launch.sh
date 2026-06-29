#!/usr/bin/env bash
# Headless test of pvbot_control.launch.py: bring the whole ros2_control stack
# up and sample rail_slide position to confirm a smooth down+up climb.
set +e
source /opt/ros/humble/setup.bash
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$HERE"
pkill -9 -f gzserver 2>/dev/null; pkill -9 -f gzclient 2>/dev/null
pkill -9 -f spawner 2>/dev/null; pkill -9 -f robot_state_pub 2>/dev/null
pkill -9 -f pvbot_rail_controller 2>/dev/null; sleep 3

ros2 launch pvbot_control.launch.py gui:=false >/tmp/launch.log 2>&1 &
LP=$!
sleep 34
echo "=== nodes ==="; ros2 node list 2>/dev/null | head -8
echo "=== joint topics ==="; ros2 topic list 2>/dev/null | grep -iE "joint|rail|control" | head -8
echo "=== controllers ==="
ros2 control list_controllers 2>&1 | head -4
echo "=== rail_slide trajectory (rclpy monitor, ~24 s) ==="
python3 _monitor_rail.py 2>/dev/null

kill $LP 2>/dev/null
pkill -9 -f gzserver 2>/dev/null; pkill -9 -f robot_state_pub 2>/dev/null
pkill -9 -f pvbot_rail_controller 2>/dev/null
echo "=== launch errors ==="
grep -iE "error|exception|not available|failed" /tmp/launch.log 2>/dev/null | grep -ivE "waiting|will be truncated" | head -5
echo DONE
