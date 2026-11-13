# Study specification — testing-nasdaq-bear-trap

**Governing rules:** repository root `RESEARCH_PROTOCOL.md` and local [`AGENTS.md`](AGENTS.md).

**Status:** interim. Study 1 design captured below; Tier 1 pre-registration lives in [`PREREG/`](PREREG/) and must not be silently edited after the first real-data run.

## Question

> Does a mechanical reclaim of a broken swing low (Nasdaq "bear trap") predict
> better-than-normal forward returns versus drawdown-matched days — and do
> null models, second sweeps, survival curves, or a multi-index panel change that?

## Study 1 hypotheses

| ID | Claim | Test | Kill condition |
|---|---|---|---|
| H1 | Returns after reclaim exceed drawdown-matched days | Placebo vs days 5–20% below 120d high; 36-test grid | Placebo p ≥ 0.05 (or after FDR) |
| H0 | No edge | Same | Rejected only if H1 survives |

## Study 1 primary specification

- Support lookback **N = 120**; low age ≥ **10**; cooldown **20**; reclaim **K = 10**
- Retest window 60; horizons 20/60/120; placebo B = 5,000, seed 7
- Implemented in `src/events.py` (`PRIMARY`); regression-tested against Appendix B/C fixtures

## Tier 1 (see PREREG/)

20 primary tests across A–D; within-study Bonferroni and across-tier BH q = 0.05.
Parameters inherited from Study 1 are not re-tuned. B1 20-day window is a
documented deviation (`PREREG/B_second_sweep.md`).

## Fixtures / data

- `tests/fixtures/expected_ndx_events.csv`, `expected_spx_events.csv` — Study 1 event tables
- Clean series (not in git by default): `data/clean/ndx_1985_2026.csv`, `data/clean/spx_1950_2026.csv`
- Do not adjust fixtures to make a test pass; fix the engine instead
