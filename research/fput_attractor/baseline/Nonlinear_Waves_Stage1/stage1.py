"""Reproducible Stage 1: modal Galerkin reduction of a driven damped alpha-FPUT chain.

Reference model: Y. Shi and H. Ren, Phys. Rev. E 113, 034221 (2026),
DOI 10.1103/mbbf-ll5l, Eq. (1), N=8, alpha=.25, eta=.0025,
F=.005, Omega=.347, fixed boundaries and zero initial conditions.

No result from this code is claimed to be novel.
"""
from pathlib import Path
import argparse, csv, json
import numpy as np
from numba import njit
from scipy.integrate import solve_ivp
from scipy.signal import periodogram


def matrices(n):
    x=np.arange(1,n+1)[:,None]; k=np.arange(1,n+1)[None,:]
    phi=np.sqrt(2/(n+1))*np.sin(np.pi*x*k/(n+1))
    d=np.diff(np.concatenate((np.zeros((1,n)),phi,np.zeros((1,n)))), axis=0)
    w=2*np.sin(np.pi*np.arange(1,n+1)/(2*(n+1)))
    c=np.einsum('bi,bj,bk->ijk',d,d,d)
    g=phi.sum(axis=0)
    return phi,d,w,c,g


@njit(cache=True)
def dynamics(t,y,w,c,g,alpha,eta,F,Omega):
    m=len(w); out=np.empty(2*m)
    for k in range(m):
        acc=-w[k]*w[k]*y[k]-eta*y[m+k]+F*g[k]*np.cos(Omega*t)
        for i in range(m):
            for j in range(m):
                acc-=alpha*c[k,i,j]*y[i]*y[j]
        out[k]=y[m+k]
        out[m+k]=acc
    return out


@njit(cache=True)
def rk4(w,c,g,alpha,eta,F,Omega,periods,steps):
    m=len(w); y=np.zeros(2*m); data=np.empty((periods,2*m))
    period=2*np.pi/Omega; h=period/steps; t=0.
    for p in range(periods):
        for _ in range(steps):
            k1=dynamics(t,y,w,c,g,alpha,eta,F,Omega)
            k2=dynamics(t+h/2,y+h*k1/2,w,c,g,alpha,eta,F,Omega)
            k3=dynamics(t+h/2,y+h*k2/2,w,c,g,alpha,eta,F,Omega)
            k4=dynamics(t+h,y+h*k3,w,c,g,alpha,eta,F,Omega)
            y+=(h/6)*(k1+2*k2+2*k3+k4)
            t+=h
        data[p]=y
    return data


def energies(data,w):
    m=len(w)
    return .5*(data[:,m:]**2+(data[:,:m]*w)**2)


def measurements(data,w,last):
    E=energies(data,w); s=E[-last:]; e=s[:,0]
    fr,pow=periodogram(e-e.mean(),detrend=False)
    ix=1+np.argmax(pow[1:]); freq=float(fr[ix]);
    return {'mode1_mean':float(s[:,0].mean()),'mode1_range':float(np.ptp(s[:,0])),
            'mode2_mean':float(s[:,1].mean()),'mode2_range':float(np.ptp(s[:,1])),
            'mode3_mean':float(s[:,2].mean()) if s.shape[1]>2 else None,
            'mode1_dominant_modulation_period_drive_cycles':float(1/freq),
            'mode1_modulation_peak_power':float(pow[ix]),
            'mode1_modulation_peak_fraction':float(pow[ix]/pow[1:].sum())}


