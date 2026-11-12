"""H1b forward returns — run ONLY after RESULTS.md H1b design freeze.

Primary T002b: SOX vs SPX Fisher exact on further-10% DD within 63 sessions.
T002c: IXIC vs SOX sensitivity (same era).
SMH/SOXX: robustness descriptive only (no p-values).

Bootstrap unit = bear-market episode (events <252 sessions apart).
Decision rule uses SOX's own further-10% rate (see RESULTS.md).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

from core.config_io import ROOT, study_outputs
from src.h1_power_check import SERIES, load_close
from src.h1b_deep_dd_counts import classify_h1b_series

EPISODE_GAP = 252  # sessions: consecutive events closer than this → same episode
DD_HORIZON = 63
DD_THRESHOLD = -0.10
RET_HORIZONS = (21, 63, 252)


def assign_episode_ids(events: pd.DataFrame, close_index: pd.DatetimeIndex) -> pd.DataFrame:
    """Episode = run of events with consecutive gaps < EPISODE_GAP sessions."""
    if events.empty:
        return events.assign(episode_id=pd.Series(dtype=str))
    out = events.sort_values("date").copy()
    ids = []
    ep_num = 0
    prev_pos = None
    for _, row in out.iterrows():
        p = int(close_index.get_loc(row["date"]))
        if prev_pos is None or (p - prev_pos) >= EPISODE_GAP:
            ep_num += 1
        ids.append(f"{row['series']}_E{ep_num:02d}")
        prev_pos = p
    out["episode_id"] = ids
    return out


def forward_metrics(close: pd.Series, event_date: pd.Timestamp) -> dict:
    """+21/+63/+252 returns and max further DD within 63 from event close.

    Returns NaN for horizons that lack enough subsequent sessions.
    """
    if event_date not in close.index:
        raise KeyError(event_date)
    loc = int(close.index.get_loc(event_date))
    c0 = float(close.iloc[loc])
    out: dict = {"date": event_date}
    for h in RET_HORIZONS:
        if loc + h < len(close):
            out[f"ret_p{h}"] = float(close.iloc[loc + h] / c0 - 1.0)
        else:
            out[f"ret_p{h}"] = float("nan")
    # max further drawdown within 63 = min relative level over next 63 sessions
    end = min(loc + DD_HORIZON, len(close) - 1)
    if end <= loc:
        out["max_dd_63"] = float("nan")
        out["further_dd_10"] = False
        out["n_fwd_sessions"] = 0
    else:
        path = close.iloc[loc + 1 : end + 1].astype(float) / c0 - 1.0
        mdd = float(path.min()) if len(path) else float("nan")
        out["max_dd_63"] = mdd
        out["n_fwd_sessions"] = int(len(path))
        # only score the binary if full 63 sessions observed
        if len(path) >= DD_HORIZON and np.isfinite(mdd):
            out["further_dd_10"] = bool(mdd <= DD_THRESHOLD)
        else:
            out["further_dd_10"] = False
            out["max_dd_63"] = mdd if np.isfinite(mdd) else float("nan")
            out["dd63_incomplete"] = True
    return out


def build_event_panel(raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (per-event metrics with episode IDs, episode summary)."""
    rows = []
    ep_rows = []
    for spec in SERIES:
        close = load_close(spec.symbol, raw_dir)
        _summary, decl = classify_h1b_series(close, spec.label)
        if decl.empty:
            continue
        # fwd-eligible only for the tested sample
        decl = decl.loc[decl["fwd_eligible"]].copy()
        decl = assign_episode_ids(decl, close.index)
        for _, ev in decl.iterrows():
            m = forward_metrics(close, pd.Timestamp(ev["date"]))
            rows.append(
                {
                    "series": spec.label,
                    "episode_id": ev["episode_id"],
                    "date": ev["date"],
                    "ret_event": float(ev["ret"]),
                    "dist_high_tm1": float(ev["dist_high_tm1"]),
                    **{k: m[k] for k in m if k != "date"},
                }
            )
        for eid, g in decl.groupby("episode_id", sort=True):
            ep_rows.append(
                {
                    "series": spec.label,
                    "episode_id": eid,
                    "n_events": len(g),
                    "first_date": g["date"].min(),
                    "last_date": g["date"].max(),
                }
            )
    panel = pd.DataFrame(rows)
    episodes = pd.DataFrame(ep_rows)
    return panel, episodes


