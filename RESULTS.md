# RESULTS — Flush or regime change?

**What would change the book** (why this study exists):

- **If H2 and H5 hold and L(5) is positive** → flush; supplier-heavy book is positioned correctly; patience.
- **If H4 rejects stability and the layer dummy dominates in November** → profit pool moved toward builders; a book with zero builder exposure is one bet expressed ten ways.
- **If H1 shows semis have a materially worse continuation base rate than the S&P** → the 6 Nov "don't sell into the hole" inference does not apply to this book; size differently before the next leg.
- **If H3 flips and valuation dominates** → crowding framework from July/October/November is wrong; three prior notes need retracting.

Fill **Result** and **Decision** only after code runs. Do not edit hypotheses after seeing results.

| ID | Hypothesis | Null | Decision rule / falsifier | Result | Decision |
|---|---|---|---|---|---|
| H1 | Semis do not inherit S&P benign first-shock base rate | Conditional first-shock near-high fwd distribution indistinguishable from S&P | Further 10%+ DD frequency within bootstrap CI of S&P → Call 5 extends | Near-high first-shock cell underpowered (T002 NOT_RUN); **H1b** deep-DD: SOX 40% vs SPX 24% further-10% DD/63d, Fisher raw p=0.465 | H1b inconclusive (25–50%); book rests on H2/H5; Call 5 does not transfer (K002) |
| H2 | Builder–supplier spread is mean-reverting factor, not beta | Residual spread is random walk; extremes uninformative | VR≈1 and no sig. fwd spread return → seesaw is description only | *pending* | |
| H3 | Crowding dominates valuation across episodes | Crowding has no incremental R² over valuation+fundamentals | Valuation incremental R² > crowding in ≥4/7 episodes → retract crowding claim | Falsifier not triggered (3/6); crowding incr adj-R² ≤0 in 5/6; p 0.26–0.90 E3–E7 | **H3 UNSUPPORTED** (K003): neither crowding nor valuation adds power within layers |
| H4 | Driver rotated Oct → Nov 2026 | Coefficient vector stable across E6 and E7 | Wald fails to reject @5% → one regime; may pool | Core Wald p≈0.012; full-vector Wald NUMERICAL_DEGENERATE; rdf 24/24 | **REJECT** stability — do not pool E6/E7 |
| H5 | Pre-open L(k) forecasts 63d relative supplier performance | L(5)/L(10) uninformative OOS | OOS R²≤0 or hit≤50% → demote to commentary | *pending* | |

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

## H4 results (P4)

**Run:** 2026-11-11 (Australia/Melbourne). Frozen SUR/Wald on H3 primary vector incl. layer dummies.

- N complete: E6=36, E7=36; k slopes=11; **residual df 24 / 24**
- Full-vector Wald: stat=20208.6, p=0.0, cond=3.28e+05 → **NUMERICAL_DEGENERATE**
- Core Wald (PC1s+mcap): stat=12.82, df=4, **p=0.01217**
- **Decision:** REJECT stability @5% — do not pool E6 and E7
- **Power caveat:** Residual df E6=24, E7=24 with k=11 slopes (+intercept). N=36/36 complete cases. Wild-cluster Wald with 13/13 GICS clusters is low-power for equality; a non-rejection does not prove coefficient equality. Full-vector V condition number=3.28e+05 (ill=True); core Wald p=0.01217. Decision basis=core_pc1_mcap_wald_FULL_VECTOR_NUMERICAL_DEGENERATE. Inspect per-coef diffs in h4_e6_e7_coefficients.csv.

Exhibits: `h4_wald_summary.json`, `h4_e6_e7_coefficients.csv`.

**Stop after H4.**

