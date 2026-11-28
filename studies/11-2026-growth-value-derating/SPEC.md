# Study specification

**Governing rules:** repository root `RESEARCH_PROTOCOL.md`. The full pre-registration is in [`PREREG.md`](PREREG.md), dated 28 Nov 2026 and committed before computation. This file summarises it.

## Question

> Was the 2026 fall in the S&P 500 Growth forward P/E, to below Value, driven by price, earnings, index composition or real yields?

## Hypotheses

| ID | Claim | Test | Kill condition |
|---|---|---|---|
| P1 | The Growth P/E drop is earnings-driven (EPS leg > 60%) or price-driven (PRICE leg > 50%) | Phase 1 log identity, peak to 2026-11-27 | Neither threshold met: "mixed" |
| E | The Dec 2025 reconstitution is a material artefact (COMPOSITION leg > 30%) | Phase 1 composition leg | COMPOSITION <= 30% |
| A | Earnings catch-up with cash support | Phase 2A (if selected): FCF-minus-SBC / NI change >= -10pp and breadth net positive | Not met |
| B | Inflated estimates | Phase 2A (if selected): FCF-minus-SBC / NI down > 15pp and capex / depreciation > 2.0 | Not met |
| D | Discount-rate shock | Phase 2B (if selected): real-yield coefficient < 0, \|t\| > 2, BH p < 0.10, explains >= 50% of the relative move | Not met: C by elimination (WEAK) |

## Fixtures

`config/fixtures.yaml`: file hashes and row counts of the raw pack, plus values documented in the pack README. The pipeline stops if they do not reproduce.

## Decision rules

Frozen in `PREREG.md`.
