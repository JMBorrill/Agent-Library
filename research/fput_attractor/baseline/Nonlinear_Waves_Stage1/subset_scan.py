"""Exploratory hypothesis generator; selection of subsets is IN-SAMPLE, not novel evidence."""
import sys,csv
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from stage1 import matrices,rk4,measurements
n=8; phi,d,w,c,g=matrices(n)
sets=[(1,2),(1,2,3),(1,2,4),(1,2,5),(1,2,6),(1,2,7),(1,2,8),(1,2,3,4),(1,2,3,5),(1,2,3,6),(1,2,4,5),(1,2,4,6),(1,2,3,4,5),(1,2,3,4,5,6),(1,2,3,4,5,6,7,8)]
rows=[]
for subs in sets:
    ix=np.array(subs)-1
    s=rk4(w[ix],np.ascontiguousarray(c[np.ix_(ix,ix,ix)]),g[ix],.25,.0025,.005,.347,2500,160)
    r=measurements(s,w[ix],500)
    row={'mode_indices':','.join(map(str,subs)),'mode_count':len(subs),'E1_range':r['mode1_range'],'E2_range':r['mode2_range'],'E1_mean':r['mode1_mean'],'E2_mean':r['mode2_mean'],'dominant_period':r['mode1_dominant_modulation_period_drive_cycles']}
    rows.append(row)
    print(row, flush=True)
with open(Path(__file__).parent/'results'/'subset_scan.csv','w',newline='') as f:
    wr=csv.DictWriter(f,fieldnames=rows[0].keys());wr.writeheader();wr.writerows(rows)
