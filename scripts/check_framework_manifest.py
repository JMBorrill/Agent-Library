#!/usr/bin/env python3
"""Validate manifests for internal consistency; NOT source or domain correctness."""
from pathlib import Path
import json,sys,re
ROOT=Path(__file__).resolve().parents[1]
issues=[]
def load(relative):
    try:return json.loads((ROOT/relative).read_text(encoding='utf-8'))
    except Exception as e:issues.append(f'{relative}: {e}'); return []
sources=load('sources/registry.json'); plan=load('sources/framework-build-plan.json'); nasa=load('sources/nasa-17-processes.json')
source_ids=[s.get('id') for s in sources]
if len(source_ids)!=len(set(source_ids)):issues.append('Duplicate source ID')
planned=[p.get('source_id') for p in plan]
if len(planned)!=len(set(planned)): issues.append('Duplicate framework plan source ID')
if set(planned)!=set(source_ids):issues.append(f'Plan/source ID mismatch. Plan missing: {set(source_ids)-set(planned)}; Registry missing: {set(planned)-set(source_ids)}')
for s in sources:
    if not str(s.get('url','')).startswith('https://'):issues.append('Invalid source URL: '+str(s.get('id')))
proc=nasa.get('processes',[]) if isinstance(nasa,dict) else []
if len(proc)!=17:issues.append('NASA map must have 17 processes, found '+str(len(proc)))
if len({p.get('id') for p in proc})!=17:issues.append('NASA process ID collision')
for i,p in enumerate(proc,1):
    if p.get('id')!=f'SE-{i:02}':issues.append('Nonconsecutive NASA process ID '+str(p.get('id')))
    if p.get('source_id') not in source_ids:issues.append('Unknown source in NASA map '+str(p))
    if not p.get('proposed_skill_ids'):issues.append('Missing skills for NASA process '+str(p.get('id')))
    for sk in p.get('proposed_skill_ids',[]):
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',sk): issues.append('Invalid proposed skill name '+str(sk))
if issues:
    print('\n'.join('FAIL: '+error for error in issues)); sys.exit(1)
print(f'PASS: {len(source_ids)} source URLs and framework plan entries; {len(proc)} preliminary NASA process mappings; metadata integrity only.')
