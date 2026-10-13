# Source audit: `owasp-asvs`

| Field | Value |
|---|---|
| Source ID | `owasp-asvs` |
| Title (as verified) | OWASP Application Security Verification Standard 5.0.0 |
| Publisher / author | The OWASP Foundation (OWASP ASVS project); copyright 2008-2025 per `0x01-Frontispiece.md` |
| Edition / version / effective date | Version 5.0.0, May 2025 (`0x01-Frontispiece.md` § "Copyright and License"; `README.md` § "Latest Stable Version - 5.0.0") |
| Canonical URL (registry) | https://owasp.org/www-project-application-security-verification-standard/ |
| URL(s) actually read | `https://raw.githubusercontent.com/OWASP/ASVS/v5.0.0/5.0/...` (release tag, used for the index) and `https://raw.githubusercontent.com/OWASP/ASVS/master/...` (README, LICENSE.md, front matter, Makefile, V1 cross-check) |
| Access status | VERIFIED |
| Access method | Official GitHub repository raw files via curl. owasp.org not fetched (proxy blocks) |
| Date checked | 2026-10-13 |
| Licence / reuse terms (as verified) | CC BY-SA 4.0 (Creative Commons Attribution-ShareAlike 4.0 International): `LICENSE.md` (CC BY-SA 4.0 legal text), `README.md` licence statement, `5.0/en/0x01-Frontispiece.md` § "Copyright and License" (reuse must clearly communicate licence terms). ShareAlike applies to adaptations |
| Normative status | Advisory/voluntary standard; becomes mandatory only when adopted by contract, policy or regulation. OWASP does not certify vendors or software (`0x04-Assessment_and_Certification.md`) |

## Access ledger
- `master`: `README.md` (200), `LICENSE.md` (200), `LICENSE` (404), `5.0/Makefile` (200), `5.0/en/0x01-Frontispiece.md`, `0x02-Preface.md`, `0x03-What-is-the-ASVS.md`, `0x04-Assessment_and_Certification.md`, `0x10-V1-Encoding-and-Sanitization.md`, `0x90-Appendix-A_Glossary.md` (all 200). 404: `5.0/README.md`, `5.0/en/0x00-Header.md`, `5.0/en/0x03-Using-ASVS.md`, `5.0/en/TOC.md`.
- Tag `v5.0.0` (pinned; README says `master` is "bleeding edge" with 5.0.1 as next target): all 17 chapter files `5.0/en/0x10-V1-...` to `5.0/en/0x26-V17-WebRTC.md` (200), front matter `0x01`–`0x05` (incl. `0x05-For-Users-Of-4.0.md`), `0x90-Appendix-A_Glossary.md`, `0x91-Appendix-B_References.md`, `0x92-Appendix-C_Cryptography.md` (200, appendix B/C existence only), official exports `5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.csv` and `..._en.flat.json` (200). Probe for a V18 file (`0x27-V18`) returned 404.
- Chapter filenames were discovered by probing (GitHub API listing blocked); completeness confirmed because the official CSV's chapter/section set equals the parsed set.
- `master` V1 file was byte-identical to the `v5.0.0` V1 file on 2026-10-13; other chapters were not diffed against `master`.

## Verified content
**Index build** — `sources/extracts/owasp-asvs-5.0.0-index.json` parsed from the 17 tag `v5.0.0` chapter files (rows `| **x.y.z** | text | level |`; requirement text omitted).
- 17 chapters, 80 sections, **345 requirements**: **L1 = 70, L2 = 183, L3 = 92**. The level column is the lowest level at which the requirement applies (L2 compliance = L1 + L2 = 253; L3 = all 345).
- Cross-check: every ID, section assignment and level matches the official `..._en.csv` (345 rows) exactly; section IDs/titles also match. No duplicates, no malformed rows, no ambiguity found.

| Chapter | Title | File | Sections | L1 | L2 | L3 | Total |
|---|---|---|---|---|---|---|---|
| V1 | Encoding and Sanitization | `5.0/en/0x10-V1-Encoding-and-Sanitization.md` | 5 | 8 | 19 | 3 | 30 |
| V2 | Validation and Business Logic | `5.0/en/0x11-V2-Validation-and-Business-Logic.md` | 4 | 4 | 7 | 2 | 13 |
| V3 | Web Frontend Security | `5.0/en/0x12-V3-Web-Frontend-Security.md` | 7 | 8 | 11 | 12 | 31 |
| V4 | API and Web Service | `5.0/en/0x13-V4-API-and-Web-Service.md` | 4 | 2 | 8 | 6 | 16 |
| V5 | File Handling | `5.0/en/0x14-V5-File-Handling.md` | 4 | 4 | 5 | 4 | 13 |
| V6 | Authentication | `5.0/en/0x15-V6-Authentication.md` | 8 | 13 | 22 | 12 | 47 |
| V7 | Session Management | `5.0/en/0x16-V7-Session-Management.md` | 6 | 6 | 12 | 1 | 19 |
| V8 | Authorization | `5.0/en/0x17-V8-Authorization.md` | 4 | 4 | 3 | 6 | 13 |
| V9 | Self-contained Tokens | `5.0/en/0x18-V9-Self-contained-Tokens.md` | 2 | 4 | 3 | 0 | 7 |
| V10 | OAuth and OIDC | `5.0/en/0x19-V10-OAuth-and-OIDC.md` | 7 | 5 | 24 | 7 | 36 |
| V11 | Cryptography | `5.0/en/0x20-V11-Cryptography.md` | 7 | 3 | 11 | 10 | 24 |
| V12 | Secure Communication | `5.0/en/0x21-V12-Secure-Communication.md` | 3 | 3 | 6 | 3 | 12 |
| V13 | Configuration | `5.0/en/0x22-V13-Configuration.md` | 4 | 1 | 12 | 8 | 21 |
| V14 | Data Protection | `5.0/en/0x23-V14-Data-Protection.md` | 3 | 2 | 7 | 4 | 13 |
| V15 | Secure Coding and Architecture | `5.0/en/0x24-V15-Secure-Coding-and-Architecture.md` | 4 | 3 | 10 | 8 | 21 |
| V16 | Security Logging and Error Handling | `5.0/en/0x25-V16-Security-Logging-and-Error-Handling.md` | 5 | 0 | 16 | 1 | 17 |
| V17 | WebRTC | `5.0/en/0x26-V17-WebRTC.md` | 3 | 0 | 7 | 5 | 12 |

