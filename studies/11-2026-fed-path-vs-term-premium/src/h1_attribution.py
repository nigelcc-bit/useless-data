"""H1: term-premium share of the 2026 rise in the 10y zero yield (ACM and KW).
Also: 2y sanity line, robustness R4 (ACM, end 2026-11-17) and R5 (real vs breakeven).

    python -m src.h1_attribution
"""
from __future__ import annotations

import pandas as pd

from src import load
from src.common import BP, END_2026, OUT, log_run, log_test, share

START = pd.Timestamp("2025-12-31")
END_R4 = pd.Timestamp("2026-11-17")


def _at(s: pd.Series, d: pd.Timestamp) -> float:
    if d not in s.index or pd.isna(s.loc[d]):
        raise KeyError(f"{s.name} not published on {d.date()}")
    return float(s.loc[d])


def split(y: pd.Series, rny: pd.Series, tp: pd.Series, start, end, model, maturity, check) -> dict:
    dy = (_at(y, end) - _at(y, start)) * BP
    drny = (_at(rny, end) - _at(rny, start)) * BP
    dtp = (_at(tp, end) - _at(tp, start)) * BP
    return {"check": check, "model": model, "maturity": maturity, "start": start.date(), "end": end.date(),
            "y_start": _at(y, start), "tp_start": _at(tp, start),
            "d_y_bp": dy, "d_rny_bp": drny, "d_tp_bp": dtp,
            "residual_bp": dy - drny - dtp, "tp_share": share(dtp, dy)}


def decide(shares: list[float]) -> str:
    if any(pd.isna(s) for s in shares):
        return "no claim (|dy| < 25bp in at least one model)"
    if all(s > 0.5 for s in shares):
        return "term-premium driven"
    if all(s < 0.5 for s in shares):
        return "path driven"
    return "model-dependent, no claim"


def main() -> pd.DataFrame:
    a, kw, f = load.acm(), load.kim_wright(), load.fred()
    rows = []
    for n, k in [(10, "10"), (2, "02")]:
        tag = "H1" if n == 10 else "2y sanity"
        rows.append(split(a[f"ACMY{k}"], a[f"ACMRNY{k}"], a[f"ACMTP{k}"], START, END_2026, "ACM", n, tag))
        rows.append(split(kw[f"KWY{n}"], kw[f"KWRNY{n}"], kw[f"KWTP{n}"], START, END_2026, "KW", n, tag))
    rows.append(split(a["ACMY10"], a["ACMRNY10"], a["ACMTP10"], START, END_R4, "ACM", 10, "R4"))

    # R5: par DGS10 vs real DFII10 + breakeven T10YIE (different split, not a TP split)
    d10 = (_at(f["DGS10"], END_2026) - _at(f["DGS10"], START)) * BP
    dre = (_at(f["DFII10"], END_2026) - _at(f["DFII10"], START)) * BP
    dbe = (_at(f["T10YIE"], END_2026) - _at(f["T10YIE"], START)) * BP
    rows.append({"check": "R5", "model": "FRED par", "maturity": 10, "start": START.date(), "end": END_2026.date(),
                 "y_start": _at(f["DGS10"], START), "d_y_bp": d10, "d_real_bp": dre, "d_breakeven_bp": dbe,
                 "residual_bp": d10 - dre - dbe,
                 "breakeven_share": share(dbe, d10)})
    out = pd.DataFrame(rows)

    h1 = out[out.check == "H1"].set_index("model")
    verdict = decide([h1.loc["ACM", "tp_share"], h1.loc["KW", "tp_share"]])
    out["verdict"] = ""
    out.loc[out.check == "H1", "verdict"] = verdict
    r4 = out[out.check == "R4"].iloc[0]
    r4_side = "n/a" if pd.isna(r4.tp_share) else ("above 0.5" if r4.tp_share > 0.5 else "at or below 0.5")
    out.loc[out.check == "R4", "verdict"] = f"ACM share {r4_side}"
    out.to_csv(OUT / "h1_attribution.csv", index=False, float_format="%.6g")

    effect = (f"ACM share {h1.loc['ACM','tp_share']:.3f} (dy {h1.loc['ACM','d_y_bp']:.1f}bp, dTP {h1.loc['ACM','d_tp_bp']:.1f}bp); "
              f"KW share {h1.loc['KW','tp_share']:.3f} (dy {h1.loc['KW','d_y_bp']:.1f}bp, dTP {h1.loc['KW','d_tp_bp']:.1f}bp)")
    log_test("H1", "H1", "TP share of dy10, 2025-12-31 to 2026-11-13, ACM and KW (decision rule, no p)",
             verdict, None, effect, 2, "decision rule, not in FDR family", "decision_rule")
    log_test("R4", "H1", "H1 ACM share with end date 2026-11-17", f"ACM share {r4_side}", None,
             f"ACM share {r4.tp_share:.3f} (dy {r4.d_y_bp:.1f}bp, dTP {r4.d_tp_bp:.1f}bp)", 1,
             "descriptive", "robustness")
    r5 = out[out.check == "R5"].iloc[0]
    log_test("R5", "H1", "dDGS10 split into dDFII10 + dT10YIE over the H1 window", "descriptive", None,
             f"dDGS10 {r5.d_y_bp:.1f}bp = real {r5.d_real_bp:.1f} + breakeven {r5.d_breakeven_bp:.1f} + residual {r5.residual_bp:.1f}",
             1, "different split (real vs inflation compensation), not substituted for TP split", "robustness")
    log_run("src/h1_attribution.py", {"start": START, "end": END_2026, "end_r4": END_R4, "min_abs_dy_bp": 25},
            {"verdict": verdict, "acm_share": h1.loc["ACM", "tp_share"], "kw_share": h1.loc["KW", "tp_share"],
             "r4_share": r4.tp_share, "r5_residual_bp": r5.residual_bp})
    print(out.to_string())
    print("H1 verdict:", verdict)
    return out


if __name__ == "__main__":
    main()
