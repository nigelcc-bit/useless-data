# Panel QC: development sample

Built by `src/build_panel.py` from `data/raw/` with a read filter 2000-01-01 <= Date <= 2025-12-31 (no 2026 rows loaded). SPY excluded.

- Tickers: **500**; skipped (no development-sample rows): **3** FDXF, HONA, VYLR
- Rows (with y): **2,849,486**; rows with both x and y (analysis sample): **2,831,321**
- Dates: **6,534** (2000-01-03 to 2025-12-23)
- Names per date (rows with y): min **343**, median **442**, max **500**
- Names per date (analysis sample): min **334**, median **440**, max **500**
- Share of NaN x (rows with y): **0.64%**
- Adjustment-event rows (|Adj Close/Close ratio change| > 0.5%), x set to NaN: **17,680**

## Top 10 |gap| (raw x = ln(Open_t / Close_t-1), after NaN-ing adjustment events)

| date | ticker | x_raw | gap |
|---|---|---|---|
| 2008-09-16 | AIG | -0.9451 | -61.1% |
| 2002-07-02 | PWR | -0.8017 | -55.1% |
| 2003-03-31 | REGN | -0.6937 | -50.0% |
| 2019-01-14 | PCG | -0.6470 | -47.6% |
| 2000-09-29 | AAPL | -0.6408 | -47.3% |
| 2014-05-16 | TKO | -0.6361 | -47.1% |
| 2009-01-20 | STT | -0.6030 | -45.3% |
| 2025-08-26 | ECHO | +0.5938 | +81.1% |
| 2001-09-26 | AES | -0.5857 | -44.3% |
| 2000-03-06 | WSM | -0.5821 | -44.1% |
