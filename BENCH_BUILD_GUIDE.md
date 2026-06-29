# Bench Build Guide — what to build now with what you have

**Updated 2026-06-17.** Inventory basis: RAM order S148371 + Future Electronics order 210690 (see the procurement table in `MINIMUM_PROTOTYPE_BUYLIST.md`).

The point of this guide: get the **motion carriage running end-to-end this week** with the parts already in your hands, and prep the TEC tiles so you can drop them in the moment the heatsinks and the big 12 V supply arrive.

---

## What you can build today vs what's blocked

**Build now (everything is in hand):**
- The **rail + carriage + belt drive**, motor, encoder, limit switches, ESP32, L298N, 5 V buck.
- Firmware that drives the carriage from end to end, reverses on the limit switches, and counts encoder ticks for position.

**Blocked until you buy more:**
- **TEC water harvesting** — you have the 4 tiles, but no hot-side heatsinks, no cold plate, no thermal paste, and no high-current 12 V supply. Running a tile without a hot-side sink destroys it in under a minute. So: prep and label the tiles now, run them later.

**Power note:** the motion build needs a **12 V source of only a few amps** — a spare 12 V/2–5 A wall adapter, a laptop-type brick, or an old PC ATX supply all work. You do **not** need the LRS-350-12 yet; that one is only for the four tiles (≈24 A).

---

## 1. Find and label the hot/cold side of each TEC (do this first)

You asked how to tell the sides apart. Do not trust the printed label or the photos online — confirm it yourself, it takes 30 seconds per tile and you only do it once.

**The wiring convention (your starting guess):**
- A genuine TEC1-12706 has a **red** and a **black** wire.
- Wire **red → +12 V**, **black → −/GND**.
- With that polarity, the face **opposite** the side the wires exit goes cold; the wire-exit face goes hot. *Conventions vary between batches, which is exactly why you test instead of trusting this.*

**The test that actually settles it (do this for all 4):**
1. Set a bench supply or adapter to a **low voltage — 3 to 5 V, not 12 V**. Lay the tile on the table, nothing clamped to it.
2. Touch red to +, black to −, for **5–10 seconds only**. One face turns noticeably cold, the other warm — you can feel it with a fingertip, or read it with one of your DS18B20 probes.
3. Mark the **cold** face with a permanent marker (a dot or "C"). That is the side that will face your condensing/cold plate; the other side bolts to the heatsink.
4. If the side you expected to be cold came out hot, your polarity is reversed — swap the leads, or just flip your mark. Either is fine; just keep all four tiles oriented the same way in the stack.

**Two hard rules:**
- **Never** run a tile at full 12 V without a heatsink clamped to the hot side. The hot side hits 80 °C+ in seconds with nowhere to dump heat, and the solder inside the module melts. The 3–5 V, few-second test above is safe precisely because it is brief and low-power.
- The stack is always **cold plate → TEC cold side / TEC hot side → heatsink → fan**, with thermal paste at every metal-to-metal joint. Water condenses on the cold plate.

---

## 2. Mechanical: rail, carriage, belt

You have a 1 m 2040 V-slot rail, one OpenBuilds mini V-gantry plate with wheels, a GT2 belt, two 20-tooth GT2 pulleys, an idler kit, M5 T-nuts, and L-brackets.

**Layout (fixed motor, moving carriage — the 3D-printer X-axis pattern):**

```
   [MOTOR + pulley]====belt====(idler pulley)
        |                            |
   left end                      right end
        |---------- 1 m rail ----------|
              [GANTRY CARRIAGE]   <- belt ends clamp to it
   [LIM_L]                         [LIM_R]
```

