# Study A results

Paths per model: 500. Seed 7. Sample end 2026-11-09.

## Primary tests (block null, 4 tests, Bonferroni alpha = 0.0125)

| index | metric | observed | null_mean | null_lo | null_hi | p | bonferroni_sig |
|---|---|---|---|---|---|---|---|
| NDX | reclaim_rate | 0.860 | 0.792 | 0.658 | 0.911 | 0.283 | False |
| NDX | retest_rate | 0.722 | 0.648 | 0.459 | 0.807 | 0.399 | False |
| SPX | reclaim_rate | 0.779 | 0.748 | 0.643 | 0.840 | 0.487 | False |
| SPX | retest_rate | 0.791 | 0.637 | 0.509 | 0.750 | 0.004 | True |

## All models, swing-low level

| index | model | metric | observed | null_mean | null_lo | null_hi | excess | p |
|---|---|---|---|---|---|---|---|---|
| NDX | block | reclaim_rate | 0.860 | 0.792 | 0.658 | 0.911 | 0.069 | 0.283 |
| NDX | block | retest_rate | 0.722 | 0.648 | 0.459 | 0.807 | 0.074 | 0.399 |
| NDX | block | breaks_per_year | 1.046 | 1.099 | 0.741 | 1.472 | -0.054 | 0.846 |
| NDX | block | deep_share | 0.432 | 0.480 | 0.314 | 0.650 | -0.048 | 0.583 |
| NDX | garch | reclaim_rate | 0.860 | 0.762 | 0.586 | 0.936 | 0.098 | 0.279 |
| NDX | garch | retest_rate | 0.722 | 0.626 | 0.389 | 0.820 | 0.097 | 0.391 |
| NDX | garch | breaks_per_year | 1.046 | 0.633 | 0.365 | 0.924 | 0.413 | 0.016 |
| NDX | garch | deep_share | 0.432 | 0.453 | 0.216 | 0.696 | -0.020 | 0.886 |
| NDX | gbm | reclaim_rate | 0.860 | 0.735 | 0.628 | 0.837 | 0.125 | 0.020 |
| NDX | gbm | retest_rate | 0.722 | 0.710 | 0.560 | 0.835 | 0.012 | 0.934 |
| NDX | gbm | breaks_per_year | 1.046 | 1.349 | 0.973 | 1.776 | -0.303 | 0.176 |
| NDX | gbm | deep_share | 0.432 | 0.406 | 0.250 | 0.566 | 0.026 | 0.731 |
| NDX | iid | reclaim_rate | 0.860 | 0.680 | 0.557 | 0.804 | 0.180 | 0.008 |
| NDX | iid | retest_rate | 0.722 | 0.694 | 0.533 | 0.833 | 0.029 | 0.747 |
| NDX | iid | breaks_per_year | 1.046 | 1.346 | 0.936 | 1.776 | -0.300 | 0.176 |
| NDX | iid | deep_share | 0.432 | 0.385 | 0.226 | 0.541 | 0.047 | 0.587 |
| NDX | msvol | reclaim_rate | 0.860 | 0.695 | 0.559 | 0.815 | 0.166 | 0.008 |
| NDX | msvol | retest_rate | 0.722 | 0.700 | 0.536 | 0.846 | 0.022 | 0.866 |
| NDX | msvol | breaks_per_year | 1.046 | 1.128 | 0.778 | 1.557 | -0.082 | 0.794 |
| NDX | msvol | deep_share | 0.432 | 0.459 | 0.293 | 0.643 | -0.027 | 0.774 |
| SPX | block | reclaim_rate | 0.779 | 0.748 | 0.643 | 0.840 | 0.031 | 0.487 |
| SPX | block | retest_rate | 0.791 | 0.637 | 0.509 | 0.750 | 0.154 | 0.004 |
| SPX | block | breaks_per_year | 1.121 | 1.153 | 0.899 | 1.401 | -0.032 | 0.854 |
| SPX | block | deep_share | 0.343 | 0.320 | 0.204 | 0.434 | 0.024 | 0.723 |
| SPX | garch | reclaim_rate | 0.779 | 0.751 | 0.636 | 0.858 | 0.028 | 0.631 |
| SPX | garch | retest_rate | 0.791 | 0.641 | 0.487 | 0.775 | 0.150 | 0.036 |
| SPX | garch | breaks_per_year | 1.121 | 0.746 | 0.527 | 0.977 | 0.375 | 0.004 |
| SPX | garch | deep_share | 0.343 | 0.270 | 0.134 | 0.417 | 0.073 | 0.315 |
| SPX | gbm | reclaim_rate | 0.779 | 0.730 | 0.647 | 0.812 | 0.049 | 0.244 |
| SPX | gbm | retest_rate | 0.791 | 0.716 | 0.611 | 0.806 | 0.075 | 0.140 |
| SPX | gbm | breaks_per_year | 1.121 | 1.367 | 1.056 | 1.668 | -0.246 | 0.112 |
| SPX | gbm | deep_share | 0.343 | 0.228 | 0.141 | 0.322 | 0.115 | 0.012 |
| SPX | iid | reclaim_rate | 0.779 | 0.670 | 0.571 | 0.770 | 0.109 | 0.036 |
| SPX | iid | retest_rate | 0.791 | 0.692 | 0.576 | 0.802 | 0.099 | 0.068 |
| SPX | iid | breaks_per_year | 1.121 | 1.333 | 1.030 | 1.617 | -0.212 | 0.180 |
| SPX | iid | deep_share | 0.343 | 0.208 | 0.121 | 0.307 | 0.135 | 0.020 |
| SPX | msvol | reclaim_rate | 0.779 | 0.697 | 0.602 | 0.792 | 0.082 | 0.088 |
| SPX | msvol | retest_rate | 0.791 | 0.686 | 0.560 | 0.794 | 0.105 | 0.076 |
| SPX | msvol | breaks_per_year | 1.121 | 1.170 | 0.912 | 1.473 | -0.049 | 0.838 |
| SPX | msvol | deep_share | 0.343 | 0.275 | 0.167 | 0.385 | 0.068 | 0.267 |

## Pseudo-level difference-in-differences (secondary)

| index | pseudo_level | metric | observed_diff | null_diff_mean | p |
|---|---|---|---|---|---|
| NDX | q05 | reclaim_rate | 0.114 | 0.038 | 0.259 |
| NDX | q05 | retest_rate | 0.062 | -0.002 | 0.459 |
| NDX | q10 | reclaim_rate | 0.194 | 0.038 | 0.024 |
| NDX | q10 | retest_rate | 0.070 | -0.017 | 0.383 |
| NDX | q20 | reclaim_rate | 0.094 | 0.030 | 0.375 |
| NDX | q20 | retest_rate | 0.102 | -0.018 | 0.228 |
| SPX | q05 | reclaim_rate | 0.093 | 0.015 | 0.124 |
| SPX | q05 | retest_rate | 0.107 | -0.005 | 0.076 |
| SPX | q10 | reclaim_rate | 0.101 | 0.019 | 0.128 |
| SPX | q10 | retest_rate | 0.115 | -0.017 | 0.036 |
| SPX | q20 | reclaim_rate | 0.101 | 0.020 | 0.164 |
| SPX | q20 | retest_rate | 0.104 | -0.023 | 0.048 |
