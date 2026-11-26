# Thanksgiving week and drawdown at entry (pre-registration)

Frozen **2026-11-26 (Thanksgiving Day, US markets closed), before the
2026-11-27 session**, and before any data was downloaded or computed.

## Question

Do the seasonal claims about Thanksgiving week hold, and does starting the
week in a correction change the outlook?

## Data

- Primary: Yahoo `^GSPC` daily closes, 1950-01-03 to 2026-11-25.
- Secondary: Yahoo `^NDX` daily closes, 1985 onward (first available day) to
  2026-11-25.
- Index closes (price only, no dividends).

## Definitions

- **Thanksgiving** = 4th Thursday of November (markets closed).
- **Black Friday (BF)** = first trading day after Thanksgiving.
- **Wednesday-before (WB)** = last trading day before Thanksgiving.
- **Friday before (F0)** = last trading day on or before the Friday 6 days
  before Thanksgiving.
- **Thanksgiving week return** = close(BF) / close(F0) - 1. Normally 4
  trading days (Mon, Tue, Wed, Fri).
- **Monday after (MA)** = first trading day after BF.
- **Drawdown at entry** = close(F0) / max(close over the 252 trading days
  ending at F0) - 1. "In a correction" = drawdown between **-20% and -10%
  inclusive**.
- **Year-end outcome** = close on the last trading day of December >
  close(BF).
- Daily return = close-to-close simple return.

## Sample

- Test years: **1950-2025** for ^GSPC (76 Thanksgiving weeks), **first full
  year with 252 prior sessions to 2025** for ^NDX. **2026 is never used in a
  test.**
- Halves: **1950-1987 vs 1988-2025** (^GSPC). ^NDX halves: first half of its
  years vs second half (split at the median year).
- Randomness: numpy seed **7**, **10,000** resamples per empirical p.

## Tests (every one goes in outputs/trials.csv)

### C1 seasonal (claim: Thanksgiving week, WB and BF are unusually positive)

- **C1-week**: hit rate (share of years up), median and mean of the week
  return, vs all other rolling 4-trading-day windows in the same years
  (excluding windows that overlap F0 to BF). Null: draw one random other
  window per year, 10,000 times; recompute each statistic. Two-sided
  empirical p = 2 x min(share of draws >= observed, share <= observed),
  capped at 1. **Primary for the C1 verdict: week hit rate.**
- **C1-WB** and **C1-BF**: the same three statistics for the single day vs
  all other trading days in the same years (one random other day per year
  per draw).
- 9 p-values.

### C2 decay (claim: the Thanksgiving-week edge has faded)

- Week hit rate 1950-1987 vs 1988-2025: Fisher exact, two-sided.
  **Primary.**
- Week median, first vs second half: Mann-Whitney U, two-sided.
- Rolling 20-year hit rate (chart, descriptive).
- 2 p-values.

### C3 drawdown conditioning (claim: starting the week in a 10-20% correction changes the year-end outcome)

- Year-end hit rate in years with drawdown at entry in [-20%, -10%] vs all
  other years. Report n, hits, Beta(1,1) posterior mean, **90% credible
  interval** (5th to 95th percentile of Beta(1 + hits, 1 + misses)), Fisher
  exact two-sided p. **Primary.**
- **CONTROL**: every Friday (last trading day of each week, Oct-Dec,
  1950-2025) with drawdown in [-20%, -10%] vs all other Oct-Dec Fridays.
  Outcome = last-trading-day-of-December close > close 4 trading days after
  that Friday (mirrors F0 -> BF); Fridays whose +4 day is not before the last
  trading day are dropped. Same statistics. Fridays overlap within a year, so
  the control Fisher p is optimistic; this is noted, not corrected.
- 2 p-values.

### C4 liquidity (claim: Black Friday moves are unusually small)

- |BF return| vs |return| on all other days in the same years: median ratio
  and Mann-Whitney U two-sided p. **Primary.**
- The same for the Monday after.
- 2 p-values.

### Secondary index (^NDX)

- C1-week (3 statistics) and C3 primary repeated on ^NDX. 4 p-values.
  Reported for robustness; included in the multiple-testing family; they do
  not set the verdicts.

### Multiple testing

Benjamini-Hochberg across **all** p-values above (19). Raw and adjusted
reported.

## Verdict rules (per claim, from its primary test)

- **CONFIRMED**: BH-adjusted p < 0.05 **and** the effect has the same sign in
  both halves.
- **WEAK**: raw p < 0.10, or the halves disagree in sign.
- **KILLED**: otherwise.
- C3 also **INCONCLUSIVE** if n < 10 drawdown years or the 90% credible
  interval spans 50%.

"Effect sign" per claim:
- C1: observed statistic minus the median of the null draws (positive =
  better than other weeks).
- C2: second-half minus first-half hit rate, and the same for the median
  (negative = decay). Same sign = both negative or both positive.
- C3: drawdown-year hit rate minus other-year hit rate.
- C4: median |BF| / median |other| minus 1 (negative = quieter).

## 2026 setup (recorded, not tested)

Drawdown at entry on F0 = 2026-11-20 and week-to-date return F0 -> WB
(2026-11-25). Re-run on **2026-12-01** (score the week: BF = 2026-11-27) and
**2027-01-04** (score year-end) against the frozen base rates. 2026 never
enters a test.
