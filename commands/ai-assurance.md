---
description: Run an AI system risk assessment and assurance review using the NIST AI RMF and Playbook.
argument-hint: "<AI system description path> [policies path]"
---
Act as the `review-board-chair` subagent and run `workflows/ai-system-assurance.yaml`.

Arguments: $ARGUMENTS

Save artefacts under `reviews/ai-system-assurance-<YYYY-MM-DD>/`. Use `python -m agentlib ai-rmf` tools to
generate and validate the profile and risk register. The final recommendation must name the accountable human
decision-maker and list residual risks.
