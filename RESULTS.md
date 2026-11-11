# RESULTS — Flush or regime change?

**What would change the book** (why this study exists):

- **If H2 and H5 hold and L(5) is positive** → flush; supplier-heavy book is positioned correctly; patience. **Outcome #1 can no longer trigger:** H2 was required and is **killed (K004)** — seesaw is description, not signal.
- **If H4 rejects stability and the layer dummy dominates in November** → profit pool moved toward builders; a book with zero builder exposure is one bet expressed ten ways. **Outcome #2 triggered (H4).**
- **If H1 shows semis have a materially worse continuation base rate than the S&P** → the 6 Nov "don't sell into the hole" inference does not apply to this book; size differently before the next leg.
- **If H3 flips and valuation dominates** → crowding framework from July/October/November is wrong; three prior notes need retracting.

### Outcomes scorecard (pre-registered)

| # | Pre-registered outcome | Status |
|---|---|---|
| 1 | H2 + H5 hold and L(5) > 0 → flush / patience | **Cannot trigger** — H2 killed (K004); H5 **PRIOR ONLY** (OOS N=4) |
| 2 | H4 rejects + layer dominates November → profit pool to builders | **Triggered** |
| 3 | H1 semis worse continuation than S&P → Call 5 does not apply | Settled via H1b/K002 (Call 5 does not transfer; H1b inconclusive) |
| 4 | H3 flips, valuation dominates → retract crowding notes | **Not triggered** — H3 UNSUPPORTED (K003); neither block wins |

Fill **Result** and **Decision** only after code runs. Do not edit hypotheses after seeing results.

| ID | Hypothesis | Null | Decision rule / falsifier | Result | Decision |
|---|---|---|---|---|---|
| H1 | Semis do not inherit S&P benign first-shock base rate | Conditional first-shock near-high fwd distribution indistinguishable from S&P | Further 10%+ DD frequency within bootstrap CI of S&P → Call 5 extends | Near-high first-shock cell underpowered (T002 NOT_RUN); **H1b** deep-DD: SOX 40% vs SPX 24% further-10% DD/63d, Fisher raw p=0.465 | H1b inconclusive (25–50%); book rests on H2/H5; Call 5 does not transfer (K002) |
| H2 | Builder–supplier spread is mean-reverting factor, not beta | Residual spread is random walk; extremes uninformative | VR≈1 and no sig. fwd spread return → seesaw is description only | CD p=0.45; pooled fwd net 30bp p_NW 0.30–0.76 (N=9); 63d +3.5% net 7/9 = PRIOR | **K004** — seesaw is description, not signal; outcome #1 cannot trigger |
| H3 | Crowding dominates valuation across episodes | Crowding has no incremental R² over valuation+fundamentals | Valuation incremental R² > crowding in ≥4/7 episodes → retract crowding claim | Falsifier not triggered (3/6); crowding incr adj-R² ≤0 in 5/6; p 0.26–0.90 E3–E7 | **H3 UNSUPPORTED** (K003): neither crowding nor valuation adds power within layers |
| H4 | Driver rotated Oct → Nov 2026 | Coefficient vector stable across E6 and E7 | Wald fails to reject @5% → one regime; may pool | Stacked name-cluster Wald wild p **&lt; 0.001 (0 of 999)**; CR2 p=0.005; funding Shapley E6=0.011 (alt NOT supported) | **REJECT** — outcome #2 triggered; do not pool E6/E7 |
| H5 | Pre-open L(k) forecasts 63d relative supplier performance | L(5)/L(10) uninformative OOS | OOS R²≤0 or hit≤50% → demote to commentary | Troughs=15; train=10 / OOS=5; OOS L10 N=4 | **PRIOR ONLY** (OOS N&lt;8); do not test |

## Fixture reproduction (P0)

Source vocabulary:

- **SPEC_LITERAL** — recomputed from numbers typed into the spec / `config/fixtures.yaml`; arithmetic check only; **must re-verify against ingested prices in P1** (`src.gates.p1_spec_literal`).
- **RAW_FILE** — name the file under `data/raw/`.
- **DERIVED** — state from what.

