# Training-period verdicts (events through 2017-12-31)

Written before the hold-out was run. Source: `results/layer_tests_train.csv`, `ledger.csv`.
Ledger: 69 tests, 55 with p-values, **0 survive BH at q = 0.10**.

## Summary per layer

| Layer | Verdict |
|---|---|
| L1 H1 Fed stance | KILLED on all assets and targets |
| L2 H2a realised-vol roll | KILLED on all assets and targets |
| L2 H2b VIX/VIX3M exit (1.00) | KILLED (SOX); UNDERPOWERED (SPX, NDX: fewer than 8 signal rows / 9-13 episodes, 2007-2017 only) |
| L2 H2b-095 | KILLED (SOX); UNDERPOWERED (SPX, NDX) |
| L2 H2c VIX >= 90th pct of 5y | KILLED on all assets and targets |
| L3 H3 credit not confirming | KILLED on all assets and targets |
| L3 H4 Korea non-semis | NOT RUN (product split not obtainable; PREREGISTRATION B3) |
| L3 H4-total substitute | KILLED on all assets and targets (closest miss of the study: NDX T2, 3m change, skill +0.111, perm p 0.002, BH 0.110) |
| H5 structural break | descriptive only (report) |

Layer 0 (price/episode state only) is therefore **not beaten** by any pre-registered layer in training.

## Survivors

None.

## Killed

