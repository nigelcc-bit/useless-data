# MU regime read: regime change or flush?  (pre-registration)

Frozen 2026-11-25, before any model was fit. Price data was inspected only to
date the selloff.

## Question

MU closed at a record **1213.18** (adj.) on 2026-06-25 and at **629.79** on
2026-11-24 (**-48%**). Is the selloff a **regime change** (MU has moved into a
persistent stress state) or a **flush** (a stress spell of normal length that
fits MU's own history)?

Selloff start date (2026-06-25 peak) is `JUDGMENT_CODED_POST_OUTCOME`; it is
used only for description, not for the model.

## Data

Yahoo chart API adjusted closes, MU, SOXX, SPY, daily. 2009 used only to warm
up rolling and expanding statistics; the model sample starts 2010-01-04.
Cross-checked against repo `data/processed/adj_close.parquet` (2015+) and
Financial Datasets closes (spot check Nov 2026).

## Model (primary, P0)

- Features: daily log return r_t and 21-day realised vol rv21_t (annualised).
  Each standardised by **expanding-window** mean and std using data up to t.
- 2-state Gaussian HMM (hmmlearn, full covariance), EM with **20 random
  starts**, keep best log-likelihood. Degenerate check: each state must hold
  >= 5% of days.
- Label rule: the state with higher mean rv21 = **stress**.
- **Filtered** P(stress_t | data to t): refit on an expanding window every 63
  sessions from 2013-01-02 (3 years of training), forward-filter with the
  latest parameters until the next refit. Out-of-sample from 2013.
- Smoothed P(stress): one full-sample fit, forward-backward. Reported only
  for the look-ahead gap.

## Verdict rule (claim = "this is a regime change")

- **HOLDS**: filtered P(stress) > 0.8 for >= 10 consecutive sessions ending
  on the last date, stable across random starts (current P(stress) on the
  same side of 0.5 for >= 80% of starts that converge within 1% of best LL),
  **and** the current stress spell is longer than the 75th percentile of past
  stress spells (persistence beyond a normal flush).
- **WEAK**: P between 0.5 and 0.8, or the call flips with start or feature
  set, or P > 0.8 but the spell is within the normal duration range.
- **KILLED**: filtered P(stress) is below 0.5 now; only smoothed crosses it.
- **INCONCLUSIVE**: fewer than 3 past stress spells in sample.

Spell = run of filtered P(stress) > 0.5, gaps of <= 5 sessions merged.

## Mandatory checks

1. Look-ahead gap: days where filtered and smoothed 0.5-calls differ; and a
   toy rule (long MU when P(stress)_{t-1} < 0.5, else cash) run on filtered
   vs smoothed to show how much smoothing overstates.
2. Kalman beta of MU on SOXX: beta_t random walk, delta = 1e-4,
   observation noise from 2010-2012 OLS residual variance; band = +/- 2 sd.
   Compared with 63-day rolling OLS.
3. Durations: past stress spell lengths, median with bootstrap 90% CI.

## Robustness (each counted as a trial)

- R1: 3 states (stress = highest-vol state)
- R2: returns only (no rv21)
- R3: add SOXX rv21 as a third feature
- R4: rv10 instead of rv21

Note: "stress" here is a **volatility** state. It is not directional; MU's
2026 rally was also high-vol. Mean return in each state is reported.
