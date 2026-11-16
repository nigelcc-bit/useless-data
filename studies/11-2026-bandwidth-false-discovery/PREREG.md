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
