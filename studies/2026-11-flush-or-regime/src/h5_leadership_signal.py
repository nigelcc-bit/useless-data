"""H5 — Pre-open leadership statistic has forecasting power.

P6 (counts first): apply frozen trough rule on the supplier−builder
cumulative spread from 2023-01-01; print every trough with L(5)/L(10)
available under the asof−1 close convention; walk-forward train vs OOS
counts. If OOS N < 8 → H5 PRIOR ONLY (do not test).

Trough rule (Pre-P1 + P6 clarification):
  Series = cumulative sum of (EW supplier daily ret − EW builder daily ret)
  from 2023-01-01.
  τ = 63d low on that series, confirmed by next close up.
  L(k) starts after confirmation close (close[τ+1] → close[τ+1+k]),
  divided by trailing supplier/builder beta ratio.

Walk-forward split (frozen for counts):
  Train = confirmation date < 2025-01-01
  OOS   = confirmation date ≥ 2025-01-01
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from core.config_io import ROOT, study_outputs
from core.features.layer import layer_assignments
from src.monitor.leadership import (
    TROUGH_LOOKBACK,
    _beta_ratio,
    confirmed_trough_flags,
    leadership_after_trough,
)
from src.h2_spread_factor import (
    BETA_WINDOW,
    START,
    _builder_supplier_tickers,
    _ew_returns,
    beta_neutral_residual,
    causal_z,
)

STATUS = "COUNTS"
NULL = "L(5) and L(10) carry no information about subsequent 63d relative supplier performance."
FALSIFIER = "OOS R² ≤ 0 or hit rate ≤ 50% → demote discriminating test to commentary."

TROUGH_RULE = "63d_low_on_cum_supplier_minus_builder_spread_confirmed_next_close_up"
L_WINDOW = "after_confirmation_close"
SIGNAL_CUTOFF = "asof_minus_1_close"
WF_OOS_START = "2025-01-01"
N_FLOOR = 8


def _price_index_from_returns(rets: pd.Series) -> pd.Series:
    r = rets.dropna()
    return (1.0 + r).cumprod()


def cum_supplier_minus_builder(
    s_ret: pd.Series, b_ret: pd.Series, start: str = START
) -> pd.Series:
    """Cumulative sum of (supplier − builder) daily EW returns from `start`."""
    df = pd.concat([s_ret.rename("s"), b_ret.rename("b")], axis=1).dropna()
    df = df.loc[start:]
    spread = (df["s"] - df["b"]).rename("spread_ret")
    return spread.cumsum().rename("cum_spread")


def enumerate_troughs(
    cum_spread: pd.Series,
    suppliers_px: pd.Series,
    builders_px: pd.Series,
    lookback: int = TROUGH_LOOKBACK,
) -> pd.DataFrame:
    """Every confirmed trough on cum_spread with L(5)/L(10) when available."""
    flags = confirmed_trough_flags(cum_spread, lookback=lookback)
    rows = []
    cal = cum_spread.dropna().index
    pos = {d: i for i, d in enumerate(cal)}
    for τ in cal[flags.reindex(cal).fillna(False)]:
        i = pos[τ]
        if i + 1 >= len(cal):
            continue
        conf = cal[i + 1]
        row = {
            "trough_date": τ,
            "confirmation_date": conf,
            "cum_spread_at_trough": float(cum_spread.loc[τ]),
            "walk_forward_split": (
                "train" if pd.Timestamp(conf) < pd.Timestamp(WF_OOS_START) else "oos"
            ),
        }
        for k in (5, 10):
            # L(k) knowable once confirmation+k close is in hand
            if i + 1 + k >= len(cal):
                row[f"L{k}"] = np.nan
                row[f"L{k}_available_date"] = pd.NaT
                row[f"L{k}_complete"] = False
                continue
            avail = cal[i + 1 + k]
            # Signal convention: value dated with closes through avail (asof-1 = avail
            # when asof = next session). Compute on series truncated at avail.
            L = leadership_after_trough(
                suppliers_px.loc[:avail],
                builders_px.loc[:avail],
                τ,
                k=k,
                beta_window=63,
            )
            # Verify no peek: recomputing with only [:avail] is the definition
            row[f"L{k}"] = L
            row[f"L{k}_available_date"] = avail
            row[f"L{k}_complete"] = bool(np.isfinite(L))
        rows.append(row)
    return pd.DataFrame(rows)


def run(*, stop_after_counts: bool = True) -> dict:
    exhibits = study_outputs() / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)

    adj = pd.read_parquet(ROOT / "data" / "processed" / "adj_close.parquet")
    adj.index = pd.to_datetime(adj.index)

    builders, suppliers = _builder_supplier_tickers()
    b_ret = _ew_returns(adj, builders)
    s_ret = _ew_returns(adj, suppliers)
    # Price indices for L(k) (level series starting before 2023 for beta warm-up)
    b_px = _price_index_from_returns(b_ret)
    s_px = _price_index_from_returns(s_ret)

    cum = cum_supplier_minus_builder(s_ret, b_ret, start=START)
    troughs = enumerate_troughs(cum, s_px, b_px)
    troughs.to_csv(exhibits / "h5_trough_list.csv", index=False)

    n_total = int(len(troughs))
    n_l5 = int(troughs["L5_complete"].sum()) if n_total else 0
    n_l10 = int(troughs["L10_complete"].sum()) if n_total else 0
    train = troughs.loc[troughs["walk_forward_split"] == "train"]
    oos = troughs.loc[troughs["walk_forward_split"] == "oos"]
    # Power floor on OOS troughs with complete L(10) (test regressor available)
    n_train = int(len(train))
    n_oos = int(len(oos))
    n_train_l10 = int(train["L10_complete"].sum()) if n_train else 0
    n_oos_l10 = int(oos["L10_complete"].sum()) if n_oos else 0

    if n_oos_l10 < N_FLOOR:
        decision = "PRIOR_ONLY"
        note = (
            f"OOS N with complete L(10) = {n_oos_l10} < {N_FLOOR} → H5 PRIOR ONLY; "
            "do not test. Counts and monitor only."
        )
    else:
        decision = "TESTABLE_N_GE_8"
        note = f"OOS N with complete L(10) = {n_oos_l10} ≥ {N_FLOOR}; testing deferred to later P6 step."

    summary = {
        "status": "COUNTS_ONLY" if stop_after_counts else decision,
        "decision": decision,
        "trough_rule": TROUGH_RULE,
        "start": START,
        "wf_oos_start": WF_OOS_START,
        "n_troughs_total": n_total,
        "n_L5_complete": n_l5,
        "n_L10_complete": n_l10,
        "n_train": n_train,
        "n_oos": n_oos,
        "n_train_L10_complete": n_train_l10,
        "n_oos_L10_complete": n_oos_l10,
        "n_floor": N_FLOOR,
        "note": note,
        "builders": builders,
        "suppliers": suppliers,
        "stop_after_counts": stop_after_counts,
        "forward_test_run": False,
    }
    (exhibits / "h5_trough_counts.json").write_text(json.dumps(summary, indent=2))

    # tests_run
    tests_path = study_outputs() / "tests_run.csv"
    tests = pd.read_csv(tests_path) if tests_path.exists() else pd.DataFrame()
    if len(tests):
        tests = tests[~tests["test_id"].isin(["H5_TROUGH_COUNTS", "H5_WF_SPLIT"])]
    extra = pd.DataFrame(
        [
            {
                "test_id": "H5_TROUGH_COUNTS",
                "hypothesis": "H5",
                "description": (
                    "Confirmed 63d troughs on cum supplier−builder spread from 2023; "
                    "L(5)/L(10) availability"
                ),
                "status": decision,
                "raw_p": "",
                "bh_p": "",
                "effect": n_total,
                "n": n_oos_l10,
                "notes": json.dumps(summary),
            },
            {
                "test_id": "H5_WF_SPLIT",
                "hypothesis": "H5",
                "description": (
                    f"Walk-forward split train conf<{WF_OOS_START} vs OOS; "
                    f"power floor N≥{N_FLOOR} on OOS L10"
                ),
                "status": decision,
                "raw_p": "",
                "bh_p": "",
                "effect": n_oos_l10,
                "n": n_train_l10,
                "notes": (
                    f"train={n_train} (L10={n_train_l10}); "
                    f"oos={n_oos} (L10={n_oos_l10}); {note}"
                ),
            },
        ]
    )
    pd.concat([tests, extra], ignore_index=True).to_csv(tests_path, index=False)

    print("=== H5 trough counts (P6) ===")
    print(json.dumps(summary, indent=2))
    print("\nTrough list:")
    cols = [
        "trough_date",
        "confirmation_date",
        "walk_forward_split",
        "L5",
        "L5_available_date",
        "L10",
        "L10_available_date",
    ]
    if len(troughs):
        print(troughs[cols].to_string(index=False))
    else:
        print("(none)")
    print("\n", note)
    return summary


def main() -> None:
    run(stop_after_counts=True)


if __name__ == "__main__":
    main()
