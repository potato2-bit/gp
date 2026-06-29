# AWH Simulation Design Spec — DoE / Surrogate / Climate / Economics / Repo

**System:** Solar-regenerated silica-gel adsorption atmospheric water harvester (AWH).
Night adsorption -> daytime solar regeneration -> ambient condensation -> distilled water for
autonomous PV-panel cleaning across several Egyptian climate sites. No thermoelectric stage.

**Scope of this document:** Everything *except* the CFD solver physics. The high-fidelity core is
an OpenFOAM 2-D axisymmetric model of the silica-gel packed bed (specified separately). This
document covers the design of experiments (DoE) that exercises that solver, the surrogate that
replaces it, the climate coupling that drives the surrogate over 8760 h at many sites, the
economics (LCOW), the reproducible repo layout, and the end-to-end V&V gates.

**Why multi-fidelity:** the axisymmetric CFD is too slow to run 8760 h x 6 sites = ~52,560
evaluations. We run the CFD on a sparse DoE (a few hundred cases), fit a Gaussian-process surrogate
per response, then evaluate the surrogate millions of times against hourly NASA POWER data. The
surrogate is the bridge between "physically faithful but slow" and "annual sweep at site scale".

---

## 1. DoE input factors

The factor set is split into **operating factors** (set by climate and control each cycle — these
are the live inputs at climate-sweep time) and **design factors** (fixed by hardware — chosen once,
then frozen for the annual sweep). A single surrogate is trained over the *union* of both so we can
later optimize the design; at sweep time the design factors are held at the chosen design point and
only the operating factors vary hour-to-hour (cycle-to-cycle).

### Operating factors (vary with climate/control — surrogate inputs at sweep time)

| # | Factor | Symbol | Range | Justification (Egypt-specific) |
|---|--------|--------|-------|-------------------------------|
| 1 | Adsorption-phase ambient temperature | `T_ads` | 5 – 30 °C | Night-time T2M across the 6 sites. Aswan/Siwa winter nights drop to ~5–8 °C; Delta/coast summer nights stay ~22–28 °C. Adsorption is the cool, humid half-cycle, so the relevant T is the *nocturnal* envelope, not the 45 °C daytime peak. |
| 2 | Adsorption-phase relative humidity | `RH_ads` | 15 – 90 % | Drives uptake. Upper-Egypt desert nights ~20–40 % RH; Mediterranean/Red-Sea coast nights 60–90 %. Floor at 15 % covers the worst Siwa/Aswan summer night; ceiling 90 % covers Alamein/Hurghada humid nights. Silica gel uptake is steep in 0.3–0.7 a/a0, so this range must be wide. |
| 3 | Regeneration temperature | `T_reg` | 60 – 120 °C | Solar-collector-delivered desorption temperature. 60 °C is the minimum that meaningfully strips physisorbed water from silica gel; 120 °C is the practical ceiling for a single-glazed flat-plate/evacuated air collector in Egyptian DNI (the upper end needs evacuated tubes or concentration). Above ~120 °C silica-gel hydrothermal aging accelerates. |
| 4 | Air face velocity | `u_face` | 0.1 – 1.0 m/s | Superficial velocity through the packed bed. Below 0.1 m/s the bed is mass-transfer-starved; above ~1 m/s the fan parasitic (pressure drop ~ u to u^1.8 via Ergun) and outlet-air bypass dominate. Sets both the adsorption loading rate and the regeneration sweep. |

### Design factors (hardware — frozen for the annual sweep, swept in DoE for later optimization)

| # | Factor | Symbol | Range | Justification |
|---|--------|--------|-------|---------------|
| 5 | Bed length (flow depth) | `L_bed` | 30 – 150 mm | Axial depth of packed silica gel. 30 mm = thin fast-cycling bed (low Δp, low capacity); 150 mm = deep high-capacity bed (high Δp, slow thermal wave). Brings the diffusion/convection time-constant trade-off into the DoE. |
| 6 | Particle diameter | `d_p` | 1 – 4 mm | Commercial silica-gel bead grades. Small beads: fast intraparticle diffusion, high Δp; large beads: low Δp, slow kinetics. 1–4 mm spans the standard packed-bed dehumidification grades. |
| 7 | Half-cycle time | `t_half` | 2 – 12 h | Duration of each adsorption (or regeneration) phase. Anchored to the diurnal cycle: a one-cycle-per-day machine has ~12 h adsorption (night) + ~12 h regeneration (day); faster sub-diurnal cycling (2–6 h) is allowed in the DoE so the optimizer can choose. The CYCLE, not the hour, is the integration unit downstream. |

**Total: 7 factors** (4 operating, 3 design). Air pressure is fixed per-site from elevation
(Magnus + station pressure, already handled by `psychrometrics_hourly.py`); it is not a DoE factor.

**Surrogate inputs at climate-sweep time:** `T_ads`, `RH_ads`, `T_reg`, plus the frozen design
vector (`u_face`, `L_bed`, `d_p`, `t_half`). Of these, the first three change every cycle from NASA
POWER; `T_reg` is derived from daytime irradiance via the collector relation in §6. The design
vector is constant across the 8760-h sweep for a given hardware configuration.

