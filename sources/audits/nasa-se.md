# Source audit: `nasa-se`

| Field | Value |
|---|---|
| Source ID | `nasa-se` |
| Title (as verified) | NASA Systems Engineering Handbook, NASA/SP-2016-6105 Rev 2 (title seen in search results and library/bookseller records only) |
| Publisher / author | NASA (Office of the Chief Engineer) |
| Edition / version / effective date | Rev 2, 2016 (printings dated 2017 also circulate). No 2024/2025/2026 edition found in search results. Governing requirements: NPR 7123.1 (secondary results indicate 7123.1D, effective 5 July 2023, expiring 5 July 2028, amended by later changes) |
| Canonical URL (registry) | https://www.nasa.gov/reference/systems-engineering-handbook/ |
| URL(s) actually read | None (primary). Search-engine result snippets only |
| Access status | INACCESSIBLE |
| Access method | curl and WebFetch attempted (blocked); search-engine results only for secondary corroboration |
| Date checked | 2026-10-13 |
| Licence / reuse terms (as verified) | Not verified. Background (unverified this session): NASA works are generally not subject to US copyright, but the handbook may contain third-party figures/material; link rather than redistribute |
| Normative status | Advisory guidance (handbook). Mandatory requirements for NASA programmes sit in NPR 7123.1, not in the handbook; neither is binding outside NASA/contract context |

## Access ledger
- `curl https://www.nasa.gov/` -> `curl: (56) CONNECT tunnel failed, response 403` (same for ntrs.nasa.gov, swehb.nasa.gov).
- WebFetch https://www.nasa.gov/reference/systems-engineering-handbook/ -> `getaddrinfo ENOTFOUND www.nasa.gov`.
- WebFetch https://ntrs.nasa.gov/citations/20170001761 -> `getaddrinfo ENOTFOUND ntrs.nasa.gov`.
- No official NASA GitHub copy of the handbook was looked for beyond this; unofficial mirrors (academia.edu, center-hosted PDF copies on larc.nasa.gov appear in results) were NOT downloaded or relied on.
- WebSearch (several queries) succeeded; results summarised below as secondary.

## Verified content
None. No primary or official NASA content was opened during this session.

## Secondary corroboration (not primary verification)
Detailed list with evidence URLs: `sources/extracts/nasa-se-processes-corroboration.json`.
- **17 common technical processes in three sets** (System Design; Product Realization; Technical Management/Crosscutting), originating in NPR 7123.1 and shown as the "SE engine" (Figure 2.1-1, handbook section 2.1). Processes 1–9 are described as project-execution tasks and 10–17 as crosscutting tools; not strictly sequential. [search snippets of https://www.nasa.gov/seh/2-1_technical-processes and the NASA-hosted PDF]
- **Section numbers/names** (table-of-contents text in snippets of https://www.nasa.gov/sites/default/files/atoms/files/nasa_systems_engineering_handbook_0.pdf and bookfusion listing): 4.1 Stakeholder Expectations Definition; 4.2 Technical Requirements Definition; 4.3 Logical Decomposition; 4.4 Design Solution Definition; 5.1 Product Implementation; 5.2 Product Integration; 5.3 Product Verification; 5.4 Product Validation; 5.5 Product Transition; 6.1 Technical Planning; 6.2 Requirements Management; 6.3 Interface Management; 6.4 Technical Risk Management; 6.5 Configuration Management; 6.6 Technical Data Management; 6.7 Technical Assessment; 6.8 Decision Analysis. Each section is split into a process description and guidance subsection.
- **Life cycle**: Formulation (Pre-Phase A, A, B) and Implementation (C, D, E, F) separated by Key Decision Points (MIT OCW 16.842 slides reproducing NASA chart; nasa.gov/seh phase pages in snippets). Individual phase titles not confirmed.
- **Reviews**: MCR, SRR, MDR/SDR, PDR, CDR, PRR (conditional), SIR, TRR, SAR, ORR, FRR, CERR (discretionary), PLAR, DR (decommissioning) – from a SWEHB chart (https://swehb.nasa.gov/x/WwD7) and MIT slides. Review-to-phase mapping NOT confirmed.
- **NPR 7123.1 status**: 7123.1C effective 14 Feb 2020 (expired 14 Feb 2025); 7123.1D effective 5 July 2023 (center-hosted copy https://explorers.larc.nasa.gov/APSMEX25/SMEX/pdf_files/NASA02_NPR_7123_1D.pdf in results; SWEHB cites it "updated w/Change 2"). No 7123.1E found. Not verified on NODIS.
- **Newer edition**: none found; a 2025 NASA technical memorandum on the handbook appears in NTRS results (https://ntrs.nasa.gov/citations/20250004844) but is not a new edition.

## Elements useful as AI skills
- Process catalogue (17 processes, three sets) as a checklist scaffold – pointer: handbook ch. 2.1, 4–6 (secondary).
- Life-cycle gating with KDPs and milestone reviews – pointer: handbook ch. 3, NPR 7123.1 (secondary).
- Per-process input/activity/output pattern (process description + guidance) – structural pointer only.

## Proposed skills, agents and tools
- Systems-engineering planning skill: use `nasa-se-processes-corroboration.json` as a schema of process IDs; produce SEMP-style outlines, requirements traceability, review-readiness checklists.
- Validator script: check that a generated plan references each of the 17 process IDs and a review set, flagging "requires NPR 7123.1 check" for entry/exit criteria.
- Chapter-level sources: `nasa-se-design`, `nasa-se-realize`, `nasa-se-manage`.

## Limitations, applicability and copyright
- Everything above is secondary; do not quote or cite as read. Entry/exit criteria, tailoring rules and review sets differ by programme type and are set by NPR 7123.1/NPR 7120.5 – a human must check the current NODIS text.
- Handbook is NASA-specific guidance, not certification; adapt for non-NASA contexts.
- Possible third-party embedded material: link, do not redistribute figures.

## Re-check by
2027-04-13 – re-attempt primary access (nasa.gov PDF / NTRS); confirm current NPR 7123.1 letter and changes on NODIS; check for a Rev 3 handbook.
