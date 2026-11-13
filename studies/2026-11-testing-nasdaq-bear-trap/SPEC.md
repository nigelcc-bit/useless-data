# Study specification — testing-nasdaq-bear-trap

**Governing rules:** repository root [`RESEARCH_PROTOCOL.md`](../../RESEARCH_PROTOCOL.md)
and local [`AGENTS.md`](AGENTS.md) (study-specific only; protocol wins on conflict).

**Status:** interim. Tier 1 registered; real-data run pending clean CSVs.

## Frozen registration (Tier 1)

Pre-registration lives in [`PREREG/`](PREREG/) and was frozen when that tree
landed on `main`:

| File | Study |
|---|---|
| [`PREREG/A_null_models.md`](PREREG/A_null_models.md) | A — null models |
| [`PREREG/B_second_sweep.md`](PREREG/B_second_sweep.md) | B — second sweep |
| [`PREREG/C_survival.md`](PREREG/C_survival.md) | C — survival |
| [`PREREG/D_panel.md`](PREREG/D_panel.md) | D — panel |
| [`PREREG/README.md`](PREREG/README.md) | 20-test budget + BH across Tier 1 |

**Registration timestamp:** git commit `1ff80ed` (*Add Tier 1 runnable package into nasdaq bear-trap study*, 13 Nov 2026). Commit timestamps must show this freeze came before any real-data Tier 1 results.

Do not silently edit `PREREG/` after the first real-data run. Any post-freeze change needs a `DEVIATION:` line in the same commit (see `AGENTS.md`).

## Question

> Does a mechanical reclaim of a broken swing low (Nasdaq "bear trap") predict
> better-than-normal forward returns versus drawdown-matched days — and do
> null models, second sweeps, survival curves, or a multi-index panel change that?

## Study 1 hypotheses (historical; Claude-chat run)

| ID | Claim | Test | Kill condition |
|---|---|---|---|
| H1 | Returns after reclaim exceed drawdown-matched days | Placebo vs days 5–20% below 120d high; 36-test grid | Placebo p ≥ 0.05 (or after FDR) |
| H0 | No edge | Same | Rejected only if H1 survives |

## Study 1 primary specification

- Support lookback **N = 120**; low age ≥ **10**; cooldown **20**; reclaim **K = 10**
- Retest window 60; horizons 20/60/120; placebo B = 5,000, seed 7
- Implemented in `bear_trap/events.py` (`PRIMARY`); regression-tested against Appendix B/C fixtures

## Tier 1

20 primary tests across A–D; within-study Bonferroni and across-tier BH q = 0.05
(see `PREREG/README.md`). Parameters inherited from Study 1 are not re-tuned.
B1 20-day window is a documented deviation (`PREREG/B_second_sweep.md`).

Ledger after a run: `outputs/tests_run.csv` (raw_p, bh_p for all 20) and
`outputs/killed_hypotheses.md`, written by `analyses/s99_tier1_summary.py`.

## Fixtures / data

- `tests/fixtures/expected_ndx_events.csv`, `expected_spx_events.csv` — Study 1 event tables (never adjust to pass)
- Clean series (gitignored): `data/clean/ndx_1985_2026.csv`, `data/clean/spx_1950_2026.csv`
- Primary NDX/SPX loads **fail loudly** if clean files are missing (no silent Yahoo fallback)
- When clean files are deposited, register them in root `data/raw_manifest.csv` via `python scripts/build_raw_manifest.py` (sha256, source, date)
- Yahoo downloads use `core.ingest.yahoo`, cached under this study’s `data/raw/`
