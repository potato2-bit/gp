#!/usr/bin/env bash
# Render a headless Gazebo Classic frame of the AWH unit -> awh_shot.png
set +e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
export DISPLAY=:0
LOG="$HERE/_shot.log"; : > "$LOG"

echo "[1] injecting screenshot camera sensor" | tee -a "$LOG"
python3 - <<'PY'
src = open('awh_world.sdf').read()
cam = '''    <model name="shot_camera">
      <static>true</static>
      <pose>4.6 -4.6 3.0 0 0.42 2.356</pose>
      <link name="link">
        <sensor name="shot_cam" type="camera">
          <always_on>1</always_on><update_rate>2</update_rate><visualize>false</visualize>
          <camera>
            <horizontal_fov>1.0</horizontal_fov>
            <image><width>1600</width><height>1000</height><format>R8G8B8</format></image>
            <clip><near>0.05</near><far>100</far></clip>
            <save enabled="true"><path>/tmp/awhshot</path></save>
          </camera>
        </sensor>
      </link>
    </model>
  </world>'''
open('awh_world_shot.sdf','w').write(src.replace('  </world>', cam, 1))
print('   shot world written')
PY

rm -rf /tmp/awhshot; mkdir -p /tmp/awhshot
echo "[2] launching gzserver headless" | tee -a "$LOG"
gzserver --verbose awh_world_shot.sdf >> "$LOG" 2>&1 &
GZ=$!
sleep 10
kill $GZ 2>/dev/null; pkill -f gzserver 2>/dev/null; sleep 1

echo "=== /tmp/awhshot ===" | tee -a "$LOG"
ls -la /tmp/awhshot 2>/dev/null | tail -5 | tee -a "$LOG"
LAST=$(ls -t /tmp/awhshot/*.jpg /tmp/awhshot/*.png 2>/dev/null | head -1)
if [ -n "$LAST" ]; then
  cp "$LAST" "$HERE/awh_shot.png" && echo "COPIED -> awh_shot.png" | tee -a "$LOG"
else
  echo "NO FRAMES — tail of log:" | tee -a "$LOG"; tail -20 "$LOG"
fi
