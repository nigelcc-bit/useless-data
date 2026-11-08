"""Layer / exposure judgment block (H3 regressors 7–8).

Layer assignment is judgment-coded from config/universe.yaml — flag in every output.
AI revenue exposure 0–3 is judgment; missing until explicitly coded in config.
"""

from __future__ import annotations

import pandas as pd

from src.config_io import universe


def layer_assignments() -> pd.DataFrame:
    """One row per ticker: primary layer (+ alternate if dual-coded)."""
    u = universe()
    rows = []
    for layer, meta in (u.get("layers") or {}).items():
        for ticker, info in (meta.get("names") or {}).items():
            rows.append(
                {
                    "ticker": ticker,
                    "layer": layer,
                    "layer_ambiguous": bool((info or {}).get("ambiguous", False)),
                    "layer_justification_JUDGMENT": (info or {}).get("justification", ""),
                }
            )
    df = pd.DataFrame(rows)
    dual = u.get("dual_code") or {}
    if dual and len(df):
        df["layer_alternate_JUDGMENT"] = df["ticker"].map(
            lambda t: (dual.get(t) or {}).get("alternate_layer")
        )
    else:
        df["layer_alternate_JUDGMENT"] = None
    return df


def ai_revenue_exposure() -> pd.Series:
    """Judgment 0–3. Empty until config/ai_exposure.yaml is filled."""
    path_keys = universe()  # noqa: F841 — reserved for future config join
    # No coded exposure file yet → all missing (shows in coverage)
    tickers = layer_assignments()["ticker"]
    return pd.Series(index=tickers, dtype="float64", name="ai_revenue_exposure_0_3_JUDGMENT")
