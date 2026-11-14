# Tier 1 data provenance (this run)

**Run date:** 2026-11-14 (UTC)  
**Branch:** `cursor/tier1-yahoo-run-1cdd`  
**Command:** `./run_all.sh` (default `PATHS=500`)

## SUPERSEDED (Studies A, B, C)

On 2026-11-14 the owner recorded that **A, B and C in this folder are
SUPERSEDED** by the clean-data run on `claude/lucid-turing-nuuzwt`
(commits `01a5f00` engine tie-rule fix + `4bc34ee` A–C results). That run:

- used `data/clean/ndx_1985_2026.csv` / `spx_1950_2026.csv`;
- reproduced all 43 NDX + 86 SPX Appendix B/C events;
- changed support-window ties to the **oldest** occurrence of the minimum.

Do not quote A–C numbers from this PR. Keep the artifacts here only as an
audit trail of the Yahoo / pre-fix provisional run.

**Study D is not superseded.** It was not re-run on clean data; the D rows
and plots in this folder remain the only (still provisional, Yahoo-panel)
Study D numbers.

## Source used (this Yahoo run)

Validated Study 1 clean files were **not** available in this Cloud Agent
workspace (`data/clean/*.csv` are gitignored). An env-setup request to
upload them was **skipped by the owner** on 2026-11-14. Loaders used Yahoo
Finance via `yfinance` (`^NDX`, `^GSPC`, and the Study D panel tickers),
cached under `data/raw/`.

```
DEVIATION: first Tier 1 real-data run used Yahoo fallback, not the Study 1
Investing.com / gt / mirror splices. Appendix B/C regression was SKIPPED.
Yahoo SPX (1950–2026-11-09) yielded 84 events vs Appendix C’s 86 under the
pre-fix most-recent age-tie rule. A–C superseded as above; D remains
provisional Yahoo-panel output.
```

## What this run did

- `pytest -q`: 30 passed, 2 skipped (Appendix B/C clean-file regressions).
- Yahoo panel download + validate for primary + secondary universes.
- Studies A–D and `s99_tier1_summary.py` completed without error.
