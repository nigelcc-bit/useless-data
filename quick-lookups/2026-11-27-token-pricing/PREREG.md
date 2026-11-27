# PREREG: Token pricing, crack or Jevons?

Written 2026-11-27 and committed before any test statistic is computed.
Folder: `quick-lookups/2026-11-27-token-pricing/`. Data: `token_pricing_data_pack.zip` (collected 2026-11-27), unzipped to `data/raw/` (gitignored).

## Question

Average AI token prices have fallen. The brief cites Ramp's blended OpenAI+Anthropic price at about -41% from the March 2026 peak*; that figure is unverified until computed here. Meanwhile token volume has grown. Three readings are possible:
- a **crack** in the AI revenue thesis (pricing power eroding, spend not keeping up);
- **healthy elastic demand** (Jevons: lower prices, more total spend);
- partly a **mix** effect (customers trading down to cheaper models) rather than like-for-like cuts.

## Conflict of interest

This study is about Anthropic's pricing power, and the analyst (Claude) is made by Anthropic. Rules:
- every claim traces to a file in the pack or a cited source;
- evidence for both camps is reported with equal prominence;
- findings unfavourable to Anthropic are not softened;
- killed results are reported as prominently as surviving ones.

## Disclosure: what was seen before this file was written

- **Pack README** read in full. Its caveats are binding (see below).
- **File headers** (column names, first 2-3 rows) of every file used.
- **Last rows of the two C1 vintage charts.**
  - `qWoIn_v1`, Oct 2026 letter: on 2026-10-11, volume index 1224.6 and spend index 614.0 (base 100 = 2026-01-11).
  - `7VRXW_v3`, Nov 2026 letter: on 2026-11-01, volume 1449.5 and spend 593.9.
  - These show volume growing faster than spend since January, i.e. the implied price fell. No elasticity was computed. The thresholds below come from the brief and were not tuned to these values.
- **Ramp's latest summary text**: Anthropic 58.7% of token spend in the week ending 15 Nov 2026; total token spend +12.0% vs the same week last month.
- **424B4 structure only.**
  - The quarterly statement of operations covers Q1 2025 to Q3 2026, with Revenue and "Compute and infrastructure" as an operating-expense line.
  - The filing says that during 2025 it moved to a nature-of-expense presentation, so "cost of revenue" and "gross profit" are **no longer presented**.
  - "Compute and infrastructure" covers research, model development, serving customers and internal usage.
  - The MD&A headline says revenue grew 1,127% year over year in Q3 2026 vs compute and infrastructure expense growth of 382%. That is an annual comparison and does not settle the two-quarter test below.
  - No quarterly values were read.

## Binding caveats (from the pack README)

1. Ramp "volumes" are indices. Use growth rates and ratios within a file, never levels across files. Within a file, maker columns share one scale. For example, Jan 2025 spend index A 3.9, O 1.4 gives 73.6% vs the published share of 72.8%, so summing Anthropic + OpenAI within one file is allowed.
2. Ramp token data is a subsample (Token Spend Management users with connected API keys).
3. Ramp revises history; letter chart CSVs are earlier vintages.
4. Derived per-model prices are approximate. They are only good for direction. Only models with at least 0.5% token share are included.
5. Wayback tables vary in layout; some cells hold "input / output" together.
6. OpenRouter is developer-skewed and covers 52 weeks only. It is descriptive.

## Skills and routes

| Skill | Use | Route |
|---|---|---|
| symptom-evaluation | Differential and discriminators (below), written before reading results | Installed; invoked via Skill tool |
| small-sample-truth | C3 effective N; any "X of Y windows" claim | Installed; invoked via Skill tool |
| tail-audit | C3 regression, OLS vs t-fit | Installed; invoked via Skill tool |

`quick-lookups/README.md` and `RESEARCH_PROTOCOL.md` live in the `useless-data` repo, which this session cannot read. Conventions are taken from the brief.

## Differential (symptom-evaluation)

**Symptom:** Ramp's blended OpenAI+Anthropic price per million tokens fell from its March 2026 peak to mid-November 2026, while token volume rose. Population: Ramp Token Spend Management businesses. Window: March 2026 peak week to the latest week (15 Nov 2026).

