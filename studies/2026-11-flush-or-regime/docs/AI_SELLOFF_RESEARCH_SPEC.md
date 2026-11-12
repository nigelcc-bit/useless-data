# Research Specification: Was 5 Nov 2026 a Flush or a Regime Change?

**A pre-registered data-science brief for the AI capex cross-section, 2018-2026.**

Author context: written 7 Nov 2026 as the follow-on to `Blue_Tsunami_Flush_AI_Selloff_6Nov2026.docx`. That note is descriptive and rests on one session and 23 names. This spec converts its claims into falsifiable, properly-powered tests. Target environment: Cursor on local machine with unrestricted network (the cloud sandbox cannot reach Yahoo, Stooq or FRED; your laptop can — that is the single biggest reason to run this locally).

**Governing rule for this project: you are a false-discovery controller, not a pattern generator. Every hypothesis below is pre-registered with a null, a decision rule and a kill condition. Count every test you run, including the ones you abandon. A result that survives only after you changed the window, the universe or the threshold is not a result.**

---

## 0. The one question

> After a violent decline in the AI supply chain, does the cross-section mean-revert into the same names (positioning flush), or does leadership rotate away from them (thesis change)?

Everything below serves that question. If a task does not change the answer, cut it.

The 6 Nov note's provisional answer was "thesis event stacked on a positioning event," argued from a single session. That is a hypothesis, not a finding.

---

## 1. What is already established — do not re-derive, use as fixtures

These numbers were verified from Interactive Brokers bars and named press on 6 Nov 2026. **Hard-code them into the test suite.** If your pipeline cannot reproduce them, your pipeline is wrong — do not "fix" them by adjusting the figures.

### 1.1 Index and ETF moves, 5 Nov 2026 (one-day, close to close)

| Instrument | Move | Source class |
|---|---|---|
| S&P 500 | -4.36% to 7,353.73 | press |
| Nasdaq Composite | -5.52% to 24,315.00 | press |
| Nasdaq 100 | -6.4% | press |
| Dow | -1,833.06 (-3.44%) | press |
| PHLX SOX | -12.3% to 9,011.14 | press |
| VIX | 16.61 → 28.18 (+69.7%) | press |
| SPY | -4.4% | IBKR bars |
| QQQ | -6.5% | IBKR bars |
| SMH | -11.2% | IBKR bars |
| SOXX | -12.1% (press quotes -12.8%) | IBKR bars |

**Note the SOXX discrepancy (-12.1% vs -12.8%).** Resolving it is task D1 below. Do not paper over it.

### 1.2 Verified daily closes, 26 Oct to 5 Nov 2026

```
dates = [10-26, 10-27, 10-28, 10-29, 10-30, 11-02, 11-03, 11-04, 11-05]
SPY   = [765.37, 769.66, 772.31, 769.36, 755.72, 752.10, 754.35, 766.81, 733.00]
QQQ   = [712.20, 721.25, 725.61, 715.34, 690.49, 681.09, 685.28, 691.95, 647.05]
SOXX  = [163.94, 170.35, 173.98, 171.29, 157.17, 151.22, 155.00, 150.14, 131.90]  # 3:1 split-adjusted
SMH   = [541.62, 557.98, 567.67, 561.67, 522.49, 508.31, 518.52, 504.27, 447.73]
```

### 1.3 Cross-sectional results to reproduce (N=23 names, 4 Nov → 5 Nov)

- Hyperscaler EW (MSFT, AMZN, GOOGL, META): **-3.0%**. Supplier EW (N=16): **-12.9%**.
- Six-session (28 Oct → 5 Nov): hyperscalers **-2.8%**, suppliers **-26.5%**, SOXX **-24.2%**.
- Spearman(5 Nov return, YTD return to 4 Nov) = **-0.69**, p < 0.001. AI-chain only (N=20): **-0.76**.
- Spearman(5 Nov return, 28 Oct → 4 Nov return) = **+0.59**, p = 0.003. AI-chain only: **+0.73**.
- 21 of 23 names more than 20% below 52-week high. SPY -6.2%, SOXX -39.7%.
- **53%** of the log decline from 28 Oct to 5 Nov occurred before 5 Nov.

### 1.4 S&P 500 event study (daily closes 1928-2019)

