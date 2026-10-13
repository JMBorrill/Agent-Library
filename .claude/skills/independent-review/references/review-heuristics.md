# Challenge-review heuristics (library guidance)

## Questions that find most problems
1. What decision does this support, and who owns it?
2. Which three claims matter most? Open the evidence for each.
3. What was *not* tested, analysed or asked? Is that stated?
4. Which numbers are measured, which estimated, which assumed? Are they labelled?
5. Which sources were actually readable (see `sources/registry.json` access_status)?
6. What would change the conclusion, and how cheap is it to find out?
7. Who reviewed this before, and were they independent?

## Common failure patterns in AI-generated artifacts
- Plausible precision: section numbers, rates or dates recalled from memory presented as verified.
- Invented stakeholder voice: quotes or "users said" with no session reference.
- Assurance drift: "the plan covers X" becoming "X is verified" a few pages later.
- Self-approval: the authoring agent writes "approved" or "GO" as if it were the decision.
- Passing checks presented as proof: a clean lint or schema check described as engineering adequacy.

## Writing findings
State the claim, where it appears, what evidence you looked for, what you found, and the specific
evidence that would resolve it. Avoid vague findings ("improve robustness").

## Sign-off markers used by `claim_check.py`
`[signoff: <name/role>, YYYY-MM-DD]` — only when a human decision record exists; link the record.
`[evidence: <record id or path>]` — for research findings and quotations.
