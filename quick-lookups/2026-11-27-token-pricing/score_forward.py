#!/usr/bin/env python3
"""Score the forward test pre-registered in FORWARD_PREREG.md (commit 096fa39) on new data only.

Usage:
  python score_forward.py --ramp-dir data/raw_forward/2027-01-12/04_ramp_ai_index_data --capture-date 2027-01-12
  python score_forward.py ... --q4-revenue 21000 --q4-compute 12000 --report-filed 2027-03-15 --report-name "FY2026 10-K"
  python score_forward.py --self-check      # rebuild check vs the pack's derived per-model file, data <= 2026-11-15 only

Ramp files expected in --ramp-dir (same names as the pack): token_spend_by_model_maker_volumes.csv,
token_volume_by_model_maker_volumes.csv, token_spend_by_model_shares.csv, token_volume_by_model_shares.csv,
token_prices_blended.csv. Amounts in $ millions. Appends to outputs/forward_scores.csv and outputs/forward_trials.csv;
earlier rows are never edited.
"""
import argparse
import csv
import datetime as dt
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
CUTOFF = pd.Timestamp("2026-11-15")
FIRST_SCORE = pd.Timestamp("2027-01-10")
REPORT_DEADLINE = pd.Timestamp("2027-04-30")
RUN_LEN = 8
Q3_REV, Q3_COMP = 16956.0, 9863.0  # 424B4, $M
MIN_TOKEN_SHARE = 0.5


def tier_of(model: str) -> str:
    """Frozen in FORWARD_PREREG.md. Do not edit."""
    for t in ("Opus", "Sonnet", "Haiku", "Fable", "Mythos"):
        if t in model:
            return "claude-" + t.lower()
    for t in ("Codex", "Nano", "Mini", "Luna", "Terra", "Sol", "Astra"):
        if t in model:
            return "gpt-" + t.lower()
    if model.startswith("GPT"):
        return "gpt-base"
    if re.match(r"^o\d", model):
        return "o-series"
    return model.lower()


def lab_of(model: str) -> str:
    if model.startswith("Claude"):
        return "Anthropic"
    if re.match(r"^(GPT|o\d)", model):
        return "OpenAI"
    return "Other"


def weekly(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["period"].str.replace("Week ending ", "", regex=False), format="%b %d, %Y")
    return df.drop(columns="period").set_index("date").sort_index()


def daily_prices(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["period"].str.replace("7 days ending ", "", regex=False), format="%b %d, %Y")
    return df.drop(columns="period").set_index("date").sort_index().rename(columns={"OpenAI & Anthropic": "Combined"})


def rolling_e(Sw, Vw, w=13):
    S13, V13 = Sw.rolling(w).sum(), Vw.rolling(w).sum()
    P13 = S13 / V13
    dV, dP = np.log(V13 / V13.shift(w)), np.log(P13 / P13.shift(w))
    return pd.DataFrame({"dlnV": dV, "dlnP": dP, "e": dV / dP}).dropna()


def derived_prices(rd: Path) -> pd.DataFrame:
    """Per-model price = blended 7-day price at week end x (spend share / token share), token share >= 0.5%."""
    ss, ts = weekly(rd / "token_spend_by_model_shares.csv"), weekly(rd / "token_volume_by_model_shares.csv")
    px = daily_prices(rd / "token_prices_blended.csv")["Combined"]
    rows = []
    for w in ts.index:
        if w not in px.index or w not in ss.index:
            continue
        for m in ts.columns:
            if m.strip().lower() == "other":  # Ramp's residual bucket, not a model (the pack's derived file excludes it)
                continue
            q = ts.at[w, m]
            s = ss.at[w, m] if m in ss.columns else np.nan
            if pd.notna(q) and q >= MIN_TOKEN_SHARE and pd.notna(s) and s > 0:
                rows.append(dict(week_ending=w, model=m, q=q, s=s, blended=px[w], p=px[w] * s / q))
    d = pd.DataFrame(rows)
    d["lab"] = d.model.map(lab_of)
    d["tier"] = d.model.map(tier_of)
    return d


