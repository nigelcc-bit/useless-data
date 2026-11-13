# Study A: Does support exist?

## Question
Do closes around a 6-month swing low behave differently from what the index's
own return process produces with no memory of price levels?

## Motivation
A back-of-envelope reflection-principle check (driftless Gaussian walk, 1.5-2%
daily vol, discrete-monitoring correction, Study 1 medians) gives reclaim
rates of about 73-76% and retest rates of about 77-81%, against observed NDX
86% / 72% and SPX 78% / 79%. If the full null reproduces these, "retests are
the norm" is a property of volatility, not of support.

## Design
- Engine: Study 1 primary spec, unchanged (bear_trap/events.py, regression-tested).
- Sample: NDX 1985-09-26 to 2026-11-09, SPX 1950-01-03 to 2026-11-09 (Study 1 data).
- Null models (bear_trap/nulls.py), each fitted to the full-sample log returns:
  - **block (primary)**: stationary bootstrap, mean block 20 days. Keeps fat
    tails, vol clustering and short-range autocorrelation; destroys any
    dependence on price relative to a prior low.
  - gbm, iid, garch (GARCH(1,1)-t), msvol (2-state Markov-switching): secondary.
- 500 simulated paths per model, each the same length as the real series, seed 7.
- Statistic per path: reclaim rate (share of resolved breaks reclaimed within K),
  retest rate (share of reclaims with full 60-day data that close below the sweep low).

## Primary tests (4)
For each index and each of {reclaim rate, retest rate}: two-sided percentile
p-value of the observed rate within the block-null distribution of per-path
rates. Significance: p < 0.0125 (Bonferroni over 4).

## Hypotheses
- **H0**: observed rates lie within the block-null distribution (support adds nothing).
- **H1**: observed rates differ from the null. Directional expectation stated in
  advance: reclaim rate above null (mean reversion at lows); retest rate no different.

## Secondary (descriptive)
- Same comparison under gbm, iid, garch, msvol, and for breaks per year and the
  deep-sweep share.
- Pseudo-level DiD: run the same break/reclaim rule on trailing 5th, 10th and
  20th percentile levels (first downward crossing, no age rule). Paired per
  block path, compare (rate at min minus rate at quantile) observed vs null.
  If minima are special, the observed difference exceeds the null difference.

## Kill criteria
- If the NDX and SPX retest rates are inside the block null (p > 0.0125): retire
  "retests are the norm" as a market-structure claim. Stop-placement guidance
  should come from volatility (Study C hazard), not from the level.
- If the reclaim rate exceeds the null in both indices: support carries short-
  horizon mean reversion. That becomes the hypothesis to monetise in Tier 2,
  noting Study 1 found no forward-return edge.

## Known limitations
- The block bootstrap preserves within-block autocorrelation, so any short-range
  mean reversion in returns themselves is kept in the null. This is deliberate:
  the test isolates level-specific behaviour.
- One real path per index: the observed rate carries sampling noise of the same
  size as the per-path null spread, which the percentile test accounts for.
