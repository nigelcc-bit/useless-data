"""Funding block (H3 regressor 6).

Net debt / EBITDA, interest coverage, lease liabilities / assets.
Source of truth: SEC EDGAR / XBRL (spec §6). Not ingested in P3 coverage → NaN.
"""

from __future__ import annotations

import pandas as pd

FUNDING_COLS = (
    "net_debt_ebitda",
    "interest_coverage",
    "lease_liab_assets",
)


def empty_funding(tickers: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {c: pd.Series(index=tickers, dtype="float64") for c in FUNDING_COLS}
    )
