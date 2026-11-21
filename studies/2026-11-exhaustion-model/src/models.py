"""Bayesian logistic regression (MAP + Laplace/probit predictive), LOEO CV, Brier, Wilson.
PREREGISTRATION Part C5."""
from __future__ import annotations

import itertools

import numpy as np
from scipy.stats import norm

SLOPE_SD = 1.0
INT_SD = 2.5


def _std(Xtr, Xte):
    mu = Xtr.mean(0)
    sd = Xtr.std(0)
    sd[sd == 0] = 1.0
    return (Xtr - mu) / sd, (Xte - mu) / sd


def fit_map(X, y, iters=50):
    """X without intercept, standardised. Returns (beta incl. intercept, posterior cov)."""
    n, k = X.shape
    Z = np.column_stack([np.ones(n), X])
    prec = np.r_[1 / INT_SD ** 2, np.full(k, 1 / SLOPE_SD ** 2)]
    b = np.zeros(k + 1)
    for _ in range(iters):
        eta = np.clip(Z @ b, -30, 30)
        p = 1 / (1 + np.exp(-eta))
        g = Z.T @ (y - p) - prec * b
        H = (Z * (p * (1 - p))[:, None]).T @ Z + np.diag(prec)
        step = np.linalg.solve(H, g)
        b += step
        if np.max(np.abs(step)) < 1e-8:
            break
    eta = np.clip(Z @ b, -30, 30)
    p = 1 / (1 + np.exp(-eta))
    H = (Z * (p * (1 - p))[:, None]).T @ Z + np.diag(prec)
    return b, np.linalg.inv(H)


def predict(b, cov, X):
    Z = np.column_stack([np.ones(len(X)), X])
    mu = Z @ b
    var = np.einsum("ij,jk,ik->i", Z, cov, Z)
    return 1 / (1 + np.exp(-mu / np.sqrt(1 + np.pi * var / 8)))


def fit_predict(Xtr, ytr, Xte):
    if Xtr.shape[1] == 0:
        Ztr, Zte = Xtr, Xte
    else:
        Ztr, Zte = _std(Xtr, Xte)
    b, cov = fit_map(Ztr, ytr)
    return predict(b, cov, Zte), b


def loeo(X, y, groups):
    """Leave-one-episode-out predictions."""
    pred = np.empty(len(y))
    for g in np.unique(groups):
        te = groups == g
        pred[te], _ = fit_predict(X[~te], y[~te], X[te])
    return pred


def brier(p, y):
    return float(np.mean((p - y) ** 2))


def coef(X, y):
    """Standardised coefficients from a full fit (intercept first)."""
    Z, _ = _std(X, X)
    return fit_map(Z, y)[0]


def select_subsets(df, feats, target, groups, max_k=3):
    """Score every subset of size 1..max_k by LOEO Brier. Returns list sorted best first."""
    y = df[target].to_numpy(float)
    out = []
    for k in range(1, max_k + 1):
        for s in itertools.combinations(feats, k):
            X = df[list(s)].to_numpy(float)
            out.append((brier(loeo(X, y, groups), y), s))
    out.sort(key=lambda t: t[0])
    return out


def wilson(k, n, z=1.6449):
    """90% Wilson interval."""
    if n == 0:
        return (np.nan, np.nan)
    ph = k / n
    den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


def bh(p, q=0.10):
    """Benjamini-Hochberg: returns adjusted p-values (NaN kept)."""
    p = np.asarray(p, float)
    ok = ~np.isnan(p)
    adj = np.full_like(p, np.nan)
    pv = p[ok]
    m = len(pv)
    if m == 0:
        return adj
    o = np.argsort(pv)
    r = pv[o] * m / np.arange(1, m + 1)
    r = np.minimum.accumulate(r[::-1])[::-1]
    a = np.empty(m)
    a[o] = np.minimum(r, 1)
    adj[ok] = a
    return adj
