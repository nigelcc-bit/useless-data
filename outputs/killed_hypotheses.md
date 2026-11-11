# Killed hypotheses

Equal in status to the findings. A project that kills nothing has learned nothing.

| ID | Hypothesis | Killed by | Date | Note |
|---|---|---|---|---|
| K001 | Call 3 magnitude as published (−0.69 / −0.76 YTD Spearmans; supplier EW −12.9) | P1 Yahoo ingest + gap diagnosis | 2026-11-08 | **Call 3 magnitude revised** — label **UNRECONCILED** for YTD rho (note inputs unrecoverable; Yahoo Close≈Adj at −0.53, p=0.0093). Supplier/neocloud EW = **NOTE ERROR** (Yahoo+IBKR −13.91% neocloud vs note −10.6). Also SUPERSEDED: six-session supplier EW −26.5→−27.89; worst-7 adds IREN. Old targets retained under SUPERSEDED. |
| K002 | Call 5 (near-high first-shock flush vs regime) transfers to semis | P2 H1 classification | 2026-11-08 | Call 5 does not transfer to semis. On 5 Nov SOX was a cluster day 29.8% below its 252d high, not a near-high first shock. Settled by classification, no forward returns. Semis near-high (le5) first-shock cells N=1–7 → T002 `NOT_RUN_UNDERPOWERED`. SPX 5 Nov is a first shock under rule A only; rule B classifies it as a cluster day (2026-06-05 event). |
| K003 | Call 3 (crowding, not valuation) in multivariate H3 panel | P4 H3 primary | 2026-11-11 | **Call 3 (crowding, not valuation) not supported in multivariate panel; univariate crowding association (adj R² 0.37 E6, 0.23 E7) is absorbed by layer dummies.** Falsifier not triggered (val beats crowding 3/6 counted). Crowding incremental adj-R² ≤ 0 in 5/6 counted episodes; wild-bootstrap p 0.26–0.90 in E3–E7. Decision: **H3 UNSUPPORTED** — neither crowding nor valuation adds explanatory power within layers. |
| K004 | Builder-supplier spread is a mean-reverting factor (H2) | P5 H2 hetero-robust VR + forwards | 2026-11-12 | **Killed by:** hetero-robust VR non-reject at all q, Chow–Denning p=0.45; pooled de-clustered forward spread returns not significant (N=9). Seesaw is description, not signal. **PRIOR (not a finding):** 63d point estimate +3.5% net, 7/9 positive — logged under Priors; do not cite as evidence. |

## Abandoned tests

| ID | Why abandoned | Counted in FDR family? |
|---|---|---|
| T002 | Semis near-high first-shock cells underpowered (N=1–7); Call 5 does not transfer | Yes — retained as `NOT_RUN_UNDERPOWERED` |

## Priors (N < 8 — not tested)

Record H1 cells that fail the N≥8 floor here. Print the full episode list in `outputs/exhibits/h1_small_cell_event_lists.csv`.

H1b (EXPLORATORY, T002b) deep-DD cluster counts: see `outputs/exhibits/h1b_deep_dd_counts.csv` and event lists. Same N≥8 floor; no forward returns until registered and powered.

| ID | Claim | Why PRIOR | Date | Note |
|---|---|---|---|---|
| P-H2-63d | H2 de-clustered −2.5σ events: +63d mean_net ≈ +3.5%, hit 7/9 | Underpowered / non-significant (N=9; NW p=0.31) | 2026-11-12 | Point estimate only. K004 kills the factor claim; do not promote 63d rebound to a finding. |
| P-H5 | H5 L(5)/L(10) forecasts 63d relative supplier performance | OOS N with complete L(10) = 4 &lt; 8 | 2026-11-12 | **PRIOR ONLY — do not test.** Troughs=15 (train 10 / OOS 5) on cum supplier−builder spread from 2023. Monitor still ships. |
