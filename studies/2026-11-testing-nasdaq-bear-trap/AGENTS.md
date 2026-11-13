# Instructions for coding agents (Cursor, Claude Code, etc.)

This is a pre-registered empirical study. Follow these rules when editing.

1. **Do not change parameters in `src/events.py` `Spec` defaults, `PREREG/`, or
   the primary test definitions in `studies/` without being asked.** Any such
   change must add a `DEVIATION:` line to the relevant `PREREG/*.md` explaining
   what changed and why, in the same commit.
2. `python -m pytest -q` must pass before and after any change to `src/`. The
   Appendix B/C regression test is the anchor. If it fails, fix the engine and
   leave the fixtures alone.
3. No look-ahead: every outcome uses data strictly after the entry close, and
   is NaN unless its full window exists.
4. New analyses go in new scripts under `studies/` with their own `PREREG/`
   file written first. Count their tests in `PREREG/README.md`.
5. Report every test that is run, including null results. Never delete a result
   because it looks bad.
6. Do not recall prices or statistics from memory. Fetch the data, then check
   it against known anchors (for example NDX close 27,907.63 on 2026-11-09).
