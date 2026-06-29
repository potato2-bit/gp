# Solar-Regenerated Silica-Gel AWH — CFD Solver & Physics Design Spec

**Scope of this document.** This is the *solver and physics* half of the simulation
spec for a 2-D axisymmetric, solar-regenerated **silica-gel adsorption** atmospheric
water harvester (AWH). It defines geometry/mesh, governing equations, the OpenFOAM
implementation strategy, BCs and phase switching, the condensation/collection model,
numerics, properties, and a V&V plan. It does **not** design the DoE or the Kriging
surrogate — this CFD model is the high-fidelity training source those consume.

Engine: **OpenFOAM** (ESI `openfoam.com` v2306+ or Foundation `openfoam.org` v11),
run under **WSL2**. Geometry: **2-D axisymmetric wedge** packed bed, axial through-flow.

Units are SI throughout. Symbols are collected in the nomenclature at the end.

---

## 0. Physical picture and the one fact that drives the whole model

Cycle: **(night/high-RH) ADSORPTION** — humid ambient air is drawn axially through a
silica-gel packed bed; vapour adsorbs, releasing the isosteric heat of adsorption →
**(day) DESORPTION/REGENERATION** — solar heat raises the bed temperature, the
equilibrium loading collapses, vapour desorbs into a carrier-air stream →
**CONDENSATION** — the hot, vapour-rich desorption stream is cooled at an ambient
condenser below its dew point; the condensate is the harvested distilled water for
PV-panel cleaning.

The single most important modelling fact, and the one most often gotten wrong:
**desorbed vapour is not collected water.** Only the fraction of the desorbed vapour
whose partial pressure exceeds the saturation pressure at the *condenser* surface
temperature condenses. The CFD model produces the desorption-outlet vapour flow; a
separate (algebraic) condenser model converts that to litres. Section 5 makes this
explicit and quantitative.

---

## 1. Geometry & Mesh

### 1.1 The wedge approach (why, not just how)

OpenFOAM has no native 2-D axisymmetric mode. The standard idiom is a **wedge**: a
single-cell-thick slice spanning a small angle θ about the axis, with the two angled
faces declared as a `wedge` patch pair. OpenFOAM then treats the azimuthal direction
as zero-gradient and recovers true cylindrical-axisymmetric behaviour. This is the
correct choice for a packed bed with axial flow and no swirl: it captures the radial
gradients (wall heating during regeneration, wall channelling) at ~1/Nθ the cell
count of a full 3-D mesh.

Rules for a valid wedge (these are hard requirements; violating them gives a
non-runnable or wrong mesh):

- **Wedge half-angle θ ≤ 5°** total (i.e. ±2.5° about the x–z plane). Larger angles
  break the small-angle assumption OpenFOAM uses for the wedge transform.
- **Exactly one cell in the azimuthal direction.**
- The wedge **must be symmetric about and touch the axis**; the two `wedge` patches
  must be planar and on opposite sides of the centre-plane.
- The axis edge collapses to zero thickness — `blockMesh` handles this if the front
  and back vertices share the axis coordinates. Cells at the axis are prisms, not hexes.
- Patch types: angled faces → `wedge`; the single-cell front/back are *not* separate
  patches (they are the wedge pair). If instead you build a *symmetry slice* with finite
  thickness you would use `empty`, but for true axisymmetry use `wedge`. **Use `wedge`.**

Axis x = axial (flow) direction; r = radial. Inlet at x = 0, outlet at x = L.

### 1.2 Parametrisation

Bed length L ∈ [30, 150] mm (axial), bed diameter D ∈ [100, 400] mm → radius
R = D/2 ∈ [50, 200] mm. Drive both from a small `m4`/`#calc` header in `blockMeshDict`
so the DoE can regenerate the mesh per design point:

```
// blockMeshDict header (OpenFOAM #calc style)
L   1   #calc "0.030";          // [m]  bed length, 0.030–0.150
R   1   #calc "0.050";          // [m]  bed radius, 0.050–0.200
theta   1   #calc "2.5";        // [deg] wedge half-angle
rad     #calc "degToRad($theta)";
y       #calc "$R*sin($rad)";   // +y face coordinate at outer radius
z       #calc "$R*cos($rad)";   // (front/back split about x–z plane)
```

Vertices: 4 on the axis (y=z=0) at x∈{0,L}, doubled into the ±θ front/back set at
the outer radius (±y, z). One block, graded radially toward the wall.

### 1.3 Baseline cell counts and grading

Drivers of resolution: (i) the **mass-transfer / thermal front** that sweeps axially
during a breakthrough — needs enough axial cells to resolve the moving front, and
(ii) the **near-wall radial gradient** during solar regeneration (heat enters from the
wall). The packed bed is treated as a continuum porous medium, so we are **not**
resolving individual pellets — cell size is set by gradient resolution, not by d_p.

Baseline (for L = 90 mm, R = 100 mm midpoint design):

| Direction | Cells | Grading | Rationale |
|---|---|---|---|
| Axial (x) | **120** | uniform | resolve the axial concentration/temperature front; target ≥ 20–30 cells across the front thickness |
| Radial (r) | **30** | expansion ratio ~3 toward wall (finer at wall) | capture wall heat-flux boundary layer during regeneration |
| Azimuthal | **1** | — | wedge requirement |

≈ 3,600 cells. This is small; a transient run is cheap, so bias toward more axial
cells. For the DoE, scale axial cells with L to keep Δx roughly constant
(Δx ≈ 0.75 mm), and radial cells with R (keep Δr_wall ≈ 0.5 mm).

### 1.4 Grid-independence procedure

1. Pick the **most demanding DoE corner** for the grid study: shortest bed (30 mm) +
   highest face velocity (1.0 m/s) → steepest, fastest-moving front. Grid-independence
   proven there is conservative for the rest.
2. Three meshes, refining by ~√2 in each in-plane direction:
   coarse (85×21), baseline (120×30), fine (170×42).
3. Monitor scalar QoIs, not field snapshots: **(a)** breakthrough time t_50 (time for
   outlet humidity to reach 50% of inlet), **(b)** cycle-integrated adsorbed mass,
   **(c)** peak bed temperature during adsorption, **(d)** desorption-outlet
   cumulative vapour mass.
4. Report **Grid Convergence Index (GCI)** (Roache) using the three meshes; accept the
   baseline when GCI_fine→baseline < 3% on all four QoIs and the observed order p is in
   a sane range (1 ≲ p ≲ 2 for the upwind-blended schemes here).
5. Repeat the *time-step* study independently (Section 6.4) — mesh and dt independence
   are separate gates.

---

## 2. Governing Equations

