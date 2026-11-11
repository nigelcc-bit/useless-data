"""H2 — Builder-supplier spread is a mean-reverting factor, not beta.

Conditioning variable (Pre-P1 revision d):
  Credit regime = above/below 126d median of the regime series.
  - 2023-01-01 → day before CRWV CDS history starts: **HY OAS only**
    (FRED BAMLH0A0HYM2). CRWV CDS has no history before its 2025 IPO.
  - From CRWV CDS availability onward: prefer CRWV CDS; still archive HY OAS
    as a parallel series for sensitivity.

Do not splice CRWV CDS into 2023–2024.
"""

STATUS = "NOT_RUN"
NULL = "After beta control, supplier-minus-builder spread is a random walk."
FAALSIFIER = "Variance ratio ≈ 1 and no significant forward spread return."

REGIME_PRIMARY_PRE_CRWV = "BAMLH0A0HYM2"  # FRED HY OAS
REGIME_PRIMARY_POST_CRWV = "CRWV_CDS"
REGIME_PRE_CRWV_END = "CRWV_CDS_HISTORY_START"  # fill at P1 from data
