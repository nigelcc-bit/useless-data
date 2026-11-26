# MU regime read: regime change or flush?  (result)

Run 2026-11-25. Pre-registration: [`PREREG.md`](PREREG.md) (committed before any fit).

```
VERDICT: WEAK | confidence 60%
Claim: MU's selloff from the 2026-06-25 peak (-48%) is a regime change, not a flush
Method: 2-state Gaussian HMM on z(log return), z(rv21); expanding refits every 63 sessions,
        forward-filtered out of sample from 2013 (TB03 Ch15 HMM and Kalman filters | TB02 Ch9 HMMs)
Data: Yahoo adj closes MU/SOXX/SPY, 2010-01-04 to 2026-11-24, daily, run 2026-11-25 | Trials counted: 8
```

| Filtered P(stress) | Days in state | Median past duration | Smoothed vs filtered disagreement | Kalman beta now |
|---|---|---|---|---|
| **1.00** (>0.8 for 24 sessions) | **326** (since 2025-08-11) | 26 (90% CI 23 to 32), p75 46, n = 33 | **525 of 3,496 days (15%)** | **1.31 +/- 0.13** vs SOXX |

**Conclusion.** MU did change regime, but the change came in **August 2025, during the rally**, not at
the June 2026 peak. The primary model has had MU in its high-vol state for 326 sessions, the longest
spell since 2010 (the previous record was 242 sessions, Jun 2015 to Jun 2016). The selloff is happening
inside that state. Separating out the most extreme vol state (3-state model), MU has been in it for
only **18 sessions**, below the past p75 of 56. That length so far looks like a flush. Under the
pre-registered rule this is **WEAK**, because the answer flips with the feature set and the number of states.

**Would change if:** the 3-state top-vol spell runs past roughly **56 sessions** (about mid-February 2027)
with P > 0.8, which would make it regime-like in the stricter model too; or filtered P(stress) in P0
drops below 0.5 for more than 5 sessions, which would end the 2025 to 2026 vol regime.

**Rival explanation:** this is not a selloff regime but one long high-vol episode, an AI-memory boom
with its own reversal. The stress state's mean daily return is **+0.10%**, about the same as the calm
state's (+0.09%). The HMM measures volatility, not direction, so it cannot tell a boom from a bust.

**Next:** re-check the 3-state spell length weekly; add a direction feature (63-day return or drawdown)
as a pre-registered v2 if a directional answer is needed.

## Robustness (all counted)

| ID | Variant | P(stress) now | Sessions > 0.8 | Current spell | Past p75 | Reads as |
|---|---|---|---|---|---|---|
| P0 | 2-state, r + rv21 (primary) | 1.00 | 24 | **326** | 46 | regime (vol regime since Aug 2025) |
| R1 | 3-state, r + rv21 (top-vol state) | 1.00 | 18 | **18** | 56 | flush-sized so far |
| R2 | 2-state, returns only | 1.00 | **3** | 28 | 8 | fails the 10-session rule |
| R3 | 2-state, + SOXX rv21 | 1.00 | 24 | 292 | 63 | regime |
| R4 | 2-state, r + rv10 | 1.00 | 27 | 28 | 32 | flush-sized so far |

- **Random-start stability (P0):** 20 of 20 starts converged within 1% of the best log-likelihood; all give
  P(stress) now = 1.00. The state is stable, so the WEAK call comes from the feature set and state count, not from the starts.
- **3-state path (R1):** the top-vol state switched off in **September 2026** (month-end P = 0.004) and back
  on in late October, so the selloff leg is a new spell.
- Both states are well populated (34% / 66% occupancy), so neither is degenerate.

## Look-ahead gap (mandatory)

- The filtered and smoothed 0.5-calls differ on **525 of 3,496 days (15%)**.
- Toy rule (long MU when yesterday's P(stress) < 0.5, else cash), 2013 to 2026:
  - filtered: **Sharpe 0.66**, 18.0% per year (log), 48% time in market
  - smoothed: Sharpe 0.75, 23.6% per year (log): overstates by **~0.09 Sharpe and ~5.6 pp per year**
  - buy and hold: Sharpe 0.66, 33.3% per year (log)
- The filtered rule adds no risk-adjusted edge over buy and hold. This is a regime description, not a trade.

## Kalman beta (MU on SOXX daily log returns)

- Now **1.31 +/- 0.13** (2 sd); 63-day rolling OLS 1.23. It peaked at 1.49 on 2026-06-25.
- The 2010 to 2025 median is 1.38, so beta has fallen back toward normal and has **not** shifted
  regime. The selloff is not MU decoupling from semis on beta.

## Trial ledger (8)

P0, R1, R2, R3, R4 (five HMM specifications), the Kalman beta, and the filtered and smoothed toy backtests.
One earlier run of the identical spec crashed while writing JSON. It was rerun unchanged and its
numbers matched, so it is not counted as a separate trial.

## Caveats

- Prices: Yahoo adjusted closes. Returns matched the repo's stored MU series (2015 to 2026, 2,979 days,
  max abs daily return difference 1e-6), and Nov 17 to 23 closes matched Financial Datasets. MU's 2026
  price levels (peak about 1,213) are as the vendors report them; I did not check them against an
  exchange record.
- Selloff start date (2026-06-25) is judgment-coded after the fact; the model does not use it.
- "Stress" means **high volatility**, not falling prices.
- This is a point-in-time read as of 2026-11-24. The probabilities and spell lengths will change with new data.
- `outputs/regime_strip.png` was drawn before a title-text fix in `run.py`. The data in it is correct,
  but the title wording is awkward; rerunning `run.py` regenerates it with the corrected title.

## Files

- `run.py`: full pipeline (takes about 14 minutes; 20 starts per refit)
- `outputs/regime_strip.png`: price, filtered vs smoothed P(stress), Kalman beta, 2013 to 2026
- `outputs/regime_strip_2026.png`: 2026 zoom
- `outputs/results.json`, `trials.csv`, `stress_spells_P0.csv`, `recent_probs_2026.csv`, `kalman_beta.csv`
