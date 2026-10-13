# Framework selection

## Problem characterisation
LLM assistant (AI system) in a public service; consequences include harm to citizens' rights and access to
benefits; a funding decision is needed.

## Selected frameworks

| Framework | Skill | Role | Status |
|---|---|---|---|
| NIST AI RMF + Playbook | `nist-ai-rmf` | product (trustworthiness) and governance | advisory unless adopted by departmental policy |
| HM Treasury Green Book | `green-book-appraisal` | decision (value for money) | mandatory for central government spending proposals per departmental rules — confirm with the finance team |
| OWASP ASVS | `owasp-asvs` | product (application security) | advisory |
| NIST SSDF | `nist-ssdf` | process (secure development) | advisory |

## Plan
Run `ai-system-assurance` (agents `ai-risk-assessor`, `ai-governance-advisor`) for the risk assessment and
`public-investment-business-case` (agent `economic-appraisal-analyst`) for funding approval, with
`evidence-auditor` on both.
