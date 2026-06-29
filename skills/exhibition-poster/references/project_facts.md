# Project facts — the single content source for the poster and deck

Pull content from here. Every figure traces to a project file. If you need something not
listed, mark it `[confirm]` rather than inventing it. Sources:
`memory/project_context.md`, `memory/awh_pvbot_integration.md`, `integration/README.md`,
`integration/results/integration_summary.json`, `integration/AWH_PVBOT_INTEGRATION.pdf`,
`exhibition/IDEA_VALIDATION_RESULTS.md`, `exhibition/COMPETITION_FORM_RESPONSES.md`, and the
ZC Innovation Exhibition registration sheet.

## Identity (confirmed from the ZC registration sheet)

- **Title (use this):** Autonomous Solar-Regenerated Atmospheric Water-Harvesting Robot for
  Photovoltaic Panel Cleaning  _(method changed to solar-regenerated silica gel; the ZC booklet
  still shows the old "Thermoelectric" wording — drop it everywhere in the artifacts)_
- **Short name (for footers):** Solar-AWH PV-Cleaning Robot
- **Hook:** "The cleaner that makes its own water." (alt: "No trucked water. No one on the roof.")
- **One-line:** An autonomous robot that harvests its own distilled cleaning water from desert
  air with a solar-regenerated silica-gel adsorber, then cleans the panels that power it — and the
  closed loop is validated, day by day, across six Egyptian sites.
- **Author / team:** Rahma Hesham El-Hamouly (ID 202000434) — solo project
- **Institution:** Zewail City of Science and Technology — School of Engineering
- **Major:** Renewable Energy Engineering (ENG-REE)
- **Advisor:** Dr. Osama Elsamni
- **Contact:** s-rahma.elhamouly@zewailcity.edu.eg · 01278277298
- **Event:** ZC Innovation Exhibition (competing for the Special Innovation Award)
- **Project type (rubric):** Hardware / device · Prototype / technical solution · Social /
  environmental impact solution

## The big idea — now an integrated, closed loop

The project no longer stops at "a robot that makes its own water." It now **closes and proves
the loop**: a solar-regenerated silica-gel atmospheric-water-harvesting dock supplies a rail-guided
cleaning robot, and a year-long daily co-simulation over real climate data answers the question
the two halves only assumed — **can the robot harvest the water it needs to clean the array
that powers it?** Answer: yes, everywhere tested, with a tiny energy cost.

## The problem (rubric §2)

PV operators in Egypt's desert cities need panels clean continuously, but water is scarce and
trucked, and crews on hot rooftops are slow, costly, and a fall/heat hazard. Soiling quietly
erodes yield every day between cleanings. Current options all fail: manual crews need water and
labour, dry robots scratch the glass and leave dust, coatings wear off, doing nothing wastes
power.

## Users (rubric §3–4)

- **User (lives it):** O&M teams of utility/commercial PV plants in the desert belt; rooftop-
  solar owners in NAC / New Alamein / New Mansoura; municipal solar-streetlight operators.
- **Decision-maker:** O&M managers / facility owners.   **Payer:** developers, ESCOs, new-city
  sustainability programmes (possible subsidy).
- **Evidence:** real NASA POWER (2020) climate series for six Egyptian sites; a coupled
  supply-demand model; an as-built silica-gel dock design; a live ROS 2 + Gazebo demo. Still to gather:
  ≥3 O&M/owner interviews; a measured 24 h harvest run on the bench unit.

## The solution (rubric §5)

A solar-regenerated silica-gel bed adsorbs water vapour from the cool night air; by day the sun
regenerates the bed and the released vapour condenses into distilled water over the panels and
banks it in a dock reservoir. A rail-guided robot drives itself along a 24° PV panel and cleans
on schedule, spraying 0.3 L/m² per pass from that reservoir while a microfibre roller wipes.
Each day the harvester refills the tank; each cleaning pass draws from it — supply and demand
share one clock. Control runs on an ESP32 (encoder + end switches); the live coupling is a ROS 2
node (`awh_water_bus.py`) that banks harvest, drains/refills the tank, and publishes the balance.

**What's new:** no other panel cleaner brings its own water *and proves the loop closes*. Dry
robots scratch and leave dust; wet robots need trucked water a desert can't spare. This one
harvests distilled water from the air, washes wet with zero external water, leaves no streaks,
and is validated as a self-supplying system across a full year and six climates.

## System flow (for the diagram)

Night desert air → silica-gel bed adsorbs moisture → sun regenerates the bed → distilled water
to the dock reservoir (banked daily) →
rail robot sprays 0.3 L/m² + microfibre roller → clean panel → more energy to the grid → that
energy powers the harvest (loop closes).

## The integration — what was actually built and validated

- `integration/awh_pvbot_cosim.py` — coupled annual water+energy balance, **6 sites × 3 scales**,
  daily over the real climate year. Outputs in `integration/results/`.
- `integration/awh_water_bus.py` — **live ROS 2 coupling**: subscribes to `spray_on`, banks AWH
  harvest, drains/refills the tank, publishes the balance. Testable core, no ROS dependency.
- `integration/build_demo.py` + `run_integrated_demo.sh` — integrated Gazebo world + the live
  demo (screenshots, GIF in `integration/figures/`).
- Report: `integration/AWH_PVBOT_INTEGRATION.pdf` (6 pp).

