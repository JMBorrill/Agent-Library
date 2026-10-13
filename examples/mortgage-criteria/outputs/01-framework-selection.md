# Framework selection — Mortgage Criteria Platform

**Oversight level:** high

## Selected packs
| Pack | Why | Triggers | Skills |
|---|---|---|---|
| systems-engineering | physical/multidisciplinary system or high consequence of failure — needs requirements, interfaces, risk, V&V and gates | risk:high | `se-technical-planning`, `se-stakeholder-conops`, `se-requirements`, `se-risk-analysis`, `se-verification-validation`, `se-review-gates`, `se-change-control`, `se-configuration-management`, `se-technical-data-management` |
| software | software is being built — code review, traceability and delivery metrics apply | flag:software, keyword:web, keyword:platform | `software-code-review`, `software-requirements-traceability` |
| reliability-security | deployed service handling data or users — threat modelling, ASVS controls, secure development and operations apply | flag:multi_tenant, flag:personal_data, flag:online_service | `security-threat-model`, `security-asvs-controls`, `security-code-checks`, `security-secure-development`, `sre-service-level-objectives`, `sre-production-readiness` |
| product | external users/customers — evidence-led discovery and scoped delivery apply | flag:external_users | `product-discovery`, `product-requirements-brief`, `product-experiment-design`, `product-shaping` |
| ux | user interface — accessible form and error patterns apply | flag:ui | `ux-accessibility-review` |
| finance-credit | investment, unit economics or lending decisions — reproducible financial and credit analysis apply | flag:finance, flag:lending, keyword:mortgage, keyword:lender, keyword:credit | `credit-criteria-modelling`, `credit-risk-governance`, `finance-fca-scope-check` |
| ai-governance | AI components — risk assessment, evaluation, prompt-injection testing and oversight apply | flag:ai, keyword:ai, keyword:recommendation, keyword:ai-powered | `ai-risk-assessment`, `ai-eval-harness`, `ai-prompt-injection-review`, `ai-human-oversight` |
| orchestration | independent challenge review applies to every project | always | `independent-review`, `select-frameworks` |

## Excluded packs
| Pack | Why not |
|---|---|
| space-engineering | no space or low-gravity context detected |

## Agents
| Agent | Skills it covers here |
|---|---|
| `ai-evaluation-engineer` | ai-eval-harness, ai-human-oversight, ai-prompt-injection-review, ai-risk-assessment |
| `ai-governance-reviewer` | ai-eval-harness, ai-human-oversight, ai-prompt-injection-review, ai-risk-assessment |
| `credit-regulatory-reviewer` | credit-criteria-modelling, credit-risk-governance, finance-fca-scope-check |
| `financial-analyst` | credit-criteria-modelling |
| `independent-reviewer` | independent-review, se-requirements, se-review-gates, se-verification-validation |
| `product-lead` | product-discovery, product-experiment-design, product-requirements-brief, product-shaping, ux-accessibility-review |
| `reliability-engineer` | sre-production-readiness, sre-service-level-objectives |
| `requirements-engineer` | se-change-control, se-requirements, software-requirements-traceability |
| `safety-risk-reviewer` | se-change-control, se-risk-analysis |
| `security-reviewer` | security-asvs-controls, security-code-checks, security-secure-development, security-threat-model |
| `software-quality-reviewer` | software-code-review, software-requirements-traceability, ux-accessibility-review |
| `systems-engineer` | se-configuration-management, se-review-gates, se-stakeholder-conops, se-technical-data-management, se-technical-planning |
| `vv-engineer` | se-verification-validation |

