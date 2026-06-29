#!/usr/bin/env bash
# Render a real headless Gazebo Classic frame of the finished model.
set +e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
source /opt/ros/humble/setup.bash
export DISPLAY=:0

echo "[1] building shot world (camera sensor injected)"
python3 - <<'PY'
src = open('panel_world_tilt.sdf').read()
cam = '''    <!-- headless screenshot camera sensor -->
    <model name="shot_camera">
      <static>true</static>
      <pose>-1.0 -2.3 2.3 0 0.62 1.13</pose>
      <link name="link">
        <sensor name="shot_cam" type="camera">
          <always_on>1</always_on>
          <update_rate>2</update_rate>
          <visualize>false</visualize>
          <camera>
            <horizontal_fov>1.05</horizontal_fov>
            <image><width>1600</width><height>1000</height><format>R8G8B8</format></image>
            <clip><near>0.05</near><far>100</far></clip>
            <save enabled="true"><path>/tmp/gzshot</path></save>
          </camera>
        </sensor>
      </link>
    </model>

  </world>'''
src = src.replace('  </world>', cam, 1)
open('panel_world_shot.sdf', 'w').write(src)
print('   world written, bytes=', len(src))
PY

rm -rf /tmp/gzshot; mkdir -p /tmp/gzshot

echo "[2] launching gzserver headless (ROS factory)"
gzserver --verbose panel_world_shot.sdf \
  -s libgazebo_ros_init.so -s libgazebo_ros_factory.so > /tmp/gz.log 2>&1 &
GZ=$!

echo "[3] waiting for /spawn_entity"
for i in $(seq 1 40); do
  ros2 service list 2>/dev/null | grep -q /spawn_entity && { echo "   spawn up"; break; }
  sleep 1
done
sleep 2

echo "[4] spawning robot at demo pose"
ros2 run gazebo_ros spawn_entity.py -entity pvbot -file "$HERE/pvbot.urdf" \
  -x 0.65 -y 0 -z 0.91 -P -0.41888 > /tmp/spawn.log 2>&1
echo "   spawn rc=$?"

echo "[5] letting camera save frames (robot in scene)"
sleep 6

kill $GZ 2>/dev/null; pkill -f gzserver 2>/dev/null; sleep 1

echo "=== /tmp/gzshot ==="
ls -la /tmp/gzshot 2>/dev/null | tail -10
LAST=$(ls -t /tmp/gzshot/* 2>/dev/null | head -1)
echo "LAST=$LAST"
if [ -n "$LAST" ]; then
  cp "$LAST" "$HERE/gazebo_real_shot.png" && echo "COPIED -> gazebo_real_shot.png"
else
  echo "NO FRAMES — tail of gz.log:"; tail -25 /tmp/gz.log
fi
