"""Split / large-move audit.

Policy (P1):
  - Scope: equity + ETF columns only (exclude ^INDEX symbols).
  - Every Yahoo-reported split in the raw cache must be listed in
    config/corporate_actions.yaml (date ±5 sessions) or the build fails.
  - Single-day |ret| > 25% *without* a Yahoo split event is logged as a
    market gap (earnings etc.) and does **not** fail the build.
  - |ret| > 25% *with* a Yahoo split must match corporate_actions.yaml.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from src.config_io import ROOT


def load_corporate_actions() -> pd.DataFrame:
    path = ROOT / "config" / "corporate_actions.yaml"
    data = yaml.safe_load(path.read_text())["actions"]
    return pd.DataFrame(data)


def equity_columns(columns: list[str] | pd.Index) -> list[str]:
    return [c for c in columns if not str(c).startswith("^")]


def flag_large_moves(
    close: pd.DataFrame,
    threshold: float = 0.25,
) -> pd.DataFrame:
    cols = equity_columns(list(close.columns))
    rets = close[cols].pct_change()
    records = []
    for col in rets.columns:
        s = rets[col].dropna()
        hit = s[s.abs() > threshold]
        for dt, ret in hit.items():
            records.append(
                {
                    "ticker": col,
                    "date": pd.Timestamp(dt).strftime("%Y-%m-%d"),
                    "ret": float(ret),
                }
            )
    return pd.DataFrame(records)


def yahoo_splits_from_raw(raw_dir: Path) -> pd.DataFrame:
    """Parse split events from cached Yahoo chart JSON."""
    rows = []
    for path in sorted(raw_dir.glob("yahoo_*.json")):
        # yahoo_MSFT.json or yahoo__GSPC.json
        stem = path.stem[len("yahoo_") :]
        ticker = stem if not stem.startswith("_") else "^" + stem[1:]
        if ticker.startswith("^"):
            continue
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        result = (payload.get("chart") or {}).get("result") or []
        if not result:
            continue
        events = result[0].get("events") or {}
        splits = events.get("splits") or {}
        for _key, sp in splits.items():
            # sp: date, numerator, denominator, splitRatio
            ts = pd.to_datetime(sp.get("date"), unit="s", utc=True).tz_convert(None)
            rows.append(
                {
                    "ticker": ticker,
                    "date": ts.strftime("%Y-%m-%d"),
                    "numerator": sp.get("numerator"),
                    "denominator": sp.get("denominator"),
                    "splitRatio": sp.get("splitRatio"),
                    "source": "yahoo_events",
                }
            )
    return pd.DataFrame(rows)


def audit_large_moves(
    close: pd.DataFrame,
    raw_dir: Path,
    threshold: float = 0.25,
    date_tolerance_days: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Return (gap_log, split_report, failure_messages)."""
    flags = flag_large_moves(close, threshold=threshold)
    ysplits = yahoo_splits_from_raw(raw_dir)
    actions = load_corporate_actions()
    failures: list[str] = []

    # 1) Every Yahoo split must be in corporate_actions.yaml
    split_rows = []
    for _, sp in ysplits.iterrows() if len(ysplits) else []:
        sub = actions[actions["ticker"] == sp["ticker"]]
        ok = False
        for _, act in sub.iterrows():
            if abs((pd.Timestamp(sp["date"]) - pd.Timestamp(act["date"])).days) <= date_tolerance_days:
                ok = True
                break
        split_rows.append({**sp.to_dict(), "in_corporate_actions": ok})
        if not ok:
            failures.append(
                f"Yahoo split {sp['ticker']} {sp['date']} ratio={sp.get('splitRatio')} "
                f"missing from corporate_actions.yaml"
            )

    # 2) Large moves: annotate whether Yahoo had a split; only fail if split unexplained
    gap_rows = []
    for _, row in flags.iterrows() if len(flags) else []:
        has_split = False
        if len(ysplits):
            near = ysplits[
                (ysplits["ticker"] == row["ticker"])
                & (
                    (pd.to_datetime(ysplits["date"]) - pd.Timestamp(row["date"]))
                    .abs()
                    .dt.days
                    <= date_tolerance_days
                )
            ]
            has_split = len(near) > 0
        kind = "split_related" if has_split else "market_gap"
        explained = True
        reason = "yahoo_split+corporate_actions" if has_split else "no_split_event_treated_as_gap"
        if has_split:
            # must be in corporate actions
            sub = actions[actions["ticker"] == row["ticker"]]
            explained = False
            for _, act in sub.iterrows():
                if abs((pd.Timestamp(row["date"]) - pd.Timestamp(act["date"])).days) <= date_tolerance_days:
                    explained = True
                    reason = f"corporate_actions {act.get('type')} {act.get('ratio')}"
                    break
            if not explained:
                failures.append(
                    f"{row['ticker']} {row['date']} ret={row['ret']:+.2%} coincides with "
                    f"Yahoo split but not listed in corporate_actions.yaml"
                )
        gap_rows.append({**row.to_dict(), "kind": kind, "explained": explained, "reason": reason})

    return pd.DataFrame(gap_rows), pd.DataFrame(split_rows), failures


def sync_corporate_actions_from_yahoo(raw_dir: Path) -> int:
    """Append any Yahoo splits missing from corporate_actions.yaml. Returns count added."""
    path = ROOT / "config" / "corporate_actions.yaml"
    data = yaml.safe_load(path.read_text())
    actions = data.get("actions") or []
    existing = {(a["ticker"], a["date"]) for a in actions}
    ysplits = yahoo_splits_from_raw(raw_dir)
    added = 0
    for _, sp in ysplits.iterrows() if len(ysplits) else []:
        key = (sp["ticker"], sp["date"])
        # also treat near-duplicates
        if any(
            a["ticker"] == sp["ticker"]
            and abs((pd.Timestamp(a["date"]) - pd.Timestamp(sp["date"])).days) <= 5
            for a in actions
        ):
            continue
        actions.append(
            {
                "ticker": sp["ticker"],
                "date": sp["date"],
                "type": "split",
                "ratio": sp.get("splitRatio") or f"{sp.get('numerator')}:{sp.get('denominator')}",
                "note": "auto-imported from Yahoo chart events during P1",
            }
        )
        added += 1
    data["actions"] = actions
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return added
