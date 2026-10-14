from pathlib import Path
import csv, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
P=Path(__file__).parent
with (P/'floquet_scan.csv').open() as f:rows=list(csv.DictReader(f))
fig,ax=plt.subplots(figsize=(9,5),layout='constrained')
for m in [4,8]:
    r=[x for x in rows if int(x['modes'])==m]
    ax.plot([float(x['F']) for x in r],[float(x['max_multiplier_modulus']) for x in r],label=f'{m} modes')
ax.axhline(1,linestyle='--',alpha=.6,label='Stability boundary: |μ| = 1')
ref=json.loads((P/'floquet_refined.json').read_text())
for m in [4,8]:
    q=[x for x in ref if x['modes']==m and x['steps_per_period']==720][0]
    F=q['critical_F']
    ax.scatter([F],[1],s=38,zorder=3)
    ax.annotate(f'{m} modes: F={F:.7f}',(F,1),xytext=(F+.00017,1.002 if m==4 else .988),fontsize=9)
ax.set(xlabel='Driving amplitude F', ylabel='Largest Floquet multiplier magnitude',title='Driven α-FPUT phase-locked orbit: linear stability versus drive amplitude')
ax.set_ylim(.968,1.028);ax.legend(loc='lower right');ax.grid(alpha=.2)
fig.savefig(P/'floquet_crossing.png',dpi=180);plt.close(fig)

bs=json.loads((P/'basin_check.json').read_text())
fig,ax=plt.subplots(figsize=(9,4.5),layout='constrained')
xs=np.arange(len(bs));vals=[b['mode1_last750_range'] for b in bs]
ax.bar(xs,vals)
ax.set_xticks(xs,[b['initial_state'].replace('_',' ') for b in bs]);ax.set(ylabel='Mode-1 energy range over final 750 drive periods (log scale)',title='Basin dependence at N=8, F=0.0045')
ax.set_yscale('log')
ax.grid(axis='y',alpha=.2)
fig.savefig(P/'bistability_pilot.png',dpi=180);plt.close(fig)
