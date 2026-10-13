```yaml
case:
  id: AC-PAY-23
  title: payments-api is acceptably secure for release 2.3
  scope: payments-api commit a1b2c3d, production configuration
  decision_authority: Head of Security Assurance
claims:
  - id: C1
    text: payments-api commit a1b2c3d is acceptably secure for release.
    criticality: high
    argument: Product (ASVS verification) and process (SSDF) evidence together, plus third-party component risk.
    subclaims: [C1.1, C1.2, C1.3]
  - id: C1.1
    text: Authentication meets ASVS Level 2 requirements in V6.
    criticality: high
    frameworks: ["V6.2.1"]
    evidence: [EV-1]
  - id: C1.2
    text: Code review is enforced for all changes.
    criticality: high
    frameworks: ["PW.7.1"]
    evidence: [EV-2]
  - id: C1.3
    text: Known vulnerabilities in third-party components are identified and addressed.
    status: undeveloped
    justification: Dependency scanning results are not yet available; action A-1 to run SCA before release.
evidence:
  - id: EV-1
    description: ASVS L2 V6 verification report, all requirements pass
    artefact: reports/asvs-v6.md
    method: Test
    strength: E3
  - id: EV-2
    description: Branch protection settings and sample of 20 merged pull requests
    artefact: reports/ssdf.md
    method: Inspection
    strength: E3
```

Run `python -m agentlib assurance-case check case.yaml --base .`: the verdict is **incomplete** because C1.3 is
undeveloped. The Head of Security Assurance decides whether to release with C1.3 as a condition.
