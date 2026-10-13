---
name: nist-ai-rmf
description: >-
  AI system risk assessment and AI governance with the NIST AI Risk Management Framework (AI RMF 1.0,
  NIST AI 100-1) and the NIST AI RMF Playbook: mapping context and impacts (MAP), measuring and testing
  trustworthiness (MEASURE), prioritising and treating risk (MANAGE) and organisational governance
  (GOVERN) across the 72 subcategories and the seven trustworthy-AI characteristics. Produces impact
  assessments / context records, AI risk registers, current/target profiles with gap analysis, model/
  system cards and monitoring & incident plans, validated by deterministic tools. Use when asked to
  assess or govern an AI/ML or generative-AI system, write an AI impact assessment, build or review an
  AI risk register, create an AI RMF profile or gap analysis, map controls to AI RMF subcategories, or
  look up what a subcategory or the Playbook says.
license: Skill text MIT; NIST AI 100-1 and the AI RMF Playbook are U.S. Government works (NIST)
metadata:
  version: 1.0.0
  category: ai-governance
  maturity: beta
  sources: [nist-ai, nist-ai-playbook]
  catalogs: [nist-ai-rmf, nist-ai-rmf-playbook]
  tools:
    - "python -m agentlib ai-rmf list"
    - "python -m agentlib ai-rmf show"
    - "python -m agentlib ai-rmf characteristics"
    - "python -m agentlib ai-rmf profile-template"
    - "python -m agentlib ai-rmf check-profile"
    - "python -m agentlib ai-rmf register-template"
    - "python -m agentlib ai-rmf check-register"
    - "python -m agentlib ai-rmf scan"
---

# NIST AI RMF 1.0 - AI risk assessment and governance

The AI RMF Core has **4 functions, 19 categories and 72 subcategories** (Tables 1-4, PDF pp. 27-38):
GOVERN 19, MAP 18, MEASURE 22, MANAGE 13. The Playbook gives voluntary *suggested actions* and
*transparency & documentation questions* for every subcategory. All outcome text, page numbers and
Playbook actions come from `catalog/nist-ai-rmf.json` and `catalog/nist-ai-rmf-playbook.json` - **never
quote a subcategory or invent an id from memory; run the tools.** Ids look like `GOVERN 1.1`,
`MAP 5.1`, `MEASURE 2.11`, `MANAGE 4.3` (there is no GOVERN 7, MAP 6 or MEASURE 2.14). <!-- evidence:ignore -->

## When to use

- **AI impact assessment / context record** for a new or changed AI system (MAP; go/no-go input).
- **AI risk register**: identify, rate, treat and track AI risks against trustworthiness characteristics.
- **Current / target profile and gap analysis** for an organisation, business unit or system (Section 6).
- **Measurement / TEVV planning**: what to test for validity, safety, security, bias, privacy, explainability.
- **Governance design or review**: policies, roles, inventory, oversight, third-party AI, decommissioning.
- **Monitoring & incident planning** for deployed systems (MANAGE 2.4, 4.1, 4.3; MEASURE 2.4, 3.x).
- **Lookups**: "what does MAP 1.5 say", "what does the Playbook suggest for MEASURE 2.11".

Not for: legal advice on specific AI regulations, or certifying conformity - the AI RMF is voluntary and
has no certification scheme. For hosting-software security use `skills/owasp-asvs/`; for citation and
evidence discipline use `skills/evidence-and-citation/`.

## Workflow

### 0. Frame the engagement
1. Establish the **AI system(s)** in scope, lifecycle stage (plan/design, build, verify, deploy, operate,
   retire), the organisation's role (developer, deployer, acquirer) and the deliverables requested.
2. Ask for (or record as assumptions) the organisation's **risk tolerance** (MAP 1.5, GOVERN 1.3).
   The AI RMF does **not** prescribe risk tolerance (Section 1.2.2, PDF p. 12) - never invent one.
3. Pick templates from [templates/](templates/) - see *Outputs*.

### 1. MAP - context and impacts (do this first; it is the basis for MEASURE and MANAGE)
1. Fill [templates/ai-context-record.md](templates/ai-context-record.md): intended purpose and
   beneficial uses, context-specific laws/norms, deployment setting, users and affected people
   (MAP 1.1), mission and business value (MAP 1.3, 1.4), risk tolerance (MAP 1.5), system requirements
   (MAP 1.6), task and method (MAP 2.1), knowledge limits and human oversight (MAP 2.2, MAP 3.5),
   TEVV considerations (MAP 2.3), benefits and costs (MAP 3.1, 3.2), application scope (MAP 3.3),
   third-party components (MAP 4.1, 4.2) and impact likelihood/magnitude (MAP 5.1).
2. Include **foreseeable misuse / use beyond intended purpose** and **non-AI alternatives**
   (`ai-rmf show "MAP 1.1"` lists the Playbook actions).
3. Record the **go/no-go input**: Section 5.2 says completing MAP should give enough context for an
   initial go/no-go decision (PDF p. 30). State who decides; the agent only recommends.

