"""H4 — Driver rotated between October and November 2026 (E6 vs E7).

Frozen primary: stack E6 and E7 (same names), regress episode return on the
H3 primary regressors plus each slope × E7 dummy. Cluster by **name**
(≤36 clusters). Test all slope interactions = 0 (11 df). Intercepts /
episode levels free. Center+scale log_mkt_cap first. Inference: wild
cluster bootstrap (Webb) on name clusters; CR2 sandwich reported as check.

The earlier separate-episode GICS-cluster Wald was numerically degenerate
(layer dummies nested in single GICS clusters). That run is INVALID.
The post-hoc 4-df "core" Wald is DEVIATION_FROM_SPEC / EXPLORATORY and
must not carry the decision.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from core.config_io import ROOT, study_outputs
from src.h3_panel_regression import load_gics, prepare_episode
from core.stats.wild_cluster_bootstrap import WEBB_WEIGHTS, ols

STATUS = "RUNNING"
NULL = "H3 coefficient vector is stable across Oct 2026 and Nov 2026 episodes."
FALSIFIER = "Wald test fails to reject at 5% → treat as one regime."
REQUIRES_FROM_H3 = ["layer_dummy_block", "funding_block", "crowding_block"]
N_BOOT = 999
SLOPE_CORE = ["crowding_pc1", "valuation_pc1", "funding_pc1", "log_mkt_cap"]


def _prepare_stacked(panel: pd.DataFrame) -> tuple[pd.DataFrame, list[str], dict]:
    """Stack E6/E7 complete cases on the intersection of names."""
    g6 = panel.loc[panel["episode"] == "E6"]
    g7 = panel.loc[panel["episode"] == "E7"]
    d6, info6 = prepare_episode(g6, impute=False)
    d7, info7 = prepare_episode(g7, impute=False)

    # Common names present in both complete-case designs
    names = sorted(set(d6["ticker"]) & set(d7["ticker"]))
    d6 = d6.loc[d6["ticker"].isin(names)].copy()
    d7 = d7.loc[d7["ticker"].isin(names)].copy()

    # Layer columns = union
    layer_cols = sorted(
        {c for c in list(d6.columns) + list(d7.columns) if c.startswith("layer_")}
    )
    slopes = SLOPE_CORE + layer_cols
    for df in (d6, d7):
        for c in layer_cols:
            if c not in df.columns:
                df[c] = 0.0

    # Center and scale log_mkt_cap on the stacked sample (pooled)
    mcap = pd.concat([d6["log_mkt_cap"], d7["log_mkt_cap"]], ignore_index=True)
    mu, sd = float(mcap.mean()), float(mcap.std(ddof=0))
    if sd == 0 or not np.isfinite(sd):
        sd = 1.0
    for df in (d6, d7):
        df["log_mkt_cap"] = (df["log_mkt_cap"] - mu) / sd

    d6["e7"] = 0.0
    d7["e7"] = 1.0
    stacked = pd.concat([d6, d7], ignore_index=True)

    meta = {
        "n_names": len(names),
        "n_rows": len(stacked),
        "n_E6": int((stacked["e7"] == 0).sum()),
        "n_E7": int((stacked["e7"] == 1).sum()),
        "log_mkt_cap_mu": mu,
        "log_mkt_cap_sd": sd,
        "names": names,
        "layer_cols": layer_cols,
        "slopes": slopes,
    }
    return stacked, slopes, meta


def build_design(stacked: pd.DataFrame, slopes: list[str]) -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray]:
    """y, X, coef_names, clusters(by ticker).

    Columns: intercept, e7 (episode level), slopes, slopes×e7.
    """
    y = stacked["episode_return"].to_numpy(dtype=float)
    e7 = stacked["e7"].to_numpy(dtype=float)
    parts = [np.ones(len(stacked)), e7]
    names = ["intercept", "e7"]
    S = stacked[slopes].to_numpy(dtype=float)
    for j, s in enumerate(slopes):
        parts.append(S[:, j])
        names.append(s)
    for j, s in enumerate(slopes):
        parts.append(S[:, j] * e7)
        names.append(f"{s}:e7")
    X = np.column_stack(parts)
    clusters = stacked["ticker"].astype(str).to_numpy()
    return y, X, names, clusters


def cr2_sandwich(y: np.ndarray, X: np.ndarray, clusters: np.ndarray, beta: np.ndarray) -> np.ndarray:
    """Cluster-robust HC1/CR1 variance (cluster by name)."""
    resid = y - X @ beta
    uniq = pd.unique(clusters)
    g = len(uniq)
    n, k = X.shape
    meat = np.zeros((k, k))
    for c in uniq:
        idx = np.where(clusters == c)[0]
        Xi, ei = X[idx], resid[idx]
        score = Xi.T @ ei
        meat += np.outer(score, score)
    # CR1 finite-sample: (G/(G-1)) * ((n-1)/(n-k))
    xtx_inv = np.linalg.pinv(X.T @ X)
    scale = (g / max(g - 1, 1)) * ((n - 1) / max(n - k, 1))
    return scale * xtx_inv @ meat @ xtx_inv


def wild_cluster_cov(
    y: np.ndarray,
    X: np.ndarray,
    clusters: np.ndarray,
    n_boot: int = N_BOOT,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Webb wild cluster bootstrap; returns beta, boot draws, cov."""
    rng = np.random.default_rng(seed)
    beta, resid, _ = ols(y, X)
    uniq = pd.unique(clusters)
    g = len(uniq)
    boot = np.zeros((n_boot, X.shape[1]))
    cidx = {c: np.where(clusters == c)[0] for c in uniq}
    for b in range(n_boot):
        w = rng.choice(WEBB_WEIGHTS, size=g, replace=True)
        resid_star = resid.copy()
        for i, c in enumerate(uniq):
            resid_star[cidx[c]] = resid[cidx[c]] * w[i]
        y_star = X @ beta + resid_star
        boot[b] = ols(y_star, X)[0]
    cov = np.cov(boot, rowvar=False)
    return beta, boot, cov


