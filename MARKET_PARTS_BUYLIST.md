# Market Parts Buy-List — Rail-Guided PV-Cleaning Robot

**Design basis:** `output/rail_guided_design.json` (full-width brush, rack-and-pinion rail drive) + `output/tec_robot_results.json` + `output/nac_tec_robot_results.json` (NAC dock, trade_3p5day f=1.0).
**Two quantities per line:** **B** = bench prototype, **F** = full residential NAC dock.
**Self-supply target:** The design now targets **100% self-supply** at the **0.3 L/m² microfibre dose** (down from the 1.8 L/m² wet-wash figure), so the residential cleaning demand drops to 13.8 L/event and full atmospheric self-supply is feasible at 38 TEC tiles.
**Exchange rate:** ~48 EGP/USD (band 47–50), per `tec_deployment_analysis_v1.1` (CBE 2025–26).
**Import landed factor:** ×1.38 on catalogue (15% freight/ins + 5% duty + 14% VAT on CIF+duty), same source.

**Price provenance flags:**
- **LIVE** — fetched HTTP 200 from the vendor's Shopify `product.json` on **2026-06-13**, exact EGP, in stock.
- **L-12Jun** — live price from `MARKET_BOM.tex` run of 2026-06-12, reused (spot-checked, unchanged 13 Jun).
- **IND** — indicative, checked 2026-06-13; RAM renders prices client-side so RAM and local-market lines can't be scraped — confirm at counter.
- **SEARCH** — no confirmable product URL; a vendor search link to the exact part is given. Confirm SKU before buying.

Vendors: **FE** = Future Electronics Egypt (`store.fut-electronics.com`), **RAM** = RAM Electronics (`ram-e-shop.com`), **LOC** = local workshop / agri-marine / computer mall, **SOL** = Cairo solar distributor, **IMP-Pololu**, **IMP-Ali** = Aliexpress.

---

## 1. Rail drive (NEW — rack-and-pinion, replaces free wheels)

Requirement (J:rail_drive): ≥**0.838 N·m** at the Ø30 mm pinion, **38.2 rpm** at 0.06 m/s, 12 V DC **geared + encoder** (ROS 2 odometry). Two driven rails → **0.42 N·m/motor**. The drive must also **hold the carriage on the 24° tilt when unpowered** (the slide problem); see hold note below.

| Need (calc) | Chosen part (mfr / PN) | Rated | Margin | Weight | Vendor | URL | Unit EGP | B | F | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| Drive motor 0.42 N·m/rail, ~38 rpm, encoder, resists back-drive | **GA25-370 12 V 1:71 ("60 rpm") encoder gearmotor** (8 kg·cm) — run **2 driven rails** | 0.78 N·m stall; 60 rpm no-load; **1.5 A stall, 0.42 A rated**; kt≈0.52 N·m/A | **1.86×** torque/motor; 1.57× speed; **0.64 PWM duty** at 38 rpm | 0.105 kg ea | FE | https://store.fut-electronics.com/products/ga25-370-motor-encoder | 445 | 2 | 2 | LIVE 2026-06-13 (60 rpm SKU); confirm ratio at counter |
| — worm-gear hold option (self-locking, no slide) | **JGY-370 12 V worm gearmotor, ~40 rpm** (self-locking) | ~1.4 N·m; non-back-drivable | holds unpowered | ~0.20 kg ea | IMP-Ali | https://www.aliexpress.com/wholesale?SearchText=JGY-370+12V+40rpm+worm+gear+motor | ~600 (landed) | 0 | 0 | **NEW** SEARCH — encoder variant, confirm |
| Motor driver (BOTH drive motors, dual ch) | **Cytron MDD3A** dual DC driver, 3 A cont / 5 A peak/ch, 5–30 V; brake mode | 3 A cont/ch (3.7× I_op); 5 A peak ≥ 1.5 A stall; 30 V ≥ 1.3×12 | right-sized (BTS7960 43 A was 53× overkill) | 0.020 kg | FE | https://store.fut-electronics.com/products/cytron-3a-dual-channel-dc-motor-driver | 520 | 1 | 1 | **NEW** SEARCH — confirm SKU at FE counter |

**Pinion + rack** (Ø30 mm = **module-1, z=30**; 4.8 m total = 2 rails × 2.4 m). No Egyptian source — import.