Volume-averaged (Darcy-scale) continuum equations over the porous bed. ε is the
**inter-particle bed voidage** (superficial/Darcy formulation: velocity **u** is the
superficial velocity, ρ is the gas density, fluxes use the full face area). Subscripts:
g = gas (humid air), s = solid (silica gel + adsorbed water).

### 2.1 Continuity (humid air in the porous bed)

$$
\frac{\partial (\varepsilon \rho_g)}{\partial t} + \nabla\!\cdot(\rho_g \mathbf{u})
= \dot{S}_m
$$

- ρ_g [kg m⁻³] gas density, **u** [m s⁻¹] superficial velocity, ε [–] voidage.
- $\dot{S}_m$ [kg m⁻³ s⁻¹] is the mass the gas phase loses to (adsorption) or gains
  from (desorption) the solid:
  $$\dot{S}_m = -(1-\varepsilon)\,\rho_s\,\frac{\partial \bar{q}}{\partial t}$$
  with ρ_s the silica-gel particle (skeletal-apparent) density and $\bar q$ the bed-
  average loading [kg water / kg dry gel]. During adsorption $\partial\bar q/\partial t>0$
  so $\dot S_m<0$ (gas loses vapour). This source couples continuity, species, and energy.

In practice the gas-phase mass change is small relative to the convective flux at these
velocities, but keep it: it is what closes the water balance and what the collection
model integrates.

### 2.2 Momentum — Darcy–Forchheimer (Ergun) porous resistance

$$
\frac{\partial(\rho_g \mathbf{u})}{\partial t}
+ \nabla\!\cdot\!\left(\frac{\rho_g}{\varepsilon}\,\mathbf{u}\mathbf{u}\right)
= -\nabla p + \nabla\!\cdot\boldsymbol{\tau}
\;-\; \underbrace{\left(\mu\, d\,\mathbf{u} + \tfrac{1}{2}\rho_g\, f\,|\mathbf{u}|\,\mathbf{u}\right)}_{\text{Darcy–Forchheimer sink}}
$$

OpenFOAM's `DarcyForchheimer` porosity model writes the sink as
$\mathbf{S} = -(\mu\,d + \tfrac{1}{2}\rho |\mathbf{u}| f)\,\mathbf{u}$, i.e. **d** is the
viscous (Darcy) coefficient [m⁻²] and **f** the inertial (Forchheimer) coefficient
[m⁻¹]. Mapping the **Ergun equation** onto these:

$$
\boxed{\,d = \dfrac{150\,(1-\varepsilon)^2}{\varepsilon^{3}\,d_p^{2}}\;[\text{m}^{-2}]
\qquad
f = \dfrac{3.5\,(1-\varepsilon)}{\varepsilon^{3}\,d_p}\;[\text{m}^{-1}]\,}
$$

Derivation note on the factor 3.5: Ergun's inertial constant is 1.75 in
$\Delta p/L = 150\frac{(1-\varepsilon)^2}{\varepsilon^3}\frac{\mu u}{d_p^2}
+ 1.75\frac{(1-\varepsilon)}{\varepsilon^3}\frac{\rho u^2}{d_p}$.
Because OpenFOAM's Forchheimer term carries an explicit **½**, the dictionary value is
**f = 2 × 1.75 = 3.5** times the geometric group, i.e. the 3.5 above already absorbs the
½. (This factor-of-two is the single most common porosity-coefficient error — verify by
checking that your computed Δp matches a hand Ergun calculation at one velocity.)

Worked sanity check (d_p = 2 mm, ε = 0.4): d = 150·0.36/(0.064·4e-6) =
**3.16×10⁸ m⁻²**; f = 3.5·0.6/(0.064·0.002) = **1.64×10⁴ m⁻¹**. At u = 0.5 m/s,
air (μ=1.8e-5, ρ=1.2): viscous Δp/L = μ·d·u = 2.85 kPa/m; inertial = ½ρ f u² = 2.95
kPa/m → ~5.8 kPa/m total, ~0.5 kPa over a 90 mm bed. Reasonable for fine gel.

### 2.3 Water-vapour species transport

Transport the vapour **mass fraction** Y [kg vapour / kg humid air] (numerically
better-behaved across phase switching than concentration, and native to the reacting
solvers):

$$
\frac{\partial(\varepsilon \rho_g Y)}{\partial t}
+ \nabla\!\cdot(\rho_g \mathbf{u}\,Y)
= \nabla\!\cdot\!\big(\rho_g D_\text{eff}\,\nabla Y\big)
\;\underbrace{-\,(1-\varepsilon)\,\rho_s\,\frac{\partial \bar q}{\partial t}}_{\text{adsorption sink }\dot S_Y}
$$

- $D_\text{eff}$ [m² s⁻¹] effective axial dispersion = molecular diffusion / tortuosity
  + mechanical dispersion: $D_\text{eff} = D_m/\tau + 0.5\,d_p\,|\mathbf u|/\varepsilon$
  (a standard packed-bed dispersion closure; τ ≈ 1.4–2 for random spheres). $D_m$(H₂O–air)
  ≈ 2.6×10⁻⁵ m² s⁻¹ at 300 K.
- The sink term is **identical in magnitude** to $\dot S_m$ in continuity — because the
  adsorbed/desorbed mass is entirely water vapour. This consistency is mandatory; if you
  implement them separately, assert they share one computed `mDotAds` field.

### 2.4 Energy — LTE vs LTNE (decision and justification)

**Decision: use LTE (single-temperature, local thermal equilibrium) as the baseline;
keep LTNE as a documented validation spot-check, not the production model.**

Justification for a silica-gel bed at face velocities 0.1–1.0 m/s:

- The relevant criterion is whether the interstitial gas and the pellets stay near the
  same temperature. The fluid–solid heat-transfer time constant is short relative to
  the **thermal-front residence time** here: gas residence time over a 90 mm bed at
  0.1–1.0 m/s is 0.09–0.9 s, but the *thermal* front moves far slower than the gas
  because the solid heat capacity per bed volume, $(1-\varepsilon)\rho_s c_{p,s}$
  (~0.6·1100·920 ≈ 6×10⁵ J m⁻³ K⁻¹), hugely exceeds the gas’s
  $\varepsilon\rho_g c_{p,g}$ (~0.4·1.1·1006 ≈ 4.4×10² J m⁻³ K⁻¹). The gas equilibrates
  to the local solid temperature within a few particle diameters.
- Pellet Biot number for intraparticle conduction is small (k_s ≈ 0.2 W m⁻¹K⁻¹,
  d_p ~2 mm, gas-side h ~ tens of W m⁻²K⁻¹ → Bi ≲ 0.1), so intra-pellet temperature
  gradients are minor and a lumped pellet temperature is defensible.
