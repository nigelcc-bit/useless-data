"""Diagnose supplier-EW and YTD-Spearman gaps. Diagnostic only — not new gates.

Decision rule (pre-registered):
  pipeline error → fix pipeline
  note error → SUPERSEDE old target with Yahoo (+ provenance); log Call 3 magnitude revised
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy import stats

from core.config_io import ROOT, study_outputs
from core.ingest.fred import fetch_fred_series
from src.resolve_d5_d7 import load_nov5_panel_meta

EXHIBITS = study_outputs() / "exhibits"


def note_supplier_set() -> dict[str, list[str]]:
    """Best reconstruction of the note's 16 suppliers from layer counts + named names.

    Note (findings): Semis N=7 −14.0; optics/network N=4 −13.8; power/cooling N=2 −10.8;
    neocloud N=3 −10.6. Named worst: LITE, MU, AMD, MRVL, LRCX, NBIS, VRT.
    Semis N=7 with MU+LRCX named implies compute+memory+semicap mix used in the note.
    """
    return {
        "semis_n7": ["NVDA", "AMD", "AVGO", "MRVL", "TSM", "MU", "LRCX"],
        "optics_n4": ["LITE", "COHR", "ANET", "GLW"],
        "power_n2": ["VRT", "ETN"],
        "neocloud_n3": ["CRWV", "NBIS", "IREN"],
    }


def our_supplier_set(meta: pd.DataFrame) -> list[str]:
    return meta.loc[(meta["ai_chain"] == 1) & (meta["layer"] != "builders"), "ticker"].tolist()


def load_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    close = pd.read_parquet(ROOT / "data" / "processed" / "prices.parquet")
    adj = pd.read_parquet(ROOT / "data" / "processed" / "adj_close.parquet")
    close.index = pd.to_datetime(close.index).normalize()
    adj.index = pd.to_datetime(adj.index).normalize()
    return close, adj


def ret(px: pd.DataFrame, ticker: str, d1: str, d0: str) -> float:
    a = float(px.loc[pd.Timestamp(d1), ticker])
    b = float(px.loc[pd.Timestamp(d0), ticker])
    return a / b - 1.0


def supplier_ew_diag(close: pd.DataFrame) -> dict:
    note = note_supplier_set()
    note_flat = [t for group in note.values() for t in group]
    meta = load_nov5_panel_meta()
    ours = our_supplier_set(meta)
    only_note = sorted(set(note_flat) - set(ours))
    only_ours = sorted(set(ours) - set(note_flat))
    both = sorted(set(note_flat) & set(ours))

    rows = []
    for t in sorted(set(note_flat) | set(ours)):
        r = ret(close, t, "2026-11-05", "2026-11-04") * 100
        rows.append(
            {
                "ticker": t,
                "in_note_set": t in note_flat,
                "in_our_set": t in ours,
                "yahoo_ret_nov5_pct": r,
            }
        )
    detail = pd.DataFrame(rows).sort_values("ticker")
    note_ew = float(np.mean([ret(close, t, "2026-11-05", "2026-11-04") for t in note_flat])) * 100
    our_ew = float(np.mean([ret(close, t, "2026-11-05", "2026-11-04") for t in ours])) * 100

    # Layer EWs on note set vs note targets
    layer_rows = []
    targets = {
        "semis_n7": -14.0,
        "optics_n4": -13.8,
        "power_n2": -10.8,
        "neocloud_n3": -10.6,
    }
    for key, tickers in note.items():
        ew = float(np.mean([ret(close, t, "2026-11-05", "2026-11-04") for t in tickers])) * 100
        layer_rows.append(
            {
                "layer_bucket": key,
                "tickers": ",".join(tickers),
                "yahoo_ew": ew,
                "note_target_ew": targets[key],
                "delta": ew - targets[key],
            }
        )
    return {
        "note_suppliers": note_flat,
        "our_suppliers": ours,
        "only_in_note": only_note,
        "only_in_ours": only_ours,
        "intersection": both,
        "sets_identical": only_note == [] and only_ours == [],
        "yahoo_ew_on_note_set": note_ew,
        "yahoo_ew_on_our_set": our_ew,
        "note_target_ew": -12.9,
        "detail": detail,
        "layer_ew": pd.DataFrame(layer_rows),
    }


def ytd_spearman_diag(close: pd.DataFrame, adj: pd.DataFrame) -> dict:
    """Note name-level YTD was never in the uploaded findings — mark note_ytd as NA.

    Compare Yahoo Close (split-adjusted chart close) vs Adj Close (split+div).
    """
    meta = load_nov5_panel_meta()
    rows = []
    for _, m in meta.iterrows():
        t = m["ticker"]
        r5 = ret(close, t, "2026-11-05", "2026-11-04") * 100
        ytd_close = ret(close, t, "2026-11-04", "2025-12-31") * 100
        ytd_adj = ret(adj, t, "2026-11-04", "2025-12-31") * 100
        rows.append(
            {
                "ticker": t,
                "ai_chain": int(m["ai_chain"]),
                "layer": m["layer"],
                "note_ytd_pct": np.nan,  # original CSV not uploaded
                "yahoo_ytd_close_pct": ytd_close,
                "yahoo_ytd_adj_pct": ytd_adj,
                "abs_diff_close_vs_adj": abs(ytd_close - ytd_adj),
                "ret_nov5_pct": r5,
            }
        )
    df = pd.DataFrame(rows)
    # ranks (1 = highest YTD)
    df["rank_ytd_close"] = df["yahoo_ytd_close_pct"].rank(ascending=False)
    df["rank_ytd_adj"] = df["yahoo_ytd_adj_pct"].rank(ascending=False)
    df["rank_nov5"] = df["ret_nov5_pct"].rank(ascending=False)
    df["rank_change_close_vs_adj"] = df["rank_ytd_close"] - df["rank_ytd_adj"]
    df = df.sort_values("rank_change_close_vs_adj", key=lambda s: s.abs(), ascending=False)

    def spear(ytd_col: str, mask=None) -> tuple[float, float]:
        sub = df if mask is None else df.loc[mask]
        rho, p = stats.spearmanr(sub["ret_nov5_pct"], sub[ytd_col])
        return float(rho), float(p)

    ai = df["ai_chain"] == 1
    rho_c, p_c = spear("yahoo_ytd_close_pct")
    rho_a, p_a = spear("yahoo_ytd_adj_pct")
    rho_c_ai, p_c_ai = spear("yahoo_ytd_close_pct", ai)
    rho_a_ai, p_a_ai = spear("yahoo_ytd_adj_pct", ai)

    # Exact panel N=23 / N=20 already is the note's reconstructed 23 names
    return {
        "note_ytd_available": False,
        "note_ytd_reason": "ai_selloff_cross_section_5Nov2026.csv was never uploaded; name-level note YTD unknown",
        "per_name": df,
        "spearman_close_n23": {"rho": rho_c, "p": p_c, "n": 23},
        "spearman_adj_n23": {"rho": rho_a, "p": p_a, "n": 23},
        "spearman_close_ai_n20": {"rho": rho_c_ai, "p": p_c_ai, "n": int(ai.sum())},
        "spearman_adj_ai_n20": {"rho": rho_a_ai, "p": p_a_ai, "n": int(ai.sum())},
        "note_target_n23": -0.69,
        "note_target_ai": -0.76,
    }


def lite_sensitivity(close: pd.DataFrame) -> dict:
    meta = load_nov5_panel_meta()
    rows = []
    for _, m in meta.iterrows():
        t = m["ticker"]
        rows.append(
            {
                "ticker": t,
                "ai_chain": int(m["ai_chain"]),
                "ret_nov5": ret(close, t, "2026-11-05", "2026-11-04") * 100,
                "ytd": ret(close, t, "2026-11-04", "2025-12-31") * 100,
                "prior5": ret(close, t, "2026-11-04", "2026-10-28") * 100,
            }
        )
    df = pd.DataFrame(rows)
    base = df.copy()
    ex = df[df["ticker"] != "LITE"].copy()

    def pack(frame: pd.DataFrame) -> dict:
        ai = frame["ai_chain"] == 1
        out = {}
        for name, col in (("ytd", "ytd"), ("prior5", "prior5")):
            rho, p = stats.spearmanr(frame["ret_nov5"], frame[col])
            rho_ai, p_ai = stats.spearmanr(frame.loc[ai, "ret_nov5"], frame.loc[ai, col])
            out[f"spearman_{name}_n{len(frame)}"] = {"rho": float(rho), "p": float(p), "n": len(frame)}
            out[f"spearman_{name}_ai_n{int(ai.sum())}"] = {
                "rho": float(rho_ai),
                "p": float(p_ai),
                "n": int(ai.sum()),
            }
        return out

    return {"with_LITE": pack(base), "without_LITE": pack(ex)}


def append_tests_run(row: dict) -> None:
    path = study_outputs() / "tests_run.csv"
    df = pd.read_csv(path)
    df = df[df["test_id"] != row["test_id"]]
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False)


def fetch_nasdaqcom(raw_dir: Path) -> pd.Series:
    return fetch_fred_series("NASDAQCOM", raw_dir)


def nasdaq_crosscheck(raw_dir: Path, close: pd.DataFrame) -> pd.DataFrame:
    nas = fetch_nasdaqcom(raw_dir)
    d0, d1 = pd.Timestamp("2026-11-04"), pd.Timestamp("2026-11-05")
    rows = []
    # FRED NASDAQCOM vs Yahoo ^IXIC
    for label, series in (
        ("FRED_NASDAQCOM", nas),
        ("Yahoo_IXIC", close["^IXIC"]),
    ):
        if d0 not in series.index or d1 not in series.index:
            rows.append({"series": label, "status": "DATE_MISSING"})
            continue
        r = float(series.loc[d1] / series.loc[d0] - 1.0)
        rows.append(
            {
                "series": label,
                "close_1104": float(series.loc[d0]),
                "close_1105": float(series.loc[d1]),
                "ret_nov5": r,
                "note_ixic_ret": -0.0552,
                "status": "OK",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    EXHIBITS.mkdir(parents=True, exist_ok=True)
    raw_dir = ROOT / "data" / "raw" / "2026-11-07"
    close, adj = load_frames()

    # 1. Supplier EW
    sdiag = supplier_ew_diag(close)
    sdiag["detail"].to_csv(EXHIBITS / "diag_supplier_set.csv", index=False)
    sdiag["layer_ew"].to_csv(EXHIBITS / "diag_supplier_layer_ew.csv", index=False)
    print("=== 1. SUPPLIER SET ===")
    print("note:", sdiag["note_suppliers"])
    print("ours:", sdiag["our_suppliers"])
    print("only_in_note:", sdiag["only_in_note"])
    print("only_in_ours:", sdiag["only_in_ours"])
    print("sets_identical:", sdiag["sets_identical"])
    print(f"Yahoo EW on note set: {sdiag['yahoo_ew_on_note_set']:.4f}  (note target -12.9)")
    print(f"Yahoo EW on our set:  {sdiag['yahoo_ew_on_our_set']:.4f}")
    print(sdiag["layer_ew"].to_string(index=False))
    print(sdiag["detail"].to_string(index=False))

    # 2–3. YTD Spearman + exact p
    ydiag = ytd_spearman_diag(close, adj)
    ydiag["per_name"].to_csv(EXHIBITS / "diag_ytd_rank_change.csv", index=False)
    print("\n=== 2. YTD SPEARMAN DIAG ===")
    print("note_ytd_available:", ydiag["note_ytd_available"], "—", ydiag["note_ytd_reason"])
    print("per-name (sorted by |rank change close vs adj|):")
    cols = [
        "ticker",
        "note_ytd_pct",
        "yahoo_ytd_close_pct",
        "yahoo_ytd_adj_pct",
        "abs_diff_close_vs_adj",
        "rank_ytd_close",
        "rank_ytd_adj",
        "rank_change_close_vs_adj",
        "ret_nov5_pct",
    ]
    print(ydiag["per_name"][cols].to_string(index=False))
    print("\n=== 3. EXACT P-VALUES ===")
    for key in (
        "spearman_close_n23",
        "spearman_adj_n23",
        "spearman_close_ai_n20",
        "spearman_adj_ai_n20",
    ):
        print(key, ydiag[key])

    # 4. LITE sensitivity
    lite = lite_sensitivity(close)
    (EXHIBITS / "diag_lite_sensitivity.json").write_text(json.dumps(lite, indent=2))
    print("\n=== 4. LITE SENSITIVITY ===")
    print(json.dumps(lite, indent=2))
    append_tests_run(
        {
            "test_id": "P1_LITE_SENSITIVITY",
            "hypothesis": "meta",
            "description": "Spearman YTD/prior5 excluding LITE (merger ~2 Nov)",
            "status": "DIAGNOSTIC",
            "raw_p": lite["without_LITE"]["spearman_ytd_n22"]["p"],
            "bh_p": "",
            "effect": lite["without_LITE"]["spearman_ytd_n22"]["rho"],
            "n": 22,
            "notes": (
                f"with_LITE ytd_rho={lite['with_LITE']['spearman_ytd_n23']['rho']:.4f}; "
                f"without_LITE ytd_rho={lite['without_LITE']['spearman_ytd_n22']['rho']:.4f}; "
                f"ai_with={lite['with_LITE']['spearman_ytd_ai_n20']['rho']:.4f}; "
                f"ai_without={lite['without_LITE']['spearman_ytd_ai_n19']['rho']:.4f}"
            ),
        }
    )

    # 5. FRED NASDAQCOM
    nx = nasdaq_crosscheck(raw_dir, close)
    nx.to_csv(EXHIBITS / "fred_nasdaqcom_crosscheck.csv", index=False)
    print("\n=== 5. FRED NASDAQCOM ===")
    print(nx.to_string(index=False))

    # Decision summary artifact
    decision = {
        "supplier_ew": {
            "sets_identical": sdiag["sets_identical"],
            "yahoo_ew_note_set": sdiag["yahoo_ew_on_note_set"],
            "note_target": -12.9,
            "gap": sdiag["yahoo_ew_on_note_set"] + 12.9,
            "layer_deltas": sdiag["layer_ew"].to_dict(orient="records"),
        },
        "ytd_spearman": {
            "close_n23": ydiag["spearman_close_n23"],
            "adj_n23": ydiag["spearman_adj_n23"],
            "note_target": -0.69,
            "adj_vs_close_changes_conclusion": bool(
                abs(ydiag["spearman_close_n23"]["rho"] - ydiag["spearman_adj_n23"]["rho"]) < 0.02
            ),
        },
        "lite": lite,
    }
    (EXHIBITS / "diag_decision_inputs.json").write_text(json.dumps(decision, indent=2, default=str))


if __name__ == "__main__":
    main()
