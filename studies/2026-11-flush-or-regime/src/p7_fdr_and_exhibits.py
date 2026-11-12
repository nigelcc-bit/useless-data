"""P7 — FDR across the pre-registered family + house-style exhibits.

- Benjamini–Hochberg q=0.10 over every pre-registered test row in
  tests_run.csv (NOT_RUN/underpowered listed with reason).
- Exploratory / DEVIATION rows in a separate table (unadjusted).
- Romano–Wolf stepdown for the H3 regressor-block horse race.
- 10–14 exhibits in house style.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from core.config_io import ROOT, study_outputs
from core.stats.fdr import benjamini_hochberg
from core.stats.romano_wolf import romano_wolf_stepdown_pvalues
from src.viz import HOUSE

EXHIBITS = study_outputs() / "exhibits"
CREAM = HOUSE["cream"]
ORANGE = HOUSE["orange"]
DARK = HOUSE["dark"]
JUDGMENT = "#6B5B4F"  # visually distinct from measurement orange


def _parse_p(x) -> float:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return float("nan")
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if not s or s.lower() in ("nan", "none", ""):
        return float("nan")
    if s.startswith("<"):
        # "< 0.001 (0 of 999)" → 0.001 for BH (conservative upper bound on p)
        m = re.search(r"<\s*([0-9.]+)", s)
        return float(m.group(1)) if m else 0.001
    try:
        return float(s)
    except ValueError:
        return float("nan")


# Statuses that are NOT in the pre-registered FDR family
EXPLORATORY_STATUSES = {
    "EXPLORATORY",
    "EXPLORATORY_UNTESTED",
    "EXPLORATORY_NOT_FDR",
    "DIAGNOSTIC",
    "DEVIATION_FROM_SPEC",
    "RUN_DEVIATION_FROM_SPEC",
    "FROZEN_TEST_INVALID",
    "SUPERSEDED",
    "SUPERSEDED_TARGETS",
    "COUNTS",
    "LOGGED",
}


def classify_row(row: pd.Series) -> str:
    st = str(row.get("status", ""))
    tid = str(row.get("test_id", ""))
    if st in EXPLORATORY_STATUSES or "EXPLORATORY" in st or "DEVIATION" in st:
        return "exploratory"
    if st == "FROZEN_TEST_INVALID" or "INVALID" in st:
        return "exploratory"
    if tid.startswith("H4_ROBUST") or tid.startswith("H2_NOV"):
        return "exploratory"
    if tid.startswith("H3_REVIEW"):
        return "exploratory"
    # SUPERSEDED_BY keeps the placeholder in the pre-registered ledger (no p)
    # Pre-registered family (includes NOT_RUN / underpowered / PRIOR_ONLY)
    return "preregistered"


def run_fdr(q: float = 0.10) -> dict:
    tests = pd.read_csv(study_outputs() / "tests_run.csv")
    tests["raw_p_num"] = tests["raw_p"].map(_parse_p)
    tests["family"] = tests.apply(classify_row, axis=1)

    pre = tests.loc[tests["family"] == "preregistered"].copy()
    exp = tests.loc[tests["family"] == "exploratory"].copy()

    # BH on rows with numeric p
    has_p = pre["raw_p_num"].notna()
    bh = benjamini_hochberg(pre.loc[has_p, "raw_p_num"], q=q)
    pre["bh_p"] = np.nan
    pre["reject_bh_q10"] = False
    pre.loc[has_p, "bh_p"] = bh["bh_p"].to_numpy()
    pre.loc[has_p, "reject_bh_q10"] = bh["reject_q"].to_numpy()

    # Reasons for no p
    def _reason(r):
        if np.isfinite(r["raw_p_num"]):
            return ""
        st = str(r["status"])
        if st.startswith("SUPERSEDED_BY"):
            return st  # placeholder retired; FDR family unchanged (no p)
        if st in ("NOT_RUN", "NOT_RUN_UNDERPOWERED"):
            return f"{st}: {r.get('notes', '') or r.get('description', '')}"
        if st in ("PRIOR_ONLY",):
            return "PRIOR_ONLY — N floor not met; not tested"
        if st in ("PASS", "DONE", "KEPT", "RESOLVED_VIA_P1", "UNSUPPORTED", "REJECT", "OPEN"):
            return f"status={st} (no numeric p; decision/gate row)"
        if st == "COUNTS":
            return "COUNTS only"
        return f"no numeric p (status={st})"

    pre["no_p_reason"] = pre.apply(_reason, axis=1)

    # Write back bh_p into tests_run for rows we adjusted
    tests = tests.copy()
    tests["bh_p"] = tests["bh_p"].astype(object)
    tests["bh_p"] = ""
    for idx, row in pre.iterrows():
        if np.isfinite(row.get("bh_p", np.nan)):
            tid = row["test_id"]
            tests.loc[tests["test_id"] == tid, "bh_p"] = f"{float(row['bh_p']):.6g}"
    tests.to_csv(study_outputs() / "tests_run.csv", index=False)

    pre.to_csv(EXHIBITS / "p7_fdr_preregistered.csv", index=False)
    exp.to_csv(EXHIBITS / "p7_fdr_exploratory_unadjusted.csv", index=False)

    # Romano–Wolf for H3 block horse race (crowding vs valuation PC1 p's, E3–E7)
    h3 = pd.read_csv(EXHIBITS / "h3_primary_by_episode.csv")
    rw_inputs = {}
    for _, r in h3.iterrows():
        ep = r["episode"]
        if ep in ("E1", "E2"):
            continue  # degenerate / fragile
        if pd.notna(r["p_crowding_pc1"]):
            rw_inputs[f"{ep}_crowding_pc1"] = float(r["p_crowding_pc1"])
        if pd.notna(r["p_valuation_pc1"]):
            rw_inputs[f"{ep}_valuation_pc1"] = float(r["p_valuation_pc1"])
    rw = romano_wolf_stepdown_pvalues(rw_inputs, rho=0.4, seed=717)
    rw.to_csv(EXHIBITS / "p7_romano_wolf_h3_blocks.csv", index=False)

    summary = {
        "q": q,
        "n_preregistered": int(len(pre)),
        "n_with_p": int(has_p.sum()),
        "n_reject_bh": int(pre["reject_bh_q10"].sum()),
        "n_exploratory": int(len(exp)),
        "n_nop_listed": int((~has_p).sum()),
        "romano_wolf_h3": rw.to_dict(orient="records"),
    }
    (EXHIBITS / "p7_fdr_summary.json").write_text(json.dumps(summary, indent=2))
    print("=== FDR summary ===")
    print(json.dumps(summary, indent=2))
    print("\nPre-registered with p (raw / BH):")
    cols = ["test_id", "hypothesis", "status", "raw_p_num", "bh_p", "reject_bh_q10"]
    print(pre.loc[has_p, cols].to_string(index=False))
    print("\nRomano–Wolf H3 blocks:")
    print(rw.to_string(index=False))
    return summary


def _style(ax, title: str, method_tag: str, judgment: bool = False):
    ax.set_facecolor(CREAM)
    ax.figure.patch.set_facecolor(CREAM)
    ax.set_title(title, color=DARK, fontsize=12, pad=10)
    ax.text(
        0.99,
        0.02,
        f"method: {method_tag}" + (" | JUDGMENT" if judgment else ""),
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color=JUDGMENT if judgment else DARK,
        alpha=0.85,
    )
    for spine in ax.spines.values():
        spine.set_color(DARK)
        spine.set_linewidth(0.6)
    ax.tick_params(colors=DARK)
    ax.yaxis.label.set_color(DARK)
    ax.xaxis.label.set_color(DARK)


def make_exhibits() -> list[Path]:
    EXHIBITS.mkdir(parents=True, exist_ok=True)
    out_paths: list[Path] = []

    def save(fig, name):
        p = EXHIBITS / name
        fig.savefig(p, dpi=140, bbox_inches="tight", facecolor=CREAM)
        plt.close(fig)
        out_paths.append(p)
        print("wrote", p.name)

    # 1. ETF / note reproduction bars
    fig, ax = plt.subplots(figsize=(8, 4.5))
    labels = ["SOXX", "SMH", "QQQ", "SPY"]
    vals = [-12.15, -11.21, -6.49, -4.41]
    ax.bar(labels, vals, color=ORANGE, edgecolor=DARK)
    ax.axhline(0, color=DARK, lw=0.8)
    ax.set_ylabel("5 Nov 2026 return (%)")
    _style(ax, "5 Nov ETF moves (Yahoo = IBKR; N=1 day)", "descriptive frequency")
    save(fig, "fig01_etf_nov5.png")

    # 2. Builder vs supplier EW
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(
        ["Builders EW\n(N=6)", "Suppliers EW\n(N=16 note book)", "Neocloud EW\n(N=3)"],
        [-2.98, -13.53, -13.91],
        color=[DARK, ORANGE, ORANGE],
        edgecolor=DARK,
    )
    ax.axhline(0, color=DARK, lw=0.8)
    ax.set_ylabel("5 Nov return (%)")
    _style(ax, "Builder–supplier gap larger than the note printed", "descriptive frequency")
    save(fig, "fig02_builder_supplier_ew.png")

    # 3. H1b further-DD rates — SOX/SPX primary; others muted descriptive
    h1b = pd.read_csv(EXHIBITS / "h1b_forward_summary.csv")
    ep = pd.read_csv(EXHIBITS / "h1b_episodes.csv")
    n_bear = ep.groupby("series").size().to_dict()
    order = ["SPX", "SOX", "SMH", "SOXX", "IXIC"]
    h1b = h1b.set_index("series").reindex(order).reset_index()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = []
    for s in h1b["series"]:
        if s in ("SOX", "SPX"):
            colors.append(ORANGE if s == "SOX" else DARK)
        else:
            colors.append("#C8C0B4")  # muted cream-grey
    rates = h1b["rate"] * 100
    bars = ax.bar(h1b["series"], rates, color=colors, edgecolor=DARK)
    for bar, (_, row) in zip(bars, h1b.iterrows()):
        n_ev = int(row["n"])
        n_bm = int(n_bear.get(row["series"], 0))
        label = "primary" if row["series"] in ("SOX", "SPX") else "descriptive"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.2,
            f"N={n_ev} ev\n{n_bm} bears\n({label})",
            ha="center",
            va="bottom",
            fontsize=7,
            color=DARK if row["series"] in ("SOX", "SPX") else "#8A8074",
        )
    ax.axhline(25, color="#5A5A5A", ls="--", lw=1.2, label="≤25% patience (dashed)")
    ax.axhline(50, color="#B85A2A", ls="--", lw=1.2, label="≥50% another leg (dashed)")
    ax.set_ylim(0, max(rates.max() + 18, 60))
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.set_ylabel("Further 10% DD within 63d (%)")
    _style(
        ax,
        "H1b deep-DD continuation — SOX vs SPX primary (N on bars)",
        "conditional frequency",
    )
    save(fig, "fig03_h1b_continuation.png")

    # 4. H3 Shapley
    shap = pd.read_csv(EXHIBITS / "h3_shapley_r2_e5_e7.csv")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    pivot = shap.pivot(index="block", columns="episode", values="shapley_r2")
    pivot.plot(kind="bar", ax=ax, color=[DARK, ORANGE, "#C45A1A"], edgecolor=DARK)
    ax.set_ylabel("Shapley R²")
    ax.legend(frameon=False, title="")
    _style(ax, "H3 Shapley R² — layer dominates E5–E7 (complete-case N≈35–36)", "panel regression")
    save(fig, "fig04_h3_shapley.png")

    # 5. H3 incremental adj-R2 horse race
    prim = pd.read_csv(EXHIBITS / "h3_primary_by_episode.csv")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ep = prim.loc[~prim["excluded_from_falsifier"].astype(bool) | (prim["excluded_from_falsifier"] == False)]
    # include all with values
    sub = prim.dropna(subset=["incr_adj_r2_crowding", "incr_adj_r2_valuation"], how="all")
    x = np.arange(len(sub))
    w = 0.35
    ax.bar(x - w / 2, sub["incr_adj_r2_crowding"], w, label="crowding incr", color=ORANGE, edgecolor=DARK)
    ax.bar(x + w / 2, sub["incr_adj_r2_valuation"], w, label="valuation incr", color=DARK, edgecolor=DARK)
    ax.set_xticks(x)
    ax.set_xticklabels(sub["episode"])
    ax.axhline(0, color=DARK, lw=0.8)
    ax.legend(frameon=False, fontsize=8)
    ax.set_ylabel("Incremental adj-R²")
    ax.set_xticklabels(
        [f"{r.episode}\nN={int(r.n_complete)}" for r in sub.itertuples()], fontsize=8
    )
    _style(ax, "H3 horse race: incremental adj-R² by episode", "panel regression")
    save(fig, "fig05_h3_horse_race.png")

    # 6. H4 slope × E7 interactions — wild + CR2 CIs
    inter = pd.read_csv(EXHIBITS / "h4_slope_interactions_ci.csv")
    inter = inter.copy()
    inter["ci95_lo_cr2"] = inter["coef"] - 1.96 * inter["se_cr2"]
    inter["ci95_hi_cr2"] = inter["coef"] + 1.96 * inter["se_cr2"]
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    y = np.arange(len(inter))
    ax.hlines(
        y - 0.12,
        inter["ci95_lo_pct"],
        inter["ci95_hi_pct"],
        color=ORANGE,
        lw=1.6,
        label="wild-boot 95% CI",
    )
    ax.hlines(
        y + 0.12,
        inter["ci95_lo_cr2"],
        inter["ci95_hi_cr2"],
        color=DARK,
        lw=1.2,
        label="CR2 95% CI",
    )
    ax.plot(inter["coef"], y, "o", color=ORANGE, markersize=7, zorder=3)
    ax.axvline(0, color=DARK, lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(inter["interaction"], fontsize=8)
    ax.set_xlabel("Slope × E7 coefficient (N=72 stacked; 11 df)")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    _style(
        ax,
        "H4 slope×E7 — Holm: no interaction @5%; joint Wald rejects (BH p=0.011)",
        "panel regression",
    )
    save(fig, "fig06_h4_interactions.png")

    # 7. Layer taxonomy (JUDGMENT)
    from core.features.layer import layer_assignments

    layers = layer_assignments()
    counts = layers.groupby("layer").size().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(counts.index, counts.values, color=JUDGMENT, edgecolor=DARK)
    ax.set_xlabel("N names")
    _style(ax, "Universe by layer (judgment-coded)", "judgment", judgment=True)
    save(fig, "fig07_layer_taxonomy_judgment.png")

    # 8. H2 VR
    vr = pd.read_csv(EXHIBITS / "h2_variance_ratio.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(vr["q"], vr["vr"], "-o", color=ORANGE, lw=2, markersize=8)
    ax.axhline(1.0, color=DARK, ls="--", lw=0.8)
    ax.set_xlabel("q (sessions)")
    ax.set_ylabel("Variance ratio")
    n_vr = int(vr["n"].iloc[0]) if "n" in vr.columns else 965
    _style(ax, f"H2 Lo–MacKinlay VR (hetero z*; N={n_vr} days; CD non-reject)", "event study")
    save(fig, "fig08_h2_variance_ratio.png")

    # 9. H2 forward net returns
    fwd = pd.read_csv(EXHIBITS / "h2_forward_summary.csv")
    pooled = fwd.loc[fwd["scope"] == "pooled"]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(
        pooled["horizon"].astype(str) + "d",
        pooled["mean_net"] * 100,
        color=ORANGE,
        edgecolor=DARK,
        yerr=pooled["se_nw"] * 100,
        capsize=4,
    )
    ax.axhline(0, color=DARK, lw=0.8)
    ax.set_ylabel("Mean net forward spread (%)")
    _style(ax, "H2 pooled fwd spread net 30bp (N=9; K004)", "event study")
    save(fig, "fig09_h2_forward.png")

    # 10. H2 event z path sample year
    series = pd.read_csv(EXHIBITS / "h2_spread_series.csv", index_col=0, parse_dates=True)
    if "spread_z" not in series.columns:
        # recompute quickly from residual
        from src.h2_spread_factor import causal_z

        series["spread_z"] = causal_z(series["spread_beta_neutral"].dropna())
    fig, ax = plt.subplots(figsize=(9, 4))
    sub = series.loc["2025":]
    ax.plot(sub.index, sub["spread_z"], color=DARK, lw=0.9)
    ax.axhline(-2.5, color=ORANGE, ls="--", lw=1, label="−2.5σ")
    ax.legend(frameon=False, fontsize=8)
    ax.set_ylabel("Causal spread z")
    _style(ax, "H2 beta-neutral spread z (2025–; causal σ)", "event study")
    save(fig, "fig10_h2_spread_z.png")

    # 11. H5 trough L5 values
    troughs = pd.read_csv(EXHIBITS / "h5_trough_list.csv", parse_dates=["trough_date"])
    fig, ax = plt.subplots(figsize=(9, 4))
    colors = [ORANGE if s == "oos" else DARK for s in troughs["walk_forward_split"]]
    ax.scatter(troughs["trough_date"], troughs["L5"], c=colors, edgecolors=DARK, s=40)
    ax.axhline(0, color=DARK, lw=0.8)
    ax.set_ylabel("L(5)")
    n_tr = int((troughs["walk_forward_split"] == "train").sum())
    n_oos = int((troughs["walk_forward_split"] == "oos").sum())
    _style(
        ax,
        f"H5 L(5) troughs (dark=train N={n_tr}, orange=OOS N={n_oos}) — PRIOR ONLY",
        "event study",
    )
    save(fig, "fig11_h5_L5_troughs.png")

    # 12. Outcomes scorecard
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.axis("off")
    rows = [
        ("#1 flush/patience (H2+H5)", "DEAD — H2 K004; H5 PRIOR ONLY"),
        ("#2 profit pool to builders (H4)", "TRIGGERED"),
        ("#3 Call 5 does not apply (H1)", "INCONCLUSIVE (H1b 40%)"),
        ("#4 valuation dominates (H3)", "NOT TRIGGERED; crowding unsupported"),
    ]
    for i, (a, b) in enumerate(rows):
        ax.text(0.02, 0.85 - i * 0.22, a, fontsize=11, color=DARK, fontweight="bold")
        ax.text(0.55, 0.85 - i * 0.22, b, fontsize=11, color=ORANGE)
    _style(ax, "Pre-registered outcomes scorecard", "descriptive frequency")
    save(fig, "fig12_outcomes_scorecard.png")

    # 13. Kill log summary
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.axis("off")
    kills = [
        ("K001", "Call 3 magnitudes / supplier EW"),
        ("K002", "Call 5 transfers to semis"),
        ("K003", "Crowding-not-valuation (H3)"),
        ("K004", "Seesaw is a mean-reverting factor (H2)"),
    ]
    for i, (k, t) in enumerate(kills):
        ax.text(0.05, 0.8 - i * 0.2, k, fontsize=12, color=ORANGE, fontweight="bold")
        ax.text(0.2, 0.8 - i * 0.2, t, fontsize=11, color=DARK)
    _style(ax, "Kill log — equal status to findings", "descriptive frequency")
    save(fig, "fig13_kill_log.png")

    # 14. AI exposure JUDGMENT
    try:
        from core.features.layer import ai_revenue_exposure

        ai = ai_revenue_exposure("E7").dropna()
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(ai, bins=[-0.5, 0.5, 1.5, 2.5, 3.5], color=JUDGMENT, edgecolor=DARK, align="mid")
        ax.set_xticks([0, 1, 2, 3])
        ax.set_xlabel("AI exposure score (0–3)")
        ax.set_ylabel("N names")
        _style(ax, "AI exposure scores E7 (judgment-coded, post-outcome)", "judgment", judgment=True)
        save(fig, "fig14_ai_exposure_judgment.png")
    except Exception as e:  # noqa: BLE001
        print("skip fig14", e)

    # Caption index
    captions = [
        {"file": p.name, "path": str(p.relative_to(ROOT))} for p in out_paths
    ]
    (EXHIBITS / "p7_exhibit_index.json").write_text(json.dumps(captions, indent=2))
    return out_paths


def main() -> None:
    run_fdr(q=0.10)
    paths = make_exhibits()
    print(f"\n{len(paths)} exhibits written.")


if __name__ == "__main__":
    main()
