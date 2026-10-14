"""Limited nearby-amplitude exploratory check; not a held-out test of a fitted theory."""
import sys,csv
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from stage1 import matrices,rk4,measurements
n=8;phi,d,w,c,g=matrices(n)
rows=[]
for F in (0.0045,0.005,0.0055):
  for m in (2,3,4,8):
    z=rk4(w[:m],np.ascontiguousarray(c[:m,:m,:m]),g[:m],.25,.0025,F,.347,2500,160)
    vals=measurements(z,w[:m],500)
    row={'F':F,'modes':m,**vals}
    print(F,m,vals['mode1_range'],vals['mode2_range'],flush=True)
    rows.append(row)
with (Path(__file__).parent/'results'/'amplitude_scan.csv').open('w',newline='') as f:
    wr=csv.DictWriter(f,fieldnames=rows[0].keys());wr.writeheader();wr.writerows(rows)
