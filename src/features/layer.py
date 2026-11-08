"""Layer / exposure judgment block (H3).

Layer assignment is judgment-coded from config/universe.yaml.
AI revenue exposure 0–3 from config/ai_exposure.yaml — tag JUDGMENT_CODED_POST_OUTCOME.
"""

from __future__ import annotations

import yaml
import pandas as pd

from src.config_io import ROOT, universe


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
    """Judgment 0–3 from config/ai_exposure.yaml (PROPOSED until human sign-off)."""
    path = ROOT / "config" / "ai_exposure.yaml"
    if not path.exists():
        tickers = layer_assignments()["ticker"]
        return pd.Series(
            index=tickers, dtype="float64", name="ai_revenue_exposure_0_3_JUDGMENT"
        )
    data = yaml.safe_load(path.read_text())
    names = data.get("names") or {}
    s = pd.Series(
        {t: (meta or {}).get("score") for t, meta in names.items()},
        dtype="float64",
        name="ai_revenue_exposure_0_3_JUDGMENT",
    )
    # align to universe
    tickers = layer_assignments()["ticker"]
    return s.reindex(tickers)


def ai_exposure_meta() -> dict:
    path = ROOT / "config" / "ai_exposure.yaml"
    if not path.exists():
        return {"status": "MISSING", "tag": "JUDGMENT_CODED_POST_OUTCOME"}
    data = yaml.safe_load(path.read_text())
    return {
        "status": data.get("status"),
        "tag": data.get("tag", "JUDGMENT_CODED_POST_OUTCOME"),
    }
