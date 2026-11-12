"""Resolve D5/D7 from ingested prices only. Never calibrate to targets."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats

from core.config_io import ROOT, fixtures, study_config_dir


def load_nov5_panel_meta() -> pd.DataFrame:
    path = study_config_dir() / "nov5_panel.yaml"
    names = yaml.safe_load(path.read_text())["names"]
    return pd.DataFrame(names)


def _close(px: pd.DataFrame, ticker: str, date: str) -> float:
    ts = pd.Timestamp(date)
    if ticker not in px.columns:
        raise KeyError(ticker)
    # forward/back fill not allowed — exact date or fail
    if ts not in px.index:
        # try normalized match
        if ts.normalize() in px.index:
            ts = ts.normalize()
        else:
            raise KeyError(f"{ticker}: no close on {date}")
    val = px.loc[ts, ticker]
    if pd.isna(val):
        raise ValueError(f"{ticker} NaN on {date}")
    return float(val)


def build_cross_section(
    close: pd.DataFrame,
    high: pd.DataFrame | None = None,
    *,
    use_intraday_high: bool = True,
) -> pd.DataFrame:
    """Compute name-level stats from ingested closes (and daily highs).

    YTD to 4 Nov = close[2026-11-04] / close[2025-12-31] - 1
    prior 5d = close[2026-11-04] / close[2026-10-28] - 1  (28 Oct → 4 Nov)
    5 Nov ret = close[2026-11-05] / close[2026-11-04] - 1
    dist 52w: vs trailing 252-session max of High (if use_intraday_high)
              else max of Close — note used intraday.
    """
    meta = load_nov5_panel_meta()
    rows = []
    for _, m in meta.iterrows():
        t = m["ticker"]
        c1105 = _close(close, t, "2026-11-05")
        c1104 = _close(close, t, "2026-11-04")
        c1028 = _close(close, t, "2026-10-28")
        c_yoy = _close(close, t, "2025-12-31")
        ret_nov5 = c1105 / c1104 - 1.0
        ret_prior5 = c1104 / c1028 - 1.0
        ytd = c1104 / c_yoy - 1.0
        # 52w high window ending 2026-11-05
        end = pd.Timestamp("2026-11-05")
        window = close[t].loc[:end].dropna().iloc[-252:]
        if use_intraday_high and high is not None and t in high.columns:
            hi_win = high[t].loc[:end].dropna().iloc[-252:]
            peak = float(hi_win.max())
            high_basis = "daily_high"
        else:
            peak = float(window.max())
            high_basis = "daily_close"
        dist = c1105 / peak - 1.0
        rows.append(
            {
                "ticker": t,
                "layer": m["layer"],
                "ai_chain": int(m["ai_chain"]),
                "ret_nov5_pct": ret_nov5 * 100.0,
                "ret_prior5_pct": ret_prior5 * 100.0,
                "ytd_to_4nov_pct": ytd * 100.0,
                "dist_52w_high_pct": dist * 100.0,
                "high_basis": high_basis,
                "source": "RAW_FILE:data/processed/prices.parquet",
            }
        )
    return pd.DataFrame(rows)


def summarise(cs: pd.DataFrame) -> dict:
    builders = cs["layer"] == "builders"
    suppliers = (cs["ai_chain"] == 1) & ~builders
    ai = cs["ai_chain"] == 1
    rho_ytd, p_ytd = stats.spearmanr(cs["ret_nov5_pct"], cs["ytd_to_4nov_pct"])
    rho_ytd_ai, _ = stats.spearmanr(
        cs.loc[ai, "ret_nov5_pct"], cs.loc[ai, "ytd_to_4nov_pct"]
    )
    rho_p5, p_p5 = stats.spearmanr(cs["ret_nov5_pct"], cs["ret_prior5_pct"])
    rho_p5_ai, _ = stats.spearmanr(
        cs.loc[ai, "ret_nov5_pct"], cs.loc[ai, "ret_prior5_pct"]
    )
    return {
        "n": len(cs),
        "hyperscaler_ew_nov5_pct": float(cs.loc[builders, "ret_nov5_pct"].mean()),
        "supplier_ew_nov5_pct": float(cs.loc[suppliers, "ret_nov5_pct"].mean()),
        "spearman_nov5_vs_ytd": float(rho_ytd),
        "spearman_nov5_vs_ytd_p": float(p_ytd),
        "spearman_nov5_vs_ytd_ai_only": float(rho_ytd_ai),
        "spearman_nov5_vs_prior5": float(rho_p5),
        "spearman_nov5_vs_prior5_p": float(p_p5),
        "spearman_nov5_vs_prior5_ai_only": float(rho_p5_ai),
        "names_gt20pct_below_52w": int((cs["dist_52w_high_pct"] < -20).sum()),
        "high_basis": cs["high_basis"].iloc[0],
    }


def compare_to_targets(summary: dict, cs: pd.DataFrame) -> tuple[bool, pd.DataFrame, list[str]]:
    """Return (ok, per_name_diff_helpful, failure_messages). Does not adjust targets."""
    fx = fixtures()["cross_section_targets"]
    gates = fixtures()["gates"]
    failures: list[str] = []

    def check(name: str, got: float, target: float, tol: float) -> None:
        if abs(got - target) > tol:
            failures.append(f"{name}: observed={got:.6g} target={target} tol={tol}")

    check("hyperscaler_ew_nov5_pct", summary["hyperscaler_ew_nov5_pct"], fx["hyperscaler_ew_nov5_pct"], 0.15)
    check("supplier_ew_nov5_pct", summary["supplier_ew_nov5_pct"], fx["supplier_ew_nov5_pct"], 0.3)
    check("spearman_nov5_vs_ytd", summary["spearman_nov5_vs_ytd"], fx["spearman_nov5_vs_ytd"], 0.05)
    check(
        "spearman_nov5_vs_ytd_ai_only",
        summary["spearman_nov5_vs_ytd_ai_only"],
        fx["spearman_nov5_vs_ytd_ai_only"],
        0.05,
    )
    check("spearman_nov5_vs_prior5", summary["spearman_nov5_vs_prior5"], fx["spearman_nov5_vs_prior5"], 0.05)
    check(
        "spearman_nov5_vs_prior5_ai_only",
        summary["spearman_nov5_vs_prior5_ai_only"],
        fx["spearman_nov5_vs_prior5_ai_only"],
        0.05,
    )
    if summary["names_gt20pct_below_52w"] != fx["names_gt20pct_below_52w"]:
        failures.append(
            f"names_gt20pct_below_52w: observed={summary['names_gt20pct_below_52w']} "
            f"target={fx['names_gt20pct_below_52w']}"
        )
    if summary["spearman_nov5_vs_ytd"] >= gates["spearman_ytd_max"]:
        failures.append(
            f"spearman_ytd_max gate: observed={summary['spearman_nov5_vs_ytd']} "
            f"required < {gates['spearman_ytd_max']}"
        )

    # Per-name table for debugging (no note-level name targets except a few verified)
    verified_nov5 = {
        "MSFT": -3.6,
        "AMZN": -2.2,
        "GOOGL": -2.2,
        "META": -4.0,
        "AMD": -17.3,
        "MRVL": -16.4,
        "MU": -17.5,
        "LRCX": -16.4,
        "LITE": -18.7,
        "VRT": -14.0,
        "NBIS": -14.9,
    }
    diffs = []
    for _, row in cs.iterrows():
        t = row["ticker"]
        note_val = verified_nov5.get(t)
        diffs.append(
            {
                "ticker": t,
                "ret_nov5_pct": row["ret_nov5_pct"],
                "note_ret_nov5_pct": note_val,
                "delta_vs_note": (row["ret_nov5_pct"] - note_val) if note_val is not None else np.nan,
                "ytd_to_4nov_pct": row["ytd_to_4nov_pct"],
                "ret_prior5_pct": row["ret_prior5_pct"],
                "dist_52w_high_pct": row["dist_52w_high_pct"],
            }
        )
        if note_val is not None and abs(row["ret_nov5_pct"] - note_val) > 0.35:
            failures.append(
                f"name {t} ret_nov5: ingested={row['ret_nov5_pct']:.3f} "
                f"note={note_val} (|delta|>0.35pp)"
            )
    return len(failures) == 0, pd.DataFrame(diffs), failures