| Gate | Target | Observed | Status | Source |
|---|---|---|---|---|
| SOXX 5 Nov | −12.1% ±0.3pp | −12.15% | PASS | SPEC_LITERAL → re-verified RAW_FILE `data/processed/prices.parquet` (P1) |
| SPY 5 Nov | −4.4% ±0.2pp | −4.41% | PASS | SPEC_LITERAL → RAW_FILE prices.parquet (P1) |
| QQQ 5 Nov | −6.5% ±0.2pp | −6.49% | PASS | SPEC_LITERAL → RAW_FILE prices.parquet (P1) |
| SMH 5 Nov | −11.2% ±0.2pp | −11.21% | PASS | SPEC_LITERAL → RAW_FILE prices.parquet (P1) |
| SOXX 28 Oct→5 Nov | −24.2% | −24.19% | PASS | SPEC_LITERAL → RAW_FILE prices.parquet (P1) |
| Log-decline share before 5 Nov | 53% | 53.2% | PASS | SPEC_LITERAL → RAW_FILE prices.parquet (P1) |
| Hyperscaler EW 5 Nov | −2.98% | −2.98% | PASS | DERIVED — prices.parquet (note −3.0 SUPERSEDED as rounding) |
| Supplier EW 5 Nov | −13.53% | −13.53% | PASS | DERIVED — note −12.9 **SUPERSEDED** (neocloud layer error) |
| Spearman(5 Nov, YTD) | −0.53 (p=0.0093) | −0.53 | PASS | DERIVED — note −0.69 **SUPERSEDED / UNRECONCILED** (inputs unrecoverable); Call 3 magnitude revised |
| Spearman(5 Nov, prior 5d) | +0.62 | +0.62 | PASS | DERIVED — close 4 Nov / close 28 Oct |
| Names >20% below 52w high | 21/23 | 21/23 | PASS | DERIVED — vs trailing 252d **daily High** |

Diagnosis: [`docs/gap_diagnosis.md`](docs/gap_diagnosis.md). Old note targets retained under `superseded_cross_section_targets_6nov_note` in `config/fixtures.yaml`.

### Skipped tests (current suite)

The three D5 Spearman skips (requested accounting):

| # | Test | Reason |
|---|---|---|
| 1 | `test_spearman_ytd_gate` | D5 — YTD inputs were circular; panel quarantined |
| 2 | `test_spearman_prior5` | D5 — prior-5d inputs were circular; panel quarantined |
| 3 | `test_ai_only_spearmans` | D5 — same circular inputs; panel quarantined |

Additional skips after quarantine / P1 wiring:

| Test | Reason |
|---|---|
| `test_hyperscaler_and_supplier_ew` | D7 — name-level aggregate lacks RAW_FILE under `data/raw/` |
| `test_distance_from_high_count` | D7 — name-level 52w distances lack RAW_FILE |
| `test_p1_spec_literal_gate_against_ingested_prices` | *(armed — prices.parquet present; PASS in P1)* |

### P1 gate (mandatory)

Every **SPEC_LITERAL** row above must reproduce from `data/processed/prices.parquet` within its tolerance via `src.gates.p1_spec_literal.run_p1_spec_literal_gate`, or **P1 fails**. **P1 result: PASS** for SPEC_LITERAL; **FAIL** for supplier EW + YTD Spearmans (targets not changed).

## Open data defects

| ID | Issue | Status |
|---|---|---|
| D1 | SOXX −12.1% (IBKR) vs −12.8% (press) | OPEN — Yahoo matches IBKR −12.15%; press quote still unresolved |
| D2 | Stooq JS-challenged | OPEN — Yahoo used; Stooq cross-check skipped |
| D3 | Financial Datasets MCP needs auth; Plan tier history/burst limits | OPEN |
| D4 | MRVL/LITE all-stock deal | **CLOSED — CONFIRMED** (~2026-11-02; Seeking Alpha/WSJ/CNBC via Google News RSS); merger dummy from 2026-11-02 |
| D5 | Name-level YTD/prior5 | **RESOLVED FROM INGEST** — prior5 Spearmans PASS; **YTD Spearmans FAIL vs note** (finding) |
| D6 | Point-in-time forward P/S and P/E consensus unavailable from listed sources | OPEN — trailing multiples lagged to filing date pre-registered as DEVIATION_FROM_SPEC (FDR test T005b) |
| D7 | Name-level EW / 52w | **RESOLVED FROM INGEST** — hyperscaler EW + 21/23 PASS; **supplier EW FAIL** vs −12.9 (finding) |

## Pre-P1 revisions

Dated **2026-11-08 (Australia/Sydney)**. Original text preserved; revisions logged here before P1 ingest.

### (a) H5 trough definition

**Original:** *“L(k) = [cumulative EW supplier return − cumulative EW builder return] over the k sessions following a local trough, divided by the trailing supplier/builder beta ratio.”* — “local trough” was undefined.

**Revision (fixed now):**
- Trough day τ = a close at the lowest level of the prior 63 sessions (window [τ−62, τ]), confirmed by the next close being higher (`close[τ+1] > close[τ]`).
- L(k) starts counting **after** the confirmation close: cumulative from `close[τ+1]` to `close[τ+1+k]`.
- **Convention asserted in tests:** trough flag at τ uses closes up to τ+1 only; signal L at `asof` uses closes up to `asof−1` only (APAC / 5pm HKT).

### (b) H3 valuation block — forward multiples

