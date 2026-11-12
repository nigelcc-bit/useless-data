"""FINRA equity short interest (bi-monthly CDN files).

Attempt history back through 2018. If coverage fails that bar → caller drops SI
and logs DEVIATION_FROM_SPEC (crowding = mom/dist/vol only).
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

from core.config_io import ROOT, episodes, universe, study_outputs

CDN = "https://cdn.finra.org/equity/otcmarket/biweekly/shrt{yyyymmdd}.csv"
MIN_INTERVAL_S = 0.15
# Settlement-date candidates around mid/month-end (CDN 404s skipped)
def _candidate_dates(start: str, end: str) -> list[pd.Timestamp]:
    idx = pd.date_range(start, end, freq="B")
    out = []
    for d in idx:
        if d.day in (13, 14, 15, 16) or d.is_month_end or d.day >= 27:
            out.append(pd.Timestamp(d).normalize())
    return sorted(set(out))


def universe_tickers() -> list[str]:
    out = []
    for _layer, meta in (universe().get("layers") or {}).items():
        out.extend((meta.get("names") or {}).keys())
    return sorted(set(out))


def fetch_settlement_file(
    settle: pd.Timestamp,
    raw_dir: Path,
    session: requests.Session,
    last: list[float],
) -> pd.DataFrame | None:
    ymd = settle.strftime("%Y%m%d")
    cache = raw_dir / f"finra_shrt{ymd}.csv"
    def _load_or_none(p: Path) -> pd.DataFrame | None:
        if not p.exists() or p.stat().st_size < 50:
            return None
        df = _read_finra_csv(p)
        if df is None or df.empty or len(df.columns) < 2:
            return None
        return df

    cached = _load_or_none(cache)
    if cached is not None:
        return cached
    # stale/corrupt cache → refetch
    if cache.exists() and cache.stat().st_size >= 50:
        cache.unlink()

    elapsed = time.monotonic() - last[0]
    if elapsed < MIN_INTERVAL_S:
        time.sleep(MIN_INTERVAL_S - elapsed)
    url = CDN.format(yyyymmdd=ymd)
    try:
        r = session.get(url, timeout=60)
        last[0] = time.monotonic()
    except requests.RequestException:
        last[0] = time.monotonic()
        return None
    if r.status_code != 200 or len(r.content) < 50:
        cache.write_bytes(b"")  # negative cache
        return None
    # Write full download temporarily, then slim to universe tickers for git size.
    cache.write_bytes(r.content)
    df = _load_or_none(cache)
    if df is None:
        return None
    tickers = set(universe_tickers())
    cols = {c.lower(): c for c in df.columns}
    sym = (
        cols.get("issuesymbolidentifier")
        or cols.get("symbolcode")
        or cols.get("symbol")
    )
    if sym:
        slim = df.loc[df[sym].astype(str).str.upper().isin(tickers)].copy()
        slim.to_csv(cache, sep="|", index=False)
        return slim if not slim.empty else df.iloc[0:0]
    return df


def _read_finra_csv(path: Path) -> pd.DataFrame:
    """FINRA biweekly files are pipe-delimited (historical) or comma (rare)."""
    kwargs = dict(engine="python", on_bad_lines="skip", dtype=str)
    try:
        df = pd.read_csv(path, sep="|", **kwargs)
        if len(df.columns) == 1:
            df = pd.read_csv(path, **kwargs)
        return df
    except Exception:
        try:
            return pd.read_csv(path, **kwargs)
        except Exception:
            return pd.DataFrame()


def ingest_finra(
    raw_dir: Path | None = None,
    start: str = "2018-01-01",
    end: str = "2026-11-05",
) -> tuple[pd.DataFrame, dict]:
    """Download FINRA SI files; return long panel + coverage diagnostics."""
    raw_dir = raw_dir or (ROOT / "data" / "raw" / "2026-11-08")
    raw_dir.mkdir(parents=True, exist_ok=True)
    sess = requests.Session()
    last = [0.0]
    tickers = set(universe_tickers())
    frames = []
    ok_dates = []
    fail_dates = []
    months = pd.period_range(start, end, freq="M")
    # Mid-month + month-end per month; nudge back over weekends/holidays
    probes_slim: list[pd.Timestamp] = []
    for m in months:
        mid = pd.Timestamp(year=m.year, month=m.month, day=15)
        month_end = pd.Timestamp(m.end_time).normalize()
        for base in (mid, month_end):
            for back in range(0, 5):
                probes_slim.append((base - pd.Timedelta(days=back)).normalize())
    seen: set[pd.Timestamp] = set()
    probes_ordered: list[pd.Timestamp] = []
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
    for d in probes_slim:
        if d not in seen and start_ts <= d <= end_ts:
            seen.add(d)
            probes_ordered.append(d)

    print(f"FINRA: probing up to {len(probes_ordered)} settlement-date candidates…")
    for d in probes_ordered:
        df = fetch_settlement_file(d, raw_dir, sess, last)
        if df is None or df.empty:
            fail_dates.append(d.strftime("%Y-%m-%d"))
            continue
        cols = {c.lower(): c for c in df.columns}
        sym_col = (
            cols.get("issuesymbolidentifier")
            or cols.get("symbolcode")
            or cols.get("symbol")
        )
        short_col = (
            cols.get("currentshortsharenumber")
            or cols.get("currentshortpositionquantity")
            or cols.get("shortinterest")
        )
        date_col = cols.get("settlementdate")
        if not sym_col or not short_col:
            fail_dates.append(d.strftime("%Y-%m-%d"))
            continue
        sub = df[[sym_col, short_col]].copy()
        if date_col:
            sub["settlement_date"] = pd.to_datetime(df[date_col])
        else:
            sub["settlement_date"] = d
        sub = sub.rename(columns={sym_col: "ticker", short_col: "short_shares"})
        sub["ticker"] = sub["ticker"].astype(str).str.upper()
        sub["short_shares"] = pd.to_numeric(sub["short_shares"], errors="coerce")
        sub = sub.loc[sub["ticker"].isin(tickers) & sub["short_shares"].notna()]
        ok_dates.append(d.strftime("%Y-%m-%d"))
        if not sub.empty:
            frames.append(sub)
            print(f"  FINRA {d.date()} hits={len(sub)}", flush=True)

    if not frames:
        panel = pd.DataFrame(columns=["ticker", "settlement_date", "short_shares"])
    else:
        panel = pd.concat(frames, ignore_index=True)
        panel = panel.drop_duplicates(["ticker", "settlement_date"], keep="last")

    first_ok = min(ok_dates) if ok_dates else None
    # Need coverage for earliest H3 episode start (E1 = 2018-10-01)
    e1_start = pd.Timestamp(episodes()["episodes"]["E1"]["window"][0])
    covers_2018 = bool(first_ok and pd.Timestamp(first_ok) <= e1_start)

    diag = {
        "n_files_ok": len(ok_dates),
        "n_files_fail_or_empty": len(fail_dates),
        "first_settlement": first_ok,
        "last_settlement": max(ok_dates) if ok_dates else None,
        "covers_e1_2018": covers_2018,
        "n_rows": len(panel),
        "n_tickers": int(panel["ticker"].nunique()) if len(panel) else 0,
    }
    exhibits = study_outputs() / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)
    panel.to_csv(exhibits / "finra_short_interest_panel.csv", index=False)
    pd.Series(diag).to_json(exhibits / "finra_si_diagnostics.json")
    print("FINRA diagnostics:", diag)
    return panel, diag


def si_pct_asof(
    panel: pd.DataFrame,
    shares_outstanding: float | None,
    ticker: str,
    asof: pd.Timestamp,
) -> float:
    """Short shares / shares outstanding at latest settlement ≤ asof."""
    if panel.empty or shares_outstanding in (None, 0):
        return float("nan")
    sub = panel.loc[
        (panel["ticker"] == ticker) & (panel["settlement_date"] <= pd.Timestamp(asof))
    ]
    if sub.empty:
        return float("nan")
    short = float(sub.sort_values("settlement_date").iloc[-1]["short_shares"])
    return short / float(shares_outstanding)


if __name__ == "__main__":
    ingest_finra()
