# Appraisal process: rationale, longlist and shortlist (Green Book 2026)

Citations give the paragraph number, the PDF page of `hm-treasury-green-book-2026.pdf` and the printed page.
For body pages, the printed page is the PDF page minus 6. Catalog ids are from `catalog/green-book.json`.

## Context

- **What it is and who uses it.** Appraisal assesses the costs, benefits and risks of the options for meeting
  government objectives (para 2.1). It is mandatory for departments and arm's length bodies on significant
  spending, and is also used for regulatory impact assessments (paras 1.3-1.4, PDF p.7).
- **ROAMEF.** The cycle runs Rationale, Objectives, Appraisal, Monitoring, Evaluation, Feedback. The Green Book
  covers the first three stages; the Magenta Book covers M&E (paras 2.2-2.3, PDF p.9).
- **Value for money (Box 1, PDF p.10).** A balanced judgement across six factors:
  - performance against objectives and CSFs;
  - monetisable costs and benefits;
  - unmonetisable costs and benefits;
  - public sector financial impact;
  - distribution across groups and places;
  - risk and uncertainty.
  An option that fails its objectives cannot be value for money.

## The four stages (Table 1, para 2.8, PDF p.11 / printed p.5)

| Stage | What it produces | Catalog id |
|---|---|---|
| 1. Rationale and objectives | Why act, what is needed, and what happens if government does not act; SMART objectives | `stage.1-rationale-objectives` |
| 2. Options generation and longlist appraisal | A wide longlist narrowed to a shortlist | `stage.2-options-longlist` |
| 3. Shortlist appraisal | Social CBA or CEA of the shortlisted options | `stage.3-shortlist` |
| 4. Preferred option | A single option that optimises value for money, advised to decision makers | `stage.4-preferred-option` |

All four stages must be informed by evidence, including previous evaluations (para 2.9).

## Rationale and objectives (Chapter 4, PDF pp.23-28)

Develop these five components (para 4.1).

1. **Case for change** (paras 4.2-4.8). Explain why government needs to act and why businesses, households or
   charities cannot achieve the outcomes themselves.
   - Typical rationales are market failures (public goods, externalities, market power, imperfect information,
     co-ordination failure) and equity.
   - PESTLE analysis is optional context.
2. **Theory of change** (paras 4.9-4.13). Show the chain from inputs to outputs to outcomes.
   - It must rest on evidence; do not simply assert it.
   - State the assumptions so that decision makers can agree them.
3. **Business as usual** (paras 4.14-4.19, PDF p.26).
   - BAU is the expected outcome if current arrangements continue. It is not "do nothing".
   - Describe it fairly: overstating BAU costs makes intervention look better than it is.
   - Monetise BAU where possible.
   - Present options in absolute terms and avoid normalising BAU to zero (para 4.19).
   - Use BAU to separate deadweight from additionality (para 4.17).
4. **SMART objectives** (paras 4.20-4.26). Objectives must be specific, measurable, achievable, realistic and
   time-limited.
   - Keep them few.
   - Prefer outcome-based objectives over output-based ones.
5. **Strategic fit** (para 4.27). Show alignment with the parent programme or portfolio, with the
   organisation's other work, and with other public bodies.

**Transformational change.** Claims of transformational change must be explained transparently and backed by
evidence (para 4.30). **Policy hierarchy.** A project appraisal does not need to justify its parent programme
(paras 3.6-3.10, PDF p.18).

## Longlist (Chapter 5, PDF pp.29-36)

- **Purpose.** Think broadly and creatively. Options generation and longlist appraisal are often skipped; they
  must not be (paras 5.1-5.3).
- **Documentation.** Record every option considered and why it was, or was not, progressed (para 5.4).
- **Critical success factors** (Table 4, PDF p.30):
  1. objectives and strategic fit;
  2. value for money;
  3. supplier capacity and capability;
  4. affordability;
  5. achievability.
  Constraints can also be CSFs: legal, ethical, social acceptability, timing, environmental (para 5.6).
- **Which options pass.** Any option that fails the objectives or a CSF does not go to the shortlist
  (para 5.9).
