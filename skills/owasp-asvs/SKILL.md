---
name: owasp-asvs
description: >-
  Application security verification and security requirements definition with the OWASP Application
  Security Verification Standard (ASVS) 5.0.0: scoping and level selection, building a verification
  plan/checklist, performing and structuring verification with evidence, mapping security findings to
  ASVS requirements, checking a filled assessment and writing the verification report. Deterministic
  tools generate level-filtered checklists, validate assessments (unknown ids, missing requirements,
  fail without finding, N/A without justification) and compute per-chapter compliance. Use when asked
  to verify, assess, pentest-scope or report on a web application or API against ASVS, to map pentest
  or scanner findings to ASVS, or to define security requirements for a new application or feature.
license: Skill text MIT; ASVS content CC BY-SA 4.0 (The OWASP Foundation)
metadata:
  version: 1.0.0
  category: security
  maturity: beta
  sources: [owasp-asvs]
  catalogs: [owasp-asvs-5]
  tools:
    - "python -m agentlib asvs chapters"
    - "python -m agentlib asvs show"
    - "python -m agentlib asvs search"
    - "python -m agentlib asvs checklist"
    - "python -m agentlib asvs check-assessment"
    - "python -m agentlib asvs map-findings"
---

# OWASP ASVS 5.0.0 - application security verification

ASVS 5.0.0 is a list of 345 verifiable application security requirements in 17 chapters (V1-V17),
each assigned Level 1, 2 or 3. This skill turns it into a repeatable verification engagement or a
security requirements specification. All requirement text, levels and pages come from
`catalog/owasp-asvs-5.json`; never quote a requirement or level from memory - run the tools.

## When to use

- **Verification / assessment**: "Assess our app against ASVS L2", "what does an ASVS audit need",
  "build a test plan", "is this assessment complete", "write the verification report".
- **Finding triage**: map pentest, SAST/DAST or bug-bounty findings to ASVS requirements.
- **Design-time requirements**: derive a security requirements spec for a new system or feature
  (the standard explicitly supports use as architecture guidance and a secure coding reference,
  PDF pp. 17-18).
- **Procurement**: express "must meet ASVS level X" and the evidence a supplier must provide (PDF p. 18).

Not for: process-level secure development (use an SSDF skill), mobile/IoT specifics (out of ASVS
scope), or legal certification - OWASP does not certify vendors, verifiers or software (PDF p. 19).

## Key facts (verified in the PDF)

- Identifier format `<chapter>.<section>.<requirement>`, e.g. `1.2.5`; in reports prefer the
  version-qualified form `v5.0.0-1.2.5` (lowercase v) because ids change between versions (PDF pp. 16-17).
  Chapters/sections are written `V1`, `V1.2`. ASVS 4.x ids do **not** carry over (PDF p. 21).
- Levels are cumulative: a level requires its own and all lower-level requirements; higher-level
  requirements are recommendations (PDF p. 13); L2 = all L1 + L2 (~70% of ASVS, PDF p. 14).
  5.0.0 has 70 L1 of 345 requirements (PDF p. 23); the catalog confirms 70 / 183 / 92 (L1/L2/L3).
- The organisation chooses its level from its risk, data sensitivity and user expectations; ASVS does
  not prescribe it (PDF p. 15). Detail: [references/levels-and-scoping.md](references/levels-and-scoping.md).
- Each requirement's verification ends in pass or fail (PDF p. 11). Documentation requirements (the
  `Vn.1 ... Documentation` sections) are verified separately from their implementation (PDF p. 12).

## Workflow

### 1. Scope and select the level
1. Record the application boundary: components, interfaces (browser UI, APIs, GraphQL, WebSocket,
   WebRTC), identity model (local auth, IdP, OAuth/OIDC roles), data sensitivity. WAFs, load
   balancers and proxies may count as part of the application for relevant controls (PDF p. 11).
2. Choose the target level with the organisation using
   [references/levels-and-scoping.md](references/levels-and-scoping.md); record the rationale.
3. Decide chapter applicability with [references/chapter-guide.md](references/chapter-guide.md).
   Exclude a chapter only when its triggering technology is absent (e.g. V3 for a machine-to-machine
   API, V10 without OAuth, V17 without WebRTC; PDF p. 15). Record every exclusion with a reason - the
   report must state what was included and give an opinion on exclusions (PDF p. 19).

### 2. Build the verification plan
```sh
python -m agentlib asvs chapters --sections                     # orientation, counts per level
python -m agentlib asvs checklist --level 2 --chapters V1 V2 V4 V6 V7 V8 V9 V11 V12 V13 V14 V15 V16 \
    --format csv -o asvs-l2-checklist.csv                        # md | csv | yaml | json
```
Fill [templates/verification-plan.md](templates/verification-plan.md): scope, level, excluded
chapters with rationale, verification methods per chapter, evidence expectations, access needed
(documentation, source, configuration, people - especially for L2/L3, PDF p. 20), schedule.
Method selection: [references/verification-methods.md](references/verification-methods.md).

