# Study D: Cross-market panel

## Question
Does Study 1's null result, and the roughly 60/40 analog split, hold on a panel
of broad equity indices with many more episodes, once inference respects the
fact that crashes are global?

## Universe (fixed before running)
**Primary**: SPX, NDX, RUT, DAX, CAC, FTSE, STOXX50, N225, HSI, KOSPI, ASX200,
TSX. Requires at least 15 years of data (src/data.py PANEL_PRIMARY). DJI is
excluded as a near-duplicate of SPX.

**Secondary (descriptive only)**: DJI, 9 SPDR sector ETFs, gold futures, BTC.

## Data
- Yahoo Finance via yfinance, price index closes, cached in data/raw/.
- NDX and SPX use the Study 1 clean files when present.
- Every series is passed through `validate()`: daily moves over 15%, gaps, flat
  runs and duplicates are reported. Any market with unexplained flags is
  reported and excluded before results are viewed; the reason is logged here
  as a DEVIATION.

## Design
- Study 1 primary spec on each market.
- Excess return = event forward return minus that market's drawdown-matched mean.
- Clusters: calendar month of the break (primary), calendar quarter (sensitivity).

## Primary tests (2)
Pooled mean excess return at 60 and 120 days:
- p-value from a stratified placebo, where each market's events are matched by
  draws from its own pool;
- 95% CI from a cluster bootstrap by month.

Significance: p < 0.025 **and** a cluster CI that excludes 0.

## Descriptive
- Pooled reclaim and retest rates with month-cluster CIs. These should land in
  the Study 1 range of 60-86% and 55-80% if the Study 1 result generalises.
- Analog cell (reclaimed while 10-20% below the 120-day high): P(regain high),
  P(20% drawdown), P(retest), each with Wilson and cluster CIs. The quantity of
  interest is the effective number of clusters, not the event count.
- Per-market table and forest plot.

## Kill criteria
- If the pooled excess is not significant: the "no edge" result is general,
  not a Nasdaq/S&P quirk.
- If the pooled analog P(regain high) sits below 50% with a cluster CI below
  59%: the NDX 59% figure was a small-sample high draw, and the "modest lean to
  recovery" read in Study 1 section 9.2 should be withdrawn.

## Known limitations
- Yahoo index histories for some markets start late or contain bad prints;
  `validate()` output is part of the results.
- Price indices only. Dividend yields differ across markets, but excess returns
  are within-market, so the comparison stays fair.
- Global co-movement means even month clusters understate dependence in long
  bear markets. The quarter sensitivity is there to show how much this matters.
