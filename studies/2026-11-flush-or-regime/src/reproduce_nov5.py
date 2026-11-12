"""Reproduce SPEC_LITERAL ETF fixtures from numbers typed into the spec.

Name-level cross-section reproduction is BLOCKED until P1 writes raw closes
under data/raw/ (see RESULTS.md Source column). Quarantined fabricated
panels were removed from data/; the audit record lives under docs/ only.
"""

from __future__ import annotations

import numpy as np

from core.config_io import fixtures


def etf_returns_from_closes() -> dict[str, float]:
    """Arithmetic on SPEC_LITERAL close vectors in config/fixtures.yaml.

    P1 must re-verify each observable against ingested prices.parquet
    (src.gates.p1_spec_literal.run_p1_spec_literal_gate).
    """
    fx = fixtures()["verified_closes_2026_10_26_to_11_05"]
    out: dict[str, float] = {}
    for name in ("SPY", "QQQ", "SOXX", "SMH"):
        series = fx[name]
        out[name] = series[-1] / series[-2] - 1.0
    for name in ("SPY", "QQQ", "SOXX", "SMH"):
        series = fx[name]
        out[f"{name}_six_session"] = series[-1] / series[2] - 1.0
    soxx = fx["SOXX"]
    log_full = np.log(soxx[-1] / soxx[2])
    log_pre = np.log(soxx[-2] / soxx[2])
    out["soxx_log_decline_share_before_nov5"] = float(log_pre / log_full)
    return out


def print_report() -> None:
    rets = etf_returns_from_closes()
    print("=== ETF one-day returns (SPEC_LITERAL arithmetic on fixture closes) ===")
    for k in ("SPY", "QQQ", "SOXX", "SMH"):
        print(f"  {k}: {rets[k] * 100:+.2f}%")
    print(f"  SOXX six-session: {rets['SOXX_six_session'] * 100:+.2f}%")
    print(
        f"  SOXX log-decline share before 5 Nov: "
        f"{rets['soxx_log_decline_share_before_nov5']:.2%}"
    )
    print("=== Cross-section ===")
    print("  BLOCKED — no RAW_FILE name-level panel (D5/D7); see docs/reconstruction_audit.md")


def main() -> None:
    print_report()


if __name__ == "__main__":
    main()