**Original:** regressors include “Forward P/S, forward P/E, EV/EBITDA (the valuation block).”

**Revision:** listed sources do not provide point-in-time consensus forward multiples → **D6**. Fallback pre-registered now: **trailing** P/S, P/E, EV/EBITDA lagged to **filing date**, labelled `DEVIATION_FROM_SPEC` in every output, counted as separate FDR test **T005b**. Spec forward-multiple horse race remains the target once a PIT consensus source is wired.

### (c) H4 layer dummy

**Original:** H4 claimed “the supplier-vs-builder layer dummy dominates in November” but the H3 regressor list never estimated a layer dummy.

**Revision:** H3 regressor list now includes an explicit **layer dummy block** (builders = reference). H4’s SUR/Wald is over the full H3 vector including that block.

### (d) H2 credit regime before CRWV CDS

**Original:** conditioning on “CRWV CDS or a high-yield proxy.”

**Revision:** CRWV CDS has no history before its 2025 IPO. For **2023–2024**, regime variable is **HY OAS only** (`BAMLH0A0HYM2`). Do not splice CRWV CDS into that window. From CDS availability onward, prefer CRWV CDS and keep HY OAS as sensitivity.

### (e) Missing-data gate

**Original:** `panel.isna().mean().max() < 0.15` (global).

**Revision:** apply **NaN &lt; 15% per episode** among names that existed at episode start, and **print per-episode counts** of names that existed at episode start (survivorship quantification). Implemented in `src/panel_quality.py`.

### (f) Quarantine of fabricated name-level series (2026-11-08, later same day)

**Original:** `data/processed/nov5_cross_section.csv` held back-solved `ytd_to_4nov_pct` / `ret_prior5_pct` tagged CALIBRATED_CIRCULAR so Spearmans would PASS.

**Revision:** file deleted; no CALIBRATED values under `data/` or `config/`; `docs/reconstruction_audit.md` is the sole record; `tests/test_quarantine_calibrated.py` fails the build if `src/` reads a CALIBRATED column/file.

## H1b design (frozen before forward returns)

**Frozen:** 2026-11-08 14:16 Australia/Sydney (AEDT). Counts already logged (`outputs/exhibits/h1b_deep_dd_counts.csv`). **No forward returns have been loaded at freeze time.** Do not edit this design block after seeing forward-return results.

### State (from P2 counts)
- Rule B event; `dist_high_tm1 < −20%`; cluster day (another rule-B event in prior 126 sessions).
- De-cluster: first qualifying day per non-overlapping 63-session block.
- Fwd-eligible: not within 63 sessions of 2026-11-05. N≥8 floor → `TESTABLE_N_GE_8`.

### Primary / robustness / sensitivity
| Role | Contrast | FDR row | Inference |
|---|---|---|---|
| **Primary** | SOX vs SPX, de-clustered deep-DD events, further 10%+ drawdown within 63 sessions | **T002b** | Fisher exact (raw p logged) |
| **Robustness** | SMH, SOXX same state vs SPX rates | — | Descriptive only — **no p-values** |
| **Sensitivity** | IXIC vs SOX (same era) | **T002c** | Fisher exact; one extra FDR row |

### Bootstrap unit
Resample **bear-market episodes**, not events. An episode = a run of de-clustered events in which consecutive events are separated by **fewer than 252 sessions**. Print episode IDs before / with results.

### Decision rule (SOX own forward record — drives the book)
| SOX rate of further-10% DD within 63 sessions | Decision |
|---|---|
| **≥ 50%** | “Do not add supplier beta” stands; sizing must assume another leg |
| **≤ 25%** | Patience reading supported by sector history |
| **Between 25% and 50%** | Inconclusive; book decision rests on H2/H5 |

### Per-event report
For each fwd-eligible de-clustered event: `+21` / `+63` / `+252` close-to-close return; max further drawdown within 63 sessions (min of `close[t+j]/close[t]−1` for j=1…63). Print the full list when N&lt;20 (all H1b series currently N≤21; print SOX/SMH/SOXX/IXIC in full; SPX N=21 print in full).

### Status at freeze
T002b / T002c registered as EXPLORATORY / planned sensitivity. Forward-return module not yet executed.

## H1b results (post-freeze)

**Run:** 2026-11-08 (Australia/Sydney). Code: `src/studies/h1b_forward.py`. Exhibits: `h1b_forward_events.csv`, `h1b_episodes.csv`, `h1b_forward_summary.csv`. Design block above is immutable.

### Episode IDs (bootstrap unit)
Printed in `outputs/exhibits/h1b_episodes.csv`. Counts: SPX 14 episodes / 21 events; IXIC 7 / 10; SOX 10 / 15; SMH 8 / 9; SOXX 7 / 10.

### Further-10% DD within 63 sessions

