"""Layer / exposure judgment block (H3).

Layer assignment is judgment-coded from config/universe.yaml.
AI revenue exposure 0–3 from config/ai_exposure.yaml — tag JUDGMENT_CODED_POST_OUTCOME.
Scores are time-varying: E1–E4 vs E5–E7 (plus optional per-episode overrides).
"""

from __future__ import annotations

import yaml
import pandas as pd

from core.config_io import reference_path, universe

# Episode bands per human decision 2026-11-08
E1_E4 = {"E1", "E2", "E3", "E4"}
E5_E7 = {"E5", "E6", "E7"}


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


def _load_ai_yaml() -> dict:
    path = reference_path("ai_exposure")
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def ai_score_for_episode(ticker: str, episode: str, data: dict | None = None) -> float:
    """Resolve time-varying AI exposure score for (ticker, episode)."""
    data = data if data is not None else _load_ai_yaml()
    names = data.get("names") or {}
    meta = names.get(ticker) or {}
    by_ep = meta.get("score_by_episode") or {}
    if episode in by_ep and by_ep[episode] is not None:
        return float(by_ep[episode])
    if episode in E5_E7:
        if "score_e5_e7" in meta and meta["score_e5_e7"] is not None:
            return float(meta["score_e5_e7"])
        # legacy single score field = E5–E7 band
        if "score" in meta and meta["score"] is not None:
            return float(meta["score"])
    if episode in E1_E4:
        if "score_e1_e4" in meta and meta["score_e1_e4"] is not None:
            return float(meta["score_e1_e4"])
    return float("nan")


def ai_revenue_exposure(episode: str | None = None) -> pd.Series:
    """Judgment 0–3. If episode given, return time-varying scores for that episode."""
    data = _load_ai_yaml()
    tickers = layer_assignments()["ticker"]
    if episode is None:
        # Default: E5–E7 (current) scores for backward-compat callers
        vals = {t: ai_score_for_episode(t, "E5", data) for t in tickers}
    else:
        vals = {t: ai_score_for_episode(t, episode, data) for t in tickers}
    return pd.Series(vals, dtype="float64", name="ai_revenue_exposure_0_3_JUDGMENT")


def ai_exposure_meta() -> dict:
    data = _load_ai_yaml()
    if not data:
        return {"status": "MISSING", "tag": "JUDGMENT_CODED_POST_OUTCOME"}
    return {
        "status": data.get("status"),
        "tag": data.get("tag", "JUDGMENT_CODED_POST_OUTCOME"),
        "sign_off": data.get("sign_off"),
        "time_varying": True,
        "bands": data.get("bands"),
        "human_decision": data.get("human_decision"),
        "companyfacts_segment_note": data.get("companyfacts_segment_note"),
    }


def spearman_ai_vs_layer_dummy(panel: pd.DataFrame) -> pd.DataFrame:
    """Per-episode Spearman ρ between AI score and AI-chain vs non_ai_control dummy.

    AI-chain = layer != non_ai_control. Flags |ρ|>0.8 as redundant.
    """
    from scipy.stats import spearmanr

    rows = []
    df = panel.copy()
    df["ai_chain"] = (df["layer"] != "non_ai_control").astype(float)
    for ep, g in df.groupby("episode", sort=True):
        sub = g.loc[
            g["listed_at_start"]
            & g["ai_revenue_exposure_0_3_JUDGMENT"].notna()
            & g["ai_chain"].notna()
        ]
        if len(sub) < 5:
            rows.append(
                {
                    "episode": ep,
                    "n": len(sub),
                    "spearman_rho": float("nan"),
                    "redundant_abs_rho_gt_0_8": False,
                    "note": "too few observations",
                }
            )
            continue
        rho, _p = spearmanr(
            sub["ai_revenue_exposure_0_3_JUDGMENT"],
            sub["ai_chain"],
        )
        rows.append(
            {
                "episode": ep,
                "n": len(sub),
                "spearman_rho": float(rho),
                "redundant_abs_rho_gt_0_8": bool(abs(rho) > 0.8),
                "note": "score redundant with layer dummy" if abs(rho) > 0.8 else "",
            }
        )
    return pd.DataFrame(rows)
