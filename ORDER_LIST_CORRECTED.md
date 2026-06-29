# Corrected Order List — Minimum Bench ("harvests + moves")

Grouped by **where you buy it**, with your real cart prices. ★ = add (was missing). ⇄ = swap (wrong part). ✅ = bought (confirmed on your receipts). ☐ = still to buy. Updated **2026-06-17**: checkboxes now reflect your two receipts (FE order 210690 + RAM S148371), plus your cooling + gate-driver decisions and the twin-rail choice.

Rate ~48 EGP/USD.

> **Procurement status (2026-06-17).** You've **spent ≈ 4,149 EGP** on two orders and now hold almost the entire motion + sensor + control set (✅ below). What's left is the hot-side cooling, the big PSU, the 10 kΩ gate-resistors, the العتبة cleaning hardware, the wiring kit, and the twin-rail 2nd side — see **Still to buy** after the totals.

> **Decision: 4 tiles (locked 2026-06-15).** Four TEC tiles dump ~280 W of heat and pull up to ~24 A. The 4 CPU coolers + LRS-350-12 (29 A) + 14 AWG bus + 30 A fuse below are all sized for that. The "1-tile" notes are kept only as a fallback if cooling/power give you trouble on the bench.
>
> **Two things that bite at 4 tiles — read these:**
> 1. **Don't run the TECs at 100 %.** PWM them to ~70 %. Four tiles at full 6 A = 24 A, plus motor+pump+fans ≈ 3 A → ~27 A on a 29 A supply (93 % load, runs hot). At ~70 % drive the bus is ~16–19 A — comfortable headroom **and** better COP/condensation. (Full-blast option: stagger the motor/pump so they never run with all 4 TECs at peak.)
> 2. **Each CPU cooler must be ≥ 70 W TDP.** If the hot side climbs past ~60 °C the cold side can't reach dew point and **water stops** — the whole point fails. Buy real tower coolers, not low-profile stock ones.

---

## 0. From home / hardware shop (cheap — grab these, or you may already have them)

The small bits the build assumes you have. Most cost very little.

