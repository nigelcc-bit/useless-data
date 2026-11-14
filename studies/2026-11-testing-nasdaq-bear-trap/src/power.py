"""N01: minimum detectable effect (MDE) and TOST equivalence for Study 1 reclaim returns.

Specification: PREREG/N01_power.md (committed before this module was run).

Inputs are the Study 1 event lists in tests/fixtures (Appendix B/C, returns
rounded to 0.1 point). The drawdown-matched benchmark means are the Study 1
Table 7.3 values, treated as known constants.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = {"NDX": ROOT / "tests" / "fixtures" / "expected_ndx_events.csv",
            "SPX": ROOT / "tests" / "fixtures" / "expected_spx_events.csv"}
HORIZONS = (20, 60, 120)

# Study 1 Table 7.3, drawdown-matched column (days 5-20% below the 120-day high).
BENCHMARK_MEANS = {
    "NDX": {20: 0.016, 60: 0.050, 120: 0.100},
    "SPX": {20: 0.007, 60: 0.019, 120: 0.036},
}
# Study 1 Table 7.3 "after reclaim" and Table 7.2 counts: anchors only.
REPORTED_RECLAIM_MEANS = {
    "NDX": {20: 0.015, 60: 0.046, 120: 0.116},
    "SPX": {20: 0.005, 60: 0.020, 120: 0.037},
}
REPORTED_RECLAIMED = {"NDX": 37, "SPX": 67}
ANCHOR_TOL = 0.0011          # 0.11 point: rounding of report and fixtures

ALPHA = 0.05
POWER = 0.80
BONFERRONI_STUDY1 = 0.05 / 36
BOUNDS = (0.02, 0.05)
R_SIMS = 10_000
SEED = 7
TOL = 0.0005
CROSSCHECK_TOL = 0.002


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
def load_study1_events(index: str) -> pd.DataFrame:
    """Study 1 event list for NDX or SPX (all breaks, reclaimed or not)."""
    df = pd.read_csv(FIXTURES[index], parse_dates=["break_date", "entry_date"])
    df["reclaimed"] = df["reclaimed"].astype(bool)
    df.insert(0, "index", index)
    return df


def reclaim_returns(events: pd.DataFrame, h: int) -> np.ndarray:
    """Forward h-day returns of reclaimed events with a full window."""
    x = events.loc[events["reclaimed"], f"r{h}"].dropna()
    return x.to_numpy(float)


def sample_stats(x) -> dict:
    x = np.asarray(x, float)
    return dict(n=int(x.size), mean=float(x.mean()), sd=float(x.std(ddof=1)))


def check_anchors(events_by_index: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Compare fixture means/counts with Study 1 tables. Raises if any fails."""
    rows = []
    for ix, ev in events_by_index.items():
        n_rec = int(ev["reclaimed"].sum())
        rows.append(dict(index=ix, item="reclaimed count", got=n_rec,
                         reported=REPORTED_RECLAIMED[ix], ok=n_rec == REPORTED_RECLAIMED[ix]))
        for h in HORIZONS:
            m = float(reclaim_returns(ev, h).mean())
            rep = REPORTED_RECLAIM_MEANS[ix][h]
            rows.append(dict(index=ix, item=f"mean r{h}", got=round(m, 5), reported=rep,
                             ok=abs(m - rep) <= ANCHOR_TOL))
    out = pd.DataFrame(rows)
    if not out["ok"].all():
        raise AssertionError("N01 anchor check failed:\n" + out[~out["ok"]].to_string(index=False))
    return out


# ----------------------------------------------------------------------------
# Power and MDE
# ----------------------------------------------------------------------------
def power_analytic(delta: float, n: int, sd: float, alpha: float = ALPHA) -> float:
    """Exact power of the one-sided one-sample t-test (noncentral t)."""
    df = n - 1
    crit = stats.t.ppf(1 - alpha, df)
    return float(stats.nct.sf(crit, df, delta / (sd / np.sqrt(n))))


def mde_analytic(n: int, sd: float, alpha: float = ALPHA, power: float = POWER) -> float:
    return float(brentq(lambda d: power_analytic(d, n, sd, alpha) - power, 1e-9, 10 * sd))


def _draws(n: int, R: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).standard_normal((R, n))


def power_simulated(delta: float, n: int, sd: float, alpha: float = ALPHA,
                    R: int = R_SIMS, seed: int = SEED, Z: np.ndarray | None = None) -> float:
    """Share of simulated Normal(mu0 + delta, sd) samples that reject H0: mean <= mu0.

    Works in excess-return units (mu0 = 0). Pass Z to reuse common random numbers.
    """
    Z = _draws(n, R, seed) if Z is None else Z
    X = delta + sd * Z
    t = X.mean(axis=1) / (X.std(axis=1, ddof=1) / np.sqrt(n))
    return float((t > stats.t.ppf(1 - alpha, n - 1)).mean())


