#!/usr/bin/env python3
"""Study 5 end to end (seed 7). Fixture gate -> Phase 1 -> only the Phase 2 branch(es) Phase 1 selects -> credit side-check.
Pre-registration: PREREG.md (commit d9238e3)."""
import json
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from common import OUT, SEED, Ledger, check_fixtures  # noqa: E402
import pandas as pd  # noqa: E402
import phase1_split  # noqa: E402

random.seed(SEED)
np.random.seed(SEED)


def main() -> int:
    check_fixtures()
    L = Ledger()
    p1 = phase1_split.run(L)
    g = p1["variants"]["primary (EPS b)"]["growth"]
    print(f"PHASE 1: peak {p1['peak']} ({p1['peak_pe']:.2f}x) -> {p1['end']} ({g['pe_end']:.2f}x)")
    print(f"  Growth legs: PRICE {g['price_share']:.1%}, EPS {g['eps_share']:.1%}, COMPOSITION {g['comp_share']:.1%}, RESIDUAL {g['resid_share']:.1%}")
    print(f"  CLASSIFICATION: {p1['classification']}{' + ARTEFACT MATERIAL' if p1['artefact_material'] else ''}; branches to run: {p1['branches']}")
    print(f"  flips under robustness variants: {p1['flips']}")
    summary = {"phase1": {k: p1[k] for k in ("peak", "classification", "artefact_material", "branches", "flips")}}
    peak = pd.Timestamp(p1["peak"])
    if "2A" in p1["branches"]:
        import phase2a_quality
        r = phase2a_quality.run(L)
        summary["phase2a"] = r["verdict"]
        print(f"PHASE 2A: {r['verdict']}  inputs {r['rule_inputs']}")
    else:
        print("PHASE 2A: not run (not selected by Phase 1)")
        L.trial("2A", "Phase 2A", "not run", "", 0, "not selected by Phase 1 rule")
    if "2B" in p1["branches"]:
        import phase2b_rates
        r = phase2b_rates.run(L, peak)
        summary["phase2b"] = r["verdict"]
        print(f"PHASE 2B: {r['verdict']}  (explained share {r['real_yield_explained_share']:.0%})")
    else:
        print("PHASE 2B: not run (not selected by Phase 1)")
        L.trial("2B", "Phase 2B", "not run", "", 0, "not selected by Phase 1 rule")
    import phase2b_rates
    cr = phase2b_rates.credit_sidecheck(L, peak)
    summary["credit"] = cr
    L.write()
    # kill log (protocol rule 7)
    killed = [t for t in L.tests if t["status"] == "KILLED"]
    lines = ["# Killed hypotheses", "", "| ID | Claim | Killed by | Date |", "|---|---|---|---|"]
    lines += [f"| {t['test_id']} | {t['description']} | {t['effect']} | 2026-11-28 |" for t in killed]
    (OUT / "killed_hypotheses.md").write_text("\n".join(lines) + "\n")
    (OUT / "run_summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print(f"trials: {len(L.trials)}; tests: {len(L.tests)}; killed: {len(killed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
