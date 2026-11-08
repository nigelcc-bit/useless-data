# Gap diagnosis — supplier EW & YTD Spearman (2026-11-08, Australia/Sydney)

Pre-registered rule: pipeline error → fix pipeline; note error → SUPERSEDE with Yahoo + provenance; log “Call 3 magnitude revised”.  
If note inputs are unrecoverable but Yahoo internal sources agree → label **UNRECONCILED** (same SUPERSEDE action, honest label).

## 0. Third-source confirmation — neocloud 5 Nov (IBKR)

Independent IBKR daily closes (desk check, 2026-11-08):

| Name | IBKR 5 Nov | Yahoo 5 Nov |
|---|---:|---:|
| CRWV | −9.83% | −9.83% |
| IREN | −16.95% | −16.95% |
| NBIS | −14.94% | −14.94% |
| **Neocloud EW** | **−13.91%** | **−13.91%** |

IBKR matches Yahoo exactly. The 6 Nov note’s neocloud EW (−10.6%) is rejected by **two** market-data sources. Confirms the **NOTE ERROR** rule for supplier / neocloud EW (not a Yahoo artifact).

## 1. Supplier EW

| | Note reconstruction | Ours (`nov5_panel.yaml`) |
|---|---|---|
| Semis N=7 | NVDA, AMD, AVGO, MRVL, TSM, MU, LRCX | same |
| Optics N=4 | LITE, COHR, ANET, GLW | same |
| Power N=2 | VRT, ETN | same |
| Neocloud N=3 | CRWV, NBIS, IREN | same |

**Difference:** none — sets identical.  
Yahoo / IBKR EW on that exact set: **−13.53%** (note target −12.9%).

| Layer | Yahoo EW | Note layer target | Delta |
|---|---:|---:|---:|
| Semis N=7 | −14.00 | −14.0 | +0.00 |
| Optics N=4 | −13.85 | −13.8 | −0.05 |
| Power N=2 | −10.70 | −10.8 | +0.10 |
| **Neocloud N=3** | **−13.91** | **−10.6** | **−3.31** |

3/16 × 3.31 ≈ 0.62pp ≈ full supplier-EW gap.

**Rule:** **NOTE ERROR** (neocloud layer; IBKR+Yahoo agree). → **SUPERSEDE** `supplier_ew_nov5_pct: -12.9 → -13.53`; `layer_neocloud_ew_nov5: -10.6 → -13.91`.

## 2. YTD Spearman

Name-level note YTD: **unavailable** (`ai_selloff_cross_section_5Nov2026.csv` never uploaded).

| Series | ρ (N=23) | p | ρ AI (N=20) | p |
|---|---:|---:|---:|---:|
| Yahoo Close (split-adj chart) | −0.529644 | 0.009345 | −0.590977 | 0.006070 |
| Yahoo Adj Close (split+div) | −0.532609 | 0.008885 | −0.595489 | 0.005601 |
| Note target | −0.69 | — | −0.76 | — |

Close vs Adj: max \|rank change\| = 1; ρ shifts &lt; 0.01. Pipeline series agree.

Excluding LITE (merger): ρ worsens to −0.486 (N=22) — does **not** move toward −0.69.

**Rule:** **UNRECONCILED** (note YTD inputs unrecoverable; Yahoo Close and Adj Close agree at ≈−0.53). Same SUPERSEDE action as a note error, honest label. → **SUPERSEDE** Spearmans to Yahoo Close; Call 3 magnitude revised.

## 3. Exact p-values

- N=23, ρ=−0.5296442687747036 → **p = 0.009344661031627151**
- N=20 AI, ρ=−0.5909774436090225 → **p = 0.006070153699275824**

## 4. LITE sensitivity

Logged as `P1_LITE_SENSITIVITY` in `outputs/tests_run.csv` (DIAGNOSTIC).

## 5. FRED NASDAQCOM

| Series | 4 Nov | 5 Nov | ret | vs note −5.52% |
|---|---:|---:|---:|---|
| FRED NASDAQCOM | 25736.51 | 24315.00 | −5.5233% | match |
| Yahoo ^IXIC | 25736.51 | 24315.00 | −5.5233% | match |

## 6. Full cross-section re-derivation (prices.parquet)

Because the note had at least one wrong per-name value (neocloud / IREN), every remaining note figure built on that cross-section was re-derived. Threshold: \|Δ\| &gt; 0.3pp → SUPERSEDE.

See `outputs/exhibits/rediagnose_cross_section_table.csv`.

| Metric | Note | Re-derived | Δ pp | Action |
|---|---:|---:|---:|---|
| Hyperscaler EW 5 Nov | −3.0 | −2.98 | +0.02 | keep |
| Supplier EW 5 Nov | −12.9 | −13.53 | −0.63 | **SUPERSEDED** |
| Hyperscaler EW six-session | −2.8 | −2.78 | +0.02 | keep |
| Supplier EW six-session | −26.5 | −27.89 | −1.39 | **SUPERSEDED** |
| Semis EW 5 Nov | −14.0 | −14.00 | +0.00 | keep |
| Optics EW 5 Nov | −13.8 | −13.85 | −0.05 | keep |
| Power EW 5 Nov | −10.8 | −10.70 | +0.10 | keep |
| Neocloud EW 5 Nov | −10.6 | −13.91 | −3.31 | **SUPERSEDED** (IBKR+Yahoo) |
| Non-AI EW 5 Nov | −8.7 | −8.71 | −0.01 | keep |
| Names &gt;20% below 52w high | 21 | 21 | 0 | keep |
| SPY vs 52w high | −6.2 | −6.22 | −0.02 | keep |
| SOXX vs 52w high | −39.7 | −39.68 | +0.02 | keep |
| Worst-7 list | LITE,MU,AMD,MRVL,LRCX,NBIS,VRT | LITE,MU,AMD,**IREN**,MRVL,LRCX,NBIS | IREN in / VRT out | **SUPERSEDED** list |
| 10-name book 5 Nov / six-session | −14.6 / −29.6 | — | — | **UNRECONCILED** (membership not in uploads) |
| 13-name book 52w / YTD | −46.7 / +34.5 | — | — | **UNRECONCILED** (membership not in uploads) |

52w basis for re-derivation: trailing 252-session **daily High**.