def mde_simulated(n: int, sd: float, alpha: float = ALPHA, power: float = POWER,
                  R: int = R_SIMS, seed: int = SEED, lo: float = 0.0, hi: float = 1.0,
                  tol: float = TOL) -> float:
    """Smallest delta (bisection, common random numbers) with simulated power >= `power`."""
    Z = _draws(n, R, seed)
    if power_simulated(hi, n, sd, alpha, Z=Z) < power:
        raise ValueError(f"power < {power} even at delta = {hi}")
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if power_simulated(mid, n, sd, alpha, Z=Z) >= power:
            hi = mid
        else:
            lo = mid
    return hi


def mde_table(events_by_index: dict[str, pd.DataFrame], R: int = R_SIMS,
              seed: int = SEED) -> pd.DataFrame:
    rows = []
    for ix, ev in events_by_index.items():
        for h in HORIZONS:
            s = sample_stats(reclaim_returns(ev, h))
            sim = mde_simulated(s["n"], s["sd"], ALPHA, POWER, R, seed)
            exact = mde_analytic(s["n"], s["sd"], ALPHA, POWER)
            if abs(sim - exact) > CROSSCHECK_TOL:
                raise AssertionError(f"{ix} r{h}: simulated MDE {sim:.4f} vs exact {exact:.4f}")
            rows.append(dict(
                index=ix, horizon=f"r{h}", n=s["n"], sd=s["sd"], reclaim_mean=s["mean"],
                benchmark_mean=BENCHMARK_MEANS[ix][h],
                mde_sim=sim, mde_exact=exact, mde_sd_units=sim / s["sd"],
                mde_bonf_exact=mde_analytic(s["n"], s["sd"], BONFERRONI_STUDY1, POWER),
                detectable_mean=BENCHMARK_MEANS[ix][h] + sim,
            ))
    return pd.DataFrame(rows)


def format_mde_table(t: pd.DataFrame) -> pd.DataFrame:
    """Human-readable version (percentage points)."""
    pct = lambda v: f"{v * 100:+.1f}%"  # noqa: E731
    pts = lambda v: f"{v * 100:.2f}"    # noqa: E731
    return pd.DataFrame({
        "Index": t["index"], "Horizon": t["horizon"], "n": t["n"],
        "SD (pts)": t["sd"].map(pts),
        "Reclaim mean": t["reclaim_mean"].map(pct),
        "Benchmark": t["benchmark_mean"].map(pct),
        "MDE sim (pts)": t["mde_sim"].map(pts),
        "MDE exact (pts)": t["mde_exact"].map(pts),
        "MDE / SD": t["mde_sd_units"].map(lambda v: f"{v:.2f}"),
        "MDE @0.00139 (pts)": t["mde_bonf_exact"].map(pts),
    })


def power_curve(n: int, sd: float, deltas, alpha: float = ALPHA) -> np.ndarray:
    return np.array([power_analytic(d, n, sd, alpha) for d in deltas])


# ----------------------------------------------------------------------------
# TOST
# ----------------------------------------------------------------------------
def tost(x, mu0: float, bound: float, alpha: float = ALPHA) -> dict:
    """Two one-sided t-tests for |mean(x) - mu0| < bound."""
    s = sample_stats(x)
    n, df = s["n"], s["n"] - 1
    d = s["mean"] - mu0
    se = s["sd"] / np.sqrt(n)
    p_lower = float(stats.t.sf((d + bound) / se, df))     # H0a: d <= -bound
    p_upper = float(stats.t.cdf((d - bound) / se, df))    # H0b: d >= +bound
    tq = stats.t.ppf(1 - alpha, df)
    p = max(p_lower, p_upper)
    return dict(n=n, diff=d, se=se, ci90_lo=d - tq * se, ci90_hi=d + tq * se,
                bound=bound, p_lower=p_lower, p_upper=p_upper, p_tost=p,
                equivalent=bool(p < alpha))


