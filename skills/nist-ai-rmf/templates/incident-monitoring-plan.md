# AI monitoring and incident response plan

> Template (library convention). Anchors: MEASURE 2.4 (production monitoring), MEASURE 3.1-3.3
> (tracking emergent risks, feedback and appeal), MANAGE 2.3 (previously unknown risks), MANAGE 2.4
> (supersede, disengage, deactivate), MANAGE 3.1-3.2 (third-party and pre-trained models), MANAGE 4.1
> (post-deployment monitoring plan), MANAGE 4.3 (incident communication), GOVERN 4.3 (incident
> identification and information sharing), GOVERN 1.7 (decommissioning).

| Field | Value |
|---|---|
| System / version | |
| Plan owner | |
| Authority to disengage / deactivate (MANAGE 2.4) | |
| Review cadence | |

## 1. Monitoring metrics and triggers (MEASURE 2.4, MANAGE 4.1)
| Metric | Characteristic | Data source | Frequency | Alert threshold (set by org) | Action on breach | Owner |
|---|---|---|---|---|---|---|

## 2. User feedback, appeal and override (MEASURE 3.3, MANAGE 4.1)
- Channels; triage SLA; appeal route; override logging:

## 3. Third-party and model updates (MANAGE 3.1, MANAGE 3.2)
- Upstream model/version change monitoring; re-evaluation triggers:

## 4. Incident definition and severity
| Severity | Definition (examples) | Response time | Escalation |
|---|---|---|---|

## 5. Response playbook
1. Detect and log (GOVERN 4.3)
2. Contain: degrade, fall back to non-AI process, or disengage/deactivate (MANAGE 2.4)
3. Investigate root cause; unknown risk -> MANAGE 2.3 procedure; update risk register
4. Recover and verify (re-run MEASURE tests before re-enabling)
5. Communicate to relevant AI actors and affected communities (MANAGE 4.3); regulators if required
6. Lessons learned -> continual improvement (MANAGE 4.2)

## 6. Decommissioning (GOVERN 1.7, MANAGE 4.1)
- Criteria, data retention/deletion, dependent systems, communication:

## 7. Records
- Where incidents, overrides and changes are logged; retention:
