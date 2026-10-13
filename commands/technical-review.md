---
description: Run a NASA-style technical life-cycle review gate (readiness, requirements audit, evidence audit, board recommendation).
argument-hint: "<review-id e.g. PDR> <path to requirements file> [design artefact paths]"
---
Act as the `review-board-chair` subagent and run the workflow defined in `workflows/technical-review-gate.yaml`.

Arguments: $ARGUMENTS

1. Read the workflow file and confirm the required inputs from the arguments; ask for any that are missing.
2. Initialise the review folder with `python -m agentlib workflow init technical-review-gate --input ...` and fill the artefact stubs it creates.
3. Execute the stages in order, delegating to the named subagents, and apply each gate exactly as specified.
4. Finish with the decision record from `templates/review-board-decision.md` and a stage status table.
