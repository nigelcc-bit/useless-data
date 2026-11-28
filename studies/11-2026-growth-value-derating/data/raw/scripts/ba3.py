from digi import load
import numpy as np, pandas as pd, datetime as dt
D=load('BA')
def groups(v):
    v=sorted(v); g=[[v[0]]]
    for a in v[1:]:
        (g[-1].append(a) if a-g[-1][-1]<=2 else g.append([a]))
    return [np.mean(x) for x in g]
k,off=1.271,-9; o0=dt.date(2008,1,1).toordinal()
todate=lambda x: pd.Timestamp(dt.date.fromordinal(int(round(o0+(x-583.5)/k+off))))
px=pd.read_csv('deliver/row3_sp500_growth_value_price_index_daily_2016_now.csv',index_col=0,parse_dates=True)
pe=pd.read_csv('deliver/row1_yardeni_fwd_pe_growth_value_daily_digitised_1995_2026.csv',index_col=0,parse_dates=True)
res={}
for fig,pes,col,nm,peN in [('F16',[30,20,15,10],'sp500_growth_2029','growth','growth'),('F17',[20,15,10],'sp500_value_2034','value','value')]:
    F=D[fig]; n=len(pes)
    red=pd.DataFrame([(todate(c[0]),c[2][0]) for c in F['cols'] if len(c[2])==1],columns=['d','y'])
    red=red[red.d>='2016-11-01']; act=px[col].reindex(red.d,method='ffill').values
    b,a=np.polyfit(red.y,np.log10(act),1); r=np.log10(act)-(a+b*red.y)
    msg=f'{fig} red-fit px/decade {-1/b:.1f} resid sd {r.std()*np.log(10)*100:.2f}%'
    if fig=='F16':
        yt=groups(F['yt']); vals=[9000,8000,7000,6000,5000,4000,3000,2000,1000,900,800,700,600,500,400,300]
        bb,aa=np.polyfit(yt,np.log10(vals),1); msg+=f' | tick-fit px/decade {-1/bb:.1f}; value at y=600 tick {10**(aa+bb*600):.1f} vs red-fit {10**(a+b*600):.1f}'
        a,b=aa,bb  # use exact tick calibration for growth
    print(msg)
    recs=[]
    for x,bl,rd in F['cols']:
        if len(bl)!=n: continue
        v=10**(a+b*np.array(bl)); e=v/np.array(pes)
        recs.append((todate(x),np.exp(np.log(e).mean()),e.min(),e.max()))
    df=pd.DataFrame(recs,columns=['date','eps','eps_min_line','eps_max_line']).groupby('date').mean()
    print(' line disagreement median %', round(((df.eps_max_line-df.eps_min_line)/df.eps).median()*100,2), 'last', df.tail(1).round(2).to_dict('records'))
    res[nm]=df.eps
    # derived
    d=(px[col]/pe[peN].reindex(px.index)).dropna()
    w_ba=df.eps.reindex(pd.date_range(df.index.min(),df.index.max())).interpolate(limit=10).resample('W-FRI').last()
    w_dr=d.rolling(5,center=True,min_periods=3).median().resample('W-FRI').last()
    j=pd.concat({'ba':w_ba,'derived':w_dr},axis=1).dropna().loc['2017-01-01':]
    rel=(j.derived/j.ba-1)*100
    print(' derived/BA -1 (%): mean',round(rel.mean(),2),'sd',round(rel.std(),2),'2024+ mean',round(rel.loc['2024':].mean(),2),'sd',round(rel.loc['2024':].std(),2))
    res[nm+'_derived']=w_dr
pd.to_pickle(res,'eps.pkl')
