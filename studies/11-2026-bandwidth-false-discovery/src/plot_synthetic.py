"""Chart: pattern-hunter NW t vs bandwidth multiple, synthetic null case.

Reads out/synthetic_null.csv (written by tests/test_synthetic.py) and writes
out/synthetic_null.png. Plotting only; no new statistics.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "out"
SURFACE, INK, INK2, SERIES = "#fcfcfb", "#0b0b0b", "#52514e", "#2a78d6"
DOT = "#86b6ef"  # lighter step of the same blue ramp


def main() -> None:
    df = pd.read_csv(OUT / "synthetic_null.csv")
    mults = sorted(df["mult"].unique())
    h_cv = float(df.loc[df["mult"] == 1.0, "h"].iloc[0])
    pos = {m: i for i, m in enumerate(mults)}
    rng = np.random.default_rng(7)  # jitter only

    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=200, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    xj = df["mult"].map(pos) + rng.uniform(-0.18, 0.18, len(df))
    ax.scatter(xj, df["t_nw"], s=14, color=DOT, edgecolor=SURFACE, linewidth=0.6,
               label="one null dataset", zorder=2)
    med = df.groupby("mult")["t_nw"].median()
    share = df.groupby("mult")["t_nw"].apply(lambda s: (s > 3).mean())
    ax.plot([pos[m] for m in mults], med.values, color=SERIES, linewidth=2, marker="o",
            markersize=7, markeredgecolor=SURFACE, label="median over datasets", zorder=3)
    ax.axhline(3, color=INK2, linewidth=1, linestyle=(0, (4, 3)), zorder=1)
    ax.text(len(mults) - 0.5, 3.05, "edge bar t = 3", color=INK2, fontsize=8, ha="right", va="bottom")
    for m in mults:
        ax.text(pos[m], -2.85, f"{share[m]:.0%}", color=INK2, fontsize=8, ha="center")
    ax.text(-0.6, -2.85, "t > 3:", color=INK2, fontsize=8, ha="right")

    ax.set_xticks(range(len(mults)), [f"{m:g}x" for m in mults])
    ax.set_xlim(-0.9, len(mults) - 0.4)
    ax.set_ylim(-3.1, 4)
    ax.set_xlabel(f"Bandwidth multiple of LCV bandwidth (h_cv = {h_cv:.3f})", color=INK, fontsize=9)
    ax.set_ylabel("Pattern-hunter Newey-West t (5 lags)", color=INK, fontsize=9)
    n_rep = df["rep"].nunique()
    ax.set_title(f"Null case: best 5% x-pocket t-stat by bandwidth ({n_rep} datasets, n = 50,000 each, seed 7)",
                 color=INK, fontsize=10, loc="left")
    ax.grid(axis="y", color="#e4e3df", linewidth=0.6)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color("#c9c8c2")
    ax.tick_params(colors=INK2, labelsize=8)
    leg = ax.legend(loc="lower left", bbox_to_anchor=(0.0, 0.08), fontsize=8, frameon=False)
    for t in leg.get_texts():
        t.set_color(INK)
    fig.tight_layout()
    fig.savefig(OUT / "synthetic_null.png", facecolor=SURFACE)


if __name__ == "__main__":
    main()