| asset   | target   | layer       |   n_ep |   n_rows |   skill |   coef |   sign_h1 |   sign_h2 |   n_assets_same_sign |   p_perm |   p_bh | verdict                                                                                                                       |
|:--------|:---------|:------------|-------:|---------:|--------:|-------:|----------:|----------:|---------------------:|---------:|-------:|:------------------------------------------------------------------------------------------------------------------------------|
| SPX     | T1       | H1          |     49 |      102 |   0.015 |  0.419 |    -1.000 |     1.000 |                    1 |    0.011 |  0.151 | KILLED: skill +0.015<0.02; sign not shared by 2 of 3 assets; sign flips across halves; BH p 0.15>0.10                         |
| SPX     | T1       | H2a         |     49 |      143 |  -0.003 |  0.157 |     1.000 |    -1.000 |                    3 |    0.549 |  1.000 | KILLED: skill -0.003<0.02; sign flips across halves; BH p 1.00>0.10                                                           |
| SPX     | T1       | H2c         |     19 |       47 |  -0.157 |  0.350 |   nan     |     1.000 |                    3 |    0.817 |  1.000 | KILLED: skill -0.157<0.02; halves sign not evaluable (one half has no data); BH p 1.00>0.10                                   |
| SPX     | T1       | H3          |     49 |      102 |   0.209 | -1.171 |    -1.000 |    -1.000 |                    2 |    0.026 |  0.204 | KILLED: BH p 0.20>0.10                                                                                                        |
| SPX     | T1       | H4total_yoy |     41 |       83 |  -0.040 | -0.047 |    -1.000 |    -1.000 |                    3 |    0.865 |  1.000 | KILLED: skill -0.040<0.02; BH p 1.00>0.10                                                                                     |
| SPX     | T1       | H4total_d3  |     40 |       82 |  -0.038 |  0.110 |     1.000 |    -1.000 |                    1 |    0.914 |  1.000 | KILLED: skill -0.038<0.02; sign not shared by 2 of 3 assets; sign flips across halves; BH p 1.00>0.10                         |
| SPX     | T2       | H1          |     49 |      102 |   0.033 |  0.505 |    -1.000 |     1.000 |                    2 |    0.045 |  0.275 | KILLED: sign flips across halves; BH p 0.28>0.10                                                                              |
| SPX     | T2       | H2a         |     49 |      143 |  -0.012 |  0.048 |     1.000 |     1.000 |                    3 |    0.981 |  1.000 | KILLED: skill -0.012<0.02; BH p 1.00>0.10                                                                                     |
| SPX     | T2       | H2c         |     19 |       47 |  -0.115 | -0.055 |   nan     |    -1.000 |                    1 |    0.915 |  1.000 | KILLED: skill -0.115<0.02; sign not shared by 2 of 3 assets; halves sign not evaluable (one half has no data); BH p 1.00>0.10 |
| SPX     | T2       | H3          |     49 |      102 |   0.013 | -0.400 |    -1.000 |    -1.000 |                    2 |    0.671 |  1.000 | KILLED: skill +0.013<0.02; BH p 1.00>0.10                                                                                     |
| SPX     | T2       | H4total_yoy |     41 |       83 |  -0.035 | -0.287 |    -1.000 |    -1.000 |                    3 |    0.215 |  0.696 | KILLED: skill -0.035<0.02; BH p 0.70>0.10                                                                                     |
| SPX     | T2       | H4total_d3  |     40 |       82 |  -0.050 | -0.056 |    -1.000 |     1.000 |                    3 |    0.861 |  1.000 | KILLED: skill -0.050<0.02; sign flips across halves; BH p 1.00>0.10                                                           |
| NDX     | T1       | H1          |     61 |      119 |  -0.057 | -0.028 |    -1.000 |     1.000 |                    2 |    1.000 |  1.000 | KILLED: skill -0.057<0.02; sign flips across halves; BH p 1.00>0.10                                                           |
| NDX     | T1       | H2a         |     61 |      159 |  -0.004 |  0.018 |     1.000 |    -1.000 |                    3 |    0.755 |  1.000 | KILLED: skill -0.004<0.02; sign flips across halves; BH p 1.00>0.10                                                           |
| NDX     | T1       | H2c         |     51 |       98 |  -0.034 |  0.403 |     1.000 |     1.000 |                    3 |    0.124 |  0.568 | KILLED: skill -0.034<0.02; BH p 0.57>0.10                                                                                     |
| NDX     | T1       | H3          |     61 |      119 |  -0.018 |  0.425 |     1.000 |     1.000 |                    1 |    0.785 |  1.000 | KILLED: skill -0.018<0.02; sign not shared by 2 of 3 assets; BH p 1.00>0.10                                                   |
| NDX     | T1       | H4total_yoy |     61 |      119 |  -0.012 | -0.289 |    -1.000 |    -1.000 |                    3 |    0.111 |  0.568 | KILLED: skill -0.012<0.02; BH p 0.57>0.10                                                                                     |
| NDX     | T1       | H4total_d3  |     61 |      119 |   0.038 | -0.518 |    -1.000 |    -1.000 |                    2 |    0.007 |  0.128 | KILLED: BH p 0.13>0.10                                                                                                        |
| NDX     | T2       | H1          |     61 |      119 |  -0.027 | -0.302 |    -1.000 |     1.000 |                    1 |    0.342 |  0.890 | KILLED: skill -0.027<0.02; sign not shared by 2 of 3 assets; sign flips across halves; BH p 0.89>0.10                         |
| NDX     | T2       | H2a         |     61 |      159 |  -0.006 |  0.026 |     1.000 |    -1.000 |                    3 |    0.700 |  1.000 | KILLED: skill -0.006<0.02; sign flips across halves; BH p 1.00>0.10                                                           |
| NDX     | T2       | H2c         |     51 |       98 |  -0.037 |  0.472 |     1.000 |    -1.000 |                    2 |    0.184 |  0.696 | KILLED: skill -0.037<0.02; sign flips across halves; BH p 0.70>0.10                                                           |
| NDX     | T2       | H3          |     61 |      119 |   0.014 |  0.588 |     1.000 |     1.000 |                    1 |    0.250 |  0.735 | KILLED: skill +0.014<0.02; sign not shared by 2 of 3 assets; BH p 0.74>0.10                                                   |
| NDX     | T2       | H4total_yoy |     61 |      119 |   0.039 | -0.496 |    -1.000 |    -1.000 |                    3 |    0.005 |  0.128 | KILLED: BH p 0.13>0.10                                                                                                        |
| NDX     | T2       | H4total_d3  |     61 |      119 |   0.111 | -0.771 |    -1.000 |    -1.000 |                    3 |    0.002 |  0.110 | KILLED: BH p 0.11>0.10                                                                                                        |
| SOX     | T1       | H1          |     94 |      195 |  -0.017 | -0.080 |    -1.000 |     1.000 |                    2 |    0.888 |  1.000 | KILLED: skill -0.017<0.02; sign flips across halves; BH p 1.00>0.10                                                           |
| SOX     | T1       | H2a         |     94 |      248 |  -0.008 |  0.095 |     1.000 |     1.000 |                    3 |    0.985 |  1.000 | KILLED: skill -0.008<0.02; BH p 1.00>0.10                                                                                     |
| SOX     | T1       | H2b         |     23 |       54 |  -0.029 |  0.282 |    -1.000 |     1.000 |                    2 |    0.860 |  1.000 | KILLED: skill -0.029<0.02; sign flips across halves; BH p 1.00>0.10                                                           |
| SOX     | T1       | H2b095      |     23 |       57 |  -0.044 |  0.039 |    -1.000 |     1.000 |                    1 |    0.965 |  1.000 | KILLED: skill -0.044<0.02; sign not shared by 2 of 3 assets; sign flips across halves; BH p 1.00>0.10                         |
| SOX     | T1       | H2c         |     94 |      195 |  -0.012 |  0.212 |     1.000 |    -1.000 |                    3 |    0.447 |  0.983 | KILLED: skill -0.012<0.02; sign flips across halves; BH p 0.98>0.10                                                           |
| SOX     | T1       | H3          |     94 |      195 |  -0.013 | -0.125 |    -1.000 |    -1.000 |                    2 |    0.602 |  1.000 | KILLED: skill -0.013<0.02; BH p 1.00>0.10                                                                                     |
| SOX     | T1       | H4total_yoy |     94 |      195 |   0.036 | -0.470 |    -1.000 |    -1.000 |                    3 |    0.017 |  0.187 | KILLED: BH p 0.19>0.10                                                                                                        |
| SOX     | T1       | H4total_d3  |     94 |      195 |   0.011 | -0.368 |    -1.000 |    -1.000 |                    2 |    0.044 |  0.275 | KILLED: skill +0.011<0.02; BH p 0.28>0.10                                                                                     |
| SOX     | T2       | H1          |     94 |      195 |  -0.009 |  0.075 |    -1.000 |     1.000 |                    2 |    0.254 |  0.735 | KILLED: skill -0.009<0.02; sign flips across halves; BH p 0.74>0.10                                                           |
| SOX     | T2       | H2a         |     94 |      248 |  -0.003 |  0.060 |     1.000 |     1.000 |                    3 |    0.955 |  1.000 | KILLED: skill -0.003<0.02; BH p 1.00>0.10                                                                                     |
| SOX     | T2       | H2b         |     23 |       54 |  -0.017 |  0.403 |    -1.000 |     1.000 |                    1 |    0.356 |  0.890 | KILLED: skill -0.017<0.02; sign not shared by 2 of 3 assets; sign flips across halves; BH p 0.89>0.10                         |
| SOX     | T2       | H2b095      |     23 |       57 |  -0.042 |  0.119 |    -1.000 |     1.000 |                    2 |    0.977 |  1.000 | KILLED: skill -0.042<0.02; sign flips across halves; BH p 1.00>0.10                                                           |
| SOX     | T2       | H2c         |     94 |      195 |  -0.004 |  0.302 |     1.000 |    -1.000 |                    2 |    0.148 |  0.626 | KILLED: skill -0.004<0.02; sign flips across halves; BH p 0.63>0.10                                                           |
| SOX     | T2       | H3          |     94 |      195 |  -0.015 | -0.013 |    -1.000 |    -1.000 |                    2 |    0.809 |  1.000 | KILLED: skill -0.015<0.02; BH p 1.00>0.10                                                                                     |
| SOX     | T2       | H4total_yoy |     94 |      195 |  -0.001 | -0.314 |    -1.000 |    -1.000 |                    3 |    0.214 |  0.696 | KILLED: skill -0.001<0.02; BH p 0.70>0.10                                                                                     |
| SOX     | T2       | H4total_d3  |     94 |      195 |   0.020 | -0.386 |    -1.000 |    -1.000 |                    3 |    0.023 |  0.204 | KILLED: skill +0.020<0.02; BH p 0.20>0.10                                                                                     |

