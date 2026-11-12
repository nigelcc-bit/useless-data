# Flush or regime change? The 5 Nov 2026 AI selloff

A pre-registered study of whether the November 2026 selloff in the AI supply chain was a **positioning flush** (crowded names sold, then bought back) or a **regime change** (the market moving the AI profit pool away from suppliers and toward the companies paying for the buildout).

**Status:** **Complete** (tagged `flush-or-regime-v1`). H2 killed (**K004**); H3 unsupported (**K003**); H4 rejects pooling E6/E7; H5 **PRIOR ONLY** (OOS N=4); P7 FDR/exhibits done. Study pin **2026-11-05**. Nothing in this README is a trading recommendation.

Governing rules: repository root [`RESEARCH_PROTOCOL.md`](../../RESEARCH_PROTOCOL.md).

---

## 1. The question

> After a violent decline in the AI supply chain, does the cross-section mean-revert into the same names (flush), or does leadership rotate away from them (thesis change)?

On **5 Nov 2026** the S&P 500 fell **4.36%**, the Nasdaq Composite **5.52%** and the PHLX Semiconductor index (SOX) **12.3%**. The four hyperscalers fell about **3%** on average and AI suppliers about **13.5%**.

A same-week note (*The Blue Tsunami Flush*, 6 Nov, in `docs/`) argued from that one session and 23 hand-picked names that this was "a thesis event stacked on a positioning event". This study turns that note's claims into tests that can fail.

### What would change the decision

| If this happens | Then |
|---|---|
| H2 and H5 hold and the leadership statistic L(5) is positive | Flush. A supplier-heavy book is positioned correctly; the right action is patience. |
| H4 rejects stability and the supplier/builder layer dominates in November | The profit pool has moved toward builders. A book with no builder exposure is one bet expressed ten ways. |
| H1 shows semis continue falling more often than the S&P | The 6 Nov "don't sell into the hole" inference does not apply to a semis book. Resize before the next leg. |
| H3 shows valuation explains the selloff better than crowding | The crowding framework behind the July, October and November notes is wrong and those notes are retracted. |

---

## 2. Hypotheses

Each hypothesis has a null, a decision rule and a kill condition, fixed in `RESULTS.md` before any result was computed.

| ID | Claim | Test | Kill condition |
|---|---|---|---|
| **H1** | Semis do not inherit the S&P's benign base rate after a sharp one-day drop | Event study on SOX, SMH, SOXX and Nasdaq vs the S&P; Fisher exact test on "fell another 10% within 63 sessions" | Semis' further-drawdown rate within the S&P's bootstrap interval |
| **H2** | The supplier-minus-builder spread is a mean-reverting factor, not just market beta | Beta-neutral daily spread from 2023; variance ratio; forward spread returns after -2.5σ days, split by credit regime | Variance ratio ≈ 1 and no forward spread return |
| **H3** | Crowding explains episode losses better than valuation | Per-episode cross-sectional regression on 45 names × 7 episodes; crowding, valuation, funding and layer blocks | Valuation adds more R² than crowding in at least 4 of 7 episodes |
| **H4** | The driver changed between October (funding) and November (permitting/volume) | SUR across the two episodes; Wald test on coefficient equality | Coefficients stable at 5%: treat the two episodes as one regime |
| **H5** | A leadership statistic computed from the prior US close forecasts the next 63 sessions | Walk-forward out-of-sample regression from 2023 | Out-of-sample R² ≤ 0 or hit rate ≤ 50% |

H5 has a hard implementability rule: the signal must use closes up to the previous US session only, so an APAC desk can place it as a pre-order before 5pm HKT.

---

## 3. Data sources

