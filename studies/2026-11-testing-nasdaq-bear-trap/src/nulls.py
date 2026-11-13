"""Null-model price simulators for Study A ("does support exist?").

Every simulator takes the real log-return series and returns a callable
sim(n, rng) -> price path of length n (starting at 100). The event engine is
then run on simulated paths with the identical Spec, so selection effects
(a break has to happen first) are matched by construction.

Models
  gbm      i.i.d. Gaussian, mean and std matched            (no fat tails, no clustering)
  iid      i.i.d. resample of real returns                  (fat tails, no clustering)
  block    stationary block bootstrap, mean block 20d       (fat tails, clustering, short-range
                                                             autocorrelation; level-dependence destroyed)
  garch    GARCH(1,1) with Student-t innovations            (parametric clustering)
  msvol    2-state Markov-switching mean and variance       (regime structure)

The `block` model is the pre-registered primary null: it keeps everything about
the return process except any dependence on where price sits relative to a
prior low.
"""
from __future__ import annotations

import warnings
import numpy as np

from .inference import stationary_bootstrap_idx


def _to_path(lr: np.ndarray, start: float = 100.0) -> np.ndarray:
    return start * np.exp(np.r_[0.0, np.cumsum(lr)])


def make_gbm(lr: np.ndarray):
    mu, sd = float(np.mean(lr)), float(np.std(lr, ddof=1))
    return lambda n, rng: _to_path(rng.normal(mu, sd, n - 1))


def make_iid(lr: np.ndarray):
    return lambda n, rng: _to_path(rng.choice(lr, n - 1, replace=True))


def make_block(lr: np.ndarray, mean_block: float = 20.0):
    def sim(n, rng):
        idx = stationary_bootstrap_idx(len(lr), n - 1, mean_block, rng)
        return _to_path(lr[idx])
    return sim


def make_garch(lr: np.ndarray):
    from arch import arch_model
    am = arch_model(100 * lr, mean="Constant", vol="GARCH", p=1, q=1, dist="t")
    res = am.fit(disp="off")
    p = res.params
    mu, omega, alpha, beta, nu = (float(p["mu"]), float(p["omega"]), float(p["alpha[1]"]),
                                  float(p["beta[1]"]), float(p["nu"]))
    scale = np.sqrt((nu - 2) / nu)          # unit-variance Student-t
    burn = 500

    def sim(n, rng):
        m = n - 1 + burn
        z = rng.standard_t(nu, m) * scale
        eps = np.empty(m)
        s2 = omega / max(1e-12, 1 - alpha - beta)
        for i in range(m):
            eps[i] = np.sqrt(s2) * z[i]
            s2 = omega + alpha * eps[i] ** 2 + beta * s2
        return _to_path((mu + eps[burn:]) / 100)
    sim.params = dict(mu=mu, omega=omega, alpha=alpha, beta=beta, nu=nu)
    return sim


def make_msvol(lr: np.ndarray):
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = MarkovRegression(lr * 100, k_regimes=2, trend="c", switching_variance=True)
        res = mod.fit(disp=False, search_reps=5)
    P = res.regime_transition[:, :, 0]          # P[i, j] = Pr(S_t = i | S_{t-1} = j)
    names = list(res.model.param_names)
    p = dict(zip(names, np.asarray(res.params)))
    mu = np.array([p["const[0]"], p["const[1]"]]) / 100
    sd = np.sqrt(np.array([p["sigma2[0]"], p["sigma2[1]"]])) / 100
    # stationary distribution
    evals, evecs = np.linalg.eig(P)
    pi = np.real(evecs[:, np.argmin(np.abs(evals - 1))])
    pi = pi / pi.sum()

    def sim(n, rng):
        s = np.empty(n - 1, dtype=int)
        s[0] = rng.choice(2, p=pi)
        u = rng.random(n - 1)
        for i in range(1, n - 1):
            s[i] = 0 if u[i] < P[0, s[i - 1]] else 1
        return _to_path(rng.normal(mu[s], sd[s]))
    sim.params = dict(mu=mu, sd=sd, P=P, pi=pi)
    return sim


MODELS = {
    "gbm": make_gbm,
    "iid": make_iid,
    "block": make_block,
    "garch": make_garch,
    "msvol": make_msvol,
}
