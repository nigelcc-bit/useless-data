# The Blue Tsunami Flush: 5 Nov 2026 AI selloff post-mortem (6 Nov 2026)

Deliverable: `Blue_Tsunami_Flush_AI_Selloff_6Nov2026.docx` / `.pdf` (21pp, 12 exhibits) + `ai_selloff_cross_section_5Nov2026.csv` + `sp500_4pct_days_event_table.csv`. Input: uploaded X compilation `tech_selloff_analyst_takes_nov2026.md` (100 posts).

## Data
- Verified: IBKR daily bars 26 Oct to 5 Nov and monthly bars (52w highs, Dec-25 close) for 27 instruments; S&P 500 daily 1928-2019 (fja05680 GitHub mirror); press for index closes (Yahoo, CNBC, NBC, AP, Reuters, Bloomberg).
- Not available: Financial Datasets had not posted 5 Nov and returns "Unauthorized" on bursts (keep to a few calls at a time); IBKR limit is 10 req/s and 30/min (batches of 9 with 21s pauses work). Yahoo/Stooq/FRED blocked from sandbox; raw.githubusercontent.com works.
- Starred (single source or recall): Abbott 21 Sep Texas permit pause, $500M DC loan auction (bids 19 Nov), CRWV notes ~76c and CDS 1,168bp (Oct), Marvell to buy Lumentum in stock, JPM levels (7,500-7,600 / 7,200 / 7,000; VIX 35), Dec hike odds ~69%, post-2019 event-study episodes.

## Tape (5 Nov)
Nasdaq Comp -5.52% (24,315.00; -11.9% from 6 Oct record), NDX -6.4%, S&P -4.36% (7,353.73), Dow -1,833.06 (-3.44%), RUT -4.45%, SOX -12.3% (~-38% from June), VIX 28.18 (+69.7%, from 16.61). IBKR: SPY -4.4%, QQQ -6.5%, SMH -11.2%, SOXX -12.1% (press -12.8%).
SOXX 28 Oct to 4 Nov -13.7% (30 Oct alone -8.2% on Intel guide + Amazon capex), to 5 Nov -24.2%; 53% of the log decline preceded 5 Nov. SOXX -39.7% from 52w intraday high; SPY -6.2%; QQQ -15.2%.

## Cross-section (N=23 single names, 4 Nov to 5 Nov close)
- Hyperscalers EW -3.0% (AMZN -2.2, GOOGL -2.2, MSFT -3.6, META -4.0) = the four smallest losers. Suppliers EW (N=16) -12.9%. Semis -14.0 (N=7), optics/network -13.8 (4), power/cooling -10.8 (2), neocloud -10.6 (3), non-AI -8.7 (3).
- Six sessions (28 Oct to 5 Nov): hyperscalers -2.8%, suppliers -26.5%.
- Worst: LITE -18.7, MU -17.5, AMD -17.3, MRVL -16.4, LRCX -16.4, NBIS -14.9, VRT -14.0.
- Spearman vs 5 Nov return: YTD-to-4-Nov -0.69 (p<0.001; AI-only -0.76); prior 5-session return +0.59 (p=0.003; AI-only +0.73); distance from 52w high +0.45. Crowding/momentum sort, not valuation.
- 21 of 23 names >20% below 52w high (exceptions MSFT -4%, AMZN -9%).
- Book as listed Oct 2026, equal weight assumed: 10 AI names -14.6% on 5 Nov, -29.6% over six sessions; all 13 names avg -46.7% from 52w high, +34.5% YTD EW. All AI names are supplier-side (no builder exposure).

## Event study (S&P 500, 1928-2019; -4% days, N=151)
- 125 of 151 are cluster days (another within 126 sessions). First shocks: 26.
- First shock within 5% of 252d high (2026 condition), N=9 (1929-03, 1936-09, 1948-11, 1950-06, 1955-09, 1986-09, 1989-10, 1997-10, 2018-02): +21d median +1.8% (7/9), +63d +6.7% (8/9), +252d +3.1% (7/9); worst further 63d drawdown median -2.2%, 0/9 beyond -10%.
- Within 10%, N=15: +63d 13/15, 1/15 beyond -10% (3 Oct 1929, -39%).
- First shock >10% below high, N=11: +21d 3/11 positive, 5/11 fell a further 10%+.
- Any-day baseline: +63d +2.4% (63%), +252d +8.9% (69%).
- Outside dataset (recall*): 27 Feb 2020 (~-25% further), 3 Apr 2025 (~-8% further, ~+15% a quarter later). Closest structural analogue: 14 Apr 2000 (+11% in 63d, -12% in 252d).

## Policy
Reuters: 40 of 41 ballot measures against data centers (only ~10 binding, CS Monitor). Goldman: 45% of planned US capacity in states likely to restrict, expects temporary. Texas 25-30% of pipeline (GS/Wells/SemiAnalysis). SemiAnalysis: ~30 GW of 62.2 GW 2028 adds in pause-candidate states (ceiling); 2027 largely locked; Sept: 1.5 of ~20 GW under local curbs actually delayed. Goldman May 2026: only 50-60% of planned capacity on schedule anyway. Wells Fargo: each 10% cut to planned Texas capacity = -1.6% AI infra spend (total freeze ~-16% by linear extrapolation, judgment).

## Compilation audit
File summary said 28 Bull / 35 Bear / 37 Hold; labels actually sum to 19 / 35 / 46. Unique sources (N=82): 14 / 30 / 38. Unique opinion holders (N=66): 12 / 25 / 29. Named strategists and desks (N=16): 1 / 10 / 5. "47 of 50 ballot measures" not supported (40 of 41).

## Seven calls
1. Election = accelerant not origin. 2. Builder-supplier seesaw returned (capex-volume repricing, unlike October's correlated de-grossing). 3. Sort on crowding, not valuation. 4. Policy exposure large, measured loss small, price ahead of both; funding (CRWV credit, loan auction) is the second channel. 5. First-shock base rate favours an index bounce within a quarter, weak 12-month record. 6. S&P has paid <1/3 of median midterm fee (-6.2% vs -19.6%), semis double. 7. Feed not capitulating; tally miscounted.

## Monitoring flips
Leadership on rebound days (suppliers >2x builders over first five up days = flush; builders lead = thesis); supplier-hyperscaler 21d corr >0.8 rising together vs <0.4; SOXX 5 Nov low 130.74 intraday / 131.90 close (split-adjusted); CRWV 2032 notes >85 vs <70; loan auction 19 Nov clears >90 vs <80; Texas scope (grandfathering vs service guarantees vacated); S&P reclaim 7,500-7,600 vs close below ~6,618; VIX <22 vs >35; Dec FOMC.

## Weaknesses / next work
One session, 23 hand-picked names, overlapping predictors; event study ends 2019 and is for the S&P, not Nasdaq/SOX; conditioning rule chosen post hoc; correlated sell-side capacity estimates; equal-weight book assumption; 52w highs from monthly bars not checked for corporate actions (GLW, ORCL flagged). Next: pull Nasdaq Comp and SOX daily history via desktop browser and re-run the first-shock study on the sector including 2020 and 2025; compute supplier and hyperscaler daily betas through November.
