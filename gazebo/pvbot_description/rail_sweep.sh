#!/usr/bin/env bash
# rail_sweep.sh - kinematic rail drive for the gantry carriage.
#
# A free-wheel model cannot climb 24 deg glass (the wheels break traction and
# slide). The real drive is a RACK-AND-PINION: a positive, geared drive that is
# constrained to the rail and cannot slip. This script reproduces that by
# gliding the carriage along the rail line by setting its pose - down the slope
# (cleaning) then back up (return) - so it moves smoothly BOTH ways.
#
# The rail line in world coords was measured from the physics run:
#   top    (x=0.65, z=0.91)   <-> bottom (x=-0.72, z=0.28),  pitch -0.41888 rad.
set +e
TOP_X=0.65;  TOP_Z=0.91
BOT_X=-0.72; BOT_Z=0.28
PITCH=-0.41888
STEPS=${STEPS:-30}
DT=${DT:-0.05}

place() {            # $1 = fraction 0(top) .. 1(bottom)
  local t="$1"
  local x z
  x=$(awk "BEGIN{printf \"%.4f\", $TOP_X+($BOT_X-$TOP_X)*$t}")
  z=$(awk "BEGIN{printf \"%.4f\", $TOP_Z+($BOT_Z-$TOP_Z)*$t}")
  gz model -m pvbot -x "$x" -y 0 -z "$z" -R 0 -P "$PITCH" -Y 0 >/dev/null 2>&1
}

# descend the rail (cleaning pass)
for i in $(seq 0 "$STEPS"); do
  place "$(awk "BEGIN{printf \"%.4f\", $i/$STEPS}")"
  sleep "$DT"
done
sleep 0.4
# climb back up the rail (rack-and-pinion return)
for i in $(seq "$STEPS" -1 0); do
  place "$(awk "BEGIN{printf \"%.4f\", $i/$STEPS}")"
  sleep "$DT"
done
sleep 0.4
