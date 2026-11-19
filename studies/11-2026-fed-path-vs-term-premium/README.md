# Study 4: Fed path vs term premium

**Question.** How much of the 2026 rise in the 10-year Treasury yield comes from the expected path of short rates versus the term premium, through what channel, and is the current mix unusual compared with past hiking cycles?

**Status.** Pre-registered tests run. All four tested claims killed (H3, H4a, H4b, H5a); H1 "path driven"; H2 and H5b prior only. Results: [`RESULTS.md`](RESULTS.md). Research note not written.

- Pre-registration: [`PREREG.md`](PREREG.md) (frozen; deviations go in its dated section)
- Study rules: [`CLAUDE.md`](CLAUDE.md); programme rules: [`RESEARCH_PROTOCOL.md`](../../RESEARCH_PROTOCOL.md)
- Data and checksums: [`data/MANIFEST.md`](data/MANIFEST.md); fixtures: [`config/fixtures.yaml`](config/fixtures.yaml)

## Run

```bash
cd studies/11-2026-fed-path-vs-term-premium
python3 -m src.h1_attribution && python3 -m src.h2_hike_windows && python3 -m src.h3_decoupling \
  && python3 -m src.h4_oil && python3 -m src.h5_fomc && python3 -m src.fdr && python3 -m src.exhibits
```

Re-running appends to `out/runs.csv` and marks earlier `out/tests_run.csv` rows as superseded.

## Run the data gates

```bash
cd studies/11-2026-fed-path-vs-term-premium
python3 -m pytest -q
```

Requires Python with pandas and PyYAML (plus numpy, scipy, statsmodels for the later analysis).

Nothing here is a trading recommendation.
