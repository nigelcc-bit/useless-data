# Study 1: Is the Nasdaq "Bear Trap" Real?

## Base rates for failed breakdowns of a swing low, Nasdaq 100 (1985-2026) and S&P 500 (1950-2026)

| | |
|---|---|
| **Authors** | Nigel (question, data sourcing), Claude (design, code, analysis) |
| **Run date** | 10 Nov 2026 (write-up compiled 13 Nov 2026) |
| **Project** | AI selloff programme — separate study from flush-or-regime |
| **Repo study** | `studies/2026-11-testing-nasdaq-bear-trap` (slug `testing-nasdaq-bear-trap`) |
| **Status** | Interim — Study 1 complete on full data in Claude chat; **not final**. Tier 1 registered at commit `1ff80ed`; **real-data run pending** clean CSVs. |
| **Companion studies** | `2026-11-flush-or-regime`; Study 2 (macro and valuation scorecard); midterm-election side study |
| **Code** | Claude workspace: `trap_study.py`, `trap_pool.py`, `trap_drill.py`, `trap_tail.py`, `make_charts.py` (not yet ported to this repo) |

---

## Contents

1. Executive summary
2. Background and the question
3. The current event in detail
4. Key terms
5. Data: sources, cleaning and validation
6. Method
7. Results
8. Charts
9. Interpretation and practical implications
10. How Study 1 fits with Study 2 and the midterm study
11. Limitations and threats to validity
12. What would change the conclusions
13. Reproducibility
14. Version history of the analysis
- Appendix A: Formulas
- Appendix B: Full event list, Nasdaq 100
- Appendix C: Full event list, S&P 500
- Appendix D: Sources

---

## 1. Executive summary

**Question.** On 5 Nov 2026 the Nasdaq 100 closed below its 29 Jul 2026 swing low and then closed back above it on 9 Nov. A widely shared chart labelled this, and two similar episodes in 2025 and 2026, as "bear traps": breakdowns that fail and lead to rallies. Does this pattern carry real information about what comes next, or is it picked out with hindsight?

**Answer.** The pattern carries **no forward-return edge**. Defined mechanically and tested on 41 years of Nasdaq data and 76 years of S&P data:

- **Reclaiming a broken 6-month low is the normal outcome, not a special signal.**
  - Nasdaq 100: **86%** of breaks (37 of 43) were reclaimed within 10 trading days.
  - S&P 500: **78%** (67 of 86).
- **Most reclaims are followed by a retest.** Within 60 trading days, price closed below the low of the break in **72%** of Nasdaq cases and **79%** of S&P cases.
- **Returns after a reclaim match any comparable dip.**
  - Nasdaq 120-day return: **+11.6%**, against **+10.0%** for all days 5-20% below their high (p = 0.32).
  - S&P 120-day return: **+3.7%** against **+3.6%** (p = 0.46).
  - Across 12 definitions and 3 horizons (36 tests), the smallest p-value is **0.09**. Nothing is significant, before or after allowing for the number of tests.
- **The cases most like today lean roughly 60/40 toward recovery on the Nasdaq.** These are reclaims made while the index was already 10-20% below its 120-day high (n = 17):
  - **59%** regained the high within about 6 months.
  - **35%** went on to a 20% drawdown.
  - The failures cluster in stress years: 1990, 2008, 2018, 2022 (twice) and 2025.
  - The S&P version of this group is weaker: 30% regained the high, 52% reached a 20% drawdown, n = 33.
- **The "traps" on the original chart were second sweeps.** In both March 2025 and March 2026 the first mechanical reclaim failed, and the real low came days to weeks later, 4.6% to 11.6% below the broken level. The chart marks a level that can only be identified after the fact.
- **The current breakdown is limited to the Nasdaq.** The S&P 500 did not break its own 6-month low (7,267). Broad bear markets such as 2000-02, 2008 and 2022 broke both indices.

**Bottom line for the current setup.** Expect a **retest of 26,630** (roughly 60-75% likely by base rate). A stop placed just under that level is more likely than not to be hit, even if the low eventually holds. After that, the Nasdaq history leans modestly toward recovery. Whether this episode is a flush or a regime change cannot be decided from price history; that is the job of the macro and positioning evidence (Study 2).

---

## 2. Background and the question

### 2.1 Where the question came from

During the November 2026 AI-stock selloff, a chart circulated showing the Nasdaq 100 from mid-2024 to November 2026, with three episodes marked "Trap":

| Episode | Prior swing low | Sweep below it | Outcome shown on the chart |
|---|---|---|---|
| 1 | Aug 2024 low | Apr 2025 sweep | Strong rally afterwards |
| 2 | Nov 2025 low | Mar-Apr 2026 sweep | Strong rally afterwards |
| 3 | Jul-Aug 2026 low | Nov 2026 sweep | Current, unresolved |

The implied claim is that a break below a prior swing low followed by a fast reversal (a "bear trap", "liquidity sweep" or "failed breakdown") marks a durable low.

### 2.2 Why the chart cannot answer the question

1. **Sample of three, chosen after the fact.** Only episodes that worked are marked. Breaks below support that kept going (2000-02, 2008, early 2022) are not shown.
2. **Bull-market window only.** 2024-2026 was mostly a rising market, where any dip-buying rule looks good.
3. **The levels are defined with hindsight.** The marked trap low is the lowest point of the episode, which is only known later.

The useful question is: **across all breaks of an established low, how often does a quick reclaim occur, and does it predict better-than-normal returns?**

### 2.3 Hypotheses (stated before running)

- **H1 (pattern has an edge):** returns after a reclaim of a broken swing low exceed returns on comparable days that were simply in a drawdown.
- **H0 (no edge):** returns after a reclaim are no different from comparable drawdown days.
- **Secondary questions:** how often reclaims are followed by retests, and how cases resembling today (already 10-20% off the high) turned out.

---

## 3. The current event in detail

All values are Nasdaq 100 daily closes unless stated.

| Item | Value |
|---|---|
| 6-month swing low (support) | **27,192.31** on 29 Jul 2026 |
| Days between the swing low and the break | 70 trading days |
| Last close before the break | 28,437.17 on 4 Nov 2026 |
| Break | **26,629.81** on 5 Nov 2026 (-6.36% on the day; 2.1% below support) |
| Intraday low on 5 Nov | 26,606.43 |
| Next close | 26,989.99 on 6 Nov 2026 (still below support) |
| Reclaim | **27,907.63** on 9 Nov 2026 (+3.40% on the day; 2.6% above support) |
| Sweep low (lowest close of the break) | 26,629.81 |
| 120-day high before the break | 31,224.47 on 6 Oct 2026 |
| Drawdown at the break | -14.7% from the 120-day high |
| 200-day average at the break | about 27,977 (price below it) |
| S&P 500 on 5 Nov 2026 | 7,353.73, above its own 6-month low of 7,267.0 (10 Jun 2026) and 5.9% off its 120-day high |
| S&P 500 on 9 Nov 2026 | 7,549.94 (Investing.com; Yahoo confirmed the same close in the Study 2 data pull) |

Context at the time (from the Project knowledge base, as of 10 Nov 2026): US midterm elections on 3 Nov 2026 produced a Democratic sweep; the Nasdaq 100 fell about 4.7% in the following week; the Fed funds target was 3.75-4.00% after a September hike; the 10-year Treasury yield was about 4.86%; and concern centred on the durability of AI capital spending.

---

## 4. Key terms

| Term | Meaning in this study |
|---|---|
| **Swing low / support (L)** | The lowest daily close over the previous N trading days, provided it was set at least 10 trading days earlier |
| **Break** | The first daily close below the support level |
| **Reclaim** | A daily close back above the support level within K trading days of the break |
| **Sweep low** | The lowest close between the break and the reclaim (or the K-day mark if there is no reclaim) |
| **Retest (failure)** | Any close below the sweep low within 60 trading days after the reclaim |
| **Trap** | A break that is reclaimed (used descriptively; the study tests whether it means anything) |
| **Drawdown-matched days** | Every day on which the index closed 5-20% below its 120-day high: the benchmark |
| **Placebo p-value** | The chance that randomly chosen drawdown-matched days do as well as or better than the days after reclaims |
| **Analog** | A reclaimed event where the index was 10-20% below its 120-day high at the break, as it is today |
| **Episode** | A cluster of related events in the same selloff; several breaks can occur in one bear market |
| **Trading days** | Market days; 20, 60, 120 and 252 trading days are roughly 1, 3, 6 and 12 months |

