"""Driven FPUT periodic-orbit continuation and variational Floquet spectrum.
Independent verification required before physical/bifurcation claims.
Reference Shi & Ren PRE 113 034221 (2026) doi:10.1103/mbbf-ll5l.
"""
import os,sys,csv,json
from pathlib import Path
import numpy as np
from scipy.optimize import root
from scipy.integrate import solve_ivp
from numba import njit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Nonlinear_Waves_Stage1'))
from stage1 import matrices,dynamics

@njit(cache=True)
def tangent_rhs(t,z,w,c,g,alpha,eta,F,Omega):
    m=len(w);dim=2*m; out=np.zeros(dim+dim*dim)
    Q=z[:m];V=z[m:dim]
    for k in range(m):
        a= -w[k]*w[k]*Q[k]-eta*V[k]+F*g[k]*np.cos(Omega*t)
        for i in range(m):
            for j in range(m):
                a -= alpha*c[k,i,j]*Q[i]*Q[j]
        out[k]=V[k];out[m+k]=a
    # M is flattened row-major, dM = J M
    for k in range(m):
        for col in range(dim):
            out[dim+k*dim+col]=z[dim+(m+k)*dim+col]
            dd=-w[k]*w[k]*z[dim+k*dim+col]-eta*z[dim+(m+k)*dim+col]
            for i in range(m):
                coeff=0.
                for j in range(m): coeff+=c[k,i,j]*Q[j]
                dd-=2*alpha*coeff*z[dim+i*dim+col]
            out[dim+(m+k)*dim+col]=dd
    return out

@njit(cache=True)
def orbit_one_period(y,w,c,g,alpha,eta,F,Omega,steps):
    dim=len(y);T=2*np.pi/Omega; h=T/steps
    z=np.zeros(dim+dim*dim);z[:dim]=y
    for j in range(dim): z[dim+j*dim+j]=1.
    t=0.
    for j in range(steps):
        k1=tangent_rhs(t,z,w,c,g,alpha,eta,F,Omega)
        k2=tangent_rhs(t+h/2,z+h*k1/2,w,c,g,alpha,eta,F,Omega)
        k3=tangent_rhs(t+h/2,z+h*k2/2,w,c,g,alpha,eta,F,Omega)
        k4=tangent_rhs(t+h,z+h*k3,w,c,g,alpha,eta,F,Omega)
        z+=(h/6)*(k1+2*k2+2*k3+k4)
        t+=h
    return z[:dim],z[dim:].reshape((dim,dim))


def periodic_orbit(y0, w,c,g,F, steps,alpha=.25,eta=.0025,Omega=.347):
    def f(y):
        yp,M=orbit_one_period(y,w,c,g,alpha,eta,F,Omega,steps)
        return yp-y, M-np.eye(len(y))
    r=root(f,y0,jac=True,method='hybr',options={'xtol':1e-11,'maxfev':150})
    yp,M=orbit_one_period(r.x,w,c,g,alpha,eta,F,Omega,steps)
    res=np.max(np.abs(yp-r.x));v=np.linalg.eigvals(M)
    return r, M, v, res

def independently_check_one_period(y,w,c,g,F,steps,alpha=.25,eta=.0025,Omega=.347):
    T=2*np.pi/Omega; n=len(w);dim=2*n
    z=np.r_[y,np.eye(dim).reshape(-1)]
    sol=solve_ivp(lambda t,z:tangent_rhs(t,z,w,c,g,alpha,eta,F,Omega), (0,T),z,method='DOP853',rtol=2e-11,atol=2e-13)
    zr=sol.y[:,-1]
    za,ma=orbit_one_period(y,w,c,g,alpha,eta,F,Omega,steps)
    return {'independent_solver_success':bool(sol.success),'state_difference_RK4_vs_DOP853':float(np.max(abs(za-zr[:dim]))),'monodromy_difference_RK4_vs_DOP853':float(np.max(abs(ma-zr[dim:].reshape((dim,dim))))),'nfev':sol.nfev}

def run(steps=180):
    path=Path(__file__).resolve().parent
    rows=[]; detailed={}; verify={}
    for m in (4,8):
        phi,d,w0,c0,g0=matrices(8)
        w=w0[:m];c=np.ascontiguousarray(c0[:m,:m,:m]);g=g0[:m]
        y=np.zeros(2*m)
        # small continuation steps, follow one synchronized branch from F=0
        fs=np.arange(0,0.00651,0.0001)
        for F in fs:
            r,M,v,res=periodic_orbit(y,w,c,g,float(F),steps)
            eigmax=np.max(abs(v)); eig_near=v[np.argmax(abs(v))]
            if res<1e-8: y=r.x.copy()
            rows.append({'modes':m,'F':round(float(F),7),'root_success':bool(r.success),'fixed_point_residual':float(res),'max_multiplier_modulus':float(eigmax),'leading_multiplier_real':float(eig_near.real),'leading_multiplier_imag':float(eig_near.imag),'fixed_point_q_norm':float(np.linalg.norm(r.x[:m]))})
            if res>1e-8:
                print('Unconverged branch',m,F,res,r.message,flush=True)
                break
            if any(abs(F-f)<0.00005001 for f in (.003,.004,.0045,.005,.0055,.006)):
                detailed[f'{m}_{F:.4f}']={'multipliers':[[float(e.real),float(e.imag)] for e in v],'fixed_point':y.tolist(),'residual':float(res)}
                print(f'm={m}, F={F:.4f}, max |mu|={eigmax:.9f}, leading={eig_near:.7f}, residual={res:.1e}',flush=True)
        verify[str(m)]=independently_check_one_period(y,w,c,g, F=0.006,steps=steps)
    with (path/'floquet_scan.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (path/'floquet_detailed.json').write_text(json.dumps(detailed,indent=2))
    (path/'solver_crosscheck.json').write_text(json.dumps(verify,indent=2))
    print('solver cross check',verify,flush=True)
    return rows

if __name__=='__main__':
    run()
