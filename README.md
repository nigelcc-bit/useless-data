# Equity research programme

Shared `core/` library and dated studies under `studies/`. Each study is a
false-discovery controller: pre-register, count every test, kill what fails.
Governing rules: [`RESEARCH_PROTOCOL.md`](RESEARCH_PROTOCOL.md).

Nothing here is a trading recommendation.

## Start a new study

```bash
python3 scripts/new_study.py <slug>   # → studies/YYYY-MM-<slug>/
```

Edit that folder’s `SPEC.md` / `RESULTS.md` before computing. Point
`config/pins.yaml` at the `core/reference/*_v…` versions you freeze.
Set `AI_STUDY_DIR` if more than one study is active; otherwise the default
is `studies/2026-11-flush-or-regime`.

## Studies

| Name | Question | Status | Tag |
|---|---|---|---|
| [2026-11-flush-or-regime](studies/2026-11-flush-or-regime/) | After a violent AI-supply-chain decline, does the cross-section mean-revert (flush) or does leadership rotate (regime change)? | **Complete** — H2 killed (K004); H3 unsupported (K003); H4 rejects; H5 prior only; P7 FDR/exhibits done | `flush-or-regime-v1` |
| [2026-11-testing-nasdaq-bear-trap](studies/2026-11-testing-nasdaq-bear-trap/) | Does reclaiming a broken swing low (Nasdaq "bear trap") predict better-than-normal returns vs drawdown-matched days? | **Interim** — Study 1 filed; Tier 1 code filed (A–D); full-data run pending clean CSVs | — |
| [11-2026-fed-path-vs-term-premium](studies/11-2026-fed-path-vs-term-premium/) | Study 4: how much of the 2026 rise in the 10-year yield is the expected Fed path versus the term premium (ACM primary, Kim-Wright secondary), and is the mix unusual against past hiking cycles? | **Complete** (P1 live check pending 9 Dec 2026) — H1 path driven; H3, H4a, H4b, H5a killed (BH); H2, H5b prior only; [note](studies/11-2026-fed-path-vs-term-premium/NOTE.md) | — |

## Layout

```
core/                 shared ingest, adjust, features, stats, reference YAML
studies/<dated>/      one study: config, src, tests, docs, outputs, RESULTS
studies/_template/    scaffold for scripts/new_study.py
data/                 shared raw / processed (not study-local)
tests/                generic gates (no study-specific fixtures)
RESEARCH_PROTOCOL.md  programme rules
```

## Install

```bash
python3 -m pip install -e ".[dev]"
PYTHONPATH=.:studies/2026-11-flush-or-regime pytest
```

## Findings

[`FINDINGS.md`](FINDINGS.md) summarises every study in one machine-readable
file: one `## studies/<folder>` section per study, a
`Status: complete | interim | Run: YYYY-MM-DD | Source: <file>` line, and one
YAML block listing 3-8 findings. Killed and prior-only results are findings
too.

Every finding has these fields (use `null` where not applicable):

| Field | Meaning |
|---|---|
| `id` | `ud-<study-slug>-<short-key>`, unique and stable across re-runs |
| `study` | `studies/<folder>` |
| `type` | `quant` |
| `region` | `US` or `global` |
| `topic` | e.g. `equities`, `ai-supply-chain`, `rates`, `methods` |
| `claim` | one plain-English sentence, at most 30 words, results only, no advice |
| `verdict` | `supported`, `killed`, `weak`, `prior-only`, `inconclusive` or `interim` |
| `confidence` | the study's own stated confidence, else `null` |
| `numbers` | strings copied verbatim from `source_file` (no rounding or conversion) |
| `source_file` | exact path of the file the numbers come from |
| `run_date` | `YYYY-MM-DD` |
| `valid_until` | `YYYY-MM-DD` if the result depends on live prices or a scheduled re-check, else `null` |
| `owner_bot` | `vera` or `tilly` |
| `links_to` | ids of related findings, including `fw-...` ids in fed-watchers |
| `people` | `[]` |

**Replace on re-run.** Re-running a study replaces its section; it never
adds a second one. Ids stay the same so links keep working.

`python scripts/check_findings.py` fails if a block does not parse, a field
is missing or invalid, an id or section is duplicated, a number is not found
verbatim in its source file, or a study with a `RESULTS.md` (or a README
`## Answer` section) has no section. It warns when `valid_until` has passed.
CI runs it on every push.
