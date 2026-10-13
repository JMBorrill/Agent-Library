# Claim strength scale

Grade every assessment conclusion. Report the grade next to the conclusion.

| Grade | Name | Basis | Allowed wording |
|---|---|---|---|
| E4 | Demonstrated | Independent test, measurement or inspection of the real artefact, reproducible, recorded | "verified by test/inspection on <date>, record <ref>" |
| E3 | Corroborated | Two or more independent artefacts agree (e.g. config + log, design + code) | "evidence indicates ... (corroborated by ...)" |
| E2 | Documented | A single artefact or statement asserts it (policy, plan, interview) | "documented in ...; not independently verified" |
| E1 | Asserted | Verbal or self-declared without artefact | "reported by ...; no evidence seen" |
| E0 | None | Nothing examined | "not assessed" |

Rules:

1. A "met/implemented/pass" status needs at least E2; safety-, security- or money-critical items need E3+.
2. Never upgrade a grade because the claim is plausible or common practice.
3. A gap in evidence is a finding in its own right ("unable to verify"), not a pass.
4. AI-generated analysis is never itself evidence of conformance; it is a judgement (category c).
5. Verification methods follow NASA practice where relevant: Test, Analysis, Inspection, Demonstration
   (see the `requirements-engineering` skill).
