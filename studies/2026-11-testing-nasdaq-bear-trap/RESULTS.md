# Results — testing-nasdaq-bear-trap

**Status:** interim (not final). Tier 1 code filed; **no full-data Tier 1 result yet**.

Date every revision; keep the original text.

## Study 1 (Claude chat) — filed, not programme-final

| Field | Value |
|---|---|
| Write-up | [`docs/Study1_Bear_Trap_Full_Report.md`](docs/Study1_Bear_Trap_Full_Report.md) |
| Run date | 10 Nov 2026 (write-up compiled 13 Nov 2026) |
| Primary result | H0 not rejected — reclaim returns ≈ drawdown-matched; min placebo p = 0.09 over 36 tests |
| Reclaim rates | Nasdaq 86% (37/43); S&P 78% (67/86) within 10 days (N=120) |
| Retest rates | Nasdaq 72%; S&P 79% within 60 days |
| Repo ledger | engine fixtures in `tests/fixtures/`; full 43+86 regression pending clean CSVs |

## Tier 1 — pre-registered, not yet run on full data

| Study | Pre-reg | Decision | Date |
|---|---|---|---|
| A Null models | [`PREREG/A_null_models.md`](PREREG/A_null_models.md) | *pending clean data + run* | — |
| B Second sweep | [`PREREG/B_second_sweep.md`](PREREG/B_second_sweep.md) | *pending* | — |
| C Survival | [`PREREG/C_survival.md`](PREREG/C_survival.md) | *pending* | — |
| D Panel | [`PREREG/D_panel.md`](PREREG/D_panel.md) | *pending* | — |
| Tier BH (20 tests) | [`PREREG/README.md`](PREREG/README.md) | *pending* → `results/TIER1_SUMMARY.md` | — |

Verified before full run: Appendix B #33–43 exact match on 2019–2026 NDX mirror; four scripts smoke-tested on that slice / synthetic panel only.
