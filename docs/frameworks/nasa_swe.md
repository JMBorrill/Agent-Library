# NASA software engineering and software assurance (NPR 7150.2D, NASA-STD-8739.8B)

Implementation notes for the `nasa-swe` framework: what was extracted, how, what the tools do, and the
known gaps.

## Sources

| Source id | Document | Pinned PDF | Pages |
|---|---|---|---|
| `nasa-software-requirements` | NPR 7150.2D NASA Software Engineering Requirements (effective 2022-03-08, expires 2027-03-08) | `sources/pdfs/nasa-software-engineering-requirements-7150-2d.pdf` | 89 |
| `nasa-software-assurance` | NASA-STD-8739.8B Software Assurance and Software Safety Standard (2022-09-08) | `sources/pdfs/nasa-software-assurance-8739-8b.pdf` | 65 |
| `nasa-software` | NASA Software Engineering and Assurance Handbook (NASA-HDBK-2203, swehb.nasa.gov) | link only - **not bundled** | - |

Printed page numbers equal PDF page numbers in both PDFs. The SWEHB wiki is recommended further reading
in both skills; none of its content is reproduced or paraphrased.

## Components

| Path | Purpose |
|---|---|
| `scripts/extract/nasa_swe.py` | Reproducible extraction (`--check` compares without writing). Verifies PDF SHA-256 against the manifest. |
| `catalog/npr-7150-2d.json` | 130 SWE requirements; Appendix C applicability; Appendix D classes; Table 1 traceability; legend; tailoring summary. |
| `catalog/nasa-std-8739-8b.json` | SASS-01; 5 safety-critical criteria; 103 Table 1 rows (198 SA/SS tasks, 100 SWEs); 49 IV&V requirements; 2 tailoring "shall" statements; 12 Appendix A Table 2 cause areas. |
| `agentlib/frameworks/nasa_swe.py` | CLI `python -m agentlib nasa-swe ...` and eval graders. |
| `skills/nasa-software-engineering/` | Classification, matrix, tailoring and life-cycle planning skill (+4 templates). |
| `skills/nasa-software-assurance/` | SA planning, safety-criticality, hazard analysis, IV&V, audits (+4 templates). |
| `agents/software-engineering-lead.md`, `agents/software-assurance-engineer.md` | Subagents using the skills. |
| `evals/nasa-software-engineering/`, `evals/nasa-software-assurance/` | 5 cases each with golden and negative outputs. |
| `tests/test_nasa_swe.py` | Catalog integrity, tool logic, CLI and graders. |

## Extraction method and verification

NPR 7150.2D

- Body text (Chapters 2-5, PDF pp. 11-43) from `pdftotext -layout`. Running header/footer removed. The PDF
  repeats the last line of each page at the top of the next page; that duplicate is dropped.
- A requirement is the text from the nearest preceding paragraph number (1-2 digit components, so
  "7150.2 requirements" at a line start is not mistaken for a paragraph) up to its `[SWE-nnn]` tag, plus the
  lettered list that follows. Notes (5-space indented in the layout text) go to `notes`; a list resumes
  after a note when the next letter in sequence appears (SWE-126 b., SWE-148 f.). SWE-086 has no paragraph
  number of its own (heading 5.2); the heading line is skipped.
- Count check: 130 unique tags = 30 (Chapter 2) + 100 (Chapters 3-5).
- Appendix C (pp. 56-78) read with pdfplumber word coordinates: SWE number at x~95, Authority x 300-372,
  class X marks at x = 373/390/407/424/441 (A-E), Class F Authority x 455-525, Class F X at x >= 525.
  Wrapped Authority text is collected over the row's lines (gives "HQ OSMA" for SWE-141 and
  "HQ OCE and HQ OSMA" for SWE-032). Assertions: 100 rows; the row set equals the Chapter 3-5 SWEs;
  sections match the body; spot checks on SWE-033/141/174/015/032.
- Applicability counts (X): A 100, B 100, C 92, D 64, E 12, F 65.
- NPR 7150.2D's matrix uses only `X` and blank (2.2.4, p. 18; C.3, p. 55). Earlier revisions' notations such
  as "P(Center)" do not occur in this revision; none are modelled.
- SWE-015 has an X in the Class F column but an empty Class F Authority cell in the PDF; recorded as-is.
- Table 1 (SWE-052 traceability by class, p. 31) is encoded in the script and verified against the X
  positions on the page.
- Appendix D criteria/exclusions are encoded as (id, page, verbatim text) and each text is asserted to be
  present on its page. Criterion ids (`A-1a`, `B-x3`, `C-scope` ...) are library-assigned.
- Text fidelity: verbatim with whitespace normalised; curly quotes straightened; the ® sign dropped.

NASA-STD-8739.8B

- Table 1 (pp. 17-47) read with pdfplumber: section x < 120, SWE# 120-160, NPR text 160-415, tasks x >= 415.
  Tasks split on `<n>.` at the start of a task-column line in sequence; repeated column headers removed; a
  line-end hyphen after a letter is joined without a space. pdfplumber splits a few words inside glyph runs
  ("i ncorrect", "han dling"); `heal_splits` re-joins a short fragment with the next token only when the
  pdftotext rendering of the same pages contains the joined word and not the split form. Assertions: 103 rows, the SWE set equals the NPR
  Appendix C set, every row has >= 1 task.