def fisher_further_dd(
    panel: pd.DataFrame,
    a: str,
    b: str,
    min_date: pd.Timestamp | None = None,
) -> dict:
    """Fisher exact: series a vs b on further_dd_10 among complete 63d paths.

    If min_date is set (e.g. SOX inception for T002c same-era sensitivity),
    both series are truncated to event dates >= min_date.
    """
    def cell(series: str) -> tuple[int, int]:
        sub = panel.loc[
            (panel["series"] == series)
            & (panel["n_fwd_sessions"] >= DD_HORIZON)
        ]
        if min_date is not None:
            sub = sub.loc[pd.to_datetime(sub["date"]) >= min_date]
        pos = int(sub["further_dd_10"].sum())
        neg = int((~sub["further_dd_10"]).sum())
        return pos, neg

    a_pos, a_neg = cell(a)
    b_pos, b_neg = cell(b)
    table = np.array([[a_pos, a_neg], [b_pos, b_neg]])
    # scipy: rows = groups, cols = (success, failure); oddsratio for first row
    odds, p = fisher_exact(table, alternative="two-sided")
    n_a, n_b = a_pos + a_neg, b_pos + b_neg
    rate_a = a_pos / n_a if n_a else float("nan")
    rate_b = b_pos / n_b if n_b else float("nan")
    return {
        "group_a": a,
        "group_b": b,
        "a_dd": a_pos,
        "a_no": a_neg,
        "b_dd": b_pos,
        "b_no": b_neg,
        "rate_a": rate_a,
        "rate_b": rate_b,
        "odds_ratio": float(odds) if np.isfinite(odds) else float("nan"),
        "raw_p": float(p),
        "table": table.tolist(),
        "min_date": str(min_date.date()) if min_date is not None else "",
    }


def sox_decision(rate: float) -> str:
    if not np.isfinite(rate):
        return "INCONCLUSIVE — no SOX rate"
    if rate >= 0.50:
        return (
            "DO_NOT_ADD_SUPPLIER_BETA — further-10% DD in ≥50% of SOX events; "
            "sizing must assume another leg"
        )
    if rate <= 0.25:
        return (
            "PATIENCE_SUPPORTED — further-10% DD in ≤25% of SOX events; "
            "sector history supports the patience reading"
        )
    return (
        "INCONCLUSIVE — SOX further-10% rate between 25% and 50%; "
        "book decision rests on H2/H5"
    )


def descriptive_rate(panel: pd.DataFrame, series: str) -> dict:
    sub = panel.loc[
        (panel["series"] == series) & (panel["n_fwd_sessions"] >= DD_HORIZON)
    ]
    n = len(sub)
    k = int(sub["further_dd_10"].sum()) if n else 0
    return {
        "series": series,
        "n": n,
        "n_further_dd_10": k,
        "rate": (k / n) if n else float("nan"),
        "median_ret_p21": float(sub["ret_p21"].median()) if n else float("nan"),
        "median_ret_p63": float(sub["ret_p63"].median()) if n else float("nan"),
        "median_ret_p252": float(sub["ret_p252"].median()) if n else float("nan"),
        "median_max_dd_63": float(sub["max_dd_63"].median()) if n else float("nan"),
    }


def print_event_list(panel: pd.DataFrame, series: str) -> None:
    sub = panel.loc[panel["series"] == series].sort_values("date")
    n = len(sub)
    print(f"\n=== {series} per-event forward metrics (N={n}) ===")
    if n >= 20:
        print("(N>=20; still printing full list per freeze note for H1b)")
    for _, r in sub.iterrows():
        dd_flag = "DD10" if r.get("further_dd_10") else "ok"
        print(
            f"  {pd.Timestamp(r['date']).date()}  ep={r['episode_id']}  "
            f"ret21={r['ret_p21']:+.2%}  ret63={r['ret_p63']:+.2%}  "
            f"ret252={r['ret_p252']:+.2%}  maxDD63={r['max_dd_63']:+.2%}  [{dd_flag}]"
        )


def upsert_tests(rows: list[dict]) -> None:
    path = study_outputs() / "tests_run.csv"
    tests = pd.read_csv(path)
    for row in rows:
        tests = tests[tests["test_id"] != row["test_id"]]
    pd.concat([tests, pd.DataFrame(rows)], ignore_index=True).to_csv(path, index=False)


