#!/usr/bin/env python3
"""Small no-dependency sanity check for Agent Skills frontmatter and starter traceability."""
from pathlib import Path
import csv, json, re, sys
ROOT=Path(__file__).resolve().parents[1]
errors=[]
sources=json.loads((ROOT/'sources/registry.json').read_text())
ids={s['id'] for s in sources}
for skill in (ROOT/'.claude/skills').glob('*/SKILL.md'):
    raw=skill.read_text()
    if not raw.startswith('---\n') or raw.count('---')<2:
        errors.append(f'{skill}: missing YAML frontmatter')
        continue
    fm=raw.split('---',2)[1]
    fields={}
    for line in fm.splitlines():
        if ':' in line:
            k,v=line.split(':',1); fields[k.strip()]=v.strip()
    name=fields.get('name','')
    if name!=skill.parent.name or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',name):
        errors.append(f'{skill}: invalid name')
    if not fields.get('description') or len(fields['description'])>1024:
        errors.append(f'{skill}: invalid description')
    match=re.search(r'Source ID: `([^`]+)`',raw)
    if not match or match.group(1) not in ids:
        errors.append(f'{skill}: unknown source ID')
for agent in (ROOT/'.claude/agents').glob('*.md'):
    raw=agent.read_text()
    if not raw.startswith('---\n') or f'name: {agent.stem}\n' not in raw:
        errors.append(f'{agent}: invalid frontmatter/name')
requirements=list(csv.DictReader((ROOT/'examples/aster-01/requirements.csv').open()))
test_ids=set()
for r in requirements:
    if r['id'] in test_ids: errors.append(f"Duplicate requirement: {r['id']}")
    test_ids.add(r['id'])
    if not r.get('verification_id') or not r.get('acceptance_criteria'):
        errors.append(f"Requirement incomplete: {r['id']}")
if errors:
    print('\n'.join('ERROR: '+s for s in errors));sys.exit(1)
print(f'PASS: {len(list((ROOT/".claude/skills").glob("*/SKILL.md")))} skills; {len(list((ROOT/".claude/agents").glob("*.md")))} agents; {len(requirements)} example requirements; {len(ids)} sources.')
