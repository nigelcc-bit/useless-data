# Quick lookups

Fast, single-question research: a beta check, a regime read, a quick
backtest sanity test. Lighter than a full study under `studies/`, but kept
so the work can be found and reused later.

Nothing here is a trading recommendation.

## Convention

One folder per lookup: `quick-lookups/YYYY-MM-DD-<slug>/`

| File | Purpose |
|---|---|
| `PREREG.md` | Question, method, thresholds and verdict rule, committed **before** results |
| `run.py` | Self-contained script; reruns end to end |
| `data/` | Small processed inputs (CSV). Raw API payloads go in `data/raw/` and are not committed |
| `outputs/` | Charts, tables, trial ledger |
| `RESULT.md` | Verdict card (Tier 1) plus short notes |

Light version of `RESEARCH_PROTOCOL.md`: pre-register, count every variant
tried, report killed results as prominently as survivors, filtered (not
smoothed) signals for anything decision-related. If a lookup grows into a
real question, promote it to `studies/` with `scripts/new_study.py`.

## Index

| Date | Lookup | Question | Verdict |
|---|---|---|---|
| 2026-11-25 | [mu-regime-read](2026-11-25-mu-regime-read/) | Is MU's 2026 selloff a regime change or a flush? (HMM, since 2010) | **WEAK**: vol regime since Aug 2025; selloff leg flush-sized so far |
