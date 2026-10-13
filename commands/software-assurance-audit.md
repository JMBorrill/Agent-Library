---
description: Run an NPR 7150.2D compliance and NASA-STD-8739.8B software assurance audit for a software product.
argument-hint: "<software description path> [project artefacts folder]"
---
Act as the `review-board-chair` subagent and run `workflows/software-assurance-audit.yaml`.

Arguments: $ARGUMENTS

Software classification is proposed, not decided: record it as a candidate and ask the user to confirm the class
before generating the compliance matrix. Initialise the review folder with `python -m agentlib workflow init software-assurance-audit --input <name>=<path>` and fill the artefact stubs it creates; record gates with `python -m agentlib workflow gate`.
