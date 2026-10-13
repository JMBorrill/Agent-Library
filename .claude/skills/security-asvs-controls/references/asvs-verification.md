# ASVS 5.0.0 verification notes

Original wording; facts from `sources/audits/owasp-asvs.md` (ASVS 5.0.0, tag `v5.0.0`, read
2026-10-13). Requirement text is not reproduced — read it in the standard.

## Structure (as indexed)
17 chapters, 80 sections, 345 requirements. Levels are cumulative: an L2 target covers L1 + L2
(253 requirements); L3 covers all 345.

| Chapter | Title | L1 | L2 | L3 |
|---|---|---|---|---|
| V1 | Encoding and Sanitization | 8 | 19 | 3 |
| V2 | Validation and Business Logic | 4 | 7 | 2 |
| V3 | Web Frontend Security | 8 | 11 | 12 |
| V4 | API and Web Service | 2 | 8 | 6 |
| V5 | File Handling | 4 | 5 | 4 |
| V6 | Authentication | 13 | 22 | 12 |
| V7 | Session Management | 6 | 12 | 1 |
| V8 | Authorization | 4 | 3 | 6 |
| V9 | Self-contained Tokens | 4 | 3 | 0 |
| V10 | OAuth and OIDC | 5 | 24 | 7 |
| V11 | Cryptography | 3 | 11 | 10 |
| V12 | Secure Communication | 3 | 6 | 3 |
| V13 | Configuration | 1 | 12 | 8 |
| V14 | Data Protection | 2 | 7 | 4 |
| V15 | Secure Coding and Architecture | 3 | 10 | 8 |
| V16 | Security Logging and Error Handling | 0 | 16 | 1 |
| V17 | WebRTC | 0 | 7 | 5 |

## Citing requirements
- ASVS recommends `v<version>-<chapter>.<section>.<requirement>` with a lowercase `v`, e.g.
  `v5.0.0-1.2.5`. An unversioned ID is read as "latest version", which is ambiguous over time —
  the script rejects it. The library's `ASVS-v5.0.0-1.2.5` form is accepted too.
- Major versions renumber requirements; minor versions may add or remove but keep numbering.

## Verification practice
- Verify documentation requirements and their paired implementation requirements separately.
- Combine methods: automated tests for regressions, code/config review for design properties,
  pen-test for exploitability. "Testable by automation" is not the same as "an off-the-shelf
  scanner checks it".
- A verification report states scope, target level, every requirement checked, exceptions and
  N/A items with reasons.

## Coverage figures produced
- `mapped_pct` — in-scope requirements that appear in the map.
- `pass_pct_of_applicable` — passes divided by rows marked applicable (N/A rows excluded).
Both are bookkeeping measures. Neither is a security score.

## Chapter selection prompts
- No browser client → consider excluding V3 (record why).
- No OAuth/OIDC → V10 out; no WebRTC → V17 out; no file upload/download → most of V5 out.
- GraphQL or WebSocket in use → keep V4 sections V4.3 / V4.4.
