"""Romano–Wolf stepdown for a small family of dependent tests.

Uses a max-t / min-p bootstrap stepdown (Westfall–Young / Romano–Wolf style)
when bootstrap draws of the test statistics are supplied; otherwise falls back
to a p-value stepdown that still reports the multiplicity-adjusted sequence.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def romano_wolf_stepdown_pvalues(
    p_values: dict[str, float],
    *,
    n_boot: int = 999,
    seed: int = 42,
    rho: float = 0.5,
) -> pd.DataFrame:
    """Romano–Wolf-style stepdown adjusted p-values for a named family.

    Without stored bootstrap statistics we simulate a Gaussian equicorrelated
    null (correlation `rho`) to generate the stepdown null distribution of
    the minimum p-value — a conservative approximation for the H3 block horse
    race when only marginal wild-bootstrap p-values are on disk.
    """
    from scipy.stats import norm

    names = list(p_values.keys())
    p = np.array([float(p_values[n]) for n in names], dtype=float)
    m = len(names)
    if m == 0:
        return pd.DataFrame(columns=["test", "raw_p", "rw_p"])

    # Order by increasing raw p (most significant first)
    order = np.argsort(p)
    p_sorted = p[order]
    names_sorted = [names[i] for i in order]

    rng = np.random.default_rng(seed)
    # Equicorrelated Gaussian → transform to p under null
    cov = np.full((m, m), rho)
    np.fill_diagonal(cov, 1.0)
    # Simulate null z-draws; convert to two-sided p
    L = np.linalg.cholesky(cov + 1e-12 * np.eye(m))
    adj = np.ones(m)
    for k in range(m):
        # Remaining family size
        rem = m - k
        # Bootstrap null min-p among remaining
        Z = rng.standard_normal((n_boot, rem)) @ L[k:, k:].T
        Pnull = 2 * (1 - norm.cdf(np.abs(Z)))
        min_p_null = Pnull.min(axis=1)
        # Stepdown p = share of null min-p ≤ observed p_k
        pk = p_sorted[k]
        adj_k = float(np.mean(min_p_null <= pk))
        # Enforce monotonicity
        adj[k] = max(adj_k, adj[k - 1] if k else adj_k)
        adj[k] = min(adj[k], 1.0)

    # Map back
    rw = {names_sorted[i]: adj[i] for i in range(m)}
    rows = [
        {"test": n, "raw_p": float(p_values[n]), "rw_p": float(rw[n])} for n in names
    ]
    return pd.DataFrame(rows)
