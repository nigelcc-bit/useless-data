"""P1 gate: every SPEC_LITERAL fixture must reproduce from ingested prices.

If any row fails its tolerance, P1 fails. Arithmetic recompute from
config/fixtures.yaml alone is not enough after P1 — prices.parquet is required.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from core.config_io import ROOT, fixtures

PRICES_PATH = ROOT / "data" / "processed" / "prices.parquet"


@dataclass(frozen=True)
class SpecLiteralCheck:
    name: str
    target: float
    tol: float
    how: str  # human-readable derivation


# Registry mirrored by RESULTS.md Source=SPEC_LITERAL rows.
SPEC_LITERAL_CHECKS: tuple[SpecLiteralCheck, ...] = (
    SpecLiteralCheck("SOXX_5_Nov", -0.121, 0.003, "SOXX[-1]/SOXX[-2]-1 from fixture close vector"),
    SpecLiteralCheck("SPY_5_Nov", -0.044, 0.002, "SPY[-1]/SPY[-2]-1"),
    SpecLiteralCheck("QQQ_5_Nov", -0.065, 0.002, "QQQ[-1]/QQQ[-2]-1"),
    SpecLiteralCheck("SMH_5_Nov", -0.112, 0.002, "SMH[-1]/SMH[-2]-1"),
    SpecLiteralCheck(
        "SOXX_six_session",
        -0.242,
        0.003,
        "SOXX[5 Nov]/SOXX[28 Oct]-1",
    ),
    SpecLiteralCheck(
        "SOXX_log_decline_share_before_nov5",
        0.53,
        0.02,
        "log(SOXX[4 Nov]/SOXX[28 Oct]) / log(SOXX[5 Nov]/SOXX[28 Oct])",
    ),
)


def prices_available(path: Path = PRICES_PATH) -> bool:
    return path.is_file()


def _close_on(px: pd.DataFrame, ticker: str, date: str) -> float:
    if ticker not in px.columns:
        raise KeyError(f"{ticker} missing from prices.parquet")
    ts = pd.Timestamp(date)
    if ts not in px.index:
        raise KeyError(f"{date} missing from prices.parquet index")
    val = px.loc[ts, ticker]
    if pd.isna(val):
        raise ValueError(f"{ticker} NaN on {date}")
    return float(val)


def observed_from_prices(px: pd.DataFrame) -> dict[str, float]:
    """Compute SPEC_LITERAL observables from ingested daily closes."""
    soxx_1105 = _close_on(px, "SOXX", "2026-11-05")
    soxx_1104 = _close_on(px, "SOXX", "2026-11-04")
    soxx_1028 = _close_on(px, "SOXX", "2026-10-28")
    spy_1105 = _close_on(px, "SPY", "2026-11-05")
    spy_1104 = _close_on(px, "SPY", "2026-11-04")
    qqq_1105 = _close_on(px, "QQQ", "2026-11-05")
    qqq_1104 = _close_on(px, "QQQ", "2026-11-04")
    smh_1105 = _close_on(px, "SMH", "2026-11-05")
    smh_1104 = _close_on(px, "SMH", "2026-11-04")
    log_full = np.log(soxx_1105 / soxx_1028)
    log_pre = np.log(soxx_1104 / soxx_1028)
    return {
        "SOXX_5_Nov": soxx_1105 / soxx_1104 - 1.0,
        "SPY_5_Nov": spy_1105 / spy_1104 - 1.0,
        "QQQ_5_Nov": qqq_1105 / qqq_1104 - 1.0,
        "SMH_5_Nov": smh_1105 / smh_1104 - 1.0,
        "SOXX_six_session": soxx_1105 / soxx_1028 - 1.0,
        "SOXX_log_decline_share_before_nov5": float(log_pre / log_full),
    }


def run_p1_spec_literal_gate(path: Path = PRICES_PATH) -> pd.DataFrame:
    """Return a report; raise AssertionError if any check fails."""
    if not prices_available(path):
        raise FileNotFoundError(
            f"P1 gate requires {path}. Run local ingest before claiming P1 complete."
        )
    px = pd.read_parquet(path)
    obs = observed_from_prices(px)
    rows = []
    failures = []
    for chk in SPEC_LITERAL_CHECKS:
        got = obs[chk.name]
        ok = abs(got - chk.target) < chk.tol
        rows.append(
            {
                "name": chk.name,
                "target": chk.target,
                "observed": got,
                "tol": chk.tol,
                "pass": ok,
                "source": "SPEC_LITERAL",
                "how": chk.how,
            }
        )
        if not ok:
            failures.append(f"{chk.name}: observed={got:.6f} target={chk.target} tol={chk.tol}")
    report = pd.DataFrame(rows)
    if failures:
        raise AssertionError("P1 SPEC_LITERAL gate failed:\n" + "\n".join(failures))
    # Cross-check config fixtures still match registry targets (no silent retarget)
    fx = fixtures()
    assert abs(fx["gates"]["soxx_nov5_ret"] - (-0.121)) < 1e-12
    assert abs(fx["gates"]["spy_nov5_ret"] - (-0.044)) < 1e-12
    return report


def main() -> None:
    report = run_p1_spec_literal_gate()
    print(report.to_string(index=False))
    print("P1 SPEC_LITERAL gate: PASS")


if __name__ == "__main__":
    main()
