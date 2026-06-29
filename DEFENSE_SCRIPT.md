# Defense Package — Autonomous Thermoelectric Water-Harvesting Robot for PV Cleaning
**Presenter: Rahma Hesham · 20 min talk + 10 min Q&A**

Pacing target: ~18 min of talking leaves buffer. If you fall behind, compress slides 7, 12, and 14 (multi-scale, Vision 2030, next steps) — they are the most cuttable.

---

## PART 1 — FULL SCRIPT (what to say, slide by slide)

### Slide 1 — Title (~30s)
"Good morning. My name is Rahma Hesham, and this is my senior design project: an autonomous thermoelectric water-harvesting robot for cleaning photovoltaic panels, designed for Egypt's new sustainable cities. It was supervised by Dr. Osama Elsamni. The core idea is simple to state: a robot that makes its own water from the air to clean solar panels, with no external water and no grid connection."

### Slide 2 — The Problem (~1:30)
"Egypt is building solar everywhere, but in our climate dust is the enemy. Panels lose between half a percent and two percent of their output every single day to soiling, and without cleaning that builds to 15 to 40 percent in a month. The usual fix is to wash them with water. The problem is that the desert sites and the new cities where we are putting most of this PV are exactly the places where water is scarce or expensive to truck in. So we are stuck: don't clean and lose a third of your energy, or clean and spend water you don't have. That contradiction is what this project set out to break."

### Slide 3 — Concept (~1:30)
"My answer is a rail-guided robot that harvests its own cleaning water from the air. At night it runs thermoelectric coolers that pull the surface below the dew point, so moisture condenses and is collected. During the day it traverses the panel rows on a rail and wipes them clean with that harvested water. It closes its own water loop, so it needs no external supply. The three ideas to remember are: harvest at night, clean by day, and stay completely self-sufficient."

### Slide 4 — How the harvesting works (~2:00)
"This is the heart of the project. A thermoelectric cooler is a solid-state heat pump — pass current through it and one side gets cold. We drive that cold side below the local dew point, and water condenses out of the night air, the same way dew forms on a cold bottle. We modelled this hour by hour against real NASA climate data. At our design site, the New Administrative Capital, each tile produces about 38.7 litres a year at a coefficient of performance of 1.9. This chart shows how that performance changes with the temperature lift — the smaller the lift, the better the efficiency, which is why we keep the hot side cool and run during the cool, humid night window of six to eight hours."

### Slide 5 — Robot design (~2:00)
"The robot itself is a rail-guided gantry that rides up and down the tilted panel. The key decision here is that it is rail-guided and not a free-driving rover. On 24-degree glass a free rover simply slides — we confirmed that in simulation. So instead it runs on two rails with a rack-and-pinion drive, powered by two GA25-370 gearmotors with encoder feedback. The whole carriage comes in at eight kilograms. It cleans with a damp microfibre brush, and I want to stress the word damp — the dose is only 0.3 litres per square metre, and that single choice is what makes the water budget work, which I'll prove in a moment."

### Slide 6 — Control (~1:30)
"Control runs on a two-tier ROS 2 stack. A Raspberry Pi 4 does the thinking — path planning, the cleaning sequence, and the mission state machine. An ESP32 handles the fast, hard-real-time job — motor control, the encoders, end-stop detection, and the safety cut-outs. Splitting it this way keeps the timing-critical loop separate from the high-level logic. [If time: show backup slide 17.] I validated the motion in a Gazebo simulation: the carriage climbs the 24-degree rail, runs a full down-and-up sweep, and returns, confirming the drive both climbs and holds."

### Slide 7 — Multi-scale (~1:00)
"The same architecture scales. I designed it at three sizes: a small street-lamp unit, the building rooftop, and a large industrial ground-mount block. The harvester and the control are shared across all three. But the one I carried all the way to a built prototype is the residential rooftop, so that's what the rest of the talk focuses on."

### Slide 8 — Reference design, NAC (~1:30)
"The reference is a 9.9 kilowatt-peak residential rooftop in the New Administrative Capital — 46 square metres of panel. The rail system spans the array, and the robot cleans it using only self-harvested water. The headline numbers: it needs 38 condensation tiles, it draws about 14 percent of the array's own energy, and the full installed system is costed at around 218,000 Egyptian pounds."

### Slide 9 — Site selection (~1:00)
"I evaluated two climates that bracket the performance. Benban, in Upper Egypt, is the worst case — very dry, 16 to 25 percent humidity, almost no dew. The New Administrative Capital is the realistic deployment site — semi-arid, 52 percent average humidity, with a real six-to-eight-hour dew window. The point of using both is honesty: Benban is the floor that proves the concept survives the driest Egyptian air, and NAC is where it actually runs."

