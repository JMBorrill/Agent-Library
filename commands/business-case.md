---
description: Develop and assure a Green Book five-case business case with deterministic NPSV, BCR and sensitivity analysis.
argument-hint: "<spending proposal path> <cost-benefit data csv/yaml>"
---
Act as the `review-board-chair` subagent and run `workflows/public-investment-business-case.yaml`.

Arguments: $ARGUMENTS

All discounting, NPSV, BCR, switching values and optimism bias adjustments must be computed with
`python -m agentlib greenbook ...`, never by hand. Save artefacts under
`reviews/public-investment-business-case-<YYYY-MM-DD>/`.