def bh_qvalues(p) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values."""
    p = np.asarray(p, float)
    m = p.size
    order = np.argsort(p)
    ranked = p[order] * m / np.arange(1, m + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(q, 1.0)
    return out


def tost_table(events_by_index: dict[str, pd.DataFrame], bounds=BOUNDS,
               alpha: float = ALPHA, fdr_q: float = 0.10) -> pd.DataFrame:
    rows = []
    for ix, ev in events_by_index.items():
        for h in HORIZONS:
            x = reclaim_returns(ev, h)
            for b in bounds:
                rows.append(dict(index=ix, horizon=f"r{h}", benchmark_mean=BENCHMARK_MEANS[ix][h],
                                 **tost(x, BENCHMARK_MEANS[ix][h], b, alpha)))
    t = pd.DataFrame(rows)
    t["bh_q"] = bh_qvalues(t["p_tost"])
    t["bh_equivalent_q10"] = t["bh_q"] < fdr_q
    return t


# ----------------------------------------------------------------------------
# Outputs and test ledger
# ----------------------------------------------------------------------------
def save_outputs(mde: pd.DataFrame, tst: pd.DataFrame, out_dir: Path | None = None) -> Path:
    out = out_dir or ROOT / "results" / "N01_power"
    out.mkdir(parents=True, exist_ok=True)
    mde.to_csv(out / "mde.csv", index=False)
    tst.to_csv(out / "tost.csv", index=False)
    return out


LEDGER_COLS = ["test_id", "hypothesis", "description", "status", "raw_p", "bh_p",
               "effect", "n", "notes", "raw_p_num", "family"]


def ledger_rows(tst: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in tst.iterrows():
        b = int(round(r["bound"] * 100))
        rows.append(dict(
            test_id=f"N01-TOST-{r['index']}-{r['horizon']}-b{b}",
            hypothesis="N01 equivalence",
            description=f"TOST: {r['index']} reclaim {r['horizon']} within +/-{b} pts of drawdown-matched mean",
            status="equivalent" if r["equivalent"] else "not equivalent",
            raw_p=f"{r['p_tost']:.4f}", bh_p=f"{r['bh_q']:.4f}",
            effect=f"{r['diff']:+.4f}", n=int(r["n"]),
            notes="Study 1 data already seen; re-expression, not new evidence (PREREG/N01_power.md)",
            raw_p_num=r["p_tost"], family="N01_TOST"))
    return pd.DataFrame(rows, columns=LEDGER_COLS)


def update_ledger(tst: pd.DataFrame, path: Path | None = None) -> pd.DataFrame:
    """Replace any earlier N01 rows in outputs/tests_run.csv with the current ones."""
    path = path or ROOT / "outputs" / "tests_run.csv"
    old = pd.read_csv(path, dtype=str) if path.exists() and path.stat().st_size else \
        pd.DataFrame(columns=LEDGER_COLS)
    old = old[old.get("family", pd.Series(dtype=str)) != "N01_TOST"]
    new = pd.concat([old, ledger_rows(tst).astype(str)], ignore_index=True)[LEDGER_COLS]
    new.to_csv(path, index=False)
    return new


# ----------------------------------------------------------------------------
# DESCRIPTIVE: cluster-bootstrap MDE (PREREG/N01_power.md addendum; no tests)
# ----------------------------------------------------------------------------
def reclaim_returns_with_year(events: pd.DataFrame, h: int) -> tuple[np.ndarray, np.ndarray]:
    """Same sample as reclaim_returns, plus calendar year of the break for clustering."""
    m = events["reclaimed"] & events[f"r{h}"].notna()
    return events.loc[m, f"r{h}"].to_numpy(float), events.loc[m, "break_date"].dt.year.to_numpy()


def cluster_bootstrap_se(x, clusters, B: int = 5000, seed: int = SEED) -> tuple[float, int]:
    """SD of the pooled event mean when whole clusters are resampled with replacement."""
    x = np.asarray(x, float)
    codes, uniq = pd.factorize(np.asarray(clusters))
    G = len(uniq)
    sums = np.bincount(codes, weights=x, minlength=G)
    sizes = np.bincount(codes, minlength=G).astype(float)
    rng = np.random.default_rng(seed)
    counts = np.stack([np.bincount(rng.integers(0, G, G), minlength=G) for _ in range(B)])
    means = (counts @ sums) / (counts @ sizes)
    return float(means.std(ddof=1)), G


def cluster_mde_table(events_by_index: dict[str, pd.DataFrame], B: int = 5000, seed: int = SEED,
                      alpha: float = ALPHA, power: float = POWER) -> pd.DataFrame:
    zsum = stats.norm.ppf(1 - alpha) + stats.norm.ppf(power)
    rows = []
    for ix, ev in events_by_index.items():
        for h in HORIZONS:
            x, yr = reclaim_returns_with_year(ev, h)
            se_cl, G = cluster_bootstrap_se(x, yr, B, seed)
            se_iid = x.std(ddof=1) / np.sqrt(x.size)
            tsum = stats.t.ppf(1 - alpha, G - 1) + stats.t.ppf(power, G - 1)
            rows.append(dict(index=ix, horizon=f"r{h}", n=x.size, G=G, se_iid=se_iid,
                             se_cluster=se_cl, se_ratio=se_cl / se_iid,
                             mde_iid_z=zsum * se_iid, mde_cluster_z=zsum * se_cl,
                             mde_cluster_t=tsum * se_cl))
    return pd.DataFrame(rows)


def format_cluster_mde_table(t: pd.DataFrame) -> pd.DataFrame:
    pts = lambda v: f"{v * 100:.2f}"   # noqa: E731
    return pd.DataFrame({
        "Index": t["index"], "Horizon": t["horizon"], "n": t["n"], "Years (G)": t["G"],
        "SE iid (pts)": t["se_iid"].map(pts), "SE cluster (pts)": t["se_cluster"].map(pts),
        "SE ratio": t["se_ratio"].map(lambda v: f"{v:.2f}"),
        "MDE iid z (pts)": t["mde_iid_z"].map(pts),
        "MDE cluster z (pts)": t["mde_cluster_z"].map(pts),
        "MDE cluster t(G-1) (pts)": t["mde_cluster_t"].map(pts),
    })
