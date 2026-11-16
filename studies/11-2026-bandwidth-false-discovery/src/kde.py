"""2D Gaussian product-kernel KDE, KDE conditional mean, and LOO likelihood CV.

Inputs are assumed to be rank-transformed to normal scores (unit scale on both
axes), so a single bandwidth per axis is enough; no full bandwidth matrix.
A bandwidth argument `h` may be a scalar (same on both axes) or a pair (hx, hy).
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import numpy as np

_CHUNK = 500  # rows per block in pairwise computations (memory ~ CHUNK * n floats)


def _pair(h) -> tuple[float, float]:
    if np.ndim(h) == 0:
        return float(h), float(h)
    hx, hy = h
    return float(hx), float(hy)


def _gauss(u: np.ndarray) -> np.ndarray:
    return np.exp(-0.5 * u * u) / np.sqrt(2.0 * np.pi)


def kde2d(x, y, h, xg=None, yg=None, points=None) -> np.ndarray:
    """Product Gaussian KDE f(u, v) = 1/n sum_i K_hx(u - x_i) K_hy(v - y_i).

    Give either a grid (`xg`, `yg`: 1D arrays) or `points` = (u, v) arrays.
    Grid mode returns an array of shape (len(yg), len(xg)); it uses the
    separability of the product kernel, so cost is O(n * (len(xg) + len(yg))).
    Point mode returns a 1D array of densities at the given points.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    hx, hy = _pair(h)
    n = x.size
    if xg is not None and yg is not None:
        xg = np.asarray(xg, dtype=float)
        yg = np.asarray(yg, dtype=float)
        kx = _gauss((xg[:, None] - x[None, :]) / hx) / hx  # (Gx, n)
        ky = _gauss((yg[:, None] - y[None, :]) / hy) / hy  # (Gy, n)
        return (ky @ kx.T) / n
    if points is not None:
        u, v = (np.asarray(a, dtype=float).ravel() for a in points)
        out = np.empty(u.size)
        for s in range(0, u.size, _CHUNK):
            e = slice(s, s + _CHUNK)
            kx = _gauss((u[e, None] - x[None, :]) / hx) / hx
            ky = _gauss((v[e, None] - y[None, :]) / hy) / hy
            out[e] = (kx * ky).sum(axis=1) / n
        return out
    raise ValueError("Give either xg and yg (grid) or points=(u, v).")


def cond_mean(x_train, y_train, x_eval, h) -> np.ndarray:
    """E[y | x] implied by the product Gaussian KDE.

    Integrating y over the 2D product-kernel density gives the Nadaraya-Watson
    estimator with bandwidth hx on x; hy cancels. If `h` is a pair, hx is used.
    Weights are shifted per evaluation point before exponentiating, so far-tail
    evaluation points do not underflow to 0/0.
    """
    xt = np.asarray(x_train, dtype=float)
    yt = np.asarray(y_train, dtype=float)
    xe = np.asarray(x_eval, dtype=float).ravel()
    hx, _ = _pair(h)
    out = np.empty(xe.size)
    for s in range(0, xe.size, _CHUNK):
        e = slice(s, s + _CHUNK)
        z = ((xe[e, None] - xt[None, :]) / hx) ** 2
        z -= z.min(axis=1, keepdims=True)
        w = np.exp(-0.5 * z)
        out[e] = (w @ yt) / w.sum(axis=1)
    return out