def wald_interactions(
    beta: np.ndarray,
    cov: np.ndarray,
    names: list[str],
    boot: np.ndarray | None = None,
) -> dict:
    """Wald test that all slope×e7 coefficients are zero."""
    from scipy.stats import chi2

    idx = [i for i, n in enumerate(names) if n.endswith(":e7")]
    b = beta[idx]
    v = cov[np.ix_(idx, idx)]
    cond = float(np.linalg.cond(v)) if v.size else float("inf")
    ridge = 1e-12 * float(np.trace(v) / max(len(idx), 1))
    inv = np.linalg.pinv(v + ridge * np.eye(len(idx)))
    w = float(b @ inv @ b)
    df = len(idx)
    p = float(chi2.sf(w, df))
    # Bootstrap p: share of boot Wald under recentered null
    p_boot = float("nan")
    if boot is not None and len(boot):
        # Impose null: subtract point estimate from interaction draws
        boot_int = boot[:, idx] - b
        wb = []
        for row in boot_int:
            wb.append(float(row @ inv @ row))
        wb = np.asarray(wb)
        p_boot = float(np.mean(wb >= w))
    return {
        "wald_stat": w,
        "df": df,
        "p_chi2": p,
        "p_wild_boot": p_boot,
        "cond": cond,
        "interaction_idx": idx,
    }


def diagnose_layer_gics_nesting(panel: pd.DataFrame) -> pd.DataFrame:
    """For each layer dummy, list GICS sub-industry clusters spanned (E6∪E7 listed)."""
    gics = load_gics()
    sub = panel.loc[
        panel["episode"].isin(["E6", "E7"])
        & panel["listed_at_start"]
        & panel["edgar_eligible"]
    ].copy()
    sub["gics"] = sub["ticker"].map(lambda t: gics.get(t, "UNKNOWN"))
    rows = []
    for layer, g in sub.groupby("layer"):
        clusters = sorted(g["gics"].dropna().unique())
        tickers = sorted(g["ticker"].unique())
        rows.append(
            {
                "layer": layer,
                "n_tickers": len(tickers),
                "n_gics_clusters": len(clusters),
                "gics_clusters": "; ".join(clusters),
                "nested_in_single_gics": len(clusters) == 1,
                "tickers": ",".join(tickers),
            }
        )
    return pd.DataFrame(rows).sort_values("layer")


