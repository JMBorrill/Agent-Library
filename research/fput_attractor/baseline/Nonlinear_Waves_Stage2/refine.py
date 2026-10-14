"""Refine Floquet |mu|=1 stability thresholds and check solver/step consistency."""
from pathlib import Path
import csv,json,sys
import numpy as np
from scipy.optimize import brentq,root
from scipy.integrate import solve_ivp
from floquet import periodic_orbit,tangent_rhs,orbit_one_period
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Nonlinear_Waves_Stage1'))
from stage1 import matrices,rk4,measurements
P=Path(__file__).parent

def adaptive_solve(y,w,c,g,F):
    m=len(w);dim=2*m;T=2*np.pi/.347
    def evalmap(y):
        z=np.r_[y,np.eye(dim).reshape(-1)]
        sol=solve_ivp(lambda t,z:tangent_rhs(t,z,w,c,g,.25,.0025,F,.347),(0,T),z,method='DOP853',rtol=1e-11,atol=1e-13)
        assert sol.success
        last=sol.y[:,-1];return last[:dim],last[dim:].reshape((dim,dim))
    def fn(y):
        end,M=evalmap(y)
        return end-y,M-np.eye(dim)
    r=root(fn,y,jac=True,method='hybr',options={'xtol':3e-12})
    end,M=evalmap(r.x)
    vals=np.linalg.eigvals(M)
    return {'residual':float(max(abs(end-r.x))),'max_multiplier_modulus':float(max(abs(vals))),'max_multiplier':[[float(x.real),float(x.imag)] for x in vals if abs(x)>0.995], 'root_success':bool(r.success),'root_state_difference_from_seed':float(max(abs(y-r.x)))}


def run():
    raw=json.loads((P/'floquet_detailed.json').read_text());output=[]
    for m,bracket in ((4,(.0050,.0055)),(8,(.0045,.0050))):
        phi,d,w0,c0,g0=matrices(8);w=w0[:m];c=np.ascontiguousarray(c0[:m,:m,:m]);g=g0[:m]
        seed=np.array(raw[f'{m}_{bracket[0]:.4f}']['fixed_point'])
        for steps in (180,360,720):
            def scalar(F):
                r,M,v,res=periodic_orbit(seed,w,c,g,F,steps)
                if res>1e-8: raise RuntimeError((m,F,res))
                return max(abs(v))-1
            a,b=bracket
            t=brentq(scalar,a,b,xtol=2e-11)
            r,M,v,res=periodic_orbit(seed,w,c,g,t,steps)
            top=v[np.argmax(abs(v))]
            rec={'modes':m,'steps_per_period':steps,'critical_F':float(t),'max_multiplier_modulus':float(max(abs(v))),'max_multiplier_real':float(top.real),'max_multiplier_imag':float(top.imag),'fixed_point_residual':float(res),'adaptive_at_RK4_threshold':adaptive_solve(r.x,w,c,g,float(t)) if steps==720 else None}
            output.append(rec)
            print(f'm={m}, steps={steps}, critical_F={t:.10f}, lead={top.real:.7f}+{top.imag:.7f}i',flush=True)
    # Compare full chain from rest to the stable locked solution at F=.0045
    phi,d,w,c,g=matrices(8);out=[]
    for F in (.0044,.0045,.0046,.0048,.0050):
        r,M,v,res=periodic_orbit(np.array(raw['8_0.0045']['fixed_point']),w,np.ascontiguousarray(c),g,F,360)
        z=rk4(w,np.ascontiguousarray(c),g,.25,.0025,F,.347,4500,160)
        row={'F':F,'max_floquet_abs':float(max(abs(v))),'root_residual':float(res),'late_mode1_range_1000':float(measurements(z,w,1000)['mode1_range']), 'late_mode2_range_1000':float(measurements(z,w,1000)['mode2_range']),'trajectory_terminal_distance_to_locked_orbit':float(max(abs(z[-1]-r.x)))}
        out.append(row)
        print('Attractor from rest',row,flush=True)
    (P/'floquet_refined.json').write_text(json.dumps(output,indent=2))
    (P/'rest_initial_condition_test.json').write_text(json.dumps(out,indent=2))
    return output,out
if __name__=='__main__': run()
