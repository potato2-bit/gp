# Custom OpenFOAM adsorption solver (Tier 2)

To be created in Step 4 (per Appendix A §3). Custom solver derived from
`rhoReactingBuoyantFoam`:
- adds the loading field `q` and its LDF PDE  dq/dt = k_LDF (q* - q)
- exposes a shared `mDotAds = (1-eps)*rhoS*dq/dt` field
- adsorption species sink, isosteric-heat source, and Darcy-Forchheimer porosity applied
  via coded `fvOptions` (kept in `cases/template/constant/fvOptions`)

Build under WSL with the OpenFOAM env sourced:
```
wmake          # in this directory once the solver source is added
```
Validation before any DoE run: box/mass-balance (V1), Ergun Δp (V2), mesh (V3), time-step
(V4), isotherm impl. (VA1), LSBU breakthrough (VA2). See Appendix A §8.