---

## 2. DoE sampling design

### Recommended sampler

**Sobol' sequence (scipy.stats.qmc.Sobol)** as the primary sampler, with **LHS-maximin
(scipy.stats.qmc.LatinHypercube, `optimization="random-cd"` or SMT `LHS criterion='ese'`)** as a
cross-check. Rationale:

- **Sobol'** gives low-discrepancy, space-filling coverage that is *extensible* — you can double the
  sample (next 2^k block) without discarding earlier runs, which matters because each CFD case is
  expensive and you may want to add points after seeing the first fit. Use a power-of-two sample
  size to preserve Sobol' balance properties.
- **LHS-maximin** guarantees one sample per equal-probability stratum per axis and maximizes the
  minimum inter-point distance; it is the classical GP/Kriging training design and is the safe
  default if you do not need extensibility.

For 7 factors GP fitting, either is defensible; Sobol' is preferred here only because of the
extend-without-waste property.

### Run count

Rule of thumb for GP training designs: **10–15 x dimensions**.

- 7 factors -> **70–105 training runs**. Use a Sobol' block of **128** (next power of two above 105)
  for clean extensibility, or 96 if CFD budget is tight.
- **Held-out test set: 24–32 additional points** drawn from an *independent* Sobol' sequence (or a
  different scramble seed) — never reuse training points for the acceptance gates in §5. ~25 % of the
  training count is a reasonable held-out size.
- **Total CFD budget: ~150–160 cases** (128 train + 32 test). At a few minutes to ~1 h per
  axisymmetric case this is an overnight-to-few-days batch under WSL (§4).

### Adaptive / sequential refinement (optional, recommended)

After the initial fit, add points where the surrogate is least trustworthy:

- **GP variance-based infill (active learning MacKay / ALM):** sample where posterior variance is
  highest.
- **Expected-improvement-style infill** if you are also optimizing yield/SEC.
- SMT exposes `smt.applications.ego` and adaptive sampling helpers; or implement ALM directly from
  the KRG `predict_variances`. Add in small batches (8–16) and re-validate until gates pass.

### Tools

- `scipy.stats.qmc.Sobol`, `scipy.stats.qmc.LatinHypercube` (in-stdlib-adjacent, already a dep).
- `SMT` (`smt.sampling_methods.LHS`) — integrates directly with the SMT surrogate.
- `pyDOE3` — classical designs (full/fractional factorial, Box-Behnken) if you later want a
  response-surface comparison.
- `SALib` — if you want Sobol' *sensitivity indices* (not just sampling) to rank factor importance.

---

## 3. CFD response outputs -> surrogate targets

Each CFD run returns per-cycle integrated and transient quantities. We train **one independent GP
per scalar response** (multi-output GPs are possible but per-response GPs are simpler, let each
response choose its own hyperparameters, and let a response fail its gate without poisoning others).

| # | CFD response | Symbol | Units | How obtained from CFD | Surrogate target |
|---|--------------|--------|-------|----------------------|------------------|
| 1 | Water uptake / yield per cycle | `m_w` | kg/cycle (or kg per kg sorbent) | Time-integral of adsorbed-then-desorbed water mass over the half-cycle; equals delivered condensate per cycle | GP #1 (primary yield model) |
| 2 | Cycle-average specific energy consumption | `SEC` | kWh/kg | (regen energy + fan energy) / `m_w` | GP #2 |
| 3 | Regeneration energy per cycle | `Q_reg` | kWh/cycle (or kJ) | Time-integral of heat input to the bed during desorption | GP #3 |
| 4 | Peak bed temperature | `T_peak` | °C | Max cell temperature over the regeneration phase | GP #4 (safety/aging guard) |
| 5 | Pressure drop | `dP` | Pa | Steady Δp across bed at `u_face` (Ergun-consistent CFD output) | GP #5 (drives fan OPEX) |
| 6 | Outlet humidity transient | `omega_out(t)` | kg/kg vs t | Outlet patch time series | reduced to scalars (see below) |
| 7 | Outlet temperature transient | `T_out(t)` | °C vs t | Outlet patch time series | reduced to scalars (see below) |

**Handling transients (#6, #7):** do **not** train a GP on full time series. Reduce each transient
to physically meaningful scalars and fit a GP to each scalar:

- breakthrough time (time to reach X % of inlet ω during adsorption),
- peak outlet ω during regeneration (condenser sizing),
- cycle-mean outlet T.

If a transient shape is genuinely needed downstream, fit GPs to a few principal-component scores of
the curve (POD/PCA reduction), but for this project the scalar reductions above are sufficient — the
economics and annual-yield model only consume `m_w`, `SEC`, `Q_reg`, `dP`, and `T_peak`.

**Minimum target set for the annual sweep:** GP #1 (`m_w`) and GP #5 (`dP`) are mandatory (yield +
fan OPEX). GP #2/#3 give SEC/regen energy for the energy balance. GP #4 (`T_peak`) is a constraint
check, not a yield driver.

