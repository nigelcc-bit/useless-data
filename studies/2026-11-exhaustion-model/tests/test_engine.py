import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import episodes as epi  # noqa: E402
import models  # noqa: E402


def S(v):
    return pd.Series(np.asarray(v, float), index=pd.bdate_range("2000-01-03", periods=len(v)))


def test_engine_basic_ladder_and_rebound_reset():
    # peak 100, fall to 89 (B10), 84 (B15), rebound to 93 (>=1.1*84=92.4 -> reset), fall again
    s = S([90, 100, 95, 89, 84, 88, 93, 95, 85, 80])
    st, E, V = epi.run_engine(s)
    assert list(V["type"])[:2] == ["B10", "B15"]
    assert E.iloc[0]["reset_type"] == "rebound" and int(E.iloc[0]["reset_i"]) == 6
    # new P tracked from reset: 93 -> 95; 85 <= 0.9*95=85.5 -> second episode B10
    assert E.iloc[1]["peak"] == 95 and int(E.iloc[1]["b10_i"]) == 8
    # legs counts rebound resets since ATH 100
    assert st["legs"].iloc[8] == 1


def test_engine_new_high_reset():
    s = S([100, 89, 95, 101, 91.0, 90.0])
    st, E, V = epi.run_engine(s)
    assert E.iloc[0]["reset_type"] == "new_high"
    assert int(E.iloc[1]["b10_i"]) == 5  # 90.0 <= 0.9*101 = 90.9; 91.0 is not


def test_engine_no_lookahead():
    rng = np.random.default_rng(0)
    s = S(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 1500))))
    full, _, _ = epi.run_engine(s)
    for cut in [300, 777, 1200]:
        part, _, _ = epi.run_engine(s.iloc[:cut])
        pd.testing.assert_frame_equal(full.iloc[:cut], part)


def test_first_shocks_gap():
    r = np.zeros(400)
    r[[10, 100, 300]] = -0.05
    s = S(100 * np.cumprod(1 + r))
    A = epi.first_shocks(s, -0.04)
    assert list(A["i"]) == [10, 300]


def test_bayes_logit_recovers_sign():
    rng = np.random.default_rng(1)
    x = rng.normal(size=(400, 1))
    y = (rng.random(400) < 1 / (1 + np.exp(-1.5 * x[:, 0]))).astype(float)
    assert models.coef(x, y)[1] > 0.8


def test_bh():
    a = models.bh([0.01, 0.04, 0.03, 0.5])
    assert np.allclose(a, [0.04, 0.0533333, 0.0533333, 0.5], atol=1e-6)


def test_lag_monthly_m_plus_2():
    import features
    m = pd.Series([1.0, 2.0, 3.0], index=pd.to_datetime(["2020-01-01", "2020-02-01", "2020-03-01"]))
    d = pd.to_datetime(["2020-02-28", "2020-03-02", "2020-03-31", "2020-04-01", "2020-05-15"])
    v = features.lag_monthly(m, pd.DatetimeIndex(d))
    assert np.isnan(v.iloc[0]) and v.iloc[1] == 1.0 and v.iloc[2] == 1.0 and v.iloc[3] == 2.0 and v.iloc[4] == 3.0
