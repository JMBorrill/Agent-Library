# Monitoring and incident response plan - "Ask Aurora" customer-service assistant

| Field | Value |
|---|---|
| System | Ask Aurora v1.3: retrieval-augmented assistant on a third-party foundation model via API |
| Plan owner | Head of Digital Customer Service |
| Authority to disengage / deactivate | Duty Operations Manager (24/7); confirmed by Head of Digital within 24 h |
| Review cadence | Monthly metrics review; full plan review every 6 months or after a severity-1 incident |

Assessed using NIST AI RMF 1.0 and the AI RMF Playbook. Thresholds below are **set by the
organisation** (risk committee, 2026-09) - the AI RMF prescribes no thresholds.

## 1. Monitoring metrics and triggers

Production monitoring of functionality and behaviour [nist-ai MEASURE 2.4, p. 34]; post-deployment
monitoring plan including user input, appeal and override, incident response, recovery and change
management [nist-ai MANAGE 4.1, p. 38].

| Metric | Characteristic | Data source | Frequency | Threshold (org-set) | Action on breach | Owner |
|---|---|---|---|---|---|---|
| Answer groundedness (sampled human review) | Valid and reliable | 200 sampled conversations | Weekly | < 95% grounded | Investigate; restrict topic | QA lead |
| Wrong billing/disconnection advice | Safe | Complaints + review sample | Daily | Any confirmed case | Severity-1 incident | Duty Ops Manager |
| Prompt-injection / jailbreak detections | Secure and resilient | Guardrail logs | Real time | > 20/hour or any data leak | Block pattern; consider disengage | Security operations |
| Personal data in outputs | Privacy-enhanced | DLP scanner | Real time | Any customer data of another person | Severity-1 incident | DPO |
| Escalation-to-human success rate | Accountable and transparent | Handoff logs | Daily | < 98% | Fix routing; notify ops | Contact-centre manager |
| Resolution rate by language / accessibility channel | Fair - with harmful bias managed | Analytics | Monthly | > 10 point gap vs English web chat | Root-cause review | Data science lead |
| Input drift vs evaluation set | Valid and reliable | Embedding drift monitor | Weekly | Drift score above control limit | Re-run evaluation suite | ML engineer |

Playbook actions adopted: compare production metrics with pre-deployment values
[nist-ai-playbook MEASURE 2.4/action-1, p. 109]; anomaly monitoring with control limits
[nist-ai-playbook MEASURE 2.4/action-3, p. 110].

## 2. User feedback, appeal and override

Thumbs-down and "talk to a person" on every answer; complaints tagged "assistant"; customers can ask
for any assistant-given account action to be reviewed. Feedback rates and appeal outcomes are analysed
monthly [nist-ai MEASURE 3.3, p. 36] [nist-ai-playbook MEASURE 3.3/action-2, p. 138].

## 3. Third-party and model updates

The foundation model is a pre-trained third-party component: version pinned; provider change notices
monitored; the evaluation suite is re-run before adopting any new model version
[nist-ai MANAGE 3.1, p. 37] [nist-ai MANAGE 3.2, p. 37] [nist-ai-playbook MANAGE 3.2/action-2, p. 55].

## 4. Incident severity

| Severity | Definition | Response | Escalation |
|---|---|---|---|
| 1 | Harmful advice acted on, data leak, or systematic wrong answers on safety topics | Disengage within 30 minutes | Head of Digital, DPO, CISO; regulator if required |
| 2 | Repeated wrong answers on a topic, guardrail bypass without leak | Restrict topic within 4 hours | Head of Digital |
| 3 | Isolated low-impact errors | Fix in next release | Product owner |

## 5. Response procedure

1. **Detect and log** every incident in the AI incident log [nist-ai GOVERN 4.3, p. 29].
2. **Contain - supersede, disengage or deactivate:** fall back to the static FAQ and human chat queue;
   the Duty Operations Manager may disengage without further approval when a severity-1 trigger is met
   [nist-ai MANAGE 2.4, p. 37] [nist-ai-playbook MANAGE 2.4/action-2, p. 53].
3. **Investigate:** for a previously unknown risk, follow the unknown-risk procedure and add it to the
   risk register [nist-ai MANAGE 2.3, p. 37].
4. **Recover:** re-run the evaluation suite and red-team prompts before re-enabling
   [nist-ai MEASURE 2.7, p. 35].
5. **Communicate** errors and incidents to relevant AI actors and affected customers, and record them
   [nist-ai MANAGE 4.3, p. 38] [nist-ai-playbook MANAGE 4.3/action-2, p. 59].
6. **Improve:** lessons learned feed the monthly review [nist-ai MANAGE 4.2, p. 38].

## 6. Decommissioning

If the assistant is retired: remove the entry point, retain conversation logs per retention schedule,
delete provider-side data under contract, update the AI inventory [nist-ai GOVERN 1.7, p. 28].

## 7. Records and sign-off

Incident log, override log and change log in the service-management tool; retention 2 years.

| Role | Name | Decision | Date |
|---|---|---|---|
| Head of Digital Customer Service | | Approve plan | |

This plan supports, but does not replace, professional judgement and the organisation's formal approval.