---

## 4. Automation — templating + batch-running the DoE under WSL

Goal: from a DoE table (CSV of factor values, one row per case), generate one OpenFOAM case
directory per row, run them all under WSL2, extract the §3 responses to a single tidy CSV. Fully
reproducible from the DoE seed.

### Case templating (Python -> OpenFOAM)

Two viable approaches; **Jinja2 dictionary templating is recommended** for clarity and zero OpenFOAM
Python-binding fragility:

- **Jinja2 (recommended):** keep a `cases/template/` skeleton (`0/`, `constant/`, `system/`) with
  `{{ T_reg }}`, `{{ u_face }}`, `{{ L_bed }}`, `{{ d_p }}`, etc. placeholders in the dict files
  (`blockMeshDict`, `transportProperties`/bed properties, boundary `0/` fields, `controlDict`).
  A `doe/render_cases.py` loop reads the DoE CSV and renders one `cases/run_0001/`… per row.
  Bed length / particle diameter feed `blockMeshDict` geometry and the porous-media/kinetics
  coefficients respectively.
- **PyFoam (alternative):** `ParsedParameterFile` edits dict entries programmatically. Robust but
  adds a heavier dependency and can lag OpenFOAM version changes. Use it only if you prefer
  object-level edits over text templating.

Pin the OpenFOAM version (e.g. OpenFOAM v2312 / OpenFOAM 11) and record it in `docs/` so meshes and
dict schemas stay stable.

### Batch execution under WSL2

- Driver script `doe/run_doe.sh` (runs inside WSL) iterates case dirs: `blockMesh` -> solver ->
  `postProcess`.
- Parallelize across cases (not within — each axisymmetric case is small) with **GNU parallel**:
  `ls -d cases/run_* | parallel -j $(nproc) ./run_one_case.sh {}`. This is the simplest robust job
  array on a single WSL box. On a cluster, swap for a SLURM job array.
- Each case writes a `controlDict` `functionObjects` block to compute Δp, outlet patch averages, and
  integrated mass on the fly, so no post-hoc reconstruction is needed.

### Result extraction -> CSV

- Use OpenFOAM **`functionObjects`** (`fieldAverage`, `surfaceFieldValue` on inlet/outlet patches,
  `volFieldValue` for bed temperature) writing to `postProcessing/`.
- `doe/extract_results.py` walks `cases/run_*/postProcessing/`, reads the function-object `.dat`
  files, computes the §3 scalar reductions, and appends one row per case to
  `data/doe_responses.csv` keyed by case id (joined back to the DoE factor table by id).

### Reproducibility

- One `doe/doe_config.yaml`: sampler (`sobol`/`lhs`), seed, n_train, n_test, factor bounds.
- The DoE table (`data/doe_design.csv`) is regenerable bit-for-bit from seed + config.
- Log OpenFOAM version, solver name, and git commit into each case dir (`case_meta.json`).

---

## 5. Surrogate model

### Recommendation

**Gaussian Process / Kriging, one model per response (§3).**

- **Library: SMT (Surrogate Modeling Toolbox), `smt.surrogate_models.KRG`.** SMT is purpose-built for
  engineering surrogates, exposes `predict_variances` (needed for adaptive infill in §2), supports
  the Matérn 5/2 correlation, and offers `MFK` (multi-fidelity Kriging) if you later add a cheap
  low-fidelity model (e.g. a lumped/0-D bed model) to fuse with the CFD. *(Verified: SMT correlation
  functions include `matern52`, `matern32`, `squar_exp`, `abs_exp`; SMT provides KRG and MFK.)*
- **Alternatives:** `sklearn.gaussian_process.GaussianProcessRegressor` (with
  `Matern(nu=2.5) + WhiteKernel` for nugget) — fine, widely understood, but weaker on training-data
  derivatives and multi-fidelity. `GPy` — most flexible kernels, heavier API. Use sklearn as the
  fallback if SMT install is troublesome under WSL.

### Kernel

**Matérn 5/2** (`corr='matern52'` in SMT, `Matern(nu=2.5)` in sklearn). It is twice-differentiable
(physically sensible for smooth thermofluid responses) without the over-smoothing of the squared-
exponential. Include a **nugget** (`WhiteKernel` / SMT `nugget`/`noise` term) to absorb CFD numerical
noise and keep the covariance matrix well-conditioned. Standardize inputs to the unit hypercube and
standardize each response (zero mean, unit variance) before fitting; anisotropic length-scales (one
per factor) let the GP learn factor importance.

### Validation and acceptance gates

- **k-fold cross-validation, k = 5** (or leave-one-out for the ~128-point set if cheap).
- **Acceptance gates per response:**
  - **R² ≥ 0.95** on the held-out test set (and CV mean R² ≥ 0.95).
  - **RMSE ≤ 5 % of the response range** (normalized RMSE on held-out test).
  - For the safety response `T_peak`, also require **max abs error ≤ 5 °C** (not just RMSE), because
    it gates the aging constraint.
