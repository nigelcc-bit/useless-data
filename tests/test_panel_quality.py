"""Per-episode missing-data gate (Pre-P1 revision e)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.panel_quality import (
    assert_episode_nan_gates,
    episode_missingness_report,
    episode_windows,
    universe_tickers,
)


def test_episode_windows_frozen():
    windows = episode_windows()
    assert "E7" in windows
    assert windows["E7"] == ("2026-10-28", "2026-11-05")
    assert "E1" in windows


def test_per_episode_nan_gate_and_existence_counts(capsys):
    tickers = universe_tickers()
    # Synthetic listing starts: half the book missing before 2020
    rng = np.random.default_rng(0)
    starts = {}
    for i, t in enumerate(tickers):
        if i % 3 == 0:
            starts[t] = pd.Timestamp("2017-01-03")
        elif i % 3 == 1:
            starts[t] = pd.Timestamp("2021-06-01")
        else:
            starts[t] = pd.Timestamp("2024-01-02")
    listing = pd.Series(starts)
    # Dense features for existing names
    panel = pd.DataFrame(
        {
            "feat_a": rng.normal(size=len(tickers)),
            "feat_b": rng.normal(size=len(tickers)),
        },
        index=tickers,
    )
    report = episode_missingness_report(panel, listing, ["feat_a", "feat_b"])
    captured = capsys.readouterr().out
    assert "n_existed_at_start" in captured
    assert set(report["episode"]) == set(episode_windows())
    # All existed names have features → nan gate passes
    assert_episode_nan_gates(report)
    # Existence counts rise over time
    assert report.loc[report["episode"] == "E1", "n_existed_at_start"].iloc[0] < report.loc[
        report["episode"] == "E7", "n_existed_at_start"
    ].iloc[0]


def test_nan_gate_fails_when_sparse():
    tickers = universe_tickers()[:6]
    listing = pd.Series({t: pd.Timestamp("2015-01-02") for t in tickers})
    panel = pd.DataFrame(
        {"feat_a": [1.0, np.nan, np.nan, np.nan, np.nan, np.nan]},
        index=tickers,
    )
    report = episode_missingness_report(panel, listing, ["feat_a"], max_nan_share=0.15)
    with pytest.raises(AssertionError, match="episode NaN gate failed"):
        assert_episode_nan_gates(report)
