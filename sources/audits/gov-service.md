# Source audit: `gov-service`

| Field | Value |
|---|---|
| Source ID | `gov-service` |
| Title (as verified) | Not verified from primary. Secondary results title the pages "Service Standard", "How the discovery phase works", etc. under gov.uk/service-manual. |
| Publisher / author | Government Digital Service (GDS) — UNVERIFIED (inferred from repo ownership `alphagov` and secondary results) |
| Edition / version / effective date | Unverified. Secondary sources state the current 14-point Service Standard replaced the 18-point Digital Service Standard from 1 July 2019. |
| Canonical URL (registry) | https://www.gov.uk/service-manual |
| URL(s) actually read | Primary pages: none. GitHub (context only): `raw.githubusercontent.com/alphagov/service-manual-publisher/main/README.md`, `.../service-manual-frontend/main/README.md`, `.../govuk-content-schemas/main/README.md`, `.../publishing-api/main/content_schemas/examples/service_manual_service_standard/frontend/service_manual_service_standard.json` |
| Access status | INACCESSIBLE (primary); content claims below are UNVERIFIED / secondary only |
| Access method | Attempted WebFetch and curl (both failed); GitHub raw files (tooling repos and a test fixture only); search-engine results |
| Date checked | 2026-10-13 |
| Licence / reuse terms (as verified) | UNVERIFIED. GOV.UK content is commonly published under the Open Government Licence v3.0, but no Service Manual page or footer was read in this session, and the search did not surface a licence statement. Treat OGL v3.0 as a claim to confirm. |
| Normative status | Contextual: secondary sources describe the Service Standard as the standard UK central-government services are assessed against (GDS assessments); the wider Service Manual is guidance. Not verified from primary. |

## Access ledger
- WebFetch `https://www.gov.uk/service-manual/service-standard` — failed: `getaddrinfo ENOTFOUND www.gov.uk`.
- curl `https://www.gov.uk/service-manual/service-standard` — `curl: (56) CONNECT tunnel failed, response 403`.
- curl `https://www.gov.uk/api/content/service-manual/service-standard` (Content API) — same CONNECT 403.
- `alphagov/service-manual-publisher` README (main and master) — 200. States this app publishes and maintains gov.uk/service-manual and, with Service Manual Frontend, replaced the earlier Jekyll-based `government-service-design-manual`. Content lives in the publisher's database, not in the repo, so no guidance text is obtainable from it.
- `alphagov/service-manual-frontend` README — 200. States the app is retired and service manual pages are rendered by `government-frontend`.
- `alphagov/govuk-content-schemas` README — 200. States schemas merged into `publishing-api`; repo archived.
- `publishing-api/.../examples/service_manual_service_standard/frontend/service_manual_service_standard.json` — 200 (also present in archived govuk-content-schemas). It is a schema test fixture: `public_updated_at` 2016-06-30, child points titled in the OLD 18-point style (e.g. "1. Understand user needs", "3. Have a multidisciplinary team"), poster URL `example.com`. NOT authoritative for current content; recorded only to prevent mistaken reuse.
- `alphagov/government-frontend`, `alphagov/frontend` READMEs — 200 (rendering apps; no content).
- No public GitHub repository holding current Service Manual prose was found.

## Verified content
None of the Service Manual's guidance content was verified. The only verified facts are about tooling (from READMEs above): Service Manual Publisher publishes gov.uk/service-manual; Service Manual Frontend is retired; content schemas now live in publishing-api.

## Secondary corroboration (not primary verification)
All items below are SECONDARY (search-engine result summaries and third-party/departmental pages). Do not cite as verified.

