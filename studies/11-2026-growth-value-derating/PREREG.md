# PREREG: Is the Growth discount real?

**Splitting the 2026 S&P 500 Growth de-rating into price, earnings, composition and rates.**

Dated **28 Nov 2026**. Committed before any computation on the data pack. Governing rules: repo-root `RESEARCH_PROTOCOL.md`. Nothing here is a trading recommendation.

## What was seen before writing this

- The data pack README (`data/raw/README_datapack.md`) in full. It documents:
  - digitised end values: Growth forward P/E 17.10 and Value 17.29 on 27 Nov 2026;
  - the Dec 2025 Growth membership change (216 to 139 names);
  - method agreement between the two EPS series;
  - the Dec 2026 framework change.
- Column headers and the first data row of each file. The first rows are dated Jan 2024 or earlier, apart from snapshot files.
- No statistic over the study window was computed.
- The brief states the symptom: a peak near 29x, and 17.1x vs 17.3x on 27 Nov 2026.

## Symptom

The S&P 500 Growth forward P/E fell from its 2025-26 peak (about 29x) to about 17.1x on 27 Nov 2026. That is below Value (about 17.3x), the first crossing since 2008-09.

## Candidates (written before results)

- **A. Earnings catch-up.** Forward EPS rose and price was flat. Benign.
- **B. Inflated estimates.** EPS rose on accruals or capex optimism that cash does not support.
- **C. Fundamental de-rating.** Price fell on lower long-run growth or doubts about AI returns.
- **D. Discount-rate shock.** Rising real yields hit long-duration Growth.
- **E. Artefact.** Either the Dec 2025 style reconstitution (Growth went from about 216 to 139 names, with IT about half the index) or the roll of the forward-EPS window.

## Window (data-defined, fixed now)

- **Weekly grid:** Fridays in `row1_yardeni_fwd_pe_growth_value_weekly_2024_now.csv` (`week_ending`).
- **Peak:** the week of the maximum weekly Growth forward P/E with week_ending between 2025-01-03 and 2026-11-27 inclusive. Ties go to the earliest.
- **End:** 2026-11-27.
- **Reconstitution window:** weeks ending 2025-12-12 to 2026-01-02. Its log change runs from the week ending 2025-12-05 (last pre-window week) to the week ending 2026-01-02. The window counts only where it lies inside [Peak, End]. If the Peak falls after the window, the composition leg is 0; if the Peak falls inside it, the window is clipped at the Peak.

## Phase 1 decomposition (primary test)

**Identity:** dln(PE) = dln(Price) - dln(EPS), weekly, for Growth and for Value separately.

**Data**
- **PE:** row1 weekly (`growth`, `value`).
- **Price:** S&P DJI index levels from row3 (`sp500_growth_2029`, `sp500_value_2034`), taking the last close on or before each Friday. That covers holidays; dates are approximate to about 2 days, per the pack.
- **EPS, primary, method (b):** Price / PE, computed here from row3 and row1.
  - Under (b) the identity holds exactly, so **the residual is zero by construction**. It is still reported.
- **EPS, robustness, method (a):** row2 Blue Angels digitised (`*_fwd_eps_yardeni_blueangels_digitised`). Where (a) is missing (after about 30 Oct 2026), (b) is used, chain-linked so that the splice week adds no jump: the (b) series is rescaled to (a) at the last week with (a).
  - Under (a), the residual = total minus the legs, which is digitisation noise.

**Legs.** Each is a share of the total log P/E drop D = ln(PE_End) - ln(PE_Peak); legs sum to 1 with the residual.
- **PRICE** = sum of weekly dln(Price) outside the reconstitution window, divided by D.
- **EPS** = minus the sum of weekly dln(EPS) outside the window (organic EPS growth), divided by D.
- **COMPOSITION** = [dln(PE) over the window - dln(Price) over the window], divided by D.
- **RESIDUAL** = 1 - PRICE - EPS - COMPOSITION.

No EPS growth rate is computed across the window: the EPS jump inside it is the composition leg, which is how the series is chain-linked.

**Classification of the Growth legs** (applied in this order):
1. If EPS > 60% **and** PRICE > 50% both hold (possible when another leg is negative): "mixed", run 2A and 2B.
2. EPS > 60%: **"earnings-driven"**, run Phase 2A only.
3. PRICE > 50%: **"price-driven"**, run Phase 2B only.
4. Otherwise: **"mixed"**, run both 2A and 2B.
5. COMPOSITION > 30%: flag **"artefact material"**, whatever else holds.

