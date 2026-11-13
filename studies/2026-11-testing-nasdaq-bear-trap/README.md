# Testing the Nasdaq "bear trap"

Separate study from [`2026-11-flush-or-regime`](../2026-11-flush-or-regime/). Asks whether a failed breakdown of a swing low (a "bear trap" / reclaim) carries forward-return information, and extends that with Tier 1 null / second-sweep / survival / panel tests.

**Status:** interim — Study 1 write-up filed; **Tier 1 runnable code filed; not yet run on full 1950/1985–2026 clean data**. Nothing here is a trading recommendation.

Slug: `testing-nasdaq-bear-trap`

Governing rules: repository root [`RESEARCH_PROTOCOL.md`](../../RESEARCH_PROTOCOL.md). Agent rules for this package: [`AGENTS.md`](AGENTS.md).

---

## Question

> Across all breaks of an established swing low, how often does a quick reclaim occur, and does it predict better-than-normal returns versus comparable drawdown days?

## Study 1 (interim)

Full write-up: [`docs/Study1_Bear_Trap_Full_Report.md`](docs/Study1_Bear_Trap_Full_Report.md).

Headline (run 10 Nov 2026; write-up 13 Nov 2026): reclaiming a broken 6-month low is common (~86% Nasdaq / ~78% S&P within 10 days), most reclaims retest, and forward returns after reclaim match drawdown-matched benchmarks (no edge; smallest placebo p = 0.09 across 36 tests).

## Tier 1 extensions (code filed; full-data run pending)

| Study | Question | Script |
|---|---|---|
| **A** Null models | Do reclaim/retest rates differ from random-price nulls? | `studies/s01_null_models.py` |
| **B** Second sweep | Does the chart's second sweep beat comparable dips? | `studies/s02_second_sweep.py` |
| **C** Survival | How does retest risk decay after a reclaim (live readout)? | `studies/s03_survival.py` |
| **D** Panel | Do results hold across 12 indices with month-clustered inference? | `studies/s04_panel.py` |

Pre-registration (20 primary tests): [`PREREG/`](PREREG/). **Commit `PREREG/` before the first real-data run** (already in this tree; treat first full-data run as gated on clean files + green pytest).

### What’s verified so far

- Engine reproduces Appendix B events **#33–43** exactly on the free Nasdaq mirror (2019–2026).
- Full Appendix B/C regression (43 NDX + 86 SPX) runs once clean files are present.
- All four study scripts smoke-tested on the 2019–2026 NDX slice / synthetic panel; those outputs are not results.
- Yahoo download path not verified in the build environment — check `python -m src.data` coverage before trusting the panel.

### Setup and run

```bash
cd studies/2026-11-testing-nasdaq-bear-trap
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Required for full Study 1 regression + Tier 1 on real data:
#   data/clean/ndx_1985_2026.csv
#   data/clean/spx_1950_2026.csv

python -m pytest -q
./run_all.sh                 # PATHS=100 ./run_all.sh for a quick pass
```

Without the clean files, loaders fall back to Yahoo `^NDX` / `^GSPC` (not the validated Study 1 splices); the full regression test skips.

Outputs: `results/<study>/` and `results/TIER1_SUMMARY.md` (BH across 20 primary p-values).

### Known design note

B1’s 20-day window was chosen knowing the Apr 2025 episode — recorded as a pre-registration deviation; 10-day and 40-day sensitivity runs are the clean ones (`PREREG/B_second_sweep.md`).

Live event note (as delivered with Tier 1): as of the 11 Nov close, 26,630 had not been retested (closes 27,741 and 28,374). A partial-looking 12 Nov mirror bar was left out.

## Layout

```
docs/Study1_Bear_Trap_Full_Report.md
PREREG/                 Tier 1 pre-registration (20 primary tests)
src/                    event engine, nulls, inference, data loaders
studies/s01…s04*.py     Tier 1 study scripts + s99 summary
tests/                  engine unit + Appendix B/C fixtures
data/clean/             put ndx_1985_2026.csv + spx_1950_2026.csv here
results/                Tier 1 outputs (after run_all)
AGENTS.md / run_all.sh / requirements.txt / pytest.ini
```

## Companion work

- Project sibling: flush vs regime change (`studies/2026-11-flush-or-regime`)
- Planned: Study 2 (macro/valuation scorecard), midterm-election side study
