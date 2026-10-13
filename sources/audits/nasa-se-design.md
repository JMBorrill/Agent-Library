# Source audit: `nasa-se-design`

| Field | Value |
|---|---|
| Source ID | `nasa-se-design` |
| Title (as verified) | NASA SE Handbook (NASA/SP-2016-6105 Rev 2), chapter 4.0 System Design Processes (title from search snippets only) |
| Publisher / author | NASA |
| Edition / version / effective date | Rev 2 (2016); see `nasa-se.md` |
| Canonical URL (registry) | https://www.nasa.gov/reference/4-0-system-design-processes/ |
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
4.1 Stakeholder Expectations Definition; 4.2 Technical Requirements Definition; 4.3 Logical Decomposition; 4.4 Design Solution Definition. Snippets describe the set as defining/baselining stakeholder expectations, generating/baselining technical requirements, decomposing requirements into logical and behavioural models, and converting requirements into a design solution; one snippet lists decomposition methods (function, time, behaviour, data flow, states, modes, architecture).
Evidence URLs per section: `sources/extracts/nasa-se-processes-corroboration.json`.

## Elements useful as AI skills
Stakeholder needs elicitation, requirements writing/quality checks, functional decomposition, design-option definition (structure only; detailed procedure text not read).

## Proposed skills, agents and tools
See `nasa-se.md`; use the section IDs above as stable keys in skill checklists.

## Limitations, applicability and copyright
Secondary only; do not quote. Confirm against the NASA PDF/web chapter and NPR 7123.1 before relying on detail.

## Re-check by
2027-04-13 – re-attempt primary access to the chapter page.
