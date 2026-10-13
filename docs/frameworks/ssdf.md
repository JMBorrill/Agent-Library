# NIST SP 800-218 SSDF v1.1 - implementation notes

| Component | Path |
|---|---|
| Source PDF | `sources/pdfs/nist-ssdf-1-1.pdf` (source id `nist-ssdf`, 36 pages) |
| Catalog | `catalog/nist-ssdf.json` |
| Extraction script | `scripts/extract/ssdf.py` (`--check` verifies the catalog matches a fresh extraction) |
| Tools / CLI | `agentlib/frameworks/ssdf.py` -> `python -m agentlib ssdf ...` |
| Tests | `tests/test_ssdf.py` |
| Skill | `skills/nist-ssdf/` |
| Subagent | `agents/secure-development-reviewer.md` |
| Evals | `evals/nist-ssdf/` |

## Catalog

- **Groups (4)**: PO, PS, PW, RV with the Section 2 definitions (PDF p.13). Table 1 labels PS as "Protect
  Software (PS)" while Section 2 says "Protect the Software"; both are recorded (`title`, `table_label`).
- **Items**: 19 active practices and 42 active tasks (PO 5/13, PS 3/4, PW 8/16, RV 3/9 practices/tasks),
  plus 6 retired identifiers kept as `status: retired` with `moved_to` (PW.3, PW.3.1, PW.3.2, PW.4.3, PW.4.5,
  PW.5.2 - matching the Change Log on PDF p.36). Counts are asserted in the extraction script and tests.
- Each task has verbatim `text`, `practice`, `group`, `examples` (list, "Example n:" prefixes removed, order
  preserved so Ex.n = list index n), `references` (list of `{ref, text}` using the document's bibliography
  keys, e.g. `SP80053: SA-1, SA-8`), `citation.pdf_page` (row start), `printed_page` (= PDF page - 9),
  `pdf_pages` when the row continues onto the next page, and `formerly` where the task says "[Formerly ...]".
- `parameters.eo14028_4e_mapping`: Appendix A Table 2 (PDF p.33), 15 EO 14028 Section 4e subsections -> task ids
  (4e(ix) stored as its text "All practices and tasks consistent with a risk-based approach").
- **Fidelity**: `verbatim-normalised-whitespace`. Line breaks are joined with single spaces; a line ending in a
  hyphen is joined without a space (the table only breaks at real hyphens in compounds such as
  "open-source"). Superscript footnote markers (6-7pt) are dropped; footnote text below the separator rule is
  excluded. Reference strings are verbatim, including odd-looking values that are in the PDF (e.g.
  `SCTPC: MAINTAIN3`).

### Extraction method

Table 1 (PDF pp.14-28, landscape 1224x792) has fixed column borders on every page: Practices x 39-243,
Tasks 243-472, Examples 473-810, References 810-1186. Each column is cropped (above the footnote rule) and
read line by line with pdfplumber. Task rows start at `XX.n.n:` lines; example/reference lines are assigned
to the task whose start (page, y) precedes them (6pt tolerance for cell padding). Practices start at a bold
line after non-bold text; group header rows are bold `Name (XX)` lines. `pdftotext -layout` was insufficient
because the four columns interleave; generic pdfplumber table extraction merges cells unpredictably.
Sanity assertions: counts per group, 42 tasks, retired set, every active task has examples and references,
spot checks (PO.1.1 text, PO.1.3 formerly PW.3.1, PO.1.2 has 7 examples, RV.3.4 on p.27, Table 2 entries).

## CLI

```
python -m agentlib ssdf list [--group PW] [--all] [--format text|json]
python -m agentlib ssdf show <PO|PO.1|PO.1.1> [--format text|json]
python -m agentlib ssdf assessment-template [--format md|csv|yaml] [--out FILE]
python -m agentlib ssdf check-assessment FILE [--format md|json] [--today YYYY-MM-DD] [--max-gaps N]
python -m agentlib ssdf evidence-matrix FILE [--full-text] [--out FILE]
python -m agentlib ssdf map-pipeline FILE [--format md|json]
python -m agentlib ssdf pipeline-controls
```

Exit codes: 0 ok; 1 `check-assessment` found validation errors; 2 input error (unknown id, unreadable file).

### Assessment checking

Input: YAML/JSON (`{assessment: {...}, tasks: [...]}` or a list), CSV, or Markdown tables with `id` and
`status` columns. Errors: row without id, unknown id, retired id (suggests replacement), duplicate, missing
task, empty/invalid status, implemented without evidence, not-applicable without justification. Warnings:
partial without evidence, planned without owner/target date, unparseable or past target date.

Scoring (heuristic): coverage = (implemented + 0.5 x partial) / (tasks - not-applicable), overall / group /
practice. Conservative: unassessed, invalid, implemented-without-evidence and not-applicable-without-
justification rows earn 0 (and the latter stays in the denominator).

Prioritisation (heuristic, because SSDF says its practices are not prioritised, PDF p.12): status severity,
then count of specific EO 14028 4e subsections mapped by Appendix A Table 2, then document order. Tiers High /
Medium / Low are documented in `prioritise_gaps` and the skill's assessment-method reference.

### Pipeline mapping

`PIPELINE_RULES` maps ~40 control types (with aliases such as codeql, snyk, cosign, syft) to tasks. Every
mapping carries a basis: `example` (an SSDF notional example or task text names the control; the note cites
`<task> Ex.n`) or `interpretive`. `scheduled: true` adds RV.1.x support for scanners; `blocking: true` adds
PO.4.2 Ex.3. Tasks are reported as `supported`, `interpretive-support` or `no-supporting-control`, with
organisational tasks flagged. Output always states support != compliance.

## Graders (for `python` checks)

| Function | Purpose |
|---|---|
| `grade_ids_valid` | all `XX.n.n` ids exist in v1.1; retired ids fail unless `allow_retired` and described as retired/moved; `min` |
| `grade_practice_ids_valid` | same for practice ids |
| `grade_no_overclaim` | no un-negated "SSDF compliant/certified/fully compliant" claims |
| `grade_page_citations` | `PW.7.2 (p.23)`-style citations match the catalog page; `min` |
| `grade_assessment_numbers` | output states the tool's overall coverage for `fixture`, names High-tier gaps and validation-error tasks |
| `grade_pipeline_gaps` | output names >= `min_fraction` of unsupported technical tasks for `fixture` and does not present them as covered |

## Assumptions and known gaps

- Only SSDF v1.1 (Feb 2022). No later revisions or profiles.
- Group/practice/task pages are the PDF page where the row starts; long rows continue (recorded in `pdf_pages`).
- The pipeline rule set and the organisational-task list are this library's judgement, documented in the
  module and in `skills/nist-ssdf/references/pipeline-mapping-rules.md` (kept in sync by a test).
- References are kept as raw strings per source key; individual control ids (e.g. SP 800-53 `SA-15`) are not
  split into structured lists because some keys hold titles with commas (e.g. SCFPSSD, SCSIC).
- No government attestation form content is reproduced; the evidence matrix is "attestation-style" only.
