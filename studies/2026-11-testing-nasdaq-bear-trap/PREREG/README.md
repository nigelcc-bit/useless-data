# Pre-registration

Each study's hypotheses, primary tests, thresholds and kill criteria are written
here and **committed before the study is run on real data**. The commit
timestamp is the proof. Any change after first run goes in a new commit with a
"DEVIATION:" line in the study file explaining what changed and why.

## Tier 1 test budget

| Study | Primary tests | Within-study correction |
|---|---|---|
| A Null models | 4 (2 indices x reclaim/retest rate vs block null) | Bonferroni, alpha 0.0125 |
| B Second sweep | 12 (2 definitions x 2 indices x 3 horizons) | Bonferroni, alpha 0.0042; BH q = 0.05 reported |
| C Survival | 2 (log-rank, observed vs block null retest curve, per index) | Bonferroni, alpha 0.025 |
| D Panel | 2 (pooled mean excess r60, r120) | Bonferroni, alpha 0.025 |
| **Total** | **20** | Across Tier 1: Benjamini-Hochberg q = 0.05 on all 20 p-values |

Everything else (other null models, pseudo-level DiD, Cox hazard ratios,
per-market rows, analog shares, secondary universe) is **descriptive** and is
not to be quoted as a finding without a new pre-registered test on fresh data.

## Parameters inherited from Study 1 (not re-tuned)

N = 120, K = 10, min age 10, cooldown 20, retest window 60, horizons 20/60/120,
drawdown-matched pool 5-20% below the 120-day high, placebo B = 5,000, seed 7.
N = 120 and the 10-20% analog band were chosen with the Nov 2026 event in view
(Study 1, sections 6.2 and 6.6); Tier 1 inherits that and does not re-tune them.
