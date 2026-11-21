# Study 3: The Exhaustion Model

21 Nov 2026. Data through the 20 Nov 2026 close. Nothing here is a trading recommendation.

**Pre-registration commit: `6b531d8`.** That commit contains `PREREGISTRATION.md` and the data gates, and nothing else; no outcome had been computed when it was made. Later commits, in order:
- `488e30f`: code and deviation D1, before the first run.
- `f9ad371`: training run and D2.
- `79166f4`: training verdicts.
- `6e6a30c`: hold-out unlock.
- `fd8614b`: the single hold-out run.

## Answer first

**None of the pre-registered exhaustion layers separates contained episodes from escalating ones better than price-and-episode state alone.** All 55 testable layer and inherited tests on the 69-row ledger fail, and 0 survive Benjamini-Hochberg at q = 0.10. Out of sample (2018 to 2026), Layer 0 itself scores **worse than a constant base rate** on all six asset/target pairs. The two strongest training-period candidates reverse sign in the hold-out:
- **H3 credit**, SPX T1: training skill **+0.209**, hold-out **-0.240**.
- **H4-total Korea export momentum**, NDX T2: training skill **+0.111**, hold-out **-0.193**.

What survives is descriptive: the escalation ladder, which matters by asset (exhibit 2). NDX containment falls from **63%** at -10% to **41%** at -20%. SPX does not fall: **76%** at -10%, **79%** at -20%. SOX is below 55% at every rung.

**Live.**
- **SPX:** the 5 Nov first shock (-4.36%) was followed by a -10% swing crossing on 20 Nov (6,910.39, -11.6% from the 6 Oct peak of 7,818.93). The first-shock containment line (**6,618.36**) has not been breached; the 20 Nov close is 4.4% above it.
- **SOX:** in a new episode, -20.4% from its 11 Nov reference peak. This is its third leg since the June all-time high.
- **H2b:** has not fired. VIX/VIX3M has been above 1.0 since 17 Nov (1.16 on 20 Nov).

---

## 0. Step 0: scoring the parent notes before building

| # | Prior flip / call | Reading | Status | Source |
|---|---|---|---|---|
| 1 | $500M data-centre loan auction, bids 19 Nov: >90 flush, <80 thesis | ING's competitive sale of about a dozen data-centre loans **stalled on low bids**, with no clearing price published. ING moved to bilateral sales. Pre-auction FT price talk was >90c for the Wisconsin/Texas loans and mid-80s for New Mexico (indications, not a result). | **Neither flip triggered (no print).** *Rescored post-hoc (D8): see Post-hoc diagnostics.* A failed competitive process is qualitatively a stress signal, but it is not the pre-registered reading. | Bloomberg, 20 Nov 2026 ("ING's $500 million data center loan auction stalls on low bids"). **Single source**, read via search snippet only; verify. |
| 2 | Fear Cycle flip: "any top-4 capex cut" | AMZN kept ~$220B (29 Oct). GOOGL kept $195-205B (28 Oct). META narrowed to $135-145B, raising the low end (21 Oct, outside the 28-30 Oct window). MSFT Q1 capex was $45.2B vs its own >$50B guide; the full-year figure was reportedly trimmed ~$175B to ~$170B, framed as a delivery delay. | **Not triggered on a strict reading** (no formal cut). MSFT is the borderline case. Its ~$5bn shortfall was first reported by The Information: a miss against the company's own guide, not a guidance cut. | CNBC 28-29 Oct; Meta IR; Motley Fool transcripts; Blockspace and 24/7 Wall St on the MSFT/IREN item. The "$175B to $170B" figure is **secondary-source only**; sources conflict on whether it is FY27 or CY26. |
| 3 | Rebound leadership: suppliers > 2x builders over the first five up days after 5 Nov = flush | SPX had only **3 up days** from 6 Nov to 20 Nov (6, 9, 11 Nov). Over those 3: suppliers EW **+24.7%**, builders EW **+2.1%** (ratio ~12x). | **Incomplete (3 of 5 up days).** *Rescored post-hoc (D8).* Leaning flush on the days available, but the rebound reversed: SPX fell on 7 straight sessions to 20 Nov. | `src/step0.py`, Yahoo closes, 23-name Blue Tsunami list (16 suppliers, 4 builders; 3 non-AI controls excluded) |
| 4a | Fear Cycle falsifier "SMH new high by ~Nov 2026" | **FAILED** | Recorded as scored in chat; not recomputed | prompt |
| 4b | Holding-the-List "close below 29-Jul low" | **FIRED** (ETF level) | Recorded; not recomputed | prompt |
| 4c | v14 credit trigger CRWV CDS > 1,000bp | **Fired.** Search results show ~1,278-1,289bp on 5 Nov, ~1,155bp on 6 Nov, ~1,152bp on 10 Nov, "1,100-1,200bp" mid-Nov | Fired; multiple CNBC reports, but via search snippets only | CNBC 6, 10, 18 Nov 2026 |

Caveat: the Step 0 web facts came from a research sub-agent that could read **search-result text only**; direct page fetches to Bloomberg, Fool and Korean outlets were blocked by the network policy. Treat every Step 0 web item as needing confirmation against the primary source.

---

## Data and method in one paragraph

The eight input files named in the prompt were not attached, so all inputs were rebuilt from public sources: Yahoo closes for SPX, NDX, SOX, VIX and VIX3M, and FRED for FEDFUNDS, BAA, GS10, BAA10Y and Korean exports. Every file is logged in `data/raw/MANIFEST.csv`. All the prompt's validation checks pass (`tests/test_data.py`, 19 tests).

Method:
- **Events:**
  - Family A: first shocks at the SPX -4% percentile (0.295th). That gives NDX -6.35% and SOX -8.15%.
  - Family B: -10/-15/-20/-30% swing-drawdown crossings, with a 10%-rebound or new-high reset.
- **Targets:** T1 = no further 10% fall within 63 sessions. T2 = T1 and higher 252 sessions later.
- **Model:** Bayesian logistic regression with at most 3 features, evaluated leave-one-episode-out.
- **Survival rules:** Brier skill of at least 0.02, sign agreement across assets and across sample halves, and episode-block permutation p-values with BH across the ledger.
- **Hold-out:** run once.

Full rules: `PREREGISTRATION.md` Parts A to C. Deviations: Part D (D1 to D3).

---

## Exhibit 1. Episodes per asset

Full tables are in `results/episodes_{SPX,NDX,SOX}.csv` (one row per episode) and `results/events_{asset}.csv` (one row per event, with targets and forward returns).

