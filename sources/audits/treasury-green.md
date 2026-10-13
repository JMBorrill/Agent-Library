# Source audit: `treasury-green`

| Field | Value |
|---|---|
| Source ID | `treasury-green` |
| Title (as verified) | The Green Book (2026) – reported subtitle "UK Government Guidance on Appraisal" (previous editions: "Appraisal and Evaluation in Central Government") (search snippets only) |
| Publisher / author | HM Treasury |
| Edition / version / effective date | 2026 edition, published 5 February 2026 (multiple secondary sources: gov.uk snippets, MajorProjects, New Civil Engineer 6 Feb 2026). Previous editions (incl. 2022) withdrawn and archived at The National Archives |
| Canonical URL (registry) | https://www.gov.uk/government/publications/the-green-book-appraisal-and-evaluation-in-central-government/the-green-book-2026 |
| URL(s) actually read | None (primary) |
| Access status | INACCESSIBLE |
| Access method | Blocked host; search-engine results only |
| Date checked | 2026-10-13 |
| Licence / reuse terms (as verified) | Not verified. GOV.UK content is normally under the Open Government Licence v3.0 unless stated otherwise (background; no result confirmed it for this page) |
| Normative status | Mandatory guidance for UK central government appraisal (HM Treasury); advisory/proportionate elsewhere |

## Access ledger
- `curl https://www.gov.uk/` and `https://assets.publishing.service.gov.uk/` -> `curl: (56) CONNECT tunnel failed, response 403`.
- WebFetch registry URL -> `getaddrinfo ENOTFOUND www.gov.uk`.
- WebSearch succeeded (5 queries). Redirect behaviour between URL variants could not be tested.

## Verified content
None.

## Secondary corroboration (not primary verification)
- **Existence/date**: 2026 edition dated 5 Feb 2026; described in gov.uk change log snippets as radically shorter and simpler, annexes largely merged into the core text, value for money and BCRs reframed, following the Green Book Review 2025 (https://www.gov.uk/government/publications/the-green-book-appraisal-and-evaluation-in-central-government snippet; https://www.newcivilengineer.com/latest/treasury-publishes-renewed-green-book-to-help-fund-projects-in-overlooked-areas-06-02-2026/). Evaluation guidance reportedly sits in the Magenta Book (HotPMO blog).
- **URL**: the search index returned `https://www.gov.uk/government/publications/the-green-book--2/the-green-book-2026` titled "The Green Book (2026)" and parent `https://www.gov.uk/government/publications/the-green-book--2`. The registry variant (`.../the-green-book-appraisal-and-evaluation-in-central-government/the-green-book-2026`) was NOT seen in any result; that parent page exists and lists the 2026 edition and withdrawn editions. Best evidence therefore favours the `the-green-book--2` URL as the HTML edition, but this is unconfirmed – a human should load both and record any redirect.
- **STPR/discounting**: Green Book supplementary guidance on discounting (asset dated Feb 2026, https://assets.publishing.service.gov.uk/media/698488ab2df808759a7bd70f/Green_Book_supplementary_guidance_-_discounting.pdf) states 3.5% real for years 0–30, 3.0% for 31–75, 2.5% thereafter (snippet). A Green Book Discount Rate Review (ToR 16 Dec 2025; Freeman & Groom report dated 30 June 2026) made recommendations that are explicitly not HM Treasury policy; one snippet of its findings describes a 3% rate decomposition that conflicts with the 3.5% STPR – unresolved. No adopted change found.
- **Five Case Model**: gov.uk snippet says the Green Book uses the five-case model per business case guidance; case names (strategic, economic, commercial, financial, management) from secondary sources.
- **Optimism bias / switching values**: not confirmed for the 2026 edition; only older supplementary optimism-bias guidance appeared.
- **OGL**: not confirmed.

## Elements useful as AI skills
Options appraisal workflow (long list -> shortlist -> preferred option), five-case business case structure, discounting at STPR schedule, risk/optimism adjustments, switching-value sensitivity analysis – all require primary confirmation for the 2026 text.

## Proposed skills, agents and tools
Appraisal skill with a parameter file (discount schedule with source + date, optimism-bias uplifts left blank until verified), NPV calculator script, five-case outline template. Flag "pending discount-rate review outcome".

## Limitations, applicability and copyright
UK public sector; proportionality expected. Discount rate may change following the 2026 review – re-check before every use. Licence assumed OGL but unverified.

## Re-check by
2026-12-13 – confirm canonical URL/redirect, OGL statement, STPR after discount rate review response, optimism-bias/switching-value guidance in 2026 edition.