- LTNE matters mainly at high velocity / large pellets / strongly transient pulsed
  heating. Our regime sits at the LTE-valid end except possibly the (1.0 m/s, 4–5 mm
  pellet) corner — that is exactly where the LTNE spot-check earns its keep.

**LTE energy equation** (one temperature T for gas+solid):

$$
\frac{\partial}{\partial t}\big[(\rho c_p)_\text{eff}\,T\big]
+ \nabla\!\cdot(\rho_g c_{p,g}\,\mathbf{u}\,T)
= \nabla\!\cdot(k_\text{eff}\nabla T)
\;+\; \underbrace{(1-\varepsilon)\,\rho_s\,\Delta H_\text{ads}\,\frac{\partial \bar q}{\partial t}}_{\text{heat of adsorption source }\dot S_T}
$$

with the effective volumetric heat capacity and conductivity
$$(\rho c_p)_\text{eff} = \varepsilon\rho_g c_{p,g} + (1-\varepsilon)\rho_s\big(c_{p,s} + \bar q\, c_{p,\text{w,ads}}\big),$$
$$k_\text{eff} = \varepsilon k_g + (1-\varepsilon)k_s \;(+\,\text{dispersion } \rho_g c_{p,g} D_\text{eff,th}).$$

- $\Delta H_\text{ads}$ [J kg⁻¹] = **isosteric heat of adsorption** (positive, exothermic).
  During adsorption $\partial\bar q/\partial t>0$ → source heats the bed; during
  desorption it is a sink (cooling), which is physically why regeneration needs solar
  heat input.
- $c_{p,\text{w,ads}}$ is the specific heat of the adsorbed water (~4180 J kg⁻¹K⁻¹);
  including it in $(\rho c_p)_\text{eff}$ is second-order but cheap.

**LTNE (two-temperature) form, for the spot-check only:**

$$
\varepsilon(\rho c_p)_g\Big(\tfrac{\partial T_g}{\partial t}+\tfrac{1}{\varepsilon}\mathbf u\!\cdot\!\nabla T_g\Big)
=\nabla\!\cdot(k_{g,\text{eff}}\nabla T_g)+h_{sf}a_{sf}(T_s-T_g)
$$
$$
(1-\varepsilon)(\rho c_p)_s\tfrac{\partial T_s}{\partial t}
=\nabla\!\cdot(k_{s,\text{eff}}\nabla T_s)+h_{sf}a_{sf}(T_g-T_s)+(1-\varepsilon)\rho_s\Delta H_\text{ads}\tfrac{\partial\bar q}{\partial t}
$$
with interfacial area $a_{sf}=6(1-\varepsilon)/d_p$ and $h_{sf}$ from a packed-bed Nu
correlation (e.g. Wakao: $Nu = 2 + 1.1\,Re_p^{0.6}Pr^{1/3}$). The heat of adsorption is
released **into the solid** phase in LTNE.

### 2.5 Adsorption kinetics — Linear Driving Force (LDF)

$$
\boxed{\;\frac{\partial \bar q}{\partial t} = k_\text{LDF}\,\big(q^{*}(T,\text{RH}) - \bar q\big)\;}
$$

- $\bar q$ [kg/kg] current bed-average loading, $q^*$ [kg/kg] equilibrium loading at the
  local T and vapour partial pressure (Section 2.6).
- $k_\text{LDF}$ [s⁻¹] from the surface-diffusion LDF closure (Glueckauf form, with the
  silica-gel/water constants of **Chihara & Suzuki 1983**, as used by Sakoda & Suzuki
  and ubiquitously since):
  $$
  k_\text{LDF} = \frac{F_0\,D_s}{R_p^{2}},\qquad F_0 = 15,\qquad
  D_s = D_{s0}\exp\!\Big(-\frac{E_a}{R\,T}\Big),
  $$
  $$
  D_{s0} = 2.54\times10^{-4}\ \text{m}^2\,\text{s}^{-1},\quad
  E_a = 4.2\times10^{4}\ \text{J mol}^{-1},\quad
  R_p = 1.7\times10^{-4}\ \text{m (verify/replace with your gel’s }R_p).
  $$
  Worked value at T = 300 K: D_s = 2.54e-4·exp(−42000/(8.314·300)) = 2.54e-4·5.0e-8 ≈
  **1.27×10⁻¹¹ m² s⁻¹** → k_LDF = 15·1.27e-11/(1.7e-4)² ≈ **6.6×10⁻³ s⁻¹**
  (time constant ~150 s). At a desorption temperature of 350 K, D_s rises ~9× → k_LDF
  ≈ 6×10⁻² s⁻¹ — kinetics speed up sharply with the regeneration heat, as expected.
  **Critically, R_p scales k_LDF as 1/R_p²: re-evaluate for your actual pellet size**
  (the Chihara R_p above is a fine RD-gel value; a 2 mm pellet has R_p = 1 mm and is
  ~35× slower).

### 2.6 Isotherm q*(T, RH) — recommendation and constants

Two defensible choices; recommend **based on what you will validate against**:

**(A) Recommended for this project — temperature-explicit empirical correlation
(Hraiech et al. 2025), because the geometry, conditions, and gel match the named
validation dataset (300 mm bed, 27–44 °C, 44–82 % RH):**

$$
q^{*}(T,\varphi)=0.1049\,\varphi^{0.5432}-0.00156\,(T-25)\,\varphi+8.91\times10^{-5}(T-25)^2
$$
with φ = RH (decimal 0–1), T in **°C**, q* in kg/kg (adsorption branch;
RMSE 1.5 %, R² 0.99). A separate desorption branch (hysteresis) is given:
$q^*=0.0987\varphi^{0.5891}-0.00203(T-25)\varphi+7.56\times10^{-5}(T-25)^2$. Using the
matching branch per phase captures the measured hysteresis.

**(B) Recommended if you need thermodynamic consistency / wide-pressure extrapolation —
Tóth isotherm (Chua/Chakraborty/Ng, RD silica gel):**

$$
q^{*}=\frac{q_m\,K_0\,e^{Q_{st}/RT}\,P_v}{\big[1+(K_0 e^{Q_{st}/RT}P_v)^{t}\big]^{1/t}}
$$
with literature RD-gel values $q_m\approx0.4$ kg/kg, $t\approx0.8$ (heterogeneity
exponent), and the equilibrium constant/heat term fitted so that the **isosteric heat
$Q_{st}\approx2800$ kJ/kg** (Chakraborty et al. 2009, Tóth fit). P_v is the vapour
partial pressure [Pa], related to RH by $P_v=\varphi\,P_\text{sat}(T)$ with Antoine/
Arden-Buck for $P_\text{sat}$.

