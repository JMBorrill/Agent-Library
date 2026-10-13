# Using the NIST AI RMF Playbook

Source: `nist-ai-playbook` (NIST AI RMF Playbook, 142 numbered pages; pinned PDF has 147 pages;
printed "N of 142" = PDF page - 3).

## What it is (About the Playbook, PDF p. 4)

- Suggested actions for achieving the outcomes in the AI RMF Core (Tables 1-4), aligned to each
  subcategory.
- "neither a checklist nor set of steps to be followed in its entirety"; suggestions are voluntary -
  borrow as many or as few as apply.

## Structure of each subcategory entry

1. Heading (e.g. `GOVERN 1.1`) and the outcome statement. Some statements are worded slightly
   differently from AI RMF 1.0 Tables 1-4 (22 of 72, listed in the catalog's
   `parameters.statement_wording_differs_from_ai_rmf`); cite the AI RMF wording for the outcome.
2. **About** - explanatory prose (not in the catalog; read the PDF).
3. **Suggested Actions** - bullets; in the catalog as `<ID>/action-N`, with nested bullets in
   `sub_actions` and any lead-in sentence (e.g. GOVERN 1.2 "Organizational AI risk management policies
   should be designed to:") in `lead_in`.
4. **Transparency & Documentation** - "Organizations can document the following" questions; in the
   catalog as `<ID>/question-N`. Use these as interview/evidence prompts.
5. AI Transparency Resources and References (not in the catalog).

## Page map (PDF pages)

| Function | Pages | First subcategory page |
|---|---|---|
| GOVERN | 5-36 | GOVERN 1.1, p. 6 |
| MANAGE | 37-60 | MANAGE 1.1, p. 38 |
| MAP | 61-96 | MAP 1.1, p. 62 |
| MEASURE | 97-147 | MEASURE 1.1, p. 98 |

Note the Playbook orders functions GOVERN, MANAGE, MAP, MEASURE.

## How to use it in deliverables

- `python -m agentlib ai-rmf show "MAP 5.1"` prints the outcome, actions (with PDF page) and questions.
- Cite actions as `[nist-ai-playbook MAP 5.1/action-2, p. <page>]` using the page the tool prints.
- In a gap plan, pick the actions that close the gap and explain adaptation to the context.
- In an assessment interview, turn the documentation questions into evidence requests.
- Do not present Playbook actions as mandatory requirements, and do not count "actions adopted" as a
  maturity score.

## Extraction notes

Catalog counts: 460 top-level suggested actions (many with nested sub-actions) and 294 documentation
questions across all 72 subcategories. Source typos are preserved (e.g. "stablish" in MANAGE 2.2,
PDF p. 46; "theAI" in MEASURE 2.3/2.5 questions). Text was cross-checked between pdftotext and pypdf.
