# Pipeline review - acme-checkout

The pipeline is in good shape and is SSDF compliant for most of the Produce Well-Secured Software group.

## Covered

| Task | Control |
|---|---|
| PW.7.2 | CodeQL and peer review |
| PW.4.4 | Dependabot + Snyk |
| PS.2.1 | Covered by Cosign image signing |
| PS.3.2 | Covered by lockfiles, which act as an SBOM |
| PO.5.1 | Covered by Checkov IaC scanning |

## Gaps

- PW.8.2: no DAST.
- RV.1.3: no disclosure policy.

Overall the build pipeline satisfies the SSDF requirements apart from testing.
