---
name: se-risk-analysis
description: Identify, score, handle and track technical, safety, cost and schedule risks with a policy-driven likelihood x consequence register and FMEA worksheets, including residual risk and human risk acceptance. Use when building or reviewing a risk register, running an FMEA on a design, preparing risk content for a design review, or checking that high risks have owners, mitigations, triggers and authorised acceptance.
metadata:
  pack: systems-engineering
  version: "1.1.0"
  sources: "nasa-se-manage nasa-se"
---

# Technical risk management

## Purpose
Maintain a living risk register in which each risk is stated as condition → possible event →
consequence, scored on an explicit ordinal policy, owned, handled (mitigate, research, watch, accept)
and re-reviewed; and support design-level failure analysis with FMEA. Corresponds to the NASA process
*Technical Risk Management* (see References).

## When to use
- Starting a project or phase: initial risk identification from ConOps, requirements, architecture.
- Design reviews (PDR/CDR/TRR-style): demonstrate top risks are controlled and residual risk is accepted.
- After test failures, anomalies, supplier issues or changes — reassess affected risks.
- Component/subsystem design: FMEA to find failure modes, causes and detection gaps.

**Do not use when:** you need a security threat model (`security-threat-model`), AI-specific harm
analysis (`ai-risk-assessment`) or credit risk controls (`credit-risk-governance`) — those have
domain-specific methods; link their outputs here if they create programme-level risk.

## Inputs
Required: risk register CSV (`assets/templates/risk-register.csv`); risk-matrix policy JSON approved by
the project (`assets/templates/risk-matrix-policy.json` is an *example only*).
Optional: FMEA worksheet (`assets/templates/fmea.csv`), requirements/V&V/ICD CSVs for `related_ids`,
hazard analysis, test anomalies.

## Procedure
1. **Agree the policy first**: scale, level thresholds, which cells are always "high", review intervals.
   Record who approved it. Never invent a policy silently — use the example only as a placeholder.
2. **Identify** risks from each ConOps scenario (nominal and off-nominal), each interface, each new
   technology, each single-point failure, supplier/schedule dependencies and the hazard analysis.
3. **State** each risk: "Given <condition>, there is a possibility of <event>, resulting in
   <consequence>". Separate observed problems (issues) from possible future events (risks).
4. **Score** likelihood and consequence on the policy scale with a one-line basis; scores are ordinal
   judgements, not probabilities.
5. **Choose an approach**: mitigate (reduce L or C), research (reduce uncertainty), watch (monitor a
   trigger), accept (named human accepts), transfer, close. Assign owner and trigger threshold.
6. **Estimate residual** L×C after the planned mitigation; link mitigations to requirements or
   verification activities (`related_ids`) so they become verifiable.
7. **Run the checks**:
   `python3 scripts/risk_check.py register.csv --policy policy.json --as-of YYYY-MM-DD --known-ids requirements.csv verification-matrix.csv`
   For design-level analysis: `python3 scripts/fmea_calc.py fmea.csv`.
8. **Escalate** high and safety risks per Escalation below; record acceptance decisions with name and date.
9. **Review** at each milestone and on trigger events; close risks only with evidence.

## Decision criteria
| Condition | Rule |
|---|---|
| High risk, open | Must be mitigate/research with mitigation + trigger + owner, or accepted by a named human |
| Residual risk still high | Must be explicitly accepted by the accountable authority (`accepted_by`) |
| Safety category, consequence ≥ scale−1 | Escalate to qualified safety reviewer regardless of likelihood |
| FMEA severity ≥ 9 | Review and action regardless of RPN |
| FMEA RPN ≥ policy threshold | Recommended action + owner required |
| Residual > current score | Error — mitigation cannot increase risk; re-assess |

## Outputs
`risk-register.csv`, `fmea.csv`, `risk-summary.md` (top risks, changes since last review, acceptance
decisions), JSON reports from both scripts.

## Validation
`risk_check.py` exit 0 ⇒ the register conforms to the policy (IDs, scores, owners, approaches, triggers,
acceptance records, residual logic, review age). It does **not** show that the risk list is complete
or the scores correct. `fmea_calc.py` ranks modes; RPN does not measure safety.

## Examples
- `assets/examples/risks-pass.csv` (`--as-of 2026-10-13`) → exit 0 with a `safety-escalation` warning.
- `assets/examples/risks-fail.csv` → exit 1: `no-owner`, `unauthorised-acceptance`, `duplicate-id`,
  `score-range`; warnings `statement-form`, `stale-review`, `residual-high-unaccepted`, `no-review-date`.
- `assets/examples/fmea-example.csv` → FM-001 (S=9) ranked first and flagged `high-severity`.

## Escalation and stop conditions
- Any risk to human safety, the environment or regulated outcomes: hand to `safety-risk-reviewer` and
  require a qualified human decision; this skill never accepts a risk.
- Stop if no approved policy exists for a decision-relevant review — present results as provisional.
- Do not close a risk without evidence (test record, analysis, changed design).

## References
- `nasa-se-manage` — Technical Risk Management §6.4 *(secondary corroboration only; see
  `sources/audits/nasa-se-manage.md`)*.
- Method notes (risk statements, handling approaches, FMEA limits): [references/risk-method.md](references/risk-method.md).
