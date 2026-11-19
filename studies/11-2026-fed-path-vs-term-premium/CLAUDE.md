# Rules for this study

- PREREG.md was frozen before any 2026 decomposition was computed. Do not change it; deviations go in its dated "Deviations" section with the original text kept.
- `data/raw/` holds the files exactly as pulled. Never edit them. Any cleaning happens in `src/` and writes to `data/processed/`.
- Fixtures in `config/fixtures.yaml` are never adjusted. If `tests/test_data.py` fails, the pipeline stops.
- Every analysis run appends a row to `out/runs.csv` (timestamp, script, params, result, git hash). Every hypothesis test appends to `out/tests_run.csv`, including failed and abandoned ones.
- Report killed hypotheses (`out/killed_hypotheses.md`) with the same prominence as survivors.
- ACM is the primary model, Kim-Wright the secondary. A result that holds under only one model is reported as model-dependent.
- Python, pandas, numpy, scipy, statsmodels. Parquet for processed data.

Programme-wide rules: repository root `RESEARCH_PROTOCOL.md`.