| Series | N | n DD10 | rate | role |
|---|---:|---:|---:|---|
| SPX | 21 | 5 | 23.8% | control |
| SOX | 15 | 6 | **40.0%** | primary |
| SMH | 9 | 1 | 11.1% | robustness (no p) |
| SOXX | 10 | 3 | 30.0% | robustness (no p) |
| IXIC | 10 | 4 | 40.0% | (full sample); same-era vs SOX below |

### Tests
| ID | Contrast | Table (DD / no) | odds | raw p | status |
|---|---|---|---:|---:|---|
| **T002b** | SOX vs SPX | SOX 6/9; SPX 5/16 | 2.13 | **0.465** | RUN |
| **T002c** | IXIC vs SOX (from 1996-01-09) | IXIC 2/3; SOX 6/9 | 1.00 | **1.000** | RUN |

### SOX decision rule (drives the book)
SOX further-10% rate = **40%** → **INCONCLUSIVE** (between 25% and 50%). Book decision rests on H2/H5. “Do not add supplier beta” is neither confirmed nor overturned by H1b alone.

### Episode-level hit rates (descriptive — no new tests)
An episode “hits” if **any** de-clustered event in that episode has further-10% DD within 63 sessions.

| Series | Episode hits | note |
|---|---|---|
| SOX | **3/10** | SOX_E02 (1997–98), SOX_E03 (2000), SOX_E06 (2008) |
| SPX | **5/14** | |
| IXIC | **4/7** | |
| SMH | **1/8** | |
| SOXX | **2/7** | |

SMH/SOXX **miss the 1997–98 episode** (listing starts 2000/2001), which holds **3 of SOX’s 6** event-level further-DD hits.

### Median forward outcomes (event-level)

| Series | median +63 | median +252 | median max_dd_63 |
|---|---:|---:|---:|
| SPX | +9.6% | +19.7% | −6.7% |
| SOX | **+1.5%** | **+30.6%** | **−8.5%** |
| SMH | +19.1% | +47.2% | −6.3% |
| SOXX | +12.8% | +36.6% | −7.3% |
| IXIC | −0.1% | +11.9% | −9.0% |

### EXPLORATORY_UNTESTED (post-hoc; not in FDR family)
**Logged 2026-11-08 (Australia/Sydney).** Judgment-coded over N=10 SOX episodes. **Not a pre-registered test; do not count in FDR.**

> SOX further-drawdown hits occurred only in earnings-led downturns (1997–98, 2000, 2008), not in shock/rate-led episodes.

Candidate monitor (desk, not a test): AI-supplier forward EPS revisions over the next 4–8 weeks.

### Per-event lists
Full event-level `+21/+63/+252` and `max_dd_63` printed at run time and stored in `outputs/exhibits/h1b_forward_events.csv` (all series N≤21).

## H3 design (frozen before fundamentals load)

**Frozen:** 2026-11-08 22:15 Australia/Sydney (AEDT). **No SEC/FINRA fundamentals have been loaded at freeze time.** Do not edit this design block after seeing fundamental coverage or regression output.

### Primary model
Per-episode cross-section of **episode return** on:
- crowding **PC1**
- valuation **PC1**
- funding **PC1**
- layer dummy (builders = reference)
- log market cap

Full regressor list (mom, dist, vol, trailing multiples, funding ratios, …) = **secondary**. Report **VIFs** and **PC loadings** for every run.

### Inference
- Wild cluster bootstrap on **GICS sub-industry** clusters (Webb weights)
- Plus **episode-level** bootstrap
- Do not report naive OLS t-stats as primary inference

### Universe
H3 universe = names with **EDGAR 10-K / 10-Q or 20-F** coverage at episode start. Exclusions listed in `config/universe.yaml` with reason (kept current as coverage is measured). Survivorship: count names that existed at each episode start.

### AI exposure (0–3)
Cursor proposes; human signs off. Tag: **`JUDGMENT_CODED_POST_OUTCOME`**. Always run H3 **with and without** this regressor.

### Valuation (D6)
Trailing P/S, P/E, EV/EBITDA lagged to **filing date** only (`DEVIATION_FROM_SPEC`, FDR row **T005b**). No point-in-time forward multiples until D6 clears.

### Short interest
Attempt FINRA equity short interest history. If not available back through 2018 episode starts → **drop SI**, log `DEVIATION_FROM_SPEC`, crowding = mom / dist / vol only.

### Status at freeze
P3 coverage skeleton exists (`panel.parquet` price blocks only). Fundamentals ingest and updated coverage follow this freeze commit.


## H3 P3 ingest notes (post-freeze)

**Run:** 2026-11-08 (Australia/Sydney). Design block above unchanged.