- 151 one-day declines ≥ 4%. **125 are cluster days** (another within 126 sessions), concentrated 1929-33 and 2008-09. 26 are first shocks.
- First shock within 5% of 252d high (N=9): +63d higher in **8/9**, median **+6.7%**; worst further drawdown median -2.2%; **0/9** fell a further 10%.
- Within 10% (N=15): 13/15 at +63d; **1/15** fell a further 10% — 3 Oct 1929, -39%.
- More than 10% below high (N=11): 3/11 positive at +21d; **5/11** fell a further 10%.
- Any-day baseline: +63d median +2.4% (63% positive); +252d +8.9% (69%).
- **The near-high set's +252d median is +3.1%, below the +8.9% baseline.** Good quarter, poor year.

### 1.5 Prior project findings to treat as priors, not facts

- July 2026 flush: run-up vs flush-return rank correlation **-0.64**. October 2026 flush: **-0.56**.
- October 2026: supplier-hyperscaler daily correlation rose **+0.35 → +0.81**; best single predictor of October loss was September beta to CRWV (rho **-0.68**).
- October 2026: forward multiples had **no** explanatory power (P/S rho -0.11, P/E +0.01, EV/EBITDA +0.03).
- Layer-rank correlation between the July and October episodes: **+0.51**.
- Midterm years (N=24, 1930-2022): median intra-year S&P drawdown **-19.6%**, 20/24 worse than -10%. 2026 so far: **-9.1%** (30 Mar low).
- Falsified narrative: AI "layer-by-layer rotation" — first-half vs second-half rank correlation **-0.59** implies mean reversion, not a relay.

---

## 2. Open questions, ranked by decision value

| # | Question | Why it matters | Current state |
|---|---|---|---|
| Q1 | Does the S&P first-shock base rate transfer to semis? | The note's Call 5 is an S&P result used in a semis book. That is a category error until tested. | **Unknown.** No sector base rate exists. |
| Q2 | Is builder-vs-supplier divergence a distinct, mean-reverting factor or just a beta artefact? | Decides whether the discriminating test is meaningful. | One session of evidence. |
| Q3 | Does crowding beat valuation and fundamentals in a proper panel, or only in a 23-name snapshot? | The whole "positioning not valuation" claim. | Three episodes, rank correlations only, no controls. |
| Q4 | Did the driver change between October (funding) and November (permitting/volume)? | If the coefficient vector rotated, the two episodes are different animals and should not be pooled. | Asserted, never tested. |
| Q5 | Can a leadership statistic be computed pre-US-open and acted on as a pre-order? | The APAC desk closes 5pm HKT and places orders ahead of the US session. An intraday signal is useless there. | Not addressed. |

---

## 3. Pre-registration

Fill in the **Result** and **Decision** columns only after the code runs. Do not edit a hypothesis after seeing its result; if you must revise, log the original and mark the revision as exploratory.

### H1 — Semis do not inherit the S&P's benign first-shock base rate

- **H0:** Conditional on a first shock near the 252d high, the SOX/SMH forward-return distribution is statistically indistinguishable from the S&P's.
- **H1:** Semis show materially higher continuation risk — specifically, a higher frequency of a further 10%+ drawdown within 63 sessions.
- **Test:** Replicate the Section 1.4 design on SOX (1994-2026), Nasdaq Composite (1971-2026) and SMH/SOXX (2000-2026). Event threshold scaled to each series' volatility: use both an absolute -4% rule **and** a -2.5σ rule on trailing 252d vol, reported separately. Fisher exact test on the "further 10% drawdown" 2×2; bootstrap CI on the median forward return difference.
- **Power check first:** before running, compute how many qualifying episodes each series yields. **If a conditional cell has N < 8, report it as a prior and do not test it.** Pooling across indices to manufacture N is forbidden — they are not independent.
- **Falsifier:** if semis' further-drawdown frequency is within the bootstrap CI of the S&P's, the note's Call 5 extends to the sector and the "don't add supplier beta" caveat weakens.
- **Known trap:** SOX has only ~32 years and its shocks cluster hard (2000-02, 2008, 2018, 2020, 2022, 2025). Expect N of 5-12 after conditioning. Say so loudly.

### H2 — The builder-supplier spread is a mean-reverting factor, not beta

