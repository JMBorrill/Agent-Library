# Acceptance and quality gates

## Coverage statuses (must not be conflated)
- `unresearched`: URL known but relevant source content not checked.
- `researched`: authoritative version and exact applicable sections checked; notes with source pointers exist.
- `mapped`: actual verified source sections mapped to skill(s), agent routing and artifacts.
- `implemented`: skill and templates/scripts work on at least one realistic example.
- `tested`: unit checks, negative fixtures and a documented workflow execution pass locally.
- `human_review_pending`: needs domain expert validation of substantive reasoning or high-stakes gate.
- `blocked`: access rights, source unavailable or content insufficient to implement accurately.

## Gate 1: SOURCE integrity
A skill with `researched` must cite a source ID, full URL, edition/effective date where known, actual section references, and licensing/redistribution note. URLs alone do not count as verified knowledge. A published framework must not silently be labelled mandatory in contexts where it is advisory.

## Gate 2: SKILL actionability
A skill states when to invoke it and NOT invoke it, concrete input contract, procedural method, output schema/template, worked example, negative or adversarial case, escalation rules and a validator/test where mechanical checking is possible. Avoid roleplay or vague commands such as 'ensure best practice'.

## Gate 3: AGENT separation
Agent has narrow permissions, clearly assigned skills, handoff contract and defined human sign-off. Reviewer cannot approve its own author's artifact; use distinct instance/role and actual evidence.

## Gate 4: TEST evidence
Unit tests check invariants and reproducibility; negative tests demonstrate error detection. For NASA: identifiers, parent links, traceability, test references, acceptance checks and risk change impact. For finance: numerically proven scenarios, zero/negative denominator handling. For code: at least one security or build check. For AI: malicious prompt/tool-use example with expected deny or escalation; don't expose real secrets.

## Gate 5: REAL use case
Do at least three synthetic projects: ASTER-01, mortgage criteria decision support and AI business scheduling CRM. Outputs must state assumptions, source links, pass/fail evidence and human review gates; not claim qualification, compliance or production readiness.

## Gate 6: SAFE distribution
Installer is opt-in, defaults to dry-run, avoids overwrite or network access by default; never pushes to GitHub or deploys production without explicit authorisation.

## Gate 7: Honest reporting
Report tested/unverified separately; no estimated coverage disguised as measured coverage. If source access fails, continue elsewhere and flag its status. Commit and issue list are optional only where authorised.
