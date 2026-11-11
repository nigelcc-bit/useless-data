"""H4 — Driver rotated between October and November 2026.

Uses the full H3 coefficient vector, **including the layer dummy block**
(Pre-P1 revision c). H3 must estimate layer dummies; H4 tests whether
those loadings (and the funding block) differ between E6 and E7 via SUR/Wald.

Do not pool E6 and E7 until this test adjudicates stability.
"""

STATUS = "NOT_RUN"
NULL = "H3 coefficient vector is stable across Oct 2026 and Nov 2026 episodes."
FAALSIFIER = "Wald test fails to reject at 5% → treat as one regime."

REQUIRES_FROM_H3 = ["layer_dummy_block", "funding_block", "crowding_block"]
