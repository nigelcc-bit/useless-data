"""H3 — Crowding dominates valuation in the cross-section across episodes.

Regressor list (standardized, winsorised 2.5/97.5), episode FE, SE clustered
by GICS sub-industry; bootstrap by episode:

Crowding block
  1. Prior 63d return
  2. Distance from 252d high at episode start
  3. Trailing 21d realised vol
  4. Short interest as % of float

Valuation block  **(Pre-P1 revision b — D6)**
  5a. SPEC: forward P/S, forward P/E, EV/EBITDA from point-in-time consensus
      → none of our listed sources provide this. Defect D6.
  5b. FALLBACK (pre-registered deviation): trailing P/S, trailing P/E,
      EV/EBITDA lagged to *filing date*, not period-end.
      Labelled DEVIATION_FROM_SPEC in every output.
      Counted as a **separate** test in the FDR family (T005b).

Funding block
  6. Net debt / EBITDA, interest coverage, lease liabilities / assets

Layer / exposure
  7. AI revenue exposure (judgment 0–3; flag judgment in every output)
  8. **Layer dummy / layer FE** (Pre-P1 revision c — required by H4;
     was referenced there but never estimated). Builders = reference;
     dummies for compute_semis, memory_storage, semicap, optics_networking,
     power_cooling, neoclouds, non_ai_control. ORCL dual-code sensitivity.

Liquidity controls
  9. Log market cap and ADV
"""

STATUS = "NOT_RUN"
NULL = "Crowding proxies carry no incremental R² over valuation + fundamentals."
FAALSIFIER = "Valuation block incremental R² exceeds crowding in ≥ 4 of 7 episodes."

VALUATION_SPEC = "point_in_time_forward_multiples"
VALUATION_FALLBACK = "trailing_multiples_lagged_to_filing_date"
VALUATION_FALLBACK_LABEL = "DEVIATION_FROM_SPEC"
VALUATION_FALLBACK_DEFECT = "D6"
VALUATION_FALLBACK_TEST_ID = "T005b"

REGRESSORS = [
    "prior_63d_return",
    "dist_252d_high",
    "realised_vol_21d",
    "short_interest_pct_float",
    "trailing_ps_filing_lag",  # fallback; forward_ps when D6 cleared
    "trailing_pe_filing_lag",
    "ev_ebitda_filing_lag",
    "net_debt_ebitda",
    "interest_coverage",
    "lease_liab_assets",
    "ai_revenue_exposure_0_3_JUDGMENT",
    "layer_dummy_block",  # H4 dependency — estimated in H3
    "log_mkt_cap",
    "adv",
]
