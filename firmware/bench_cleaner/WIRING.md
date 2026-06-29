# Bench Cleaner — Complete Wiring Reference

Solar-AWH PV-Cleaning Robot, bench prototype. Matches `bench_cleaner.ino`.

## Board roles
- **Board #1** (dual L298N) = **H-BRIDGE / DRIVE board** → Rail L on ch A, Rail R on ch B (driven as one).
- **Board #2** (dual L298N) = **CLEAN board** → ch A = brush, ch B = pump.
- **ESP32 DevKit 30-pin** = the controller.
- **Buck converter** = 12 V → 5 V. **ACS712** = current sensor. **DHT22/AM2302** = humidity.

---

## 1. How 12 V becomes 3.3 V (two regulators, in series)

12 V never touches a 3.3 V part. It steps down twice:

```
12 V ──▶ [BUCK module] ──▶ 5 V ──▶ ESP32 "5V/VIN" pin ──▶ [ESP32 onboard
                                                          AMS1117-3.3 regulator] ──▶ 3.3 V
                                                          (out on the "3V3" pin)
```

1. **12 V → 5 V** in the **buck converter** (your DC-DC step-down module). Set/confirm 5 V.
2. **5 V → 3.3 V** *inside the ESP32 board* — its onboard **AMS1117-3.3** regulator. Feed 5 V
   into **5V (VIN)**; the board outputs 3.3 V on the **3V3** pin.

The **3V3 pin is an OUTPUT** the ESP32 makes — it powers the encoder and the DHT22.
Each L298N separately makes its own 5 V from 12 V (onboard 78M05, when its 5V jumper is on);
that board-5V feeds only the brush/pump direction ties. **Do not power the ESP32 from it.**

---

## 2. Jumper prep (both L298N boards)