---

## 5. Data: sources, cleaning and validation

### 5.1 Sources

| Series | Coverage used | Days | Source |
|---|---|---|---|
| Nasdaq 100, part 1 | 26 Sep 1985 to 19 Jul 2005 | 5,000 | Investing.com export (downloaded by Nigel). Capped at 5,000 rows by the site |
| Nasdaq 100, part 2 | 3 Jan 2005 to 31 Dec 2018 | 3,523 | Investing.com export (Nigel) |
| Nasdaq 100, part 3 | 2 Jan 2019 to 9 Nov 2026 | 1,975 | Yahoo Finance-derived GitHub mirror (`Chief-rich/nasdaq100-data`); 9 Nov 2026 close replaced with the official Investing.com value |
| S&P 500, part 1 | 3 Jan 1950 to 31 Dec 2015 | 16,607 | `sp500` dataset in the gt R package (extracted from the conda-forge build; Yahoo-sourced OHLC) |
| S&P 500, part 2 | 4 Jan 2016 to 9 Nov 2026 | 2,729 | Investing.com export (Nigel) |
| S&P 500 check file | 2 Jan 1985 to 22 Oct 2004 | 5,000 | Investing.com export, used only to validate part 1 |

**Final series:**
- **Nasdaq 100:** 26 Sep 1985 to 9 Nov 2026, **10,360 trading days**.
- **S&P 500:** 3 Jan 1950 to 9 Nov 2026, **19,336 trading days**.

**Why these sources:** the analysis workspace cannot reach Yahoo Finance, FRED or Stooq directly. The Interactive Brokers connector returned no index history, and the Financial Datasets plan only covers one year. Nigel downloaded the Investing.com files in pieces to work around the 5,000-row limit.

### 5.2 Cleaning steps

1. Parsed Investing.com dates (MM/DD/YYYY) and removed thousands separators from prices.
2. Sorted ascending by date and confirmed there are no duplicate dates.
3. Spliced the Nasdaq parts: part 1 up to the day before part 2 starts, then part 2, then part 3 from 2019. Where files overlap, the later file is used.
4. Spliced the S&P parts: gt data up to 31 Dec 2015, then Investing.com from 4 Jan 2016.
5. Replaced the partial 9 Nov 2026 Nasdaq bar from the mirror (27,863) with the official close (27,907.63).
6. Used **closing prices only** for all event definitions. Before about 1962 the S&P data has open = high = low = close, which does not affect a close-based study.

### 5.3 Validation

| Check | Result |
|---|---|
| Nasdaq overlap, 2005 (137 days in both Investing.com files) | Exact match (maximum difference 0.0%) |
| Nasdaq joins (2004/2005, 2018/2019) | Ordinary daily returns at the joins; no jumps |
| S&P gt data vs Investing.com, 1985-2004 | Median absolute difference **0.004%**, maximum 0.17% |
| S&P join (2015/2016) | Ordinary daily returns; 4-day calendar gap over New Year |
| Duplicate dates | None in either series |
| Longest gap between trading days | Ordinary holiday and weekend gaps (7 calendar days or less) |
| Largest daily moves | Real events: Nasdaq +18.8% on 3 Jan 2001 and -15% on 19 Oct 1987; S&P -20.5% on 19 Oct 1987 |
| Recent Nasdaq closes (5 and 6 Nov 2026) | Mirror and Investing.com match exactly |
| S&P 9 Nov 2026 close | Investing.com 7,549.94. An early Yahoo search snippet showed 7,376.86, but the later Yahoo download matched 7,549.94. Resolved |

---

## 6. Method

### 6.1 Design principles

- **Define everything mechanically before looking at results**, so the pattern cannot be fitted to the answer.
- **Measure from the point a trader could act**: the reclaim close, not the eventual low.
- **Compare with a fair benchmark**, so the test asks whether the pattern beats "buying any dip", not whether stocks go up on average.
- **Report every variant tried**, including the ones that look worse.

### 6.2 Event definition (primary specification)

For each trading day *t*, using daily closes *C*:

1. **Support:** L(t) = min(C over days t-120 to t-1), the lowest close of the previous **N = 120** trading days.
2. **Established low:** the day that set L(t) must be at least **10 trading days** before *t*. Otherwise the "support" is just yesterday's close in a falling market.
3. **Break:** C(t) < L(t). Only the first close below starts an event. After a break, no new break can start for **20 trading days** (cooldown), so one selloff is not counted many times.
4. **Reclaim:** the first close C(t+k) > L(t) for k = 1 to **K = 10**.
5. **Sweep low:** the lowest close from the break to the reclaim, or to day t+K if there is no reclaim.
6. **Retest:** any close below the sweep low within 60 trading days after the reclaim (evaluated only when 60 days of later data exist).
7. **Forward returns** at 20, 60 and 120 trading days, measured from the reclaim close. For breaks without a reclaim, measured from the close K days after the break.
8. **Worst close within h days:** the lowest close in the h days after the reclaim, relative to the reclaim close.

**Why N = 120 and K = 10?** 120 trading days is about six months, a common "intermediate swing" horizon, and it is the shortest standard lookback that identifies the 29 Jul low as support for the current break: the low is 70 days old, so N = 60 would miss it. This choice was made knowing the current event. Section 7.6 shows the conclusion does not depend on it.

### 6.3 Outcome measures

| Measure | Definition |
|---|---|
| Reclaim rate | Share of breaks reclaimed within K days |
| Retest rate | Share of reclaims followed by a close below the sweep low within 60 trading days |
| Further 10% drop | The worst close in the 60 days after the reclaim is 10% or more below the reclaim close |
| 20% drawdown | Any close within 120 trading days after the reclaim that is 20% or more below the 120-day high as of the break |
| Regained high | Any close within 120 trading days after the reclaim at or above the 120-day high as of the break |
| Forward return | C(reclaim + h) / C(reclaim) - 1, for h = 20, 60, 120 |

### 6.4 Benchmarks

- **Unconditional:** the average h-day forward return over all days in the sample.
- **Drawdown-matched (main benchmark):** the average h-day forward return over all days on which the index closed **5-20% below its 120-day high**.
  - Pool size: 3,338 Nasdaq days and 5,837 S&P days.
  - Rationale: every reclaim happens during a drawdown, and drawdown days have different forward returns from average days. The pattern must beat this benchmark to add anything.

### 6.5 Significance test (placebo)

For each specification, index and horizon:

1. Let *n* be the number of reclaims with forward data, and *m* their mean forward return.
2. Draw *n* days at random, with replacement, from the drawdown-matched pool, and record their mean forward return.
3. Repeat 5,000 times (random seed 7).
4. **Placebo p-value** = the share of random draws whose mean is at least *m*.

A small p-value (below 0.05) would mean that reclaims beat random comparable dips by more than chance. A p-value near 0.5 means no difference.

### 6.6 Analog filter

To describe the cases most like today, reclaimed events are restricted to those where the index was **10% to 20% below its 120-day high at the break** (today: 14.7%). This band was chosen after seeing the current state, so it describes a reference group, not a tested hypothesis.

### 6.7 Robustness grid

| Parameter | Values tested |
|---|---|
| Support lookback N | 60, 120, 250 trading days |
| Reclaim window K | 5, 10 trading days |
| Index | Nasdaq 100, S&P 500 |
| Horizon | 20, 60, 120 trading days |

That is **12 specifications** and **36 placebo tests**. All are reported in section 7.6.

### 6.8 Follow-up splits (descriptive)