- **Parity plots** (predicted vs CFD) for every response, with the y=x line and ±5 % band, saved to
  `results/parity/`.
- **Residual diagnostics:** residuals vs each factor (catch un-modeled curvature), and a
  standardized-residual histogram.

### Out-of-box clamping

The GP is only trusted inside the DoE box. At prediction time:

- **Clamp inputs** to the trained bounds before calling `predict` (record how many climate hours were
  clamped, per site — reported in §6).
- Optionally **flag extrapolation** via the GP posterior variance: if `predict_variances` exceeds a
  threshold (e.g. 2x the in-box mean variance), tag the cycle as low-confidence in the output.
- Never let `m_w` go negative or `SEC` go non-physical: post-clamp responses to physical floors.

### When to use the alternatives (brief)

- **Polynomial response surface (RSM, quadratic):** only as a fast sanity baseline or if you used a
  Box-Behnken/CCD design; cheap and interpretable but cannot capture the steep silica-gel isotherm
  knee — expect it to fail the R² gate on `m_w`.
- **RBF interpolation (SMT `RBF`):** good interpolator, no uncertainty estimate; use if GP
  hyperparameter optimization is unstable, but you lose the variance needed for adaptive infill.
- **Gradient-boosted trees (XGBoost/LightGBM):** robust to non-smoothness and great with *many*
  training points; for ~128 smooth-physics points a GP will generalize better, and trees give no
  smooth gradients or calibrated uncertainty. Use GBT only if you scale the DoE to thousands of runs.

---

## 6. Climate coupling and site list

### Site list (6 Egyptian sites spanning climate zones)

Coordinates and Köppen classes verified via public sources; T/RH characterizations are typical-year
qualitative envelopes to be replaced by the actual NASA POWER pull. All six are **BWh (hot desert)**
or **BWh/BSh** in the Köppen scheme — Egypt is overwhelmingly hot-desert — so the spanning axis is
**humidity and night-temperature regime** (coastal-humid vs interior-arid vs Nile-valley), which is
exactly what drives adsorption AWH.

| Site | Role | Lat | Lon | Köppen | Why chosen |
|------|------|-----|-----|--------|-----------|
| **Aswan / Benban** | Upper-Egypt arid; the PV anchor site | 24.45 N | 32.75 E | BWh | Benban solar park block (matches `project_inputs.yaml`). Hottest, driest — the AWH stress case. Aswan city ≈ 24.09 N, 32.90 E. |
| **Mansoura (Nile Delta)** | Agricultural Delta interior | 31.04 N | 31.38 E | BWh/BSh | Humid Delta nights, moderate temps — favorable adsorption, contrasts with Aswan. |
| **New Alamein (Mediterranean coast)** | Coastal new city | 30.93 N | 28.45 E | BWh (Mediterranean-influenced) | High coastal night RH; new sustainable-city deployment target. |
| **Hurghada (Red Sea coast)** | Red-Sea coastal | 27.18 N | 33.80 E | BWh | Marine humidity + very high DNI — best simultaneous humidity-and-solar case for solar regeneration. |
| **Siwa (Western Desert interior)** | Deep desert oasis | 29.20 N | 25.52 E | BWh | Extreme interior aridity, large diurnal swing — the low-RH stress case. (Siwa town ≈ 29.20 N, 25.52 E.) |
| **New Administrative Capital** | Desert-interior new megacity | 30.00 N | 31.60 E | BWh | Flagship "new sustainable city" deployment site; desert-interior climate near Cairo. |

*Coordinate caveats (flagged unverified-precise):* Aswan/Benban and Mansoura coordinates are
well-sourced. New Alamein (~30.92 N, 28.45 E), Siwa (~29.20 N, 25.52 E), and the New Administrative
Capital (~29.9–30.0 N, 31.6–31.7 E) are approximate city centroids from public sources; refine to
the exact deployment block before the production run. NASA POWER returns the ~0.5° grid cell, so
sub-0.1° precision does not change the climate pull materially.

### NASA POWER parameters to fetch

Hourly point API, community `RE`. Fetch **T2M, RH2M, ALLSKY_SFC_SW_DWN, WS2M** (plus keep
**PRECTOTCORR** for rain-skip logic on cleaning days). *(Verified: hourly endpoint is
`/api/temporal/hourly/point`; max 15 parameters/request; data from 2001-01-01 to near-real-time;
dates `YYYYMMDD`; communities include RE/SB/AG; defaults to LST.)*

| Param | Meaning | Use in pipeline |
|-------|---------|-----------------|
| `T2M` | 2-m air temp (°C) | adsorption-phase `T_ads`; collector ambient |
| `RH2M` | 2-m relative humidity (%) | adsorption-phase `RH_ads` |
| `ALLSKY_SFC_SW_DWN` | all-sky shortwave down (W/m² or MJ/h) | drives `T_reg` via collector relation |
| `WS2M` | 2-m wind speed (m/s) | collector convective-loss term; condenser ambient |
| `PRECTOTCORR` | corrected precip (mm/h) | skip cleaning / passive-rinse logic |

