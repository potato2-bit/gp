# Literature review and parameter provenance

Scope: the sources this project's three design parameterisations rest on, and
where each numerical default comes from. Every entry says how far it was
checked. **"Abstract-level"** means the bibliographic record and abstract were
confirmed from a publisher, repository or library page on 2026-11-26; the full
text was not read, so specific equations and constants in it are *not* claimed
here. Nothing below is cited for a number it was not checked for.

## 1. Sources

### Chladni-pattern / nodal-line design
| Ref | Citation | Checked | Used for |
|---|---|---|---|
| [1] | L. Xue, G. Wen, F. Wang, N. L. Pedersen, "Topology optimization design of Chladni patterns for vibration mode manipulability", *Acta Mech. Sin.* 40(4), 423445 (2024), doi:10.1007/s10409-023-23445-x | abstract-level (DTU Orbit) | Density method, Eq. (15) loss; this repo's reference implementation |
| [2] | Y. Yan et al., "Achieving desired nodal lines in freely vibrating structures via material-field series-expansion topology optimization", *Front. Mech. Eng.* (2023), doi:10.1007/s11465-023-0758-y | abstract-level (search snippet; author list not confirmed) | Alternative nodal-line parameterisation; states that earlier eigenmode methods control point amplitudes, so nodal lines are not strictly controlled |

### Level-set topology optimization
| Ref | Citation | Checked | Used for |
|---|---|---|---|
| [3] | M. Y. Wang, X. Wang, D. Guo, "A level set method for structural topology optimization", *Comput. Methods Appl. Mech. Eng.* 192(1-2), 227-246 (2003), doi:10.1016/s0045-7825(02)00559-5 | abstract-level | Level-set boundary representation, Hamilton-Jacobi update |
| [4] | G. Allaire, F. Jouve, A.-M. Toader, "Structural optimization using sensitivity analysis and a level-set method", *J. Comput. Phys.* 194(1), 363-393 (2004), doi:10.1016/j.jcp.2003.09.032 | abstract-level | Shape derivative + level-set advection; notes strong dependence on the initial guess |
| [5] | N. P. van Dijk, K. Maute, M. Langelaar, F. van Keulen, "Level-set methods for structural topology optimization: a review", *Struct. Multidisc. Optim.* 48(3), 437-472 (2013), doi:10.1007/s00158-013-0912-y | abstract-level (page range not confirmed) | Survey of parameterisation, update, regularisation, hole nucleation |
| [6] | S. Osher, J. A. Sethian, "Fronts propagating with curvature-dependent speed: algorithms based on Hamilton-Jacobi formulations", *J. Comput. Phys.* 79(1), 12-49 (1988) | abstract-level | Zero level set evolved by a Hamilton-Jacobi equation |
| [7] | M. Sussman, P. Smereka, S. Osher, "A level set approach for computing solutions to incompressible two-phase flow", *J. Comput. Phys.* 114(1), 146-159 (1994) | abstract-level; the reinitialisation attribution is **secondary-source only** | Signed-distance reinitialisation |
| [8] | S. Y. Wang et al., "On hole nucleation in topology optimization using the level set methods", *CMES* (2007) | title and abstract summary only; volume/pages not confirmed | Hole nucleation; also cited by a 2019 paper for the statement that a strong perimeter penalty can block small holes |

### Finite element model and eigen-analysis
| Ref | Citation | Checked | Used for |
|---|---|---|---|
| [9] | K.-J. Bathe, E. N. Dvorkin, "A four-node plate bending element based on Mindlin/Reissner plate theory and a mixed interpolation", *Int. J. Numer. Methods Eng.* 21, 367-383 (1985), doi:10.1002/nme.1620210213 | abstract-level | MITC4 shear interpolation (default element) |
| [10] | R. D. Mindlin, "Influence of rotatory inertia and shear on flexural motions of isotropic, elastic plates", *J. Appl. Mech.* 18, 31-38 (1951) | bibliographic record only; value of the shear factor in the original **not** confirmed (secondary sources give 5/6 as the usual convention and call it a lower bound, not exact) | Shear-deformable plate theory |
| [11] | R. B. Nelson, "Simplified calculation of eigenvector derivatives", *AIAA J.* 14(9), 1201-1205 (1976) | abstract-level | Eigenvector derivatives for the adjoint |
| [12] | N. L. Pedersen, "Maximization of eigenvalues using topology optimization", *Struct. Multidisc. Optim.* 20(1), 2-11 (2000), doi:10.1007/s001580050130 | abstract-level | Localised modes in low-density regions, the origin of the ersatz-void concern |

