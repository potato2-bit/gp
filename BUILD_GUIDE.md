# Build Guide — TEC Water-Harvesting PV Cleaner (4-tile bench unit)

How to assemble and wire the prototype from the parts in `ORDER_LIST_CORRECTED.md`.
Read it once end-to-end before you pick up a screwdriver. Build in the order below — mechanics first, then power, then signals, then bring-up in stages. Don't connect everything and flip the switch.

**Rate ~48 EGP/USD · 4 tiles · ~280 W heat · up to ~24 A on the 12 V bus.**

> ### Scope — this is a deliberately *scaled* demo
> It runs on **one rail** with a **23 cm full-width roller** and cleans a **~20 × 85 cm demo panel** at **100 % coverage** — the roller is as wide as the panel, so a single traverse cleans all of it. That's the real cleaning function, proven at bench scale.
>
> The **production design** is the same machine scaled up: **two rails** (one per long edge) carrying a **full-width ~1 m brush** across a real ~1 × 1.7 m residential module. Two rails because a 1 m brush supported at both ends stays flat to the glass; cantilevered off one rail it sags and chatters. You build the scaled unit here and present the full-size two-rail design in the thesis as what it represents.
>
> **Keep it honest:** size the demo panel *to the roller* (below). Don't claim a 23 cm roller cleans a 1 m-wide module — scaling the panel down to match the brush is exactly what makes a strip-wiper into a genuine full-coverage cleaner.

---

## 0. What you're building (the mental model)

Two subsystems that share one tank, one 12 V supply, and one ESP32:

1. **The harvester (stationary).** 4 TEC tiles pull water out of the air and drip it into a tank. The TECs draw heavy current and need steady cooling, so this part does **not** move — it sits on the frame.
2. **The cleaner (moving).** A gantry rides a single rail, sprays a little of the harvested water, and wipes the glass with a microfibre roller.

```
        ┌─────────── frame / stand ───────────┐
        │  [TEC module ×4]  ← harvests water    │
        │        │ drip                          │
        │        ▼                               │
        │     [TANK] ──pump──► spray bar ─┐      │
        │                                  ▼      │
   rail ═══════════[ GANTRY: roller + spray ]════════  ← cleans the panel
        │                                         │
        │   [electronics box: PSU, ESP32, drivers]│
        └──────────────────────────────────────┘
```

Keep the harvester, the rail, and the electronics box as three separate areas on the bench so heavy TEC wiring stays away from the moving parts.

---

## 1. Safety first (read this, it's short)

- **The LRS-350-12 has exposed mains terminals.** Wire it with the plug **unplugged**, fit an earthed (3-pin) mains lead to L / N / ⏚, and put the PSU in a box or behind a guard before you ever power it. Never probe the L/N side live.
- **24 A is enough to melt thin wire and start a fire.** Use the 14 AWG bus wire for the 12 V main line and keep the **30 A fuse** right at the PSU + output. No fuse, no power-on.
- **TEC hot sides reach 60–80 °C.** Mount coolers before powering tiles; don't touch a running hot side.
- Power things up **one stage at a time** (Section 7). Most "it's broken" moments are a wiring slip you'll catch in stages but never find with everything connected at once.

---

## 2. Tools & consumables you supply

Soldering iron + solder · wire stripper/cutters · small screwdrivers + hex keys (for M3/M5) · multimeter (essential) · hot-glue or epoxy · zip ties · a drill (for the spray bar + bracket holes) · a flat board/base (~60 × 40 cm) to mount everything to.

---

## 3. Mechanical assembly

### 3a. The rail + gantry (the cleaner's track)
1. Lay the **V-Slot 2040 rail (1 m)** flat and fix it to your base board. Use the **cast L corner brackets + M5 T-nuts** at each end as feet, or clamp it down. It must not flex.
2. Slide the **OpenBuilds gantry plate** onto the rail and adjust its eccentric wheel nuts until it rolls smoothly with **no side play** (snug, not tight).
3. Mount one **GT2 pulley** on the **GA25 motor shaft**; mount the **idler pulley kit** at the far end of the rail. They must line up so the belt runs straight.
4. Run the **GT2 belt**: from the motor pulley → along the rail → around the idler → back. Clamp **both belt ends to the gantry plate** (the plate has belt-loop notches). Tension it so it doesn't skip but isn't guitar-string tight.
5. Bolt the **GA25 motor** to its end of the rail with the **aluminium L-bracket** (العتبة) through the motor's 2 front **M3** holes — the 37 mm / NEMA brackets won't fit, so use the L-bracket.
6. Mount the **2 limit switches** at the two travel ends so the gantry's edge trips each one just before it runs out of rail.

### 3b. The roller (the brush)
1. Slide the **microfibre paint-roller sleeve (23 cm)** onto a straight rod/axle.
2. Press a **radial bearing (8 mm ID)** onto each rod end; bolt the two bearings to the **underside of the gantry plate** so the roller axis is **horizontal and across the direction of travel**.
3. Set the height so the microfibre **just kisses the glass** — light contact, enough to wipe, not enough to drag the gantry to a stall. It spins freely (passive); there's no motor on it.

