# Instructions for coding agents (this study only)

Programme rules are in repository root [`RESEARCH_PROTOCOL.md`](../../RESEARCH_PROTOCOL.md).
If anything here conflicts with that file, **the protocol wins**.

Study-specific constraints:

1. **Do not change** `bear_trap/events.py` `Spec` defaults, `PREREG/`, or the
   primary test definitions in `analyses/s01`–`s04` / `s99` without being asked.
   Any such change must add a `DEVIATION:` line to the relevant `PREREG/*.md`
   explaining what changed and why, in the same commit. Tier 1 registration
   timestamp is commit `1ff80ed`.
2. Root `pytest` (including `studies/2026-11-testing-nasdaq-bear-trap/tests`)
   must pass before and after any change to `bear_trap/`. The Appendix B/C
   regression fixtures are the anchor — fix the engine, leave the fixtures alone.
3. New analyses go under `analyses/` with a new `PREREG/` file written first;
   count their tests in `PREREG/README.md`.
4. Do not recall prices or statistics from memory. Fetch the data, then check
   known anchors (for example NDX close 27,907.63 on 2026-11-09).
