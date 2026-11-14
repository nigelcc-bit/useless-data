# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.6
# ---

# %% [markdown]
# # N01: Power (MDE) and TOST equivalence for Study 1 reclaim returns
#
# Specification: `PREREG/N01_power.md` (committed before this notebook ran).
# All logic is in `src/power.py`; this notebook only calls it and plots.
#
# **Hindsight status:** Study 1 data were already seen. N01 re-expresses them;
# it is not new evidence.

# %%
import sys
from pathlib import Path

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "src" / "power.py").exists())
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src import power as P

pd.set_option("display.width", 160)
events = {ix: P.load_study1_events(ix) for ix in ("NDX", "SPX")}

# %% [markdown]
# ## Anchor checks (stop if any fails)

# %%
P.check_anchors(events)

# %% [markdown]
# ## MDE at 80% power (one-sided t, alpha 0.05; 10,000 simulations, seed 7)

# %%
mde = P.mde_table(events)
print(P.format_mde_table(mde).to_markdown(index=False))

# %% [markdown]
# ## TOST equivalence vs the drawdown-matched mean (bounds +/-2 and +/-5 points, alpha 0.05)

# %%
tost = P.tost_table(events)
show = tost[["index", "horizon", "n", "benchmark_mean", "diff", "ci90_lo", "ci90_hi",
             "bound", "p_lower", "p_upper", "p_tost", "equivalent", "bh_q", "bh_equivalent_q10"]]
print(show.to_markdown(index=False, floatfmt=".4f"))

# %%
out = P.save_outputs(mde, tost)
ledger = P.update_ledger(tost)
print(f"saved to {out.relative_to(ROOT)}; ledger rows for N01: {(ledger['family'] == 'N01_TOST').sum()}")

# %% [markdown]
# ## DESCRIPTIVE: MDE under a cluster bootstrap by calendar year (no tests)
#
# PREREG/N01_power.md addendum. Resamples whole calendar years (B = 5,000,
# seed 7) to show how optimistic the iid MDEs are. Not a hypothesis test.

# %%
cl_mde = P.cluster_mde_table(events)
print(P.format_cluster_mde_table(cl_mde).to_markdown(index=False))

# %% [markdown]
# ## Charts

# %%
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
for ax, ix in zip(axes, ["NDX", "SPX"]):
    g = mde[mde["index"] == ix]
    for k, (_, r) in enumerate(g.iterrows()):
        d = np.linspace(0, 0.25, 200)
        ax.plot(d * 100, P.power_curve(int(r["n"]), r["sd"], d), label=f"{r['horizon']} (n={r['n']})")
        ax.axvline(r["mde_sim"] * 100, ls=":", lw=1, color=f"C{k}")
    ax.axhline(0.8, color="grey", lw=0.8)
    ax.set_title(f"{ix}: power vs true excess return")
    ax.set_xlabel("true excess return over drawdown-matched mean (points)")
    ax.legend(frameon=False, fontsize=8)
axes[0].set_ylabel("power (one-sided t, alpha 0.05)")
fig.tight_layout()

# %%
fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), sharey=False)
for ax, ix in zip(axes, ["NDX", "SPX"]):
    g = tost[(tost["index"] == ix) & (tost["bound"] == 0.02)].reset_index(drop=True)
    y = np.arange(len(g))
    ax.errorbar(g["diff"] * 100, y, xerr=[(g["diff"] - g["ci90_lo"]) * 100, (g["ci90_hi"] - g["diff"]) * 100],
                fmt="o", color="k", capsize=3)
    for b, ls in [(2, "--"), (5, ":")]:
        for s in (-1, 1):
            ax.axvline(s * b, ls=ls, color="grey", lw=1)
    ax.axvline(0, color="grey", lw=0.6)
    ax.set_yticks(y, g["horizon"])
    ax.set_title(f"{ix}: 90% CI of excess return vs +/-2 and +/-5 bounds")
    ax.set_xlabel("reclaim mean minus drawdown-matched mean (points)")
fig.tight_layout()
