# Vulnerability Response and Disclosure Procedure - Acme Payments

Supports SSDF v1.1 practices RV.1, RV.2 and RV.3 (NIST SP 800-218 Table 1, PDF pp.25-28). Example items are
notional options from SSDF, adopted here by policy choice.

| Field | Value |
|---|---|
| Procedure owner / PSIRT lead | Head of AppSec |
| Products covered | Checkout platform, all supported releases |
| Exercise cadence | Twice a year tabletop exercise (RV.1.3 Example 4) |

## 1. Policy statement (RV.1.3, p.26)
We publish a vulnerability disclosure policy at /security with a security contact and security.txt, commit
to acknowledge reports within 3 business days, and keep reporters informed. Legal approves safe-harbour text.

## 2. Intake channels (RV.1.1, p.25)
Researcher and customer reports; vulnerability databases and advisories for our components; automated
monitoring of SBOM/composition data of released versions; threat intelligence feeds.

## 3. Confirmation (RV.1.2, p.25)
PSIRT reproduces each credible report; scheduled CodeQL and dependency analysis run against supported releases.

## 4. Recording and risk analysis (RV.2.1, p.26)
Every vulnerability is recorded in Jira VULN with affected versions and a risk rating based on exploitability
and impact (CVSS plus exploitation status).

## 5. Risk response (RV.2.2, p.27)
Remediate, temporarily mitigate, or formally accept with CISO approval. Target remediation times by severity
are set in the Secure Development Policy. Security advisories describe affected versions, detection and fixes;
fixes are delivered through the signed update channel. Risk decisions update the PW.1.2 register.

## 6. Communications
Coordinated disclosure with reporters and upstream projects; playbooks for zero-days, in-the-wild exploitation
and multi-party incidents (RV.1.3 Example 3).

## 7. Root cause and prevention (RV.3.1-RV.3.4, p.27)
Record the root cause of each vulnerability (RV.3.1); quarterly pattern review (RV.3.2); variant analysis
for the same class (RV.3.3); SDLC and toolchain changes with lessons learned in the developer wiki (RV.3.4).

## 8. Metrics and review
Time to acknowledge, time to remediate by severity, recurring root causes; annual review.

This procedure supports, but does not replace, qualified professional, legal and organisational judgement.
