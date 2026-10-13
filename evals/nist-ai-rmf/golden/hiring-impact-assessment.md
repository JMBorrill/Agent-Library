# AI system impact assessment / context record - "TalentRank" résumé screening

| Field | Value |
|---|---|
| System | TalentRank (vendor SaaS) v4.2, configured for warehouse and office roles |
| Lifecycle stage | Plan & design / procurement (pre-deployment) |
| Organisation's role | Deployer and acquirer (vendor is the developer) |
| Date | 2026-10-13 |
| Accountable executive | Chief People Officer (GOVERN 2.3) - to confirm |

Framework: assessed using NIST AI RMF 1.0 (NIST AI 100-1) and the AI RMF Playbook. The AI RMF is
voluntary; this record does not certify anything. Citations use PDF pages.

## 1. Intended purpose and context

- **Purpose:** rank applications for ~6,000 vacancies/year so recruiters review the most relevant first;
  benefit: faster time-to-hire and more consistent screening [nist-ai MAP 1.1, p. 31].
- **Business value:** recruiter capacity is the bottleneck in peak season [nist-ai MAP 1.4, p. 31].
- **Context-specific laws and norms:** employment non-discrimination and disability law, data
  protection law; to be confirmed by employment counsel (open question Q1) [nist-ai GOVERN 1.1, p. 27].
- **Foreseeable misuse / use beyond intended purpose:** auto-rejecting low-ranked applicants without
  human review; reuse of scores for internal promotion decisions (out of scope).
- **Non-AI alternative considered:** structured knock-out questions plus manual review
  [nist-ai-playbook MAP 1.1/action-5, p. 63].

## 2. Affected stakeholders

| Group | Direct user? | How affected |
|---|---|---|
| Applicants (incl. disabled applicants, career changers, older applicants) | No | Ranking affects access to employment |
| Recruiters and hiring managers | Yes | Workload, reliance on ranking |
| HR systems / data protection | Yes | Data processing, vendor oversight |

Applicants are affected but are not users - the AI RMF notes harmed groups are not always direct users
of a system (Section 1.2.1, PDF p. 11).

## 3. Risk tolerance and requirements

- The AI RMF does not prescribe risk tolerance (Section 1.2.2, PDF p. 12). The organisation's ERM
  appetite statement says "low appetite for unlawful discrimination"; this must be translated into AI
  thresholds by the risk committee (open question Q2) [nist-ai MAP 1.5, p. 31].
- Requirements: "the system shall not be used to reject an applicant without human review"; "the
  system shall provide reasons for each ranking" [nist-ai MAP 1.6, p. 31].

## 4. System categorisation

- Task/method: supervised ranking model using a vendor fine-tuned language model on CV text
  [nist-ai MAP 2.1, p. 31].
- Knowledge limits: trained on vendor's historical hiring data; untested on our role mix; poor on
  non-standard CV formats. Human oversight: recruiters review all shortlisted and a random 10% sample of
  others [nist-ai MAP 2.2, p. 31] [nist-ai MAP 3.5, p. 32].
- TEVV considerations: representativeness of validation data and construct validity of "fit"
  [nist-ai MAP 2.3, p. 32].
- Third-party components: vendor model and hosting; IP and data-use terms [nist-ai MAP 4.1, p. 32].

## 5. Trustworthiness characteristics screen

| Characteristic | Relevance | Key failure modes | MEASURE subcategory |
|---|---|---|---|
| Valid and reliable | High | Ranking does not predict job performance for our roles | MEASURE 2.5 |
| Safe | Low | No physical safety impact; psychological harm from opaque rejection noted | MEASURE 2.6 |
| Secure and resilient | Medium | Prompt-injection text in CVs manipulating scores | MEASURE 2.7 |
| Accountable and transparent | High | Applicants not told AI is used; unclear decision ownership | MEASURE 2.8 |
| Explainable and interpretable | High | Recruiters cannot see why a CV ranked low | MEASURE 2.9 |
| Privacy-enhanced | Medium | Inference of age, health or ethnicity from CV text | MEASURE 2.10 |
| Fair - with harmful bias managed | High | Systemic and statistical bias against employment gaps, disability, age | MEASURE 2.11 |

Tradeoff noted: richer explanations may expose sensitive inferences (explainability vs privacy).

## 6. Impacts

| Impact | Stakeholders | Likelihood | Magnitude | Basis |
|---|---|---|---|---|
| Qualified applicants with career gaps ranked low and never reviewed | Applicants | Likely (4) | Major (4) | Published incidents with CV screeners; vendor's own bias report |
| Faster screening for recruiters | Recruiters | Almost certain (5) | Moderate benefit | Pilot data |
| Discrimination claim and reputational damage | Organisation | Possible (3) | Major (4) | Legal advice pending |

Likelihood and magnitude documented per [nist-ai MAP 5.1, p. 32]; scales are the library convention
(1-5), not NIST's. Engagement with applicant representatives and the disability network is planned
[nist-ai MAP 5.2, p. 33].

## 7. Go/no-go input

- **Recommendation:** proceed to a limited pilot **with conditions** - no automated rejection; disparity
  testing on our data before go-live (MEASURE 2.11); applicant notice; vendor change notification clause.
  Completing MAP should give enough context for an initial go/no-go decision (Section 5.2, PDF p. 30).
- **Decision by:** Chief People Officer with the AI risk committee - human decision, not the assessor's.

## 8. Open questions

- Q1 Applicable employment and data protection law (counsel).
- Q2 Quantitative fairness thresholds and risk tolerance (risk committee).
- Q3 Vendor's training data provenance and update cadence.

This assessment supports, but does not replace, professional judgement, legal advice or formal approval.
