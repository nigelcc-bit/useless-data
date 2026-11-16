# Study D results

Pre-registered primary panel (all 12 markets). N225 later flagged by
`validate()` (20-day flat run) after these results were viewed — see
`sensitivity_no_n225.md` (SENSITIVITY; not a primary result).

Markets: SPX, NDX, RUT, DAX, CAC, FTSE, STOXX50, N225, HSI, KOSPI, ASX200, TSX

## Per market

| market | start | breaks | reclaim_rate | retest_rate | x60 | x120 | n120 |
|---|---|---|---|---|---|---|---|
| SPX | 1950-07-13 | 86 | 0.779 | 0.791 | 0.001 | 0.002 | 67 |
| NDX | 1986-09-11 | 43 | 0.860 | 0.722 | -0.005 | 0.016 | 36 |
| RUT | 1989-12-18 | 44 | 0.705 | 0.667 | 0.027 | 0.019 | 30 |
| DAX | 1990-08-06 | 40 | 0.725 | 0.586 | -0.027 | -0.010 | 29 |
| CAC | 1990-09-20 | 53 | 0.811 | 0.651 | 0.009 | 0.005 | 43 |
| FTSE | 1984-07-10 | 52 | 0.750 | 0.436 | 0.020 | 0.024 | 39 |
| STOXX50 | 2008-01-18 | 26 | 0.769 | 0.700 | 0.001 | -0.003 | 20 |
| N225 | 1965-07-05 | 78 | 0.821 | 0.667 | 0.012 | -0.010 | 63 |
| HSI | 1987-10-26 | 50 | 0.720 | 0.694 | -0.010 | -0.012 | 35 |
| KOSPI | 1997-09-25 | 44 | 0.591 | 0.720 | 0.032 | 0.021 | 25 |
| ASX200 | 1994-05-05 | 45 | 0.733 | 0.727 | 0.006 | 0.001 | 33 |
| TSX | 1981-02-19 | 58 | 0.724 | 0.643 | 0.003 | 0.016 | 42 |

## Pooled (primary tests: mean excess r60 and r120, alpha = 0.025 each)

| sample | stat | n | clusters_month | estimate | ci_lo | ci_hi | p_placebo | ci_lo_quarter | ci_hi_quarter | clusters_quarter |
|---|---|---|---|---|---|---|---|---|---|---|
| primary | reclaim_rate | 619 | 250 | 0.754 | 0.713 | 0.797 |  |  |  |  |
| primary | retest_rate | 463 | 216 | 0.672 | 0.616 | 0.728 |  |  |  |  |
| primary | mean excess r20 | 465 | 217 | -0.001 | -0.014 | 0.011 | 0.610 | -0.013 | 0.011 | 144.000 |
| primary | mean excess r60 | 463 | 216 | 0.006 | -0.012 | 0.022 | 0.115 | -0.016 | 0.026 | 143.000 |
| primary | mean excess r120 | 462 | 215 | 0.005 | -0.020 | 0.028 | 0.245 | -0.026 | 0.036 | 142.000 |

## Analogs: reclaimed while 10-20% below the 120-day high

| sample | outcome | n | clusters_month | share | wilson_lo | wilson_hi | cluster_ci_lo | cluster_ci_hi |
|---|---|---|---|---|---|---|---|---|
| primary | regained_high | 240 | 139 | 0.329 | 0.273 | 0.391 | 0.258 | 0.402 |
| primary | dd20 | 240 | 139 | 0.475 | 0.413 | 0.538 | 0.393 | 0.559 |
| primary | retest | 241 | 140 | 0.693 | 0.632 | 0.748 | 0.617 | 0.765 |

## Secondary universe (descriptive only)

| market | start | breaks | reclaim_rate | retest_rate | x60 | x120 | n120 |
|---|---|---|---|---|---|---|---|
| DJI | 1992-10-02 | 32 | 0.812 | 0.577 | -0.005 | -0.018 | 26 |
| XLB | 2000-02-09 | 33 | 0.727 | 0.696 | -0.021 | 0.001 | 23 |
| XLE | 1999-10-08 | 33 | 0.727 | 0.625 | 0.014 | 0.023 | 24 |
| XLF | 1999-08-06 | 37 | 0.784 | 0.655 | -0.023 | -0.026 | 29 |
| XLI | 1999-10-14 | 31 | 0.710 | 0.762 | -0.022 | 0.010 | 21 |
| XLK | 2000-05-23 | 33 | 0.697 | 0.864 | -0.025 | -0.042 | 22 |
| XLP | 1999-08-04 | 30 | 0.767 | 0.682 | -0.012 | -0.010 | 22 |
| XLU | 1999-10-15 | 27 | 0.741 | 0.684 | -0.011 | -0.020 | 19 |
| XLV | 1999-08-10 | 35 | 0.886 | 0.548 | 0.021 | 0.022 | 31 |
| XLY | 1999-08-04 | 33 | 0.818 | 0.778 | 0.027 | 0.007 | 27 |
| GOLD | 2006-10-04 | 25 | 0.600 | 0.500 | 0.034 | 0.040 | 12 |
| BTC | 2015-08-18 | 23 | 0.652 | 0.867 | 0.026 | 0.004 | 15 |

| sample | stat | n | clusters_month | estimate | ci_lo | ci_hi | p_placebo | ci_lo_quarter | ci_hi_quarter | clusters_quarter |
|---|---|---|---|---|---|---|---|---|---|---|
| secondary | reclaim_rate | 372 | 146 | 0.750 | 0.699 | 0.801 |  |  |  |  |
| secondary | retest_rate | 273 | 124 | 0.681 | 0.610 | 0.751 |  |  |  |  |
| secondary | mean excess r20 | 277 | 126 | -0.000 | -0.016 | 0.015 | 0.500 | -0.017 | 0.016 | 74.000 |
| secondary | mean excess r60 | 273 | 124 | -0.001 | -0.022 | 0.020 | 0.522 | -0.027 | 0.024 | 74.000 |
| secondary | mean excess r120 | 271 | 123 | -0.002 | -0.033 | 0.027 | 0.552 | -0.040 | 0.034 | 73.000 |