**Value is the control.** The same legs are computed for Value over the same Peak and End weeks (the Growth peak, not Value's own). The crossing is explained in log points: the Growth-minus-Value difference in each leg, summing to the change in ln(PE_G/PE_V) over the window.

**Only the Phase 2 branch(es) the rule selects are run. The other branch is not run.**

### Robustness variants (all counted)

1. EPS method (a) instead of (b).
2. Reconstitution window shifted +1 week (weeks ending 2025-12-19 to 2026-01-09).
3. Reconstitution window shifted -1 week (weeks ending 2025-12-05 to 2025-12-26).
4. Window start at the second-highest weekly peak.
   - A "peak" here is a local maximum: a week whose Growth P/E is the highest within +/- 4 weeks.
   - The second-highest local maximum in the same 2025-01-03 to 2026-11-27 range is used.

Report whether the Phase 1 classification (and the artefact flag) flips under any variant. A classification that holds only in some variants is reported as fragile. The primary classification still selects the branch.

## Phase 2A: A vs B, earnings quality (run only if selected)

**Names:** the top 15 Growth names in `row5_IVW_top15_weights_end2025_vs_now.csv` with `in_top15_now` true, weighted by `weight_pct_2026-11-25`. Alphabet's GOOGL and GOOG weights are added together and use the cash flows filed under Alphabet. Weights are renormalised over the names that have data for each metric.

**Metrics** from `row6`, on trailing 4 quarters. "Latest" = the 4 quarters ending at each company's latest filed quarter; "one year earlier" = the 4 quarters ending 4 quarters before that. Each needs 8 consecutive quarters; a company lacking them is dropped from that metric.
- capex / OCF
- (OCF - capex - SBC) / net income, called "FCF-minus-SBC / NI"
- capex / depreciation
- OCF / net income

**Primary aggregation:** weight-weighted mean of the company ratios. Robustness: ratio of weight-weighted sums. Both are counted.

**Revisions**
- The breadth snapshot from row8: Growth vs Value net up-minus-down.
- FY1 consensus change over 90 days from row9 (`fy1_cur` vs `fy1_d90`), Growth vs Value. Each is weighted by the 25 Nov 2026 IVW / IVE weights. Names in both funds count in both.

**Verdict rule**
- **B supported:** the weighted top-15 FCF-minus-SBC / NI fell by more than 15 percentage points year on year, **and** the latest capex / depreciation is above 2.0.
- **A supported:** FCF-minus-SBC / NI did not fall by more than 10pp (change >= -10pp), **and** Growth revision breadth is net positive (up > down).
- **INCONCLUSIVE** otherwise.

If fewer than 8 names have data for a metric, that metric is prior-only (protocol rule 6), and any verdict that needs it is INCONCLUSIVE.

## Phase 2B: C vs D, rates (run only if selected)

**Data:** the weekly row1 grid from 2024-01-05 to 2026-11-27, with row4 DFII10 and T10YIE (FRED) taken as the last value on or before each Friday. FRED ends 25 Nov 2026, so the 27 Nov week uses 25 Nov values (noted).

**Regression:** d[ln PE_growth - ln PE_value] on d(DFII10) and d(T10YIE), with a constant and Newey-West standard errors with 4 lags.
- Run on the full window (primary) and on 2026 only.
- Robustness: the full window excluding the reconstitution-window weeks.

**D supported** if, in the primary regression:
- the real-yield coefficient is negative with |t| > 2;
- its Benjamini-Hochberg adjusted p < 0.10 within the Phase 2B family (protocol rule 5; an addition to the brief);
- **and** the real-yield change over the de-rating window explains at least half of the relative P/E move: coefficient x cumulative change in DFII10 (Peak to End) / cumulative change in ln(PE_G/PE_V) (Peak to End) >= 0.5.

Otherwise **C by elimination, labelled WEAK.**

**Phase 2B FDR family:** the real-yield and breakeven coefficient p-values in the full and 2026 regressions (4 tests), plus the robustness regression (2 tests). BH at q = 0.10 over these 6.

## Credit side-check (descriptive only)

ICE BofA IG OAS (`BAMLC0A0CM`) and BAA10Y change from the Peak week to the last available week (row10 weekly). There is no tech-specific spread in the pack, and RESULTS.md says so.

## Trials

Every leg, variant, metric and regression goes in `outputs/trials.csv`. The protocol ledger `outputs/tests_run.csv` gets every hypothesis test with raw and BH p-values where they exist. Killed claims go in `outputs/killed_hypotheses.md`. Seed 7. Nothing here is random except an optional bootstrap, and none is planned.

## Known limitations (stated up front)

- **No fixed-membership recompute:** there is no end-2025 constituent EPS.
- **The reconstitution date is inferred,** hence a window rather than a single week.
- **P/E dates are +/- 2 days,** because they are digitised.
- **Revision breadth is one snapshot,** taken 28 Nov 2026.
- **IVW weights are the fund's,** not the index's.
- **Survivorship is not an issue at index level.**

## Scheduled re-read

S&P DJI changes the style framework at the **21 Dec 2026** reconstitution: Growth drops 12-month momentum; Value adds intangibles-adjusted B/P, blended E/P and FCF/P. Pro-forma files are due 4 Dec. Phase 1 is re-run in the **first week of January 2027**, and RESULTS.md reports whether the Growth/Value P/E ordering survives the new membership. FINDINGS `valid_until` is 2027-01-08.
