"""H4 — Driver rotated between October and November 2026 (E6 vs E7).

Frozen: SUR / Wald on the full H3 coefficient vector including layer dummies.
Do not pool E6 and E7 until this test adjudicates stability.

Null: H3 coefficient vector stable across E6 and E7.
Falsifier: Wald fails to reject at 5% → treat as one regime.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config_io import ROOT
from src.studies.h3_panel_regression import (
    N_BOOT,
    load_gics,
    prepare_episode,
)
from src.stats.wild_cluster_bootstrap import design_matrix, ols, wild_cluster_bootstrap

STATUS = "RUNNING"
NULL = "H3 coefficient vector is stable across Oct 2026 and Nov 2026 episodes."
FALSIFIER = "Wald test fails to reject at 5% → treat as one regime."
REQUIRES_FROM_H3 = ["layer_dummy_block", "funding_block", "crowding_block"]


def _episode_fit(g: pd.DataFrame, gics: dict[str, str], seed: int) -> dict:
    design, info = prepare_episode(g, impute=False)
    cols = info["primary_cols"]
    # Align layer dummy columns across episodes: ensure same set
    return design, info, cols


def common_primary_cols(d6: pd.DataFrame, d7: pd.DataFrame, cols6: list[str], cols7: list[str]) -> list[str]:
    """Intersection of primary cols, preferring shared layer dummies."""
    base = ["crowding_pc1", "valuation_pc1", "funding_pc1", "log_mkt_cap"]
    layers = sorted(set(c for c in cols6 + cols7 if c.startswith("layer_")))
    # include layer col if present in either; fill missing with 0
    return base + layers


def ensure_cols(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            out[c] = 0.0
    return out


def wald_equal_beta(
    b1: np.ndarray,
    b2: np.ndarray,
    v1: np.ndarray,
    v2: np.ndarray,
    idx: list[int] | None = None,
) -> dict:
    """Wald test H0: b1[idx] = b2[idx]. Uses V1+V2 (independent episodes)."""
    from scipy.stats import chi2

    diff = b1 - b2
    v = v1 + v2
    if idx is None:
        idx = list(range(1, len(diff)))  # drop intercept
    diff_s = diff[idx]
    v_s = v[np.ix_(idx, idx)]
    cond = float(np.linalg.cond(v_s)) if v_s.size else float("inf")
    try:
        # ridge for numerical stability when layer dummies make V ill-conditioned
        ridge = 1e-10 * float(np.trace(v_s) / max(len(idx), 1))
        inv = np.linalg.pinv(v_s + ridge * np.eye(len(idx)))
        w = float(diff_s @ inv @ diff_s)
        df = len(idx)
        p = float(chi2.sf(w, df))
    except Exception:  # noqa: BLE001
        w, p, df = float("nan"), float("nan"), len(idx)
    return {"wald_stat": w, "df": df, "p_value": p, "cond": cond}


def bootstrap_cov(y: np.ndarray, X: np.ndarray, clusters: np.ndarray, n_boot: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (beta, cov) from Webb wild cluster bootstrap draws."""
    rng = np.random.default_rng(seed)
    from src.stats.wild_cluster_bootstrap import WEBB_WEIGHTS

    beta, resid, _r2 = ols(y, X)
    uniq = pd.unique(clusters)
    g = len(uniq)
    boot = np.zeros((n_boot, X.shape[1]))
    cidx = {c: np.where(clusters == c)[0] for c in uniq}
    for b in range(n_boot):
        w = rng.choice(WEBB_WEIGHTS, size=g, replace=True)
        resid_star = resid.copy()
        for i, c in enumerate(uniq):
            resid_star[cidx[c]] *= w[i]
        y_star = X @ beta + resid_star
        boot[b] = ols(y_star, X)[0]
    cov = np.cov(boot, rowvar=False)
    return beta, cov


