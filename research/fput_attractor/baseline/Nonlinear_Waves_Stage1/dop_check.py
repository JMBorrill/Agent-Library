"""Independent physical-coordinate adaptive solver check (short-time)."""
import sys, json, time
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
sys.path.insert(0,str(Path(__file__).parent))
from stage1 import matrices,rk4
n=8; alpha=.25; eta=.0025; F=.005;Omega=.347;periods=60
phi,d,w,c,g=matrices(n);T=2*np.pi/Omega

def physical_rhs(t,y):
    q=y[:n]; p=y[n:]
    dr=np.r_[q[1:]-q[:-1],-q[-1]]
    dl=np.r_[q[0],q[1:]-q[:-1]]
    return np.r_[p, dr-dl+alpha*(dr**2-dl**2)-eta*p+F*np.cos(Omega*t)]

a=time.monotonic()
sol=solve_ivp(physical_rhs,(0,periods*T),np.zeros(2*n),method='DOP853',rtol=1e-9,atol=1e-11,t_eval=[periods*T])
assert sol.success,sol.message
z=sol.y.T[0]
rk=rk4(w,c,g,alpha,eta,F,Omega,periods,320)[-1]
x=np.r_[phi@rk[:n],phi@rk[n:]]
diff=np.max(np.abs(z-x));rel=diff/max(1.,np.max(np.abs(z)))
result={'periods':periods,'dop853_nfev':sol.nfev,'rtol':1e-9,'atol':1e-11,'rk4_steps_per_period':320,'max_abs_state_diff':float(diff),'scaled_state_diff':float(rel),'wall_sec':time.monotonic()-a}
print(result,flush=True)
assert diff<5e-5, diff
with open(Path(__file__).parent/'results'/'independent_solver_check.json','w') as f:json.dump(result,f,indent=2)
