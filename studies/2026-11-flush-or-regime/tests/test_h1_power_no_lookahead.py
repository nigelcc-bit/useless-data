"""P2: fail if H1 power module reads any price dated after an event date."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.h1_power_check import (
    LookaheadError,
    classify_event_at_t,
    flag_all_events,
    trailing_sigma_to_t_minus_1,
    dist_from_high_at_t_minus_1,
)


def _synth(n: int = 500, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2000-01-03", periods=n)
    # inject crashes after warm-up (>252 sessions)
    r = rng.normal(0.0005, 0.015, n)
    r[300] = -0.05
    r[380] = -0.06
    px = 100 * np.exp(np.cumsum(r))
    return pd.Series(px, index=idx, name="PX")


def test_classify_rejects_prices_after_event_date():
    px = _synth()
    t = px.index[300]
    # deliberately include future prices
    with pytest.raises(LookaheadError):
        classify_event_at_t(px, t, "A")  # full series extends past t


def test_classify_accepts_truncated_through_t():
    px = _synth()
    t = px.index[300]
    truncated = px.loc[:t]
    ev = classify_event_at_t(truncated, t, "A")
    assert ev is not None
    assert ev["date"] == t
    assert ev["ret"] <= -0.04


def test_vectorised_flags_match_truncated_classify():
    px = _synth(500, seed=1)
    # force a sigma event too
    px.iloc[350] = px.iloc[349] * 0.90
    for rule in ("A", "B"):
        flags = flag_all_events(px, rule)
        assert len(flags) >= 1
        for _, row in flags.iterrows():
            t = row["date"]
            ev = classify_event_at_t(px.loc[:t], t, rule)
            assert ev is not None
            assert abs(ev["ret"] - row["ret"]) < 1e-12
            assert abs(ev["dist_high_tm1"] - row["dist_high_tm1"]) < 1e-12


def test_sigma_and_dist_use_only_t_minus_1():
    px = _synth()
    t = px.index[300]
    rets = px.pct_change()
    sig = trailing_sigma_to_t_minus_1(rets.loc[:t], t)
    # recompute manually from t-1
    loc = rets.index.get_loc(t)
    manual = float(rets.iloc[loc - 252 : loc].std(ddof=1))
    assert abs(sig - manual) < 1e-12
    d = dist_from_high_at_t_minus_1(px.loc[:t], t)
    through = px.iloc[:loc]
    manual_d = float(through.iloc[-1] / through.iloc[-252:].max() - 1)
    assert abs(d - manual_d) < 1e-12
