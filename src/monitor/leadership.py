"""H5 leadership statistic — closes only, available before next US open.

L(k) = [cum EW supplier − cum EW builder] over k sessions after a local trough,
divided by the trailing supplier/builder beta ratio.

Implementability gate: computable from previous US close; executable as a
single pre-order before 5pm HKT. No intraday inputs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HKT = ZoneInfo("Asia/Hong_Kong")


def _beta_ratio(suppliers: pd.Series, builders: pd.Series, window: int = 63) -> float:
    s = suppliers.pct_change().dropna()
    b = builders.pct_change().dropna()
    aligned = pd.concat([s, b], axis=1).dropna().iloc[-window:]
    if len(aligned) < max(20, window // 2):
        return np.nan
    cov = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
    var_b = cov[1, 1]
    if var_b <= 0:
        return np.nan
    beta_s = cov[0, 1] / var_b
    beta_b = 1.0
    if abs(beta_b) < 1e-8:
        return np.nan
    return float(beta_s / beta_b)


def leadership_stat(
    suppliers: pd.Series,
    builders: pd.Series,
    k: int = 5,
    asof: pd.Timestamp | None = None,
    beta_window: int = 63,
) -> float:
    """Compute L(k) using closes through asof−1 when asof is provided.

    When asof is None, uses the full series end (monitoring mode on last close).
    """
    if asof is not None:
        # Hard APAC constraint: signal at date t uses closes up to t−1 only.
        cutoff = asof - pd.tseries.offsets.BDay(1)
        suppliers = suppliers.loc[:cutoff]
        builders = builders.loc[:cutoff]

    if len(suppliers) < k + 2 or len(builders) < k + 2:
        return float("nan")

    s_cum = suppliers.iloc[-1] / suppliers.iloc[-1 - k] - 1.0
    b_cum = builders.iloc[-1] / builders.iloc[-1 - k] - 1.0
    spread = s_cum - b_cum
    br = _beta_ratio(suppliers, builders, window=beta_window)
    if br is None or not np.isfinite(br) or br == 0:
        return float("nan")
    return float(spread / br)


def interpret(L5: float, L10: float) -> str:
    """Desk-facing readout. Judgment commentary, not a trade ticket."""
    if not np.isfinite(L5):
        return "INSUFFICIENT_DATA"
    if L5 > 0 and L10 > 0:
        return "FLUSH_BIAS — suppliers leading builders on rebound window"
    if L5 < 0 and L10 < 0:
        return "THESIS_BIAS — builders leading; profit-pool rotation risk"
    return "MIXED — wait for next rebound cluster"


def main() -> None:
    # Placeholder series until prices.parquet is built (P1).
    # Prints the contract the desk will read before 5pm HKT.
    now_hkt = datetime.now(tz=timezone.utc).astimezone(HKT)
    print(f"asof_hkt={now_hkt.strftime('%Y-%m-%d %H:%M %Z')}")
    print("status=WAITING_FOR_prices.parquet")
    print("L5=nan L10=nan readout=INSUFFICIENT_DATA")
    print("rule=computable from prior US close only; no intraday")


if __name__ == "__main__":
    main()