def run(periods=2500,steps=200,last=500,output=None,do_dop=True):
    n=8; alpha=.25; eta=.0025; F=.005; Omega=.347
    phi,d,w,c,g=matrices(n); cfg={'n':n,'alpha':alpha,'eta':eta,'F':F,'Omega':Omega,'periods':periods,'steps_per_period':steps,'window_periods':last}
    assert np.allclose(np.einsum('bi,bj->ij',d,d),np.diag(w*w),atol=1e-13)
    assert abs(g[1])<1e-12 and abs(c[0,0,1])>1e-4
    rows=[]; traces={}
    for m in [2,3,4,8]:
        z=rk4(w[:m],np.ascontiguousarray(c[:m,:m,:m]),g[:m],alpha,eta,F,Omega,periods,steps)
        info=measurements(z,w[:m],last)
        rows.append({'modes':m,'solver':f'RK4/{steps}',**info})
        traces[m]=energies(z,w[:m])[-last:,:2]
    if do_dop:
        def f(t,y):return dynamics(t,y,w,c,g,alpha,eta,F,Omega)
        T=2*np.pi/Omega
        tt=np.arange(periods-last+1,periods+1)*T
        sol=solve_ivp(f,(0,periods*T),np.zeros(2*n),method='DOP853',rtol=1e-10,atol=1e-12,t_eval=tt)
        assert sol.success, sol.message
        z=sol.y.T
        info=measurements(z,w,last)
        rows.append({'modes':8,'solver':'DOP853,rtol1e-10',**info})
        traces['dop853']=energies(z,w)[:,:2]
    if output:
        output=Path(output);output.mkdir(exist_ok=True,parents=True)
        with (output/'modal_summary.csv').open('w',newline='') as f:
            wr=csv.DictWriter(f,fieldnames=rows[0].keys());wr.writeheader();wr.writerows(rows)
        with (output/'energy_traces.csv').open('w',newline='') as f:
            wr=csv.writer(f);wr.writerow(['window_drive_period','model','E1','E2'])
            for m,E in traces.items():
                for i,(e1,e2) in enumerate(E):wr.writerow([periods-last+i+1,str(m),float(e1),float(e2)])
        with (output/'configuration.json').open('w') as f:json.dump(cfg,f,indent=2)
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,axs=plt.subplots(2,1,sharex=True,figsize=(10,7),constrained_layout=True)
        x=np.arange(periods-last+1,periods+1)
        for m in [2,3,4,8]:
            axs[0].plot(x,traces[m][:,0],label=f'{m}-mode',alpha=.8,lw=1)
            axs[1].plot(x,traces[m][:,1],label=f'{m}-mode',alpha=.8,lw=1)
        axs[0].set_ylabel('Linear mode-1 energy')
        axs[1].set_ylabel('Linear mode-2 energy')
        axs[1].set_xlabel('Driving periods')
        axs[0].legend(ncol=4)
        fig.suptitle('Driven alpha-FPUT: no-fitted-parameters Galerkin truncation, N=8')
        fig.savefig(output/'modal_comparison.png',dpi=160)
        plt.close(fig)
    return cfg,rows


def test_matrices_and_rhs():
    n=8;phi,d,w,c,g=matrices(n)
    assert np.max(abs(phi.T@phi-np.eye(n))) < 1e-13
    assert np.max(abs(c-np.transpose(c,(1,0,2))))<1e-13
    assert abs(g[1])<1e-12
    # Ensure modal full-order acceleration agrees with physical-force equation.
    rng=np.random.default_rng(42)
    q=rng.uniform(-.3,.3,n);p=rng.uniform(-.2,.2,n)
    y=np.r_[phi.T@q,phi.T@p]
    acc_modal=dynamics(.132,y,w,c,g,.25,.0025,.005,.347)[n:]
    qb=np.r_[0,q,0];left=qb[1:-1]-qb[:-2];right=qb[2:]-qb[1:-1]
    acc_phys=right-left+.25*(right*right-left*left)-.0025*p+.005*np.cos(.347*.132)
    assert np.max(abs(acc_modal-phi.T@acc_phys))<1e-12
    # Conservative FPUT Hamiltonian energy conservation with nonzero initial state.
    def energy(y):
        qq=phi@y[:n];pp=phi@y[n:];r=np.diff(np.r_[0,qq,0]);return .5*np.dot(pp,pp)+np.sum(.5*r*r+.25/3*r**3)
    # Cannot use zero initial condition for conservative check: it is stationary.
    yinit=np.zeros(2*n); yinit[0]=.6
    sol=solve_ivp(lambda t,y:dynamics(t,y,w,c,g,.25,0,0,.347),(0,300),yinit,method='DOP853',rtol=1e-11,atol=1e-13,t_eval=np.linspace(0,300,500))
    H=np.array([energy(v) for v in sol.y.T]);assert np.ptp(H)/np.mean(H)<2e-9, np.ptp(H)/np.mean(H)
    return float(np.ptp(H)/np.mean(H))


if __name__=='__main__':
    pa=argparse.ArgumentParser();pa.add_argument('--periods',type=int,default=2500);pa.add_argument('--steps',type=int,default=200);pa.add_argument('--window',type=int,default=500);pa.add_argument('--full-dop',action='store_true',help='Run expensive 2500-period independent adaptive solver; use dop_check.py for quick validation');pa.add_argument('--output',default='results')
    a=pa.parse_args()
    drift=test_matrices_and_rhs(); print('Internal tests passed. Conservative FPUT test relative energy drift:',drift)
    cfg,rows=run(a.periods,a.steps,a.window,a.output,a.full_dop)
    for r in rows:print(r)
