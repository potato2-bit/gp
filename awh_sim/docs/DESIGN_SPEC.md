# AWH Simulation — Master Design Spec (Hybrid, multi-fidelity)

**System.** Solar-regenerated **silica-gel adsorption** atmospheric water harvester (AWH):
night/high-RH adsorption into a silica-gel packed bed → daytime solar regeneration →
ambient condensation → distilled water for autonomous PV-panel cleaning across several
Egyptian climate sites. **No thermoelectric stage.**

**Purpose of this document.** This is the authoritative Step-2 design. It defines the
**hybrid, multi-fidelity** simulation architecture and how the three engine tiers fit
together. Equation- and case-level detail lives in two appendices, which this spec
supersedes at the architecture level:

- **Appendix A** — [APPENDIX_A_CFD_SOLVER_PHYSICS.md](APPENDIX_A_CFD_SOLVER_PHYSICS.md):
  the OpenFOAM 2-D axisymmetric solver & physics (geometry/mesh, governing equations,
  custom solver, BCs/phase-switching, condensation model, numerics, properties, CFD V&V).
  *Reframed here as the **high-fidelity tier**, not the sole engine.*
- **Appendix B** — [APPENDIX_B_DOE_SURROGATE_CLIMATE_ECON.md](APPENDIX_B_DOE_SURROGATE_CLIMATE_ECON.md):
  DoE factors, sampling, surrogate, climate coupling, sites, economics/LCOW, repo, V&V.
  *Its DoE/surrogate sections are **upgraded to multi-fidelity** below; its climate,
  economics, site list, and repo sections stand as written.*

---

## 0. Locked decisions (recap)

| Decision | Value |
|---|---|
| Method | Solar-regenerated silica-gel desiccant AWH; no TEC |
| Model fidelity | 2-D/3-D CFD of the bed (per user); realised via a hybrid that keeps real CFD as the high-fidelity anchor |
| Engine | **Open-source, hybrid:** pyGAPS (isotherm) → CADET (fast column) → OpenFOAM (CFD), fused by multi-fidelity Kriging |
| Licensing | Zero — all tools free, run under WSL2 Ubuntu |
| Climate cases | Several Egyptian sites (6, Appendix B §6) |
| Location | `awh_sim/` inside the repo; run via WSL2 (cases on ext4 `~/`, not `/mnt/c`) |
| Outcomes | Per-site annual water yield, SEC, regeneration energy, LCOW + seasonal breakdown |

---

## 1. Architecture & data flow

Three engine tiers, each doing what it is best at, plus a surrogate that fuses the two
that produce the design responses.

