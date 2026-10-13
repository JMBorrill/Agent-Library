---
description: Recommend which frameworks, skills, subagents and workflow apply to a problem and record the selection.
argument-hint: "<problem description>"
---
Load the `framework-selector` skill (`skills/framework-selector/SKILL.md`).

Problem: $ARGUMENTS

Run `python -m agentlib route "$ARGUMENTS"`, apply the routing table and the five characterisation questions,
then produce a framework selection record using `templates/framework-selection-record.md`. Distinguish mandatory
from advisory frameworks and state what you could not determine.