### 3. Perform and record verification
For each in-scope requirement record **status** (`pass`, `fail`, `not-applicable`,
`not-verified`), **evidence** (artefact, commit/version, date, method) and, for a fail, a
**finding reference**; for N/A, a **justification**. Use `asvs show <id>` to read the exact
requirement before judging it; note level-specific clauses inside the text (e.g. "for L2 and up").
Verify documentation requirements against the document, then the paired implementation
requirement against the system. A tool run alone is not verification (PDF p. 20).
Write each failure as a finding with [templates/finding-record.md](templates/finding-record.md).

### 4. Map findings (when starting from a pentest/scanner report)
```sh
python -m agentlib asvs map-findings findings.json --top 5      # JSON/YAML/CSV: title, description, cwe
```
Candidates are **suggestions** from a keyword index (requirement text, section and chapter titles,
optional library-authored CWE hints - ASVS 5.0 itself has no CWE mapping, PDF p. 23). Read each
candidate with `asvs show` and record only the ones you confirm. See
[references/finding-mapping.md](references/finding-mapping.md).

### 5. Check the assessment
```sh
python -m agentlib asvs check-assessment assessment.yaml --level 2 --chapters V1 V2 ... [--strict]
```
Fix every error (unknown ids, missing in-scope requirements, invalid status, fail without finding,
N/A without justification). Exit code 1 = invalid or incomplete (any `not-verified` or missing);
`--strict` also fails on any `fail`. Compliance % = pass / (in-scope - N/A).

### 6. Report
Use [templates/verification-report.md](templates/verification-report.md) and
[references/reporting.md](references/reporting.md). An ASVS report lists scope, a summary of **all**
requirements checked (not only exceptions), the exceptions and remediation guidance, and notes
non-applicable requirements (PDF p. 19). Paste the `check-assessment` output as an annex.

### Design-time: security requirements specification
1. Choose a target level and applicable chapters (steps 1.1-1.3).
2. `asvs checklist --level N --chapters ... --format md` gives the requirement baseline.
3. Write the `Vn.1` documentation decisions first (they parameterise implementation requirements),
   then allocate requirements to components and acceptance tests using
   [templates/security-requirements-spec.md](templates/security-requirements-spec.md) and
   [references/requirements-definition.md](references/requirements-definition.md).

## Decision rules

- Unknown or unverified id -> do not use it; `asvs show` must succeed for every cited id.
- A requirement above the target level is a recommendation; report it separately, never count it.
- `not-applicable` only when the triggering feature is absent; "too hard" or "accepted risk" is a
  `fail` with a finding and a risk-acceptance note.
- `not-verified` is not a pass; a report with any not-verified item is incomplete.
- Never state that an application is "certified" or "ASVS compliant" as fact; say "verification
  found all N in-scope Level X requirements passed, within the stated scope and method".

## Outputs

- Verification plan (template), level-filtered checklist (md/csv/yaml/json).
- Filled assessment (YAML/JSON/CSV) that passes `check-assessment`.
- Finding records mapped to v5.0.0 requirement ids.
- Verification report with per-chapter results, compliance %, failures and exclusions.
- For design work: security requirements specification with traceability to ASVS ids.

## Quality checklist

- [ ] Level and every chapter exclusion recorded with a rationale.
- [ ] Every in-scope requirement has a status; no `not-verified` remains in a final report.
- [ ] Every fail has a finding id; every N/A has a justification.
- [ ] Every cited id exists in 5.0.0 and carries the right level (`asvs show`).
- [ ] Methods disclosed and evidence repeatable; tool output not presented as verification on its own.
- [ ] Citations in library format, e.g. `[owasp-asvs V6.2.1, p. 46]`; version-qualified ids in reports.
- [ ] CC BY-SA attribution included where requirement text is reproduced.

## Sources

`owasp-asvs` - OWASP Application Security Verification Standard 5.0.0 (May 2025), The OWASP
Foundation, CC BY-SA 4.0 (pinned PDF `sources/pdfs/owasp-asvs-5-0-0-en.pdf`, 123 pages; printed page
= PDF page - 1). Pages relied on (PDF): scope and definitions pp. 10-12; levels pp. 13-15; structure
and referencing pp. 15-17; use cases pp. 17-18; assessment, reporting and verification mechanisms
pp. 19-20; changes from 4.x and level counts pp. 21-24; requirement chapters V1-V17 pp. 24-96
(per-chapter pages in [references/chapter-guide.md](references/chapter-guide.md)).

## Limitations

- Output supports, but does not replace, qualified professional judgement, a qualified security
  verifier, or formal assurance/approval; OWASP does not certify and no tool output is a certification.
- The catalog reproduces requirement statements only; chapter introductions, notes under tables and
  Appendix C (cryptography standards) must be read in the PDF when relevant.
- `map-findings` is a lexical heuristic: it can miss or mis-rank requirements; confirm every mapping.
- ASVS covers the application, not CI/CD, hosting or operations (PDF p. 11); pair with process
  frameworks (e.g. SSDF) for those.