### Slide 10 — Climate data (~1:00)
"This is the real measured climate at the site, month by month — temperature, dew point, and humidity from the NASA POWER record. You can see the summer months are the hard case: highest temperature, lowest humidity. That's the condition the design is sized against, so everything else in the year is easier."

### Slide 11 — Water self-sufficiency (the key result) (~2:00)
"This is the result I most want you to take away. 38 tiles produce about 1,470 litres a year. The rooftop's cleaning demand is 1,439 litres a year. So supply beats demand by about 2 percent — the system is water self-sufficient, with margin. This chart shows it holds every month at NAC; the red bars are Benban, the worst case, for comparison. And the reason it closes at all is the damp dose: at 0.3 litres per square metre the daily demand is 3.9 litres against 4.0 litres of supply. A full wet wash would need 13 litres a day — that would take 124 tiles instead of 38, and it simply wouldn't fit. The damp wipe is the whole reason this is feasible. On energy, the robot recovers the soiling losses and pays back the prototype cost in about three years."

### Slide 12 — Vision 2030 (~1:00)
"This lines up directly with Egypt's Vision 2030: it adds renewable yield by killing soiling losses, it conserves water by using zero freshwater, and it's built for exactly the new cities the country is developing — the New Administrative Capital, New Alamein, and the others."

### Slide 13 — Conclusions (~1:30)
"To conclude. I showed that thermoelectric water harvesting is feasible in Egyptian conditions, even at the driest site. I showed the residential rooftop reaches full water self-sufficiency at NAC with a positive margin. The robot is built as a working prototype at eight kilograms, with its motion validated in simulation, and it's costed to the Egyptian market at about 8,950 pounds for the bench build. In one line: a machine that draws its rinse from the night air and gives the panels back their light."

### Slide 14 — Next steps (~1:00)
"The next step is a full field season — putting the prototype on a real NAC rooftop and measuring it across a year against the numbers I've modelled. Beyond that, an adaptive harvesting algorithm that tunes the TEC current to the live humidity, and fleet coordination for the industrial scale."

### Slide 15 — Thank you / Q&A (~30s)
"Thank you. I'm happy to take your questions." [Have backup slides 16 cost, 17 validation, 18 climate calcs ready to jump to.]

---

## PART 2 — SUMMARIZED TALKING POINTS (glance cards)

- **S1 Title** — Robot that makes its own water to clean PV. No external water, no grid. Supervised by Dr. Elsamni.
- **S2 Problem** — Dust: 0.5–2%/day, 15–40%/month. Cleaning needs water; desert/new cities have none. Break the contradiction.
- **S3 Concept** — Harvest at night, clean by day, fully self-sufficient. Rail-guided.
- **S4 AWH** — TEC = solid-state heat pump → cold side below dew point → water. 38.7 L/tile/yr, COP 1.9 at NAC. Small lift = better efficiency.
- **S5 Robot** — Rail-guided (rover slides on 24° glass). Rack-and-pinion, 2× GA25-370, 8 kg. **Damp** microfibre, 0.3 L/m².
- **S6 Control** — Two-tier ROS 2: Pi 4 (planning) + ESP32 (real-time motors/safety). [Show S17: Gazebo climbs & sweeps.]
- **S7 Multi-scale** — 3 sizes; shared harvester/control; residential rooftop is the built one.
- **S8 NAC** — 9.9 kWp, 46 m², 38 tiles, ~14% of array energy, ~218,000 EGP full system.
- **S9 Sites** — Benban = worst-case floor (16–25% RH). NAC = real site (52.6% RH, 6–8 h dew). Honest bracketing.
- **S10 Climate** — Real NASA data; summer is the hard case (hot + dry) → design point.
- **S11 RESULT** — 1,470 supply vs 1,439 demand = **+2%, self-sufficient**. Damp 3.9 vs 4.0 L/day feasible; wet wash 13 L/day → 124 tiles, no. ~3 yr payback.
- **S12 Vision 2030** — +renewable yield, zero freshwater, built for new cities.
- **S13 Conclusions** — Feasible even at worst site; self-sufficient at NAC; 8 kg prototype built & sim-validated; 8,950 EGP bench.
- **S14 Next** — Full-year field trial; adaptive RH control; fleet.
- **S15** — Thank you. (Backups: 16 cost, 17 validation, 18 calcs.)

**Numbers to never get wrong:** 38 tiles · 38.7 L/tile/yr · COP 1.9 · 0.3 L/m² · +2% margin · 14% energy · 8 kg · 24° · 8,950 EGP bench.

---

## PART 3 — EXPECTED QUESTIONS & ANSWERS

**Q1. Why clean every 3.5 days? Your own literature says 7–21 days.**
"Those 7-to-21-day figures are for less dusty sites. At NAC's soiling rate of up to 2 percent a day, a 14-day interval would let losses build to nearly 30 percent. Cleaning roughly twice a week caps the average loss at about 3 to 4 percent, which is the economic sweet spot. The harvester is sized to that interval, and the water budget still closes."

