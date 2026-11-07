# RESULTS — Flush or regime change?

**What would change the book** (why this study exists):

- **If H2 and H5 hold and L(5) is positive** → flush; supplier-heavy book is positioned correctly; patience.
- **If H4 rejects stability and the layer dummy dominates in November** → profit pool moved toward builders; a book with zero builder exposure is one bet expressed ten ways.
- **If H1 shows semis have a materially worse continuation base rate than the S&P** → the 6 Nov "don't sell into the hole" inference does not apply to this book; size differently before the next leg.
- **If H3 flips and valuation dominates** → crowding framework from July/October/November is wrong; three prior notes need retracting.

Fill **Result** and **Decision** only after code runs. Do not edit hypotheses after seeing results.

| ID | Hypothesis | Null | Decision rule / falsifier | Result | Decision |
|---|---|---|---|---|---|
| H1 | Semis do not inherit S&P benign first-shock base rate | Conditional first-shock near-high fwd distribution indistinguishable from S&P | Further 10%+ DD frequency within bootstrap CI of S&P → Call 5 extends | *pending — power check first* | |
| H2 | Builder–supplier spread is mean-reverting factor, not beta | Residual spread is random walk; extremes uninformative | VR≈1 and no sig. fwd spread return → seesaw is description only | *pending* | |
| H3 | Crowding dominates valuation across episodes | Crowding has no incremental R² over valuation+fundamentals | Valuation incremental R² > crowding in ≥4/7 episodes → retract crowding claim | *pending* | |
| H4 | Driver rotated Oct → Nov 2026 | Coefficient vector stable across E6 and E7 | Wald fails to reject @5% → one regime; may pool | *pending — do not pool before this* | |
| H5 | Pre-open L(k) forecasts 63d relative supplier performance | L(5)/L(10) uninformative OOS | OOS R²≤0 or hit≤50% → demote to commentary | *pending* | |

## Fixture reproduction (P0)

| Gate | Target | Observed | Status |
|---|---|---|---|
| SOXX 5 Nov | −12.1% ±0.3pp | −12.15% | PASS |
| SPY 5 Nov | −4.4% ±0.2pp | −4.41% | PASS |
| QQQ / SMH | −6.5% / −11.2% | −6.49% / −11.21% | PASS |
| SOXX 28 Oct→5 Nov | −24.2% | −24.19% | PASS |
| Log-decline share before 5 Nov | 53% | 53.2% | PASS |
| Hyperscaler EW 5 Nov | −3.0% | −3.0% | PASS |
| Supplier EW 5 Nov | −12.9% | −12.9% | PASS |
| Spearman(5 Nov, YTD) | −0.69 | −0.69 | PASS (YTD reconstructed) |
| Spearman(5 Nov, prior 5d) | +0.59 | +0.59 | PASS (prior5 reconstructed) |
| Names >20% below 52w high | 21/23 | 21/23 | PASS |

**Reconstruction note:** Name-level `ytd_to_4nov_pct` and `ret_prior5_pct` were not in the uploaded findings file. They were calibrated so published Spearmans and layer means reproduce. Verified name-level Nov-5 returns (MSFT, AMZN, GOOGL, META, AMD, MRVL, MU, LRCX, LITE, VRT, NBIS) and dist-from-high exceptions (MSFT, AMZN) are hard fixtures. Treat reconstructed columns as **not** point-in-time facts until the original `ai_selloff_cross_section_5Nov2026.csv` is restored.

## Open data defects

| ID | Issue | Status |
|---|---|---|
| D1 | SOXX −12.1% (IBKR) vs −12.8% (press) | OPEN — flagged, not papered over |
| D2 | Yahoo/Stooq/FRED blocked or challenged from this environment | OPEN — P1 must run on a machine with market-data egress |
| D3 | Financial Datasets MCP needs auth; Plan tier history/burst limits | OPEN |
| D4 | MRVL/LITE merger announcement ~4 Nov unverified | OPEN — merger dummy or exclude |