| Source | What it provides | Coverage | Notes |
|---|---|---|---|
| **Yahoo Finance** (`yfinance`) | Daily OHLCV for all names, ETFs and indices | Names 2015-2026; S&P 500 from 1928, Nasdaq from 1971, SOX from 1994, SMH from 2000, SOXX from 2001 | Primary price source. Matches IBKR closes on every fixture checked. |
| **Interactive Brokers** | Daily bars | 26 Oct to 6 Nov 2026 | Verification only: fixture closes and the CRWV / IREN / NBIS neocloud check |
| **FRED** | High-yield OAS (`BAMLH0A0HYM2`), 10y yield, fed funds, VIX, Nasdaq Composite | Full history | Credit-regime variable for H2; Nasdaq cross-check |
| **SEC EDGAR XBRL** (companyfacts) | Revenue, earnings, debt, cash, interest, leases, shares outstanding | All 45 names (ASML, IREN, NBIS, TSM via 20-F) | Every value lagged to its **filing date**, not its period end |
| **FINRA** | Equity short interest | From 12 Jan 2018 | Crowding block |
| **Press** (Reuters, CNBC, AP, Bloomberg) | 5 Nov index closes | One session | Fixtures only |

**Not available, and how it is handled**

- **Point-in-time forward consensus estimates:** no free source. H3 uses trailing measures lagged to filing date, labelled `DEVIATION_FROM_SPEC` and counted as a separate test (T005b).
- **Stooq:** blocked; Yahoo and FRED used instead.
- **Segment revenue:** not in companyfacts, so the 0-3 AI-exposure score is a human judgment, coded after the outcomes were known. It is tagged `JUDGMENT_CODED_POST_OUTCOME` and H3 is run with and without it.

### Universe (45 names, `core/reference/universe_v2026-11.yaml`)

| Layer | Names |
|---|---|
| Builders | MSFT, AMZN, GOOGL, META, AAPL, ORCL (ORCL also coded as neocloud for sensitivity) |
| Compute semis | NVDA, AMD, AVGO, MRVL, TSM, INTC |
| Memory and storage | MU, SNDK, WDC, STX |
| Semicap equipment | LRCX, AMAT, KLAC, ASML, TER |
| Optics and networking | LITE, COHR, ANET, GLW, ALAB, CIEN, FN, APH |
| Power and cooling | GEV, VRT, ETN, PWR, NVT |
| Neoclouds | CRWV, NBIS, IREN, APLD, CORZ |
| Non-AI control | CRWD, NOW, HOOD, PANW, SNOW, DDOG |

### Episodes (`config/episodes.yaml`, frozen)

| ID | Window | Character | Role |
|---|---|---|---|
| E1 | 2018-10-01 to 2018-12-24 | Semis bear, Fed tightening | Out of sample |
| E2 | 2020-02-19 to 2020-03-23 | COVID crash | Out of sample |
| E3 | 2022-01-03 to 2022-10-14 | Rate-driven de-rating | Out of sample |
| E4 | 2025-04-03 to 2025-04-08 | Tariff shock | Out of sample |
| E5 | 2026-07-15 to 2026-07-25 | AI flush #1 (dates to confirm) | Fit |
| E6 | 2026-09-30 to 2026-10-19 | AI flush #2, funding-led | Fit |
| E7 | 2026-10-28 to 2026-11-05 | The subject episode | Fit |

---

## 4. Method and discipline

See [`RESEARCH_PROTOCOL.md`](../../RESEARCH_PROTOCOL.md). This study’s ledger is `outputs/tests_run.csv`; kill log `outputs/killed_hypotheses.md`; FDR at BH q=0.10 over the pre-registered family (Romano–Wolf for H3 blocks).

---

## 5. Final results

Study as-of pin: **2026-11-05**. Tag: `flush-or-regime-v1`. Full table: [`RESULTS.md`](RESULTS.md). Kill log: [`outputs/killed_hypotheses.md`](outputs/killed_hypotheses.md). Addendum: [`docs/addendum_6nov_calls.md`](docs/addendum_6nov_calls.md). Exhibits: `outputs/exhibits/fig01_*.png` … `fig14_*.png`.

### Outcomes scorecard

| # | Outcome | Status |
|---|---|---|
| 1 | H2+H5 hold, L(5)>0 → flush / patience | **Dead** (K004; H5 PRIOR ONLY) |
| 2 | H4 rejects + layer dominates Nov → profit pool to builders | **Triggered** |
| 3 | H1 semis worse than S&P → Call 5 does not apply | **Inconclusive** (H1b 40%; K002) |
| 4 | H3 valuation dominates → retract crowding | **Not triggered**; crowding unsupported (K003) |

### Hypotheses

