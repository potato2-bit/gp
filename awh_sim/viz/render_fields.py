#!/usr/bin/env python3
"""Render OpenFOAM scalar fields of the AWH bed to PNG screenshots (headless).

No ParaView/pyvista needed: parses the ascii internalField + cell centres (Cx,Cy,Cz
from `postProcess -func writeCellCentres`), maps each cell to (x, r) of the axisymmetric
wedge, mirrors about the axis, and draws a filled field map with matplotlib. Produces a
per-field montage over time plus a final-state panel.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np


def read_scalar(path: Path, ncells=None):
    txt = path.read_text()
    if re.search(r"internalField\s+uniform", txt):
        v = float(re.search(r"internalField\s+uniform\s+([-\d.eE+]+)", txt).group(1))
        return np.full(ncells, v)
    m = re.search(r"List<scalar>\s*\n?\s*(\d+)\s*\(([^)]*)\)", txt, re.S)
    n = int(m.group(1))
    vals = np.array([float(x) for x in m.group(2).split()])
    assert vals.size == n, f"{path}: {vals.size} != {n}"
    return vals


def cell_xr(timedir: Path):
    Cx = read_scalar(timedir / "Cx")
    Cy = read_scalar(timedir / "Cy", Cx.size)
    Cz = read_scalar(timedir / "Cz", Cx.size)
    return Cx, np.sqrt(Cy ** 2 + Cz ** 2)


def panel(ax, x, r, f, title, label, cmap):
    # mirror about the axis for a full-bed look
    X = np.concatenate([x, x]) * 1000.0          # mm
    R = np.concatenate([r, -r]) * 1000.0
    F = np.concatenate([f, f])
    tri = mtri.Triangulation(X, R)
    tpc = ax.tripcolor(tri, F, shading="gouraud", cmap=cmap)
    ax.set_title(title, fontsize=9)
    ax.set_aspect("auto")
    ax.set_xlabel("axial x [mm]", fontsize=8)
    ax.set_ylabel("radius [mm]", fontsize=8)
    cb = plt.colorbar(tpc, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label(label, fontsize=8)
    cb.ax.tick_params(labelsize=7)


FIELDS = {
    "Y": dict(label="vapour mass fraction Y", cmap="viridis", conv=lambda v: v),
    "T": dict(label="temperature [°C]", cmap="inferno", conv=lambda v: v - 273.15),
    "q": dict(label="loading q [kg/kg]", cmap="cividis", conv=lambda v: v),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ctime", default=None, help="time dir holding Cx/Cy/Cz")
    args = ap.parse_args()

    case = Path(args.case)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    times = sorted([p.name for p in case.iterdir()
                    if re.fullmatch(r"\d+(\.\d+)?", p.name) and (p / "Y").exists()],
                   key=float)
    ctime = args.ctime or times[-1]
    x, r = cell_xr(case / ctime)
    print("times:", times, "| ncells:", x.size)

    # pick up to 6 frames spread across time for the montage
    sel = times if len(times) <= 6 else [times[i] for i in
          np.linspace(0, len(times) - 1, 6).round().astype(int)]

    for fld, spec in FIELDS.items():
        fig, axes = plt.subplots(1, len(sel), figsize=(3.0 * len(sel), 2.8), squeeze=False)
        vmin = vmax = None
        data = {}
        for t in sel:
            fp = case / t / fld
            if fp.exists():
                data[t] = spec["conv"](read_scalar(fp, x.size))
        allv = np.concatenate(list(data.values()))
        vmin, vmax = float(allv.min()), float(allv.max())
        for ax, t in zip(axes[0], sel):
            f = data.get(t)
            if f is None:
                continue
            panel(ax, x, r, f, f"t = {float(t):.0f} s", spec["label"], spec["cmap"])
            ax.collections[0].set_clim(vmin, vmax)
        fig.suptitle(f"AWH adsorption bed — {spec['label']} (axisymmetric wedge)", fontsize=11)
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        p = out / f"field_{fld}_evolution.png"
        fig.savefig(p, dpi=140); plt.close(fig)
        print("saved", p.name)

    # final-state 3-panel
    tf = times[-1]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.0), squeeze=False)
    for ax, fld in zip(axes[0], FIELDS):
        spec = FIELDS[fld]
        f = spec["conv"](read_scalar(case / tf / fld, x.size))
        panel(ax, x, r, f, fld, spec["label"], spec["cmap"])
    fig.suptitle(f"AWH adsorption bed — final state (t = {float(tf):.0f} s)", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    p = out / "field_final_state.png"
    fig.savefig(p, dpi=140); plt.close(fig)
    print("saved", p.name)


if __name__ == "__main__":
    main()
