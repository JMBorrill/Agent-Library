# NIST AI RMF 1.0 + Playbook - implementation notes

Module: `agentlib/frameworks/ai_rmf.py` (CLI `python -m agentlib ai-rmf ...`)
Catalogs: `catalog/nist-ai-rmf.json`, `catalog/nist-ai-rmf-playbook.json`
Extraction: `scripts/extract/ai_rmf.py` (`--check` verifies the committed catalogs are reproducible)
Skill: `skills/nist-ai-rmf/` - Agents: `agents/ai-risk-assessor.md`, `agents/ai-governance-advisor.md`
Evals: `evals/nist-ai-rmf/` - Tests: `tests/test_ai_rmf.py`

## Sources

| Source id | Document | Pinned file | Pages |
|---|---|---|---|
| `nist-ai` | NIST AI 100-1, AI RMF 1.0 (January 2023) | `sources/pdfs/nist-ai-rmf-1-0.pdf` | 48 (printed page = PDF page - 5 from Part 1) |
| `nist-ai-playbook` | NIST AI RMF Playbook (142 numbered pages) | `sources/pdfs/nist-ai-rmf-playbook.pdf` | 147 (printed "N of 142" = PDF page - 3) |

## Catalog contents

`nist-ai-rmf` (fidelity `verbatim-normalised-whitespace`):
- `groups`: 4 functions (`kind: function`, paraphrased `summary`, section start page) and 19 categories
  (`kind: category`, verbatim statement as `title`, `parent` = function).
- `items`: 72 subcategories (`id` e.g. `GOVERN 1.1`, `function`, `group` = category, verbatim `text`,
  `citation.pdf_page`, `printed_page`, `section` e.g. `5.1 Table 1`).
- `parameters`: per-function counts, the 7 trustworthy characteristics (id, section 3.x, name,
  paraphrased summary, page), profile summary (Section 6), risk response options (MANAGE 1.3).

Counts asserted in the extraction script: GOVERN 6 categories / 19 subcategories (1.1-1.7, 2.1-2.3,
3.1-3.2, 4.1-4.3, 5.1-5.2, 6.1-6.2); MAP 5 / 18; MEASURE 4 / 22; MANAGE 4 / 13; total 19 / 72;
ids are contiguous per category; spot checks of verbatim text.

`nist-ai-rmf-playbook` (fidelity `verbatim-normalised-whitespace`):
- 460 suggested actions (`<SUB>/action-N`; nested bullets in `sub_actions`, lead-in text in
  `lead_in`) and 294 transparency & documentation questions (`<SUB>/question-N`), all 72
  subcategories covered, each with the PDF page where the bullet starts.
- `parameters.subcategories`: per subcategory the Playbook start page, the Playbook's statement and
  counts. `parameters.statement_wording_differs_from_ai_rmf` lists the 22 subcategories whose Playbook
  statement differs in wording from the AI RMF 1.0 tables (e.g. GOVERN 1.2 omits "and practices").
- Not reproduced: "About" prose, AI Transparency Resources, References.

## Extraction method

AI RMF tables are two-column (Categories | Subcategories). Full-page `pdftotext -layout` sometimes
separates the columns by a single space, so the script uses pdfplumber only for geometry (x of the
"Subcategories" header, table top/bottom from the header, "Continued on next page" and the next
section heading) and asserts that no word straddles the column boundary; it then runs
`pdftotext -layout` on each cropped column. End-of-line hyphenation from the justified LaTeX layout is
removed except for real compounds (`context-specific`, `context-relevant`), verified by reading.

The Playbook is single-column, ragged-right; line-end hyphens are real compounds (e.g. `third-party`)
and are kept. Bullets at indentation <= 2 are top-level actions; deeper bullets are sub-actions.

## Font-extraction check (Playbook)

The brief warned of font-extraction issues. Word-sequence similarity between `pdftotext` and `pypdf`
was >= 0.95 on every page except the cover (p. 1, decorative); pages 4 and 60 differ only in word
order (0.958 / 0.961). No `(cid:...)` glyphs or missing text were found; pdfplumber agrees on spot
checks. **Source typos are preserved, not corrected:** "stablish" (MANAGE 2.2, PDF p. 46), "theAI"
(MEASURE 2.3 / 2.5 questions), "non- measurement" (MEASURE 1.1), "consider, non-AI solutions"
(MAP 1.1). No content was inferred or filled in. No gaps recorded (`parameters.gaps` is empty).

## Tools

| Command | Purpose |
|---|---|
| `ai-rmf list [--function FN] [--format json] [--full]` | List subcategories with PDF pages |
| `ai-rmf show <id> [--format md\|json] [--no-questions]` | Outcome + Playbook actions/questions. Accepts `GOVERN 1.1`, `gv-1.1`, `MS 2.11` |
| `ai-rmf characteristics` | The 7 trustworthy characteristics |
| `ai-rmf profile-template [--functions ...] [--format md\|csv\|yaml] [--system] [-o]` | Current/target worksheet |
| `ai-rmf check-profile <file> [--functions ...] [--json]` | Validation + gap analysis by function/category; exit 1 on errors |
| `ai-rmf register-template [--format md\|csv\|yaml]` | Risk register template |
| `ai-rmf check-register <file> [--json]` | Register validation; exit 1 on errors |
| `ai-rmf scan <file> [--json]` | Subcategory ids referenced per function; exit 1 on invalid ids |

Inputs: YAML/JSON (a list, or a mapping with `subcategories:` / `risks:`), CSV, or Markdown (largest
pipe table). Headers are normalised (case, spaces, punctuation) and common aliases are accepted.

Graders for eval suites: `grade_valid_subcategory_ids`, `grade_function_coverage`,
`grade_trustworthy_characteristics`, `grade_playbook_refs`, `grade_register_table`,
`grade_profile_table`.

## Library conventions (not from NIST)

The AI RMF prescribes no risk tolerance (Section 1.2.2, PDF p. 12), no thresholds and no profile
template (PDF p. 39). The following are conventions of this library and are labelled as such in
outputs:
- Profile status scale: not-implemented < partially-implemented < largely-implemented < implemented,
  plus not-applicable; evidence required for `implemented`.
- Register scales: likelihood 1-5, impact 1-5, rating bands on L x I: 1-4 low, 5-9 medium, 10-16 high,
  20-25 critical. Grounding: Playbook GOVERN 1.3 "About" describes risk ≈ impact x likelihood on a
  qualitative or quantitative scale (Playbook PDF p. 9). Inherent/residual mismatches with the matrix
  are warnings (organisations may use their own matrix).
- Register rules (errors): required fields; valid ids and characteristics; residual > inherent needs
  `residual_justification`; `accept` needs `accepted_by`; residual high/critical needs `escalated_to`
  or `accepted_by`. Treatment vocabulary is from MANAGE 1.3.
- Characteristic-to-MEASURE mapping (2.5-2.11) follows the subcategory wording; "related"
  subcategories in the skill reference are library judgement.

## Known gaps / limitations

- Only AI RMF 1.0 and the bundled Playbook snapshot; the Generative AI Profile (NIST AI 600-1) and
  crosswalks are not catalogued.
- Playbook "About" text and references are not extracted.
- `check-profile` cannot judge whether evidence is adequate - only that it is recorded.
- Grader `grade_trustworthy_characteristics` uses phrase patterns (e.g. "secure and resilient");
  paraphrases such as "robust to attack" are not detected.
