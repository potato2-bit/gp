# Minimum Prototype Buy-List — "Harvests Water and Moves"

**Goal:** the cheapest *working* prototype that does the two things the thesis must show on real hardware:
1. **TEC harvesting** — four Peltier tiles on the carriage condense measurable water from the air, logged.
2. **Autonomous traverse** — the carriage drives itself along a short guide rail under motor power, end to end, the way the rail-guided cleaner sweeps a panel.

Spraying/brushing a coupon while it moves is a cheap add-on (below), but the bare minimum is **harvest + move**.

**What this is NOT:** the full 2.4 m rail set with imported rack-and-pinion, the 38-tile residential dock, the off-grid solar/battery chain, or the Raspberry Pi / ROS 2 stack. The carriage runs **tethered to the bench PSU** (no battery) and is driven by an **ESP32** alone. The 24° tilt and the full rack-and-pinion drive are validated in the **Gazebo simulation**; the bench proves the physics moves.

**Rate:** ~48 EGP/USD. Flags: LIVE = HTTP 200 on 2026-06-13; IND = indicative, confirm at counter. Links carried from the verified `MARKET_PARTS_BUYLIST.md`.

---

## ✅ Procurement status — updated 2026-06-17 (supersedes the cart-check below)

Two orders are in: **RAM Electronics S148371** (531.75 EGP) and **Future Electronics order 210690** (3,617.50 EGP). Total spent so far **≈ 4,149 EGP**. Here is where that leaves the bench. The build steps for what you can assemble now are in `BENCH_BUILD_GUIDE.md`.

### Bought — in hand ✅
| Part | Qty | Block | Note |
|---|---:|---|---|
| TEC1-12706 Peltier tile | 4 | A | matches spec |
| ESP32 DevKit 30-pin | 1 | E | |
| GA25-370 encoder gearmotor (250 rpm, 9 kg·cm) | 1 | B | 250 rpm variant — PWM the speed down to the ~0.08 m/s sweep |
| 2040 V-slot rail, 1 m | 2 | B | now have **2** — used as **two parallel running rails** (twin-rail gantry, chosen 2026-06-17). Needs a 2nd gantry plate + a cross-beam to span them (see Still-needed) |
| OpenBuilds mini V-gantry plate + wheels | 1 | B | the carriage |
| GT2 belt + 2× 20T pulleys (5 mm bore) + idler kit | 1 set | B | ⚠ check pulley bore vs motor shaft before fitting |
| Limit switches (straight-hinge + roller-lever) | 2 | B | both fine as end-stops |
| M5 T-nuts for 2040 | 16 | B | |
| Cast-Al L corner brackets | 4 | struct | rail-to-base mounting |
| Radial bearings 8 ID / 22 OD | 2 | C | brush roller ends |
| Mini diaphragm pump 4 L/min | 1 | C | |
| PVC tube 6 mm, 1 m | 5 | C | water line / spray feed |
| DHT22 (AM2302) | 1 | D | inlet air T/RH → dew point |
| DS18B20 waterproof probe | 2 | D | cold-plate temp |
| ACS712-30A DC current module | 1 | D | correct DC sensor (not INA219/SCT013) |
| Mini DC-DC step-down 12–24→5 V, 3 A | 1 | E | = the 5 V logic buck |
| 40×40 mm 5 V brushless fan | 4 | A | ⚠ small — see substitutions |
| IRF540N N-MOSFET | 6 | A/E | ⚠ not logic-level — see substitutions |
| 2N2222 transistor | 5 | A/E | use as gate driver for the IRF540N |
| NTC 10k thermistor | 5 | D | extra heatsink-temp probes |
| 1 kΩ resistor | 5 | D/E | dividers / gate resistors |
| 3D-printer nozzle 0.4 mm | 3 | C | fine jet (not flat-fan) |

### Substitutions — different part than specced ⚠
| Specced | You bought | Verdict |
|---|---|---|
| DRV8871 driver | **L298N red board** | Fine on the bench. Dual H-bridge, ~2 A/ch ≥ the GA25 1.5 A stall. Costs ~2 V drop and a little torque — acceptable for a horizontal/low-tilt test. |
| LM2596 buck | **Mini DC-DC 12–24→5 V 3 A** | Equivalent. This is your 5 V logic rail for the ESP32. |
| IRLZ44N (logic-level) | **IRF540N** | ⚠ Not logic-level: 3.3 V on the gate barely turns it on and it cooks half-on. Two ways out — (a) for the first harvest test hardwire the tiles ON to 12 V, no switching; or (b) drive each IRF540N gate to 12 V through a 2N2222 (you have 5). Circuit in the build guide. |
| 4× CPU tower cooler + fan | **4× 40 mm 5 V fan** | ⚠ A 40 mm fan moves ~6 CFM — nowhere near enough to dump ~50 W off a tile's hot side. Use these as **cold-side** air movers (pull humid air across the cold fins) and still buy real hot-side heatsinks. They run on 5 V (off the buck), not 12 V. |
| Flat-fan spray nozzle | **3D-printer nozzle 0.4 mm** | Works as a fine jet; a flat-fan/mist nozzle covers a coupon better. Keep for now. |

