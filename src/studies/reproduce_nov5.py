"""Reproduce §1.1–1.3 fixtures from hard-coded closes and the N=23 panel.

Governing rule: if we cannot reproduce the published numbers, stop.
Do not retune figures to make gates pass.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from src.config_io import ROOT, fixtures

PANEL_PATH = ROOT / "data" / "processed" / "nov5_cross_section.csv"


def etf_returns_from_closes() -> dict[str, float]:
    fx = fixtures()["verified_closes_2026_10_26_to_11_05"]
    out: dict[str, float] = {}
    for name in ("SPY", "QQQ", "SOXX", "SMH"):
        series = fx[name]
        out[name] = series[-1] / series[-2] - 1.0
    # Six-session: 28 Oct (index 2) → 5 Nov (index 8)
    for name in ("SPY", "QQQ", "SOXX", "SMH"):
        series = fx[name]
        out[f"{name}_six_session"] = series[-1] / series[2] - 1.0
    # Share of log decline before 5 Nov (28 Oct → 4 Nov vs 28 Oct → 5 Nov)
    soxx = fx["SOXX"]
    log_full = np.log(soxx[-1] / soxx[2])
    log_pre = np.log(soxx[-2] / soxx[2])
    out["soxx_log_decline_share_before_nov5"] = float(log_pre / log_full)
    return out


def load_panel() -> pd.DataFrame:
    df = pd.read_csv(PANEL_PATH)
    assert len(df) == 23, f"expected N=23, got {len(df)}"
    return df


def layer_ew(df: pd.DataFrame, mask: pd.Series, col: str = "ret_nov5_pct") -> float:
    return float(df.loc[mask, col].mean())


def cross_section_stats(df: pd.DataFrame) -> dict[str, float]:
    builders = df["layer"] == "builders"
    suppliers = (df["ai_chain"] == 1) & ~builders
    ai = df["ai_chain"] == 1

    rho_ytd, p_ytd = stats.spearmanr(df["ret_nov5_pct"], df["ytd_to_4nov_pct"])
    rho_ytd_ai, p_ytd_ai = stats.spearmanr(
        df.loc[ai, "ret_nov5_pct"], df.loc[ai, "ytd_to_4nov_pct"]
    )
    rho_p5, p_p5 = stats.spearmanr(df["ret_nov5_pct"], df["ret_prior5_pct"])
    rho_p5_ai, p_p5_ai = stats.spearmanr(
        df.loc[ai, "ret_nov5_pct"], df.loc[ai, "ret_prior5_pct"]
    )

    return {
        "n": float(len(df)),
        "hyperscaler_ew_nov5_pct": layer_ew(df, builders),
        "supplier_ew_nov5_pct": layer_ew(df, suppliers),
        "spearman_nov5_vs_ytd": float(rho_ytd),
        "spearman_nov5_vs_ytd_p": float(p_ytd),
        "spearman_nov5_vs_ytd_ai_only": float(rho_ytd_ai),
        "spearman_nov5_vs_prior5": float(rho_p5),
        "spearman_nov5_vs_prior5_p": float(p_p5),
        "spearman_nov5_vs_prior5_ai_only": float(rho_p5_ai),
        "names_gt20pct_below_52w": float((df["dist_52w_high_pct"] < -20).sum()),
        "n_suppliers": float(suppliers.sum()),
        "n_builders": float(builders.sum()),
    }


def print_report() -> None:
    rets = etf_returns_from_closes()
    df = load_panel()
    xs = cross_section_stats(df)
    print("=== ETF one-day returns (from fixture closes) ===")
    for k in ("SPY", "QQQ", "SOXX", "SMH"):
        print(f"  {k}: {rets[k] * 100:+.2f}%")
    print(f"  SOXX six-session: {rets['SOXX_six_session'] * 100:+.2f}%")
    print(
        f"  SOXX log-decline share before 5 Nov: "
        f"{rets['soxx_log_decline_share_before_nov5']:.2%}"
    )
    print("=== Cross-section ===")
    for k, v in xs.items():
        print(f"  {k}: {v}")


def main() -> None:
    print_report()


if __name__ == "__main__":
    main()
