# EO 14028 mapping and attestation-style evidence

## What SP 800-218 says

- Appendix A, "The SSDF and Executive Order 14028" (PDF p.33, printed p.24), explains that Section 4 of EO 14028
  directed NIST to identify practices for software supply chain security, and **Table 2** maps EO 14028
  Section 4e subsections to SSDF practices and tasks "that can help address each subsection as part of a
  risk-based approach".
- 4e(ix) maps to "All practices and tasks consistent with a risk-based approach"; every other subsection maps
  to specific tasks. The catalog stores Table 2 in `parameters.eo14028_4e_mapping`; `ssdf show <task>` prints
  the subsections for a task and the evidence matrix includes them as a column.
- The same page notes NIST also published guidance on how producers and acquirers can communicate about
  attestation of conformance with EO 14028 Section 4e. That guidance is **not** in this source pack.

Each task's References column also lists `EO14028: 4e(...)` entries (Table 1). Table 2 and the per-task
reference entries are both from the PDF; if they ever disagree, cite the one you used.

## What this library does and does not do

- `ssdf evidence-matrix` produces an *attestation-style* matrix: for every task, the producer's status, the
  evidence it points to, the owner, the EO 14028 4e subsections (from Table 2), and notes. It is intended to
  help an accountable person decide what they can attest to and to brief reviewers.
- It is **not** an attestation form and does not reproduce any government form. Attestation content,
  signatories and legal effect must be checked against the current official requirements, which are outside
  this source.
- A row is only as good as its evidence reference. Before anyone signs anything, sample the evidence
  (open the document, inspect the pipeline run, check the SBOM is current).

## Reading the matrix

| Column | Meaning |
|---|---|
| Status | The producer's self-assessed status (`implemented`, `partial`, `planned`, `not-implemented`, `not-applicable`) |
| Evidence | References to artefacts; `**none**` flags an implemented/partial row with no evidence |
| EO 14028 4e | Subsections Table 2 maps to the task (4e(ix) applies to all and is omitted) |
| Justification / notes | Why N/A, what is missing, target dates |
| Source | PDF page of the task in Table 1 |

Open validation issues are listed at the end; resolve them before the matrix is used externally.