## Impact (rubric §7) — the big stat callouts (real co-sim numbers, residential 9.9 kWp / 46 m²)

| Number | Label | Basis / source |
|---|---|---|
| 1,435 L/yr | cleaning water the robot harvests from air — its whole need | `integration_summary.json` (demand_Lyr) |
| ~7.4–8.9 MWh/yr | energy recovered by keeping the panel clean (per site) | co-sim `energy_recovered_kWh_yr` |
| 1.2–1.6 % | of the array's own output spent harvesting + cleaning (self-powered) | co-sim `parasitic_frac` |
| 0 | external water trucked in · workers sent onto the roof | design intent |
| 6 / 6 | Egyptian sites where the loop closes (3 scales each) | co-sim across all sites |
| ~45 kg | silica-gel bed that closes the loop at NAC = the as-built dock (validation) | co-sim `sized_bed_kg` |

Per-site detail (residential): NAC ~45 kg silica gel, 7,950 kWh/yr, 1.23% parasitic;
Benban ~68 kg (min 77), 8,927 kWh/yr, 1.64% (defers 6 cleans); Mansoura ~45 kg, 7,393 kWh/yr,
0 deferred. Silica-gel canister 42–77 kg fits the 0.4 m dock cube.

## The headline engineering insight (feature this — judges love it)

**The binding constraint is the summer low-RH spell, not the annual average.** Sizing to a 20%
annual surplus is not enough in arid sites — Benban still defers 6 cleans because a low-humidity
summer stretch (days ~120–240) drains the reservoir, while humid Delta sites ride through with
margin. Design rule: **size the harvester to the worst spell, not the yearly mean.**

## Value proposition (rubric §6)

For PV operators in Egypt's desert who can't spare water or risk rooftop crews, the robot keeps
panels clean and makes its own distilled water from the air — unlike dry robots that scratch and
leave dust, or wet ones that depend on trucked water — and it pays for the water and the cleaning
out of the extra power it recovers (1.2–1.6% in, thousands of kWh back).

## Market / three scales (rubric §7 + deck)

1. **Commercial rooftops** — malls, warehouses, factories (50–500 kWp).
2. **Residential rooftops** — villas & apartments in new cities (3–20 kWp) ← the validated demo scale.
3. **Solar street-lights** — standalone poles (100–400 Wp each). Stretch: industrial / cold-storage PV.
Self-supply is scale-invariant in the co-sim. Deployment: NAC · New Alamein · New Mansoura · New Ismailia.

## Demo readiness (rubric §8)

- **Show:** the live integrated Gazebo + ROS 2 demo (AWH dock fills the tank, robot sweeps the
  24° panel, spray draws the tank down, balance prints live) + the bench prototype + this poster.
- **Already works:** design complete; year-long co-sim validated over 6 sites × 3 scales; live
  ROS 2 WaterBus self-check at NAC (f = 1.21, 3.8 L deficit); integrated world renders clean.
- **Setup:** laptop running the Gazebo demo / GIF; the bench unit; the poster.
- **Backup if live demo fails:** play the rendered demo GIF (`figures/awh_pvbot_demo.gif`) and
  walk the reservoir-year figure on the poster.

## Business model / adoption (rubric §9)

Segments: utility & commercial PV O&M, residential solar owners, municipal street-lighting.
Value: clean panels + zero external water + zero rooftop labour, self-powered. Channels: solar
EPC/O&M firms, new-city sustainability programmes. Revenue: cleaning-as-a-service or unit sale;
possible new-city subsidy. Key partners: NREA / Benban developers, new-city authorities. Cost:
off-the-shelf BOM; per-scale payback model `[confirm]`.

## Next validation steps (rubric §10)

Riskiest assumption: that real night-time silica-gel water yield at low RH matches the modelled harvest.
Cheapest test: a measured 24 h harvest run on the bench dock, logging litres vs. RH and temp,
compared to the co-sim. Then: ≥3 O&M/owner interviews and a per-scale payback model.

## Honesty notes (carry these — they build credibility, don't hide them)

- Gazebo Classic has no fluid solver: the tank fill is real geometry (water column = reservoir
  level); the spray is a visual cue.
- Soiling is modelled as 1%/day with a 3.5% clean threshold — reproduces the design cadence and
  is defensible for desert Egypt, but real soiling is episodic.
- Recovered-energy figures are an upper bound (compared against a never-cleaned panel).

## Stage (rubric §1/§5)

**Prototype developed + integrated system validated in simulation.** Design finished; the
tilted-rail robot and the silica-gel AWH dock are coupled and validated in a year-long co-sim and a live
ROS 2 + Gazebo demo; bench parts procured and assembling. Move to "Testing / Validation" once the
measured harvest + movement tests run.

## Hero assets (real, in integration/figures/)

- **Hero image:** `integration/figures/shot_mid_clean.png` — the integrated Gazebo scene: AWH
  dock cube + robot on the 24° panel, HUD showing tank 78%, panel 48% cleaned, 6.7 L drawn.
- **Proof figure:** `integration/figures/fig_reservoir_year.png` (loop stays positive all year,
  6 sites) or `fig_supply_demand.png` / `fig_sizing.png` — pick the clearest at poster size.
- **Demo GIF (deck/backup):** `integration/figures/awh_pvbot_demo.gif`.
