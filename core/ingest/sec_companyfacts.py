"""SEC XBRL companyfacts ingest (data.sec.gov).

Policy:
  - User-Agent MUST include a contact address.
  - Max 10 requests/second (sleep ≥ 0.1s).
  - Cache JSON under data/raw/<asof>/sec_companyfacts_CIK##########.json
  - Every fact stamped with its FILING date; features lag to filing date only.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import requests

from core.config_io import ROOT, universe, study_outputs

SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
COMPANYFACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
USER_AGENT = "useless-data-ai-selloff-study/0.1 (contact: nigelcalixto4@gmail.com)"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov",
}
TICKER_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
}
MIN_INTERVAL_S = 0.11  # ≤ 10 req/s

# Prefer USD unit facts; pick first matching tag that has data.
TAG_CANDIDATES: dict[str, list[str]] = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
        "Revenues",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
    ],
    "net_income": ["NetIncomeLoss"],
    "operating_income": ["OperatingIncomeLoss"],
    "da": [
        "DepreciationDepletionAndAmortization",
        "DepreciationAndAmortization",
        "DepreciationAmortizationAndAccretionNet",
    ],
    "cash": ["CashAndCashEquivalentsAtCarryingValue", "Cash"],
    "interest_expense": ["InterestExpense", "InterestExpenseDebt"],
    "lease_liability": [
        "OperatingLeaseLiability",
        "OperatingLeaseLiabilityCurrent",
        "FinanceLeaseLiability",
    ],
    "long_term_debt": [
        "LongTermDebtNoncurrent",
        "LongTermDebt",
        "LongTermDebtAndCapitalLeaseObligations",
    ],
    "short_term_debt": [
        "LongTermDebtCurrent",
        "ShortTermBorrowings",
        "CommercialPaper",
    ],
    "shares_outstanding": [
        "EntityCommonStockSharesOutstanding",
        "CommonStockSharesOutstanding",
        "WeightedAverageNumberOfDilutedSharesOutstanding",
        "WeightedAverageNumberOfSharesOutstandingBasic",
    ],
}


def _throttle(last: list[float]) -> None:
    elapsed = time.monotonic() - last[0]
    if elapsed < MIN_INTERVAL_S:
        time.sleep(MIN_INTERVAL_S - elapsed)
    last[0] = time.monotonic()


def load_ticker_cik_map(raw_dir: Path, session: requests.Session | None = None) -> dict[str, str]:
    """ticker → zero-padded 10-digit CIK."""
    cache = raw_dir / "sec_company_tickers.json"
    sess = session or requests.Session()
    if cache.exists():
        data = json.loads(cache.read_text())
    else:
        r = sess.get(SEC_TICKERS, headers=TICKER_HEADERS, timeout=60)
        r.raise_for_status()
        data = r.json()
        cache.write_text(json.dumps(data))
    out = {}
    for _k, row in data.items():
        t = str(row.get("ticker", "")).upper()
        cik = str(row.get("cik_str", "")).zfill(10)
        if t and cik:
            out[t] = cik
    return out


def fetch_companyfacts(
    cik: str,
    raw_dir: Path,
    session: requests.Session | None = None,
    last: list[float] | None = None,
    use_cache: bool = True,
) -> dict:
    raw_dir.mkdir(parents=True, exist_ok=True)
    cache = raw_dir / f"sec_companyfacts_CIK{cik}.json"
    if use_cache and cache.exists():
        return json.loads(cache.read_text())
    sess = session or requests.Session()
    last = last or [0.0]
    _throttle(last)
    url = COMPANYFACTS.format(cik=cik)
    # Host header must match data.sec.gov for companyfacts
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
    }
    r = sess.get(url, headers=headers, timeout=120)
    if r.status_code == 404:
        cache.write_text(json.dumps({"error": "404", "cik": cik}))
        return {"error": "404", "cik": cik}
    r.raise_for_status()
    payload = r.json()
    cache.write_text(json.dumps(payload))
    return payload


def _extract_tag_series(facts: dict, tags: list[str]) -> pd.DataFrame:
    """Return DataFrame of filed/end/val for first available tag (USD / shares)."""
    usgaap = (facts.get("facts") or {}).get("us-gaap") or {}
    dei = (facts.get("facts") or {}).get("dei") or {}
    store = {**usgaap, **dei}
    for tag in tags:
        block = store.get(tag)
        if not block:
            continue
        units = block.get("units") or {}
        # prefer USD, then shares, then pure
        series = None
        for unit_key in ("USD", "shares", "pure"):
            if unit_key in units:
                series = units[unit_key]
                break
        if not series and units:
            series = next(iter(units.values()))
        if not series:
            continue
        rows = []
        for item in series:
            filed = item.get("filed")
            end = item.get("end") or item.get("instant")
            val = item.get("val")
            form = item.get("form")
            if filed is None or val is None:
                continue
            rows.append(
                {
                    "tag": tag,
                    "filed": pd.Timestamp(filed),
                    "period_end": pd.Timestamp(end) if end else pd.NaT,
                    "val": float(val),
                    "form": form,
                    "fy": item.get("fy"),
                    "fp": item.get("fp"),
                }
            )
        if rows:
            df = pd.DataFrame(rows).sort_values("filed")
            return df
    return pd.DataFrame(columns=["tag", "filed", "period_end", "val", "form", "fy", "fp"])


def latest_asof(series: pd.DataFrame, asof: pd.Timestamp) -> float | None:
    """Latest value with filing date ≤ asof."""
    if series.empty:
        return None
    sub = series.loc[series["filed"] <= pd.Timestamp(asof)]
    if sub.empty:
        return None
    return float(sub.iloc[-1]["val"])


def fundamentals_asof(facts: dict, asof: pd.Timestamp) -> dict:
    """Point-in-time fundamentals lagged to filing date."""
    out: dict = {"asof": pd.Timestamp(asof)}
    extracted = {k: _extract_tag_series(facts, tags) for k, tags in TAG_CANDIDATES.items()}
    for k, df in extracted.items():
        out[k] = latest_asof(df, asof)

    rev = out.get("revenue")
    ni = out.get("net_income")
    oi = out.get("operating_income")
    da = out.get("da")
    cash = out.get("cash")
    ltd = out.get("long_term_debt")
    std = out.get("short_term_debt")
    interest = out.get("interest_expense")
    lease = out.get("lease_liability")
    shares = out.get("shares_outstanding")

    total_debt = None
    if ltd is not None or std is not None:
        total_debt = (ltd or 0.0) + (std or 0.0)
    ebitda = None
    if oi is not None:
        ebitda = oi + (da or 0.0)

    out["total_debt"] = total_debt
    out["ebitda"] = ebitda
    out["net_debt"] = (total_debt - cash) if (total_debt is not None and cash is not None) else None
    out["net_debt_ebitda"] = (
        out["net_debt"] / ebitda
        if (out.get("net_debt") is not None and ebitda not in (None, 0))
        else None
    )
    out["interest_coverage"] = (
        ebitda / abs(interest)
        if (ebitda is not None and interest not in (None, 0))
        else None
    )
    # lease / assets proxy: lease / (cash + rough assets unknown) → store raw lease
    out["lease_liab_assets"] = None  # needs total assets; filled if we add assets tag
    assets_df = _extract_tag_series(facts, ["Assets"])
    assets = latest_asof(assets_df, asof)
    out["assets"] = assets
    if lease is not None and assets not in (None, 0):
        out["lease_liab_assets"] = lease / assets

    # trailing multiples need price × shares and revenue/earnings — done in panel builder
    out["shares_outstanding"] = shares
    out["revenue"] = rev
    out["net_income"] = ni
    return out


def has_edgar_coverage(facts: dict) -> dict:
    """Whether 10-K / 10-Q / 20-F forms appear in extracted facts."""
    if facts.get("error"):
        return {
            "has_companyfacts": False,
            "has_10k": False,
            "has_10q": False,
            "has_20f": False,
            "forms": "",
        }
    forms = set()
    for section in ((facts.get("facts") or {}).values()):
        if not isinstance(section, dict):
            continue
        for _tag, block in section.items():
            for unit_rows in (block.get("units") or {}).values():
                for item in unit_rows:
                    f = item.get("form")
                    if f:
                        forms.add(f)
    return {
        "has_companyfacts": True,
        "has_10k": "10-K" in forms or "10-K/A" in forms,
        "has_10q": "10-Q" in forms or "10-Q/A" in forms,
        "has_20f": "20-F" in forms or "20-F/A" in forms,
        "forms": ",".join(sorted(forms)),
    }


def universe_tickers() -> list[str]:
    out = []
    for _layer, meta in (universe().get("layers") or {}).items():
        out.extend((meta.get("names") or {}).keys())
    return sorted(out)


def ingest_all(raw_dir: Path | None = None) -> pd.DataFrame:
    raw_dir = raw_dir or (ROOT / "data" / "raw" / "2026-11-08")
    raw_dir.mkdir(parents=True, exist_ok=True)
    sess = requests.Session()
    last = [0.0]
    cik_map = load_ticker_cik_map(raw_dir, sess)
    rows = []
    for t in universe_tickers():
        cik = cik_map.get(t)
        if not cik:
            rows.append(
                {
                    "ticker": t,
                    "cik": "",
                    "has_companyfacts": False,
                    "has_10k": False,
                    "has_10q": False,
                    "has_20f": False,
                    "forms": "",
                    "eligible_h3": False,
                    "exclude_reason": "no CIK in SEC company_tickers.json",
                }
            )
            continue
        print(f"  SEC companyfacts {t} CIK{cik}", flush=True)
        facts = fetch_companyfacts(cik, raw_dir, sess, last)
        cov = has_edgar_coverage(facts)
        eligible = cov["has_10k"] or cov["has_10q"] or cov["has_20f"]
        reason = ""
        if not cov["has_companyfacts"]:
            reason = "companyfacts 404 / empty"
        elif not eligible:
            reason = f"no 10-K/10-Q/20-F in companyfacts (forms={cov['forms']})"
        rows.append(
            {
                "ticker": t,
                "cik": cik,
                **cov,
                "eligible_h3": eligible,
                "exclude_reason": reason,
            }
        )
    df = pd.DataFrame(rows)
    exhibits = study_outputs() / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)
    df.to_csv(exhibits / "edgar_coverage_by_name.csv", index=False)
    return df


if __name__ == "__main__":
    ingest_all()
