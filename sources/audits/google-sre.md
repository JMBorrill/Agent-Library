# Source audit: `google-sre`

| Field | Value |
|---|---|
| Source ID | `google-sre` |
| Title (as verified) | Site Reliability Engineering: How Google Runs Production Systems (2016); companion The Site Reliability Workbook (2018) (titles from search snippets) |
| Publisher / author | Google; O'Reilly Media (eds. Beyer, Jones, Petoff, Murphy) |
| Edition / version / effective date | 1st edition 2016 (registry says 2017 – O'Reilly listing in results shows 2016/2017 printings); Workbook 2018 |
| Canonical URL (registry) | https://sre.google/sre-book/table-of-contents/ |
| URL(s) actually read | None (primary) |
| Access status | INACCESSIBLE |
| Access method | Blocked host; search-engine results only |
| Date checked | 2026-10-13 |
| Licence / reuse terms (as verified) | NOT verified. CC BY-NC-ND 4.0 for the online book is the registry's claim and common background knowledge, but no search result this session confirmed it |
| Normative status | Advisory industry practice |

## Access ledger
- `curl https://sre.google/` -> `curl: (56) CONNECT tunnel failed, response 403`.
- WebFetch https://sre.google/sre-book/table-of-contents/ -> `getaddrinfo ENOTFOUND sre.google`.
- No official Google GitHub copy of the book is known; none probed.
- WebSearch succeeded (5 queries).

## Verified content
None.

## Secondary corroboration (not primary verification)
SRE book (snippets of https://sre.google/sre-book/table-of-contents/ and O'Reilly/Open Library listings):
- Ch. 4 Service Level Objectives (Part II Principles); Ch. 6 Monitoring Distributed Systems; Ch. 8 Release Engineering; Ch. 13 Emergency Response; Ch. 14 Managing Incidents; Ch. 15 Postmortem Culture: Learning from Failure (Part III Practices). Four parts: Introduction, Principles, Practices, Management.
Workbook (snippets of https://sre.google/workbook/table-of-contents/ and https://sre.google/workbook/alerting-on-slos/):
- Ch. 2 Implementing SLOs; Ch. 3 SLO Engineering Case Studies; Ch. 5 Alerting on SLOs (Part I Foundations); Ch. 4 Monitoring; Ch. 9 Incident Response; Ch. 10 Postmortem Culture.
- Ch. 5 recommends multiwindow, multi-burn-rate alerts as its most refined option (short window ~1/12 of long window). Commonly cited starting values for a 99.9% SLO (blogs only: last9.io, pydantic.dev): page at 14.4x over 1h/5m (~2% budget), page at 6x over 6h/30m (~5%), ticket at 1x over 3d/6h (~10%). Treat numbers as unverified until read on sre.google.
- Licence: not confirmed by any result.

## Elements useful as AI skills
SLI/SLO/error-budget definition, burn-rate alert design, incident management roles, blameless postmortem structure, release engineering principles – chapter pointers above.

## Proposed skills, agents and tools
Reliability skill with: SLO spec schema (SLI, target, window), burn-rate calculator script (math is generic; thresholds configurable, not copied), postmortem template written in original words.

## Limitations, applicability and copyright
If CC BY-NC-ND 4.0 applies, adaptations (derivatives) of text are not permitted – link and paraphrase concepts only; no commercial reuse of text. Licence must be confirmed on sre.google footer by a human.

## Re-check by
2027-04-13 – confirm licence footer; read Workbook ch. 5 for burn-rate table.
