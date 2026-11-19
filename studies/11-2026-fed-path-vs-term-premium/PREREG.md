# Study 4: Fed path vs term premium. What is driving the 10-year at 5%?

**Date frozen:** 20 Nov 2026 (AEDT). Data pulled 19 Nov 2026 (UTC).
**Governing rules:** repository root `RESEARCH_PROTOCOL.md`. Study rules: `CLAUDE.md`.

## Problem

The 10-year Treasury yield is around 5.1%, the highest since 2007. The Fed hiked 25bp on 16 Sep 2026 (its first hike since 2023), held at 3.75-4.00% on 28 Oct, and markets largely price another hike on 9 Dec. The debate is whether the long end is high because markets expect a higher policy path (the Fed story) or because investors demand more compensation for holding duration (the term-premium story: oil and inflation risk, deficits, supply). The two stories lead to different trades and different reactions to a December hike.

## Question

How much of the 2026 rise in the 10-year yield comes from the expected path of short rates versus the term premium, through what channel, and is the current mix unusual compared with past hiking cycles?

## What has been seen before freezing

To build and check the data pipeline, the following were seen on screen: the last values of each series (fixtures in `config/fixtures.yaml`), the first rows of each file, and the dates of target changes. **No decomposition, change, regression or chart of any 2026 window has been computed.** The analysis code does not yet exist.

## Data (all public, pulled through the built-in browser because the workspace cannot reach these hosts)

| File | Source | Series | Coverage |
|---|---|---|---|
| `data/raw/acm_daily.csv` | NY Fed, `ACMTermPremium.xls`, sheet "ACM Daily" | ACMY01-10 (fitted zero yields), ACMTP01-10 (term premium), ACMRNY01-10 (risk-neutral yield = expected average short rate) | 1990-01-02 to 2026-11-17 |
| `data/raw/fred_daily.csv` | FRED `fredgraph.csv` | THREEFYTP2/5/10, THREEFY2/10 (Kim-Wright), DGS3MO/2/5/10/30, T10YIE, T5YIFR, DFII5/10, DCOILWTICO, DFEDTARU/L, DFF | 1990-01-02 to 2026-11-19, business days |
| `data/raw/fred_target_changes.csv` | FRED DFEDTAR (to 2008-12-15) and DFEDTARU (from 2008-12-16) | Change dates only (lossless for a step series) | 1982 to 2026-11-19 |
| `data/raw/fomc_dates.csv` | federalreserve.gov calendars and historical pages | Meeting and call end dates, scheduled flag | 1990 to 2026 |

Checksums and row counts are in `data/MANIFEST.md`. Cross-source fixture: the Financial Datasets par curve gives 10y = 7.94 on 1990-01-02, so DGS10 must equal 7.94 that day.

## Definitions (frozen)

- **Decomposition.** For maturity n: y(n) = RNY(n) + TP(n). Primary model **ACM** (Adrian, Crump and Moench). Secondary model **Kim-Wright** (KW): RNY = THREEFY - THREEFYTP. Both are fitted zero-coupon yields, not par yields.
- **Model-free cross-check.** DGS10 = DFII10 (real) + T10YIE (breakeven). This is a different split (real vs inflation compensation), reported beside the term-premium split, never substituted for it.
- **Common end date.** 2026-11-13 (last KW date). Every 2026 window ends there unless stated.
- **First hike.** Mechanical: the first target increase after at least 12 months with no increase, dated to the FOMC announcement on or before the FRED effective date. From 1990 this gives 1994-02-04, 1997-03-25, 1999-06-30, 2004-06-30, 2015-12-16, 2022-03-16 and 2026-09-16 (six prior episodes plus 2026).
- **Hike window.** First-hike date t0, from t0 minus 126 trading days to t0 plus 41 trading days. For 2026 that ends on or before 2026-11-13.
- **FOMC announcement days.** Scheduled meetings from 1994-02-04 onward (statements began in Feb 1994). Unscheduled meetings, calls, notation votes and the cancelled 2020-03-18 meeting are excluded. Two-day meetings use the second day.
- **Daily change.** Close-to-close difference in percentage points, on days where both series are present (pairwise, no fill).
- **Weekly change.** Last available business day of each week (Mon-Fri), differenced.

## Hypotheses