| Branch | Reading | Tests that speak to it |
|---|---|---|
| (a) Jevons, healthy | Spend grows as prices fall | C1 (sign and size of realised elasticity); C4 (revenue per compute dollar) |
| (b) Commoditisation | Like-for-like frontier prices fall, margins compress | C2 Fisher like-for-like index; C2 list-price index; C4 revenue per compute dollar and proxy margin; C3 (does share punish relative price?); C5 open-weight substitution (descriptive) |
| (c) Mix artefact (measurement branch) | Average price falls because usage shifts to cheaper models | C2 mix component |
| (d) Subsidised volume | Tokens without revenue (free tiers, promos) | **Not testable with this pack** |
| (e) Circular demand | AI firms' own workloads | **Not testable with this pack** |

Benign branch: (a). Artefact branch: (c).

**Discriminators**
- (a) vs (b): C1 latest |e| vs 1, together with the C4 revenue-per-compute trend.
- (b) vs (c): the share of the price fall explained by the C2 Fisher like-for-like index vs the mix residual.

## Tests

### C1 Realised spend-volume elasticity
- **Data:** `token_spend_by_model_maker_volumes.csv` and `token_volume_by_model_maker_volumes.csv`, Anthropic and OpenAI columns; combined = A + O within each file.
- **Sample start:** the first week in which all four series (A and O, spend and volume) are >= 1.0, to limit 1-decimal rounding error. Robustness: start 2026-01-11.
- **4-week table:** non-overlapping 4-week blocks, aligned to end at the latest week. Block sums give spend growth g_S and volume growth g_V; implied price growth = g_S / g_V.
- **Cross-check:** the implied price log-growth vs the log-growth of the 4-week mean of `token_prices_blended.csv` (matching column). Report the median absolute gap in log points.
- **Rolling realised elasticity**, weekly. S13(t) and V13(t) are 13-week sums ending at week t, and P13 = S13 / V13. Then e(t) = ln(V13(t)/V13(t-13)) / ln(P13(t)/P13(t-13)). It is labelled "realised", not causal, everywhere.
- **Readings** apply only when the price fell (ln P change < 0):
  - Jevons if |e| > 1 (spend rose).
  - Crack if |e| < 1 (spend fell) for >= 8 consecutive weekly windows.
  - Windows where the price rose are flagged as "price not falling".
- **Verdict input:** combined, latest window. Anthropic and OpenAI are reported separately.
- **small-sample-truth:** share of non-overlapping 13-week windows with |e| > 1, beta-binomial with a uniform prior.

### C2 Mix vs like-for-like
- **Data:** `DERIVED_implied_weekly_price_by_model_from_ramp_shares.csv`. q = token share, p = implied price.
- **Fisher index:** chain-linked weekly, using models present in both adjacent weeks. Laspeyres = sum p_t q_{t-1} / sum p_{t-1} q_{t-1}; Paasche = sum p_t q_t / sum p_{t-1} q_t; Fisher = sqrt(L x P).
- **Unit value** (blended price of covered models): UV_t = sum q_t p_t / sum q_t.
- **Decomposition:** ln(UV_T/UV_0) = ln(Fisher_T/Fisher_0) + mix. Report the like-for-like share and the mix share of the log change. Ramp's own blended change is reported alongside.
- **Base week:** the week ending (Sunday) whose date has the highest combined blended price in March 2026 in `token_prices_blended.csv`. Same base for each lab and combined. Robustness: each lab's own March peak.
- **Scope:** Anthropic models, OpenAI models, combined.
- **List-price index** (`list_prices_long.csv`):
  - (i) Fixed versions: models listed in both the last snapshot on or before 2026-03-31 and the latest snapshot of each lab. Input and output prices separately; ratio of geometric means.
  - (ii) Tier successors (descriptive): flagship and mid-tier list prices at both dates.
  - Compare direction with the Fisher index.
- **Validation:** the derived price averaged over April 2026 weeks vs Ramp's April 2026 published table, error per model.

### C3 Share vs relative price
- **Data:**
  - share = A / (A + O) from `token_spend_by_model_maker_shares.csv`;
  - x = ln(P_A / P_O), using 4-week means of the `token_prices_blended.csv` Anthropic and OpenAI columns;
  - both on the same 4-week blocks as C1.