def fisher(dd: pd.DataFrame, key: str, base, end):
    weeks = sorted(w for w in dd.week_ending.unique() if base <= w <= end)
    if len(weeks) < 2:
        return None
    g = dd.groupby(["week_ending", key]).apply(lambda x: pd.Series({"p": (x.p * x.q).sum() / x.q.sum(), "q": x.q.sum()}),
                                                 include_groups=False).reset_index()
    lnF = 0.0
    for a, b in zip(weeks[:-1], weeks[1:]):
        A, B = g[g.week_ending == a].set_index(key), g[g.week_ending == b].set_index(key)
        m = A.index.intersection(B.index)
        if len(m):
            L = (B.p[m] * A.q[m]).sum() / (A.p[m] * A.q[m]).sum()
            P = (B.p[m] * B.q[m]).sum() / (A.p[m] * B.q[m]).sum()
            lnF += 0.5 * (np.log(L) + np.log(P))
    uv = dd.groupby("week_ending").apply(lambda x: (x.p * x.q).sum() / x.q.sum(), include_groups=False)
    lnUV = float(np.log(uv[weeks[-1]] / uv[weeks[0]]))
    return dict(ln_uv=lnUV, ln_fisher=float(lnF), lfl_share=(lnF / lnUV) if lnUV < 0 else None, weeks=len(weeks))


def append(path: Path, row: dict):
    new = not path.exists()
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row.keys()))
        if new:
            w.writeheader()
        w.writerow(row)


