#!/usr/bin/env python3
"""Build data/raw_manifest.csv: file, sha256, source URL, pull date.

Raw payloads stay on disk under data/raw/ (gitignored); only the manifest
is committed for reproducibility.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd

from src.config_io import ROOT

RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "raw_manifest.csv"


def source_url(rel: str) -> str:
    name = Path(rel).name
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


def main() -> None:
    rows = []
    for path in sorted(RAW.rglob("*")):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        rel = path.relative_to(ROOT).as_posix()
        # pull date = parent folder name if YYYY-MM-DD
        parent = path.parent.name
        pull_date = parent if re.fullmatch(r"\d{4}-\d{2}-\d{2}", parent) else ""
        rows.append(
            {
                "file": rel,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "source_url": source_url(rel),
                "pull_date": pull_date,
            }
        )
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Wrote {OUT} rows={len(df)}")


if __name__ == "__main__":
    main()
