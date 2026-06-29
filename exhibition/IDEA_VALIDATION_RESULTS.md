# Idea Validation — Completed Frameworks

**Project:** Autonomous Solar-Regenerated Atmospheric Water-Harvesting Robot for PV Panel
Cleaning — solar silica-gel atmospheric water harvesting + autonomous panel cleaning.
**Author:** Rahma Hesham El-Hamouly (ID 202000434) · Renewable Energy Engineering · solo project
**Advisor:** Dr. Osama Elsamni · updated 2026-06-27 (method: solar silica-gel, current co-sim numbers)

> Plain-text mirror of `idea_validation_results.pdf` — paste straight into the Gmail
> draft / a slide / the proposal. The four templates in `here.pdf` (Desirability–
> Feasibility–Viability, Empathy, Problem Statement, Impact Statement), filled in for
> this project.

**The idea in one line.** An autonomous rail-guided robot that cleans photovoltaic panels
*while harvesting its own distilled cleaning water from the surrounding air* using a
solar-regenerated silica-gel adsorption module — engineered for Egypt's new sustainable
cities at three scales: **commercial rooftops, residential rooftops, and solar
street-lighting**.

---

## 1. Desirable / Feasible / Viable (the "sweet spot")

**Desirable — "Do they want this?"**
PV operators in Egypt's desert sites lose generation to dust *continuously* and already
pay for cleaning crews and trucked water. The pull: cut soiling losses **without**
spending scarce water or sending workers onto hot roofs.
*Evidence to gather:* O&M interviews (NREA / Benban developers) and rooftop-solar owners.
*Riskiest assumption:* will owners trust an unattended robot on the array? → one-rooftop
pilot + 3 interviews.

**Feasible — "Can we do this?"**
The cleaning robot is built entirely from off-the-shelf parts (V-slot gantry + OpenBuilds
plate, GA25 geared motor + encoder, ESP32, diaphragm pump, microfibre roller); those parts
are **already procured**. The harvester is a solar-regenerated silica-gel bed — no Peltier
tiles, no compressor, almost no electricity, because the sun does the regeneration; the bed
is being sourced for the bench. Adsorption yield was checked against the Benban climate
(RH 25–55 %, T 25–42 °C), where it keeps working in the dry summer hours that defeat
condensation. Cleaning-water duty sized at **0.3 L/m²/pass** (microfibre dose).
*Riskiest assumption:* night-time silica-gel water yield at low RH → test with a measured
24 h harvest run, logging litres vs. RH and temperature against the co-simulation.

**Viable — "Should we do this?"**
Value = avoided trucked-water cost + avoided labour + recovered generation (soiling losses
returned to the grid). Harvested-water LCOW ≈ **0.6–1.0 EGP/L** (silica gel, solar-regenerated;
electrical SEC only 0.11–0.17 kWh/kg), to be weighed against trucked or bottled water plus the
recovered kWh. The system spends only **1.2–1.6%** of the array's output to run and returns
**7.4–8.9 MWh/yr** at the validated residential scale. Model: cleaning-as-a-service or unit
sale to plant owners / new-city authorities.
*Riskiest assumption:* cost per cleaned m² vs. value recovered at the small (residential /
street-lamp) scales → bottom-up payback per scale (see `integration/payback_model`).

**Sweet spot.** A self-watering autonomous PV cleaner is *desirable* (saves water + labour),
*feasible* (off-the-shelf cleaning robot built; passive solar harvester being sourced), and
*viable* (recovers energy + avoids water cost) — strongest at **commercial-rooftop** scale
first, then residential and street-lamp.

---

## 2. Empathy — understanding the user behind the problem

1. **Who experiences this problem?** O&M teams of utility/commercial PV plants in Egypt's
   desert belt (e.g. Benban, new-city rooftops); residential rooftop-solar owners in the
   New Administrative Capital, New Alamein and New Mansoura; municipal operators of solar
   street-lights.
2. **What do they currently do?** Manual cleaning with brushes and water, roughly every
   2–4 weeks (~18×/yr), using trucked or mains water — or they skip cleaning and accept the
   loss.
