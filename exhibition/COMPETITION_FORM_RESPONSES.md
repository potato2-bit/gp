# Competition / Exhibition Form — Responses

**Project:** Autonomous Solar-Regenerated Atmospheric Water-Harvesting Robot for Photovoltaic Panel Cleaning (solar silica-gel water harvesting + autonomous panel cleaning)
**Author:** Rahma Hesham El-Hamouly (ID 202000434) · Renewable Energy Engineering · solo project
**Advisor:** Dr. Osama Elsamni · Zewail City of Science and Technology
**Grounded in:** `skills/exhibition-poster/references/project_facts.md`, `integration/results/integration_summary.json`, `integration/AWH_PVBOT_INTEGRATION.pdf`, `IDEA_VALIDATION_RESULTS.md`.
**Voice:** humanized to match Rahma's own writing.

> Method note: harvesting is **solar-regenerated silica-gel adsorption**, not the earlier
> thermoelectric (Peltier) condensation. The change is deliberate and evidence-based — see the
> method note in *Innovation Developed* below.

---

## Research Problem or Industry Gap

PV operators in Egypt's new desert cities have to keep their panels clean all the time, but they can't spare fresh water to wash them and they can't keep sending workers up onto hot rooftops. Water is scarce and trucked in, so washing thousands of rooftops with it is expensive and wasteful; sending crews up to do it is slow and a real fall-and-heat hazard. Meanwhile dust quietly eats into the power every single day between cleanings. The cleaners that exist today force a bad choice: clean dry and scratch the glass while leaving dust behind, or clean wet and pay to truck in water a desert site doesn't have.

---

## Proposed Solution / Innovation

We built a robot that cleans the panels and makes its own cleaning water out of the air, so no water has to be trucked in and nobody has to climb onto the roof. A bed of silica gel sits in a small dock beside the array. Through the cool desert night it quietly soaks up water vapour from the air; during the day the sun heats the bed and drives that water back off, and it condenses into clean distilled water that banks in a tank. The robot then drives itself along the panels on a guide rail and cleans them on a set schedule, spraying that distilled water from a spray bar while a microfibre roller wipes. The harvesting needs almost no electricity, because the sun does the regeneration — so the whole system runs on a sliver of the power the clean panels give back.

The cleaning robot runs on an ESP32 board with a motor encoder and end switches, and the system is built from cheap off-the-shelf parts. The full tilted-rail version already runs in a Gazebo simulation, and a year-long, day-by-day co-simulation over six Egyptian sites proves the robot harvests all the water it needs to clean the array that powers it. The silica-gel bench prototype is being built now.

---

## Potential Impact

You no longer have to choose between clean panels and saved water, because the robot makes its own. On the residential system we validated (a 9.9 kWp rooftop, 46 m² of panel), the robot harvests its **whole 1,435 L/yr cleaning need straight from the air**, and keeping the panels clean returns **about 7.4–8.9 MWh a year** to the grid — energy that dust would otherwise steal. All of that costs only **1.2–1.6% of the array's own output** to run, so the system pays for its water and its cleaning out of the extra power it recovers. The loop closes at **all six Egyptian sites** we tested, across three scales. Scaled up, the same idea avoids roughly **31,000 m³ of trucked cleaning water a year at a 200 MW plant**. No one works on a hot roof, and because the water is distilled there are no chemicals and no streaks. It is cheap, it scales from utility plants down to home rooftops and street-lights, and it can spread across Egypt's new cities.

---

## Innovation Developed

No other panel cleaner brings its own water. The robots that exist either clean dry, which scratches the glass and leaves dust, or they clean wet but need water trucked in, which a desert site can't spare. Ours pulls its own distilled water out of the night air with a solar-regenerated silica-gel bed, so it washes the panels wet without a single drop from outside, and distilled water leaves no streaks. It is one machine that harvests, drives, and cleans, designed to work at three sizes: commercial rooftops, home rooftops, and solar street-lights. And it doesn't just claim the loop closes — a full-year, day-by-day co-simulation over six climates proves the harvest keeps up with the cleaning everywhere we tested.

**Why silica gel and not a Peltier cooler (the method change).** We first sized a thermoelectric (Peltier) condenser, the obvious way to wring water from air. But our own feasibility study showed condensation collapses below about 35% relative humidity — exactly the dry summer hours that bind an arid Egyptian site like Benban. Solar-regenerated adsorption keeps working in that dry, hot air, and the sun does the regeneration for almost free. So we changed the harvester on the evidence: the method that wins in Egypt's climate, not the one that's easiest to draw.

---

## Project Stage

**Selected: Prototype Developed.**

The design is finished, the tilted-rail system is validated in a Gazebo simulation and a live ROS 2 demo, and the integrated supply-and-demand loop is proven in a year-long co-simulation over six sites and three scales. The silica-gel bench prototype is being assembled. Once the measured 24-hour harvest run and the movement test are done before the exhibition, move this up to **Testing / Validation Phase**.
