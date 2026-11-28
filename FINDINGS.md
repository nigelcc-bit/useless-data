# Findings: useless-data

Last updated: 2026-11-28

Nothing here is a trading recommendation.

One section per study; re-running a study replaces its section, never adds a
second one. Every finding uses the schema in [README.md](README.md#findings).
`hypothesis` is the statement that was tested and `verdict` refers to it;
`finding` and `key_stats` are the plain-English result. Every string under
`numbers` is copied verbatim from `source_file`, every number spoken in
`finding` or `key_stats` appears in `numbers`, and `scripts/check_findings.py`
enforces both.

## quick-lookups/2026-11-25-mu-regime-read

Status: complete | Run: 2026-11-25 | Source: quick-lookups/2026-11-25-mu-regime-read/RESULT.md

```yaml
- id: ud-mu-regime-read-regime-change
  study: quick-lookups/2026-11-25-mu-regime-read
  type: quant
  region: US
  topic: equities
  hypothesis: Micron's 2026 selloff is a lasting regime change rather than a short flush.
  verdict: weak
  finding: Micron entered a jumpy, high-volatility phase in August 2025, during its rally. The 2026 selloff itself has so far lasted no longer than a normal shakeout.
  key_stats:
    - "high-volatility phase 326 trading days old"
    - "selloff phase 18 trading days old, past spells usually under 56"
  confidence: 60
  numbers:
    - "VERDICT: WEAK | confidence 60%"
    - "**326** (since 2025-08-11)"
    - "the June 2026 peak"
    - "only **18 sessions**, below the past p75 of 56"
  source_file: quick-lookups/2026-11-25-mu-regime-read/RESULT.md
  run_date: 2026-11-25
  valid_until: 2027-02-15
  owner: fx-115
  links_to: []
  people: []
```

## studies/2026-11-flush-or-regime

Status: complete | Run: 2026-11-12 | Source: RESULTS.md

```yaml
- id: ud-flush-or-regime-h4-driver-rotation
  study: studies/2026-11-flush-or-regime
  type: quant
  region: US
  topic: ai-supply-chain
  hypothesis: What drove AI-stock returns changed between the October and November 2026 selloffs.
  verdict: supported
  finding: What drove AI-stock losses did change from October to November, mainly where each company sits in the supply chain rather than its funding.
  key_stats:
    - "adjusted p-value 0.011"
    - "the only one of 11 planned tests to pass the many-tests check"
  confidence: null
  numbers:
    - "CR2 p=0.005"
    - "funding Shapley E6=0.011"
    - "BH≈0.011"
    - "| 11 | **1** (`H4_WALD_E6_E7`, BH≈0.011) |"
  source_file: studies/2026-11-flush-or-regime/RESULTS.md
  run_date: 2026-11-12
  valid_until: null
  owner: fx-115
  links_to: [ud-flush-or-regime-h3-crowding]
  people: []
- id: ud-flush-or-regime-h2-seesaw
  study: studies/2026-11-flush-or-regime
  type: quant
  region: US
  topic: ai-supply-chain
  hypothesis: After a sharp split between AI chip suppliers and big-tech buyers, the gap snaps back, so extremes predict a rebound.
  verdict: killed
  finding: After sharp splits between chip suppliers and big-tech buyers, the gap did not reliably snap back. The see-saw describes the past but does not predict.
  key_stats:
    - "no reliable snap-back at 5, 21 or 63 trading days after costs"
    - "only 9 usable past cases"
  confidence: null
  numbers:
    - "CD p=0.45 (BH 0.73)"
    - "fwd NW p 0.30–0.76"
    - "net of 30bp at 5/21/63"
    - "pooled N=**9**"
  source_file: studies/2026-11-flush-or-regime/RESULTS.md
  run_date: 2026-11-12
  valid_until: null
  owner: fx-115
  links_to: [ud-flush-or-regime-h5-trough-signal]
  people: []
- id: ud-flush-or-regime-h3-crowding
  study: studies/2026-11-flush-or-regime
  type: quant
  region: US
  topic: ai-supply-chain
  hypothesis: Crowded positioning, more than valuation, explains which AI stocks fall most in a selloff.
  verdict: killed
  finding: Neither crowded positioning nor valuation explained which AI stocks fell most once each company's place in the supply chain was known.
  key_stats:
    - "crowding added nothing in 5 of 6 selloffs"
  confidence: null
  numbers:
    - "Falsifier not triggered (3/6)"
    - "crowding incr ≤0 in 5/6"
    - "adj R² 0.37 E6, 0.23 E7"
  source_file: studies/2026-11-flush-or-regime/RESULTS.md
  run_date: 2026-11-12
  valid_until: null
  owner: fx-115
  links_to: [ud-flush-or-regime-h4-driver-rotation]
  people: []
- id: ud-flush-or-regime-h1-semis-further-drop
  study: studies/2026-11-flush-or-regime
  type: quant
  region: US
  topic: ai-supply-chain
  hypothesis: After a deep drawdown, chip stocks are more likely than the broad US market to fall another 10%.
  verdict: inconclusive
  finding: Chip stocks fell another 10% more often than the broad market after deep drawdowns, but with only 15 cases the gap could be chance.
  key_stats:
    - "chips fell another 10% in 40% of cases, the broad market in 24%"
    - "p-value 0.465, far from significant"
  confidence: null
  numbers:
    - "Further-10% DD within 63 sessions"
    - "H1b SOX 40% vs SPX 24%, Fisher p=0.465 (BH 0.73)"
    - "SOX 10 / 15"
  source_file: studies/2026-11-flush-or-regime/RESULTS.md
  run_date: 2026-11-12
  valid_until: null
  owner: fx-115
  links_to: [ud-testing-nasdaq-bear-trap-reclaim-returns]
  people: []
- id: ud-flush-or-regime-h5-trough-signal
  study: studies/2026-11-flush-or-regime
  type: quant
  region: US
  topic: ai-supply-chain
  hypothesis: A signal taken after chip suppliers hit a low against big-tech buyers predicts their performance over the next three months.
  verdict: prior-only
  finding: This signal could not be tested yet. There were only 4 out-of-sample cases, below the 8 needed.
  key_stats:
    - "4 usable test cases, 8 required"
  confidence: null
  numbers:
    - "Troughs=15; train=10 / OOS=5; OOS L10 N=4"
    - "N ≥ 8"
  source_file: studies/2026-11-flush-or-regime/RESULTS.md
  run_date: 2026-11-12
  valid_until: null
  owner: fx-115
  links_to: [ud-flush-or-regime-h2-seesaw]
  people: []
- id: ud-flush-or-regime-supplier-drop-corrected
  study: studies/2026-11-flush-or-regime
  type: quant
  region: US
  topic: ai-supply-chain
  hypothesis: AI suppliers fell 12.9% on 5 November 2026, as an earlier note said.
  verdict: killed
  finding: Rebuilt from raw prices, AI suppliers fell 13.53% on 5 November, not 12.9%. The earlier note had put some companies in the wrong group.
  key_stats:
    - "supplier average fell 13.53%, not 12.9%"
  confidence: null
  numbers:
    - "Supplier EW 5 Nov"
    - "−13.53%"
    - "note −12.9 **SUPERSEDED** (neocloud layer error)"
  source_file: studies/2026-11-flush-or-regime/RESULTS.md
  run_date: 2026-11-12
  valid_until: null
  owner: fx-115
  links_to: []
  people: []
```

## studies/11-2026-fed-path-vs-term-premium

Status: complete | Run: 2026-11-19 | Source: RESULTS.md

```yaml
- id: ud-fed-path-vs-term-premium-h1-path-driven
  study: studies/11-2026-fed-path-vs-term-premium
  type: quant
  region: US
  topic: rates
  hypothesis: The extra pay investors demand for holding long bonds, the term premium, accounts for more than half of the 2026 rise in the 10-year Treasury yield.
  verdict: killed
  finding: Most of the 2026 rise in the ten-year Treasury yield came from expected Fed rate moves, not from extra pay for holding long bonds.
  key_stats:
    - "main model: yield up 86.6 basis points, term premium down 2.4"
    - "second model: term premium up 41.5, still under half the rise"
  confidence: null
  numbers:
    - "2026 windows end 2026-11-13"
    - "ACM: Δy10 +86.6, ΔRNY10 +89.0, ΔTP10 -2.4"
    - "KW: Δy10 +89.3, ΔRNY10 +47.8, ΔTP10 +41.5"
    - "Both below 0.5."
  source_file: studies/11-2026-fed-path-vs-term-premium/RESULTS.md
  run_date: 2026-11-19
  valid_until: null
  owner: fx-115
  links_to: [ud-fed-path-vs-term-premium-tp-level]
  people: []
- id: ud-fed-path-vs-term-premium-h2-hike-cycles
  study: studies/11-2026-fed-path-vs-term-premium
  type: quant
  region: US
  topic: rates
  hypothesis: The term premium's share of the yield rise in the 2026 hiking window is higher than in each of the six earlier hiking cycles.
  verdict: prior-only
  finding: The term premium's share of the 2026 rise was lower, not higher, than in earlier hiking cycles, but six past cycles are too few to test.
  key_stats:
    - "term premium share 0.10 in the main model, 0.46 in the second"
    - "6 past cycles, 8 needed for a test"
  confidence: null
  numbers:
    - "Prior only (N = 6 < 8)"
    - "2026 window TP share: ACM **0.10**, KW **0.46**"
  source_file: studies/11-2026-fed-path-vs-term-premium/RESULTS.md
  run_date: 2026-11-19
  valid_until: null
  owner: fx-115
  links_to: [ud-fed-path-vs-term-premium-h1-path-driven]
  people: []
- id: ud-fed-path-vs-term-premium-h3-no-decoupling
  study: studies/11-2026-fed-path-vs-term-premium
  type: quant
  region: US
  topic: rates
  hypothesis: The 10-year yield broke away from the 2-year yield in 2026.
  verdict: killed
  finding: The ten-year and two-year yields moved together about as closely as in a normal year.
  key_stats:
    - "R-squared 0.668, typical for a year"
    - "ranked 21st of 36 years for how closely they moved"
  confidence: null
  numbers:
    - "R² 2026 = **0.668** (β 0.73)"
    - "21 of 36 base years have R² ≤ 2026"
  source_file: studies/11-2026-fed-path-vs-term-premium/RESULTS.md
  run_date: 2026-11-19
  valid_until: null
  owner: fx-115
  links_to: []
  people: []
- id: ud-fed-path-vs-term-premium-h4-oil
  study: studies/11-2026-fed-path-vs-term-premium
  type: quant
  region: US
  topic: rates
  hypothesis: Oil prices drove the term premium in 2026.
  verdict: killed
  finding: Under the main model, oil prices did not reliably move the term premium in 2026. A second model disagrees, so the link is unproven.
  key_stats:
    - "main model test score 1.47, below the 2 needed"
    - "second model test score 3.22"
  confidence: null
  numbers:
    - "t < 2; fails BH"
    - "(2026-only sample): t 1.47, p 0.071"
    - "β 21.7, **t 3.22**"
  source_file: studies/11-2026-fed-path-vs-term-premium/RESULTS.md
  run_date: 2026-11-19
  valid_until: null
  owner: fx-115
  links_to: []
  people: []
- id: ud-fed-path-vs-term-premium-h5-fed-days
  study: studies/11-2026-fed-path-vs-term-premium
  type: quant
  region: US
  topic: rates
  hypothesis: On Fed decision days, the term premium responds to policy news in the 2-year yield.
  verdict: killed
  finding: On Fed decision days the term premium barely moved with policy news under the main model. A second model disagrees, and one live check remains.
  key_stats:
    - "main model slope 0.042, close to zero"
    - "second model slope 0.325"
  confidence: null
  numbers:
    - "β = **0.042**"
    - "t 0.48, R² 0.002"
    - "β **0.325**, **t 12.9**"
  source_file: studies/11-2026-fed-path-vs-term-premium/RESULTS.md
  run_date: 2026-11-19
  valid_until: 2026-12-09
  owner: fx-115
  links_to: []
  people: []
- id: ud-fed-path-vs-term-premium-tp-level
  study: studies/11-2026-fed-path-vs-term-premium
  type: quant
  region: US
  topic: rates
  hypothesis: The term premium in November 2026 is unusually high by historical standards.
  verdict: weak
  finding: The term premium is high compared with the years since 2008 but middling since 1990, and it was already that high at the end of 2025.
  key_stats:
    - "96th percentile since 2015 in the main model"
    - "43rd percentile since 1990"
  confidence: null
  numbers:
    - "high for the post-2008 era (96th percentile since 2015 under ACM, 99th under KW) but middling over 1990-2026 (43rd, 62nd); under ACM it was already that high on 31 Dec 2025"
  source_file: studies/11-2026-fed-path-vs-term-premium/README.md
  run_date: 2026-11-19
  valid_until: null
  owner: fx-115
  links_to: [ud-fed-path-vs-term-premium-h1-path-driven]
  people: []
```

## studies/11-2026-bandwidth-false-discovery

Status: complete | Run: 2026-11-17 | Source: README.md

```yaml
- id: ud-bandwidth-false-discovery-h1-noise-edges
  study: studies/11-2026-bandwidth-false-discovery
  type: quant
  region: US
  topic: methods
  hypothesis: Looking at stock data in finer detail makes a pattern-finder find more fake winning patterns in pure noise.
  verdict: supported
  finding: Finer detail made the pattern-finder find fake winning patterns in pure noise far more often, and the real data never beat the noise.
  key_stats:
    - "fake hits rose from 0.2-0.6% to 4.8-6.4% of tries"
    - "best real score 2.86, under the bar of 3"
  confidence: null
  numbers:
    - "rises from 0.2-0.6% at 4x to 4.8-6.4% at 0.25x"
    - "The real data never cleared t > 3 (max 2.86, at 0.25x, placebo p 0.10)"
  source_file: studies/11-2026-bandwidth-false-discovery/README.md
  run_date: 2026-11-17
  valid_until: null
  owner: fx-117
  links_to: [ud-testing-nasdaq-bear-trap-reclaim-returns]
  people: []
- id: ud-bandwidth-false-discovery-h2-net-losses
  study: studies/11-2026-bandwidth-false-discovery
  type: quant
  region: US
  topic: methods
  hypothesis: The pattern strategy made money after trading costs from 2005 to 2025.
  verdict: killed
  finding: After trading costs, every version of the strategy lost money from 2005 to 2025, mostly because it traded too often.
  key_stats:
    - "lost 3% to 9% a year after costs"
    - "trading costs about 10% a year"
  confidence: null
  numbers:
    - "Walk-forward 2005-2025, net of 10bp per side, nothing survives"
    - "All 28 cells lose money: -3% to -9% a year, net t -1.0 to -7.2"
    - "Turnover of about 0.40 a day costs about 10% a year"
  source_file: studies/11-2026-bandwidth-false-discovery/README.md
  run_date: 2026-11-17
  valid_until: null
  owner: fx-117
  links_to: [ud-bandwidth-false-discovery-gross-signal]
  people: []
- id: ud-bandwidth-false-discovery-gross-signal
  study: studies/11-2026-bandwidth-false-discovery
  type: quant
  region: US
  topic: methods
  hypothesis: Before trading costs, the pattern carries a real predictive signal.
  verdict: weak
  finding: Before costs there was a small signal, mostly rebounds after big overnight drops and stronger with smoother settings, but never strong enough to convince.
  key_stats:
    - "12 of 28 versions beat nearly all random comparisons"
    - "best test score 2.9, under the bar of 3"
  confidence: null
  numbers:
    - "Gross t is 0.4-2.9 (none above 3)"
    - "12 of 28 cells beat all or nearly all of 50 placebos"
    - "Spearman 0.63"
  source_file: studies/11-2026-bandwidth-false-discovery/README.md
  run_date: 2026-11-17
  valid_until: null
  owner: fx-117
  links_to: [ud-bandwidth-false-discovery-h1-noise-edges]
  people: []
- id: ud-bandwidth-false-discovery-holdout-2026
  study: studies/11-2026-bandwidth-false-discovery
  type: quant
  region: US
  topic: methods
  hypothesis: The pattern strategy works on unseen 2026 data.
  verdict: inconclusive
  finding: On unseen 2026 data every version made money, but it was really one bet on rebounds in a good year and not statistically significant.
  key_stats:
    - "made 7% to 40% a year after costs"
    - "219 trading days, 12 distinct bets"
  confidence: null
  numbers:
    - "2 Jan to 13 Nov 2026, 219 trading days"
    - "Net returns were positive in every cell (+7% to +40% annualised, net t 0.30-1.95)"
    - "The 28 cells use only 12 distinct pockets"
  source_file: studies/11-2026-bandwidth-false-discovery/README.md
  run_date: 2026-11-17
  valid_until: null
  owner: fx-117
  links_to: [ud-bandwidth-false-discovery-gross-signal]
  people: []
```

## studies/2026-11-testing-nasdaq-bear-trap

Status: interim | Run: 2026-11-10 | Source: RESULTS.md

```yaml
- id: ud-testing-nasdaq-bear-trap-reclaim-returns
  study: studies/2026-11-testing-nasdaq-bear-trap
  type: quant
  region: US
  topic: equities
  hypothesis: When the Nasdaq or S&P 500 climbs back above a broken low, returns afterwards beat those after similar drops.
  verdict: interim
  finding: So far, returns after an index climbed back above a broken low looked no better than after similar drops. Full-data tests are still pending.
  key_stats:
    - "best of 36 tests had a p-value of 0.09, not significant"
  confidence: null
  numbers:
    - "H0 not rejected"
    - "min placebo p = 0.09 over 36 tests"
  source_file: studies/2026-11-testing-nasdaq-bear-trap/RESULTS.md
  run_date: 2026-11-10
  valid_until: null
  owner: fx-115
  links_to: [ud-bandwidth-false-discovery-h1-noise-edges, ud-flush-or-regime-h1-semis-further-drop]
  people: []
- id: ud-testing-nasdaq-bear-trap-reclaim-rate
  study: studies/2026-11-testing-nasdaq-bear-trap
  type: quant
  region: US
  topic: equities
  hypothesis: Broken lows in the Nasdaq and S&P 500 are usually reclaimed within 10 days.
  verdict: interim
  finding: In the first study, broken lows were usually reclaimed within 10 days, 86% of the time for the Nasdaq and 78% for the S&P.
  key_stats:
    - "Nasdaq 37 of 43 cases"
    - "S&P 67 of 86 cases"
  confidence: null
  numbers:
    - "Nasdaq 86% (37/43)"
    - "S&P 78% (67/86) within 10 days"
  source_file: studies/2026-11-testing-nasdaq-bear-trap/RESULTS.md
  run_date: 2026-11-10
  valid_until: null
  owner: fx-115
  links_to: [ud-testing-nasdaq-bear-trap-retest-rate]
  people: []
- id: ud-testing-nasdaq-bear-trap-retest-rate
  study: studies/2026-11-testing-nasdaq-bear-trap
  type: quant
  region: US
  topic: equities
  hypothesis: After a reclaim, prices usually fall back to test the old low within 60 days.
  verdict: interim
  finding: In the first study, prices usually came back down to test the old low within 60 days, 72% of the time for the Nasdaq and 79% for the S&P.
  key_stats:
    - "Nasdaq 72%, S&P 79%"
  confidence: null
  numbers:
    - "Nasdaq 72%; S&P 79% within 60 days"
  source_file: studies/2026-11-testing-nasdaq-bear-trap/RESULTS.md
  run_date: 2026-11-10
  valid_until: null
  owner: fx-115
  links_to: [ud-testing-nasdaq-bear-trap-reclaim-rate]
  people: []
```

## quick-lookups/2026-11-26-thanksgiving-week-drawdown

Status: interim | Run: 2026-11-26 | Source: quick-lookups/2026-11-26-thanksgiving-week-drawdown/RESULT.md

```yaml
- id: ud-thanksgiving-week-drawdown-c1-seasonal
  study: quick-lookups/2026-11-26-thanksgiving-week-drawdown
  type: quant
  region: US
  topic: equities
  hypothesis: The S&P 500 rises more often in Thanksgiving week than in other four-day stretches.
  verdict: weak
  finding: Thanksgiving week rose in most years, more often than ordinary weeks, but the main test narrowly missed the bar once many tests were accounted for.
  key_stats:
    - "up in 53 of 76 years, versus 56.6% for other weeks"
    - "adjusted p-value 0.053, just above 0.05"
  confidence: 60
  numbers:
    - "week up in **53 of 76 years (69.7%)** vs 56.6% for other 4-day windows; raw p 0.022, BH p 0.053"
    - "the week up-rate's BH p drops below 0.05"
  source_file: quick-lookups/2026-11-26-thanksgiving-week-drawdown/RESULT.md
  run_date: 2026-11-26
  valid_until: 2027-01-04
  owner: fx-115
  links_to: [ud-thanksgiving-week-drawdown-c2-decay]
  people: []
- id: ud-thanksgiving-week-drawdown-c2-decay
  study: quick-lookups/2026-11-26-thanksgiving-week-drawdown
  type: quant
  region: US
  topic: equities
  hypothesis: The Thanksgiving-week edge has faded since 1988.
  verdict: killed
  finding: Thanksgiving week rose a bit less often after 1988 than before, but the drop is small enough to be chance.
  key_stats:
    - "up 73.7% of years in 1950-1987, 65.8% in 1988-2025"
    - "p-value 0.618"
  confidence: 70
  numbers:
    - "hit rate **73.7% (1950-1987) vs 65.8% (1988-2025)**, Fisher p 0.618"
  source_file: quick-lookups/2026-11-26-thanksgiving-week-drawdown/RESULT.md
  run_date: 2026-11-26
  valid_until: 2027-01-04
  owner: fx-115
  links_to: [ud-thanksgiving-week-drawdown-c1-seasonal]
  people: []
- id: ud-thanksgiving-week-drawdown-c3-drawdown
  study: quick-lookups/2026-11-26-thanksgiving-week-drawdown
  type: quant
  region: US
  topic: equities
  hypothesis: When the S&P 500 enters Thanksgiving week down 10-20% from its high, it is less likely to finish the year above its Black Friday close.
  verdict: inconclusive
  finding: In past corrections the market finished the year above Black Friday less often, but with 15 cases the gap may be chance.
  key_stats:
    - "year-end up in 6 of 15 correction years, 43 of 60 other years"
    - "likely range 22.7% to 60.9%"
  confidence: 55
  numbers:
    - "year-end up in **6 of 15 correction years (40.0%)** vs 43 of 60 other years (71.7%); 90% interval 22.7% to 60.9% spans 50%"
  source_file: quick-lookups/2026-11-26-thanksgiving-week-drawdown/RESULT.md
  run_date: 2026-11-26
  valid_until: 2027-01-04
  owner: fx-115
  links_to: [ud-flush-or-regime-h1-semis-further-drop]
  people: []
- id: ud-thanksgiving-week-drawdown-c4-liquidity
  study: quick-lookups/2026-11-26-thanksgiving-week-drawdown
  type: quant
  region: US
  topic: equities
  hypothesis: The S&P 500 moves less on Black Friday than on a normal trading day.
  verdict: weak
  finding: Black Friday moves were about as large as on a normal day; earlier and later decades pointed opposite ways.
  key_stats:
    - "typical Black Friday move 0.92 times a normal day"
    - "p-value 0.880"
  confidence: 50
  numbers:
    - "median absolute move **0.92x** a normal day, Mann-Whitney p 0.880; halves disagree"
  source_file: quick-lookups/2026-11-26-thanksgiving-week-drawdown/RESULT.md
  run_date: 2026-11-26
  valid_until: 2027-01-04
  owner: fx-115
  links_to: []
  people: []
```

## quick-lookups/2026-11-27-token-pricing

Status: complete | Run: 2026-11-27 | Source: quick-lookups/2026-11-27-token-pricing/RESULT.md

```yaml
- id: ud-token-pricing-crack
  study: quick-lookups/2026-11-27-token-pricing
  type: quant
  region: US
  topic: ai-pricing
  hypothesis: Falling AI token prices are a crack in the AI revenue thesis, with business spending not keeping up as prices fall.
  verdict: killed
  finding: Not on the pre-registered tests, since spending still outran price cuts, but a reviewer found two test flaws favouring that result and reads it as weak.
  key_stats:
    - "token prices down 43% and spend up 20% over the latest 13 weeks"
    - "reviewer reading weak, about 55% confidence"
  confidence: 45
  numbers:
    - "price -43%, volume +108%, spend +20%"
    - "latest 13 weeks"
    - "Reviewer reading: WEAK, about 55% confidence."
  source_file: quick-lookups/2026-11-27-token-pricing/RESULT.md
  run_date: 2026-11-27
  valid_until: 2027-01-10
  owner: fx-115
  links_to: [ud-token-pricing-anthropic-elasticity, ud-token-pricing-mix, ud-token-pricing-revenue-per-compute]
  people: []
- id: ud-token-pricing-anthropic-elasticity
  study: quick-lookups/2026-11-27-token-pricing
  type: quant
  region: US
  topic: ai-pricing
  hypothesis: Spending on Anthropic's models still rises faster than its token prices fall.
  verdict: weak
  finding: Only just, since Anthropic's spend grew 5.9% over 13 weeks while its prices fell, and that margin has shrunk every week for two months.
  key_stats:
    - "Anthropic token spend up 5.9% over 13 weeks"
    - "Anthropic price-sensitivity reading of 1.10, close to the tipping point"
  confidence: null
  numbers:
    - "13-week spend growth **+5.9%**"
    - "1.10"
  source_file: quick-lookups/2026-11-27-token-pricing/RESULT.md
  run_date: 2026-11-27
  valid_until: 2027-01-10
  owner: fx-115
  links_to: [ud-token-pricing-crack]
  people: []
- id: ud-token-pricing-mix
  study: quick-lookups/2026-11-27-token-pricing
  type: quant
  region: US
  topic: ai-pricing
  hypothesis: Average token prices fell mostly because customers switched to cheaper models, not because prices were cut.
  verdict: weak
  finding: It depends on definitions, since the same model versions did not get cheaper, but newer versions in each tier cost far less, so tier for tier prices fell 65%.
  key_stats:
    - "same-version prices up 2% since the March peak"
    - "tier-for-tier prices down 65% since the March peak"
  confidence: null
  numbers:
    - "Like-for-like **+2%**"
    - "Like-for-like **-65%**"
  source_file: quick-lookups/2026-11-27-token-pricing/RESULT.md
  run_date: 2026-11-27
  valid_until: null
  owner: fx-115
  links_to: [ud-token-pricing-crack]
  people: []
- id: ud-token-pricing-share-vs-price
  study: quick-lookups/2026-11-27-token-pricing
  type: quant
  region: US
  topic: ai-pricing
  hypothesis: Anthropic's share of business AI token spend does not respond to its price relative to OpenAI.
  verdict: prior-only
  finding: Too little data to test, since Anthropic's share tends to slip when it gets relatively pricier, but the sample equals about 5.8 independent points.
  key_stats:
    - "effective sample of only 5.8 independent data points"
  confidence: null
  numbers:
    - "effective n = 5.8"
  source_file: quick-lookups/2026-11-27-token-pricing/RESULT.md
  run_date: 2026-11-27
  valid_until: null
  owner: fx-115
  links_to: []
  people: []
- id: ud-token-pricing-revenue-per-compute
  study: quick-lookups/2026-11-27-token-pricing
  type: quant
  region: US
  topic: ai-pricing
  hypothesis: Anthropic's revenue per dollar of compute is falling.
  verdict: killed
  finding: Not versus the start of 2026, but revenue per compute dollar fell 17% in the latest quarter, from 2.08 to 1.72, which the reviewer counts as falling.
  key_stats:
    - "revenue per compute dollar of 1.40 in Q1 2026, 2.08 in Q2 and 1.72 in Q3"
    - "compute margin proxy down 10.1 points in the latest quarter"
  confidence: null
  numbers:
    - "**1.40** (Q1 2026), **2.08** (Q2), **1.72** (Q3)"
    - "revenue per compute dollar fell **17%**, from **2.08** to **1.72**"
    - "the compute margin proxy fell **10.1pp**"
  source_file: quick-lookups/2026-11-27-token-pricing/RESULT.md
  run_date: 2026-11-27
  valid_until: null
  owner: fx-115
  links_to: [ud-token-pricing-crack]
  people: []
```

## studies/11-2026-growth-value-derating

Status: complete | Run: 2026-11-28 | Source: studies/11-2026-growth-value-derating/RESULTS.md

```yaml
- id: ud-growth-value-derating-earnings-driven
  study: studies/11-2026-growth-value-derating
  type: quant
  region: US
  topic: equities
  hypothesis: The 2026 fall in the S&P 500 Growth forward P/E was driven by rising forward earnings rather than falling prices.
  verdict: supported
  finding: Yes, rising earnings forecasts explain 95.5% of the drop from 29.32 to 17.10 times earnings, while Growth stock prices barely moved.
  key_stats:
    - "rising earnings explain 95.5% of the P/E drop"
    - "P/E down from 29.32 to 17.10 between 31 Oct 2025 and 27 Nov 2026"
  confidence: null
  numbers:
    - "account for **95.5%** of the Growth P/E drop from **29.32x** (31 Oct 2025) to **17.10x** (27 Nov 2026)"
  source_file: studies/11-2026-growth-value-derating/RESULTS.md
  run_date: 2026-11-28
  valid_until: 2027-01-08
  owner: fx-115
  links_to: [ud-growth-value-derating-reshuffle-artefact, ud-growth-value-derating-crossing, ud-growth-value-derating-inflated-estimates]
  people: []
- id: ud-growth-value-derating-reshuffle-artefact
  study: studies/11-2026-growth-value-derating
  type: quant
  region: US
  topic: equities
  hypothesis: The December 2025 index reshuffle is a material cause of the Growth P/E drop.
  verdict: killed
  finding: No, the reshuffle accounts for only 5.7% of the drop, and no alternative window or start date pushes it near the 30% bar.
  key_stats:
    - "reshuffle share 5.7% of the drop, 10.1% at most across variants"
  confidence: null
  numbers:
    - "COMPOSITION **5.7%**; 5.1% to 10.1% across variants"
    - "COMPOSITION > 30%"
  source_file: studies/11-2026-growth-value-derating/RESULTS.md
  run_date: 2026-11-28
  valid_until: 2027-01-08
  owner: fx-115
  links_to: [ud-growth-value-derating-earnings-driven]
  people: []
- id: ud-growth-value-derating-crossing
  study: studies/11-2026-growth-value-derating
  type: quant
  region: US
  topic: equities
  hypothesis: Growth fell below Value on P/E mainly because Growth earnings estimates rose faster, not because Growth prices fell.
  verdict: supported
  finding: Mostly, faster Growth earnings growth explains 66% of the gap that closed, and Value's stronger prices explain 23%.
  key_stats:
    - "faster Growth earnings growth explains 66% of the gap"
    - "Value's stronger prices explain 23% of the gap"
  confidence: null
  numbers:
    - "**66%** from faster Growth EPS growth"
    - "**23%** from Value's price outperforming"
  source_file: studies/11-2026-growth-value-derating/RESULTS.md
  run_date: 2026-11-28
  valid_until: 2027-01-08
  owner: fx-115
  links_to: [ud-growth-value-derating-earnings-driven]
  people: []
- id: ud-growth-value-derating-inflated-estimates
  study: studies/11-2026-growth-value-derating
  type: quant
  region: US
  topic: equities
  hypothesis: The earnings behind the Growth de-rating are inflated, with the biggest Growth companies' cash flow not keeping up with their reported profits.
  verdict: supported
  finding: The pre-set test passed because free cash after investment fell, but operating cash still roughly covers profits, so this signals heavy spending, not proven inflated earnings.
  key_stats:
    - "free cash after stock pay down 21.1 points, to 39.9% of profits"
    - "operating cash 1.14 times profits, from 1.21"
    - "capex at 2.98 times depreciation"
  confidence: 50
  numbers:
    - "**61.0%** to **39.9%**"
    - "-21.1pp"
    - "capex ran at **2.98x** depreciation"
    - "1.21 to 1.14"
  source_file: studies/11-2026-growth-value-derating/RESULTS.md
  run_date: 2026-11-28
  valid_until: 2027-01-08
  owner: fx-115
  links_to: [ud-growth-value-derating-cash-backed-catch-up]
  people: []
- id: ud-growth-value-derating-cash-backed-catch-up
  study: studies/11-2026-growth-value-derating
  type: quant
  region: US
  topic: equities
  hypothesis: Growth's earnings catch-up is backed by cash, with cash conversion holding up and estimate revisions positive.
  verdict: killed
  finding: No, revisions were positive, but cash conversion fell 21.1 points, well past the 10-point limit set for this benign reading.
  key_stats:
    - "cash conversion down 21.1 points against a 10-point limit"
  confidence: null
  numbers:
    - "-21.1pp against a floor of -10pp"
  source_file: studies/11-2026-growth-value-derating/RESULTS.md
  run_date: 2026-11-28
  valid_until: 2027-01-08
  owner: fx-115
  links_to: [ud-growth-value-derating-inflated-estimates]
  people: []
```
