# Research protocol

Governing rules for every study in this programme. Copied from the
pre-registration discipline in the flush-or-regime research spec; they are
not optional and apply study-by-study.

1. **Pre-registration.** Hypotheses, thresholds, windows and decision rules
   are written into the study’s `RESULTS.md` (and/or `SPEC.md`) **before**
   the code that tests them runs. Every revision is dated and keeps the
   original text. Commit timestamps must show each freeze came before its
   results.

2. **Fixtures are never adjusted.** Numbers verified against an external
   source are hard-coded in the study’s `config/fixtures.yaml`. If the
   pipeline cannot reproduce them, the pipeline stops. Targets are never
   adjusted to make a test pass; a confirmed error in a prior note is
   recorded as `SUPERSEDED`, with provenance.

3. **Look-ahead tests.** Truncate the data at random dates and assert every
   earlier feature is unchanged. Fundamentals are lagged to filing date.
   Any signal used for live monitoring may use closes up to *t−1* only.

4. **Count every test.** The study’s `outputs/tests_run.csv` logs every
   test, including abandoned and underpowered ones. Nothing informal stays
   off the ledger.

5. **FDR.** Benjamini–Hochberg at **q = 0.10** runs once per study, at the
   end, over that study’s pre-registered family. Use Romano–Wolf (or an
   equivalent stepdown) when the family is a block of dependent regressors.

6. **Small-N honesty.** Any cell with **N < 8** is reported as a **prior
   only** and not tested. Cells with N < 10 print their full event lists.

7. **Kill log.** `outputs/killed_hypotheses.md` records every claim that
   failed and the number that killed it. It has the same status as the
   findings.

8. **Judgment inputs tagged.** Layer assignment, AI-exposure scores,
   episode dates and similar human codes are tagged (e.g.
   `JUDGMENT_CODED_POST_OUTCOME`) and tested with and without when they
   enter a decision.

9. **No post-hoc thresholds.** A result that survives only after changing
   the window, the universe or the threshold is not a result. Re-open the
   pre-registration instead.