> Honesty flag on constants: the **functional forms and the headline numbers I have
> verified** ($q_m\!\approx\!0.4$, $t\!\approx\!0.8$, $Q_{st}=2800$ kJ/kg). The exact
> $K_0$ for the Tóth fit and the precise $R_p$ for *your* gel batch are paper/batch
> specific — pull $K_0$ from the original Chua et al. 2002 table and re-fit $R_p$ from
> your supplier datasheet before production runs. The Hraiech (A) correlation is fully
> specified and is the safer default here.

GAB vs D-A vs the above: GAB is excellent for the 0–0.9 RH range of food/desiccant work
but its three constants (q_m, C, K) are themselves T-dependent and you would have to fit
their Arrhenius dependence yourself; **D-A** is strong for microporous filling but
silica gel’s isotherm is better matched by Tóth in the cooling/desalination literature.
For a graduate timeline, prefer the **ready, T-explicit (A)** form and reserve GAB/D-A
as alternates only if validation demands it.

---

## 3. OpenFOAM Implementation Strategy — the crux

### 3.1 Recommendation: **custom solver from `rhoReactingBuoyantFoam`, NOT `adsorpFoam`**

Rationale (graduate timeline, solo, must validate the result):

- **`adsorpFoam` (Gößnitzer, TU Wien 2016)** is a real multicomponent adsorption solver
  with equilibrium (Extended Langmuir, IAST) and diffusion-based kinetics. But: it is a
  decade-old thesis code, tied to an old OpenFOAM version, multicomponent/IAST machinery
  you do not need (you have one adsorbate: water), and porting + understanding + revalidating
  someone else’s solver on a current OpenFOAM is often *slower* than building a focused one.
  Treat it as a **reference for term-by-term implementation and a cross-check**, not the
  production base.
- **`rhoReactingBuoyantFoam`** already gives you, for free, exactly the hard parts:
  compressible humid-gas thermodynamics, a transported species mass-fraction equation
  (Y), the energy equation with buoyancy, and PIMPLE pressure–velocity coupling. It is a
  single-region solver (good — LTE is single-region) with full `fvOptions` support. You
  add adsorption as **source terms on Y and h, plus a porosity source on U** — most of
  which can be done *without editing the solver* via coded `fvOptions`. This is the
  lowest-risk path to a defensible, validated result.
- Reserve **`chtMultiRegionFoam`** only if you commit to LTNE (separate solid region) or
  to resolving solar heat conducted through a real bed wall as a coupled solid — overkill
  for the baseline.

So: **start from `rhoReactingBuoyantFoam`, drive adsorption through `fvOptions`, and
edit the solver only for the loading-field PDE** ($\bar q$) which has no natural home in
a stock solver.

### 3.2 What goes where

| Physics term | Mechanism | Edits solver? |
|---|---|---|
| (d) Darcy–Forchheimer porosity on **U** | `explicitPorositySource` (DarcyForchheimer) in `fvOptions`, restricted to the bed cellZone | No |
| The loading field $\bar q$ and its PDE $\partial\bar q/\partial t=k_\text{LDF}(q^*-\bar q)$ | **Add to solver**: declare `volScalarField q`, solve a tiny explicit/implicit ODE-per-cell each step; also compute `qStar`, `kLDF`, and `mDotAds = (1-eps)*rhoS*dqdt` | **Yes** (cleanest) |
| (b) species sink/source on **Y**: $-(1-\varepsilon)\rho_s\,\partial\bar q/\partial t$ | `coded` (or `semiImplicit`) source in `fvOptions` reading `mDotAds` — or add `fvm::Sp/Su` directly in YEqn | Either |
| (a) the LDF rate itself | computed alongside $\bar q$ (solver) and reused by all sources | Yes (with q) |
| (c) energy source $\Delta H_\text{ads}\cdot$rate | `coded` source in `fvOptions` on `h`/`e`, = `dHads*mDotAds` | No (preferred) |
| Continuity mass source $\dot S_m$ | same `mDotAds`; add as `fvOptions` mass source or fold into the rho/p step | depends on solver version |

Why $\bar q$ lives in the solver, not `fvOptions`: every source above depends on the
**same** `mDotAds = (1-eps)*rhoS*dqdt`, and `dqdt` depends on `qStar(T,Y)` and on the
*previous* q. Computing it once in the solver and exposing q, qStar, kLDF, mDotAds as
registered fields lets the `fvOptions` `codedSource`s simply look them up — no
double-evaluation, guaranteed sign/magnitude consistency between the Y, h and continuity
sinks (the consistency requirement from §2.3).

### 3.3 Solver-side additions (sketch)

In `createFields.H` add registered fields `q`, `qStar`, `kLDF`, `mDotAds`. After the
energy/transport solve each PIMPLE iteration, update them:

```cpp
// --- adsorption update (LTE, water on silica gel) ---
forAll(q, c)
{
    scalar Tc  = T[c];                       // K
    scalar phi = relHum(Y[c], p[c], Tc);     // local RH from Y, p, T (psat helper)
    scalar qs  = qStarHraiech(Tc, phi);      // §2.6(A), T in degC inside
    scalar Ds  = Ds0*Foam::exp(-Ea/(Rgas*Tc));
    scalar kL  = 15.0*Ds/sqr(Rp);            // k_LDF [1/s]
    scalar dq  = kL*(qs - q[c]);             // dq/dt [1/s]
    qStar[c] = qs;  kLDF[c] = kL;
    q[c]    += runTime.deltaTValue()*dq;     // explicit; or implicit, see §9
    mDotAds[c] = (1.0 - eps)*rhoS*dq;        // [kg/m3/s] >0 adsorb
}
```

Then either add to `YEqn.H` / `EEqn.H` directly, or expose `mDotAds` and let `fvOptions`
apply it (next section).

### 3.4 Concrete `fvOptions` snippets

**LDF species sink + isosteric-heat source via `codedSource`** (these read the
solver-registered `mDotAds`; `selectionMode cellZone bed` confines them to the packed
region):

```cpp
// constant/fvOptions

adsorptionSpeciesSink
{
    type            scalarCodedSource;
    selectionMode   cellZone;
    cellZone        bed;
    fields          (H2O);            // the vapour mass-fraction field
    name            adsSpeciesSink;
    codeAddSup
    #{
        const volScalarField& mDot =
            mesh().lookupObject<volScalarField>("mDotAds"); // kg/m3/s
        // YEqn is per unit mass; source on (rho*Y): -mDot  (adsorb removes vapour)
        eqn -= mDot;                   // [kg/m3/s], sign: adsorption depletes Y
    #};
}

adsorptionHeatSource
{
    type            scalarCodedSource;
    selectionMode   cellZone;
    cellZone        bed;
    fields          (h);              // sensible enthalpy (or e); match your thermo
    name            adsHeatSrc;
    codeAddSup
    #{
        const volScalarField& mDot =
            mesh().lookupObject<volScalarField>("mDotAds"); // kg/m3/s
        const scalar dHads = 2.8e6;    // J/kg, isosteric heat (Chakraborty 2009)
        eqn += dHads*mDot;             // adsorption (mDot>0) heats; desorption cools
    #};
}
```

