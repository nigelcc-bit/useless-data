# Testing the Nasdaq "bear trap"

Separate study from [`2026-11-flush-or-regime`](../2026-11-flush-or-regime/). Asks whether a failed breakdown of a swing low (a "bear trap" / reclaim) carries forward-return information, and extends that with Tier 1 null / second-sweep / survival / panel tests.

**Status:** interim — Study 1 write-up filed; **Tier 1 registered** (commit `1ff80ed`); **real-data run pending** clean CSVs. Nothing here is a trading recommendation.

Slug: `testing-nasdaq-bear-trap`

Governing rules: [`RESEARCH_PROTOCOL.md`](../../RESEARCH_PROTOCOL.md). Study notes for agents: [`AGENTS.md`](AGENTS.md).

---

## Question

> Across all breaks of an established swing low, how often does a quick reclaim occur, and does it predict better-than-normal returns versus comparable drawdown days?

## Study 1 (interim)

Full write-up: [`docs/Study1_Bear_Trap_Full_Report.md`](docs/Study1_Bear_Trap_Full_Report.md).

Headline (run 10 Nov 2026; write-up 13 Nov 2026): reclaiming a broken 6-month low is common (~86% Nasdaq / ~78% S&P within 10 days), most reclaims retest, and forward returns after reclaim match drawdown-matched benchmarks (no edge; smallest placebo p = 0.09 across 36 tests).

## Tier 1 extensions (registered; full-data run pending)

| Study | Question | Script |
|---|---|---|
| **A** Null models | Do reclaim/retest rates differ from random-price nulls? | `analyses/s01_null_models.py` |
| **B** Second sweep | Does the chart's second sweep beat comparable dips? | `analyses/s02_second_sweep.py` |
| **C** Survival | How does retest risk decay after a reclaim (live readout)? | `analyses/s03_survival.py` |
| **D** Panel | Do results hold across 12 indices with month-clustered inference? | `analyses/s04_panel.py` |

Frozen registration: [`PREREG/`](PREREG/) (timestamp commit `1ff80ed`). See [`SPEC.md`](SPEC.md).

### What’s verified so far

- Engine reproduces Appendix B events **#33–43** exactly on the free Nasdaq mirror (2019–2026).
- Full Appendix B/C regression (43 NDX + 86 SPX) runs once clean files are present.
- All four analysis scripts smoke-tested on the 2019–2026 NDX slice / synthetic panel; those outputs are not results.
- Yahoo path uses `core.ingest.yahoo`. Check coverage from `python -m bear_trap.data` before trusting the panel.

### Setup and run

From the **repo root**:

```bash
pip install -e ".[dev,bear-trap]"

# Required for primary NDX/SPX loads + full regression:
#   studies/2026-11-testing-nasdaq-bear-trap/data/clean/ndx_1985_2026.csv
#   studies/2026-11-testing-nasdaq-bear-trap/data/clean/spx_1950_2026.csv
# Then: python scripts/build_raw_manifest.py

pytest    # collects this study’s tests via root pyproject
cd studies/2026-11-testing-nasdaq-bear-trap && ./run_all.sh
# quick pass: PATHS=100 ./run_all.sh
```

Missing clean files → primary `load_index` **raises** (no silent Yahoo fallback).

Outputs under `outputs/` (`A_null_models/`, …, `TIER1_SUMMARY.md`); ledger
`outputs/tests_run.csv` and kill log `outputs/killed_hypotheses.md` via `analyses/s99_tier1_summary.py`.

### Known design note

B1’s 20-day window was chosen knowing the Apr 2025 episode — recorded as a pre-registration deviation; 10-day and 40-day sensitivity runs are the clean ones (`PREREG/B_second_sweep.md`).

## Layout

```
docs/Study1_Bear_Trap_Full_Report.md
PREREG/                 Tier 1 pre-registration (20 primary tests)
bear_trap/              event engine, nulls, inference, data loaders
analyses/s01…s04*.py    Tier 1 scripts + s99 summary
tests/                  engine unit + Appendix B/C fixtures
data/clean/             ndx_1985_2026.csv + spx_1950_2026.csv (gitignored)
outputs/                Tier 1 outputs + programme ledger
AGENTS.md / run_all.sh
```

## Companion work

- Project sibling: flush vs regime change (`studies/2026-11-flush-or-regime`)
- Planned: Study 2 (macro/valuation scorecard), midterm-election side study
