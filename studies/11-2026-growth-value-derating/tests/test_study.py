"""Study 5 gates: fixtures, the log identity, no look-ahead (RESEARCH_PROTOCOL rule 3), and the frozen classification rule."""
import numpy as np
import pandas as pd
import pytest

from common import RECON, check_fixtures, weekly_panel
from phase1_split import classify, find_peak, legs


def test_fixtures_reproduce():
    check_fixtures()  # raises SystemExit if any hash or documented value does not reproduce


def test_identity_holds_weekly_for_method_b():
    w = weekly_panel()
    for s in ("g", "v"):
        lhs = np.log(w[f"pe_{s}"]).diff()
        rhs = np.log(w[f"px_{s}"]).diff() - np.log(w[f"eps_b_{s}"]).diff()
        assert np.allclose(lhs.dropna(), rhs.dropna(), atol=1e-12)


def test_method_b_residual_equals_window_price_move():
    w = weekly_panel()
    peak = find_peak(w.pe_g)
    L = legs(w, "g", "eps_b_g", peak, pd.Timestamp("2026-11-27"), RECON)
    x = np.log(w.px_g.loc[peak:"2026-11-27"]).diff().iloc[1:]
    in_w = (x.index >= RECON[0]) & (x.index <= RECON[1])
    assert L["resid_lp"] == pytest.approx(float(x[in_w].sum()), abs=1e-12)


@pytest.mark.parametrize("seed_offset", range(5))
def test_no_lookahead_truncation(seed_offset):
    """Truncating the data at a random date must not change any leg computed on an earlier window."""
    rng = np.random.default_rng(7 + seed_offset)
    w = weekly_panel()
    dates = w.index[(w.index > pd.Timestamp("2026-02-01")) & (w.index < pd.Timestamp("2026-11-20"))]
    T = dates[rng.integers(len(dates))]
    end = w.index[w.index <= T][-2]
    peak = w.pe_g.loc["2025-01-03":end].idxmax()
    full = legs(w, "g", "eps_b_g", peak, end, RECON)
    trunc = legs(w.loc[:T], "g", "eps_b_g", peak, end, RECON)
    assert full == trunc


@pytest.mark.parametrize("eps,price,comp,expected", [
    (0.61, 0.0, 0.0, ("earnings-driven", False)),
    (0.60, 0.51, 0.0, ("price-driven", False)),
    (0.70, 0.60, -0.3, ("mixed", False)),
    (0.30, 0.30, 0.31, ("mixed", True)),
])
def test_classification_rule_is_the_frozen_one(eps, price, comp, expected):
    assert classify({"eps_share": eps, "price_share": price, "comp_share": comp}) == expected