| ID | Decision |
|---|---|
| H1 / H1b | Call 5 does not transfer (K002). Deep-DD continuation **inconclusive** (SOX 40%). |
| H2 | **K004** — seesaw is description, not a mean-reverting factor. |
| H3 | **K003 / UNSUPPORTED** — neither crowding nor valuation wins within layers. |
| H4 | **REJECT** stability (BH q=0.10: only family reject). Outcome #2. |
| H5 | **PRIOR ONLY** (OOS N=4). Monitor ships; untested. |

### FDR (Benjamini–Hochberg q=0.10)

Pre-registered family with numeric p: 11 tests. **Only `H4_WALD_E6_E7` rejects** after BH (raw &lt;0.001 → BH≈0.011). NOT_RUN / underpowered / PRIOR_ONLY rows listed with reasons in `p7_fdr_preregistered.csv`. Exploratory / DEVIATION rows unadjusted in `p7_fdr_exploratory_unadjusted.csv`. Romano–Wolf on H3 E3–E7 crowding/valuation PC1: no block survives (`p7_romano_wolf_h3_blocks.csv`).

### Note reproduction (still the baseline)

ETF 5 Nov: SOXX **−12.15%**, SPY **−4.41%**, QQQ **−6.49%**, SMH **−11.21%**. Builder EW **−2.98%**, supplier EW **−13.53%**, neocloud **−13.91%** (note understated the gap). YTD Spearman **−0.53** (note −0.69 UNRECONCILED).

### Seven calls

| Call | Status |
|---|---|
| 1. Election = accelerant | Untested |
| 2. Seesaw returned | Direction yes; **not a factor (K004)**; H4 outcome #2 |
| 3. Crowding not valuation | **K003** |
| 4. Funding / policy channel | H4 reject; funding-dominates-Oct **no**; layer composition rotated |
| 5. First-shock bounce base rate | **Does not apply to semis** |
| 6. Midterm fee paid | Descriptive only |
| 7. Feed / tally | Survives as audit |

### Monitor refresh (DESCRIPTIVE — not a study result)

Snapshot through **2026-11-10** (`data/processed/monitor_snapshots/`). Study pin unchanged. **5 Nov trough confirmed on 6 Nov**; L(5) not yet available; through 10 Nov suppliers +7.0% vs builders +2.4% since confirmation; spread z 6/9/10 Nov: +1.66 / +0.49 / +0.16. Label: single observation, H5 untested. Desk flips: beta-neutral spread z and L(5)/beta ratio (not the retired “suppliers &gt;2× builders” rule).

---

## 6. Known limitations

- **Small samples.** 45 names, 7 episodes, about 10 semis bear markets. Expect wide intervals; a hit rate is often more useful than a p-value.
- **Survivorship.** The universe is today's names. Many did not exist in early episodes (E1 has 33 listed names of 45). Counts per episode are printed rather than corrected.
- **Judgment inputs.** Layer assignment, AI-exposure scores and episode dates are judgment calls, several made after outcomes were known. They are tagged and tested with and without.
- **Trailing, not forward, valuation.** No point-in-time consensus source was available.
- **Merger contamination.** MRVL's all-stock deal for LITE (around 2 Nov 2026) makes LITE's later returns partly a merger spread. A dummy is applied and a without-LITE sensitivity is logged.

---

## 7. Layout (this study)

```
config/       fixtures, episodes, nov5_panel, pins.yaml (reference versions)
docs/         research spec, 6 Nov note, diagnosis write-ups, addendum
src/          hypotheses, gates, monitor, P1 / snapshot entry points
tests/        study-specific gates
outputs/      exhibits, tests_run.csv, killed_hypotheses.md
RESULTS.md    pre-registration table
```

Shared library and data live at the repo root (`core/`, `data/`).

## 8. Reproduce

```bash
# from repository root
python3 -m pip install -e ".[dev]"
export PYTHONPATH=.:studies/2026-11-flush-or-regime
python -m src.run_p1                 # prices, FRED, splits
python -m src.reproduce_nov5         # fixture check
python -m src.h1b_forward
python -m src.h2_spread_factor
python -m src.h3_panel_regression
python -m src.h4_coefficient_rotation
pytest
python -m src.monitor.leadership     # pre-open statistic / daily desk
```

Requires Python 3.12+ and network access to Yahoo Finance, FRED, SEC EDGAR and FINRA.
