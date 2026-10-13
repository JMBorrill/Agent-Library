# Source audit: `nist-ai`

| Field | Value |
|---|---|
| Source ID | `nist-ai` |
| Title (as verified) | NIST AI Risk Management Framework (AI RMF 1.0, NIST AI 100-1) and AI RMF Playbook; Generative AI Profile (NIST AI 600-1) (titles from search snippets) |
| Publisher / author | NIST |
| Edition / version / effective date | AI RMF 1.0, January 2023; AI 600-1, July 2024. Secondary sources report a revision in progress (no successor published per results) |
| Canonical URL (registry) | https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook |
| URL(s) actually read | None (primary) |
| Access status | INACCESSIBLE |
| Access method | Blocked hosts; official GitHub probe unsuccessful; search-engine results only |
| Date checked | 2026-10-13 |
| Licence / reuse terms (as verified) | Not verified (NIST US Government work – background only) |
| Normative status | Voluntary guidance; not law or certification (some third-party jurisdictions may reference it – not verified) |

## Access ledger
- `curl https://www.nist.gov/`, `https://airc.nist.gov/`, `https://nvlpubs.nist.gov/` -> `curl: (56) CONNECT tunnel failed, response 403`.
- WebFetch registry URL -> `getaddrinfo ENOTFOUND www.nist.gov`; WebFetch https://airc.nist.gov/airmf-resources/playbook/ -> `getaddrinfo ENOTFOUND airc.nist.gov`.
- Official GitHub: probed README of usnistgov/{AI-RMF-Playbook, ai-rmf-playbook, airc, AIRMF, ai-rmf, NIST-AI-RMF-Playbook, cprt} -> not found; usnistgov/oscal-content guessed paths (AI100-1, AI-RMF, AI_RMF, AI600-1 variants) -> 404. No official machine-readable source located.
- WebSearch succeeded (6 queries).

## Verified content
None.

## Secondary corroboration (not primary verification)
- Four functions GOVERN, MAP, MEASURE, MANAGE; GOVERN is cross-cutting.
- Category counts: GOVERN 6, MAP 5, MEASURE 4, MANAGE 4 (19 categories). Subcategory counts per third-party guides: 19/18/22/13 = 72 (https://neuraltrust.ai/blog/nist-ai-rmf-implementation-guide, https://docs.modulos.ai/frameworks/nist-ai-rmf/map). MEASURE=22 only implied.
- GOVERN 1–6 themes (paraphrase): policies/processes; accountability and training; workforce diversity/inclusion; risk-aware culture; engagement with AI actors; third-party/supply-chain risk.
- Seven trustworthiness characteristics: valid and reliable; safe; secure and resilient; accountable and transparent; explainable and interpretable; privacy-enhanced; fair with harmful bias managed (snippet attributed to https://airc.nist.gov/airmf-resources/airmf/3-sec-characteristics/ plus summaries).
- AI 600-1 names 12 GAI risks; confirmed in results: confabulation, CBRN information/capabilities, harmful bias, data privacy, human-AI configuration. Others not confirmed.
- AI 100-1 describes itself as a living document with formal community review expected no later than 2028 (snippet of nvlpubs PDF).
- Structure file: `sources/extracts/nist-ai-rmf-structure.json` – subcategory lists intentionally EMPTY.

## Elements useful as AI skills
Function/category scaffold for AI risk assessments; trustworthiness characteristics as an evaluation checklist; GAI risk list for LLM-system reviews.

## Proposed skills, agents and tools
AI-risk review skill using the category IDs as keys; a human must populate subcategory text from AI 100-1 Tables / Playbook. Validator flags any subcategory text without a primary citation.

## Limitations, applicability and copyright
No primary text read; do not quote titles. Third-party claims about mandatory status (e.g. EO 14110, rescinded) are outdated/unreliable. Re-verify counts.

## Re-check by
2027-01-13 – obtain AI 100-1 PDF/Playbook JSON from nist.gov/airc; check for AI RMF revision.
