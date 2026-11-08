"""H1b — EXPLORATORY counts only. Register BEFORE any forward returns.

Hypothesis (T002b): Semis deep-drawdown cluster days have worse 63-session
forward outcomes than S&P days in the same state.

State (counts phase only — no forward prices loaded):
  - rule B event
  - series >20% below trailing 252d high at t−1 (dist_high_tm1 < −0.20)
  - cluster day (another qualifying rule-B event in prior 126 sessions)

De-cluster: keep the first qualifying day per non-overlapping 63-session block.
Apply N>=8 floor → TESTABLE_N_GE_8 else PRIOR_ONLY_NOT_TESTED.
Stop after counts.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config_io import ROOT
from src.studies.h1_power_check import (
    ASOF,
    SERIES,
    LookaheadError,
    flag_all_events,
    forward_eligible_mask,
    load_close,
    mark_first_shocks,
)

DEEP_DD = -0.20  # more than 20% below 252d high
BLOCK = 63
STATUS_OK = "TESTABLE_N_GE_8"
STATUS_PRIOR = "PRIOR_ONLY_NOT_TESTED"


def select_h1b_state(events: pd.DataFrame) -> pd.DataFrame:
    """Rule B cluster days >20% below 252d high."""
    if events.empty:
        return events
    return events.loc[
        (~events["first_shock"])
        & (events["dist_high_tm1"] < DEEP_DD)
    ].copy()


def decluster_63(events: pd.DataFrame, close_index: pd.DatetimeIndex) -> pd.DataFrame:
    """Keep first qualifying day in each non-overlapping 63-session block."""
    if events.empty:
        return events
    out = events.sort_values("date").copy()
    keep = []
    next_ok_pos = -10**9
    for _, row in out.iterrows():
        p = int(close_index.get_loc(row["date"]))
        if p >= next_ok_pos:
            keep.append(True)
            next_ok_pos = p + BLOCK
        else:
            keep.append(False)
    return out.loc[keep].reset_index(drop=True)


def classify_h1b_series(close: pd.Series, label: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (summary_row_df, declustered_event_list). Never reads prices after ASOF scan end
    for classification beyond the series itself; no forward returns.
    """
    events = flag_all_events(close, "B")
    events = mark_first_shocks(events, close.index)
    if events.empty:
        summary = pd.DataFrame(
            [
                {
                    "series": label,
                    "n_state_raw": 0,
                    "n_declustered_all": 0,
                    "n_declustered_fwd_eligible": 0,
                    "first_event": pd.NaT,
                    "last_event": pd.NaT,
                    "status": STATUS_PRIOR,
                }
            ]
        )
        return summary, events

    eligible = forward_eligible_mask(events, close.index)
    events = events.copy()
    events["fwd_eligible"] = eligible.values
    state = select_h1b_state(events)
    decl = decluster_63(state, close.index)
    decl_el = decl.loc[decl["fwd_eligible"]] if len(decl) else decl
    n = int(len(decl_el))
    summary = pd.DataFrame(
        [
            {
                "series": label,
                "n_state_raw": int(len(state)),
                "n_declustered_all": int(len(decl)),
                "n_declustered_fwd_eligible": n,
                "first_event": decl_el["date"].min() if n else pd.NaT,
                "last_event": decl_el["date"].max() if n else pd.NaT,
                "status": STATUS_OK if n >= 8 else STATUS_PRIOR,
            }
        ]
    )
    if len(decl):
        decl = decl.assign(series=label)
    return summary, decl


def assert_no_forward_prices_in_module(close: pd.Series, event_date: pd.Timestamp) -> None:
    """Hard gate used by tests: classifying at t must not see prices after t."""
    if close.index.max() > event_date:
        raise LookaheadError(
            f"H1b must not read prices after event {event_date.date()}; "
            f"got max={close.index.max().date()}"
        )


