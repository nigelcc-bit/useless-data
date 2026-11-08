# Gap diagnosis — supplier EW & YTD Spearman (2026-11-08, Australia/Sydney)

Pre-registered rule: pipeline error → fix pipeline; note error → SUPERSEDE with Yahoo + provenance; log “Call 3 magnitude revised”.

## 1. Supplier EW

| | Note reconstruction | Ours (`nov5_panel.yaml`) |
|---|---|---|
| Semis N=7 | NVDA, AMD, AVGO, MRVL, TSM, MU, LRCX | same |
| Optics N=4 | LITE, COHR, ANET, GLW | same |
| Power N=2 | VRT, ETN | same |
| Neocloud N=3 | CRWV, NBIS, IREN | same |

**Difference:** none — sets identical.  
Yahoo EW on that exact set: **−13.53%** (note target −12.9%).

| Layer | Yahoo EW | Note layer target | Delta |
|---|---:|---:|---:|
| Semis N=7 | −14.00 | −14.0 | +0.00 |
| Optics N=4 | −13.85 | −13.8 | −0.05 |
| Power N=2 | −10.70 | −10.8 | +0.10 |
| **Neocloud N=3** | **−13.91** | **−10.6** | **−3.31** |

3/16 × 3.31 ≈ 0.62pp ≈ full supplier-EW gap.

**Rule:** **NOTE ERROR** (neocloud layer print in the 6 Nov note). Pipeline membership correct; Yahoo neocloud returns are the fixture. → **SUPERSEDE** `supplier_ew_nov5_pct: -12.9 → -13.53`.

## 2. YTD Spearman

Name-level note YTD: **unavailable** (`ai_selloff_cross_section_5Nov2026.csv` never uploaded).

| Series | ρ (N=23) | p | ρ AI (N=20) | p |
|---|---:|---:|---:|---:|
| Yahoo Close (split-adj chart) | −0.529644 | 0.009345 | −0.590977 | 0.006070 |
| Yahoo Adj Close (split+div) | −0.532609 | 0.008885 | −0.595489 | 0.005601 |
| Note target | −0.69 | — | −0.76 | — |

Close vs Adj: max \|rank change\| = 1 (MSFT/AMZN/ANET/GLW only); ρ shifts &lt; 0.01. **Not an adjusted/unadjusted pipeline bug.**

Excluding LITE (merger): ρ worsens to −0.486 (N=22), AI −0.535 — does **not** move toward −0.69.

**Rule:** **NOTE ERROR** (Call 3 crowding magnitude overstated). → **SUPERSEDE** Spearmans to Yahoo Close values; log Call 3 magnitude revised.

## 3. Exact p-values (requested)

- N=23, ρ=−0.5296442687747036 → **p = 0.009344661031627151**
- N=20 AI, ρ=−0.5909774436090225 → **p = 0.006070153699275824**

## 4. LITE sensitivity

Logged as `P1_LITE_SENSITIVITY` in `outputs/tests_run.csv` (DIAGNOSTIC).

## 5. FRED NASDAQCOM

| Series | 4 Nov | 5 Nov | ret | vs note −5.52% |
|---|---:|---:|---:|---|
| FRED NASDAQCOM | 25736.51 | 24315.00 | −5.5233% | match |
| Yahoo ^IXIC | 25736.51 | 24315.00 | −5.5233% | match |

Stooq still blocked; NASDAQCOM is the Nasdaq cross-check.
