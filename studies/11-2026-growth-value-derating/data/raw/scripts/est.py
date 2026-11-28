from digi import load
import pandas as pd, numpy as np
Y=load('YEST'); asof=pd.Timestamp(Y['asof'][:10]); D=Y['d']
rows=[]
for t,v in D.items():
    if not v.get('trend'): continue
    tr={x['p']:x for x in v['trend']}
    y0,y1=tr.get('0y',{}),tr.get('+1y',{})
    r={'ticker':t,'price':v.get('px'),'mcap':v.get('mcap'),'fy0_end':y0.get('end'),'fy1_end':y1.get('end')}
    for p,x in [('fy0',y0),('fy1',y1)]:
        for k in ['avg','n','cur','d7','d30','d60','d90','up7','up30','dn7','dn30']: r[f'{p}_{k}']=x.get(k)
    if r['fy0_end']:
        mleft=max(0,min(12,(pd.Timestamp(r['fy0_end'])-asof).days/30.44)); w=mleft/12
        for s in ['cur','d30','d60','d90']:
            a,b=r.get(f'fy0_{s}'),r.get(f'fy1_{s}')
            r[f'ntm_eps_{s}']= (w*a+(1-w)*b) if a is not None and b is not None else np.nan
        r['w_fy0']=round(w,3)
    rows.append(r)
E=pd.DataFrame(rows)
E.to_csv('deliver/row9_constituent_consensus_eps_yahoo_snapshot_20261128.csv',index=False)
def load_w(f):
    d=pd.read_csv('deliver/'+f); d=d[d.assetClass.astype(str).str.contains('Equity')].copy()
    d['ticker']=d.ticker.astype(str).str.strip().str.replace(' ','-').str.replace('.','-').replace({'BRKB':'BRK-B','BFB':'BF-B'})
    return d.groupby('ticker').marketWeight.sum()
res={}
for nm,f in [('growth','row5_IVW_holdings_20261125.csv'),('value','row5_IVE_holdings_20261125.csv')]:
    w=load_w(f); e=E.set_index('ticker').reindex(w.index); cov=w[e.fy1_avg.notna()].sum()/w.sum()
    up=e.fy1_up30.fillna(0); dn=e.fy1_dn30.fillna(0)
    br_cnt=(up.sum()-dn.sum())/(up.sum()+dn.sum())
    br_w=((up-dn)/(up+dn).replace(0,np.nan)*w).sum()/w[(up+dn)>0].sum()
    ch90=(e.fy1_cur/e.fy1_d90-1); ch30=(e.fy1_cur/e.fy1_d30-1)
    ok=ch90.notna()&np.isfinite(ch90)&(e.fy1_d90.abs()>0.05)
    share_up90=(w[ok]*(ch90[ok]>0)).sum()/w[ok].sum()
    wch90=(w[ok]*ch90[ok].clip(-0.5,0.5)).sum()/w[ok].sum()
    ok3=ch30.notna()&np.isfinite(ch30)&(e.fy1_d30.abs()>0.05)
    wch30=(w[ok3]*ch30[ok3].clip(-0.5,0.5)).sum()/w[ok3].sum()
    res[nm]={'n_names':len(w),'weight_coverage':round(cov,3),'up30_count':int(up.sum()),'down30_count':int(dn.sum()),'breadth_count_(up-dn)/(up+dn)':round(br_cnt,3),'breadth_capweighted':round(br_w,3),'capw_share_FY1_up_vs_90d':round(share_up90,3),'capw_FY1_EPS_chg_90d_pct':round(wch90*100,2),'capw_FY1_EPS_chg_30d_pct':round(wch30*100,2)}
R=pd.DataFrame(res); R.index.name='metric'; R.to_csv('deliver/row8_revision_breadth_growth_vs_value_snapshot_20261128.csv'); print(R)
print(E[E.ticker.isin(['NVDA','MSFT','AAPL','XOM'])][['ticker','fy0_end','fy0_avg','fy1_avg','ntm_eps_cur','ntm_eps_d90','fy1_up30','fy1_dn30']])
