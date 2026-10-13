# AI governance programme design - Harbour Community Bank

Designed using the NIST AI RMF 1.0 GOVERN function (Table 1, PDF pp. 27-29) and the AI RMF Playbook.
The AI RMF is **voluntary** and outcome-based; it does not prescribe structures, tolerances or templates,
so everything below is a proposal sized for a 900-person bank with ~25 models (credit, fraud, marketing,
one generative-AI pilot). GOVERN is cross-cutting and drives the system-level MAP, MEASURE and MANAGE
work (Section 5, PDF p. 25).

## 1. Policies and processes (GOVERN 1)

| Element | AI RMF outcome | Design |
|---|---|---|
| Regulatory register | GOVERN 1.1 [nist-ai GOVERN 1.1, p. 27] | Compliance maintains AI-relevant laws and supervisory guidance; quarterly review |
| AI policy | GOVERN 1.2 [nist-ai GOVERN 1.2, p. 27] | One AI policy embedding the seven trustworthy characteristics, linked to model risk and privacy policies |
| Risk tiering and tolerance | GOVERN 1.3 [nist-ai GOVERN 1.3, p. 27] | Three tiers by impact on customers; tolerance statements approved by the board risk committee |
| Transparent risk process | GOVERN 1.4 [nist-ai GOVERN 1.4, p. 27] | Documented lifecycle gates: intake, impact assessment, validation, approval, monitoring |
| Monitoring and review | GOVERN 1.5 [nist-ai GOVERN 1.5, p. 28] | Tier 1 annual review, Tier 2 every two years; policy review annually |
| AI inventory | GOVERN 1.6 [nist-ai GOVERN 1.6, p. 28] | Extend the model inventory to all AI incl. vendor and generative AI; named inventory owner [nist-ai-playbook GOVERN 1.6/action-2, p. 15] |
| Decommissioning | GOVERN 1.7 [nist-ai GOVERN 1.7, p. 28] | Retirement checklist: dependants, data retention, customer communication |

## 2. Accountability and training (GOVERN 2)

- RACI covering first line (model owners), second line (model risk / AI risk), third line (internal
  audit) [nist-ai GOVERN 2.1, p. 28]; separate development from validation
  [nist-ai-playbook GOVERN 2.1/action-3, p. 18].
- Role-based training: board, model owners, developers, front-line users [nist-ai GOVERN 2.2, p. 28].
- The Chief Risk Officer is the accountable executive; the board risk committee decides on Tier 1
  deployments and on any high residual risk [nist-ai GOVERN 2.3, p. 28].

## 3. People and oversight (GOVERN 3)

- Impact assessments for Tier 1 systems include compliance, customer advocacy and accessibility
  perspectives [nist-ai GOVERN 3.1, p. 28].
- Defined human-AI roles (approver, reviewer, override authority) per system [nist-ai GOVERN 3.2, p. 28].

## 4. Culture, documentation and incidents (GOVERN 4)

- Model documentation standard (system card) for every inventoried system [nist-ai GOVERN 4.2, p. 29].
- AI incidents reported through the operational-risk event process, with AI-specific categories
  [nist-ai GOVERN 4.3, p. 29].

## 5. Engagement (GOVERN 5)

- Complaints and customer-feedback data reviewed for AI-related themes quarterly [nist-ai GOVERN 5.1, p. 29].

## 6. Third parties (GOVERN 6)

- AI clauses in supplier contracts: data use, IP, change notification, audit rights
  [nist-ai GOVERN 6.1, p. 29]; contingency for failure of high-risk vendor AI
  [nist-ai GOVERN 6.2, p. 29].

## 7. How GOVERN drives the other functions

| Function | Governance requirement | Subcategories |
|---|---|---|
| MAP | Impact assessment / context record before build or purchase; tolerance per tier | MAP 1.1, MAP 1.5, MAP 5.1 |
| MEASURE | Independent validation for Tier 1; fairness and privacy testing | MEASURE 1.3, MEASURE 2.11, MEASURE 2.10 |
| MANAGE | Risk responses recorded; residual risk accepted by the right authority; monitoring and incident communication | MANAGE 1.3, MANAGE 1.4, MANAGE 4.1, MANAGE 4.3 |

## 8. Implementation roadmap

1. Q4 2026: inventory complete; policy approved; RACI agreed.
2. Q1 2027: tiering and tolerance; impact-assessment template live; training wave 1.
3. Q2 2027: Tier 1 systems re-assessed; current/target GOVERN profile re-run
   (`python -m agentlib ai-rmf check-profile`).

## 9. Decision requested

Board risk committee to approve the policy framework and tiering approach. This design supports, but
does not replace, the judgement of the bank's governing bodies and its legal and compliance advisers.
