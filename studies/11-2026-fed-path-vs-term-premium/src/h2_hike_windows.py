"""H2 (PRIOR ONLY, N = 6 < 8): term-premium share of dy10 in each first-hike window.

Window: t0 - 126 to t0 + 41 trading days on each model's own calendar; the 2026 window
ends at or before 2026-11-13. Share follows D2 (not reported if |dy10| < 25bp).

    python -m src.h2_hike_windows
"""
from __future__ import annotations

import pandas as pd

from src import load
from src.common import BP, END_2026, OUT, log_run, log_test, share, window

BEFORE, AFTER = 126, 41


def model_frames() -> dict[str, pd.DataFrame]:
    a, kw = load.acm(), load.kim_wright()
    return {
        "ACM": pd.DataFrame({"y": a["ACMY10"], "rny": a["ACMRNY10"], "tp": a["ACMTP10"]}).dropna(),
        "KW": pd.DataFrame({"y": kw["KWY10"], "rny": kw["KWRNY10"], "tp": kw["KWTP10"]}).dropna(),
    }


def main() -> tuple[pd.DataFrame, pd.DataFrame]:
    hikes = load.first_hikes()
    rows, paths, issues = [], [], []
    for model, df in model_frames().items():
        for t0 in hikes:
            cap = END_2026 if t0.year == 2026 else None
            w = window(df.index, t0, BEFORE, AFTER, cap=cap)
            if w["truncated"]:
                issues.append(f"{model} {t0.date()}: window truncated to t0+{w['end_offset']} ({w['end'].date()})")
            s, e = df.loc[w["start"]], df.loc[w["end"]]
            dy, drny, dtp = (e.y - s.y) * BP, (e.rny - s.rny) * BP, (e.tp - s.tp) * BP
            rows.append({"episode": str(t0.date()), "model": model, "start": w["start"].date(),
                         "t0": t0.date(), "end": w["end"].date(), "end_offset": w["end_offset"],
                         "truncated": w["truncated"], "y_start": s.y, "tp_start": s.tp,
                         "d_y_bp": dy, "d_rny_bp": drny, "d_tp_bp": dtp, "tp_share": share(dtp, dy)})
            seg = df.loc[w["start"]:w["end"]]
            rel = range(-BEFORE, -BEFORE + len(seg))
            paths.append(pd.DataFrame({"episode": str(t0.date()), "model": model, "rel_day": list(rel),
                                       "date": seg.index.date, "cum_d_tp_bp": ((seg.tp - s.tp) * BP).values,
                                       "cum_d_rny_bp": ((seg.rny - s.rny) * BP).values,
                                       "cum_d_y_bp": ((seg.y - s.y) * BP).values}))
    out = pd.DataFrame(rows)
    out["label"] = "PRIOR ONLY (N = 6 < 8)"
    out.to_csv(OUT / "h2_hike_windows.csv", index=False, float_format="%.6g")
    pd.concat(paths).to_csv(OUT / "h2_paths.csv", index=False, float_format="%.6g")

    comp = {}
    for model in ["ACM", "KW"]:
        m = out[out.model == model].set_index("episode")
        s26 = m.loc["2026-09-16", "tp_share"]
        prior = m.drop("2026-09-16")["tp_share"]
        comp[model] = {"share_2026": s26, "n_prior_reported": int(prior.notna().sum()),
                       "n_prior_below_2026": int((prior < s26).sum()) if pd.notna(s26) else None}
    effect = "; ".join(f"{k}: 2026 share {v['share_2026']:.3f}, above {v['n_prior_below_2026']} of "
                       f"{v['n_prior_reported']} reported prior shares" if pd.notna(v["share_2026"])
                       else f"{k}: 2026 share not reported (|dy| < 25bp)" for k, v in comp.items())
    log_test("H2", "H2", "TP share of dy10 in 2026 hike window vs six prior windows, ACM and KW",
             "prior only (N = 6 < 8), not tested", None, effect, 6, "; ".join(issues) or "no truncation",
             "prior")
    log_run("src/h2_hike_windows.py", {"before": BEFORE, "after": AFTER, "cap_2026": END_2026,
                                        "episodes": [str(h.date()) for h in hikes]},
            {"comparison": comp, "issues": issues})
    print("PRIOR ONLY (N = 6 < 8)")
    print(out.drop(columns="label").to_string())
    for i in issues:
        print("LOG:", i)
    return out, pd.concat(paths)


if __name__ == "__main__":
    main()
