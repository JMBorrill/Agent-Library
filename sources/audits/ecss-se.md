# Source audit: `ecss-se`

| Field | Value |
|---|---|
| Source ID | `ecss-se` |
| Title (as verified) | ECSS-E-ST-10C Rev.1 – Space engineering: System engineering general requirements (title from search snippets) |
| Publisher / author | European Cooperation for Space Standardization (ECSS), ESA Requirements and Standards Section |
| Edition / version / effective date | Rev.1, 15 February 2017 (snippets describe it as issue 3, revision 1; supersedes ECSS-E-ST-10C of 6 March 2009). No Rev.2 found |
| Canonical URL (registry) | https://ecss.nl/standard/ecss-e-st-10c-rev-1-system-engineering-general-requirements-15-february-2017/ |
| URL(s) actually read | None (primary) |
| Access status | INACCESSIBLE |
| Access method | Blocked host; search-engine results only |
| Date checked | 2026-10-13 |
| Licence / reuse terms (as verified) | Not read. Snippets of ecss.nl indicate site use requires registration and that downloading implies acceptance of the "ECSS License Agreement / Disclaimer"; the substantive licence terms were not seen |
| Normative status | Mandatory only when made applicable by contract (e.g. ESA/European space projects) after tailoring; otherwise reference |

## Access ledger
- `curl https://ecss.nl/` -> `curl: (56) CONNECT tunnel failed, response 403`.
- WebFetch registry URL -> `getaddrinfo ENOTFOUND ecss.nl`.
- WebSearch succeeded (2 queries).

## Verified content
None.

## Secondary corroboration (not primary verification)
- Rev.1 dated 15 Feb 2017; the 2009 edition is listed as cancelled/superseded by Rev.1 (snippets of https://ecss.nl/standard/ecss-e-st-10c-system-engineering-general-requirements/ and the PDF link https://ecss.nl/wp-content/uploads/2017/02/ECSS-E-ST-10C-Rev.1(15February2017).pdf).
- Change summary (snippet): implemented change requests, updated scope, a new normative reference to ECSS-E-AS-11 (TRL adoption notice), and "system engineering organisation" renamed "system engineering function".
- Scope (snippet): system-engineering implementation requirements for space systems and products, with applicability pre-tailored by product type in a table (clause 7 per snippet; not independently verified – do not cite clause numbers).
- Access (snippets of https://ecss.nl/standards/active-standards/ and site pages): registration requested; downloads subject to the ECSS License Agreement/Disclaimer; ESA disclaims liability.
- No ECSS-E-ST-10C Rev.2 seen in results (absence of evidence only).

## Elements useful as AI skills
Structural only: requirement-oriented SE framework with pre-tailoring by product type, and document requirement definitions (DRDs) as artefact templates – content not read; no clause numbers asserted.

## Proposed skills, agents and tools
Supplement to `nasa-se` for European space contexts: a tailoring-matrix template and an artefact checklist whose rows must be filled by a human from the licensed standard. Do not embed ECSS text.

## Limitations, applicability and copyright
Licence terms unread; assume no redistribution of text/DRDs. Requires a registered human download to verify clauses and confirm no newer revision.

## Re-check by
2027-04-13 – check ecss.nl active standards list for a newer revision; read licence agreement.