### Extending the existing fetch script

`scripts/fetch_nasa_power.py` already builds the hourly point URL and writes a CSV. Two changes:

1. **Add irradiance + wind to the parameter list** in `project_inputs.yaml` under
   `nasa_power.parameters`: `[T2M, RH2M, ALLSKY_SFC_SW_DWN, WS2M, PRECTOTCORR]` (5 params, well under
   the 15-param cap).
2. **Loop over multiple sites.** Replace the single `site:` block with a `sites:` list (name, lat,
   lon, elevation, koppen). Wrap the existing fetch body in `for s in cfg["sites"]:` and write one
   CSV per site: `data/climate/nasa_power_hourly_<site>.csv`. Keep the same JSON-parse/align logic;
   only the output filename and lat/lon vary. This is a ~15-line change that preserves the verified
   request structure already in the script.

### Half-cycle aggregation (hour -> cycle -> day -> year)

The surrogate's integration unit is the **cycle**, not the hour. Map the diurnal profile onto the
surrogate inputs as follows, for each calendar day:

1. **Split day into adsorption window (night) and regeneration window (day)** using solar
   geometry or simply `ALLSKY_SFC_SW_DWN > 0` for daytime. With one cycle/day, adsorption ≈ the dark
   hours, regeneration ≈ the sunlit hours; `t_half` is then the window length (≈ matches the 12 h
   half-cycle, consistent with the DoE range).
2. **Representative adsorption T, RH:** aggregate the night hours. Use the **humidity-weighted mean**
   (mass-of-water-weighted) rather than a plain arithmetic mean, because uptake is set by available
   vapor: `RH_ads = mean over night of RH2M`, `T_ads = mean over night of T2M`, or better, compute
   night-mean humidity ratio ω via `psychrometrics_hourly.py` and back out the representative
   `(T_ads, RH_ads)` consistent with that ω. Reuse the existing `omega_kg_kg()` and `p_ws_pa()`
   functions directly.
3. **Regeneration temperature from daytime irradiance** via a simple flat-plate **solar air
   collector** relation (verified qualitatively: outlet T rises ~linearly with irradiance, and
   collector efficiency falls as plate-ambient ΔT grows):

   ```
   T_reg = T_amb_day + (eta_coll * G_bar * A_coll) / (m_dot_air * cp_air)
   ```
   where `G_bar` is the daytime-mean `ALLSKY_SFC_SW_DWN`, `eta_coll` a constant collector efficiency
   (0.45–0.6 for a good single-glazed air collector; or the standard
   `eta = eta_0 - a1*(T_plate - T_amb)/G` curve if you want temperature-dependent efficiency),
   `A_coll` the collector area, `m_dot_air = rho * u_face * A_bed`, `cp_air ≈ 1005 J/kg·K`.
   **Clamp `T_reg` to the DoE range [60, 120] °C.** On low-irradiance days `T_reg` may fall below
   60 °C — then the day yields little/no regeneration; record those days explicitly.

4. **Evaluate the surrogate once per cycle** with `(T_ads, RH_ads, T_reg, design_vector)` ->
   `m_w`, `SEC`, `Q_reg`, `dP`. **Clamp every input to the trained box first** (§5) and count clamped
   cycles per site.
5. **Integrate:** `daily_water = sum of m_w over cycles that day` (usually 1) ->
   `annual_water = sum over 365 days`. Aggregate parasitic fan energy from `dP` and `u_face`, and
   regeneration energy from `Q_reg`, the same way.
6. **Seasonal breakdown:** report monthly and DJF/MAM/JJA/SON water, SEC, and yield per site —
   adsorption AWH typically peaks in the humid cool season, so the seasonal profile is a key result.
7. **Rain handling:** on hours with meaningful `PRECTOTCORR`, log a passive-rinse / cleaning-skip
   flag (the robot need not clean a freshly rained-on panel); this feeds the cleaning-demand model,
   not the water-production model.

**Output of climate stage:** per-site `results/annual_<site>.csv` (monthly + annual water, SEC,
regen energy, fan energy, clamped-cycle count) and a cross-site summary table.

---

## 7. Economics / LCOW

### LCOW formula

```
LCOW = (CRF * CAPEX + OPEX_annual) / Water_annual          [USD per m^3 or per L]

CRF  = i (1 + i)^n / ((1 + i)^n - 1)                        capital recovery factor
```

With `i = 0.08`, `n = 15 yr` (from `project_inputs.yaml`): **CRF ≈ 0.1168**.
`Water_annual` is the §6 annual yield (use m³ for $/m³, then divide by 1000 for $/L).

### CAPEX components

