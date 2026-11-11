"""Funding block (H3).

Net debt / EBITDA, interest coverage, lease liabilities / assets.
Source: SEC EDGAR companyfacts, lagged to filing date.

Pre-P4 revision (ASC 842): public-company adoption for fiscal years beginning
after 2015-12-15 (ASU 2016-02) / effectively after 2018-12-15 for public
business entities. E1 (2018-10-01) is structurally pre-adoption for nearly
all names — do **not** impute lease=0. Build E1 funding PC1 from
net_debt_ebitda + interest_coverage only when lease coverage is sparse.
"""

from __future__ import annotations

import pandas as pd

FUNDING_COLS = (
    "net_debt_ebitda",
    "interest_coverage",
    "lease_liab_assets",
)
FUNDING_COLS_E1_NO_LEASE = (
    "net_debt_ebitda",
    "interest_coverage",
)


def empty_funding(tickers: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {c: pd.Series(index=tickers, dtype="float64") for c in FUNDING_COLS}
    )


def funding_cols_for_episode(episode: str, lease_nonmissing: int, n_listed: int) -> tuple[str, ...]:
    """Drop lease from E1 PC1 when structurally absent (do not impute zero)."""
    if episode == "E1" and (n_listed == 0 or lease_nonmissing / max(n_listed, 1) < 0.25):
        return FUNDING_COLS_E1_NO_LEASE
    return FUNDING_COLS
