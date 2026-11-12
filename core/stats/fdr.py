"""Benjamini-Hochberg FDR control across the full test family."""

from __future__ import annotations

import pandas as pd


def benjamini_hochberg(p_values: pd.Series, q: float = 0.10) -> pd.DataFrame:
    """Return raw and BH-adjusted p-values with reject flags at level q."""
    s = p_values.dropna().astype(float).sort_values()
    m = len(s)
    if m == 0:
        return pd.DataFrame(columns=["raw_p", "bh_p", "reject_q"])
    ranks = pd.Series(range(1, m + 1), index=s.index)
    bh = (s * m / ranks).iloc[::-1].cummin().iloc[::-1].clip(upper=1.0)
    out = pd.DataFrame({"raw_p": s, "bh_p": bh})
    out["reject_q"] = out["bh_p"] <= q
    return out.reindex(p_values.index)
