# Solar Sorption Atmospheric Water Harvesting for Egypt — One-Page Brief

**Pitch.** A solar-regenerated desiccant unit that pulls drinking-quality, **salt-free** water
from night air for **off-grid communities in Egypt's new reclaimed lands** — where the grid
is absent, groundwater is deep and brackish, and refrigeration-based water machines physically
do not work.

---

### The problem
Agriculture is **80–85 %** of Egypt's water; the new desert-reclamation settlements run on
**fossil groundwater (to 1,500 m), brackish (300–800+ ppm), and depleting**. The people living
there need *drinking* water, and their only options are trucked or bottled water (**5–7 EGP/L**)
or desalinating brackish wells. The incumbent air-water technology — **vapour-compression
condensation** (Watergen, GENAQ, Hydrologic) — **stops producing below ~30–35 % RH**, exactly
the arid interior's night condition. That market is unserved.

### The solution & the right method
A **solar-thermal-regenerated sorption** unit: night air adsorbs onto a desiccant; daytime sun
regenerates it; vapour condenses to liquid. We benchmarked three methods on hourly NASA-POWER
climate at **6 Egyptian sites**, in EGP:

| Method | Works arid? | Water (1 m³ sorbent) | LCOW |
|---|---|---|---|
| PV condensation | **No** (fails at Benban) | humid-only | 0.5–1.6 EGP/L |
| Silica gel (sorption) | Yes | 20,000–33,000 L/yr | 0.6–1.0 EGP/L |
| **CaCl₂/silica composite (sorption)** | **Yes** | **51,000–94,000 L/yr** | **0.40–0.74 EGP/L** |

The **CaCl₂ composite is best at every site** — most water *and* lowest cost — and the only
option that holds up in the arid new lands. Its **2.76× advantage over plain silica gel is
confirmed in our G1-validated CADET model**, not assumed.

### Why it is credible (the engineering is done)
A full multi-fidelity simulation pipeline, gated and validated:
- **Tier-0** isotherm + isosteric heat (Gate G0 pass; cross-checked 43 kJ/mol).
- **Tier-1** CADET packed-bed breakthrough vs the LSBU dataset (**Gate G1 pass**).
- **Tier-2** a **custom OpenFOAM adsorption solver** written and validated (mass-balance V1,
  Ergun Δp V2 to 0.29 %).
- **Surrogate** (water R²=0.98) → **6-site annual yield**, **EGP economics**, and a 3D model.

### Market & competition
AWG market **$4.2–7.9 bn by 2030, ~9–17 % CAGR**. Sorption peers: SOURCE Global, **Uravu Labs**
(liquid desiccant — dropped silica gel), **Water Harvesting Inc / Atoco** (MOF, low-RH).
Condensation peers dominate the humid/grid segment. In Egypt, only **IRSC (Cairo)** builds AWGs —
the **off-grid arid-land sorption niche is open**.

### Economics & honest verdict
- **Cost:** ~0.4–0.7 EGP/L (composite) vs bottled 5–7 EGP/L → **payback ~2–4 years** for
  households that buy water. **Near-zero electrical SEC** (0.11–0.17 kWh/kg; regen is solar).
- **Not** an irrigation source (volume: one feddan would need ~167 t of sorbent) and **not**
  competitive with subsidized Nile tap (~0.001 EGP/L). It is a **decentralized, salt-free
  domestic-water** product for places the grid and clean groundwater don't reach.

### The ask / roadmap
1. **Build the prototype on cheap silica gel** (full pipeline already validated on it).
2. **Upgrade the sorbent to a CaCl₂/silica composite** for the validated ~2.8× yield at low RH;
   engineer against salt leaching/corrosion. Locally-sourced **rice-husk-ash silica** is the
   cost/sustainability path.
3. **Pilot in one reclaimed-land settlement**; sell the financed *unit*, not the litre.

**Bottom line:** a defensible, solar, salt-free, off-grid water unit for Egypt's new lands —
strongest where every competitor is weakest.
