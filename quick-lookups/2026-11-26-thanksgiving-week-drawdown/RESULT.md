# Thanksgiving week and drawdown at entry (result)

Run 2026-11-26 (Thanksgiving Day, before the 2026-11-27 session).
Pre-registration: [`PREREG.md`](PREREG.md), committed in `851e663` before any
data was downloaded. Nothing here is a trading recommendation.

**Data:** Yahoo ^GSPC daily closes 1950-01-03 to 2026-11-25 and ^NDX 1985-10-01
to 2026-11-25, price index only. Tests use 1950-2025 for the S&P 500 (76
Thanksgiving weeks) and 1986-2025 for the Nasdaq-100 (40). **2026 is not in any
test.** Seed 7, 10,000 resamples. **Trials counted: 19** (`outputs/trials.csv`);
Benjamini-Hochberg across all 19.

## Summary

| Claim | Verdict | Decisive number |
|---|---|---|
| C1 Thanksgiving week is unusually strong | **WEAK** | week up in **53 of 76 years (69.7%)** vs 56.6% for other 4-day windows; raw p 0.022, BH p 0.053 |
| C2 the edge has faded | **KILLED** | hit rate **73.7% (1950-1987) vs 65.8% (1988-2025)**, Fisher p 0.618 |
| C3 starting in a 10-20% correction changes year-end odds | **INCONCLUSIVE** | year-end up in **6 of 15 correction years (40.0%)** vs 43 of 60 other years (71.7%); 90% interval 22.7% to 60.9% spans 50% |
| C4 Black Friday moves are unusually small | **WEAK** | median absolute move **0.92x** a normal day, Mann-Whitney p 0.880; halves disagree |

## C1 seasonal

```
VERDICT: WEAK | confidence 60%
Claim: Thanksgiving week (Fri close to Black Friday close) is up more often, and by more, than other 4-day windows
Method: compare with one random other 4-day window per year, 10,000 draws, two-sided empirical p (seasonality test)
Data: Yahoo ^GSPC, 1950-2025, daily, as of 2026-11-25 close | Trials counted: 19
```

| Test | Thanksgiving | Other windows / days | Raw p | BH p | Rule |
|---|---|---|---|---|---|
| **Week up (primary)** | **69.7%** | 56.6% | 0.022 | **0.053** | WEAK |
| Week median | 0.87% | 0.25% | 0.002 | 0.015 | CONFIRMED |
| Week mean | 0.71% | 0.14% | 0.011 | 0.035 | CONFIRMED |
| Wednesday-before up | **76.3%** | 52.6% | 0.0002 | **0.004** | CONFIRMED |
| Wednesday-before median | 0.30% | 0.05% | 0.008 | 0.029 | CONFIRMED |
| Black Friday up | **71.1%** | 52.6% | 0.002 | **0.015** | CONFIRMED |
| Black Friday median | 0.26% | 0.05% | 0.016 | 0.045 | CONFIRMED |
| Black Friday mean | 0.28% | 0.04% | 0.032 | 0.057 | WEAK |

Conclusion: the pre-registered primary test (week up-rate) misses the BH cut by a hair, so C1 is **WEAK**.
The week's median and mean, and the two holiday days on their own, all pass after correction with the same sign in both halves.
The seasonal tilt is real for the two days around the holiday and mostly carries the week.
Would change if: the week up-rate's BH p drops below 0.05 once 2026 and later years join the sample.
Rival explanation: the holiday days are low-volume and historically drifted up; with only 76 weeks the week-level hit rate is noisy even if the days are not.
Nasdaq-100 (secondary, 1986-2025): week up 67.5% vs 57.5%, raw p 0.224; not significant.

## C2 decay

```
VERDICT: KILLED | confidence 70%
Claim: the Thanksgiving-week edge is smaller in 1988-2025 than in 1950-1987
Method: Fisher exact on up-weeks by half (primary), Mann-Whitney on week returns; rolling 20-year hit rate
Data: Yahoo ^GSPC, 1950-2025 | Trials counted: 19
```

| Half | Weeks up | Median week |
|---|---|---|
| 1950-1987 | **73.7%** (28 of 38) | 1.19% |
| 1988-2025 | **65.8%** (25 of 38) | 0.45% |
| Test | Fisher p **0.618** (BH 0.691) | Mann-Whitney p 0.136 (BH 0.199) |

Conclusion: both numbers are lower in the second half, but neither difference is close to significant. The rolling 20-year rate dipped to about 55% in 2000-2013 and recovered to 70% by 2025 (`outputs/c2_rolling_hit_rate.png`).
Would change if: a longer or out-of-sample record showed the 2000s dip persisting.
Rival explanation: 38 weeks per half is too few to see a moderate decay.

## C3 drawdown conditioning

```
VERDICT: INCONCLUSIVE | confidence 55%
Claim: when the S&P 500 enters Thanksgiving week 10-20% below its 252-day high, the year-end close beats the Black Friday close at a different rate
Method: Fisher exact, drawdown years vs other years; Beta(1,1) posterior with 90% credible interval; control on all Oct-Dec Fridays
Data: Yahoo ^GSPC, 1951-2025 (75 years with a full 252-day lookback) | Trials counted: 19
```