### Optimisers and projection
| Ref | Citation | Checked | Used for |
|---|---|---|---|
| [13] | K. Svanberg, "The method of moving asymptotes - a new method for structural optimization", *Int. J. Numer. Methods Eng.* 24(2), 359-373 (1987), doi:10.1002/nme.1620240207 | abstract-level | MMA |
| [14] | I. Loshchilov, F. Hutter, "Decoupled weight decay regularization", ICLR 2019, arXiv:1711.05101 | abstract-level | AdamW |
| [15] | F. Wang, B. S. Lazarov, O. Sigmund, "On projection methods, convergence and robust formulations in topology optimization", *Struct. Multidisc. Optim.* 43(6), 767-784 (2011), doi:10.1007/s00158-010-0602-y | abstract-level | Heaviside projection; simple projection does not give local length-scale control |

## 2. What the literature does and does not settle

* **Nothing found here validates the specific numerical defaults of the
  level-set and spline methods** (Heaviside half-width, CFL step, smoothing
  length, reinitialisation interval, hole radius, perforation grid). Wang et
  al. [3] and the review [5] are about compliance-type problems, and only the
  abstracts were read. These defaults must therefore be treated as
  *empirical*, justified only by the measurements in `docs/MEASUREMENTS.md`,
  not by a citation.
* [4] and [5] both flag the initial design as a strong determinant of the
  outcome, which is consistent with this repo's finding that the perforation
  grid matters (3x4 vs 4x5 vs 5x6 holes, README "Tuning notes").
* [8] (as relayed by a later paper) says a strong perimeter penalty can block
  small holes. This repo's perimeter weight 0.2 is therefore a trade-off to be
  measured, not a literature value.
* The shear correction factor 5/6 is a convention. A secondary source says it
  is a lower bound and that the exact factor is higher in some regimes; the
  repo's own check (computed 227.2 Hz vs the paper's 225.01 Hz, <1%) is the
  evidence for it, and that check depends on the paper's unstated nu and kappa.

## 3. Provenance of each default (to be completed from measurements)

Legend: **L** literature (ref), **P** paper-stated, **F** fitted by the repo
author to a paper value, **E** empirical tuning on the quick mesh, **U** no
source found. Numbers in the last column are filled in by the sweeps in
`docs/MEASUREMENTS.md`.

| Parameter | Default | Class | Note |
|---|---|---|---|
| Poisson ratio nu, shear factor kappa | 0.3, 5/6 | F | fitted to the paper's 5th-mode frequency of the uniform plate |
| Band / gap / surround widths | 1 / 2 / 8 el | F/E | gap and surround read off Fig. 2(b) of [1]; band from a repo-derived estimate |
| epsilon, tau | 0.01, 0.40 | P (per README) | from [1]; not re-verified from the paper text |
| Volume cap V* (paper loss) | 0.55 | F | never stated in [1] |
| Level-set void: E, rho ratio | 1e-3, 1e-5 | E | the repo tests that no spurious void modes appear; no source |
| Heaviside half-width | 0.08 m | E | README says Wang et al. use two elements; **not verified** |
| HJ step / decay / min | 0.008 / 0.996 / 0.002 m | E | tuned on the 0.04 m mesh |
| Smoothing length | 0.057 m | E | |
| Reinit interval | 5 | E | |
| Initial holes, radius | 4x5, 0.35 | E | |
| Perimeter weight | 0.2 | E | |
| Signed-loss kappa, zone-energy share | see `formulations.py` | U | introduced in the latest commit |
