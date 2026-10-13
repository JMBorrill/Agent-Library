# Northfield Mutual - AI RMF GOVERN profile: gap analysis

Scope: enterprise AI governance, GOVERN function only (19 subcategories, Table 1, PDF pp. 27-29).
Profiles per AI RMF Section 6 (PDF p. 38); NIST prescribes no profile template, so the status scale is
the library convention. Tool: `python -m agentlib ai-rmf check-profile govern-profile.yaml`.

## Validation result

The submitted profile **fails** one check: GOVERN 1.1 is marked `implemented` but no evidence is
recorded (the note says legal tracks AI laws "informally"). I have re-rated GOVERN 1.1 current status
to `partially-implemented` pending a documented regulatory register. All other rows are valid.

## Corrected profile

| Subcategory | Current status | Target status | Priority | Owner | Evidence | Notes |
|---|---|---|---|---|---|---|
| GOVERN 1.1 | partially-implemented | implemented | high | General Counsel | Informal legal tracking (no register) | Re-rated from implemented: no evidence |
| GOVERN 1.2 | partially-implemented | implemented | high | Chief Risk Officer | Draft AI policy v0.3 | |
| GOVERN 1.3 | not-implemented | implemented | high | Chief Risk Officer | | |
| GOVERN 1.4 | partially-implemented | largely-implemented | medium | Chief Risk Officer | ERM policy section 4 | |
| GOVERN 1.5 | not-implemented | implemented | medium | AI Risk Committee secretary | | |
| GOVERN 1.6 | partially-implemented | implemented | high | CIO | Spreadsheet of 14 models (incomplete) | |
| GOVERN 1.7 | not-implemented | largely-implemented | low | CIO | | |
| GOVERN 2.1 | partially-implemented | implemented | high | COO | RACI draft | |
| GOVERN 2.2 | not-implemented | implemented | medium | HR Learning lead | | |
| GOVERN 2.3 | largely-implemented | implemented | high | CEO | Board risk committee ToR 2026 | |
| GOVERN 3.1 | partially-implemented | largely-implemented | medium | Head of Data Science | | |
| GOVERN 3.2 | not-implemented | implemented | high | COO | | |
| GOVERN 4.1 | partially-implemented | largely-implemented | low | CTO | Engineering principles page | |
| GOVERN 4.2 | partially-implemented | implemented | medium | Head of Data Science | Model documentation standard | |
| GOVERN 4.3 | not-implemented | implemented | high | CISO | | |
| GOVERN 5.1 | not-implemented | partially-implemented | low | Head of Customer Experience | | |
| GOVERN 5.2 | not-implemented | partially-implemented | low | Head of Data Science | | |
| GOVERN 6.1 | partially-implemented | implemented | high | Head of Procurement | Standard supplier contract (no AI clauses) | |
| GOVERN 6.2 | not-implemented | implemented | medium | Head of Procurement | | |

## Gap summary

| Category | Subcategories | Implemented | Gaps | High-priority gaps |
|---|---|---|---|---|
| GOVERN 1 policies, processes, inventory | 7 | 0 | 7 | 4 |
| GOVERN 2 accountability and training | 3 | 0 | 3 | 2 |
| GOVERN 3 diversity and human-AI roles | 2 | 0 | 2 | 1 |
| GOVERN 4 risk culture | 3 | 0 | 3 | 1 |
| GOVERN 5 engagement | 2 | 0 | 2 | 0 |
| GOVERN 6 third parties | 2 | 0 | 2 | 1 |
| **Total** | **19** | **0** | **19** | **9** |

Main themes: no risk-tolerance process (GOVERN 1.3), incomplete AI inventory (GOVERN 1.6), no
human-AI oversight role definitions (GOVERN 3.2), no AI incident process (GOVERN 4.3), and supplier
contracts without AI clauses (GOVERN 6.1).

## Action plan (high priority first)

| Gap | Action (Playbook item) | Owner | Due | Evidence of closure |
|---|---|---|---|---|
| GOVERN 1.3 | Define impact and likelihood assessment scales and an overall risk scoring approach [nist-ai-playbook GOVERN 1.3/action-3, p. 10] [nist-ai-playbook GOVERN 1.3/action-4, p. 10] | Chief Risk Officer | Q1 2027 | Approved AI risk tolerance and rating standard |
| GOVERN 1.6 | Policy for creating and maintaining the AI inventory and a named inventory owner [nist-ai-playbook GOVERN 1.6/action-1, p. 15] [nist-ai-playbook GOVERN 1.6/action-2, p. 15] | CIO | Q4 2026 | Complete inventory with owners and risk tier |
| GOVERN 3.2 | Define and differentiate human roles for human-AI configurations [nist-ai-playbook GOVERN 3.2/action-1, p. 23] | COO | Q1 2027 | Oversight role descriptions in RACI |
| GOVERN 4.3 | Policies for reporting and documenting incident response [nist-ai-playbook GOVERN 4.3/action-3, p. 29] | CISO | Q1 2027 | AI incident procedure integrated with security IR |
| GOVERN 6.1 | Policies addressing third-party AI systems and data [nist-ai-playbook GOVERN 6.1/action-1, p. 34] | Head of Procurement | Q1 2027 | AI contract clause library in use |
| GOVERN 1.1 | Maintain awareness of applicable legal/regulatory requirements; document a regulatory register [nist-ai-playbook GOVERN 1.1/action-1, p. 6] | General Counsel | Q4 2026 | Regulatory register with review dates |
| GOVERN 1.2 | Connect AI governance to existing governance and risk controls [nist-ai-playbook GOVERN 1.2/action-2, p. 8] | Chief Risk Officer | Q1 2027 | Approved AI policy v1.0 |
| GOVERN 2.1 | Define AI risk roles and responsibilities [nist-ai-playbook GOVERN 2.1/action-1, p. 17] | COO | Q4 2026 | Approved RACI |
| GOVERN 2.3 | Board committee oversight integrated with ERM [nist-ai-playbook GOVERN 2.3/action-2, p. 21] | CEO | Q4 2026 | Committee minutes showing AI risk decisions |

Medium and low priority gaps (GOVERN 1.4, 1.5, 1.7, 2.2, 3.1, 4.1, 4.2, 5.1, 5.2, 6.2) follow in 2027;
see `ai-rmf show` for Playbook actions. Playbook actions are voluntary suggestions (Playbook PDF p. 4).

This analysis supports, but does not replace, the judgement of the risk committee and board.