**Darcy–Forchheimer porosity via `explicitPorositySource`:**

```cpp
bedPorosity
{
    type            explicitPorositySource;
    selectionMode   cellZone;
    cellZone        bed;
    explicitPorositySourceCoeffs
    {
        type        DarcyForchheimer;
        DarcyForchheimerCoeffs
        {
            d   (3.16e8 3.16e8 3.16e8);   // [1/m2] from Ergun, §2.2
            f   (1.64e4 1.64e4 1.64e4);   // [1/m]
            coordinateSystem
            {
                origin  (0 0 0);
                e1      (1 0 0);          // axial
                e2      (0 1 0);
            }
        }
    }
}
```

> Sign discipline: OpenFOAM `codedSource` sign conventions differ between solver
> versions and between `eqn += S` (explicit) vs `Su/Sp` split. **Verify signs with a
> zero-flow box test** (§8): seed a uniform humid cell zone, no inlet flow, and confirm
> Y *drops* and T *rises* during a simulated adsorption step, and the reverse when q* is
> forced low (desorption). Do this before trusting any breakthrough curve.

---

## 4. Boundary & Initial Conditions, and Phase Switching

### 4.1 Patches

- **inlet** (x=0): velocity `flowRateInletVelocity` or fixed superficial U; `Y` =
  inlet humidity; `T` = inlet air temperature; `p` zeroGradient.
- **outlet** (x=L): `pressureInletOutletVelocity`/`inletOutlet` on U and Y, fixed p
  (ambient), `inletOutlet` T.
- **wall** (outer radius): no-slip U; **T** = the regeneration boundary (see §4.3);
  Y zeroGradient (impermeable).
- **wedge** patches: `wedge` type, no values.
- **axis**: handled by wedge collapse (empty/symmetry implicit).

### 4.2 Initial conditions, both phases

| Field | Adsorption start | Desorption start |
|---|---|---|
| T | ambient night T (e.g. 295 K) | = bed state at end of adsorption |
| Y | ambient (high RH) | = end-of-adsorption field |
| q (loading) | low/“regenerated” (≈ residual after last desorption) | **high** (≈ saturated from adsorption) |
| U, p | quiescent → ramp inlet | quiescent → ramp purge/buoyant flow |

The clean way is **two chained cases**: run adsorption to a stop time, `mapFields` (or
just continue the same case directory) so the desorption case **inherits the final
q, T, Y fields** as its initial condition. This is more robust than one continuous run.

### 4.3 Imposing solar regeneration — recommendation

Two physical options; the system is specified as **"solar-regenerated"**, so:

**Recommended: heated bed wall heat flux (closed-bed / indirect solar collector).**
Impose a time-varying **wall heat flux** q''_wall [W m⁻²] (or wall T) on the outer-radius
patch, representing a solar thermal collector / absorber jacket conducting heat into the
bed. Use `externalWallHeatFluxTemperature` (flux or h+T_ambient mode) or a
`codedFixedValue` ramping with the solar day. This matches "solar-regenerated," produces
the radial wall→core thermal gradient that motivates the radial mesh refinement, and
keeps the desorbed vapour **undiluted** (higher partial pressure → easier condensation,
more water). It does require a low carrier-air flow to sweep desorbed vapour to the
condenser.

*Alternative (model, don’t recommend as primary): hot-air purge inlet* — feed hot, dry
air at the inlet during desorption (`fixedValue` high-T, low-Y at inlet). Simpler to
impose, but it **dilutes** the desorbed vapour, lowering the condenser dew point and the
water yield, and it is "solar-heated-air" rather than the closed solar-thermal concept.
Keep it as a comparison case only.

### 4.4 Phase-switch mechanism in OpenFOAM

Three viable mechanisms, in increasing flexibility:

1. **Two cases (recommended for clarity + validation):** separate `adsorption/` and
   `desorption/` case dirs; chain via field mapping (§4.2). Each has static BCs. Easiest
   to debug, easiest to validate each branch independently.
2. **`timeVaryingMappedFixedValue` / `uniformFixedValue` with a table:** one case; inlet
   T, Y, U and wall flux are driven by time tables that step at the switch time. Good for
   running full diurnal cycles in one job.
3. **`codedFixedValue` BCs** keyed on `this->db().time().value()`: full programmatic
   control (e.g. switch the isotherm branch and the wall flux at t_switch). Most
   flexible, most error-prone.

For the DoE training runs (single-phase response per design point) use **(1)**. For a
small number of full-cycle validation runs use **(2)** or **(3)**. Also switch the
**isotherm branch** (adsorption vs desorption, §2.6A hysteresis) with the phase.

---

## 5. Condensation / Collection Model (desorbed vapour ≠ collected water)

The CFD model gives the **desorption-outlet vapour mass flow**
$\dot m_{v,\text{out}}(t) = \big(\rho_g\,u_x\,Y\,A\big)\big|_{x=L}$ [kg s⁻¹] (integrate
over the outlet patch; multiply the wedge result by $2\pi/\theta_\text{rad}$ to recover
the full annulus). The **harvested water** is what an ambient condenser pulls out of
this stream — a *post-processing* (algebraic) step, not part of the CFD PDEs:

1. The outlet stream has humidity ratio $\omega_\text{out}=Y/(1-Y)$
   [kg water/kg dry air] and dry-air flow $\dot m_{da}$.
2. The condenser cools it to surface temperature $T_c$ (ambient or sub-ambient). Exit
   humidity ratio is capped at saturation at $T_c$:
   $\omega_\text{sat}(T_c)=0.622\,P_\text{sat}(T_c)/(P-P_\text{sat}(T_c))$.
3. **Condensate rate**
   $$\dot m_\text{water}(t)=\dot m_{da}\,\max\!\big[0,\;\omega_\text{out}(t)-\omega_\text{sat}(T_c)\big]\,\eta_c,$$
   with $\eta_c$ a condenser effectiveness (<1; not all super-saturation is captured).
4. **Harvested volume** $V=\frac{1}{\rho_w}\int_\text{desorption}\dot m_\text{water}\,dt$.