- **ENA & ENB jumpers → REMOVE** on both boards (so ESP32 PWM controls speed).
- **5V-regulator jumper → LEAVE ON** (12 V supply; this gives the board's 5V pin).

---

## 3. Power & ground harness

| From | To |
|---|---|
| 12 V supply **(+)** | ACS712 **Ip+** |
| ACS712 **Ip−** | Board #1 **VS(+12V)** · Board #2 **VS(+12V)** · buck **IN+** |
| 12 V supply **(−)** | common ground bus |
| buck **5V OUT** | ESP32 **5V(VIN)** · ACS712 **VCC** |
| ESP32 **3V3 OUT** | encoder **Vcc** · DHT22 **VCC** |

**Common ground bus — tie ALL of these together:** 12 V(−), buck GND, Board #1 GND,
Board #2 GND, ESP32 GND, ACS712 GND, encoder GND, DHT22 GND, both limit-switch COMs.

> Motors see ~10 V (each L298N drops ~2 V). Normal — everything still runs.

---

## 4. Board #1 (H-BRIDGE) → ESP32  — rails

Two motors = **two channels**. Motor A (Rail L) on **channel A**, Motor B (Rail R) on
**channel B** — each to its **own** outputs. The firmware drives both together and **reverses
channel B in software** (because the motors face each other) so they move as **one**.

| Board #1 pin | ESP32 GPIO |
|---|---|
| ENA | **25** |
| IN1 | **26** |
| IN2 | **27** |
| ENB | **14** |
| IN3 | **16** |
| IN4 | **17** |

### Motor wiring — each motor to its own outputs (no crossing)

| Wire (typical colour — **confirm yours**) | To |
|---|---|
| **Rail L (Motor A)** power A (**red**) | Board #1 **OUT1** |
| **Rail L (Motor A)** power B (**white**) | Board #1 **OUT2** |
| **Rail R (Motor B)** power A (**red**) | Board #1 **OUT3** |
| **Rail R (Motor B)** power B (**white**) | Board #1 **OUT4** |
| **Rail L** encoder Vcc (**blue**) | ESP32 **3V3** |
| **Rail L** encoder GND (**black**) | common ground |
| **Rail L** encoder A / C1 (**yellow**) | ESP32 **32** |
| **Rail L** encoder B / C2 (**green**) | ESP32 **33** |
| **Rail R** 4 encoder wires | tape off (only one encoder is read) |

> Each motor's **2 thick power wires** go to its channel's outputs; the other 4 are the encoder.
> The firmware reverses ch B (`RAIL_R_REVERSED 1`) so both travel the same way — **no crossed
> wires**. **Test:** type `f`; if Rail R goes the wrong way, set `RAIL_R_REVERSED 0` (your two
> motors are mounted the same way, not mirrored).

---

## 5. Board #2 (CLEAN) → ESP32  — brush + pump

Brush and pump spin one way only, so their direction is **hardwired on the board** and the
ESP32 controls only their EN (speed).

| Board #2 pin | Wire to |
|---|---|
| **ENA** (ch A) | ESP32 **23** |
| IN1 (ch A) | Board #2 **5V** (fixes brush direction) |
| IN2 (ch A) | Board #2 **GND** |
| **ENB** (ch B) | ESP32 **22** |
| IN3 (ch B) | Board #2 **5V** (fixes pump direction) |
| IN4 (ch B) | Board #2 **GND** |

### Brush motor (2 wires)
| Brush wire | To |
|---|---|
| wire 1 | Board #2 **OUT1** |
| wire 2 | Board #2 **OUT2** |
*(wrong way? swap these two.)*

### Pump (2 wires — submersible, sits in the tank)
| Pump wire | To |
|---|---|
| **red** | Board #2 **OUT3** |
| **black** | Board #2 **OUT4** |

---

## 6. ACS712 current sensor

| ACS712 pin | To |
|---|---|
| **Ip+** (screw) | 12 V supply (+) |
| **Ip−** (screw) | the +12 V feeding both boards' VS |
| **VCC** | buck 5 V |
| **GND** | common ground |
| **OUT** | **10 kΩ → GPIO34**, and **GPIO34 → 10 kΩ → GND** (÷2 divider — protects the pin) |

## 7. DHT22 / AM2302 humidity sensor

| DHT22 pin | To |
|---|---|
| **+ / VCC** | ESP32 **3V3** |
| **OUT / DATA** | ESP32 **GPIO4** |
| **− / GND** | common ground |

3-pin module: those three wires. Bare 4-pin sensor: add a 4.7 kΩ–10 kΩ pull-up DATA→3V3
(pin 3 unused). Needs Adafruit "DHT sensor library" + "Adafruit Unified Sensor".

## 8. Limit switches

| Switch | Wiring |
|---|---|
| LIM_L | COM → GND, **NO → GPIO18** |
| LIM_R | COM → GND, **NO → GPIO19** |

---

## Master ESP32 pin table

| GPIO | Role |
|---|---|
| 25 / 26 / 27 | Board #1 ENA / IN1 / IN2 — **Rail L (Motor A)** |
| 14 / 16 / 17 | Board #1 ENB / IN3 / IN4 — **Rail R (Motor B)** |
| 23 | Board #2 ch A EN — **Brush** speed |
| 22 | Board #2 ch B EN — **Pump** speed |
| 32 / 33 | Encoder A / B (Rail-L motor) |
| 18 / 19 | LIM_L / LIM_R |
| 34 | ACS712 OUT (via ÷2 divider) |
| 4 | DHT22 DATA |
| 3V3 | encoder Vcc + DHT22 VCC (ESP32 makes this from the 5 V) |
| 5V (VIN) | from buck |
| GND | common bus |

---

## Serial control (115200, line ending = Newline)

| Type | Does |
|---|---|
| `r120` | set **rail** speed (0–255) |
| `b200` | set **brush** speed |
| `p180` | set **pump** speed |
| `f` / `v` | rails forward / reverse |
| `x` | rails stop |
| `m` | brush on/off |
| `w` | pump on/off |
| `g` | run auto cleaning sweep |
| `s` | STOP everything |

Telemetry line: `[mode] rail.. br.. pu.. | ticks .. pos ..mm spray ..mL I ..A | ..%RH ..C dew ..C`

## Power-on checks (in order)
1. Confirm **5 V** on the buck output and **3.3 V** on the ESP32 3V3 pin *before* wiring sensors.
2. Confirm common ground with a meter; confirm the ÷2 divider on GPIO34.
3. Flash (with the DHT library installed), open Serial Monitor → `ready (manual)`.
4. `f` → carriage moves smoothly one way (if Rail R goes wrong way, flip `RAIL_R_REVERSED` — §4).
   `x` stop, `v` reverse. `b150`+`m` brush. `p180`+`w` pump. `s` stop all. `g` auto sweep.
