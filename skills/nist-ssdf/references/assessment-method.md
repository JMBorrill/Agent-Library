# SSDF gap assessment method

How to run a defensible, evidence-based SSDF v1.1 self-assessment with the `ssdf` tools. Page numbers are
PDF pages of NIST SP 800-218 (printed page = PDF page - 9).

## 1. Framing the assessment correctly

- SSDF describes **outcomes**, not tools or techniques (PDF p.8; PDF pp.10-11). Assess whether the task's
  outcome is achieved, not whether a particular product is installed.
- It is **not a checklist** and its practices **are not prioritized**; implementation degree and formality vary
  with the producer's risk, cost, feasibility and applicability (PDF p.12). The assessment is a baseline for a
  risk-based improvement plan, not a pass/fail audit.
- Not every practice applies to every case (PDF p.12). Record applicability decisions with a justification.
- Notional implementation examples are optional and not the only options (PDF p.13). Use them as evidence
  prompts, never as mandatory sub-requirements.
- Define the undefined terms (sensitive data, qualified person, well-secured) and enumerate environments
  (development, build, staging, integration, test, production, distribution) before assessing PO.5 (PDF p.13).
- Where platforms/services share responsibility, record which party performs each task and how the provider
  attests (PDF p.12). A task done by a provider can be `implemented` only with evidence from that provider.

## 2. Scope statement (record in the worksheet header)

Organisation; products/services in scope; teams; SDLC model (agile, DevOps, waterfall); delivery model;
languages/build toolchains; hosting/platform providers and shared-responsibility split; period assessed;
assessor(s) and independence; evidence access limits.

## 3. Evidence by practice group

| Group | Typical evidence |
|---|---|
| PO (Prepare the Organization) | Secure development policy and requirements baseline (PO.1.1/PO.1.2); supplier contract clauses (PO.1.3); RACI and role descriptions, training records and curriculum (PO.2.x); management commitment statement (PO.2.3); toolchain standard (PO.3.1); pipeline-as-code, tool hardening and integrity checks (PO.3.2); retained tool artifacts/audit trail (PO.3.3); security criteria, KPIs/KRIs, gate definitions (PO.4.1); automated collection and protection of check results (PO.4.2); environment separation, MFA, access logs (PO.5.1); endpoint hardening baselines/MDM (PO.5.2) |
| PS (Protect the Software) | Repository access reviews, branch protection, commit/code signing (PS.1.1); published hashes and signature verification guidance for acquirers (PS.2.1); release archive with retention and read-only access (PS.3.1); SBOM/provenance per release and how it is shared and protected (PS.3.2) |
| PW (Produce Well-Secured Software) | Threat models and data classification (PW.1.1); security requirements/risk decisions register (PW.1.2); standard security services/libraries (PW.1.3); design review records (PW.2.1); component approval, SCA, vetted repositories (PW.4.1/PW.4.4); in-house component practices (PW.4.2); secure coding standard and tooling (PW.5.1); compiler/interpreter/build configuration (PW.6.x); review/analysis policy and triaged findings (PW.7.x); test policy, DAST/fuzzing/pentest results (PW.8.x); secure default configuration baseline and admin documentation (PW.9.x) |
| RV (Respond to Vulnerabilities) | Vulnerability intake sources and monitoring (RV.1.1); continuous analysis of supported releases (RV.1.2); disclosure policy, PSIRT, playbooks, exercises (RV.1.3); vulnerability records with risk scoring (RV.2.1); remediation decisions, advisories, update delivery (RV.2.2); root-cause records, trend analysis, class eradication, SDLC changes (RV.3.x) |

Run `python -m agentlib ssdf show <task>` to see the printed examples and references for each task before
interviewing owners.

## 4. Status rules and evidence quality

- `implemented` needs at least one artefact you have inspected, covering the whole scope. Interviews alone
  give `partial` at most.
- `partial` when the outcome is achieved for some products/teams/releases, or when one element (e.g. the
  "maintain over time" or "triage" part of a task) is missing.
- `planned` only with a committed owner and date; otherwise `not-implemented`.
- `not-applicable` requires a justification that would convince an independent reviewer.
- Record the evidence location (document id, URL, ticket, log path) rather than the evidence itself.

The checker enforces these rules: errors for unknown ids, retired ids, duplicates, missing tasks, empty or
invalid status, `implemented` without evidence and `not-applicable` without justification; warnings for
`partial` without evidence, `planned` without owner/target date, bad or past target dates.

## 5. Scoring (tool heuristic)

`coverage = (implemented + 0.5 x partial) / (tasks - not-applicable)`, reported overall, per group and per
practice. Unassessed rows, `implemented` without evidence and `not-applicable` without justification score
0 (conservative). `implemented %` is reported separately. These figures describe a self-assessment; they are
not an SSDF "score" defined by NIST.

## 6. Prioritisation (tool heuristic)

SSDF does not prioritise (PDF p.12), so the tool uses a transparent ordering that you should then adjust to
the organisation's risk:

1. Status severity: unassessed / not-implemented > implemented-without-evidence / planned > partial.
2. Number of EO 14028 Section 4e subsections mapped to the task in Appendix A Table 2 (PDF p.33) - a proxy
   for relevance to software supply-chain attestation.
3. Document order.

Tiers: **High** = unassessed or not-implemented and EO-mapped; **Medium** = other unassessed or
not-implemented, implemented-without-evidence, or planned without owner/date; **Low** = partial, or planned
with owner and date. Adjust for: exposure of the product, foundational dependencies (e.g. PO.4.1 criteria
before PO.4.2 automation; PW.1.1 risk models before PW.2.1 design review), regulatory/customer obligations.

## 7. Common pitfalls

- Treating the scanner as the control: PW.7.2 and PW.8.2 also require recording and triaging issues.
- Marking PS.2.1 implemented because artifacts are signed internally: the task is about making integrity
  verification information *available to acquirers*.
- Counting an SBOM that is generated but never shared, protected or updated as PS.3.2 `implemented`
  (see PS.3.2 examples 1-4).
- Marking all of PW.6 N/A for interpreted languages: PW.6 covers "compiler, interpreter, and build" tools.
- Citing retired ids (PW.4.5, PW.5.2...) from SSDF 1.0-era material.
- Reporting "SSDF compliant". Say "self-assessed coverage of N% across 42 tasks".