### 3c. The spray bar
1. Cap one end of the **½″ PVC pipe** (~25 cm). Either drill a row of ~1 mm holes along it **or** fit the **agri drip/misting nozzles** at intervals.
2. Mount it on the gantry's **leading edge, ahead of the roller**, aimed at the glass, so it wets the strip just before the roller reaches it.
3. Run **6 mm PVC tube** from the **pump outlet** to the spray bar.

### 3d. The harvester module (×4 tiles) — stationary
For **each** of the 4 tiles, build this sandwich:
```
   [ CPU cooler ]  ← HOT side, fan blowing  (rejects ~70 W)
        ││  ← thermal paste
   [ TEC1-12706 ]  (red wire = +, mark it)
        ││  ← thermal paste
   [ small heatsink or bare ceramic ]  ← COLD side, condenses water
        ↑ 5 V fan blows humid room air across it
```
1. Thermal-paste **both** TEC faces. Clamp the TEC firmly between the CPU cooler (hot) and the cold-side surface — even pressure, no gaps.
2. Point a **40 mm 5 V fan** at each cold face to push humid air over it.
3. Tilt each cold face slightly so condensation runs to a low edge; put a small lip/channel there and a tube to the **tank**.
4. Mount all 4 on the frame, hot sides facing **out/up** so the coolers exhaust into open air — not at each other.

### 3e. The tank
- 5 L jerrycan under the harvester drips. The **pump** draws from it and feeds the spray bar. Keep the pump at/near the tank, not on the moving gantry.

