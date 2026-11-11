"""H2 — Builder-supplier spread is a mean-reverting factor, not beta.

Construction (spec §H2):
  - Daily EW supplier basket and EW builder basket (taxonomy §4).
  - Suppliers = AI-chain layers excluding builders (exclude non_ai_control).
  - Beta-neutralise: regress each basket on SPY over trailing 126d;
    residual spread = supplier residual − builder residual.
  - Sample: 2023-01-01 → present (AI capex cycle).

Inference:
  - Lo–MacKinlay VR with heteroskedasticity-robust z*(q); Chow–Denning joint.
  - −2.5σ events use rolling mean/sd ending at t−1 (shift 1), matching H1 rule B.
  - Forward design frozen in RESULTS.md before this module computes forwards.

Conditioning (Pre-P1 revision d): HY OAS (BAMLH0A0HYM2) above/below lagged
126d median. Ingested FRED HY OAS begins 2023-11-07.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config_io import ROOT
from src.features.layer import layer_assignments

STATUS = "RUNNING"
NULL = "After beta control, supplier-minus-builder spread is a random walk."
FALSIFIER = "Variance ratio ≈ 1 and no significant forward spread return."

REGIME_PRIMARY_PRE_CRWV = "BAMLH0A0HYM2"
START = "2023-01-01"
BETA_WINDOW = 126
SIGMA_WINDOW = 126
EVENT_THRESHOLD_SIGMA = -2.5
VR_HORIZONS = (2, 5, 10, 21)
FWD_HORIZONS = (5, 21, 63)
DECLUSTER_BLOCK = 21
ROUND_TRIP_COST = 0.003  # 30bp
N_BOOT = 999
SEED = 5276


def _builder_supplier_tickers() -> tuple[list[str], list[str]]:
    layers = layer_assignments()
    builders = sorted(layers.loc[layers["layer"] == "builders", "ticker"].tolist())
    suppliers = sorted(
        layers.loc[
            ~layers["layer"].isin(["builders", "non_ai_control"]), "ticker"
        ].tolist()
    )
    return builders, suppliers


def _ew_returns(adj: pd.DataFrame, tickers: list[str]) -> pd.Series:
    cols = [t for t in tickers if t in adj.columns]
    rets = adj[cols].sort_index().pct_change()
    ew = rets.mean(axis=1, skipna=True)
    n = rets.notna().sum(axis=1)
    return ew.where(n > 0).rename("ew")


def beta_neutral_residual(
    basket: pd.Series, market: pd.Series, window: int = BETA_WINDOW
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Trailing OLS residual; also return rolling alpha and beta (as-of t, fit on t-W:t-1...t-1 only via window ending before t).

    Fit at index i uses observations [i-window, i) — i.e. through t−1 when
    predicting residual at t (standard rolling OLS for day-t residual).
    """
    df = pd.concat([basket.rename("y"), market.rename("m")], axis=1).dropna()
    resid = pd.Series(index=df.index, dtype=float)
    alpha = pd.Series(index=df.index, dtype=float)
    beta = pd.Series(index=df.index, dtype=float)
    y = df["y"].to_numpy()
    m = df["m"].to_numpy()
    for i in range(window, len(df)):
        yy = y[i - window : i]
        mm = m[i - window : i]
        X = np.column_stack([np.ones(window), mm])
        coef = np.linalg.lstsq(X, yy, rcond=None)[0]
        alpha.iloc[i] = coef[0]
        beta.iloc[i] = coef[1]
        resid.iloc[i] = y[i] - (coef[0] + coef[1] * m[i])
    return resid, alpha, beta


