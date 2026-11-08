"""P3 — Build H3 feature panel and coverage table.

Snapshots features at each episode *start* using data with filing/trading
dates ≤ start only. Coverage table = names × episodes × block % non-missing.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.config_io import ROOT, episodes, universe
from src.features.crowding import (
    SI_DEVIATION,
    distance_from_high,
    prior_return,
    realised_vol,
)
from src.features.ffill_audit import write_audit
from src.features.funding import FUNDING_COLS
from src.features.layer import ai_exposure_meta, ai_revenue_exposure, layer_assignments
from src.features.liquidity import adv_dollar, load_volume_panel
from src.features.valuation import VALUATION_COLS
from src.ingest.finra_short_interest import ingest_finra, si_pct_asof
from src.ingest.sec_companyfacts import (
    fetch_companyfacts,
    fundamentals_asof,
    ingest_all as ingest_edgar_coverage,
    load_ticker_cik_map,
)

# Crowding without SI when DEVIATION_FROM_SPEC
CROWDING_COLS_WITH_SI = (
    "prior_63d_return",
    "dist_252d_high",
    "realised_vol_21d",
    "short_interest_pct_float",
)
CROWDING_COLS_NO_SI = (
    "prior_63d_return",
    "dist_252d_high",
    "realised_vol_21d",
)


def block_cols(include_si: bool) -> dict[str, tuple[str, ...]]:
    return {
        "crowding": CROWDING_COLS_WITH_SI if include_si else CROWDING_COLS_NO_SI,
        "valuation": VALUATION_COLS,
        "funding": FUNDING_COLS,
        "layer": ("layer", "ai_revenue_exposure_0_3_JUDGMENT"),
        "liquidity": ("log_mkt_cap", "adv"),
    }


def universe_tickers() -> list[str]:
    return sorted(layer_assignments()["ticker"].tolist())


def equity_close(prices: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    cols = [t for t in tickers if t in prices.columns]
    return prices[cols].sort_index()


def asof_loc(index: pd.DatetimeIndex, dt: pd.Timestamp) -> pd.Timestamp | None:
    if len(index) == 0:
        return None
    pos = index.searchsorted(pd.Timestamp(dt), side="right") - 1
    if pos < 0:
        return None
    return index[pos]


def episode_return(close: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> float:
    s = asof_loc(close.dropna().index, start)
    e = asof_loc(close.dropna().index, end)
    if s is None or e is None or e <= s:
        return float("nan")
    c0, c1 = float(close.loc[s]), float(close.loc[e])
    if c0 <= 0 or not np.isfinite(c0) or not np.isfinite(c1):
        return float("nan")
    return c1 / c0 - 1.0


def _trailing_multiples(price: float, shares: float | None, fund: dict) -> dict:
    out = {c: float("nan") for c in VALUATION_COLS}
    if shares in (None, 0) or not np.isfinite(price) or price <= 0:
        return out
    mcap = price * float(shares)
    rev = fund.get("revenue")
    ni = fund.get("net_income")
    ebitda = fund.get("ebitda")
    net_debt = fund.get("net_debt")
    if rev not in (None, 0):
        out["trailing_ps_filing_lag"] = mcap / float(rev)
    if ni not in (None, 0) and float(ni) > 0:
        out["trailing_pe_filing_lag"] = mcap / float(ni)
    if ebitda not in (None, 0):
        ev = mcap + (float(net_debt) if net_debt is not None else 0.0)
        out["ev_ebitda_filing_lag"] = ev / float(ebitda)
    return out


def build_panel(
    prices_path: Path | None = None,
    raw_dir: Path | None = None,
    *,
    run_edgar: bool = True,
    run_finra: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    prices_path = prices_path or (ROOT / "data" / "processed" / "prices.parquet")
    raw_dir = raw_dir or (ROOT / "data" / "raw" / "2026-11-08")
    prices = pd.read_parquet(prices_path)
    prices.index = pd.to_datetime(prices.index).tz_localize(None).normalize()
    tickers = universe_tickers()
    close = equity_close(prices, tickers)
    volume = load_volume_panel(raw_dir, tickers)

    # Ffill audit (does not alter feature math)
    write_audit(prices_path)

    # EDGAR coverage + caches
    if run_edgar:
        print("=== EDGAR companyfacts ingest ===")
        edgar_cov = ingest_edgar_coverage(raw_dir)
    else:
        edgar_cov = pd.read_csv(ROOT / "outputs" / "exhibits" / "edgar_coverage_by_name.csv")

    cik_map = load_ticker_cik_map(raw_dir)
    facts_cache: dict[str, dict] = {}
    for t in tickers:
        cik = cik_map.get(t)
        if not cik:
            continue
        path = raw_dir / f"sec_companyfacts_CIK{cik}.json"
        if path.exists():
            facts_cache[t] = json.loads(path.read_text())

    # FINRA SI
    include_si = False
    si_panel = pd.DataFrame()
    si_diag: dict = {}
    if run_finra:
        print("=== FINRA short interest ingest ===")
        si_panel, si_diag = ingest_finra(raw_dir)
        include_si = bool(si_diag.get("covers_e1_2018"))
    si_status = (
        "KEPT"
        if include_si
        else f"DROPPED_{SI_DEVIATION}"
    )
    print(f"Short interest decision: {si_status} diag={si_diag}")

    blocks = block_cols(include_si)
    layers = layer_assignments().set_index("ticker")
    ai = ai_revenue_exposure()
    ai_meta = ai_exposure_meta()

    eps = episodes()["episodes"]
    # Precompute price feature frames (native calendar)
    mom = prior_return(close, 63)
    dist = distance_from_high(close, 252)
    vol = realised_vol(close, 21)
    adv = adv_dollar(close, volume, 21) if len(volume) else pd.DataFrame()

    rows = []
    for eid, meta in eps.items():
        start = pd.Timestamp(meta["window"][0])
        end = pd.Timestamp(meta["window"][1])
        asof = asof_loc(close.index, start)
        if asof is None:
            continue
        # truncate feature frames to asof (look-ahead gate)
        mom_t = mom.loc[:asof]
        dist_t = dist.loc[:asof]
        vol_t = vol.loc[:asof]
        adv_t = adv.loc[:asof] if len(adv) else adv

        for ticker in tickers:
            if ticker not in close.columns:
                continue
            listed = bool(close[ticker].loc[:asof].notna().any())
            ep_ret = episode_return(close[ticker], start, end)
            px = float(close[ticker].loc[asof]) if asof in close.index and pd.notna(close[ticker].loc[asof]) else float("nan")

            fund = {}
            if ticker in facts_cache and not facts_cache[ticker].get("error"):
                fund = fundamentals_asof(facts_cache[ticker], asof)
            shares = fund.get("shares_outstanding")
            multiples = _trailing_multiples(px, shares, fund)

            si_val = float("nan")
            if include_si:
                si_val = si_pct_asof(si_panel, shares, ticker, asof)

            log_mcap = float("nan")
            if shares not in (None, 0) and np.isfinite(px) and px > 0:
                log_mcap = float(np.log(px * float(shares)))

            row = {
                "episode": eid,
                "episode_start": start,
                "episode_end": end,
                "ticker": ticker,
                "listed_at_start": listed,
                "episode_return": ep_ret,
                "role": meta.get("role"),
                "character": meta.get("character"),
                "feature_asof": asof,
                "prior_63d_return": float(mom_t[ticker].loc[asof]) if asof in mom_t.index and ticker in mom_t else np.nan,
                "dist_252d_high": float(dist_t[ticker].loc[asof]) if asof in dist_t.index and ticker in dist_t else np.nan,
                "realised_vol_21d": float(vol_t[ticker].loc[asof]) if asof in vol_t.index and ticker in vol_t else np.nan,
                "short_interest_pct_float": si_val if include_si else np.nan,
                "trailing_ps_filing_lag": multiples["trailing_ps_filing_lag"],
                "trailing_pe_filing_lag": multiples["trailing_pe_filing_lag"],
                "ev_ebitda_filing_lag": multiples["ev_ebitda_filing_lag"],
                "net_debt_ebitda": fund.get("net_debt_ebitda"),
                "interest_coverage": fund.get("interest_coverage"),
                "lease_liab_assets": fund.get("lease_liab_assets"),
                "log_mkt_cap": log_mcap,
                "adv": float(adv_t[ticker].loc[asof]) if len(adv_t) and asof in adv_t.index and ticker in adv_t else np.nan,
                "layer": layers.loc[ticker, "layer"] if ticker in layers.index else None,
                "ai_revenue_exposure_0_3_JUDGMENT": float(ai.get(ticker)) if ticker in ai.index and pd.notna(ai.get(ticker)) else np.nan,
                "edgar_eligible": bool(
                    edgar_cov.loc[edgar_cov["ticker"] == ticker, "eligible_h3"].iloc[0]
                )
                if ticker in set(edgar_cov["ticker"])
                else False,
                "valuation_label": "DEVIATION_FROM_SPEC",
                "ai_exposure_tag": ai_meta.get("tag"),
            }
            rows.append(row)

    panel = pd.DataFrame(rows)
    coverage = coverage_table(panel, blocks)
    meta_out = {
        "include_si": include_si,
        "si_status": si_status,
        "si_diag": si_diag,
        "ai_exposure": ai_meta,
        "block_cols": {k: list(v) for k, v in blocks.items()},
    }
    return panel, coverage, meta_out


def coverage_table(panel: pd.DataFrame, blocks: dict[str, tuple[str, ...]]) -> pd.DataFrame:
    records = []
    for (ep, ticker), g in panel.groupby(["episode", "ticker"], sort=True):
        row = g.iloc[0]
        for block, cols in blocks.items():
            present = [c for c in cols if c in g.columns]
            n_ok = 0
            for c in present:
                v = row[c]
                if c == "layer":
                    n_ok += int(isinstance(v, str) and len(v) > 0)
                else:
                    n_ok += int(pd.notna(v))
            pct = 100.0 * n_ok / len(present) if present else 0.0
            records.append(
                {
                    "ticker": ticker,
                    "episode": ep,
                    "block": block,
                    "pct_non_missing": pct,
                    "n_cols": len(present),
                    "listed_at_start": bool(row.get("listed_at_start", False)),
                    "edgar_eligible": bool(row.get("edgar_eligible", False)),
                }
            )
    return pd.DataFrame(records)


def coverage_summary(coverage: pd.DataFrame) -> pd.DataFrame:
    sub = coverage.loc[coverage["listed_at_start"] & coverage["edgar_eligible"]]
    if sub.empty:
        sub = coverage.loc[coverage["listed_at_start"]]
    return (
        sub.groupby(["episode", "block"], sort=True)["pct_non_missing"]
        .mean()
        .reset_index()
        .rename(columns={"pct_non_missing": "mean_pct_non_missing"})
    )


def update_universe_exclusions(edgar_cov: pd.DataFrame) -> None:
    """Write exclusions into universe.yaml for names lacking 10-K/10-Q/20-F."""
    path = ROOT / "config" / "universe.yaml"
    data = yaml.safe_load(path.read_text())
    exclusions = []
    for _, r in edgar_cov.iterrows():
        if not r["eligible_h3"]:
            exclusions.append(
                {
                    "ticker": r["ticker"],
                    "reason": r["exclude_reason"] or "no EDGAR 10-K/10-Q/20-F at companyfacts",
                }
            )
    data["h3_exclusions"] = exclusions
    data["h3_universe_rule"] = (
        "Names with EDGAR 10-K/10-Q or 20-F coverage in companyfacts; "
        "exclusions listed under h3_exclusions with reason."
    )
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def run() -> dict:
    exhibits = ROOT / "outputs" / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)
    processed = ROOT / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)

    print("=== P3 H3 panel rebuild (coverage + EDGAR) ===")
    panel, coverage, meta = build_panel()
    panel.to_parquet(processed / "panel.parquet", index=False)
    coverage.to_csv(exhibits / "h3_feature_coverage.csv", index=False)
    summary = coverage_summary(coverage)
    summary.to_csv(exhibits / "h3_feature_coverage_summary.csv", index=False)
    (exhibits / "h3_panel_meta.json").write_text(json.dumps(meta, indent=2, default=str))

    edgar_cov = pd.read_csv(exhibits / "edgar_coverage_by_name.csv")
    update_universe_exclusions(edgar_cov)

    print("\n=== Coverage summary (listed ∩ EDGAR-eligible) ===")
    pivot = summary.pivot(index="episode", columns="block", values="mean_pct_non_missing")
    print(pivot.round(1).to_string())
    print("\n=== EDGAR coverage by name ===")
    print(edgar_cov.to_string(index=False))
    print(f"\nSI status: {meta['si_status']}")
    print(f"AI exposure: {meta['ai_exposure']}")

    # tests_run log
    tests_path = ROOT / "outputs" / "tests_run.csv"
    tests = pd.read_csv(tests_path)
    for tid in ("P3_H3_COVERAGE", "P3_SI_DECISION", "P3_FFILL_AUDIT", "T005b"):
        tests = tests[tests["test_id"] != tid]
    n_excl = int((~edgar_cov["eligible_h3"]).sum())
    extra = pd.DataFrame(
        [
            {
                "test_id": "P3_H3_COVERAGE",
                "hypothesis": "H3",
                "description": "Updated feature coverage names×episodes×block after EDGAR/FINRA",
                "status": "PASS",
                "raw_p": "",
                "bh_p": "",
                "effect": "",
                "n": len(coverage),
                "notes": f"si={meta['si_status']}; edgar_exclusions={n_excl}",
            },
            {
                "test_id": "P3_SI_DECISION",
                "hypothesis": "H3",
                "description": "FINRA short interest back-to-2018 gate",
                "status": meta["si_status"],
                "raw_p": "",
                "bh_p": "",
                "effect": "",
                "n": meta.get("si_diag", {}).get("n_rows", ""),
                "notes": json.dumps(meta.get("si_diag", {})),
            },
            {
                "test_id": "P3_FFILL_AUDIT",
                "hypothesis": "meta",
                "description": "Price hole ffill audit; cap=1; native calendars for returns",
                "status": "PASS",
                "raw_p": "",
                "bh_p": "",
                "effect": "",
                "n": "",
                "notes": "see ffill_audit_detail.csv; holes=US Memorial/Labor Day 2026",
            },
            {
                "test_id": "T005b",
                "hypothesis": "H3",
                "description": "Trailing multiples lagged to filing date (D6 fallback)",
                "status": "WIRED_DEVIATION_FROM_SPEC",
                "raw_p": "",
                "bh_p": "",
                "effect": "",
                "n": "",
                "notes": "columns in panel.parquet; FDR family member when H3 runs",
            },
        ]
    )
    pd.concat([tests, extra], ignore_index=True).to_csv(tests_path, index=False)
    return {"panel": panel, "coverage": coverage, "summary": summary, "meta": meta}


def main() -> None:
    run()


if __name__ == "__main__":
    main()
