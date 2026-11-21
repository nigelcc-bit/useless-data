# Study 3: The Exhaustion Model -- PRE-REGISTRATION

Registered 21 Nov 2026. Folder `studies/2026-11-exhaustion-model/`.

This file is committed **before any outcome statistic is computed** (no target, forward return,
hit rate, Brier score or test statistic has been calculated at the time of this commit; only the
data gates in `tests/test_data.py` and the shock-threshold percentile in Part B, which is a
definition and uses no forward data). Any later change is logged in Part D with date and reason;
the original text stays.

Part A reproduces sections 4 to 7 of the study prompt verbatim. Part B lists data-forced edits.
Part C fixes the operational details the prompt leaves open; they were written before any
outcome was computed and are binding. Part D is the deviation log.

Question: after a fast equity drawdown, what separates the episodes where selling exhausts and a
durable rally follows from the ones that escalate?

---

# Part A. Prompt sections 4 to 7 (verbatim)

## 4. Episodes and targets (pre-registered)

Assets: SPX (from 1954-07 where the Fed series starts; price features from 1950), NDX (1985+), SOX (1994+). Modelled separately. Pooled results only with clustering by overlapping calendar windows.

**Event family A, first shocks.**
- SPX: daily close-to-close return <= -4%. Compute that threshold's percentile in the SPX full-sample daily return distribution; NDX and SOX use the same percentile of their own distributions.
- First shock = no other shock in the prior 126 sessions.
- Record distance from the 252-session high at the shock.

**Event family B, swing drawdown crossings.**
- Reference peak = highest close since the last reset. Event = first close <= 0.90 x reference peak.
- Reset when the close rebounds >= 10% off the episode trough, or makes a new high. The next reference peak is then tracked from the reset. (This deliberately splits long bears into separate legs, so failed bear-market rallies become events. Peak-to-recovery counting merges NDX 2000-2015 into one episode and is NOT used.)
- Also record -15%, -20%, -30% crossings within each episode (escalation ladder).

