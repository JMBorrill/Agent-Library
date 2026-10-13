# Human oversight design: <system name>

Owner: <name/role> · Reviewer: <name/role> · Date: YYYY-MM-DD

## 1. Decisions supported and automation level
Oversight matrix: `oversight-matrix.csv` (check: `oversight_check.py` result PASS/FAIL).

## 2. Who approves what
| Decision | Operator | Approver (before effect) | Four-eyes needed? |
|---|---|---|---|

## 3. Override and appeal
- How an operator overrides the AI output (UI path) and what is logged (who, when, reason code):
- How an affected individual asks for human review / complains; target response time:

## 4. Automation-bias mitigations
- Rationale and sources shown with every recommendation:
- Confidence / uncertainty display:
- Independent judgement first for high-impact decisions (operator records view before seeing AI output)?
- Periodic blind-review sample and override-rate monitoring:

## 5. Escalation
| Trigger | Escalate to | Within |
|---|---|---|

## 6. Kill switch and rollback
- Kill switch owner and deputy:
- Mechanism (feature flag / route to manual queue) and time to effect:
- Rollback triggers (metric thresholds) and last exercise date:
- Manual fallback process and capacity:

## 7. Logging and records
Decision log fields, retention, access controls.

## 8. Open issues; requires human sign-off
