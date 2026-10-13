# AI RMF Core: functions and categories

Source: `nist-ai` (NIST AI 100-1, AI RMF 1.0, January 2023), Section 5 and Tables 1-4. Pages are PDF
pages (printed page = PDF page - 5). Category statements below are verbatim from the tables; the
"how to apply" notes are this library's paraphrase. Get exact subcategory text with
`python -m agentlib ai-rmf show "<ID>"` or `ai-rmf list --function <FN> --full`.

## How the Core fits together (Section 5, PDF pp. 25-26)

- Four functions: GOVERN, MAP, MEASURE, MANAGE; each broken into categories and subcategories.
- The actions "do not constitute a checklist, nor are they necessarily an ordered set of steps" (PDF p. 25).
- GOVERN is cross-cutting and infused through the other three (Fig. 5, PDF p. 25).
- After instituting GOVERN outcomes, most users start with MAP and continue to MEASURE or MANAGE; the
  process is iterative with cross-referencing between functions (PDF p. 26).
- Organisations may select from among categories and subcategories according to resources and
  capabilities (PDF p. 26) - a profile records that selection.

## Counts (verified against Tables 1-4)

| Function | Section / start page | Categories | Subcategories | Table pages |
|---|---|---|---|---|
| GOVERN | 5.1, PDF p. 26 | 6 | 19 | 27-29 |
| MAP | 5.2, PDF p. 29 | 5 | 18 | 31-33 |
| MEASURE | 5.3, PDF p. 33 | 4 | 22 | 34-36 |
| MANAGE | 5.4, PDF p. 36 | 4 | 13 | 37-38 |
| **Total** | | **19** | **72** | |

## Categories

| Category | Statement (verbatim) | Subcategories | PDF pp. |
|---|---|---|---|
| GOVERN 1 | Policies, processes, procedures, and practices across the organization related to the mapping, measuring, and managing of AI risks are in place, transparent, and implemented effectively. | GOVERN 1.1-1.7 (7) | 27-28 |
| GOVERN 2 | Accountability structures are in place so that the appropriate teams and individuals are empowered, responsible, and trained for mapping, measuring, and managing AI risks. | GOVERN 2.1-2.3 (3) | 28 |
| GOVERN 3 | Workforce diversity, equity, inclusion, and accessibility processes are prioritized in the mapping, measuring, and managing of AI risks throughout the lifecycle. | GOVERN 3.1-3.2 (2) | 28 |
| GOVERN 4 | Organizational teams are committed to a culture that considers and communicates AI risk. | GOVERN 4.1-4.3 (3) | 28-29 |
| GOVERN 5 | Processes are in place for robust engagement with relevant AI actors. | GOVERN 5.1-5.2 (2) | 29 |
| GOVERN 6 | Policies and procedures are in place to address AI risks and benefits arising from third-party software and data and other supply chain issues. | GOVERN 6.1-6.2 (2) | 29 |
| MAP 1 | Context is established and understood. | MAP 1.1-1.6 (6) | 31 |
| MAP 2 | Categorization of the AI system is performed. | MAP 2.1-2.3 (3) | 31-32 |
| MAP 3 | AI capabilities, targeted usage, goals, and expected benefits and costs compared with appropriate benchmarks are understood. | MAP 3.1-3.5 (5) | 32 |
| MAP 4 | Risks and benefits are mapped for all components of the AI system including third-party software and data. | MAP 4.1-4.2 (2) | 32 |
| MAP 5 | Impacts to individuals, groups, communities, organizations, and society are characterized. | MAP 5.1-5.2 (2) | 32-33 |
| MEASURE 1 | Appropriate methods and metrics are identified and applied. | MEASURE 1.1-1.3 (3) | 34 |
| MEASURE 2 | AI systems are evaluated for trustworthy characteristics. | MEASURE 2.1-2.13 (13) | 34-35 |
| MEASURE 3 | Mechanisms for tracking identified AI risks over time are in place. | MEASURE 3.1-3.3 (3) | 35-36 |
| MEASURE 4 | Feedback about efficacy of measurement is gathered and assessed. | MEASURE 4.1-4.3 (3) | 36 |
| MANAGE 1 | AI risks based on assessments and other analytical output from the MAP and MEASURE functions are prioritized, responded to, and managed. | MANAGE 1.1-1.4 (4) | 37 |
| MANAGE 2 | Strategies to maximize AI benefits and minimize negative impacts are planned, prepared, implemented, documented, and informed by input from relevant AI actors. | MANAGE 2.1-2.4 (4) | 37 |
| MANAGE 3 | AI risks and benefits from third-party entities are managed. | MANAGE 3.1-3.2 (2) | 37 |
| MANAGE 4 | Risk treatments, including response and recovery, and communication plans for the identified and measured AI risks are documented and monitored regularly. | MANAGE 4.1-4.3 (3) | 38 |