**Targets, evaluated at the event or signal date t:**
- **T1 "contained"**: min close over (t, t+63] > 0.90 x close(t). (Blue Tsunami's "fell a further 10%+" metric, inverted.)
- **T2 "rally holds"**: close(t+252) > close(t) AND T1.
- Also report continuous forward returns at 21, 63, 252 sessions and the max further drawdown within 63.

## 5. Model layers (pre-registered)

**Layer 0, baseline (the thing to beat).** Features at t: depth from reference peak; distance from 252-session high; above/below 200-session moving average; episode duration (sessions since reference peak); leg count (number of 10% rebounds since the last all-time high). Output: conditional frequency tables (depth bucket x trend state) and a logistic model choosing at most 3 of these by LOEO Brier, chosen on the training set only.

**Layer 1, regime.** H1 Fed stance: FEDFUNDS change over the prior 6 months (lagged per section 1): tightening >= +50bp, easing <= -50bp, else neutral. Midterm-note rule adapted to a rolling window.

**Layer 2, timing.** Price-derived; counted as one family.
- H2a Realised-vol roll: 20-session realised vol falls >= 20% below its max of the prior 20 sessions while price is still in the episode.
- H2b VIX/VIX3M exit: after >= 3 consecutive closes with VIX/VIX3M > 1.0, the first close < 1.0 is the signal (2007+). One alternative threshold (0.95) may be logged as a separate ledger test; no other tuning.
- H2c VIX percentile: VIX close at or above its 90th percentile of the prior 5 years (1990+).

**Layer 3, durability.**
- H3 Credit confirmation: change in Baa-GS10 from the month before the reference peak to the latest available month at t, divided by drawdown depth at t. Below the training-set median = "credit not confirming". Daily `BAA10Y` version for 1986+ as robustness.
- H4 Korea non-semis exports: YoY growth of (total minus semiconductor) exports and its 3-month change, lagged. Must show incremental value over the asset's own 63-session return (partial correlation, and LOEO Brier gain). If the product split is unavailable before some year, run H4 only on that window and say so. If H4 adds nothing over SOX, report it as a kill.
- H5 (descriptive only, no inference) structural break: compare sessions-to-trough and T1 rates for episodes before vs after 2018-01-01.

**Excluded from v1 (state in the report):** valuation, mechanism classifier (needs long supplier/customer baskets), PB gross, retail flows, options, international panel, single-name module.

## 6. Evaluation (pre-registered)

- Leave-one-episode-out CV on the training set. Metrics: Brier score, Brier skill vs Layer 0, calibration plot, hit rate per bucket with Wilson intervals.
- A layer **survives** only if: Brier skill vs Layer 0 >= 0.02 in LOEO, the sign of the effect agrees across at least 2 of 3 assets, the sign agrees in both halves of the training sample (pre/post 1990 for SPX), and its permutation p-value survives BH at q = 0.10 across the ledger.
- Never report significance on a cell with fewer than 8 events; show counts instead.
- Then run the hold-out once. Report hold-out Brier vs Layer 0 with the episode list (expected to include Q4-2018, Feb-Mar 2020, 2022 legs, Apr 2025, the 2026 episodes).

## 7. Live test (pre-registered today, 21 Nov 2026)

State at registration (verified unless starred):
- SPX: first shock 5 Nov 2026 close 7,353.73 (-4.36%). **Fails the first-shock-near-highs base rate if SPX closes below 6,618 (= 0.90 x 7,353.73) within 63 sessions of 5 Nov (about early Feb 2027).** SPY 715.87 on 19 Nov, -8.1% from 779.09 (6 Oct).
- SOX: 8,408.59 on 20 Nov, -42.5% from 14,634.72 (22 Jun), -10.7% on the day, below the 5 Nov close 9,011.14. Escalation cell.
- VIX 35.89 (20 Nov, 96.5th percentile since 1990); VIX/VIX3M 1.16, inverted since 17 Nov (inversion on 10.1% of days since 2007). **H2b signal has NOT fired.**
- Baa-GS10 1.46pp (Oct average; 1.6th percentile since 2000). Credit not confirming.
- Korean exports +83.7% YoY (Sep); semis > half of the total (single month, Trading Economics).
- Fed funds 3.63 -> 3.88 (tightening; Dec hike priced*).
- Starred: CRWV CDS ~1,067-1,195bp; Goldman PB gross 97th percentile of 5y (6 Nov).

Score at 63 and 126 sessions after 5 Nov for SPX/NDX/SOX: T1, the H2b signal date if any, and the Layer 0 to 3 predicted probabilities as frozen on the registration commit.

---

# Part B. Data-forced edits (made before any outcome was computed)

B1. **Input files were not supplied.** The eight files listed in prompt section 2 were not attached
to the session. Every raw file was rebuilt from public sources and logged in
`data/raw/MANIFEST.csv` (URL, pull time, rows, sha256):
- SPX, NDX, SOX, VIX, VIX3M daily closes: Yahoo Finance chart API (`^GSPC`, `^NDX`, `^SOX`,
  `^VIX`, `^VIX3M`), pulled 21 Nov 2026, through 20 Nov 2026. File names kept as in the prompt.
  SPX and NDX therefore already run to 20 Nov; no proxy (SPY/QQQ) is needed.
- FEDFUNDS, BAA, GS10 (monthly), BAA10Y, VIXCLS, VXVCLS, NASDAQ100, SP500 (daily): FRED,
  pulled 21 Nov 2026. Baa-GS10 is computed as BAA minus GS10 (range 0.29 to 6.01, Oct 2026 1.46,
  matching the prompt).
- Korean exports: FRED `XTEXVA01KRM667S` (OECD MEI, exports of goods, USD, SA, 1957-01 to
  2026-09). The NSA and KRW columns of the prompt's file are not used.
- All prompt validation checks pass on the rebuilt data (`tests/test_data.py`): 1987-10-19 SPX
  -20.5%, NDX -15.1%; SOX min 2020-03-16 -15.9%, max 2025-04-09 +18.7%; SOX peak 14,634.72 on
  2026-06-22; SOX-SPX daily return correlation 0.71 +/- 0.04; registration-state values in
  section 7 (SPX 5 Nov 7,353.73 -4.36%; SOX 20 Nov 8,408.59; VIX 35.89; VIX/VIX3M 1.16).
- Yahoo VIX has ~330 holiday-dated null rows; rows not on the SPX calendar are dropped.
  Yahoo VIX3M is truncated to start 2007-12-04 (official history start) and checked against
  FRED VXVCLS.
- NDX: FRED `NASDAQ100` disagrees with Yahoo on ~360 days in 1986-2005 (2003-2005 FRED values
  appear date-shifted; Yahoo 2003-12-31 = 1,467.92 matches the published close). Yahoo is used;
  the two agree from 2006. Recorded in the data-gap register.

B2. **Shock thresholds (family A).** The SPX -4% close-to-close threshold is at the
**0.2947th percentile** of SPX daily returns 1950-01-04 to 2026-11-20 (57 of 19,344 days). The
same percentile gives **NDX -6.35%** (1985-10 to 2026-11) and **SOX -8.15%** (1994-05 to 2026-11).
These are definitions (no forward data used). The full-sample percentile includes hold-out
returns, as the prompt specifies; this is a threshold definition only.

B3. **Korea product split (H4).** The semiconductor/total product split was not obtainable from
this environment (Korea Customs Service, MOTIE, KITA, KOSIS, UN Comtrade and Trading Economics
hosts are all blocked by the network policy). Web search indicates a monthly HS 8541/8542 series
exists from 2000 (Trading Economics, sourced from Korea Customs Service, paid download); the
product-split start date for the data-gap register is therefore "2000, not obtained". H4 as specified (non-semis exports) **cannot be
run** and is recorded as NOT RUN (data gap), which is neither a kill nor a survivor. As a
data-forced substitute, **H4-total** uses total Korean exports (USD, SA) with exactly the H4
construction (YoY growth and its 3-month change, lagged m+2) and the same incremental-value
requirement over the asset's own 63-session return. Because semis are now more than half of
Korean exports, H4-total is a weaker proxy for the "non-semis" idea; a null for H4-total does not
kill H4.

B4. **H2c history.** VIX begins 1990-01-02, so the 5-year trailing percentile is first available
in early 1995 (1,260 prior VIX sessions required). H2c is evaluated only on events from then on.

---

# Part C. Operational definitions (binding; written before any outcome was computed)

## C1. Samples
- SPX: closes from 1950-01-03. Events from **1954-09-01** (first date a lagged FEDFUNDS value is
  usable), so every layer that can be computed uses the same SPX event set.
- NDX events from 1986-10-01 and SOX events from 1995-05-01 (252-session warm-up).
- **Training**: event date t <= 2017-12-31. **Hold-out**: 2018-01-01 <= t <= 2026-11-20. Training
  targets that need prices after 2017-12-31 still use them (prompt: train through 2017-12-31 by
  event date); this is noted as a minor overlap. Hold-out events whose target window is not yet
  complete are censored for that target and move to the live test.
- The hold-out is run **once**, by `src/evaluate.py --holdout`, only after the training verdicts
  are committed. A line recording the unlock is added to Part D before the run.

## C2. Episode engine (family B)
State machine on closes, per asset:
- Out of episode: reference peak P = highest close since the last reset (initially since the
  first close). When close <= 0.90 P, a **B10 event** fires and the episode starts; trough
  = running min close from then on.
- In episode: record **B15, B20, B30** at the first close <= 0.85 P, 0.80 P, 0.70 P.
- **Reset** when close >= 1.10 x trough ("rebound reset") or close > P ("new-high reset").
  After a reset, P is tracked afresh from the reset close.
- **Episode span** = [date of P, reset date] (open if no reset yet).
- **Leg count** at t = number of rebound resets since the last all-time high close (all-time
  over the asset's own history in the file).
- **Ladder events** B10/B15/B20/B30 are all modelling rows. Rows from the same episode share an
  episode id and are always left out together in LOEO and kept together in permutations.

## C3. Family A first shocks
- Shock = daily close-to-close return <= the asset threshold in B2. First shock = no other shock
  in the prior 126 sessions.
- A first shock whose date falls inside a family-B episode span takes that episode id; otherwise
  it gets its own id. If a first shock occurs before a B10 crossing within the same P (i.e. in
  the run-up to the crossing), it belongs to the episode that P starts if that episode crosses
  -10% within 63 sessions; otherwise its own id.
- Family A and family B rows are modelled together (one dataset per asset), with a row-type
  indicator recorded but **not** used as a feature (so Layer 0 stays the five prompt features).
  Exhibits report each family separately.

## C4. Layer 0 features at t
1. `depth` = close(t) / P - 1, with P the current reference peak of the episode engine.
2. `dist252` = close(t) / max(close over the 252 sessions ending t) - 1.
3. `above200` = 1 if close(t) > 200-session simple moving average of closes ending t, else 0.
4. `duration` = sessions from the date of P to t.
5. `legs` = leg count (C2).
Continuous features are standardised with training-set mean and sd (per asset, per fit).
Conditional tables: depth buckets (> -10%, -10 to -15%, -15 to -20%, -20 to -30%, <= -30%)
x trend state (above/below 200-session MA).

## C5. Model
- Bayesian logistic regression, priors Normal(0, 1) on standardised slopes, Normal(0, 2.5) on the
  intercept. Fit by MAP (Newton-Raphson); predictive probability by Laplace approximation with
  the probit (MacKay) correction. No other model class.
- **Layer 0 selection**: all subsets of the five features of size 1 to 3 (25 models) are scored by
  LOEO Brier on the training set; the best is Layer 0. Separately per asset and per target.
- **Layer k model** = best **2-feature** Layer 0 subset (by LOEO Brier) + the layer's single
  feature (3 features). It is compared with the full Layer 0 (best of 25). The Layer 0 score is
  optimistically selected, so this comparison is conservative against the layer.
- Brier skill vs Layer 0 = 1 - Brier(layer k, LOEO) / Brier(Layer 0, LOEO).

## C6. Layer features (one per test)
- **H1** `fed6m` = +1 if FEDFUNDS(m) - FEDFUNDS(m-6) >= +0.50, -1 if <= -0.50, else 0, with m the
  latest month usable at t under the m+2 rule.
- **H2a** row-augmented. Signal date = first session inside an episode (after B10, before reset)
  where 20-session realised vol (sd of daily log returns x sqrt(252)) <= 0.80 x its max over the
  prior 20 sessions. Signal dates are added as rows (with all Layer 0 features at that date and
  the episode's id); the layer feature is 1 on signal rows and 0 on all other rows. Layer 0 is
  refit on the same augmented rows for the comparison.
- **H2b** row-augmented, same mechanics. Signal = first close with VIX/VIX3M < 1.00 after >= 3
  consecutive closes > 1.00, occurring while the asset is inside an episode. 2007-12+ only.
  **H2b-095** = same with 0.95 for both thresholds; a separate ledger test, no other variants.
  VIX/VIX3M is market-wide and is used unchanged for NDX and SOX.
- **H2c** `vixhi` = 1 if VIX(t) >= 90th percentile of VIX over the prior 1,260 sessions.
- **H3** `credit_nc` = 1 if credit is "not confirming": ratio (Baa-GS10 latest usable month at t
  minus Baa-GS10 in the month before the month of P) / |depth(t)| is below its training-set
  median (per asset), else 0. Monthly values usable from m+2. **H3-daily** (robustness, ledger
  test, not a verdict input): same with daily BAA10Y at t-1 and at the session before P, 1986+.
- **H4-total** `kr_yoy`, `kr_d3`: YoY growth of total exports (m+2 lag) and its 3-month change.
  The layer feature is `kr_yoy`; `kr_d3` is a second ledger test. Incremental value: (i) partial
  correlation of the feature with the target controlling for the asset's 63-session return at t;
  (ii) LOEO Brier of (best-2 Layer 0 + ret63 + feature) vs (best-2 Layer 0 + ret63). Data from
  1970. Kill if neither shows gain.
- **H5** descriptive only.

## C7. Tests and survival
- Each (hypothesis, asset, target) is one ledger row. Statistic = LOEO Brier skill vs Layer 0.
  **Permutation p-value**: the layer feature is shuffled across episodes (whole-episode blocks:
  each episode's rows receive the feature vector of a randomly drawn episode with the same row
  structure where possible, otherwise rows are permuted within row type), 999 draws, p = (1 +
  #{permuted skill >= observed}) / 1000. Fixed seed 20261121.
- **Survives** (per asset and target) only if all hold: (a) Brier skill >= 0.02; (b) the sign of
  the layer coefficient (full training fit) agrees in at least 2 of 3 assets; (c) the sign agrees
  in both halves of the training sample (SPX: events before / from 1990-01-01; NDX and SOX: split
  at the median training episode start date); (d) BH-adjusted permutation p <= 0.10 across the
  whole ledger.
- Fewer than 8 training **episodes** with the feature available (or, for binary features, fewer
  than 8 rows in either class) = **UNDERPOWERED**: counts only, no p-value is reported as
  significant, verdict "prior only".
- Inherited-threshold tests (ledger, `inherited_from` filled), training sample, Fisher exact:
  I1 first shock within 5% of 252-session high vs not, T1 (Blue Tsunami Flush);
  I2 first shock more than 10% below 252-session high vs not, "fell a further 10%+" = not T1
  (Blue Tsunami Flush); I3 VIX >= 35 at the event vs < 35, T1 (JPM VIX 35 level via Blue
  Tsunami desk color). Per asset.
- BH at q = 0.10 is applied once over every p-value in `ledger.csv` (training tests), and once
  more over training + hold-out rows after the hold-out run; both reported.

## C8. Live test
- Frozen live predictions (Layer 0 to 3 for T1 and T2, per asset, at the 5 Nov 2026 SPX first
  shock date and at 20 Nov 2026) are written to `results/live_frozen.csv` and committed before
  any live outcome exists. Scoring dates: 63 and 126 sessions after 5 Nov 2026.


---

# Part D. Deviation log

(none yet)