| ID | Claim | Test | Decision / kill rule |
|---|---|---|---|
| **H1** | The term premium accounts for more than half of the change in the 10y zero yield from 2025-12-31 to 2026-11-13. | Share = ΔTP10 / Δy10, under ACM and under KW. Descriptive, no p-value. | Both above 0.5: "term-premium driven". Both below 0.5: "path driven". Otherwise: **model-dependent, no claim**. If abs(Δy10) < 25bp the share is not reported (ratio unstable). |
| **H2** | The term-premium share of Δy10 in the 2026 hike window is higher than in each of the six prior hike windows. | Same share in every window, both models. | N = 6 prior episodes < 8: **prior only, not tested** (protocol rule 6). Full event list printed. |
| **H3** | In 2026 the long end has decoupled from policy news: the R² of daily ΔDGS10 on ΔDGS2 for 2026 is below the 10th percentile of calendar-year R² over 1990-2025. | OLS by calendar year (1990-2025, 36 years); empirical rank of 2026. p = (number of years with R² ≤ R²_2026 + 1) / 37. | Killed if 2026 is not in the bottom 10% or fails BH. |
| **H4a** | In 2026 the ACM 10y term premium moves with oil: weekly ΔACMTP10 on weekly Δln(WTI) has a positive slope. | OLS, 2026 weeks only, Newey-West (4 lags). One-sided p. | Killed if t < 2 or fails BH. |
| **H4b** | The oil sensitivity of the term premium is larger in 2026 than in 1990-2025. | Pooled weekly OLS with a 2026 dummy and interaction; interaction coefficient > 0, Newey-West (4 lags). One-sided p. | Killed if t < 2 or fails BH. |
| **H5a** | On FOMC announcement days, the 10y term premium responds to policy news: ΔACMTP10 on ΔDGS2 has a non-zero slope, 1994-2025. | OLS on scheduled announcement days, HC1 errors. Two-sided p. | Killed if it fails BH. Sign reported either way (no prior on direction: the literature has both a credibility channel, negative, and a risk-premium channel, positive). |
| **H5b** | 2026 announcement days show a larger term-premium share of the 10y move than the 1994-2025 average. | Descriptive, 7 days (Jan to Oct 2026). | N = 7 < 8: **prior only.** Every day printed. |

**Mechanisms.** H1 and H2: if the hike path were driving the long end, RNY10 should carry most of the move. H3: a term-premium-driven long end moves on news unrelated to the policy path, so policy-sensitive 2y changes explain less of it. H4: an energy shock raises inflation uncertainty, and inflation-risk compensation is part of the term premium. H5: the debate about Fed days ("hike and the curve steepens") is a claim about how the term premium reacts to policy news.

## FDR family

BH at q = 0.10 over {H3, H4a, H4b, H5a} (four p-values), run once at the end. H1 is a pre-set decision rule, not a test. H2 and H5b are priors.

## Robustness (reported, not in the family)

1. Kim-Wright in place of ACM for H4 and H5a.
2. H3 with ΔDGS30 in place of ΔDGS10.
3. H4 excluding 2020-03-01 to 2020-04-30.
4. H1 with the end date 2026-11-17 (ACM only).
5. The real vs breakeven split of ΔDGS10 over the H1 window.

## Live check (not a test)

**P1.** The FOMC decision on 9 Dec 2026: record the one-day ΔDGS2, ΔDGS10, ΔACMTP10 and ΔACMRNY10 when ACM publishes the date. Compare with the H5a slope. One observation, no inference.

## Known limitations

- ACM and KW are model estimates, and their parameters are re-estimated as new data arrive, so past values can be revised. The decomposition is only as good as the model. Results are reported under both, and a disagreement is a finding in itself.
- Neither model separates fiscal and supply premia from inflation-risk premia. H4 tests one channel (oil), not the full list.
- The six prior hike windows are a small sample with different starting conditions (1994 bond rout, 2022 from zero rates).
- Data pulled once on 19 Nov 2026. Later revisions are not tracked.

## Number of trials

Four tested p-values (H3, H4a, H4b, H5a), one decision rule (H1), two priors (H2, H5b), five robustness checks. Every run appends a row to `out/runs.csv`; every test to `out/tests_run.csv`.

## Deviations

None yet. Any change after this commit goes here, dated, with the original text kept.