**Steps:**
1. **Mount the rail to a base.** Screw the 1 m rail down to a flat board or bench using two of the L corner brackets + M5 T-nuts at the ends. Keep it straight and rigid. Start **flat/horizontal** — incline comes later.
2. **Fit the gantry plate** onto the rail so its V-wheels seat in the slot. Adjust the eccentric nut(s) on the gantry so the wheels roll smoothly with no rock and no slop. It should glide by hand the full length.
3. **Mount the motor** at the left end. Use the GA25 round-body bracket (still to buy) or, until it arrives, clamp the motor body to an L-bracket so its shaft points along the rail and the pulley lines up with the belt path.
4. ⚠ **Pulley-to-shaft fit check — this commonly bites.** Your GT2 pulleys have a **5 mm bore**, and the GA25-370 output shaft is a smaller **D-shaft (≈4 mm)**. Measure both. If the bore is loose on the shaft: ream/sleeve it, file a flat for the grub screw to bite, or get a pulley matched to the actual shaft. The pulley must lock to the shaft or the belt just slips and nothing moves.
5. **Mount the idler** at the right end so the belt runs parallel to the rail at the height of the gantry's belt-clamp slot.
6. **Route the belt:** anchor one belt end to the carriage, run it around the idler, back to the motor pulley, around it, and anchor the other end to the carriage. Tension it so it is firm with no sag but still turns freely. Teeth meshed on both pulleys.
7. **Limit switches** at each end, positioned so the carriage trips them just before it runs off either end. Wire each on its **COM + NO** terminals (reads as a closed-to-ground contact when pressed). The straight-hinge switch and the roller-lever switch are interchangeable here — put either at either end.

---

## 3. Electronics: wiring the motion loop

**Power tree:**
```
12 V source ──┬── L298N  +12V (VS)   ── drives the motor
              └── DC-DC buck IN ── 5 V OUT ── ESP32 5V (VIN) pin
ALL grounds tied together (12 V GND, buck GND, L298N GND, ESP32 GND).
```
Common ground is not optional — if the ESP32 ground and the L298N ground are not joined, the control signals float and the motor does random things.

**L298N ↔ ESP32:**
| L298N pin | Goes to | Purpose |
|---|---|---|
| ENA | ESP32 GPIO25 | PWM speed |
| IN1 | ESP32 GPIO26 | direction A |
| IN2 | ESP32 GPIO27 | direction B |
| OUT1 / OUT2 | motor M+ / M− (the **thick** pair) | motor power |
| +12V (VS) | 12 V source | motor supply |
| GND | common ground | |
| +5V | leave; do **not** also feed the ESP32 from here if the buck already does — pick one 5 V source | |

Remove the ENA jumper on the L298N so your PWM controls speed (jumper on = full speed always).

**GA25-370 encoder (6 wires — colors vary, confirm against your seller):**
| Typical color | Connect to |
|---|---|
| Red | motor M+ → L298N OUT1 |
| Black/White (thick) | motor M− → L298N OUT2 |
| Blue | encoder Vcc → **ESP32 3V3** |
| Green | encoder GND → common ground |
| Yellow | encoder A → ESP32 GPIO32 |
| White (thin) | encoder B → ESP32 GPIO33 |

To find the **motor pair**: the two leads that spin the motor when you brush them on a battery are M+/M−; the other four are the encoder. Power the encoder from **3.3 V** (not 5 V) so its output pulses stay inside the ESP32's safe input range.

**Limit switches:**
| Switch | ESP32 pin | Wiring |
|---|---|---|
| LIM_L | GPIO18 (INPUT_PULLUP) | COM→GND, NO→GPIO18 |
| LIM_R | GPIO19 (INPUT_PULLUP) | COM→GND, NO→GPIO19 |

Pressed = pin pulled LOW.

---

## 4. Firmware — minimal sweep + encoder (ESP32 Arduino core 3.x)

Flash this, open the serial monitor at 115200, and the carriage should drive to one end, reverse at the limit switch, and report encoder counts. Tune `DUTY` down until the speed looks like a cleaning sweep (~0.08 m/s).

