"""H5 — Pre-open leadership statistic has forecasting power.

Trough rule (Pre-P1 revision a; replaces "local trough"):
  trough day τ = close at the lowest level of the prior 63 sessions,
  confirmed by the next close being higher.
  L(k) starts counting after the confirmation close
  (close[τ+1] → close[τ+1+k]).

Convention:
  - trough flag at τ uses closes up to τ+1 only
  - signal at asof uses closes up to asof−1 only (APAC / 5pm HKT)

Walk-forward from 2023; costs 15–40bp. Intraday variants are out of scope.
"""

STATUS = "NOT_RUN"
NULL = "L(5) and L(10) carry no information about subsequent 63d relative supplier performance."
FAALSIFIER = "OOS R² ≤ 0 or hit rate ≤ 50% → demote discriminating test to commentary."

TROUGH_RULE = "63d_low_confirmed_next_close_up"
L_WINDOW = "after_confirmation_close"
SIGNAL_CUTOFF = "asof_minus_1_close"
