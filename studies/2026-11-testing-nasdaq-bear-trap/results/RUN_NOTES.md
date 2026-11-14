# Tier 1 run notes (A, B, C on Study 1 clean data)

- Data: data/clean/ndx_1985_2026.csv (10,360 days) and spx_1950_2026.csv (19,336 days);
  9 Nov 2026 anchors 27,907.63 and 7,549.94 verified. NDX extended to 11 Nov 2026 with the
  Yahoo-derived mirror for the Study C live readout only. The mirror's 12 Nov bar looked
  partial and was excluded.
- Regression: all 43 NDX and 86 SPX Study 1 events reproduced (pytest 9 passed) after
  one engine fix (support-window ties use the OLDEST occurrence; see src/events.py).
- Study D not run here (needs Yahoo). The D rows from an earlier synthetic smoke test were
  removed; TIER1_SUMMARY.md therefore covers 18 of 20 tests.
- Seeds: 7 throughout. Study A: 500 paths per model. Study C: 200 null paths.
