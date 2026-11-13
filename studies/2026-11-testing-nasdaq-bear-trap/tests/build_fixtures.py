"""Parse Appendix B (NDX, 43 events) and Appendix C (SPX, 86 events) of the
Study 1 report into CSV fixtures used by test_engine.py.

    python tests/build_fixtures.py
"""
from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "Study1_Bear_Trap_Full_Report.md"
OUT = ROOT / "tests" / "fixtures"

COLS = ["n", "break_date", "level", "break_vs_level", "sweep_vs_level", "dd_at_break",
        "reclaimed", "entry_date", "retest", "r20", "r60", "r120", "worst60", "regained_high"]


def _pct(x):
    x = x.strip()
    return float(x.replace("%", "").replace("+", "")) / 100 if x not in ("n/a", "") else None


def _yn(x):
    x = x.strip()
    return {"Yes": True, "No": False}.get(x)


def parse(section_title: str) -> pd.DataFrame:
    text = REPORT.read_text()
    start = text.index(section_title)
    rows = []
    for line in text[start:].splitlines()[1:]:
        if line.startswith("### ") or line.startswith("## "):
            if rows:
                break
            continue
        m = re.match(r"^\|\s*(\d+)\s*\|", line)
        if not m:
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        rows.append(dict(
            n=int(c[0]), break_date=pd.to_datetime(c[1], format="%d %b %Y"),
            level=float(c[2].replace(",", "")), break_vs_level=_pct(c[3]), sweep_vs_level=_pct(c[4]),
            dd_at_break=_pct(c[5]), reclaimed=_yn(c[6]),
            entry_date=pd.to_datetime(c[7].replace("(K-day mark)", "").strip(), format="%d %b %Y"),
            retest=_yn(c[8]), r20=_pct(c[9]), r60=_pct(c[10]), r120=_pct(c[11]),
            worst60=_pct(c[12]), regained_high=_yn(c[13]),
        ))
    return pd.DataFrame(rows, columns=COLS)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    b = parse("### Appendix B: Nasdaq 100")
    c = parse("### Appendix C: S&P 500")
    assert len(b) == 43, len(b)
    assert len(c) == 86, len(c)
    b.to_csv(OUT / "expected_ndx_events.csv", index=False)
    c.to_csv(OUT / "expected_spx_events.csv", index=False)
    print(f"wrote {len(b)} NDX and {len(c)} SPX expected events")