### 3f. The demo panel (size it to the roller — this is what makes it honest)
- Use a small PV module or a sheet of glass **~20–23 cm wide** (≤ the 23 cm roller, so the roller covers the full width with a little to spare) **× up to ~85 cm long** (the rail's usable travel between the limit switches).
- Mount it at the same **~24° tilt** as the design, with the rail running along its **long** edge so the gantry traverses the 85 cm length.
- Because the roller spans the full panel width, **one pass down the length = the whole panel cleaned.** That's the demo's whole point: at this size it isn't wiping a strip, it's cleaning 100 % of a representative panel.
- In the thesis, state the demo scale explicitly and show the full-size two-rail / full-width-brush design (Scope box above) as the production version it stands in for.

---

## 4. Electrical — power tree

Build this skeleton first and verify voltages (Section 7) before adding any load.

```
AC mains ─(earthed lead)─► LRS-350-12 ─► +12V / GND  ─[30 A fuse on +12V]─► 12 V BUS
                                                                            │
  12 V BUS ──► Mini DC-DC buck (IN) ──► OUT set to 5.0 V ──► 5 V RAIL
```
- Set the buck to **exactly 5.0 V with a multimeter before** connecting the ESP32 — do this with nothing else attached.
- From the 12 V bus, fan out to: the 4 TEC drivers, the 4 CPU-cooler fans (12 V), the L298N, and the pump driver.
- From the 5 V rail: ESP32 VIN, and the 4 cold-side fans (5 V).

**The one rule that saves hours: every ground is the same ground.** PSU −, buck −/−, ESP32 GND, L298N GND, all MOSFET sources, all sensor grounds → one common node. A split ground makes the whole thing behave randomly.

---

## 5. Electrical — per subsystem

### 5a. TEC tiles ×4 (low-side switch + NPN gate driver)
Per tile (the IRF540N is **not** logic-level, so the 2N2222 driver is required):
```
 12 V ── TEC(+)            TEC(–) ── IRF540N drain
                                     IRF540N source ── GND
                                     IRF540N gate ──┬── 10 kΩ ── 12 V
                                                    └── 2N2222 collector
 ESP32 GPIO ──1 kΩ── 2N2222 base ;   2N2222 emitter ── GND
```
- **Logic is inverted:** GPIO **HIGH → TEC OFF**, GPIO **LOW → TEC ON**.
- Put the **ACS712-30A in series on the 12 V line that feeds all 4 TECs**; its analog OUT → ESP32 pin 36.
- Build one driver, test it (Section 7), then replicate ×4. You have a 5th IRF540N + driver set as the pump switch / spare.

### 5b. Motor (GA25) → L298N
| L298N pin | to |
|---|---|
| +12V | 12 V bus |
| GND | common GND |
| +5V logic | leave the onboard regulator jumper **on** (it makes its own 5 V from 12 V) |
| OUT1 / OUT2 | GA25 motor + / − |
| IN1 / IN2 | ESP32 GPIO 33 / 32 (direction) |
| ENA | ESP32 GPIO 4 (PWM = speed) |

GA25 **encoder**: A → GPIO 18, B → GPIO 19, encoder VCC → 3.3 V, encoder GND → GND. (The 2 thick wires are motor power → L298N; the thin ones are the encoder.)

### 5c. Pump
Switch it like a TEC: pump(+) → 12 V, pump(−) → the **5th IRF540N** drain, gate driven by its 2N2222 from **GPIO 25**.

### 5d. Sensors
- **DHT22** (air T/RH): VCC → 3.3 V, GND → GND, DATA → **GPIO 23** + a 10 kΩ pull-up to 3.3 V.
- **DS18B20 ×2** (temps): both share **GPIO 5** (1-wire bus) + one 4.7 kΩ pull-up to 3.3 V. One on a hot-side cooler, one on a cold face.
- **Limit switches ×2**: one leg → GND, other → **GPIO 16 / 17**, set `INPUT_PULLUP` in code (no resistor needed).

### 5e. Fans
- 4× **CPU-cooler fans** (12 V): the two power pins → 12 V bus / GND (ignore PWM/tach).
- 4× **cold-side fans** (5 V): + → 5 V rail, − → GND.

### 5f. ESP32 pin map (full)
| Function | GPIO | Note |
|---|---|---|
| TEC 1–4 gates | 13, 14, 27, 26 | output, **inverted** |
| Pump gate | 25 | output, inverted |
| L298N IN1 / IN2 / ENA | 33, 32, 4 | ENA = PWM |
| Encoder A / B | 18, 19 | interrupt inputs |
| DHT22 | 23 | + 10 kΩ pull-up |
| DS18B20 (shared) | 5 | + 4.7 kΩ pull-up |
| Limit sw 1 / 2 | 16, 17 | `INPUT_PULLUP` |
| ACS712 (analog) | 36 | ADC1, input-only |

---

## 6. Firmware — what it has to do (logic outline)

You can flash this incrementally. Order of features:
1. **Blink** — prove the board + 5 V rail.
2. **Harvest loop:** read DHT22; if room RH is high enough, drive the 4 TEC gates **LOW** (ON) at ~**70 % PWM** (don't run 100 % — see Section 8). Watch the hot-side DS18B20: if it climbs past ~**60 °C**, back the PWM off. Watch the ACS712: if total TEC current spikes, cut the tiles.
3. **Motor jog:** PWM ENA, set IN1/IN2 for direction, count encoder ticks; stop on either limit switch.
4. **Clean cycle:** pump ON → wet → traverse rail end-to-end (roller wipes) → reverse → pump OFF. Trigger it on a timer or a button.
5. Tie it together: harvest continuously; run a clean cycle on schedule, pausing the heaviest TEC load during motor+pump moves so you stay under the PSU limit.

---

## 7. Bring-up — power up in THIS order (don't skip)

| Step | Do | Pass = |
|---|---|---|
| 1 | PSU alone, fused, **no loads**. Measure output. | **12.0 V** |
| 2 | Add buck, nothing downstream. Measure + adjust. | **5.0 V** |
| 3 | ESP32 on the 5 V rail. Flash Blink. | LED blinks |
| 4 | **One** TEC + its driver. Command the pin. Measure tile current with the ACS712 / meter. | tile switches ON/OFF cleanly, gate swings ~12 V |
| 5 | Replicate to 4 tiles. Run at 70 %. Watch hot-side temp + total current. | hot side stabilizes, current < 24 A |
| 6 | Motor + L298N. Jog both directions. | moves both ways, stops on limits |
| 7 | DHT22 + DS18B20 + limit switches. | sane readings on serial |
| 8 | Pump. | sprays, no leaks |
| 9 | Full clean cycle, then leave harvester running. | water collects in the tank |

If a step fails, **stop there** — the fault is in what you just added.

---

## 8. The two numbers that decide if it works

1. **Run the TECs at ~70 % PWM, not 100 %.** 4 tiles at full 6 A = 24 A; add motor + pump + fans (~3 A) and you're at ~27 A on a 29 A supply — too hot to hold. At ~70 % the bus is ~16–19 A (comfortable) **and** the COP is better, so you actually get *more* water. If you ever do run full-blast, stagger the motor/pump so they never run with all 4 tiles at peak.
2. **Each CPU cooler must be ≥ 70 W TDP.** If a hot side passes ~60 °C, the cold side can't reach dew point and **water stops** — that's the failure mode that kills the demo. Real tower coolers, not low-profile stock ones.

---

## 9. Troubleshooting

| Symptom | Likely cause |
|---|---|
| Whole thing acts random / resets | split ground — tie all grounds to one node |
| TEC won't switch | inverted logic (LOW = ON), or gate not reaching 12 V (check the 10 kΩ to +12 V) |
| No water forms | hot side too hot (cooler too small / no paste / dry-clamped), or room air too dry — check DHT22 RH |
| Gantry stalls or skips | roller pressed too hard on glass, or belt too loose, or wheels too tight |
| PSU clicks / sags | over 24 A — drop TEC PWM, or staggering motor/pump |
| Motor runs one way only | an IN pin not connected, or ENA not getting PWM |
| ESP32 won't boot | feeding it 12 V instead of 5 V (check the buck), or a strapping pin held by a sensor |

---

*Parts and prices: `ORDER_LIST_CORRECTED.md`. This guide assumes the 4-tile build locked 2026-06-15.*
