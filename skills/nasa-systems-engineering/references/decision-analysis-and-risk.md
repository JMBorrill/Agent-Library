# Decision analysis (trade studies) and technical risk

Source: NASA SE Handbook, NASA/SP-2016-6105 Rev 2 (`nasa-se`), Sections 6.8 (PDF pp. 206-214) and 6.4
(PDF pp. 173-179). PDF pages.

## When formal decision analysis is warranted (6.8.1.1, PDF p. 209)

Many decisions need only clear input from the responsible disciplines. Formal analysis is warranted as
**complexity**, **uncertainty**, **multiple attributes** and **diversity of stakeholders** increase, and
when stakes for cost, safety or mission success are high. Effort should be commensurate with the
consequences of the decision (PDF p. 210).

## Steps (6.8.1.2, PDF pp. 209-212)

1. **Understand the decision** in the mission/system context: intended outcome in performance, cost and
   schedule; who the decision-making body is (PDF p. 209).
2. **Define criteria**: types (customer expectations and requirements, technology limitations,
   environmental impact, safety, risks, life-cycle cost, schedule), acceptable range and scale, rank by
   importance. Criteria should be objective, measurable and able to differentiate options. Criteria may be
   **mandatory** ("shall have") or enhancing; an option that fails a mandatory criterion is disregarded
   (PDF p. 210).
3. **Identify alternatives** covering the decision space (design, operational, cost, schedule options);
   brainstorming, literature search, trade trees to prune; document options considered and dropped; doing
   nothing can be an option (PDF pp. 210-211).
4. **Select evaluation methods and tools** proportionate to the decision: simulations, weighted tradeoff
   matrices, trade studies, surveys, human-in-the-loop testing, prototypes, testing (PDF p. 211).
5. **Evaluate** each alternative against each criterion, considering uncertainty - it matters if reducing
   it could change the ranking. Normalise criteria with operational definitions of each scale point (e.g.
   "high" = probability of 67 percent and above) (PDF pp. 211-212).
6. **Recommend**: usually a single alternative, but present all closely ranked alternatives when they do not
   differ significantly or uncertainty could alter the ranking. If a lower-scoring option is recommended,
   explain why and re-examine the criteria with the decision-maker (PDF p. 212).
7. **Report and capture** assumptions, uncertainties, sensitivities, methods and lessons learned
   (PDF pp. 212-213).

Completing the decision matrix is the default evaluation method; every cell for every criterion and option
is completed by the team (note, PDF p. 212). It is best practice to document a decision matrix for a major
decision even if only one alternative is viable (PDF p. 211).

Tool: `python -m agentlib nasa-se trade-study <file>` normalises weights, screens mandatory criteria,
ranks alternatives and flags close rankings (default 5% margin - a library convention, not a handbook value).

## Decision report contents (6.8.1.3 and Table 6.8-1, PDF pp. 213-214)

Report items: mission and system context; decision needed and intended outcomes; decision criteria;
alternatives; evaluation methods and tools; assumptions, uncertainties and sensitivities; results of all
evaluations; recommendations; final decision with rationale; lessons learned (PDF p. 213).
Table 6.8-1 sections: 1 Executive Summary; 2 Problem/Issue Description; 3 Decision Matrix Setup
Rationale (criteria, options, weights, evaluation methods); 4 Decision Matrix Scoring Rationale; 5 Final
Decision Matrix; 6 Risk/Benefits; 7 Recommendation and/or Final Decision; 8 Dissent; 9 References;
A Appendices (PDF pp. 213-214). Template: [../templates/trade-study-matrix.md](../templates/trade-study-matrix.md).

## Technical risk (6.4)

- Risk is the potential for performance shortfalls with respect to explicitly established requirements,
  in the safety, technical, cost and schedule domains (PDF p. 173).
- Characterised by **triplets**: the scenario(s) leading to degraded performance, their likelihood(s), and
  the consequence(s); uncertainties are included in likelihoods and consequences (PDF pp. 173, 175).
  Scenarios begin with initiating events (PDF p. 173).
- Risk management = **Risk-Informed Decision Making (RIDM)**, which informs direction-setting decisions such
  as design choices, plus **Continuous Risk Management (CRM)**, which manages risks during implementation
  (NPR 8000.4; PDF p. 177).
- Activities: strategy; identify risks with clear risk statements; assess; prepare mitigation (select risks,
  set trigger thresholds, stakeholders to inform); monitor periodically (more often near thresholds; report
  at life-cycle reviews); implement mitigation/contingency when triggered until residual risk is acceptable;
  capture work products (PDF pp. 177-178).
- Outputs: mitigation/contingency actions, technical risk reports, work products (PDF p. 179).
- Risk categories defined in the key-concepts box: cost, schedule, technical and programmatic risk
  (PDF p. 175).

Template: [../templates/risk-record.md](../templates/risk-record.md). The handbook defers detailed risk
scoring scales to NASA/SP-2011-3422 (Risk Management Handbook) and NASA/SP-2010-576 (RIDM Handbook),
which are not part of the source pack - do not invent likelihood/consequence thresholds; use the
project's Risk Management Plan.
