# Source audit: `nasa-software`

| Field | Value |
|---|---|
| Source ID | `nasa-software` |
| Title (as verified) | NASA Software Engineering and Assurance Handbook (SWEHB; document designation NASA-HDBK-2203) – supports NPR 7150.2 NASA Software Engineering Requirements (titles from search snippets) |
| Publisher / author | NASA Office of the Chief Engineer / Office of Safety and Mission Assurance |
| Edition / version / effective date | Wiki "SWEHB" current version aligned to NPR 7150.2D and NASA-STD-8739.8B (snippets). NPR 7150.2D reported as 2022 (NASA-STD-8739.8B revision history references alignment with 7150.2D dated 2022-09-08). NASA-HDBK-2203B approved 20 April 2020 per a NASA SMA news item. No NPR 7150.2E found |
| Canonical URL (registry) | https://swehb.nasa.gov/ |
| URL(s) actually read | None (primary) |
| Access status | INACCESSIBLE |
| Access method | Blocked host; search-engine results only |
| Date checked | 2026-10-13 |
| Licence / reuse terms (as verified) | Not verified (NASA work; third-party content possible) |
| Normative status | NPR 7150.2 is mandatory for NASA (and flowed-down contracts); the handbook is advisory guidance |

## Access ledger
- `curl https://swehb.nasa.gov/` -> `curl: (56) CONNECT tunnel failed, response 403`.
- WebFetch https://swehb.nasa.gov/ -> `getaddrinfo ENOTFOUND swehb.nasa.gov`.
- WebSearch succeeded (3 queries).

## Verified content
None.

## Secondary corroboration (not primary verification)
- Requirement IDs use the form SWE-nnn (e.g. SWE-020 "classify each system and subsystem containing software ... Classes A–F per Appendix D", SWE-021 reclassification) – snippets of https://swehb.nasa.gov/x/BoHeB.
- Six software classes A–F: A human-rated space software; B non-human-rated space software; C mission support software; D basic science/engineering design and research software (approx.); E design concept / research software (approx.); F general-purpose computing, business and IT. Only A and F wording seen reliably; B–E descriptions are paraphrases of a summary and need checking.
- Classification plus separate software safety-criticality (NASA-STD-8739.8) determines applicable requirements via the NPR 7150.2 requirements mapping matrix (Appendix C per snippet).
- SWEHB home page lists NPR 7150.2D and NASA-STD-8739.8B as the requirement sets it supports; older SWEHB versions (7150.2A/B) remain online labelled as superseded.
- NASA-HDBK-2203B five-year review date (20 Apr 2025, from a Scribd copy) has passed – status unknown.

## Elements useful as AI skills
- Software classification decision procedure (class A–F + safety criticality) -> requirement subset.
- Per-SWE requirement guidance pages (rationale, guidance, small-project notes) – structure only.

## Proposed skills, agents and tools
Software-assurance review skill: classification questionnaire, SWE-ID cross-reference table populated by a human from NPR 7150.2D Appendix C; validator that flags uncited SWE IDs.

## Limitations, applicability and copyright
Secondary only. Confirm current NPR 7150.2 letter on NODIS and current handbook revision. NASA-specific; not a certification.

## Re-check by
2027-04-13 – NODIS for NPR 7150.2 revision; swehb.nasa.gov version banner.
