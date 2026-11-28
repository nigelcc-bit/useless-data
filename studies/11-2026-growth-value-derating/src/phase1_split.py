"""Phase 1: split the Growth forward P/E drop (peak to 2026-11-27) into PRICE, EPS, COMPOSITION and RESIDUAL legs.
Identity dln(PE) = dln(Price) - dln(EPS). Value is the control. Rules frozen in PREREG.md."""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import END, OUT, PEAK_FROM, PEAK_TO, RECON, weekly_panel


def find_peak(pe: pd.Series) -> pd.Timestamp:
    s = pe.loc[PEAK_FROM:PEAK_TO]
    return s.idxmax()  # earliest on ties


def second_local_peak(pe: pd.Series, k: int = 4) -> pd.Timestamp:
    s = pe.loc[PEAK_FROM:PEAK_TO]
    peaks = [t for i, t in enumerate(s.index) if s.iloc[i] == s.iloc[max(0, i - k): i + k + 1].max()]
    ranked = sorted(peaks, key=lambda t: (-s[t], t))
    # collapse plateaus: drop local peaks within k weeks of a higher-ranked one
    keep = []
    for t in ranked:
        if all(abs((t - u).days) > 7 * k for u in keep):
            keep.append(t)
    return keep[1]


def legs(w: pd.DataFrame, side: str, eps_col: str, peak, end, recon) -> dict:
    x = w.loc[peak:end]
    lpe, lpx, leps = np.log(x[f"pe_{side}"]), np.log(x[f"px_{side}"]), np.log(x[eps_col])
    d_pe, d_px, d_eps = lpe.diff().iloc[1:], lpx.diff().iloc[1:], leps.diff().iloc[1:]
    in_w = (d_pe.index >= recon[0]) & (d_pe.index <= recon[1])
    D = float(lpe.iloc[-1] - lpe.iloc[0])
    price_lp = float(d_px[~in_w].sum())
    eps_lp = float(-d_eps[~in_w].sum())
    comp_lp = float(d_pe[in_w].sum() - d_px[in_w].sum())
    resid_lp = D - price_lp - eps_lp - comp_lp
    return dict(total_lp=D, price_lp=price_lp, eps_lp=eps_lp, comp_lp=comp_lp, resid_lp=resid_lp,
                price_share=price_lp / D, eps_share=eps_lp / D, comp_share=comp_lp / D, resid_share=resid_lp / D,
                recon_weeks_in_window=int(in_w.sum()), weeks=int(len(d_pe)),
                pe_start=float(x[f"pe_{side}"].iloc[0]), pe_end=float(x[f"pe_{side}"].iloc[-1]))


def classify(L: dict) -> tuple[str, bool]:
    e, p = L["eps_share"] > 0.60, L["price_share"] > 0.50
    cls = "mixed" if (e and p) else ("earnings-driven" if e else ("price-driven" if p else "mixed"))
    return cls, bool(L["comp_share"] > 0.30)


def branches(cls: str) -> list[str]:
    return {"earnings-driven": ["2A"], "price-driven": ["2B"], "mixed": ["2A", "2B"]}[cls]