- **Calendar:** `2026-05-25` / `2026-09-07` rows came from Yahoo **`^VIX`** printing on US equity holidays, then an outer join in `build_price_frames`. Dropped via `drop_vix_only_sessions` (no ffill). Source note in `src/features/calendar_hygiene.py`.
- **ADV regression:** broke in commit `2902f6f` (volume read from `data/raw/2026-11-08` with no equity Yahoo caches). Fixed by `resolve_yahoo_raw_dir` → `2026-11-07`. Guard: `tests/test_adv_coverage.py` (≥90% listed).
- **EDGAR:** all 45 seed names have 10-K/10-Q or 20-F in companyfacts → `h3_exclusions: []`.
- **Short interest:** FINRA biweekly CDN available from **2018-01-12** → **KEPT** (covers E1). Crowding = mom/dist/vol/SI.
- **AI exposure:** time-varying E1–E4 / E5–E7 in `config/ai_exposure.yaml`. **Signed off by Nigel, 2026-11-11.** Status `SIGNED_OFF`, tag `JUDGMENT_CODED_POST_OUTCOME`. companyfacts had no segment data — scores are judgment without segment evidence. Spearman vs layer dummy: `ai_exposure_spearman_vs_layer.csv`.
- Coverage exhibits: `h3_feature_coverage.csv`, `h3_feature_coverage_summary.csv`, `edgar_coverage_by_name.csv`, `ffill_audit_*.csv`.


## Pre-P4 revisions

**Logged:** 2026-11-11 (Australia/Melbourne). **Before any H3 regression.**

### (a) Valuation block → yields
Use **E/P, S/P, EBITDA/EV** (filing-date lagged) instead of P/E, P/S, EV/EBITDA so loss-makers stay in the cross-section. Still `DEVIATION_FROM_SPEC` / FDR **T005b** (trailing, not forward PIT). Recovered names per episode: `outputs/exhibits/valuation_yield_recovered_names.csv`.

### (b) Lease liabilities / ASC 842
Public-business-entity ASC 842 effective for fiscal years beginning after **2018-12-15**. E1 start **2018-10-01** is structurally pre-adoption for nearly all names (`asc842_lease_first_filed.csv`: lease filed by E1 for **1/45** names — MSFT early adopter). **Do not impute zero.** E1 funding PC1 built from `net_debt_ebitda` + `interest_coverage` only when lease coverage is sparse.

### (c) Missing data
- **Primary:** complete cases per episode (print N).
- **Sensitivity:** median imputation + missing-indicator dummies.
- Episodes with **N < 20** complete cases are reported but **excluded from the H3 falsifier count**.

### Repo hygiene
`data/raw/` gitignored; `data/raw_manifest.csv` holds file / sha256 / source URL / pull date.


## H3 review (P4)

**Run:** 2026-11-11 (Australia/Melbourne).

### Decision
**H3 UNSUPPORTED: neither crowding nor valuation adds explanatory power within layers.**

- Falsifier not triggered (valuation beats crowding in 3/6 counted; E1 excluded).
- Crowding incremental adj-R² ≤ 0 in **5/6** counted episodes; wild-bootstrap p on crowding PC1 is 0.26–0.90 in E3–E7.
- K003: Call 3 (crowding, not valuation) not supported in multivariate panel; univariate crowding association (adj R² 0.37 E6, 0.23 E7) is absorbed by layer dummies.

### Fragility / degenerate inference
| episode | N | k | residual_df | flag | p_crowding | note |
|---|---:|---:|---:|---|---:|---|
| E1 | 8 | 10 | -3 | DEGENERATE | 0.000 | p=0.000 DEGENERATE (saturated / non-positive residual df; bootstrap mass at point estimate) |
| E2 | 21 | 10 | 10 | FRAGILE | 0.000 | p=0.000 DEGENERATE/FRAGILE (residual df small; wild-bootstrap p not reliable) |
| E3 | 28 | 11 | 16 | nan | 0.829 | nan |
| E4 | 31 | 11 | 19 | nan | 0.897 | nan |
| E5 | 35 | 11 | 23 | nan | 0.262 | nan |
| E6 | 36 | 11 | 24 | nan | 0.294 | nan |
| E7 | 36 | 11 | 24 | nan | 0.721 | nan |

E1 is **DEGENERATE** (saturated, residual df < 0, R²=1). E2 is **FRAGILE** (residual df=10). p=0.000 in E1/E2 is **DEGENERATE** — wild-bootstrap mass collapses when the fit is saturated / residual df is tiny; do not read as “highly significant”.

### EXPLORATORY (not in FDR family)
**Layer incremental adj-R²** over crowding+valuation+funding+mcap:

- E1: nan
- E2: 0.6023904360995089
- E3: 0.2806635842074383
- E4: 0.02948242442715676
- E5: 0.16840349968069335
- E6: 0.2058908956324268
- E7: 0.26913857027762633

**Shapley R² (E5–E7)** — layer dominates:

