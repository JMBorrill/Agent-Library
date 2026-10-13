# Using ASVS to define security requirements (design time)

Source: OWASP ASVS 5.0.0 - documented security decisions (PDF pp. 12, 21-22), use cases as security
architecture guidance and secure coding reference (PDF pp. 17-18), forking/tailoring (PDF pp. 16-17).
Paraphrased.

## Principles

- ASVS requirements state security goals, not mechanisms; mechanisms appear only where they are the
  sole practical solution or as examples (PDF p. 21). Keep that property in your spec: requirement
  = outcome; design = mechanism.
- **Documented security decisions.** Where rules differ per application (permissions, input
  validation, protection of sensitive data, session timeouts), ASVS requires the decision to be
  documented, then implemented (PDF p. 12). Documentation requirements sit in the first section of a
  chapter and always have a related implementation requirement (PDF p. 12). Decisions may live in a
  document or in a mandated common library (PDF p. 12).
- Tailoring is encouraged (organisation- or domain-specific fork, omitting irrelevant sections), as long
  as ids stay traceable so "passing 4.1.1 means the same" everywhere (PDF pp. 16-17).

## Documentation sections in 5.0.0 (from the catalog)

| Section | Topic | Requirements (level) |
|---|---|---|
| V2.1 | Validation and business logic | 2.1.1 (1), 2.1.2 (2), 2.1.3 (2) |
| V3.1 | Web frontend | 3.1.1 (3) |
| V5.1 | File handling | 5.1.1 (2) |
| V6.1 | Authentication | 6.1.1 (1), 6.1.2 (2), 6.1.3 (2) |
| V7.1 | Session management | 7.1.1 (2), 7.1.2 (2), 7.1.3 (2) |
| V8.1 | Authorization | 8.1.1 (1), 8.1.2 (2), 8.1.3 (3), 8.1.4 (3) |
| V11.1 | Cryptographic inventory and documentation | 11.1.1 (2), 11.1.2 (2), 11.1.3 (3), 11.1.4 (3) |
| V13.1 | Configuration | 13.1.1 (2), 13.1.2 (3), 13.1.3 (3), 13.1.4 (3) |
| V14.1 | Data protection | 14.1.1 (2), 14.1.2 (2) |
| V15.1 | Secure coding and architecture | 15.1.1 (1), 15.1.2 (2), 15.1.3 (2), 15.1.4 (3), 15.1.5 (3) |
| V16.1 | Security logging | 16.1.1 (2) |

Read each with `python -m agentlib asvs show <id>` before writing the decision.

## Procedure

1. Fix target level and applicable chapters/sections (see [levels-and-scoping.md](levels-and-scoping.md)).
2. Generate the baseline: `python -m agentlib asvs checklist --level N --chapters ... --format yaml`.
3. Write the documented decisions for each applicable `Vn.1` requirement first; they parameterise
   other requirements (e.g. 6.1.1 rate-limit/anti-automation decisions feed 6.3.1).
4. For each requirement, record: component(s) responsible, implementation approach or approved
   library, acceptance/verification test, owner, phase. Use
   [../templates/security-requirements-spec.md](../templates/security-requirements-spec.md).
5. Mark requirements not applicable with a justification tied to architecture (e.g. "no file upload").
6. Keep ids version-qualified (`v5.0.0-x.y.z`) so the spec survives future ASVS releases.
7. Later, the same file becomes the verification checklist; validate with `asvs check-assessment`.
