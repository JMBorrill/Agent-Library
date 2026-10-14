"""Coexisting-attractor validation for full N=8 forced damped FPUT.
Shows basin dependence, not classification of a particular quasiperiodic attractor.
"""
from pathlib import Path
import json,sys
import numpy as np
from numba import njit
from scipy.integrate import solve_ivp
from floquet import periodic_orbit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Nonlinear_Waves_Stage1'))
from stage1 import matrices,dynamics,energies

@njit(cache=True)
def integrate_from(y0,w,c,g,F,periods,steps):
    alpha=.25;eta=.0025;Omega=.347
    period=2*np.pi/Omega;h=period/steps;t=0.
    y=y0.copy();trace=np.zeros((periods,len(y)))
    for p in range(periods):
        for _ in range(steps):
            k1=dynamics(t,y,w,c,g,alpha,eta,F,Omega)
            k2=dynamics(t+h/2,y+h*k1/2,w,c,g,alpha,eta,F,Omega)
            k3=dynamics(t+h/2,y+h*k2/2,w,c,g,alpha,eta,F,Omega)
            k4=dynamics(t+h,y+h*k3,w,c,g,alpha,eta,F,Omega)
            y+=(h/6)*(k1+2*k2+2*k3+k4)
            t+=h
        trace[p]=y
    return trace

def run():
    phi,d,w,c,g=matrices(8);c=np.ascontiguousarray(c);F=.0045
    y_seed=np.array(json.loads((Path(__file__).parent/'floquet_detailed.json').read_text())['8_0.0045']['fixed_point']);r,M,v,res=periodic_orbit(y_seed,w,c,g,F,360)
    assert res<1e-9
    roots=r.x
    n=3500;win=750
    results=[]
    for label,y0 in (('zero',np.zeros(16)),('locked_plus_1e-3',roots+np.r_[.001,np.zeros(15)]),('locked_plus_1e-2',roots+np.r_[.01,np.zeros(15)])):
        data=integrate_from(y0,w,c,g,F,n,320)
        E=energies(data,w)
        row={'initial_state':label,'periods':n,'steps_per_period':320,'mode1_last750_range':float(np.ptp(E[-win:,0])),'mode2_last750_range':float(np.ptp(E[-win:,1])),'last_state_supdist_from_drive_locked_fixed_point':float(np.max(abs(data[-1]-roots))),'max_locked_branch_floquet_modulus':float(max(abs(v)))}
        results.append(row)
        print(row,flush=True)
        if label=='zero':
            # long-time independent solver check, same terminal state, 20 subsequent periods
            state=data[-21]
            T=2*np.pi/.347
            sol=solve_ivp(lambda t,y:dynamics(t,y,w,c,g,.25,.0025,F,.347),(0,20*T),state,method='DOP853',rtol=1e-11,atol=1e-13)
            # stroboscopic forcing phase reset is valid because snapshot occurred at integer drive period
            row['short_forward_crosscheck_DOP853_vs_RK4_320_terminal_supnorm']=float(np.max(abs(sol.y[:,-1]-data[-1])))
            row['short_forward_crosscheck_DOP853_nfev']=int(sol.nfev)
    (Path(__file__).parent/'basin_check.json').write_text(json.dumps(results,indent=2))
    return results
if __name__=='__main__':run()