block|E5|E6|E7
crowding|0.0125|0.1444|0.0916
funding|0.0374|0.011|0.0229
layer|0.3558|0.4096|0.4029
mcap|0.0091|0.0936|0.127
valuation|0.0092|0.024|0.0337


episode        E5      E6      E7
block                            
crowding   0.0125  0.1444  0.0916
funding    0.0374  0.0110  0.0229
layer      0.3558  0.4096  0.4029
mcap       0.0091  0.0936  0.1270
valuation  0.0092  0.0240  0.0337

**Crowding PC1 orientation:** vol and SI loadings flip to the **same sign as momentum** in E2/E3; elsewhere they load opposite mom/dist (risk-off / crowded-short axis). See `h3_pc1_orientation.csv`.

episode  load_vol   load_si  load_mom  load_dist  vol_si_same_sign_as_mom
     E1 -0.475711 -0.383047  0.517984   0.598888                    False
     E2  0.611297  0.427963  0.620089   0.242184                     True
     E3  0.392103  0.453276  0.682990   0.417518                     True
     E4 -0.552985 -0.464413  0.471612   0.506073                    False
     E5 -0.495232 -0.534399  0.227024   0.646238                    False
     E6 -0.438942 -0.468303  0.504482   0.577511                    False
     E7 -0.503068 -0.481749  0.455512   0.554392                    False

**E6/E7 primary vs secondary** (`h3_e6_e7_primary_vs_secondary.csv`):

episode          model  n_complete   adj_r2  coef_crowding_pc1  coef_valuation_pc1  p_crowding_pc1  p_valuation_pc1  coef_prior_63d  coef_dist_252d  coef_vol_21d   coef_si   coef_ep   coef_sp  coef_ebitda_ev
     E6    primary_pc1          36 0.537102           0.014692           -0.007451        0.264264         0.428428             NaN             NaN           NaN       NaN       NaN       NaN             NaN
     E6 secondary_full          36 0.793734                NaN                 NaN             NaN              NaN       -0.020991       -0.058803     -0.474769 -0.783915 -0.839723 -0.232733       -0.492871
     E7    primary_pc1          36 0.530459           0.009786            0.013443        0.754755         0.436436             NaN             NaN           NaN       NaN       NaN       NaN             NaN
     E7 secondary_full          36 0.730944                NaN                 NaN             NaN              NaN       -0.323699        0.168495     -0.284948 -0.180097 -0.969342  0.125002       -0.644232


## H4 results (P4) — frozen stacked Wald

**Run:** 2026-11-11 (Australia/Melbourne); additions accepted 2026-11-12.

### Status
- Prior separate-episode GICS-cluster Wald: **FROZEN TEST INVALID** (numerically degenerate).
- Post-hoc 4-df core Wald (p≈0.012): **DEVIATION_FROM_SPEC / EXPLORATORY** — own `tests_run` row; **must not carry the decision**.
- **Primary (this run):** stacked E6+E7, H3 primary slopes + slope×E7, cluster by **name** (G=36), Webb wild bootstrap. Intercepts/episode levels free. `log_mkt_cap` centered+scaled.

### Degeneracy diagnosis (layer ⊃ GICS)
Several layer dummies nest inside a single GICS sub-industry cluster, so a GICS-cluster sandwich cannot separately identify those layer effects (singular / explosive V). Nested in one GICS cluster: **3/8** layers (compute_semis→Semiconductors; neoclouds→Application Software; semicap→Semiconductor Materials & Equipment). Confirmed cause of the invalid prior run. Full table: `h4_layer_gics_nesting.csv`.

### Primary Wald
- N=72 (36 names × 2); interaction df=11
- Design XtX cond=4.82e+03; interaction V cond (wild)=1.63e+03
- Wald (wild) stat=39.51; p_chi2=4.337e-05; **wald_p_wild_boot = &lt; 0.001 (0 of 999)**
- CR2 check: stat=26.71; **p_chi2=0.005**
- **Decision:** H4 null **REJECTED** (wild p&lt;0.001, CR2 p=0.005) — do not pool E6 and E7
- **Power caveat:** Stacked N=72 (36 names × 2). k_slopes=11; interaction df=11. Name clusters=36. A non-rejection does not prove equality with G≈36 clusters.

### What rotated (pre-registered alternative)
- Pre-registered alternative **"funding dominates October" NOT supported** (funding Shapley E6 = **0.011**).
- What rotated: **layer composition** — compute semis worse in E7 (robust); neoclouds and funding borderline (percentile CI excludes 0; neither survives Holm @5%).
- **Pre-registered outcome #2 triggered:** H4 rejects stability and the layer dummy dominates in November → profit pool moved toward builders; a book with zero builder exposure is one bet expressed ten ways.

### Slope × E7 interactions (raw + Holm)