| | SPX | NDX | SOX |
|---|---|---|---|
| Event start | 1954-09 | 1986-10 | 1995-05 |
| Training episodes (to 2017) | 49 | 61 | 94 |
| Hold-out episodes (2018 to 20 Nov 2026) | 9 | 18 | 33 |
| First shocks (training / hold-out) | 13 / 5 | 5 / 2 | 6 / 3 |

**Hold-out episode list, SPX** (T1/T2 measured at the -10% crossing):

| Peak | -10% crossed | Trough | Max depth | Reset | T1 | T2 |
|---|---|---|---|---|---|---|
| 2018-01-26 | 2018-02-08 | 2018-02-08 | -10.2% | rebound | 1 | 1 |
| 2018-09-20 | 2018-11-23 | 2018-12-24 | -19.8% | rebound | 0 | 0 |
| 2020-02-19 | 2020-02-27 | 2020-03-23 | -33.9% | rebound | 0 | 0 |
| 2022-01-03 | 2022-02-22 | 2022-03-08 | -13.0% | rebound | 1 | 0 |
| 2022-03-29 | 2022-04-29 | 2022-06-16 | -20.8% | rebound | 0 | 0 |
| 2022-08-16 | 2022-09-16 | 2022-10-12 | -16.9% | rebound | 1 | 1 |
| 2023-07-31 | 2023-10-27 | 2023-10-27 | -10.3% | rebound | 1 | 1 |
| 2025-02-19 | 2025-03-13 | 2025-04-08 | -18.9% | rebound | 1 | 1 |
| 2026-10-06 | 2026-11-20 | open | -11.6% so far | open | pending | pending |

The NDX and SOX lists (18 and 33 hold-out episodes) are in the CSVs. They include Q4-2018, Feb-Mar 2020, the 2022 legs, Apr 2025 and the 2026 episodes. The 2022 bear splits into four SPX/NDX legs and six SOX legs, as the reset rule intends.

**SPX first shocks** (all; `dist252` measured at the shock close):

| Date | Shock | From 252d high | T1 | T2 | +63d | Worst within 63d |
|---|---|---|---|---|---|---|
| 1955-09-26 | -6.6% | -6.6% | 1 | 1 | +6.1% | -4.2% |
| 1962-05-28 | -6.7% | -23.6% | 1 | 1 | +7.3% | -5.7% |
| 1986-09-11 | -4.8% | -7.3% | 1 | 1 | +6.7% | -2.2% |
| 1987-10-16 | -5.2% | -16.1% | 0 | 0 | -10.9% | -20.8% |
| 1989-10-13 | -6.1% | -7.3% | 1 | 0 | +1.0% | -0.3% |
| 1997-10-27 | -6.9% | -10.8% | 1 | 1 | +11.5% | +3.0% |
| 1998-08-31 | -6.8% | -19.3% | 1 | 1 | +21.6% | +0.2% |
| 2000-04-14 | -5.8% | -11.2% | 1 | 0 | +11.3% | +1.3% |
| 2001-03-12 | -4.3% | -22.7% | 1 | 0 | +6.3% | -6.5% |
| 2001-09-17 | -4.9% | -30.0% | 1 | 0 | +8.1% | -7.0% |
| 2002-09-03 | -4.2% | -25.1% | 0 | 0 | +6.4% | -11.5% |
| 2008-09-15 | -4.7% | -23.8% | 0 | 0 | -26.2% | -36.9% |
| 2011-08-04 | -4.8% | -12.0% | 1 | 1 | +3.2% | -8.4% |
| 2018-02-05 | -4.1% | -7.8% | 1 | 1 | +0.9% | -2.6% |
| 2020-02-27 | -4.4% | -12.0% | 0 | 0 | +1.7% | -24.9% |
| 2022-05-18 | -4.0% | -18.2% | 1 | 1 | +9.2% | -6.5% |
| 2025-04-03 | -4.8% | -12.2% | 1 | 1 | +15.4% | -7.7% |
| **2026-11-05** | **-4.4%** | **-5.9%** | pending | pending | | |

Tallies:
- SPX first shocks: **13 of 17 resolved were contained (T1)**, 9 of 17 held for a year (T2).
- SOX first shocks: **1 of 9 contained** (training and hold-out together).
- NDX first shocks: 3 of 6.

---

## Exhibit 2. Escalation ladder (index level, all events)

| Asset | Rung | Episodes reaching | P(reach next) | T1 (90% Wilson) | T2 | Median +63d | Median +252d | Median worst in 63d |
|---|---|---|---|---|---|---|---|---|
| SPX | -10% | 56 | 54% | 76% [66,84] n=55 | 60% [49,70] | +3.0% | +15.7% | -5.5% |
| SPX | -15% | 30 | 47% | 63% [48,76] n=30 | 50% [36,64] | +4.2% | +17.7% | -4.7% |
| SPX | -20% | 14 | 43% | 79% [57,91] n=14 | 64% [43,81] | +6.0% | +21.3% | -6.4% |
| SPX | -30% | 6 | | 5/6 (n<8) | 5/6 | +3.9% | +24.1% | -6.7% |
| NDX | -10% | 79 | 48% | 63% [54,71] n=78 | 57% [47,66] | +8.3% | +20.8% | -6.0% |
| NDX | -15% | 38 | 58% | 51% [38,64] n=37 | 43% [31,57] | +1.9% | +26.3% | -8.9% |
| NDX | -20% | 22 | 27% | **41% [26,58] n=22** | 36% [22,54] | +1.9% | +7.5% | -15.0% |
| NDX | -30% | 6 | | 2/6 (n<8) | 1/6 | +10.8% | +0.2% | -14.0% |
| SOX | -10% | 127 | 55% | 52% [45,60] n=124 | 42% [35,49] | +6.2% | +12.1% | -8.2% |
| SOX | -15% | 70 | 61% | 41% [32,51] n=68 | 27% [19,37] | +4.1% | +7.4% | -14.3% |
| SOX | -20% | 43 | 28% | **34% [23,47] n=41** | 28% [18,40] | +6.0% | +11.5% | -13.0% |
| SOX | -30% | 12 | | 55% [32,76] n=11 | 45% [24,68] | +16.2% | +23.3% | -10.0% |

Rows within an episode share outcomes, so the intervals are too narrow. Training and hold-out splits are in `results/escalation_ladder.csv`; the figure is `results/fig_escalation_ladder.png`.

**Reading the ladder:**
- **SPX:** escalation does not degrade containment. Once SPX is down 20% it has historically been closer to the bottom than the top of the move.
- **NDX:** escalation is informative. At -20%, 59% of events fell a further 10%+.
- **SOX:** about a coin flip or worse at every rung.

The current SOX state (-20.4%, third leg) sits in a cell where **T1 = 34% and T2 = 28%**.

---

## Exhibit 3. Layer 0 conditional tables (training)

