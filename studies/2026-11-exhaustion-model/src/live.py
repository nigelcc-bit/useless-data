"""Live test (PREREGISTRATION section 7 / C8). Frozen predictions from training-only fits.

Writes results/live_frozen.csv and results/live_state.csv. Re-run after 2027 dates to score.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate as ev  # noqa: E402
import features as F  # noqa: E402
import models as M  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
# NYSE holidays used for counting forward sessions (from the published NYSE calendar as recalled;
# verify before scoring): Thanksgiving, Christmas, New Year, MLK, Presidents, Good Friday, Memorial Day.
HOL = pd.to_datetime(["2026-11-26", "2026-12-25", "2027-01-01", "2027-01-18", "2027-02-15",
                      "2027-03-26", "2027-05-31"])
LIVE_LAYERS = ["H1", "H2b", "H2c", "H3"]


def nth_session(start, n):
    days = pd.bdate_range(start + pd.Timedelta(days=1), periods=n + 20, freq="C", holidays=HOL)
    return days[n - 1]


def main():
    data, thr = ev.build_all()
    meds = json.load(open(R / "credit_medians.json"))
    sel = pd.read_csv(R / "layer0_selection.csv")
    L = pd.read_csv(R / "layer_tests_train.csv")
    t0 = pd.Timestamp("2026-11-05")
    out, state = [], []
    for a in ev.ASSETS:
        d = data[a]["d"]
        r = data[a]["rows"]
        for col, newcol, key in [("credit_ratio", "credit_nc", "credit")]:
            d[newcol] = np.where(d[col].isna(), np.nan, (d[col] < meds[a][key]).astype(float))
            r[newcol] = np.where(r[col].isna(), np.nan, (r[col] < meds[a][key]).astype(float))
        d["is_signal"] = 0.0
        last = d.index[-1]
        for when in [t0, last]:
            x = d.loc[[when]]
            for t in ev.TARGETS:
                s = sel[(sel.asset == a) & (sel.target == t)].iloc[0]
                best = s["best"].split("+")
                tr = r[r["sample"] == "train"].dropna(subset=ev.L0F + [t])
                p0, _ = M.fit_predict(tr[best].to_numpy(float), tr[t].to_numpy(float), x[best].to_numpy(float))
                out.append(dict(asset=a, as_of=when.date(), target=t, layer="L0", model="+".join(best), p=float(p0[0]),
                                train_base_rate=float(tr[t].mean())))
                for layer in LIVE_LAYERS:
                    row = L[(L.asset == a) & (L.target == t) & (L.layer == layer)].iloc[0]
                    feat = ev.LAYERS[layer][0]
                    tr2 = ev.layer_frame(a, data, layer, t, "train")
                    if layer == "H3":
                        tr2 = tr2.assign(credit_nc=np.where(tr2["credit_ratio"] < meds[a]["credit"], 1.0, 0.0))
                    cols = row["base2"].split("+") + [feat]
                    pk, _ = M.fit_predict(tr2[cols].to_numpy(float), tr2[t].to_numpy(float), x[cols].to_numpy(float))
                    out.append(dict(asset=a, as_of=when.date(), target=t, layer=layer, model="+".join(cols),
                                    p=float(pk[0]), feature_value=float(x[feat].iloc[0]), train_verdict=row["verdict"]))
        st = d.iloc[-1]
        c0 = d.loc[t0, "close"]
        state.append(dict(asset=a, as_of=last.date(), close=st["close"], ref_peak=st["P"],
                          ref_peak_date=d.index[int(st["Pi"])].date(), depth=st["depth"], in_episode=bool(st["in_ep"]),
                          above200=st["above200"], legs=st["legs"], vix=st["vix"], vix_vix3m=st["vratio"],
                          vixhi=st["vixhi"], fed6m=st["fed6m"], baa_gs10_lag=st["baa_gs10_lag"], kr_yoy=st["kr_yoy"],
                          close_5nov=c0, T1_line_from_5nov=0.90 * c0, min_close_since_5nov=d.loc[t0:, "close"].iloc[1:].min(),
                          T1_from_5nov_failed_yet=bool(d.loc[t0:, "close"].iloc[1:].min() <= 0.90 * c0),
                          h2b_signal_since_5nov=str(F.signal_dates(d, data[a]["E"], "H2b").query("i > @d.index.get_loc(@t0)")["i"].map(lambda i: d.index[i].date()).tolist())))
    LF = pd.DataFrame(out)
    LF.to_csv(R / "live_frozen.csv", index=False)
    S = pd.DataFrame(state)
    S["score_date_63"] = nth_session(t0, 63).date()
    S["score_date_126"] = nth_session(t0, 126).date()
    S.to_csv(R / "live_state.csv", index=False)
    vr = data["SPX"]["d"]["vratio"].loc["2026-11-10":]
    print(vr.round(3).to_string())
    print(S.T.to_string())
    print(LF.round(3).to_string())


if __name__ == "__main__":
    main()
