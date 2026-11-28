"""Shared loaders, trial ledger and fixture gate for Study 5 (growth-value de-rating). Pre-registration: PREREG.md."""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

STUDY = Path(__file__).resolve().parents[1]
RAW = STUDY / "data" / "raw"
OUT = STUDY / "outputs"
OUT.mkdir(exist_ok=True)
SEED = 7

PEAK_FROM, PEAK_TO = pd.Timestamp("2025-01-03"), pd.Timestamp("2026-11-27")
END = pd.Timestamp("2026-11-27")
RECON = (pd.Timestamp("2025-12-12"), pd.Timestamp("2026-01-02"))  # weeks ending, inclusive (change weeks)


# ------------------------------------------------------------------ loaders
def weekly_pe() -> pd.DataFrame:
    df = pd.read_csv(RAW / "row1_yardeni_fwd_pe_growth_value_weekly_2024_now.csv", parse_dates=["week_ending"])
    return df.set_index("week_ending").sort_index()


def daily_prices() -> pd.DataFrame:
    df = pd.read_csv(RAW / "row3_sp500_growth_value_price_index_daily_2024_now.csv", parse_dates=["date"])
    return df.set_index("date").sort_index()


def on_or_before(daily: pd.Series, dates: pd.DatetimeIndex) -> pd.Series:
    s = daily.dropna().sort_index()
    pos = s.index.searchsorted(dates, side="right") - 1
    if (pos < 0).any():
        raise ValueError("no observation on or before some grid date")
    return pd.Series(s.values[pos], index=dates)


def weekly_panel() -> pd.DataFrame:
    """Weekly grid: PE (row1), price on/before Friday (row3), EPS (b) = price/PE, EPS (a) = Blue Angels (row2)."""
    pe = weekly_pe()
    px = daily_prices()
    w = pd.DataFrame(index=pe.index)
    w["pe_g"], w["pe_v"] = pe["growth"], pe["value"]
    w["px_g"] = on_or_before(px["sp500_growth_2029"], pe.index)
    w["px_v"] = on_or_before(px["sp500_value_2034"], pe.index)
    w["eps_b_g"], w["eps_b_v"] = w.px_g / w.pe_g, w.px_v / w.pe_v
    e = pd.read_csv(RAW / "row2_fwd_eps_growth_value_weekly_2024_now.csv", parse_dates=["week_ending"]).set_index("week_ending")
    w["eps_a_g_raw"] = e["growth_fwd_eps_yardeni_blueangels_digitised"].reindex(w.index)
    w["eps_a_v_raw"] = e["value_fwd_eps_yardeni_blueangels_digitised"].reindex(w.index)
    for s in ("g", "v"):  # splice (b) onto (a) after (a) ends, rescaled at the last (a) week (no jump)
        a = w[f"eps_a_{s}_raw"]
        last = a.last_valid_index()
        scale = a[last] / w.at[last, f"eps_b_{s}"]
        w[f"eps_a_{s}"] = a.where(w.index <= last, w[f"eps_b_{s}"] * scale)
    w.attrs["eps_a_last_week"] = str(last.date())
    return w


def fred_on_grid(grid: pd.DatetimeIndex) -> pd.DataFrame:
    f = pd.read_csv(RAW / "row4_fred_DFII10_DGS10_daily_2024_now.csv", parse_dates=["date"]).set_index("date").sort_index()
    return pd.DataFrame({c: on_or_before(f[c], grid) for c in ("DFII10", "T10YIE", "DGS10")})


# ------------------------------------------------------------------ ledgers
class Ledger:
    def __init__(self):
        self.trials: list[dict] = []
        self.tests: list[dict] = []

    def trial(self, phase, test, variant, statistic, n, result):
        self.trials.append(dict(trial_id=len(self.trials) + 1, phase=phase, test=test, variant=variant,
                                statistic=statistic, n=n, result=result,
                                timestamp=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))

    def test(self, test_id, hypothesis, description, status, raw_p=None, effect=None, n=None, notes="", family=""):
        self.tests.append(dict(test_id=test_id, hypothesis=hypothesis, description=description, status=status,
                               raw_p="" if raw_p is None else f"{raw_p:.4g}", bh_p="", effect="" if effect is None else effect,
                               n="" if n is None else n, notes=notes, raw_p_num=raw_p if raw_p is not None else "", family=family))

    def write(self):
        # BH within each family (protocol rule 5, q = 0.10)
        fams = {}
        for t in self.tests:
            if t["family"] and t["raw_p_num"] != "":
                fams.setdefault(t["family"], []).append(t)
        for fam, ts in fams.items():
            p = np.array([t["raw_p_num"] for t in ts], float)
            bh = bh_adjust(p)
            for t, b in zip(ts, bh):
                t["bh_p"] = f"{b:.4g}"
        for name, rows in (("trials.csv", self.trials), ("tests_run.csv", self.tests)):
            if not rows:
                continue
            with open(OUT / name, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)


def bh_adjust(p: np.ndarray) -> np.ndarray:
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(adj, 1.0)
    return out


# ------------------------------------------------------------------ fixtures gate
def check_fixtures() -> None:
    fx = yaml.safe_load((STUDY / "config" / "fixtures.yaml").read_text())
    bad = []
    for name, spec in fx["files"].items():
        p = RAW / name
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if h != spec["sha256"]:
            bad.append(f"{name}: sha256 {h} != {spec['sha256']}")
    pe = weekly_pe()
    for v in fx["pe_end"]:
        got = float(pe.loc[pd.Timestamp(v["week"]), v["series"]])
        if abs(got - v["value"]) > 1e-9:
            bad.append(f"PE {v}: got {got}")
    wb = pd.read_csv(RAW / "row5_IVW_holdings_20251107_wayback.csv", skiprows=9)
    n_pre = int((wb["Asset Class"] == "Equity").sum())
    post = pd.read_csv(RAW / "row5_IVW_holdings_20251231.csv")
    n_post = int((post["assetClass"] == "Equity").sum())
    if (n_pre, n_post) != (fx["ivw_names"]["pre_2025_11_07"], fx["ivw_names"]["post_2025_12_31"]):
        bad.append(f"IVW equity names {n_pre}->{n_post} != fixtures")
    if bad:
        raise SystemExit("FIXTURE GATE FAILED (pipeline stops):\n" + "\n".join(bad))