- **Sweep depth:** reclaimed events with a sweep low 1.5% or more below support (deep, like today's 2.1%) vs shallower.
- **Position vs 200-day average** at the break.
- **The analog band** (section 6.6).
- **Breaks that were not reclaimed**, for comparison.

### 6.9 Trial accounting

- Primary hypothesis tests: 36 (section 6.7).
- Descriptive splits: about 6.
- A Bonferroni correction for 36 tests would require p below 0.0014 for significance. No test came close even to 0.05, so the correction does not matter for the conclusion.

---

## 7. Results

### 7.1 Event counts and timing

| | Nasdaq 100 | S&P 500 |
|---|---|---|
| Sample | 1985-2026 (41 years) | 1950-2026 (76 years) |
| Breaks (primary spec) | 43 (including 5 Nov 2026) | 86 |
| Reclaimed within 10 days | 37 | 67 |
| Not reclaimed | 6 | 19 |
| Median age of the broken low | 52 trading days | 57 trading days |
| Median close below support on the break day | -0.7% | -0.6% |
| Median sweep low below support | -1.6% | -1.4% |
| Median time from break to reclaim | 3 calendar days | 2 calendar days |

Most breaks are shallow and short. The current break (-2.1% close, -2.1% sweep) is deeper than the median.

### 7.2 Headline results (primary specification: N = 120, K = 10)

| Measure | Nasdaq 100 | S&P 500 |
|---|---|---|
| Reclaimed within 10 days | **86%** (37 of 43) | **78%** (67 of 86) |
| Retest of sweep low within 60 days | **72%** (26 of 36 with data) | **79%** (53 of 67) |
| Further 10%+ drop within 60 days | 33% | 27% |
| Regained 120-day high within about 6 months | 50% | 33% |
| Share of reclaims with a positive 120-day return | 72% | 61% |

### 7.3 Forward returns vs benchmarks

| Horizon | Nasdaq: after reclaim | Nasdaq: drawdown-matched | Nasdaq: all days | Nasdaq p | S&P: after reclaim | S&P: drawdown-matched | S&P: all days | S&P p |
|---|---|---|---|---|---|---|---|---|
| 20 days | +1.5% | +1.6% | +1.3% | 0.54 | +0.5% | +0.7% | +0.7% | 0.61 |
| 60 days | +4.6% | +5.0% | +4.0% | 0.58 | +2.0% | +1.9% | +2.2% | 0.45 |
| 120 days | **+11.6%** | **+10.0%** | +8.0% | **0.32** | **+3.7%** | **+3.6%** | +4.4% | **0.46** |

**Reading:** the average return after a reclaim is within about 1.5 percentage points of the drawdown-matched benchmark at every horizon, in both indices, and none of the differences is statistically meaningful. **H0 (no edge) cannot be rejected.**

### 7.4 Breaks that were not reclaimed

| | Nasdaq 100 | S&P 500 |
|---|---|---|
| Breaks not reclaimed within 10 days | 6 | 19 |
| Average 60-day return (from day K) | +7.9% | +3.7% |
| Average 120-day return | +14.8% | +6.5% |

Breaks that were *not* reclaimed did no worse, and on these small samples slightly better (for example after the October 1987 crash). This is another sign that the reclaim itself carries little information.

### 7.5 Effect of sweep depth and trend

| Reclaimed events | Nasdaq 100 | S&P 500 |
|---|---|---|
| Deep sweep (1.5% or more below support), n | 16 | 23 |
| Deep: retest within 60 days | 60% | 65% |
| Deep: average 60-day / 120-day return | +1.1% / +6.2% | +0.4% / +1.3% |
| Shallow sweep: retest within 60 days | 81% | 86% |

- **Shallow breaks are revisited more often.** That is expected: when the sweep low sits barely below support, normal noise takes price back below it.
- **Deep breaks like today's retest less often, but have weaker returns afterwards** (Nasdaq 120-day +6.2% vs +11.6% for all reclaims).
- **Position vs 200-day average:** every break in both indices occurred with price below its 200-day average. Breaking a 6-month low almost guarantees that, so this split carries no information.

### 7.6 Robustness: all 12 specifications

| Index | N | K | Breaks | Reclaimed | Retest | 60d after reclaim | 120d after reclaim | p (20d) | p (60d) | p (120d) |
|---|---|---|---|---|---|---|---|---|---|---|
| S&P | 60 | 5 | 144 | 60% | 75% | +2.4% | +4.5% | 0.34 | 0.31 | 0.26 |
| S&P | 60 | 10 | 144 | 72% | 72% | +2.3% | +4.6% | 0.22 | 0.34 | 0.21 |
| S&P | 120 | 5 | 86 | 70% | 80% | +2.1% | +3.9% | 0.64 | 0.44 | 0.42 |
| **S&P** | **120** | **10** | **86** | **78%** | **79%** | **+2.0%** | **+3.7%** | **0.61** | **0.45** | **0.46** |
| S&P | 250 | 5 | 59 | 68% | 78% | +2.6% | +3.0% | 0.53 | 0.32 | 0.61 |
| S&P | 250 | 10 | 59 | 80% | 77% | +2.5% | +3.2% | 0.64 | 0.33 | 0.57 |
| Nasdaq | 60 | 5 | 79 | 63% | 60% | +6.8% | +13.3% | 0.13 | 0.17 | 0.12 |
| Nasdaq | 60 | 10 | 79 | 76% | 55% | +5.8% | +12.0% | 0.09 | 0.32 | 0.22 |
| Nasdaq | 120 | 5 | 43 | 72% | 73% | +6.4% | +13.9% | 0.38 | 0.29 | 0.14 |
| **Nasdaq** | **120** | **10** | **43** | **86%** | **72%** | **+4.6%** | **+11.6%** | **0.54** | **0.58** | **0.32** |
| Nasdaq | 250 | 5 | 20 | 65% | 69% | +1.1% | +7.7% | 0.88 | 0.87 | 0.66 |
| Nasdaq | 250 | 10 | 20 | 80% | 63% | -0.7% | +5.5% | 0.79 | 0.96 | 0.82 |

Bold rows are the primary specification. Drawdown-matched benchmarks: S&P +1.9% (60 days) and +3.6% (120 days); Nasdaq +5.0% and +10.0%.

- **Lowest p-value across 36 tests: 0.09** (Nasdaq, N = 60, K = 10, 20 days). Not significant at 5%, and far from the 0.0014 a Bonferroni correction would require.
- The Nasdaq rows with a 60-day lookback come closest to significance, but they capture many shallow, short-lived dips in a long-rising index.
- Reclaim and retest rates are high in every specification: reclaims 60-86%, retests 55-80%.

### 7.7 Closest matches to today (reclaimed while 10-20% off the 120-day high)

| | Nasdaq 100 | S&P 500 | Pooled |
|---|---|---|---|
| Events | 17 | 33 | 50 |
| Retest within 60 days | 59% | 82% | 74% |
| Went on to a 20% drawdown | **35%** | 52% | 46% |
| Regained the 120-day high within about 6 months | **59%** | 30% | 40% |

**All 17 Nasdaq analog events:**

| Break date | Off high at break | Retest within 60d | 60d return | 120d return | 20% drawdown | Regained high |
|---|---|---|---|---|---|---|
| 15 Nov 1988 | -12.4% | No | +8.6% | +24.5% | No | Yes |
| 15 Jan 1990 | -12.3% | Yes | +1.2% | +13.1% | No | Yes |
| 6 Aug 1990 | -18.2% | Yes | -14.9% | +9.7% | **Yes** | No |
| 17 Jun 1992 | -17.6% | Yes | +7.8% | +20.5% | No | Yes |
| 13 Apr 1994 | -12.2% | Yes | -3.4% | +6.4% | No | No |
| 23 Jun 1994 | -15.5% | No | +9.0% | +9.0% | No | No |
| 9 Jan 1996 | -14.0% | No | +10.0% | +22.5% | No | Yes |
| 15 Apr 2005 | -13.4% | No | +8.5% | +6.4% | No | No |
| 17 Jan 2008 | -17.7% | Yes | +4.2% | -2.1% | **Yes** | No |
| 2 Jul 2010 | -15.9% | No | +15.8% | +28.6% | No | Yes |
| 8 Aug 2011 | -15.2% | Yes | +8.4% | +14.2% | No | Yes |
| 21 Aug 2015 | -10.3% | No | +8.4% | -3.7% | No | Yes |
| 8 Feb 2016 | -16.1% | No | +9.5% | +18.0% | No | Yes |
| 19 Nov 2018 | -13.3% | Yes | +2.9% | +5.7% | **Yes** | Yes |
| 21 Jan 2022 | -12.9% | Yes | -3.5% | -18.1% | **Yes** | No |
| 22 Feb 2022 | -16.3% | Yes | -15.2% | -4.8% | **Yes** | No |
| 13 Mar 2025 | -13.3% | Yes | +11.4% | +20.0% | **Yes** | Yes |

- **Recoveries cluster in calmer periods:** 1988-96 and 2010-16.
- **The 20% drawdowns cluster in stress years:** 1990 (recession and Gulf War), 2008 (financial crisis), 2018 (Fed hiking into a slowdown), 2022 (inflation and rate shock) and 2025 (tariff shock).
- **Even two of those (2018 and 2025)** went on to regain the high within about 6 months.
- **The S&P analog group (n = 33)** includes clusters in 1973-74, 2000-02, 2008 and 2022, which explains its weaker figures. Several events come from the same bear market, so the number of independent episodes is well below 33.
- **A 59% rate on 17 events is uncertain:** a 95% range is roughly 35% to 80%.

### 7.8 The "traps" on the original chart

Applying the primary rule to the two earlier episodes on the chart:

| Episode | Support broken | First break | First reclaim | Retest? | Actual low | Depth of actual low below support |
|---|---|---|---|---|---|---|
| Mar-Apr 2025 | 19,344 | 13 Mar 2025 | 14 Mar 2025 | Yes | 17,090 on 8 Apr 2025 | **-11.6%** |
| Mar 2026 | 24,054 | 20 Mar 2026 | 23 Mar 2026 | Yes | 22,953 on 30 Mar 2026 | **-4.6%** |

- In both cases a trader acting on the first reclaim would have been stopped out or sat through a further drop.
- The chart's "trap" levels are the **second, deeper sweep**, which can only be identified once the rally is under way.
- The first episode on the chart (Aug 2024 low, Apr 2025 sweep) is not captured by the 120-day rule, because the Aug 2024 low was more than 120 trading days old by April 2025. It falls in the 250-day specification instead.

### 7.9 Breadth check: Nasdaq vs S&P

| | Nasdaq 100 | S&P 500 |
|---|---|---|
| 6-month low before 5 Nov | 27,192 (29 Jul 2026) | 7,267 (10 Jun 2026) |
| Close on 5 Nov | 26,630 (**below**) | 7,354 (**above**) |
| Off 120-day high | -14.7% | -5.9% |

The S&P never broke its own 6-month low during this selloff. Broad bear markets (2000-02, 2008, 2022) broke both indices. A breakdown confined to the Nasdaq is consistent with a sector or crowding unwind rather than a market-wide regime change. This is an observation about one episode, not a tested result.

---

## 8. Charts

The six charts are on the results page "Study 1: Is the Nasdaq bear trap real?" and are saved as PNG files.

| File | Title | What it shows |
|---|---|---|
| `c1_ndx_traps.png` | The chart's "traps" were second sweeps | Nasdaq 100, Jun 2024 to Nov 2026 (log scale), with each mechanical break (orange) and reclaim (green) marked, the support levels dashed, and the actual 2025 and 2026 lows annotated |
| `c2_outcomes.png` | Reclaim is normal, and so is a retest | Reclaim rate, retest rate, further 10% drop, and regained high, Nasdaq vs S&P |
| `c3_returns.png` | No better than any comparable dip | Average 20, 60 and 120-day returns after a reclaim vs drawdown-matched days, for each index |
| `c4_pvalues.png` | No definition shows an edge | Placebo p-values for all 12 specifications at 60 and 120 days, all well above 0.05 |
| `c5_ndx_analogs.png` | Cases most like today | The 17 Nasdaq analogs by date and 120-day return, coloured by whether they reached a 20% drawdown |
| `c6_ndx_vs_spx.png` | A Nasdaq-only breakdown | May to Nov 2026, each index against its own 6-month low |

---

## 9. Interpretation and practical implications

### 9.1 What the results mean

1. **A "trap" is a label, not a signal.** Quick reclaims are the most common outcome of a break below support, and they carry no information about forward returns beyond the fact that the market is in a drawdown.
2. **Retests are the norm.** Most reclaims are followed within three months by a close below the low of the break. Charts that show a clean V-shaped recovery are the minority.
3. **The second sweep problem.** The traps that look obvious in hindsight were often the second, deeper flush. A rule that buys the first reclaim is buying before the real low in a large share of cases.
4. **Context decides the outcome.** Among the cases most like today, the split between recovery and a deeper drawdown lines up with the macro backdrop (calm periods vs stress years), not with anything in the price pattern.

### 9.2 Practical implications for the current setup

| Situation | Base-rate guidance |
|---|---|
| Buying the 9 Nov reclaim | No edge over buying any comparable dip; expect a retest |
| Stop just below 26,630 | Likely to be hit (about 60-75% retest rate; 60% for deep sweeps) even if the low eventually holds |
| Scaling in | A plan that keeps size available for a retest fits the base rates better than full size on the first reclaim |
| Waiting for confirmation | A second sweep that holds, or confirmation from macro and positioning, is more informative than the first reclaim |
| 6-month view | Modest lean toward recovery on the Nasdaq (about 60/40 in the closest analogs), with wide uncertainty |

**Levels to watch:**
- **26,630:** the sweep low. A close below it means the retest has failed.
- **27,192:** support. Holding above it after a retest would be the "second sweep" pattern.
- **31,224:** the 120-day high. Regaining it within about 6 months happened in 59% of the closest analogs.

### 9.3 What this study cannot say

It cannot say whether this episode is a flush or a regime change. Price history only gives the base rate. Telling the two apart needs information outside price: earnings revisions, credit spreads, the yield curve, valuation and positioning. That is the subject of Study 2.

---

## 10. How Study 1 fits with Study 2 and the midterm study

| Study | Question | Main finding | Read for Nov 2026 |
|---|---|---|---|
| **Study 1** (this report) | Does a reclaimed breakdown predict anything? | No edge; retests are common; about 60/40 recovery in the closest analogs | Expect a retest of 26,630; modest lean to recovery |
| **Study 2** | Which non-price signals separated recoveries from deeper legs among these same events? | The combined macro checklist had no out-of-sample skill. An inverted yield curve (73% further drop, 7 episodes) and CAPE above 30 (70% further drop, 9 episodes) stood out, but rest on few episodes | Curve not inverted (+1.08); credit, labour and earnings benign; CAPE 40.7 is the one warning: a rougher path, not a failed recovery |
| **Midterm study** | Do stocks do well after US midterm elections? | 18 of 18 S&P and 10 of 10 Nasdaq midterms were followed by a positive 12 months; S&P +15.5% vs +7.4% for other Novembers (p = 0.02) | Supports a positive 12 months from the 2 Nov 2026 entry |

**Combined view:** a retest is likely, high valuation makes another leg down more likely than usual, and the macro backdrop and election cycle both lean toward eventual recovery. None of these is a forecast; they are base rates to size against.

---

## 11. Limitations and threats to validity

1. **Small samples.**
   - 43 Nasdaq and 86 S&P breaks overall.
   - The analog groups hold 17 and 33 events, and several come from the same bear market.
   - Percentages in those groups have wide uncertainty (roughly plus or minus 20 points).
2. **Clustering and overlap.**
   - The placebo test treats events as independent and draws benchmark days independently.
   - It ignores clustering in time and the overlap of 120-day return windows.
   - That makes the test, if anything, too generous to the pattern, which still showed no edge.
3. **Hindsight in parameter choice.**
   - N = 120 and the 10-20% analog band were chosen with the current event in view.
   - The grid shows the main conclusion holds across alternatives; the analog figures are descriptive.
4. **Survivorship and index changes.** Both indices changed composition over time (the Nasdaq 100 of 1990 is not the Nasdaq 100 of 2026). The study assumes price behaviour around swing lows is comparable across eras.
5. **Price only.** No information on macro, earnings, positioning or volatility was used (by design; see Study 2).
6. **Closes only.** Intraday sweeps that did not close below support are not counted; using intraday lows would produce more, shallower events.
7. **Data provenance.**
   - Index data comes from free sources (Investing.com, a Yahoo-derived mirror, and an R package dataset), not an official index vendor.
   - Cross-checks show close agreement, but small revisions or errors cannot be ruled out.
8. **Returns are price returns.** Dividends are excluded from both the event returns and the benchmark, so the comparison is fair, but absolute returns understate total return.

---

## 12. What would change the conclusions

| Finding | What would overturn or weaken it |
|---|---|
| No edge after a reclaim | A specification chosen before seeing the data, tested on new data (for example other markets or post-2026), that shows reclaims beating drawdown-matched days with p below 0.01 |
| Retests are likely | A much shorter retest window, or intraday definitions, could change the rates; the direction (retests common) is consistent across all 12 specifications |
| About 60/40 recovery in Nasdaq analogs | More events from future selloffs; adding other indices (Russell 2000, DAX, Nikkei) to pool independent episodes |
| Breakdown is Nasdaq-only | An S&P close below 7,267 would remove this argument |

---

## 13. Reproducibility

### 13.1 Files

| File | Purpose |
|---|---|
| `ndx_1985_2026.csv` | Cleaned Nasdaq 100 daily closes |
| `spx_1950_2026.csv` | Cleaned S&P 500 daily closes |
| `trap_study.py` | Event definition, 12-specification grid, benchmarks and placebo test; writes `trap_grid.csv` and the per-index event files |
| `events_NDX_1985-2026.csv`, `events_SPX_1950-2026.csv` | Every event under the primary specification, with outcomes |
| `trap_grid.csv` | Summary statistics and p-values for all 12 specifications |
| `trap_pool.py` | Per-index, pooled and analog outcome statistics |
| `trap_drill.py`, `trap_tail.py` | Sweep-depth and follow-through splits (written for earlier runs; the final figures in sections 7.5 and 7.7 were recomputed on the full data) |
| `make_charts.py` | The six charts |

### 13.2 Steps

1. Build the cleaned series from the source files (section 5.2).
2. Run `trap_study.py` to produce the events and grid.
3. Run `trap_pool.py` for the pooled and analog statistics.
4. Run `make_charts.py` for the charts.

**Environment:** Python 3.13 with pandas, NumPy and matplotlib. Random seed 7 for the placebo draws; p-values vary by about 0.01 between seeds.

---

## 14. Version history of the analysis

| Version | Data | Main change in results |
|---|---|---|
| v1 | S&P 1950-2015, Nasdaq 2019-2026 | First run: no edge; Nasdaq based on 11 events |
| v2 | Added Nasdaq 1985-2005 | Confirmed no edge; analog results diverged by era (1988-96 mostly recovered) |
| v3 | Added Nasdaq 2005-2018 (full 1985-2026 series) | Nasdaq 43 events; closest-match split about 60/40 toward recovery |
| v4 (final) | Added S&P 2016-2026 (full 1950-2026 series) | S&P 86 events; found that the S&P had not broken its own low in Nov 2026 |

The headline conclusion (no edge, retests common) was the same in every version.

---

## Appendix A: Formulas

- Support: L(t) = min{ C(t-N), ..., C(t-1) }, with argmin at least 10 days before t.
- Break: C(t) < L(t), and no break in the previous 20 trading days.
- Reclaim day: r = min{ t+k : C(t+k) > L(t), 1 <= k <= K }.
- Sweep low: S = min{ C(t), ..., C(r) }.
- Retest: exists j in 1..60 with C(r+j) < S.
- Forward return: R(h) = C(r+h) / C(r) - 1.
- Worst close within h days: W(h) = min{ C(r+1), ..., C(r+h) } / C(r) - 1.
- Drawdown at break: D = C(t) / max{ C(t-119), ..., C(t) } - 1.
- 20% drawdown outcome: exists j in 1..120 with C(r+j) / H - 1 <= -0.20, where H is the 120-day high at the break.
- Regained high outcome: exists j in 1..120 with C(r+j) >= H.
- Placebo p-value: p = (1/B) * sum over b of 1[ mean of n random benchmark returns in draw b >= observed mean ], B = 5,000.
- 95% range for a proportion (Wilson): (p + z²/2n ± z * sqrt(p(1-p)/n + z²/4n²)) / (1 + z²/n), z = 1.96.

---

## Appendix B and C: Full event lists (primary specification, N = 120, K = 10)

Column notes:
- **Support level:** the 6-month low that was broken.
- **Break close vs support:** how far the break-day close was below support.
- **Sweep low vs support:** the lowest close before the reclaim.
- **Off 120d high:** drawdown at the break.
- **Reclaim date:** for breaks not reclaimed, the date K days after the break, from which returns are measured.
- **Retest in 60d:** "n/a" where there was no reclaim or not enough later data.
- **Returns and worst close:** measured from the reclaim close (or the K-day mark).
- **Regained high in 120d:** reclaimed events only.


### Appendix B: Nasdaq 100, all 43 breaks (primary specification)

| # | Break date | Support level | Break close vs support | Sweep low vs support | Off 120d high | Reclaimed | Reclaim date | Retest in 60d | 20d | 60d | 120d | Worst within 60d | Regained high in 120d |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 11 Sep 1986 | 140.54 | -1.5% | -4.0% | -15.6% | No | 25 Sep 1986 (K-day mark) | n/a | +3.3% | +4.5% | +35.2% | -1.5% | n/a |
| 2 | 19 Oct 1987 | 181.47 | -14.2% | -29.2% | -27.2% | No | 02 Nov 1987 (K-day mark) | n/a | -9.9% | +3.6% | +14.6% | -14.3% | n/a |
| 3 | 15 Nov 1988 | 168.22 | -0.1% | -2.6% | -12.4% | Yes | 30 Nov 1988 | No | +4.4% | +8.6% | +24.5% | +0.6% | Yes |
| 4 | 15 Jan 1990 | 208.01 | -0.2% | -0.2% | -12.3% | Yes | 16 Jan 1990 | Yes | -2.2% | +1.2% | +13.1% | -6.7% | Yes |
| 5 | 06 Aug 1990 | 201.79 | -0.2% | -0.2% | -18.2% | Yes | 07 Aug 1990 | Yes | -4.4% | -14.9% | +9.7% | -18.5% | No |
| 6 | 24 Sep 1990 | 178.29 | -0.4% | -0.4% | -27.9% | Yes | 25 Sep 1990 | Yes | -1.3% | +10.9% | +41.5% | -8.6% | Yes |
| 7 | 17 Jun 1992 | 294.62 | -0.4% | -0.9% | -17.6% | Yes | 19 Jun 1992 | Yes | +1.2% | +7.8% | +20.5% | -2.3% | Yes |
| 8 | 13 Apr 1994 | 373.37 | -1.6% | -4.8% | -12.2% | Yes | 25 Apr 1994 | Yes | +0.6% | -3.4% | +6.4% | -6.1% | No |
| 9 | 23 Jun 1994 | 355.38 | -0.5% | -1.0% | -15.5% | Yes | 27 Jun 1994 | No | +0.8% | +9.0% | +9.0% | -2.1% | No |
| 10 | 09 Jan 1996 | 546.93 | -2.3% | -2.3% | -14.0% | Yes | 11 Jan 1996 | No | +12.4% | +10.0% | +22.5% | -3.7% | Yes |
| 11 | 31 Aug 1998 | 1,153.87 | -1.2% | -1.2% | -22.2% | Yes | 01 Sep 1998 | Yes | +10.7% | +31.6% | +63.7% | -7.1% | Yes |
| 12 | 08 Oct 1998 | 1,140.34 | -1.0% | -1.0% | -23.0% | Yes | 09 Oct 1998 | No | +21.7% | +64.0% | +85.3% | +0.8% | Yes |
| 13 | 12 Oct 2000 | 3,023.42 | -0.6% | -0.6% | -26.7% | Yes | 13 Oct 2000 | Yes | -11.8% | -26.4% | -55.8% | -35.1% | No |
| 14 | 10 Nov 2000 | 3,004.45 | -3.8% | -5.6% | -29.5% | Yes | 14 Nov 2000 | Yes | -9.6% | -24.8% | -38.3% | -30.0% | No |
| 15 | 19 Dec 2000 | 2,506.54 | -4.3% | -15.1% | -41.5% | Yes | 03 Jan 2001 | Yes | +3.1% | -37.8% | -30.7% | -38.2% | No |
| 16 | 20 Feb 2001 | 2,128.78 | -1.6% | -11.6% | -48.9% | No | 06 Mar 2001 (K-day mark) | n/a | -29.2% | -8.9% | -20.1% | -30.6% | n/a |
| 17 | 06 Sep 2001 | 1,370.75 | -0.7% | -17.8% | -33.7% | No | 26 Sep 2001 (K-day mark) | n/a | +24.6% | +36.2% | +26.9% | +0.1% | n/a |
| 18 | 03 Jun 2002 | 1,159.25 | -0.0% | -0.0% | -30.8% | Yes | 04 Jun 2002 | Yes | -18.3% | -19.8% | -5.1% | -27.3% | No |
| 19 | 23 Sep 2002 | 857.08 | -1.6% | -1.6% | -40.4% | Yes | 25 Sep 2002 | Yes | +12.4% | +14.3% | +22.1% | -8.6% | No |
| 20 | 26 Jul 2004 | 1,370.04 | -0.1% | -0.1% | -9.8% | Yes | 27 Jul 2004 | Yes | -1.6% | +4.4% | +12.2% | -6.3% | Yes |
| 21 | 15 Apr 2005 | 1,432.57 | -1.7% | -1.8% | -13.4% | Yes | 21 Apr 2005 | No | +5.1% | +8.5% | +6.4% | -2.6% | No |
| 22 | 12 May 2006 | 1,645.09 | -0.6% | -4.6% | -7.0% | No | 26 May 2006 (K-day mark) | n/a | -3.1% | -2.7% | +11.7% | -9.6% | n/a |
| 23 | 12 Jul 2006 | 1,516.85 | -1.0% | -4.3% | -13.7% | No | 26 Jul 2006 (K-day mark) | n/a | +4.2% | +14.7% | +20.6% | -0.6% | n/a |
| 24 | 17 Jan 2008 | 1,846.09 | -0.2% | -3.1% | -17.7% | Yes | 01 Feb 2008 | Yes | -6.6% | +4.2% | -2.1% | -9.8% | No |
| 25 | 03 Mar 2008 | 1,740.95 | -0.4% | -0.4% | -22.6% | Yes | 04 Mar 2008 | Yes | +6.0% | +15.8% | +10.8% | -4.1% | No |
| 26 | 12 Nov 2008 | 1,169.78 | -0.4% | -0.4% | -43.3% | Yes | 13 Nov 2008 | Yes | -2.8% | -1.1% | +12.3% | -16.5% | No |
| 27 | 02 Jul 2010 | 1,732.99 | -0.3% | -0.3% | -15.9% | Yes | 06 Jul 2010 | No | +9.1% | +15.8% | +28.6% | +1.9% | Yes |
| 28 | 16 Jun 2011 | 2,202.97 | -0.1% | -0.5% | -8.9% | Yes | 20 Jun 2011 | Yes | +8.8% | +2.2% | +3.5% | -7.5% | Yes |
| 29 | 08 Aug 2011 | 2,192.96 | -6.0% | -6.0% | -15.2% | Yes | 15 Aug 2011 | Yes | +0.3% | +8.4% | +14.2% | -7.9% | Yes |
| 30 | 21 Aug 2015 | 4,305.38 | -2.5% | -6.7% | -10.3% | Yes | 27 Aug 2015 | No | -2.3% | +8.4% | -3.7% | -5.6% | Yes |
| 31 | 08 Feb 2016 | 4,016.32 | -1.4% | -1.7% | -16.1% | Yes | 12 Feb 2016 | No | +8.7% | +9.5% | +18.0% | +2.1% | Yes |
| 32 | 19 Nov 2018 | 6,713.90 | -1.1% | -2.8% | -13.3% | Yes | 28 Nov 2018 | Yes | -9.1% | +2.9% | +5.7% | -14.7% | Yes |
| 33 | 12 Mar 2020 | 7,550.79 | -3.8% | -3.8% | -25.3% | Yes | 13 Mar 2020 | Yes | +4.2% | +24.7% | +55.3% | -12.5% | Yes |
| 34 | 21 Jan 2022 | 14,472.12 | -0.2% | -0.2% | -12.9% | Yes | 24 Jan 2022 | Yes | -4.4% | -3.5% | -18.1% | -10.1% | No |
| 35 | 22 Feb 2022 | 14,003.11 | -0.9% | -3.5% | -16.3% | Yes | 25 Feb 2022 | Yes | +4.0% | -15.2% | -4.8% | -16.6% | No |
| 36 | 26 Apr 2022 | 13,046.64 | -0.3% | -0.3% | -21.5% | Yes | 28 Apr 2022 | Yes | -8.8% | -10.2% | -17.5% | -17.3% | No |
| 37 | 13 Jun 2022 | 11,769.84 | -4.1% | -5.5% | -31.9% | Yes | 24 Jun 2022 | No | +1.8% | -2.1% | -3.0% | -5.0% | No |
| 38 | 30 Sep 2022 | 11,127.57 | -1.4% | -1.4% | -22.8% | Yes | 03 Oct 2022 | Yes | +1.6% | -4.9% | +12.9% | -4.9% | No |
| 39 | 03 Nov 2022 | 10,692.06 | -0.0% | -0.0% | -21.8% | Yes | 04 Nov 2022 | Yes | +8.6% | +17.9% | +21.9% | -1.6% | No |
| 40 | 28 Dec 2022 | 10,690.60 | -0.1% | -0.1% | -21.9% | Yes | 29 Dec 2022 | No | +8.8% | +15.2% | +36.0% | -1.9% | Yes |
| 41 | 13 Mar 2025 | 19,344.49 | -0.6% | -0.6% | -13.3% | Yes | 14 Mar 2025 | Yes | -5.1% | +11.4% | +20.0% | -13.3% | Yes |
| 42 | 20 Mar 2026 | 24,054.38 | -0.6% | -0.6% | -8.5% | Yes | 23 Mar 2026 | Yes | +9.5% | +22.7% | +20.4% | -5.1% | Yes |
| 43 | 05 Nov 2026 | 27,192.31 | -2.1% | -2.1% | -14.7% | Yes | 09 Nov 2026 | n/a | n/a | n/a | n/a | n/a | n/a |

### Appendix C: S&P 500, all 86 breaks (primary specification)

| # | Break date | Support level | Break close vs support | Sweep low vs support | Off 120d high | Reclaimed | Reclaim date | Retest in 60d | 20d | 60d | 120d | Worst within 60d | Regained high in 120d |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 13 Jul 1950 | 16.73 | -0.2% | -0.2% | -14.0% | Yes | 14 Jul 1950 | Yes | +8.4% | +18.6% | +24.5% | -1.1% | Yes |
| 2 | 01 Jun 1953 | 24.19 | -0.2% | -0.2% | -9.4% | Yes | 02 Jun 1953 | Yes | -0.3% | -1.2% | +0.6% | -2.8% | No |
| 3 | 31 Aug 1953 | 23.54 | -0.9% | -0.9% | -11.4% | Yes | 02 Sep 1953 | Yes | -0.3% | +5.9% | +11.4% | -3.6% | No |
| 4 | 21 Nov 1956 | 44.70 | -0.1% | -0.1% | -10.0% | Yes | 23 Nov 1956 | Yes | +2.7% | -3.3% | +4.5% | -6.1% | No |
| 5 | 05 Feb 1957 | 44.38 | -1.1% | -4.5% | -10.4% | No | 19 Feb 1957 (K-day mark) | n/a | +1.4% | +8.1% | +6.5% | -0.5% | n/a |
| 6 | 10 Sep 1957 | 43.88 | -0.0% | -0.0% | -10.7% | Yes | 11 Sep 1957 | Yes | -5.1% | -6.7% | -6.6% | -11.9% | No |
| 7 | 21 Sep 1959 | 56.00 | -1.3% | -1.5% | -9.0% | Yes | 24 Sep 1959 | No | -1.4% | +4.3% | -3.2% | -1.4% | No |
| 8 | 16 Feb 1960 | 55.14 | -0.7% | -0.7% | -9.4% | Yes | 18 Feb 1960 | Yes | -1.4% | -1.0% | +0.5% | -4.2% | No |
| 9 | 19 Sep 1960 | 54.13 | -0.5% | -0.5% | -7.2% | Yes | 21 Sep 1960 | Yes | -0.6% | +4.8% | +16.5% | -4.3% | Yes |
| 10 | 25 Oct 1960 | 52.48 | -0.5% | -0.5% | -10.1% | Yes | 26 Oct 1960 | No | +5.8% | +13.9% | +24.1% | +0.6% | Yes |
| 11 | 16 Apr 1962 | 67.90 | -0.4% | -0.4% | -6.9% | Yes | 18 Apr 1962 | Yes | -6.4% | -15.3% | -16.2% | -23.4% | No |
| 12 | 14 Jun 1962 | 55.50 | -2.1% | -2.1% | -24.2% | Yes | 15 Jun 1962 | Yes | +3.5% | +4.8% | +12.6% | -6.4% | No |
| 13 | 07 Mar 1966 | 89.03 | -1.1% | -1.9% | -6.4% | Yes | 21 Mar 1966 | Yes | +2.7% | -2.8% | -14.5% | -6.2% | No |
| 14 | 09 May 1966 | 87.35 | -1.2% | -4.3% | -8.2% | No | 23 May 1966 (K-day mark) | n/a | +0.6% | -5.8% | -4.9% | -5.8% | n/a |
| 15 | 29 Jul 1966 | 83.63 | -0.0% | -1.6% | -11.1% | Yes | 04 Aug 1966 | Yes | -7.4% | -4.4% | +2.2% | -12.8% | No |
| 16 | 06 Oct 1966 | 74.53 | -0.6% | -1.8% | -19.9% | Yes | 11 Oct 1966 | No | +8.6% | +10.5% | +19.9% | +2.3% | No |
| 17 | 08 Feb 1968 | 91.14 | -0.3% | -2.3% | -6.9% | Yes | 20 Feb 1968 | Yes | -2.5% | +6.2% | +8.2% | -3.9% | Yes |
| 18 | 17 Jun 1969 | 97.98 | -0.0% | -1.8% | -7.7% | Yes | 01 Jul 1969 | Yes | -6.4% | -4.0% | -7.6% | -8.8% | No |
| 19 | 17 Dec 1969 | 89.48 | -0.3% | -0.3% | -10.5% | Yes | 18 Dec 1969 | Yes | -1.1% | -3.7% | -16.7% | -6.2% | No |
| 20 | 26 Jan 1970 | 89.20 | -1.2% | -4.7% | -10.3% | No | 09 Feb 1970 (K-day mark) | n/a | +2.0% | -8.7% | -10.3% | -9.7% | n/a |
| 21 | 22 Apr 1970 | 85.02 | -0.9% | -7.6% | -14.3% | No | 06 May 1970 (K-day mark) | n/a | -1.2% | -1.8% | +5.4% | -12.8% | n/a |
| 22 | 30 Jul 1971 | 95.72 | -0.1% | -0.1% | -8.8% | Yes | 02 Aug 1971 | Yes | +3.7% | -1.3% | +8.3% | -2.5% | No |
| 23 | 01 Nov 1971 | 93.53 | -0.8% | -0.8% | -9.6% | Yes | 03 Nov 1971 | Yes | +1.0% | +9.7% | +12.9% | -5.0% | Yes |
| 24 | 25 Apr 1973 | 108.52 | -0.2% | -0.2% | -9.9% | Yes | 26 Apr 1973 | Yes | -1.6% | -1.3% | +1.2% | -7.0% | No |
| 25 | 25 Jun 1973 | 102.73 | -0.5% | -0.5% | -15.0% | Yes | 26 Jun 1973 | Yes | +6.1% | +3.3% | -9.7% | -2.7% | No |
| 26 | 21 Aug 1973 | 101.28 | -0.4% | -0.7% | -12.3% | Yes | 23 Aug 1973 | No | +5.2% | +1.9% | -10.7% | -0.3% | No |
| 27 | 20 Nov 1973 | 100.53 | -1.9% | -8.3% | -11.5% | No | 05 Dec 1973 (K-day mark) | n/a | +7.3% | +3.7% | -5.7% | -1.6% | n/a |
| 28 | 11 Feb 1974 | 92.16 | -1.6% | -1.6% | -18.6% | Yes | 15 Feb 1974 | Yes | +6.3% | -1.7% | -11.6% | -2.9% | No |
| 29 | 24 Apr 1974 | 90.66 | -0.4% | -1.2% | -16.1% | Yes | 01 May 1974 | Yes | -5.2% | -10.6% | -20.3% | -13.4% | No |
| 30 | 27 Jun 1974 | 86.89 | -0.7% | -8.1% | -13.5% | No | 12 Jul 1974 (K-day mark) | n/a | -2.8% | -21.9% | -15.5% | -25.1% | n/a |
| 31 | 31 Jul 1974 | 79.89 | -0.7% | -1.6% | -20.5% | Yes | 06 Aug 1974 | Yes | -14.7% | -7.7% | -6.4% | -22.7% | No |
| 32 | 27 Sep 1974 | 65.20 | -0.4% | -4.5% | -31.5% | Yes | 09 Oct 1974 | No | +10.2% | +4.8% | +21.5% | -4.1% | No |
| 33 | 30 Mar 1977 | 98.81 | -0.3% | -0.4% | -8.3% | Yes | 01 Apr 1977 | Yes | -0.3% | +0.9% | -4.2% | -3.1% | No |
| 34 | 25 May 1977 | 97.11 | -0.4% | -1.0% | -9.9% | Yes | 03 Jun 1977 | Yes | +2.5% | -1.3% | -1.2% | -1.7% | No |
| 35 | 26 Aug 1977 | 96.12 | -0.1% | -0.1% | -6.0% | Yes | 29 Aug 1977 | Yes | -1.7% | -0.9% | -9.2% | -6.4% | No |
| 36 | 11 Oct 1977 | 95.04 | -0.1% | -4.3% | -6.7% | No | 25 Oct 1977 (K-day mark) | n/a | +5.6% | -1.2% | +2.7% | -1.7% | n/a |
| 37 | 09 Jan 1978 | 90.71 | -0.1% | -1.6% | -10.9% | No | 23 Jan 1978 (K-day mark) | n/a | -1.8% | +5.2% | +9.3% | -2.6% | n/a |
| 38 | 16 Feb 1978 | 88.58 | -0.6% | -1.7% | -10.1% | No | 03 Mar 1978 (K-day mark) | n/a | +1.2% | +10.8% | +20.0% | -0.6% | n/a |
| 39 | 31 Oct 1978 | 94.27 | -1.2% | -1.2% | -12.9% | Yes | 01 Nov 1978 | Yes | -2.2% | +4.9% | +5.8% | -4.5% | No |
| 40 | 24 Mar 1980 | 99.87 | -0.6% | -1.7% | -16.2% | Yes | 28 Mar 1980 | No | +4.9% | +14.4% | +27.5% | -0.9% | Yes |
| 41 | 24 Aug 1981 | 127.13 | -1.3% | -7.2% | -8.5% | No | 08 Sep 1981 (K-day mark) | n/a | +1.2% | +5.7% | -4.0% | -4.4% | n/a |
| 42 | 22 Feb 1982 | 112.77 | -1.0% | -1.1% | -11.7% | Yes | 24 Feb 1982 | Yes | -0.4% | +1.0% | -8.3% | -5.4% | No |
| 43 | 18 Jun 1982 | 107.34 | -0.1% | -0.1% | -12.6% | Yes | 22 Jun 1982 | Yes | +2.9% | +14.3% | +28.9% | -5.4% | Yes |
| 44 | 30 Jul 1982 | 107.20 | -0.1% | -0.1% | -10.4% | Yes | 02 Aug 1982 | Yes | +8.0% | +23.4% | +34.2% | -6.0% | Yes |
| 45 | 06 Feb 1984 | 160.84 | -1.7% | -3.9% | -8.4% | No | 21 Feb 1984 (K-day mark) | n/a | +2.7% | +2.2% | +7.0% | -0.2% | n/a |
| 46 | 22 May 1984 | 154.29 | -0.3% | -2.6% | -9.1% | Yes | 04 Jun 1984 | Yes | -0.7% | +8.5% | +6.6% | -4.2% | Yes |
| 47 | 23 Jul 1984 | 149.03 | -0.1% | -0.8% | -8.8% | Yes | 26 Jul 1984 | No | +11.4% | +11.9% | +14.1% | +0.1% | Yes |
| 48 | 29 Sep 1986 | 230.67 | -0.3% | -0.3% | -9.4% | Yes | 30 Sep 1986 | No | +3.4% | +6.7% | +30.2% | +1.0% | Yes |
| 49 | 19 Oct 1987 | 278.21 | -19.2% | -19.2% | -33.2% | No | 02 Nov 1987 (K-day mark) | n/a | -9.3% | -1.0% | +2.6% | -12.4% | n/a |
| 50 | 04 Dec 1987 | 224.84 | -0.4% | -0.4% | -33.5% | Yes | 07 Dec 1987 | No | +13.2% | +17.1% | +10.8% | +2.1% | No |
| 51 | 22 Jan 1990 | 332.61 | -0.7% | -2.9% | -8.2% | No | 05 Feb 1990 (K-day mark) | n/a | +1.8% | +0.8% | +6.5% | -2.3% | n/a |
| 52 | 17 Aug 1990 | 329.11 | -0.4% | -6.7% | -11.1% | No | 31 Aug 1990 (K-day mark) | n/a | -2.4% | -1.4% | +13.4% | -8.4% | n/a |
| 53 | 24 Sep 1990 | 307.06 | -0.8% | -0.8% | -17.4% | Yes | 25 Sep 1990 | Yes | +1.3% | +7.1% | +20.7% | -4.2% | Yes |
| 54 | 29 Mar 1994 | 457.49 | -1.1% | -4.1% | -6.1% | No | 13 Apr 1994 (K-day mark) | n/a | -0.6% | +0.4% | +1.9% | -1.1% | n/a |
| 55 | 27 Aug 1998 | 1,052.31 | -0.9% | -9.0% | -12.1% | No | 11 Sep 1998 (K-day mark) | n/a | -2.4% | +17.7% | +26.4% | -4.9% | n/a |
| 56 | 23 Sep 1999 | 1,281.41 | -0.1% | -0.3% | -9.8% | Yes | 27 Sep 1999 | Yes | +0.8% | +11.7% | +14.1% | -2.8% | Yes |
| 57 | 11 Oct 2000 | 1,373.86 | -0.7% | -3.2% | -10.3% | Yes | 13 Oct 2000 | Yes | -0.6% | -4.4% | -17.9% | -8.0% | No |
| 58 | 22 Nov 2000 | 1,329.78 | -0.6% | -0.6% | -13.0% | Yes | 24 Nov 2000 | Yes | -2.7% | -6.6% | -3.7% | -6.6% | No |
| 59 | 21 Feb 2001 | 1,264.74 | -0.7% | -1.5% | -17.5% | Yes | 26 Feb 2001 | Yes | -9.1% | +3.3% | -6.8% | -13.0% | No |
| 60 | 07 Sep 2001 | 1,103.25 | -1.6% | -12.5% | -17.3% | No | 27 Sep 2001 (K-day mark) | n/a | +8.0% | +12.4% | +13.3% | +2.0% | n/a |
| 61 | 26 Apr 2002 | 1,080.17 | -0.4% | -1.4% | -8.2% | Yes | 01 May 2002 | Yes | -2.0% | -21.5% | -17.2% | -26.6% | No |
| 62 | 03 Jun 2002 | 1,049.49 | -0.8% | -0.8% | -11.2% | Yes | 05 Jun 2002 | Yes | -9.1% | -12.6% | -11.4% | -24.0% | No |
| 63 | 07 Oct 2002 | 797.70 | -1.6% | -1.6% | -30.2% | Yes | 08 Oct 2002 | Yes | +14.6% | +13.8% | +7.5% | -2.7% | No |
| 64 | 26 Jul 2004 | 1,084.10 | -0.0% | -0.0% | -6.4% | Yes | 27 Jul 2004 | Yes | +0.1% | +0.8% | +8.2% | -2.9% | Yes |
| 65 | 12 Jun 2006 | 1,248.29 | -0.9% | -2.0% | -6.7% | Yes | 15 Jun 2006 | No | -1.6% | +3.5% | +12.6% | -1.7% | Yes |
| 66 | 08 Jan 2008 | 1,406.70 | -1.2% | -1.2% | -11.2% | Yes | 09 Jan 2008 | Yes | -5.1% | -2.6% | -8.8% | -9.6% | No |
| 67 | 06 Mar 2008 | 1,310.50 | -0.5% | -2.8% | -16.7% | Yes | 11 Mar 2008 | No | +2.6% | +6.3% | -2.9% | -3.3% | No |
| 68 | 02 Jul 2008 | 1,273.37 | -0.9% | -1.7% | -11.6% | Yes | 08 Jul 2008 | Yes | +0.9% | -8.8% | -31.5% | -13.1% | No |
| 69 | 15 Sep 2008 | 1,214.91 | -1.8% | -4.8% | -16.4% | Yes | 19 Sep 2008 | Yes | -25.1% | -30.8% | -39.7% | -40.0% | No |
| 70 | 19 Nov 2008 | 848.92 | -5.0% | -11.4% | -42.6% | Yes | 24 Nov 2008 | Yes | +1.3% | -12.7% | +6.6% | -12.7% | No |
| 71 | 23 Feb 2009 | 752.44 | -1.2% | -1.2% | -41.8% | Yes | 24 Feb 2009 | Yes | +4.3% | +16.9% | +29.9% | -12.5% | No |
| 72 | 07 Jun 2010 | 1,056.74 | -0.6% | -0.6% | -13.7% | Yes | 08 Jun 2010 | Yes | -0.2% | +1.7% | +12.0% | -3.7% | Yes |
| 73 | 02 Aug 2011 | 1,256.88 | -0.2% | -0.2% | -8.0% | Yes | 03 Aug 2011 | Yes | -3.3% | +1.9% | +5.2% | -12.8% | No |
| 74 | 03 Oct 2011 | 1,119.46 | -1.8% | -1.8% | -19.4% | Yes | 04 Oct 2011 | No | +8.4% | +12.4% | +25.7% | +1.8% | Yes |
| 75 | 15 Oct 2014 | 1,863.40 | -0.0% | -0.0% | -7.4% | Yes | 17 Oct 2014 | No | +8.1% | +6.6% | +10.9% | +0.9% | Yes |
| 76 | 20 Aug 2015 | 2,040.24 | -0.2% | -8.5% | -4.5% | No | 03 Sep 2015 (K-day mark) | n/a | +0.0% | +6.6% | -0.2% | -3.6% | n/a |
| 77 | 20 Jan 2016 | 1,867.61 | -0.4% | -0.4% | -11.9% | Yes | 21 Jan 2016 | Yes | +2.6% | +12.1% | +15.2% | -2.1% | Yes |
| 78 | 24 Oct 2018 | 2,663.40 | -0.3% | -0.3% | -9.4% | Yes | 25 Oct 2018 | Yes | -2.7% | -2.3% | +7.5% | -13.1% | No |
| 79 | 23 Nov 2018 | 2,641.20 | -0.3% | -0.3% | -10.2% | Yes | 26 Nov 2018 | Yes | -7.7% | +4.6% | +7.1% | -12.1% | Yes |
| 80 | 09 Mar 2020 | 2,887.60 | -4.9% | -22.5% | -18.9% | No | 23 Mar 2020 (K-day mark) | n/a | +22.3% | +39.2% | +49.3% | +9.4% | n/a |
| 81 | 23 Feb 2022 | 4,300.50 | -1.7% | -1.7% | -11.9% | Yes | 25 Feb 2022 | Yes | +3.6% | -9.4% | -2.3% | -11.0% | No |
| 82 | 29 Apr 2022 | 4,170.70 | -0.9% | -0.9% | -13.9% | Yes | 03 May 2022 | Yes | -1.8% | -1.1% | -9.1% | -12.2% | No |
| 83 | 13 Jun 2022 | 3,900.79 | -3.9% | -6.0% | -21.8% | Yes | 24 Jun 2022 | No | +1.4% | -1.4% | +2.1% | -3.2% | No |
| 84 | 26 Sep 2022 | 3,666.77 | -0.3% | -0.5% | -19.2% | Yes | 28 Sep 2022 | Yes | +3.0% | +2.8% | +5.9% | -3.8% | No |
| 85 | 10 Mar 2025 | 5,618.26 | -0.1% | -1.7% | -8.6% | Yes | 14 Mar 2025 | Yes | -4.9% | +7.1% | +14.9% | -11.6% | Yes |
| 86 | 20 Mar 2026 | 6,538.76 | -0.5% | -0.5% | -6.8% | Yes | 23 Mar 2026 | Yes | +7.3% | +12.8% | +15.8% | -3.6% | Yes |


---

## Appendix D: Sources

**Data**
- Investing.com, Nasdaq 100 and S&P 500 historical data (CSV exports downloaded by Nigel, Nov 2026).
- Yahoo Finance-derived Nasdaq 100 daily history, GitHub repository `Chief-rich/nasdaq100-data` (`data/ndx_daily/history.csv`), accessed 10 Nov 2026.
- `sp500` dataset in the gt R package (version 1.4.0, conda-forge build), daily S&P 500 OHLC 1950-2015.
- Yahoo Finance (via the Study 2 data pull) for the 9 Nov 2026 S&P 500 cross-check.

**Context**
- Project knowledge base (`claude/quant-knowledge-base.md`), market snapshot as of 10 Nov 2026, for the Fed, yields and midterm context.
- Original "Trap" chart and JPM, BofA and prime broker charts shared by Nigel, 10 Nov 2026.

**Methods background** (from memory; check before formal citation)
- Bailey and Lopez de Prado (2014), The Deflated Sharpe Ratio, on multiple-testing inflation.
- Harvey, Liu and Zhu (2016), ...and the Cross-Section of Expected Returns, on t-stat hurdles for data-mined patterns.

---

*Not investment advice. Base rates describe history; they do not determine the next move.*
