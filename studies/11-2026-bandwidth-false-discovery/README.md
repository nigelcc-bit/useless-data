# Bandwidth and false discovery in conditional stock-return densities

**Problem.** Pattern-finding on stock data is an under-smoothed density estimate, so it can turn noise into peaks that look like tradable edges.
**Question.** How much of the "edge" in conditional stock-return densities comes from the bandwidth choice rather than real predictability?
**Method.** 2D Gaussian KDE of the overnight gap vs the 5-day market-relative return (S&P 500, within-date normal scores), bandwidth 0.25x-4x the LCV bandwidth crossed with minimum pocket 0.5%-5% (28 cells), tested in-sample, walk-forward 2005-2025 and on a 2026 holdout against within-date placebos ([PREREG.md](PREREG.md), including Deviations).

## Answer

- **In-sample, a smaller bandwidth manufactures edges on noise (H1 supported).** On the within-date placebo, the share of pattern-hunter t > 3 rises from 0.2-0.6% at 4x to 4.8-6.4% at 0.25x (t > 2: about 5% to 37-54%). The real data never cleared t > 3 (max 2.86, at 0.25x, placebo p 0.10); no cell had placebo p below 0.05.
- **Walk-forward 2005-2025, net of 10bp per side, nothing survives (H2 supported).** All 28 cells lose money: -3% to -9% a year, net t -1.0 to -7.2. Turnover of about 0.40 a day costs about 10% a year.
- **Walk-forward gross: a small real signal, stronger at wider bandwidths.** Gross t is 0.4-2.9 (none above 3) on +1% to +7% a year; 12 of 28 cells beat all or nearly all of 50 placebos (gross p ≤ 0.05, unadjusted). Gross t rises with the bandwidth multiple (Spearman 0.63): the under-smoothed cells did worst out of sample. The pockets chosen are almost always the large gap-down tail (short-term reversal).

## Holdout 2026 (single run, 2 Jan to 13 Nov 2026, 219 trading days)

- Trained on 2021-2025 with frozen pockets: gross t 0.73-2.44 in all 28 cells (none above 3; 1x cells 1.14-1.57). Net returns were positive in every cell (+7% to +40% annualised, net t 0.30-1.95). The 28 cells use only 12 distinct pockets, so this is close to one bet on gap-down reversal in a favourable year, and not significant.
- Spearman of bandwidth multiple vs gross t: 0.32 in the holdout vs 0.63 in the walk-forward; same sign, weaker.

## Key charts

- [out/synthetic_null_grid.png](out/synthetic_null_grid.png): synthetic null, false-discovery rate by bandwidth x pocket size.
- [out/real_vs_placebo.png](out/real_vs_placebo.png): in-sample real t and placebo p by cell.
- [out/wf_cumulative.png](out/wf_cumulative.png): walk-forward cumulative net return vs placebo 5th-95th band.

## Limitations

- **Survivorship:** universe is the 16 Nov 2026 constituents; delisted and removed names are missing. This likely flatters a gap-down reversal strategy (names that gapped down and kept falling are more likely to have left the index).
- **Placebo depth:** 50 walk-forward placebo reps, so the smallest empirical p is 1/51 = 0.02; 500 reps in-sample.
- **Multiple testing:** 28 cells (highly overlapping) in each test; no FDR adjustment applied to the numbers above.
- **One signal** (overnight gap), one horizon (5 days), one cost assumption (10bp per side, no market impact or borrow).
- **2026 holdout** is about 10 months (219 days), one regime.

All runs, including killed results, are logged in [out/runs.csv](out/runs.csv).

**Status: complete.**