Full tables are in `results/layer0_tables.md`. The best Layer 0 model per asset and target, chosen by LOEO Brier from 25 subsets:

| Asset | Target | Layer 0 model | Training base rate | LOEO Brier | Climatology Brier | Training skill vs climatology | **Hold-out skill vs climatology** |
|---|---|---|---|---|---|---|---|
| SPX | T1 | depth + dist252 + above200 | 0.735 | 0.182 | 0.195 | +0.064 | **-0.026** |
| SPX | T2 | above200 + duration + legs | 0.559 | 0.244 | 0.247 | +0.011 | **-0.037** |
| NDX | T1 | dist252 | 0.521 | 0.193 | 0.250 | +0.225 | **-0.017** |
| NDX | T2 | dist252 | 0.445 | 0.206 | 0.247 | +0.168 | **-0.019** |
| SOX | T1 | above200 + duration + legs | 0.421 | 0.228 | 0.244 | +0.064 | **-0.145** |
| SOX | T2 | depth + legs | 0.308 | 0.199 | 0.213 | +0.067 | **-0.208** |

**The baseline does not generalise either.** Two caveats:
- The training-vs-climatology skill is optimistic, because Layer 0 is the best of 25 subsets selected on the same data.
- The SOX hold-out failure is mostly a level shift. SOX hold-out T1 at -10% was **63%** (n=30) against **49%** in training. Post-2018 semis drawdowns resolved upward more often than 1995-2017 ones, so a model calibrated on the dot-com and 2008 eras is too bearish.

---

## Exhibit 4. Per-layer LOEO Brier skill vs Layer 0 (training) and survival verdict

Source: `results/layer_tests_train.csv`. Skill = 1 - Brier(layer) / Brier(Layer 0). The survival bar is +0.02. p is the episode-block permutation p-value (999 draws); BH is across the full ledger.

| Layer | SPX T1 | SPX T2 | NDX T1 | NDX T2 | SOX T1 | SOX T2 | Verdict |
|---|---|---|---|---|---|---|---|
| H1 Fed 6m stance | +0.015 (p .011, BH .15) | +0.033 (p .045, BH .26) | -0.057 | -0.027 | -0.017 | -0.009 | **KILLED** |
| H2a realised-vol roll | -0.003 | -0.012 | -0.004 | -0.006 | -0.008 | -0.003 | **KILLED** |
| H2b VIX/VIX3M exit 1.00 | -0.008 (u) | -0.022 (u) | -0.025 (u) | -0.019 (u) | -0.029 | -0.017 | **KILLED** (SOX) / **UNDERPOWERED** (SPX, NDX) |
| H2b-095 | -0.019 (u) | +0.008 (u) | -0.074 (u) | -0.076 (u) | -0.044 | -0.042 | **KILLED** / UNDERPOWERED |
| H2c VIX >= 90th pct of 5y | -0.157 | -0.115 | -0.034 | -0.037 | -0.012 | -0.004 | **KILLED** |
| H3 credit not confirming | **+0.209** (p .026, BH .20) | +0.013 | -0.018 | +0.014 | -0.013 | -0.015 | **KILLED** |
| H3-daily (robustness) | -0.113 | -0.083 | -0.017 | -0.037 | -0.011 | -0.010 | robustness only; does not replicate H3 |
| H4 Korea non-semis | | | | | | | **NOT RUN** (data gap) |
| H4-total YoY | -0.040 | -0.035 | -0.012 | +0.039 (p .005, BH .13) | +0.036 (p .017, BH .19) | -0.001 | **KILLED** |
| H4-total 3m change | -0.038 | -0.050 | +0.038 (p .007, BH .13) | **+0.111** (p .002, BH .11) | +0.011 | +0.020 | **KILLED** |

(u) = underpowered: fewer than 8 signal rows, or 9 to 13 episodes, with 2007-2017 only.

Notes:
- **H3 on SPX T1** is the largest training skill in the study, and its sign runs **against** the "credit not confirming = flush" story. When spreads widened little per unit of equity drawdown, SPX was *less* often contained (coefficient -1.17). It fails BH, the daily BAA10Y version shows the opposite skill (-0.113), and it collapses in the hold-out (-0.240).
- **H4-total** has a negative coefficient on all three assets: faster Korean export acceleration goes with *worse* outcomes. On NDX T2 its incremental value over the asset's own 63-session return is real in training (partial correlation **-0.235**, Brier gain **+12.1%**; `results/h4_incremental.csv`). It misses BH by 0.01 and reverses in the hold-out (-0.193). It is a substitute for the pre-registered non-semis series, so it neither confirms nor kills H4.

---

## Exhibit 5. Killed hypotheses (same prominence as survivors)

| Hypothesis | Killed by |
|---|---|
| **H1 Fed stance** (Midterm-note rule, rolling) | Skill below 0.02 on 4 of 6 cells. Sign flips between pre/post-1990 SPX halves. BH 0.15 at best. Hold-out mixed (+0.063 SPX T1, -0.099 NDX T2). |
| **H2a realised-vol roll-over** as an entry signal | Negative skill on all 6 cells. Under the random-timing null (signal moved to a random in-episode day), p >= 0.55 on all cells. Vol roll-over dates were no better than random days in the same episode. |
| **H2b VIX/VIX3M term-structure exit** | Too few events before 2018 to test on SPX/NDX (6-7 signals, 9-13 episodes). Negative skill on SOX. Hold-out skill close to zero (-0.033 to +0.035). **Not a survivor; a prior only.** |
| **H2c VIX >= 90th percentile of 5y** | Negative skill on all 6 cells, as low as -0.157 (SPX T1). |
| **H3 credit not confirming** (v14 composite) | BH 0.20; daily version contradicts it; reverses out of sample (-0.240). |
| **H4-total Korean exports** (substitute) | BH 0.11 to 1.00; NDX T2 reverses out of sample. |
| **I1 / I1b** "first shock within 5% of the 252d high is usually contained" (Blue Tsunami) | At the shock close (I1): **0 qualifying events**, so the definition cannot fire. At the pre-shock close (I1b, D2): SPX 4/4 vs 6/9, NDX 1/1 vs 2/4. **n < 8, prior only**, not testable at this sample size. |
| **I2 / I2b** "first shock >10% below high: fell a further 10%+" | Fisher p 0.19 to 1.00; n < 8 in the critical cells. |
| **I3** VIX >= 35 at the first episode event | SPX 3/7 vs 12/14 contained (p 0.12, BH 0.57); NDX and SOX no difference. |

**Same-author risk, stated:** every inherited threshold above came from one author's notes over one window and one vendor. None of them is confirmed here.

---

## Exhibit 6. Hold-out scorecard (2018-01-01 to 2026-11-20, run once)