## Frameworks (source access status in this library)
| Source | Title | Access | Normative status |
|---|---|---|---|
| `basel-credit` | Basel Committee Credit Risk Principles | INACCESSIBLE | advisory to supervisors/banks; jurisdiction implementation varies |
| `fca` | FCA Handbook | INACCESSIBLE | mandatory for FCA-authorised firms within scope (legal advice required to determine scope) |
| `google-review` | Google Engineering Practices | VERIFIED | advisory |
| `google-sre` | Site Reliability Engineering, Google | INACCESSIBLE | advisory |
| `gov-design` | GOV.UK Design System | VERIFIED | advisory |
| `gov-service` | GOV.UK Service Manual | INACCESSIBLE | advisory |
| `nasa-se` | NASA Systems Engineering Handbook, NASA/SP-2016-6105 Rev 2 | INACCESSIBLE | advisory |
| `nasa-se-design` | NASA SE Handbook, chapter 4 | INACCESSIBLE | advisory |
| `nasa-se-manage` | NASA SE Handbook, chapter 6 | INACCESSIBLE | advisory |
| `nasa-se-realize` | NASA SE Handbook, chapter 5 | INACCESSIBLE | advisory |
| `nasa-software` | NASA Software Engineering and Assurance Handbook | INACCESSIBLE | advisory |
| `nist-ai` | NIST AI RMF Playbook | INACCESSIBLE | advisory |
| `nist-ssdf` | NIST Secure Software Development Framework (SSDF) | PARTIALLY_VERIFIED | advisory (mandatory only where contractually required, e.g. US federal suppliers) |
| `owasp-asvs` | OWASP ASVS | VERIFIED | advisory (voluntary standard; contractual if adopted) |
| `shape-up` | Shape Up by Ryan Singer | INACCESSIBLE | advisory |

## Recommended workflow
- **1. Frame and tailor**: `select-frameworks`, `se-technical-planning`, `se-stakeholder-conops`, `product-discovery`, `finance-fca-scope-check`, `ai-risk-assessment`
- **2. Define needs and requirements**: `product-requirements-brief`, `product-experiment-design`, `se-requirements`, `credit-criteria-modelling`
- **3. Design and analyse**: `security-threat-model`, `ai-human-oversight`, `product-shaping`, `credit-risk-governance`
- **4. Build and verify**: `se-verification-validation`, `software-code-review`, `software-requirements-traceability`, `security-code-checks`, `security-asvs-controls`, `security-secure-development`, `ux-accessibility-review`, `ai-eval-harness`, `ai-prompt-injection-review`, `se-risk-analysis`
- **5. Independent review and gates**: `independent-review`, `se-review-gates`, `se-change-control`, `se-configuration-management`
- **6. Release, transition and operate**: `sre-service-level-objectives`, `sre-production-readiness`, `se-technical-data-management`

## Human sign-offs required
- Decision owner approves tailoring, baselines and gate decisions
- Compliance officer / legal counsel confirms regulatory applicability and obligations
- Authorised lender staff make all credit decisions; the system only supports them
- Accountable owner approves AI deployment after independent evaluation review
- Data-protection lead approves personal-data processing and lawful basis

## Install (dry-run first)
```
python3 scripts/install_packs.py --target <PROJECT_DIR> --skills se-technical-planning,se-stakeholder-conops,se-requirements,se-risk-analysis,se-verification-validation,se-review-gates,se-change-control,se-configuration-management,se-technical-data-management,software-code-review,software-requirements-traceability,security-threat-model,security-asvs-controls,security-code-checks,security-secure-development,sre-service-level-objectives,sre-production-readiness,product-discovery,product-requirements-brief,product-experiment-design,product-shaping,ux-accessibility-review,credit-criteria-modelling,credit-risk-governance,finance-fca-scope-check,ai-risk-assessment,ai-eval-harness,ai-prompt-injection-review,ai-human-oversight,independent-review,select-frameworks --agents ai-evaluation-engineer,ai-governance-reviewer,credit-regulatory-reviewer,financial-analyst,independent-reviewer,product-lead,reliability-engineer,requirements-engineer,safety-risk-reviewer,security-reviewer,software-quality-reviewer,systems-engineer,vv-engineer   # dry-run by default; add --apply to write
```

_Proposal generated by select_frameworks.py; the project owner decides which frameworks apply._

INFO: 12 selected framework sources were not verified at primary level in this library: basel-credit, fca, google-sre, gov-service, nasa-se, nasa-se-design, nasa-se-manage, nasa-se-realize, nasa-software, nist-ai, nist-ssdf, shape-up