def cond_mean_binned(x_train, y_train, x_eval, h, n_grid: int = 4096) -> np.ndarray:
    """Fast approximation of `cond_mean` by linear binning (Wand 1994 style).

    Training points are linearly binned onto `n_grid` equally spaced nodes; the
    numerator sum K(.) y and denominator sum K(.) are formed at every node by
    direct (not FFT) convolution with the Gaussian kernel, truncated at 8 h, so
    small tail weights carry no FFT round-off. Values at `x_eval` are linearly
    interpolated between nodes. Cost is O(n + n_grid * kernel width).
    The kernel normalising constant cancels in the ratio.
    """
    xt = np.asarray(x_train, dtype=float)
    yt = np.asarray(y_train, dtype=float)
    xe = np.asarray(x_eval, dtype=float).ravel()
    hx, _ = _pair(h)
    lo = min(xt.min(), xe.min())
    hi = max(xt.max(), xe.max())
    grid = np.linspace(lo, hi, n_grid)
    delta = grid[1] - grid[0]
    pos = (xt - lo) / delta
    i0 = np.clip(np.floor(pos).astype(int), 0, n_grid - 2)
    w1 = pos - i0
    w0 = 1.0 - w1
    cnt = np.bincount(i0, w0, n_grid) + np.bincount(i0 + 1, w1, n_grid)
    ysum = np.bincount(i0, w0 * yt, n_grid) + np.bincount(i0 + 1, w1 * yt, n_grid)
    half = min(int(np.ceil(8.0 * hx / delta)), n_grid - 1)
    ker = np.exp(-0.5 * (np.arange(-half, half + 1) * delta / hx) ** 2)
    den = np.convolve(cnt, ker, mode="full")[half : half + n_grid]
    num = np.convolve(ysum, ker, mode="full")[half : half + n_grid]
    with np.errstate(invalid="ignore", divide="ignore"):
        m_grid = num / den
    ok = np.isfinite(m_grid) & (den > 0)
    return np.interp(xe, grid[ok], m_grid[ok])


def loo_loglik(x, y, hs) -> np.ndarray:
    """Mean leave-one-out log-likelihood of the 2D KDE for each common bandwidth in `hs`.

    Pairwise squared distances are computed once per block and reused for all h.
    Each point's log density is a shifted log-sum-exp (shift = squared distance
    to its nearest other point), so isolated points give a large negative but
    finite value instead of underflowing to -inf. Blocks run in threads (numpy
    releases the GIL inside the kernels).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    hs = np.asarray(hs, dtype=float)
    n = x.size
    xs = x.astype(np.float32)
    ys = y.astype(np.float32)
    logsum = np.zeros((hs.size, n))

    def block(s: int) -> None:
        e = slice(s, min(s + _CHUNK, n))
        d2 = (xs[e, None] - xs[None, :]) ** 2 + (ys[e, None] - ys[None, :]) ** 2
        d2[np.arange(e.stop - e.start), np.arange(e.start, e.stop)] = np.inf  # leave self out
        dmin = d2.min(axis=1, keepdims=True)
        d2 -= dmin
        for k, h in enumerate(hs):
            c = -0.5 / h**2
            ssum = np.exp(d2 * np.float32(c)).sum(axis=1, dtype=np.float64)
            logsum[k, e] = np.log(ssum) + c * dmin[:, 0].astype(np.float64)

    with ThreadPoolExecutor(max_workers=os.cpu_count() or 1) as ex:
        list(ex.map(block, range(0, n, _CHUNK)))
    log_norm = np.log((n - 1) * 2.0 * np.pi * hs**2)
    return (logsum - log_norm[:, None]).mean(axis=1)


def lcv_bandwidth(x, y, max_n: int = 20_000, seed: int = 7, return_path: bool = False):
    """Leave-one-out likelihood cross-validated common bandwidth.

    Subsamples to at most `max_n` points (fixed `seed`). Searches a coarse log
    grid of 13 values on [0.02, 2.0] (step ratio ~1.47), then a fine log grid of
    13 values between the neighbours of the coarse optimum (step ratio ~1.07). Returns the best h (and optionally the
    evaluated (h, score) path). Note: with a subsample of m < n points the CV
    bandwidth is the one optimal for m points; it is not rescaled to n.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size > max_n:
        idx = np.random.default_rng(seed).choice(x.size, size=max_n, replace=False)
        x, y = x[idx], y[idx]
    coarse = np.geomspace(0.02, 2.0, 13)
    sc = loo_loglik(x, y, coarse)
    k = int(np.nanargmax(sc))
    lo, hi = coarse[max(k - 1, 0)], coarse[min(k + 1, coarse.size - 1)]
    fine = np.geomspace(lo, hi, 13)
    sf = loo_loglik(x, y, fine)
    h_best = float(fine[int(np.nanargmax(sf))])
    if return_path:
        hs = np.concatenate([coarse, fine])
        scores = np.concatenate([sc, sf])
        order = np.argsort(hs)
        return h_best, hs[order], scores[order]
    return h_best
