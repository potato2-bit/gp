# 1 m³ Silica-Gel AWH vs Desert Sand — 6 Egyptian Sites (EGP)

Standalone AWH project. Annual results for a **1 m³ sorbent bed**, driven by the trained
multi-fidelity surrogate over hourly **NASA POWER (2020)** climate at six sites, with
regeneration temperature from **measured daytime irradiance** (ALLSKY_SFC_SW_DWN) through
the flat-plate collector relation. Costs in **EGP** at 49 EGP/USD; electricity 0.98 EGP/kWh
(EgyptERA); CRF = 0.1168 (i = 8 %, n = 15 yr).

## Silica gel (1 m³ = 750 kg)
| Site | Water (L/yr) | Yield (L/kg-gel/yr) | SEC_tot (kWh/kg) | SEC_elec | CAPEX (EGP) | LCOW (EGP/L) |
|---|---|---|---|---|---|---|
| Mansoura | 29,008 | 38.7 | 1.09 | 0.113 | 553,087 | **3.73** |
| NAC | 28,937 | 38.6 | 1.11 | 0.113 | 554,608 | **3.75** |
| New Alamein | 27,841 | 37.1 | 1.11 | 0.118 | 548,200 | **3.87** |
| Siwa | 24,841 | 33.1 | 1.16 | 0.132 | 534,436 | **4.26** |
| Hurghada | 22,274 | 29.7 | 1.19 | 0.147 | 521,547 | **4.67** |
| Benban (Aswan) | 19,113 | 25.5 | 1.28 | 0.171 | 508,610 | **5.35** |

Gel LCOW **3.7–5.4 EGP/L** straddles the condensation-AWH anchor (≈4–8 EGP/L). Electrical
SEC is only **0.11–0.17 kWh/kg** because regeneration is solar; total SEC ≈1.1–1.3 kWh/kg
matches the literature adsorption anchor (1.16). Humid-Delta sites (Mansoura, NAC) win;
arid Upper-Egypt (Benban) is the hardest.

## Desert sand (same 1 m³ = 1600 kg, near-inert sorbent)
| Site | Water (L/yr) | SEC_tot (kWh/kg) | LCOW (EGP/L) | Gel water ÷ sand |
|---|---|---|---|---|
| Mansoura | 1,304 | 66.7 | 196 | 22× |
| NAC | 1,199 | 72.9 | 213 | 24× |
| New Alamein | 1,274 | 68.3 | 200 | 22× |
| Siwa | 841 | 103.8 | 304 | 30× |
| Hurghada | 717 | 121.6 | 356 | 31× |
| Benban | 416 | 210.6 | 614 | 46× |

Sand harvests **~2–5 %** of the gel's water at **≈40–115× the cost**, with SEC two orders
of magnitude worse — you spend the regeneration heat warming 1600 kg of inert sand for
almost no uptake. This quantifies why the **sorbent**, not the cycle, is what makes
adsorption AWH work.

## Method notes / honesty
- Surrogate G3: water (m_w) R²=0.98 and Q_reg R²=0.98 PASS; SEC/removal weaker (full
  384-pt DoE would tighten). Built on 120 CADET low-fi points; OpenFOAM solver validated
  (V1 mass/sign, V2 Ergun) supplies the thermal physics.
- Sand isotherm q*=0.003·RH^1.5 kg/kg is an order-of-magnitude literature value (sand BET
  ≈0.1–1 vs gel 600–700 m²/g); the contrast is robust to the exact number.
- 1 m³ realised as replicated design-point modules, each inside the validated DoE box.
- "Clamped" cycles (≈205–264/yr per site) are nights whose RH/T fall outside the surrogate's
  trained box (arid Egypt, low-RH stress) — reported, not hidden.

## Passive (family nested-cube) vs forced-flow — CADET-validated
The forced-flow numbers above use a fan (u = 0.1–1.0 m/s). The family box-in-box is
**passive** (natural convection, u ~ 0.003–0.05 m/s). A CADET sweep at a representative
family point (T_ads 18 °C, RH 55 %, T_reg 80 °C, 12 h night) gives the real penalty:

| u (m/s) | water/cycle vs forced | bed loaded | fan power |
|---|---|---|---|
| 0.30 (forced) | 100 % | 100 % | 0.53 W |
| 0.05 | 98 % | 100 % | 0.009 W |
| 0.02 | 89 % | 100 % | 0.001 W |
| 0.01 | 63 % | 74 % | ~0 |
| 0.005 | 32 % | 73 % | ~0 |

Over a 12 h night the bed reaches **equilibrium loading**, so above **~0.02 m/s** the
passive penalty is only **2–11 %** (and the fan parasitic vanishes). Below ~0.01 m/s it
becomes air/front-limited and falls off. Natural convection in a vented ~0.5–1 m enclosure
comfortably reaches ≳0.02 m/s, so the family L/day figures hold within ~10 % passively —
a cheap night vent / small chimney keeps u above the threshold. (`results/passive_penalty.png`)

## Artifacts
`results/annual_summary.csv`, `results/annual_summary_sand.csv`,
`results/lcow_gel_EGP.csv`, `results/lcow_sand_EGP.csv`,
`results/silica_vs_sand_EGP.{csv,png}`, per-site `results/annual_<site>.csv`.
3D model: `gazebo/awh_description/` (`awh_world.sdf`, `awh_shot.png`).
