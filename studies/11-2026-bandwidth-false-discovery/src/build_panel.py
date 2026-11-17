"""Build the development-sample panel (date, ticker) of x and y, rank-transformed.

Development sample only: each raw Parquet file is read with a row filter
Date <= 2025-12-31, so 2026 rows never enter memory (CLAUDE.md holdout rule).

Definitions (PREREG.md, Variables):
- x = ln(Open_t / Close_{t-1}) from yfinance Open and Close. These are not
  dividend-adjusted but ARE split-adjusted by yfinance (checked: AAPL Close on
  2020-08-28, before its 4:1 split, is 124.81), so splits do not create gaps.
  x is set to NaN where the Adj Close / Close ratio changes by more than 0.5%
  day on day (dividend or other adjustment event); and on each ticker's first row.
- y = ln(AdjClose_{t+5} / AdjClose_t), t+5 = the ticker's 5th next trading row,
  minus the equal-weight mean of y over all tickers with y on that date.
  Rows whose t+5 falls after 2025-12-31 have no y (filtered out on read) and
  are dropped.
- Universe: S&P 500 constituents in data/raw/ excluding SPY (an ETF, kept as a
  benchmark, not a cross-sectional name).
- Normal scores: within each date, over rows with both x and y, rank/(n+1) then
  the inverse normal CDF (average ranks for ties). Demeaning y does not change
  its within-date ranks; the demeaned raw y is kept for reference.

Writes data/panel_dev.parquet and out/panel_qc.md. Usage (study directory):
    python3 -m src.build_panel
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from .runlog import log_run

STUDY_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = STUDY_DIR / "data" / "raw"
PANEL = STUDY_DIR / "data" / "panel_dev.parquet"
QC = STUDY_DIR / "out" / "panel_qc.md"
DEV_START = pd.Timestamp("2000-01-01")
DEV_END = pd.Timestamp("2025-12-31")
ADJ_JUMP = 0.005
HORIZON = 5
EXCLUDE = {"SPY"}


def load_dev(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path, columns=["Open", "Close", "Adj Close"],
                         filters=[("Date", ">=", DEV_START), ("Date", "<=", DEV_END)])
    assert df.empty or df.index.max() <= DEV_END, f"{path.name}: holdout row loaded"
    return df.sort_index()


def ticker_rows(t: str, df: pd.DataFrame) -> pd.DataFrame:
    ratio = df["Adj Close"] / df["Close"]
    adj_event = (ratio / ratio.shift(1) - 1).abs() > ADJ_JUMP
    x = np.log(df["Open"] / df["Close"].shift(1))
    x[adj_event | x.isna()] = np.nan
    y_raw = np.log(df["Adj Close"].shift(-HORIZON) / df["Adj Close"])
    return pd.DataFrame({"date": df.index, "ticker": t, "x_raw": x.values,
                         "y_raw": y_raw.values, "adj_event": adj_event.values})


def normal_scores(v: pd.Series, by: pd.Series) -> pd.Series:
    r = v.groupby(by).rank(method="average")
    n = v.groupby(by).transform("count")
    return pd.Series(norm.ppf(r / (n + 1)), index=v.index)


def main() -> None:
    files = sorted(p for p in RAW_DIR.glob("*.parquet") if p.stem not in EXCLUDE)
    parts, no_dev = [], []
    for p in files:
        df = load_dev(p)
        if len(df) <= HORIZON:  # listed in 2026 (or too short): no development rows
            no_dev.append(p.stem)
            continue
        parts.append(ticker_rows(p.stem, df))
    panel = pd.concat(parts, ignore_index=True)
    n_adj_events = int(panel["adj_event"].sum())

    panel = panel[panel["y_raw"].notna()].copy()            # drops last 5 rows per ticker
    panel["y_dm"] = panel["y_raw"] - panel.groupby("date")["y_raw"].transform("mean")
    share_nan_x = float(panel["x_raw"].isna().mean())

    both = panel["x_raw"].notna()
    panel["x"] = np.nan
    panel["y"] = np.nan
    sub = panel[both]
    panel.loc[both, "x"] = normal_scores(sub["x_raw"], sub["date"]).values
    panel.loc[both, "y"] = normal_scores(sub["y_dm"], sub["date"]).values
    panel = panel.sort_values(["date", "ticker"], kind="stable").reset_index(drop=True)
    panel = panel[["date", "ticker", "x_raw", "y_raw", "y_dm", "adj_event", "x", "y"]]
    PANEL.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(PANEL, index=False)

    names = panel.groupby("date")["ticker"].size()
    names_xy = panel[panel["x"].notna()].groupby("date").size()
    top = panel.loc[panel["x_raw"].notna()].assign(abs_gap=lambda d: d["x_raw"].abs()) \
        .nlargest(10, "abs_gap")[["date", "ticker", "x_raw"]]
    top["gap_pct"] = np.expm1(top["x_raw"])
    lines = [
        "# Panel QC: development sample",
        "",
        "Built by `src/build_panel.py` from `data/raw/` with a read filter "
        f"{DEV_START.date()} <= Date <= {DEV_END.date()} (no 2026 rows loaded). SPY excluded.",
        "",
        f"- Tickers: **{panel['ticker'].nunique()}**; skipped (no development-sample rows): "
        f"**{len(no_dev)}** {', '.join(no_dev)}",
        f"- Rows (with y): **{len(panel):,}**; rows with both x and y (analysis sample): "
        f"**{int(panel['x'].notna().sum()):,}**",
        f"- Dates: **{panel['date'].nunique():,}** ({panel['date'].min().date()} to {panel['date'].max().date()})",
        f"- Names per date (rows with y): min **{names.min()}**, median **{int(names.median())}**, "
        f"max **{names.max()}**",
        f"- Names per date (analysis sample): min **{names_xy.min()}**, median **{int(names_xy.median())}**, "
        f"max **{names_xy.max()}**",
        f"- Share of NaN x (rows with y): **{share_nan_x:.2%}**",
        f"- Adjustment-event rows (|Adj Close/Close ratio change| > {ADJ_JUMP:.1%}), x set to NaN: "
        f"**{n_adj_events:,}**",
        "",
        "## Top 10 |gap| (raw x = ln(Open_t / Close_t-1), after NaN-ing adjustment events)",
        "",
        "| date | ticker | x_raw | gap |",
        "|---|---|---|---|",
    ]
    lines += [f"| {r.date.date()} | {r.ticker} | {r.x_raw:+.4f} | {r.gap_pct:+.1%} |" for r in top.itertuples()]
    QC.write_text("\n".join(lines) + "\n")

    log_run("src/build_panel.py",
            {"dev_start": str(DEV_START.date()), "dev_end": str(DEV_END.date()), "adj_jump": ADJ_JUMP,
             "horizon": HORIZON, "exclude": sorted(EXCLUDE)}, "",
            {"rows": len(panel), "rows_xy": int(panel["x"].notna().sum()),
             "dates": int(panel["date"].nunique()), "tickers": int(panel["ticker"].nunique()),
             "share_nan_x": round(share_nan_x, 5), "adj_events": n_adj_events, "skipped_no_dev": no_dev})
    print(QC.read_text())


if __name__ == "__main__":
    main()
