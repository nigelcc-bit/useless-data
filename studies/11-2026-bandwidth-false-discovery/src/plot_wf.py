"""Cumulative net walk-forward return for three cells against the placebo 5th-95th band.

Reads out/wf_real_daily.parquet and out/wf_placebo_paths.csv; writes
out/wf_cumulative.png. Plotting only. Real paths are daily; the placebo band
is the 5th-95th percentile of month-end cumulative net return across reps.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "out"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SERIES, BAND = "#2a78d6", "#cde2fb"
CELLS = [("1x_0.5%", "1x LCV bandwidth, 0.5% min pocket"),
         ("1x_5.0%", "1x LCV bandwidth, 5% min pocket"),
         ("0.25x_2.0%", "0.25x LCV bandwidth, 2% min pocket")]


def main() -> None:
    daily = pd.read_parquet(OUT / "wf_real_daily.parquet")
    paths = pd.read_csv(OUT / "wf_placebo_paths.csv")
    n_rep = paths["rep"].nunique()
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), dpi=200, facecolor=SURFACE, sharey=True)
    for ax, (key, label) in zip(axes, CELLS):
        ax.set_facecolor(SURFACE)
        p = paths[paths["cell"] == key].pivot(index="month", columns="rep", values="cum_net")
        mx = pd.PeriodIndex(p.index, freq="M").to_timestamp(how="end")
        lo, hi = np.nanquantile(p.values, 0.05, axis=1), np.nanquantile(p.values, 0.95, axis=1)
        ax.fill_between(mx, lo, hi, color=BAND, linewidth=0, step="post",
                        label=f"placebo 5th-95th ({n_rep} reps)")
        cum = np.cumprod(1 + daily[f"{key}_net"]) - 1
        ax.plot(cum.index, cum.values, color=SERIES, linewidth=1.6, label="real, net of 10bp/side")
        ax.axhline(0, color=INK2, linewidth=0.8)
        ax.set_title(label, color=INK, fontsize=9.5, loc="left")
        ax.grid(axis="y", color=GRID, linewidth=0.6)
        for s in ["top", "right"]:
            ax.spines[s].set_visible(False)
        for s in ["left", "bottom"]:
            ax.spines[s].set_color("#c9c8c2")
        ax.tick_params(colors=INK2, labelsize=8)
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    axes[0].set_ylabel("Cumulative net return (compounded)", color=INK, fontsize=9)
    leg = axes[0].legend(loc="lower left", fontsize=8, frameon=False)
    for t in leg.get_texts():
        t.set_color(INK)
    fig.suptitle("Walk-forward 2005-2025 (5-year training, 1-year test), gap pocket long-short, "
                 "5-day overlapping holds", color=INK, fontsize=10.5, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(OUT / "wf_cumulative.png", facecolor=SURFACE)


if __name__ == "__main__":
    main()
