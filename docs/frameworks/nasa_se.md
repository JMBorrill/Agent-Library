# NASA Systems Engineering Handbook (`nasa_se`)

Source id `nasa-se`: NASA Systems Engineering Handbook, NASA/SP-2016-6105 Rev 2 (2016), pinned at
`sources/pdfs/nasa-systems-engineering-handbook-rev2.pdf` (356 pages, sha256 checked by the extractor).
Printed page = PDF page - 13 from PDF p. 14 onward (asserted on every page footer during extraction).

## Components

| Component | Path |
|---|---|
| Extraction script | `scripts/extract/nasa_se.py` (`--check` verifies committed catalogs are reproducible) |
| Catalogs | `catalog/nasa-se-processes.json` (17 items), `catalog/nasa-se-lifecycle.json` (38 items: 7 phases, 6 KDPs, 16 reviews, 9 TRLs), `catalog/nasa-requirements-checklist.json` (72 items: 55 Appendix C checklist items, 7 metadata, 4 verification methods, 6 validation steps) |
| Tools / CLI | `agentlib/frameworks/nasa_se.py` -> `python -m agentlib nasa-se ...` |
| Tests | `tests/test_nasa_se.py` |
| Skills | `skills/nasa-systems-engineering/`, `skills/requirements-engineering/` |
| Agents | `agents/systems-engineer.md`, `agents/requirements-engineer.md` |
| Evals | `evals/nasa-systems-engineering/` (5 cases), `evals/requirements-engineering/` (5 cases) |

## CLI

```sh
python -m agentlib nasa-se lint-requirements reqs.csv [--format table|json|markdown] [-o FILE]
        [--fail-on error|warning|info|never] [--min-severity ...] [--no-rationale] [--no-verification]
python -m agentlib nasa-se trace reqs.yaml [--external NGO-] [--top-level system] [--matrix] [--format ...]
python -m agentlib nasa-se review-checklist PDR [--project NAME] [--format markdown|json] [-o FILE]
python -m agentlib nasa-se trade-study trade.yaml [--close-margin 0.05] [--format markdown|json]
python -m agentlib nasa-se processes [--group G] [--id N|slug|section] [--format table|markdown|json]
python -m agentlib nasa-se lifecycle [--kind phase|kdp|review|trl] [--format ...]
python -m agentlib nasa-se req-checklist [-o FILE]
```

Exit codes: `lint-requirements` 1 when a finding at/above `--fail-on` exists; `trace` 1 on any trace error;
2 for unreadable input or unknown ids; otherwise 0.

Input formats for requirement sets: CSV/TSV with a header, YAML/JSON (list, `{requirements: [...]}` or
`{id: text | {...}}`), Markdown pipe tables, or Markdown lists (`- **ID**: text` with indented
`Rationale:`, `Verification:`, `Parent:` sub-bullets). Column aliases include `id/req id/requirement no`,
`text/requirement/shall statement`, `rationale`, `verification/verification method/method`,
`parent/traced from`, `children`, `level`, `status`. Parent value `self-derived` marks self-derived
requirements (6.2.1.2.3).

Graders for eval suites: `grade_requirements_quality`, `grade_verification_methods`, `grade_trace`,
`grade_review_phase_consistency`, `grade_process_coverage`, `grade_decision_matrix`.

## Extraction approach and fidelity

- Every catalog page number is computed by locating an anchor string in the `pdftotext -layout` text; the
  script fails if an anchor is missing or a count changes (17 processes with 4/5/8 per group; activity
  heading counts per process; 7 phases, 6 KDPs, 16 reviews, 9 TRLs; 55 Appendix C items; unverifiable and
  ambiguous term lists present in the item text).
- Processes: purposes paraphrased; input/output labels are the handbook's bullet labels (asserted present in
  each section); activity titles are the verbatim `X.Y.1.2.n` headings.
- Life cycle: phase/review purposes, timing and results are paraphrases of Table 2.2-1, the phase blue boxes
  and Table 6.7-1; NPR 7123.1 Appendix G table numbers are verified on the page. Table 3.0-1 (product
  maturity) and Figure G.4-1 (TRLs) are graphics; their cells were transcribed from page renders and the
  row labels / figure caption are cross-checked against the text layer.
- Appendix C items: verbatim (whitespace and quotes normalised), sliced between ordered anchors.

## Assumptions and design decisions

- Catalog item ids are library-assigned slugs (processes), acronyms (reviews), `KDP-A`... and `TRL-n`;
  Appendix C items have no handbook numbers, so ids like `c4-clarity-unambiguous` are catalog-assigned.
- TRR is not a row of Table 6.7-1; it is included from the Section 5.3 note (PDF p. 122) and glossary (PDF
  p. 246) with criteria "tailored by the project".
- Linter severities are a library judgement: violations the handbook states as rules (no "shall",
  multiple "shall", ambiguous/unverifiable terms, missing/duplicate ID, invalid method) are errors;
  stylistic or heuristic items (passive voice, compound statement, "-ly"/"-ize" words, negative statement,
  TBD, missing rationale/method) are warnings; TBR and missing tolerance are info. A small exception list
  avoids flagging established names such as "safe mode".
- `trade-study` uses a weighted sum of raw scores with normalised weights; the 5% "closely ranked" margin is
  a library default, not a handbook value.
- Top level for `trace` is `--top-level`, else the level of the first requirement; without levels, a
  requirement with children and no parent is a root.

## Known gaps

- NPR 7123.1 Appendix G entrance/success criteria are not bundled, so review checklists reference the table
  number only. The NASA Expanded Guidance for SE (frequently referenced by the handbook) is not in the pack.
- IT (NPR 7120.7), R&T (NPR 7120.8) and software (NPR 7150.2) life cycles, program-level review variants
  (PSR/PIR) and the Appendix N peer review guidance are not cataloged.
- Appendices E (validation matrix), H (integration plan), I (V&V plan outline), K, L, M, P, R and T are cited
  in skills but not cataloged.
- The linter is lexical; it cannot judge technical correctness, level, feasibility or implementation bias.
