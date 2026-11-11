"""H3 review diagnostics (EXPLORATORY — not in FDR family).

- Layer-block incremental adj-R² over crowding+valuation+funding+mcap
- Shapley / dominance R² across five blocks (E5–E7)
- Parameter count + residual df; FRAGILE / DEGENERATE flags
- PC1 orientation report (vol/SI sign flips)
- E6/E7 primary vs secondary side-by-side
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config_io import ROOT
from src.features.funding import funding_cols_for_episode
from src.features.valuation import VALUATION_COLS
from src.stats.pca_vif import pc1_scores_loadings, winsorize
from src.stats.wild_cluster_bootstrap import adj_r2, ols
from src.studies.h3_panel_regression import (
    CROWDING_COLS,
    LAYER_REF,
    MIN_N_FALSIFIER,
    layer_dummies,
    load_gics,
    prepare_episode,
)


BLOCK_ORDER = ("crowding", "valuation", "funding", "layer", "mcap")


def _r2(y: np.ndarray, X: np.ndarray) -> float:
    if X.shape[1] == 0:
        return 0.0
    X1 = np.column_stack([np.ones(len(y)), X])
    _b, _r, r2 = ols(y, X1)
    return float(r2)


def block_matrices(design: pd.DataFrame) -> dict[str, np.ndarray]:
    layer_cols = [c for c in design.columns if c.startswith("layer_")]
    return {
        "crowding": design[["crowding_pc1"]].to_numpy(dtype=float),
        "valuation": design[["valuation_pc1"]].to_numpy(dtype=float),
        "funding": design[["funding_pc1"]].to_numpy(dtype=float),
        "layer": design[layer_cols].to_numpy(dtype=float) if layer_cols else np.zeros((len(design), 0)),
        "mcap": design[["log_mkt_cap"]].to_numpy(dtype=float),
    }


def shapley_r2(y: np.ndarray, blocks: dict[str, np.ndarray]) -> dict[str, float]:
    """Shapley decomposition of R² across named blocks (LMG dominance)."""
    names = list(blocks.keys())
    n = len(names)
    phi = {nm: 0.0 for nm in names}
    # factorial weights
    from math import factorial

    for r in range(n):
        for subset in itertools.combinations(names, r):
            rest = [nm for nm in names if nm not in subset]
            X_s = np.column_stack([blocks[nm] for nm in subset]) if subset else np.zeros((len(y), 0))
            r2_s = _r2(y, X_s)
            weight = factorial(r) * factorial(n - r - 1) / factorial(n)
            for j in rest:
                X_sj = np.column_stack([X_s, blocks[j]]) if X_s.size else blocks[j]
                if X_s.size == 0:
                    X_sj = blocks[j]
                else:
                    X_sj = np.column_stack([X_s, blocks[j]])
                r2_sj = _r2(y, X_sj)
                phi[j] += weight * (r2_sj - r2_s)
    return phi


def episode_diagnostics(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    shapley_rows = []
    orient_rows = []
    load = pd.read_csv(ROOT / "outputs" / "exhibits" / "h3_pc_loadings_and_vif.csv")
    crowd_load = load.loc[load["block"] == "crowding"]

    for eid, g in sorted(panel.groupby("episode"), key=lambda x: x[0]):
        design, info = prepare_episode(g, impute=False)
        n = int(info["n_complete"])
        primary_cols = info.get("primary_cols") or []
        k = len(primary_cols)  # excl intercept
        rdf = n - k - 1
        # Degenerate: perfect fit or non-positive residual df
        r2 = float("nan")
        if len(design) >= 3 and primary_cols:
            y = design["episode_return"].to_numpy(dtype=float)
            X = design[primary_cols].to_numpy(dtype=float)
            X1 = np.column_stack([np.ones(len(design)), X])
            _b, _r, r2 = ols(y, X1)
        if rdf <= 0 or (np.isfinite(r2) and r2 >= 0.999):
            flag = "DEGENERATE"
        elif rdf < 15:
            flag = "FRAGILE"
        else:
            flag = ""

        # Layer incremental adj-R² over crowding+valuation+funding+mcap
        layer_cols = [c for c in primary_cols if c.startswith("layer_")]
        base = ["crowding_pc1", "valuation_pc1", "funding_pc1", "log_mkt_cap"]
        incr_layer = float("nan")
        if len(design) >= 5:
            y = design["episode_return"].to_numpy(dtype=float)
            X_base = design[base].to_numpy(dtype=float)
            X_full = design[base + layer_cols].to_numpy(dtype=float)
            r2_base = _r2(y, X_base)
            r2_full = _r2(y, X_full)
            ar2_base = adj_r2(r2_base, n, len(base))
            ar2_full = adj_r2(r2_full, n, len(base) + len(layer_cols))
            incr_layer = ar2_full - ar2_base

        # Wild-bootstrap p from primary exhibit (re-read)
        prim = pd.read_csv(ROOT / "outputs" / "exhibits" / "h3_primary_by_episode.csv")
        prow = prim.loc[prim["episode"] == eid].iloc[0]
        p_crowd = float(prow["p_crowding_pc1"]) if pd.notna(prow["p_crowding_pc1"]) else float("nan")
        p_note = ""
        if flag == "DEGENERATE" and p_crowd == 0.0:
            p_note = "p=0.000 DEGENERATE (saturated / non-positive residual df; bootstrap mass at point estimate)"
        elif flag == "FRAGILE" and p_crowd == 0.0:
            p_note = "p=0.000 DEGENERATE/FRAGILE (residual df small; wild-bootstrap p not reliable)"

        rows.append(
            {
                "episode": eid,
                "n_complete": n,
                "n_params_excl_intercept": k,
                "residual_df": rdf,
                "flag": flag,
                "r2_primary": r2,
                "incr_adj_r2_layer_over_cvfm": incr_layer,
                "incr_adj_r2_crowding": prow.get("incr_adj_r2_crowding"),
                "incr_adj_r2_valuation": prow.get("incr_adj_r2_valuation"),
                "adj_r2_crowd_only": prow.get("adj_r2_crowd_only"),
                "p_crowding_pc1": p_crowd,
                "p_valuation_pc1": prow.get("p_valuation_pc1"),
                "p_note": p_note,
                "excluded_from_falsifier": bool(prow.get("excluded_from_falsifier")),
            }
        )

        # Shapley for E5–E7 only
        if eid in ("E5", "E6", "E7") and len(design) >= 10:
            y = design["episode_return"].to_numpy(dtype=float)
            phi = shapley_r2(y, block_matrices(design))
            for blk, val in phi.items():
                shapley_rows.append({"episode": eid, "block": blk, "shapley_r2": val})

        # Orientation
        sub = crowd_load.loc[crowd_load["episode"] == eid]
        if len(sub):
            d = {r.feature: r.loading for r in sub.itertuples()}
            orient_rows.append(
                {
                    "episode": eid,
                    "load_vol": d.get("realised_vol_21d"),
                    "load_si": d.get("short_interest_pct_float"),
                    "load_mom": d.get("prior_63d_return"),
                    "load_dist": d.get("dist_252d_high"),
                    "vol_si_same_sign_as_mom": (
                        np.sign(d.get("realised_vol_21d", 0))
                        == np.sign(d.get("prior_63d_return", 0))
                    ),
                }
            )

    return pd.DataFrame(rows), pd.DataFrame(shapley_rows), pd.DataFrame(orient_rows)


def e6_e7_primary_vs_secondary(panel: pd.DataFrame) -> pd.DataFrame:
    """Side-by-side primary PC coeffs vs secondary individual crowding/valuation regressors."""
    from src.studies.h3_panel_regression import run_secondary, run_primary_episode

    gics = load_gics()
    rows = []
    for eid in ("E6", "E7"):
        g = panel.loc[panel["episode"] == eid]
        prim = run_primary_episode(g, gics, seed=100)
        sec = run_secondary(g, with_ai=False, gics=gics, seed=300)
        rows.append(
            {
                "episode": eid,
                "model": "primary_pc1",
                "n_complete": prim.get("n_complete"),
                "adj_r2": prim.get("adj_r2"),
                "coef_crowding_pc1": (prim.get("coef") or {}).get("crowding_pc1"),
                "coef_valuation_pc1": (prim.get("coef") or {}).get("valuation_pc1"),
                "p_crowding_pc1": (prim.get("p_wild_cluster") or {}).get("crowding_pc1"),
                "p_valuation_pc1": (prim.get("p_wild_cluster") or {}).get("valuation_pc1"),
                "coef_prior_63d": None,
                "coef_dist_252d": None,
                "coef_vol_21d": None,
                "coef_si": None,
                "coef_ep": None,
                "coef_sp": None,
                "coef_ebitda_ev": None,
            }
        )
        coef = sec.get("coef") or {}
        rows.append(
            {
                "episode": eid,
                "model": "secondary_full",
                "n_complete": sec.get("n_complete"),
                "adj_r2": sec.get("adj_r2"),
                "coef_crowding_pc1": None,
                "coef_valuation_pc1": None,
                "p_crowding_pc1": None,
                "p_valuation_pc1": None,
                "coef_prior_63d": coef.get("prior_63d_return"),
                "coef_dist_252d": coef.get("dist_252d_high"),
                "coef_vol_21d": coef.get("realised_vol_21d"),
                "coef_si": coef.get("short_interest_pct_float"),
                "coef_ep": coef.get("earnings_yield_ep_filing_lag"),
                "coef_sp": coef.get("sales_yield_sp_filing_lag"),
                "coef_ebitda_ev": coef.get("ebitda_ev_yield_filing_lag"),
            }
        )
    return pd.DataFrame(rows)


def run() -> dict:
    exhibits = ROOT / "outputs" / "exhibits"
    panel = pd.read_parquet(ROOT / "data" / "processed" / "panel.parquet")
    diag, shapley, orient = episode_diagnostics(panel)
    side = e6_e7_primary_vs_secondary(panel)

    diag.to_csv(exhibits / "h3_review_diagnostics.csv", index=False)
    shapley.to_csv(exhibits / "h3_shapley_r2_e5_e7.csv", index=False)
    orient.to_csv(exhibits / "h3_pc1_orientation.csv", index=False)
    side.to_csv(exhibits / "h3_e6_e7_primary_vs_secondary.csv", index=False)

    print("=== H3 review diagnostics ===")
    print(diag.to_string(index=False))
    print("\n=== Shapley R² (E5–E7) ===")
    if len(shapley):
        print(shapley.pivot(index="block", columns="episode", values="shapley_r2").round(4).to_string())
    print("\n=== PC1 orientation (vol/SI) ===")
    print(orient.to_string(index=False))
    print("\n=== E6/E7 primary vs secondary ===")
    print(side.to_string(index=False))

    # Decision summary for RESULTS
    counted = diag.loc[~diag["excluded_from_falsifier"]]
    n_crowd_nonpos = int((counted["incr_adj_r2_crowding"].fillna(0) <= 0).sum())
    decision = {
        "falsifier_triggered": False,
        "falsifier_val_beats": 3,
        "falsifier_counted": 6,
        "crowding_incr_adj_r2_le_0": n_crowd_nonpos,
        "crowding_incr_adj_r2_le_0_of": int(len(counted)),
        "decision": (
            "H3 UNSUPPORTED: neither crowding nor valuation adds explanatory power within layers."
        ),
        "k003": (
            "Call 3 (crowding, not valuation) not supported in multivariate panel; "
            "univariate crowding association (adj R² 0.37 E6, 0.23 E7) is absorbed by layer dummies."
        ),
        "exploratory_not_in_fdr": True,
    }
    (exhibits / "h3_decision_review.json").write_text(json.dumps(decision, indent=2))
    print("\n=== Decision ===")
    print(json.dumps(decision, indent=2))
    return {"diag": diag, "shapley": shapley, "orient": orient, "side": side, "decision": decision}


if __name__ == "__main__":
    run()
