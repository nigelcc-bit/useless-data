# Study specification — testing-nasdaq-bear-trap

**Governing rules:** see repository root `RESEARCH_PROTOCOL.md`.

**Status:** interim. This SPEC captures the Study 1 design already run in Claude chat.
It will be re-frozen before the extended study computes. Do not treat the interim
report as a final pre-registration for programme purposes until that freeze.

## Question

> Does a mechanical reclaim of a broken swing low (Nasdaq "bear trap") predict
> better-than-normal forward returns versus drawdown-matched days?

## Hypotheses

| ID | Claim | Test | Kill condition |
|---|---|---|---|
| H1 | Returns after reclaim of a broken swing low exceed returns on comparable drawdown days | Placebo: mean forward return after reclaim vs 5,000 draws from days 5–20% below 120d high; horizons 20/60/120d; N∈{60,120,250}, K∈{5,10}; Nasdaq and S&P | Placebo p ≥ 0.05 on primary and robustness grid (or after FDR) |
| H0 | No edge — reclaim returns match drawdown-matched days | Same as H1 | Rejected only if H1 survives |

Secondary (descriptive, not edge tests): reclaim rate; retest rate within 60d; analog band (10–20% off 120d high at break).

## Primary specification (Study 1)

- Support lookback **N = 120** trading days; low must be ≥ **10** days old
- Break: first close below support; **20**-day cooldown
- Reclaim window **K = 10** trading days
- Forward returns from reclaim close (or K-day mark if no reclaim)
- Benchmark: all days closed 5–20% below 120-day high
- Placebo seed **7**, **5,000** draws with replacement

## Fixtures

Hard-code verified closes and event counts in `config/fixtures.yaml` when porting
code into this repo. Do not adjust fixtures to make a test pass.

## Decision rules

Freeze thresholds and windows in this file and `RESULTS.md` **before** the
extended-study code runs. Study 1 numbers in `docs/` are historical findings from
the Claude workspace, not yet reproduced under this repository's ledger.
