#!/usr/bin/env bash
# Full coverage on the 24 deg tilt: spawn at the lower corner, run the coverage
# node, sample odom over time. Pass = robot stays within the panel (|x|<1.0,
# |y|<0.5 in panel-local, i.e. odom bounded) and moves in BOTH axes.
set +e
source /opt/ros/humble/setup.bash
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$HERE"
pkill -9 -f gzserver 2>/dev/null; sleep 2

gzserver panel_world_tilt.sdf -s libgazebo_ros_init.so -s libgazebo_ros_factory.so >/tmp/gz.log 2>&1 &
sleep 6
# spawn near the TOP of the slope, facing up-slope; sweep mode descends first
ros2 run gazebo_ros spawn_entity.py -entity pvbot -file pvbot.urdf \
  -x 0.65 -y 0 -z 0.91 -P -0.41888 >/tmp/sp.log 2>&1
grep -o "Successfully spawned.*" /tmp/sp.log
sleep 2

odom() { ros2 topic echo --once /odom 2>/dev/null \
  | awk '/position:/{p=1} p&&/x:/{x=$2} p&&/y:/{y=$2} p&&/z:/{print "x="x" y="y" z="$2; exit}'; }

echo "[rail-guided SWEEP on tilt: clean_speed 0.06, 2 fall-line passes]"
python3 pvbot_coverage.py --ros-args -p mode:=sweep -p clean_speed:=0.06 \
  -p stroke_len:=1.4 -p n_sweeps:=2 >/tmp/cov.log 2>&1 &
COV=$!
echo -n "  t0   "; odom
for t in 12 12 12 12 12 12; do sleep $t; echo -n "  t+    "; odom; done
echo "--- coverage log (segments) ---"; grep -oE '(sweep|rail-guided).*' /tmp/cov.log | tail -8
kill $COV 2>/dev/null; pkill -9 -f gzserver 2>/dev/null
echo "TILTCOV_DONE"
