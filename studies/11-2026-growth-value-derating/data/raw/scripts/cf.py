from digi import load
import pandas as pd, numpy as np, datetime as dt
D=load('SECALL'); A,B=D['a'],D['b']
PRI={'ocf':['NetCashProvidedByUsedInOperatingActivities','NetCashProvidedByUsedInOperatingActivitiesContinuingOperations'],
 'capex':['PaymentsToAcquirePropertyPlantAndEquipment','PaymentsToAcquireProductiveAssets','PaymentsToAcquireOtherPropertyPlantAndEquipment','PaymentsForProceedsFromProductiveAssets'],
 'dep_amort':['DepreciationDepletionAndAmortization','DepreciationAndAmortization','DepreciationAmortizationAndAccretionNet','Depreciation','OtherDepreciationAndAmortization'],
 'amort_intangibles':['AmortizationOfIntangibleAssets','OtherDepreciationAndAmortization'],
 'net_income':['NetIncomeLoss','ProfitLoss'],
 'sbc':['ShareBasedCompensation','AllocatedShareBasedCompensationExpense'],
 'finance_lease_principal':['FinanceLeasePrincipalPayments','RepaymentsOfLongTermCapitalLeaseObligations'],
 'acquisitions':['PaymentsToAcquireBusinessesNetOfCashAcquired']}
def facts(t,c):
    f=A[t]['f'].get(c) or B.get(t,{}).get('us-gaap:'+c) or []
    df=pd.DataFrame(f,columns=['start','end','val','fy','fp','form','filed','frame']).dropna(subset=['start'])
    if df.empty: return df
    df['start']=pd.to_datetime(df.start); df['end']=pd.to_datetime(df.end); df['days']=(df.end-df.start).dt.days
    return df.sort_values('filed').drop_duplicates(['start','end'],keep='last')
def quarterly(df):
    if df.empty: return pd.Series(dtype=float,index=pd.DatetimeIndex([]))
    q={}
    for _,r in df[(df.days>=80)&(df.days<=100)].iterrows(): q[r.end]=(r.val,'direct')
    ytd=df[df.days>100]
    for _,r in ytd.iterrows():
        if r.end in q: continue
        prev=ytd[(ytd.start==r.start)&(ytd.end<r.end)]
        if len(prev):
            p=prev.sort_values('end').iloc[-1]
            if 75<=(r.end-p.end).days<=105: q[r.end]=(r.val-p.val,'ytd_diff')
        elif 75<= r.days <=105: q[r.end]=(r.val,'direct')
        else:
            # first quarter of a fiscal year whose ytd covers one quarter handled above; also try direct quarter + ytd 6m
            pass
    # second pass: 6M ytd minus Q1 direct
    for _,r in ytd.iterrows():
        if r.end in q: continue
        q1=df[(df.start==r.start)&(df.days>=80)&(df.days<=100)]
        if len(q1)==1 and 160<=r.days<=200: q[r.end]=(r.val-q1.val.iloc[0],'ytd_diff')
    s=pd.Series({k:v[0] for k,v in q.items()},dtype=float); s.index=pd.DatetimeIndex(s.index); s=s.sort_index(); s.attrs['how']={k:v[1] for k,v in q.items()}; return s
rows=[]; used={}
for t in A:
    out={}; used[t]={}
    for fld,cands in PRI.items():
        best=None
        for c in cands:
            s=quarterly(facts(t,c)); s=s[s.index>='2023-01-01']
            if best is None or len(s)>len(best[1])+1: best=(c,s)
        if best and len(best[1]): out[fld]=best[1]; used[t][fld]=best[0]
    df=pd.DataFrame(out); df.index.name='fiscal_quarter_end'; df.insert(0,'ticker',t); df.insert(1,'company',A[t]['name'])
    rows.append(df.reset_index())
CF=pd.concat(rows)
num=[c for c in PRI if c in CF]
CF[num]=CF[num]/1e6
CF['fcf_ocf_minus_capex']=CF.ocf-CF.capex
CF['fcf_minus_sbc']=CF.fcf_ocf_minus_capex-CF.sbc
CF['capex_to_dep']=(CF.capex/CF.dep_amort).round(3)
CF['ocf_to_ni']=(CF.ocf/CF.net_income).round(3)
CF=CF.round(1)
CF.to_csv('deliver/row6_top15_quarterly_cashflows_SEC_XBRL_USDm.csv',index=False)
pd.DataFrame(used).T.to_csv('deliver/row6_concepts_used_per_company.csv',index_label='ticker')
print(pd.DataFrame(used).T.to_string())
print(CF.groupby('ticker').agg(n=('ocf','size'),first=('fiscal_quarter_end','min'),last=('fiscal_quarter_end','max'),miss_ocf=('ocf',lambda x:x.isna().sum()),miss_capex=('capex',lambda x:x.isna().sum()),miss_da=('dep_amort',lambda x:x.isna().sum()),miss_ni=('net_income',lambda x:x.isna().sum()),miss_sbc=('sbc',lambda x:x.isna().sum())).to_string())
print(CF[CF.ticker=='NVDA'][['fiscal_quarter_end','ocf','capex','dep_amort','net_income','sbc']].tail(6).to_string())
