# Study A results

Paths per model: 500. Seed 7. Sample end 2026-11-09.

## Primary tests (block null, 4 tests, Bonferroni alpha = 0.0125)

| index | metric | observed | null_mean | null_lo | null_hi | p | bonferroni_sig |
|---|---|---|---|---|---|---|---|
| NDX | reclaim_rate | 0.860 | 0.792 | 0.664 | 0.902 | 0.271 | False |
| NDX | retest_rate | 0.722 | 0.663 | 0.488 | 0.814 | 0.483 | False |
| SPX | reclaim_rate | 0.692 | 0.723 | 0.649 | 0.798 | 0.459 | False |
| SPX | retest_rate | 0.790 | 0.655 | 0.560 | 0.747 | 0.004 | True |

## All models, swing-low level

| index | model | metric | observed | null_mean | null_lo | null_hi | excess | p |
|---|---|---|---|---|---|---|---|---|
| NDX | block | reclaim_rate | 0.860 | 0.792 | 0.664 | 0.902 | 0.068 | 0.271 |
| NDX | block | retest_rate | 0.722 | 0.663 | 0.488 | 0.814 | 0.059 | 0.483 |
| NDX | block | breaks_per_year | 1.046 | 1.107 | 0.803 | 1.497 | -0.061 | 0.834 |
| NDX | block | deep_share | 0.432 | 0.476 | 0.323 | 0.638 | -0.043 | 0.595 |
| NDX | garch | reclaim_rate | 0.860 | 0.761 | 0.583 | 0.932 | 0.100 | 0.267 |
| NDX | garch | retest_rate | 0.722 | 0.630 | 0.387 | 0.818 | 0.093 | 0.423 |
| NDX | garch | breaks_per_year | 1.046 | 0.632 | 0.341 | 0.925 | 0.414 | 0.012 |
| NDX | garch | deep_share | 0.432 | 0.450 | 0.218 | 0.682 | -0.017 | 0.914 |
| NDX | gbm | reclaim_rate | 0.860 | 0.736 | 0.628 | 0.839 | 0.125 | 0.016 |
| NDX | gbm | retest_rate | 0.722 | 0.710 | 0.561 | 0.833 | 0.012 | 0.882 |
| NDX | gbm | breaks_per_year | 1.046 | 1.350 | 0.960 | 1.776 | -0.304 | 0.196 |
| NDX | gbm | deep_share | 0.432 | 0.407 | 0.250 | 0.571 | 0.026 | 0.727 |
| NDX | iid | reclaim_rate | 0.860 | 0.677 | 0.543 | 0.795 | 0.184 | 0.004 |
| NDX | iid | retest_rate | 0.722 | 0.700 | 0.541 | 0.840 | 0.023 | 0.834 |
| NDX | iid | breaks_per_year | 1.046 | 1.338 | 0.949 | 1.776 | -0.292 | 0.204 |
| NDX | iid | deep_share | 0.432 | 0.396 | 0.243 | 0.552 | 0.037 | 0.635 |
| NDX | msvol | reclaim_rate | 0.860 | 0.695 | 0.569 | 0.820 | 0.165 | 0.008 |
| NDX | msvol | retest_rate | 0.722 | 0.701 | 0.529 | 0.833 | 0.022 | 0.838 |
| NDX | msvol | breaks_per_year | 1.046 | 1.116 | 0.754 | 1.509 | -0.070 | 0.802 |
| NDX | msvol | deep_share | 0.432 | 0.460 | 0.259 | 0.633 | -0.027 | 0.766 |
| SPX | block | reclaim_rate | 0.692 | 0.723 | 0.649 | 0.798 | -0.030 | 0.459 |
| SPX | block | retest_rate | 0.790 | 0.655 | 0.560 | 0.747 | 0.136 | 0.004 |
| SPX | block | breaks_per_year | 1.187 | 1.312 | 1.086 | 1.573 | -0.124 | 0.343 |
| SPX | block | deep_share | 0.321 | 0.366 | 0.273 | 0.460 | -0.045 | 0.355 |
| SPX | garch | reclaim_rate | 0.692 | 0.743 | 0.647 | 0.845 | -0.051 | 0.363 |
| SPX | garch | retest_rate | 0.790 | 0.647 | 0.523 | 0.764 | 0.143 | 0.024 |
| SPX | garch | breaks_per_year | 1.187 | 0.810 | 0.614 | 1.025 | 0.377 | 0.004 |
| SPX | garch | deep_share | 0.321 | 0.305 | 0.174 | 0.443 | 0.016 | 0.834 |
| SPX | gbm | reclaim_rate | 0.692 | 0.721 | 0.647 | 0.794 | -0.029 | 0.435 |
| SPX | gbm | retest_rate | 0.790 | 0.739 | 0.658 | 0.821 | 0.051 | 0.208 |
| SPX | gbm | breaks_per_year | 1.187 | 1.575 | 1.294 | 1.857 | -0.388 | 0.004 |
| SPX | gbm | deep_share | 0.321 | 0.292 | 0.215 | 0.378 | 0.029 | 0.479 |
| SPX | iid | reclaim_rate | 0.692 | 0.635 | 0.564 | 0.712 | 0.058 | 0.152 |
| SPX | iid | retest_rate | 0.790 | 0.709 | 0.615 | 0.797 | 0.082 | 0.072 |
| SPX | iid | breaks_per_year | 1.187 | 1.548 | 1.283 | 1.827 | -0.360 | 0.008 |
| SPX | iid | deep_share | 0.321 | 0.269 | 0.185 | 0.360 | 0.052 | 0.275 |
| SPX | msvol | reclaim_rate | 0.692 | 0.690 | 0.614 | 0.764 | 0.003 | 0.970 |
| SPX | msvol | retest_rate | 0.790 | 0.698 | 0.592 | 0.789 | 0.092 | 0.052 |
| SPX | msvol | breaks_per_year | 1.187 | 1.311 | 1.076 | 1.588 | -0.124 | 0.343 |
| SPX | msvol | deep_share | 0.321 | 0.333 | 0.235 | 0.437 | -0.012 | 0.830 |

## Pseudo-level difference-in-differences (secondary)

| index | pseudo_level | metric | observed_diff | null_diff_mean | p |
|---|---|---|---|---|---|
| NDX | q05 | reclaim_rate | 0.114 | 0.036 | 0.224 |
| NDX | q05 | retest_rate | 0.062 | 0.006 | 0.523 |
| NDX | q10 | reclaim_rate | 0.194 | 0.037 | 0.032 |
| NDX | q10 | retest_rate | 0.070 | -0.001 | 0.427 |
| NDX | q20 | reclaim_rate | 0.094 | 0.030 | 0.379 |
| NDX | q20 | retest_rate | 0.102 | -0.002 | 0.263 |
| SPX | q05 | reclaim_rate | 0.021 | 0.010 | 0.810 |
| SPX | q05 | retest_rate | 0.086 | -0.009 | 0.052 |
| SPX | q10 | reclaim_rate | 0.032 | 0.014 | 0.639 |
| SPX | q10 | retest_rate | 0.102 | -0.018 | 0.028 |
| SPX | q20 | reclaim_rate | 0.014 | 0.012 | 0.950 |
| SPX | q20 | retest_rate | 0.098 | -0.024 | 0.008 |
