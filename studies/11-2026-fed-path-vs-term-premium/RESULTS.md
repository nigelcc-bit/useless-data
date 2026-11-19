# Study 4: results

Pre-registration frozen in `596af1d`; definitional deviations D1-D2 committed in `649d424` before any result; analysis code committed in `726d13b` before its first run. Numbers below are copied from `out/*.csv` and `out/tests_run.csv`. No narrative.

Changes in basis points (bp). 2026 windows end 2026-11-13 unless stated. BH at q = 0.10 over {H3, H4a, H4b, H5a}.

## Hypotheses

| ID | Verdict | Key number | n | Raw p | BH p |
|---|---|---|---|---|---|
| **H1** | **Killed: "path driven"** (decision rule) | ACM: Δy10 +86.6, ΔRNY10 +89.0, ΔTP10 -2.4, share **-0.03**. KW: Δy10 +89.3, ΔRNY10 +47.8, ΔTP10 +41.5, share **0.47**. Both below 0.5. | 2 models | n/a | n/a |
| **H2** | **Prior only (N = 6 < 8)** | 2026 window TP share: ACM **0.10**, KW **0.46**. Lower than every reported prior-window share under both models (4 of 6 prior windows reported; 1997 and 2004 have abs(Δy10) < 25bp) | 6 prior + 2026 | n/a | n/a |
| **H3** | **Killed** | R² 2026 = **0.668** (β 0.73); 21 of 36 base years have R² ≤ 2026; 10th percentile of 1990-2025 = 0.429 | 218 days | 0.595 | **0.791** |
| **H4a** | **Killed** (t < 2; fails BH) | β = 16.4 bp ACM TP10 per unit Δln WTI, **t 1.47** | 46 weeks | 0.071 | **0.285** |
| **H4b** | **Killed** (t < 2; fails BH) | 2026 × Δln WTI interaction = -12.3, **t -0.81** (base slope 28.7) | 1,917 weeks (46 in 2026) | 0.791 | **0.791** |
| **H5a** | **Killed** (fails BH) | β = **0.042** bp ACM TP10 per bp ΔDGS2, sign positive, t 0.48, R² 0.002 | 255 days | 0.633 | **0.791** |
| **H5b** | **Prior only (N = 7 < 8)** | 2026 mean D1 share **0.487** vs 1994-2025 mean **0.525**; 3 of 7 days above the benchmark | 7 days (benchmark 255) | n/a | n/a |

**Survivors of BH: none.** All four tested claims are killed. Kill log: `out/killed_hypotheses.md`.

### H2 table (PRIOR ONLY, N = 6 < 8)

Window t0-126 to t0+41 trading days, on each model's own calendar. Share is ΔTP10 / Δy10, not reported if abs(Δy10) < 25bp (D2).

| Episode (t0) | Model | Start | End | y10 start (%) | TP10 start (%) | Δy10 | ΔRNY10 | ΔTP10 | Share |
|---|---|---|---|---|---|---|---|---|---|
| 1994-02-04 | ACM | 1993-07-30 | 1994-04-06 | 6.07 | 2.45 | +105.8 | +78.3 | +27.5 | 0.26 |
| 1997-03-25 | ACM | 1996-09-18 | 1997-05-22 | 6.87 | 1.85 | -9.9 | +5.8 | -15.7 | n/r |
| 1999-06-30 | ACM | 1998-12-28 | 1999-08-31 | 5.07 | 0.78 | +125.0 | +41.6 | +83.3 | 0.67 |
| 2004-06-30 | ACM | 2003-12-29 | 2004-08-27 | 4.52 | 2.32 | -3.2 | +43.3 | -46.4 | n/r |
| 2015-12-16 | ACM | 2015-06-16 | 2016-02-17 | 2.43 | 0.38 | -52.9 | +1.4 | -54.3 | 1.03 |
| 2022-03-16 | ACM | 2021-09-13 | 2022-05-13 | 1.37 | -0.51 | +164.5 | +134.8 | +29.7 | 0.18 |
| **2026-09-16** | **ACM** | 2026-03-18 | 2026-11-13 (t0+40) | 4.31 | 0.65 | **+80.5** | **+72.7** | **+7.8** | **0.10** |
| 1994-02-04 | KW | 1993-07-30 | 1994-04-06 | 6.09 | 1.64 | +106.1 | +56.5 | +49.6 | 0.47 |
| 1997-03-25 | KW | 1996-09-18 | 1997-05-22 | 6.87 | 1.72 | -10.9 | -7.2 | -3.6 | n/r |
| 1999-06-30 | KW | 1998-12-28 | 1999-08-31 | 5.10 | 0.88 | +117.8 | +61.5 | +56.3 | 0.48 |
| 2004-06-30 | KW | 2003-12-29 | 2004-08-27 | 4.52 | 1.18 | -3.8 | +8.2 | -12.0 | n/r |
| 2015-12-16 | KW | 2015-06-16 | 2016-02-17 | 2.53 | 0.35 | -61.3 | -24.4 | -36.8 | 0.60 |
| 2022-03-16 | KW | 2021-09-13 | 2022-05-13 | 1.45 | -0.22 | +153.3 | +78.6 | +74.7 | 0.49 |
| **2026-09-16** | **KW** | 2026-03-18 | 2026-11-13 (t0+40) | 4.32 | 0.61 | **+81.8** | **+44.5** | **+37.3** | **0.46** |

### H5b days (PRIOR ONLY, N = 7 < 8)

