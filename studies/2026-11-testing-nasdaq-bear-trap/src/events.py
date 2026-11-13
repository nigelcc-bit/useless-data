"""Event engine for failed-breakdown ("bear trap") studies.

Reproduces the Study 1 primary specification exactly (Appendix A of
docs/Study1_Bear_Trap_Full_Report.md) and generalises it for Tier 1 work:

    Support      L(t) = min{C(t-N), ..., C(t-1)}, argmin at least `min_age` days before t
    Break        C(t) < L(t), and no accepted break in the previous `cooldown` days
    Reclaim      r = first t+k, 1 <= k <= K, with C(t+k) > L(t)
    Sweep low    S = min{C(t), ..., C(r)}   (or to t+K if no reclaim)
    Retest       any C(r+j) < S, j = 1..retest_window (evaluated only with full data)
    Returns      C(e+h)/C(e) - 1, e = r if reclaimed else t+K

All indices are integer positions into the close array. Every outcome that
needs future data is NaN unless the full window exists (no partial windows).

Design choices that Appendix A does not pin down (documented so the
regression test can arbitrate):
  * Ties in the support window: the MOST RECENT occurrence of the minimum is
    used for the age rule (conservative). Ties are essentially absent in
    index closes.
  * Cooldown: a break at t is accepted only if t - last_accepted_break > cooldown.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, replace
import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view


@dataclass(frozen=True)
class Spec:
    N: int = 120                 # support lookback (trading days)
    K: int = 10                  # reclaim window
    min_age: int = 10            # established-low rule
    cooldown: int = 20           # min spacing between accepted breaks
    retest_window: int = 60
    horizons: tuple = (20, 60, 120)
    high_lookback: int = 120     # for drawdown-at-break and the 120d high H
    dd_threshold: float = -0.20  # "went on to a 20% drawdown"
    outcome_window: int = 120    # window for dd20 / regained-high outcomes
    survival_max: int = 250      # follow-up for time-to-event columns
    level: str = "min"           # "min" (swing low) or "q05", "q10", "q20" (trailing quantile pseudo-levels)

    def with_(self, **kw) -> "Spec":
        return replace(self, **kw)

    def as_dict(self) -> dict:
        return asdict(self)


PRIMARY = Spec()


# ----------------------------------------------------------------------------
# Level construction
# ----------------------------------------------------------------------------
def support_levels(C: np.ndarray, spec: Spec):
    """Return (L, age, valid) arrays aligned to t.

    L[t]   level computed from C[t-N .. t-1]
    age[t] t minus the index of the (most recent) minimum; NaN for quantile levels
    valid  True where the level is defined
    """
    n, N = len(C), spec.N
    L = np.full(n, np.nan)
    age = np.full(n, np.nan)
    if n <= N:
        return L, age, np.zeros(n, bool)
    W = sliding_window_view(C[:-1], N)          # W[i] = C[i : i+N]  -> level for t = i+N
    t_idx = np.arange(N, n)
    if spec.level == "min":
        L[N:] = W.min(axis=1)
        last_argmin = N - 1 - np.argmin(W[:, ::-1], axis=1)   # most recent occurrence
        age[N:] = N - last_argmin                              # t - (i + argmin)
    elif spec.level.startswith("q"):
        q = int(spec.level[1:]) / 100.0
        L[N:] = np.quantile(W, q, axis=1)
    else:
        raise ValueError(f"unknown level {spec.level}")
    valid = ~np.isnan(L)
    return L, age, valid


def trailing_high(C: np.ndarray, lookback: int) -> np.ndarray:
    """max{C(t-lookback+1), ..., C(t)} (includes today)."""
    return pd.Series(C).rolling(lookback, min_periods=lookback).max().to_numpy()


def realized_vol(C: np.ndarray, window: int = 20) -> np.ndarray:
    """Annualised close-to-close vol over the `window` returns ending at t."""
    r = np.diff(np.log(C), prepend=np.nan)
    return pd.Series(r).rolling(window, min_periods=window).std().to_numpy() * np.sqrt(252)


# ----------------------------------------------------------------------------
# Event detection
# ----------------------------------------------------------------------------
def find_breaks(C: np.ndarray, spec: Spec = PRIMARY) -> list[tuple[int, float, float]]:
    """Accepted break days as (t, level, age)."""
    L, age, valid = support_levels(C, spec)
    if spec.level == "min":
        cand = valid & (C < L) & (age >= spec.min_age)
    else:
        prev_ok = np.r_[False, (C[:-1] >= L[:-1])]   # first crossing below a quantile level
        cand = valid & (C < L) & prev_ok
    out, last = [], -10**9
    for t in np.flatnonzero(cand):
        if t - last > spec.cooldown:
            out.append((int(t), float(L[t]), float(age[t])))
            last = t
    return out


def _first_true(mask: np.ndarray) -> int:
    idx = np.flatnonzero(mask)
    return int(idx[0]) if idx.size else -1


def detect_events(close: pd.Series | np.ndarray, spec: Spec = PRIMARY,
                  rv_window: int = 20) -> pd.DataFrame:
    """Run the full event engine. Returns one row per accepted break."""
    if isinstance(close, pd.Series):
        dates = close.index
        C = close.to_numpy(dtype=float)
    else:
        C = np.asarray(close, dtype=float)
        dates = pd.RangeIndex(len(C))
    n = len(C)
    H_arr = trailing_high(C, spec.high_lookback)
    RV = realized_vol(C, rv_window)
    rows = []
    for t, L, age in find_breaks(C, spec):
        K = spec.K
        # --- reclaim
        k_end = min(t + K, n - 1)
        r = -1
        if k_end > t:
            j = _first_true(C[t + 1:k_end + 1] > L)
            r = t + 1 + j if j >= 0 else -1
        reclaimed = r >= 0
        complete_k = (t + K) <= n - 1
        if not reclaimed and not complete_k:
            # Unresolved: still inside the reclaim window at data end
            e = -1
        else:
            e = r if reclaimed else t + K
        sweep_end = r if reclaimed else min(t + K, n - 1)
        S = float(C[t:sweep_end + 1].min())
        H = float(H_arr[t]) if not np.isnan(H_arr[t]) else np.nan

        row = dict(
            t=t, break_date=dates[t], level=L, age=age,
            break_vs_level=C[t] / L - 1, sweep_low=S, sweep_vs_level=S / L - 1,
            dd_at_break=C[t] / H - 1 if H == H else np.nan, high_120=H,
            rv20_at_break=RV[t],
            reclaimed=reclaimed if (reclaimed or complete_k) else np.nan,
            entry=e, entry_date=dates[e] if e >= 0 else pd.NaT,
            entry_close=C[e] if e >= 0 else np.nan,
        )
        # --- forward returns & worst close
        for h in spec.horizons:
            row[f"r{h}"] = C[e + h] / C[e] - 1 if (e >= 0 and e + h <= n - 1) else np.nan
        w = spec.retest_window
        row[f"worst{w}"] = (C[e + 1:e + w + 1].min() / C[e] - 1) if (e >= 0 and e + w <= n - 1) else np.nan
        # --- retest (reclaimed only, full window)
        if reclaimed and r + w <= n - 1:
            row["retest"] = bool((C[r + 1:r + w + 1] < S).any())
        else:
            row["retest"] = np.nan
        # --- dd20 / regained high (full outcome window only)
        ow = spec.outcome_window
        if e >= 0 and e + ow <= n - 1 and H == H:
            fut = C[e + 1:e + ow + 1]
            row["dd20"] = bool((fut / H - 1 <= spec.dd_threshold).any())
            row["regained_high"] = bool((fut >= H).any())
        else:
            row["dd20"] = np.nan
            row["regained_high"] = np.nan
        # --- time-to-event columns for survival analysis (from entry)
        if e >= 0:
            fut = C[e + 1:min(e + spec.survival_max, n - 1) + 1]
            follow = len(fut)
            j_rt = _first_true(fut < S) if reclaimed else -1
            j_hi = _first_true(fut >= H) if H == H else -1
            row["follow_days"] = follow
            row["t_retest"] = j_rt + 1 if j_rt >= 0 else follow
            row["e_retest"] = int(j_rt >= 0) if reclaimed else np.nan
            row["t_high"] = j_hi + 1 if j_hi >= 0 else follow
            row["e_high"] = int(j_hi >= 0)
        else:
            row.update(follow_days=0, t_retest=np.nan, e_retest=np.nan, t_high=np.nan, e_high=np.nan)
        rows.append(row)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["reclaim_date"] = np.where(df["reclaimed"] == True, df["entry_date"], pd.NaT)  # noqa: E712
    return df


# ----------------------------------------------------------------------------
# Fast summary for simulation loops
# ----------------------------------------------------------------------------
def path_stats(C: np.ndarray, spec: Spec = PRIMARY) -> dict:
    """Reclaim rate, retest rate and counts for one price path (no returns)."""
    n = len(C)
    br = find_breaks(C, spec)
    n_res = n_rec = n_rt_obs = n_rt = n_deep = 0
    for t, L, _ in br:
        K = spec.K
        if t + K > n - 1:
            k_end = n - 1
            j = _first_true(C[t + 1:k_end + 1] > L) if k_end > t else -1
            if j < 0:
                continue                      # unresolved at data end
        else:
            j = _first_true(C[t + 1:t + K + 1] > L)
        n_res += 1
        if j < 0:
            continue
        r = t + 1 + j
        n_rec += 1
        S = C[t:r + 1].min()
        if S / L - 1 <= -0.015:
            n_deep += 1
        w = spec.retest_window
        if r + w <= n - 1:
            n_rt_obs += 1
            n_rt += bool((C[r + 1:r + w + 1] < S).any())
    return dict(
        n_breaks=n_res,
        reclaim_rate=n_rec / n_res if n_res else np.nan,
        retest_rate=n_rt / n_rt_obs if n_rt_obs else np.nan,
        deep_share=n_deep / n_rec if n_rec else np.nan,
        breaks_per_year=n_res / (n / 252),
    )


# ----------------------------------------------------------------------------
# Tier 1-B: second-sweep events
# ----------------------------------------------------------------------------
def second_sweep_events(close: pd.Series, events: pd.DataFrame, spec: Spec = PRIMARY,
                        b1_window: int = 20) -> pd.DataFrame:
    """Derive second-sweep entries from first-reclaim events.

    B1 'second reclaim'  : after the first reclaim r1 a retest occurs (first close < S1 at u,
                           u within retest_window). Entry = first close > L within b1_window days of u.
    B2 'held retest'     : after r1 the first close back below L occurs at p (within retest_window)
                           before any close < S1. Entry = first close > L within K days of p,
                           provided min(C[p..entry]) > S1 (a higher low).
    """
    C = close.to_numpy(float)
    dates = close.index
    n = len(C)
    w = spec.retest_window
    rows = []
    for _, ev in events.iterrows():
        if ev["reclaimed"] is not True and ev["reclaimed"] != 1:
            continue
        r1, L, S1 = int(ev["entry"]), ev["level"], ev["sweep_low"]
        seg = C[r1 + 1:min(r1 + w, n - 1) + 1]
        u_rel = _first_true(seg < S1)
        p_rel = _first_true(seg < L)
        # ---- B1
        if u_rel >= 0:
            u = r1 + 1 + u_rel
            seg2 = C[u + 1:min(u + b1_window, n - 1) + 1]
            j = _first_true(seg2 > L)
            if j >= 0:
                rows.append(_entry_row("B1", ev, u + 1 + j, C, dates, spec, trigger=u,
                                       second_low=C[u:u + 1 + j + 1].min()))
        # ---- B2 (pullback below L that happens before any close < S1)
        if p_rel >= 0 and (u_rel < 0 or p_rel < u_rel):
            p = r1 + 1 + p_rel
            seg3 = C[p + 1:min(p + spec.K, n - 1) + 1]
            j = _first_true(seg3 > L)
            if j >= 0:
                e = p + 1 + j
                lo = C[p:e + 1].min()
                if lo > S1:
                    rows.append(_entry_row("B2", ev, e, C, dates, spec, trigger=p, second_low=lo))
    return pd.DataFrame(rows)


def _entry_row(kind, ev, e, C, dates, spec, trigger, second_low):
    n = len(C)
    row = dict(kind=kind, break_date=ev["break_date"], first_entry_date=ev["entry_date"],
               trigger_date=dates[trigger], entry=e, entry_date=dates[e], level=ev["level"],
               sweep_low=ev["sweep_low"], second_low=second_low,
               second_low_vs_level=second_low / ev["level"] - 1, dd_at_break=ev["dd_at_break"])
    for h in spec.horizons:
        row[f"r{h}"] = C[e + h] / C[e] - 1 if e + h <= n - 1 else np.nan
    w = spec.retest_window
    row[f"worst{w}"] = C[e + 1:e + w + 1].min() / C[e] - 1 if e + w <= n - 1 else np.nan
    row[f"below_second_low_{w}d"] = bool((C[e + 1:e + w + 1] < second_low).any()) if e + w <= n - 1 else np.nan
    return row