Source: `results/holdout_scorecard.csv` and `results/holdout_predictions.csv`. Skill vs Layer 0 (both fitted on training only):

| Layer | SPX T1 | SPX T2 | NDX T1 | NDX T2 | SOX T1 | SOX T2 |
|---|---|---|---|---|---|---|
| H1 | +0.063 | +0.012 | -0.026 | -0.099 | +0.027 | +0.009 |
| H2a | -0.006 | -0.109 | +0.004 | -0.008 | -0.021 | +0.004 |
| H2b | +0.007 | +0.004 | +0.035 | +0.001 | -0.033 | +0.006 |
| H2b-095 | +0.062 | -0.046 | -0.005 | -0.004 | -0.024 | +0.001 |
| H2c | -0.050 | -0.035 | -0.002 | -0.078 | +0.069 | +0.046 |
| H3 | **-0.240** | +0.069 | -0.018 | -0.124 | +0.027 | +0.001 |
| H3-daily | +0.021 | -0.042 | -0.059 | -0.050 | +0.018 | -0.013 |
| H4-total YoY | -0.001 | +0.078 | -0.026 | +0.032 | +0.124 | +0.042 |
| H4-total 3m | +0.008 | +0.015 | -0.131 | **-0.193** | +0.008 | -0.041 |

- Hold-out sizes: SPX 20 rows / 8 episodes; NDX 28-30 / 15-17; SOX 50-58 / 26-30.
- 13 of 54 layer cells clear +0.02 in the hold-out. Across all 54 cells, training skill and hold-out skill are essentially unrelated (Spearman **0.09**; `results/fig_skill_train_vs_holdout.png`).
- **The one consistent pattern, a lead and not a finding:** H4-total YoY (the level of Korean export growth, with a negative coefficient: high export growth means worse outcomes).
  - It had raw permutation p < 0.05 in training on NDX T2 (+0.039, p .005) and SOX T1 (+0.036, p .017).
  - It is positive in the hold-out on 5 of 6 cells (+0.124 on SOX T1).
  - It failed BH, and it is a proxy for the series that was actually pre-registered.
  - The current reading, **+84.7% YoY (Sep 2026)**, has been exceeded only in 1973-74 since 1970, which is far outside the NDX/SOX training range. Any live use of it is extrapolation.

**H5 (descriptive only, structural break):** *The figures below include open episodes; corrected in Post-hoc diagnostics, item 3 (D6).*
- Median sessions from the -10% crossing to the trough:
  - SPX: 26 before 2018 vs 17 after.
  - NDX: 9 vs 3.5.
  - SOX: 5 vs 3.
- T1 at the -10% crossing:
  - SPX: 79% (n=47) vs 62% (n=8).
  - NDX: 62% vs 65%.
  - SOX: 49% vs 63%.

Post-2018 drawdowns reach their trough faster. For SOX they have also resolved upward more often. This shift alone is enough to break a 1995-2017 calibration.

---

## Exhibit 7. Live-test dashboard (registered 21 Nov 2026)

Frozen predictions: `results/live_frozen.csv`. State: `results/live_state.csv`. Figure: `results/fig_live.png`.

| | SPX | NDX | SOX |
|---|---|---|---|
| Close 20 Nov | 6,910.39 | 25,028.98 | 8,408.59 |
| Reference peak | 7,818.93 (6 Oct) | 31,224.47 (6 Oct) | 10,564.11 (11 Nov) |
| Depth | -11.6% | -19.8% | -20.4% |
| Deepest rung so far (this episode) | B10 (20 Nov) | B15 (19 Nov) | B20 (20 Nov) |
| Above 200d MA | no | no | no |
| Legs since all-time high | 0 | 0 | 3 |
| VIX / VIX >= 90th pct 5y | 35.89 / yes | | |
| VIX/VIX3M | 1.16 (above 1.0 since 17 Nov); **H2b has not fired** | | |
| Fed 6m stance (lagged) | neutral (+25bp < +50bp) | | |
| Baa-GS10 (latest usable, Sep) | 1.48 | | |
| H3 credit flag | 0, mechanically. The reference peak (Oct) is too recent for a lagged monthly change to exist, so the H3 construct cannot see this episode yet. This differs from the prompt's level-based "credit not confirming" read. | | |
| **T1 line from 5 Nov (0.90 x 5 Nov close)** | **6,618.36** | 23,966.83 | 8,110.03 |
| Breached yet? | no (min close 6,910.39) | no (25,028.98) | no (8,408.59) |
| **T1 line from 20 Nov (0.90 x 20 Nov close)** | **6,219.35** | 22,526.08 | 7,567.73 |
| Layer 0 P(T1), event on 5 Nov | **0.91** | 0.74 | 0.21 |
| Layer 0 P(T2), event on 5 Nov | 0.81 | 0.64 | 0.12 |
| Layer 0 P(T1), as of 20 Nov | **0.80** | 0.67 | **0.24** |
| Layer 0 P(T2), as of 20 Nov | 0.39 | 0.56 | 0.17 |
| Score dates (63 / 126 sessions after 5 Nov) | **2027-02-08 / 2027-05-10** | | |

The Layer 1-3 frozen probabilities are in `results/live_frozen.csv`. They are recorded as pre-registered, but every one of those layers is killed or underpowered, so they carry no weight.

The session counts assume the NYSE holidays listed in `src/live.py`, which I wrote from memory and have not verified. Check them against the published NYSE 2027 calendar before scoring.

---

## Exhibit 8. Data-gap register

| Gap | Effect | Status |
|---|---|---|
| Prompt's eight input files not attached | All inputs rebuilt from Yahoo/FRED; prompt checks reproduce | Logged (B1) |
| **Korea exports by product (semis vs total)** | **H4 not run.** A monthly HS 8541/8542 series reportedly exists **from 2000** (Trading Economics, sourced from Korea Customs Service, paid download). KCS, MOTIE, KITA, KOSIS and UN Comtrade are unreachable from this environment. | Open. Needs a manual download. |
| Korea first-20-days November 2026 print | Not found by 21 Nov. Latest found: 1-10 Nov total +111.9% YoY, chips +331.2% (KCS via Korea Times, 11 Nov). Sep 2026 per MOTIE: total $120.9B (+83.5%), chips $60.3B (+262.8%). Oct: total $115.3B (+93.7%), chips $56.4B (+259.4%). | Open; search snippets only |
| FRED NASDAQ100 1986-2005 vs Yahoo | ~360 disagreeing days; FRED appears date-shifted in 2003-2005. Yahoo used. | Logged (B1) |
| Real-time vintages (revisions) | FEDFUNDS, Baa and GS10 are rarely revised, but Korean exports (OECD MEI, SA) are revised and re-seasonally-adjusted. Latest vintage used with an m+2 lag; no ALFRED vintages. | Known look-ahead risk for H4-total |
| VIX OHLC early years; VIX3M before 2007-12 | Closes only; VIX3M from 2007-12-04 | By design |
| H2b history | Only 2007-2017 in training: 6-9 signals per asset | Underpowered; resolvable only with time |
| Options positioning, PB gross, retail flows | Excluded from v1 by design. Goldman PB gross (97th pct, 6 Nov) is single-source. | Not modelled |
| Mechanism classifier, valuation, international panel, single names | Excluded from v1 | Not modelled |
| NYSE 2027 holiday calendar | Used to date the scoring sessions; from memory | Verify before scoring |

