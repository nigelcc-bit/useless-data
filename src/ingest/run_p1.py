"""P1 orchestrator: ingest → adjust → survivorship → D5/D7 → SPEC_LITERAL gate.

If any fixture fails: STOP. Do not adjust targets/windows/names.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import requests
import yaml

from src.adjust.splits import (
    audit_large_moves,
    flag_large_moves,
    sync_corporate_actions_from_yahoo,
    yahoo_splits_from_raw,
)
from src.config_io import ROOT, episodes, fixtures, universe
from src.gates.p1_spec_literal import run_p1_spec_literal_gate
from src.ingest.fred import fetch_all_fred
from src.ingest.stooq import fetch_stooq
from src.ingest.yahoo import fetch_many
from src.panel_quality import episode_missingness_report
from src.studies.resolve_d5_d7 import build_cross_section, compare_to_targets, summarise

START = "2015-01-01"
END = "2026-11-05"
TODAY = date.today().isoformat()  # machine UTC date for raw folder name


def all_symbols() -> list[str]:
    tickers: list[str] = []
    for layer in universe()["layers"].values():
        tickers.extend(layer["names"].keys())
    # ETFs + indices
    extras = ["SPY", "QQQ", "SOXX", "SMH", "^GSPC", "^IXIC", "^SOX", "^VIX"]
    # unique preserve order
    seen = set()
    out = []
    for t in tickers + extras:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def build_price_frames(ohlcv: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    close = pd.DataFrame({k: v["Close"] for k, v in ohlcv.items()})
    high = pd.DataFrame({k: v["High"] for k, v in ohlcv.items()})
    adj = pd.DataFrame(
        {k: v["Adj Close"] if "Adj Close" in v.columns else v["Close"] for k, v in ohlcv.items()}
    )
    close.index = pd.to_datetime(close.index).normalize()
    high.index = pd.to_datetime(high.index).normalize()
    adj.index = pd.to_datetime(adj.index).normalize()
    return close.sort_index(), high.sort_index(), adj.sort_index()


def stooq_crosscheck(raw_dir: Path, close: pd.DataFrame) -> pd.DataFrame:
    rows = []
    # Stooq is often JS-challenged from this environment — try one probe first.
    probe = fetch_stooq("SPY", raw_dir)
    if probe is None:
        return pd.DataFrame(
            [
                {
                    "symbol": sym,
                    "status": "STOOQ_UNAVAILABLE",
                    "note": "probe SPY failed; skipped remaining",
                }
                for sym in ["SPY", "QQQ", "SOXX", "SMH", "^GSPC", "^IXIC", "^VIX"]
            ]
        )
    for sym in ["SPY", "QQQ", "SOXX", "SMH", "^GSPC", "^IXIC", "^VIX"]:
        sdf = probe if sym == "SPY" else fetch_stooq(sym, raw_dir)
        if sdf is None or "Close" not in sdf.columns:
            rows.append({"symbol": sym, "status": "STOOQ_UNAVAILABLE"})
            continue
        d = pd.Timestamp("2026-11-05")
        if d not in close.index or sym not in close.columns:
            rows.append({"symbol": sym, "status": "YAHOO_MISSING"})
            continue
        if d not in sdf.index:
            rows.append({"symbol": sym, "status": "STOOQ_DATE_MISSING"})
            continue
        y = float(close.loc[d, sym])
        s = float(sdf.loc[d, "Close"])
        rows.append(
            {
                "symbol": sym,
                "yahoo": y,
                "stooq": s,
                "rel_diff": (y - s) / s if s else None,
                "status": "OK" if abs(y - s) / max(abs(s), 1e-9) < 0.02 else "MISMATCH",
            }
        )
    return pd.DataFrame(rows)


def merger_check_mrvl_lite(raw_dir: Path) -> dict:
    """Search public sources for MRVL all-stock deal for LITE ~4 Nov 2026."""
    out = {
        "status": "UNVERIFIED",
        "confirmed": False,
        "sources": [],
        "note": "",
    }
    queries = [
        "https://news.google.com/rss/search?q=Marvell+Lumentum+acquisition+2026&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=MRVL+LITE+all-stock+November+2026&hl=en-US&gl=US&ceid=US:en",
    ]
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ai-selloff-study/0.1)"}
    snippets = []
    for url in queries:
        try:
            r = requests.get(url, headers=headers, timeout=30)
            text = r.text
            (raw_dir / "merger_search_raw.xml").write_text(text[:200000])
            snippets.append(text[:5000])
        except Exception as e:  # noqa: BLE001
            snippets.append(f"ERR {e}")
    blob = "\n".join(snippets).lower()
    keywords = ["lumentum", "marvell", "all-stock", "all stock", "acquire", "acquisition", "to buy"]
    hits = sum(1 for k in keywords if k in blob)
    # Require strong evidence: both company names + acquire language in RSS
    if "lumentum" in blob and "marvell" in blob and (
        "acqui" in blob or "to buy" in blob or "all-stock" in blob or "all stock" in blob
    ):
        # Extract a title-ish line
        out["confirmed"] = True
        out["status"] = "CONFIRMED"
        out["note"] = "RSS hit for Marvell/Lumentum acquisition language; see merger_search_raw.xml"
        out["sources"].append("Google News RSS (cached under data/raw)")
        out["announcement_date"] = "2026-11-04"  # provisional from note; refine if title has date
    else:
        out["status"] = "UNVERIFIED"
        out["confirmed"] = False
        out["note"] = (
            f"No clear RSS confirmation (keyword_hits={hits}). "
            "D4 closed as unverified — no merger dummy applied."
        )
        out["sources"].append("Google News RSS searched; no definitive hit")
    (raw_dir / "merger_check_mrvl_lite.json").write_text(json.dumps(out, indent=2))
    return out


def listing_starts(close: pd.DataFrame) -> pd.Series:
    starts = {}
    for col in close.columns:
        s = close[col].dropna()
        starts[col] = s.index.min() if len(s) else pd.NaT
    return pd.Series(starts)


def glw_orcl_52w(close: pd.DataFrame, high: pd.DataFrame) -> pd.DataFrame:
    end = pd.Timestamp("2026-11-05")
    rows = []
    for t in ("GLW", "ORCL"):
        if t not in close.columns:
            rows.append({"ticker": t, "status": "MISSING"})
            continue
        c = float(close.loc[end, t])
        hi = high[t].loc[:end].dropna().iloc[-252:]
        cl = close[t].loc[:end].dropna().iloc[-252:]
        rows.append(
            {
                "ticker": t,
                "close_2026_11_05": c,
                "52w_high_daily_high": float(hi.max()),
                "52w_high_daily_close": float(cl.max()),
                "dist_vs_daily_high_pct": 100 * (c / float(hi.max()) - 1),
                "dist_vs_daily_close_pct": 100 * (c / float(cl.max()) - 1),
                "status": "OK",
            }
        )
    return pd.DataFrame(rows)


def append_tests_run(rows: list[dict]) -> None:
    path = ROOT / "outputs" / "tests_run.csv"
    existing = pd.read_csv(path) if path.exists() else pd.DataFrame()
    # drop prior P1 rows we're refreshing
    if len(existing):
        existing = existing[~existing["test_id"].astype(str).str.startswith("P1")]
    new = pd.DataFrame(rows)
    out = pd.concat([existing, new], ignore_index=True)
    out.to_csv(path, index=False)


def main() -> int:
    raw_dir = ROOT / "data" / "raw" / TODAY
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed = ROOT / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    exhibits = ROOT / "outputs" / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)

    test_log: list[dict] = []
    symbols = all_symbols()
    print(f"P1 ingest {len(symbols)} symbols → {raw_dir}", flush=True)

    # 1. Yahoo OHLCV
    ohlcv = fetch_many(symbols, START, END, raw_dir)
    # Drop empty downloads
    ohlcv = {k: v for k, v in ohlcv.items() if len(v) > 0}
    missing = sorted(set(symbols) - set(ohlcv))
    if missing:
        print("WARN missing Yahoo symbols:", missing, flush=True)
        (raw_dir / "yahoo_missing.json").write_text(json.dumps(missing))
    close, high, adj = build_price_frames(ohlcv)
    # Prefer Adj Close for return work; keep Close/High for 52w / split flags
    # yfinance/Yahoo Adj Close is split+dividend adjusted — for drawdowns use Close
    # Spec: price series for drawdown; we store both
    prices = pd.concat(
        {"Close": close, "High": high, "AdjClose": adj},
        axis=1,
    )
    # Flatten MultiIndex columns to Close_SPY etc. OR save three frames
    # Simpler: save wide Close as prices.parquet primary + sidecar highs
    close.to_parquet(processed / "prices.parquet")
    high.to_parquet(processed / "highs.parquet")
    adj.to_parquet(processed / "adj_close.parquet")
    print(f"Wrote prices.parquet {close.shape}", flush=True)

    # 2. FRED
    fred = fetch_all_fred(raw_dir)
    fred.to_parquet(processed / "fred.parquet")
    fred.to_csv(raw_dir / "fred_all.csv")
    test_log.append(
        {
            "test_id": "P1_FRED",
            "hypothesis": "meta",
            "description": "FRED BAMLH0A0HYM2 DGS10 FEDFUNDS VIXCLS",
            "status": "PASS" if fred.shape[1] == 4 else "FAIL",
            "raw_p": "",
            "bh_p": "",
            "effect": "",
            "n": len(fred),
            "notes": str(list(fred.columns)),
        }
    )

    # Stooq cross-check (best effort)
    stooq_rep = stooq_crosscheck(raw_dir, close)
    stooq_rep.to_csv(exhibits / "stooq_crosscheck.csv", index=False)
    print(stooq_rep.to_string(index=False), flush=True)

    # 3. Split audit — Yahoo splits ↔ corporate_actions; every |ret|>25%
    # needs a sourced reason in large_move_reasons.yaml (no auto-explain).
    added = sync_corporate_actions_from_yahoo(raw_dir)
    print(f"corporate_actions: auto-imported {added} Yahoo splits", flush=True)
    ysplits = yahoo_splits_from_raw(raw_dir)
    ysplits.to_csv(exhibits / "yahoo_splits.csv", index=False)
    flags = flag_large_moves(close)
    flags.to_csv(exhibits / "large_moves_close.csv", index=False)
    gap_log, split_report, failures = audit_large_moves(close, raw_dir)
    gap_log.to_csv(exhibits / "split_audit_gaps.csv", index=False)
    split_report.to_csv(exhibits / "split_audit.csv", index=False)
    if failures:
        print("SPLIT AUDIT FAILED:", file=sys.stderr)
        for f in failures:
            print(" ", f, file=sys.stderr)
        test_log.append(
            {
                "test_id": "P1_SPLIT_AUDIT",
                "hypothesis": "meta",
                "description": "Yahoo splits + sourced |ret|>25% reasons required",
                "status": "FAIL",
                "raw_p": "",
                "bh_p": "",
                "effect": "",
                "n": len(split_report),
                "notes": "; ".join(failures)[:500],
            }
        )
        append_tests_run(test_log)
        print("STOP — unexplained large moves / splits. Do not proceed.")
        return 2
    n_moves = len(gap_log) if len(gap_log) else 0
    n_explained = int(gap_log["explained"].sum()) if n_moves else 0
    test_log.append(
        {
            "test_id": "P1_SPLIT_AUDIT",
            "hypothesis": "meta",
            "description": "Yahoo splits matched; every |ret|>25% has sourced reason",
            "status": "PASS",
            "raw_p": "",
            "bh_p": "",
            "effect": "",
            "n": len(split_report),
            "notes": (
                f"yahoo_splits={len(split_report)}; large_moves={n_moves}; "
                f"sourced_explained={n_explained}; no auto-explain"
            ),
        }
    )

    glw_orcl = glw_orcl_52w(close, high)
    glw_orcl.to_csv(exhibits / "glw_orcl_52w.csv", index=False)
    print(glw_orcl.to_string(index=False), flush=True)

    # 4. Merger
    merger = merger_check_mrvl_lite(raw_dir)
    print("MERGER:", json.dumps(merger, indent=2), flush=True)
    if merger["confirmed"]:
        dummy = pd.DataFrame(
            [
                {
                    "ticker": "MRVL",
                    "event": "merger_announced_LITE",
                    "from_date": merger.get("announcement_date", "2026-11-04"),
                    "dummy": 1,
                },
                {
                    "ticker": "LITE",
                    "event": "merger_target_MRVL",
                    "from_date": merger.get("announcement_date", "2026-11-04"),
                    "dummy": 1,
                },
            ]
        )
        dummy.to_csv(processed / "merger_dummy.csv", index=False)
        d4 = "CONFIRMED — merger dummy written"
    else:
        d4 = "CLOSED_UNVERIFIED"
        (processed / "merger_dummy.csv").write_text(
            "ticker,event,from_date,dummy\n"
        )
    test_log.append(
        {
            "test_id": "P1_D4_MERGER",
            "hypothesis": "meta",
            "description": "MRVL/LITE all-stock deal ~4 Nov 2026",
            "status": d4,
            "raw_p": "",
            "bh_p": "",
            "effect": "",
            "n": "",
            "notes": merger.get("note", "")[:400],
        }
    )

    # 5. Survivorship
    starts = listing_starts(close)
    starts.to_csv(exhibits / "listing_starts.csv", header=["first_close"])
    # Build empty feature panel for existence counts only
    uni = [c for c in close.columns if not c.startswith("^") and c not in ("SPY", "QQQ", "SOXX", "SMH")]
    # Actually count full universe.yaml names
    from src.panel_quality import universe_tickers

    u = universe_tickers()
    listing = starts.reindex(u)
    panel = pd.DataFrame(index=u)
    panel["ok"] = 0.0
    for t in u:
        if t in close.columns and close[t].notna().any():
            panel.loc[t, "ok"] = 1.0
    surv = episode_missingness_report(panel, listing, ["ok"], max_nan_share=0.15)
    surv.to_csv(exhibits / "survivorship_by_episode.csv", index=False)

    # 6. D5/D7 resolution — use Close (price) series as note used price returns
    cs = build_cross_section(close, high, use_intraday_high=True)
    cs.to_csv(processed / "nov5_cross_section_ingested.csv", index=False)
    summary = summarise(cs)
    (exhibits / "d5_d7_summary.json").write_text(json.dumps(summary, indent=2))
    print("D5/D7 SUMMARY:", json.dumps(summary, indent=2), flush=True)
    ok, diffs, fail_msgs = compare_to_targets(summary, cs)
    diffs.to_csv(exhibits / "d5_d7_per_name_diff.csv", index=False)
    print(diffs.to_string(index=False), flush=True)

    # SPEC_LITERAL gate
    try:
        lit = run_p1_spec_literal_gate(processed / "prices.parquet")
        lit.to_csv(exhibits / "p1_spec_literal_report.csv", index=False)
        print(lit.to_string(index=False), flush=True)
        lit_ok = True
        lit_notes = "all SPEC_LITERAL within tol"
    except Exception as e:  # noqa: BLE001
        lit_ok = False
        lit_notes = str(e)[:500]
        print("SPEC_LITERAL GATE FAILED:", e, flush=True)

    test_log.append(
        {
            "test_id": "P1_SPEC_LITERAL",
            "hypothesis": "meta",
            "description": "SPEC_LITERAL fixtures vs prices.parquet",
            "status": "PASS" if lit_ok else "FAIL",
            "raw_p": "",
            "bh_p": "",
            "effect": "",
            "n": "",
            "notes": lit_notes,
        }
    )
    test_log.append(
        {
            "test_id": "P1_D5_D7",
            "hypothesis": "meta",
            "description": "name-level EW/Spearman/52w from ingested closes",
            "status": "PASS" if ok else "FAIL",
            "raw_p": "",
            "bh_p": "",
            "effect": str(summary.get("spearman_nov5_vs_ytd", "")),
            "n": summary.get("n", ""),
            "notes": ("OK" if ok else "; ".join(fail_msgs))[:500],
        }
    )
    append_tests_run(test_log)

    if not lit_ok or not ok:
        print("\n=== STOP: fixture disagreement (finding, not a retarget) ===", flush=True)
        for m in fail_msgs:
            print(" ", m, flush=True)
        if not lit_ok:
            print(" ", lit_notes, flush=True)
        print("\nPer-name diff: outputs/exhibits/d5_d7_per_name_diff.csv", flush=True)
        return 1

    print("P1 complete — fixtures reproduced from ingested data.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
