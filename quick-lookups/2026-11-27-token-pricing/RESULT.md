# Token pricing: crack in the AI revenue thesis, or Jevons?

```
VERDICT: KILLED | confidence 45%
Claim: Falling token prices are a crack in the AI revenue thesis
Method: realised spend-volume elasticity, Fisher price index (mix vs like-for-like), share vs relative price, S-1 unit economics
Data: token_pricing_data_pack (Ramp AI Index, Anthropic 424B4, OpenRouter, Wayback), collected 2026-11-27 | Trials counted: 54
```

Pre-registration: `PREREG.md`, committed in fed-watchers as **bd31314** (https://github.com/nigelcc-bit/fed-watchers/commit/bd31314f21f737c30190bf860d003aca5885f26c) before any statistic was computed; the study moved here on 2026-11-27 without its git history. Run date 2026-11-27. Latest Ramp week: 15 Nov 2026.

Nothing here is a trading recommendation.

**Why the label is KILLED but confidence is only 45%.** All three pre-registered kill conditions are met, and the revision check flips nothing, so the rule says KILLED. Two of the three legs are fragile:
- **C2 depends on a definition.** The split rests on whether a cheaper successor model counts as "the same product". Counting successors within a tier as the same product (an exploratory check, not pre-registered) turns the mix result around and the verdict becomes WEAK.
- **C1 is close to its threshold.** Realised |e| has fallen every week for two months; Anthropic's is at **1.10**.

Conflict of interest: this study is about Anthropic's pricing power and was run by Claude, which Anthropic makes. Evidence for both camps is shown with equal weight below, and every number traces to a file in the pack.

## Headline table

| Measure | Reading | Pre-registered leg |
|---|---|---|
| Realised elasticity, latest 13 weeks (combined OpenAI + Anthropic) | **\|e\| = 1.33** (price -43%, volume +108%, spend +20%, in log terms -0.55 / +0.73 / +0.18) | \|e\| > 1: Jevons. **Kill leg met** |
| Same, Anthropic only | **\|e\| = 1.10**; 13-week spend growth **+5.9%** | Close to the line |
| Same, OpenAI only | **\|e\| = 1.76** | |
| Mix vs like-for-like since the 1 Mar 2026 peak (same model version, chain Fisher) | Covered-model price **-70%**. Like-for-like **+2%**, so **mix = 102%** of the fall | Mix >= 50%. **Kill leg met** |
| Same, successors linked by tier (**exploratory**) | Like-for-like **-65%**: **87%** of the fall (Anthropic **108%**, OpenAI **38%**) | Would fail the kill leg |
| Anthropic share vs ln(relative price), 4-week | **-13.4pp per log point**. Newey-West p **0.093**; block-bootstrap 90% CI **[-26.8, +2.1]**; t-fit p 0.055; **n = 23, effective n = 5.8** | Hypothesis "share does not respond" **survives** (not significant at 5% in either fit). Under `RESEARCH_PROTOCOL.md` rule 6 (N < 8) this is a **prior only**, not a test |
| Gross margin | **Not reported**: the 424B4 no longer presents cost of revenue or gross profit | Logged limitation |
| Compute margin (proxy: revenue minus compute and infrastructure, over revenue) | **28.4%** (Q1 2026), **51.9%** (Q2), **41.8%** (Q3) | Q3 vs Q1: stable or rising. **Kill leg met** |
| Revenue per compute dollar | **1.40** (Q1 2026), **2.08** (Q2), **1.72** (Q3) | Q3 vs Q1: stable or rising. **Kill leg met** |
| ...but the latest quarter | Revenue per compute dollar **-17%** and compute margin proxy **-10.1pp**, Q2 to Q3 2026 | Not the pre-registered test; reported with equal weight |
| Price-cut disclosure | **$600M** = **11.1%** of the Q2 to Q3 2026 revenue increase ($5,401M); **$70M** = **10.6%** of the Q3 to Q4 2025 increase ($658M) | Context |

Charts in `outputs/`:
- `chart_rolling_elasticity.png`
- `chart_price_index_decomposition.png`
- `chart_share_vs_relative_price.png`
- `chart_s1_quarterly_economics.png`

## Conclusion

On the pre-registered tests, falling token prices do **not** look like a crack yet.
- **Spend has kept rising as prices fell.** Every 13-week window with a falling price since the first one (August 2025) shows |e| > 1, and there were zero "crack" windows (|e| < 1 with the price falling).
- **Same-version prices haven't fallen.** Models that exist at both dates are no cheaper, on Ramp effective prices (Fisher +2%) or on list prices (9 Anthropic models, ratio 1.00).
- **Anthropic's revenue per compute dollar is higher than at the start of 2026.**

The case for the crack camp is real, though:
- **Successors are much cheaper.** Each new Anthropic tier is priced well below the one it replaced: Opus $5/$25 to $4/$20, Sonnet $3/$15 to $2/$10, Haiku $1/$5 to $0.10/$0.50 per million input/output tokens. Counted tier for tier, effective prices fell **65%**, and Anthropic's own filing describes its $600M revenue hit as "price reductions introduced as part of new model versions".
- **Elasticity is sliding toward 1.** Combined e went from **-2.63 to -1.33** in eight weeks; Anthropic's spend growth over 13 weeks has slowed to +5.9%.
- **The latest quarter got worse.** Revenue per compute dollar and the compute margin proxy both fell sharply in Q3 2026.

The honest reading: demand has so far outrun price cuts, but the cushion is thinning fast.

## Would change if

- **Ramp weekly data, next 2-4 weeks** (and the December 2026 Ramp AI Index letter*, date not in the pack): the crack reading needs combined |e| < 1 for 8 consecutive weeks. At the current pace, Anthropic's |e| could cross 1 within the next few weekly prints. One cross is not the crack reading; eight weeks is.
- **Anthropic's first periodic report covering Q4 2026** (likely the FY2026 10-K in early 2027*; verify the filing date):
  - another quarter of falling revenue per compute dollar (below 1.72) would make Q4 vs Q2 "falling";
  - so would a compute margin proxy below 41.8% (Q4 vs Q2) on the same rule.
- **A per-model price source with more than 4 weeks of overlap** that confirms or rejects the derived prices (Sonnet 4.6 is off by 37%).

## Strongest rival explanation

**(b) Commoditisation, delivered through new versions.** Labs cut price by launching cheaper successors rather than repricing old models. A same-version index can't see that, so it shows up as "mix". This reading is consistent with:
- the tier-successor list prices;
- the tier-linked index (87% like-for-like);
- the S-1's own wording;
- the Q3 2026 drop in revenue per compute dollar.

It is not consistent with spend still rising faster than prices fall (C1).

## Differential (symptom-evaluation)

| Branch | Evidence | Status |
|---|---|---|
| (a) Jevons, healthy | C1: all 51 price-falling windows have \|e\| > 1; C4 Q3 vs Q1 up | **Leading on pre-registered tests**, weakening |
| (b) Commoditisation | Tier-linked index 87% like-for-like; successor list cuts of 20% to 90%; C4 Q2 to Q3 down; $600M price-cut disclosure | **Strong rival** |
| (c) Mix artefact | Same-version Fisher +2% (mix 102%); fixed-version list prices unchanged | Supported **only** if a successor counts as a different product |
| (d) Subsidised volume | Not testable with this pack. Related: the 424B4 estimates **5% to 7%** of nine-month 2026 revenue came from customers violating usage policy or commercial terms, expected to decline | Untested; flagged |
| (e) Circular demand | Not testable with this pack | Untested |

## Killed and failed results

- **The crack reading in C1:** zero qualifying windows (needs >= 8 consecutive weeks of |e| < 1 with the price falling; longest run 0).
- **The HOLDS rule:** none of its three conditions is met.
- **C3's kill rule** ("negative and significant in both fits") was **not** met, so the hypothesis "share does not respond to relative price" survives. Two caveats:
  - The slope is negative, with p = 0.09 (Newey-West) and 0.055 (t-fit), on an effective n of only **5.8**.
  - In first differences the slope is -6.0 (p 0.53). tail-audit labels that variant WEAK (the coefficient moves 50% under the t-fit; nu = 2.9).
- **The brief's "-41% from the March 2026 peak" does not reproduce on current-vintage data.** Ramp's combined blended price went from **$1.16** (7 days to 1 Mar) to **$0.45** (7 days to 15 Nov), **-61%**. The brief's figure may come from an earlier vintage.
- **The example share jumps** (51.3% to 60.5%, 53.2% to 49.3%) do not appear in the current-vintage weekly data. Scored by size against the weekly noise in Anthropic's share (SD 4.35pp, or 2.56pp in 2026):
  - +9.2pp is **outside** the noise (z 2.1, or 3.6 against the 2026 noise);
  - -3.9pp is **inside** it (z -0.9 / -1.5).
- **OpenAI fixed-version list-price index:** not computable. The Nov 2026 snapshot lists only the GPT-6 family, so 0 models match March.

## Revision check

Nothing flips.

| Check | Vintage | Current data, same week | Flip? |
|---|---|---|---|
| C1 at 11 Oct 2026 (Oct letter, qWoIn v1) | e = -2.94, Jevons | e = -2.11, Jevons | No |
| C1 at 1 Nov 2026 (Nov letter, 7VRXW v3) | e = -1.71, Jevons | e = -1.47, Jevons | No |
| C3 on Sep 2026 prices (0lGNa v2, 8 blocks) | slope +15.7, p 0.002 | not killed either way | No |
| C3 on Oct 2026 prices (DUO9V v3, 9 blocks) | slope +4.0, p 0.59 | not killed | No |

Caveats on the revision check:
- **C3 is only partially checkable.** No vintage of lab spend shares exists, so only prices were swapped. The vintage relative prices differ from current ones by 0.15 to 0.24 log points on average.
- **The sign of the C3 slope differs between the old 2026 price vintages and the full current sample.** That shows how fragile C3 is.
- **The C1 vintages cover all Ramp token spend,** not OpenAI + Anthropic only.

## Caveats

- **Ramp data:** a subsample (Token Spend Management users with connected API keys). Volumes are indices, and history is revised.
- **Derived per-model prices are approximate.** Validation against Ramp's April 2026 table:
  - Haiku 4.5 **+2%**, Opus 4.6 **+13%**, Sonnet 4.6 **+37%**;
  - the three OpenAI models in the table were below the file's 0.5% share cut-off in April.
  - Coverage of token share is **73.8%** at the base week and **87.6%** at the latest; Grok 4.7 sits in "combined".
- **Effective prices are not list prices.** Ramp's price is per token across input, output and cached tokens. Part of the tier-level fall (Opus 4.6 at $1.70/M in March vs Opus 5.5 at $0.44/M now, while its list price fell only 20%) reflects how tokens are used (caching, input/output mix), not only lower prices.
- **"Compute and infrastructure" is not cost of revenue.** It includes research, model training and internal usage, so the proxy margin is not comparable to a software gross margin.
- **Realised elasticity is not causal.** New models shift demand at the same time as prices change.
- **C3 has a spurious-regression risk:** both series trend. Residual autocorrelation is 0.60, hence effective n 5.8.
- **OpenRouter (C5) is descriptive only.** Its open-weight token share rose from **27.1%** to **77.1%** (1 Dec 2025 to 23 Nov 2026), while OpenAI + Anthropic still hold **97.5%** of Ramp token volume. OpenRouter is developer-skewed and Ramp is enterprise; the two samples barely overlap.

## Deviations from pre-registration

1. **C2x tier-linked index added after seeing results.** It is exploratory, labelled as such everywhere, and does not change the pre-registered verdict. It was added because the matched-model index cannot see price cuts that arrive as new versions, which the S-1 says is how Anthropic cut prices.
2. **Example jumps not found in the data.** They were scored by their stated size against the weekly noise, instead of being located.
3. **Base week.** The pre-registered rule picks the March Sunday with the highest 7-day price: 1 Mar 2026. That is also the daily March peak.

## Protocol alignment (added 2026-11-27, on moving to useless-data)

The study was first written in fed-watchers, without access to this repo's `quick-lookups/README.md` and `RESEARCH_PROTOCOL.md`. On the move it was checked against both. None of the changes below alters the pre-registered verdict.

- **Rule 6, small N.** C3's effective sample is 5.8, below 8, so C3 is a **prior only** and is not counted as a test of the hypothesis. The 23 four-week observations behind it are listed in `data/c3_share_vs_relative_price_4wk.csv`. The C1 small-sample card (4 non-overlapping 13-week windows, all with \|e\| > 1) is also a prior only.
- **Rule 5, false discovery rate.** Benjamini-Hochberg at q = 0.10 over the four C3 p-values: Newey-West levels 0.093, t-fit levels 0.055, Newey-West differences 0.528, t-fit differences 0.090. **None passes**; the smallest needs 0.025. No other test in this lookup produces a p-value.
- **Rule 1, freeze before results.** The freeze commit lives in fed-watchers (link above), because history was not carried over.
- **Earlier "not done" items, now resolved.**
  - The MU regime-read results (commit `16e3557`) were already on `main` via PR #28.
  - This repo's conventions are now read and applied (this section).
- **Unchanged on purpose.** `PREREG.md` is frozen text. Its line saying this repo could not be read was true when written, and is left as it is.

## Files

- `PREREG.md`: pre-registration (fed-watchers commit bd31314)
- `run.py`: reruns everything from `data/raw/` (the unzipped pack, gitignored)
- `data/*.csv`: processed tables, by test (c1 to c4, c2x exploratory)
- `outputs/trials.csv`: all 54 trials; `outputs/results.json`: every number above
- `outputs/chart_*.png`: four charts

## Reviewer note (2026-11-27)

Added after the result. It does **not** change the pre-registered verdict above (KILLED, 45%), which stands as the record of what the frozen rule produced.

**C2 spec flaw.** The pre-registered like-for-like measure is a same-version index: it compares each model only with itself. It cannot see price cuts delivered through cheaper successor models, and the S-1 says that is how Anthropic's cuts happened: "price reductions introduced as part of new model versions and contractual discounts". Every Anthropic tier's successor is listed below its predecessor (Opus $5/$25 to $4/$20, Sonnet $3/$15 to $2/$10, Haiku $1/$5 to $0.10/$0.50). So the kill leg "mix >= 50% of the fall" was met **largely by construction**. The same-version index showed +2% while the tier-linked index showed -65% (87% like-for-like).

**C4 wording flaw.** "Falling over the last two quarters" was operationalised as Q3 2026 vs Q1 2026, which reads as stable or rising. Quarter on quarter, Q2 to Q3 2026:
- revenue per compute dollar fell **17%**, from **2.08** to **1.72**;
- the compute margin proxy fell **10.1pp**, from 51.9% to 41.8%.

Read quarter on quarter, the C4 kill leg fails and the HOLDS leg ("falling") is met.

**C3** is a prior only under protocol rule 6 (effective N 5.8) and plays no part in the verdict rule.

**Reviewer reading: WEAK, about 55% confidence.**
- **C1:** spend still outran price cuts in the latest window (combined \|e\| 1.33). That points away from a crack, but Anthropic's \|e\| (1.10) is near the line and falling.
- **Corrected C2:** like-for-like at the tier level is 87%, which points to commoditisation.
- **Corrected C4:** quarter on quarter, the latest quarter is falling.

With the legs split, the pre-registered rule's "anything else" branch gives WEAK.

**Conflict of interest.** Claude, which Anthropic makes, ran this study about Anthropic's pricing power. Both flaws pushed toward the verdict favourable to Anthropic (KILLED). That is why they are written up here in full and why a forward test with the corrected specs is pre-registered in `FORWARD_PREREG.md`.
