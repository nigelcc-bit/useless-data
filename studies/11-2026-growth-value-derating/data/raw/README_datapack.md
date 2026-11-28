# Growth vs Value data pack (pulled 28 Nov 2026)

Status per requested row. "Got it" means the requested data from the requested source (or its fallback) over the requested window.

| # | Item | Result | Source actually used | Window delivered |
|---|---|---|---|---|
| 1 | Growth and Value forward P/E (Yardeni) | **Got it (digitised)** | Yardeni Growth vs Value page, Fig 4 (daily, LSEG Datastream I/B/E/S image), digitised at 9999x1500 px | Daily 1995 to 27 Nov 2026; weekly Fri from Jan 2024 (152 weeks, no gaps) |
| 2 | Growth and Value forward EPS | **Got it (two independent ways)** | (a) Yardeni Figs 16/17 "Blue Angels" lines digitised; (b) S&P DJI price index divided by Row 1 P/E | Weekly 2007 to now; (a) ends about 30 Oct 2026 (chart data end), (b) runs to 27 Nov 2026 |
| 3 | Growth and Value price index | **Got it (primary source)** | S&P DJI index pages (index IDs 2029 Growth, 2034 Value, 340 S&P 500) | Daily Oct 2016 to 27 Nov 2026 (730 days from Jan 2024) |
| 4 | DFII10 and DGS10 | **Got it** | FRED | Daily Jan 2024 to 25 Nov 2026 (FRED not yet updated for 27 Nov); T10YIE included |
| 5 | Top 15 Growth holdings and weights | **Got it** | iShares IVW holdings (official as-of 31 Dec 2025 and 25 Nov 2026), plus IVE both dates and a pre-rebalance IVW file (7 Nov 2025, Wayback) | Snapshots |
| 6 | Cash flows for the top-15 names | **Got it, with gaps** | SEC EDGAR XBRL company facts (10-Q/10-K), quarterly derived from YTD where needed | 15 quarters per company, 2023 Q1 to latest filed |
| 7 | Style rebalance dates and constituent changes | **Partly** | S&P DJI announcements (2 PDFs), S&P DJI blog, membership changes inferred from IVW holdings | Dec 2025 effective date is inferred from convention, not a primary notice |
| 8 | Revision breadth, Growth vs Value, monthly | **Partly: snapshot plus proxy** | Yahoo consensus (up/down revisions last 30 days) for all 587 holdings, weighted by ETF weights; monthly proxy from Row 2 | Breadth: one snapshot (28 Nov 2026). Monthly proxy: Dec 2024 to Nov 2026 |
| 9 | Constituent forward EPS | **Partly: "now" only** | Yahoo Finance consensus (FY0, FY1, and the 7/30/60/90-days-ago values) | 503 of 507 tickers, 28 Nov 2026. End-2025 snapshot **not obtained** |
| 10 | IG spread, tech/hyperscalers vs IG index | **Fallback only** | FRED BAA10Y, AAA10Y, ICE BofA IG OAS overall and by rating | Daily 2024 to 26 Nov 2026, weekly 2025 to now. **No tech-specific spread** |

## Accuracy and validation

- **Row 1 P/E**: digitised end values Growth 17.10 and Value 17.29 against Yardeni legend 17.0 and 17.3 (27 Nov). Value/Growth ratio on 19 Nov is 0.984 against Fig 22's published 0.98. Spot checks: 13 Aug 2021 within 0.05 of published values. One spot check (9 Nov 2020) was off by about 0.8 for Growth, possibly the vaccine-day gap within a single pixel column, so treat single days around violent moves with care. Resolution is about 0.04 P/E points and about 1.2 calendar days per pixel column, so dates are approximate to about plus or minus 2 days. Weekly values are the last column on or before each Friday.
- **Row 2 EPS**: the two methods agree. From 2024, (b)/(a) minus 1 averages +0.4% (sd 0.85% Growth, 0.63% Value). The four Growth Blue Angel lines agree with each other within a median 0.37%. Blue Angel legend anchors (19 Nov): Growth 8,779.08/30 = 292.6, Value 2,677.90/20 = 133.9; derived (b) around 19 Nov gives about 287 to 296 and 132 to 134. Method (b) is noisier week to week (about 1%) because the P/E dates are approximate.
- **Level breaks**: forward EPS for a style index jumps at each December reconstitution (index membership changes). See the Dec 2024 weekly moves in Row 2. Do not compute growth rates across a December without chain-linking.
- An earlier apparent conflict (Fig 16 index level) was a misread of the legend; the chart says 5,065.71, matching S&P DJI 5,065.72.
- **Row 6**: SEC values match Financial Datasets for NVDA exactly. Financial Datasets' MSFT D&A is wrong (quarterly values around 1 to 2bn and annual totals in Q4), so SEC XBRL is used throughout. `capex_to_dep`, `ocf_to_ni`, `fcf_ocf_minus_capex` and `fcf_minus_sbc` are computed columns. Units are USD millions.