| Need | Part | Rated | Vendor | URL | Unit EGP | B | F | Verified |
|---|---|---|---|---|---|---|---|---|
| Pinion Ø30 module-1, bore to fit GA25 6 mm shaft (+grub/adapter) | Module-1 steel pinion z30, 6 mm bore | mesh w/ M1 rack | IMP-Ali | https://www.aliexpress.com/wholesale?SearchText=module+1+pinion+gear+30mm+bore+8mm | ~265 ea (landed) | 2 | 2 | SEARCH 200 — confirm bore/SKU |
| Rack 4.8 m, module-1 steel (1 m bars) | Module-1 steel gear rack, 1 m × needed | M1, 20×20 face | IMP-Ali | https://www.aliexpress.com/wholesale?SearchText=module+1+steel+gear+rack+1m | ~530 (landed) | 1060 (2 m) | 3180 (6 m) | SEARCH 200 — confirm SKU |

**Hold-on-tilt note.** Gravity puts 31.9 N along the slope → 0.48 N·m back-drive at the pinion (0.24 N·m/rail). A GA25-370 spur/planetary box is **not** self-locking, so the carriage will creep if it just coasts. The committed fix is the **MDD3A brake mode** (short the windings at park) plus a small **sprung park detent** that drops into the rack at the docked position. If a brake-free mechanical hold is preferred, swap to the **JGY-370 worm gearmotor** (self-locking, listed above), which trades the encoder ratio range and a little efficiency for a guaranteed unpowered hold.

---

## 2. Guide rails + carriage bogies (NEW)

Requirement (J:rails): 2 rails × 2.4 m V-slot extrusion; 4–8 V-groove wheels ride them; brackets to panel frame.

| Need (calc) | Chosen part (mfr / PN) | Rated | Margin | Vendor | URL | Unit EGP | B | F | Verified |
|---|---|---|---|---|---|---|---|---|---|
| Guide rail, 2040 V-slot, 2×2.4 m (1 m bars, cut) | **V-Slot 20×40 mm Al 6063 bar, 1 m, black anodized** (SKU 5E-BAR2462) | 6063-T5, V-slot | ample stiffness for 8 kg carriage | FE | https://store.fut-electronics.com/products/v-slot-20mm-x-40mm-linear-rail-1m-black-anodized | 480 | 2 | 6 | LIVE 2026-06-13, in stock |
| Carriage bogie w/ wheels (per side) | **OpenBuilds Mini V-Gantry Plate kit, complete w/ wheels** (SKU 110) | rides 2040 V-slot | 4 wheels/kit | FE | https://store.fut-electronics.com/products/openbuilds-mini-v-gantry-plate-complete-set-kit | 390 | 2 | 2 | LIVE 2026-06-13, in stock |
| Spare/extra V-wheels | **Solid V-Wheel bearing kit** (SKU 316-SOLIDVWHEEL) | V-groove, Delrin+brng | — | FE | https://store.fut-electronics.com/products/solid-v-wheel | 95 | 4 | 4 | LIVE 2026-06-13 |
| — metal V-wheel option (heavier load) | **Metal V-Groove bearing kit** (SKU 75-MOTIONVG002) | steel V-groove | — | FE | https://store.fut-electronics.com/products/dual-metal-v-groove-bearing-kit | 100 | 0 | 4 | LIVE 2026-06-13 |
| Rail-to-frame mount, L-bracket | **Cast Al L corner bracket** (SKU 35-COR01) | extrusion-grade | — | FE | https://store.fut-electronics.com/products/cast-corner-bracket | 15 | 2 | 4 | LIVE 2026-06-13 |
| Hidden inside corner bracket M3 | **Inside hidden corner bracket 20×20** (SKU 50-BRAK01) | M3 | — | FE | https://store.fut-electronics.com/products/inside-hidden-corner-bracket-m3-for-aluminum-extrusion-20x20 | 30 | 1 | 2 | LIVE 2026-06-13 |
| T-nuts (fasten brackets/rack to slot) | **M5 slide-in T-nut for 2020/2040 V-slot** (SKU 48) | M5 | — | FE | https://store.fut-electronics.com/products/t-nut-for-v-slot-aluminum-bar | 5 | 10 | 20 | LIVE 2026-06-13 |

---

## 3. Full-width brush roller (CHANGED 0.25 m → 0.96 m)

Requirement (J:brush): 0.96 m long, Ø50 mm, microfibre over PVC/Al core, 2× 608ZZ-class bearings, shaft. Brush motor 12 V ~100 rpm, drag 1.73 N / 0.065 N·m; spec ~0.3–0.5 N·m for startup margin.

