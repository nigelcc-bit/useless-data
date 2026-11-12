# Addendum to the 6 Nov note — which of seven calls survive?

**Two pages.** Updated **2026-11-12 (Australia/Melbourne)** after P7 final (FDR + exhibits).  
Study results pinned to **2026-11-05**. Monitor refresh is DESCRIPTIVE only.  
Full magnitude table: `docs/gap_diagnosis.md` §6. Kill log: `outputs/killed_hypotheses.md`.

---

## Page 1 — Scorecard

| Call | Claim | Survived? |
|---|---|---|
| 1 | Election = accelerant not origin | **Untested** (out of scope of H1–H5) |
| 2 | Builder–supplier seesaw returned (unlike October) | **Direction intact; not a factor.** Magnitudes corrected (builders −2.98%, suppliers −13.53% on 5 Nov; gap larger than printed). **H2 killed (K004)** — seesaw is description, not signal. **H4 outcome #2 triggered.** |
| 3 | Sort on crowding, not valuation | **Killed (K003).** Multivariate H3: neither crowding nor valuation adds power within layers; univariate crowding absorbed by layer dummies. |
| 4 | Policy exposure large; funding a second channel | **Partially.** H4 null rejected (wild p &lt; 0.001; CR2 p=0.005). Funding-dominates-October **not** supported (Shapley E6=0.011). What rotated: **layer composition**. |
| 5 | First-shock base rate favours bounce within a quarter | **Does not apply to the semis book (K002).** SOX on 5 Nov was a deep-DD cluster day, not a near-high first shock. H1b deep-DD: SOX 40% further-10% within 63d → **inconclusive**. |
| 6 | S&P has paid &lt;1/3 midterm fee; semis double | **Descriptive only** — not tested as a hypothesis. |
| 7 | Feed not capitulating; tally miscounted | **Survives** as an audit finding. |

### Pre-registered outcomes

| # | Outcome | Status |
|---|---|---|
| 1 | H2+H5 hold, L(5)&gt;0 → flush / patience | **Dead** (H2 K004; H5 PRIOR ONLY) |
| 2 | H4 rejects + layer dominates Nov → profit pool to builders | **Triggered** |
| 3 | H1 semis worse continuation than S&P | **Inconclusive** (H1b 40%; Call 5 does not transfer) |
| 4 | H3 valuation dominates → retract crowding | **Not triggered**; crowding unsupported (K003) |

---

## Page 2 — Detail the desk still needs

**H2 / Call 2.** Hetero-robust VR and Chow–Denning (p=0.45) do not reject a random walk; pooled de-clustered forwards net 30bp are insignificant (N=9). The 63d point estimate (+3.5% net, 7/9) is a **PRIOR**, not a finding. **4 Nov** (day after midterm) was an H2 −2.5σ event (z=−3.81); **5 Nov was not** (z=−0.59).

**H5 / monitor.** OOS troughs with complete L(10) = 4 &lt; 8 → **PRIOR ONLY; untested.** Daily desk monitor still ships (`python -m src.monitor.daily_desk`). Monitor refresh after the pin (snapshot through **2026-11-10**): the **5 Nov cum-spread trough was confirmed on 6 Nov**; L(5) not yet available (needs five sessions after confirmation); from confirmation through 10 Nov suppliers lead builders on cumulative return (+7.0% vs +2.4%); beta-neutral spread z path 6/9/10 Nov: +1.66 / +0.49 / +0.16. Label: **DESCRIPTIVE, single observation, H5 untested.**

**H3 / Call 3.** Layer Shapley R² dominates E5–E7 (~0.36–0.41). Crowding incremental adj-R² ≤ 0 in 5/6 counted episodes. Romano–Wolf stepdown on E3–E7 crowding/valuation PC1 p-values: no block survives multiplicity.

**H4 / Call 4.** Only pre-registered test that rejects after Benjamini–Hochberg q=0.10 (raw &lt;0.001 → BH≈0.011). Do not pool E6 and E7.

**H1 / Call 5.** Classification settles the transfer question before forward returns. Deep-DD history: coin-flip next quarter, strong following year for SOX — not a base-rate for patience from the S&P first-shock cell.

### Monitoring flips (operational; H5 PRIOR ONLY / untested)

Retired: “suppliers &gt;2× builders over the first five up days” — with a trailing beta ratio ≈2.3 that rule fires on almost any up market.

Use the daily desk instead (`python -m src.monitor.daily_desk`, prior US close, before 5pm HKT):

- **Beta-neutral spread z** (causal σ through t−1): ≤ −2.5 ≈ H2-style extreme; near 0 = no residual seesaw
- **L(5) / trailing supplier–builder beta ratio**: L(5)&gt;0 after a confirmed cum-spread trough = suppliers leading on a beta-adjusted rebound window; L(5)&lt;0 = builders leading
- Still watch: supplier–hyperscaler 21d corr &gt;0.8 rising together vs &lt;0.4; CRWV 2032 notes &gt;85 vs &lt;70; loan auction 19 Nov; Texas scope; S&P reclaim 7,500–7,600; VIX &lt;22 vs &gt;35; Dec FOMC
- SOXX 5 Nov low 130.74 intraday / 131.90 close (split-adjusted) — reference level only

### Cross-section corrections (P1)

Worst-7 on 5 Nov (Yahoo): LITE, MU, AMD, **IREN**, MRVL, LRCX, NBIS — note omitted IREN and kept VRT.  
Oct 2026 book (10 AI / 13 names) figures **UNRECONCILED** — membership not in uploads.
