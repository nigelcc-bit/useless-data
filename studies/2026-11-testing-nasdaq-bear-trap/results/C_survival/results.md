# Study C results

## Kaplan-Meier: P(event by day 60 | none by day d)

| index | event | days_survived | S | p_event_by_h_given_none_yet | logrank_p_vs_null | null_p_event_by_60_given_none_yet |
|---|---|---|---|---|---|---|
| NDX | retest of sweep low | 0 | 1.000 | 0.722 | 0.364 | 0.650 |
| NDX | retest of sweep low | 5 | 0.583 | 0.524 | 0.364 | 0.467 |
| NDX | retest of sweep low | 10 | 0.500 | 0.444 | 0.364 | 0.368 |
| NDX | retest of sweep low | 20 | 0.417 | 0.333 | 0.364 | 0.255 |
| NDX | retest of sweep low | 30 | 0.389 | 0.286 | 0.364 | 0.173 |
| NDX | retest of sweep low | 40 | 0.306 | 0.091 | 0.364 | 0.095 |
| NDX | regain 120d high | 0 | 1.000 | 0.222 | 0.166 | 0.201 |
| NDX | regain 120d high | 5 | 1.000 | 0.222 | 0.166 | 0.197 |
| NDX | regain 120d high | 10 | 1.000 | 0.222 | 0.166 | 0.187 |
| NDX | regain 120d high | 20 | 0.944 | 0.176 | 0.166 | 0.158 |
| NDX | regain 120d high | 30 | 0.889 | 0.125 | 0.166 | 0.122 |
| NDX | regain 120d high | 40 | 0.889 | 0.125 | 0.166 | 0.083 |
| SPX | retest of sweep low | 0 | 1.000 | 0.791 | 0.001 | 0.638 |
| SPX | retest of sweep low | 5 | 0.582 | 0.641 | 0.001 | 0.473 |
| SPX | retest of sweep low | 10 | 0.388 | 0.462 | 0.001 | 0.380 |
| SPX | retest of sweep low | 20 | 0.313 | 0.333 | 0.001 | 0.261 |
| SPX | retest of sweep low | 30 | 0.269 | 0.222 | 0.001 | 0.175 |
| SPX | retest of sweep low | 40 | 0.254 | 0.176 | 0.001 | 0.108 |
| SPX | regain 120d high | 0 | 1.000 | 0.164 | 0.372 | 0.198 |
| SPX | regain 120d high | 5 | 1.000 | 0.164 | 0.372 | 0.191 |
| SPX | regain 120d high | 10 | 0.970 | 0.138 | 0.372 | 0.182 |
| SPX | regain 120d high | 20 | 0.955 | 0.125 | 0.372 | 0.156 |
| SPX | regain 120d high | 30 | 0.940 | 0.111 | 0.372 | 0.124 |
| SPX | regain 120d high | 40 | 0.925 | 0.097 | 0.372 | 0.087 |

## Cox proportional hazards (pooled, stratified by index, SEs clustered by year)

**retest** (n = 103, concordance 0.619, PH assumption not rejected)

| event | covariate (per 1 sd) | hazard_ratio | hr_lo | hr_hi | p |
|---|---|---|---|---|---|
| retest | sweep_depth | 0.824 | 0.678 | 1.000 | 0.050 |
| retest | dd_abs | 0.951 | 0.665 | 1.362 | 0.786 |
| retest | rv20 | 1.245 | 0.882 | 1.757 | 0.213 |

**high** (n = 103, concordance 0.713, PH assumption not rejected)

| event | covariate (per 1 sd) | hazard_ratio | hr_lo | hr_hi | p |
|---|---|---|---|---|---|
| high | sweep_depth | 0.811 | 0.599 | 1.097 | 0.174 |
| high | dd_abs | 0.410 | 0.302 | 0.558 | 0.000 |
| high | rv20 | 1.339 | 0.861 | 2.083 | 0.195 |

## Live event

| idx | break_date | reclaim_date | sweep_low | level | high_120 | last_date | days_since_reclaim | retested | regained_high | sweep_depth | dd_abs | rv20 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NDX | 2026-11-05 00:00:00 | 2026-11-09 00:00:00 | 26629.811 | 27192.311 | 31224.471 | 2026-11-11 00:00:00 | 2 | False | False | 0.021 | 0.147 | 0.318 |

| index | outcome | status | km_conditional | cox_conditional |
|---|---|---|---|---|
| NDX | retest of sweep low by day 60 | not yet, 2 trading days after reclaim | 0.643 | 0.653 |
| NDX | regain 120d high by day 60 | not yet, 2 trading days after reclaim | 0.222 | 0.316 |