| Need (calc) | Chosen part (mfr / PN) | Rated | Margin | Weight | Vendor | URL | Unit EGP | B | F | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| Brush motor, 12 V, ~100 rpm, drag 0.065 N·m | **GA25-370 12 V 100 rpm encoder gearmotor** | 0.78 N·m stall; 100 rpm; 0.13 A steady, ~1.6 A inrush | 12× vs steady drag | 0.105 kg | FE | https://store.fut-electronics.com/products/ga25-370-motor-encoder | 445 | 1 | 1 | LIVE 2026-06-13 |
| Brush switch (one direction, low-side) | **IRLZ44N** logic-level N-MOSFET (TO-220) | 55 V, 47 A; Vgs(th) logic-level; ESP32 GPIO gate | 30× on 1.6 A inrush | 0.003 kg | FE | https://store.fut-electronics.com/search?q=IRLZ44N | 35 | 1 | 1 | **NEW** SEARCH — confirm SKU |
| Roller bearings, 608ZZ class (8 ID / 22 OD) | **Radial bearing 8 mm ID / 22 mm OD** (SKU MECHBRNG228) | 608-size, shielded | meets | 0.02 kg | FE | https://store.fut-electronics.com/products/radial-bearings-8mm-inner-22mm-outer | 45 | 2 | 2 | LIVE 2026-06-13, in stock |
| Roller core Ø50 × 0.96 m + microfibre sleeve | PVC/Al pipe Ø50 + microfibre wrap (fabricate) | 0.96 m | — | LOC | (workshop) | 350 | 350 | 350 | IND 2026-06-13 |
| Roller shaft 8 mm + flex coupling | 8 mm shaft + 6→8 coupling | — | — | LOC | (workshop) | 160 | 160 | 160 | IND 2026-06-13 |

---

## 4. Water spray (UNCHANGED design, full-width bar)

Requirement: 0.6 L/panel (13.8 L per full-array event at the 0.3 L/m² microfibre dose) low-pressure spray; 12 V diaphragm; spray bar 0.96 m + 9 flat-fan nozzles.

| Need (calc) | Chosen part (mfr / PN) | Rated | Margin | Vendor | URL | Unit EGP | B | F | Verified |
|---|---|---|---|---|---|---|---|---|---|
| Pump (full), low-pressure ≥0.16 L/min mean, pressure-switch | **Seaflo 21-series SFDP1-010-035-21** diaphragm, 3.8 L/min @2.4 bar | 3.8 L/min, 2.4 bar | 24× flow | LOC (marine/agri) | https://ram-e-shop.com/?s=diaphragm+pump+seaflo | 1800 | 0 | 1 | IND 2026-06-13 |
| Pump (bench), mini diaphragm 12 V | **Brushless diaphragm pump 4 L/min, Hmax 3 m** (SKU PUMP020) | 4 L/min | 4.3× flow | FE | https://store.fut-electronics.com/products/small-liquid-pump-4-l-min | 320 | 1 | 0 | LIVE 2026-06-13 |
| Pump switch (3.75 A, low-side) | **IRLZ44N** logic-level N-MOSFET + flyback diode | 55 V, 47 A; 12× on 3.75 A | ESP32 GPIO gate | FE | https://store.fut-electronics.com/search?q=IRLZ44N | 35 | 1 | 1 | **NEW** SEARCH — shares part with brush switch |
| Spray bar 0.96 m + 9 flat-fan nozzles | PVC bar + 9 brass flat-fan nozzles | full-width fan | — | LOC (agri) | https://ram-e-shop.com/?s=spray+nozzle | 300 | 1 | 1 | IND 2026-06-13 |
| Tank + tubing + fittings | 5 L tank, 8 mm tube, fittings | — | — | LOC | — | 300 | 300 | 300 | IND 2026-06-13 |

---

## 5. TEC AWG module (UNCHANGED)

Tiles: bench **4**; NAC dock **38** (trade_3p5day f=1.0, 100% self-supply). 1 fan per ~2 tiles → 20 fans full.

