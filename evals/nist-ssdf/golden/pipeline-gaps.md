# SSDF v1.1 pipeline review - acme-checkout (GitHub Actions)

Mapping produced with `python -m agentlib ssdf map-pipeline` and its documented rules. A control that
supports a task is not proof the task is implemented: support != compliance. Scope, enforcement, triage and
records still have to be evidenced.

## Summary

- 8 of 42 tasks have an example-based supporting control in this pipeline.
- Unmapped step: the Checkov IaC scan has no SSDF mapping rule, so it earns no credit here (it may still be
  useful for environment security evidence under PO.5.1, which needs separate review).
- Disabled step: Cosign image signing is `enabled: false`, so it is ignored.

## Tasks with supporting controls

| Task | Supporting steps | Basis |
|---|---|---|
| PS.1.1 (p.18) | Branch protection with 2 reviewers and CODEOWNERS; repository access control | PS.1.1 Ex.1, Ex.2, Ex.4 |
| PW.7.2 (p.23) | CodeQL, peer review, Gitleaks (secret scanning is interpretive) | PW.7.2 Ex.1, Ex.4, Ex.6 |
| PW.4.4 (p.22) | Dependabot + Snyk | PW.4.4 Ex.1, Ex.2 |
| PW.4.1 (p.21) | Snyk composition analysis; lockfiles (interpretive) | PW.4.1 Ex.3 |
| RV.1.2 (p.25) | Scheduled CodeQL runs | RV.1.2 Ex.1 |
| PO.4.2 (p.17) | Blocking CodeQL and Gitleaks gates | PO.4.2 Ex.3 |
| PO.3.2 (p.16) | Pipeline-as-code; actions pinned by SHA | PO.3.2 Ex.3, Ex.7 |
| PW.5.1 (p.22) | ESLint security rules | PW.5.1 Ex.7 |

## Technical tasks with no supporting control

| Task | Gap | Suggested control |
|---|---|---|
| PS.2.1 (p.19) | No integrity information for acquirers (signing step disabled) | Enable Cosign signing and publish release hashes |
| PS.3.1 (p.19) | No release archive with protected retention | Immutable artifact repository with read-only access |
| PS.3.2 (p.19) | No SBOM or provenance data | Generate SBOM (SPDX/CycloneDX) and signed build provenance per release |
| PW.8.2 (p.24) | No DAST, fuzzing or security tests | Add DAST for public APIs and fuzzing of parsers |
| RV.1.1 (p.25) | Dependency scanning is not scheduled against released versions | Schedule SCA / SBOM monitoring of supported releases |
| RV.2.1 (p.26) | Findings are not tracked in an issue tracker | Auto-file findings with risk scoring |
| RV.3.3 (p.27) | No class-wide variant analysis | Add CodeQL variant queries after each confirmed vulnerability |
| PO.3.3 (p.16) | Tool results are not retained as artifacts | Retain scan results and logs with a retention policy |
| PO.5.1 (p.17) | Environment separation and MFA not described | Document SSO/MFA and network separation for CI and build |
| PW.1.1, PW.2.1 | No threat modelling or design review step | Threat-model and design-review gates for new services |
| PW.6.1, PW.6.2 | No build tool / interpreter configuration controls | Pin and verify build tool versions; approved build configuration |
| PW.9.1, PW.9.2 | No tests of secure default settings | Tests asserting secure defaults |

Organisational tasks (for example PO.1.x, PO.2.x, PW.7.1, RV.1.3, RV.3.1) are expected to be evidenced by
policies and process records rather than pipeline steps.

## Caveat

This review supports, but does not replace, qualified professional judgement or an assessment of whether the
tasks are actually implemented across all products and releases.