```
                ┌─────────────────────────────────────────────────────────────┐
 VALIDATION     │  Hraiech 2025 isotherms (27/33/44 °C, 44–82% RH)             │
 DATA           │  LSBU/Yeboah 2021 packed-bed breakthrough (T, ω traces)      │
                └───────────────┬─────────────────────────────┬───────────────┘
                                │                             │
                                ▼                             │
   TIER 0   ┌──────────────────────────────┐                 │ (validate)
  pyGAPS    │ Fit GAB / Dubinin-Astakhov /  │                 │
 (isotherm) │ Tóth/Sips to silica-gel/water │                 │
            │ → q*(T,RH) params + isosteric │                 │
            │ heat ΔH_ads(loading)          │                 │
            └───────────────┬──────────────┘                 │
                            │ isotherm + ΔH_ads feed both engines
              ┌─────────────┴───────────────┐                │
              ▼                             ▼                 ▼
   TIER 1 (LOW-FI, cheap, many)     TIER 2 (HIGH-FI, expensive, few)
   ┌──────────────────────────┐    ┌──────────────────────────────────┐
   │ CADET column model        │   │ OpenFOAM 2-D axisymmetric CFD      │
   │ GRM/LRMP + LDF + Sips/Tóth│   │ (Appendix A): non-isothermal,      │
   │ cyclic; T(t) prescribed   │   │ spatially-resolved, isosteric-heat │
   │ from collector schedule   │   │ coupled, wall-flux solar regen     │
   │ → m_w, breakthrough, ω_out│   │ → m_w, Q_reg, SEC, T_peak, ω_out   │
   │ + lumped energy post-model│   │ (the thermal truth CADET lacks)    │
   │ ~10²–10³ runs (seconds ea)│   │ ~30–60 runs (min–hr ea) + 3-D ck.  │
   └────────────┬─────────────┘    └─────────────────┬────────────────┘
                │   nested DoE (high-fi ⊂ low-fi)     │
                └──────────────┬──────────────────────┘
                               ▼
              ┌──────────────────────────────────────┐
              │ MULTI-FIDELITY KRIGING (SMT MFK)      │
              │ co-kriging: fuse cheap CADET + few    │
              │ OpenFOAM → one fused GP per response  │
              │ (m_w, SEC, Q_reg, T_peak, ω_out)      │
              │ dP computed directly from Ergun       │
              └──────────────┬───────────────────────┘
                             ▼
        ┌────────────────────────────────────────────────────┐
        │ CLIMATE SWEEP (Appendix B §6)                       │
        │ hourly NASA POWER (T2M,RH2M,ALLSKY_SW,WS2M) × 6     │
        │ Egyptian sites → half-cycle aggregation →           │
        │ evaluate fused GP per cycle → annual integration     │
        └──────────────┬─────────────────────────────────────┘
                       ▼
        ┌────────────────────────────────────────────────────┐
        │ OUTCOMES: per-site annual yield, SEC, regen energy, │
        │ seasonal profile, and LCOW (Appendix B §7)          │
        └────────────────────────────────────────────────────┘
```

**Why this beats single-engine.** CADET removes the adsorption-coding risk for the
*mass* side (built-in isotherms + LDF + cyclic) and is fast enough to flood the DoE;
OpenFOAM supplies the *non-isothermal, spatially-resolved* truth (the isosteric-heat
feedback and wall-driven regeneration CADET cannot represent); multi-fidelity Kriging
fuses them so the annual sweep inherits CFD-grade accuracy at column-model cost. pyGAPS
guarantees a cited, defensible isotherm + isosteric heat feeding both.

---

## 2. Tier 0 — Isotherm & isosteric heat (pyGAPS)

**Role.** Single source of truth for the equilibrium loading law q*(T, RH) and the
isosteric heat ΔH_ads, consumed by both engines. Removes the "which constants?" ambiguity
flagged in Appendix A §2.6.

- **Input data:** Hraiech et al. 2025 (adsorption + desorption branches, 27/33/44 °C,
  44–82 % RH) and the LSBU/Yeboah 2021 packed-bed dataset.
- **Fits (pyGAPS built-ins):** GAB, Dubinin-Astakhov, Tóth, Langmuir-Freundlich (Sips),
  Freundlich. Fit each branch; report RMSE/R² per model; pick the best-fitting form that
  is **also expressible in CADET** (see Tier 1) — in practice **Sips/Tóth**.
- **Isosteric heat:** pyGAPS computes ΔH_ads(loading) by the Clausius-Clapeyron /
  Whittaker method across the isotherm family. Output a ΔH_ads(q) curve and a single
  representative value with an uncertainty band (Appendix A flags 2.2–2.8 MJ/kg).
- **Outputs (machine-readable):** `data/isotherm/params.yaml` (model, constants,
  T-dependence, ΔH_ads(q), fit quality). Both CADET binding params and the OpenFOAM
  `qStar`/`dHads` expressions are generated from this one file.
- **Gate G0:** chosen isotherm reproduces the Hraiech data within its published RMSE
  (~1.5 % adsorption); ΔH_ads within the literature band. No engine runs until G0 passes.

---

## 3. Tier 1 — CADET fast column engine (low-fidelity for the fusion)

**Role.** The primary, fast DoE engine for the *mass* responses, and the "many cheap
points" leg of the multi-fidelity surrogate. Built-in adsorption ⇒ near-zero custom code.

