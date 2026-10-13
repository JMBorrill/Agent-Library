# Trustworthy AI characteristics

Source: `nist-ai` Section 3 "AI Risks and Trustworthiness" (PDF pp. 17-23, printed pp. 12-18).
Summaries are paraphrased; run `python -m agentlib ai-rmf characteristics` for the catalog version.

The seven characteristics: **valid and reliable, safe, secure and resilient, accountable and
transparent, explainable and interpretable, privacy-enhanced, and fair with harmful bias managed**
(PDF p. 17). Fig. 4 shows valid & reliable as the base (a necessary condition) and accountable &
transparent as relating to all others (PDF p. 17).

| Id (library) | Section | PDF page | Primary MEASURE subcategory | Other strongly related subcategories |
|---|---|---|---|---|
| `valid-reliable` | 3.1 Valid and Reliable | 18 | MEASURE 2.5 | MEASURE 2.3, MEASURE 2.4, MAP 2.3 |
| `safe` | 3.2 Safe | 19 | MEASURE 2.6 | MANAGE 2.4, MAP 5.1 |
| `secure-resilient` | 3.3 Secure and Resilient | 20 | MEASURE 2.7 | MAP 4.1, MANAGE 3.1 |
| `accountable-transparent` | 3.4 Accountable and Transparent | 20 | MEASURE 2.8 | GOVERN 2.1, GOVERN 4.2, MAP 2.2 |
| `explainable-interpretable` | 3.5 Explainable and Interpretable | 21 | MEASURE 2.9 | MAP 2.2 |
| `privacy-enhanced` | 3.6 Privacy-Enhanced | 22 | MEASURE 2.10 | MAP 1.6 |
| `fair-bias-managed` | 3.7 Fair – with Harmful Bias Managed | 22 | MEASURE 2.11 | MAP 1.2, GOVERN 3.1 |

The MEASURE 2.5-2.11 mapping follows the subcategory wording (e.g. MEASURE 2.11 "Fairness and bias ...
are evaluated", PDF p. 35). The "other related" column is this library's judgement - verify relevance
with `ai-rmf show <id>`. MEASURE 2.12 (environmental impact and sustainability) has no matching
Section 3 characteristic but should be assessed where training/inference is resource-heavy.

## Key points per characteristic (paraphrase)

**Valid and reliable (PDF pp. 18-19).** Validation: objective evidence that requirements for the
specific intended use are fulfilled (ISO 9000:2015). Reliability: performing as required without
failure over time under given conditions. Accuracy (with realistic, representative test sets and
documented methodology; disaggregated where relevant) and robustness/generalisability contribute and can
be in tension. Ongoing testing/monitoring confirms deployed performance; consider human intervention
where the system cannot detect or correct errors.

**Safe (PDF pp. 19-20).** Must not, under defined conditions, endanger human life, health, property or
the environment. Responsible design, clear information to deployers, responsible decisions by
deployers/users, and documentation of risks based on empirical incident evidence. Risks of serious
injury or death get the most urgent prioritisation. Approaches: simulation, in-domain testing,
real-time monitoring, ability to shut down, modify or have human intervention; align with sector
safety guidelines.

**Secure and resilient (PDF p. 20).** Resilience: withstand unexpected adverse events or changes and
degrade safely and gracefully. Security: confidentiality, integrity, availability via protection
mechanisms; covers adversarial examples, data poisoning, exfiltration of models/training data/IP.
NIST CSF and RMF are cited as applicable guidance.

**Accountable and transparent (PDF pp. 20-21).** Accountability presupposes transparency - the extent
information about the system and its outputs is available to those interacting with it, appropriate to
lifecycle stage and role. Spans design decisions, training data, model structure, intended use, and
who made deployment decisions. Supports redress. A transparent system is not necessarily accurate,
private, secure or fair. Data provenance supports both.

**Explainable and interpretable (PDF pp. 21-22).** Explainability = representation of underlying
mechanisms ("how"); interpretability = meaning of output in context ("why"); transparency = "what
happened" (PDF p. 22). Tailor explanations to the user's role, knowledge and skill.

**Privacy-enhanced (PDF p. 22).** Safeguard autonomy, identity and dignity; anonymity,
confidentiality and control. Inference can re-identify people. PETs, de-identification and aggregation
help; under data sparsity they can reduce accuracy and affect fairness decisions. See NIST Privacy
Framework.

**Fair - with harmful bias managed (PDF pp. 22-23).** Equality and equity; fairness perceptions differ
across cultures and applications. Mitigating harmful bias does not by itself make a system fair. Three
major bias categories: **systemic, computational and statistical, human-cognitive** - each can occur
without prejudice or intent (PDF p. 23). See NIST SP 1270.

## Tradeoffs (PDF pp. 17-18)

- Examples named by NIST: interpretability vs privacy; predictive accuracy vs interpretability;
  privacy-enhancing techniques vs accuracy (under data sparsity), affecting fairness.
- Highly secure but unfair, accurate but opaque, or inaccurate but secure/private/transparent systems
  are all undesirable; balance is required and depends on context.
- Resolve tradeoffs transparently and justifiably; record the decision and decision-maker.
- Human judgement should set metrics and threshold values (PDF p. 17) - the AI RMF gives none.

## Writing it up

For each characteristic in an assessment give: relevance (high/medium/low/not applicable, with
reason), the specific failure modes for this system, affected stakeholders, metrics and thresholds set
by the organisation, the MEASURE subcategory and Playbook actions used, and residual concerns.
