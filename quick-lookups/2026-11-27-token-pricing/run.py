#!/usr/bin/env python3
"""Token pricing quick-lookup: crack in the AI revenue thesis or Jevons demand?
Reruns end to end from data/raw/ (the unzipped token_pricing_data_pack). Pre-registration: PREREG.md (commit bd31314).
Writes small processed CSVs to data/, tables/charts/trials to outputs/. Every test and variant is logged to outputs/trials.csv."""
import csv
import datetime as dt
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import optimize, special, stats

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
DATA = HERE / "data"
OUT = HERE / "outputs"
OUT.mkdir(exist_ok=True)
TRIALS = []
RES = {}
RNG = np.random.default_rng(20261127)
BLUE, ORANGE, AQUA, INK, INK2, GRID = "#257de0", "#f47230", "#00b894", "#191919", "#666666", "#e6e6e6"


def trial(test, variant, statistic, n, result):
    TRIALS.append(dict(trial_id=len(TRIALS) + 1, test=test, variant=variant, statistic=statistic, n=n, result=result,
                       timestamp=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.tick_params(colors=INK2)


# ---------------------------------------------------------------- loaders
def ramp_weekly(name):
    df = pd.read_csv(RAW / "04_ramp_ai_index_data" / f"{name}.csv")
    df["date"] = pd.to_datetime(df["period"].str.replace("Week ending ", "", regex=False), format="%b %d, %Y")
    return df.drop(columns="period").set_index("date").sort_index()


def ramp_daily_prices(name="token_prices_blended"):
    df = pd.read_csv(RAW / "04_ramp_ai_index_data" / f"{name}.csv")
    df["date"] = pd.to_datetime(df["period"].str.replace("7 days ending ", "", regex=False), format="%b %d, %Y")
    return df.drop(columns="period").set_index("date").sort_index()


spend = ramp_weekly("token_spend_by_model_maker_volumes")[["Anthropic", "OpenAI"]]
vol = ramp_weekly("token_volume_by_model_maker_volumes")[["Anthropic", "OpenAI"]]
spend_sh = ramp_weekly("token_spend_by_model_maker_shares")
vol_sh = ramp_weekly("token_volume_by_model_maker_shares")
px = ramp_daily_prices().rename(columns={"OpenAI & Anthropic": "Combined"})
spend["Combined"] = spend.Anthropic + spend.OpenAI
vol["Combined"] = vol.Anthropic + vol.OpenAI
LATEST = spend.index[-1]
RES["latest_week"] = str(LATEST.date())

# ================================================================= C1
ok = (spend[["Anthropic", "OpenAI"]] >= 1.0).all(axis=1) & (vol[["Anthropic", "OpenAI"]] >= 1.0).all(axis=1)
START = ok[ok].index[0]
RES["c1_start"] = str(START.date())
S = spend.loc[START:]
V = vol.loc[START:]

# 4-week blocks aligned to end at the latest week
nb = len(S) // 4
idx = S.index[len(S) - 4 * nb:]
blk = pd.Series(np.repeat(np.arange(nb), 4), index=idx)
S4 = S.loc[idx].groupby(blk.values).sum()
V4 = V.loc[idx].groupby(blk.values).sum()
blk_end = pd.Series(idx).groupby(blk.values).max().values
blk_start = pd.Series(idx).groupby(blk.values).min().values - np.timedelta64(6, "D")
S4.index = V4.index = pd.to_datetime(blk_end)


def block_mean_prices(daily, starts, ends):
    rows = []
    for a, b in zip(starts, ends):
        rows.append(daily.loc[(daily.index >= a) & (daily.index <= b)].mean())
    return pd.DataFrame(rows, index=pd.to_datetime(ends))


P4_ramp = block_mean_prices(px, blk_start, blk_end)
c1_tab = []
for lab in ["Combined", "Anthropic", "OpenAI"]:
    gS = np.log(S4[lab]).diff()
    gV = np.log(V4[lab]).diff()
    gP = gS - gV
    gR = np.log(P4_ramp[lab]).diff()
    gap = (gP - gR).abs().dropna()
    for t in S4.index[1:]:
        c1_tab.append(dict(block_end=t.date(), lab=lab, spend_logg=gS[t], volume_logg=gV[t], implied_price_logg=gP[t], ramp_price_logg=gR[t]))
    RES[f"c1_crosscheck_median_abs_gap_{lab}"] = float(gap.median())
    trial("C1", f"cross-check implied vs Ramp blended price, {lab}", "median |log gap| per 4-week block", len(gap), f"{gap.median():.3f}")
pd.DataFrame(c1_tab).to_csv(DATA / "c1_four_week_growth.csv", index=False, float_format="%.5f")


def rolling_e(Sw, Vw, w=13):
    S13 = Sw.rolling(w).sum()
    V13 = Vw.rolling(w).sum()
    P13 = S13 / V13
    dV = np.log(V13 / V13.shift(w))
    dP = np.log(P13 / P13.shift(w))
    dS = np.log(S13 / S13.shift(w))
    return pd.DataFrame({"dlnV": dV, "dlnP": dP, "dlnS": dS, "e": dV / dP}).dropna()


def readings(E):
    falling = E.dlnP < 0
    jev = falling & (E.e.abs() > 1)
    crack = falling & (E.e.abs() < 1)
    run, best, cur_run = 0, 0, 0
    for c in crack:
        run = run + 1 if c else 0
        best = max(best, run)
    cur_run = run
    return falling, jev, crack, best, cur_run


E = {}
for lab in ["Combined", "Anthropic", "OpenAI"]:
    E[lab] = rolling_e(S[lab], V[lab])
    falling, jev, crack, best, cur = readings(E[lab])
    last = E[lab].iloc[-1]
    read = ("price not falling" if last.dlnP >= 0 else ("Jevons (|e|>1, spend up)" if abs(last.e) > 1 else "crack (|e|<1, spend down)"))
    RES[f"c1_{lab}"] = dict(latest_e=float(last.e), latest_abs_e=float(abs(last.e)), dlnP=float(last.dlnP), dlnV=float(last.dlnV), dlnS=float(last.dlnS),
                            reading=read, windows=int(len(E[lab])), price_falling_windows=int(falling.sum()), jevons_windows=int(jev.sum()),
                            crack_windows=int(crack.sum()), longest_crack_run=int(best), current_crack_run=int(cur),
                            crack_rule_8wk_met_now=bool(cur >= 8), crack_rule_8wk_ever=bool(best >= 8))
    trial("C1", f"latest 13-week realised elasticity, {lab}", "e = dlnV/dlnP", 1, f"e={last.e:.2f}; {read}")
    trial("C1", f"crack rule (|e|<1, price falling, >=8 consecutive weeks), {lab}", "longest run / current run", len(E[lab]), f"{best} / {cur}")
    E[lab].to_csv(DATA / f"c1_rolling_elasticity_{lab.lower()}.csv", float_format="%.5f")

# Robustness: start 2026-01-11
E_rob = rolling_e(spend.loc["2026-01-11":, "Combined"], vol.loc["2026-01-11":, "Combined"])
RES["c1_rob_start_2026"] = dict(latest_e=float(E_rob.e.iloc[-1]), dlnP=float(E_rob.dlnP.iloc[-1]))
trial("C1", "robustness: sample start 2026-01-11, Combined", "latest e", len(E_rob), f"{E_rob.e.iloc[-1]:.2f}")

# small-sample-truth: non-overlapping 13-week windows with price falling, count |e|>1
Ec = E["Combined"]
nonover = Ec.iloc[::-13]
nf = nonover[nonover.dlnP < 0]
c, n = int((nf.e.abs() > 1).sum()), len(nf)
post = stats.beta(1 + c, 1 + n - c)
RES["c1_nonoverlap"] = dict(c=c, n=n, post_mean=post.mean(), lo90=post.ppf(0.05), hi90=post.ppf(0.95), p_gt_half=1 - post.cdf(0.5))
trial("C1", "small-sample-truth: non-overlapping 13-week windows (price falling) with |e|>1, Combined", "c/n, Beta(1,1) posterior", n,
      f"{c}/{n}; mean {post.mean():.2f}; 90% {post.ppf(0.05):.2f}-{post.ppf(0.95):.2f}")

# ================================================================= C2
d = pd.read_csv(RAW / "05_ramp_per_model_observed_prices" / "DERIVED_implied_weekly_price_by_model_from_ramp_shares.csv", parse_dates=["week_ending"])
d["lab"] = np.where(d.model.str.startswith("Claude"), "Anthropic", np.where(d.model.str.match(r"^(GPT|o\d)"), "OpenAI", "Other"))
d = d.rename(columns={"implied_observed_price_usd_per_mtok": "p", "token_share_pct": "q"})

# base week: Sunday in March 2026 with highest combined 7-day blended price
march_sundays = [t for t in px.index if t.year == 2026 and t.month == 3 and t.weekday() == 6]
BASE = max(march_sundays, key=lambda t: px.loc[t, "Combined"])
RES["c2_base_week"] = str(BASE.date())
RES["c2_base_blended"] = float(px.loc[BASE, "Combined"])
RES["c2_latest_blended"] = float(px.loc[LATEST, "Combined"])
RES["c2_ramp_blended_pct_change"] = float(px.loc[LATEST, "Combined"] / px.loc[BASE, "Combined"] - 1)
# also: March daily max (brief's "-41% from the March 2026 peak")
mar = px.loc["2026-03-01":"2026-03-31", "Combined"]
RES["c2_march_daily_peak"] = dict(date=str(mar.idxmax().date()), value=float(mar.max()),
                                  pct_to_latest_daily=float(px["Combined"].iloc[-1] / mar.max() - 1), latest_daily_date=str(px.index[-1].date()))


def fisher_decomp(dd, base, end):
    weeks = sorted(w for w in dd.week_ending.unique() if base <= w <= end)
    lnF = 0.0
    path = [(weeks[0], 0.0, None)]
    for a, b in zip(weeks[:-1], weeks[1:]):
        A = dd[dd.week_ending == a].set_index("model")
        B = dd[dd.week_ending == b].set_index("model")
        m = A.index.intersection(B.index)
        if len(m) == 0:
            path.append((b, lnF, 0))
            continue
        L = (B.p[m] * A.q[m]).sum() / (A.p[m] * A.q[m]).sum()
        P = (B.p[m] * B.q[m]).sum() / (A.p[m] * B.q[m]).sum()
        lnF += 0.5 * (np.log(L) + np.log(P))
        path.append((b, lnF, len(m)))
    uv = dd.groupby("week_ending").apply(lambda g: (g.p * g.q).sum() / g.q.sum(), include_groups=False)
    lnUV = np.log(uv.loc[weeks[-1]] / uv.loc[weeks[0]])
    return lnF, lnUV, pd.DataFrame(path, columns=["week_ending", "ln_fisher", "matched_models"]).set_index("week_ending"), uv


c2 = {}
paths = {}
for lab, sub in [("Combined", d), ("Anthropic", d[d.lab == "Anthropic"]), ("OpenAI", d[d.lab == "OpenAI"])]:
    for base_name, base in [("combined March peak", BASE), ("own-lab March peak", None)]:
        if base is None:
            col = "Combined" if lab == "Combined" else lab
            base = max(march_sundays, key=lambda t: px.loc[t, col])
        lnF, lnUV, path, uv = fisher_decomp(sub, base, LATEST)
        mix = lnUV - lnF
        ramp_col = lab
        lnR = np.log(px.loc[LATEST, ramp_col] / px.loc[base, ramp_col])
        lfl_share = lnF / lnUV if lnUV < 0 else np.nan
        mix_share = mix / lnUV if lnUV < 0 else np.nan
        key = f"{lab}|{base_name}"
        c2[key] = dict(lab=lab, base=str(base.date()), ln_unit_value=lnUV, pct_unit_value=np.expm1(lnUV), ln_fisher=lnF, pct_fisher=np.expm1(lnF),
                       ln_mix=mix, like_for_like_share=lfl_share, mix_share=mix_share, ln_ramp_blended=lnR, pct_ramp_blended=np.expm1(lnR),
                       covered_token_share_base=float(sub[sub.week_ending == base].q.sum()), covered_token_share_latest=float(sub[sub.week_ending == LATEST].q.sum()))
        trial("C2", f"Fisher like-for-like vs mix, {lab}, base {base_name} ({base.date()})", "share of log fall: like-for-like / mix", 1,
              f"LfL {lfl_share:.0%} / mix {mix_share:.0%}" if lnUV < 0 else "unit value did not fall")
        if base_name == "combined March peak":
            paths[lab] = (path, uv)
RES["c2"] = c2
pd.DataFrame(c2.values()).to_csv(DATA / "c2_fisher_mix_decomposition.csv", index=False, float_format="%.5f")

# validation vs Ramp April 2026 published table
pub = pd.read_csv(RAW / "05_ramp_per_model_observed_prices" / "ramp_observed_cost_per_mtok_by_model_april_2026.csv")
name_map = {"GPT-5-nano": "GPT-5 Nano", "Claude Haiku 4.5": "Claude Haiku 4.5", "Claude Sonnet 4.6": "Claude Sonnet 4.6",
            "Claude Opus 4.6": "Claude Opus 4.6", "GPT-5.5": "GPT-5.5", "GPT-4o": "GPT-4o"}
apr = d[(d.week_ending >= "2026-04-01") & (d.week_ending <= "2026-04-30")]
val = []
for r in pub.itertuples():
    m = name_map.get(r.model, r.model)
    x = apr[apr.model == m].p
    derived = float(x.mean()) if len(x) else np.nan
    val.append(dict(model=r.model, derived_model=m, published=r.ramp_observed_cost_usd_per_mtok, derived_april_mean=derived, weeks=len(x),
                    pct_error=(derived / r.ramp_observed_cost_usd_per_mtok - 1) if len(x) else np.nan))
VAL = pd.DataFrame(val)
VAL.to_csv(DATA / "c2_validation_vs_ramp_april_2026.csv", index=False, float_format="%.4f")
for r in VAL.itertuples():
    trial("C2", f"validation derived vs published April 2026, {r.model}", "pct error", r.weeks, "not in derived file" if np.isnan(r.pct_error) else f"{r.pct_error:+.0%}")
RES["c2_validation"] = VAL.to_dict(orient="records")

# list-price index (Wayback)
LP = pd.read_csv(RAW / "07_wayback_list_prices" / "list_prices_long.csv")


def norm_model(s):
    s = str(s).strip()
    m = re.match(r"^(Claude (?:Opus|Sonnet|Haiku|Fable|Mythos) [\d.]+)", s)
    if m:
        return m.group(1).lower()
    m = re.match(r"^((?:gpt|o)[\w.\-]*)", s.lower())
    return m.group(1) if m else None


def list_prices(lab, date):
    x = LP[(LP.lab == lab) & (LP.snapshot_date == date)].copy()
    x = x[~x.table_header.fillna("").str.contains("Batch|Training|Fine|Size|Tool|Usage", case=False)]
    cand = x[x.table_header.fillna("").str.contains(r"Input|Base", case=False) | x.price_column.fillna("").str.contains("Input|Base|Prompt caching", case=False)]
    t0 = x[x.table_idx == cand.table_idx.min()]  # all rows of the first standard (non-batch) price table
    out = {}
    labelled = t0.price_column.fillna("").str.contains(r"^(?:Base Input Tokens|Input|Output Tokens|Output)$", case=False).any()
    if labelled:
        for r in t0.itertuples():
            mdl = norm_model(r.model_or_row_label)
            if not mdl:
                continue
            pc = str(r.price_column).lower()
            v = float(str(r.first_usd_value)) if pd.notna(r.first_usd_value) else np.nan
            if pc in ("base input tokens", "input"):
                out.setdefault(mdl, {})["input"] = v
            elif pc in ("output tokens", "output"):
                out.setdefault(mdl, {})["output"] = v
    else:  # grouped layout: per model, first value = input, second = output (verified against snapshot text headers)
        for mdl_raw, g in t0.groupby("model_or_row_label", sort=False):
            mdl = norm_model(mdl_raw)
            vals = [float(v) for v in g.first_usd_value if pd.notna(v)]
            if mdl and len(vals) >= 2:
                out[mdl] = {"input": vals[0], "output": vals[1]}
    return out


lp_rows, lp_res = [], {}
for lab, d0, d1 in [("Anthropic", "2026-03-01", "2026-11-01"), ("OpenAI", "2026-03-04", "2026-11-01")]:
    a, b = list_prices(lab, d0), list_prices(lab, d1)
    for k, v in a.items():
        lp_rows.append(dict(lab=lab, snapshot=d0, model=k, **v))
    for k, v in b.items():
        lp_rows.append(dict(lab=lab, snapshot=d1, model=k, **v))
    both = [k for k in a if k in b and all(s in a[k] and s in b[k] for s in ("input", "output"))]
    res = dict(base_snapshot=d0, latest_snapshot=d1, models_base=len(a), models_latest=len(b), matched=both)
    for side in ("input", "output"):
        if both:
            r = np.exp(np.mean([np.log(b[k][side] / a[k][side]) for k in both]))
            res[f"fixed_version_{side}_ratio"] = float(r)
        else:
            res[f"fixed_version_{side}_ratio"] = None
    lp_res[lab] = res
    trial("C2", f"list-price index at fixed versions, {lab} ({d0} vs {d1})", "geomean ratio input/output; matched models", len(both),
          f"input {res['fixed_version_input_ratio']}, output {res['fixed_version_output_ratio']}; matched {both}")
# tier successors (descriptive)
tiers = {"Anthropic": [("opus", r"claude opus"), ("sonnet", r"claude sonnet"), ("haiku", r"claude haiku")]}
succ = []
for lab, d0, d1 in [("Anthropic", "2026-03-01", "2026-11-01")]:
    a, b = list_prices(lab, d0), list_prices(lab, d1)
    for tier, pat in tiers[lab]:
        def newest(dct):
            ks = [k for k in dct if re.match(pat, k)]
            return max(ks, key=lambda k: [float(x) for x in re.findall(r"[\d.]+", k)[0].split(".") if x]) if ks else None
        ka, kb = newest(a), newest(b)
        if ka and kb:
            succ.append(dict(lab=lab, tier=tier, base_model=ka, base_input=a[ka].get("input"), base_output=a[ka].get("output"),
                             latest_model=kb, latest_input=b[kb].get("input"), latest_output=b[kb].get("output")))
for lab, d0, d1 in [("OpenAI", "2026-03-04", "2026-11-01")]:
    a, b = list_prices(lab, d0), list_prices(lab, d1)
    ka, kb = next(iter(a)), next(iter(b))  # first-listed model of the standard table = flagship as presented
    succ.append(dict(lab=lab, tier="first-listed flagship", base_model=ka, base_input=a[ka].get("input"), base_output=a[ka].get("output"),
                     latest_model=kb, latest_input=b[kb].get("input"), latest_output=b[kb].get("output")))
SUCC = pd.DataFrame(succ)
SUCC.to_csv(DATA / "c2_list_price_tier_successors.csv", index=False)
pd.DataFrame(lp_rows).to_csv(DATA / "c2_list_prices_parsed.csv", index=False)
for r in SUCC.itertuples():
    trial("C2", f"list-price tier successor (descriptive), {r.lab} {r.tier}", "base vs latest input/output", 1,
          f"{r.base_model} {r.base_input}/{r.base_output} -> {r.latest_model} {r.latest_input}/{r.latest_output}")
RES["c2_list_prices"] = lp_res
RES["c2_tier_successors"] = SUCC.to_dict(orient="records")

# ----- C2x EXPLORATORY (not pre-registered): tier-linked index, successors treated as the same product
def tier_of(model):
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


dt_ = d.assign(tier=d.model.map(tier_of))
tier_week = dt_.groupby(["week_ending", "tier", "lab"], as_index=False).apply(
    lambda g: pd.Series({"p": (g.p * g.q).sum() / g.q.sum(), "q": g.q.sum()}), include_groups=False).rename(columns={"tier": "model"})
c2x = {}
for lab, sub in [("Combined", tier_week), ("Anthropic", tier_week[tier_week.lab == "Anthropic"]), ("OpenAI", tier_week[tier_week.lab == "OpenAI"])]:
    lnF, lnUV, path_t, _ = fisher_decomp(sub, BASE, LATEST)
    lfl_t = lnF / lnUV if lnUV < 0 else np.nan
    c2x[lab] = dict(ln_unit_value=lnUV, ln_tier_fisher=lnF, pct_tier_fisher=np.expm1(lnF), like_for_like_share=lfl_t, mix_share=1 - lfl_t)
    trial("C2x (exploratory)", f"tier-linked Fisher (successors = same product), {lab}", "share of log fall: like-for-like / mix", 1,
          f"LfL {lfl_t:.0%} / mix {1 - lfl_t:.0%}")
    if lab == "Combined":
        tier_path_combined = path_t
RES["c2x_tier_linked"] = c2x
RES["c2x_tier_map"] = dt_[["model", "tier"]].drop_duplicates().sort_values("tier").values.tolist()
pd.DataFrame(c2x).T.to_csv(DATA / "c2x_tier_linked_exploratory.csv", float_format="%.5f")

# ================================================================= C3
share_w = (spend_sh.Anthropic / (spend_sh.Anthropic + spend_sh.OpenAI) * 100).loc[START:]
sh4 = share_w.loc[idx].groupby(blk.values).mean()
sh4.index = pd.to_datetime(blk_end)
x4 = np.log(P4_ramp.Anthropic / P4_ramp.OpenAI)
C3 = pd.DataFrame({"share_pp": sh4, "ln_rel_price": x4}).dropna()
C3.to_csv(DATA / "c3_share_vs_relative_price_4wk.csv", float_format="%.5f")


def nw_lag(n):
    return max(1, int(np.floor(4 * (n / 100) ** (2 / 9))))


def ols_nw(y, x):
    X = sm.add_constant(x)
    f = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": nw_lag(len(y))})
    return f


def block_boot_slope(y, x, block=3, reps=2000):
    y, x = np.asarray(y), np.asarray(x)
    n = len(y)
    starts = np.arange(n - block + 1)
    out = []
    for _ in range(reps):
        sel = np.concatenate([np.arange(s, s + block) for s in RNG.choice(starts, int(np.ceil(n / block)))])[:n]
        X = np.column_stack([np.ones(n), x[sel]])
        out.append(np.linalg.lstsq(X, y[sel], rcond=None)[0][1])
    return np.quantile(out, [0.05, 0.95])


def t_fit(y, x, iters=500):
    """Univariate t regression by EM (tail-audit): w=(nu+1)/(nu-2+delta), delta=e^2/sigma2 (sigma2 = covariance scale)."""
    y, x = np.asarray(y, float), np.asarray(x, float)
    X = np.column_stack([np.ones(len(y)), x])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    s2 = e.var()
    nu = 5.0

    def ll(nu_, e_, s2_):
        scale2 = s2_ * (nu_ - 2) / nu_
        return np.sum(stats.t.logpdf(e_ / np.sqrt(scale2), nu_) - 0.5 * np.log(scale2))

    for _ in range(iters):
        delta = e ** 2 / s2
        w = (nu + 1) / (nu - 2 + delta)
        W = np.diag(w)
        b_new = np.linalg.solve(X.T @ W @ X, X.T @ W @ y)
        e = y - X @ b_new
        s2_new = np.mean(w * e ** 2)
        r = optimize.minimize_scalar(lambda v: -ll(v, e, s2_new), bounds=(2.05, 200), method="bounded")
        nu_new = r.x
        if np.max(np.abs(b_new - b)) < 1e-9 and abs(nu_new - nu) < 1e-6:
            b, s2, nu = b_new, s2_new, nu_new
            break
        b, s2, nu = b_new, s2_new, nu_new
    delta = e ** 2 / s2
    w = (nu + 1) / (nu - 2 + delta)
    cov = s2 * np.linalg.inv(X.T @ np.diag(w) @ X)
    se = np.sqrt(np.diag(cov))
    llt = ll(nu, e, s2)
    lln = np.sum(stats.norm.logpdf(y - X @ np.linalg.lstsq(X, y, rcond=None)[0], scale=np.std(y - X @ np.linalg.lstsq(X, y, rcond=None)[0])))
    return dict(b=b, se=se, nu=nu, w=w, e=e, lr=2 * (llt - lln))


def hill(resid, frac):
    a = np.sort(np.abs(resid))[::-1]
    k = int(np.floor(frac * len(a)))
    if k < 1:
        return np.nan, k
    return 1.0 / np.mean(np.log(a[:k] / a[k])), k


def c3_run(df, label, record=True):
    y, x = df.share_pp.values, df.ln_rel_price.values
    n = len(y)
    f = ols_nw(y, x)
    b, se, p = f.params[1], f.bse[1], f.pvalues[1]
    lo, hi = block_boot_slope(y, x)
    res = f.resid
    rho = np.corrcoef(res[:-1], res[1:])[0, 1]
    neff = n * (1 - rho) / (1 + rho)
    tf = t_fit(y, x)
    bt, set_ = tf["b"][1], tf["se"][1]
    zt = bt / set_
    pt = 2 * (1 - stats.t.cdf(abs(zt), df=max(n - 2, 1)))
    h5, k5 = hill(tf["e"], 0.05)
    h10, k10 = hill(tf["e"], 0.10)
    low_w = pd.Series(tf["w"], index=df.index).nsmallest(min(5, n))
    kill = (b < 0 and p < 0.05) and (bt < 0 and pt < 0.05)
    one_only = ((b < 0 and p < 0.05) != (bt < 0 and pt < 0.05))
    sign_flip = np.sign(b) != np.sign(bt)
    move = abs(bt - b) / abs(b) if b != 0 else np.nan
    ta = "KILLED" if sign_flip else ("WEAK" if (one_only or ((p < 0.05) != (pt < 0.05)) or move > 0.25) else "HOLDS")
    out = dict(label=label, n=n, slope_ols=b, se_nw=se, p_nw=p, nw_lag=nw_lag(n), boot90=[lo, hi], rho_resid=rho, n_eff=neff,
               slope_t=bt, se_t=set_, p_t=pt, nu=tf["nu"], lr_t_vs_gauss=tf["lr"], hill_5pct=(h5, k5), hill_10pct=(h10, k10),
               lowest_weight_periods=[str(i.date()) for i in low_w.index], coef_move=move, tail_audit_label=ta,
               hypothesis_killed=bool(kill), r2=f.rsquared)
    if record:
        trial("C3", f"OLS-NW share on ln(P_A/P_O), {label}", "slope (pp per log point), p, n_eff", n, f"{b:.2f}, p={p:.3f}, n_eff={neff:.1f}")
        trial("C3", f"block bootstrap 90% CI, {label}", "slope CI", n, f"[{lo:.2f}, {hi:.2f}]")
        trial("C3", f"tail-audit t-fit, {label}", "slope, p, nu", n, f"{bt:.2f}, p={pt:.3f}, nu={tf['nu']:.1f}; {ta}")
    return out


RES["c3_levels"] = c3_run(C3, "levels, 4-week")
dC3 = C3.diff().dropna()
RES["c3_diffs"] = c3_run(dC3, "first differences, 4-week")

# weekly noise and the example jumps
sw = (spend_sh.Anthropic / (spend_sh.Anthropic + spend_sh.OpenAI) * 100)
dsw = sw.diff().dropna()
sd_w = float(dsw.loc[START:].std())
RES["c3_weekly_sd_pp"] = sd_w
RES["c3_weekly_sd_pp_2026"] = float(dsw.loc["2026-01-01":].std())
ex = []
raw_A = spend_sh.Anthropic
for a_, b_ in [(51.3, 60.5), (53.2, 49.3)]:
    hits = [(t0, t1) for t0, t1 in zip(raw_A.index[:-1], raw_A.index[1:]) if abs(raw_A[t0] - a_) < 0.051 and abs(raw_A[t1] - b_) < 0.051]
    hits_s = [(t0, t1) for t0, t1 in zip(sw.index[:-1], sw.index[1:]) if abs(sw[t0] - a_) < 0.051 and abs(sw[t1] - b_) < 0.051]
    if hits:
        t0, t1 = hits[0]
        chg = raw_A[t1] - raw_A[t0]
        basis = "Anthropic share of all token spend (raw column)"
    elif hits_s:
        t0, t1 = hits_s[0]
        chg = sw[t1] - sw[t0]
        basis = "A/(A+O) share"
    else:
        sd_raw_all = float(raw_A.diff().loc[START:].std())
        sd_raw_26 = float(raw_A.diff().loc["2026-01-01":].std())
        chg = b_ - a_
        ex.append(dict(example=f"{a_}% to {b_}%", found=False, note="values not present in current-vintage weekly data; stated move scored vs weekly noise",
                       change_pp=chg, sd_pp_full=sd_raw_all, sd_pp_2026=sd_raw_26, z_full=chg / sd_raw_all, z_2026=chg / sd_raw_26,
                       inside_noise_full=bool(abs(chg / sd_raw_all) < 2), inside_noise_2026=bool(abs(chg / sd_raw_26) < 2)))
        trial("C3", f"example jump {a_}% to {b_}% (not in current data; stated size vs noise)", "z vs weekly SD of Anthropic share, full / 2026", 0,
              f"z={chg / sd_raw_all:.2f} / {chg / sd_raw_26:.2f}")
        continue
    sd_raw = float(raw_A.diff().loc[START:].std()) if basis.startswith("Anthropic share of all") else sd_w
    z = chg / sd_raw
    ex.append(dict(example=f"{a_}% to {b_}%", found=True, weeks=f"{t0.date()} to {t1.date()}", basis=basis, change_pp=float(chg), sd_pp=sd_raw, z=float(z), inside_noise=bool(abs(z) < 2)))
    trial("C3", f"example jump {a_}% to {b_}%", "z vs weekly SD", 1, f"z={z:.2f} ({'inside' if abs(z) < 2 else 'outside'} noise)")
RES["c3_examples"] = ex

# ================================================================= C4
txt = re.sub(r"<[^>]+>", " ", (RAW / "01_anthropic_s1_filings" / "2026-11-19_Anthropic_424B4_final_prospectus_anthropicpbc-424b4.htm").read_text(errors="ignore"))
import html as _html

txt = re.sub(r"\s+", " ", _html.unescape(txt))
i0 = txt.find("Quarterly Consolidated Statements of Operations")
seg = txt[i0:i0 + 6000]


def grab(label_re, nvals=7):
    m = re.search(label_re + r"\s*((?:\(?\$?\s?[\d,]+\)?\s*){%d})" % nvals, seg)
    vals = re.findall(r"\(?\$?\s?([\d,]+)\)?", m.group(1))
    return [float(v.replace(",", "")) for v in vals[:nvals]]


Q = ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025", "Q1 2026", "Q2 2026", "Q3 2026"]
rev = grab(r"Revenue")
comp = grab(r"Compute and infrastructure")
C4 = pd.DataFrame({"quarter": Q, "revenue_musd": rev, "compute_infra_musd": comp})
C4["revenue_per_compute_dollar"] = C4.revenue_musd / C4.compute_infra_musd
C4["compute_margin_proxy"] = (C4.revenue_musd - C4.compute_infra_musd) / C4.revenue_musd
C4.to_csv(DATA / "c4_s1_quarterly_unit_economics.csv", index=False, float_format="%.4f")
r1, r3 = C4.revenue_per_compute_dollar.iloc[4], C4.revenue_per_compute_dollar.iloc[6]
m1, m3 = C4.compute_margin_proxy.iloc[4], C4.compute_margin_proxy.iloc[6]
rpc_trend = "falling" if r3 < 0.98 * r1 else "stable or rising"
mar_trend = "falling" if m3 < m1 - 0.02 else "stable or rising"
q2q3_rpc = C4.revenue_per_compute_dollar.iloc[6] / C4.revenue_per_compute_dollar.iloc[5] - 1
q2q3_mar = C4.compute_margin_proxy.iloc[6] - C4.compute_margin_proxy.iloc[5]
cut600 = 600 / (rev[6] - rev[5])
cut70 = 70 / (rev[3] - rev[2])
RES["c4"] = dict(table=C4.to_dict(orient="records"), rpc_trend_q1_to_q3_2026=rpc_trend, margin_trend_q1_to_q3_2026=mar_trend,
                 rpc_q2_to_q3_2026_change=float(q2q3_rpc), margin_q2_to_q3_2026_change_pp=float(q2q3_mar * 100),
                 price_cut_600_share_of_increase=float(cut600), price_cut_70_share_of_increase=float(cut70),
                 rev_increase_q2_q3_2026=rev[6] - rev[5], rev_increase_q3_q4_2025=rev[3] - rev[2])
trial("C4", "revenue per compute dollar, Q1 2026 vs Q3 2026 (pre-registered rule)", "ratio Q3/Q1", 3, f"{r1:.3f} -> {r3:.3f}: {rpc_trend}")
trial("C4", "compute margin proxy, Q1 2026 vs Q3 2026 (pre-registered rule)", "pp change", 3, f"{m1:.1%} -> {m3:.1%}: {mar_trend}")
trial("C4", "revenue per compute dollar, Q2 to Q3 2026 (reported alongside)", "pct change", 2, f"{q2q3_rpc:+.1%}")
trial("C4", "compute margin proxy, Q2 to Q3 2026 (reported alongside)", "pp change", 2, f"{q2q3_mar * 100:+.1f}pp")
trial("C4", "$600M price cut as share of Q2->Q3 2026 revenue increase", "ratio", 1, f"{cut600:.1%}")
trial("C4", "$70M price cut as share of Q3->Q4 2025 revenue increase", "ratio", 1, f"{cut70:.1%}")
m = re.search(r"approximately (\d+)% to (\d+)% of our revenue for the nine months ended September 30, 2026", txt)
RES["c4_policy_violation_revenue_pct"] = [int(m.group(1)), int(m.group(2))] if m else None

# ================================================================= C5 (descriptive)
orr = pd.read_csv(RAW / "06_openrouter_rankings" / "weekly_tokens_open_vs_closed_weights.csv", parse_dates=["period_start"])
orr["open_share"] = orr.open / (orr.open + orr.closed)
ramp_ao_tok = (vol_sh.Anthropic + vol_sh.OpenAI)
c5 = dict(first_week=str(orr.period_start.iloc[0].date()), first_open_share=float(orr.open_share.iloc[0]),
          last_week=str(orr.period_start.iloc[-1].date()), last_open_share=float(orr.open_share.iloc[-1]),
          ramp_ao_token_share_start=float(ramp_ao_tok.loc[:orr.period_start.iloc[0] + pd.Timedelta(days=6)].iloc[-1]),
          ramp_ao_token_share_latest=float(ramp_ao_tok.iloc[-1]))
RES["c5"] = c5
trial("C5", "OpenRouter open-weight share of tokens (descriptive)", "first vs last week", len(orr), f"{c5['first_open_share']:.1%} -> {c5['last_open_share']:.1%}")
trial("C5", "Ramp OpenAI+Anthropic token-volume share (descriptive)", "same window", 1, f"{c5['ramp_ao_token_share_start']:.1f}% -> {c5['ramp_ao_token_share_latest']:.1f}%")

# ================================================================= Revision robustness
CD = RAW / "03_ramp_ai_index_letters" / "chart_data"
rev_c1 = []
for f, lbl in [("qWoIn_v1_ai_spend_is_flat_as_usage_rises.csv", "Oct 2026 letter (qWoIn v1)"),
               ("7VRXW_v3_ai_spend_grows_but_usage_outpaces.csv", "Nov 2026 letter (7VRXW v3)")]:
    v = pd.read_csv(CD / f)
    v.columns = ["date", "vol", "spend"]
    v["date"] = pd.to_datetime(v.date)
    v = v.set_index("date")
    Ev = rolling_e(v.spend, v.vol)
    t = Ev.index[-1]
    cur = rolling_e(spend.loc[:t, "Combined"], vol.loc[:t, "Combined"]).iloc[-1]
    rv = "Jevons" if (Ev.dlnP.iloc[-1] < 0 and abs(Ev.e.iloc[-1]) > 1) else ("crack" if Ev.dlnP.iloc[-1] < 0 else "price not falling")
    rc = "Jevons" if (cur.dlnP < 0 and abs(cur.e) > 1) else ("crack" if cur.dlnP < 0 else "price not falling")
    rev_c1.append(dict(vintage=lbl, week=str(t.date()), e_vintage=float(Ev.e.iloc[-1]), reading_vintage=rv, e_current=float(cur.e), reading_current=rc, flip=rv != rc))
    trial("Revision", f"C1 13-week e at vintage last week, {lbl}", "vintage vs current", 1, f"{Ev.e.iloc[-1]:.2f} ({rv}) vs {cur.e:.2f} ({rc})")
RES["revision_c1"] = rev_c1

rev_c3 = []
for f, lbl in [("0lGNa_v2_ai_token_prices_are_falling.csv", "Sep 2026 letter (0lGNa v2)"), ("DUO9V_v3_ai_token_prices_are_falling.csv", "Oct 2026 letter (DUO9V v3)")]:
    v = pd.read_csv(CD / f, parse_dates=["Date"]).set_index("Date")
    keep = [(a, b) for a, b in zip(blk_start, blk_end) if a >= v.index.min() and b <= v.index.max()]
    if len(keep) < 4:
        rev_c3.append(dict(vintage=lbl, n=len(keep), note="too few overlapping blocks"))
        continue
    A_, B_ = zip(*keep)
    pv = block_mean_prices(v, A_, B_)
    dfv = pd.DataFrame({"share_pp": sh4.loc[pd.to_datetime(B_)], "ln_rel_price": np.log(pv.Anthropic / pv.OpenAI)}).dropna()
    dfc = C3.loc[dfv.index]
    rv = c3_run(dfv, f"revision {lbl}", record=False)
    rc = c3_run(dfc, f"current data, same blocks as {lbl}", record=False)
    rev_c3.append(dict(vintage=lbl, n=len(dfv), slope_vintage=rv["slope_ols"], p_vintage=rv["p_nw"], killed_vintage=rv["hypothesis_killed"],
                       slope_current_same_blocks=rc["slope_ols"], p_current_same_blocks=rc["p_nw"], killed_current_same_blocks=rc["hypothesis_killed"],
                       killed_full_sample=RES["c3_levels"]["hypothesis_killed"],
                       flip=rv["hypothesis_killed"] != RES["c3_levels"]["hypothesis_killed"],
                       mean_abs_ln_rel_price_gap=float((dfv.ln_rel_price - dfc.ln_rel_price).abs().mean())))
    trial("Revision", f"C3 on vintage prices, {lbl}", "slope, p, killed?", len(dfv), f"{rv['slope_ols']:.2f}, p={rv['p_nw']:.3f}, killed={rv['hypothesis_killed']}")
RES["revision_c3"] = rev_c3

# ================================================================= Verdict
e_ok = RES["c1_Combined"]["dlnP"] < 0
abs_e = RES["c1_Combined"]["latest_abs_e"]
lfl = c2["Combined|combined March peak"]["like_for_like_share"]
mixs = c2["Combined|combined March peak"]["mix_share"]
c4_fall = (rpc_trend == "falling") or (mar_trend == "falling")
c4_ok = (rpc_trend == "stable or rising") and (mar_trend == "stable or rising")
holds = e_ok and abs_e < 1 and c4_fall and (lfl >= 0.5)
killed = e_ok and abs_e > 1 and c4_ok and (mixs >= 0.5)
flip_any = any(r["flip"] for r in rev_c1) or any(r.get("flip", False) for r in rev_c3)
verdict = "HOLDS" if holds else ("KILLED" if killed else "WEAK")
if verdict in ("HOLDS", "KILLED") and flip_any:
    verdict = "WEAK"
RES["verdict"] = dict(label=verdict, c1_abs_e=abs_e, c1_price_falling=bool(e_ok), c4_rpc_trend=rpc_trend, c4_margin_trend=mar_trend,
                      c2_like_for_like_share=lfl, c2_mix_share=mixs, revision_flip=bool(flip_any),
                      conditions_holds=[bool(e_ok and abs_e < 1), bool(c4_fall), bool(lfl >= 0.5)],
                      conditions_killed=[bool(e_ok and abs_e > 1), bool(c4_ok), bool(mixs >= 0.5)])
trial("Verdict", "pre-registered rule", "HOLDS/KILLED/WEAK conditions", 1, verdict)
lfl_x = c2x["Combined"]["like_for_like_share"]
killed_x = e_ok and abs_e > 1 and c4_ok and (1 - lfl_x >= 0.5)
holds_x = e_ok and abs_e < 1 and c4_fall and (lfl_x >= 0.5)
verdict_x = "HOLDS" if holds_x else ("KILLED" if killed_x else "WEAK")
RES["verdict_sensitivity_tier_linked"] = dict(label=verdict_x, like_for_like_share=lfl_x)
trial("Verdict", "sensitivity: C2 replaced by tier-linked index (exploratory)", "label", 1, verdict_x)
# sensitivity: C1 on Anthropic alone and the deceleration of |e|
RES["c1_trend_last8"] = {lab: [round(float(v), 3) for v in E[lab].e.iloc[-8:]] for lab in ["Combined", "Anthropic", "OpenAI"]}

# ================================================================= Charts
# 1 price index decomposition (combined)
path, uv = paths["Combined"]
uvi = uv.loc[path.index] / uv.loc[path.index[0]] * 100
fi = np.exp(path.ln_fisher) * 100
fig, ax = plt.subplots(figsize=(9, 5), dpi=200)
ax.plot(uvi.index, uvi.values, color=BLUE, lw=2, label="Blended price of covered models (unit value)")
ax.plot(fi.index, fi.values, color=ORANGE, lw=2, label="Like-for-like, same model version (chain Fisher, pre-registered)")
ti = np.exp(tier_path_combined.ln_fisher) * 100
ax.plot(ti.index, ti.values, color=AQUA, lw=2, ls="--", label="Like-for-like, successor = same tier (exploratory)")
ax.annotate(f"{ti.iloc[-1] - 100:+.0f}%", (ti.index[-1], ti.iloc[-1]), xytext=(4, 0), textcoords="offset points", va="center", color=INK, fontsize=9)
ax.axhline(100, color=INK2, lw=0.8)
ax.annotate(f"{uvi.iloc[-1] - 100:+.0f}%", (uvi.index[-1], uvi.iloc[-1]), xytext=(4, 0), textcoords="offset points", va="center", color=INK, fontsize=9)
ax.annotate(f"{fi.iloc[-1] - 100:+.0f}%", (fi.index[-1], fi.iloc[-1]), xytext=(4, 0), textcoords="offset points", va="center", color=INK, fontsize=9)
ttl = (f"Since the March peak the average price of covered models moved {uvi.iloc[-1] - 100:+.0f}%. Same-version prices moved {fi.iloc[-1] - 100:+.0f}%,"
       f"\nbut counting successors as the same tier they moved {ti.iloc[-1] - 100:+.0f}% (models with >=0.5% token share, base {BASE.date()} = 100)")
ax.set_title(ttl, loc="left", fontsize=10, color=INK)
ax.set_ylabel("Index, base week = 100", color=INK2)
style(ax)
ax.legend(frameon=False, fontsize=9)
fig.tight_layout()
fig.savefig(OUT / "chart_price_index_decomposition.png")
plt.close(fig)

# 2 rolling elasticity
fig, ax = plt.subplots(figsize=(9, 5), dpi=200)
for lab, col in [("Combined", INK), ("Anthropic", ORANGE), ("OpenAI", BLUE)]:
    e_ = E[lab].e.where(E[lab].dlnP <= -0.05)  # e is unstable when the price barely moves
    ax.plot(e_.index, e_.values, color=col, lw=2 if lab == "Combined" else 1.2, label=lab)
ax.axhline(-1, color=INK2, lw=0.9, ls="--")
ax.text(E["Combined"].index[-1], -0.85, "e = -1: below this line spend rises as price falls", color=INK2, fontsize=8, va="bottom", ha="right")
ax.axhline(0, color=INK2, lw=0.6)
ax.set_ylabel("Realised elasticity e = dln(volume) / dln(price)", color=INK2)
ax.set_title(f"Spend still rises as prices fall, but less each week: combined e moved from {RES['c1_trend_last8']['Combined'][0]:.2f} to {RES['c1_Combined']['latest_e']:.2f} in 8 weeks"
             f"\n(realised 13-week elasticity, not causal; shown only where the 13-week price fell 5% or more)", loc="left", fontsize=10, color=INK)
style(ax)
ax.legend(frameon=False, fontsize=9)
fig.tight_layout()
fig.savefig(OUT / "chart_rolling_elasticity.png")
plt.close(fig)

# 3 share vs relative price
fig, ax = plt.subplots(figsize=(7.5, 5.5), dpi=200)
ax.scatter(C3.ln_rel_price, C3.share_pp, s=40, color=BLUE, edgecolor="white", linewidth=1.5, zorder=3)
for t in [C3.index[0], C3.index[-1]]:
    ax.annotate(str(t.date()), (C3.ln_rel_price[t], C3.share_pp[t]), xytext=(5, 5), textcoords="offset points", fontsize=8, color=INK2)
xx = np.linspace(C3.ln_rel_price.min(), C3.ln_rel_price.max(), 50)
L3 = RES["c3_levels"]
ax.plot(xx, ols_nw(C3.share_pp.values, C3.ln_rel_price.values).params[0] + L3["slope_ols"] * xx, color=ORANGE, lw=1.5)
ax.set_xlabel("ln(Anthropic price / OpenAI price), 4-week mean", color=INK2)
ax.set_ylabel("Anthropic share of A+O token spend (%)", color=INK2)
ax.set_title(f"Share vs relative price: slope {L3['slope_ols']:.1f}pp per log point (NW p={L3['p_nw']:.2f}), n={L3['n']}, effective n={L3['n_eff']:.1f}",
             loc="left", fontsize=9.5, color=INK)
style(ax)
fig.tight_layout()
fig.savefig(OUT / "chart_share_vs_relative_price.png")
plt.close(fig)

# 4 S-1 quarterly economics (two panels, one axis each)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6), dpi=200)
xq = np.arange(len(C4))
a1.bar(xq - 0.2, C4.revenue_musd / 1000, width=0.38, color=BLUE, label="Revenue")
a1.bar(xq + 0.2, C4.compute_infra_musd / 1000, width=0.38, color=ORANGE, label="Compute and infrastructure")
a1.set_xticks(xq, C4.quarter, rotation=45, fontsize=8)
a1.set_ylabel("$ billions", color=INK2)
a1.legend(frameon=False, fontsize=8)
a1.set_title("Revenue overtook compute cost in 2026", loc="left", fontsize=10, color=INK)
style(a1)
a2.plot(xq, C4.revenue_per_compute_dollar, color=INK, lw=2, marker="o", ms=5)
for i, v in enumerate(C4.revenue_per_compute_dollar):
    a2.annotate(f"{v:.2f}", (i, v), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=8, color=INK)
a2.set_xticks(xq, C4.quarter, rotation=45, fontsize=8)
a2.set_ylabel("Revenue per $ of compute and infrastructure", color=INK2)
a2.set_title(f"Revenue per compute dollar peaked in Q2 2026, then fell {abs(q2q3_rpc):.0%} in Q3", loc="left", fontsize=10, color=INK)
style(a2)
fig.tight_layout()
fig.savefig(OUT / "chart_s1_quarterly_economics.png")
plt.close(fig)

# ================================================================= write
with open(OUT / "trials.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(TRIALS[0].keys()))
    w.writeheader()
    w.writerows(TRIALS)


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if np.isnan(o) else round(float(o), 6)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (pd.Timestamp, dt.date)):
        return str(o)
    return o


(OUT / "results.json").write_text(json.dumps(clean(RES), indent=1))
print(json.dumps(clean(RES["verdict"]), indent=1))
print(f"trials: {len(TRIALS)}")