## Underpowered (prior only; counts, no significance)

| asset   | target   | layer   |   n_ep |   n_rows |   skill |   coef |   sign_h1 |   sign_h2 |   n_assets_same_sign |   p_perm |   p_bh | verdict                   |
|:--------|:---------|:--------|-------:|---------:|--------:|-------:|----------:|----------:|---------------------:|---------:|-------:|:--------------------------|
| SPX     | T1       | H2b     |      9 |       28 |  -0.008 | -0.082 |   nan     |    -1.000 |                    1 |    0.595 |    nan | UNDERPOWERED (prior only) |
| SPX     | T1       | H2b095  |      9 |       27 |  -0.019 | -0.221 |   nan     |    -1.000 |                    2 |    0.714 |    nan | UNDERPOWERED (prior only) |
| SPX     | T2       | H2b     |      9 |       28 |  -0.022 | -0.010 |   nan     |    -1.000 |                    2 |    0.836 |    nan | UNDERPOWERED (prior only) |
| SPX     | T2       | H2b095  |      9 |       27 |   0.008 |  0.151 |   nan     |     1.000 |                    2 |    0.502 |    nan | UNDERPOWERED (prior only) |
| NDX     | T1       | H2b     |     13 |       31 |  -0.025 |  0.228 |     1.000 |   nan     |                    2 |    0.438 |    nan | UNDERPOWERED (prior only) |
| NDX     | T1       | H2b095  |     13 |       31 |  -0.074 | -0.160 |    -1.000 |   nan     |                    2 |    0.881 |    nan | UNDERPOWERED (prior only) |
| NDX     | T2       | H2b     |     13 |       31 |  -0.019 | -0.106 |    -1.000 |   nan     |                    2 |    0.430 |    nan | UNDERPOWERED (prior only) |
| NDX     | T2       | H2b095  |     13 |       31 |  -0.076 | -0.175 |    -1.000 |   nan     |                    1 |    0.878 |    nan | UNDERPOWERED (prior only) |

