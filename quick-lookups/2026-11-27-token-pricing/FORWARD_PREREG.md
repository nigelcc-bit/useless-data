# FORWARD_PREREG: token pricing, forward test on new data only

Written and committed 2026-11-27, **before** any Ramp data after the week ending 15 Nov 2026, or any Anthropic report covering Q4 2026, is loaded. The scoring script `score_forward.py` is committed **after** this file.

Nothing here is a trading recommendation.

## Why this exists

The original test (`PREREG.md`, verdict in `RESULT.md`) had two spec flaws, recorded in the 2026-11-27 reviewer note. Both pushed toward the verdict favourable to Anthropic:
- **C2** used a same-version index that cannot see price cuts delivered through successor models.
- **C4** compared Q3 with Q1 instead of quarter on quarter.

This file fixes both specs and tests them **only on data that did not exist when the flaws were found**. The original verdict is not edited.

**Conflict of interest.** The analyst is Claude, made by Anthropic; the subject is Anthropic's pricing power. The thresholds below are fixed now and are not changed after new data arrives.

## What "new data" means

- **Ramp:** weekly rows with week ending **after 2026-11-15**, from a fresh capture of the Ramp AI Index page (same CSV names as `data/raw/04_ramp_ai_index_data/`).
  - Save each capture under `data/raw_forward/<capture-date>/04_ramp_ai_index_data/` (gitignored), and record the capture date.
  - The latest capture is the vintage used. If Ramp revises weeks up to 15 Nov, the revised history is used and the size of the revision is reported.
- **Anthropic:** the first SEC report that covers the quarter ending 31 Dec 2026. That is probably the FY2026 Form 10-K*; the filing date is **unverified**, so check EDGAR.
- **Disclosure.** The original run already loaded the pack's daily 7-day blended prices for 16 and 17 Nov 2026. No other post-15-Nov data has been seen. The forward tests use weekly data only.

## C1 Realised elasticity (crack signal)

- **Method:** unchanged from `PREREG.md` C1.
  - Weekly Ramp spend and volume indices (`token_spend_by_model_maker_volumes.csv`, `token_volume_by_model_maker_volumes.csv`).
  - Sample starts at the first week in which all four Anthropic/OpenAI series are >= 1.0.
  - Combined = Anthropic + OpenAI within each file.
  - S13, V13 = 13-week sums; P13 = S13 / V13; e(t) = ln(V13(t)/V13(t-13)) / ln(P13(t)/P13(t-13)).
- **Forward windows:** windows ending on weeks after 2026-11-15. The first is the week ending 2026-11-22.
- **C1 hits (crack)** when, in **8 consecutive** forward windows, **both** Anthropic and Combined have a falling price (ln P13 change < 0) **and** |e| < 1.
- **When it is scored:**
  - First scoring at the week ending **2027-01-10**, the 8th forward week. That is interim unless C1 has hit.
  - After that, it is re-scored at each capture until the C4 report is filed.
  - A hit at any point before the C4 report's filing date counts.

## C2 Tier-linked like-for-like index (corrected primary; reported, not in the verdict rule)

- **Per-model prices** are rebuilt from the new capture the same way the pack's derived file was: p_i = blended OpenAI+Anthropic 7-day price at the week-end date x (model spend share / model token share), for models with token share >= 0.5% that week.
- **Tier prices:** p_tier = token-share-weighted mean of p_i within the tier; q_tier = sum of token shares.
- **Index:** chain-linked weekly Fisher over the tiers present in both adjacent weeks.
  - Base week **2026-11-15**; end at the latest forward week.
  - Unit value UV = sum q p / sum q over covered models.
  - Like-for-like share = ln(Fisher change) / ln(UV change), defined only if UV fell.
- **Commoditisation reading** if the like-for-like share is **>= 50%** of the further fall. If UV did not fall, report "no further fall".
- **Secondary:** the same-version index (the original C2), reported alongside.
- **Tier mapping (frozen now).** The tier is the first rule that matches the model name:
  1. Contains Opus, Sonnet, Haiku, Fable or Mythos (checked in that order): `claude-<word>`.
  2. Contains Codex, Nano, Mini, Luna, Terra, Sol or Astra (in that order): `gpt-<word>`.
  3. Starts with "GPT": `gpt-base`.
  4. Starts with "o" followed by a digit: `o-series`.
  5. Anything else: its own lower-cased name (its own tier).

  A successor is the same product as its predecessor within a tier. New models are mapped by the same rules, **without exception**. Any new model that lands in `gpt-base` or in its own tier is listed in the output so readers can judge it; the mapping is not changed.

  Mapping of every model in the pack (46):

