"""H2 — Builder-supplier spread is a mean-reverting factor, not beta.

Construction (spec §H2):
  - Daily EW supplier basket and EW builder basket (taxonomy §4).
  - Suppliers = AI-chain layers excluding builders (exclude non_ai_control).
  - Beta-neutralise: regress each basket on SPY over trailing 126d;
    residual spread = supplier residual − builder residual.
  - Sample: 2023-01-01 → present (AI capex cycle).

This module implements through the variance ratio and −2.5σ event
counts by HY OAS regime. Forward returns are intentionally NOT computed
here (stop before forward returns per P5 gate).

Conditioning variable (Pre-P1 revision d):
  Credit regime = above/below 126d median of the regime series.
  - 2023-01-01 → present (pre-CRWV CDS): **HY OAS only**
    (FRED BAMLH0A0HYM2). CRWV CDS has no history before its 2025 IPO.
  - Do not splice CRWV CDS into 2023–2024.

Note: ingested FRED HY OAS currently begins 2023-11-07; events before
the 126d median is available are counted as unclassified warm-up.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.config_io import ROOT
from src.features.layer import layer_assignments

STATUS = "RUNNING"
NULL = "After beta control, supplier-minus-builder spread is a random walk."
FALSIFIER = "Variance ratio ≈ 1 and no significant forward spread return."

REGIME_PRIMARY_PRE_CRWV = "BAMLH0A0HYM2"  # FRED HY OAS
REGIME_PRIMARY_POST_CRWV = "CRWV_CDS"
START = "2023-01-01"
BETA_WINDOW = 126
SIGMA_WINDOW = 126
EVENT_THRESHOLD_SIGMA = -2.5
VR_HORIZONS = (2, 5, 10, 21)


def _builder_supplier_tickers() -> tuple[list[str], list[str]]:
    layers = layer_assignments()
    builders = sorted(layers.loc[layers["layer"] == "builders", "ticker"].tolist())
    # AI-chain suppliers: all layers except builders and non_ai_control
    suppliers = sorted(
        layers.loc[
            ~layers["layer"].isin(["builders", "non_ai_control"]), "ticker"
        ].tolist()
    )
    return builders, suppliers


def _ew_returns(adj: pd.DataFrame, tickers: list[str]) -> pd.Series:
    """Equal-weight daily return; include a name only on days it has a valid close."""
    cols = [t for t in tickers if t in adj.columns]
    px = adj[cols].sort_index()
    rets = px.pct_change()
    ew = rets.mean(axis=1, skipna=True)
    n = rets.notna().sum(axis=1)
    ew = ew.where(n > 0)
    return ew.rename("ew")


def beta_neutral_residual(
    basket: pd.Series, market: pd.Series, window: int = BETA_WINDOW
) -> pd.Series:
    """Trailing OLS residual of basket on market (with intercept)."""
    df = pd.concat([basket.rename("y"), market.rename("m")], axis=1).dropna()
    resid = pd.Series(index=df.index, dtype=float)
    y = df["y"].to_numpy()
    m = df["m"].to_numpy()
    for i in range(window, len(df)):
        yy = y[i - window : i]
        mm = m[i - window : i]
        X = np.column_stack([np.ones(window), mm])
        beta = np.linalg.lstsq(X, yy, rcond=None)[0]
        resid.iloc[i] = y[i] - (beta[0] + beta[1] * m[i])
    return resid


def variance_ratio(x: pd.Series, q: int) -> dict:
    """Lo–MacKinlay overlapping variance ratio (homoskedastic)."""
    from scipy.stats import norm

    r = x.dropna().to_numpy(dtype=float)
    n = len(r)
    if n < q * 4:
        return {"q": q, "vr": float("nan"), "z": float("nan"), "p": float("nan"), "n": n}
    mu = r.mean()
    rq = np.array([r[i - q + 1 : i + 1].sum() for i in range(q - 1, n)])
    var1 = np.sum((r - mu) ** 2) / (n - 1)
    varq = np.sum((rq - q * mu) ** 2) / (len(rq) - 1)
    vr = (varq / q) / var1 if var1 > 0 else float("nan")
    phi = (2 * (2 * q - 1) * (q - 1)) / (3 * q * n)
    z = (vr - 1.0) / np.sqrt(phi) if phi > 0 and np.isfinite(vr) else float("nan")
    p = float(2 * norm.sf(abs(z))) if np.isfinite(z) else float("nan")
    return {"q": q, "vr": float(vr), "z": float(z), "p": p, "n": n, "phi": float(phi)}


def run(*, stop_before_forward: bool = True) -> dict:
    exhibits = ROOT / "outputs" / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)

    adj = pd.read_parquet(ROOT / "data" / "processed" / "adj_close.parquet")
    adj.index = pd.to_datetime(adj.index)
    fred = pd.read_parquet(ROOT / "data" / "processed" / "fred.parquet")
    fred.index = pd.to_datetime(fred.index)

    builders, suppliers = _builder_supplier_tickers()
    assert "SPY" in adj.columns, "SPY required for beta control"

    b_ret = _ew_returns(adj, builders)
    s_ret = _ew_returns(adj, suppliers)
    spy = adj["SPY"].pct_change()

    # Keep pre-START history for rolling beta estimation, then truncate outputs
    b_resid = beta_neutral_residual(b_ret, spy, window=BETA_WINDOW)
    s_resid = beta_neutral_residual(s_ret, spy, window=BETA_WINDOW)
    spread = (s_resid - b_resid).rename("spread_beta_neutral")

    sample = spread.loc[START:].dropna()
    series = pd.DataFrame(
        {
            "builder_ew_ret": b_ret,
            "supplier_ew_ret": s_ret,
            "spy_ret": spy,
            "builder_resid": b_resid,
            "supplier_resid": s_resid,
            "spread_beta_neutral": spread,
        }
    ).loc[START:]
    series.to_csv(exhibits / "h2_spread_series.csv")

    # --- Variance ratio ---
    vr_rows = [variance_ratio(sample, q) for q in VR_HORIZONS]
    vr_df = pd.DataFrame(vr_rows)
    vr_df.to_csv(exhibits / "h2_variance_ratio.csv", index=False)

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

    # --- −2.5σ events by HY OAS regime ---
    roll_mu = sample.rolling(SIGMA_WINDOW, min_periods=SIGMA_WINDOW).mean()
    roll_sd = sample.rolling(SIGMA_WINDOW, min_periods=SIGMA_WINDOW).std(ddof=1)
    z = (sample - roll_mu) / roll_sd
    events = z[z <= EVENT_THRESHOLD_SIGMA].dropna()

    hy = fred[REGIME_PRIMARY_PRE_CRWV].astype(float).sort_index()
    hy_first = str(hy.dropna().index.min().date()) if hy.notna().any() else None
    hy = hy.reindex(sample.index).ffill()
    hy_med = hy.rolling(SIGMA_WINDOW, min_periods=SIGMA_WINDOW).median().shift(1)
    regime = pd.Series(
        np.where(hy > hy_med, "HY_OAS_above_median", "HY_OAS_below_median"),
        index=sample.index,
        name="regime",
    )
    regime = regime.where(hy_med.notna())

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
    counts = (
        classified.groupby("regime").size().rename("n_events").reset_index()
    )
    count_summary = {
        "n_events_total": int(len(classified)),
        "n_events_unclassified_warmup": n_unclassified,
        "n_events_by_regime": {
            str(r["regime"]): int(r["n_events"]) for _, r in counts.iterrows()
        },
        "n_sample_days": int(len(sample)),
        "n_z_eligible_days": int(z.notna().sum()),
        "threshold": EVENT_THRESHOLD_SIGMA,
        "sigma_window": SIGMA_WINDOW,
        "regime_series": REGIME_PRIMARY_PRE_CRWV,
        "regime_rule": "above/below trailing 126d median of HY OAS (median lagged 1 day)",
        "hy_oas_first_obs": hy_first,
        "stop_before_forward": stop_before_forward,
        "forward_returns_computed": False,
    }
    counts.to_csv(exhibits / "h2_event_counts_by_regime.csv", index=False)

    summary = {
        "status": "COUNTS_AND_VR_ONLY" if stop_before_forward else "FULL",
        "null": NULL,
        "falsifier": FALSIFIER,
        "start": START,
        "n_builders": len(builders),
        "n_suppliers": len(suppliers),
        "builders": builders,
        "suppliers": suppliers,
        "beta_window": BETA_WINDOW,
        "n_sample_days": int(len(sample)),
        "spread_mean": float(sample.mean()),
        "spread_std": float(sample.std(ddof=1)),
        "ar1": ar1,
        "variance_ratio": vr_rows,
        "events": count_summary,
        "note": (
            "P5 stop gate: variance ratio + −2.5σ event counts by HY OAS regime only. "
            "Forward spread returns NOT computed."
        ),
    }
    (exhibits / "h2_vr_event_summary.json").write_text(json.dumps(summary, indent=2))

    tests_path = ROOT / "outputs" / "tests_run.csv"
    tests = pd.read_csv(tests_path) if tests_path.exists() else pd.DataFrame()
    drop_ids = ("H2_VR", "H2_EVENT_COUNTS")
    if len(tests):
        tests = tests[~tests["test_id"].isin(drop_ids)]
    vr10 = next(r for r in vr_rows if r["q"] == 10)
    extra = pd.DataFrame(
        [
            {
                "test_id": "H2_VR",
                "hypothesis": "H2",
                "description": (
                    "Lo–MacKinlay variance ratio on beta-neutral supplier−builder "
                    f"spread from {START}; horizons {list(VR_HORIZONS)}"
                ),
                "status": "RUN_STOP_BEFORE_FWD",
                "raw_p": vr10["p"],
                "bh_p": "",
                "effect": vr10["vr"],
                "n": vr10["n"],
                "notes": json.dumps(
                    {"vr_table": vr_rows, "ar1_phi": ar1["phi"], "primary_q": 10}
                ),
            },
            {
                "test_id": "H2_EVENT_COUNTS",
                "hypothesis": "H2",
                "description": (
                    f"−{abs(EVENT_THRESHOLD_SIGMA)}σ spread event counts by HY OAS "
                    "126d-median regime (no forward returns yet)"
                ),
                "status": "COUNTS_ONLY",
                "raw_p": "",
                "bh_p": "",
                "effect": count_summary["n_events_total"],
                "n": count_summary["n_z_eligible_days"],
                "notes": json.dumps(count_summary),
            },
        ]
    )
    pd.concat([tests, extra], ignore_index=True).to_csv(tests_path, index=False)

    print("=== H2 variance ratio ===")
    print(vr_df.to_string(index=False))
    print("\nAR(1):", ar1)
    print("\n=== −2.5σ event counts by HY OAS regime ===")
    print(counts.to_string(index=False))
    print(json.dumps(count_summary, indent=2))
    if stop_before_forward:
        print("\nSTOP before forward returns (P5 gate).")
    return summary


def main() -> None:
    run(stop_before_forward=True)


if __name__ == "__main__":
    main()
