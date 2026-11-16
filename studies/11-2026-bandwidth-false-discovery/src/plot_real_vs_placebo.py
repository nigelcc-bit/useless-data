"""Two-panel heatmap: real pattern-hunter t by cell, and its empirical placebo p by cell.

Reads out/real_vs_placebo.csv, writes out/real_vs_placebo.png. Plotting only.
Left: real NW t (sequential blue if all t >= 0, else diverging blue/orange
around a neutral 0). Right: empirical p (darker = smaller p). Every cell labelled.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "out"
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
SEQ = LinearSegmentedColormap.from_list("blue_seq", BLUE)
DIV = LinearSegmentedColormap.from_list("div", ["#b35806", "#f1a340", "#e8e7e3", "#6da7ec", "#184f95"])


def panel(ax, fig, tab, cmap, vmin, vmax, fmt, title, dark_if):
    im = ax.imshow(tab.values, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    for i in range(tab.shape[0]):
        for j in range(tab.shape[1]):
            v = tab.values[i, j]
            ax.text(j, i, fmt(v), ha="center", va="center", fontsize=8,
                    color="#ffffff" if dark_if(v) else INK)
    ax.set_xticks(range(tab.shape[1]), [f"{m:g}x" for m in tab.columns])
    ax.set_yticks(range(tab.shape[0]), [f"{f:.1%}" for f in tab.index])
    ax.set_xlabel("Bandwidth multiple of LCV bandwidth", color=INK, fontsize=9)
    ax.set_ylabel("Minimum pocket size", color=INK, fontsize=9)
    ax.set_title(title, color=INK, fontsize=10, loc="left")
    ax.tick_params(colors=INK2, labelsize=8, length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=INK2, labelsize=7, length=0)


def main() -> None:
    s = pd.read_csv(OUT / "real_vs_placebo.csv")
    n_pl = int(s["n_placebo"].min())
    t = s.pivot(index="min_frac", columns="mult", values="real_t")
    p = s.pivot(index="min_frac", columns="mult", values="emp_p")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), dpi=200, facecolor=SURFACE)
    tmin, tmax = float(np.nanmin(t.values)), float(np.nanmax(t.values))
    if tmin >= 0:
        panel(axes[0], fig, t, SEQ, 0, tmax, lambda v: f"{v:.2f}", "Real-data pattern-hunter t (NW, 5 lags)",
              lambda v: v > 0.55 * tmax)
    else:
        a = max(abs(tmin), abs(tmax))
        panel(axes[0], fig, t, DIV, -a, a, lambda v: f"{v:.2f}", "Real-data pattern-hunter t (NW, 5 lags)",
              lambda v: abs(v) > 0.6 * a)
    panel(axes[1], fig, p, SEQ.reversed(), 0, 1, lambda v: f"{v:.3f}",
          f"Empirical p vs within-date placebo ({n_pl} reps)", lambda v: v < 0.35)
    fig.suptitle("Development sample 2000-2025, in-sample, no costs: real t and placebo p by "
                 "bandwidth x minimum pocket size", color=INK, fontsize=10.5, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(OUT / "real_vs_placebo.png", facecolor=SURFACE)


if __name__ == "__main__":
    main()