- **H0:** After controlling for market beta, the supplier-minus-builder spread follows a random walk; extreme daily values carry no information about forward relative returns.
- **H1:** Extreme negative spread days are followed by positive spread returns over 21-63 sessions (mean reversion), conditional on the funding regime.
- **Construction:** daily EW supplier basket and EW builder basket (taxonomy in §4). Beta-neutralise: regress each basket on SPY over a trailing 126d window, form the residual spread. Build from 1 Jan 2023 (the start of the AI capex cycle) to present.
- **Test:** event study on spread days beyond -2.5σ. Report forward spread returns at 5/21/63 sessions with hit rates, plus an AR(1) / variance-ratio test on the spread series.
- **Conditioning variable:** credit regime (CRWV CDS or a high-yield proxy, above/below its 126d median). The core claim is that the spread mean-reverts in a flush and trends in a thesis change.
- **Falsifier:** variance ratio ≈ 1 and no significant forward spread return → the seesaw is description, not signal, and §9 of the note's monitoring dashboard needs rewriting.

### H3 — Crowding dominates valuation in the cross-section, across episodes

- **H0:** In a multivariate episode regression, crowding proxies carry no incremental explanatory power over valuation and fundamentals.
- **H1:** Prior run-up and distance-from-high dominate; forward multiples are insignificant.
- **Design:** panel of ~120 names (§4) × 7 episodes (§5). Dependent variable: episode return. Regressors, all standardized and winsorised at 2.5/97.5:
  1. Prior 63d return (run-up / momentum)
  2. Distance from 252d high at episode start
  3. Trailing 21d realised vol
  4. Short interest as % of float
  5. Forward P/S, forward P/E, EV/EBITDA (the valuation block)
  6. Net debt / EBITDA, interest coverage, lease liabilities / assets (the funding block)
  7. AI revenue exposure (judgment-coded 0-3; **flag it as judgment in every output**)
  8. Log market cap and ADV (liquidity controls)
- **Inference:** episode fixed effects; standard errors clustered by GICS sub-industry; bootstrap by episode (not by name) because names are cross-correlated within an episode. Report a horse race: adjusted R² of crowding block alone vs valuation block alone vs both.
- **Falsifier:** if the valuation block's incremental R² exceeds the crowding block's in ≥ 4 of 7 episodes, the "not a valuation sort" claim dies.
- **Known trap:** run-up, distance-from-high and realised vol are collinear by construction (expect |rho| 0.6-0.85). **Report variance inflation factors and run a PCA or orthogonalisation; do not interpret individual coefficients inside a collinear block.** The 6 Nov note could not separate these and said so — do not repeat that limitation, resolve it.

### H4 — The driver rotated between October and November 2026

- **H0:** The coefficient vector from the H3 regression is stable across the Oct 2026 and Nov 2026 episodes.
- **H1:** Funding-block loadings dominate in October; the supplier-vs-builder layer dummy dominates in November.
- **Test:** seemingly-unrelated regression across the two episodes with a Wald test on coefficient equality (a Chow test generalisation). Report the full coefficient-difference vector with CIs, not just the p-value.
- **Why it matters:** if the vector is stable, October and November are one continuous funding event and the permitting narrative is decoration. If it rotated, they are two separate repricings and must never be pooled in any later study.
- **Falsifier:** Wald test fails to reject at 5% → treat the two episodes as one regime.

### H5 — A pre-open leadership statistic has forecasting power

- **Definition:** L(k) = [cumulative EW supplier return − cumulative EW builder return] over the k sessions following a local trough, divided by the trailing supplier/builder beta ratio. Computed **on closes only**, so it is available before the next US open.
- **H0:** L(5) and L(10) carry no information about the subsequent 63-session relative performance of suppliers.
- **H1:** L(5) > 0 by more than the beta ratio predicts → flush → suppliers outperform over 63 sessions.
- **Test:** across all troughs identified in §5 episodes, regress forward 63d supplier-minus-builder return on L(5) and L(10). Report out-of-sample performance using expanding-window walk-forward from 2023.
- **Implementability gate (hard requirement):** the signal must be computable from data available at the previous US close and executable as a single pre-order before 5pm HKT. **Any variant needing intraday data or same-session execution is out of scope — the desk cannot trade it.**
- **Falsifier:** out-of-sample R² ≤ 0 or hit rate ≤ 50% → the discriminating test in the note's §9 is not tradable and should be demoted to commentary.

---

## 4. Universe and taxonomy

Build the panel with an explicit layer assignment. The layer variable is the key regressor for H4, so it must be defensible and documented per name.