- Service Standard has 14 points, effective from 1 July 2019, replacing an 18-point version. Results: https://www.civilserviceworld.com/articles/news/streamlined-gds-service-standard-removes-need-ministerial-tests ; https://www.publictechnology.net/articles/news/streamlined-gds-service-standard-removes-need-ministerial-tests ; https://service-manual.nhs.uk/service-standard ; https://gov.uk/service-manual/service-assessments/pre-july-2019-digital-service-standard
- Point names as reported by search summaries (numbering for 3, 5 and 8 inferred from the order reported, not confirmed):
  1. Understand users and their needs; 2. Solve a whole problem for users; 3. Provide a joined up experience across all channels; 4. Make the service simple to use; 5. Make sure everyone can use the service; 6. Have a multidisciplinary team; 7. Use agile ways of working; 8. Iterate and improve frequently; 9. Create a secure service which protects users' privacy; 10. Define what success looks like and publish performance data; 11. Choose the right tools and technology; 12. Make new source code open; 13. Use and contribute to open standards, common components and patterns; 14. Operate a reliable service.
  Results: https://www.gov.uk/service-manual/service-standard (listed, not read); https://www.gov.uk/service-manual/service-standard/point-4-make-the-service-simple-to-use ; https://apply-the-service-standard.education.gov.uk/service-standard/9-create-a-secure-service ; https://www.digital.mod.uk/service-manual/meet-the-standard ; https://www.pega.com/system/files/resources/2026-08/Pega%20and%20GDS%20Alignment%20White%20Paper.pdf
- NHS service standard contains the 14 GOV.UK points plus 3 health-specific points: https://service-manual.nhs.uk/service-standard
- Phases: discovery, alpha, beta (private or public), live, and retirement when users no longer need the service or it is not cost-effective. Results: https://www.gov.uk/service-manual/phases/beta ; https://www.gov.uk/service-manual/phases/live ; https://digitalpublicservices.gov.wales/guidance-and-standards/service-manual/delivering-services-agile-way/the-phases-of-agile-delivery . Sources disagree on which phases end in an assessment.
- Discovery: understand the problem before committing to build; learn about users, constraints (technical, legal), policy intent and improvement opportunities; break down assumptions; agree what is out of scope; do not start building in discovery; findings decide whether to move to alpha. Results: https://www.gov.uk/service-manual/phases/discovery ; https://www.gov.uk/service-manual/agile-delivery/how-the-discovery-phase-works
- User research in discovery: find likely users, what they are trying to do, how, and their problems; include disabled people and people with low digital skills; use existing evidence (analytics, call centre data) and interviews/observation. Results: https://www.gov.uk/service-manual/user-research/user-research-in-discovery ; https://www.gov.uk/service-manual/user-centred-design/user-needs.html

## Elements useful as AI skills
(Pending primary verification.)
- Service Standard self-assessment checklist (14 points) — pointer: gov.uk/service-manual/service-standard (unread).
- Phase-gate procedure: discovery exit questions (problem understood, users identified, assumptions tested, decision on alpha) — pointer: gov.uk/service-manual/phases/discovery (unread).
- User research planning prompts — pointer: gov.uk/service-manual/user-research (unread).

## Proposed skills, agents and tools
- Skill "discovery plan / discovery exit review" and "Service Standard readiness review" — do not ship until point wording is verified from gov.uk.
- Schema: `service-standard-points.json` with fields id, official title, URL, verified flag; populate only after primary access.
- Pair with `gov-design` for design-level checks (point 13 relates to common components and patterns — secondary).

## Limitations, applicability and copyright
- No primary text read; all content claims are secondary and may contain paraphrase errors or outdated numbering. A human (or a session with gov.uk access) must verify point titles, numbering and phase guidance.
- Applies to UK central government services; departmental variants (NHS, DfE, MOD, Welsh Government) adapt it and must not be conflated with the GOV.UK text.
- Licence (OGL v3.0) unverified; the 2016 fixture JSON in publishing-api is a test example, not content to reuse.

## Re-check by
2026-11-13 — retry primary access to gov.uk/service-manual (Service Standard, phases, discovery, user research pages) and the licence footer; replace secondary items with verified pointers.