**Using the ASVS** — `5.0/en/0x03-What-is-the-ASVS.md` (there is no separate "Using-ASVS" file in 5.0):
- § "Documented security decisions": documentation requirements sit in a chapter's first section and each pairs with an implementation requirement; verifying documentation and implementation are separate activities.
- § "Application Security Verification Levels" / "Level evaluation" / "Level 1" / "Level 2" / "Level 3" / "Which level to achieve": three levels; levels chosen by priority (risk reduction vs effort, low entry barrier); L1 ≈ 20% (minimum, first-layer defences; not necessarily black-box testable), L2 ≈ 50% more (target for most applications; ~70% cumulative), L3 the final ~30% (defence in depth, hard-to-implement). Organisations pick their level by risk analysis.
- § "The structure of the ASVS": ~350 requirements in 17 chapters; filter chapters/sections by relevance (e.g. skip V3 for machine-to-machine APIs, V10/V17 if no OAuth/WebRTC).
- § "Release strategy": Major.Minor.Patch semantics (major may renumber; minor may add/remove but keep numbering; patch only removes or relaxes).
- § "How to Reference ASVS Requirements": ID format `<chapter>.<section>.<requirement>`; preferred external citation `v<version>-<chapter>.<section>.<requirement>`, e.g. `v5.0.0-1.2.5`; the `v` must be lowercase; unversioned IDs are taken to mean the latest version.
- § "Flexibility with the ASVS" / "Forking the ASVS": organisation-specific forks encouraged if traceability is preserved; start forks from L1.
- `0x04-Assessment_and_Certification.md`: OWASP does not certify; reports should state scope, level targeted, all requirements checked, exceptions and N/A items; automated tools alone are insufficient ("testable using automation != running an off the shelf tool"); black-box-only testing discouraged.
- `0x05-For-Users-Of-4.0.md` (title "Changes Compared to v4.x"): of 286 v4.0.3 requirements, few remain unchanged and identifiers differ throughout; v5 drops direct NIST/CWE mappings; levels redefined.

## Secondary corroboration (not primary verification)
None used.

## Elements useful as AI skills
- Versioned requirement citation rule (`v5.0.0-x.y.z`) — `0x03` § "How to Reference ASVS Requirements".
- Level selection by risk and cumulative scoping (L1 ⊂ L2 ⊂ L3) — `0x03` level sections.
- Chapter applicability filtering — `0x03` § "The structure of the ASVS".
- Paired documentation/implementation verification — `0x03` § "Documented security decisions".
- Verification report contents and scope statement; tool/pen-test limits — `0x04`.
- Machine-readable ID/level/section index for coverage maps — `sources/extracts/owasp-asvs-5.0.0-index.json`.

## Proposed skills, agents and tools
- Planned `security-asvs-controls`, `security-release-gate`, `security-threat-model` (per `sources/framework-build-plan.json`); agents: Security reviewer, Software quality reviewer.
- Tools: validator that every cited ASVS ID exists in the index and carries the `v5.0.0-` prefix; level filter (target level → applicable IDs); verification-map template (ID, level, applicable/N/A with rationale, evidence, result); evaluation fixture: deliberately vulnerable scenarios.

## Limitations, applicability and copyright
- Pinned to tag `v5.0.0`; `master` may diverge (5.0.1 planned). Re-generate the index for any new release; IDs are not stable across major versions (4.x → 5.0 renumbered).
- Requirement text is deliberately not reproduced; skills must read the source. Any reproduction or adaptation of text triggers CC BY-SA 4.0 ShareAlike obligations.
- Percentages in the level guidance are approximate; actual counts here: L1 70 (20.3%), L2 183 (53.0%), L3 92 (26.7%).
- Some requirements carry stricter conditions at higher levels within their text; the level column alone does not capture this — a human must read the text.
- Commit SHA of the tag not captured (API blocked).

## Re-check by
2027-04-13 — check for ASVS 5.0.1 or later release; if released, re-run the index build against the new tag and diff IDs/levels; re-confirm licence.