def self_check() -> int:
    rd = HERE / "data" / "raw" / "04_ramp_ai_index_data"
    pack = pd.read_csv(HERE / "data" / "raw" / "05_ramp_per_model_observed_prices" /
                       "DERIVED_implied_weekly_price_by_model_from_ramp_shares.csv", parse_dates=["week_ending"])
    mine = derived_prices(rd)
    mine = mine[mine.week_ending <= CUTOFF]
    j = pack.merge(mine, left_on=["week_ending", "model"], right_on=["week_ending", "model"], how="outer", indicator=True)
    both = j[j._merge == "both"]
    err = (both.p / both.implied_observed_price_usd_per_mtok - 1).abs()
    print(f"rows: pack {len(pack)}, rebuilt {len(mine)}, matched {len(both)}, pack-only {int((j._merge == 'left_only').sum())}, "
          f"rebuilt-only {int((j._merge == 'right_only').sum())}; median |rel err| {err.median():.4f}, max {err.max():.4f}")
    ok = len(both) >= 0.95 * len(pack) and err.median() < 0.01
    print("SELF-CHECK", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ramp-dir", type=Path)
    ap.add_argument("--capture-date")
    ap.add_argument("--q4-revenue", type=float)
    ap.add_argument("--q4-compute", type=float)
    ap.add_argument("--q3-revenue", type=float, default=Q3_REV, help="override only if the new report restates Q3")
    ap.add_argument("--q3-compute", type=float, default=Q3_COMP)
    ap.add_argument("--report-filed")
    ap.add_argument("--report-name", default="")
    ap.add_argument("--as-of", default=dt.date.today().isoformat())
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    if a.ramp_dir is None:
        ap.error("--ramp-dir is required (a fresh Ramp capture after 2026-11-15)")
    rd = a.ramp_dir
    as_of = pd.Timestamp(a.as_of)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    trials = []

    # ---------------- C1
    sp = weekly(rd / "token_spend_by_model_maker_volumes.csv")[["Anthropic", "OpenAI"]]
    vo = weekly(rd / "token_volume_by_model_maker_volumes.csv")[["Anthropic", "OpenAI"]]
    ok = (sp >= 1.0).all(axis=1) & (vo >= 1.0).all(axis=1)
    start = ok[ok].index[0]
    sp, vo = sp.loc[start:], vo.loc[start:]
    sp["Combined"], vo["Combined"] = sp.sum(axis=1), vo.sum(axis=1)
    EA, EC = rolling_e(sp.Anthropic, vo.Anthropic), rolling_e(sp.Combined, vo.Combined)
    last_week = sp.index[-1]
    fw = EA.index[EA.index > CUTOFF].intersection(EC.index)
    deadline = pd.Timestamp(a.report_filed) if a.report_filed else None
    if deadline is not None:
        fw = fw[fw <= deadline]
    crack = [(EA.dlnP[w] < 0 and abs(EA.e[w]) < 1 and EC.dlnP[w] < 0 and abs(EC.e[w]) < 1) for w in fw]
    run = best = 0
    for c in crack:
        run = run + 1 if c else 0
        best = max(best, run)
    c1_hit = best >= RUN_LEN
    c1_final = c1_hit or deadline is not None
    trials.append(("C1", "forward crack run (Anthropic AND Combined |e|<1, price falling)", f"longest {best}, current {run}, weeks {len(fw)}"))

    # ---------------- C2 (reported, not in verdict)
    c2 = {"tier": None, "same_version": None, "unmapped_or_base_models": ""}
    try:
        d = derived_prices(rd)
        dd = d[d.week_ending >= CUTOFF]
        if dd.week_ending.max() > CUTOFF:
            c2["tier"] = fisher(dd, "tier", CUTOFF, dd.week_ending.max())
            c2["same_version"] = fisher(dd, "model", CUTOFF, dd.week_ending.max())
            flag = sorted(set(dd.loc[(dd.tier == "gpt-base") | (~dd.tier.str.match(r"^(claude-|gpt-|o-series)")), "model"]))
            c2["unmapped_or_base_models"] = "; ".join(flag)
        trials.append(("C2", "tier-linked Fisher from 2026-11-15", str(c2["tier"])))
        trials.append(("C2", "same-version Fisher from 2026-11-15 (secondary)", str(c2["same_version"])))
    except FileNotFoundError as e:
        trials.append(("C2", "not computed", f"missing file: {e.filename}"))

    # ---------------- C4
    q3_rpc, q3_m = a.q3_revenue / a.q3_compute, (a.q3_revenue - a.q3_compute) / a.q3_revenue
    c4_hit, rpc, margin = None, None, None
    if a.q4_revenue is not None and a.q4_compute is not None:
        rpc = a.q4_revenue / a.q4_compute
        margin = (a.q4_revenue - a.q4_compute) / a.q4_revenue
        c4_hit = (rpc < q3_rpc) and (margin < q3_m)
        trials.append(("C4", "Q4 vs Q3 2026", f"rpc {rpc:.4f} vs {q3_rpc:.4f}; margin {margin:.2%} vs {q3_m:.2%}; hit={c4_hit}"))

    # ---------------- verdict status
    if c4_hit is None:
        if as_of > REPORT_DEADLINE:
            status = "INCONCLUSIVE (no Q4 2026 report by 2027-04-30)"
        else:
            status = "interim" + (" (C1 hit)" if c1_hit else "") + ("" if last_week >= FIRST_SCORE else " (before first scoring week 2027-01-10)")
    else:
        hits = int(bool(c1_hit)) + int(bool(c4_hit))
        status = {2: "HOLDS", 1: "WEAK", 0: "KILLED"}[hits]

    row = dict(scored_utc=stamp, as_of=a.as_of, capture_date=a.capture_date or "", ramp_dir=str(rd), last_week=str(last_week.date()),
               forward_weeks=len(fw), c1_longest_run=best, c1_current_run=run, c1_hit=c1_hit,
               e_anthropic_latest=round(float(EA.e.iloc[-1]), 4), e_combined_latest=round(float(EC.e.iloc[-1]), 4),
               c2_tier_lfl_share=None if not c2["tier"] else c2["tier"]["lfl_share"],
               c2_tier_ln_uv=None if not c2["tier"] else round(c2["tier"]["ln_uv"], 5),
               c2_same_version_lfl_share=None if not c2["same_version"] else c2["same_version"]["lfl_share"],
               c2_flagged_models=c2["unmapped_or_base_models"],
               q4_revenue=a.q4_revenue, q4_compute=a.q4_compute, q4_rpc=None if rpc is None else round(rpc, 4),
               q4_margin_proxy=None if margin is None else round(margin, 4), q3_rpc=round(q3_rpc, 4), q3_margin_proxy=round(q3_m, 4),
               c4_hit=c4_hit, report=a.report_name, report_filed=a.report_filed or "", status=status)
    OUT.mkdir(exist_ok=True)
    append(OUT / "forward_scores.csv", row)
    for t, v, r in trials:
        append(OUT / "forward_trials.csv", dict(scored_utc=stamp, test=t, variant=v, result=r))
    for k, v in row.items():
        print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