### Still needed ❌ (priority order)
1. **Rail-2 side for the twin-rail gantry — pick one:**
   - **Option A (DIY bogie):** 2–4 V-wheels (~95 EGP ea) on a small bracket/plate from parts on hand → **~190–380 EGP**.
   - **Option B (buy plate):** a 2nd OpenBuilds mini V-gantry plate with wheels → **~390 EGP**.
   - **Either way, plus a cross-beam** to join the two sides: short 2020/2040 extrusion (~30–40 cm) or a stiff flat Al bar, mounted with your existing corner brackets + T-nuts → **~200 EGP**.
   - You can build/test on **rail 1 alone** meanwhile. (Both options are written up with a comparison + drawing in `guide.tex`/`guide.pdf`.)
2. **Hot-side heat rejection** — 4× CPU cooler or finned heatsink **with a real fan**, + **thermal paste**, + **Al cold plate**. *No heat rejection = no condensation.* (~1,470 EGP) **Biggest gap.**
3. **12 V high-current PSU** for the 4-tile array — LRS-350-12 (12 V/29 A) or any ≥24 A unit. (~1,250 EGP) *For the motion build alone, any 12 V ≥3 A adapter you already own is enough — the big PSU is only for the tiles.*
4. **Brush roller core + microfibre sleeve** (~240), **spray bar + flat-fan nozzles** (~150), **5 L tank + fittings** (~250).
5. **GA25 round-body motor bracket** (~60) — or fabricate a clamp.
6. **Wiring, connectors, protoboard, fuses, drag-chain** (~350).
7. *(Only if you skip the 2N2222 driver trick)* **IRLZ44N ×4** (~160).

**Remaining spend ≈ 3,800–4,400 EGP** to finish the full twin-rail bench (low end = Option A DIY bogie; high end = Option B bought plate; both include the cross-beam). The rail-1 motion subsystem you can build right now.

---

## ⚠ Cart check (2026-06-14) — fix these before you pay

Your FE cart is mostly right, but **6 parts are wrong** and **5 essentials are missing**.

**Wrong — swap these:**
1. **IRFZ44N → IRLZ44N.** IRFZ44N needs ~10 V on the gate; the ESP32 gives 3.3 V, so it won't switch the 6 A tiles cleanly (it overheats half-on). IRLZ44N is the **logic-level** version — same package/price.
2. **SCT013 (AC current) → ACS712-30A (DC).** SCT013 is a split-core transformer for AC mains; the TEC runs on DC, so it reads nothing useful. You need a DC sensor, and INA219 (±3.2 A) is too small for the ~24 A bus — use **ACS712-30A**.
3. **T-Nut 4040 (M8) → M5 T-nuts for 2040.** Your rail is **2040** (20 mm slot); the 4040/M8 nut won't fit it.
4. **NEMA 23 motor mount → GA25 round bracket.** Your motor is a Ø25 GA25-370; a NEMA 23 (57 mm square) mount doesn't fit it.
5. **EDR-120-12 (10 A) PSU → ≥24 A.** 4 tiles × 6 A = 24 A ≈ 288 W; a 120 W/10 A supply runs **only ~1–2 tiles**. Use a 12 V/24–29 A (e.g. LRS-350-12) or cut to 1 tile on the 10 A.
6. **3D-printer nozzle (0.4 mm)** works as a fine *jet* but won't fan-wet a coupon — fine to keep, but a flat-fan/mist nozzle covers better.

**Missing — the build won't work without these:**
1. **Motor DRIVER** (DRV8871 ~120, or L298 dual ~90/130) — the GA25 can't run off the ESP32 directly.
2. **TEC hot-side cooling:** 4× heat sink/CPU cooler + fans + Al cold plate + thermal paste — **no heat rejection = no condensation.** This is the single biggest gap.
3. **LM2596 buck** (12→5 V logic rail).
4. **Brush roller core + microfibre, spray bar, water tank.**
5. **Wiring, connectors, fuses, protoboard.**

