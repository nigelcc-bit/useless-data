"""Valuation block (H3).

SPEC: point-in-time forward P/S, P/E, EV/EBITDA — unavailable (D6).
FALLBACK: trailing multiples lagged to filing date (DEVIATION_FROM_SPEC, T005b).

No fundamentals loaded in P3 coverage phase → columns present, all NaN.
"""

from __future__ import annotations

import pandas as pd

VALUATION_COLS = (
    "trailing_ps_filing_lag",
    "trailing_pe_filing_lag",
    "ev_ebitda_filing_lag",
)
VALUATION_LABEL = "DEVIATION_FROM_SPEC"
VALUATION_DEFECT = "D6"


def empty_valuation(tickers: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {c: pd.Series(index=tickers, dtype="float64") for c in VALUATION_COLS}
    )
