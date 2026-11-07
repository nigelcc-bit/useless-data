# AI selloff study — flush or regime change?

Pre-registered tests for the AI-capex cross-section after 5 Nov 2026.
Governing rule: **false-discovery controller, not pattern generator.**

> After a violent decline in the AI supply chain, does the cross-section mean-revert into the same names (positioning flush), or does leadership rotate away from them (thesis change)?

Upstream note: *The Blue Tsunami Flush* (6 Nov 2026). This repo converts its claims into falsifiable tests (see uploaded research spec).

## Quick start

```bash
python3 -m pip install -e ".[dev]"
PYTHONPATH=. python -m src.studies.reproduce_nov5
PYTHONPATH=. pytest
PYTHONPATH=. python -m src.monitor.leadership
```

## Status

| Phase | Work | Gate |
|---|---|---|
| **P0** | Repo, fixtures, quality gates | §6.3 assertions — **in progress / local green** |
| P1 | Ingest + `prices.parquet` 2015–2026 | Needs market-data egress (Yahoo/Stooq blocked here) |
| P2 | H1 sector base rate | Power check N before returns |
| P3 | Feature blocks; `panel.parquet` | Look-ahead audit |
| P4 | H3 then H4 | VIFs; no pooling before H4 |
| P5 | H2 spread factor | Variance ratio |
| P6 | H5 + costs | Pre-open / 5pm HKT constraint |
| P7 | FDR family; fill RESULTS.md + kill log | Last — do not reorder |

## Layout

See research spec §8. Configs in `config/` are frozen. Notebooks are exploration only — nothing in a notebook is a result.

## House style

Exhibits: cream `#FBF6EC`, orange `#E8762C`, dark `#2B2B2B`. Judgment-coded fields (layer, AI exposure, episode dating) must be visually distinct and captioned.
