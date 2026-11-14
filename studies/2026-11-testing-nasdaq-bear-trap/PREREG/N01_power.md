# N01: Power (MDE) and equivalence (TOST) for Study 1 reclaim returns

Written 2026-11-14, before any code for this analysis was written or run.
Notebook: `notebooks/n01_power_and_equivalence.ipynb`. Logic: `src/power.py`.

## Why
Study 1 found no forward-return edge after a reclaim (all placebo p >= 0.09).
A null result is only informative if the test could have detected an edge of
a size that matters. N01 asks two things:

1. **MDE:** with Study 1's sample sizes and observed dispersion, what is the
   smallest excess return the test would detect with 80% power?
2. **Equivalence:** can we positively conclude that reclaim returns are
   *within* +/-2 or +/-5 percentage points of the drawdown-matched mean, rather
   than only failing to reject a difference?

## Hindsight status (read first)
The Study 1 data have already been seen: the reclaim means are known to sit
within about 1.5 points of the benchmark (Study 1, section 7.3). N01 is
therefore a **re-expression of known data**, not new evidence. Its outcome is
partly foreseeable. The equivalence bounds (+/-2%, +/-5%) were set by the study
owner on 2026-11-14, are round numbers, and are not tuned. No result from N01
may be quoted as an out-of-sample confirmation.

## Data
- Per-event returns: `tests/fixtures/expected_ndx_events.csv` (Appendix B, NDX
  1985-2026) and `tests/fixtures/expected_spx_events.csv` (Appendix C, SPX
  1950-2026). These are the Study 1 primary-specification (N = 120, K = 10)
  event lists, returns rounded to 0.1 point.
- Sample per index and horizon h in {20, 60, 120}: events with
  `reclaimed == True` and non-missing `r{h}`. This is the Study 1 "after
  reclaim" sample. n and SD are computed from it, not recalled.
- Benchmark mu0 (drawdown-matched mean, days 5-20% below the 120-day high),
  from Study 1 Table 7.3, treated as a known constant (pool sizes 3,338 NDX
  and 5,837 SPX days):

| Index | r20 | r60 | r120 |
|---|---|---|---|
| NDX | +1.6% | +5.0% | +10.0% |
| SPX | +0.7% | +1.9% | +3.6% |

### Anchor checks (stop if any fails)
- Fixture reclaim means must match Study 1 Table 7.3 "after reclaim" within
  0.11 point (rounding): NDX +1.5 / +4.6 / +11.6, SPX +0.5 / +2.0 / +3.7.
- Reclaimed counts must equal Study 1 Table 7.2: NDX 37, SPX 67.

## Analysis 1: MDE simulation (descriptive, not a hypothesis test)
- Test whose power is computed: one-sided one-sample t-test of
  H1: mean(r_h) > mu0, alpha = 0.05, df = n - 1.
  (Study 1 used a placebo resampling test; the t-test is the parametric
  analogue using the event-sample SD, as specified.)
- Data-generating process: n draws from Normal(mu0 + delta, sd_obs), where n
  and sd_obs are the Study 1 values for that index and horizon.
- Power at delta: share of R = 10,000 simulated samples that reject.
  Common random numbers across delta (one fixed draw matrix per cell), seed 7.
- MDE: smallest delta with power >= 0.80, found by bisection on
  [0, 1.0] (return units) to a tolerance of 0.0005 (0.05 point).
- Cross-check: exact MDE from the noncentral t distribution. If simulated and
  exact MDE differ by more than 0.2 point, stop and investigate.
- Grid: 2 indices x 3 horizons = 6 cells. Also reported, descriptively, the
  MDE at Study 1's Bonferroni alpha (0.05 / 36 = 0.00139), and the MDE in SD
  units (delta / sd).
- Output: `results/N01_power/mde.csv`, printed verbatim in the notebook.

## Analysis 2: TOST equivalence (12 tests)
- Statistic: d = mean(r_h) - mu0, SE = sd / sqrt(n), df = n - 1.
- Bounds b in {0.02, 0.05}: absolute return, i.e. +/-2 and +/-5 percentage
  points of h-day return around mu0, at every horizon.
- Two one-sided t-tests: H0a: d <= -b vs d > -b; H0b: d >= +b vs d < +b.
  Each at alpha = 0.05. Equivalence is declared iff both reject, i.e.
  p_TOST = max(p_a, p_b) < 0.05 (equivalently, the 90% CI for d lies inside
  (-b, +b)). By intersection-union, each TOST is a level-0.05 test.
- Family: 2 bounds x 3 horizons x 2 indices = **12 tests**. Decision rule is
  per test at alpha 0.05 as specified. Benjamini-Hochberg at q = 0.10 over
  the 12 p_TOST values is also reported (RESEARCH_PROTOCOL rule 5).
- Note: the bounds are nested, so equivalence at +/-2 implies it at +/-5.
- Output: `results/N01_power/tost.csv`; all 12 rows logged to
  `outputs/tests_run.csv`.

## Interpretation rules (fixed now)
- Equivalence at +/-2: "any reclaim edge at this horizon is smaller than
  2 points" is supported.
- Equivalence at +/-5 only: "any edge is smaller than 5 points"; a 2-5 point
  edge cannot be excluded.
- Neither: inconclusive. This is **not** evidence of an edge; it means the
  sample is too small or too dispersed.
- MDE above 5 points at a horizon: Study 1's null at that horizon is weak
  evidence of no edge.

## Known limitations
- Events overlap in time (120-day windows, clustered bear markets), so the
  effective sample is smaller than n. The iid MDE is optimistic (a lower
  bound) and TOST p-values are anti-conservative. A cluster-robust version is
  out of scope here.
- Returns in the fixtures are rounded to 0.1 point; the effect on SD is
  negligible at these dispersions.
- mu0 carries sampling error and is rounded to 0.1 point; treated as fixed.
- Returns are heavy-tailed (e.g. NDX 2000-02); the Normal DGP is an
  approximation.
