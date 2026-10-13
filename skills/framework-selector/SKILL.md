---
name: framework-selector
description: >-
  Routes a professional engineering, security, AI-governance or investment problem to the right
  frameworks, skills, subagents and workflows in this library, and explains how they combine
  (e.g. SSDF for the process plus ASVS for the product; NASA SE lifecycle reviews plus Green Book
  business case). Use when starting a new piece of work, when a request spans several disciplines,
  or when unsure which skill or workflow applies.
metadata:
  version: 1.0.0
  category: meta
  maturity: beta
  sources: [nasa-se, nasa-software-requirements, nasa-software-assurance, nist-ai, nist-ssdf, owasp-asvs, treasury-green]
  tools: ["python -m agentlib list", "python -m agentlib route"]
---

# Framework selector

## When to use

- At the start of an engagement, to choose the frameworks and plan the work.
- When a request mentions several concerns (e.g. "an AI feature in a public-sector service that needs a
  business case and a security review").
- When asked "which standard applies?" — answer with the routing table and the rationale, and state
  that mandatory applicability is set by contract, regulation or organisational policy, not by this skill.

## Workflow

1. **Characterise the problem** with five questions:
   1. What is being produced or decided? (system, software, AI system, investment/policy decision)
   2. Which life-cycle stage? (concept, requirements, design, build, verify, operate, retire)
   3. What are the consequences of failure? (safety, mission, security, financial, rights/harms)
   4. Who is the accountable authority and what do they need to see?
   5. Are any frameworks *mandated* (contract, NASA NPR applicability, government spending rules)?
2. **Get a ranked suggestion** from the deterministic router, then apply judgement:

   ```sh
   python -m agentlib route "threat model and security verification for a payments web API"
   ```

3. **Apply the routing table** in [references/routing-table.md](references/routing-table.md). Combine
   frameworks by role: *process* (how work is done: NASA SE, NPR 7150.2D, SSDF), *product* (properties
   the output must have: ASVS, AI RMF trustworthiness characteristics), *decision* (whether to invest:
   Green Book), *assurance* (independent confidence: NASA-STD-8739.8B, evidence-and-citation).
4. **Pick a workflow** if one fits (`python -m agentlib list workflows`); otherwise assemble stages
   from the skills and subagents listed.
5. **Write a short framework selection record** (which frameworks, why, which are mandatory vs
   advisory, tailoring decisions, accountable authority) and carry it into the work.

## Outputs

- Framework selection record: frameworks, rationale, mandatory/advisory status, skills, agents,
  workflow, accountable authority, open questions.

## Sources

Routing rationale relies on each framework's own statement of scope:
`nasa-se` (Rev 2, Ch. 1-2 scope and SE engine), `nasa-software-requirements` (NPR 7150.2D, Ch. 1
applicability), `nasa-software-assurance` (NASA-STD-8739.8B, Section 1 scope), `nist-ai`
(AI 100-1, Part 1 audience and Part 2 core), `nist-ssdf` (SP 800-218, Section 1 introduction),
`owasp-asvs` (5.0.0, front matter "using the ASVS"), `treasury-green` (2026, Chapter 1 scope).
Detailed pages are cited in each framework skill.

## Limitations

- Keyword routing is a starting point; it cannot detect obligations hidden in contracts or law.
- Framework applicability (e.g. whether NPR 7150.2D binds a project) is decided by the organisation.
- Output supports, but does not replace, qualified professional judgement.