| ✓ | Item | ~EGP | Where / link | Size / note |
|---|---|---:|---|---|
| ☐ | Screwdriver set (flat-head + Phillips/cross) | 80 | [Amazon.eg](https://www.amazon.eg/s?k=screwdriver+set) / hardware | PH1+PH2 and a 4–6 mm flat cover everything here |
| ☐ | Allen / hex key set (metric) | 50 | [Amazon.eg](https://www.amazon.eg/s?k=allen+key+set+metric) / hardware | **OpenBuilds wheels use these** — mostly **3 mm** hex (M5), **2–2.5 mm** (M3) |
| ☐ | Small adjustable spanner / 8–10 mm wrench | 40 | hardware | turns the **eccentric nut** on the gantry wheels |
| ☐ | Jumper wires, **male-to-female** (40-pack) | 50 | [FE](https://store.fut-electronics.com/search?q=jumper+wires) / [RAM](https://ram-e-shop.com/?s=jumper+wire) | connect boards with no soldering |
| ☐ | Small breadboard (400-point) | 40 | [FE](https://store.fut-electronics.com/search?q=breadboard) / [RAM](https://ram-e-shop.com/?s=breadboard) | optional — makes joining all the grounds easy |
| ☐ | 12 V power adapter, **≥ 2–3 A** | 100 | [Amazon.eg](https://www.amazon.eg/s?k=12v+3a+power+adapter) / reuse a router/CCTV/laptop brick | for the **motion test only** — must say "Output: 12V". (The big ~29 A LRS-350 is only for the 4 tiles later — §3.) |
| ☐ | USB **data** cable for the ESP32 | 30 | local / [Amazon.eg](https://www.amazon.eg/s?k=usb+data+cable) | micro-USB **or** USB-C — check your board. Must carry **data**, not charge-only |
| ☐ | Multimeter (basic) | 150 | [Amazon.eg](https://www.amazon.eg/s?k=multimeter) / [RAM](https://ram-e-shop.com/?s=multimeter) | set the buck to **5.0 V**, check polarity/continuity — **very useful** |
| ☐ | Digital caliper (cheap) | 120 | [Amazon.eg](https://www.amazon.eg/s?k=digital+caliper) | measure the **4 mm shaft vs 5 mm pulley bore**, tube sizes |
| ☐ | Wire stripper / small side-cutter | 60 | hardware / [Amazon.eg](https://www.amazon.eg/s?k=wire+stripper) | for the 14/18 AWG wire |
| ☐ | Permanent marker + steel ruler/tape | 30 | stationery | mark the TEC **cold side**; measure the rail gap |
| ☐ | Zip ties + double-sided foam tape | 30 | hardware | tidy cabling; stick boards down |
| ☐ | Kitchen scale (0.1–1 g) | — | you likely have it | **weigh the harvested water** (your yield number) |
| ☐ | Flat board / table to mount the rail on | — | you have it | keep it flat and rigid |
| ☐ | Computer with internet | — | you have it | to install the free [Arduino IDE](https://www.arduino.cc/en/software) |
| ☐ | (Optional) Soldering iron + solder | 250 | [Amazon.eg](https://www.amazon.eg/s?k=soldering+iron+kit) | only if you move off the breadboard to a permanent build |

---

## 1. Future Electronics — one cart  (≈ 3,640 EGP as you have it; see swaps)

| ✓ | Item | Qty | Unit | Note (incl. size / link) |
|---|---|---:|---:|---|
| ✅ | [TEC1-12706 tile](https://store.fut-electronics.com/products/thermoelectric-cooler) | 4 | 120 | bought. **40 × 40 × 3.6 mm**, 12 V, ~6 A max |
| ✅ | [IRF540N MOSFET](https://ram-e-shop.com/?s=IRF540N) | 6 | 18 | bought (RAM). TO-220; **NOT logic-level** — use the 2N2222 driver below |
| ✅ | [2N2222 NPN transistor](https://ram-e-shop.com/?s=2N2222) | 5 | 3 | bought (RAM). TO-92; gate driver, 1 per MOSFET — **inverts the logic** |
| ☐ | [Resistor 10 kΩ](https://ram-e-shop.com/?s=resistor+10k) (gate pull-up) | ~4 | 1 | ★ **still to buy** — ¼ W; one per tile (you only bought 1 kΩ) |
| ✅ | [Resistor 1 kΩ](https://ram-e-shop.com/?s=resistor+1k) (base) | 5 | 1 | bought (FE). ¼ W; 5 cover 4 base resistors |
| ✅ | [NTC thermistor 10 k](https://ram-e-shop.com/?s=NTC+thermistor) | 5 | 5 | bought (FE) — bonus heatsink temp probes |
| ✅ | [GA25-370 12 V encoder gearmotor](https://store.fut-electronics.com/products/ga25-370-motor-encoder) | 1 | 445 | bought. Body **Ø25 mm**, shaft **~4 mm D**, **2× M3** front holes (~17 mm apart) |
| ✅ | [**L298N** dual H-bridge driver](https://ram-e-shop.com/?s=L298N) | 1 | 110 | bought (RAM). Drives both rail motors; ⇄ not a stepper driver |
| ☐ | [GA25 25 mm motor bracket](https://store.fut-electronics.com/search?q=motor+bracket) *(optional)* | 1 | 30–60 | ★ cleaner mount than the DIY L-bracket (§5). Use **M3×6 mm** screws |
| ✅ | [V-Slot 2040 extrusion, 1 m](https://store.fut-electronics.com/products/v-slot-20mm-x-40mm-linear-rail-1m-black-anodized) | 2 | 480 | bought — **you have 2** → twin-rail (Appendix). **20 × 40 mm**, M5 slot |
| ✅ | [OpenBuilds Mini V-Gantry plate + wheels](https://store.fut-electronics.com/products/openbuilds-mini-v-gantry-plate-complete-set-kit) | 1 | 390 | bought. Wheels: **3 mm hex**; eccentric nut needs a spanner |
| ✅ | [GT2 timing pulley (20 T)](https://store.fut-electronics.com/search?q=GT2+pulley) | 2 | 45 | bought. **5 mm bore** — ⚠ vs ~4 mm motor shaft (sleeve / file a flat) |
| ✅ | [GT2 timing belt](https://store.fut-electronics.com/search?q=GT2+belt) | 1 | 65 | bought. **6 mm wide, 2 mm pitch** |
| ✅ | [Smooth idler pulley kit](https://store.fut-electronics.com/search?q=idler+pulley) | 1 | 90 | bought |
| ✅ | [**T-Nut M5** for 2020/2040 V-Slot](https://store.fut-electronics.com/products/t-nut-for-v-slot-aluminum-bar) | 16 | 5 | bought. **M5** slide-in; pair with **M5 × 8–10 mm** bolts |
| ✅ | [Cast aluminium L corner bracket](https://store.fut-electronics.com/products/cast-corner-bracket) | 4 | 15 | bought — frame / stand corners |
| ✅ | [Limit switch (hinge + roller)](https://store.fut-electronics.com/search?q=limit+switch) | 2 | 40 | bought — wire **C + NO** |
| ✅ | [Brushless DC fan 40×40 5 V](https://store.fut-electronics.com/search?q=40mm+fan) | 4 | 60 | bought — **40 × 40 mm, 5 V**, cold-side airflow. Keep (CPU fans cool only the hot side) |
| ✅ | [Mini diaphragm pump 4 L/min](https://store.fut-electronics.com/products/small-liquid-pump-4-l-min) | 1 | 320 | bought — 12 V, spray |
| ✅ | [PVC tube 6 mm, 1 m](https://store.fut-electronics.com/search?q=pvc+tube) | 5 | 20 | bought — **6 mm** tube |
| ✅ | [Radial bearing 8/22](https://store.fut-electronics.com/products/radial-bearings-8mm-inner-22mm-outer) | 2 | 45 | bought — **8 mm ID / 22 mm OD / 7 mm** (608-class), brush roller |
| ✅ | [DHT22](https://store.fut-electronics.com/products/precision-digital-temperature-humidity-sensor-module-dh22) | 1 | 285 | bought — air T/RH |
| ✅ | [ESP32 DevKit 30-pin](https://store.fut-electronics.com/products/esp-32) | 1 | 260 | bought — the brain |
| ✅ | [Mini DC-DC 12-24V→5V, 3 A](https://store.fut-electronics.com/search?q=dc+dc+step+down) | 1 | 90 | bought — set output to **5.0 V** with a multimeter |
| ☐ | [Header pins / female headers](https://ram-e-shop.com/?s=header+pins) | 1 | 10 | only if the ESP32 came without headers; **2.54 mm** pitch |

*Motor mount: the GA25 (**Ø25 mm** body) does **not** fit the 37 mm or NEMA 23 brackets. Bolt it via its **2 front M3 holes** (~17 mm apart — measure yours) to either a small aluminium **L-bracket** (العتبة, §5) or the optional GA25 25 mm bracket above. **Use short M3 × 6 mm screws** — longer ones bottom out on the gearbox and jam the gears.*

**Gate-driver wiring (per TEC tile) — important, the logic is inverted:**
```
  ESP32 GPIO ──[1 kΩ]── base (2N2222)
  12 V ──[10 kΩ]──┬── collector (2N2222) ── GATE of IRF540N
                  └── (this node is the gate)
  emitter (2N2222) ── GND
  IRF540N: drain → TEC(–),  source → GND,  TEC(+) → 12 V
```
GPIO **HIGH → TEC OFF**, GPIO **LOW → TEC ON** (the NPN inverts). Set the pin LOW (or use `digitalWrite(pin, !state)`) in firmware. The 10 kΩ pulls the gate to a full 12 V so the IRF540N turns hard on.

---

## 2. RAM Electronics  (≈ 565 EGP)

| ✓ | Item | Qty | Unit | Note (incl. size / link) |
|---|---|---:|---:|---|
| ✅ | [DS18B20 waterproof](https://ram-e-shop.com/?s=DS18B20) | 2 | 170 | bought — probe ~**6 mm Ø**, 1 m lead; cold-plate temp |
| ✅ | [**ACS712-30A** DC current module](https://ram-e-shop.com/?s=ACS712) | 1 | 100 | bought — **±30 A DC** (SCT013 is AC; INA219 too small) |
| ✅ | [3D nozzle 0.4 mm](https://ram-e-shop.com/?s=nozzle) | 3 | 25 | bought — **0.4 mm** fine jet; the agri nozzles (§5) wet wider |

---

## 3. Industrial (Talaat Harb / Abdeen)  (≈ 1,647 EGP)

| ✓ | Item | Qty | Unit | Note (incl. size / link) |
|---|---|---:|---:|---|
| ☐ | [Mean Well **LRS-350-12** PSU](https://ram-e-shop.com/?s=LRS-350) | 1 | 1,647 | ★ still to buy. **12 V, 29 A (350 W)**. ⇄ replaces EDR-120-12 (10 A — too small for 4 tiles). **1-tile build: skip, keep your 10 A.** |

---

## 4. Computer shop — TEC hot-side cooling  (the part that makes or breaks it)

| ✓ | Item | Qty | Unit | Note (incl. size / link) |
|---|---|---:|---:|---|
| ☐ | [**CPU tower cooler**](https://www.amazon.eg/s?k=cpu+tower+cooler) (heat pipes + ~90 mm fan, **≥65 W TDP**) | 4 | ~300 | ★ **still to buy — the make-or-break part.** Rejects ~70 W/tile. Mounting face must cover the **40 × 40 mm** tile. (1-tile: **×1**) |
| ☐ | [Thermal paste (high W/m·K)](https://ram-e-shop.com/?s=thermal+paste) | 1 | 120 | ★ a thin film on **every** TEC face — hot side *and* cold side |

*Cold side (the **plate is dropped**): the harvested water now condenses **directly on the TEC cold ceramic** (or a small finned heatsink stuck to it), with the 4× 40 mm fans pushing humid air across it and a lip/channel underneath to catch the drip. One CPU cooler **per tile** goes on the hot side; the cold face is left exposed to the air.*

---

## 5. العتبة (Ataba) market — buy tomorrow (by shop)

**This is the cleaning + water hardware. The brush here is the 23 cm demo brush** — full-width for the ~20×85 cm demo panel (Scope box in `BUILD_GUIDE.md`). For the full-width two-rail brush, see the Appendix below.

*These are local-market items — no fixed product page. The Arabic is what to ask for; an Amazon.eg/Jumia search link is given as an online fallback.*

| ✓ | Item (size) | Shop / ask for · online fallback | ~EGP | Note |
|---|---|---|---:|---|
| ☐ | Microfibre **paint roller 23 cm (9″) + 1 spare sleeve** | دهانات «اسطوانة دهان ميكروفايبر ٢٣ سم + بديل» · [Amazon.eg](https://www.amazon.eg/s?k=microfiber+paint+roller+23cm) | 60 | **THE BRUSH.** Microfibre, *not* foam. Sleeve **inner Ø ~8 mm** slides on the rod, through your 2 bearings. |
| ☐ | **Rod / axle** — straight steel rod **8 mm Ø × ~30 cm** | عدة / حدايد · [Amazon.eg](https://www.amazon.eg/s?k=8mm+steel+rod) | 20 | **8 mm** to fit the bearings (8 ID); the roller spins on this |
| ☐ | **Spray bar**: ½″ PVC pipe (~30 cm) + end cap | سباكة · [Amazon.eg](https://www.amazon.eg/s?k=pvc+pipe+half+inch) | 25 | drill a row of **~1 mm** holes, or fit the nozzles below |
| ☐ | **Drip/misting nozzles** (adjustable) | أدوات زراعية «نقّاطات / رشاشات ري» · [Amazon.eg](https://www.amazon.eg/s?k=drip+irrigation+nozzle) | 5 ea ×4 | low-pressure atomise — ⇄ replaces the 3D nozzle |
| ☐ | **Demo panel**: PV module **or** glass sheet **~20 × 85 cm** | سولار/كهرباء، أو زجّاج · [Amazon.eg](https://www.amazon.eg/s?k=small+solar+panel) | 100 | ≤ 23 cm wide so the roller covers full width. Scrap glass is fine (free if you have a pane). |
| ☐ | **Water tank**: 5 L jerrycan / food box + barb fittings | بلاستيك / أدوات منزلية · [Amazon.eg](https://www.amazon.eg/s?k=5L+jerrycan) | 50 | catches the harvested water |
| ☐ | **Aluminium L-bracket** (GA25 motor mount) | عدة / حدايد · [Amazon.eg](https://www.amazon.eg/s?k=aluminum+l+bracket) | 15 | + 2× **M3 × 6 mm** screws (short — long ones jam the gearbox) |
| ☐ | M3 / M5 assorted screws + nuts | مسامير · [Amazon.eg](https://www.amazon.eg/s?k=m3+m5+screw+assortment) | 30 | **M5 × 8–10 mm** for the T-nuts; **M3 × 6 mm** for the motor |

> **Tomorrow's must-buys for the brush:** the **roller + spare sleeve**, a **rod**, and the **demo panel/glass**. Everything else in this table you can grab the same trip.

---

## 6. Wiring / connectors / fuses (FE or RAM — buy with the cart, no extra trip)

| ✓ | Item (size) | Qty | ~EGP | Note / link |
|---|---|---:|---:|---|
| ☐ | Silicone hookup wire **18 AWG**, red + black | 2 m each | 40 | motor, pump, per-tile TEC · [RAM](https://ram-e-shop.com/?s=silicone+wire) |
| ☐ | Wire **14 AWG (2.5 mm²)**, red + black | 1 m each | 40 | 12 V main bus (4 tiles ≈ 24 A). **1-tile: 16 AWG.** · [RAM](https://ram-e-shop.com/?s=14+awg+wire) |
| ☐ | Dupont jumper wires (M-M / M-F / F-F, 40 each) | 1 set | 50 | signals · [FE](https://store.fut-electronics.com/search?q=jumper+wires) |
| ☐ | Breadboard (400-pt) + perfboard | 1 + 1 | 50 | prototype then solder · [FE](https://store.fut-electronics.com/search?q=breadboard) |
| ☐ | Screw terminal blocks (2-pin, **5 mm** pitch) | 8 | 5 ea | 12 V / motor / pump / TEC · [RAM](https://ram-e-shop.com/?s=screw+terminal+block) |
| ☐ | Inline blade-fuse holder + fuses (**30 A** main + **5 A** logic) | 1 set | 35 | **1-tile: 10 A main** · [Amazon.eg](https://www.amazon.eg/s?k=inline+blade+fuse+holder) |
| ☐ | XT60 or 2-pin connector (PSU output) | 1 pair | 15 | [RAM](https://ram-e-shop.com/?s=XT60) |
| ☐ | Heat-shrink tubing assortment | 1 pack | 20 | [Amazon.eg](https://www.amazon.eg/s?k=heat+shrink+tubing) |

---

## Totals (4-tile build)

| Source | EGP |
|---|---:|
| Future Electronics | ≈ 3,820 |
| RAM Electronics | ≈ 440 |
| Industrial (PSU) | 1,647 |
| Computer shop (4 CPU coolers + paste) | ≈ 1,320 |
| العتبة (market) | ≈ 320 |
| Wiring / connectors | ≈ 295 |
| **Total** | **≈ 7,850 EGP (~164 USD)** |

*(cold plate dropped; IRF540N cheaper than the IRFZ44N line; +rod & demo panel in the market section.)*

**1-tile build** (1 TEC + 1 CPU cooler, keep your 10 A PSU, lighter wiring): **≈ 4,200 EGP** — and it still proves harvesting + traverse.

---

## Still to buy (as of 2026-06-17)

You've **spent ≈ 4,149 EGP** (FE 210690 + RAM S148371) and already hold the full motion + sensor + control set (✅ above). What remains:

1. **10 kΩ gate-resistors** (~5 EGP) — you bought only 1 kΩ; need one pull-up per tile.
2. **4 CPU coolers + thermal paste** (~1,320) — the make-or-break hot-side cooling.
3. **Mean Well LRS-350-12 PSU** (~1,647) — to run all 4 tiles at once.
4. **العتبة cleaning hardware** (~320) — roller + sleeve, rod, spray bar, nozzles, demo panel, tank, L-bracket, screws.
5. **Wiring / connectors / fuses** (~295).
6. **Twin-rail 2nd side** (Appendix) — Option A DIY bogie (~190–380) **or** Option B 2nd plate (~390), + a cross-beam (~150–200).

**Remaining ≈ 3,900–4,200 EGP** to finish the full twin-rail bench.

---

## Drop from your original cart
❌ DRV8825 / A4988 (stepper drivers — can't run a DC motor) · ❌ SCT013 (AC) · ❌ 4040/M8 T-nut · ❌ 37 mm & NEMA 23 motor brackets (too big for the Ø25 GA25) · ❌ HS.13 heatsink (way too small for the hot side) · ❌ standalone hot-side fan (CPU coolers include their own) · ❌ aluminium cold plate (condense on the cold face directly).
Keep + driver-assist: **IRF540N** (add the NPN gate driver — it's not logic-level). Keep: the 4× 40 mm fans (cold-side airflow).

## Fastener & dimension cheat-sheet (every measurable spec in one place)

| Thing | Measurement |
|---|---|
| Rail (2040 V-slot) | **20 × 40 mm** cross-section; slot takes **M5** T-nuts |
| T-nut bolts | **M5 × 8–10 mm**, button/low-profile head (**3 mm** hex) |
| Motor-mount screws | **M3 × 6 mm** into the GA25 front holes — **short** (long ones jam the gears) |
| GA25 front hole spacing | ~**17 mm** (measure yours) |
| GA25 motor | body **Ø25 mm**; output shaft **~4 mm** D-shaft |
| GT2 pulley bore | **5 mm** (vs ~4 mm shaft → sleeve / adapter / file a flat) |
| GT2 belt | **6 mm** wide, **2 mm** tooth pitch |
| Brush bearings | **8 mm ID / 22 mm OD / 7 mm** (608-class) |
| Brush rod / axle | **8 mm Ø** (to fit the bearings) |
| TEC tile | **40 × 40 × 3.6 mm** |
| Fans | **40 × 40 mm**, **5 V** |
| Main 12 V bus wire | **14 AWG** (2.5 mm²) for 4 tiles ≈ 24 A; **18 AWG** branches |
| Fuses | **30 A** main, **5 A** logic (1-tile: 10 A main) |
| Hex keys you'll use | **3 mm** (M5 / V-wheels), **2–2.5 mm** (M3) |
| *(Real robot)* Pinion | module-1, **z=30**, ~**Ø30 mm**, **6 mm** bore; rack = module-1 |

---

## Sanity checks
- **Motor driver:** L298N ~2 A/ch > GA25 stall 1.5 A. ✓ (DRV8825/A4988 are for steppers — wrong motor type.)
- **MOSFET gate:** IRF540N needs ~10 V; the 2N2222 + 10 kΩ pull-up swings the gate to 12 V (logic inverts). ✓
- **PSU:** 4 tiles ×6 A = 24 A < 29 A. ✓ (10 A = 1 tile only.)
- **Cooling:** ~70 W/tile needs a CPU cooler, not a 40×40 mm heatsink. ✓ (Cold side condenses on the bare cold face + 40 mm fan airflow.)
- **Logic rail:** Mini DC-DC 12→5 V feeds the ESP32 (never raw 12 V). ✓
- **Current sensor:** ACS712-30A (DC) for the bus; ±30 A covers 24 A. ✓

---

## Appendix — full-width two-rail upgrade (you already own 2× 1 m rails)

**You've chosen the twin-rail layout (2026-06-17)** — so this is now the plan, not just an option. It turns the strip demo into a true full-width cleaner: a brush spanning between **two parallel rails**, traversing the panel length. The cost below is the *delta* on top of the demo, not a fresh build.

**How it re-uses what you have:** your **2 owned rails** become the two **side rails** (one per long edge of the panel). **One motor** drives one side via the existing belt; a rigid **cross-beam** spans the rails, carries the full-width brush, and drags the second (passive) carriage along the other rail — **no second motor** for the demo. Because both rails are now side rails, the cross-beam is a **separate short bar you add** (a stiff aluminium bar, or a short 2020/2040 offcut).

| ✓ | Add | Qty | ~EGP | Note |
|---|---|---:|---:|---|
| ☐ | 2nd carriage side — **Option A (DIY):** 2–4 V-wheels on a small bracket | 1 | 190–380 | cheaper; rides rail 2 (bracket from parts on hand) |
| ☐ | 2nd carriage side — **Option B:** OpenBuilds gantry plate + wheels | 1 | 390 | cleanest; rides rail 2 — **pick A *or* B, not both** |
| ☐ | Cross-beam (stiff Al bar or short 2020/2040 offcut) | 1 | 150–200 | spans the two rails, carries the brush |
| ☐ | Full-width microfibre brush/roller (~60–90 cm) | 1 | 130 | length = panel width = rail spacing |
| ☐ | Longer brush axle rod + 2 extra bearings | 1 | 130 | spans the cross-beam |
| ☐ | Longer ½″ PVC spray bar + 2 more nozzles | 1 | 40 | full-width spray |
| ☐ | Extra GT2 belt (loop ~2.2 m for a 1 m traverse) | 1 | 65 | only if your current belt is too short |
| ☐ | T-nuts + corner brackets (mount 2nd rail + beam square) | — | 110 | squaring the frame |
| | **Delta — rails reused, single-side drive** | | **≈ 815–1,065 EGP** | Option A low end / Option B high end, incl. cross-beam |

**Racking caveat:** single-side drive + a rigid beam can *rack* (one side leads) if the beam flexes or the rails aren't parallel. Fine for a ~60–90 cm span. The **proper production version drives both sides in sync** — add a 2nd GA25 (445) + a 2nd pulley/idler/belt set (~250); the L298N's **spare channel** runs it, so **no new driver**. That's **≈ +700 EGP more → ~1,475 EGP total delta**.

**Reality check on 1 m rails:** they cap the **traverse** at ~85 cm, so you'd clean a panel up to **(rail spacing) wide × ~85 cm long** — a small real module, not a full 1.7 m one. A full-size residential module needs ~1.7 m side rails.
