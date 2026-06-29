#!/usr/bin/env bash
# Run the FULL launch (controllers active) and watch base_link WORLD z over time.
# On-panel z is ~0.36..0.77; ground is ~0.037. Confirms it no longer sinks.
set +e
source /opt/ros/humble/setup.bash
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$HERE"
pkill -9 -f gzserver 2>/dev/null; pkill -9 -f robot_state_pub 2>/dev/null
pkill -9 -f spawner 2>/dev/null; pkill -9 -f pvbot_rail 2>/dev/null; sleep 3

ros2 launch pvbot_control.launch.py gui:=false >/tmp/launch.log 2>&1 &
zpos() { gz model -m pvbot -i 2>/dev/null | grep -A8 'name: "pvbot::base_link"' | grep -m1 'z:' | awk '{print "base_link world z = "$2}'; }
for i in $(seq 1 16); do sleep 3; echo -n "t+$((i*3))s: "; zpos; done
echo "=== controllers ==="; grep -iE "Configured and activated" /tmp/launch.log 2>/dev/null | head -2
pkill -9 -f gzserver 2>/dev/null; pkill -9 -f robot_state_pub 2>/dev/null
pkill -9 -f pvbot_rail 2>/dev/null; pkill -9 -f spawner 2>/dev/null
echo DONE