## Known gaps and caveats (by row)

- **Row 4**: holiday blanks left as NaN, not filled.
- **Row 5**: IVW is a fund, not the index; weights differ slightly from S&P DJI. S&P DJI's own site only shows the top 10 official index weights (as of 30 Oct 2026; in `row5_spdji_top10_official_index_weights_20261030.csv`). Alphabet appears as two lines (GOOGL, GOOG). Berkshire's ticker normalised to BRK.B.
- **Row 6**:
  - MSFT D&A is depreciation only (from the PP&E note) and is missing for 6 quarters in 2023 to early 2024; MSFT's cash flow "depreciation, amortization, and other" line is not tagged in a usable standard concept.
  - JPM has no capex concept (banks do not report it this way).
  - Berkshire has no SBC concept.
  - AVGO, GOOGL, TSLA and MSFT D&A use `Depreciation`; AVGO's large intangibles amortisation is in a separate column.
  - NVDA's latest quarter (Oct 2026) is not yet in the SEC feed.
  - The concept used per company and field is in `row6_concepts_used_per_company.csv`.
- **Row 7**:
  - Constituent changes are inferred from IVW holdings: 7 Nov 2025 against 31 Dec 2025 (Dec 2025 reconstitution: 34 added, 111 removed, 216 to 139 names) and 31 Dec 2025 against 25 Nov 2026 (intra-year: S&P 500 adds and deletes).
  - BK to BNY is a ticker change, not a membership change.
  - Names held in both IVW and IVE are "split" names.
  - The official S&P DJI pro-forma constituent files are subscription-only.
- **Row 8**:
  - The Bloomberg/LSEG monthly breadth history was not reachable.
  - Yardeni has no Growth/Value revisions chart on the style page (all 25 figures checked).
  - The breadth snapshot uses FY+1 revisions.
  - The monthly proxy is month-on-month % change in forward EPS. It is not breadth. It includes the natural roll of the 12-month window and December reconstitution breaks. Nov 2026 uses method (b).
- **Row 9**:
  - `ntm_eps_*` is a time-weighted blend of FY0 and FY1 consensus, an approximation.
  - Yahoo returned nothing for BK, DAY, FOX and HOLX.
  - The end-2025 snapshot does not exist in any free source I could reach; the 90-days-ago values only go back to late Aug 2026.
- **Row 10**: FRED's ICE BofA series only start 28 Nov 2023 (3-year licence window). A tech/hyperscaler spread needs Bloomberg/ICE/LSEG, or bond-level TRACE prices for a basket (e.g. MSFT, AAPL, AMZN, GOOGL, META, ORCL bonds) against Treasuries. I did not build that.

## Big finding for the study

S&P DJI is changing the style factor framework at the **21 Dec 2026** reconstitution:
- **Growth**: drops 12-month price momentum.
- **Value**: adds intangibles-adjusted book-to-price, a blended trailing/forward E/P, and FCF/P.

Pro-forma files are due **4 Dec 2026**. Expect a Growth/Value membership shock and an EPS/P-E level break in both series that week.

## Files

- `row1_*`: P/E (daily digitised 1995 to now; weekly 1995 to now; weekly 2024 to now with Growth/Value ratio).
- `row2_*`: forward EPS, both methods.
- `row3_*`: S&P DJI daily levels.
- `row4_*`: FRED real and nominal 10y, plus a computed breakeven column.
- `row5_*`: full IVW/IVE holdings on each date, plus the top-15 table.
- `row6_*`: quarterly cash flows and concept map.
- `row7_*`: events CSV, membership changes, and the two S&P DJI PDFs.
- `row8_*`: breadth snapshot and monthly proxy.
- `row9_*`: constituent consensus snapshot.
- `row10_*`: fallback spreads.
- `scripts/`: digitising, SEC and estimate code.

## Sources

- Yardeni Research charts, Growth vs Value page: https://yardeni.com/charts/us-stock-market/stock-market-investment-styles/growth-vs-value (images served by LSEG Datastream)
- S&P DJI index pages (S&P 500 Growth, S&P 500 Value) and announcements: https://www.spglobal.com/spdji/en/indices/equity/sp-500-growth/
- iShares IVW: https://www.ishares.com/us/products/239725/ishares-sp-500-growth-etf ; IVE product id 239728
- Wayback Machine capture of the IVW holdings file, 10 Nov 2025
- FRED: https://fred.stlouisfed.org
- SEC EDGAR XBRL API: https://data.sec.gov/api/xbrl/companyfacts/
- Yahoo Finance quoteSummary (earningsTrend)
- S&P DJI Indexology blog, 15 Jan 2026: https://www.indexologyblog.com/2026/01/15/inside-the-annual-style-indices-rebalance-methodology-process-and-outcomes/