3. **What is difficult, costly, slow, risky or frustrating?** Water is scarce and trucked
   (expensive, logistically hard); manual cleaning on hot rooftops is slow, labour-intensive
   and a fall/heat hazard; soiling losses accrue *every day* between cleanings.
4. **What alternatives do they already use?** Manual crews; dry robotic sweepers (no water,
   but risk micro-scratches/residue); anti-soiling coatings; or doing nothing.
5. **What would make them adopt your solution?** Proven water self-sufficiency, no rooftop
   labour, *measurable* yield recovery, reliability in dust and 40 °C heat, and a clear
   payback.
6. **Who benefits, who decides, who pays?** *Benefit:* plant owners, the grid, the
   environment. *Decide:* O&M managers / facility owners. *Pay:* plant developers, ESCOs,
   or new-city / sustainability programmes (possible subsidy).

---

## 3. Problem Statement Definition

`[USERS]` **needs to** `[NEEDS]` **because** `[INSIGHTS]`

| USERS (be very specific) | NEEDS (verb) | Surprising INSIGHTS |
|---|---|---|
| PV operators in Egypt's new desert cities — from 200 MW utility blocks to residential rooftops and solar street-lights. | keep panels clean *continuously* without consuming scarce fresh water or putting workers on rooftops. | the cleaning water can be adsorbed from the same night air over the site, then released by the day's sun — so the cleaner makes its own water, closing the loop. |

**Assembled statement.** *PV operators in Egypt's new desert cities need to clean their
panels continuously — without consuming scarce fresh water or risking rooftop labour —
because soiling silently erodes a large share of annual yield while trucked cleaning water
is costly, yet the night air over the very same site can supply that water for free.*

---

## 4. Impact Statement

**If implemented, our project can help** PV operators in Egypt's arid new cities
**achieve** higher energy yield with near-zero external water use for cleaning, **by**
deploying an autonomous robot that harvests its own distilled water from the air
(solar-regenerated silica-gel adsorption) and cleans panels on schedule, **leading to**
recovered soiling losses, thousands of cubic metres of trucked water avoided per year, and
zero rooftop labour.

| Impact indicator | Target for this project | Basis |
|---|---|---|
| Energy saved / recovered | **7.4–8.9 MWh/yr** recovered at the validated 9.9 kWp residential scale; panels kept near-clean year-round | `integration_summary.json` |
| Water saved (external) | robot self-supplies its **whole 1,435 L/yr** cleaning need from air (residential); ≈ **31,000 m³/yr** trucked water avoided at a 200 MW block (illustrative scale-up, 0.3 L/m²) | co-sim `demand_Lyr`; scale-up calc |
| Cost reduced | Avoided water-trucking + cleaning labour; harvested-water LCOW ≈ **0.6–1.0 EGP/L** (solar silica gel); runs on 1.2–1.6 % of array output | `awh_sim` economics; co-sim `parasitic_frac` |
| Safety improved | Workers removed from hot rooftops — 0 rooftop man-hours | design intent |
| Waste reduced | No detergents; distilled water leaves no residue/streaking | distilled condensate |
| Environmental / health | Less freshwater stress + more clean solar kWh → less fossil backup | sustainability framing |
| Number of users served | Scalable across thousands of rooftops + street-lights in NAC / New Alamein / New Mansoura / New Ismailia | 3-scale deployment plan |
| Process efficiency | Continuous autonomous cleaning (3.5-day cadence) vs. periodic manual crews | autonomy |

---

### Riskiest assumption to validate next
That night-time silica-gel water yield, at the site's low-RH hours, actually meets the
cleaning-water duty. Cheapest test: a measured 24 h harvest run on the bench dock, logging
litres harvested vs. RH and temperature, compared against the co-simulation.

### Before you present — numbers to confirm / insert your cited figure
1. The soiling energy-loss % for your site (replace "a large share" with your cited %/day
   or %/yr).
2. Demand evidence from ≥3 O&M / owner interviews (guide in `exhibition/INTERVIEW_GUIDE.md`).
3. The per-scale cost & payback model (commercial vs. residential vs. street-lamp) —
   `integration/payback_model`.

Quantitative values are pulled from this project's own files; treat ranges marked "~" as
estimates to refine.