*(One note, not an error: the FE GA25-370 is the 250 rpm variant, not the 1:71/60 rpm I specced. With the GT2 belt it's fine — PWM the speed down to the ~0.08 m/s sweep; the belt gives ample force.)*

The corrected, complete list is below.

---

## What you buy

### A. TEC water-harvesting core (rides on the carriage)
| Part | Spec it meets | Vendor | Link | EGP | Qty | Line |
|---|---|---|---|---:|---:|---:|
| TEC1-12706 Peltier tile | 4-tile array, design basis | FE | https://store.fut-electronics.com/products/thermoelectric-cooler | 120 | 4 | 480 |
| CPU tower cooler (hot-side sink **+ fan included**) | rejects ≤90 W/tile | LOC (computer mall) | — | 300 | 4 | 1,200 |
| Cold plate, Al 6061 | condensing face | LOC (workshop) | — | 150 | 1 | 150 |
| IRLZ44N **logic-level** MOSFET (PWM each tile) | gate from ESP32 3.3 V; 55 V/47 A | FE | https://store.fut-electronics.com/search?q=IRLZ44 | 40 | 4 | 160 |
| Thermal paste | high W/m·K | LOC | — | 120 | 1 | 120 |
| **Subtotal** | | | | | | **2,110** |

### B. Motion system (makes it move)
| Part | Spec it meets | Vendor | Link | EGP | Qty | Line |
|---|---|---|---|---:|---:|---:|
| **GA25-370 12 V 1:71 (60 rpm) encoder gearmotor** | drive motor; 0.78 N·m stall, encoder for closed-loop position | FE | https://store.fut-electronics.com/products/ga25-370-motor-encoder | 445 | 1 | 445 |
| **DRV8871** single-channel motor driver | 3.6 A; covers GA25 stall (1.5 A) ×2.4, 6.5–45 V | FE | https://store.fut-electronics.com/search?q=DRV8871 | 120 | 1 | 120 |
| 2040 V-slot rail, 1 m | **two parallel running rails** (twin-rail gantry) | FE | https://store.fut-electronics.com/products/v-slot-20mm-x-40mm-linear-rail-1m-black-anodized | 480 | 2 | 960 |
| OpenBuilds mini V-gantry plate + wheels | one plate per rail (cart spans both) — *Option A swaps the 2nd plate for a DIY V-wheel bogie at ~190–380* | FE | https://store.fut-electronics.com/products/openbuilds-mini-v-gantry-plate-complete-set-kit | 390 | 2 | 780 |
| Cross-beam joining the two plates | short 2020/2040 extrusion ~30–40 cm or stiff Al bar | FE / LOC | https://store.fut-electronics.com/search?q=v-slot+extrusion | 200 | 1 | 200 |
| GT2 timing belt (2 m) + 2 pulleys + idler | **positive** belt drive — holds on a slope, no rack import needed (drives rail 1 only) | FE / LOC | https://store.fut-electronics.com/search?q=GT2+belt | 200 | 1 | 200 |
| Limit switch (end of travel) ×2 | tells the ESP32 where the rail ends; reverses the sweep | FE | https://store.fut-electronics.com/search?q=limit+switch | 40 | 2 | 80 |
| **GA25 round-body motor bracket** (25 mm clamp) | mounts the GA25-370 — **NOT a NEMA 23 mount** (the GA25 is a Ø25 round gearmotor, a NEMA 23 mount won't fit) | FE / LOC | https://store.fut-electronics.com/search?q=GA25+bracket | 60 | 1 | 60 |
| **M5 T-nuts + M5 bolts** for 2020/2040 V-slot | fasten the bracket/idler/rail | FE | https://store.fut-electronics.com/search?q=t-nut+v-slot | 5 | 12 | 60 |
| **Subtotal** (Option B / 2nd plate; Option A DIY bogie ≈ −200 to −10) | | | | | | **2,905** |

### C. Cleaning head (sprays/wipes while it moves)
| Part | Spec it meets | Vendor | Link | EGP | Qty | Line |
|---|---|---|---|---:|---:|---:|
| Mini 12 V diaphragm pump | 4 L/min, low-pressure spray | FE | https://store.fut-electronics.com/products/small-liquid-pump-4-l-min | 320 | 1 | 320 |
| Short spray bar + 3 flat-fan nozzles | wets the coupon as it passes | LOC (agri) | https://ram-e-shop.com/?s=spray+nozzle | 150 | 1 | 150 |
| Tank (5 L) + tubing + fittings | feeds from the harvested water | LOC | — | 250 | 1 | 250 |
| Short brush roller (~0.25 m, microfibre) + 2 bearings | dry-wipes the coupon | LOC + FE | https://store.fut-electronics.com/products/radial-bearings-8mm-inner-22mm-outer | 240 | 1 | 240 |
| **Subtotal** | | | | | | **960** |

### D. Sensors (so the result is measured)
| Part | Measures | Vendor | Link | EGP | Qty | Line |
|---|---|---|---|---:|---:|---:|
| DHT22 (AM2302) | inlet air T / RH → dew point | FE | https://store.fut-electronics.com/products/precision-digital-temperature-humidity-sensor-module-dh22 | 285 | 1 | 285 |
| DS18B20 waterproof probe | cold-plate temp / frost guard | FE | https://store.fut-electronics.com/search?q=DS18B20 | 170 | 2 | 340 |
| **ACS712-30A** DC current module | TEC bus current (→ COP, SEC). **DC, ±30 A** — the bus is up to 24 A, so INA219 (±3.2 A) and SCT013 (AC only) are BOTH wrong here | FE / RAM | https://ram-e-shop.com/?s=ACS712 | 90 | 1 | 90 |
| **Subtotal** | | | | | | **715** |

*Water yield is weighed on a kitchen scale — no sensor needed. The motor encoder gives carriage position.*

### E. Control + power (one ESP32, mains-tethered)
| Part | Role | Vendor | Link | EGP | Qty | Line |
|---|---|---|---|---:|---:|---:|
| ESP32 DevKit (30-pin) | drives the motor (PWM + encoder), reads sensors, holds TEC set-point, runs the sweep, logs | FE | https://store.fut-electronics.com/products/esp-32 | 260 | 1 | 260 |
| Mean Well LRS-350-12 PSU (12 V, 29 A) | powers tiles + fans + motor + pump from the wall | RAM | https://ram-e-shop.com/?s=LRS-350-12 | 1,250 | 1 | 1,250 |
| LM2596 buck (12→5 V) | logic rail | RAM | https://ram-e-shop.com/?s=LM2596 | 80 | 1 | 80 |
| IRLZ44N MOSFET (pump on/off) | switches the pump from the ESP32 | FE | https://store.fut-electronics.com/search?q=IRLZ44 | 40 | 1 | 40 |
| Wiring, connectors, protoboard, drag-chain | assembly + the trailing power tether | LOC / FE | — | 350 | 1 | 350 |
| **Subtotal** | | | | | | **1,980** |

---

## Total

| Block | EGP |
|---|---:|
| A. TEC harvesting core | 2,110 |
| B. Motion system (twin-rail, Option B 2nd plate) | 2,905 |
| C. Cleaning head | 960 |
| D. Sensors | 715 |
| E. Control + power | 1,980 |
| **MINIMUM TOTAL (harvests + moves)** | **≈ 8,670 EGP (~181 USD)** |

*Twin-rail with Option A (DIY rail-2 bogie instead of a 2nd plate) trims block B by ~200, to ≈ 8,470 EGP total.*

**Optional add-ons:**
- *Powered brush* (spins the roller as it sweeps): GA25-370 motor (445) + upgrade the DRV8871 to a dual **Cytron MDD3A** (+130) → **+575 EGP**.
- *Tilt/motion sensing* on an inclined track: MPU-6050 IMU → **+180 EGP**.

Under half of the ~20,965 EGP full bench, and it already demonstrates the two headline behaviours end to end.

---

## What's still cut, and why it's safe

| Cut | Why the thesis is still covered |
|---|---|
| Full 2.4 m rails + imported rack-and-pinion | The 1 m rail + GT2 belt proves single-axis traverse; the deployment rack-and-pinion on the 24° rail is in `MARKET_PARTS_BUYLIST.md` and validated in Gazebo |
| Second *driven* rail (motor on rail 2) | You're building the twin-rail gantry (cart spans both rails), but only **rail 1 is driven** by the belt; rail 2 just guides. A second motor + belt on rail 2 is a deployment detail |
| Raspberry Pi 4 + ROS 2 stack | The ESP32 runs the sweep and logging on its own; ROS 2 is exercised in simulation |
| 12 V 10 Ah carriage battery | The bench runs tethered off the PSU — no need to carry a 1.3 kg pack |
| 38-tile dock + 48 V bus + solar/MPPT/battery | Deployment scale only; quoted in the thesis, not built. The bench stays at 12 V (4 tiles ≈ 24 A on the 29 A PSU) |
| Full-width 0.96 m brush | A short 0.25 m brush proves dust removal on a coupon |

---

## Buy it all in one Cairo run (Thursday)
- **Future Electronics (FE):** 4× TEC1-12706, 5× IRLZ44N, **GA25-370 motor**, **DRV8871 driver**, **2040 V-slot rail**, **V-gantry kit**, GT2 belt + pulleys, 2× limit switch, ESP32, mini pump, DHT22, 608ZZ bearings.
- **RAM Electronics:** DS18B20 ×2, INA219, LM2596, Mean Well LRS-350-12.
- **Computer mall / workshop / agri shop (LOC):** 4× CPU coolers, cold plate, brush roller + microfibre, spray bar + nozzles, tank/tubing, brackets, wiring + drag-chain.

Everything is in stock in Cairo — no imports. The one deployment part that *would* be imported (the steel rack-and-pinion) is deliberately swapped for a local GT2 belt on the bench. Verify the RAM/LOC counter prices (IND); FE prices were live on 2026-06-13.
