"""Valuation block (H3).

SPEC: point-in-time forward multiples — unavailable (D6).
PRE-P4 revision: use **yields** (E/P, S/P, EBITDA/EV) lagged to filing date
so loss-makers stay in the cross-section (negative E/P is valid).
Still labelled DEVIATION_FROM_SPEC / T005b (trailing, not forward PIT).
"""

from __future__ import annotations

import pandas as pd

VALUATION_COLS = (
    "earnings_yield_ep_filing_lag",  # E/P
    "sales_yield_sp_filing_lag",  # S/P
    "ebitda_ev_yield_filing_lag",  # EBITDA/EV
)
# Legacy multiple column names (kept for migration notes only)
VALUATION_COLS_LEGACY_MULTIPLES = (
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


def trailing_yields(price: float, shares: float | None, fund: dict) -> dict:
    """Filing-lagged trailing yields. Loss-makers keep finite E/P (<0)."""
    import numpy as np

    out = {c: float("nan") for c in VALUATION_COLS}
    if shares in (None, 0) or not np.isfinite(price) or price <= 0:
        return out
    mcap = price * float(shares)
    rev = fund.get("revenue")
    ni = fund.get("net_income")
    ebitda = fund.get("ebitda")
    net_debt = fund.get("net_debt")
    if rev not in (None, 0) and np.isfinite(float(rev)):
        out["sales_yield_sp_filing_lag"] = float(rev) / mcap
    if ni is not None and np.isfinite(float(ni)):
        # include losses (negative yield) — Pre-P4 revision a
        out["earnings_yield_ep_filing_lag"] = float(ni) / mcap
    if ebitda not in (None, 0) and np.isfinite(float(ebitda)):
        ev = mcap + (float(net_debt) if net_debt is not None else 0.0)
        if ev != 0 and np.isfinite(ev):
            out["ebitda_ev_yield_filing_lag"] = float(ebitda) / ev
    return out