Key consequences to state in the spec: (i) if $\omega_\text{out}\le\omega_\text{sat}(T_c)$
**no water is collected** regardless of how much desorbs — the dew point must clear the
condenser temperature; (ii) the **wall-flux regeneration** (§4.3) beats hot-air purge
precisely because it keeps $\omega_\text{out}$ high; (iii) report both *desorbed* and
*collected* masses — they differ, and conflating them is the classic AWH over-estimate.

$P_\text{sat}(T)$: use Arden-Buck or Antoine — e.g. Buck:
$P_\text{sat}=611.21\exp[(18.678-T_C/234.5)\,(T_C/(257.14+T_C))]$ Pa, $T_C$ in °C.

---

## 6. Numerical Setup

### 6.1 `fvSchemes`

- `ddtSchemes`: `Euler` (bounded, robust for the stiff sources) — or `backward` /
  `CrankNicolson 0.5` once stable, for time accuracy in the validation runs.
- `gradSchemes`: `Gauss linear`; `limited` (cellLimited Gauss linear 1) on gradients
  feeding the source terms to keep them bounded on the wedge.
- `divSchemes`: convection on **U** `Gauss linearUpwindV grad(U)`; on **Y** and **h**
  `Gauss limitedLinear 1` (bounded, near-2nd-order) — Y must stay in [0,1], so a
  **bounded** scheme is non-negotiable. Fall back to `Gauss upwind` for the first
  transient if you see wiggles, then tighten.
- `laplacianSchemes`: `Gauss linear corrected` (or `limited corrected 0.5` on skewed
  near-axis cells).
- `interpolationSchemes`: `linear`. `snGradSchemes`: `corrected`.

### 6.2 `fvSolution`

- `p` / `p_rgh`: `GAMG`, `smoother GaussSeidel`, tol 1e-7, relTol 0.01 (0 on final).
- `U`, `Yi`, `h`, `e`: `PBiCGStab`/`smoothSolver` (symGaussSeidel), tol 1e-8, relTol 0.05.
- `q` (loading), if solved as a field: trivial — `diagonal` or local update.

### 6.3 PIMPLE

- `nOuterCorrectors` 2–3 (transient, with sources → outer correctors help couple the
  source updates to the fields), `nCorrectors` 2, `nNonOrthogonalCorrectors` 1.
- Under-relaxation on fields and especially on the **source** (relax `q`/`mDotAds`
  update, e.g. 0.5–0.7) if the phase-switch transient rings.
- `momentumPredictor yes`.

### 6.4 Time stepping

- `adjustTimeStep yes`; **maxCo 0.5** (convective). But the limiter here is often the
  **source time constant**, not Courant: ensure $\Delta t \lesssim 0.2/k_\text{LDF}$
  (~30 s at 300 K, ~3 s at 350 K desorption) — so cap `maxDeltaT` accordingly, or treat
  the LDF update implicitly (§9) to relax this.
- Tolerances/convergence: residual floor 1e-6 on U/p, 1e-7 on Y/h; for steady-per-phase
  DoE points, run to QoI stationarity (outlet Y and integrated mass flat to <0.1 %/min).

---

## 7. Material & Model Properties Table

| Property | Symbol | Value | Units | Source / note |
|---|---|---|---|---|
| Silica-gel particle density | ρ_s | **750** (bulk/“apparent” Fluka Rubin) | kg m⁻³ | Hraiech 2025 (bulk 750 g/L). Skeletal SiO₂ ~2.2–2.6 g/cm³ (LSBU) — use bulk in $(1-\varepsilon)\rho_s$ |
| Bed bulk density | ρ_b | ~750 | kg m⁻³ | = (1−ε)ρ_s,skeletal; consistent with above |
| Bed porosity (inter-particle) | ε | **0.35–0.40** (use 0.38) | – | LSBU/Hraiech; verify per packing |
| Particle diameter | d_p | **2.0** (range 0.5–5) | mm | choose per design; LSBU used 3.35–4.75 mm |
| Pellet radius (kinetics) | R_p | 1.7×10⁻⁴ (RD fine) / =d_p/2 | m | Chihara & Suzuki — **re-set to your gel** |
| Solid specific heat | c_{p,s} | **921** (≈0.92 kJ/kg·K) | J kg⁻¹K⁻¹ | standard silica-gel value; measure via DSC for accuracy |
| Solid thermal conductivity | k_s | **0.197** | W m⁻¹K⁻¹ | LSBU (measured) |
| BET surface area | – | 600–700 | m² g⁻¹ | LSBU 600.9; Hraiech 700 |
| Pore volume | – | 0.35–0.4 | cm³ g⁻¹ | LSBU 0.35; Hraiech 0.4 |
| **Isosteric heat of adsorption** | ΔH_ads / Q_st | **2800** (2.8×10⁶) | kJ/kg (J/kg) | Chakraborty 2009 (Tóth fit). Hraiech: 40–42 kJ/mol ⇒ ÷0.018 ≈ 2200–2350 kJ/kg — **use 2.5×10⁶ ± 0.3×10⁶ as the uncertainty band** |
| LDF pre-exp diffusivity | D_{s0} | 2.54×10⁻⁴ | m² s⁻¹ | Chihara & Suzuki 1983 |
| LDF activation energy | E_a | 4.2×10⁴ | J mol⁻¹ | Chihara & Suzuki 1983 |
| LDF geometric factor | F_0 | 15 | – | Glueckauf / Sakoda–Suzuki |
| Isotherm (recommended) | q*(T,φ) | 0.1049φ^0.5432 − 0.00156(T−25)φ + 8.91e-5(T−25)² | kg/kg | Hraiech 2025, adsorption branch |
| Isotherm (alt, Tóth) | q_m, t | q_m≈0.4, t≈0.8, Q_st=2800 kJ/kg | – | Chua 2002 / Chakraborty 2009; K_0 from original table |
| Humid-air density | ρ_g | ideal-gas mixture (thermo) | kg m⁻³ | ~1.1–1.2 at 295–300 K |
| Humid-air viscosity | μ | 1.8×10⁻⁵ | Pa·s | air at ~300 K |
| Humid-air c_p | c_{p,g} | ~1006 (dry) / mixture | J kg⁻¹K⁻¹ | thermo |
| Air thermal conductivity | k_g | 0.026 | W m⁻¹K⁻¹ | ~300 K |
| H₂O–air molecular diffusivity | D_m | 2.6×10⁻⁵ | m² s⁻¹ | ~300 K, for D_eff |
| Adsorbed-water c_p | c_{p,w,ads} | ~4180 | J kg⁻¹K⁻¹ | liquid water |

Effective bed properties computed in-solver per §2.4 (k_eff, (ρc_p)_eff) and §2.2
(d, f from ε, d_p).