| Model | Tier |
|---|---|
| Claude Fable 5 | claude-fable |
| Claude Fable 5.1 | claude-fable |
| Claude Fable 5.2 | claude-fable |
| Claude 3.5 Haiku | claude-haiku |
| Claude Haiku 4.5 | claude-haiku |
| Claude Opus 4.1 | claude-opus |
| Claude Opus 4.5 | claude-opus |
| Claude Opus 4.5 (2025 11 01) | claude-opus |
| Claude Opus 4.6 | claude-opus |
| Claude Opus 4.7 | claude-opus |
| Claude Opus 4.8 | claude-opus |
| Claude Opus 5 | claude-opus |
| Claude Opus 5.5 | claude-opus |
| Claude 3.5 Sonnet | claude-sonnet |
| Claude 3.7 Sonnet | claude-sonnet |
| Claude Sonnet 4 | claude-sonnet |
| Claude Sonnet 4.5 | claude-sonnet |
| Claude Sonnet 4.6 | claude-sonnet |
| Claude Sonnet 5 | claude-sonnet |
| Claude Sonnet 5.5 | claude-sonnet |
| GPT-6 Astra | gpt-astra |
| GPT-4.1 | gpt-base |
| GPT-4o | gpt-base |
| GPT-5 | gpt-base |
| GPT-5.1 | gpt-base |
| GPT-5.2 | gpt-base |
| GPT-5.4 | gpt-base |
| GPT-5.5 | gpt-base |
| GPT-5 Codex | gpt-codex |
| GPT-5.1 Codex | gpt-codex |
| GPT-5.2 Codex | gpt-codex |
| GPT-5.3 Codex | gpt-codex |
| GPT 6 Luna | gpt-luna |
| GPT-5.6 Luna | gpt-luna |
| GPT-4.1 Mini | gpt-mini |
| GPT-4o Mini | gpt-mini |
| GPT-5 Mini | gpt-mini |
| GPT-5.4 Mini | gpt-mini |
| o4 Mini | gpt-mini |
| GPT 6 Sol | gpt-sol |
| GPT 6.1 Sol | gpt-sol |
| GPT-5.6 Sol | gpt-sol |
| GPT 6.1 Terra | gpt-terra |
| GPT-5.6 Terra | gpt-terra |
| Grok 4.7 | grok 4.7 |
| o3 | o-series |

## C4 Quarter-on-quarter unit economics (corrected)

- **Inputs:** Q4 2026 Revenue and Compute and infrastructure expense, from the first report covering Q4 2026.
  - If only full-year figures are given: Q4 = FY2026 - (Q1 + Q2 + Q3 2026). Use the report's own Q1-Q3 figures if it gives them, else the 424B4's.
  - If the line item is renamed or reclassified so that it is not comparable, C4 is **INCONCLUSIVE**. No substitute line is used.
- **Revenue per compute dollar** = Revenue / Compute and infrastructure. **Compute margin proxy** = (Revenue - Compute and infrastructure) / Revenue.
- **Thresholds:** Q3 2026 from the 424B4, $16,956M revenue and $9,863M compute and infrastructure. That gives revenue per compute dollar **1.7192** (shown as 1.72) and a proxy margin **41.83%** (shown as 41.8%).
  - If the new report restates Q3, the restated Q3 is used and the restatement is noted.
- **C4 hits (crack)** when Q4 revenue per compute dollar is **below 1.7192 AND** the proxy margin is **below 41.83%**.

## Verdict rule

Claim: falling token prices are a crack in the AI revenue thesis.

- **HOLDS:** C1 hit AND C4 hit.
- **KILLED:** neither C1 nor C4 hit by the time the Q4 report is filed.
- **WEAK:** exactly one hit.
- **INCONCLUSIVE:** C4 not computable, or no report covering Q4 2026 has been filed by **2027-04-30**. That date is a placeholder deadline because the filing date is unverified; if a later due date is verified, this is noted, not silently changed.
- **Interim:** before the Q4 report, the status is "interim", with C1 and C2 readings reported.

## Ledger and outputs

- `score_forward.py` appends one row per scoring run to `outputs/forward_scores.csv`. The row records the capture date, last week used, C1 run lengths, C2 shares, C4 values (if supplied), and the verdict status.
- Every scoring run and variant is also appended to `outputs/forward_trials.csv`.
- Earlier rows are never edited.