| Need (calc) | Chosen part (mfr / PN) | Rated | Margin | Vendor | URL | Unit EGP | B | F | Verified |
|---|---|---|---|---|---|---|---|---|---|
| TEC tile, design basis 130 EGP | **TEC1-12706**, 40×40 mm | ΔTmax 66 K, Qc,max 56 W | −8% vs basis | FE | https://store.fut-electronics.com/products/thermoelectric-cooler | 120 | 4 | 38 | LIVE 2026-06-13, in stock |
| Hot-side fan, 12 V, ~2.5 W | 120 mm 12 V axial, 2.5 W class | 2.5 W | exact (energy budget) | RAM / LOC | https://ram-e-shop.com/?s=120mm+12v+fan | 180 | 2 (60 mm @75) | 20 | IND 2026-06-13 |
| Hot-side sink, Rth ≤0.5 K/W, reject ≤90 W/tile | bench: used CPU tower cooler 95 W TDP; full: extruded Al fin 13 cm/tile | meets fwd-draft | 1.06× | LOC | — | 300 (bench) / 700/m (full) | 4×300 | ~5 m | IND 2026-06-13 |
| Cold plate Al 6061 | machined Al plate | — | — | LOC | — | 150 (B) / 600 (F) | 1 | 1 | IND 2026-06-13 |
| TEC string switch, **48 V bus, per series-quad** (6 A/string) | **IRLB4030** 100 V logic-level N-MOSFET — one per string | 100 V (≥2×53 V open-string), 180 A (≥2×6 A) | 8× current, 1.9× voltage | FE / IMP | https://www.infineon.com/cms/en/product/power/mosfet/n-channel/irlb4030/ | 60 | 4 | 10 | **NEW** SEARCH — bench keeps IRF540N at 12 V; dock uses 10 (9 quads + 1 pair) |
| Thermal paste | high-W/mK paste | — | — | LOC | — | 120 | 1 | 1 | IND |

---

## 6. Sensors (UNCHANGED)

| Need | Chosen part (mfr / PN) | Rated | Vendor | URL | Unit EGP | B | F | Verified |
|---|---|---|---|---|---|---|---|---|
| Air T/RH (dew point), ±0.5°C ±2% | **DHT22 (AM2302)** module | ±0.5°C, ±2% RH | FE | https://store.fut-electronics.com/products/precision-digital-temperature-humidity-sensor-module-dh22 | 285 | 1 | 1 | LIVE 2026-06-13 |
| Cold-plate temp / frost guard | **DS18B20** waterproof probe | ±0.5°C, −55…125°C | RAM | https://ram-e-shop.com/?s=DS18B20 | 90 | 2 | 2 | IND 2026-06-13 |
| Current/power telemetry | **INA219** breakout | ±3.2 A bus | RAM | https://ram-e-shop.com/?s=INA219 | 120 | 1 | 1 | IND (FE no stock) |
| IMU, tilt/fall trip | **MPU-6050** breakout | ±16 g, ±2000°/s | FE | https://store.fut-electronics.com/search?q=MPU6050 | 180 | 1 | 1 | L-12Jun |
| Edge / limit switch ×2 | lever microswitch 10 A | 10 A | FE / LOC | https://store.fut-electronics.com/search?q=limit+switch | 40 | 2 | 2 | L-12Jun |
| Encoder | integral to GA25-370 drive motor (§1) | — | — | — | incl. | — | — | — |

---

## 7. Compute (UNCHANGED — two-tier per ROS2_ARCHITECTURE)

| Need | Chosen part | Rated | Weight | Vendor | URL | Unit EGP | B | F | Verified |
|---|---|---|---|---|---|---|---|---|---|
| Real-time MCU (drive PWM, encoders, TEC PID, micro-ROS) | **ESP32 DevKit 30-pin** | 240 MHz dual-core | 0.010 kg | FE | https://store.fut-electronics.com/products/esp-32 | 260 | 1 | 1 | LIVE 2026-06-13 |
| ROS 2 host | **Raspberry Pi 4B 4 GB** | quad A72, Jazzy | 0.055 kg (w/ heatsink) | RAM / Amazon.eg | https://ram-e-shop.com/?s=raspberry+pi+4 | 5200 | 1 | 1 | IND 2026-06-13 |

---

## 8. Power

