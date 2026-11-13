# Testing the Nasdaq "bear trap"

Separate study from [`2026-11-flush-or-regime`](../2026-11-flush-or-regime/). Asks whether a failed breakdown of a swing low (a "bear trap" / reclaim) carries forward-return information on the Nasdaq 100 and S&P 500.

**Status:** interim — Claude-chat Study 1 write-up filed; **not final**. An extended study will follow in this folder. Nothing here is a trading recommendation.

Slug: `testing-nasdaq-bear-trap`

Governing rules: repository root [`RESEARCH_PROTOCOL.md`](../../RESEARCH_PROTOCOL.md).

---

## Question

> Across all breaks of an established swing low, how often does a quick reclaim occur, and does it predict better-than-normal returns versus comparable drawdown days?

## Interim finding (Study 1)

Full write-up: [`docs/Study1_Bear_Trap_Full_Report.md`](docs/Study1_Bear_Trap_Full_Report.md).

Headline from the interim analysis (run 10 Nov 2026; write-up 13 Nov 2026): reclaiming a broken 6-month low is common (~86% Nasdaq / ~78% S&P within 10 days), most reclaims retest, and forward returns after reclaim match drawdown-matched benchmarks (no edge; smallest placebo p = 0.09 across 36 tests).

## Layout

```
README.md / SPEC.md / RESULTS.md
docs/Study1_Bear_Trap_Full_Report.md   interim Claude-chat finding
config/pins.yaml
src/                                   code TBD (trap_study.py etc. in extended pass)
tests/
outputs/
```

## Companion work

- Project sibling: flush vs regime change (`studies/2026-11-flush-or-regime`)
- Planned companions named in Study 1: Study 2 (macro/valuation scorecard), midterm-election side study
- Extended study: to be developed here; do not treat Study 1 as the locked programme result
