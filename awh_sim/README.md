
# awh_sim — Solar-regenerated silica-gel adsorption AWH simulation

A multi-fidelity simulation of a **solar-regenerated silica-gel adsorption atmospheric
water harvester** (AWH) that produces distilled water for autonomous PV-panel cleaning,
evaluated across several Egyptian climate sites. Sub-project of the graduation project.

See [`docs/DESIGN_SPEC.md`](docs/DESIGN_SPEC.md) for the full design (master + Appendix A
OpenFOAM solver/physics + Appendix B DoE/surrogate/climate/economics).

## Architecture (hybrid, open-source, runs under WSL2 Ubuntu)

```
pyGAPS (isotherm + isosteric heat)
   → CADET (fast cyclic column, low-fidelity, many runs)
   → OpenFOAM 2-D axisymmetric CFD (non-isothermal, high-fidelity, ~40 runs)
   → SMT multi-fidelity Kriging (fuse low+high)
   → NASA POWER hourly climate sweep × 6 Egyptian sites
   → annual yield / SEC / regeneration energy / LCOW
```

## Pipeline (directory = stage)

| Dir | Stage | Entry point |
|---|---|---|
| `isotherm/` | Tier 0 — fit q*(T,RH) + ΔH_ads | `fit_isotherm.py` |
| `cadet/`    | Tier 1 — fast column DoE (low-fi) | `run_cadet_doe.py` |
| `solver/` + `cases/` | Tier 2 — OpenFOAM CFD (high-fi) | `../doe/run_doe.sh` |
| `doe/`      | nested DoE sampling + templating + extraction | `sample_doe.py` |
| `surrogate/`| multi-fidelity Kriging train + validate | `train_mfk.py` |
| `climate/`  | NASA POWER fetch + cycle aggregation + annual sweep | `run_annual.py` |
| `economics/`| LCOW | `lcow.py` |
| `tests/`    | unit tests | `pytest` |

## Environment setup (WSL2 Ubuntu 22.04)

> Run cases on the **ext4 home** (`~/awh_runs`), NOT under `/mnt/c` (OpenFOAM small-file
> I/O is 5–20× slower on the Windows mount). Keep this repo on `/mnt/c`, copy/symlink the
> case dir to `~` for runs.

```bash
# 1. OpenFOAM (ESI / openfoam.com)
curl -fsSL https://dl.openfoam.com/add-debian-repo.sh | sudo bash
sudo apt-get update && sudo apt-get install -y openfoam2406-default
echo 'source /usr/lib/openfoam/openfoam2406/etc/bashrc' >> ~/.bashrc

# 2. Miniconda + CADET-Core
wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/mc.sh
bash /tmp/mc.sh -b -p ~/miniconda3 && ~/miniconda3/bin/conda init bash
conda create -n awh python=3.11 -y && conda activate awh
conda install -c conda-forge cadet -y      # CADET-Core (cadet-cli)

# 3. Python deps (in the awh env)
pip install -r requirements.txt            # incl. cadet-process, pygaps, smt
pip freeze > requirements.lock.txt         # pin once validated
```

Verify: `cadet-cli --version`, `blockMesh -help`, `python -c "import smt, pygaps, cadet"`.

## Run order

```bash
conda activate awh
python isotherm/fit_isotherm.py            # Gate G0
python cadet/build_column.py --selftest    # Gate G1 (LSBU breakthrough)
python doe/sample_doe.py                    # nested DoE table
python cadet/run_cadet_doe.py              # low-fi responses
python doe/render_cases.py && bash doe/run_doe.sh   # high-fi CFD (Gate G2)
python doe/extract_results.py
python surrogate/train_mfk.py && python surrogate/validate.py   # Gate G3
python climate/fetch_sites.py
python climate/run_annual.py               # annual sweep
python economics/lcow.py                    # Gate G4
```
