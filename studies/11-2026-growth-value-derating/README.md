# 11-2026-growth-value-derating

**Study 5: Is the Growth discount real?** It splits the 2026 S&P 500 Growth forward P/E de-rating into price, earnings, composition and rates. Nothing here is a trading recommendation.

Slug: `growth-value-derating`

**Status:** complete (pre-registered 28 Nov 2026 in `d9238e3`; run 28 Nov 2026). Scheduled re-read in the first week of January 2027, after the 21 Dec 2026 style reconstitution.

## Answer

- **The de-rating came from earnings, not prices.** The Growth forward P/E fell from 29.32x (31 Oct 2025) to 17.10x (27 Nov 2026). Rising forward earnings explain **95.5%** of that drop, and the Growth index price barely moved.
- **The reconstitution didn't cause it.** The Dec 2025 reconstitution explains only **5.7%**, and no robustness variant changes that classification.
- **Growth crossed below Value** mainly because its earnings estimates rose faster: 66% of the gap, with 23% from Value's stronger prices.
- **The earnings aren't fully backed by cash.** Among the top 15 Growth names, free cash flow after stock-based pay fell from **61.0% to 39.9%** of net income in a year, and capex ran at **2.98x** depreciation. The pre-registered rule therefore supports **B (inflated estimates)** over A (a cash-backed catch-up), at 60% confidence.
- **The main rival is an AI investment phase:** the earnings are real but heavily reinvested. The rule cannot exclude it.
- **The rates branch (C vs D) was not run,** because Phase 1 did not select it.

Full write-up: [`RESULTS.md`](RESULTS.md). Pre-registration: [`PREREG.md`](PREREG.md).

## Layout

| Path | Purpose |
|---|---|
| `PREREG.md`, `SPEC.md` | Frozen pre-registration and summary |
| `config/fixtures.yaml` | Data hashes and documented values; the pipeline stops if they do not reproduce |
| `data/raw/` | 28 Nov 2026 data pack (README in `README_datapack.md`) |
| `src/phase1_split.py` | Phase 1 legs, robustness variants, headline chart |
| `src/phase2a_quality.py` | Phase 2A, earnings quality (ran) |
| `src/phase2b_rates.py` | Phase 2B, rates (not run: not selected), and the credit side-check |
| `run_all.py` | End to end, seed 7; runs only the branch Phase 1 selects |
| `outputs/` | `phase1_legs.csv/.png`, `phase2a_*.csv`, `trials.csv`, `tests_run.csv`, `killed_hypotheses.md` |
| `tests/test_study.py` | Fixtures, identity, look-ahead truncation, frozen classification rule |

## Reproduce

```
cd studies/11-2026-growth-value-derating
python run_all.py
pytest
```

## Final step

Add or update this study's section in FINDINGS.md (repo root), then run
`python scripts/check_findings.py`. Re-runs replace the section; they never
add a second one.