```cpp
// Bench motion test: GA25-370 on L298N, encoder feedback, limit-switch reverse.
// ESP32 Arduino core 3.x (uses ledcAttach/ledcWrite).

const int ENA = 25, IN1 = 26, IN2 = 27;   // L298N
const int ENC_A = 32, ENC_B = 33;          // encoder channels
const int LIM_L = 18, LIM_R = 19;          // end stops

const int PWM_FREQ = 20000, PWM_RES = 8;   // 20 kHz, 0-255
int DUTY = 120;                            // ~47% -> slow it to sweep speed

volatile long ticks = 0;
int dir = +1;                              // +1 = toward right, -1 = toward left

void IRAM_ATTR encISR() {
  // quadrature: read B at A's rising edge to get direction
  if (digitalRead(ENC_B)) ticks++; else ticks--;
}

void drive(int d) {                        // d = +1, -1, or 0 (stop)
  if (d > 0)      { digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);  ledcWrite(ENA, DUTY); }
  else if (d < 0) { digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH); ledcWrite(ENA, DUTY); }
  else            { digitalWrite(IN1, LOW);  digitalWrite(IN2, LOW);  ledcWrite(ENA, 0); }
}

void setup() {
  Serial.begin(115200);
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  ledcAttach(ENA, PWM_FREQ, PWM_RES);
  pinMode(ENC_A, INPUT_PULLUP); pinMode(ENC_B, INPUT_PULLUP);
  pinMode(LIM_L, INPUT_PULLUP); pinMode(LIM_R, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_A), encISR, RISING);
  drive(dir);
}

void loop() {
  if (dir > 0 && digitalRead(LIM_R) == LOW) {   // hit right end
    drive(0); delay(300); dir = -1; drive(dir);
  }
  if (dir < 0 && digitalRead(LIM_L) == LOW) {   // hit left end
    drive(0); delay(300); dir = +1; drive(dir);
  }
  static unsigned long t = 0;
  if (millis() - t > 200) { t = millis();
    Serial.printf("dir %+d  ticks %ld\n", dir, ticks);
  }
}
```

**First-run checklist:**
- If the motor runs the *wrong way* relative to your limit switches, swap IN1/IN2 in the wiring or swap `dir` signs — the carriage must move *toward* the switch it is checking.
- If `ticks` jumps around or never changes, the encoder Vcc/GND or A/B wiring is off; confirm 3.3 V on Vcc and that A/B are the two thin signal wires.
- If the belt slips (motor spins, carriage doesn't move full travel), the pulley grub screw isn't biting the shaft — back to step 2.4.

---

## 5. Test plan (motion)

1. **Bench-glide, no power:** push the carriage by hand end to end. Smooth, no rock, switches trip. Fix mechanics before adding power.
2. **Horizontal drive:** flash the sketch, watch it sweep and reverse. Note encoder ticks per full length — that's your position calibration (ticks → mm).
3. **Speed trim:** lower `DUTY` until one length takes about as long as a real cleaning pass (rail length ÷ 0.08 m/s ≈ 12.5 s for 1 m). Log it.
4. **Incline:** prop the rail to ~10–15° first, then toward 24°. Watch whether the belt holds the carriage on the slope when stopped. On the bench this shows the slide problem the deployment rack-and-pinion solves; note it for the report — you are not expected to climb 24° on a belt.

---

## 6. TEC prep you can do now (so harvest is plug-in later)

Even though you can't run the tiles yet, do the prep:
1. **Label all 4 cold sides** (section 1).
2. **Plan the stack:** decide the cold plate (a flat Al bar/plate, to buy/machine) the four cold faces press against, and four heatsinks for the hot faces. One 40 mm fan you have can sit on the **cold-plate** side to pull humid room air across it; the hot-side heatsinks need their own bigger fans (still to buy).
3. **Gate-driver circuit for the IRF540N** (only if you want PWM/on-off control rather than hardwired-on). The IRF540N is not logic-level, so use a 2N2222 to swing its gate to 12 V:
   ```
   ESP32 GPIO ──[1kΩ]── base (2N2222)
   2N2222 emitter ── GND
   2N2222 collector ──┬── IRF540N gate
                      └──[10kΩ]── +12V        (pull-up)
   IRF540N source ── GND ;  drain ── TEC −  ;  TEC + ── +12V
   ```
   Note this **inverts** the logic (GPIO HIGH = tile OFF). One transistor + two resistors per tile; you have 5 transistors and 5 resistors, enough for four tiles.
4. **For the very first water test you can skip the MOSFETs entirely** — wire the tiles' hot sides to heatsinks, feed them straight from the 12 V supply, and just measure condensate on a kitchen scale. Add switching/PWM afterward.

**Then buy, in this order:** heatsinks + paste + cold plate → 12 V high-current PSU → roller/microfibre + nozzles + tank → wiring/protoboard. Full list with prices in `MINIMUM_PROTOTYPE_BUYLIST.md`.

---

## One-line status

Motion bench is fully buildable today. Water harvesting waits on hot-side heatsinks and a ≥24 A 12 V supply — until then, label the tiles and build the carriage.
