"""In-sample "pattern hunter": best contiguous x-pocket by KDE conditional mean.

Procedure (PREREG.md, Method):
1. Fit E[y | x] with the KDE conditional mean at bandwidth h.
2. Sort observations by x and cut them into `n_bins` equal-count bins.
   Score each bin by the average fitted E[y | x] of its observations.
3. Among all contiguous runs of bins holding at least `min_frac` of the
   observations, pick the run with the highest observation-weighted average
   fitted E[y | x].
4. Trade it: long the pocket, short everything else. Per period, the return is
   mean(y inside) - mean(y outside). The t-stat is the Newey-West (Bartlett,
   5 lags) t of the mean of that series.

By default E[y | x] is evaluated exactly at `n_eval` quantiles of x and linearly
interpolated to the observations (O(n_eval * n) instead of O(n^2)); a
precomputed fit at every observation can be passed instead via `m_obs`.
Costs are not applied here (estimator only).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import statsmodels.api as sm

from .kde import cond_mean


@dataclass
class Pocket:
    lo: float                 # pocket lower x bound (inclusive)
    hi: float                 # pocket upper x bound (inclusive)
    frac: float               # share of observations inside
    score: float              # average fitted E[y | x] inside the pocket
    returns: np.ndarray       # long-short series, one value per period
    periods: np.ndarray       # period labels for `returns`
    t_nw: float               # Newey-West t of mean(returns)
    mean: float               # mean(returns)


def nw_tstat(r: np.ndarray, lags: int = 5) -> float:
    """t-stat of the mean of r with Newey-West (Bartlett) standard errors."""
    r = np.asarray(r, dtype=float)
    fit = sm.OLS(r, np.ones_like(r)).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(fit.tvalues[0])


def _best_run(bin_sum: np.ndarray, bin_cnt: np.ndarray, min_count: int) -> tuple[int, int]:
    """Indices [i, j] (inclusive) of the contiguous bin run with >= min_count obs
    and the highest count-weighted mean of the per-obs scores."""
    cs = np.concatenate([[0.0], np.cumsum(bin_sum)])
    cc = np.concatenate([[0], np.cumsum(bin_cnt)])
    i = np.arange(bin_sum.size)[:, None]
    j = np.arange(bin_sum.size)[None, :]
    cnt = cc[j + 1] - cc[i]
    with np.errstate(invalid="ignore", divide="ignore"):
        avg = (cs[j + 1] - cs[i]) / cnt
    avg[(j < i) | (cnt < min_count)] = -np.inf
    k = int(np.argmax(avg))
    return divmod(k, bin_sum.size)


def default_n_bins(min_frac: float) -> int:
    """PREREG deviation (16 Nov 2026): n_bins = max(200, 4 / min_frac)."""
    return int(max(200, int(np.ceil(4.0 / min_frac - 1e-9))))


def best_pocket(x, y, h, min_frac: float = 0.05, dates=None,
                n_bins: int | None = None, n_eval: int = 400, lags: int = 5,
                m_obs=None) -> Pocket:
    """Find the best x-pocket in-sample and return its long-short series and NW t.

    `dates`: period label per observation (e.g. trading date). The long-short
    return for each period is mean(y in pocket) - mean(y outside) among that
    period's observations; periods with nobody inside or outside are dropped.
    If `dates` is None, each observation is its own period and the series is
    r_i = n * y_i * (1[in]/n_in - 1[out]/n_out), whose mean equals the
    inside-minus-outside spread.

    `n_bins`: None means the deviation rule max(200, 4 / min_frac); for
    min_frac = 0.05 this is 200, the value used before the deviation.
    `m_obs`: optional precomputed fitted E[y|x] at every observation (e.g. from
    kde.cond_mean_binned), so one fit can be shared across pocket sizes. If
    None, the exact cond_mean at `n_eval` quantiles is interpolated, as before.
    """
    if n_bins is None:
        n_bins = default_n_bins(min_frac)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = x.size

    # 1. Fitted E[y|x] at quantiles of x, interpolated to every observation.
    if m_obs is None:
        q = np.quantile(x, np.linspace(0.0, 1.0, n_eval))
        m_obs = np.interp(x, q, cond_mean(x, y, q, h))
    else:
        m_obs = np.asarray(m_obs, dtype=float)

    # 2. Equal-count bins in x order.
    order = np.argsort(x, kind="stable")
    bin_of_rank = np.minimum((np.arange(n) * n_bins) // n, n_bins - 1)
    bin_sum = np.bincount(bin_of_rank, weights=m_obs[order], minlength=n_bins)
    bin_cnt = np.bincount(bin_of_rank, minlength=n_bins)

    # 3. Best contiguous run with at least min_frac of observations.
    i, j = _best_run(bin_sum, bin_cnt, int(np.ceil(min_frac * n)))
    ranks_in = (bin_of_rank >= i) & (bin_of_rank <= j)
    inside = np.zeros(n, dtype=bool)
    inside[order[ranks_in]] = True
    xs_in = x[inside]
    lo, hi = float(xs_in.min()), float(xs_in.max())
    score = float(m_obs[inside].mean())

    # 4. Long-short series.
    if dates is None:
        n_in = inside.sum()
        n_out = n - n_in
        r = n * y * np.where(inside, 1.0 / n_in, -1.0 / n_out)
        periods = np.arange(n)
    else:
        codes, periods = _factorize(np.asarray(dates))
        k = periods.size
        s_in = np.bincount(codes, weights=y * inside, minlength=k)
        c_in = np.bincount(codes, weights=inside.astype(float), minlength=k)
        s_out = np.bincount(codes, weights=y * ~inside, minlength=k)
        c_out = np.bincount(codes, weights=(~inside).astype(float), minlength=k)
        ok = (c_in > 0) & (c_out > 0)
        r = s_in[ok] / c_in[ok] - s_out[ok] / c_out[ok]
        periods = periods[ok]

    return Pocket(lo=lo, hi=hi, frac=float(inside.mean()), score=score,
                  returns=r, periods=periods, t_nw=nw_tstat(r, lags), mean=float(r.mean()))


def _factorize(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Codes in sorted order of unique labels (so the series is in time order)."""
    uniq, codes = np.unique(a, return_inverse=True)
    return codes, uniq