| Layer | Definition | Seed names |
|---|---|---|
| **Builders (hyperscalers)** | Pay for the buildout; capex is a cash outflow | MSFT, AMZN, GOOGL, META, ORCL*, AAPL |
| **Compute semis** | GPU/ASIC/CPU for AI | NVDA, AMD, AVGO, MRVL, TSM, INTC |
| **Memory and storage** | DRAM/HBM/NAND | MU, SNDK, WDC, STX, SK Hynix (ADR), Samsung |
| **Semicap equipment** | Tools and metrology | LRCX, AMAT, KLAC, ASML, TER, Advantest, Disco, BESI |
| **Optics and networking** | Transceivers, switches, fibre | LITE, COHR, ANET, GLW, ALAB, CIEN, FN, APH |
| **Power, cooling, electrical** | Grid, turbines, thermal | GEV, VRT, ETN, PWR, NVT, Bloom, Modine |
| **Neoclouds and AI hosting** | Lease-financed compute | CRWV, NBIS, IREN, APLD, CORZ, Nscale |
| **Non-AI control group** | Similar beta, no AI capex link | CRWD, NOW, HOOD, PANW, SNOW, DDOG |

\* ORCL is deliberately ambiguous — builder by business model, neocloud by funding structure. **Code it both ways and report sensitivity.** Ambiguous names are where the taxonomy earns or loses its credibility.

**Control group matters.** Without it you cannot distinguish "AI chain was sold" from "high-multiple growth was sold." The 6 Nov note had only 3 control names; this needs 10-15.

---

## 5. Episode definitions

Pre-register the dates. Do not optimise them later.

| ID | Window | Character | Why included |
|---|---|---|---|
| E1 | 2018-10-01 → 2018-12-24 | Semis bear, Fed tightening | Prior tightening-cycle analogue |
| E2 | 2020-02-19 → 2020-03-23 | COVID crash | Exogenous shock, out-of-sample for the 1928-2019 study |
| E3 | 2022-01-03 → 2022-10-14 | Rate-driven de-rating | The valuation-led counterexample |
| E4 | 2025-04-03 → 2025-04-08 | Tariff shock | Policy shock analogue, recent |
| E5 | 2026-07 (confirm exact dates) | AI flush #1 | rho -0.64 on run-up |
| E6 | 2026-09-30 → 2026-10-19 | AI flush #2, funding-led | rho -0.56; CRWV beta dominant |
| E7 | 2026-10-28 → 2026-11-05 | The subject episode | The one to explain |

E1-E4 are the out-of-sample set for anything fitted on E5-E7. **Do not fit and test on the same episodes.**

---

## 6. Data layer

### 6.1 Sources, in order of preference

1. **yfinance / local network** — works on your laptop, blocked in the sandbox. Primary source for long daily history (SPX, IXIC, SOX, SOXX, SMH, all single names). Free, adequate for daily closes, **unreliable for corporate actions** — verify.
2. **Stooq** — free daily index history, good cross-check on yfinance for index levels.
3. **FRED** — FEDFUNDS, DGS10, high-yield OAS (BAMLH0A0HYM2), VIX. Essential for the regime conditioning in H2.
4. **IBKR MCP** — authoritative for recent bars; **10 req/s and 30 req/min hard limit.** Use only for verification of the fixture dates, not for bulk history. Build a rate-limited queue with disk cache if you touch it at all.
5. **Financial Datasets MCP** — fundamentals and filings. Plan tier caps history at ~1 year, returns `Unauthorized` on bursts, and `total_debt` mis-parses for CRWV (use total liabilities plus cash-flow debt issuance instead). Derived margin fields are inconsistent when non-operating income is large — always check against raw line items.
6. **SEC EDGAR full-text / XBRL** — the only trustworthy source for the funding block. Slow but correct.

### 6.2 Mandatory adjustments

- **Splits.** SOXX did a 3:1 in 2026 (30 Oct close 471.51 pre-split ≈ 157.17 post). SNDK did 8-for-1. **Build a split-verification test:** for each name, flag any single-day move beyond ±25% and check it against a corporate-actions table before accepting it.
- **Dividends.** Use total-return series for the base-rate work, price series for the drawdown work. State which, per exhibit.
- **The 52-week high problem.** The 6 Nov note took highs from monthly bars and flagged GLW and ORCL as showing implausible single-month gaps. Rebuild highs from daily data and re-verify those two.
- **Point-in-time index membership.** Today's SOXX constituents are not 2018's. Either source historical membership or **accept survivorship bias and quantify it** by reporting how many of today's names existed and were listed at each episode start.
- **Merger contamination.** MRVL and LITE: one source reports an all-stock acquisition announced around 4 Nov 2026 (unverified). If confirmed, their returns after the announcement are a merger spread, not an AI-capex signal. **Verify the deal and either exclude post-announcement observations or add a merger dummy.**

