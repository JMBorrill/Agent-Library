# Official framework source pack

Collected 13 October 2026 for the professional AI agent and skills library.
These are unchanged publisher PDFs, not AI-generated summaries or recreated books.

| Source | Version | PDF pages | File |
|---|---|---:|---|
| NASA Systems Engineering Handbook | NASA/SP-2016-6105 Rev 2 (2016) | 356 | [nasa-systems-engineering-handbook-rev2.pdf](pdfs/nasa-systems-engineering-handbook-rev2.pdf) |
| NASA Software Engineering Requirements | NPR 7150.2D; effective 2022-03-08; expires 2027-03-08 | 89 | [nasa-software-engineering-requirements-7150-2d.pdf](pdfs/nasa-software-engineering-requirements-7150-2d.pdf) |
| NASA Software Assurance and Software Safety Standard | NASA-STD-8739.8B (2022) | 65 | [nasa-software-assurance-8739-8b.pdf](pdfs/nasa-software-assurance-8739-8b.pdf) |
| Artificial Intelligence Risk Management Framework | NIST AI 100-1 / AI RMF 1.0 (2023) | 48 | [nist-ai-rmf-1-0.pdf](pdfs/nist-ai-rmf-1-0.pdf) |
| NIST AI RMF Playbook | Snapshot downloaded 2026-10-13; living resource | 147 | [nist-ai-rmf-playbook.pdf](pdfs/nist-ai-rmf-playbook.pdf) |
| Secure Software Development Framework | NIST SP 800-218 / SSDF 1.1 (2022) | 36 | [nist-ssdf-1-1.pdf](pdfs/nist-ssdf-1-1.pdf) |
| The Green Book: UK government guidance on appraisal | 2026 edition | 88 | [hm-treasury-green-book-2026.pdf](pdfs/hm-treasury-green-book-2026.pdf) |
| OWASP Application Security Verification Standard | 5.0.0 (2025) | 123 | [owasp-asvs-5-0-0-en.pdf](pdfs/owasp-asvs-5-0-0-en.pdf) |

## Provenance and integrity

`pdf-manifest.json` records each title, publisher, edition, source URL, resolved URL,
retrieval date, byte count, page count, SHA-256 and reuse notice. It also records all
link-only frameworks and why no PDF was bundled. See `THIRD_PARTY_NOTICES.md`.

Run from the repository root:

```sh
python3 scripts/verify_source_pdfs.py
```

The validator uses Python's standard library. If `pdfinfo` is installed, it also
opens each PDF and compares its page count. Missing parser support is reported
as a skipped check, not claimed as successful PDF parsing.

## Claude reading workflow

1. Validate the source pack, then select the relevant manifest IDs.
2. Start with `nasa-se`: Chapters 4, 5 and 6 supply the design, realisation and
   technical-management processes. `nasa-se-design`, `nasa-se-realize` and
   `nasa-se-manage` reuse this PDF; do not create duplicate copies.
3. Read selected pages rather than putting all PDFs into the model context.
   If available, extract a range with:

   ```sh
   pdftotext -f 1 -l 10 -layout sources/pdfs/nasa-systems-engineering-handbook-rev2.pdf /tmp/nasa-pages.txt
   ```

   Replace page numbers with the actual PDF page indices. Printed page labels
   can differ. Preserve both in evidence records.
4. Cite source ID, edition, exact section, printed page and PDF page. Record
   which pages were actually reviewed; possession is not evidence of review.
5. For NASA software, read the live SWEHB wiki as well as the supporting NPR
   7150.2D and NASA-STD-8739.8B PDFs. They are distinct sources.
6. Treat the NIST Playbook as a snapshot of a living resource. Poppler produced
   missing-font warnings on some pages; render those pages or use another
   extractor when text is incomplete. Never fill gaps from inference.
7. Retrieve link-only sources from their official sites. Honour access and
   reproduction restrictions. Do not manufacture a PDF and label it official.
8. Before making time-sensitive claims, check the publisher for superseding
   editions, errata and effective dates. Pinned editions are not automatically
   the latest forever.
9. When the starter repository arrives, map these IDs and paths into its existing
   `sources/registry.json` schema without overwriting it. This separate manifest
   deliberately does not invent the missing registry's schema.

The full agent-development mission still needs its starter specification,
registry, agents and skills. This pack supplies reading material only.
