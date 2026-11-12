"""Daily desk monitor — readable before 5pm HKT from the prior US close.

Spec deliverable 5 / P6–P7:
  Prints L(5), L(10), current trough status, and the 4-Nov-style
  beta-neutral supplier−builder spread z.

Monitor refresh (P7): reads the latest *monitor snapshot* (may extend past
STUDY_ASOF). Study H1–H5 results stay pinned to 2026-11-05.
Post-5-Nov readout is labelled DESCRIPTIVE, single observation, H5 untested.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from core.config_io import ROOT, study_outputs
from src.monitor_snapshot import latest_snapshot_dir
from src.monitor.leadership import (
    TROUGH_LOOKBACK,
    confirmed_trough_flags,
    interpret,
    leadership_after_trough,
)
from src.h2_spread_factor import (
    BETA_WINDOW,
    SIGMA_WINDOW,
    START,
    _builder_supplier_tickers,
    _ew_returns,
    beta_neutral_residual,
    causal_z,
)
from src.h5_leadership_signal import (
    _price_index_from_returns,
    cum_supplier_minus_builder,
)
from src.study_pin import STUDY_ASOF

HKT = ZoneInfo("Asia/Hong_Kong")
NOV5 = pd.Timestamp("2026-11-05")


def _load_adj() -> tuple[pd.DataFrame, str]:
    """Prefer latest monitor snapshot; fall back to study pin."""
    snap = latest_snapshot_dir()
    if snap is not None and (snap / "adj_close.parquet").exists():
        adj = pd.read_parquet(snap / "adj_close.parquet")
        src = f"monitor_snapshot:{snap.name}"
    else:
        adj = pd.read_parquet(ROOT / "data" / "processed" / "adj_close.parquet")
        src = "study_pin"
    adj.index = pd.to_datetime(adj.index).normalize()
    return adj, src


def run_monitor(asof_hkt: datetime | None = None) -> dict:
    adj, price_source = _load_adj()
    prior_close = pd.Timestamp(adj.dropna(how="all").index.max()).normalize()

    builders, suppliers = _builder_supplier_tickers()
    b_ret = _ew_returns(adj, builders)
    s_ret = _ew_returns(adj, suppliers)
    spy = adj["SPY"].pct_change() if "SPY" in adj.columns else pd.Series(dtype=float)

    b_px = _price_index_from_returns(b_ret).loc[:prior_close]
    s_px = _price_index_from_returns(s_ret).loc[:prior_close]

    cum = cum_supplier_minus_builder(s_ret, b_ret, start=START).loc[:prior_close]
    flags = confirmed_trough_flags(cum, lookback=TROUGH_LOOKBACK)
    eligible = flags.index[flags].tolist()
    known = []
    for τ in eligible:
        loc = cum.index.get_loc(τ)
        if isinstance(loc, slice):
            continue
        if loc + 1 < len(cum.index) and cum.index[loc + 1] <= prior_close:
            known.append(τ)
    last_trough = known[-1] if known else None
    last_conf = None
    L5 = float("nan")
    L10 = float("nan")
    if last_trough is not None:
        loc = cum.index.get_loc(last_trough)
        last_conf = cum.index[loc + 1]
        if loc + 1 + 5 < len(cum.index) and cum.index[loc + 1 + 5] <= prior_close:
            L5 = leadership_after_trough(s_px, b_px, last_trough, k=5)
        if loc + 1 + 10 < len(cum.index) and cum.index[loc + 1 + 10] <= prior_close:
            L10 = leadership_after_trough(s_px, b_px, last_trough, k=10)

    is_low_today = (
        bool(cum.iloc[-1] == cum.iloc[-TROUGH_LOOKBACK:].min())
        if len(cum) >= TROUGH_LOOKBACK
        else False
    )

    b_resid, _, _ = beta_neutral_residual(b_ret, spy, window=BETA_WINDOW)
    s_resid, _, _ = beta_neutral_residual(s_ret, spy, window=BETA_WINDOW)
    spread = (s_resid - b_resid).loc[START:prior_close].dropna()
    z = causal_z(spread, window=SIGMA_WINDOW)

    # --- DESCRIPTIVE post-5-Nov refresh (single observation; H5 untested) ---
    descriptive = _nov5_descriptive(
        cum, flags, s_px, b_px, s_ret, b_ret, spread, z, prior_close
    )

    now_hkt = asof_hkt or datetime.now(tz=timezone.utc).astimezone(HKT)
    out = {
        "asof_hkt": now_hkt.strftime("%Y-%m-%d %H:%M %Z"),
        "prior_us_close": str(prior_close.date()),
        "price_source": price_source,
        "study_asof_pin": str(STUDY_ASOF.date()),
        "signal_cutoff": "prior_US_close_only",
        "readable_before": "17:00 Asia/Hong_Kong",
        "L5": None if not np.isfinite(L5) else float(L5),
        "L10": None if not np.isfinite(L10) else float(L10),
        "readout": interpret(L5, L10),
        "trough_rule": "63d_low_on_cum_supplier_minus_builder_confirmed_next_close_up",
        "last_confirmed_trough": None
        if last_trough is None
        else str(pd.Timestamp(last_trough).date()),
        "last_confirmation_date": None
        if last_conf is None
        else str(pd.Timestamp(last_conf).date()),
        "prior_close_is_63d_low_on_cum_spread": is_low_today,
        "spread_beta_neutral": float(spread.loc[prior_close])
        if prior_close in spread.index
        else None,
        "spread_z": float(z.loc[prior_close])
        if prior_close in z.index and np.isfinite(z.loc[prior_close])
        else None,
        "descriptive_post_nov5": descriptive,
    }

    exhibits = study_outputs() / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)
    (exhibits / "h5_daily_monitor.json").write_text(json.dumps(out, indent=2, default=str))
    # Flat CSV for the DESCRIPTIVE daily z path
    if descriptive.get("daily_since_nov5"):
        pd.DataFrame(descriptive["daily_since_nov5"]).to_csv(
            exhibits / "h5_monitor_descriptive_since_nov5.csv", index=False
        )
    return out


def _nov5_descriptive(
    cum: pd.Series,
    flags: pd.Series,
    s_px: pd.Series,
    b_px: pd.Series,
    s_ret: pd.Series,
    b_ret: pd.Series,
    spread: pd.Series,
    z: pd.Series,
    prior_close: pd.Timestamp,
) -> dict:
    """DESCRIPTIVE single-observation refresh after the study pin."""
    nov5_is_trough = bool(flags.get(NOV5, False)) if NOV5 in flags.index else False
    # Confirmation of a 5 Nov trough would be the next session (6 Nov)
    conf = None
    confirmed = False
    if NOV5 in cum.index:
        loc = cum.index.get_loc(NOV5)
        if not isinstance(loc, slice) and loc + 1 < len(cum.index):
            conf = cum.index[loc + 1]
            # Confirmed iff 5 Nov was a 63d low AND next close up
            window = cum.iloc[max(0, loc - TROUGH_LOOKBACK + 1) : loc + 1]
            is_low = bool(cum.loc[NOV5] == window.min())
            confirmed = bool(is_low and cum.loc[conf] > cum.loc[NOV5])
            nov5_is_trough = is_low and confirmed

    L5_from_nov5 = float("nan")
    if confirmed and conf is not None:
        # L(5) available at conf+5
        loc = cum.index.get_loc(NOV5)
        if loc + 1 + 5 < len(cum.index) and cum.index[loc + 1 + 5] <= prior_close:
            L5_from_nov5 = leadership_after_trough(s_px, b_px, NOV5, k=5)

    # Cumulative supplier vs builder return since Nov 5 trough (from confirmation or from Nov5)
    start_px = conf if (confirmed and conf is not None) else NOV5
    daily = []
    if start_px in s_px.index and prior_close in s_px.index:
        for d in s_px.loc[start_px:prior_close].index:
            if d not in b_px.index:
                continue
            s_cum = float(s_px.loc[d] / s_px.loc[start_px] - 1.0)
            b_cum = float(b_px.loc[d] / b_px.loc[start_px] - 1.0)
            daily.append(
                {
                    "date": str(pd.Timestamp(d).date()),
                    "supplier_cum_ret_since_ref": s_cum,
                    "builder_cum_ret_since_ref": b_cum,
                    "supplier_minus_builder_cum": s_cum - b_cum,
                    "spread_beta_neutral": float(spread.loc[d])
                    if d in spread.index
                    else None,
                    "spread_z": float(z.loc[d])
                    if d in z.index and np.isfinite(z.loc[d])
                    else None,
                }
            )

    return {
        "label": "DESCRIPTIVE",
        "single_observation": True,
        "h5_status": "UNTESTED_PRIOR_ONLY",
        "note": (
            "Monitor refresh after study pin 2026-11-05. "
            "Not an H5 test; not in the FDR family."
        ),
        "nov5_was_63d_low_candidate": NOV5 in cum.index,
        "nov5_trough_confirmed_on_next_close": confirmed,
        "confirmation_date": None if conf is None else str(pd.Timestamp(conf).date()),
        "L5_since_nov5_trough": None
        if not np.isfinite(L5_from_nov5)
        else float(L5_from_nov5),
        "L5_available": bool(np.isfinite(L5_from_nov5)),
        "cum_return_ref": "confirmation_close" if confirmed else "2026-11-05",
        "daily_since_nov5": daily,
    }


def main() -> None:
    out = run_monitor()
    print("=== Daily desk monitor (prior US close; before 5pm HKT) ===")
    for k, v in out.items():
        if k == "descriptive_post_nov5":
            print("--- DESCRIPTIVE post-5-Nov (single obs; H5 untested) ---")
            d = v
            for kk, vv in d.items():
                if kk == "daily_since_nov5":
                    continue
                print(f"  {kk}={vv}")
            print("  daily_since_nov5:")
            for row in d.get("daily_since_nov5") or []:
                print(
                    f"    {row['date']}: s_cum={row['supplier_cum_ret_since_ref']:+.4f} "
                    f"b_cum={row['builder_cum_ret_since_ref']:+.4f} "
                    f"s-b={row['supplier_minus_builder_cum']:+.4f} "
                    f"z={row['spread_z']}"
                )
        else:
            print(f"{k}={v}")


if __name__ == "__main__":
    main()