| Group | n | Year-end up | Posterior mean | 90% interval | Fisher p (BH) |
|---|---|---|---|---|---|
| **Drawdown 10-20% at entry** | **15** | **6 (40.0%)** | 41.2% | **22.7% to 60.9%** | **0.033 (0.057)** |
| Other years | 60 | 43 (71.7%) | | | |
| Control: Oct-Dec Fridays in a 10-20% drawdown | 137 | 90 (65.7%) | 65.5% | 58.7% to 72.0% | 0.027 (0.057) |
| Control: other Oct-Dec Fridays | 751 | 563 (75.0%) | | 72.3% to 77.5% | |
| Nasdaq-100, drawdown years (1986-2025) | 4 | 2 | 50.0% | 18.9% to 81.1% | 1.000 |

Conclusion: correction years ended the year up less often (40.0% vs 71.7%), and the gap points the same way in both halves.
But n = 15 and the 90% interval spans 50%, so under the pre-registered rule it is **INCONCLUSIVE**.
The control shows the same direction for any autumn Friday in a correction (65.7% vs 75.0%) but a smaller gap.
So part of the effect is "being in a drawdown", not "Thanksgiving". The control p is optimistic, because Fridays overlap within a year.
Would change if: a few more correction years land on the same side, pushing the interval below 50%.
Rival explanation: the 15 years cluster in bear markets (1957, 1969, 1973, 2000-2001, 2022); this may be bear-market momentum, not a holiday effect.

Drawdown years: 1957, 1962, 1966, 1969, 1970, 1971, 1973, 1977, 1978, 1981, 1990, 2000, 2001, 2011, 2022 (`outputs/c3_drawdown_years_gspc.csv`).

## C4 liquidity

```
VERDICT: WEAK | confidence 50%
Claim: absolute Black Friday moves are smaller than on other days
Method: median |return| ratio and Mann-Whitney U, Black Friday vs all other days in the same years; same for the Monday after
Data: Yahoo ^GSPC, 1950-2025 | Trials counted: 19
```

| Day | Median absolute move | vs other days | Mann-Whitney p (BH) | Halves |
|---|---|---|---|---|
| **Black Friday** | 0.43% | **0.92x** (other 0.46%) | **0.880 (0.929)** | disagree |
| Monday after | 0.53% | 1.16x | 0.066 (0.104) | agree (larger) |

Conclusion: Black Friday is not measurably quieter; the ratio is near 1, and it was above 1 before 1988 and below 1 after.
The verdict is WEAK only because the frozen rule says "WEAK if the halves disagree". Read without that clause it would be KILLED (see Deviations).
The Monday after moves more than a normal day (1.16x, raw p 0.066).
Would change if: intraday or volume data showed a real liquidity gap that close-to-close returns miss.
Rival explanation: the short session lowers volume, not necessarily the size of the close-to-close move.

## 2026 setup (recorded, not tested)

| Index | Friday before (2026-11-20) drawdown | Week to date (to Wed 2026-11-25) |
|---|---|---|
| S&P 500 | **-11.6%** (inside the 10-20% band) | **+3.94%** |
| Nasdaq-100 | -19.8% | +4.07% |

Frozen base rates to score against:
- **2026-12-01 re-run:** score the week. The base rate for an up week is 69.7%.
- **2027-01-04 re-run:** score year-end against Black Friday. Correction years went up 40.0% of the time, other years 71.7%.

These are point-in-time figures as of the 2026-11-25 close.

## Deviations

- **D1 (data window).** The drawdown needs 252 prior sessions, and the price file starts on 1950-01-03, so 1950 has no drawdown. C3 and its control therefore use 1951-2025 (75 years). C1, C2 and C4 use all 76 years. For the Nasdaq-100, PREREG already started at the first year with a full lookback (1986).
- **D2 (verdict rule reading).** The frozen rule is "WEAK: raw p < 0.10 **or** the halves disagree" and is applied as written. This matters only for C4: Black Friday's halves disagree (p 0.880), so it is WEAK. Under a reading where the halves only downgrade an otherwise significant result, C4 would be KILLED. Both readings are in `outputs/trials.csv` (`verdict_rule`, `alt_reading`).
- **D3 (one 3-day week).** 1963 had 3 trading days, because markets closed on 25 Nov 1963. It is kept as defined.
- **C3 rule order.** INCONCLUSIVE overrides the other labels when n < 10 or the interval spans 50%.

## Trial ledger (19)

- C1: 9 tests (week, Wednesday-before and Black Friday, each by up-rate, median and mean)
- C2: 2 tests
- C3: 2 tests (main and control)
- C4: 2 tests (Black Friday and Monday after)
- Nasdaq-100: 4 tests (C1 week by up-rate, median and mean; C3 main)

The 2026 setup is recorded but not tested. Full table: `outputs/trials.csv`.

## Files

- `run.py`: full pipeline (fetches Yahoo, about 15 seconds)
- `data/`: closes and per-year event tables
- `outputs/`: `trials.csv`, `results.json`, `c3_drawdown_years_gspc.csv`, `c2_rolling20_hit_rate.csv`, `c2_rolling_hit_rate.png`, `c1_week_vs_null.png`