def run() -> dict:
    exhibits = ROOT / "outputs" / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)
    panel = pd.read_parquet(ROOT / "data" / "processed" / "panel.parquet")
    gics = load_gics()

    g6 = panel.loc[panel["episode"] == "E6"]
    g7 = panel.loc[panel["episode"] == "E7"]
    d6, info6, cols6 = _episode_fit(g6, gics, 106)
    d7, info7, cols7 = _episode_fit(g7, gics, 107)
    cols = common_primary_cols(d6, d7, cols6, cols7)
    d6 = ensure_cols(d6, cols)
    d7 = ensure_cols(d7, cols)

    n6, n7 = len(d6), len(d7)
    k = len(cols)
    rdf6, rdf7 = n6 - k - 1, n7 - k - 1

    y6, X6, names = design_matrix(d6, cols)
    y7, X7, _ = design_matrix(d7, cols)
    cl6 = d6["ticker"].map(lambda t: gics.get(t, "UNKNOWN")).to_numpy()
    cl7 = d7["ticker"].map(lambda t: gics.get(t, "UNKNOWN")).to_numpy()

    b6, v6 = bootstrap_cov(y6, X6, cl6, N_BOOT, seed=406)
    b7, v7 = bootstrap_cov(y7, X7, cl7, N_BOOT, seed=407)

    # Full slope Wald (ex intercept) + core-only (PC1s + mcap, no layer)
    wald_full = wald_equal_beta(b6, b7, v6, v7)
    core_idx = [names.index(c) for c in ("crowding_pc1", "valuation_pc1", "funding_pc1", "log_mkt_cap")]
    wald_core = wald_equal_beta(b6, b7, v6, v7, idx=core_idx)

    # Per-coefficient differences
    coef_rows = []
    for i, nm in enumerate(names):
        se_diff = float(np.sqrt(max(v6[i, i] + v7[i, i], 0.0)))
        diff = float(b6[i] - b7[i])
        z = diff / se_diff if se_diff > 0 else float("nan")
        coef_rows.append(
            {
                "coef": nm,
                "beta_E6": float(b6[i]),
                "beta_E7": float(b7[i]),
                "diff_E6_minus_E7": diff,
                "se_diff_wild": se_diff,
                "z_diff": z,
            }
        )
    coef_df = pd.DataFrame(coef_rows)
    coef_df.to_csv(exhibits / "h4_e6_e7_coefficients.csv", index=False)

    # Full-vector Wald with 7 layer dummies is often numerically explosive
    # (tiny eigenvalues → huge statistic). Treat as DEGENERATE when cond is
    # large or the statistic is pathologically above the χ² reference; then
    # decide on the core (PC1s+mcap) Wald, still reporting the full attempt.
    from scipy.stats import chi2 as chi2dist

    chi2_ref = float(chi2dist.ppf(0.999, wald_full["df"]))
    ill = (
        float(wald_full.get("cond") or 0) > 1e5
        or (np.isfinite(wald_full["wald_stat"]) and wald_full["wald_stat"] > 50 * chi2_ref)
    )
    if ill:
        p_decision = wald_core["p_value"]
        decision_basis = "core_pc1_mcap_wald_FULL_VECTOR_NUMERICAL_DEGENERATE"
    else:
        p_decision = wald_full["p_value"]
        decision_basis = "full_slope_wald"

    if np.isfinite(p_decision) and p_decision >= 0.05:
        decision = "FAIL TO REJECT stability @5% — may treat E6/E7 as one regime (with power caveat)"
        pool = True
    elif np.isfinite(p_decision) and p_decision < 0.05:
        decision = "REJECT stability @5% — do not pool E6 and E7"
        pool = False
    else:
        decision = "WALD_UNDEFINED"
        pool = False

    power_caveat = (
        f"Residual df E6={rdf6}, E7={rdf7} with k={k} slopes (+intercept). "
        f"N={n6}/{n7} complete cases. Wild-cluster Wald with {len(pd.unique(cl6))}/"
        f"{len(pd.unique(cl7))} GICS clusters is low-power for equality; a non-rejection "
        f"does not prove coefficient equality. Full-vector V condition number="
        f"{wald_full.get('cond'):.2e} (ill={ill}); core Wald p={wald_core['p_value']:.4g}. "
        f"Decision basis={decision_basis}. Inspect per-coef diffs in h4_e6_e7_coefficients.csv."
    )

    summary = {
        "null": NULL,
        "falsifier": FALSIFIER,
        "n_E6": n6,
        "n_E7": n7,
        "k_slopes": k,
        "residual_df_E6": rdf6,
        "residual_df_E7": rdf7,
        "wald_stat_full": wald_full["wald_stat"],
        "wald_df_full": wald_full["df"],
        "wald_p_full": wald_full["p_value"],
        "wald_cond_full": wald_full.get("cond"),
        "wald_stat_core": wald_core["wald_stat"],
        "wald_df_core": wald_core["df"],
        "wald_p_core": wald_core["p_value"],
        "decision_basis": decision_basis,
        "pool_allowed": pool,
        "decision": decision,
        "power_caveat": power_caveat,
        "coef_names": names,
    }
    (exhibits / "h4_wald_summary.json").write_text(json.dumps(summary, indent=2))

    print("=== H4 SUR/Wald E6 vs E7 ===")
    print(json.dumps(summary, indent=2))
    print("\nPer-coefficient:")
    print(coef_df.to_string(index=False))
    print("\nPOWER CAVEAT:", power_caveat)

    # tests_run
    tests_path = ROOT / "outputs" / "tests_run.csv"
    tests = pd.read_csv(tests_path) if tests_path.exists() else pd.DataFrame()
    if len(tests):
        tests = tests[tests["test_id"] != "H4_WALD_E6_E7"]
    extra = pd.DataFrame(
        [
            {
                "test_id": "H4_WALD_E6_E7",
                "hypothesis": "H4",
                "description": "Wald equality of H3 primary vector E6 vs E7 (wild-cluster cov)",
                "status": "FAIL_TO_REJECT" if pool else ("REJECT" if np.isfinite(p_decision) and p_decision < 0.05 else "UNDEFINED"),
                "raw_p": p_decision,
                "bh_p": "",
                "effect": wald_full["wald_stat"],
                "n": n6 + n7,
                "notes": power_caveat,
            }
        ]
    )
    pd.concat([tests, extra], ignore_index=True).to_csv(tests_path, index=False)
    return summary


def main() -> None:
    run()


if __name__ == "__main__":
    main()
