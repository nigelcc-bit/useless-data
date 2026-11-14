# Study C results

## Kaplan-Meier: P(event by day 60 | none by day d)

| index | event | days_survived | S | p_event_by_h_given_none_yet | logrank_p_vs_null | null_p_event_by_60_given_none_yet |
|---|---|---|---|---|---|---|
| NDX | retest of sweep low | 0 | 1.000 | 0.722 | 0.452 | 0.667 |
| NDX | retest of sweep low | 5 | 0.583 | 0.524 | 0.452 | 0.488 |
| NDX | retest of sweep low | 10 | 0.500 | 0.444 | 0.452 | 0.385 |
| NDX | retest of sweep low | 20 | 0.417 | 0.333 | 0.452 | 0.266 |
| NDX | retest of sweep low | 30 | 0.389 | 0.286 | 0.452 | 0.190 |
| NDX | retest of sweep low | 40 | 0.306 | 0.091 | 0.452 | 0.110 |
| NDX | regain 120d high | 0 | 1.000 | 0.222 | 0.132 | 0.194 |
| NDX | regain 120d high | 5 | 1.000 | 0.222 | 0.132 | 0.190 |
| NDX | regain 120d high | 10 | 1.000 | 0.222 | 0.132 | 0.179 |
| NDX | regain 120d high | 20 | 0.944 | 0.176 | 0.132 | 0.152 |
| NDX | regain 120d high | 30 | 0.889 | 0.125 | 0.132 | 0.117 |
| NDX | regain 120d high | 40 | 0.889 | 0.125 | 0.132 | 0.083 |
| SPX | retest of sweep low | 0 | 1.000 | 0.790 | 0.003 | 0.653 |
| SPX | retest of sweep low | 5 | 0.642 | 0.673 | 0.003 | 0.499 |
| SPX | retest of sweep low | 10 | 0.444 | 0.528 | 0.003 | 0.405 |
| SPX | retest of sweep low | 20 | 0.358 | 0.414 | 0.003 | 0.283 |
| SPX | retest of sweep low | 30 | 0.296 | 0.292 | 0.003 | 0.193 |
| SPX | retest of sweep low | 40 | 0.247 | 0.150 | 0.003 | 0.117 |
| SPX | regain 120d high | 0 | 1.000 | 0.148 | 0.531 | 0.182 |
| SPX | regain 120d high | 5 | 1.000 | 0.148 | 0.531 | 0.174 |
| SPX | regain 120d high | 10 | 0.975 | 0.127 | 0.531 | 0.163 |
| SPX | regain 120d high | 20 | 0.963 | 0.115 | 0.531 | 0.134 |
| SPX | regain 120d high | 30 | 0.951 | 0.104 | 0.531 | 0.105 |
| SPX | regain 120d high | 40 | 0.926 | 0.080 | 0.531 | 0.071 |

## Cox proportional hazards (pooled, stratified by index, SEs clustered by year)

**retest** (n = 117, concordance 0.601, PH assumption REJECTED: report KM only)

| event | covariate (per 1 sd) | hazard_ratio | hr_lo | hr_hi | p |
|---|---|---|---|---|---|
| retest | sweep_depth | 0.870 | 0.735 | 1.029 | 0.105 |
| retest | dd_abs | 0.857 | 0.645 | 1.138 | 0.285 |
| retest | rv20 | 1.255 | 0.913 | 1.724 | 0.162 |

**high** (n = 117, concordance 0.715, PH assumption not rejected)

| event | covariate (per 1 sd) | hazard_ratio | hr_lo | hr_hi | p |
|---|---|---|---|---|---|
| high | sweep_depth | 0.834 | 0.627 | 1.109 | 0.212 |
| high | dd_abs | 0.416 | 0.312 | 0.553 | 0.000 |
| high | rv20 | 1.173 | 0.744 | 1.849 | 0.492 |

## Live event

| idx | break_date | reclaim_date | sweep_low | level | high_120 | last_date | days_since_reclaim | retested | regained_high | sweep_depth | dd_abs | rv20 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NDX | 2026-11-05 00:00:00 | 2026-11-09 00:00:00 | 26629.811 | 27192.311 | 31224.471 | 2026-11-13 00:00:00 | 4 | False | False | 0.021 | 0.147 | 0.318 |

| index | outcome | status | km_conditional | cox_conditional |
|---|---|---|---|---|
| NDX | retest of sweep low by day 60 | not yet, 4 trading days after reclaim | 0.565 | 0.592 |
| NDX | regain 120d high by day 60 | not yet, 4 trading days after reclaim | 0.222 | 0.305 |
