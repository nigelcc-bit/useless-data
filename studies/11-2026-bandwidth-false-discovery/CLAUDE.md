# Rules for this study

- Never load 2026 data in analysis code until PREREG.md has a signed-off "Holdout unlocked" line.
- No look-ahead: signals use only data available at the close of day t (or the open, for the gap).
- Fixed seeds. Every experiment appends a row to out/runs.csv (timestamp, script, params, bandwidth, result, git hash).
- Report killed results alongside survivors.
- Do not change PREREG.md after results exist. Any deviation goes in a dated "Deviations" section.
- Python, pandas, numpy, scipy, statsmodels. Prefer Parquet for data.

Programme-wide rules: repository root `RESEARCH_PROTOCOL.md`.
