"""Collect the 20 pre-registered Tier 1 primary p-values, apply
Benjamini-Hochberg across the tier, and write the programme ledger.

Writes:
  outputs/TIER1_SUMMARY.md
  outputs/tests_run.csv          — all 20 primary tests (raw_p, bh_p)
  outputs/killed_hypotheses.md   — failures vs within-study / kill criteria

Run after analyses/s01–s04. Without prior study outputs, registers the 20
tests as NOT_RUN (still writes the ledger rows).
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from common import ROOT, md_table
from bear_trap.inference import bh_fdr

OUT = ROOT / "outputs"
LEDGER = OUT / "tests_run.csv"
KILL = OUT / "killed_hypotheses.md"

# Canonical 20 primary tests (order fixed for BH across Tier 1).
PRIMARY_TESTS = [
    # Study A — 4
    dict(test_id="T1A_NDX_RECLAIM", study="A", hypothesis="A",
         description="NDX reclaim_rate vs block null", within_alpha=0.05 / 4,
         kill_claim="reclaim rate differs from block null (NDX)"),
    dict(test_id="T1A_NDX_RETEST", study="A", hypothesis="A",
         description="NDX retest_rate vs block null", within_alpha=0.05 / 4,
         kill_claim="retests-are-the-norm as market-structure (NDX)"),
    dict(test_id="T1A_SPX_RECLAIM", study="A", hypothesis="A",
         description="SPX reclaim_rate vs block null", within_alpha=0.05 / 4,
         kill_claim="reclaim rate differs from block null (SPX)"),
    dict(test_id="T1A_SPX_RETEST", study="A", hypothesis="A",
         description="SPX retest_rate vs block null", within_alpha=0.05 / 4,
         kill_claim="retests-are-the-norm as market-structure (SPX)"),
    # Study B — 12
    *[
        dict(
            test_id=f"T1B_{ix}_{kind}_R{h}",
            study="B", hypothesis="B",
            description=f"{ix} {kind} r{h} vs drawdown-matched placebo",
            within_alpha=0.05 / 12,
            kill_claim=f"second-sweep edge ({ix} {kind} r{h})",
            index=ix, kind=kind, h=h,
        )
        for kind in ("B1", "B2")
        for ix in ("NDX", "SPX")
        for h in (20, 60, 120)
    ],
    # Study C — 2
    dict(test_id="T1C_NDX_RETEST_LR", study="C", hypothesis="C",
         description="NDX retest curve vs null (log-rank)", within_alpha=0.05 / 2,
         kill_claim="retest survival differs from null (NDX)"),
    dict(test_id="T1C_SPX_RETEST_LR", study="C", hypothesis="C",
         description="SPX retest curve vs null (log-rank)", within_alpha=0.05 / 2,
         kill_claim="retest survival differs from null (SPX)"),
    # Study D — 2
    dict(test_id="T1D_POOLED_R60", study="D", hypothesis="D",
         description="pooled mean excess r60", within_alpha=0.05 / 2,
         kill_claim="pooled excess return edge at 60d"),
    dict(test_id="T1D_POOLED_R120", study="D", hypothesis="D",
         description="pooled mean excess r120", within_alpha=0.05 / 2,
         kill_claim="pooled excess return edge at 120d"),
]


def _bh_adjusted_p(pvals: np.ndarray) -> np.ndarray:
    """BH-adjusted p-values (step-up), NaN-safe."""
    p = np.asarray(pvals, float)
    m = p.size
    adj = np.full(m, np.nan)
    ok = np.isfinite(p)
    if not ok.any():
        return adj
    idx = np.flatnonzero(ok)
    pv = p[idx]
    order = np.argsort(pv)
    ranked = pv[order]
    n = ranked.size
    out = np.empty(n)
    out[-1] = min(1.0, ranked[-1])
    for i in range(n - 2, -1, -1):
        out[i] = min(out[i + 1], ranked[i] * n / (i + 1))
    adj[idx[order]] = out
    return adj


def _collect_pvalues() -> dict[str, float]:
    """Map test_id -> raw p from study outputs when present."""
    found: dict[str, float] = {}
    a = OUT / "A_null_models" / "summary.csv"
    if a.exists():
        d = pd.read_csv(a)
        d = d[(d.model == "block") & (d.level == "min")
              & d.metric.isin(["reclaim_rate", "retest_rate"])]
        for _, r in d.iterrows():
            key = f"T1A_{r['index']}_{'RECLAIM' if r.metric == 'reclaim_rate' else 'RETEST'}"
            found[key] = float(r.p)
    b = OUT / "B_second_sweep" / "results.csv"
    if b.exists():
        d = pd.read_csv(b)
        for _, r in d.iterrows():
            key = f"T1B_{r['index']}_{r.kind}_R{int(r.h)}"
            found[key] = float(r.p_placebo)
    c = OUT / "C_survival" / "km_tables.csv"
    if c.exists():
        d = pd.read_csv(c)
        d = d[(d.event == "retest of sweep low") & (d.days_survived == 0)]
        if "logrank_p_vs_null" in d.columns:
            for _, r in d.iterrows():
                found[f"T1C_{r['index']}_RETEST_LR"] = float(r.logrank_p_vs_null)
    dp = OUT / "D_panel" / "pooled.csv"
    if dp.exists():
        d = pd.read_csv(dp)
        for _, r in d.iterrows():
            if r.stat == "mean excess r60":
                found["T1D_POOLED_R60"] = float(r.p_placebo)
            elif r.stat == "mean excess r120":
                found["T1D_POOLED_R120"] = float(r.p_placebo)
    return found


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    found = _collect_pvalues()
    rows = []
    for spec in PRIMARY_TESTS:
        tid = spec["test_id"]
        raw = found.get(tid, np.nan)
        status = "PASS" if tid in found else "NOT_RUN"
        rows.append({
            "test_id": tid,
            "hypothesis": spec["hypothesis"],
            "description": spec["description"],
            "status": status,
            "raw_p": "" if not np.isfinite(raw) else f"{raw:.6g}",
            "bh_p": "",
            "effect": "",
            "n": "",
            "notes": "family=tier1_primary; within_alpha="
                     f"{spec['within_alpha']:.6g}",
            "raw_p_num": raw if np.isfinite(raw) else np.nan,
            "family": "tier1_primary",
            "within_alpha": spec["within_alpha"],
            "kill_claim": spec["kill_claim"],
            "study": spec["study"],
        })

    T = pd.DataFrame(rows)
    n_expected = 20
    assert len(T) == n_expected, f"expected {n_expected} primary tests, got {len(T)}"

    raw_nums = T["raw_p_num"].to_numpy(float)
    bh_adj = _bh_adjusted_p(raw_nums)
    bh_reject = bh_fdr(np.nan_to_num(raw_nums, nan=1.0), 0.05)
    T["bh_p"] = ["" if not np.isfinite(v) else f"{v:.6g}" for v in bh_adj]
    T["bh_reject_q05"] = bh_reject
    T["within_study_sig"] = [
        bool(np.isfinite(p) and p < a)
        for p, a in zip(raw_nums, T["within_alpha"])
    ]

    # Programme ledger columns
    ledger_cols = [
        "test_id", "hypothesis", "description", "status",
        "raw_p", "bh_p", "effect", "n", "notes", "raw_p_num", "family",
    ]
    # Preserve any non-tier1 rows already in the ledger
    if LEDGER.exists():
        prev = pd.read_csv(LEDGER)
        keep = prev[~prev["test_id"].isin(T["test_id"])] if "test_id" in prev.columns else prev.iloc[0:0]
        out_ledger = pd.concat([keep, T[ledger_cols]], ignore_index=True)
    else:
        out_ledger = T[ledger_cols]
    out_ledger.to_csv(LEDGER, index=False)

    # Kill log: within-study failures that meet kill criteria framing.
    # For Tier 1, a "kill" is logged when a primary test ran and did NOT reject
    # at the within-study alpha where the PREREG kill criterion is "no edge /
    # inside null" — i.e. status ran and not within_study_sig for claims that
    # die when the null holds. We also log BH-tier failures of H1-style edges.
    kill_lines = [
        "# Killed hypotheses",
        "",
        "Equal in status to the findings. Populated by `analyses/s99_tier1_summary.py` "
        "after s01–s04. Empty until a real-data Tier 1 run.",
        "",
        "| ID | Claim | Killed by | Date | Note |",
        "|---|---|---|---|---|",
    ]
    today = date.today().isoformat()
    kills = 0
    for _, r in T.iterrows():
        if r["status"] == "NOT_RUN":
            continue
        p = r["raw_p_num"]
        # Kill criteria in PREREG: claims die when test does NOT beat alpha
        # (no edge / inside null). Log those as kills of the edge claim.
        if np.isfinite(p) and not r["within_study_sig"]:
            kills += 1
            kid = f"K-{r['test_id']}"
            kill_lines.append(
                f"| {kid} | {r['kill_claim']} | {r['test_id']} "
                f"(p={r['raw_p']}, α={r['within_alpha']:.4g}) | {today} | "
                f"within-study non-reject; BH_p={r['bh_p'] or 'n/a'} |"
            )
    if kills == 0:
        kill_lines.append("| — | — | — | — | no Tier 1 kills yet |")
    kill_lines.append("")
    KILL.write_text("\n".join(kill_lines))

    # Summary markdown
    summary = T[["test_id", "study", "description", "status", "raw_p", "bh_p",
                 "within_study_sig", "bh_reject_q05"]].copy()
    note = "" if (T["status"] == "PASS").sum() == n_expected else (
        f"\n\nWARNING: {(T['status'] == 'PASS').sum()} of {n_expected} "
        f"pre-registered tests have results; others are NOT_RUN."
    )
    txt = "# Tier 1 primary tests\n\n" + md_table(summary, "{:.4f}") + note + "\n"
    (OUT / "TIER1_SUMMARY.md").write_text(txt)
    print(txt)
    print(f"Wrote {LEDGER}")
    print(f"Wrote {KILL}")


if __name__ == "__main__":
    main()
