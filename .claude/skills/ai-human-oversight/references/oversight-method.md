# Human oversight method notes (original wording)

## Automation levels used here
| ai_role | The AI... | The human... |
|---|---|---|
| inform | retrieves, summarises, highlights facts or matches | decides with full discretion |
| recommend | proposes an outcome with rationale | accepts, changes or rejects; owns the outcome |
| draft | prepares an artefact (letter, record update) | edits and releases it |
| act | causes the effect directly | monitors samples/metrics, can stop and reverse |

"Human in the loop" only means something when the human could realistically reach a different
answer: they see the inputs, have time, are measured on quality rather than throughput, and
disagreeing is easy and logged.

## Automation bias: practical mitigations
- Show the evidence and sources behind a recommendation, not just a score.
- For high-impact cases, have the reviewer record a provisional view before revealing the AI
  output (or for a random sample).
- Seed known-wrong recommendations into a training/QA sample and measure catch rate.
- Monitor override rate, time-to-decision and agreement by reviewer; extremes trigger review.
- Rotate reviewers and avoid targets that reward clearing queues.

## Explanation and appeal for decisions about individuals
For credit, eligibility and similar decisions, people affected should be able to learn the main
reasons for an adverse outcome and ask for a human to look again. The validator enforces the
presence of an explanation flag and an appeal route for decisions whose names suggest this
category; whether a specific explanation is adequate under applicable law is a legal question
outside this skill.

## Kill switch and rollback
- One named owner and a deputy; a mechanism that takes effect in minutes (feature flag, routing
  to a manual queue), tested on a schedule.
- Rollback triggers are metric thresholds written in advance (e.g. misclassification > 3% in the
  weekly sample; any confirmed data leak; injection alert on a side-effecting path).
- A manual fallback process sized for full volume, or an agreed degraded service.

## Logging
Per decision: case ID, AI output and version, data used, human action (accept/modify/reject),
reason code, approver, timestamps. Retention and access per the data protection assessment.

## Relation to the AI RMF (unverified)
Secondary sources list *accountable and transparent* and *explainable and interpretable* among the
trustworthiness characteristics, and summaries describe GOVERN as covering accountability roles
and MANAGE as covering response, recovery and the ability to disengage systems *(paraphrased;
category/subcategory mapping not verified against the primary)*.