---

## 8. Verification & Validation Plan

### 8.1 Verification (is the math solved right)

- **V1 — sign/box test (do first):** uniform humid box, no flow, run one adsorption then
  one desorption window. Gate: Y↓ & T↑ during adsorption; Y↑ & T↓ during desorption;
  global water balance ($\Delta$adsorbed = $\int\dot S_Y$) closes to <0.5 %.
- **V2 — porosity Δp:** single-phase airflow through the bed, compare CFD Δp(u) to the
  hand Ergun curve at u = 0.1, 0.5, 1.0 m/s. Gate: <2 % across the velocity range
  (this catches the factor-of-2 f error).
- **V3 — mesh independence:** GCI procedure of §1.4 on the 30 mm / 1.0 m/s corner.
  Gate: GCI < 3 % on all four QoIs.
- **V4 — time-step independence:** halve maxDeltaT until t_50 and cumulative mass change
  <1 %. Gate met before any validation run.
- **V5 — isotherm/kinetics unit test:** evaluate `qStarHraiech` and `kLDF` against the
  closed-form §2.5–2.6 at sample (T, RH); a single isolated cell should relax q→q* with
  the analytic time constant 1/k_LDF.

### 8.2 Validation (is it the right math)

- **VA1 — isotherm vs Hraiech et al. 2025:** reproduce equilibrium loading across
  27/33/44 °C × 44–82 % RH. Gate: within the paper's own RMSE band (≈1.5 % adsorption,
  ≈10 % desorption), since we use their correlation — this validates *implementation*,
  not the fit.
- **VA2 — packed-bed breakthrough vs LSBU dataset (Yeboah & Darkwa 2021, PMC7815469):**
  set the model to the FPB case (L = 0.30 m, d_p 3.35–4.75 mm, u 0.30–0.47 m/s, inlet
  21–26 °C and the dataset’s RH), and compare the **outlet humidity breakthrough curve**
  and the **MTZ temperature rise** to the measured traces. Gate: breakthrough time within
  ±15 %, peak MTZ ΔT within ±20 % (dataset has real packing/wall non-idealities the
  axisymmetric continuum model cannot fully capture — be honest that ±15 % is the
  realistic target, not 5 %).
- **VA3 (optional) — full-cycle water mass:** if any cited bed-scale yield exists for a
  comparable gel/condenser, check the *collected* (not desorbed) water to order of
  magnitude.

### 8.3 3-D spot-checks

Run **2–3** full-3-D cases (one mid-DoE point, one extreme L, one extreme D) to confirm
the wedge axisymmetric assumption holds (no azimuthal structure, wall channelling
captured). Gate: integrated QoIs within 5 % of the wedge.

### 8.4 Acceptance gates (summary)

| Gate | Criterion |
|---|---|
| Mass balance (V1) | <0.5 % closure |
| Ergun Δp (V2) | <2 % vs hand calc |
| Mesh GCI (V3) | <3 % all QoIs |
| Time-step (V4) | <1 % on t_50, mass |
| Isotherm impl. (VA1) | within source RMSE |
| Breakthrough (VA2) | t within ±15 %, ΔT within ±20 % |
| 3-D check (8.3) | <5 % vs wedge |

Only a model passing V1–V4 + VA1–VA2 is released to the DoE.

---

## 9. Risks Specific to OpenFOAM Adsorption (and mitigations)

1. **Stiff source terms.** k_LDF rises ~10× from adsorption to desorption temperature;
   an explicit q-update forces $\Delta t<0.2/k_\text{LDF}$ → tiny steps in the hot phase.
   *Mitigate:* update q **semi-implicitly** per cell —
   $q^{n+1}=(q^n+\Delta t\,k_\text{LDF}\,q^*)/(1+\Delta t\,k_\text{LDF})$ (unconditionally
   stable, exact for constant q*); apply the species/heat sinks with an `Sp` (implicit)
   part where possible (`semiImplicitSource`/`fvm::Sp`) so large rates don’t blow up Y or h.
2. **Phase-switch transient.** Step-changing wall flux/inlet at t_switch shocks the
   pressure/velocity field. *Mitigate:* **ramp** BCs over a few seconds
   (`uniformFixedValue` table), drop maxDeltaT around the switch, add an outer corrector,
   relax q. Prefer the **two-case chained** approach (§4.4-1) for production so each phase
   is clean.
3. **Unbounded Y / negative loading.** Sharp fronts + central schemes → Y<0 or q overshoot
   q*. *Mitigate:* bounded `limitedLinear`/`upwind` on Y, `clip`/`MULES`-style bounding,
   and clamp $0\le q\le q_m$, $0\le Y\le 1$ in the solver update.
4. **Validating a self-written solver.** The biggest risk: a plausible-but-wrong source
   sign or a unit error. *Mitigate:* the V1 box test and V2 Ergun test **before** any
   physics run; cross-read the term implementation against `adsorpFoam`’s equation files
   as an independent reference; keep `mDotAds` a single shared field so Y/h/continuity
   can never disagree.
5. **WSL2 /mnt/c I/O slowness.** Running the case under `/mnt/c/...` (Windows-mounted) is
   often **5–20× slower** for OpenFOAM’s many-small-file I/O than the native ext4 fs.
   *Mitigate:* keep the case in the **WSL2 home (`~/`, ext4)**, not under `/mnt/c`; use
   `writeControl adjustableRunTime` with sane `writeInterval` to limit write frequency;
   `purgeWrite 2` for DoE runs; copy results back to `/mnt/c` only at the end.
6. **Wedge/axis pitfalls.** Wrong patch type (`empty` vs `wedge`), non-symmetric wedge,
   or >5° angle → silently wrong radial transport or `checkMesh` failures.
   *Mitigate:* `checkMesh` must pass with zero errors; verify wedge faces are conjugate;
   keep θ ≤ 5° total.
7. **Isotherm/kinetics constant provenance.** R_p, K_0 (Tóth), and ΔH_ads carry real
   uncertainty (ΔH_ads spans 2.2–2.8 MJ/kg across sources). *Mitigate:* run the surrogate
   DoE with ΔH_ads and R_p flagged as **uncertain inputs**; do a small sensitivity sweep
   so the downstream surrogate inherits an honest error bar.

### Honest effort estimate

Mesh + single-phase porosity validation (V2) and the box test (V1): ~1–2 weeks. The
custom solver (q field + sources + sign-correct fvOptions) reaching a clean breakthrough:
the real work, **~3–5 weeks** including debugging signs/stiffness for someone new to
OpenFOAM solver editing. VA1/VA2 validation + grid/time studies: ~1–2 weeks. Full-cycle
phase-switch + 3-D checks: ~1 week. Total ~6–9 focused weeks. The dominant risk and time
sink is **#4 (validating a self-written solver)** — budget for it, and do V1/V2 first.