- **Framework:** **CADET-Process** (high-level Python; native cyclic/section handling,
  flow-sheet, parameter studies) on top of CADET-Core; `conda install -c conda-forge
  cadet` + `pip install cadet-process`.
- **Flow sheet:** `Inlet → Column → Outlet`. Single adsorbing component = water vapour in
  an inert air carrier (vapour concentration in the gas phase).
- **Unit model:** **Lumped-Rate-Model-with-Pores (LRMP)** for the DoE (fast, includes film
  + pore resistance); **General-Rate-Model (GRM)** for a few cross-checks against the LRMP
  and OpenFOAM. Both are CADET built-ins.
- **Binding model:** **Sips (Langmuir-Freundlich)** or **Tóth-family**, with `IS_KINETIC=1`
  and an **LDF** rate, parameters and T-dependence imported from Tier 0. (GAB/D-A are not
  native to CADET — Tier 0 picks a CADET-expressible form that matches the data.)
- **LDF coefficient:** k_LDF from the Chihara/Glueckauf closure (Appendix A §2.5),
  re-evaluated for the DoE's particle size (k_LDF ∝ 1/R_p²).
- **Thermal swing (the CADET limitation, handled explicitly):** released CADET-Core is
  **isothermal**. Emulate the cycle by **prescribing a temperature profile T(t)** —
  cool/ambient during adsorption, ramped to T_reg during desorption — via CADET's
  external-function parameter dependence (binding affinity/capacity as polynomial in T,
  from the Tier-0 multi-temperature fits). This captures the *equilibrium* shift with
  temperature but **not** the self-consistent isosteric-heat feedback or the spatial
  thermal front — that gap is exactly what Tier 2 supplies and what the MFK fusion
  corrects for.
- **Cyclic operation:** CADET-Process `Cycle`/sections run multiple ad/de cycles to
  cyclic steady state; one cycle = one adsorption section + one desorption section.
- **Responses produced:** water uptake/yield per cycle `m_w`, outlet breakthrough ω_out(t)
  (reduced to scalars per Appendix B §3), and a **lumped energy post-model** giving a
  cheap `Q_reg`/`SEC` estimate = sensible bed heating (∫(ρc_p)dT) + desorption enthalpy
  (ΔH_ads·Δq) + fan work (Ergun). These cheap thermal estimates are the **low-fi leg** for
  those responses; OpenFOAM is the high-fi truth.
- **Run budget:** seconds per case ⇒ the full low-fi DoE (10²–10³ cases) is minutes-to-an-
  hour. This is what makes a dense surrogate affordable.
- **Gate G1:** CADET reproduces the LSBU breakthrough curve (time within ±15 %, MTZ shape)
  using the Tier-0 isotherm + Chihara LDF, before it feeds the surrogate.

---

## 4. Tier 2 — OpenFOAM CFD (high-fidelity anchor)

**Role.** The spatially-resolved, **non-isothermal** truth: isosteric-heat coupling,
wall-flux solar regeneration, radial thermal front, and the responses CADET cannot
compute honestly (`Q_reg`, `SEC`, `T_peak`). Full detail in **Appendix A**.

- Engine, geometry, mesh, governing equations, custom `rhoReactingBuoyantFoam`-based
  solver, `fvOptions` sources, BCs, phase switching, condensation model, numerics,
  property table, and CFD V&V are all in Appendix A — unchanged, but now scoped as the
  **high-fidelity tier** rather than the only engine.
- **Run budget:** minutes–hours per 2-D axisymmetric case ⇒ only the **high-fi DoE subset
  (~30–60 cases)** plus the 2–3 full-3-D spot-checks (Appendix A §8.3). The high-fi points
  are a **nested subset** of the CADET low-fi DoE (same factor vectors) so co-kriging can
  pair them.
- **Cross-tier consistency:** OpenFOAM and CADET share the Tier-0 isotherm and the Chihara
  LDF, so any divergence between them is *physics* (thermal coupling, spatial gradients),
  not parameter mismatch — which is precisely the signal the MFK fusion learns.
