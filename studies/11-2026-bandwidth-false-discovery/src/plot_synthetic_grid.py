"""Heatmap: null false-discovery rate by bandwidth multiple x minimum pocket size.

Reads out/synthetic_null_grid.csv, writes out/synthetic_null_grid.png.
Plotting only. Two panels (share t > 2, share t > 3), each with its own
sequential scale starting at 0; every cell is labelled with its value.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "out"
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
CMAP = LinearSegmentedColormap.from_list("blue_seq", RAMP)


def main() -> None:
    df = pd.read_csv(OUT / "synthetic_null_grid.csv")
    h_cv = float(df.loc[df["mult"] == 1.0, "h"].iloc[0])
    n_rep = df["rep"].nunique()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), dpi=200, facecolor=SURFACE)
    for ax, thr in zip(axes, [2, 3]):
        tab = (df.assign(hit=df["t_nw"] > thr)
                 .groupby(["min_frac", "mult"])["hit"].mean().unstack("mult"))
        vmax = float(tab.values.max())
        im = ax.imshow(tab.values, cmap=CMAP, vmin=0, vmax=vmax, aspect="auto")
        for i in range(tab.shape[0]):
            for j in range(tab.shape[1]):
                v = tab.values[i, j]
                ax.text(j, i, f"{v:.1%}", ha="center", va="center", fontsize=8,
                        color="#ffffff" if v > 0.55 * vmax else INK)
        ax.set_xticks(range(tab.shape[1]), [f"{m:g}x" for m in tab.columns])
        ax.set_yticks(range(tab.shape[0]), [f"{f:.1%}" for f in tab.index])
        ax.set_xlabel(f"Bandwidth multiple of LCV bandwidth (h_cv = {h_cv:.3f})", color=INK, fontsize=9)
        ax.set_ylabel("Minimum pocket size", color=INK, fontsize=9)
        ax.set_title(f"Share of null datasets with pattern-hunter t > {thr}", color=INK,
                     fontsize=10, loc="left")
        ax.tick_params(colors=INK2, labelsize=8, length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_facecolor(SURFACE)
        cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02, format=lambda v, _: f"{v:.0%}")
        cb.outline.set_visible(False)
        cb.ax.tick_params(colors=INK2, labelsize=7, length=0)
    fig.suptitle(f"Synthetic null: false-discovery rate by bandwidth x minimum pocket size "
                 f"({n_rep} datasets per cell, n = 50,000, seed 7)", color=INK, fontsize=10.5,
                 x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(OUT / "synthetic_null_grid.png", facecolor=SURFACE)


if __name__ == "__main__":
    main()
