"""Episode engine (family B), first shocks (family A). PREREGISTRATION Part C2-C3.

Every quantity at index i uses closes up to and including i only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LADDER = [(0.90, "B10"), (0.85, "B15"), (0.80, "B20"), (0.70, "B30")]


def run_engine(close: pd.Series):
    """Return (daily_state DataFrame, episodes DataFrame, ladder events DataFrame)."""
    c = close.to_numpy(float)
    n = len(c)
    P, Pi = c[0], 0
    ath = c[0]
    legs = 0
    in_ep = False
    trough = trough_i = None
    ep = -1
    crossed: set[str] = set()
    st = {k: np.empty(n) for k in ["P", "Pi", "in_ep", "ep", "legs", "trough"]}
    eps, evs = [], []
    for i in range(n):
        x = c[i]
        if x > ath:
            ath = x
            legs = 0
        if in_ep:
            reset = None
            if x > P:
                reset = "new_high"
            elif x >= 1.10 * trough:
                reset = "rebound"
            if reset:
                e = eps[-1]
                e.update(reset_i=i, reset_type=reset)
                if reset == "rebound" and x <= ath:
                    legs += 1
                in_ep = False
                P, Pi = x, i
            else:
                if x < trough:
                    trough, trough_i = x, i
                    eps[-1].update(trough_i=i, trough=x)
                for lvl, name in LADDER:
                    if name not in crossed and x <= lvl * P:
                        crossed.add(name)
                        evs.append(dict(i=i, type=name, ep=ep))
        else:
            if x > P:
                P, Pi = x, i
            if x <= 0.90 * P:
                in_ep = True
                ep += 1
                trough, trough_i = x, i
                crossed = set()
                eps.append(dict(ep=ep, peak_i=Pi, peak=P, b10_i=i, trough_i=i, trough=x,
                                reset_i=np.nan, reset_type="open", legs_at_start=legs))
                for lvl, name in LADDER:
                    if x <= lvl * P:
                        crossed.add(name)
                        evs.append(dict(i=i, type=name, ep=ep))
        st["P"][i], st["Pi"][i], st["in_ep"][i] = P, Pi, in_ep
        st["ep"][i] = ep if in_ep else -1
        st["legs"][i], st["trough"][i] = legs, trough if in_ep else np.nan
    idx = close.index
    state = pd.DataFrame(st, index=idx)
    state["in_ep"] = state["in_ep"].astype(bool)
    state[["Pi", "ep", "legs"]] = state[["Pi", "ep", "legs"]].astype(int)
    E = pd.DataFrame(eps)
    if len(E):
        for k in ["peak_i", "b10_i", "trough_i"]:
            E[k.replace("_i", "_date")] = idx[E[k].astype(int)]
        E["reset_date"] = [idx[int(r)] if r == r else pd.NaT for r in E["reset_i"]]
        E["max_depth"] = E["trough"] / E["peak"] - 1
        E["sessions_to_trough"] = E["trough_i"] - E["b10_i"]
    V = pd.DataFrame(evs)
    if len(V):
        V["date"] = idx[V["i"]]
    return state, E, V


def shock_threshold_pct(spx: pd.Series, thr: float = -0.04) -> float:
    r = spx.pct_change().dropna()
    return float((r <= thr).mean())


def first_shocks(close: pd.Series, thr: float, gap: int = 126) -> pd.DataFrame:
    r = close.pct_change().to_numpy()
    shock = np.where(r <= thr)[0]
    # "no other shock in the prior 126 sessions": previous shock index < i - 126
    first = [i for i in shock if not np.any((shock < i) & (shock >= i - gap))]
    return pd.DataFrame(dict(i=first, date=close.index[first], ret=r[first], type="A"))


def assign_shock_episodes(A: pd.DataFrame, E: pd.DataFrame, n_episodes_offset: int = 100000):
    """C3: a first shock inside [peak_i, reset_i] of an episode takes its id, except a shock
    before the B10 crossing more than 63 sessions ahead of it, which gets its own id."""
    ids = []
    for k, row in A.iterrows():
        i = row["i"]
        got = None
        for _, e in E.iterrows():
            end = e["reset_i"] if e["reset_i"] == e["reset_i"] else np.inf
            if e["peak_i"] <= i <= end:
                if i < e["b10_i"] and e["b10_i"] - i > 63:
                    continue
                got = int(e["ep"])
                break
        ids.append(got if got is not None else n_episodes_offset + k)
    A = A.copy()
    A["ep"] = ids
    return A
