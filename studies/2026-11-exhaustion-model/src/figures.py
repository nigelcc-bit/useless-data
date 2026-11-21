"""Report figures from results/*.csv."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
ASSETS = ["SPX", "NDX", "SOX"]
COL = {"SPX": "#3b6ea5", "NDX": "#d08c2e", "SOX": "#7a4f9a"}


def ladder():
    ev = {a: pd.read_csv(R / f"events_{a}.csv") for a in ASSETS}
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for ax, t in zip(axes, ["T1", "T2"]):
        for k, a in enumerate(ASSETS):
            e = ev[a]
            e = e[e["type"].str.startswith("B")].dropna(subset=[t])
            g = e.groupby("type")[t].agg(["mean", "count"]).reindex(["B10", "B15", "B20", "B30"])
            x = np.arange(4) + (k - 1) * 0.22
            ax.bar(x, g["mean"], width=0.2, color=COL[a], label=a)
            for xi, (m, n) in zip(x, g.itertuples(index=False)):
                if n == n:
                    ax.text(xi, (m if m == m else 0) + 0.02, f"{int(n)}", ha="center", fontsize=7, color="#444")
        ax.set_xticks(range(4), ["-10%", "-15%", "-20%", "-30%"])
        ax.set_title(f"{t} rate at each rung (all events 1954/86/95 to 2026; n above bars)", fontsize=9)
        ax.set_ylim(0, 1.05)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("share of events")
    axes[0].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(R / "fig_escalation_ladder.png", dpi=150)
    plt.close(fig)


def skill():
    tr = pd.read_csv(R / "layer_tests_train.csv")
    ho = pd.read_csv(R / "holdout_scorecard.csv")
    ho = ho[ho["layer"] != "L0"]
    m = tr.merge(ho[["asset", "target", "layer", "skill"]], on=["asset", "target", "layer"], suffixes=("_train", "_hold"))
    fig, ax = plt.subplots(figsize=(6, 5))
    for a in ASSETS:
        s = m[m["asset"] == a]
        ax.scatter(s["skill_train"], s["skill_hold"], color=COL[a], label=a, s=22)
    for _, r in m[(m["skill_train"] > 0.08) | (m["skill_hold"] < -0.15)].iterrows():
        ax.annotate(f"{r['layer']} {r['asset']} {r['target']}", (r["skill_train"], r["skill_hold"]), fontsize=7,
                    xytext=(4, 2), textcoords="offset points")
    ax.axhline(0, color="grey", lw=0.8)
    ax.axvline(0, color="grey", lw=0.8)
    ax.axvline(0.02, color="grey", lw=0.8, ls="--")
    ax.set_xlabel("training LOEO Brier skill vs Layer 0")
    ax.set_ylabel("hold-out Brier skill vs Layer 0 (2018-2026)")
    ax.set_title("Every layer: training vs hold-out skill", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(R / "fig_skill_train_vs_holdout.png", dpi=150)
    plt.close(fig)


def live():
    C = pd.read_parquet(ROOT / "data" / "processed" / "closes.parquet")
    S = pd.read_csv(R / "live_state.csv")
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    for ax, a in zip(axes, ASSETS):
        s = C[a].dropna().loc["2026-06-01":]
        st = S[S.asset == a].iloc[0]
        ax.plot(s.index, s.values, color=COL[a], lw=1.3)
        ax.axhline(st["T1_line_from_5nov"], color="#b03030", ls="--", lw=0.9)
        ax.text(s.index[0], st["T1_line_from_5nov"], " T1 fails below (0.9 x 5 Nov close)", fontsize=7, va="bottom", color="#b03030")
        ax.axvline(pd.Timestamp("2026-11-05"), color="grey", lw=0.7)
        ax.set_title(f"{a}: {st['depth']:+.1%} from ref. peak {st['ref_peak_date']}", fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", labelsize=7)
    fig.tight_layout()
    fig.savefig(R / "fig_live.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    ladder()
    skill()
    live()