- A supplier watermark (licensee/user/date) is printed in the page margin; words with x < 40 or below
  `page.height - 45` are excluded, and a glyph run that splits list numbers (e.g. "1" + "8.") is re-joined.
- IV&V 4.4.2.1-4.4.2.49 from the layout text (pp. 50-56), asserted to be consecutive; actor derived from
  the sentence subject (4.4.2.3 is the NASA SMA TA).
- Safety-critical criteria (4.2), SASS-01 (4.3) and the 4.5 tailoring statements are encoded verbatim and
  asserted present.
- Appendix A Table 2 (pp. 59-65): 12 cause areas (asserted by name), causes split on numbering.
- Library-assigned ids: `SC-4.2-a..e`, `4.5-1`, `4.5-2`, `HAZ-*` (flagged `id_assigned_by_library`).
  `SA-SWE-nnn[a-d]` wraps the standard's Table 1 rows. `safety_related_tasks` is a keyword heuristic.

## CLI

```sh
python -m agentlib nasa-swe classify --list-questions
python -m agentlib nasa-swe classify --answers answers.yaml [--format json]
python -m agentlib nasa-swe classify --yes B-scope --yes B-1a --safety-critical
python -m agentlib nasa-swe matrix --class B [--safety-critical] [--ivv] [--format md|csv|json] [-o file]
python -m agentlib nasa-swe check-matrix rmm.csv [--class B] [--format md|json]   # exit 1 on errors
python -m agentlib nasa-swe sa-tasks [--swe SWE-134] [--class C] [--safety-only] [--ivv] [--format md|json]
python -m agentlib nasa-swe sc-assess --criteria b,e | --answers sc.yaml
python -m agentlib nasa-swe hazard-causes [--area command]
python -m agentlib nasa-swe show SWE-219 | 4.4.2.3 | SASS-01
```

Exit codes: 0 ok, 1 matrix has errors, 2 invalid input (unknown id/class/file).

### Classification decision procedure

Questions are the Appendix D scopes, criteria and exclusions. A class matches when at least one of its
criteria is answered yes (Class A/B criteria also need their scope question) and none of its exclusions is
yes. The candidate is the highest matching engineering class (A > B > C > D > E; D.2 "assign the higher of
the classes"); Class F is proposed only when no engineering class matches (an F match alongside an
engineering class is reported as "classify separately"). If `safety_critical` is yes and the result is E or
undetermined, the candidate becomes D (Class E cannot be safety-critical, p. 85). Output always carries the
authority disclaimer (SWE-020, Note to 3.5.1, D.2).

### Matrix and checking

`matrix` emits every requirement marked X for the class with Authority (Class F uses the Class F
Authority column), a condition note for conditional requirements (safety-critical, IV&V, project
category, CMMI) and empty Status / Tailoring rationale / Approval / Evidence columns. Allowed statuses:
Compliant, Partially Compliant, Non-Compliant, Planned, Tailored, Not Applicable (library vocabulary; the
NPR prescribes none). `check-matrix` reads csv (`# class: X` comment supported), json/yaml (`{"class":...,
"rows": [...]}`) or the first Markdown table with a SWE column; column names are matched by alias.

Errors: malformed/unknown ids, duplicates, missing X requirements, missing/invalid status, Compliant or
Partially Compliant without evidence, Tailored/Not Applicable/Non-Compliant/Partially Compliant without
rationale. Warnings: Tailored without approval, HQ-authority tailoring without HQ approval, 3.11 relief
without SAISO/CISO, Chapter 2 ids, unknown class. Info: requirement blank for the class.

### Graders (for `python` eval checks)

`grade_swe_ids_valid`, `grade_candidate_class` (expects "Candidate class: X"),
`grade_matrix_coverage` (Markdown table rows vs Appendix C, `forbid`, status validity),
`grade_safety_critical_determination` ("Safety-critical determination: Yes|No" + 4.2 letters),
`grade_ivv_refs_valid` (4.4.2.1-49 only), `grade_page_citations` (library citation syntax checked against
catalog pages incl. Appendix C pages), `grade_check_matrix_fixture` (output names every error the tool
finds in a fixture).

## Assumptions

- "Applicable" means marked X in Appendix C for the class; conditional wording is annotated, not filtered,
  because C.3 asks for every X requirement to be addressed (tailored out with justification if needed).
- Chapter 2 requirements are institutional (Center Director, OCE, Chief SMA, TAs) and are not matrix rows.
- Table 1 SA tasks apply when the corresponding SWE applies (SASS-01).

## Known gaps

- Appendix C requirement text is not stored separately (it repeats the body text with minor wording
  differences, e.g. "trades studies" vs "trade studies"); the body text is authoritative in the catalog.
- Notes are stored verbatim but not split into multiple notes; the Chapter 6 records list and Appendix A
  (definitions) / B (acronyms) / E (references) of the NPR are not cataloged.
- NASA-STD-8739.8B definitions (3.2) are summarised in the skill reference, not cataloged; Appendix A
  Table 2 long entries (e.g. the data-dictionary cause) are kept as one cause string.
- The classifier cannot weigh the five underlying factors (D.1) or Appendix D examples automatically; it
  only walks the definitions the user answers.

## Change requests for shared files

None required. `agentlib/frameworks/evidence.py` already recognises `SWE-nnn` identifiers against the
`nasa-software-requirements` catalog; citations to Appendix C pages are written as
`[nasa-software-requirements Appendix C SWE-nnn, p. N]` so its page-tolerance check does not flag them.
