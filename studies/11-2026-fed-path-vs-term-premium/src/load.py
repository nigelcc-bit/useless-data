"""Loaders only. No transformation beyond typing and the KW identity."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CONFIG = ROOT / "config"


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fixtures() -> dict:
    with open(CONFIG / "fixtures.yaml") as f:
        return yaml.safe_load(f)


def _daily(name: str) -> pd.DataFrame:
    df = pd.read_csv(RAW / name, dtype=str, keep_default_na=False)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df = df.set_index("date")
    return df.apply(lambda s: pd.to_numeric(s.replace({"": None, ".": None}), errors="raise")).astype(float)


def fred() -> pd.DataFrame:
    """FRED merged daily file, date-indexed, float, NaN where not published."""
    return _daily("fred_daily.csv")


def acm() -> pd.DataFrame:
    """NY Fed ACM daily: ACMYnn, ACMTPnn, ACMRNYnn (n = 01..10)."""
    return _daily("acm_daily.csv")


def kim_wright() -> pd.DataFrame:
    """Kim-Wright 2y and 10y: yield, term premium, risk-neutral yield (= yield - TP)."""
    f = fred()
    out = pd.DataFrame(index=f.index)
    for n in (2, 10):
        out[f"KWY{n}"] = f[f"THREEFY{n}"]
        out[f"KWTP{n}"] = f[f"THREEFYTP{n}"]
        out[f"KWRNY{n}"] = f[f"THREEFY{n}"] - f[f"THREEFYTP{n}"]
    return out


def target_changes() -> pd.DataFrame:
    """Target (DFEDTAR to 2008-12-15, then DFEDTARU upper bound) on change dates only."""
    df = pd.read_csv(RAW / "fred_target_changes.csv", dtype={"series": str, "value": float})
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    return df


def fomc_dates() -> pd.DataFrame:
    df = pd.read_csv(RAW / "fomc_dates.csv", dtype=str, keep_default_na=False)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    return df


def fomc_announcement_days(start: str = "1994-02-04") -> pd.DatetimeIndex:
    """Scheduled meetings only (second day of two-day meetings), from `start`."""
    d = fomc_dates()
    d = d[(d["kind"] == "meeting") & (d["flag"] == "scheduled") & (d["date"] >= pd.Timestamp(start))]
    return pd.DatetimeIndex(d["date"].sort_values().unique(), name="date")


def first_hikes(start: str = "1990-01-01", gap_days: int = 365, lookback_days: int = 3) -> list[pd.Timestamp]:
    """First target increase after >= `gap_days` with no increase, dated to the FOMC
    meeting or call on, or within `lookback_days` before, the FRED effective date."""
    tc = target_changes().sort_values("date").reset_index(drop=True)
    up = tc[tc["value"].diff() > 0]["date"].reset_index(drop=True)
    gaps = up.diff().dt.days
    eff = up[(gaps >= gap_days) & (up >= pd.Timestamp(start))]
    fd = fomc_dates()
    events = fd[fd["kind"].isin(["meeting", "call"]) & ~fd["flag"].isin(["cancelled", "excluded"])]["date"]
    out = []
    for e in eff:
        cand = events[(events <= e) & (events >= e - pd.Timedelta(days=lookback_days))]
        if cand.empty:
            raise ValueError(f"no FOMC meeting or call within {lookback_days} days before {e.date()}")
        out.append(cand.max())
    return out