- **Gate G2:** Appendix A gates V1–V4 + VA1–VA2 (box/mass balance, Ergun Δp, mesh & time
  independence, isotherm impl., breakthrough within ±15 %).

---

## 5. Multi-fidelity surrogate (SMT MFK)

Upgrades Appendix B §5 from single- to **multi-fidelity Kriging**.

- **Method:** **SMT `MFK`** (multi-fidelity / co-kriging). For each design response, fuse
  the dense low-fi CADET data with the sparse high-fi OpenFOAM data into **one fused GP**
  that predicts at high-fi accuracy across the whole box. Matérn-5/2 correlation, nugget,
  anisotropic length-scales, inputs scaled to the unit hypercube.
- **Per-response strategy:**
  | Response | Low-fi (CADET) | High-fi (OpenFOAM) | Surrogate |
  |---|---|---|---|
  | `m_w` water yield/cycle | ✓ (mass-accurate) | ✓ (thermally-coupled) | **MFK** |
  | ω_out breakthrough scalars | ✓ | ✓ | **MFK** |
  | `Q_reg` regen energy | ✓ (lumped post-model) | ✓ (CFD truth) | **MFK** |
  | `SEC` | ✓ (lumped) | ✓ | **MFK** |
  | `T_peak` | ✗ (isothermal) | ✓ | **single-fidelity GP (high-fi only)** |
  | `dP` pressure drop | — | — | **direct Ergun** (no surrogate) |
- **Why MFK, not just high-fi GP:** ~30–60 CFD points alone undertrain a 7-D GP; the
  hundreds of CADET points supply the global trend, the CFD points supply the correction.
  This is the standard variance-reduction argument for co-kriging.
- **Fallback:** if MFK cross-validation does not beat a high-fi-only GP (rare, but possible
  if the fidelities are poorly correlated for a response), drop to single-fidelity GP for
  that response and add high-fi adaptive points. Decide per response on the CV result.
- **Acceptance (Gate G3):** per response, on a held-out **high-fi** test set:
  R² ≥ 0.95, nRMSE ≤ 5 % of range; `T_peak` also max-abs-err ≤ 5 °C; 5-fold CV consistent;
  parity plots in `results/parity/`. Out-of-box clamping + posterior-variance flagging per
  Appendix B §5.

---

## 6. DoE design (multi-fidelity, nested)

Factors and ranges are **unchanged from Appendix B §1** (4 operating: T_ads, RH_ads,
T_reg, u_face; 3 design: L_bed, d_p, t_half). Sampling becomes nested:

- **Low-fi (CADET) DoE:** Sobol' block of **256–512** points over the 7-factor box (cheap,
  so sample generously; extensible).
- **High-fi (OpenFOAM) DoE:** a **nested subset of ~32–48** of the low-fi points
  (max-min / Sobol-subset so the high-fi set is space-filling *and* a strict subset of the
  low-fi set — required for co-kriging pairing) + a small independent **high-fi test set
  (~12–16)** for Gate G3.
- **Adaptive infill:** after the first MFK fit, add high-fi points where the **fused-GP
  posterior variance** is largest (ALM) — spend scarce CFD runs where they most reduce
  uncertainty. Add in batches of 6–8; re-validate.
- **Tools:** `scipy.stats.qmc.Sobol`, `SMT` sampling, `pyDOE3`; `SALib` for Sobol
  sensitivity indices to rank factor importance and possibly freeze weak design factors.

---

## 7. Climate coupling & sites — per Appendix B §6 (stands)

Unchanged by the hybrid: hourly **NASA POWER** (`T2M, RH2M, ALLSKY_SFC_SW_DWN, WS2M`,
+`PRECTOTCORR`) for **6 Egyptian sites** (Aswan/Benban, Mansoura, New Alamein, Hurghada,
Siwa, New Administrative Capital), half-cycle aggregation (cycle = integration unit),
collector relation for T_reg, per-cycle surrogate evaluation, annual + seasonal
integration, out-of-box clamping with per-site clamped-cycle audit. Reuses
`scripts/fetch_nasa_power.py` (+ irradiance/wind + site loop) and
`scripts/psychrometrics_hourly.py` (ω, dew point) directly.

