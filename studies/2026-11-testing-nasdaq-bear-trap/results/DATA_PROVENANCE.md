# Tier 1 data provenance (this run)

**Run date:** 2026-11-14 (UTC)  
**Branch:** `cursor/tier1-yahoo-run-1cdd`  
**Command:** `./run_all.sh` (default `PATHS=500`)

## Source used

Validated Study 1 clean files were **not** available in this Cloud Agent
workspace (`data/clean/ndx_1985_2026.csv`, `data/clean/spx_1950_2026.csv` are
gitignored). An env-setup request to upload them was **skipped by the owner**
on 2026-11-14; Yahoo remains the working path for this environment. Loaders
used Yahoo Finance via `yfinance` (`^NDX`, `^GSPC`, and the Study D panel
tickers), cached under `data/raw/`.

```
DEVIATION: first Tier 1 real-data run used Yahoo fallback, not the Study 1
Investing.com / gt / mirror splices. Appendix B/C regression remains SKIPPED
(clean files absent). Yahoo NDX reproduces event dates #1–43 and the recent
#33–43 cache test; Yahoo SPX in the 1950–2026-11-09 window yields 84 events
vs Appendix C’s 86 (missing 1962-04-16 and 1962-06-14 under the engine’s
most-recent age-tie rule on gt/Yahoo prints). Treat all Tier 1 numbers in
this folder as provisional until re-run on the validated clean CSVs.
```

## What did pass

- `pytest -q`: 30 passed, 2 skipped (Appendix B/C clean-file regressions).
- Yahoo panel download + validate for primary + secondary universes.
- Studies A–D and `s99_tier1_summary.py` completed without error.

## Re-run gate

Copy Nigel’s validated files into `data/clean/`, confirm
`pytest -q` shows **0 skipped** on `test_reproduces_study1`, then re-run
`./run_all.sh` and replace these results.
