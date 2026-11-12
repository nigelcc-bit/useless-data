"""PCA (first component) and VIFs for H3."""

from __future__ import annotations

import numpy as np
import pandas as pd


def winsorize(s: pd.Series, p: float = 0.025) -> pd.Series:
    lo, hi = s.quantile(p), s.quantile(1 - p)
    return s.clip(lo, hi)


def standardize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        mu, sd = out[c].mean(), out[c].std(ddof=0)
        out[c] = 0.0 if sd == 0 or not np.isfinite(sd) else (out[c] - mu) / sd
    return out


def pc1_scores_loadings(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """First principal component scores + loadings on complete columns.

    Uses SVD of the standardized matrix. Returns (scores aligned to df.index,
    loadings Series indexed by columns). Empty if <2 columns or <3 rows.
    """
    cols = [c for c in df.columns if df[c].notna().sum() >= 3]
    if len(cols) < 1 or len(df) < 3:
        return pd.Series(index=df.index, dtype="float64"), pd.Series(dtype="float64")
    # require complete cases across selected cols for PCA fit
    sub = df[cols].dropna()
    if len(sub) < 3 or sub.shape[1] < 1:
        return pd.Series(index=df.index, dtype="float64"), pd.Series(dtype="float64")
    if sub.shape[1] == 1:
        z = standardize(sub)
        scores = z.iloc[:, 0].reindex(df.index)
        loadings = pd.Series({cols[0]: 1.0})
        return scores, loadings
    z = standardize(sub).to_numpy()
    # SVD
    _u, _s, vt = np.linalg.svd(z, full_matrices=False)
    loadings = pd.Series(vt[0], index=cols)
    # sign: positive loading on first column
    if loadings.iloc[0] < 0:
        loadings = -loadings
    scores_fit = z @ loadings.to_numpy()
    scores = pd.Series(scores_fit, index=sub.index).reindex(df.index)
    return scores, loadings


def vif_table(X: pd.DataFrame) -> pd.Series:
    """Variance inflation factors via regressing each col on the others."""
    cols = list(X.columns)
    out = {}
    for i, c in enumerate(cols):
        y = X[c].to_numpy()
        Z = X.drop(columns=[c]).to_numpy()
        if Z.shape[1] == 0:
            out[c] = 1.0
            continue
        # add intercept
        Z1 = np.column_stack([np.ones(len(Z)), Z])
        try:
            beta, *_ = np.linalg.lstsq(Z1, y, rcond=None)
            yhat = Z1 @ beta
            ss_res = float(np.sum((y - yhat) ** 2))
            ss_tot = float(np.sum((y - y.mean()) ** 2))
            r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
            out[c] = float("inf") if r2 >= 1.0 else 1.0 / (1.0 - r2)
        except np.linalg.LinAlgError:
            out[c] = float("nan")
    return pd.Series(out, name="VIF")