---

## 8. Economics / LCOW — per Appendix B §7 (stands)

LCOW = (CRF·CAPEX + OPEX_annual)/Water_annual, CRF ≈ 0.1168 (i=0.08, n=15 from
`project_inputs.yaml`). CAPEX (sorbent, vessel, solar collector, fan, condenser, controls)
and OPEX (fan parasitic from dP, maintenance, periodic sorbent replacement). Sanity anchors
(verified): condensation AWH ≈ $0.17/L grid / $0.09/L on PV; sorbent-system $6.5–11/m³;
solar-desiccant energy 116–1021 kWh/m³; adsorption SEC anchor 1.16 kWh/kg.

---

## 9. Reproducible repo structure (`awh_sim/`, updated for hybrid)

```
awh_sim/
├── README.md
├── requirements.txt
├── awh_sim_config.yaml          # imports project_inputs.yaml; adds sites/doe/surrogate/collector/bed
├── isotherm/                    # TIER 0 (pyGAPS)
│   ├── fit_isotherm.py          # fit GAB/DA/Toth/Sips to Hraiech+LSBU; ΔH_ads
│   └── (-> data/isotherm/params.yaml)
├── cadet/                       # TIER 1 (CADET low-fi)
│   ├── build_column.py          # CADET-Process flow sheet, binding from params.yaml
│   ├── run_cadet_doe.py         # low-fi DoE batch (fast)
│   └── energy_postmodel.py      # lumped Q_reg/SEC estimate
├── cases/                       # TIER 2 (OpenFOAM high-fi)
│   ├── template/                # Jinja2 OpenFOAM skeleton (0/, constant/, system/)
│   └── run_XXXX/                # generated per high-fi DoE row (git-ignored)
├── solver/                      # custom OpenFOAM solver + fvOptions (Appendix A)
├── doe/
│   ├── doe_config.yaml          # sampler, seed, n_lowfi, n_highfi, n_test, bounds
│   ├── sample_doe.py            # nested Sobol' (high-fi ⊂ low-fi) + test set
│   ├── render_cases.py          # Jinja2 -> cases/run_XXXX/
│   ├── run_doe.sh               # WSL driver (blockMesh->solve->postProcess, GNU parallel)
│   └── extract_results.py       # CADET + OpenFOAM postProcessing -> data/*_responses.csv
├── surrogate/
│   ├── train_mfk.py             # SMT MFK per response (fuse low+high fi)
│   ├── validate.py              # parity, gates (R²>=0.95, nRMSE<=5%), MFK-vs-singleGP
│   └── models/                  # serialized fused GPs
├── climate/
│   ├── fetch_sites.py           # extends scripts/fetch_nasa_power.py (sites + irradiance/wind)
│   ├── aggregate_cycles.py      # hour->cycle (reuses psychrometrics_hourly.py)
│   └── run_annual.py            # surrogate over 8760 h x sites -> results/annual_*.csv
├── economics/
│   └── lcow.py                  # CRF, CAPEX/OPEX, LCOW vs anchors
├── data/
│   ├── isotherm/params.yaml
│   ├── doe_design.csv           # with a 'fidelity' column (lowfi/highfi/test)
│   ├── cadet_responses.csv
│   ├── openfoam_responses.csv
│   └── climate/                 # nasa_power_hourly_<site>.csv
├── results/{parity/, annual_<site>.csv, summary_lcow.csv}
├── docs/{DESIGN_SPEC.md (this), APPENDIX_A_*.md, APPENDIX_B_*.md}
└── tests/{test_aggregate_cycles.py, test_lcow.py, test_isotherm_fit.py, test_surrogate_clamp.py}
```