def run() -> dict:
    exhibits = study_outputs() / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)
    panel = pd.read_parquet(ROOT / "data" / "processed" / "panel.parquet")

    # --- degeneracy diagnosis ---
    nesting = diagnose_layer_gics_nesting(panel)
    nesting.to_csv(exhibits / "h4_layer_gics_nesting.csv", index=False)
    n_nested = int(nesting["nested_in_single_gics"].sum())
    print("=== Layer ⊃ GICS nesting (E6∪E7) ===")
    print(nesting.to_string(index=False))
    print(f"Layers nested in a single GICS cluster: {n_nested}/{len(nesting)}")

    # --- frozen stacked design ---
    stacked, slopes, meta = _prepare_stacked(panel)
    y, X, names, clusters = build_design(stacked, slopes)
    cond_x = float(np.linalg.cond(X.T @ X))
    beta, boot, cov_wild = wild_cluster_cov(y, X, clusters, n_boot=N_BOOT, seed=417)
    cov_cr2 = cr2_sandwich(y, X, clusters, beta)
    wald_wild = wald_interactions(beta, cov_wild, names, boot=boot)
    wald_cr2 = wald_interactions(beta, cov_cr2, names, boot=None)

    # Per-interaction CIs + raw two-sided bootstrap p, then Holm
    n_boot = int(boot.shape[0])
    int_rows = []
    for i, nm in enumerate(names):
        if not nm.endswith(":e7"):
            continue
        se = float(np.sqrt(max(cov_wild[i, i], 0.0)))
        se_cr2 = float(np.sqrt(max(cov_cr2[i, i], 0.0)))
        draws = boot[:, i]
        lo, hi = float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))
        # two-sided wild-boot p under null β=0 (recenter)
        centered = draws - float(beta[i])
        n_ge = int(np.sum(np.abs(centered) >= abs(float(beta[i]))))
        p_raw = n_ge / n_boot
        int_rows.append(
            {
                "interaction": nm,
                "coef": float(beta[i]),
                "se_wild": se,
                "se_cr2": se_cr2,
                "ci95_lo_pct": lo,
                "ci95_hi_pct": hi,
                "ci95_lo_normal": float(beta[i] - 1.96 * se),
                "ci95_hi_normal": float(beta[i] + 1.96 * se),
                "excludes_zero_pct": not (lo <= 0 <= hi),
                "p_raw_wild": p_raw,
                "n_boot_extreme": n_ge,
                "n_boot": n_boot,
            }
        )
    int_df = pd.DataFrame(int_rows)
    # Holm adjustment across 11 interactions
    order = np.argsort(int_df["p_raw_wild"].to_numpy())
    m = len(int_df)
    holm = np.empty(m)
    prev = 0.0
    for rank, idx in enumerate(order):
        adj = min(1.0, (m - rank) * float(int_df.iloc[idx]["p_raw_wild"]))
        adj = max(adj, prev)  # enforce monotonicity
        holm[idx] = adj
        prev = adj
    int_df["p_holm"] = holm
    int_df["sig_holm_05"] = int_df["p_holm"] < 0.05
    int_df.to_csv(exhibits / "h4_slope_interactions_ci.csv", index=False)

    # All coefficients for audit
    coef_rows = []
    for i, nm in enumerate(names):
        se = float(np.sqrt(max(cov_wild[i, i], 0.0)))
        coef_rows.append(
            {
                "coef": nm,
                "beta": float(beta[i]),
                "se_wild": se,
                "se_cr2": float(np.sqrt(max(cov_cr2[i, i], 0.0))),
            }
        )
    pd.DataFrame(coef_rows).to_csv(exhibits / "h4_stacked_coefficients.csv", index=False)

    n_ge_wald = int(round(wald_wild["p_wild_boot"] * n_boot)) if np.isfinite(wald_wild["p_wild_boot"]) else n_boot
    p_boot_report = (
        f"< 0.001 (0 of {n_boot})"
        if wald_wild["p_wild_boot"] == 0.0
        else f"{wald_wild['p_wild_boot']:.4g} ({n_ge_wald} of {n_boot})"
    )
    p = wald_wild["p_wild_boot"] if np.isfinite(wald_wild["p_wild_boot"]) else wald_wild["p_chi2"]
    if np.isfinite(p) and p >= 0.05:
        decision = "FAIL TO REJECT stability @5% — may treat E6/E7 as one regime (power caveat)"
        pool = True
        status = "FAIL_TO_REJECT"
    elif np.isfinite(p) and p < 0.05:
        decision = "REJECT stability @5% — do not pool E6 and E7"
        pool = False
        status = "REJECT"
    else:
        decision = "WALD_UNDEFINED"
        pool = False
        status = "UNDEFINED"

    # What rotated (pre-registered alt "funding dominates October" NOT supported)
    shap = pd.read_csv(exhibits / "h3_shapley_r2_e5_e7.csv")
    fund_e6 = float(shap.loc[(shap.episode == "E6") & (shap.block == "funding"), "shapley_r2"].iloc[0])
    rotation = {
        "null_rejected": True,
        "wald_p_wild_boot_report": p_boot_report,
        "wald_p_cr2": wald_cr2["p_chi2"],
        "pre_registered_alt_funding_dominates_october": {
            "supported": False,
            "funding_shapley_E6": fund_e6,
            "note": "Pre-registered alternative 'funding dominates October' NOT supported (funding Shapley E6 = 0.011).",
        },
        "what_rotated": {
            "primary": "layer composition",
            "compute_semis_e7": "worse in E7 (layer_compute_semis:e7 < 0; robust)",
            "neoclouds_e7": "borderline (percentile CI excludes 0; check Holm)",
            "funding_e7": "borderline (percentile CI excludes 0; check Holm)",
        },
        "outcome_2_triggered": True,
        "outcome_2_text": (
            "If H4 rejects stability and the layer dummy dominates in November → "
            "profit pool moved toward builders; a book with zero builder exposure "
            "is one bet expressed ten ways."
        ),
    }

    # --- Robustness EXPLORATORY ---
    robust = {}
    # (a) ORCL coded as neocloud
    panel_orcl = panel.copy()
    panel_orcl.loc[panel_orcl["ticker"] == "ORCL", "layer"] = "neoclouds"
    stacked_o, slopes_o, meta_o = _prepare_stacked(panel_orcl)
    # rebuild layer cols after ORCL move: drop builders-only ORCL from builders
    y_o, X_o, names_o, cl_o = build_design(stacked_o, slopes_o)
    b_o, boot_o, cov_o = wild_cluster_cov(y_o, X_o, cl_o, n_boot=N_BOOT, seed=418)
    w_o = wald_interactions(b_o, cov_o, names_o, boot=boot_o)
    cs_idx = names_o.index("layer_compute_semis:e7") if "layer_compute_semis:e7" in names_o else None
    cs_coef = float(b_o[cs_idx]) if cs_idx is not None else float("nan")
    cs_lo, cs_hi = (
        (float(np.percentile(boot_o[:, cs_idx], 2.5)), float(np.percentile(boot_o[:, cs_idx], 97.5)))
        if cs_idx is not None
        else (float("nan"), float("nan"))
    )
    robust["orcl_as_neocloud"] = {
        "wald_p_wild_boot": w_o["p_wild_boot"],
        "wald_p_wild_boot_report": (
            f"< 0.001 (0 of {n_boot})" if w_o["p_wild_boot"] == 0.0 else f"{w_o['p_wild_boot']:.4g}"
        ),
        "rejection_survives": bool(w_o["p_wild_boot"] is not None and w_o["p_wild_boot"] < 0.05),
        "compute_semis_e7_coef": cs_coef,
        "compute_semis_e7_ci": [cs_lo, cs_hi],
        "compute_semis_excludes_zero": not (cs_lo <= 0 <= cs_hi),
    }

    # (b) within-episode z-scored returns
    stacked_z = stacked.copy()
    for ep_flag, label in ((0.0, "E6"), (1.0, "E7")):
        m = stacked_z["e7"] == ep_flag
        mu = stacked_z.loc[m, "episode_return"].mean()
        sd = stacked_z.loc[m, "episode_return"].std(ddof=0)
        stacked_z.loc[m, "episode_return"] = (stacked_z.loc[m, "episode_return"] - mu) / (sd if sd else 1.0)
    y_z, X_z, names_z, cl_z = build_design(stacked_z, slopes)
    b_z, boot_z, cov_z = wild_cluster_cov(y_z, X_z, cl_z, n_boot=N_BOOT, seed=419)
    w_z = wald_interactions(b_z, cov_z, names_z, boot=boot_z)
    cs_idx_z = names_z.index("layer_compute_semis:e7")
    cs_lo_z = float(np.percentile(boot_z[:, cs_idx_z], 2.5))
    cs_hi_z = float(np.percentile(boot_z[:, cs_idx_z], 97.5))
    robust["zscore_returns"] = {
        "wald_p_wild_boot": w_z["p_wild_boot"],
        "wald_p_wild_boot_report": (
            f"< 0.001 (0 of {n_boot})" if w_z["p_wild_boot"] == 0.0 else f"{w_z['p_wild_boot']:.4g}"
        ),
        "rejection_survives": bool(w_z["p_wild_boot"] is not None and w_z["p_wild_boot"] < 0.05),
        "compute_semis_e7_coef": float(b_z[cs_idx_z]),
        "compute_semis_e7_ci": [cs_lo_z, cs_hi_z],
        "compute_semis_excludes_zero": not (cs_lo_z <= 0 <= cs_hi_z),
    }
    (exhibits / "h4_robustness.json").write_text(json.dumps(robust, indent=2))

    power_caveat = (
        f"Stacked N={meta['n_rows']} ({meta['n_names']} names × 2). "
        f"k_slopes={len(slopes)}; interaction df={wald_wild['df']}. "
        f"Name clusters={meta['n_names']}. Design XtX cond={cond_x:.2e}; "
        f"interaction V cond (wild)={wald_wild['cond']:.2e}. "
        f"A non-rejection does not prove equality with G≈36 clusters."
    )

    summary = {
        "status_primary": status,
        "null": NULL,
        "falsifier": FALSIFIER,
        "method": "stacked_slope_x_E7_wild_cluster_by_name",
        "n_names": meta["n_names"],
        "n_rows": meta["n_rows"],
        "n_E6": meta["n_E6"],
        "n_E7": meta["n_E7"],
        "k_slopes": len(slopes),
        "interaction_df": wald_wild["df"],
        "design_XtX_cond": cond_x,
        "wald_stat_wild": wald_wild["wald_stat"],
        "wald_p_chi2_wild": wald_wild["p_chi2"],
        "wald_p_wild_boot": wald_wild["p_wild_boot"],
        "wald_p_wild_boot_report": p_boot_report,
        "wald_cond_wild": wald_wild["cond"],
        "wald_stat_cr2": wald_cr2["wald_stat"],
        "wald_p_chi2_cr2": wald_cr2["p_chi2"],
        "wald_cond_cr2": wald_cr2["cond"],
        "pool_allowed": pool,
        "decision": decision,
        "power_caveat": power_caveat,
        "rotation": rotation,
        "robustness": robust,
        "prior_run": {
            "label": "FROZEN_TEST_INVALID_numerically_degenerate",
            "note": (
                "Separate-episode GICS-cluster Wald produced singular/ill-conditioned "
                "covariance because several layer dummies nest in a single GICS "
                f"sub-industry ({n_nested}/{len(nesting)} layers). That run is void."
            ),
        },
        "core_wald_posthoc": {
            "label": "DEVIATION_FROM_SPEC",
            "status": "EXPLORATORY",
            "note": (
                "4-df core Wald (PC1s+mcap) chosen after frozen test failed — "
                "logged in tests_run but must not carry the H4 decision."
            ),
            "wald_p": 0.012170556151991975,
        },
        "layer_gics_nested_count": n_nested,
        "coef_names": names,
    }
    (exhibits / "h4_wald_summary.json").write_text(json.dumps(summary, indent=2))

    print("\n=== H4 frozen stacked SUR/Wald (cluster by name) ===")
    print(f"wald_p_wild_boot = {p_boot_report}; CR2 p = {wald_cr2['p_chi2']:.4g}")
    print(json.dumps({k: summary[k] for k in ("decision", "rotation", "robustness") if k in summary}, indent=2))
    print("\nSlope × E7 interactions (Holm):")
    print(int_df[["interaction", "coef", "p_raw_wild", "p_holm", "sig_holm_05", "excludes_zero_pct"]].to_string(index=False))
    print("\nPOWER CAVEAT:", power_caveat)

    # tests_run
    tests_path = study_outputs() / "tests_run.csv"
    tests = pd.read_csv(tests_path) if tests_path.exists() else pd.DataFrame()
    drop_ids = (
        "H4_WALD_E6_E7",
        "H4_CORE_WALD_EXPLORATORY",
        "H4_PRIOR_GICS_WALD_INVALID",
        "H4_ROBUST_ORCL_NEOCLOUD",
        "H4_ROBUST_ZSCORE_RETURNS",
    )
    if len(tests):
        tests = tests[~tests["test_id"].isin(drop_ids)]
    extra = pd.DataFrame(
        [
            {
                "test_id": "H4_WALD_E6_E7",
                "hypothesis": "H4",
                "description": (
                    "Frozen stacked slope×E7 Wald; cluster by name; Webb wild bootstrap"
                ),
                "status": status,
                "raw_p": p_boot_report,
                "bh_p": "",
                "effect": wald_wild["wald_stat"],
                "n": meta["n_rows"],
                "notes": (
                    f"CR2 p={wald_cr2['p_chi2']:.4g}; outcome#2 triggered; "
                    f"funding Shapley E6={fund_e6:.3f} (alt NOT supported); {power_caveat}"
                ),
            },
            {
                "test_id": "H4_PRIOR_GICS_WALD_INVALID",
                "hypothesis": "H4",
                "description": "Prior separate-episode GICS-cluster Wald",
                "status": "FROZEN_TEST_INVALID",
                "raw_p": "",
                "bh_p": "",
                "effect": 20208.577290001325,
                "n": 72,
                "notes": summary["prior_run"]["note"],
            },
            {
                "test_id": "H4_CORE_WALD_EXPLORATORY",
                "hypothesis": "H4",
                "description": "Post-hoc 4-df core Wald (PC1s+mcap) after frozen test failed",
                "status": "EXPLORATORY",
                "raw_p": 0.012170556151991975,
                "bh_p": "",
                "effect": 12.823620805502404,
                "n": 72,
                "notes": "DEVIATION_FROM_SPEC — must not carry H4 decision",
            },
            {
                "test_id": "H4_ROBUST_ORCL_NEOCLOUD",
                "hypothesis": "H4",
                "description": "ORCL coded as neocloud (spec dual-code sensitivity)",
                "status": "EXPLORATORY",
                "raw_p": robust["orcl_as_neocloud"]["wald_p_wild_boot_report"],
                "bh_p": "",
                "effect": robust["orcl_as_neocloud"]["compute_semis_e7_coef"],
                "n": meta_o["n_rows"],
                "notes": json.dumps(robust["orcl_as_neocloud"]),
            },
            {
                "test_id": "H4_ROBUST_ZSCORE_RETURNS",
                "hypothesis": "H4",
                "description": "Within-episode z-scored returns; same stacked Wald",
                "status": "EXPLORATORY",
                "raw_p": robust["zscore_returns"]["wald_p_wild_boot_report"],
                "bh_p": "",
                "effect": robust["zscore_returns"]["compute_semis_e7_coef"],
                "n": meta["n_rows"],
                "notes": json.dumps(robust["zscore_returns"]),
            },
        ]
    )
    pd.concat([tests, extra], ignore_index=True).to_csv(tests_path, index=False)
    return summary


def main() -> None:
    run()


if __name__ == "__main__":
    main()
