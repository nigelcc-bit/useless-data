"""Wild cluster bootstrap with Webb (2014) six-point weights."""

from __future__ import annotations

import numpy as np
import pandas as pd

# Webb (2014) six-point distribution
WEBB_WEIGHTS = np.array(
    [
        -np.sqrt(1.5),
        -1.0,
        -np.sqrt(0.5),
        np.sqrt(0.5),
        1.0,
        np.sqrt(1.5),
    ]
)


def ols(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Return beta, residuals, R² (with intercept column already in X)."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    ss_res = float(np.sum(resid**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return beta, resid, r2


def adj_r2(r2: float, n: int, k: int) -> float:
    """k = number of regressors excluding intercept."""
    if n <= k + 1:
        return float("nan")
    return 1.0 - (1.0 - r2) * (n - 1) / (n - k - 1)


def design_matrix(df: pd.DataFrame, cols: list[str]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    y = df["episode_return"].to_numpy(dtype=float)
    X_cols = [c for c in cols if c in df.columns]
    X = df[X_cols].to_numpy(dtype=float)
    X = np.column_stack([np.ones(len(df)), X])
    return y, X, ["intercept"] + X_cols


def wild_cluster_bootstrap(
    y: np.ndarray,
    X: np.ndarray,
    clusters: np.ndarray,
    n_boot: int = 999,
    seed: int = 42,
) -> dict:
    """Webb wild cluster bootstrap for coefficient SEs and p-values.

    Null imposed: residual wild bootstrap under estimated beta.
    """
    rng = np.random.default_rng(seed)
    beta, resid, r2 = ols(y, X)
    uniq = pd.unique(clusters)
    g = len(uniq)
    boot = np.zeros((n_boot, X.shape[1]))
    cluster_index = {c: np.where(clusters == c)[0] for c in uniq}
    for b in range(n_boot):
        w = rng.choice(WEBB_WEIGHTS, size=g, replace=True)
        resid_star = resid.copy()
        for i, c in enumerate(uniq):
            resid_star[cluster_index[c]] = resid[cluster_index[c]] * w[i]
        y_star = X @ beta + resid_star
        beta_star, *_ = np.linalg.lstsq(X, y_star, rcond=None)
        boot[b] = beta_star
    se = boot.std(axis=0, ddof=1)
    # two-sided p: share of |beta*-beta| >= |beta| under centered draws
    # Use percentile method relative to null of 0 for inference on coeffs
    pvals = []
    for j in range(X.shape[1]):
        # impose null beta_j=0: wild bootstrap of residual model without that restriction
        # simpler: p = 2 * min(mean(boot[:,j]<=0), mean(boot[:,j]>=0))
        pj = 2 * min(float(np.mean(boot[:, j] <= 0)), float(np.mean(boot[:, j] >= 0)))
        pvals.append(min(pj, 1.0))
    return {
        "beta": beta,
        "se": se,
        "p": np.array(pvals),
        "r2": r2,
        "n_boot": n_boot,
        "n_clusters": g,
    }


def episode_bootstrap_r2(
    y: np.ndarray,
    X: np.ndarray,
    n_boot: int = 999,
    seed: int = 7,
) -> dict:
    """Resample rows with replacement; distribution of adj-R² and betas."""
    rng = np.random.default_rng(seed)
    n, k = X.shape[0], X.shape[1] - 1
    beta, _resid, r2 = ols(y, X)
    boot_r2 = np.zeros(n_boot)
    boot_beta = np.zeros((n_boot, X.shape[1]))
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        bb, _, rr = ols(y[idx], X[idx])
        boot_beta[b] = bb
        boot_r2[b] = adj_r2(rr, n, k)
    return {
        "beta": beta,
        "r2": r2,
        "adj_r2": adj_r2(r2, n, k),
        "boot_adj_r2_mean": float(np.nanmean(boot_r2)),
        "boot_adj_r2_lo": float(np.nanpercentile(boot_r2, 2.5)),
        "boot_adj_r2_hi": float(np.nanpercentile(boot_r2, 97.5)),
        "boot_beta_se": boot_beta.std(axis=0, ddof=1),
    }