def run(raw_dir: Path | None = None) -> dict:
    raw_dir = raw_dir or (ROOT / "data" / "raw" / "2026-11-08")
    exhibits = study_outputs() / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)

    print("=== H1b FORWARD RETURNS (design frozen in RESULTS.md) ===")
    panel, episodes = build_event_panel(raw_dir)
    panel.to_csv(exhibits / "h1b_forward_events.csv", index=False)
    episodes.to_csv(exhibits / "h1b_episodes.csv", index=False)

    print("\n=== Episode IDs (bootstrap unit; gap < 252 sessions) ===")
    print(episodes.to_string(index=False))

    # Primary + sensitivity Fisher
    t002b = fisher_further_dd(panel, "SOX", "SPX")
    # T002c same-era: truncate both to SOX sample start
    sox_start = pd.to_datetime(panel.loc[panel["series"] == "SOX", "date"]).min()
    t002c = fisher_further_dd(panel, "IXIC", "SOX", min_date=sox_start)
    print("\n=== T002b Fisher SOX vs SPX (further 10% DD / 63d) ===")
    print(t002b)
    print("\n=== T002c Fisher IXIC vs SOX (sensitivity, same era) ===")
    print(t002c)

    # Robustness descriptive
    desc = [descriptive_rate(panel, s) for s in ("SPX", "SOX", "SMH", "SOXX", "IXIC")]
    desc_df = pd.DataFrame(desc)
    desc_df.to_csv(exhibits / "h1b_forward_summary.csv", index=False)
    print("\n=== Descriptive rates (SMH/SOXX = robustness, no p-values) ===")
    print(desc_df.to_string(index=False))

    sox_rate = float(desc_df.loc[desc_df["series"] == "SOX", "rate"].iloc[0])
    decision = sox_decision(sox_rate)
    print(f"\n=== SOX decision rule ===\nrate={sox_rate:.2%} → {decision}")

    for s in ("SPX", "SOX", "SMH", "SOXX", "IXIC"):
        print_event_list(panel, s)

    # Log FDR rows with raw p
    upsert_tests(
        [
            {
                "test_id": "T002b",
                "hypothesis": "H1b",
                "description": (
                    "Fisher exact further-10pct DD within 63d: SOX vs SPX "
                    "de-clustered deep-DD cluster events"
                ),
                "status": "RUN",
                "raw_p": t002b["raw_p"],
                "bh_p": "",
                "effect": t002b["odds_ratio"],
                "n": t002b["a_dd"] + t002b["a_no"] + t002b["b_dd"] + t002b["b_no"],
                "notes": (
                    f"SOX {t002b['a_dd']}/{t002b['a_dd']+t002b['a_no']}="
                    f"{t002b['rate_a']:.3f}; SPX {t002b['b_dd']}/"
                    f"{t002b['b_dd']+t002b['b_no']}={t002b['rate_b']:.3f}; "
                    f"decision={decision}"
                ),
            },
            {
                "test_id": "T002c",
                "hypothesis": "H1b",
                "description": (
                    "Fisher exact further-10pct DD within 63d: IXIC vs SOX "
                    "(sensitivity, same era)"
                ),
                "status": "RUN",
                "raw_p": t002c["raw_p"],
                "bh_p": "",
                "effect": t002c["odds_ratio"],
                "n": t002c["a_dd"] + t002c["a_no"] + t002c["b_dd"] + t002c["b_no"],
                "notes": (
                    f"IXIC {t002c['a_dd']}/{t002c['a_dd']+t002c['a_no']}="
                    f"{t002c['rate_a']:.3f}; SOX {t002c['b_dd']}/"
                    f"{t002c['b_dd']+t002c['b_no']}={t002c['rate_b']:.3f}"
                ),
            },
            {
                "test_id": "P2_H1B_FORWARD",
                "hypothesis": "H1b",
                "description": "H1b forward returns + episode IDs + SOX decision rule",
                "status": "PASS",
                "raw_p": "",
                "bh_p": "",
                "effect": sox_rate,
                "n": int(len(panel)),
                "notes": decision,
            },
        ]
    )

    return {
        "panel": panel,
        "episodes": episodes,
        "t002b": t002b,
        "t002c": t002c,
        "desc": desc_df,
        "sox_rate": sox_rate,
        "decision": decision,
    }


def main() -> None:
    run()


if __name__ == "__main__":
    main()