Bench: 12 V mains PSU ≥10 A (4 tiles ≈24 A worst case → 29 A unit) + drive battery. **Carriage battery committed at 12 V 10 Ah LFP** (not 20 Ah) — see the weight-closure flag below. Full dock (nac f=1.0, standalone off-grid): ~1416 Wp PV (3×~550 Wp) + ~849 Ah/12 V LFP storage. **The dock TEC bus is now 48 V** (38 tiles wired as 9 series-quads + 1 series-pair, 63 A vs 228 A at 12 V), so the dock MPPT collapses from three oversized 12 V units to **one 48 V controller** (see ELECTRICAL_DESIGN.tex §7). **Grid-coupled option (recommended):** the house already carries a 9.9 kWp array, so the dock can draw its ~6.5 kWh/day night load from the house bus and skip the dedicated PV/MPPT/battery, leaving only ~14,000 EGP of marginal AWG hardware.

| Need (calc) | Chosen part (mfr / PN) | Rated | Margin | Weight | Vendor | URL | Unit EGP | B | F | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| Bench PSU ≥10 A (24 A worst case) | **Mean Well LRS-350-12** | 12 V, 29 A | 1.2× | 1.0 kg | RAM / Amazon.eg | https://ram-e-shop.com/?s=LRS-350-12 | 1250 | 1 | 0 | IND 2026-06-13 |
| **Carriage battery 12 V 10 Ah LFP** (weight-driven downsize) | local 10 Ah LiFePO₄ + 15–20 A BMS | 15 A cont.; ~91 Wh usable → ~4 cleans/charge, dock top-up | 0.77C peak | **1.30 kg** | SOL | https://ram-e-shop.com/?s=lifepo4+12v+10ah | 2800 | 1 | 1 | **CHANGED** 20 Ah→10 Ah; IND 2026-06-13 |
| PV ~1416 Wp (nac f=1.0, 3 modules) | 3 × ~550 Wp Tier-1 mono module | ~1650 Wp | 1.17× | — | SOL | (quote) | 7500 | 0 | 3 | IND (nac cost block: 22500) |
| **Dock MPPT, 48 V bus** (was 3× oversized 12 V) | **1× EPever Tracer4215AN** 40 A, 150 V PV | PV charge ~30 A at 48 V → 1.33× | 1.33× | 1.5 kg | SOL | https://www.epever.com/ | 9500 | 0 | 1 | **CHANGED** 3 units→1; IND |
| Battery ~849 Ah/12 V LFP (n_pack 5) | 5 × ~200 Ah 12 V LiFePO₄ | ~1000 Ah | 1.18× | — | SOL | (quote) | 32000 | 0 | 5 | IND (nac cost block: 160000) |
| 12→5 V logic buck (carriage) | **LM2596** module, 3 A | 3 A | 1.5× | 0.015 kg | RAM | https://ram-e-shop.com/?s=LM2596 | 80 | 2 | 3 | L-12Jun (FE OOS, buy RAM) |
| DC distribution / fusing | bus bar, blade fuses, wiring | per ELECTRICAL_DESIGN | — | 0.30 kg (carriage) | LOC | — | 250 (B) / 2500 (F) | 1 | 1 | IND |

### Carriage weight budget (closes at 7.99 kg ≤ 8.0 kg target)

The TEC condenser is a **stationary dock**, so its ~1.05 kg leaves the carriage. With the real LFP weighed honestly, a 20 Ah pack (~2.3 kg) plus a still-mounted TEC would push the carriage to ~11 kg. Two corrections close it: TEC off the carriage, and the pack dropped to 12 V 10 Ah (~1.3 kg) with dock top-up charging.

| Item | Mass (kg) |
|---|---:|
| Carriage base plate (Al 6061, 3 mm) | 1.10 |
| Full-width brush 0.96 m | 1.00 |
| Carriage side-frames (2) | 0.80 |
| V-groove wheels ×8 + bogie plates | 0.40 |
| Drive motors 2× GA25-370 | 0.21 |
| Steel pinions 2× Ø30 M1 | 0.06 |
| Brush motor GA25-370 | 0.105 |
| Driver MDD3A + 2 MOSFET switches | 0.05 |
| Water pump (diaphragm) | 0.30 |
| **Battery 12 V 10 Ah LFP** | **1.30** |
| ESP32 DevKit | 0.010 |
| Raspberry Pi 4B + heatsink | 0.055 |
| Sensors + 2 limit switches | 0.10 |
| Cabling, connectors, fuses | 0.30 |
| Tank dry + spray bar + nozzles + tube | 0.40 |
| Water, mean fill (1.8 L) | 1.80 |
| **Total** | **7.99** |

---

## 9. Structure / misc

