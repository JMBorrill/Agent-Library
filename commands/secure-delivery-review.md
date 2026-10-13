---
description: Run a secure software delivery review combining a NIST SSDF process assessment with OWASP ASVS verification.
argument-hint: "<system description path> <pipeline yaml path> [repo path or commit]"
---
Act as the `review-board-chair` subagent and run `workflows/secure-software-delivery.yaml`.

Arguments: $ARGUMENTS

Initialise the review folder with `python -m agentlib workflow init secure-software-delivery --input <name>=<path>` and fill the artefact stubs it creates; record gates with `python -m agentlib workflow gate`. Stop at each `human` gate (ASVS level
choice, final decision) and ask the user unless they have pre-authorised proceeding. Run every `check` command
named in a gate and attach its output.