### 6.3 Data quality gates

Write these as assertions that fail the build:

```python
assert abs(soxx_ret["2026-11-05"] + 0.121) < 0.003     # fixture §1.1
assert abs(spy_ret["2026-11-05"] + 0.044) < 0.002
assert spearman(nov5_ret, ytd_ret)[0] < -0.60          # fixture §1.3
assert n_events_sp500_4pct_1928_2019 == 151            # fixture §1.4
assert first_shock_near_high_63d_hits == (8, 9)
assert no_single_day_move_exceeds(0.25, unless_in=corporate_actions)
assert panel.isna().mean().max() < 0.15                # or document each gap
```

**If a gate fails, stop and resolve it. Do not proceed with a caveat.**

---

## 7. Statistical discipline

This is the part that separates the project from a chart deck.

1. **Count every test.** Maintain `tests_run.csv` with one row per hypothesis test, including abandoned ones. Apply Benjamini-Hochberg FDR control at q=0.10 across the full family; report both raw and adjusted p-values. For the H3 regressor horse race specifically, use Romano-Wolf stepdown (it handles the cross-correlation between regressors properly).
2. **Overlapping windows inflate t-stats.** Forward 63d and 126d returns overlap heavily. Use Newey-West with lag = horizon, or block bootstrap by episode. Never report a naive t-stat on overlapping forward returns.
3. **Report effect size against costs.** An edge smaller than round-trip slippage is not an edge. Assume 15-40bp round trip for liquid names, more on a -12% day; model it explicitly. Use **expectancy**, not risk-to-reward ratios.
4. **Small N honesty.** Any conditional cell with N < 10 gets its episode list printed in full, as the 6 Nov note did for the N=15 set. A reader must be able to see that "8 of 9" includes 1929 as a near-neighbour.
5. **Kill log.** `killed_hypotheses.md` — every hypothesis that failed, with the number that killed it. **This file is a deliverable, equal in status to the findings.** A project that kills nothing has learned nothing.
6. **No post-hoc threshold tuning.** The -2.5σ event threshold, the 126d first-shock window, the 5%/10% distance bands: all fixed here, now. If you test a second threshold, it counts as a second test in the FDR family.
7. **Separate measurement from judgment** in every output. Layer assignment, AI-revenue-exposure coding and episode dating are judgment. Colour them differently in charts and say so in captions.

---

## 8. Repo structure

```
ai-selloff-study/
├── README.md
├── pyproject.toml              # uv or poetry; pin everything
├── config/
│   ├── universe.yaml           # name → layer, with a one-line justification each
│   ├── episodes.yaml           # the §5 table, frozen
│   └── fixtures.yaml           # §1 verified numbers
├── data/
│   ├── raw/                    # immutable downloads, dated subfolders
│   ├── interim/
│   └── processed/              # panel.parquet, prices.parquet
├── src/
│   ├── ingest/                 # one module per source, all with disk cache + rate limits
│   ├── adjust/                 # splits, dividends, point-in-time membership
│   ├── features/               # crowding, valuation, funding blocks
│   ├── studies/
│   │   ├── h1_sector_base_rate.py
│   │   ├── h2_spread_factor.py
│   │   ├── h3_panel_regression.py
│   │   ├── h4_coefficient_rotation.py
│   │   └── h5_leadership_signal.py
│   ├── stats/                  # fdr.py, bootstrap.py, newey_west.py
│   └── viz/                    # house style: cream FBF6EC, orange E8762C, dark 2B2B2B
├── tests/
│   ├── test_fixtures.py        # §6.3 gates
│   └── test_no_lookahead.py    # see §9
├── notebooks/                  # exploration only; nothing in a notebook is a result
├── outputs/
│   ├── exhibits/
│   ├── tests_run.csv
│   └── killed_hypotheses.md
└── RESULTS.md                  # the pre-registration table, filled in
```

