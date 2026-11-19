"""Build the two small raw files from pages saved off the public sources.

Run once at pull time; the outputs in data/raw/ are then frozen and never edited.

    python -m src.build_raw <download_dir>

<download_dir> must hold DFEDTAR.csv, DFEDTARU.csv (FRED fredgraph.csv),
hYYYY.htm for 1990-2020 (fomchistoricalYYYY.htm) and cal.htm (fomccalendars.htm).
"""
from __future__ import annotations

import csv
import re
import sys
from datetime import date
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], 1)}
ABBR = {k[:3]: v for k, v in MONTHS.items()}


def month_num(tok: str) -> int:
    t = tok.strip().lower()
    return MONTHS.get(t) or ABBR[t[:3]]


def target_changes(dl: Path) -> list[tuple[str, str, str]]:
    rows = []
    for s in ["DFEDTAR", "DFEDTARU"]:
        prev = None
        with open(dl / f"{s}.csv") as f:
            for r in csv.DictReader(f):
                v = r[s].strip()
                if v in ("", "."):
                    continue
                if prev is None or float(v) != prev:
                    rows.append((s, r["observation_date"], v))
                    prev = float(v)
    return rows


def end_date(year: int, month_txt: str, day_txt: str) -> tuple[date, bool]:
    """Return the end date of a meeting and whether it crossed a month."""
    days = [int(x) for x in re.findall(r"\d+", day_txt)]
    months = [m for m in re.split(r"[/\-\s]+", month_txt) if m.strip()]
    cross = len(months) > 1
    m = month_num(months[-1])
    return date(year, m, days[-1]), cross


def classify(label: str) -> tuple[str, str]:
    lo = label.lower()
    if "notation" in lo:
        return "notation", "excluded"
    if "conference call" in lo:
        return "call", "unscheduled"
    if "cancel" in lo:
        return "meeting", "cancelled"
    if "unscheduled" in lo:
        return "meeting", "unscheduled"
    return "meeting", "scheduled"


def parse_hist(dl: Path, year: int) -> list[dict]:
    html = (dl / f"h{year}.htm").read_text(encoding="utf-8", errors="replace")
    out = []
    for h in re.findall(r"<h[2-6][^>]*>([^<]*)</h[2-6]>", html):
        label = re.sub(r"\s+", " ", h).strip()
        if not label.endswith(f"- {year}"):
            continue
        body = label[: -len(f"- {year}")].strip()
        mtoks = re.findall(r"[A-Za-z]+", body.split("(")[0].replace("Meeting", "").replace("Conference Call", ""))
        dtoks = re.findall(r"\d+", body.split("(")[0])
        if not mtoks or not dtoks:
            raise ValueError(f"cannot parse heading: {label!r}")
        # end date = last month name and last day number (handles "Jan/Feb 31-1")
        d, cross = date(year, month_num(mtoks[-1]), int(dtoks[-1])), len(mtoks) > 1
        kind, flag = classify(label)
        note = []
        if "(unscheduled)" in label and "Meeting" not in label:
            note.append("heading says only '(unscheduled)', not 'Meeting' or 'Conference Call'; classified as an unscheduled meeting")
        out.append(dict(date=d.isoformat(), kind=kind, flag=flag, label=label,
                        provenance=f"fomchistorical{year}.htm" + (" (cross-month heading: end month and day taken from last month and last day)" if cross else ""),
                        note="; ".join(note)))
    return out


def parse_cal(dl: Path) -> list[dict]:
    html = (dl / "cal.htm").read_text(encoding="utf-8", errors="replace")
    parts = re.split(r'<a id="\d+">(\d{4}) FOMC Meetings</a>', html)
    out = []
    for i in range(1, len(parts), 2):
        year, chunk = int(parts[i]), parts[i + 1]
        if year < 2021 or year > 2026:
            continue
        pairs = re.findall(
            r'fomc-meeting__month[^>]*>\s*<strong>([^<]+)</strong>.*?fomc-meeting__date[^>]*>([^<]+)<',
            chunk, flags=re.S)
        for mtxt, dtxt in pairs:
            mtxt, dtxt = mtxt.strip(), re.sub(r"\s+", " ", dtxt).strip()
            d, cross = end_date(year, mtxt, re.sub(r"\(.*?\)", "", dtxt))
            low = dtxt.lower()
            if "notation" in low:
                kind, flag = "notation", "excluded"
            elif "unscheduled" in low:
                kind, flag = "meeting", "unscheduled"
            elif "cancel" in low:
                kind, flag = "meeting", "cancelled"
            else:
                kind, flag = "meeting", "scheduled"
            out.append(dict(date=d.isoformat(), kind=kind, flag=flag, label=f"{mtxt} {dtxt} - {year}",
                            provenance="fomccalendars.htm" + (" (cross-month heading: end month and day taken from last month and last day)" if cross else ""),
                            note="* = Summary of Economic Projections" if "*" in dtxt else ""))
    return out


MANUAL = {
    # date: (flag, note)
    "2003-09-15": ("excluded", "2003 page lists both 15 and 16 Sept; 16 Sept is the announcement day (manual fix)"),
}


def fomc_dates(dl: Path) -> list[dict]:
    rows = []
    for y in range(1990, 2021):
        rows += parse_hist(dl, y)
    rows += parse_cal(dl)
    for r in rows:
        if r["date"] in MANUAL:
            r["flag"], extra = MANUAL[r["date"]]
            r["provenance"] += "; manual flag"
            r["note"] = "; ".join(x for x in [r["note"], extra] if x)
    rows.sort(key=lambda r: (r["date"], r["kind"]))
    return rows


def main(dl: str) -> None:
    dl = Path(dl)
    with open(RAW / "fred_target_changes.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["series", "date", "value"])
        w.writerows(target_changes(dl))
    cols = ["date", "kind", "flag", "label", "provenance", "note"]
    with open(RAW / "fomc_dates.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(fomc_dates(dl))


if __name__ == "__main__":
    main(sys.argv[1])