def run(raw_dir: Path | None = None) -> dict:
    raw_dir = raw_dir or (ROOT / "data" / "raw" / "2026-11-08")
    exhibits = ROOT / "outputs" / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)

    summaries = []
    lists = []
    print("=== H1b EXPLORATORY — deep-DD cluster counts (rule B, dist<-20%, de-cluster 63) ===")
    print("NO FORWARD RETURNS COMPUTED.")
    for spec in SERIES:
        close = load_close(spec.symbol, raw_dir)
        summary, decl = classify_h1b_series(close, spec.label)
        summaries.append(summary)
        if len(decl):
            lists.append(decl)
        row = summary.iloc[0]
        print(
            f"{spec.label}: raw_state={row['n_state_raw']}  "
            f"declustered={row['n_declustered_all']}  "
            f"fwd_eligible={row['n_declustered_fwd_eligible']}  "
            f"[{row['status']}]"
        )

    summary_df = pd.concat(summaries, ignore_index=True)
    summary_df.to_csv(exhibits / "h1b_deep_dd_counts.csv", index=False)
    if lists:
        list_df = pd.concat(lists, ignore_index=True)
        list_df.to_csv(exhibits / "h1b_deep_dd_event_lists.csv", index=False)
    else:
        list_df = pd.DataFrame()

    print("\n=== H1b count table ===")
    print(summary_df.to_string(index=False))
    print("\n=== H1b event lists (declustered, all; mark PRIOR if N<8) ===")
    for _, row in summary_df.iterrows():
        n = int(row["n_declustered_fwd_eligible"])
        series = row["series"]
        print(f"\n{series} N_fwd_eligible={n} [{row['status']}]")
        if list_df.empty:
            continue
        sub = list_df.loc[
            (list_df["series"] == series) & (list_df["fwd_eligible"])
        ].sort_values("date")
        for _, e in sub.iterrows():
            print(
                f"  {pd.Timestamp(e['date']).date()}  ret={e['ret']:+.2%}  "
                f"dist_tm1={e['dist_high_tm1']:+.2%}"
            )

    # near-ASOF note for SOX on 5 Nov (cluster, deep DD) — classification only
    sox = load_close("^SOX", raw_dir)
    sox_ev = mark_first_shocks(flag_all_events(sox, "B"), sox.index)
    asof_row = sox_ev.loc[sox_ev["date"] == ASOF]
    if len(asof_row):
        r = asof_row.iloc[0]
        print(
            f"\nSOX @ {ASOF.date()}: first_shock={r['first_shock']}  "
            f"dist_tm1={r['dist_high_tm1']:+.2%}  "
            f"(cluster deep-DD day; not near-high first shock)"
        )

    # Register T002b BEFORE any forward return is loaded (counts only).
    tests_path = ROOT / "outputs" / "tests_run.csv"
    tests = pd.read_csv(tests_path)
    for tid in ("T002b", "P2_H1B_COUNTS"):
        tests = tests[tests["test_id"] != tid]
    n_map = {
        r.series: int(r.n_declustered_fwd_eligible) for r in summary_df.itertuples()
    }
    extra = pd.DataFrame(
        [
            {
                "test_id": "T002b",
                "hypothesis": "H1b",
                "description": (
                    "EXPLORATORY: semis deep-drawdown cluster days have worse "
                    "63-session forward outcomes than S&P days in the same state "
                    "(rule B, dist<-20%, cluster; de-cluster 63-session blocks)"
                ),
                "status": "EXPLORATORY",
                "raw_p": "",
                "bh_p": "",
                "effect": "",
                "n": "",
                "notes": (
                    f"registered before any forward returns; counts N={n_map}; "
                    "apply N>=8 floor; see h1b_deep_dd_counts.csv"
                ),
            },
            {
                "test_id": "P2_H1B_COUNTS",
                "hypothesis": "H1b",
                "description": "H1b deep-DD cluster de-clustered counts by series",
                "status": "PASS",
                "raw_p": "",
                "bh_p": "",
                "effect": "",
                "n": int(summary_df["n_declustered_fwd_eligible"].sum()),
                "notes": "counts only; no forward returns; see h1b_deep_dd_event_lists.csv",
            },
        ]
    )
    pd.concat([tests, extra], ignore_index=True).to_csv(tests_path, index=False)

    return {"summary": summary_df, "events": list_df}


def main() -> None:
    run()


if __name__ == "__main__":
    main()