## H4-total incremental value over the asset's own 63-session return

| asset   | target   | feature   |   partial_corr |   brier_base |   brier_with |   brier_gain |   n |   n_ep |
|:--------|:---------|:----------|---------------:|-------------:|-------------:|-------------:|----:|-------:|
| SPX     | T1       | kr_yoy    |         -0.005 |        0.195 |        0.203 |       -0.044 |  83 |     41 |
| SPX     | T1       | kr_d3     |          0.157 |        0.195 |        0.203 |       -0.040 |  82 |     40 |
| SPX     | T2       | kr_yoy    |         -0.185 |        0.264 |        0.268 |       -0.014 |  83 |     41 |
| SPX     | T2       | kr_d3     |         -0.051 |        0.264 |        0.271 |       -0.027 |  82 |     40 |
| NDX     | T1       | kr_yoy    |         -0.016 |        0.198 |        0.199 |       -0.005 | 119 |     61 |
| NDX     | T1       | kr_d3     |         -0.152 |        0.198 |        0.189 |        0.047 | 119 |     61 |
| NDX     | T2       | kr_yoy    |         -0.130 |        0.207 |        0.193 |        0.069 | 119 |     61 |
| NDX     | T2       | kr_d3     |         -0.235 |        0.207 |        0.182 |        0.121 | 119 |     61 |
| SOX     | T1       | kr_yoy    |         -0.157 |        0.238 |        0.237 |        0.004 | 195 |     94 |
| SOX     | T1       | kr_d3     |         -0.098 |        0.238 |        0.238 |       -0.003 | 195 |     94 |
| SOX     | T2       | kr_yoy    |         -0.158 |        0.200 |        0.200 |       -0.000 | 195 |     94 |
| SOX     | T2       | kr_d3     |         -0.163 |        0.200 |        0.196 |        0.022 | 195 |     94 |

