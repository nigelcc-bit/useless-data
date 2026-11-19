"""P1 live check (not a test): the 9 Dec 2026 FOMC decision.

Run only after a manual refresh of data/raw/ that includes 2026-12-09 in the ACM file.
Prints one-day dDGS2, dDGS10, dACMTP10 and dACMRNY10 (bp) and compares dACMTP10 with
the fitted H5a line (out/h5a_fit.json). One observation, no inference.

    python -m src.live_p1
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from src import load
from src.common import BP, OUT, log_run

DAY = pd.Timestamp("2026-12-09")


def one_day(s: pd.Series, d: pd.Timestamp) -> tuple[float, str]:
    s = s.dropna()
    if d not in s.index:
        raise KeyError(d)
    i = s.index.get_loc(d)
    return float((s.iloc[i] - s.iloc[i - 1]) * BP), str(s.index[i - 1].date())


def main() -> int:
    a, f = load.acm(), load.fred()
    if DAY not in a["ACMTP10"].dropna().index:
        print(f"ACM has not published {DAY.date()} yet (last date {a.index.max().date()}). Nothing to do.")
        return 1
    out = {}
    for k, s in [("d_dgs2", f["DGS2"]), ("d_dgs10", f["DGS10"]),
                 ("d_acm_tp10", a["ACMTP10"]), ("d_acm_rny10", a["ACMRNY10"])]:
        out[k], out[f"prev_{k[2:]}"] = one_day(s, DAY)
    fit = json.loads((OUT / "h5a_fit.json").read_text())["H5a"]
    out["h5a_fitted_d_acm_tp10"] = fit["alpha"] + fit["beta"] * out["d_dgs2"]
    out["h5a_residual"] = out["d_acm_tp10"] - out["h5a_fitted_d_acm_tp10"]
    for k, v in out.items():
        print(f"{k:>24}: {v}")
    print("One observation, no inference.")
    log_run("src/live_p1.py", {"day": DAY}, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