def variance_ratio_hetero(x: pd.Series, q: int) -> dict:
    """Lo–MacKinlay overlapping VR with heteroskedasticity-robust z*(q).

    δ̂_j = n * Σ_{t=j+1}^n (r_t−μ)²(r_{t−j}−μ)² / [Σ (r_t−μ)²]²
    θ̂ = 4 Σ_{j=1}^{q−1} (1−j/q)² δ̂_j
    z* = (VR−1) / √θ̂
    """
    from scipy.stats import norm

    r = x.dropna().to_numpy(dtype=float)
    n = len(r)
    out = {
        "q": q,
        "vr": float("nan"),
        "z_homo": float("nan"),
        "p_homo": float("nan"),
        "z_star": float("nan"),
        "p_star": float("nan"),
        "theta": float("nan"),
        "phi_homo": float("nan"),
        "n": n,
    }
    if n < q * 4:
        return out
    mu = r.mean()
    # overlapping q-period returns
    rq = np.array([r[i - q + 1 : i + 1].sum() for i in range(q - 1, n)])
    var1 = np.sum((r - mu) ** 2) / (n - 1)
    varq = np.sum((rq - q * mu) ** 2) / (len(rq) - 1)
    vr = (varq / q) / var1 if var1 > 0 else float("nan")
    out["vr"] = float(vr)

    # Homoskedastic (kept for audit only; decision uses z*)
    phi = (2 * (2 * q - 1) * (q - 1)) / (3 * q * n)
    out["phi_homo"] = float(phi)
    z_h = (vr - 1.0) / np.sqrt(phi) if phi > 0 and np.isfinite(vr) else float("nan")
    out["z_homo"] = float(z_h)
    out["p_homo"] = float(2 * norm.sf(abs(z_h))) if np.isfinite(z_h) else float("nan")

    # Heteroskedasticity-robust
    e = r - mu
    sse = float(np.sum(e**2))
    if sse <= 0 or q < 2:
        # q=1 is trivial VR=1; for q>=2 need at least one lag
        if q == 1:
            out["z_star"] = 0.0
            out["p_star"] = 1.0
            out["theta"] = 0.0
        return out
    theta = 0.0
    for j in range(1, q):
        # δ̂_j
        num = float(np.sum((e[j:] ** 2) * (e[:-j] ** 2)))
        delta_j = n * num / (sse**2)
        theta += 4.0 * ((1.0 - j / q) ** 2) * delta_j
    out["theta"] = float(theta)
    # z* = √n (VR−1) / √θ̂   (θ̂ = asym. var of √n(VR−1))
    z_star = (
        np.sqrt(n) * (vr - 1.0) / np.sqrt(theta)
        if theta > 0 and np.isfinite(vr)
        else float("nan")
    )
    out["z_star"] = float(z_star)
    out["p_star"] = (
        float(2 * norm.sf(abs(z_star))) if np.isfinite(z_star) else float("nan")
    )
    return out


def chow_denning(vr_rows: list[dict]) -> dict:
    """Chow–Denning joint test: CD = max |z*(q)|; SMM asymptotic p-value.

    p ≈ 1 − [2Φ(CD) − 1]^m  (studentized maximum modulus, large-n).
    """
    from scipy.stats import norm

    zs = [abs(r["z_star"]) for r in vr_rows if np.isfinite(r.get("z_star", np.nan))]
    m = len(zs)
    if not zs:
        return {"cd_stat": float("nan"), "m": 0, "p_smm": float("nan"), "argmax_q": None}
    cd = float(max(zs))
    argmax_q = int(vr_rows[int(np.argmax([abs(r["z_star"]) for r in vr_rows]))]["q"])
    # asymptotic SMM p-value
    p = float(1.0 - (2.0 * norm.cdf(cd) - 1.0) ** m)
    return {"cd_stat": cd, "m": m, "p_smm": p, "argmax_q": argmax_q}


def causal_z(spread: pd.Series, window: int = SIGMA_WINDOW) -> pd.Series:
    """z at t uses mean/sd of spread through t−1 only (H1 rule B)."""
    # rolling at t includes t; shift(1) → window ends at t−1
    mu = spread.rolling(window, min_periods=window).mean().shift(1)
    sd = spread.rolling(window, min_periods=window).std(ddof=1).shift(1)
    return ((spread - mu) / sd).rename("z")


