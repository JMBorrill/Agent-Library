# Framework selection — AI Operations Platform

**Oversight level:** medium

## Selected packs
| Pack | Why | Triggers | Skills |
|---|---|---|---|
| software | software is being built — code review, traceability and delivery metrics apply | flag:software, keyword:saas, keyword:platform, keyword:service | `software-code-review`, `software-requirements-traceability` |
| reliability-security | deployed service handling data or users — threat modelling, ASVS controls, secure development and operations apply | flag:multi_tenant, flag:personal_data, flag:online_service, flag:payments, keyword:saas, keyword:multi-tenant | `security-threat-model`, `security-asvs-controls`, `security-code-checks`, `security-secure-development`, `sre-service-level-objectives`, `sre-production-readiness` |
| product | external users/customers — evidence-led discovery and scoped delivery apply | flag:external_users, keyword:customer, keyword:mvp, keyword:saas, keyword:crm, keyword:businesses | `product-discovery`, `product-requirements-brief`, `product-experiment-design`, `product-shaping` |
| ux | user interface — accessible form and error patterns apply | flag:ui | `ux-accessibility-review` |
| finance-credit | investment, unit economics or lending decisions — reproducible financial and credit analysis apply | flag:finance, keyword:unit economics, keyword:saas | `finance-unit-economics` |
| ai-governance | AI components — risk assessment, evaluation, prompt-injection testing and oversight apply | flag:ai, keyword:ai, keyword:ai-powered | `ai-risk-assessment`, `ai-eval-harness`, `ai-prompt-injection-review`, `ai-human-oversight` |
| orchestration | independent challenge review applies to every project | always | `independent-review`, `select-frameworks` |

## Excluded packs
| Pack | Why not |
|---|---|
| systems-engineering | no hardware, physical test, safety-critical or high-risk element detected |
| space-engineering | no space or low-gravity context detected |

## Agents
| Agent | Skills it covers here |
|---|---|
| `ai-evaluation-engineer` | ai-eval-harness, ai-human-oversight, ai-prompt-injection-review, ai-risk-assessment |
| `ai-governance-reviewer` | ai-eval-harness, ai-human-oversight, ai-prompt-injection-review, ai-risk-assessment |
| `financial-analyst` | finance-unit-economics |
| `independent-reviewer` | independent-review |
| `product-lead` | product-discovery, product-experiment-design, product-requirements-brief, product-shaping, ux-accessibility-review |
| `reliability-engineer` | sre-production-readiness, sre-service-level-objectives |
| `requirements-engineer` | software-requirements-traceability |
| `security-reviewer` | security-asvs-controls, security-code-checks, security-secure-development, security-threat-model |
| `software-quality-reviewer` | software-code-review, software-requirements-traceability, ux-accessibility-review |

## Frameworks (source access status in this library)
| Source | Title | Access | Normative status |
|---|---|---|---|
| `damodaran` | Aswath Damodaran Corporate Finance | INACCESSIBLE | advisory |
| `google-review` | Google Engineering Practices | VERIFIED | advisory |
| `google-sre` | Site Reliability Engineering, Google | INACCESSIBLE | advisory |
| `gov-design` | GOV.UK Design System | VERIFIED | advisory |
| `gov-service` | GOV.UK Service Manual | INACCESSIBLE | advisory |
| `nasa-se` | NASA Systems Engineering Handbook, NASA/SP-2016-6105 Rev 2 | INACCESSIBLE | advisory |
| `nasa-se-manage` | NASA SE Handbook, chapter 6 | INACCESSIBLE | advisory |
| `nasa-software` | NASA Software Engineering and Assurance Handbook | INACCESSIBLE | advisory |
| `nist-ai` | NIST AI RMF Playbook | INACCESSIBLE | advisory |
| `nist-ssdf` | NIST Secure Software Development Framework (SSDF) | PARTIALLY_VERIFIED | advisory (mandatory only where contractually required, e.g. US federal suppliers) |
| `owasp-asvs` | OWASP ASVS | VERIFIED | advisory (voluntary standard; contractual if adopted) |
| `shape-up` | Shape Up by Ryan Singer | INACCESSIBLE | advisory |

## Recommended workflow
- **1. Frame and tailor**: `select-frameworks`, `product-discovery`, `ai-risk-assessment`
- **2. Define needs and requirements**: `product-requirements-brief`, `product-experiment-design`, `finance-unit-economics`
- **3. Design and analyse**: `security-threat-model`, `ai-human-oversight`, `product-shaping`
- **4. Build and verify**: `software-code-review`, `software-requirements-traceability`, `security-code-checks`, `security-asvs-controls`, `security-secure-development`, `ux-accessibility-review`, `ai-eval-harness`, `ai-prompt-injection-review`
- **5. Independent review and gates**: `independent-review`
- **6. Release, transition and operate**: `sre-service-level-objectives`, `sre-production-readiness`

## Human sign-offs required
- Decision owner approves tailoring, baselines and gate decisions
- Accountable owner approves AI deployment after independent evaluation review
- Data-protection lead approves personal-data processing and lawful basis

## Install (dry-run first)
```
python3 scripts/install_packs.py --target <PROJECT_DIR> --skills software-code-review,software-requirements-traceability,security-threat-model,security-asvs-controls,security-code-checks,security-secure-development,sre-service-level-objectives,sre-production-readiness,product-discovery,product-requirements-brief,product-experiment-design,product-shaping,ux-accessibility-review,finance-unit-economics,ai-risk-assessment,ai-eval-harness,ai-prompt-injection-review,ai-human-oversight,independent-review,select-frameworks --agents ai-evaluation-engineer,ai-governance-reviewer,financial-analyst,independent-reviewer,product-lead,reliability-engineer,requirements-engineer,security-reviewer,software-quality-reviewer   # dry-run by default; add --apply to write
```

_Proposal generated by select_frameworks.py; the project owner decides which frameworks apply._

INFO: 9 selected framework sources were not verified at primary level in this library: damodaran, google-sre, gov-service, nasa-se, nasa-se-manage, nasa-software, nist-ai, nist-ssdf, shape-up