| Component | Basis |
|-----------|-------|
| Silica-gel mass & cost | `m_sorbent = rho_bulk * A_bed * L_bed` x bed count; cost per kg of desiccant. Anchor total against `capex_MUSD.silica_desiccant = 2.2 MUSD` at plant scale. |
| Vessel / bed housing | Pressure vessel + ducting, scaled with bed volume. |
| Solar collector | `A_coll` (from §6 collector sizing) x $/m² installed air-collector cost. |
| Fan / blower | Sized for `dP` at `u_face`; cost ~ with rated airflow x static pressure. |
| Condenser | Sized from peak regeneration outlet ω (the §3 transient reduction). |
| Controls / automation | Sensors, valves, dampers, PLC, integration. |

### OPEX components (annual)

| Component | Basis |
|-----------|-------|
| Fan parasitic energy | `E_fan = (Vdot * dP / eta_fan) * operating_hours`, costed at `electricity_USD_per_kWh = 0.020`. `dP` from GP #5, `Vdot = u_face * A_bed`. |
| Regeneration energy cost | If regeneration is purely solar-thermal, this is ~0 marginal; include only any electric trim/backup heat. (Solar-thermal is the design intent, so the regeneration energy is mostly a CAPEX, not OPEX, line.) |
| Maintenance | % of CAPEX/yr (typically 2–4 %). |
| Periodic silica-gel replacement | Silica gel degrades over thousands of ad/de cycles; amortize replacement every ~3–5 yr as an annualized OPEX line. |

### Worked structure (to be filled by the economics module)

```
CRF            = 0.08*(1.08^15) / (1.08^15 - 1)            ≈ 0.1168
Annualized CAPEX = CRF * (Cap_sorbent + Cap_vessel + Cap_coll
                          + Cap_fan + Cap_cond + Cap_ctrl)
OPEX_annual     = E_fan*0.020 + maint + sorbent_replacement_annualized
LCOW            = (Annualized CAPEX + OPEX_annual) / Water_annual_m3
```

### Sanity anchors (verified figures)

- **SEC anchor:** adsorption SEC ≈ **1.16 kWh/kg** (`project_inputs.yaml`, `sec_kWh_per_kg.adsorption_avg`).
  The surrogate's cycle-average SEC (GP #2) should land in the same order of magnitude; published
  solar-desiccant AWH energy is **116–1021 kWh/m³** (≈ 0.12–1.0 kWh/kg of *thermal* input), so a
  solar-thermal machine sits at the low end of electric-equivalent SEC. *(Verified: ACS ES&T Eng.
  2024 cites solar-desiccant AWH at 116–1021 kWh/m³.)*
- **LCOW anchor (condensation, grid):** **≈ $0.17/L ($170/m³)** for a modeled AWH unit in an arid
  climate on grid power; **≈ $0.09/L** on existing solar PV. *(Verified: ACS ES&T Eng. 2024.)*
- **LCOW anchor (sorbent-based, literature range):** **$6.5–11/m³** (≈ **$0.0065–0.011/L**),
  depending on energy recovery and sorbent. The adsorption machine here should land far below the
  $0.17/L condensation figure and near the sorbent literature band; if it does not, revisit collector
  sizing or yield. *(Verified: ACS ES&T Eng. 2024 citing prior sorbent-system work.)*

Egypt's very low electricity tariff (0.020 USD/kWh) and high solar resource both push LCOW down
versus the literature, which is the project's central economic argument.

---

## 8. Reproducible repo structure for `awh_sim/`

```
awh_sim/
├── README.md
├── requirements.txt
├── awh_sim_config.yaml          # sub-project config (extends/imports project_inputs.yaml)
├── cases/
│   ├── template/                # OpenFOAM skeleton with Jinja2 placeholders (0/, constant/, system/)
│   └── run_XXXX/                # generated per-DoE-row (git-ignored; regenerable)
├── solver/                      # custom solver / fvOptions / porous-bed setup (CFD side, ref only)
├── doe/
│   ├── doe_config.yaml          # sampler, seed, n_train, n_test, factor bounds
│   ├── sample_doe.py            # Sobol'/LHS -> data/doe_design.csv
│   ├── render_cases.py          # Jinja2: doe_design.csv -> cases/run_XXXX/
│   ├── run_doe.sh               # WSL driver: blockMesh -> solve -> postProcess (GNU parallel)
│   └── extract_results.py       # postProcessing/*.dat -> data/doe_responses.csv
├── surrogate/
│   ├── train.py                 # SMT KRG per response; k-fold CV; save models
│   ├── validate.py              # parity plots, gate checks (R^2>=0.95, nRMSE<=5%)
│   └── models/                  # pickled/serialized GPs (one per response)
├── climate/
│   ├── fetch_sites.py           # extends scripts/fetch_nasa_power.py to sites + irradiance
│   ├── aggregate_cycles.py      # hour -> cycle (T_ads, RH_ads, T_reg); reuses psychrometrics
│   └── run_annual.py            # drive surrogate over 8760 h x sites -> results/annual_*.csv
├── economics/
│   └── lcow.py                  # CRF, CAPEX/OPEX build-up, LCOW vs anchors
├── data/
│   ├── doe_design.csv
│   ├── doe_responses.csv
│   └── climate/                 # nasa_power_hourly_<site>.csv (one per site)
├── results/
│   ├── parity/                  # surrogate parity plots
│   ├── annual_<site>.csv
│   └── summary_lcow.csv
├── docs/
│   └── DESIGN_DOE_SURROGATE_CLIMATE_ECON.md   # this document
└── tests/
    ├── test_aggregate_cycles.py
    ├── test_lcow.py             # CRF, LCOW formula unit tests
    └── test_surrogate_clamp.py  # out-of-box clamping behavior
```

