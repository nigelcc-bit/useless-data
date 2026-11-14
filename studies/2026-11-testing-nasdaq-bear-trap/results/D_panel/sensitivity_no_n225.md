# SENSITIVITY: Study D excluding N225

N225 flagged by `validate()` (longest_flat_run = 20) in Yahoo data after the
pre-registered primary D results were viewed. Primary D (all 12 markets) is
unchanged; this run drops N225 only.

Markets: SPX, NDX, RUT, DAX, CAC, FTSE, STOXX50, HSI, KOSPI, ASX200, TSX

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
| HSI | 1987-10-26 | 50 | 0.720 | 0.694 | -0.010 | -0.012 | 35 |
| KOSPI | 1997-09-25 | 44 | 0.591 | 0.720 | 0.032 | 0.021 | 25 |
| ASX200 | 1994-05-05 | 45 | 0.733 | 0.727 | 0.006 | 0.001 | 33 |
| TSX | 1981-02-19 | 58 | 0.724 | 0.643 | 0.003 | 0.016 | 42 |

## Pooled

| sample | stat | n | clusters_month | estimate | ci_lo | ci_hi | p_placebo | ci_lo_quarter | ci_hi_quarter | clusters_quarter |
|---|---|---|---|---|---|---|---|---|---|---|
| primary_no_n225 | reclaim_rate | 541 | 217 | 0.745 | 0.697 | 0.792 |  |  |  |  |
| primary_no_n225 | retest_rate | 400 | 188 | 0.672 | 0.612 | 0.734 |  |  |  |  |
| primary_no_n225 | mean excess r20 | 402 | 189 | -0.001 | -0.016 | 0.012 | 0.608 | -0.015 | 0.012 | 129.000 |
| primary_no_n225 | mean excess r60 | 400 | 188 | 0.005 | -0.016 | 0.023 | 0.166 | -0.019 | 0.027 | 128.000 |
| primary_no_n225 | mean excess r120 | 399 | 187 | 0.007 | -0.020 | 0.033 | 0.169 | -0.029 | 0.042 | 127.000 |

## Analogs: reclaimed while 10-20% below the 120-day high

| sample | outcome | n | clusters_month | share | wilson_lo | wilson_hi | cluster_ci_lo | cluster_ci_hi |
|---|---|---|---|---|---|---|---|---|
| primary_no_n225 | regained_high | 202 | 118 | 0.337 | 0.275 | 0.404 | 0.259 | 0.418 |
| primary_no_n225 | dd20 | 202 | 118 | 0.465 | 0.398 | 0.534 | 0.372 | 0.558 |
| primary_no_n225 | retest | 203 | 119 | 0.695 | 0.628 | 0.754 | 0.612 | 0.774 |
