# Findings: useless-data

Last updated: 2026-11-25

Nothing here is a trading recommendation.

One section per study; re-running a study replaces its section, never adds a
second one. Every finding uses the schema in [README.md](README.md#findings).
Every string under `numbers` is copied verbatim from `source_file`, and
`scripts/check_findings.py` enforces this.

## studies/2026-11-flush-or-regime

Status: complete | Run: 2026-11-12 | Source: RESULTS.md

```yaml
- id: ud-flush-or-regime-h4-driver-rotation
  study: studies/2026-11-flush-or-regime
  type: quant
  region: US
  topic: ai-supply-chain
  claim: What explained AI-stock returns changed between the October and November 2026 selloffs, mainly which part of the supply chain a company sits in.
  verdict: supported
  confidence: null
  numbers:
    - "CR2 p=0.005"
    - "funding Shapley E6=0.011"
    - "BH≈0.011"
  source_file: studies/2026-11-flush-or-regime/RESULTS.md
  run_date: 2026-11-12
  valid_until: null
  owner_bot: vera
  links_to: [ud-flush-or-regime-h3-crowding]
  people: []
- id: ud-flush-or-regime-h2-seesaw
  study: studies/2026-11-flush-or-regime
  type: quant
  region: US
  topic: ai-supply-chain
  claim: After sharp splits between AI chip suppliers and big-tech buyers, the gap did not reliably snap back. The see-saw describes the past but does not predict.
  verdict: killed
  confidence: null
  numbers:
    - "CD p=0.45 (BH 0.73)"
    - "fwd NW p 0.30–0.76"
    - "63d +3.5% net 7/9 = PRIOR"
  source_file: studies/2026-11-flush-or-regime/RESULTS.md
  run_date: 2026-11-12
  valid_until: null
  owner_bot: vera
  links_to: [ud-flush-or-regime-h5-trough-signal]
  people: []
- id: ud-flush-or-regime-h3-crowding
  study: studies/2026-11-flush-or-regime
  type: quant
  region: US
  topic: ai-supply-chain
  claim: Crowded positioning did not explain which AI stocks fell most once each company's supply-chain layer was known. Valuation did not either.
  verdict: killed
  confidence: null
  numbers:
    - "Falsifier not triggered (3/6)"
    - "crowding incr ≤0 in 5/6"
    - "adj R² 0.37 E6, 0.23 E7"
  source_file: studies/2026-11-flush-or-regime/RESULTS.md
  run_date: 2026-11-12
  valid_until: null
  owner_bot: vera
  links_to: [ud-flush-or-regime-h4-driver-rotation]
  people: []
- id: ud-flush-or-regime-h1-semis-further-drop
  study: studies/2026-11-flush-or-regime
  type: quant
  region: US
  topic: ai-supply-chain
  claim: After a deep drawdown, chip stocks fell another 10% more often than the S&P 500, but the samples are too small to call it a real difference.
  verdict: inconclusive
  confidence: null
  numbers:
    - "H1b SOX 40% vs SPX 24%, Fisher p=0.465 (BH 0.73)"
    - "SOX 10 / 15"
  source_file: studies/2026-11-flush-or-regime/RESULTS.md
  run_date: 2026-11-12
  valid_until: null
  owner_bot: vera
  links_to: [ud-testing-nasdaq-bear-trap-reclaim-returns]
  people: []
- id: ud-flush-or-regime-h5-trough-signal
  study: studies/2026-11-flush-or-regime
  type: quant
  region: US
  topic: ai-supply-chain
  claim: A signal for chip suppliers bouncing back after a relative low could not be tested; there were only 4 out-of-sample cases, below the 8 required.
  verdict: prior-only
  confidence: null
  numbers:
    - "Troughs=15; train=10 / OOS=5; OOS L10 N=4"
  source_file: studies/2026-11-flush-or-regime/RESULTS.md
  run_date: 2026-11-12
  valid_until: null
  owner_bot: vera
  links_to: [ud-flush-or-regime-h2-seesaw]
  people: []
- id: ud-flush-or-regime-supplier-drop-corrected
  study: studies/2026-11-flush-or-regime
  type: quant
  region: US
  topic: ai-supply-chain
  claim: Rechecked against raw prices, AI suppliers fell more on 5 November than an earlier note said; that note had put some companies in the wrong group.
  verdict: supported
  confidence: null
  numbers:
    - "−13.53%"
    - "note −12.9 **SUPERSEDED** (neocloud layer error)"
  source_file: studies/2026-11-flush-or-regime/RESULTS.md
  run_date: 2026-11-12
  valid_until: null
  owner_bot: vera
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
  claim: The 2026 rise in the 10-year Treasury yield came mostly from expected Fed rate moves, not from extra pay demanded for holding long bonds.
  verdict: supported
  confidence: null
  numbers:
    - "ACM: Δy10 +86.6, ΔRNY10 +89.0, ΔTP10 -2.4"
    - "KW: Δy10 +89.3, ΔRNY10 +47.8, ΔTP10 +41.5"
    - "Both below 0.5."
  source_file: studies/11-2026-fed-path-vs-term-premium/RESULTS.md
  run_date: 2026-11-19
  valid_until: null
  owner_bot: vera
  links_to: [ud-fed-path-vs-term-premium-tp-level]
  people: []
- id: ud-fed-path-vs-term-premium-h2-hike-cycles
  study: studies/11-2026-fed-path-vs-term-premium
  type: quant
  region: US
  topic: rates
  claim: The long-bond premium's share of the 2026 yield rise was lower than in earlier hiking cycles, but six past cycles are too few to test.
  verdict: prior-only
  confidence: null
  numbers:
    - "Prior only (N = 6 < 8)"
    - "2026 window TP share: ACM **0.10**, KW **0.46**"
  source_file: studies/11-2026-fed-path-vs-term-premium/RESULTS.md
  run_date: 2026-11-19
  valid_until: null
  owner_bot: vera
  links_to: [ud-fed-path-vs-term-premium-h1-path-driven]
  people: []
- id: ud-fed-path-vs-term-premium-h3-no-decoupling
  study: studies/11-2026-fed-path-vs-term-premium
  type: quant
  region: US
  topic: rates
  claim: In 2026 the 10-year yield did not break away from the 2-year yield; their daily moves stayed about as linked as in a typical year.
  verdict: killed
  confidence: null
  numbers:
    - "R² 2026 = **0.668** (β 0.73)"
    - "21 of 36 base years have R² ≤ 2026"
  source_file: studies/11-2026-fed-path-vs-term-premium/RESULTS.md
  run_date: 2026-11-19
  valid_until: null
  owner_bot: vera
  links_to: []
  people: []
- id: ud-fed-path-vs-term-premium-h4-oil
  study: studies/11-2026-fed-path-vs-term-premium
  type: quant
  region: US
  topic: rates
  claim: Oil prices did not reliably move the long-bond premium in 2026 under the main model. A second model disagrees, so any link depends on the model.
  verdict: killed
  confidence: null
  numbers:
    - "t 1.47, p 0.071"
    - "β 21.7, **t 3.22**"
  source_file: studies/11-2026-fed-path-vs-term-premium/RESULTS.md
  run_date: 2026-11-19
  valid_until: null
  owner_bot: vera
  links_to: []
  people: []
- id: ud-fed-path-vs-term-premium-h5-fed-days
  study: studies/11-2026-fed-path-vs-term-premium
  type: quant
  region: US
  topic: rates
  claim: On Fed decision days the long-bond premium barely reacted to policy news under the main model. The second model disagrees; one live check remains.
  verdict: killed
  confidence: null
  numbers:
    - "t 0.48, R² 0.002"
    - "β **0.325**, **t 12.9**"
  source_file: studies/11-2026-fed-path-vs-term-premium/RESULTS.md
  run_date: 2026-11-19
  valid_until: 2026-12-09
  owner_bot: vera
  links_to: []
  people: []
- id: ud-fed-path-vs-term-premium-tp-level
  study: studies/11-2026-fed-path-vs-term-premium
  type: quant
  region: US
  topic: rates
  claim: The long-bond premium is high by post-2008 standards but middling since 1990, and under the main model it was already that high at end-2025.
  verdict: supported
  confidence: null
  numbers:
    - "96th percentile since 2015 under ACM, 99th under KW"
    - "(43rd, 62nd)"
  source_file: studies/11-2026-fed-path-vs-term-premium/README.md
  run_date: 2026-11-19
  valid_until: null
  owner_bot: vera
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
  claim: Making a pattern-finder look at stock data in finer detail makes it find fake winning patterns in pure noise far more often.
  verdict: supported
  confidence: null
  numbers:
    - "rises from 0.2-0.6% at 4x to 4.8-6.4% at 0.25x"
    - "The real data never cleared t > 3 (max 2.86, at 0.25x, placebo p 0.10)"
  source_file: studies/11-2026-bandwidth-false-discovery/README.md
  run_date: 2026-11-17
  valid_until: null
  owner_bot: tilly
  links_to: [ud-testing-nasdaq-bear-trap-reclaim-returns]
  people: []
- id: ud-bandwidth-false-discovery-h2-net-losses
  study: studies/11-2026-bandwidth-false-discovery
  type: quant
  region: US
  topic: methods
  claim: After trading costs, every version of the pattern strategy lost money from 2005 to 2025, mostly because it traded too often.
  verdict: supported
  confidence: null
  numbers:
    - "All 28 cells lose money: -3% to -9% a year, net t -1.0 to -7.2"
    - "Turnover of about 0.40 a day costs about 10% a year"
  source_file: studies/11-2026-bandwidth-false-discovery/README.md
  run_date: 2026-11-17
  valid_until: null
  owner_bot: tilly
  links_to: [ud-bandwidth-false-discovery-gross-signal]
  people: []
- id: ud-bandwidth-false-discovery-gross-signal
  study: studies/11-2026-bandwidth-false-discovery
  type: quant
  region: US
  topic: methods
  claim: Before costs there was a small real signal, mostly rebounds after big overnight drops, and it was stronger with smoother, less detailed settings.
  verdict: weak
  confidence: null
  numbers:
    - "Gross t is 0.4-2.9 (none above 3)"
    - "12 of 28 cells beat all or nearly all of 50 placebos"
    - "Spearman 0.63"
  source_file: studies/11-2026-bandwidth-false-discovery/README.md
  run_date: 2026-11-17
  valid_until: null
  owner_bot: tilly
  links_to: [ud-bandwidth-false-discovery-h1-noise-edges]
  people: []
- id: ud-bandwidth-false-discovery-holdout-2026
  study: studies/11-2026-bandwidth-false-discovery
  type: quant
  region: US
  topic: methods
  claim: On unseen 2026 data every version made money, but it was really one bet on rebounds in a good year and not statistically significant.
  verdict: inconclusive
  confidence: null
  numbers:
    - "Net returns were positive in every cell (+7% to +40% annualised, net t 0.30-1.95)"
    - "The 28 cells use only 12 distinct pockets"
    - "219 trading days"
  source_file: studies/11-2026-bandwidth-false-discovery/README.md
  run_date: 2026-11-17
  valid_until: null
  owner_bot: tilly
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
  claim: When the Nasdaq or S&P 500 climbs back above a broken low, later returns look no better than after similar drops without that signal.
  verdict: interim
  confidence: null
  numbers:
    - "H0 not rejected"
    - "min placebo p = 0.09 over 36 tests"
  source_file: studies/2026-11-testing-nasdaq-bear-trap/RESULTS.md
  run_date: 2026-11-10
  valid_until: null
  owner_bot: vera
  links_to: [ud-bandwidth-false-discovery-h1-noise-edges, ud-flush-or-regime-h1-semis-further-drop]
  people: []
- id: ud-testing-nasdaq-bear-trap-reclaim-rate
  study: studies/2026-11-testing-nasdaq-bear-trap
  type: quant
  region: US
  topic: equities
  claim: Broken lows in the Nasdaq and S&P 500 were usually reclaimed within 10 days.
  verdict: interim
  confidence: null
  numbers:
    - "Nasdaq 86% (37/43)"
    - "S&P 78% (67/86)"
  source_file: studies/2026-11-testing-nasdaq-bear-trap/RESULTS.md
  run_date: 2026-11-10
  valid_until: null
  owner_bot: vera
  links_to: [ud-testing-nasdaq-bear-trap-retest-rate]
  people: []
- id: ud-testing-nasdaq-bear-trap-retest-rate
  study: studies/2026-11-testing-nasdaq-bear-trap
  type: quant
  region: US
  topic: equities
  claim: After a reclaim, prices usually came back down to test the old low again within 60 days.
  verdict: interim
  confidence: null
  numbers:
    - "Nasdaq 72%; S&P 79% within 60 days"
  source_file: studies/2026-11-testing-nasdaq-bear-trap/RESULTS.md
  run_date: 2026-11-10
  valid_until: null
  owner_bot: vera
  links_to: [ud-testing-nasdaq-bear-trap-reclaim-rate]
  people: []
```