---

## Falsifiable conclusion

**Claim.** After a fast drawdown, none of the measures tested here separates exhaustion from escalation better than where the index sits in its own drawdown:
- Fed stance.
- Volatility roll-over.
- VIX term-structure exit.
- VIX extremes.
- Credit confirmation.
- Korean export momentum.

The defensible content is the **per-asset escalation ladder**, and even the price-only baseline was mis-calibrated after 2018.

On that baseline, the live reading is:
- **SPX** is more likely contained than not: P(T1 from 20 Nov) = 0.80.
- **SOX** is more likely to fall a further 10% than not: P(T1) = 0.24. SOX has done this on 8 of 9 first shocks since 1995.

**What would overturn it, and when it is checked:**
1. **SPX, 63 sessions after 5 Nov (2027-02-08): an SPX close at or below 6,618.36 before then.** That fails the first-shock base rate (13 of 17 contained). Checked on 2027-02-08.
2. **SPX close at or below 6,219.35 within 63 sessions of 20 Nov (by ~2027-02-24).** That fails the Layer 0 T1 call of 0.80.
3. **SOX: no close at or below 7,567.73 within 63 sessions of 20 Nov (by ~2027-02-24).** That contradicts the SOX call; the base case is a further 10% fall.
4. **Method-level:** if a fresh pre-registered test in the next study finds any of H1-H4 with BH-surviving skill >= 0.02 that also holds out of sample, this study's null is wrong for that layer. The obvious candidates are H4 on the true non-semis series once it is obtained, and the H4-total YoY lead in exhibit 6.

The live rows get rescored by rerunning `python src/live.py` after 2027-02-24, and again after 2027-05-25 for the 126-session T2 check from 20 Nov.


---

## Post-hoc diagnostics (added after the hold-out; deviations D4-D9)

Nothing in this section changes a pre-registered result. The ledger, BH values, training verdicts and hold-out scorecard above stand as computed. Code: `src/posthoc.py`. Outputs: `results/posthoc/`.

### 1. Power: minimum detectable Brier-skill gain (D4)

**Method.**
- **Effective N:** training events are chained into one cluster whenever their [t, t+252]-session windows overlap.
- **Formula:** MDE = (1.96 + 0.84)^2 x p(1-p) / (N_eff x Brier_L0), at 80% power and two-sided alpha 0.05, where p is the training base rate. It comes from the Brier resolution term for the smallest detectable hit-rate difference.
- **Lower bound:** it ignores the cost of fitting the layer and any overlap with Layer 0, so the true MDE is higher.

**Effective N per asset** (training rows include the H2a signal rows):

| Asset | Event rows | Episodes | N_eff (252 chained) | Greedy non-overlapping 252 windows | N_eff (63 chained, T1 horizon) |
|---|---|---|---|---|---|
| SPX | 143 | 49 | **21** | 28 | 45 |
| NDX | 159 | 61 | **10** | 21 | 29 |
| SOX | 248 | 94 | **4** | 18 | 23 |
| Pooled, all three, same windows counted once | 416 (329 distinct dates) | | **21** | | |

**Pooling adds nothing.** The pooled N_eff of 21 equals SPX alone. NDX and SOX do add 11 clusters that start outside any SPX cluster, but their long chains (e.g. SOX 1995-2007 is one cluster) bridge separate SPX clusters by about as many, so the net count is unchanged.

**MDE (skill vs Layer 0) on N_eff** (full table with all 54 cells in `results/posthoc/power_mde.csv`):

| Layer | SPX T1 | SPX T2 | NDX T1 | NDX T2 | SOX T1 | SOX T2 |
|---|---|---|---|---|---|---|
| H1 | 0.40 | 0.38 | 1.01 | 0.94 | 2.10 | 2.10 |
| H2a | 0.40 | 0.37 | 1.09 | 1.00 | 2.11 | 2.18 |
| H2b | 2.61 | 2.48 | 1.76 | 2.05 | 3.20 | 3.62 |
| H2c | 2.01 | 1.82 | 1.58 | 1.44 | 2.10 | 2.10 |
| H3 | 0.40 | 0.38 | 1.01 | 0.94 | 2.10 | 2.10 |
| H4-total YoY | 0.56 | 0.54 | 1.01 | 0.94 | 2.10 | 2.10 |

