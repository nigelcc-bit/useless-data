"""Write results/verdicts_train.md and results/killed_hypotheses.md from training outputs."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
L = pd.read_csv(R / "layer_tests_train.csv")
LED = pd.read_csv(ROOT / "ledger.csv")
H4 = pd.read_csv(R / "h4_incremental.csv")


def tbl(df):
    return df.to_markdown(index=False, floatfmt=".3f")


cols = ["asset", "target", "layer", "n_ep", "n_rows", "skill", "coef", "sign_h1", "sign_h2", "n_assets_same_sign",
        "p_perm", "p_bh", "verdict"]
v = L[cols].copy()
surv = v[v["verdict"] == "SURVIVES"]
killed = v[v["verdict"].str.startswith("KILLED")]
under = v[v["verdict"].str.startswith("UNDERPOWERED")]
inh = LED[LED["inherited_from"].fillna("").str.len() > 0][["test_id", "hypothesis", "statistic", "p_value", "p_bh", "n_events", "detail", "inherited_from"]]
txt = f"""# Training-period verdicts (events through 2017-12-31)

Written before the hold-out was run. Source: `results/layer_tests_train.csv`, `ledger.csv`.
Ledger: {len(LED)} tests, {int(LED['p_value'].notna().sum())} with p-values, **{int((LED['p_bh'] <= 0.10).sum())} survive BH at q = 0.10**.

## Summary per layer

| Layer | Verdict |
|---|---|
| L1 H1 Fed stance | {'SURVIVES somewhere' if (surv.layer=='H1').any() else 'KILLED on all assets and targets'} |
| L2 H2a realised-vol roll | {'SURVIVES somewhere' if (surv.layer=='H2a').any() else 'KILLED on all assets and targets'} |
| L2 H2b VIX/VIX3M exit (1.00) | {'SURVIVES somewhere' if (surv.layer=='H2b').any() else 'KILLED (SOX); UNDERPOWERED (SPX, NDX: fewer than 8 signal rows / 9-13 episodes, 2007-2017 only)'} |
| L2 H2b-095 | {'SURVIVES somewhere' if (surv.layer=='H2b095').any() else 'KILLED (SOX); UNDERPOWERED (SPX, NDX)'} |
| L2 H2c VIX >= 90th pct of 5y | {'SURVIVES somewhere' if (surv.layer=='H2c').any() else 'KILLED on all assets and targets'} |
| L3 H3 credit not confirming | {'SURVIVES somewhere' if (surv.layer=='H3').any() else 'KILLED on all assets and targets'} |
| L3 H4 Korea non-semis | NOT RUN (product split not obtainable; PREREGISTRATION B3) |
| L3 H4-total substitute | {'SURVIVES somewhere' if surv.layer.str.startswith('H4').any() else 'KILLED on all assets and targets (closest miss of the study: NDX T2, 3m change, skill +0.111, perm p 0.002, BH 0.110)'} |
| H5 structural break | descriptive only (report) |

Layer 0 (price/episode state only) is therefore **not beaten** by any pre-registered layer in training.

## Survivors

{tbl(surv) if len(surv) else 'None.'}

## Killed

{tbl(killed)}

## Underpowered (prior only; counts, no significance)

{tbl(under)}

## H4-total incremental value over the asset's own 63-session return

{tbl(H4)}

## Inherited thresholds (training, one row per episode)

{tbl(inh)}
"""
(R / "verdicts_train.md").write_text(txt)
k = ["# Killed hypotheses (Study 3)\n",
     "Same status as findings. Every row failed at least one pre-registered survival condition.\n",
     tbl(killed[["asset", "target", "layer", "skill", "p_perm", "p_bh", "verdict"]]),
     "\n\nAlso: H4 (Korea non-semis exports) NOT RUN, data gap. Inherited thresholds I1-I3, I1b, I2b: none "
     "significant after BH; I1 had zero qualifying events at the shock-close definition (see D2).\n"]
(R / "killed_hypotheses.md").write_text("\n".join(k))
print(txt[:1800])