| interaction | coef | p_raw_wild | p_holm | sig_holm_05 | pct CI excl 0 |
|---|---:|---:|---:|:---:|:---:|
| crowding_pc1:e7 | −0.0049 | 0.844 | 1.000 | no | no |
| valuation_pc1:e7 | 0.0209 | 0.051 | 0.459 | no | no |
| funding_pc1:e7 | 0.0282 | 0.058 | 0.464 | no | yes |
| log_mkt_cap:e7 | 0.0610 | 0.132 | 0.925 | no | no |
| layer_compute_semis:e7 | −0.1131 | 0.006 | 0.066 | no | yes |
| layer_memory_storage:e7 | −0.0236 | 0.809 | 1.000 | no | no |
| layer_neoclouds:e7 | 0.1706 | 0.038 | 0.380 | no | yes |
| layer_non_ai_control:e7 | −0.0483 | 0.622 | 1.000 | no | no |
| layer_optics_networking:e7 | −0.0297 | 0.744 | 1.000 | no | no |
| layer_power_cooling:e7 | 0.0185 | 0.760 | 1.000 | no | no |
| layer_semicap:e7 | 0.0322 | 0.530 | 1.000 | no | no |

No individual interaction is Holm-significant @5%. Joint Wald (11 df) carries the rejection. Compute-semis is the strongest single move (raw p=0.006, Holm p=0.066).

### Robustness (EXPLORATORY)

| Check | Rejection survives? | compute_semis:e7 CI excl 0? |
|---|---|---|
| (a) ORCL coded as neocloud (spec dual-code) | **yes** (wild p &lt; 0.001) | **yes** (coef −0.141) |
| (b) Within-episode z-scored returns | **yes** (wild p &lt; 0.001) | **no** (CI includes 0) |

Logged as `H4_ROBUST_ORCL_NEOCLOUD` / `H4_ROBUST_ZSCORE_RETURNS` in `tests_run.csv`.

### Descriptive: layer Shapley is not November-specific
Layer Shapley R² dominates in **all three** AI episodes — E5 **0.36**, E6 **0.41**, E7 **0.40** — so layer dominance alone is not November-specific. H4 tests which layer loadings changed; funding did not dominate October.

Exhibits: `h4_wald_summary.json`, `h4_slope_interactions_ci.csv`, `h4_stacked_coefficients.csv`, `h4_layer_gics_nesting.csv`, `h4_robustness.json`.

## H2 design (frozen before forward returns)

**Frozen:** 2026-11-12 (Australia/Melbourne). **No forward returns have been loaded at freeze time.** Do not edit this design block after seeing forward-return results.

### Construction (already run)
- Sample: 2023-01-01 → present. EW builders vs EW AI-chain suppliers (exclude `non_ai_control`).
- Beta-neutral residual vs SPY (trailing 126d OLS with intercept); spread = supplier residual − builder residual.
- −2.5σ events: rolling mean/sd of spread **end at t−1** (shift 1), matching H1 rule B.
- Regime: HY OAS (`BAMLH0A0HYM2`) above/below lagged 126d median. FRED HY OAS history starts **2023-11-07**; events before the 126d warm-up are **unclassified**.

### Forward design (frozen now)
- **De-cluster:** first event per non-overlapping **21-session** block (on the trading calendar).
- **Primary:** pooled forward spread return at **5 / 21 / 63** sessions (sum of residual spread over t+1…t+h). Report hit rate and median. Inference: **Newey–West** (lag = horizon) and block bootstrap. **Mean reversion = positive** forward spread return.
- **Regime split** (HY OAS above/below lagged 126d median) = **PRIOR ONLY** if either cell has **N &lt; 8**.
- Report all forward results **net of 30bp round-trip cost**.

### Status at freeze
VR (hetero-robust z*) + Chow–Denning + causal event counts + Nov 4/5 exploratory decomp are run. Forward module not yet executed.

---

## H2 results (P5) — VR, events, exploratory (pre-forward)

**Run:** 2026-11-12 (Australia/Melbourne). Forward block below filled only after freeze commit.

### Variance ratio (Lo–MacKinlay, hetero-robust z*)

| q | VR | z* | p* | z_homo (audit) | p_homo (audit) |
|---:|---:|---:|---:|---:|---:|
| 2 | 0.990 | −0.22 | 0.828 | −0.30 | 0.762 |
| 5 | 0.891 | −1.11 | 0.267 | −1.54 | 0.123 |
| 10 | 0.786 | −1.43 | 0.152 | −1.97 | 0.049 |
| 21 | 0.669 | −1.49 | 0.137 | −2.01 | 0.044 |

**Chow–Denning** joint (q = 2,5,10,21): CD = **1.49**, SMM p = **0.446** — do not reject VR=1 jointly at 5%. Homoskedastic z inflated significance; hetero-robust does not. Each q is its own `tests_run` row (`H2_VR_q2`…`H2_VR_q21`) plus `H2_CHOW_DENNING`.