### 2. Identify and rate risks per trustworthiness characteristic
1. Run `python -m agentlib ai-rmf characteristics` and walk all seven: valid & reliable; safe; secure &
   resilient; accountable & transparent; explainable & interpretable; privacy-enhanced; fair - with
   harmful bias managed (Section 3, PDF pp. 17-23). Note tradeoffs between them explicitly.
2. Generate a register: `python -m agentlib ai-rmf register-template --format yaml -o register.yaml`
   (or `csv`/`md`; see [templates/ai-risk-register.md](templates/ai-risk-register.md)).
3. For each risk record: id, description (event, cause, consequence), affected stakeholders,
   characteristic(s), likelihood, impact, inherent rating, treatment (**mitigate / transfer / avoid /
   accept**, MANAGE 1.3), controls, residual rating, owner, linked subcategories, review date.
4. Scales: use the organisation's matrix if it has one. Otherwise use the library convention
   (1-5 x 1-5; bands 1-4 low, 5-9 medium, 10-16 high, 20-25 critical) and **say it is a convention** -
   the Playbook only describes risk as approximately impact x likelihood on a qualitative or
   quantitative scale (GOVERN 1.3 "About", Playbook PDF p. 9).
5. Validate: `python -m agentlib ai-rmf check-register register.yaml`. Fix every error. Rules enforced:
   all required fields; valid subcategory ids and characteristics; residual must not exceed inherent
   without `residual_justification`; `accept` needs `accepted_by`; **high/critical residual needs
   `escalated_to` or `accepted_by`**. Read warnings (matrix inconsistencies, missing controls).

### 3. MEASURE - plan the evidence
1. Map each characteristic to its MEASURE 2 subcategory (valid & reliable 2.5, safe 2.6, secure &
   resilient 2.7, accountable & transparent 2.8, explainable & interpretable 2.9, privacy 2.10,
   fair/bias 2.11, environmental 2.12; see
   [references/trustworthy-characteristics.md](references/trustworthy-characteristics.md)).
2. For each, name metrics, test sets, thresholds **set by the organisation** (never from the AI RMF),
   disaggregation, who tests (independence per MEASURE 1.3) and what cannot be measured (MEASURE 1.1).
3. Pull concrete suggested actions with `python -m agentlib ai-rmf show "MEASURE 2.11"` and cite
   them by Playbook item id (e.g. `MEASURE 2.11/action-1`).

### 4. MANAGE - treat, monitor, respond
1. Decide proceed / proceed with conditions / do not proceed (MANAGE 1.1) - as a **recommendation**.
2. Prioritise treatment (MANAGE 1.2), plan responses (MANAGE 1.3), document residual risk to
   downstream acquirers and end users (MANAGE 1.4).
3. Write the monitoring and incident plan from
   [templates/incident-monitoring-plan.md](templates/incident-monitoring-plan.md): monitoring metrics
   and triggers (MEASURE 2.4, MANAGE 4.1), supersede/disengage/deactivate criteria and authority
   (MANAGE 2.4), unknown-risk response (MANAGE 2.3), third-party/pre-trained model monitoring
   (MANAGE 3.1, 3.2), incident communication to affected communities (MANAGE 4.3).
4. Produce a model/system card from [templates/model-system-card.md](templates/model-system-card.md)
   (MAP 2.2 knowledge limits, MEASURE 2.9 explanation, MANAGE 1.4 residual risks).

### 5. GOVERN - organisational profile and gaps
1. `python -m agentlib ai-rmf profile-template --format yaml -o profile.yaml` (add `--functions GOVERN`
   to limit scope). Fill current and target status (`not-implemented`, `partially-implemented`,
   `largely-implemented`, `implemented`, `not-applicable`), priority, owner, **evidence**, notes.
2. `python -m agentlib ai-rmf check-profile profile.yaml` - fixes: unknown ids, missing subcategories,
   invalid statuses, `implemented` without evidence. The report gives gaps (target > current) by
   function and category, highest priority first.
3. Turn gaps into an action plan citing Playbook actions (`ai-rmf show <id>`); see
   [templates/ai-profile.md](templates/ai-profile.md) and
   [references/profiles-and-registers.md](references/profiles-and-registers.md).

### 6. Quality gate before delivery
Run `python -m agentlib ai-rmf scan <deliverable.md>` - it fails on any invented subcategory id and
shows coverage per function. Re-run `check-register` / `check-profile` on the final artefacts.

## Decision rules

- **Unacceptable risk**: where significant negative impacts are imminent, severe harms are occurring or
  catastrophic risks are present, development/deployment should cease safely until risks are managed
  (Section 1.2.3, PDF p. 13). Recommend stop; escalate to the accountable executive (GOVERN 2.3).
- **High/critical residual risk** is never silently accepted: name the escalation body or the accepting
  authority and date (MANAGE 1.3, 1.4; GOVERN 2.3).