## Inherited thresholds (training, one row per episode)

| test_id        | hypothesis                                                                          |   statistic |   p_value |    p_bh |   n_events | detail                            | inherited_from                               |
|:---------------|:------------------------------------------------------------------------------------|------------:|----------:|--------:|-----------:|:----------------------------------|:---------------------------------------------|
| H1_SPX_T1      | Fed stance (6m FEDFUNDS change, lagged) adds skill over Layer 0                     |       0.015 |     0.011 |   0.151 |         49 | rows=102 perm_p=0.011             | Midterm Cycle note (Fed rule)                |
| H2b_SPX_T1     | VIX/VIX3M term-structure exit (1.00) date is a better entry                         |      -0.008 |   nan     | nan     |          9 | rows=28 perm_p=0.595 UNDERPOWERED | v16 episode-state flag desk color            |
| H2c_SPX_T1     | VIX >= 90th pct of prior 5y at t adds skill                                         |      -0.157 |     0.817 |   1.000 |         19 | rows=47 perm_p=0.817              | Fear Cycle / VIX levels                      |
| H3_SPX_T1      | Credit not confirming (Baa-GS10 change per unit depth below median) adds skill      |       0.209 |     0.026 |   0.204 |         49 | rows=102 perm_p=0.026             | v14 credit composite                         |
| H3daily_SPX_T1 | H3 with daily BAA10Y (robustness)                                                   |      -0.113 |     0.966 |   1.000 |         26 | rows=59 perm_p=0.966              | v14 credit composite                         |
| H1_SPX_T2      | Fed stance (6m FEDFUNDS change, lagged) adds skill over Layer 0                     |       0.033 |     0.045 |   0.275 |         49 | rows=102 perm_p=0.045             | Midterm Cycle note (Fed rule)                |
| H2b_SPX_T2     | VIX/VIX3M term-structure exit (1.00) date is a better entry                         |      -0.022 |   nan     | nan     |          9 | rows=28 perm_p=0.836 UNDERPOWERED | v16 episode-state flag desk color            |
| H2c_SPX_T2     | VIX >= 90th pct of prior 5y at t adds skill                                         |      -0.115 |     0.915 |   1.000 |         19 | rows=47 perm_p=0.915              | Fear Cycle / VIX levels                      |
| H3_SPX_T2      | Credit not confirming (Baa-GS10 change per unit depth below median) adds skill      |       0.013 |     0.671 |   1.000 |         49 | rows=102 perm_p=0.671             | v14 credit composite                         |
| H3daily_SPX_T2 | H3 with daily BAA10Y (robustness)                                                   |      -0.083 |     0.814 |   1.000 |         26 | rows=59 perm_p=0.814              | v14 credit composite                         |
| H1_NDX_T1      | Fed stance (6m FEDFUNDS change, lagged) adds skill over Layer 0                     |      -0.057 |     1.000 |   1.000 |         61 | rows=119 perm_p=1.000             | Midterm Cycle note (Fed rule)                |
| H2b_NDX_T1     | VIX/VIX3M term-structure exit (1.00) date is a better entry                         |      -0.025 |   nan     | nan     |         13 | rows=31 perm_p=0.438 UNDERPOWERED | v16 episode-state flag desk color            |
| H2c_NDX_T1     | VIX >= 90th pct of prior 5y at t adds skill                                         |      -0.034 |     0.124 |   0.568 |         51 | rows=98 perm_p=0.124              | Fear Cycle / VIX levels                      |
| H3_NDX_T1      | Credit not confirming (Baa-GS10 change per unit depth below median) adds skill      |      -0.018 |     0.785 |   1.000 |         61 | rows=119 perm_p=0.785             | v14 credit composite                         |
| H3daily_NDX_T1 | H3 with daily BAA10Y (robustness)                                                   |      -0.017 |     0.295 |   0.811 |         61 | rows=119 perm_p=0.295             | v14 credit composite                         |
| H1_NDX_T2      | Fed stance (6m FEDFUNDS change, lagged) adds skill over Layer 0                     |      -0.027 |     0.342 |   0.890 |         61 | rows=119 perm_p=0.342             | Midterm Cycle note (Fed rule)                |
| H2b_NDX_T2     | VIX/VIX3M term-structure exit (1.00) date is a better entry                         |      -0.019 |   nan     | nan     |         13 | rows=31 perm_p=0.430 UNDERPOWERED | v16 episode-state flag desk color            |
| H2c_NDX_T2     | VIX >= 90th pct of prior 5y at t adds skill                                         |      -0.037 |     0.184 |   0.696 |         51 | rows=98 perm_p=0.184              | Fear Cycle / VIX levels                      |
| H3_NDX_T2      | Credit not confirming (Baa-GS10 change per unit depth below median) adds skill      |       0.014 |     0.250 |   0.735 |         61 | rows=119 perm_p=0.250             | v14 credit composite                         |
| H3daily_NDX_T2 | H3 with daily BAA10Y (robustness)                                                   |      -0.037 |     0.990 |   1.000 |         61 | rows=119 perm_p=0.990             | v14 credit composite                         |
| H1_SOX_T1      | Fed stance (6m FEDFUNDS change, lagged) adds skill over Layer 0                     |      -0.017 |     0.888 |   1.000 |         94 | rows=195 perm_p=0.888             | Midterm Cycle note (Fed rule)                |
| H2b_SOX_T1     | VIX/VIX3M term-structure exit (1.00) date is a better entry                         |      -0.029 |     0.860 |   1.000 |         23 | rows=54 perm_p=0.860              | v16 episode-state flag desk color            |
| H2c_SOX_T1     | VIX >= 90th pct of prior 5y at t adds skill                                         |      -0.012 |     0.447 |   0.983 |         94 | rows=195 perm_p=0.447             | Fear Cycle / VIX levels                      |
| H3_SOX_T1      | Credit not confirming (Baa-GS10 change per unit depth below median) adds skill      |      -0.013 |     0.602 |   1.000 |         94 | rows=195 perm_p=0.602             | v14 credit composite                         |
| H3daily_SOX_T1 | H3 with daily BAA10Y (robustness)                                                   |      -0.011 |     0.535 |   1.000 |         94 | rows=195 perm_p=0.535             | v14 credit composite                         |
| H1_SOX_T2      | Fed stance (6m FEDFUNDS change, lagged) adds skill over Layer 0                     |      -0.009 |     0.254 |   0.735 |         94 | rows=195 perm_p=0.254             | Midterm Cycle note (Fed rule)                |
| H2b_SOX_T2     | VIX/VIX3M term-structure exit (1.00) date is a better entry                         |      -0.017 |     0.356 |   0.890 |         23 | rows=54 perm_p=0.356              | v16 episode-state flag desk color            |
| H2c_SOX_T2     | VIX >= 90th pct of prior 5y at t adds skill                                         |      -0.004 |     0.148 |   0.626 |         94 | rows=195 perm_p=0.148             | Fear Cycle / VIX levels                      |
| H3_SOX_T2      | Credit not confirming (Baa-GS10 change per unit depth below median) adds skill      |      -0.015 |     0.809 |   1.000 |         94 | rows=195 perm_p=0.809             | v14 credit composite                         |
| H3daily_SOX_T2 | H3 with daily BAA10Y (robustness)                                                   |      -0.010 |     0.402 |   0.921 |         94 | rows=195 perm_p=0.402             | v14 credit composite                         |
| I1_SPX_T1      | First shock within 5% of 252-session high is contained (T1) more often              |     nan     |   nan     | nan     |         13 | 0/0 vs 10/13                      | Blue Tsunami Flush (6 Nov 2026)              |
| I2_SPX_T1      | First shock >10% below 252-session high is contained less often (fell further 10%+) |      -0.300 |     0.528 |   1.000 |         13 | 7/10 vs 3/3                       | Blue Tsunami Flush (6 Nov 2026)              |
| I1b_SPX_T1     | I1 with pre-shock (t-1) distance from 252-session high, as in the parent note       |       0.333 |     0.497 |   1.000 |         13 | 4/4 vs 6/9                        | Blue Tsunami Flush (6 Nov 2026)              |
| I2b_SPX_T1     | I2 with pre-shock (t-1) distance from 252-session high, as in the parent note       |      -0.429 |     0.192 |   0.696 |         13 | 4/7 vs 6/6                        | Blue Tsunami Flush (6 Nov 2026)              |
| I3_SPX_T1      | VIX >= 35 at the first event of an episode changes T1 rate                          |      -0.429 |     0.120 |   0.568 |         21 | 3/7 vs 12/14                      | JPM VIX 35 level via Blue Tsunami desk color |
| I1_NDX_T1      | First shock within 5% of 252-session high is contained (T1) more often              |     nan     |   nan     | nan     |          5 | 0/0 vs 3/5                        | Blue Tsunami Flush (6 Nov 2026)              |
| I2_NDX_T1      | First shock >10% below 252-session high is contained less often (fell further 10%+) |      -0.500 |     1.000 |   1.000 |          5 | 2/4 vs 1/1                        | Blue Tsunami Flush (6 Nov 2026)              |
| I1b_NDX_T1     | I1 with pre-shock (t-1) distance from 252-session high, as in the parent note       |       0.500 |     1.000 |   1.000 |          5 | 1/1 vs 2/4                        | Blue Tsunami Flush (6 Nov 2026)              |
| I2b_NDX_T1     | I2 with pre-shock (t-1) distance from 252-session high, as in the parent note       |      -0.667 |     0.400 |   0.921 |          5 | 1/3 vs 2/2                        | Blue Tsunami Flush (6 Nov 2026)              |
| I3_NDX_T1      | VIX >= 35 at the first event of an episode changes T1 rate                          |       0.021 |     1.000 |   1.000 |         56 | 5/8 vs 29/48                      | JPM VIX 35 level via Blue Tsunami desk color |
| I1_SOX_T1      | First shock within 5% of 252-session high is contained (T1) more often              |     nan     |   nan     | nan     |          6 | 0/0 vs 1/6                        | Blue Tsunami Flush (6 Nov 2026)              |
| I2_SOX_T1      | First shock >10% below 252-session high is contained less often (fell further 10%+) |     nan     |   nan     | nan     |          6 | 1/6 vs 0/0                        | Blue Tsunami Flush (6 Nov 2026)              |
| I1b_SOX_T1     | I1 with pre-shock (t-1) distance from 252-session high, as in the parent note       |     nan     |   nan     | nan     |          6 | 0/0 vs 1/6                        | Blue Tsunami Flush (6 Nov 2026)              |
| I2b_SOX_T1     | I2 with pre-shock (t-1) distance from 252-session high, as in the parent note       |     nan     |   nan     | nan     |          6 | 1/6 vs 0/0                        | Blue Tsunami Flush (6 Nov 2026)              |
| I3_SOX_T1      | VIX >= 35 at the first event of an episode changes T1 rate                          |       0.089 |     0.711 |   1.000 |         94 | 4/7 vs 42/87                      | JPM VIX 35 level via Blue Tsunami desk color |
