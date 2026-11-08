"""H1 P2 — power check only. COUNTS. No forward returns / drawdowns / post-event prices.

Governing constraints for this phase:
  - Use Close (price), not total return.
  - Trailing vol at event t uses returns through t−1 only.
  - Distance bands use t−1 close vs trailing 252d closing high through t−1.
  - Never read a price dated after the event date when classifying that event.
  - Events within 63 sessions of 2026-11-05 are excluded from forward-eligible
    counts and listed separately (includes 5 Nov itself).

Rules (separate FDR family members when tested later):
  A: one-day close-to-close return <= −4%
  B: return <= −2.5 × trailing 252d daily stdev (to t−1)

First shock: no qualifying event in the prior 126 sessions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.config_io import ROOT
from src.ingest.yahoo import fetch_yahoo_ohlcv

ASOF = pd.Timestamp("2026-11-05")
HORIZON_EXCLUDE = 63  # sessions: events within this of ASOF → not forward-eligible
FIRST_SHOCK_WINDOW = 126
VOL_WINDOW = 252
HIGH_WINDOW = 252
ABS_THRESHOLD = -0.04
SIGMA_MULT = -2.5

# Control reproduction window for the 151-event fixture
SPX_FIXTURE_START = pd.Timestamp("1928-01-01")
SPX_FIXTURE_END = pd.Timestamp("2019-12-31")
SPX_FIXTURE_N_EVENTS = 151


@dataclass(frozen=True)
class SeriesSpec:
    symbol: str
    label: str


SERIES = (
    SeriesSpec("^GSPC", "SPX"),
    SeriesSpec("^IXIC", "IXIC"),
    SeriesSpec("^SOX", "SOX"),
    SeriesSpec("SMH", "SMH"),
    SeriesSpec("SOXX", "SOXX"),
)


class LookaheadError(RuntimeError):
    pass


def _assert_no_future(prices: pd.Series, event_date: pd.Timestamp) -> None:
    """Fail if `prices` contains any index date after event_date."""
    if len(prices) and prices.index.max() > event_date:
        raise LookaheadError(
            f"P2 must not read prices after event {event_date.date()}; "
            f"got max={prices.index.max().date()}"
        )


def load_close(symbol: str, raw_dir: Path) -> pd.Series:
    df = fetch_yahoo_ohlcv(symbol, "1928-01-01", "2026-11-05", raw_dir, use_cache=True)
    s = df["Close"].astype(float).dropna()
    s.index = pd.to_datetime(s.index).normalize()
    return s.sort_index()


def daily_returns(close: pd.Series) -> pd.Series:
    return close.pct_change()


def trailing_sigma_to_t_minus_1(returns: pd.Series, t: pd.Timestamp, window: int = VOL_WINDOW) -> float:
    """Stdev of daily returns using observations with date <= t−1 only."""
    loc = returns.index.get_loc(t)
    if isinstance(loc, slice):
        raise KeyError(t)
    # returns.iloc[loc] is ret at t (uses close t and t-1); exclude it
    hist = returns.iloc[max(0, loc - window) : loc]  # up to but not including t
    hist = hist.dropna()
    if len(hist) < window:
        return float("nan")
    return float(hist.iloc[-window:].std(ddof=1))


def dist_from_high_at_t_minus_1(close: pd.Series, t: pd.Timestamp, window: int = HIGH_WINDOW) -> float:
    """(close[t−1] / max close over window ending t−1) − 1."""
    loc = close.index.get_loc(t)
    if isinstance(loc, slice) or loc < 1:
        return float("nan")
    # only prices through t-1
    through = close.iloc[:loc]  # excludes t
    _assert_no_future(through, close.index[loc - 1])
    if len(through) < window:
        return float("nan")
    window_px = through.iloc[-window:]
    peak = float(window_px.max())
    c_tm1 = float(window_px.iloc[-1])
    if peak <= 0:
        return float("nan")
    return c_tm1 / peak - 1.0


def classify_event_at_t(
    close: pd.Series,
    t: pd.Timestamp,
    rule: str,
) -> dict | None:
    """Classify a single date using prices through t only. Returns None if not an event.

    Raises LookaheadError if `close` contains any date after t (P2 hard gate).
    """
    _assert_no_future(close, t)
    close_t = close.loc[:t]
    if t not in close_t.index:
        return None
    loc = close_t.index.get_loc(t)
    if isinstance(loc, slice) or loc < 1:
        return None
    rets = daily_returns(close_t)
    ret_t = float(rets.loc[t])
    if not np.isfinite(ret_t):
        return None

    if rule == "A":
        hit = ret_t <= ABS_THRESHOLD
        sigma = np.nan
    elif rule == "B":
        sigma = trailing_sigma_to_t_minus_1(rets, t)
        if not np.isfinite(sigma) or sigma <= 0:
            return None
        hit = ret_t <= SIGMA_MULT * sigma
    else:
        raise ValueError(rule)
    if not hit:
        return None

    dist = dist_from_high_at_t_minus_1(close_t, t)
    if not np.isfinite(dist):
        return None

    return {
        "date": t,
        "ret": ret_t,
        "sigma": sigma,
        "dist_high_tm1": dist,
        "band_le5": dist >= -0.05,
        "band_le10": dist >= -0.10,
        "band_gt10": dist < -0.10,
    }


def flag_all_events(close: pd.Series, rule: str) -> pd.DataFrame:
    """Scan series with causal (no-lookahead) vectorised features.

    Equivalence to per-date truncated classify_event_at_t is asserted in tests.
    """
    rets = daily_returns(close)
    # sigma at t uses returns through t-1 only
    sigma = rets.shift(1).rolling(VOL_WINDOW, min_periods=VOL_WINDOW).std(ddof=1)
    # dist at t uses close[t-1] vs max of closes ending t-1
    close_tm1 = close.shift(1)
    high_tm1 = close.shift(1).rolling(HIGH_WINDOW, min_periods=HIGH_WINDOW).max()
    dist = close_tm1 / high_tm1 - 1.0

    if rule == "A":
        hit = rets <= ABS_THRESHOLD
    elif rule == "B":
        hit = rets <= SIGMA_MULT * sigma
    else:
        raise ValueError(rule)

    ok = hit & dist.notna() & rets.notna()
    if rule == "B":
        ok = ok & sigma.notna() & (sigma > 0)

    idx = close.index[ok.fillna(False)]
    rows = []
    for t in idx:
        d = float(dist.loc[t])
        rows.append(
            {
                "date": t,
                "ret": float(rets.loc[t]),
                "sigma": float(sigma.loc[t]) if rule == "B" else np.nan,
                "dist_high_tm1": d,
                "band_le5": d >= -0.05,
                "band_le10": d >= -0.10,
                "band_gt10": d < -0.10,
            }
        )
    return pd.DataFrame(rows)


def mark_first_shocks(events: pd.DataFrame, close_index: pd.DatetimeIndex) -> pd.DataFrame:
    if events.empty:
        return events.assign(first_shock=False, cluster=False)
    out = events.copy()
    out["first_shock"] = False
    out["cluster"] = False
    # map dates to positions in full calendar
    pos = {d: close_index.get_loc(d) for d in out["date"]}
    event_pos = sorted(pos[d] for d in out["date"])
    first_flags = []
    for d in out["date"]:
        p = pos[d]
        prior = [q for q in event_pos if p - FIRST_SHOCK_WINDOW <= q < p]
        first_flags.append(len(prior) == 0)
    out["first_shock"] = first_flags
    # Cluster day = not a first shock (another qualifying event in prior 126 sessions).
    # Note: 151 SPX −4% days → 26 first shocks + 125 cluster days.
    out["cluster"] = ~out["first_shock"]
    return out


def forward_eligible_mask(events: pd.DataFrame, close_index: pd.DatetimeIndex) -> pd.Series:
    """False if event is within HORIZON_EXCLUDE sessions of ASOF."""
    if ASOF not in close_index:
        # find nearest
        asof_loc = close_index.get_indexer([ASOF], method="pad")[0]
    else:
        asof_loc = close_index.get_loc(ASOF)
    if isinstance(asof_loc, slice):
        raise RuntimeError("ASOF indexer failed")
    ok = []
    for d in events["date"]:
        p = close_index.get_loc(d)
        ok.append(abs(int(p) - int(asof_loc)) > HORIZON_EXCLUDE)
    return pd.Series(ok, index=events.index)


def band_label(row: pd.Series) -> str:
    if row["band_le5"]:
        return "le5"
    if row["band_le10"]:
        return "le10_ex5"  # between 5 and 10 — for exclusive listing
    return "gt10"


def power_table_for_series(close: pd.Series, label: str, rule: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Returns (summary_rows, event_list, excluded_near_asof)."""
    events = flag_all_events(close, rule)
    events = mark_first_shocks(events, close.index)
    if events.empty:
        summary = pd.DataFrame(
            [
                {
                    "series": label,
                    "rule": rule,
                    "band": band,
                    "n_first_shocks_fwd_eligible": 0,
                    "n_cluster_days_all": 0,
                    "n_first_shocks_all": 0,
                    "first_event": None,
                    "last_event": None,
                    "status": "PRIOR_ONLY_NOT_TESTED",
                }
                for band in ("le5", "le10", "gt10")
            ]
        )
        return summary, events, events

    eligible = forward_eligible_mask(events, close.index)
    events = events.copy()
    events["fwd_eligible"] = eligible.values
    excluded = events.loc[~events["fwd_eligible"]].copy()
    excl_note = excluded.assign(series=label, rule=rule)

    rows = []
    for band, mask_col, exclusive in (
        ("le5", "band_le5", False),
        ("le10", "band_le10", False),  # cumulative <=10% as in the note
        ("gt10", "band_gt10", False),
    ):
        sub_all = events.loc[events[mask_col]]
        sub_first_all = sub_all.loc[sub_all["first_shock"]]
        sub_first_el = sub_first_all.loc[sub_first_all["fwd_eligible"]]
        sub_cluster = sub_all.loc[sub_all["cluster"]]
        n = int(len(sub_first_el))
        status = "PRIOR_ONLY_NOT_TESTED" if n < 8 else "POWERED"
        rows.append(
            {
                "series": label,
                "rule": rule,
                "band": band,
                "n_first_shocks_fwd_eligible": n,
                "n_first_shocks_all": int(len(sub_first_all)),
                "n_cluster_days_all": int(len(sub_cluster)),
                "n_all_events_in_band": int(len(sub_all)),
                "first_event": sub_first_el["date"].min() if n else pd.NaT,
                "last_event": sub_first_el["date"].max() if n else pd.NaT,
                "status": status,
            }
        )
    return pd.DataFrame(rows), events, excl_note