### Config

Add `awh_sim/awh_sim_config.yaml` that **imports the existing `project_inputs.yaml`** (economics,
SEC anchors, Benban site) and adds the AWH-specific blocks: `sites:` list (§6), `doe:` (factor
bounds, sampler, seed, run counts), `surrogate:` (kernel, gates), `collector:` (eta, area), `bed:`
(rho_bulk, bed count). Do not duplicate economics — read them from `project_inputs.yaml` so there is
one source of truth.

### Reuse of existing scripts

- `scripts/fetch_nasa_power.py` -> base for `climate/fetch_sites.py` (add irradiance/wind + site
  loop; §6).
- `scripts/psychrometrics_hourly.py` -> import `p_ws_pa`, `omega_kg_kg` directly in
  `climate/aggregate_cycles.py` for the night-ω and dew-point math; no rewrite.
- `project_inputs.yaml` -> single source of economics, SEC anchors, discount rate, life.

### Pinned `requirements.txt`

```
numpy>=1.26,<3
scipy>=1.11           # stats.qmc Sobol/LHS
pandas>=2.0
matplotlib>=3.8
pyyaml>=6.0
requests>=2.31        # NASA POWER fetch (or keep urllib stdlib)
smt>=2.6              # KRG, MFK, matern52, LHS, EGO/adaptive
scikit-learn>=1.4     # GaussianProcessRegressor fallback + CV utilities
pyDOE3>=1.0           # classical designs (RSM comparison)
SALib>=1.5            # Sobol sensitivity indices (optional)
Jinja2>=3.1           # OpenFOAM case templating
# PyFoam            # optional alternative to Jinja2 templating; install only if used
```

Pin exact versions in a lockfile (`pip freeze > requirements.lock.txt`) once the WSL environment is
validated, since SMT and its compiled deps are the most version-sensitive piece.

---

## 9. End-to-end V&V gates

Three gates in series; each must pass before the next is trusted.

### Gate A — CFD validation (upstream; physics spec owns the detail)

- Mesh-independence (Δp and uptake within ~2 % across mesh levels) and time-step independence.
- Bed energy/mass balance closes within ~1–2 % per cycle.
- Validate against at least one published silica-gel packed-bed breakthrough/uptake dataset (isotherm
  + kinetics) before generating the DoE responses. **No surrogate is fit until Gate A passes.**

### Gate B — Surrogate accuracy (§5)

- Per response, on the held-out test set: **R² ≥ 0.95** and **nRMSE ≤ 5 % of range**; `T_peak` also
  **max abs error ≤ 5 °C**.
- 5-fold CV mean R² ≥ 0.95 (guards against a lucky test split).
- Parity plots within ±5 % band; residuals show no systematic factor dependence.
- If any response fails, add adaptive infill points (§2) and refit; do not proceed to the annual
  sweep with a failed response.

### Gate C — Annual-yield + LCOW sanity vs literature

- **Specific water productivity (SWP):** per-cycle yield per kg sorbent should sit in the published
  silica-gel band — pure silica gel ≈ **0.1–0.4 L/kg per cycle** (≈ 159 g/kg in a 12-h cycle at
  ~556 W/m² is a reported point); composites reach higher. A surrogate-driven annual yield implying
  >1 L/kg/cycle for *pure* silica gel is a red flag. *(Verified: silica-gel prototype ~159 g/kg per
  12-h cycle; composite systems ~0.4 L/kg/day.)*
- **SEC:** annual-mean SEC within a factor of ~2 of the 1.16 kWh/kg anchor (solar-thermal regen
  should trend lower on the *electric-equivalent* basis).
- **LCOW:** below the **$0.17/L** condensation/grid anchor and within range of the **$6.5–11/m³**
  sorbent literature band; if Egypt's low tariff + high DNI do not push it under $0.17/L, audit the
  CAPEX (collector area, sorbent mass) and yield.
- **Cross-site monotonicity check:** humid-coastal sites (Alamein, Hurghada, Mansoura) should
  out-yield arid-interior sites (Aswan, Siwa) at equal hardware — if not, the aggregation or clamping
  is wrong.
- **Clamped-cycle audit:** report the fraction of climate cycles clamped to the DoE box per site; if
  a large fraction is clamped (e.g. >10 %), widen the DoE ranges in §1 and re-run, because the
  surrogate is extrapolating over too much of the real climate.

---

## References (IEEE style)

