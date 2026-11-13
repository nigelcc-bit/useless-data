# Study C: Survival analysis of retests and recoveries

## Question
Study 1 reports a static 72% (NDX) / 79% (SPX) retest rate within 60 days.
How does the retest probability decay as a reclaim survives day by day? Is that
decay different from the block-bootstrap null? And what does it imply for the
live Nov 2026 Nasdaq event?

## Design
- Spells start at the reclaim close. Two outcomes:
  - **retest**: first close below the sweep low;
  - **regain**: first close at or above the 120-day high at the break.
- Censoring at 120 trading days or at the data end.
- Fit sample: all Study 1 reclaimed events with breaks before 2026-11-01. The
  live event is excluded from fitting and used only for prediction.
- Kaplan-Meier per index. The conditional probability table is
  P(event by day 60 | none by day d) = 1 - S(60)/S(d) for d = 0, 5, 10, 20, 30, 40.
- Null: the same spells from 200 block-bootstrap paths (Study A primary null).

## Primary tests (2)
Log-rank test, observed vs null retest curve, per index. Significance:
p < 0.025 (Bonferroni over 2).

## Descriptive
- Log-rank for the regain curve.
- Cox proportional hazards, pooled across indices, stratified by index, SEs
  clustered by calendar year, ridge penalty 0.05. Covariates standardised:
  sweep depth below support, drawdown at break, and 20-day realised vol at
  break. Hazard ratios are descriptive: n is small and the covariates were
  chosen after Study 1 showed sweep depth mattered for retest rates.
- Live-event readout: KM and Cox conditional probabilities given the number of
  days the 9 Nov 2026 reclaim has survived without a retest.

## Kill criteria
- Retest curve not different from the null (p > 0.025): the decay is
  volatility-driven. Use the null hazard, which has far more events, for stop
  and sizing decisions.
- Proportional-hazards violation (check `cph.check_assumptions`): report KM only.

## Caveat on the live readout
The readout is a base rate conditioned on time survived. It is not a forecast
and must not be updated by eyeballing intraday moves. Re-run after each close.