- **Estimates.** Longlist estimates are indicative ranges, not full CBA (para 5.10).
- **Other checks.** Consider dependencies and unintended consequences, such as gaming of incentive schemes
  (paras 5.11-5.12).

### Methods (paras 5.13-5.16)

- The options framework filter (OFF) is recommended but not mandatory.
- MCDA is acceptable if it uses swing weighting and an expert facilitator.
- Simple weighting-and-scoring MCA is **recommended against**.
- SWOT may be used.

### Options framework filter (paras 5.21-5.35, PDF pp.32-36)

- **How it runs.** Through structured, facilitated workshops with explicit deliberation (paras 5.22-5.23).
- **Categories, in order.** Scope, then solution, then delivery, then implementation, then funding
  (para 5.25). Each stage builds on the green choices from the earlier stages (paras 5.28-5.32).
- **Ratings** (para 5.26):
  - **Green**: best meets the CSFs.
  - **Amber**: meets the CSFs, but less well.
  - **Red**: fails the CSFs and is dropped.
  Record the reason for every rating, with evidence, assumptions and sources (para 5.27).
- **Presentation.** Use an options summary matrix alongside the workshop record (para 5.33; Table 5 example).
  Template: [options-longlist-matrix.md](../templates/options-longlist-matrix.md).

### Shortlist (paras 5.17-5.20, 5.35, PDF pp.32, 36)

Aim for around five options:

- **BAU**: always included, as the benchmark.
- **Do minimum**: just meets the objectives, which exposes any gold plating in other options.
- **Preferred way forward**: all-green option choices.
- **More ambitious**: some greens swapped for ambers, giving higher benefits at higher cost or risk.
- **Less ambitious**: some greens swapped for ambers, giving lower benefits at lower cost or risk. This can be
  omitted if the preferred way forward is the do minimum.

The preferred way forward from the longlist can differ from the preferred option chosen after shortlist
appraisal (para 5.20).

## Shortlist appraisal (Chapter 6, PDF pp.37-54)

The flow follows Figure 5 (PDF p.37).

1. **Choose a method.** Use social CBA by default; use CEA where the main benefits cannot be monetised or the
   options deliver the same output (para 6.4).
2. **Scope.** All UK residents (paras 6.5-6.7). ODA proposals also count recipient-country impacts (para 6.8).
3. **Time horizon** (paras 6.9-6.13). Cover the whole lifetime. Standard periods, counted after year 0:
   - 60 years for infrastructure;
   - 30 years for refurbishment;
   - 10 years for regulations;
   - 10 years for other proposals.
   Agree anything longer with HM Treasury.
4. **Climate scenarios** (para 6.14). Use 2°C warming if the horizon ends before 2040, and both 2°C and 4°C if
   it ends in 2040 or later.
5. **Classify costs and benefits** (paras 6.23-6.31; Figure 6):
   - monetisable, split into cash and non-cash;
   - unmonetisable, split into quantifiable and qualitative;
   - costs split into capital, operating and maintenance.
6. **Exclusions and treatments** (paras 6.32-6.44):
   - exclude sunk costs;
   - handle transfers consistently;
   - exclude GDP/GVA effects and Keynesian multipliers;
   - exclude the cost of raising public funds, except for private finance options.
7. **Real terms and discounting** (paras 6.45-6.59). See
   [discounting-and-metrics.md](discounting-and-metrics.md).
8. **Risk, optimism bias and contingency** (paras 6.60-6.84). See
   [risk-and-optimism-bias.md](risk-and-optimism-bias.md).
9. **Public sector financial impact** (paras 6.85-6.91). Show it in nominal terms and undiscounted.
   Cost-shifting between public bodies is not value for money (para 6.87).
10. **Summary metrics, ranking, sensitivity and switching values** (paras 6.93-6.105).
11. **Distributional and place-based analysis** (Chapter 7) and **presentation in the AST** (Chapter 9).

## Statutory duties (para 3.18, PDF pp.21-22)

Reflect these explicitly at both longlist and shortlist stages:

- the EPPS duty under the Environment Act 2021;
- the biodiversity duty (England);
- the public sector equality duty (PSED).

Devolved governments may add their own duties (para 3.19).
