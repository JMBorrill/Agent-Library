# Source audit: `shape-up`

| Field | Value |
|---|---|
| Source ID | `shape-up` |
| Title (as verified) | Not verified from primary. Secondary sources: "Shape Up: Stop Running in Circles and Ship Work that Matters" by Ryan Singer. |
| Publisher / author | Ryan Singer / Basecamp — UNVERIFIED (secondary only) |
| Edition / version / effective date | Unverified (no edition or date read) |
| Canonical URL (registry) | https://basecamp.com/shapeup |
| URL(s) actually read | None from the primary source |
| Access status | INACCESSIBLE (primary); content claims below are SECONDARY only |
| Access method | WebFetch and curl attempted (both failed); search-engine results only |
| Date checked | 2026-10-13 |
| Licence / reuse terms (as verified) | UNVERIFIED. Secondary sources say the book is free to read online at basecamp.com/shapeup with no signup; no copyright notice was read. Assume all rights reserved by the author/publisher: do not mirror, copy chapters or redistribute unofficial PDFs; paraphrase and link only. |
| Normative status | Advisory — a product-development methodology from one company; no regulatory or standard status. |

## Access ledger
- WebFetch `https://basecamp.com/shapeup` — failed: `getaddrinfo ENOTFOUND basecamp.com`.
- curl `https://basecamp.com/shapeup` — `curl: (56) CONNECT tunnel failed, response 403`.
- No official GitHub/raw mirror of the book is known; none was probed (unofficial mirrors would not count as primary and could breach copyright).
- WebSearch (4 queries) — results were mostly third-party summaries, vendor blogs and AI-skill listing pages; one result URL pointed at a book appendix page (https://Basecamp.com/shapeup/4.0-appendix-01) but its content was not read.

## Verified content
None. No text from the book was read in this session.

## Secondary corroboration (not primary verification)
All items SECONDARY; wording is ours; several summaries come from low-quality sources (AI-skill listings) and must be checked against the book.

- Shaping has four steps: set boundaries (decide appetite), rough out the elements, address risks and rabbit holes, write the pitch. Results: https://tao.lifeitself.org/shapeup ; https://danlebrero.com/2021/06/16/shape-up-summary/ ; https://reflectoring.io/book-review-shape-up/ ; https://writesoftwarewell.com/highlights/shape-up ; https://www.rubick.com/wiki/process/shape-up
- Appetite: time the idea is worth, set before designing. Small batch ≈ team of 2–3 for one to two weeks; big batch ≈ same size team for six weeks. Results: https://tao.lifeitself.org/shapeup ; https://danlebrero.com/2021/06/16/shape-up-summary/ . (One AI-skill page used a different S/M/L scheme — https://skillsmp.com/creators/asafelobotomy/xanadassistant/packs-shapeup-skills-shapeuppitching — conflicting, not reliable.)
- Pitch ingredients: problem, appetite, solution, rabbit holes, no-gos. Results: same as above plus https://skillsmp.com/creators/asafelobotomy/xanadassistant/packs-shapeup-skills-shapeuppitching
- Cycles of six weeks followed by a two-week cool-down (bugs, exploration, shaping next work). Result: https://claudeskills.info/skills/guia-matthieu/clawfu-skills/shape-up/ ; https://agentskills.so/skills/wdavidturner-product-skills-shape-up (weak sources).
- Betting table: where shaped pitches are chosen for the next cycle. Result: https://www.indiehackers.com/post/has-anyone-experienced-basecamp-s-shape-up-edae90c1a0 ; https://claudeskills.info/skills/guia-matthieu/clawfu-skills/shape-up/
- Circuit breaker: unfinished work does not automatically get extended at the end of the cycle; it must be re-bet. Result: https://claudeskills.info/skills/guia-matthieu/clawfu-skills/shape-up/ (weak source).
- Scopes and hill charts: projects are broken into scopes; each scope is plotted on a hill chart where uphill means still figuring out unknowns and downhill means execution. Results: https://www.process.st/shape-up/ ; https://www.prodpad.com/?p=85944 ; https://www.curiouslab.io/blog/hill-chart-benefits-and-why
- Not corroborated: the phrase "imagined vs discovered tasks" (no result supported it).
- Book is free online at basecamp.com/shapeup; Basecamp states it built Basecamp to implement the method (appendix, per search snippet). Results: https://adactio.com/tags/shapeup ; https://Basecamp.com/shapeup/4.0-appendix-01

## Elements useful as AI skills
(Pending primary verification; pointers are to the book's unread chapters.)
- Pitch-writing template: problem / appetite / solution / rabbit holes / no-gos.
- Shaping procedure: appetite first, then rough elements (e.g. breadboarding, fat-marker sketches — names not verified here), then risk review.
- Cycle planning: betting table decision record, circuit-breaker rule, cool-down allocation.
- Progress reporting: scope list plus hill-chart position per scope.

## Proposed skills, agents and tools
- Skill "write a Shape Up-style pitch" with a pitch schema (five fields) and a checklist that appetite is stated before the solution and no-gos are explicit.
- Skill "scope mapping and hill-chart status" (text-based hill position per scope).
- Do not attribute exact terminology or quotes to the book until verified.

## Limitations, applicability and copyright
- No primary access; everything is secondary, some from low-reliability AI-generated listing sites. A human must read basecamp.com/shapeup to confirm terms, cycle lengths, team sizes and chapter names.
- Methodology reflects one company's practice; practitioner reports note teams adapt it heavily.
- Copyright: book is free to read but not openly licensed as far as can be told (licence not verified). Do not mirror, bulk-quote or host PDFs; paraphrase and link.

## Re-check by
2026-11-13 — retry access to basecamp.com/shapeup; verify the concept list, chapter names and copyright notice; downgrade or remove any secondary claim that the book does not support.
