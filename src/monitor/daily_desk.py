"""Daily desk monitor — readable before 5pm HKT from the prior US close.

Spec deliverable 5 / P6:
  Prints L(5), L(10), current trough status, and the 4-Nov-style
  beta-neutral supplier−builder spread z. Uses closes through the
  prior US session only (APAC pre-order constraint).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from src.config_io import ROOT
from src.monitor.leadership import (
    TROUGH_LOOKBACK,
    confirmed_trough_flags,
    interpret,
    leadership_after_trough,
)
from src.studies.h2_spread_factor import (
    BETA_WINDOW,
    SIGMA_WINDOW,
    START,
    _builder_supplier_tickers,
    _ew_returns,
    beta_neutral_residual,
    causal_z,
)
from src.studies.h5_leadership_signal import (
    _price_index_from_returns,
    cum_supplier_minus_builder,
)

HKT = ZoneInfo("Asia/Hong_Kong")


def _prior_us_close_cutoff(adj_index: pd.DatetimeIndex) -> pd.Timestamp:
    """Latest session date on disk = prior US close for the monitor asof."""
    return pd.Timestamp(adj_index.max()).tz_localize(None)


def run_monitor(asof_hkt: datetime | None = None) -> dict:
    adj = pd.read_parquet(ROOT / "data" / "processed" / "adj_close.parquet")
    adj.index = pd.to_datetime(adj.index)
    prior_close = _prior_us_close_cutoff(adj.index)

    builders, suppliers = _builder_supplier_tickers()
    b_ret = _ew_returns(adj, builders)
    s_ret = _ew_returns(adj, suppliers)
    spy = adj["SPY"].pct_change()

    b_px = _price_index_from_returns(b_ret).loc[:prior_close]
    s_px = _price_index_from_returns(s_ret).loc[:prior_close]

    # Desk trough status + L(k) on H5 cum-spread troughs (closes through prior_close)
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
        # L(k) only if confirmation+k ≤ prior_close
        if loc + 1 + 5 < len(cum.index) and cum.index[loc + 1 + 5] <= prior_close:
            L5 = leadership_after_trough(s_px, b_px, last_trough, k=5)
        if loc + 1 + 10 < len(cum.index) and cum.index[loc + 1 + 10] <= prior_close:
            L10 = leadership_after_trough(s_px, b_px, last_trough, k=10)

    if len(cum) >= TROUGH_LOOKBACK:
        is_low_today = bool(cum.iloc[-1] == cum.iloc[-TROUGH_LOOKBACK:].min())
    else:
        is_low_today = False
    pending_or_confirmed = False
    if len(cum) >= 2:
        prev = cum.index[-2]
        if prev in flags.index and bool(flags.get(prev, False)):
            pending_or_confirmed = True

    # Beta-neutral spread z (H2 / 4-Nov style), causal through prior_close
    b_resid, _, _ = beta_neutral_residual(b_ret, spy, window=BETA_WINDOW)
    s_resid, _, _ = beta_neutral_residual(s_ret, spy, window=BETA_WINDOW)
    spread = (s_resid - b_resid).loc[START:prior_close].dropna()
    z = causal_z(spread, window=SIGMA_WINDOW)
    z_last = float(z.loc[prior_close]) if prior_close in z.index and np.isfinite(z.loc[prior_close]) else float("nan")
    spread_last = (
        float(spread.loc[prior_close])
        if prior_close in spread.index
        else float("nan")
    )

    now_hkt = asof_hkt or datetime.now(tz=timezone.utc).astimezone(HKT)
    readout = interpret(L5, L10)
    out = {
        "asof_hkt": now_hkt.strftime("%Y-%m-%d %H:%M %Z"),
        "prior_us_close": str(prior_close.date()),
        "signal_cutoff": "prior_US_close_only",
        "readable_before": "17:00 Asia/Hong_Kong",
        "L5": None if not np.isfinite(L5) else float(L5),
        "L10": None if not np.isfinite(L10) else float(L10),
        "readout": readout,
        "trough_rule": "63d_low_on_cum_supplier_minus_builder_confirmed_next_close_up",
        "last_confirmed_trough": None if last_trough is None else str(pd.Timestamp(last_trough).date()),
        "last_confirmation_date": None if last_conf is None else str(pd.Timestamp(last_conf).date()),
        "prior_close_is_63d_low_on_cum_spread": is_low_today,
        "prior_day_was_confirmed_trough": pending_or_confirmed,
        "spread_beta_neutral": spread_last,
        "spread_z": z_last,
        "spread_z_note": "causal z (mean/sd through t-1); 4-Nov-style H2 event used z≤−2.5",
    }

    exhibits = ROOT / "outputs" / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)
    (exhibits / "h5_daily_monitor.json").write_text(json.dumps(out, indent=2))
    return out


def main() -> None:
    out = run_monitor()
    print("=== Daily desk monitor (prior US close; before 5pm HKT) ===")
    for k, v in out.items():
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