## Applying each function (paraphrase)

### GOVERN (PDF pp. 26-29)
Organisation-level: policies and legal requirements (1.1-1.4), monitoring and periodic review (1.5),
**AI system inventory** (1.6), **decommissioning** (1.7), roles and training (2.1-2.2), **executive
accountability for AI risk decisions** (2.3), diverse teams and human-AI oversight roles (3.1-3.2),
safety-first culture, impact documentation and incident information-sharing (4.1-4.3), external
feedback (5.1-5.2), third-party IP and contingency for high-risk third-party data/systems (6.1-6.2).
Typical evidence: approved AI policy, RACI, inventory extract, training records, committee minutes,
supplier contract clauses, decommissioning procedure.

### MAP (PDF pp. 29-33)
System-level context: purposes, laws/norms, users and impacts (1.1); team diversity (1.2); mission and
business value (1.3-1.4); **risk tolerances** (1.5); requirements (1.6); task/method, knowledge limits,
TEVV considerations (2.1-2.3); benefits, costs, scope, operator proficiency, **human oversight**
(3.1-3.5); component and third-party risks and controls (4.1-4.2); **likelihood and magnitude of each
impact** and engagement practices (5.1-5.2). Completing MAP should allow an initial go/no-go decision
(PDF p. 30).

### MEASURE (PDF pp. 33-36)
Select metrics starting with the most significant risks and document what is not measured (1.1);
review metrics (1.2); independent assessors (1.3); TEVV of each trustworthy characteristic (2.1-2.13,
see `trustworthy-characteristics.md`); track emergent and hard-to-measure risks and user feedback
(3.1-3.3); check measurement efficacy in deployment context (4.1-4.3). Section 5.3 notes TEVV before
deployment and regularly in operation, with uncertainty measures and benchmarks (PDF p. 33).

### MANAGE (PDF pp. 36-38)
Go/no-go determination (1.1); prioritise by impact, likelihood and resources (1.2); responses -
**mitigating, transferring, avoiding, or accepting** (1.3); **residual risks documented** for
downstream acquirers and end users (1.4); non-AI alternatives and resources (2.1); sustain value (2.2);
respond to previously unknown risks (2.3); **supersede, disengage or deactivate** (2.4); third-party
and pre-trained model monitoring (3.1-3.2); post-deployment monitoring plans, continual improvement,
incident communication (4.1-4.3).

## Risk concepts used throughout (Section 1, PDF pp. 9-14)

- Risk = composite of probability of an event and magnitude of its consequences; impacts can be
  positive or negative (Section 1.1, PDF p. 9).
- Harm can be to people, organisations and ecosystems (Fig. 1, PDF p. 10).
- Measurement challenges: third-party components, emergent risks, lack of reliable metrics,
  lifecycle stage, real-world vs lab, inscrutability, human baseline (Section 1.2.1, PDF pp. 10-11).
- The AI RMF does not prescribe risk tolerance (Section 1.2.2, PDF p. 12).
- Unacceptable risk: cease development/deployment safely until managed (Section 1.2.3, PDF p. 13).
- Residual risk = risk remaining after treatment; document it (PDF p. 13).
- Integrate AI risk with enterprise risk management, cybersecurity and privacy (Section 1.2.4, PDF p. 13).
- AI actors and lifecycle stages: Figs. 2-3 (PDF pp. 15-16) and Appendix A (PDF p. 40);
  AI vs traditional software risks: Appendix B (PDF p. 43).
