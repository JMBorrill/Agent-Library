# SSDF evidence register notes

Original guidance. Identifiers and titles from NIST SP 800-218 v1.1 (OSCAL catalog, read
2026-10-13; `sources/audits/nist-ssdf.md`, PARTIALLY_VERIFIED — task statements and the PDF
narrative were not reviewed for this library, so the evidence ideas below are library suggestions,
not NIST examples).

## Practices (v1.1)
| Group | Practices |
|---|---|
| PO Prepare the Organization | PO.1 Define Security Requirements for Software Development; PO.2 Implement Roles and Responsibilities; PO.3 Implement Supporting Toolchains; PO.4 Define and Use Criteria for Software Security Checks; PO.5 Implement and Maintain Secure Environments for Software Development |
| PS Protect Software | PS.1 Protect All Forms of Code from Unauthorized Access and Tampering; PS.2 Provide a Mechanism for Verifying Software Release Integrity; PS.3 Archive and Protect Each Software Release |
| PW Produce Well-Secured Software | PW.1, PW.2, PW.4–PW.9 (no PW.3) |
| RV Respond to Vulnerabilities | RV.1 Identify and Confirm Vulnerabilities on an Ongoing Basis; RV.2 Assess, Prioritize, and Remediate Vulnerabilities; RV.3 Analyze Vulnerabilities to Identify Their Root Causes |

## Evidence ideas (library suggestions)
| Practice | Evidence that is easy to date and re-check |
|---|---|
| PO.1 | Secure development policy; security requirements baseline (e.g. ASVS level decision) |
| PO.3 / PW.6 | CI pipeline configuration at a tag; build flags |
| PS.1 | Branch-protection export; repository access review |
| PS.2 | Signing runbook and a verification log for a recent release |
| PW.1 / PW.2 | Threat model (`security-threat-model`) and design review record |
| PW.4 | Allow-listed component register; `dependency_pin_check.py` report |
| PW.5 / PW.7 | Coding standard; `security-code-checks` reports; code review records (`software-code-review`) |
| PW.8 | Pen-test report; ASVS verification map (`security-asvs-controls`) |
| RV.1–RV.3 | CVE monitoring dashboard export; vulnerability SLA; postmortems with root-cause analysis |

## Freshness
Default maximum evidence age is 365 days (library default — set your own policy). Always pass
`--as-of` so results are reproducible; the script never reads the system clock.

## Dependency pinning rationale
- Applications: exact pins or a lockfile make builds reproducible and changes reviewable.
- Libraries: ranges let consumers resolve compatible versions; over-pinning causes conflicts.
- VCS references must name a full commit hash; branch names and tags can move.
- Hash-checking (`--hash=`) adds integrity protection; reported as info when absent.
