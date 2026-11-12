"""H3 — Crowding dominates valuation across episodes (P4).

Primary (frozen): episode return ~ crowding PC1 + valuation PC1 + funding PC1
+ layer dummies + log mkt cap.

Inference: wild cluster bootstrap (GICS sub-industry, Webb weights) +
episode-level bootstrap.

Horse race: adj R² for crowding-only / valuation-only / both (+ controls).
Falsifier: valuation incremental adj-R² > crowding in ≥4/7 episodes
(episodes with N<20 complete cases reported but excluded from falsifier count).

Missing data: primary = complete cases; sensitivity = median impute + missing
indicators.

Secondary: full regressors, with/without AI exposure.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from core.config_io import ROOT, reference_path, study_outputs
from core.features.funding import funding_cols_for_episode
from core.features.valuation import VALUATION_COLS
from core.stats.pca_vif import pc1_scores_loadings, standardize, vif_table, winsorize
from core.stats.wild_cluster_bootstrap import (
    adj_r2,
    design_matrix,
    episode_bootstrap_r2,
    ols,
    wild_cluster_bootstrap,
)

STATUS = "RUNNING"
NULL = "Crowding proxies carry no incremental R² over valuation + fundamentals."
FALSIFIER = (
    "Valuation block incremental adj-R² exceeds crowding in ≥ 4 of 7 episodes "
    "(episodes with N<20 complete cases excluded from falsifier count)."
)

CROWDING_COLS = [
    "prior_63d_return",
    "dist_252d_high",
    "realised_vol_21d",
    "short_interest_pct_float",
]
LAYER_REF = "builders"
MIN_N_FALSIFIER = 20
N_BOOT = 999


def load_gics() -> dict[str, str]:
    path = reference_path("gics_subindustry")
    data = yaml.safe_load(path.read_text())
    return dict(data.get("clusters") or {})


def layer_dummies(layer: pd.Series) -> pd.DataFrame:
    cats = sorted({x for x in layer.dropna().unique() if x != LAYER_REF})
    out = pd.DataFrame(index=layer.index)
    for c in cats:
        out[f"layer_{c}"] = (layer == c).astype(float)
    return out


def prepare_episode(
    g: pd.DataFrame,
    *,
    impute: bool = False,
) -> tuple[pd.DataFrame, dict]:
    """Build primary-model design for one episode. Returns (design_df, info)."""
    g = g.loc[g["listed_at_start"] & g["edgar_eligible"]].copy()
    info: dict = {"episode": g["episode"].iloc[0] if len(g) else None, "n_listed_edgar": len(g)}
    if g.empty:
        return g, info

    eid = str(g["episode"].iloc[0])
    lease_nn = int(g["lease_liab_assets"].notna().sum())
    fund_cols = list(
        funding_cols_for_episode(eid, lease_nn, len(g))
    )
    crowd_cols = [c for c in CROWDING_COLS if c in g.columns]
    val_cols = [c for c in VALUATION_COLS if c in g.columns]

    # Winsorise continuous features within episode
    for c in crowd_cols + val_cols + fund_cols + ["log_mkt_cap", "adv", "episode_return"]:
        if c in g.columns:
            g[c] = winsorize(g[c].astype(float))

    if impute:
        # median impute + missing indicators for PC inputs and controls
        for c in crowd_cols + val_cols + fund_cols + ["log_mkt_cap"]:
            miss = g[c].isna()
            g[f"miss_{c}"] = miss.astype(float)
            if miss.any() and miss.all() is False:
                g[c] = g[c].fillna(g[c].median())
            elif miss.all():
                g[c] = 0.0
        info["impute"] = True
    else:
        info["impute"] = False

    # PC1s on (possibly imputed) blocks
    crowd_pc, crowd_load = pc1_scores_loadings(g[crowd_cols])
    val_pc, val_load = pc1_scores_loadings(g[val_cols])
    fund_pc, fund_load = pc1_scores_loadings(g[fund_cols])
    g["crowding_pc1"] = crowd_pc
    g["valuation_pc1"] = val_pc
    g["funding_pc1"] = fund_pc
    info["loadings"] = {
        "crowding": crowd_load.to_dict(),
        "valuation": val_load.to_dict(),
        "funding": fund_load.to_dict(),
    }
    info["funding_cols"] = fund_cols

    dummies = layer_dummies(g["layer"])
    for c in dummies.columns:
        g[c] = dummies[c]

    primary_cols = (
        ["crowding_pc1", "valuation_pc1", "funding_pc1", "log_mkt_cap"]
        + list(dummies.columns)
    )
    if impute:
        miss_cols = [c for c in g.columns if c.startswith("miss_")]
        primary_cols = primary_cols + miss_cols

    # complete cases for primary outcome + primary cols
    need = ["episode_return"] + primary_cols
    complete = g.dropna(subset=need).copy()
    info["n_complete"] = int(len(complete))
    info["primary_cols"] = primary_cols
    info["excluded_from_falsifier"] = info["n_complete"] < MIN_N_FALSIFIER
    return complete, info


def incremental_adj_r2(df: pd.DataFrame, block: str, controls: list[str]) -> dict:
    """adjR2(block+controls) - adjR2(controls); also block-only adjR2."""
    y = df["episode_return"].to_numpy(dtype=float)
    n = len(df)

    def fit(cols: list[str]) -> float:
        cols = [c for c in cols if c in df.columns]
        if not cols:
            # intercept only
            r2 = 0.0
            return adj_r2(r2, n, 0)
        X = np.column_stack([np.ones(n), df[cols].to_numpy(dtype=float)])
        _b, _r, r2 = ols(y, X)
        return adj_r2(r2, n, len(cols))

    block_cols = [block]
    both = block_cols + controls
    ar2_controls = fit(controls)
    ar2_block = fit(block_cols)
    ar2_both = fit(both)
    return {
        "adj_r2_block_only": ar2_block,
        "adj_r2_controls": ar2_controls,
        "adj_r2_block_plus_controls": ar2_both,
        "incremental_adj_r2": ar2_both - ar2_controls,
    }


def run_primary_episode(g: pd.DataFrame, gics: dict[str, str], seed: int) -> dict:
    design, info = prepare_episode(g, impute=False)
    eid = info["episode"]
    out: dict = {"episode": eid, **{k: info[k] for k in info if k != "loadings"}}
    out["loadings"] = info.get("loadings")
    if design.empty or info["n_complete"] < 5:
        out["status"] = "TOO_FEW"
        return out

    # VIFs on primary continuous PCs + log_mcap
    vif_cols = [c for c in ["crowding_pc1", "valuation_pc1", "funding_pc1", "log_mkt_cap"] if c in design]
    out["vif"] = vif_table(design[vif_cols]).to_dict()

    y, X, names = design_matrix(design, info["primary_cols"])
    clusters = design["ticker"].map(lambda t: gics.get(t, "UNKNOWN")).to_numpy()
    wcb = wild_cluster_bootstrap(y, X, clusters, n_boot=N_BOOT, seed=seed)
    epb = episode_bootstrap_r2(y, X, n_boot=N_BOOT, seed=seed + 1)
    out["coef"] = {names[i]: float(wcb["beta"][i]) for i in range(len(names))}
    out["se_wild_cluster"] = {names[i]: float(wcb["se"][i]) for i in range(len(names))}
    out["p_wild_cluster"] = {names[i]: float(wcb["p"][i]) for i in range(len(names))}
    out["r2"] = float(wcb["r2"])
    out["adj_r2"] = float(epb["adj_r2"])
    out["adj_r2_boot"] = {
        "mean": epb["boot_adj_r2_mean"],
        "lo": epb["boot_adj_r2_lo"],
        "hi": epb["boot_adj_r2_hi"],
    }
    out["n_clusters"] = int(wcb["n_clusters"])

    # Horse race
    layer_cols = [c for c in info["primary_cols"] if c.startswith("layer_")]
    base_controls = ["funding_pc1", "log_mkt_cap"] + layer_cols
    crowd_hr = incremental_adj_r2(design, "crowding_pc1", base_controls)
    val_hr = incremental_adj_r2(design, "valuation_pc1", base_controls)
    both_controls = base_controls  # funding + layer + mcap
    # both blocks together
    y2, X2, _ = design_matrix(design, ["crowding_pc1", "valuation_pc1"] + both_controls)
    _b, _r, r2_both = ols(y2, X2)
    ar2_both = adj_r2(r2_both, len(design), 2 + len(both_controls))
    out["horse_race"] = {
        "crowding": crowd_hr,
        "valuation": val_hr,
        "adj_r2_both_blocks_plus_controls": ar2_both,
        "valuation_beats_crowding_incremental": (
            val_hr["incremental_adj_r2"] > crowd_hr["incremental_adj_r2"]
        ),
    }
    out["status"] = "OK"
    return out


def run_sensitivity_impute(g: pd.DataFrame, gics: dict[str, str], seed: int) -> dict:
    design, info = prepare_episode(g, impute=True)
    if design.empty or info["n_complete"] < 5:
        return {"episode": info["episode"], "status": "TOO_FEW", "n_complete": info["n_complete"]}
    y, X, names = design_matrix(design, info["primary_cols"])
    clusters = design["ticker"].map(lambda t: gics.get(t, "UNKNOWN")).to_numpy()
    wcb = wild_cluster_bootstrap(y, X, clusters, n_boot=N_BOOT, seed=seed)
    return {
        "episode": info["episode"],
        "n_complete": info["n_complete"],
        "adj_r2": adj_r2(wcb["r2"], len(design), len(names) - 1),
        "coef_crowding_pc1": float(wcb["beta"][names.index("crowding_pc1")])
        if "crowding_pc1" in names
        else None,
        "coef_valuation_pc1": float(wcb["beta"][names.index("valuation_pc1")])
        if "valuation_pc1" in names
        else None,
        "status": "OK",
    }


def run_secondary(g: pd.DataFrame, with_ai: bool, gics: dict[str, str], seed: int) -> dict:
    """Full regressor list OLS with wild cluster SE."""
    g = g.loc[g["listed_at_start"] & g["edgar_eligible"]].copy()
    eid = g["episode"].iloc[0] if len(g) else None
    if g.empty:
        return {"episode": eid, "with_ai": with_ai, "status": "EMPTY"}
    for c in CROWDING_COLS + list(VALUATION_COLS) + [
        "net_debt_ebitda",
        "interest_coverage",
        "lease_liab_assets",
        "log_mkt_cap",
        "adv",
        "ai_revenue_exposure_0_3_JUDGMENT",
        "episode_return",
    ]:
        if c in g.columns:
            g[c] = winsorize(g[c].astype(float))
    dummies = layer_dummies(g["layer"])
    for c in dummies.columns:
        g[c] = dummies[c]
    cols = (
        CROWDING_COLS
        + list(VALUATION_COLS)
        + ["net_debt_ebitda", "interest_coverage", "lease_liab_assets", "log_mkt_cap", "adv"]
        + list(dummies.columns)
    )
    if with_ai:
        cols = cols + ["ai_revenue_exposure_0_3_JUDGMENT"]
    cols = [c for c in cols if c in g.columns]
    design = g.dropna(subset=["episode_return"] + cols)
    if len(design) < 5:
        return {
            "episode": eid,
            "with_ai": with_ai,
            "n_complete": len(design),
            "status": "TOO_FEW",
        }
    y, X, names = design_matrix(design, cols)
    clusters = design["ticker"].map(lambda t: gics.get(t, "UNKNOWN")).to_numpy()
    wcb = wild_cluster_bootstrap(y, X, clusters, n_boot=N_BOOT, seed=seed)
    return {
        "episode": eid,
        "with_ai": with_ai,
        "n_complete": len(design),
        "adj_r2": adj_r2(wcb["r2"], len(design), len(names) - 1),
        "coef": {names[i]: float(wcb["beta"][i]) for i in range(len(names))},
        "se_wild_cluster": {names[i]: float(wcb["se"][i]) for i in range(len(names))},
        "p_wild_cluster": {names[i]: float(wcb["p"][i]) for i in range(len(names))},
        "ai_tag": "JUDGMENT_CODED_POST_OUTCOME" if with_ai else None,
        "status": "OK",
    }


def run() -> dict:
    exhibits = study_outputs() / "exhibits"
    exhibits.mkdir(parents=True, exist_ok=True)
    panel = pd.read_parquet(ROOT / "data" / "processed" / "panel.parquet")
    gics = load_gics()

    primary_rows = []
    loadings_rows = []
    sens_rows = []
    secondary_rows = []
    falsifier_episodes = []

    print("=== H3 primary (complete cases) ===")
    for i, (eid, g) in enumerate(sorted(panel.groupby("episode"), key=lambda x: x[0])):
        print(f"\n--- {eid} ---")
        res = run_primary_episode(g, gics, seed=100 + i)
        print(
            f"N_complete={res.get('n_complete')}  adjR2={res.get('adj_r2')}  "
            f"excluded_from_falsifier={res.get('excluded_from_falsifier')}  status={res.get('status')}"
        )
        if res.get("horse_race"):
            hr = res["horse_race"]
            print(
                f"  incr adjR2 crowding={hr['crowding']['incremental_adj_r2']:.4f}  "
                f"valuation={hr['valuation']['incremental_adj_r2']:.4f}  "
                f"val_beats={hr['valuation_beats_crowding_incremental']}"
            )
        primary_rows.append(
            {
                "episode": eid,
                "n_complete": res.get("n_complete"),
                "excluded_from_falsifier": res.get("excluded_from_falsifier"),
                "adj_r2": res.get("adj_r2"),
                "r2": res.get("r2"),
                "n_clusters": res.get("n_clusters"),
                "funding_cols": ",".join(res.get("funding_cols") or []),
                "incr_adj_r2_crowding": (res.get("horse_race") or {})
                .get("crowding", {})
                .get("incremental_adj_r2"),
                "incr_adj_r2_valuation": (res.get("horse_race") or {})
                .get("valuation", {})
                .get("incremental_adj_r2"),
                "val_beats_crowding": (res.get("horse_race") or {}).get(
                    "valuation_beats_crowding_incremental"
                ),
                "adj_r2_crowd_only": (res.get("horse_race") or {})
                .get("crowding", {})
                .get("adj_r2_block_only"),
                "adj_r2_val_only": (res.get("horse_race") or {})
                .get("valuation", {})
                .get("adj_r2_block_only"),
                "adj_r2_both": (res.get("horse_race") or {}).get(
                    "adj_r2_both_blocks_plus_controls"
                ),
                "coef_crowding_pc1": (res.get("coef") or {}).get("crowding_pc1"),
                "coef_valuation_pc1": (res.get("coef") or {}).get("valuation_pc1"),
                "coef_funding_pc1": (res.get("coef") or {}).get("funding_pc1"),
                "p_crowding_pc1": (res.get("p_wild_cluster") or {}).get("crowding_pc1"),
                "p_valuation_pc1": (res.get("p_wild_cluster") or {}).get("valuation_pc1"),
                "status": res.get("status"),
            }
        )
        for block, loads in (res.get("loadings") or {}).items():
            for feat, val in (loads or {}).items():
                loadings_rows.append(
                    {"episode": eid, "block": block, "feature": feat, "loading": val}
                )
        for feat, v in (res.get("vif") or {}).items():
            loadings_rows.append(
                {"episode": eid, "block": "VIF", "feature": feat, "loading": v}
            )

        if not res.get("excluded_from_falsifier") and res.get("status") == "OK":
            falsifier_episodes.append(res)

        sens = run_sensitivity_impute(g, gics, seed=200 + i)
        sens_rows.append(sens)
        print(f"  sensitivity impute N={sens.get('n_complete')} adjR2={sens.get('adj_r2')}")

        for with_ai in (False, True):
            sec = run_secondary(g, with_ai, gics, seed=300 + i + int(with_ai))
            secondary_rows.append(
                {
                    "episode": eid,
                    "with_ai": with_ai,
                    "n_complete": sec.get("n_complete"),
                    "adj_r2": sec.get("adj_r2"),
                    "status": sec.get("status"),
                    "ai_tag": sec.get("ai_tag"),
                    "coef_ai": (sec.get("coef") or {}).get(
                        "ai_revenue_exposure_0_3_JUDGMENT"
                    ),
                }
            )

    primary_df = pd.DataFrame(primary_rows)
    primary_df.to_csv(exhibits / "h3_primary_by_episode.csv", index=False)
    pd.DataFrame(loadings_rows).to_csv(exhibits / "h3_pc_loadings_and_vif.csv", index=False)
    pd.DataFrame(sens_rows).to_csv(exhibits / "h3_sensitivity_median_impute.csv", index=False)
    pd.DataFrame(secondary_rows).to_csv(exhibits / "h3_secondary_full_regressors.csv", index=False)

    # Falsifier
    counted = primary_df.loc[~primary_df["excluded_from_falsifier"] & (primary_df["status"] == "OK")]
    n_val_beats = int(counted["val_beats_crowding"].fillna(False).sum())
    n_counted = int(len(counted))
    falsified = n_val_beats >= 4
    decision = (
        "REJECT crowding claim (valuation dominates)"
        if falsified
        else "FAIL TO REJECT crowding claim on falsifier"
    )
    summary = {
        "null": NULL,
        "falsifier": FALSIFIER,
        "n_episodes_counted": n_counted,
        "n_episodes_val_beats_crowding": n_val_beats,
        "falsifier_triggered": falsified,
        "decision": decision,
        "excluded_episodes": primary_df.loc[
            primary_df["excluded_from_falsifier"], "episode"
        ].tolist(),
        "ai_exposure_tag": "JUDGMENT_CODED_POST_OUTCOME",
        "valuation_label": "DEVIATION_FROM_SPEC",
    }
    (exhibits / "h3_falsifier_summary.json").write_text(json.dumps(summary, indent=2))
    print("\n=== H3 FALSIFIER ===")
    print(json.dumps(summary, indent=2))

    # tests_run log
    tests_path = study_outputs() / "tests_run.csv"
    tests = pd.read_csv(tests_path) if tests_path.exists() else pd.DataFrame()
    for tid in ("T005b", "H3_PRIMARY", "H3_HORSE_RACE", "H3_SECONDARY_AI", "H3_SENSITIVITY_IMPUTE"):
        if len(tests):
            tests = tests[tests["test_id"] != tid]
    extra = pd.DataFrame(
        [
            {
                "test_id": "T005b",
                "hypothesis": "H3",
                "description": "Trailing yields E/P S/P EBITDA/EV filing-lag (D6 fallback)",
                "status": "RUN_DEVIATION_FROM_SPEC",
                "raw_p": "",
                "bh_p": "",
                "effect": "",
                "n": int(primary_df["n_complete"].sum()),
                "notes": "Pre-P4 yields replace multiples; FDR family member",
            },
            {
                "test_id": "H3_PRIMARY",
                "hypothesis": "H3",
                "description": "Primary PC1 model wild-cluster + episode bootstrap",
                "status": decision.split()[0],
                "raw_p": "",
                "bh_p": "",
                "effect": f"val_beats={n_val_beats}/{n_counted}",
                "n": n_counted,
                "notes": json.dumps(summary),
            },
            {
                "test_id": "H3_HORSE_RACE",
                "hypothesis": "H3",
                "description": "adjR2 crowding-only / valuation-only / both",
                "status": "RUN",
                "raw_p": "",
                "bh_p": "",
                "effect": f"val_beats={n_val_beats}",
                "n": n_counted,
                "notes": "see h3_primary_by_episode.csv",
            },
            {
                "test_id": "H3_SECONDARY_AI",
                "hypothesis": "H3",
                "description": "Full regressors with/without AI exposure",
                "status": "RUN",
                "raw_p": "",
                "bh_p": "",
                "effect": "",
                "n": len(secondary_rows),
                "notes": "JUDGMENT_CODED_POST_OUTCOME",
            },
            {
                "test_id": "H3_SENSITIVITY_IMPUTE",
                "hypothesis": "H3",
                "description": "Median imputation + missing-indicator dummies",
                "status": "RUN",
                "raw_p": "",
                "bh_p": "",
                "effect": "",
                "n": len(sens_rows),
                "notes": "sensitivity only; primary=complete cases",
            },
        ]
    )
    pd.concat([tests, extra], ignore_index=True).to_csv(tests_path, index=False)
    return {"primary": primary_df, "summary": summary}


def main() -> None:
    run()


if __name__ == "__main__":
    main()