def reproduce_spx_151(close: pd.Series) -> dict:
    """Control: count rule-A events on ^GSPC from 1928 through 2019."""
    sub = close.loc[SPX_FIXTURE_START:SPX_FIXTURE_END]
    events = flag_all_events(sub, "A")
    n = len(events)
    return {
        "n_events": n,
        "target": SPX_FIXTURE_N_EVENTS,
        "match": n == SPX_FIXTURE_N_EVENTS,
        "first": events["date"].min() if n else None,
        "last": events["date"].max() if n else None,
    }


def overlap_note(metas: dict[str, pd.Series]) -> str:
    lines = []
    labels = list(metas)
    for i, a in enumerate(labels):
        for b in labels[i + 1 :]:
            ia, ib = metas[a].index, metas[b].index
            inter = ia.intersection(ib)
            if len(inter):
                lines.append(
                    f"{a} ∩ {b}: {inter.min().date()} → {inter.max().date()} "
                    f"({len(inter)} sessions) — NOT independent; do not pool"
                )
    return "\n".join(lines)


def run(raw_dir: Path | None = None) -> dict:
    raw_dir = raw_dir or (ROOT / "data" / "raw" / "2026-11-08")
    raw_dir.mkdir(parents=True, exist_ok=True)
    exhibits = ROOT / "outputs" / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)

    closes: dict[str, pd.Series] = {}
    inception = []
    for spec in SERIES:
        s = load_close(spec.symbol, raw_dir)
        closes[spec.label] = s
        inception.append(
            {
                "series": spec.label,
                "yahoo_symbol": spec.symbol,
                "first_date": s.index.min(),
                "last_date": s.index.max(),
                "n_sessions": len(s),
            }
        )
    inception_df = pd.DataFrame(inception)
    inception_df.to_csv(exhibits / "h1_series_inception.csv", index=False)
    print("=== Inception ===")
    print(inception_df.to_string(index=False))

    # SPX 151 control
    spx_ctrl = reproduce_spx_151(closes["SPX"])
    print("\n=== SPX 1928-2019 rule A control ===")
    print(spx_ctrl)
    if not spx_ctrl["match"]:
        print(
            f"WARNING: expected {SPX_FIXTURE_N_EVENTS} events, got {spx_ctrl['n_events']} "
            "(will still produce power table; do not retarget fixture silently)"
        )

    summaries = []
    all_events = []
    excluded_all = []
    small_cells = []

    for spec in SERIES:
        for rule in ("A", "B"):
            print(f"\nScanning {spec.label} rule {rule} ...", flush=True)
            summary, events, excluded = power_table_for_series(closes[spec.label], spec.label, rule)
            summaries.append(summary)
            if len(events):
                ev = events.copy()
                ev["series"] = spec.label
                ev["rule"] = rule
                all_events.append(ev)
            if len(excluded):
                excluded_all.append(excluded)
            for _, row in summary.iterrows():
                if row["n_first_shocks_fwd_eligible"] < 10:
                    # full event list for the cell
                    mask = {
                        "le5": "band_le5",
                        "le10": "band_le10",
                        "gt10": "band_gt10",
                    }[row["band"]]
                    cell = events.loc[events["first_shock"] & events["fwd_eligible"] & events[mask]]
                    for _, e in cell.iterrows():
                        small_cells.append(
                            {
                                "series": spec.label,
                                "rule": rule,
                                "band": row["band"],
                                "date": e["date"],
                                "ret": e["ret"],
                                "dist_high_tm1": e["dist_high_tm1"],
                                "n_cell": row["n_first_shocks_fwd_eligible"],
                                "status": row["status"],
                            }
                        )

    summary_df = pd.concat(summaries, ignore_index=True)
    summary_df.to_csv(exhibits / "h1_power_table.csv", index=False)
    if all_events:
        pd.concat(all_events, ignore_index=True).to_csv(exhibits / "h1_all_events.csv", index=False)
    if excluded_all:
        pd.concat(excluded_all, ignore_index=True).to_csv(
            exhibits / "h1_events_near_asof_excluded.csv", index=False
        )
    small_df = pd.DataFrame(small_cells)
    small_df.to_csv(exhibits / "h1_small_cell_event_lists.csv", index=False)

    print("\n=== POWER TABLE (fwd-eligible first shocks) ===")
    print(summary_df.to_string(index=False))
    print("\n=== Cells with N < 10 (full event lists) ===")
    if len(small_df):
        for (series, rule, band), g in small_df.groupby(["series", "rule", "band"]):
            print(f"\n{series} rule {rule} band {band} N={len(g)} [{g['status'].iloc[0]}]")
            for _, r in g.iterrows():
                print(
                    f"  {pd.Timestamp(r['date']).date()}  ret={r['ret']:+.2%}  "
                    f"dist_tm1={r['dist_high_tm1']:+.2%}"
                )
    else:
        print("(none)")

    print("\n=== Series overlap (do not pool) ===")
    print(overlap_note(closes))

    print("\n=== Events within 63 sessions of 2026-11-05 (excluded from fwd-eligible) ===")
    if excluded_all:
        ex = pd.concat(excluded_all, ignore_index=True)
        print(ex.groupby(["series", "rule"]).size().to_string())
        print(ex[["series", "rule", "date", "ret", "dist_high_tm1", "first_shock"]].to_string(index=False))
    else:
        print("(none)")

    # Log PLANNED Fisher test
    tests_path = ROOT / "outputs" / "tests_run.csv"
    tests = pd.read_csv(tests_path)
    tests = tests[tests["test_id"] != "T002"]
    planned = {
        "test_id": "T002",
        "hypothesis": "H1",
        "description": (
            "Fisher exact further-10pct DD within 63d: semis vs SPX, "
            "near-high (le5) first-shock cell — PLANNED after power check"
        ),
        "status": "PLANNED",
        "raw_p": "",
        "bh_p": "",
        "effect": "",
        "n": "",
        "notes": (
            f"P2 power only; SPX_1928_2019_ruleA_n={spx_ctrl['n_events']} "
            f"(target 151, match={spx_ctrl['match']}); "
            "no forward returns computed this phase"
        ),
    }
    # also log P2 power check rows
    for tid in ("P2_H1_POWER", "P2_SPX_151_CONTROL"):
        tests = tests[tests["test_id"] != tid]
    extra = pd.DataFrame(
        [
            planned,
            {
                "test_id": "P2_SPX_151_CONTROL",
                "hypothesis": "H1",
                "description": "Reproduce 151 SPX <=-4% days 1928-2019",
                "status": "PASS" if spx_ctrl["match"] else "FAIL",
                "raw_p": "",
                "bh_p": "",
                "effect": spx_ctrl["n_events"],
                "n": spx_ctrl["n_events"],
                "notes": f"first={spx_ctrl['first']} last={spx_ctrl['last']}",
            },
            {
                "test_id": "P2_H1_POWER",
                "hypothesis": "H1",
                "description": "Power check N first shocks by series/rule/band (fwd-eligible)",
                "status": "PASS",
                "raw_p": "",
                "bh_p": "",
                "effect": "",
                "n": int(summary_df["n_first_shocks_fwd_eligible"].sum()),
                "notes": "counts only; N<8 PRIOR_ONLY_NOT_TESTED; see h1_power_table.csv",
            },
        ]
    )
    pd.concat([tests, extra], ignore_index=True).to_csv(tests_path, index=False)

    return {
        "spx_control": spx_ctrl,
        "summary": summary_df,
        "inception": inception_df,
    }


def main() -> None:
    run()


if __name__ == "__main__":
    main()
