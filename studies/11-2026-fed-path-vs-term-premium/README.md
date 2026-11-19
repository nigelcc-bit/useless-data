# Study 4: Fed path vs term premium

**Question.** How much of the 2026 rise in the 10-year Treasury yield comes from the expected path of short rates versus the term premium, through what channel, and is the current mix unusual compared with past hiking cycles?

**Status.** Pre-registered, data validated, analysis not started.

- Pre-registration: [`PREREG.md`](PREREG.md) (frozen; deviations go in its dated section)
- Study rules: [`CLAUDE.md`](CLAUDE.md); programme rules: [`RESEARCH_PROTOCOL.md`](../../RESEARCH_PROTOCOL.md)
- Data and checksums: [`data/MANIFEST.md`](data/MANIFEST.md); fixtures: [`config/fixtures.yaml`](config/fixtures.yaml)

## Run the data gates

```bash
cd studies/11-2026-fed-path-vs-term-premium
python3 -m pytest -q
```

Requires Python with pandas and PyYAML (plus numpy, scipy, statsmodels for the later analysis).

Nothing here is a trading recommendation.