**`requirements.txt`** (Appendix B list **plus** the hybrid tools):
```
numpy>=1.26,<3
scipy>=1.11
pandas>=2.0
matplotlib>=3.8
pyyaml>=6.0
requests>=2.31
smt>=2.6              # KRG + MFK (multi-fidelity), matern52, LHS, EGO/ALM
scikit-learn>=1.4     # GP fallback + CV
pyDOE3>=1.0
SALib>=1.5
Jinja2>=3.1
pygaps>=4.0           # TIER 0 isotherm fitting + isosteric heat
cadet-process>=0.9    # TIER 1 (pulls CADET-Python; CADET-Core via conda)
# CADET-Core installed via: conda install -c conda-forge cadet
# OpenFOAM installed via apt (ESI openfoam.com) — TIER 2, not a pip dep
```
Pin to a lockfile (`pip freeze`) once the WSL env validates; SMT and CADET are the
version-sensitive pieces.

---

## 10. End-to-end V&V gates (5, in series)

| Gate | Tier | Criterion |
|---|---|---|
| **G0** Isotherm fit | 0 (pyGAPS) | chosen q*(T,RH) within Hraiech RMSE; ΔH_ads in literature band |
| **G1** CADET column | 1 (CADET) | reproduces LSBU breakthrough (t ±15 %, MTZ shape) with Tier-0 isotherm + Chihara LDF |
| **G2** CFD | 2 (OpenFOAM) | Appendix A V1–V4 + VA1–VA2 (mass balance <0.5 %, Ergun Δp <2 %, mesh GCI <3 %, dt <1 %, breakthrough ±15 %) |
| **G3** MFK surrogate | fusion | per response R²≥0.95, nRMSE≤5 % on held-out high-fi; T_peak max-err≤5 °C; MFK ≥ single-GP or fall back |
| **G4** Annual + LCOW sanity | climate/econ | SWP in silica-gel band (~0.1–0.4 L/kg/cycle); SEC within ~2× of 1.16 kWh/kg; LCOW below $0.17/L and near $6.5–11/m³; humid-coastal > arid-interior; clamped cycles <10 %/site |

---

## 11. Effort & timeline (hybrid vs pure OpenFOAM)

The hybrid **lowers risk and total time** versus pure OpenFOAM, because CADET carries the
mass-side DoE cheaply and the costly custom-solver work shrinks to a smaller high-fi set.

| Phase | Work | Est. |
|---|---|---|
| Tier 0 | pyGAPS isotherm fit + ΔH_ads, Gate G0 | ~3–5 days |
| Tier 1 | CADET column build + LSBU validation (G1) + low-fi DoE | ~1–1.5 weeks |
| Tier 2 | OpenFOAM custom solver + CFD V&V (G2) + ~40 high-fi runs + 3-D checks | ~4–6 weeks (dominant; Appendix A §9) |
| Fusion | MFK train/validate (G3), adaptive infill | ~1 week |
| Climate+econ | site fetch, aggregation, annual sweep, LCOW (G4) | ~1–1.5 weeks |
| **Total** | overlap Tier 0/1 with Tier 2 setup | **~7–9 weeks** |

The dominant cost and risk remains the **self-written OpenFOAM solver** (Appendix A §9
risk #4) — but it now needs to be right over ~40 anchor points, not the whole DoE.

---

## 12. Open items to confirm before/at build time

- **Bed geometry:** default = cylindrical packed bed (2-D axisymmetric). A flat tray bed
  would force 3-D and change the CFD tier scope.
- **Regeneration mode:** default = wall heat-flux (closed solar-thermal collector), per
  Appendix A §4.3 — keeps desorbed vapour undiluted for better condensation. Hot-air purge
  kept only as a comparison case.
- **Isotherm form in CADET:** Tier 0 picks the best CADET-expressible fit (Sips/Tóth);
  confirm it meets G0 before committing.
- **Compute:** ~40 transient 2-D CFD runs + 3-D checks need a workstation; budget WSL2 RAM
  in `.wslconfig`. Run cases on ext4 `~/`, sync results to the repo.
- **Coordinates/costs flagged unverified** in Appendix B (Alamein/Siwa/NAC centroids; $/kg
  & $/m² unit costs) to refine before production/thesis citation.
```
