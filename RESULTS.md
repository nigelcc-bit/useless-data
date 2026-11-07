# RESULTS — Flush or regime change?

**What would change the book** (why this study exists):

- **If H2 and H5 hold and L(5) is positive** → flush; supplier-heavy book is positioned correctly; patience.
- **If H4 rejects stability and the layer dummy dominates in November** → profit pool moved toward builders; a book with zero builder exposure is one bet expressed ten ways.
- **If H1 shows semis have a materially worse continuation base rate than the S&P** → the 6 Nov "don't sell into the hole" inference does not apply to this book; size differently before the next leg.
- **If H3 flips and valuation dominates** → crowding framework from July/October/November is wrong; three prior notes need retracting.

Fill **Result** and **Decision** only after code runs. Do not edit hypotheses after seeing results.

| ID | Hypothesis | Null | Decision rule / falsifier | Result | Decision |
|---|---|---|---|---|---|
| H1 | Semis do not inherit S&P benign first-shock base rate | Conditional first-shock near-high fwd distribution indistinguishable from S&P | Further 10%+ DD frequency within bootstrap CI of S&P → Call 5 extends | *pending — power check first* | |
| H2 | Builder–supplier spread is mean-reverting factor, not beta | Residual spread is random walk; extremes uninformative | VR≈1 and no sig. fwd spread return → seesaw is description only | *pending* | |
| H3 | Crowding dominates valuation across episodes | Crowding has no incremental R² over valuation+fundamentals | Valuation incremental R² > crowding in ≥4/7 episodes → retract crowding claim | *pending* | |
| H4 | Driver rotated Oct → Nov 2026 | Coefficient vector stable across E6 and E7 | Wald fails to reject @5% → one regime; may pool | *pending — do not pool before this* | |
| H5 | Pre-open L(k) forecasts 63d relative supplier performance | L(5)/L(10) uninformative OOS | OOS R²≤0 or hit≤50% → demote to commentary | *pending* | |

## Fixture reproduction (P0)

Source vocabulary:

- **SPEC_LITERAL** — recomputed from numbers typed into the spec / `config/fixtures.yaml`; arithmetic check only; **must re-verify against ingested prices in P1** (`src.gates.p1_spec_literal`).
- **RAW_FILE** — name the file under `data/raw/`.
- **DERIVED** — state from what.

| Gate | Target | Observed | Status | Source |
|---|---|---|---|---|
| SOXX 5 Nov | −12.1% ±0.3pp | −12.15% | PASS | SPEC_LITERAL — `config/fixtures.yaml` `verified_closes_2026_10_26_to_11_05.SOXX` |
| SPY 5 Nov | −4.4% ±0.2pp | −4.41% | PASS | SPEC_LITERAL — same close vector, SPY |
| QQQ 5 Nov | −6.5% ±0.2pp | −6.49% | PASS | SPEC_LITERAL — same close vector, QQQ |
| SMH 5 Nov | −11.2% ±0.2pp | −11.21% | PASS | SPEC_LITERAL — same close vector, SMH |
| SOXX 28 Oct→5 Nov | −24.2% | −24.19% | PASS | SPEC_LITERAL — SOXX[5 Nov]/SOXX[28 Oct]−1 |
| Log-decline share before 5 Nov | 53% | 53.2% | PASS | SPEC_LITERAL — log(SOXX 4 Nov/28 Oct) ÷ log(SOXX 5 Nov/28 Oct) |
| Hyperscaler EW 5 Nov | −3.0% | *(not evaluated)* | **BLOCKED** — D7 | *(no RAW_FILE)* |
| Supplier EW 5 Nov | −12.9% | *(not evaluated)* | **BLOCKED** — D7 | *(no RAW_FILE)* |
| Spearman(5 Nov, YTD) | −0.69 | *(not evaluated)* | **BLOCKED** — D5 | *(no RAW_FILE; fabricated values quarantined)* |
| Spearman(5 Nov, prior 5d) | +0.59 | *(not evaluated)* | **BLOCKED** — D5 | *(no RAW_FILE; fabricated values quarantined)* |
| Names >20% below 52w high | 21/23 | *(not evaluated)* | **BLOCKED** — D7 | *(no RAW_FILE)* |

Fixture **targets** above are unchanged. Fabricated name-level YTD/prior5 values were **removed** from `data/` and `config/`; the only residual record is [`docs/reconstruction_audit.md`](docs/reconstruction_audit.md).

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
| `test_p1_spec_literal_gate_against_ingested_prices` | P1 ingest not present (`data/processed/prices.parquet`) — gate arms when file exists |

### P1 gate (mandatory)

Every **SPEC_LITERAL** row above must reproduce from `data/processed/prices.parquet` within its tolerance via `src.gates.p1_spec_literal.run_p1_spec_literal_gate`, or **P1 fails**. Arithmetic on YAML alone does not clear P1.

## Open data defects

| ID | Issue | Status |
|---|---|---|
| D1 | SOXX −12.1% (IBKR) vs −12.8% (press) | OPEN — flagged, not papered over |
| D2 | Yahoo/Stooq/FRED blocked or challenged from this cloud environment | OPEN — **P1 runs locally**, not in Cloud |
| D3 | Financial Datasets MCP needs auth; Plan tier history/burst limits | OPEN |
| D4 | MRVL/LITE merger announcement ~4 Nov unverified | OPEN — merger dummy or exclude |
| D5 | Name-level YTD and prior-5d inputs unverified (circular reconstruction) | OPEN — values quarantined from `data/`/`config/`; Spearman gates skipped |
| D6 | Point-in-time forward P/S and P/E consensus unavailable from listed sources | OPEN — trailing multiples lagged to filing date pre-registered as DEVIATION_FROM_SPEC (FDR test T005b) |
| D7 | Name-level aggregates (hyperscaler/supplier EW, 21/23 below 52w) lack RAW_FILE | OPEN — BLOCKED until P1 writes name closes under `data/raw/` |

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
