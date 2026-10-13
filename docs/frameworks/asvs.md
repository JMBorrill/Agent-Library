# OWASP ASVS 5.0.0 - framework implementation notes

| Item | Value |
|---|---|
| Source id | `owasp-asvs` - `sources/pdfs/owasp-asvs-5-0-0-en.pdf` (123 pages, May 2025) |
| Licence | ASVS content (c) 2008-2025 The OWASP Foundation, CC BY-SA 4.0. The catalog is a derivative and keeps the attribution (`catalog.description`, `parameters.license`, `parameters.attribution`). |
| Catalog | `catalog/owasp-asvs-5.json` (catalog id `owasp-asvs-5`) |
| Extraction | `scripts/extract/asvs.py` (`--check` verifies the committed catalog is reproducible) |
| Tools | `agentlib/frameworks/asvs.py` -> `python -m agentlib asvs ...` |
| Tests | `tests/test_asvs.py` |
| Skill / agent | `skills/owasp-asvs/`, `agents/application-security-verifier.md` |
| Evals | `evals/owasp-asvs/` (6 cases, each with golden and negative output) |

## Catalog contents

- 17 chapters (V1-V17) and 80 sections as `groups` (`kind: chapter|section`, `parent`, `requirement_count`,
  citation of the heading page).
- 345 requirements as `items`: `id` (document form `<chapter>.<section>.<requirement>`, e.g. `1.2.5`, PDF
  p. 16), `canonical_ref` (`v5.0.0-1.2.5`, the version-qualified form the standard recommends), verbatim
  `text`, `level` (1/2/3), `chapter`, `group` (section) and `citation` (`pdf_page`, `printed_page` =
  pdf_page - 1, section).
- Level counts: L1 70, L2 183, L3 92. The standard states 70 L1 out of 345 (PDF p. 23). The extraction
  script asserts both numbers, plus 17 chapters, 80 sections, unique ids, contiguous numbering within
  each section, and that every text starts with "Verify".
- `levels`: definitions of L1-L3 with citations (PDF pp. 13-15), the cumulative rule (PDF pp. 13-14) and
  level-selection guidance (PDF p. 15).
- `parameters`: requirement counts (per level and cumulative), id format, assessment statuses, licence.

Fidelity: `verbatim-normalised-whitespace`. Whitespace is collapsed and U+2011 non-breaking hyphens are
rendered as `-`. Missing spaces after closing curly quotes (e.g. `‘SameSite’attribute`) come from the
PDF text layer and are kept as they are.

Not itemised: chapter control objectives, section introductions, notes under tables (e.g. the ORDER BY
note after V1.2), references, and the appendices (glossary and Appendix C cryptography standards).

## Tool behaviour and assumptions

- **Identifiers**: `1.2.5`, `V1.2.5`, `v5.0.0-1.2.5` and `ASVS 1.2.5` are accepted. Ids qualified with
  another version (e.g. `v4.0.3-...`) are rejected, because ids changed in 5.0 (PDF p. 21).
- **Levels are cumulative**: the standard says higher-level requirements are recommendations (PDF p. 13)
  and that L2 requires all L1 and L2 requirements (PDF p. 14). A Level N selection is therefore `level <= N`.
- **check-assessment**: accepts JSON, YAML or CSV, as a list, `{results: [...]}` or `{id: status}`.
  Statuses are `pass`, `fail`, `not-applicable` and `not-verified`, with common aliases (`n/a`,
  `passed` ...). Errors: unknown or duplicate ids, invalid status, missing in-scope requirement, `fail`
  without `finding_ref`/`finding`, `not-applicable` without `justification`/`rationale`. Requirements
  above the level or outside the chapter scope produce warnings and are excluded from the figures.
  Compliance % = pass / (in-scope - N/A). Exit 1 if the file is invalid or incomplete (missing or
  `not-verified`); `--strict` also exits 1 when any requirement fails. Exit 2 on usage or input errors.
- **map-findings**: deterministic lexical ranking. Requirement text is weighted 1.0 with BM25 length
  normalisation, section title 1.5 and chapter title 0.5, all weighted by IDF. Query bigrams found
  verbatim in the text add a bonus, but only when both tokens are uncommon. A small documented synonym
  table expands abbreviations (xss, idor, ssrf, jwt ...). `CWE_SECTION_HINTS` is **library-authored**:
  ASVS 5.0 dropped CWE mappings (PDF p. 23), so these hints are heuristic only. Output is labelled as
  suggestions.
- **Graders** (for evals): `grade_ids_exist`, `grade_level_appropriate`, `grade_levels_claimed`
  (inline `x.y.z (L2)` and Markdown tables with ID and Level columns), `grade_covers_scope`,
  `grade_chapters_exist` and `grade_json_assessment`. Version strings such as `5.0.0` and `4.0.3` are
  ignored, because no ASVS section is numbered 0.

## Known gaps

- Level-specific clauses inside requirement text ("for L2 and up ...") are kept in `text` but are not
  modelled as separate fields.
- No v4.0.3 to v5.0.0 mapping. OWASP publishes this separately, and it is not in the pinned PDF.
- The finding mapper is lexical. It cannot reason about semantics, so a human must confirm each mapping.
- The evidence checker (`agentlib/frameworks/evidence.py`) recognises only `V`-prefixed ids in prose
  (`V6.2.1`). The bare form `6.2.1` is not cross-checked there. The `asvs` graders handle both.