An MDE above 1 means no achievable skill gain (skill can't exceed 1) could be detected at 80% power.

**Results.**
- **Every one of the 48 testable cells has MDE > 0.05.**
  - The smallest MDE on N_eff is **0.37**.
  - On greedy non-overlapping windows it is **0.28**.
  - Even treating every episode as independent, it is **0.089** (SOX).
- **Relabels:**
  - **40 pre-registered KILLs become "UNDERPOWERED"** in a new `posthoc_label` column.
  - The 8 pre-registered UNDERPOWERED cells stay as they are.
  - The 6 robustness rows are unchanged.
- **What the pre-registered bar implies:** the survival bar (skill >= 0.02) needed roughly 20 times more independent episodes than history provides.

**Reading.** The kills are absence of evidence, not evidence of absence. The one exception is the scale of the hold-out reversals (H3 SPX T1 at -0.24, H4-total d3 NDX T2 at -0.19). Those are large enough to matter, but they too sit inside the MDE.

### 2. Hold-out: Layer 0 vs constant, per asset (D5)

The constant is the training base rate for that asset and target. "Diff" = Brier(Layer 0) - Brier(constant); positive means the baseline is worse.

| Asset | Target | Rows | Episodes | N_eff (252) | Brier L0 | Brier const | Diff | 90% CI on N_eff clusters | 90% CI on episodes | Does "worse than constant" survive? |
|---|---|---|---|---|---|---|---|---|---|---|
| SPX | T1 | 20 | 8 | 5 | 0.193 | 0.188 | +0.005 | -0.014 to +0.030 | -0.018 to +0.032 | **No.** Point estimate only. |
| SPX | T2 | 20 | 8 | 5 | 0.239 | 0.230 | +0.009 | -0.043 to +0.066 | -0.044 to +0.068 | **No.** Point estimate only. |
| NDX | T1 | 30 | 17 | **1** | 0.247 | 0.243 | +0.004 | not testable | -0.049 to +0.065 | **No.** One cluster; episode CI includes 0. |
| NDX | T2 | 28 | 15 | **1** | 0.270 | 0.265 | +0.005 | not testable | -0.051 to +0.068 | **No.** One cluster; episode CI includes 0. |
| SOX | T1 | 58 | 30 | **1** | 0.303 | 0.265 | +0.038 | not testable | +0.002 to +0.075 | **Only on episode clusters**, which ignore 252-day overlap. Not testable on N_eff. |
| SOX | T2 | 50 | 26 | **1** | 0.347 | 0.287 | +0.060 | not testable | +0.028 to +0.090 | **Only on episode clusters.** Not testable on N_eff. |

**Statement.**
- The Layer 0 point estimate is worse than the constant in all six cells.
- **On N_eff the claim does not survive:**
  - SPX: N_eff 5, CI includes 0.
  - NDX and SOX: the 2018-2026 hold-out is one chained cluster, so N_eff = 1 and it can't be tested.
- **On episode clustering, only SOX** (T1 and T2) is significantly worse than constant. That is consistent with the level shift in exhibit 3 (hold-out T1 63% vs training 49%).
- **Correct wording:** "worse than constant" is a point-estimate observation for SPX and NDX, and a weak, overlap-sensitive result for SOX.

**Hold-out events, all of them** (Layer 0 and constant predictions; `results/posthoc/holdout_events.csv`). Censored targets are blank.

**SPX** (20 events)

| Date       | Event   |   Episode |   T1 |   L0 P(T1) |   Const P(T1) |   T2 |   L0 P(T2) |   Const P(T2) |
|:-----------|:--------|----------:|-----:|-----------:|--------------:|-----:|-----------:|--------------:|
| 2018-02-05 | A       |        49 |    1 |       0.91 |          0.74 |    1 |       0.81 |          0.56 |
| 2018-02-08 | B10     |        49 |    1 |       0.91 |          0.74 |    1 |       0.81 |          0.56 |
| 2018-11-23 | B10     |        50 |    0 |       0.80 |          0.74 |    0 |       0.40 |          0.56 |
| 2018-12-20 | B15     |        50 |    1 |       0.80 |          0.74 |    1 |       0.42 |          0.56 |
| 2020-02-27 | A       |        51 |    0 |       0.80 |          0.74 |    0 |       0.37 |          0.56 |
| 2020-02-27 | B10     |        51 |    0 |       0.80 |          0.74 |    0 |       0.37 |          0.56 |
| 2020-03-09 | B15     |        51 |    0 |       0.80 |          0.74 |    0 |       0.37 |          0.56 |
| 2020-03-12 | B20     |        51 |    1 |       0.79 |          0.74 |    1 |       0.37 |          0.56 |
| 2020-03-20 | B30     |        51 |    1 |       0.78 |          0.74 |    1 |       0.38 |          0.56 |
| 2022-02-22 | B10     |        52 |    1 |       0.80 |          0.74 |    0 |       0.39 |          0.56 |
| 2022-04-29 | B10     |        53 |    0 |       0.76 |          0.74 |    0 |       0.44 |          0.56 |
| 2022-05-11 | B15     |        53 |    1 |       0.76 |          0.74 |    1 |       0.45 |          0.56 |
| 2022-05-18 | A       |        53 |    1 |       0.76 |          0.74 |    1 |       0.45 |          0.56 |
| 2022-06-16 | B20     |        53 |    1 |       0.76 |          0.74 |    1 |       0.47 |          0.56 |
| 2022-09-16 | B10     |        54 |    1 |       0.67 |          0.74 |    1 |       0.50 |          0.56 |
| 2022-09-26 | B15     |        54 |    1 |       0.68 |          0.74 |    1 |       0.50 |          0.56 |
| 2023-10-27 | B10     |        55 |    1 |       0.80 |          0.74 |    1 |       0.60 |          0.56 |
| 2025-03-13 | B10     |        56 |    1 |       0.80 |          0.74 |    1 |       0.37 |          0.56 |
| 2025-04-03 | A       |        56 |    1 |       0.80 |          0.74 |    1 |       0.39 |          0.56 |
| 2025-04-04 | B15     |        56 |    1 |       0.80 |          0.74 |    1 |       0.39 |          0.56 |

**NDX** (30 events)

| Date       | Event   |   Episode |   T1 |   L0 P(T1) |   Const P(T1) |   T2 |   L0 P(T2) |   Const P(T2) |
|:-----------|:--------|----------:|-----:|-----------:|--------------:|-----:|-----------:|--------------:|
| 2018-02-08 | B10     |        62 |    1 |       0.80 |          0.52 |    1 |       0.70 |          0.45 |
| 2018-04-02 | B10     |        63 |    1 |       0.80 |          0.52 |    1 |       0.70 |          0.45 |
| 2018-10-24 | B10     |        64 |    0 |       0.79 |          0.52 |    0 |       0.69 |          0.45 |
| 2018-12-17 | B15     |        64 |    1 |       0.73 |          0.52 |    1 |       0.62 |          0.45 |
| 2018-12-21 | B20     |        64 |    1 |       0.65 |          0.52 |    1 |       0.54 |          0.45 |
| 2019-06-03 | B10     |        65 |    1 |       0.79 |          0.52 |    1 |       0.69 |          0.45 |
| 2020-02-27 | B10     |        66 |    0 |       0.76 |          0.52 |    0 |       0.66 |          0.45 |
| 2020-03-09 | A       |        66 |    0 |       0.69 |          0.52 |    0 |       0.59 |          0.45 |
| 2020-03-09 | B15     |        66 |    0 |       0.69 |          0.52 |    0 |       0.59 |          0.45 |
| 2020-03-12 | B20     |        66 |    1 |       0.57 |          0.52 |    1 |       0.47 |          0.45 |
| 2020-03-16 | B10     |        67 |    1 |       0.53 |          0.52 |    1 |       0.43 |          0.45 |
| 2020-09-08 | B10     |        68 |    1 |       0.79 |          0.52 |    1 |       0.69 |          0.45 |
| 2021-03-08 | B10     |        69 |    1 |       0.79 |          0.52 |    1 |       0.69 |          0.45 |
| 2022-01-20 | B10     |        70 |    0 |       0.80 |          0.52 |    0 |       0.70 |          0.45 |
| 2022-01-27 | B15     |        70 |    1 |       0.73 |          0.52 |    0 |       0.63 |          0.45 |
| 2022-03-14 | B20     |        70 |    0 |       0.64 |          0.52 |    0 |       0.54 |          0.45 |
| 2022-04-22 | B10     |        71 |    0 |       0.67 |          0.52 |    0 |       0.57 |          0.45 |
| 2022-04-29 | B15     |        71 |    0 |       0.62 |          0.52 |    0 |       0.52 |          0.45 |
| 2022-05-09 | B20     |        71 |    1 |       0.55 |          0.52 |    1 |       0.45 |          0.45 |
| 2022-08-31 | B10     |        72 |    0 |       0.56 |          0.52 |    0 |       0.46 |          0.45 |
| 2022-09-22 | B15     |        72 |    1 |       0.47 |          0.52 |    1 |       0.39 |          0.45 |
| 2022-10-10 | B20     |        72 |    1 |       0.41 |          0.52 |    1 |       0.34 |          0.45 |
| 2022-12-27 | B10     |        73 |    1 |       0.40 |          0.52 |    1 |       0.33 |          0.45 |
| 2023-10-26 | B10     |        74 |    1 |       0.79 |          0.52 |    1 |       0.69 |          0.45 |
| 2024-08-02 | B10     |        75 |    1 |       0.79 |          0.52 |    1 |       0.69 |          0.45 |
| 2025-03-10 | B10     |        76 |    0 |       0.78 |          0.52 |    0 |       0.67 |          0.45 |
| 2025-04-03 | B15     |        76 |    1 |       0.72 |          0.52 |    1 |       0.61 |          0.45 |
| 2025-04-04 | B20     |        76 |    1 |       0.64 |          0.52 |    1 |       0.53 |          0.45 |
| 2026-03-27 | B10     |        77 |    1 |       0.79 |          0.52 |      |     nan    |        nan    |
| 2026-07-29 | B10     |        78 |    1 |       0.79 |          0.52 |      |     nan    |        nan    |

**SOX** (58 events)

| Date       | Event   |   Episode |   T1 |   L0 P(T1) |   Const P(T1) |   T2 |   L0 P(T2) |   Const P(T2) |
|:-----------|:--------|----------:|-----:|-----------:|--------------:|-----:|-----------:|--------------:|
| 2018-02-08 | B10     |        97 |    1 |       0.42 |          0.42 |    1 |       0.19 |          0.31 |
| 2018-03-28 | B10     |        98 |    1 |       0.42 |          0.42 |    1 |       0.20 |          0.31 |
| 2018-10-10 | B10     |        99 |    0 |       0.16 |          0.42 |    0 |       0.19 |          0.31 |
| 2018-10-24 | B15     |        99 |    1 |       0.16 |          0.42 |    1 |       0.16 |          0.31 |
| 2018-10-24 | B20     |        99 |    1 |       0.16 |          0.42 |    1 |       0.16 |          0.31 |
| 2018-12-19 | B10     |       100 |    1 |       0.23 |          0.42 |    1 |       0.21 |          0.31 |
| 2018-12-24 | B15     |       100 |    1 |       0.22 |          0.42 |    1 |       0.18 |          0.31 |
| 2019-05-13 | B10     |       101 |    1 |       0.42 |          0.42 |    1 |       0.20 |          0.31 |
| 2019-05-20 | B15     |       101 |    1 |       0.41 |          0.42 |    1 |       0.18 |          0.31 |
| 2019-08-05 | B10     |       102 |    1 |       0.43 |          0.42 |    1 |       0.19 |          0.31 |
| 2020-02-25 | B10     |       103 |    0 |       0.43 |          0.42 |    0 |       0.19 |          0.31 |
| 2020-02-27 | B15     |       103 |    0 |       0.43 |          0.42 |    0 |       0.17 |          0.31 |
| 2020-03-09 | A       |       103 |    0 |       0.21 |          0.42 |    0 |       0.15 |          0.31 |
| 2020-03-09 | B20     |       103 |    0 |       0.21 |          0.42 |    0 |       0.15 |          0.31 |
| 2020-03-16 | B10     |       104 |    1 |       0.23 |          0.42 |    1 |       0.18 |          0.31 |
| 2020-03-16 | B15     |       104 |    1 |       0.23 |          0.42 |    1 |       0.18 |          0.31 |
| 2020-09-08 | B10     |       105 |    1 |       0.43 |          0.42 |    1 |       0.20 |          0.31 |
| 2021-03-04 | B10     |       106 |    1 |       0.42 |          0.42 |    1 |       0.19 |          0.31 |
| 2021-05-10 | B10     |       107 |    1 |       0.40 |          0.42 |    0 |       0.20 |          0.31 |
| 2022-01-19 | B10     |       108 |    0 |       0.41 |          0.42 |    0 |       0.20 |          0.31 |
| 2022-01-25 | B15     |       108 |    0 |       0.21 |          0.42 |    0 |       0.17 |          0.31 |
| 2022-02-23 | B10     |       109 |    0 |       0.22 |          0.42 |    0 |       0.21 |          0.31 |
| 2022-03-07 | B15     |       109 |    1 |       0.21 |          0.42 |    0 |       0.18 |          0.31 |
| 2022-04-06 | B10     |       110 |    0 |       0.23 |          0.42 |    0 |       0.20 |          0.31 |
| 2022-04-11 | B15     |       110 |    0 |       0.23 |          0.42 |    0 |       0.18 |          0.31 |
| 2022-04-27 | B20     |       110 |    0 |       0.22 |          0.42 |    0 |       0.16 |          0.31 |
| 2022-06-10 | B10     |       111 |    0 |       0.24 |          0.42 |    0 |       0.22 |          0.31 |
| 2022-06-13 | B15     |       111 |    1 |       0.24 |          0.42 |    1 |       0.19 |          0.31 |
| 2022-07-01 | B20     |       111 |    1 |       0.22 |          0.42 |    1 |       0.16 |          0.31 |
| 2022-08-29 | B10     |       112 |    0 |       0.23 |          0.42 |    0 |       0.22 |          0.31 |
| 2022-09-02 | B15     |       112 |    0 |       0.23 |          0.42 |    0 |       0.19 |          0.31 |
| 2022-09-22 | B20     |       112 |    0 |       0.21 |          0.42 |    0 |       0.17 |          0.31 |
| 2022-12-22 | B10     |       113 |    1 |       0.24 |          0.42 |    1 |       0.23 |          0.31 |
| 2023-04-25 | B10     |       114 |    1 |       0.46 |          0.42 |    1 |       0.23 |          0.31 |
| 2023-08-17 | B10     |       115 |    1 |       0.48 |          0.42 |    1 |       0.24 |          0.31 |
| 2023-10-25 | B15     |       115 |    1 |       0.20 |          0.42 |    1 |       0.20 |          0.31 |
| 2024-04-17 | B10     |       116 |    1 |       0.40 |          0.42 |    0 |       0.20 |          0.31 |
| 2024-04-19 | B15     |       116 |    1 |       0.39 |          0.42 |    0 |       0.17 |          0.31 |
| 2024-07-19 | B10     |       117 |    0 |       0.43 |          0.42 |    0 |       0.20 |          0.31 |
| 2024-07-25 | B15     |       117 |    0 |       0.42 |          0.42 |    0 |       0.18 |          0.31 |
| 2024-08-02 | B20     |       117 |    1 |       0.41 |          0.42 |    1 |       0.15 |          0.31 |
| 2024-09-06 | B10     |       118 |    1 |       0.22 |          0.42 |    1 |       0.19 |          0.31 |
| 2024-11-15 | B10     |       119 |    1 |       0.21 |          0.42 |    1 |       0.21 |          0.31 |
| 2025-01-27 | A       |       120 |    0 |       0.24 |          0.42 |    0 |       0.21 |          0.31 |
| 2025-01-27 | B10     |       120 |    0 |       0.24 |          0.42 |    0 |       0.21 |          0.31 |
| 2025-03-03 | B15     |       120 |    0 |       0.21 |          0.42 |    0 |       0.18 |          0.31 |
| 2025-03-11 | B20     |       120 |    0 |       0.21 |          0.42 |    0 |       0.17 |          0.31 |
| 2025-04-04 | B30     |       120 |    1 |       0.19 |          0.42 |    1 |       0.12 |          0.31 |
| 2025-04-21 | B10     |       121 |    1 |       0.24 |          0.42 |    1 |       0.22 |          0.31 |
| 2025-11-18 | B10     |       122 |    1 |       0.42 |          0.42 |    1 |       0.20 |          0.31 |
| 2025-12-17 | B10     |       123 |    1 |       0.43 |          0.42 |      |     nan    |        nan    |
| 2026-03-06 | B10     |       124 |    1 |       0.43 |          0.42 |      |     nan    |        nan    |
| 2026-03-30 | B15     |       124 |    1 |       0.40 |          0.42 |      |     nan    |        nan    |
| 2026-06-05 | A       |       125 |    0 |       0.44 |          0.42 |      |     nan    |        nan    |
| 2026-06-05 | B10     |       125 |    0 |       0.44 |          0.42 |      |     nan    |        nan    |
| 2026-07-02 | B10     |       126 |    0 |       0.43 |          0.42 |      |     nan    |        nan    |
| 2026-07-07 | B15     |       126 |    0 |       0.42 |          0.42 |      |     nan    |        nan    |
| 2026-07-17 | B20     |       126 |    0 |       0.41 |          0.42 |      |     nan    |        nan    |

### 3. H5: pre/post-2018 descriptive comparison (D6)

Descriptive only, no inference. Completed episodes only: open episodes are excluded because their trough is not final. T1 is measured at the -10% crossing.

| Asset | Period | Episodes | Median sessions B10 to trough (IQR) | Trough on the B10 day | Median max depth | T1 rate (90% Wilson) |
|---|---|---|---|---|---|---|
| SPX | pre-2018 | 47 | 26 (3-56) | 17% | -15.4% | 79% (67-87%), n=47 |
| SPX | 2018+ | 8 | 17.5 (8-18) | 25% | -17.9% | 63% (35-84%), n=8 |
| NDX | pre-2018 | 61 | 9 (1-22) | 25% | -15.3% | 62% (52-72%), n=61 |
| NDX | 2018+ | 17 | 3 (0-21) | 35% | -12.5% | 65% (45-81%), n=17 |
| SOX | pre-2018 | 94 | 5 (1-14) | 21% | -16.3% | 49% (41-57%), n=94 |
| SOX | 2018+ | 32 | 4.5 (2-14) | 25% | -15.8% | 63% (48-76%), n=30 |

**Correction to exhibit 6.** That text gave post-2018 medians of 17 / 3.5 / 3 sessions, which included open episodes. Excluding them gives **17.5 / 3 / 4.5**.

**Reading.**
- **Faster troughs:** visible for SPX and NDX in the medians. **Not for SOX** (5 vs 4.5).
- **T1 rates:** every 90% interval overlaps across periods. The SOX rise (49% to 63%) is the largest move, but with 30 hold-out episodes it is not distinguishable from noise.

### 4. Data checks (D7)

| Check | Result |
|---|---|
| VIX3M start in `MANIFEST.csv` | **2006-07-17** for the raw Yahoo file, which includes back-calculated pre-launch values. MANIFEST does *not* show 2007-12-04 for this file. FRED VXVCLS (the cross-check) starts 2007-12-04. |
| VIX3M actually used | Processed series starts **2007-12-04** (cut in `src/ingest.py`, asserted in `tests/test_data.py`). The first VIX/VIX3M ratio is 2007-12-04 for all assets; the first H2b signal is 2007-12-18. **0 rows of 2006-07 to 2007-12 data enter any feature.** |
| Korean-export look-ahead | `kr_yoy` / `kr_d3` are used only in the **H4-total** layers and the H4 incremental check (`h4_incremental.csv`). Not in Layer 0, and not in any live frozen model (L0, H1, H2b, H2c, H3). `events_*.csv` and `live_state.csv` print the value for description only. **Confirmed: the revision look-ahead affects only H4-total.** |
| Other monthly series | FEDFUNDS, BAA and GS10 also use the latest vintage, but they are not revised in practice. |

### 5. Step 0 rescored (D8)

| Item | Original scoring | Post-hoc rescoring |
|---|---|---|
| $500M data-centre loan auction (bids 19 Nov) | Neither flip triggered (no print) | **No clear = failed financing; thesis-side, provisional (single source: Bloomberg 20 Nov, via search snippet).** |
| Rebound leadership (5 up days) | Incomplete, leaning flush (suppliers +24.7% vs builders +2.1% over 3 up days) | **Inconclusive: 3 up days, 5 required.** |

### 6. Limitations (D9)

- **H1 measured past Fed stance, not policy reversal.** The feature is the lagged 6-month FEDFUNDS change, bucketed at ±50bp, known at t with an m+2 lag. It says nothing about a real-time pivot (a first cut, or the market pricing one) during the drawdown, which is the mechanism usually argued for exhaustion. A null on H1 is not a null on "the Fed put".
- **A credit x policy interaction is post-hoc and untestable here.** The idea is that credit non-confirmation matters only when policy is easing (or tightening). It was not pre-registered. It would split N_eff of 4-21 into four cells, which is far below the MDE in item 1. It should not be inferred from the H3 or H1 tables.
- **Power (item 1)** is the binding limitation of the whole study. The pre-registered survival bar sat well below what the sample could detect.