- **Cannot measure ≠ low risk**: the inability to measure a risk does not imply high or low risk
  (Section 1.2.1, PDF p. 10). Record unmeasured risks (MEASURE 1.1) and track them (MEASURE 3.2).
- **Third-party / foundation models**: treat as in scope - GOVERN 6.1-6.2, MAP 4.1-4.2, MANAGE 3.1-3.2.
- **Human-facing or sensitive-data systems** warrant higher initial prioritisation (PDF p. 13).
- **Characteristics trade off**; document the tradeoff and who decided, not just the metrics (PDF p. 17).
- **Status `implemented` requires evidence** (document, log, test report) - otherwise use a lower status.
- Playbook actions are **suggestions** ("neither a checklist nor set of steps", Playbook PDF p. 4);
  select what fits, and say why others were not adopted when material.

## Outputs

| Artefact | Template | Validator |
|---|---|---|
| AI system impact assessment / context record (`ai-context-record`) | [templates/ai-context-record.md](templates/ai-context-record.md) | `ai-rmf scan` |
| AI risk register (`ai-risk-register`) | [templates/ai-risk-register.md](templates/ai-risk-register.md) or `register-template` | `ai-rmf check-register` |
| Current/target profile + gap analysis (`ai-profile`) | [templates/ai-profile.md](templates/ai-profile.md) or `profile-template` | `ai-rmf check-profile` |
| Model / system card | [templates/model-system-card.md](templates/model-system-card.md) | `ai-rmf scan` |
| Monitoring & incident plan | [templates/incident-monitoring-plan.md](templates/incident-monitoring-plan.md) | `ai-rmf scan` |
| Governance review (`governance-review`) | [templates/governance-review.md](templates/governance-review.md) | `ai-rmf scan` |

Every deliverable: states scope, system version and date; cites subcategories as
`[nist-ai MAP 1.1, p. 31]` and Playbook items as `[nist-ai-playbook MAP 1.1/action-4, p. 63]`; separates
facts, assumptions and recommendations; lists open questions; and ends with a decision/sign-off block
naming the accountable human.

## Quality checklist

- [ ] Every subcategory id exists (`ai-rmf scan` shows no INVALID ids); page numbers are PDF pages from the tools.
- [ ] All seven trustworthiness characteristics considered (or explicitly scoped out with reason).
- [ ] Affected stakeholders include people who are not direct users (Section 1.2.1, PDF p. 11).
- [ ] Register passes `check-register`; high residual risks escalated or accepted by a named authority.
- [ ] Profile passes `check-profile`; every gap has owner and priority.
- [ ] Risk tolerance, scales and thresholds are attributed to the organisation, not to NIST.
- [ ] Third-party components, decommissioning and incident response are covered.
- [ ] No claim of "AI RMF compliance/certification"; wording is "aligned with" or "using".

## References

- [references/core-functions.md](references/core-functions.md) - functions, categories, how to apply each, pages.
- [references/trustworthy-characteristics.md](references/trustworthy-characteristics.md) - definitions, tradeoffs, MEASURE mapping.
- [references/profiles-and-registers.md](references/profiles-and-registers.md) - profiles, gap analysis, register rules, scales.
- [references/playbook-guide.md](references/playbook-guide.md) - Playbook structure, page map, how to cite actions.

## Sources

- `nist-ai` - NIST AI 100-1, *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*, January 2023.
  Relied on: Section 1 risk framing, tolerance, prioritisation, residual risk (PDF pp. 9-14, printed 4-9);
  Section 3 trustworthy characteristics (PDF pp. 17-23, printed 12-18); Section 5 Core and Tables 1-4
  (PDF pp. 25-38, printed 20-33); Section 6 Profiles (PDF pp. 38-39, printed 33-34). Printed page =
  PDF page - 5.
- `nist-ai-playbook` - NIST AI RMF Playbook (companion to AI RMF 1.0; 142 numbered pages, 147 PDF pages).
  Relied on: About the Playbook (PDF p. 4); GOVERN (PDF pp. 5-36), MANAGE (pp. 37-60), MAP (pp. 61-96),
  MEASURE (pp. 97-147). Printed "N of 142" = PDF page - 3.

## Limitations

- Output supports, but does not replace, qualified professional judgement, legal advice, or formal
  assurance, audit or approval by the accountable decision-makers. Go/no-go and risk acceptance are
  human decisions.
- The AI RMF is voluntary and outcome-based; it prescribes no risk tolerance, scales, thresholds or
  profile templates (PDF p. 39). Status levels, the 5x5 matrix and templates here are library conventions.
- The catalogs cover AI RMF 1.0 and the bundled Playbook snapshot. Later NIST profiles (e.g. the
  Generative AI Profile, NIST AI 600-1) are not included; check for newer editions.
- Playbook "About" text, transparency resources and references are not in the catalog - read the PDF.
- Some Playbook subcategory statements differ in wording from AI RMF 1.0 Tables 1-4; the AI RMF
  wording (`ai-rmf show`) is authoritative for outcome text.
