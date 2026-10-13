# Source audit: `nasa-se-manage`

| Field | Value |
|---|---|
| Source ID | `nasa-se-manage` |
| Title (as verified) | NASA SE Handbook (NASA/SP-2016-6105 Rev 2), chapter 6.0 Crosscutting Technical Management (title from search snippets only) |
| Publisher / author | NASA |
| Edition / version / effective date | Rev 2 (2016); see `nasa-se.md` |
| Canonical URL (registry) | https://www.nasa.gov/reference/6-0-crosscutting-technical-management/ |
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
6.1 Technical Planning; 6.2 Requirements Management; 6.3 Interface Management; 6.4 Technical Risk Management; 6.5 Configuration Management; 6.6 Technical Data Management; 6.7 Technical Assessment; 6.8 Decision Analysis. Snippets: 6.1 is the first of eight technical management processes with extensive planning early in Pre-Phase A; 6.3 helps control development when work is divided among parties; 6.4 frames risk via scenarios, likelihoods and consequences and refers to the separate NASA Risk Management Handbook.
Evidence URLs per section: `sources/extracts/nasa-se-processes-corroboration.json`.

## Elements useful as AI skills
Planning templates, interface control documents, risk registers (scenario/likelihood/consequence), CM baselines, technical reviews, decision matrices (structure only; detailed procedure text not read).

## Proposed skills, agents and tools
See `nasa-se.md`; use the section IDs above as stable keys in skill checklists.

## Limitations, applicability and copyright
Secondary only; do not quote. Confirm against the NASA PDF/web chapter and NPR 7123.1 before relying on detail.

## Re-check by
2027-04-13 – re-attempt primary access to the chapter page.
