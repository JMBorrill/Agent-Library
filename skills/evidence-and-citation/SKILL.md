---
name: evidence-and-citation
description: >-
  Disciplined evidence handling for professional assessments produced with AI assistance: how to cite
  the pinned framework sources (source id, locator, PDF page), how to record evidence, how to grade claim
  strength, and how to avoid over-claiming compliance or certification. Includes a deterministic checker
  (python -m agentlib evidence check) that validates citations, page ranges and framework identifiers
  (SSDF tasks, AI RMF subcategories, NPR 7150.2D SWE ids, ASVS requirements) against the catalogs.
  Use when writing or reviewing any assessment, gap analysis, review package, business case or report
  that relies on the library's frameworks, and always before delivering such a document.
metadata:
  version: 1.0.0
  category: quality
  maturity: beta
  sources: [nasa-se, nasa-software-requirements, nasa-software-assurance, nist-ai, nist-ai-playbook, nist-ssdf, treasury-green, owasp-asvs]
  tools: ["python -m agentlib evidence check", "python -m agentlib evidence sources"]
---

# Evidence and citation

Every other skill in this library produces documents that people may rely on. This skill sets the
evidence standard they share. Load it alongside any framework skill.

## When to use

- Drafting an assessment, review package, compliance matrix, risk register, business case or report.
- Reviewing someone else's (or another agent's) document for traceable, honest claims.
- Before delivering any output: run the checker and fix every error.

## Workflow

1. **Identify the sources in play.** List them with `python -m agentlib evidence sources`. Use the
   `id` column as the citation key. Link-only sources (e.g. `nasa-software`, `gov-service`) may be cited
   by id and section but have no checkable page.
2. **Read before citing.** Open the relevant pages of the pinned PDF (see `sources/README.md` for
   `pdftotext -f N -l N`). Possession of a PDF is not evidence that it was read; cite only pages you read.
3. **Cite in the library format** — `[<source-id> <locator>, p. <pdf-page>]`, for example
   `[nist-ssdf PW.7.1, p. 23]`, `[treasury-green para 5.32, p. 35]`. The page is the *PDF* page of the
   pinned file; add the printed page in the locator if it differs. Full rules:
   [references/citation-format.md](references/citation-format.md).
4. **Record evidence, not assertions.** For every assessed control/requirement, record what was
   examined, by whom, when, and the result, using
   [templates/evidence-record.md](templates/evidence-record.md). Grade each claim with the evidence
   strength scale in [references/claim-strength.md](references/claim-strength.md).
5. **Separate the four kinds of statement**: (a) what the source says, (b) what was observed,
   (c) the assessor's judgement, (d) recommendations. Never present (c) as (a).
6. **Use calibrated language.** An AI-assisted assessment may say "evidence reviewed indicates the
   requirement appears to be met"; it must not say "certified", "fully compliant", "guaranteed" or
   "approved for operation". Those decisions belong to the accountable authority.
7. **Run the checker** and resolve all errors; justify or fix warnings:

   ```sh
   python -m agentlib evidence check report.md --require-citations
   ```

   It flags unknown source ids, out-of-range pages, citations whose page disagrees with the catalog,
   framework identifiers that do not exist (e.g. a hallucinated `PW.9.3` or `SWE-999`) and over-claims. <!-- evidence:ignore -->
8. **State limitations and open items** at the end of the document: what was not reviewed, assumptions
   made, evidence not available.

## Outputs

- Documents whose every normative statement carries a checkable citation.
- Evidence records (one per assessed item or per evidence artefact).
- A clean `evidence check` run (attach its output to review packages).

## Quality checklist

- [ ] Every framework claim has a citation in the library format with a PDF page.
- [ ] Every requirement/control identifier exists in the catalog (checker reports no identifier errors).
- [ ] Observations name the artefact examined (path, version/commit, date).
- [ ] No over-claiming language; approval decisions attributed to the accountable authority.
- [ ] Limitations and unreviewed scope are stated.

## Sources

All bundled sources, as listed in `sources/pdf-manifest.json`:
`nasa-se` (NASA/SP-2016-6105 Rev 2), `nasa-software-requirements` (NPR 7150.2D),
`nasa-software-assurance` (NASA-STD-8739.8B), `nist-ai` (NIST AI 100-1),
`nist-ai-playbook` (AI RMF Playbook snapshot 2026-10-13), `nist-ssdf` (SP 800-218 v1.1),
`treasury-green` (Green Book 2026), `owasp-asvs` (ASVS 5.0.0). This skill defines a citation discipline
for those sources; it does not restate their content. Page ranges are checked against the manifest.

## Limitations

- The checker validates the *form* and *existence* of citations and identifiers, not whether the cited
  page actually supports the claim; a human or a second agent must spot-check substance.
- Catalog page tolerance is ±2 pages; tables spanning pages can trigger warnings that need judgement.
- Output supports, but does not replace, qualified professional judgement, formal assurance or approval.
