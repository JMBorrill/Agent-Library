"""Independent exact one-soliton benchmark for the unforced undamped Toda chain.
V(r) = exp(-r)+r-1; q''[n]=exp(q[n-1]-q[n])-exp(q[n]-q[n+1]).
Uses prescribed exact boundary displacements of an infinite lattice.
"""
from pathlib import Path
import json
import numpy as np
from scipy.integrate import solve_ivp
from scipy.special import expit

def exact(n,t,kappa=.4,n0=35.):
    beta=np.sinh(kappa)
    a=-2*(kappa*(np.asarray(n)-n0)-beta*t)
    ap=a+2*kappa
    q=np.logaddexp(0,ap)-np.logaddexp(0,a)
    p=2*beta*(expit(ap)-expit(a))
    dd=(2*beta)**2*(expit(ap)*(1-expit(ap))-expit(a)*(1-expit(a)))
    return q,p,dd

def run(nsites=120, t_end=45.):
    ids=np.arange(1,nsites+1)
    q,p,_=exact(ids,0);init=np.r_[q,p]
    def rhs(t,z):
        q=z[:nsites];p=z[nsites:]
        qb=np.r_[exact(0,t)[0],q,exact(nsites+1,t)[0]]
        force=np.exp(qb[:-2]-qb[1:-1])-np.exp(qb[1:-1]-qb[2:])
        return np.r_[p,force]
    checkpoints=np.linspace(0,t_end,91)
    r=solve_ivp(rhs,(0,t_end),init,t_eval=checkpoints,method='DOP853',rtol=1e-10,atol=1e-12)
    assert r.success,r.message
    e=[];strain=[]
    for t,z in zip(r.t,r.y.T):
        qq,pp,_=exact(ids,t)
        e.append(float(np.max(np.abs(z-np.r_[qq,pp]))))
        exact_bond=np.diff(np.r_[exact(0,t)[0], qq, exact(nsites+1,t)[0]])
        sim_bond=np.diff(np.r_[exact(0,t)[0], z[:nsites],exact(nsites+1,t)[0]])
        strain.append(float(np.max(abs(sim_bond-exact_bond))))
    q0,p0,dd0=exact(ids,7.5)
    eq_qq=np.r_[exact(0,7.5)[0],q0,exact(nsites+1,7.5)[0]]
    dd_rhs=np.exp(eq_qq[:-2]-eq_qq[1:-1])-np.exp(eq_qq[1:-1]-eq_qq[2:])
    residual=float(np.max(abs(dd_rhs-dd0)))
    # separate less-accurate solver for convergence and verification
    r2=solve_ivp(rhs,(0,t_end),init,t_eval=checkpoints,method='RK45',rtol=1e-8,atol=1e-10)
    assert r2.success
    cross=float(np.max(abs(r.y[:,-1]-r2.y[:,-1])))
    ret={'method':'DOP853','sites':nsites,'t_end':t_end,'kappa':.4,'soliton_speed':float(np.sinh(.4)/.4),'analytic_equations_residual':residual,'max_absolute_displacement_or_momentum_error':float(max(e)),'max_absolute_strain_error':float(max(strain)),'DOP853_vs_RK45_terminal_state_max_abs_difference':cross,'function_evaluations_dop853':int(r.nfev),'function_evaluations_rk45':int(r2.nfev),'boundary_conditions':'exact infinite-lattice soliton sampled at finite lattice endpoints'}
    (Path(__file__).parent/'toda_validation.json').write_text(json.dumps(ret,indent=2))
    return ret
if __name__=='__main__':
    print(json.dumps(run(),indent=2))
