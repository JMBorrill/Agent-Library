# Review practice notes (library guidance)

## Reviews named in NASA life cycles (secondary corroboration only)
MCR (mission concept), SRR (system requirements), MDR/SDR (mission/system definition), PDR
(preliminary design), CDR (critical design), PRR (production readiness, conditional), SIR (system
integration), TRR (test readiness), SAR (system acceptance), ORR (operational readiness), FRR (flight
readiness), PLAR, CERR, DR (decommissioning). Which review applies in which phase, and their real
entrance/success criteria, are defined by NPR 7123.1 / NPR 7120.5 and **must be checked by a human**
against the current NODIS text before use in a NASA context. See `sources/audits/nasa-se.md`.

## Roles
- **Review chair** — independent of the project team; runs the review, owns the recommendation.
- **Reviewers** — read evidence before the meeting; write actions (RIDs) with requested closure evidence.
- **Project** — presents evidence, responds to RIDs.
- **Gate authority** — decides; may accept conditions or overrule with recorded rationale.

## Tailoring for small projects
A one-hour requirements walk-through with an independent engineer and a signed checklist is a
legitimate SRR for a lab prototype. A safety-relevant test always needs a TRR, however small.

## Anti-patterns
- "Review by slideware" — criteria marked met from presentation statements.
- Reviewers who wrote the artifacts.
- Closing actions by assertion ("done") without evidence.
- Treating GO_WITH_CONDITIONS as GO and never closing conditions.
