---
name: assurance-case
description: >-
  Builds and checks a structured assurance case (claims, arguments, evidence) that ties framework
  results together for a decision-maker: e.g. "the payments API is acceptably secure for release",
  argued through ASVS verification, SSDF process evidence and residual-risk acceptance. A deterministic
  checker (python -m agentlib assurance-case check) enforces one root claim, no cycles, every leaf claim
  backed by evidence of adequate strength or explicitly undeveloped with justification, and real framework
  identifiers. Use when preparing a release, safety, security or AI deployment decision package, or when
  a review board needs one argument that integrates several assessments.
metadata:
  version: 1.0.0
  category: quality
  maturity: beta
  sources: [nasa-se, nasa-software-assurance, owasp-asvs]
  tools:
    - "python -m agentlib assurance-case template"
    - "python -m agentlib assurance-case check"
    - "python -m agentlib assurance-case render"
---

# Assurance case

An assurance case is a structured argument that a top-level claim (for example "acceptably secure for
release") is supported by evidence. This library uses a simple claims-arguments-evidence (CAE) form.
**The CAE structure, criticality levels and strength thresholds are library conventions**; none of the
bundled frameworks prescribes an assurance-case notation. What the frameworks do require is objective,
documented evidence behind conclusions — the case is a way to show that evidence and its gaps in one place.

## When to use

- A decision (release, deployment, go/no-go at a review, funding gate) depends on several assessments.
- The `review-board-chair` needs one integrated argument for a board decision record.
- An auditor asks "why do you believe X?" and the answer spans multiple frameworks.

Not for: a single checklist assessment (use the framework skill's own report), or proving claims that have
no evidence yet (record them as **undeveloped** instead).

## Workflow

1. **State the top claim precisely**, with scope (artefacts, versions, environment) and the decision
   authority. Vague claims ("the system is secure") cannot be argued; bounded ones can ("payments-api
   commit a1b2c3d meets ASVS L2 for V1-V8 and has no open high findings").
2. **Start from the template:** `python -m agentlib assurance-case template > case.yaml`.
3. **Decompose with an explicit argument.** For each claim that has subclaims, write *why* the subclaims
   together suffice (e.g. "by ASVS chapter in scope, plus the SSDF process that produced the build").
   Common decomposition patterns: [references/argument-patterns.md](references/argument-patterns.md).
4. **Attach evidence to leaf claims**, using the evidence records and strength scale of
   `skills/evidence-and-citation/` (E0-E4). Criticality sets the minimum strength:
   low/medium need E2, high needs E3 (library convention). Name the artefact (path or URL) for each item.
5. **Mark gaps honestly.** A claim without adequate evidence is `status: undeveloped` with a
   justification and the action that will close it — never padded with weak evidence.
6. **List framework identifiers** each claim relies on under `frameworks:` (e.g. `PW.7.1`, `V6.2.1`,
   `GOVERN 1.1`, `SWE-022`); the checker rejects identifiers that do not exist.
7. **Check and iterate** until there are no errors:

   ```sh
   python -m agentlib assurance-case check case.yaml --base .   # --base also checks artefact paths exist
   ```

   Verdict `complete` (no undeveloped claims), `incomplete` (valid but with declared gaps) or `invalid`.
8. **Render for the decision-maker:** `python -m agentlib assurance-case render case.yaml > case.md`,
   then run `python -m agentlib evidence check case.md` and attach both to the decision record
   (`templates/review-board-decision.md`).

## Outputs

- `case.yaml` (machine-checkable) and `case.md` (rendered argument tree + evidence register).
- The checker output, attached to the decision package.

## Quality checklist

- [ ] One root claim, bounded by scope, with a named decision authority.
- [ ] Every decomposition states its argument; no circular reasoning (checker enforces no cycles).
- [ ] Every leaf claim has evidence meeting its criticality, or is undeveloped with a justification.
- [ ] Evidence names concrete artefacts with versions; strengths follow the E0-E4 scale.
- [ ] Undeveloped claims appear as conditions or residual risks in the decision record.
- [ ] Nothing claims certification or approval; the decision rests with the named authority.

## Sources

- `nasa-se` (NASA/SP-2016-6105 Rev 2): product verification is complete only with documented objective
  evidence of compliance (or a waiver) and closure of discrepancy and nonconformance reports
  [nasa-se, p. 128]; verification provides objective evidence that every "shall" was met [nasa-se, p. 129].
- `nasa-software-assurance` (NASA-STD-8739.8B): IV&V uses analysis and testing to identify objective
  evidence and conclusions for an independent assessment [nasa-software-assurance 4.4.1.1, p. 48].
- `owasp-asvs` (5.0.0): verification should provide robust evidence of findings with detailed
  documentation; running an automated tool alone is insufficient [owasp-asvs, p. 20].

## Limitations

- The checker validates structure, identifiers and declared evidence strength, not whether the evidence
  really supports the claim; the `evidence-auditor` must spot-check substance.
- A well-formed case can still rest on a flawed argument; challenge each decomposition ("what else
  would have to be true?").
- Output supports, but does not replace, qualified professional judgement or the decision authority's approval.