**Q2. The water budget only closes by 2%. What about a bad month or a bad year?**
"Three buffers. First, the controller scales TEC run-time on live humidity, so it harvests harder when conditions allow. Second, there's a storage tank that carries water across days. Third, the margin is a design lever — adding a few tiles widens it cheaply. And even at Benban, the absolute worst case, the system still produces water, just less. So 2 percent is the conservative annual-mean margin, not a knife-edge."

**Q3. TEC has worse efficiency and higher cost-of-water than vapour compression. Why use it?**
"Because the constraint here isn't energy cost — the energy is free PV surplus. It's reliability, water access, and scale. TEC has no compressor and no moving refrigeration parts, so it's silent and low-maintenance on a rooftop. And it scales down to a single tile, which a compressor can't. The higher levelised cost of water is a plant-scale metric that doesn't capture why TEC fits a panel-top robot."

**Q4. Is 0.3 L/m² really enough to clean a panel?**
"Yes, because we clean by contact, not by flushing. A damp microfibre bar lifts the dust by capillary uptake once the glass is wetted — that's documented in the cleaning literature I cite. You only need a full litre-plus rinse if you're trying to wash dust off as runoff. The damp wipe restores the transmittance without it, and that's the only reason the water budget is feasible at all."

**Q5. Did you actually build it, or is this only simulation?**
"Both. The bench prototype is built — the motion, sensing, and control hardware are purchased and assembled, about 4,150 pounds of it already in hand. The carriage motion is validated in Gazebo. What's left, and what I list as future work, is the full year of field measurement on a real rooftop."

**Q6. What about the quality of the harvested water — won't it spot the panels?**
"TEC condensate is essentially distilled — under 5 milligrams per litre of dissolved solids, well below the 50-milligram rinse limit for spotting. It passes a light treatment train: a sediment filter, activated carbon, and a UV step to stop biofilm in the tank. So it's actually cleaner than tap water."

**Q7. Walk me through the economics / payback.**
"The rooftop recovers about 3,100 kilowatt-hours a year of soiling losses, worth roughly 62 dollars at the current tariff. The bench prototype is 8,950 pounds, about 186 dollars, so the recovered energy alone returns it in about three years. The full self-supplying installation costs more and pays back slower on energy alone — but its real value is enabling cleaning at sites that have no water at all."

**Q8. How does the robot stay on a 24-degree tilt without sliding?**
"It doesn't rely on friction. It's a rail-guided gantry driven by a rack and pinion — a positive, geared mesh. The motor delivers 45 newtons against a 35-newton gravity-plus-rolling load, a 1.3 margin, with a 1.86 torque margin on the motor. The simulation confirms it climbs and holds. A free-wheeled rover, by contrast, slid — which is exactly why I went rail-guided."

**Q9. Why not just dry-brush, or use a waterless electrostatic method?**
"Dry brushing risks scratching the glass and removes less of the soiling. Wet wiping restores more transmittance, which the literature backs. Electrostatic and waterless methods exist but have their own limits in heavy, sticky desert dust. The damp wipe is the balance: effective, gentle, and nearly water-free."

**Q10. Is COP 1.9 realistic for a Peltier device?**
"It's the modelled operating COP under NAC's cool, humid night conditions, at the optimised current. It's consistent with published TEC water-harvesting tests by Shourideh and by Eslami, whose measured per-module rates bracket mine. I deliberately sized the operating point near the smallest temperature lift that still clears the dew-point margin, which is where COP is best."

**Q11. Why include Benban at all if you deploy at NAC?**
"As a stress test. If the design produces water even in the driest air in Egypt, then anywhere greener is safe. Benban is the floor; NAC is the design point. It's there to prove robustness, not as a deployment target."

**Q12. When does it harvest versus clean — don't they conflict?**
"No, they're time-separated. It harvests at night during the dew window and cleans at dawn or in daylight when the panels are producing. The battery time-shifts the night-time harvesting load into the daytime solar surplus, so the array always covers it."

**Q13. How does this scale to a 200 kWp farm?**
"Same harvester and same control, with more tiles and longer rails, and a fleet of carriages instead of one. Fleet coordination — scheduling and rail conflict — is the piece I flag as future work for that scale."

**Q14. What's the single biggest risk or weakness?**
"Honestly, the thin self-sufficiency margin and the dependence on a real field season to confirm the modelled yields. I've been conservative — worst-case site, conservative collection efficiency — but until it runs a full year on a roof, the yield numbers are modelled, not measured. That's my number-one next step."

**Q15. (If asked about team)** "This was an individual senior design project; I carried the design, the modelling, the prototype, and the simulation."
