#!/usr/bin/env python3
"""Build data/raw_manifest.csv: file, sha256, source URL, pull date.

Raw payloads stay on disk under data/raw/ (gitignored); only the manifest
is committed for reproducibility.

Also registers Study 1 clean splices when present under
studies/2026-11-testing-nasdaq-bear-trap/data/clean/
(ndx_1985_2026.csv, spx_1950_2026.csv).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd

from core.config_io import ROOT

RAW = ROOT / "data" / "raw"
BEAR_TRAP_CLEAN = (
    ROOT / "studies" / "2026-11-testing-nasdaq-bear-trap" / "data" / "clean"
)
OUT = ROOT / "data" / "raw_manifest.csv"

STUDY1_CLEAN_SOURCES = {
    "ndx_1985_2026.csv": (
        "Study 1 validated NDX splice (Investing.com + Yahoo mirror); "
        "see studies/2026-11-testing-nasdaq-bear-trap/docs/Study1_Bear_Trap_Full_Report.md"
    ),
    "spx_1950_2026.csv": (
        "Study 1 validated SPX splice (gt R package + Investing.com); "
        "see studies/2026-11-testing-nasdaq-bear-trap/docs/Study1_Bear_Trap_Full_Report.md"
    ),
}


def source_url(rel: str) -> str:
    name = Path(rel).name
    if name in STUDY1_CLEAN_SOURCES:
        return STUDY1_CLEAN_SOURCES[name]
    if name.startswith("yahoo_"):
        sym = name[len("yahoo_") : -len(".json")].replace("_", "^", 1) if name.startswith("yahoo__") else name[len("yahoo_") : -len(".json")]
        if name.startswith("yahoo__"):
            sym = "^" + name[len("yahoo__") : -len(".json")]
        return f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
    if name.startswith("sec_companyfacts_CIK"):
        cik = name[len("sec_companyfacts_") : -len(".json")]
        return f"https://data.sec.gov/api/xbrl/companyfacts/{cik}.json"
    if name == "sec_company_tickers.json":
        return "https://www.sec.gov/files/company_tickers.json"
    if name.startswith("finra_shrt"):
        ymd = name[len("finra_shrt") : -len(".csv")]
        return f"https://cdn.finra.org/equity/otcmarket/biweekly/shrt{ymd}.csv"
    if name.startswith("fred_"):
        series = name[len("fred_") : -len(".csv")]
        if series == "all":
            return "https://fred.stlouisfed.org/"
        return f"https://fred.stlouisfed.org/series/{series}"
    if "merger" in name:
        return "https://efts.sec.gov/LATEST/search-index"
    return "UNKNOWN"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _row(path: Path, pull_date: str = "") -> dict:
    rel = path.relative_to(ROOT).as_posix()
    return {
        "file": rel,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "source_url": source_url(rel),
        "pull_date": pull_date,
    }


def main() -> None:
    rows = []
    for path in sorted(RAW.rglob("*")):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        parent = path.parent.name
        pull_date = parent if re.fullmatch(r"\d{4}-\d{2}-\d{2}", parent) else ""
        rows.append(_row(path, pull_date))

    if BEAR_TRAP_CLEAN.is_dir():
        for name in STUDY1_CLEAN_SOURCES:
            path = BEAR_TRAP_CLEAN / name
            if path.is_file():
                # mtime date as pull_date until a dedicated stamp is recorded
                pull_date = pd.Timestamp(path.stat().st_mtime, unit="s").strftime("%Y-%m-%d")
                rows.append(_row(path, pull_date))

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Wrote {OUT} rows={len(df)}")


if __name__ == "__main__":
    main()