**Environment:** Python 3.12, pandas 2.x, numpy, scipy, statsmodels (for SUR/Wald and Newey-West), linearmodels (panel with clustered SEs), arch (bootstrap), matplotlib. Avoid sklearn for inference work — it gives no standard errors.

---

## 9. Look-ahead audit

Write `tests/test_no_lookahead.py` before writing any study code. It must assert:

- No feature computed at date *t* uses data from *t+1* or later. Test by shifting the entire input frame forward one day and confirming every feature changes.
- Forward returns are never regressors.
- 52-week highs at date *t* use only data ≤ *t*.
- Index membership at date *t* uses the membership known at *t*, or the survivorship caveat is explicitly recorded in the output metadata.
- Fundamentals are lagged to their **filing date**, not their period-end date. A Q3 figure is not knowable on 30 Sep.
- For H5: the signal at date *t* uses closes up to *t-1* only, matching the APAC pre-order constraint.

**A silent look-ahead is the single most common way a study like this produces a beautiful false result.**

---

## 10. Deliverables

1. `RESULTS.md` — the §3 pre-registration table with Result and Decision filled in, nothing else changed.
2. `killed_hypotheses.md` — what died and what killed it.
3. 10-14 exhibits in house style, each captioned with its **method tag** (descriptive frequency / event study / conditional frequency / panel regression / judgment).
4. `panel.parquet` — the reusable cross-sectional dataset. This outlives the study and feeds later work.
5. A monitoring module that computes the H5 statistic daily and prints it in a form that can be read before 5pm HKT.
6. A two-page addendum to the 6 Nov note recording which of its seven calls survived.

---

## 11. Sequencing

| Phase | Work | Gate before proceeding |
|---|---|---|
| **P0** (0.5d) | Repo, env, fixtures, data-quality gates | All §6.3 assertions pass |
| **P1** (1-2d) | Ingest + adjust; build prices.parquet for full universe, 2015-2026 | Split audit clean; fixtures reproduce |
| **P2** (1d) | H1 sector base rate | Power check: report N per cell **before** looking at returns |
| **P3** (1-2d) | Feature blocks; panel.parquet | Look-ahead audit passes |
| **P4** (1-2d) | H3 panel regression, then H4 rotation test | VIFs reported; collinearity resolved |
| **P5** (1d) | H2 spread factor | Variance ratio computed |
| **P6** (1-2d) | H5 signal + walk-forward + costs | Pre-open constraint verified in code |
| **P7** (0.5d) | FDR across the whole family; write RESULTS.md and the kill log | Adjusted p-values reported alongside raw |

**Do not reorder P7.** Running FDR at the end, over the complete test log, is the point.

---

## 12. Anti-patterns — reject these if they appear

- **Training a return-prediction model on 23 names.** You have a cross-section, not a dataset. Nothing here justifies machine learning; every hypothesis above is answerable with a regression and an event study, and those come with standard errors.
- **Reporting a Sharpe ratio on overlapping forward windows.** It will be inflated by roughly √(horizon/step).
- **Pooling episodes before testing H4.** If the coefficient vector rotated, pooled estimates are an average of two different regimes and mean nothing.
- **Treating the S&P base rate as a semis base rate.** That is the error H1 exists to correct.
- **Letting the October CRWV-beta finding and the November layer finding both be "the explanation."** They are competing hypotheses; H4 adjudicates.
- **Charting first.** Every exhibit must implement a named method from §3. If you cannot name the method, the chart is decoration.
- **Quietly dropping a name because it hurts the result.** Exclusions go in `universe.yaml` with a reason, decided before the regression runs.

---

## 13. What would change the book

State this at the top of `RESULTS.md`, because it is why the study exists:

- **If H2 and H5 hold and L(5) is positive** → the episode is a flush, the supplier-heavy book is positioned correctly, and the right action is patience.
- **If H4 rejects stability and the layer dummy dominates in November** → the market has moved the profit pool toward the builders, and a book with zero builder exposure is one bet expressed ten ways.
- **If H1 shows semis have a materially worse continuation base rate than the S&P** → the "don't sell into the hole" inference from the 6 Nov note does not apply to this book, and position sizing must change before the next leg.
- **If H3 flips and valuation dominates** → the entire crowding framework from July, October and November is wrong, and three prior notes need retracting.

The study is worth running precisely because the fourth outcome is possible.