---

## Nomenclature

ε bed voidage [–]; ρ_g, ρ_s gas/solid density [kg m⁻³]; **u** superficial velocity
[m s⁻¹]; p pressure [Pa]; Y vapour mass fraction [–]; q, q̄ loading [kg/kg]; q* equilibrium
loading [kg/kg]; k_LDF LDF coefficient [s⁻¹]; D_s, D_{s0} surface diffusivity / pre-exp
[m² s⁻¹]; E_a activation energy [J mol⁻¹]; F_0 LDF factor 15 [–]; R_p pellet radius [m];
d, f Darcy/Forchheimer coeffs [m⁻², m⁻¹]; d_p particle diameter [m]; D_eff dispersion
[m² s⁻¹]; D_m molecular diffusivity [m² s⁻¹]; T temperature [K] (or °C where noted in
isotherm); ΔH_ads / Q_st isosteric heat [J kg⁻¹]; c_{p,*} specific heats [J kg⁻¹K⁻¹];
k_g, k_s, k_eff thermal conductivities [W m⁻¹K⁻¹]; φ / RH relative humidity [–]; P_sat
saturation pressure [Pa]; ω humidity ratio [kg/kg dry air]; T_c condenser temperature [K];
η_c condenser effectiveness [–]; A area [m²]; θ wedge angle [deg]; Re_p, Nu, Pr, Bi, Co
dimensionless groups.

---

## References (IEEE style; URLs as verified June 2026)

[1] C. Gößnitzer, "Development of a Multicomponent Adsorption Solver in OpenFOAM (adsorpFoam)," Diplomarbeit, TU Wien, 2016. doi:10.34726/hss.2016.29940. https://repositum.tuwien.at/handle/20.500.12708/6009 — *Verified: solver exists, ELM/IAST equilibrium + diffusion kinetics, multicomponent.*

[2] M. Hraiech et al., "Experimental characterization of silica gel adsorption and desorption isotherms under varying temperature and relative humidity in a fixed bed reactor," *Sci. Rep.*, vol. 15, 29041, 2025. https://pmc.ncbi.nlm.nih.gov/articles/PMC12334598/ (PDF: https://www.nature.com/articles/s41598-025-14677-7) — *Verified: T-explicit isotherm Eq. (8)/(10) constants, ΔH_ads 40–42 kJ/mol, 300 mm bed / 3 cm layer, 27–44 °C, 44–82 % RH, ρ_bulk 750 g/L, SSA 700 m²/g.*

[3] D. Yeboah and J. Darkwa, "Experimental data on water vapour adsorption on silica gel in fully packed and Z-annulus packed beds," *Data in Brief*, vol. 35, 106736, 2021. doi:10.1016/j.dib.2021.106736. https://pmc.ncbi.nlm.nih.gov/articles/PMC7815469/ — *Verified: FPB L = 0.30 m, d_p 3.35–4.75 mm, k_s 0.197 W/m·K, u 0.30–0.47 m/s, MTZ T data, BET 600.9 m²/g.*

[4] K. Chihara and M. Suzuki, "Air drying by packed bed of activated carbon and silica gel; LDF surface-diffusion kinetics," cited in silica-gel/water adsorption modelling. *Verified (secondary):* D_{s0}=2.54×10⁻⁴ m²/s, E_a=4.2×10⁴ J/mol, F_0=15, R_p=1.7×10⁻⁴ m — reproduced across multiple adsorption-chiller modelling papers (e.g. via [5]). *Primary numerical values verified secondhand; cross-check against Sakoda & Suzuki, J. Chem. Eng. Japan 17(1):52–57, 1984.*

[5] A. Chakraborty, B. B. Saha, K. C. Ng et al., "Adsorption thermodynamics of silica gel–water systems," *J. Chem. Eng. Data*, vol. 54, pp. 448–452, 2009. doi:10.1021/je800458k. https://pubs.acs.org/doi/10.1021/je800458k — *Verified (secondary): Tóth-fit isosteric heat ΔH_ads = 2800 kJ/kg for silica gel/water.*

[6] H. T. Chua, K. C. Ng, A. Chakraborty, N. M. Oo, M. A. Othman, "Adsorption characteristics of silica gel + water systems," *J. Chem. Eng. Data*, vol. 47, pp. 1177–1181, 2002. doi:10.1021/je0255067. https://pubs.acs.org/doi/10.1021/je0255067 — *Verified (secondary): Tóth isotherm best-fit for RD/A/3A silica gel, 298–338 K, 500–7000 Pa; q_m and t source. Exact K_0 to be read from the paper’s table.*

[7] S. Ergun, "Fluid flow through packed columns," *Chem. Eng. Prog.*, 48(2):89–94, 1952 — *Standard reference for the 150 / 1.75 packed-bed Δp constants used in §2.2.* (Form/constants verified via OpenFOAM porosity practice; original not fetched.)

[8] OpenFOAM porosity (`DarcyForchheimer`, `explicitPorositySource`) and wedge documentation — CFD Direct / OpenFOAM.com user guides; CFD-Online porosity-coefficient thread. https://doc.cfd.direct/openfoam/user-guide-v11/ — *Verified: d/f definitions, explicitPorositySource usage, Ergun→d,f mapping incl. the ½ → factor-2 on f.*

[9] `rhoReactingBuoyantFoam` solver reference, OpenFOAM API guide. https://www.openfoam.com/documentation/guides/latest/api/rhoReactingBuoyantFoam_8C.html — *Verified: compressible reacting buoyant solver, species + energy + PIMPLE, suitable single-region base.*

### Honesty / verification notes

- **Fully specified & verified:** Hraiech isotherm constants [2]; isosteric heat 2800 kJ/kg [5]; LSBU bed geometry & k_s [3]; LDF Chihara constants D_{s0}/E_a/F_0 [4]; Ergun→Darcy-Forchheimer d,f mapping and the f factor-of-2 [7,8]; solver base [1,9].
- **Verified secondhand (cross-check the primary before production):** the exact Chihara & Suzuki R_p / D_{s0} (use [4] note), Tóth K_0 [6], and the ΔH_ads spread (2.2–2.8 MJ/kg across [2] vs [5]) — treat ΔH_ads and R_p as **uncertain DoE inputs**.
- **Standard textbook, not separately fetched:** Wakao Nu correlation, Arden-Buck P_sat, packed-bed dispersion closure (D_eff), Glueckauf F_0=15 — all standard and uncontroversial; cite primary sources if the spec reviewer requires.
