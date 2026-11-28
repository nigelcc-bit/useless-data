import json,base64,gzip,glob,datetime as dt,numpy as np,pandas as pd
def load(k):
    f=sorted(glob.glob(f'chunks/{k}.*')); n=int(f[0].split('.')[-1]); s=''.join(open(f'chunks/{k}.{i:03d}.{n}').read() for i in range(n))
    return json.loads(gzip.decompress(base64.b64decode(s)))
def xdate(xs, xticks, y0):
    t=np.array(xticks); yrs=np.array([dt.date(y0+i,1,1).toordinal() for i in range(len(t))])
    return [dt.date.fromordinal(int(round(o))) for o in np.interp(xs,t,yrs,left=np.nan,right=np.nan) if not np.isnan(o)] , np.interp(xs,t,yrs)
