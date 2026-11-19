# Study 4: Fed path vs term premium

**Question.** How much of the 2026 rise in the 10-year Treasury yield comes from the expected path of short rates versus the term premium, through what channel, and is the current mix unusual compared with past hiking cycles?

**Status.** Complete (P1 live check pending 9 Dec 2026).

**Answer.** Under the primary model (ACM), the 2026 rise in the 10-year zero yield (+87bp, 31 Dec 2025 to 13 Nov 2026) is almost entirely the expected policy path (+89bp) rather than the term premium (-2bp). Kim-Wright splits it +48bp path / +42bp term premium. Both term-premium shares are below one half, so the pre-registered verdict is "path driven". In the model-free cross-check the par 10-year rose +97bp, all of it real yield (+98bp; breakeven -1bp). The 10-year has not decoupled from the 2-year (2026 R² 0.67, ranked 21st of 36 years; slope 0.73), and the term premium sits at the 44th (ACM) and 62nd (KW) percentile of its 1990-2026 history. None of the four tested hypotheses survives BH at q = 0.10. The two Kim-Wright-only positives carry little weight, because Kim-Wright's daily term premium is about half the yield change (R² 0.96-0.99; exploratory X1).

- Results: [`RESULTS.md`](RESULTS.md)
- Research note: [`NOTE.md`](NOTE.md) (also `NOTE.docx`)
- Pre-registration: [`PREREG.md`](PREREG.md) (frozen; deviations go in its dated section)
- Study rules: [`CLAUDE.md`](CLAUDE.md); programme rules: [`RESEARCH_PROTOCOL.md`](../../RESEARCH_PROTOCOL.md)
- Data and checksums: [`data/MANIFEST.md`](data/MANIFEST.md); fixtures: [`config/fixtures.yaml`](config/fixtures.yaml)

## Run

```bash
cd studies/11-2026-fed-path-vs-term-premium
python3 -m src.h1_attribution && python3 -m src.h2_hike_windows && python3 -m src.h3_decoupling \
  && python3 -m src.h4_oil && python3 -m src.h5_fomc && python3 -m src.fdr && python3 -m src.exhibits \
  && python3 -m src.x_exploratory   # exploratory X1-X2, not in the BH family
```

Re-running appends to `out/runs.csv` and marks earlier `out/tests_run.csv` rows as superseded.

## Run the data gates

```bash
cd studies/11-2026-fed-path-vs-term-premium
python3 -m pytest -q
```

Requires Python with pandas and PyYAML (plus numpy, scipy, statsmodels for the later analysis).

Nothing here is a trading recommendation.
