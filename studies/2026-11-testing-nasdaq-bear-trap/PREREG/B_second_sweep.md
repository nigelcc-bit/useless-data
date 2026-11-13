# Study B: Is the second sweep the real signal?

## Question
Study 1 found that in both chart episodes (Mar 2025, Mar 2026) the first
mechanical reclaim failed and the durable low came on a second, deeper sweep.
Does entering on a second-sweep pattern beat buying any comparable dip?

## Definitions (fixed before running)
Starting from each Study 1 primary-spec reclaimed event (support L, first
reclaim r1, sweep low S1):

- **B1 second reclaim**: the first close below S1 within 60 days of r1 (day u),
  then the first close above L within **20** trading days of u. Entry = that close.
- **B2 held retest (higher low)**: the first close below L within 60 days of r1
  (day p), occurring before any close below S1; then the first close above L
  within K = 10 days of p, with min(C[p..entry]) > S1. Entry = that close.

Hindsight note: the 20-day B1 window was chosen knowing the Apr 2025 second
reclaim took about 15 trading days from the retest. It is a round, one-month
choice, but it was not blind. A sensitivity run at 10 and 40 days is
descriptive only.

## Primary tests (12)
For B1 and B2, each index, horizons 20/60/120: placebo p-value (Study 1
method: 5,000 draws from the drawdown-matched pool, seed 7) for the mean
forward return from entry. Significance: p < 0.0042 (Bonferroni over 12).
Benjamini-Hochberg at q = 0.05 also reported.

## Reported with each test
n, number of distinct calendar years (clusters), mean, 95% CI from a cluster
bootstrap by calendar year of the original break, hit rate, drawdown-pool mean,
first-reclaim mean.

## Hypotheses
- **H0**: second-sweep entries earn the same as drawdown-matched days.
- **H1** (one-sided, stated in advance): second-sweep entries earn more.

## Kill criteria
- No test passes Bonferroni and the 120-day cluster CI includes the pool mean
  in both indices: "wait for the second sweep" has no return edge either. Its
  only remaining value would be risk (a smaller worst-60 after entry), which is
  reported but not tested here.
- If B1 or B2 passes in one index only: treat as a hypothesis for the Study D
  panel, not a finding.

## Expected sample sizes
Small. On the 2019-2026 NDX slice, B1 = 8 and B2 = 3 events. Full-sample n
will likely be about 15-30 per definition per index. Report Wilson intervals
on hit rates.
