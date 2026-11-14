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
# # N03: Event gallery (descriptive only, no tests)
#
# Every Study 1 primary-specification break (N = 120, K = 10) for NDX and SPX.
# Logic is in `src/gallery.py`; this notebook only calls it and plots.
#
# Panel A uses the Study 1 event lists (always available). Panel B draws price
# windows around each break only if `data/clean/*.csv` are present.

# %%
import sys
from pathlib import Path

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "src" / "gallery.py").exists())
sys.path.insert(0, str(ROOT))

import pandas as pd
import matplotlib.pyplot as plt

from src import gallery as G

pd.set_option("display.width", 160)
COLORS = {"reclaimed, held": "#1baf7a", "reclaimed, retested": "#eb6834",
          "not reclaimed": "#2a78d6", "reclaimed, retest n/a": "#9a998f"}
frames = {ix: G.gallery_frame(ix) for ix in ("NDX", "SPX")}

# %% [markdown]
# ## Outcome summary by category

# %%
for ix, ev in frames.items():
    print(ix)
    print(G.outcome_summary(ev).to_markdown(index=False, floatfmt=".3f"), "\n")

# %% [markdown]
# ## Panel A: outcome profile per event (return from entry close at 0/20/60/120 days)

# %%
for ix, ev in frames.items():
    prof = G.outcome_profiles(ev)
    nr, nc = G.grid_shape(len(ev), 8)
    fig, axes = plt.subplots(nr, nc, figsize=(1.9 * nc, 1.45 * nr), sharex=True, sharey=True)
    for ax in axes.flat:
        ax.set_visible(False)
    for ax, (n, g) in zip(axes.flat, prof.groupby("n", sort=True)):
        ax.set_visible(True)
        oc = g["outcome"].iloc[0]
        ax.plot(g["day"], g["ret"] * 100, marker="o", ms=2.5, color=COLORS[oc])
        ax.axhline(0, color="grey", lw=0.5)
        ax.set_title(g["label"].iloc[0], fontsize=7)
        ax.tick_params(labelsize=6)
    handles = [plt.Line2D([], [], color=c, label=k) for k, c in COLORS.items()]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=8)
    fig.suptitle(f"{ix}: return from entry (%) at day 0/20/60/120, all {len(ev)} breaks", fontsize=10)
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))

# %% [markdown]
# ## Sweep depth vs 120-day return

# %%
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
for ax, (ix, ev) in zip(axes, frames.items()):
    for oc, g in ev.groupby("outcome"):
        ax.scatter(g["sweep_vs_level"] * 100, g["r120"] * 100, s=18, color=COLORS[oc], label=oc)
    ax.axhline(0, color="grey", lw=0.6)
    ax.set_title(f"{ix}: sweep depth vs 120-day return")
    ax.set_xlabel("sweep low vs support (%)")
    ax.set_ylabel("r120 from entry (%)")
axes[0].legend(frameon=False, fontsize=8)
fig.tight_layout()

# %% [markdown]
# ## Panel B: price windows (needs data/clean)

# %%
for ix, ev in frames.items():
    close = G.load_clean_close(ix)
    if close is None:
        print(f"{ix}: data/clean/{G.STUDY1_FILES[ix]} not present; price-window panel skipped.")
        continue
    nr, nc = G.grid_shape(len(ev), 8)
    fig, axes = plt.subplots(nr, nc, figsize=(1.9 * nc, 1.45 * nr), sharex=True)
    for ax in axes.flat:
        ax.set_visible(False)
    for ax, (_, r) in zip(axes.flat, ev.iterrows()):
        ax.set_visible(True)
        w = G.price_window(close, r["break_date"], r["level"])
        ax.plot(w["day"], w["rel"] * 100, color=COLORS[r["outcome"]], lw=1)
        ax.axhline(0, color="grey", lw=0.5, ls="--")
        ax.axvline(0, color="grey", lw=0.5)
        ax.set_title(r["label"], fontsize=7)
        ax.tick_params(labelsize=6)
    fig.suptitle(f"{ix}: close vs broken support (%), days -40..+120 from break", fontsize=10)
    fig.tight_layout()