- **Regression:** OLS of share (pp) on x, Newey-West SE with lag = floor(4 (n/100)^(2/9)), at least 1.
- **Block bootstrap:** moving blocks of 3 periods, 2,000 reps, 90% CI for the slope.
- **Effective N** = n (1 - rho) / (1 + rho), with rho = the AR(1) coefficient of residuals.
- **Robustness:** first differences.
- **tail-audit:**
  - univariate t-fit by EM (weights (nu + 1)/(nu - 2 + delta), nu by 1-D likelihood);
  - Wald test under the t-fit;
  - Hill index on residuals at k = 5% and 10% of n (flagged as meaningless if k < 3);
  - lowest-weight periods;
  - t vs Gaussian LR boundary test (5% critical value 2.71).
- **Hypothesis:** "Anthropic's share does not respond to its relative price." **KILLED if the slope is negative and significant at 5% under OLS-NW AND under the t-fit.** It is WEAK under tail-audit rules if significance holds in only one fit.
- **Weekly noise:** SD of week-to-week changes in A / (A + O). Locate the example jumps (51.3% to 60.5%, 53.2% to 49.3%), if present, and express each as a z-score vs that SD. "Inside the noise" if |z| < 2.

### C4 S-1 unit economics (424B4 primary)
- **Extract:** quarterly Revenue and Compute and infrastructure expense, Q1 2025 to Q3 2026, from the 424B4 quarterly table.
- **Revenue per compute dollar** = Revenue / Compute and infrastructure.
- **Proxy margin** = (Revenue - Compute and infrastructure) / Revenue. It is labelled "compute margin (proxy)" everywhere. It is **not** a gross margin: the filing presents none, and the compute line includes research and training.
- **Trend over the last two quarters**, Q1 2026 to Q3 2026:
  - "falling" if Q3 2026 < 0.98 x Q1 2026 (proxy margin: < Q1 - 2pp);
  - "stable or rising" otherwise.
- **Price-cut effect:**
  - $600M / (Rev Q3 2026 - Rev Q2 2026);
  - $70M / (Rev Q4 2025 - Rev Q3 2025);
  - passage text from `02_price_cut_disclosure`.
- **Computability:** C4 counts as computable if revenue per compute dollar can be extracted. A filing-defined gross margin is absent, which is a logged limitation, not grounds for INCONCLUSIVE.

### C5 OpenRouter (descriptive only)
- Open-weight share of tokens by week, from `weekly_tokens_open_vs_closed_weights.csv`.
- Compared with Ramp's OpenAI + Anthropic token-volume share trend over the same weeks.
- No inference.

### Revision robustness
- **C1:** recompute the combined 13-week realised elasticity from `qWoIn_v1` (earliest vintage, Oct 2026) and `7VRXW_v3` (Nov 2026) at each vintage's last week. Compare with current-page data at the same week.
  - These vintages index all Ramp token spend, not A + O only. The comparison is approximate, and this is flagged.
  - A flip = the Jevons/crack reading at that week differs.
- **C3:** recompute x from `0lGNa_v2` (Sep 2026, earliest) and `DUO9V_v3` (Oct 2026) daily prices over overlapping periods. No vintage of lab spend shares exists in the pack, so current shares are used and the check is partial.
  - A flip = the C3 kill status differs.

## Verdict rule

Claim: "falling token prices are a crack in the AI revenue thesis".

- **HOLDS:** all of the following.
  - C1 combined |e| < 1 in the latest window (price falling);
  - C4 proxy margin OR revenue per compute dollar falling over the last two quarters;
  - C2 like-for-like share of the combined fall >= 50%.
- **KILLED:** all of the following.
  - C1 combined |e| > 1 in the latest window;
  - C4 proxy margin AND revenue per compute dollar stable or rising;
  - C2 mix share of the combined fall >= 50%.
- **WEAK:** anything else, or a verdict that flips under the revision check.
- **INCONCLUSIVE:** C1 or C4 (revenue per compute dollar) cannot be computed.

Every test and variant is logged in `outputs/trials.csv`. Deviations after this commit go in RESULT.md under "Deviations".
