# Bandwidth and false discovery in conditional stock-return densities

**Date:** 16 Nov 2026

## Problem

Pattern-finding on stock data is effectively an under-smoothed density estimate, so it turns noise into peaks that look like tradable edges.

## Question

How much of the "edge" found in conditional stock-return densities comes from the bandwidth choice rather than real predictability?

## Hypotheses

- H1: On placebo data, the share of bandwidths that "find" an in-sample edge (t > 3) rises sharply as the bandwidth shrinks below the cross-validated bandwidth.
- H2: On real data, any edge found at small bandwidths does not survive out of sample; at the cross-validated bandwidth, out-of-sample t is below 3 after costs.

## Data

- Universe: current S&P 500 constituents plus SPY. Survivorship bias is a known limitation (delisted names are missing).
- Development sample: 2000-01-01 to 2025-12-31.
- Holdout: 2026-01-01 onward. Locked. Not loaded, plotted or summarised until the method is final and Nigel signs off.

## Variables (computed in a later session)

- Signal x: overnight gap, ln(Open_t / Close_{t-1}).
- Target y: forward 5-day log return, Close_t to Close_{t+5}, minus the equal-weight universe mean on the same dates.
- Both are rank-transformed to normal scores within each date before KDE.

## Method

- 2D Gaussian KDE of (x, y); conditional mean E[y | x] taken from the KDE.
- Bandwidth grid: {0.25, 0.5, 0.75, 1, 1.5, 2, 4} x the leave-one-out likelihood cross-validated bandwidth.
- "Pattern hunter" test: in-sample, find the x-interval (minimum 5% of observations) with the highest conditional mean; trade it long-short against the rest; record its t-stat.
- Walk-forward test: fit on a rolling 5-year window, trade the following year, repeated 2005 to 2025.
- Costs: 10bp per side.
- Edge bar: t > 3 (Harvey-Liu-Zhu), Newey-West standard errors with 5 lags.

## Placebo

- Shuffle y across stocks within each date (no true edge can exist). 500 runs, seed 7.
- False-discovery rate = share of placebo runs where the pattern-hunter t > 3, reported per bandwidth.

## Number of trials

1 signal x 7 bandwidths x 2 tests, plus 500 placebo runs per bandwidth. Every run is logged.

## Prior pilot

16 Nov 2026, Nasdaq 100, 1-day density forecasts, n = 1,478: changing the bandwidth moved forecast quality about 20x more than changing the kernel; 0.5x Silverman was the worst KDE.

## Deviations (16 Nov 2026, before any real-data results)

**Reason.** Synthetic tests (`tests/test_synthetic.py`, commit `0a3005a`, results in `out/runs.csv` and `out/synthetic_null.png`) showed that the 5% minimum pocket dominates the bandwidth effect: on null data the share of pattern-hunter t > 3 was 0-2% at every bandwidth multiple from 0.25x to 4x. With a 5% minimum the design cannot show whether under-smoothing creates false discoveries. No real stock data had been used for any computation when this deviation was written.

**Changes.**
- Minimum pocket size becomes a design factor: {0.5%, 1%, 2%, 5%}, crossed with the bandwidth grid {0.25, 0.5, 0.75, 1, 1.5, 2, 4} x the LCV bandwidth (28 cells).
- Pocket search resolution: n_bins = max(200, 4 / min_frac) equal-count bins (800, 400, 200, 200 for 0.5%, 1%, 2%, 5%).
- Report the share of t > 2 as well as t > 3 in every cell.
- Null replications: 500 per cell.

**Consequence for the trial count (derived from the changes above).** 1 signal x 7 bandwidths x 4 pocket sizes x 2 tests = 56 trials, plus 500 null runs per cell (28 cells, 14,000 runs). Every run is logged.

**Implementation notes (numerical, not design).**
- For the grid runs, E[y | x] is computed by `kde.cond_mean_binned` (linear binning onto 4,096 nodes, direct convolution with the Gaussian kernel truncated at 8h) and evaluated at every observation. On a synthetic check against the exact `kde.cond_mean` (n = 50,000; 1,000 evaluation points including both tails) the largest absolute difference was 7.6e-5 at h = 0.06 and below 5e-6 at h >= 0.24.
- Periods with no observation inside the pocket (or none outside) are dropped from the long-short series. With small pockets and few names per period this removes many periods; the number of periods used is recorded per run.