[1] NASA Langley Research Center, "POWER | Docs | Data Services | Hourly API," NASA POWER.
[Online]. Available: https://power.larc.nasa.gov/docs/services/api/temporal/hourly/ (accessed Jun. 25, 2026).
*Verified: endpoint `/api/temporal/hourly/point`; max 15 parameters/request; hourly data 2001-01-01 to near-real-time; date format YYYYMMDD; communities RE/SB/AG; defaults to LST.*

[2] NASA Langley Research Center, "POWER | Docs | Tutorials | Parameters," NASA POWER.
[Online]. Available: https://power.larc.nasa.gov/docs/tutorials/parameters/ (accessed Jun. 25, 2026).
*Verified: T2M, RH2M, ALLSKY_SFC_SW_DWN, WS2M, PRECTOTCORR parameter definitions.*

[3] T. P. Tomich et al. / ACS authors, "Techno-Economic Analysis of Atmospheric Water Harvesting
Across Climates," *ACS ES&T Engineering*, 2024. [Online]. Available:
https://pubs.acs.org/doi/10.1021/acsestengg.4c00098 and PMC mirror
https://pmc.ncbi.nlm.nih.gov/articles/PMC11250088/ (accessed Jun. 25, 2026).
*Verified: arid-climate condensation AWH LCOW ≈ $0.17/L (grid), ≈ $0.09/L (existing solar PV);
annual yield ≈ 6,341 L/yr arid; sorbent-system LCOW $6.5–11/m³; solar-desiccant AWH energy
116–1021 kWh/m³.*

[4] P. Saren et al. (eds.) / SMT developers, "SMT 2.0: A Surrogate Modeling Toolbox with a focus on
Hierarchical and Mixed Variables Gaussian Processes," arXiv:2305.13998, 2023, and SMT documentation.
[Online]. Available: https://arxiv.org/abs/2305.13998 and https://smt.readthedocs.io/ (accessed
Jun. 25, 2026).
*Verified: SMT provides KRG and MFK; correlation functions include matern52, matern32, squar_exp,
abs_exp; LHS sampling; EGO/adaptive utilities; predict_variances.*

[5] SciPy developers, "scipy.stats.qmc — Quasi-Monte Carlo (Sobol, LatinHypercube)," SciPy manual.
[Online]. Available: https://docs.scipy.org/doc/scipy/reference/stats.qmc.html (accessed Jun. 25, 2026).
*Library capability, not independently re-verified beyond standard documentation.*

[6] Köppen climate classification (Egypt = BWh hot desert), Wikipedia / standard climatology.
[Online]. Available: https://en.wikipedia.org/wiki/K%C3%B6ppen_climate_classification (accessed
Jun. 25, 2026).
*Verified: Aswan and central/southern Egypt = BWh (hot desert), mean annual T > 18 °C.*

[7] Geodatos / latlong sources for Egyptian city coordinates (Aswan 24.09 N 32.90 E; Mansoura
31.04 N 31.38 E; Hurghada ~27.18 N 33.80 E; Siwa ~29.20 N 25.52 E; New Alamein ~30.92 N 28.45 E;
New Administrative Capital ~29.9–30.0 N 31.6–31.7 E). [Online]. Available:
https://www.geodatos.net/en/coordinates/egypt/aswan , https://www.latlong.net/ (accessed
Jun. 25, 2026).
*Aswan/Benban and Mansoura well-sourced; Alamein, Siwa, and NAC are approximate city centroids —
flagged for refinement to the exact deployment block.*

[8] Silica-gel adsorption AWH performance (specific water productivity / regeneration). Representative
sources from the adsorption-AWH literature, e.g. "Harvesting water from air using adsorption material
– Prototype and experimental results," *Separation and Purification Technology*, 2021, and composite
silica-gel/LiCl studies. [Online]. Available:
https://www.sciencedirect.com/science/article/pii/S1383586620323947 (accessed Jun. 25, 2026).
*Verified (search-level): pure silica gel ≈ 159 g water/kg sorbent per 12-h cycle at ~556 W/m²;
composite systems ≈ 0.4 L/kg/day; pure silica-gel uptake ≤ ~0.4 g/g — exact per-paper numbers
should be re-checked against the full text before citing in the thesis.*

[9] Flat-plate / solar air collector outlet-temperature–irradiance relation. Standard solar-thermal
references (Duffie & Beckman, *Solar Engineering of Thermal Processes*) and flat-plate performance
studies. [Online]. Available:
https://www.sciencedirect.com/science/article/abs/pii/S0038092X20308963 (accessed Jun. 25, 2026).
*Verified (search-level): outlet temperature rises ~linearly with irradiance; collector efficiency
falls as plate–ambient ΔT increases. The η0 − a1·ΔT/G curve is the standard model; coefficients
to be taken from the chosen collector datasheet.*

**Unverified / to refine before production:** exact deployment coordinates for Alamein/Siwa/NAC;
per-paper silica-gel SWP and isotherm numbers (search-level only); collector η coefficients (use
datasheet); the $/kg, $/m² unit costs for the CAPEX build-up (not yet anchored to vendor quotes —
only the plant-scale 2.2 MUSD desiccant total in `project_inputs.yaml` is fixed).
```
