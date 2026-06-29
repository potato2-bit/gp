#!/usr/bin/env bash
# Render extra Gazebo frames from several camera poses for labelling.
set +e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
source /opt/ros/humble/setup.bash
export DISPLAY=:0

python3 - <<'PY'
src = open('panel_world_tilt.sdf').read()
def cam(name, pose, path):
    return f'''    <model name="{name}">
      <static>true</static>
      <pose>{pose}</pose>
      <link name="link">
        <sensor name="cam" type="camera">
          <always_on>1</always_on><update_rate>2</update_rate><visualize>false</visualize>
          <camera>
            <horizontal_fov>1.05</horizontal_fov>
            <image><width>1600</width><height>1000</height><format>R8G8B8</format></image>
            <clip><near>0.05</near><far>100</far></clip>
            <save enabled="true"><path>{path}</path></save>
          </camera>
        </sensor>
      </link>
    </model>
'''
blocks  = cam("cam_wide",  "-1.0 -2.3 2.3 0 0.62 1.13", "/tmp/shot_wide")
blocks += cam("cam_close", "0.30 -1.30 1.55 0 0.52 1.05", "/tmp/shot_close")
blocks += cam("cam_low",   "-1.75 -1.75 1.30 0 0.32 0.66", "/tmp/shot_low")
src = src.replace('  </world>', blocks + '\n  </world>', 1)
open('panel_world_shot2.sdf','w').write(src)
print('world written')
PY

for d in wide close low; do rm -rf /tmp/shot_$d; mkdir -p /tmp/shot_$d; done

gzserver --verbose panel_world_shot2.sdf \
  -s libgazebo_ros_init.so -s libgazebo_ros_factory.so > /tmp/gz2.log 2>&1 &
GZ=$!
for i in $(seq 1 40); do ros2 service list 2>/dev/null | grep -q /spawn_entity && break; sleep 1; done
sleep 2
ros2 run gazebo_ros spawn_entity.py -entity pvbot -file "$HERE/pvbot.urdf" \
  -x 0.65 -y 0 -z 0.91 -P -0.41888 > /tmp/spawn2.log 2>&1
echo "spawn rc=$?"
sleep 6
kill $GZ 2>/dev/null; pkill -f gzserver 2>/dev/null; sleep 1

for d in wide close low; do
  LAST=$(ls -t /tmp/shot_$d/* 2>/dev/null | head -1)
  if [ -n "$LAST" ]; then cp "$LAST" "$HERE/shot_$d.png"; echo "shot_$d.png OK"; else echo "shot_$d EMPTY"; fi
done