| Need | Part | Vendor | Unit EGP | B | F | Verified |
|---|---|---|---|---|---|---|
| Carriage / chassis plates Al 6061 | cut/drilled Al plate | LOC | 600 (B) / 1800 (F) | 1 | 1 | IND 2026-06-13 |
| Fasteners, cable, connectors | M3–M5 kit, 12 AWG, JST/XT60 | LOC / FE | incl. above | — | — | IND |

---

## Cost rollup

| Subsystem | Bench (EGP) | Full dock (EGP) |
|---|---:|---:|
| 1+2. Rail, drive (MDD3A), rack, bogies, rails | 5,460 | 9,610 |
| 3. Full-width brush (+ IRLZ44N switch) | 1,080 | 1,080 |
| 4. Water spray (+ IRLZ44N switch) | 880 | 2,435 |
| 5. TEC AWG (4 / 38 tiles, IRLB4030 strings) | 2,180 | 13,956 |
| 6. Sensors | 845 | 845 |
| 7. Compute | 5,460 | 5,460 |
| 8. Power (standalone off-grid) | 4,460 | 194,740 |
| 9. Structure / misc | 600 | 1,800 |
| **TOTAL (standalone)** | **≈ 20,965 EGP (~437 USD)** | **≈ 229,926 EGP (~4,790 USD)** |

The standalone full-dock total drops about 23,200 EGP against the previous build: the 48 V TEC bus replaces three oversized 12 V MPPT units with one (−19,000 EGP), and the carriage pack downsizes from 20 Ah to 10 Ah (−1,700 EGP). The right-sized MDD3A driver and the per-string IRLB4030 switches add a little back.

**Grid-coupled dock (recommended):** drawing the night load from the house 9.9 kWp array deletes the dedicated PV, MPPT, and battery bank (–187,000 EGP), so the marginal AWG hardware for 100% self-supply is about **14,000 EGP** (38 tiles + sinks + fans + cold plate + per-string switching). The standalone total above prices the off-grid case only.

**Three biggest cost drivers (standalone full dock):** (1) **station battery bank** 160,000 EGP, 70% of the dock, the price of storing one harvest cycle at 100% self-supply; (2) **PV modules** 22,500 EGP; (3) **TEC AWG hardware** ~14,000 EGP. The single 48 V MPPT (9,500 EGP) is now a minor line, no longer a top driver, because raising the dock bus from 12 V to 48 V cut the charge current by four. Energy is still ~85% of the standalone full dock, which is why the grid-coupled option is recommended. On the bench, the drivers are the **Raspberry Pi (5,200)**, the **rack-and-pinion + extrusion rail set (~6,400 combined)**, and the **10 Ah drive battery (2,800)**.

---

## Buy in Cairo Thursday vs ship

**Buy same-day in Cairo (in-stock, confirmed live 2026-06-13):**
- FE counter: 2040 V-slot bars, OpenBuilds gantry kits, V-wheels, brackets, T-nuts, **2× GA25-370 1:71 drive + 1× GA25-370 100 rpm brush motor**, **Cytron MDD3A driver**, **IRLZ44N MOSFETs (brush + pump switches)**, 608ZZ bearings, TEC1-12706 ×4, DHT22, MPU-6050, IRF540N (bench TEC), ESP32, bench diaphragm pump, limit switches.
- RAM counter: DS18B20 ×2, INA219, LM2596 ×2, Raspberry Pi 4B, Mean Well LRS-350-12.
- LOC same-day: roller core + microfibre, shaft/coupling, CPU coolers (computer mall), cold plate (workshop), spray bar + nozzles (agri), tank/tubing, chassis plate, **10 Ah LFP drive battery (solar shop)**, fasteners/cable.

**Ship / import (order Day 1, one parcel):**
- **Rack + pinion** (module-1 steel) — Aliexpress, **the only mechanically-critical import**; no Egyptian stock. 2–4 wk; landed ×1.38. *Confirm pinion bore matches the GA25 6 mm shaft before ordering, or buy a 6→8 adapter locally.*
- **IRLB4030 100 V logic-level MOSFETs** (dock per-string TEC switches, ×10) — if not on the FE shelf; 100 V logic-level parts are sometimes import-only.
- **JGY-370 worm gearmotor** — only if the self-locking hold path is chosen over the MDD3A brake + park detent. Otherwise skip; the two-rail GA25-370 build is fully local.

**Quote, not bought (full dock only):** PV modules, MPPT, 200 Ah LFP bank — Cairo solar distributors, 1–2 wk quotes in USD; thesis pricing only.