def run(ledger) -> dict:
    w = weekly_panel()
    peak = find_peak(w.pe_g)
    peak2 = second_local_peak(w.pe_g)
    shift = pd.Timedelta(weeks=1)
    variants = {
        "primary (EPS b)": dict(eps="b", peak=peak, recon=RECON),
        "EPS method (a)": dict(eps="a", peak=peak, recon=RECON),
        "recon window +1 week": dict(eps="b", peak=peak, recon=(RECON[0] + shift, RECON[1] + shift)),
        "recon window -1 week": dict(eps="b", peak=peak, recon=(RECON[0] - shift, RECON[1] - shift)),
        "start at 2nd-highest local peak": dict(eps="b", peak=peak2, recon=RECON),
    }
    rows, res = [], {"peak": str(peak.date()), "peak_pe": float(w.pe_g[peak]), "second_peak": str(peak2.date()),
                     "second_peak_pe": float(w.pe_g[peak2]), "end": str(END.date()), "eps_a_last_week": w.attrs["eps_a_last_week"],
                     "variants": {}}
    for name, v in variants.items():
        out = {}
        for side in ("g", "v"):
            L = legs(w, side, f"eps_{v['eps']}_{side}", v["peak"], END, v["recon"])
            out[side] = L
            for leg in ("price", "eps", "comp", "resid"):
                rows.append(dict(variant=name, index="Growth" if side == "g" else "Value", leg=leg.upper() if leg != "comp" else "COMPOSITION",
                                 log_points=L[f"{leg}_lp"], share_of_drop=L[f"{leg}_share"], total_log_change=L["total_lp"],
                                 peak=str(v["peak"].date()), recon_window=f"{v['recon'][0].date()}..{v['recon'][1].date()}"))
        cls, art = classify(out["g"])
        diff = {k: out["g"][f"{k}_lp"] - out["v"][f"{k}_lp"] for k in ("total", "price", "eps", "comp", "resid")}
        res["variants"][name] = dict(growth=out["g"], value=out["v"], classification=cls, artefact_material=art, g_minus_v_lp=diff)
        g = out["g"]
        ledger.trial("1", "Growth legs", name, "PRICE / EPS / COMP / RESID share of log P/E drop", g["weeks"],
                     f"{g['price_share']:.1%} / {g['eps_share']:.1%} / {g['comp_share']:.1%} / {g['resid_share']:.1%} -> {cls}{', artefact material' if art else ''}")
        vv = out["v"]
        ledger.trial("1", "Value legs (control)", name, "PRICE / EPS / COMP / RESID share of log P/E change", vv["weeks"],
                     f"{vv['price_share']:.1%} / {vv['eps_share']:.1%} / {vv['comp_share']:.1%} / {vv['resid_share']:.1%}")
        ledger.trial("1", "Growth minus Value, log points", name, "total / price / eps / comp / resid", g["weeks"],
                     " / ".join(f"{diff[k]:+.3f}" for k in ("total", "price", "eps", "comp", "resid")))
    prim = res["variants"]["primary (EPS b)"]
    flips = {n: (r["classification"] != prim["classification"] or r["artefact_material"] != prim["artefact_material"])
             for n, r in res["variants"].items() if n != "primary (EPS b)"}
    res["classification"], res["artefact_material"] = prim["classification"], prim["artefact_material"]
    res["branches"] = branches(prim["classification"])
    res["flips"] = flips
    ledger.test("P1", "P1", "Phase 1 classification of the Growth P/E drop", prim["classification"], n=prim["growth"]["weeks"],
                effect=f"EPS {prim['growth']['eps_share']:.1%}, PRICE {prim['growth']['price_share']:.1%}",
                notes="flips under: " + (", ".join(k for k, f in flips.items() if f) or "none"))
    ledger.test("E", "E", "Composition (Dec 2025 reconstitution) > 30% of the drop", "CONFIRMED" if prim["artefact_material"] else "KILLED",
                n=prim["growth"]["recon_weeks_in_window"], effect=f"COMPOSITION {prim['growth']['comp_share']:.1%}")

    pd.DataFrame(rows).to_csv(OUT / "phase1_legs.csv", index=False, float_format="%.6f")
    (OUT / "phase1_results.json").write_text(json.dumps(res, indent=1, default=float))
    chart(res)
    return res


def chart(res):
    v = res["variants"]["primary (EPS b)"]
    cols = {"PRICE": "#257de0", "EPS": "#f47230", "COMPOSITION": "#00b894", "RESIDUAL": "#8a8a8a"}
    keys = {"PRICE": "price_lp", "EPS": "eps_lp", "COMPOSITION": "comp_lp", "RESIDUAL": "resid_lp"}
    fig, ax = plt.subplots(figsize=(8.5, 5.4), dpi=200)
    for i, (lab, side) in enumerate((("Growth", "growth"), ("Value", "value"))):
        L = v[side]
        pos, neg = 0.0, 0.0
        for leg, c in cols.items():
            val = L[keys[leg]] * 100
            if abs(val) < 1e-9:
                continue
            base = pos if val >= 0 else neg
            ax.bar(i, val, bottom=base, color=c, width=0.55, edgecolor="white", linewidth=2, label=leg if i == 0 else None)
            if abs(val) >= 5:
                ax.text(i, base + val / 2, f"{leg}\n{val:+.0f}", ha="center", va="center", fontsize=8, color="white")
            if val >= 0:
                pos += val
            else:
                neg += val
        ax.plot([i - 0.32, i + 0.32], [L["total_lp"] * 100] * 2, color="#191919", lw=2)
        ax.text(i + 0.34, L["total_lp"] * 100, f"total {L['total_lp'] * 100:+.0f}", va="center", fontsize=8, color="#191919")
    ax.axhline(0, color="#666666", lw=0.8)
    ax.set_xticks([0, 1], ["S&P 500 Growth", "S&P 500 Value"])
    ax.set_ylabel("Log points (x100), peak week to 27 Nov 2026", color="#666666")
    g = v["growth"]
    lead = max(("PRICE", g["price_share"]), ("EPS", g["eps_share"]), ("COMPOSITION", g["comp_share"]), key=lambda t: t[1])
    names = {"PRICE": "price", "EPS": "rising forward earnings", "COMPOSITION": "index composition"}
    ax.set_title(f"Growth P/E fell {abs(g['total_lp']) * 100:.0f} log points from its {res['peak']} peak, "
                 f"{lead[1]:.0%} of it from {names[lead[0]]}\n"
                 f"Composition {g['comp_share']:.0%}, price {g['price_share']:+.0%}, residual {g['resid_share']:+.0%}. "
                 f"Negative legs pushed P/E down (EPS method b)", loc="left", fontsize=9.5, color="#191919")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e6e6e6", lw=0.6)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "phase1_legs.png")
    plt.close(fig)
