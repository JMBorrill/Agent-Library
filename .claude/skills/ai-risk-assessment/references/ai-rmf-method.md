# AI RMF method notes (original wording)

Source: `nist-ai` (NIST AI RMF 1.0, AI 100-1; Playbook). Primary documents were **INACCESSIBLE**
here (`sources/audits/nist-ai.md`). Everything below is either secondary corroboration recorded
in `sources/extracts/nist-ai-rmf-structure.json` or the author's working knowledge, and is marked.

## Structure used by the linter
| Function | Categories | Role in this skill | Status |
|---|---|---|---|
| GOVERN | 1–6 | accountability, policy, third-party (GOVERN 6) | category count secondary *(unverified)* |
| MAP | 1–5 | context, intended use, impacts | secondary *(unverified)* |
| MEASURE | 1–4 | evaluation evidence; MEASURE 2 = trustworthiness evaluation *(unverified)* | secondary *(unverified)* |
| MANAGE | 1–4 | treatment, third-party, response and recovery | secondary *(unverified)* |

GOVERN is described by secondary sources as cross-cutting (it applies throughout the other three).
Subcategories: secondary sources report about 72 in total; the list was not obtained, so the linter
accepts any `<cat>.<n>` pattern and emits `rmf-subcategory-unverified`. When AI 100-1 is
obtained, populate `subcategories` arrays in `assets/data/airmf-1.0-structure.json`; the linter then
enforces membership automatically.

## Reference format
`AIRMF-1.0-MAP-1` (category) or `AIRMF-1.0-MEASURE-2.11` (subcategory, pattern only). Version is
part of the ID so a register survives a future AI RMF revision (secondary sources report one is in
progress — unconfirmed).

## Trustworthiness characteristics (secondary corroboration)
valid-and-reliable · safe · secure-and-resilient · accountable-and-transparent ·
explainable-and-interpretable · privacy-enhanced · fair-with-harmful-bias-managed.
Use them as a checklist when identifying risks: each characteristic should either appear on at
least one risk or be recorded as not relevant with a reason.

## Generative AI risks (AI 600-1, partial)
Secondary results confirm these risk names among twelve: confabulation; CBRN information or
capabilities; harmful bias; data privacy; human-AI configuration. Others were not confirmed —
do not cite a full list from this library.

## Scoring scale (library convention, not NIST)
Likelihood and impact 1–5; score = product (1–25). Bands: low < 8, medium 8–14, high ≥ 15
(`--high-threshold`). Impact anchors for decisions about people: 5 = lasting financial, legal or
safety harm to individuals or many people; 4 = significant harm, reversible with effort;
3 = moderate, readily corrected; 2 = minor inconvenience; 1 = negligible. NIST does not prescribe
this scale; adapt to the organisation's risk appetite and record the change.

## Proportionality
The AI RMF is voluntary guidance. Apply it in proportion to the stakes: a short card and a handful
of risks for an internal drafting tool; the full register, card, evals and oversight matrix for
decision support about individuals. Recording *why* a function was applied lightly is better than
silently skipping it (the linter emits `function-not-referenced` as info).

## Go/no-go is a recommendation
The output vocabulary is GO / GO_WITH_CONDITIONS / NO_GO, always "requires human sign-off". The
scripts never print "approved" or "compliant".
