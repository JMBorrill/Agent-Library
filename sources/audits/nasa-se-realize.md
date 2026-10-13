# Source audit: `nasa-se-realize`

| Field | Value |
|---|---|
| Source ID | `nasa-se-realize` |
| Title (as verified) | NASA SE Handbook (NASA/SP-2016-6105 Rev 2), chapter 5.0 Product Realization (title from search snippets only) |
| Publisher / author | NASA |
| Edition / version / effective date | Rev 2 (2016); see `nasa-se.md` |
| Canonical URL (registry) | https://www.nasa.gov/reference/5-0-product-realization/ |
| URL(s) actually read | None (primary) |
| Access status | INACCESSIBLE |
| Access method | Blocked host; search-engine results only |
| Date checked | 2026-10-13 |
| Licence / reuse terms (as verified) | Not verified; see `nasa-se.md` |
| Normative status | Advisory NASA guidance; requirements in NPR 7123.1 |

## Access ledger
Same host as parent: www.nasa.gov -> `curl: (56) CONNECT tunnel failed, response 403`; WebFetch -> `getaddrinfo ENOTFOUND www.nasa.gov`. Full ledger in `nasa-se.md`.

## Verified content
None.

## Secondary corroboration (not primary verification)
5.1 Product Implementation; 5.2 Product Integration; 5.3 Product Verification; 5.4 Product Validation; 5.5 Product Transition, each with process description and guidance subsections (TOC snippets). Verification vs validation distinction not read in primary text.
Evidence URLs per section: `sources/extracts/nasa-se-processes-corroboration.json`.

## Elements useful as AI skills
Integration planning, verification matrices (method per requirement), validation planning, transition/hand-over checklists (structure only; detailed procedure text not read).

## Proposed skills, agents and tools
See `nasa-se.md`; use the section IDs above as stable keys in skill checklists.

## Limitations, applicability and copyright
Secondary only; do not quote. Confirm against the NASA PDF/web chapter and NPR 7123.1 before relying on detail.

## Re-check by
2027-04-13 – re-attempt primary access to the chapter page.
