# Secure software delivery review (SSDF + ASVS)

Combines a NIST SSDF process gap assessment of how software is built with an OWASP ASVS verification of the application itself, then audits the evidence and produces a release-readiness recommendation.

Workflow `secure-software-delivery` v1.0.0. Sources: nist-ssdf, owasp-asvs.

## Inputs

- `system-description` (required): Application purpose, architecture, data sensitivity, exposure and users.
- `pipeline-description` (required): YAML description of the CI/CD pipeline and development controls.
- `codebase` (required): Repository path or URL and commit under review.

## Stages

### 1. Security scope and ASVS level selection (`scope`)

- Agent: `application-security-verifier`; skills: `owasp-asvs`
- Consumes: system-description
- Produces: asvs-verification-plan
- Tools: `python -m agentlib asvs checklist --level <n>`
- Gate (human):
  - [ ] ASVS level chosen with documented rationale (data sensitivity, exposure, consequences).
  - [ ] In-scope chapters and exclusions are justified.

### 2. SSDF process gap assessment (`process`)

- Agent: `secure-development-reviewer`; skills: `nist-ssdf`
- Consumes: pipeline-description, codebase
- Produces: ssdf-assessment, ssdf-pipeline-map
- Tools: `python -m agentlib ssdf map-pipeline <file>`; `python -m agentlib ssdf check-assessment <file>`
- Gate (automated):
  - [ ] Every SSDF task has a status; implemented tasks cite evidence.
  - Check: `python -m agentlib ssdf check-assessment <ssdf-assessment>`

### 3. ASVS verification (`verify`)

- Agent: `application-security-verifier`; skills: `owasp-asvs`
- Consumes: asvs-verification-plan, codebase
- Produces: asvs-assessment, asvs-verification-report
- Tools: `python -m agentlib asvs check-assessment <file> --level <n>`
- Gate (automated):
  - [ ] Every in-scope requirement has a result; failures reference findings.
  - Check: `python -m agentlib asvs check-assessment <asvs-assessment> --level <n>`

### 4. Independent evidence audit (`evidence-audit`)

- Agent: `evidence-auditor`; skills: `evidence-and-citation`
- Consumes: ssdf-assessment, asvs-verification-report
- Produces: evidence-audit-report
- Gate (agent-review):
  - [ ] No checker errors; spot-checks recorded.

### 5. Release-readiness recommendation (`decision`)

- Agent: `review-board-chair`; skills: `nist-ssdf`, `owasp-asvs`, `evidence-and-citation`
- Consumes: ssdf-assessment, asvs-verification-report, evidence-audit-report
- Produces: release-recommendation
- Gate (human):
  - [ ] Open high-severity findings have owners and either fixes or explicit risk acceptance by the accountable authority.

## Outputs

- `release-recommendation`: Board decision record for release readiness.
