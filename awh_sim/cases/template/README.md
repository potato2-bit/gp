# OpenFOAM case template (Tier 2)

Jinja2-templated OpenFOAM skeleton rendered per high-fi DoE row by `../../doe/render_cases.py`.

To be created in Step 4 (per Appendix A):
```
template/
├── 0/            {T, U, p, p_rgh, H2O}     # ICs/BCs with {{ placeholders }}
├── constant/     {transportProperties, thermophysicalProperties, fvOptions, polyMesh via blockMesh}
└── system/       {blockMeshDict (#calc L,R), controlDict (functionObjects), fvSchemes, fvSolution}
```
Placeholders: `{{ T_reg }}`, `{{ u_face }}`, `{{ L_bed }}`, `{{ d_p }}`, `{{ porosity }}`,
derived Ergun `{{ d_darcy }}`/`{{ f_forch }}`, and `{{ k_ldf }}`.