D1 share = abs(ΔTP10) / (abs(ΔTP10) + abs(ΔRNY10)), ACM. Benchmark: 1994-2025 mean = 0.525 (n = 255).

| Date | ΔDGS2 | ΔDGS10 | ΔACMY10 | ΔACMRNY10 | ΔACMTP10 | D1 share |
|---|---|---|---|---|---|---|
| 2026-01-28 | +3 | +2 | +2.6 | +0.3 | +2.3 | 0.88 |
| 2026-03-18 | +8 | +6 | +6.4 | +6.0 | +0.4 | 0.06 |
| 2026-04-29 | +8 | +6 | +6.5 | +5.0 | +1.5 | 0.23 |
| 2026-06-17 | +15 | +6 | +6.8 | +11.4 | -4.6 | 0.29 |
| 2026-07-29 | -4 | +6 | +7.0 | -5.4 | +12.4 | 0.70 |
| 2026-09-16 | +7 | +1 | +1.0 | +5.0 | -3.9 | 0.44 |
| 2026-10-28 | -3 | +6 | +6.5 | -2.0 | +8.5 | 0.81 |

## Robustness checks (reported, not in the FDR family)

1. **R1, Kim-Wright in place of ACM.** **H4a flips:** β 21.7, **t 3.22**, one-sided p 0.0006. **H4b does not flip:** interaction +10.4 (sign reverses from ACM's -12.3), t 1.29, p 0.098. **H5a flips:** β **0.325**, **t 12.9**, p 2.7e-38, R² 0.60. Under the CLAUDE.md rule, H4a and H5a hold under KW only and are **model-dependent**.
2. **R2, ΔDGS30 in place of ΔDGS10 (H3).** R² 2026 = 0.392; 16 of 36 base years ≤ 2026; p 0.459. **No flip.**
3. **R3, excluding 2020-03-01 to 2020-04-30 (H4).** H4a is unchanged (2026-only sample): t 1.47, p 0.071. H4b: interaction -20.3, t -1.38, p 0.916. **No flip.**
4. **R4, H1 with end date 2026-11-17 (ACM).** Δy10 +82.5, ΔTP10 -0.1, share -0.001. **No flip** (still below 0.5).
5. **R5, real vs breakeven split of ΔDGS10 over the H1 window.** ΔDGS10 **+97** = ΔDFII10 **+98** + ΔT10YIE **-1**; residual **0.0** (see data notes: in this data T10YIE equals DGS10 - DFII10 on every date).

## Model disagreement (ACM vs Kim-Wright)

- **H1 window:** ΔTP10 differs by **44bp** (ACM -2.4, KW +41.5) and ΔRNY10 by **41bp** (ACM +89.0, KW +47.8), for nearly the same Δy10 (+86.6 vs +89.3). Both shares fall below 0.5, but ACM by 0.53 and KW by 0.03.
- **Level gap, ACM TP10 minus KW TP10:** +17.7bp on 2025-12-31, **-26.2bp** on 2026-11-13. Over 1990-2026: mean +24bp, mean absolute 57bp, range -128bp (2022-04-01) to +236bp (2008-11-03). (E9)
- **Daily ΔTP10 correlation:** 0.63 over 1990-2026, 0.61 in 2026. In 2026 the daily standard deviation is 3.85bp for ACM and 1.94bp for KW.
- **FOMC days:** H5a slope 0.04 (ACM) vs 0.33 (KW).
- **Oil:** 2026 weekly oil slope t 1.47 (ACM) vs 3.22 (KW).
- **Current level percentiles (1990-2026 daily):** ACM TP10 0.75% on 2026-11-17, **44th** percentile; KW TP10 0.99% on 2026-11-13, **62nd** percentile. (E10)

## Data notes and logged issues

- **No WTI weeks dropped.** The only negative WTI print (-36.98 on Monday 2020-04-20) is not a week-end value. The week ending 2020-04-24 uses 15.99, so no weekly value is ≤ 0.
- **2026 hike window truncated** to t0+40 (2026-11-13) under both models. Its 41st trading day after 2026-09-16 falls after the common end date.
- **T10YIE = DGS10 - DFII10 exactly** in this data (max absolute residual 9e-16 over 5,973 dates). The R5 residual is therefore zero by construction.
- **DGS30, 2002-02-19 to 2006-02-08:** the file has values throughout, with level jumps at both ends (+17bp on 2002-02-19, -16bp on 2006-02-09). This is believed (not verified) to be the period when Treasury did not issue the 30-year, with FRED carrying an estimated series. It affects R2 only, and no year fell below the 100-day minimum used in R2.
- **H3 decision rule:** the rank rule (p ≤ 0.10) and the PREREG's wording ("below the 10th percentile of 1990-2025") agree for both H3 and R2. The edge case where they could differ (3 base years at or below 2026) did not arise.
- **No announcement days lost:** all 255 scheduled announcement days from 1994-02-04 to 2025-12-31, and all 7 in 2026, have every series on t and on its previous published date.
- `src/live_p1.py` is written but not run. It needs a data refresh that includes 2026-12-09.

## Exhibits (`out/exhibits/`, PNG plus CSV)

E1 decomposition 1990-2026; E2 H1 attribution; E3 hike-window paths; E4 yearly R²; E5 rolling oil β; E6 FOMC-day scatter; E7 real vs breakeven 2026; E8 2026 timeline; E9 ACM minus KW TP10; E10 current TP percentile.
