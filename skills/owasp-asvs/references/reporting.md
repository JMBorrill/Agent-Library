# Verification reporting

Source: OWASP ASVS 5.0.0 "Assessment and Certification" (PDF pp. 19-20, printed 18-19); identifier
referencing (PDF pp. 16-17). Paraphrased.

## Required content (from the standard)

1. **Scope**: which level the organisation is attempting to achieve and which requirements were
   included - stated as what was included rather than what was not (PDF p. 19).
2. **Summary of all requirements checked** - not "by exception" like a traditional pentest report
   (PDF p. 19).
3. **Requirements where exceptions were noted** (failures) and **guidance on resolving** them (PDF p. 19).
4. **Non-applicable requirements** must be noted (e.g. session management in stateless APIs) (PDF p. 19).
5. **Opinion on exclusions**: the verifier's view of the rationale for excluding requirements not
   implemented (PDF p. 19).
6. **Methods** used, disclosed and ideally repeatable (PDF p. 19); robust evidence (PDF p. 20).
7. Use version-qualified ids, `v5.0.0-<id>`, with a lowercase `v` (PDF pp. 16-17).

## Library conventions

- Generate the numbers, never compute them by hand:
  `python -m agentlib asvs check-assessment assessment.yaml --level N --chapters ... --format md`.
  Paste its per-chapter table and failure list into the report; attach the JSON as an annex.
- Compliance % = pass / (in-scope - not-applicable) x 100. Missing and not-verified count as not passed,
  and a report containing them must be labelled *incomplete* / *interim*.
- Verdict wording (calibrated):
  - "All N in-scope Level X requirements were verified as passing within the stated scope and methods."
  - "M of N in-scope Level X requirements failed; Level X is not achieved."
  - Never "certified", "fully compliant", "guaranteed secure". OWASP does not certify, and third-party
    ASVS certification claims are not OWASP-endorsed (PDF p. 19).
- Severity of failures is the verifier's risk rating (e.g. CVSS or organisational scale); ASVS levels
  are **not** severities. Record both.
- Reproduce requirement text only as needed and include the attribution line:
  "Requirement text: OWASP ASVS 5.0.0, (c) The OWASP Foundation, CC BY-SA 4.0."
- Above-level requirements that were checked are reported separately as recommendations.
