# Source audit: `fca`

| Field | Value |
|---|---|
| Source ID | `fca` |
| Title (as verified) | FCA Handbook (sourcebooks MCOB, PRIN incl. PRIN 2A, CONC, DISP) |
| Publisher / author | Financial Conduct Authority (UK) |
| Edition / version / effective date | Living rulebook; point-in-time versions apply. Dates below are secondary |
| Canonical URL (registry) | https://handbook.fca.org.uk/handbook |
| URL(s) actually read | None (primary) |
| Access status | INACCESSIBLE |
| Access method | Blocked hosts (handbook.fca.org.uk, www.fca.org.uk); search-engine results only |
| Date checked | 2026-10-13 |
| Licence / reuse terms (as verified) | Not verified |
| Normative status | Mandatory for FCA-authorised firms within scope (rules marked R; guidance G is non-binding) |

## Access ledger
- `curl https://handbook.fca.org.uk/` and `https://www.fca.org.uk/` -> `curl: (56) CONNECT tunnel failed, response 403`.
- WebFetch https://handbook.fca.org.uk/handbook -> `getaddrinfo ENOTFOUND handbook.fca.org.uk`.
- WebSearch succeeded (3 queries).

## Verified content
None.

## Secondary corroboration (not primary verification)
- **MCOB / second charge**: FCA factsheet (https://www.fca.org.uk/publication/other/fs0040.pdf snippet) – from 21 March 2016 second charge mortgages (incl. pre-existing regulated loans) became subject to FCA mortgage rules (MCD implementation). MCOB 12.4/12.5 transitional coverage of pre-2016 second charge contracts seen in snippets of handbook MCOB 12. CORROBORATED (secondary).
- **MCOB 11.6 responsible lending**: snippets of https://handbook.fca.org.uk/handbook/MCOB/11/6.html show 11.6.2R requires an affordability assessment before entering into or varying a regulated mortgage contract and references Principle 12/PRIN 2A; a fragment suggested some carve-outs (e.g. bridging/second charge variants) – NOT resolved. PARTIAL.
- **Consumer Duty (Principle 12, PRIN 2A)**: in force 31 July 2023 for open products/services; 31 July 2024 for closed products; PRIN TP 1 transitional provisions; first board report by 31 July 2024 (FCA Dear CEO letter and Hogan Lovells snippets). CORROBORATED (secondary).
- **CONC** and **DISP** scope: NOT corroborated this session.
- FCA 2018 Dear CEO letter to second charge lenders on affordability concerns (snippet).

## Elements useful as AI skills
Affordability-assessment checklist (MCOB 11.6), Consumer Duty outcomes framing, complaint-handling flow (DISP – unverified).

## Proposed skills, agents and tools
Mortgage-conduct review skill that cites rule IDs only after human confirmation of current text; a point-in-time date field in every output; disclaimer that outputs are not compliance sign-off.

## Limitations, applicability and copyright
Rules change frequently; always use the Handbook point-in-time view. Never assert compliance without qualified sign-off. UK-only.

## Re-check by
2026-12-13 – read MCOB 11.6, PRIN 2A, CONC and DISP scope on handbook.fca.org.uk.
