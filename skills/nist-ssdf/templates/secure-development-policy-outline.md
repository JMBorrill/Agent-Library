# Secure Software Development Policy - outline

> Outline aligned to NIST SP 800-218 (SSDF v1.1). Each section names the SSDF tasks it helps address; verify
> wording with `python -m agentlib ssdf show <task>`. Replace bracketed text. Keep requirements outcome-based
> and risk-based; SSDF does not prescribe tools.

| Field | Value |
|---|---|
| Policy owner | [role] |
| Approved by | [senior leader / authorizing official] (PO.2.3) |
| Version / effective date | |
| Review cycle | [e.g. at least annually or after major incidents or new requirements] (PO.1.1, PO.1.2 examples) |
| Scope | [products, teams, third parties, environments] |

## 1. Purpose and commitment
Management commitment to secure development and how it is communicated (PO.2.3).

## 2. Definitions
Organisation-specific definitions of terms SSDF leaves undefined: sensitive data, qualified person,
well-secured, and the named environments (development, build, test, staging, production, distribution...).

## 3. Roles and responsibilities
SDLC roles incl. security champions, code owners, release authority; review cadence (PO.2.1).
Role-based training requirements and proficiency review (PO.2.2).

## 4. Security requirements
- Requirements for development infrastructure and processes, including third-party components (PO.1.1).
- Requirements organisation-developed software must meet; exception process with periodic review (PO.1.2).
- Requirements communicated to suppliers of commercial components; attestation/provenance expectations (PO.1.3).

## 5. Toolchain
Mandatory tool categories per toolchain type (PO.3.1); toolchain security (pipelines-as-code, tool integrity,
updates, monitoring) (PO.3.2); artifacts tools must generate and retention (PO.3.3).

## 6. Security criteria and gates
Criteria/KPIs/KRIs for security checks across the SDLC and where they are enforced (PO.4.1); how check
information is gathered, protected and used for decisions (PO.4.2).

## 7. Development environments and endpoints
Environment separation, access control, MFA, monitoring (PO.5.1); development endpoint hardening (PO.5.2).

## 8. Protecting code and releases
Least-privilege code storage, reviews, signing (PS.1.1); integrity verification information for acquirers
(PS.2.1); release archiving (PS.3.1); provenance/SBOM collection and sharing (PS.3.2).

## 9. Design and implementation
Risk modelling (PW.1.1); tracking requirements, risks and design decisions (PW.1.2); standardised security
features (PW.1.3); design review (PW.2.1); component acquisition, in-house components and verification
(PW.4.1, PW.4.2, PW.4.4); secure coding standard (PW.5.1); compiler/interpreter/build configuration (PW.6.1,
PW.6.2).

## 10. Verification
When and how code review/analysis is performed and findings triaged (PW.7.1, PW.7.2); executable testing
policy and documentation (PW.8.1, PW.8.2); secure default configuration (PW.9.1, PW.9.2).

## 11. Vulnerability response
Reference the vulnerability response and disclosure procedure (RV.1.1-RV.1.3, RV.2.1, RV.2.2) and root cause
analysis process (RV.3.1-RV.3.4).

## 12. Exceptions, compliance monitoring and review
Exception approval and periodic review; how adherence is measured; policy review triggers.

---
Outline supports, but does not replace, qualified professional judgement and organisational approval.
