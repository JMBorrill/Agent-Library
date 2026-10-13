# Framework selection — Project ASTER

**Oversight level:** high

## Selected packs
| Pack | Why | Triggers | Skills |
|---|---|---|---|
| systems-engineering | physical/multidisciplinary system or high consequence of failure — needs requirements, interfaces, risk, V&V and gates | flag:hardware, flag:physical_tests, flag:safety_critical, keyword:robot, keyword:embedded, keyword:locomotion | `se-technical-planning`, `se-stakeholder-conops`, `se-requirements`, `se-risk-analysis`, `se-verification-validation`, `se-review-gates`, `se-logical-decomposition`, `se-architecture-trades`, `se-decision-analysis`, `se-interface-control`, `se-implementation-integration`, `se-technical-assessment`, `se-change-control`, `se-configuration-management`, `se-transition` |
| space-engineering | space or small-body environment — engineering budgets and low-gravity physics apply | keyword:asteroid, keyword:low-gravity | `space-technical-budgets`, `space-low-gravity-mobility` |
| software | software is being built — code review, traceability and delivery metrics apply | flag:software, keyword:software | `software-code-review`, `software-requirements-traceability` |
| orchestration | independent challenge review applies to every project | always | `independent-review`, `select-frameworks` |

## Excluded packs
| Pack | Why not |
|---|---|
| reliability-security | no deployed service, personal data or multi-tenancy detected |
| product | no external users or market detected (internal research tool) |
| ux | no user interface detected |
| finance-credit | no financial appraisal, revenue model or lending detected |
| ai-governance | no AI/ML component detected |

## Agents
| Agent | Skills it covers here |
|---|---|
| `independent-reviewer` | independent-review, se-decision-analysis, se-requirements, se-review-gates, se-verification-validation |
| `requirements-engineer` | se-change-control, se-interface-control, se-requirements, software-requirements-traceability |
| `safety-risk-reviewer` | se-change-control, se-risk-analysis, space-low-gravity-mobility |
| `software-quality-reviewer` | software-code-review, software-requirements-traceability |
| `systems-architect` | se-architecture-trades, se-decision-analysis, se-logical-decomposition, space-low-gravity-mobility, space-technical-budgets |
| `systems-engineer` | se-configuration-management, se-review-gates, se-stakeholder-conops, se-technical-assessment, se-technical-planning, se-transition |
| `vv-engineer` | se-implementation-integration, se-verification-validation |

## Frameworks (source access status in this library)
| Source | Title | Access | Normative status |
|---|---|---|---|
| `ecss-se` | ECSS-E-ST-10C Rev.1 | INACCESSIBLE | mandatory only where contractually applied (e.g. ESA projects) |
| `google-review` | Google Engineering Practices | VERIFIED | advisory |
| `gov-service` | GOV.UK Service Manual | INACCESSIBLE | advisory |
| `nasa-se` | NASA Systems Engineering Handbook, NASA/SP-2016-6105 Rev 2 | INACCESSIBLE | advisory |
| `nasa-se-design` | NASA SE Handbook, chapter 4 | INACCESSIBLE | advisory |
| `nasa-se-manage` | NASA SE Handbook, chapter 6 | INACCESSIBLE | advisory |
| `nasa-se-realize` | NASA SE Handbook, chapter 5 | INACCESSIBLE | advisory |
| `nasa-software` | NASA Software Engineering and Assurance Handbook | INACCESSIBLE | advisory |
| `nist-ai` | NIST AI RMF Playbook | INACCESSIBLE | advisory |

## Recommended workflow
- **1. Frame and tailor**: `select-frameworks`, `se-technical-planning`, `se-stakeholder-conops`
- **2. Define needs and requirements**: `se-requirements`
- **3. Design and analyse**: `se-logical-decomposition`, `se-architecture-trades`, `se-decision-analysis`, `se-interface-control`, `space-technical-budgets`, `space-low-gravity-mobility`
- **4. Build and verify**: `se-implementation-integration`, `se-verification-validation`, `software-code-review`, `software-requirements-traceability`, `se-technical-assessment`, `se-risk-analysis`
- **5. Independent review and gates**: `independent-review`, `se-review-gates`, `se-change-control`, `se-configuration-management`
- **6. Release, transition and operate**: `se-transition`

## Human sign-offs required
- Decision owner approves tailoring, baselines and gate decisions
- Qualified safety authority approves hazard analysis and authorises every physical test

## Install (dry-run first)
```
python3 scripts/install_packs.py --target <PROJECT_DIR> --skills se-technical-planning,se-stakeholder-conops,se-requirements,se-risk-analysis,se-verification-validation,se-review-gates,se-logical-decomposition,se-architecture-trades,se-decision-analysis,se-interface-control,se-implementation-integration,se-technical-assessment,se-change-control,se-configuration-management,se-transition,space-technical-budgets,space-low-gravity-mobility,software-code-review,software-requirements-traceability,independent-review,select-frameworks --agents independent-reviewer,requirements-engineer,safety-risk-reviewer,software-quality-reviewer,systems-architect,systems-engineer,vv-engineer   # dry-run by default; add --apply to write
```

_Proposal generated by select_frameworks.py; the project owner decides which frameworks apply._

INFO: 8 selected framework sources were not verified at primary level in this library: ecss-se, gov-service, nasa-se, nasa-se-design, nasa-se-manage, nasa-se-realize, nasa-software, nist-ai
