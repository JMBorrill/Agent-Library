# Source audit: `basel-credit`

| Field | Value |
|---|---|
| Source ID | `basel-credit` |
| Title (as verified) | Principles for the management of credit risk (Basel Committee on Banking Supervision) – search snippets |
| Publisher / author | Basel Committee on Banking Supervision (BCBS), Bank for International Settlements |
| Edition / version / effective date | Revised 30 April 2025, publication d595 (listed as current); consultation d591 Feb 2025; original 2000 version (publication number not confirmed; a result at https://bis.org/publ/bcbs54.htm is titled "Principles for the Management of Credit Risk") |
| Canonical URL (registry) | https://www.bis.org/publications/202504-guidelines-principles-management-credit-risk |
| URL(s) actually read | None (primary) |
| Access status | INACCESSIBLE |
| Access method | Blocked host; search-engine results only |
| Date checked | 2026-10-13 |
| Licence / reuse terms (as verified) | Not verified (BIS publications typically permit reproduction of short excerpts with attribution – background only) |
| Normative status | Supervisory guidance (principles for supervisors to evaluate banks); not directly binding – applied via national supervisors |

## Access ledger
- `curl https://www.bis.org/` -> `curl: (56) CONNECT tunnel failed, response 403`.
- WebFetch registry URL -> `getaddrinfo ENOTFOUND www.bis.org`.
- WebSearch succeeded (3 queries).

## Verified content
None.

## Secondary corroboration (not primary verification)
- Revised 30 April 2025 as d595 (https://www.bis.org/bcbs/publ/d595.htm snippet); aim: align with current Basel Framework and later guidance; revision not intended to change content or add topics.
- Four areas (2025 wording per snippet): suitable credit risk environment; sound credit-granting process; appropriate credit administration, measurement and monitoring; adequate controls over credit risk. The 2000 text used "appropriate credit risk environment".
- Changes: annex "Common sources of major credit problems" deleted (concentration risk covered by BCP Principle 19, Pillar 2 SRP, LEX); outdated/superseded provisions removed or revised; references updated to the consolidated Basel Framework (snippets of d591 and law-firm summaries https://finreg.aoshearman.com/BCBS-updates-principles-for-the-management-of-cre).
- Principle count: 17 in the 2000 version per third-party commentary; final 2025 count NOT confirmed. Sources differ on extent of change (BIS/law firms: technical; one consultancy: strengthened areas).

## Elements useful as AI skills
Credit-risk governance checklist organised by the four areas (no principle text reproduced).

## Proposed skills, agents and tools
Credit-policy review skill with an area-level checklist; principle-level items to be populated by a human from d595.

## Limitations, applicability and copyright
Jurisdiction-specific implementation (e.g. PRA/ECB) differs; principles are high-level. Do not invent principle text or numbering.

## Re-check by
2027-04-13 – read d595 PDF: confirm number of principles and grouping.
