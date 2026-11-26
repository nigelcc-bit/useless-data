"""MU regime read: 2-state Gaussian HMM, filtered vs smoothed, Kalman beta.

Run from this folder:  python3 run.py
Inputs: data/adj_close.csv (MU, SOXX, SPY adjusted closes from Yahoo).
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from scipy.stats import multivariate_normal

warnings.filterwarnings("ignore")
import logging
logging.getLogger("hmmlearn").setLevel(logging.ERROR)
HERE = Path(__file__).parent
OUT = HERE / "outputs"
OUT.mkdir(exist_ok=True)

SAMPLE_START = "2010-01-04"
OOS_START = "2013-01-02"
REFIT_EVERY = 63
N_STARTS = 20
TRIALS: list[dict] = []


# ---------------------------------------------------------------- features
def expanding_z(s: pd.Series, min_periods: int = 200) -> pd.Series:
    m = s.expanding(min_periods).mean()
    sd = s.expanding(min_periods).std()
    return (s - m) / sd


def build_features(px: pd.DataFrame, variant: str) -> pd.DataFrame:
    r = np.log(px["MU"]).diff()
    win = 10 if variant == "R4" else 21
    rv = r.rolling(win).std() * np.sqrt(252)
    f = {"r": expanding_z(r)}
    if variant != "R2":
        f["rv"] = expanding_z(rv)
    if variant == "R3":
        rs = np.log(px["SOXX"]).diff()
        f["rv_soxx"] = expanding_z(rs.rolling(21).std() * np.sqrt(252))
    F = pd.DataFrame(f)
    F["rv_raw"] = rv
    F["ret"] = r
    return F.loc[SAMPLE_START:].dropna()


# ---------------------------------------------------------------- HMM
def fit_best(X: np.ndarray, k: int, n_starts: int = N_STARTS):
    fits = []
    for seed in range(n_starts):
        m = GaussianHMM(n_components=k, covariance_type="full", n_iter=500,
                        tol=1e-5, random_state=seed, min_covar=1e-4)
        try:
            m.fit(X)
            fits.append((m.score(X), seed, m))
        except Exception:  # noqa: BLE001
            continue
    fits.sort(key=lambda t: -t[0])
    return fits


def stress_index(m: GaussianHMM, X: np.ndarray, rv_raw: np.ndarray) -> int:
    """Label by volatility: state whose assigned days have the highest mean raw vol."""
    post = m.predict_proba(X)
    w = post / post.sum(0)
    vol = (w * rv_raw[:, None]).sum(0)
    return int(np.argmax(vol))


def forward_filter(m: GaussianHMM, X: np.ndarray, prior: np.ndarray | None = None):
    """Pure forward recursion: P(state_t | X_1..t). No future data."""
    k = m.n_components
    B = np.column_stack([multivariate_normal(m.means_[j], m.covars_[j],
                                             allow_singular=True).pdf(X) for j in range(k)])
    alpha = np.zeros((len(X), k))
    a = (m.startprob_ if prior is None else prior @ m.transmat_) * B[0]
    alpha[0] = a / a.sum()
    for t in range(1, len(X)):
        a = (alpha[t - 1] @ m.transmat_) * B[t]
        s = a.sum()
        alpha[t] = a / s if s > 0 else alpha[t - 1]
    return alpha


def oos_filtered(F: pd.DataFrame, cols, k: int, n_starts: int) -> pd.Series:
    X = F[cols].values
    rv = F["rv_raw"].values
    idx = F.index
    start = idx.searchsorted(pd.Timestamp(OOS_START))
    out = pd.Series(np.nan, index=idx)
    prior = None
    t = start
    while t < len(idx):
        fits = fit_best(X[:t], k, n_starts)
        m = fits[0][2]
        si = stress_index(m, X[:t], rv[:t])
        # filter from start through t+REFIT_EVERY with frozen params; keep only the new block
        end = min(t + REFIT_EVERY, len(idx))
        alpha = forward_filter(m, X[:end])
        out.iloc[t:end] = alpha[t:end, si]
        t = end
    return out


def spells(p: pd.Series, thr: float = 0.5, gap: int = 5):
    on = (p > thr).values
    runs, i, n = [], 0, len(on)
    while i < n:
        if on[i]:
            j = i
            while j < n and on[j]:
                j += 1
            runs.append([i, j - 1])
            i = j
        else:
            i += 1
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] - 1 <= gap:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [(p.index[a], p.index[b], b - a + 1) for a, b in merged]


def boot_median_ci(x, n=5000, seed=0):
    rng = np.random.default_rng(seed)
    x = np.asarray(x)
    meds = np.median(rng.choice(x, size=(n, len(x)), replace=True), axis=1)
    return np.percentile(meds, [5, 95])


def toy_backtest(p: pd.Series, ret: pd.Series):
    pos = (p.shift(1) < 0.5).astype(float)
    pnl = (pos * ret).dropna()
    ann = pnl.mean() * 252
    vol = pnl.std() * np.sqrt(252)
    return {"cagr_log": float(ann), "sharpe": float(ann / vol), "time_in_mkt": float(pos.mean())}


# ---------------------------------------------------------------- Kalman beta
def kalman_beta(y: pd.Series, x: pd.Series, delta=1e-4, R=None):
    q = delta / (1 - delta)
    b, P = 1.0, 1.0
    out = []
    for yt, xt in zip(y.values, x.values):
        P = P + q
        S = xt * P * xt + R
        K = P * xt / S
        b = b + K * (yt - xt * b)
        P = (1 - K * xt) * P
        out.append((b, np.sqrt(P)))
    return pd.DataFrame(out, index=y.index, columns=["beta", "sd"])


# ---------------------------------------------------------------- main
def run_variant(px, variant, k, n_starts):
    F = build_features(px, variant)
    cols = [c for c in F.columns if c not in ("rv_raw", "ret")]
    filt = oos_filtered(F, cols, k, n_starts).dropna()
    return F, cols, filt


def main():
    px = pd.read_csv(HERE / "data/adj_close.csv", index_col=0, parse_dates=True)
    results = {}

    # ---------------- P0 primary
    F, cols, filt = run_variant(px, "P0", 2, N_STARTS)
    X = F[cols].values
    full = fit_best(X, 2, N_STARTS)
    best_ll, _, m_full = full[0]
    si = stress_index(m_full, X, F["rv_raw"].values)
    occupancy = m_full.predict_proba(X).mean(0)
    smooth = pd.Series(m_full.predict_proba(X)[:, si], index=F.index)
    filt_full = pd.Series(forward_filter(m_full, X)[:, si], index=F.index)

    # state descriptions (full-sample, descriptive)
    post = m_full.predict_proba(X)
    desc = {}
    for j, name in [(si, "stress"), (1 - si, "calm")]:
        w = post[:, j] / post[:, j].sum()
        desc[name] = {"mean_daily_logret_pct": float((w * F["ret"].values).sum() * 100),
                      "mean_rv_ann_pct": float((w * F["rv_raw"].values).sum() * 100),
                      "occupancy": float(occupancy[j]),
                      "stay_prob": float(m_full.transmat_[j, j]),
                      "implied_mean_duration_days": float(1 / (1 - m_full.transmat_[j, j]))}

    # start stability: each converged start's current filtered P(stress)
    stab = []
    for ll, seed, m in full:
        if ll >= best_ll - abs(best_ll) * 0.01:
            s = stress_index(m, X, F["rv_raw"].values)
            stab.append(float(forward_filter(m, X)[-1, s]))
    stab = np.array(stab)

    # current read on OOS filtered series
    p_now = float(filt.iloc[-1])
    above08 = (filt > 0.8).values[::-1]
    consec_08 = int(np.argmin(above08)) if not above08.all() else len(above08)
    sp = spells(filt)
    in_stress = p_now > 0.5
    cur = sp[-1] if (sp and in_stress and sp[-1][1] == filt.index[-1]) else None
    past = [s for s in sp if cur is None or s != cur]
    durs = np.array([s[2] for s in past])
    med_ci = boot_median_ci(durs) if len(durs) >= 3 else [np.nan, np.nan]
    pct_rank = float((durs < cur[2]).mean()) if cur else np.nan
    last_switch = None
    flips = np.where(np.diff((filt > 0.5).astype(int).values) != 0)[0]
    if len(flips):
        last_switch = filt.index[flips[-1] + 1]
    days_since_switch = int(len(filt.loc[last_switch:]) - 1) if last_switch is not None else None

    # look-ahead gap
    common = filt.index.intersection(smooth.index)
    fc, sc = filt.loc[common] > 0.5, smooth.loc[common] > 0.5
    disagree = int((fc != sc).sum())
    bt_f = toy_backtest(filt, F["ret"])
    bt_s = toy_backtest(smooth.loc[common], F["ret"])
    bt_bh = {"cagr_log": float(F["ret"].loc[common].mean() * 252),
             "sharpe": float(F["ret"].loc[common].mean() / F["ret"].loc[common].std() * np.sqrt(252))}

    # recent path (for the selloff)
    recent = pd.DataFrame({"price": px["MU"].reindex(filt.index), "p_filt": filt,
                           "p_smooth": smooth.reindex(filt.index)}).loc["2026-01-01":]
    recent.round(4).to_csv(OUT / "recent_probs_2026.csv")

    results["P0"] = {
        "best_ll": float(best_ll), "converged_starts": int(len(stab)), "starts": len(full),
        "occupancy": occupancy.tolist(), "states": desc,
        "p_stress_now_oos": p_now, "p_stress_now_fullfit_filtered": float(filt_full.iloc[-1]),
        "p_stress_now_smoothed": float(smooth.iloc[-1]),
        "stability_p_now": {"min": float(stab.min()), "max": float(stab.max()),
                            "share_above_0.5": float((stab > 0.5).mean())},
        "consecutive_sessions_p_gt_0.8": consec_08,
        "last_switch": str(last_switch.date()) if last_switch is not None else None,
        "days_since_switch": days_since_switch,
        "current_spell": [str(cur[0].date()), str(cur[1].date()), cur[2]] if cur else None,
        "past_spells_n": int(len(durs)), "past_median": float(np.median(durs)) if len(durs) else None,
        "past_median_ci90": [float(x) for x in med_ci],
        "past_p75": float(np.percentile(durs, 75)) if len(durs) else None,
        "past_max": int(durs.max()) if len(durs) else None,
        "current_spell_pct_rank": pct_rank,
        "lookahead_disagree_days": disagree, "lookahead_n": int(len(common)),
        "bt_filtered": bt_f, "bt_smoothed": bt_s, "bt_buyhold": bt_bh,
    }
    pd.DataFrame(sp, columns=["start", "end", "sessions"]).to_csv(OUT / "stress_spells_P0.csv", index=False)
    TRIALS.append({"id": "P0", "desc": "2-state, z(r), z(rv21)", "p_now": p_now,
                   "consec_gt_0.8": consec_08, "spell_len": cur[2] if cur else 0,
                   "past_p75": results["P0"]["past_p75"]})

    # ---------------- Kalman beta vs SOXX
    r = np.log(px[["MU", "SOXX"]]).diff().loc[SAMPLE_START:].dropna()
    tr = r.loc[:"2012-12-31"]
    b_ols = np.polyfit(tr["SOXX"], tr["MU"], 1)[0]
    R = float(np.var(tr["MU"] - b_ols * tr["SOXX"]))
    kb = kalman_beta(r["MU"], r["SOXX"], R=R)
    cov = r["MU"].rolling(63).cov(r["SOXX"])
    roll = cov / r["SOXX"].rolling(63).var()
    kb["roll63"] = roll
    kb.to_csv(OUT / "kalman_beta.csv")
    results["kalman"] = {"beta_now": float(kb["beta"].iloc[-1]), "band": float(2 * kb["sd"].iloc[-1]),
                         "roll63_now": float(roll.iloc[-1]),
                         "beta_median_2010_2025": float(kb["beta"].loc[:"2025-12-31"].median()),
                         "beta_at_peak_2026_06_25": float(kb["beta"].loc["2026-06-25"]),
                         "R": R}

    # ---------------- robustness
    for vid, k, desc_ in [("R1", 3, "3-state, z(r), z(rv21)"), ("R2", 2, "2-state, z(r) only"),
                          ("R3", 2, "2-state, + z(SOXX rv21)"), ("R4", 2, "2-state, z(r), z(rv10)")]:
        Fv, cv, fv = run_variant(px, "P0" if vid == "R1" else vid, k, 10)
        spv = spells(fv)
        pv = float(fv.iloc[-1])
        a = (fv > 0.8).values[::-1]
        c8 = int(np.argmin(a)) if not a.all() else len(a)
        curv = spv[-1] if (spv and pv > 0.5 and spv[-1][1] == fv.index[-1]) else None
        dv = np.array([s[2] for s in spv if s != curv])
        TRIALS.append({"id": vid, "desc": desc_, "p_now": pv, "consec_gt_0.8": c8,
                       "spell_len": curv[2] if curv else 0,
                       "past_p75": float(np.percentile(dv, 75)) if len(dv) else None})
        if vid == "R1":
            results["R1_recent"] = {str(k.date()): v for k, v in fv.loc["2026-06-01":].resample("ME").last().round(3).items()}

    # ---------------- chart
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(11, 8), sharex=True,
                                     gridspec_kw={"height_ratios": [2.2, 1, 1]})
    p = px["MU"].reindex(filt.index)
    a1.semilogy(p.index, p, color="#2b2b2b", lw=0.9)
    for s0, s1, _ in sp:
        a1.axvspan(s0, s1, color="#d9534f", alpha=0.18, lw=0)
    a1.set_ylabel("MU adj close (log)")
    a2.fill_between(filt.index, filt, color="#d9534f", alpha=0.6, lw=0, label="filtered (out of sample)")
    a2.plot(smooth.loc[filt.index[0]:].index, smooth.loc[filt.index[0]:], color="#337ab7", lw=0.5,
            alpha=0.8, label="smoothed (look-ahead)")
    a2.axhline(0.8, color="k", ls=":", lw=0.7)
    a2.set_ylabel("P(stress)")
    a2.legend(loc="upper left", fontsize=7, frameon=False)
    a3.plot(kb.loc[filt.index[0]:].index, kb["beta"].loc[filt.index[0]:], color="#5cb85c", lw=0.9,
            label="Kalman beta vs SOXX")
    a3.plot(roll.loc[filt.index[0]:].index, roll.loc[filt.index[0]:], color="grey", lw=0.5, alpha=0.6,
            label="63d rolling OLS")
    a3.set_ylabel("beta")
    a3.legend(loc="upper left", fontsize=7, frameon=False)
    P0 = results["P0"]
    cur_len = P0["current_spell"][2] if P0["current_spell"] else 0
    title = (f"MU high-vol state since {P0['last_switch']}: {cur_len} sessions vs past p75 of "
             f"{P0['past_p75']:.0f} (filtered P(stress) now {P0['p_stress_now_oos']:.2f})")
    fig.suptitle(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "regime_strip.png", dpi=150)

    # zoom chart for 2026
    fig, (b1, b2) = plt.subplots(2, 1, figsize=(10, 5), sharex=True)
    rz = recent
    b1.plot(rz.index, rz["price"], color="#2b2b2b")
    b1.set_ylabel("MU")
    b2.fill_between(rz.index, rz["p_filt"], color="#d9534f", alpha=0.6, lw=0, label="filtered")
    b2.plot(rz.index, rz["p_smooth"], color="#337ab7", lw=0.8, label="smoothed")
    b2.axhline(0.8, color="k", ls=":", lw=0.7)
    b2.legend(fontsize=7, frameon=False)
    fig.suptitle("2026 zoom: MU price and P(stress)", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "regime_strip_2026.png", dpi=150)

    pd.DataFrame(TRIALS).to_csv(OUT / "trials.csv", index=False)
    (OUT / "results.json").write_text(json.dumps(results, indent=2, default=str))
    print(json.dumps(results, indent=2, default=str))
    print(pd.DataFrame(TRIALS).to_string())


if __name__ == "__main__":
    main()