def decluster_on_calendar(
    event_dates: pd.DatetimeIndex, calendar: pd.DatetimeIndex, block: int = DECLUSTER_BLOCK
) -> list[pd.Timestamp]:
    """First event per non-overlapping block of `block` sessions on `calendar`."""
    cal = pd.DatetimeIndex(calendar).sort_values()
    pos = {d: i for i, d in enumerate(cal)}
    kept: list[pd.Timestamp] = []
    next_ok = -1
    for d in sorted(event_dates):
        if d not in pos:
            continue
        i = pos[d]
        if i >= next_ok:
            kept.append(pd.Timestamp(d))
            next_ok = i + block
    return kept


def newey_west_mean_se(x: np.ndarray, lag: int) -> tuple[float, float]:
    """Mean and Newey–West SE of the mean (lag = horizon)."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 2:
        return (float(x.mean()) if n else float("nan"), float("nan"))
    mu = float(x.mean())
    e = x - mu
    gamma0 = float(np.dot(e, e) / n)
    var = gamma0
    L = min(int(lag), n - 1)
    for j in range(1, L + 1):
        w = 1.0 - j / (L + 1)
        gamma_j = float(np.dot(e[j:], e[:-j]) / n)
        var += 2.0 * w * gamma_j
    se = float(np.sqrt(max(var, 0.0) / n))
    return mu, se


def block_bootstrap_mean_p(
    x: np.ndarray, block: int = 5, n_boot: int = N_BOOT, seed: int = SEED
) -> float:
    """Two-sided block-bootstrap p for H0: mean=0."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 3:
        return float("nan")
    obs = float(x.mean())
    # center under null
    xc = x - obs
    n_blocks = int(np.ceil(n / block))
    extremes = 0
    for _ in range(n_boot):
        starts = rng.integers(0, n, size=n_blocks)
        draws = np.concatenate([xc[s : s + block] for s in starts])[:n]
        if abs(float(draws.mean())) >= abs(obs):
            extremes += 1
    return extremes / n_boot


