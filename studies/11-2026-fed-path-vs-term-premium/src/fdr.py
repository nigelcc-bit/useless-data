"""Benjamini-Hochberg at q = 0.10 over exactly {H3, H4a, H4b, H5a}. Run once, at the end.

Writes bh_p and the final status back into out/tests_run.csv (latest row per test_id),
and every claim that fails into out/killed_hypotheses.md.

    python -m src.fdr
"""
from __future__ import annotations

import csv
import datetime as dt
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from core.stats.fdr import benjamini_hochberg  # noqa: E402

from src.common import OUT, TEST_FIELDS, TESTS_CSV, log_run  # noqa: E402

FAMILY = ["H3", "H4a", "H4b", "H5a"]
Q = 0.10
KILLED_MD = OUT / "killed_hypotheses.md"

CLAIMS = {
    "H1": "Term premium accounts for more than half of dy10, 2025-12-31 to 2026-11-13 (ACM and KW)",
    "H3": "2026 R2 of dDGS10 on dDGS2 below the 10th percentile of 1990-2025 yearly R2",
    "H4a": "2026 weekly dACMTP10 has a positive slope on dln WTI",
    "H4b": "Oil sensitivity of the TP is larger in 2026 than in 1990-2025",
    "H5a": "On FOMC announcement days dACMTP10 has a non-zero slope on dDGS2 (1994-2025)",
}


def main() -> pd.DataFrame:
    with TESTS_CSV.open() as f:
        rows = list(csv.DictReader(f))
    latest = {}
    for i, r in enumerate(rows):
        latest[r["test_id"]] = i
    missing = [t for t in FAMILY if t not in latest]
    if missing:
        raise SystemExit(f"FDR family incomplete, missing {missing}; run the H-scripts first")

    p = pd.Series({t: float(rows[latest[t]]["raw_p_num"]) for t in FAMILY})
    bh = benjamini_hochberg(p, q=Q)

    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    kills = []
    for t in FAMILY:
        r = rows[latest[t]]
        bh_p = float(bh.loc[t, "bh_p"])
        r["bh_p"] = f"{bh_p:.4g}"
        survives_bh = bool(bh.loc[t, "reject_q"])
        raw = float(r["raw_p_num"])
        if t == "H3":
            extra_ok, extra_txt = raw <= 0.10, f"rank p {raw:.4f} {'<=' if raw <= 0.10 else '>'} 0.10"
        elif t in ("H4a", "H4b"):
            h4 = pd.read_csv(OUT / "h4_oil.csv").set_index("test_id")
            tval = float(h4.loc[t, "t"])
            extra_ok, extra_txt = tval >= 2, f"t {tval:.2f} {'>=' if tval >= 2 else '<'} 2"
        else:
            extra_ok, extra_txt = True, ""
        if extra_ok and survives_bh:
            r["status"] = f"supported (survives BH q={Q})"
        else:
            why = []
            if not extra_ok:
                why.append(extra_txt)
            if not survives_bh:
                why.append(f"BH p {bh_p:.4f} > {Q}")
            r["status"] = "killed: " + "; ".join(why)
            kills.append((t, CLAIMS[t], "; ".join(why) + f" (raw p {raw:.4f})", today))

    # H1 is a decision rule; a claim that is not supported is logged as killed.
    if "H1" in latest:
        h1 = rows[latest["H1"]]
        if h1["status"] != "term-premium driven":
            kills.insert(0, ("H1", CLAIMS["H1"], f"decision: {h1['status']}; {h1['effect']}", today))

    with TESTS_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TEST_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    lines = ["# Killed hypotheses", "", "| ID | Claim | Killed by | Date |", "|---|---|---|---|"]
    lines += [f"| {k} | {c} | {why} | {d} |" for k, c, why, d in kills]
    KILLED_MD.write_text("\n".join(lines) + "\n")

    out = bh.assign(status=[rows[latest[t]]["status"] for t in FAMILY])
    log_run("src/fdr.py", {"family": FAMILY, "q": Q}, {t: {"raw_p": out.loc[t, "raw_p"], "bh_p": out.loc[t, "bh_p"],
                                                              "status": out.loc[t, "status"]} for t in FAMILY})
    print(out.to_string())
    print(KILLED_MD.read_text())
    return out


if __name__ == "__main__":
    main()
