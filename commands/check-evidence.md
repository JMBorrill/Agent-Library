---
description: Audit documents for valid citations, real framework identifiers, adequate evidence and no over-claiming.
argument-hint: "<document paths...>"
---
Act as the `evidence-auditor` subagent on: $ARGUMENTS

Run `python -m agentlib evidence check $ARGUMENTS --require-citations`, apply any framework-specific validators that
match the documents, spot-check at least five citations against the pinned PDFs, and report findings with a verdict
(Pass / Pass with corrections / Fail).
