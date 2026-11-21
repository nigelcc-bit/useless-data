"""Step 0 item 3: supplier vs builder equal-weight return over the first five SPX up days after 5 Nov 2026.

Universe: Blue Tsunami 23-name list (data/processed/nov5_cross_section_ingested.csv at repo root):
builders = layer 'builders' (AMZN, GOOGL, META, MSFT); suppliers = other ai_chain == 1 names (16);
the 3 non-AI controls are excluded. Daily close-to-close returns (Yahoo chart API, adjusted close not
needed over a two-week window; split check printed). Each name's return is compounded over the five
up days, then averaged equally. Flush reading if supplier EW > 2 x builder EW (both positive).
"""
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
UA = {"User-Agent": "Mozilla/5.0"}


def closes(sym):
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{sym}?period1=1793000000&period2=1795400000&interval=1d"
    for k in range(5):
        try:
            j = requests.get(url, headers=UA, timeout=30).json()["chart"]["result"][0]
            break
        except Exception:
            time.sleep(2 ** k)
    idx = pd.to_datetime(j["timestamp"], unit="s", utc=True).tz_convert("America/New_York").normalize().tz_localize(None)
    return pd.Series(j["indicators"]["quote"][0]["close"], index=idx, name=sym)


def main():
    u = pd.read_csv(REPO / "data" / "processed" / "nov5_cross_section_ingested.csv")
    u = u[u["ai_chain"] == 1]
    px = pd.concat([closes(s) for s in u["ticker"]] + [closes("^GSPC").rename("SPX")], axis=1)
    px = px.loc["2026-11-04":"2026-11-20"]
    px.to_csv(ROOT / "data" / "raw" / "step0_leadership_closes.csv")
    r = px.pct_change()
    after = r.loc["2026-11-06":]
    up = after.index[after["SPX"] > 0][:5]
    gr = (1 + r.loc[up]).prod() - 1
    b = gr[u.loc[u.layer == "builders", "ticker"]].mean()
    s = gr[u.loc[u.layer != "builders", "ticker"]].mean()
    print("SPX up days used:", [d.date() for d in up])
    print("max abs daily move per name (split check):", r.abs().max().sort_values().tail(3).round(3).to_dict())
    print(f"builders EW {b:+.2%}  suppliers EW {s:+.2%}  ratio {s / b if b else float('nan'):.2f}")
    out = pd.DataFrame(dict(name=gr.index, five_up_day_return=gr.values))
    out.to_csv(ROOT / "results" / "step0_leadership.csv", index=False)
    pd.DataFrame([dict(up_days=";".join(str(d.date()) for d in up), builders_ew=b, suppliers_ew=s,
                       ratio=s / b if b else None,
                       n_up_days=len(up),
                reading=("INCOMPLETE: only %d of 5 up days through 20 Nov; " % len(up) if len(up) < 5 else "") + ("flush (suppliers > 2x builders)" if (b > 0 and s > 2 * b) else
                                "thesis/neither (suppliers not > 2x builders)"))]).to_csv(
        ROOT / "results" / "step0_leadership_summary.csv", index=False)


if __name__ == "__main__":
    main()
