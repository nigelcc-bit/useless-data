# P1 findings — 2026-11-08 (Australia/Sydney)

Ingest ran with Yahoo chart API + FRED. Stooq returned a JS challenge page (unavailable). Targets were **not** adjusted.

## SPEC_LITERAL gate — PASS

All six ETF observables reproduce from `data/processed/prices.parquet` within tolerance. Yahoo closes match the IBKR fixture close vector for SPY/SOXX path to ≤0.01.

## D5 / D7 resolution from ingested data — FAIL (finding)

Cross-section built from Yahoo closes for the N=23 panel in `config/nov5_panel.yaml`.

| Metric | Target (6 Nov note) | Observed (Yahoo) | Verdict |
|---|---:|---:|---|
| Hyperscaler EW 5 Nov | −3.0 | −2.98 | PASS |
| Supplier EW 5 Nov | −12.9 | −13.53 | **FAIL** (tol 0.3) |
| Spearman(5 Nov, YTD→4 Nov) | −0.69 | −0.53 | **FAIL** |
| Spearman AI-only YTD | −0.76 | −0.59 | **FAIL** |
| Spearman(5 Nov, prior5 28Oct→4Nov) | +0.59 | +0.62 | PASS |
| Spearman AI-only prior5 | +0.73 | +0.75 | PASS |
| Names >20% below 52w high | 21 | 21 | PASS |

**52w high basis:** trailing 252-session **daily High** (intraday high of each session), not closes. The 6 Nov note used intraday highs from monthly bars.

**YTD definition used:** `close[2026-11-04] / close[2025-12-31] − 1`.

### Which input disagrees

1. **YTD-to-4-Nov ranks** — the Spearman vs 5 Nov return is materially weaker than the note (−0.53 vs −0.69). This is the primary disagreement. Verified name-level *5 Nov returns* match the note (MSFT/AMZN/GOOGL/META/AMD/MRVL/MU/LRCX/LITE/VRT/NBIS all within 0.05pp). So the note’s **YTD column / universe ranks**, not the one-day returns, are the suspect input.
2. **Supplier EW** — 0.63pp more negative than −12.9. Likely a small universe / equal-weight composition difference among the 16 suppliers once Yahoo fills names the note may have hand-set.
3. **Prior-5d Spearmans** — agree with the note within tolerance.

Per-name table: `outputs/exhibits/d5_d7_per_name_diff.csv`.

**Interpretation:** A failed fixture here is treated as evidence the 6 Nov note’s crowding YTD sort may be overstated or used a different YTD window/membership — **not** as license to retarget.

## D4 merger — CONFIRMED

MRVL all-stock acquisition of LITE announced ~**2026-11-02** (Seeking Alpha / TipRanks / Invezz; WSJ “Chip Maker Marvell Agrees to Buy Lumentum…”). Google News RSS cached at `data/raw/2026-11-07/merger_search_raw.xml`. Merger dummy from **2026-11-02** in `data/processed/merger_dummy.csv`.

## Survivorship (universe.yaml, n=45 today)

| Episode | Existed at start |
|---|---:|
| E1 2018-10-01 | 33 |
| E2 2020-02-19 | 35 |
| E3 2022-01-03 | 38 |
| E4–E7 | 45 |

## Split audit

Yahoo chart events → 22 splits auto-imported into `corporate_actions.yaml`. Equity `|ret|>25%` without a split event logged as market gaps (59). `^VIX` excluded from the equity audit.

## GLW / ORCL 52w (daily)

| Ticker | Dist vs daily High | Dist vs daily Close |
|---|---:|---:|
| GLW | −61.9% | −59.5% |
| ORCL | −54.4% | −54.0% |

## Stooq

Unavailable (HTML challenge). Defect remains open for index cross-check.