def compute_forward_returns(
    spread: pd.Series,
    event_dates: list[pd.Timestamp],
    regimes: pd.Series,
    horizons: tuple[int, ...] = FWD_HORIZONS,
    cost: float = ROUND_TRIP_COST,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Pooled and (if powered) regime-split forward spread returns net of cost."""
    from scipy.stats import norm

    cal = spread.dropna().index
    pos = {d: i for i, d in enumerate(cal)}
    rows = []
    for d in event_dates:
        if d not in pos:
            continue
        i = pos[d]
        row = {
            "date": d,
            "regime": regimes.get(d, np.nan) if d in regimes.index else np.nan,
            "spread_t": float(spread.loc[d]),
        }
        for h in horizons:
            if i + h >= len(cal):
                row[f"fwd_{h}"] = np.nan
                row[f"fwd_{h}_net"] = np.nan
                continue
            # sum of residual spread returns over (t+1 … t+h)
            fwd = float(spread.iloc[i + 1 : i + 1 + h].sum())
            row[f"fwd_{h}"] = fwd
            row[f"fwd_{h}_net"] = fwd - cost
        rows.append(row)
    ev = pd.DataFrame(rows)

    summary_rows = []
    for h in horizons:
        col = f"fwd_{h}_net"
        x = ev[col].dropna().to_numpy()
        mu, se = newey_west_mean_se(x, lag=h)
        tstat = mu / se if se and se > 0 else float("nan")
        p_nw = float(2 * norm.sf(abs(tstat))) if np.isfinite(tstat) else float("nan")
        p_boot = block_bootstrap_mean_p(x, block=max(h // 5, 1))
        hit = float(np.mean(x > 0)) if len(x) else float("nan")
        summary_rows.append(
            {
                "scope": "pooled",
                "horizon": h,
                "n": int(len(x)),
                "mean_net": mu,
                "median_net": float(np.median(x)) if len(x) else float("nan"),
                "hit_rate": hit,
                "se_nw": se,
                "t_nw": tstat,
                "p_nw": p_nw,
                "p_block_boot": p_boot,
                "cost_rt": cost,
                "mean_reversion_supported": bool(np.isfinite(mu) and mu > 0 and p_nw < 0.05)
                if np.isfinite(p_nw)
                else False,
            }
        )

    # Regime split — PRIOR ONLY if either cell N < 8
    regime_note = "PRIMARY"
    by_reg = {}
    for reg, g in ev.groupby("regime"):
        if pd.isna(reg):
            continue
        by_reg[str(reg)] = int(g[f"fwd_{FWD_HORIZONS[0]}_net"].notna().sum())
    cells = list(by_reg.values())
    if cells and min(cells) < 8:
        regime_note = "PRIOR_ONLY_N_LT_8"
    for reg, g in ev.groupby("regime"):
        if pd.isna(reg):
            continue
        for h in horizons:
            col = f"fwd_{h}_net"
            x = g[col].dropna().to_numpy()
            mu, se = newey_west_mean_se(x, lag=h)
            tstat = mu / se if se and se > 0 else float("nan")
            p_nw = float(2 * norm.sf(abs(tstat))) if np.isfinite(tstat) else float("nan")
            summary_rows.append(
                {
                    "scope": str(reg),
                    "horizon": h,
                    "n": int(len(x)),
                    "mean_net": mu,
                    "median_net": float(np.median(x)) if len(x) else float("nan"),
                    "hit_rate": float(np.mean(x > 0)) if len(x) else float("nan"),
                    "se_nw": se,
                    "t_nw": tstat,
                    "p_nw": p_nw,
                    "p_block_boot": block_bootstrap_mean_p(x, block=max(h // 5, 1)),
                    "cost_rt": cost,
                    "mean_reversion_supported": False,
                    "role": regime_note,
                }
            )

    summary = pd.DataFrame(summary_rows)
    meta = {
        "regime_split_role": regime_note,
        "regime_cell_n": by_reg,
        "n_declustered": int(len(ev)),
        "cost_rt": cost,
        "horizons": list(horizons),
        "decluster_block": DECLUSTER_BLOCK,
    }
    return ev, summary, meta


def nov_beta_decomposition(
    b_ret: pd.Series,
    s_ret: pd.Series,
    spy: pd.Series,
    b_resid: pd.Series,
    s_resid: pd.Series,
    b_alpha: pd.Series,
    s_alpha: pd.Series,
    b_beta: pd.Series,
    s_beta: pd.Series,
    spread: pd.Series,
    z: pd.Series,
    dates: tuple[str, ...] = ("2026-11-04", "2026-11-05"),
) -> pd.DataFrame:
    """EXPLORATORY: trailing beta decomposition for election week."""
    rows = []
    for ds in dates:
        d = pd.Timestamp(ds)
        rows.append(
            {
                "date": ds,
                "builder_ret": float(b_ret.get(d, np.nan)),
                "supplier_ret": float(s_ret.get(d, np.nan)),
                "spy_ret": float(spy.get(d, np.nan)),
                "builder_alpha_126d": float(b_alpha.get(d, np.nan)),
                "builder_beta_126d": float(b_beta.get(d, np.nan)),
                "supplier_alpha_126d": float(s_alpha.get(d, np.nan)),
                "supplier_beta_126d": float(s_beta.get(d, np.nan)),
                "builder_resid": float(b_resid.get(d, np.nan)),
                "supplier_resid": float(s_resid.get(d, np.nan)),
                "spread": float(spread.get(d, np.nan)),
                "spread_z": float(z.get(d, np.nan)),
                "is_h2_event": bool(
                    np.isfinite(z.get(d, np.nan)) and z.get(d, np.nan) <= EVENT_THRESHOLD_SIGMA
                ),
                "note": (
                    "day after midterm election; H2 −2.5σ event"
                    if ds == "2026-11-04"
                    else "NOT an H2 event (causal z > −2.5)"
                ),
                "status": "EXPLORATORY",
            }
        )
    return pd.DataFrame(rows)


def run(*, compute_forwards: bool = False) -> dict:
    exhibits = ROOT / "outputs" / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)

    adj = pd.read_parquet(ROOT / "data" / "processed" / "adj_close.parquet")
    adj.index = pd.to_datetime(adj.index)
    fred = pd.read_parquet(ROOT / "data" / "processed" / "fred.parquet")
    fred.index = pd.to_datetime(fred.index)

    builders, suppliers = _builder_supplier_tickers()
    assert "SPY" in adj.columns

    b_ret = _ew_returns(adj, builders)
    s_ret = _ew_returns(adj, suppliers)
    spy = adj["SPY"].pct_change()

    b_resid, b_alpha, b_beta = beta_neutral_residual(b_ret, spy)
    s_resid, s_alpha, s_beta = beta_neutral_residual(s_ret, spy)
    spread_full = (s_resid - b_resid).rename("spread_beta_neutral")
    sample = spread_full.loc[START:].dropna()

    series = pd.DataFrame(
        {
            "builder_ew_ret": b_ret,
            "supplier_ew_ret": s_ret,
            "spy_ret": spy,
            "builder_resid": b_resid,
            "supplier_resid": s_resid,
            "builder_alpha": b_alpha,
            "builder_beta": b_beta,
            "supplier_alpha": s_alpha,
            "supplier_beta": s_beta,
            "spread_beta_neutral": spread_full,
        }
    ).loc[START:]
    series.to_csv(exhibits / "h2_spread_series.csv")

    # --- VR hetero-robust + Chow–Denning ---
    vr_rows = [variance_ratio_hetero(sample, q) for q in VR_HORIZONS]
    vr_df = pd.DataFrame(vr_rows)
    cd = chow_denning(vr_rows)
    vr_df.to_csv(exhibits / "h2_variance_ratio.csv", index=False)
    (exhibits / "h2_chow_denning.json").write_text(json.dumps(cd, indent=2))

    lag = sample.shift(1)
    ok = sample.notna() & lag.notna()
    if ok.sum() > 10:
        y = sample[ok].to_numpy()
        x = lag[ok].to_numpy()
        X = np.column_stack([np.ones(len(x)), x])
        ar1_beta = np.linalg.lstsq(X, y, rcond=None)[0]
        ar1 = {
            "intercept": float(ar1_beta[0]),
            "phi": float(ar1_beta[1]),
            "n": int(ok.sum()),
        }
    else:
        ar1 = {"intercept": float("nan"), "phi": float("nan"), "n": int(ok.sum())}

    # --- Events: causal z (mean/sd through t−1) ---
    z = causal_z(sample, window=SIGMA_WINDOW)
    series_z = series.copy()
    series_z["spread_z"] = z.reindex(series_z.index)
    series_z.to_csv(exhibits / "h2_spread_series.csv")

    events = z[z <= EVENT_THRESHOLD_SIGMA].dropna()

    hy = fred[REGIME_PRIMARY_PRE_CRWV].astype(float).sort_index()
    hy_first = str(hy.dropna().index.min().date()) if hy.notna().any() else None
    hy = hy.reindex(sample.index).ffill()
    hy_med = hy.rolling(SIGMA_WINDOW, min_periods=SIGMA_WINDOW).median().shift(1)
    regime = pd.Series(
        np.where(hy > hy_med, "HY_OAS_above_median", "HY_OAS_below_median"),
        index=sample.index,
        name="regime",
    ).where(hy_med.notna())

    event_df = pd.DataFrame(
        {
            "date": events.index,
            "spread": sample.reindex(events.index).to_numpy(),
            "z": events.to_numpy(),
            "hy_oas": hy.reindex(events.index).to_numpy(),
            "hy_oas_126d_median_lag1": hy_med.reindex(events.index).to_numpy(),
            "regime": regime.reindex(events.index).to_numpy(),
        }
    )
    event_df.to_csv(exhibits / "h2_events_m2p5sigma.csv", index=False)

    classified = event_df.loc[event_df["regime"].notna()].copy()
    n_unclassified = int(event_df["regime"].isna().sum())
    counts = classified.groupby("regime").size().rename("n_events").reset_index()
    count_summary = {
        "n_events_total": int(len(event_df)),
        "n_events_classified": int(len(classified)),
        "n_events_unclassified_warmup": n_unclassified,
        "n_events_by_regime": {
            str(r["regime"]): int(r["n_events"]) for _, r in counts.iterrows()
        },
        "n_sample_days": int(len(sample)),
        "n_z_eligible_days": int(z.notna().sum()),
        "threshold": EVENT_THRESHOLD_SIGMA,
        "sigma_window": SIGMA_WINDOW,
        "sigma_rule": "rolling mean/sd end at t-1 (shift 1); matches H1 rule B",
        "regime_series": REGIME_PRIMARY_PRE_CRWV,
        "regime_rule": "above/below trailing 126d median of HY OAS (median lagged 1 day)",
        "hy_oas_first_obs": hy_first,
    }
    counts.to_csv(exhibits / "h2_event_counts_by_regime.csv", index=False)

    # --- EXPLORATORY Nov 4/5 ---
    nov = nov_beta_decomposition(
        b_ret, s_ret, spy, b_resid, s_resid, b_alpha, s_alpha, b_beta, s_beta, spread_full, z
    )
    nov.to_csv(exhibits / "h2_nov4_nov5_beta_decomp.csv", index=False)

    fwd_meta = None
    fwd_summary = None
    if compute_forwards:
        # De-cluster on full sample calendar
        kept = decluster_on_calendar(
            pd.DatetimeIndex(event_df["date"]), sample.index, block=DECLUSTER_BLOCK
        )
        # Mark declustered flag
        event_df["declustered"] = event_df["date"].isin(kept)
        event_df.to_csv(exhibits / "h2_events_m2p5sigma.csv", index=False)

        ev_fwd, fwd_summary, fwd_meta = compute_forward_returns(
            sample, kept, regime, horizons=FWD_HORIZONS, cost=ROUND_TRIP_COST
        )
        ev_fwd.to_csv(exhibits / "h2_forward_events.csv", index=False)
        fwd_summary.to_csv(exhibits / "h2_forward_summary.csv", index=False)
        (exhibits / "h2_forward_meta.json").write_text(json.dumps(fwd_meta, indent=2))

    summary = {
        "status": "FULL" if compute_forwards else "VR_EVENTS_EXPLORATORY",
        "null": NULL,
        "falsifier": FALSIFIER,
        "start": START,
        "n_builders": len(builders),
        "n_suppliers": len(suppliers),
        "builders": builders,
        "suppliers": suppliers,
        "beta_window": BETA_WINDOW,
        "n_sample_days": int(len(sample)),
        "ar1": ar1,
        "variance_ratio": vr_rows,
        "chow_denning": cd,
        "events": count_summary,
        "nov4_nov5_exploratory": nov.to_dict(orient="records"),
        "forward": fwd_meta,
        "compute_forwards": compute_forwards,
    }
    (exhibits / "h2_vr_event_summary.json").write_text(json.dumps(summary, indent=2, default=str))

    # --- tests_run ---
    tests_path = ROOT / "outputs" / "tests_run.csv"
    tests = pd.read_csv(tests_path) if tests_path.exists() else pd.DataFrame()
    drop_ids = [
        "H2_VR",
        "H2_EVENT_COUNTS",
        "H2_CHOW_DENNING",
        "H2_NOV4_NOV5_EXPLORATORY",
        *[f"H2_VR_q{q}" for q in VR_HORIZONS],
        *[f"H2_FWD_{h}" for h in FWD_HORIZONS],
    ]
    if len(tests):
        tests = tests[~tests["test_id"].isin(drop_ids)]

    extra_rows = []
    for r in vr_rows:
        extra_rows.append(
            {
                "test_id": f"H2_VR_q{r['q']}",
                "hypothesis": "H2",
                "description": (
                    f"Lo–MacKinlay VR(q={r['q']}) hetero-robust z* on beta-neutral "
                    f"supplier−builder spread from {START}"
                ),
                "status": "RUN",
                "raw_p": r["p_star"],
                "bh_p": "",
                "effect": r["vr"],
                "n": r["n"],
                "notes": json.dumps(
                    {
                        "z_star": r["z_star"],
                        "z_homo_audit": r["z_homo"],
                        "theta": r["theta"],
                    }
                ),
            }
        )
    extra_rows.append(
        {
            "test_id": "H2_CHOW_DENNING",
            "hypothesis": "H2",
            "description": f"Chow–Denning joint VR test across q={list(VR_HORIZONS)}",
            "status": "RUN",
            "raw_p": cd["p_smm"],
            "bh_p": "",
            "effect": cd["cd_stat"],
            "n": vr_rows[0]["n"] if vr_rows else "",
            "notes": json.dumps(cd),
        }
    )
    extra_rows.append(
        {
            "test_id": "H2_EVENT_COUNTS",
            "hypothesis": "H2",
            "description": (
                "−2.5σ spread events (causal σ through t−1) by HY OAS 126d-median regime"
            ),
            "status": "COUNTS",
            "raw_p": "",
            "bh_p": "",
            "effect": count_summary["n_events_classified"],
            "n": count_summary["n_z_eligible_days"],
            "notes": json.dumps(count_summary),
        }
    )
    extra_rows.append(
        {
            "test_id": "H2_NOV4_NOV5_EXPLORATORY",
            "hypothesis": "H2",
            "description": (
                "EXPLORATORY beta decomposition 4 Nov / 5 Nov 2026; not in FDR family"
            ),
            "status": "EXPLORATORY",
            "raw_p": "",
            "bh_p": "",
            "effect": "",
            "n": 2,
            "notes": json.dumps(nov.to_dict(orient="records"), default=str),
        }
    )
    if compute_forwards and fwd_summary is not None:
        for _, row in fwd_summary.loc[fwd_summary["scope"] == "pooled"].iterrows():
            extra_rows.append(
                {
                    "test_id": f"H2_FWD_{int(row['horizon'])}",
                    "hypothesis": "H2",
                    "description": (
                        f"Pooled de-clustered forward spread return net 30bp, h={int(row['horizon'])}"
                    ),
                    "status": "RUN",
                    "raw_p": row["p_nw"],
                    "bh_p": "",
                    "effect": row["mean_net"],
                    "n": row["n"],
                    "notes": json.dumps(
                        {
                            "median_net": row["median_net"],
                            "hit_rate": row["hit_rate"],
                            "p_block_boot": row["p_block_boot"],
                            "se_nw": row["se_nw"],
                            "regime_split_role": fwd_meta["regime_split_role"],
                        },
                        default=str,
                    ),
                }
            )

    pd.concat([tests, pd.DataFrame(extra_rows)], ignore_index=True).to_csv(
        tests_path, index=False
    )

    print("=== H2 VR (hetero-robust z*) ===")
    print(vr_df[["q", "vr", "z_star", "p_star", "z_homo", "p_homo"]].to_string(index=False))
    print("\nChow–Denning:", cd)
    print("\n=== −2.5σ events (causal σ) by HY OAS ===")
    print(counts.to_string(index=False))
    print(json.dumps(count_summary, indent=2))
    print("\n=== EXPLORATORY Nov 4/5 ===")
    print(nov[["date", "spread", "spread_z", "is_h2_event", "builder_beta_126d", "supplier_beta_126d"]].to_string(index=False))
    if compute_forwards and fwd_summary is not None:
        print("\n=== Forward returns (net 30bp) ===")
        print(fwd_summary.to_string(index=False))
        print("meta:", json.dumps(fwd_meta, indent=2))
    else:
        print("\nForwards not computed (freeze / pre-register first).")
    return summary


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument(
        "--forwards",
        action="store_true",
        help="Compute forward returns (only after RESULTS.md freeze is committed)",
    )
    args = p.parse_args()
    run(compute_forwards=args.forwards)


if __name__ == "__main__":
    main()
