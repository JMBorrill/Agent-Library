"""Deterministic numerical tests; run python -m unittest discover -s Nonlinear_Waves_Stage2 -p test_stage2.py -v."""
import unittest,json
from pathlib import Path
import numpy as np
from scipy.special import expit
from floquet import periodic_orbit,orbit_one_period,tangent_rhs
from toda_benchmark import exact,run as run_toda
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Nonlinear_Waves_Stage1'))
from stage1 import matrices

class Stage2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phi,cls.d,cls.w,cls.c,cls.g=matrices(8)
    def test_variational_matrix_matches_directional_finite_difference(self):
        w=self.w[:4];c=np.ascontiguousarray(self.c[:4,:4,:4]);g=self.g[:4]
        rng=np.random.default_rng(47)
        y=rng.uniform(-.1,.1,8);u=rng.standard_normal(8);u/=np.linalg.norm(u)
        _,M=orbit_one_period(y,w,c,g,.25,.0025,.0045,.347,200)
        eps=1e-6
        plus,_=orbit_one_period(y+eps*u,w,c,g,.25,.0025,.0045,.347,200)
        minus,_=orbit_one_period(y-eps*u,w,c,g,.25,.0025,.0045,.347,200)
        self.assertLess(np.max(abs((plus-minus)/(2*eps)-M@u)),3e-6)
    def test_floquet_determinant_matches_divergence(self):
        w=self.w[:8];c=np.ascontiguousarray(self.c);g=self.g
        y=np.zeros(16)
        _,M=orbit_one_period(y,w,c,g,.25,.0025,.0045,.347,720)
        predicted=np.exp(-8*.0025*2*np.pi/.347)
        self.assertLess(abs(np.linalg.det(M)-predicted),2e-6)
    def test_near_threshold_modulus_order(self):
        detailed=json.loads((Path(__file__).parent/'floquet_detailed.json').read_text())
        seed=np.asarray(detailed['8_0.0045']['fixed_point'])
        vals=[]
        for F in (.0045,.0050):
            r,M, eig,res=periodic_orbit(seed,self.w,np.ascontiguousarray(self.c),self.g,F,360)
            self.assertLess(res,1e-8)
            vals.append(max(abs(eig)))
        self.assertLess(vals[0],1.)
        self.assertGreater(vals[1],1.)
    def test_exact_toda_force(self):
        n=np.arange(2,100);t=12.
        q,p,dd=exact(n,t)
        qq,_,_=exact(np.arange(1,101),t)
        rhs=np.exp(qq[:-2]-qq[1:-1])-np.exp(qq[1:-1]-qq[2:])
        self.assertLess(max(abs(rhs-dd)),1e-12)

if __name__=='__main__':unittest.main()
