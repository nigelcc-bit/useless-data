"""Exhibits E1-E10: one PNG per chart plus the CSV behind it, in out/exhibits/.

Reads the out/*.csv results written by the H-scripts and the raw data through src/load.py.
Plotting only; no new tests.

    python -m src.exhibits
"""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src import load  # noqa: E402
from src.common import BP, END_2026, OUT, log_run  # noqa: E402

EX = OUT / "exhibits"
SURFACE, INK, INK2, GRID, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#b4b2aa"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"  # categorical slots 1-4, fixed order
SRC_ACM = "NY Fed ACM term structure model (ACMTermPremium.xls)"
SRC_FRED = "FRED (H.15 DGS*, Kim-Wright THREEFY*, DFII10, T10YIE, DFEDTARU)"
PULLED = "Data pulled 19 Nov 2026."
START_H1 = pd.Timestamp("2025-12-31")


def fig_ax(w=9.5, h=4.8, ncols=1, sharey=False):
    fig, axes = plt.subplots(1, ncols, figsize=(w, h), dpi=200, facecolor=SURFACE, sharey=sharey)
    for ax in np.atleast_1d(axes):
        ax.set_facecolor(SURFACE)
        ax.grid(axis="y", color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color("#c9c8c2")
        ax.tick_params(colors=INK2, labelsize=8)
    return fig, axes


def finish(fig, name: str, title: str, foot: str, data: pd.DataFrame) -> str:
    fig.suptitle(title, color=INK, fontsize=11, x=0.01, ha="left", y=0.99)
    fig.text(0.01, 0.005, foot, color=INK2, fontsize=7, ha="left", va="bottom", wrap=True)
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    fig.savefig(EX / f"{name}.png", facecolor=SURFACE)
    plt.close(fig)
    data.to_csv(EX / f"{name}.csv", float_format="%.6g")
    return name


def label_end(ax, x, y, text, color=INK, dy=0.0):
    ax.annotate(text, (x, y), xytext=(4, dy), textcoords="offset points", color=color, fontsize=7.5,
                va="center", ha="left")


def spread_end_labels(ax, items, frac=0.045):
    """items: (x, y, text, color). Push labels apart vertically so none overlap."""
    lo, hi = ax.get_ylim()
    gap = (hi - lo) * frac
    items = sorted(items, key=lambda t: t[1])
    placed = []
    for x, y, text, color in items:
        yy = y if not placed else max(y, placed[-1] + gap)
        placed.append(yy)
        ax.annotate(text, (x, y), xytext=(x, yy), textcoords="data", color=color, fontsize=7.5,
                    va="center", ha="left")
    return placed


def e1(a, kw):
    d = pd.DataFrame({"ACMY10": a["ACMY10"], "ACMRNY10": a["ACMRNY10"], "ACMTP10": a["ACMTP10"],
                      "KWTP10": kw["KWTP10"]}).dropna(how="all")
    fig, ax = fig_ax(10, 5)
    ax.plot(d.index, d.ACMY10, color=INK, lw=1.0, label="10y fitted yield (ACM)")
    ax.plot(d.index, d.ACMRNY10, color=BLUE, lw=1.0, label="Risk-neutral yield (ACM)")
    ax.plot(d.index, d.ACMTP10, color=ORANGE, lw=1.0, label="Term premium (ACM)")
    ax.plot(d.index, d.KWTP10, color=AQUA, lw=0.9, label="Term premium (Kim-Wright)")
    ax.axhline(0, color=INK2, lw=0.7)
    ax.set_ylabel("Percent", color=INK, fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    return finish(fig, "E1_acm_10y_decomposition", "E1. 10-year zero yield = risk-neutral yield + term premium, 1990-2026",
                  f"Daily. ACM to 2026-11-17, Kim-Wright to 2026-11-13. Source: {SRC_ACM}; {SRC_FRED}. {PULLED}", d)


def e2(h1):
    t = h1[h1.check == "H1"].set_index("model")[["d_y_bp", "d_rny_bp", "d_tp_bp", "tp_share"]]
    fig, ax = fig_ax(8, 4.8)
    comps = [("d_y_bp", "Change in 10y yield", MUTED), ("d_rny_bp", "Risk-neutral (expected path)", BLUE),
             ("d_tp_bp", "Term premium", ORANGE)]
    x = np.arange(len(t))
    wdt = 0.26
    for i, (c, lab, col) in enumerate(comps):
        bars = ax.bar(x + (i - 1) * wdt, t[c], wdt - 0.02, color=col, label=lab)
        for b, v in zip(bars, t[c]):
            ax.annotate(f"{v:+.0f}", (b.get_x() + b.get_width() / 2, v), xytext=(0, 3 if v >= 0 else -10),
                        textcoords="offset points", ha="center", fontsize=8, color=INK)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xticks(x, [f"{m}\nTP share {s:.2f}" for m, s in zip(t.index, t.tp_share)])
    ax.set_ylabel("Change, basis points", color=INK, fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    return finish(fig, "E2_h1_attribution_2026ytd", "E2. 10-year zero yield change, 31 Dec 2025 to 13 Nov 2026: path vs term premium (H1)",
                  f"Kim-Wright risk-neutral = THREEFY10 - THREEFYTP10. Source: {SRC_ACM}; {SRC_FRED}. {PULLED}", t)


def e3(paths):
    p = paths[paths.model == "ACM"]
    fig, axes = fig_ax(11, 4.8, ncols=2, sharey=True)
    for ax, col, lab in [(axes[0], "cum_d_tp_bp", "Term premium (ACM TP10)"),
                         (axes[1], "cum_d_rny_bp", "Risk-neutral yield (ACM RNY10)")]:
        items = []
        for ep, g in p.groupby("episode"):
            is26 = ep.startswith("2026")
            ax.plot(g.rel_day, g[col], color=BLUE if is26 else MUTED, lw=2.0 if is26 else 1.0, zorder=3 if is26 else 2)
            items.append((g.rel_day.iloc[-1], g[col].iloc[-1], ep[:4], INK if is26 else INK2))
        ax.set_xlim(-130, 60)
        spread_end_labels(ax, [(x + 3, y, t, c) for x, y, t, c in items])
        ax.axvline(0, color=INK2, lw=0.8, ls="--")
        ax.axhline(0, color=INK2, lw=0.7)
        ax.set_title(lab, color=INK, fontsize=9.5, loc="left")
        ax.set_xlabel("Trading days relative to first hike (t0)", color=INK, fontsize=9)
    axes[0].set_ylabel("Cumulative change from t0-126, bp", color=INK, fontsize=9)
    return finish(fig, "E3_hike_windows_paths", "E3. First-hike windows: term premium and risk-neutral paths, seven episodes, 2026 in blue (H2, prior only)",
                  f"ACM. Window t0-126 to t0+41 trading days; 2026 ends 2026-11-13 (t0+40). N = 6 prior episodes < 8: prior only. "
                  f"Source: {SRC_ACM}. {PULLED}", p.set_index(["episode", "rel_day"]))


def e4(h3):
    t = h3[h3.long == "DGS10"].set_index("year")
    base = t.loc[:2025, "r2"]
    p10 = float(np.percentile(base, 10))
    fig, ax = fig_ax(10, 4.6)
    cols = [BLUE if y == 2026 else MUTED for y in t.index]
    ax.bar(t.index, t.r2, color=cols, width=0.8)
    ax.axhline(p10, color=INK, lw=1.0, ls="--")
    ax.annotate(f"10th percentile of 1990-2025 = {p10:.2f}", (1990, p10), xytext=(0, 4), textcoords="offset points",
                fontsize=8, color=INK)
    ax.annotate(f"2026: {t.loc[2026, 'r2']:.2f}", (2026, t.loc[2026, "r2"]), xytext=(0, 3), textcoords="offset points",
                ha="center", fontsize=8, color=INK)
    ax.set_ylabel("R-squared", color=INK, fontsize=9)
    ax.set_xlabel("Calendar year (2026 = 1 Jan to 13 Nov)", color=INK, fontsize=9)
    ax.set_ylim(0, 1)
    out = t[["n", "beta", "r2"]].assign(pct10_1990_2025=p10)
    return finish(fig, "E4_h3_yearly_r2", "E4. How much of the daily 10-year move the 2-year explains: R-squared by year (H3)",
                  f"OLS of daily change in DGS10 on daily change in DGS2, by calendar year. Source: {SRC_FRED}. {PULLED}", out)


def e5(rb):
    fig, ax = fig_ax(10, 4.6)
    ax.plot(rb.index, rb.beta_52w, color=BLUE, lw=1.0)
    ax.axvspan(pd.Timestamp("2026-01-01"), rb.index.max(), color="#cde2fb", lw=0)
    ax.annotate("2026", (pd.Timestamp("2026-01-15"), ax.get_ylim()[1]), xytext=(0, -10), textcoords="offset points",
                fontsize=8, color=INK)
    ax.axhline(0, color=INK2, lw=0.7)
    ax.set_ylabel("bp of ACM TP10 per unit change in ln WTI", color=INK, fontsize=9)
    return finish(fig, "E5_h4_rolling_oil_beta", "E5. Rolling 52-week oil beta of the ACM 10-year term premium (H4, descriptive)",
                  f"Weekly (last business day of each Mon-Fri week). Slope of weekly change in ACMTP10 on weekly change in ln(DCOILWTICO), "
                  f"trailing 52 weekly observations. Not a test. Source: {SRC_ACM}; FRED DCOILWTICO. {PULLED}", rb)


def e6(days, fit):
    d = days.copy()
    d["date"] = pd.to_datetime(d["date"])
    base = d[d.date.dt.year <= 2025]
    y26 = d[d.date.dt.year == 2026]
    fig, ax = fig_ax(8.5, 5.6)
    ax.scatter(base.d_dgs2, base.d_acm_tp10, s=14, color=MUTED, edgecolor=SURFACE, lw=0.5, label="1994-2025")
    ax.scatter(y26.d_dgs2, y26.d_acm_tp10, s=36, color=BLUE, edgecolor=SURFACE, lw=1.5, label="2026", zorder=3)
    done = []
    for _, r in y26.sort_values("d_acm_tp10", ascending=False).iterrows():
        near = any(abs(r.d_dgs2 - x) < 1.5 and abs(r.d_acm_tp10 - y) < 3 for x, y in done)
        ax.annotate(r.date.strftime("%d %b"), (r.d_dgs2, r.d_acm_tp10), xytext=(5, -11 if near else 3),
                    textcoords="offset points", fontsize=7.5, color=INK)
        done.append((r.d_dgs2, r.d_acm_tp10))
    xs = np.linspace(base.d_dgs2.min(), base.d_dgs2.max(), 50)
    h = fit["H5a"]
    ax.plot(xs, h["alpha"] + h["beta"] * xs, color=INK, lw=1.2,
            label=f"H5a fit, 1994-2025: slope {h['beta']:.3f}, t {h['t']:.2f}, n {h['n']}")
    ax.axhline(0, color=INK2, lw=0.6)
    ax.axvline(0, color=INK2, lw=0.6)
    ax.set_xlabel("Change in 2-year yield (DGS2), bp", color=INK, fontsize=9)
    ax.set_ylabel("Change in ACM 10y term premium, bp", color=INK, fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    return finish(fig, "E6_h5_fomc_days", "E6. FOMC announcement days: term premium response to 2-year moves (H5a)",
                  f"Scheduled announcement days, one-day changes from each series' previous published date. "
                  f"Source: {SRC_ACM}; {SRC_FRED}; federalreserve.gov FOMC calendars. {PULLED}",
                  d.set_index("date")[["d_dgs2", "d_dgs10", "d_acm_tp10", "d_acm_rny10", "d1_share_acm", "sample"]])


def e7(f):
    d = f.loc[START_H1:END_2026, ["DGS10", "DFII10", "T10YIE"]].dropna()
    c = (d - d.iloc[0]) * BP
    fig, ax = fig_ax(9.5, 4.8)
    items = []
    for col, lab, color, short in [("DGS10", "10y nominal (DGS10)", INK, "nominal"),
                                   ("DFII10", "10y real (DFII10)", BLUE, "real"),
                                   ("T10YIE", "10y breakeven (T10YIE)", ORANGE, "breakeven")]:
        ax.plot(c.index, c[col], color=color, lw=1.4, label=lab)
        items.append((c.index[-1] + pd.Timedelta(days=3), c[col].iloc[-1], f"{short} {c[col].iloc[-1]:+.0f}bp", INK))
    ax.set_xlim(right=c.index[-1] + pd.Timedelta(days=45))
    spread_end_labels(ax, items)
    ax.axhline(0, color=INK2, lw=0.7)
    ax.set_ylabel("Change since 31 Dec 2025, bp", color=INK, fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    return finish(fig, "E7_r5_real_vs_breakeven", "E7. 2026 YTD: 10-year nominal change split into real yield and breakeven (R5)",
                  f"T10YIE = DGS10 - DFII10 in FRED, so the split has no residual. A real/inflation split, not a term-premium split. "
                  f"Source: {SRC_FRED}. {PULLED}", c)


def e8(f):
    d = f.loc["2026-01-01":, ["DGS2", "DGS10", "DGS30", "DFEDTARU"]]
    fomc = load.fomc_announcement_days("2026-01-01")
    fomc = fomc[fomc <= d.index.max()]
    fig, ax = fig_ax(10, 5)
    for col, lab, color in [("DGS2", "2-year", BLUE), ("DGS10", "10-year", ORANGE), ("DGS30", "30-year", AQUA)]:
        s = d[col].dropna()
        ax.plot(s.index, s, color=color, lw=1.4, label=lab)
        label_end(ax, s.index[-1], s.iloc[-1], f"{lab} {s.iloc[-1]:.2f}", color=INK)
    s = d["DFEDTARU"].dropna()
    ax.step(s.index, s, where="post", color=YELLOW, lw=1.6, label="Fed funds target, upper bound")
    label_end(ax, s.index[-1], s.iloc[-1], f"Target upper {s.iloc[-1]:.2f}", color=INK)
    for x in fomc:
        ax.axvline(x, color=INK2, lw=0.6, ls=":")
    ax.set_ylabel("Percent", color=INK, fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.set_xlim(right=d.index.max() + pd.Timedelta(days=40))
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    out = d.assign(fomc_day=d.index.isin(fomc))
    return finish(fig, "E8_2026_timeline", "E8. 2026: Treasury yields and the policy rate, with FOMC announcement days",
                  f"Daily, to 2026-11-19. Dotted vertical lines: scheduled FOMC announcement days. Source: {SRC_FRED}; federalreserve.gov FOMC calendars. {PULLED}", out)


def e9(a, kw):
    d = pd.DataFrame({"ACMTP10": a["ACMTP10"], "KWTP10": kw["KWTP10"]}).dropna()
    d["gap"] = d.ACMTP10 - d.KWTP10
    fig, ax = fig_ax(10, 4.6)
    ax.plot(d.index, d.gap, color=BLUE, lw=0.8)
    ax.axhline(0, color=INK2, lw=0.7)
    last = d.index[-1]
    label_end(ax, last, d.gap.iloc[-1], f"{last.date()}: {d.gap.iloc[-1]:+.2f}", color=INK)
    ax.set_ylabel("ACM TP10 minus Kim-Wright TP10, percentage points", color=INK, fontsize=9)
    return finish(fig, "E9_model_disagreement", "E9. Model disagreement: ACM minus Kim-Wright 10-year term premium",
                  f"Daily, common dates 1990-01-02 to 2026-11-13. Source: {SRC_ACM}; {SRC_FRED}. {PULLED}", d)


def e10(a, kw):
    rows, data = [], {}
    fig, axes = fig_ax(10, 4.6, ncols=2, sharey=False)
    for ax, (name, s, color) in zip(axes, [("ACM TP10", a["ACMTP10"].dropna(), BLUE),
                                           ("Kim-Wright TP10", kw["KWTP10"].dropna(), ORANGE)]):
        cur, cur_d = float(s.iloc[-1]), s.index[-1]
        pct = float((s <= cur).mean() * 100)
        ax.hist(s, bins=60, color=color, edgecolor=SURFACE, linewidth=0.4)
        ax.axvline(cur, color=INK, lw=1.2)
        ax.annotate(f"{cur_d.date()}: {cur:.2f}\n{pct:.0f}th percentile", (cur, ax.get_ylim()[1]), xytext=(4, -22),
                    textcoords="offset points", fontsize=8, color=INK)
        ax.set_title(f"{name}, daily 1990-{cur_d.year}", color=INK, fontsize=9.5, loc="left")
        ax.set_xlabel("Term premium, percent", color=INK, fontsize=9)
        rows.append({"model": name, "date": cur_d.date(), "current": cur, "percentile": pct, "n_days": len(s),
                     "min": s.min(), "median": s.median(), "max": s.max()})
    axes[0].set_ylabel("Number of days", color=INK, fontsize=9)
    out = pd.DataFrame(rows).set_index("model")
    return finish(fig, "E10_tp_percentile", "E10. Where the current 10-year term premium sits in its 1990-2026 distribution",
                  f"Percentile = share of days at or below the latest value. Source: {SRC_ACM}; {SRC_FRED}. {PULLED}", out)


def main() -> list[str]:
    EX.mkdir(parents=True, exist_ok=True)
    a, kw, f = load.acm(), load.kim_wright(), load.fred()
    h1 = pd.read_csv(OUT / "h1_attribution.csv")
    paths = pd.read_csv(OUT / "h2_paths.csv")
    h3 = pd.read_csv(OUT / "h3_yearly_r2.csv")
    rb = pd.read_csv(OUT / "h4_rolling_beta.csv", parse_dates=["week_end"], index_col="week_end")
    days = pd.read_csv(OUT / "h5_fomc_days.csv")
    fit = json.loads((OUT / "h5a_fit.json").read_text())
    made = [e1(a, kw), e2(h1), e3(paths), e4(h3), e5(rb), e6(days, fit), e7(f), e8(f), e9(a, kw), e10(a, kw)]
    log_run("src/exhibits.py", {"out": "out/exhibits"}, {"exhibits": made})
    print("\n".join(made))
    return made


if __name__ == "__main__":
    main()