### −2.5σ event counts (causal σ through t−1)

| Regime | N events |
|---|---:|
| HY_OAS_above_median | 7 |
| HY_OAS_below_median | 6 |
| Unclassified (HY OAS median warm-up) | 1 |

Total raw events: **14**; classified: **13**. Includes **2026-11-04**.

### EXPLORATORY (not in FDR family) — 4 Nov / 5 Nov 2026 beta decomposition

| date | builder β | supplier β | builder resid | supplier resid | spread | z | H2 event? |
|---|---:|---:|---:|---:|---:|---:|:---:|
| 2026-11-04 (day after midterm) | 1.40 | 3.39 | +0.012 | −0.118 | −0.130 | **−3.81** | **yes** |
| 2026-11-05 | 1.43 | 3.14 | +0.030 | +0.004 | −0.025 | **−0.59** | **no** |

**5 Nov is not an H2 event** (causal z = −0.59 ≫ −2.5). **4 Nov is** (z = −3.81). Exhibit: `h2_nov4_nov5_beta_decomp.csv`.

## H2 results (P5) — forward returns (post-freeze)

**Run:** 2026-11-12 (Australia/Melbourne). Design block above is immutable. Code: `src/studies/h2_spread_factor.py --forwards`.

### De-cluster
14 raw −2.5σ events → **10** after first-per-21-session block. **2026-11-04** is kept as an event but has no complete +5/+21/+63 window (sample ends 2026-11-05) → pooled N=**9** for all horizons.

### Primary — pooled forward spread return (net 30bp round-trip)

| h | N | mean_net | median_net | hit rate | NW SE | t_NW | p_NW | p_block_boot |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 9 | +0.006 | +0.007 | 67% | 0.0098 | 0.61 | 0.542 | 0.718 |
| 21 | 9 | −0.011 | +0.016 | 56% | 0.0370 | −0.30 | 0.765 | 0.800 |
| 63 | 9 | +0.035 | +0.038 | 78% | 0.0344 | 1.03 | 0.305 | 0.472 |

No horizon rejects mean=0 at 5% (NW or block bootstrap). Hit rates &gt;50% but underpowered (N=9).

### Regime split — PRIOR ONLY (both cells N &lt; 8)

| Regime | N (fwd-eligible) |
|---|---:|
| HY_OAS_above_median | 3 |
| HY_OAS_below_median | 5 |

Logged as PRIOR ONLY; not used for the H2 decision. Exhibit: `h2_forward_summary.csv`.

### Decision
- VR (hetero-robust) + Chow–Denning: **fail to reject** VR=1 jointly (CD p=0.45).
- Forward pooled: **no significant** positive mean-reversion net of 30bp at 5/21/63.
- **K004:** Builder–supplier spread is **not** a mean-reverting factor. Seesaw is description, not signal.
- **PRIOR (not a finding):** 63d mean_net +3.5%, hit 7/9 — point estimate only; do not cite as evidence.
- **Outcome #1 cannot trigger** (required H2). Call 2’s directional description still stands.

Exhibits: `h2_forward_events.csv`, `h2_forward_summary.csv`, `h2_forward_meta.json`, `h2_variance_ratio.csv`, `h2_chow_denning.json`, `h2_events_m2p5sigma.csv`, `h2_nov4_nov5_beta_decomp.csv`.

## H5 design / counts (P6) — stop before testing

**Run:** 2026-11-12 (Australia/Melbourne). Counts + monitor only.

### Trough rule
63d low on **cumulative supplier−builder EW return spread** from 2023-01-01, confirmed by next close up. L(k) after confirmation close; signal uses closes through asof−1 only.

### Walk-forward split (frozen)
- Train: confirmation date **&lt; 2025-01-01**
- OOS: confirmation date **≥ 2025-01-01**
- Power floor: OOS troughs with complete L(10) **N ≥ 8**

### Counts
| | N |
|---|---:|
| Total confirmed troughs | 15 |
| L(5) complete | 15 |
| L(10) complete | 14 |
| Train / OOS | 10 / 5 |
| Train L10 / OOS L10 | 10 / **4** |

**Decision: H5 PRIOR ONLY** — OOS L10 N=4 &lt; 8; **do not test.** Full trough list with L(5)/L(10): `h5_trough_list.csv`.

### Daily monitor (spec deliverable 5)
`python -m src.monitor.daily_desk` — from prior US close, before 5pm HKT: L(5), L(10), trough status, beta-neutral spread z. Latest (prior close 2026-11-05): L5=−0.025, L10 incomplete for latest trough; spread z=−0.59; prior close is a 63d low on cum spread (confirmation pending). Exhibit: `h5_daily_monitor.json`.

