"""Split / large-move audit.

Policy (P2 refresh):
  - Scope: equity + ETF columns only (exclude ^INDEX symbols).
  - Every Yahoo-reported split in the raw cache must be listed in
    config/corporate_actions.yaml (date ±5 sessions) or the build fails.
  - Every single-day |ret| > 25% must have a sourced reason in
    config/large_move_reasons.yaml (category ∈ {earnings, deal, ipo_listing, split}
    with a non-empty source URL). No auto-explain. Unexplained = build fails.
  - |ret| > 25% that coincides with a Yahoo split must also match
    corporate_actions.yaml.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from core.config_io import reference_path

ALLOWED_REASON_CATEGORIES = frozenset({"earnings", "deal", "ipo_listing", "split"})


def load_corporate_actions() -> pd.DataFrame:
    path = reference_path("corporate_actions")
    data = yaml.safe_load(path.read_text())["actions"]
    return pd.DataFrame(data)


def load_large_move_reasons() -> pd.DataFrame:
    path = reference_path("large_move_reasons")
    data = yaml.safe_load(path.read_text())
    moves = data.get("moves") or []
    df = pd.DataFrame(moves)
    if df.empty:
        return pd.DataFrame(
            columns=["ticker", "date", "category", "reason", "source", "source_title"]
        )
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df


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


def _lookup_reason(reasons: pd.DataFrame, ticker: str, date: str) -> dict | None:
    if reasons.empty:
        return None
    hit = reasons[(reasons["ticker"] == ticker) & (reasons["date"] == date)]
    if hit.empty:
        return None
    return hit.iloc[0].to_dict()


def audit_large_moves(
    close: pd.DataFrame,
    raw_dir: Path,
    threshold: float = 0.25,
    date_tolerance_days: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Return (gap_log, split_report, failure_messages).

    Unexplained |ret|>25% moves fail the build (no auto-explain).
    """
    flags = flag_large_moves(close, threshold=threshold)
    ysplits = yahoo_splits_from_raw(raw_dir)
    actions = load_corporate_actions()
    reasons = load_large_move_reasons()
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

    # 2) Large moves: require sourced reason; fail if missing / empty / bad category
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

        rec = _lookup_reason(reasons, row["ticker"], row["date"])
        explained = False
        reason = ""
        category = ""
        source = ""
        if rec is None:
            failures.append(
                f"{row['ticker']} {row['date']} ret={row['ret']:+.2%} unexplained "
                f"(no entry in config/large_move_reasons.yaml)"
            )
            reason = "UNEXPLAINED"
        else:
            category = str(rec.get("category") or "").strip()
            source = str(rec.get("source") or "").strip()
            reason = str(rec.get("reason") or "").strip()
            if category not in ALLOWED_REASON_CATEGORIES:
                failures.append(
                    f"{row['ticker']} {row['date']}: category '{category}' not in "
                    f"{sorted(ALLOWED_REASON_CATEGORIES)}"
                )
            elif not source or not source.startswith("http"):
                failures.append(
                    f"{row['ticker']} {row['date']}: missing/invalid source URL"
                )
            elif not reason:
                failures.append(f"{row['ticker']} {row['date']}: empty reason text")
            else:
                explained = True
                reason = f"{category}: {reason} [{source}]"

        if has_split:
            # must also be in corporate actions
            sub = actions[actions["ticker"] == row["ticker"]]
            in_ca = False
            for _, act in sub.iterrows():
                if abs((pd.Timestamp(row["date"]) - pd.Timestamp(act["date"])).days) <= date_tolerance_days:
                    in_ca = True
                    if explained:
                        reason = (
                            f"split+corporate_actions {act.get('type')} {act.get('ratio')}; "
                            + reason
                        )
                    break
            if not in_ca:
                explained = False
                failures.append(
                    f"{row['ticker']} {row['date']} ret={row['ret']:+.2%} coincides with "
                    f"Yahoo split but not listed in corporate_actions.yaml"
                )

        gap_rows.append(
            {
                **row.to_dict(),
                "kind": kind,
                "explained": explained,
                "category": category,
                "reason": reason,
                "source": source,
            }
        )

    return pd.DataFrame(gap_rows), pd.DataFrame(split_rows), failures


def sync_corporate_actions_from_yahoo(raw_dir: Path) -> int:
    """Append any Yahoo splits missing from corporate_actions.yaml. Returns count added."""
    path = reference_path("corporate_actions")
    data = yaml.safe_load(path.read_text())
    actions = data.get("actions") or []
    ysplits = yahoo_splits_from_raw(raw_dir)
    added = 0
    for _, sp in ysplits.iterrows() if len(ysplits) else []:
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
