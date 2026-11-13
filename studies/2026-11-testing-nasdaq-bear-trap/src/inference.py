"""Inference helpers: drawdown-matched benchmark, placebo test, Wilson CI,
cluster bootstrap, stationary block bootstrap indices."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from .events import trailing_high


# ----------------------------------------------------------------------------
# Benchmark pool
# ----------------------------------------------------------------------------
def drawdown_pool(close: pd.Series, horizons=(20, 60, 120), lookback=120,
                  lo=-0.20, hi=-0.05) -> pd.DataFrame:
    """Forward returns on every day the index closed lo..hi below its trailing high.

    Matches Study 1: dd = C / max(C[t-119..t]) - 1, pool = lo <= dd <= hi.
    """
    C = close.to_numpy(float)
    H = trailing_high(C, lookback)
    dd = C / H - 1
    mask = (dd >= lo) & (dd <= hi)
    out = pd.DataFrame({"dd": dd}, index=close.index)
    for h in horizons:
        fwd = np.full(len(C), np.nan)
        fwd[:-h] = C[h:] / C[:-h] - 1
        out[f"r{h}"] = fwd
    return out[mask]


def unconditional_mean(close: pd.Series, h: int) -> float:
    C = close.to_numpy(float)
    return float(np.nanmean(C[h:] / C[:-h] - 1))


# ----------------------------------------------------------------------------
# Placebo test (Study 1 section 6.5)
# ----------------------------------------------------------------------------
def placebo_p(event_rets, pool_rets, B=5000, seed=7) -> float:
    """Share of random same-size draws (with replacement) from the pool whose mean >= event mean."""
    x = np.asarray(event_rets, float)
    x = x[~np.isnan(x)]
    pool = np.asarray(pool_rets, float)
    pool = pool[~np.isnan(pool)]
    if x.size == 0 or pool.size == 0:
        return np.nan
    rng = np.random.default_rng(seed)
    draws = rng.choice(pool, size=(B, x.size), replace=True).mean(axis=1)
    return float((draws >= x.mean()).mean())


def stratified_placebo_p(event_rets_by_group: dict, pool_by_group: dict, B=5000, seed=7) -> float:
    """Placebo where each group's (market's) events are matched by draws from that group's pool."""
    rng = np.random.default_rng(seed)
    obs_parts, sims = [], np.zeros(B)
    total = 0
    for g, ev in event_rets_by_group.items():
        ev = np.asarray(ev, float)
        ev = ev[~np.isnan(ev)]
        pool = np.asarray(pool_by_group[g], float)
        pool = pool[~np.isnan(pool)]
        if ev.size == 0 or pool.size == 0:
            continue
        obs_parts.append(ev.sum())
        sims += rng.choice(pool, size=(B, ev.size), replace=True).sum(axis=1)
        total += ev.size
    if total == 0:
        return np.nan
    obs = sum(obs_parts) / total
    return float((sims / total >= obs).mean())


# ----------------------------------------------------------------------------
# Proportions and clustered uncertainty
# ----------------------------------------------------------------------------
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (centre - half, centre + half)


def cluster_bootstrap_ci(values, clusters, B=5000, seed=7, alpha=0.05, stat=np.mean):
    """Percentile CI for `stat` resampling whole clusters with replacement."""
    v = pd.Series(np.asarray(values, float))
    c = pd.Series(np.asarray(clusters))
    keep = ~v.isna()
    v, c = v[keep].to_numpy(), c[keep].to_numpy()
    if v.size == 0:
        return (np.nan, np.nan, 0)
    groups = [v[c == g] for g in pd.unique(c)]
    G = len(groups)
    rng = np.random.default_rng(seed)
    stats = np.empty(B)
    for b in range(B):
        pick = rng.integers(0, G, G)
        stats[b] = stat(np.concatenate([groups[i] for i in pick]))
    lo, hi = np.quantile(stats, [alpha / 2, 1 - alpha / 2])
    return (float(lo), float(hi), G)


def two_sided_percentile_p(obs: float, null_draws) -> float:
    """Two-sided p from a simulated null distribution (with +1 correction)."""
    d = np.asarray(null_draws, float)
    d = d[~np.isnan(d)]
    if d.size == 0 or np.isnan(obs):
        return np.nan
    lo = (np.sum(d <= obs) + 1) / (d.size + 1)
    hi = (np.sum(d >= obs) + 1) / (d.size + 1)
    return float(min(1.0, 2 * min(lo, hi)))


# ----------------------------------------------------------------------------
# Stationary bootstrap (Politis and Romano 1994)
# ----------------------------------------------------------------------------
def stationary_bootstrap_idx(n_src: int, n_out: int, mean_block: float, rng) -> np.ndarray:
    """Indices into a source array, blocks of geometric length with given mean, circular wrap."""
    p = 1.0 / mean_block
    idx = np.empty(n_out, dtype=np.int64)
    idx[0] = rng.integers(n_src)
    jumps = rng.random(n_out) < p
    starts = rng.integers(0, n_src, n_out)
    for i in range(1, n_out):
        idx[i] = starts[i] if jumps[i] else (idx[i - 1] + 1) % n_src
    return idx


def bh_fdr(pvals, q=0.05):
    """Benjamini-Hochberg: returns boolean reject array."""
    p = np.asarray(pvals, float)
    m = p.size
    order = np.argsort(p)
    thresh = q * (np.arange(1, m + 1) / m)
    passed = p[order] <= thresh
    k = np.max(np.flatnonzero(passed)) + 1 if passed.any() else 0
    rej = np.zeros(m, bool)
    rej[order[:k]] = True
    return rej
