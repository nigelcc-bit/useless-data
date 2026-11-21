# Study 3: The Exhaustion Model (2026-11)

After a fast equity drawdown, what separates episodes where selling exhausts from ones that escalate?

- Pre-registration: [`PREREGISTRATION.md`](PREREGISTRATION.md) (first commit `6b531d8`; deviations D1-D3 in Part D)
- Report: [`report/REPORT.md`](report/REPORT.md)
- Training verdicts (written before the hold-out): [`results/verdicts_train.md`](results/verdicts_train.md)
- Kill log: [`results/killed_hypotheses.md`](results/killed_hypotheses.md)
- Test ledger with BH-adjusted p: [`ledger.csv`](ledger.csv)
- Post-hoc diagnostics (power/MDE, hold-out N, H5, data checks; deviations D4-D9): `src/posthoc.py`, `results/posthoc/`, REPORT section "Post-hoc diagnostics"

**Result:** 0 of 69 ledger tests survive BH at q = 0.10. No layer beats the price/episode-state
baseline, and the baseline does not beat a constant base rate in the 2018-2026 hold-out.

## Rerun

```bash
pip install pandas numpy scipy statsmodels matplotlib pyarrow requests tabulate pytest
cd studies/2026-11-exhaustion-model
python src/fetch.py              # re-pulls raw data (appends to data/raw/MANIFEST.csv; overwrites raw files)
python src/ingest.py             # data/raw -> data/processed
python -m pytest -q tests        # data gates + engine tests; must pass
python src/evaluate.py           # training: ledger.csv, results/layer_tests_train.csv, exhibits (~6 min, 4 cores)
python src/verdicts.py           # results/verdicts_train.md, killed_hypotheses.md
python src/evaluate.py --holdout # hold-out scorecard (already run once; rerunning is reproduction only)
python src/live.py               # live state and frozen predictions; rerun after 2027-02-24 to score
python src/step0.py              # Step 0 rebound-leadership check
python src/figures.py
python src/posthoc.py            # post-hoc diagnostics (D4-D9)
```

Re-pulling data changes the vintage; to reproduce the committed results, use the committed `data/raw/`.

## Data provenance

The input files named in the prompt were not supplied; every input was rebuilt from public sources
on 21 Nov 2026 (see `data/raw/MANIFEST.csv` for URL, time, rows and sha256):

| File | Source |
|---|---|
| `spx_1950_2026.csv`, `ndx_1985_2026.csv`, `sox_daily_1994_2026.csv`, `vix_daily_1990_2026.csv`, `vix3m_daily_2007_2026.csv` | Yahoo Finance chart API (`^GSPC`, `^NDX`, `^SOX`, `^VIX`, `^VIX3M`), through 20 Nov 2026 |
| `fred_*.csv` | FRED: FEDFUNDS, BAA, GS10, BAA10Y, VIXCLS, VXVCLS, NASDAQ100, SP500, XTEXVA01KRM667S (Korea exports, USD, SA; OECD MEI) |
| `step0_leadership_closes.csv` | Yahoo, 20 names of the Blue Tsunami list, 4-20 Nov 2026 |

Korean exports by product (semis vs total) were not obtainable here; H4 was not run (data-gap register in the report).

## Layout

```
PREREGISTRATION.md  ledger.csv  README.md
data/raw/ data/processed/
src/  fetch ingest episodes features models evaluate verdicts live step0 figures
tests/  test_data.py (prompt validation gates)  test_engine.py (engine, look-ahead, BH, m+2 lag)
results/  episodes_*.csv events_*.csv escalation_ladder.csv layer0_*.{csv,md} layer_tests_train.csv
          h4_incremental.csv holdout_*.csv live_*.csv step0_*.csv runs.csv fig_*.png
report/REPORT.md
```
