# Data manifest

Files in `data/raw/` are kept exactly as pulled and are never edited. Rows exclude the header.

| File | Source | Contents | Coverage | Rows | SHA-256 | Pulled (UTC) |
|---|---|---|---|---|---|---|
| `fred_daily.csv` | FRED `https://fred.stlouisfed.org/graph/fredgraph.csv` (18 series merged on date) | THREEFYTP2, THREEFYTP5, THREEFYTP10, THREEFY2, THREEFY10, DGS3MO, DGS2, DGS5, DGS10, DGS30, T10YIE, T5YIFR, DFII5, DFII10, DCOILWTICO, DFEDTARU, DFEDTARL, DFF. Business days; blank where a series was not published. | 1990-01-01 to 2026-11-19 (first row 1990-01-01 has DFF only; the other series start 1990-01-02 or later) | 9,624 | `d0ea085ae9b135f9d56b47d98a3e76759e559579dc801a3633414fa0b7a427b4` | 2026-11-19, in a browser |
| `acm_daily.csv` | NY Fed `ACMTermPremium.xls`, sheet "ACM Daily" | ACMY01-10 (fitted zero yields), ACMTP01-10 (term premium), ACMRNY01-10 (risk-neutral yield). Values written to 10 significant figures. | 1990-01-02 to 2026-11-17 | 9,206 | `b480474168c466aa01cd40759b25b65e04324697b83d211edcb2109f4012cd4d` | 2026-11-19, in a browser |
| `fred_target_changes.csv` | FRED `fredgraph.csv?id=DFEDTAR` (to 2008-12-15) and `?id=DFEDTARU` (from 2008-12-16) | Columns `series,date,value`. Only the first observation of each series and rows where the value changes (lossless for a step series). Built by `src/build_raw.py`. | 1982-09-27 to 2026-11-19 (last change 2026-09-17, 3.75 to 4.00) | 186 | `f90660634669105378e79fdb4110ab8767a6be6cb04c0a99f7a6d728eb7136bf` | 2026-11-19, from the workspace |
| `fomc_dates.csv` | `https://www.federalreserve.gov/monetarypolicy/fomchistoricalYYYY.htm` (1990-2020) and `https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm` (2021-2026) | Columns `date,kind,flag,label,provenance,note`. Meeting, call and notation-vote end dates (second day of two-day meetings). `kind` = meeting, call, notation; `flag` = scheduled, unscheduled, cancelled, excluded. Built by `src/build_raw.py`. | 1990-02-07 to 2026-12-09 | 369 | `8fef9c8f83e4d575e632023f45758ad3f3443eb92f30cd9804784d5a5b3b46e5` | 2026-11-19, from the workspace |

## Source download checksums (inputs to `src/build_raw.py`)

| Download | SHA-256 |
|---|---|
| `DFEDTAR.csv` | `323b6d9fb014cdd8b39eab02025bb37111e9497c75fdd24ea1731ed3f360376c` |
| `DFEDTARU.csv` | `ef2bf341a8d6033dbde27771f2ac2300cfa35fd32ce317e72d4e294237a5cf1f` |

The 32 Fed HTML pages are not stored; the parsed result is `fomc_dates.csv`.

## Notes on `fomc_dates.csv`

- **Cross-month headings** ("Jan/Feb 31-1", "Oct/Nov 31-1", "July 31-August 1" and similar) are dated to the last month and last day named. This covers 2017-02-01, 2017-11-01, 2018-08-01, 2023-02-01 and 2023-11-01, as well as other cross-month meetings. Each such row says so in `provenance`.
- **2003-09-15** is flagged `excluded` by hand: the 2003 page lists both 15 and 16 Sept, and 16 Sept is the announcement day.
- **2020-03-18** is `cancelled`, as the page labels it.
- **2013-10-16, 2014-03-04 and 2019-10-04** have headings marked only "(unscheduled)". They are classified as unscheduled meetings, as recorded in `note`.
- Conference calls are `kind=call`, `flag=unscheduled`. Notation votes are `kind=notation`, `flag=excluded`.
- **Gate:** scheduled meetings from 1994-02-04 number 8 per year, except 7 in 2020; 2026 includes 2026-12-09 (`tests/test_data.py::test_fomc_gate`).
